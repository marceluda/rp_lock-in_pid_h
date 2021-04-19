// By Javier Elaskar
//#include <unistd.h>


#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>

#define SIZE 1048576



char buffer[SIZE];


void write_file(int sockfd){
    int n;
    //uint16_t sign_bit ;
    FILE *fp;
    // char *filename = "recv.txt";

    //uint16_t * buffer_i  = buffer  ;


    time_t t     = time(NULL);
    struct tm tm = *localtime(&t);
    //printf("now: %d-%02d-%02d %02d:%02d:%02d\n", tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);


    char filename[21];

    sprintf( filename , "%d-%02d-%02d_%02d%02d%02d.bin", tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec) ;


    fp = fopen(filename, "w");

    if(fp == NULL){
        printf("[-] Error opening file");
        exit(1);
    }

    int no_data;

    char  sign;

    while (1) {
        n = recv(sockfd, buffer, SIZE, 0);
        if (n <= 0) no_data++ ;
        if (no_data > 1000){
            break;
            return;
        }
        // fprintf(stderr,"%d\n" , n );

        // Next for is for fixing negative numbers encoding
        // from 14bit to 16 bit
        for(int jj=1 ; jj<n ; jj+=2 ){
            if ( (buffer[jj] & 0x20)!=0 ){
                buffer[jj] =   buffer[jj] | 0xc0 ;
            }
        }

        fwrite( buffer , 1 , n, fp );
        memset(buffer, 0, SIZE);
    }

    printf("[+] File Written: %s\n", filename );

    fclose(fp);
    return;
}

int main(){


    WSADATA wsaData;
    WSAStartup(0x0202, &wsaData);
    char *ip = "192.168.2.140";
    int port = 6000;
    int err;


    int                sockfd, connection;
    struct sockaddr_in server_addr, new_addr;
    socklen_t          addr_size;
    //char               buffer[SIZE];

    memset(buffer, 0, SIZE);


    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if(sockfd < 0) {
        perror("[-] Error in socket");
        exit(1);
    }
    printf("[+] Server socket created successfully.\n");

    server_addr.sin_family      = AF_INET;
    server_addr.sin_port        = htons(port);
    server_addr.sin_addr.s_addr = inet_addr(ip);

    err = bind(sockfd, (struct sockaddr*)&server_addr, sizeof(server_addr));
    if(err < 0) {
        perror("[-] Error in bind");
        exit(1);
    }
    printf("[+] Binding successfull.\n");

    if(listen(sockfd, 10) == 0){
        printf("[+] Listening....\n");
    }else{
        perror("[-] Error in listening");
        exit(1);
    }

    addr_size = sizeof(new_addr);

    connection = accept(sockfd, (struct sockaddr*)&new_addr, &addr_size);


    write_file( connection );
    printf("[+]Data written in the file successfully.\n");
    closesocket( connection );
    WSACleanup();

    return 0;
}
