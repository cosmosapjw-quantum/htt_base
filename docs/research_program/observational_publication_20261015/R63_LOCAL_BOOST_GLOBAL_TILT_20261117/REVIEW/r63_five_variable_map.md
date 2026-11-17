# R63 five-variable source and minimal mapping

Scope: bounded read-only support after accepted R2/C2 mapping. No remote edits, experiments, new catalogues or independent-final-review claim. Baseline f29bbab420a33aecb1c398ddd961fd45097f536b. Requested runtime gpt-6.1-sol/high; observed model/effort UNKNOWN. Skill context reused: PhysMath1.3.0 POLICY_INTEGRATION, R2/C2 evidence-first, finite scope. Root owns scientific source construction and execution.

## 1. Exact semantics and source authority

The controlling tensorized lineage is P/OBSERVATIONAL_CONVERGENCE_R39_20261107/VECTOR_TENSOR_X_FRAMEWORK.md:124–156 and P/METHOD_REBOOT_20261023/THEOREMS.md:T7 (192–237), where P=docs/research_program/observational_publication_20261015. R58 THEORY_LOOPS.md:250–270 explicitly maps this to the actual Gaussian experiment. The canonical tuple is (x,Q,Pi,F,G_F). Lowercase q is a registered scalar score or the field q(n), depending on context; it must not silently replace anchor object Q.

- **x**: a typed functional bundle x_alpha=phi_alpha(Z), with signed vector/STF values, units, frames, support, epoch/windows, observed/predicted roles and common dependence. It is not exclusively x_C. The legacy Gauss-budget scalar x_C=Sigma_G²-W_G²+Omega_tilt+DeltaOmega_k is only a many-to-one projection with its own premises; the current data do not supply all of those sectors.
- **Q**: a matching anchor/gauge/margin body, with unavailable physical anchors explicit. For K0={theta:theta^T B^-1 theta<=1}, gauge Q(theta)=sqrt(theta^T B^-1 theta). A coefficient-noise ellipsoid is an admissible **statistical reference** when labelled so; it is not a physical MES ceiling. R58's Q=sqrt(Wald/chi²_rank,.95) is precisely a noise-reference gauge.
- **Pi**: Pi_mu(alpha,t)=mu{q_alpha(Z)>t}, with scalarization and law named. It is not generically a null p-value. A confidence set alone defines no probability measure. Gaussian null Wald/adequacy tails and flat-prior Gaussian posterior gauge exceedance are different laws/questions.
- **F**: directional support h_K(u)=sup_K u.x and, when h_A(u)>0, support utilization F_sup(u)=h_K(u)/h_A(u). Signed antipodal profiles are retained. It is not measure occupancy or a physical filling fraction; those require a domain and measure. Support determines only the convex hull, not holes or chiral strata.
- **G_F**: a tensor-functional depth path containing raw signed levels, window/transport identities, full cross-depth covariance and contrasts. It is **not defined universally as a gradient of F**. Its legacy eligible positive scalar projection is a floored ratio of bin summaries, not an average of samplewise ratios. In the tensorized continuation, signed/zero-crossing values use differences and set paths.

These are five pushforwards of one experiment. They are not five fitted primitive parameters or independent likelihood factors.

## 2. Existing executable implementation to reuse

1. htt/htt/htt/infer/r58_mixed_tensor_likelihood.py:34–158, fit_linear, is the appropriate numerical kernel for R63. It Cholesky-whitens the full covariance, performs parameter-scaled SVD and independent column-equilibrated rank comparison, returns precision J, score t, whitened likelihood factor, full null basis, singular spectra, rank and declared Gaussian law. Rank disagreement fails closed. In singular models the minimum-norm representative covariance is not a finite uncertainty on null components. linear_interval:191 ff tests estimability; robust_interval:235 ff unions same-target model intervals.

2. htt/htt/htt/infer/r54_tensor_five_view.py:1–29 defines finite Gaussian views. identify:123, is_identified:142, profiled_precision:151 and carrier_mean:162 implement null/Schur/score semantics. EllipsoidBody:175 ff, gauge_range:201, support_interval:263 and support_utilization:280 provide deterministic body/region images. support_interval returns (-infinity,+infinity) for a non-estimable functional. Keep precision named J in R63 to avoid confusing it with the F support view.

3. scripts/r58/build_r58_views.py is the actual producer, not merely a source list:
   - physical_map:18–27 maps 22 kinematic+free-calibration coordinates into 11 apparent coefficients: V=c beta, dH=-A/(cH)+dcal, kappa=sigma/H+qcal; no omega column. It is a declared constant low-z response and not a general physical transfer.
   - depth_path_matrix:30–36 reorders polar12|STF20 to four8-vectors and keeps (Y0,Y1-Y0,Y2-Y0,Y3-Y0).
   - compute:70–101 builds all five views from one R58 carrier, verifies same Gaussian log-likelihood under the determinant-one path transformation, reports physical pullback rank11/nullity11, and keeps physical anchors/occupancy unavailable.
   - R63 must replace only the response-specific physical map and output names. Repeating these existing five-view calculations is not novelty.

4. htt/src/common/typefree_functionals.py:268–292 implements pointwise signed support utilization with explicit missing/zero/nonfinite anchor statuses; finite_joint_pushforward:402–431 retains undefined atom mass; strict_exceedance:460–485 computes known exceedance p and undefined mass q with probability interval [p,p+q]. It forbids inventing a probability law for FINITE_SET and requires explicit scalarization for tensor values.

5. htt/src/common/depth_path.py:14–77 stores fixed/fitted transport policy, constructs adjacent contrasts H and invertible level+contrast T, reconstructs levels, and refuses missing ordered covariance blocks rather than assuming independence. htt/src/common/htt_five_variable_state.py:1–14,36–80 stores richer tensor functional, anchor, support, law and depth-path objects.

6. htt/src/common/departure_contracts.py:125–141 is a legacy IsotropyGap **contract only**, with ratio/log/difference kind and positive epsilon floor. It is not the current Gaussian path implementation and contains no computation of G_F. METHOD_REBOOT THEOREMS.md:24 records the existing scalar production bin-summary semantics. No need to instantiate this legacy scalar class for signed R63 paths.

Avoid importing generic full_observable_x_bundle.py predicted-carrier defaults merely to obtain five-variable names. Its historical source-independent CMB/Gaia/count formulas have wider qualifications than the actual R63 response. A typed small R63 record built around the actual linear experiment is sufficient.

## 3. Minimal source-constrained R63 mapping

Let theta=(W,ell,d,kappa,other actual nuisance) with W=c b in km/s, b=present source matter velocity relative to the chosen normal frame divided by c, ell=observer-relative velocity/c (or c ell in km/s, but explicitly choose one), d=dimensionless apparent calibration dipole, and kappa=dimensionless STF response coefficients. Do not identify d with physical acceleration unless a separately qualified map is imposed. Let the chosen R63 source/history derivation supply raw columns B_W(z,n),B_ell(z,n),B_d(z,n),B_K(z,n) with units reciprocal to their parameters.

For each calibration model m, **the same source rows and actual operator** give
    X_m=O_m [B_W,B_ell,B_d,B_K,...],
    y_m=O_m eta,
    C_m=O_m C_raw O_m^T
with the reused full cross-window/cross-irrep noise+cosmic body. The original R58 carrier and R62 continuation identities are as mapped in r63_history.md. A new raw history is not supplied by a model-specific old score unless its design lies in that score's preserved span.

Whiten using the same full C_m=L_m L_m^T:
    A=L_m^-1 X_m, z=L_m^-1 y_m.
For nuisance N, Q_N projects onto col(L_m^-1 N), P_N=I-Q_N:
    A_eff=P_N A, z_eff=P_N z,
    J=A_eff^T A_eff, t=A_eff^T z_eff.
Retain the full null kernel. A functional u.theta is estimable iff u annihilates ker(A_eff). For nonlinear phi, local estimability needs Dphi ker(A_eff)=0; a global set image still requires constancy on exact fibres, not just tangent rank.

If W is the target and eta=(ell,d,kappa,...) nuisance, use one profile:
    J_W|eta=J_WW-J_Weta J_etaeta^+ J_etaW,
    t_W|eta=t_W-J_Weta J_etaeta^+ t_eta.
Return null directions and score compatibility; do not call a pseudoinverse variance a finite bound along null vectors. Prefer deriving the projected response with the whitened factor before forming J to avoid cancellation. Do not confuse this parameter Schur profile with the data-block conditional morphology innovation below.

No matter how distinct B_W and B_ell look pointwise, calibration n.d and selected-sky STF leakage may remove their distinction after P_N. Report projected singular values and the physical combinations they constrain. Unscaled or independently renormalized null columns cannot establish separation.

## 4. Five views for this mapping

**x**: save the full signed joint theta carrier (J,t,A_eff plus null basis), measured y32/C32, predicted Xtheta, W/c, ell, declared relative velocity combinations and directional expansion fields. Evaluate W·ell or tensor-vector mixed quantities on the same region/draws if requested; cross covariance changes these images. A Cartesian vector's amplitude alone loses direction and degeneracy.

**Q**: for each actually estimable target block, define a statistical origin-centred reference body in its identified quotient, with exact rank cutoff chi²_r,.95 and fitted covariance. State "fixed-C coefficient-noise reference; physical MES anchor unavailable". The full singular theta space has unbounded gauge ranges against any bounded positive-definite body; reporting a finite quotient gauge does not bound unobserved physical components. No universal speed/tilt radius is introduced just to fill a Q field.

**Pi**: choose a concrete null such as H0:W=0, profiling ell,d,kappa identically under null and full models. With fixed C, truly linear exact-zero null modes and a fixed rank, Delta chi² has chi²_delta-rank; full-model adequacy uses n-rank(X). These are conditional working-Gaussian tails. If finite-model nuisance alternatives are included, keep modelwise law identity and only form a max-p envelope for the same hypothesis/target. Distinguish this from posterior probability P(|W|>threshold).

**F**: for Theta={theta:(theta-hat)^T J(theta-hat)<=c95²}, an identified u has
    [inf u.theta,sup u.theta]
    =u.hat-theta ± c95 sqrt(u^T J^+u),
in the same numerically resolved quotient. Divide by the support of the named matching statistical/physical anchor only when positive. Non-estimable u gives unbounded support. Rotate anisotropic anchor and state together; a scalar norm or six coordinate directions does not reconstruct every support direction.

**G_F**: use exactly the same measured window carrier with a fixed invertible T retaining the common level:
    Ypath=T y, Cpath=T C T^T, Xpath=T X.
Report raw vector/STF path and chosen adjacent or level0 contrasts, not a second likelihood. The window centres are overlapping observed-z summaries; their differences are not measurements of dW/dt or global homogeneity. If the physical R63 model predicts W(z)=T_W(z)b, include that predicted path with its source law, not an arbitrary fit at each centre.

## 5. Schur morphology and gradient semantics

A genuine source-specific use of tensorization is **conditional information under the real correlated estimator**. For data split polar p / STF s in one C,
    y_s|p=y_s-C_sp C_pp^-1 y_p,
    X_s|p=X_s-C_sp C_pp^-1 X_p,
    S=C_ss-C_sp C_pp^-1 C_ps.
Then J_joint=J_p+X_s|p^T S^-1 X_s|p before common parameter/nuisance profiling. This is the actual PR255 same-law Schur mechanism. A block-diagonal covariance ablation changes the experiment; it is not deletion of independent evidence. After nuisance profiling, quantify whether STF innovation adds any W-vs-ell information or only sharpens nuisance. Preserve original and innovation null kernels. The effective-rank attribution must be computed, not assumed.

For a smooth scalar functional f(theta), gradient propagation is
    df=(grad_theta f)^T dtheta,
    Var_linear(f)=grad f^T Ctheta grad f
only for estimable tangent directions and the adopted local approximation. For vector/tensor phi use Dphi Ctheta Dphi^T and cross-target Dphi Ctheta Dpsi^T. This is standard delta-method propagation; set images are safer at singularities, zero norms or nonlinear extrema.

A depth derivative is an additional registered linear/physical functional, e.g. fixed finite-difference coefficients D_zY with covariance D_z C D_z^T, or an analytic derivative of the declared history map. It must not be inferred merely from the symbol G_F. A derivative of support F_sup(z,u) requires common target/frame/anchor and an actual differentiable path; active maximizers can switch, so even a smooth parameter path need not give a globally smooth support envelope. Physical proper-time derivatives require source-frame redshift/time conversion, not a change of label.

## 6. Concrete research delta beyond R58/R62/GLS

The new content can be an **actual source-constrained observer/history identifiability result**:

1. Take a physically derived finite compensated-dust history, including source and observer endpoint terms, and transport it through actual CF4 angular/window operator. This is different from R58's constant V and R62's unconstrained polynomial STF morphology.
2. Determine how much the source/history column survives after simultaneous observer boost, free calibration dipole and apparent STF profiling, with actual signed cross-window and polar/STF covariance. Give explicit measurable W/ell combinations and weak/null combinations in physical units.
3. Measure the added identifiable information from the real STF innovation on the same Gaussian law and how calibration choices alter it; this is directly relevant to the claim that tensor morphology helps separate local/global effects. If it adds no robust separation, the measured negative result is useful.
4. Push the resulting one region through x/Q/Pi/F/G_F with honest null support and label restricted-history quantities as conditional. Show, for example, that an apparent strong W estimate vanishes/weakens under a physically allowed observer/calibration fibre, or that a concrete bounded W contrast survives all seven nuisance prescriptions.

Neither an invertible variable change, generic GLS, generic Schur algebra nor the five-view names are mathematical novelty. The possible contribution is the explicit physical source law + actual estimator + null/weak-direction result and its measured consequences. A global tilt claim still requires interpreting the source class as spatially homogeneous and qualifying absolute observer/normal frame; this bounded CF4 calculation alone does not establish that interpretation. An independent owned aberration3D channel remains absent.

## Exact identities of newly read central sources

All paths relative to baseline checkout; SHA256 of observed files:
- htt/htt/htt/infer/r54_tensor_five_view.py: 47f9ab5fd40da9ffb8725ff9720a8d4cba7116c905a6a4c11e05b79f972e17a8
- htt/htt/htt/infer/r58_mixed_tensor_likelihood.py: f1c07d8ba7253f225af9354277a2973b5cab96c86febd08d4f8c5e1a11555bc0
- scripts/r58/build_r58_views.py: d84a05df99fb4393546222023cc37d8fe07d3bb3977c3520a60040e99445ab20
- htt/src/common/htt_five_variable_state.py: 278e3386f7f949afb8e2990abdc9726fc75f6fdb7adeb3223fdce41c67591939
- htt/src/common/typefree_functionals.py: 30f92aa9b892d449e1107a70c7ffd5f09ec178a94ac799e0294dee267f5fb2f9
- htt/src/common/depth_path.py: 7b3115ced6d68ec1ede814df6662127719bc2a12cb4cebe97098c50e6274432f
- htt/src/common/departure_contracts.py: 84682381cfb7b0356a69e74f3df1a6fbbc7be75ad84f937970485e7605d2f4d4
- P/OBSERVATIONAL_CONVERGENCE_R39_20261107/VECTOR_TENSOR_X_FRAMEWORK.md: a0f136cd79bc44d9b0af393091aa6fc6ce9e5ce0bfe2e2877e53ade1035f93ca
- P/METHOD_REBOOT_20261023/THEOREMS.md: a2c7611fccbec990d466be255dea2ac87d246a2c155cb508a89e8e244abcac0d

Read/hash inspection is complete; no numerical test or new scientific experiment was executed in this support task.
