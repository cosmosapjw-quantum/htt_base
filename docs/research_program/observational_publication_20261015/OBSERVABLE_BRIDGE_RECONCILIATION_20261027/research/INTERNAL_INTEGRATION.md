# Internal results integrated with the observable-bridge programme

Owner: `/root/internal_integration_20261027`. Date: 27 October 2026. Selected work: R2/R3/R9 under PhysMath Research Loop 1.3.0. This is a source-grounded integration of recovered internal results, not a new observational fit or a new independent review. The source packages are `HTT_TEFF_V15_EXTENSION_20261026` and `HTT_COSMO_TEFF_REFOCUS_20261026`; the external comparison is `htt_obs_bridge_run/RESEARCH_RUN_REPORT.md`. Their hashes and precise paths are in the companion JSON. Existing reviewed proofs and static checks are reused with their stated scope.

## 1. Scientific synthesis

The original research question can be retained: what do the shape, relative orientation and depth dependence of observed sky multipoles imply about radiation, matter motion and spatial geometry? The recovered results make the intervening maps explicit. They support three separately usable channels:

\[
\begin{aligned}
\text{polarization }(Q_E,O_E)&\longrightarrow\text{morphology, stability, calibrated rarity},\\
\text{intensity }C^I_{\ell m}&\longrightarrow J_{\langle A_\ell\rangle}
\longrightarrow(\rho_\gamma,q_a,\pi_{ab},\mathcal A_\gamma),\\
\text{distance/drift coefficients}&\longrightarrow
\text{common-congruence optical kinematics and finite-distance combinations}.
\end{aligned}
\]

The first channel already has a retained measured Planck example. The second has an exact radiation-stress null and uncertainty map that need no transport solution. The third has a joint optical response, a corrected dipole–octupole consistency test and distance-jet combinations. A subsequent matter-shear inversion consumes the radiation transport residual; a subsequent Bianchi compatibility calculation consumes spatial curvature and gravitational constraints. Those additional inputs are attached only to their consumers.

The useful publication unit is therefore an observable-specific inference method with one measured example and explicit physical extensions. Requiring the full six-paper history/selection/atlas programme before any such unit can finish would discard completed mathematics and conditional data products. Conversely, treating a completed mathematical interface as an empirical constraint would erase the very response information supplied by these results.

## 2. Four axes and the tensorized carrier

| Axis | Object retained | Consequence for integration |
|---|---|---|
| Symmetry, gauge and degrees of freedom | Passive triad rotations, spacetime coordinate freedom, physical observer changes and statistical nuisance directions are distinct. Generic STF2 plus STF3 has twelve real components and a nine-dimensional SO(3) quotient. | A Lorentz boost is not three redundant sky coordinates. Singular orbit strata require their actual stabilizer. A nuisance projection is not a GR gauge fixing. |
| Invariants | Chirality/powers are rotation invariants with stated parity; radiation rest-pressure eigenvalues give a Lorentz-scalar strength on their timelike branch. | State the transformation group and physical carrier for every invariant. A rotation invariant cannot alone identify a Bianchi spacetime. |
| Observables | Realized harmonic coefficients, spectral channels, optical coefficients, proper motions, masks and their joint measurement law. | Preserve field labels: polarization E is not positive bolometric intensity; magnitude multipoles are not raw Hubble-slope multipoles. |
| Physical quantities | Radiation stress at an event; congruence expansion/shear/acceleration/vorticity; spatial Ricci; history-dependent tilt. | Connect each to data through its own response and error model. Equal angular rank is insufficient. |

Use a shared physical/observable carrier \(X\) with explicit channel labels and nuisance variables. Its sample-by-functional array is \(x_{ij}=\phi_j(X_i)\), with paired reference states where required. Preserve the actual meanings:

- \(Q\): Minkowski gauge or margin relative to a declared nondegenerate anchor body, distinct from a sky quadrupole.
- \(F_{\rm sup}\): directional support utilization. Its denominator must be positive; a zero-null set cannot supply it.
- \(F_{\rm cert}\): legacy certified ceiling utilization, not a material-volume fraction.
- \(F_\nu\): occupancy only under a supplied measure and support.
- \(\Pi\): exceedance under a named joint sampling/null/posterior law; a deterministic set carries no automatic weights.
- \(G_F\): a depth/transport construction with actual shared latent realizations, frame endpoints and cross-window covariance. A radial kinetic moment index is not a depth coordinate.

The updated statistical method should retain the vector/tensor response before scalarization. For a parameter-independent compression \(T(Y)\), the retained Loop E identity \(I_Y-I_T=E[\operatorname{Cov}(s(Y)\mid T)]\succeq0\) explains why separate amplitudes can lose signed orientation information useful for separating boost, shear and calibration. It does not assert sufficiency of an arbitrary tensor summary.

## 3. What is ready to consume

### Radiation stress and low-multipole orientation

The refocused note fixes signature \((-+++ )\), \(U^2=-c^2\), outward direction \(n=-e\), and physical bolometric energy density per solid angle \(I\). Its harmonic–STF adapter is
\[
J_{A_\ell}=(-1)^\ell\int I(n)n_{\langle A_\ell\rangle}\,d\Omega,
\qquad \rho=J,\quad q_a=cJ_a,\quad\pi_{ab}=J_{ab}.
\]
For photons the velocity-dressed radial indices in the Lewis–Challinor hierarchy coincide because \(cq/E=1\). Separate spectral moments still require separate kernels. This prevents an artificial multiplication of observables by changing an index label.

Let \(f=q/(c\rho)\), \(P=\pi/\rho\). On \(\rho>0,|f|<1\), the recovered exact criterion is
\[
\mathscr D=P-\frac{3}{2+\sqrt{4-3|f|^2}}\operatorname{STF}(ff^T).
\]
Its vanishing characterizes positive perfect-radiation stress in a timelike rest frame. The Lorentz-scalar strength \(\mathcal A_\gamma\) is the norm of the three rest-pressure deviations from \(\rho_L/3\), divided by \(\rho_L\), on the unique timelike eigenbranch. Perfect stress does not imply an angularly isotropic distribution: higher harmonics can remain.

For a low-rank energy-temperature contrast \(d\cdot n+Q_T:nn+O_T:nnn\), the recovered quadratic map contains \(d\cdot O_T\), \(\operatorname{STF}(Q_T^2)\), and \(\operatorname{STF}(O_T\cdot O_T)\). Thus relative orientation enters an actual stress constraint, rather than only an abstract morphology statistic. The exact fourth-power map is preferable when additional modes exist. A joint confidence region for \((f,P)\), including calibration and spectral completion, maps to a region for \(\mathscr D\) and \(\mathcal A_\gamma\). The five-component null does not automatically have a chi-square law.

Reused numerical evidence: maximum pure-boost residual \(1.65\times10^{-16}\); rotation covariance and rest-stress invariance at floating-point precision; cubic convergence of the low-multipole approximation. The illustrative CMB-scale toy gives \(\mathcal A_\gamma=3.2659863\times10^{-6}\) and positive residual lower bound \(2.7412264\times10^{-6}\) under declared toy errors. These are method controls, not a Planck detection.

### Response-preserving reconstruction and a stopping criterion

Loop A and the v15 extension supply
\[
\mathcal L_I S=\frac{8\rho}{15}S+
\frac{10}{7}\operatorname{STF}(S\pi)-H_4:S.
\]
For nonnegative brightness its quadratic form is
\[
\langle S,\mathcal L_I S\rangle
=\int I(e)\{2|Se|^2-(e^TSe)^2\}\,d\Omega.
\]
The lower bound \(\lambda_{\min}(\rho I_3/3+\pi)\|S\|^2\) gives one sufficient coercivity certificate; the actual symmetric five-dimensional spectrum can be stronger. This is a physical response to differential expansion, not an identification of temperature quadrupole with shear.

Every response kernel lies in angular sectors \(\ell=0,2,4\). Therefore **matching those energy moments preserves the entire operator exactly** even when unresolved spectral and higher-angular entropy remain positive. In the existing static experiment, the L=2 operator error is \(0.00654243536\rho\); L=4 gives approximately \(1.2\times10^{-15}\rho\) while its normalized angular entropy residual remains \(9.37160903\times10^{-5}>0\). This is an actionable completion rule: finish the reconstruction when the target response is preserved to the declared error, not when all kinetic information is recovered.

The alternative scalar certificate
\[
\|\mathcal L_I-8\rho\mathrm{Id}/15\|_{\rm op}
\le \rho\sqrt{8\delta/3},\qquad
\delta=1-\langle(4\pi I/\rho)^{3/4}\rangle
\]
is sufficient for invertibility when \(\delta<8/75\). Failing this sufficient condition should trigger evaluation of the actual operator spectrum, not a research HOLD: the retained positive family at \(\delta=0.294552\) still has \(\lambda_{\min}/\rho=0.128233\).

Matter shear additionally satisfies \(\mathcal L_I\sigma=-R\) in the declared geodesic, irrotational, collisionless branch. With \(\|\delta\mathcal L\|\le\epsilon_L\), \(\|\delta R\|\le\epsilon_R\), and \(\widehat\lambda>\epsilon_L\),
\[
\|\sigma-\widehat\sigma\|
\le\frac{\epsilon_R+\epsilon_L\|\widehat\sigma\|}{\widehat\lambda-\epsilon_L}.
\]
The operator product can be completed before the derivative-residual product. Matching moment values at one event does not supply derivatives. Finite-band transport also has energy-boundary terms; do not apply the bolometric equation independently to uncorrected channels.

### Population and detector-response information

The supplied v15 population ratio \(\mathcal Q=\mathcal N^4/(\mathcal D\mathcal E^3)\) has pointwise Doppler weight zero because number and energy transform with weights three and four. It remains an aberrated scalar field, not invariant harmonic coefficients. A common energy-independent positive beam changes the inferred population coordinate through \(\langle T^3\rangle^4/\langle T^4\rangle^3\). The sharp range bound is an existing generalized Kantorovich specialization; its physical application is a beam-induced population-bias interval. The retained illustrative range \(T_{\max}/T_{\min}=2\) gives minimum ratio 0.51391970736, and a Planck-mixture effective \(\eta=-0.42440662570\).

This channel is useful only when number and energy, or equivalent independent spectral responses, are available. Reconstructing both from the same blackbody temperature imposes the very relation one would wish to test. It creates no independent dipole discriminator.

For a bounded detector kernel, the recovered finite-amplitude entropy frontier preserves number and energy and has an exact Bregman identity. Its local susceptibility is
\[
\chi_K=\int W\big[K-\operatorname{Proj}^{W}_{\{1,E\}}K\big]^2d\nu_U,
\qquad W=g(1+\xi g).
\]
The static MB/BE/FD width ratios 0.7032/0.7102/0.6737 demonstrate that conditioning removes directions already fixed by calibration. The small-budget \(\sqrt{2\epsilon\chi_K}\) width is asymptotic; finite-budget claims must use the finite frontier. Entropy or tail budgets need physical input and are not inferable from a residual fit alone. This connects to the external bounded-foreground proposal without identifying kinetic entropy with an arbitrary foreground-moment radius.

### Dipole, radial/transverse kinematics and the shared Hubble budget

The recovered dipole loop separates radiation intrinsic dipole from global matter tilt. Under its controlled second-order ordering,
\[
a=\beta+d,\qquad K-aa_{\rm STF}=Q-dd_{\rm STF}+O(\lambda^3).
\]
An intrinsic-quadrupole envelope or independent calibrated aberration velocity response makes this a dipole constraint. A spectral term proportional to the same total blackbody dipole is not an independent velocity measurement. The exact stress criterion above is a complementary physical target and avoids treating the second-order expansion as exact.

The optical local inverse uses sources and observer in the same smooth congruence. With physical rates \((h,S,v,\alpha)\), it gives
\[
d_r(n)=h+S:nn-\alpha\cdot n,\qquad
\mu(n)=(I-nn^T)Sn+n\times v.
\]
The leading acceleration contribution cancels in the transverse common-congruence response, while the radial acceleration dipole survives. Distant-quasar secular aberration is a different source/reference response. A free catalogue spin adds exactly three B1 kernel directions; calibrating it is a physical input, not a change of tensor basis. The retained finite design has radial rank nine, transverse rank eight and joint rank twelve under its declared response.

The magnitude optical inverse uses \(d=-A/(cH)\), \(S=\sigma/H\) and \(f_\mu=-\kappa\log(1+d\cdot n+S:nn)\). Its STF3 lift obeys \(M_S=L_S^*L_S=(S:S)I_3/3+2S^2/5\). For fixed measured \(\widehat S\ne0\),
\[
\|\widehat O-\kappa L_{\widehat S}d_{\rm obs}\|^2
=\|\widehat O_\perp\|^2+
\kappa^2(\widehat d-d_{\rm obs})^TM_{\widehat S}(\widehat d-d_{\rm obs}).
\]
Both terms consume the same remainder budget. The retained counterexample has separate scores 0.8 and 0.8 but joint score 1.13137. The budget includes \(E_3+e_O+B_z+B_{\rm sel}+|\kappa|\sqrt{3/5}e_SD_{\max}\); a direct-dipole uncertainty is handled by minimizing the quadratic term over its joint feasible region. This corrects an actually consequential testing error and should be incorporated in the optical methods product immediately.

The external dust observation is compatible with this theorem: geodesic dust sets the common-congruence acceleration to zero. It prevents relabelling a finite-window CF4 boost/bulk/calibration dipole as that acceleration. It does not invalidate the local optical law for accelerated congruences or the algebraic shared-budget test. The correct repair is an explicit response adapter for each catalogue, rather than deleting the dipole construction.

### Directional Hubble jets and geometric compatibility

The retained distance expansion recovers \(h_0,h_1\) and
\[
\mathcal J=h_2+\frac12h_0R_{KK}
=\frac{3h_1^2}{h_0}-6h_0^4d_3
\]
from three luminosity-distance coefficients. Curvature focusing and the second ray derivative remain a joint combination without another response. The two finite-redshift quantities \(cz/D_L\) and \(c/\partial_z[D_L/(1+z)]\) differ at first order in redshift; neither should be labelled an unrestricted local Hubble rate. An \(O(z^2)\) distance correction generally produces an \(O(z)\) magnitude correction. The Kasner example and positive-denominator reciprocal bound supply concrete controls without ODE evolution.

The geometric loop supplies an independent finite target. Bianchi II with \(n=(u,0,0)\) and VII\(_0\) with \(n=(0,2u,u)\), both \(a=0\), can share expansion, diagonal shear, normal dust density, zero momentum and scalar curvature \(-u^2/2\), but their spatial Ricci tensors are
\[
\frac{u^2}{2}\operatorname{diag}(1,-1,-1),\qquad
\frac{u^2}{2}\operatorname{diag}(-1,3,-3).
\]
Their different spectra identify the extra curvature information an observation would need. Flat I and equal-parameter flat VII\(_0\) instead represent the same local spatial Euclidean geometry. This distinction between geometry and homogeneous presentation should enter future atlas-equivalence tests. The algebraic compatibility evaluator and its examples can finish without an all-m T/E/B atlas; a claim from the actual CMB still needs its transfer and observational law.

## 4. Planck morphology: retained measured result and new ideal reference

The recovered primary PR3 E-mode row is \((r,\mathcal C,E,U)=(0.0582918,-0.0967707,0.808141,0.1197448)\). Its processing cutoff is 32; the retained carrier is the processed STF2/STF3 E field. The ideal conditional Gaussian law is \(U=3\sqrt3|z_1z_2z_3|\), \(z\sim\mathrm{Unif}(S^6)\), for a simple-spectrum quadrupole and independent isotropic Gaussian octupole. Reused fresh simulation: 662,397 of 1,048,576 draws are at or below the observed U; CDF 0.631711, upper tail 0.368289. This is an ordinary ideal-reference position, not a processed-Planck p-value.

All sixty retained processing carriers have a certified individual sign at relative perturbation radius \(10^{-6}\); their signs need not agree. The radius is deterministic and is not an estimated Planck error. Stable sign, parity-odd invariant and statistically significant parity violation are three distinct claims. The NPIPE route can add a processed-sky calibration; it need not delay publication of the theorem, the actual morphology table, and the accurately labelled ideal-reference control.

## 5. Specific changes to the external recommendations

| External recommendation | Integration decision | Smallest constructive correction |
|---|---|---|
| One mock-derived covariance is prerequisite for every H/K/V physical statement. | Too broad. It is central for calibrated CF4 significance under the selected null; other exact response laws and conditional sensitivity products have different inputs. | Split response derivation, estimator propagation, conditional covariance sensitivity, and source-qualified empirical calibration into separate consumers. Do not impose CF4 mocks on radiation or geometric algebra. |
| The acceleration dipole has no dust referent, so remove the dipole branch. | Preserve the geodesic-dust specialization, correct the catalogue referent. | Route CF4 finite-window dipoles to boost/bulk/calibration responses; retain accelerated-congruence and intrinsic-radiation dipole branches with their own input contracts. |
| Close K03 as no astrometric sensitivity in every regime. | Unsupported as a universal conclusion by the internal response map. | Retain the scoped low-power forecast for the existing experiment; leave alternative histories/populations and calibrated B1/E2 responses as separate tasks. The physical-audit lane verifies the literature limits. |
| A full kinetic reconstruction is needed before radiation inference. | Not required for the retained response. | Use exact energy moments 0/2/4 for the shear operator and 0/1/2 for stress. Block only the missing target-specific response or derivative inputs. |
| External Bianchi producer existence should unlock family inference. | Producer is a data route, not completed identification. | Complete geometry compatibility and convention/equivalence controls now; admit only an actual qualified atlas subset later. |
| Replace PR3 and nominal-training acceptances with available PR4/public-SN data. | Useful alternative estimands, not equivalent original completions. | Add distinct branches and preserve original acceptance and counts. Common output tests may consume either only when their estimand requirements actually match. |
| Use a bounded foreground moment radius as the physical missing ingredient. | Useful if dimensionally qualified and jointly calibrated. | Connect a target detector response to a finite support set; supply measured foreground amplitudes, parameter covariance and truncation/tail control. Do not infer an entropy allowance from an arbitrary radius or double count retained energy error. |

An external model-fitting failure can be retained as conditional evidence while the null/covariance is repaired. Agreement with a literature point estimate is a comparator, not an acceptance requirement that a new analysis must reproduce regardless of changed estimator or data law.

## 6. Concrete next task contracts and parallelism

The companion JSON provides eight task contracts with inputs, output, acceptance, stop condition, dependencies and original-acceptance effect. These are semantic integration IDs for the parent to map to the existing PR DAG, not a competing controller.

1. **INT-STRESS:** consume the retained exact null and build a joint positive-moment confidence-image comparator. Deliver the static benchmark and explicit observational adapter; empirical interval waits only for calibrated intensity products.
2. **INT-HUBBLE-JOINT:** replace separate dipole/residual acceptance in the optical methods path by the common-budget profile test, with uncertain S and magnitude-order terms. Near S=0 use direct response membership.
3. **INT-RESPONSE-SPAN:** export the exact 0/2/4 operator and response-preserving compression, with direct operator fallback when an entropy sufficient certificate fails. Report R separately.
4. **INT-PLANCK-CALIBRATION:** retain the measured morphology/stability and ideal law; add the selected PR4 processed-null branch without promoting PR3 acceptance. One independent simulation sky remains one statistical unit.
5. **INT-DIPOLE-CHANNELS:** register intrinsic-radiation, optical-acceleration, observer-boost and bulk-flow vectors separately; use independent velocity/population information only when actually supplied.
6. **INT-OPTICAL-JETS:** fit identifiable distance-jet combinations and radial/transverse closure on a declared common-source response; derivative and curvature claims consume separate evidence.
7. **INT-GEOMETRY:** expose the existing initial-data Ricci and Gauss–Codazzi evaluator, the II/VII0 witness and flat-presentation equivalence as atlas tests.
8. **INT-DETECTOR-FRONTIER:** apply the fixed-number/energy frontier to actual bounded bandpass kernels and a justified spectral budget, preserving the physical units and multichannel support directions.

INT-HUBBLE-JOINT, INT-RESPONSE-SPAN and INT-GEOMETRY have complete reused mathematical prerequisites. INT-STRESS and INT-DETECTOR-FRONTIER have static implementations and require actual instrument inputs for empirical outputs. INT-PLANCK-CALIBRATION has a ready ideal benchmark and a separate release-matched acquisition branch. INT-DIPOLE-CHANNELS and INT-OPTICAL-JETS can perform conditional response/injection studies now, with later actual-data gates. These roots should run in parallel where file ownership permits. A missing mock catalogue must not make all eight unready.

## 7. Publication priority and evidence states

The strongest immediate methods additions are the shared Hubble error-budget test, the response-specific moment-preservation result, the exact radiation-stress null with its joint uncertainty map, and the explicit ideal morphology reference law. The geometric witness and optical-jet combination provide physical examples that join the same paper rather than an unrelated collection of theorems. The number–energy and detector frontiers are supporting calibration methods until real spectral inputs demonstrate an advantage.

Potential empirical results after short local work are a release-qualified morphology percentile, a covariance-sensitivity frontier for the CF4 tensor, a joint optical model-consistency region, and a radiation-rest stress interval. All must state the actual selected sample and processing model. The existing CF4 amplitudes and Planck row can be reused as conditional/retained measured summaries; they are not remeasured here.

No independent priority claim is established by this integration. Established ingredients include Lorentz-transformed perfect fluids, STF/Gaunt algebra, covariant cosmography, VSH kinematics, entropy duality and confidence-set propagation. The prospective contribution is their explicit response-qualified tensor inference and demonstrated advantage on common inputs. Acceptance should require a comparator at matched data, calibration and error budget, rather than the presence of a new tensor notation.

Implementation status of this lane: two integration artifacts written; scientific source hashes and existing review scopes checked; no new physics execution, solver, raw-catalogue fit or remote mutation. Parent owns canonical-DAG edits and publication.
