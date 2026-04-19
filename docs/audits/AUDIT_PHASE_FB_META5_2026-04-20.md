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

## §FB-5.4

## §FB-5.5

## §FB-5.6

## §FB-5.7
