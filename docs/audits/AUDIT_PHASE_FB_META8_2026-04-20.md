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

### §FB-8.2 — aberration-kernel skeleton
**Type-distinct pin**: the aberration kernel acts on `ObserverBoost`
only; it is an observer-frame transform layered on top of
cosmological-frame multipoles and must not reuse cosmological-tilt
containers as observer-state proxies.
**Channel A**: 6 checked / 6 verified / 0 broken. Details: verified
`docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md §3`
names `aberration_kernel(L_max, boost)` as the canonical FB-8.2
surface; verified `htt/bass/hierarchy/boost_kernel.py` is the existing
axi-symmetric seed and explicitly points to the observer-side FB-8
layer; verified `bass.observer.ObserverBoost` now exists and keeps the
observer-only type boundary explicit; verified the new kernel skeleton
is placed in `bass.observer.aberration` rather than widening the
hierarchy-side seed by stealth; verified the package export in
`bass.observer.__init__` now includes `aberration_kernel`; verified the
new skipped test pins the corrected external locators in the docstring.
**Channel B**: 3 source checks / 3 verified / 0 silent divergences.
Evidence: the correct preprint for Challinor & van Leeuwen's 2002 paper
is `arXiv:astro-ph/0112457`, submitted on 2001-12-19, not the
prompt-supplied `astro-ph/0205005`; the ar5iv-rendered text states that
when the relative velocity is aligned with the tetrad axis, the
transformation becomes block-diagonal in `m`, which is the external
anchor for the observer-side aligned-kernel contract. The same source's
accessible Eq. (26) is the polarization-basis transport law rather than
the kernel equation, so the requested "Eq. (26) m=0 PSTF form" is
recorded as a locator mismatch instead of being invented. Planck 2013
XXVII, `arXiv:1303.5087`, is verified as the correct observer-velocity
paper and fixes the Sun-dipole scale at `v/c = 1.23e-3`; its accessible
Table 1 is a significance table, not a `K_{22}` / `K_{23}` coefficient
table, so that mismatch is also recorded explicitly.
**Channel C** (prose, 6-10 lines): The safest FB-8.2 skeleton is a new
observer-side kernel function rather than a retrofit of the existing
hierarchy boost seed. The hierarchy seed is about transport-side
projection and already declares its off-axis limits; the observer-side
kernel belongs in the package that owns `ObserverBoost` and the later
adapters. The aligned-boost `(L_max + 1) x (L_max + 1)` contract is an
inference from the corrected Challinor–van Leeuwen source plus the
existing on-axis seed, not a direct quotation of a single equation
number, so the audit says that plainly. Recording the two literature
locator mismatches is also important here: they are exactly the sort of
quiet drift that would make a future implementation look better grounded
than it really is. The skeleton therefore exposes the signature, cites
the corrected anchors, and stops.
**Alternatives**:
| # | Aberration surface | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | New `bass/observer/aberration.py::aberration_kernel` contract | Keeps observer ownership local to the new package; clean hand-off to FB-8.3 adapters. | Adds another package export before implementation exists. | ✅ |
| 2 | Reuse `bass/hierarchy/boost_kernel.py` directly | Reuses an existing on-axis seed. | Blurs hierarchy transport with observer-frame post-processing and weakens the type boundary. | — |
| 3 | Hide the kernel inside `apply_observer_boost` later | Smaller public API. | Erases the separate FB-8.2 audit boundary and makes literature checks harder to pin. | — |
**Core principles**: corrected external locators must be explicit;
observer-frame ownership remains inside `bass.observer`; aligned-kernel
storage is documented as an inference rather than a fabricated equation
quote; deterministic failure until the physics is implemented.
**Skeleton path**: `htt/bass/observer/aberration.py::aberration_kernel`
**Test path**:
`cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/observer/test_fb82_aberration_kernel_skeleton.py -q`
**Guard rails** (yes/no): corrected Challinor locator recorded? yes;
prompt/SDD Table 1 mismatch recorded? yes; observer-only type boundary
preserved? yes; hierarchy seed left untouched? yes
**Targeted result**: `1 skipped`.
**Regression after plant**: expected full-suite movement
`3403 passed + 54 skipped` → `3403 passed + 55 skipped` pending the
phase-close gate.

## §FB-8.3

### §FB-8.3 — observer-frame adapter skeletons
**Type-distinct pin**: observer-frame `C_ell` / `a_{ell m}` adapters
wrap cosmological-frame outputs using `ObserverBoost`; they do not
collapse cosmological tilt and observer boost into one parameter.
**Channel A**: 6 checked / 6 verified / 0 broken. Details: verified
`docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md §4`
names both `apply_observer_boost` and `observed_alm_mixing`; verified
the new `bass.observer.aberration_kernel` skeleton exists as the shared
FB-8.2 dependency; verified `bass.observer.__init__` now exports both
adapter names from the observer-only package; verified the adapters are
kept in a dedicated observer-side module rather than widening the
cosmological-frame FB-7 likelihood classes; verified the new skipped
test pins the `boost.rapidity == 0` identity promise in the public
docstring; verified no cosmological-tilt container is accepted anywhere
in the new signatures.
**Channel B**: 3 source checks / 3 verified / 0 silent divergences.
Evidence: the corrected Challinor & van Leeuwen source
`astro-ph/0112457` explicitly splits total-intensity transformations in
§II from linear-polarization transformations in §III, and the
ar5iv-rendered text states that the polarization tensor is expanded in
symmetric trace-free tensor harmonics with electric and magnetic
multipoles before giving the observer-frame mixing kernels. That is the
external anchor for separating the diagonal-spectrum adapter from the
harmonic-mixing adapter while still sourcing both from one observer-side
kernel. Planck 2013 XXVII, `arXiv:1303.5087`, again fixes the relevant
observer speed at `v/c = 1.23e-3` and describes de-boosting as the next
logical step once the signal is confirmed, which is the right external
context for these adapter placeholders.
**Channel C** (prose, 6-10 lines): The safest FB-8.3 skeleton keeps the
two observer adapters together in one module. They share the same type
boundary, the same zero-rapidity identity requirement, and the same
kernel dependency, but they still deserve separate public names because
one acts on diagonal spectra while the other acts on harmonic
coefficients. Folding both into the future likelihood adapter would hide
an important audit seam and make the FB-8.5 discriminator look more
monolithic than it should. Keeping them in `bass.observer` also enforces
the scope pin from FB-7: cosmological-frame likelihood code remains
cosmological-frame code. The skeleton therefore exposes the pair
directly and leaves the bodies unimplemented.
**Alternatives**:
| # | Adapter surface | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | Shared `bass/observer/adapters.py` with two explicit functions | Keeps both observer adapters on one write surface with a shared kernel dependency and a clean package boundary. | Slightly larger module than one-function-per-file. | ✅ |
| 2 | Split `C_ell` and `a_{ell m}` adapters into separate modules immediately | Very fine-grained file ownership. | Adds overhead without gaining any type-safety or audit clarity at skeleton stage. | — |
| 3 | Hide both adapters inside the future likelihood adapter | Smaller public API. | Obscures the FB-8.3 audit boundary and blurs transform code with likelihood composition. | — |
**Core principles**: zero-rapidity identity is public and explicit;
observer adapters stay separate from cosmological-frame likelihood code;
temperature/polarization and harmonic/spectrum roles remain distinct;
deterministic failure until the transport is implemented.
**Skeleton path**:
`htt/bass/observer/adapters.py::{apply_observer_boost, observed_alm_mixing}`
**Test path**:
`cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/observer/test_fb83_observer_adapters_skeleton.py -q`
**Guard rails** (yes/no): observer-only package boundary preserved? yes;
shared kernel dependency explicit? yes; zero-rapidity identity pinned?
yes; cosmological tilt not accepted in signatures? yes
**Targeted result**: `1 skipped`.
**Regression after plant**: expected full-suite movement
`3403 passed + 55 skipped` → `3403 passed + 56 skipped` pending the
phase-close gate.

## §FB-8.4

### §FB-8.4 — non-commutation and composition-order skeleton
**Type-distinct pin**: `compose_tilts` is diagnostic-only and keeps
cosmological tilt and observer boost as distinct transforms with a
pinned order `(cosmo-tilt -> observer-boost)`.
**Channel A**: 6 checked / 6 verified / 0 broken. Details: verified
`docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md §5`
declares `compose_tilts(global_tilt, observer_boost)` diagnostic-only;
verified `docs/lowell_bianchi/extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md`
pins separate rapidity-owning dataclasses and the load-bearing
distinction between global tilt and observer boost; verified the new
module keeps the helper in `bass.observer` rather than leaking it into a
production likelihood surface; verified the new `GlobalTilt` protocol is
typing-only and explicitly not an implementation carrier; verified the
public docstring says the helper must never be routed into production;
verified the skipped test locks those two diagnostic-only phrases in
place.
**Channel B**: 2 source checks / 1 verified / 1 broken. Evidence: the
Cambridge/CUP metadata for Ellis, Maartens & MacCallum's
*Relativistic Cosmology* verifies the 2012 publication, DOI
`10.1017/CBO9781139014403`, and the print ISBN family including the
prompt-supplied observer-side anchor. Broken: the accessible preview
does not expose the exact `§5.2` text needed to quote or line-pin the
non-commutation discussion, so that locator remains a documented source
gap rather than invented support. The local SDD and coordinator plan are
therefore the operative contract anchors for the composition-order pin.
**Channel C** (prose, 6-10 lines): FB-8.4 is the point where the code
has to resist a very tempting shortcut: turning two physically distinct
transforms into one combined parameter. The safest way to do that in a
skeleton-only pass is not to implement composition at all, but to expose
a diagnostic-only helper whose docstring forbids production use. Using a
typing-only `GlobalTilt` protocol is deliberate for the same reason. The
future extended-bundle dataclass is acknowledged, but this commit does
not pretend it already exists on disk. That keeps the signature
reviewable without creating a fake concrete type or opening an accidental
runtime dependency. The audit also keeps the book-section preview gap
explicit so later work knows exactly which part still needs a stronger
primary-source read.
**Alternatives**:
| # | Non-commutation surface | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | Diagnostic-only `compose_tilts(...)` in `bass.observer.composition` | Makes the production ban explicit and gives the audit a concrete surface to guard. | Adds a helper that intentionally does not compute anything yet. | ✅ |
| 2 | Hide the non-commutation note in docs only | Lowest code footprint. | No mechanical guard against accidental production routing. | — |
| 3 | Implement a real composed transform now | Could support later adapters directly. | Violates the skeleton-only contract and risks collapsing the two-parameter distinction before the audit is sealed. | — |
**Core principles**: diagnostic-only surface, not production; concrete
composition order pinned in the public docstring; future `GlobalTilt`
acknowledged without inventing an implementation; source gap recorded
openly.
**Skeleton path**:
`htt/bass/observer/composition.py::compose_tilts`
**Test path**:
`cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/observer/test_fb84_composition_skeleton.py -q`
**Guard rails** (yes/no): diagnostic-only production ban explicit? yes;
composition order pinned? yes; type distinction preserved? yes; exact
book-section preview gap recorded? yes
**Targeted result**: `1 skipped`.
**Regression after plant**: expected full-suite movement
`3403 passed + 56 skipped` → `3403 passed + 57 skipped` pending the
phase-close gate.

## §FB-8.5

### §FB-8.5 — discriminator skeleton
**Type-distinct pin**: the discriminator compares `H_obs` and `H_cosmo`
as separate hypotheses with separate parameter axes; it does not merge
observer boost into cosmological tilt.
**Channel A**: 7 checked / 7 verified / 0 broken. Details: verified
`docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md §6`
declares the discriminator to be the operational core of FB-8;
verified the new module lives in `bass.observer.discriminator` rather
than inside the FB-7 cosmological-frame likelihood package; verified the
function signature keeps separate `boost_model` and `tilt_model`
hypothesis inputs; verified the output schema is made explicit through
`DiscriminatorResult`; verified the new package export adds both the
function and result type; verified the docstring states the likelihood
composes on top of `bass.likelihood.cosmological_frame`; verified the
skipped test locks the `Lambda(data; H_obs, H_cosmo)` notation and the
Kosowsky anchor into the public contract.
**Channel B**: 3 source checks / 2 verified / 1 broken. Evidence:
`arXiv:1007.4539`, submitted on 2010-07-26 and published as
Phys. Rev. Lett. 106, 191301 (2011), states that observer motion induces
non-zero off-diagonal correlations between multipole moments and that
these signals should be detectable in future full-sky microwave maps
from Planck. In the accessible ar5iv text, the authors then estimate a
Planck signal-to-noise ratio of about five for the off-diagonal
cross-power signature if the dipole is entirely due to peculiar motion,
which is the requested recovery argument for an `H_obs`-style null.
Broken: the prompt-supplied statistical locator `Wald 1984, Stat. Sci.
3, 319, Ch. 6` could not be matched cleanly to an accessible primary
source in-session, so the asymptotic-likelihood-ratio citation remains a
documented TODO rather than invented support.
**Channel C** (prose, 6-10 lines): The discriminator has to be a named
surface now because FB-8 treats it as the operational core, not as a
side effect of a future sampler. Choosing the likelihood-ratio form at
the skeleton stage is the narrowest honest move: it matches the SDD, it
maps directly onto the already existing cosmological-frame likelihood
plus observer adapters, and it yields a concrete result schema that
later phases can profile or marginalise around. Just as importantly, it
does not force FB-8 to pretend that full evidence integration or
posterior-density estimation already exists. The missing asymptotic
citation is recorded explicitly, but that does not block the contract
surface itself because no statistical calibration is implemented yet.
**Alternatives**:
| # | Discriminator statistic | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | Likelihood ratio `Lambda = 2(ln L_max(H_cosmo) - ln L_max(H_obs))` | Matches the SDD exactly; keeps the observer-vs-cosmological comparison focused; can report an asymptotic p-value once the calibration citation is sealed. | Requires a later clean asymptotic-calibration citation and explicit dof handling. | ✅ |
| 2 | Bayes factor between `H_obs` and `H_cosmo` | Naturally incorporates prior volume and evidence. | Pulls FB-11 prior/evidence machinery into FB-8 too early and widens scope beyond the skeleton contract. | — |
| 3 | Posterior-density ratio from a future sampler | Aligns with later posterior workflows. | Not a standalone discriminator, depends on sampler existence, and obscures the direct `H_obs` versus `H_cosmo` test. | — |
**Core principles**: operational core stays explicit; observer and
cosmological hypotheses remain separate; the chosen statistic is
documented together with rejected alternatives; unverified asymptotic
citation remains visible instead of implied.
**Skeleton path**:
`htt/bass/observer/discriminator.py::{likelihood_ratio, DiscriminatorResult}`
**Test path**:
`cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/observer/test_fb85_discriminator_skeleton.py -q`
**Guard rails** (yes/no): alternatives table explicit? yes; chosen
statistic documented? yes; Kosowsky recovery anchor verified? yes;
unverified Wald locator recorded openly? yes
**Targeted result**: `1 skipped`.
**Regression after plant**: expected full-suite movement
`3403 passed + 57 skipped` → `3403 passed + 58 skipped` pending the
phase-close gate.

## §FB-8.6

**Type-distinct pin**: pending fill; likelihood-stack ingest will layer
observer-frame logic on top of the cosmological-frame FB-7 likelihood
without retyping cosmological tilt as observer boost.

## §FB-8.7

**Type-distinct pin**: pending fill; docs and gallery notes will keep
the cosmological and observer surfaces separated in prose and examples.
