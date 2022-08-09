#!/bin/bash
rm -rf uniform*.bin
head -c 2G </dev/urandom > ./uniform_keys.bin

python ones.py uniform_values.bin
