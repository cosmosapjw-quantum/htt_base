# PR-269 Pillar T analytic/core proof artifacts

Status: proof-author artifacts awaiting an independent frozen-candidate review.

Scope: typed mathematical and mathematical-physics statements under the exact
premises below. These records have a `diagnostic_only` claim ceiling. They do
not change observational status, validate a transfer path, supply a native
solver result, or identify a geometry family. The PR-268 registry and its
source-status fields remain unchanged.

The source titles are registration identities. Whenever this document adds the
premises needed to make a title mathematically decidable, the machine record
uses `TYPED_ELABORATION_WITH_EXPLICIT_PREMISES`; it does not pretend that prose
already contained a typed signature. The executable checks cited below are
boundary and implementation evidence. The derivations in this document are
the proof artifacts.

## Verdict and convention contract

- `PROVED_ANALYTIC` is the proof author's verdict for an exact typed statement.
- `PROVED_CONDITIONAL_ANALYTIC` proves an implication under listed physical or
  structural premises; it does not establish those premises for data.
- `RESTRICTED_WITNESS_CONFIRMED` applies only to the named finite witness.
- `REFERENCE_RESOLVED_NOT_READJUDICATED` preserves an already typed frozen
  source reference without claiming a new proof.
- `INCONCLUSIVE_MISSING_SIGNATURE` is mandatory when the legacy source lacks a
  typed assumption/domain/frame signature.
- A downstream proof atlas may render an accepted status only when canonical
  PR-269 status is `completed` and the frozen independent-review receipt is
  resolvable.

All spatial contractions below use one positive-definite spatial metric. The
registered STF5 ordering is
`(Sxx, Syy, Sxy, Sxz, Syz)`, with `Szz = -Sxx-Syy`; its five-coordinate
Euclidean norm is not the Frobenius norm of the tensor.

## PR269-VT-T1

### Typed statement

Let `Theta = 3H` with `H > 0`. Let `sigma_ab` be spatial, symmetric and
trace-free. Let the spatial antisymmetric vorticity two-form and its axial dual
satisfy

```text
omega_ab omega^ab = 2 omega_a omega^a.
```

Then the repository conventions obey

```text
Sigma2
  = sigma_ab sigma^ab / (6 H^2)
  = (3/2) ||sigma/Theta||_F^2,

W2
  = omega_ab omega^ab / (6 H^2)
  = omega_a omega^a / (3 H^2)
  = 3 ||omega/Theta||_2^2.
```

### Proof

Substitute `H = Theta/3` in the shear definition:

```text
sigma_ab sigma^ab / (6 H^2)
  = sigma_ab sigma^ab / (6 Theta^2/9)
  = (3/2) (sigma_ab/Theta)(sigma^ab/Theta).
```

For vorticity, first substitute the three-dimensional dual identity:

```text
omega_ab omega^ab / (6 H^2)
  = 2 omega_a omega^a / (6 H^2)
  = omega_a omega^a / (3 H^2).
```

Using `H = Theta/3` once more gives
`omega_a omega^a/(3H^2) = 3 omega_a omega^a/Theta^2`.
No coordinate-basis norm is substituted for either contraction.

### Boundary

The conversion is unavailable at `H = 0`, under a non-spatial/non-STF shear
input, or if the vorticity vector is assigned polar rather than axial dual
semantics. These are refused inputs, not alternative branches.

## PR269-VT-T2

### Typed statement

Let `g` be invertible and linear. Let every `A(y)` be a nonempty closed convex
absorbing body containing zero, and suppose `A(g y) = g A(y)`. Then

```text
p_{A(g y)}(g k) = p_{A(y)}(k).
```

### Proof

By definition,

```text
p_{gA}(gk) = inf {lambda > 0 : gk in lambda gA}.
```

Linearity gives `lambda gA = g(lambda A)`, and invertibility gives
`gk in g(lambda A)` exactly when `k in lambda A`. The two infimum sets are
therefore equal. Absorption supplies finite gauges on the declared domain.

### Boundary

For a singular `g`, membership in the image need not pull back uniquely. If
the body action is not equivariant, the left-hand body is not `gA`; if the
body is not absorbing, one or both gauges may be infinite. The proof asserts
nothing in those cases.

## PR269-VT-T3

### Typed statement

Let `A` be closed, convex, balanced, absorbing, and contain zero in a
finite-dimensional real vector space. Define its absolute polar by

```text
A_polar = {phi : |phi(a)| <= 1 for every a in A}.
```

Then

```text
p_A(k) = sup_{phi in A_polar} |phi(k)|.
```

### Proof

If `k in lambda A`, polar membership gives
`|phi(k)| <= lambda` for every `phi in A_polar`; taking first the supremum in
`phi` and then the infimum in admissible `lambda` proves the `<=` direction.

For the reverse direction, the closed convex balanced body equals its bipolar
in finite dimension. If `t < p_A(k)`, then `k` is not in `tA`. Strong
separation supplies a linear functional `phi` with
`sup_{a in A}|phi(a)| <= 1` and `|phi(k)| > t`. Thus `phi` is in `A_polar`.
Letting `t` increase to `p_A(k)` proves the reverse inequality.

### Boundary

Balance is essential for the absolute-polar form. A one-sided polar can treat
a non-balanced body, but that is a different statement. Closure and absorption
also cannot be silently removed.

## PR269-VT-T4

### Typed statement

Under VT-T3, type a directional stress as
`x_phi := |phi(k)|` for `phi in A_polar`. Then

```text
x_phi <= p_A(k).
```

Each admissible directional value is therefore a certified lower bound on the
global anchor stress; it is neither an equality nor a posterior quantity.

### Proof

VT-T3 identifies `p_A(k)` with the supremum of the set containing
`|phi(k)|`. Every member of a set is bounded above by its supremum.

### Boundary

The inequality does not apply to a functional outside the polar body. A signed
`phi(k)` cannot be silently relabelled as the nonnegative `x_phi`, and a
directional value cannot be promoted to the global equality without attaining
the supremum.

## PR269-VT-T9

### Typed statement

For `R in O(3)`, a polar vector transforms as `v' = Rv`, while an axial vector
transforms as `w' = det(R) Rw`. Consequently,

```text
v'.v' = v.v,
w'.w' = w.w,
v'.w' = det(R) v.w.
```

Polar-polar and axial-axial contractions are scalars; polar-axial contractions
are pseudoscalars. Proper rotations preserve all three, while a reflection
flips only the pseudoscalar.

### Proof

Orthogonality gives `R^T R = I`, and `det(R)^2 = 1`. Substitution yields the
three displayed laws directly. More generally, retaining the determinant
factor on every axial slot types any contraction before it is evaluated.

### Boundary

Erasing polar/axial types makes the reflection law undecidable. An improper
orthogonal matrix is not a member of `SO(3)` and cannot be handled by silently
forcing its determinant to `+1`.

## PR269-VT-T10

### Typed statement

Let `A` be group invariant and let `k != 0` have finite strictly positive gauge
`r = p_A(k)`. Define `u = k/r`. Then

```text
k = r u,       p_A(u) = 1,
```

and this positive-amplitude normalized factorization is unique. The group
orbit `[u]` is the normalized orbit shape, while `r` is invariant.

### Proof

Positive one-homogeneity of the gauge gives
`p_A(k/r) = p_A(k)/r = 1`. If `k = r' u'` with `r' > 0` and `p_A(u') = 1`,
then `p_A(k) = r'`; hence `r' = r` and `u' = k/r = u`.

If the body is group invariant, VT-T2 with `A(gy)=A(y)=A` gives
`p_A(gk)=p_A(k)`. Therefore the action changes only the representative of the
normalized orbit.

### Boundary

The zero state has no unique normalized direction. A gauge with nontrivial
null directions can assign zero amplitude to a nonzero state. Without group
invariance the normalization still exists, but its amplitude is not an orbit
invariant.

## PR269-TF-01-PARITY-TYPING

For the Krylov matrix `K(S,v) = [v, Sv, S^2v]`, an axial input transforms every
column by `det(R) R`. Hence

```text
det K(RSR^T, det(R)Rv)
  = det(R)^3 det(R) det K(S,v)
  = det(R)^4 det K(S,v)
  = det K(S,v).
```

The axial Krylov determinant is an `O(3)` scalar. For a polar input there is no
determinant factor on the columns, so stacking by `R` contributes one
`det(R)` and the determinant is a pseudoscalar. This is an exact parity
calculation; the oracle transform vectors are regression evidence only.

## PR269-TF-02-CATALOGUE-COMPLETION

This verdict is restricted to the registered witness:

```text
S = diag(1, 2, -3),  beta = 0,  omega = (1, 2, 3).
```

The v2 catalogue is even under `omega -> -omega` at this witness. The axial
Krylov determinant has three columns linear in `omega`, so it reverses sign.
Because `S` has three distinct eigenvalues, its orientation-preserving
orthogonal stabilizer consists of diagonal sign matrices with sign product
`+1`, the Klein four group. Mapping `omega` to `-omega` would require all three
signs to be `-1`, whose product is `-1`; no stabilizer element does so.

Thus the two witness states occupy distinct `SO(3)` orbits and the typed
Krylov sign separates this witness. Generic orbit separation and invariant
ring completeness remain `UNPROVEN`.

## PR269-TF-07-BUDGET-MORPHOLOGY-SPLIT

Assume the budget has the declared factorization

```text
B(z) = b(I1(z), I2(z), I3(z), I4(z)),
```

where the four named invariants are `tr_sigma2`, `omega2`, `beta2`, and
`delta_omega_k`. If a tangent `h` annihilates every `dIj`, the chain rule gives

```text
dB_z[h] = sum_j (partial_j b) dIj_z[h] = 0.
```

On a connected component of a common fibre, the same derivative calculation
along any differentiable path shows that the budget is constant. This proves
only the named factorization consequence. It does not claim that these four
objects generate an invariant ring or that higher even powers vanish.

## PR269-TF-08-PRODUCT-GAUGE-MAX

Let `A = product_j A_j`, where every `A_j` is a nonempty centered closed norm
ball with finite strictly positive radius, and let `p_j` be its sector gauge.
For `x = (x_j)`,

```text
x in lambda A
  iff every x_j is in lambda A_j
  iff lambda >= p_j(x_j) for every j
  iff lambda >= max_j p_j(x_j).
```

Taking the infimum over positive `lambda` proves
`p_A(x) = max_j p_j(x_j)`. Consequently the declared exceedance is
`max(p_A(x)-1, 0)`. A coupled non-product anchor or a nonpositive radius is
outside this statement.

## PR269-TF-12-ACCELERATION-EULER-SLAVING

Assume a perfect fluid with no frame heat flux or anisotropic stress, a
barotropic pressure law, `mu > 0`, and `mu+p != 0`. The spatial momentum
equation is

```text
(mu+p) A_a = -D_a p.
```

With `p = w mu` at the evaluated state and
`D_a p = cs2 D_a mu`, division by `mu(1+w)Theta` gives

```text
A_a/Theta = -[cs2/(1+w)] D_a ln(mu)/Theta.
```

If `eps_g` is the exact norm `||D ln(mu)/Theta||`, the repository acceleration
normalization gives the shape

```text
A2_std = (3/2)[cs2/(1+w)]^2 eps_g^2.
```

If the explicitly supplied `eps_g` is instead only an upper bound on that
norm, the corresponding relation is

```text
A2_std <= (3/2)[cs2/(1+w)]^2 eps_g^2.
```

No repository input currently gives this proof an absolute numerical
`eps_g` authority. The executable function therefore requires an explicit
value, labels the result conditional, and always returns
`numerical_ceiling_authorized = false`. The formula is refused at `mu <= 0`,
`w = -1`, or when the perfect-fluid premises fail.

## Legacy source resolution

PR-269 inventories every legacy Pillar-T row exactly once. The following seven
rows already have declared assumptions, domain, frame, and perturbative order
in the frozen source. PR-269 resolves those references without readjudicating
their proofs:

<a id="pr269-legacy-sig-p3"></a>
<a id="pr269-legacy-sig-p11"></a>
<a id="pr269-legacy-sig-mes-prov"></a>
<a id="pr269-legacy-sig-tsum"></a>
<a id="pr269-legacy-sig-mes-br"></a>
<a id="pr269-legacy-sig-mes-refreeze"></a>
<a id="pr269-legacy-sig-mes-mesb-trace"></a>

```text
SIG-P3
SIG-P11
SIG-MES-PROV
SIG-TSUM
SIG-MES-BR
SIG-MES-REFREEZE
SIG-MES-MESB-TRACE
```

The remaining legacy Pillar-T rows lack the required typed signature and
therefore remain `INCONCLUSIVE_MISSING_SIGNATURE`:

<a id="pr269-legacy-sig-p4"></a>
<a id="pr269-legacy-sig-p5"></a>
<a id="pr269-legacy-sig-p6"></a>
<a id="pr269-legacy-sig-p7"></a>
<a id="pr269-legacy-sig-p9"></a>
<a id="pr269-legacy-sig-p12"></a>
<a id="pr269-legacy-sig-p13"></a>
<a id="pr269-legacy-sig-p14"></a>
<a id="pr269-legacy-sig-p15"></a>
<a id="pr269-legacy-sig-p21"></a>
<a id="pr269-legacy-sig-p22"></a>
<a id="pr269-legacy-sig-p27"></a>
<a id="pr269-legacy-sig-p32"></a>
<a id="pr269-legacy-sig-t3-lin"></a>
<a id="pr269-legacy-sig-t3-full"></a>
<a id="pr269-legacy-sig-t3-int"></a>
<a id="pr269-legacy-sig-t9p"></a>
<a id="pr269-legacy-sig-u1"></a>
<a id="pr269-legacy-sig-u2"></a>
<a id="pr269-legacy-sig-bv-dyn"></a>
<a id="pr269-legacy-sig-ke-frame"></a>
<a id="pr269-legacy-sig-ke-obs"></a>
<a id="pr269-legacy-sig-ke-dyn"></a>
<a id="pr269-legacy-sig-omk-reopen"></a>

```text
SIG-P4, SIG-P5, SIG-P6, SIG-P7, SIG-P9, SIG-P12,
SIG-P13, SIG-P14, SIG-P15, SIG-P21, SIG-P22, SIG-P27,
SIG-P32, SIG-T3-lin, SIG-T3-full, SIG-T3-int, SIG-T9p,
SIG-U1, SIG-U2, SIG-BV-DYN, SIG-KE-FRAME, SIG-KE-OBS,
SIG-KE-DYN, SIG-OMK-REOPEN
```

A `CHECKED` label in the frozen source is provenance; it is not transformed
into a new PR-269 verdict. Conversely, missing source typing is not repaired by
inferring premises from a title.

## Why no four-axis CAS appears here

The selected statements use definition expansion, finite-dimensional convex
duality, determinant parity, the chain rule, or a typed fluid momentum
identity. Adding a computation gate would not address a distinct failure
class. Orbit reconstruction, Cayley-Hamilton/Krylov syzygies, realizability,
and conditional response statements remain routed to PR-270, where the
registered four-axis contract applies.

## Reproduction

```bash
python -B scripts/codex_harness/build_pr269_pillar_t_core.py --check
PYTHONPATH=htt/src:htt python -B -m pytest -p no:cacheprovider -q \
  tests/contracts/test_pillar_t_core.py
```
