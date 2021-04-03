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

#include <errno.h>


#define OSC_CONF   0
#define OSC_TRG    4
#define OSC_DEC   20
#define OSC_PNT   24



#define OSC_FPGA_BASE_ADDR 0x40100000
#define OSC_FPGA_BASE_SIZE 0x30000
#define OSC_FPGA_SIG_LEN   (16*1024)


#define OSC_FPGA_CH_A_OFFSET 0x10000
#define OSC_FPGA_CH_B_OFFSET 0x20000


#define BUF_LEN  16384


int main(int argc, char **argv){
    if(argc<3)
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
    
    
  
    connection = socket(AF_INET, SOCK_STREAM, 0);         // get TCP socket
    port   = (atoi(argv[2]));                             // get connection port
    bzero((char *)&server, sizeof((char *)&server));
                                                                          //La función bzero() es como memset() pero inicializando a 0 todas la variables
    
    server.sin_family = AF_INET;                          // Server protocol TCP
    server.sin_port   = htons(port);                      // Server port
    bcopy((char *)client->h_addr, (char *)&server.sin_addr.s_addr, sizeof(client->h_length));  // Get ip adress from client object

    if(connect(connection,(struct sockaddr *)&server, sizeof(server)) < 0){
        fprintf(stderr,"[-] Error trying to connect to the host %s:%d\n",inet_ntoa(server.sin_addr),htons(server.sin_port));
        close(connection);
        return 1;
    }
    
    fprintf(stderr,"[+] Connected with %s:%d\n",inet_ntoa(server.sin_addr),htons(server.sin_port));
    
    
    
    // ----------- mem read --------------------------------------------
    
    char       buf_c[BUF_LEN*4] ; 
    uint32_t * buf_i  = buf_c  ;
    
    int fd;
    
    char *name = "/dev/mem";
    // clean buffer
    bzero(buf_c, BUF_LEN*4);

    // Open memory
    if((fd = open(name, O_RDWR)) < 0) {
        perror("[-] Error trying to open /dev/mem");
        return 1;
    }

    long osc_addr, osc_off, osc_size = sysconf(_SC_PAGESIZE);
    osc_addr = OSC_FPGA_BASE_ADDR & (~(osc_size-1));
    osc_off  = OSC_FPGA_BASE_ADDR - osc_addr;
    osc_ptr = mmap(NULL, OSC_FPGA_BASE_SIZE , PROT_READ | PROT_WRITE, MAP_SHARED, fd , osc_addr);
    
    if((void *)osc_ptr == MAP_FAILED) {
        fprintf(stderr, "[-] osc mmap() failed: %d\n", errno);
        return -1;
    }
    
    // Oscilloscope useful registers
    uint32_t *conf   = NULL ;
    conf             = osc_ptr + OSC_CONF ;
    
    uint32_t *Dec    = NULL ;
    Dec              = osc_ptr + OSC_DEC ;
    
    uint32_t *CurWpt = NULL ;
    CurWpt           = osc_ptr + OSC_PNT ;
    
    
    uint32_t *vecA = NULL ;
    uint32_t *vecB = NULL ;

    vecA = osc_ptr +  OSC_FPGA_CH_A_OFFSET ;  // channel A
    vecB = osc_ptr +  OSC_FPGA_CH_B_OFFSET ;  // channel B

    
    unsigned long N               = 0 ;
    unsigned long fpga_addr_now   = 0 ;
    unsigned long buf_addr        = 0 ;
    unsigned long fpga_addr       = 0 ;
             long fpga_diff_addr  = 0 ;
             
    unsigned long buf_addr_top    = 0 ;
    
        
    
    // buffer cleaning
    *conf  = 2  ;   // start clearing
    usleep(300) ;
        
    // Start recording
    *conf = 1;   // start recording
    
    usleep(3) ; 
    
    do {
        // redding actual write pointer position
        fpga_addr_now   = *CurWpt  ;
        fpga_diff_addr  = ( fpga_addr_now - fpga_addr + 0x4000  ) & 0x03fff ;
        buf_addr_top    = buf_addr + fpga_diff_addr ;
                
        // iteration until reading that position
        while ( buf_addr < buf_addr_top ){
            
            // Storing values in buf_i
            buf_i[buf_addr] =  vecA[fpga_addr] + (vecB[fpga_addr]<<16 ) ;

            // counters incrementation
            buf_addr++    ;
            fpga_addr++   ; fpga_addr = fpga_addr & 0x03fff ;
        }
        
        // if surpass the theshold, send to server
        if(buf_addr>=send_min_len){
             send(connection, buf_c, (buf_addr-0)<<2 , 0); // sending
             buf_addr = 0 ;
        }
        
    } while( 1 ) ;

    
    munmap(osc_ptr, sysconf(_SC_PAGESIZE));
    // ----------- mem read --------------------------------------------
    
    perror("[+] Finished sending\n");
    
    return 0;
}
