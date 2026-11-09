# Solver-free morphology-to-likelihood routes

**Status:** R2 literature synthesis + R4 candidate construction. The equations below are a research design and direct derivation; no CAS or production implementation was executed in this turn.

## 1. Three meanings of “without a Boltzmann solver”

These must not be conflated.

- **No solver inside the sampler:** precompute a validated transfer/template grid or emulator and evaluate it inside Cobaya. This saves runtime but remains transfer-conditional.
- **No Bianchi Boltzmann hierarchy at all:** derive an exact geodesic response for a restricted background observable, such as the collisionless temperature field in Bianchi I. This can be physically grounded without predicting all CMB observables.
- **No physical transfer model:** fit arbitrary harmonic templates or BipoSH covariance directly. This is a legitimate anisotropy likelihood, but by itself it does not connect a morphology coefficient to a Bianchi geometry parameter.

R47 pursues the second route for Bianchi I temperature, uses the third route as a model-agnostic baseline, and retains the first route as a conditional extension for Bianchi V/VIIh or polarization.

## 2. Bianchi-I collisionless temperature map from conserved spatial momenta

### 2.1 Metric and observer convention

Use signature ((-+++)), explicit (c), synchronous comoving coordinates and
[
ds^2=-c^2dt^2+g_{ij}(t)dx^idx^j.
]
For a useful principal-axis parameterization,
[
g_{ij}(t)=a^2(t),[e^{2B(t)}]_{ij},qquad
B^T=B,quad operatorname{tr}B=0,quad
a(t_0)=1,quad B(t_0)=0.
]
The metric is spatially homogeneous and invariant under translations. Hence (partial_i) are Killing fields and the covariant spatial photon momenta (p_i) are conserved along each null geodesic.

At the observer, choose an orthonormal triad aligned with the coordinate axes and define (hat n) by (p_i=E_0 n_i), (hat n^That n=1). The photon energy measured by the comoving congruence obeys
[
E(t)^2=g^{ij}(t)p_i p_j.
]
Therefore
[
rac{E_*}{E_0}
=a_*^{-1}left[hat n^T e^{-2B_*}hat night]^{1/2}.
]

### 2.2 Collisionless Planck surface

Assume an isotropic Planck distribution at a sharp last-scattering hypersurface (t=t_*), with temperature (T_*), and collisionless propagation thereafter. Liouville conservation preserves the occupation number along each ray, so the observed temperature in direction (hat n) is
[
T_0(hat n)=T_*,rac{E_0}{E_*}.
]
With (ar T_0=T_*a_*) as the isotropic reference temperature,
[
oxed{rac{T_0(hat n)}{ar T_0}
=left[hat n^T e^{-2B_*}hat night]^{-1/2}.}
	ag{2.1}
]
This is an exact algebraic geodesic transfer for the restricted homogeneous Bianchi-I background and the stated emission/propagation assumptions. It does not require integrating the photon Boltzmann hierarchy.

For a fixed commuting principal-axis history with (dot B=sigma) and (B(t_0)=0),
[
B_*=-int_{t_*}^{t_0}sigma(t),dt.
	ag{2.2}
]
For non-commuting time-dependent spatial metric matrices, equation (2.2) must not be used as a naive componentwise integral: the metric at emission, or an appropriately path-ordered metric evolution, is authoritative. Equation (2.1) remains valid from the endpoint metric (g_{ij}(t_*)).

### 2.3 Small-anisotropy limit and observable tensor

For (|B_*|ll1),
[
e^{-2B_*}=I-2B_*+O(B_*^2),qquad
rac{Delta T}{T}(hat n)
=hat n^TB_*hat n+O(B_*^2).
	ag{2.3}
]
Thus the leading temperature signal is an STF quadrupole. At finite anisotropy the exact function in (2.1) is even under (hat nmapsto-hat n); it can generate higher even multipoles, but no odd multipoles under the ideal assumptions. A fitted octupole is therefore not predicted by this ideal Bianchi-I background-only channel. It must be explained by stochastic CMB realization, observer boost, other physics or systematics; it must not be silently absorbed into the Bianchi-I template.

The likelihood target is (B_*), or its equivalent integrated anisotropy metric, unless a separate dynamical prior/model maps it to the present (sigma_{ab}(t_0)). Many distinct shear histories have the same endpoint metric and the same collisionless temperature map. No inference of present-day shear or a unique time history follows from the temperature template alone.

### 2.4 Exact harmonic projection

Choose one canonical real-harmonic convention and pin it to the repository STF bridge. Define
[
a_{ell m}^{B}(B_*)=int_{S^2}dOmega,
Y_{ell m}^*(hat n)
left{[hat n^Te^{-2B_*}hat n]^{-1/2}-1ight}.
	ag{2.4}
]
Use either analytic angular integrals for special eigenvalue configurations or converged equal-area spherical quadrature with explicit integration-error estimates. Test rotation covariance, the (B_*	o0) limit, the first-order STF map, parity, and eigenvalue permutations. Do not hard-code a shear-to-(a_{ell m}) scale.

The monopole convention must be explicit. One option is to subtract the angular mean of the exact map and absorb it into the fitted CMB monopole; whichever choice is made must be applied identically to observed data, templates and simulations. The quadrupole normalization must be matched to the repository’s stored-real (a_{ell m}leftrightarrowmathrm{STF}_2) mapping, not an unscaled complex-harmonic shortcut.

## 3. Map/harmonic likelihood

Let (a) denote a finite real vector of observed low-ell modes, including exactly the fields and modes admitted by the data product. A generic conditional Gaussian model is
[
amidartheta,M sim
mathcal N!left(mu_M(artheta),,C_M(artheta)ight).
]
For the solver-free Bianchi-I temperature candidate,
[
mu_{B,I}(artheta)=a^B(B_*)+ mu_{m boost}(eta_{MO},eta_{RM})
+mu_{m other}(artheta),
]
where each added term must be independently derived, ordered in the correct observer-frame transformation and not duplicated. The stochastic sky covariance may begin with a declared statistically isotropic Gaussian reference covariance (C_{m SI}(psi)), but this is a **phenomenological/background-only approximation** when it is not the covariance predicted by perturbations on the same Bianchi background.

Let (R) be the complete observation operator, including frequency response/component separation as appropriate, beam, pixel window, mask, map filtering and harmonic projection. Then
[
d=R,a+n_{m inst}+f_{m res},
]
and, for a Gaussian residual model with covariance blocks,
[
Sigma_d=R C_M R^T+N_{m inst}+C_{m fg}+C_{m sys}.
]
The map-level likelihood is
[
-2lnmathcal L
=(d-Rmu_M)^TSigma_d^{-1}(d-Rmu_M)
+ln|Sigma_d|+N_dln(2pi).
	ag{3.1}
]
For non-Gaussian/estimated nuisance laws, replace this Gaussian expression with a source-calibrated likelihood or simulation-based density. A diagonal covariance, a C_ell-only likelihood, or a 743-byte summary NPZ cannot be called a full phase-sensitive map likelihood.

The exact likelihood route may use a low-resolution pixel vector with full covariance or a cut-sky harmonic vector with its complete induced covariance. It must not pretend a masked harmonic transform is full-sky orthogonal. Temperature and polarization may be combined only when their beams, calibration, transfer functions, cross-covariances and foreground residuals are modeled jointly.

## 4. Solver-free alternative / complementary likelihoods

### 4.1 BipoSH covariance model

For a general anisotropic stochastic sky, parameterize the off-diagonal harmonic covariance by a declared BipoSH basis:
[
C_{ell m,ell'm'}^{XY}
=C_{ell}^{XY}delta_{ellell'}delta_{mm'}
+sum_{LM}A_{ellell'}^{LM,XY}
(-1)^{m'},C_{ell m,ell' -m'}^{LM}.
	ag{4.1}
]
The Clebsch–Gordan convention, reality constraints, parity rules and finite (ell)-domain must be frozen. (X,Yin{T,E,B}) only when the selected data and transfers support those channels.

Equation (4.1) allows a statistically anisotropic likelihood without a Bianchi-specific solver. It can test whether the observed sky has covariance anisotropy and compare local-boost, instrument/foreground and generic anisotropic-covariance kernels. It does not label a Bianchi geometry unless a physical map derives (A_{ellell'}^{LM,XY}) from that geometry and the same background/perturbation model.

### 4.2 Precomputed template bank / emulator

A validated external Bianchi transfer (ABSolve, AniLoS/AniCLASS, or another qualified provider) may be run offline to produce a grid of (a_{ell m}^{T,E,B}(	heta)). An interpolator/emulator then evaluates a Cobaya likelihood without a solver call per sample. This is operationally solver-free **inside the sampler**, not independent of Boltzmann transfer physics. The grid must include exact provider revision, parameter domain, source configuration, conventions, interpolation error, independent benchmark and calibration. External products are always `TRANSFER_CONDITIONAL`, never relabelled native HTT output.

### 4.3 Simulation-based likelihood

A conditional density estimator may learn (p(S(d)mid	heta,M)) or (p(Psimid S(d),M)) from matched end-to-end simulations. This route is only admissible when the simulator contains the required foreground, mask, beam, calibration, noise, selection and model variability; training/test data are separated; SBC, coverage, FPR and posterior predictive checks are run; and simulation uncertainty is propagated. A collection of ideal isotropic Gaussian skies is not an NPIPE matched null.

## 5. How the tensorized five-variable readout enters

The statistical generative model is fit once:
[
p(artheta,psi,etamid d,M,S,W).
]
The project output (T=(x,Q,Pi,F,G_F)) is a **joint posterior/compatibility push-forward**, not a product likelihood:
[
mathfrak T=Phi_mathrm{HTT}#
p(artheta,psi,etamid d,M,S,W).
]
Here:
- (x) carries frame-typed physical state functionals and observed/predicted carrier tensors, with source/operator lineage;
- (Q) carries admissible anchor bodies and gauge fibres, with unavailable anchors remaining unavailable;
- (Pi) is a law-conditional exceedance surface evaluated against the matched source/mask/noise null;
- (F) is a directional support profile with equal-area quadrature and a certified denominator/occupancy semantic;
- (G_F) is the full cross-shell tensor functional path and covariance, not an assumed (sigma(z)) scaling.

The readout benchmark must use R46’s target-specific posterior-loss idea. Predeclare physical estimands (Psi), e.g. (B_*), a supported STF shear functional, an identifiable boost component or a directional-distance coefficient. Compare the target posterior under the full data with the posterior induced by each readout. A deterministic tensorization is lossless only for the actual likelihood/target if its conditional target information loss vanishes or is bounded/calibrated. Compare with raw (a_{ell m}), BipoSH, multipole vectors/power tensors, nuisance-hardened score, conventional posterior summaries and HTT's joint readout. The HTT readout is allowed to lose.

## 6. Bianchi attribution ladder

| Tier | What the data may establish | What remains unestablished |
|---|---|---|
| B0 | Full tensor morphology of the processed observed low-ell sky | physical source |
| B1 | Conditional compatibility with the solver-free Bianchi-I geodesic-temperature family | present shear history, polarization transfer, general Bianchi |
| B2 | Preference over explicit local-boost, isotropic realization, foreground/systematics and generic anisotropic-covariance alternatives | omitted alternatives, self-consistent Bianchi perturbation dynamics |
| B3 | A validated T/E/B or anisotropic covariance transfer for a specified Bianchi family | unique family attribution if response images overlap |
| B4 | Global family/parameter identification on the declared quotient, with nuisance-projected global separation and held-out calibration | uniqueness outside tested model class |

A conditional likelihood ratio or evidence only answers the enumerated model comparison under its stated priors and response contracts. It does not prove that a Bianchi model is the true spacetime.

## 7. Exact failure modes / hard stops

1. **History degeneracy:** equation (2.1) depends on the endpoint metric at emission. It cannot recover arbitrary (sigma(t)) from a single integrated map.
2. **Last-scattering/ionization physics:** a thin isotropic emission surface is a simplifying premise; finite visibility, scattering and reionization are not included.
3. **Polarization:** equation (2.1) predicts no self-consistent Bianchi E/B source. Do not fill E/B means with zero and use that as a physical prediction.
4. **Perturbation covariance:** (C_{m SI}) is a reference approximation unless perturbations on the same anisotropic background are computed or a qualified external provider supplies the covariance.
5. **Observer boost:** local Lorentz boost produces Doppler and aberration signatures; apply the exact ordered boost to both deterministic pattern and stochastic sky, with Wigner rotation for non-collinear boosts.
6. **Cut sky and components:** the beam/mask/component-separation response belongs inside (R); processed component maps of one sky are not independent likelihood channels.
7. **Non-uniqueness:** other anisotropic or systematic models can generate compatible low-ell patterns. The Bianchi-I tensor cannot stand in for Bianchi V/VIIh curvature parameters.

## 8. Minimal mathematical and numerical acceptance tests

- (B_*=0) gives an isotropic map and zero anisotropic (a_{ell m}).
- (B_*	oepsilon S) agrees with the first-order STF quadrupole map at (O(epsilon^2)).
- (B_*) symmetric and trace-free; (e^{-2B_*}) symmetric positive definite.
- (hat nmapsto-hat n) symmetry removes odd multipoles from the ideal Bianchi-I emission/propagation term.
- Rotating (B_*) and (hat n) together rotates the (a_{ell m}) vector by the matching irreducible (SO(3)) representation.
- All real-harmonic/STF normalizations agree with the current repository bridge.
- Equal directional quadrature and independent angular integration converge for (ellle L).
- Finite map likelihood agrees with the corresponding direct low-resolution pixel likelihood under a full-sky/no-mask fixture.
- Mask, beam, split and frequency transfer are tested by injected maps passed through the same (R).
- Conditional Gaussian likelihood recovers analytic parameter posteriors in a small known-covariance fixture.
- A local boost-only injection is not misclassified as Bianchi-I; a Bianchi-I injection is not spuriously assigned VIIh.
- Matched null SBC, coverage, FPR and posterior predictive checks pass before any empirical claim.

## References and prior art

- Pontzen & Challinor (2007), Bianchi CMB polarization transfer, https://doi.org/10.1111/j.1365-2966.2007.12221.x.
- Saadeh et al. (2016), ABSolve and Bianchi likelihood, https://doi.org/10.1093/mnras/stw1838; PRL anisotropy constraints https://doi.org/10.1103/PhysRevLett.117.131302.
- Vicente, Pereira & Pitrou (2025), AniLoS/AniCLASS line-of-sight integrators, https://arxiv.org/abs/2506.07786.
- Gerbino et al. (2020), CMB likelihood methods including exact harmonic and pixel likelihoods, https://arxiv.org/abs/1909.09375.
- Planck Collaboration (2016), BipoSH/covariance and CMB anisotropy methodology, https://arxiv.org/abs/1506.07135.
- Bridges et al. (2007), Bayesian MCMC analysis of Bianchi VIIh templates, https://doi.org/10.1111/j.1365-2966.2007.11616.x.
- Copi, Huterer & Starkman (2004), multipole vectors, https://doi.org/10.1103/PhysRevD.70.043515.
- Hajian & Souradeep (2006), BipoSH representation of CMB covariance, https://arxiv.org/abs/astro-ph/0607577.
