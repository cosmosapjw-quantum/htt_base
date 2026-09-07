# Canonical source pointers

This handoff deliberately points to immutable Git objects instead of copying large source/report artifacts.

```yaml
active_master:
  pr: 463
  commit: 0e2d6e3a890ae44303440e8534fb6080d1dac881
  path: docs/research_program/referee_seeded_20260907/00_MASTER_PLAN_KO.md
active_dag:
  pr: 463
  commit: 0e2d6e3a890ae44303440e8534fb6080d1dac881
  path: docs/research_program/referee_seeded_20260907/03_PROGRAM_DAG.yaml
postreview_theory:
  pr: 462
  commit: b4d04e62d664997eb9e1858b6195c35e4ece3378
  path: docs/research_program/post_review_20260907/THEORY_RESULTS.md
implementation_contract:
  pr: 462
  commit: b4d04e62d664997eb9e1858b6195c35e4ece3378
  path: docs/research_program/post_review_20260907/IMPLEMENTATION_CONTRACT.md
source_data_addendum:
  pr: 464
  commit: fa86d940f6d954af554bae5b577d5eb465aa2ae1
  path: docs/research_program/review_seeded_20260907/REUSE_AND_DATA_MAP.md
accepted_pedagogical_report:
  pr: 461
  commit: 9c86759f4ac7054d01d88689290a658e8ffd5863
  path: artifacts/research_reports/pedagogical_render_20260907_r1/
accepted_r3_report:
  pr: 459
  commit: d8894f1c526bdc5c8ebbb295ad91a0d92a4c8deb
  path: artifacts/research_reports/report_a_r3_render_20260907_r1/
default_code:
  branch: research/pr04-multicomponent
  commit: 50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb
exact_decoder:
  commit: 9f7d06dec0fce1c3a8a53fa5372c84d9c679c037
  path: htt/src/common/mes_krylov_completion.py
exact_boost_donor:
  commit: 29427a1f7f2c5d46e43ffe03053c4ac13e969228
processed_response_donor:
  commit: de73549c16ac6ceb63f924c86611e0a5ceb4711d
```

Do not merge whole donor branches merely to obtain one component. Resolve the exact file/import closure after `THEORY_FREEZE`.
