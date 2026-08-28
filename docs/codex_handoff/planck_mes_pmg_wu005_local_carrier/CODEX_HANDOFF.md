# PMG-WU-005 local execution handoff

## Exact state

```yaml
repository: cosmosapjw-quantum/htt_base
work_unit: PMG-WU-005
accepted_predecessor_branch: changeset/planck-mes-irrep-data-intake-20260828
accepted_predecessor_sha: 0864b00948143d9b19d4983e50fcd2d905f4a5d3
accepted_predecessor_tree: 2d96a0e908d8216014f7456891d762eb5e97faca
accepted_predecessor_pr: 424
implementation_branch: changeset/planck-mes-paired300-irrep-carrier-20260828
implementation_pr: 426
remote_implementation_state: PARTIAL_REMOTE_IMPLEMENTATION
work_unit_state: NOT_YET_EXECUTED
```

This package narrows the already-compiled PMG-WU-005 contract to the actual local NVMe execution. It is not a successor plan.

## What is already implemented and verified remotely

```text
htt/obsstat/planck_irrep_carrier.py
tests/obsstat/test_planck_irrep_carrier.py
```

The implementation provides:

- strict `float64` `(32,) + (300,32)` carrier validation;
- exact 301-row identity and registered null-order hashing;
- frozen real-harmonic layout binding for ell=2..5;
- operator, mask, beam/pixel, source-manifest, and scalar-package identities;
- atomic no-pickle NPZ plus strict JSON metadata;
- map-free replay and mutation refusal;
- feature-specific scalar-closure criteria;
- an explicit observer-space-only claim ceiling.

TDD evidence:

```text
RED:
  commit 5989c7f1ff0e948cb4c927fc5358ada1b0a9f1a3
  run https://github.com/cosmosapjw-quantum/htt_base/actions/runs/33144905940

GREEN:
  implementation commit 34c618e349555d7bdebcd13b76a3576c895e3044
  run https://github.com/cosmosapjw-quantum/htt_base/actions/runs/33145112074
  result 8 passed; py_compile PASS; git diff --check PASS
```

These are enabling outputs. They are not evidence that the 301-row raw-map execution has occurred.

## Code-path reality

The frozen operator already returns the missing information:

```text
fit_joint_cutsky_alm(...)
  -> JointCutSkyFit.retained_alm
  -> JointCutSkyFit.retained_coefficients  # 32 real numbers
```

The current worker also returns it:

```text
_process_map(...)
  -> features, timings, alm
```

The loss occurs later:

```text
_process_ffp10_component(...)
  -> keeps features
  -> discards alm

run_pr315_joint_cutsky_attended(...)
  -> keeps observed features
  -> discards observed alm
```

Do not alter the estimator to recover the carrier. Capture the existing third return in the same pass.

## First commands

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

git fetch origin --prune
git switch changeset/planck-mes-paired300-irrep-carrier-20260828
git pull --ff-only

git cat-file -e 0864b00948143d9b19d4983e50fcd2d905f4a5d3^{commit}
test "$(git rev-parse 0864b00948143d9b19d4983e50fcd2d905f4a5d3^{tree})" = "2d96a0e908d8216014f7456891d762eb5e97faca"
git merge-base --is-ancestor 0864b00948143d9b19d4983e50fcd2d905f4a5d3 HEAD

python -m pytest -q tests/obsstat/test_planck_irrep_carrier.py

python - <<'PY'
import json
from pathlib import Path
p = json.loads(Path(
    "docs/generated/planck_mes_irrep_inventory/terminal.json"
).read_text())
assert p["state"] == "SUCCEEDED"
assert p["next_executable_action"] == "PMG-WU-005"
assert p["raw_data_mutation"] is False
PY

export HTT_WORKDIR=/mnt/sn850x2t/htt_base_e2e/workdir
test -d "$HTT_WORKDIR/raw"
test -f "$HTT_WORKDIR/analysis/planck_mes_irrep/intake_manifest.json"
```

## Implement only the remaining local delta

Allowed source/test surfaces:

```text
scripts/observed_runs/run_planck_pr3.py
scripts/observed_runs/export_planck_paired300_irrep_carrier.py
tests/integration/test_planck_irrep_carrier_execution.py
docs/generated/planck_pr3_paired300_irrep_carrier/**
```

The serializer module and its focused tests may be repaired only for a reproduced defect.

### Required worker change

1. Add a one-pass row function that returns both the frozen 12 features and the exact 32 retained real coefficients.
2. Preserve the existing `_process_map` mathematics and operator identity.
3. Capture the observed carrier from the same fit.
4. Preserve exact null row order `FFP10-SMICA-CMBNOISE-00000..00299`.
5. Never run a second estimator just to obtain the carrier.

### Required raw path

Reuse the existing admitted functions in `scripts/observed_runs/prepare_planck_pr3_admission.py`:

```text
inspect_smica_cmb_noise_inventory
read_temperature_fits
reduce_temperature_map
reduce_smica_cmb_plus_noise
read_temperature_beam
read_mask_fits
reduce_mask
```

The registered semantics are:

```text
CMB_i + noise_i in K_CMB
-> one band-limited reduction
-> microK_CMB at the frozen nside/operator
```

Do not download, repair, copy, normalize, or alter raw inputs.

### Resumability

Use host-private checkpoints under:

```text
$HTT_WORKDIR/analysis/planck_mes_irrep/paired300_carrier/
```

Checkpoints must bind:

```text
row_id
CMB path/stat/content identity
noise path/stat/content identity
feature row
carrier row
completion state
```

A completed row may be reused only if all bound source identities still match.

## Required outputs

```text
docs/generated/planck_pr3_paired300_irrep_carrier/carrier.npz
docs/generated/planck_pr3_paired300_irrep_carrier/metadata.json
docs/generated/planck_pr3_paired300_irrep_carrier/scalar_closure.json
docs/generated/planck_pr3_paired300_irrep_carrier/input_identity_receipt.json
docs/generated/planck_pr3_paired300_irrep_carrier/leakage_receipt.json
docs/generated/planck_pr3_paired300_irrep_carrier/replay.json
docs/generated/planck_pr3_paired300_irrep_carrier/terminal.json
```

The private checkpoint and full raw execution manifest remain outside Git.

## Leakage receipt

Use fixed, predeclared ell>5 probes and the exact mask/operator. Do not choose modes after seeing the observation. The receipt is diagnostic; it does not correct the observed carrier or create a new statistic.

## Verification

```bash
python -m pytest -q \
  tests/obsstat/test_planck_irrep_carrier.py \
  tests/integration/test_planck_irrep_carrier_execution.py

python -m pytest -q \
  tests/integration/test_planck_irrep_carrier_execution.py \
  -k 'row or operator or closure or mutation or forged or missing'

python -m pytest -q \
  tests/integration/test_planck_mes_morphology.py \
  tests/paper/test_planck_mes_first_paper.py

python \
  scripts/observed_runs/export_planck_paired300_irrep_carrier.py \
  --replay-committed

git diff --check
```

Do not run the full suite unless a distinct cross-surface failure is first reproduced.

## Review and completion

Run one fresh-context read-only review. Apply at most one bounded repair for a reproduced current-task P0/P1.

`PASS` requires:

```text
real_host_execution=true
carrier replay=MATCH
scalar closure=MATCH
exact row count/order
frozen scalar ranks unchanged
leakage receipt present
pre/post raw immutability=MATCH
P0=0
P1=0
next_executable_action=PMG-WU-006
```

A serializer, tests, script, checkpoint, or partially completed row set is `PARTIAL`, not `PASS`.
