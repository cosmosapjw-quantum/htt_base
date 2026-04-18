# PR-020 Design Document — PSTF Primary Scaffold

> **Status**: 📝 **DESIGN (pre-audit)** — 2026-04-17
> **Target PR**: PR-020 (Phase 1 kick-off)
> **Companion**: `docs/ROADMAP_PHASE_I_TO_L.md` v2.0 §3
> **Purpose**: PR-020 착수 전 `src/pstf/` 현 상태 감사, 누락 모듈 목록, PSTF ↔ MB-95 변수 매핑 table draft.

---

## §1. Motivation

Phase 1 (PR-020..024) 은 PSTF primary 를 scalar FLRW 에 한해 production-ready 로 완성. PR-020 은 그 첫 걸음으로 **state layout + hierarchy primitives** 를 담당. 본 문서는 코드 변경 전에:

1. `src/pstf/` 현존 코드를 감사하여 재사용 가능한 것 / 버릴 것 / 재작성할 것 분리
2. PSTF ↔ MB-95 변수 대응 관계를 사전에 고정 (equivalence test 의 기반)
3. PR-020 의 구체 scope 와 deliverable 확정

---

## §2. `src/pstf/` 감사 결과

### 2.1 현존 10 모듈 (3,044 줄)

| 파일 | 줄수 | 핵심 API | 판정 |
|---|---|---|---|
| `coupling.rs` | 267 | `free_streaming_{down,up}`, `shear_coupling_{down,up}`, `cg_kappa_0`, `stf_normalization`, `triangle_rule`, `parity_rule` | ✅ **핵심 재사용** |
| `hierarchy.rs` | 388 | `PSTFHierarchy`, `HierarchyBackground`, `Species`, `step_euler` | 🟡 **부분 재사용** (struct 유지, step 교체) |
| `hierarchy_matrix.rs` | 312 | `build_coupling_table`, `build_coupling_matrix`, `matrix_bandwidth`, `verify_flrw_tridiagonal` | ✅ **재사용** |
| `lm_indexing.rs` | 288 | `LmLayout`, `LmIndex`, `LmSpecies`, `Pol` | ✅ **핵심 재사용** |
| `m_decomposition.rs` | 342 | `MmodeHierarchy`, `cg_kappa_m`, `m_streaming_{down,up}` | ⏸️ **Phase 4 에서 재사용** (FLRW 는 m=0 만) |
| `streaming_lm.rs` | 383 | `wigner3j`, `shear_coeff_axisym`, `shear_coeff_cross`, `build_photon_streaming` | ⏸️ **Phase 4 에서 재사용** (shear 계수는 Bianchi 용) |
| `collision_lm.rs` | 359 | `CollisionOperator`, `build_collision`, `apply_collision`, `THETA4_CXI`, `theta4_quadrupole_correction` | 🔍 **재유도 필요** (electron-frame ζ̃ 규약 확인) |
| `tca_lm.rs` | 256 | `TcaCriterion`, `TcaClosure`, `tca_closure_first_order`, `crs_second_order_factor` | ✅ **재사용** |
| `tensor.rs` | 319 | `stf_project_rank2`, `stf_contract_rank2`, `frobenius_3x3`, STF 직교 projection | ✅ **핵심 재사용** |
| `integration_tests.rs` | 116 | 검증 테스트 | 🟡 **재실행 후 판정** |

### 2.2 재사용 범위 요약

- **Core primitives (coupling, tensor, lm_indexing)**: 988 줄 전량 재사용 가능. 이들은 pure math / formal layer 로서 MB-95 와 무관.
- **Hierarchy assembly (hierarchy_matrix, tca_lm)**: 568 줄 재사용 가능.
- **Hierarchy struct / step (hierarchy)**: struct 유지, step 은 Rodas5P / IMEX-ARK4 integrator 로 교체 필요.
- **Collision (collision_lm)**: 359 줄 중 **electron-frame ζ̃ 유도 확인 후** 재유도 필요 여부 판정. CAMB 의 κ̇ 대신 electron-frame rate 이 DESIGN LAW 요구사항.
- **Phase 4 보류 (m_decomposition, streaming_lm)**: 725 줄은 Bianchi extension 에서 활용.

**총 재사용 가능: ~1,900 줄 (63%)**. 재유도 / 재작성 필요: ~1,150 줄 (37%). 이것은 sync_gauge_camb.rs 4,316 줄 중 60–70% 재작성 예상보다 훨씬 작음 — `src/pstf/` 가 이미 많은 기반을 제공.

### 2.3 누락 모듈 (PR-020..024 에서 신설)

| 신설 모듈 | 역할 | 대상 PR |
|---|---|---|
| `src/solver/pstf_primary/mod.rs` | 서브모듈 등록 | PR-020 |
| `src/solver/pstf_primary/layout.rs` | `PstfLayout` (state vector layout, FLRW version) | PR-020 |
| `src/solver/pstf_primary/hierarchy_wrapper.rs` | `src/pstf/hierarchy.rs` 를 Rodas5P compatible form 으로 bridge | PR-020 |
| `src/solver/pstf_primary/ic.rs` | Adiabatic IC (PSTF variables) | PR-021 |
| `src/solver/pstf_primary/rhs.rs` | Photon/ν/Thomson RHS + Jacobian | PR-022 |
| `src/solver/pstf_primary/metric.rs` | 1+3 metric scalar sector | PR-023 |
| `src/solver/pstf_primary/source.rs` | PSTF LoS source | PR-024 |
| `src/solver/pstf_primary/solve.rs` | `solve_pstf_spectrum()` | PR-024 |
| `src/core/ssot.rs` 의 `pstf` submodule | PSTF SSOT helpers (pi_abc, doppler_covariant, quad_covariant) | PR-021..024 |
| `src/core/ssot.rs` 의 `mb95` submodule | 기존 polter/doppler_source/quad_source 이동 | PR-026 (Phase 3) |

---

## §3. PSTF ↔ MB-95 변수 매핑 Table Draft

Phase 2 (PR-025) equivalence test 의 기반이 되는 **변수 대응 관계**. FLRW 극한에서만 유효.

### 3.1 Photon sector

| MB-95 (CAMB) | PSTF | FLRW 관계 |
|---|---|---|
| Θ_0 (= δ_γ/4) | I_0^{(γ)} = (1/4π) ∫ I dΩ | Θ_0 = I_0^{(γ)} / Ī (FLRW limit, normalized) |
| Θ_ℓ (ℓ ≥ 1) | I_{A_ℓ}^{(γ)} (STF tensor) | Θ_ℓ = I_{A_ℓ} · n^{⟨A_ℓ⟩} / (STF norm) |
| E_ℓ (E-mode polarization) | E_{A_ℓ}^{(γ)} (STF tensor) | E_ℓ = E_{A_ℓ} · n^{⟨A_ℓ⟩} / (STF norm) |
| B_ℓ (B-mode polarization) | B_{A_ℓ}^{(γ)} (STF tensor) | 동일 구조 |
| polter = 2Θ₂/5 + 3E₂/5 | Π^{(γ)}_{ab} = Θ₂^{STF} + E₂^{STF} + ... | FLRW: polter projected form |
| pig = 4·Θ₂ | Π_pig = 4 · I_2^{(γ)} (수치) | direct factor-4 |

STF norm: `stf_normalization(ℓ)` 이 이미 `src/pstf/coupling.rs` 에 정의됨.

### 3.2 Neutrino sector

| MB-95 | PSTF | FLRW |
|---|---|---|
| N_ℓ (massless) | I_{A_ℓ}^{(ν)} | 동일 (photon 과 평행) |
| ψ_ℓ(q) (massive) | I_{A_ℓ}^{(ν,q)} (q-indexed STF) | q 의미 동일 |

### 3.3 Metric sector — **가장 주의 필요**

| MB-95 | PSTF | FLRW 관계 |
|---|---|---|
| h (synchronous) | **없음** (gauge choice 에 따라 consistent 하지 않음) | PSTF 는 covariant 변수. gauge 선택 무관. |
| η (synchronous) | **없음** | 동일 |
| σ_{MB} = (h'+6η')/(2k) | **물리적 대응 없음** (gauge artifact) | FLRW 에서 PSTF 의 Z_{ab} = 0 이 σ_{MB} ≠ 0 과 양립 |
| Φ (Newtonian) | Φ^{1+3} = -(1/2k²) D² h | gauge-invariant Bardeen potential. PSTF 에서 직접 표현 |
| Ψ (Newtonian) | Ψ^{1+3} = -(1/2k²) D² h - 8π G a² δT^{ij} n_i n_j / 3 | 동일 |
| — | Z_{ab} (PSTF "electric" Weyl tensor) | FLRW 에서 Z_{ab} = 0; Bianchi 에서 ≠ 0 |
| — | σ_{ab} (geometric shear, extrinsic curvature) | FLRW 에서 σ_{ab} = 0. 완전히 다른 σ. |

**핵심 주의**: `i_sigma` (MB-95) 와 `sigma_ab` (PSTF/Bianchi) 는 **완전히 다른 양**. `src/solver/pstf_primary/layout.rs` 에서는 `i_sigma_metric_ab` 같은 명시적 naming 을 쓴다. `i_sigma` 재사용 금지.

### 3.4 Fluid sector

| MB-95 | PSTF | FLRW |
|---|---|---|
| δ_c (CDM density) | Δ_c = ∇_a v_c^a / H + ... (covariant) | FLRW: Δ_c = δ_c / H² scaling 확인 |
| δ_b (baryon) | Δ_b | 동일 |
| v_b (baryon velocity) | v_{ab}^{(b)} (STF symmetric part) | FLRW: v_{ab}^{(b)} = v_b · (n_a n_b − δ_{ab}/3) scalar projection |

### 3.5 Source term 매핑 (LoS integrand)

| MB-95 source | PSTF source | 관계 |
|---|---|---|
| S_SW = g·(δ_γ/4 + 2Φ + η_mb/2) | S_SW^{PSTF} = g·(I_0 + 2Φ^{1+3}) | FLRW: η_mb/2 는 gauge artifact, PSTF 에서 흡수 |
| S_Dop = ((σ_{MB} + v_b)·g' + ...) / k | S_Dop^{PSTF} = D^a v_{ab}^{(b)} · g · n^b (covariant) | FLRW: σ_{MB} 소실, v_b·g' 유지 |
| S_Quad = (5/8k²)·[...] | S_Quad^{PSTF} = Π_{ab}^{(γ)} · collision kernel | polter 대응 |
| S_E = g·polter | S_E^{PSTF} = (3/4)·g·Π_BASS | 이미 `EmodeConvention::PiBass` 로 준비됨 |

---

## §4. PR-020 Concrete Scope

### 4.1 새 파일

- `src/solver/pstf_primary/mod.rs` — 서브모듈 등록, `pub(crate) mod layout; pub(crate) mod hierarchy_wrapper;`
- `src/solver/pstf_primary/layout.rs` — `PstfLayout` struct:
  ```rust
  pub(crate) struct PstfLayout {
      pub(crate) ell_max_gamma: usize,
      pub(crate) ell_max_nu: usize,
      pub(crate) ell_max_pol: usize,
      pub(crate) nq_massive: usize,
      pub(crate) ell_max_m: usize,
      pub(crate) n_state: usize,
      // Photon intensity STF
      pub(crate) i_gamma_0: usize,
      // Photon E-mode STF
      pub(crate) i_e_0: usize,
      // Photon B-mode STF
      pub(crate) i_b_0: usize,
      // Massless neutrino STF
      pub(crate) i_nu_0: usize,
      // Massive neutrino STF (q-indexed)
      pub(crate) i_psi_0: usize,
      // Metric 1+3 covariant (no h, no η_synchronous)
      pub(crate) i_phi_cov: usize,
      pub(crate) i_sigma_metric_ab: [usize; 5],  // 5 STF components of σ_{ab}
      // Fluid
      pub(crate) i_delta_c: usize,
      pub(crate) i_delta_b: usize,
      pub(crate) i_v_b_ab: [usize; 5],   // STF components
  }
  ```
  `MIN_LMAX_*`, `has_pol()`, `validate_layout_invariants()` 는 MB-95 과 동일 pattern.

- `src/solver/pstf_primary/hierarchy_wrapper.rs` — `src/pstf/hierarchy.rs::PSTFHierarchy` 를 Rodas5P `LinearProfileDyn` compatible wrapper 로 감쌈.

### 4.2 수정 (minimal)

- `src/lib.rs` — `pub(crate) mod solver;` 하위에 이미 있으므로 추가 불필요. `src/solver/mod.rs` 에 `pub(crate) mod pstf_primary;` 등록 (1 줄).

### 4.3 TDD gate (PR-020)

**Identity tests**:
- `identity_layout_validator_rejects_zero_lmax` — `PstfLayout::new(0, 0, 0, 0, 0)` 는 assert
- `identity_flrw_projection_reduces_to_mb95_recursion` — `coupling::free_streaming_{down,up}` 이 FLRW 에서 `k·ℓ/(2ℓ+1)`, `k·(ℓ+1)/(2ℓ+1)` 재생산 (이것은 `coupling.rs` 에서 이미 구현된 값의 수치 검증)

**Limit tests**:
- `limit_sigma_ab_zero_no_structure_constants` — `shear_coupling_{down,up}` 에 `σ_{ab} = 0` 대입 시 항 소실

**Channelwise tests**:
- `channelwise_gamma_nu_independent_layout` — photon 과 neutrino 인덱스 영역 중첩 없음

**Regression test**:
- `regression_d2_bit_identical` — `dump_dl_spectrum_sparse` 재실행하여 D_2 = 1002.086744 유지 (PR-020 은 production 미연결)

**Caveat test**:
- `caveat_layout_has_no_synchronous_metric_fields` — `i_h_sync`, `i_eta_sync` 필드 존재 안 함을 컴파일 타임 assert (이름으로 추론 가능)

### 4.4 TDD gate NOT included in PR-020

아래는 PR-021..024 몫:

- IC (`adiabatic_ic_pstf`) — PR-021
- RHS / Jacobian 정합성 — PR-022
- Φ^{1+3} ↔ Φ_{Newtonian} reduction — PR-023
- LoS source integrand — PR-024

---

## §5. Rollback triggers

- `src/pstf/` 기존 모듈 unit test 중 하나라도 failing (의존성 깨짐)
- `dump_dl_spectrum_sparse` D_2 drift (PR-020 은 production 무접촉이므로 발생 안 해야 함)
- `cargo build --lib --release` 실패
- `PstfLayout::new` 에서 structural invariant violation

---

## §6. Pre-PR checklist

PR-020 scaffold 실제 작성 전 확인:

- [ ] `src/pstf/integration_tests.rs` 재실행하여 현재 통과 상태 확인
- [ ] `src/pstf/` 의 모든 public API 목록 고정 (이 문서 §2.1 의 3rd 컬럼이 PR 작성 시 API 참조 역할)
- [ ] `src/core/ssot.rs` 에 `pstf` submodule 스텁 추가 여부 결정 (PR-020 포함 vs PR-021 포함)
- [ ] `src/core/ssot.rs::polter` 등을 `mb95` submodule 로 이동하는 것은 PR-026 에서 (지금 이동하면 PR-020 scope 과잉)
- [ ] `src/solver/pstf_primary/` 폴더 생성 + `mod.rs` 스텁 만으로 이 PR 을 마무리할지, `layout.rs` 까지 포함할지 결정 → 현재 계획은 후자 (500–900 줄 규모)

---

## §7. 후속 PR 의 pre-audit 일정

| PR | Pre-audit doc 작성 시점 | 의존성 |
|---|---|---|
| PR-021 (IC) | PR-020 closure 직후 | PR-020 |
| PR-022 (RHS) | PR-021 closure 직후 | PR-021 |
| PR-023 (metric) | PR-022 closure 직후 (병렬 가능) | PR-020 |
| PR-024 (LoS source) | PR-022, PR-023 closure 후 | PR-022, PR-023 |
| PR-025 (equivalence) | PR-024 closure 후, Phase 2 개시 | Phase 1 전체 |
| PR-026 (backend switch) | PR-025 closure 후 | PR-025 |

---

## §8. 위험 및 불확실성

- **`src/pstf/` 모듈의 현재 test pass 상태 미확인**. 재실행해서 기본 통과 여부 확인 필요 (Phase 0 작업)
- **Collision operator `electron-frame ζ̃`** 의 현 `collision_lm.rs` 구현 정확성 재검증 필요. DESIGN LAW 요구사항이라 Thomson rate κ̇ 를 그대로 쓰면 안 됨.
- **Metric sector 대응** (§3.3) 이 이 문서에서 가장 많이 재검토 필요. Bardeen potential 의 PSTF 표현은 표준적이지만 code 로 옮길 때 sign / factor 주의. 별도 mini-reference 작성 고려 (Tsagas 2008 §2.3 기반).
- **FLRW equivalence tolerance ±0.5%** 이 달성 가능한지 불확실. MB-95 는 synchronous gauge, PSTF 는 covariant 이므로 초기 조건의 gauge fixing 에서 ~1% 수준 drift 가능. PR-025 에서 실제 측정 후 필요 시 tolerance 완화 또는 MB-95 쪽 gauge transform 적용.

---

*본 문서는 PR-020 착수 전 최종 확정. 변경 시 SSOT_POLICY §17.6 와 ROADMAP_PHASE_I_TO_L §3 동반 갱신.*
