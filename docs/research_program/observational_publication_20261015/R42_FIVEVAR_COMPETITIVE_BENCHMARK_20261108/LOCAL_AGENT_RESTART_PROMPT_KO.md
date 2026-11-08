# Local Agent Restart Prompt — HTT R42 (2026-11-08)

너는 `cosmosapjw-quantum/htt_base`에서 실제 물리·통계·코딩 작업을 수행하는 local coding/research agent다. 이 작업은 장기간 연구의 새 수렴 epoch이며, 단순 문서 포장이나 이전 보고서 재서술이 목표가 아니다. 목표는 **최신 HTT tensor 5변수 방법 ((x,Q,Pi,F,G_F))** 이 기존 경쟁 이론/관측·추론 방법보다 어디에서 어떤 이점을 갖는지, 또는 갖지 못하는지를 실제 관측 자료와 적대적 벤치마크로 판정하는 것이다.

## 0. 권위·작업 위치·절대 경계

Repository: `https://github.com/cosmosapjw-quantum/htt_base`  
R42 branch: `research/r42-fivevar-competitive-benchmark-20261108`  
R42 parent: `0439ae8e4870b23abfcdb9499c4c214daf12314b`  
R41 base branch: `research/r41-publication-gate-20261107`  
R41 PR: #565 (open/draft; R42 is stacked on R41)  
R42 package: `docs/research_program/observational_publication_20261015/R42_FIVEVAR_COMPETITIVE_BENCHMARK_20261108/`

먼저 `git fetch origin` 후 정확한 branch와 commit을 확인한다. R42 branch가 없으면 parent SHA에서 만든다. `main`은 현재 관측연구 head가 아니므로 기준으로 삼지 않는다. 직접 `main`에 push/merge하지 말고, R42 branch 또는 그 child feature branch 및 PR을 사용한다. Remote Desktop 또는 다른 host-control 수단을 사용하지 않는다. 단, 네가 실제로 작업하는 local checkout에서 파일·데이터·실험을 읽고 수정하는 것은 이 과업의 핵심이므로 허용된다.

변경 전 `git status`, branch, HEAD, worktree identity를 보존한다. dirty working tree를 덮어쓰지 않는다. R38/R39/R40/R41의 기존 문서·결과·로그를 삭제하거나 덮어쓰지 않는다. Raw catalogues, maps, chains, credentials를 Git에 commit하지 않는다. 다운로드는 공식 release만 사용하고, 로컬에서 실제 bytes의 SHA-256을 계산한다.

## 1. 연구 목표와 5변수 의미

혼동 금지:
- `theta_K`: 물리적 local kinematic state ((sigma_{ab}/H,omega_a/H,A_a/(cH),eta_{RM},eta_{MO})), 17차원 chart.
- `T=(x,Q,Pi,F,G_F)`: 이 common posterior/compatibility result에 적용되는 다섯 output/readout family.
- `T`의 다섯 항목은 독립 likelihood parameter나 독립 확률인자가 아니다. `p(x)p(Q)p(Pi)p(F)p(G_F)`를 곱해 likelihood를 만들지 말 것.

정의:
1. `x`: direct, normalized, mixed kinematic tensor functionals + predicted/observed carrier bundle. Each entry must declare tensor rank, O(3)/SO(3) representation, parity, units, basis/frame, redshift support, source/window/transfer, covariance and state identity.
2. `Q`: physical anchor/gauge/margin/availability bodies. Bounds must trace to a theorem, calibration, observed control or explicit prior. Unavailable is a valid status.
3. `Pi`: law-conditional exceedance surfaces for posterior push-forward, matched null and predictive laws. A pseudo-Gaussian is not an empirical null.
4. `F`: directional support and occupancy of a clearly defined image/credible set relative to a meaningful anchor. Use equal-area sphere quadrature and demonstrate convergence.
5. `G_F`: redshift/distance depth path with full cross-shell covariance and explicit transfer/transport. Posterior covariance and data covariance are different objects.

The research question is not “is tensor better than a scalar?” The main question is: “What does this latest tensor five-variable inference/readout architecture preserve, identify, calibrate or predict better than existing physical theories and methods, under which observable and data conditions?” Keep scalar (x_C) only as a secondary ablation.

## 2. Stage A: evidence/source-history audit before coding

Read and reconcile:
- `docs/research_program/observational_publication_20261015/R42_FIVEVAR_COMPETITIVE_BENCHMARK_20261108/PUBLICATION_REASSESSMENT_KO.md`
- `docs/research_program/observational_publication_20261015/R42_FIVEVAR_COMPETITIVE_BENCHMARK_20261108/FIVEVAR_COMPETITOR_BENCHMARK.yaml`
- `docs/research_program/observational_publication_20261015/R42_FIVEVAR_COMPETITIVE_BENCHMARK_20261108/RESEARCH_DAG.yaml`
- `docs/research_program/observational_publication_20261015/R42_FIVEVAR_COMPETITIVE_BENCHMARK_20261108/DATA_AND_RUNTIME_MANIFEST.yaml`
- `docs/research_program/observational_publication_20261015/R42_FIVEVAR_COMPETITIVE_BENCHMARK_20261108/HARNESS_REPAIR_AND_MUTATION_GATES.yaml`
- latest source files `htt/src/common/full_observable_x_bundle.py`, `htt/src/common/htt_five_variable_state.py`, `htt/src/common/kinematical_functionals.py`, `htt/src/common/kinematic_response.py`, `htt/src/common/relativistic_velocity_closure.py`, `htt/src/common/stf_metric_bridge.py`, `htt/htt/htt/infer/*`, `scripts/r41/*`.

Re-audit the PR history by:
1. Enumerate every PR record and classify title/state/head/base/changed files.
2. Identify every PR that changes theory, equations, observable mappings, data acquisition, covariance, likelihood, sampler, tensor functionals, five-variable semantics, harness gates or claims; read full diff/comments/reviews for those PRs.
3. For unrelated PRs record path-based reason for exclusion; do not falsely report every diff as fully reviewed.
4. Index all legacy research dossiers, generated reports, source receipts, theorem/experiment registries and handoff prompts relevant to these six research loops. Preserve superseded work as historical evidence; assign KEEP/REUSE/TRANSFORM/CONDITIONAL/QUARANTINE/RETIRED with exact path and commit.
5. Reconcile contradictions. An older execution report is not proof of present files or a valid current likelihood.

Output: `PR_LEGACY_COVERAGE.csv`, `LEGACY_DISPOSITION.yaml`, `CONTRADICTION_LEDGER.yaml`, `SOURCE_AUTHORITY_MAP.yaml`.

## 3. Stage B: inspect the actual five-variable implementation

Inspect and repair, with focused tests:

### x
Current source `full_observable_x_bundle.py` has hardcoded response values such as count factors 3.75/3.40, Gaia factors 0.92/0.18, fixed optical-depth/shear scales and zero B-mode prediction. Trace every constant to an equation, release-specific selection integration, measured calibration or code convention. Replace unexplained production constants with derived/source-specific operators. Keep observed data immutable and predictions separate. If an operator is not available, return typed UNAVAILABLE or EXTERNAL_TRANSFER_CONDITIONAL instead of a fabricated number.

### Q
Current five-variable constructor contains fixed anchor bounds/margins. Replace these only when a theorem, physical prior, calibration or external dataset supplies the bound. Record source and uncertainty. Do not convert the premise (A_a=0) into a measured anchor. Maintain explicit gauge quotient for Gaia B1 spin versus physical vorticity.

### Pi
Remove the arbitrary `RandomState(42)` Gaussian null with fixed (10^{-4}) scale from any empirical significance/FPR use. Retain it only in a named fixture test. Generate matched nulls from the correct source-specific simulations and selection pipeline: Planck end-to-end/FFP, catalogue randoms and source resampling, Gaia scan-law/systematic nulls, SN residual/covariance mocks. Record Monte Carlo uncertainty in FPR/power/quantiles.

### F
Replace non-uniform paired `linspace(theta,phi)` directions with equal-area Fibonacci/HEALPix or a validated spherical quadrature. Test rotation equivariance, parity, resolution convergence, support-set construction, (h_A(u)=0) behavior and finite-sample uncertainty. Be explicit whether support is of posterior samples, a credible region, an identified image or its convex hull.

### G_F
Do not assume (sigma(z)=sigma_0/(1+z)) unless it follows from the selected physical dynamics and stated regime. Do not use identity transport kernels merely to fill matrix shapes. Build shell-specific observational data vectors and selection functions. Derive transfer from the selected Bianchi/tilted model or explicitly call it a phenomenological diagnostic. Preserve full cross-shell covariance and distinguish:
- covariance across observed shell estimators,
- posterior covariance of latent functionals,
- covariance induced by common parameters,
- transport/model uncertainty.

Tests must falsify incorrect behavior. Add randomized rotation/boost tests, frame and units tests, limiting cases, nullspace/gauge tests, support convergence, covariance and transport checks.

## 4. Stage C: two-layer competitor benchmarking (primary task)

Do not use the scalar five-variable variant as the main competitor. Use the supplied `FIVEVAR_COMPETITOR_BENCHMARK.yaml`.

### Generative theory competitors
At minimum adjudicate:
- FLRW/LambdaCDM + local LSS/linear peculiar-velocity reconstruction;
- exact local observer Lorentz boost;
- Bianchi I and relevant Bianchi V/VIIh, LRS/Class A/B alternatives with physical CMB transfer;
- tilted multi-fluid / dipole cosmology;
- general covariant Kristian-Sachs/Heinesen Hubble/distance multipole cosmography;
- local inhomogeneity/bulk-flow/LTB-like model;
- phenomenological dipole/quadrupole plus survey-systematics model;
- HTT physical local kinematic state only where a justified dynamical/observation map exists.

### Inference/readout competitors
Compare latest ((x,Q,Pi,F,G_F)) against:
- conventional posterior mean/covariance/credible sets;
- full harmonic (a_{ell m})/BipoSH likelihood;
- multipole vectors / power and alignment tensors;
- multi-tracer number-count dipole with redshift, flux and angular-size responses;
- Gaia source-level VSH likelihood;
- hierarchical peculiar-velocity / GP or field-level reconstruction;
- score compression/nuisance-hardened compression;
- established convex support/depth/functional summaries.

A model-specific method may use fewer or different observables; declare the common data subset. Do not force false parameter equivalence. Compare physical target functionals at the source-observable level.

### Adversarial benchmark campaign
Generate matched injections:
- isotropic FLRW + realistic LSS/cosmic variance;
- pure local boost with Doppler, aberration, flux, observed-redshift and angular-size transforms;
- physical global tilt from dynamical evolution;
- Bianchi I and Bianchi V/VIIh with declared transfer;
- local flow/void without global anisotropy;
- survey/foreground/calibration/selection/scan-law artefacts;
- misaligned mixtures of boost + tilt + shear + systematics.

Evaluate:
1. identifiability of target functionals after nuisance projection and source windows;
2. SBC rank uniformity, 90/95% coverage, false-positive rate and power with Monte Carlo uncertainty;
3. held-out ELPD/appropriate multivariate scoring with actual refitting of every fold;
4. mask, split, prior, covariance and selection robustness;
5. parameterization/rotation/parity invariance;
6. runtime and ESS only at matched accuracy.

Report where HTT wins, ties and loses. Never design the benchmark to guarantee a win.

## 5. Stage D: six independent theory loops

Run the six loops separately, retaining separate claim/evidence records:
- L1 low-ell morphology -> (a_{ell m}^{T,E,B}), STF multipoles, multipole vectors, power tensors, BipoSH, mask/beam/foreground likelihood. Separate deterministic template from stochastic anisotropic covariance.
- L2 dipole anomaly -> thermodynamic CMB dipole, Doppler modulation/aberration, intrinsic radiation dipole, matter-count dipoles, Gaia glide, spectral/flux/redshift/size selection.
- L3 kinematics -> (sigma_{ab}, omega_a, A_a, eta_{RM}, eta_{MO}), exact boosts/Wigner rotations, source-level observational Jacobian, nuisance quotient.
- L4 Bianchi classification -> structure constants, Jacobi constraints, Class A/B, tilted dynamics, Bianchi I/V/VIIh; distinguish algebraic compatibility, dynamical solution, transfer and family identification.
- L5 (H(z,hat n)) -> general covariant multipoles, exact distances/low-z expansion domains, observer-vs-matter frame, local-flow and footprint controls.
- L6 local boost vs global tilt -> redshift tomography, flux/size response, local structure, source evolution and physical tilt dynamics.

For each loop output definitions, assumptions, derived mapping, approximation domain, competing models, source IDs, identifiability and a conclusion that may be negative or unresolved.

Important caveat: (n^a n^bomega_{ab}=0) only removes the direct antisymmetric contraction at that stated order; it is not a proof that vorticity is absent from every higher-order distance coefficient.

## 6. Stage E: real data and Cobaya

Use official data sources in `docs/research_program/observational_publication_20261015/R42_FIVEVAR_COMPETITIVE_BENCHMARK_20261108/DATA_AND_RUNTIME_MANIFEST.yaml`. Before downloading, inspect existing candidate files locally, then compute actual SHA-256. Keep source row IDs/order, masks, selections, windows, beam/transfer, covariance, units/frames and licence in manifests. Never commit raw data.

Minimum sequence:
1. Planck PR4/NPIPE observed frequency maps/splits/masks/beams/FFP; use observed sky as data and MC only for response/null calibration. Do not treat Commander/SMICA/PR3/PR4 maps as independent skies.
2. Quaia DR1 full catalogue + random/completeness; reconstruct magnitude/redshift subsets.
3. NVSS + RACS-low catalogues with exact declination/flux/spectral selection.
4. Gaia DR3/CRF3 source-level astrometry with full covariance, scan law, frame rotation and external tie controls.
5. Pantheon+ full table and matching covariance; then independent DES-SN5YR replication.
6. Cosmicflows-4 individual/groups and calibrator/method/covariance records; include local flow/density reconstruction.
7. SDSS redshift dipole and DESI DR2 background/anisotropic data only where their actual release products support the claimed observable.

Create a genuine Cobaya external likelihood from the validated observation operators. The old direct random-walk MH script may remain a test/reference, not production. Make every sampled background, calibration, selection, redshift-evolution and physical parameter explicit. No hidden fiducial constants. Run one-probe smoke/pilot, then joint pilot, then production chains. Save Cobaya YAML, code SHA, source manifest, environment, command, stdout/stderr, chains, checkpoints, rank-normalized split-Rhat, bulk/tail ESS, traces, autocorrelation and posterior predictive artifacts. Use a supported nested sampler with proper normalized priors for evidence; do not infer Bayes factors from MCMC alone.

## 7. Stage F: harness self-audit and repair

When a gate blocks an apparently valid claim:
1. reproduce the exact block;
2. independently evaluate the science, data, assumptions and provenance;
3. classify as SCIENTIFICALLY_JUSTIFIED_BLOCK, HARNESS_LOGIC_DEFECT, IMPLEMENTATION_DEFECT, INPUT_OR_PROVENANCE_INCOMPLETE, RUNTIME_OR_ENVIRONMENT_BLOCK, AUTHORIZATION_BLOCK or REPRESENTATION_OR_WORDING_FALSE_POSITIVE;
4. if the science is supported and the gate is defective, make the minimum harness/policy change and positive/negative regression tests;
5. if the science fails, correct/downgrade the claim instead;
6. record before/after rules and exact evidence.

Known issue: `FamilyIdentificationGate.audit_claim_text` is a substring scan. It can reject explicit negation, citations, quoted prior art or audit warnings. Replace it with structured claim metadata or a conservative assertion-context lint. Preserve rejection of an actual unsupported assertive claim.

Known potential overrestriction: absent native BASS atlas should not automatically forbid every family-specific claim if an authentic external solver or analytic transfer is physically validated. Keep provenance label EXTERNAL_TRANSFER_CONDITIONAL; never label external as native. Native solver is mandatory for a claim specifically about native BASS output, not as an automatic universal condition of scientific inference. Family identification still requires source-bound likelihood, proper model alternatives, predictive distinction, transfer validation and nuisance robustness.

## 8. Stop/continue rules

- If a dataset is missing, block only that channel and continue independent loops.
- If a physical functional lies in a non-identifiable fibre, report the identifiable quotient/bound, do not force a point estimate.
- If HTT loses to a competitor, preserve the negative result and narrow the novelty claim.
- If the latest five-variable semantics are mathematically sound but code paths are stubs/hardcoded, repair those paths rather than discarding the framework.
- If a claim is right but a harness rule is wrong, fix the harness with a minimal tested patch.
- If a claim is wrong, update the claim ledger/report/DAG; do not relax the scientific gate.

## 9. Required return package

Commit on R42 or a child feature branch and return:
- `PR_LEGACY_COVERAGE.csv`
- `LEGACY_DISPOSITION.yaml`
- `CONTRADICTION_LEDGER.yaml`
- `SOURCE_AUTHORITY_MAP.yaml`
- `FIVEVAR_IMPLEMENTATION_AUDIT.md`
- `HARNESS_GATE_ADJUDICATION.yaml`
- `COMPETITOR_REGISTRY.yaml`
- `COMPETITOR_LIKELIHOOD_MATRIX.csv`
- `SOURCE_LOCK_MANIFEST.json`
- `COBAYA_CONFIGS/` and pilot/production receipts
- `L1...L6` independent loop results
- `FIVE_VARIABLE_BENCHMARK_RESULTS.json`
- `PUBLICATION_DECISION.md`

Every execution receipt must bind branch/commit, input hashes computed from bytes, software versions, exact command, exit code and output identities. State clearly what was NOT_RUN.

## 10. Agent final response format

Return:
1. branch/commit/PR;
2. work performed and exact source revisions;
3. theory results and evidence state;
4. data actually downloaded and hashes;
5. Cobaya runs and diagnostics;
6. benchmark matrix showing where HTT wins/ties/loses;
7. harness rules changed and regression results;
8. remaining scientific and runtime blockers;
9. exact manuscript claim that the evidence supports;
10. resume point and next minimal action.

Do not say “complete”, “verified”, “converged”, “detected” or “published” without a corresponding artifact and executed evidence.
