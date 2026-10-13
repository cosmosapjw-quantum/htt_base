---
name: htt-adversarial-review-loop
description: Use when reviewing a substantial htt_base change before merge or when a concrete review finding needs closeout.
---

# htt-adversarial-review-loop

Read the candidate diff, scope, scientific contract and frozen tests in fresh
context. Do not read another review verdict first. Review correctness, regression,
test adequacy, claim hygiene and maintainability with one reviewer, not five
redundant agents. Use a separate native reviewer with explicit supported model
and high/maximum effort in fresh context. Observe actual author/reviewer settings
from matching session/turn metadata; requested settings and self-descriptions are
not observed runtime. Follow the current owner-directed procedure in
`docs/harness/CURRENT_CODEX_RUNTIME.md`; do not require removed CUH-G registration.
Actual system/developer or managed restrictions still apply.

Report actionable findings with paths, consequences and a minimal falsifier.
Separate current blockers from adjacent follow-up. Permit one targeted repair
closeout. Missing scientific inputs stay HOLD; runtime or packaging repair is not
claim admission. A clean review proceeds to authorized merge/install, without a
new review ladder. Preserve prior failed reviews as historical evidence.
