# PR-022 Design Document — PSTF RHS (Sub-track Split Proposal)

> **Status**: 📝 **DESIGN (pre-audit)** — 2026-04-17
> **Target PR**: PR-022 (Phase 1 single-biggest, weight 15)
> **Companion**: `docs/ROADMAP_PHASE_I_TO_L.md` v2.0 §3 / `PR_CONSTITUTION` §9/§10/§11
> **Dependency**: PR-020 ✅, PR-021 ✅
> **Target score**: 8 (각 sub-track) → W·S/10 = 12.0 on full PR-022 closure

---

## §1. Motivation — 큰 PR 위험과 sub-track 의 필요성

PR-022 의 단일 PR 설계:

```
src/solver/pstf_primary/rhs.rs (~600–900 줄)
  ├─ photon free-streaming RHS
  ├─ neutrino free-streaming RHS
  ├─ Thomson collision (electron-frame ζ̃)
  ├─ Jacobian (sparse, Rodas5P 호환)
  └─ RHS entry point (state → dy/dη)
```

이것을 **한 세션 에 완결** 하는 것은 다음 이유로 리스크가 큼:

1. **Anti-local-min rule (§10) 의 trigger 확률 높음** — 4 개 하위 성분 중 하나라도 실패하면 전체 PR 이 멈춤. PR-020 의 `flrw_norm_ratio_down` 실패 패턴이 4 배 확률로 발생 가능.

2. **Metric coupling `hdot/6` 의존성** — MB-95 의 `dy[lay.theta(0)] = -k·Θ_1 − hdot/6` 에서 `hdot` 은 synchronous gauge variable. PSTF 에서 대응 metric term 은 **PR-023 (metric sector)** 에 정의됨. 순환 의존. 해결 방안: PSTF RHS 의 metric coupling 을 **placeholder** 로 두고, PR-023 완료 후 wire up.

3. **Electron-frame ζ̃ 규약 결정** — `src/pstf/collision_lm.rs` 의 현 구현이 frame 명시 없이 작성됨. DESIGN LAW 는 electron-frame 요구. 재유도 필요. 이것을 RHS 와 섞으면 debug 가 어려워짐.

4. **Jacobian 이 독립 검증 단계 필요** — Rodas5P 는 analytical Jacobian 기반. RHS 와 Jacobian 이 정합한지 finite-difference check 필수. 이것은 개별 sub-track 에서만 가능.

5. **G2 FLRW gate 의 구체성 문제** — "PSTF RHS(FLRW 극한) ≡ MB-95 RHS" 는 공식화 가능하나, 전체 RHS 비교는 많은 변수 (h, η, σ, v_b, etc.) 가 얽혀 localization 어려움. Sub-track 별로 비교 범위를 좁히면 G2 가 더 tight.

### 1.1 Sub-track 분할안 (권장)

**PR-022a — PSTF free-streaming RHS only** (collision 제외)

- Scope: photon + neutrino hierarchy 의 free-streaming 부분만
- Dependency: PR-020 ✅, PR-021 ✅
- Weight: 6 (PR-022 전체 weight 15 의 subset)
- Target score: 7 (G1+G3+G4 pass 가능, G2 는 metric placeholder 때문에 부분 pass)
- G2 evidence: PSTF free-streaming RHS(FLRW 극한, metric=0) 와 MB-95 free-streaming RHS(hdot=0) 의 **free-streaming 부분만** 비교. κ̇=0 (collision 꺼짐) 에서 dΘ_ℓ/dη 의 k/(2ℓ+1) recursion 재생산 확인.
- G4 evidence: MB-95 `build_rhs_sync_v2` 의 collision-off path (opac=0) 대비.

**PR-022b — Electron-frame Thomson collision** (PSTF primary 모듈에 신규 작성)

- Scope: `src/solver/pstf_primary/collision.rs` — electron-frame ζ̃ Thomson collision 유도 + 기존 `collision_lm.rs` 와의 비교 + DESIGN LAW 명시 준수
- Dependency: PR-022a ✅, `src/pstf/collision_lm.rs` 감사 완료
- Weight: 5
- Target score: 8
- G2 evidence: PSTF collision-only RHS (free-streaming=0, metric=0) 와 MB-95 의 `-opac·(F_1 − v_b), -(9/10)·opac·Θ_2 + (3/20)·opac·E_2` 와 FLRW 극한 수치 일치
- G4 evidence: `src/pstf/collision_lm::build_collision` 과의 cross-check (두 경로 모두 PSTF-flavored 지만 규약 다를 수 있음)

**PR-022c — Jacobian (sparse Rodas5P-compatible)**

- Scope: `src/solver/pstf_primary/jacobian.rs` — sparse Jacobian 구조 + FD check
- Dependency: PR-022a, PR-022b 모두 ✅
- Weight: 4
- Target score: 7
- G2 evidence: J^{PSTF}(FLRW) ≈ J^{MB-95}(synchronous gauge) 의 block 단위 비교 — sparsity pattern 과 non-zero 값
- G3 evidence: FD Jacobian (numerical) 과 analytical Jacobian 의 1e-6 일치

**합산**: W_total = 6 + 5 + 4 = **15** (원 PR-022 weight 유지). 각 sub-track 의 target score 로부터 합산 W·S/10 = 4.2 + 4.0 + 2.8 = **11.0** (원래 target 12.0 보다 약간 낮음, 단 risk reduction 으로 정당).

### 1.2 단일 PR 대비 비용-이익

| 항목 | 단일 PR-022 | 3 sub-track |
|---|---|---|
| 세션 수 | 1 (낙관) / 3+ (현실) | 3 (예측 가능) |
| 실패 시 rollback 범위 | 전체 | 해당 sub-track 만 |
| G2 gate tightness | 약함 (많은 변수 얽힘) | 강함 (각 sub-track 별 명확) |
| PR weight 진행률 | 0 → 12 (또는 0) | 0 → 4.2 → 8.2 → 11.0 |
| Anti-local-min 발생 확률 | 높음 | 낮음 |
| design doc 복잡도 | 크고 뭉뚱그려짐 | 각각 집중 |

**결론**: Sub-track 분할 채택. 이 문서는 **PR-022a (free-streaming RHS)** 에 집중.

---

## §2. Pre-audit — src/pstf/ 및 MB-95 참조 확인

### 2.1 `src/pstf/collision_lm.rs` 의 frame 규약 감사

Grep 결과 (§1.5.1):

- **frame 명시 주석 부재** — "electron", "rest frame", "u_e" 어디에도 언급 없음
- `build_collision(layout, kappa_dot, r_b)` signature 이 `κ̇` 를 **scalar** 로 받음 — direction-dependent 옵티컬 뎁스 `κ̇(ê)` 은 지원 안 함
- `ζ_{2m} = (2/5)F_{2m} + E_{2m}` 규약 — CAMB 의 Π = F_2/10 + (9/15)E_2 를 F=4·Θ brightness 로 재정규화한 결과. CAMB-like, frame 명시 없음

**결정**: PR-022b 에서 새 `src/solver/pstf_primary/collision.rs` 를 작성하되:

- 기본 구현은 `collision_lm` 과 동일 공식 사용 (electron-frame = n^a frame at FLRW limit)
- 명시적 `FrameConvention` enum 도입: `ElectronRestFrame` (DESIGN LAW default) vs `HypersurfaceNormalFrame` (MB-95 equivalent at FLRW)
- FLRW 에서는 두 frame 이 일치. Bianchi 로 확장 시 tilt velocity v_e 로 변환 필요 (Phase 4)
- Cross-check: PR-022b G4 에서 `collision_lm::build_collision` 의 출력과 bit-identical 일치 (FLRW, tilt=0)

이것은 PR-020 의 `flrw_norm_ratio_down` 함정 재발을 피함 — scope 을 축소하고 현재 collision_lm 값을 **자체 SSOT** 로 승격하되 frame 명시를 추가하는 보수적 접근.

### 2.2 MB-95 photon RHS 의 구조 (PR-022a 대상)

`sync_gauge_camb.rs:491–529` 의 핵심:

```rust
dy[theta(0)] = -k·θ(1) − hdot/6                       // ℓ=0
dy[theta(1)] = k/3·(θ(0) − 2·θ(2)) − opac·(θ(1) − v_b/3)   // ℓ=1
dy[theta(2)] = k/5·(2·θ(1) − 3·θ(3)) − 0.9·opac·θ(2)
               + (3/20)·opac·E(2)                       // ℓ=2
dy[theta(ell)] = k/(2ℓ+1)·[ℓ·θ(ℓ-1) − (ℓ+1)·θ(ℓ+1)]
                 − opac·θ(ℓ)                            // ℓ≥3
dy[theta(lg)] = k·θ(lg-1) − (lg+1)/τ·θ(lg) − opac·θ(lg) // truncation
```

**PR-022a 의 대응**: free-streaming 부분만 구현 (opac=0, collision 항 없음):

```rust
dy[i_photon_i_m0(0)] = -k · state[i_photon_i_m0(1)] + metric_monopole_coupling  // ← placeholder
dy[i_photon_i_m0(1)] = k/3 · (state[i_photon_i_m0(0)] - 2·state[i_photon_i_m0(2)])
dy[i_photon_i_m0(ell)] = k/(2ℓ+1) · [ℓ·state[ℓ-1] - (ℓ+1)·state[ℓ+1]]   // ℓ≥2
// ℓ=lg: truncation (tau-based closure)
```

`metric_monopole_coupling` 은 PR-022a 에서는 **0 (placeholder)**. PR-023 (metric sector) 에서 wire up.

### 2.3 MB-95 neutrino RHS

`sync_gauge_camb.rs:532–...` — photon 과 구조적 평행, collision 없음 (free-streaming 즉시).

```rust
dy[nu(0)] = -k·N_1 − hdot/6
dy[nu(1)] = k/3·(N_0 − 2·N_2)
dy[nu(ell)] = k/(2ℓ+1)·[ℓ·N_{ℓ-1} − (ℓ+1)·N_{ℓ+1}]  // ℓ≥2
```

PSTF 대응은 photon 과 동일 구조. Placeholder 처리 동일.

---

## §3. PR-022a 구체 scope

### 3.1 새 파일

- `src/solver/pstf_primary/rhs_free.rs`:

  ```rust
  pub(crate) struct RhsInputs {
      pub(crate) k: f64,
      pub(crate) tau: f64,   // for ℓ_max tau-based truncation
      pub(crate) metric_monopole_source: f64,  // placeholder, PR-023 wire-up
  }

  pub(crate) fn pstf_free_streaming_rhs(
      state: &[f64],
      dy: &mut [f64],
      inputs: &RhsInputs,
      layout: &PstfFlrwLayout,
  );
  ```

  Collision 호출 없음. Metric coupling 은 `inputs.metric_monopole_source` 를 Θ_0 와 N_0 방정식에만 투입 (나머지는 free-streaming 순수).

### 3.2 TDD gate (PR-022a)

**Identity tests (3)**:
- `identity_monopole_rhs_matches_mb95_freestream` — κ̇=0, hdot=0 에서 `dΘ_0/dη = -k·Θ_1` bit-identical
- `identity_recursion_matches_mb95_freestream` — ℓ ∈ [2, 10] 에서 `dΘ_ℓ/dη = k/(2ℓ+1)·[ℓ·Θ_{ℓ-1} - (ℓ+1)·Θ_{ℓ+1}]` bit-identical
- `identity_truncation_matches_mb95` — ℓ=lg 에서 `k·Θ_{lg-1} - (lg+1)/τ·Θ_{lg}` bit-identical (opac=0)

**Limit tests (2)**:
- `limit_k_zero_rhs_vanishes` — k=0 에서 free-streaming RHS = 0
- `limit_metric_source_zero_pure_freestream` — `metric_monopole_source = 0` 에서 RHS 가 pure free-streaming (hdot 없는 MB-95 와 일치)

**Channelwise tests (2)**:
- `channelwise_photon_nu_identical_structure` — free-streaming 에서 photon 과 neutrino RHS 공식 동일
- `channelwise_polarization_unaffected_freestream` — E_ℓ, B_ℓ 는 free-streaming RHS 에서 자기 자신의 recursion 만 (photon intensity 와 decouple)

**Regression tests (2)** ← G2 FLRW gate
- `regression_rhs_matches_mb95_freestream_kappa_zero` — `κ̇=0, hdot=0` 에서 PSTF free-streaming RHS 의 각 성분이 MB-95 `build_rhs_sync_v2` (opac=0 특수화) 와 **1e-12 이내 일치**
- `regression_multiple_k_values` — k ∈ {1e-4, 1e-2, 1e-1} Mpc⁻¹ 모두에서 위 일치

**Caveat tests (2)**:
- `caveat_collision_not_applied` — `κ̇` parameter 없음 (collision 이 이 함수에서 완전히 제외됨 증명)
- `caveat_metric_source_placeholder` — `metric_monopole_source = 42` 같은 sentinel 값에 대해 Θ_0, N_0 만 영향 받음 확인

**총 11 tests**. PR-020 (12) 와 PR-021 (10) 과 유사 규모.

### 3.3 Gate forecast

| Gate | 예상 | 근거 |
|---|---|---|
| G1 COMPILE | ✅ | 새 파일 추가, 기존 회귀 없음 예상 |
| **G2 FLRW** | **부분 ✅** | `regression_rhs_matches_mb95_freestream_kappa_zero` 이 직접 evidence. 단, metric coupling 이 placeholder 이라 "full FLRW" 가 아닌 "free-streaming sub-component FLRW" 수준 |
| G3 PHYS | ✅ | k-zero limit, recursion identity, photon-ν equivalence |
| G4 CROSS | ✅ | MB-95 `build_rhs_sync_v2` (opac=0) 과 직접 대조 |

**Score: 7/10** (G2 가 부분 pass 이므로 cap 7, 정당)
- Weight 6 × Score 7 / 10 = **4.2** W·S/10
- Phase 1 진행률: 30.1% → 30.1 + 4.2/105 = **34.1%**

---

## §4. Anti-local-minimum 사전 trigger

Pre-audit §6 pattern 적용:

1. **Metric placeholder 가 RHS regression test 를 오염** — 2회 fail 시 STOP. Placeholder 값을 `0.0` 대신 `compute_metric_source_mb95_equivalent()` 같은 helper 로 대체. 이것이 PR-022a 의 scope 을 침범하면 PR-023 먼저로 순서 조정.

2. **k/(2ℓ+1) recursion 이 MB-95 과 bit-identical 안 됨** — 2회 fail 시 STOP. `pstf::coupling::free_streaming_*` 값과 inline implementation 의 차이 의심 → 전자만 사용하도록 strict 적용.

3. **Truncation term 불일치** — `(lg+1)/τ·Θ_{lg}` 의 τ 정의 (conformal time vs some other variable) 차이. MB-95 의 `tau_safe = tau.max(1e-10)` 을 PSTF 에서 그대로 가져올 것.

---

## §5. Hallucination checklist 준비

PR-022a closure 시 paste 할 것:

- [ ] `cargo build --lib --release` output
- [ ] `solver::pstf_primary::rhs_free::tests` test count (11 예상)
- [ ] `regression_rhs_matches_mb95_freestream_kappa_zero` 의 구체 ℓ, k 별 수치
- [ ] `dump_dl_spectrum_sparse` D_2 = 1002.086744 bit-identical 재확인 (8th consecutive)
- [ ] 기존 5 슈트 (pstf / source::registry / core::ssot / pstf_primary::layout / pstf_primary::ic) 회귀 없음

---

## §6. PR-022b, PR-022c preview

### PR-022b (Electron-frame Thomson collision)

**Dependency on PR-022a**: PR-022a 의 RHS 가 `metric_monopole_source` placeholder 로 잘 작동하는지 확인 후.

**Scope**:
- `src/solver/pstf_primary/collision.rs`
- `FrameConvention` enum: ElectronRestFrame (DESIGN LAW) vs HypersurfaceNormalFrame (MB-95 equivalent)
- FLRW 에서는 두 frame 이 수치적으로 일치
- `collision_lm` 의 규약을 frame-명시 형태로 승격 + DESIGN LAW 주석 추가

**TDD gate**: 11개 예상 (identity 3 + limit 2 + channelwise 2 + regression 2 + caveat 2). 특히 regression 에서 MB-95 `opac·(F_1 - v_b)` term 과 직접 bit-identical.

### PR-022c (Jacobian)

**Dependency**: PR-022a ✅ + PR-022b ✅.

**Scope**:
- `src/solver/pstf_primary/jacobian.rs`
- Sparse Jacobian structure (Rodas5P-compatible)
- FD check: numerical Jacobian vs analytical, 1e-6 일치

**TDD gate**: 9개 예상.

---

## §7. 진행률 projection (PR-022 전체 완료 후)

| 단계 | W·S/10 | Phase 1 % |
|---|---:|---:|
| 현재 (PR-021 closure) | 31.6 | 30.1% |
| PR-022a closure | 35.8 | 34.1% |
| PR-022b closure | 39.8 | 37.9% |
| PR-022c closure | 42.6 | 40.6% |

PR-022 전체 완료 후 Phase 1 진행률은 **40.6%** 로 원 target 41.5% 에 근접 (sub-track 분할로 인한 0.9pp 손실은 risk reduction 으로 정당).

---

## §8. 위험 및 불확실성

1. **Metric placeholder 가 tight G2 gate 의 방해** — 주요 위험. 완화: PR-022a 의 G2 를 "free-streaming component only" 로 축소 정의. Full G2 는 PR-023 이후.

2. **PSTF 의 "truncation" 방식이 MB-95 과 다를 가능성** — MB-95 은 `(lg+1)/τ` multiplicative term 으로 ℓ_max boundary 처리. PSTF 에서는 `src/pstf/coupling.rs` 의 `free_streaming_up(lg)` 이 표준 CG coefficient 로 truncation term 을 자체적으로 제공할 가능성. 확인 필요.

3. **τ (conformal time) 의 PSTF 정의** — PR-023 이 metric 을 정의하기 전까지 τ 값이 어디서 와야 하는가? PR-022a 에서는 `RhsInputs::tau` 로 caller 가 주입. PR-023 에서 consistent 한 tau 정의 확정.

4. **Neutrino RHS 의 photon 과의 parallelism 검증** — MB-95 에서는 완전히 평행하지만, PSTF 에서 `I_{A_ℓ}^{(ν)}` 과 `I_{A_ℓ}^{(γ)}` 의 normalization 이 다를 수 있음 (CAMB 의 brightness convention 이 photon 에만 적용 가능성). PR-022a 의 `channelwise_photon_nu_identical_structure` test 가 이것을 포착.

---

## §9. Pre-PR checklist (PR-022a 착수 전)

- [x] `src/pstf/collision_lm.rs` 감사 완료 — frame 명시 부재 확인, PR-022b 로 이관
- [x] MB-95 `build_rhs_sync_v2` 의 free-streaming 부분 격리 가능성 확인 — `opac=0` 설정으로 가능
- [x] `pstf::coupling::free_streaming_{down,up}` 값이 PR-020 에서 self-consistent 확인됨
- [ ] `RhsInputs::tau` 의 정의 (`η_0 - η_now` vs `η_now`) 확정 — PR-022a scaffold 시 MB-95 convention 확인 후 결정
- [ ] `metric_monopole_source` placeholder 의 sentinel value (0.0 vs NaN 감지용) 결정

---

## §10. 즉시 다음 행동

다음 세션에서:

1. **PR-022a scaffold 착수** — `src/solver/pstf_primary/rhs_free.rs` 신설, 11 tests 구현
2. Pre-PR checklist 마지막 2 항목 (tau definition, placeholder value) scaffold 시 결정
3. G2 FLRW gate 측정 — 구체 ℓ, k 별 수치 paste
4. D_2 bit-identical 재확인 (8th consecutive commit)
5. `pr-022a.md` closure delta + scoreboard 갱신

PR-022a 완료 후 동일 pattern 으로 PR-022b (electron-frame collision) 진입.

---

*PR-022 sub-track 분할 결정 문서. PR-022a, PR-022b, PR-022c 각각 별도 closure delta 를 작성할 것.*
