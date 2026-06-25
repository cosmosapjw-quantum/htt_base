# REV-R123 - EGS3 framework upgrade + driver + programme docs + Axis C tickets

owner: COMMON
implementation_scope: common
claim_tier: program_theorem_and_synthetic_mechanics
transfer_source: none
generating_command: `make egs3-experiments + pytest tests/contracts/test_{egs3_extension,graded_comparator_upgrade}.py`
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Land the EGS3 framework upgrade, the experiment driver, the programme docs, and
the Axis-C data-discharge tickets (continuing the approved plan after the Axis
A/B theorem layer in rev-r122).

## Changes

### Framework upgrade (additive, x_C bit-identical)
- `htt/htt/htt/core/departure_posteriors.py`: `compute_graded_comparator()`
  exposes the graded comparator `g=(Sigma2,W2,Omega_tilt,Omega_k_aniso)` and
  asserts `x = Sigma2-W2+Omega_tilt+Omega_k` reconstructs the signed comparator
  bit-identically (a view, not a redefinition). Removes the sign-cancellation
  ambiguity and the `F<0` pathology without touching any downstream artifact.
- `tests/contracts/test_graded_comparator_upgrade.py` (3 gates): bit-identical
  reconstruction, sector identity preserved under cancellation, `x` not mutated.

### Driver + harness
- `scripts/run_egs3_experiments.py` -> `docs/generated/egs3_experiments.json`
  (Axis A + B evidence). `make egs3-experiments`.
- `tests/contracts/test_egs3_extension.py` (5 gates): A1 rank-2, A3 Markov,
  B1 k-profile, B3 transverse re-opening, JSON claim boundary.

### Programme docs (`docs/research_program/egs3/`)
- README, FRAMEWORK_CRITIQUE_AND_REDESIGN (the five-variable critique + graded
  upgrade + the PSD-cone revisionary redesign design), THEOREM_CANDIDATES
  (A1-A4, B1-B4, C1-C4), DIVERGENCE (diverge->metacog->verify->converge trace),
  BLOCKER_SOLUTIONS, CLAIM_LEDGER.yaml.
- tickets: `k1_ffp10_npipe.yaml` (C1), `cf4_wfcr.yaml` (C2), `psd_cone_redesign.yaml`.

## Claim discipline

The graded upgrade and the PSD-cone redesign change *representation*, not the
claim envelope. Axis-C real-data runs keep registered blocker codes; the
mechanics (e2e max-scan, CR curl posterior, hierarchical coverage) are landed.
No detection, family/geometry, or native-solver claim.

## Validation

| Command | Status |
| --- | --- |
| `pytest tests/contracts/test_graded_comparator_upgrade.py` | 3 passed (x_C bit-identical) |
| `pytest tests/contracts/test_egs3_extension.py` | 5 passed |
| `make egs3-experiments` | wrote egs3_experiments.json |
