# A2 registered survivor-surface triage closeout

Date: 2026-09-03  
Repository: `cosmosapjw-quantum/htt_base`  
Report PR: `#449`  
Observational data: not opened  
Native BASS solver: not used

## 1. Exact authority

The triage source is PR #405 at
`463f0999949bf8534c60ad7973b7342705c2e3d6`, file
`docs/research_program/theory_promotion/THEORY_PROMOTION_MATRIX_V1.json`,
Git blob `56af1713ef8c4718598e10012819d5ab62c6e37a`.

The controlling adversarial requirement is PR #408 WU-001 at
`40dce3ab9328c1f3acb99adba11046056c639737`: every eligible exact or
conditional row, synthetic row, and declared scoped child must receive one
report disposition without allowing provisional role labels to determine
truth, novelty, or publication status.

The machine-readable output is
`REGISTERED_SURVIVOR_SURFACE.csv`.

## 2. Closed source surface

The PR #405 eligible survivor surface is exactly:

| Source class | Rows |
|---|---:|
| exact or premise-conditional | 24 |
| preregistered synthetic | 8 |
| independently reportable scoped child | 4 |
| **total** | **36** |

The report triage is:

| Report disposition | Rows |
|---|---:|
| `INCLUDED` | 16 |
| `EXCLUDED` | 13 |
| `DEFERRED` | 7 |
| **total** | **36** |

`INCLUDED` means selected for direct replay and possible use in Report A. It
does not mean that A2 independently re-proved novelty or granted publication
authority. `EXCLUDED` means omitted from this report for duplication, scope, or
representation reasons; it does not change the source truth status.
`DEFERRED` preserves the result for a named successor.

## 3. Included rows

### Core or supporting exact/conditional rows

- `PILLAR_T:VT-T1` — registered 1+3 normalization conversion; appendix only.
- `PILLAR_T:VT-T4` — one-way typed anchor-stress lower probe; appendix only.
- `PILLAR_T:VT-T6` — trace-free 3x3 Cayley--Hamilton reduction; report owner
  for its duplicate family.
- `PILLAR_T:VT-T7` — signed Krylov determinant, Gram identity, and cyclicity;
  report owner for its duplicate family.
- `PILLAR_T:VT-T9` — polar/axial O(3) parity firewall.
- `PILLAR_T:VT-T11` — supported response quotient after covariance-support
  restriction.
- `PILLAR_T:VT-T12` — principal-angle weak-identification distinction.
- `PILLAR_S:I-5.3` — one-way MES containment with no converse.
- `PILLAR_S:I-5.4` — invertible anchor-coordinate scaling preserves response
  rank and image.
- `PILLAR_S:VT-S1` — deterministic scalarization cannot increase TV or KL
  separation; strict gain and sufficiency remain separate questions.
- `PILLAR_S:VT-S4` — typed survival surface from a declared probability law;
  optimizer points are not draws.

### Synthetic validation rows

- `PILLAR_S:VT-S3` — split matched-null max-gauge calibration.
- `PILLAR_S:VT-S9` — finite nested path maximum-statistic calibration.
- `PILLAR_S:VT-S10` — weak-identification abstention cells.
- `PILLAR_S:VT-S11` — one registered orbit-response composition cell.
- `PILLAR_S:VT-S12` — matched-counterpair morphology-power witness.

Every synthetic row remains labelled synthetic and observation-independent.

## 4. Excluded rows

### Duplicate exact cores

- `PILLAR_S:I-2.2` is represented by the stronger report owner
  `PILLAR_T:VT-T6`.
- `PILLAR_S:I-2.3` is represented by the stronger report owner
  `PILLAR_T:VT-T7`.

The duplicate rows remain linked and are not counted as additional theorems.

### Representation mismatch

- `PILLAR_S:I-2.1` and `PILLAR_S:I-2.9` belong to the joint vector/tensor v2
  catalogue rather than the temperature `STF2(Q) + STF3(O)` problem.
- `NARROW:VT-T8-LOCAL-CHART` belongs to `STF2 + four vectors`, whose generic
  SO(3) quotient dimension is 14. It cannot certify the Q/O quotient, whose
  generic dimension is 9.

### Outside Report A scope

- `PILLAR_T:VT-T2`, `PILLAR_T:VT-T3`, and `PILLAR_T:VT-T10` are general
  anchor-geometry results.
- `PILLAR_S:I-5.1` and `PILLAR_S:I-5.2` are general gauge-body lemmas.
- `PILLAR_S:VT-S2` is a general acceptance-body contract whose symbol `Q`
  must not be confused with the temperature quadrupole.
- `PILLAR_S:VT-S7` belongs to the general sample-wise functional-pushforward
  programme.
- `NARROW:PR190-NORMAL-VORTICITY-OBSTRUCTION` is a same-frame Bianchi-I
  negative application. It is preserved outside the HTT-only Report A and is
  not extended to tilted frames or all Bianchi types.

## 5. Deferred rows

- `PILLAR_T:VT-T5` — physical shear-orbit strata; defer to physical-state
  geometry work.
- `PILLAR_S:VT-S8` — paired depth covariance; defer to P3.
- `PILLAR_S:VT-S5` and `PILLAR_S:VT-S6` — partial identification and random
  anchor uncertainty; defer to P2.
- `PILLAR_S:VT-S13` — open-set finite-library classification; defer to P3 or
  the future native-atlas programme.
- `NARROW:VT-T13-CHAIN-RULE` — exact physical-shear chain-rule core; defer to
  a physical-dynamics successor and do not promote it to a full covariant
  evolution law.
- `NARROW:VT-S14-SYNTHETIC-POSITIVE-CELL` — depth-conditioned local/global
  synthetic cell; defer to P3.

## 6. Independent Wolfram validation

The exact CSV content was parsed in a Wolfram Language evaluator. The final
receipt reports:

```yaml
parsed_rows: 36
unique_ids: true
source_class_counts:
  EXACT_OR_CONDITIONAL: 24
  SYNTHETIC: 8
  SCOPED_CHILD: 4
report_disposition_counts:
  INCLUDED: 16
  EXCLUDED: 13
  DEFERRED: 7
duplicate_groups_closed: true
scoped_parents_present: true
representation_firewall_closed: true
synthetic_rows_not_promoted_as_core_theorems: true
all_checks_pass: true
```

The first validation expression failed because it compared imported Boolean
cells with string literals. Inspection showed that the CSV data were correct;
the validation expression was repaired to compare Boolean values directly and
then passed. The failure and repair are retained in
`WOLFRAM_A2_VALIDATION_RECEIPT.json`.

The same independent calculation reproduced:

```text
dim STF2 = 5
dim STF3 = 7
dim[(STF2 + STF3)/SO(3)]_generic = 9
dim[STF2 + four vectors] = 17
dim[(STF2 + four vectors)/SO(3)]_generic = 14
trace-free 3x3 Cayley-Hamilton residual = 0
Krylov Gram determinant residual = 0
polar Krylov reflection residual = 0
axial Krylov reflection residual = 0
```

Here the polar determinant is a pseudoscalar and the axial determinant is an
O(3) scalar, as required by the parity firewall.

## 7. Literature scope audit

A SciSpace search was run for complete or separating invariants, Molien/Hilbert
series, reconstruction, and orbit stratification relevant to real
`STF2 + STF3` under SO(3).

The closest retrieved sources include:

- Börnsen and van de Ven, *Tangent Developable Orbit Space of an Octupole*,
  arXiv:1807.04817 — octupole alone, with vector-plus-quadrupole material as a
  preamble;
- Chillingworth, Lauterbach, and Turzi, *Molien series and low-degree
  invariants for a natural action of SO(3) wr Z2*,
  DOI `10.1088/1751-8113/48/1/015203` — a different 25-dimensional
  representation;
- literature on sets of vectors, several symmetric matrices, and rational
  invariant fields for multiple second-order tensors.

No paper in the retrieved set directly proves completeness or reconstruction
for the exact real `STF2(Q) + STF3(O)` Krylov packet used in PR #440. This is a
search result, not a universal nonexistence theorem. T2 therefore remains an
independent derivation and novelty-audit task.

For finite-null theory, Ritzwoller, Romano, and Shaikh,
*Randomization Inference: Theory and Applications*, arXiv:2406.09521, supports
exact finite-sample language only under an explicit group-invariance or
randomization hypothesis. For partial response subspaces, Cai and Zhang,
*Rate-Optimal Perturbation Bounds for Singular Subspaces*,
DOI `10.1214/17-AOS1541`, reinforces the need for perturbation size and a
singular-value gap rather than rank thresholding alone.

## 8. A2 terminal and residual boundary

```yaml
A2_state: DONE_CONTENT_AND_INDEPENDENT_WOLFRAM_VALIDATION
A2_publication_authority: false
Python_checkout_validation: NOT_EXECUTED_RUNTIME_UNAVAILABLE
GitHub_CI: NOT_USED_AS_A2_PASS_EVIDENCE
current_corrected_Planck_rank: null
observational_execution: DATA_DEFERRED_BY_OWNER
merge_authorized: false
next_node: A5_CONTRADICTION_AND_NOTATION_CLOSURE
```

A2 closes the survivor-selection omission identified by PR #408. It does not
close the current replay, novelty, theorem-proof, or manuscript gates of the
16 included rows. Those obligations are carried into A5 and T1--T8.
