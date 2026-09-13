# VALIDATION_MATRIX.md

Project template: all blank evidence is unevaluated. `tools/validate_harness.py` does not execute this matrix.

| Requirement | Check / independent oracle | Level | Expected / regime | Status | Source / command / actual result |
|---|---|---|---|---|---|
| requested observable | targeted acceptance | implementation | contract | NOT_EVALUATED | |
| preserved behavior | affected regression | implementation | baseline semantics | NOT_EVALUATED | |
| equation → algorithm | independent derivation/code trace | theory/math | stated assumptions | NOT_EVALUATED | |
| dimensions / signs | exact or symbolic check | scientific | contract conventions | NOT_EVALUATED | |
| invariant / known limit | independent toy/reference | scientific | predeclared tolerance | NOT_EVALUATED | |
| approximation / closure | consistency / order / regime | scientific | contract | NOT_EVALUATED | |
| discretization | resolution / timestep sweep | numerical | expected order | NOT_EVALUATED | |
| floating point | precision / conditioning check | numerical | roundoff separated | NOT_EVALUATED | |
| JVP / derivatives | independent direction and step sweep | numerical | error window / primal preserved | NOT_EVALUATED | |
| inference / sampling | model / seed / ensemble / uncertainty | statistical | stated error budget | NOT_EVALUATED | |
| execution fidelity | source / env / exit / stdout / stderr | operational | actual evidence | NOT_EVALUATED | |
| authority | selected source / authorization provenance | provenance | independent of self-attestation | NOT_EVALUATED | |
| important diff | independent reviewer | review | no unresolved blocking finding | NOT_EVALUATED | |

Status: `PASS / CONCERN / FAIL / NOT_EVALUATED / NOT_APPLICABLE / BLOCKED`. Record why any check is not applicable. Required unevaluated checks cannot be silently dropped. Only add checks to resolve a concrete remaining risk or satisfy a required gate; stop optional checks once sufficient evidence is obtained.
