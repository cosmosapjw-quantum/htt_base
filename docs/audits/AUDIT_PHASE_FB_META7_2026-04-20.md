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

### §FB-7.1 — line-of-sight matrix propagator skeleton
**Channel A**: 6 checked / 6 verified / 0 broken. Details: verified
`docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-7`
names `bass/spectrum/lowell_los.py` explicitly; verified
`docs/lowell_bianchi/extended_coverage/PROJECT_MEMORY_EXPLICIT.md §10`
reserves the Limber `η_sp` sign fix for FB-7; verified
`htt/bass/los/bianchi_propagator.py` is the current Bianchi-I-only LOS
scaffold with explicit FLRW delegation and `ψ' = 0` B-mode floor;
verified `htt/bass/spectrum/cl_assembly.py` is the current diagonal
spectrum consumer; verified the internal Lowell path named in the prompt
is absent and therefore cannot be cited as if it were present; verified
the tracked fallback `htt/docs/lowell_bianchi_solver_reference_PR_WBS.md`
is only an observer-side output / likelihood anchor and not a substitute
for silently claiming the missing `§7` text exists on disk.
**Channel B**: 2 source checks / 2 verified / 0 divergent. Evidence:
`arXiv:astro-ph/9603033` is the Seljak-Zaldarriaga line-of-sight paper;
the arXiv record shows submission on 1996-03-08 and states that the
temperature anisotropy is written as a time integral over a geometrical
term times a source term. That is the correct external anchor for the
LOS source-times-geometry split used by this skeleton. No prompt-supplied
external locator needed correction for FB-7.1.
**Channel C** (prose, 6-10 lines): The safest FB-7.1 skeleton is a new
`bass/spectrum/lowell_los.py` module rather than a stealth widening of
`bass/los/bianchi_propagator.py`. The shipped propagator is explicitly
honest about its narrow Bianchi-I scope, its `m ∈ {0, ±2}` block
structure, and its `ψ' = 0` B-mode floor. Reopening that module for the
all-type FB-7 surface would blur audited and unaudited semantics before
the line-of-sight matrix algebra is sealed. A dedicated builder can make
the phase-0 Limber `η_sp` sign choice explicit in its contract instead
of burying it in internal state. Keeping the return type as a generic
mapping is also deliberate: the future implementation can carry transfer
blocks, source provenance, and sign diagnostics without prematurely
freezing a concrete container. The skipped test and `NotImplementedError`
keep the placeholder honest while making the intended module path and
signature reviewable now.
**Alternatives**:
| # | LOS surface | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | New `build_lowell_line_of_sight_propagator(...)` in `bass/spectrum/lowell_los.py` | Matches the parent plan path exactly; keeps the phase-0 Limber-sign carry explicit; avoids widening the shipped Bianchi-I-only LOS module by stealth. | Adds one more spectrum-side entry point. | ✅ |
| 2 | Widen `bass/los/bianchi_propagator.py` in place | Reuses the existing LOS machinery directly. | Collapses audited Type-I-only semantics and future all-type semantics into one module before the FB-7 contract is sealed. | — |
| 3 | Hide the builder inside `bass/spectrum/cl_assembly.py` | Fewer files touched. | Mixes transfer generation with spectrum consumption and makes the LOS sign-carry harder to audit in isolation. | — |
**Core principles**: explicit phase-0 sign carry; no silent widening of
the Bianchi-I LOS module; additive spectrum-side surface; deterministic
failure until the all-type propagator lands.
**Skeleton path**:
`htt/bass/spectrum/lowell_los.py::build_lowell_line_of_sight_propagator`
**Test path**:
`cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/spectrum/test_fb71_lowell_los_skeleton.py -q`
**Guard rails** (yes/no): citations verified? yes; exact parent-plan
module path used? yes; Limber-sign choice explicit in signature? yes;
no observer-frame claim implied? yes
**Targeted result**: `1 skipped`.
**Regression after plant**: expected full-suite movement
`3403 passed + 48 skipped` → `3403 passed + 49 skipped` pending the
phase-close gate.

## §FB-7.2

### §FB-7.2 — diagonal plus off-diagonal spectrum skeleton
**Channel A**: 6 checked / 6 verified / 0 broken. Details: verified
`docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-7`
names diagonal plus off-diagonal spectrum extraction as the second
output-stage sub-phase; verified `htt/bass/spectrum/cl_assembly.py`
already owns diagonal `C_ell` assembly and keeps off-diagonal
`C_{ℓm,ℓ' m'}` / BiPoSH behind an explicit out-of-scope guard; verified
the new `htt/bass/spectrum/lowell_los.py` FB-7.1 surface is the natural
future transfer-bundle input; verified no committed spectrum module yet
owned both diagonal and off-diagonal outputs together; verified the
existing Bianchi-I scaffolding is still axisymmetric / `m`-channel aware
rather than a fully dense `(ℓ,m)` covariance engine; verified the FB-7.2
contract therefore needs its own additive module rather than widening an
already-audited W10 diagonal-only surface by stealth.
**Channel B**: 3 source checks / 2 verified / 1 corrected. Evidence:
`arXiv:astro-ph/0601594` is Lewis & Challinor's 2006 review
`"Weak Gravitational Lensing of the CMB"`, which is a valid external
review anchor for off-diagonal CMB covariance language but is not
Bianchi-specific. The prompt-supplied `astro-ph/0607373` is *not* the
Pontzen-Challinor Bianchi paper; the arXiv record resolves it to a
cosmological-recombination-lines paper. The correct Bianchi anisotropic-
mixing anchor is `arXiv:0706.2075`, whose abstract explicitly says the
authors derive the CMB radiative-transfer equation as a multipole
hierarchy in nearly-FRW but anisotropic Bianchi universes and calculate
the polarization signal in the Bianchi VII_h case.
**Channel C** (prose, 6-10 lines): The safest FB-7.2 skeleton is a new
combined spectrum-and-covariance builder that consumes the LOS bundle
and names its off-diagonal strategy explicitly. That keeps the current
`cl_assembly.py` contract honest: it was audited as a diagonal-only
consumer and already advertises off-diagonal work as future scope. The
signature chooses `m_decoupled_blocks` as the default because the
shipped LOS scaffolding is already organized in `m` channels and the
future all-type implementation can extend that logic without first
committing to a fully dense or Wigner-d-dispatched basis. A dense
`(ℓ,m)` covariance matrix would be the most literal representation, but
it would force the memory and indexing contract too early in a skeleton
rotation. A sparse Wigner-d dispatch is plausible later, especially for
non-axis-aligned subsets, but choosing it now would imply a rotational
basis contract that the current codebase does not yet expose. The new
module therefore documents the strategy choice in the signature and
leaves the body unimplemented.
**Alternatives**:
| # | off-diagonal strategy | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | `m_decoupled_blocks` | Matches the existing `m`-channel LOS scaffolding; smallest blast radius; keeps the future covariance contract close to the current Type-I transfer structure. | Still leaves the exact block layout to the implementation phase. | ✅ |
| 2 | Fully dense `(ℓ,m) × (ℓ',m')` matrix | Most literal covariance representation; no later projection step required. | Freezes indexing and memory cost too early; larger contract surface for a skeleton-only rotation. | — |
| 3 | Wigner-d sparse dispatch | Likely relevant for general rotational mixing and future observer-frame work. | Prematurely commits to a rotation-basis API that the current BASS spectrum stack does not yet expose. | — |
**Core principles**: diagonal and off-diagonal outputs reserved
together; explicit correction of the bad Pontzen-Challinor arXiv ID; no
silent widening of the audited diagonal-only spectrum assembler;
strategy choice made visible in the signature rather than hidden.
**Skeleton path**:
`htt/bass/spectrum/off_diagonal_covariance.py::assemble_bianchi_spectrum_covariance`
**Test path**:
`cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/spectrum/test_fb72_off_diagonal_covariance_skeleton.py -q`
**Guard rails** (yes/no): citations verified? yes with corrected
Pontzen locator; alternatives table explicit? yes; chosen strategy
documented in signature? yes; diagonal-only W10 surface left untouched?
yes
**Targeted result**: `1 skipped`.
**Regression after plant**: expected full-suite movement
`3403 passed + 49 skipped` → `3403 passed + 50 skipped` pending the
phase-close gate.

## §FB-7.3

### §FB-7.3 — HTT decomposition and P0-triad skeleton
**Channel A**: 6 checked / 5 verified / 1 broken. Details: verified
`docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-7`
names HTT decomposition plus the P0 triad as the third sub-phase;
verified `docs/lowell_bianchi/extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md`
states via `D9` that FB-8 consumes the FB-7.3 HTT output and must not
duplicate the triad resolution; verified `htt/bass/runtime/canonical_decision.py`
is the current β-gate / tangency gate SSOT; verified
`htt/tsc/diagnostics/tangency.py` is the current `TangencyResult` SSOT;
verified no committed `bass/likelihood/` package existed before this
plant. Broken: the prompt-supplied on-disk Lowell `§14.2` locator is
absent in this worktree, so no tracked internal text currently exposes
the exact HTT P0-triad derivation verbatim.
**Channel B**: 2 source checks / 1 verified / 1 broken. Evidence: the
external Bianchi hierarchy / polarization paper is `arXiv:0706.2075`,
submitted on 2007-06-14, and its abstract explicitly says the authors
derive the CMB radiative-transfer equation as a multipole hierarchy in
anisotropic Bianchi universes. That is the corrected external anchor for
the HTT-facing stage. Broken: because the tracked Lowell `§14.2` file is
absent, the requested internal triad derivation cannot be quoted or
cross-checked verbatim in-session; the skeleton therefore keeps the
Lowell locator as an explicit `# TODO` rather than inventing prose.
**Channel C** (prose, 6-10 lines): The safest FB-7.3 skeleton is a
single decomposition entry point that takes the three P0 inputs
explicitly. That mirrors the current codebase's ownership boundaries:
prior alignment is still a likelihood-side concern, `TangencyResult` is
owned by `tsc`, and the β-gate verdict is owned by
`CanonicalDecision`. Pulling them together in one `build_htt_decomposition`
signature makes the future audit surface reviewable without pretending
those domains have already been unified in production. Creating a new
`bass.likelihood` package is also deliberate, because FB-7.4 and FB-8.6
already imply a likelihood stack distinct from the older `htt/htt/`
inference code. Hiding the triad inside a later likelihood builder would
make the FB-7.3 exit criterion impossible to audit on its own. The
skeleton therefore exposes the triad openly and leaves the body
unimplemented.
**Alternatives**:
| # | HTT surface | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | `build_htt_decomposition(..., prior_alignment, tangency_result, beta_gate)` | Makes the P0 triad explicit at the FB-7.3 boundary; reuses existing SSOT types; clean hand-off to FB-7.4 and FB-8. | Requires callers to assemble the triad inputs explicitly. | ✅ |
| 2 | Hide the triad inside the future FB-7.4 likelihood builder | Fewer public surfaces. | Erases the separate FB-7.3 audit boundary and makes D9 impossible to enforce cleanly. | — |
| 3 | Route HTT decomposition through `htt/htt/` bridge code directly | Reuses an existing HTT namespace. | Violates the BASS/HTT ownership split and would mix solver-side decomposition with observation-side inference code too early. | — |
**Core principles**: explicit P0-triad ownership; new BASS-side
likelihood package rather than reusing HTT inference code; no invented
Lowell `§14.2` prose; deterministic failure until the decomposition is
literature-sealed.
**Skeleton path**:
`htt/bass/likelihood/htt_decomposition.py::build_htt_decomposition`
**Test path**:
`cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/likelihood/test_fb73_htt_decomposition_skeleton.py -q`
**Guard rails** (yes/no): corrected external Bianchi anchor recorded?
yes; internal Lowell gap recorded explicitly? yes; P0 triad explicit in
signature? yes; FB-8 D9 hand-off preserved? yes
**Targeted result**: `1 skipped`.
**Regression after plant**: expected full-suite movement
`3403 passed + 50 skipped` → `3403 passed + 51 skipped` pending the
phase-close gate.

## §FB-7.4

### §FB-7.4 — cosmological-frame likelihood skeleton
**Channel A**: 6 checked / 5 verified / 1 broken. Details: verified
`docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-7`
names direction-dependent likelihood as FB-7.4; verified
`docs/lowell_bianchi/extended_coverage/DEVELOPMENT_LOG_FB3_TO_FB7.md`
already carries the crucial caveat that FB-7.4 is cosmological-frame
only; verified `docs/lowell_bianchi/extended_coverage/FB8_DISCRIMINATOR_SDD.md`
§1.1 and §7 define `bass.likelihood.observer_frame_adapter` as the FB-8
consumer that wraps a `CosmologicalFrameLikelihood` from FB-7.4;
verified `htt/docs/lowell_bianchi_solver_reference_PR_WBS.md §4`
frames the honest likelihood surface in terms of observer-side maps or
`a_{ℓm}` covariance rather than diagonal `C_ell` only; verified the new
`bass.likelihood` package introduced at FB-7.3 is the right solver-owned
home for this surface. Broken: the prompt-supplied on-disk Lowell
`§14.3` locator is absent in this worktree.
**Channel B**: 2 source checks / 1 verified / 1 broken. Evidence:
`arXiv:1907.12875` is the Planck 2018 V likelihood paper; the arXiv
record shows submission on 2019-07-30 and the title is exactly
`"Planck 2018 results. V. CMB power spectra and likelihoods"`. That is
the correct external likelihood-era anchor for the FB-7.4 contract.
Broken: because the tracked Lowell `§14.3` file is absent, the exact
internal direction-dependent-likelihood derivation cannot be quoted
verbatim in-session and remains an explicit TODO.
**Channel C** (prose, 6-10 lines): The safest FB-7.4 skeleton is a
named `CosmologicalFrameLikelihood` class rather than another generic
helper function. FB-8.6 already expects that type shape, and the scope
pin is too important to leave implicit. Putting the cosmological-frame
warning in the class docstring keeps the distinction close to the future
consumer surface and prevents a later builder from quietly swallowing an
observer-boost parameter. The constructor takes HTT decomposition plus a
tier label because the phase contract itself says the resolution is
tiered, but the class refuses to say anything about observer-frame data
composition beyond the explicit FB-8 hand-off. A plain `build_*`
function would work technically, but it would undercut the type name
that the FB-8 adapter SDD already uses. The skipped test therefore checks
the scope pin text directly even though the implementation body is still
unreachable.
**Alternatives**:
| # | likelihood surface | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | `CosmologicalFrameLikelihood` class with `log_prob(...)` | Matches the FB-8.6 consumer contract already written in the SDD; lets the cosmological-frame scope pin live on the type itself. | Slightly more structure than a simple helper function. | ✅ |
| 2 | `build_cosmological_frame_likelihood(...) -> Callable` | Minimal code surface. | Loses the named type that FB-8 already expects and makes the scope pin easier to miss. | — |
| 3 | Add observer-frame kwargs now and let FB-8 refine later | One future entry point. | Violates the phase boundary immediately by collapsing cosmological-frame and observer-frame semantics into one contract. | — |
**Core principles**: cosmological-frame scope pin is mandatory and
visible on the type; FB-8 owns observer-frame composition via
`bass.likelihood.observer_frame_adapter`; no silent boost parameter in
FB-7.4; deterministic failure until the tiered likelihood lands.
**Skeleton path**:
`htt/bass/likelihood/cosmological_frame.py::CosmologicalFrameLikelihood`
**Test path**:
`cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/likelihood/test_fb74_cosmological_frame_skeleton.py -q`
**Guard rails** (yes/no): cosmological-frame-only text in docstring?
yes; FB-8 adapter named explicitly? yes; corrected Planck V arXiv ID
recorded? yes; internal Lowell gap recorded explicitly? yes
**Targeted result**: `1 skipped`.
**Regression after plant**: expected full-suite movement
`3403 passed + 51 skipped` → `3403 passed + 52 skipped` pending the
phase-close gate.

## §FB-7.5
