typedef int v16si __attribute__ ((vector_size (64)));
typedef unsigned int v16ui __attribute__ ((vector_size (64)));
typedef int v8si __attribute__ ((vector_size (32)));
typedef unsigned int v8ui __attribute__ ((vector_size (32)));
typedef int v4si __attribute__ ((vector_size (16)));
typedef unsigned int v4ui __attribute__ ((vector_size (16)));

typedef long v8sl __attribute__ ((vector_size (64)));
typedef unsigned long v8ul __attribute__ ((vector_size (64)));
typedef long v2sl __attribute__ ((vector_size (16)));
typedef unsigned long v2ul __attribute__ ((vector_size (16)));

// Typedefs for keys (K) and values/states (V)
typedef v8ui K;
typedef unsigned int Kb;
typedef v8ui V;
typedef unsigned int Vb;

//typedef struct __attribute__((aligned(32))){
typedef struct {
    uint64_t count;
    uint64_t sum;
    uint32_t min;
    uint32_t max;
} sk;

typedef struct{
    sk* sk_t0[REPLICAS];
    unsigned int nrows;
    unsigned int ncols;
    const char* keyfile;
    const char* valfile;
    unsigned long chunk_size;

    //Algorithm-specific
    unsigned int* select_seed;
} parameters;

unsigned int parity(unsigned int x) {
   unsigned int y;
   y = x ^ (x >> 1);
   y = y ^ (y >> 2);
   y = y ^ (y >> 4);
   y = y ^ (y >> 8);
   y = y ^ (y >> 16);
   return y & 1;
}

unsigned int parity(unsigned long x) {
   unsigned long y;
   y = x ^ (x >> 1);
   y = y ^ (y >> 2);
   y = y ^ (y >> 4);
   y = y ^ (y >> 8);
   y = y ^ (y >> 16);
   y = y ^ (y >> 32);
   return (unsigned long) (y & 1);
}

K* readKArrayFromFile(const char* filename, unsigned long* n_elems = NULL){
    FILE *f1 = fopen(filename, "rb");
    assert(f1 != NULL);
    fseek(f1, 0, SEEK_END);
    size_t fsize1 = ftell(f1);
    if(n_elems) *n_elems=fsize1/sizeof(K);
    fseek(f1, 0, SEEK_SET);
    K* tab1 = (K*) aligned_alloc(64,fsize1);
    size_t x = fread(tab1, 1, fsize1, f1);
    assert(x == fsize1);

    fclose(f1);

    return tab1;
}

V* readVArrayFromFile(const char* filename, unsigned long* n_elems = NULL){
    FILE *f1 = fopen(filename, "rb");
    assert(f1 != NULL);
    fseek(f1, 0, SEEK_END);
    size_t fsize1 = ftell(f1);
    if(n_elems) *n_elems=fsize1/sizeof(V);
    fseek(f1, 0, SEEK_SET);
    V* tab1 = (V*) aligned_alloc(64,fsize1);
    size_t x = fread(tab1, 1, fsize1, f1);
    assert(x == fsize1);
    fclose(f1);

    return tab1;
}

void writeVbArrayToFile(const char* filename, Vb* elements, size_t size){
    FILE *f1 = fopen(filename, "w");
    assert(f1 != NULL);

    fwrite(elements, sizeof(V), size, f1);
    fclose(f1);
}

void* readChunkFromFile(const char* filename, size_t chunk_size, unsigned int chunk_id){
    FILE *f1 = fopen(filename, "rb");
    assert(f1 != NULL);

    int rc = fseek(f1, chunk_id*chunk_size, SEEK_SET);
    assert(rc == 0);

    V* tab1 = (V*) aligned_alloc(64, chunk_size);
    size_t x = fread(tab1, 1, chunk_size, f1);
    assert(x == chunk_size);
    fclose(f1);

    return tab1;
}

inline unsigned int is_set(unsigned int x, unsigned int pos) {
    return (x >> pos) & 1;
}

inline v16ui is_set(v16ui x, unsigned int pos) {
    return (x >> pos) & 1;
}

inline v4ui is_set(v4ui x, unsigned int pos) {
    return (x >> pos) & 1;
}

inline v8ui is_set(v8ui x, unsigned int pos) {
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

inline v8ui h3(v8ui x, unsigned int* seed) {
    v8ui hash = {0, 0, 0, 0, 0, 0, 0, 0};
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
