# Direct kinematic likelihood and tensorized five-variable contract

## State, units and representation

Use (-,+,+,+), U.U=-c² and sourceward n. Distinguish the expansion scalar Theta from the parameter tuple theta. Normalize only where a stated H>0 is available:

$$
s_{ab}=\sigma_{ab}/H,\quad w_a=\omega_a/H,\quad
a_a=A_a/(cH),\quad \beta_{XY}=v_{XY}/c.
$$

The state can include all components of (s,w,a,beta), a finite explicitly declared redshift/history basis, physical geometry parameters and calibration variables. x is a typed collection of functions of that state and observations, rather than one scalar x_c. Examples are the full signed STF harmonic coefficients; temperature/polarization matrices; s,w,a,beta components; beta^T s beta; s_ab w^a w^b; a.beta; and the pseudoscalar w.beta. Different units are not added before an explicit metric/normalization is defined.

Under a proper spatial rotation R, s→RsR^T and polar vectors→Rv. Under O(3), axial w→det(R)Rw. A mixed functional must have its parity recorded. Copying a derived functional next to its parent components does not create new independent observations; their joint covariance may be singular by construction.

## General observation map

For a probe p with data D_p, retain the physical transfer T_p, measurement operator M_p, mask/beam/selection and source epoch:

$$
\mu_p(\theta,\psi)=M_p[T_p(\theta,\psi)],\qquad
L(\theta,\psi,\nu\mid D)=p(D\mid\mu(\theta,\psi),C(\theta,\psi,\nu)).
$$

psi contains foreground/calibration, response-history and catalogue nuisance parameters; nu contains covariance-law parameters. All cross-probe covariance must be declared. It cannot be set to zero merely because catalogue names differ. The displayed likelihood conditions on observed z,n when that is the actual experiment; a raw forward model instead includes latent distances/redshifts, selection and measurement errors.

For a Gaussian model, with r=D-mu,

$$
\ln L=-\frac12[r^TC^{-1}r+\ln\det C+n\ln(2\pi)].
$$

If C depends on theta_i, the score is

$$
t_i=\mu_{,i}^TC^{-1}r+
\frac12r^TC^{-1}C_{,i}C^{-1}r-
\frac12\operatorname{tr}(C^{-1}C_{,i}).
$$

The corresponding expected information is
I_ij=mu_,i^TC^-1mu_,j+(1/2)tr(C^-1C_,i C^-1C_,j).
This known linear-plus-quadratic score is needed for anisotropic covariance/boost response. A fixed linear score from one covariance is not globally sufficient for that enlarged problem. See [Alsing & Wandelt](https://arxiv.org/abs/1712.00012v2).

## Implemented CF4 physical pullback

At the current fixed local/constant response,

$$
\alpha=(V_3,d_3,\kappa_5),\qquad
\theta_{\rm ext}=(s_5,w_3,a_3,\beta_{MR,3},d_{{\rm cal},3},q_{{\rm cal},5}),
$$

$$
V=c\beta_{MR},\quad d=-a+d_{\rm cal},\quad
\kappa=s+q_{\rm cal}.
$$

Hence L(theta_ext|y_m)=L_alpha(R theta_ext|y_m) is an implemented and meaningful likelihood for directly named kinematic components. R is rank11 on22 coordinates. The kernel contains w, matched a/calibration shifts and opposite s/calibration shifts. The physical parameter manifold can be further constrained by a chosen source-bound solution; no such field-equation constraint is silently imposed.

For a linear functional ell^T theta_ext to be identified by this likelihood it must annihilate ker R. Locally, a smooth functional phi requires ker J_eff subset ker Dphi. This condition is necessary locally and does not by itself prove global identification for nonlinear multi-branch models.

For example beta^T(s+q_cal)beta is constant along the shear-calibration fibre, whereas beta^T s beta is not. A scalar norm also discards orientation and generally cannot replace the vector/tensor likelihood when the mean response and covariance are directional.

## One confidence object, five dependent views

Let E_m be the confidence ellipsoid/cylinder for the actual fixed-Gaussian experiment; its cutoff dimension matches the stated target, nuisance profile and rank. Define a finite model union E=union_m E_m, and a physical set

$$
\mathcal C_\theta=\{\theta:\exists m,\psi\in\mathcal B,\
R_m(\theta,\psi)\in E_m\}.
$$

This is the common source of the views:

| View | Definition/use | Actual R60 instance |
|---|---|---|
| x | Full signed state/carrier and response metadata | CF4 alpha, Commander Q_T, count excess |
| Q | Gauge or distance relative to a specified physical body | minimum full-sky RMS distance calibration |
| Pi | Tail under a named experiment or confidence-inversion decision | fixed-lambda Wald; count nominal sensitivity kept distinct from finite-MC Pi |
| F_support | Support/projected range of the common set | directional log-H and bounded velocity/calibration intervals |
| G_F | Depth/history functional with complete joint covariance | constant-versus-slope response, fixed mean-annihilating contrasts |

F_occupancy requires a measure on a stated support and a physical ceiling. Neither is supplied for the present physical state, so it is unavailable. A support ratio is not an occupancy probability and may be signed or exceed one.

For bounded angular calibration B_rho={xi:xi^TGxi<=rho²}, G=diag(I3/3,2I5/15), the physical map for psi=(beta,a,s) is psi=T alpha+K xi with T=diag(I3/c,-I3,I5) and K xi=(0,d_cal,-q_cal). Its support is

$$
h(u)=u^TT\hat\alpha+
\sqrt{\chi^2_{11}(.95)\,u^TT\,{\rm Cov}(\hat\alpha)\,T^Tu}
+\rho\sqrt{u^TKG^{-1}K^Tu}.
$$

Use the 11D cutoff for statements involving the whole identified alpha. An 8D or5D marginal target uses its own confidence set and cutoff. Take the outer envelope over m for interval reporting while retaining the underlying union, which need not be convex. The support hull is not the exact union.

For velocity slope, the same construction uses E+(-B ball_b), where B=Cov(alpha_hat) X^TC^-1Z. The retained raw32D experiment has additional residual information about V1; the displayed marginal union intentionally does not exploit it and is conservative under the finite response.

For a mixed nonlinear functional, report min/max over the same identified set or a posterior pushforward with an explicitly stated prior. The componentwise interval box generally contains states outside the true ellipsoid and can distort mixed contractions. No new nonlinear mixed-functional bound is claimed numerically in R60 beyond the derived contract.

## Information and publication claim boundary

For fixed C and linear mean, tensor/score coordinates reproduce the full GLS likelihood exactly on the retained32D carrier. They do not add Fisher information. Their practical contribution is to preserve signed/shape/orientation and cross-depth information, expose likelihood-null physical directions, and make Q/Pi/F/G_F refer to the same physical assumptions.

The32D carrier has not been proven sufficient for the raw35,970-group catalogue. A fair external comparison must match the raw sample, source response, covariance and selection. Scalar-only reductions may lose information, as the actual Commander branch-switch example demonstrates, while full harmonic/STF/BipoSH methods in the literature already preserve much of this structure.

Current implementation status: direct constant CF4 physical pullback inherited and verified; finite radial response and calibration supports added; Commander and counts tensor/vector measurements added as distinct experiments; general joint CMB–Gaia–counts–CF4 physical likelihood remains unresolved pending source-bound transfers and joint stochastic calibration.
