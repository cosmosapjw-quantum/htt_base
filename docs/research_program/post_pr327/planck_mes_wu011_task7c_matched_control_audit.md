# PMG-WU-011 Task-7C matched full-sky control audit

Date: 2026-09-02
Owner: OBSSTAT / PHYS-MATH / PHYS-MATH-CODE
Claim tier: diagnostic only
Scientific terminal authorized: no
Empirical beta fit: no
Global-tilt claim: no
Bianchi attribution: no
Merge authorized: no

## Executive verdict

```text
MATCHED_FULLSKY_CONTROL_IMPLEMENTED_AND_CONNECTED
/
CONTROL_ANCHORED_RANK_ADJUDICATION_EXECUTED
/
PASS_TASK7C_MATCHED_CONTROL_RANK_UNRESOLVED
/
NO_OPERATOR_SPECIFIC_CONTAINMENT_CLAIM
```

The generic repository no-go against finite-low-ell sufficiency is reused and
is not re-derived here.  The stronger processed-operator statement

```text
Im J_b subset Im K_b(L)
```

is **not** established.  At the nominal control factor `s_ctrl=5`, seventeen
of eighteen direction/cutoff coordinates are rank-ambiguous.  The single
resolved coordinate, `Z` at `L=9`, retains an eleven-dimensional low-response
survivor and therefore rejects containment at that coordinate.

The matched full-sky control is useful and reproducible, but its scalar
operator norm is too coarse to define the numerical image rank of the cut-sky
matrix.  The next node must construct a matrix-valued numerical-error envelope;
it must not extend the source cutoff to `L=20` merely to outrun a rank-policy
ambiguity.

## Question and notation

For one fixed boost direction, write

```text
J_b             : registered low-source response into retained ell=2..5
K_b(L)          : cumulative source ell=7..L cut-sky nuisance response
K_b^full(L)     : numerically identical full-sky replay control
```

The first control-anchored threshold is

```text
tau_K = max(
    rho_rel sigma_1(K),
    s_ctrl sigma_1(K_full),
    c_mach eps_machine max(m,n) sigma_1(J)
).
```

A singular value in `[tau_K/2, 2 tau_K]` is ambiguous and yields no
containment decision.  A resolved containment result must also satisfy

```text
rank(P_Im(K)^perp J) = rank([K J]) - rank(K).
```

## Exact PHYS-MATH checks

A fresh Wolfram calculation verified:

1. the rank-one angular selection rule has no channel from source
   `ell=7..20` into retained `ell=2..5` on the exact full sky;
2. the first available channels are nearest neighbours, beginning with
   `7 -> 6,8`;
3. `sum_(ell=7)^L (2 ell+1) = (L-6)(L+8)`, giving dimensions
   `15,32,51,120,240,392` at `L=7,8,9,12,16,20`;
4. exact integer-matrix trials gave zero residual for
   `rank(P_Im(K)^perp J) - [rank([K J])-rank(K)]`.

These are dimensionless angular or finite-dimensional linear-algebra
statements.  Dimension 32 at `L=8` does not prove image saturation; a
numerically certified rank or direct containment witness remains necessary.

## Direct arXiv anchors

The literature was read from the arXiv sources rather than from secondary
summaries.

- Aluri, Pant, Rotti, and Souradeep, arXiv:1510.02454: a first-order CMB
  Doppler boost is an off-diagonal nearest-neighbour harmonic response;
  masking produces additional mode coupling and its mean-field/bias must be
  characterized with unboosted simulations.
- Leung et al., arXiv:2111.01113: a scalar transfer function cannot in general
  represent realistic filtering-induced mode mixing; a two-dimensional
  response matrix is required and its inverse problem can be ill-conditioned.
- Ferreira and Quartin, arXiv:2107.10846: aberration, Doppler modulation, and
  the dipole must remain separated in a realistic beam/noise/mask pipeline,
  with an independent implementation used as a cross-check.
- Chluba and Ravenni, arXiv:2505.02080: the general boost operator is generated
  from aberration kernels; its first-order harmonic structure supplies the
  nearest-neighbour selection rule used by the exact full-sky control.

These papers support a matrix-valued, simulation-controlled response.  They do
not choose the numerical SVD rank threshold for this project.

## Implementation and TDD lineage

### A2 RED: matched-control bridge absent

```text
head: c58e1938b2dcb0a33428102cd9385209ac56683e
workflow: WU011 Task7C rank policy #4 / 33639016182
result: 1 failed, 6 passed
failure: processed_boost_matched_control absent
```

### A2 GREEN: matched full-sky control core

```text
head: 1dc5b6b0d7290b92468c542c948c7170d4e3325e
workflow: WU011 Task7C rank policy #5 / 33639476183
result: 7 passed
```

Implemented surfaces:

```text
htt/obsstat/processed_boost_matched_control.py
htt/test_wu011_task7c_matched_control.py
htt/test_wu011_task7c_rank_policy.py
```

The implementation rebuilds the source operator and the full-sky control from
the same `Task7COperatorSpec`.  It requires equality of `nside`,
`processing_lmax`, transfer kind, source cutoffs, source-operator identity, and
direction/cutoff registries.  Only the mask and therefore the joint-estimator
operator identity may differ.

### A3 RED: aggregate adjudicator absent

```text
head: c3832c4aad6b57eee95d49849b5163b3420ec9d8
workflow: WU011 Task7C rank policy #8 / 33641331559
result: 2 failed, 7 passed
failure: processed_boost_matched_control_adjudication absent
```

### A3 GREEN: fail-closed adjudication

```text
execution head: f635d873cf5e77f7cb0d2756469acde60b8609e5
workflow: WU011 Task7C rank policy #11 / 33642058624
result: 9 passed in 0.39 s
```

Additional surfaces:

```text
htt/obsstat/processed_boost_matched_control_adjudication.py
htt/obsstat/processed_boost_matched_control_artifacts.py
scripts/observed_runs/run_planck_mes_wu011_nuisance_span.py
```

The adjudicator refuses malformed rows, duplicated coordinates, incomplete
control-factor registries, rank-identity violations, or any resolved
containment flag inconsistent with the two rank witnesses.  Ambiguity or
control-factor instability maps to a typed unresolved terminal rather than a
selected rank.

## Exact execution receipt

Frozen execution head:

```text
f635d873cf5e77f7cb0d2756469acde60b8609e5
```

Task-7C workflow:

```text
workflow: WU011 Task7C nuisance span #24 / 33642058568
old Task-7C tests: 10 passed in 5.92 s
old terminal: PASS_TASK7C_SOURCE_BAND_NOT_CONVERGED
old content ID:
  sha256:60fd9a90af207a781951328642d1ad001aed46d08c8203c2bf5fa822fdf37e47
matched-control status: PASS_MATCHED_FULLSKY_CONTROL_RECEIPT
matched-control content ID:
  sha256:554cf43237fcebe429aab6f0c8a9295bed791d5e79337c2578852ebb76b7f52d
matched-control analyses: 54
adjudication terminal: PASS_TASK7C_MATCHED_CONTROL_RANK_UNRESOLVED
adjudication content ID:
  sha256:ceecd72723b5e746f1baf5feb4e61db2342c39663d215a045dbb81f6180ca92a
adjudication manifest:
  e7fae6af9229555aada372d7096f1f2f8b65be433b12af76a22137ef94a4e5c2
workflow artifact ID: 9851300447
workflow artifact digest:
  sha256:c9d6235f69fd27381279b0d007fd8dd1b75365f70bd5ce4e535f63ade4bb56a6
artifact branch:
  artifact/wu011-task7c-f635d873cf5e77f7cb0d2756469acde60b8609e5
```

All eight exact-head workflows succeeded: PR04, PR07, WU011 processed boost,
Task-7A, Task-7B, Task-7C nuisance span, Task-7C rank policy, and Repository
integrity.

## Quantitative result

The receipt contains

```text
6 directions x 3 cutoffs x 3 control factors = 54 rows.
```

At the nominal `s_ctrl=5`:

```text
coordinates: 18
rank ambiguous: 17
resolved: 1
containment candidates: 0
resolved survivors: 1
control-factor sensitivity stable: false
```

The only resolved coordinate is

```text
direction: Z
source cutoff: L=9
high rank: 21
surviving rank: 11
augmented-rank increment: 11
rank identity: true
containment: false
surviving Frobenius fraction: 0.18127109460557095
```

The smallest-singular-value saturation margin is

```text
mu = sigma_min(K) / tau_K.
```

For full row rank to be outside the ambiguity shell, `mu > 2` is required.
The best observed value is

```text
mu_max = 0.2040651815504855
at direction Z, L=12.
```

Thus even the best coordinate lies almost one order of magnitude below the
threshold crossing and almost a factor ten below the unambiguous full-rank
condition.  Increasing the cutoff from `L=12` to `L=16` does not improve this:
for Z the margin decreases from `0.2041` to `0.1664`, and for the other
symmetry classes it remains near `0.025`.

The matched full-sky/cut-sky operator-norm ratio grows with cutoff, approximately

```text
X/Y:       1.15e-3 -> 1.95e-3 -> 3.42e-3
Z:         8.39e-5 -> 1.20e-4 -> 2.00e-4
diagonals: 6.30e-4 -> 1.11e-3 -> 1.97e-3
```

for `L=9,12,16`.  The full-sky replay floor is small in operator norm, but the
cut-sky singular spectrum is sufficiently broad that a scalar multiple of that
norm places many modes inside the ambiguity shell.

## Plot-driven adversarial audit

Generated evidence:

```text
matched_control/control_to_cutsky_operator_ratio.png
matched_control/adjudication/decision_status_matrix.png
matched_control/adjudication/saturation_margin_vs_cutoff.png
```

### Correctness

The decision matrix explicitly renders `A` for ambiguity and `S` for the one
resolved survivor.  It fixes the earlier plotting failure in which ambiguous
coordinates were converted to NaN and visually disappeared.

The saturation-margin plot places all curves below the threshold crossing
`mu=1` and below the outside-shell line `mu=2`.  It therefore agrees with the
typed unresolved terminal.

### Retrieval

The matrix-valued mask/filter response agrees with the direct arXiv literature.
The plots do not convert a diagonal or scalar transfer approximation into a
physical separation claim.

### Augmentation

The negative result persists over:

- all six registered directions;
- cutoffs `L=9,12,16`;
- control factors `2,5,10`;
- exact-head reruns with pinned `healpy=1.20.0`.

This is not yet a multi-resolution numerical-error enclosure: the primary
matched control is `nside=16`.  A single full-sky replay matrix cannot be
assumed to bound all cut-sky discretization error directions.

### Generation

The next observable predicted to be decisive is not another tail norm.  It is
the singular spectrum after whitening by a matrix-valued numerical-error
operator constructed from matched full-sky replay and same-operator resolution
or iteration differences.

### Adversarial verdict

```text
rejected claim:
  current high-source image is proven to contain the low-source image

surviving claim:
  the scalar matched-control rank rule is too coarse and fails closed

narrowed project state:
  operator-specific containment remains numerically unresolved
```

## PHYS-MATH audit

PASS:

- full-sky rank-one selection rule;
- source-dimension formula;
- nested cumulative high-source image;
- augmented-rank identity;
- unit and frame neutrality of the linear-algebra test;
- explicit separation of local observer boost from global matter tilt.

P1 remaining:

- `||K_full||_2` is one scalar, not a directional or matrix-valued numerical
  error envelope;
- no theorem establishes that one deterministic full-sky replay bounds the
  cut-sky numerical error in every output direction;
- a containment result under an unrestricted deterministic nuisance class
  would not imply non-identification under a specified physical high-ell
  covariance or prior.

## PHYS-MATH-CODE audit

Genuinely closed:

- matched operator reconstruction;
- source/control identity and metadata binding;
- control-floor self-test;
- control-factor sensitivity receipt;
- fail-closed aggregate adjudication;
- machine-readable status and plot artifacts;
- exact-head workflow and artifact publication.

Still open:

- matrix-valued numerical-error envelope;
- same-`processing_lmax` `nside=16/32` convergence pair for the primary wide
  case;
- map-to-alm iteration sensitivity;
- perturbation-certified rank intervals or generalized singular values;
- adaptive cutoff short-circuit after, not before, rank resolution;
- independent PHYS-MATH and PHYS-MATH-CODE review at a frozen final head.

P2 retained:

- the older principal-angle regression can fluctuate between exact zero and
  approximately `8.5e-7` degrees for the same coincident subspace.  The exact
  execution succeeded on the frozen head, so it did not block this receipt,
  but the test should eventually compare projectors/cosines rather than the
  last-bit arccos angle.

## Next DAG node

```text
PMG-WU-011-TASK7C-A4-
MATRIX-VALUED-NUMERICAL-ERROR-ENVELOPE
```

Required execution order:

1. construct matched full-sky and cut-sky responses at common
   `processing_lmax=17` for `nside=16` and `nside=32`;
2. add at least one map-to-alm iteration perturbation at fixed resolution;
3. form error matrices from resolution and iteration differences, retaining
   their output-direction structure;
4. compare scalar-floor SVD, error-whitened generalized singular values, and
   projector perturbation bounds;
5. demand stable rank intervals over all registered controls before evaluating
   containment;
6. run `L=9` first and extend only unresolved directions to `L=12`; do not run
   `L=16/20` as a substitute for numerical-rank resolution;
7. keep every output diagnostic-only until an independent dual audit passes.

Forbidden now:

- empirical beta fitting;
- source subtraction;
- global-tilt interpretation;
- Bianchi-family attribution;
- covariance-aware likelihood without a declared high-ell covariance;
- merge or claim promotion;
- performance optimization of this path before the rank contract is stable.
