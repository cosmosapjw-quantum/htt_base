# v7 External Audit Synthesis Matrix

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
config_hash: `sha256:f78e1784742140a8dc21f95bbc8a93d1bf2d34438796809d309bc65bd8700d3c`
generating_command: `venv/bin/python scripts/build_v7_external_audit_synthesis.py`

## Zip Inputs

| Zip | SHA256 | Members | Integrity |
| --- | --- | ---: | --- |
| `htt_v6_strengthened_publication_bundle.zip` | `sha256:43ff42a3176ccf8cd562a4a9a039382fe9ea60c922416e5697726f2a06d2a237` | 26 | `PASS` |
| `htt_v6_critical_review_bundle.zip` | `sha256:5fa351f7250cec810003ae0aa4e00127802ec56b3fe70938554cb7de541ac9f4` | 17 | `PASS` |
| `htt_v6_referee_package_20260709.zip` | `sha256:dd7f5f842db170ef0110a1e89c4c009acfabb892fb145c92eb771e8fc5dabffa` | 34 | `PASS` |
| `htt_v6_referee_fortification_package_v2.zip` | `sha256:86586d44d3bf0143ad59f9e00eef6f2afa5fe2dc02a44a8860d77fa19822bbe4` | 56 | `PASS` |

## Findings

| ID | Severity | Response | Target |
| --- | --- | --- | --- |
| F1 | `fatal_if_unfixed` | Use signed component boxes and publish open/all curvature branch intervals. | `htt/obsstat/egs3_identified_set.py` |
| F2 | `fatal_if_unfixed` | PR-120 quarantines the K5/CF4 numerical card and every downstream consumer; no replacement result is supplied. | `docs/generated/cf4_p0_quarantine_block.json` |
| F3 | `major_revision` | Keep generated audit cards separate from Paper A theorem-witness-result prose. | `docs/generated/v7_external_audit_synthesis_matrix.md` |
| M1 | `major` | Add strict/equality classifier and counterexample witness. | `htt/obsstat/egs3_gf_interval.py` |
| M2 | `major` | Label current result as component-box sharpness; defer full realization. | `Paper A text` |
| M3 | `major` | Add estimated_covariance_f threshold policy with n_sim fail-closed validation. | `htt/obsstat/egs3_identified_set.py` |
| M4 | `major` | Keep rederived_here=false and block promotion of MES-dependent K5 placeholders. | `docs/generated/parent_identity_seal.json` |
| M5 | `major` | Use K5 card as closure diagnostic only; schedule measured R table/SVD card. | `future_v7_R_card` |
| M6_M7 | `major` | Keep these as diagnostic figures until matched masks/randoms/corrections are bound. | `report_data_analysis_current` |
| M8_m11 | `minor_to_major_if_untracked` | Record deterministic G1-G5 gate policy witness in v7 fortification artifact. | `scripts/run_v7_fortification_witnesses.py` |
| M9 | `major` | Split proxy dashboard from any future measured g-coordinate card. | `future_v7_R_card` |

## v7 Work Packages

| ID | Title | Acceptance |
| --- | --- | --- |
| V7-001 | Signed identified-set and threshold policy hardening | EGS3 contract tests pass and generated witnesses are current. |
| V7-002 | K5/CF4 diagnostic closure card | real CF4 bulk is used; plugin firewall blocks observational promotion. |
| V7-003 | Paper A prose and theorem-lane cleanup | claim-language and report-lane tests pass. |
| V7-BLOCKED | Deferred promotion blockers | tracked as blocked/deferred, not silently promoted. |

## Caveats

- Synthesis of external review inputs; not a scientific result.
- External code is not imported as production implementation.
- All v7 public claims remain diagnostic-only or blocked until their gates pass.
