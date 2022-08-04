# optimistic-sketching
An optimistic approach to FPGA-accelerated data-parallel sketching. This repository accompanies a publication that is under submission. Stay tuned.

Over the next few days, this repository will be filled with the artifacts listed below. Further information will be provided in individual README files.

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

| Dataset                       | Provided          | Notes                                     |
| -------                       | --------          | --------------                            |
| Uniform                       | Yes               |`Data/generate_uniform.sh`                 |
| Zipf(1.05, 1.1, 1.5)          | Yes               |`Data/generate_zipf.sh`                    |
| WC'98                         | Yes               |`Data/generate_wc98.sh`                    |
| Caida                         | Yes               | `Data/generate_caida.sh`                  |
| NYT                           | Yes               | `Data/generate_nyt.sh`                    |


The accuracy experiments also require the groundtrouth for the approximate-group by query on real-world datasets.

| Groundtruth                   | Provided          | Notes                                     |
| -------                       | --------          | --------------                            |
| WC'98                         | Yes               |`Data/gt/nyt/generate.sh`                  |
| Caida                         | Yes               |`Data/gt/caida/generate.sh`                |
| NYT                           | Yes               |`Data/gt/nyt/generate.sh`                  |

For now, we spare everyone the time- and storage-intensive preprocessing for real-wolrd datasets and just provide gzipped binary downloads. Datasets are still quite large, though. It's best to have around 50GB of free disk space.

## Full Sketching Implementations
Sketching for group-by application. Used in throughput experiments.

| Implementation                      | Provided        | Notes                               |
| -------                             | --------        | --------------                      |
| U250, optimstic, oversubscribed     | Pending         |                                     |
| U250, optimstic, regular            | Pending         |                                     |
| U250, pessimistc                    | Pending         |                                     |
| U250, host-code                     | Pending         |                                     |
| CPU (vectorized + multithreaded)    | Yes             | `Application-Sketching/SIMD+OpenMP` |
| CUDA                                | Pending         |                                     |

## RTL Generation
Based on [Scotch](https://github.com/martinkiefer/Scotch) and used for ressource consumption experiments. RTL generation was also used to generate the sketching RTL sitting inside the RTL kernels of U250 sketching implementations.

| Artifact                                  | Provided        | Notes                           |
| -------                                   | --------        | --------------                  |
| Select-Update ScotchDSL Descriptors       | Yes             | `Sketches/Select-Update`        |
| Select-Map-Reduce ScotchDSL Descriptors   | Yes             | `Sketches/Select-Map-Reduce`    |
| RTL Generators                            | Yes             | `ScotchDSL/`                    |
    
## Simulator
Computes the stall rate based on a binary input file containing keys.

| Artifact                              | Provided        | Notes          |
| -------                               | --------        | -------------- |
| Frontend + Dispatch Simulator         | Yes             | `Simulator/`|

## Sketch Evaluator
Computes accuracy efficiently given input data and groundtruth. Requires CUDA and an according GPU.

| Artifact                              | Provided        | Notes          |
| -------                               | --------        | -------------- |
| Sketch Evaluator                      | Yes             | `Evaluator/`   |

## Experiment Sets
| Experiment                                           | Provided        | Notes          |
| -------                                              | --------        | -------------- |
| Queue Size Exploration (Simulator)                   | Pending         |                |
| Merger Exploration     (Simulator)                   | Pending         |                |
| Ressource/Fmax Exploration (RTL Generator)           | Pending         |                |
| Throughput Comparison (Sketching Implementations)    | Pending         |                |
| Accuracy Comparison (Sketch Evaluator)               | Pending         |                |
