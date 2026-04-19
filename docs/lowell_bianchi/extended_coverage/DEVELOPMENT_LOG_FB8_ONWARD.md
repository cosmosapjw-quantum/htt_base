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

### FB-META-9.1 — `phase_space_grid` skeleton

- **Scope**: Created the new
  [bass/species/massive_neutrino](../../../htt/bass/species/massive_neutrino/__init__.py)
  package and added the raising
  [phase_space_grid](../../../htt/bass/species/massive_neutrino/phase_space.py)
  contract placeholder plus its skipped harness test. The package is
  intentionally off-path for `Sigma_mnu = 0`.
- **Commit anchor**: see `git log --grep='FB-META-9.1'`.
- **Test delta**: 3,403 passing + 60 skipped → 3,403 passing + 61
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META9_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META9_2026-04-20.md)
  §FB-9.1.
- **Gallery**: no-op (package boundary + contract only).
- **Carry-forward**: FB-9.2 background skeleton.
- **Notes**: the audit records the CLASS-source correction explicitly:
  the local `N_q = 15` is a bundle placeholder, while current CLASS
  exposes `ncdm_maximum_q = 15` and `ncdm_N_momentum_bins = 150`.

### FB-META-9.2 — `MassiveNeutrinoBackground` skeleton

- **Scope**: Added the constructible
  [MassiveNeutrinoBackground](../../../htt/bass/species/massive_neutrino/background.py)
  placeholder and exported it from the package `__init__`, together
  with a skipped contract test. The skeleton keeps the neutrino enum
  unchanged and raises on unimplemented thermodynamic queries.
- **Commit anchor**: see `git log --grep='FB-META-9.2'`.
- **Test delta**: 3,403 passing + 61 skipped → 3,403 passing + 62
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META9_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META9_2026-04-20.md)
  §FB-9.2.
- **Gallery**: no-op (background contract only).
- **Carry-forward**: FB-9.3 registry integration skeleton.
- **Notes**: the audit records that the prompt's Ma-Bertschinger
  `eqs. (56), (97)` are not themselves the background `rho/p` formulas,
  so the placeholder stays explicit about what is and is not verified.

### FB-META-9.3 — registry `Sigma_mnu` skeleton

- **Scope**: Extended
  [SpeciesBackgroundRegistry.from_planck2018](../../../htt/bass/species/registry.py)
  with a keyword-only `Sigma_mnu` placeholder kwarg, widened the
  top-level `bass.species` exports to include the FB-9 skeleton
  surfaces, and added a skipped contract test for the new factory
  signature. The default branch preserves the exact LB-1 massless
  neutrino constructor.
- **Commit anchor**: see `git log --grep='FB-META-9.3'`.
- **Test delta**: 3,403 passing + 62 skipped → 3,403 passing + 63
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META9_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META9_2026-04-20.md)
  §FB-9.3.
- **Gallery**: no-op (registry contract only).
- **Carry-forward**: FB-9.4 hierarchy wire-up skeleton.
- **Notes**: the positive-mass branch uses the local SDD's degenerate
  placeholder `Sigma_mnu / 3` while the default zero-mass branch keeps
  the exact LB-1 constructor call.

### FB-META-9.4 — hierarchy wire-up skeleton

- **Scope**: Extended
  [hierarchy_rhs_neutrino](../../../htt/bass/hierarchy/hierarchy_rhs.py)
  with a default-off `neutrino_background` seam, added an explicit
  `NotImplementedError` for the placeholder massive background, and
  added a skipped contract test. Existing default callers still forward
  straight into the zero-collision photon driver.
- **Commit anchor**: see `git log --grep='FB-META-9.4'`.
- **Test delta**: 3,403 passing + 63 skipped → 3,403 passing + 64
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META9_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META9_2026-04-20.md)
  §FB-9.4.
- **Gallery**: no-op (hierarchy seam only).
- **Carry-forward**: FB-9.5 tilted-compose harness.
- **Notes**: the wrapper now exposes the future integration seam
  explicitly, but the default massless runtime still takes the exact
  pre-FB-9 forwarding path.

### FB-META-9.5 — tilted-compose harness skeleton

- **Scope**: Added the requested skip-marked compose harness
  [test_tilted_massive_neutrino_compose.py](../../../htt/bass/species/test_tilted_massive_neutrino_compose.py)
  showing that `TiltedSpeciesBackground(base=MassiveNeutrinoBackground(...))`
  is the intended future shape. No production code changed in this
  sub-phase.
- **Commit anchor**: see `git log --grep='FB-META-9.5'`.
- **Test delta**: 3,403 passing + 64 skipped → 3,403 passing + 65
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META9_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META9_2026-04-20.md)
  §FB-9.5.
- **Gallery**: no-op (compose harness only).
- **Carry-forward**: FB-9.6 docs + gallery placeholders.
- **Notes**: `bass/species/tilted.py` is intentionally untouched; this
  sub-phase only reserves the future composition test surface.

### FB-META-9.6 — docs + gallery placeholders

- **Scope**: Added an FB-9 placeholder note to
  [01_species_background_spec.md](../01_species_background_spec.md),
  reserved the gallery topic
  [15_massive_neutrino](../../../figures/physics_gallery/15_massive_neutrino/README.md),
  updated the root gallery README, and added a skipped docs/gallery
  harness test. No PNGs were fabricated.
- **Commit anchor**: see `git log --grep='FB-META-9.6'`.
- **Test delta**: 3,403 passing + 65 skipped → 3,403 passing + 66
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META9_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META9_2026-04-20.md)
  §FB-9.6.
- **Gallery**: no-op (reserved topic directory + README only).
- **Carry-forward**: phase-close regression + FB-META-11 handoff.
- **Notes**: both placeholder docs state explicitly that the shipped
  zero-mass runtime is still the LB-1 massless neutrino path.

### FB-META-9.CLOSE — Phase FB-9 skeletons planted (6 sub-phases)

- **Scope**: Closed the FB-9 skeleton cycle after planting
  `FB-9.1` through `FB-9.6`, reran the full `bass/ tsc/` regression,
  and rotated the bootstrap handoff to FB-META-11.
- **Commit anchor**: see `git log --grep='FB-META-9.CLOSE'`.
- **Test delta**: 3,403 passing + 60 skipped → 3,403 passing + 66
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META9_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META9_2026-04-20.md)
  (phase-close note).
- **Gallery**: no-op (reserved topic only; no fabricated PNGs).
- **Carry-forward**: FB-META-11 bootstrap plus the explicit source
  corrections recorded in the FB-9 audit.
- **Notes**: the shipped runtime still preserves the `Sigma_mnu = 0`
  LB-1 anchor and keeps `SpeciesLabel.NEUTRINO` as the only neutrino
  enum label.

## Phase FB-11 — Inference driver + multi-type Bayes factor (extended bundle)

### FB-META-11.0 — pre-flight scan + audit scaffolding

- **Scope**: Read the required FB-11 phase documents plus the FB-7 / 8 /
  9 prerequisite skeleton surfaces, confirmed that every required
  upstream symbol exists on disk, reran the full `bass/ tsc/`
  regression, and created
  [AUDIT_PHASE_FB_META11_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META11_2026-04-20.md)
  with the seven staged `§FB-11.k` sections and the explicit
  determinism / driver-boundary banner.
- **Commit anchor**: see `git log --grep='FB-META-11.0'`.
- **Test delta**: 3,403 passing + 66 skipped → 3,403 passing + 66
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META11_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META11_2026-04-20.md).
- **Gallery**: no-op (audit/doc scaffolding only).
- **Carry-forward**: FB-11.1 through FB-11.7 skeleton plants.
- **Notes**: the pre-flight audit already records that the
  prompt-supplied `0706.2075` anchor is a `VII_h` paper rather than a
  Bianchi-IX evidence-sign source, so FB-11.6 must keep that mismatch
  explicit.

### FB-META-11.1 — `bass.inference.priors` skeleton

- **Scope**: Created the new
  [bass/inference](../../../htt/bass/inference/__init__.py) package and
  added the
  [priors](../../../htt/bass/inference/priors.py) contract module with a
  frozen `Prior` dataclass plus the named prior-builder placeholders
  promised by the FB-11 SDD. The audit records explicitly that Planck
  2018 VI is a parameter-range anchor here, while the SDD's
  half-Gaussian `Sigma_mnu` shape remains a local future-work contract.
- **Commit anchor**: see `git log --grep='FB-META-11.1'`.
- **Test delta**: 3,403 passing + 66 skipped → 3,403 passing + 67
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META11_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META11_2026-04-20.md)
  §FB-11.1.
- **Gallery**: no-op (package boundary + prior contracts only).
- **Carry-forward**: FB-11.2 sampler driver + reproducibility contract.
- **Notes**: the package exports only the priors surface for now, so no
  driver import path is opened prematurely.

### FB-META-11.2 — emcee driver + reproducibility contract

- **Scope**: Added the
  [emcee driver contract](../../../htt/bass/inference/drivers/emcee_driver.py),
  exported `PosteriorSample` / `run_posterior` from the package root,
  and created the
  [CLI placeholder](../../../htt/bass/inference/__main__.py) with
  explicit `--config` and `--seed` arguments. The planted docstrings now
  pin the same-machine byte-reproducibility contract and the
  single-threaded default without importing `emcee` yet.
- **Commit anchor**: see `git log --grep='FB-META-11.2'`.
- **Test delta**: 3,403 passing + 67 skipped → 3,403 passing + 68
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META11_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META11_2026-04-20.md)
  §FB-11.2.
- **Gallery**: no-op (driver contracts only).
- **Carry-forward**: FB-11.3 `bayes_factor` skeleton.
- **Notes**: the audit includes the required emcee vs dynesty vs zeus
  table and keeps the third-party-driver boundary explicit.

### FB-META-11.3 — `bayes_factor` skeleton

- **Scope**: Added
  [BayesFactorResult and bayes_factor](../../../htt/bass/inference/bayes.py)
  under `bass.inference`, exported them from the package root, and
  pinned thermodynamic integration as the production-default method
  while keeping nested sampling as a reference-only provenance hook.
- **Commit anchor**: see `git log --grep='FB-META-11.3'`.
- **Test delta**: 3,403 passing + 68 skipped → 3,403 passing + 69
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META11_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META11_2026-04-20.md)
  §FB-11.3.
- **Gallery**: no-op (evidence contracts only).
- **Carry-forward**: FB-11.4 convergence diagnostics.
- **Notes**: nested sampling remains documented as a cross-check only;
  no production `dynesty` import path is opened here.

### FB-META-11.4 — convergence diagnostics skeleton

- **Scope**: Added
  [r_hat, ess, geweke, and trace_plot_data](../../../htt/bass/inference/diagnostics.py)
  under `bass.inference`, exported them from the package root, and
  pinned the local threshold policy in the docstrings. The audit makes
  the threshold history explicit: Gelman-Rubin 1992 defines the
  diagnostic, while the stricter `1.01` cutoff is a later workflow
  convention.
- **Commit anchor**: see `git log --grep='FB-META-11.4'`.
- **Test delta**: 3,403 passing + 69 skipped → 3,403 passing + 70
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META11_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META11_2026-04-20.md)
  §FB-11.4.
- **Gallery**: no-op (diagnostic contracts only).
- **Carry-forward**: FB-11.5 synthetic-injection harness.
- **Notes**: the planted docstrings preserve the historical distinction
  between the original statistic and the modern acceptance threshold.

### FB-META-11.5 — synthetic-injection coverage harness

- **Scope**: Added the skip-marked
  [synthetic-injection harness](../../../htt/bass/inference/test_fb115_synthetic_injection_skeleton.py)
  that pins the future `68 % ± 5 %` coverage target and references the
  existing `run_posterior` / `bayes_factor` contracts as the intended
  end-to-end seam. No production code changed in this sub-phase.
- **Commit anchor**: see `git log --grep='FB-META-11.5'`.
- **Test delta**: 3,403 passing + 70 skipped → 3,403 passing + 71
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META11_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META11_2026-04-20.md)
  §FB-11.5.
- **Gallery**: no-op (test harness only).
- **Carry-forward**: FB-11.6 summary seam.
- **Notes**: the audit ties the harness shape back to
  Cook-Gelman-Rubin's simulation-based validation logic and records the
  inherited seed-roundtrip requirement explicitly.

### FB-META-11.6 — 11-type `ln B` summary seam

- **Scope**: Added the placeholder
  [summary config](../../../configs/fb11_summary.yaml), expanded the
  [inference CLI contract](../../../htt/bass/inference/__main__.py) to
  name the deterministic summary command and output paths, and added the
  skip-marked
  [summary harness](../../../htt/bass/inference/test_fb116_summary_run_skeleton.py)
  that pins the 11-type SSOT order. No dummy paper outputs were
  created.
- **Commit anchor**: see `git log --grep='FB-META-11.6'`.
- **Test delta**: 3,403 passing + 71 skipped → 3,403 passing + 72
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META11_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META11_2026-04-20.md)
  §FB-11.6.
- **Gallery**: no-op (CLI/config contract only).
- **Carry-forward**: FB-11.7 docs + gallery placeholders.
- **Notes**: the prompt's `arXiv:0706.2075` locator is kept explicit as
  a Bianchi `VII_h` mismatch rather than reused as a Bianchi-IX
  evidence-sign citation.

### FB-META-11.7 — docs + gallery placeholders

- **Scope**: Added an FB-11 placeholder note to
  [05_integrator_spec.md](../05_integrator_spec.md), reserved the
  gallery topic
  [16_inference_corner](../../../figures/physics_gallery/16_inference_corner/README.md),
  updated the root gallery README, and added a skipped docs/gallery
  harness test. No PNGs or paper-summary files were fabricated.
- **Commit anchor**: see `git log --grep='FB-META-11.7'`.
- **Test delta**: 3,403 passing + 72 skipped → 3,403 passing + 73
  skipped.
- **Audit**:
  [AUDIT_PHASE_FB_META11_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META11_2026-04-20.md)
  §FB-11.7.
- **Gallery**: no-op (reserved topic directory + README only).
- **Carry-forward**: phase-close regression + bundle-summary closeout.
- **Notes**: the placeholder docs say explicitly that FB-11 is
  skeleton-only; the future paper tables and gallery renders remain
  actual-work outputs, not META artifacts.

### FB-META-11.CLOSE — Phase FB-11 skeletons planted (7 sub-phases)

- **Scope**: Closed the FB-11 skeleton cycle after planting
  `FB-11.1` through `FB-11.7`, created the bundle-level summary audit
  [AUDIT_FB_META_SUMMARY_2026-04-20.md](../../audits/AUDIT_FB_META_SUMMARY_2026-04-20.md),
  and rotated the bootstrap handoff to FB-4.1 actual work.
- **Commit anchor**: see `git log --grep='FB-META-11.CLOSE'`.
- **Test delta**: last fully green pre-phase anchor
  `3,403 passing + 66 skipped`; close-gate attempt
  `3,400 passing + 73 skipped + 3 errors` because the pre-existing
  dirty-worktree deletion of `data/camb_ref_planck2018.npz` blocks the
  LB-6 CAMB oracle tests.
- **Audit**:
  [AUDIT_PHASE_FB_META11_2026-04-20.md](../../audits/AUDIT_PHASE_FB_META11_2026-04-20.md)
  (phase close note) and
  [AUDIT_FB_META_SUMMARY_2026-04-20.md](../../audits/AUDIT_FB_META_SUMMARY_2026-04-20.md).
- **Gallery**: no-op (topic `16_inference_corner` reserved; no PNGs
  fabricated).
- **Carry-forward**: FB-4.1 actual-work bootstrap plus the per-skeleton
  audit pointers in the bundle summary.
- **Notes**: the extended-bundle META sweep is complete across
  FB-4/5/6/7/8/9/11; every remaining actual-work phase now has a
  planted skeleton and a 3-channel audit section.
