#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>

#include <stdint.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <signal.h>
#include <time.h>

#include <errno.h>


#define OSC_CONF   0
#define OSC_TRG    4
#define OSC_DEC   20
#define OSC_PNT   24
#define OSC_WE_CNT 0x2C   // samples written since the last arm/reset (2.0 scope; saturates at 2^32-1)



#define OSC_FPGA_BASE_ADDR 0x40100000
#define OSC_FPGA_BASE_SIZE 0x30000
#define OSC_FPGA_SIG_LEN   (16*1024)


#define OSC_FPGA_CH_A_OFFSET 0x10000
#define OSC_FPGA_CH_B_OFFSET 0x20000

// Lock-in registers: stream_rate (0x184) is the decimation used by the scope while streaming;
// stream_cmd (0x188) != 0 while streaming (the UI Stop and rp_app_exit write 0)
#define LOCK_FPGA_BASE_ADDR   0x40600000
#define LOCK_STREAM_RATE_OFF  0x184
#define LOCK_STREAM_CMD_OFF   0x188


#define BUF_LEN  16384
#define WP_MASK  (OSC_FPGA_SIG_LEN-1)

// Send buffer, in samples (uint32: chA | chB<<16). One read of the FPGA buffer adds up to
// OSC_FPGA_SIG_LEN-1 samples and up to send_min_len-1 can be pending from the previous one,
// so the buffer is flushed before a read that would not fit (see main loop). 2*BUF_LEN of margin.
#define SEND_BUF_LEN  (2*BUF_LEN)

// Write pointer (WP) handling (v2.3.10). The 2.0 FPGA of v2.3.10-10 sometimes returned a WP some samples
// behind the previous one (scope read data crossing to the PS clock unsynchronized, fixed in rp_scope_cfg.v)
// and the old loop took it as a full turn of the buffer: 16384 old samples were sent again.
//  - WP_SAME_MAX: three consecutive reads of the WP must agree (each one equal or a little ahead of the
//    previous one); otherwise they are discarded (a WP read ahead of the real one would make us read
//    samples not written yet, i.e. from the previous turn of the buffer).
//  - The WP is used as a monotonic value: a WP behind the last accepted one (by less than half the
//    buffer, WP_HALF) is a bad read and is ignored (the last WP is used). The read pointer never goes back.
//  - WP_MARGIN: read only up to WP - WP_MARGIN (the last samples may still be in the BRAM write pipeline).
//  - The "samples written" counter (0x2C) only goes down when the scope is armed/reset: if someone else
//    does it while streaming (the WP restarts at 0 while the buffer still holds old samples), the scope
//    is reset + armed again and reading restarts at 0 (data gap, logged).
//  - STALL_NS: WP not advancing for this long (the scope was reset or stopped by a trigger while
//    streaming): the samples left up to the WP are read and the scope is reset + armed (as at start).
//  - Overrun (v2.3.10-13: classified with the "samples written" counter 0x2C). The counter gives the
//    index of each sample since the arm, so the number of unread samples is exact. More than
//    OSC_FPGA_SIG_LEN - WP_SKIP_AT unread (the reader fell behind: send() blocked, or decimation 64,
//    1.95 MS/s while the bus reads ~1.63 MS/s): the oldest ones are skipped and reading goes on
//    WP_SKIP_TO samples behind the newest (data gap, counted as overrun; skipped samples in "lost").
//    A WP more than half a buffer ahead is taken as a real advance (not as a bad read "behind",
//    wp_back) when the counter confirms it: before, a reader more than 8192 samples late was
//    counted as wp_back and that buffer was lost without notice.
//    The BRAM is read in sub-blocks of RD_SUB samples and the counter is read after each one: the
//    samples that the writer may have overwritten meanwhile (counter >= index + buffer - WP_GUARD)
//    are dropped (counted as overrun/lost) instead of sending newer samples in their place.
//    Without the counter (saturated): overrun by time (as before), reading restarts at the WP.
//  - Stop (v2.3.10-13): stream_cmd is read before and after each read of the BRAM. When it is 0 the
//    block just read is dropped (the worker of the App may already be reconfiguring the scope for the
//    oscilloscope: those were the corrupted ~9000-16000 samples at the end of each streaming), the
//    pending data is sent and the program ends (before c/streaming's SIGTERM).
//    The 0x2C counter saturates at 2^32-1 (36 min at decimation 64, 73 min at 128): from then on the
//    checks that use it are skipped (the time based overrun is kept).
#define WP_MARGIN           8
#define WP_GUARD            64
#ifndef WP_SKIP_AT
#define WP_SKIP_AT          2048
#endif
#ifndef WP_SKIP_TO
#define WP_SKIP_TO          4096
#endif
#define RD_SUB              1024
#define WE_SAT              0xffffffffu
#define WP_HALF             (OSC_FPGA_SIG_LEN/2)
#define WP_SAME_MAX         64
#define STALL_NS            (200*1000000LL)
#define STATS_NS            ( 10*1000000000LL)

// FPGA register access (the local test harness can redefine them)
#ifndef FPGA_RD
#define FPGA_RD(p)     (*(p))
#define FPGA_WR(p, v)  (*(p) = (v))
#endif

static uint32_t buf_i[SEND_BUF_LEN];

static volatile sig_atomic_t stop_req = 0;

static void on_term(int sig){
    (void)sig;
    stop_req = 1;
}

// Event counters (printed to stderr every STATS_NS when something changed, and at exit)
static unsigned long cnt_wp_glitch = 0;   // two WP reads that do not agree
static unsigned long cnt_wp_back   = 0;   // WP behind the read pointer (ignored)
static unsigned long cnt_resync    = 0;   // read pointer moved to the WP (data gap)
static unsigned long cnt_ext_arm   = 0;   // scope armed/reset by someone else while streaming
static unsigned long cnt_rearm     = 0;   // scope re-armed because the WP stopped
static unsigned long cnt_overrun   = 0;   // reader behind by more than the buffer: samples lost
static unsigned long long cnt_samples = 0;
static unsigned long long cnt_lost    = 0;   // samples skipped or dropped by overruns (0x2C counter; approx.)
static unsigned long long cnt_end_drop= 0;   // samples read after stream_cmd went to 0 (dropped)

static void print_stats(const char *when){
    fprintf(stderr, "[%s] samples=%llu wp_glitch=%lu wp_back=%lu resync=%lu ext_arm=%lu rearm=%lu overrun=%lu lost=%llu end_drop=%llu\n",
            when, cnt_samples, cnt_wp_glitch, cnt_wp_back, cnt_resync, cnt_ext_arm, cnt_rearm, cnt_overrun,
            cnt_lost, cnt_end_drop);
    fflush(stderr);
}

static long long now_ns(void){
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

// Send n samples of buf_i. Exits on error (e.g. the client closed the connection).
static void send_all(int connection, unsigned long n){
    const char *p    = (const char *) buf_i;
    size_t      left = n * sizeof(buf_i[0]);
    while(left > 0){
        ssize_t r = send(connection, p, left, MSG_NOSIGNAL);
        if(r < 0){
            if(errno == EINTR && !stop_req) continue;
            if(errno != EINTR) perror("[-] send");
            print_stats("-");
            close(connection);
            exit(1);
        }
        p    += r;
        left -= r;
    }
}

// Reset the scope buffer and arm it (the write pointer restarts at 0)
static void scope_rearm(volatile uint32_t *conf){
    FPGA_WR(conf, 2);   // start clearing
    usleep(300);
    FPGA_WR(conf, 1);   // start recording
    usleep(3);
}

// Decimation used while streaming (lock stream_rate, 17 bits; 0 and 1 mean no decimation)
static unsigned long read_dec(volatile uint32_t *rate){
    unsigned long d = rate ? (FPGA_RD(rate) & 0x1ffff) : 128;
    return d < 1 ? 1 : d;
}


int main(int argc, char **argv){
    if(argc<4)
    {
        printf("<host> <port> <send_min_len>\n");
        return 1;
    }
    struct sockaddr_in server;
    struct hostent *client;
    client = gethostbyname(argv[1]);                                      // Get client object from 1st argument
    if(client == NULL)
    {                                                                     // Check valivity
        fprintf(stderr, "[-] Host not found: %s \n", argv[1] );
        return 1;
    }
    int port, connection;

    void *osc_ptr ;


    unsigned int send_min_len = 0;
    send_min_len   = atoi(argv[3]);   // Get minimun data points length to send
    if(send_min_len < 1)            send_min_len = 1;
    if(send_min_len > BUF_LEN)      send_min_len = BUF_LEN;   // buf_i must hold send_min_len-1 + OSC_FPGA_SIG_LEN-1



    connection = socket(AF_INET, SOCK_STREAM, 0);         // get TCP socket
    port   = (atoi(argv[2]));                             // get connection port
    bzero((char *)&server, sizeof(server));
                                                                          //La función bzero() es como memset() pero inicializando a 0 todas la variables

    server.sin_family = AF_INET;                          // Server protocol TCP
    server.sin_port   = htons(port);                      // Server port
    bcopy((char *)client->h_addr, (char *)&server.sin_addr.s_addr, client->h_length);  // Get ip adress from client object

    if(connect(connection,(struct sockaddr *)&server, sizeof(server)) < 0){
        fprintf(stderr,"[-] Error trying to connect to the host %s:%d\n",inet_ntoa(server.sin_addr),htons(server.sin_port));
        close(connection);
        return 1;
    }

    fprintf(stderr,"[+] Connected with %s:%d\n",inet_ntoa(server.sin_addr),htons(server.sin_port));

    // SIGTERM/SIGINT (c/streaming stops us with SIGTERM): leave the loop and print the counters
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = on_term;
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGINT,  &sa, NULL);


    // ----------- mem read --------------------------------------------

    int fd;

    char *name = "/dev/mem";
    // clean buffer
    bzero(buf_i, sizeof(buf_i));

    // Open memory
    if((fd = open(name, O_RDWR)) < 0) {
        perror("[-] Error trying to open /dev/mem");
        return 1;
    }

    long osc_addr, osc_size = sysconf(_SC_PAGESIZE);
    osc_addr = OSC_FPGA_BASE_ADDR & (~(osc_size-1));
    osc_ptr = mmap(NULL, OSC_FPGA_BASE_SIZE , PROT_READ | PROT_WRITE, MAP_SHARED, fd , osc_addr);

    if((void *)osc_ptr == MAP_FAILED) {
        fprintf(stderr, "[-] osc mmap() failed: %d\n", errno);
        return -1;
    }

    // Lock-in page (only stream_rate is read). Optional: without it the decimation is taken as 128.
    void *lock_ptr = mmap(NULL, osc_size, PROT_READ, MAP_SHARED, fd, LOCK_FPGA_BASE_ADDR);
    volatile uint32_t *StreamRate = NULL;
    volatile uint32_t *StreamCmd  = NULL;
    if((void *)lock_ptr == MAP_FAILED) {
        fprintf(stderr, "[-] lock mmap() failed: %d (decimation taken as 128, stream_cmd not checked)\n", errno);
        lock_ptr = NULL;
    } else {
        StreamRate = (volatile uint32_t *)((char *)lock_ptr + LOCK_STREAM_RATE_OFF);
        StreamCmd  = (volatile uint32_t *)((char *)lock_ptr + LOCK_STREAM_CMD_OFF);
    }

    // Oscilloscope useful registers
    // volatile: FPGA registers, must be read/written on every access
    volatile uint32_t *conf   = NULL ;
    conf             = osc_ptr + OSC_CONF ;

    volatile uint32_t *CurWpt = NULL ;
    CurWpt           = osc_ptr + OSC_PNT ;

    volatile uint32_t *WeCnt  = osc_ptr + OSC_WE_CNT ;


    volatile uint32_t *vecA = NULL ;
    volatile uint32_t *vecB = NULL ;

    vecA = osc_ptr +  OSC_FPGA_CH_A_OFFSET ;  // channel A
    vecB = osc_ptr +  OSC_FPGA_CH_B_OFFSET ;  // channel B


    unsigned long fpga_addr       = 0 ;   // next FPGA buffer address to read
    unsigned long buf_addr        = 0 ;
    unsigned long n_read          = 0 ;
    unsigned long dec             = read_dec(StreamRate);

    unsigned long wp_last         = 0 ;   // last accepted WP (monotonic)
    uint32_t      we_last         = 0 ;   // last "samples written" counter
    uint32_t      we_wp           = 0 ;   // counter read together with wp_last
    uint32_t      we_rd           = 0 ;   // counter value (sample index since the arm) of the sample at fpga_addr
    int           cmd_stop        = 0 ;   // stream_cmd went to 0
    long long     t_now           = 0 ;
    long long     t_wp_change     = 0 ;   // last time the WP moved
    long long     t_ok            = 0 ;   // time of the last accepted WP read
    long long     t_dec           = 0 ;   // last read of the decimation
    long long     t_stats         = 0 ;
    unsigned long events_printed  = 0 ;

    // Start: reset + arm
    scope_rearm(conf);
    t_now = t_wp_change = t_ok = t_dec = t_stats = now_ns();

    while( !stop_req ) {
        // ---- stream_cmd = 0: the streaming was stopped (do not wait for the SIGTERM) ----
        if( StreamCmd && FPGA_RD(StreamCmd) == 0 ){
            cmd_stop = 1;
            break;
        }

        // ---- write pointer: three reads that must agree (each equal or slightly ahead) ----
        uint32_t      we_a = FPGA_RD(WeCnt);
        unsigned long wp_a = FPGA_RD(CurWpt) & WP_MASK ;
        unsigned long wp_b = FPGA_RD(CurWpt) & WP_MASK ;
        unsigned long wp_c = FPGA_RD(CurWpt) & WP_MASK ;
        uint32_t      we_b = FPGA_RD(WeCnt);
        t_now = now_ns();

        if( t_now - t_dec > 100000000LL ){       // decimation, every 100 ms
            dec   = read_dec(StreamRate);
            t_dec = t_now;
        }
        // sample period in ns (8 ns per ADC clock)
        long long t_smp = 8LL * (long long)dec;

        int rearm = 0;    // 1: scope armed/reset by someone else, 2: WP stopped

        if( ((wp_b - wp_a) & WP_MASK) > WP_SAME_MAX || ((wp_c - wp_b) & WP_MASK) > WP_SAME_MAX ){
            cnt_wp_glitch++;
            continue;
        }

        if( we_a < we_last || we_b < we_a ){
            // ---- scope armed/reset by someone else (written counter went down) ----
            cnt_ext_arm++;
            fprintf(stderr, "[!] scope armed/reset by someone else (written %u -> %u -> %u): re-arming\n",
                    we_last, we_a, we_b);
            rearm  = 1;
            n_read = 0;
        } else {
            we_last = we_b;

            unsigned long adv = (wp_a - wp_last) & WP_MASK ;
            long long pend    = (long long)((wp_last - fpga_addr) & WP_MASK);   // unread after the last read
            // unread samples per the "samples written" counter (-1: unknown, counter saturated)
            int       we_ok   = (we_b != WE_SAT);
            long long unread  = we_ok ? (long long)we_b - (long long)we_rd : -1;
            // WP more than half a buffer ahead (it looks "behind"): real if the counter says so
            int       far     = (adv >= WP_HALF && we_ok && (long long)we_a - (long long)we_wp >= WP_HALF);
            long long t_lag   = (t_now - t_ok) / t_smp + pend;
            if( unread > (long long)(OSC_FPGA_SIG_LEN - WP_SKIP_AT) ){
                // ---- overrun (counter): skip the oldest unread samples, go on WP_SKIP_TO behind the newest ----
                unsigned long skip = (unsigned long)(unread - WP_SKIP_TO);
                cnt_overrun++;
                cnt_resync++;
                cnt_lost += skip;
                if( cnt_overrun <= 20 || (cnt_overrun % 1000) == 0 )
                    fprintf(stderr, "[!] overrun #%lu: %lld unread samples (%lld us since the last read): %lu skipped\n",
                            cnt_overrun, unread, (t_now - t_ok)/1000LL, skip);
                fpga_addr = (fpga_addr + skip) & WP_MASK ;
                we_rd    += (uint32_t)skip ;
                unread    = WP_SKIP_TO ;
                if( adv > 0 && (adv < WP_HALF || far) ){
                    wp_last     = wp_a ;
                    we_wp       = we_a ;
                    t_wp_change = t_now ;
                } else if( adv > 0 ){
                    wp_a = wp_last;             // bad WP read: nothing is read this turn
                }
            } else if( !we_ok && t_lag > (long long)(OSC_FPGA_SIG_LEN - 512) ){
                // ---- overrun (time, counter saturated): too long since the last read ----
                cnt_overrun++;
                if( cnt_overrun <= 20 || (cnt_overrun % 1000) == 0 )
                    fprintf(stderr, "[!] overrun #%lu: %lld us without reading (%lld samples of %lld ns)\n",
                            cnt_overrun, (t_now - t_ok)/1000LL, t_lag, t_smp);
                fpga_addr   = wp_a ;    // older samples may be overwritten: restart at the WP
                wp_last     = wp_a ;
                we_wp       = we_a ;
                t_wp_change = t_now ;
                cnt_resync++;
            } else if( adv >= WP_HALF && !far ){
                // ---- WP behind the last one: bad read, keep the last WP ----
                cnt_wp_back++;
                wp_a = wp_last;
            } else if( adv > 0 ){
                wp_last     = wp_a ;
                we_wp       = we_a ;
                t_wp_change = t_now ;
            } else if( t_now - t_wp_change > STALL_NS && t_now - t_wp_change > 64 * t_smp ){
                // ---- WP stopped (scope reset or stopped by a trigger) ----
                fprintf(stderr, "[!] write pointer stopped at %lu for %lld ms: re-arming the scope\n",
                        wp_a, (t_now - t_wp_change)/1000000LL);
                rearm = 2;
            }
            t_ok = t_now ;

            // fpga_addr is never ahead of wp_last, so this is the number of unread samples
            unsigned long fpga_diff_addr = (wp_a - fpga_addr) & WP_MASK ;

            // more than half a buffer to read is accepted only if the counter agrees with the WP
            int diff_ok = fpga_diff_addr < WP_HALF || (unread >= 0 && (long long)fpga_diff_addr <= unread + WP_MARGIN);

            // ---- read up to WP - WP_MARGIN. If it stopped: up to the WP included (the last sample
            //      written), unless nothing was written since the arm ----
            if( rearm )
                n_read = (we_b > 0 && diff_ok) ? fpga_diff_addr + 1 : 0 ;
            else
                n_read = (fpga_diff_addr > WP_MARGIN && diff_ok) ? fpga_diff_addr - WP_MARGIN : 0 ;
        }

        // Flush first if this read would not fit in buf_i (n_read <= OSC_FPGA_SIG_LEN <= SEND_BUF_LEN,
        // so after the flush it always fits)
        if( buf_addr + n_read > SEND_BUF_LEN ){
            send_all(connection, buf_addr);
            buf_addr = 0 ;
        }
        unsigned long buf_addr_blk = buf_addr ;   // start of this block in buf_i
        unsigned long n_done       = 0 ;          // samples of the block read so far

        // read in sub-blocks of RD_SUB samples
        while( n_done < n_read ){
            unsigned long m    = n_read - n_done ;
            if( m > RD_SUB ) m = RD_SUB ;
            unsigned long b0   = buf_addr ;
            uint32_t      s0   = we_rd ;          // index of the first sample of the sub-block
            unsigned long k ;
            for( k = 0 ; k < m ; k++ ){
                // 14 ADC bits per channel, as in the 0.9x FPGA (the 2.0 FPGA of
                // v2.3.10 returns the samples sign-extended to 16 bits)
                buf_i[buf_addr] =  (FPGA_RD(&vecA[fpga_addr]) & 0x3fff) + ((FPGA_RD(&vecB[fpga_addr]) & 0x3fff)<<16 ) ;
                buf_addr++    ;
                fpga_addr++   ; fpga_addr = fpga_addr & WP_MASK ;
            }
            we_rd  += (uint32_t)m ;
            n_done += m ;

            // ---- samples of the sub-block that the writer may have overwritten during the read ----
            uint32_t we_post = FPGA_RD(WeCnt);
            if( we_b != WE_SAT && we_post != WE_SAT && we_post >= we_b ){
                long long n_bad = (long long)we_post - (long long)(OSC_FPGA_SIG_LEN - WP_GUARD) - (long long)s0;
                if( n_bad > 0 ){
                    if( n_bad > (long long)m ) n_bad = (long long)m;
                    memmove(&buf_i[b0], &buf_i[b0 + n_bad], (m - (unsigned long)n_bad) * sizeof(buf_i[0]));
                    buf_addr -= (unsigned long)n_bad;
                    cnt_lost += (unsigned long long)n_bad;
                    cnt_overrun++;
                    if( cnt_overrun <= 20 || (cnt_overrun % 1000) == 0 )
                        fprintf(stderr, "[!] overrun #%lu: %lld samples overwritten while reading (dropped)\n",
                                cnt_overrun, n_bad);
                    break;   // the writer reached the reader: the next turn skips ahead
                }
            }
        }

        // ---- stream_cmd went to 0 during the read: the scope may be reconfigured, drop the block ----
        if( n_done > 0 && StreamCmd && FPGA_RD(StreamCmd) == 0 ){
            cnt_end_drop += buf_addr - buf_addr_blk;
            buf_addr = buf_addr_blk;
            cmd_stop = 1;
            break;
        }
        cnt_samples += buf_addr - buf_addr_blk;

        // if surpass the theshold, send to server
        if(buf_addr>=send_min_len){
             send_all(connection, buf_addr); // sending
             buf_addr = 0 ;
        }

        if( rearm ){
            cnt_rearm++;
            scope_rearm(conf);
            fpga_addr = 0 ;
            wp_last   = 0 ;
            we_last   = 0 ;
            we_wp     = 0 ;
            we_rd     = 0 ;
            t_now = t_wp_change = t_ok = now_ns();
            continue;
        }

        // ---- counters to stderr when something happened ----
        unsigned long events = cnt_wp_glitch + cnt_wp_back + cnt_resync + cnt_ext_arm + cnt_rearm + cnt_overrun;
        if( events != events_printed && t_now - t_stats > STATS_NS ){
            print_stats("+");
            events_printed = events;
            t_stats        = t_now;
        }

        // ---- few samples available: sleep (up to 1/8 of the buffer time, max 1 ms) ----
        if( n_read < 1024 ){
            long long us = (OSC_FPGA_SIG_LEN/8) * t_smp / 1000LL;
            if( us > 1000 ) us = 1000;
            if( us >= 20 )  usleep((useconds_t)us);
        }

    }


    if(cmd_stop)
        fprintf(stderr, "[+] stream_cmd = 0: stopping\n");
    if(buf_addr > 0)
        send_all(connection, buf_addr);
    munmap(osc_ptr, OSC_FPGA_BASE_SIZE);
    if(lock_ptr) munmap(lock_ptr, osc_size);
    close(connection);
    // ----------- mem read --------------------------------------------

    print_stats("+ Finished sending");

    return 0;
}
