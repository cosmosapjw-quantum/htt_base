#!/usr/bin/env bash
# usage: run_task.sh label solver n_cells n_picard pi_ee pi_th midpoint
set -u
W=/home/cosmosapjw/Downloads/htt_r106_analysis/solver_exp/matter_feedback
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
export PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
label=$1; solver=$2; n=$3; np_=$4; ee=$5; th=$6; mid=$7
CMD=(.venv/bin/python -B $W/run_case.py --label "$label" --solver "$solver" --n-cells "$n" --n-picard "$np_" --pi-einstein-euler "$ee" --pi-thomson "$th" --midpoint-pi "$mid" --output "$W/runs/$label.json")
/usr/bin/time -f '%e s %M kB' -o "$W/logs/$label.time" "${CMD[@]}" > "$W/logs/$label.log" 2>&1
rc=$?
printf '%s\t%s\t%s\t%s\n' "$label" "$rc" "$(tail -n1 "$W/logs/$label.time")" "cd /home/cosmosapjw/Dropbox/bianchi/htt_base && PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /usr/bin/time -f '%e s %M kB' ${CMD[*]}" >> "$W/logs/commands.tsv"
exit $rc
