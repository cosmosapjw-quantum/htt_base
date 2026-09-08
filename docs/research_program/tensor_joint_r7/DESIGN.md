# R7 project design

**Selected architecture:** existing measurement/physics modules feed one typed joint experiment. HTT performs inference; MIO projects diagnostics from the same state/region; no posterior/certificate scores are multiplied together. Every branch emits a terminal result record, including meaningful negative results. The DAG governs dependencies between capabilities, not belief in one preferred hypothesis.

## 1. Data contracts

These are new proposed interfaces. The implementation plan names their files; the existing functions in REUSE_MAP retain their current signatures.

| Interface | Mandatory payload and semantics |
|---|---|
| `TensorRecord` | `sample_id`, `source_realization_id`, `noise_realization_id`, retained real-harmonic vector `(32,)`, Q `(3,3)`, O `(3,3,3)`, units, frame, harmonic layout/metric, mask, product/release/processing identities, `chart_status`. Measurement covariance `(12,12)` or its ordered provider is distinct from null ensemble scatter. |
| `JointObservationLaw` | Ordered raw/derived measurement IDs; physical/nuisance parameter names and units; `mean(theta,eta)`; full covariance/support or normalized `loglik(theta,eta)`; source/selection law; shared latent IDs; admissible domain; `jacobian_theta` and `jacobian_eta`; approximation and transfer identity. Callable implementations reside in HTT; the common schema carries serializable identities/shapes. |
| `RadiationJet` | Propagation-direction moments 1/2/3, rate derivatives needed by T3, congruence/tetrad, Theta/rho, approximation order, remainder and derivative domain. Missing jet entries have explicit missing status. |
| `PhysicalState` | Rate-normalized shear STF2, antisymmetric vorticity, acceleration, species tilts/densities, signed curvature comparator and radiation jet. Keep all components until projection. |
| `HighSourcePolicy` | `UNRESTRICTED`, `ELLIPSOID`, `GAUSSIAN`, `JOINT_MEASURED`; K/S/radius or law/extra measurements; conditional or population coverage target; exact range/positivity constraints. |
| `PhysicalRegion` | Maintained domain, acceptance rule, total coverage budget, response/jet constraints, accepted model IDs, optimizer outer-error bounds. No posterior sample cloud is labeled an outer confidence enclosure. |
| `BranchResult` | node ID, process status, scientific outcome, capabilities, input/result identities, assumptions, failed tests or absent inputs, valid estimands, uncertainty type, next discriminator. An empty set differs from a missing set. |

`Q`, `O`, frame and covariance are the reusable measurements. Krylov packet, orbit distance, power, f_B, MES normalization, F and G are consumers. A chart decoder is never a requirement for retaining a valid tensor row. `DONOR_TENSOR` certifies carrier conversion; optional `DONOR_KRYLOV` certifies the inverse chart. Withholding the latter leaves the tensor and full-orbit routes available.

## 2. Runtime versus science

`process_status ∈ {PENDING,RUNNING,COMPLETED_SUCCESS,COMPLETED_FAILED_WITH_RECEIPT,BLOCKED_WITH_RECEIPT,ABANDONED_WITH_RECEIPT}`. The final four are terminal. `scientific_outcome ∈ {NOT_EVALUATED,COMPATIBLE,REJECTED_CONJUNCTION,PARTIALLY_IDENTIFIED,NONIDENTIFIED,CONDITIONAL_BOUND,SCENARIO_ONLY,NUMERICALLY_UNRESOLVED,INPUT_UNAVAILABLE,VALIDATION_FAILED}`.

A correctly calibrated rejection is a successful process. A failed integration or a missing dataset is not a rejected cosmology. A rank-deficient physical response may still be a successfully validated NONIDENTIFIED result. It retains the kernel or overlap witness and the response that would break it.

The DAG JSON uses **settle dependencies**: wait for all listed predecessor result records to become terminal; then run if any declared capability route is satisfied. If no route is satisfied, emit a blocked record naming the missing capability and its failed producer. Do not leave a descendant waiting forever. `always_run` reducers consume the records even when all upstream branches failed. This matches the purpose of the existing `requires_terminal_receipt` edge mode; the new campaign schema is not passed off as the old PR-card schema.

The executor catches an unexpected node exception, records it as `COMPLETED_FAILED_WITH_RECEIPT/VALIDATION_FAILED`, and continues independent ready nodes. Resume uses a bounded queue: one targeted repair attempt for a reproducible numerical/software defect, then terminal unresolved status with the failed evidence. Reruns create a new attempt in the same node; outcomes are not overwritten as if the first run succeeded. External absence closes as BLOCKED_WITH_RECEIPT; arrival of the specified input reopens only affected descendants.

### Binding order and exact scope

Catalogue adapters may return `ObservationLawFactory` when measurement/selection/calibration factors are fixed but predictions await a physical provider. Its identity and unfilled response slots are distinct from `JointObservationLaw`. R7-10 composes these factories and shared measurements as `EXPERIMENT_FACTORIES`, without granting empirical eligibility. It can separately emit `ADMITTED_EXPERIMENTS` for already bound direct or conditional laws. R7-17 binds supported providers to factories, checks normalization/domain/units and emits `MODEL_BOUND_EXPERIMENTS`; these reach R7-18/19 without feeding back to R7-10. An unsupported provider returns an unavailable scope. A direct conditional CF4 Gaussian velocity-space experiment emits `CF4_CONDITIONAL_LAW`, while an unqualified sensitivity remains `CF4_SCENARIO`.

Validation and observed inference match `(experiment_id, law_id, model_id, dataset_ids, conventions, version, method_id, method_config_id)`. The method configuration includes statistic/feature selection, scales, k, acceptance level, nuisance policy, fitting and selection procedure. Conditioning target and supported parameter domain must also contain the requested scope. A copied identifier is not evidence: the consumer checks its immutable specification/result binding. `CALIBRATED_METHODS` accepts either a domain-valid `EXACT_ACCEPTANCE_PROOF` record with its numerical obligations, or a calibrated simulator record with declared accuracy. A proof for one method cannot qualify a changed statistic.

Product-keyed subrecords follow [OWNED_ASSETS.md](OWNED_ASSETS.md). Optional CMB, flow, background, distance and projected controls use existing nodes06–10/21; each has its own typed output and law eligibility. Loss of PR3 does not prevent an owned WMAP control, and loss of a raw catalogue does not remove its independently usable compressed/control product. The configured primary experiment is not silently switched.

## 3. Physical and observational providers

### CMB

For frequency channel nu, define its response to a positive full source sky through Lorentz transformation, spectral conversion, beam/pixel transfer and frozen product processing. Fixed product weights and re-estimated component-separation weights are different experiments. The default primary comparison freezes released processing and reports response uncertainty. Re-estimation is a sensitivity branch only if its algorithm is available.

The low-mode baseline fits ell=0..5 simultaneously at NSIDE64 pixel centers and retains ell=2..5 after the declared commonization. It reuses the former M1 convention. Higher-source H3 adds measured modes through their joint covariance, not as independent external priors. Low/high cross-covariance includes noise, mask and shared stochastic sky. A nuisance law can be known Gaussian only within its declared model; actual product validation is separate.

`O(beta² T0)` must be retained or bounded alongside `O(beta DeltaT)`. The source intensity Doppler weight and channel temperature linearization are explicit. Finite thermal pullback supplies the benchmark; a finished component-separated map alone does not reconstruct every removed-source response. A missing correction history permits released-map morphology but blocks the unqualified physical boost lane.

### CF4 distance and velocity

Raw distance modulus likelihood is preferred over a Gaussian velocity approximation when raw/grouped errors and calibration are available. A declared light-cone model predicts `mu_i=5log10(D_L/Mpc)+25+Z_ij eta_j`. Redshift and distance measurement errors enter their joint law; the emitter and observer four-velocities must be those of the same model. At fixed latent distance/field and shared calibration, conditional measurement factors may be Gaussian with the supplied covariance. The latent field connects density/velocity across overlapping surveys.

For selection S and latent source intensity lambda, use the normalized selected law, not a weight-only fit:
\[
\lambda_{\rm obs}(y\mid\theta,\eta,Z)=S(y)\int
\lambda(\xi\mid\theta,Z)\,p(y\mid\xi,\theta,\eta,Z)\,d\xi,
\quad \Lambda=\int\lambda_{\rm obs}(y)dy.
\]
Conditional on source count n, use `prod_i lambda_obs(y_i)/Lambda^n`; with modeled counts use `exp(-Lambda) prod_i lambda_obs(y_i)`. This Poisson statement is conditional on the declared latent field; correlated fields are integrated once, not regenerated per galaxy. For correlated measurement blocks, replace the product by the corresponding normalized joint block likelihood and its joint selection probability. Shared zero-points are integrated once outside that joint product. The selection integral and its parameter derivative are part of every fit.

If the supplied CF4 product cannot determine this raw law, execute the P affine GLS on its actual full covariance as an explicitly **conditional velocity-space experiment**. Use 9 parameters in the exact existing column order; do not infer arbitrary vorticity from radial velocities. Selection and calibration sensitivities without a validated sampling law yield SCENARIO_ONLY. Neither fallback requires Local Codex to invent an astrophysical selection function.

### DESI

Reuse the P successor's exact selected sample, 18-vector ordering, random-window handling and per-realization nuisance refit. The sample is not interchangeable with the older BGS_ANY experiment. A weighted count statistic uses a compound/weighted sampling law or the matched catalogue mocks, not a Poisson draw on weighted totals. The window response and coordinate transforms must be verified before amplitude interpretation.

Covariance mocks and held-out model stress tests are separate roles. The actual input count and realization independence are read from local products; the source's intended EZmock/Abacus counts are not an availability assertion. None of the invalidated PR-151 numerical results is an input to the successor scientific likelihood.

### JWST and cross-survey calibration

Use the existing Gaussian host population and Gaussian/Student-t measurement residual alternatives; Student-t measurement errors do not silently change the host population. Same-host method contrasts measure calibration; retain absolute distance/redshift rows when they carry geometry. Use `C11+C22-C12-C21` for a contrast. A singular covariance requires support constraints; adding arbitrary jitter is not a physical uncertainty model.

The cross-data adapter creates an object/group matching table and a measurement linear map. Consuming both source measurements and their contrasts requires the resulting singular joint measure or an equivalent nonredundant basis. Geographic proximity alone does not certify a shared object. Common calibration factors appear once in the latent eta. If the shared-error law is unknown, publish separate valid subset results and a parameterized covariance sensitivity; do not multiply them into one precise posterior.

### Baseline and observational alternative models

R7-17 also compares P0/P1 using the already bound law: P0 is its declared baseline mean/stochastic law; P1 adds only its fixed linear design columns. For a retained Q/O experiment these may be the 12 orthonormal STF mean coordinates; for CF4 use the exact 9-column affine design; for DESI use the declared cap/depth response columns. These observational additions are not physical Bianchi identifications. The bound law fixes priors or confidence domain, covariance and selection. No template direction, cutoff or background is selected to improve the observed fit without the full selection correction. A physical beta interpretation still requires its product response; baseline comparison itself does not depend on a successful native or external provider.

### BASS and external transfer

Use existing matter projection, correct `bi_continuation` dust evolution and photon transport as donors for the R3 oracle. Add the collisionless photon stress and Jacobi/provider interfaces only in Local Codex, with the selected restricted model label. Preserve the native delivery stub. An external AniLoS/AniCLASS provider advertises only implemented modes/initial conditions/channels, with physical shear-rate conversion. General scalar/native/polarized responses remain unsupported when absent. A supported CMB-only transfer can give a CMB-only physical constraint even if its distance provider is unavailable.

## 4. Confidence and optimization defaults

For a known covariance Gaussian law, invert the full n-dimensional residual test `r^T Sigma^-1 r <= chi2(n,1-alpha)`, or rank(Sigma) plus exact support for singular laws. This is conservative but needs no unproved Wilks approximation. Physical nuisance/domain constraints are optimized jointly. Linear Gaussian unrestricted and bounded high-source branches use T4's exact profile/cost formulas; ratio-box subproblems use the existing GF solver.

For nonlinear/selection laws, the default is a simulator-based Neyman acceptance procedure under each fully specified parameter point, with nuisance uncertainty handled by a certified supremum or union confidence construction. Parameter grids without outer interpolation/error control are labeled pointwise scans. Local posterior MCMC may be added as a separately labeled Bayesian summary with explicit proper priors; it never replaces the confidence enclosure or creates empirical evidence via an improper prior.

Acceptance failures in one model produce REJECTED_CONJUNCTION. If several maintained models survive, report the union of their comparable physical regions plus model-specific assumptions. The final scalar intervals do not erase the multidimensional region or its disconnected pieces. Distinct likelihood experiments are not combined by taking their most favorable tail probability.

## 5. Numerical policy and plot-driven loop

Analytic identities first use exact rationals where available. Float64 algebraic residuals use dimensionless scaled tolerance `1e-10` for well-conditioned normalized fixtures; unit changes must not change the decision. Ill-conditioned cases return their error/condition diagnosis. This is an implementation gate, not a universal physical accuracy claim.

For response/trajectory/likelihood approximations, refine independent quadrature, cutoff, timestep or grid until the resulting observable/region-bound change is below **0.1 of its declared measurement standard uncertainty** and below **0.1 of its claimed rejection/coverage margin** where that margin is nonzero. Certification needs a bound, not only successive-run agreement. If either target is absent, report numerical error explicitly and withhold that interpretation. No simulation/FPR test is a proof of continuum containment.

Required figures: full-tensor/packet/scalar recovery and chart conditioning; mask fraction versus singular values and cancellation cost; H0–H3 confidence sets; empirical coverage/FPR/power with binomial intervals and refusal rate; depth kernel singular spectrum before/after nuisance projection; shared-calibration information gain; conditional MES envelope surfaces and same-state GF ranges. Plotting must use existing results, units, uncertainty types and failed states. Residual-error pass checks scale, tails, optimization and approximation error; hostile audit tries changed support, duplicated rows, omitted cross-covariance, degeneracy and wrong frame. Fix a concrete failure and repeat its relevant plot; do not increase test volume after the decisive error is resolved.

## 6. Result synthesis

The final report has one row per physical model × nuisance experiment × admitted dataset subset. It records the actual estimand, compatibility/rejection, identified combinations, unresolved directions, uncertainty and assumption sensitivity. A full-data likelihood result is claimed only when all intended measurements entered one valid joint law. An alternative dependence-robust joint confidence result may intersect valid marginal regions under the fixed union-bound allocation in OWNED_ASSETS; it is explicitly identified as a marginal-coverage construction and is not a likelihood or posterior. Otherwise the report states the exact partitions and which shared law is missing. This is the integrated analysis accounting, not a fictitious fully joint likelihood.

The final interpretation is ordered: stable observed tensor information → justified nuisance sensitivity → conditional physical invariants → supported model constraints → additional discriminating observations. Old findings become regression witnesses and comparison models, while correct old implementations become current producers. Completion is measured by these scientific products, not by number of gates, documents or PRs.
