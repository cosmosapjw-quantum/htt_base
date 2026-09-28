# Wolfram exact-check ledger

## W1 — Screen SO(2)
For a 2x2 STF tensor G and rotation R(psi):
G' = R G R^T.
Exact:
Tr(G'^2)-Tr(G^2)=0,
det G'-det G=0.
Components rotate with 2 psi.

## W2 — Affine scaling
For k->c k at both endpoints:
(c u_s·k_s)/(c u_o·k_o) - (u_s·k_s)/(u_o·k_o)=0.

## W3 — Spatial representation rotation
Transform A,n,sigma by the same orthogonal R.
Exact:
[theta/3-A'·n'+n' sigma' n'] -
[theta/3-A·n+n sigma n] = 0.

## W4 — Observer boost
A Lorentz boost changes measured photon energy and direction by Doppler/aberration while
the null norm remains exactly zero.
Therefore observer change is physical, not representation gauge.

## W5 — Jacobi map
Independent SO(2) source/observer screen-basis rotations preserve det J.
Same-basis orthogonal rotation preserves Frobenius norm.

## W6 — Metric-aware practical rank
Nonorthogonal state reparameterization changes ordinary Gram matrix and Euclidean singular
values.
Using the transformed state metric, generalized eigenvalues are exactly preserved in the toy
example {1, eps^2}.

## W7 — Räsänen/Heinesen adapter
With n=-e:
Räsänen sky derivative = A·n - sigma:nn - theta/3.
Heinesen H(n)=theta/3-A·n+sigma:nn.
Exact sum =0.

## W8 — Generic/specialized hierarchy sign conflict
After the published positive brightness normalization:
generic T9 sign -> -8 rho sigma/15,
specialized quadrupole equation -> +8 rho sigma/15.
Exact difference =16 rho sigma/15.

## W9 — First-principles energy-integration sign
For a decaying test spectrum f_0=e^{-E},

[∫ E^4 f_0'(E)dE]/[∫E^3f_0(E)dE] = -4,
boundary term E^4 f_0 |0^∞=0.

This matches the exact integration-by-parts identity under physical boundary conditions and
supports dot Pi_ab=-4 sigma_ab Pi_0 in the isolated shear-source limit.
