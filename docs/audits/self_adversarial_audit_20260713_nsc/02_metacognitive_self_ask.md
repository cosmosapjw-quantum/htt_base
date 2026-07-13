# NSC self-adversarial audit — Stage 3: METACOGNITIVE SELF-ASK

_Executed before launching lanes. Question -> honest answer -> mitigation bound into the design._

**Q1. What do I actually know vs assume about these results?**
I wrote most of the rev-r195..r198 code in prior sessions; I know the artifact chain but I am
the AUTHOR — maximal confirmation-bias exposure. Mitigation: every correctness lane is a fresh
subagent with a refute-first prompt and no access to my session history; seeded questions
include the attacks I would least like to be true (e.g. "is the WF curl no-go trivial by
construction?", "is pk_corr=(370/308)^2 circular?", "is the 2000-mock empirical floor 3.48σ just
the resolution limit?").

**Q2. Where am I most likely wrong?**
(a) Statistical shortcuts shipped under deadline: the ML fσ8 shape correction, the ±0.02 vs
±0.10 error choice, the mock p-value floors. (b) Convention/unit handling in external grids
(LVN/CORAS/Carrick loaders). (c) Claim-surface drift: retracted theorems (T2', P36) possibly
still cited somewhere live. (d) Novelty: I have NOT systematically searched 2024–2026
literature for prior CF4 fσ8 / DESI dipole / ACT κ isotropy measurements — the field may have
already published what our cards call "measured". Mitigation: 6 dedicated web-CRAG lanes.

**Q3. What CAN'T this audit see?**
Errors requiring heavy reruns (20-min mock ensembles) — lanes are capped at ~60 s snippets, so
ensemble-level bugs are only detectable via code reading + small-N reproduction. Print-only MESb
internals (rank-10 open item) stay unverifiable. The PL3/K1 lane is excluded (data in flight).

**Q4. Is the audit design itself biased?**
Risk: lanes graded "against the claimed tier" could excuse weak claims as "honest because
caveated". Counter: the significance panel + debate judges are explicitly instructed that a
caveat does not rescue a result a referee would still reject; the attacker lanes argue the
strongest case AGAINST publishability, not against honesty.

**Q5. What would count as audit failure?**
Zero P0/P1 findings across 10 correctness lanes would itself be suspicious (author-audit
leniency); so would novelty verdicts of NEW everywhere. The completeness critic is instructed
to flag exactly these degenerate outcomes.

**Q6. Sequencing sanity?**
Correctness and novelty lanes are independent -> run concurrently. Significance genuinely needs
both -> barrier. Debate needs compiled findings -> after panel. PDR last, synthesized from all
artifacts. This matches the requested loop order (CoVe -> adversarial self-ask -> web CRAG ->
CCoT are embedded per-lane; debate + PDR close).
