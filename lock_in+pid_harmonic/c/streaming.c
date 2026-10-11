#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
//#include <arpa/inet.h>
//#include <sys/socket.h>
//#include <netinet/in.h>
//#include <netdb.h>

#include <stdint.h>
#include <sys/mman.h>
#include <fcntl.h>

#include <errno.h>


#include <signal.h>
#include <sys/wait.h>



#define LOCK_FPGA_BASE_ADDR 0x40600000
#define LOCK_FPGA_BASE_SIZE 0x100000

#define STREAM_CMD "/opt/redpitaya/www/apps/lock_in+pid_harmonic/c/stream_tcp_osc_cmd"

#define DEBUG 1


int main(int argc, char **argv){
    // v2.3.18 (as lock_in+pid_harmonic2 v2.4.3): close every inherited fd except stdin/stdout/stderr.
    // c/stream_start.sh is run by the nginx worker (os.execute) and its fds (client sockets, listening
    // sockets, logs) are not close-on-exec: without this, this process and stream_tcp_osc_cmd kept them
    // open while streaming (sockets left in CLOSE-WAIT, listening sockets held after an nginx restart).
    {
        long maxfd = sysconf(_SC_OPEN_MAX);
        int  i;
        if(maxfd < 0 || maxfd > 65536) maxfd = 65536;
        for(i = 3; i < maxfd; i++) close(i);
        errno = 0;   // EBADF of the closed fds: the perror() at the end printed "Bad file descriptor"
    }

    // mapping memory addreses for FPGA registers to variables ------------------------------

    // Open Linux memory device
    char *name = "/dev/mem";
    int fd;

    if((fd = open(name, O_RDWR)) < 0) {
        perror("[-] Error trying to open /dev/mem");
        return 1;
    }

    // Pointer for lock block memory addreses
    void *lock_ptr ;
    long lock_size = sysconf(_SC_PAGESIZE);
    long lock_addr = LOCK_FPGA_BASE_ADDR & (~(lock_size-1));
    long lock_off  = LOCK_FPGA_BASE_ADDR - lock_addr;

    //        *mmap(*addr,             length,       prot            , flags     , fd ,  offset  );
    lock_ptr = mmap(NULL, LOCK_FPGA_BASE_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd , lock_addr);

    if((void *)lock_ptr == MAP_FAILED) {
        fprintf(stderr, "[-] lock mmap() failed: %d\n", errno);
        return -1;
    }

    volatile long unsigned int *stream_ip       = lock_ptr + 380   ;
    volatile long unsigned int *stream_port     = lock_ptr + 384   ;
    volatile long unsigned int *stream_rate     = lock_ptr + 388   ;
    volatile long unsigned int *stream_cmd      = lock_ptr + 392   ;
    //long unsigned int *stream_connect  = lock_ptr + 232   ;

    // Print FPGA reg values
    #ifdef DEBUG
        fprintf(stderr, "[+] stream_ip     : %lu\n", *stream_ip );
        fprintf(stderr, "[+] stream_port   : %lu\n", *stream_port );
        fprintf(stderr, "[+] stream_rate   : %lu\n", *stream_rate );
        fprintf(stderr, "[+] stream_cmd    : %lu\n", *stream_cmd );
        //fprintf(stderr, "[+] stream_connect: %lu\n", *stream_connect );
    #endif


    // Process parameters -----------------------------------------------------------------------

    // Get IP value
    char    ip_addr[ 16];   // "255.255.255.255" + NUL
    bzero(  ip_addr, 16);
    sprintf(ip_addr,  "%lu.%lu.%lu.%lu"  , ((*stream_ip)>> 8*0)&255    ,
                                           ((*stream_ip)>> 8*1)&255    ,
                                           ((*stream_ip)>> 8*2)&255    ,
                                           ((*stream_ip)>> 8*3)&255    );
    // Get TCP port
    char  port_s[ 15] ;
    bzero(port_s, 15);
    sprintf(port_s , "%lu" , *stream_port );


    #ifdef DEBUG
        fprintf(stderr,"[+] Server address: %s\n", ip_addr) ;
        fprintf(stderr,"[+] Server port   : %s\n", port_s) ;
        fflush( stderr );
    #endif



    // wait unitl streaming start
    while( 0 == *stream_cmd ) usleep(10000);

    #ifdef DEBUG
        fprintf(stderr,"[+] Streaming started\n") ;
        fflush( stderr );
    #endif


    // We fork the process.
    pid_t pid = fork();
    if(pid < 0) {
        perror("[-] fork");
        return 1;
    }

    if(pid == 0) { // The parent process will do the streaming.
        setpgid(0, 0);
        execl(STREAM_CMD,STREAM_CMD, ip_addr , port_s , "64" , NULL);

        printf("[-] Something terminated early\n");
        exit(127);
    } else{  // The child, will stop it.
        while(1){
            // v2.3.10: if stream_tcp_osc_cmd ended by itself (connection refused/closed), end too,
            // so that check_streaming shows the real state
            if( waitpid(pid, NULL, WNOHANG) == pid ){
                #ifdef DEBUG
                    fprintf(stderr, "[+] stream_tcp_osc_cmd ended\n");
                #endif
                break;
            }
            if( 1> *stream_cmd) {  // If stream_cmd goes to 0, stop the streaming
                kill(-pid, SIGTERM);
                usleep(500000);   // was sleep(0.5), i.e. sleep(0)
                kill(-pid, SIGKILL);

                #ifdef DEBUG
                    perror("[+] Finishing streaming\n");
                #endif
                break;
            }
            usleep(10000);   // poll stream_cmd every 10 ms (it was a busy loop at 100 % CPU)
        }
    }





    // Clean the lock_ptr pointer
    munmap(lock_ptr, LOCK_FPGA_BASE_SIZE);

    return 0;
}
