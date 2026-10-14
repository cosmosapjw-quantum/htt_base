# CAS-07 M04: 2D Jacobi Volterra identity and induced-norm majorant

## Physics/math audit verdict

The four M04 statements follow under exactly the admitted derivative/Jacobi and
Euclidean operator-norm hypotheses. This is a matrix-majorization component only;
scientific admission remains `HOLD`. No determinant, singular-value, conjugate-point,
physical screen-transport existence, or Bianchi-family conclusion follows here.

## Assumptions and conventions

Let `E=R^2` with its standard Euclidean norm and let `B=L(E,E)`, a
four-dimensional Banach space with induced operator norm. Work on `0<=s<=L`,
`L>0`, `K>=0`. The maps `D,D1,D2,R : [0,L] -> B` obey the exact regularity,
initial data, Jacobi equation `D2(t)=-R(t)∘D(t)`, and `||R(t)||op<=K` in
`ADMITTED_INPUTS.json`. Derivatives at endpoints are understood one-sided.
`D` and `f_K` have length units, `R` and `K` inverse-length-squared units,
`D1` is dimensionless, and `D2` inverse-length. The signature/frame conventions
in `COMMON_SPEC.md` do not enter this Euclidean screen-map assertion. No
symmetry or commutation is imposed.

The only accepted external mathematical statements are the literal M02
componentwise integral Taylor formula and the literal M03 universal scalar
Volterra comparison, as quoted in `ADMITTED_INPUTS.json`. The arguments below
show why their hypotheses hold in this particular matrix problem.

## 1. Componentwise Volterra identity

Choose the standard orthonormal basis of `E`. Every entry `d_ij` of `D` has
the supplied two derivatives, and its second derivative is continuous. M02
applies to each of the four real components:

`d_ij(s)=d_ij(0)+s*d'_ij(0)+∫_0^s (s-t)*d''_ij(t)dt`.

For clarity, this is also verified directly: for
`H_ij(s)=∫_0^s (s-t)d''_ij(t)dt`, continuity permits Leibniz differentiation,
giving `H_ij(0)=H'_ij(0)=0` and `H''_ij(s)=d''_ij(s)` in the interior, with
continuous endpoint limits. Thus `d_ij-d_ij(0)-s*d'_ij(0)-H_ij` is affine
with zero value and derivative at zero. The four entry identities reconstruct
the equality in `B`, since integration in finite-dimensional `B` is entrywise.

The initial data yield `D(0)=0`, `D1(0)=Id`. In entries, the supplied Jacobi
equation is `d''_ij(t)=-Σ_{h=1}^2 r_ih(t)d_hj(t)`, exactly the `(i,j)` entry
of `-R(t)∘D(t)`. Substitution gives

`D(s)=s*Id-∫_0^s(s-t)*(R(t)∘D(t))dt`.

The integrand is continuous and hence Bochner integrable. The order `R∘D` is
retained throughout. `run.py` uses four arbitrary component functions to
check the Taylor derivative certificate and symbolic matrix multiplication;
it also confirms that generic `R D-D R` is nonzero.

## 2. Scalar premise with the induced operator norm

Set `u(s)=||D(s)||op`. Continuity of `D` and the reverse triangle inequality
give continuity of `u`; by definition `u>=0`. The identity map has induced
Euclidean operator norm one, so `||s*Id||op=s` for `s>=0`. For any continuous
`B`-valued integrand, the Bochner integral inequality holds in this norm.
Triangle inequality and nonnegative kernel `s-t` therefore give

`u(s)<=s+∫_0^s(s-t)||R(t)∘D(t)||op dt`.

For each `t`, the induced operator norm is submultiplicative:
`||R(t)∘D(t)||op<=||R(t)||op ||D(t)||op<=K*u(t)`. This follows directly by
applying both maps to any vector `v` with `||v||=1` and taking the supremum;
it neither replaces the norm by Frobenius norm nor requires a symmetric map.
Consequently

`u(s)<=s+K∫_0^s(s-t)u(t)dt`.

This is precisely M03's continuous nonnegative scalar premise on `[0,L]`.

## 3. Norm of D

Apply the accepted universal M03 comparison to that premise:
`u(s)<=f_K(s)`. Here `f_0(s)=s` and, when `K>0`,
`f_K(s)=sinh(sqrt(K)*s)/sqrt(K)`. The comparison applies to every continuous
`u` satisfying the premise, not merely to a sample or a finite Volterra
iteration. For an independent exact check of the comparison function, set
`k=sqrt(K)>0`. SymPy evaluates

`s+k^2*∫_0^s(s-t)*sinh(k*t)/k dt - sinh(k*s)/k = 0`.

Thus `f_K=s+K∫(s-t)f_K`, including the separate `K=0` identity. This check
does not replace M03's universal comparison proof.

## 4. Norm of D minus s Id

Take the induced norm of the integral remainder in section 1. The same
Bochner and composition inequalities, now followed by section 3, give

`||D(s)-s*Id||op <= K∫_0^s(s-t)u(t)dt`
`                         <= K∫_0^s(s-t)f_K(t)dt = f_K(s)-s`.

The last equality is the exact integral identity above. All quantities are
nonnegative on the admitted domain. At `s=0`, both bounds read `0<=0`.
When `K=0`, `||R(t)||op<=0` forces `R(t)=0` for every `t`; the Volterra
identity then gives the stronger exact `D(s)=s*Id`, and both bounds are
equalities. Constant `R=-K*Id` gives `D=f_K*Id`, an equality-growth control,
but is not used to prove the universal inequalities.

## Dimensional/sign/limit checks

The kernel `(s-t)R(t)D(t)dt` has length units. The Jacobi minus sign is kept in
the matrix identity; norm bounds erase that sign. The majorant is finite for
every finite `s` and `K>=0`; `f_K(0)=0`, and its `K->0+` limit is `s`.
There is no Lorentz or indefinite norm in the inequalities. No determinant
estimate follows merely from an upper bound on `||D||op`.

## Claim-tier implications

The four exact M04 obligations may be marked component `PASS` if the frozen
hash and executable checks pass. The full CAS aggregate still requires the
other blind axes and adjudication under the same contract. Scientific
admission is `HOLD`.
