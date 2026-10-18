# HTT theory-to-observation next loop: theoretical research R1-R10

Date: 2026-10-15 KST. Starting Git HEAD:
13d8d85fa470d645d008986e8f77d8d0f70fdf54.
This continues the source-bound R/C loops in the parent research directory
without retroactively editing their claims or upstream observational reports.

## R1–R3: Original scientific questions and primary-source comparisons

(1) CMB: The finite Planck NSIDE64 mask and ell6..12 high-to-low operator K
from the preceding loop has full row rank 32. That identifies a linear
nonidentifiability ONLY if all 133 high-mode coefficients are free. The
previous experiment replacing the free nuisance by a 32-dimensional
train-only ridge adjustment made heldout prediction worse by about 2–13%.
Can one instead use 1–3 physics-geometrical directions of the actual K to
obtain an improved, conditional nuisance adjustment and retained local
boost tangent on the same published SMICA sky?

(2) CF4: Under the earlier PR179 registered H_ONLY selection-conditional
analysis, which actual design components drive the q_cat WITHHELD state?
Does the combined H-like n and cubic z^2*n response explain the small
q-like z*n information analytically, separately from method calibration
and sky selection nuisances?

Planck inputs use Galactic NSIDE64 thermodynamic temperature fluctuations
in microK and fixed released/synthetic FFP10 CMB+noise pair identifiers,
not independent recovered cosmological states. The CF4 source contains
authenticated grouped equatorial J2000 RA/DEC, frame-derived Vcmb,
distance modulus DMzp, and reported modulus error e_DMzp. The latter is
not the physical absolute-source redshift intercept or a complete survey
selection/cross-calibration likelihood.

Comparison with authoritative prior work:
- Planck 2018 IV, component separation (A&A 641 A4, 2020):
  https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html
- Gruetjen & Shellard, masked-sky augmented CMB statistics:
  https://arxiv.org/abs/1212.6945
- Phipson & Smyth 2010 / Hemerik & Goeman 2018 finite permutation rank;
  the observed-versus-FFP10 exchangeability remains a separate unmet premise.
- Tully et al. 2023 Cosmicflows-4, Heinesen 2021 general cosmography,
  Duangchan et al. 2026 A&A CF4 forward modeling.
- Existing HTT: GR optical first-jet theorem, Lorentz pullback,
  finite masked nuisance quotient, prior PR179 H/Q gate, and loop1/loop2
  conditional observational statistical implementations.

## R4–R5: New bounded constructive derivations

### K-left-singular 1–3-dimensional nuisance

Let K=R P_mask Y_(ell6:12) be the already registered 32x133
real harmonic response of high modes through the selected-mask
simultaneous ell0..5 fit. A singular value decomposition
K = U diag(sigma) V^T determines a geometry-only left subspace
U_r=U[:,1:r], r=1,2,3. An arbitrary orthogonal redefinition of
high source harmonic coefficients K->K V0 leaves K K^T and the
leading left subspace unchanged up to an internal orthogonal basis,
away from an unresolved singular-value crossing.

For each same-sky 32-vector Y=Y_fit5, H=Y_fit12-Y_fit5,
let Z_r=H U_r (r controls only). On the 60 training paired skies,
fit B_r in R^(r x 32) with

 B_r=(Zc^T Zc + lambda I)^(-1) Zc^T Yc,
 lambda = rho tr(Zc^T Zc)/r,
 rho in {0.25,1,4}.

Reconstruct the reduced-residual observable

 R=Y-mu_trainY -(H-mu_trainH) U_r B_r.

A baseline with B=0 is kept. Selection is based on fixed fivefold
CV within the TRAINING 60 sky identities only, with a predeclared
minimum gain of 0.5% in training CV squared error; otherwise baseline.
No simulated heldout sky or observed real Planck score selects r/rho.
Then fit the selected rule on all 60 training skies and apply it to
240 heldout full-sky paired realizations and the observed sky.

The resulting score is a quadratic in R with a train-only shrinkage
covariance. Under an actual complete joint observed/null exchangeable
sky law CONDITIONAL ON TRAINING (unverified), applying the frozen
selection/scoring map to the real sky and each heldout paired sky
gives the same conservative finite-rank theorem:
 p=(1+#null_score_ge_observed)/(1+B), B=240.
The two mask scores are joined by a row-wise maximum, not flattened
as independent skies. Historical feature selection before this loop
is not included in this two-choice maximum and the result is
nonconfirmatory physical Planck evidence.

For heldout centred matrices Yt, Zt, the EXACT finite-sample change
in unweighted residual MSE for fitted B obeys

 Delta_MSE = ||Zt B||_F^2/N
             -2 tr((Yt-mu_trainY)^T Zt B)/N.

The first is an added prediction-variance penalty and the second
is the heldout cross-predictive benefit. Large eigenvalues of
the geometric K K^T alone do not constrain the sign of Delta_MSE:
they describe high-mode coupling geometry, not Cov(Y,H).
Under the ideal scalar joint Gaussian model the population ridge
loss relative to the optimal conditional projection is
 c^2 lambda^2/[b(b+lambda)^2] >= 0.
That formula does not uniquely explain empirical training/heldout
differences and does not assert any new universal no-go.

The local physical-surrogate derivative under the previously
registered thermodynamic Doppler-weight-one convention is

 J_R = J_5 - (U_r B_r)^T (J_12-J_5).

Both J derivatives here are evaluated on an ALREADY OBSERVED,
ell<=12 re-fitted SMICA source surrogate; beta_ref is a reference
dimensionless observer-boost increment, not a measured intrinsic
source velocity. An actual unboosted sky/beam/foreground transfer
is required to promote this to physical parameter inference.

### Constructive q radial alias in Cosmicflows-4

For ANY positive z0 and any (weighted) observation row,

 z*n = (z0/2)*n + (1/(2 z0))*z^2*n
       - ((z-z0)^2/(2 z0))*n.

Thus a q-like z*n column can be approximated by a linear
combination of an H-like n column and a cubic-like z^2*n column,
with an explicitly controlled quadratic residual in radial width.
Given positive per-row design weights w_i and unit n_i, the best
weighted least-squares linear projection in span[n,z^2*n]
obeys

 [sum_i w_i ||r_i||^2]/[sum_i w_i z_i^2]
 <= [sum_i w_i (z_i-z0)^4/(4 z0^2)]/[sum_i w_i z_i^2].

The upper bound applies to the TRACE of the unnormalized q=z*n
Gram. It is NOT equal to the smallest GENERALIZED EIGENVALUE
of the normalized PR179 q design. In a narrow shell with
relative radial width Delta z/z0, the relative squared residual
is O((Delta z/z0)^4). This is a direct polynomial algebra and
projection inequality, not a claimed novel general-relativity
no-go theorem.

To compare contributions without changing existing gates,
calculate each fold's q generalised relative information eigenspectrum
for several DECLARED nested nuisance sets:
 raw; H only; cubic only; H+cubic; prior base only;
 prior base+H; prior base+cubic; prior base+H+cubic;
 nonmethod base+H+cubic and an intermediate method-offset scenario.
Reparametrization-invariant relative eigenvalues use
 eig(G_ret,G_raw), Graw=Q^T WQ, Gret=Qperp^T W Qperp.
The nuisance decomposition is ORDER DEPENDENT, not a unique causal
allocation to a named astrophysical selection effect.

## R6–R8: Executed numerical discrimination and limits

SMICA fixed geometry: the 1st, 2nd and 3rd singular left modes of K
explain respectively approximately 52%, 68%, 73% of the heldout H
difference energy at mask >0.5 (mask >0.8: 51%, 67%, 72%).
This does NOT imply comparable predictive power for Y.

Both masks chose rank3 rho4 from 60 training skies, whose
CV relative MSE improvements were 0.733% and 0.764%.
On the INDEPENDENT heldout240 simulation sky pairs, the
MSE changed by +0.235% and +0.260%, with paired 1,000-bootstrap
conditional 95% intervals [-0.134%,+0.605%] and
[-0.074%,+0.641%]. These bootstrap intervals overlap zero.
There is thus no validated improvement in heldout prediction.

The chosen two-mask conditional joint rank is
  (171+1)/241 = 172/241 = 0.7136929461.
This is NOT a confirmatory physical Planck p-value.
The additional-boost reference surrogate derivative/conditional
training scatter changes (mask0.5) from 0.0214834 to 0.0221026
and (mask0.8) from 0.0216593 to 0.0223248.
This is a small sensitivity change, not an increase in physical
detection power. Source convention and repeated same-sky use
remain restricted as above.

CF4: original 38,053 actual groups, existing registered PR179
35,549 domain, five preserved folds. The mean weakest relative
Fisher information with raw no nuisance is 1; after
H only 0.15251; cubic only 0.05430; H+cubic 0.005622;
existing base+H 0.029359; full existing base+H+cubic 0.002655.
If method-family terms are omitted but other base+H+cubic terms
remain, the result is 0.002949. Contributions are conditional on
their order; it is INVALID to assert a unique physical cause.

Exact fourth-moment envelope: across the five folds the
un-normalized q=z*n, H+cubic best weighted squared residual
averages 0.006770 of raw q trace, while the constructive bound
averages 0.018467. Wolfram verified the identity exactly,
and local tests verify the O(width^4) limit. This is a
source-bound discrete-design result, not real q inference.

## R9–R10: Admission and computational bridge

Accepted as EXPLORATORY_CONDITIONAL:
- Geometry-based lowrank nuisance and proper training-only choice
  under stated null exchangeability assumptions.
- Empirical failure to obtain heldout predictive improvement
  at this configuration.
- Finite CF4 q alias decomposition and polynomial fourth-moment
  upper bound with preserved PR179 WITHHELD status.

Not admitted: full Planck FFP10 observational physical null,
true intrinsic sky, 2018/Planck compsep transfer, global-tilt,
Bianchi low-ell native solver, cosmic acceleration measurement,
or CF4 calibrated shared method/selection likelihood.

Code and actual evidence are in the companion C1–C10 report;
new core sources under htt/obsstat are
geometric_lowrank_control.py, cf4_q_nuisance_ablation.py.
The prior source-blocker ledger has not been overwritten.
