# PDF Claim Lint Report

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
config_hash: `sha256:22098db1b168d0b60541c71e785a8373ae1c406391bdd1ffde9c8fa6f440d65d`
input_hashes:
- docs/generated/manuscript_pdf/htt_base_research_report.pdf:sha256:404748a9873db0f314e0e0c3facb76e2b103c9be026e4693f8b88ffa222d3950
caveats:
- PDF text extraction is used as a final prose-surface lint.
- lnB numeric mentions are warnings unless paired with high-strength claim language.
- Legacy or conditioned pages must carry explicit context markers.
generating_command: python scripts/pdf_claim_lint.py
git_commit_or_worktree_state: 367039e+dirty
artifact_path: docs/generated/pdf_claim_lint_report.md

## Summary

- PDF: `docs/generated/manuscript_pdf/htt_base_research_report.pdf`
- PDF SHA256: `sha256:404748a9873db0f314e0e0c3facb76e2b103c9be026e4693f8b88ffa222d3950`
- Pages scanned: `344`
- Failed findings: `0`
- Warning findings: `7`

## Findings

| Severity | Page | Pattern | Context |
| --- | ---: | --- | --- |
| `warn` | 114 | `lnB numeric or threshold` | inement of the single-fluid transfer function used in the VER06 legacy pipeline. It does not change the evidence value (ln B = +26.40) but it does provide the physical interpretation: the departure parameter measures, to 98% accuracy, the neutrin |
| `warn` | 141 | `lnB numeric or threshold` | el—the Bayesian Occam razor. Model comparison proceeds through the Bayes factor Bij := Zi , Zj (7.3) or equivalently ln Bij = ln Zi − ln Zj . We adopt the Jeffreys scale Jeffreys [1961] for qualitative interpretation: \| ln B\| < 1 is “not worth m |
| `warn` | 171 | `lnB numeric or threshold` | he fiducial [10−30 , 10−4 ], a narrow [10−15 , 10−6 ], and a wide [10−30 , 10−2 ]. The fiducial and wide variants yield ln B ≈ +26.3; the narrow variant drops to +3.0 because restricting the Σ2std range concentrates prior volume in a region of pa |
| `warn` | 179 | `lnB numeric or threshold` | to +22.3 but remains above the legacy high-support threshold. To reduce the evidence below the “substantial” threshold (ln B < 2.5) requires ρ > 0.9, which is astrophysically implausible given the distinct wavelengths and selection functions. The |
| `warn` | 207 | `lnB numeric or threshold` | ihoods would be the natural next step. The directional information is the principal casualty of this design choice: the ln B ≈ +26.3 is a direction-marginalised Bayes factor that could strengthen or weaken under directional constraints. 9.9.2 W |
| `warn` | 207 | `lnB numeric or threshold` | hysical. The departure is tilt-dominated: Ωtilt contributes > 99% of x; shear contributes < 10−12 . Non-zero departure (ln B = +26.4) is robust to LOCO ablation, prior variation, and correlation sweeps. 206 |
| `warn` | 218 | `lnB numeric or threshold` | through a coarse-graining procedure—remains an open theoretical problem. Third, the direction-marginalised Bayes factor ln B ≈ +26 (VER05 primary) discards potentially model-separating directional information. A joint pixel-level analysis using t |
