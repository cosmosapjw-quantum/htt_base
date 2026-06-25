# PR07-007 / PR07-008 — Paper Freeze Exit Notes

Both freezes gate on `docs/research_program/pr04/PAPER_EXIT_CRITERIA.md`. They
need no observational detection and no low-ℓ solver.

## PR07-007 — PAPER-A manuscript freeze (after PR07-002/004/005 + local xAct)

Required content: explicit theorem hypotheses (lapse, congruence normalization,
connection, Λ, time domain); equality/null branches (the duplicate-block
full-column-rank qualifier); survey-window rank diagnostics (data rank reported
separately from prior-conditioned rank); numerical-tolerance analysis; and the
counterexamples (radial-vorticity no-go, single-shell degeneracy, first-jet).
Freeze gates:
- `make paper-a-gates` green (PR04 identifiability/congruence + PR07 PAPER-A);
- `make pr07-wolfram` PASS on the local Wolfram/xAct host (all checks true);
- `pdf_claim_lint` 0 failed; no Wigner-angle / EGS-identity leakage.

## PR07-008 — PAPER-B manuscript freeze (after PR07-001/002/003/005 + dynamics review)

Headlines: scalar non-sufficiency, abstract PSD moment cone, the dimensionally
consistent shear-memory identity `σ̇=STF(−3Hσ+κπ)=STF(−3Hσ+3H²Π)`, the exact
dust-FLRW oracle, and the temporal observability theorem. Do **not** claim
discovery of tilted Bianchi-I solutions or new nonlinear stability
(Sandin–Uggla / Fournodavlos novelty boundary, `WEB_CRAG_LEDGER.md`). Freeze gates:
- `make paper-b-gates` green (PR04 Bianchi/pushforward + PR07 units/conservation/
  integrators);
- independent dynamics reviewer sign-off (the chain-rule verifier is independent
  of the production RHS);
- `make pr07-wolfram` PASS; `pdf_claim_lint` 0 failed.

Both remain `planned` in `pr_registry.yaml` until their gate bundles are
re-run green at freeze time.
