#include <iostream>
#include "utils.h"
#include <fstream>

typedef v8ui K;
typedef uint32_t Kb;

int main(int argc, char *argv[]) {
    //First, let's assume

    uint32_t * seed = new uint32_t [8*sizeof(Kb)];
    std::ifstream ss = std::ifstream("/dev/urandom", std::ifstream::binary);
    if(ss) ss.read((char*) seed, sizeof(Kb)*sizeof(uint32_t)*8);
    if (! ss) throw std::runtime_error("Error while reading seed from /dev/urandom.");
    ss.close();

    std::ifstream is = std::ifstream(argv[1], std::ifstream::binary);
    std::ofstream os = std::ofstream(argv[2], std::ifstream::binary);

    K k;
    if(is && os){
        while(true) {
            is.read((char *) (&k), sizeof(K));
            if (is.eof()) break;
            if (! is) throw std::runtime_error("Error while reading from file.");

            k = h3(k, seed);
            os.write((char*) (&k), sizeof(K));
        }

    }
    else throw std::invalid_argument("Input files not found.");
    is.close();
    os.close();

    return 0;
}
