# optimistic-sketching
An optimistic approach to FPGA-accelerated data-parallel sketching. This repository accompanies a publication that is under submission. Stay tuned.

Over the next few days, this repository will be filled with the artifacts listed below. Over time, we will provide increasingly detailed documentation in the README files in subfolders starting with the experiments.

## Requirements
* Python 3.9+ (RTL Generation, Dataset Generation)
* Python Packages: antlr4-python3-runtime 4.9.3 (Code Generation), tensorflow-probability (we used 0.17.0, Zipf data), tensorflow (we used 2.9.1, Zipf data)
* Boost (used for generation of random seeds in some baselines)
* Vivado (we used 2021.2; for experiments with dummy I/O template)
* Vitis (recently upgraded to 2022.1; for experiments with U250)
* Xilinx Runtime (recently upgraded to 2022.1 + U250 XDMA 4.1 Shell)
* Java Runtime (for ANTLR4 parser generation, RTL Generation)
* CUDA (we used 11.6, GPU baseline + accuracy experiments)
* GCC (we used 9.4, CPU baseline)

If you want to compile and run the FPGA parts without changing anything, you will need access to a U250 accelerator flashed with a compatibel deployment platform. Otherwise you may have to make changes to the project. 

For the CUDA parts, any recent Nvidia GPU will do. We used an A100. 

For the CPU baseline, any x86_64 CPU with AVX2 will do. We used an AMD EPYC 7742 (for historic reasons still caled Ryzen in the paper). It is generally recommended to run anything with use an x86_64 CPU with a recent Linux operating system as this is the only configuration we tested. Some artifacts may not compile or execute (e.g., tensorflow-probabilities is not available on a POWER system).

## Experiment Sets
| Experiment                                           | Provided                     | Notes          |
| -------                                              | --------                     | -------------- |
| Queue Size Exploration (Simulator)                   | Yes, with README             | `Experiments/stall_rates` |
| Merger Exploration     (Simulator)                   | Yes, with README             | `Experiments/stall_rates` |
| Ressource/Fmax Exploration (RTL Generator)           | Yes, with README             | `Experiments/resources+fmax`|
| Accuracy Comparison (Sketch Evaluator)               | Yes, with README             | `Experiments/accuracy` |
| Throughput (GPU)                                     | Yes, with README             | `Experiments/throughput/GPU`|
| Throughput (CPU)                                     | Yes, with README             | `Experiments/throughput/CPU` |
| Throughput (U250)                                    | Yes, with README             | `Experiments/throughput/U250` |


## Datasets
Our experiments use four different datasets:

| Dataset                       | Provided          | Notes                                     |
| -------                       | --------          | --------------                            |
| Uniform                       | Yes               |`Data/generate_uniform.sh`                 |
| Zipf($rho)                    | Yes               |`Data/generate_zipf.sh $rho`                    |
| WC'98                         | Yes               |`Data/generate_wc98.sh`                    |
| Caida                         | Yes               |`Data/generate_caida.sh`                  |
| NYT                           | Yes               |`Data/generate_nyt.sh`                    |


The accuracy experiments also require the groundtrouth for the approximate-group by query on real-world datasets.

| Groundtruth                   | Provided          | Notes                                     |
| -------                       | --------          | --------------                            |
| WC'98                         | Yes               |`Data/gt/nyt/generate.sh`                  |
| Caida                         | Yes               |`Data/gt/caida/generate.sh`                |
| NYT                           | Yes               |`Data/gt/nyt/generate.sh`                  |

For now, we spare everyone the time- and storage-intensive preprocessing for real-wolrd datasets and just provide gzipped binary downloads from TUBs Nextcloud. Datasets are still quite large, though. It's best to have around 50GB of free disk space.

## Full Sketching Implementations
Sketching for group-by application. Used in throughput experiments.

| Implementation                      | Provided        | Notes                                             |
| -------                             | --------        | --------------                                    |
| U250, optimstic, oversubscribed     | Yes             | `Application-Sketching/Vitis-U250/oversubscribed` |
| U250, optimstic, regular            | Yes             | `Application-Sketching/Vitis-U250/regular`        |
| U250, pessimistc                    | Yes             | `Application-Sketching/Vitis-U250/pessimistic`    |
| U250, host-code                     | Yes             | `Application-Sketching/Vitis-U250/host` |
| CPU (vectorized + multithreaded)    | Yes             | `Application-Sketching/SIMD+OpenMP`               |
| CUDA                                | Yes             | `Application-Sketching/CUDA`                      |

FPGA device code is provided as Zips than can be imported using `Vitis -> File -> Import...`. Large BLOBs in Git are not ideal and we are working on a smarter solution.

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
