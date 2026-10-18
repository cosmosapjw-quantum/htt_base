#!/usr/bin/env bash
# Run only in the owner's already-integrated primary checkout and native runtime.
# This helper has NOT been executed in the scratch worker.
set -euo pipefail
PLANCK_EXPECTED_REF="${1:?Provide explicit origin/<authorized-continuation-branch>}"
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
ROOT=/mnt/extdrive/workdir/htt_open_data
P=docs/research_program/observational_publication_20261015
S="$P/L01_R8_C8_TWO_MASK_STABILITY_20261017"
PLANCK_PYTHON="${PLANCK_PYTHON:?Set the exact interpreter from the existing native runtime receipt}"
git status --short
git rev-parse HEAD
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
"$PLANCK_PYTHON" "$P/L01_R10_C10_RUNTIME_RECOVERY_20261017/scripts/l01_checkout_guard.py" \
  --expected-ref "$PLANCK_EXPECTED_REF"
"$PLANCK_PYTHON" -m pytest -q "$S/tests/test_l01_matched_split_stream.py"
"$PLANCK_PYTHON" "$S/src/l01_matched_split_stream.py" \
  --root "$ROOT" \
  --native-report "$ROOT/provenance/L01_NATIVE_PIXEL_RESIDUAL_full_20261017T135250Z.json" \
  --injection-report "$ROOT/provenance/L01_LOW_SOURCE_WINDOW_RESPONSE_20261017T150345Z.json" \
  --native-receipt "$ROOT/provenance/L01_NATIVE_PR3_POL_K64x90_v2.json" \
  --chunk-pixels 8192 \
  --out "$ROOT/provenance/L01_NATIVE_MATCHED_SPLITS_$(date -u +%Y%m%dT%H%M%SZ).json"
