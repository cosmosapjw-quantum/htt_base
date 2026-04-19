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

### §FB-8.1 — `ObserverBoost` dataclass skeleton
**Type-distinct pin**: `ObserverBoost` is an observer-only rapidity
carrier in `bass.observer`; it must not inherit from, alias, or accept
the cosmological tilt surface.
**Channel A**: 6 checked / 6 verified / 0 broken. Details: verified
`docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md §2`
names `ObserverBoost(rapidity, v_hat)` as the canonical FB-8.1 surface;
verified `docs/lowell_bianchi/extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md`
pins rapidity SSOT reuse and downstream type distinction via `D4` /
`D9`; verified `docs/lowell_bianchi/extended_coverage/SCOPE_DECISIONS.md`
seals the observer-versus-cosmological split on 2026-04-20; verified
`docs/audits/AUDIT_PHASE_FB3_2026-04-19.md §FB-3.5` records rapidity as
the decision-level SSOT plus the shared admissibility gate; verified
commit `c1130ad` exists locally as the shipped FB-3.5 anchor; verified
`bass.species.tilted.assert_tilt_admissible` is present and imported by
the new skeleton module instead of being reimplemented.
**Channel B**: 2 source checks / 2 verified / 0 divergent. Evidence:
the local FB-3.5 audit states that rapidity is the decision-level SSOT
and that `assert_tilt_admissible` is the published shared guard; the
matching shipped commit `c1130ad` is present on this branch with the
subject `FB-3.5: beta-gate reparametrisation (rapidity SSOT + shared
gate)`. No external locator is required for FB-8.1 because the prompt's
literature anchor is the internal FB-3.5 audit itself.
**Channel C** (prose, 6-10 lines): The safest FB-8.1 skeleton is a new
observer-only dataclass in `bass.observer`, not an extension of
`TiltedSpeciesBackground`. The whole point of the extended bundle is to
make the type checker and the audit surface reject any silent collapse
of `(beta_cosmo, v_hat_cosmo)` into `(beta_obs, v_hat_obs)`. Reusing the
FB-3.5 admissibility gate is still correct, because direction and
sub-luminal-domain validation are shared conventions rather than shared
physics. That is why the skeleton imports the gate but still raises:
the contract can pin the SSOT now without pretending the observer-frame
transport exists. Creating `bass.observer.__init__` in the same commit
also makes the package boundary explicit before any aberration or
discriminator code lands.
**Alternatives**:
| # | `ObserverBoost` surface | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | New `bass/observer/observer_boost.py::ObserverBoost` dataclass | Makes the observer-only ownership boundary explicit; cleanly reuses the FB-3.5 guard SSOT without reusing the cosmological type. | Adds a new package boundary before any functional implementation exists. | ✅ |
| 2 | Subclass `TiltedSpeciesBackground` | Reuses an existing dataclass and helpers. | Violates the type-distinct requirement and invites silent cosmology/observer conflation. | — |
| 3 | Leave observer boosts as raw tuples / mappings in later APIs | Minimal code surface today. | Hides the FB-8.1 contract, weakens type checking, and delays the key distinction the whole phase is meant to enforce. | — |
**Core principles**: separate ownership boundary first; rapidity and
admissibility remain single-sourced through FB-3.5; no inheritance from
the cosmological tilt carrier; deterministic failure until FB-8
implementation exists.
**Skeleton path**: `htt/bass/observer/observer_boost.py::ObserverBoost`
and `htt/bass/observer/__init__.py`
**Test path**:
`cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/observer/test_fb81_observer_boost_skeleton.py -q`
**Guard rails** (yes/no): type-distinct package boundary explicit? yes;
shared admissibility import verified? yes; no inheritance path opened?
yes; rapidity SSOT anchor cited? yes
**Targeted result**: `1 skipped`.
**Regression after plant**: expected full-suite movement
`3403 passed + 53 skipped` → `3403 passed + 54 skipped` pending the
phase-close gate.

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
