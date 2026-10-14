# CAS-11-C01 finite identity (SageMath + Singular axis)

Let `d=f-h`, `e=h-g`, and write `G_g=grad H(g)`, `G_h=grad H(h)`.
By the admitted definition, direct expansion gives

`D_H(f||g)-D_H(f||h)-D_H(h||g)`
`= -<G_g,d+e>+<G_h,d>+<G_g,e>`
`= <G_h-G_g,d>`.

This is an identity for values and gradients at the named points. It does not
require convexity or a positive Bregman divergence. If `G_h-G_g=V lambda`,
ordinary finite-dimensional Euclidean transpose algebra gives
`<V lambda,d>=<lambda,V^T d>`. Thus exact `V^T d=0` makes the cross term
exactly zero for every finite `n,k`. Sage checks the corresponding polynomial
identity over the rationals in four generated dimensions; Singular separately
checks the polynomial identity and ideal reduction for `n=k=2`.

The orientation control uses `H(x)=x^3/3`, `f=2`, `g=1`: forward divergence
is `4/3` and reverse is `5/3`. The approximate matching control has
`V=lambda=1`, `f-h=1/10`; its cross term remains `1/10`. These controls
check conventions and guard against promoting approximate equality to exact
cancellation. This finite component says nothing about integrability,
continuum entropy bounds, or science.
