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



#define LOCK_FPGA_BASE_ADDR 0x40600000
#define LOCK_FPGA_BASE_SIZE 0x100000

#define STREAM_CMD "/opt/redpitaya/www/apps/lock_in_mtm/c/stream_tcp_osc_cmd"

#define DEBUG 1


int main(int argc, char **argv){
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

    long unsigned int *stream_ip       = lock_ptr + 212   ;
    long unsigned int *stream_port     = lock_ptr + 216   ;
    long unsigned int *stream_rate     = lock_ptr + 220   ;
    long unsigned int *stream_status   = lock_ptr + 224   ;
    long unsigned int *stream_cmd      = lock_ptr + 228   ;
    //long unsigned int *stream_connect  = lock_ptr + 232   ;

    // Print FPGA reg values
    #ifdef DEBUG
        fprintf(stderr, "[+] stream_ip     : %lu\n", *stream_ip );
        fprintf(stderr, "[+] stream_port   : %lu\n", *stream_port );
        fprintf(stderr, "[+] stream_rate   : %lu\n", *stream_rate );
        fprintf(stderr, "[+] stream_status : %lu\n", *stream_status );
        fprintf(stderr, "[+] stream_cmd    : %lu\n", *stream_cmd );
        //fprintf(stderr, "[+] stream_connect: %lu\n", *stream_connect );
    #endif


    // Process parameters -----------------------------------------------------------------------

    // Get IP value
    char    ip_addr[ 15];
    bzero(  ip_addr, 15);
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

    if(pid == 0) { // The parent process will do the streaming.
        setpgid(0, 0);
        execl(STREAM_CMD,STREAM_CMD, ip_addr , port_s , "64" , NULL);

        printf("[-] Something terminated early\n");
        exit(127);
    } else{  // The child, will stop it.
        while(1){
            if( 1> *stream_cmd) {  // If stream_cmd goes to 0, stop the streaming
                kill(-pid, SIGTERM);
                sleep(0.5);
                kill(-pid, SIGKILL);

                #ifdef DEBUG
                    perror("[+] Finishing streaming\n");
                #endif
                break;
            }
        }
    }





    // Clean the lock_ptr pointer
    munmap(lock_ptr, sysconf(_SC_PAGESIZE));

    return 0;
}
