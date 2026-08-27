# Codex Execution Prompt — Planck MES Irrep/Global Formalism

Repository: `cosmosapjw-quantum/htt_base`

Use the repository package at:

`docs/codex_handoff/planck_mes_irrep_global_formalism_execution`

The active planning branch is `analysis/planck-mes-extended-data-execution-20260826`. Its frozen predecessor is
`2669a55ef230d1ca9e79c09d3344f7b15c50ac0e` and canonical scientific base is
`changeset/pr324-mes-methodology-stack-20260826@3cdeaba39e164c911a26c5daa37f0e15b29614d3`.

Your task is to implement and execute **exactly one** active work unit at a
time, beginning with `PMG-WU-001`. Do not execute the superseded
`PED-WU-001..004` order.

Before changing code:

1. run `python scripts/validate_planck_mes_irrep_global_formalism_plan.py`;
2. read the active pointer, `AUTHORITY_AND_SCOPE.yaml`,
   `PRIOR_PLAN_SUPERSESSION.yaml`, `FORMALISM_CONTRACT.yaml`,
   `FORMALISM_MIGRATION_MATRIX.yaml`, `P0_P1_THREAT_CATALOG.json`,
   `INVARIANT_TEST_MATRIX.yaml`, and the selected work unit;
3. verify exact Git ancestry;
4. inspect only the source/tests named by that work unit.

Non-negotiable semantics:

- `ObservableIrrepState` is observer/data space and is not physical shear,
  vorticity, acceleration, geometry, global tilt, local boost, or a Bianchi
  family.
- `JointAnisotropyState` remains physical/pre-solver.
- `MesPremiseNormalizer` is a one-way normalizer and cannot create direction,
  STF shape, response, or independent information.
- `ResponseBoundObservableState` requires a certified matching response.
- Preserve all frozen scalar outputs and exact ranks.
- Every new Planck map read must serialize the complete 32-dimensional
  retained harmonic carrier.
- Observation/null/injection rows use the same registered operator,
  projection, reducer, tail, and degeneracy policy within a pool.
- The 999 CMB-only pool never replaces the paired-300 primary.
- Commander never emits a finite rank.
- Physical-template labels require exact solver/frame/transfer provenance.
- Do not tune statistics or templates from observed outcomes.
- Do not guess across a semantic boundary. Emit a typed blocked state.
- Fail closed on claims, not exploratory progress.
- One fresh read-only review and at most one targeted repair per work unit.
- No successor planning package.

Required sequence:

```text
PMG-WU-001 -> PMG-WU-002 -> PMG-WU-003 -> PMG-WU-004 ->
PMG-WU-005 -> PMG-WU-006 -> PMG-WU-007 -> PMG-WU-008 ->
PMG-WU-009
```

`PMG-WU-003` must produce a real map-free analysis result. If two substantial
cycles have produced only plans, contracts, or reviews, classify
`PROCESS_STARVATION`, freeze optional governance, and execute the shortest
admissible objective step.

For the selected work unit, use TDD, run the exact risk-scoped commands, create
the required objective artifacts, inspect plots when required, commit/push the
coherent delta, and provide the evidence fields listed in the contract.
Never report PASS for unexecuted work.
