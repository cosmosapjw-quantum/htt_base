# CAS-07 M05: SymPy axis

The frozen contract is `24e3ae1e11d2a75335cd7fac436e8d1656100dc7877672d08464a4612a19348e`; the admitted input hash is `22fbf2a3fcc428d25f8e9fb0d6e1866c8057ebc7e76dd4ad248bd144300a5a75`. This proof uses the literal accepted M01, M04, and C02 statements in `ADMITTED_INPUTS.json` as interfaces. It does not inspect their proofs or any sibling axis.

Let `K>=0`, `L>0`, and `0<s<=L`, with `eta_K(L)<1`; retain exactly the Jacobi premises admitted by M04. The screen is Euclidean `R^2`, `D(s)` is an arbitrary real linear map, and its norm is the induced Euclidean operator norm. No symmetry, normality, positivity, diagonalizability, or commutation property of `D` is assumed.

1. **CAS-07-M05-REWRITE.** Since `s>0`, the definition `eta_K(s)=f_K(s)/s-1` gives the exact identity `s eta_K(s)=f_K(s)-s`. SymPy simplifies this identity to zero on both definition branches: `f_0(s)=s` and `f_K(s)=sinh(sqrt(K)s)/sqrt(K)` for `K>0`. No series, numerical tolerance, or branch continuation is involved.
2. **CAS-07-M05-C02-PREMISE.** Accepted M01 yields `0<=eta_K(s)<=eta_K(L)<1`. In particular, `eta_K(s)<1`; if `u=1-eta_K(L)>0` and `v=eta_K(L)-eta_K(s)>=0`, then `1-eta_K(s)=u+v>0`. Accepted M04 gives `||D(s)-s Id||op<=f_K(s)-s`; the exact rewrite replaces its right side by `s eta_K(s)`. Together with `s>0`, these are precisely the scalar and norm premises of accepted C02.
3. **CAS-07-M05-DETERMINANT-SIGN.** Apply accepted C02 to this same arbitrary real `2x2` map `D(s)`, with `eta=eta_K(s)`. C02 supplies `det(D(s))>0`; this determinant sign is a *conclusion* of its application, never an input. The positive real `sqrt(det(D(s)))` is therefore defined.
4. **CAS-07-M05-DISTANCE-BOUND.** C02 supplies `s(1-eta_K(s))<=sqrt(det(D(s)))<=s(1+eta_K(s))` on the positive square-root branch. By the admitted definition this middle term is `dA(s)`. Since `1-eta_K(s)>0`, the lower bound is strictly positive. This is exactly the target distance interval.

At `K=0`, `eta_0(s)=0`; M04 bounds a nonnegative norm above by zero, so `D(s)=s Id`. SymPy confirms `det(s Id)=s^2>0` and `sqrt(s^2)=s` for positive `s`; both interval endpoints equal `s`. The target excludes `s=0` and `eta=1`. This composition establishes only the determinant and distance bridge, with no `t` refinement or full theorem/scientific admission.

`m05_bridge.py` performs the exact branch identities and algebraic domain/endpoint controls with SymPy 1.14.0. Its output is raw computation evidence for the displayed dependency composition; the accepted C02 theorem carries the universal arbitrary nonsymmetric matrix implication.
