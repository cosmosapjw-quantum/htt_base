#!/usr/bin/env bash
# usage: run_one.sh LABEL IMPL FAMILY CELLS DEPTH TIMING
# Runs one case under /usr/bin/time from the repo root, appends a record to logs/commands.tsv.
set -u
W=/home/cosmosapjw/Downloads/htt_r106_analysis/solver_exp/geometry_stage
cd /home/cosmosapjw/Dropbox/bianchi/htt_base || exit 99
export PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
LABEL=$1; IMPL=$2; FAM=$3; CELLS=$4; DEPTH=$5; TIMING=$6
CMD=(.venv/bin/python -B "$W/run_case.py" --impl "$IMPL" --family "$FAM" --cells "$CELLS" --depth "$DEPTH" --timing "$TIMING" --out "$W/runs/$LABEL")
/usr/bin/time -o "$W/logs/$LABEL.time" -f '%e s %M kB' "${CMD[@]}" > "$W/logs/$LABEL.log" 2>&1
RC=$?
printf '%s\t%s\t%s\t%s\n' "$LABEL" "$RC" "$(cat "$W/logs/$LABEL.time" | tail -1)" "cd /home/cosmosapjw/Dropbox/bianchi/htt_base && PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 ${CMD[*]}" >> "$W/logs/commands.tsv"
echo "$LABEL rc=$RC $(tail -1 "$W/logs/$LABEL.time")"
