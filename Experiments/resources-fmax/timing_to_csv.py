import sys
import re

state = "SKIP1"
f = open(sys.argv[1])

for l in f:
    if state == "SKIP1" and "WNS(ns)" in l:
        state = "SKIP2"
        continue

    if state == "SKIP2":
        state = "GRAB_WNS"
        continue

    if state == "GRAB_WNS":
        wcns = float(l.split()[0])
        state = "SKIP3"
        continue

    if state == "SKIP3" and "Waveform(ns)" in l:
        state="SKIP4"
        continue

    if state == "SKIP4":
        state="GRAB_TARGET_PERIOD"
        continue

    if state == "GRAB_TARGET_PERIOD":
        target_period = float(l.split()[3])
        break

print(F"{1000/target_period},{1000/(target_period-wcns)}")
