# PR07 Audit-Repair Programme — Step-by-step PR List

Source: 2026-06-25 PR04 adversarial audit (`pr07_research_repair_execution_pack`,
verdict **MAJOR_REVISIONS**). Folded into this repo per `AGENT_SKILL_MAP.md`.
Status column reflects what has landed on `research/pr04-multicomponent`.

Legend: ✅ landed · 🔜 ready/runnable · ⛔ blocked (registered blocker code) ·
🧭 separate long-term project.

## P0 — blockers and reproducibility

| PR | Title | Status | Where |
|---|---|---|---|
| PR07-001 | Unit-safe anisotropic-stress ownership | ✅ rev-r116 | `bass/background/bi_continuation/{moments,dynamics}.py`, report B-shear |
| PR07-002 | Theorem & claim repair (NT-A1/A3/B3, A-Wigner split) | ✅ rev-r116 | `docs/final_report/main.tex`, `wolfram/*.wls`, claim lint |
| PR07-003 | Independent Bianchi-I dynamics verification | ✅ rev-r116 | `bass/background/bi_continuation/verification.py`, `research_gates/pr07` |
| PR07-004 | PAPER-A proof closure (3 corollaries) | ✅ rev-r116 | `htt/htt/htt/departure/paper_a_closure.py` |
| PR07-005 | Reproducible gate surface | ✅ rev-r116 | `Makefile`, `.github/workflows/pr07-audit-repair-gates.yml` |
| PR07-006 | Measurement-report correction & quarantine | ✅ rev-r116 | report K1/K4/K5/K6 wording + `obsstat` mechanics |

**PR07-001 acceptance** (met): round-trip rel err 1.6e-16; two RHS paths agree
0.0; `dσ̇/dπ=κ`, `dσ̇/dΠ=3H²`; PR04 23/23 hold.
**PR07-002 acceptance** (met): Wolfram JSON `status=PASS` (all checks true,
xAct 1.3.0); forbidden-claim scan 0 findings; captions agree with the registry.
**PR07-003 acceptance** (met): 1000-state residuals <1e-11; DOP853/Radau exact-
dust <1e-9; RK4 convergence slope ∈ [3.6,4.4]; event guards.
**PR07-004 acceptance** (met): radial-vorticity rank 0; shell rank 3 / broad-
depth rank 6; temporal tensor rank 15; duplicate-block null-space qualified by
full column rank; boost/first-jet split. Closes the three previously
`BLOCKED_PROOF_REVIEW` corollaries.

## P1 — paper closure

| PR | Title | Status | Gate |
|---|---|---|---|
| PR07-007 | PAPER-A manuscript freeze | 🔜 after 002/004/005 + local xAct | `PAPER_EXIT_CRITERIA` |
| PR07-008 | PAPER-B manuscript freeze | 🔜 after 001/002/003/005 + dynamics review | `PAPER_EXIT_CRITERIA` |

PAPER-A headlines: local nuisance-quotient identifiability under the linear
model, radial-vorticity and single-shell no-go, temporal STF rank, boost /
first-jet split. PAPER-B headlines: scalar non-sufficiency, abstract PSD moment
cone, dimensionally consistent shear-memory identity, exact dust-FLRW oracle.
Neither claims a tilted Bianchi-I solution discovery or nonlinear stability
(Sandin–Uggla / Fournodavlos novelty boundary — see `WEB_CRAG_LEDGER.md`).

## P2 — observational lanes (delegated when data are absent)

| PR | Title | Status | Blocker |
|---|---|---|---|
| PR08-002 | K5 hierarchical bulk-flow likelihood | ✅ mechanics rev-r116 | — (release-matched mocks are PR08-003) |
| PR08-005 | Independent 2MRS cross-reconstruction contract | 🔜 contract/spec | provenance-complete comparison; no covariance merge |
| PR08-001 | K1 PR4/E2E summary pipeline | ⛔ | `BLOCKED_MISSING_PR4_E2E_ACCESS` |
| PR08-003 | K5 release-matched forward mocks | ⛔ | `BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP` |
| PR08-004 | K6 field-realization posterior | ⛔ (curl-suppression demo landed) | `BLOCKED_MISSING_FIELD_REALIZATIONS` |
| PR08-006 | Joint posterior + legacy scalar pushforward | ⛔ | after 001/003/004; fail-closed `x_C,Q,Π,F,G_F` |

PR08-002 mechanics (`obsstat/bulkflow_mle.py:fit_hierarchical_bulk`,
`hierarchical_coverage_experiment`): `y=NB+Wα+Zδ+ε`, `δ~N(0,T)`,
`ε~N(0,diag(σ_meas²+σ_star²))`; Woodbury/Schur marginalization; measurement /
mock-calibrated / cosmic-variance covariance reported separately. CoVe coverage
near nominal; selection-offset bias 15.0→1.9 km/s. PR08-003 (release-matched
mocks) and cosmic variance remain blocked.

## P3 — separate long-term low-ℓ solver (project: restricted_bianchi_i_multifluid)

| PR | Title | Status |
|---|---|---|
| PR10-001 | Convention & oracle contract | 🧭 |
| PR10-002 | FLRW perturbation comparator (vs CAMB/CLASS) | 🧭 |
| PR10-003 | Collision / TCA conservation | 🧭 |
| PR10-004 | LOS convergence surface | 🧭 |
| PR10-005 | Nearly-FLRW Bianchi-I seed | 🧭 |
| PR10-006 | Family × mode × orientation support truth matrix | 🧭 |

Exact-FLRW + transfer comparator is the first science gate; old-Rust
spectra/evidence/atlas are inadmissible substitutes; **PAPER-C/D stay blocked**
until these pass. Plus four future xAct PRs feeding PR10-001/005: (1) full 1+3
decomposition from `∇_b u_a` via xTensor; (2) Bianchi-I connection/kinematics
via xCoba cross-checked to Python; (3) xPert only after background +
perturbation parameter are registered; (4) canonical `InputForm` + hash export.

## Merge order

1. PR07-001 & PR07-005 (units, imports, gates) — ✅.
2. PR07-002/003/004 in parallel — ✅; PR07-006 after wording stabilized — ✅.
3. PR07-007/008 manuscript freezes.
4. PR08 tickets as inputs arrive; PR10 separate project.
