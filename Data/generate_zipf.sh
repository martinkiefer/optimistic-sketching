#!/bin/bash
python generateZipf.py $1 zipf_${1}_keys.bin
python ones.py zipf_${1}_values.bin

