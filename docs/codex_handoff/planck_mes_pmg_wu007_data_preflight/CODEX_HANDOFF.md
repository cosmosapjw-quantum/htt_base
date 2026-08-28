# PMG-WU-007 data-transition handoff

## Authority

```yaml
repository: cosmosapjw-quantum/htt_base
branch: changeset/planck-mes-wu007-data-preflight-20260829
stacked_on_wu006: 67a8e08cc24836130c89bab5c1be26ef71d19ca8
operator_report_time: 2026-08-29T00:21:00+09:00
remote_downloads_reported_remaining: 0
active_downloads_reported: 0
raw_data_mutation_reported: false
tracked_repository_mutation_reported: false
```

The operator report is accepted as the current host-state input, but the repository-side preflight must still be run against the real paths. It is metadata-only and does not open FITS payloads.

## Current transition state

```yaml
PMG_WU005:
  state: BLOCKED_BY_P1_PENDING_LOCAL_REBIND
  repair_pr: 430
PMG_WU006:
  state: EXECUTED_CONDITIONALLY_VALID
  result_pr: 431
  map_free: true
  raw_maps_reopened: false
PMG_WU007:
  execution_permission: EXPLORATORY_NONAUTHORITATIVE
  claim_admission: BLOCKED_PENDING_PMG_WU005_REBIND
```

Do not discard or recompute PMG-WU-006 merely because its accepted-predecessor chain is pending. Preserve the numerical result and close the upstream provenance separately.

## Data classification

The required Planck surface for PMG-WU-007 is:

```yaml
SMICA_CMB:
  ids: 00000..00999 excluding 00970
  expected_count: 999
SMICA_noise:
  ids: 00000..00299
  expected_count: 300
Commander_complete_descriptive:
  ids: [00000, 00001, 00002]
Commander_partial_quarantine:
  ids: [00003, 00004, 00005, 00006]
  open_authorized: false
  resume_download_authorized: false
```

The 12 absent entries in the broad observational inventory are not a PMG-WU-007 download blocker. They are local `obs_bundle` targets:

```text
ACT DR6: TT, TE, EE                 3
DESI: BGS/LRG/QSO x NGC/SGC         6
scalar defaults                     3
```

When the corresponding local source products exist, classify these as `LOCAL_PLACEMENT_REQUIRED`, not missing remote data. Do not use the broad inventory's `40/52` count as a reason to reopen downloading.

## Preserve the user's legacy cleanup

From the existing cleanup worktree, record but do not reset:

```bash
git status --porcelain=v1 > /tmp/htt_legacy_cleanup_status_20260829.txt
git diff --binary > /tmp/htt_legacy_cleanup_20260829.patch
```

Create a separate worktree:

```bash
git fetch origin --prune
git worktree add \
  ../htt-planck-mes-wu007-data-preflight-20260829 \
  origin/changeset/planck-mes-wu007-data-preflight-20260829
cd ../htt-planck-mes-wu007-data-preflight-20260829
```

Never run `reset --hard`, `clean -fdx`, or a broad restore in the cleanup worktree.

## Focused verification

```bash
python -m pytest -q tests/contracts/test_planck_mes_wu007_data_preflight.py
python -m py_compile scripts/validate_planck_mes_wu007_data_preflight.py
```

## Real-host preflight

The scalar-source search is deliberately bounded. Pass exact directories with `--scalar-root`; the script will not recursively scan the 1.4 TB store.

```bash
python scripts/validate_planck_mes_wu007_data_preflight.py \
  --workdir /mnt/sn850x2t/htt_base_e2e/workdir \
  --repo-root "$(git rev-parse --show-toplevel)" \
  --scalar-root "$(git rev-parse --show-toplevel)" \
  --json-output \
    /mnt/sn850x2t/htt_base_e2e/workdir/analysis/planck_mes_irrep/wu007_data_preflight.json
```

Add another exact `--scalar-root /path/to/directory` only when a scalar file is located directly in that directory.

Required PASS projection:

```yaml
state: PASS
download:
  mandatory_remote_download_count: 0
  active_downloads: 0
  eta_minutes: 0
  classification: COMPLETE
planck_wu007:
  smica_cmb:
    count: 999
    known_missing_ids: [00970]
  smica_noise:
    count: 300
  commander:
    complete_ids: [00000, 00001, 00002]
    partial_open_authorized: false
obs_bundle:
  target_count: 12
  unresolved_local_source_count: 0
  classification: NO_REMOTE_DOWNLOAD_REQUIRED_LOCAL_PLACEMENT_ONLY
transition:
  wu007:
    execution_permission: EXPLORATORY_NONAUTHORITATIVE
    claim_admission: BLOCKED_PENDING_PMG_WU005_REBIND
raw_data_mutation: false
```

If one local source is unresolved, do not relabel it as a remote download automatically. Report its exact dataset ID and source search roots.

## PMG-WU-007 execution boundary

After preflight PASS, implement and run the already registered WU-007 science lanes:

```text
scripts/observed_runs/run_planck_mes_smica_cmbonly_999.py
scripts/observed_runs/run_planck_mes_commander_observation.py
tests/integration/test_planck_mes_irrep_extended_data.py
```

Preserve these hard boundaries:

- SMICA-999 is a separate CMB-only robustness ensemble; it does not replace paired-300.
- Include row 00818 and exclude only known-missing 00970.
- Every successful map lane must emit carrier plus observable-irrep projection; scalar-only completion is invalid.
- Commander uses the observation and three complete descriptive rows only; `finite_rank_emitted=false`.
- Refuse `.partial` before FITS open.
- Do not tune the primary method to robustness outcomes.
- Before PMG-WU-005 rebind, terminal state must be `EXECUTED_EXPLORATORY_NONAUTHORITATIVE`, not an admitted `SUCCEEDED` chain transition.

The old plan text that checks `intake_summary.json['status']` is not authoritative. The accepted PMG-WU-004 precondition is `docs/generated/planck_mes_irrep_inventory/terminal.json` with `state == 'SUCCEEDED'`.

## Stopping rule

This handoff authorizes one data preflight and the actual WU-007 exploratory execution. It does not authorize another download campaign, meta-review package, Planck PR4/NPIPE substitution, Commander partial recovery, or claim promotion before the WU-005 evidence rebind.
