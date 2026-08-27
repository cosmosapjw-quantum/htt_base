# Codex Execution Prompt — Planck MES Irrep/Global Formalism

Repository: `cosmosapjw-quantum/htt_base`

The canonical global-formalism package remains at:

`docs/codex_handoff/planck_mes_irrep_global_formalism_execution`

PMG-WU-001 has been implemented on PR #419. Do **not** rerun PMG-WU-001.

```yaml
wu001_branch: changeset/planck-mes-observable-irrep-state-20260827
wu001_implementation_commit: 47ef087b158e0dbf8ac4b7b5205f39c1a050d9c0
wu001_implementation_tree: 8abbe9040cb72357387ec3c29f0e1e74921af0ea
pull_request: 419
next_work_unit: PMG-WU-002
```

Use the PMG-WU-002 transition package at:

`docs/codex_handoff/planck_mes_pmg_wu002_execution_transition`

Start with:

`docs/codex_handoff/planck_mes_pmg_wu002_execution_transition/CODEX_HANDOFF_PROMPT.md`

Do not use `analysis/planck-mes-pmg-wu002-transition-20260827`; that ref does not exist.

PR #419 is an open draft. PMG-WU-002 implementation must begin on a fresh branch only after either:

1. PR #419 is accepted/merged and an exact accepted base SHA is recorded; or
2. the user explicitly authorizes stacked execution from the exact package-host head.

Do not guess between those modes.

Non-negotiable semantics remain:

- `ObservableIrrepState` is observer/data space, not physical shear, vorticity, acceleration, geometry, tilt, boost, or Bianchi family.
- `JointAnisotropyState` remains physical/pre-solver.
- `MesPremiseNormalizer` is one-way and cannot create direction, STF shape, response, or independent information.
- `ResponseBoundObservableState` requires a certified matching response and identified-set semantics under rank deficiency.
- Preserve all frozen scalar outputs and exact ranks.
- No Planck map read or scientific result in PMG-WU-002.
- One fresh read-only review and at most one targeted repair.
- No successor planning package.

On PMG-WU-002 PASS, start PMG-WU-003 immediately and execute the map-free coordinate/reducer audit. Never report PASS for documentation-only, tests-only, scaffolded, or unexecuted work.
