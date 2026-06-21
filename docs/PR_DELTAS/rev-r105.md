# REV-R105 - Self-Contained Final-Results Report + Separate External-Audit Package

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: mixed_none_observed_and_external_transfer_conditional
sky_support_status: mixed_full_sky_map_and_cf4_reconstruction_grid
null_mock_status: mixed_null_calibrated_bootstrap_and_synthetic_theorem
generating_command: `Codex REV-R105 build a credible-only final-results report and a separate external-audit zip + prompt`
git_commit_or_worktree_state: pending_rev_r105_commit

## Request

Produce a NEW, separate research report that removes all
old/outdated/legacy/deprecated material from the current report, carries only
credible results, is self-contained with final results (no development
history), and ships a separate zip + prompt for external audit. Keep the
existing version (the full VER06 manuscript) unchanged.

## Approach

Rather than strip the 12-chapter VER06 manuscript in place (which would destroy
its audit trail), author a fresh self-contained `article`-class report that
carries only the four kinds of result that survive the project's
claim-firewall, and wrap it in its own deterministic audit package. The full
manuscript under `docs/manuscript/` is untouched.

Credible-claim envelope carried into the new report:
1. Framework: the master departure comparator
   `x_C = Sigma2_std - W2_std + Omega_tilt + Omega_k_aniso` as a SIGNED
   comparator (not an invariant magnitude) and its diagnostic variables
   x_C/Q/Pi/F/G_F, plus the MES kinematic-bound linkage. (C1, diagnostic-only.)
2. Three Wolfram-verified conditional EGS-type theorems NT-A1/A3/B3 (REV-R104),
   with the broader convention-conditional registry (B4/G2/G5/S1/S3/S4/S5)
   named only as kill-switch-blocked program theorems.
3. Two null-calibrated model-independent real-data measurements: K1 (Planck PR3
   low-ell morphology vs isotropic LambdaCDM null) and K4 (CF4++ bulk-flow apex
   vs depth). (REV-R102/R103, diagnostic-only.)
4. Explicitly transfer-conditional diagnostics (AniCLASS-external /
   empirical-proxy shear->D_ell), provenance only, premise-conditioned,
   not source-identification.

Deliberately EXCLUDED from the new report: development history, superseded
paths, conditioned legacy appendix figures, any blocked overclaim, and any
result lacking a recorded generating command + manifest. A standing-blocks
section restates up front that family-ID, geometry detection, native-solver
validation, posterior-odds/model-ranking, and native-validation labels remain
blocked.

## Role Split

- Physics/statistics auditor steelman: the comparator must be presented as
  signed (the -W2 term can cancel); MES must be a derived bound under stated
  hypotheses; K1 p-values must be local/look-elsewhere-tracked/single-sky/not
  full-covariance; K4 bootstrap must be a lower bound, with the edge reversal
  flagged.
- Claim-gate reviewer steelman: every result is diagnostic-only or
  transfer-conditional; no numeric lnB is paired with high-strength language;
  the report passes `pdf_claim_lint` (0 failed, 0 warnings); the package
  manifest keeps `family_identification:false` and `native_solver_result:false`.
- Harness/reproducibility steelman: the package is byte-deterministic (fixed zip
  date, sorted entries) with a `--check` mode and a contract test; it reuses
  only manifest-backed figures.

## Changes

- `docs/final_report/main.tex`: new self-contained report (9-page PDF). Sections:
  scope/claim-discipline, framework, conditional theorems (NT-A1/A3/B3 +
  figures), model-independent measurements (K1 + K4 tables/figures),
  transfer-conditional diagnostics, standing blocks, reproducibility, and a
  self-contained bibliography. `\graphicspath{{../../figures/}}` reuses the six
  existing manifest-backed figures.
- `docs/final_report/main.pdf`: compiled report (latexmk, all refs resolved,
  six figures embedded). Tracked as the deliverable.
- `scripts/build_final_report_audit_package.py`: deterministic builder ->
  `docs/final_report/htt_base_final_results_audit_package.{zip,_manifest.json}`
  + `htt_base_final_results_audit_prompt.md`. Wraps the report (tex + pdf), the
  six figures + sidecar manifests, and the backing generated records
  (theorem proof record, K1/K4 reports, transfer inventory, claim freeze).
  Ships its own adversarial audit prompt. `--check` / `--dry-run` modes.
- `tests/contracts/test_final_report_audit_package.py`: gates pass, manifest
  keeps family-ID/native-solver blocked, zip deterministic, on-disk package
  up-to-date, report source carries no forbidden claim language, report PDF
  passes claim-lint (0 failed).
- `.gitignore`: track `docs/final_report/main.{tex,pdf}`; ignore latexmk scratch
  and the transient claim-lint check file.

## Artifact Metadata

- owner: COMMON
- implementation_scope: common
- claim_tier: diagnostic_only
- config_hash:
  - `scripts/build_final_report_audit_package.py:sha256:11cd82b2e107d367f2b2f56858bcc3ea015a42ff572803975de779ac7d1f37ce`
  - `docs/final_report/main.tex:sha256:dce4dc58525660e7fad2291410bc3349e76512366f0d2dea600b909551049e2c`
  - `tests/contracts/test_final_report_audit_package.py:sha256:655e0b8e7e2b9adae1d96aa2eb0487768ae9392bf42c33aea6eb3f5cf7b48e16`
- caveats:
  - self-contained credible-claim distillation; not the full development manuscript;
  - all results diagnostic-only or explicitly transfer-conditional;
  - no Bianchi family-ID, no geometry detection, no native low-ell solver validation;
  - the full VER06 manuscript under docs/manuscript/ is preserved unchanged.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `latexmk -pdf main.tex` (from docs/final_report) | PASS | 9 pages; all refs resolved; six figures embedded. |
| `venv/bin/python scripts/pdf_claim_lint.py --pdf docs/final_report/main.pdf` | PASS | Failed findings 0, warning findings 0. |
| `venv/bin/python scripts/build_final_report_audit_package.py` | PASS | 28 entries; all required assertions true. |
| `venv/bin/python scripts/build_final_report_audit_package.py --check` | PASS | Byte-deterministic; up-to-date. |
| `pytest -q tests/contracts/test_final_report_audit_package.py` | PASS | `6 passed`. |
| figure no-op | N/A | No new figures generated (reused existing manifest-backed set); no gallery regen required. |
