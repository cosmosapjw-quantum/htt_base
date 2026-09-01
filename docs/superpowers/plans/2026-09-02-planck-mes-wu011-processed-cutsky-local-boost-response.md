# PMG-WU-011 Processed Cut-Sky Local-Boost Response Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and validate a content-bound synthetic processed local-observer boost response that follows the repository's real source-transfer, weighted joint-fit, post-fit commonization, and retained-carrier order.

**Architecture:** Add one focused `processed_boost_response` module that composes the already reviewed WU-010 Lorentz APIs with `planck_pr3_operator.fit_joint_cutsky_alm`. Use an exact finite pixel-space path, a first-order path, and a frozen `ell=0..6` coefficient Jacobian. Keep plotting and receipt generation in a separate synthetic runner.

**Tech Stack:** Python 3.10+, NumPy, SciPy, healpy, pytest, matplotlib, repository SHA/content-ID helpers.

**Spec:** `docs/superpowers/specs/2026-09-02-planck-mes-wu011-processed-cutsky-local-boost-response-design.md`

## Global Constraints

- Scientific base is PR #441 head `04680e99d56b9974fe1120854370af1fb94fb1d6`.
- WU-010 predecessor closeout is `29427a1f7f2c5d46e43ffe03053c4ac13e969228`.
- Metric is `(-,+,+,+)`; outward sky direction is `n=-e`; active observer boost is `+beta`; `beta=v/c`.
- Exact finite pullback is restricted to strictly positive thermodynamic blackbody temperature with Doppler weight `d=1`.
- Baseline order is `B_beta -> D_src -> pixel synthesis -> weighted joint ell=0..5 solve -> D_com -> H_ret`.
- The existing joint solver is authoritative; the Frisch--Waugh--Lovell form is a diagnostic only.
- Scientific stored-real and internal joint-fit real bases must never be conflated.
- Source Jacobian band is `ell=0..6`; fit band is `ell=0..5`; retained band is `ell=2..5`.
- No raw Planck access, observed rank, empirical beta fit, boost subtraction, global tilt, polarization, foreground exclusion, Bianchi attribution, or P01--P27 replay.
- Every production change starts from a failing test and ends with a focused commit.

---

## File Map

- Create `htt/obsstat/processed_boost_response.py`: typed source sky, processed operator, finite/linear evaluation, Jacobian, mutations, receipts.
- Create `htt/test_wu011_processed_boost_contract.py`: fast CI authority, zero-boost, linearization, basis, alias, and terminal tests.
- Create `tests/obsstat/test_processed_boost_response.py`: detailed regression and negative tests.
- Create `scripts/observed_runs/run_planck_mes_wu011_processed_boost_response.py`: deterministic synthetic runner and plot/receipt writer.
- Create `docs/research_program/post_pr327/planck_mes_wu011_processed_boost_audit.md`: final formula, runtime, SciSpace, Wolfram, plot, and claim-boundary audit.
- Generate `docs/generated/planck_mes_wu011_processed_boost_response/`: JSON/CSV/PNG artifacts with SHA-256 manifest.
- Modify PR #443 body, Jira `BASS-21`, Confluence pages `21823493` and `22151174`, and research workspace tab `07_WU011_Processed_Response_Plan` only after exact-head readback.

---

### Task 1: Freeze Authority, Bases, Schemas, and Typed Terminals

**Files:**
- Create: `htt/test_wu011_processed_boost_contract.py`
- Create: `tests/obsstat/test_processed_boost_response.py`
- Create: `htt/obsstat/processed_boost_response.py`

**Interfaces:**
- Consumes: `JOINT_CUTSKY_ESTIMATOR_ID`, `JointCutSkyOperator`, `real_alm_layout` from `htt.obsstat.planck_pr3_operator`.
- Produces: `ProcessedBoostTerminal`, `PositiveAbsoluteSkySpec`, `ProcessedBoostOperator`, scientific/internal basis adapters.

- [ ] **Step 1: Write the failing authority and import tests**

```python
from __future__ import annotations

import numpy as np
import pytest


def _api():
    try:
        from obsstat import processed_boost_response as api
    except ImportError as exc:
        pytest.fail(f"WU-011 API missing: {exc}", pytrace=False)
    return api


def test_wu011_authority_and_order_are_frozen() -> None:
    api = _api()
    assert api.WU010_CLOSEOUT_HEAD == "29427a1f7f2c5d46e43ffe03053c4ac13e969228"
    assert api.JOINT_ESTIMATOR_ID == "joint_weighted_real_harmonic_l0_l5_retain_l2_l5:v1"
    assert api.PROCESSING_ORDER == (
        "FINITE_OR_LINEAR_BOOST",
        "SOURCE_BEAM_PIXEL_TRANSFER",
        "HEALPIX_SYNTHESIS",
        "WEIGHTED_JOINT_L0_L5_SOLVE",
        "POSTFIT_TARGET_SOURCE_COMMONIZATION",
        "RETAIN_L2_L5",
    )


def test_wu011_scientific_and_joint_real_bases_roundtrip() -> None:
    api = _api()
    rng = np.random.default_rng(20260902)
    scientific = rng.normal(size=49)
    internal = api.scientific_to_joint_real(scientific, lmin=0, lmax=6)
    replayed = api.joint_to_scientific_real(internal, lmin=0, lmax=6)
    np.testing.assert_allclose(replayed, scientific, rtol=0.0, atol=0.0)
```

- [ ] **Step 2: Run the focused RED test**

Run:

```bash
cd htt_base/htt
pytest -q -m fast test_wu011_processed_boost_contract.py
```

Expected: collection failure containing `WU-011 API missing`.

- [ ] **Step 3: Implement the minimal schema and basis adapters**

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import numpy as np

from .planck_pr3_operator import JOINT_CUTSKY_ESTIMATOR_ID

WU010_CLOSEOUT_HEAD = "29427a1f7f2c5d46e43ffe03053c4ac13e969228"
JOINT_ESTIMATOR_ID = JOINT_CUTSKY_ESTIMATOR_ID
SOURCE_LMAX = 6
FIT_LMAX = 5
RETAINED_LMIN = 2
PROCESSING_ORDER = (
    "FINITE_OR_LINEAR_BOOST",
    "SOURCE_BEAM_PIXEL_TRANSFER",
    "HEALPIX_SYNTHESIS",
    "WEIGHTED_JOINT_L0_L5_SOLVE",
    "POSTFIT_TARGET_SOURCE_COMMONIZATION",
    "RETAIN_L2_L5",
)

class ProcessedBoostTerminal(str, Enum):
    PASS_SYNTHETIC_PROCESSED_RESPONSE = "PASS_SYNTHETIC_PROCESSED_RESPONSE"
    BLOCKED_BY_MOVED_AUTHORITY = "BLOCKED_BY_MOVED_AUTHORITY"
    BLOCKED_BY_BASIS_MISMATCH = "BLOCKED_BY_BASIS_MISMATCH"
    BLOCKED_BY_MISSING_ABSOLUTE_T = "BLOCKED_BY_MISSING_ABSOLUTE_T"
    BLOCKED_BY_OPERATOR_IDENTITY_MISMATCH = "BLOCKED_BY_OPERATOR_IDENTITY_MISMATCH"
    BLOCKED_BY_REPLAY_MISMATCH = "BLOCKED_BY_REPLAY_MISMATCH"
    BLOCKED_BY_LINEARIZATION_FAILURE = "BLOCKED_BY_LINEARIZATION_FAILURE"
    BLOCKED_BY_SIGN_MUTATION_SURVIVAL = "BLOCKED_BY_SIGN_MUTATION_SURVIVAL"
    BLOCKED_BY_RANK_DEFICIENCY = "BLOCKED_BY_RANK_DEFICIENCY"
    BLOCKED_BY_CONDITION_CEILING = "BLOCKED_BY_CONDITION_CEILING"
    BLOCKED_BY_TRANSFER_UNRESOLVED = "BLOCKED_BY_TRANSFER_UNRESOLVED"
    BLOCKED_BY_NUISANCE_DEFINITION = "BLOCKED_BY_NUISANCE_DEFINITION"
    BLOCKED_BY_ALIAS_UNCONTROLLED = "BLOCKED_BY_ALIAS_UNCONTROLLED"
    BLOCKED_BY_HISTORICAL_PARITY_FAILURE = "BLOCKED_BY_HISTORICAL_PARITY_FAILURE"
    NO_ADMISSIBLE_NEW_RESULT = "NO_ADMISSIBLE_NEW_RESULT"


def scientific_to_joint_real(values: object, *, lmin: int, lmax: int) -> np.ndarray:
    x = np.asarray(values, dtype=np.float64)
    expected = sum(2 * ell + 1 for ell in range(lmin, lmax + 1))
    if x.shape != (expected,) or not np.all(np.isfinite(x)):
        raise ValueError("scientific stored-real carrier has the wrong finite shape")
    out = x.copy()
    cursor = 0
    for ell in range(lmin, lmax + 1):
        cursor += 1
        for _m in range(1, ell + 1):
            out[cursor] *= math.sqrt(2.0)
            out[cursor + 1] *= -math.sqrt(2.0)
            cursor += 2
    return out


def joint_to_scientific_real(values: object, *, lmin: int, lmax: int) -> np.ndarray:
    x = np.asarray(values, dtype=np.float64)
    out = x.copy()
    cursor = 0
    for ell in range(lmin, lmax + 1):
        cursor += 1
        for _m in range(1, ell + 1):
            out[cursor] /= math.sqrt(2.0)
            out[cursor + 1] /= -math.sqrt(2.0)
            cursor += 2
    return out
```

- [ ] **Step 4: Run RED-to-GREEN authority tests**

Run the same focused command. Expected: PASS for authority and basis tests; all later tests remain absent.

- [ ] **Step 5: Commit**

```bash
git add htt/obsstat/processed_boost_response.py htt/test_wu011_processed_boost_contract.py tests/obsstat/test_processed_boost_response.py
git commit -m "test(obsstat): freeze WU-011 processed-response authority"
```

---

### Task 2: Build the Positive Source Sky and Source Transfer Path

**Files:**
- Modify: `htt/obsstat/processed_boost_response.py`
- Modify: `htt/test_wu011_processed_boost_contract.py`
- Modify: `tests/obsstat/test_processed_boost_response.py`

**Interfaces:**
- Consumes: `real_vector_to_alm` from `planck_pr3_operator`, healpy synthesis, WU-010 strict-positive pullback.
- Produces: `PositiveAbsoluteSkySpec`, `build_positive_sky_map`, `apply_source_transfer`.

- [ ] **Step 1: Write failing positivity and transfer-order tests**

```python
def test_positive_sky_refuses_nonpositive_samples_without_clipping() -> None:
    api = _api()
    coefficients = np.zeros(49)
    coefficients[4] = 100.0
    with pytest.raises(api.ProcessedBoostError, match="strictly positive"):
        api.PositiveAbsoluteSkySpec(
            monopole_temperature=1.0,
            scientific_coefficients=coefficients,
            source_lmax=6,
            nside=16,
            units="microK_CMB",
        )


def test_source_transfer_is_applied_after_boost() -> None:
    api = _api()
    spec = api.synthetic_reference_sky(nside=16)
    beta = np.array([2.0e-3, -1.0e-3, 1.5e-3])
    correct = api.source_convolved_finite_map(spec, beta, mutation=None)
    wrong = api.source_convolved_finite_map(spec, beta, mutation="TRANSFER_BEFORE_BOOST")
    assert np.linalg.norm(correct - wrong) > 0.0
```

- [ ] **Step 2: Verify RED**

Expected missing `PositiveAbsoluteSkySpec` and `source_convolved_finite_map`.

- [ ] **Step 3: Implement strict-positive synthesis**

Use the scientific-to-joint adapter, `real_vector_to_alm`, `healpy.alm2map`, and a pixel positivity certificate. Store immutable arrays and a canonical SHA-256 content ID. The constructor must reject `min(map)<=0`; it must never clip or offset automatically.

Implement source convolution as

```python
boosted = pullback_thermodynamic_temperature_field(
    target_directions,
    beta,
    spec.evaluate_intrinsic,
)
boosted_alm = hp.map2alm(boosted, lmax=spec.source_lmax, iter=0, pol=False)
source_alm = hp.almxfl(
    boosted_alm,
    operator.source_beam[:spec.source_lmax + 1]
    * operator.source_pixel_window[:spec.source_lmax + 1],
    inplace=False,
)
source_map = hp.alm2map(source_alm, nside=spec.nside, lmax=spec.source_lmax, pol=False)
```

The transfer-before-boost mutation must construct a separately identified source field and must never reuse the baseline operator ID.

- [ ] **Step 4: Run positivity, zero-beta, and transfer-order tests**

Expected: strict refusal for nonpositive samples, byte-stable zero-beta maps, and nonzero correct/mutated differential for a nonconstant transfer.

- [ ] **Step 5: Commit**

```bash
git add htt/obsstat/processed_boost_response.py htt/test_wu011_processed_boost_contract.py tests/obsstat/test_processed_boost_response.py
git commit -m "feat(obsstat): add positive source-sky processing"
```

---

### Task 3: Bind the Existing Joint Solver and Zero-Boost Replay

**Files:**
- Modify: `htt/obsstat/processed_boost_response.py`
- Modify: both WU-011 test files

**Interfaces:**
- Consumes: `build_joint_cutsky_operator`, `fit_joint_cutsky_alm`, source/target transfer arrays.
- Produces: `ProcessedBoostOperator`, `ProcessedBoostEvaluation`, `evaluate_processed_boost`.

- [ ] **Step 1: Write failing operator-identity and replay tests**

```python
def test_processed_operator_refuses_a_different_mask_from_joint_operator() -> None:
    api = _api()
    mask = api.synthetic_apodized_mask(nside=16)
    joint = api.build_registered_joint_operator(mask)
    changed = mask.copy(); changed[0] *= 0.5
    with pytest.raises(api.ProcessedBoostError, match="operator identity"):
        api.ProcessedBoostOperator.from_components(mask=changed, joint_operator=joint)


def test_zero_boost_matches_direct_fit_joint_cutsky_alm() -> None:
    api = _api()
    spec, operator = api.synthetic_reference_problem(nside=16)
    evaluated = api.evaluate_processed_boost(spec, operator, np.zeros(3), mode="FINITE")
    direct = api.direct_zero_boost_replay(spec, operator)
    np.testing.assert_allclose(
        evaluated.retained_coefficients,
        direct.retained_coefficients,
        rtol=0.0,
        atol=2.0e-12,
    )
    assert evaluated.operator_id == operator.content_id
```

- [ ] **Step 2: Verify RED**

Expected missing operator/evaluation types.

- [ ] **Step 3: Implement the operator wrapper**

`ProcessedBoostOperator.from_components` must validate:

- exact mask array equality and mask SHA against `JointCutSkyOperator`;
- `lmin=0`, `lmax=5`, `retained_lmin=2`;
- exact `JOINT_ESTIMATOR_ID`;
- positive transfer arrays covering `ell=0..6` for source synthesis and `ell=0..5` for commonization;
- target/source ratio no greater than `1+1e-10` in the fitted band;
- fixed `PROCESSING_ORDER` in its content hash.

`evaluate_processed_boost` must call `fit_joint_cutsky_alm`; it must not reproduce the normal-equation solve.

- [ ] **Step 4: Run zero-boost and moved-authority tests**

Expected: zero residual within the declared tolerance and typed refusal for mask/authority mutation.

- [ ] **Step 5: Commit**

```bash
git add htt/obsstat/processed_boost_response.py htt/test_wu011_processed_boost_contract.py tests/obsstat/test_processed_boost_response.py
git commit -m "feat(obsstat): bind WU-011 to the joint cut-sky solver"
```

---

### Task 4: Add the Processed First-Order Generator and Convergence Gate

**Files:**
- Modify: production module and both test files

**Interfaces:**
- Consumes: WU-010 `doppler_weight_one_scalar_pullback` or the reviewed first-order scalar generator, exact finite field pullback.
- Produces: `evaluate_processed_linear_response`, `finite_to_linear_diagnostic`.

- [ ] **Step 1: Write failing convergence and sign-mutation tests**

```python
def test_processed_finite_minus_linear_is_quadratic() -> None:
    api = _api()
    spec, operator = api.synthetic_reference_problem(nside=16)
    direction = np.array([0.4, -0.2, 0.3]); direction /= np.linalg.norm(direction)
    diagnostic = api.finite_to_linear_diagnostic(
        spec,
        operator,
        beta_direction=direction,
        amplitudes=(4e-4, 2e-4, 1e-4, 5e-5),
        fit_slice=slice(1, 4),
    )
    assert 1.8 <= diagnostic.residual_slope <= 2.2
    assert diagnostic.scaled_plateau_relative_spread <= 0.25


def test_processed_sign_and_omitted_dipole_mutations_remain_linear() -> None:
    api = _api()
    spec, operator = api.synthetic_reference_problem(nside=16)
    report = api.mutation_order_diagnostic(spec, operator)
    assert 0.8 <= report.wrong_sign_slope <= 1.2
    assert 0.8 <= report.omitted_dipole_slope <= 1.2
```

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Implement the linear path**

Evaluate the intrinsic scalar generator on the target pixel directions, then apply the same `D_src`, map synthesis, joint solve, post-fit commonization, and retained selection as the finite path. Do not call the strict-positive absolute-temperature API on the signed generator field.

Fit log residuals only when every norm is finite and positive. Refuse a slope fit if fewer than three preregistered points survive the numeric floor.

- [ ] **Step 4: Run focused convergence tests**

Expected: correct residual slope near two; sign and omitted-dipole mutations near one.

- [ ] **Step 5: Commit**

```bash
git add htt/obsstat/processed_boost_response.py htt/test_wu011_processed_boost_contract.py tests/obsstat/test_processed_boost_response.py
git commit -m "feat(obsstat): add processed boost linearization gate"
```

---

### Task 5: Build the `ell=0..6` Coefficient Jacobian and Alias Blocks

**Files:**
- Modify: production module and both test files

**Interfaces:**
- Produces: `ProcessedBoostJacobian`, `build_processed_boost_jacobian`, source/output registries.

- [ ] **Step 1: Write failing shape, rank, and alias tests**

```python
def test_processed_jacobian_has_registered_dimensions() -> None:
    api = _api()
    _spec, operator = api.synthetic_reference_problem(nside=16)
    result = api.build_processed_boost_jacobian(operator)
    assert result.tensor.shape == (3, 32, 49)
    assert len(result.source_registry) == 49
    assert len(result.output_registry) == 32
    assert result.ell6_alias_block.shape == (3, 32, 13)


def test_ell6_alias_is_nonzero_on_cut_sky_and_resolved() -> None:
    api = _api()
    _spec, operator = api.synthetic_reference_problem(nside=16)
    result = api.build_processed_boost_jacobian(operator)
    assert np.linalg.norm(result.ell6_alias_block) > 0.0
    assert np.all(np.isfinite(result.singular_values))
```

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Implement basis injection**

For each of 49 scientific source coordinates and each Cartesian beta basis vector, synthesize a positive reference sky by adding a fixed monopole large enough to preserve positivity. Compute the first-order retained response after subtracting the independently processed monopole response. Store the tensor in `(beta_axis, output, source)` order.

Use exact integer source-registry fields:

```python
@dataclass(frozen=True)
class ScientificMode:
    ell: int
    m: int
    component: str  # "REAL" or "IMAG"; m=0 uses REAL
```

The `ell=6` block is columns corresponding exactly to 13 registered coordinates.

- [ ] **Step 4: Run shape, alias, and deterministic-content tests**

- [ ] **Step 5: Commit**

```bash
git add htt/obsstat/processed_boost_response.py htt/test_wu011_processed_boost_contract.py tests/obsstat/test_processed_boost_response.py
git commit -m "feat(obsstat): add processed boost coefficient Jacobian"
```

---

### Task 6: Verify Nuisance Profiling and Historical Fixed-Axis Parity

**Files:**
- Modify: production module and both test files
- Read-only dependency: `htt/obsstat/boost_biposh_residual.py`

**Interfaces:**
- Produces: `weighted_fwl_retained_solution`, `historical_fixed_axis_parity`.

- [ ] **Step 1: Write failing full-solve/FWL and parity tests**

```python
def test_weighted_fwl_matches_the_simultaneous_joint_solve() -> None:
    api = _api()
    spec, operator = api.synthetic_reference_problem(nside=16)
    pixel_map = api.source_convolved_finite_map(spec, np.array([1e-3,0.0,0.0]), operator)
    full = api.evaluate_pixel_map_with_joint_solver(pixel_map, operator)
    fwl = api.weighted_fwl_retained_solution(pixel_map, operator)
    np.testing.assert_allclose(fwl, full.retained_coefficients, rtol=0.0, atol=3e-11)


def test_historical_fixed_axis_overlap_has_small_relative_residual() -> None:
    api = _api()
    report = api.historical_fixed_axis_parity(nside=64, lmax=24)
    assert report.domain_matched
    assert report.relative_l2_residual <= 2e-10
```

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Implement FWL as an audit-only calculation**

Compute `N`, `R`, and weighted projection on supported pixels. Do not route production outputs through FWL. Record nuisance rank four and refuse rank loss.

- [ ] **Step 4: Implement historical parity narrowly**

Use the exact solar-dipole axis and transfer convention declared by `ExactBoostOperator`. Compare pixel maps before masking and compare processed retained coefficients only when the source band, `nside`, and transfer are matched. Otherwise return a typed non-domain result instead of a numeric pass.

- [ ] **Step 5: Run focused tests and commit**

```bash
git add htt/obsstat/processed_boost_response.py htt/test_wu011_processed_boost_contract.py tests/obsstat/test_processed_boost_response.py
git commit -m "test(obsstat): close nuisance and fixed-axis parity gates"
```

---

### Task 7: Generate the Synthetic Receipt and Mandatory Plots

**Files:**
- Create: `scripts/observed_runs/run_planck_mes_wu011_processed_boost_response.py`
- Generate: `docs/generated/planck_mes_wu011_processed_boost_response/*`
- Create: `docs/research_program/post_pr327/planck_mes_wu011_processed_boost_audit.md`

**Interfaces:**
- Consumes: all prior WU-011 APIs.
- Produces: `processed_boost_response_receipt.json`, CSV matrices, plot PNGs, SHA-256 manifest.

- [ ] **Step 1: Write a failing runner contract test**

Require exact keys, terminal enum, source/operator identities, no observed-data fields, and plot manifest hashes.

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Implement the deterministic runner**

Freeze:

```python
NSIDE = 16
SOURCE_LMAX = 6
FIT_LMAX = 5
BETA_DIRECTIONS = np.eye(3)
BETA_AMPLITUDES = (4e-4, 2e-4, 1e-4, 5e-5)
CONDITION_CEILING = 1e8
```

Generate separate figures, never subplots:

- `finite_to_linear_residual.png`;
- `scaled_quadratic_plateau.png`;
- `mutation_residual.png`;
- `response_singular_values.png`;
- `response_matrix_beta_x.png`, `_beta_y.png`, `_beta_z.png`;
- `ell6_alias_matrix.png`;
- `mask_transfer_differentials.png`;
- `fwl_residual.png`;
- `historical_parity_residual.png`.

Each plot gets a SHA-256 recorded in the JSON receipt. Matrices are also saved as CSV with explicit row/column registries.

- [ ] **Step 4: Run the synthetic runner**

```bash
python scripts/observed_runs/run_planck_mes_wu011_processed_boost_response.py \
  --output docs/generated/planck_mes_wu011_processed_boost_response
```

Expected terminal: `PASS_SYNTHETIC_PROCESSED_RESPONSE` only when every output-bearing prerequisite passes. Otherwise emit the first typed blocker and omit dependent coefficients/plots.

- [ ] **Step 5: Inspect every plot and write the hostile audit**

The audit must state which curves establish `O(beta^2)`, which mutations remain `O(beta)`, whether singular values are stable, whether `ell=6` aliasing is controlled, and whether fixed-axis parity lies within tolerance.

- [ ] **Step 6: Commit**

```bash
git add scripts/observed_runs/run_planck_mes_wu011_processed_boost_response.py \
  docs/generated/planck_mes_wu011_processed_boost_response \
  docs/research_program/post_pr327/planck_mes_wu011_processed_boost_audit.md \
  htt/test_wu011_processed_boost_contract.py
git commit -m "research: add WU-011 synthetic processed-response receipt"
```

---

### Task 8: Final Verification, Dual Audit, and Cross-System Readback

**Files:**
- Modify only documentation/metadata after code freeze.

**Interfaces:**
- Produces: frozen implementation candidate, final document-closeout head, fresh reviews, synchronized GitHub/Jira/Confluence/workspace identities.

- [ ] **Step 1: Run focused verification**

```bash
cd htt_base
pytest -q htt/test_wu010_audit_closure.py \
          htt/test_wu010_harmonic_oracle.py \
          htt/test_wu011_processed_boost_contract.py
pytest -q tests/obsstat/test_lorentz_sky_pullback.py \
          tests/obsstat/test_boost_response.py \
          tests/obsstat/test_planck_lowell_irrep_projection.py \
          tests/obsstat/test_processed_boost_response.py
python scripts/observed_runs/run_planck_mes_wu011_processed_boost_response.py \
  --output docs/generated/planck_mes_wu011_processed_boost_response \
  --verify-existing
```

- [ ] **Step 2: Run repository gates**

Use the repository's PR04, PR07, and repository-integrity workflows. Preserve exact run IDs and job/step conclusions.

- [ ] **Step 3: Perform PHYS--MATH review**

Check signs, units, source/fit bands, positivity, finite/linear limits, mask transport, transfer noncommutation, nuisance treatment, and claim boundary.

- [ ] **Step 4: Perform PHYS--MATH--CODE review**

Check actual call graph, operator order, basis adapters, identities, typed terminals, mutation sensitivity, plot provenance, and no accidental use of observed data.

- [ ] **Step 5: Freeze the implementation candidate and update documentation only**

Record candidate head/tree, tests, runs, plots, and remaining limitations. A later documentation closeout must not change equations.

- [ ] **Step 6: Synchronize all control planes**

Update:

- PR #443 or the implementation successor PR body;
- Jira `BASS-21` status and exact head;
- Confluence pages `21823493` and `22151174`;
- research workspace tab `07_WU011_Processed_Response_Plan` and completion dashboard.

Read all four systems back and require identical head, terminal, claim ceiling, and next DAG node.

- [ ] **Step 7: Final commit**

```bash
git add docs/research_program/post_pr327/planck_mes_wu011_processed_boost_audit.md
git commit -m "docs: close WU-011 processed-response audit"
```

## Plan Self-Review

- Every v2 design lane W11-A through W11-J is assigned to a task.
- The plan follows the actual `fit_joint_cutsky_alm` order and never inserts a baseline filter absent from the repository path.
- All production tasks have an explicit RED command and expected failure.
- Scientific and internal real bases have named adapters and round-trip tests.
- Source completeness through `ell=6`, the `(3,32,49)` response tensor, and the `(3,32,13)` alias block are fixed.
- No placeholder, raw-data run, observed statistic, empirical beta, global tilt, polarization, Bianchi attribution, or formal-dossier promotion is present.
