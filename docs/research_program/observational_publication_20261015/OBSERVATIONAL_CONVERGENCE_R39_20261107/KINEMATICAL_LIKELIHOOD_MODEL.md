# R39 kinematical theta and multi-probe likelihood contract

**Status:** derived model-to-data design; no observed likelihood, posterior, or physical component estimate is produced by this document.  
**Authority:** HTT tensor/MES upgrade plan (2026-07-30), K0 typed kinematical crosswalk V2, K3 typed kinematical MES draft, METHOD_REBOOT_20261023/THEOREMS.md T7, R9 revision 2, and the R39 vector/tensor-x application note.

## 1. The primary parameter is a physical kinematical state, not a CMB summary

The notation \(\theta\) denotes a kinematical state parameterized on a declared congruence and set of spacetime points/epochs. It is not restricted to an observed harmonic coefficient vector.

Use metric signature \((-+++)\). For this likelihood contract, let \(U^a\) be the physical four-velocity of the selected congruence, \(U^aU_a=-c^2\), and define

\[
h_{ab}=g_{ab}+\frac{U_aU_b}{c^2},\qquad
\vartheta=\nabla_aU^a.
\]

The kinematical decomposition is

\[
\nabla_bU_a
=-\frac{1}{c^2}U_bA_a
+\frac{1}{3}\vartheta h_{ab}
+\sigma_{ab}+\omega_{ab},
\]

with

\[
A_a=U^b\nabla_bU_a,\quad
\sigma_{ab}=h_a{}^ch_b{}^d\nabla_{(c}U_{d)}
-\frac13\vartheta h_{ab},\quad
\omega_{ab}=h_a{}^ch_b{}^d\nabla_{[c}U_{d]}.
\]

Thus \(U^aA_a=U^a\sigma_{ab}=U^a\omega_{ab}=0\), \(\sigma_{ab}=\sigma_{(ab)}\), \(\sigma^a{}_a=0\), and \(\omega_{ab}=\omega_{[ab]}\). In an oriented orthonormal spatial triad \(e_A{}^a\), \(A,B=1,2,3\), use the axial dual

\[
\omega_A=\frac12\epsilon_{ABC}\omega^{BC}.
\]

The raw kinematical coordinates are therefore:

| Block | Independent real components | O(3) type | Raw units |
|---|---:|---|---|
| \(\sigma_{AB}\) | 5 | polar STF2, even | s\(^{-1}\) |
| \(\omega_A\) | 3 | axial vector, pseudo | s\(^{-1}\) |
| \(A_A\) | 3 | polar vector, even | m s\(^{-2}\) |
| \(\beta_{\rm RM,A}\) | 3 | polar vector, even | dimensionless |
| \(\beta_{\rm MO,A}\) | 3 | polar vector, even | dimensionless |

Here \(\beta_{\rm RM}\) is the radiation–matter relative velocity and \(\beta_{\rm MO}\) is the matter–observer relative velocity. Each vector carries both a physical frame ID and a spatial basis ID. An orthogonal 3D basis transport only aligns axes inside the same physical frame; it is not a Lorentz boost and cannot convert components between distinct physical rest frames. Mixed functionals and the first-order closure require both vectors to be represented in one common physical tetrad. A different physical frame ID therefore requires an explicit Lorentz/tetrad bridge; without it, preserve the direct vectors but mark mixed contractions and the derived closure as `RELATIVISTIC_FRAME_BRIDGE_REQUIRED`. Each vector carries both a physical frame ID and a spatial basis ID. An orthogonal 3D basis transport only aligns axes inside the same physical frame; it is not a Lorentz boost and cannot convert components between distinct physical rest frames. Mixed functionals and the first-order closure require both vectors to be represented in one common physical tetrad. A different physical frame ID therefore requires an explicit Lorentz/tetrad bridge; without it, preserve the direct vectors but mark mixed contractions and the derived closure as RELATIVISTIC_FRAME_BRIDGE_REQUIRED. The radiation–observer velocity \(\beta_{\rm RO}\) is retained as a derived/closure view, not added as a third independent three-vector. At first order,

\[
\beta_{\rm RO}=\beta_{\rm RM}+\beta_{\rm MO}+O(\beta^2).
\]

This relation is not an exact relativistic velocity-addition law. For exact composition, retain the ordered tetrads, boost convention, and any Wigner rotation. Never identify \(\beta_{\rm RO}\) with \(\beta_{\rm MO}\) without a matter–radiation premise.

The four blocks named by the user, with the project-required two independent frame velocities, give a 17-dimensional finite-dimensional core at one fixed spacetime point and epoch. If the signed scalar curvature-budget coordinate \(\Delta\Omega_k\) is admitted, the baseline becomes 18-dimensional. Optional spatial STF curvature, electric/magnetic Weyl, anisotropic stress and additional matter fields add their own typed blocks. A locally free SO(3) orbit quotient removes three orientation degrees of freedom, but this dimension count is **not** an observational rank or an identification theorem. With only one generic beta vector, the minimal \((\sigma,\omega,A,\beta)\) tuple has 14 real components before quotient.

### 1.1 Field-valued versus finite-dimensional theta

The true object can be field-valued:

\[
\theta_K(x)=
\left\{\sigma_{ab}(x),\omega_a(x),A_a(x),
\beta_{\rm RM}^a(x),\beta_{\rm MO}^a(x)\right\}.
\]

For a homogeneous Bianchi benchmark the coefficients may reduce to time-dependent functions or a finite parameter vector. For an inhomogeneous/perturbed model, expand in a declared basis, for example

\[
\sigma_{AB}(t,\mathbf x)=\sum_r s_r\,S^{(r)}_{AB}(t,\mathbf x),
\]

and analogously for the other blocks. Then \(\theta\) denotes the coefficient set \(\{s_r,w_r,a_r,b_r,\ldots\}\) together with the basis and truncation identity. A finite truncation is a model choice, not a consequence of tensor notation.

Store the frame, congruence, epoch/redshift window, averaging scale, triad, units, parity, spatial transport rule, perturbative order and source/provider identity with every block. A missing component is not a zero component.

The isotropic expansion \(H=\vartheta/3\) and other background/matter parameters can be included in a larger joint state \((\theta,\psi)\), or held in a declared background sector \(\psi\). They must not be silently absorbed into a dimensionless kinematical ratio.

### 1.2 Physical realizability is a separate layer

Arbitrary values of \((\sigma,\omega,A,\beta)\) at a point define a kinematical coordinate tuple, not automatically a solution of Einstein–matter dynamics. A physical model must impose the appropriate 1+3 Ricci identities, constraint/evolution equations, matter conservation, frame/tetrad compatibility, regularity and boundary/initial conditions. A solver-free phenomenological likelihood may first constrain an admissible kinematical response family, but it must report that level explicitly and may not promote it to a Bianchi family or GR solution.

## 2. x is the typed functional bundle of theta and the observable carriers

Let \(Z=(\theta,\psi,\eta,\xi)\), where \(\psi\) denotes background/matter/transfer parameters, \(\eta\) calibration/selection/systematic nuisances and \(\xi\) shared latent fields such as primordial perturbations, foregrounds or large-scale structure. The functional registry contains three distinct roles:

1. **Physical kinematical coordinates:** identity maps of each raw tensor/vector block, plus explicitly normalized copies such as \(\sigma_{AB}/H\), \(\omega_A/H\), \(A_A/(cH)\), \(\beta_{\rm RM,A}\) and \(\beta_{\rm MO,A}\).
2. **Observable carriers:** predicted \(a_{\ell m}^{T,E,B}\), BipoSH coefficients, source-count multipoles, Gaia E/B vector-spherical-harmonic coefficients and directional-distance multipoles.
3. **Mixed physical functionals:** registered contractions, products, projections, invariants and response functionals mixing the kinematical blocks.

For posterior draw or common-state witness \(s\),

\[
x_{s\alpha}=\phi_\alpha(Z_s)\in V_\alpha,
\qquad
K_\alpha(D)=\phi_\alpha(C(D)),
\]

where \(V_\alpha\) is the declared output representation and \(C(D)\) is one joint posterior-supported or simultaneous confidence/identified region. The heterogeneous output spaces may be polar/axial vectors, STF tensors, spin/harmonic carriers, scalars, pseudoscalars, paths or sets. The sample axis must identify posterior draws, confidence-set witnesses, null simulations, injections and other sample types separately.

Observed data carriers \(d^{\rm obs}\), including measured \(\tilde a_{\ell m}\), are source-bound fixed evidence. Predicted carriers \(\mathcal O_\alpha(Z_s)\) vary across samples. They may be displayed in one HTT bundle with roles OBSERVED_CARRIER and PREDICTED_CARRIER, but the observed coefficients must not be relabelled as posterior draws or counted again as an independent likelihood factor after their raw map has already been used.

### 2.1 Direct and mixed kinematical functionals

The initial registry should include at least the following examples. \(H\ne0\) is assumed wherever a Hubble-normalized expression appears.

| Functional | Definition | Output type | Interpretation |
|---|---|---|---|
| SIGMA_RAW | \(\sigma_{AB}\) | STF2 polar, 5 | Direct kinematical coordinates |
| OMEGA_RAW | \(\omega_A\) | axial vector, 3 | Direct kinematical coordinates |
| ACCEL_RAW | \(A_A\) | polar vector, 3 | Direct kinematical coordinates |
| BETA_RM, BETA_MO | corresponding relative-velocity vectors | polar vectors, 3 each | Distinct frame roles |
| SIGMA_H | \(\sigma_{AB}/H\) | STF2 polar | Dimensionless shear |
| OMEGA_H | \(\omega_A/H\) | axial vector | Dimensionless vorticity |
| ACCEL_C_H | \(A_A/(cH)\) | polar vector | Dimensionless acceleration |
| SIGMA_CONTRACT_BETA | \(\sigma_{AB}\beta_{\rm RM}^A\beta_{\rm RM}^B/H\) | scalar, even | Directional shear along matter–radiation tilt |
| BETA_DOT_OMEGA | \(\beta_{\rm RM}^A\omega_A/H\) | pseudoscalar, odd | Relative handedness/orientation |
| SIGMA_BETA_VECTOR | \(\sigma^A{}_B\beta_{\rm RM}^B/H\) | polar vector | Mixed anisotropic response direction |
| BETA_CROSS_OMEGA | \(\epsilon^A{}_{BC}\beta_{\rm RM}^B\omega^C/H\) | polar vector | Mixed polar/axial coupling |
| BETA_DOT_ACCEL | \(\beta_{\rm MO}^A A_A/(cH)\) | scalar, even | Observer-frame acceleration coupling |
| SIGMA_CUBIC | \(\mathrm{tr}(\sigma^3)/H^3\) | scalar, even | Shear-shape invariant |
| OMEGA_STRESS | \(\omega_A\omega^A/(6H^2)\) | nonnegative scalar | Vorticity sector stress |

These are not all equivalent targets. A scalar contraction is one additional registered functional and never replaces its vector/tensor source. For an orthogonal transformation \(R\in O(3)\),

\[
\sigma'\!=R\sigma R^T,\qquad
A'\!=RA,\qquad
\beta'\!=R\beta,\qquad
\omega'\!=(\det R)R\omega.
\]

Thus \(\beta\cdot\omega\) is a pseudoscalar; \(\beta^A\sigma_{AB}\beta^B\) is an even scalar. SO(3) orbit outputs retain handedness; an O(3) quotient deliberately identifies reflection-related states. Store the transformation law with the functional, not infer it from numerical component signs.

### 2.2 Relation to CMB and other observable harmonics

The physical tensor \(\sigma_{AB}\) and the observed CMB temperature quadrupole \(Q_{AB}\) share an STF2 representation but are not the same physical object. Likewise, observed \(a_{\ell m}\), STF multipole carriers and Gaia VSH coefficients live in observer/data space. Their relation to \(\theta\) is a forward map with source, redshift, frame, polarization, mask, beam, selection and transfer metadata. The current observer-irrep state remains an observer/data-space object; do not use it as a surrogate physical kinematical state.

## 3. The likelihood is defined on the common physical state

Write the complete observed data as

\[
D=\{D_{\rm CMB},D_{\rm count},D_{\rm SN/CF4},
D_{\rm ast},D_{\rm other}\},
\]

where the entries can include harmonic coefficients or maps, source redshifts \(z_i\), sky directions \(\hat n_i\), fluxes/colours, distance moduli, proper-motion vectors, polarization, lensing and their source identities/covariances. The likelihood is

\[
\mathcal L(\theta,\psi,\eta;D)
\equiv p(D\mid\theta,\psi,\eta,\mathcal W,\mathcal S),
\]

with explicit observation windows \(\mathcal W\), selections \(\mathcal S\) and source/operator versions. The posterior is a distinct object,

\[
p(\theta,\psi,\eta\mid D)
\propto \mathcal L(\theta,\psi,\eta;D)
\,p(\theta,\psi,\eta).
\]

The notation \(L(\theta\mid D)\) is often used informally for the likelihood as a function of \(\theta\); strictly, it is the density of \(D\) conditional on \(\theta\). A profile likelihood is an objective, not a probability law. A prior may regularize an ill-posed field reconstruction, but prior curvature does not create data-supported rank.

The shared-latent form is the preferred starting point:

\[
p(D\mid\theta,\psi,\eta)
=
\int d\xi\;p(\xi\mid\theta,\psi)
\,p(D\mid\xi,\theta,\psi,\eta).
\]

If the probe noises are conditionally independent only after conditioning on \(\xi\), factorize the conditional term, not the already marginalized probe likelihoods:

\[
p(D\mid\theta,\psi,\eta)
=
\int d\xi\;p(\xi\mid\theta,\psi)
\prod_p p(D_p\mid\xi,\theta,\psi,\eta_p,\mathcal W_p).
\]

This preserves common-sky cosmic variance, shared large-scale structure, overlapping sources, calibration and processing dependencies. If a justified conditional-independence model is unavailable, retain a joint likelihood/cross-covariance or report the combination as unavailable/conditional. Multiplying independent-looking marginal likelihoods is not a neutral default.

## 4. First observation-operator likelihood blocks

The first release should support at least the following likelihood families, with source-bound providers.

### 4.1 CMB T/E/B and harmonic covariance

Let \(\mathbf a^{\rm sky}\) be a real, nonredundant vectorization of the latent full-sky \(T,E,B\) coefficients, with the reality condition \(a_{\ell,-m}=(-1)^m a_{\ell m}^*\) respected. For map/split/frequency product \(r\),

\[
\mathbf d_{{\rm CMB},r}
=\mathsf P_r(\eta_r)\mathbf a^{\rm sky}+\mathbf n_r,
\qquad
\mathbf a^{\rm sky}\sim
\mathcal N(\boldsymbol\mu_{\rm CMB}(\theta,\psi),
\mathsf S_{\rm CMB}(\theta,\psi)).
\]

Here \(\mathsf P_r\) includes the actual component/bandpass operator, beam, pixel window, mask, filtering and estimator. Under the Gaussian working likelihood,

\[
\mathbf d_{{\rm CMB},r}\sim
\mathcal N\!\left(
\mathsf P_r\boldsymbol\mu_{\rm CMB},
\mathsf P_r\mathsf S_{\rm CMB}\mathsf P_r^T+\mathsf N_r
\right),
\]

or the corresponding joint covariance for multiple splits/frequencies. Anisotropic kinematics can alter both mean templates and the full off-diagonal harmonic covariance. The covariance may be represented by BipoSH or related tensor carriers, but a BipoSH estimate derived from the same \(\tilde a_{\ell m}\) is not an additional independent data set. Use either the raw map/harmonic likelihood or a declared compressed-estimator likelihood with its full covariance and transfer.

For local observer boost, the aberration and Doppler-modulation pieces have different harmonic responses and different contaminants. The mask and mean-field correction must be applied to the full processed operator. The existing PR-442/443/444 work is the required predecessor, not a new kernel to rewrite.

### 4.2 Source-count point-process likelihood

For source catalogue entries \(y_i=(\hat n_i,z_i,F_i,\mathrm{colour}_i,\ldots)\), define an observed intensity that includes selection and physical/kinematical response, for example

\[
\lambda_{\rm obs}(y\mid\theta,\psi,\eta,\xi)
=S(y\mid\eta)\,\bar\lambda(y\mid\psi,\xi)
\exp\!\left[\Delta_{\rm kin}(y;\theta,\psi,\eta)\right].
\]

The exponential parameterization is one positive-intensity option, not a fixed physical law. For an inhomogeneous Poisson process,

\[
\mathcal L_{\rm count}
=\exp\!\left[-\int_{\mathcal Y}\lambda_{\rm obs}(y)\,dy\right]
\prod_{i=1}^{N}\lambda_{\rm obs}(y_i).
\]

Conditioning on the observed count changes the normalizer and must be stated. Clustering and overdispersion generally require a Cox/hierarchical point process or an explicitly justified covariance approximation. The response must include the release-specific flux/redshift distribution, completeness, sky mask, Galactic/declination cuts, component grouping, local structure, spectral response and cross-match overlap. A single universal Ellis–Baldwin coefficient is not the full catalogue likelihood.

### 4.3 Supernova/standard-candle distance likelihood

For observed distance moduli \(\mu_i\) at \((z_i,\hat n_i)\),

\[
\mu_i^{\rm th}(\theta,\psi)
=5\log_{10}
\left[\frac{d_L(z_i,\hat n_i;\theta,\psi)}{10\,{\rm pc}}\right],
\]

and a Gaussian working likelihood is

\[
\boldsymbol\mu_{\rm obs}
\sim
\mathcal N\!\left(
\boldsymbol\mu_{\rm th}+M\mathbf 1,\,
\mathsf C_{\rm stat}+\mathsf C_{\rm cal}
+\mathsf C_{\rm pv}(\theta,\psi)
+\mathsf C_{\rm other}
\right).
\]

The exact data vector, full two-axis covariance subsetting, absolute-magnitude/calibration nuisance, redshift frame, peculiar-velocity model, selection/truncation normalizer and source identities are part of the likelihood. The distance \(d_L\) is computed from the direction-dependent null/optical propagation or a validated finite-redshift transfer, not by extrapolating a local \(z\to0\) formula over the full survey.

In the local sourceward direction convention \(n^a n_a=1\), the first-order directional Hubble rate of a congruence is

\[
\mathbb H_u(\hat n)
=\frac{\vartheta}{3}
-\frac{A_an^a}{c}
+\sigma_{ab}n^an^b.
\]

Consequently,

\[
d_L(z,\hat n)
=\frac{cz}{\mathbb H_u(\hat n)}+O(z^2)
\]

within the regular local optical domain. The antisymmetric vorticity tensor does not contribute to this leading \(n^an^b\) contraction. Thus low-z radial distances have a leading monopole/dipole/quadrupole response to expansion/acceleration/shear, but they do not identify vorticity at this order. The observer–matter boost adds a distinct Doppler contribution whose relative importance scales strongly at low redshift; it must not be merged with the intrinsic acceleration dipole. Finite-z attribution requires a light-cone response and remainder.

### 4.4 Gaia/astrometric proper-motion likelihood

For source \(i\), express the two tangent-plane proper-motion components as a vector \(\boldsymbol\mu_i\) in a declared local orthonormal sky basis. A source-level Gaussian model is

\[
\boldsymbol\mu_i
\sim\mathcal N\!\left(
\boldsymbol\mu_i^{\rm pred}(\theta,\psi,\eta,\xi),
\mathsf C_{\mu,i}
\right),
\]

with the full astrometric covariance and any inter-source/systematic covariance retained. The predicted tangent field is projected onto spin-1/vector spherical harmonics. E1 glide, B1 spin and E2 shear-like coefficients are distinct observed functionals with their own parity and systematic response; none is automatically equal to \(A_a\), \(\omega_a\) or \(\sigma_{ab}\). Cross-match, magnitude/colour, parallax, scanning-law and reference-frame systematics must enter the observation model.

### 4.5 Local optical angular drift: the complementary vorticity channel

The leading radial Hubble diagram is blind to the antisymmetric vorticity tensor, but the same local optical problem has a transverse direction-drift channel. This is an existing derived result in the repository's LOOP C construction (2026-10-26), based on the covariant connecting-vector and null-Jacobi endpoint map; R39 must reuse it rather than re-derive it under a new name.

For a smooth common timelike congruence in a convex normal neighbourhood, before caustics, with geometric optics, differentiable source tracking and an observer Fermi-Walker triad, define for sourceward unit direction \(n\)

\[
d(n)=\lim_{r\to0}\frac{cz(n,r)}{r},\qquad
\mu(n)=\lim_{r\to0}\frac{dn_{\rm obs}}{d\tau},\qquad
P(n)=I-nn^T.
\]

Here \(r\) is a locally calibrated optical distance with the affine-distance normalization specified in LOOP C. With the same \((-+++)\), outward-\(n\), axial-vorticity convention as the R39 state, the response is

\[
\boxed{
d(n)=H+\sigma_{ij}n^in^j-\frac{A_i n^i}{c},
\qquad
\mu_{\rm FW}(n)=P(n)\sigma n+n\times\omega.
}
\]

All terms in \(d\) and \(\mu\) have units s\(^{-1}\). The \(A/c\) term is an inverse-time vector. The angular formula is an optical endpoint result, not simply a simultaneous-constant-time relative-velocity argument: observer aberration and retarded emitter motion cancel the apparent extra acceleration term at this order. Do not append \(c\,P A\) to the transverse response. The physical acceleration is instead carried by the radial dipole.

If the catalogue triad rotates relative to the Fermi-Walker triad with angular velocity \(\Omega\), and \(k=d\tau/dt_{\rm cat}>0\), the measured angular field is

\[
\mu_{\rm cat}(n)=k\{P(n)\sigma n+n\times[\omega+\Omega]\}.
\]

Thus its B1 channel measures the sum \(\omega+\Omega\), not physical vorticity alone. A gyro or independent nonrotating-frame calibration is needed to separate them. Without that calibration, the exact three-dimensional null transformation \((\delta\omega,\delta\Omega)=(-q,q)\) remains. The source's own transverse motion, structural/centroid drift, propagation effects, observer translation and source slip must also be represented; a distant quasar is not automatically a comoving dust marker.

For the ideal uniformly weighted full sphere and calibrated Fermi-Walker clock/triad, exact moment inverses are

\[
H=\langle d\rangle,\qquad
\frac{A_i}{c}=-3\langle d\,n_i\rangle,
\]

\[
\sigma_{ij}
=\frac{15}{2}\left\langle d\left(n_i n_j-\frac{\delta_{ij}}{3}\right)\right\rangle
=5\langle\mu_{(i}n_{j)}\rangle,
\qquad
\omega=-\frac32\langle n\times\mu\rangle.
\]

This is a conditional local inverse, not yet a finite-survey estimator or a cosmological solution. Under the ideal full-sphere response, radial data have rank 9 (H, STF2 shear, polar acceleration), transverse data rank 8 (shared shear and axial vorticity), and the joint kinematical map rank 12. Adding unknown triad spin gives 15 columns but leaves rank 12. These are algebraic properties of this particular local response and full-sphere design, not rank statements about Gaia or a real selected catalogue.

For an actual catalogue, form source-level rows for both radial and transverse observables using the real \(\hat n_a\), tangent basis, distance window, selection, frame conversion and source population. The relevant finite-source Jacobian has a radial block with derivatives against \((H,\sigma_I,A/c)\), and a transverse block against \((\sigma_I,\omega,\Omega)\). Whiten on the full covariance support, project source slip, triad spin, clock, selection, calibration and other nuisance directions in that same metric, then compute the supported quotient. The radial–transverse shear closure residual is an additional model check; finite-distance/remainder and selection effects can make it nonzero without identifying a unique failure mechanism.

The new R39 code kernel common.kinematical_functionals.local_optical_response and local_optical_jacobian reuses the existing common.relativistic_kinematics.kinematics_from_velocity_jet adapter. The Jacobian is an unwhitened ideal source-level derivative; it is not itself the observed Gaia/CF4 Jacobian and cannot certify empirical rank.

## 5. Joint likelihood, nuisance projection and functional identifiability

The full joint data vector is not generally a product of independent probe vectors. If a Gaussian approximation to the admitted joint summaries is justified, stack

\[
\mathbf d=(\mathbf d_{\rm CMB},\mathbf d_{\rm count}^{\rm comp},
\boldsymbol\mu_{\rm SN},\boldsymbol\mu_{\rm Gaia},\ldots)
\]

with full \(\mathsf C_{\rm joint}\), including nonzero cross-probe blocks where required. For a Gaussian summary with mean \(\boldsymbol m(\theta,\eta)\) and covariance \(\mathsf C(\theta,\eta)\), the expected Fisher information is

\[
F_{ij}
=(\partial_i\boldsymbol m)^T\mathsf C^{-1}(\partial_j\boldsymbol m)
+\frac12\mathrm{Tr}\!\left[
\mathsf C^{-1}(\partial_i\mathsf C)
\mathsf C^{-1}(\partial_j\mathsf C)
\right],
\]

when the covariance is parameter-dependent and the Gaussian regularity conditions hold. For a Poisson point process, the corresponding ideal information is

\[
F_{ij}^{\rm count}
=\int_{\mathcal Y}
\frac{\partial_i\lambda(y)\,\partial_j\lambda(y)}
{\lambda(y)}\,dy,
\]

before latent clustering and nuisance marginalization. These formulas are diagnostics/approximations for the actual admitted likelihood; they do not replace end-to-end coverage tests.

After supported-covariance whitening and nuisance projection, a local response \(J_{\rm eff}\) can be formed from the actual source-conditioned estimator/forward operators. Its singular spectrum, null/weak directions, parameter scaling, principal angles and condition number on the supported quotient must be reported. A functional \(\phi_\alpha(\theta)\) is locally identified only if

\[
\ker J_{\rm eff}\subseteq\ker D\phi_\alpha.
\]

For a parameter-dependent covariance or non-Gaussian likelihood, use the full likelihood score/Fisher tangent rather than the mean-response Jacobian alone. Global identification requires \(\phi_\alpha\) to be constant on each exact observational fibre. Otherwise the correct output is the entire image

\[
K_\alpha(D)=\{\phi_\alpha(\theta):
\theta\in\Theta(D)\},
\]

with empty, bounded non-singleton, unbounded, disconnected and unresolved cases kept distinct.

The R39 target is not “full rank for every coordinate”. It is to identify which direct and mixed kinematical functionals are constrained by which observation channels, which combinations remain degenerate, and which additional observable would separate them.

## 6. The tensorized five-variable methodology is applied to the likelihood/posterior as one object

Construct one joint likelihood and then one joint posterior or simultaneous compatibility/confidence region. Only then derive the five HTT outputs from the same \((\theta,\psi,\eta,\xi)\) draws/witnesses:

### x — typed state/functional bundle

Contains raw kinematical components, observable carriers and mixed functionals. Every functional carries its source state, rank, parity, units, frame/congruence, epoch/window, normalization, response and availability. A scalarization is one optional functional, never the primary definition.

### Q — matching anchor and acceptance-body score

For each declared functional family, retain the matched MES/physical anchor body, its nuisance dependence, gauge, margin and active boundary directions. An acceleration or velocity block with no admitted anchor remains ANCHOR_UNAVAILABLE; a geodesic premise \(A_a=0\) is not a numerical acceleration anchor. A Q score is meaningful only for its registered acceptance body; it is not a generic scalar sufficient statistic for \(\theta\).

### F — directional support, sample pushforward and occupancy

For identified set \(\mathcal I_\alpha\) and matching anchor \(\mathcal A_\alpha\),

\[
h_{\mathcal I_\alpha}(u)=
\sup_{x\in\mathcal I_\alpha}\langle u,x\rangle,
\qquad
F_\alpha(u)=\frac{h_{\mathcal I_\alpha}(u)}
{h_{\mathcal A_\alpha}(u)}
\]

only where the matching support is positive and the registered domain is satisfied. Preserve this support profile separately from the sample-wise pushforward and any measure-defined occupancy. A support function does not reconstruct nonconvex/chiral strata.

### Pi — law-conditional exceedance surface

For a registered functional \(\phi_\alpha\), matching anchor body \(\mathcal A_\alpha\), registered acceptance score \(Q_{\mathcal A_\alpha}\), score map \(T_\alpha\), explicit law \(\nu\), conditions \(\eta\), and threshold \(c\), define

\[
q_\alpha(Z)=T_\alpha\!\left(Q_{\mathcal A_\alpha}(\phi_\alpha(Z))\right),
\qquad
\Pi_{\phi_\alpha,T_\alpha}(c\mid\eta;\nu)
=\Pr_\nu[q_\alpha(Z)\ge c\mid\eta].
\]

This is the conditional exceedance contract. \(Q_{\mathcal A}\) itself is a registered acceptance-body/gauge score; \(T_\alpha\) is part of the functional specification.

The law must be named as null simulation, injection, bootstrap/resampling, posterior or posterior-predictive pushforward. Likelihood and profile likelihood are not probability laws. A posterior exceedance, frequentist null tail and compatibility-set bound are different interpretations.

### G_F — functional depth path

Store the tensor functionals, frame/basis transport, support profiles, paired contrasts and full cross-depth/mask/frequency covariance. Preserve the initial/common-depth block as well as contrasts. For signed or zero-crossing functionals use set/support differences, not an automatically floored positive ratio. The legacy one-dimensional \(G_F\) is only a restricted view of this path.

This construction makes the five-variable method central to interpreting the joint likelihood: it explains what is constrained, by which anchor, in which directions, under which law, and how the identified functional set changes with depth/window. It does not add five independent likelihood factors or multiply marginal posterior intervals.

## 7. Minimum useful ablations and falsification tests

All ablations use identical admitted data, likelihood normalization, nuisance treatment, selection, masks, covariance and injections:

1. observed harmonic carriers only (no direct physical \(\theta\) functionals);
2. direct kinematical coordinates only;
3. direct coordinates plus registered mixed functionals;
4. full joint model with CMB, counts, Gaia and distance channels;
5. leave-one-probe-out variants;
6. legacy scalar \(x_C\) only versus typed tensor \(x\);
7. SO(3) orbit outputs versus the declared O(3) reflection quotient.

A tensorized model is useful only if it improves calibrated prediction, functional identification/coverage or controlled discrimination without nuisance leakage. A larger parameter/function list or a narrower prior posterior is not success.

Required manufactured/limit tests include:

- FLRW zero section; zero shear/vorticity/acceleration and coincident frames;
- shear-only, vorticity-only, acceleration-only, global-tilt-only and local-boost-only injections;
- \(A=0\) geodesic branch versus unavailable acceleration anchor;
- exact and first-order velocity composition with non-collinear axes/Wigner rotation;
- repeated-eigenvalue and zero-shear strata;
- O(3) improper-transform parity tests for every direct and mixed functional;
- small-\(z\) local optical limit versus finite-z transfer;
- vorticity radial-Hubble leading-order blindness and a separately specified reopening channel;
- CMB mask/beam/frequency/split matched null and no double-counting of BipoSH summaries;
- count selection, local-structure and overdispersion injections;
- Gaia E1/B1/E2 leakage/systematic injections;
- full cross-covariance versus an intentionally wrong block-diagonal model;
- posterior coverage, null false-positive control, injection bias and leave-one-probe-out prediction;
- prior-width and parameterization/basis sensitivity for every weakly identified direction.

## 8. Prior-art boundary and actual R39 contribution candidate

The component methods are established predecessors:
- 1+3 covariant kinematics and the separation of expansion, shear, vorticity and acceleration;
- observer-boosted CMB covariance/BipoSH and masked-sky mean-field calibration;
- Bianchi temperature/polarization transport with shear/rotation-dependent patterns;
- spin-1 proper-motion harmonic likelihoods with E/B parity;
- the project's own observable-irrep, full-sky boost pullback, STF2-to-STF3 and processed cut-sky response work;
- typed kinematical MES, anchor geometry and joint response-limited identified sets.

R39 must not claim those pieces as newly invented. The candidate contribution is the **single source-conditioned likelihood-to-functional inference map** that places raw congruence kinematics, frame-relative velocities, observable harmonic carriers and their mixed tensor functionals on one common latent state, propagates their shared dependencies through actual multi-probe operators, and returns the five tensorized HTT views with functional-specific identifiability and set-valued uncertainty. This is conditional until the actual operators, data/covariance identities, and coverage/predictive ablations are implemented and executed.

## 9. Literature and internal authority

Primary/technical foundations:

- Ellis & van Elst, *Cosmological Models* (Cargèse Lectures 1998), arXiv:gr-qc/9812046: 1+3 covariant kinematics, dynamics, tetrads and radiation/matter perturbations. https://arxiv.org/abs/gr-qc/9812046
- Heinesen, *Multipole expansion of the general luminosity distance*, JCAP 05 (2021) 008, arXiv:2010.06534: covariant directional Hubble parameter and luminosity-distance multipoles. https://arxiv.org/abs/2010.06534
- Sung & Coles, *Temperature and polarization patterns in anisotropic cosmologies*, JCAP 06 (2011) 036: Bianchi temperature/polarization patterns and shear/rotation effects. https://doi.org/10.1088/1475-7516/2011/06/036
- Planck Collaboration, *Planck 2013 results. XXVII. Doppler boosting of the CMB: Eppur si muove*, A&A 571 (2014) A27: velocity-induced modulation/aberration, off-diagonal covariance, mask mean field and simulation-calibrated estimator. https://doi.org/10.1051/0004-6361/201321556
- Catena & Notari, *Cosmological parameter estimation: impact of CMB aberration*, JCAP 04 (2013) 028: cut-sky aberration/Doppler corrections can bias parameter inference if omitted. https://doi.org/10.1088/1475-7516/2013/04/028
- *Cosmology with extragalactic proper motions: harmonic formalism, estimators, and forecasts*, MNRAS 486 (2019) 145: spin-1 harmonics, E/B parity, proper-motion covariance likelihood and redshift-dependent transverse-velocity statistics. https://academic.oup.com/mnras/article/486/1/145/5376504
- *Beyond dust in local cosmography: perturbative Vlasov predictions*, arXiv:2610.25145 (2026): local directional Hubble multipoles, acceleration/shear terms, and distinction between intrinsic acceleration and observer Doppler response. https://arxiv.org/abs/2610.25145

Internal controlling sources:

- HTT_VECTOR_TENSOR_MES_TWO_PILLAR_UPGRADE_PLAN_20260730.md §§2,4,6;
- K0_TYPED_KINEMATICAL_MES_AUTHORITY_CROSSWALK_V2.yaml;
- K3_TYPED_KINEMATICAL_MES_CORE_DRAFT_20260905.md §§4–6;
- HTT_REPORT_A_EVIDENCE_INTEGRATED_R3.md §§4–9;
- tensor_joint_r9/revision2/MODEL_TO_DATA.md and THEORY_EXTENSION.md;
- METHOD_REBOOT_20261023/THEOREMS.md T7;
- R39 VECTOR_TENSOR_X_FRAMEWORK.md and PR_LEGACY_AUDIT.md.
