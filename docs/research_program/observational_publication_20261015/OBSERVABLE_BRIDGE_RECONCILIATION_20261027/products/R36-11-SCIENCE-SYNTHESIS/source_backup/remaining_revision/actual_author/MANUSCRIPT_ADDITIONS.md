# Author text and source table for the remaining qualified observable bridges

This file is an author contract, not a new scientific result or controller task. Only the passages inside **Manuscript text** blocks are intended for an external-reader English REVTeX document. Table directives refer to the exact locators in EDITOR_CONTRACT.json. The author may normalize mathematical typography and cross-reference labels, but must return to the scientific author if the meaning, physical assumptions, units, input identity, or numerical scope would change.

## Editorial allocation and consuming decision

| Qualified source | Publication destination | Existing original consumers informed, not completed | Physical increment |
|---|---|---|---|
| Exact CF4 operator plus repaired correlated response | R32-08-H03-PAPER, after the existing tensor-carrier section | H02, H04, H05, H06, S02, K04, V04 | Exact covariance transport through the retained estimator, correlated depth/radius response and footprint dependence |
| Public released-magnitude SN comparator | Same H03 paper, separate following section | R23-SN, H04, V04, K04 | An actual signed two-depth angular-magnitude fit with the selected released covariance and a conditional joint reference |
| Repaired finite geometry image | R32-07-P5-ALGEBRA, new appendix | B02, B03, K04 | Equal-scalar/different-Ricci witnesses, full tensor uncertainty, repaired flat-center ranks and retained LRS-V connection |
| Radiation-stress and energy-response comparison | R32-09-BANDPASS-PAPER/radiation_supplement, a source-bound scientific supplement linked in the existing paper README | S02, S04, V04, L03 | Full bolometric finite-boost stress comparison plus target-preserving rank-four energy response |

The first, second and third allocations follow FRONTIER.json paper IDs and the actual manuscript contents. INTERNAL_INTEGRATION.json maps INT-R04 directly to P5. It maps INT-R10 to NEW_RADIATION_STRESS_METHODS, while INT-R06/07 map response compression to the bandpass methods. The existing bandpass paper treats a finite nine-moment foreground class and a finite response matrix; it does not provide calibrated positive bolometric intensity, a complete temperature sky, or the synthetic Gaussian law used in the stress comparison. A short self-contained supplement is therefore physically coherent. It must explicitly call itself a companion methods calculation and cannot extend the parent paper's foreground class. This is a manuscript artifact within existing work, not a new campaign, task, frontier, or acceptance gate.

The already applied P4 endpoint/history manuscript is preserved completely. Source 03 is already consumed there through the qualified 11 candidate. Future optical-joint integration is reserved for the existing P6 optical paper after exact qualification of 04; future morphology integration is reserved for the existing quadrupole–octupole methods paper after exact qualification of 06. Neither reserved location contributes a number, figure, or claim now. Foreground-budget 07 and atlas-intake 09 remain input holds, not results.

## H03 paper: allowed framing edits

Keep the current title, all original equations, all original numerical tables/figures and the dimensionless CF4 quotient unchanged. Append two sentences to the abstract after its present final sentence:

**Manuscript text**

We also propagate a common Gaussian velocity field through the exact finite-window estimator, retaining its cross-window and cross-smoothing covariance under an explicit restricted-band model. A separate two-depth Pantheon+ magnitude comparison retains all signed dipole and quadrupole coordinates and gives a joint improvement of 17.2066 for 16 angular coefficients, with conditional upper-tail probability 0.37235 under the released selected-covariance Gaussian law.

**End manuscript text**

In the retained-carrier section, change only the scope of the sentence “The experiment here consumes only the saved statistics” to “The original finite-window sensitivity experiment below consumes the saved statistics; the later covariance and supernova sections consume separate retained response products.” Common calibration, PV and selection covariance remains empirically unmeasured. Do not imply that conditional analytic covariance measures these missing laws.

## H03 inserted section: Correlated velocity uncertainty through a fixed survey estimator

**Manuscript text**

A velocity-field model becomes relevant to the apparent expansion coefficients only after it is propagated through the same estimator that produced them. Freeze the catalogue distances, directions, weights and row order, and write

\[
 \widehat\theta=A y,\qquad y_i=c z_{{\rm CMB},i},\qquad
 A_w=(X_w^T W_wX_w)^{-1}X_w^T W_w,
 \quad X_{w,i}=d_i(1,n_i,E_1:n_in_i,\ldots,E_5:n_in_i).
\]

The four window blocks form a 36 by 35,970 operator. The directions are outward ICRS J2000, distances are in Mpc, the input is in km/s, and the output coefficients are in km/s/Mpc. The released redshift defines a fixed proxy; it is not varied as an observer parameter. The five matrices \(E_A\) form the signed orthonormal STF basis used earlier. Applying the same operator to a source bulk velocity and to observer motion gives \([AN,-AN]\), where row \(i\) of \(N\) is \(n_i^T\). Consequently \((h,h)\) is a null direction for every constant vector \(h\). This statement concerns source minus observer velocity; the earlier comparison between a velocity response and a constant apparent-rate dipole is a different design comparison.

For an independent source-error component with diagonal variance \(D\), a common velocity-field factor \(V\), and mean-design offsets \(Z\eta\) with covariance \(\Sigma\), the propagated covariance is

\[
 C_\theta=A\operatorname{diag}(D)A^T+(AV)(AV)^T+K\Sigma K^T,
 \qquad K=AZ.
\]

Independence is part of this stipulated decomposition. Correlated source classes require their joint factors and cross terms. The original weighting law,
\(250^2+[70(\ln10/5)d_i e_{{\rm DM},i}]^2\), already contains a velocity-scale term and has no established empirical decomposition. We display its propagated working covariance separately. It is neither added to nor subtracted from the new conditional total.

The velocity calculation uses the Eisenstein–Hu no-wiggle approximation and a common present-day Gaussian density realization, propagated with the prescribed linear growth factors. The numerical background is \(H_0=67.36\) km/s/Mpc, \(\Omega_m=0.3153\), \(\Omega_\Lambda=0.6847\), \(\omega_b=0.02237\), \(n_s=0.9649\), and \(\sigma_8=0.8111\). The two wavenumber bands are \([0.005,0.02]\) and \([0.02,0.05]\,h\,{\rm Mpc}^{-1}\), with \(h=0.6736\). Shared Gaussian smoothing radii are 5, 10 and 20 \(h^{-1}\) Mpc. At a positive quadrature node, the source response is proportional to

\[
 b_i(k,\hat k)=g_i(n_i\!\cdot\!\hat k)e^{ik\hat k\cdot x_i}
 \left[\frac{P_0(k)w_k w_\Omega}{(2\pi)^3}\right]^{1/2} S_R(k),
 \qquad x_i=\chi(z_{{\rm CMB},i})n_i,
 \quad g_i=a_iH_if_iD_i.
\]

Real and imaginary projected columns give a positive-semidefinite Gram matrix. There is no magnitude derivative in this velocity-to-rate response. All radii and windows see the same field, yielding a full 108-coordinate covariance rather than independent blocks.

[Generate table CF4-COV from TABLE.csv and the saved covariance matrices: each band at each radius; R=5 combined PV, inherited working and stipulated total traces. Units are (km/s/Mpc)^2. Display at least eight decimal places for the traces.]

At 5 \(h^{-1}\) Mpc the two band traces sum to 17.05835032 \((\mathrm{km/s/Mpc})^2\). The original working trace is 4.76965546 in these units. A separate total, which stipulates an independent 150 km/s source term and four independent method mean-design offsets with standard deviation 0.4 km/s/Mpc, has trace 17.68057386. The offsets use \(Z_{im}=d_i1_{m(i)=m}\); this is not a magnitude-zero-point derivative. Varying the distance calibration itself would also change distances, design and possibly weights. Power outside the two bands, nonlinear velocities, the empirical source-selection law and calibration/PV cross terms are not supplied by this calculation.

[Include sealed CF4 FIGURE.png. Caption: Correlation of the propagated apparent coefficients for the two prescribed velocity bands at R=5 h^{-1} Mpc. Each consecutive block of nine coordinates contains a monopole, three signed dipole components and five STF components in one redshift window. The off-diagonal blocks retain the common-source velocity field. These matrices describe the conditional Gaussian band model; they are not estimates of the complete empirical survey covariance.]

[Generate table CF4-FOOTPRINT with four rows and three radius columns from the repaired SENSITIVITY.json. Use matched-radius trace ratios, not the historical root-level sensitivity file. Include selected group counts.]

Removing or restricting catalogue subsets changes the response even under the same field model. At the smallest radius, northern and southern ICRS subsets have PV trace ratios 2.405 and 2.580 relative to the full sample; removing FP or TF groups gives 1.173 and 0.867. The corresponding ratios at the largest radius are 2.172, 2.360, 1.171 and 0.863. These are overlapping-source, footprint-dependent estimator comparisons. They provide a quantitative reason to retain the actual survey support, rather than independent confirmations of an anisotropic flow.

Under the stipulated 36-coordinate total covariance at the smallest radius, a prespecified comparison of a shared monopole, affine monopole and shared nine-coordinate mean gives minimum discrepancies 174.925896, 145.158891 and 80.137690, with ranks 1, 2 and 9. The rule \(T+\operatorname{rank}\ln36\) selects the nine-coordinate mean. The retained 2,000-draw Gaussian selected-statistic reference under the fitted shared-monopole model gives an upper-tail estimate \(1/2001=0.00049975\), with Monte Carlo standard error approximately 0.00050. This is a finite check of that stipulated reference. It is not an empirical CF4 population probability, and it is not directly comparable to the earlier 12-coordinate dipole statistic, which uses a different response and covariance. A sample-covariance inverse correction alone would not validate a selected statistic; for example, the Gaussian 64-mock, 36-coordinate inverse factor \(26/63\) leaves finite-covariance uncertainty to be propagated.

**End manuscript text**

## H03 inserted section: A released-magnitude angular comparison in two depth bins

**Manuscript text**

A second observable can be studied without assigning the apparent CF4 tensor to a matter shear. We use the released Pantheon+ corrected magnitudes and their total statistical-plus-systematic covariance, retaining the original observation order and repeated supernova observations. The primary sample contains 490 noncalibrator rows with \(0.0233\le z_{\rm HD}\le0.15\); the lower-redshift sensitivity sample contains 705 rows with \(0.01\le z_{\rm HD}\le0.15\). Both split at \(z_{\rm HD}=0.06\), giving 342/148 and 557/148 low/high rows respectively. The samples overlap.

Define the fixed dimensionless reference and residual

\[
 \mu_{\rm ref}=5\log_{10}\left[(1+z_{\rm HEL})
 \int_0^{z_{\rm HD}}\frac{dz}{\sqrt{0.3153(1+z)^3+0.6847}}\right],
 \qquad y=m_{b,\rm corr}-\mu_{\rm ref}.
\]

An additive magnitude intercept and one high-bin offset are profiled. Neither is an independent absolute-Hubble-constant measurement. In each bin, the angular response is \(d\cdot n+\sum_{A=1}^5q_A n^TE_An\), with coefficients in magnitudes. The axes are the released RA/DEC Cartesian chart; its physical reference-frame binding has not been established here. The signed STF basis is

\[
 E_1=\operatorname{diag}(1,-1,0)/\sqrt2,\quad
 E_2=\operatorname{diag}(1,1,-2)/\sqrt6,\quad
 (E_3,E_4,E_5)=(e_xe_y^T+e_ye_x^T,
 e_xe_z^T+e_ze_x^T,e_ye_z^T+e_ze_y^T)/\sqrt2.
\]

Selection uses the marginal covariance \(C_s=P_s C_{\rm STAT+SYS}P_s^T\) once, with the same original row indices on both axes. No separate diagonal magnitude error, PV term, jitter or rescaling is added. The complete released 1,701-row array contains 389 unordered pairs exceeding the fixed symmetry tolerance, with maximum asymmetry \(3.0\times10^{-8}\,\mathrm{mag}^2\). All affected pairs lie outside the 705-row selected union. Both consumed submatrices are exactly symmetric as stored and positive definite. This validates the consumed submatrices without certifying or repairing the unused full array.

After Cholesky whitening, both nuisance columns are projected out and all 16 angular directions retain full rank. Let \(T_0\) and \(T_1\) be the profiled nuisance-only and angular-model quadratic discrepancies. Under the fixed-design Gaussian law with known selected covariance, \(\Delta T=T_0-T_1\) has a conditional \(\chi^2_{16}\) reference. The nominal 95-percent threshold is 26.2962.

[Generate SN-FIT table: cohort, low/high count, T_null, T_dipole, T_full, Delta T, conditional upper-tail probability, from the two RESULT fit branches. Generate signed low/high/contrast eight-coordinate table using all coordinates; retain both full 16x16 covariance matrices and each contrast covariance in the numerical supplement.]

The primary improvement is 17.206588 with conditional upper-tail probability 0.372352; lowering the minimum redshift gives 16.554089 and 0.415003. The primary comparison does not reject its isotropic two-level nuisance model under this conditional law. Sixteen leave-one-survey comparisons retain angular rank 16 and give improvements from 14.0415 to 18.9251. These correlated deletions describe sensitivity; they do not calibrate an independent population null. All 50,616 low/high covariance entries in the primary selected matrix are nonzero, and the complete cross-bin covariance is retained.

[Include sealed PUBLIC_SN_SIGNED_COORDINATES.pdf. Caption: Signed apparent-magnitude dipole and STF coordinates in the released Cartesian chart for the primary and overlapping lower-redshift sample. Error bars are marginal one-standard-deviation displays. Inference uses the full joint covariance and the prespecified 16-coordinate comparison; individual bars are not simultaneous acceptance intervals or separate binwise tests.]

The chart \(d_{L*}=d_L/(1+z_{\rm HEL})^2\) subtracts \(10\log_{10}(1+z_{\rm HEL})\) from both observed magnitude and reference mean at fixed released redshifts. The residual and its fitted coefficients are therefore invariant; the retained real-data coefficient change is below \(10^{-14}\) mag. Subtracting from only one side changes the residual and fails this consistency test. A physical observer boost also changes photon redshift, direction, distance response and potentially selection and uncertainty, so chart invariance is not a boosted-observer fit. The released \(z_{\rm HD}\) includes its peculiar-velocity correction; \(z_{\rm CMB}\) is retained and is not substituted for the photon-redshift factor.

These magnitude tensors are a separate released-observable estimand. They do not establish nominal light-curve-training parity, a material-frame shear, acceleration, or a physical observer velocity. The supernova and CF4 comparisons have neither a supplied common response nor a measured shared-PV cross-covariance, so their statistics are not added and their probabilities are not multiplied. Their useful common output is a signed, covariance-aware description of apparent angular structure with explicit depth support.

**End manuscript text**

Add the following paragraph to Conclusions, leaving the existing quantitative conclusions unchanged:

**Manuscript text**

The additional covariance transport demonstrates how a shared velocity field changes the joint apparent-coefficient uncertainty through the actual survey operator. The released-magnitude comparison gives a distinct observational application with its own angular response and covariance. Their physical combination requires source, observer-frame and cross-survey error models; those requirements cannot be replaced by treating the two apparent tensors as measurements of one material shear.

**End manuscript text**

## P5 appendix: A spatial-curvature tensor distinguishes equal-scalar initial data

Insert after the existing physical interpretation and before its source/reproducibility section. Preserve all original numbered equations and source Markdown; the new appendix source is separately consumed by the current report assembler. Use labels A1 onward to avoid collision with original explicit equation tags.

**Manuscript text**

The scalar spatial curvature in an instantaneous energy constraint does not determine the full intrinsic curvature. To display the missing information, choose an oriented right-handed orthonormal triad, \(\epsilon_{123}=+1\), signature \((-+++ )\), and

\[
 K_{ij}=-(h\delta_{ij}+S_{ij}),\qquad h=H/c,\quad S=\sigma/c,
 \qquad \kappa_g=8\pi G/c^4.
\]

The symmetric structure tensor \(n\) and vector \(a\) satisfy \(na=0\). The signed momentum and Hamiltonian constraints in this convention are

\[
 \kappa_g q_i=3S_{ij}a_j+\epsilon_{ijk}n_{jl}S_{kl},\qquad
 3h^2=\kappa_g\varepsilon_N+\Lambda+\tfrac12S:S-\tfrac12{}^{(3)}R.
\]

Here \(\varepsilon_N\) and \(q\) are normal-frame energy-density and flux-density coordinates in J/m^3; the corresponding energy current is \(cq\). The quantities \(n,a,h,S\) have inverse-length units. In the class-A subspace \(a=0\), the spatial Ricci tensor is

\[
 {}^{(3)}\!\mathrm{Ric}
 =2n^2-(\operatorname{tr}n)n+
 [\tfrac12(\operatorname{tr}n)^2-\operatorname{tr}(n^2)]I.
\]

This tensor formula supplies a finite map independent of a photon transfer calculation.

Set \(u_*=10^{-26}\,\mathrm{m}^{-1}\), \(h/u_*=2\),
\(S/u_*=\operatorname{diag}(1/10,-1/20,-1/20)\), and \(\Lambda=0\). The choices
\(n/u_*=\operatorname{diag}(1,0,0)\) and
\(n/u_*=\operatorname{diag}(0,2,1)\) provide type-II and unequal type-VII\(_0\) witness presentations. Both have
\[
 {}^{(3)}R/u_*^2=-1/2,\qquad
 \kappa_g\varepsilon_N/u_*^2=4697/400,\qquad q=0,
\]
while their ordered Ricci spectra are \((-1/2,-1/2,1/2)u_*^2\) and \((-3/2,-1/2,3/2)u_*^2\). The minimum Frobenius separation of their proper-rotation orbits is \(\sqrt2\,u_*^2\). Equal scalar curvature and the displayed common matter/expansion/shear coordinates therefore leave different intrinsic curvature tensors.

For a finite uncertainty calculation, use the 12 dimensionless coordinates consisting of the six Frobenius coordinates of \(n/u_*\), \(h/u_*\), and five signed STF coordinates of \(S/u_*\). The map \(F\) returns six Ricci coordinates, normal energy and three signed flux coordinates, all normalized by \(u_*^2\) with \(\kappa_g\) for matter. Each input set is \(z=z_0+L\xi\), \(\|\xi\|\le1\), with \(L=\operatorname{diag}(0.05,\ldots,0.05,0.01,\ldots,0.01)\), seven entries followed by five. This is a declared deterministic ellipsoid, not a covariance estimate. Since this map is quadratic,

\[
 F(z_0+L\xi)=F(z_0)+JL\xi+\tfrac12\mathcal H[L\xi,L\xi].
\]

For a projection \(w\), a whole-set radius is
\[
 b_w=\|L^TJ^Tw\|_2+	frac12\|L^T\mathcal H_wL\|_{\rm op}
 +e_{\rm round},\qquad \mathcal H_w=\sum_k w_k\mathcal H_k.
\]

The sum of conservative Ricci Frobenius radii for the two matched sets is \(0.41697619\,u_*^2\), below their orbit-center separation. Thus these two constructed tensor sets are disjoint under the stated bound. Their neighborhoods need not retain the center's Bianchi class or a common perfect-fluid model. Positivity bounds establish \(h>0\) and \(\varepsilon_N>0\) throughout these sets, while signed flux can vary.

[Generate GEO-CENTERS table from repair_01/TABLE.json: all four n, h, S, normal energy and flux centers, geometry-Jacobian rank and joint-image rank; never read the obsolete parent table.]

The two flat controls use \(n=0\) and \(n/u_*=\operatorname{diag}(0,1,1)\), both with \(S=0\), \(h/u_*=2\), \(\kappa_g\varepsilon_N/u_*^2=12\), and \(q=0\). Both have zero full spatial Riemann and the same local Euclidean intrinsic geometry through distinct simply transitive presentations. At II, unequal VII\(_0\), I and flat VII\(_0\), the six-component geometry Jacobian ranks are 6, 6, 0 and 3; the ten-component joint-image ranks are 9, 10, 1 and 6. At type I only the first energy derivative is nonzero, \(\partial(\kappa_g\varepsilon_N/u_*^2)/\partial(h/u_*)=12\). A zero geometry Jacobian does not make the map constant: \(\mathrm{Ric}(tn)=t^2\mathrm{Ric}(n)\). The nonzero Hessian and curved exactly flat paths must be retained when interpreting the local rank.

[Include sealed repaired GEOMETRY_IMAGE.pdf. Caption: Deterministic images of four declared initial-data ellipsoids. Left: 577 prescribed probes per center and conservative whole-set bounds in scalar and tensor projections. Middle: center Ricci spectra and conservative tensor radii. Right: singular values of the six-component geometry Jacobian, not the ten-component joint map. Probe clouds visualize the sets; the whole-set quadratic enclosure establishes the stated separation. Center labels name witness presentations, and the two flat centers describe the same local intrinsic Euclidean geometry. No empirical probability or coverage is assigned.]

The connection to the LRS-V region studied in the main text preserves all 280 retained tensor tuples. The proper cyclic frame transformation \((e_1,e_2,e_3)=(e_z,e_x,e_y)\) carries signed shear, flux, pressure and anisotropic stress into this triad. The retained maximum relative Hamiltonian and momentum residuals are \(1.11\times10^{-16}\) and \(9.48\times10^{-17}\). Velocity remains the physical speed \(\beta=v/c\), with matter velocity undefined in the absent-matter vacuum branch. This algebraic conversion is not an evolved spacetime solution or a measured curvature constraint. An observational use requires a calibrated, same-frame response to the curvature tensor. Neither scalar agreement nor tensor-set separation identifies a Bianchi family from a CMB sky.

**End manuscript text**

## Radiation supplement: title and abstract

**Manuscript text**

# Radiation stress under finite observer boosts and response-preserving energy moments

A low temperature quadrupole approximates radiation stress only within its amplitude and spectral assumptions. We compare exact bolometric fourth-power conversion with a linear temperature-to-moment adapter on the same six positive synthetic skies and the same correlated errors. Both adapters use the same finite-boost stress residual and invariant rest-pressure anisotropy. Their physical-target coverage and interval widths differ even when their method-target calibration is similar. Separately, energy moments of angular ranks zero, two and four preserve the complete five-dimensional radiative shear-response operator. In a retained compression example, rank-four response agreement reaches numerical precision while a positive angular entropy residual remains. These are conditional full-sky radiation methods; applying them to measured channels requires calibrated intensity, spectral completion and a measured joint error law. The accompanying finite-bandpass foreground analysis addresses a different inverse problem and does not supply those inputs.

**End manuscript text**

## Radiation supplement section: Physical moments and two common-input adapters

**Manuscript text**

Use signature \((-+++ )\), outward sky direction \(n\), photon direction \(e=-n\), and bolometric energy density per solid angle \(I\) in J m\(^{-3}\) sr\(^{-1}\). With a calibrated energy temperature,
\[
 I=C_\gamma T_E^4,\quad C_\gamma=\frac{\pi k_B^4}{60\hbar^3c^3},\quad
 \rho=\int I\,d\Omega,\quad q=-c\int I n\,d\Omega,\quad
 \pi=\int I\operatorname{STF}(nn)\,d\Omega.
\]
The reference temperature is 2.7255 K, giving \(\rho_{\rm ref}=4.17480092\times10^{-14}\) J/m\(^3\). Set \(f=q/(c\rho)\), \(P=\pi/\rho\). On the positive moment domain with a unique timelike Landau eigenbranch, define
\[
 \mathscr D=P-\frac{3\operatorname{STF}(ff^T)}{2+\sqrt{4-3|f|^2}},\qquad
 \mathcal A_\gamma=\frac{[\sum_{i=1}^3(p_{L,i}-\rho_L/3)^2]^{1/2}}{\rho_L}.
\]
The residual \(\mathscr D\) is an observer-frame STF tensor; \(\mathcal A_\gamma\) is invariant under observer tetrad changes on this branch. A zero residual tests a timelike isotropic-pressure rest stress. It does not require every higher angular multipole to vanish.

The source brightness is \(I_{\rm rest}/I_{\rm ref}=1+aP_2(n_{{\rm rest},z})\), with \(a\in\{0,2\times10^{-5},0.02\}\), boosted by \(\boldsymbol\beta=b(0.6,0,0.8)\), \(b\in\{0.00123,0.3\}\). The complete positive temperature sky is obtained from this specified boost, retaining its higher modes. The analytic target is the Lorentz transform of \(\operatorname{diag}(1,1/3-a/15,1/3-a/15,1/3+2a/15)\rho_{\rm ref}\), so \(\mathcal A_{\gamma,\rm true}=\sqrt6|a|/15\).

Only the three temperature dipole and five temperature STF coordinates are perturbed. Their Gaussian standard deviations are \(7.5\times10^{-6}\) and \(9.375\times10^{-7}\), and their correlation is \(0.8I_8+0.2ss^T\), \(s=(1,-1,1,1,-1,1,-1,1)\). Monopole and higher temperature modes are noiseless known inputs. Both methods receive identical errors. The exact adapter integrates the fourth power of that sky. The linear adapter uses \(f_{\rm lin}=-4d_T/3\) and \(P_{\rm lin}=8Q_T/15\), with the same monopole normalization, then applies the same exact \(\mathscr D\) and Landau readout. This isolates the temperature-to-moment approximation. The joint flux/stress covariance, including its three-by-five cross block, is retained; it is not replaced by independent dipole and quadrupole errors.

**End manuscript text**

## Radiation supplement section: Conditional calibration, coverage and widths

**Manuscript text**

Each case uses 8,191 calibration skies and 4,096 disjoint test skies. Calibration is pointwise around the known noiseless response of each method. For \(\mathscr D\), the confidence-region radius is the 7,783rd ordered calibration norm error, producing a five-dimensional ball. For \(\mathcal A_\gamma\), the interval subtracts the 7,988th and 204th ordered calibration errors and intersects the result with \([0,\infty)\). An upper endpoint below zero produces an empty interval and is counted as noncoverage. The exact physical target and the noiseless method target are assessed separately; no bias correction is fitted to force them to coincide.

[Generate RAD-COVERAGE and RAD-WIDTH tables for all six cases and both methods using methods selected by case and method labels. Show hits/N plus Clopper–Pearson interval, five-dimensional ball diameter, A empty fraction, nonempty count and mean width. All widths are dimensionless; a 10^-6 display factor must be explicit. Do not quote a paired width mean without its common-nonempty denominator.]

For the pure-boost case at \(b=0.00123\), the exact and linear physical-target \(\mathscr D\) counts are 3,872/4,096 and 3,035/4,096, while the invariant-anisotropy counts are 3,914/4,096 and 1,545/4,096. Their \(\mathscr D\) ball diameters are nearly equal, \(3.390\times10^{-6}\) and \(3.381\times10^{-6}\). Thus similar widths can conceal different target bias. The linear method-target coverage remains near its nominal level across the cases even where its physical-target coverage fails.

At \(a=0,b=0.3\), the exact \(\mathscr D\) count is 3,934/4,096, or 0.960449, with a retained 95-percent interval [0.954021,0.966209]. This single high estimate is an unadjusted finite-simulation diagnostic among the reported comparisons, not a claim of exact 95-percent coverage. Calibration-content uncertainty is separate: under continuous errors its retained central intervals are [0.945254,0.954684] for the ball and [0.945382,0.954801] for the scalar interval. No seeds, quantiles or sample counts were adjusted. Empty exact-method scalar intervals occur in 89 and 119 test skies in the two pure-boost cases; corresponding nonempty means use 4,007 and 3,977 skies. Empirical measured-sky error-law misspecification is outside these intervals.

[Include sealed comparison.pdf. Caption: Common-input synthetic comparison of exact and linear temperature adapters. Upper panels show physical-target coverage and finite-test Clopper–Pearson intervals; the dashed line is the nominal calibration level. Lower panels show the five-dimensional residual-ball diameter and the mean width of nonempty rest-anisotropy intervals. Empty intervals count as noncoverage and are excluded only from the explicitly labeled nonempty width means. Both methods use the same correlated temperature errors, with noiseless known monopole and higher modes. These are pointwise oracle benchmarks, not calibrated intervals for an unknown observed CMB sky.]

**End manuscript text**

## Radiation supplement section: The moments needed for the target response

**Manuscript text**

Let \(H_4=\int I(e)e_{\langle i}e_je_ke_{l\rangle}\,d\Omega\). On the five-dimensional STF space, the instantaneous radiative response is
\[
 \mathcal L_I S=\frac{8\rho}{15}S+
 \frac{10}{7}\operatorname{STF}[\tfrac12(S\pi+\pi S)]-H_4:S,
\]
with quadratic form
\[
 S:\mathcal L_I S=\int I(e)[2|Se|^2-(e^TSe)^2],d\Omega.
\]
Only energy moments of ranks zero, two and four enter. Matching these moments therefore preserves the entire operator, independently of unresolved higher angular structure. In the retained compression experiment, the operator error normalized by \(\rho_0\) is 0.00654243536 at rank two and \(3.3393\times10^{-16}\) at rank four on the primary quadrature, while the positive normalized angular entropy residual is \(9.37160903\times10^{-5}\). The higher quadrature gives rank-four error \(4.3301\times10^{-15}\); the conclusion is numerical agreement at the checked precision, not exact binary equality.

[Generate RAD-RESPONSE table with all five rank-four response eigenvalues and both quadrature checks. Preserve the full five-by-five matrix in the numerical supplement.]

For the positive \(e^{8\mu^2}\) brightness family, a sufficient entropy lower bound is \(-0.352935\rho\), while the actual minimum response eigenvalue is \(0.12823282\rho>0\). A failed sufficient certificate does not establish loss of coercivity; the finite operator spectrum provides the direct check. If a specified transport branch supplies \(\mathcal L_I\sigma=-R\), a shear estimate also needs the derivative residual \(R\), its frame and its error. That residual is absent here, so no matter shear is inferred from instantaneous brightness alone.

The finite-bandpass foreground problem and this bolometric calculation constrain different objects. A calibrated intensity/spectral completion is needed to carry measured channel amplitudes into the positive energy moments used above. Polarization E is not such an intensity, and evaluating number and energy from one imposed blackbody temperature does not create a second independent observed channel. The present contribution is a response-specific stopping criterion and a matched-input stress comparison under a stated synthetic law.

**End manuscript text**

## Production source and validation instructions

EDITOR_CONTRACT.json binds all consumed files, publication-status/formal-review evidence, affected production preimages and numeric locators. The old pending flags inside sealed RESULT files are historical producer records; the separate qualified status and formal return determine reuse eligibility. Never rewrite these flags or manifests.

Prepare a bounded candidate overlay outside production. Implement one cached-data assembler/checker whose contract is the required CLI listed in EDITOR_CONTRACT.json. It must read results and sufficient statistics only. It may format signed vectors/matrices, compute simple presentation traces/ratios from saved matrices, and recount saved hit arrays, but must not run an R36 producer, refit raw data, regenerate MC, redownload data, rerun old paper numeric generators, or evolve a solver. Reuse the four sealed source figures. No new scientific comparison is authorized.

For each changed live paper, retain only the necessary old source preimages in a small local baseline directory. Validate immutable science sources against their original hashes; validate overlay targets against either the frozen preimage or exact reviewed postimage. On replay after application, the assembler must accept the applied identity and regenerate the same current content. Do not feed current modified TeX/PDF into the old release's output-manifest validator and report that expected overlay difference as a scientific failure. Conversely, do not relax old validators or silently rewrite their source hashes. Preserve original arrays, curves, equations, claims and old output manifests; expose the current entrypoint in a concise README.

Before independent review: build all three current documents, run cached-consumer falsifiers, verify old numerical/figure identities and rendered-table values, and inspect the new pages. The exact final candidate, sources and outcomes go to a fresh Astra reviewer who did not author this contract or implementation. Only after that review may the existing controller apply the bounded overlay. After actual application, run the current production consumer/checker, compile all affected documents, compare PDF text to the reviewed candidate, and apply a second time with zero changed targets. These are existing publication checks with an operational consumer; no new campaign gate or original-acceptance promotion is created.
