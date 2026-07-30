# PR-269 formal boundary

This directory records the formalization boundary for the analytic/core
Pillar-T slice.

- The exact typed statements and analytic derivations live in
  `docs/research_program/vector_tensor/proofs/PR269_PILLAR_T_CORE.md`.
- The machine-readable records live in
  `docs/research_program/vector_tensor/proofs/PILLAR_T_CORE_PROOFS_V1.yaml`.
- The executable boundary witnesses live in
  `htt/src/common/pillar_t_core_proofs.py`.

No Lean or CAS artifact is manufactured for definition expansion, determinant
bookkeeping, the chain rule, or elementary convex-gauge identities. Statements
whose registered proof mode requires four independent axes remain unadjudicated
until PR-270 and are not represented as PR-269 proof records.

The proof-author verdicts in this slice remain non-renderable until canonical
PR-269 completion and a valid frozen independent-review receipt.
