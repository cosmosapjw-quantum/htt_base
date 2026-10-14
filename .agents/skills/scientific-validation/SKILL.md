---
name: scientific-validation
description: Review research-code changes for physics and mathematics correctness, including dimensions, signs, symmetry, conservation, limits, boundaries, positivity, approximation order, and regime of validity.
---


# Scientific Validation
For `htt_base`, follow `AGENTS.md` and the selected task contract. Use applicable existing records; create a new artifact only when a consuming decision requires it. Preserve frozen and historical evidence. A skill verdict does not promote scientific admission beyond the applicable project gate.


1. Act independently from the implementer.
2. Read the scientific contract and diff.
3. Check only applicable invariants and reference cases.
4. Record each `PASS`, `CONCERN`, `FAIL`, `NOT_APPLICABLE`, or `NOT_TESTED` with evidence.
5. Block promotion on FAIL and propose the smallest repair or missing test.
6. Update an applicable existing `VALIDATION_MATRIX.md`, or return the results to the task owner.
