# H02 actual upstream TF contributors and selection composition

Acquired the fixed official CDS J/ApJ/902/145 ReadMe and both compressed source
tables, retaining the direct `.dat` HTTP404 failures and successful `.dat.gz`
receipts. Raw galaxy rows stay outside Git. Executed actual PGC→CF4 galaxy→group→
35,970 selected-group joins, quality/band overlap and the inherited correlated
depth-window working-weight composition; previous fits were reused, not repeated.

The 10,737-row measurement and 9,792-row distance releases are not nested:
947/2 one-sided identities and eleven blank distances are explicitly retained.
7,573 finite-distance galaxies map to 6,697 selected groups. Their working-weight
support is 24.815% overall, 49.644% at z=.025 and .288% at z=.080. This is not a
selection probability, calibration influence or proof of unchanged ingestion.
Band/group overlaps and missing method counts are preserved.

Code, ten tests, actual aggregate results, PNG/PDF, report, raw first failures and
source/run receipts are in `CONTINUATION_20261018/H02_UPSTREAM_SELECTION_20261018/`.
Author and parent: ten tests PASS. Fresh independent reviewer: all source joins,
quality/overlap/count/quantile fields and 150 window metrics reproduced; nine
nonwriting tests plus independent SHA-tamper falsifier PASS; PNG inspected.
No blocking finding or repair. See `INDEPENDENT_REVIEW_NATIVE_H02_UPSTREAM_20261018.md`.

Parent's first DAG-test invocation used nonexistent top-level test paths and
returned pytest exit4, no tests run. The correct existing targets are
`tests/obsstat/test_htt_publication_dag.py` and
`tests/htt/test_sixpaper_goal_execution.py`; the initial path error is not a
scientific/test failure and is not counted as validation. Running those correct
targets returned **7 FAILED, 11 PASSED**. Six legacy tests still assert the
original four-anchor/nine-ready snapshot (including a cycle test intercepted
earlier by the unfinished-prerequisite guard); one continuation test calls the
live DAG a frozen fourteen-anchor snapshot. Live progress is now sixteen, with
V02 ready. These failures are preserved, not silently fixed or counted as PASS:
`test_actual_six_paper_program_unique_and_acyclic`,
`test_ready_is_actual_dependency_scoped_not_priority_confusion`,
`test_blocked_input_does_not_block_independent_study`,
`test_task_packet_exact_task_and_provenance_limits`,
`test_dag_export_derived_is_hash_stable_and_non_scheduling`,
`test_dependency_cycle_refused`, and
`DecisionTests.test_historical_snapshot_remains_fourteen`.
The DAG's own validation/export succeeds; no acceptance, dependency, validator or
historical snapshot was weakened to satisfy these stale snapshot assertions.
Whitespace checking reports one trailing blank line at the reviewed report's
EOF; it is retained to preserve the reviewed source/receipt byte binding.

Original H02 remains HOLD: true selection, shared calibration/velocity covariance,
independent angular anchor and source-null pipeline are not supplied by these
tables. Original acceptances/dependencies and 16/42 completed count are unchanged;
all six papers remain NOT_READY_TO_SUBMIT. Requested implementation/review models
were gpt-6.1-sol/high and gpt-6-astra/xhigh; observed identities UNKNOWN.
No physical likelihood/admission, solver/ODE, main merge or journal submission.
