# Project memory — explicit transcript

**Purpose**: every fact that the assistant's persistent memory carried
— and which a new collaborator would need in order to make
intention-preserving decisions — is recorded here verbatim, in plain
prose, so the bundle is legible even without any memory access.

**Parent**: [INDEX.md](INDEX.md).

---

## 1. Author / audience

- **User**: Jiwon, PhD researcher at **Soongsil OMEG** (Origin, Matter,
  and Evolution Group). Primary build target is the **BASS** cosmology
  solver — an approximation-free 1+3 covariant Boltzmann stack for
  Bianchi cosmologies and their FLRW limits.
- **Collaboration tone**: expect precise physics references, explicit
  citations in every modified docstring, and zero tolerance for
  silent fallbacks. Treat pushback on implementation choices as
  default behaviour rather than exception.
- **User email on record**: cosmosapjw@gmail.com.

## 2. Architecture constraints (non-negotiable)

These are the "truth engine" invariants. Any code review that
weakens them is rejected regardless of other merits.

- **Approximation-free truth engine mandated.** The codebase's reason
  for existence is to have a solver that, at any fixed tolerance, is
  *not* distinguishable from the exact equations. Approximations that
  the literature uses as performance shortcuts are banned.
- **Banned approximations** (explicit blacklist):
  - **TCA pre-phase** (Tight-Coupling Approximation used as a
    pre-decoupling shortcut) — not allowed anywhere in the production
    path. TCA may appear only as a *closure strategy* comparator
    inside `bass/hierarchy/closure.py`, never as an integrator
    substitute.
  - **FLRW UFA** (Ultra-Relativistic Fluid Approximation) — banned
    for neutrinos and photons in all forms. The PSTF hierarchy must
    be integrated fully.
  - **Photon RSA** (Radiation Streaming Approximation) — banned. The
    line-of-sight integral is evaluated, not substituted by its
    late-time asymptote.
- **PSTF (Projected Symmetric Trace-Free) is the sole multipole
  representation** in production. Any ℓm-style expansion enters only
  through a documented PSTF round-trip (see
  [02_multipole_hierarchy_spec.md](../02_multipole_hierarchy_spec.md)).
- **External-code guard**: CAMB / CLASS / AniCLASS / HEALPix outputs
  are allowed **only** as fixture files (typically `data/*.npz`) and
  only referenced inside test oracles. Production modules must not
  import any of them. The guard is enforced by
  `bass/validation/test_external_code_policy.py`.

## 3. Git workflow constraints

- **Single repo**: Python (`bass_py` / `htt/`) and Rust (`bass_rs` /
  `Cargo.toml`) live in the same repository.
- **Additive commits only**: do not rewrite history (no `rebase -i`,
  no `reset --hard`, no force-push to `main`). Every correction
  lands as a new commit, typically with the `AUDIT(<tag>): <short>`
  prefix when it is closing an audit finding.
- **No branch workflow**: all development happens on `main`. Branches
  are used only for one-off experiments that never merge; they
  must not carry production code.
- **`project/` tree is local-only**. The top-level `/project`
  directory is `.gitignore`d intentionally; manuscript drafts,
  private notes, and local scratchpads live there and must never be
  staged. Manuscript gates are verified in audit logs rather than in
  committed `.tex` files.

## 4. Phase-boundary audit rule

Every commit that closes a sub-phase — whether `LB-N`, `FB-N.k`,
`Phase LB complete`, or any commit whose message rotates the
`NEXT_SESSION_PROMPT.md` handoff — **must** self-trigger the
integrated phys-math-code audit template at
[docs/audits/AUDIT_PROMPT.md](../../audits/AUDIT_PROMPT.md) and record
the result under `docs/audits/AUDIT_PHASE_<tag>_<date>.md`.

Findings produced by the audit are ranked P0 / P1 / P2 / P3. P0 and
P1 are fixed **in the same session** as separate commits whose
messages carry the `AUDIT(<tag>): <short>` prefix. P2 and P3 are
carried forward to a named future session and tracked in the
audit's §9 "carry-forward ledger".

The assistant *never* waits for the user to remind it that an audit
is needed; every phase boundary self-triggers the audit. The
`.claude/hooks/check_phase_boundary_audit.py` hook exists as a
belt-and-suspenders reminder, but the canonical discipline is
self-triggered.

## 5. Phase-boundary gallery rule

Every phase boundary **must** extend
`scripts/make_physics_gallery.py` with new plots covering every
physical quantity added by the phase, regenerate all PNGs under
`figures/physics_gallery/`, and visually inspect each new PNG
before the commit lands. A phase that produces no new physical
quantity (e.g. a pure abstraction rotation such as FB-3.1) records
an explicit "no-op on gallery" entry in its audit document — silence
is not acceptable.

## 6. Performance targets

- **Single-run target**: 10–15 seconds on a low-spec dev machine
  (4 physical cores, ≤16 GB RAM). This is wall-time for one
  complete LowellBianchiIntegrator run at Type I, L_max ≈ 32,
  tolerances matching the Planck-2018 CAMB fixture.
- **Reference baselines** (for comparator sanity, not for match):
  CAMB at 5 s, CLASS at 7 s on the same machine. The project does
  not aim to beat them; it aims to be *correct* while staying
  within a factor-of-two range.
- **Measured bottleneck as of the freshest profile**:
  `ksolve` dominates at 93 % wall-time; Bessel evaluation at
  6.5 %; everything else sub-percent. The legacy "Bessel 57.7 %"
  figure that circulates in older notes is from a stale profiling
  run and must not be used for optimisation decisions.

## 7. Profiling toolchain (installed)

The project carries a local profiling stack, pinned via
`bass_py/pip freeze` snapshots in `docs/audits/pip_freeze_*.txt`.
Primary tools and intended use:

- `pyinstrument` — first-pass wall-time attribution; treat it as
  the source of truth for "where is the time going?".
- `scalene` — CPU + memory joint profile for hotspots where the
  two resources interact (PSTF cache, Bessel tabulation).
- `memray` — allocation tracing; used when mimalloc hot-path
  analysis needs an orthogonal view.
- `cProfile` + `snakeviz` — secondary cross-check; do not trust it
  alone (sampling bias).

## 8. Solver infrastructure

- **Integrator**: Rodas5P (linear + nonlinear branches) on the
  Python side; diffsol BDF on the Rust side. Both expose compatible
  `solve_ivp`-style contracts.
- **Allocator**: mimalloc on the Rust cdylib side; reduces allocation
  contention under heavy PSTF cache churn.
- **Duplicated trees**: there are currently two `pstf_primary/`
  directories from a historical migration. Only the canonical one
  inside `htt/bass/hierarchy/` is wired into the production path;
  the other is kept for archaeological reference until post-FB
  devops closes it.

## 9. Approved plans (snapshot of 2026-04-18)

- [ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md](../../ROADMAP_v3_APPROXIMATION_FREE_2026-04-18.md)
  — Rust-side truth-engine roadmap. Approved.
- [ROADMAP_PHASE_I_TO_L.md](../../ROADMAP_PHASE_I_TO_L.md) —
  bass_py preliminary plots / FAST_TRACK. Approved.
- [FULL_BIANCHI_COVERAGE_PLAN.md](../FULL_BIANCHI_COVERAGE_PLAN.md) —
  FB-0 through FB-7 roadmap. Approved.
- **This bundle** ([INDEX.md](INDEX.md)) — FB-8 / FB-9 / FB-11
  (scope sealed 2026-04-20; FB-10 / FB-12 / FB-13 discarded per
  [SCOPE_DECISIONS.md](SCOPE_DECISIONS.md)) + history
  consolidation.

## 10. Phase-0 audit findings (still live)

Three bugs were located during the Phase-0 audit and remain on the
carry-forward ledger until addressed in their reserved sessions:

1. **ODE divergence for k > 0.03**. Origin: an implicit truncation
   in the IC layer whose symptoms appear only at moderate k. Reserved
   for FB-5 (perturbation sector k ≠ 0).
2. **Limber `η_sp` sign**. The line-of-sight Limber approximation
   path uses an η sign convention opposite to the integrator's.
   Reserved for FB-7 (line-of-sight propagator).
3. **Full-mode D_2 collapse**. When full-mode dispatch is active and
   the amplitude tower is deep, the D_2 PSTF slot collapses to
   numerical zero at late times. Reserved for FB-5.1 (harmonic-mode
   wire-up with complex-dtype `nabla_dispatch`).

## 11. BASS project context

- **Phase 1 focus**: PSTF primary migration. The "PSTF primary"
  surface became the single source of truth for multipole storage;
  legacy ℓm storage was deprecated behind a documented round-trip.
- **Regression anchor**: bit-identical `D_2` transfer function at
  the radiation-era IC point, evaluated against a frozen fixture.
  Any PSTF-layer refactor must keep this anchor byte-identical.

## 12. Local-only directories (never stage)

- `/project` — manuscript drafts, private notes, anything not
  destined for the tracked history.
- Any `*.zip`, `*.tar.gz`, or PDF artifact that appears at the repo
  root during a session. These are almost always binary drops from
  other tools; investigate before staging.
- `/legacy` — captured snapshot of the prior monorepo layout.

## 13. Pointers

- External-repo coordinate for issues / feedback:
  https://github.com/anthropics/claude-code/issues (reporting
  assistant behaviour, not BASS bugs).
- BASS bugs live in the `docs/audits/AUDIT_PHASE_*` ledger; there is
  no external tracker.

---

*Whenever new persistent-memory entries are added upstream, add a
mirror entry here in the same commit that adds the memory. The two
must not diverge.*
