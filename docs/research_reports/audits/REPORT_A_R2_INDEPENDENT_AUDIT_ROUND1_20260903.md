# Report A R2 independent audit — round 1

Date: 2026-09-03  
Repository: `cosmosapjw-quantum/htt_base`  
Report PR: #449  
Observational data used: none

## Executive verdict

```text
REPORT_A_DRAFT_EXISTS
/
R1_RECLASSIFIED_COMPLETE_AS_DRAFT
/
R2_ACTIVE_WITH_TWO_SEPARATE_REPAIR_PRS
/
T4_TIE_RULE_REPAIRED
/
T9_COUNT_FLATTENING_PENDING
/
NO_PUBLICATION_FREEZE
```

The current report branch already contains the integrated theory/methods draft,
all eight theory packs, and an integrated claim ledger. The next node is not
additional first-draft writing. It is independent audit and bounded repair.

The audit distinguishes mathematical validity, implementation validity,
execution evidence, provenance, and novelty. It does not use majority vote
across those axes.

## 1. Authority and lineage

The report composes several Git-diverged evidence lineages. Two new repair PRs
now carry the load-bearing implementation work rather than silently modifying
the report branch:

- PR #450: mechanical PR-408 WU-001 registered-survivor extraction on a branch
  descended from merged PR #408;
- PR #451: Q/O Krylov packet-image syzygy guard on a branch descended from the
  PR #440 tensorized semantic authority.

The report branch may import their frozen receipts by content identity after
review. It must not claim that either lineage is a linear ancestor of the
other.

## 2. A2 survivor-source audit

The neutral source surface contains:

```yaml
exact_or_conditional_broad: 24
synthetic_broad: 8
scoped_included: 4
scoped_deferred: 1
included_total: 36
registered_total: 37
unique_theorem_count: null
```

The deferred source candidate is
`PR284_NEW:FINITE-REGISTERED-PATH`. Its narrower four-atom arithmetic fixture
may receive a distinct successor identity, but the CAS-conflicted parent must
not be silently promoted.

PR #449 contains the corrected 37-row content and a closeout narrative. That is
not yet the mechanical WU-001 execution required by PR #408. PR #450 now adds
source-first tests, a deterministic extractor, and exact PR-405 Git-object
replay in a dedicated workflow. The local source-equivalent contract run is
`13 passed`; the exact-head workflow ended before runner assignment and
therefore supplied no execution receipt.

Current A2 classification:

```yaml
content_surface: CORRECTED_TO_37_ROWS
mechanical_implementation: PRESENT_IN_PR450
local_contract_run: PASS_SOURCE_EQUIVALENT
exact_head_ci: PRESTART_NO_EXECUTION
report_import_authority: PENDING_PR450_SEAL
```

## 3. T2 Q/O orbit reconstruction audit

### Mathematical core

The generic temperature representation is

\[
\mathrm{STF}_2(Q)\oplus\mathrm{STF}_3(O),
\]

with generic locally free `SO(3)` quotient dimension

\[
5+7-3=9.
\]

This is distinct from the PR #367/#408 `STF2 + four vectors` slice with generic
quotient dimension 14.

For

\[
v_a=O_{abc}Q_{bc},\qquad
\mathscr K_{QO}=[v,Qv,Q^2v],
\]

the cyclic chart is valid only where `det K != 0` and the conditioning contract
is satisfied. The full Q/O tensors remain the primary observables outside this
chart.

### Code-level P1 and repair

The original decoder reconstructed a candidate `Q` and `O` but did not require

\[
O:Q=\mathscr K_{QO}e_0.
\]

A forged STF3 packet could therefore preserve the stored Krylov moments and
trilinear coordinates while decoding outside the image of the forward packet
map. PR #451 adds a RED mutation and the minimal image-syzygy guard.

The mathematical reconstruction theorem for forward-generated packets
survives. The arbitrary-packet decoder is not implementation-verified until
PR #451 executes on its exact head.

Current T2 classification:

```yaml
mathematics: PASS_ON_DECLARED_NONZERO_CYCLIC_DOMAIN
source_implementation_after_repair: PRESENT_IN_PR451
source_equivalent_mutation_run: RED_GREEN_PASS
exact_head_execution: PRESTART_NO_EXECUTION
novelty: UNRESOLVED
forbidden: [GLOBAL_INVARIANT_RING, ALL_STRATA_COMPLETENESS]
```

The current literature search found general tensor-invariant, symmetry-class,
and separating-set machinery, but no direct primary-source match for the exact
Q/O Krylov16 reconstruction contract. Absence of a match in this search is not
a novelty proof.

## 4. T4 finite-null audit and completed repair

The theorem remains:

> joint row exchangeability plus equivariance of the complete analysis map
> implies a super-uniform observation-inclusive upper-tail rank.

The complete map includes representation construction, chart status, nuisance
fit, adaptive selection, missingness, score, and tie policy.

The committed asymmetric-selection fixture previously omitted the deterministic
tie rule. Fresh Wolfram enumeration gives:

```text
ties -> coordinate 2: p=1/2 for 12, p=3/4 for 12
ties -> coordinate 1: p=1/2 for  6, p=3/4 for 18
maximum size violation in both cases: 1/4
symmetric pooled selection: p=3/4 for 18, p=1 for 6, maximum violation 0
```

The theorem pack and receipt have now been corrected. This changes neither the
main theorem nor the maximum violation; it makes the exact counterexample
reproducible.

## 5. T9 ledger audit

The base T9 ledger declares 27 claims but actually contains 29 unique claim
rows. A committed validation overlay correctly records:

```yaml
actual_claim_count: 29
unique_claim_ids: true
canonical_sorted_id_sha256:
  bc81bdd2d5325f5561834594cb3f4195dc29c22ee461dcf77e067373678b22fe
```

Before report freeze the ledger must be rewritten as one self-contained v2
artifact with `claim_count=29`. The overlay remains repair history; it is not a
permanent substitute for a consistent canonical ledger.

## 6. WU-010/WU-011 evidence boundary

WU-010 remains scoped implementation-verified on its frozen exact head.

WU-011 must retain two identities:

```yaml
current_source_head: de73549c16ac6ceb63f924c86611e0a5ceb4711d
last_byte_exact_scientific_head: f635d873cf5e77f7cb0d2756469acde60b8609e5
last_byte_exact_terminal: PASS_TASK7C_MATCHED_CONTROL_RANK_UNRESOLVED
```

The continuum wide-mask result and finite-HEALPix result are different
operators with different error models. Continuum row rank 32 is not a finite
HEALPix theorem. A thresholded partial singular subspace also requires a
perturbation-to-gap bound; matrix rank and singular-subspace certification are
separate statements.

## 7. Statistical literature boundary

Primary literature on randomization inference supports exact finite-sample
control under a group-invariance/randomization hypothesis. It does not license
observation-specific feature selection or missing-row deletion. The report's
row-equivariant theorem is therefore the correct project-specific interface.

Primary singular-subspace perturbation literature requires a perturbation
scale together with an absolute or relative spectral gap. Consequently:

- full-row rank may be certified by a robust smallest-singular-value margin;
- partial-rank image orientation needs a Wedin/Davis-Kahan-type angle bound;
- numerical rank thresholding alone is insufficient.

## 8. Publication blockers after this round

### P0 publication blockers

None in the surviving theorem statements after the T4 correction, provided the
current claim ceilings remain in force.

### P1 blockers

1. PR #450 exact-head survivor extraction has not executed.
2. PR #451 exact-head packet-image regression has not executed.
3. The T9 ledger is not yet flattened to v2.
4. The integrated report draft has not been regenerated against the corrected
   T4 text and repaired T2 implementation boundary.
5. A complete reference/bibliography matrix and primary-source scope audit are
   not yet frozen.
6. Current GitHub-hosted jobs end before runner assignment because the account
   billing/spending gate remains unresolved.

### P2 items

- portable all-direction interval/ball seal for continuum `L=12`;
- complete numerical-error family/radius provenance for finite HEALPix;
- publication novelty assessment for the Q/O reconstruction chart.

The P2 items can remain explicitly unresolved in Report A. They are not all
required to release a theory/methods report whose conclusion is properly
limited.

## 9. Revised execution order

```text
A2M  PR450 mechanical source-surface execution          ACTIVE / CI blocked
T2C  PR451 packet-image implementation repair           ACTIVE / CI blocked
T4R  tie-rule theorem and receipt repair                 DONE
R1   integrated manuscript first draft                  DONE_AS_DRAFT
R2A  PHYS-MATH/STAT/CODE/PROVENANCE audit round 1        DONE_WITH_P1
R2B  flatten T9 + regenerate draft + citation matrix     NEXT
R2C  exact-head execution receipts                       BLOCKED_BY_BILLING
R3   blind referee and bounded revision                  WAITING
R4   freeze theory/methods report                        WAITING
P1-P3 observation-independent successors                AFTER_R4
D0/O1-O4 observational lane                              DATA_DEFERRED_BY_OWNER
```

## 10. Claim boundary

No current scalar-only MES rank, corrected tensorized Planck rank, empirical
observer velocity, boost subtraction, global matter-frame tilt, physical
shear/vorticity estimate, foreground cause, Bianchi-family attribution,
finite-HEALPix no-go theorem, BASS/native-solver result, merge, or publication
approval is introduced by this audit.
