#include <iostream>
#include <cassert>
#include <cstring>
#include <chrono>
#include <filesystem>
#include <atomic>
#include <sstream>
#include <omp.h>

#include "params.h"
#include "utils.h"

#define CHUNKS (REPLICAS)


inline void update(sk* tmp_p, Vb tmp_d){
                    tmp_p->count += 1;
                    tmp_p->sum += tmp_d;
                    tmp_p->min = std::min(tmp_d,tmp_p->min);
                    tmp_p->max = std::max(tmp_d,tmp_p->max);
}

void update_sketch(unsigned int nrows, unsigned int ncols, sk* s, K* kchunk, V* vchunk, unsigned long chunk_size, unsigned int* select_seed){
    for(unsigned int r = 0; r < nrows; r++){
        for(unsigned int j = 0; j < chunk_size / (sizeof(K)/sizeof(Kb)); j++){
            K select = h3(*(kchunk+j), select_seed+sizeof(Kb)*8*r);
            select = select % ncols;
            for(unsigned int k = 0; k < sizeof(K)/sizeof(Kb); k++){
                sk* tmp_p = s + r*ncols+ select[k];
                Vb tmp_d = vchunk[j][k]; 
                update(tmp_p, tmp_d);
            }
        }
    }
}

void sketch_contruction(parameters* p, double& processing_time){
    omp_set_dynamic(0);
    omp_set_num_threads(REPLICAS);

    K* keys[CHUNKS];
    V* values[CHUNKS];

    std::chrono::time_point<std::chrono::steady_clock>* begin_processing = new std::chrono::time_point<std::chrono::steady_clock>[REPLICAS];
    std::chrono::time_point<std::chrono::steady_clock>* end_processing = new std::chrono::time_point<std::chrono::steady_clock>[REPLICAS];

#pragma omp parallel
{

    unsigned long id = omp_get_thread_num();
    unsigned int replica = id;
    unsigned int chunk_id = id;
    keys[chunk_id] = (K*) readChunkFromFile(p->keyfile, p->chunk_size*sizeof(Kb), chunk_id);
    values[chunk_id]  = (V*) readChunkFromFile(p->valfile, p->chunk_size*sizeof(Vb), chunk_id);

    p->sk_t0[replica] = (sk *) aligned_alloc(64, p->nrows * p->ncols * sizeof(sk));     
    sk* s = p->sk_t0[replica];
    for(unsigned int i = 0; i < p->nrows; i++){
        for(unsigned int j = 0; j < p->ncols; j++){
            s[i*p->nrows+j].count = 0;
            s[i*p->nrows+j].sum = 0;
            s[i*p->nrows+j].min = 0xffffffffu;
            s[i*p->nrows+j].max = 0;
        }
    }
    K* kchunk = keys[chunk_id];
    V* vchunk = values[chunk_id];

    unsigned int *select_seed = (unsigned int*) aligned_alloc(64,sizeof(Kb)*8*p->nrows*sizeof(unsigned int));
    std::memcpy(select_seed, p->select_seed, sizeof(Kb)*8*p->nrows*sizeof(unsigned int));
    #pragma omp barrier
    begin_processing[id] = std::chrono::steady_clock::now();
    update_sketch(p->nrows, p->ncols, s, kchunk, vchunk, p->chunk_size, select_seed);
    end_processing[id] = std::chrono::steady_clock::now();
}

    std::chrono::time_point<std::chrono::steady_clock> minbegin_p = begin_processing[0];
    std::chrono::time_point<std::chrono::steady_clock> maxend_p = end_processing[0];
    
    long x = std::chrono::duration_cast<std::chrono::nanoseconds>(end_processing[0]-begin_processing[0]).count();
    for(unsigned int i = 1; i < REPLICAS; i++) {
        x += std::chrono::duration_cast<std::chrono::nanoseconds>(end_processing[i]-begin_processing[i]).count();
        if(minbegin_p > begin_processing[i]) minbegin_p= begin_processing[i];
        if(maxend_p < end_processing[i]) maxend_p = end_processing[i];
    }
    //processing_time = ((double) std::chrono::duration_cast<std::chrono::nanoseconds>(maxend_p - minbegin_p).count());
    processing_time = (((double) x)/(REPLICAS));
}


void print_sketches(parameters p){
    for(unsigned int l = 0; l < REPLICAS; l++){
    //for(unsigned int l = NROWS; l < NROWS*2; l++){
        //std::cout << "-- Replica : " << l << std::endl;
            std::cout << "Row: " << l << " | ";
            for(unsigned int r = 0; r < p.nrows; r++){
                unsigned int row_sum = 0;
                for(unsigned int j = 0; j < p.ncols; j++){
                    row_sum += p.sk_t0[l][p.ncols*r+j].count;
                    std::cout << p.sk_t0[l][p.ncols*r+j].count << " & ";
                    std::cout << p.sk_t0[l][p.ncols*r+j].sum << " & ";
                    std::cout << p.sk_t0[l][p.ncols*r+j].min << " & ";
                    std::cout << p.sk_t0[l][p.ncols*r+j].max << " | ";
                }
                std::cout << "| Sum: " << row_sum << std::endl;
            }
            //if(row_sum != CHUNK_SIZE*THREADS_PER_REPLICA){
            //    std::cout << "Error in consistency check." << std::endl;
            //    assert(false);
            //}
    }
}

int main( int argc, const char* argv[] )
{
    parameters p;
    p.nrows = atol(argv[1]);
    p.ncols = atol(argv[2]);
    p.keyfile = argv[3];
    p.valfile = argv[4];

    unsigned long fsize = 0;

    std::filesystem::path path{p.keyfile};
    fsize = std::filesystem::file_size(path);
    p.chunk_size = fsize/(sizeof(Vb)*REPLICAS);
    p.chunk_size = (p.chunk_size / 64) * 64;
    p.select_seed = (unsigned int*) readChunkFromFile("./seed.dump", sizeof(Kb)*8*p.nrows*sizeof(unsigned int), 0);

    double processing_time = 0.0;
    sketch_contruction(&p, processing_time);

    volatile int i = 0;
    //writeVbArrayToFile("sketch.dump", p.sk_t0, p.skn_rows*p.skn_cols*p.replicas);
    if(i) print_sketches(p);

    std::cout   << p.nrows << ";" << p.ncols << ";" << REPLICAS  
                 << ";" << p.chunk_size << ";"
                << processing_time << ";"
                << REPLICAS*p.chunk_size*(sizeof(Vb)+sizeof(Kb))*8.0 / (processing_time)
                << std::endl;


    return 0;
}
