from itertools import product
targets = [
# The big accelerators."
"4096\ 1\ 256\ 4\ 2\ 4",
"4096\ 1\ 128\ 4\ 2\ 8",
"4096\ 1\ 64\ 4\ 2\ 16",
"4096\ 1\ 32\ 4\ 2\ 32"
]


head = F"""
all : {" ".join(map(lambda x : F"{x[0]}.{x[1]}.done", product(targets,range(1,6))))}
"""
print(head)

for t in targets:
    for s in range(1,6):
        target_string = F"""
{t}.{s}.done :
\tbash run_experiment.sh {t} {s} 
\ttouch {t}.{s}.done
"""
        print(target_string)
