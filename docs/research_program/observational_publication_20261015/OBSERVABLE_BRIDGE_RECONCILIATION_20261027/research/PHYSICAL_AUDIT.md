# Physical audit and constructive optical/astrometric repairs

Owner: `/root/external_physical_audit_20261027`. Date: 2026-10-27. Scope: R3/R5/R6, PhysMath 1.3.0. The external report is useful evidence for candidate bridges, not authority to change scientific acceptance. This note reads its report, decision gate, adversarial review, negative-results ledger and numerical sources, then checks the affected physical arguments against primary papers. The latest retained checkpoint is `a55036ad09c53a9215dee3282e425d37cfb95443`; the root owns live-reference verification. No solver, ODE, raw catalogue fit or external write was performed by this lane.

## 1. Decisions on the external recommendations

| Finding | Evidence and consequence | Constructive disposition |
|---|---|---|
| PH-01: astrometric closure is overbroad | N-001 and the gate infer no sensitivity in any regime from one local amplitude and selected early-time CMB bounds. Saadeh et al. give mode-dependent limits, including a regular tensor limit of 1e-6, not a universal 1e-10. A weak bound is also not an empty identified set. | Retain the low priority of a CF4-scale shear fit using distant quasars. Replace universal rejection by a source/history-specific power calculation. Original K03/K05 remain unqualified. |
| PH-02: the quoted direction-drift law is incomplete | External `mu=-H P S n` retains only one term of Marcori et al. (2018), eq. (5.13). Their full first-order Bianchi-I response also contains a distance-dependent endpoint/history term. T-04 computes a norm and sets its curl check to literal `True`; it cannot validate the response sign or missing history. | Use the two-time response in section 2, with a declared domain and local-limit test. This is a real, solver-free theory input. |
| PH-03: the acceleration correction needs two distinctions | Exact pressureless, separately conserved geodesic dust has A=0. This supports rejecting an automatic acceleration interpretation of a finite-window fitted dipole. It does not prove that every smoothed effective congruence is geodesic, or that every boosted local Hubble dipole is proportional to 1/z. | Keep intrinsic congruence acceleration, observer-frame expansion dipole, and finite-redshift magnitude residual as three distinct carriers. Section 3 supplies their connection. |
| PH-04: mocks are treated as the only route to covariance | An inherited weighting matrix does not automatically equal an empirical error law. Nevertheless a stated analytic correlated law can be pushed through the exact frozen estimator now; selected-catalogue mocks are one route to validating it, not a prerequisite for deriving it. | Start the conditional exact-operator covariance lane in section 4. Preserve the empirical-selection gate for original H02/H04/H05/H06. |
| PH-05: T-12 and broad model rejection | The attachment includes T-01–T-07 and T-11 executable sources/results, but not a T-12 program/result receipt. Its few fitted depth laws cannot exhaust LambdaCDM velocity fields. | Root's separate T-12 replay lane supplies numerical evidence. Irrespective of numerical agreement, use 'these finite designs fail under the retained covariance', not 'no LambdaCDM dipole law fits'. |
| PH-06: external pass/kill rules overidentify degenerate parameters | Requiring fitted observer and bulk speeds separately to match quoted CF4-derived values is inappropriate when their leading columns are collinear and the comparison datasets overlap. | Test the identifiable combination first; add independently calibrated frame information through a joint likelihood. Do not enforce source-overlapping point estimates as hard pass bounds. |

## 2. A useful replacement for the incomplete proper-motion law

Use signature (-,+,+,+), proper time t, outward source direction n in a nonrotating observer tetrad, and P=I-nn^T. Consider a homogeneous, weakly anisotropic Bianchi-I geometry

\[
ds^2=-c^2dt^2+a(t)^2[e^{2B(t)}]_{ij}dx^i dx^j,
\quad B^T=B,\quad \mathrm{tr}B=0,
\]

with fixed principal axes and first order in B and its perturbative derivatives. Let \(\chi_{so}=c\int_{t_s}^{t_o}dt/a(t)\) and \(D_{so}=a_o\chi_{so}\). With comoving emitters and observer, the convention-translated response from Marcori et al. eq. (5.13) is

\[
\mu(n,z)=P\,A_{\rm PM}(z)n,
\qquad A_{\rm PM}(z)=\frac{2c}{D_{so}}(B_o-B_s)-\dot B_o.
\tag{1}
\]

The first term is their parallax/history contribution; the second is the local aberration contribution. Their paper explicitly distinguishes the two. The source is [Marcori et al., Phys. Rev. D 98, 023517 (2018), sections 5.2.1–5.4](https://arxiv.org/pdf/1805.12121). Equation (1) uses physical-time rates; all its terms have units s^-1. It is not a response law for an arbitrary spatially localized CF4 velocity field or a quasar photocentre.

For any STF matrix A, direct spherical moments give

\[
\langle|PAn|^2\rangle
=\langle n^TA^2n\rangle-\langle(n^TAn)^2\rangle
=\frac13\mathrm{tr}A^2-\frac2{15}\mathrm{tr}A^2
=\frac15\|A\|_F^2.
\tag{2}
\]

Thus the external RMS relation remains valid for **A_PM**, not generally for sigma_o alone. At short source distance, \(B_o-B_s=\dot B_o\Delta t+O(\Delta t^2)\) and \(D_{so}=c\Delta t+O(H\Delta t^2)\), so

\[
\mu=P\sigma_o n+O(\Delta t),\qquad \sigma_o=\dot B_o.
\tag{3}
\]

This positive sign has a direct independent check: if a nearby physical separation obeys \(\dot r=(H I+\sigma)r\), differentiating \(n=r/|r|\) gives \(\dot n=P\sigma n\). Sources move toward the faster-expanding axis. The exact submitted Wolfram calculation and output are retained in the JSON companion; it returns `{0,0,0}` for the derivative identity. A central finite difference gives error 8.14e-12, whereas reversing the sign gives error 0.09 in the declared dimensionless test.

A finite-history bound follows without solving dynamics. If \(\|\dot\sigma(t)\|_F\le L_\sigma\) on the source-observer interval, then

\[
\|A_{\rm PM}-\sigma_o\|_F
\le 2\left|\frac{c\Delta t}{D_{so}}-1\right|\|\sigma_o\|_F
+\frac{cL_\sigma\Delta t^2}{D_{so}}.
\tag{4}
\]

Proof: write \(B_o-B_s=\int_{t_s}^{t_o}\sigma(t)dt\), add/subtract \(\sigma_o\Delta t\), and integrate \(\|\sigma(t)-\sigma_o\|\le L_\sigma(t_o-t)\). This bound turns the missing history into a named finite nuisance interval, conditional on supplied D, Delta t and L_sigma. Those bounds must be physically justified before source admission.

There is also a constructive history discriminator. The perturbation \(\delta B=\varepsilon\tau(1-\tau)T\), \(\tau=(t-t_s)/\Delta t\), with fixed STF T, leaves both endpoint B values unchanged but gives \(\delta\sigma_o=-\varepsilon T/\Delta t\). Equation (1) consequently changes by \(\delta A_{\rm PM}=+\varepsilon T/\Delta t\). Equal endpoint deformation therefore need not mean equal direction drift. This is a finite kinematic example, not a new Bianchi solution or a fit to quasars. It naturally complements the retained endpoint/history degeneracy results.

### What sensitivity can actually establish

For a specified PM data vector, covariance V, response A and nuisance design N, whiten with V^-1/2 and project away N. The Fisher matrix is

\[
\mathcal I=A^TV^{-1/2}(I-P_{V^{-1/2}N})V^{-1/2}A.
\tag{5}
\]

The noncentrality for parameter s is \(s^T\mathcal I s\). A small maximum over the *declared* physical domain establishes low power for that experiment, not absence of a physical response. A null information direction gives an unbounded or prior-domain-limited identified set; an empty set instead means incompatibility. A common B1 sky rotation is degenerate with unconstrained reference-frame spin, while E2 and depth-dependent responses require their own projected-rank check. Mask-induced mixing is handled in V and the design, not by assuming full-sky orthogonality.

The late-time/early-time distinction is supported by [Quercellini et al. (2009)](https://arxiv.org/abs/0905.4853). [Saadeh et al. (2016)](https://arxiv.org/abs/1605.07178) give a vector limit 4.7e-11 and regular-tensor limit 1.0e-6 within their dynamical families. These are mode/history-qualified bounds, not limits on every local tensor. Their conventional shear scalar also differs from a Frobenius norm by sqrt(2). These distinctions invalidate the external blanket no-go without predicting a detectable signal in the cached catalogue.

## 3. The optical inverse survives, with a better physical interpretation

The local same-congruence law

\[
\mathcal H(n)=H-A\cdot n/c+\sigma:nn,
\qquad d=-A/(cH),\quad S=\sigma/H
\tag{6}
\]

is a legitimate covariant kinematic construction. Heinesen's eq. (4.1) supplies this structure; section 5 supplies a separate observer-boost map. For exact separately conserved dust, momentum conservation makes A=0. A Newtonian gravitational coordinate acceleration must not be inserted for A. This is a correction to the data interpretation, not a refutation of (6) or of its tensor inverse. See [Heinesen (2021)](https://arxiv.org/pdf/2010.06534).

The phrase 'smoothed or not' is too strong. In a mass-weighted coarse-graining, even force-free streams satisfy

\[
(\partial_t+\bar u\cdot\nabla)\bar u_i
=-\bar\rho^{-1}\partial_j\tau_{ij},\quad
\tau_{ij}=\overline{\rho u_i u_j}-\bar\rho\bar u_i\bar u_j.
\tag{7}
\]

Velocity dispersion can accelerate the effective flow. Its relativistic analogue has effective pressure, stress and flux. An effective A therefore requires the averaging/source model; it is neither automatically zero nor automatically measured by H03. Tilt by itself likewise does not imply non-geodesic motion.

There are three different dipoles to retain:

1. The intrinsic acceleration dipole of the chosen congruence, equation (6).
2. The local **observer-frame physical expansion dipole**. For geodesic matter and observer velocity beta=v/c, Maartens et al.'s first-order boost gives
   \[
   d_{\rm boost}=-2(I+S)\beta+O(\beta^2).
   \tag{8}
   \]
3. A finite-redshift magnitude residual from source/observer velocities. Its leading low-z behavior is proportional to relative radial velocity divided by cz, with additional O(beta) and higher-distance terms. A single 1/z column is a useful first approximation, not the complete covariant boost law.

The source [Maartens et al., JCAP 09 (2024) 070, v3 sections 3.1 and 4.2](https://arxiv.org/html/2312.09875v3) provides the precise frame convention and distance correction. It requires \(d_{L*}=d_L/(1+z)^2\) for the invariant slope relation; the boosted vertex redshift also changes. Its eq. (70) displays a spurious octupole if the uncorrected luminosity-distance slope is used. This correction must precede an observed acceleration–shear interpretation.

On a qualified slope chart, the same retained mathematical inverse

\[
O_\mu=\kappa L_Sd+R_3,\quad
\widehat d_S=\kappa^{-1}M_S^{-1}(O_\mu:S)
\tag{9}
\]

can target d_boost rather than A. If \(I+S\) is invertible, the conditional next map is

\[
\widehat\beta=-\tfrac12(I+S)^{-1}\widehat d_S.
\tag{10}
\]

This is a useful reinterpretation, not a plug-in estimator for raw observed magnitude. Construct the forward map for redshift, distance, aberration and source window jointly, then use the shared-error-budget test from the internal 2026-10-26 note. It must include uncertainty in S, the optical chart, finite distance and selection. At S=0 the octupole inverse loses absolute information even if the direct dipole remains measurable.

### The boost/bulk rank statement

At leading low z, observations depend on \(n\cdot(v_s-v_o)/(cz)\). If a constant source bulk vector and observer velocity are both fitted through the same three projected columns K, the design is [K,-K], with null vectors (a,a). Only their difference is identified. Higher-order frame terms, a known radial profile or external observer information can break this degeneracy; a nonzero angle between approximate columns does not by itself guarantee useful precision. Report whitened singular values and profile intervals. Treat source-overlapping external velocity estimates through their covariance rather than hard independent two-sigma thresholds.

## 4. Replace the mock-only prerequisite by a conditional exact-operator route

Freeze the catalogue positions, grouping, selected cohort, windows, nuisance columns, units and estimator. If its stacked coefficient estimate is \(\widehat\theta=K y\), linearizing a stipulated velocity law gives

\[
y=m+R v+\epsilon,\qquad
V_\theta=K[N+R\Psi R^T]K^T.
\tag{11}
\]

The derivative R must be the actual data-to-estimator derivative; it is not interchangeable between magnitude and cz/d observables. Additional calibration components enter only once and only when not already included in N or profiled nuisance columns.

For a single-epoch, homogeneous Gaussian linear velocity field,

\[
\Psi_{ij}=(aHf)^2\int\frac{d^3k}{(2\pi)^3}
P_\delta(k)\frac{(n_i\cdot k)(n_j\cdot k)}{k^4}
e^{ik\cdot(r_i-r_j)}.
\tag{12}
\]

Here P_delta has length cubed, k inverse length, and Psi velocity squared. This equation has a positive spectral-feature representation. For positive quadrature weights, write \(\Psi\approx BB^T\), including sine/cosine features. Then

\[
V_{\theta,\rm PV}=\sum_\alpha (KRb_\alpha)(KRb_\alpha)^T.
\tag{13}
\]

Streaming the vectors KRb_alpha directly into a 36-by-36 covariance avoids constructing a 35,970-by-35,970 matrix. Positive semidefiniteness is automatic at every finite quadrature stage. This is the constructive computational output; catalogue selection and nonlinear/source modeling remain separate limitations. The root's covariance lane owns implementation/replay.

The resulting law is conditional on fixed observed positions and stipulated velocity/calibration assumptions. It can produce a conditional null, compare scales, expose dominant covariance modes and plan mocks immediately. Physical selection inference still requires its source likelihood or a justified sensitivity class. Public SDSS mocks with another footprint must first be passed through an explicitly justified catalogue/selection adapter. Their existence alone does not validate CF4 coverage.

For N=64 independent Gaussian mocks and p=36 fitted-summary coordinates, an unbiased sample covariance has a biased inverse. The multiplicative correction is (N-p-2)/(N-1)=26/63, not one; for p=12 it is 50/63. A corrected inverse alone does not restore a Gaussian likelihood. [Hartlap et al. (2007)](https://arxiv.org/abs/astro-ph/0608064) and [Sellentin & Heavens (2016)](https://arxiv.org/abs/1511.05969) describe the issue and covariance-marginalized treatment. For an independent Gaussian test vector with known null mean and covariance estimated from N mocks, \(T=y^TS^{-1}y\) obeys \(T\sim p(N-1)/(N-p)F_{p,N-p}\). This formula is not automatically valid after fitting the same data or choosing windows. Calibrate the entire chosen statistic or use the applicable likelihood; preserve mock independence and finite-N uncertainty.

## 5. Executable continuation and scientific acceptance

| Existing branch | New work that is ready | Positive output | Still required for original acceptance |
|---|---|---|---|
| H02/H04/H05/H06 | Frozen-estimator analytic correlated covariance and T-12 replay | Conditional 36D law, identifiable depth combinations, sensitivity/power plots | Parent selection, empirical calibration/PV law and validation of stipulated model |
| K03/K05 | Two-time PM response, source-distance bins, projected information/power | Signed history-qualified response and constrained combinations/finite power limits | Centroid-to-matter transfer, source depths, Gaia/radio covariance, reference-frame law |
| K04/V04 | Frame-corrected optical forward map and shared-budget inverse | Separate intrinsic A, observer beta and finite-depth velocity targets | Actual source/frame/clock likelihood and error budgets |
| P3/P6 companions | Amend interpretation and add conditional theorems above | A coherent morphology→response→physical-quantity methods result | Common-input empirical validation before physical detection claims |

Do not close original scientific inputs by replacing them with 'law exists' or 'weak sensitivity'. Mark the completed theory component separately and enqueue its consumer. The external audit's useful corrections are retained: direct CF4-window identification with local shear is conditional; working covariance needs a physical law; raw finite-window dipoles do not automatically measure four-acceleration. Its universal no-go and mock-only stopping rule are replaced by the concrete response/covariance work above.

The JSON companion records source identities, tool checks, scope and machine-readable contract suggestions. These results are literature-supported/derived with lightweight static checks. This lane makes no observational detection, publication-readiness or new first-in-literature claim.
