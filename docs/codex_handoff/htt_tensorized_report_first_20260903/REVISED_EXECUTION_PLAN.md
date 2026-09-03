# HTT theory-report-first execution plan — A2/A5 and first theorem-pack closeout

Date: 2026-09-03  
Repository: `cosmosapjw-quantum/htt_base`  
Control PR: `#449`  
Mode: theory only; observational data and native BASS work excluded

## 1. Current scientific objective

Produce a self-contained HTT theory/methods report whose central statement is:

> Correct tensorization preserves low-multipole morphology discarded by scalar
> summaries, but processed response, nuisance overlap, and numerical uncertainty
> limit physical attribution.

The report will contain no corrected Planck rank, empirical observer velocity,
boost subtraction, global-tilt inference, physical shear/vorticity estimate,
foreground causal attribution, or Bianchi-family result.

## 2. Authority and evidence policy

Report A uses a federation rather than one implicit latest branch:

```text
PR #367  typed vector/tensor framework
PR #405  157-candidate source matrix
PR #408  survivor-surface P0 contract
PR #440  corrected temperature Q/O semantics and source implementation
PR #441  wording/proof-obligation summary; formal dossier pending
PR #442  accepted full-sky local-observer response
PR #444  current processed-response source plus earlier byte-exact terminal
PR #446  exact z-direction author artifact and verifier contract
PR #447  external verifier implementations
PR #449  report control plane
```

Every claim carries separate fields for mathematical truth, literature support,
direct derivation, numerical checking, source implementation, accepted runtime,
scientific terminal, and publication status.

## 3. Completed preflight nodes

### A0 — repository surface

`DONE_REPORT_SCOPE`.

The default branch, merged framework, report-authority PRs, load-bearing code,
documents, tests, artifacts, and workflow receipts have been inventoried.
BASS and observational pipelines were classified out of scope rather than
silently imported.

### A1 — authority and supersession

`DONE_REPORT_SCOPE`.

Scalar-only MES results are historical only; old WU-006--008 Q/O, tensor-rank,
foreground, and injection interpretations remain withdrawn. Git-diverged
lineages are cited separately.

### A2 — registered survivor-surface triage

`DONE_CONTENT_AND_INDEPENDENT_WOLFRAM_VALIDATION`.

PR #405 and PR #408 define the report-eligible surface:

```yaml
exact_or_conditional: 24
synthetic: 8
scoped_children: 4
total: 36
```

Every row now has one report disposition:

```yaml
INCLUDED: 16
EXCLUDED: 13
DEFERRED: 7
```

Two duplicate exact-core pairs each have one report owner. All scoped children
retain their parent identity. `STF2+four vectors` and temperature
`STF2+STF3` remain separated. A fresh Wolfram parse verified all counts and
coverage.

A2 does not promote truth or novelty. It closes the omission risk found by PR
#408 and determines what must be directly replayed.

### A3 — representation firewall

`DONE_CONTRACT`.

```text
Temperature Q/O:       STF2 + STF3, ambient 12, generic quotient 9
VT-T8 framework slice: STF2 + four vectors, ambient 17, generic quotient 14
```

No result from the second representation may serve as a proof of the first.

### A4 — execution receipt index

`DONE_INITIAL`.

Runtime success, runtime failure, mixed evidence, prestart/no-execution,
source-only, artifact-only, local non-byte-exact, and summary-only states are
separate.

### A5 — contradiction and notation closure

`DONE_CONTRACT_AND_WOLFRAM_COVERAGE`.

The frozen notation registry separates:

- `Q_ab` from an acceptance gauge;
- `O_abc` from asymptotic `mathcal O`;
- `beta_obs`, `beta_RM`, `beta_MO`, and `beta_RO`;
- algebraic, numerical, robust, quotient, and finite-pool ranks;
- structural nulls, covariance nulls, nuisance images, statistical nulls, and
  typed missingness;
- theorem, implementation, runtime, science-terminal, publication, and merge
  status.

Every one of the sixteen included survivor rows is mapped exactly once to a
theory pack and report section.

## 4. Completed substantive theory packs

### T1 — stored-real harmonic/STF representation

`PASS_STORED_REAL_STF_REPRESENTATION_THEORY`.

Completed:

- Parseval isometry for the actual stored-real basis;
- exact Cartesian STF2 and STF3 basis tensors;
- projection and inverse maps;
- Gram constants and norm identities;
- rotation/parity intertwining;
- dimensional and zero-amplitude checks;
- independent exact Wolfram receipt.

The result is mathematically derived and Wolfram-checked. PR #440 source agrees,
but its exact-head GitHub runtime remains `PRESTART_NO_EXECUTION`.

### T3 — conditional MES geometry

`PASS_CONDITIONAL_MES_GEOMETRY_AND_EQUIVARIANCE_FIREWALL`.

Completed:

- direct source binding to the MES papers and COBE application;
- premise matrix, including geodesic congruence, all-observer Copernican
  extension, and derivative-hierarchy assumptions;
- PSTF conversion from `C_2,C_3`;
- standard `Sigma^2,W^2` conversion;
- one-way implication and explicit converse prohibition;
- proof that scalars alone cannot equivariantly generate a nonzero vector or
  STF tensor;
- exact Wolfram checks.

The MES coefficients are `LITERATURE_SUPPORTED`; the normalization and no-go
are `DERIVED_AND_WOLFRAM_CHECKED`.

### T4 — exact finite-null theory

`PASS_FINITE_NULL_ROW_EQUIVARIANCE_THEORY`.

Completed:

- finite-sample super-uniform rank theorem under joint exchangeability and
  complete row-permutation equivariance;
- exact tie-free discrete uniformity;
- conditions under which data-adaptive selection remains valid;
- typed handling of chart failure and missingness;
- null-fidelity and shared-realization boundaries;
- exact four-row counterexample where observation-specific feature selection
  violates size by `1/4`;
- exhaustive Wolfram tie checks for pool sizes 2 through 7.

This theorem does not certify any particular Planck/FFP10 reference pool.

### T5 — exact full-sky local-observer response

`PASS_WU010_EXACT_LOCAL_OBSERVER_RESPONSE_SYNTHESIS`.

Completed:

- exact thermodynamic-temperature Lorentz pullback and solid-angle Jacobian;
- first-order Doppler-plus-aberration generator;
- quadrupole-induced dipole/STF3 decomposition;
- adjoint, normal matrix, algebraic inverse, and orthogonal projector;
- four-dimensional response-orthogonal octupole residual;
- sharp `kappa_2(M_Q)<=5/3` proof with equality spectrum `(-5,4,1)`;
- exact Wolfram receipts;
- readback of the accepted WU-010 exact-head workflows.

The result remains full-sky, local-observer, strictly positive absolute
thermodynamic temperature, and `d=1` only.

## 5. Current primary node: T2

### Goal

Independently prove or narrow the PR #440 conditioned Q/O Krylov reconstruction
without borrowing the fourteen-dimensional VT-T8 result.

### Required derivation

For normalized `Q` and `O`, define

```text
v = O:Q
K = [v, Qv, Q^2 v]
```

Prove:

1. `det K` has the eigenframe Vandermonde factorization;
2. `det K != 0` is equivalent to simple Q spectrum and nonzero eigenframe
   components of `v`;
3. trace-free Cayley--Hamilton determines `Q^3 v` and `Q^4 v` from lower
   moments;
4. the five Krylov moments determine `K^T K`;
5. the signed Gram square root fixes one canonical proper orientation;
6. the companion matrix reconstructs `Q`;
7. ten trilinear contractions reconstruct `O`;
8. equal packets imply one SO(3) orbit;
9. the signed determinant distinguishes a mirror pair missed by even
   invariants;
10. zero, repeated-spectrum, contraction-null, noncyclic, and ill-conditioned
    strata are typed rather than discarded.

### T2 evidence plan

- exact derivation;
- exact rational/algebraic witness in Wolfram;
- proper-rotation covariance check;
- mirror counterexample;
- explicit comparison with the closest retrieved invariant-theory literature;
- novelty remains `UNRESOLVED` unless a directly matching source is found.

### T2 terminals

```text
PASS_GENERIC_QO_SO3_CHART_WITH_TYPED_STRATA
PASS_RECONSTRUCTION_WITH_NOVELTY_UNRESOLVED
UNRESOLVED_QO_RECONSTRUCTION
```

The likely scientific terminal may combine the first two clauses: a proved
generic chart with novelty still unresolved.

## 6. Current parallel node: T6

T6 can proceed independently once T5 is frozen.

Required outputs:

- exact processing-chain factorization;
- quotient identity
  `rank([K J])-rank(K)`;
- nested-image theorem and short-circuit condition;
- separate Task-7A/7B negative evidence, last byte-exact Task-7C result, and
  current source-only A4 mathematics;
- continuum/discrete distinction;
- no finite-HEALPix promotion.

T6 should then open T7 and T8 in parallel.

## 7. Remaining theory nodes

### T7 — continuum wide-mask response

Current evidence:

- z direction: exact rational block-minor author artifact, rank 32 at `L=12`;
- other five registered directions: strong multi-engine high-precision
  numerical evidence;
- external GitHub verifier workflows: `PRESTART_NO_EXECUTION`;
- portable all-direction interval proof: open.

Allowed terminal:

```text
PASS_Z_EXACT_FIVE_DIRECTION_NUMERICAL
```

if interval closure remains unavailable and the evidence grades remain explicit.

### T8 — matrix numerical-error theorem

Mathematical tasks:

- Loewner envelope for additive deterministic coefficient balls;
- compensated family scaling and family-internal orthogonal invariance;
- zero-family pathology;
- error-whitened full-row certificate;
- actual error-family completeness conditions;
- separate Wedin/spectral-gap theorem for partial subspaces.

### T9 — integrated claim ledger

T9 begins only after T2, T6, T7, and T8. It will bind exact statements,
assumptions, evidence grades, source identities, allowed wording, forbidden
extensions, novelty status, and remaining obligations.

## 8. Manuscript and audit order

```text
T2 + T6
  -> T7 and T8
  -> T9 integrated claim ledger
  -> R1 full manuscript and appendices
  -> R2 PHYS-MATH / STATISTICS / CODE / PROVENANCE audit
  -> R3 blind referee and bounded revision
  -> R4 frozen Report A
```

The report may preserve an unresolved finite-HEALPix result; it may not present
that unresolved item as a continuum refutation or hide it.

## 9. Post-report and observational boundaries

After R4, P1--P3 may proceed as observation-independent successors. The
observational path remains:

```yaml
D0: DATA_DEFERRED_BY_OWNER
O1_corrected_carrier_repair: BLOCKED
O2_statistic_and_nuisance_registry: BLOCKED
O3_Planck_FFP10_execution: BLOCKED
O4_observation_report: BLOCKED
```

No current theory node is authorized to reopen D0.

## 10. Updated readiness

| Workstream | Current readiness |
|---|---:|
| repository inventory | 100% for Report A scope |
| authority/supersession | 98% |
| survivor triage | 100% content and independent Wolfram validation |
| representation firewall | 100% |
| execution receipt index | 95% |
| notation/contradiction contract | 100% |
| T1 stored-real/STF theory | 100% theory; runtime admission separate |
| T2 Q/O orbit reconstruction | 70% source understanding; direct proof active |
| T3 conditional MES theory | 100% at retained geodesic scope |
| T4 finite-null theory | 100% at explicit premise scope |
| T5 WU-010 synthesis | 100% at accepted full-sky scope |
| T6 WU-011 quotient synthesis | 88--92% source material; integrated pack pending |
| T7 continuum result | 90--95% graded evidence; all-direction interval 25--40% |
| T8 error-envelope theorem | 85--90% mathematics; error-class completeness unresolved |
| T9 integrated claim ledger | 65--70% |
| Report A working prose | 65--72% |
| audited report release candidate | 0% |
| corrected observational result | 0%, intentionally deferred |

## 11. Current terminal

```text
A2_REGISTERED_SURVIVOR_TRIAGE_CLOSED
/
A5_NOTATION_AND_CONTRADICTION_CONTRACT_CLOSED
/
T1_T3_T4_T5_COMPLETE_AT_TYPED_SCOPE
/
T2_PRIMARY_NEXT
/
T6_PARALLEL_NEXT
/
OBSERVATIONAL_DATA_DEFERRED
/
NO_MERGE_OR_CLAIM_PROMOTION
```
