# Six independent theory loops

## 공통 정의와 컨벤션

Metric signature \((-+++)\), physical four-velocity \(U^aU_a=-c^2\), \(c\) 유지. A named congruence U has projector and kinematics
\[
h_{ab}=g_{ab}+\frac{U_aU_b}{c^2},\qquad
\nabla_bU_a=\frac{\Theta}{3}h_{ab}+\sigma_{ab}+\omega_{ab}-\frac{U_ba_a}{c^2},
\]
where \(\Theta=\nabla_aU^a\), \(a_a=U^b\nabla_bU_a\), \(\sigma_{ab}=D_{\langle b}U_{a\rangle}\), \(\omega_{ab}=D_{[b}U_{a]}\). Observer O, material/source U, homogeneous normal N, and radiation frame R are distinct physical fields. The endpoint redshift is
\[
1+z=\frac{-(U_s\cdot k_s)}{-(O_o\cdot k_o)}.
\]
Define pair-labelled relative Lorentz factors \(\gamma_{OU}=-O\cdot U/c^2=\cosh\chi_{OU}\), \(\gamma_{UN}=-U\cdot N/c^2=\cosh\chi_{UN}\). Do not collapse O/U and U/N into one beta.

---

## L1. Low-\u2113 morphology → physical response observables

**Question.** Which low-multipole temperature/polarization morphology features are actually predicted by local observer boost, radiation stress anisotropy, matter shear or a specified Bianchi history, after processing?

Use a signed real coefficient carrier \(x=\{a_{\ell m}^{T,E,B}\}\) with frame, direction sign, units, bandpass, mask, beam and transfer identity. The observation model is
\[
x_{\rm obs}=\mathcal P_{\rm mask}\mathcal B_{\rm beam}
\mathcal R_{\rm inst}\mathcal L_{O/R}(\boldsymbol\beta)x_{\rm rest}+n.
\]
A boost acts through Doppler-weighted angular remapping before mask/beam processing. First-order boost couples neighbouring multipoles, but Doppler modulation and aberration are non-identical harmonic responses. A dipole amplitude alone is not a complete observer-boost estimator. Polarization screen-basis transport and E/B response require their own convention and operator.

Feature families may include multipole-vector contractions, parity statistics, angular-momentum axes, BipoSH and \(C_\ell^{XY}\), \(TE/TB/EB\). These are correlated summaries of one sky, not independent likelihood factors.

**Candidate new work.** Connect the signed low-\u2113 T/E/B carrier, local boost response and physical shear/Bianchi image under the same processed observation operator and nuisance span. Test whether any component remains outside the nuisance-equivalent boost image. A new morphology scalar by itself is not novelty.

**Falsifiers.** Independent mapmaking/component separation, frequency/detector splits, alternate masks, foreground injections, intensity-to-temperature Doppler leakage, beam/mask mode coupling, same-sky identity, blinded statistics and end-to-end matched simulations. Preserve out-of-model residual.

**Status.** Conditional theory review complete. Existing PR4 Commander MC100 is a C0 E-mode anchor only. Alternate pipeline/T/E/B null replication and Bianchi-linked transfer remain input-gated.

---

## L2. CMB/LSS dipole anomaly

For flux-limited population \(N(>S)\propto S^{-x}\), \(S_\nu\propto\nu^{-\alpha}\), the leading Ellis–Baldwin count dipole is
\[
\mathbf D_{\rm kin}=[2+x(1+\alpha)]\boldsymbol\beta_{OU}.
\]
This is the baseline only under the declared source-count/spectral convention. Observed-redshift selection introduces boost-induced migration across redshift-bin edges. In each tracer/flux/redshift bin b,
\[
\mathbf D_b=\mathbf R_{\beta,b}\boldsymbol\beta_{OU}
+\mathbf D_{{\rm LSS},b}+\mathbf D_{{\rm selection},b}
+\mathbf D_{{\rm calibration},b}+\epsilon_b.
\]
The response must include Doppler, aberration, flux threshold and observed-redshift migration. LSS terms are correlated across windows.

**Candidate new work.** Use an independent CMB aberration anchor and several tracer/redshift windows with different selection slopes and clustering kernels. A local boost is common at the observer; finite-volume structure varies with window; coherent source-frame drift needs its own modeled depth response. Direction alignment alone is insufficient.

**Falsifiers.** Imaging depth, stellar contamination, Galactic extinction, source fragmentation, flux threshold, spectral-index distribution, random catalogues, completeness/fiber assignment, redshift-edge migration, mock covariance, leave-one-tracer-out and count/flux/angular-size consistency. Invalid mock covariance means no p-value.

**Status.** Theory contract complete; literature is rich. DESI DR1 products are public, but the historical PR151 exact-selection covariance was invalidated and must be reconstructed before any significance claim.

---

## L3. Beyond-FLRW covariant kinematics

For a geodesic source congruence, the leading local radial expansion coefficient has monopole plus STF quadrupole:
\[
\mathcal H_U(\mathbf n)=\Theta_U/3+\sigma^{(U)}_{ab}n^an^b.
\]
There is no independent odd dipole in this geodesic leading term. An observed dipole can arise from observer/source acceleration, O/U boost, redshift correction, finite-depth flow or selection. If the source congruence is accelerated, its acceleration response is a separately signed dipole term. The radial symmetric contraction annihilates \(\omega_{ab}\); radial distance data alone do not reconstruct vorticity.

Transverse proper motion adds projected gradient/history response, but frame spin/glide remains a nuisance. Gaia E1/B1 24D, E2/STF5 and CF4 radial response are different carriers until a common source/frame/distance/covariance map exists.

**Candidate new work.** A typed radial+transverse observation map with nuisance quotient, finite-error physical image and explicit estimable target. Do not demand all kinematic components if the detector span lacks them.

**Falsifiers.** PM spin/glide injection, source-distance/history variation at fixed endpoints, radial-only versus radial+PM ablation, frame rotations, distance-method/group folds, finite-z remainder and full cross-covariance.

**Status.** Conditional optical/1+3 results exist in R32/R36/TBO. Same-congruence source law and common frame/source calibration remain blockers.

---

## L4. Anisotropy evaluation and Bianchi classification

Bianchi type is defined by a simply transitive spatial 3D Lie group and structure constants \(C^a{}_{bc}\). Class A/B and types I–IX are not determined by one preferred axis or shear. A family comparison needs invariant-frame geometry, Einstein/Gauss–Codazzi constraints and matter \(q_a,\pi_{ab}\), spatial Ricci and electric/magnetic Weyl response.

For physical family k, map its model/IC/history set through one common observation operator to \(\mathscr R_k(\theta)\). Compare compatible images and keep the out-of-family residual. Two listed templates may both be inadequate.

**Candidate new work.** Family-compatible sets with common physical-error image and invariant response bundle \((\sigma,E,H,q,\pi)\), explicitly coupled to validated transfer and processing. Scalar Ricci can distinguish some geometry pairs; no universal tensor-superiority claim follows.

**Falsifiers.** Constraint residuals, passive frame/triad transforms, orientation, FLRW-limit overlap, boundary sequences, out-of-family perturbations, matter/tilt variants and T/E/B transfer sensitivity.

**Status.** Existing finite geometry results are supplied-geometry witnesses. Native low-\u2113 Bianchi T/E/B Boltzmann transfer remains absent; sky-family identification is blocked.

---

## L5. Redshift/direction-dependent Hubble factor

A generic truncated luminosity-distance chart is
\[
d_L(z,\mathbf n)=\frac{cz}{\mathcal H_0(\mathbf n)}
\left[1+\frac{1-\mathcal Q(\mathbf n)}{2}z+O(z^2)\right],
\]
only after redshift/distance, source congruence, observer frame, direction, optical reciprocity, calibration and finite-distance remainder are specified. Observer-dependent cosmography shows that Hubble multipoles transform under boosts; standard H(z,dL) formula needs correction outside the matter frame.

In the geodesic matter frame the local leading term has monopole plus shear quadrupole. Observer boost/acceleration adds frame-dependent odd multipoles. Higher-z evolution also contains line-of-sight flow, focusing, curvature, lensing and selection.

**Candidate new work.** Redshift-windowed monopole/dipole/STF2 with full window covariance and exact zHEL/zCMB/zHD mapping. Avoid hemisphere H0 fits and do not treat zHD as independent heliocentric depth.

**Falsifiers.** Redshift-edge changes, PV floor, SN survey/calibrator splits, CF4 method/group splits, calibration/Malmquist, correlated PV, window leave-one-out, distance/redshift frame perturbations, opacity/reciprocity and finite-z remainder.

**Status.** Conditional CF4/Pantheon+ products exist, not an absolute physical H0 dipole. Retained low-z Pantheon+ and cosmic-chronometer windows do not overlap enough for a direct low-z CBL result.

---

## L6. Local observer boost versus global material tilt

The two physical axes are
\[
\beta_{OU}^2=1-\gamma_{OU}^{-2},\qquad
\beta_{UN}^2=1-\gamma_{UN}^{-2},\qquad
\gamma_{XY}=-X\cdot Y/c^2.
\]
The four combinations \((U=N,O=U)\), \((U=N,O\ne U)\), \((U\ne N,O=U)\), \((U\ne N,O\ne U)\) are kinematically possible. CMB primarily constrains O/R, matter radial/PM may constrain O/U, whereas U/N needs an independently defined normal/geometry/dynamics. Finite-volume bulk flow is a windowed stochastic statistic, not homogeneous tilt.

### Local nuisance-quotient theorem

Let d be one stacked observable vector with resolved positive-definite covariance C, linearized physical response Rθ, nuisance response Nη, and target Lθ. Define
\[
R_w=C^{-1/2}R,\quad N_w=C^{-1/2}N,\quad
P_N=I-N_wN_w^+,\quad A=P_NR_w.
\]
Then Lθ is locally estimable iff
\[
\ker A\subseteq\ker L
\quad\Longleftrightarrow\quad
\operatorname{rank}\begin{pmatrix}A\\L\end{pmatrix}=\operatorname{rank}(A).
\]
Proof: Av=0 means θ and θ+v yield the same nuisance-quotiented mean. The target is invariant across all such representatives iff Lv=0 for every v in ker A. This is local linear estimability, not global nonlinear identification or calibrated model selection.

For nonlinear competitors compare their images under the same selection/covariance/nuisance/remainder. If images overlap, or the requested target varies along a kernel, return an identified set or ABSTAIN. Gaussian noise distributions have common support; mean-image distance alone is not a perfect classifier. Power/FPR calibration is required.

### Finite-volume bridge

A measured bulk flow \(v_W=\int d^3x\,W(\mathbf x)v(\mathbf x)\) is a windowed random variable. Relating it to homogeneous tilt requires velocity covariance/power spectrum, window, selection, gauge/frame and history, e.g. \(p(v_W\mid\beta_{UN},\mathrm{history})\). One finite-volume realization cannot be renamed homogeneous tilt.

**Falsifiers.** Boost-only, coherent source drift-only, tilt+boost, shear-only, systematics-only, mixtures and confusable cases; redshift/tracer holdouts; same-sky/covariance tests; finite remainder; out-of-family residual; abstention calibration.

**Status.** Exact endpoint/pairwise theory exists conditionally in TBO/PR-194. Source-bound multi-probe response, held-out calibration and finite-volume bridge are not observationally complete.
