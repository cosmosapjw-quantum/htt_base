# Manuscript Audit Repair Matrix

owner: COMMON
implementation_scope: manuscript_audit_repair
claim_tier: diagnostic_only
transfer_source: mixed_external_proxy_and_none
config_hash: sha256:manual-repair-matrix-rev-r089
input_hashes:
- docs/audits/external_research_inputs_2026-06-20/RESEARCH_AUDIT_REPORT.md
- docs/audits/external_research_inputs_2026-06-20_reaudit/audit_ver2.md
- docs/generated/audit_ver2_response_matrix.json
- docs/generated/pdf_claim_lint_report.md
- docs/manuscript/ch01_introduction.tex
- docs/manuscript/ch02_dipole_anomaly.tex
- docs/manuscript/ch03_framework.tex
- docs/manuscript/ch04_bianchi_bounds.tex
- docs/manuscript/ch05_teff_corrections.tex
- docs/manuscript/ch07_results.tex
- docs/manuscript/ch08_robustness.tex
- docs/manuscript/ch09_discussion.tex
- docs/manuscript/ch10_future.tex
sky_support_status: mixed_not_applicable_and_manifest_bound
null_mock_status: mixed_blocked_and_not_applicable
generating_command: manual matrix from RESEARCH_AUDIT_REPORT.md, audit_ver2.md, REV-R075 diff, and REV-R089 strict PDF lint
git_commit_or_worktree_state: pending_rev_r089_commit
caveats:
- not native transfer
- no morphology-family naming or selection claim
- no geometry-detection claim
- CF4++ sensitivity numbers remain quarantined until a dedicated rerun binds config and input hashes
- HTT posterior exceedance is distinct from MIO diagnostic exceedance
- positive lnB surfaces remain premise-conditioned amplitude fits, not source-identification claims
- PDF lint is a prose-surface gate and does not replace matched null, covariance, PPC, LOOCV, or native-atlas validation

This matrix tracks closure of the immediate external manuscript audit findings
and the stricter follow-up re-audit downclaim requirements without promoting any
legacy transfer-dependent number to native-solver evidence.

| Finding | Files | Resolution | Status |
| --- | --- | --- | --- |
| neutrino quadrupole wording | `docs/manuscript/ch05_teff_corrections.tex`, `docs/manuscript/ch09_discussion.tex` | replaced discovery/accuracy wording with transfer-conditional contribution-fraction language and explicit non-native status | closed |
| CF4++ lnB provenance | `docs/manuscript/ch07_results.tex`, `docs/manuscript/ch08_robustness.tex`, `docs/manuscript/ch09_discussion.tex` | removed headline promotion and marked `+44/+105.8` sensitivity values as non-canonical, quarantined, or pending dedicated rerun before publication use | closed |
| Q/F/Pi harmonization | `docs/manuscript/ch03_framework.tex`, `docs/manuscript/ch07_results.tex` | separated HTT posterior exceedance `\Pi_{\rm HTT}` from MIO diagnostic exceedance `\Pi_{\rm MIO}` and clarified that MIO `Q/F/Pi` carry no posterior, occupancy, or evidence semantics | closed |
| headline departure number provenance | `docs/manuscript/ch01_introduction.tex`, `docs/manuscript/ch02_dipole_anomaly.tex`, `docs/manuscript/ch07_results.tex` | split the legacy HTT posterior mean `\bar{Q}\simeq0.092` from the S3 filling fraction `\FF=0.063` for dust and `0.084` for radiation | closed |
| NO_FLRW_LIMIT rows | `docs/manuscript/ch07_results.tex` | replaced forced numeric Bayes entries with `N/A (no FLRW limit)` while retaining finite curved-reference rows separately | closed |
| sensitivity window wording | `docs/manuscript/ch07_results.tex` | replaced growing-mode detection wording with sensitivity-band/sensitivity-window wording | closed |
| observer-frame marginalization pending | `docs/manuscript/ch07_results.tex`, `docs/manuscript/ch09_discussion.tex` | marked legacy `ln B` numbers as rest-frame conditional and stated observer-frame marginalization remains pending | closed |
| strict positive `ln B` reclassification | `docs/manuscript/ch01_introduction.tex`, `docs/manuscript/ch02_dipole_anomaly.tex`, `docs/manuscript/ch07_results.tex`, `docs/manuscript/ch08_robustness.tex`, `docs/manuscript/ch09_discussion.tex`, `docs/manuscript/ch10_future.tex` | reclassified positive Bayes-factor language as premise-conditioned amplitude fit, configured likelihood-ratio value, or legacy diagnostic bin; removed source-identification and geometry-support readings | closed in REV-R089 |
| PDF-surface claim firewall | `scripts/pdf_claim_lint.py`, `docs/generated/pdf_claim_lint_report.md`, `tests/contracts/test_pdf_claim_lint.py` | added strict fail patterns for re-audit phrases and high-strength `ln B` contexts; final PDF lint reports `Failed findings: 0` for `htt_base_research_report.pdf` sha256 `7243cebf41226475f124d9466f3aa81cd5c6cd28ddf0ab9c429669fd76be4239` | closed in REV-R089 |
| PPC and contaminated-null interpretation | `docs/manuscript/ch07_results.tex`, `docs/manuscript/ch08_robustness.tex`, `docs/manuscript/ch09_discussion.tex` | changed PPC language from data-property wording to single-`\beta` likelihood/covariance predictive-adequacy failure; kept contaminated-null failure as a blocker for stronger source claims | closed in REV-R089 |
| comparator and filling semantics | `docs/manuscript/ch07_results.tex`, `docs/manuscript/ch08_robustness.tex`, `docs/manuscript/ch09_discussion.tex` | replaced most-conservative flat-comparator framing with fiducial comparator plus comparator envelope; split class-conditioned filling from legacy budget-normalised score | closed in REV-R089 |
| source hierarchy and future-test wording | `docs/manuscript/ch02_dipole_anomaly.tex`, `docs/manuscript/ch08_robustness.tex`, `docs/manuscript/ch10_future.tex` | removed wording that made survey-independence, future Bayes-factor forecasts, or local-flow compatibility read as current source-identification evidence | closed in REV-R089 |
