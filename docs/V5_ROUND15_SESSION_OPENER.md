# V5-RUNTIME Round-15 — Session Opener

_Paste the block under **"PROMPT FOR NEXT SESSION"** at the bottom into a fresh
Claude session. Everything needed to resume Round-15 is inlined; no prior
context required._

---

## Cumulative state

**Branch**: `main`
**Latest commit**: `<TBD-after-this-commit>` (Round-15 §10 decisive test)
**Previous milestone**: `86e53ee` (Round-12→14 investigation chain — 23 files,
no production code changes; defect catalog D-1/D-2/D-3 documented)
**Production code HEAD invariant**: `0536f0e` (R12 Phase C) — no production
code change since Phase C.

**Fast baseline (still 1723 passed)**:
```bash
venv/bin/python -m pytest \
    htt/bass/los/ htt/bass/transport/ htt/bass/spectrum/ \
    htt/bass/forward/ htt/bass/validation/test_d2_regression_anchor.py \
    htt/bass/validation/test_verification_pack.py \
    htt/bass/validation/test_ver3_gate_stop.py \
    htt/bass/test_statistics.py htt/bass/runtime/test_ver2_execution.py \
    htt/bass/runtime/test_cosmological_config.py \
    htt/bass/perturbation/ \
    htt/bass/hierarchy/test_ver2_seed_compatibility.py \
    -m "not slow"
```

**Anchor invariants (DO NOT BREAK)**:
- Route-B Rust `D_2 = 1002.086744 μK²` (Rust binary
  `bass_rs dump_dl_spectrum_sparse`, MB-95 sync_gauge_camb.rs path) —
  bit-identical
- Route-B Python golden MM-curve (analytic, no PSTF) — bit-identical
- 43 CAMB cross-check tests at `b_k_sq=1.0`
  (`test_fb53_regular_adiabatic_ic_skeleton.py`) — bit-identical
- Fast baseline 1723 passed unchanged

**No CAMB runtime dependency in production code**. CAMB allowed as
audit/comparison oracle in `scripts/v5_round1*_*.py` diagnostics only.

## V5 DAG status (post Round-14)

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
| Round-9. D_ℓ linear-probe wrapper + B_K² convention | ✅ | 6 commits |
| Round-10. ν seed-formula fix (B_K_sq factor) | ✅ | `03efd18` |
| Round-11. eta_cov inner-amplitude fix | ✅ | `ee33a38` |
| R12 Phase C. B_K_sq semantic cleanup | ✅ | `0536f0e` |
| Round-12→14 investigation (no prod change) | ✅ | `86e53ee` |
| **Round-15 P0. D-1 LoS grid decoupling** | ⏸ | **next** |
| Round-15 P1. D-3 gauge fix | ⏸ | needs P0 |
| Round-15 P2. D-2 seed validity (multi-month) | ⏸ | needs P0+P1 |
| 5. CAMB cross-check | ⏸ | needs P0+P1+P2 |

## Round-12→14 investigation outcome (4 audit cycles, 10 verdicts)

**Three independent architectural defects** identified by external
auditor consensus (see `docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md`
for full prose):

- **D-1: IMEX/LoS grid conflation** (Round-15 P0, 1-2 weeks)
- **D-2: Lowell seed validity range** (Round-15 P2, multi-month)
- **D-3: Synchronous/Newtonian gauge mismatch** (Round-15 P1, sub-week)

**§10 decisive test result** (commit `<TBD>` HEAD):

`scripts/v5_round15_decisive_los_test.py` fed CAMB-computed Newtonian-
gauge `T_source(η, k)` directly through BASS's existing
`project_temperature_transfer` on the 64-uniform-linear η-grid.
Compared per-(k, ℓ) against CAMB's own direct Δ_T:

```
0/12 cells within 1.0 ± 5%
4/12 cells sign-flipped
5/12 cells |ratio| ∈ [10, 100]
1/12 cells |ratio| > 100   (k=1e-3 ℓ=4: ratio = +3687!)
median |ratio| = 8.30
max |ratio|    = 3687
```

**Case D confirmed** (per Claude Opus R14 §10 classification): even
with PERFECT CAMB sources, the BASS LoS projector + 64-uniform-linear
η-grid cannot reproduce CAMB Δ_ℓ. The 220 Mpc grid spacing aliases
high-ℓ Bessel oscillations; the 19 Mpc visibility FWHM has only 1
grid point inside it.

**Implication**: D-2 (seed amplitude) and D-3 (gauge) fixes are
**meaningless** until D-1 is resolved — even perfect upstream sources
can't survive the LoS projector pathology.

Full transcript: `docs/audits/diagnostic_transcripts_round12_to_14_2026-04-25/round15_decisive_los_test.txt`

## Round-15 P0 concrete scope (this session's task)

### Task: D-1 fix — decouple LoS η-grid from IMEX output

**Current architecture** (the bug):
```python
# In htt/bass/spectrum/flrw_pipeline.py::_los_and_wrap (line 306):
eta_grid = np.asarray(integration_result.eta, dtype=np.float64)  # 64 uniform-linear
eta_for_los = np.clip(eta_grid, 0.0, eta_0_mpc)
# This grid is reused for both source extraction AND LoS quadrature.
delta_T = project_temperature_transfer(
    float(k_mpc), source_T, eta_for_los, bessel_config,
)
```

**The bug**: `eta_for_los` has Δη=220 Mpc (uniform), but:
- Visibility g(η) FWHM ≈ 19 Mpc → only 1 grid point in recombination zone
- Bessel oscillation period at k=1e-1: 2π/k = 63 Mpc → undersampled
- Aliasing produces sign flips and 10-100× over-amplification (§10 test)

**Target architecture** (the fix):
```python
# New: bass.los.los_grid_builder
def build_los_grid(
    k: float,
    eta_today: float,
    eta_init: float,
    *,
    n_per_oscillation: int = 8,   # Nyquist-safe per Bessel period
    recomb_eta: float = 281.0,
    recomb_fwhm: float = 19.0,
    n_per_recomb_fwhm: int = 8,
    sparse_late_isw: bool = True,
) -> np.ndarray:
    """Per-k LoS quadrature grid composed of:
      1. Recombination-refined zone: [eta_init, recomb_eta + 5*FWHM]
         with Δη = recomb_fwhm / n_per_recomb_fwhm ≈ 2.4 Mpc
      2. k-adapted oscillation zone: [recomb_zone_end, eta_today]
         with Δη = (2π/k) / n_per_oscillation
      3. Late-ISW sparse zone (optional): coarser sampling once Bessel
         is well-resolved
    """
    ...
```

Then in `flrw_pipeline._los_and_wrap`:
```python
# Replace integrator-output η-grid with k-adapted LoS grid:
eta_for_los = build_los_grid(k_mpc, eta_0_mpc, eta_init=261.0)
# Sources are PCHIP callables; evaluate on new grid:
source_T_on_los = build_temperature_source(
    eta_for_los, sources, g_of_eta, kappa_of_eta,
)
delta_T = project_temperature_transfer(
    float(k_mpc), source_T_on_los, eta_for_los, bessel_config,
)
```

**Sources are already callables** (`sources.psi`, `sources.theta_0`, etc.
are `PchipInterpolator` instances built in
`tier_b_source_extraction.py`); they can be evaluated on any η grid
within the integration result's domain. No integrator changes needed
for D-1 fix.

### Validation gate (acceptance criteria for D-1 fix)

1. **§10 decisive test re-run**: `venv/bin/python scripts/v5_round15_decisive_los_test.py`
   - Pre-fix: 0/12 within 5%, 4/12 sign-flipped, max ratio 3687
   - Post-fix target: **≥ 8/12 within 5%, 0 sign flips, max ratio < 1.5**
   - Confirms BASS LoS projector + new grid is healthy (Case A)

2. **All 1723 fast tests still pass** (no regression)

3. **Anchor tests bit-identical**:
   - `test_fb53_regular_adiabatic_ic_skeleton.py` (43 tests + 9 R10/R11) — bit-identical
   - `test_d2_regression_anchor.py` (6 tests) — bit-identical
   - Route-B Rust `D_2 = 1002.086744` unchanged (independent path)

4. **BASS native α(k, ℓ)** (without CAMB): expect significant change vs
   pre-fix (D-1 was masking the source extractor errors). After D-1 fix,
   BASS native still wrong vs CAMB direct = expected (that's D-3 + D-2,
   tackled in P1/P2).

### Implementation hints

- **Pre-tabulate `j_ℓ(x)`** per ℓ on fine x-grid (CAMB does this in
  `bessels.f90 BesselJl_setup`). Use `scipy.special.spherical_jn` once
  per ℓ for x ∈ [0, 50] at 5000 points; cache as module-level array.
  Reduces the per-k cost of LoS projection from O(N_eta · scipy_call)
  to O(N_eta · interp).
- **Per-k grid size**: for typical k ∈ [1e-4, 1e-1], grid size ranges
  from ~100 (recombination + sparse late) to ~5000 (recombination +
  fine late for k=1e-1). Total compute increase per k: factor 3-50× vs
  current 64-point grid; offset by Bessel pre-tabulation savings.
- **Source callables already PCHIP-wrapped**: `sources.psi(eta_for_los)`
  works with any η grid in domain. No re-extraction needed per k.
- **g_of_eta, kappa_of_eta**: also evaluate on new grid via existing
  callables built in `flrw_pipeline.build_visibility_and_kappa_callables`.

### Optional refinement (defer if D-1 alone passes Case A)

If §10 test re-run still shows residual (e.g., Case A but with 5-15%
errors), consider:
- **Adaptive Bessel quadrature** instead of trapezoid
- **Composite Simpson rule** on the recombination-refined zone

But default trapezoid on the new grid should suffice based on Claude
Opus R14 toy experiment (§2 of `round14_audit04_opus.md`).

## Constraints (non-negotiable)

- **No CAMB import in production code**. CAMB stays in
  `scripts/v5_round1*_*.py` diagnostic scripts only. The `bass.*` and
  `htt.*` runtime trees must remain self-contained.
- All anchor invariants preserved (see top of doc).
- D-1 fix is **incremental and surgical**: new module + 2-3 line change
  in `_los_and_wrap`. No changes to integrator, source extractor, or
  seed code.
- Phase 1 commit ends with §10 test re-run showing Case A. If Case A
  not achieved, do NOT proceed to D-3 / D-2 — investigate the residual
  D-1 issue (e.g., grid construction details) instead.

## Quick start commands

```bash
# Baseline confirmation (~25 s, must show 1723 passed unchanged)
venv/bin/python -m pytest \
    htt/bass/los/ htt/bass/transport/ htt/bass/spectrum/ \
    htt/bass/forward/ htt/bass/validation/test_d2_regression_anchor.py \
    htt/bass/validation/test_verification_pack.py \
    htt/bass/validation/test_ver3_gate_stop.py \
    htt/bass/test_statistics.py htt/bass/runtime/test_ver2_execution.py \
    htt/bass/runtime/test_cosmological_config.py htt/bass/perturbation/ \
    htt/bass/hierarchy/test_ver2_seed_compatibility.py -m "not slow" -q

# §10 decisive test (~3 min) — pre-fix baseline
venv/bin/python scripts/v5_round15_decisive_los_test.py

# Quick BASS native α at k=1e-3 (~45 s) — for development iteration
venv/bin/python -c "
import sys; sys.path.insert(0, 'htt/src'); sys.path.insert(0, 'htt')
from bass.species.registry import SpeciesBackgroundRegistry
from bass.spectrum.flrw_pipeline import (
    FLRWPipelineConfig, compute_linear_probe_transfer_function,
)
sp = SpeciesBackgroundRegistry.from_planck2018()
cfg = FLRWPipelineConfig(L_max_tower=4, ell_max_transfer=4,
                         unit_amplitude_normalization=False)
tf = compute_linear_probe_transfer_function(sp, 1e-3, config=cfg, probe_b_k_sq=1.0)
print('BASS α at k=1e-3, ℓ=0..4 =', tf.delta_T_m0)
"
```

## Round-15 P1/P2 (after P0 lands)

After D-1 fix lands and §10 test passes Case A:

**P1 (D-3 gauge fix, sub-week)**:
- Expose synchronous-gauge `h_S'` from integrator state (modify
  `IntegrationResult` schema if needed)
- In `tier_b_source_extraction.py:225`:
  ```python
  theta0_g_synchronous = t_tower[:, _slot(0, 0)]
  # NEW: convert sync → Newt for ℓ=0 only
  theta0_g_newtonian = theta0_g_synchronous + h_S_dot / 6
  ```
- Validation: BASS native α(k, ℓ) → CAMB direct comparison ratio
  drops by factor ~10 vs post-D-1 baseline

**P2 (D-2 seed validity, multi-month)**:
- Two sub-options:
  - (D-2a) Push η_init to z ~ 10⁹ (η_init ~ 0.01 Mpc) +
    tight-coupling approximation in IMEX
  - (D-2c) Matching-asymptotic: analytic super-horizon seed →
    numerical sub-horizon at horizon crossing
- Both are multi-month work. Choose based on BASS team capacity.

After P0+P1+P2, BASS native α(k, ℓ) should match CAMB direct to ≤ 5%
across all probed (k, ℓ). Then PR-024b/c can proceed.

---

## PROMPT FOR NEXT SESSION

```
V5-RUNTIME Round-15 P0 (D-1 LoS grid decoupling) 진행해줘. 자세한 맥락은
`docs/V5_ROUND15_SESSION_OPENER.md` 를 먼저 읽어줘 — Round-12 → 14 investigation
chain (4 audit cycles, 10 verdicts) 의 결과로 확정된 D-1/D-2/D-3 defect 분해,
§10 decisive test 결과 (Case D — D-1 critical, max ratio 3687×), Round-15 P0
concrete scope (target architecture + validation gate), constraints
(BASS-native, no CAMB runtime dep), anchor invariants, quick start commands
모두 거기에 정리되어 있어.

핵심 사실 요약:
- HEAD = `<TBD-after-commit>` (Round-15 §10 결과 commit)
- Production code HEAD invariant = `0536f0e` (R12 Phase C 이후 production
  변경 없음)
- §10 test 결과: 0/12 cells within 5%, 4/12 sign-flipped, max ratio 3687×.
  → D-1 (LoS grid) 가 dominant defect. D-2/D-3 fix 는 D-1 fix 이전에는
  무의미 (perfect CAMB sources 도 BASS LoS projector + 64-uniform-linear
  grid 통과 못함).
- Round-14 4/4 auditor 가 Hybrid (CAMB import) 권장했으나 사용자 거부 →
  BASS-native 경로 유지. CAMB 는 audit/diagnostic oracle 만.

P0 구체 작업:
1. `bass/los/los_grid_builder.py` 신규 모듈 작성:
   `build_los_grid(k, eta_today, eta_init, *, n_per_oscillation=8,
                   recomb_eta=281, recomb_fwhm=19, n_per_recomb_fwhm=8,
                   sparse_late_isw=True) -> np.ndarray`
   복합 grid: 재결합 zone refined (Δη ≈ 2.4 Mpc) + k-adapted
   oscillation zone (Δη ≈ 2π/(k·8)) + sparse late-ISW.

2. `bass/los/flrw_bessel_projector.py`: pre-tabulate `j_ℓ(x)` per ℓ
   (CAMB BesselJl_setup analog, scipy.special.spherical_jn 5000-point
   x-grid). 모듈 레벨 cache.

3. `htt/bass/spectrum/flrw_pipeline.py::_los_and_wrap` (line ~306):
   2-3 line change. `eta_for_los = np.clip(eta_grid, ...)` 를
   `eta_for_los = build_los_grid(k_mpc, eta_0_mpc, eta_init=261.0)` 로
   교체. Source callables 는 이미 PchipInterpolator wrapped 이므로
   새 grid 에서 evaluation 가능.

Validation gate:
- `venv/bin/python scripts/v5_round15_decisive_los_test.py` 재실행.
  Pre-fix: 0/12 within 5%, max ratio 3687.
  Post-fix target: ≥ 8/12 within 5%, 0 sign flips, max |ratio| < 1.5.
- Fast baseline 1723 passed 유지
- 43 fb53 + 9 R10/R11 + 6 D_2 anchor tests bit-identical
- Route-B Rust 1002.086744 μK² unchanged (Rust independent path)

Constraints:
- NO CAMB import in `bass.*` or `htt.*` runtime trees. CAMB stays
  in `scripts/v5_round1*_*.py` diagnostic scripts only.
- D-1 fix 는 incremental + surgical. Integrator/seed/source extractor
  변경 없음. 새 모듈 + 2-3 line `_los_and_wrap` 변경.

진행 순서:
1. 우선 baseline + §10 pre-fix test 한번 돌려 현재 상태 확인
2. `bass/los/los_grid_builder.py` 모듈 design + 작성
3. Bessel pre-tabulation 추가 (성능 최적화)
4. `_los_and_wrap` 수정
5. §10 test 재실행 → Case A 도달 확인
6. Fast baseline 재확인
7. Single commit (D-1 fix module + projector update + pipeline integration)

P0 commit 후 P1 (D-3 gauge fix, sub-week) 진행. P2 (D-2 seed validity,
multi-month) 는 별도 long track.

시작: 우선 docs/V5_ROUND15_SESSION_OPENER.md 를 읽어 전체 맥락 복원.
이후 Quick start commands 의 baseline + §10 test 한 번 돌려 현재 상태가
session opener 와 일치하는지 확인. 그다음 D-1 fix 모듈 설계부터 시작해줘.
```
