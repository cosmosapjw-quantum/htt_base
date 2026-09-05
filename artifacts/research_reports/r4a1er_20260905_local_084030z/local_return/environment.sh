export WT=/mnt/sn850x2t/htt_base_e2e/R4A1E_LOCAL_EXISTING_R2_20260905T084030Z/worktree
export RUN=/mnt/sn850x2t/htt_base_e2e/R4A1E_LOCAL_EXISTING_R2_20260905T084030Z/result
export PY=/mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin/python
export PATH=/mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin:/home/cosmosapjw/.elan/toolchains/leanprover--lean4---v4.31.0/bin:/usr/local/bin:/usr/bin:/bin
export ELAN_TOOLCHAIN=leanprover/lean4:v4.31.0
export PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1
unset PYTHONPATH PYTHONHOME LEAN_PATH LEAN_SRC_PATH
cd "$WT"
D=docs/research_reports/verifiers/r4a1nf
