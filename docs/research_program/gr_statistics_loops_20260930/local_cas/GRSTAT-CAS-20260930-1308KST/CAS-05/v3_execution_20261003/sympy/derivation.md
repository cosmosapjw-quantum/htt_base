# Independent SymPy finite-component derivation

Input identities are the exact v3 execution contract, `NEUTRAL_INPUT.json`, and
`COMMON_SPEC.md` recorded in `result.json`. The current calculation covers only
CAS-05-C01, C02 and C03. The Python source computes the statements on every run;
this note explains how those computations align with the frozen target.

## C01: conformal curvature and origin frame

Use coordinates `(t,x,y,z)` with `t=x0=c*time` and
`eta=diag(-1,1,1,1)`. Set
`phi=-b*t²-b*(x²+y²+z²)/2+lambda*t²*x/2` and `g=exp(2phi) eta`.
`axis.py` constructs the diagonal metric and its inverse, then evaluates
Christoffel symbols, Ricci tensor, scalar curvature and Einstein tensor using
the declared commutator convention. Simplification of all ten symmetric
components against the independently stated target gives zero residual:

`G_ab=-2 phi_ab+2 phi_a phi_b+2 eta_ab Box_eta(phi)+eta_ab (dphi)^2_eta`.

At the origin `phi=0`, `dphi=0`, `g=eta` and `dg=0`. The computed Einstein
tensor is `diag(6b,0,0,0)`. With Einstein-defined stress
`T=(G+Lambda*g)/kappa`, the future rest vector is `u=(1,0,0,0)`,
`epsilon=(6b-Lambda)/kappa`, each `p_i=Lambda/kappa`, and the finite eigenvalue
gap is `epsilon+p_i=6b/kappa>0` under `b,kappa>0`.

Differentiate `T^a_b u^b=-epsilon u^a` at the origin. The spatial equations
give `(epsilon+p_i) partial_mu u^i=-partial_mu T^i_0`; differentiation of
`g(u,u)=-1` gives `partial_mu u^0=0` because `dg(0)=0`. Direct metric-curvature
derivatives yield `partial_t T^1_0=-2lambda/kappa` and all other
`partial_mu T^i_0=0`. Thus `partial_t u^1=lambda/(3b)` and every other
finite `partial_mu u^i` is zero. The origin Christoffel symbols vanish, so
for `U=c u` the spatial physical acceleration is
`A^1=c² lambda/(3b)`, `A^2=A^3=0`. The script evaluates all differentiated
eigenvector and normalization residuals symbolically. It does not construct a
smooth eigenfield.

The same derivative calculation gives `partial_x epsilon=0` and
`partial_x p_2=-2lambda/kappa`. For `lambda != 0`, this is the finite
`EF-NOT-EOS` witness: these values cannot arise from a single differentiable
barotropic `p_2(epsilon)` at the origin. No EOS is assumed.

## C02: finite ray frame contraction

On `t=y=z=0, x=s`, take `E_a=exp(-phi) partial_a`. The `Lambda*g` terms
cancel in `kappa[T(E0,E0)+T(E2,E2)]`, leaving
`exp(-2phi)(G_00+G_22)`. Metric curvature gives
`G_00+G_22=6b-2lambda*s`, while `phi=-b*s²/2`. The exact result is
`exp(b*s²)(6b-2lambda*s)`. At `lambda=0` it is positive for all finite
real `s`. If `lambda != 0`, it vanishes at `s=3b/lambda`; this is the
contracted loss of the strict positive gap on that ray. The calculation is a
frame contraction, without an away-from-origin eigenfield claim.

## C03: finite metric 3-jet

Let `q_i=-6b*k_0i`, `M_ij=-6b*k_ji`, `S=(M+M.T)/2`, and
`W=(M-M.T)/2` for arbitrary real twelve `k` entries. Define the full
symmetric `H` by `H_00=0`, `H_ij=-delta_ij*t*S_kl*x^k*x^l/2`, and
`H_0i=H_i0=-t*r²*q_i/2-r²*W_ij*x^j/5`. The script constructs all 16
entries, explicitly checks every component and derivative through order two
vanishes at the origin, and builds the representative
`g^J=eta+2phi0*eta+H`. The exact conformal baseline and this representative
have identical metric derivatives through order three at the origin because
`exp(2phi0)-1-2phi0` starts at coordinate order four.

For this representative, `g(0)=eta` and `dg(0)=0`. Differentiating the
Christoffel definition directly gives `dGamma(0)` from `d²g(0)` and
`d²Gamma(0)` from `d³g(0)`. Since `Gamma(0)=0`, the product terms in Ricci
and its first derivative vanish there. The script contracts these arrays to
compute `G(0)` and all 40 first coefficients for the ten symmetric Einstein
components; it performs the same calculation for the baseline and subtracts.
The exact full tables and twelve full basis images are stored in the execution
payload. In particular, the twelve `delta G_0i` coefficients are
`delta(d_mu G_0i)=q_i` for `mu=0`, and `M_i,mu` for spatial `mu`.

The finite right inverse is constructive: given any real `k_mu_i`, use the
`q,M,S,W,H` formulas above. Symbolic residuals check every
`-delta(d_mu G_i0)/(6b)-k_mu_i=0`; division uses `b>0`. At the origin the
stress gap remains `6b/kappa`, and these residuals are precisely the
differentiated spatial eigenvector equations, so the induced finite vector jet
has `partial_mu u_i=k_mu_i`. The script also evaluates all twelve basis
specializations and the four differentiated Bianchi contractions
`sum_a eta^aa partial_a G_ab(0)=0`. Because `dg(0)=0`, these are the four
equivalent origin stress-divergence constraints.

The calculation does not establish nonlinear `delta G` away from the origin,
a Lorentzian/strict-DEC neighborhood, a smooth isolated eigenframe via IFT,
or any radius uniform in the member parameters. Those analytic obligations
remain outside this finite component and outside scientific admission.
