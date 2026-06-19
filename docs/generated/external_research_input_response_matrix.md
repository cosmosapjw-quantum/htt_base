# External Research Input Response Matrix

owner: COMMON
implementation_scope: external_research_input_intake
claim_tier: diagnostic_only
transfer_source: none
config_hash: sha256:4126d40877fc558463f07dba1c1653e747c4ec4697df4b143b35381f65af3be8
input_inventory: `docs/audits/external_research_inputs_2026-06-20/input_inventory.json`
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `venv/bin/python scripts/inventory_external_research_inputs.py --write`
archive_manifest: `docs/audits/external_research_inputs_2026-06-20/ARCHIVE_MANIFEST.md`

## Prioritized Actions

| Priority | Action | Source inputs | Owner | Next step | kill-switches |
| --- | --- | --- | --- | --- | --- |
| P0 | audit minor revisions | `RESEARCH_AUDIT_REPORT.md` | COMMON/manuscript | Track the minor-revision items as bounded repo deltas: prose downgrades, cross-chapter numeric reconciliation, and Pi/Q/F terminology cleanup. | Stop promotion if a requested edit needs native solver validation, geometry-detection wording, or Bianchi family identification. |
| P0 | formalism harmonization | `RESEARCH_AUDIT_REPORT.md; publishable_data_analysis_program.zip` | COMMON/MIO/HTT | Reserve MIO Pi/Q/F language for diagnostic exceedance and filling reports, and keep HTT posterior semantics separate in manuscript-facing text. | Block any row that merges MIO diagnostics with HTT evidence terms or turns a diagnostic score into a truth claim. |
| P0 | CF4++ traceability | `RESEARCH_AUDIT_REPORT.md; htt_publishable_novel_analysis_program_2026-06-19.zip` | obsstat/HTT | Bind any CF4++ number to canonical input hashes, config hashes, and a rerunnable command before it appears in a result table. | Remove the number from result prose if canonical inputs cannot reproduce it. |
| P1 | local/global joint rest-frame program | `htt_publishable_novel_analysis_program_2026-06-19.zip` | HTT/obsstat | Map the joint rest-frame proposal onto the existing local/global candidate lane with observer-frame caveats and transfer provenance. | Keep it in forecast/candidate status until matched nulls, covariance, and observer-motion marginalization exist. |
| P1 | finite mock/rank/Fisher/null/PPC plan | `htt_publishable_novel_analysis_program_2026-06-19.zip; publishable_data_analysis_program.zip` | HTT/obsstat | Stage finite mock calibration, response-rank checks, Fisher diagnostics, matched nulls, and PPC/LOOCV gates before stronger inference wording. | Do not promote a likelihood or local/global statement when any rank, null, covariance, PPC, or LOOCV gate is missing. |
| P0 | theorem program P0 | `htt_beyond_mes_egs_theorem_program_2026-06-19.zip; egs_theorem_program.zip` | COMMON/physics_audit | Extract theorem statements, assumptions, units, frame conventions, and proof obligations into a repo-local audit table. | Abort promotion when assumptions depend on unavailable native transfer, unstated regularity, or hidden observer-frame choices. |
| P1 | theorem program P1 | `htt_beyond_mes_egs_theorem_program_2026-06-19.zip` | physics_audit/obsstat | Convert surviving theorem obligations into synthetic or analytic tests that exercise signs, limits, denominators, and finite-cover behavior. | Keep theorem artifacts proposed-only if tests are toy-only or lack dimension/frame coverage. |
| P2 | theorem program P2 | `htt_beyond_mes_egs_theorem_program_2026-06-19.zip` | manuscript/COMMON | Only after P0/P1 closure, draft manuscript-safe theorem wording with explicit claim tier and caveat boxes. | Do not move proposed theorem text into publication-facing claims without independent proof review and validation evidence. |

## Intake Boundary

These rows convert uploaded audit/proposal material into repo-local work items. They do not promote any result, theorem, transfer output, or manuscript number.

## Caveats

- diagnostic/proposed inputs
- not publication evidence
- no native low-ell solver output or validation is present
- no Bianchi family identification
- no geometry-detection wording or evidence promotion
