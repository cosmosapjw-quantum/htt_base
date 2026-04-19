# AUDIT_PHASE_FB_META9_2026-04-20

**Banner**: META pre-flight — FB-9 massive-neutrino species / extended-bundle skeletons + 3-channel verification
**LB-1 anchor**: throughout FB-9, `Sigma_mnu = 0` must remain byte-identical to the LB-1 massless `NeutrinoBackground` path on the full `bass/ tsc/` suite.
**Enum pin**: `SpeciesLabel.NEUTRINO` remains the only neutrino enum label; FB-9 dispatch happens behind the registry factory and must not add `MASSIVE_NEUTRINO`.

## Pre-flight scan

- Required reading completed for:
  `docs/lowell_bianchi/extended_coverage/PROJECT_MEMORY_EXPLICIT.md`,
  `docs/lowell_bianchi/extended_coverage/FB9_MASSIVE_NEUTRINO_SDD.md`,
  `docs/lowell_bianchi/extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md`,
  `docs/lowell_bianchi/extended_coverage/SELF_AUDIT_AUTOMATION.md`,
  `docs/audits/AUDIT_PROMPT.md`,
  `htt/bass/species/base.py`,
  `htt/bass/species/neutrino.py`,
  `htt/bass/species/registry.py`,
  `htt/bass/species/tilted.py`,
  and `htt/bass/hierarchy/hierarchy_rhs.py`.
- Reading summaries:
  - `PROJECT_MEMORY_EXPLICIT.md`: additive commits only, no silent fallbacks, and every phase boundary must carry an explicit audit trail.
  - `FB9_MASSIVE_NEUTRINO_SDD.md`: the canonical FB-9 surfaces are a new `bass.species.massive_neutrino` package, a registry-side `Sigma_mnu` kwarg, hierarchy-side massive-ν wire-up, and a no-new-enum dispatch policy.
  - `EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md`: FB-9 is in-scope by sealed decision `D7 = (a)` and still inherits the bundle-wide byte-anchor rule.
  - `SELF_AUDIT_AUTOMATION.md`: FB-9 writes to `DEVELOPMENT_LOG_FB8_ONWARD.md`, rotates `NEXT_SESSION_PROMPT.md`, and must mark gallery no-op states explicitly.
  - `AUDIT_PROMPT.md`: restore contract first, then map equations to code, then record the smallest honest patch.
  - `base.py` / `neutrino.py` / `registry.py`: the current production path is purely massless, the neutrino slot already uses `SpeciesLabel.NEUTRINO`, and `from_planck2018()` is the only load-bearing dispatch point.
  - `tilted.py`: `TiltedSpeciesBackground` already composes over any `SpeciesBackground` subclass, so FB-9.5 can stay a harness-only contract test.
  - `hierarchy_rhs.py`: `hierarchy_rhs_neutrino()` is presently a zero-collision wrapper around the photon driver, which makes a default-off massive-ν kwarg the smallest honest FB-9.4 skeleton.
- Regression gate executed on the exact FB-9 META anchor:
  `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
  → `3403 passed, 60 skipped`.
- Literature/source correction recorded up front for FB-9.1:
  the primary CLASS non-cold-relic paper is Lesgourgues & Tram 2011
  (`arXiv:1104.2935`), which describes adaptive quadrature for ncdm.
  The current CLASS `explanatory.ini` exposes `ncdm_maximum_q = 15`
  and `ncdm_N_momentum_bins = 150`; therefore the FB-9 skeleton's
  local `N_q = 15` is treated as a bundle contract, not as a direct
  CLASS default.

## §FB-9.1

### §FB-9.1 — `phase_space_grid` skeleton
**Channel A**: 5 checked / 5 verified / 0 broken. Details: verified
the new `bass.species.massive_neutrino` package is the correct isolated
write surface for FB-9; verified the local SDD pins the placeholder
signature `phase_space_grid(mass_eV, N_q=15)`; verified the package
docstrings state the LB-1 zero-mass invariant explicitly; verified the
new skipped contract test only inspects signature/doc surface; verified
no existing production import path now routes through the new module.
**Channel B**: 3 source checks / 2 verified / 1 corrected. Evidence:
Lesgourgues & Tram 2011 (`arXiv:1104.2935`) is the primary CLASS
non-cold-relic source and describes adaptive quadrature comparison for
ncdm rather than a fixed 15-point rule; the current CLASS
`explanatory.ini` exposes `ncdm_maximum_q = 15` and
`ncdm_N_momentum_bins = 150`; therefore the FB-9 skeleton keeps the
bundle-local `N_q = 15` contract but records it as a local placeholder,
not as a directly verified CLASS default.
**Channel C** (prose, 6-10 lines): The right FB-9.1 skeleton is a new
package boundary plus one raising function. That is enough to pin the
future import path, the future name, and the future default placeholder
without introducing any accidental zero-mass detour. The audit also has
to stay honest about the literature: CLASS IV supports Gauss-Laguerre
as one strategy, but its actual ncdm machinery is adaptive and the
current reference input does not equate `15` with the number of
momentum bins. Keeping `N_q = 15` in the skeleton is still acceptable
because it is a local SDD contract, not production physics. The skip
test exists only to lock that contract into CI while the implementation
remains intentionally absent.
**Alternatives**:
| # | Quadrature-family placeholder | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | Gauss-Laguerre placeholder API | Matches the local FB-9 SDD naming and one supported CLASS quadrature family; simple future hand-off. | The paper's actual strategy is adaptive, so the fixed `N_q=15` contract must be documented as local, not canonical CLASS. | ✅ |
| 2 | Gauss-Legendre on a log-momentum grid | Familiar for bounded transformed integrals. | Not the local SDD pick and adds a second convention before any implementation exists. | — |
| 3 | Plain trapezoidal placeholder | Easiest to explain. | Weakest convergence story and least aligned with the local SDD wording. | — |
**Core principles**: package boundary first; zero-mass runtime untouched;
literature correction recorded explicitly; deterministic failure until
the true quadrature lands.
**Skeleton path**:
`htt/bass/species/massive_neutrino/__init__.py`,
`htt/bass/species/massive_neutrino/phase_space.py`
**Test path**:
`cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/species/test_fb91_phase_space_grid_skeleton.py -q`
**LB-1 anchor clause**: `Sigma_mnu = 0` must not route through any new
phase-space helper; the LB-1 massless class remains the only active
zero-mass path.
**Targeted result**: `1 skipped`.
**Regression after plant**: expected full-suite movement
`3403 passed + 60 skipped` → `3403 passed + 61 skipped` pending the
phase-close gate.

## §FB-9.2

| Row | Status | Note |
|---|---|---|
| Scope | pending | `MassiveNeutrinoBackground.rho_rest()` / `.p_rest()` contract placeholder in the new package. |
| LB-1 anchor clause | pinned | `Sigma_mnu = 0` must keep using `NeutrinoBackground`; any massive-ν object is off-path unless the caller opts in explicitly. |

## §FB-9.3

| Row | Status | Note |
|---|---|---|
| Scope | pending | `SpeciesBackgroundRegistry.from_planck2018(..., Sigma_mnu=0.0)` dispatch skeleton. |
| LB-1 anchor clause | pinned | Default kwargs must preserve the exact LB-1 registry composition and full-suite byte identity. |

## §FB-9.4

| Row | Status | Note |
|---|---|---|
| Scope | pending | `hierarchy_rhs_neutrino` massive-ν wire-up skeleton with a default-off extension point. |
| LB-1 anchor clause | pinned | With no new kwarg passed, or with `Sigma_mnu = 0`, the neutrino hierarchy wrapper must remain byte-identical to the LB-1 / FB-2.4 path. |

## §FB-9.5

| Row | Status | Note |
|---|---|---|
| Scope | pending | `TiltedSpeciesBackground(base=MassiveNeutrinoBackground(...))` skip-marked compose harness only. |
| LB-1 anchor clause | pinned | The FB-3 wrapper remains unchanged; the zero-mass path keeps the existing massless base object and existing β=0 byte anchor. |

## §FB-9.6

| Row | Status | Note |
|---|---|---|
| Scope | pending | docs placeholder plus reserved gallery topic `15_massive_neutrino/`. |
| LB-1 anchor clause | pinned | Placeholder docs may describe future massive-ν work, but they must state plainly that the current shipped zero-mass runtime remains the LB-1 massless implementation. |
