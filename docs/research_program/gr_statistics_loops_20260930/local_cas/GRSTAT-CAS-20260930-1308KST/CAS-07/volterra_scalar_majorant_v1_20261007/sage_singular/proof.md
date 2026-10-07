# CAS-07 M03 scalar Volterra comparison

Take the exact real domain of the frozen contract: `K >= 0`, `L > 0`, and an
arbitrary continuous `u : [0,L] -> R` with `0 <= u(x) <= x + T_K[u](x)` at
every point. Here `T_K[v](x) = K integral_0^x (x-t)v(t)dt`. Integrals below are
ordinary Riemann integrals of continuous functions; interchange of iterated
integrals is valid on each compact triangular domain.

If `K=0`, `T_K=0`, so the given inequality directly yields `u(x)<=x=f_0(x)`
at every `x`, including zero. Thus assume `K>0` for the remaining argument.

The operator `T_K` is linear and positive: if `v<=w` pointwise on `[0,L]`,
then `T_K[v]<=T_K[w]`, since `K(x-t)>=0` for `0<=t<=x<=L`. Repeated
substitution from the *given* premise, and induction using positivity, gives
for every integer `N>=1`

    u(x) <= sum_{j=0}^{N-1} T_K^j[id](x) + T_K^N[u](x),

where `id(x)=x`. The base case is the given inequality. Applying `T_K` to
the previous comparison and then adding `id` proves the next case. This uses
no regularity of `u` beyond continuity.

For every continuous `v` and integer `n>=1`, the exact iterated-kernel formula is

    T_K^n[v](x) = K^n/(2n-1)! integral_0^x (x-t)^(2n-1)v(t)dt.

At `n=1` this is the definition. In the induction step, triangle integration
gives the inner kernel convolution

    integral_t^x (x-s)(s-t)^(2n-1) ds
      = (x-t)^(2n+1)/((2n)(2n+1)).

Indeed set `s=t+y(x-t)`, integrate `(1-y)y^(2n-1)` from zero to one, and
obtain `1/(2n)-1/(2n+1)`. The extra Jacobian and factors of `x-t` produce
the displayed power. Multiplying by `1/(2n-1)!` gives `1/(2n+1)!`, proving
the formula for `n+1`. This is valid for `x=t` as both sides vanish. The pinned
Singular executable checks the exact polynomial antiderivative and endpoint
residuals for representative integer instances; this written induction proves
the arbitrary-integer identity.

In particular `T_K^0[id]=id`, and either applying the kernel formula to `id`
or integrating a beta polynomial yields

    T_K^n[id](x)=K^n x^(2n+1)/(2n+1)!  for every n>=0.

For the remainder, compactness and continuity give a finite real bound
`M=max_{[0,L]}u>=0`. Positivity and the kernel formula imply for every
`n>=1`, uniformly in `x in [0,L]`,

    0 <= T_K^n[u](x)
       <= M K^n/(2n-1)! integral_0^x (x-t)^(2n-1)dt
       = M K^n x^(2n)/(2n)! <= M K^n L^(2n)/(2n)!.

The final sequence tends to zero: its successive ratio is
`K L^2/((2n+2)(2n+1))`, which tends to zero. This supplies a uniform,
explicit vanishing bound, including `M=0` and `x=0`. The seed series
`sum_{j>=0}K^j x^(2j+1)/(2j+1)!` converges absolutely and uniformly on
`[0,L]` by comparison with `sum K^j L^(2j+1)/(2j+1)!`; its successive
ratio likewise tends to zero. Taking `N -> infinity` in the finite
comparison therefore yields the pointwise universal inequality

    u(x) <= sum_{j>=0} K^j x^(2j+1)/(2j+1)!
         = sinh(sqrt(K)*x)/sqrt(K) = f_K(x).

The last equality is the defining entire power series for `sinh`; `sqrt(K)`
is its positive real branch. At `x=0`, the original premise also gives
`0<=u(0)<=0`. The `u=0` control satisfies all premises. The equality control
`u=f_K` satisfies `f_K=id+T_K[f_K]` by uniformly convergent termwise
integration of the displayed series, or by shifting its coefficients under
`T_K`; at `K=0`, `f_0=id` satisfies the same equation. Neither control is used
as a premise for arbitrary `u`.

This establishes only the contracted scalar functional comparison. It does
not derive the matrix Jacobi inequality or any scientific conclusion.
