import itertools
import sys
from collections import defaultdict

class MakeGraph:
    def __init__(self):
        self.nodedict = {}

    def addNode(self, node):
        self.nodedict[node.target_name] = node

    def getNodeByKey(self, key):
        return self.nodedict[key]

    def makeFile(self):
        for v in self.nodedict.values():
            if v.command is not None:
                frame = F"""
{v.target_name} : {" ".join(map(lambda x: x.target_name, v.requirements))}
\t{v.command}  
"""
            else:
                frame = F"""
{v.target_name} : {" ".join(map(lambda x: x.target_name, v.requirements))}
"""
            print(frame)

class MakeNode:
    def __init__(self, target_name, command, requirements):
        self.target_name = target_name
        self.command = command
        self.requirements = requirements

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # We start with a beautiful empty make graph
    datasets = {("nyt",),("caida",), ("wc98",), ("uniform",), ("zipf", 1.05), ("zipf", 1.1), ("zipf", 1.5)}
    rows = [1]
    cols = [2048*4096]
    has_smqt = [0]
    ib = [(8,8), (8,16), (16,16), (16,32), (32,32), (32, 64), (64, 64), (64, 128)]
    if sys.argv[1] == "cross":
        qsizes = [2, 4, 8 ,16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
        smg_sizes = [0, 2, 4, 8, 16, 32, 64, 128]
        has_smt = [0,1]
    elif sys.argv[1] == "queue_size":
        qsizes = [2, 4, 8 ,16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
        smg_sizes = [0]
        has_smt = [0]
    elif sys.argv[1] == "merging":
        qsizes = [None]
        smg_sizes = [0, 2, 4, 8, 16, 32, 64, 128]
        has_smt = [0,1]
    else:
        print("Invalid program argumens only options allowed are (cross, queue_size, merging)")
        exit(1)
    iterations = 10

    mg = MakeGraph()
    deps = []

    target = "clean"
    command = "rm -f hasher simulator *.csv wc98_* nyt_* caida_* uniform_* zipf_*"
    simulator_node = MakeNode(target, command, [])
    mg.addNode(simulator_node)

    target = "simulator"
    command = "g++ -O3 -march=native ../../Simulation/simulator.cpp -o ./simulator"
    simulator_node = MakeNode(target, command, [])
    mg.addNode(simulator_node)

    target = "hasher"
    command = "g++ -O3 -march=native ../../Simulation/hasher.cpp -o ./hasher"
    hasher_node = MakeNode(target, command, [])
    mg.addNode(hasher_node)

    # Start with generating the datasets (dataset generation doesn't depend on anything)
    for d in datasets:
        ds = d[0]
        if d[0] == "zipf":
            ds += F"_{d[1]}"
        target = F"../../Data/{ds}_keys.bin"

        if d[0] == "uniform":
            command = f"cd ../../Data/; bash generate_uniform.sh"
            node = MakeNode(target, command, [])
            mg.addNode(node)
        elif d[0] == "wc98":
            command = f"cd ../../Data/; bash generate_wc98.sh"
            node = MakeNode(target, command, [])
            mg.addNode(node)
        elif d[0] == "nyt":
            command = f"cd ../../Data/; bash generate_nyt.sh"
            node = MakeNode(target, command, [])
            mg.addNode(node)
        elif d[0] == "caida":
            command = f"cd ../../Data/; bash generate_caida.sh"
            node = MakeNode(target, command, [])
            mg.addNode(node)
        elif d[0] == "zipf":
            command = f"cd ../../Data/; bash generate_zipf.sh {d[1]}"
            node = MakeNode(target, command, [])
            mg.addNode(node)


        else:
            raise Exception("Unknown dataset.")


    for i in range(max(rows)):
        for j in range(iterations):
            for d in datasets:
                ds = d[0]
                if d[0] == "zipf":
                    ds += F"_{d[1]}"

                target = f"{ds}_i{j}_o{i}"
                command = f"./hasher ../../Data/{ds}_keys.bin ./{target}"
                node = MakeNode(target, command, [mg.getNodeByKey(f"../../Data/{ds}_keys.bin"), hasher_node])
                mg.addNode(node)

    for d, m, n, (i, b), qs, sms, hsmqt, hsmt, j  in itertools.product(datasets, rows, cols, ib, qsizes, smg_sizes, has_smqt, has_smt, range(iterations)):
        # Has to be commented out for queue size experiments
        if qs is None:
            if i == b:
                qs = 512
            else:
                qs = 64

        ds = d[0]
        if d[0] == "zipf":
            ds += F"_{d[1]}"

        target = F"{ds}_{m}_{n}_{i}_{b}_{qs}_{sms}_{hsmqt}_{hsmt}_{j}.csv"
        command = f"./simulator {m} {n} {i} {b} {qs} {sms} {hsmqt} {hsmt} ./{ds}_i{j}_o > {target}"
        requirements = [simulator_node]+list(map(lambda x : mg.getNodeByKey(f"{ds}_i{j}_o{x}"), range(m)))
        node = MakeNode(target, command, requirements)
        deps.append(node)
        mg.addNode(node)

    all_node = MakeNode("all", "", deps)
    mg.addNode(all_node)

    mg.makeFile()
