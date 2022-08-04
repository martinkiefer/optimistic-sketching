#pragma GCC diagnostic ignored "-Wignored-attributes"
#include <iostream>
#include <chrono>
#include <time.h>
#include <boost/random/mersenne_twister.hpp>
#include <boost/random/uniform_int_distribution.hpp>

#define CHUNK_SIZE (1024*1024*256)

#define gpuErrchk(ans) { gpuAssert((ans), __FILE__, __LINE__); }
inline void gpuAssert(cudaError_t code, const char *file, int line, bool abort=true)
{
   if (code != cudaSuccess) 
   {
      fprintf(stderr,"GPUassert: %s %s %d\n", cudaGetErrorString(code), file, line);
      if (abort) exit(code);
   }
}

__device__ unsigned int parity(unsigned int x) {
    unsigned int y;
    y = x ^ (x >> 1);
    y = y ^ (y >> 2);
    y = y ^ (y >> 4);
    y = y ^ (y >> 8);
    y = y ^ (y >>16);
    return y & 1;
 }
 
 __device__ unsigned int nonlinear_h(unsigned int x) {
     return parity((x >> 0) | (x >> 1));
 }
 
 __device__ unsigned int is_set(unsigned int x, unsigned int pos) {
     return (x >> pos) & 1;
 }
 

 __device__ unsigned int h3(unsigned int x, unsigned int nsketches, unsigned int* seed) {
    unsigned int hash = 0;
    for(int i = 0; i < 32; i++){
        hash ^=  seed[i*nsketches]*is_set(x,i); 
    }
    return hash;
}


 __device__ int ech3(unsigned int v, unsigned int seed, unsigned int sbit){
     //First we compute the bitwise AND between the seed and the value
     int res = parity(v & seed) ^ nonlinear_h(v) ^ sbit ;
     //Aaaand here comes the parity
     return 2*res-1;
 }


//Full version, operates row by row
 __global__ void construct_sketch_full_r(
    unsigned int skn_rows,
    unsigned int skn_cols,
    unsigned int n_replicas,
    unsigned long n_values,
    unsigned int* __restrict__ key,
    unsigned int* __restrict__ value,
    unsigned int* __restrict__ select_seed,
    unsigned long long int* __restrict__ sketches_count,
    unsigned long long int* __restrict__ sketches_sum,
    unsigned int* __restrict__ sketches_min,
    unsigned int* __restrict__ sketches_max
) 
{
    unsigned int global_size = gridDim.x * blockDim.x;
    unsigned int global_id = blockIdx.x * blockDim.x + threadIdx.x;
    unsigned long n_partitions = global_size / skn_rows;
    //unsigned long partition_size = (n_values-1)/n_replicas+1;
    unsigned int partition = global_id % n_partitions;
    unsigned int r = global_id / n_partitions;
    unsigned int replica = r / skn_rows;
    unsigned int row = r % skn_rows;


    for(unsigned long i = partition + (replica*n_partitions); i < n_values; i += (n_partitions*n_replicas)){
            unsigned int select = 0;
            for(int k = 0; k < 32; k++)  if(is_set(key[i],k)) select ^= select_seed[row*32+k];
            select = select % skn_cols;

            atomicAdd(&sketches_count[r*skn_cols+select], 1UL);
            atomicAdd(&sketches_sum[r*skn_cols+select], (unsigned long) value[i]);
            atomicMin(&sketches_min[r*skn_cols+select], value[i]);
            atomicMax(&sketches_max[r*skn_cols+select], value[i]);
    }
}


typedef struct{

    size_t skn_rows;
    size_t skn_cols;
    size_t replicas;

    unsigned long long int* sk_cnt;
    unsigned long long int* sk_sum;
    unsigned int* sk_min;
    unsigned int* sk_max;

    unsigned long ts;
    unsigned long nkeys;

    unsigned int* keys;
    unsigned int* values;
    unsigned int* select_seed;

} parameters;

void* cudaAllocAndCopy(void* hst_ptr, size_t size){
    void* d_ptr;
    cudaMalloc((void **) &d_ptr, size);
    cudaMemcpy(d_ptr, hst_ptr, size, cudaMemcpyHostToDevice);
    return d_ptr;
}

void writeSArrayToFile(const char* filename, int* elements, size_t size){
    FILE *f1 = fopen(filename, "w");
    assert(f1 != NULL);
    
    fwrite(elements, sizeof(int), size, f1);
    fclose(f1);
}

void* readMappedArrayFromFile(const char* filename, size_t * filesize = NULL){
    FILE *f1 = fopen(filename, "rb");
    assert(f1 != NULL);
    fseek(f1, 0, SEEK_END);
    size_t fsize1 = ftell(f1);
    if(filesize) *filesize=fsize1;
    fseek(f1, 0, SEEK_SET);
    void* tab1;
    cudaHostAlloc(&tab1,fsize1, cudaHostAllocMapped);
    size_t x = fread(tab1, fsize1, 1, f1);
    fclose(f1);

    return tab1;
}

void* readArrayFromFile(const char* filename, size_t * filesize = NULL){
    FILE *f1 = fopen(filename, "rb");
    assert(f1 != NULL);
    fseek(f1, 0, SEEK_END);
    size_t fsize1 = ftell(f1);
    if(filesize) *filesize=fsize1;
    fseek(f1, 0, SEEK_SET);
    void* tab1;
    void* gtab1;
    cudaMalloc(&gtab1, fsize1);
    gpuErrchk(cudaPeekAtLastError());
    tab1 = malloc(fsize1);
    size_t x = fread(tab1, fsize1, 1, f1);
    fclose(f1);

    cudaMemcpy(gtab1, tab1, fsize1, cudaMemcpyHostToDevice);
    gpuErrchk(cudaPeekAtLastError());
    return gtab1;
}

double sketch_contruction(parameters* p){
    size_t local = 64;
    int tot_SM = 0;
    cudaDeviceGetAttribute(&tot_SM, cudaDevAttrMultiProcessorCount, 0);

    int occupancy = 0;
    cudaOccupancyMaxActiveBlocksPerMultiprocessor(&occupancy, construct_sketch_full_r, local, 0);

    size_t global = occupancy*tot_SM*local;
    auto begin = std::chrono::high_resolution_clock::now();
    
    construct_sketch_full_r<<<global/local, local>>>((unsigned int) (p->skn_rows*p->replicas), (unsigned int) p->skn_cols, (unsigned int) p->replicas, p->ts, p->keys, p->values, p->select_seed, p->sk_cnt, p->sk_sum, p->sk_min, p->sk_max);
    gpuErrchk(cudaPeekAtLastError());
    
    cudaDeviceSynchronize();
    auto end = std::chrono::high_resolution_clock::now();
    return std::chrono::duration_cast<std::chrono::nanoseconds>(end-begin).count();
}


int main( int argc, const char* argv[] )
{
    parameters p;
    cudaSetDevice(1);
    cudaSetDeviceFlags(cudaDeviceMapHost);

    p.skn_rows = (unsigned int) atoll(argv[1]);
    p.skn_cols = (unsigned int) atoll(argv[2]);
    p.replicas = (unsigned int) atoll(argv[3]);

    
    //Initialize sketches
    cudaMalloc((void **) &p.sk_cnt, p.replicas*p.skn_rows*p.skn_cols*sizeof(unsigned long long int));
    gpuErrchk(cudaPeekAtLastError());
    cudaMemset(p.sk_cnt, 0, p.replicas*p.skn_rows*p.skn_cols*sizeof(unsigned long));
    gpuErrchk(cudaPeekAtLastError());

    cudaMalloc((void **) &p.sk_sum, p.replicas*p.skn_rows*p.skn_cols*sizeof(unsigned long long int));
    gpuErrchk(cudaPeekAtLastError());
    cudaMemset(p.sk_sum, 0, p.replicas*p.skn_rows*p.skn_cols*sizeof(unsigned long));
    gpuErrchk(cudaPeekAtLastError());

    cudaMalloc((void **) &p.sk_min, p.replicas*p.skn_rows*p.skn_cols*sizeof(unsigned int));
    gpuErrchk(cudaPeekAtLastError());
    cudaMemset(p.sk_min, 255, p.replicas*p.skn_rows*p.skn_cols*sizeof(unsigned int));
    gpuErrchk(cudaPeekAtLastError());

    cudaMalloc((void **) &p.sk_max, p.replicas*p.skn_rows*p.skn_cols*sizeof(unsigned int));
    gpuErrchk(cudaPeekAtLastError());
    cudaMemset(p.sk_max, 0, p.replicas*p.skn_rows*p.skn_cols*sizeof(unsigned int));
    gpuErrchk(cudaPeekAtLastError());

    size_t size = 0;
    p.keys = (unsigned int *) readArrayFromFile(argv[4], &size);
    p.values = (unsigned int *)readArrayFromFile(argv[5],&size);
    p.ts = size/sizeof(unsigned int);

    unsigned int* select_seed =  (unsigned int*) malloc(sizeof(unsigned int)*32*32*p.skn_rows);

    boost::random::mt19937 gen(time(0));
    for(unsigned int i = 0; i < p.skn_rows*32*32; i++){
       select_seed[i] = gen();
    }
    p.select_seed = (unsigned int*) cudaAllocAndCopy(select_seed, p.skn_rows*32*32*sizeof(unsigned int));

    double time = sketch_contruction(&p);
    std::cout << p.skn_rows << ";" << p.skn_cols << ";" << p.replicas << ";" << p.ts << ";" << p.ts*sizeof(unsigned int)*2*8 / (float) time << std::endl;

    return 0;
}
