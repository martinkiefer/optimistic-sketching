#!/bin/bash
for rho in 1.05 1.1 1.5; do
    python generateZipf.py $rho zipf_$rho.dump
done
