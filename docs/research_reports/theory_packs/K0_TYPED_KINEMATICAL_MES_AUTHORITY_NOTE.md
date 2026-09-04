# K0 — Typed kinematical MES authority crosswalk

## Result

The current Report-A draft correctly makes the low-multipole tensors

\[
\mathcal O_{\rm low}=(Q_{ab},O_{abc})
\]

the primary observable state and rejects scalar-only MES ranks as current
observational results. It nevertheless omits a second tensorisation already
present in the original repository programme: the typed physical state

\[
\mathcal X_{\rm phys}
=\mathcal K_{\rm cong}\times\mathcal V_{\rm frame}\times\mathcal G,
\]

where

\[
\mathcal K_{\rm cong}=(\sigma_{ab},\omega_a,A_a),
\qquad
\mathcal V_{\rm frame}=(\beta_{RO}^{a},\beta_{RM}^{a},\beta_{MO}^{a}).
\]

The observable and physical states are not identical. Their relation requires
a separately declared response model and an identification analysis.

## 1. Four objects that must not be collapsed

The revised report must preserve four distinct objects.

1. **Observable state**
   \[
   \mathcal O_{\rm low}=(Q,O,\ldots).
   \]

2. **Physical kinematical state**
   \[
   X=(\sigma,\omega,A,\beta_{RO},\beta_{RM},\beta_{MO},\mathcal G,\ldots).
   \]

3. **MES anchor family**
   \[
   \mathcal B_{\rm MES}(\epsilon_1,\epsilon_2,\epsilon_3),
   \]
   containing only registered, premise-conditioned sector bounds.

4. **Identified set**
   \[
   \Theta(y)=\{X:X\text{ satisfies every available sector anchor and }
   \mathcal R(X)\text{ is compatible with }y\}.
   \]

An anchor body is not a physical-state estimate. An observable tensor is not a
kinematical tensor. A response relation is not a scalar bound. An identified
set is not a point estimate unless a separate rank and regularity argument
establishes point identification.

## 2. Sector-wise MES inheritance

The active geodesic MES authority supplies two verified channels:

\[
\texttt{MES\_G\_SIGMA}\longrightarrow
\texttt{sigma\_ab\_sigma\_ab\_over\_6H2},
\]

and

\[
\texttt{MES\_G\_OMEGA}\longrightarrow
\texttt{omega\_ab\_omega\_ab\_over\_6H2}.
\]

Their exact normalisation, frame, congruence, perturbative order and dipole
attribution are carried by the registered anchor metadata. The report should
retain the registered invariant names wherever conversion between a vorticity
vector and antisymmetric tensor could change a numerical factor.

Acceleration \(A_a\) remains a typed physical component but has
`NO_MES_ANCHOR` on the active geodesic branch. The anisotropic-curvature
coordinate likewise has no registered MES curvature ceiling. Absence of an
anchor is a typed result, not a zero radius and not permission to invent a
bound.

## 3. Radial-only theorem

Let \(V\) be an orthogonal representation of \(O(3)\), and let an available
MES sector body be

\[
B_R=\{x\in V:\|x\|\le R\}.
\]

For every \(g\in O(3)\),

\[
\|gx\|^2=\langle gx,gx\rangle=\langle x,x\rangle.
\]

Hence

\[
x\in B_R\quad\Longleftrightarrow\quad gx\in B_R.
\]

The bound constrains the orbit radius but is constant along the orbit. It
therefore cannot select an eigenframe, vector direction, handedness or other
tensor morphology. This is the correct inheritance of the older scalar MES
bound inside a tensorised physical-state programme. It is consistent with the
scalar-to-tensor equivariance obstruction.

Morphology nevertheless remains part of the physical state. Registered
functionals such as

\[
\operatorname{tr}\sigma^3,
\qquad
\beta_{RM}\!\cdot\!\omega,
\qquad
\beta_{RM}^{a}\sigma_{ab}\beta_{RM}^{b}
\]

carry shape, parity or relative-orientation information independently of the
radial MES anchors.

## 4. Product-body stress and anti-cancellation

For available sector balls

\[
B_j=\{x_j:\|x_j\|\le R_j\},
\qquad
\mathcal B=\prod_jB_j,
\]

the Minkowski gauge is

\[
\boxed{\rho_{\mathcal B}(x)=\max_j\frac{\|x_j\|}{R_j}}.
\]

Indeed, \(x\in t\mathcal B\) if and only if \(\|x_j\|\le tR_j\) for every
\(j\), so the smallest admissible \(t\) is the displayed maximum. Shear and
vorticity stresses therefore cannot cancel as they could in a signed scalar
sum.

A numerical sector stress is defined only when numerator and anchor agree in
target sector, invariant, frame, congruence, normalisation, perturbative order
and branch. Otherwise the result is a typed `CHANNEL_MISMATCH`,
`ANCHOR_UNAVAILABLE` or `NUMERATOR_UNIDENTIFIED` state.

## 5. Response-limited identification

The MES body alone supplies no map

\[
(Q,O)\longmapsto(\sigma,\omega,A).
\]

Within the current Report-A scope, the closed kinematical response lane is the
local observer-radiation velocity \(\beta_{RO}\) through WU-010. It must not be
identified with global matter-frame tilt. Full observable responses for
\(\sigma_{ab}\), \(\omega_a\), \(A_a\), \(\beta_{RM}\), \(\beta_{MO}\) and
the optional geometry tensors are not closed by the present report.

Consequently, unavailable or rank-deficient response sectors remain set-valued
or abstaining. No point attribution is admitted merely because a scalar MES
ceiling is small.

## 6. Provenance

The physical-state lane is source-authoritative on the merged PR-367 lineage,
whereas the current report branch descends from the corrected Q/O semantic
line. These histories are Git-diverged. K0 binds the donor files by exact Git
blob identity and imports their semantics into the report plan; it does not
claim that the production modules are present or executed on the Report-A
head.

## 7. Literature boundary

The Maartens–Ellis–Stoeger programme and later 1+3 covariant CMB literature
treat radiation multipoles and spacetime kinematical or curvature variables in
a covariant hierarchy. This supports retaining shear and vorticity as physical
tensor sectors rather than replacing them by anomaly scores. The exact
software partition, channel keys, product-body gauge and
response/identified-set contract remain repository-specific constructions and
require direct derivation and source binding.

Partial-identification literature supports reporting a feasible set under
inequality restrictions rather than a point when the observation map is
incomplete. It does not prove that the present physical identified set is
sharp; sharpness and response completeness remain separate obligations.

## 8. Claim ceiling

K0 establishes an authority crosswalk, not a new observational or physical
measurement. It introduces no corrected Planck rank, no physical shear or
vorticity estimate, no global tilt, no Bianchi-family attribution, no
finite-HEALPix no-go theorem and no BASS/native-solver result.

## Evidence grade

```text
source identity and semantic crosswalk: SOURCE-CHECKED
radial-only theorem: DERIVED-EXACT
product-body gauge: DERIVED-EXACT
Wolfram replay: BLOCKED BY UPSTREAM HTTP 502
runtime probe: PARTIAL RUNTIME RECOVERY; NO ACCEPTED SCIENTIFIC RECEIPT
claim promotion: NONE
```
