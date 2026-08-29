# Codex execution prompt — apply and execute PMG-WU-008

Repository: `cosmosapjw-quantum/htt_base`

Checkout in a **new clean worktree**:

```text
changeset/planck-mes-irrep-injection-power-foundation-20260829
```

Do not touch the user's clean `codex_emergency` checkout or the preserved recovery
directory. Do not query, rerun, or inspect GitHub Actions.

## 1. Apply the content-bound foundation

```bash
bash docs/codex_handoff/planck_mes_pmg_wu008_overlay/apply_overlay.sh
```

Then read the applied canonical prompt and contract:

```text
docs/codex_handoff/planck_mes_pmg_wu008_injection_power/CODEX_HANDOFF_PROMPT.md
docs/codex_handoff/planck_mes_pmg_wu008_injection_power/WU008_EXECUTION_CONTRACT.yaml
docs/codex_handoff/planck_mes_pmg_wu008_injection_power/IMPLEMENTATION_PLAN.md
```

## 2. Validate and commit the foundation

```bash
python scripts/validate_planck_mes_pmg_wu008_injection_power.py
python -m pytest -q \
  tests/obsstat/test_planck_irrep_injections.py \
  tests/integration/test_planck_mes_irrep_injections.py \
  tests/contracts/test_planck_mes_pmg_wu008_injection_power.py
python -m py_compile \
  htt/obsstat/planck_irrep_injections.py \
  scripts/observed_runs/run_planck_mes_irrep_injections.py \
  scripts/validate_planck_mes_pmg_wu008_injection_power.py
git diff --check
```

Review the applied diff. Commit it as a code-only candidate, then run:

```bash
python scripts/validate_planck_mes_pmg_wu008_injection_power.py --check-git
```

## 3. Execute PMG-WU-008 only

```bash
python scripts/observed_runs/run_planck_mes_irrep_injections.py --execute
```

Frozen design:

```yaml
templates: 5
amplitudes: 13
orientation_nodes: 48 deterministic seedless SO(3) nodes
baseline_clusters_per_lane: 64
lanes: [paired-300, SMICA CMB-only-999]
coordinate_reducer: exact cross-fitted LOO-ECDF
combiners: [min-p, empirically calibrated Fisher]
alpha: 1/20
maps_opened: 0
```

The physical Bianchi-template lane remains `DEFERRED_NOT_ATTEMPTED`; the exact
formula SSOT/atlas is not an evolved sky template. Do not add a physical-looking
substitute.

## 4. Review and close

Run the risk-scoped regressions listed in the implementation plan. Inspect all three
figures directly at 3.3-inch and 6.8-inch widths. Obtain one independent read-only
fresh review; allow at most one targeted repair.

Finalize with the exact review receipt, then execute:

```bash
python scripts/observed_runs/run_planck_mes_irrep_injections.py --replay-committed
```

Replay must recompute the full map-free power study and return `MATCH` with
`maps_opened=0` and `raw_data_mutation=false`.

Push only the applied foundation and reviewed portable WU-008 evidence to the same
branch. A weak or null power result is a valid completion. PMG-WU-009 starts only
after the reviewed terminal has remote readback.
