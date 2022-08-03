#include <iostream>
#include <deque>
#include <tuple>
#include <fstream>

// Light-weight FIFO queue based on a ring buffer.
template<class T>
class RingBuffer{
private:
    uint32_t size;
    T* buffer;
    uint32_t head;
    uint32_t tail;
    uint32_t elems;
    T lelem;

public:
    RingBuffer(uint32_t size) :
    size(size), head(0), tail(0), elems(0)
    {
        buffer = new T[size];
    }

    void push(T elem){
        elems++;
        buffer[head] = elem;
        head++;
        if(head == size) head = 0;
    }

    bool isEmpty(){
        return elems == 0;
    }

    bool isFull(){
        return elems == size;
    }

    uint32_t getElements(){
        return elems;
    }

    T pop(){
        elems--;
        T rt = buffer[tail];
        tail++;
        if(tail == size) tail = 0;
        lelem = rt;
        return rt;
    }

    
    T peek(){
        if(isEmpty()) return lelem;
        return buffer[tail];
    }

};

class RowSimulator{
private:
    uint32_t inputs;
    uint32_t banks;

    //Number of positions in each queue
    uint32_t qsize;

    //Number of elements in the shift merger
    uint32_t smsize;

    // Do we simulate a merging queue tail?
    bool has_mqt;

    // Do we simulate a merge tree?
    bool has_mt;

    // One queue per bank and input value
    RingBuffer<u_int32_t>** q;

    // One queue tail for every queue
    // Offset
    uint32_t ** qt_o;
    // Is the current value the neutral one?
    bool ** qt_v;

    // One shift merger array for every queue
    uint32_t*** sma_o;
    bool*** sma_v;

    uint32_t * cur_input;

public:
    RowSimulator(uint32_t  inputs, uint32_t banks, uint32_t qsize, uint32_t smsize, bool has_mqt, bool has_mt) :
        inputs(inputs), banks(banks), qsize(qsize), smsize(smsize), has_mqt(has_mqt), has_mt(has_mt)
    {
        //Initialize the army of arrays and ring buffers
        q = new RingBuffer<uint32_t>*[banks];
        qt_o = new uint32_t*[banks];
        qt_v = new bool*[banks];
        cur_input = new uint32_t[banks];

        for(uint32_t b = 0; b < banks; b++) {
            q[b] = (RingBuffer<uint32_t>*) malloc(sizeof(RingBuffer<uint32_t>) * inputs);
            for(uint32_t i = 0; i < inputs; i++) q[b][i] = RingBuffer<uint32_t>(qsize);
            qt_o[b] = new uint32_t[inputs]();
            qt_v[b] = new bool[inputs]();
        }

        if(smsize > 0) {
            sma_o = new uint32_t **[banks];
            sma_v = new bool **[banks];
            for (uint32_t b = 0; b < banks; b++) {
                sma_o[b] = new uint32_t *[inputs];
                sma_v[b] = new bool *[inputs];
                for (uint32_t i = 0; i < inputs; i++) {
                    sma_o[b][i] = new uint32_t[smsize]();
                    sma_v[b][i] = new bool[smsize]();
                }
            }
        }
    }

   void shift_sm(uint32_t& offset, bool& valid, uint32_t bank, uint32_t input){
        if(smsize > 0){
            uint32_t to = offset;
            bool tv = valid;
            offset = sma_o[bank][input][smsize-1];
            valid = sma_v[bank][input][smsize-1];
            for(uint32_t i = 0; i < smsize-1; i++){
                sma_o[bank][input][smsize-i-1] = sma_o[bank][input][smsize-i-2];
                sma_v[bank][input][smsize-i-1] = sma_v[bank][input][smsize-i-2];
            }
            if(to % banks == bank) {
                sma_o[bank][input][0] = to;
                sma_v[bank][input][0] = tv;
            }
            else {
                sma_o[bank][input][0] = 0;
                sma_v[bank][input][0] = false;
            }


            for(uint32_t i = 0; i < smsize-1; i++){
                if(sma_o[bank][input][smsize - 1] == sma_o[bank][input][i]) sma_v[bank][input][i] = false;
            }

        }
   }

   void shift_sm(uint32_t& offset, bool& valid, uint32_t input){
        uint32_t bank = 0;
        if(smsize > 0){
            uint32_t to = offset;
            bool tv = valid;
            offset = sma_o[bank][input][smsize-1];
            valid = sma_v[bank][input][smsize-1];
            for(uint32_t i = 0; i < smsize-1; i++){
                sma_o[bank][input][smsize-i-1] = sma_o[bank][input][smsize-i-2];
                sma_v[bank][input][smsize-i-1] = sma_v[bank][input][smsize-i-2];
            }
            sma_o[bank][input][0] = to;
            sma_v[bank][input][0] = tv;

                for(uint32_t i = 0; i < smsize-1; i++){
                    sma_v[bank][input][i] &= 
                        (sma_v[bank][input][smsize-1] == false) |
                        (sma_o[bank][input][smsize - 1] != sma_o[bank][input][i]) ;
                }
        }
   }

   void update_tail(uint32_t& offset, bool& valid, uint32_t bank, uint32_t input){
        // For architectures that do not have a shift merger
       //if(valid) std::cout << offset << std::endl;
        if(! (offset % banks == bank)){
            valid = false;
        }

        if(valid == false && ! q[bank][input].isEmpty()){
            //if(valid) std::cout << "z" << std::endl;
            valid = false;
        }
        else if(has_mqt && qt_o[bank][input] == offset && ! q[bank][input].isEmpty())
        {
            //if(valid) std::cout << "y" << std::endl;
            // Swallow update due to merge
            qt_v[bank][input] |= valid;
            valid = false;
        }
        else{
            //if(valid) std::cout << "x" << std::endl;
            // Replace
            bool tb = qt_v[bank][input];
            uint32_t to = qt_o[bank][input];
            qt_v[bank][input] = valid;
            qt_o[bank][input] = offset;
            valid = tb;
            offset = to;
        }
   }

    void addToQueue(uint32_t offset, bool& valid, uint32_t bank, uint32_t input){
            if(valid and offset % banks == bank){
                //std::cout << "append" << std::endl;
                q[bank][input].push(offset);
            }
    }

   void process_queues(uint32_t bank){
        if(! has_mt) {
            uint32_t i = cur_input[bank];
            if (! q[bank][i].isEmpty()) q[bank][i].pop();
        }
        else    {
            uint32_t i = cur_input[bank];
            /*for(uint32_t k = 0; k < inputs; k++){
                if(! q[bank][(i+k) % inputs].isEmpty()) i = (i + k) % inputs;
            }*/
            uint32_t o = 0;
            //if (! q[bank][i].isEmpty()){
                o = q[bank][i].peek();
                for(uint32_t j = 0; j < inputs; j++){
                    if((! q[bank][j].isEmpty()) && q[bank][j].peek() == o){
                        q[bank][j].pop();
                    }
                }
            //}
        }
       cur_input[bank]++;
       if (cur_input[bank] >= inputs) cur_input[bank] = 0;
   }

    bool isStalled(){
        //std::cout << "---------" << std::endl;
        for(uint32_t b = 0; b < banks; b++) {
            for(uint32_t i = 0; i < inputs; i++) {
                //std::cout << b << " | " << i << " | " << q[b][i].getElements() << std::endl;
                if(q[b][i].isFull()) return true;
            }
        }
        return false;
   }


    void tick(uint32_t* offset){
        // First things first: We empty the queue
        for(uint32_t b = 0; b < banks; b++) {
            process_queues(b);
            ;
        }

        for(uint32_t i = 0; i < inputs; i++) {
            uint32_t ot = offset[i];
            bool vt = true;
            shift_sm(ot, vt, i);
            for(uint32_t b = 0; b < banks; b++) {
                uint32_t o = ot;
                bool v = vt;

                //update_tail(o, v, b, i);
                addToQueue(o, v, b, i);
            }
        }

    }

    void stalledTick(){
        // First things first: We empty the queue
        for(uint32_t b = 0; b < banks; b++) {
            process_queues(b);
            ;
        }
    }

};

class MatrixSimulator{
private:
    uint32_t rows;
    uint32_t cols;
    uint32_t inputs;
    uint32_t banks;

    //Number of positions in each queue
    uint32_t qsize;

    //Number of elements in the shift merger
    uint32_t smsize;

    // Do we simulate a merging queue tail?
    bool has_mqt;

    // Do we simulate a merge tree?
    bool has_mt;

    RowSimulator* ra;

    std::ifstream* ifsa;
public:
    MatrixSimulator(std::string prefix, uint32_t rows, uint32_t cols, uint32_t  inputs, uint32_t banks, uint32_t qsize, uint32_t smsize, bool has_mqt, bool has_mt) :
            rows(rows), cols(cols), inputs(inputs), banks(banks), qsize(qsize), smsize(smsize), has_mqt(has_mqt), has_mt(has_mt)
    {
        ra = (RowSimulator*) malloc(sizeof(RowSimulator)*rows);
        ifsa = new std::ifstream [rows];
        for(uint32_t r = 0; r < rows; r++) {
            ra[r] = RowSimulator(inputs, banks,qsize, smsize, has_mqt, has_mt);
            ifsa[r] = std::ifstream(prefix+std::to_string(r), std::ifstream::binary);
            if(ifsa[r].fail())  throw std::invalid_argument(std::string("Could not find file :")+prefix+std::to_string(r));
        }
    }

    void run_experiment(){
        uint32_t* v = new uint32_t [inputs];
        bool ready = true;

        uint64_t stalls = 0;
        uint64_t cycles = 0;
        uint64_t queue_elems = 0;

        while(true){
            bool next_ready = true;
            for(uint32_t r = 0; r < rows; r++){
                if(ready){
                    ifsa[r].read ((char*) v,inputs*sizeof(uint32_t));
                    if(ifsa[r].eof()) goto done;
                    if (! ifsa[r]) throw std::runtime_error("Error while reading from file.");

                    for(uint32_t i = 0; i < inputs; i++) v[i] = v[i] % cols;
                     ra[r].tick(v);
                }
                else {
                    ra[r].stalledTick();
                }
                next_ready &= ! ra[r].isStalled();
            }
            cycles++;
            if(! next_ready) stalls++;
	        ready=next_ready;
        }
        done:
        std::cout << rows << "," << cols << "," << inputs << "," << banks << "," << qsize << "," << smsize << ","
        << has_mqt << "," << has_mt << "," << cycles << "," << stalls << "," << (((double) stalls)/cycles) << std::endl;
    }


};


int main(int argc, char *argv[]) {
    if(argc < 10) throw std::invalid_argument("Insufficient arguments");
    uint32_t rows = atoi(argv[1]);
    uint32_t cols = atoi(argv[2]);
    uint32_t inputs = atoi(argv[3]);
    uint32_t banks = atoi(argv[4]);
    uint32_t qs = atoi(argv[5]);
    uint32_t smg = atoi(argv[6]);

    bool has_sm = atoi(argv[7]) == 1;
    bool has_smt = atoi(argv[8]) == 1;

    MatrixSimulator r (std::string(argv[9]), rows, cols, inputs, banks, qs, smg, has_sm, has_smt);

    r.run_experiment();

    return 0;
}
