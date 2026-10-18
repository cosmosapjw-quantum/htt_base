# Scoped independent review: native CF4 continuation

Decision: `SCOPED_REVIEW_PASS` for the S02/H02 conditional research increment.
Reviewer `/root/native_science_review` did not author the reviewed files and
worked read-only in a fresh bounded context. Requested model/effort:
`gpt-6-astra/xhigh`; observed runtime: `UNKNOWN`. Implementers requested
`gpt-6.1-sol/high`; observed runtime: `UNKNOWN`. Parent performed the prescribed
metadata repair and integration.

Baseline branch `research/htt-sixpaper-goals-robustness-20261018`, HEAD
`1e095a2749cce9b28e45aac043a82218c21f84e5`, draft PR #560. Reviewed scope:
`S02_EXECUTION_20261018/` and `H02_EXECUTION_20261018/` beside this file. L01/L02
are separate ongoing units and are not approved by this decision.

## Independent evidence

- S02: 12/12 tests passed, including independent LP extrema comparisons,
  positivity/domain failures, same-measure preservation and all 2048 coupled
  witnesses. The generalized eigenvalue extrema and directed-cycle minimax
  are sound under the stated fitted-field calibration class. Physical unknown
  mass remains one; no common-congruence mapping was supplied.
- H02: 13/13 tests passed. Independent full-intercept SVD reproduced all 20
  actual-source fit blocks with maximum coefficient difference 1.64e-14 mag
  and covariance difference 5.20e-17 mag². Nonbinary-kernel covariance,
  overlapping windows, 160-comparison union bound and shared-window calibration
  LP preserve the stated dependence and assumptions.
- Figures and reports were inspected; they retain working-law, source-selection
  and common-calibration limitations. Released-distance heldout diagnostics are
  correctly not presented as independent upstream calibration validation.

## One finding and its closeout

The initial S02 label `raw_cf4_source_sha256` and phrase "upstream raw SHA"
incorrectly described the selected-row NPZ identity as a raw CDS-table identity.
Code/report/generated JSON now identify it as `selected_cf4_source_npz_sha256`.
The reviewer verified that reversing only these metadata substitutions recovers
the originally reviewed bytes. Numerical arrays and values did not change.
Parent reran 12 S02 and 13 H02 tests successfully. No unresolved finding blocks
publication of this scoped increment.

Final SHA256 identities verified by the reviewer:

| File relative to this directory | SHA256 |
|---|---|
| S02_EXECUTION_20261018/calibration_obstruction.py | 5576e7230f70f534eefbca4eb8ad4aea4d79475c0d15f6dfb2a186650ad04e32 |
| S02_EXECUTION_20261018/REPORT_KO.md | 6e5fb100ac72aa2d21de1683ab3fddf556ee12975b90376fc3a5b4a181e92984 |
| S02_EXECUTION_20261018/results/S02_CALIBRATION_OBSTRUCTION.json | 6904b7ccadb5edbde0af2ace7283517dcc9d862003190b46b9f12bf27a598ae1 |
| H02_EXECUTION_20261018/h02_actual.py | 0575f37de540ae875edaf4e050ecb3360230e8b5a3c6fa7bcf9f07d72b02f1c5 |
| H02_EXECUTION_20261018/results/h02_actual_centers.json | c3f70ae28c860d3aa0276df17afc56db9f29586b0d329b773c27d01890ae7ac3 |

Original S02/H02 acceptance remains unmet. S02 needs source-qualified physical
response/finite-redshift/calibration information; H02 needs an empirical selected
law, shared calibration/velocity law and source null simulation reproduction.
Dependencies and acceptance criteria remain unchanged. This review approves
conditional research publication, not canonical node completion, manuscript
readiness, whole-repository CI, physical admission, main merge or submission.
