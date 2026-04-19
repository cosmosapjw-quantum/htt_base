# AUDIT_PHASE_FB_META6_2026-04-20

**Banner**: META pre-flight — FB-6 regression-harness skeletons + 3-channel verification

## Pre-flight scan

- Required reading completed for:
  `docs/lowell_bianchi/extended_coverage/PROJECT_MEMORY_EXPLICIT.md`,
  `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-6`,
  `docs/lowell_bianchi/extended_coverage/SELF_AUDIT_AUTOMATION.md`,
  `docs/audits/AUDIT_PROMPT.md`,
  `htt/bass/background/bianchi_types.py`,
  `htt/bass/integration/test_lowell_bianchi.py`,
  and `htt/bass/hierarchy/test_fb36_tilted_regression.py`.
- Reading summaries:
  - `PROJECT_MEMORY_EXPLICIT.md`: phase-boundary audits are mandatory,
    additive commits only, external-code outputs remain test fixtures,
    and no silent fallback is allowed anywhere on the truth-engine path.
  - `FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-6`: the phase closes
    only after a 22-configuration regression matrix, five named
    cross-type continuity limits, and the literature/CAMB ground-truth
    cross-check surfaces are all pinned.
  - `SELF_AUDIT_AUTOMATION.md`: each rotation must append to the audit
    ledger, update the development log, rotate the handoff prompt, and
    keep any carry-forward claim explicit rather than tribal.
  - `AUDIT_PROMPT.md`: restore contract first, keep physics/code/numeric
    verification separate, and prefer the smallest patch that removes
    the most risk.
  - `htt/bass/background/bianchi_types.py`: the 11-type SSOT already
    names the registry and the load-bearing continuity relations
    `III = VI_{-1}`, `VII_h -> VII_0`, `VII_0 -> I`, `V -> open FLRW`,
    and `IX -> closed/isotropic`.
  - `htt/bass/integration/test_lowell_bianchi.py`: the existing LB-6
    integration suite is the oracle/style anchor for future FB-6
    regression coverage and already reuses the shipping
    `data/camb_ref_planck2018.npz` fixture.
  - `htt/bass/hierarchy/test_fb36_tilted_regression.py`: the immediate
    style exemplar for large explicit parameter sweeps is a dedicated
    regression module with clear ledger comments and shared fixture
    helpers.
- Regression gate executed on the exact FB META anchor:
  `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
  → `3403 passed, 11 skipped`.
- Workspace note: the repo already contains many unrelated deletions and
  untracked files before this session. FB-META-6 will stage only the
  audit/log/handoff surfaces plus the explicit FB-6 harness file
  requested by the prompt.
- Source-of-work rule for this phase: unlike FB-META-4 / FB-META-5, the
  committed skeleton lives in the test harness itself. The in-scope code
  surface is `htt/bass/integration/test_full_bianchi_coverage.py`; no
  production module is introduced in this META session.

## §FB-6.1

### §FB-6.1 — 22-configuration regression-harness skeleton
**Channel A**: 6 checked / 6 verified / 0 broken. Details: verified `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-6` names a new `bass/integration/test_full_bianchi_coverage.py` surface; verified `htt/bass/background/bianchi_types.py` is the 11-type SSOT; verified `htt/bass/integration/test_lowell_bianchi.py` is the existing LB-6 integration/oracle anchor; verified `htt/bass/hierarchy/test_fb36_tilted_regression.py` is the immediate style exemplar for an explicit large parameter sweep; verified there was no pre-existing `htt/bass/integration/test_full_bianchi_coverage.py`; verified the prompt requires a committed harness skeleton rather than a new production helper.
**Channel B**: 3 source checks / 2 verified / 1 partial. Evidence: Cambridge metadata confirms *Dynamical Systems in Cosmology* (1997) as the Wainwright-Ellis textbook anchor for the 11-type registry. `arXiv:0901.2122` (`Rogues' gallery`) was submitted on 2009-01-15 and revised on 2009-05-11; it explicitly treats the open/flat `VII_h` family together with its limiting types `I`, `V`, and `VII_0`, and it is the correct figure-bearing 2009 reference for FB-6.1 / FB-6.3. The older `arXiv:0706.2075` was submitted on 2007-06-14 and remains the earlier hierarchy paper, so the prompt's year/arXiv pairing is normalized here rather than copied forward. The Cambridge preview does not expose the full `§11.1` table text in-session, so the all-11-type list is taken from the local registry SSOT rather than a guessed textbook transcription.
**Channel C** (prose, 6-10 lines): The safest FB-6.1 skeleton is the regression harness itself because this sub-phase is a coverage declaration, not a reusable algorithm. A flat 22-row table makes the future review surface literal: every type and both orthogonal/tilted branches are visible in one diff and can be fixture-wired row by row later. A generated `11 × 2` product would be shorter, but it would hide the exact audit surface in helper logic and make future per-row fixture edits noisier. Keeping the file under `bass/integration` matches the phase contract: each future row is supposed to cover background invariants, hierarchy finiteness, and closure dispatch together rather than one lower-level subsystem. The tests stay skipped, and the unreachable `NotImplementedError` line keeps the placeholder honest without pretending the assertions exist yet. No production module or new fixture file is introduced here; only the committed matrix shape is sealed.
**Alternatives**:
| # | parametrisation shape | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | Flat explicit 22-row `pytest.param(...)` list | The full coverage declaration is visible in one place; row order is stable; future fixture keys can diverge per row without refactoring the test decorator. | More verbose than a generated product. | ✅ |
| 2 | Nested `ALL_BIANCHI_TYPES × {"orthogonal", "tilted"}` product | Shorter source; guaranteed mechanical coverage if the registry size stays fixed. | Hides the reviewed matrix behind generation logic and makes future per-row fixture naming / comments less explicit. | — |
**Core principles**: explicit coverage declaration; committed harness instead of helper-only scaffolding; no hidden matrix generation; no production code added in a META session.
**Skeleton path**: `htt/bass/integration/test_full_bianchi_coverage.py::test_fb61_full_bianchi_configuration_matrix`
**Test path**: `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/integration/test_full_bianchi_coverage.py -q`
**Guard rails** (yes/no): 22 explicit rows? yes; 11-type coverage? yes; orthogonal+tilted per type? yes; no production module introduced? yes
**Regression after plant**: `3403 passed + 33 skipped`.

## §FB-6.2

### §FB-6.2 — cross-type continuity-limit skeleton
**Channel A**: 6 checked / 6 verified / 0 broken. Details: verified `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-6` names exactly five continuity limits; verified `htt/bass/background/bianchi_types.py` already encodes `III = VI_{-1}`, `VII_h -> VII_0`, `VII_0 -> I`, `V` as the open-FLRW branch, and the isotropic Type IX parameterization; verified `htt/bass/hierarchy/nabla_dispatch.py` carries the same `III = VI_{h=-1}` identification with explicit literature citations; verified FB-6.1's committed 22-row matrix remained unchanged while this rotation added only named tuples; verified the same integration module is the intended home for the continuity harness; verified no helper abstraction is needed to plant the future tuple table.
**Channel B**: 5 limit checks / 5 reconciled / 0 divergent. Evidence: `arXiv:0901.2122` (submitted 2009-01-15; revised 2009-05-11) states that the open/flat models are `VII_h` together with the limiting types `I`, `V`, and `VII_0`, and its Figure 1 caption identifies the `VII_h -> VII_0`, `VII_h -> V`, and `VII_0 -> I` limits in words. The same paper states that enlarging the physical curvature radius of Type IX yields Type I, which is the closed/isotropic branch behind the reserved `IX_BKL_isotropic` tuple. For `VI_h -> III`, the local SSOT and `nabla_dispatch.py` explicitly define Type III as `VI_{h=-1}` and cite Ellis-MacCallum 1969; DOI/OSTI metadata confirms the identity of that 1969 classification paper. I infer from those combined sources that the five named tuples are the correct continuity skeleton to reserve, even though the Cambridge preview still does not expose the W-E `§18` table text itself.
**Channel C** (prose, 6-10 lines): The safest FB-6.2 skeleton is five explicit named tuples, not a generalized limit-builder helper. Each limit has different semantics: `h -> 0+` is one-sided, `h -> -1` lands on a distinct named type, `n -> 0` in `VII_0` and `IX` means isotropization rather than just parameter shrinkage, and `a_twist -> 0` for Type V is a direct structural-constant collapse. A helper would blur those distinctions before the actual epsilon schedules and normalization conventions are audited. Keeping the tuples in the same integration module also makes the phase structure linear and readable: FB-6.1 declares the coverage rows, FB-6.2 declares the continuity rows, and FB-6.3 will declare the oracle rows. The `IX_BKL_isotropic` target remains a descriptive label on purpose because the future assertion is about an isotropic branch of Type IX rather than a separate registry entry. As with FB-6.1, the test is still only a skipped placeholder with an unreachable `NotImplementedError`.
**Alternatives**:
| # | continuity surface | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | Five explicit named tuples in the integration test module | Keeps sidedness and target semantics visible; no helper indirection; easy to add per-limit fixture metadata later. | Slightly repetitive. | ✅ |
| 2 | One helper that constructs limits from `(source, parameter, target)` rules | Centralizes naming and could reduce repetition. | Hides load-bearing distinctions (`0+`, `-1`, isotropic branch labels) in helper code before the actual tolerances are verified. | — |
**Core principles**: explicit named-limit declaration; no guessed epsilon schedule; no helper abstraction that hides sidedness or target-branch semantics.
**Skeleton path**: `htt/bass/integration/test_full_bianchi_coverage.py::test_fb62_cross_type_continuity_limits`
**Test path**: `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/integration/test_full_bianchi_coverage.py -q`
**Guard rails** (yes/no): five named limits present? yes; FB-6.1 matrix unchanged? yes; `III = VI_{-1}` recorded explicitly? yes; no tolerance guesses introduced? yes
**Regression after plant**: `3403 passed + 38 skipped`.

## §FB-6.3

### §FB-6.3 — Pontzen-Challinor / CAMB oracle-fixture skeleton
**Channel A**: 6 checked / 6 verified / 0 broken. Details: verified `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-6` names a Pontzen-Challinor + CAMB ground-truth cross-check; verified `htt/bass/integration/test_lowell_bianchi.py` already uses the shipped `data/camb_ref_planck2018.npz` oracle; verified no new fixture data should ship in this META session; verified `tests/fixtures/` is the canonical root-level home for future stable regression inputs; verified FB-6.1 and FB-6.2 tables remained unchanged while FB-6.3 added only fixture-path rows; verified the prompt still requires a harness-only skeleton rather than any spectrum-production module.
**Channel B**: 5 source checks / 4 verified / 1 corrected. Evidence: `arXiv:0901.2122` (submitted 2009-01-15; revised 2009-05-11) is the verified 2009 Pontzen paper and the accessible arXiv text contains three figures, not four. Figure 1 is the VII_h / limiting-type vector-mode grid, Figure 3 is the nucleosynthesis-compatible VII_h / VII_0 grid, and `§IV` is the closed-model / Type IX discussion; that is the correct figure/section surface for the reserved literature oracles. The prompt's "Fig 4 + §IV" locator is therefore corrected here to "Figures 1 and 3 + §IV" rather than copied forward inaccurately. `astro-ph/0601594` is the 2006 Lewis-Challinor FLRW/CMB-spectra review, while the actual numeric FLRW oracle in this repo remains the shipped CAMB Planck-2018 NPZ. I infer from those sources that the off-diagonal CTT rows should be reserved as future fixture paths only, not presented as already-digitized figure products.
**Channel C** (prose, 6-10 lines): The safest FB-6.3 skeleton is a fixture-path table inside the existing integration harness because this sub-phase is about oracle layout, not yet about spectral code. Reusing `data/camb_ref_planck2018.npz` for the CAMB-backed rows avoids inventing a duplicate FLRW fixture path when the repo already has the canonical external-code oracle. The literature side is different: those paths need to live under `tests/fixtures/fb6/` because the future inputs will be digitized or hand-curated figure-derived baselines rather than production data files. Keeping the off-diagonal CTT rows as reserved paths is load-bearing honesty: the accessible 2009 paper gives pattern/section anchors, but it does not hand us a ready-made numeric off-diagonal table in this session. The corrected figure count also matters operationally, because planting a bogus `fig4` filename now would lock in a bad contract for the actual-work session. As with the prior two rotations, the tests stay skipped and the `NotImplementedError` branch remains unreachable but explicit.
**Alternatives**:
| # | oracle layout | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | Reuse `data/camb_ref_planck2018.npz` for CAMB rows; reserve `tests/fixtures/fb6/...` for literature-digitized rows | Matches the existing LB-6 oracle path; keeps new FB-6-specific digitized inputs out of the production-style `data/` root until they actually exist. | Two roots appear in one table. | ✅ |
| 2 | Put every future oracle path under `data/` | One root for all files. | Blurs shipped external-code fixtures with future hand-curated digitizations and would imply new data landed when none did. | — |
**Core principles**: honest fixture-path reservation only; reuse the existing CAMB oracle; correct the 2009 figure locator instead of propagating a bad citation; no binary fixture data shipped in META.
**Skeleton path**: `htt/bass/integration/test_full_bianchi_coverage.py::test_fb63_literature_and_camb_oracle_fixtures`
**Test path**: `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/integration/test_full_bianchi_coverage.py -q`
**Guard rails** (yes/no): literature paths reserved under `tests/fixtures/fb6`? yes; CAMB rows reuse the shipped NPZ? yes; prompt's Fig. 4 mismatch corrected? yes; no new fixture data shipped? yes
**Regression after plant**: `3403 passed + 48 skipped`.
