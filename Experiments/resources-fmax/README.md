# Resource + Fmax Experiments
In these experiments, we fire up experiments for the resource consumption.

We have three experiment sets:
* pessimstiv-vs-optimistic: Experiments comparing the pessimstic to optimistic architectures with default parameters and the same number of columns.
* optimstic-only: Experiments comparing the regular and oversubscribed architecture for a fixed number of columns.
* cnt-vs-sum: Experiments comparing the sum and count sketch with various degrees of merging.

## Running the experiments
Running the experiment sets is easy: You only need Vivado (enterprise version, unfortunately), you go into the subfolders and do the following:
```
parallelism=32
export VIVADO_DIR="/data-sata/Xilinx/Vivado/2021.2/bin" #Path to the bin directory of your vivado installation
python generate_makefile.py > Makefile
make all -j $parallelism
```
You can run multiple Vivado runs in parallel by using the -j option of make. Choose the degree of parallelism to suit your number of cores and RAM available. The experiments require multiple hundres of Gigabytes disk space because Vivado builds can be quite large.

# Generating machine-readable output
After you are done, the folders will contain many Vivado builds that are in no way easy to evaluate. Luckily, we have a little script that extraxts the resource consumption and maximum operating frequency into CSV files.

You go switch to this subfolder and execute
```
bash generate_csv.sh $dir_to_subfolder_with_builds > results.csv
```

The format of the csv for optimistc architecture is:
```"rows", "inputs", "banks", "memory_segment_depth", "segments", "queue_size", "has_vertical_merging", "unused_parameter", "horizontal_look_ahead", "seed", 
"instance", "entity", "total_luts",  "logic_luts", "lutrams", "srls", "ffs", "bram36s", "bram18s", "urams", "dsps", "target_fmax", "actual_fmax"
```
The first line of parameters has architecture parameters. The seed denotes an integer, each standing for one implementation strategy. The second line has the fields in the Vivado ressource utilization report, the target fmax (900MHz, just something unrealistically high), and the actual max reported by Vivado. Resources are cumulative and includes all subcomponents.


For pessimistic it is similar, but the first part is adjusted for the different arguments of the pessimistic code generator:
```"memory_segment_depth", "rows", "segments", "dispatch_factor (always 4)", "dispatch_factor (always 2)",  "inputs", "seed",
"instance", "entity", "total_luts",  "logic_luts", "lutrams", "srls", "ffs", "bram36s", "bram18s", "urams", "dsps", "target_fmax", "actual_fmax"
```

The following entities are associated with the follwoing parts of the architecture:
* Backend: `"dfu", "memory_component_0", "forwarding_update", "dchain_vector"`
* Frontend: `"selector", "hash_converter"`
* Dispatcher: `"concurrency_controller"`


