# Executed commands and continuation boundary

Working directory: `/mnt/sn850x2t/htt_base_e2e/TENSOR-JOINT-R8-20260909/worktree`.
Python: `/mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin/python` (Python 3.12.3).
Set `PYTHONPATH="$PWD/htt/htt:$PWD/htt/src:$PWD/htt:$PWD"` and `PYTHONDONTWRITEBYTECODE=1`.

The actual productive runs were:

```sh
python -B scripts/observed_runs/run_r8_restricted_history.py \
  --out docs/generated/tensor_joint_r8/restricted_history \
  --archive /home/cosmosapjw/Dropbox/bianchi/rec_bianchi/archive/inputs/bianchi_background_solver_v87/bianchireview87.tar.gz
OPENBLAS_NUM_THREADS=1 python -B scripts/observed_runs/run_r8_orbit_continuation.py \
  --saved-root /mnt/sn850x2t/htt_base_e2e/TENSOR-JOINT-R8-20260909/numerical_runs \
  --out docs/generated/tensor_joint_r8/orbit_continuation
python -B scripts/observed_runs/r8_product_intake.py
python -B -m pytest -o addopts='' --import-mode=importlib -q \
  tests/r8 tests/r7/test_mes_region.py tests/r7/test_joint_experiment.py
python -B scripts/observed_runs/run_tensor_joint_r8.py \
  --dag docs/research_program/tensor_joint_r8/campaign_dag.json \
  --run-dir docs/generated/tensor_joint_r8/final/campaign --dry-plan
python -B scripts/observed_runs/run_tensor_joint_r8.py \
  --dag docs/research_program/tensor_joint_r8/campaign_dag.json \
  --run-dir docs/generated/tensor_joint_r8/final/campaign
python -B scripts/observed_runs/run_tensor_joint_r8.py \
  --dag docs/research_program/tensor_joint_r8/campaign_dag.json \
  --run-dir docs/generated/tensor_joint_r8/final/campaign \
  --evidence-dir docs/generated/tensor_joint_r8/final --resume
python -B scripts/observed_runs/build_r8_final_report.py
```

The first full campaign has 52 new attempts. Current-source validation invalidated 27 dependent attempts; unchanged receipts were reused. The completed old A/B/D/E experiments were not replayed. The saved mock5 file under `final/mocks` is a byte-identical copy for the explicit final evidence directory, not a new experiment.

## Next-session instruction

Start from this implementation branch and its published commit, not the unrelated dirty main checkout. Read REPORT.md, REVIEW.md, IMPLEMENTATION_STATUS.md and the canonical PR-247 card. All 52 action handlers are implemented and terminal. Do not restart this campaign as if 39 handlers remain missing. Do not repeat the 54-history/432-ray grid, completed representation/jet/field controls, or the fixed 30-pool continuation merely to activate a policy.

If further scientific admission is requested, scope the exact missing obligation first: independent A/B/D CAS acceptance; the held mixture diagnostic; a product-specific CMB/CF4/JWST or R3 response/sampling law; or strict scheduler deadline enforcement. The 25 unresolved ranks remain valid intervals and preserve their original targets. A new resource allocation is required for additional checkpoints. `load_pool(path)` reads the saved exact pair trees and banks; the existing continuation driver returns completed receipts without consuming another checkpoint. Missing or changed source inputs must not be replaced silently.

No merge, native solver admission or empirical physical confidence is authorized by this delivery.
