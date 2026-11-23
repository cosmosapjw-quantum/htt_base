#!/bin/bash
# usage: run_one.sh LABEL impl mode cells cap family
L=$1; shift
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
export PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
J=/home/cosmosapjw/Downloads/htt_r106_analysis/solver_exp/judge
CMD=".venv/bin/python -B $J/run_case.py --impl $1 --mode $2 --cells $3 --cap $4 --family $5 --out $J/runs/$L.json"
echo "$CMD" > $J/logs/$L.cmd
/usr/bin/time -f '%e s %M kB' -o $J/logs/$L.time $CMD > $J/logs/$L.log 2>&1
echo $? > $J/logs/$L.rc
echo "$L rc=$(cat $J/logs/$L.rc) $(cat $J/logs/$L.time)"
