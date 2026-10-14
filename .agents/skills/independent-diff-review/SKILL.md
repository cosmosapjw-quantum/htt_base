---
name: independent-diff-review
description: Review a research-code diff independently for correctness, scientific inconsistency, numerical instability, regression, missing tests, hidden scope expansion, and reproducibility gaps.
---


# Independent Diff Review
For `htt_base`, follow `AGENTS.md` and the selected task contract. Use applicable existing records; create a new artifact only when a consuming decision requires it. Preserve frozen and historical evidence. A skill verdict does not promote scientific admission beyond the applicable project gate.


1. Read the task contract, scientific contract, validation matrix, tests, and diff.
2. Prioritize blocking correctness/science/numerics issues over style.
3. Give each finding severity, file/location, impact, evidence or reproduction, and recommended fix.
4. If no findings, state residual risks and untested areas.
5. Do not implement unless explicitly asked; preserve reviewer independence.
