# REV-R116 - PR07 audit-repair: Stage-0 harness + PR07-001/002/003/004/005/006

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
generating_command: `make pr07-gates && make pr07-wolfram && python scripts/run_pr07_experiments.py && python scripts/cove_verify_pr07.py`
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Apply the 2026-06-25 PR07 adversarial-audit pack
(`pr07_research_repair_execution_pack.zip`, MAJOR_REVISIONS verdict) to this
repo: adopt its harness/agents/skills and execute the staged repair PRs. This
delta lands Stage-0 (harness) plus the portable repair PRs PR07-001..006; the
governance / ticket surface and CHANGELOG land in a follow-up delta.

## Decisions

- Continue on branch `research/pr04-multicomponent` (additive commits).
- Fold the pack's harness into the existing repo (no parallel `htt_pr07`
  package): the audit's 10 CoVe lanes map 1:1 onto the repo's `.claude` agents
  and `htt-*` skills; physics is ported into the canonical `bass`/`obsstat`/
  `departure` modules; gates are wired into the `Makefile` + `research_gates/pr07/`.

## Changes

### Stage 0 - harness (folded)
- `Makefile`: `pr07-gates` (portable), `pr07-wolfram` (local symbolic),
  `pr07-cove`; PYTHONPATH spans repo / repo/htt / repo/htt/htt; interpreter
  fallback venv->python3->python.
- `research_gates/pr07/tests/test_pr07_{units,conservation,integrators,paper_a}.py`
  exercise the real `bass`/`departure` modules (16 gates).
- `wolfram/pr07_{symbolic_core,xact_abstract,bianchi_i_coordinates}.wls` +
  `scripts/run_pr07_wolfram_proofs.py` -> `docs/generated/pr07_wolfram_proofs.json`
  (wolframclient backend, xAct 1.3.0). **Fixed a real bug in the pack's
  coordinate script**: the Christoffel symbol was named `Gamma`, colliding with
  the protected built-in (Euler gamma), silently voiding the definition and
  yielding `theta=0`; renamed to `Chr`, so theta = H1+H2+H3 now verifies.
- `scripts/capability_probe.py` -> `docs/generated/pr07_capability_probe.json`
  (records engine/xAct presence as a registered status; absence is a blocker).
- `scripts/run_pr07_experiments.py` + `scripts/cove_verify_pr07.py` ->
  `docs/generated/pr07_{paper_a,paper_b,k1,k5,k6}.json` + `pr07_cove_report.json`
  (schema htt.pr07.cove.v1, PASS_WITH_REGISTERED_DELEGATIONS, 13/13 checks).
- `scripts/pdf_claim_lint.py`: FAIL_PATTERNS extended with the PR07 forbidden
  overclaims (EGS identity, cosmic-variance floor, tilt signature,
  model-independent anomaly, CRLB/Cramer-Rao, minimum-variance estimator);
  the first five are strict.
- `.github/workflows/pr07-audit-repair-gates.yml`: forbidden-deps (required) +
  PR04/PR07 gates + experiments + CoVe + contract test + JSON/checksum artifacts.
- `.gitignore`: ignore the input-drop pack + its extraction.

### PR07-001 - unit-safe anisotropic-stress ownership
- `bass/background/bi_continuation/moments.py`: `normalize_anisotropic_stress`,
  `physical_anisotropic_stress`, explicit `pi_physical` owner + `Pi_normalized`
  property; `TiltMoments.Pi` kept as deprecated alias; kappa<=0 guard; exact
  convention gate in `tilt_moments`.
- `bass/background/bi_continuation/dynamics.py`: `shear_rhs_from_physical` /
  `shear_rhs_from_normalized` (exactly equivalent); `rhs` uses the physical
  form; `1-w v^2` and dust-domain guards.
- `docs/final_report/main.tex`: B-shear equation now
  `STF(-3H sigma + kappa pi) = STF(-3H sigma + 3H^2 Pi)`, derivatives kappa and
  3H^2, invalid `kappa Pi` removed; figure caption names the physical stress.
- Acceptance met: round-trip 1.6e-16, two-path 0.0, d/dpi=kappa, d/dPi=3H^2.

### PR07-002 - theorem and claim repair (Wolfram-gated)
- NT-A1 -> closure-conditional identity (symbolic kappa; 4/21 figure-only).
- NT-A3 -> sampling variance of the standard ideal full-sky Gaussian estimator
  (equality, not a Cramer-Rao bound / universal floor).
- NT-B3 -> additive contrast `Delta_F = L F`, `L 1 = 0`; legacy ratio branch-
  limited to nonzero reference bins; attribution needs a response-rank gate.
- A-Wigner split into A-boost (exact composition, explicitly not a Wigner-angle
  claim) + A-first-jet no-go; A-rank null-space equality qualified by full
  column rank. Forbidden tokens removed; captions realigned.

### PR07-003 - independent Bianchi-I dynamics verification
- `bass/background/bi_continuation/verification.py`: chain-rule conservation
  residuals (independent of the production RHS), Gauss/Codazzi transport, and
  DOP853/Radau event-guarded `integrate_solve_ivp`. Gates: 1000-state residuals
  <1e-11, DOP853/Radau exact-dust <1e-9, RK4 slope in [3.6,4.4].

### PR07-004 - PAPER-A proof closure
- `htt/htt/htt/departure/paper_a_closure.py`: numerical_rank,
  duplicate_block_audit (full-column-rank qualification), radial_vorticity_response
  (no-go), single_shell_dipole_design (rank 3 vs broad-depth rank 6),
  temporal_tensor_design (rank 15), boost_composition_audit, first_jet_counterexample.

### PR07-005 - reproducible gate surface
- Makefile PYTHONPATH/interpreter fallback; forbidden-deps as a required CI
  check; portable numerical gates separated from the local Wolfram gate; JSON +
  checksums published as CI artifacts.

### PR07-006 - measurement wording + PR08-002/K6/K1 mechanics
- `obsstat/bulkflow_mle.py`: K5 renamed to weighted-Gaussian MLE/GLS (not
  minimum-variance); inverse-Fisher covariance labelled conditional; PR08-002
  `fit_hierarchical_bulk` + `hierarchical_coverage_experiment` (random
  effects + profiled sigma_star; measurement/mock/cosmic covariance separated).
- `obsstat/affine_flow.py`: `potential_flow_projection` + `curl_suppression_ensemble`
  (K6 structural non-identifiability; no recovered-vorticity inference).
- `obsstat/lowell_global_calibration.py`: K1 max-scan global calibration mechanics.
- `docs/final_report/main.tex`: K4 strict-lower-bound/edge attribution softened;
  K5 estimator renamed + conditional covariance; K6 vorticity recast as
  structurally non-identifiable.

## Claim discipline

No family identification, global tilt, native-solver result, or physical-
vorticity detection. All new artifacts are synthetic/theorem mechanics or
transfer-conditional diagnostics. Forbidden-token claim lint passes (0 failed).
Blocked observational lanes terminate in registered blocker codes (no proxy).

## Validation

| Command | Status |
| --- | --- |
| `verify_forbidden_dependencies.py` | PASS (0 findings) |
| `unittest research_gates/pr04` | 23/23 |
| `unittest research_gates/pr07` | 16/16 |
| `make pr07-wolfram` | PASS (all symbolic checks true; xAct 1.3.0) |
| `run_pr07_experiments.py` + `cove_verify_pr07.py` | PASS_WITH_REGISTERED_DELEGATIONS (13/13) |
| `pytest tests/contracts/test_pr07_audit_repair.py` | 6 passed |
| `pytest tests/obsstat` | 111 passed |
| `latexmk docs/final_report/main.tex` | PASS; 14 pages |
| `pdf_claim_lint.py --pdf .../main.pdf` | Failed 0 |
