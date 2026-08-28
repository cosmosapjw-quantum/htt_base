# Codex prompt — run the PMG-WU-007 data preflight, then execute the robustness lanes

Repository: `cosmosapjw-quantum/htt_base`

Use a separate worktree from:

```text
changeset/planck-mes-wu007-data-preflight-20260829
```

Read first:

```text
docs/codex_handoff/planck_mes_pmg_wu007_data_preflight/CODEX_HANDOFF.md
scripts/validate_planck_mes_wu007_data_preflight.py
tests/contracts/test_planck_mes_wu007_data_preflight.py
docs/codex_handoff/planck_mes_irrep_global_formalism_execution/AUDIT_COMPILED_EXEC_PLAN.yaml
```

Current authority:

```yaml
operator_report_time: 2026-08-29T00:21:00+09:00
mandatory_remote_downloads_reported_remaining: 0
active_downloads_reported: 0
PMG_WU005: BLOCKED_BY_P1_PENDING_LOCAL_REBIND
PMG_WU006:
  head: 67a8e08cc24836130c89bab5c1be26ef71d19ca8
  state: EXECUTED_CONDITIONALLY_VALID
  raw_maps_reopened: false
PMG_WU007:
  execution_permission: EXPLORATORY_NONAUTHORITATIVE
  claim_admission: BLOCKED_PENDING_PMG_WU005_REBIND
```

Preserve the user's existing legacy docs/plots cleanup. Record its status and binary patch, then create a separate worktree. Do not reset, clean, restore, or mix the cleanup into this branch.

Run:

```bash
python -m pytest -q tests/contracts/test_planck_mes_wu007_data_preflight.py
python -m py_compile scripts/validate_planck_mes_wu007_data_preflight.py

python scripts/validate_planck_mes_wu007_data_preflight.py \
  --workdir /mnt/sn850x2t/htt_base_e2e/workdir \
  --repo-root "$(git rev-parse --show-toplevel)" \
  --scalar-root "$(git rev-parse --show-toplevel)" \
  --json-output \
    /mnt/sn850x2t/htt_base_e2e/workdir/analysis/planck_mes_irrep/wu007_data_preflight.json
```

The script is metadata-only. It must not open FITS payloads or recursively scan the 1.4 TB workdir. Add exact `--scalar-root` directories only when needed.

PASS requires:

```yaml
SMICA_CMB: exact 999, known_missing=[00970]
SMICA_noise: exact 300
Commander_complete: [00000,00001,00002]
Commander_partial_open_authorized: false
mandatory_remote_download_count: 0
obs_bundle_target_count: 12
obs_bundle_unresolved_local_source_count: 0
WU007_execution_permission: EXPLORATORY_NONAUTHORITATIVE
WU007_claim_admission: BLOCKED_PENDING_PMG_WU005_REBIND
raw_data_mutation: false
```

Do not treat the broad inventory's `40/52` state as a download failure. The 12 absent paths are ACT 3, DESI 6, and scalar 3 local placement/conversion targets. Do not copy large DESI products blindly or duplicate them merely to satisfy a path count; classify and handle that maintenance lane separately.

After preflight PASS, implement and execute the registered WU-007 lanes:

```text
scripts/observed_runs/run_planck_mes_smica_cmbonly_999.py
scripts/observed_runs/run_planck_mes_commander_observation.py
tests/integration/test_planck_mes_irrep_extended_data.py
docs/generated/planck_mes_smica_cmbonly_999/**
docs/generated/planck_mes_commander_observation/**
```

Hard requirements:

- SMICA-999 is separate from and cannot replace paired-300.
- Include 00818; exclude only 00970.
- Same frozen operator/projection schema as the accepted carrier analysis.
- Emit carrier and irrep projection for every successful lane.
- Commander emits no finite rank and uses only the observation plus complete rows 00000..00002.
- Refuse `.partial` before FITS open.
- No raw mutation, no result-selected tuning, no physical-source/Bianchi/local-global/likelihood claim.
- Until PR #430 finishes PMG-WU-005 evidence rebind, emit `EXECUTED_EXPLORATORY_NONAUTHORITATIVE`; do not claim an admitted `SUCCEEDED` transition.

Use the accepted PMG-WU-004 terminal at:

```text
docs/generated/planck_mes_irrep_inventory/terminal.json
```

Do not use the stale plan precondition `intake_summary.json['status']`.

Run focused tests, map-free replay, and one fresh read-only review. Allow at most one targeted repair. Commit and push only WU-007 code/tests/portable evidence. Do not start another download campaign or governance loop.
