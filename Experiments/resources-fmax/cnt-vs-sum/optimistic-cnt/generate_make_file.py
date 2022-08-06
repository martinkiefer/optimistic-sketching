from itertools import product

targets = [
# The big accelerators."
"1\ 16\ 16\ 4096\ 256\ 512\ 0\ 0\ 0",
"1\ 16\ 16\ 4096\ 256\ 512\ 1\ 0\ 0",
"1\ 16\ 16\ 4096\ 256\ 512\ 1\ 0\ 16",
"1\ 16\ 16\ 4096\ 256\ 512\ 1\ 0\ 32",
"1\ 16\ 16\ 4096\ 256\ 512\ 1\ 0\ 64"
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
