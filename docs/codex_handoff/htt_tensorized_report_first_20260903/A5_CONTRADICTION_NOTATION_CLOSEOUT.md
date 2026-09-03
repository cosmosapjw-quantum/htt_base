# A5 contradiction and notation closure

Date: 2026-09-03  
Repository: `cosmosapjw-quantum/htt_base`  
Report PR: `#449`  
Scientific claim promotion: no  
Observational execution: none

## Inputs and outputs

A5 consumes the completed A2 surface and the authority, representation, and
execution preflights. It freezes:

```text
NOTATION_AND_CONVENTION_REGISTRY.yaml
REPORT_SECTION_CLAIM_MAP.csv
CONTRADICTION_LEDGER.yaml v3
A5_CONTRADICTION_NOTATION_CLOSEOUT.md
```

The A2 source surface contains 36 eligible rows and the closed report
classification `16 INCLUDED / 13 EXCLUDED / 7 DEFERRED`.

## Closed semantic collisions

- `Q_ab` is reserved for the temperature quadrupole. Acceptance gauges use
  `p_A` or `rho_A`.
- `O_abc` denotes the temperature octupole. Asymptotic order is written
  `mathcal O`.
- `beta_obs`, `beta_RM`, `beta_MO`, and `beta_RO` carry distinct velocity
  semantics.
- Algebraic, tolerance-dependent numerical, robust, nuisance-quotient, and
  finite-pool order ranks use different symbols.
- Structural nulls, covariance-null directions, nuisance images, statistical
  null laws, and typed missingness are not interchangeable.
- Theorem truth, source implementation, accepted runtime, scientific terminal,
  publication, and merge status remain independent fields.

## Representation firewall

The report uses the temperature representation

```text
STF2(Q)+STF3(O), ambient dimension 12, generic SO(3) quotient dimension 9.
```

The PR #367/#408 VT-T8 result concerns

```text
STF2+four vectors, ambient dimension 17, generic SO(3) quotient dimension 14.
```

The latter cannot prove the former.

## Included-row coverage

Every A2-included row occurs exactly once in
`REPORT_SECTION_CLAIM_MAP.csv`. A fresh Wolfram parse gave:

```yaml
rows: 16
unique_source_ids: true
exact_A2_included_coverage: true
pack_counts:
  T2: 3
  T3: 3
  T4: 5
  T6: 4
  T8: 1
synthetic_rows_typed_as_validation: true
```

T1 and T5 are sourced from PR #440 and PR #442 respectively rather than from
the PR #405 survivor matrix.

## Literature consequences

The retrieved invariant-theory literature contains close but different
representations: pure octupole, vector-plus-quadrupole, sets of vectors, sets of
symmetric matrices, and a different 25-dimensional SO(3) representation. The
retrieved set does not directly prove completeness or reconstruction for the
exact real `STF2(Q)+STF3(O)` Krylov packet. This is not a universal
nonexistence claim; it leaves T2 as a direct proof and novelty-comparison task.

Randomization-inference literature supports finite-sample exactness under an
explicit group-invariance or exchangeability hypothesis, so T4 binds the
complete selection and row-processing algorithm. Singular-subspace
perturbation literature requires perturbation size together with a spectral
gap, so T8 separates partial-subspace stability from numerical rank.

## Terminal

```yaml
A5_state: DONE_CONTRACT_AND_WOLFRAM_COVERAGE
report_level_direct_contradictions: 0
unqualified_symbol_collisions: 0
A2_included_rows_mapped: 16_of_16
substantive_proofs_completed_by_A5: 0
observational_data_opened: false
merge_authorized: false
ready_parallel_nodes:
  - T1_STORED_REAL_STF_REPRESENTATION
  - T3_CONDITIONAL_MES_GEOMETRY
  - T4_FINITE_NULL_THEORY
  - T5_WU010_SYNTHESIS
critical_path_primary: T1_TO_T2_TO_T9_TO_R1
critical_path_response: T5_TO_T6_TO_T7_T8_TO_T9
```
