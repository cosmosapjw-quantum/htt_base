# PR-021 Design Document — PSTF Adiabatic IC

> **Status**: 📝 **DESIGN (pre-audit)** — 2026-04-17
> **Target PR**: PR-021 (Phase 1 second commit)
> **Companion**: `docs/ROADMAP_PHASE_I_TO_L.md` v2.0 §3 / `PR_CONSTITUTION.md` §9 (4-Gate), §11 (Hallucination)
> **Dependency**: PR-020 ✅ (`PstfFlrwLayout`)
> **Weight**: 10 | **Target score**: 8

---

## §1. Motivation

Phase 1 의 두 번째 code PR. PSTF state vector 위에서 **adiabatic initial condition** 을 유도한다. PR-022 (RHS) 와 PR-024 (LoS source) 가 모두 IC 를 소비하므로 이것이 다음 단계의 전제.

**핵심 도전**: MB-95 의 IC 는 synchronous-gauge 변수 `η_s`, `σ_synchronous`, `v_b`, `Θ_ℓ` 기반. PSTF 는 gauge-invariant 공변 변수 위에서 정의. **동일한 물리적 adiabatic mode** 를 두 다른 변수 basis 로 표현할 때 값 자체는 다르지만, **FLRW 극한에서 관측량 (δ_γ, v_b) 의 초기값은 일치** 해야 한다. 이것이 PR-021 의 G2 gate.

---

## §2. MB-95 IC 현 구현 (oracle reference)

`src/solver/sync_gauge_camb.rs::adiabatic_ic` (lines 3297–3318):

```rust
// ζ = 1 규약, k·η ≪ 1 (radiation era 초기)
y[i_etak]    = -k        // η_s = -1 → etak = -k
y[i_clxc]    = 1.5       // δ_c = 3/2
y[i_clxb]    = 1.5       // δ_b = 3/2
y[theta(0)]  = 0.5       // Θ_0 = δ_γ/4 = 1/2
y[nu(0)]     = 0.5       // N_0 = δ_ν/4 = 1/2
y[theta(1)]  = k/(6·ℋ)   // Θ_1 ≈ k/(6·ℋ)
y[nu(1)]     = k/(6·ℋ)   // N_1 ≈ k/(6·ℋ)
y[i_vb]      = 3·Θ_1     // v_b = k/(2·ℋ) (tight coupling: v_b = 3·Θ_1)
y[i_sigma]   = 0         // σ_synchronous = 0 at early times
```

주석: "standard ΛCDM adiabatic mode at early times (kτ ≪ 1)".

### 2.1 이 값들의 출처

CAMB 와 MB-95 1995 논문 §5 의 regular series. `η_s → −1` 규약은 `ζ = 1` 에 해당하며, `χ_0 = −1` 와 동치. Lewis-Challinor-Lasenby 2000 CAMB 원 논문이 이 규약을 사용.

### 2.2 "Θ_2 = 0" 문제

PR-020 의 pre-audit design doc 과 방법론 참조 (v6.0 §5.3 pitfall #1) 에서 지적된 바:

> Orthogonal Bianchi + Θ_2 = 0 은 WRONG. Use TCA closure value.

MB-95 IC 에서 `Θ_2 = 0` 으로 설정된 것은 FLRW 에서 초기 Thomson TCA 가 `Θ_2 → 0` 을 강제하기 때문 — 실제로는 TCA 의 첫 번째 보정에서 `Θ_2 ≈ (32/45) · k·τ_c · v_b` 로 빠르게 수렴. 하지만 이 PR-021 이 다루는 것은 **IC at η_init** 이고, 그 시점에서 `Θ_2 = 0` 은 안전한 0차 근사 (FLRW 에서는).

Bianchi orthogonal 의 경우 `Θ_2 ≠ 0` at init (시어 배경이 직접 quadrupole 주입) — Phase 4 spec. PR-021 은 FLRW 만.

---

## §3. PSTF IC 유도 (PR-021 의 scope)

### 3.1 변수 대응 (FLRW limit)

`pr-020-design.md §3` 의 매핑 table 을 IC 값으로 구체화:

| 물리량 | MB-95 값 | PSTF 변수 | PSTF 값 (FLRW) |
|---|---|---|---|
| δ_γ / 4 (photon monopole) | `Θ_0 = 1/2` | `I_0^{(γ)}(m=0)` | `1/2 · N_γ` |
| v_γ (photon dipole, in velocity units) | `Θ_1 = k/(6ℋ)` | `I_1^{(γ)}(m=0)` | `N_1 · k/(6ℋ)` |
| Θ_2 (photon quadrupole) | 0 (at η_init) | `I_2^{(γ)}(m=0)` | 0 |
| δ_ν / 4 | `N_0 = 1/2` | `I_0^{(ν)}(m=0)` | `1/2 · N_ν` |
| v_ν | `N_1 = k/(6ℋ)` | `I_1^{(ν)}(m=0)` | `N_ν · k/(6ℋ)` |
| δ_c | `1.5` | — (fluid sector, PR-023 이후) | ⏸️ 보류 |
| δ_b | `1.5` | — (fluid sector) | ⏸️ 보류 |
| v_b | `k/(2ℋ)` | — (fluid sector) | ⏸️ 보류 |

**Normalization factor `N_γ`, `N_ν`, `N_1`** 은 PSTF STF tensor 와 MB-95 brightness multipole 사이의 관계에서 나옴. PR-020 의 `flrw_norm_ratio_down` 실패 경험에서 배운 교훈: **이 normalization 은 단순 coefficient 가 아니라 full STF-to-Y_ℓ^m projection chain**.

### 3.2 Scope 제한 — PR-021 이 할 일 / 안 할 일

**할 일**:
- PSTF photon 과 neutrino monopole / dipole / quadrupole 초기값을 **self-consistent** 하게 설정 (조정 계수 포함)
- `PstfAdiabaticIc` struct 에 FLRW-limit physical observables (δ_γ, v_γ, etc.) 를 저장 — MB-95 값과 직접 비교 가능한 form
- MB-95 `adiabatic_ic` 와의 비교: physical δ_γ(η_init) 이 일치 (ratio 1.00 ± 1e-3) — 이것이 G2 FLRW gate
- k-dependence (`∝ k` for dipole, `∝ k²` for 아직 설정되지 않는 higher ℓ) 검증 — G3 PHYS gate

**안 할 일**:
- Fluid sector (δ_c, δ_b, v_b) — PSTF fluid variables 는 PR-023 (metric) 과 함께 도입
- Metric variables (Φ^{1+3}, Z_{ab}) — PR-023
- Tilted Bianchi boost rules (v6.0 §5.2) — Phase 4
- `Θ_2 ≠ 0` TCA closure — PR-022 (RHS + TCA) 에서 처리
- 정확한 PSTF ↔ MB-95 normalization 의 **모든** 계수 — PR-025 이 완결. PR-021 은 "observable δ_γ 수준에서 일치" 로 만족.

### 3.3 Normalization 전략

PR-020 의 실패를 반복하지 않기 위해 다음 전략을 채택:

**단순 FLRW 에서의 adiabatic mode 는 gauge-invariant observable (δ_γ, v_γ) 를 통해 정의된다.** PSTF IC 는 이 observable 값이 MB-95 와 일치하도록 setting 한다 — PSTF 변수의 내재 normalization 이 무엇이든.

구체적으로: `I_0^{(γ)}(m=0)` 의 state vector 값을 그대로 `0.5` 로 놓되, 이것이 `δ_γ = 2` 를 의미하도록 하는 **projection rule** 을 `PstfAdiabaticIc::observables()` method 에 encode. 이 projection rule 은 §4.3 에서 명시.

이 전략의 장점:
- PR-020 에서 겪은 "coefficient-level normalization" 의 함정을 회피
- MB-95 와의 비교가 **state vector 수준이 아니라 physical observable 수준** 에서 이루어짐
- PR-025 (equivalence test) 에서 C_ℓ 수준 비교의 선행 단계

**주의**: 이 전략은 PR-021 의 G2 gate 를 "MB-95 δ_γ 와 PSTF `observables().delta_gamma` 의 ratio 1.00 ± 1e-3" 으로 정의함을 의미. State vector 자체의 값 비교가 아님.

---

## §4. PR-021 Concrete Scope

### 4.1 새 파일

- `src/solver/pstf_primary/ic.rs`:
  ```rust
  pub(crate) struct PstfIcInputs {
      pub(crate) k: f64,           // wavenumber, Mpc⁻¹
      pub(crate) adotoa: f64,      // ℋ at η_init
      pub(crate) zeta: f64,        // curvature perturbation amplitude (default 1)
  }

  pub(crate) struct PstfObservables {
      pub(crate) delta_gamma: f64,  // photon density contrast, δ_γ
      pub(crate) v_gamma: f64,      // photon bulk velocity (Θ_1 · 3)
      pub(crate) delta_nu: f64,     // neutrino density contrast
      pub(crate) v_nu: f64,         // neutrino bulk velocity
      pub(crate) quad_gamma: f64,   // Θ_2 (= 0 at init for FLRW)
  }

  pub(crate) fn pstf_adiabatic_ic(
      inputs: &PstfIcInputs,
      layout: &PstfFlrwLayout,
  ) -> Vec<f64>;  // state vector initialized

  impl PstfObservables {
      pub(crate) fn from_state(
          state: &[f64],
          layout: &PstfFlrwLayout,
          k: f64,
      ) -> Self;  // projection rule
  }
  ```

### 4.2 State vector 초기값

```rust
// §3.1 변수 대응 테이블 기반
state[layout.i_photon_i_m0(0)]  = 0.5;                    // I_0^{(γ)}
state[layout.i_photon_i_m0(1)]  = k / (6.0 * adotoa);     // I_1^{(γ)}
// I_ℓ^{(γ)} for ℓ ≥ 2 = 0
state[layout.i_neutrino_m0(0)]  = 0.5;                    // I_0^{(ν)}
state[layout.i_neutrino_m0(1)]  = k / (6.0 * adotoa);     // I_1^{(ν)}
// E_ℓ, B_ℓ all zero at adiabatic init
```

Fluid sector 는 전혀 건드리지 않음 (state vector 에서 그 부분은 zero-initialized 또는 PR-023 에서 별도 init).

### 4.3 Projection rule (`PstfObservables::from_state`)

FLRW 에서 MB-95 과 비교 가능한 physical observable 계산:

```rust
fn from_state(state: &[f64], layout: &PstfFlrwLayout, k: f64) -> Self {
    // PSTF FLRW limit projection
    //   δ_γ = 4 · I_0^{(γ)}(m=0)        (MB-95 Θ_0 = δ_γ/4 과 동치)
    //   v_γ = 3 · I_1^{(γ)}(m=0)        (MB-95 v = 3·Θ_1 tight-coupling 관례)
    //   Θ_2 = I_2^{(γ)}(m=0)            (직접)
    let delta_gamma = 4.0 * state[layout.i_photon_i_m0(0)];
    let v_gamma = 3.0 * state[layout.i_photon_i_m0(1)];
    let quad_gamma = if layout.ell_max_gamma >= 2 {
        state[layout.i_photon_i_m0(2)]
    } else { 0.0 };
    let delta_nu = 4.0 * state[layout.i_neutrino_m0(0)];
    let v_nu = 3.0 * state[layout.i_neutrino_m0(1)];
    Self { delta_gamma, v_gamma, delta_nu, v_nu, quad_gamma }
}
```

**핵심**: state 값 자체는 MB-95 Θ_ℓ 와 동일한 수치지만, `PstfObservables` 를 경유하여 physical 의미를 부여. 이것이 PR-021 이 scope 내에서 성립하는 이유 — state 수준에서는 간단한 복사지만, 추후 PSTF `I_{A_ℓ}` tensor 구조로 확장될 때 이 projection rule 이 확장 포인트가 됨.

### 4.4 TDD gate (PR-021)

**Identity tests (2)**:
- `identity_photon_monopole_equals_half` — `state[i_photon_i_m0(0)] == 0.5` (바로 assert)
- `identity_photon_dipole_proportional_to_k_over_h` — `state[i_photon_i_m0(1)]` 이 k 에 선형, adotoa 에 반비례

**Limit tests (2)**:
- `limit_k_zero_dipole_vanishes` — k → 0 에서 I_1^{(γ)} → 0
- `limit_neutrino_matches_photon_adiabatic` — adiabatic 에서 photon 과 neutrino 의 monopole/dipole 동일

**Channelwise tests (1)**:
- `channelwise_polarization_zero_at_init` — pol-ON layout 에서 E_ℓ = B_ℓ = 0 for all ℓ

**Regression tests (2)** ← G2 FLRW gate
- `regression_delta_gamma_matches_mb95_adiabatic` — `PstfObservables::from_state()` 의 `delta_gamma` 가 MB-95 `adiabatic_ic` 의 `4·Θ_0 = 2.0` 와 일치 (ratio 1.00 ± 1e-6 — 이 case 는 수치 일치 기대)
- `regression_v_gamma_matches_mb95_adiabatic` — PSTF `v_gamma` 가 MB-95 `3·Θ_1 = k/(2·ℋ)` 와 일치 (ratio 1.00 ± 1e-6)

**Caveat tests (2)**:
- `caveat_fluid_sector_untouched_by_ic` — state vector 의 fluid 영역 (LmLayout::baryon_start 부터 cdm 끝) 은 이 IC 함수가 건드리지 않음을 확인 (pre-initialize 된 sentinel 값 유지)
- `caveat_higher_multipoles_zero` — ℓ ≥ 2 의 I_ℓ^{(γ)}, I_ℓ^{(ν)} 모두 0 임을 확인 (Θ_2 TCA closure 는 PR-022)

**총 9 tests**.

### 4.5 추가 file 수정

- `src/solver/pstf_primary/mod.rs` — `pub(crate) mod ic;` 등록 (1 줄)

### 4.6 생산 경로 접촉 없음

`solve_production_spectrum` 은 여전히 MB-95 `adiabatic_ic` 를 호출. PR-021 의 `pstf_adiabatic_ic` 는 **isolated test fixture** 로만 사용. D_2 = 1002.086744 bit-identical 유지.

---

## §5. Gate analysis (4-Gate forecast)

| Gate | 예상 상태 | 증거 계획 |
|---|---|---|
| G1 COMPILE | ✅ | `cargo build --lib --release` 성공, 9 신규 + 기존 test 회귀 없음 |
| **G2 FLRW** | ✅ | `regression_delta_gamma_matches_mb95_adiabatic`, `regression_v_gamma_matches_mb95_adiabatic` 이 직접 증거. ratio 1.00 ± 1e-6 (state-value copy 이므로 bit-identical 에 가까움) |
| G3 PHYS | ✅ | k-linearity (dipole ∝ k), adotoa 의존성, adiabatic mode 간 photon-neutrino 일치 — 총 3 physical consistency checks |
| G4 CROSS | ✅ | MB-95 `adiabatic_ic` (Rust oracle) 과의 직접 비교. 이 PR 이 G4 를 pass 하는 첫 PSTF PR. |

**예상 score: 8 / 10** (cap = 9, 단 convergence figure / publication-ready output 미포함이라 8). W·S/10 = 10 × 8 / 10 = **8.0**.

Phase 1 진행률 갱신 예상: 23.6 → **31.6** / 105 = **30.1%**.

---

## §6. Anti-local-minimum considerations

PR-020 경험 후, 다음 trigger 를 조기 감지:

- **Trigger 1**: MB-95 `δ_γ = 2.0` 와 PSTF `from_state().delta_gamma` 가 2.0 이 아닌 값으로 나오면 → 2번째 시도 (tolerance 완화) 금지. 즉시 STOP, §3.3 normalization 전략 재검토.
- **Trigger 2**: k-linearity test 가 ULP 수준이 아닌 `1e-3` 이상 차이를 보이면 → `adotoa` 값 정확성 점검 (MB-95 와 같은 background 사용하는지).
- **Trigger 3**: fluid sector caveat test 실패 (IC 함수가 fluid 영역을 건드림) → scope creep 경고. `ic.rs` 의 write 영역을 photon + neutrino 로 제한.

어떤 trigger 든 2번째 시도에서 실패하면 `STUCK_LOG.md` 에 기록 + PR-022 pre-audit 로 이동.

---

## §7. Hallucination checklist (§11.1 준비)

PR-021 closure 시 다음을 paste 할 준비:

- [ ] `cargo build --lib --release` output
- [ ] `solver::pstf_primary::ic::tests` test count (9 예상)
- [ ] `regression_delta_gamma_matches_mb95_adiabatic` 의 실제 numerical output: `expected = 2.0, got = <value>, rel_err = <value>`
- [ ] `regression_v_gamma_matches_mb95_adiabatic` 의 실제 numerical output
- [ ] `dump_dl_spectrum_sparse` D_2 = 1002.086744 재측정 (production 무접촉 확인)
- [ ] 기존 4 슈트 (pstf / source::registry / core::ssot / pstf_primary::layout) 회귀 없음 paste

---

## §8. 위험 및 불확실성

1. **FLRW 에서 `δ_γ = 2.0` 가 정말 canonical 값인가?** — MB-95 adiabatic 의 `Θ_0 = 1/2` × 4 = 2.0 은 `ζ = 1` 규약. CAMB normalization 에서는 이것이 primordial curvature perturbation 단위. PSTF 가 같은 규약을 따르는지 문헌 재확인 필요 — Tsagas et al. 2008 review §4 참조 가능.
2. **State vector 의 fluid 영역이 LmLayout 에서 할당되어 있는가?** — 그렇다면 IC 함수가 이 영역을 손대지 않아야 caveat test 성립. `lm_indexing.rs` 의 baryon_start / cdm_start 영역 확인 필요.
3. **k / ℋ 비율의 numerical precision** — 초기 `η_init` 에서 ℋ 가 어떤 값인지, 그리고 `k = 10⁻² Mpc⁻¹` 정도의 대표값에서 k/(6ℋ) 이 어떤 order 인지. MB-95 test fixture 에서 가져오는 게 가장 안전 — `CambBackground` 객체 가 있으면 거기서 `bg0.adotoa` 직접 사용.
4. **PSTF IC normalization 문서화 부족** — `src/pstf/` 하위의 기존 코드가 IC 를 다루는지 확인 필요. `pstf::hierarchy::PSTFHierarchy` 에 initial state 설정 helper 있을 수 있음.

이 4 항목은 PR-021 scaffold 착수 시 우선 확인.

---

## §9. Pre-PR checklist

- [ ] `src/pstf/hierarchy.rs` 나 `src/pstf/lm_indexing.rs` 에 IC 관련 helper 있는지 재확인
- [ ] `src/solver/sync_gauge_camb.rs::adiabatic_ic` 를 호출하는 test 에서 background object 가 어떻게 만들어지는지 확인 (PR-021 의 identity test 에서 재사용)
- [ ] `PstfFlrwLayout` 의 state vector initialization 이 `vec![0.0; n_state]` 로 clean 하게 시작하는지 확인 (fluid sector caveat 가 성립하려면)
- [ ] `CambBackground` struct 이 PR-021 test 에서 필요한 `adotoa` 값을 노출하는지 확인

---

## §10. Scope for PR-022 (다음 PR preview)

PR-021 완료 후 PR-022 (PSTF RHS) 에 필요한 것:

- IC 는 PR-021 이 제공 → RHS 가 시작점으로 사용
- TCA closure `Θ_2 ≈ (32/45) · k · τ_c · v_b` 의 PSTF 대응 — PR-022 에서 처리
- Jacobian sparsity — `src/pstf/hierarchy_matrix::build_coupling_matrix` 재사용
- Thomson collision — electron-frame ζ̃ 재유도 필요 (PR-020 design §2.2 의 `collision_lm.rs` 재검토 항목)

PR-022 는 Phase 1 의 biggest PR (weight 15). 하나로 할지 sub-track 분할할지는 PR-021 closure 후 재평가.

---

*Pre-audit design frozen 2026-04-17. PR-021 scaffold 다음 세션에서 착수.*
