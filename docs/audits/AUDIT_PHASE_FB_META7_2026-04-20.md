# AUDIT_PHASE_FB_META7_2026-04-20

**Banner**: META pre-flight — FB-7 spectrum/HTT/cosmological-frame-likelihood skeletons + 3-channel verification

## Pre-flight scan

- Required reading completed for:
  `docs/lowell_bianchi/extended_coverage/PROJECT_MEMORY_EXPLICIT.md`,
  `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-7`,
  `docs/lowell_bianchi/extended_coverage/SELF_AUDIT_AUTOMATION.md`,
  `docs/audits/AUDIT_PROMPT.md`,
  `htt/docs/lowell_bianchi_solver_reference_PR_WBS.md §4`,
  `htt/bass/los/bianchi_propagator.py`,
  and `htt/bass/spectrum/cl_assembly.py`.
- Required-reading exception recorded: the prompt-supplied on-disk path
  `docs/lowell_bianchi/lowell_bianchi_solver_reference.md` is absent in
  this worktree. The closest tracked internal substitute is
  `htt/docs/lowell_bianchi_solver_reference_PR_WBS.md`, whose observer-
  side output / likelihood section is used as the local Lowell anchor
  for this META cycle rather than inventing a missing file.
- Reading summaries:
  - `PROJECT_MEMORY_EXPLICIT.md`: phase-boundary audits are mandatory,
    additive commits only, the phase-0 Limber `η_sp` sign bug closes in
    FB-7, and silent fallbacks remain forbidden on the truth-engine
    path.
  - `FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-7`: the phase closes
    only after the line-of-sight propagator, diagonal plus off-diagonal
    spectra, HTT decomposition with the P0 triad, a *cosmological-
    frame* direction-dependent likelihood, and a Planck-2018 FLRW-limit
    match are all pinned.
  - `SELF_AUDIT_AUTOMATION.md`: every rotation must update the audit
    ledger, development log, and handoff prompt while keeping any
    carry-forward or broken locator explicit.
  - `AUDIT_PROMPT.md`: restore contract before proposing fixes, keep
    physics/code/numerics separate, and record the smallest patch that
    removes the most risk.
  - `htt/docs/lowell_bianchi_solver_reference_PR_WBS.md §4`: the local
    internal Lowell-style note pins the observer-side outputs
    `T/Q/U` or `a_{ℓm}^{T,E,B}` and states that the honest anisotropic
    likelihood surface is the full covariance
    `⟨a_{ℓm}^X a_{ℓ' m'}^{Y*}⟩`, not just diagonal `C_ℓ`.
  - `htt/bass/los/bianchi_propagator.py`: the shipped LOS scaffolding is
    currently Bianchi-I-only, block-diagonal in `m ∈ {0, ±2}`, and
    already names the `ψ' = 0` B-mode floor plus FLRW delegation as the
    load-bearing known limits.
  - `htt/bass/spectrum/cl_assembly.py`: the shipped spectrum scaffolding
    already assembles diagonal `C_ℓ` from transfer functions and keeps
    off-diagonal `C_{ℓm,ℓ' m'}` / BiPoSH extraction behind an explicit
    out-of-scope guard, which makes it the natural FB-7.2 extension
    point.
- Regression gate executed on the exact FB META anchor:
  `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
  → `3403 passed, 48 skipped`.
- Source-of-work rule pinned for this phase: committed skeletons will be
  additive `htt/bass/` surfaces, and every FB-7.4 note must explicitly
  say "cosmological-frame only; FB-8 composes observer-frame via
  `bass.likelihood.observer_frame_adapter`."

## §FB-7.1

## §FB-7.2

## §FB-7.3

## §FB-7.4

## §FB-7.5
