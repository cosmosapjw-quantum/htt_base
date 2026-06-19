# Manuscript Audit Repair Matrix

owner: COMMON
implementation_scope: manuscript_audit_repair
claim_tier: diagnostic_only
transfer_source: mixed_external_proxy_and_none
config_hash: sha256:manual-repair-matrix-rev-r075
input_hashes:
- docs/audits/external_research_inputs_2026-06-20/RESEARCH_AUDIT_REPORT.md
- docs/manuscript/ch01_introduction.tex
- docs/manuscript/ch02_dipole_anomaly.tex
- docs/manuscript/ch03_framework.tex
- docs/manuscript/ch05_teff_corrections.tex
- docs/manuscript/ch07_results.tex
- docs/manuscript/ch08_robustness.tex
- docs/manuscript/ch09_discussion.tex
sky_support_status: mixed_not_applicable_and_manifest_bound
null_mock_status: mixed_blocked_and_not_applicable
generating_command: manual matrix from RESEARCH_AUDIT_REPORT.md and REV-R075 manuscript diff
git_commit_or_worktree_state: pending_rev_r075_commit
caveats:
- not native transfer
- no family identification
- no geometry-detection claim
- CF4++ sensitivity numbers remain quarantined until a dedicated rerun binds config and input hashes
- HTT posterior exceedance is distinct from MIO diagnostic exceedance

This matrix closes the immediate external manuscript audit findings without
promoting any legacy transfer-dependent number to native-solver evidence.

| Finding | Files | Resolution | Status |
| --- | --- | --- | --- |
| neutrino quadrupole wording | `docs/manuscript/ch05_teff_corrections.tex`, `docs/manuscript/ch09_discussion.tex` | replaced discovery/accuracy wording with transfer-conditional contribution-fraction language and explicit non-native status | closed |
| CF4++ lnB provenance | `docs/manuscript/ch07_results.tex`, `docs/manuscript/ch08_robustness.tex`, `docs/manuscript/ch09_discussion.tex` | removed headline promotion and marked `+44/+105.8` sensitivity values as non-canonical, quarantined, or pending dedicated rerun before publication use | closed |
| Q/F/Pi harmonization | `docs/manuscript/ch03_framework.tex`, `docs/manuscript/ch07_results.tex` | separated HTT posterior exceedance `\Pi_{\rm HTT}` from MIO diagnostic exceedance `\Pi_{\rm MIO}` and clarified that MIO `Q/F/Pi` carry no posterior, occupancy, or evidence semantics | closed |
| headline departure number provenance | `docs/manuscript/ch01_introduction.tex`, `docs/manuscript/ch02_dipole_anomaly.tex`, `docs/manuscript/ch07_results.tex` | split the legacy HTT posterior mean `\bar{Q}\simeq0.092` from the S3 filling fraction `\FF=0.063` for dust and `0.084` for radiation | closed |
| NO_FLRW_LIMIT rows | `docs/manuscript/ch07_results.tex` | replaced forced numeric Bayes entries with `N/A (no FLRW limit)` while retaining finite curved-reference rows separately | closed |
| sensitivity window wording | `docs/manuscript/ch07_results.tex` | replaced growing-mode detection wording with sensitivity-band/sensitivity-window wording | closed |
| observer-frame marginalization pending | `docs/manuscript/ch07_results.tex`, `docs/manuscript/ch09_discussion.tex` | marked legacy `ln B` numbers as rest-frame conditional and stated observer-frame marginalization remains pending | closed |
