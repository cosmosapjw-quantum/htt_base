# PDF Claim Lint Report

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
config_hash: `sha256:53080d0bb7cbfb8ab7d9a80afb876523b4d4f1fee33af31ca14781099f3a9a8f`
input_hashes:
- docs/final_report/main.pdf:sha256:109a8ba4e0a70d707f91d9c1dc101a0cd0763f6af41233750e9a2b7dfe1872a0
caveats:
- PDF text extraction is used as a final prose-surface lint.
- lnB numeric mentions are warnings unless paired with high-strength claim language.
- Direction-marginalized diagnostic-preference language is allowed as a warning-only technical Bayes-factor mention.
- Legacy or conditioned pages must carry explicit context markers.
generating_command: python scripts/pdf_claim_lint.py --pdf docs/final_report/main.pdf
git_commit_or_worktree_state: 55a2f68+dirty
artifact_path: docs/generated/pdf_claim_lint_report.md

## Summary

- PDF: `docs/final_report/main.pdf`
- PDF SHA256: `sha256:109a8ba4e0a70d707f91d9c1dc101a0cd0763f6af41233750e9a2b7dfe1872a0`
- Pages scanned: `18`
- Failed findings: `0`
- Warning findings: `0`

## Findings

No PDF claim-lint findings.
