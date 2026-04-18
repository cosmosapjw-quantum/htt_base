# PR-022b Design Document — PSTF Electron-frame Thomson Collision

> **Status**: 📝 **DESIGN (pre-audit)** — 2026-04-17
> **Target PR**: PR-022b (sub-track b of PR-022)
> **Dependency**: PR-020 ✅, PR-021 ✅, PR-022a ✅
> **Weight**: 5
> **Target score**: 8

---

## §1. Scope

PSTF primary state vector 위에서 Thomson collision operator 를 **electron-frame ζ̃ convention** 으로 구현. DESIGN LAW 요구사항 준수 + MB-95 `camb_rhs` 와 FLRW 수치 일치.

### 포함된 것
- `src/solver/pstf_primary/collision.rs` (예상 ~350 줄)
  - `FrameConvention` enum — ElectronRestFrame (default, DESIGN LAW) vs HypersurfaceNormalFrame (MB-95 equivalent at FLRW)
  - `CollisionInputs { kappa_dot, r_b }` — opacity + baryon-photon ratio
  - `pstf_thomson_collision(state, dy, inputs, layout)` — photon sector collision (ν 는 collision 없음)
  - `ThomsonCollisionOperator` struct (sparse block structure for Jacobian 의 준비)

### 포함되지 않은 것
- Free-streaming RHS: PR-022a ✅
- Jacobian (analytical sparse): PR-022c
- Metric coupling: PR-023
- ν collision (= 0, 명시적으로 처리): **trivial test 만 포함**

---

## §2. Physical derivation

### 2.1 Electron-frame ζ̃ definition

Thomson collision 의 정확한 형태는 photon distribution function 을 **어느 frame 에서 보느냐** 에 따라 달라짐:

- **Electron rest frame** (electron 순간 정지 frame): collision 이 등방적, angle-averaged. `u_e^a` 가 4-velocity.
- **Hypersurface-normal frame** (synchronous gauge의 `n^a`): electron 이 움직이는 frame. `n^a − u_e^a` 차이가 velocity 로 들어감.

DESIGN LAW 는 electron rest frame 을 요구. FLRW 에서 `n^a = u_e^a` 가 되므로 (isotropy) 두 frame 이 일치 — **PR-022b 에서는 FLRW 에 한정하여 두 frame 수치 일치를 증명** 하고, Bianchi tilt 확장은 Phase 4 로 미룸.

### 2.2 ℓ-specific collision operator (Θ convention)

**Θ_ℓ = F_ℓ / 4** (brightness convention 의 1/4). MB-95 `camb_rhs` 가 사용하는 convention. 이것을 PSTF primary 에서도 채택:

```
ℓ = 0:  C[Θ_0] = 0                                  (energy conservation)
ℓ = 1:  C[Θ_1] = −κ̇·(Θ_1 − v_b/3)                   (photon-baryon drag)
ℓ = 2:  C[Θ_2] = −(9/10)·κ̇·Θ_2 + (3/20)·κ̇·E_2      (pol feedback, E 가 있는 경우)
         = −κ̇·Θ_2                                    (pol 없는 경우)
ℓ ≥ 3:  C[Θ_ℓ] = −κ̇·Θ_ℓ                              (pure damping)
```

Baryon side (momentum conservation, `r_b = (3/4)·ρ_b/ρ_γ`):
```
dv_b/dη |_drag = (κ̇/r_b)·(3·Θ_1 − v_b)
```

E-mode polarization (ℓ = 2):
```
C[E_2] = −κ̇·E_2 + (κ̇/10)·(Θ_2/5·2 + E_2) ??? 
```
— 이것 재유도 필요. MB-95 comment `Π = F_2/10 + (9/15)E_2` 에서 `Π_Θ = Θ_2/10 + (9/15)·E_2/4 = Θ_2/10 + (3/20)·E_2` 이 `C[Θ_2] = −0.9·κ̇·Θ_2 + 0.15·κ̇·E_2` 에 대응. E-mode 의 C 는 재유도 from 정확한 식.

### 2.3 `src/pstf/collision_lm.rs` 의 coefficient 재감사 결과 ⚠️

**중요한 발견 (2026-04-17 pre-audit)**: `collision_lm.rs:107-118` 의 ℓ=1 block matrix:

```rust
matrix: vec![
    // [dF_{1m}/dη, dF_{1m}/dv_b^m]
    -kd,            kd,
    // [dv_b^m/dF_{1m}, dv_b^m/dv_b^m]
    3.0 * kd * inv_rb / 4.0,  -kd * inv_rb,
],
```

주석은 brightness convention 이라 적혀 있으나 matrix 값이 자체 일관적이지 않음:
- Row 1 `[−kd, kd]`: dF_1/dη = −κ̇·F_1 + κ̇·v_b → 이것은 `−κ̇·(F_1 − v_b)` **여기서 v_b 단위가 F 와 동일** 이어야 함.
- Row 2 `[3kd/(4·r_b), −kd/r_b]`: dv_b/dη = (3κ̇/(4·r_b))·F_1 − (κ̇/r_b)·v_b → 이것은 `(κ̇/r_b)·((3/4)·F_1 − v_b)`

**이 두 식이 momentum-conserving pair 이려면**:
- Θ convention 일 경우: `−κ̇(Θ_1 − v_b/3)` on Θ_1 row, `(κ̇/r_b)·(3·Θ_1 − v_b)` on v_b row → **coefficients `(1/3)` 와 `3` 이 짝**
- F=4Θ convention 일 경우: `−κ̇(F_1 − (4/3)·v_b/?)` on F_1 row, `(κ̇/r_b)·((3/4)·F_1 − v_b)` on v_b row — v_b 의 재정의 필요

`collision_lm.rs` 의 **row 2 coefficient `3/4`** 와 **row 1 의 `1`** 은 standard Θ 나 F 어느 convention 에서도 momentum-conserving pair 가 아님. **Probable bug** 또는 "baryon v_b 는 Θ convention, photon F 는 brightness convention" 혼재.

**결정**: PR-022b 에서는 `collision_lm.rs` 를 **G4 cross-check target 으로 사용하지 않음** — 대신 MB-95 `camb_rhs` 를 primary oracle 로 사용. `collision_lm.rs` coefficient issue 는 **별도 issue 로 flag** (STUCK_LOG 가 아니라 별도 BUG 문서) 하고 Phase 2 이후에 해결.

이것은 **PR-020 의 `flrw_norm_ratio_down`** 함정과 동일한 pattern — 잘못된 reference 를 쓰는 대신 scope 을 축소하고 올바른 oracle 로 재정렬.

### 2.4 Primary oracle: MB-95 `camb_rhs`

`sync_gauge_camb.rs:491-508` 이 참조:
```
dΘ_0/dη (collision part) = 0
dΘ_1/dη (collision part) = −opac·(Θ_1 − v_b/3)
dΘ_2/dη (collision part) = −0.9·opac·Θ_2 + (3/20)·opac·E_2     (with pol)
dΘ_ℓ/dη (collision part) = −opac·Θ_ℓ                             (ℓ ≥ 3)
dv_b/dη (drag part)      = opac·(3·Θ_1 − v_b)/r_b                 (from L486-487)
```

여기서 `opac = κ̇ > 0` (positive by convention in `camb_rhs`).

**PSTF primary 는 이것을 그대로 port**. PSTF layout 의 photon intensity 인덱스는 `i_photon_i_m0(ℓ)` = `photon_intensity_start + ℓ` for m=0, 값은 state 에서 **Θ_ℓ** 를 저장 (bit-identical to PR-021 IC). E_ℓ 는 `i_photon_e_m0(ℓ)`, baryon v_b 는 `inner.baryon_start + 1`.

---

## §3. API 설계

### 3.1 `FrameConvention` enum

```rust
/// Thomson collision 의 frame 선택.
///
/// DESIGN LAW 는 ElectronRestFrame 요구. FLRW 에서는 두 frame 이
/// 수치적으로 동일 — HypersurfaceNormalFrame 은 Bianchi 로 확장 시
/// MB-95 port 경로를 비교하기 위한 기준 frame.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum FrameConvention {
    /// DESIGN LAW default. Electron rest frame 에서 ζ̃ 정의.
    ElectronRestFrame,
    /// MB-95 equivalent at FLRW. Hypersurface-normal u_n = n^a frame.
    /// FLRW 에서 ElectronRestFrame 과 bit-identical.
    HypersurfaceNormalFrame,
}

impl Default for FrameConvention {
    fn default() -> Self { Self::ElectronRestFrame }
}
```

FLRW 에서 두 frame 이 수치 동일함은 `test_frame_equivalence_flrw` test 로 증명 (PR-022b 에서). Bianchi tilt 확장 시 차이가 발생하는데, 그것은 Phase 4 의 scope.

### 3.2 `CollisionInputs` struct

```rust
pub(crate) struct CollisionInputs {
    /// Thomson opacity κ̇ [Mpc⁻¹], positive by convention.
    pub(crate) kappa_dot: f64,
    /// Baryon-photon ratio r_b = (3/4)·ρ_b/ρ_γ, positive.
    pub(crate) r_b: f64,
    /// E-mode coupling on/off (PR-022b 에서는 optional — default off 로 pol-less 테스트 먼저).
    pub(crate) use_pol_feedback: bool,
    /// Frame convention (default: ElectronRestFrame).
    pub(crate) frame: FrameConvention,
}
```

### 3.3 Main function

```rust
pub(crate) fn pstf_thomson_collision(
    state: &[f64],
    dy: &mut [f64],
    inputs: &CollisionInputs,
    layout: &PstfFlrwLayout,
);
```

Caller 는 이 함수를 **PR-022a 의 `pstf_free_streaming_rhs` 와 additive 로 합성**:
```rust
// In future RHS dispatcher (PR-024 scope):
let mut dy = vec![0.0; layout.n_state];
pstf_free_streaming_rhs(state, &mut dy, &free_inputs, layout);
pstf_thomson_collision(state, &mut dy, &collision_inputs, layout);  // additive
// ... + metric (PR-023) + fluid (PR-023)
```

**No-op structural check**: collision 은 photon intensity 와 baryon velocity 만 touch. ν, metric, cdm 은 무접촉 (caveat test).

---

## §4. TDD gate (11 tests 예상)

### Identity (3 tests)
- `identity_ell0_collision_zero` — `dy[photon_i_m0(0)]` contribution from collision = 0 (energy conservation)
- `identity_ell1_drag_matches_mb95` — `dy[photon_i_m0(1)]` collision 항이 `−κ̇·(Θ_1 − v_b/3)` (MB-95 식) 과 rel err < 1e-14
- `identity_ell_ge_3_pure_damping` — ℓ ∈ {3, 5, 10} 에서 `dy[photon_i_m0(ℓ)]` collision = `−κ̇·Θ_ℓ`

### Limit (2 tests)
- `limit_kappa_dot_zero_trivial` — κ̇=0 에서 모든 dy contribution = 0
- `limit_no_pol_feedback` — `use_pol_feedback=false` 에서 `dy[photon_i_m0(2)]` = `−κ̇·Θ_2` (9/10 factor 없음, pol 항 없음)

### Channelwise (2 tests)
- `channelwise_neutrino_no_collision` — `dy` 의 neutrino 영역 에 ZERO contribution (ν 는 decoupled)
- `channelwise_cdm_metric_untouched` — fluid (cdm) 와 metric 영역 무접촉

### Regression (2 tests) — G2 evidence
- `regression_collision_matches_mb95_full_path` — PR-022a free-streaming + PR-022b collision 을 합한 full `dy` 가 MB-95 `camb_rhs` (pol off, hdot=0) 와 bit-identical 일치, ℓ={0,1,2,3,5,ℓ_max}, rel err < 1e-13
- `regression_multiple_kappa_dot` — κ̇ ∈ {0.01, 1.0, 100.0} Mpc⁻¹ 모두에서 일치 (opacity regime 전범위)

### Caveat (2 tests)
- `caveat_frame_equivalence_flrw` — FLRW state 에서 `FrameConvention::ElectronRestFrame` 과 `HypersurfaceNormalFrame` 이 bit-identical dy 생성
- `caveat_baryon_drag_sign_convention` — `dy[baryon v_b]` 의 sign 이 MB-95 와 일치 (`+opac·(3·Θ_1 − v_b)/r_b`)

---

## §5. Gate forecast

| Gate | 예상 | 근거 |
|---|---|---|
| G1 COMPILE | ✅ | 새 파일, 기존 회귀 없음 예상 |
| **G2 FLRW** | **✅ (full)** | `regression_collision_matches_mb95_full_path` 가 free-streaming + collision 합산 full path 비교. PR-022a 의 partial G2 보다 tight — metric 이 없어도 `hdot=0` 특수화로 full MB-95 RHS 재현 가능 |
| G3 PHYS | ✅ | κ̇=0 limit, pol-off limit, ℓ=0 conservation, frame equivalence |
| G4 CROSS | ✅ | MB-95 `camb_rhs` 직접 대조. 단 `collision_lm.rs` 는 **사용 안 함** (§2.3 bug 의심) |

**Score: 8/10** forecast. Weight 5 × 8/10 = **W·S/10 = 4.0**.

Phase 1 진행률: 34.1% → **37.9%** (35.8 + 4.0)/105.

---

## §6. Anti-local-min triggers

1. **`collision_lm.rs` coefficient bug 에 얽힘** — 2회 fail 시 STOP. 이미 §2.3 에서 flag, MB-95 을 primary oracle 로 사용하여 사전 회피.

2. **E-mode pol feedback 재유도 실수** — pol_feedback 이 복잡하므로 첫 iteration 에서는 `use_pol_feedback=false` 로 구현, pol 은 별도 PR 로 분리. `limit_no_pol_feedback` test 가 pol-off path 만 검증.

3. **κ̇ sign convention 혼재** — PSTF 와 MB-95 모두 positive convention 이므로 문제 없음. 단 matrix 에 포함할 때 `−κ̇` 가 정확히 `−kappa_dot.abs()` 인지 assertion.

---

## §7. Hallucination checklist 준비

PR-022b closure 시 paste 할 것:
- [ ] `cargo build --lib --release` output
- [ ] `solver::pstf_primary::collision::tests` test count (11 예상)
- [ ] `regression_collision_matches_mb95_full_path` 의 ℓ별, κ̇별 수치
- [ ] D_2 = 1002.086744 bit-identical (9th consecutive)
- [ ] 기존 6 슈트 (pstf / source::registry / core::ssot / pstf_primary::{layout,ic,rhs_free}) 회귀 없음

---

## §8. Pre-PR checklist (PR-022b 착수 전)

- [x] `collision_lm.rs` ℓ=1 block coefficient bug 의심 — MB-95 을 primary oracle 로 대체 (§2.3)
- [x] MB-95 `camb_rhs` 의 collision 구조 localize — 완료 (§2.4)
- [x] `FrameConvention` enum 설계 — default ElectronRestFrame, FLRW 에서 frame equivalence 증명 필요 (§3.1)
- [ ] `r_b` 의 positivity guard — MB-95 과 동일하게 `r_b.max(1e-10)` 채택
- [ ] E-mode pol feedback 는 **PR-022b 에서는 off 로 고정**, future PR 에서 활성화

---

## §9. 즉시 다음 행동

다음 세션에서:

1. **PR-022b scaffold** — `src/solver/pstf_primary/collision.rs` 신설
2. `FrameConvention` enum + `CollisionInputs` struct + `pstf_thomson_collision` 함수 구현
3. 11 tests 작성 (§4 specification 그대로)
4. G2 gate 측정: `regression_collision_matches_mb95_full_path` 수치 paste
5. D_2 bit-identical 재확인 (9th consecutive commit)
6. `pr-022b.md` closure delta + scoreboard 갱신 (진행률 34.1% → 37.9%)

PR-022b 완료 후 **PR-022c (Jacobian)** 로 동일 pattern 진입.

---

## §10. `collision_lm.rs` coefficient issue — 별도 flagging

PR-022b 의 scope **외** 이지만 future work 로 문서화:

- `collision_lm.rs:107-118` 의 ℓ=1 block matrix 가 Θ convention 과 F convention 을 섞는 것으로 의심됨. Row 1 은 F-natural, row 2 는 `3/4` factor 로 hybrid. Momentum-conserving pair 가 되려면 `(1, 1/3)` (Θ) 또는 `(1, 3/4)` (F 의 잘못된 pairing) 이어야 하나 현재 `(1, 3/4)` 이 `1` 과 짝지어져 있어 일관성 없음.
- Impact: `src/pstf/` 모듈은 production 경로 가 아니므로 D_2 에 영향 없음 (confirmed by PR-022a bit-identical). 단 Phase 2 이후 PSTF hierarchy 가 `collision_lm` 을 참조하는 경로 활성화 시 문제 발생 가능.
- Future work: `docs/BUGS/` 디렉토리 신설 후 `collision_lm_ell1_coefficient_audit.md` 작성. PR-022b 완료 후 처리.

---

*PR-022b design doc. `collision_lm.rs` bug 의심은 이미 §2.3 에서 식별되어 있으며, MB-95 을 primary oracle 로 사용하여 PR-022b 는 clean 한 구현이 가능.*
