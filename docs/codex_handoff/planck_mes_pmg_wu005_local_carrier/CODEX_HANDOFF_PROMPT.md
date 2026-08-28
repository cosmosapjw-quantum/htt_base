# Codex execution prompt — PMG-WU-005

Repository: `cosmosapjw-quantum/htt_base`

Use the existing implementation branch:

```text
changeset/planck-mes-paired300-irrep-carrier-20260828
```

Exact accepted PMG-WU-004 authority:

```yaml
sha: 0864b00948143d9b19d4983e50fcd2d905f4a5d3
tree: 2d96a0e908d8216014f7456891d762eb5e97faca
pull_request: 424
state: SUCCEEDED
```

Read:

```text
docs/codex_handoff/planck_mes_pmg_wu005_local_carrier/PACKAGE_INDEX.yaml
docs/codex_handoff/planck_mes_pmg_wu005_local_carrier/AUTHORITY_BINDING.yaml
docs/codex_handoff/planck_mes_pmg_wu005_local_carrier/REMOTE_IMPLEMENTATION_STATUS.yaml
docs/codex_handoff/planck_mes_pmg_wu005_local_carrier/CODE_PATH_BINDING.yaml
docs/codex_handoff/planck_mes_pmg_wu005_local_carrier/LOCAL_RUNTIME_CONTRACT.yaml
docs/codex_handoff/planck_mes_pmg_wu005_local_carrier/P0_P1_LOCAL_GATES.yaml
docs/codex_handoff/planck_mes_pmg_wu005_local_carrier/PORTABILITY_FINDING.yaml
docs/codex_handoff/planck_mes_pmg_wu005_local_carrier/GUIDE_BINDING.yaml
docs/codex_handoff/planck_mes_pmg_wu005_local_carrier/CODEX_HANDOFF.md
```

The strict carrier writer/replay and eight focused tests are already implemented and GREEN. Do not rewrite them unless a focused test reproduces a defect.

Implement and execute only the remaining real-host part of **PMG-WU-005**.

Use:

```text
/mnt/sn850x2t/htt_base_e2e/workdir
```

Core rule:

```text
_process_map already returns features, timings, alm.
Capture that alm in the same pass.
Do not reconstruct a carrier from scalar features.
Do not run a second estimator.
```

Required local work:

1. write integration RED tests for one-pass carrier threading, exact row order, same-operator identity, scalar closure, raw immutability, and fixed ell>5 leakage probes;
2. add the smallest worker/export delta;
3. execute observed SMICA plus the exact 300 paired CMB+noise rows;
4. write the seven required portable outputs;
5. replay without maps;
6. run risk-scoped regressions;
7. perform one fresh read-only review and at most one bounded repair.

Hard constraints:

- raw/download roots are read-only;
- preserve exact 301-row order;
- no row drop or replacement;
- no tolerance adjustment after seeing results;
- no 999, Commander, irrep rank, likelihood, paper, or physical inference;
- no scalar-to-direction fabrication;
- no successor planning package;
- no PASS for partial execution.

Required terminal:

```yaml
work_unit: PMG-WU-005
state: SUCCEEDED
real_host_execution: true
replay_status: MATCH
scalar_closure: MATCH
raw_data_mutation: false
claim_promotion: false
unresolved_blockers: []
next_executable_action: PMG-WU-006
```

On PASS, start PMG-WU-006 immediately.
