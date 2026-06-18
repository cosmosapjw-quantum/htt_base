# PDF Claim Lint Report

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
config_hash: `sha256:22098db1b168d0b60541c71e785a8373ae1c406391bdd1ffde9c8fa6f440d65d`
input_hashes:
- docs/generated/manuscript_pdf/htt_base_research_report.pdf:sha256:da54b2b63a373e27d059c3a89815f7a7fa784669704623bb48bed94eeefcbb3c
caveats:
- PDF text extraction is used as a final prose-surface lint.
- lnB numeric mentions are warnings unless paired with high-strength claim language.
- Legacy or conditioned pages must carry explicit context markers.
generating_command: python scripts/pdf_claim_lint.py
git_commit_or_worktree_state: e40baf5+dirty
artifact_path: docs/generated/pdf_claim_lint_report.md

## Summary

- PDF: `docs/generated/manuscript_pdf/htt_base_research_report.pdf`
- PDF SHA256: `sha256:da54b2b63a373e27d059c3a89815f7a7fa784669704623bb48bed94eeefcbb3c`
- Pages scanned: `348`
- Failed findings: `0`
- Warning findings: `9`

## Findings

| Severity | Page | Pattern | Context |
| --- | ---: | --- | --- |
| `warn` | 115 | `lnB numeric or threshold` | inement of the single-fluid transfer function used in the VER06 legacy pipeline. It does not change the evidence value (ln B = +26.40) but it does provide the physical interpretation: the departure parameter measures, to 98% accuracy, the neutrin |
| `warn` | 142 | `lnB numeric or threshold` | el—the Bayesian Occam razor. Model comparison proceeds through the Bayes factor Bij := Zi , Zj (7.3) or equivalently ln Bij = ln Zi − ln Zj . We adopt the Jeffreys scale Jeffreys [1961] for qualitative interpretation: \| ln B\| < 1 is “not worth m |
| `warn` | 173 | `lnB numeric or threshold` | he fiducial [10−30 , 10−4 ], a narrow [10−15 , 10−6 ], and a wide [10−30 , 10−2 ]. The fiducial and wide variants yield ln B ≈ +26.3; the narrow variant drops to +3.0 because restricting the Σ2std range concentrates prior volume in a region of pa |
| `warn` | 181 | `lnB numeric or threshold` | hir SBI downgrade. 8.18 Summary of robustness findings Table 8.5 collects the key sensitivities. The tilt detection (ln B > 5) survives all tested perturbations except CMB-only and the extreme ρ > 0.85 limit. The departure quantities (Q, Π, vt |
| `warn` | 181 | `lnB numeric or threshold` | to +22.3 but remains above the legacy high-support threshold. To reduce the evidence below the “substantial” threshold (ln B < 2.5) requires ρ > 0.9, which is astrophysically implausible given the distinct wavelengths and selection functions. The |
| `warn` | 183 | `lnB numeric or threshold` | recovered ln B ≈ −3 under null data, confirming that the pipeline does not generate spurious tilt detections from structured systematics |
| `warn` | 183 | `lnB numeric or threshold` | use model (single direction + amplitude for all surveys) has a conditional diagnostic preference over the null model (∆ ln B = +29.7). Low-z ablation—removing each survey in turn—preserves the directional signal above threshold in all cases, conf |
| `warn` | 196 | `lnB numeric or threshold` | . This result does not invalidate the departure parameter detection; it constrains the interpretation. The Bayes factor ln Btilt = +25.29 measures the phenomenological signal for nonzero tilt across seven data channels. The Martı́n–Skordis analysis n |
| `warn` | 209 | `lnB numeric or threshold` | ihoods would be the natural next step. The directional information is the principal casualty of this design choice: the ln B ≈ +26.3 is a direction-marginalised Bayes factor that could strengthen or weaken under directional constraints. 9.9.2 W |
