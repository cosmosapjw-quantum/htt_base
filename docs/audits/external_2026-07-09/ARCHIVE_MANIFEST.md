# External Review Bundle Archive Manifest — v6 → v7

owner: COMMON
implementation_scope: external_review_input_intake
claim_tier: diagnostic_only
transfer_source: none
generating_command: manual archive (bundle intake for the v7 / Fifth-Revision cycle)

## Boundary

This folder archives the human-readable review documents extracted from the four
external audit/upgrade bundles delivered on 2026-07-09, each reviewing the v6
external-audit research report (`external_audit_research_report_20260708_v6`,
rev-r146). They are external-reviewer inputs only — **not** repo-authored current
research claims, validation artifacts, publication evidence, native-transfer
outputs, or family-identification support. External code shipped inside the
bundles is reference-only and is **reimplemented**, never imported, in v7.

The four source `.zip` archives remain untracked at the repository root because
`scripts/build_v7_external_audit_synthesis.py` reads them there as fail-closed,
hash-verified inputs. Their SHA256s are pinned below and in
`docs/generated/v7_external_audit_synthesis_matrix.json`.

## Source bundles (SHA256, root-untracked)

| Bundle zip | SHA256 | Role |
| --- | --- | --- |
| `htt_v6_critical_review_bundle.zip` | `5fa351f7250cec810003ae0aa4e00127802ec56b3fe70938554cb7de541ac9f4` | critic review + P0/P1/P2 checklist + package-integrity audit |
| `htt_v6_referee_package_20260709.zip` | `dd7f5f842db170ef0110a1e89c4c009acfabb892fb145c92eb771e8fc5dabffa` | referee report F1–F3/M1–M10/m1–m12 + 12 numerical experiments |
| `htt_v6_referee_fortification_package_v2.zip` | `86586d44d3bf0143ad59f9e00eef6f2afa5fe2dc02a44a8860d77fa19822bbe4` | referee superset + fortification plan + strengthened-theorem proofs |
| `htt_v6_strengthened_publication_bundle.zip` | `43ff42a3176ccf8cd562a4a9a039382fe9ea60c922416e5697726f2a06d2a237` | publication-strengthening strategy + WP0–WP8 + claim-defense matrix |

## Archived documents

- `critical_review/` — critic review (`critical_review_ko.md`), own theorem candidates T1–T10, P0/P1/P2 `revision_checklist.csv`, `review_matrix.json`.
- `referee_fortification/` — referee report (`01_referee_report_ko.md`), paste-ready R1–R12 (`02_revision_recommendations_ko.md`), theorem candidates T1–T9 (`03_theorem_candidates_ko.md`), fortification master plan (`05_fortification_plan_ko.md`), full strengthened-theorem proofs T1′/T2′/T4′/T5′/T8′/T9′/T3-lin (`06_strengthened_theorems_ko.md`), 12-experiment `numerical_experiments_SUMMARY.md` (10 PASS / 1 WARN / 1 REFUTED).
- `strengthened_publication/` — strengthen-not-tone-down plan, theorem-upgrade candidates, claim-defense matrix C1–C10, `work_packages.yaml` (WP0–WP8), `web_bibliography.md` (Saadeh 2016 etc.), Paper A/B templates.

## Consensus findings routed to v7

F1 (Ω_k signed domain), M1 (P36 strictness iff), M2 (P31 sharpness → T3-lin), M3
(estimated-covariance Hotelling/F), F2 (K5/CF4 end-to-end), M4 (MES ε
rederivation), M5 (measured-R disclosure), M6/M7 (DESI window / CF4 Malmquist),
M8 (gate-policy printing), M9 (proxy dashboard rename), M10 (literature table),
m1–m12 (minors); strengthened theorems T1′/T2′/T4′/T5′/T8′/T9′/T3-lin/T7. Machine
routing in `docs/generated/v7_external_audit_synthesis_matrix.{json,md}`.

## Caveats

- Diagnostic/proposed external inputs; not publication evidence.
- No native low-ℓ solver output or validation is present or implied.
- No Bianchi family identification; no geometry-detection wording or evidence promotion.
- Numerical experiment values quoted in the archived docs are the reviewers' own runs; the repo reimplements and re-verifies independently under v7.
