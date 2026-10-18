#!/usr/bin/env bash
set -euo pipefail
PKGROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${PKGROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export PYTHONDONTWRITEBYTECODE=1
python3 "${PKGROOT}/src/mes_eps_diagnostic.py" --inputs "${PKGROOT}/inputs" --verify-only
python3 -m pytest -q "${PKGROOT}/tests/test_mes_eps_diagnostic.py"
# Never overwrite the source archive's frozen results, create a fresh outdir.
RUNDIR="$(mktemp -d -t htt-c8-mes-eps-run.XXXXXX)"
python3 "${PKGROOT}/src/mes_eps_diagnostic.py" --inputs "${PKGROOT}/inputs" --output "$RUNDIR"
printf 'Local replay saved: %s/C8_OBS_MES_EPS_RESULT.json\n' "$RUNDIR"
python3 - "$PKGROOT/results/C8_OBS_MES_EPS_RESULT.json" "$RUNDIR/C8_OBS_MES_EPS_RESULT.json" <<'PY'
import sys,json
before=json.load(open(sys.argv[1]));after=json.load(open(sys.argv[2]));
if before!=after:
    raise SystemExit('SOURCE_NUMERICAL_IDENTITY_MISMATCH: do not claim replay PASS')
print('SOURCE_NUMERICAL_IDENTITY_PASS')
PY
