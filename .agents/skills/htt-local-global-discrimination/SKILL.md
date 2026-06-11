---
name: htt-local-global-discrimination
description: Use when implementing local boost, global tilt candidate, depth-gap, response-overlap, null competition, PPC/LOOCV, or HTT mixture models.
---

# htt-local-global-discrimination


Start with rank/response overlap before posterior. A rank-deficient response yields no-claim. Local boost, global tilt, Bianchi/background, and survey/systematic blocks must remain distinct. Matched nulls and FPR must exist before strong claims.


## Required output when invoked

Return:

- evidence read,
- proposed changes,
- tests to run,
- risks and kill-switches,
- artifacts/status updates needed.
