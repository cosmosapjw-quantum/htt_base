# Formalism Audit Originality Response Matrix

owner: COMMON
implementation_scope: formalism_audit_response_matrix
claim_tier: diagnostic_only
transfer_source: mixed_none_external_and_conditioned_legacy
sky_support_status: not_directional
null_mock_status: mixed_diagnostic_unmatched_and_not_applicable
config_hash: none_manual_REV_R068_response_matrix_update
input_hashes:
- `formalism_originality_program.zip`: `57c00c1f3868fe0e62270b9625d5e97386c57925363a9bfb21137d9d8348bbc9`
- `statistical_formalism_audit_report.zip`: `bdfb44061817bf01ca543356daaf3110cff70878edd14d3d4c5cc27cc4f34377`
- `AUDIT_REPORT (1).md`: `6da68d227f733049ac8664893534867db0dac0e6c9002f55b0650b84eb4e026c`
- `verify_formalism_claims.py`: `97ecdb132444f4498d3a53ede3206cdfb9ba5a02dcce2d76b19f8d9894ac93d5`
- `docs/generated/current_science_plot_payload.json`: `678a4a2c551de924b21ef32496bffca3fecc4b090a108642bcbc0c953b3c852c`
caveats:
- This matrix is a response and scheduling artifact, not a scientific validation artifact.
- Open findings remain open or blocking until code, generated payloads, prose, and tests are changed in later REV items; resolved rows are diagnostic-only implementation evidence, not validation evidence.
- MIO quantities remain diagnostic-only; HTT inference remains separate; scalar formalism values do not support geometry or family claims before native morphology atlas gates.
generating_command: manual REV-R068 update after payload regeneration, formalism label verification, claim-language scan, and audit-package regeneration
git_commit_or_worktree_state: `8706cdd+dirty` before REV-R068 commit

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
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/verify_formalism_figure_labels.py docs/generated/current_science_plot_payload.json` | 0 | current production linter passes canonical row ownership/definition, `x/Q` comparator display metadata, Q-summary dereferencing, `Q-spread` specification-curve metadata, `x/F` cancellation-display metadata, and noncanonical `Pi` policy-contract metadata requirements | Production gate for current generated payload passes after REV-R068. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python docs/audits/formalism_audit_2026-06-19/verify_formalism_claims.py docs/generated/current_science_plot_payload.json` | 0 | `cancellation trap reproduced: YES`; archived script still reports `Pi`, `F`, `G_F` absent from semantic split | Archived verifier policy expects all five canonical symbols. Current figure intentionally relabels proxy lanes and keeps canonical `Pi/F/G_F` absent until production formal rows are plotted. |

## Finding-To-Action Matrix

| ID | Severity | Finding | Current evidence | Required action | Owner lane | Target | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | Fatal/High | Semantic split figure binds canonical `Pi`, `F`, and `G_F` to non-canonical quantities, with `F`/`G_F` owner shown as HTT instead of MIO. | Current production linter passes after proxy relabeling; semantic split shows canonical `x/Q`, noncanonical `Q-spread`, `1-FPR`, and `G-envelope`; `Pi_policy_display_contract` is a noncanonical side summary, not a plotted Pi result; archived verifier still flags absent `Pi/F/G_F` by design. | Keep proxy lanes relabeled unless repopulated from canonical production formalism objects; do not claim formal `Pi/F/G_F` bars from current proxy rows. | COMMON/MIO/HTT boundary | REV-R064/REV-R068 | Implemented/test-covered for misbinding; canonical `Pi/F/G_F` result rows remain future work |
| A2 | Fatal/High | Direction-marginalized Bayes-factor prose uses detection-style wording. | Archived audit cites manuscript/report prose around tilt and departure diagnostics; current REV-R063 does not edit manuscript prose. | Replace with conditional diagnostic-preference language and promote the lint rule from warn to fail. | manuscript/COMMON claim guard | REV-R065 | Open/blocking |
| A3 | Medium | "98 percent accuracy" wording can be read as unsupported measurement accuracy. | Archived audit flags prior page/report wording; current REV-R063 does not edit manuscript prose. | Replace with transfer-conditional contribution-fraction wording and cite provenance. | manuscript/transfer provenance | REV-R065 | Open/blocking |
| A4 | Medium | `F` naming and legacy `*_posterior` filename exposure risk physical-occupancy or posterior interpretation. | Archived audit flags the certified filling-fraction name and `root__fig_filling_fraction_posterior`. | Define `F` as the signed projection fraction of the admissible MES-linear ceiling; retire legacy posterior-named figure filename from manuscript-facing surfaces. | MIO/manuscript | REV-R066 plus figure cleanup | Open/blocking |
| A5 | Medium | `x_C`/`F` cancellation caveat is missing from displays. | Current payload carries `departure_display_contract`, `cancellation_counterexample`, and `x` row sector/cancellation/M display metadata. | Keep signed component breakdown, absolute component total, and cancellation index required next to every `x_C`/`F` display. | MIO/obsstat display | REV-R066 | Implemented/test-covered for current displays; future canonical `F` rows must satisfy the same contract |
| A6 | Medium | Legacy VER2 atlas/production labels can surface stale readiness claims. | Archived audit flags `atlas_available`, `atlas_ready`, and production-candidate/production-grade labels in legacy payloads. | Over-stamp legacy internal promotion fields to `legacy_not_current`; keep them quarantined as prior context only. | COMMON/legacy quarantine | later cleanup or REV-R065/R066 split | Open/blocking |
| A7 | Low | Comparator labels must appear on every `x_C`/`Q` display. | `NormalizedScore.display_metadata`, `ComparatorMultiverseSummary`, current payload `x/Q` rows, and `scripts/verify_formalism_figure_labels.py` require comparator/frame/units plus Q multiverse metadata. | Keep comparator labels mandatory for every displayed `x_C`/`Q`; keep spread language restricted to specification-curve sensitivity. | MIO/display | REV-R068 | Implemented/test-covered |
| A8 | Low | `G_F` floor reporting must be visible. | Audit notes floor stabilization can censor real gap values when a floor is applied. | Surface `floor_applied_by_bin` wherever `G_F` is reported. | MIO/display | REV-R066 | Open |

## Proposal Upgrade Matrix

| ID | Proposal item | Response action | Acceptance gate | Status |
| --- | --- | --- | --- | --- |
| U1 | Sector-resolved departure profile plus first-class cancellation reporting. | Promote component vector, absolute component total, and cancellation index to required display metadata for `x_C`/`F`. | No `x_C` or `F` display lacks component profile and cancellation index; includes a worked cancellation counterexample. | Proposed/open |
| U2 | Total-anisotropy magnitude companion to `F`. | Add unsigned magnitude companion or documented sector norm beside `F`; define `F` precisely. | Every `F` display carries companion magnitude and avoids physical-volume or posterior interpretation. | Proposed/open |
| U3 | Semantic-firewall specification plus adversarial fuzzer. | Productionized deterministic hostile matrix in `scripts/generate_semantic_firewall_fuzz_report.py`; it exercises reserved-language checks, the figure-label linter, Q/Pi/F/G_F constructors, transfer provenance gates, rank/covariance blockers, and MIO-to-HTT guards. | `docs/generated/semantic_firewall_fuzz_report.md` reports 15/15 blocked cases, zero smuggles, and zero leakage paths; current figures remain covered by `scripts/verify_formalism_figure_labels.py`. | Implemented/test-covered in REV-R067; remains diagnostic-only firewall coverage |
| U4 | Matched-null plus depth-template discrimination for `G_F`. | Treat as a forecast/hardening path until matched calibrated nulls drive FPR below threshold. | Matched-null FPR below registered threshold and forecast language only unless gates close. | Proposed/open; blocking for stronger local/global claims |
| U5 | Comparator-multiverse reporting for `x_C`/`Q`. | Added `ComparatorMultiverseSummary`, generated current-code comparator-conditioned samples, displayed Q baseline/spread metadata, removed schema-only atlas numeric consumption, and enforced comparator fields plus summary dereferencing in the label linter. | Comparator never implicit in `x_C`/`Q` figures or tables. | Implemented/test-covered in REV-R068; diagnostic-only specification-curve sensitivity |

## Proposal Experiment Matrix

| ID | Experiment item | Response action | Acceptance gate | Status |
| --- | --- | --- | --- | --- |
| E1 | Cancellation null distribution. | Port or reproduce against production MIO objects after U1 scope is opened. | Quantifies cancellation-index distribution and includes a worked counterexample. | Proposed/open |
| E2 | `F` fail-closed coverage. | Extended the production fuzzer to cover negative `x_C`, super-ceiling, non-admissible external ceiling, non-admissible observational ceiling, and no clipping. | `tests/contracts/test_semantic_firewall_fuzz.py` and `docs/generated/semantic_firewall_fuzz_report.md` show expected refusal for all covered `F` hostile cases. | Implemented/test-covered in REV-R067; broader numeric stress grids remain optional |
| E3 | `Pi` threshold-registration bias. | Added production guard coverage for selected-threshold smuggling and post-hoc threshold selection; REV-R068 adds noncanonical `Pi_policy_display_contract` metadata for measure kind, threshold policy, registration status, raw calibration status, and look-elsewhere trials. | Guard coverage and display metadata are present; a separate quantitative bias experiment is still a future analysis item. | Partially implemented in REV-R067/R068; experiment remains open |
| E4 | `G_F` matched-null plus boost-vs-tilt depth discriminant. | Keep as forecast until matched null/covariance support exists; no current local/global conclusion. | Matched calibration and quantitative separation report, or explicit non-discrimination result. | Proposed/open; blocking for stronger local/global language |
| E5 | Comparator multiverse for `x_C`/`Q`. | Current payload reports three explicit current-code Q comparator-conditioned samples, baseline Q, absolute/relative spread, source hashes, comparator-axis metadata, and display metadata. | Comparator spread reported with every relevant `x_C`/`Q` summary. | Implemented/test-covered in REV-R068; not statistical uncertainty |
| E6 | Semantic-firewall fuzz. | Ported archived reference taxonomy to production guard contracts and emitted manifest-backed JSON/Markdown coverage artifacts. | `semantic_firewall_fuzz_report` records 15 hostile production-boundary cases, all blocked. | Implemented/test-covered in REV-R067 |
| E7 | MIO-to-HTT leakage audit. | Enumerated likelihood and posterior-pushforward ingress points and required production guards to reject MIO diagnostic-shaped inputs. | Fuzzer reports zero MIO-to-HTT leakage paths; existing `tests/contracts/test_mio_htt_no_merge.py` and `tests/htt/test_posterior_pushforward.py` remain in the regression slice. | Implemented/test-covered in REV-R067 |

## Role Review Notes

| Role | Finding |
| --- | --- |
| Code mapper | REV-R063 touches archive and generated docs only; it does not modify formalism code, manuscript prose, figure generators, or payload generators. |
| Harness engineer | Required verifier is archived at `docs/audits/formalism_audit_2026-06-19/verify_formalism_claims.py`; a zero exit means the verifier ran, not that findings are fixed. |
| Physics/statistics auditor | `x_C`, `Q`, `Pi`, `F`, and `G_F` remain diagnostic-only; the open matrix does not license detection, evidence, native transfer validation, geometry, or family claims. |
| Claim-gate reviewer | Comparator and cancellation display gates are now implemented/test-covered; legacy-label, `G_F` floor reporting, and stronger canonical `Pi/F/G_F` result displays remain blocked until their own evidence gates close. |
| Regression tester | Required claim-language scan should be run on this matrix; broader figure/prose tests are intentionally deferred because no production figure/manuscript code is changed in REV-R063. |

## Residual Risks

- The archived audit verifier currently checks only cancellation and an all-canonical semantic split policy; production current-payload gating is now handled by `scripts/verify_formalism_figure_labels.py`.
- The originality proposal scripts are archived reference/proposal material. They are not production tests until ported to repo contracts.
- Current payload hash `678a4a2c551de924b21ef32496bffca3fecc4b090a108642bcbc0c953b3c852c` passes the production label verifier; the archived verifier still reports absent `Pi/F/G_F` because current proxy rows are intentionally not relabeled as canonical formal rows.
