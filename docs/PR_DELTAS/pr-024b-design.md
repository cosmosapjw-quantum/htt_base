# PR-024b Design Document — PSTF Time Integration + Source Grid

> **Status**: 📝 **DESIGN (pre-audit)** — 2026-04-18
> **Target PR**: PR-024b (sub-track b of PR-024)
> **Dependency**: PR-020~023c ✅, PR-024a ✅
> **Weight**: 4
> **Target score**: 7

---

## §1. Scope

PSTF state 를 η grid 위에서 시간 적분하여 snapshot 별 state trajectory + source grid 생성. PR-024a 의 `pstf_source_function` 을 각 snapshot 에서 호출. PR-024c (LoS + spectrum) 의 input 이 될 `PstfKmodeResult` 생성.

### 포함된 것
- `src/solver/pstf_primary/matrix.rs` (예상 ~200 줄)
  - `build_pstf_matrix_into(k, tau, bg, coll_params, cs2b, layout, out: &mut [f64])` — `M(τ)` coefficient matrix for linear RHS, `n_state × n_state` flat form
  - Column-by-column construction via `pstf_full_rhs(state=e_j)` — RHS linearity exploited
- `src/solver/pstf_primary/integrate.rs` (예상 ~300 줄)
  - `PstfKmodeResult` struct (CambKmodeResult mirror)
  - `pstf_solve_kmode(k, common, params, layout, ic) -> Result<PstfKmodeResult, String>` — Rodas5P 시간 적분 + snapshot source collection
- 기존 `CommonProfile` + `integrate_linear_profile_rodas5p` (MB-95 경로) 재사용

### 포함되지 않은 것
- LoS integral: PR-024c
- C_ℓ spectrum assembly: PR-024c
- k-grid parallel solve: PR-024c
- ISW post-pass FD: future

---

## §2. Pre-audit — Approach 선택

### 2.1 Jacobian gap 분석

**Critical finding**: `pstf_analytical_jacobian` (PR-022c) 은 **free-streaming + collision** sector 만 포괄. PR-023a (metric RHS), PR-023b (fluid RHS), PR-023c (hdot-derived metric_monopole_source) 의 기여는 Jacobian 에 없음.

따라서 PR-022c Jacobian 을 그대로 쓰면 `metric_monopole_source`, metric, fluid 반영 못 함 → MB-95 equivalence 불가능.

### 2.2 3 approach 비교

| Approach | Pros | Cons | 선택 |
|---|---|---|---|
| **A. Jacobian 확장** (PR-023a/b/c 추가) | 깔끔, 재사용성 | 큰 scope, PR-024b 벗어남 | ✗ |
| **B. Callback-based stepper** (generic RK) | 가장 간단 | MB-95 stepper 다르면 bit-identical 불가 | ✗ |
| **C. Unit-vector matrix build** (pstf_full_rhs 로) | MB-95 stepper 재사용, linear RHS 활용 | per-snapshot n_state calls (overhead) | ✅ |

**선택: Approach C** — `pstf_full_rhs` 의 linearity 를 활용하여 각 τ snapshot 마다 coefficient matrix 를 column-by-column 구성. MB-95 와 **동일한 `integrate_linear_profile_rodas5p` stepper** 사용 → 수치 오차 source 동일.

### 2.3 Linearity 정당화 (PR-022c 증거)

PR-022c 의 `jacobian_fd_check` test 가 `pstf_free_streaming_rhs` + `pstf_thomson_collision` 이 상태 독립 Jacobian (linear) 임을 5-point FD 로 검증. 이후 추가된 PR-023a/b/c 도 state 에 선형:
- `pstf_metric_rhs`: dgq, dgs 는 state 의 linear combination, sigmadot 은 σ, etak 의 linear combination
- `pstf_fluid_rhs`: clxcdot = −hdot/2 (hdot 이 linear), vbdot = −ℋ·v_b + cs2b·k·clxb (linear)
- `pstf_full_rhs`: 4 sector 합산 — linear + linear = linear

따라서 `pstf_full_rhs(state, dy, inputs, layout)` 이 linear. Unit-vector decomposition 으로 exact coefficient matrix 복원 가능:

```
M(τ)[:, j] = pstf_full_rhs(state = e_j, inputs, layout)   // e_j: unit vector
```

구현:
```rust
pub(crate) fn build_pstf_matrix_into(
    k: f64, tau: f64,
    bg: &BackgroundQuantities,
    kappa_dot: f64, r_b: f64,
    cs2b: f64,
    layout: &PstfFlrwLayout,
    out: &mut [f64],  // n_state × n_state, column-major or row-major
) {
    let n = layout.n_state;
    assert_eq!(out.len(), n * n);
    out.fill(0.0);
    
    let inputs = FullRhsInputs {
        k, tau, bg: *bg,
        kappa_dot, r_b,
        use_pol_feedback: false,  // production default
        frame: FrameConvention::ElectronRestFrame,
        cs2b,
    };
    
    let mut state = vec![0.0_f64; n];
    let mut dy = vec![0.0_f64; n];
    for j in 0..n {
        state.fill(0.0);
        state[j] = 1.0;
        dy.fill(0.0);
        pstf_full_rhs(&state, &mut dy, &inputs, layout);
        // Column j of M: M[i, j] = dy[i] for state = e_j
        for i in 0..n {
            out[i * n + j] = dy[i];   // row-major (matches integrate_linear_profile_rodas5p)
        }
    }
}
```

**Cost**: n_state × n_snaps `pstf_full_rhs` calls per k-mode. For n_state ≈ 300, n_snaps ≈ 200 → ~60,000 evals. 이것은 PR-024b 의 "build mats_flat" 단계. 기존 MB-95 의 `build_camb_matrix_into` 는 더 빠른 analytic form 사용하지만 PR-024b 에서는 correctness-first (performance optimization 은 future PR).

---

## §3. Layout Accessor Range Check (PR-024a 교훈)

PR-024a 에서 E-mode layout ℓ<2 panic 이 발생했으므로 **본 PR 에서 touch 하는 모든 layout accessor 의 허용 ell range 를 명시**:

### 3.1 사용하는 accessor 리스트

| Accessor | 허용 ell range | PR-024b 에서 touch 하는가 |
|---|---|---|
| `i_metric_etak()` | scalar | ✅ (state extraction, matrix build) |
| `i_metric_sigma()` | scalar | ✅ |
| `i_photon_i_m0(ell)` | ell ∈ [0, ell_max_gamma] | ✅ (unit vector loop over all j) |
| `i_photon_e_m0(ell)` | **ell ∈ [2, ell_max_gamma]** | ✅ (pol on 시 only, 2..=lg loop) |
| `i_photon_b_m0(ell)` | **ell ∈ [2, ell_max_gamma]** | ✅ (pol on 시 only) |
| `i_neutrino_m0(ell)` | ell ∈ [0, ell_max_nu] | ✅ |
| `i_baryon_delta()` | scalar | ✅ |
| `i_baryon_v_m0()` | scalar | ✅ |
| `i_cdm_delta()` | scalar | ✅ |
| `i_cdm_v_m0()` | scalar | ✅ (v_c = 0 sync gauge, but index valid) |

### 3.2 Unit vector loop range

`build_pstf_matrix_into` 의 unit vector loop `for j in 0..n_state` 는 **모든 state slot** 을 iterate. 이것은 각 slot 이 "valid position in state array" 면 문제 없음 — accessor assertion 이 발동하는 것은 accessor 를 **특정 ell 로 호출할 때**, 단순히 state[j] 를 읽고 쓰는 것은 항상 안전.

따라서 column-by-column matrix build 에서 layout accessor range 문제 발생하지 않음. `pstf_full_rhs` 내부에서 호출되는 accessor 들만 주의하면 됨. `pstf_full_rhs` 는 PR-023c 에서 이미 검증됨 (accessor assertion 발동 없음).

### 3.3 Snapshot extraction range

`PstfKmodeResult` 의 snapshot 별 source 계산 시 `pstf_source_function` 호출. PR-024a 에서 E_0 unconditional zero 로 해결됨 → range 문제 없음.

### 3.4 Pre-audit verdict

PR-024b 는 **layout accessor range check 가 모두 통과**. PR-024a 의 교훈이 성공적으로 pre-audit 에 integrated.

---

## §4. API 설계

### 4.1 PstfKmodeResult

```rust
pub(crate) struct PstfKmodeResult {
    pub(crate) eta_grid: Vec<f64>,
    pub(crate) source_total: Vec<f64>,
    pub(crate) source_sw: Vec<f64>,
    pub(crate) source_dop: Vec<f64>,
    pub(crate) source_quad: Vec<f64>,
    pub(crate) source_e_total: Vec<f64>,
    pub(crate) phi: Vec<f64>,
    pub(crate) psi: Vec<f64>,
    pub(crate) polterdot_grid: Vec<f64>,
    pub(crate) n_state: usize,
    pub(crate) state_trajectory: Option<Vec<Vec<f64>>>,  // opt-in, expensive memory
}
```

MB-95 `CambKmodeResult` mirror. `state_trajectory` 은 optional (debugging / PR-025 equivalence test 용).

### 4.2 pstf_solve_kmode

```rust
pub(crate) fn pstf_solve_kmode(
    k: f64,
    common: &CommonProfile,     // MB-95 기존 struct 재사용 (background + visibility)
    layout: &PstfFlrwLayout,
    ic_state: Vec<f64>,          // from pstf_adiabatic_ic (PR-021)
    save_trajectory: bool,
) -> Result<PstfKmodeResult, String> {
    // 1. Build mats_flat via build_pstf_matrix_into over common.tau_profile
    // 2. Call integrate_linear_profile_rodas5p
    // 3. Loop snapshots:
    //    - Extract state
    //    - Call pstf_full_rhs → dy
    //    - Call pstf_source_function → SourceTerms
    //    - Store in result
    // 4. Return PstfKmodeResult
}
```

---

## §5. TDD gate (10 tests 예상)

### Identity (3 tests)
- `identity_matrix_build_matches_unit_vectors` — `build_pstf_matrix_into` column j 가 `pstf_full_rhs(e_j)` 와 bit-identical
- `identity_matrix_linearity` — `pstf_full_rhs(a·u + b·v) = a·pstf_full_rhs(u) + b·pstf_full_rhs(v)` — linearity 재검증
- `identity_matrix_multiple_tau` — 서로 다른 τ 에서 matrix build 가 일관성 (coefficient 가 τ-dependent 해야 하지 structure 는 일관)

### Regression (3 tests) — G2 FLRW
- `regression_solve_kmode_single_k` — k=0.01 에서 PSTF state trajectory active indices 가 MB-95 `solve_camb_kmode` 결과와 tolerance 1e-8 이내 (stepper 동일하므로 accumulated FP roundoff 내)
- `regression_source_grid_matches_mb95` — 각 snapshot source_total 이 MB-95 해당 snapshot 와 tolerance 1e-10
- `regression_phi_psi_matches_mb95` — phi, psi trajectory 도 MB-95 와 tolerance 1e-10

### Channelwise (2 tests)
- `channelwise_source_grid_nonzero_only_during_visibility` — source_total 이 visibility 가 non-negligible 한 η 범위에서만 nonzero
- `channelwise_state_initial_condition` — eta_grid[0] 에서 state 가 `pstf_adiabatic_ic` IC 와 일치

### Caveat (2 tests)
- `caveat_trajectory_save_optional` — `save_trajectory=true/false` 각각 정상 동작
- `caveat_layout_accessor_range_check` — E-mode / B-mode ell<2 호출 시도 없음 (tests 내부에서 모든 accessor 사용을 검증)

**총 10 tests**.

---

## §6. Gate forecast

| Gate | 예상 | 근거 |
|---|---|---|
| G1 COMPILE | ✅ | 새 파일, 기존 `integrate_linear_profile_rodas5p` 재사용 |
| **G2 FLRW (full)** | **✅** (tolerance-based) | `regression_solve_kmode_single_k` + `regression_source_grid_matches_mb95` + `regression_phi_psi_matches_mb95` — 동일 stepper, 동일 tau_profile, 동일 background → FP tolerance 1e-8~1e-10 이내 일치 |
| G3 PHYS | ✅ | Identity (matrix build linearity), channelwise (visibility range, IC), caveat (trajectory opt, layout range) |
| G4 CROSS | ✅ | MB-95 `solve_camb_kmode` + `solve_kmode_full_with_common` inline 대조 |

**Score: 7/10** forecast. W=4 × S=7/10 = **W·S/10 = 2.8** (forecast 정확).

Phase 1 진행률: 50.8% → **53.5%**.

**Important caveat**: G2 tolerance-based (1e-8~1e-10), NOT bit-identical. Reason: MB-95 의 `build_camb_matrix_into` 는 hand-written analytic form, PSTF 의 `build_pstf_matrix_into` 는 unit-vector decomposition. 두 방법이 **mathematically equivalent** 이나 floating-point 의 associativity 로 인해 exact bit-identical 은 보장 안 됨. **PR-024c 에서 D_2 bit-identical** 을 target 으로 삼는 것은 MB-95 와 PSTF 가 **다른 경로** 로 D_2 에 도달하는 것을 의미 — algorithm-level equivalence 는 PR-025 이 별도 증명.

---

## §7. Anti-local-min triggers

1. **Matrix build row-major vs column-major 혼동** — `integrate_linear_profile_rodas5p` 의 `mats_flat` 이 어떤 ordering 인가? 구현 시 `build_camb_matrix_into` 직접 확인하여 동일 ordering 사용.

2. **`cs2b` source** — PR-024b `FullRhsInputs` 가 cs2b 를 요구. `CommonProfile` 이 snapshot 별 cs2b 를 보유하는지 확인 (MB-95 와 공유 가능).

3. **`kappa_dot`, `r_b` 접근** — 마찬가지로 `CommonProfile.bg_at_snap[i]` 에서 추출.

4. **IC 시점 정렬** — PR-021 IC 는 τ=0.5~1 에서 시작, MB-95 tau_profile 도 동일 시점. `pstf_solve_kmode` 의 `eta_eval` 는 IC 시점부터 τ_0 까지. 경계 시점 일치 검증 필수.

5. **Unit vector loop panic** — `pstf_full_rhs(state=e_j)` 에서 `state[layout.i_metric_sigma()] = 1.0` 일 때 sigmadot 계산이 정상. 다른 slot 도 모두 정상. §3 에서 layout range 통과 확인.

---

## §8. PR-024a 교훈의 적용

- [x] **Layout accessor range check** — §3 에 전용 섹션, 모든 accessor 열거
- [x] Pre-audit 가 physics / SSOT / MB-95 mapping 뿐 아니라 **layout convention dimension** 도 검토
- [x] Unit vector loop 의 `state[j] = 1.0` 가 각 slot 에서 valid 한가 사전 검증
- [x] E-mode ℓ<2 와 같은 hidden assertion 이 없는가 확인

---

## §9. Pre-PR checklist

- [x] MB-95 `solve_camb_kmode` + `solve_kmode_full_with_common` 구조 재감사 (§2)
- [x] Jacobian gap (PR-022c 범위) 식별 + 해결 approach 선택 (C: unit-vector build)
- [x] `pstf_full_rhs` linearity 정당화 (PR-022c 증거)
- [x] Layout accessor range check 완료 (§3, PR-024a 교훈 적용)
- [x] G2 tolerance 명시 (1e-8~1e-10, NOT bit-identical, reason documented)

---

## §10. 즉시 다음 행동

동일 turn 내:
1. **PR-024b scaffold** — `src/solver/pstf_primary/matrix.rs` + `integrate.rs`
2. `build_pstf_matrix_into()` 구현 (column-by-column unit vector)
3. `PstfKmodeResult` + `pstf_solve_kmode()` 구현
4. 10 tests (§5)
5. D_2 15th consecutive 재확인 (production path 무접촉 예상)
6. `pr-024b.md` closure delta + scoreboard 갱신 (50.8% → 53.5%)

PR-024b 완료 후 **PR-024c (LoS + spectrum assembly, Phase 1 technical capstone)** 진입. PR-024c 의 D_2 bit-identical target 이 Phase 1 의 crown.

---

*PR-024b design. Approach C (unit-vector matrix build) 로 Jacobian 확장 scope 회피하면서 MB-95 stepper 공유. Layout accessor range check 는 PR-024a 교훈을 pre-audit 에 구조적으로 반영. G2 tolerance-based 로 honest scoping — bit-identical 은 PR-024c 의 D_2 level 에서 target.*
