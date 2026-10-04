# CAS-05 v3 Lean statement alignment

This axis uses only the frozen `EXECUTION_CONTRACT_V3.json`, `NEUTRAL_INPUT.json`,
and `COMMON_SPEC.md` as mathematical inputs. Coordinates are length-valued
`0,1,2,3`; `sig 0=-1` and the other signs are `+1`. The curvature index order
in the source is `R_ab = R^c_acb`. Parameters `b>0`, `Lambda<3b`, `kappa>0`,
`c>0`, arbitrary finite real `lambda`, and arbitrary real `k` are retained.
Some algebraic identities hold on a larger domain; the positive and nonzero
assumptions appear on the division, gap, strict DEC, and right-inverse theorems.

| Contracted component | Kernel-checked statements | Exact scope |
| --- | --- | --- |
| C01 metric curvature | `christoffel_from_metric`, `dChristoffel_from_metric`, `ricciMetric_eq`, `einstein_from_metric` | Metric `E eta`, inverse `E^-1 eta`, first and second metric derivatives; `E != 0`, symmetric Hessian. The displayed conformal Einstein expression is a theorem, not a primitive definition of the metric curvature. |
| C01 neutral polynomial and origin | `phi_exact_taylor`, `jPhi_cubic`, `origin_G`, `origin_stress00`, `origin_stressii`, `origin_gap_pos`, `origin_strictDEC` | Exact finite Taylor identity for `phi_lambda`, origin stress `(6b-Lambda)/kappa`, pressure `Lambda/kappa`, gap `6b/kappa`, and strict origin DEC under the declared inequalities. |
| C01 differentiated eigenvector | `origin_G_exact_first_jet`, `origin_dG_full`, `dMetric_origin_zero`, `dStressOrigin_eq`, `eigenvector_normalization_jet`, `eigenvector_differentiated_equation`, `origin_acceleration`, `other_eigenvector_rates_zero`, `density_first_jet_zero`, `pressure_first_jet`, `nonEOS_pressure_gradient` | Exact first Taylor coefficient at the origin; the remainder is explicitly quadratic in the scale parameter. The finite future normalized eigenvector jet has `du^0=0`, `du^1_0=lambda/(3b)`, and every other spatial rate zero. Acceleration is `c^2 lambda/(3b)`. Density first jet is zero while pressure gradient is nonzero when `lambda != 0`. No eigenfield away from the origin is asserted. |
| C02 orthonormal ray | `ray_phi`, `ray_metric_scale`, `frame_pair`, `ray_frame_gap`, `ray_lambda_zero`, `ray_conditional_root` | On `x0=x2=x3=0,x1=s`, the two frame contractions carry `E^-1=exp(b s^2)`. `kappa(epsilon+p2)=exp(b s^2)(6b-2lambda s)` for all real `lambda,s`; the `lambda=0` case is explicit and `s=3b/lambda` is used only with `lambda != 0`. |
| C03 supplied cubic and jets | `S_symmetric`, `W_skew`, `H_symmetric`, `H00_zero`, `H_from_third_jet`, `H_homogeneous_cubic`, `H_origin_zero`, `j1H_origin`, `j2H_origin` | `H00=0`; symmetric `H0i=Hi0`; diagonal spatial `Hij` and zero off-diagonal spatial entries. `S=sym M` and `W=skew M` are coefficient matrices. The exact identity `H(X)=(1/6) sum J_abcde X_d X_e X_f` binds the explicit neutral cubic to the formal third tensor. Homogeneity `H(tX)=t^3 H(X)` proves that value, first and repeated second polynomial Taylor coefficients vanish at the origin. |
| C03 metric to curvature | `ddGamma_derived_from_metric3jet`, `dRicci_derived_from_connection_jet`, `dEinstein_derived_from_metric3jet`, `full40_first_Einstein_coefficients` | Generic finite product-rule expressions start from the inverse metric and first/second/third metric jets, then the connection, Ricci, scalar trace, and Einstein jet. At the origin `dg=0`, `d(g^-1)=0`, `j2H=0`, and `Gamma=0`; the background second-jet and curvature-times-`H` terms vanish in the *difference*. This yields the closed 40-coefficient table for arbitrary real `k`, not a target linear operator supplied as an axiom. |
| C03 basis, Bianchi, inverse, eigenvector | `origin_bianchi_four`, `all_twelve_basis_0i`, `full40_for_each_of_twelve_basis`, `right_inverse_q`, `right_inverse_M`, `universal_right_inverse_0i`, `normalizedEigenvectorJet_eq_k`, `normalized_differentiated_eigen_equation` | Four origin contractions, every `k_(row,col)` with row `0..3` and spatial column `1..3`, an explicit inverse for arbitrary real target `q_i,M_ij` when `b>0`, and finite normalized eigenvector jet `du^i_mu=k_mu_i`. |

The C03 closed coefficient table is, with spatial `i,j,l` and `tr M=sum_i M_ii`:

```text
mu=0:   dG_00=tr M, dG_0i=q_i, dG_ij=(S_ij-delta_ij tr M)/2
mu=l:   dG_00=0,    dG_0i=M_i l,
        dG_ij=(delta_i l q_j+delta_j l q_i)/2-delta_ij q_l
```

The universal `full40_first_Einstein_coefficients` theorem quantifies over
all four derivative directions and all sixteen tensor index pairs, hence all
40 independent symmetric entries. `full40_for_each_of_twelve_basis` instantiates
that theorem for each of the twelve `kBasis row col` choices. The separate
`all_twelve_basis_0i` theorem checks the index orientation directly:
`M_ij=-6b k_ji`. For arbitrary target `q,M`, `kRight` sets
`k_0i=-q_i/(6b)` and `k_ji=-M_ij/(6b)`; no rank-only argument is used.

Finite jet convention: a degree-three polynomial is represented by its exact
cubic coefficient array, not by a floating-point Taylor fit. `H_from_third_jet`
is an equality of the complete coordinate polynomials, and
`H_homogeneous_cubic` excludes all degree-zero, degree-one, and degree-two
terms, including repeated spatial/time derivatives. The formal first and
Hessian arrays in the source are only finite polynomial jet components. The
neutral input supplies that the conformal exponential remainder has coordinate
order at least four; this Lean axis uses the specified metric 3-jet
representative and does not prove a neighborhood estimate for that remainder.

All C03 equalities concern the homogeneous degree-one Taylor jet of
`G[g^(0)+H]-G[g^(0)]` at the origin. They are not nonlinear identities away
from the origin. The finite eigenvector equations do not establish a smooth
eigenfield or an implicit-function theorem. Lorentzian/strict DEC neighborhood
persistence, a uniform radius, CAS04/CAS06, an EOS/action, and full scientific
admission remain outside this axis. The scientific admission state is `HOLD`.
