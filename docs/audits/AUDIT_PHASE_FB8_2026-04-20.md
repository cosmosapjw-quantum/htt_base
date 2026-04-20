# AUDIT_PHASE_FB8_2026-04-20

**Banner**: actual-work closeout for FB-8 observer-frame discriminator

## Phase summary

- Scope completed:
  - `htt/bass/observer/observer_boost.py` (FB-8.1)
  - `htt/bass/observer/aberration.py` (FB-8.2)
  - `htt/bass/observer/adapters.py` (FB-8.3)
  - `htt/bass/observer/composition.py` (FB-8.4)
  - `htt/bass/observer/discriminator.py` (FB-8.5)
  - `htt/bass/likelihood/observer_frame_adapter.py` (FB-8.6)
- New gallery topic rendered:
  `figures/physics_gallery/14_observer_frame/`
- Manuscript updated:
  `docs/manuscript/ch02_dipole_anomaly.tex`,
  `docs/manuscript/ch09_discussion.tex`,
  `docs/manuscript/references.bib`
- Conventions updated:
  `docs/lowell_bianchi/00_conventions.md §13`
- Rotation updated:
  `docs/lowell_bianchi/extended_coverage/DEVELOPMENT_LOG_FB8_ONWARD.md`,
  `docs/lowell_bianchi/NEXT_SESSION_PROMPT.md`
- Phase-close fix:
  `htt/bass/observer/__init__.py` now exposes the discriminator
  lazily so the full suite no longer trips an observer/likelihood
  import cycle during collection.
- Warning-hygiene fix:
  `htt/tsc/charts/laguerre_basis.py` now uses overflow-safe occupation
  formulas, and `bass.species` exposes a sweep-friendly
  `recombination_warning_policy` so high-volume parameter scans or
  inference loops can silence the known HyRec/FLRW support-gap warning.

## Required-reading close

- Read and used:
  - `docs/audits/AUDIT_PHASE_FB_META8_2026-04-20.md`
  - `docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md`
  - `docs/lowell_bianchi/extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md`
  - `docs/lowell_bianchi/extended_coverage/SCOPE_DECISIONS.md`
  - `htt/bass/species/tilted.py`
  - `docs/manuscript/ch02_dipole_anomaly.tex`
  - `docs/manuscript/ch09_discussion.tex`
- Scope guard preserved:
  the observer boost remains type-distinct from cosmological tilt, the
  aberration kernel stays linear in `beta_obs`, and no deferred FB-10 /
  FB-12 / FB-13 scope was reopened.

## Verification ledger

| Check | Command | Result |
|---|---|---|
| Syntax | `venv/bin/python -m py_compile scripts/make_physics_gallery.py` | PASS |
| Topic-14 render | `venv/bin/python scripts/make_physics_gallery.py --only 14_observer_frame` | PASS; 4/4 PNGs rendered |
| FB-8 targeted tests | `cd htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/observer/test_fb81_observer_boost_skeleton.py bass/observer/test_fb82_aberration_kernel_skeleton.py bass/observer/test_fb83_observer_adapters_skeleton.py bass/observer/test_fb84_composition_skeleton.py bass/observer/test_fb85_discriminator_skeleton.py bass/observer/test_fb87_docs_gallery_skeleton.py bass/likelihood/test_fb86_observer_frame_adapter_skeleton.py -q` | `225 passed in 1.78s` |
| Full regression | `cd htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` | `4104 passed, 14 skipped, 2 warnings in 147.62s` |

At phase close the earlier Laguerre overflow-warning signature is gone.
Only two known recombination support-gap warnings remain, both tied to
the intentional HyRec/FLRW coverage mismatch. High-volume sweeps can now
set `recombination_warning_policy='ignore'` when that gap is already an
accepted modelling choice.

## §FB-8.1

### FB-8.1 — `ObserverBoost` rapidity SSOT

- **Type-distinct pin**:
  `ObserverBoost` is an observer-only carrier in `bass.observer`; it
  does not inherit from and is not silently coercible to the
  cosmological tilt carrier.
- **Channel A (implementation)**:
  `ObserverBoost` now stores non-negative rapidity internally, derives
  `velocity`, `gamma`, and `gamma_sq`, and routes validation through
  `bass.species.tilted.assert_tilt_admissible(...)`.
- **Channel B (source anchor)**:
  the rapidity/admissibility rule is shared with FB-3.5, but the
  runtime type is not. That is the D4 scope pin from the extended plan.
- **Channel C (verification)**:
  FB-8.1 tests mirror the FB-3.1 / FB-3.5 guard set: finite rapidity,
  non-negative scalar, valid unit direction, and exact `tanh` / `cosh`
  property recovery.

## §FB-8.2

### FB-8.2 — aligned aberration kernel `K_{ell ell'}(beta_obs)`

- **Type-distinct pin**:
  the aberration kernel consumes `ObserverBoost` only; cosmological
  tilt is not accepted as an observer-state proxy.
- **Channel A (implementation)**:
  `aberration_kernel(L_max, boost)` now returns the linear tridiagonal
  aligned kernel with exact identity at `beta_obs = 0`.
- **Channel B (source anchor)**:
  the shipped kernel is the linear aligned recurrence used for the
  observer-frame layer and is externally anchored to
  Challinor & van Leeuwen 2002 plus the Planck 2013 XXVII observer-speed
  scale `beta_obs = 1.23e-3`.
- **Channel C (verification)**:
  the FB-8.2 tests pin the exact linear coefficients. At
  `beta_obs = 1e-3`, the audit witness values are
  `K_22 = 1.0` and `K_23 = -4.2857142857142855e-4`, matching the
  implemented recurrence and the regression test surface.

## §FB-8.3

### FB-8.3 — observer-frame `C_ell` / `a_{ell m}` adapters

- **Type-distinct pin**:
  both adapters operate on cosmological-frame outputs plus a separate
  `ObserverBoost`; they do not fuse observer and cosmological velocity
  parameters.
- **Channel A (implementation)**:
  `apply_observer_boost(...)` and `observed_alm_mixing(...)` ship as
  pure functions with exact copy-return at zero boost.
- **Channel B (source anchor)**:
  the diagonal-spectrum adapter uses the same aligned kernel as the
  harmonic adapter, so `C_ell` and `a_{ell m}` stay on one observer-side
  SSOT rather than drifting into separate ad hoc corrections.
- **Channel C (verification)**:
  the FB-8.3 tests pin byte-identity at `beta_obs = 0`, cross-check the
  diagonal-spectrum weighting against explicit kernel algebra, and keep
  the `a_{ell m} -> C_ell` consistency test green.

## §FB-8.4

### FB-8.4 — composition order and non-commutation

- **Type-distinct pin**:
  `GlobalTiltState` and `ObserverBoost` remain separate dataclasses in
  separate modules; `compose_tilts(...)` rejects `ObserverBoost` if it
  is passed in as the cosmological tilt argument.
- **Channel A (implementation)**:
  `compose_tilts(...)` ships as a diagnostic-only helper; it is not
  routed into production, and the conventions file pins the order
  `cosmo-tilt -> observer-boost`.
- **Channel B (source anchor)**:
  the non-commutation claim is operational rather than rhetorical:
  observer boosting is a local frame transform on a formed sky,
  whereas cosmological tilt changes the underlying rest-frame signal.
- **Channel C (explicit witness)**:
  with the FB-8.4 test spectra and
  `(eta_cosmo, vhat_cosmo) = (1.0e-3, \hat x)`,
  `(eta_obs, vhat_obs) = (1.23e-3, \hat z)`,
  the two production-order branches differ in TT by
  `[-2.267e-10, -1.198e-10, -7.536e-11, -5.206e-11, -3.822e-11, -2.928e-11, -8.137e-11]`
  over `ell = 2..8`.
  For the second witness state,
  `(eta_cosmo, vhat_cosmo) = (8.0e-4, (\hat x + \hat y)/sqrt(2))`,
  `(eta_obs, vhat_obs) = (1.1e-3, (\hat y + \hat z)/sqrt(2))`,
  the TT mismatch is
  `[-1.451e-10, -7.668e-11, -4.822e-11, -3.331e-11, -2.445e-11, -1.874e-11, -5.206e-11]`.
  The diagnostic sum returned by `compose_tilts(...)` is therefore kept
  explicitly out of the production path.

## §FB-8.5

### FB-8.5 — discriminator `Lambda(data; H_obs, H_cosmo)`

- **Type-distinct pin**:
  the discriminator compares an `ObserverHypothesis` against a
  `TiltHypothesis`; the two models keep their own typed parameter
  carriers and are never merged into a single velocity parameter.
- **Channel A (implementation)**:
  `likelihood_ratio(...)` now returns
  `Lambda = 2 [ln L_cosmo - ln L_obs]` together with the profiled
  `ObserverBoost` and `GlobalTiltState` estimators.
- **Channel B (source anchor)**:
  the coverage workflow follows the recoverability logic used in the
  Kosowsky-Kahniashvili observer-motion argument: the local boost and a
  genuine cosmological anisotropy need to be separated at the
  likelihood level, not by informal amplitude comparison.
- **Channel C (verification)**:
  the seeded `N = 500` coverage runs pass the 99% KS-uniformity gate
  under both truth hypotheses:
  `H_obs -> D_KS = 0.001, p_KS = 1.0`,
  `H_cosmo -> D_KS = 0.001, p_KS = 1.0`.
  The zero-signal dataset also remains pinned at
  `Lambda = 0` and `p = 0.5`.

## §FB-8.6

### FB-8.6 — observer-frame likelihood adapter

- **Type-distinct pin**:
  `ObserverFrameLikelihood` wraps the cosmological-frame likelihood; it
  does not reopen FB-7.4 and does not reinterpret cosmological tilt as
  an observer boost.
- **Channel A (implementation)**:
  the adapter now supports explicit observer-boost parsing plus flat,
  delta, and Gaussian boost priors, together with profile and
  marginalisation helpers.
- **Channel B (source anchor)**:
  the delta-prior path is the key phase-boundary invariant because it
  proves the observer layer reduces exactly to FB-7 when
  `beta_obs = 0`.
- **Channel C (verification)**:
  FB-8.6 tests keep the delta-prior byte-identity green, verify that
  `beta_obs` / `v_hat_obs` parsing lands on the same boost carrier as
  the explicit dataclass path, and pin the profiled best-fit boost
  rather than letting zero-observer cases inherit a stale amplitude.

## §FB-8.7

### FB-8.7 — docs, gallery, and closeout surfaces

- **Type-distinct pin**:
  the docs surface repeats the same boundary as the code surface:
  cosmological tilt and observer boost are separate typed layers with a
  fixed composition order.
- **Channel A (implementation)**:
  topic `14_observer_frame/` is now rendered with four PNGs, the root
  gallery README is updated, `00_conventions.md §13` is populated,
  Chapter 2 gains the new observer-frame discriminator section, and
  Chapter 9 now points back to that operational section.
- **Channel B (source anchor)**:
  `references.bib` now carries the three phase-specific observer-frame
  sources:
  `ChallinorVanLeeuwen2002`, `Planck2013XXVII`,
  `KosowskyKahniashvili2011`.
- **Channel C (verification)**:
  the FB-8.7 docs/gallery harness is real now and passes at
  `27 passed`; it checks the topic-14 PNGs, the script dispatch,
  the conventions section, the new Chapter-2 section/subsections, the
  Chapter-9 cross-reference, and the bibliography keys.

## Validation checklist

- [x] Six skeleton code surfaces implemented.
- [x] `beta_obs = 0 ->` aberration identity byte-for-byte.
- [x] Linear observer-frame `C_ell` / `a_{ell m}` adapters wired and tested.
- [x] Non-commutation witness written out explicitly in the audit.
- [x] Discriminator coverage test green on both `H_obs` and `H_cosmo`.
- [x] Gallery topic 14 rendered.
- [x] `ch02_dipole_anomaly` observer-frame discriminator section added.
- [x] `ch09_discussion` cross-reference paragraph added.
- [x] `00_conventions §13` populated.
- [x] Audit + dev-log + NEXT_SESSION rotated.

## Phase close

FB-8 is closed locally at the actual-work boundary with the
observer-frame boost carrier, aligned linear aberration kernel,
observer-side `C_ell` / `a_{ell m}` adapters, composition-order audit,
local-boost vs global-tilt discriminator, and the observer-frame
likelihood wrapper all implemented and verified.

- Full-suite state at close:
  `4104 passed, 14 skipped, 2 warnings`
- Gallery state at close:
  Topic 14 rendered with 4/4 PNGs.
- Documentation state at close:
  conventions, manuscript, bibliography, audit, and handoff all updated
  to the FB-8 actual-work boundary.
