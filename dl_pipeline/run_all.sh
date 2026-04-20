#!/usr/bin/env bash
# ============================================================================
# run_all.sh — single-command BASS data pipeline runner
#
#   bash run_all.sh                       # default workdir = ./workdir
#   bash run_all.sh /path/to/workdir
#
# Environment variables (all optional):
#   FORCE=1                  re-download / re-extract even if outputs exist
#   SKIP_HEAVY=1             skip large pip installs in env stage
#   SKIP_LARGE_MAPS=1        skip ~3 GB Planck Commander/SMICA maps
#   SCALARS_ROOT=/path       repo containing obs_defaults*.json
#   ACT_DR6_SACC_URL=...     URL for ACT DR6 sacc file (if known)
#   CF4_GRID_URL=...         override the built-in CF4++ grid URL if needed
#   BASS_VENV_PY=/path/py    override default venv python (default: ../venv/bin/python)
#   BUNDLE_ZIP=1             also write obs_bundle.zip (off by default for local dev)
#   PLANCK_NSIDE_OUT=N       NSIDE for Planck map/mask downgrade (default 16)
#   FULL_RES_MAPS=1          also dump NSIDE=2048 Planck map/mask NPZs
#   DESI_MODE=minimal|extended  DESI column set (default: extended)
#
# Stages run by --all (in order):
#   env, planck_pr3, bicep_keck, planck_lensing, act_dr4, act_dr6,
#   spt3g_y1, desi_y1, cf4, camb_refs, scalars, package
# ============================================================================
set -euo pipefail

WORKDIR="${1:-$PWD/workdir}"
PIPELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$PIPELINE_DIR/.." && pwd)"
FETCH="$PIPELINE_DIR/scripts/fetch.py"
VENV_PY="${BASS_VENV_PY:-$REPO_ROOT/venv/bin/python}"

if [[ ! -f "$FETCH" ]]; then
    echo "[err] $FETCH not found — are you running this from the dl_pipeline dir?" >&2
    exit 2
fi

if [[ ! -x "$VENV_PY" ]]; then
    echo "[err] venv python not found at: $VENV_PY" >&2
    echo "      Create it with: python3 -m venv $REPO_ROOT/venv && $REPO_ROOT/venv/bin/pip install -r $PIPELINE_DIR/requirements.txt" >&2
    echo "      Or override with BASS_VENV_PY=/path/to/python bash run_all.sh ..." >&2
    exit 2
fi

if [[ "$WORKDIR" == /path/to/* ]]; then
    echo "[err] refusing placeholder workdir: $WORKDIR" >&2
    exit 2
fi

# Build optional flags from env
FLAGS=()
[[ "${FORCE:-0}" == "1" ]]            && FLAGS+=(--force)
[[ "${SKIP_HEAVY:-0}" == "1" ]]       && FLAGS+=(--skip-heavy)
[[ "${SKIP_LARGE_MAPS:-0}" == "1" ]]  && FLAGS+=(--skip-large-maps)
[[ "${BUNDLE_ZIP:-0}" == "1" ]]       && FLAGS+=(--bundle-zip)
[[ "${FULL_RES_MAPS:-0}" == "1" ]]    && FLAGS+=(--full-res-maps)
[[ -n "${PLANCK_NSIDE_OUT:-}" ]]      && FLAGS+=(--planck-nside-out "$PLANCK_NSIDE_OUT")
[[ -n "${DESI_MODE:-}" ]]             && FLAGS+=(--desi-mode "$DESI_MODE")
[[ -n "${SCALARS_ROOT:-}" ]]          && FLAGS+=(--scalars-root "$SCALARS_ROOT")

mkdir -p "$WORKDIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " BASS data pipeline"
echo " workdir : $WORKDIR"
echo " python  : $VENV_PY"
echo " flags   : ${FLAGS[*]:-(none)}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

"$VENV_PY" "$FETCH" --root "$WORKDIR" --all "${FLAGS[@]}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Final bundle: $WORKDIR/obs_bundle.zip"
echo " Logs:          $WORKDIR/logs/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
