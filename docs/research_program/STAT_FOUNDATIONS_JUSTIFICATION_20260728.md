# Statistical justification of premise anchors and response geometry

Status: canonical methodology authority for PR-254 through PR-258
Claim tier ceiling: `diagnostic_only`
Roadmap claim level: `roadmap_rescue_v1:C2`
Data lane: finite analytic or synthetic response supports only
Scientific status: `OPEN`

## 1. Scope

This document separates three objects that must not be identified with one
another:

1. a physical departure state;
2. stress against a typed premise anchor; and
3. what a declared response operator can identify.

The separation is necessary because changing coordinates, choosing a physical
reference scale, and gaining information from data are different operations.
No normalizer creates response rank. No anchor stress is automatically a
distance from FLRW, a probability, an occupancy fraction, or evidence. No
finite pre-native response library identifies a Bianchi family.

The canonical state remains

\[
u=(\sigma_{ab}[5],\omega_a[3],\beta_a[3],\Delta\Omega_k[1]).
\]

The historical signed budget coordinate \(x_C\) remains a
`BC1_LEGACY_PROJECTION`: it is one signed support direction of the state and
retains its frozen numerical values. It is not a state norm, an identified
estimand, evidence, or physical volume occupancy. Refining the representation
does not promote its claim tier (`BC2_NO_REPRESENTATION_PROMOTION`).

## 2. Typed premise anchors

For a fixed typed anchor body \(\mathcal A\), the runtime defines a Minkowski
gauge only when the registered body is closed, convex, absorbing, and contains
the origin:

\[
\rho_{\mathcal A}(u)=
\inf\{\lambda>0:u\in\lambda\mathcal A\}.
\]

The implemented and four-axis-checked statements are limited to:

- the unit sublevel is the registered body,
  \(\{u:\rho_{\mathcal A}(u)\leq1\}=\mathcal A\);
- for a product of typed Euclidean block balls,
  \(\rho_{\mathcal A}(u)=\max_j\|u_j\|/B_j\);
- if a registered physical premise class satisfies
  \(H_{\rm lin}\subseteq\mathcal A_{\rm MES}\), then
  \(H_{\rm lin}\Rightarrow\rho_{\rm MES}\leq1\);
- right multiplication of a response by an invertible anchor coordinate map
  preserves rank on the declared supported subspace.

Only the forward premise implication is licensed. A true-state value
\(\rho_{\rm MES}>1\) contradicts at least one registered premise in the
specified anchor branch. A value \(\rho_{\rm MES}\leq1\) does not support the
premise class, establish FLRW proximity, establish linearity, or identify a
source.

The strong general forms `J1-EXACT` (exact physical-set equality and essential
uniqueness) and `J2-UNIFORM` (uniform finite-sample validity with a noisy random
anchor) failed their registered counterexample-first lane in that generality.
They are `REFUTED_OR_RESTRICTED`, not established results. Any narrower future
theorem needs a new domain, joint law, assumptions, and validation contract.

### 2.1 Distinct margin quantities

The following quantities are different types:

\[
m=1-\rho,\qquad
h=\frac{1}{\rho},\qquad
h-1=\frac{1}{\rho}-1,\qquad
e_{\rm raw}=\max(\rho-1,0).
\]

Here \(m\) is an additive radial margin, \(h\) is a multiplicative scale to the
boundary, \(h-1\) is relative boundary growth, and \(e_{\rm raw}\) is raw
anchor excess. In particular, \(1-\rho\) is not multiplicative headroom and
raw anchor excess is not an e-value. A calibrated e-value requires a separate
registered joint null law and calibration receipt.

### 2.2 Normalizer benchmark

Expansion-normalized, MES-anchored, Fisher-whitened, template-limit,
dynamical-breakdown, and prior-quantile normalizers were compared on the same
synthetic base draws using purpose-specific Pareto vectors. There is no
universal scalar winner. MES is therefore classified as
`ONE_ANCHOR_AMONG_FAMILY`.

Exact transformed likelihoods remain invariant under an invertible coordinate
change. Differences caused by estimator restrictions or numerical
conditioning are reported as such; they are not information gain created by
the anchor.

## 3. Response geometry

Let \(R\) be a declared finite response matrix, \(C\) one symmetric positive
semidefinite covariance, \(P_N\) the nuisance-tangent projector in the
covariance-supported space, and \(D_{\mathcal A}\) an available invertible
anchor coordinate map. The anchored response object is

\[
J_{\mathcal A}=P_N C_{\rm supp}^{-1/2}R D_{\mathcal A}.
\]

All terms have exact identities and matching units. The covariance-null
response is retained separately. Positive-diagonal correlation-null
directions use a dimensionless standardized residual. An exactly
zero-variance coordinate has no covariance-derived unit scale and is retained
instead as an exact structural equality constraint; any nonzero displacement
there fails closed independently of a positive coordinate-unit rescaling.
A missing provider is not a zero response. A singular covariance is evaluated
only on its supported quotient; either a structural-null mismatch or a
material dimensionless null residual prevents a finite supported-space
candidate.

This layer reports rank, singular spectrum, reachable and null directions,
principal angles, and identified-set contraction. It does not detect
nonlinearity or a physical source by itself. Nonlinearity, local/global source
geometry, low-\(\ell\) morphology, and response-class compatibility remain
separate report types.

For labels that distinguish a local boost from a global-tilt candidate, the
PR-256 source-response geometry is controlling. `NON_IDENTIFIED`, `SUM_ONLY`,
and `MISSING_RESPONSE_PROVIDER` prevent a response-class candidate even when
two selected finite nodes are far apart. That gate is valid only for the exact
PR-258 class, observable, covariance, nuisance, provider-response and transfer
contract used to construct it. A dimension-changing or otherwise nonidentical
crosswalk is unavailable and fails closed; PR-256 geometry must instead be
recomputed in the target observable space.

## 4. Finite response classes and open-set abstention

A PR-258 response class is an exact finite analytic or synthetic support under
one observable, covariance, nuisance, convention, and transfer contract. It is
not a continuous manifold, likelihood model, physical source, geometry, or
Bianchi family. The identifier is restricted to the
`response-class-*` namespace to prevent those meanings from entering the
public API.

All PR-258 edges and decisions use one score:

\[
d^2(x,S)=\min_{s\in S}
\left\|P_N C_{\rm supp}^{-1/2}(x-s)\right\|_2^2.
\]

Its registered metric identity is
`OBSERVABLE_COVARIANCE_SQUARED_DISTANCE_V1`. Anchor coordinate scaling is the
identity for this observable-space distance. The equivalence tolerance,
unknown threshold, and decision margin all live in this same dimensionless
squared-score space. The equivalence report binds the exact numeric nuisance
tangent identity; classification under different nuisance bytes is a contract
error. If support nodes tie in supported score, the node-consistent
covariance-null residual and then stable node identity break the tie.
The covariance-null operator is retained from the standardized covariance
support before nuisance projection. A direction removed only because it lies
on the registered nuisance orbit therefore has zero covariance-null residual;
it is quotiented out and is not called unsupported.

Two supports receive a direct edge when their minimum squared separation is
at or below the frozen equivalence tolerance. Connected components are the
declared conservative closure of this non-transitive nearness relation. The
report retains direct edges and the full pairwise table; component membership
must not be narrated as pairwise equality. If all supports share an FLRW
boundary node, they collapse globally unless a detectable-domain restriction
was registered before scores were examined.

A positive unknown threshold defines an acceptance tube around exact finite
nodes. It does not interpolate a continuous response manifold. Status
precedence is fail-closed:

1. missing/native provider status;
2. unsupported covariance or material covariance-null residual;
3. global response-equivalence or non-clique closure;
4. unknown-tube boundary or exterior;
5. decision-margin tie or weak separation;
6. PR-256 local/global source-rank gate, when applicable;
7. only then, `RESPONSE_CLASS_CANDIDATE`.

An unknown or ambiguous input carries no nearest-known decision label.
Neutral response classes cannot share one collection-level source gate with
local/global source-specific classes.
The source-specific gate has no public status-plus-receipt constructor. The
active HTT facade accepts an exact factory-derived PR-256
`SourceResponseGeometryReport`, content-identifies it, and binds its status to
the exact target class contracts, ordered observable labels, covariance,
nuisance tangent, provider IDs, provider response IDs and transfer provenance.
An arbitrary digest or a gate from another response library cannot unlock a
candidate.

### 4.1 Added observables

An added observable is keyed by stable support-node identities, not row
position. It carries one enlarged joint covariance, including cross
covariance, and one enlarged nuisance contract. The complete class graph is
recomputed. Separating members of an old component is insufficient if another
class becomes connected under the enlarged geometry.

This operation can reopen a finite response graph. It does not prove that a
physical null direction was reopened. A physical kernel claim requires a
separate response-rank proof showing that the added response row lies outside
the registered row span.

### 4.2 Finite-support sensitivity

Exact duplicate nodes are removed canonically and cannot change a decision.
Refinement, expansion, contraction, and boundary restriction are reported
separately. Without a parameter-domain measure and weights, these are
finite-support perturbations—not support volume, prior robustness, or
Bayesian evidence.

## 5. Synthetic benchmark result

The frozen PR-258 benchmark uses master seed `20260728`, 20,000 held-out draws
per registered cell, identity covariance, no nuisance direction, no transfer
provider, and thresholds frozen before generation. It reports:

- false response-class candidate rate: 0;
- response-equivalence coverage: 1;
- generator-conditional unknown detection rate: 1;
- abstention rate across the registered known/equivalence/unknown mixture:
  \(2/3\);
- maximum observed Monte Carlo standard error: approximately \(0.001925\);
- zero decision changes for the registered duplicate, refinement, expansion,
  contraction, and boundary-restriction probes.

These values validate only the declared synthetic software cells. The unknown
rate is conditional on the preregistered displaced unknown generator; it is
not uniform open-set coverage. Zero sensitivity in these particular probes is
not a general robustness theorem.

The benchmark envelope binds known and unknown cells to one supplied baseline
equivalence report, the equivalence cell to its own report, and each of all
five registered support perturbations to its own supplied report. All cells
share one frozen decision protocol. This prevents an unrelated equivalence
report from donating reopening metadata to otherwise incompatible
classification rows.
The aggregator also consumes the typed baseline and perturbed class
collections. It verifies immutable provider, convention, nuisance, transfer,
and source-semantics metadata; the declared subset or superset relation;
duplicate provenance; and distinct non-baseline report identities. A map
whose five labels all point to the baseline support is rejected before rates
are computed.

The benchmark reads no PR-151 partial data, observed sky, old Rust science
output, external transfer, or native solver output. Its machine claim tier is
`diagnostic_only`; roadmap level `C2` is a separate planning label.

## 6. Future native adapter

The future-native adapter is schema-only and returns `NEEDS_NATIVE`. It cannot
emit response values until an external native solver supplies a release,
commit, transfer-function specification, response-grid and parameter-domain
identities, harmonic convention, sky/mask/covariance contract, and validation
receipt.

Pre-native analytic or synthetic response classes cannot be relabeled as
native. The present equivalence quotient is a compatibility and abstention
layer that a future validated native atlas may consume; it is not that atlas.

## 7. Claim boundary

Supported:

- typed premise-anchor stress and distinct margin semantics;
- purpose-specific normalizer comparison;
- covariance-supported response rank and null directions;
- finite response-equivalence components;
- generator-conditional synthetic unknown rejection and abstention;
- negative, inconclusive, missing-provider, and `NEEDS_NATIVE` outcomes.

Forbidden:

- treating \(x_C\), anchor stress, or response distance as FLRW distance,
  occupancy, evidence, posterior probability, or source classification;
- reporting prior-induced rank as data identification;
- replacing missing covariance, response, or transfer components by zero;
- Bianchi family identification, ranking, or geometry detection;
- observational validation from the PR-258 synthetic benchmark;
- native-solver validation before the future adapter gate;
- using PR-151 partial acquisition or old Rust science output as validation.

The strongest current conclusion is therefore methodological: typed premise
anchors and covariance-supported response geometry form a testable
intermediate layer with explicit abstention. They do not establish an
observed departure from FLRW or identify a Bianchi family.
