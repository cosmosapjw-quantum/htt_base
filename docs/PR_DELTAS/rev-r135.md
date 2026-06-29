# REV-R135 - External-audit revision (two packs) + K1 noise-only long-run prep

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: mixed_none_observed_and_external_transfer_conditional
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Two external audit packs (separate from the internal phys-math-code audit committed at
`ee22a1f` / CHANGELOG rev-r134) arrived: `htt_research_evaluation_review` (MINOR) and
`pr08_reassessment_audit_pack` (MAJOR). Review and revise accordingly. Also prepare for the
K1 noise-only long-run (Planck noise-only data still downloading).

## What both reviewers actually flagged

They read the **committed report/table/artifact surfaces**, which lagged behind the
module-level fixes the internal rev-r134 had already landed (`NULL_SECTOR_KIND`,
`exceedance_evalue_finite_null`, the PSD Ω_k-signed fix). So most fixes are
surface-propagation; the genuine over-claims are the K5/K6 data labels. Full finding→fix
table: `docs/audits/external_2026-06-29/RESPONSE_MATRIX.md`.

## Changes

**Theorem-label precision** (`build_egs_results_table.py`, `run_egs3_experiments.py`,
`main.tex`): NT-A1 → closure-conditional; NT2-A1/EGS3-B1 → "conditional on the registered
shear-response profile" / single-mode finite-k (dropped "genuine"/"floor nothing
beats"/"strictly below"); NT-B3 → contrast language (no `G_F=1 iff`); NT2-B1 → registered
closure/H3 scope, explicitly not a generic-CMB statement; C_up=9 documented.

**Ω_k null precision** (audit substantive item): relabelled "joint null {W²,Ω_k}" →
structural null {W²} (order-independent; response column a *genuine zero*, not Σ²-collinear)
+ leading-EGS-order no-channel {Ω_k} (re-opens beyond leading order). New regression gate
`test_egs3_axis_a.py::test_omega_k_column_is_a_genuine_zero_not_sigma2_collinear` proves the
rank-2 count alone cannot distinguish the two; `run_egs3_experiments.py` now emits
`null_kinds` + `leading_order_response_col_norms` + the genuine-zero flag.

**K-row honesty downgrade** (`main.tex`, table, `BLOCKERS.md`, `pr08_006_joint_artifact.py`):
- K5: bulk flow `|B|=341±102 km/s` stays a measurement; CV coverage labelled CONDITIONAL on
  a fixed ΛCDM `σ_cv=150 km/s/comp` prior (not "release-matched forward mocks"); ΛCDM
  ~150-250 km/s expectation noted; full selection/Malmquist mocks remain a gate.
- K6: "WF mean-field curl-suppression no-go" with the true Hoffman-Ribak CR posterior STILL
  BLOCKED (not "discharged"); injection noted as a single solid-body mode.
- K1: SMICA 0.097 vs Commander 0.121 (~25%) flagged, reported side by side, not averaged.
- PR08-006: rank-2 = one measured (Ω_tilt) + one partial (Σ²) + two fail-closed.
- Abstract reframed to a diagnostic methods-and-calibration envelope.
- EGS3-A3 e-value: GRF-ΛCDM null idealisation stated; finite-null α=(k+1)/(n+1) referenced.

**K1 noise-only long-run mode** (`k1_global_maxscan.py` + `tests/obsstat/test_k1_noise_mode.py`):
`--noise-mc-dir [--method] [--max-noise-sims]` (route 4 of the download guide) adds a local
ΛCDM signal to the real per-method instrument-noise sims → a noise-augmented null, written to
a SEPARATE artifact (`k1_global_maxscan_e2e_noise.json`) so the canonical GRF result is
untouched. Method-matched, capped, robust to an empty dir. Honest residual: no residual
foregrounds/systematics, no matched signal → K1 stays `measured_partial`. Ready to run when
the ~300 noise files land. Exercised now with a synthetic fixture.

**Package self-containment** (`build_research_evaluation_package.py` +
`test_research_evaluation_package.py`): the 13 report-referenced scripts/proofs (+ the
`research_gates/pr04/tests` files) are bundled; `check_report_references` passes against the
`research_evaluation/` subtree. The eval prompt's claim framing updated to the corrected
post-audit statements.

**Linter hardening**: `scripts/claim_lint_research_surfaces.py` folds both packs'
forbidden-phrase set into a permanent repo gate over report+table+blockers;
`research_gates/external_audit_2026_06_29/reviewer_verification.py` committed as the
independent re-check; `tests/contracts/test_external_audit_2026_06_29.py` gates both.

**Hygiene**: K5 figure docstring/caveat "minimum-variance" → "weighted-GLS" (the PNG title was
already weighted-GLS); manuscript pdf_claim_lint verified 0-failed/66-warning (the audit's
"2 findings" does not reproduce; blessed lint report left untouched).

## Claim discipline

No published number changed; x_C bit-identity preserved. No family-ID, geometry, native-solver,
MIO-as-odds, or scalar→family. Major data tasks (full CF4 mocks; true CR posterior; native
solver) remain registered blockers / separate project.

## Validation

| Command | Status |
| --- | --- |
| `latexmk` report | PASS; 23 pages |
| `pdf_claim_lint` (final report, to scratch) | Failed 0, Warning 0 |
| `pdf_claim_lint` (manuscript, to scratch) | Failed 0, Warning 66 (lnB; = blessed) |
| `claim_lint_research_surfaces.py` + audit2 `claim_lint.py` | 0 hits each |
| `reviewer_verification.py` | 5/5 confirmed |
| `check_report_references.py` vs package subtree | 0 missing |
| new gate + K1-noise tests | 15 passed |
| egs2/egs3 gates + obsstat K-tests | 57 passed |
| `pytest tests/contracts/` | 355 passed, 0 failed |
| all audit packages rebuilt + `--check` | current |
| 4-lens adversarial verification workflow | see CHANGELOG |
