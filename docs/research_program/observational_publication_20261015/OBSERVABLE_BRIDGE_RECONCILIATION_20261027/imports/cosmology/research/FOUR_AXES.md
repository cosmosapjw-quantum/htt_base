# Four distinct axes for cosmological inference with v15

26 October 2026 · internal R3/R4 corrective note · no push, source edit or solver. V15 Angular Calculus is a tool for constructing cosmological statistical constraints from realized sky coefficients and kinetic moments. Its mathematical novelty is a separate question. This note aligns definitions and proposes one bounded inference target; it does not execute a full research loop.

Write \(c_{\ell m}\) for the user's realized sky coefficients \(C_{\ell m}\), and reserve \(C_\ell\) for an ensemble angular power spectrum. A realized coefficient, a rotational invariant of those coefficients, a physical stress tensor and a likelihood parameter are different objects.

## 1. Symmetry/gauge, invariants, observables and physical quantities

| Transformation or uncertainty | Symmetry/gauge and degrees of freedom | Invariants | Observables | Physical quantities |
|---|---|---|---|---|
| Spatial sky rotation \(R\in SO(3)\) | Passive triad relabelling rotates sky, masks and reference axes together. A generic STF2⊕STF3 pair has 12 real components and a 9-dimensional rotation quotient. Stabilizers change exceptional-orbit dimensions. | Powers, STF traces, mixed contractions and proper-rotation chirality. Two powers alone do not characterize the 9-dimensional quotient. Reflection is additional parity, not an automatic SO(3) redundancy. | Harmonic coefficients transform by Wigner matrices; external-axis or mask-relative orientations must be retained when relevant. | Radiation stress and shear each transform as tensors, but sharing an STF2 representation does not identify them. |
| Lorentz change of observer \(U\to U'\) | Three local boost parameters specify a physically different measurement. They are not three sky-coordinate redundancies to subtract from a fixed-observer state. Observer and matter congruences must be named. | Scalar phase-space occupation at the same momentum-space point; spacetime tensor contractions when all arguments transform. Sky power and \(\pi_{ab}\pi^{ab}/\rho^2\) relative to an observer are not generally boost invariant. | Photon energy, angular direction, spectrum and all inferred multipoles change together. Incoming sky direction is \(n=-e\), opposite photon propagation. | Observer-resolved \(\rho,q,\pi\) mix under boosts. Radiation energy frame, matter frame and statistical-isotropy frame are distinct definitions. |
| Spacetime diffeomorphism / perturbative gauge | Coordinate relabelling changes components, not a geometrical event or relational observation. Perturbative changes of slicing change the background–perturbation split. They do not erase physical shear or radiation stress. | Covariant scalars at the same physical event; properly defined relational light-cone observables. A background-referenced perturbation need not itself be gauge invariant. | Measured frequency ratios, angles and distances are tied to source/observer worldlines; component formulas require that identification. | \(T_{ab}\), \(\nabla_aU_b\), curvature and their specified projections. Field equations and transport connect these separate tensors. |
| Statistical nuisance: gains, beam, foregrounds, mask, velocity uncertainty | Uncertain parameters or competing responses, not generally a physical gauge group. Marginalization, profiling and nuisance-image projection are different operations. | An estimable functional must survive the chosen nuisance model; no universal nuisance-invariant statistic is assumed. | Calibrated channel maps, fitted coefficients, joint covariance/noise law and selection support. | Uncertainty in the inferred physical state. Projection can remove information about a physical component; it does not remove that component from nature. |

For one quadrupole alone, \(\operatorname{tr}(Q_T^2),\operatorname{tr}(Q_T^3)\) determine its unordered eigenvalues. They do not determine its orientation relative to another field. For a quadrupole–octupole pair, mixed invariants preserve information discarded by \(\widehat C_2,\widehat C_3\). Power-spectrum sufficiency holds for a specified Gaussian statistically isotropic likelihood under its observation assumptions; it is not a consequence of rotational invariance alone. The primary low-multipole likelihood discussion in Benabed et al. explicitly distinguishes the ideal full sky from mask/nonstationary-noise coupling.

## 2. The actual observational-to-physical map

V15 fixes \(U^2=-c^2\) and supplies a reconstruction/calibration of \(f(E,e;U)\). Its \((T,\mu)\) fields are not a preferred-observer selection. A usable cosmological inference has the form
\[
 y_r=\mathcal M_r[f,U,\eta]+\epsilon_r,
 \qquad c_{\ell m}=\int T_{\rm fit}(n)Y^*_{\ell m}(n)\,d\Omega,
\]
\[
 J^{(n)}_{\langle A_\ell\rangle}
 =\int K_{n\ell}(E,m)e_{\langle A_\ell\rangle}f\,d\nu_U.
\tag{1}
\]
Here \(\eta\) contains the declared calibration/foreground variables; \(K_{n\ell}\) fixes which moment hierarchy is meant. In the Lewis–Challinor convention used by v15, \(K_{n\ell}=Ev^{\ell+2n}\), \(v=cq/E\). Then \(\rho=J^{(0)}\), physical energy flux is \(cJ_a^{(0)}\), anisotropic stress is \(\pi_{ab}=J_{ab}^{(0)}\), and isotropic pressure is \(J^{(1)}/3\). All these moments have energy-density units before the flux factor \(c\).

For exactly Planckian photon rays, \(I(e)=C_\gamma T(e)^4\), \(C_\gamma=\pi k_B^4/(60\hbar^3c^3)\), and \(\pi_{ab}=\int I(e)e_{\langle a}e_{b\rangle}d\Omega\). Thus Gaunt products map temperature coefficients into brightness moments; temperature quadrupole alone equals stress only at an explicitly linearized order. For spectrally distorted rays, use the actual energy-weighted spectrum. V15's energy-matched thermal lift preserves that ray energy, hence preserves its stress exactly: a spectral entropy residual is not automatically an additional stress residual.

Shear is instead \(\sigma_{ab}=\nabla_{\langle a}u_{b\rangle}\), \(u=U/c\), with inverse-length units. Earlier Loop A supplies the conditional transport equation \(\mathcal L_I\sigma=-R\), including independent temporal/spatial radiation derivatives in \(R\). An instantaneous sky measures neither those derivatives nor shear merely by giving \(J_{ab}^{(0)}\). Rotational invariants of \(\pi\) and \(\sigma\) remain invariants of different physical objects.

## 3. Preserve the meanings of HTT diagnostics

| Name | Defined object | What must accompany its cosmological use |
|---|---|---|
| \(x\) | Named scalar functional or retained sample-by-functional array. Legacy \(x_C=\Sigma^2-W^2+\Omega_{\rm tilt}+\Delta\Omega_{k,\rm aniso}\) is a signed comparator in its stated convention. | Physical forward map, normalizations and sector assumptions; it is not a universal anisotropy norm. |
| \(Q\) | Premise-anchor Minkowski gauge/margin, e.g. \(\gamma_\mathcal B(X)=\inf\{t:X\in t\mathcal B\}\), or a separately specified response score. | Body, origin, channel and denominator/domain. “Gauge” here is a convex-body functional, not spacetime gauge. Distinguish \(Q_T\), the temperature quadrupole tensor. |
| \(F_{\rm cert}\) | \(x_C/U_{\rm ceiling}\) in the sign-clean certified-ceiling sector. | Applicable ceiling and sign premises; it is ceiling utilization. |
| \(F_{\rm sup}\) | Directional support utilization, such as \(h_\mathcal I(s)/h_\mathcal B(s)\); current pointwise implementation can use a signed directional difference. | The actual set/point version, direction, positive support denominator and finite direction grid. |
| \(F_\nu\) | \(\nu(B\cap D)/\nu(D)\), when \(0<\nu(D)<\infty\). | Defined domain, occupied event and measure. Only a justified physical spatial measure makes this a material-volume fraction. |
| \(\Pi\) | \(P\{\phi(X)>t\mid\eta\}\), or a named partial-identification envelope over nuisance choices. | Joint law, event and conditioning. Neither an optimizer nor a support set supplies probability. Distinguish lowercase stress \(\pi_{ab}\). |
| \(G_F\) | Registered depth/window transport and coherence functional. | Actual windows, feature transport, shared calibration and cross-window covariance. Persistence with depth alone does not identify global tilt. |

These definitions are source-bound: the 36-page report §§23.1–23.4 and the current source audit distinguish the three \(F\) namespaces. They are not competing numerical definitions of one physical occupancy.

## 4. One narrow cosmological inference candidate

**Target:** a joint, observer-qualified confidence constraint on CMB radiation anisotropic stress
\[
 \mathcal A_\pi(U)=\frac{\sqrt{\pi_{ab}(U)\pi^{ab}(U)}}{\rho_\gamma(U)},
\tag{2}
\]
using realized multichannel \(c_{\ell m}\), with observer velocity and unresolved spectral/sky contributions retained jointly. The four axes are explicit: spatial rotations are representation redundancy; (2) is their scalar invariant; maps and coefficients are observations; \(\pi\) is physical radiation stress. Changing \(U\) changes the target, so the selected observer must be stated or its uncertainty included.

Two exact controls anchor the construction. Positive brightness implies \(0\le\mathcal A_\pi\le\sqrt{2/3}\), since the normalized raw second moment is positive semidefinite with trace one. An isotropic radiation field seen under a boost has \(\mathcal A_\pi=4\sqrt{2/3}\,\beta^2/(3+\beta^2)\). Thus a nonzero measured stress invariant can be entirely observer-induced; rotational invariance does not remove that contribution.

Construct one confidence region \(\mathcal C_\alpha\) for the calibrated map/spectrum, observer and nuisances under a valid joint sampling law, with declared band/tail and missing-sky assumptions. Push that same region through (1):
\[
 [A_-,A_+]=\left[\inf_{z\in\mathcal C_\alpha}\mathcal A_\pi(z),
                   \sup_{z\in\mathcal C_\alpha}\mathcal A_\pi(z)\right].\tag{3}
\]
If the true joint state lies in \(\mathcal C_\alpha\) with probability at least \(1-\alpha\), its stress functional lies in (3) with at least that coverage. This familiar confidence-set mapping is the statistical mechanism, not a new theorem. The candidate contribution is a quantitatively useful **physical moment constraint** with nonlinear temperature conversion, explicit observer response and calibrated missing-information bounds, rather than another invariant morphology score.

Nearest precedents are Maartens–Gebbie–Ellis (1999), [astro-ph/9808163](https://arxiv.org/abs/astro-ph/9808163), for nonlinear radiation moments; the thermal/blackbody Gaunt and mixing literature already compared in v15; Benabed et al., [DOI 10.1111/j.1365-2966.2009.15202.x](https://doi.org/10.1111/j.1365-2966.2009.15202.x), for low-\(\ell\) likelihood construction; and Saadeh et al. (2016), [1605.07178](https://arxiv.org/abs/1605.07178), for actual model-dependent cosmological shear constraints from CMB temperature/polarization. The latter uses dynamical anisotropic templates and a full likelihood; (2) targets local radiation stress and does not inherit their shear interpretation.

The first decisive test is an injected-sky joint-coverage experiment comparing (3) with a linear temperature-quadrupole conversion under identical masks, bandpasses, observer uncertainty and covariance. Include a pure-boost thermal control and a nonthermal control with the same directional energy. The latter must give the same true stress despite different spectral entropy. Proceed to measured maps only if the new interval has calibrated coverage and materially differs where the simple approximation fails. Novelty remains a specific statistical-constraint hypothesis until that comparison is performed. A later shear constraint additionally needs \(R\), its joint errors and the chosen transport branch; it is a separate physical target.

Sources reused: supplied v15 I/II, earlier five-loop synthesis and A/B notes, and source-exact HTT diagnostic definitions. Exactly two targeted new primary searches were used: low-\(\ell\) moment likelihoods and the Saadeh cosmological shear analysis. The latter's abstract and primary-method search excerpts were read; no new claimed numerical constraint was extracted. This completes the requested R3 alignment and R4 candidate construction only.
