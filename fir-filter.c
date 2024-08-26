#include <stdio.h>
#include <stdint.h>
 
//////////////////////////////////////////////////////////////
//  Filter Code Definitions
//////////////////////////////////////////////////////////////
 
// maximum number of inputs that can be handled
// in one function call
#define MAX_INPUT_LEN   80
// maximum length of filter than can be handled
#define MAX_FLT_LEN     2000
// buffer to hold all of the input samples
#define BUFFER_LEN      (MAX_FLT_LEN - 1 + MAX_INPUT_LEN)
 
// array to hold input samples
double insamp[ BUFFER_LEN ];
 
// FIR init
void firFloatInit( void )
{
    memset( insamp, 0, sizeof( insamp ) );
}
 
// the FIR filter function
void firFloat( double *coeffs, double *input, double *output,
       int length, int filterLength )
{
    double acc;     // accumulator for MACs
    double *coeffp; // pointer to coefficients
    double *inputp; // pointer to input samples
    int n;
    int k;
 
    // put the new samples at the high end of the buffer
    memcpy( &insamp[filterLength - 1], input,
            length * sizeof(double) );
 
    // apply the filter to each input sample
    for ( n = 0; n < length; n++ ) {
        // calculate output n
        coeffp = coeffs;
        inputp = &insamp[filterLength - 1 + n];
        acc = 0;
        for ( k = 0; k < filterLength; k++ ) {
            acc += (*coeffp++) * (*inputp--);
        }
        output[n] = acc;
    }
    // shift input samples back in time for next time
    memmove( &insamp[0], &insamp[length],
            (filterLength - 1) * sizeof(double) );
 
}
 
//////////////////////////////////////////////////////////////
//  Test program
//////////////////////////////////////////////////////////////
 
// bandpass filter centred around 1000 Hz
// sampling rate = 8000 Hz
 
#define FILTER_LEN  2000
void get_coeffs(double coeffs[]){
    FILE* coefficients;
    coefficients = fopen("coefficients.bin", "rb");
    if (coefficients == NULL) {
        printf("Error: could not open file\n");
        exit(-1);
    }
    fread(coeffs, sizeof(double), 2000, coefficients); 
}
 
void intToFloat( int16_t *input, double *output, int length )
{
    int i;
 
    for ( i = 0; i < length; i++ ) {
        output[i] = (double)input[i];
    }
}
 
void floatToInt( double *input, int16_t *output, int length )
{
    int i;
 
    for ( i = 0; i < length; i++ ) {
        if ( input[i] > 32767.0 ) {
            input[i] = 32767.0;
        } else if ( input[i] < -32768.0 ) {
            input[i] = -32768.0;
        }
        // convert
        output[i] = (int16_t)input[i];
    }
}
 
// number of samples to read per loop
#define SAMPLES   80
 
int main( void )
{
    int size;
    int16_t input[SAMPLES];
    int16_t output[SAMPLES];
    double floatInput[SAMPLES];
    double floatOutput[SAMPLES];
    double coeffs[MAX_FLT_LEN];
    FILE   *in_fid;
    FILE   *out_fid;
 
    // open the input waveform file
    in_fid = fopen( "input.pcm", "rb" );
    if ( in_fid == 0 ) {
        printf("couldn't open input.pcm");
        return -1;
    }
 
    // open the output waveform file
    out_fid = fopen( "C:\\Users\\Fritz\\Documents\\Bachelorarbeit\\Tests\\output.bin", "wb" );
    if ( out_fid == 0 ) {
        printf("couldn't open outputFloat.pcm");
        return -1;
    }
 
    // initialize the filter
    firFloatInit();

    get_coeffs(coeffs);
 
    // process all of the samples
    do {
        // read samples from file
        size = fread( input, sizeof(int16_t), SAMPLES, in_fid );
        // convert to doubles
        intToFloat( input, floatInput, size );
        // perform the filtering
        firFloat( coeffs, floatInput, floatOutput, size,
               FILTER_LEN );
        // convert to ints
        // write samples to file
        fwrite( floatOutput, sizeof(double), size, out_fid );
    } while ( size != 0 );
 
    fclose( in_fid );
    fclose( out_fid );
 
    return 0;
}
