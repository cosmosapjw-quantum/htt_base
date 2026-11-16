# R58: six convergent theory loops and their implemented observational connection

Owner: HTT inference; MIO consumes diagnostics. Baseline: `77f61c17ba33ff28ff4f16a7d42621d8041e5ce4`. Scope: existing data only, claim tier C0. The six questions below retain independent R1–R10 records; a shared carrier is reused where the questions genuinely share data. This document adopts existing R7–R9/R39 mathematics and the latest R54 results, then connects them to the executed full-covariance CF4 experiment. Stage completion means the stated bounded question has been addressed; it does not mean all six topics have a new observational detection.

Current computed evidence is `OWNED_TENSOR_RESULT.json` and `OWNED_TENSOR_CARRIERS.npz` (placed in the result directory by the owned-data runner). Result schema: `htt.r58.owned_mixed_tensor/1`, status `NUMERICALLY_CHECKED_CONDITIONAL`. The separate physical/five-view builder is `scripts/r58/build_r58_views.py`; its final execution and review status must be read from its generated result and review receipt, not inferred from its presence here. The retained internal sources and exact reading scope are in the R58 history audit. `R54/MANUSCRIPT_CLAIM_TABLE_R54.md` controls historical numerical claims over earlier passages of `R54/THEORY_LOOPS.md`.

## Shared conventions and the actual experiment

Use signature `(-,+,+,+)`, sourceward spatial unit direction n, an explicitly declared orthonormal triad, and explicit c. The physical variables are shear sigma_AB and vorticity omega_A in s^-1, acceleration A_A in length/time^2, and dimensionless relative velocities beta. STF5 coordinates in this experiment use an orthonormal Frobenius basis E_a, so K=Σ_a kappa_a E_a and tr(K²)=Σ_a kappa_a². Do not combine them with the older nonorthonormal Cartesian STF5 chart without its Gram transform.

The executed estimand is the eleven-component apparent coefficient

\[
\alpha=(V_x,V_y,V_z,d_x,d_y,d_z,\kappa_0,\ldots,\kappa_4),
\]

where V is in km s^-1 and d,K are dimensionless log-Hubble anisotropy coefficients. On the selected 35,970 CF4 groups,

\[
\eta_i=N_{m,i}\gamma_m+g(z_i)n_i^aV_a+n_i^ad_a+n_i^aK_{ab}n_i^b+\epsilon_i.\tag{S1}
\]

A fixed reference H_fid makes eta=ln[c(1+z) chi_hat(z)/(H_fid d_L,obs)] dimensionless; omitting this constant in stored logarithms only changes the fitted monopole nuisance. For each of the seven retained nuisance models m, the existing source-window operator O_m gives

\[
y_m=O_m\eta\in\mathbb R^{32},\quad X_m=O_m[g\,n,n,E_a:nn]\in\mathbb R^{32\times11},\quad
C_m=O_m C_{\rm noise}O_m^T+C_{{\rm cosmic},m}.\tag{S2}
\]

The 32 rows are four windows of polar3 plus STF5. The actual velocity response is propagated into **all** rows; the sky window produces nonzero velocity-to-STF coupling. C_m retains polar–STF and cross-window blocks. Its cosmic term is the pinned R54 linear LCDM pair-sum body; R58 does not recompute that body or independently validate the cosmic/selection model. Operator byte fingerprints differ across platforms, while input/code/cache identities, labels/model keys and seven-model numerical reproduction are checked. This is scientific numerical reuse, not byte-identical replay.

For the fixed Gaussian working experiment, the normalized likelihood is

\[
-2\log L_m(\alpha;y_m)=(y_m-X_m\alpha)^TC_m^{-1}(y_m-X_m\alpha)+\log\det C_m+32\log(2\pi).\tag{S3}
\]

The precision is J_m=X_m^T C_m^-1 X_m, the score t_m=X_m^T C_m^-1 y_m and q0_m=y_m^T C_m^-1 y_m. A centered whitened factor is retained for stable evaluation, along with q0/normalization for adequacy. Calling J_m the view F would conflate two different objects. Each model has numerical rank 11; its 95% simultaneous set is

\[
\mathcal C_m=\{\alpha:(\alpha-\hat\alpha_m)^TJ_m(\alpha-\hat\alpha_m)\le\chi^2_{11,.95}\},\qquad
\mathcal C_\cup=\bigcup_{m\in\mathcal M}\mathcal C_m.\tag{S4}
\]

The union covers the true coefficient with at least 95% probability if one **listed** model and its fixed Gaussian law are correct. The listed models were motivated by previous data inspection; the displayed tails are conditional/exploratory. They do not calibrate model search, unknown calibration, selection misspecification or every possible nuisance law. Different O_m define different compressed experiments: their likelihood ordinates are not ranked by AIC or Bayes factors. The 32-row experiment is not proved sufficient for the raw catalogue.

## L1 — Low-ell morphology to physical observables

**R1 — Contract; complete.** Determine the physical history functionals encoded by low-ell temperature/polarization morphology and whether they identify present shear. Reuse the owned T/E diagnostics; add no new CMB data or transfer solver. The bounded output is an explicit physical map and its identifiable quotient.

**R2 — Evidence reuse; reused.** `tensor_joint_r7/THEORY.md` T1/T3, `tensor_joint_r8/THEORY.md` O4/P1, R39 `VECTOR_TENSOR_X_FRAMEWORK.md`, and R54 `THEORY_LOOPS.md` EQ-01–06 / `THEOREMS.md` T8. Full multipole vectors plus amplitudes and raw harmonics already retain the same tensor information; scalar power/norm reductions can lose orientation and relative shape. CMB STF morphology is a data-space object, while sigma is a congruence kinematic tensor connected by a transfer/history map.

**R3 — Assumptions; complete.** Restrict the reused kernel to first-order spatially homogeneous type-I shear, the stated Thomson hierarchy and optical-depth history. N=ln a and s=sigma/H are dimensionless. The temperature/E transfer assumptions are distinct from the finite-z CF4 phenomenology. E is diagnostic under the final R54 B-null decision.

**R4 — Candidate choice; complete.** Keep the five-component history functionals Sigma_T and Sigma_E as x, instead of assigning the same measured quadrupole directly to sigma(today). Compare a specified one-/two-mode history family with an unrestricted function-space history. This separates data information from history regularization.

**R5 — Derivation; derived/reused.** The collision matrix has eigenvalues 1 and 3/10. Its exponential yields

\[
K_T(\tau)=\frac{6e^{-\tau}+e^{-3\tau/10}}7,\quad
K_E(\tau)=\frac{\sqrt6}7(e^{-3\tau/10}-e^{-\tau}),\quad
\Sigma_{T,E}=\int K_{T,E}(\tau(N))s(N)\,dN.\tag{L1.1}
\]

For s(N)=Σ_j b_j f_j(N), the componentwise map is M_ij=∫K_i f_j dN, so its rank is at most two with T+E and at most one with T alone. On an interval of strictly monotone tau, rho=K_E/K_T=√6(1-q)/(1+6q), q=e^-7tau/10, is monotone. A nonzero function annihilated by K_T must change sign; one annihilated by both kernels has at least two sign changes. Conversely, three disjoint bumps give a 2×3 moment matrix with a nontrivial null vector. Scaling the corresponding null history leaves both moments fixed and makes its norm arbitrarily large. This proves absence of a norm upper bound **in the unrestricted history space**. Compact norm/derivative budgets or other explicit physical families can bound it; a two-parameter family is not the only possible regularization.

**R6 — Checks; reused plus corrected scope.** K_T(0)=1, K_E(0)=0; all terms in Sigma are dimensionless; the small-optical-depth E response is O(tau). The stable rho expression avoids exponential overflow. The R58 proof review supplies a numerical optical-depth counterexample to the former unstable implementation and restricts the overstrong upper-bound consequence. These are repairs to scope/numerics, not new physical no-go claims.

**R7 — Discriminating evidence; reused.** The R54 final claim table reports T pipeline shifts ≤0.34 sd and calibrated perfect-fluid T-only present-shear illustration 1.16e-9. Its E FFP-only B-null tails are .00664/.00332; the 10.6× variance floor uses tested maps and leaves E diagnostic. No new E-based limit is computed in R58. This evidence selects the T-only history-functional reading for a bounded manuscript.

**R8 — Decision.** `derived` transfer/history quotient; `numerically checked` inherited T consistency; present shear remains model-labelled. The classical kernels, multipole tensorization and Chebyshev argument are attributed reuse. T/E morphology alone does not select a unique shear history in the unrestricted domain.

**R9 — Coding connection.** Register `Sigma_T_STF5` and diagnostic `Sigma_E_STF5` separately from `sigma_over_H_STF5`, with kernel, frame, epoch and STF basis IDs. A scalar x_C is an additional functional. Existing CMB evidence is not multiplied again through derived morphology summaries. R58 CF4 K is not assigned a CMB history without an explicit transfer.

**R10 — Closeout.** This loop closes with a bounded history-functional statement and reuses the existing CMB result. The next local task is native replay of the R58 package and manuscript integration; a new CMB acquisition or general Bianchi transfer is outside this convergence slice.

## L2 — Dipole anomaly

**R1 — Contract; complete.** Determine what the owned source-count dipoles and distance frame carrier can say about a nonkinematic dipole, distinguishing non-detection, power and the particular selection/systematic law.

**R2 — Evidence reuse; reused.** R7 T4/T8 joint-law and nuisance rules; R39 `KINEMATICAL_LIKELIHOOD_MODEL.md` §4.2; R54-L03 result and the final claim table; R54 T9 interpreted with explicit endpoint velocities. The earlier R38/R41 hard-coded or unsourced joint claims stay quarantined by R39/R42.

**R3 — Assumptions; complete.** For population a in a specified shell, define its Ellis–Baldwin coefficient k_a and observer, matter, radiation velocities v_O,v_j,v_R in one triad. Include intrinsic count dipole d_int,a and selection/systematic response. A universal k_a without the selected flux/redshift distribution is insufficient.

**R4 — Candidate choice; complete.** Use a vector residual and its full covariance rather than dipole amplitude alone. Preserve the same estimator, window and clustering/systematic law in observed and simulated quantities; the R54 owned-catalogue result is reused instead of downloading a catalogue to increase significance.

**R5 — Derivation; derived.** At first order,

\[
D_R=(v_O-v_R)/c,\quad D_a=k_a(v_O-v_j)/c+d_{{\rm int},a},\quad V_j=v_j-v_R,
\]

so

\[
r_a=D_a/k_a-D_R+V_j/c=d_{{\rm int},a}/k_a.\tag{L2.1}
\]

This is an endpoint identity for a common shell under the response assumptions. For a stacked residual r=B y, C_r=B C_y B^T includes all cross-probe covariance. A quadratic r^T C_r^+r requires exact support and a justified joint sampling law. If only marginal valid tests are available, R8 J1 combines their common-state acceptance sets with allocated error probability; missing cross-covariance is not set to zero.

**R6 — Checks; complete/reused.** All terms in L2.1 are dimensionless. Coincident frames and zero intrinsic dipole give zero residual. Endpoint velocities resolve the sign ambiguity between historical beta_RM conventions. A count dipole and a distance velocity from different shells do not obey the same-shell identity without an evolution hypothesis.

**R7 — Evidence; reused.** R54 owned-estimator tails with receipt systematics are Quaia .309 and NVSS .421, versus mock-only .00599/.329. Power against a doubled dipole is .20, below the retained .80 criterion. The latest joint closure p=.0865 is conditional on the R54 count and CF4 laws. R58 adds no new count likelihood or power claim.

**R8 — Decision.** `unresolved` anomaly interpretation on the owned samples; underpowered non-detection does not establish the kinematic-only hypothesis. The reusable result is the vector residual contract and the explicit systematic sensitivity, not a rejection of published anomalies on different catalogues.

**R9 — Coding connection.** A future joint consumer must carry `(population, shell, k_a, direction frame, selection, covariance law)` and the full covariance of r. Five-view Pi must state whether it is a count-null tail or a posterior exceedance. The R58 CF4-only likelihood is not silently promoted to this joint experiment.

**R10 — Closeout.** Retain the existing count result as a bounded companion to the mixed CF4 analysis. Local work is reproducibility and manuscript integration; absent response/cross-covariance is recorded as an explicit limit rather than replaced by new data acquisition.

## L3 — Beyond-FLRW kinematic quantity measurement

**R1 — Contract; complete.** Pull the actually fitted apparent vector/STF coefficients back to direct kinematical variables and identify exactly which component or mixed functional the current experiment measures.

**R2 — Evidence reuse; reused.** July30 vector/tensor MES plan §2; R7 T3/T4; R9 T2; R39 physical theta and functional-identifiability contract; R54 T6/T7 and the reviewed R58 rank solver. The user’s physical-theta likelihood was already designed in R39; R58 supplies a real source-bound carrier consumer.

**R3 — Assumptions; complete.** The local optical relation, for a named congruence and sourceward n, is

\[
\mathbb H(n)=H-A_an^a/c+\sigma_{ab}n^an^b,\quad d_L=cz/\mathbb H(n)+O(z^2).\tag{L3.1}
\]

This defines a constant low-z phenomenological pullback, not an exact finite-z solution for arbitrary kinematics. Keep dimensionless s=sigma/H, w=omega/H, a=A/(cH), beta=V/c plus free calibration dipole d_cal and STF q_cal. The signed endpoint of beta is the specified coherent velocity V relative to the redshift reference frame.

**R4 — Candidate choice; complete.** Use the 22-coordinate state theta=(s5,w3,a3,beta3,d_cal3,q_cal5) and one map alpha=K theta. Direct physical components and mixed functionals are legitimate x entries; their identifiability is decided after the pullback.

**R5 — Derivation; derived.** The map is

\[
V=c\beta,\qquad d=-a+d_{\rm cal},\qquad\kappa=s+q_{\rm cal}.\tag{L3.2}
\]

Since X_m has column rank11 and K has row rank11, rank(X_m K)=11. Its null space has dimension11: arbitrary w (3), `(a,d_cal)->(a+u,d_cal+u)` (3), and `(s,q_cal)->(s+S,q_cal-S)` (5). Thus the likelihood L_m(theta)=L_m(K theta) constrains beta, -a+d_cal and s+q_cal. It leaves the individual s,w,a components unbounded on the unrestricted calibration domain. A differentiable functional phi is locally data-identifiable only if Dphi annihilates this null space; global constancy on each fibre is required globally. For example `beta^T(s+q_cal)beta` is a mixed identifiable apparent functional, whereas `beta^T s beta` changes under a shear–calibration null displacement.

**R6 — Checks; derived/reviewed solver.** Symmetric tracefree nn contractions cannot contain the antisymmetric vorticity at this leading order. The units in L3.1 and L3.2 agree. The R58 solver compares rank in declared physical scales with column equilibration and refuses unresolved disagreement; its null basis/estimability checks were independently reviewed. The exact posterior statement under a prior is `p(nu|iota,y)=p(nu|iota)`; marginal width can change through prior correlation, so it is not evidence of new data rank.

**R7 — Execution status.** All seven observed 32×11 fits have rank11. The 22-coordinate pullback and five-view serialization are implemented in `build_r58_views.py`; the code was under review when this loop record was drafted. The rank11/null11 conclusion above is an algebraic result conditional on the checked rank11 apparent design. Do not invent an executed physical interval table until `FIVE_VIEW_RESULT.json` and its review exist.

**R8 — Decision.** `derived` physical identified quotient, `numerically checked` apparent coefficient likelihood. The owned data support a joint apparent vector/STF inference. Individual shear, acceleration and vorticity require additional stated physical/calibration information for finite bounds. This is an explicit measurement statement, not a universal impossibility theorem.

**R9 — Coding connection.** Keep coordinate names, normalization H, triad, epoch/window, O(3) parity, and physical-map hypothesis with x. A free null coordinate serializes unbounded support rather than a zero variance from a pseudoinverse. Direct and mixed functionals are pushforwards of one set; they are not independent data factors.

**R10 — Closeout.** The local continuation performs native replay of the current likelihood and physical/five-view builder, then reports the rank and null directions in the bounded manuscript. It does not impose a narrow prior merely to obtain a complete physical-component table.

## L4 — Anisotropy evaluation and classification, including Bianchi spaces

**R1 — Contract; complete.** Determine the shape information actually present in a vector–STF carrier and distinguish observable orbit classification from identifying a dynamical Bianchi family.

**R2 — Evidence reuse; reused.** R7 T1/T7, R8 O1/O4, R9 revision2 F1/F3; R39 typed tensor/parity contract; R48 Bianchi novelty assessment and R49 general tilted Bianchi design. The internal history already records metric/group-action degeneracies and the need for source-bound transfers.

**R3 — Assumptions; complete.** Let K be the apparent symmetric tracefree tensor in S1. Under rotations R, K->RKR^T and d->Rd. Polar and axial vectors transform differently under reflections. Actual sky windows remain in X_m,C_m; an isotropic representation theorem does not remove survey mode coupling.

**R4 — Candidate choice; complete.** Retain K and d jointly. Norm, eigenvalues, shape and relative contractions are derived x views. An eigen-axis is undefined or unstable at repeated eigenvalues, and the zero tensor has no normalized shape. The current family claim is an observable compatibility class only.

**R5 — Derivation; derived/reused.** With eigenvalues summing to zero, the normalized shape

\[
s_K=\sqrt6\,\mathrm{tr}(K^3)/[\mathrm{tr}(K^2)]^{3/2}\in[-1,1]\tag{L4.1}
\]

has extrema on the repeated-eigenvalue strata, obtained by constrained extremization with fixed trace and Frobenius norm. It complements the amplitude but loses orientation. A mixed directional observable is

\[
h(n)=d\cdot n+K:nn=\ell(n)^T\alpha,\quad
\ell(n)=(0_3,n_3,E_0:nn,\ldots,E_4:nn).\tag{L4.2}
\]

Its exact image under S4 is

\[
\ell^T\hat\alpha_m\pm\sqrt{\chi^2_{11,.95}\,\ell^TJ_m^{-1}\ell}.\tag{L4.3}
\]

The variance includes the polar–STF term `2 n^T Cov(d,kappa) w(n)`; this is a direct mixed functional whose interpretation depends on the full tensor covariance. For the model union, take the union of the model images; minimum/maximum endpoints give only its outer interval hull. Nonlinear shape/chirality images require the original set, since support functions see its convex hull.

**R6 — Checks; complete/reused.** The STF norm and L4.1 use the orthonormal basis; s_K is undefined at zero. L4.2 is invariant when tensor, direction, response and covariance are rotated consistently. Cross-covariance is required by the variance expansion, independently of any claimed new method. The R58 independent data reconstruction checks the actual mixed response and covariance against a separate WLS implementation.

**R7 — Evidence; executed mixed experiment/reused classification limits.** The maximum canonical polar–STF correlations in the seven actual window carriers range .80365–.84256. This is strong dependence of measured blocks, not a detected physical shear–velocity coupling. The R54 constant quadrupole 2.2–2.6% H remains exploratory/HOLD; no calibrated nonlinear shape or stable physical axis is promoted here.

**R8 — Decision.** The executed contribution is joint directional uncertainty with real window coupling. Bianchi family identification stays `blocked` by the absent admitted family transfer, whereas observable tensor likelihood and directional support are available. A space with identical relevant transfer on the observed channels belongs to the same observational equivalence class regardless of its label.

**R9 — Coding connection.** Raw K, its full joint covariance with V,d, and the reconstruction basis belong to x. L4.3 is a linear-support consumer of the same confidence set. An amplitude-only/scalar-x baseline is a lossy comparator, not the strongest competing full-information method. The fair full-covariance GLS comparator ties the tensor carrier by construction.

**R10 — Closeout.** Include the mixed covariance and directional-support mechanism in the bounded note. Leave physical family labels and uncalibrated axes out of its claim table; native replay and manuscript production are the remaining local work.

## L5 — Redshift- and direction-dependent Hubble factor

**R1 — Contract; complete.** Measure the conditional apparent directional expansion on the owned catalogue and determine the effect of keeping the full vector–STF covariance under existing nuisance choices. This is the new executed observational branch of R58.

**R2 — Evidence reuse; reused.** R7 T7/T8, R8 J1/P2, R9 T2 and revision2 D1–D3; R36 historical carrier; R54 EQ-30–37 and the catalogue-level log estimator. R54’s bias repair and cached cosmic body are retained, not relabelled new.

**R3 — Assumptions; complete.** Work with Gaussian distance-modulus errors, fixed selected rows/window/nuisance operators and the pinned linear cosmic covariance. With E(z)=H(z)/H0 and chi_hat=∫dz/E,

\[
g(z)=\frac{(1+z)/(E(z)\widehat\chi(z))-1}{c}.\tag{L5.1}
\]

The units are (km s^-1)^-1; gV is dimensionless. The fiducial geometry, redshift-space positions, catalogue selection and nuisance choices are part of the experiment.

**R4 — Candidate choice; complete.** Compare the full C_m in S2 to the intentionally misspecified block covariance B_m=diag(C_polar,C_STF), keeping y_m and X_m unchanged. The seven models are `log`, `log_mono`, `log_split`, `log_survey`, `log_mono_radial`, `log_mono_galactic`, `log_mono_error`. Do not select the smallest p or rank their different compressed densities as one common-data evidence calculation.

**R5 — Derivation; derived/reused.** If d_obs=D exp(s epsilon) and weights scale as d_obs^-2, linear distance regression has E(H_hat)/H=exp(s²/2) for common s. Log distance removes this particular error-in-variables bias. For the retained compressed Gaussian experiment, let P be the Euclidean projector onto the whitened X_m. Then

\[
q_0=\|C_m^{-1/2}y_m\|^2=W+R,\quad
W=\|P C_m^{-1/2}y_m\|^2,\quad R=\|(I-P)C_m^{-1/2}y_m\|^2.\tag{L5.2}
\]

Under alpha=0, W~chi²_11 and R~chi²_21 independently, while q0~chi²_32. These are different valid conditional tests. The block-covariance estimator has linear map L_B=(X^T B^-1 X)^-1 X^T B^-1, nominal covariance (X^T B^-1 X)^-1, but true sampling covariance L_B C L_B^T. Its nominal ellipsoid law is the weighted sum Σ_j lambda_j Z_j², where lambda are the covariance-ratio eigenvalues; it is not generally chi²_11.

**R6 — Independent checks; complete for the stated experiment.** The independent reviewer reconstructed observations, design, white covariance and GLS with a separate direct-WLS oracle; existing cosmic cache reuse remained explicit. All seven marginal R54 headlines reproduce numerically. The generic likelihood review checks direct Gaussian log likelihood, rank/estimability, interval inversion and large null directions. This validates implementation of the fixed experiment, not the correctness of the catalogue selection or cosmic model.

**R7 — Actual results; numerically checked.** All fits have rank11. Modelwise apparent-zero Wald p ranges 1.97e-7–.0153427; the finite-list maximum is .0153427. The raw32 null maximum is .1122129; residual-model adequacy tails range .43380–.88834. These outcomes are consistent with L5.2: the 11-dimensional modeled response isolates a different component of the data than the raw32 omnibus statistic. Each simultaneous coordinate interval includes zero in the union, although the joint ellipsoid union excludes the common origin at this conditional level; a coordinate hull loses joint geometry.

Deleting polar–STF covariance changes individual fitted coordinates by at most .189–.408 of the full-fit sd across the seven models. This shift is a descriptive comparison of correlated estimators, not a significance test. The actual-to-nominal variance eigenvalues span about .535–1.473. Under the **declared full Gaussian law**, 20,000 parameter-error draws per model give nominal95% block-model ellipsoid coverage .93205–.93560 versus full-GLS .94960; Monte Carlo standard error is approximately .0017–.0018. An independent 60,000-draw reconstruction reproduces the same undercoverage scale. This is a calibration experiment on the actual design/covariance, not empirical coverage over repeated universes or a validated law under unknown systematics.

**R8 — Decision.** The narrow new result is that owned CF4 vector/STF window coupling has a measurable effect on joint uncertainty and an explicit covariance-deletion ablation undercovers. The conditional finite-family apparent-zero Wald tail is reported with its exploratory and model restrictions. It is not a physical acceleration/shear detection. Full GLS and the sufficient tensor carrier are equivalent methods on this experiment.

**R9 — Coding connection.** `run_r58_owned_tensor.py` builds S1–S2; `r58_mixed_tensor_likelihood.py` evaluates S3–S4, supports estimable contrasts and retains residual information. Output records model-specific inputs, nuisance, row order, normalized likelihood and joint intervals. The 95% union is retained modelwise; its coordinate hull is labelled as a hull rather than an exact multidimensional set.

**R10 — Closeout.** The source-bound calculation is executed without acquiring data or recomputing the expensive pair sum. Local work is native replay under the committed environment, final artifact binding and writing the bounded covariance/calibration result. A new survey, richer cosmological model search or renewed significance tuning is outside this slice.

## L6 — Distinguishing a local boost from a global tilt

**R1 — Contract; complete.** Determine which depth-response and frame statements survive the latest theory corrections and the full mixed carrier. Separate the named constant-velocity submodel from general homogeneous evolving tilt.

**R2 — Evidence reuse; reused.** R7 T9, R8 P2, R9 T1/T2, R39 frame/likelihood contract; R54 T7c/T9 and L6 data; the R58 independent proof review’s evolving homogeneous-velocity counterexample.

**R3 — Assumptions; corrected.** `CONST_V` means V_j=V for the specified observed windows. “Homogeneous” means no spatial dependence on a constant-time slice; it does not force the same velocity at different emission times on the past light cone. A physical tilt model needs its own evolution/transfer. The CF4 redshift frame and sourceward convention determine the sign of V; aliases beta_RM/beta_MR alone do not determine it.

**R4 — Candidate choice; complete.** Compare the response columns g(z)n and constant n after the actual nuisance/window/covariance map. Preserve the model’s full response into STF rows. Treat general evolving V(z), intrinsic count dipoles and calibration evolution as different model classes, not as aliases of CONST_V.

**R5 — Derivation; derived/reused.** For one directional component with depth covariance c, constant fractional dipole A and velocity V,

\[
F_{V\mid A}=g^Tc^{-1}g-\frac{(g^Tc^{-1}\mathbf1)^2}{\mathbf1^Tc^{-1}\mathbf1}.\tag{L6.1}
\]

This is the Schur complement after fitting A. It vanishes exactly when g is constant in the supported experiment; actual sky/nuisance rank must also be retained. For the alternative observer/global response pair in R9, R(z)=H(z)∫_0^z dz'/H(z')-(1+z) obeys R'=H'∫dz'/H and R=-1+(1+q_dec,0)z²/2+O(z³), showing weak low-z separation. These kernels describe different declared physical decompositions and are not substituted for one another by name.

As a constructive counterexample to “homogeneous tilt implies CONST_V,” freely moving nonrelativistic test matter on FLRW has physical peculiar velocity V(a)=V0/a, hence V(z)=(1+z)V0 at first order. It is spatially homogeneous yet varies across observed shells. Substitution into L2.1 still gives exact same-shell closure. Therefore failure of CONST_V cannot exclude arbitrary homogeneous evolving tilt.

**R6 — Checks; complete/reused.** L6.1 is nonnegative by Cauchy–Schwarz in the c^-1 inner product; it tends to zero when the depth responses become proportional. The independent proof-check artifact verifies the evolving example at z=.1,.2,.5 with closure residual below 1.4e-19. This counterexample refutes an overbroad identification of two hypotheses, not the existence of a useful constant-velocity test.

**R7 — Evidence; reused plus new carrier scope.** R54 final closure p=.0865, its named CONST_V joint hypothesis p=.0832, independent-frame model p=.158 and calibration+count-offset model p=.531 remain separate, conditional results. R58 fits one V alongside apparent d,K with full response; it does not rerun a complete count–distance evolving-tilt test. The broad V-coordinate union intervals, e.g. V_x∈[-1235.28,722.66] km/s at the simultaneous95% hull level, reflect weak separation in this joint fit and do not provide a physical tilt limit.

**R8 — Decision.** Local boost/general tilt discrimination remains `unresolved` on the owned experiment. The delivered positive result is the correctly named response model, its measured apparent-state likelihood and its identifiability limits. No arbitrary-tilt rejection is claimed.

**R9 — Supersession and implementation.** This section **supersedes the broad wording** in `R54/THEORY_LOOPS.md`, Loop L6, that equates global tilt with constant velocity at every depth. Retain the old numerical result and relabel its hypothesis `CONST_V_ON_SELECTED_WINDOWS`; leave general evolving tilt untested. The physical builder records V=c beta only for its declared constant low-z response; it does not manufacture a general Bianchi/tilt transfer.

**R10 — Closeout.** Integrate the corrected hypothesis label and limits into the native replay and bounded manuscript. Do not open another solver/data campaign to turn the current CONST_V result into a broader exclusion.

## Five-view restoration and the precise role of tensorization

R39 `VECTOR_TENSOR_X_FRAMEWORK.md:124–156` is the controlling definition lineage; R7–R9 joint-set and path results supply its mathematics. The five views share one experiment:

| View | Definition in this slice | Availability and boundary |
|---|---|---|
| x | typed observed y32, its predicted X alpha, alpha’s direct polar/STF components, and declared physical/mixed functional maps | Measured and predicted roles remain distinct. Direct theta is reached only through the declared physical map. |
| Q | gauge relative to a declared matching body, e.g. K0,m={alpha:alpha^T J_m alpha≤c95²}; at the fit Q=√(W/c95²) | This is a statistical coefficient-noise body. A physical MES ceiling is unavailable unless separately supplied. |
| Pi | tail of a named law for a named score; here W against chi²_11, q0 against chi²_32, or residual against chi²_21 | They answer different questions. A compatibility set alone supplies no probability measure. |
| F | support-utilization: h_C(u)/h_K0(u) where denominator is positive; for the ellipsoid h_C(u)=u^T alpha_hat+c95√(u^T J^-1u) | Support ratio is **not a filling fraction/occupancy**. Occupancy needs a declared measure and eligible physical/reference domain. |
| G_F | typed tensor-functional values across windows with full covariance, initial level and contrasts | R39 explicitly permits raw tensor-functional paths. An invertible path representation is not a new independent likelihood or physical evolution measurement. |

For a four-window tensor path, T first reorders the polar12/STF20 vector into four 8-vectors and maps `(Y0,Y1,Y2,Y3)` to `(Y0,Y1-Y0,Y2-Y0,Y3-Y0)`. T is invertible with absolute determinant1, so y'=Ty, X'=TX and C'=TCT^T preserve S3. This is the R9 revision2 D3 mechanism. Differences alone erase the common mode. The physical five-view builder must verify this equality and preserve source/window/basis metadata.

For the finite nuisance union, h_union(u)=max_m h_Cm(u); support bounds alone describe its convex hull, not holes or orientation strata. When Q has a common anchor it can be evaluated on the union; model-specific noise anchors must remain labelled modelwise. No five-view quantity is multiplied into L again. The demonstrated scientific role is preserving signed components, mixed directional uncertainty, explicit reference-body choices and dependence across windows; tensorization cannot exceed the power envelope of the exact same likelihood.

## C1–C10 execution account

| Stage | Actual account and evidence | State at drafting |
|---|---|---|
| C1 Goal/baseline | Fixed source HEAD, owned35970 rows, R54 cached operators/body and seven nuisance models; new output full32×11 mixed likelihood | complete |
| C2 Formula–data–code | S1–S3 map to runner/operator template multiplication and `r58_mixed_tensor_likelihood.py`; original marginal receipts retained | complete |
| C3 Numerical design | Whitened factor/SVD, declared scaling and equilibrated rank check, null-space estimability, normalized centered likelihood, full covariance | complete for reviewed kernel |
| C4 DAG/resources | Existing R54 cached body reused with hashes, labels/model keys and numerical parity; no downloads or new pair sum | executed scoped reuse |
| C5 Implementation | Owned runner and mixed likelihood implemented; physical/five-view builder exists with L3.2 and invertible depth transform | complete; final builder/physical map and actual seven-model directional results independently verified |
| C6 Implementation checks | Independent review records25 kernel tests passed plus24 independent full-rank GLS/contrast/logL oracles; do not extend this receipt to later untested changes | implementation-verified scoped |
| C7 Scientific checks | Independent catalogue/operator reconstruction, source covariance/response checks, same-carrier block deletion sandwich covariance; R54 theorem corrections backed by explicit counterexamples | numerically checked/derived conditional |
| C8 Reproducibility | Python3.12.14/NumPy2.3.5 recorded in owned result; seven-model legacy reproduction and independent covariance checks; exact operator-byte replay explicitly false | numerical reproduction checked; native final replay pending |
| C9 Independent review | `REVIEW/MATH_IMPLEMENTATION_REVIEW.json`: PASS_SCOPED_WITH_EXPLICIT_LIMITATIONS; `REVIEW/DATA_INDEPENDENT_REVIEW.json`: independent finite-assertion verification, no findings; physical-view review is separate | reviewed scope only |
| C10 Decision/handoff | Bounded mixed-covariance/calibration note; source/results/tests and exact native commands supplied by the R58 handoff; no acquisition or new research expansion | native replay and manuscript pending; final builder binding complete |

The remaining obligations are one native reproduction of the committed candidate and completion of the bounded manuscript with generated figures/tables and verified citations. Promotion beyond C0 requires separate evidence for the relevant physical/selection model; neither a successful test count nor a closed DAG node supplies it. The present slice ends with its measured effect and limitations, including an honest TIE to full-information GLS.

Final integration: 57 R58 tests passed (1 optional fixture test skipped; equivalent full-data runner executed separately); 39 affected R54 module/theorem tests passed against the repaired module overlay. REVIEW/VIEWS_INDEPENDENT_REVIEW.json binds builder and actual FIVE_VIEW_RESULT. Depth path logL error2.84e-14; independent directional interval error1.31e-15. No full-repository test claim.
