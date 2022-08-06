#!/bin/bash
rm -rf uniform*.bin
head -c 2G </dev/urandom > ./uniform_key.bin
