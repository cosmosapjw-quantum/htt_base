# Development log — FB-8 onward

**Purpose**: canonical ledger of every extended-bundle sub-phase from
FB-8 onward. Entries are append-only: once a row lands it is never
rewritten; a superseding fact is appended as a new row with a
cross-reference.

**Parent**: [INDEX.md](INDEX.md).
**Coordinator plan**:
[EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md](EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md).

---

## Phase FB-8 — Observer-frame discriminator (extended bundle)

### FB-META-8.0 — pre-flight scan + audit scaffolding

- **Scope**: Read the required FB-8 phase documents plus the rapidity
  and boost-kernel SSOT modules, confirmed that
  `bass.species.tilted.assert_tilt_admissible` exists, and created
  [AUDIT_PHASE_FB_META8_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META8_2026-04-20.md)
  with the observer-versus-cosmological type-distinction banner and
  seven staged `§FB-8.k` sections.
- **Commit anchor**: see `git log --grep='FB-META-8.0'`.
- **Test delta**: 3,403 passing + 53 skipped → 3,403 passing + 53
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META8_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META8_2026-04-20.md).
- **Gallery**: no-op (audit/doc scaffolding only).
- **Carry-forward**: sub-phase skeleton plants FB-8.1 through FB-8.7.
- **Notes**: all observer-frame production surfaces for this phase land
  under `htt/bass/observer/`; production composition remains layered via
  `bass.likelihood.observer_frame_adapter`.

### FB-8.1 — `ObserverBoost` dataclass (rapidity SSOT)

- **Scope**: Created the new
  [bass/observer](../../../htt/bass/observer/__init__.py) package with a
  module docstring that pins the observer-versus-cosmological split and
  added the skeleton
  [ObserverBoost](../../../htt/bass/observer/observer_boost.py) dataclass.
  The contract imports the shared FB-3.5 admissibility gate rather than
  duplicating rapidity / direction validation and explicitly forbids
  inheritance from the cosmological tilt type.
- **Commit anchor**: see `git log --grep='FB-META-8.1'`.
- **Test delta**: 3,403 passing + 53 skipped → 3,403 passing + 54
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META8_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META8_2026-04-20.md)
  §FB-8.1.
- **Gallery**: no-op (package boundary + contract only).
- **Carry-forward**: FB-8.2 aberration-kernel skeleton.
- **Notes**: `ObserverBoost` is type-distinct from cosmological tilt;
  the shared FB-3.5 guard is reused only as an admissibility SSOT.

### FB-8.2 — aberration kernel `K_{ell ell'}(beta_obs)`

- **Scope**: Added the skeleton
  [aberration_kernel](../../../htt/bass/observer/aberration.py) surface
  under `bass.observer` and exported it from the new observer package.
  The contract keeps the observer-frame kernel separate from the
  hierarchy-side `boost_kernel.py` seed and records the corrected
  Challinor locator (`astro-ph/0112457`) plus the Planck-2013 Table 1
  mismatch explicitly in the audit instead of silently accepting the
  prompt wording.
- **Commit anchor**: see `git log --grep='FB-META-8.2'`.
- **Test delta**: 3,403 passing + 54 skipped → 3,403 passing + 55
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META8_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META8_2026-04-20.md)
  §FB-8.2.
- **Gallery**: no-op (kernel contract only).
- **Carry-forward**: FB-8.3 observer-frame adapter skeletons.
- **Notes**: aligned-kernel storage is an explicit inference from the
  corrected literature plus the existing on-axis seed; the audit calls
  that out directly.

### FB-8.3 — observer-frame `C_ell` / `a_{ell m}` adapters

- **Scope**: Added
  [apply_observer_boost and observed_alm_mixing](../../../htt/bass/observer/adapters.py)
  as explicit observer-side adapter skeletons over the FB-8.2 kernel and
  exported both from `bass.observer`. The contracts pin the
  zero-rapidity byte-identity requirement while keeping all
  observer-frame post-processing outside the FB-7 cosmological-frame
  likelihood package.
- **Commit anchor**: see `git log --grep='FB-META-8.3'`.
- **Test delta**: 3,403 passing + 55 skipped → 3,403 passing + 56
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META8_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META8_2026-04-20.md)
  §FB-8.3.
- **Gallery**: no-op (adapter contracts only).
- **Carry-forward**: FB-8.4 non-commutation / composition-order pin.
- **Notes**: both adapters stay in the observer package so the
  cosmological-frame FB-7 scope pin remains intact.

### FB-8.4 — non-commutation + SSOT composition-order pin

- **Scope**: Added the diagnostic-only
  [compose_tilts](../../../htt/bass/observer/composition.py) skeleton and
  exported it from `bass.observer`. The helper is explicitly banned from
  the production path and uses a typing-only `GlobalTilt` protocol so
  the future cosmological tilt carrier is acknowledged without being
  silently fabricated.
- **Commit anchor**: see `git log --grep='FB-META-8.4'`.
- **Test delta**: 3,403 passing + 56 skipped → 3,403 passing + 57
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META8_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META8_2026-04-20.md)
  §FB-8.4.
- **Gallery**: no-op (diagnostic contract only).
- **Carry-forward**: FB-8.5 discriminator skeleton.
- **Notes**: the accessible Ellis/Maartens/MacCallum preview confirms
  the book metadata but not the exact `§5.2` text, so the audit records
  that source gap explicitly.

### FB-8.5 — discriminator `Lambda(data; H_obs, H_cosmo)`

- **Scope**: Added the operational-core skeleton
  [likelihood_ratio](../../../htt/bass/observer/discriminator.py) and
  the matching
  [DiscriminatorResult](../../../htt/bass/observer/discriminator.py)
  schema under `bass.observer`. The audit includes the required
  alternatives table and picks the likelihood-ratio statistic while
  recording the unresolved asymptotic-citation gap instead of pretending
  it is already closed.
- **Commit anchor**: see `git log --grep='FB-META-8.5'`.
- **Test delta**: 3,403 passing + 57 skipped → 3,403 passing + 58
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META8_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META8_2026-04-20.md)
  §FB-8.5.
- **Gallery**: no-op (discriminator contract only).
- **Carry-forward**: FB-8.6 likelihood-stack ingest.
- **Notes**: the Kosowsky/Kahniashvili recovery argument is verified;
  the prompt's statistical locator is still an explicit TODO.

### FB-8.6 — observer-frame likelihood adapter

- **Scope**: Added the skeleton
  [ObserverFrameLikelihood](../../../htt/bass/likelihood/observer_frame_adapter.py)
  wrapper in `bass.likelihood` and exported it from the package
  `__init__`. The contract composes over
  `CosmologicalFrameLikelihood` rather than reopening it, and keeps the
  observer prior typed through a local protocol instead of fabricating a
  concrete prior implementation.
- **Commit anchor**: see `git log --grep='FB-META-8.6'`.
- **Test delta**: 3,403 passing + 58 skipped → 3,403 passing + 59
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META8_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META8_2026-04-20.md)
  §FB-8.6.
- **Gallery**: no-op (likelihood wrapper contract only).
- **Carry-forward**: FB-8.7 docs + gallery skeleton.
- **Notes**: the Lowell `§14` on-disk locator is still absent and is
  kept visible as an audit gap.

### FB-8.7 — docs + gallery placeholder

- **Scope**: Added an FB-8 observer-frame placeholder section to
  [00_conventions.md](../00_conventions.md), reserved the gallery topic
  [14_observer_frame](../../../figures/physics_gallery/14_observer_frame/README.md),
  and updated the root gallery README so the phase's no-op render status
  is explicit rather than implied.
- **Commit anchor**: see `git log --grep='FB-META-8.7'`.
- **Test delta**: 3,403 passing + 59 skipped → 3,403 passing + 60
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META8_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META8_2026-04-20.md)
  §FB-8.7.
- **Gallery**: no-op (reserved topic directory + README only).
- **Carry-forward**: phase-close regression + FB-META-9 handoff.
- **Notes**: no dummy PNGs were generated; the no-op is documented in
  both the gallery tree and the audit.

### FB-META-8.CLOSE — Phase FB-8 skeletons planted (7 sub-phases)

- **Scope**: Closed the FB-8 skeleton cycle after planting
  `FB-8.1` through `FB-8.7`, reran the full `bass/ tsc/` regression, and
  rotated the bootstrap handoff to FB-META-9.
- **Commit anchor**: see `git log --grep='FB-META-8.CLOSE'`.
- **Test delta**: 3,403 passing + 53 skipped → 3,403 passing + 60
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META8_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META8_2026-04-20.md)
  (phase-close note).
- **Gallery**: no-op (topic reserved; no fabricated PNGs).
- **Carry-forward**: FB-META-9 bootstrap plus the explicit source gaps
  recorded in the audit.
- **Notes**: observer-versus-cosmological type distinction is now pinned
  across the code skeletons, the docs, and the handoff contract.

## Phase FB-9 — Massive neutrino species (extended bundle)

### FB-META-9.0 — pre-flight scan + audit scaffolding

- **Scope**: Read the required FB-9 phase documents plus the current
  neutrino, registry, tilt-wrapper, and hierarchy surfaces; confirmed
  the exact `Sigma_mnu = 0` baseline anchor; and created
  [AUDIT_PHASE_FB_META9_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META9_2026-04-20.md)
  with the six staged `§FB-9.k` sections and the explicit no-new-enum
  dispatch pin.
- **Commit anchor**: see `git log --grep='FB-META-9.0'`.
- **Test delta**: 3,403 passing + 60 skipped → 3,403 passing + 60
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META9_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META9_2026-04-20.md).
- **Gallery**: no-op (audit/doc scaffolding only).
- **Carry-forward**: FB-9.1 through FB-9.6 skeleton plants.
- **Notes**: the pre-flight audit records that current CLASS references
  expose `ncdm_maximum_q = 15` and `ncdm_N_momentum_bins = 150`, so the
  local FB-9 skeleton default `N_q = 15` is treated as a bundle
  contract rather than a directly verified CLASS default.
