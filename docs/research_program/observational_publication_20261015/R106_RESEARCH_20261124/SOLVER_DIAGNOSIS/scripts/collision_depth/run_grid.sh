#!/usr/bin/env bash
# Usage: run_grid.sh "cells:cap" ...  (runs at most 3 concurrently)
set -u
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
export PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
W=/home/cosmosapjw/Downloads/htt_r106_analysis/solver_exp/collision_depth
one() {
  c=${1%%:*}; k=${1##*:}; tag=c${c}_cap${k}
  /usr/bin/time -f '%e s %M kB' -o $W/logs/$tag.time .venv/bin/python -B $W/run_case.py --cells $c --cap $k --output $W/runs/$tag.json > $W/logs/$tag.log 2>&1
  echo "$tag rc=$? $(cat $W/logs/$tag.time | tail -1)" >> $W/logs/grid_status.txt
}
export -f one; export W
printf '%s\n' "$@" | xargs -P 3 -I{} bash -c 'one {}'
