# optimistic-sketching
An optimistic approach to FPGA-accelerated data-parallel sketching. This repository accompanies a publication that is under submission. Stay tuned.

Over the next few days, this repository will be filled with the artifacts listed below. Further information can be found in the individual README files.

## Requirements
* Python 3.9+ (RTL Generation, Dataset Generation)
* Python Packages: antlr4-python3-runtime 4.9.3 (Code Generation), tensorflow-probability (we used 0.17.0, Zipf data)
* Vivado (we used 2021.2; for experiments with dummy I/O template)
* Vitis (recently upgraded to 2022.1; for experiments with U250)
* Xilinx Runtime (recently upgraded to 2022.1 + U250 XDMA 4.1 Shell)
* Java Runtime (for ANTLR4 parser generation, RTL Generation)
* CUDA (we used 11.6, GPU baseline + accuracy experiments)
* GCC (we used 9.4, CPU baseline)

If you want to compile and run the FPGA parts without changing anything, you will need access to a U250 accelerator flashed with a compatibel deployment platform. Otherwise you may have to make changes to the project. 

For the CUDA parts, any recent Nvidia GPU will do. We used an A100. 

For the CPU baseline, any x86_64 CPU with AVX2 will do. We used an AMD EPYC 7742 (for historic reasons still caled Ryzen in the paper). It is generally recommended to run anything with use an x86_64 CPU with a recent Linux operating system as this is the only configuration we tested. Some artifacts may not compile or execute (e.g., tensorflow-probabilities is not available on a POWER system).

## Datasets
Our experiments use four different datasets:

| Dataset                       | Provided        | Notes                                     |
| -------                       | --------        | --------------                            |
| Uniform                       | Yes             |`data/generate_uniform.sh`                 |
| Zipf(1.05, 1.1, 1.5)          | Yes             |`data/generate_zipf.sh`                    |
| Cup'98                        | Pending         |                                           |
| Caida                         | Pending         |                                           |
| NYT                           | Pending         |                                           |


The accuracy experiments also require the groundtrouth for the approximate-group by query on real-world datasets. We will either provide it as binary data or as part of a larger ETL job for real-world datasets. 

While things are easy for artificial datasets, we are currently figuring out whether / how we can distribute the real-world datasets and derrivatives of them.

## Full Sketching Implementations
Sketching for group-by application. Used in throughput experiments.

| Implementation                      | Provided        | Notes          |
| -------                             | --------        | -------------- |
| U250, optimstic, oversubscribed     | Pending         |                |
| U250, optimstic, regular            | Pending         |                |
| U250, pessimistc                    | Pending         |                |
| CPU (vectorized + multithreaded)    | Pending         |                |
| CUDA                                | Pending         |                |

## RTL Generation
Based on [Scotch](https://github.com/martinkiefer/Scotch) and used for ressource consumption experiments. RTL generation was also used to generate the sketching RTL sitting inside the RTL kernels of U250 sketching implementations.

| Artifact                                  | Provided        | Notes                     |
| -------                                   | --------        | --------------            |
| Select-Update ScotchDSL Descriptors       | Pending         |                           |
| Select-Map-Reduce ScotchDSL Descriptors   | Pending         |                           |
| RTL Generators                            | Yes             | `ScotchDSL/`              |
    
## Simulator
Computes the stall rate based on a binary input file containing keys.

| Artifact                              | Provided        | Notes          |
| -------                               | --------        | -------------- |
| Frontend + Dispatch Simulator         | Pending         |                |

## Sketch Evaluator
Computes accuracy efficiently given input data and groundtruth. Requires CUDA and an according GPU.

| Artifact                              | Provided        | Notes          |
| -------                               | --------        | -------------- |
| Sketch Evaluator                      | Pending         |                |

## Experiment Sets
| Experiment                                           | Provided        | Notes          |
| -------                                              | --------        | -------------- |
| Queue Size Exploration (Simulator)                   | Pending         |                |
| Merger Exploration     (Simulator)                   | Pending         |                |
| Ressource/Fmax Exploration (RTL Generator)           | Pending         |                |
| Throughput Comparison (Sketching Implementations)    | Pending         |                |
| Accuracy Comparison (Sketch Evaluator)               | Pending         |                |
