#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
target="${1:-/mnt/sn850x2t/htt_base_e2e/workdir/raw/desi_dr1_mocks}"
retry_wait="${DESI_RETRY_WAIT_SECONDS:-60}"
max_restarts="${DESI_MAX_RESTARTS:-0}"
aria_jobs="${DESI_ARIA_JOBS:-3}"
batch_size="${DESI_BATCH_SIZE:-10}"

cd "$repo_root"

restart_count=0
while true; do
  if venv/bin/python -B dl_pipeline/scripts/download_desi_dr1_mocks.py \
      --target "$target" \
      --aria-jobs "$aria_jobs" \
      --batch-size "$batch_size" \
      --audit-ez-count 10 \
      --audit-abacus-count 5; then
    break
  else
    rc=$?
  fi
  restart_count=$((restart_count + 1))
  printf 'DESI acquisition attempt failed rc=%s restart=%s; preserving .part files and retrying in %ss\n' \
    "$rc" "$restart_count" "$retry_wait"
  if [[ "$max_restarts" -gt 0 && "$restart_count" -ge "$max_restarts" ]]; then
    printf 'DESI acquisition reached DESI_MAX_RESTARTS=%s\n' "$max_restarts" >&2
    exit "$rc"
  fi
  sleep "$retry_wait"
done

venv/bin/python -B scripts/desi_official_mock_card.py \
  --acquisition-manifest "$target/desi_dr1_mock_acquisition_manifest.json" \
  --jobs 12

venv/bin/python -B scripts/codex_harness/run_pr151_desi_exact_selection.py --write
venv/bin/python -B scripts/desi_official_mock_card.py \
  --acquisition-manifest "$target/desi_dr1_mock_acquisition_manifest.json" \
  --jobs 12 --check
venv/bin/python -B scripts/codex_harness/run_pr151_desi_exact_selection.py --check
