# HTT Six Observational Papers Implementation Plan

> **For agentic workers:** Use the host's available task-by-task implementation workflow. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Six independently testable, source-qualified and referee-reviewable HTT observational manuscripts on statistics x/F/Pi/Q/G_F, low-ell anomalies, H(z,n), local/global tilt, Bianchi identification and beyond-FLRW kinematical measurements.

**Architecture:** An immutable-input publication overlay consumes older PR/legacy scientific assets through typed observation/physical transfer interfaces, one paper-specific result+claim gate at a time. The machine-readable 42-node source of truth is docs/research_program/observational_publication_20261015/PUBLICATION_DAG.json; this plan gives engineering entry points and first independently verifiable outputs.

**Tech Stack:** Python 3.12, NumPy/SciPy/HEALPix/Astropy, existing htt/obsstat and htt/htt/htt modules, actual released CF4/Planck sources, JSON/LaTeX/Markdown, pytest and Wolfram/xAct when relevant to derived physical response. No local Codex prerequisite.

## Global Constraints

- Keep original checkout /home/cosmosapjw/Dropbox/bianchi/htt_base @ 13d8d85f and 57 original dirty files unchanged; only use isolated branch/worktree or explicitly merged source-owned changes. GitHub 245-card canonical PR backlog remains untouched.
- No observational physical claim or journal submission merely from completed tests. Raw observations, selection, covariance, and source/observer congruence must be scientifically admissible. All six current papers NOT_READY_TO_SUBMIT.
- Preserve every negative/null and undefined-mass result, and keep 9 processed Planck source maps as ONE physical CMB sky, not nine independent skies. FFP10 fixed-weight bank is not an automatically exchangeable physical null.
- Preserve prior authentic legacy mathematical ideas and original definitions and provide a typed adapter rather than aliasing unrelated x, F4, F, Q, G_F, Pi or priors. Units c, frames, signature (-,+,+,+) must be explicit.
- Avoid redoing lengthy solver/history derivations while P1–P3 source-conditioned data tasks are executable. Where native global history/Bianchi atlas is genuinely missing, record the exact external response contract and keep independent tasks ready.

---

### Task 1: Shared source and selection contract, papers P1–P6

**Files:**
- Consume: docs/research_program/observational_publication_20261015/SOURCE_CROSSWALK_AT_DESIGN.json
- Create (proposed): docs/research_program/observational_publication_20261015/SOURCE_BINDINGS.json
- Create (proposed): docs/research_program/observational_publication_20261015/CLAIM_SELECTION_LEDGER.json
- Test (proposed): tests/obsstat/test_htt_publication_source_bindings.py

**Interfaces:** Source record has source_id, file/ref commit/bytes identity, units, signal/observer frame, selection window, overlap group, observation law, covariance owner, null-source authority, admissible claim tier; one source can appear in multiple paper modules with the SAME overlap group.

- [ ] **Step 1: Add failing test.** Make one Planck SMICA_HM/NILC shared-sky record and one overlapping CF4 method group; reject attempted independent likelihood multiplication without a declared cross-source covariance or conditionally independent latent-variable factorization.
- [ ] **Step 2: Verify red failure.** Run PYTHONPATH=htt/src:htt python3 -m pytest tests/obsstat/test_htt_publication_source_bindings.py -q; expected unknown source/overlap check before implementation.
- [ ] **Step 3: Implement source crosswalk.** Hash actual release/mask files when accessible, prove source cohort identities and distinguish local-only 2026-10-15 source artifacts from Git commit contents. Record historical P2 statistic search as retrospective and planned confirmatory statistic families as future registration.
- [ ] **Step 4: Run focused test.** Same command, expected zero failures for source/hash/overlap examples.
- [ ] **Step 5: Integrate check.** python3 scripts/htt_publication_dag.py --task X01 and --task X03; compare actual source bindings to both output artifacts and persist source identity receipt.
- [ ] **Step 6: Commit only source binding files.** No main merge or mutation of old canonical DAG.

### Task 2: P2 Planck T/E/B anomaly with matched source processing

**Files:** Proposed htt/obsstat/publication_lowell_response.py, scripts/run_htt_lowell_null_adequacy.py, tests/obsstat/test_publication_lowell_response.py; consume docs/research_program/htt_mes_eps_loop9_20261015/results_v2/result.json.

**Interfaces:** response(planck_release, common_mask, bandpass_beam, harmonic_lowell, higher_modes) returns source-matched estimator, noise/foreground tags, finite leakage operator; null_bank also returns independent latent CMB, noise and nuisance simulation IDs. No p-value until null_match_pass.

- [ ] **Step 1: Fail on unequal mask or reusing a noise ID in a purported independent calibration sample.**
- [ ] **Step 2: Run python3 -m pytest tests/obsstat/test_publication_lowell_response.py -q, expected failure before implementation.**
- [ ] **Step 3: Inject actual l2–8 harmonics into source masks and spin-2 E/B with corresponding treatment.** Tie observer dipole subtraction and beam transfer to the released-product metadata, not an assumed 5/10 arcmin Gaussian illustration.
- [ ] **Step 4: Repeat tests; require finite kinematic boost/noise/highmode positive controls and exact same-sky identities.**
- [ ] **Step 5: Use calibrated prospective trial family in L02–L05; report max-stat finite Monte Carlo null rank and selection history with competing Planck VII method.**
- [ ] **Step 6: Commit bounded source/null result; hold P2 claim without validated physical simulation exchangeability.**

### Task 3: P3 CF4 directional redshift-dependent Hubble factor

**Files:** Proposed htt/obsstat/htt_hubble_depth_window.py, scripts/run_htt_hubble_depth_tomography.py, tests/obsstat/test_htt_hubble_depth_window.py; consume docs/research_program/cf4_schur_loop8_20261015/results/result.json and immutable CF4 group sources.

**Interfaces:** window_H(redshift, sky_vector, modulus, group_id, method_id, covariance_owner, selection_id, window_spec) returns H_eff(z,n) monopole, dipole, STF2, observed window/cross-window covariance, null-model information; no automatic sigma_ab assignment.

- [ ] **Step 1: Add failing exact isotropic-mock and anisotropic-window dipole/monopole leakage tests; include repeated group IDs and overlapping bins.**
- [ ] **Step 2: Run python3 -m pytest tests/obsstat/test_htt_hubble_depth_window.py -q; expect missing implementation failure.**
- [ ] **Step 3: Implement explicit survey-angle and depth kernels, fixed observable units km/s/Mpc, true distance likelihood or source-qualified selection approximant, peculiar-velocity model.** Use stable linear-solver/Schur QR; do not allocate full 35,970² covariance.
- [ ] **Step 4: Pass exact injection tests and compare old 35,970 fixed-Gaussian STF coefficients under exactly matching simplified assumptions.**
- [ ] **Step 5: Perform H02–H05 method/sky holdout, mock-calibrated false anisotropy, overlapping-window covariance, and compare to Boubel 2024, Duangchan 2026 and Stiskalek negative null.**
- [ ] **Step 6: Commit H_W observable inference with source-law limits; physical H=Theta/3 requires an additional transport gate.**

### Task 4: P1 x,F,Pi,Q,G_F statistical inference on actual observations

**Files:** Proposed htt/obsstat/publication_functionals.py and tests/obsstat/test_publication_functionals.py; consume frozen htt/htt/htt/departure/posterior_pushforward.py, common/typefree_functionals.py and htt/mio/formalism/filling_fraction.py and isotropy_gap.py as **semantic references only**.

**Interfaces:** samplewise_functionals(joint_atoms, same_congruence_sector_budget, typed_positive_anchor, depth_bins, floor) returns signed x, sector F or undefined, Q or undefined, strict Pi outer interval [known>t,known>t+undefined], G_F or undefined, preserved joint IDs, original weights, provenance and cross-sky dependence.

- [ ] **Step 1: Add failing tests for negative x, zero denominator, exact threshold tie, frame mismatch, inverse-MIO firewall, and genuine missing-sector probability.**
- [ ] **Step 2: Run python3 -m pytest tests/obsstat/test_publication_functionals.py -q; expect missing module failure.**
- [ ] **Step 3: Adapt existing frozen PR066/PR521 finite joint image, not a new competing definition.** Explicitly split historical Q=x/U_sigma from any eventual physically certified total-defect occupancy; do not use F4 angular moment as F.
- [ ] **Step 4: Verify all tests, exact normalization, nonincreasing Pi on defined mass, unknown-mass coverage under different allowed completions.**
- [ ] **Step 5: Run actual-source paired conditional images; only promote observational partial-ID claim if a real likelihood or rigorously justified outer set has source support and selection controls.**
- [ ] **Step 6: Commit figure/results showing negative and undefined mass, not a synthetic-only cosmology posterior.**

### Task 5: P4 local boost versus homogeneous global tilt

**Files:** Proposed htt/obsstat/htt_local_global_frame_adapter.py, tests/obsstat/test_htt_local_global_frame_adapter.py; reuse previous processed_boost_theory_bridge.py and nulls/local_boost_depth_null.py as read-only scientific references.

**Interfaces:** typed beta_RO, beta_RM, beta_MO, rapidity rho, galaxy bulk B_W; physical history tensor adapter returns separate data-response columns under source/beam/covariance with condition-number and error budgets.

- [ ] **Step 1: Add failing Lorentz composition and false duplicate-history-column tests.**
- [ ] **Step 2: Run python3 -m pytest tests/obsstat/test_htt_local_global_frame_adapter.py -q; expect missing implementation.**
- [ ] **Step 3: Inject finite observer boosts into real Planck mask and source response; do not rebrand that as global tilt.**
- [ ] **Step 4: Test same-frame/rapidity exact invariance, multi-depth rank/singular-value vs error bound and nuisance quotient.**
- [ ] **Step 5: Acquire physically distinct Einstein-Boltzmann global tilt history and common source covariance for V03–V05; otherwise preserve a narrowly scoped identified-set physical limit.**
- [ ] **Step 6: Commit only validated local response; keep final P4 physical distinction blocked until V03–V05 evidence.**

### Task 6: P5 Bianchi family and mode identification

**Files:** Proposed docs/research_program/observational_publication_20261015/BIANCHI_ATLAS_INTAKE.json, tests/obsstat/test_htt_publication_bianchi_atlas.py, scripts/run_htt_bianchi_family_comparison.py.

**Interfaces:** accepted transfer record explicitly binds Bianchi type, branch/mode, metric and curvature signs, initial data, polarization conventions, recombination/Thomson physics, all-m T/E/B, lmax, interpolation error, native solver identity and actual Planck response.

- [ ] **Step 1: Add failing incomplete T/E/B coverage and invalid type/exceptional branch tests.**
- [ ] **Step 2: Run python3 -m pytest tests/obsstat/test_htt_publication_bianchi_atlas.py -q; expect missing atlas gate before implementation.**
- [ ] **Step 3: Discover and evaluate verified native external atlas per family, including 11 canonical and exceptional VI_-1/9; missing Bianchi types remain missing instead of substituted FLRW.**
- [ ] **Step 4: Verify physical constraints, numerical convergence, polarisation and sign parity; compare accepted family subsets with Saadeh et al (2016).**
- [ ] **Step 5: Run actual Planck matched model comparison, family-equivalence null rank and injection confusion only after qualified transfer and null.**
- [ ] **Step 6: Commit a subset paper response only when its physical likelihood passes; never claim untested all-type identification.**

### Task 7: P6 partial measurement of cosmological kinematics

**Files:** Proposed htt/obsstat/htt_kinematic_identifiability.py, tests/obsstat/test_htt_kinematic_identifiability.py, scripts/run_htt_kinematic_identified_sets.py.

**Interfaces:** one-congruence covariant tensor sigma_ab, omega_a, A_a, relative material/radiation tilt beta_a; observation operator contains CF4 radial plus explicitly independently sourced nonradial channels and covariance/selection/clock tags.

- [ ] **Step 1: Add failing antisymmetric n^i omega_ij n^j=0 test; fail on mistakenly interpreting CF4 apparent STF or angular dipole as geometry shear or four-acceleration.**
- [ ] **Step 2: Run python3 -m pytest tests/obsstat/test_htt_kinematic_identifiability.py -q; expect missing operator gate.**
- [ ] **Step 3: Implement source-qualified linearized radial response, nullspace and physically dimensioned tensor map with explicit rank and source frame.**
- [ ] **Step 4: Verify nullspace under rotations/parity and preserve unbounded/undefined sectors without positive-redefining signed x.**
- [ ] **Step 5: Add true optical/Jacobi, kSZ, polarization or proper-motion independent response when its physical source law is validated; compute actual identified subspace and uncertainty/upper limits.**
- [ ] **Step 6: Commit partial source-qualified measurement only if real-selection/noise transfer adequate; unresolved vorticity/acceleration/tilt cannot be called measured.**

### Task 8: Manuscript-level gates, one independent decision per paper

**Files:** PUBLICATION_DAG.json each paper's terminal S06/L06/H06/V06/B05/K06; respective manuscript+figures under a new paper-owned report path; tests/obsstat/test_htt_publication_dag.py.

**Interfaces:** decision(paper, source_manifest, estimand, null_calibration, results, comparator, reviewer) returns NOT_READY_TO_SUBMIT / READY_FOR_SCIENTIFIC_REVIEW / READY_TO_SUBMIT with exact missing list and evidence links. Neither decision mutates main nor submits a journal file.

- [ ] **Step 1: Add a failing decision test attempting to promote P2 on pre-existing FFP10 alone and P5 on an analytic Bianchi shape template alone.**
- [ ] **Step 2: Verify test fails under false-PASS behavior.**
- [ ] **Step 3: Assemble actual first-author result tables, negative/null findings, uncertainty budget and full reproducibility; compare each paper's own prior art, independent review no more than one fresh pass.**
- [ ] **Step 4: PASS only when actual scoped admission checks close; otherwise output typed missing physical or statistical inputs and continue independent READY lanes.**
- [ ] **Step 5: Re-run python3 scripts/htt_publication_dag.py --validate and publication DAG tests.**
- [ ] **Step 6: Save standalone paper artifacts in owner branch; merging main, journal submission and six separate PR creation require distinct user requests or separately justified published workflow.**

## Current validated initial state

As of 2026-10-15, 6 papers, 42 task nodes, 4 historical scoped evidence anchors, 38 new research tasks, 7 external-input-held nodes, 9 ready nodes and six separate submission gates. No six manuscripts are currently submitted or ready to submit. Source SHA identity is recorded for relevant older PR/results; reader should prefer exact published commit over uncommitted local-only copies.

Initial READY sequence recommendation: P2/L01 and P3/H01 first; P1/S01 third, with X01/X02/X03 shared literature/data selection work. P4/V01, P6/K01, P5/B01 can run independently without waiting for Bianchi solver. End after a substantive bounded research result and its targeted tests; do not build an endless plan-review loop.

## Unresolved decisions

1. **Paper venues and author list:** proposed to evaluate PRD/JCAP/MNRAS/A&A after first results; none is a submission instruction.
2. **Physical response provider:** for P4/P5/P6 native polarized Bianchi and source-frame history, decide from verified available code/PR; a planned external tool is not a verified physical solution.
3. **Additional selected raw survey products:** empirical CF4 subgroup selection and shared method covariances, Planck end-to-end null, and nonradial data may require separate source acquisition. Their absence blocks physical claim gates, not source-conditioned computations.
