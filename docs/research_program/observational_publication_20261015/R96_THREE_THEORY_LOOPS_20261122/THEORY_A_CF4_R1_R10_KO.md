# R96-A: SQ-CF4, theory R1–R10 (executed)

**Scope:** 35,970 actual CF4 groups, four H03 windows × nine coefficients, signature (-,+,+,+), c=299792.458 km/s. The mathematical and source-conditioned computation is executed; the upstream zero-point posterior is not available.

**R1 · Question.** Can R36 four-method covariance, R27 seven-channel calibration quotient, and R95 physical low-k PV be combined without double-counting? Identify which data can and cannot constrain a common nine-coefficient expansion tensor.

**R2 · Source.** R36 RESULT_MATRICES.npz, R27 FACTOR.npz, 35,970 group ID-locked H03 source, R95 G02. Original Tully et al. Cosmicflows-4 (2022): https://scispace.com/papers/cosmicflows-4-1420ai40 . Competitor Stiskalek–Desmond–Lavaux TF/SN anisotropy forward modeling (2025): https://scispace.com/papers/no-evidence-for-h-0-anisotropy-from-tully-fisher-or-khfanub008b9 . Different calibration/selection contracts.

**R3 · Definitions.** For fitted y in R^36, shared D=1_4 tensor I_9, beta in R^9, source-conditioned C_PV, H03 C_noise, J7 in R^(36x7), Jbulk in R^(36x3), distinguish R36 inherited covariance from newly modeled H03 covariance. No assumption that R27 support is upstream posterior covariance.

**R4 · Alternatives.** A: C_R36=C_PV+K4 Sigma4 K4^T+R_R36. B: C_R95=C_PV+C_H03noise+J7 Sigma7 J7^T, Sigma7=sigma_cal^2 I_7 as explicit sensitivity. C: source-qualified raw pre-intercalibration hierarchical calibration/selection with independent anchors; not available this cycle.

**R5 · Derivation.** For C=C0+UU^T, U=sigma_cal J7, Woodbury gives C^-1=C0^-1-C0^-1 U(I+U^T C0^-1 U)^-1 U^T C0^-1; beta_hat=(D^T C^-1 D)^-1 D^T C^-1 y; Cov(beta_hat)=(D^T C^-1 D)^-1. The identity mu_pub=mu_pre+M delta is unchanged by (mu_pre,delta)->(mu_pre-M eps,delta+eps). Post-corrected catalog alone therefore does not uniquely identify original upstream calibration, unless independent raw anchors or restrictions fix the gauge.

**R6 · Counterexample and physics check.** R36 residual C_R36-C_PV-K4 Sigma4 K4^T has positive minimum eigenvalue 1.01e-5. The difference C_R36-(C_PV+C_H03noise) has eigen range [-0.90324,+0.25713], hence is indefinite. It is *not* independent positive semidefinite noise; naively summing models would double count different conditionally defined terms.

**R7 · Actual computation.** New cf4_covariance_bridge.py recomputes all 4×9 H03 weighted fits over all 35,970 groups, actual 36×7 calibration and 36×3 bulk Jacobians, 3 radii (5,10,20) × five calibration SD (0,.02,.05,.10,.20) grid. Exact Cholesky–Woodbury parity <=1.3e-12 on tested coefficients; R36 y parity <=2.42e-13; R95 H0 grid parity <2e-7.

**R8 · Numeric conclusion.** Conditional H0 km/s/Mpc: R36 old 72.23818±0.38769; new R95 sigma_cal=0:72.92614±0.35919; sigma_cal=.05mag:72.00983±1.10601; sigma_cal=.20mag:68.40442±2.27697. These are four *working-model* conditional estimates, not independent physical measurements or anisotropy evidence.

**R9 · Mathematical/computational contract.** Declare source IDs, units, working noise, physical low-k power, selection, calibration covariance and heldout separately. Enforce PSD, window/source selection and overlapping methods; test rank deficiency and random working covariance; preserve alternative models rather than adding them.

**R10 · Bounded completion.** Actual artifacts: CF4_COVARIANCE_RECONCILIATION.json; scripts/r96/cf4_covariance_bridge.py; scoped tests. Next: connect truly independent pre-intercalibration method/posterior and missing-k/selection covariance. Physical original SQ-CF4 remains BLOCKED_INPUT; finite conditional sensitivity completed.
