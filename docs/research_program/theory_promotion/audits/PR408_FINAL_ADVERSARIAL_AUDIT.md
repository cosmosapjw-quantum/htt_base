# PR-408 final post-execution adversarial audit

## Exact audit target

```yaml
repository: cosmosapjw-quantum/htt_base
pull_request: 408
base_sha: bdad91a204c424030cd6d0e562232b6965a42900
audited_head_sha: cb815244c5482c89f795519eb8d9886077acc2bb
audited_head_tree: ba8a03012137984b748e61d70df69cfa576a7a91
changed_files: 10
additions: 2021
science_code_changed: false
canonical_dag_changed: false
observed_data_used: false
operating_profile: private_single_researcher_local_v1
guide_sha256: b9fa1498b4d8a1a34ff58d7be6f2622f68d6afb8e630900214ad6a6f94b87ada
```

## Executive verdict

```yaml
preserve_PR408_as_planning_evidence: true
execute_PR408_as_written: false
merge_as_final_implementation_contract: false
current_scientific_release_authority: false
findings:
  P0: 2
  P1: 10
  P2: 3
decision: APPLY_FINAL_AUDIT_COMPILED_OVERLAY_IN_PR408
```

PR-408 is a substantial improvement over PR-405 through PR-407. It correctly
separates survivor release from campaign exhaustion, keeps `NOT_ATTEMPTED`
distinct from `REFUTED`, defers genuinely new theory, and requires research
before code.

The remaining failure modes arise because the research outcome and survivor
surface are still manually preselected, while the weak-agent contract is not
yet expressed as individually complete `audit-compiled-work-unit/v1` units.
The exact-head generic CI is green, but it does not execute any PR-408 package
validator or scientific closeout test.

This audit is the final planning overlay. It replaces rather than layers more
review gates: one fresh-context implementation review and one final
strong-model differential audit remain.

---

# A. Scientific-result audit

## A1. PR-284 registered finite fixture

For

\[
\Omega=\{0,1,2,3\},\quad P(i)=\frac14,\quad X=(-3,-1,1,3),
\]

the registered fine, middle, and coarse conditional averages are

\[
M_0=(-3,-1,1,3),\quad
M_1=(-2,-2,2,2),\quad
M_2=(0,0,0,0).
\]

Also

\[
E[X]=0,\qquad E[X^2]=5.
\]

At \(\lambda=6/5\),

\[
\lambda^2E[X^2]=\frac{36}{5},\qquad
\max_j |M_j|^2=(9,4,4,9).
\]

The inclusive event contains atoms 0 and 3, hence

\[
P\!\left(\max_j |M_j|^2\geq\lambda^2E[X^2]\right)
=\frac12\leq\frac{25}{36},
\]

with exact slack \(7/36\).

This is an exact finite worked example and regression vector. It does not
establish a general reverse-martingale theorem, optional stopping, convergence,
an iff characterization, or observed calibration. The present Lean source is a
formal arithmetic replay unless a pre-existing typed finite-probability proof is
found.

```yaml
truth_status: ESTABLISHED
evidence_modalities:
  - EXACT_FINITE_ENUMERATION
  - EXACT_SYMBOLIC_IDENTITY
  - FORMAL_ARITHMETIC_REPLAY
publication_role: INTERNAL_REGRESSION
broad_parent_status: UNRESOLVED
```

## A2. PR-190 normal-vorticity obstruction

In the registered homogeneous Bianchi-I hypersurface-normal frame,
hypersurface orthogonality implies zero vorticity. Therefore

\[
W^2=3\sum_i(\omega_i/\Theta)^2=0,
\]

which is incompatible, in that same frame, with the registered targets
\(W^2=1/25\) and \(W^2=3/100\).

The mathematical core is correct but standard at the Frobenius level. Any
publishable novelty can only lie in the exact registered-target application,
not in the general statement that a hypersurface-normal congruence is
irrotational.

```yaml
truth_status: ESTABLISHED
scope: SAME_FRAME_HYPERSURFACE_NORMAL_BIANCHI_I
publication_role: NEGATIVE_APPLICATION
novelty_status: UNASSESSED
forbidden_extensions:
  - arbitrary_tilted_frame_no_go
  - all_Bianchi_no_go
```

## A3. VT-T5, VT-T6, VT-T7

The discriminant/shape identity, trace-free \(3\times3\)
Cayley-Hamilton reduction, and Krylov/Vandermonde/Gram identities are exact.
They are supporting algebraic lemmas, not three automatically novel standalone
theorems.

```yaml
publication_role: SUPPORTING_LEMMA
novelty_status: KNOWN_OR_STANDARD_UNLESS_EXACT_APPLICATION_DIFFERS
```

## A4. VT-T8 local chart

A real STF \(3\times3\) tensor contributes five parameters and four vectors
contribute twelve. On a locally free generic \(SO(3)\) stratum the expected
quotient dimension is

\[
5+12-3=14.
\]

The registered Jacobian factor is

\[
-48v_{01}^4v_{02}^4v_{03}^4
(\lambda_1-\lambda_2)^5
(\lambda_1+2\lambda_2)^5
(2\lambda_1+\lambda_2)^5.
\]

At the registered witness it equals \(50331648\neq0\). This establishes
local algebraic independence on the declared simple-spectrum cyclic slice.

A publication-facing local-quotient claim additionally needs an explicit
statement that the ordered eigenframe slice is a local transverse section and
that residual discrete sign/permutation choices do not invalidate the local
coordinate statement. If that source proof cannot be resolved, the statement
must be downgraded to:

> the fourteen invariant functions have full-rank Jacobian on the registered
> slice.

Prior literature already studies separating sets and integrity bases for
\(O(3)\) matrix invariants, \(SO(3)/O(3)\) vector invariants, and the orbit
space of a vector plus a quadrupole. Therefore novelty of the exact
Krylov-moment chart and its determinant factorization is unresolved rather
than presumed.

```yaml
current_role: PRIMARY_PROPOSITION_CANDIDATE
truth_status: ESTABLISHED_FOR_REGISTERED_SLICE_JACOBIAN
local_quotient_status: REQUIRES_TRANSVERSE_SLICE_EVIDENCE
novelty_status: UNASSESSED
forbidden:
  - global_orbit_separation
  - invariant_ring_completeness
  - global_quotient_atlas
```

## A5. VT-T13 chain-rule core

For differentiable STF \(\sigma\),

\[
\dot I_2=2\operatorname{tr}(\sigma\dot\sigma),\qquad
\dot I_3=3\operatorname{tr}(\sigma^2\dot\sigma).
\]

For \(I_2>0\),

\[
\dot J_\sigma=
3\sqrt6\,
\frac{
 I_2\operatorname{tr}(\sigma^2\dot\sigma)
 -I_3\operatorname{tr}(\sigma\dot\sigma)
}{I_2^{5/2}}.
\]

This is exact but standard differentiation. It does not establish the requested
full covariant dynamics.

```yaml
publication_role: SUPPORTING_LEMMA
forbidden_extension: FULL_COVARIANT_EVOLUTION_LAW
```

## A6. VT-S14

The registered positive synthetic cell and proportional-design negative control
are useful method validation only.

```yaml
evidence_modality: PREREGISTERED_SYNTHETIC_EXPERIMENT
publication_role: SYNTHETIC_VALIDATION
theorem: false
observational_result: false
family_identification: false
```

## A7. Aggregate surface

PR-405 reports 24 exact/premise-conditional broad PASS rows, 8 synthetic PASS
rows, and additional scoped cores. PR-408 preselects only eight survivors.
That selection may ultimately be correct, but it is not mechanically derived
or accompanied by one disposition for every other eligible row.

Consequently:

```yaml
selected_survivor_set: PROVISIONAL
unique_theorem_count: NOT_AVAILABLE
campaign_completion_status: OPEN
survivor_release_may_proceed: true
```

---

# B. P0 findings

## P0-408-001 — manual survivor selection can silently omit established rows

The research loop asks which existing results survive, but its evidence ledger
starts with a manually chosen set. It does not deterministically triage all 24
exact/conditional broad PASS rows, 8 synthetic PASS rows, and every declared
scoped child into `INCLUDED`, `EXCLUDED`, or `DEFERRED`.

A weak agent can therefore produce a polished survivor overlay while silently
dropping a relevant result.

Required guard:

```yaml
test: test_registered_survivor_triage_detects_injected_eligible_candidate
stop: BLOCKED_REGISTERED_SURVIVOR_SURFACE_NOT_CLOSED
```

The repair is not a universal candidate-universe claim. It closes only the
declared source registries and adjudication surfaces.

## P0-408-002 — research conclusions are precommitted before current replay

`RESEARCH_LOOP_CLOSEOUT.yaml` marks selected evidence as `SUPPORTED`, chooses
H3, and assigns publication roles before the current exact replay and novelty
audit are complete. `coding_handoff_ready=false` prevents immediate coding but
does not make the research loop genuinely falsifiable.

A valid research receipt must be able to retain, narrow, downgrade, defer, or
exclude each candidate when source, replay, domain, or novelty evidence changes.

Required guard:

```yaml
test: test_research_decision_changes_when_source_or_replay_evidence_is_mutated
stop: BLOCKED_RESEARCH_OUTCOME_PRECOMMITTED
```

No implementation status may be projected from provisional role labels.

---

# C. P1 findings

1. **Source-of-truth precedence is implicit.** The package says which overlay
   controls but does not provide the complete precedence order required for
   ambiguous source, receipt, and PR prose conflicts.

2. **Work units are not complete weak-agent contracts.** The five units omit
   per-unit authority, objective, non-goals, risk, full scope, preconditions,
   invariants, failure modes, exact verification commands, and completion
   evidence required by `audit-compiled-work-unit/v1`.

3. **Risk units are too broad.** One exact-replay unit contains PR-284,
   PR-190, VT-T5/T6/T7/T8/T13, and therefore combines independently
   rejectable mathematical claims and publication roles.

4. **Novelty audit is not executable.** “Statement-level novelty comparison”
   lacks a search log, nearest-prior-art table, overlap dimensions, decision
   rule, and reviewer receipt.

5. **Evidence and replay vocabulary still drifts.** The audit uses
   `CURRENT_PARTIAL`, which is outside the canonical replay enum, and narrative
   aliases can be confused with proof modalities.

6. **Load-bearing package validation is absent from CI.** Exact-head CI is
   green but executes no PR-408 contract parser, cross-file enum checker,
   survivor-surface test, or audit projection test.

7. **Final strong-model differential audit is absent.** A fresh cheap reviewer
   is present, but the attached guide also requires a bounded final audit of
   contract compliance, contract completeness, evidence validity, and scope.

8. **The separate PR-407 terminal gate is redundant.** An approved exact
   PR-408 terminal descending from the audited PR-407 head is sufficient.
   Requiring two human terminal receipts adds process starvation without a
   distinct failure class.

9. **VT-T8 quotient language lacks a mechanical slice certificate.** The
   determinant calculation proves a slice Jacobian; the local quotient wording
   additionally needs a resolved transverse-slice argument or an explicit
   downgrade.

10. **Process-cost and gate-non-proliferation analysis is missing.** PR-408 is
    the fourth planning/audit layer in this chain. It must explicitly replace
    old gates, reuse evidence, and forbid another planning successor.

---

# D. P2 findings

1. `tiltded_or_arbitrary_frame_extension` is a typo.
2. The package manifest lists files but does not content-bind the controlling
   cross-file package.
3. “Drive through loops” can be read as executed work even though only planning
   documents were produced.

---

# E. Constructive disposition

Do not create another stacked planning PR. Amend PR-408 itself with one final
controlling overlay and then stop planning.

Future implementation uses seven coherent risk units:

1. registered survivor-surface triage;
2. invariant/local-geometry evidence and novelty;
3. PR-190 negative-application closeout;
4. PR-284 internal exact-example closeout;
5. VT-S14 synthetic-validation closeout;
6. typed survivor overlay;
7. focused CI, fresh review, and final differential audit.

Only the approved exact PR-408 terminal commit is the implementation
predecessor. The implementation must prove that the audited PR-407 head is an
ancestor, but does not require a second PR-407 terminal ceremony.

The canonical DAG remains unchanged in PR-408. At implementation time the
existing generator allocates IDs append-only, and the previous node/edge/
resolution surfaces must be exact prefixes.

---

# F. Prior-art implications

The following literature surfaces are mandatory novelty inputs, not proof that
the exact PR-408 candidate is already known:

- Lopatin and Ferreira, arXiv:1810.10397, minimal generating/separating sets
  for selected O(3) matrix-invariant problems;
- Dhont, Cassam-Chenaï, and Patras, arXiv:1511.01311, Molien functions and
  integrity bases for sets of spatial vectors;
- Börnsen and van de Ven, arXiv:1807.04817, orbit spaces including a vector
  plus quadrupole preamble;
- Ellis and van Elst, arXiv:gr-qc/9812046, standard 1+3 covariant kinematics.

The novelty gate must compare the exact representation, number and parity type
of vectors, invariant family, local/global claim, and explicit factorization.
