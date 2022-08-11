# CPU Throughput Experiments
## Setup
The Makefile will get all the datasets (if they are not already downloaded) and compile the two CPU baselines (one sketch per thread, one sketch per row). 
```
make all # Use '-j num_processes' if you want things to go faster
```
The current make file assumes 128 cores and 256 threads. If you want to change this, modify the threads parameter in the Makefile.

## Experiments
The rest is simple. You bring sufficient time (~a day) and run 'bash run_experiment.sh'. If your system has only one socket, the OS scheduler will probably place threads according to the strategy if you set the number of threads correctly. If you have multiple sockets or want to be extra sure, modify/comment in the `GOMP_CPU_AFFINITY` variable exports allowing you to pin software threads to hardware threads.

A CSV for every dataset is created. It has the following format:
```
"rows", "columns", "threads", "chunk_size", "processing_time", "throughput"
```
Chunk_size is the number of key-value pairs added per thread.
