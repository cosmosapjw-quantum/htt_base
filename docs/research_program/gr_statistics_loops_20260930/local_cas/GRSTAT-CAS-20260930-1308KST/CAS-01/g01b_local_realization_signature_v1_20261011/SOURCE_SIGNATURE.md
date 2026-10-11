# G01-B local-realization source signature

Status: **source signature recovered; local-realization theorem not formally
proved**.

## Bound statement

`gr/OPTICAL_THEOREMS.md`, SHA-256
`5ae2b6a65a5704247bed3d7dc5f01924318063ee5443cfa95c30c452b0ea8c21`,
§4 (Theorem 3) fixes the intended local theorem.  It assumes a smooth
Lorentzian metric near `p`, observer `o`, an admissible optical pair, and a
spatial skew fibre element `W`.  In normal coordinates matched to the observer
tetrad it defines

```text
v^b(x) = u^b + c⁻¹ η^(bd) Q_(ad) x^a
u^b(x) = v^b(x) / sqrt(-g_(cd)(x) v^c(x) v^d(x)).
```

The proposed conclusions are strictly local: some open neighbourhood of `p`
has future-timelike `v`; the normalized field is smooth and future unit; its
value and covariant first derivative are `u(0)=u0` and
`∇_a u_b(0)=Q_ab/c`.  Defining the physical field `U=c*u` gives the prescribed
`∇_a U_b(0)=Q_ab`; its integral curves are a local congruence.  The source
explicitly denies a fixed-size neighbourhood, finite-distance bound, global
extension, homogeneity, or a material/Einstein realization.  With `Q` formed
from the admissible pair and its chosen spatial-skew fibre element `W` by the
source's Eq. (11), Theorem 3 also concludes that the constructed field has the
prescribed ideal optical pair `(Z,H)` through its stated optical identity.

## Exact formal target to freeze before an author proof packet

The theorem must quantify a local coordinate chart, smooth metric components
`g : R^4 -> Bilin(R^4,R)`, a marked origin, `c>0`, a future unit value `u`, and
a covariant two-tensor `Q` satisfying the normalization compatibility
`Q_ab u^b = 0`.  It must also include the normal-coordinate facts

```text
g(0) = η,       derivative g at 0 = 0,
v(x) = u + c⁻¹ η⁻¹ Q^T x.
```

The required conclusion must exhibit an **open** neighbourhood `N` containing
`0` on which `g(x)(v(x),v(x)) < 0` and the selected time orientation is future;
define the positive-root normalization there; prove its smoothness, unit norm,
and `u(0)=u0`, `∇u(0)=Q/c`, hence `∇(c*u)(0)=Q`.  A separate local ODE theorem
must then produce integral curves on an interval local to each initial point.
No uniform radius and no global flow/completeness may occur in the target.  A
final geometric mapping theorem must connect the constructed `U` with the
original prescribed `(Z,H)`; it is part of G01-B's source conclusion and not a
consequence of pointwise normalization alone.

## Available and missing bindings

`CAS-01-C04` is reusable only for the pointwise algebraic normalization
derivative.  It does not establish an open timelike neighbourhood, smoothness
of the square-root denominator, a Lorentzian chart, or local flow existence.

Pinned mathlib has no already-bound project interface identifying a general
smooth Lorentzian metric, its Levi-Civita connection, normal coordinates,
time orientation, and local flow with the concrete formula above.  A proof
packet must therefore either implement that geometry or state a transparent
conditional local-coordinate lemma.  The latter is not G01-B completion and
must not be used to promote the source theorem.

## Claim boundary

This recovers the original theorem's source signature and prevents replacing
local existence by a pointwise `g(v,v)<0` assertion.  It performs no Lean
compilation, no four-axis replay, and no scientific admission.
