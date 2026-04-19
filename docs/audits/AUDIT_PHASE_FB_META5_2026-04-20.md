# AUDIT_PHASE_FB_META5_2026-04-20

**Banner**: META pre-flight — no physics; 3-channel verification + local-only skeleton plants

## Pre-flight scan

- Required reading completed for:
  `docs/lowell_bianchi/extended_coverage/PROJECT_MEMORY_EXPLICIT.md`,
  `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-5`,
  `docs/lowell_bianchi/extended_coverage/SELF_AUDIT_AUTOMATION.md`,
  `docs/audits/AUDIT_PROMPT.md`,
  `htt/bass/hierarchy/nabla_dispatch.py`,
  `htt/bass/hierarchy/boost_kernel.py`,
  `htt/bass/background/bianchi_types.py`,
  and the prompt-supplied Lowell solver reference anchor.
- Required-reading exception recorded: the named on-disk path
  `docs/lowell_bianchi/lowell_bianchi_solver_reference.md §13` does
  not exist in this worktree, matching the prior META-4 audit drift.
- Regression gate executed exactly as requested:
  `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
  → `3403 passed, 4 skipped`.
- Source-of-work rule pinned for this phase: `htt/` may receive local
  skeleton plants but must never be staged; committed artifacts are the
  audit, development log, and `NEXT_SESSION_PROMPT.md` only.

## §FB-5.1

### §FB-5.1 — harmonic-mode decomposition + complex-dtype ``nabla`` wire-up skeleton
**Channel A**: 6 checked / 5 verified / 1 broken. Details: verified `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-5` names per-type harmonic decomposition and complex-dtype dispatch wire-up as the first perturbation rotation; verified `htt/bass/hierarchy/nabla_dispatch.py` already exposes the complex-valued `HarmonicMode` + `make_nabla_tilde` SSOT and explicitly defers off-axis subsets to `FB-5.2`; verified `htt/bass/hierarchy/boost_kernel.py` reserves the off-axis Wigner-d lift for `FB-5.2`; verified `htt/bass/hierarchy/ic.py` keeps perturbative IC seeding deferred to FB-5.3 so FB-5.1 should not reopen the IC surface; verified `docs/audits/AUDIT_PHASE_FB2_2026-04-19.md` carries the complex-dtype driver wire-up forward to `FB-5.1`. Broken: the prompt-supplied `docs/lowell_bianchi/lowell_bianchi_solver_reference.md §13.1` path is absent on disk in this worktree.
**Channel B**: 2 arXiv checks / 1 verified / 1 broken. Evidence: prompt-supplied `astro-ph/0607373` resolves on arXiv to an unrelated recombination-lines paper, so that citation is rejected for FB-5.1. The relevant Pontzen-Challinor Bianchi hierarchy paper is `arXiv:0706.2075` (`"We derive the CMB radiative transfer equation in the form of a multipole hierarchy"`), which is the corrected external anchor for the VII_h spiral-mode context.
**Channel C** (prose, 6-10 lines): The safest FB-5.1 contract is a context builder that wraps the existing `HarmonicMode` descriptor instead of mutating `hierarchy_rhs_photon` directly. The reason is structural: FB-2 already sealed the complex-valued `make_nabla_tilde` SSOT, but the production driver is still real-dtype and k=0-biased. A context surface can carry the future complex operator, the mode label, and the truncation metadata without pretending the full driver path already exists. That preserves the audit invariant from FB-2.1: the complex dispatch remains explicit and cannot silently leak into the current real-only evolution path. The known-limit pin for this skeleton is therefore negative rather than positive: the function must raise until the mode-state machine, complex packing, and driver coupling land together. Off-axis Wigner-d rotations stay outside this contract and remain reserved for FB-5.2.
**Alternatives**:
| # | signature | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | `make_harmonic_mode_rhs_context(structure, mode, *, L_max) -> dict[str, object]` | Wraps the existing FB-2 `HarmonicMode` SSOT; keeps the future complex operator out of the shipped driver until the full perturbation path is ready; smallest blast radius. | Return payload is only a contract placeholder until FB-5.1 lands for real. | ✅ |
| 2 | `hierarchy_rhs_photon(..., harmonic_mode=None, allow_complex=False)` | Future callers would touch the production driver directly. | Reopens a sealed RHS interface before the k≠0 packing, complex state layout, and audit invariants are verified; too much blast radius for a skeleton-only rotation. | — |
**Core principles**: external-code policy; PSTF SSOT; no silent complex/real fallback; explicit correction of broken citations; deterministic failure until the full perturbation path lands.
**Skeleton path**: `htt/bass/perturbation/harmonic_modes.py::make_harmonic_mode_rhs_context`
**Test path**: `htt/bass/perturbation/test_fb51_harmonic_modes_skeleton.py::test_fb51_harmonic_mode_rhs_context_skeleton_contract`
**Guard rails** (yes/no): citations verified? yes; imports exist? yes; ≥ 2 alternatives? yes; broken prompt anchor recorded? yes
**Regression after plant**: 3,403 passed + 5 skipped (one new local-only skipped contract test over the 2026-04-20 baseline).

## §FB-5.2

### §FB-5.2 — full ``∇̃`` with off-axis Wigner-d skeleton
**Channel A**: 6 checked / 5 verified / 1 broken. Details: verified `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-5` names FB-5.2 as the mode-resolved `∇̃` lift; verified `htt/bass/hierarchy/nabla_dispatch.py` raises explicit `NotImplementedError("FB-5.2")` on the generic off-axis / non-abelian subsets; verified `htt/bass/hierarchy/boost_kernel.py` reserves the sibling off-axis Wigner-d lift for the same phase; verified `docs/audits/AUDIT_PHASE_FB2_2026-04-19.md` repeatedly records `FB-5.2` as the carry-forward for those deferred subsets; verified the new FB-5.1 surface intentionally did not mutate the shipped driver and therefore leaves FB-5.2 free to own the off-axis factory. Broken: the prompt-supplied Lowell solver reference `§13` path is still absent on disk.
**Channel B**: 1 arXiv check / 1 partial verification / 1 unresolved citation. Evidence: `arXiv:0706.2075` verifies the general Bianchi multipole-hierarchy context, but this session did not recover an arXiv-only locator that specifically seals the off-axis Wigner-d reduction itself. That narrower citation is therefore demoted to `# TODO: citation needed` rather than invented.
**Channel C** (prose, 6-10 lines): The off-axis lift needs a separate factory because the shipped `make_nabla_tilde` implementation is intentionally honest about its abelian-subalgebra scope. Patching that function in place would blur the line between the verified axis-aligned branch and the still-unverified Wigner-d machinery. A distinct `FB-5.2` factory can demand explicit rotation metadata, making the future Euler-angle dependence part of the contract rather than an optional hidden branch. That also keeps the failure mode sharp: if the caller has only an axis-aligned mode, they should stay on the FB-2 path; if they request an off-axis mode, they must opt into the new factory. The skeleton therefore refuses silent promotion from axis-aligned to off-axis semantics. Its known-limit pin is again structural: only the explicit future implementation may reduce onto the existing FB-2 operator when the supplied Euler angles collapse to the identity.
**Alternatives**:
| # | signature | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | `make_full_mode_nabla_tilde_operator(structure, mode, *, euler_angles) -> Callable[..., object]` | Keeps the off-axis scope separate from the already-audited axis-aligned path; makes rotation metadata explicit; smallest regression blast radius. | Adds a second factory name that future callers must choose intentionally. | ✅ |
| 2 | `make_nabla_tilde(structure, mode, *, euler_angles=None)` | One public name for both axis-aligned and off-axis branches. | Collapses audited and unaudited semantics into a single surface and raises the risk of silent fallback or accidental path widening. | — |
**Core principles**: explicit deferred-scope routing; PSTF SSOT; no silent axis-aligned fallback; deterministic failure until the off-axis reduction is literature-sealed.
**Skeleton path**: `htt/bass/perturbation/full_nabla_operator.py::make_full_mode_nabla_tilde_operator`
**Test path**: `htt/bass/perturbation/test_fb52_full_nabla_operator_skeleton.py::test_fb52_full_mode_nabla_tilde_operator_skeleton_contract`
**Guard rails** (yes/no): citations verified? partial with TODO demotion; imports exist? yes; ≥ 2 alternatives? yes; broken prompt anchor recorded? yes
**Regression after plant**: 3,403 passed + 6 skipped (two local-only skipped contract tests over the 2026-04-20 baseline).

## §FB-5.3

### §FB-5.3 — CAMB regular adiabatic seed skeleton
**Channel A**: 5 checked / 4 verified / 1 broken. Details: verified `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-5` names FB-5.3 as the CAMB regular adiabatic seed rotation; verified `htt/bass/hierarchy/ic.py` keeps the current perturbation seed zero-by-default and explicitly says the general regular-adiabatic seeder belongs at FB-5.3; verified the current `make_initial_state` surface only exposes narrow axisymmetric `Π_2` / `E_2` seeding and therefore should not be widened by stealth; verified the existing perturbation package has no seed-constructor surface yet. Broken: the prompt-supplied Lowell solver reference `§13.2` path is absent on disk.
**Channel B**: 2 arXiv checks / 1 verified / 1 broken. Evidence: `arXiv:astro-ph/9506072` explicitly says `"Isentropic initial conditions on super-horizon scales are derived."` That is the valid seed anchor. The prompt-supplied Lewis-Challinor `arXiv:astro-ph/9911177` resolves to a closed-FRW line-of-sight paper, not a regular-adiabatic initial-condition derivation, so it is rejected for FB-5.3 and demoted to `# TODO`.
**Channel C** (prose, 6-10 lines): The safe skeleton is a separate seed factory rather than a new mode flag on `make_initial_state`. The existing `ic.py` contract is intentionally small and zero-by-default, with only two narrow axisymmetric escape hatches for already-audited shear-driven tests. Folding CAMB-style seeding into that surface now would suggest the analytic formulas are already sealed and that the current caller graph is ready for k-dependent ICs, neither of which is true. A distinct `FB-5.3` constructor can take the mode scale, start time, and truncation explicitly and later decide how to compose with `zero_IC` without rewriting LB-5 semantics retroactively. The known-limit pin is the current baseline itself: until the perturbation seed is derived, the production default remains the zero seed and this placeholder must raise rather than guess formulas.
**Alternatives**:
| # | signature | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | `make_camb_regular_adiabatic_seed(*, k_comoving, eta_initial, a_initial, L_max) -> np.ndarray` | Keeps the new k-dependent IC logic off the shipped zero-IC surface; explicit mode/time metadata; smallest blast radius. | Future callers must wire the returned state into the existing pack/unpack path explicitly. | ✅ |
| 2 | `make_initial_state(..., seed_mode=\"camb_regular_adiabatic\") -> np.ndarray` | One IC entry point for both zero and regular-adiabatic seeds. | Widens an already-shipped LB-5 contract before the formulas and k-dependent semantics are fully audited. | — |
**Core principles**: no silent default change away from zero-IC; explicit k-dependent perturbation metadata; deterministic failure until the full seed derivation is sealed.
**Skeleton path**: `htt/bass/perturbation/regular_adiabatic_ic.py::make_camb_regular_adiabatic_seed`
**Test path**: `htt/bass/perturbation/test_fb53_regular_adiabatic_ic_skeleton.py::test_fb53_regular_adiabatic_seed_skeleton_contract`
**Guard rails** (yes/no): citations verified? yes with TODO demotion; imports exist? yes; ≥ 2 alternatives? yes; broken prompt anchors recorded? yes
**Regression after plant**: 3,403 passed + 7 skipped (three local-only skipped contract tests over the 2026-04-20 baseline).

## §FB-5.4

### §FB-5.4 — ``k = 0`` limit gate skeleton
**Channel A**: 5 checked / 5 verified / 0 broken. Details: verified `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-5` names FB-5.4 as the `k=0` recovery gate; verified `htt/bass/integration/test_lowell_bianchi.py` is the shipped LB-6 background / geometry regression anchor; verified `docs/PROGRESS_SCOREBOARD.md` already treats the `k=0` limit as an explicit physics check; verified the preceding FB-5.1 through FB-5.3 skeletons kept the mode, off-axis, and seed surfaces separate, leaving room for a standalone validator instead of an implicit integrator branch.
**Channel B**: 0 arXiv-only verifications / 2 citations demoted to `# TODO`. Evidence: the prompt's primary anchors for this sub-phase are Sachs-Wolfe 1967 and Kolb-Turner 1990, neither of which is available as an arXiv-era source. No substitute arXiv-only locator was adopted in this session, so both remain explicit TODO citations rather than guessed stand-ins.
**Channel C** (prose, 6-10 lines): The safest FB-5.4 contract is a validator, not a hidden integrator toggle. The reason is that `k = 0` is a recovery condition on the perturbation path, not a new production evolution mode by itself. Keeping the limit check as an assertion surface forces the future implementation to name both inputs: the perturbative state and the LB-6 background anchor it must collapse onto. That also prevents a subtle failure mode where an integrator silently detects a small k and switches algorithms without leaving an auditable trace. The large-scale Sachs-Wolfe gate belongs in the same validator family for the same reason: it is a known-limit check, not an excuse to widen runtime heuristics. The placeholder therefore raises until the comparison contract, tolerances, and observables are fully sealed.
**Alternatives**:
| # | signature | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | `assert_k_zero_limit_matches_background(*, k_comoving, background_state, perturbation_state, atol, rtol) -> None` | Makes the recovery target explicit; keeps the gate outside runtime evolution; smallest blast radius. | Future callers must gather the two state vectors before checking. | ✅ |
| 2 | `run(..., enforce_k_zero_limit=True)` | One integrator flag could own the comparison internally. | Hides a known-limit assertion inside runtime control flow and increases the risk of silent branch switching. | — |
**Core principles**: explicit known-limit validation; no hidden runtime mode switches; deterministic failure until the background-recovery contract is sealed.
**Skeleton path**: `htt/bass/perturbation/k_zero_limit_gate.py::assert_k_zero_limit_matches_background`
**Test path**: `htt/bass/perturbation/test_fb54_k_zero_limit_gate_skeleton.py::test_fb54_k_zero_limit_gate_skeleton_contract`
**Guard rails** (yes/no): citations verified? local yes / external TODO; imports exist? yes; ≥ 2 alternatives? yes; silent fallback avoided? yes
**Regression after plant**: 3,403 passed + 8 skipped (four local-only skipped contract tests over the 2026-04-20 baseline).

## §FB-5.5

### §FB-5.5 — Class B mode-quantisation skeleton
**Channel A**: 5 checked / 5 verified / 0 broken. Details: verified `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-5` names FB-5.5 as the Class B / Type V mode-quantisation rotation; verified `htt/bass/hierarchy/nabla_dispatch.py` already records the Type V Harrison-style hyperbolic branch and the Class B `a_twist²/(1+|h|)` offset; verified `htt/bass/background/bianchi_types.py` is the SSOT for `a_twist`, `h_parameter`, and the per-type Class B labels; verified the preceding FB-5.2 off-axis skeleton kept the mode-resolved operator separate, leaving space for a quantisation helper that only builds metadata.
**Channel B**: 0 arXiv-only verifications / 2 citations demoted to `# TODO`. Evidence: the prompt anchors for Harrison 1967 and Lyth-Stewart 1990 are pre-arXiv literature. No arXiv-only replacement was accepted in this session, so both remain explicit TODO citations.
**Channel C** (prose, 6-10 lines): The safest FB-5.5 contract is a pure metadata helper keyed by `StructureConstants`. The quantisation rule depends on the Class B twist and the group parameter `h`, so it should consume the same structure-constant SSOT that already drives `nabla_dispatch` rather than duplicating per-type branching elsewhere. Keeping it as a separate helper also avoids inflating the existing `HarmonicMode` descriptor before the continuous-versus-discrete branch rules are fully sealed. The future mode-state machine can call this helper first, then hand the resulting metadata to whichever harmonic or operator path is appropriate. That is cleaner than pretending quantisation is implicit in the generic mode label. The placeholder therefore raises until the branch taxonomy and scaling rules are literature-sealed.
**Alternatives**:
| # | signature | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | `quantise_class_b_mode(structure, *, eigenvalue, branch=\"principal\") -> dict[str, object]` | Reuses the existing structure-constant SSOT; keeps quantisation metadata separate from the generic mode descriptor; smallest blast radius. | Future callers must explicitly thread the returned metadata forward. | ✅ |
| 2 | `HarmonicMode(..., quantisation=\"class_b\")` | Keeps all mode metadata in one container. | Widens an already-shipped FB-2 descriptor before the Class B branch taxonomy is sealed; higher regression risk. | — |
**Core principles**: structure-constant SSOT; explicit metadata construction; no silent per-type quantisation rules hidden in unrelated factories.
**Skeleton path**: `htt/bass/perturbation/class_b_mode_quantization.py::quantise_class_b_mode`
**Test path**: `htt/bass/perturbation/test_fb55_class_b_mode_quantization_skeleton.py::test_fb55_class_b_mode_quantization_skeleton_contract`
**Guard rails** (yes/no): citations verified? local yes / external TODO; imports exist? yes; ≥ 2 alternatives? yes; hidden branching avoided? yes
**Regression after plant**: 3,403 passed + 9 skipped (five local-only skipped contract tests over the 2026-04-20 baseline).

## §FB-5.6

## §FB-5.7
