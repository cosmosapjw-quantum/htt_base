# From observed anisotropy to physical motion

The mathematical results in this repository become most useful when arranged around an inverse problem: what can a measured sky or catalogue tell us about the motion, deformation and geometry of its sources? The answer depends on what the observation preserves. A temperature multipole preserves an angular pattern; a redshift–distance slope preserves a contraction of a velocity derivative; a survey window preserves a weighted average. Each can discard directions that a subsequent normalization or statistical calculation cannot recover.

This chapter follows that chain from physical state to observable response and uncertainty. It synthesizes 26 families whose representative statements and assumptions were read in the repository. The source basis is the adaptive commit `0d5ab96bdb55398076629099664c77517ec33bb4`, supplemented by the historical identities recorded in the inventory. Analytic arguments, scoped formal components and statistical constructions retain their stated domains. The chapter does not report a new solver run, proof replay or observational fit.

## Which motion is being measured?

Choose a future unit timelike congruence \(u^a\), with metric signature \((-+++)\), and write the physical velocity as \(U^a=cu^a\). Expansion measures the local change of volume, shear the change of shape, vorticity the local rotation, and acceleration the bending of the chosen worldlines. They are properties of that congruence. Velocities between radiation, matter and observer frames are additional objects: a local observer boost and a radiation–matter tilt need not describe the same motion.

The signed comparator illustrates why these distinctions matter. In its registered convention,

\[
x_C=\Sigma^2-W^2+\Omega_{\rm tilt}+\Delta\Omega_k,
\qquad
W^2=\frac{\omega_{ab}\omega^{ab}}{6H^2}
=\frac{|\boldsymbol\omega|^2}{3H^2}.
\]

Oppositely signed contributions can cancel. On the algebraic shear–vorticity slice, \((\Sigma^2,W^2)=(a,a)\) gives \(x_C=0\) while the unsigned sum is \(2a\). Thus a small comparator does not imply small deformation and rotation separately. The factor relating tensor and vector vorticity norms also matters: changing it changes a ceiling even when the symbol \(W^2\) remains unchanged. These are the cancellation and normalization results in **F01**. Their observational use is to prevent a scalar balance from being read as a measurement of every physical sector.

Whether such an algebraic state exists physically is a separate question. A hypersurface-normal congruence is irrotational by Frobenius. The registered Bianchi-I lower and interior targets requiring \(W^2=1/25\) and \(3/100\) therefore conflict with that same normal congruence. The exact obstruction in **F02** explains why a box endpoint can be mathematically attainable in component coordinates yet absent from the chosen physical constraint surface. Moving to a different tilted congruence changes the question and requires a new, explicit frame and matter binding.

The same distinction applies to multiple matter streams (**F09**). Equal positive-weight streams moving in opposite directions have zero first velocity moment but a nonzero second moment and anisotropic stress. A small bulk velocity can therefore coexist with substantial relative motion. The registered first-order relation \(\beta_{RO}=\beta_{RM}+\beta_{MO}+O(\beta^2)\) is useful at that order; finite boosts require Lorentz composition. Whether relative motion decays further depends on the equation of state, drag and interactions. The repository's stable drag fixtures and radiation boundary are class-conditional mechanics, rather than a universal assertion that all tilt relaxes.

Sources: `formal_pr169/Pr169UnsignedLeakage/Basic.lean`; `formal_pr186/Pr186W2/Basic.lean`; `formal_pr223/Pr223Multifluid/Basic.lean`; `formal_pr171/Pr171TiltRelaxation/Basic.lean`; PR #368's typed-attainability result; `docs/research_reports/theory_packs/K1R_TYPED_KINEMATICAL_MES_THEOREM_PACK.md`.

## What does a small radiation anisotropy constrain?

The conditional MES programme (**F03**) connects restrictions on radiation multipoles and their derivatives to restrictions on named kinematical invariants. Its useful output is a premise-matched admissible body for physical states. The geodesic branch fixes acceleration structurally to zero; that premise is different from having measured a numerical zero-radius acceleration anchor. Outside that branch, an acceleration bound requires an additional authority, such as an Euler equation with a specified matter model and density-gradient bound.

A rotationally invariant sector bound constrains magnitude without choosing orientation. For an orthogonal representation and \(B_R=\{v:\|v\|\le R\}\), membership is unchanged by every allowed rotation. Such a ball cannot select an eigenframe, handedness or preferred vector direction. This is why an upper bound on shear magnitude does not supply a shear tensor, and why an observed temperature quadrupole is not itself physical shear despite sharing an STF rank-two representation.

For a genuinely factorized anchor body \(B=\prod_jB_j\), its Minkowski gauge is

\[
\rho_B(X)=\max_j\rho_{B_j}(X_j).
\]

This maximum retains sector stress that a signed sum could cancel. Once response, nuisance or physical constraints couple the sectors, the full feasible body need not factorize, and its geometry must be retained. The required bridge to observation is a transfer and measurement map with the same frame, normalization, perturbative order and derivative assumptions as the anchor. Small measured endpoint multipoles alone do not provide all those inputs.

Sources: `docs/research_reports/theory_packs/T3_CONDITIONAL_MES_GEOMETRY_THEOREM_PACK.md`; `docs/research_reports/theory_packs/K1R_TYPED_KINEMATICAL_MES_THEOREM_PACK.md`; `docs/research_program/THEOREM_SIGNATURES_V2.yaml`.

## What information is present in the angular pattern?

For a real sky, stored-real harmonic coordinates retain five quadrupole and seven octupole degrees of freedom. The harmonic–STF maps in **F11** express those same patterns as \(T_2(n)=Q_{ab}n^an^b\) and \(T_3(n)=O_{abc}n^an^bn^c\), with explicit norm factors. For the repository's stated normalization,

\[
Q:Q=\frac{15}{8\pi}\|c_2\|^2,
\qquad O:O=\frac{35}{8\pi}\|c_3\|^2.
\]

These maps preserve morphology; they do not add an independent channel. Multipole-vector coordinates likewise describe the same underlying temperature tensors when their amplitude, sign and permutation conventions are retained.

Powers \(C_2,C_3\) preserve sizes while removing relative orientations. A common physical sky rotation acts on both tensors together, whereas rotating them independently erases their alignment. On the nonzero cyclic domain, the contraction \(v_a=\bar O_{abc}\bar Q_{bc}\) and Krylov frame \(K=[v,\bar Qv,\bar Q^2v]\) support reconstruction of the common proper-rotation orbit when \(\det K\ne0\). The sign of this determinant carries orientation information that can distinguish a mirror pair. Singular strata require their own descriptions; a well-defined invariant packet on the cyclic domain is not automatically a decoder for every degenerate state.

The observable implication is practical: preserve full coefficients and their joint uncertainty before choosing an alignment or chirality statistic. If an external flow direction is part of the question, retain its relation to the sky as well. Quotienting away absolute orientation and then asking for its depth coherence would request information already removed. Conversion from these observational invariants to physical shear or tilt still requires a transfer response.

Representation stability matters even before physical interpretation. A nearly degenerate eigensystem may have a well-measured tensor but an unstable preferred axis. In such a case the tensor and its uncertainty remain useful observations while an axis summary should remain unresolved or set-valued. The same principle appears in the fixed-contraction fibre: preserving a quadrupole and one octupole contraction can leave a sphere of allowed octupoles rather than a single reconstructed pattern. A direction extracted from one convenient representative would then describe a choice inside the fibre. It would not be an additional measured direction. These examples explain why the repository preserves raw tensors alongside lower-dimensional summaries.

Sources: `docs/research_reports/theory_packs/T1_STORED_REAL_STF_THEOREM_PACK.md`; `docs/research_reports/theory_packs/T2_QO_ORBIT_RECONSTRUCTION_THEOREM_PACK.md`; `docs/research_reports/theory_synthesis_20260913/REPORT.md`, §§8–9.

## How does local observer motion change that pattern?

A local Lorentz boost changes both apparent temperature and apparent direction. For thermodynamic temperature with Doppler weight one, its first-order generator is

\[
\delta_\beta T=(\beta\cdot n)T-
[\beta-(\beta\cdot n)n]\cdot\nabla_{S^2}T.
\]

The first term modulates the field; the second shifts the pattern across the sphere. They mix multipoles. In the full-sky quadrupole-to-octupole block of **F08**, \(B_Q\beta=3\beta_{\langle a}Q_{bc\rangle}\), and the associated contraction matrix is \(M_Q=(Q:Q)I+6Q^2/5\), with Frobenius normal matrix \(B_Q^*B_Q=3M_Q\). For \(Q\ne0\), it is positive definite with condition number at most \(5/3\). This supplies a stable algebraic projection onto the boost-shaped octupole component.

Physical attribution requires another step. If the intrinsic octupole is unrestricted, it can contain that same component; a stable projection need not be a unique velocity estimate. Similarly, aligned acceleration and kinematic direct-source columns can be collinear when the evolution operator is fixed and \(k_{\rm eff}=0\). That limited source identity does not establish equivalence after changing streaming, damping or perturbative order. An independently constrained intrinsic sky, covariance model or velocity anchor provides the missing discrimination.

For global tilt, an independently justified homogeneous-orbit normal \(N\) is especially valuable (**F23**). Once it is supplied, \(\gamma=-u\cdot N\) and \(\beta^2=1-\gamma^{-2}\) determine the relative tilt. A local observer measurement does not by itself select this normal. Coordinate synchronization, replacement of the physical observer and changes of the source congruence must therefore remain distinct operations.

Sources: `docs/research_reports/theory_packs/T5_WU010_LOCAL_OBSERVER_RESPONSE_THEOREM_PACK.md`; `formal_pr168/Pr168AccelKinematic/Basic.lean`; `docs/research_program/gr_statistics_loops_20260930/supplements/DOSSIER_POSITIVE_BRIDGE.md`.

## What survives masking, processing and nuisance fitting?

The observation operator determines which of the preceding distinctions reach an estimator. Boosting, beam and pixel processing, masking, synthesis and joint fitting have an order. After this processing, a low-source response \(J\) can overlap the image of an allowed high-source nuisance operator \(K\). The quotient theorem in **F12** states

\[
\operatorname{rank}(P_{\operatorname{Im}K^\perp}J)
=\operatorname{rank}[K\ J]-\operatorname{rank}K.
\]

It counts the low-source directions that cannot be reproduced by the declared nuisance class. Adding high-source columns enlarges its image. Once containment is certified, increasing that unrestricted cutoff cannot restore a surviving direction. A physical amplitude or covariance model can change the inference because it restricts which nuisance combinations are plausible; it is a new input, rather than a consequence of the quotient identity.

Numerical rank also needs an error budget. The repository's frozen additive perturbation families yield \(\Delta\Delta^T\preceq\Gamma_E\). Whitening by \(\Gamma_E^{-1/2}\) bounds the perturbation operator norm by one, so computed whitened singular values exceeding one certify corresponding true-rank directions. This construction separates numerical error from a physical high-multipole prior. Its observational value is to show which leakage or survivor conclusions survive declared integration and discretization errors. The remaining requirement is that the actual operator error belongs to the calibrated family; a large singular value cannot establish that membership itself.

An anchor coordinate change supplies a useful comparison of these directions. With response derivative \(J\), observational whitener \(W\), nuisance projector \(P_\perp\), and anchor coordinate map \(X=Lz\), the research formulation uses \(A_{\rm anch}=P_\perp WJL\) and \(\mathcal I_{\rm anch}=A_{\rm anch}^TA_{\rm anch}\). This expresses sensitivity in units of the permitted physical body. An invertible \(L\) changes scaling and conditioning while leaving response rank unchanged. Thus an attractive normalized error bar should be interpreted together with singular values and null directions: normalization can improve comparison without creating a measurement. When a new channel is proposed, the relevant question is whether it adds a direction after both noise weighting and nuisance removal.

Sources: `docs/research_reports/theory_packs/T6_WU011_PROCESSED_RESPONSE_QUOTIENT_THEOREM_PACK.md`; `docs/research_reports/theory_packs/T8_MATRIX_NUMERICAL_ERROR_ENVELOPE_THEOREM_PACK.md`.

## What do local redshift and distance observations recover?

The optical inverse in **F04** begins with ideal absolute directional data at one event: an intercept \(Z(n)=\lim(1+z)\) and an area-distance slope \(H(n)=c\,\partial z/\partial d_A|_0\). For a smooth future unit source field,

\[
Z=\zeta_0+\zeta\cdot n,\quad \zeta_0^2-|\zeta|^2=1,
\qquad H=h_0+h_1\cdot n+h_2:nn.
\]

The intercept fixes \(u=(\zeta_0,\zeta)\). Writing \(S_{00}=h_0\), \(S_{0i}=-h_{1i}/2\) and \(S_{ij}=h_{2ij}\), the symmetric derivative is \(B=S+S(u,u)g\). Acceleration, expansion and shear follow from \(A=2cBu\), the trace and the spatial STF projection. The null-ray contraction removes antisymmetric information: the complete normalization-compatible derivative retains an arbitrary spatial antisymmetric \(W\), a three-dimensional vorticity fibre.

This is a constructive local inverse for a test-source congruence. Its use for galaxies additionally requires a tracer and coarse-graining interpretation. It explains why an Hubble dipole alone cannot identify acceleration or peculiar velocity. The absolute intercept participates in the inverse, while luminosity-to-area-distance conversion needs reciprocity and the relevant transparency assumptions.

The geodesic restriction \(A=0\) sharpens this picture (**F05**). A compatible source velocity is a timelike eigenvector of the Lorentz-self-adjoint slope operator. Vanishing expansion eigenvalues can leave a family of such velocities, so a slope-only inverse becomes nonunique or sensitive near degeneracy. An absolute intercept or independent velocity anchor closes that gap. The finite perturbation estimates instead control how bounded coefficient errors and a rapidity bound propagate into \(B\), without requiring an expansion eigengap for that full-data inverse.

Sources: `docs/research_program/gr_statistics_loops_20260930/gr/OPTICAL_THEOREMS.md`; the same programme's `cas/CAS_TASKS.json`, CAS-01–03.

## Why do distance range and averaging scale matter?

An observational catalogue samples finite distances, rather than derivatives at a mathematical vertex. The Jacobi–Taylor certificate (**F07**) controls the resulting bridge. If the optical tidal operator and redshift second derivative are bounded along the entire ray, define \(\eta(s)=\sinh(\sqrt K s)/(\sqrt K s)-1<1\). Then

\[
s(1-\eta)\le d_A\le s(1+\eta),\qquad
|Z(s)-Z_0-H_0d_A/c|
\le M_2s^2/2+|H_0|s\eta(s)/c.
\]

Focusing changes affine distance into area distance; source variation contributes the Taylor remainder. Together they provide a finite-distance envelope for a local Hubble law. The conditional formal synthesis treats a supplied Jacobi system and scalar with those segment-wide bounds. Actual curvature and source-derivative bounds must come from physical inputs; they cannot be inferred merely from small local multipoles.

Distance variation also changes identifiability (**F15**). In the oracle problem with known radii and zero remainder, the unconstrained design is \(X=[E_4,\operatorname{diag}(r/c)E_9]\). Full rank thirteen requires full angular ranks and disjoint column images. At one radius, intercept changes can be absorbed into the slope. Even varying radii can retain the alias when their angular dependence has a special form. Nine unisolvent directions at one radius plus four suitable repeated directions at another give a constructive full-rank design; the physically normalized intercept chart has twelve parameters. With positive slack in finite remainder bounds, nearby physical states can still produce identical native means.

Spatial averaging introduces another effect (**F10**). In the scalar two-patch construction,

\[
Q_B=6w(1-w)(H_1-H_2)^2-2\langle\sigma^2\rangle.
\]

Different expansion rates create a variance term, so averaged backreaction and averaged shear are generally different quantities. Likewise, two survey windows can weight the same velocity field differently. The bridge between shell estimates and a physical evolution therefore needs actual angular and radial selection functions, a shared epoch convention and their cross-window uncertainty.

The remainder and window questions interact in an actual catalogue. Nearby and distant rows need not be realizations of the same local linear coefficient law with different noise. They may carry different finite-distance bias, tracer selection and calibration responses. Increasing the distance range can improve intercept–slope leverage while enlarging the remainder envelope; decreasing it can reduce that envelope while weakening the leverage. The theorem supplies a way to display this tradeoff through the joint admissible set. It does not select an optimal cut without a specified physical envelope, survey design and loss. A constructive analysis can therefore report a prespecified range of distance cuts and their resulting response spectra and feasible sets.

Sources: `docs/research_program/gr_statistics_loops_20260930/gr/FINITE_DISTANCE_THEOREM.md`; `local_cas/GRSTAT-CAS-20260930-1308KST/CAS-07/conditional_synthesis_v1_20261008/RESULT.md` within that programme; `statistics/NATIVE_INFERENCE_THEOREMS.md`; `formal_pr170/Pr170BuchertTwoPatch/Basic.lean`.

## Which additional physical information closes the inverse?

Stress derivatives supply one route (**F06**). If the energy frame is a smooth isolated timelike eigenline of stress, differentiation gives

\[
(S_T+\epsilon I)\nabla_XU=-c\,h(\nabla_XT)u.
\]

The inverse spectral gap controls the frame's derivative. Stress values, energy conditions and a metric two-jet alone need not supply this derivative information. The source packet constructs local fixed-causal-EOS families with identical event curvature and stress but unbounded acceleration; its stronger matter restriction is important. A density-gradient bound in Euler's equation, or \(T,\nabla T\) with a nonzero gap, gives the corresponding positive control. These are local statements about specified fields and neighborhoods.

Vorticity requires information absent from the optical symmetric derivative (**F21**). Two nonparallel spatial velocity-derivative directions can remove the hidden rotation, with Gram matrix \(G=\sum w(I-xx^T)\). Radiation offers another conditional route: after known expansion, shear and acceleration contributions are subtracted, an independently supplied brightness derivative and collision residual can give \(R=[M,W]\). In an eigenbasis, \(W_{ij}=R_{ij}/(m_i-m_j)\). A spectral gap controls error; independently oriented channels can remove a common commutant even when each channel alone is axisymmetric.

The newer CAS15 spectral wrapper constructs the diagonalizer and ordered spectral witness from symmetric input. Its least-squares error conclusion retains a positive observed gap and genuine minimizer as inputs. This strengthens the algebraic bridge, while the physical task remains obtaining the derivative and collision channels. It is not an extraction of vorticity from one static CMB map.

The error relation makes the role of those inputs quantitative. For a true commutator \(R=[M,W]\), an estimated symmetric matrix \(\widehat M\), residual data \(\widehat R\), and a skew least-squares solution \(\widehat W\), the scoped synthesis gives

\[
\|\widehat W-W\|_F
\le\frac{\varepsilon_R+2\varepsilon_M W_*}{\widehat\delta},
\qquad
\widehat\delta\ge\delta-2\varepsilon_M.
\]

Here the residual error, matrix operator error and bound on the true rotation are supplied in the declared norms. The observed positive gap is what permits division. The second inequality alone need not establish that positivity. Physically, nearly equal radiation-moment eigenvalues make a rotation about the corresponding directions hard to observe; independent channel orientations can be more useful than simply measuring the same axisymmetric pattern more precisely.

Sources: `docs/research_program/gr_statistics_loops_20260930/gr/ENERGYFRAME_THEOREMS.md`; `supplements/DOSSIER_POSITIVE_BRIDGE.md`; `local_cas/GRSTAT-CAS-20260930-1308KST/CAS-15/spectral_wrapper_v1_20261010/lean/WrapperIntegration.lean`, all within the same programme.

## How can spectral information control a missing response?

Retained moments constrain a distribution without fixing it. Under a common observer and measure, exact moment matching, an entropy budget \(D_H(f\Vert g)\le\varepsilon\) and a reciprocal-Hessian envelope \(W\), **F18** gives

\[
|\langle K,f-g\rangle|
\le\sqrt{2\varepsilon}\,
\operatorname{dist}_{L^2(Wd\nu)}(K,V).
\]

Only the part of the target kernel outside the measured moment span \(V\) remains uncertain. For several kernels, their residual Gram matrix defines the joint ellipsoid \(e\in\operatorname{ran}R\), \(e^TR^\dagger e\le2\varepsilon\). This preserves shared kinetic uncertainty across channels; it is different from stochastic measurement covariance.

For a specified linear collision operator, replace \(K\) by its adjoint image \(\mathcal L^*K\) (**F19**). If that image lies in \(V\), the collision moment is already determined. Otherwise the same residual construction identifies which additional bands or moments would reduce uncertainty. Static entropy control does not bound arbitrary spacetime derivatives: moment-null oscillations can remain small statically while their derivatives grow. A transport or horizontal Fisher budget is additional information.

This perspective also distinguishes two uncertainty-reduction strategies. A smaller entropy budget constrains how far the whole allowed distribution can move; an extra measured moment removes a particular direction relevant to the target kernel. The latter can be valuable even when it does not greatly alter a global distributional summary. For Bose–Einstein occupations, the programme supplies a sufficient common envelope using \(F_b(E)=(e^{bE}-1)^{-1}\) and \(W=F_b(1+F_b)\). Together with the photon measure this controls the required infrared behavior, while the ultraviolet tail decays. The parameters controlling that envelope still require spectral or external physical information; bolometric energy alone does not fix them.

Within a fixed-support thermal mixture, number and energy moments \(m_3,m_4\) permit a calibrated cubic-width bandpass error certificate (**F20**), whereas energy alone generally leaves a quadratic-width bound under the same prior. Sharp moment intervals retain the remaining mixture ambiguity; their relative minimax representative differs from a maximum-entropy representative. The observational bridge is the actual bandpass, thermal-shape/support assumptions and occupation envelope.

Angular integration has a similarly explicit boundary (**F22**). The Cartesian theorem proves that GL5 polar-cosine nodes and nine equally spaced azimuths integrate sphere monomials of total degree at most eight exactly. Products require their actual degree accounting or a tail bound. Restricted cold-electron Thomson coherency bounds involve a matrix-valued field, so scalar monomial exactness alone does not validate arbitrary spin, collision or polarization transport.

Sources: `docs/research_program/gr_statistics_loops_20260930/supplements/TEFF_POSITIVE_BRIDGE.md`; `cas/CAS_TASKS.json`, CAS-11–16; `local_cas/GRSTAT-CAS-20260930-1308KST/CAS-16/c03_cartesian_bridge_v1_20261009/lean/FullBridge.lean`.

## What can be identified when a unique state is unavailable?

The feasible-state construction (**F13**) keeps observation and physical premises together:

\[
\Theta(y;\eta)=D_\eta\cap B_{\rm MES}(y;\eta)
\cap\mathcal R_\eta^{-1}(C_y(\eta)).
\]

For an exact linear response and a feasible \(X_0\), uniqueness means that no nonzero kernel displacement remains in the admissible body. Full column rank is sufficient, but inequalities can also remove every feasible displacement. A bounded non-singleton set is partial identification; an unbounded set retains unconstrained directions. Functionals are evaluated on this same joint set. Independently extremizing a shared numerator and denominator generally yields a relaxation, because the two extremes may require different states.

The tensorized formulation makes this geometry visible without silently changing legacy names. The preserved research synthesis uses a joint physical state \(X\) and sample-by-functional values \(\phi_j(X_i)\) in place of a scalar-only \(x\) view; the specific signed \(x_C\) above remains its own functional. The role previously summarized by diagnostic \(Q\) becomes channel-matched anchor gauge and margin, \(\rho_B(X)=\inf\{t:X\in tB\}\) and \(1-\rho_B(X)\). Here diagnostic \(Q\) is distinct from the temperature quadrupole tensor \(Q_{ab}\).

For the identified finite set \(\mathcal I\), the corresponding directional support-utilization profiles are

\[
F_+(u)=h_{\mathcal I}(u)/h_B(u),\qquad
F_\pm(u)=\max\{h_{\mathcal I}(u),h_{\mathcal I}(-u)\}/h_B(u),
\]

where the denominator is positive. These source-defined profiles retain direction and active constraints; they are not silently substituted for every legacy filling-fraction field. For a declared law,

\[
\Pi_\phi(c\mid\eta,\mathcal L)
=\Pr_{\mathcal L}\{\phi(X)>c\mid\eta\}.
\]

Vector or tensor outputs require a specified event or scalarization. \(G_F\)'s structured continuation is a depth/mask/feature-transport path rather than a universal scalar ratio. The current `depth_path.py` forms adjacent residuals \(y_{j+1}-K_jy_j\) and requires full covariance blocks; it does not infer their Gaussianity or physical meaning. `functional_pushforward.py` explicitly leaves legacy scalar reports unchanged and retains coupled posterior draws and undefined mass. Thus the research formulation, compatibility reports and current supplied-law computations remain distinguishable.

For a Euclidean sector radius \(R_j\), the quadratic saturation \(S_j=\|X_j\|^2/R_j^2\) equals the square of its radial gauge. This relates the two diagnostics without making their numerical excesses identical: \(\max(\rho-1,0)\) and \(\max(\rho^2-1,0)\) have the same acceptance boundary but different margins. If the denominator is a fixed external ceiling, a numerator interval can be divided by it monotonically. When the ceiling is estimated from the same realization, the ratio must retain that joint dependence. A separate numerator interval and denominator interval do not automatically describe all attainable pairings.

The same care determines the meaning of an exceedance curve. Under a matched empirical null law, \(\Pi_\phi\) describes that diagnostic distribution; under an explicitly supplied posterior law it is a posterior pushforward. Neither is automatically the probability that the physical model is true. The current finite functional image also retains records where the requested quantity is undefined, for example because an anchor is unavailable. Conditioning them away would change the question unless that conditioning was declared. These distinctions allow the tensorized diagnostics to remain physically interpretable as they move between feasible sets, null ensembles and posterior draws.

Sources: `docs/research_reports/theory_packs/K1R_TYPED_KINEMATICAL_MES_THEOREM_PACK.md`; `docs/research_reports/theory_synthesis_20260913/REPORT.md`, §§16–17,23; `htt/src/common/anchor_geometry.py`; `htt/src/common/depth_path.py`; `htt/htt/htt/infer/functional_pushforward.py`.

## What does the statistical law justify?

Native-observation inversion (**F14**) models measured redshift and distance modulus jointly, retaining latent distances, calibration and admissible finite-distance remainder. Under a known positive-definite covariance \(C\), fixed linear nuisance matrix \(F\), and the correct Gaussian observation law, whitening and projecting out that nuisance give

\[
\|PC^{-1/2}[y-m(\theta_*)]\|^2\sim\chi^2_\nu,
\qquad \nu=m-\operatorname{rank}F.
\]

Inverting this true-parameter pivot and projecting the resulting set gives simultaneous physical coverage. A nonempty full set with an empty geodesic subset rejects geodesicity within the declared model. An empty full set signals model incompatibility. Latent-parameter fitting does not turn its optimized minimum into the same pivot, and selection using noisy observables requires its actual selected-data law.

Singular Gaussian laws retain an exact support (**F24**). A residual outside \(\operatorname{ran}C\) is incompatible; inside it, \(r^TC^\dagger r\) uses covariance rank as degrees of freedom. Adding a ridge changes that support. Products sharing a sky, seed or calibration need cross-covariance: \(\operatorname{Cov}(A-B)=C_{AA}+C_{BB}-C_{AB}-C_{BA}\). Valid marginal confidence sets can instead be combined using a preassigned union-bound budget, without assuming independence.

Estimated covariance changes calibration (**F25**). The classical independent Gaussian/Wishart Hotelling model uses an \(F\) law with \(n>k\); the Hartlap factor corrects an inverse-covariance mean bias, not every tail probability. The repository's special Imbens–Manski construction also assumes a particular joint endpoint law with deterministic width. Neither calibration automatically transfers to random anchors or a differently estimated covariance.

Finite-null ranks offer another route (**F17**). Exchangeable observed/reference rows and a permutation-equivariant complete analysis yield the conservative rank \(p=(1+\#\{T_i\ge T_0\})/(B+1)\). Fitting, selection and missingness belong inside that analysis. A correct formula cannot repair a null ensemble with mismatched mask or noise. Exact enclosures of one fixed statistic can support adaptive numerical stopping while preserving the enclosure; changing the analysis after inspecting the data is a different selection problem.

Sources: `docs/research_program/gr_statistics_loops_20260930/statistics/NATIVE_INFERENCE_THEOREMS.md`; `docs/research_reports/theory_packs/T4_FINITE_NULL_ROW_EQUIVARIANCE_THEOREM_PACK.md`; `docs/research_reports/theory_synthesis_20260913/REPORT.md`, §§18–21.

## Which distinctions remain inaccessible, and which measurements help?

The information-loss constructions (**F16**) make the scientific consequences concrete. Two admissible optical coefficient tuples can have equal separate-sector powers while one is geodesic and the other accelerated. Under the specified independent isotropic Gaussian block experiment, their compressed laws are identical although full coefficients have positive KL separation. The loss concerns those powers: the orientation-aware scalar \(J_{\rm geo}=A_aA^a/(4c^2)\) preserves the contractions needed for this property. A second construction gives identical exterior redshift–distance data with different source values inside an unobserved ball, under a common smoothness bound. More exterior samples cannot resolve that interior continuation without another input.

Absolute scale has a related ambiguity (**F23**). With a free common modulus offset, \(r\mapsto\lambda r\), \(H\mapsto H/\lambda\), and a compensating offset preserve native means whenever both transformed points remain admissible. Absolute acceleration scale then needs distance calibration. Fixed external remainder bounds can restrict this transformation and must be transformed consistently before asserting a global symmetry.

Finally, repeated analyses need a dependence-aware evidence rule (**F26**). Fixed convex averages of valid e-values retain their null-mean bound under dependence; products require conditional validity. Actual conditional expectations support Rao–Blackwell or martingale arguments, whereas an arbitrary depth summary does not. Bayesian evidence similarly changes only through the stated likelihood and normalized prior: an entirely likelihood-inactive nuisance integrates to one and receives no automatic penalty for its name or dimension.

These results point to constructive measurements: absolute intercept and distance anchors, independent transverse derivatives, source-frame collision and spectral information, angular/radial designs with useful singular values, and channels outside the existing nuisance image. Their value is that they supply a missing response or constrain a previously free physical direction. The resulting analysis can then propagate the same joint states through \(x_C\), anchor stress, directional support, exceedance and depth-path diagnostics, with the observational law and physical bridge attached at every step.

The dependence requirement has a small exact illustration. Let one fair Bernoulli variable \(B\) generate \(E_1=E_2=2B\). Each factor has null expectation one, yet their product has expectation two. Reusing one fluctuation twice therefore fails the mean condition required of an e-value product. A fixed weighted average retains it. The analogous Bayesian distinction is between a likelihood-active parameter and an inactive label: if \(L\) does not depend on \(\eta\) and \(\pi(\eta\mid\theta)\) is normalized, integration over \(\eta\) contributes exactly one. These calculations help decide whether an apparent gain came from genuinely discriminating observations, a changed physical prior, or repeated use of the same information.

Sources: `docs/research_program/gr_statistics_loops_20260930/statistics/INFORMATION_LIMIT_THEOREMS.md`; `statistics/NATIVE_INFERENCE_THEOREMS.md`; `docs/research_reports/theory_synthesis_20260913/REPORT.md`, §§19–24.
