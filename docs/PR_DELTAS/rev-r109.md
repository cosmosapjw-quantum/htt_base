# REV-R109 - LR-06B + LR-06C: PAPER-A/PAPER-B theorem gates, symbolic proofs, figures

owner: BASS
implementation_scope: bass_py
claim_tier: program_theorem
transfer_source: none
sky_support_status: not_directional
null_mock_status: synthetic_only
generating_command: `make paper-a-gates && make paper-b-gates`
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

LR-06B (PAPER-A) and LR-06C (PAPER-B) run in parallel after the LR-06A
foundation, with no raw data. Consolidate the identifiability/congruence and the
restricted Bianchi-I dynamics theorem suites: prove the analytic cores, add the
`make paper-a-gates`/`make paper-b-gates` targets (which the handoff left "to be
added in canonical repo"), map theorems to tests, and ship a synthetic figure
suite.

## Deliverables (shared across both papers)

- `scripts/prove_pr04_paper_theorems.py`: Wolfram symbolic proofs of seven
  analytic cores -> `docs/generated/pr04_paper_theorem_proofs.{json,md}`. All
  QED=True. PAPER-A: A-rank (duplicate block adds zero identifiable rank, (x,-x)
  nullspace), A-flrw (flat-FLRW first jet theta=3H, zero shear), A-wigner
  (non-collinear boosts compose to an exact Lorentz map whose velocity != the
  Euclidean rapidity sum). PAPER-B: B-nonsuff (equal Omega_tilt, different STF Pi),
  B-psd (PSD second moment = sum of antipodal eigen-pairs), B-dust (exact dust
  scale factor gives Hdot=-(3/2)H^2 and exact Gauss constraint), B-shear
  (sigmadot=STF(-3H sigma + kappa Pi), d(sigmadot)/dPi = kappa).
- `Makefile`: thread-pinned targets `paper-a-gates` (14 gate tests + proofs),
  `paper-b-gates` (9 gate tests + proofs), `pr04-gates` (all 23 + forbidden-dep
  scan + proofs), `pr04-proofs`, `pr04-forbidden-deps`.
- `docs/research_program/pr04/PAPER_THEOREM_MAP.md`: theorem -> gate test ->
  symbolic-proof id -> status, with the registered Bianchi-I branch stated and
  the three PAPER-A corollaries (radial-vorticity no-go, single-shell degeneracy,
  temporal tensor rank) honestly marked `BLOCKED_PROOF_REVIEW`.
- `scripts/make_pr04_paper_figures.py`: four diagnostic-only figures generated
  from the real overlay modules (A1 rank ladder, A2 Wigner non-additivity, B1
  scalar non-sufficiency, B2 dust-FLRW error + shear memory) with source.json +
  gated manifests; `--check` deterministic.

## Status against PAPER_EXIT_CRITERIA

- PAPER-A: response identifiability, complementary-channel sufficiency, and
  congruence/Wigner kinematics PASS (symbolic). Radial-vorticity no-go,
  single-shell degeneracy, temporal tensor rank remain `BLOCKED_PROOF_REVIEW`
  (analytic corollaries of the proved rank audit; standalone proofs pending
  independent review; temporal-rank ties to LR-06G).
- PAPER-B: flux balance, PSD tilt moments, exact conservation + constraint
  transport (exact FLRW oracle), shear memory, scalar nonclosure all PASS
  (symbolic or symbolic+numeric). `BLOCKED_DYNAMICS_REVIEW` (independent dynamics
  review) remains the submission-prep gate.

## Claim boundary

Program theorems under registered hypotheses; structural identities, not
detections. No raw data, native solver output, or family identification. Figures
are diagnostic-only/paper-appendix-conditioned with `family_identification:false`,
`native_solver_result:false`.

## Validation

| Command | Status |
| --- | --- |
| `venv/bin/python scripts/prove_pr04_paper_theorems.py` | ALL_QED (7/7) |
| `make paper-a-gates` | Ran 14 tests OK + ALL_QED |
| `make paper-b-gates` | Ran 9 tests OK + ALL_QED |
| `make pr04-gates` | 23 tests OK + forbidden-deps clean + ALL_QED |
| `venv/bin/python scripts/make_pr04_paper_figures.py --check` | up to date |
