# Codex prompt — execute PMG-WU-004 only

Repository: `cosmosapjw-quantum/htt_base`

Branch: `changeset/planck-mes-irrep-data-intake-20260828`

Accepted predecessor:

```yaml
sha: 03f002d97deb31648f47a9a5bdc0e7706354909e
tree: 1d4447dbf90e0a7170fbe68e5db287e91e4d0391
pull_request: 422
```

Read, in order:

```text
docs/codex_handoff/planck_mes_pmg_wu004_local_intake/PACKAGE_INDEX.yaml
docs/codex_handoff/planck_mes_pmg_wu004_local_intake/AUTHORITY_BINDING.yaml
docs/codex_handoff/planck_mes_pmg_wu004_local_intake/LOCAL_RUNTIME_CONTRACT.yaml
docs/codex_handoff/planck_mes_pmg_wu004_local_intake/P0_P1_LOCAL_GATES.yaml
docs/codex_handoff/planck_mes_pmg_wu004_local_intake/CODEX_HANDOFF.md
```

Then implement and execute **PMG-WU-004 only**.

Use TDD. Add the read-only inventory inspector and its focused integration test, then run it on:

```text
/mnt/sn850x2t/htt_base_e2e/workdir
```

Required facts:

```text
SMICA CMB 00000..00999 excluding only 00970 = 999
SMICA noise 00000..00299 = 300
Commander complete 00000..00002
Commander partial 00003..00006 quarantined before FITS open
00818 decided by FITS semantics and streaming digest, never size alone
NPIPE absent
hsc_kids contains no admitted HSC/SACC payload
```

Hard constraints:

- raw/download/private source roots are read-only;
- refuse symlink escape;
- no full 910-GiB preflight hash;
- no raw or private manifest in Git;
- no scientific rank, carrier, paper, or physical-claim work;
- no successor planning package;
- one fresh review and at most one bounded repair;
- a scaffold or tests-only patch is not PASS.

Required outputs:

```text
docs/generated/planck_mes_irrep_inventory/intake_summary.json
docs/generated/planck_mes_irrep_inventory/route_receipt.json
docs/generated/planck_mes_irrep_inventory/selected_input_manifest.json
docs/generated/planck_mes_irrep_inventory/terminal.json
/mnt/sn850x2t/htt_base_e2e/workdir/analysis/planck_mes_irrep/intake_manifest.json
```

On PASS, immediately start PMG-WU-005. On invalid inventory, mutation, escape, or unresolved 00818 semantics, emit the narrow typed BLOCKED state and stop.
