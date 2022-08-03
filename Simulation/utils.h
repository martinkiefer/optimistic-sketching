//
// Created by Martin Kiefer on 08.02.22.
//

#ifndef FILEHASHER_UTILS_H
#define FILEHASHER_UTILS_H


#include <iostream>

typedef int32_t v16si __attribute__ ((vector_size (64)));
typedef uint32_t v16ui __attribute__ ((vector_size (64)));
typedef int32_t v8si __attribute__ ((vector_size (32)));
typedef uint32_t v8ui __attribute__ ((vector_size (32)));
typedef int32_t v4si __attribute__ ((vector_size (16)));
typedef uint32_t v4ui __attribute__ ((vector_size (16)));

typedef int64_t v8sl __attribute__ ((vector_size (64)));
typedef uint64_t v8ul __attribute__ ((vector_size (64)));
typedef int64_t v4si __attribute__ ((vector_size (32)));
typedef uint64_t v4ui __attribute__ ((vector_size (32)));
typedef int64_t v2sl __attribute__ ((vector_size (16)));
typedef uint64_t v2ul __attribute__ ((vector_size (16)));


inline unsigned int is_set(unsigned int x, unsigned int pos) {
    return (x >> pos) & 1;
}

inline v16ui is_set(v16ui x, unsigned int pos) {
    return (x >> pos) & 1;
}

inline v4ui is_set(v4ui x, unsigned int pos) {
    return (x >> pos) & 1;
}

inline v8ul is_set(v8ul x, unsigned int pos) {
    return (x >> pos) & 1;
}

inline v2ul is_set(v2ul x, unsigned int pos) {
    return (x >> pos) & 1;
}

inline unsigned int is_set(unsigned long x, unsigned int pos) {
    return (x >> pos) & 1;
}


inline v16ui h3(v16ui x, unsigned int* seed) {
    v16ui hash = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    for(int i = 0; i < 32; i++){
        hash ^= is_set(x,i) * seed[i];
    }
    return hash;
}

inline v4ui h3(v4ui x, unsigned int* seed) {
    v4ui hash = {0, 0, 0, 0};
    for(int i = 0; i < 32; i++){
        hash ^= is_set(x,i) * seed[i];
    }
    return hash;
}
inline uint32_t h3(uint32_t x, unsigned int* seed) {
    uint32_t hash = 0;
    for(int i = 0; i < 32; i++){
        hash ^= is_set(x,i) * seed[i];
    }
    return hash;
}

inline v8ul h3(v8ul x, unsigned int* seed) {
    v8ul hash = {0, 0, 0, 0, 0, 0, 0, 0};
    for(int i = 0; i < 64; i++){
        hash ^= is_set(x,i) * seed[i];
    }
    return hash;
}

inline v2ul h3(v2ul x, unsigned int* seed) {
    v2ul hash = {0, 0};
    for(int i = 0; i < 64; i++){
        hash ^= is_set(x,i) * seed[i];
    }
    return hash;
}



#endif //FILEHASHER_UTILS_H
