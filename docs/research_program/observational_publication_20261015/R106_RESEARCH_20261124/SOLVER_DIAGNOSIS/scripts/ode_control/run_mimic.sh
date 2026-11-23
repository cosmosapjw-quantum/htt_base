#!/usr/bin/env bash
# usage: run_mimic.sh CELLS
set -u
CELLS=$1; LABEL=mimic_c$CELLS
W=/home/cosmosapjw/Downloads/htt_r106_analysis/solver_exp/ode_control
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
export PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
CMD=(.venv/bin/python -B $W/mimic_case.py --cells $CELLS --output $W/runs/$LABEL.json)
echo "${CMD[*]}" > $W/logs/$LABEL.cmd
/usr/bin/time -o $W/logs/$LABEL.time -f '%e s %M kB' "${CMD[@]}" > $W/logs/$LABEL.log 2>&1
RC=$?
echo $RC > $W/logs/$LABEL.rc
echo "$LABEL rc=$RC $(tail -1 $W/logs/$LABEL.time)"
