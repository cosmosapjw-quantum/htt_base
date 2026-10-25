# R29 independent controller candidate audit

Decision: **HOLD publication pending one bounded two-file repair**. Requested reviewer gpt-6-astra/xhigh; observed runtime UNKNOWN. Candidate source f92b06c1ab9622c9210d15f1bb7a983d3ef3e7d190b2f063b90d43c6480a539e, tests f94f7151a2326ed32bb449b0c104d8c966dea2307d3dc8e993f175e410ecc3be, HEAD d93605e66adfececa89b90681124b232a5f90220.

Three defects were reproduced in one metadata-only script under this directory:

1. **P1 — durable target split**, controller lines 2624–2632. Saving through the live topology replaces the supplied symlink; the original external target stays stale. Pin the resolved target for read/write and adjacent result sidecars; preserve the symlink chain and ordinary new-file init.
2. **P1 — exhausted ordinary transport restoration**, lines 1608–1610 and 1644–1661. `retry_prohibited=True` is discarded for ordinary packets, and exact-packet prelaunch resume succeeds. Persist and enforce the prohibition without mutating the refused state; retain temporary non-prohibited recovery.
3. **P2 — first-failure author cannot receive a repair followup**, lines 1444–1483 and 2527–2529. A structured plan is accepted by research record but rejected at ACK. A string plan still requires a nonexistent successful initial candidate. Support a narrow actual acknowledged execute/repair blocker (code/numeric, substantive true) and exact raw-receipt base with no prior candidate, preserving original author, input, route, history, accounting, independence and unknown-outcome protection. A fresh author does work, so this is a continuation defect, not total deadlock.

These defects predate the dirty additions. They are findings against actual current live use, not attribution to the new 2020 insertions. The existing dirty source must be preserved.

The exact minimal repair contract and test boundaries are in RESULT.json. Only research_controller.py and test_research_controller_frontier.py may change; no production state reinitialization, migration, scientific replay or ultra consumption is authorized by this review. A fresh independent review must decide publication of the repaired identity.

Independent copied-state append/typed-obligation checks preserved all 86 old tasks, packets, campaign and ultra records; completed without a qualified product remained blocked. Product names do not establish equivalence of scientific estimands. Keep unqualified worker descriptors as unqualified and retain the original scientific acceptance boundary.

Targeted existing metadata tests: 42 passed, 3 lifecycle-state skips, 81 subtests, 4.88 seconds. The independent reproducer tool reported 4.296046951 seconds. No old CF4/SavedLaw/Gaia historical suite replay or scientific producer ran. No production bytes changed in the independent copy check. Green tests did not cover the three reproduced failures.

Files: REPRO_RESULTS.json contains raw observations; reproduce_metadata.py is the one executed reproducer; TARGETED_TESTS.log retains test output. This audit read no prior controller verdict and used no repository harness/skill as a correctness oracle.
