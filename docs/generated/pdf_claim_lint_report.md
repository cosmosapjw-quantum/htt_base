# PDF Claim Lint Report

owner: COMMON
implementation_scope: common
claim_tier: blocked
transfer_source: none
sky_support_status: not_applicable_no_current_pdf
null_mock_status: not_applicable_no_current_pdf
config_hash: `sha256:480888c416b18eb2f2df60ea5ebc5d24c401e7a308bfe817d4660fc2c9b514e4`
input_hashes:
- docs/generated/cf4_p0_quarantine_block.json:sha256:7046c3bbefc18c840a36798fccd7f3dcdae9616ab1ef6f9eb2344e6c573405c7
caveats:
- No current manuscript PDF exists at the active path, so no PDF prose surface was scanned.
- The prior PDF and lint report are immutable historical evidence under legacy/cf4_p0 with public_use false.
- This blocked report is not a passing PDF claim lint and cannot satisfy a publication gate.
- The canonical CF4 P0 block record is authoritative and authorizes no replacement value.
generating_command: python scripts/pdf_claim_lint.py
git_commit_or_worktree_state: e6da367+dirty
artifact_path: docs/generated/pdf_claim_lint_report.md
status: BLOCKED_NO_CURRENT_PDF
claim_lint_passed: false

## Summary

- PDF: `docs/generated/manuscript_pdf/htt_base_research_report.pdf`
- PDF SHA256: `None`
- PDF manifest: `docs/generated/manuscript_pdf/htt_base_research_report.manifest.json`
- Quarantine block: `docs/generated/cf4_p0_quarantine_block.json`
- Quarantine block SHA256: `sha256:7046c3bbefc18c840a36798fccd7f3dcdae9616ab1ef6f9eb2344e6c573405c7`
- Pages scanned: `0`
- Failed findings: `0`
- Warning findings: `0`
- Open findings: `C1-K5-MV-F1, C3-K5-VCORR-ML-F1, N-DATA-CF4-DOWNSTREAM`

## Findings

No current PDF was linted. This surface is blocked by the canonical CF4 P0 quarantine record.
