# AUDIT_PHASE_FB_META8_2026-04-20

**Banner**: META pre-flight — FB-8 observer-frame discriminator /
extended-bundle skeletons + 3-channel verification
**Type distinction pin**: throughout FB-8,
`(beta_cosmo, v_hat_cosmo)` and `(beta_obs, v_hat_obs)` remain
separate typed surfaces with separate ownership. No inheritance, no
silent coercion, and no production path may conflate cosmological tilt
with observer boost.

## Pre-flight scan

- Required reading completed for:
  `docs/lowell_bianchi/extended_coverage/PROJECT_MEMORY_EXPLICIT.md`,
  `docs/lowell_bianchi/extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md`,
  `docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md`,
  `docs/lowell_bianchi/extended_coverage/SCOPE_DECISIONS.md`,
  `docs/lowell_bianchi/extended_coverage/SELF_AUDIT_AUTOMATION.md`,
  `docs/audits/AUDIT_PROMPT.md`,
  `htt/bass/species/tilted.py`,
  and `htt/bass/hierarchy/boost_kernel.py`.
- Reading summaries:
  - `PROJECT_MEMORY_EXPLICIT.md`: phase-boundary audits remain
    mandatory, additive commits only are allowed, no silent fallbacks
    are permitted on the truth-engine path, and every unresolved carry
    must stay explicit.
  - `EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md`: FB-8 is the
    observer-frame extended bundle, `D4` pins rapidity SSOT reuse, and
    `D9` keeps FB-8 downstream of the FB-7 HTT decomposition rather than
    duplicating it.
  - `FB8_DISCRIMINATOR_SDD.md`: the canonical FB-8 package split is
    `bass.observer.*` for observer-only boost/discriminator machinery
    plus `bass.likelihood.observer_frame_adapter` for composition on top
    of the already cosmological-frame FB-7 likelihood.
  - `SCOPE_DECISIONS.md`: the 2026-04-20 scope seal limits the extended
    bundle to FB-8 / FB-9 / FB-11, forbids speculative survey/lensing
    expansions, and keeps the observer-versus-cosmological distinction
    load-bearing.
  - `SELF_AUDIT_AUTOMATION.md`: FB-8 onward writes to
    `DEVELOPMENT_LOG_FB8_ONWARD.md`, rotates
    `NEXT_SESSION_PROMPT.md`, and must mark no-op gallery outcomes
    explicitly rather than omitting them.
  - `AUDIT_PROMPT.md`: restore contract before proposing fixes, keep the
    physics/code/numerics split visible, and record the smallest honest
    patch that removes the most risk.
  - `htt/bass/species/tilted.py`: `assert_tilt_admissible`,
    `velocity_to_rapidity`, `rapidity_to_velocity`, and
    `V_HAT_E_DEFAULT` are the rapidity / admissibility SSOT that
    `ObserverBoost` must reuse rather than reimplement.
  - `htt/bass/hierarchy/boost_kernel.py`: the existing boost kernel is
    an axi-symmetric seed for the hierarchy-side transport problem and
    explicitly points to `FB8_DISCRIMINATOR_SDD.md §3` as the separate
    observer-side aberration layer.
- Grep-check completed: `bass.species.tilted.assert_tilt_admissible`
  exists on disk and is importable for the future `ObserverBoost`
  skeleton contract.
- Regression gate executed on the exact FB META anchor:
  `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
  → `3403 passed, 53 skipped`.
- Source-of-work rule pinned for this phase: new observer-only skeletons
  land under `htt/bass/observer/`; `compose_tilts(global_tilt,
  observer_boost)` remains diagnostic-only per the SDD; production
  likelihood composition continues to flow through
  `bass.likelihood.observer_frame_adapter` on top of the FB-7
  cosmological-frame surface.

## §FB-8.1

**Type-distinct pin**: pending fill; `ObserverBoost` will remain an
observer-only rapidity carrier and will not inherit from or alias the
cosmological tilt surface.

## §FB-8.2

**Type-distinct pin**: pending fill; the aberration kernel surface will
act on `ObserverBoost` only and will not reuse cosmological-tilt
containers as observer-state proxies.

## §FB-8.3

**Type-distinct pin**: pending fill; observer-frame `C_ell` /
`a_{ell m}` adapters will wrap cosmological outputs without collapsing
the cosmo-versus-observer split.

## §FB-8.4

**Type-distinct pin**: pending fill; non-commutation notes will pin the
composition order explicitly so cosmological tilt and observer boost
stay distinct transforms.

## §FB-8.5

**Type-distinct pin**: pending fill; the discriminator will compare
`H_obs` against `H_cosmo` as separate hypotheses rather than a single
merged tilt parameter.

## §FB-8.6

**Type-distinct pin**: pending fill; likelihood-stack ingest will layer
observer-frame logic on top of the cosmological-frame FB-7 likelihood
without retyping cosmological tilt as observer boost.

## §FB-8.7

**Type-distinct pin**: pending fill; docs and gallery notes will keep
the cosmological and observer surfaces separated in prose and examples.
