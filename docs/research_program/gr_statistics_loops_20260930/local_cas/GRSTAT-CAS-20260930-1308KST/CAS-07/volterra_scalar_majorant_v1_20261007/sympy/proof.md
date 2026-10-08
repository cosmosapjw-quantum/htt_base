# CAS-07 M03 scalar Volterra comparison: SymPy axis proof

Frozen contract SHA-256: `6c840eaffac0744da3d1b2f9c7de3f8b1c45af2d949ba4831b5e90d4ec9a51ae`.
Admitted inputs SHA-256: `bbb0f93dc43ddd3ee96cdee065f8173ccac44007a6908ae66714f25e3214661d`.
Common specification SHA-256: `4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897`.

Let `T[v](x)=K integral_0^x (x-t)v(t)dt` on `[0,L]`, where `L>0` and
`K>=0`. Let `u` be any continuous real function on `[0,L]` with `u>=0`
and `u(x)<=x+T[u](x)` for every `x` in the interval. We prove the target
without assuming it or differentiating `u`.

If `K=0`, `T=0`; the premise directly gives `u(x)<=x=f_0(x)`, including
`x=0`. For the remainder of the proof take `K>0`. The kernel is nonnegative
for `0<=t<=x`, so `v<=w` pointwise implies `T[v]<=T[w]` pointwise. Set
`g(x)=x`. For every integer `N>=1`,

`u(x) <= sum_{j=0}^{N-1} T^j[g](x) + T^N[u](x)`.                (1)

The base `N=1` is the given premise. If (1) holds for `N`, apply the
order-preserving operator `T` to the original premise to obtain
`T^N[u] <= T^N[g]+T^{N+1}[u]` (equivalently, apply `T^N`);
substitution into (1) proves the `N+1` case. All iterates are defined:
the kernel and each preceding iterate are continuous on a compact triangle.
No polynomial restriction is placed on `u`.

SymPy integrates the generic coefficient exactly for an arbitrary nonnegative
integer `n`:

`T[K^n x^(2n+1)/(2n+1)!] = K^(n+1) x^(2n+3)/(2n+3)!`,

`T[K^n x^(2n)/(2n)!] = K^(n+1) x^(2n+2)/(2n+2)!`.

Starting with `g(x)=x` and `1`, induction therefore gives
`T^j[g](x)=K^j x^(2j+1)/(2j+1)!` and
`T^N[1](x)=K^N x^(2N)/(2N)!` for all nonnegative integers `j,N`.
These are exact all-index identities checked in `check.py` by symbolic
integration and simplification.

Continuity of `u` on compact `[0,L]` supplies a finite
`M=max_{[0,L]} u>=0`. By positivity, for every `x in [0,L]`,

`0 <= T^N[u](x) <= M T^N[1](x)
                   = M K^N x^(2N)/(2N)!
                   <= M (K L^2)^N/(2N)!`.                       (2)

For fixed finite `K,L`, the ratio of consecutive terms on the right of (2)
is `K L^2/((2N+2)(2N+1))`, which tends to zero. Thus the right side tends
to zero (also when `M=0`), uniformly in `x`. This proves the remainder
disappears; it is not discarded merely because it is nonnegative.

The partial sums in (1) are nonnegative and bounded termwise by
`L (K L^2)^j/(2j+1)!`. The ratio of consecutive majorant terms is
`K L^2/((2j+3)(2j+2)) -> 0`; hence their series converges. The
Weierstrass M-test gives absolute, uniform convergence on `[0,L]`.
The Taylor series definition of `sinh` (also evaluated exactly by SymPy)
identifies its sum as

`sum_{j=0}^infinity K^j x^(2j+1)/(2j+1)!
 = sinh(sqrt(K)x)/sqrt(K) = f_K(x)`.

Taking `N -> infinity` in (1), using (2) and the convergent series,
gives `u(x)<=f_K(x)` for every `x in [0,L]`. At `x=0` the premise gives
`0<=u(0)<=0`; both branches of `f_K` vanish. The admissible control
`u=0` is included. Equality control `u=f_K` satisfies the premise because
the exact series obeys `f_K=g+T[f_K]`: positivity and uniform convergence
permit termwise integration, or dominated convergence on `[0,L]` does.

The result is confined to the scalar Volterra comparison. Matrix Jacobi
reduction, determinant bounds, and scientific admission remain outside this
axis. The actual native author model and effort were not observed; the
owner-authorized direct continuation has no global launch ID.
