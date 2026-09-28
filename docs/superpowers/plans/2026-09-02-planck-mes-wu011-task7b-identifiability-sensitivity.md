# PMG-WU-011 Task-7B Identifiability and Sensitivity Atlas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic cut-sky sensitivity atlas that identifies which mask, transfer, source sector, and out-of-band modes control the WU-011 processed local-observer boost response.

**Architecture:** Add one focused diagnostic module alongside Task-7A rather than changing the admitted positive-sky or production fit APIs. Reuse the Task-5B metric-whitened `(3,32,49)` Jacobian for registered modes, construct separate signed linear response blocks for source `ell=7..9`, and emit a content-bound case/sector atlas with a candidate-or-refusal terminal.

**Tech Stack:** Python 3.12, NumPy, SciPy, healpy 1.20.0, pytest, matplotlib, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-02-planck-mes-wu011-task7b-identifiability-sensitivity-design.md`

## Global Constraints

- Scientific branch: `changeset/planck-mes-wu011-processed-local-boost-response-20260902`.
- Task-7A predecessor: `b2422d9435eafbebd2584b747cb4b4ef9716caaf`.
- Metric `(-,+,+,+)`, sky direction `n=-e`, active boost `+beta`, `beta=v/c`, Doppler weight `d=1`.
- Production positive sky remains frozen at source `ell<=6`; extended `ell=7..9` modes are signed first-order diagnostics only.
- Production outputs continue to use `fit_joint_cutsky_alm`; no independent fit implementation.
- No raw Planck data, observed rank, empirical beta, subtraction, global tilt, polarization, foreground exclusion, Bianchi attribution, or formal-dossier promotion.
- Every code addition starts with a failing test and ends with exact-head workflow readback.

---

### Task 1: Freeze Task-7B schemas, case registry, and RED workflow

**Files:**
- Create: `htt/test_wu011_processed_boost_identifiability.py`
- Create: `.github/workflows/wu011-task7b-identifiability.yml`

**Interfaces:**
- Consumes: none at RED.
- Produces: import and registry contracts for `obsstat.processed_boost_identifiability`.

- [ ] **Step 1: Write the failing import and terminal tests**

```python
def _api():
    try:
        from obsstat import processed_boost_identifiability as api
    except ImportError as exc:
        pytest.fail(f"WU-011 Task-7B API missing: {exc}", pytrace=False)
    return api


def test_task7b_case_registry_and_terminals_are_frozen():
    api = _api()
    assert api.CI_CORE_CASE_IDS == (
        "FULL_IDENTITY",
        "BINARY_Z_IDENTITY",
        "APODIZED_Z_NARROW_IDENTITY",
        "APODIZED_Z_REFERENCE_IDENTITY",
        "APODIZED_Z_WIDE_IDENTITY",
        "APODIZED_Z_REFERENCE_MATCHED_GAUSSIAN",
        "APODIZED_Z_REFERENCE_GAUSSIAN",
    )
    assert api.Task7BTerminal.PASS_TASK7B_ATLAS_NO_CANDIDATE.value
```

- [ ] **Step 2: Add a dedicated workflow**

Run only the new test at RED. Expected: failure containing `WU-011 Task-7B API missing` while all dependency installation steps pass.

- [ ] **Step 3: Commit**

```bash
git add htt/test_wu011_processed_boost_identifiability.py \
        .github/workflows/wu011-task7b-identifiability.yml
git commit -m "test(obsstat): freeze WU-011 Task-7B atlas contracts"
```

---

### Task 2: Implement registered cut-sky cases and invariant sector diagnostics

**Files:**
- Create: `htt/obsstat/processed_boost_identifiability.py`
- Modify: `htt/test_wu011_processed_boost_identifiability.py`

**Interfaces:**
- Consumes: `build_joint_cutsky_operator`, `ProcessedBoostOperator`, `build_processed_boost_jacobian`, `metric_whitened_matrix`.
- Produces: `Task7BCaseSpec`, `Task7BCaseResult`, `build_task7b_case`, mask/transfer registries.

- [ ] **Step 1: Write failing case-construction tests**

```python
def test_task7b_registered_case_has_invariant_sector_diagnostics():
    api = _api()
    case = api.build_task7b_case(api.smoke_case_spec())
    assert case.jacobian_rank == 48
    assert np.isfinite(case.jacobian_nonzero_condition)
    assert sum(case.source_sector_frobenius_fractions) == pytest.approx(1.0)
    assert sum(case.weak_mode_sector_weights) == pytest.approx(1.0)
    assert 0.0 < case.f_sky_effective <= 1.0
```

- [ ] **Step 2: Verify RED**

Expected missing case types and builder.

- [ ] **Step 3: Implement masks and transfers**

```python
FULL: W=1
BINARY_Z: W=1[z>=0]
APODIZED_Z_NARROW: clip((z+0.225)/0.45,0,1)
APODIZED_Z_REFERENCE: clip((z+0.45)/0.90,0,1)
APODIZED_Z_WIDE: clip((z+0.75)/1.50,0,1)
```

Transfer registry:

```python
IDENTITY
MATCHED_GAUSSIAN
REFERENCE_GAUSSIAN
```

Use the same Gaussian coefficients as Task-7A. Record mean, quadratic, effective sky fraction, transition fraction, joint-normal condition, Jacobian condition, physical neighbour/alias norms, and content IDs.

- [ ] **Step 4: Implement singular-vector sector diagnostics**

For the metric-whitened anisotropy matrix `M=J_tilde[:,1:]`, compute compact SVD. Split the 48 right-singular coordinates into source `ell=1..6` blocks of widths `(3,5,7,9,11,13)`.

```python
F_ell = ||M[:,block_ell]||_F^2 / ||M||_F^2
p_ell = ||v_min[block_ell]||_2^2
```

Refuse nonfinite values or sums outside `2e-12` of unity.

- [ ] **Step 5: Run focused tests and commit**

```bash
git add htt/obsstat/processed_boost_identifiability.py \
        htt/test_wu011_processed_boost_identifiability.py
git commit -m "feat(obsstat): add cut-sky identifiability case diagnostics"
```

---

### Task 3: Add extended source-band leakage blocks

**Files:**
- Modify: `htt/obsstat/processed_boost_identifiability.py`
- Modify: `htt/test_wu011_processed_boost_identifiability.py`

**Interfaces:**
- Produces: `ExtendedSourceBlock`, `build_extended_source_block`, `ExtendedTailDiagnostic`.

- [ ] **Step 1: Write failing selection-rule and tail tests**

```python
def test_fullsky_extended_ell7_block_is_numerical_zero():
    api = _api()
    block = api.build_extended_source_block(api.smoke_fullsky_operator(), source_ell=7)
    assert block.metric_frobenius_norm <= block.fullsky_numerical_ceiling


def test_cutsky_extended_tail_is_content_bound():
    api = _api()
    tail = api.build_extended_tail(api.smoke_cutsky_operator(), ell_min=7, ell_max=8)
    assert tuple(row.source_ell for row in tail.blocks) == (7, 8)
    assert tail.cumulative_metric_frobenius > 0.0
    assert 0.0 <= tail.projection_fraction_into_registered_image <= 1.0
```

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Implement one-mode signed generator**

For a unit scientific stored-real source coordinate at fixed `ell`, build packed `alm`, evaluate `alm2map_der1`, and use

```text
delta_beta T = (beta.n)T - [beta-(beta.n)n].grad_S2 T.
```

Apply the exact registered source transfer, HEALPix synthesis, authoritative joint fit, post-fit commonization, and retained conversion. Require `processing_lmax >= source_ell+1`.

- [ ] **Step 4: Implement tail overlap diagnostics**

Stack metric-whitened blocks `ell=7..ell_max`. Let `Q_low` be an orthonormal basis for the registered `ell=1..6` response image. Report

```python
projection_fraction = ||Q_low Q_low.T K_tail||_F / ||K_tail||_F
principal_cosine = sigma_max(Q_low.T Q_tail)
minimum_principal_angle_degrees = arccos(clamp(principal_cosine,-1,1))
```

Full-sky extended blocks must converge to zero; cut-sky nonzero blocks are out-of-band leakage.

- [ ] **Step 5: Run focused tests and commit**

```bash
git add htt/obsstat/processed_boost_identifiability.py \
        htt/test_wu011_processed_boost_identifiability.py
git commit -m "feat(obsstat): add extended source-band leakage diagnostics"
```

---

### Task 4: Build the deterministic atlas and candidate/refusal terminal

**Files:**
- Modify: `htt/obsstat/processed_boost_identifiability.py`
- Create: `scripts/observed_runs/run_planck_mes_wu011_identifiability_atlas.py`
- Modify: `.github/workflows/wu011-task7b-identifiability.yml`
- Modify: `htt/test_wu011_processed_boost_identifiability.py`

**Interfaces:**
- Produces: `Task7BAtlas`, `Task7BArtifactBundle`, `build_task7b_atlas`, `write_task7b_artifacts`, `verify_task7b_artifacts`.

- [ ] **Step 1: Write failing atlas and artifact tests**

Require seven ordered cases, deterministic terminal, exact source revision, finite tables, five separate figures, and SHA-256 manifest verification.

- [ ] **Step 2: Implement terminal semantics**

A case is a numerical candidate only if rank 48, condition `<=100`, `ell6_alias_to_neighbor<=1`, and cumulative `ell7..9` tail/neighbour `<=1`. Return `PASS_TASK7B_ATLAS_CANDIDATE_FOUND` if any case passes, otherwise `PASS_TASK7B_ATLAS_NO_CANDIDATE`. A no-candidate result is not an execution failure.

- [ ] **Step 3: Implement outputs**

Write:

```text
terminal.json
summary.json
cases.csv
sector_participation.csv
extended_source_leakage.csv
gate_ratios.csv
condition_vs_mask.png
alias_and_tail_vs_case.png
weak_mode_sector_weights.png
source_sector_frobenius_fractions.png
extended_leakage_decay.png
SHA256SUMS
```

- [ ] **Step 4: Update workflow and run exact-head CI**

The workflow must run the focused tests, generate the atlas under `artifacts/wu011-task7b`, verify the manifest, upload an Actions artifact, and create a create-only exact-head artifact branch.

- [ ] **Step 5: Commit**

```bash
git add htt/obsstat/processed_boost_identifiability.py \
        htt/test_wu011_processed_boost_identifiability.py \
        scripts/observed_runs/run_planck_mes_wu011_identifiability_atlas.py \
        .github/workflows/wu011-task7b-identifiability.yml
git commit -m "research: add WU-011 Task-7B identifiability atlas"
```

---

### Task 5: Audit, synchronize, and choose the next node

**Files:**
- Create: `docs/research_program/post_pr327/planck_mes_wu011_task7b_identifiability_audit.md`
- Update metadata only after code freeze.

**Interfaces:**
- Produces: exact-head audit, GitHub/Jira/Confluence/Dropbox readback, and next DAG decision.

- [ ] **Step 1: Perform PHYS-MATH audit**

Check dimensions, units, stored-real metrics, singular-vector sector sums, source-band selection rules, mask/transfer separation, and full-sky zero controls.

- [ ] **Step 2: Perform PHYS-MATH-CODE audit**

Check actual call graph, no raw-data path, content hashes, no use of strict-positive finite API for signed extended modes, and no implicit replacement of the authoritative joint solve.

- [ ] **Step 3: Inspect every figure**

Identify which cases improve conditioning, whether apodization suppresses high-ell leakage, whether matched transfer helps, which source sector dominates the weak singular vector, and whether any numerical candidate survives.

- [ ] **Step 4: Synchronize exact head**

Update PR #444, Jira `BASS-21`, Confluence pages `21823493`, `22151174`, `22347781`, and Dropbox `/bianchi/htt_base/WU011_TASK7B_20260902`. Read all systems back.

- [ ] **Step 5: Choose next node**

- Candidate found: `TASK7C_COVARIANCE_AWARE_RESPONSE_VALIDATION`.
- No candidate and high-ell tail dominates: `TASK7C_AUGMENTED_SOURCE_BASIS_AND_MARGINALIZATION`.
- No candidate but mask choice controls the failure: `TASK7C_MASK_APODIZATION_OPERATOR_REDESIGN`.

## Plan Self-Review

- The plan preserves the positive absolute-sky API and isolates signed high-ell diagnostics.
- All seven registered cases are specified exactly.
- Metric and source-sector definitions are invariant and typed.
- Full-sky zero controls and cut-sky leakage are not conflated.
- Candidate thresholds are explicitly engineering-only and cannot authorize inference.
- Every implementation task has RED, GREEN, and commit steps.
