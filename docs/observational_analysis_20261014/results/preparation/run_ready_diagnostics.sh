#!/usr/bin/env bash
set -euo pipefail
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=htt:htt/htt:htt/src

# Only currently runnable entrypoints are active; physical inference is not auto-promoted.

# DESI_RELEASE_SUMMARY: Released scalar qiso likelihood, DV/rd re-expression and pointwise conditional intervals
/home/cosmosapjw/venv/bin/python -B scripts/analyze_desi_bao_summary.py --input workdir/raw/desi_dr1_fullshape_bgs_bright_v1.2/likelihood/likelihood_bao-recon_syst_BGS_BRIGHT-21.5_GCcomb_z0.1-0.4.h5 --output-dir /home/cosmosapjw/Dropbox/bianchi/htt_base/docs/observational_analysis_20261014/results/preparation/runs/desi

# CF4_GROUPED_DIAGNOSTIC: Observed grouped coverage and conditional response sensitivity; synthetic injection remains a separate validation section
# REUSE_EXISTING_RESULT: /home/cosmosapjw/venv/bin/python -B scripts/r2_cf4_product_diagnostic.py --source workdir/raw/cf4_full --output /home/cosmosapjw/Dropbox/bianchi/htt_base/docs/observational_analysis_20261014/results/preparation/runs/cf4.json

# CMB_SAME_SKY_DIAGNOSTIC: Four common-mask same-sky product contrasts at retained ell=2..5
# REUSE_EXISTING_RESULT: /usr/bin/python -B scripts/r2_cmb_product_diagnostic.py --controls docs/generated/tensor_joint_r8/owned_controls/cmb/cmb_controls.npz --metadata docs/generated/tensor_joint_r8/owned_controls/cmb/cmb.json --output /home/cosmosapjw/Dropbox/bianchi/htt_base/docs/observational_analysis_20261014/results/preparation/runs/cmb.json
