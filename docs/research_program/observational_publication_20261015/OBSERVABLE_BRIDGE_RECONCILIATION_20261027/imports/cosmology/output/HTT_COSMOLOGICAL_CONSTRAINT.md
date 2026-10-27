# From observed sky multipoles to a calibrated radiation-stress constraint

Internal corrective research note, 26 October 2026. This note redirects the preceding v15 extension toward the user's cosmological inference programme. The target is a physical constraint constructed from observed sky coefficients and kinetic moments. Angular Calculus is used as the calibration and uncertainty interface. Its independent mathematical novelty is not the research target here.

The completed result is an exact, finite-boost radiation-stress null, its nonlinear low-multipole representation, and a finite-error exclusion certificate. Static computations verify the formulae. No measured CMB fit or transport evolution is performed; previous internal reports and original campaign acceptance remain unchanged.

## 1. Keep the four axes separate

| Axis | Object and operation | Interpretation retained here |
|---|---|---|
| Symmetry, gauge and degrees of freedom | Passive sky-triad rotations, spacetime coordinate freedom, and observer choice are distinguished. Generic STF2 plus STF3 has 12 real components and a 9-dimensional SO(3) quotient. | A boost changes the physical observer; it is not three redundant sky coordinates. Statistical nuisance removal is not a spacetime gauge transformation. |
| Invariants | STF traces and powers are rotation scalars. Eigenvalues of the mixed radiation tensor and its rest-frame stress scalar are Lorentz scalars on the specified branch. | State the transformation group. Rotation invariance alone does not remove observer motion or determine geometry. |
| Observables | Calibrated frequency-channel maps, realized harmonic coefficients, beam/mask response and their joint measurement law. | A coefficient C_lm differs from an angular power C_l. A fitted thermodynamic temperature is not automatically a full bolometric energy temperature. |
| Physical quantities | Radiation energy, energy flux, pressure and anisotropic stress at an event; separately, matter shear, vorticity and curvature. | The first group is recovered from calibrated kinetic moments. The second needs a transport/optical/dynamical response. Equal tensor rank is not a physical identification. |

The radiation tensor has nine independent components: a symmetric four-tensor has ten and its massless trace vanishes. At fixed positive energy density its observer decomposition has three flux and five STF stress components. A perfect-radiation tensor has four parameters: one rest energy and three velocity components. Thus its null imposes five constraints on the nine-dimensional radiation-tensor space. This count describes the model submanifold; it is not a gauge quotient or an automatically valid chi-square calibration.

## 2. The observable-to-moment adapter

Use signature \((-+++ )\), \(U^2=-c^2\), outward sky direction \(n\) and photon propagation \(e=-n\). Define a field-labelled harmonic coefficient
\[
C^X_{\ell m}=\int X(n)Y^*_{\ell m}(n)\,d\Omega,
\qquad \int |Y_{\ell m}|^2d\Omega=1.
\tag{1}
\]
Let I be physical bolometric energy density per solid angle. Spectral radiance must first be integrated and divided by c. The photon moments are
\[
J_{A_\ell}=(-1)^\ell\int I(n)n_{\langle A_\ell\rangle}\,d\Omega,
\quad \rho=J,\quad q_a=cJ_a,\quad \pi_{ab}=J_{ab}.
\tag{2}
\]
Writing \(Y_{\ell m}=\mathcal Y^{\ell m}_{A_\ell}n^{A_\ell}\) gives
\[
J_{A_\ell}=(-1)^\ell\Delta_\ell\sum_m C^I_{\ell m}\mathcal Y^{\ell m}_{A_\ell},
\qquad \Delta_\ell=\frac{4\pi\ell!}{(2\ell+1)!!}.
\tag{3}
\]
The detailed convention note supplies the inverse and metric-sign adapters. In the Lewis–Challinor hierarchy adopted by v15,
\[
J^{(i)}_{A_\ell}=\int E v^{\ell+2i}e_{\langle A_\ell\rangle}f\,d\nu_U,
\qquad v=\frac{cq}{E},\quad E^2=m^2c^4+c^2q^2.
\tag{4}
\]
Their total velocity degree is n=ell+2i. For photons v=1, all i coincide at a given angular rank. Additional spectral energy moments require their own kernels; they are not new independent photon velocity moments obtained by relabelling i. CMB measurements also do not supply a massive neutrino hierarchy through substitution.

For the v15 energy-calibrated photon temperature T_E, including a nonthermal spectrum with the same ray energy,
\[
I=C_\gamma T_E^4,\qquad C_\gamma=\frac{\pi k_B^4}{60\hbar^3c^3}.
\tag{5}
\]
Thus all coefficients enter through the exact polynomial (1+Theta)^4. Ordinary Planck component-map temperatures can be used this way only with their spectral calibration and completion error specified. The v15 lift preserves a known ray energy and hence its stress exactly. It cannot tighten an already exact bolometric stress measurement merely by assigning a temperature.

## 3. A physical null that removes the stress induced by an arbitrary boost

In an orthonormal observer tetrad, write the contravariant radiation tensor as
\[
T^{\mu\nu}=\rho
\begin{pmatrix}1&f_j\\f_i&\delta_{ij}/3+P_{ij}\end{pmatrix},
\qquad f_a=\frac{q_a}{c\rho},\quad P_{ab}=\frac{\pi_{ab}}\rho,
\quad P^a{}_a=0.
\tag{6}
\]
Here rho, T and pi have energy-density units; f and P are dimensionless. The flux f is unrelated to the HTT F diagnostics. For positive non-beam radiation, rho>0 and |f|<1. The positive-intensity moment cone also imposes constraints on P, which must be retained in the measurement image.

**Proposition: exact perfect-radiation stress criterion.** Under rho>0 and |f|<1, (6) is a positive perfect-radiation stress tensor in some timelike rest frame if and only if
\[
\boxed{\mathscr D_{ab}=P_{ab}-G_{ab}(f)=0,\qquad
G_{ab}(f)=\kappa(f^2)f_{\langle a}f_{b\rangle},\quad
\kappa(s)=\frac3{2+\sqrt{4-3s}}.}
\tag{7}
\]
This is an algebraic application of the perfect-fluid Lorentz transformation. It tests the radiation stress tensor, not microscopic isotropy of the entire sky or spectrum.

**Proof.** Here beta is the dimensionless velocity of the radiation energy frame measured in the chosen observer tetrad, using the active +beta matrix convention of the toy. The chosen observer's velocity measured in that rest frame has the opposite sign. A rest tensor diag(rho_L,rho_L/3,rho_L/3,rho_L/3), transformed with this convention, has
\[
\rho=\rho_L\frac{3+\beta^2}{3(1-\beta^2)},\qquad
f=\frac{4\beta}{3+\beta^2},\qquad
P=\frac4{3+\beta^2}\beta_{\langle a}\beta_{b\rangle}.
\tag{8}
\]
The subluminal root of the flux equation is beta=kappa(f squared) f. Substitution gives (7). Conversely, this beta is subluminal for |f|<1; choosing rho_L=3rho(1-beta squared)/(3+beta squared)>0 reconstructs every component of (6). This proves sufficiency as well as necessity. The limiting value at f=0 is kappa=3/4. A pure null beam lies at the excluded |f|=1 boundary and has no such timelike radiation rest frame.

The vanishing of script-D is an observer-independent property of T, while its nonzero norm generally depends on the observer. For an actual Lorentz-scalar strength, take the unique future timelike eigenvector of the mixed tensor T^mu_nu, with eigenvalue -rho_L, and its three rest-pressure eigenvalues p_i. Then
\[
\mathcal A_\gamma=\frac{[\sum_{i=1}^3(p_i-\rho_L/3)^2]^{1/2}}{\rho_L}.
\tag{9}
\]
This is the normalized anisotropic stress in the radiation energy frame. It is invariant under a change of observer and under coordinates at the same event. Existence of the unique timelike eigenbranch and positive rho_L are part of its domain. Direct pressure differences are numerically preferable to subtracting nearly equal quadratic invariants. A_gamma=0 establishes a perfect stress tensor; a pure octupole or other higher angular structure may still be present. The radiation energy frame is not automatically the matter frame or a global cosmological rest frame.

## 4. What low-ell morphology contributes to that physical constraint

Let the energy-temperature contrast have no monopole and, for this expansion, contain only ranks one through three:
\[
\Theta(n)=d_an^a+Q^T_{ab}n^an^b+O^T_{abc}n^an^bn^c,
\qquad d,Q^T,O^T=O(\epsilon),\quad \|\Theta\|_\infty<1.
\tag{10}
\]
Exact angular integration of (5), followed by normalization by the actual rho, gives
\[
\begin{aligned}
P_{ab}={}&\frac8{15}Q^T_{ab}+\frac45d_{\langle a}d_{b\rangle}
+\frac{24}{35}d^cO^T_{abc}\\
&+\frac{16}{35}Q^T_{c\langle a}Q^{T\,c}_{b\rangle}
+\frac8{35}O^T_{\langle a|cd|}O^{T\,cd}_{b\rangle}
+O(\epsilon^3).
\end{aligned}\tag{11}
\]
The outward-direction convention gives f=-4d/3+O(epsilon squared). Subtracting (7) therefore produces
\[
\boxed{\begin{aligned}
\mathscr D_{ab}=\frac8{15}\big[&Q^T_{ab}-d_{\langle a}d_{b\rangle}
+\frac97d^cO^T_{abc}\\
&+\frac67Q^T_{c\langle a}Q^{T\,c}_{b\rangle}
+\frac37O^T_{\langle a|cd|}O^{T\,cd}_{b\rangle}\big]
+O(\epsilon^3).
\end{aligned}}\tag{12}
\]
The pairing proof of the coefficients is in CONVENTIONS.md. The denominator has no first-order correction because the temperature monopole is removed. Higher temperature modes, if present, contribute additional products; the practical estimator should use the exact map rather than silently imposing (10).

Equation (12) gives relative low-multipole orientation a physical role: dipole–octupole and quadratic tensor contractions contribute to a stress-level departure from every boosted perfect-radiation tensor. Separate C_1, C_2 and C_3 powers cannot recover these tensors or their joint covariance. The Gaunt couplings are established mathematics; the application target is their calibrated joint physical constraint. At CMB-sized perturbations, many corrections are small, so practical importance must be demonstrated against actual calibration and foreground errors rather than inferred from formal nonlinearity.

## 5. A finite-error statistical certificate

Suppose one valid joint measurement event bounds
\[
\|\widehat P-P\|_F\le e_P,\qquad
\|\widehat f-f\|_2\le e_f,\qquad
\|f\|,\|\widehat f\|\le r<1.
\tag{13}
\]
It may come from a joint likelihood or a confidence region including calibration, foregrounds, masks and spectral completion. Marginal error bars do not automatically give this joint event.

Differentiating G in direction h gives
\[
DG_f[h]=\kappa\,\mathrm{STF}(hf^T+fh^T)
+2\kappa'(f^2)(f\cdot h)\mathrm{STF}(ff^T),
\quad\kappa'(s)=\frac9{2\sqrt{4-3s}(2+\sqrt{4-3s})^2}.
\tag{14}
\]
Since ||STF(ff)||=sqrt(2/3)|f| squared and the ball is convex,
\[
L_G(r)=2\kappa(r^2)r+2\sqrt{2/3}\kappa'(r^2)r^3,
\quad\|\widehat{\mathscr D}-\mathscr D\|_F\le e_P+L_G(r)e_f=:e_D.
\tag{15}
\]
**Hence ||Dhat||>e_D excludes the perfect-radiation stress null on event (13).** If that event has uniform coverage at least 1-alpha, the rule has type-I error at most alpha. This coverage argument is standard confidence-set mapping; (7) and (15) provide its explicit physical target and finite uncertainty propagation. A sharper implementation tests intersection of the full joint confidence set with (7), preserving correlations and the positive moment cone.

For a local Gaussian approximation, the five-component STF Jacobian gives
\[
V_D=V_{PP}+DG_fV_{ff}DG_f^T
-V_{Pf}DG_f^T-DG_fV_{fP}.
\tag{16}
\]
Using a chi-square law additionally requires the stated Gaussian/rank/linearization conditions or simulation calibration. A confidence region can instead be pushed through the exact eigenvalue map (9) to obtain a bound on A_gamma with inherited coverage. No entropy defect is used as a p-value or an observational covariance.

## 6. Where v15 and tensorized HTT change the analysis

The shared physical carrier X contains the calibrated moments and nuisance state. Its sample-by-functional array x can now include rho, f, P, script-D, the radiation-frame pressure eigenvalues and A_gamma. Rotational invariants are computed after the same joint map, preserving relative orientation and common errors.

For finite spectral channels, v15's energy-matched lift and response residuals organize which moment combinations are observed and which need a spectral completion bound. The preceding entropy-response construction can bound unmeasured kernel directions if its entropy/tail allowance is physically supplied. Equal ray energy already means equal stress: unresolved spectral entropy should not be added again as an independent stress error. Missing-sky and beam errors enter their actual observation operators.

HTT Q remains a Minkowski gauge relative to a declared physical tolerance body, not a spacetime gauge. The zero null in (7) has zero support and cannot serve as a positive denominator. F_sup can compare the joint identified image with a nondegenerate, declared radiation-stress tolerance body; it must not silently reuse a matter-shear MES radius. Pi requires a named sampling/posterior law and a named event. G_F needs actual cross-window data and coupling; the radial moment index i is not a redshift coordinate. F_cert and measure-occupancy F_nu retain their separate old definitions.

The new cosmological objective is therefore a joint constraint on radiation stress beyond an observer boost, with a separately reported invariant strength A_gamma. A later matter-shear constraint can consume the same calibrated brightness through the previous equation L_I sigma=-R. The radiation derivative/transport residual R and its covariance remain an additional physical measurement/model input; no instantaneous harmonic statistic supplies it.

## 7. Executed checks and scientific decision

The Wolfram evaluator returned two exact zeros for the inverse-velocity and stress-null identities. Python checks arbitrary boost and rotation controls, the finite-error Lipschitz estimate, and cubic convergence of the low-multipole expansion. The figure uses analytical radiation states I proportional to 1+a P_2, with rest stress A_gamma=sqrt(6)|a|/15. It includes a pure-boost control and a nonzero rest stress whose invariant value is unchanged as the observer moves.

For the declared CMB-scale toy \(a=2\times10^{-5}\), relative observer speed \(0.00123\), \(e_P=5\times10^{-7}\) and \(e_f=10^{-5}\), the residual norm is \(3.2659764\times10^{-6}\), its finite error bound is \(5.2475006\times10^{-7}\), and the positive lower bound is \(2.7412264\times10^{-6}\). The invariant rest-stress strength is \(\mathcal A_\gamma=3.2659863\times10^{-6}\). These error radii are specified toy inputs, not estimated Planck uncertainties. This checks the inference mechanism without presenting a new observational detection.

**Result status:** the exact physical null, its nonlinear representation and the finite-error certificate are DERIVED and NUMERICALLY CHECKED within their domains. Their ingredients—perfect-fluid boosts, STF/Gaunt algebra and confidence-set propagation—are established. The project contribution candidate is a usable joint cosmological constraint with nonlinear conversion, spectral/observer calibration and explicit invariant interpretation. It becomes a convincing independent methods result only after a common-input coverage/constraint comparison against the linear temperature-quadrupole method. The next decisive application is that controlled comparison on released multichannel low-ell products, followed by the A_gamma interval; it does not require building a Boltzmann solver.

Sources: the two supplied Angular Calculus v15 papers; the prior five-loop report, especially A/B/C; Maartens–Gebbie–Ellis (1999), [astro-ph/9808163](https://arxiv.org/abs/astro-ph/9808163); Lewis–Challinor (2002), [astro-ph/0203507](https://arxiv.org/abs/astro-ph/0203507); the attached Ellis–Maartens–MacCallum text §§4–5; the closest low-ell likelihood and dynamical-shear comparators recorded in FOUR_AXES.md. The original HTT statistical meanings are bound to the previous report §§23.1–23.4 and its inspected implementation.


\begin{center}\includegraphics[width=\textwidth]{/workspace/scratch/ef61c9590364/HTT_COSMO_TEFF_REFOCUS_20261026/figures/radiation_stress_constraint.pdf}\end{center}

**Figure.** The observer-resolved stress changes under a boost; the radiation-rest invariant is constant. The final panel shows the finite-error certificate for the declared CMB-scale toy. No measured sky or fitted Planck error model is used.


\clearpage

# Two retained applications: polarization morphology and optical kinematics

The same tensorized inference programme can consume different physical carriers without identifying them. This addition joins the user's Planck example and Hubble-diagram inverse to the radiation-stress construction. The relevant current carrier is
\[
X=(Q_E,O_E;\ \rho_\gamma,f_\gamma,P_\gamma;\ d,S,O_\mu;\ \eta),
\]
where semicolons distinguish polarization morphology, intensity stress, optical kinematics and their joint nuisances. Each channel has its own observation map, invariant group and error body. Cross-channel physical conclusions require an explicit response connecting them.

## 1. The Planck example is a measured morphology result

The retained report's pinned-primary PR3 E-mode row, processing cutoff 32, secondary window 0 degrees, FULL product, gives

| Quantity | Retained value |
|---|---:|
| Quadrupole shape r | 0.0582918 |
| Signed chirality C | -0.0967707 |
| Fixed-shape envelope E(r) | 0.808141 |
| Envelope utilization U | 0.1197448 |

Here \(r=j^2/t^3\), \(t=\mathrm{tr}Q_E^2\), \(j=\mathrm{tr}Q_E^3\), and
\[
E(r)^2=(1-6r)(1+3r/40),\qquad U=|\mathcal C|/E(r).
\tag{P1}
\]
The fields analysed are degrees two and three of a processed polarization E pseudo-harmonic product; 32 is its processing cutoff. The values were verified against the pinned report, not by re-extracting the original maps during this loop. The cached-pilot row is a different source and is not substituted.

**A fresh ideal Gaussian benchmark.** Conditional on any simple-spectrum quadrupole, an independent isotropic Gaussian STF3 octupole has a uniform normalized direction on the seven-dimensional Frobenius sphere. Diagonalizing its three-dimensional contraction image and dividing by the sharp envelope gives
\[
U\ \overset{d}{=}\ 3\sqrt3\,|z_1z_2z_3|,\qquad z\sim\operatorname{Unif}(S^6).
\tag{P2}
\]
The result follows because the three contraction singular values and the quadrupole Vandermonde cancel against that envelope. The remaining four coordinates lie in the contraction kernel. Its moments provide checks:
\[
\mathbb E U=\frac{15\sqrt3}{64\pi},\qquad \mathbb E U^2=\frac3{77}.
\tag{P3}
\]
With seed 20261026 and 1,048,576 draws, 662,397 fall below the displayed U. The estimated CDF is **0.631711**, with binomial Monte Carlo 95% interval **[0.630787,0.632634]**; the upper tail is **0.368289**. This independently supports the proposed approximately 63.1% benchmark. The original historical percentile's receipt was not recovered. Equation (P2) is an ideal Gaussian reference, not a Planck mask/noise/foreground-calibrated probability; random spatial rotation of a fixed octupole is also a different null.

**Sign stability is a separate property.** The retained report uses \(\bar Q=Q_E/q_0\), \(\bar O=O_E/o_0\), with \(q_0=o_0=10^{-5}\,\mathrm K_{CMB}\), and joint full-tensor Frobenius norm \(m^2=\|\bar Q\|^2+\|\bar O\|^2\). For perturbations of norm at most \(\rho_{stab}m\), its sufficient certificate is
\[
\chi^2>36\rho_{stab}^2(1+\rho_{stab})^{16}(m^2)^9.
\tag{P4}
\]
All 60 saved processing carriers pass at \(\rho_{stab}=10^{-6}\); 39 pass at \(10^{-5}\). This is the saved report's certificate, not a newly estimated physical error radius. Each carrier retains its own sign locally; the 60 signs are not all equal, and the carriers are correlated views of one sky. A stable sign may have an ordinary null percentile, as this example does. The accessible compact report numbers (P4) as equation (13); the current R32-01 equation (35) is a different optical sign bound.

On the four axes: the E tensors are rotation-covariant observables; C is a proper-rotation invariant pseudoscalar, U is reflection-even, and (P4) is deterministic local robustness. None alone establishes statistical parity violation. E(n) is not positive bolometric intensity, so substituting it into I=C_gamma T_E^4 would be physically invalid. Its interpretation remains polarization morphology until an appropriate polarized response is supplied.

## 2. The Hubble inverse becomes one joint physical test

The pinned local optical model defines
\[
d=-\frac A{cH},\quad S=\frac\sigma H,\qquad
f_\mu(n)=-\kappa\log[1+d\cdot n+S:nn],\quad\kappa=5/\ln10.
\tag{H1}
\]
Thus d is normalized acceleration of the declared common observer/emitter congruence; it is not the CMB dipole or an arbitrary velocity dipole. S is the directional Hubble-slope quadrupole; the magnitude quadrupole instead obeys Q_mu=-kappa S plus a finite nonlinear remainder. For \(\sup|d\cdot n+S:nn|\le\epsilon<1\),
\[
O_\mu=\kappa L_Sd+R_3,\quad
\|R_3\|\le E_3(\epsilon)
=\sqrt{35/2}\frac{\kappa\epsilon^3}{3(1-\epsilon)},
\quad M_S=L_S^*L_S=\frac{S:S}{3}\mathrm{Id}+\frac25S^2.
\tag{H2}
\]
The proposed inverse and perpendicular residual are retained. The constructive repair is to preserve their **shared** error budget. For fixed measured \(\widehat S\ne0\), a joint event with \(\|S-\widehat S\|\le e_S\), \(|d|\le D_{max}\) permits
\[
B=E_3+e_O+B_z+B_{sel}
+|\kappa|\sqrt{3/5}\,e_SD_{max}.
\tag{H3}
\]
The last term follows from \(\|L_{S-\widehat S}\|\le\sqrt{3/5}e_S\). Error ownership must prevent double counting. The finite-distance order also needs correction: \(d_L=cz/\mathcal H+O(z^2)\) generally gives an **O(z) magnitude correction**. An O(z squared) magnitude remainder requires the first correction to be modeled or removed. Selection and frame terms are separately bounded by their actual response.

For an exact direct estimate d_obs, the key identity is
\[
\begin{aligned}
\|\widehat O-\kappa L_{\widehat S}d_{obs}\|^2
={}&\|\widehat O_\perp\|^2\\
&+\kappa^2(\widehat d-d_{obs})^TM_{\widehat S}
(\widehat d-d_{obs}).
\end{aligned}\tag{H4}
\]
The joint right-hand side must be at most B squared. Separate bounds on the two terms are only necessary. The finite control in the source package has separate normalized scores **0.8 and 0.8**, but joint score **1.13137085**; both separate tests pass while the common model-error ball is missed.

For a direct-vector error ball \(|d-d_{obs}|\le e_d\), use
\[
Q_{joint,min}^2=\frac{\|\widehat O_\perp\|^2+
\kappa^2\min_{|d-d_{obs}|\le e_d}
(\widehat d-d)^TM_{\widehat S}(\widehat d-d)}{B^2}.
\tag{H5}
\]
This is a three-dimensional convex minimization. A value above one rejects the specified joint response/error model. For full correlated data, use the original joint region rather than replacing it by independent balls. Near S=0 use direct response-set testing; the inverse has unbounded absolute gain there. At B=0 test exact membership rather than assigning a ratio.

Agreement means compatibility with the local acceleration–shear response; it does not prove that mechanism alone. Separating finite-redshift, selection and source-frame alternatives requires their distinct registered responses across depth/processing windows, with cross-window covariance. This is the appropriate role for the existing G_F machinery.

## 3. Revised contribution target

The coherent paper target is a **response-qualified tensor statistical analysis**: retain the measured Planck morphology and its deterministic stability, infer radiation stress from intensity moments through v15, and test the optical acceleration–shear image with one shared uncertainty budget. The same mathematical tensor operations serve three different carriers. Their invariants and physical meanings remain typed throughout.

The new ideal U benchmark and shared-budget test are completed constructions. A claim of improved cosmological constraints needs a common-data comparison with existing estimators and calibrated processing/noise models. The next short observational step is to supply those joint input products, not to build a native Boltzmann solver or to identify Bianchi geometry from an E-mode chirality score.


\begin{center}\includegraphics[width=\textwidth]{/workspace/scratch/ef61c9590364/HTT_COSMO_TEFF_REFOCUS_20261026/figures/planck_hubble_controls.pdf}\end{center}

**Figure.** Left: a fresh ideal Gaussian reference for the retained Planck morphology value. Right: two separate compatibility scores can both pass while their shared joint error budget fails. These controls retain different carriers and nulls. Detailed independent review records accompany the source package.
