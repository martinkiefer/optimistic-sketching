# FPGA Throughput Experiments
## Setup
First, you have to compile the ZIP projects in the `Vitis-U250` folder in Application-Sketching. Each compile give you a file called `binary_container_1.xclbin`, you have to copy them to this folder with the names `pessimistic.xclbin`, `regular.xclbin`, and `oversubscribed.xclbin`. From there, you can generate datasets and download host code by running:
```
make all # Use '-j num_processes' if you want things to go faster
```

## Run experiment
You just run
```
bash run_experiment.sh
```

and get CSV files for each architecture and dataset. The CSV file has the following format:
```
"dataset_size", "ints_per_kernel", "execution_time", "throughput"
```
`int_per_kernel` counts the number of 32bit ints (keys and values) processed by each of the four kernels. 
