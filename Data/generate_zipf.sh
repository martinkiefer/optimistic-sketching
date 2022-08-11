#!/bin/bash
rm -f zipf_${1}_*.bin zipf_${1}.bin
python generateZipf.py $1 zipf_${1}_keys.bin
python ones.py zipf_${1}_values.bin
python rowify.py zipf_${1}_keys.bin zipf_${1}_values.bin zipf_${1}.bin
