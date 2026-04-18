# PR-024 Design Document — PSTF LoS Source + solve_pstf_spectrum

> **Status**: 📝 **DESIGN (pre-audit)** — 2026-04-18
> **Target PR**: PR-024 (Phase 1 remaining single-largest, W=12)
> **Dependency**: PR-020~022c ✅, PR-023 sub-track 전체 ✅
> **Recommendation**: **Sub-track 분할** (PR-022, PR-023 pattern 재적용)

---

## §1. Motivation — sub-track 분할 권장

PR-024 가 포함해야 할 components:

1. **LoS source function** — `pstf_source_function(state, dy, inputs, layout) -> SourceTerms` (PSTF state vector 에서 source channel 계산)
2. **ODE time integration** — k-mode 별로 η grid 를 따라 `pstf_full_rhs` 를 적분 (Rodas5P implicit solve 재사용)
3. **Source time grid** — 각 η 에서 source 값 저장 (LoS integral 용)
4. **LoS integral** — `∫dη S(k,η) j_ℓ(k(τ_0 − η))` — spherical Bessel + trapezoidal integration
5. **k-grid + spectrum assembly** — 여러 k 값에 대한 transfer function 계산 후 `C_ℓ = (4π/k³)|T_ℓ|² P(k) dk` 로 spectrum 조립
6. **Test: PSTF D_ℓ dump** — MB-95 oracle 과 비교 가능한 D_ℓ 결과 생성

단일 PR 에 모두 들어가면 anti-local-min 위험 높음. PR-022, PR-023 에서 확인된 분할 pattern 이 여기서도 적용:

### 1.1 Sub-track 분할안 (권장)

**PR-024a — PSTF source function (W=4, target S=7)**
- Scope: `src/solver/pstf_primary/source.rs`
- `PstfSourceInputs`, `pstf_source_function()` — PSTF state/dy 에서 SW + Dop + Quad + E + ISW channel 계산
- SSOT helpers (`core::ssot::polter`, `polter_dot`, `source_sw`, `source_isw`, `source_doppler`, `source_polter_quad`, `source_emode`) 재사용 — PR-010 이 이미 구축한 기반 활용
- G2 target: MB-95 `production_source_v1` 와 동일 input (state, dy, background) 에서 bit-identical 결과

**PR-024b — Time integration + source grid (W=4, target S=7)**
- Scope: `src/solver/pstf_primary/integrate.rs`
- `PstfKmodeResult { eta_grid, source_total, state_trajectory }`
- `pstf_solve_kmode(k, params, vis, layout) -> Result<PstfKmodeResult>` — Rodas5P 로 η 적분, 각 snapshot 에서 source 저장
- MB-95 `CommonProfile` / `eta_snap_grid` 재사용 (background + visibility 는 이미 있음)
- G2 target: 하나의 k 값에서 PSTF state trajectory 가 MB-95 equivalent trajectory 와 bit-identical (tolerance 1e-10)

**PR-024c — LoS integration + spectrum assembly (W=4, target S=8)**
- Scope: `src/solver/pstf_primary/los.rs` + `src/solver/pstf_primary/spectrum.rs`
- `pstf_los_integrate()` — spherical Bessel + trapezoidal
- `solve_pstf_spectrum()` — k-grid 순회 + `C_ℓ = (4π/k³)|T_ℓ|²P(k)` 조립
- Test: `dump_pstf_dl_spectrum_sparse` — PSTF 로 D_ℓ 생성
- G2 target: PSTF D_2 == MB-95 oracle D_2 = 1002.086744 (bit-identical)

**합산**: W = 4+4+4 = **12** (원 PR-024 weight 유지)
Target W·S/10 = 2.8 + 2.8 + 3.2 = **8.8** (원 target 9.6 의 91.7%, PR-022/PR-023 과 유사한 비율)

### 1.2 단일 PR vs 3 sub-track 비교

| 항목 | 단일 PR-024 | 3 sub-track |
|---|---|---|
| Scope | 1200+ 줄 single PR | 각 400~500 줄 |
| 실패 시 rollback 범위 | 전체 | 해당 sub-track |
| G2 gate tightness | source + integration + LoS + spectrum 섞여 모호 | 각 sub-track 별 명확 |
| First-try success 확률 | 낮음 (4 component 동시) | 높음 (각 독립) |
| MB-95 oracle 과의 비교 granularity | D_ℓ 만 | source (PR-024a), state (PR-024b), D_ℓ (PR-024c) — 3 layers |
| Anti-local-min 위험 | 높음 | 낮음 |

**결론**: Sub-track 분할 채택. 이 문서는 **PR-024a (source function)** 에 집중.

---

## §2. Pre-audit — MB-95 `production_source_v1` 재감사

### 2.1 SourceTerms struct (이미 존재)

`sync_gauge_camb.rs:285`:
```rust
pub(crate) struct SourceTerms {
    pub(crate) s_total: f64,    // SW + Dop + Quad + ISW(deferred)
    pub(crate) s_sw: f64,
    pub(crate) s_dop: f64,
    pub(crate) s_quad: f64,
    pub(crate) s_e: f64,
    pub(crate) polterdot: f64,   // For post-pass FD → polter_ddot
}
```

PSTF 에서도 동일 struct 재사용 — convention 통일로 PR-025 equivalence 비교 단순화.

### 2.2 Source channels (SSOT 이미 구축)

`src/source/registry.rs` (PR-010) 이 이미 SSOT 제공:
- `source_sw(inp: &SourceInputs) -> f64` — SW = g · (δ_γ/4 + 2·φ + η_MB/2)
- `source_isw(inp: &SourceInputs, exp_minus_tau: f64) -> f64` — **PR-024 에서는 deferred** (post-pass FD, MB-95 와 동일)
- `source_doppler(inp: &SourceInputs) -> f64` — [(σ+v_b)·g' + (σ̇+v̇_b)·g] / k
- `source_polter_quad(inp: &SourceInputs, polter_dot: f64) -> f64` — CAMB `s_quad`
- `source_emode(inp: &SourceInputs, conv: EmodeConvention) -> f64` — polter-based

**PR-024a 의 역할**: PSTF state/dy → `SourceInputs` 변환 + SSOT 호출. PSTF state 에서 추출:
- `theta0 = state[i_photon_i_m0(0)]`
- `theta2 = state[i_photon_i_m0(2)]`
- `e0, e2 = state[i_photon_e_m0(0/2)]`
- `vb = state[i_baryon_v_m0()]`
- `vbdot = dy[i_baryon_v_m0()]`
- `sigma = state[i_metric_sigma()]`
- `sigmadot = dy[i_metric_sigma()]`
- `eta_s = state[i_metric_etak()] / k`
- `phi = eta_s - bg.h_conformal * sigma / k` — from MB-95 `L334`
- `eta_mb = −2 · eta_s` — MB-95 `L335`
- `delta_g = 4·theta0` — MB-95 `L336`

### 2.3 MB-95 와의 bit-identical 보장

PR-010 Stage B 에서 `production_source_v1` 이 이미 SSOT helpers 를 사용하도록 port 완료됨 (주석 `polter / polterdot via SSOT helpers`). 따라서 동일 input 에서 SSOT 호출 → bit-identical guaranteed.

PR-024a 의 핵심은 **PSTF layout ↔ MB-95 CambLayout 의 1:1 매핑**:

```
MB-95                              ↔  PSTF
───────────────────────────────────────────────────────────
y[lay.i_etak]                      ↔  state[layout.i_metric_etak()]
y[lay.i_sigma]                     ↔  state[layout.i_metric_sigma()]
y[lay.theta(0)]                    ↔  state[layout.i_photon_i_m0(0)]
y[lay.theta(2)]                    ↔  state[layout.i_photon_i_m0(2)]
y[lay.e_mode(0)]                   ↔  state[layout.i_photon_e_m0(0)]
y[lay.e_mode(2)]                   ↔  state[layout.i_photon_e_m0(2)]
y[lay.i_vb]                        ↔  state[layout.i_baryon_v_m0()]
dy[lay.theta(2)] (pigdot 계산)     ↔  dy[layout.i_photon_i_m0(2)]
```

이 매핑은 PR-021 IC (state-level copy from MB-95) 에서 이미 검증된 구조. PR-024a 는 extraction 만 하면 되므로 **1-to-1 shallow logic** — first-try pass 가능성 높음.

---

## §3. PR-024a 구체 scope

### 3.1 PstfSourceInputs struct

MB-95 의 `SourceInputs` 를 PSTF layout 에서 읽어오는 helper. 실제로는 `source::registry::SourceInputs` 를 그대로 reuse — **새 struct 만들 필요 없음**. PSTF 전용 extractor 함수만 추가:

```rust
/// Extract SourceInputs from PSTF state + dy.
/// Mirrors MB-95 `production_source_v1:315-360` logic.
pub(crate) fn pstf_extract_source_inputs(
    state: &[f64],
    dy: &[f64],
    k: f64,
    bg: &BackgroundQuantities,
    layout: &PstfFlrwLayout,
) -> SourceInputs;
```

### 3.2 Main function

```rust
pub(crate) fn pstf_source_function(
    state: &[f64],
    dy: &[f64],
    k: f64,
    bg: &BackgroundQuantities,
    vis: &VisibilityAtSnap,  // g, g', g''  (reuse MB-95 struct)
    layout: &PstfFlrwLayout,
) -> SourceTerms;
```

Wraps:
1. `pstf_extract_source_inputs()` → `SourceInputs`
2. Call `source::registry::source_sw/doppler/polter_quad/emode()` with extracted inputs
3. `s_total = s_sw + s_dop + s_quad` (ISW deferred to post-pass FD, same as MB-95)
4. Return `SourceTerms { s_total, s_sw, s_dop, s_quad, s_e, polterdot }`

### 3.3 Dependencies

- `VisibilityAtSnap` — MB-95 `visibility_hyrec::VisibilityResult` snapshot. Already exists, reusable.
- `BackgroundQuantities` — PR-023a 이미 있음. Extended with `adotoa` if needed (MB-95 convention).

---

## §4. TDD gate (10 tests 예상)

### Identity (3 tests)
- `identity_phi_extraction_matches_mb95` — `phi = eta_s - adotoa*sigma/k` formula (MB-95 `L334`) 일치
- `identity_eta_mb_extraction_matches_mb95` — `eta_mb = −2·eta_s` (MB-95 `L335`)
- `identity_delta_g_extraction_matches_mb95` — `delta_g = 4·theta_0`

### Channel (4 tests) — **G2 regression**
- `regression_source_sw_matches_mb95` — SW channel 값이 MB-95 `production_source_v1` 의 SW 부분과 bit-identical (rel err < 1e-14)
- `regression_source_doppler_matches_mb95` — Doppler channel
- `regression_source_polter_quad_matches_mb95` — polter quad channel
- `regression_source_total_matches_mb95` — s_total (full assembly) bit-identical

### Channelwise (2 tests)
- `channelwise_source_no_isw` — ISW = 0 explicit (deferred to post-pass, same as MB-95)
- `channelwise_polterdot_export` — polterdot field 가 SSOT `polter_dot()` 와 일치

### Caveat (1 test)
- `caveat_pol_off_e_source_zero` — pol disabled layout 에서 s_e = 0

**총 10 tests**.

---

## §5. Gate forecast

| Gate | 예상 | 근거 |
|---|---|---|
| G1 COMPILE | ✅ | 새 파일, SSOT helpers 재사용으로 기존 회귀 없음 |
| **G2 FLRW (full)** | **✅** | `regression_source_total_matches_mb95` 이 direct bit-identical. PR-010 SSOT 기반이라 알고리즘적으로 same path |
| G3 PHYS | ✅ | Identity (phi, eta_mb, delta_g), channelwise (ISW 없음, polterdot), caveat (pol off) |
| G4 CROSS | ✅ | MB-95 `production_source_v1` inline 대조 (primary oracle) |

**Score: 7/10** forecast. W=4 × S=7/10 = **W·S/10 = 2.8** (forecast 정확).

Phase 1 진행률: 48.1% → **50.8%**.

**6 PR 연속 first-try success 가능성 — PR-024a 는 shallow extraction logic (새 physics 없음, SSOT 재사용) 이라 PR-022c/023a/023b 와 유사 난이도**.

---

## §6. Anti-local-min triggers

1. **Background convention 혼동** — MB-95 의 `bg.adotoa` (= ℋ) vs PR-023a 의 `h_conformal` (동일 값). Test 에서 두 convention 일치 확인 필수.

2. **`phi` formula sign** — MB-95 `L334`: `phi = eta_s - adotoa * sigma / k`. 이것은 **synchronous → Newtonian gauge transformation** 공식. PSTF 가 synchronous-equivalent 로 운영되므로 동일 공식 재사용. 단 phi 의 sign convention 이 여러 문헌에서 달라지는 경우 있음 — MB-95 public path 가 authoritative.

3. **`vis` 구조체 접근** — `g`, `g'`, `g''` 의 필드명이 MB-95 `VisibilityResult` 에서 `vis_at[i]`, `dot_vis_at[i]`, `ddot_vis_at[i]`. 이것을 그대로 PSTF 쪽에 넘기면 되므로 혼동 없을 듯.

---

## §7. Pre-PR checklist

- [x] MB-95 `production_source_v1` 구조 재감사 완료 (§2)
- [x] `source::registry` SSOT 이미 구축 확인 (PR-010 Stage B)
- [x] PSTF layout ↔ MB-95 layout 1:1 매핑 확정 (§2.3)
- [x] Sub-track 분할 결정 — PR-024a (source) / PR-024b (integration) / PR-024c (LoS + spectrum)
- [ ] `VisibilityAtSnap` 재사용 vs 새 struct 판단 (구현 시)
- [ ] `BackgroundQuantities` 가 `adotoa` 을 포함하는지 확인 — 이미 `h_conformal` 이 그것임

---

## §8. 즉시 다음 행동

동일 turn 내:

1. **PR-024a scaffold** — `src/solver/pstf_primary/source.rs` 신설
2. `pstf_extract_source_inputs()` + `pstf_source_function()` 구현
3. 10 tests (§4)
4. D_2 14th consecutive 재확인 (PSTF primary module 추가, production path 무접촉 예상)
5. `pr-024a.md` closure delta + scoreboard 갱신 (48.1% → 50.8%)

PR-024a 완료 후 동일 pattern 으로 PR-024b (integration) → PR-024c (LoS + spectrum) 진입. PR-024c 완료 시 **PSTF primary 가 MB-95 와 bit-identical D_2 = 1002.086744 μK² 생성** — Phase 1 의 technical capstone.

---

*PR-024 sub-track 분할 문서. Phase 1 최대 PR (W=12) 을 3 sub-track 으로 안전하게 진행. PR-024c 완료 시 PSTF primary 가 oracle D_ℓ spectrum 을 재현 가능 — 중간점검 plot 에서 확인한 ΛCDM shape 를 PSTF 로 생성하는 Phase 1 capstone 도달.*
