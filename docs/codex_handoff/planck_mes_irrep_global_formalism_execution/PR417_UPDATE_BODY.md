## Purpose

This update supersedes the scalar-only execution order in the original PR
without deleting its data-inventory evidence. It recompiles the next Planck MES
work around one typed representation-aware formalism:

```text
ObservableIrrepState
!= JointAnisotropyState
!= MesPremiseNormalizer
!= ResponseBoundObservableState
```

The immediate scientific correction is that, on the registered
`epsilon_1=0` branch,

```text
W2_max = C2/(30*pi*T0^2)
Sigma2_max = (27/98)*(7*epsilon2+epsilon3)^2
sigma(Sigma2_max,W2_max,M) = sigma(C2,C3,M)
```

so the existing MES coordinates add no information to `(C2,C3,M)`. The
updated plan makes reducer non-invariance, observable irrep morphology, and
measured injection power the main execution targets.

## Authority

```yaml
canonical_science_base: changeset/pr324-mes-methodology-stack-20260826
canonical_science_sha: 3cdeaba39e164c911a26c5daa37f0e15b29614d3
canonical_science_tree: 47bdbb72aae62ca4280a96897f80028b1b910c20
planning_predecessor_sha: 2669a55ef230d1ca9e79c09d3344f7b15c50ac0e
planning_predecessor_tree: 274d74507542cc99bb4ea355705791fa03d15697
active_branch: analysis/planck-mes-extended-data-execution-20260826
draft_pr: 417
```

## Supersession

The original package remains historical inventory/route authority, but
`PED-WU-001..004` are no longer executable. Active order:

```text
PMG-WU-001  canonical ObservableIrrepState + frozen scalar baseline
PMG-WU-002  global formalism adapters and type firewalls
PMG-WU-003  real map-free coordinate/reducer mechanism audit
PMG-WU-004  read-only local inventory
PMG-WU-005  real paired-300 301x32 carrier export/replay
PMG-WU-006  ell=2/3 observable irrep-orbit calibration
PMG-WU-007  carrier-preserving 999 and Commander execution
PMG-WU-008  controlled injection power
PMG-WU-009  methods-first paper revision
```

## Machine package

```text
docs/codex_handoff/planck_mes_irrep_global_formalism_execution/
docs/codex_handoff/ACTIVE_PLANCK_MES_EXECUTION_PACKAGE.yaml
scripts/validate_planck_mes_irrep_global_formalism_plan.py
tests/contracts/test_planck_mes_irrep_global_formalism_plan.py
```

The package includes 25 P0/P1 failure classes, a complete invariant/test
matrix, nine `audit-compiled-work-unit/v1` contracts, exact formalism and
migration matrices, one fresh-context review contract, one final differential
audit contract, and an anti-process-starvation transition policy.

## Execution boundary

- preserve all frozen scalar outputs and exact ranks;
- do not infer physical source from observer-space irreps;
- do not use the physical orbit catalogue on Planck observable states;
- preserve the 32 retained real harmonic coefficients on every new map pass;
- paired-300 remains primary; 999 is separate robustness; Commander no-rank;
- algebraic injections are method-power only;
- physical-template claims require certified solver/frame/transfer receipts;
- one fresh review and at most one targeted repair per work unit;
- no successor planning package before real `PMG-WU-003` execution.

## Requested review

Review only the compiled semantic and execution boundary:

1. observer/physical/premise/response type separation;
2. exact MES identity and no-information theorem;
3. carrier-preserving map execution;
4. finite-null reducer/tail symmetry;
5. observable ell=2/3 orbit morphology scope;
6. primary/robustness/Commander role separation;
7. injection provenance;
8. explicit PASS-to-execution transitions.

This PR remains a planning/implementation handoff, not a scientific result or
claim promotion.
