# PR-023 Design Document — PSTF Metric (1+3 Covariant Scalar Sector)

> **Status**: 📝 **DESIGN (pre-audit)** — 2026-04-18
> **Target PR**: PR-023 (Phase 1 remaining single-largest, W=10)
> **Dependency**: PR-020 ✅, PR-021 ✅, PR-022a ✅, PR-022b ✅, PR-022c ✅
> **Recommendation**: **Sub-track 분할** (PR-022 pattern 재적용)

---

## §1. Motivation — sub-track 분할 권장

PR-023 이 포함해야 할 components:

1. **Metric state variables** — PSTF 1+3 covariant 형태로 `etak`, `σ`, (+ Z_{ab} preparation for Bianchi)
2. **Metric RHS** — `etakdot = dgq/2`, `sigmadot = −2ℋ·σ − dgs/k + etak`
3. **Fluid state + RHS** — `clxc`, `clxb`, `v_b`, RHS `−hdot/2`, `−k·v_b − hdot/2`, `−ℋ·v_b + c_s²·k·clxb`
4. **Background struct + injection** — ℋ(a), ρ_γ(a), ρ_ν(a), ρ_b(a), c_s²(a)
5. **Metric monopole source helper** — `pstf_metric_monopole_source()` 가 PR-022a placeholder 에 wire-up
6. **Fluid collision coupling** — `+opac·(3Θ_1 − v_b)/r_b` term 은 PR-022b collision 에 이미 구현, 연결만 필요

단일 PR 에 이 모든 것이 들어가면 anti-local-min 위험이 큼 (PR-022 에서 확인된 pattern).

### 1.1 Sub-track 분할안 (권장)

**PR-023a — PSTF metric state + RHS (W=4, target S=7)**
- Scope: `src/solver/pstf_primary/metric.rs`
- `MetricInputs`, `BackgroundQuantities` structs
- `pstf_metric_rhs()` — `etakdot`, `sigmadot` 계산
- `pstf_metric_monopole_source()` — `−hdot/6` export for PR-022a wire-up
- Metric state layout 에 `etak`, `σ` 배치 (metric block 11 DOF 중 [0]=etak, [1]=σ, 나머지는 Bianchi 용 reservation)
- G2 target: `etakdot`, `sigmadot`, `hdot`, `−hdot/6` 각각 MB-95 과 bit-identical

**PR-023b — Fluid (CDM + baryon) state + RHS (W=3, target S=7)**
- Scope: `src/solver/pstf_primary/fluid.rs`
- `FluidInputs`, `pstf_fluid_rhs()` — `clxc`, `clxb`, `v_b` RHS (collision drag 제외)
- Baryon-photon collision drag 는 PR-022b 에 이미 있음 — fluid RHS 는 free-streaming 유사 metric coupling 만
- PR-022b 의 baryon v_b drag 와 PR-023b 의 `vbdot = −ℋ·v_b + c_s²·k·clxb` 가 additive
- G2 target: fluid RHS full FLRW

**PR-023c — Full RHS composition + PR-022a G2 승격 (W=3, target S=8)**
- Scope: RHS dispatcher + **PR-022a metric placeholder wire-up**
- `pstf_full_rhs(state, dy, inputs, layout)` = free_streaming + collision + metric + fluid
- PR-022a 의 `metric_monopole_source = 0.0` 을 `pstf_metric_monopole_source()` 로 실제 wire-up
- **Retrospective G2 승격**: PR-022a test 를 재실행하여 full FLRW regression (MB-95 전체 RHS 와 bit-identical)
- **PR-022a score 7 → 8 retrospective 갱신** (G2 partial → full)

**합산**: W = 4 + 3 + 3 = **10** (원 PR-023 weight 유지)
Target W·S/10 = 2.8 + 2.1 + 2.4 = **7.3** (원 target 8.0 의 91.3%)

### 1.2 단일 PR 대비 위험-이익

| 항목 | 단일 PR-023 | 3 sub-track |
|---|---|---|
| 세션 수 | 1 (낙관) / 3+ (현실) | 3 (예측 가능) |
| 실패 시 rollback 범위 | 전체 | 해당 sub-track |
| G2 gate tightness | 중간 (metric+fluid+coupling 섞임) | 강함 (각 sub-track 별) |
| PR-022a G2 승격 | 같이 진행 | PR-023c 에서 명시적 |
| 배경 주입 복잡도 | 전체 동시 | PR-023a 에서 집중 |
| Anti-local-min 위험 | 높음 | 낮음 |

**결론**: Sub-track 분할 채택. 이 문서는 **PR-023a (metric state + RHS)** 에 집중.

---

## §2. Pre-audit — MB-95 metric RHS 정확한 구조

### 2.1 Momentum constraint (etakdot)

```
dgq = (4/3)·grho_γ · v_γ + (4/3)·grho_ν · v_ν + grho_b · v_b  [+ massive ν]
    = (4/3)·grho_γ · 4·Θ_1 + (4/3)·grho_ν · 4·N_1 + grho_b · v_b
    = (16/3) · (grho_γ · Θ_1 + grho_ν · N_1) + grho_b · v_b

etakdot = dgq / 2
```

여기서 `grho_γ`, `grho_ν`, `grho_b` 는 **comoving density × 3H₀²** 또는 유사 background 인자. MB-95 `CambBackground` struct 에서 주입. PSTF 에서 동일 convention 채택.

### 2.2 Shear evolution (sigmadot)

```
dgs = grho_γ · π_γ + grho_ν · π_ν [+ dgs_massive_ν]
    = grho_γ · 4·Θ_2 + grho_ν · 4·N_2
    = 4·(grho_γ · Θ_2 + grho_ν · N_2)

sigmadot = −2·ℋ · σ − dgs/k + etak
```

`ℋ = aH` (conformal Hubble). `etak = state[i_etak]` 는 MB-95 에서 state vector 에 저장되는 변수. PSTF 에서도 state 에 저장 (metric block 의 [0]).

### 2.3 Derived: hdot (algebraic, not in state)

```
hdot = 2·k·σ − 6·etakdot/k
     = 2·k·σ − 6 · [dgq/2] / k
     = 2·k·σ − 3·dgq/k
```

`hdot` 은 state 에 저장 안 됨. 매 RHS 평가마다 계산. PR-022a 의 `metric_monopole_source = −hdot/6` 으로 export.

### 2.4 `metric_monopole_source` 공식

```
−hdot/6 = −(2·k·σ − 3·dgq/k) / 6
        = −k·σ/3 + dgq/(2k)
        = −k·σ/3 + etakdot/k
```

Photon/neutrino ℓ=0 RHS:
```
dΘ_0/dη = −k·Θ_1 + metric_monopole_source
dN_0/dη = −k·N_1 + metric_monopole_source
```

이것이 PR-023a 의 핵심 output: `pstf_metric_monopole_source(state, inputs, layout) -> f64`.

---

## §3. PR-023a 구체 scope

### 3.1 State layout

Metric block (11 DOF) 내 배치:
```
metric[0] = etak    ← active, MB-95 equivalent
metric[1] = σ       ← active, shear scalar
metric[2..=10] = 0  ← reserved for Bianchi-I Z_{ab} tensor (Phase 4)
```

`PstfFlrwLayout` 에 accessor 추가:
```rust
impl PstfFlrwLayout {
    pub(crate) fn i_metric_etak(&self) -> usize { 0 }
    pub(crate) fn i_metric_sigma(&self) -> usize { 1 }
}
```

### 3.2 API

```rust
pub(crate) struct BackgroundQuantities {
    pub(crate) h_conformal: f64,  // ℋ = aH [Mpc⁻¹]
    pub(crate) grho_gamma: f64,   // photon comoving density factor
    pub(crate) grho_nu: f64,      // neutrino
    pub(crate) grho_b: f64,       // baryon
    // + massive ν 추가 가능 (PR-023a 에서는 optional, default 0)
}

pub(crate) struct MetricInputs {
    pub(crate) k: f64,
    pub(crate) bg: BackgroundQuantities,
}

pub(crate) fn pstf_metric_rhs(
    state: &[f64],
    dy: &mut [f64],
    inputs: &MetricInputs,
    layout: &PstfFlrwLayout,
);

/// Metric monopole source = −hdot/6 for wire-up into PR-022a.
pub(crate) fn pstf_metric_monopole_source(
    state: &[f64],
    inputs: &MetricInputs,
    layout: &PstfFlrwLayout,
) -> f64;

/// Compute dgq separately for test purposes.
pub(crate) fn pstf_momentum_constraint_dgq(
    state: &[f64],
    v_b: f64,  // baryon v_b from fluid sector (PR-023b)
    bg: &BackgroundQuantities,
) -> f64;

/// Compute hdot algebraically.
pub(crate) fn pstf_hdot(
    state: &[f64],
    v_b: f64,
    inputs: &MetricInputs,
    layout: &PstfFlrwLayout,
) -> f64;
```

### 3.3 Dependencies on other sectors

- **Baryon v_b**: metric RHS 는 `v_b` 값이 필요 (`dgq` 계산). Test 에서는 state 에 v_b 를 직접 주입. Production 에서는 `layout.inner.baryon_start + 2` 에서 읽음.
- **Photon/neutrino dipole, quadrupole**: Θ_1, Θ_2, N_1, N_2 필요. Test 에서는 PR-021 adiabatic IC 사용.

### 3.4 TDD gate (11 tests 예상)

**Identity (3 tests)**:
- `identity_dgq_matches_mb95` — photon + ν dipole + baryon v_b 에서 `dgq = (16/3)(ρ_γ·Θ_1 + ρ_ν·N_1) + ρ_b·v_b` bit-identical
- `identity_etakdot_matches_mb95` — `etakdot = dgq/2` bit-identical
- `identity_sigmadot_matches_mb95` — `−2ℋ·σ − dgs/k + etak` 수식 일치

**Limit (2 tests)**:
- `limit_zero_state_trivial` — state=0 에서 `etakdot=0`, `sigmadot=0`, `hdot=0`
- `limit_no_anisotropic_stress_sigma_decays` — Θ_2=N_2=0 (dgs=0), η=0 에서 `sigmadot = −2ℋ·σ` pure damping

**Regression (3 tests)** — **G2 full FLRW**:
- `regression_hdot_matches_mb95` — `hdot = 2·k·σ − 6·etakdot/k` 수식 (derived) bit-identical with MB-95 `camb_rhs:473` rel err < 1e-14
- `regression_monopole_source_matches_mb95` — `pstf_metric_monopole_source()` == `−hdot/6` bit-identical
- `regression_metric_rhs_multiple_k` — k ∈ {1e-4, 1e-2, 1e-1} 에서 etakdot, sigmadot MB-95 일치

**Channelwise (2 tests)**:
- `channelwise_photon_nu_untouched` — metric RHS 가 photon/ν dy 에 zero contribution
- `channelwise_fluid_untouched` — metric RHS 가 fluid (cdm, baryon) dy 에 zero contribution (fluid RHS 는 PR-023b scope)

**Caveat (1 test)**:
- `caveat_metric_block_reserved_for_bianchi` — metric[2..=10] 의 dy 가 0 유지 (PR-023a 에서는 사용 안 함)

**총 11 tests**.

### 3.5 Gate forecast

| Gate | 예상 | 근거 |
|---|---|---|
| G1 COMPILE | ✅ | 새 파일 추가 |
| **G2 FLRW (full)** | **✅** | `regression_metric_rhs_multiple_k` 이 direct MB-95 대조 |
| G3 PHYS | ✅ | Identity/limit/caveat |
| G4 CROSS | ✅ | MB-95 `camb_rhs:462-481` inline 대조 |

**Score: 7/10** forecast (G1+G2+G3+G4 모두 pass → cap 9, publication figure 없음 → 7).

Weighted: W=4 × S=7/10 = **W·S/10 = 2.8**. Phase 1 진행률: 40.6% → **43.3%**.

---

## §4. Anti-local-min triggers

1. **Background 주입 convention 혼재** — MB-95 의 `grho_γ` 가 `8πG·ρ·a²` 같은 특수 조합인지 확인. 2회 fail 시 STOP + `CambBackground` struct 재감사.

2. **k-dependent vs k-independent terms 혼동** — `etakdot`, `sigmadot` 에서 `etak/k`, `dgs/k`, `dgq/k` factor 가 정확한지 sign 포함 확인.

3. **v_b 위치 mismatch** — PR-022b 에서 baryon v_b = `baryon_start + 2`. Metric RHS 가 같은 위치를 read 해야 함. `identity_dgq_matches_mb95` 에서 catch.

---

## §5. PR-023a vs PR-023b 의 interface

PR-023a 는 fluid RHS 를 **포함하지 않음** (fluid 는 PR-023b). 그러나 metric RHS 는 **fluid state (v_b) 를 read** 해야 함. 이것은 dependency 방향:

```
PR-023a (metric) ← reads v_b ← (fluid state, 어디서든 주입)
PR-023b (fluid) ← reads σ, etak, photon/ν → writes fluid dy
```

PR-023a scope 에서는 v_b 를 **state 로부터 read** 만 하고, fluid 의 RHS 는 건드리지 않음. Test 는 v_b 를 직접 state 에 주입 (`state[baryon_start+2] = ...`).

---

## §6. PR-023c 의 retrospective G2 승격 계획

PR-023c 에서 PR-022a 의 G2 partial → full 승격 방법:

1. PR-022a 의 `regression_rhs_matches_mb95_freestream_kappa_zero` test 를 **derivative 로** 새 test 추가 (기존 test 는 그대로 유지):
   ```rust
   regression_rhs_matches_mb95_full_path_with_metric  // NEW
   ```
2. 이 test 는 PR-023a 의 `pstf_metric_monopole_source()` 를 호출하여 `RhsInputs::metric_monopole_source` 에 주입
3. MB-95 `camb_rhs` full path (opac=0) 와 모든 ℓ 에서 bit-identical
4. PR-022a score 7 → 8 **retrospective** (scoreboard 에서 footnote 추가, W·S/10 4.2 → 4.8, Δ=+0.6)

이것은 **sub-track 분할 전략의 최종 보상** — PR-022a 의 partial G2 "빚" 이 PR-023c 에서 청산됨.

---

## §7. Pre-PR checklist (PR-023a 착수 전)

- [x] MB-95 `camb_rhs:462-481` 의 metric RHS 구조 재감사 완료 (§2)
- [x] PSTF metric block (11 DOF) 중 [0]=etak, [1]=σ 배치 확정 (§3.1)
- [x] `BackgroundQuantities` struct 설계 (§3.2)
- [x] Sub-track 분할 결정 — PR-023a (metric) / PR-023b (fluid) / PR-023c (composition + PR-022a 승격) (§1.1)
- [ ] `h_conformal` 단위 확인 — MB-95 `bg.grho_*` 가 이미 ℋ 인자 포함하는지 분리인지
- [ ] Massive ν term 은 PR-023a 에서는 skip (future PR)

---

## §8. 즉시 다음 행동

동일 turn 내:
1. **PR-023a scaffold** — `src/solver/pstf_primary/metric.rs` 신설
2. `BackgroundQuantities`, `MetricInputs`, `pstf_metric_rhs`, `pstf_metric_monopole_source`, `pstf_hdot`, `pstf_momentum_constraint_dgq` 구현
3. 11 tests (§3.4 specification)
4. PstfFlrwLayout 에 `i_metric_etak`, `i_metric_sigma` accessor 추가
5. D_2 11th consecutive 재확인
6. `pr-023a.md` closure delta + scoreboard 갱신 (40.6% → 43.3%)

PR-023a 완료 후 동일 pattern 으로 PR-023b (fluid) → PR-023c (composition + PR-022a 승격) 진입.

---

*PR-023 sub-track 분할 문서. PR-022 pattern 재적용 — Phase 1 남은 single-largest PR (W=10) 을 3 sub-track 으로 안전하게 진행. PR-023c 에서 PR-022a 의 G2 partial 이 full 로 retrospective 승격 — sub-track 분할 전략의 최종 마무리.*
