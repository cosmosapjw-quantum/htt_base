# Codex execution prompt — PMG-WU-007

Repository: `cosmosapjw-quantum/htt_base`

Checkout the actual package branch:

```text
changeset/planck-mes-wu007-smica999-preflight-20260829
```

Exact accepted PMG-WU-006 authority:

```yaml
sha: 242eb4b9904a0c5d8514f3b50c7341d4837d71f5
tree: 86c580bbdd9d465992b2db6532d1086e1ec1ce9a
pull_request: 434
state: SUCCEEDED
replay_status: MATCH
next_executable_action: PMG-WU-007
```

Read, in order:

```text
docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution/PACKAGE_INDEX.yaml
docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution/AUTHORITY_BINDING.yaml
docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution/DATA_AVAILABILITY_BINDING.yaml
docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution/WU007_EXECUTION_CONTRACT.yaml
docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution/EVIDENCE_ADAPTIVE_CLAIM_ENVELOPE.yaml
docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution/REFEREE_FINDINGS_ROUTE.yaml
docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution/P0_P1_THREAT_CATALOG.json
docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution/INVARIANT_TEST_MATRIX.yaml
docs/codex_handoff/planck_mes_pmg_wu007_smica999_local_execution/CODEX_HANDOFF.md
```

Validate the package and committed preflight tests. Then execute the read-only preflight on `/mnt/sn850x2t/htt_base_e2e/workdir`.

No additional download is required or permitted.

After preflight PASS, create:

```text
changeset/planck-mes-smica-cmbonly-999-irrep-20260829
```

Implement and execute **PMG-WU-007 only**.

Core execution contract:

```text
observation row:
  reuse accepted one-pass observation carrier; do not reopen the observation map

null rows:
  official SMICA CMB-only IDs 00000..00999 excluding only 00970
  exactly 999
  include 00818
  read zero noise maps

operator:
  exact accepted joint-cutsky operator, mask, beam/pixel transfer,
  real-harmonic layout, frame and units

outputs:
  same-row scalar projection + 32-component low-ell carrier
  frozen WU-006 irrep families under both accepted reducers
  separate robustness schema/path/null identity
```

Hard prohibitions:

- do not query, rerun, or inspect GitHub Actions;
- do not download data;
- do not overwrite or supersede the paired-300 primary;
- do not change features, tails, reducers, tolerances or expected primary ranks;
- do not reconstruct a carrier from scalar features;
- do not read paired noise maps;
- do not run Commander/NILC/SEVEM/NPIPE;
- do not perform injection/power work;
- do not infer foreground, shear, vorticity, local/global origin or Bianchi family;
- do not promote claims because a rank is small;
- do not create another plan or audit package;
- do not report PASS for preflight, partial execution, or tests alone.

Use TDD, local focused verification, one independent read-only fresh review and at most one bounded repair. Bind all required outputs and exact figure inspection to a reviewed terminal.

On PASS, start PMG-WU-008 immediately.
