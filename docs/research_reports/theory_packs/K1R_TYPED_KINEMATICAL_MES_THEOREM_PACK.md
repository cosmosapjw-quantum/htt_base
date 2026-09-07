# K1R — Typed kinematical MES theorem repair and completion

## Status and authority

This pack supersedes the semantic interpretation of
`K1_TYPED_KINEMATICAL_MES_THEOREM_PACK.md` where the two differ. It preserves
the ten-result K1 core while closing the bounded review findings required
before K2 claim recompilation.

The report and physical-state donor are Git-diverged authorities:

```text
Report-A K1 input head:
409ad49a341870f49694b9a57e0baa19ddf841c4

Merged physical-state donor PR #367 head:
6bafca66285ef071081453313bb7d2d6b261599c
```

The donor is imported by exact source identity and scientific semantics. Its
production code and execution status are not copied into the report branch.
This pack contains no Planck/FFP10 execution, no physical shear, vorticity or
acceleration estimate, no global-tilt attribution, no finite-HEALPix no-go
theorem and no native BASS result.

## 1. Four non-interchangeable objects

Let

\[
\mathcal O_{\rm low}=(Q_{ab},O_{abc},\ldots)
\]

be the observable low-multipole temperature-tensor state. Let

\[
\mathcal X_{\rm phys}
=\mathcal K_{\rm cong}\times\mathcal V_{\rm frame}\times\mathcal G
\]

be the typed physical state, where

\[
\mathcal K_{\rm cong}=(\sigma_{ab},\omega_a,A_a)
\]

contains kinematics of one declared congruence and

\[
\mathcal V_{\rm frame}
=(\beta_{RO}^{a},\beta_{RM}^{a},\beta_{MO}^{a})
\]

contains velocities between radiation, matter and observer frames. The
registered first-order relation is

\[
\beta_{RO}^{a}
=\beta_{RM}^{a}+\beta_{MO}^{a}+O(\beta^2).
\]

Let \(\mathfrak A_{\rm MES}\) be the family of premise-matched MES anchor
authorities, and let \(\Theta\) be a set-valued physical identification
object. Then

\[
\boxed{
\mathcal O_{\rm low}
\ne
\mathcal X_{\rm phys}
\ne
\mathfrak A_{\rm MES}
\ne
\Theta
}.
\]

An equality of representation types does not imply a physical identity. In
particular, \(Q_{ab}\) and \(\sigma_{ab}\) are both STF rank-two tensors but
encode different physical objects.

## 2. Geometry nomenclature and representation registry

The geometry block contains a signed scalar curvature-budget coordinate

\[
\Delta\Omega_k\in V_0
\]

and, separately, optional anisotropic geometry tensors. The scalar coordinate
is not an anisotropic spatial-curvature tensor. The latter is represented by

\[
{}^{(3)}S_{ab}={}^{(3)}R_{\langle ab\rangle}
\]

when available.

| Object | Raw dimension | O(3) type | Role |
|---|---:|---|---|
| \(Q_{ab}\) | 5 | polar STF2; \(\ell=2\) even | observable block |
| \(O_{abc}\) | 7 | polar STF3; \(\ell=3\) odd | observable block |
| \(\sigma_{ab}\) | 5 | polar STF2 | congruence kinematics |
| \(\omega_a\) | 3 | axial vector | congruence kinematics |
| \(A_a\) | 3 | polar vector | congruence kinematics |
| \(\beta_{RM}^a\) | 3 | polar vector | radiation-matter relation |
| \(\beta_{MO}^a\) | 3 | polar vector | matter-observer relation |
| \(\beta_{RO}^a\) | 3 | polar vector | first-order closure-derived relation |
| \(\Delta\Omega_k\) | 1 | scalar | signed curvature-budget coordinate |
| \({}^{(3)}S_{ab}\) | 5 | polar STF2 | optional anisotropic spatial curvature |
| \(E_{ab}\) | 5 | polar STF2 | optional electric Weyl tensor |
| \(H_{ab}\) | 5 | axial STF2 | optional magnetic Weyl tensor |
| \(\pi_{ab}\) | 5 | polar STF2 | optional anisotropic stress |

Excluding optional geometry tensors and treating \(\beta_{RO}\) as a
derived first-order view, the general physical core has raw dimension

\[
5+3+3+3+3+1=18.
\]

On a locally free principal \(SO(3)\) stratum only, its quotient dimension is

\[
\boxed{18-3=15}.
\]

On the registered geodesic subdomain, \(A_a=0\) is a branch premise, so the
raw dimension becomes

\[
5+3+3+3+1=15
\]

and the corresponding locally free quotient dimension is

\[
\boxed{15-3=12}.
\]

These are conditional dimension counts, not global orbit-separation theorems.
They do not apply unchanged on strata with non-trivial stabilisers. Each
admitted optional STF2 geometry block adds five raw dimensions before the
appropriate stabiliser correction.

## Proposition K1R-T1 — typed state partition and missingness

The decomposition

\[
\mathcal X_{\rm phys}
=\mathcal K_{\rm cong}\times\mathcal V_{\rm frame}\times\mathcal G
\]

is semantic, not merely architectural. A legacy scalar or untyped vector is
not assigned to one of these blocks without an explicit adapter that fixes its
frame, congruence, epoch, averaging scale, basis, normalisation and
perturbative order. Missing components remain typed as missing, abstaining or
needing a native provider; they are never replaced by numerical zero.

**Status:** `SOURCE_DEFINED_EXACT`.

## Proposition K1R-T2 — state-anchor separation

A MES anchor is a conditional constraint on one named physical invariant. It
is not an element of \(\mathcal X_{\rm phys}\), an observation, a likelihood,
a posterior, a distance or an estimate of a tensor direction.

The verified numerical geodesic channels are

\[
\texttt{MES\_G\_SIGMA}
:\quad
\frac{\sigma_{ab}\sigma^{ab}}{6H^2},
\]

and

\[
\texttt{MES\_G\_OMEGA}
:\quad
\frac{\omega_{ab}\omega^{ab}}{6H^2},
\]

with the exact vector/tensor vorticity adapter and normalisation fixed by the
registered authority.

**Status:** `SOURCE_DEFINED_EXACT`.

## Proposition K1R-T3 — geodesic acceleration premise versus anchor availability

The MES theorem authority records

```text
MES_G_ACCEL:
  congruence: geodesic
  status: VERIFIED_STRUCTURAL
  coefficients: (0,0,0)
```

because the geodesic branch imposes

\[
A_a=0.
\]

This is a structural domain premise. The statistical anchor surface separately
returns an acceleration absence object with no numerical value. Consequently,

\[
\boxed{
A_a=0\ \text{on the geodesic branch}
\quad\ne\quad
\text{a zero-radius numerical MES anchor}
}.
\]

Outside the geodesic branch, \(A_a\) remains a typed physical component and no
active verified acceleration ceiling is admitted. A future Euler or momentum-
equation bound would be an `EXTERNAL_PHYSICAL` authority requiring a declared
equation of state, matter model, congruence and density-gradient bound.

**Status:** `SOURCE_DEFINED_STRUCTURAL_BOUNDARY`.

## Theorem K1R-T4 — radial-only information

Let \(V\) be an orthogonal representation of \(O(3)\), and let

\[
B_R=\{x\in V:\|x\|\le R\},\qquad R>0.
\]

For every \(g\in O(3)\),

\[
\|gx\|^2
=\langle x,g^Tgx\rangle
=\|x\|^2.
\]

Hence

\[
x\in B_R\quad\Longleftrightarrow\quad gx\in B_R.
\]

A rotationally invariant MES sector bound is therefore constant on each
orbit. It may constrain a radial magnitude but cannot select an eigenframe,
vector direction, handedness or non-radial tensor morphology. Equivalently, a
non-zero vector or STF tensor cannot be constructed equivariantly from
rotational scalar data alone.

**Status:** `DERIVED_EXACT`; fresh Wolfram execution remained unavailable and is
not counted as a pass.

## Theorem K1R-T5 — factorised product-body gauge

Let \(B_j\) be absorbing sector bodies with Minkowski gauges \(\rho_j\), and
let

\[
B_{\rm prod}=\prod_{j\in J}B_j.
\]

Then

\[
\boxed{
\rho_{B_{\rm prod}}(x)
=\max_{j\in J}\rho_j(x_j)
}.
\]

Indeed, \(x\in tB_{\rm prod}\) if and only if
\(\rho_j(x_j)\le t\) for every \(j\); the least admissible \(t\) is the
maximum. The factorised gauge therefore prevents signed cancellation between
sector stresses.

This theorem concerns the factorised anchor body only. The full feasible set

\[
F(y;\eta)
=D_\eta\cap B_{\rm prod}(y;\eta)
\cap\mathcal R_\eta^{-1}(C_y(\eta))
\]

need not factorise after response, physics or nuisance constraints are
imposed. Its gauge or support function must not be replaced by the product-body
maximum without a separate factorisation proof.

For example, with

\[
B_0=[-1,1]^2,
\qquad
F=B_0\cap\{x_1+x_2\le1\},
\]

one has \(\rho_{B_0}(1,1)=1\) but \(\rho_F(1,1)=2\).

**Status:** `DERIVED_EXACT_WITH_SCOPE_BOUNDARY`.

## Proposition K1R-T6 — quadratic sector saturation and gauge are related but distinct

Suppose a sector has a Euclidean radius \(R_j\), quadratic numerator

\[
N_j=\|x_j\|^2
\]

and ceiling \(U_j=R_j^2\). Define the quadratic sector saturation

\[
S_j=\frac{N_j}{U_j}.
\]

Then

\[
S_j=\rho_j(x_j)^2
\]

and, for the factorised product body,

\[
\boxed{
\rho_{B_{\rm prod}}(x)^2
=\max_j S_j.
}
\]

The admission boundaries agree,

\[
\rho_{B_{\rm prod}}\le1
\quad\Longleftrightarrow\quad
\max_jS_j\le1,
\]

but the numerical margins

\[
\max(\rho_{B_{\rm prod}}-1,0)
\]

and

\[
\max(\max_jS_j-1,0)
\]

are different diagnostics. Neither is automatically a probability, likelihood
or evidence term.

If a fixed ensemble-calibrated ceiling \(U_j>0\) and an identified numerator
interval

\[
N_j=[\underline N_j,\overline N_j]
\]

are available, then

\[
S_j=
\left[
\frac{\underline N_j}{U_j},
\frac{\overline N_j}{U_j}
\right]
\]

and the exceedance interval is obtained by the monotone map
\(s\mapsto\max(s-1,0)\). A realisation-conditional random denominator is not
divided as though fixed; it remains `RATIO_UNIDENTIFIED` and requires the
registered joint random-anchor inference lane.

**Status:** `DERIVED_EXACT_PLUS_SOURCE_CONTRACT`.

## Proposition K1R-T7 — exact channel matching

A numerical sector stress is admitted only when numerator and anchor share one
exact channel key:

\[
(\text{sector},\text{invariant},\text{frame},\text{congruence},
\text{normalisation},\text{order},\text{branch}).
\]

A mismatch or unavailable object yields a typed non-numerical status such as

```text
NUMERATOR_UNIDENTIFIED
ANCHOR_UNAVAILABLE
CHANNEL_MISMATCH
RATIO_UNIDENTIFIED
```

rather than a fabricated ratio.

**Status:** `SOURCE_DEFINED_EXACT`.

## Theorem K1R-T8 — jointly conditioned physical identified set

Let \(\eta\) collect predeclared frame, congruence, perturbative branch,
attribution, nuisance choices and analysis procedure. If MES ceilings are
constructed from the same low-multipole data \(y\) as the response
compatibility region, define

\[
\boxed{
\Theta(y;\eta)
=D_\eta
\cap B_{\rm MES}(y;\eta)
\cap\mathcal R_\eta^{-1}(C_y(\eta)).
}
\]

The anchor and response restrictions form one joint feasible system. Their
appearance as separate set factors does not make them independent evidence.
If the same data enter both constructions, a likelihood, p-value or evidence
factorisation requires an additional joint-law argument and is not supplied by
this set identity.

The complete data-to-output map used in a finite-null rank must therefore
include MES ceiling construction, anchor conditioning, chart handling,
nuisance fitting, selection, missingness, tie handling and final scoring.

**Status:** `DERIVED_CONDITIONAL_WITH_SOURCE_SUPPORTED_SET_SEMANTICS`.

## Theorem K1R-T9 — singleton feasible-fibre criterion

Consider an exact linear response \(\mathcal R_\eta\) and a feasible state
\(X_0\in\Theta(y;\eta)\). Let

\[
F_y=D_\eta\cap B_{\rm MES}(y;\eta).
\]

Then

\[
\Theta(y;\eta)=F_y\cap(X_0+\ker\mathcal R_\eta).
\]

Consequently,

\[
\boxed{
\Theta(y;\eta)=\{X_0\}
\quad\Longleftrightarrow\quad
\{h\in\ker\mathcal R_\eta:X_0+h\in F_y\}=\{0\}.
}
\]

Full column rank of the response is sufficient but not necessary, because
predeclared inequalities may remove every non-zero kernel direction. For
example,

\[
\mathcal R=(1\ \ 1),\qquad y=0,
\qquad D=\{(x_1,x_2):x_1\ge0,\ x_2\ge0\}
\]

has rank one but the unique feasible solution is \((0,0)\).

A bounded non-singleton set is partial identification; an unbounded set retains
recession directions; an empty set is model infeasibility; and solver or
authority failure is undetermined. If a response provider is absent, the
correct outcome is non-identification or abstention rather than an inferred
tensor direction.

**Status:** `DERIVED_EXACT_SET_THEOREM_WITH_CONDITIONAL_APPLICATION`.

## Proposition K1R-T10 — velocity-frame response boundary

The three velocity blocks retain distinct source semantics. WU-010 transforms
the radiation sky to a local observer and therefore closes only the scoped
radiation-observer response associated with \(\beta_{RO}\). It does not by
itself identify \(\beta_{RM}\), \(\beta_{MO}\), global matter-frame tilt or
congruence kinematics.

**Status:** `LITERATURE_AND_IMPLEMENTATION_SUPPORTED_SCOPED_RESULT`.

## Proposition K1R-T11 — physical morphology remains separately typed

Registered physical functionals may return scalar, pseudoscalar, polar or
axial vector, STF tensor, identified-set or path-valued outputs. Examples
include

\[
\sigma_{ab},\quad\omega_a,\quad A_a,
\quad\operatorname{tr}\sigma^2,
\quad\operatorname{tr}\sigma^3,
\quad\omega^2,
\]

\[
\beta_{RM}\cdot\omega,
\qquad
\beta_{RM}^{a}\sigma_{ab}\beta_{RM}^{b}.
\]

Each functional retains its input-state identity, codomain, O(3) type, parity,
frame, congruence, epoch, scale, normalisation, branch and optional anchor
identity. Its existence does not imply observational identification.

**Status:** `SOURCE_DEFINED_EXACT`.

## Proposition K1R-T12 — scalar inheritance is not scalar-method revival

The retired scalar-collection lane used a scalar collection as the primary
observable morphology or current anomaly rank. The retained MES lane instead
uses scalar quantities as one-way, premise-conditioned radial constraints on
named sectors of a distinct physical tensor state.

Thus tensorisation does not discard the original MES physical inequalities;
it embeds them as typed sector constraints while preserving the full Q/O
observable morphology, physical tensor functionals and response-limited
identification.

**Status:** `DERIVED_POLICY_EXACT`.

## Integrated scientific spine

```text
observable Q/O tensor state
→ typed congruence/frame/geometry state
→ sector-matched MES constraints
→ physical tensor functionals and orbit morphology
→ jointly conditioned response/identified set
→ finite-null validity of the complete analysis map
→ scoped local beta_RO response
→ processed-response quotient
→ continuum/finite numerical boundary
→ conditional robust-rank certification
```

No anchor-to-state arrow is generative. No observable-to-physical tensor map is
admitted without a declared response. No product-body formula is silently
extended to a coupled feasible set.

## Claim boundary

This pack does not supply:

- a corrected tensorised Planck rank;
- an empirical observer velocity or boost subtraction;
- a physical shear, vorticity or acceleration estimate;
- a global-tilt or geometry detection;
- a Bianchi-family attribution;
- a complete finite-HEALPix no-go theorem;
- a BASS or native-solver result;
- publication or merge authority.

## Terminal

```text
PASS_K1R_TYPED_KINEMATICAL_MES_REPAIR_SOURCE
/
GEOMETRY_DIMENSION_AND_PARITY_REGISTRY_CLOSED
/
GEODESIC_ACCELERATION_PREMISE_SEPARATED_FROM_NUMERICAL_ANCHOR
/
DATA_DEPENDENT_IDENTIFIED_SET_AND_SHARED_DATA_FIREWALL_CLOSED
/
PRODUCT_GAUGE_AND_QUADRATIC_SATURATION_SEPARATED
/
PHYSICAL_RESPONSE_SECTORS_EXCEPT_BETA_RO_UNRESOLVED
/
WOLFRAM_REPLAY_BLOCKED_NOT_COUNTED
/
NO_CLAIM_PROMOTION
```
