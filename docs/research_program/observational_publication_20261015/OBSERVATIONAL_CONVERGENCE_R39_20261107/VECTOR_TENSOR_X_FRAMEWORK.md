# R39 application note: vector/tensor-valued x in HTT observational cosmology

## 1. Authority and decision

This note applies the pinned HTT tensorized contract in:

- METHOD_REBOOT_20261023/THEOREMS.md, especially definitions and T7;
- tensor_joint_r9/revision2/MODEL_TO_DATA.md;
- tensor_joint_r9/revision2/THEORY_EXTENSION.md;
- the vector/tensor MES migration lineage (PR-248–275; GitHub PR #360 and #367).

The canonical output remains (x,Q,Pi,F,G_F), with the ordering and meaning fixed by the pinned theorem. R38's presentation order is not a license to change semantics. In particular, x is not x_C and is not a scalar-valued likelihood parameter.

The R9 documents define x as a sample × functional object whose component rank and parity are retained. T7 defines a common typed state Z, one simultaneous confidence/identified region C(D), and functional images K_phi(D)=phi(C(D)). The R39 application follows these definitions.

## 2. Typed mathematical object

Let the common latent state be

\[
Z=(Z_{\rm phys},Z_{\rm obs},\eta,A,R),
\]

where Z_phys contains physical kinematic/geometry tensors, Z_obs contains explicitly defined observable carriers or their latent predictions, eta contains shared and probe-specific nuisance variables, A contains population/MES anchors, and R contains response/remainder variables. Each coordinate carries frame, congruence, epoch/redshift window, spatial basis, units, parity, perturbative order, provider identity and support status.

Let C(D) be one joint posterior support or one simultaneous confidence/identified region for Z. A registered functional is a typed map

\[
\phi_\alpha:\mathcal Z_\alpha\longrightarrow V_\alpha,
\qquad
V_\alpha=V_{\ell_\alpha}^{p_\alpha},
\]

where V is the declared scalar/vector/STF/spin-harmonic representation and p is its parity/action type. For state draw or admissible common-state sample s,

\[
x_{s\alpha}=\phi_\alpha(Z_s)\in V_\alpha.
\]

Thus the bundle has an outer sample index and an inner functional index, but the entries are heterogeneous typed objects. It is not generally a rectangular real matrix with one scalar per column. A numerical flattened representation is permitted only as a storage/linear-algebra view with an explicit orthonormal basis, metric, units, parity map and inverse reconstruction. Flattening does not erase the type record.

The set-valued counterpart is

\[
K_\alpha(D)=\phi_\alpha(C(D))\subseteq V_\alpha,
\]

or a certified outer set containing it. Preserve the status EMPTY, UNBOUNDED, UNDEFINED, UNAVAILABLE and NUMERICALLY_UNRESOLVED separately. A coordinate absent from the admitted observation map remains unrestricted or explicitly restricted; it is never zero-filled.

### Sample-axis contract

The sample axis must say what a sample means. Posterior draws, confidence-set witnesses, common null realizations, map splits, catalogue objects, and redshift-shell summaries are different sample spaces. They cannot be concatenated under one index merely because they are arrays. Each sample has a stable state_id or realization_id and provenance. Catalogue object rows are raw data rows, not posterior samples of Z.

### Equivariance and parity

For a rotation/reflection R, every functional declares its representation action:

\[
\phi_\alpha(\rho_Z(R)Z)
=\rho_\alpha(R)\phi_\alpha(Z).
\]

For polar/axial vectors, STF tensors and spin-weighted harmonics the corresponding O(3) or SO(3) representation is explicit. For improper R, polar/axial distinction is retained. Parity-sensitive functionals carry their parity sign; they are not silently identified under reflection. SO(3) orbit comparisons retain chirality, whereas O(3) comparisons quotient it out. The observation window generally breaks full-sky equivariance; its action must be included in the observation operator, not mistaken for a transformation law of the sky itself.

## 3. Cosmology functional registry: proposed first release

The registry below is an applied design, not a claim that each component is already observed or identified.

| Functional family | Typed x component | Representation and parity | Primary data carrier | Interpretation ceiling |
|---|---|---|---|---|
| Observer/radiation/matter frame | beta_RO, beta_RM, beta_MO | polar V1 | CMB dipole and independent boost estimator; tracer counts | Exact only after ordered tetrad/boost convention; first-order closure is separately tagged |
| Residual radiation dipole | d_int | polar V1, with gauge-invariant transfer definition | CMB temperature/polarization and lensing/long-mode response | Not a free temperature-gradient label |
| Optical acceleration | A/(cH) | polar V1 | low-z directional distance/Hubble dipole | Requires congruence and local optical assumptions |
| Shear history | sigma_ij(z)/H(z) | STF2, even parity | SN/CF4 directional quadrupoles, Gaia E2 VSH, CMB transfer | Finite-z coefficients are effective until transfer is validated |
| Vorticity | omega_i/H | axial V1 | B1/frame-sensitive astrometric and physical transfer channels | Do not infer from an E1 glide or STF2 alone |
| Weyl curvature | E_ij/H^2, H_ij/H^2 | STF2 electric/even and magnetic/odd | Bianchi/inhomogeneous transfer and optical propagation | Not currently supplied by a Gaia or distance quadrupole alone |
| Spatial curvature/geometry | 3-Ricci STF, invariant structure constants | typed rank-0/rank-2/geometric data | family-specific distance and CMB transfer | Needed for Bianchi family classification |
| CMB morphology | T_lm, E_lm, B_lm, STF T2/T3, multipole-vector and parity functionals | spin/harmonic irreps; T/E parity (-1)^l, B parity (-1)^(l+1) | observed Planck frequency/split maps | Processing and window responses retained |
| CMB statistical anisotropy | A^{LM,XY}_{ll'} BipoSH | rank-L harmonic carrier with XY parity rule | off-diagonal T/E/B covariance | Boost, mask, lensing and intrinsic modulation must be separated |
| Source-count morphology | count dipole D_i and higher multipoles | polar V1 plus higher STF/spherical harmonics | Quaia/NVSS/RACS source catalogue + randoms | Selection, clustering and overdispersion are part of the likelihood |
| Astrometric morphology | a^E_lm, a^B_lm | spin-1 VSH; E/B parity distinct | Gaia DR3 source proper motions and full covariance | E1 glide, B1 spin and E2 shear-like patterns separated |
| Directional distance | D_i(z), Q_ij(z), higher registered multipoles | V1 and STF2+ | Pantheon+, CF4; angular BAO only if uncompressed products | Local and finite-z estimands kept separate |

The physical variables and measured carriers are distinct spaces. For example, an observed Gaia E2 coefficient is a data summary in an astrometric spin-1 field; it is not identical to metric sigma_ij. The bridge between them is a redshift-, frame- and selection-conditioned forward response.

## 4. Observation map and identifiability

For probe p, source/selection release r and observable carrier a, write

\[
d_{p,r}=\mathcal O_{p,r}(Z;\,W_{p,r})+n_{p,r},
\]

where W includes the actual angular/redshift/flux window, beam, mask, bandpass, estimator and selection. Its local response is

\[
J_{p,r}=\left.\frac{\partial\mathcal O_{p,r}}{\partial Z}\right|_{Z_*}.
\]

Stack the admitted probes only after source identities and covariance are fixed. Let C be the full joint data covariance, including cross-probe blocks where known. Let N span shared and product-specific nuisance tangent directions in the same whitened data space. With a declared positive-eigenspace whitening W_C, define

\[
\bar J=W_CJ,\qquad \bar N=W_CN,\qquad
P_\perp=I-\bar N(\bar N^T\bar N)^+\bar N^T,
\qquad J_{\rm eff}=P_\perp\bar J.
\]

Rank is evaluated on the supported covariance quotient and is accompanied by the full singular spectrum, units/column scaling, weak/null parameter combinations and sensitivity to masks/cuts/nuisance choices. No prior or arbitrary normalization may increase the data-supported rank.

For a functional phi with derivative Dphi, local identifiability requires

\[
\ker J_{\rm eff}\subseteq\ker D\phi.
\]

Nonlinear/global identifiability is stronger: phi must be constant on each exact observation fibre. If it is not, retain the set image phi(C(D)). Therefore the full tensor bundle can contain well-measured functionals and unrestricted/unidentified components simultaneously. A rank number for the entire coordinate vector does not decide all functional targets.

The joint response must include the real estimator operators. A hand-written block matrix, isotropic covariance, or a zero-filled missing probe is not an observation-derived Jacobian.

## 5. Five-variable HTT application

The common region C(D) is constructed before any HTT summaries. The five outputs are then obtained as follows.

### x: functional-value bundle

For every registered sample s and functional alpha, store x_salpha=phi_alpha(Z_s), preserving the output tensor, rank, parity, units, frame, epoch, domain, support and provenance. Keep tensor objects as typed values. A scalar contraction is an additional registered functional, not the definition of x.

### Q: anchor/gauge/margin bundle

Q_alpha is the anchor object matched to functional alpha: gauge body, admissible margin, MES normalizer or population reference, with its own joint uncertainty and identity. It is not a likelihood factor. If the anchor is unknown or unavailable, do not replace it by an arbitrary isotropic sphere or zero.

### F: directional support and occupancy

For a functional set K_alpha and matching anchor A_alpha, directional support is

\[
h_{K_\alpha}(u)=\sup_{x\in K_\alpha}\langle u,x\rangle.
\]

Where h_A(u)>0, define the support-utilization profile F_sup,alpha(u)=h_K(u)/h_A(u). Keep it distinct from directional support, sample pushforward and measure-defined occupancy. For nonconvex/chiral sets retain the original set/strata because the support function sees only the convex hull. A finite angular grid maximum is a lower bound unless an independently certified Lipschitz/outer correction is supplied.

### Pi: typed strict-exceedance surface

Given an explicitly identified source/posterior/null law mu and a registered scalar score q_alpha that is invariant/equivariant under the declared action, define

\[
\Pi_\mu(\alpha,t)=\mu\{q_\alpha(Z)>t\}.
\]

Pi is indexed by functional/score and threshold, with the law named. It is not automatically a frequentist p-value. A confidence/identified set without a probability law yields bounds/support, not a fabricated exceedance probability.

### G_F: tensor-functional depth path

For ordered redshift, flux, frequency or distance shells, retain raw tensor-functional values and the full joint covariance across every shell. If Y=(Y_0,...,Y_m), any fixed path transform T produces C_Ypath=T C_Y T^T. Preserve the initial/common level as well as the differences: difference-only paths annihilate common modes and can lose the very monopole/constant component needed for frame calibration. Missing cross-covariance blocks mean the joint depth law is unavailable, not zero. Fitted transports require a joint law or repeated fitting inside every null/injection replicate.

The five quantities are outputs of the same joint physical/data object. They are not five independent scalar parameters or likelihood factors.

## 6. Why x_C is insufficient: a concrete R39 ablation

The legacy projection

\[
x_C=\Sigma_G^2-W_G^2+\Omega_{\rm tilt}+\Delta\Omega_k
\]

is retained as a signed budget diagnostic where its original premises apply. It is not the primary estimand. The mapping from the tensor state to x_C is many-to-one: distinct shear/vorticity/tilt/curvature configurations can cancel in x_C. It discards vector orientation, tensor eigendirections, parity, redshift evolution, spatial-curvature structure and functional dependence. Equal x_C therefore does not imply equal observable response or equal physical state.

The R39 ablation must compare, on identical admitted data and mocks:

1. scalar x_C-only representation;
2. the complete registered vector/STF/spin functional bundle;
3. the same bundle after O(3) quotient;
4. the same bundle after SO(3) quotient, retaining chirality;
5. tensor bundle with selected channels removed (CMB T/E, counts, Gaia E/B, distance multipoles).

The outcome is not automatically that the tensor model wins. It must show a preregistered improvement in calibrated out-of-sample prediction, identifiable functional coverage or discrimination power at controlled false-positive rate, without increasing nuisance leakage. If no measurable improvement occurs, report it as a null methods comparison.

## 7. Reuse map and current code boundary

Existing code found on the R39 branch:

- common/r9_product.py: ProductIntake enforces exact ordered row/covariance identity and explicit release/frame/epoch/selection/calibration/mask/law metadata; SharedStateEmbedding keeps physical/observable/nuisance roles distinct and does not silently convert units or frames.
- common/tensor_functionals.py: fixed 3x7 STF contraction-fibre support. It requires q fixed, returns JOINT_Q_INVERSE_IMAGE_REQUIRED for uncertain q, and explicitly says its numerical support is not a confidence certificate.
- common/depth_path.py: fixed feature path and full covariance assembly. Any missing ordered covariance block returns None, so independence is not silently inserted.
- METHOD_REBOOT_20261023/THEOREMS.md T7: common joint domain, simultaneous functional-image coverage, gauge/anchor stability, directional support, Pi surface and information-preserving depth path.
- tensor_joint_r9/revision2/MODEL_TO_DATA.md and THEORY_EXTENSION.md: source intake, shared nuisance/anchor, full covariance, joint law, common-state intersection and tensor confidence image.

What is not yet present as an admitted production implementation is a cosmology-wide TensorFunctionalBundle tying the physical tensor state, CMB morphology carriers, source-count operators, Gaia VSH, optical distance multipoles and their cross-covariance/selection provenance together. R39 records this as a local implementation task, not a completed feature.

## 8. Acceptance and novelty gate

A tensor-x implementation is accepted only when:

1. every functional has a unique ID, declared input domain, representation rank, parity, units, frame, epoch/window, map version and availability status;
2. all functionals for a sample share the same state_id and common confidence/identified-set identity;
3. rotations/reflections transform both functional and anchor according to their registered representation; invariant functionals remain invariant;
4. physical and measured carriers are not conflated;
5. nuisance projection and response rank come from the actual source-conditioned observation operator;
6. all required covariance blocks are present or explicitly unavailable;
7. joint-set images preserve disconnected/chiral/undefined/unbounded/unresolved strata;
8. injection/coverage/false-positive and leave-one-probe-out gates are passed;
9. scalar x_C ablation demonstrates what information it loses and whether tensor x restores any data-supported, predictive information.

No novelty claim is made from the existence of vector/tensor x, identified-set images, support functions, SO(3)/O(3) actions or depth covariance alone. Those are already part of the repository's prior research. A possible publishable contribution is the validated cosmological source-conditioned operator and a demonstrably useful identifiable tensor-functional quotient built on top of that prior framework.


## 10. Direct physical kinematical theta and likelihood integration

The functional domain is now explicitly enlarged to include the physical kinematical state itself, not only observer-space harmonic carriers. The primary field/coefficient state is

\[
\theta_K=\{\sigma_{ab},\omega_a,A_a,
\beta_{\rm RM}^a,\beta_{\rm MO}^a\},
\]

with the congruence/frame/epoch/triad/units metadata and O(3) representation types defined in KINEMATICAL_LIKELIHOOD_MODEL.md. The observer-frame velocity \(\beta_{\rm RO}\) remains a derived closure view rather than an extra independent three-vector. The optional signed \(\Delta\Omega_k\) and further geometry/matter tensors are distinct extension blocks.

The x registry therefore contains (i) direct identity functionals of every component, (ii) dimensionless copies with declared normalization, (iii) mixed scalar/vector/pseudoscalar/STF functionals of \(\theta_K\), and (iv) predicted observable carriers such as T/E/B harmonics, BipoSH, source-count multipoles, Gaia VSH and distance multipoles. The measured carriers \(d^{\rm obs}\) are fixed source-bound evidence; predicted carriers \(\mathcal O_\alpha(\theta)\) vary over posterior draws or identified-set witnesses. Keep those roles separate to avoid treating derived summaries as independent data.

The end target is the single source-conditioned likelihood \(\mathcal L(\theta,\psi,\eta;D)=p(D\mid\theta,\psi,\eta)\) for \(D=\{a_{\ell m}^{T,E,B},z_i,\hat n_i,F_i,\mu_i,\boldsymbol\mu_i^{\rm Gaia},\ldots\}\), with actual masks/windows/selections and cross-probe dependence. Build one joint posterior or compatibility region; then derive the five HTT outputs x,Q,Pi,F,G_F from that common object. Q is the matching anchor/acceptance body, Pi is a law-conditional exceedance surface, F keeps support/pushforward/occupancy distinct, and G_F is the full-covariance functional depth path. The five outputs are not independent likelihood terms.

See KINEMATICAL_LIKELIHOOD_MODEL.md for the kinematic decomposition, direct and mixed functional examples, CMB/count/SN/Gaia likelihood blocks, covariance treatment, functional-identifiability condition, and falsification/ablation plan. This is a derived design contract; no multi-probe observed likelihood or posterior has yet been produced.
