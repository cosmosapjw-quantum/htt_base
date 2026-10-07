# CAS-07 M04 SageMath + Singular axis: Jacobi matrix majorant

## Physics/math audit verdict

The four M04 statements follow for arbitrary continuous real linear maps on the
two-dimensional Euclidean screen under the exact admitted derivative and Jacobi
premises. This is an analytic matrix component only. Its scientific admission is
`HOLD`; no determinant, sign, distance, geometry, or observational claim follows.

## Assumptions and conventions

Let `E=R^2` with its standard positive Euclidean norm and let
`B=L(E,E)`. All operator norms below are induced Euclidean norms. `B` is a
finite-dimensional Banach space, with identity `I` satisfying `||I||op=1`.
`L>0`, `K>=0`; `0<=s<=L`. The admitted `D,D1,D2,R` have the regularity in
`ADMITTED_INPUTS.json`, `D(0)=0`, `D1(0)=I`, `D2=-R∘D`, and `||R||op<=K`.
The sign in the Jacobi equation is minus. `K` has dimension `L^-2`, `D` and
`s` dimension `L`, and `R` dimension `L^-2`. The supplied screen setting does
not require symmetry, commutation, a Lorentz norm, or any optical sign premise.

## Exact Volterra identity

Choose an orthonormal basis of `E`. Every matrix entry `d_ij` has two
derivatives and continuous second derivative. Apply the accepted M02 scalar
integral Taylor formula to each entry:

`d_ij(s)=d_ij(0)+s d1_ij(0)+∫_0^s (s-t)d2_ij(t)dt`.

The four entrywise identities combine to a Bochner identity in `B`, because
integration in a finite-dimensional normed space is coordinatewise and is
basis-independent. Substitute the initial data and `D2(t)=-R(t)∘D(t)`:

`D(s)=s I-∫_0^s (s-t)(R(t)∘D(t))dt`.

Composition order is fixed by the Jacobi premise. No inverse of `D` is used
in the universal argument. The Sage and Singular scripts also check a distinct
exact manufactured example with noncommuting coefficient matrices; that example
is a diagnostic, not the universal proof.

## Scalar premise and comparison

Set `u(s)=||D(s)||op`. Continuity of `D` and continuity of the norm give
continuous, nonnegative `u`. On `0<=t<=s`, the kernel `s-t` is nonnegative.
The Banach integral norm inequality, triangle inequality, operator norm
submultiplicativity, and `||I||op=1` yield

`u(s)<=s+∫_0^s(s-t)||R(t)∘D(t)||op dt`
`    <=s+K∫_0^s(s-t)u(t)dt`.

This establishes the M03 premise rather than assuming it. For completeness,
define positive `Tv(s)=K∫_0^s(s-t)v(t)dt` on continuous nonnegative functions.
Iterating the premise gives

`u <= Σ_(j=0)^(n-1) T^j(s) + T^n u`.

Direct integration of monomials gives
`T(t^m)(s)=K s^(m+2)/((m+1)(m+2))` for every integer `m>=0`; hence
`T^j(s)=K^j s^(2j+1)/(2j+1)!`. With `M=max_[0,L] u`, positivity also gives
`0<=T^n u(s)<=M K^n s^(2n)/(2n)!`. This remainder tends uniformly to zero
on `[0,L]`, including when `K=0`. Consequently

`u(s)<=Σ_(j>=0) K^j s^(2j+1)/(2j+1)! = f_K(s)`.

The sum is `s` for `K=0`, and `sinh(sqrt(K)s)/sqrt(K)` for `K>0`. Thus
`||D(s)||op<=f_K(s)` over the entire declared real domain. This also gives
the accepted M03 comparison without a finite-truncation inference.

## Departure from the flat-screen map

Subtract `s I` from the exact Volterra identity and take the same induced
operator norm. Using the proved `u(t)<=f_K(t)`, positivity of the kernel, and
`||R||op<=K` gives

`||D(s)-sI||op<=K∫_0^s(s-t)f_K(t)dt`.

For `K>0`, `f_K''=K f_K`, `f_K(0)=0`, and `f_K'(0)=1`; applying the scalar
integral Taylor formula gives the exact identity
`K∫_0^s(s-t)f_K(t)dt=f_K(s)-s`. For `K=0`, both sides are zero because
`f_0(s)=s`. Therefore `||D(s)-sI||op<=f_K(s)-s`.

At `s=0`, `D(0)=0=f_K(0)` makes all four identities and inequalities exact.
At `K=0`, `||R(t)||op<=0` implies `R(t)=0`, so `D2=0` and the Volterra
identity gives `D(s)=sI`. Constant `R=-K I` attains `D(s)=f_K(s)I`, showing
the growth bound is sharp for `K>0`; it is a control case, not an extra
symmetry premise.

## Executable evidence and limits

`run.py` invokes actual SageMath 10.9 and the contract-pinned Singular
4.4.1/44100 binary. Sage checks exact 2x2 component integration and the
scalar differential identity; Singular checks a generic noncommuting
polynomial matrix composition identity and weighted kernel identities. These
checks support the algebraic steps. The universal norm and convergence proof
is the written argument above; finite algebra alone could not establish it.

No domain or assumption differs from the frozen contract. The component's
claim ceiling remains `matrix_majorization_only_no_determinant_or_science`.
