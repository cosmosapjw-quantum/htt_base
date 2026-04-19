# Full Bianchi coverage — extension roadmap (post-LB)

**Drafted**: 2026-04-19 (LB-6 직후)
**Status**: planning document (design-only; no code written by this plan)
**Scope**: LB 완료 상태의 `LowellBianchiIntegrator` 를 "모든 일반 Bianchi 모델 + tilted sector" 까지 확장하기 위한 다단계 로드맵.
**Parent specs**: `docs/lowell_bianchi/README.md` §6/§7; LB-0 … LB-6 완료 스펙.

---

## 0. "9개 Bianchi 모델" 이라는 표현에 대한 정의

Bianchi-Behr 분류의 공식 개수는 **11개** (LB 레포에서는 `ALL_BIANCHI_TYPES` 에 그대로 나열됨):

| Class A (a_twist = 0, unimodular) | Class B (a_twist ≠ 0) |
|---|---|
| I, II, VI₀, VII₀, VIII, IX | III, IV, V, VI_h, VII_h |

"9개 Bianchi" 라는 흔한 표현은 보통 VI₀·VII₀ 를 VI_h·VII_h 의 h→0 극한으로 흡수해서 세는 관례 (혹은 III = VI_{-1} 을 VI_h 에 흡수). **본 플랜은 11개 type 을 모두 대상**으로 하며 "9개" 는 literature convention 을 반영하기 위한 별칭으로만 사용한다. "tilted / non-tilted 각각 11개" → 전체 coverage 대상 = **22 configurations**.

Reference conventions:
- Ellis & MacCallum, *Commun. Math. Phys.* 12, 108 (1969)
- Wainwright & Ellis, *Dynamical Systems in Cosmology* (CUP 1997) — per-type background
- Pontzen & Challinor, *PRD* 79, 103518 (2009) — Class B frame (`a_α = (0, a, 0)`) 고정
- King & Ellis 1973; Barrow-Koivisto; lowell §11.3 (tilted sector)

---

## 1. 현재 코드가 **이미** 지원하는 것 (LB-6 완료 시점)

| Sub-system | Status | Evidence |
|---|---|---|
| `StructureConstants` 11 types + Jacobi validation | ✅ full | `bass/background/bianchi_types.py` (`type_*_constants`, `get_type`) |
| 배경 쉬어 소스 per-type (Class A + Class B 11개) | ⚠️ provisional | `bass/transport/shear_sources.py` `SOURCE_STATUS` (I/V "VALIDATED"; 9개 "PROVISIONAL") |
| 배경 integrator (`solve_bianchi_background`) | ✅ 11 type dispatch-ready | `bass/background/einstein_bianchi.py` |
| LB-5 unified integrator (`LowellBianchiIntegrator.run`) | ✅ cosmology-agnostic | `bass/hierarchy/integrator.py` |
| Orthogonal (β=0) PSTF hierarchy (T1/T2/T3/T8/T9) | ✅ | `bass/hierarchy/hierarchy_rhs.py` (LB-2a + LB-2b) |
| Closure strategies (HardCut / FreeStream / PowerLaw / TCA) | ✅ | `bass/hierarchy/closure.py` (LB-3) |
| Thomson PSTF collision (orthogonal kernel) | ✅ | `bass/collision/thomson_pstf.py` (LB-4) |
| Tilted visibility Layer A (scalar × `cosh β + sinh β ê·v̂_e`) | ✅ | `bass/collision/tilted_visibility.py` (LB-4) |
| Reduced ν fluid (Δ_ν, q_ν, π_ν, G₃) | ✅ | `bass/hierarchy/neutrino_reduced.py` (LB-5) |
| Kolb-table regression (Type I, FLRW-limit) | ✅ | `bass/integration/test_lowell_bianchi.py` (LB-6) |

## 2. 현재 코드의 **결함 / 빠진 부분**

| Gap | Affected types | Affected sector | Severity for "9-type 확장" |
|---|---|---|---|
| `anisotropic_3_curvature` returns `None` 로 fall-through | II, III, IV, VI₀, VI_h, VII_h, VIII, IX (8/11) | Hierarchy RHS ³R_{ab} 커플링 | **P0** |
| ∇̃ (공간 구조상수 연산자) class-B 타입에서 `NotImplementedError` | III, IV, V, VI_h, VII_h (5/11) | Hierarchy 전반 + k≠0 perturbation | **P0** |
| Shear source `PROVISIONAL` (계산식만, validation 없음) | 9/11 | 배경 | **P1** |
| Tilted species non-perturbative β (full Lorentz boost on multipoles) | 전 type | Collision + Hierarchy | **P0** |
| Vorticity ω_a ≠ 0 (tilted 4-velocity) | 전 tilted | T4/T5/T6/T7 kinematic terms | **P0** |
| 4-acceleration A_a ≠ 0 coupling | Class B + tilted | T4/T5 | **P0** |
| Thomson kernel full Lorentz (Layer B) | 전 tilted | Collision | **P0** |
| B-mode polarization + E-B mixing (tilted) | 전 tilted | Collision + spectrum | **P1** |
| k ≠ 0 perturbation sector | 전 type | 스펙트럼 | **P0** (for C_ℓ) |
| `detect_critical_events` `eta_star`/`chi_star` keys 누락 | 전 type | test 헬퍼 (LB-6 F2 carry) | P2 |
| `einstein_bianchi` Σ-convention vs Ellis convention mismatch | 전 type | 다운스트림 일관성 | **P1** (LB-5 F2 carry) |
| Massive ν (m_ν > 0) 지원 없음 | 전 type | Species | P2 |
| LB-6 regression 은 Type I only — 나머지 10 type 회귀 없음 | 10/11 | Gate | **P1** |
| Spectrum extraction (line-of-sight) 구현 없음 | 전 type | Output | **P0** (for any observable comparison) |
| HTT / likelihood (lowell §14) 없음 | 전 type | Inference | **P0** (for inference loop) |

"**P0**" = 9-type 확장의 critical path; "**P1**" = phase gate 을 막지는 않지만 release-quality 필요; "P2" = nice-to-have / polish.

---

## 3. Target state (플랜 완료 시)

1. `LowellBianchiIntegrator.run(cosmo=<any of 11 types>, beta=<any>, v_hat_e=<any unit vector>)` 가 **예외 없이** 통과하고 모든 post-integration invariant 를 만족한다.
2. 11 type × {orthogonal, tilted} = 22 configuration 별 regression suite 가 green 하다. FLRW 한계 (I, V, VII₀, VII_h→0, IX→BKL isotropic) 는 CAMB Planck-2018 에 < 5 % 정합.
3. Line-of-sight projection 이 각 type 별로 C_ℓ^{TT, EE, TE, BB} + off-diagonal C_{ℓm, ℓ'm'} (anisotropic types) 를 추출한다.
4. HTT decomposition + direction-dependent likelihood (lowell §14) 이 Pontzen-Challinor (2009) Bianchi VII_h / IX spiral patterns 를 reproduce 한다.
5. 모든 외부 코드 금지 조항 유지 (CAMB/CLASS 는 test oracle 에서만).

---

## 4. Phase decomposition — FB (Full Bianchi) roadmap

총 **7 phases, ~30 sessions** (하루 1 세션 기준 약 6 주). 각 phase 는 마지막에 phase-boundary audit + NEXT_SESSION_PROMPT rotation + commit 을 갖는다.

### Phase FB-0 — Convention & dispatch SSOT (3 sessions)

**목표**: 11-type coverage 를 위한 foundation 정비. LB-5/LB-6 carry-forwards 를 청산한 후 모든 후속 phase 가 single-source-of-truth 를 사용.

| Session | 산출물 |
|---|---|
| FB-0.1 | LB-5 F2 resolution: `einstein_bianchi` Σ-convention 을 Ellis (`σ × a³ = const`) 로 정규화; LB-6 I-11/I-12 테스트를 Ellis convention 으로 flip; `proper_shear_at_eta` 변환 업데이트. 배경 전 type regression green. |
| FB-0.2 | `BianchiCosmology(structure, beta=0, v_hat_e=(1,0,0))` field 확장; `make_cosmology(type_label, beta=..., v_hat_e=...)` 팩토리; `IntegratorConfig` 에 tilt 파라미터 노출. β=0 만으로 LB-5/LB-6 regression 유지. |
| FB-0.3 | LB-6 F2 carry: `detect_critical_events` 에 `eta_star`/`chi_star` 키 추가; LB-6 테스트 헬퍼 교체; audit + phase boundary. |

**Exit criteria**: 2,558 baseline 유지 + 신규 FB-0 tests. 모든 11-type factory 가 LB-5 integrator 로부터 예외 없이 호출 가능 (배경 단계 only, hierarchy trivial).

### Phase FB-1 — Per-type background validation (4 sessions)

**목표**: `shear_sources.py` 의 9 "PROVISIONAL" 소스를 "VALIDATED" 로 upgrade. Wainwright-Ellis 문헌 수치 + Kasner 해석해 + Pontzen-Challinor spiral 해석해와 대조.

| Session | 산출물 |
|---|---|
| FB-1.1 | Class A 배경: I / II / VI₀ / VII₀ 에 대해 per-type Kasner exponent limit + Wainwright-Ellis §18 Table 11.1 매치. Source regression promote → "VALIDATED". |
| FB-1.2 | Class A 배경: VIII / IX — Bianchi IX 은 recollapse 가능하므로 `eta_final` auto-terminate 분기 필요 (`solve_ivp` event detection). BKL oscillation 테스트 (기본 axis-symmetric 에서만). |
| FB-1.3 | Class B 배경: III / IV / V / VI_h / VII_h — twist-coupled shear source. Type V 는 open FLRW limit 정합 (기존), VII_h 는 Pontzen-Challinor (2009) spiral 매치. |
| FB-1.4 | `anisotropic_3_curvature` 11-type 구현 (tetrad_state.py). Y-Block `³R_{ab}^{aniso}` 표현식 전 type 에 explicit. Phase-boundary audit. |

**Exit criteria**: `SOURCE_STATUS` 모두 "VALIDATED"; per-type background regression (σ(t) trajectory, a(t) behaviour, ³R_{ab}^{aniso} tensor) pass.

### Phase FB-2 — Hierarchy RHS curved-space T-terms (4 sessions)

**목표**: LB-2b 가 orthogonal 에서 생략했던 T4/T5/T6/T7 + ∇̃ 공간 연산자를 11 type 에서 wire-up.

| Session | 산출물 |
|---|---|
| FB-2.1 | `∇̃` operator dispatch table (lowell §13): FLRW / I / V / VII₀ / IX 에서 harmonic 모드 decomposition. `bass/hierarchy/contractions.py` 의 `NotImplementedError` 우회 해결. |
| FB-2.2 | Class A 나머지 (II / VI₀ / VIII) ∇̃ 구현; spatial Ricci tensor 커플링 T1/T2 correction. |
| FB-2.3 | Class B (III / IV / VI_h / VII_h) ∇̃ 구현 — twist parameter `a` 가 들어간 structure constant 커플링. Type III 특수 (h=-1) 케이스. |
| FB-2.4 | T4/T5/T6/T7 활성화: vorticity ω_a, 4-accel A_a 가 0 이 아닌 tilted / Class-B 케이스에서 hierarchy_rhs 에 연결. `hierarchy_rhs_photon` extension + regression. Phase audit. |

**Exit criteria**: `hierarchy_rhs_photon(eta, tower, cosmo=<any 11 type>, ...)` 모든 type 에서 finite output. Unit tests: FLRW → LB-2 결과와 bit-identical; per-type sanity checks (e.g., IX 에서 spatial curvature 가 damping term 추가).

### Phase FB-3 — Tilted sector (non-perturbative β) (6 sessions)

**가장 큰 phase.** lowell §11-§13 tilted-velocity primitives 를 PSTF hierarchy 에 non-perturbative 하게 꿰매 넣는다.

| Session | 산출물 |
|---|---|
| FB-3.1 | `TiltedSpeciesBackground(base, beta, v_hat_e)` abstraction (bass/tilt/tilted_species.py) — ρ̃, p̃, q̃_a 를 non-perturbative 하게 계산. Orthogonal limit (β→0) 에서 기존 species 재현. |
| FB-3.2 | Non-perturbative boost kernel `B(η, ê)` 를 direction-dependent 하게 모든 PSTF moment 에 projection. `bass/tilt/boost_kernel.py` + Wigner-D 테이블 (axi-symmetric sector only at FB-3). |
| FB-3.3 | `einstein_bianchi` + tilt 커플링: energy-momentum conservation 이 baryon drift 를 shear source 에 피드백. Y-Block 의 `compute_shear_source` 를 `(sc, Sp, Sm, calH, a, q̃_a)` 로 확장. |
| FB-3.4 | `hierarchy_rhs` vorticity ω_a ≠ 0 branches 활성화 — tilted species drift 가 hierarchy 에 vorticity 를 유도. T4/T5 에 vorticity coupling explicit. |
| FB-3.5 | `CanonicalDecision` β-gate 재매개화: VT-07 의 `|β| ≤ safety_margin × ε_1 / (1 + η_u̇)` 가 small-β 전제. Non-perturbative 용 새 gate (β 전 range; cosh β - 1 이 주 metric). |
| FB-3.6 | Audit + tilted regression suite: β-sweep (β ∈ {0, 0.01, 0.1, 0.5}) × 11 type → 44 configurations 가 예외 없이 integrate; β→0 에서 FB-1/2 결과 재현 within rtol; 순간적 β-jump (non-physical but numerically stressful) 테스트. |

**Exit criteria**: `LowellBianchiIntegrator(IntegratorConfig(bianchi_cosmo=..., beta=0.3))` 모든 11 type 에서 green. Canonical decision 이 β > safety limit 에서 explicit raise (no silent fallback).

### Phase FB-4 — Tilted Thomson kernel (Layer B) (3 sessions)

**목표**: LB-4 Layer A (scalar visibility × B(η,ê)) 에서 Layer B (full Lorentz boost on PSTF collision kernel) 로 lift.

| Session | 산출물 |
|---|---|
| FB-4.1 | Thomson kernel full-Lorentz: Dodelson §4.5 PSTF Boltzmann + lowell §11.3 full boost. `ThomsonPSTFCollisionOperator` 에 β-dependent term 추가; orthogonal (β=0) limit 은 LB-4 그대로. |
| FB-4.2 | E-B mixing: tilted LOS 에서 E-mode 가 부분적으로 B-mode 로 회전. `PolarizationHierarchyState` 에 B-field slot; `EModeThomsonCollisionOperator` 가 E↔B 커플. |
| FB-4.3 | 2nd-order v_e² corrections (LB-4d deferred). 선형 boost 는 LB-4 Layer A 에 포함; FB-4.3 은 v_e² (Doppler 2nd) 를 명시적으로. Pontzen-Challinor cross-check. Audit. |

**Exit criteria**: β-sweep × polarization regression. BB 스펙트럼이 β=0 에서 exactly zero; β=0.1 에서 Pontzen-Challinor 의 10^{-1} × EE 스케일.

### Phase FB-5 — Perturbation sector k ≠ 0 (7 sessions — 가장 많음)

**목표**: LB-6 의 k=0 배경을 Fourier (or harmonic) mode 로 확장. CAMB regular adiabatic seed + tilted boost rule (§13.5).

| Session | 산출물 |
|---|---|
| FB-5.1 | Harmonic mode decomposition per type: I/V/VII₀ 은 plane-wave; IX 는 discrete `ℓ ≤ n` spectrum; VII_h 은 spiral Q-modes (Pontzen-Challinor). `bass/perturbation/harmonic_modes.py` 설계. |
| FB-5.2 | ∇̃ full operator (lowell §13) — k-space dispatch. FB-2 의 단순 dispatch 를 mode-기반으로 확장. |
| FB-5.3 | CAMB regular adiabatic seed IC (lowell §13.2): δ_γ, δ_b, δ_c, δ_ν, θ_γ, θ_b, θ_c, θ_ν, σ_ν 의 leading-order analytic expression at radiation era. |
| FB-5.4 | k=0 limit 이 LB-6 (background only) 재현; k > 0 trivial 모드 (large-scale Sachs-Wolfe) gate 통과. |
| FB-5.5 | Class B mode quantization: twist `a` 가 mode scaling 을 수정. Type V 의 open-FLRW mode (Harrison 의 hyperbolic harmonics) 구현. |
| FB-5.6 | Tilted-boost seed rule (§13.5) — PSTF-regularised: tilted IC 는 orthogonal IC 에 Lorentz-transform 만으로 얻어지는 게 아니라 initial-value-surface 에서 boost 한 후 재-regularise 필요. |
| FB-5.7 | 전 type × k-range regression + phase audit. IX 는 `ℓ ≤ n` cutoff 으로 모드 수 제한 확인. |

**Exit criteria**: C_ℓ^{TT} for Type I + baseline k-grid 이 CAMB Planck-2018 Dl_TT (`data/camb_ref_planck2018.npz`) 에 ell ∈ [2,30] 에서 < 5 % match; VII_h C_ℓ 이 Pontzen-Challinor shape reproduce.

### Phase FB-6 — 22-configuration regression suite (3 sessions)

**목표**: 11-type × {orthogonal, tilted} 전 configuration 회귀 + cross-type continuity + 문헌 ground truth.

| Session | 산출물 |
|---|---|
| FB-6.1 | `bass/integration/test_full_bianchi_coverage.py` 신규 — per-type orthogonal + tilted fixture 22개, 각각 background invariant + hierarchy finite + closure dispatch pass. LB-6 스타일 diagnostic playbook (§12) 확장. |
| FB-6.2 | Cross-type continuity: VII_h → VII₀ as h→0⁺; VI_h → III as h→-1; VII₀ → I as n→0; V → I as a→0; FB-1 의 source limits 가 smooth. IX → BKL isotropic 로 n→0 limit. |
| FB-6.3 | Pontzen-Challinor (2009) C_TT / off-diagonal cross-check for VII_h and IX. CAMB FLRW limit match for I/V/VII₀/VII_h→0/IX→BKL. Audit + phase gate. |

**Exit criteria**: 22 configurations all green; 3 literature ground-truth shape matches (P-C spiral, P-C IX, CAMB Planck-2018).

### Phase FB-7 — Spectrum + HTT + likelihood (5+ sessions)

**목표**: 출력단. Per-type 으로 C_ℓ (+ off-diagonal) 추출 → HTT decomposition → direction-dependent likelihood.

| Session | 산출물 |
|---|---|
| FB-7.1 | Line-of-sight matrix propagator (lowell §7): `bass/spectrum/lowell_los.py` — 11 type 에서 visibility × source 합성. |
| FB-7.2 | C_ℓ^{TT, EE, TE, BB} 추출 + off-diagonal C_{ℓm, ℓ'm'} (anisotropic types). |
| FB-7.3 | HTT decomposition (lowell §14.2) + P0 triad (prior alignment / tangency / β-gate) resolution. |
| FB-7.4 | Direction-dependent likelihood (lowell §14.3) — tiered resolution. |
| FB-7.5 | Full Planck-2018 Likelihood 매치 at FLRW limit (cross-check CAMB + HyRec + the full HTT stack). Audit + final phase gate. |
| FB-7.N | [보류] Lensing / ISW / non-Gaussian extension — post-FB scope. |

**Exit criteria**: Likelihood evaluator that returns ln B (bayes factor) between a Bianchi type and FLRW for each of the 11 types, given a synthetic Planck-2018-quality data. 모든 type 의 ln B 이 수치적으로 안정 (no NaN / Inf / silent fallback).

---

## 5. Dependency graph (phase 간 의존성)

```
FB-0 ─┬─► FB-1 ──► FB-2 ──► FB-3 ──► FB-4 ──► FB-6 ──► FB-7
      │              │       │         │         ▲
      │              │       ▼         │         │
      │              │      FB-5 ──────┴─────────┘
      │              │       ▲
      │              └───────┘
      └─────── FB-5 가 FB-2 ∇̃ 필요
```

* FB-0 은 모든 phase 의 prerequisite.
* FB-1 / FB-2 는 직렬 (background → hierarchy).
* FB-3 / FB-4 는 tilted sector pair; FB-3 가 FB-4 앞에.
* FB-5 (perturbation) 는 FB-2 ∇̃ 에 의존하지만 FB-3 / FB-4 와 병렬 진행 가능.
* FB-6 은 FB-1~5 결과 전체를 regression; FB-7 이 최종.

**Parallel opportunity**: 팀이 2인 이상이면 FB-3 (tilted) 와 FB-5 (perturbation) 는 병렬로 진행 가능 — FB-3 은 β를 확장, FB-5 은 k를 확장. 교차점은 FB-6 에서 tilted+k 조합을 동시 회귀할 때.

---

## 6. Open design decisions — **answered 2026-04-20**

| # | 결정 사항 | 옵션 | 결정 | 비고 |
|---|---|---|---|---|
| D1 | Frame convention | (a) Ellis canonical (a along 1), n₁=0 for Class B; (b) Pontzen-Challinor (a along 2), n₂=0 for Class B | **(b) — 단, (a) 와의 명시적 변환식을 `00_conventions.md` 에 제공** | `bianchi_types.py` 가 Pontzen-Challinor frame 으로 이미 운용 중이므로 (b) 를 SSOT 로 고정하되, Ellis-canonical literature fixture 를 로드할 때 필요한 inverse tensor-rotation `R: e₁ ↔ e₂` 을 `bass.background.bianchi_types` 에 `ellis_to_pc_rotation()` / `pc_to_ellis_rotation()` 공용 헬퍼로 둔다. 두 frame 의 `(n_ab, a_α)` 매핑은 `(n₁, n₂, n₃, a) → (n₂, n₁, n₃, a)` + σ_ab 의 동일 matrix-conjugation. |
| D2 | Σ-convention | (a) Ellis: Σ_ab = a σ_ab, Σ² × a⁴ = const; (b) einstein_bianchi: Σ × a = const | **(a) Ellis** | 이미 FB-0.1 에서 flip 되어 shipped. |
| D3 | "9 vs 11 types" | (a) 11 (전부); (b) 9 (VI₀·VII₀ 흡수) | **(a) 11** | 코드에 이미 있음; 유지. |
| D4 | Tilted β parametrization | (a) rapidity β (non-perturbative); (b) boost 속도 v_e (cap `\|v_e\|<1`) | **(a) rapidity** | 현재 `TiltedSpeciesBackground.beta` 는 velocity (FB-3.1 ship). FB-3.5 β-gate reparametrisation 에서 rapidity 를 internal SSOT 로 전환하고 velocity 는 derived property 로 유지. |
| D5 | Bianchi IX recollapse 처리 | (a) event-terminated solve_ivp; (b) pre-compute η_max_IX | **(a)** | FB-1.2 에서 shipped. |
| D6 | k 분해 backend | (a) plane-wave + Harrison hyperbolic + Q-mode dispatch; (b) CAMB-style | **(a)** | FB-5 에서 per-type dispatch SSOT. |
| D7 | Massive ν (FB-범위에 포함?) | (a) 포함; (b) 별도 phase | **(a) 포함** | Extended coverage bundle 의 FB-9 로 분리되지만 FB-범위 안으로 포함 (post-FB 항목 아님). 상세: [extended_coverage/FB9_MASSIVE_NEUTRINO_SDD.md](extended_coverage/FB9_MASSIVE_NEUTRINO_SDD.md). |
| D8 | External comparison oracle 추가 (CLASS? Healpy?) | (a) CAMB only; (b) CAMB + CLASS | **(a) CAMB only** | External-code guard 유지. |
| D9 | HTT P0 triad 의 resolution 순서 | (a) FB-7.3; (b) FB-0 에서 미리 | **(a) FB-7.3** | |
| D10 | LB-6 `tca_active_mask` 의 tilted 확장 | (a) 확장; (b) deprecate | **(a) 확장** | LB-5 API 호환 유지. |

---

## 7. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Bianchi IX recollapse 가 LSODA 를 stalling | High | Medium | FB-1.2 에서 event termination + η_max safety margin |
| ∇̃ Class B 연산이 LB-2 PSTF cache 을 초과 (ℓ > L_MAX_CACHED=8) | Medium | High | FB-2.1 에서 cache 확장 SSOT; post-FB benchmark |
| Non-perturbative β 가 LB-3 closure 의 암시적 small-β 전제를 위반 | High | High | FB-3.5 에서 β-gate 재매개화 + 가드 강화 |
| Perturbation sector 에서 IX mode counting 이 CAMB-style k-grid 에 안 맞음 | Medium | Medium | FB-5.1 에서 per-type mode dispatch SSOT; `k` 를 dimensionless eigenvalue 로 추상화 |
| Pontzen-Challinor literature fixture 가 코드 frame convention 과 misalign | Medium | Low | FB-0.2 에서 frame convention lock; literature fixture 로드시 explicit transform |
| HyRec fixture Δz = 1 grid 가 tilted recomb 에서 resolution 부족 | Low | Medium | Post-FB 에서 sub-grid HyRec refresh; FB-범위에서는 LB-6-08 ± 1 tolerance 유지 |
| 회귀 suite 가 22 config × 수십 테스트 = 수천 테스트 → wall-time blowup | Medium | Medium | `@pytest.mark.slow` aggressive; FB-6 에서 nightly split |
| External-code policy 위반 (someone imports `camb` in FB-7) | Low | High | `test_external_code_policy` 유지; FB-7 CAMB 는 오직 fixture NPZ 로부터 |

---

## 8. Milestones (관리자용 게이트)

| Milestone | 완료 phase | 의미 |
|---|---|---|
| **M1**: "11-type background verified" | FB-1 | Wainwright-Ellis table 전부 재현; provisional → validated |
| **M2**: "11-type hierarchy integrable" | FB-2 | 전 type 에서 `LowellBianchiIntegrator.run()` 예외 없이 통과 |
| **M3**: "tilted sector greenlit" | FB-4 | β>0 에서 integrate; Pontzen-Challinor qualitative shape 매치 |
| **M4**: "perturbation sector greenlit" | FB-5 | C_ℓ TT 추출 가능; CAMB Planck-2018 < 5 % 매치 at FLRW limit |
| **M5**: "full coverage" | FB-6 | 22 configurations regression green |
| **M6**: "inference ready" | FB-7 | Likelihood evaluator returns stable ln B for 11 types |

게이트 M1~M6 이 통과하면 이후는 post-FB 유지보수 + HTT 정밀화 + lensing 확장 phase.

---

## 9. Session budget 요약

| Phase | Sessions | Cumulative |
|---|---|---|
| FB-0 | 3 | 3 |
| FB-1 | 4 | 7 |
| FB-2 | 4 | 11 |
| FB-3 | 6 | 17 |
| FB-4 | 3 | 20 |
| FB-5 | 7 | 27 |
| FB-6 | 3 | 30 |
| FB-7 | 5 | 35 |

**약 35 sessions, ~7 주 (일일 1 세션 기준).** 병렬화 (FB-3 ∥ FB-5) 가능하면 ~5 주.

---

## 10. Post-FB 범위 (본 플랜 제외)

### In extended bundle (FB-8 / FB-9 / FB-11 — scope sealed 2026-04-20)

- **Observer-frame layer + local-boost vs global-tilt discriminator** — **→ [extended_coverage/FB8_DISCRIMINATOR_SDD.md](extended_coverage/FB8_DISCRIMINATOR_SDD.md)** (coordinator: [EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md §5 FB-8](extended_coverage/EXTENDED_COVERAGE_PLAN_FB8_FB9_FB11.md)).
- **Massive neutrino (m_ν > 0)** — **→ [extended_coverage/FB9_MASSIVE_NEUTRINO_SDD.md](extended_coverage/FB9_MASSIVE_NEUTRINO_SDD.md)** (coordinator §5 FB-9).
- **Inference driver + multi-type Bayes factor** — **→ [extended_coverage/FB11_INFERENCE_DRIVER_SDD.md](extended_coverage/FB11_INFERENCE_DRIVER_SDD.md)** (coordinator §5 FB-11).

### Discarded 2026-04-20 — not re-entered without fresh SDD + dated entry

아래 세 항목은 [extended_coverage/SCOPE_DECISIONS.md](extended_coverage/SCOPE_DECISIONS.md) §§2–4
에서 완전 out-of-scope 폐기로 기록됨. 재진입 시 §5 의 재진입 절차 필수.

- **Survey systematics 통합 (mask / beam / noise)** — 폐기; `htt/` + `mio/` 의 observation-side 인프라가 이 surface 를 계속 담당.
- **Lensing / ISW 비선형 보정** — 폐기; 저-ℓ target 에서 선행 순위 낮음 + CAMB fixture 로 충당 가능.
- **2nd-order tilt (v_e² × anisotropy cross-terms)** — 폐기; Planck-2018 precision 범위에서 불필요.

### 여전히 post-extended

- Non-Gaussian primordial initial conditions.
- Bianchi IX Mixmaster BKL oscillation regime (near-singularity).
- GPU 가속 / ark4 IMEX stepper 채택.

**Extended bundle 진입점**: [extended_coverage/INDEX.md](extended_coverage/INDEX.md) — FB-8 / FB-9 / FB-11
의 3-phase SDD + FB-3 이후 역사 로그 + self-audit automation + memory 명시화를 bundle 로 통합.

---

## 11. 승인 체크리스트 — **sealed 2026-04-20**

- [x] §0 "9 vs 11" 결정 → 11 사용 (D3 = a).
- [x] §6 D1~D10 design decisions → 2026-04-20 승인; 각 항목의 결정은 위 §6 표 참조 (D1 은 변형 승인 — "(b) 지원하되 (a) 변환식 제공").
- [x] post-LB A/B/C 옵션 (README.md §7) 을 FB 가 대체.
- [x] 첫 세션 (FB-0.1 — Ellis convention flip) 이 NEXT_SESSION_PROMPT §2 로 rotate 되어 shipped.
- [x] Extended coverage bundle (FB-8 / FB-9 / FB-11) scope 확정; FB-10 / FB-12 / FB-13 slot 은 [extended_coverage/SCOPE_DECISIONS.md](extended_coverage/SCOPE_DECISIONS.md) 에서 완전 out-of-scope 폐기 결정으로 기록됨.

승인이 완료되었으므로 본 §11 은 역사 기록으로 유지한다. 본 플랜의 forward motion 은 FB-0.1 부터 시작하여 FB-3.2 까지 shipped, 현재 FB-3.3 rotation 중이며, FB-7 완료 후 [extended_coverage/](extended_coverage/) bundle 로 flow 된다.

---

## References (문헌 SSOT)

| 주제 | 참조 |
|---|---|
| Bianchi 분류 원본 | Ellis & MacCallum 1969, *CMP* 12, 108 |
| Dynamical systems in 11 types | Wainwright & Ellis 1997, *Dynamical Systems in Cosmology*, CUP |
| CMB in Bianchi VII_h, IX | Pontzen & Challinor 2007/2009, *MNRAS* / *PRD* |
| Type IV, VI_h marginal limits | Krasiński et al. 2003, *GRG* 35, 475 |
| Tilted fluids | King & Ellis 1973, *CMP* 31, 209 |
| lowell BASS solver reference | `lowell_bianchi_solver_reference.md` §6~§14 |
| PSTF decomposition | Ellis 1971; Ellis-Bruni-Ellis 1992 |
| W6-04 TCA closure algebra | `bass/closure/quadrupole_tca.py` (LB-3) |
| LB-0…LB-6 audit logs | `docs/audits/AUDIT_PHASE_LB*_*.md` |
