# Codex prompt — recover PMG-WU-005 evidence without rerunning maps

Repository: `cosmosapjw-quantum/htt_base`

Use the actual repair branch:

```text
changeset/planck-mes-paired300-evidence-repair-v2-20260828
```

Read:

```text
docs/codex_handoff/planck_mes_pmg_wu005_evidence_recovery/PACKAGE_INDEX.yaml
docs/codex_handoff/planck_mes_pmg_wu005_evidence_recovery/AUTHORITY_AND_SCOPE.yaml
docs/codex_handoff/planck_mes_pmg_wu005_evidence_recovery/RECOVERY_CONTRACT.yaml
docs/codex_handoff/planck_mes_pmg_wu005_evidence_recovery/P0_P1_THREAT_CATALOG.json
docs/codex_handoff/planck_mes_pmg_wu005_evidence_recovery/INVARIANT_TEST_MATRIX.yaml
docs/codex_handoff/planck_mes_pmg_wu005_evidence_recovery/LOCAL_CHECKPOINT_AND_CLEANUP.yaml
docs/codex_handoff/planck_mes_pmg_wu005_evidence_recovery/CODEX_HANDOFF.md
```

Current authority:

```yaml
executed_result_sha: dded7702f319191e2dd1a88a7a25c64353ea3fb8
executed_result_tree: 318dae5fa3535d0f3d4e32c3558aa6bc8d0058bc
rows_executed: 301
raw_data_mutation: false
work_unit_state: BLOCKED_BY_P1
repair_pull_request: 430
PMG_WU006_started: false
```

Do not rerun the 301 maps. Do not use or trust the pre-review `SUCCEEDED` terminal. Do not restore or mix the user's local legacy docs/plots cleanup.

First preserve the cleanup worktree status/patch and create a separate Git worktree from the remote repair branch. Validate the focused repair tests.

Then use the admitted host paths:

```text
workdir: /mnt/sn850x2t/htt_base_e2e/workdir
portable output: docs/generated/planck_pr3_paired300_irrep_carrier
private checkpoints: /mnt/sn850x2t/htt_base_e2e/workdir/analysis/planck_mes_irrep/paired300_carrier
WU-004 private manifest: /mnt/sn850x2t/htt_base_e2e/workdir/analysis/planck_mes_irrep/intake_manifest.json
private recovery evidence: /mnt/sn850x2t/htt_base_e2e/workdir/analysis/planck_mes_irrep/paired300_evidence_repair
```

Execute the exact `--prepare` command in `CODEX_HANDOFF.md`. It must:

- match the exact observed/mask/300 CMB/300 noise role and row graph to accepted PMG-WU-004 identities;
- hard-bind the frozen scalar NPZ and every pre-review portable artifact;
- classify the preserved post-hoc-bound checkpoints as non-authoritative and not reusable, because the completed result reused zero checkpoints;
- create an artifact manifest and pending terminal;
- report `raw_maps_reopened=false`.

Run one external, read-only fresh review of the repaired diff and exact artifacts. Use `FRESH_REVIEW_RECEIPT_TEMPLATE.json`. PASS requires P0=0, P1=0 and exactly one used repair round. Do not perform another repair under this prompt.

Execute `--finalize`, install the reviewed terminal while archiving the rejected terminal privately, and run:

```bash
python scripts/observed_runs/export_planck_paired300_irrep_carrier.py --replay-committed
```

Required final terminal:

```yaml
format: PLANCK_PR3_PAIRED300_REVIEWED_TERMINAL_V1
work_unit: PMG-WU-005
state: SUCCEEDED
real_host_execution: true
replay_status: MATCH
scalar_closure: MATCH
raw_data_mutation: false
claim_promotion: false
P0_remaining: 0
P1_remaining: 0
unresolved_blockers: []
next_executable_action: PMG-WU-006
```

Commit and push only the bounded repair code/tests and reviewed portable evidence to the existing repair branch. Private manifests, checkpoints, raw data, and legacy cleanup changes must not enter this PR.

PMG-WU-006 may start only after remote readback, exact-head focused CI, and PR #430/parent PR evidence update. A scaffold, pending terminal, or self-attested terminal is not PASS.
