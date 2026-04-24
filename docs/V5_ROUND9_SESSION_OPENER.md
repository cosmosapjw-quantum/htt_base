# V5-RUNTIME Round-9 — Session Opener

_Paste the block under **"PROMPT FOR NEXT SESSION"** at the bottom into a fresh Claude
session. Everything needed to resume Round-9 is inlined; no prior context required._

---

## Cumulative state (end of current session)

**Branch**: `main`
**Latest commit**: `ac48319` (Round-8 linear-probe API)
**Fast-baseline**: `1712 passed + 1 skipped + 3 slow-deselected` on
```
pytest htt/bass/los/ htt/bass/transport/ htt/bass/spectrum/ htt/bass/forward/ \
       htt/bass/validation/test_d2_regression_anchor.py \
       htt/bass/validation/test_verification_pack.py \
       htt/bass/validation/test_ver3_gate_stop.py \
       htt/bass/test_statistics.py \
       htt/bass/runtime/test_ver2_execution.py \
       htt/bass/runtime/test_cosmological_config.py \
       htt/bass/perturbation/ \
       htt/bass/hierarchy/test_ver2_seed_compatibility.py \
       -m "not slow"
```

**Anchor invariants (DO NOT BREAK)**:
- `D_2 = 1002.086744 μK²` (Route-B MM-curve) bit-identical
- `λ_max < 2e-15` across `L_max ∈ {4,6,8,12,16}` at γ_T ∈ {0, 1}
- Pre-V5 tests using `eta_initial_mpc=0.5` toy sentinel unchanged

## V5 DAG Option D status

| Step | Status | Commit |
|---|---|---|
| 1. multipole_cutoff validation | ✅ | `bce0eb9` |
| 2. IMEX cosmological stability | ✅ | `bce0eb9` |
| 3. Real IC injection path | ✅ | `e78e012` + `88f82fc` + `39fa085` |
| 4a. Tier-B → FLRWSourceTerms extractor | ✅ | `1aa2710` |
| 4b-core. LoS + k-sweep + D_ℓ + optimization | ✅ | `26b7dc2` + `0d8932d` + `08e8039` |
| 4b-(a). Super-horizon IC + b_k_sq knob | ✅ | `866d643` |
| Round-6. Visibility-bias isolation | ✅ | `04770ac` |
| Round-7. k-dependent P(k) callable | ✅ | `c2c0e19` |
| Round-8. Response regime map + linear-probe API | ✅ | `ac48319` |
| **Round-9. D_ℓ linear-probe wrapper + B_K↔ζ calibration** | ⏸ | **next** |
| 5. CAMB cross-check | ⏸ | needs Round-9 |

## Round-8 key findings (drive Round-9 design)

### Solver response regime map (measured 45 s sweep, 8 workers)

```
ℓ=2 at k=1e-3 Mpc⁻¹:
  b_k_sq = 0       →  Δ_T = −3.34e-3    pure visibility-source bias
  b_k_sq = 1e-10   →  Δ_T = −3.34e-3    BELOW bias noise floor
  b_k_sq = 1e-6    →  Δ_T = −3.34e-3    BELOW bias noise floor
  b_k_sq = 1e-3    →  Δ_T = −3.35e-3    edge of noise
  b_k_sq = 1.0     →  Δ_T = +9.38e-3    ✓ clean LINEAR regime
  b_k_sq = 100     →  Δ_T = +2.73e-1    mild saturation
  b_k_sq = 1e4     →  Δ_T = +4.06e+1    quadratic saturation
```

### Non-linearity root cause

`bass/perturbation/regular_adiabatic_ic.py::_seed_formulae`:

```
eta_cov = 2·B_K · (1 − x²/12 · (B_K − 10/denom))
```

The inner factor `(B_K − 10/denom)` introduces a **B_K²** term. At
`b_k_sq · x² ≫ 12` the quadratic dominates (saturation). For
`x² ≈ 0.068` (k=1e-3, η=260 Mpc), saturation threshold is
`b_k_sq ≈ 176`.

### Planck-2018 ζ problem

Physical ζ ≈ 4.6e-5 is BELOW the bias noise floor O(1e-3). Direct
extraction at physical amplitude gives zero / noise. **Linear-probe
extraction** is the pragmatic workaround: probe inside `[~1e-3, ~10]`,
extract the coefficient α(k), then scale analytically at C_ℓ assembly.

## Infrastructure Round-9 builds on

### Working APIs (all in `htt/bass/spectrum/flrw_pipeline.py`)

- `FLRWPipelineConfig` — config bundle with `primordial_b_k_sq`,
  `primordial_b_k_sq_fn`, `bias_subtraction`, `adiabatic_mode_seed`,
  `unit_amplitude_normalization`, etc.
- `compute_transfer_function_at_k(species, k, *, config, bianchi_type)`
  — single-k solver + extractor + LoS
- `compute_transfer_function_grid(species, k_grid, *, config, n_workers, chunked)`
  — parallel k-sweep, auto-chunks when N_k > n_workers
- `compute_linear_probe_transfer_function(species, k, *, config, probe_b_k_sq=1.0)`
  — **Round-8**: 2 parallel solver runs → returns α(k) per-unit-B_K_sq
- `compute_flrw_cl_tt(species, *, k_grid_mpc, pipeline_config, assembly_config, n_workers, bianchi_type)`
  — C_ℓ^TT/C_ℓ^EE assembly wrapper
- `compute_flrw_d_ell(...)` — D_ℓ assembly wrapper

### Helper patterns

- Parent-side k-dependent resolution: `_resolve_primordial_b_k_sq(cfg, k)`
- Parallel dispatch via `_worker_task` + `_worker_task_chunk` +
  `_worker_task_bias_pair` with fork-inherited globals
  `_WORKER_SPECIES`, `_WORKER_CONFIG`, `_WORKER_BIANCHI_TYPE`
- Chunked shared-bg path: `_run_chunk_shared_bg(species, k_values, *, cfg, bianchi_type)`
- Bias-subtracted grid: `_compute_transfer_function_grid_bias_subtracted(species, k_array, *, cfg, bianchi_type, effective)`
- Pair subtraction: `_subtract_transfer_functions(target, bias)` →
  returns `target − bias` element-wise on every Δ field

### Cost structure

- Per-k solver cost: ~42 s (IMEX integrator, dominates 98%)
- Per-k k-independent setup: ~0.8 s (amortizable via chunking)
- Parallel scaling: 7.7× on 4 workers (near-linear)
- For N_k=6 k-grid + 2 runs/k (linear-probe): 12 tasks / 8 workers = 2 × 45 s ≈ 90 s

## Round-9 concrete scope

### R9-A: `compute_flrw_d_ell_linear_probe` wrapper

Add to `htt/bass/spectrum/flrw_pipeline.py`:

```python
def compute_flrw_d_ell_linear_probe(
    species: SpeciesBackgroundRegistry,
    *,
    k_grid_mpc: np.ndarray,
    pipeline_config: FLRWPipelineConfig | None = None,
    assembly_config: CLAssemblyConfig | None = None,
    probe_b_k_sq: float = 1.0,
    n_workers: int | None = None,
    bianchi_type: str = "I",
) -> dict[str, Any]:
    """Run N_k parallel linear probes → α(k) grid → C_ℓ via analytic
    P_ζ(k) assembly. Returns bundle with k_grid, alpha_transfer_functions,
    cl_tt, cl_ee, d_tt, d_ee.
    """
```

**Implementation outline**:
1. For each k in `k_grid_mpc`, dispatch 2 parallel solver runs:
   `(k, b=0)` bias + `(k, b=probe_b_k_sq)` target.
2. Total = `2 × N_k` tasks; dispatch via `ProcessPoolExecutor(max_workers=effective)`
   with `effective = min(n_workers or cpu_count, 2·N_k)`.
3. Per k, compute α(k) = `(Δ_target − Δ_bias) / probe_b_k_sq`
   (same formula as `compute_linear_probe_transfer_function`).
4. Build `transfer_fn = _transfer_fn_from_grid(k_grid, alpha_list)`.
5. Call `assemble_cl_TT_isotropic(transfer_fn, assembly_config)` →
   uses `assembly_config.A_s × (k/k_pivot)^{n_s-1}` as P_ζ(k).
6. Apply `compute_dl(...)` → return bundle.

**Expected wall time** (Planck-2018, L_max=4, N_k=6, 8 workers):
~90 s (12 tasks / 8 workers = 2 rounds × 45 s).

### R9-B: Convention-audit diagnostic

Add a small script or slow test that runs `compute_flrw_d_ell_linear_probe`
and compares `D_2^output / D_2^{Route-B}` (= 1002.086744 μK²). This
empirically measures the B_K ↔ ζ conversion factor needed:

```
expected_ratio = 1.0  (if B_K_sq = ζ² in Lowell §13.2 convention)
observed_ratio = D_2_probe / 1002.086744
conversion_factor = sqrt(expected_ratio / observed_ratio)
```

The `conversion_factor` tells us what the true B_K ↔ ζ relationship is.
Possible outcomes:
- `conversion_factor ≈ 1`: B_K_sq is exactly ζ², calibration trivial.
- `conversion_factor = sqrt((k·η)²)` at horizon crossing: B_K_sq
  encodes a pre-growth factor.
- `conversion_factor = constant` independent of k: global scale
  mismatch.

### R9-C: Apply calibration + validate

Once the conversion factor is known (R9-B), either:
- Bake it into `FLRWPipelineConfig.primordial_b_k_sq_fn` default
- Or add a post-assembly `calibration_factor` kwarg to
  `compute_flrw_d_ell_linear_probe`

Validate: `D_2` within 10% (or whatever the k-grid quadrature error
allows) of Route-B. Increase N_k if needed for tighter accuracy.

### R9-D (optional, stretch)

If R9-B reveals a k-dependent correction, investigate Lowell §13.2 or
CAMB source code to determine the exact B_K ↔ ζ convention. The
`bass/perturbation/regular_adiabatic_ic.py::_seed_formulae` docstring
refers to "FB-5.3 regular-adiabatic startup vector" and "Lowell §13.2"
— these may have the explicit mapping.

## Constraints (non-negotiable)

- `D_2 = 1002.086744 μK²` Route-B bit-identical — any Round-9 change
  must preserve this anchor on the legacy path. New APIs should default
  off / preserve existing behavior.
- `1712 passed` baseline — no test regressions.
- No TCA pre-phase, FLRW UFA, photon RSA injection (CLAUDE.md §6
  approximation-free mandate).
- Any calibration factor discovery must be documented with the
  physical reference (Ma-Bertschinger / CAMB equation number /
  Lowell §13.2 paragraph).

## Quick start commands

```bash
# Baseline check (~25 s)
venv/bin/python -m pytest htt/bass/los/ htt/bass/transport/ htt/bass/spectrum/ \
    htt/bass/forward/ htt/bass/validation/test_d2_regression_anchor.py \
    htt/bass/validation/test_verification_pack.py htt/bass/validation/test_ver3_gate_stop.py \
    htt/bass/test_statistics.py htt/bass/runtime/test_ver2_execution.py \
    htt/bass/runtime/test_cosmological_config.py htt/bass/perturbation/ \
    htt/bass/hierarchy/test_ver2_seed_compatibility.py -m "not slow" -q

# V5 fast-check (~5 s)
venv/bin/python scripts/v5_operator_fast_check.py

# Cosmological smoke (~45 s, slow-marked)
venv/bin/python -m pytest -m slow htt/bass/runtime/test_cosmological_smoke.py

# Linear-probe single-k sanity (~45 s)
venv/bin/python -c "
import sys; sys.path.insert(0, 'htt/src'); sys.path.insert(0, 'htt')
from bass.species.registry import SpeciesBackgroundRegistry
from bass.spectrum.flrw_pipeline import compute_linear_probe_transfer_function
sp = SpeciesBackgroundRegistry.from_planck2018()
alpha = compute_linear_probe_transfer_function(sp, 1.0e-3, probe_b_k_sq=1.0)
print(f'α(k=1e-3) for T[ℓ=0..4] = {alpha.delta_T_m0}')
"
```

---

## PROMPT FOR NEXT SESSION

```
V5-RUNTIME Round-9 를 이어서 진행할게. 이전 세션에서 Round-8까지 완료됐고
commit `ac48319`로 반영됨. 자세한 맥락은 `docs/V5_ROUND9_SESSION_OPENER.md`
를 먼저 읽어줘 — 누적 commit 체인, Round-8의 핵심 발견 (solver 응답 regime
map, 비선형성 원인 규명, linear-probe API), Round-9 구체 범위 (R9-A
wrapper + R9-B convention audit + R9-C calibration apply), 불변성
(`D_2 = 1002.086744 μK²` bit-identical, 1712 baseline, λ_max < 2e-15)이
모두 거기에 정리돼 있어.

Round-8 landing 이후 주요 사실 요약:
- 솔버 응답이 `b_k_sq ∈ [~1e-3, ~10]`에서만 깨끗이 선형. 아래쪽은
  visibility-source bias (O(1e-3))에 묻히고, 위쪽은 `_seed_formulae`의
  eta_cov에 포함된 B_K² 항이 포화시킴 (threshold ~176 at k=1e-3, η=260).
- Planck ζ ≈ 4.6e-5는 bias noise floor 아래. 직접 추출 불가. Pragmatic
  path: linear regime에서 probe해서 coefficient α(k) 추출 후 C_ℓ
  assembly에서 P_ζ(k)로 analytic하게 스케일.
- 이걸 단일-k로 해주는 API가 `compute_linear_probe_transfer_function`
  (commit `ac48319`). 다음 할 일은 N_k 버전으로 확장.

Round-9 진행 순서:

  R9-A  `compute_flrw_d_ell_linear_probe(species, *, k_grid_mpc, ...)`
        wrapper를 `htt/bass/spectrum/flrw_pipeline.py`에 추가. 내부적으로
        `2 × N_k` parallel 태스크를 dispatch해 각 k에서 α(k) 추출 후
        `assemble_cl_TT_isotropic` + `compute_dl`로 D_ℓ 반환. 예상 wall
        time ≈ 90 s (N_k=6, 8 workers).

  R9-B  Convention audit diagnostic — R9-A wrapper를 Planck-2018 기본
        `A_s=2.1e-9, n_s=0.9649, k_pivot=0.05`로 돌려 `D_2^output /
        1002.086744` 비율을 측정. 이 비율이 B_K ↔ ζ 변환 인자를 알려줌.
        후보: (1) 1 (trivial); (2) (k·η_*)² (pre-growth factor); (3)
        k-independent 상수 (global scale).

  R9-C  Calibration 인자를 `FLRWPipelineConfig.primordial_b_k_sq_fn`
        기본값에 반영하거나 `compute_flrw_d_ell_linear_probe`에
        `calibration_factor` kwarg를 추가. 검증: D_2가 Route-B 앵커의
        10% 이내 (또는 k-grid quadrature error 수준).

  R9-D  (stretch) 필요하면 Lowell §13.2 또는 CAMB 소스 비교로 exact
        convention 확정.

불변성 유지:
  - `D_2 = 1002.086744 μK²` Route-B anchor bit-identical (legacy path)
  - 1712 fast baseline no regression
  - 새 API는 opt-in default OFF, 기존 동작 preserve

최적화 우선:
  - R9-A에서 `ProcessPoolExecutor` 병렬화 + fork-inherited species
    유지. `effective = min(cpu_count, 2·N_k)`로 worker 포화시키기.
  - Chunked shared-bg 재사용 고려 — 2개씩 묶어서 bias + target을 한
    worker가 sequential로 돌리면 0.8 s/k 재사용 절약. 단 병렬성 손실
    없는 경우에만 (2·N_k > n_workers일 때).

시작: 우선 docs/V5_ROUND9_SESSION_OPENER.md를 읽어 전체 맥락 복원. 이후
Quick start commands를 한 번 돌려 baseline이 그대로인지 확인. 그다음
R9-A 구현부터 시작해줘.
```
