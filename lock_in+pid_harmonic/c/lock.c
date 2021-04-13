#include <assert.h>
#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <stdint.h>
#include <sys/mman.h>
#include <fcntl.h>

#include <errno.h>


#include <unistd.h>
//#include <signal.h>



#define PARAMS_NUM 99






#define LOCK_FPGA_BASE_ADDR 0x40600000
#define LOCK_FPGA_BASE_SIZE 0x100000





/* Registers description structure */
typedef struct registers_s {
    char  *name;
    int    index;
    int    is_signed;
    int    read_only;
    float  min_val;
    float  max_val;
} registers_t;



static registers_t registers[PARAMS_NUM] = {
    // [LOCKREGS DOCK]
    { "oscA_sw"                ,   0, 0, 0,          0,         31 },
    { "oscB_sw"                ,   1, 0, 0,          0,         31 },
    { "osc_ctrl"               ,   2, 0, 0,          0, 4294967295 },
    { "trig_sw"                ,   3, 0, 0,          0,        255 },
    { "out1_sw"                ,   4, 0, 0,          0,         15 },
    { "out2_sw"                ,   5, 0, 0,          0,         15 },
    { "lock_control"           ,   6, 0, 0,          0,       2047 },
    { "lock_feedback"          ,   7, 0, 1,          0,       2047 },
    { "lock_trig_val"          ,   8, 1, 0,      -8192,       8191 },
    { "lock_trig_time"         ,   9, 0, 0,          0, 4294967295 },
    { "lock_trig_sw"           ,  10, 0, 0,          0,         15 },
    { "rl_error_threshold"     ,  11, 0, 0,          0,       8191 },
    { "rl_signal_sw"           ,  12, 0, 0,          0,          7 },
    { "rl_signal_threshold"    ,  13, 1, 0,      -8192,       8191 },
    { "rl_config"              ,  14, 0, 0,          0,          7 },
    { "rl_state"               ,  15, 0, 1,          0,         31 },
    { "sf_jumpA"               ,  16, 1, 0,      -8192,       8191 },
    { "sf_jumpB"               ,  17, 1, 0,      -8192,       8191 },
    { "sf_config"              ,  18, 0, 0,          0,         31 },
    { "signal_sw"              ,  19, 0, 0,          0,          7 },
    { "signal_i"               ,  20, 1, 1,      -8192,       8191 },
    { "sg_amp0"                ,  21, 0, 0,          0,         31 },
    { "sg_amp1"                ,  22, 0, 0,          0,         15 },
    { "sg_amp2"                ,  23, 0, 0,          0,         15 },
    { "sg_amp3"                ,  24, 0, 0,          0,         15 },
    { "lpf_F0"                 ,  25, 0, 0,          0,         63 },
    { "lpf_F1"                 ,  26, 0, 0,          0,         63 },
    { "lpf_F2"                 ,  27, 0, 0,          0,         63 },
    { "lpf_F3"                 ,  28, 0, 0,          0,         63 },
    { "error_sw"               ,  29, 0, 0,          0,          7 },
    { "error_offset"           ,  30, 1, 0,      -8192,       8191 },
    { "error"                  ,  31, 1, 1,      -8192,       8191 },
    { "error_mean"             ,  32, 1, 1, -2147483648, 2147483647 },
    { "error_std"              ,  33, 1, 1, -2147483648, 2147483647 },
    { "mod_out1"               ,  34, 1, 0,      -8192,       8191 },
    { "mod_out2"               ,  35, 1, 0,      -8192,       8191 },
    { "gen_mod_phase"          ,  36, 0, 0,          0,       2519 },
    { "gen_mod_hp"             ,  37, 0, 0,          0,      16383 },
    { "ramp_A"                 ,  38, 1, 1,      -8192,       8191 },
    { "ramp_B"                 ,  39, 1, 1,      -8192,       8191 },
    { "ramp_step"              ,  40, 0, 0,          0, 4294967295 },
    { "ramp_low_lim"           ,  41, 1, 0,      -8192,       8191 },
    { "ramp_hig_lim"           ,  42, 1, 0,      -8192,       8191 },
    { "ramp_reset"             ,  43, 0, 0,          0,          1 },
    { "ramp_enable"            ,  44, 0, 0,          0,          1 },
    { "ramp_direction"         ,  45, 0, 0,          0,          1 },
    { "ramp_sawtooth"          ,  46, 0, 0,          0,          1 },
    { "ramp_B_factor"          ,  47, 1, 0,      -4096,       4096 },
    { "sin_ref"                ,  48, 1, 1,      -8192,       8191 },
    { "cos_ref"                ,  49, 1, 1,      -8192,       8191 },
    { "cos_1f"                 ,  50, 1, 1,      -8192,       8191 },
    { "cos_2f"                 ,  51, 1, 1,      -8192,       8191 },
    { "cos_3f"                 ,  52, 1, 1,      -8192,       8191 },
    { "in1"                    ,  53, 1, 1,      -8192,       8191 },
    { "in2"                    ,  54, 1, 1,      -8192,       8191 },
    { "out1"                   ,  55, 1, 1,      -8192,       8191 },
    { "out2"                   ,  56, 1, 1,      -8192,       8191 },
    { "oscA"                   ,  57, 1, 1,      -8192,       8191 },
    { "oscB"                   ,  58, 1, 1,      -8192,       8191 },
    { "X_28"                   ,  59, 1, 1, -134217728,  134217727 },
    { "Y_28"                   ,  60, 1, 1, -134217728,  134217727 },
    { "F1_28"                  ,  61, 1, 1, -134217728,  134217727 },
    { "F2_28"                  ,  62, 1, 1, -134217728,  134217727 },
    { "F3_28"                  ,  63, 1, 1, -134217728,  134217727 },
    { "cnt_clk"                ,  64, 0, 1,          0, 4294967295 },
    { "cnt_clk2"               ,  65, 0, 1,          0, 4294967295 },
    { "read_ctrl"              ,  66, 0, 0,          0,          7 },
    { "pidA_sw"                ,  67, 0, 0,          0,         31 },
    { "pidA_PSR"               ,  68, 0, 0,          0,          4 },
    { "pidA_ISR"               ,  69, 0, 0,          0,          9 },
    { "pidA_DSR"               ,  70, 0, 0,          0,          5 },
    { "pidA_SAT"               ,  71, 0, 0,          0,         13 },
    { "pidA_sp"                ,  72, 1, 0,      -8192,       8191 },
    { "pidA_kp"                ,  73, 1, 0,      -8192,       8191 },
    { "pidA_ki"                ,  74, 1, 0,      -8192,       8191 },
    { "pidA_kd"                ,  75, 1, 0,      -8192,       8191 },
    { "pidA_in"                ,  76, 1, 1,      -8192,       8191 },
    { "pidA_out"               ,  77, 1, 1,      -8192,       8191 },
    { "pidA_ctrl"              ,  78, 0, 0,          0,          7 },
    { "ctrl_A"                 ,  79, 1, 1,      -8192,       8191 },
    { "pidB_sw"                ,  80, 0, 0,          0,         31 },
    { "pidB_PSR"               ,  81, 0, 0,          0,          4 },
    { "pidB_ISR"               ,  82, 0, 0,          0,          9 },
    { "pidB_DSR"               ,  83, 0, 0,          0,          5 },
    { "pidB_SAT"               ,  84, 0, 0,          0,         13 },
    { "pidB_sp"                ,  85, 1, 0,      -8192,       8191 },
    { "pidB_kp"                ,  86, 1, 0,      -8192,       8191 },
    { "pidB_ki"                ,  87, 1, 0,      -8192,       8191 },
    { "pidB_kd"                ,  88, 1, 0,      -8192,       8191 },
    { "pidB_in"                ,  89, 1, 1,      -8192,       8191 },
    { "pidB_out"               ,  90, 1, 1,      -8192,       8191 },
    { "pidB_ctrl"              ,  91, 0, 0,          0,          7 },
    { "ctrl_B"                 ,  92, 1, 1,      -8192,       8191 },
    { "aux_A"                  ,  93, 1, 0,      -8192,       8191 },
    { "aux_B"                  ,  94, 1, 0,      -8192,       8191 },
    { "stream_ip"              ,  95, 0, 0,          0, 4294967295 },
    { "stream_port"            ,  96, 0, 0,          0, 4294967295 },
    { "stream_rate"            ,  97, 0, 0,          0,      65536 },
    { "stream_cmd"             ,  98, 0, 0,          0, 4294967295 }
    // [LOCKREGS DOCK END]
};



// Function for string to int conversion **********************************
typedef enum {
    STR2INT_SUCCESS,
    STR2INT_OVERFLOW,
    STR2INT_UNDERFLOW,
    STR2INT_INCONVERTIBLE
} str2int_errno;

/* Convert string s to int out.
 *
 * @param[out] out The converted int. Cannot be NULL.
 *
 * @param[in] s Input string to be converted.
 *
 *     The format is the same as strtol,
 *     except that the following are inconvertible:
 *
 *     - empty string
 *     - leading whitespace
 *     - any trailing characters that are not part of the number
 *
 *     Cannot be NULL.
 *
 * @param[in] base Base to interpret string in. Same range as strtol (2 to 36).
 *
 * @return Indicates if the operation succeeded, or why it failed.
 */
str2int_errno str2int(int32_t *out, char *s, int base) {
    char *end;
    if (s[0] == '\0' || isspace(s[0]))
        return STR2INT_INCONVERTIBLE;
    errno = 0;
    long l = strtol(s, &end, base);
    /* Both checks are needed because INT_MAX == LONG_MAX is possible. */
    if (l > INT_MAX || (errno == ERANGE && l == LONG_MAX))
        return STR2INT_OVERFLOW;
    if (l < INT_MIN || (errno == ERANGE && l == LONG_MIN))
        return STR2INT_UNDERFLOW;
    if (*end != '\0')
        return STR2INT_INCONVERTIBLE;
    *out = l;
    return STR2INT_SUCCESS;
}


//***************************************************************************


// For memory reading
char      *name = "/dev/mem";
int        fd;
void      *lock_ptr ;
int32_t   *lock ;




/* Reading FPGA register of lock module
 *
 * @param[index] number of the register
 *
 * @return Returns the register value
 *
 **/
void read_reg(int index){
    printf("%s:%d\n" , registers[index].name , lock[index] );
}


/* Write FPGA register value of lock module
 *
 * @param[index] number of the register
 *
 * @param[val] value to be written
 *
 * @return Returns the register value
 *
 **/
void write_reg(int index, int32_t val ){
    lock[index] = val ;
    printf("%s:%d\n" , registers[index].name , lock[index] );
}



/* Get index number from parameter name
 *
 * @param[name] name of the parameter
*
 * @return Returns the register index
 *
 **/
int reg_name_to_index(char *name){
    for(int jj=0; jj<PARAMS_NUM ; jj++){
        if (strcmp(name, registers[jj].name ) == 0) return registers[jj].index ;
    }
    return -1 ;
}





int main(int argc, char *argv[]) {
    int32_t  s_value=0 ;
    uint32_t u_value=0 ;
    int jj=0 ;
    int index;



    // Open Linux memory device


    if((fd = open(name, O_RDWR)) < 0) {
        perror("[-] Error trying to open /dev/mem");
        return 1;
    }

    // Pointer for lock block memory addreses
    long lock_size = sysconf(_SC_PAGESIZE);
    long lock_addr = LOCK_FPGA_BASE_ADDR & (~(lock_size-1));
    long lock_off  = LOCK_FPGA_BASE_ADDR - lock_addr;

    //        *mmap(*addr,             length,       prot            , flags     , fd ,  offset  );
    lock_ptr = mmap(NULL, LOCK_FPGA_BASE_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, fd , lock_addr);

    if((void *)lock_ptr == MAP_FAILED) {
        fprintf(stderr, "[-] lock mmap() failed: %d\n", errno);
        return -1;
    }

    lock       = lock_ptr ;


    if(argc>1){
        // Arguments arte the reg names and values te be read and written
        for(jj=1; jj<argc ; jj++){

            index = reg_name_to_index(argv[jj]);

            if( index<0 ){
                fprintf(stdout,"ERROR: parameter '%s' not found\n", argv[jj]);
                return -1 ;
            }

            if( (jj+1<argc) &&  (str2int(&s_value, argv[jj+1], 10)==STR2INT_SUCCESS)   ){
                // Next arg is a number. Must be a write operation

                if(registers[index].read_only) {
                    printf("ERROR: %s is read-only and cannot be written\n",registers[index].name );
                    return -2;
                }
                if( (!registers[index].is_signed) && (s_value<0) ) {
                    printf("ERROR: %s is not a signed register and you tried to sed value %d\n",registers[index].name, s_value );
                    return -2;
                }
                write_reg(index, s_value);

                jj++; // skip value
            }else{
                // There's no next or it's not a number. Must be a read operation
                read_reg(index);
            }
        }
    }else{
        // Just print all the values
        for(jj=0; jj<PARAMS_NUM ; jj++){
            read_reg(jj);
            //printf("%d\n" , lock[jj] );
        }
    }

    // Clean the lock_ptr pointer
    munmap(lock_ptr, sysconf(_SC_PAGESIZE));
    return EXIT_SUCCESS;
}
