---
name: htt-adversarial-review-loop
description: Use for every substantial PR before commit, especially after implementation and tests.
---

# htt-adversarial-review-loop


Review from five independent angles: correctness, regressions, test adequacy, scientific/claim hygiene, maintainability. Lead with concrete findings. Distinguish must-fix from follow-up. Fix real findings before commit; document accepted residual risks.


## Required output when invoked

Return:

- evidence read,
- proposed changes,
- tests to run,
- risks and kill-switches,
- artifacts/status updates needed.
