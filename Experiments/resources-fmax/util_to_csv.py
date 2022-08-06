import sys
import re

state = "SKIP1"
f = open(sys.argv[1])

r = re.compile("__\d+$")

for l in f:
    if state == "SKIP1" and "+--" in l:
        state = "SKIP2"
        continue

    if state == "SKIP2" and "+--" in l:
        state = "PRINT"
        continue

    if state == "PRINT" and "+--" in l:
        break

    if state == "PRINT":
        split = l.split("|")
        try:
            while True:
                split.remove("")
        except ValueError:
            pass

        try:
            while True:
                split.remove("\n")
        except ValueError:
            pass



        split = list(map(lambda x : x.strip(), split))
        if split[0][0] == "(":
            continue


        i = r.search(split[1])
        if i:
            split[1] = split[1][:i.start()] 
        
        print(",".join(split))
