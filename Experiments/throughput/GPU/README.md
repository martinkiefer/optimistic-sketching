# GPU Throughput Experiments
## Setup
The Makefile will get all the datasets (if they are not already downloaded) and compile the two CUDA baselines. You need to specifiy your CUDA folder and the streaming multiprocessor architecture.
```
export CUDA_PREFIX="/usr/local/cuda-11.2"
GPU_ARCH ?= "sm_75"
make all # Use '-j num_processes' if you want things to go faster
```

## Experiments
The rest is simple, you bring a large GPU and sufficient time (~a day). You run 'bash run_experiment.sh'. A CSV for every dataset is created. It has the following format:
```
"rows", "columns", "replicas", "filesize", "throughput"
```
Replicas is set to zero for the row-by-row strategy.
