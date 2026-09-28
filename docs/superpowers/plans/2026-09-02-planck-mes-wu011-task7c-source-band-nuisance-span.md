# PMG-WU-011 Task-7C Source-Band Convergence and Nuisance-Span Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans task by task. Keep every code step RED-first and preserve typed negative terminals.

**Goal:** Determine whether the high-source processed response converges beyond `ell=9` and whether any registered low-source local-boost response survives unrestricted high-ell nuisance on the retained `ell=2..5` carrier.

**Architecture:** Extend the Task-7B diagnostic module with reusable source-block caching, directional contraction, metric-weighted image geometry, and source-cutoff/resolution ladders. Do not alter the positive finite-sky API, the Task-5B registered Jacobian, or the authoritative simultaneous joint solver.

**Tech Stack:** Python 3.12, NumPy, SciPy, healpy 1.20.0, pytest, matplotlib, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-02-planck-mes-wu011-task7c-source-band-nuisance-span-design.md`

## Global Constraints

- Task-7B source head: `13d40cb4d600e9e5687f27f506aa978c77cbcfb7`.
- Task-7B terminal: `PASS_TASK7B_ATLAS_NO_CANDIDATE`.
- Best cut-sky baseline: `APODIZED_Z_WIDE_IDENTITY`.
- Metric `(-,+,+,+)`, `n=-e`, active `+beta`, `beta=v/c`, Doppler weight `d=1`.
- Extended source modes are signed first-order diagnostics only.
- No point inversion of the `99`-column augmented response.
- No raw Planck access, empirical beta, subtraction, global tilt, polarization, foreground exclusion, Bianchi attribution, or formal-dossier promotion.

---

### Task 1: Freeze directional and cutoff schemas with RED contracts

**Files:**
- Create: `htt/test_wu011_processed_boost_nuisance_span.py`
- Create: `.github/workflows/wu011-task7c-nuisance-span.yml`

**Interfaces:**
- Consumes: none at RED.
- Produces: import, direction registry, terminal, cutoff-registry contracts.

- [ ] **Step 1: Write failing import/registry tests**

```python
def _api():
    try:
        from obsstat import processed_boost_nuisance_span as api
    except ImportError as exc:
        pytest.fail(f"WU-011 Task-7C API missing: {exc}", pytrace=False)
    return api


def test_task7c_registries_are_frozen():
    api = _api()
    assert api.DIRECTION_IDS == ("X","Y","Z","D111","D1M11","D11M1")
    assert api.CORE_SOURCE_CUTOFFS == (9,12,16)
    assert api.Task7CTerminal.PASS_TASK7C_SOURCE_BAND_NOT_CONVERGED.value
```

- [ ] **Step 2: Add a dedicated workflow and verify RED**

The dependency setup must pass and the test must fail only because the module is absent.

- [ ] **Step 3: Commit**

```bash
git add htt/test_wu011_processed_boost_nuisance_span.py \
        .github/workflows/wu011-task7c-nuisance-span.yml
git commit -m "test(obsstat): freeze WU-011 Task-7C nuisance-span contracts"
```

---

### Task 2: Add reusable extended-block cache and directional contractions

**Files:**
- Create: `htt/obsstat/processed_boost_nuisance_span.py`
- Modify: `htt/obsstat/processed_boost_identifiability.py` only if a pure helper must be exported without changing semantics.
- Modify: Task-7C tests.

**Interfaces:**
- Consumes: Task-7B extended source blocks and Task-5B scientific Jacobian.
- Produces: `DirectionalResponse`, `ExtendedBlockCache`, direction registry.

- [ ] **Step 1: Write failing direction-normalization and contraction tests**

Require exact unit norms and verify linearity:

```python
J_(a b1+b b2) = a J_b1+b J_b2
K_(a b1+b b2) = a K_b1+b K_b2.
```

- [ ] **Step 2: Implement typed direction registry**

Use immutable `float64` vectors and content identities. Sign-reversed directions are deliberately omitted because image geometry is unchanged.

- [ ] **Step 3: Implement block caching**

Cache each `(operator_id,source_ell)` tensor exactly once and reuse it for all directions and cutoffs. The content hash must bind operator, source ell, metric, and map/harmonic replay settings.

- [ ] **Step 4: Implement metric-whitened directional matrices**

For direction `bhat`, contract the Cartesian axis first, then whiten:

```python
J_bhat = einsum("i,ioj->oj", bhat, J_tensor[:, :, 1:])
K_bhat_ell = einsum("i,ioj->oj", bhat, K_ell_tensor)
```

Use the retained output metric and per-source-ell metric.

- [ ] **Step 5: Run focused tests and commit**

```bash
git add htt/obsstat/processed_boost_nuisance_span.py \
        htt/test_wu011_processed_boost_nuisance_span.py
git commit -m "feat(obsstat): add directional source-response geometry"
```

---

### Task 3: Implement model-free nuisance projection and principal-angle audits

**Files:**
- Modify: production module and tests.

**Interfaces:**
- Produces: `DirectionalNuisanceResult`, metric SVD/projector helpers.

- [ ] **Step 1: Write failing rank and projection tests**

Full-sky high-ell numerical-floor blocks must not erase the exact low response. A synthetic high-nuisance matrix spanning the output must produce zero surviving rank.

- [ ] **Step 2: Implement thresholded image bases**

Use compact SVD with a frozen relative threshold. Return explicit ranks and refuse ambiguous floor crossings.

- [ ] **Step 3: Implement the model-free survivor**

```text
Q_K = orthonormal image basis of K_bhat(L)
P_K_perp = I-Q_K Q_K^T
J_surv = P_K_perp J_bhat.
```

Report low/high/surviving ranks, surviving Frobenius fraction, and principal angles. Do not construct a pseudoinverse for source coefficients.

- [ ] **Step 4: Test metric reparameterization invariance**

Rescale one low and one high source coordinate together with their source metrics; all image/rank/angle diagnostics must remain unchanged.

- [ ] **Step 5: Commit**

```bash
git add htt/obsstat/processed_boost_nuisance_span.py \
        htt/test_wu011_processed_boost_nuisance_span.py
git commit -m "feat(obsstat): add model-free high-ell nuisance projection"
```

---

### Task 4: Add source-cutoff and resolution convergence ladders

**Files:**
- Modify: production module and tests.

**Interfaces:**
- Produces: `SourceCutoffResult`, `Task7CAtlas`.

- [ ] **Step 1: Write failing cutoff-ladder tests**

Require ordered cutoffs `(9,12,16)`, per-ell blocks through 16, and exact nested cumulative column registries.

- [ ] **Step 2: Implement the core wide-mask ladder**

```text
nside=16, processing_lmax=17, L=9,12,16.
```

Report per-block norms, cumulative norms, last-block fractions, directional nuisance ranks, survivor ranks, and drifts.

- [ ] **Step 3: Add resolution controls**

At `L=12`, compare `nside=16` and `32` with `processing_lmax=17`. Bind the exact mask and transfer arrays into every operator identity.

- [ ] **Step 4: Add full/reference controls**

At `nside=16`, `L=12`, run `FULL_IDENTITY` and `APODIZED_Z_REFERENCE_GAUSSIAN`. Full-sky high-ell blocks must remain below a registered numerical-floor envelope.

- [ ] **Step 5: Implement terminal choice**

Return:

- `SOURCE_BAND_NOT_CONVERGED` if the highest-cutoff block fractions or rank/fraction drifts fail;
- `MODEL_FREE_NO_IDENTIFIED_SUBSPACE` if convergence passes and every direction has zero stable survivor rank;
- `MODEL_FREE_IDENTIFIED_SUBSPACE` only if convergence passes and every direction has a nonzero stable survivor.

Mixed directional outcomes are a typed blocker requiring a widened direction registry, not an averaged pass.

- [ ] **Step 6: Commit**

```bash
git add htt/obsstat/processed_boost_nuisance_span.py \
        htt/test_wu011_processed_boost_nuisance_span.py
git commit -m "feat(obsstat): add Task-7C source-cutoff convergence atlas"
```

---

### Task 5: Generate deterministic artifacts and perform dual audit

**Files:**
- Create: `scripts/observed_runs/run_planck_mes_wu011_nuisance_span.py`
- Create: `docs/research_program/post_pr327/planck_mes_wu011_task7c_nuisance_span_audit.md`
- Modify: dedicated workflow.

**Interfaces:**
- Produces: typed terminal, CSV/JSON/PNG/NPZ artifacts, manifest, exact-head artifact branch.

- [ ] **Step 1: Write failing artifact roundtrip tests**

Require source SHA, case/direction/cutoff registries, five separate figures, and manifest verification.

- [ ] **Step 2: Implement outputs**

At minimum:

```text
terminal.json
summary.json
source_block_norms.csv
directional_nuisance_span.csv
cutoff_convergence.csv
resolution_controls.csv
block_decay.png
nuisance_rank_vs_cutoff.png
surviving_fraction_vs_cutoff.png
principal_angles_vs_cutoff.png
resolution_drift.png
SHA256SUMS
```

- [ ] **Step 3: Run exact-head workflow and publish create-only artifact branch**

Preserve artifact ID, digest, branch, commit, and dependency versions.

- [ ] **Step 4: PHYS-MATH audit**

Check dimensions, metrics, rank thresholds, source-band nesting, fixed-direction contraction, and the distinction between deterministic nuisance and covariance-aware uncertainty.

- [ ] **Step 5: PHYS-MATH-CODE audit**

Check actual solver reuse, cache identity, no strict-positive API misuse, no pseudoinverse point estimate, typed negative terminals, and no raw-data path.

- [ ] **Step 6: Hostile figure audit**

Inspect every figure externally. A numerical table pass alone is insufficient for final closeout.

- [ ] **Step 7: Synchronize GitHub, Jira, Confluence, Dropbox, and research workspace**

Keep PR #444 draft. Read every control plane back at the same exact source head.

## Plan Self-Review

- The plan does not attempt an underdetermined 99-column point inverse.
- It separates cutoff convergence from model-free nuisance-span geometry.
- It preserves exact stored-real metrics and the scientific `T0` null.
- It uses wide apodization as the best cut-sky baseline and full/reference cases as controls.
- It postpones covariance-aware likelihood construction until source-band convergence and deterministic survivor status are known.
- Negative terminals are successful characterizations and cannot be recoded as implementation failures.
