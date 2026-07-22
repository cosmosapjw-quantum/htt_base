# HTT External-Fusion Round-3 Bundle

This self-contained planning and reference-code bundle integrates external cosmology software with HTT's response-rank, partial-identification, coverage and source-discrimination framework. It continues the proposed roadmap at **PR-247** and adds a dedicated **redshift/depth-resolved CMB low-ell pole programme** for distinguishing an observer-end local boost from finite-depth local structure and a coherent global source.

The core reference suite needs only NumPy and SciPy. External cosmology packages are fail-closed optional plugins: a missing package creates a blocked capability receipt, never a toy result stamped as an external result.

## Main documents

- `docs/01_HOSTILE_REFEREE_STEELMAN_EXTERNAL_FUSION.md`
- `docs/02_ADVOCATE_STEELMAN_UPGRADE_EXTERNAL_FUSION.md`
- `docs/03_EXTERNAL_FUSION_PR_ROADMAP_20260722.md`
- `docs/04_PUBLICATION_READINESS_MASTER_CHECKLIST_EXTERNAL_FUSION.md`
- `docs/05_REDSHIFT_DEPTH_LOWELL_POLE_PROGRAM.md`
- `docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md`
- `docs/09_EXECUTABLE_ASSET_CATALOG.md`
- `docs/10_PACKAGE_VALIDATION.md`

Machine-readable cards live in `pr_cards/`, `PR_GATE_MATRIX.json`, `HOSTILE_ADVOCATE_MATRIX.json`, `configs/` and `schemas/`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-core.txt
make validate
```

`make validate` checks the frozen release manifest. After intentionally modifying the bundle, review the diff and use `make freeze` to generate a new manifest.

Probe optional integrations:

```bash
make plugin-probe
```

Candidate package groups are in `requirements-profiles/*.in`. They are deliberately not frozen locks: each PR must choose and pin exact versions after its official example and license checks.

## Local htt_base overlay

Install non-destructively under `external_fusion_round3/` inside a local checkout:

```bash
python tools/install_into_repo.py --repo /path/to/htt_base --dry-run
python tools/install_into_repo.py --repo /path/to/htt_base --apply
cd /path/to/htt_base/external_fusion_round3
make validate
```

Add `--include-context` only when the bundled historical planning references are needed inside the checkout.

## Low-ell pole reference commands

```bash
PYTHONPATH=src python experiments/rotation_covariance_test.py
PYTHONPATH=src python experiments/lowell_shell_poles_demo.py
PYTHONPATH=src python experiments/shell_kernel_conservation_demo.py
PYTHONPATH=src python experiments/local_boost_global_tilt_benchmark.py
PYTHONPATH=src python experiments/remote_fields_demo.py
```

Optional Planck commands require user-supplied official FITS files and `healpy`:

```bash
PYTHONPATH=src python experiments/planck_lowell_poles.py MAP.fits --mask-fits MASK.fits
PYTHONPATH=src python experiments/planck_map_family_compare.py \
  --map SMICA=SMICA.fits --map COMMANDER=COMMANDER.fits --mask MASK.fits
```

These Planck scripts are quicklook adapters. Publication use requires matched mask/foreground/null calibration under the relevant PR gates.

## Track boundary

Track I may use FLRW simulators, LSS mocks, remote-field phenomenology and actual-data summaries, but it may not emit Bianchi family or geometry claims. Track II remains intentionally blocked until a real native Bianchi Boltzmann `SolverDeliveryReceipt` passes `schemas/solver_delivery_receipt.schema.json` and all independent benchmark gates.
