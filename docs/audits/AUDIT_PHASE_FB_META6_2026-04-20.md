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

Pending `FB-META-6.2`: cross-type continuity-limit skeleton.

## §FB-6.3

Pending `FB-META-6.3`: Pontzen-Challinor / CAMB oracle-fixture skeleton.
