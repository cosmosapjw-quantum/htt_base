# Formalism Audit Originality Response Matrix

owner: COMMON
implementation_scope: formalism_audit_response_matrix
claim_tier: diagnostic_only
transfer_source: mixed_none_external_and_conditioned_legacy
sky_support_status: not_directional
null_mock_status: mixed_diagnostic_unmatched_and_not_applicable
config_hash: none_manual_REV_R063_response_matrix
input_hashes:
- `formalism_originality_program.zip`: `57c00c1f3868fe0e62270b9625d5e97386c57925363a9bfb21137d9d8348bbc9`
- `statistical_formalism_audit_report.zip`: `bdfb44061817bf01ca543356daaf3110cff70878edd14d3d4c5cc27cc4f34377`
- `AUDIT_REPORT (1).md`: `6da68d227f733049ac8664893534867db0dac0e6c9002f55b0650b84eb4e026c`
- `verify_formalism_claims.py`: `97ecdb132444f4498d3a53ede3206cdfb9ba5a02dcce2d76b19f8d9894ac93d5`
- `docs/generated/current_science_plot_payload.json`: `4cd77a839f275f54c39a73d44184179163c498747b5db8beb6c411aacb996d03`
caveats:
- This matrix is a response and scheduling artifact, not a scientific validation artifact.
- Open findings remain open or blocking until code, generated payloads, prose, and tests are changed in later REV items.
- MIO quantities remain diagnostic-only; HTT inference remains separate; scalar formalism values do not support geometry or family claims before native morphology atlas gates.
generating_command: manual apply_patch after archive extraction and archived verifier run
git_commit_or_worktree_state: `40f789da0e8b70472d6384d1f7a7b12019b50329` with untracked REV-R063 archive/matrix inputs; no commit made

## Sources Archived

| Source | Archived path | Status |
| --- | --- | --- |
| Audit report zip | `docs/audits/formalism_audit_2026-06-19/statistical_formalism_audit_report.zip` | archived |
| Audit report markdown | `docs/audits/formalism_audit_2026-06-19/statistical_formalism_audit_report/AUDIT_REPORT.md` and `docs/audits/formalism_audit_2026-06-19/AUDIT_REPORT (1).md` | archived; hashes match |
| Audit verifier | `docs/audits/formalism_audit_2026-06-19/verify_formalism_claims.py` | archived at required root path |
| Originality program zip | `docs/audits/formalism_audit_2026-06-19/formalism_originality_program.zip` | archived |
| Originality proposal docs/scripts | `docs/audits/formalism_audit_2026-06-19/formalism_originality_program/` | extracted and archived |
| Archive manifest | `docs/audits/formalism_audit_2026-06-19/ARCHIVE_MANIFEST.md` | created |

## Verification Snapshot

| Command | Exit | Result | Interpretation |
| --- | ---: | --- | --- |
| `python3 docs/audits/formalism_audit_2026-06-19/verify_formalism_claims.py docs/generated/current_science_plot_payload.json` | 0 | `cancellation trap reproduced: YES`; `semantic-split mismatch found: YES`; mismatched symbols `Pi`, `F`, `G_F`; `F` and `G_F` owner-swapped to HTT in the figure payload | Verifier executed successfully, but its findings keep the semantic split and cancellation-display issues open/blocking. |

## Finding-To-Action Matrix

| ID | Severity | Finding | Current evidence | Required action | Owner lane | Target | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | Fatal/High | Semantic split figure binds canonical `Pi`, `F`, and `G_F` to non-canonical quantities, with `F`/`G_F` owner shown as HTT instead of MIO. | Archived verifier against `docs/generated/current_science_plot_payload.json` reports mismatches for 3/5 symbols. | Relabel the bars as their actual proxy quantities or repopulate the figure from canonical production formalism objects; add a symbol/owner/definition registry linter. | COMMON/MIO/HTT boundary | REV-R064 | Open/blocking |
| A2 | Fatal/High | Direction-marginalized Bayes-factor prose uses detection-style wording. | Archived audit cites manuscript/report prose around tilt and departure diagnostics; current REV-R063 does not edit manuscript prose. | Replace with conditional diagnostic-preference language and promote the lint rule from warn to fail. | manuscript/COMMON claim guard | REV-R065 | Open/blocking |
| A3 | Medium | "98 percent accuracy" wording can be read as unsupported measurement accuracy. | Archived audit flags prior page/report wording; current REV-R063 does not edit manuscript prose. | Replace with transfer-conditional contribution-fraction wording and cite provenance. | manuscript/transfer provenance | REV-R065 | Open/blocking |
| A4 | Medium | `F` naming and legacy `*_posterior` filename exposure risk physical-occupancy or posterior interpretation. | Archived audit flags the certified filling-fraction name and `root__fig_filling_fraction_posterior`. | Define `F` as the signed projection fraction of the admissible MES-linear ceiling; retire legacy posterior-named figure filename from manuscript-facing surfaces. | MIO/manuscript | REV-R066 plus figure cleanup | Open/blocking |
| A5 | Medium | `x_C`/`F` cancellation caveat is missing from displays. | Archived verifier reproduces examples where `x_C` is zero while component magnitude is nonzero and cancellation index is 1.0. | Require signed component breakdown, absolute component total, and cancellation index next to every `x_C`/`F` display. | MIO/obsstat display | REV-R066 | Open/blocking |
| A6 | Medium | Legacy VER2 atlas/production labels can surface stale readiness claims. | Archived audit flags `atlas_available`, `atlas_ready`, and production-candidate/production-grade labels in legacy payloads. | Over-stamp legacy internal promotion fields to `legacy_not_current`; keep them quarantined as prior context only. | COMMON/legacy quarantine | later cleanup or REV-R065/R066 split | Open/blocking |
| A7 | Low | Comparator labels must appear on every `x_C`/`Q` display. | Formalism contracts carry comparator metadata; audit says display layer must show it. | Add comparator labels to every figure/table cell containing `x_C` or `Q`; enforce via display linter. | MIO/display | REV-R066 or linter follow-up | Open |
| A8 | Low | `G_F` floor reporting must be visible. | Audit notes floor stabilization can censor real gap values when a floor is applied. | Surface `floor_applied_by_bin` wherever `G_F` is reported. | MIO/display | REV-R066 | Open |

## Proposal Upgrade Matrix

| ID | Proposal item | Response action | Acceptance gate | Status |
| --- | --- | --- | --- | --- |
| U1 | Sector-resolved departure profile plus first-class cancellation reporting. | Promote component vector, absolute component total, and cancellation index to required display metadata for `x_C`/`F`. | No `x_C` or `F` display lacks component profile and cancellation index; includes a worked cancellation counterexample. | Proposed/open |
| U2 | Total-anisotropy magnitude companion to `F`. | Add unsigned magnitude companion or documented sector norm beside `F`; define `F` precisely. | Every `F` display carries companion magnitude and avoids physical-volume or posterior interpretation. | Proposed/open |
| U3 | Semantic-firewall specification plus adversarial fuzzer. | Productionize symbol registry, owner/tier rules, reserved-language checks, and figure-label linter seeded by archived verifier. | Fuzzer reports zero successful smuggles; figure-label linter passes on current figures. | Proposed/open |
| U4 | Matched-null plus depth-template discrimination for `G_F`. | Treat as a forecast/hardening path until matched calibrated nulls drive FPR below threshold. | Matched-null FPR below registered threshold and forecast language only unless gates close. | Proposed/open; blocking for stronger local/global claims |
| U5 | Comparator-multiverse reporting for `x_C`/`Q`. | Report admissible comparator spread and comparator labels as a specification-curve style diagnostic. | Comparator never implicit in `x_C`/`Q` figures or tables. | Proposed/open |

## Proposal Experiment Matrix

| ID | Experiment item | Response action | Acceptance gate | Status |
| --- | --- | --- | --- | --- |
| E1 | Cancellation null distribution. | Port or reproduce against production MIO objects after U1 scope is opened. | Quantifies cancellation-index distribution and includes a worked counterexample. | Proposed/open |
| E2 | `F` fail-closed coverage. | Extend production tests for negative `x_C`, super-ceiling, non-admissible ceiling, and no clipping. | 100 percent expected accept/reject coverage in production tests. | Proposed/open |
| E3 | `Pi` threshold-registration bias. | Add production or methods-level diagnostic showing post-hoc threshold inflation and registered-threshold protection. | Reports pre-registered versus post-hoc exceedance gap with look-elsewhere context. | Proposed/open |
| E4 | `G_F` matched-null plus boost-vs-tilt depth discriminant. | Keep as forecast until matched null/covariance support exists; no current local/global conclusion. | Matched calibration and quantitative separation report, or explicit non-discrimination result. | Proposed/open; blocking for stronger local/global language |
| E5 | Comparator multiverse for `x_C`/`Q`. | Run comparator sensitivity over admissible comparators and expose spread. | Comparator spread reported with every relevant `x_C`/`Q` summary. | Proposed/open |
| E6 | Semantic-firewall fuzz. | Port archived reference fuzzer to production guard contracts. | Zero successful reserved-language, owner, clipping, or post-hoc threshold smuggles. | Proposed/open |
| E7 | MIO-to-HTT leakage audit. | Enumerate diagnostic-to-inference interfaces and require inference constructors to reject MIO diagnostic inputs. | Zero leakage paths into evidence/posterior/model-ranking surfaces. | Proposed/open |

## Role Review Notes

| Role | Finding |
| --- | --- |
| Code mapper | REV-R063 touches archive and generated docs only; it does not modify formalism code, manuscript prose, figure generators, or payload generators. |
| Harness engineer | Required verifier is archived at `docs/audits/formalism_audit_2026-06-19/verify_formalism_claims.py`; a zero exit means the verifier ran, not that findings are fixed. |
| Physics/statistics auditor | `x_C`, `Q`, `Pi`, `F`, and `G_F` remain diagnostic-only; the open matrix does not license detection, evidence, native transfer validation, geometry, or family claims. |
| Claim-gate reviewer | All semantic split, prose, cancellation, legacy-label, comparator, and floor-reporting findings remain open or blocking until later REV patches close them with tests. |
| Regression tester | Required claim-language scan should be run on this matrix; broader figure/prose tests are intentionally deferred because no production figure/manuscript code is changed in REV-R063. |

## Residual Risks

- The archived audit verifier currently checks only cancellation and semantic-split payload semantics; it does not check manuscript detection prose, legacy labels, comparator labels, or `G_F` floor reporting.
- The originality proposal scripts are archived reference/proposal material. They are not production tests until ported to repo contracts.
- Current payload hash `4cd77a839f275f54c39a73d44184179163c498747b5db8beb6c411aacb996d03` still contains the semantic-split mismatch reported by the archived verifier.
