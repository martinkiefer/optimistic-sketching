from itertools import product

targets = [
# The big accelerators."
"1\ 4\ 4\ 4096\ 256\ 512\ 1\ 0\ 64",
"1\ 4\ 8\ 4096\ 256\ 64\ 1\ 0\ 2",

"1\ 8\ 8\ 4096\ 128\ 512\ 1\ 0\ 64",
"1\ 8\ 16\ 4096\ 128\ 64\ 1\ 0\ 2",

"1\ 16\ 16\ 4096\ 64\ 512\ 1\ 0\ 64",
"1\ 16\ 32\ 4096\ 64\ 64\ 1\ 0\ 2",

"1\ 32\ 32\ 4096\ 32\ 512\ 1\ 0\ 32",
"1\ 32\ 64\ 4096\ 64\ 64\ 1\ 0\ 2"
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
