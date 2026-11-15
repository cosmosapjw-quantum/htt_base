# LOCAL CODING AGENT RESTART PROMPT — HTT R49 GENERAL TILTED BIANCHI

You are the local coding agent for repository cosmosapjw-quantum/htt_base. Execute the R49 plan in the checked-out local repository. Read this prompt in full before changing files.

## Mission

Continue the HTT observational programme beyond Bianchi I. Build a physically correct general tilted-Bianchi pipeline covering Class A and Class B families, then connect the resulting physical state to CMB low-ell morphology/covariance, source-count dipoles, Gaia astrometry, directional distances and the HTT five-view tensor posterior. Use only data already present in the local data catalogue. Do not download new data. NPIPE PR4 must not block the project: use the PR3+FFP10 calibrated primary lane and treat NPIPE as a separate robustness/noise lane.

The goal is a genuinely publishable, evidence-backed result, not a larger collection of design documents. Keep the claim ceiling at C0 until actual source-bound likelihoods, calibrated inference, adversarial benchmarks and independent validation are complete.

## Authority and immutable source pointers

Repository: cosmosapjw-quantum/htt_base

R49 branch:
research/r49-general-tilted-bianchi-20261112

R49 parent package:
research/htt-six-loop-core00-20261109
parent head: 1b8abb1399f9f80b8e69bd57c2cc1592e2d1bcd4
parent PR: #573

Companion code repair:
research/htt-six-loop-core03-repair-20261109
head: 8a6ae269751a8a6878eaf9e1192c28fe1c067523
PR: #574
This repair PR is a separate open draft. Review and integrate it in a dedicated worktree before editing its consumers. Do not assume it is merged. Do not cherry-pick blindly. Prefer a normal merge after checking base identity, tree overlap and conflict scope. If a conflict affects science semantics, stop that subtask and preserve both variants for adjudication.

R49 documents:
docs/research_program/observational_publication_20261015/R49_GENERAL_TILTED_BIANCHI_20261112/

Read in order:
1. README.md
2. R49_DAG.json
3. R49_OBSERVATION_CONTRACT.json
4. R49_CLAIM_LEDGER.json
5. R49_GENERAL_TILTED_BIANCHI_KO.md
6. this prompt

## Hard scientific invariants

1. Signature (-,+,+,+). Keep c explicit. Declare the time coordinate and normalization of the normal N^a.
2. Distinguish the homogeneous-slice normal N, every fluid congruence u_s, radiation frame, local observer frame and catalogue reference frame.
3. The tilt is a three-vector V_s^alpha for each physical species:
   u_s^a = Gamma_s (N^a + c V_s^alpha e_alpha^a),
   Gamma_s = (1 - V_s^2)^(-1/2), V_s^2 < 1.
   Scalar beta and vhat are derived coordinates only. At V=0, its direction is undefined.
4. Preserve both geometry and matter congruence kinematics:
   theta_s, shear sigma_s, vorticity omega_s and acceleration A_s are calculated from nabla_a u_s,b. They are not silently replaced by normal-frame variables.
5. Each species contributes its exact normal-frame stress:
   epsilon_N = (epsilon+p) Gamma^2 - p
   J_a = c (epsilon+p) Gamma^2 V_a
   S_ab = p h_ab + (epsilon+p) Gamma^2 V_a V_b
   pi_ab = (epsilon+p) Gamma^2 V_<a V_b>
   Verify these against the chosen T_ab and tetrad convention using a symbolic/algebraic oracle.
6. Enforce Jacobi, Hamiltonian, momentum and Codazzi constraints at initial conditions and every accepted integration step. Derive momentum-constraint signs/c factors from the repository's extrinsic-curvature definition; do not fit a mock sign.
7. Single perfect-fluid Bianchi I with positive enthalpy has no genuine tilt under the standard homogeneous momentum constraint. Write a negative test. If a Bianchi-I beta remains, declare whether it is multi-fluid counter-streaming, radiation-to-matter relative tilt or local observer boost. Never describe all of these as global single-fluid tilt.
8. Class A and Class B are distinct constraint families. Preserve every type: I, II, III, IV, V, VI_0, VI_h, VII_0, VII_h, VIII, IX. Keep h continuous where defined; preserve h=-1 and h=-1/9 boundaries.
9. Do not infer that an entire family has no solution from a self-similar or equilibrium-point no-go. It is a no-go only for its declared equation of state, symmetry and asymptotic assumptions.
10. Compose relative velocities in exact order. Propagate Wigner rotations to every spatial tensor, polarization basis, covariance and source operator.
11. The CMB deterministic Bianchi template mean and stochastic harmonic covariance are terms of one data law. Do not multiply them as independent likelihood factors for the same a_lm.
12. HTT x,Q,Pi,F,G_F are derived from one common posterior/compatibility law. Never fit each view independently.
13. Missing source, selection, covariance, transfer, frame anchor or calibration is UNAVAILABLE/BLOCKED. Never replace it with a zero vector, random direction, identity/diagonal covariance, hard-coded dipole or default physical constant.
14. No result is a Bianchi family detection unless the family-specific transfer, calibrated data likelihood and competing model benchmark pass.

## Work plan: execute in order, stop only on a real blocker

### Task 0 — safe checkout and current-state pinning
- Read AGENTS.md, repo policy and actual branch/HEAD/tree.
- Confirm local worktree status, dirty files and untracked files. Do not reset, clean, stash or overwrite user files.
- Create a dedicated worktree from R49 branch. If it already exists, inspect it; do not destroy it.
- Fetch #573 and #574. Verify exact base/head relationships.
- Integrate #574 repairs into the dedicated R49 worktree only after checking conflicts. Record merge commit, tree SHA and changed files.
- Record the exact R49 base and code-repair identities in a local receipt.
Acceptance: worktree safe, ancestry and file identity recorded. If dirty files risk overwrite, stop writes and report.

### Task 1 — source/code/data audit
- Trace the canonical algebra representation (a,n,C) through every general Bianchi type factory.
- Compare BianchiAlgebra with legacy StructureConstants. Produce an explicit axis permutation, orientation, epsilon and sign conversion. Add round-trip tests. Never guess the map.
- Trace all beta and tilt call sites. Classify each as global normal-to-fluid tilt, species-relative velocity, radiation-to-matter boost, local observer boost, or first-order approximation.
- Trace every physical coefficient in the model to a derivation, calibration file or declared nuisance. Mark unsupported constants UNAVAILABLE.
- Resolve the actual local raw-data root from repository instructions and inventory. Rehash only the required files; do not download anything.
Outputs: CURRENT_AUTHORITY.json, BIANCHI_CONVENTION_BRIDGE.json, TILT_CALLSITE_MAP.json, DATA_REHASH_RECEIPT.json.

### Task 2 — general tilted state and physical constraints
Implement a typed state with:
- Bianchi type, Class A/B, a_alpha, n_alpha_beta, C^alpha_beta_gamma, h and algebra convention ID;
- normal geometry H_N, full STF5 Sigma_N and required lapse/normal acceleration terms;
- one independent V_s^alpha and EOS/source identity per species;
- observer/radiation/matter/catalogue frame IDs and epoch/basis IDs;
- exact normal-frame projections epsilon_N,J_a,S_ab,pi_ab;
- derived kinematics theta_s,sigma_s,omega_s,A_s for each species.

Implement constraint residuals and family admissibility:
- Jacobi;
- Hamiltonian;
- all three momentum constraints;
- Gauss-Codazzi and propagation residuals;
- energy/Euler equations for every fluid.
Build type-specific admissibility from the actual equations and cited literature. Do not hard-code a universal prior box.
Fixtures must include Bianchi-I single-fluid forbidden tilt; the published two-fluid Bianchi-I future-stability branch for positive Lambda and 1/3 < K_1 <= K_2 < 5/7 (Fournodavlos, Marshall & Oliynyk 2026, DOI 10.1007/s00023-026-01727-7); allowed multi-fluid total-momentum cancellation; tilted II; VI_0; VI_h at h=-1/9 and generic h; Class-B III/IV/V/VII_h; vortical tilted VIII/IX cases where admissible. The two-fluid Bianchi-I result is prior art and a benchmark, not a novelty claim. A fixture is not an observed solution.

### Task 3 — general dynamical system
- Build an expansion-normalized invariant-frame RHS covering full STF shear and vector tilt.
- Keep the metric/coframe connection as an independent curvature oracle.
- Enforce constraints at IC and every accepted step, abort on violations.
- Use adaptive solver tolerances and grid-refinement convergence.
- Test untilted and FLRW limits, exact known branches, class-wise boundaries and extreme-tilt domain limits.
- Do not expand the five-family reduced RHS by adding labels without deriving the missing equations.
Outputs: general_rhs, family_registry, convergence report, exact branch regression report.

### Task 4 — general photon and CMB transfer
- Generalize the Bianchi-I hierarchy only after a family-dispatched geodesic/screen operator exists.
- Carry photon direction in the invariant tetrad, screen basis, polarization rotation, visibility and Thomson collision terms.
- Include temperature and linear polarization I,Q,U or T,E,B.
- Distinguish normal shear, matter shear and radiation shear.
- Reproduce Bianchi-I endpoint, then V/VII_h reference patterns, then add Class-A/Class-B cases.
- Use external AniCLASS/ABSolve outputs as a comparison oracle, not as proof that our own native implementation ran.
- Do not claim coverage for non-FLRW-limit families using a linearized near-FLRW solver.

### Task 5 — common likelihood and tensorized five-view
- Create one source-bound generative model for CMB, counts, astrometry and directional distances.
- Model a_lm with deterministic Bianchi mean plus the complete covariance, including BipoSH/off-diagonal terms, beam, mask, foreground and noise.
- Model Quaia, NVSS and RACS as separate point processes with actual selection/random/catalogue inputs and covariance.
- Model Gaia source-level proper motions, scanning law, full covariance and reference-frame spin nuisance.
- Model Pantheon+ and CF4 with exact rows, full covariance, selection and group/method uncertainties.
- DESI isotropic BAO is a background control only unless the angular estimator is used.
- Derive x,Q,Pi,F,G_F from one common posterior. Ensure every functional has rank, parity, units, frame, epoch, operator ID, normalization and canonical state ID.
- Add scalar x_C only as an ablation.
- Cobaya missing-input preflight must fail closed.

### Task 6 — observed CMB path without an NPIPE blocker
Primary calibrated lane:
- Planck PR3 SMICA/HM and same-release FFP10.
- Recheck exact local hashes, FITS headers, frame, ordering, units, masks, splits, beams and transfer windows.
- Existing PR3 pilot used only 60 pairs and is not final calibration. Start with N=60 smoke, N=200 pilot, then N>=500 or a justified MC-error stopping rule.
- Re-run estimator bias, injections, coverage, SBC and PPC. Use a deterministic seed ledger.
- Keep split-map noise diagnosis separate from cosmic-variance null.

NPIPE PR4:
- Inventory says 22 files (~19.78 GB) are held. Rehash locally.
- Use full NPIPE maps only as a separate observed-map robustness comparison after beam/transfer/mask/frequency/pixelization harmonization.
- Use half-ring differences only as a noise-only diagnostic with one-realization limitation.
- Do not treat PR3 FFP10 as PR4 matched simulations.
- Optional synthetic PR4 null: declare C_l, noise model, transfer and assumptions; label SYNTHETIC/TRANSFER_CONDITIONAL.
- The absence of official matched NPIPE MC must never block the calibrated PR3 primary result.

### Task 7 — other owned-data analyses
Use already held data only:
- Quaia, NVSS, RACS counts;
- Gaia DR3/CRF3 plus scanning law;
- Pantheon+ full covariance and CF4 grouped/source data;
- DESI directional/full-shape products only when angular information exists.
Reconcile every row, source ID, selection and covariance. No hard-coded values and no fake randoms.

### Task 8 — sampler and adversarial benchmark
- Run source-bound Cobaya chains only after all adapter preflight passes.
- Record priors, sampler version, random seed, chain paths external to Git, code commit, data hashes and config hashes.
- Require split-Rhat plus bulk/tail ESS, SBC/coverage, PPC and leave-one-probe-out tests.
- Benchmark against Bianchi VII_h template fit, BipoSH-only, multipole vectors/power tensor, local-boost-only, FLRW+local-structure, single-probe fits and scalar x_C ablation.
- Test family false-positive rates under action-equivalent geometries and covariance/selection misspecification.
- Report honestly where HTT wins, ties, loses or cannot be compared.

### Task 9 — result receipt and push
- Write compact JSON/Markdown receipts in the R49 package, not raw maps or chains.
- Update R49_DAG.json and R49_CLAIM_LEDGER.json only for actually executed tasks.
- Run targeted tests, relevant full suites and compile checks. Record exact command, environment, exit code, duration and commit/tree identity.
- Review the exact diff. Push only to research/r49-general-tilted-bianchi-20261112. Never force-push. Update the existing R49 draft PR.
- Do not merge PR #573, #574 or R49 automatically.

## Required acceptance tests

1. All eleven algebra fixtures obey Jacobi and convention round-trip.
2. The normal-frame stress tensor projections match direct tensor projection for random subluminal V.
3. Bianchi-I single-perfect-fluid nonzero tilt is rejected under the theorem assumptions.
4. A two-fluid Bianchi-I counter-streaming fixture with total normal-frame momentum zero is admitted only if all other Einstein/fluid constraints pass.
5. Each species' fluid kinematics differ from normal kinematics in a nontrivial tilted fixture.
6. Class A and Class B vector-tilt RHSs pass constraint-preservation and grid-convergence tests.
7. h=-1, h=-1/9, rank-change and eigenvalue-degeneracy boundaries do not divide by zero or silently relabel a type.
8. Bianchi-I and V/VII_h ray/polarization reference limits are reproduced.
9. CMB mean and covariance are not double-counted.
10. PR3 FFP10 coverage is calibrated; NPIPE map-only lane is not mislabeled as a matched null.
11. Source-bound likelihoods fail closed when any required source/covariance/selection/frame/transfer is missing.
12. x,Q,Pi,F,G_F are emitted from one common posterior.
13. All benchmark comparisons use matched sources, masks, covariance and priors where possible.

## Anti-drift and anti-hallucination protocol

For every scientific or implementation claim, record:
- claim ID;
- exact source path and commit;
- evidence kind: established / literature-supported / derived / numerically-checked / implementation-verified / conjectural / unresolved;
- test status: PASS / CONCERN / FAIL / NOT_RUN;
- failure class: theory / numerical / implementation / runtime-environment / input-missing / authorization;
- exact scope and limitation.

Never:
- claim a test passed without the actual command result;
- infer local files exist from the GitHub data catalogue;
- cite a branch name as proof a commit was merged;
- present synthetic or mock values as observed;
- make a literature priority claim from a bounded search;
- say Bianchi I has genuine single-fluid tilt without resolving its momentum constraint;
- say B1 equals vorticity without a frame-spin anchor;
- say PR4 has matched coverage from PR3 FFP10;
- infer Bianchi family from anisotropy amplitude or curvature spectrum alone.

After each productive task save one compact checkpoint: completed outputs, exact identity, tests run, unresolved issue and the single next action. Do not create new meta-gates unless a concrete defect requires one. Stop repeated reviews after one bounded adversarial pass and repair material defects directly.

## Required return format

At completion return:
1. exact branch/head/tree;
2. PR URL and draft/ready status;
3. files changed;
4. exact local dataset identities and sizes/hashes;
5. equations/operators implemented;
6. commands and tests with exit codes;
7. sampler diagnostics and posterior summary if actually run;
8. per-claim evidence state;
9. failures/blockers with failure class and smallest next action;
10. what was deliberately not claimed.

Begin with Task 0 and then proceed sequentially. Do not ask the user to repeat information already in the repo.