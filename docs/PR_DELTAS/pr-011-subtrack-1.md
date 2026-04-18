# PR-011 Sub-track 1 — ν Hessian Closed-Form SSOT Promotion

> **Status**: ✅ **MERGED** (2026-04-17)
> **Track**: A (FLRW denominator hardening)
> **Parent**: PR-011 (massive-ν + lensing + high-ℓ)
> **Dependency**: PR-010 (complete) ✅

---

## Scope

R-P2-02 의 확정 결과 — **two-field (ξ, η) Fermi-Dirac Hessian closed-form** 을 `core::ssot::constants` 로 승격. PR-011 의 massive-ν completion 사전 작업.

**핵심 결과**: α, β, γ, δ 계수가 η₀=0, ξ₀=1 에서 모두 폐쇄형 (π, ζ(3), ζ(5) 의 유리 조합). β, γ 는 η₀=0 에서도 **비영** — symmetric background 에서도 chemical-potential perturbation 이 quadrupole 에 기여.

---

## What this PR delivered

### `src/core/ssot.rs::constants` 확장 (4 새 상수)

```rust
/// α = (10/3)·F₃(0) = 7π⁴/36 ≈ 18.9413
pub(crate) const NU_HESSIAN_ALPHA_ZERO: f64 = 7.0 * π⁴ / 36.0;

/// β = 2·(−F₂(0)) = −6·ζ(3) ≈ −7.2123
/// (symmetrization factor 2 from ∂²/∂ξ∂η entering twice in f 의 2차 전개)
pub(crate) const NU_HESSIAN_BETA_ZERO: f64 = -6.0 * ζ(3);

/// γ = F₁(0) = π²/12 ≈ 0.8225
pub(crate) const NU_HESSIAN_GAMMA_ZERO: f64 = π²/12;

/// δ = −(5/24)·F₄(0) = −(75/16)·ζ(5) ≈ −4.8606
/// (shear-temperature coupling, from Liouville operator, NOT Hessian of f)
pub(crate) const NU_HESSIAN_DELTA_ZERO: f64 = -(75/16) * ζ(5);
```

### Ratios (derived, not stored — SSOT discipline)

```text
|β|/α = 216·ζ(3) / (7π⁴)  ≈ 0.3808    (non-negligible cross-coupling)
γ/α   = 3 / (7π²)         ≈ 0.0434    (chemical potential sensitivity)
```

`NU_HESSIAN_BETA_OVER_ALPHA_ZERO` 같은 derived 상수는 **SSOT 위반** 이라 의도적으로 저장 안 함 (primary 상수에서 계산 가능 = single source of truth). Test 에서는 closed-form 공식과 대조.

### 6 new unit tests

- `nu_hessian_alpha_matches_7pi4_over_36` — α = 7π⁴/36 정밀 대조
- `nu_hessian_beta_matches_minus_6_zeta3` — β ≈ -7.2123
- `nu_hessian_gamma_matches_pi2_over_12` — γ = π²/12 정밀 대조
- `nu_hessian_delta_matches_minus_75_16_zeta5` — δ ≈ -4.8606
- `nu_hessian_signs` — α>0, β<0, γ>0, δ<0
- `nu_hessian_ratios_nonzero` — `|β|/α ≈ 0.3808 > 0.1`, `γ/α ≈ 0.0434 > 0.01` (핵심 물리 주장)

Test 결과: **6/6 PASS**. SSOT 전체 (35/35 PASS).

---

## What this PR explicitly does NOT claim

- **Production 경로에서 사용 안 됨** — 현재 BASS 의 massive-ν code path (Papers II/III 2F, optional A3) 는 이 계수들을 직접 호출하지 않음. 이 PR 은 **향후** two-field Fermi-Dirac 2차 source 구현을 위한 SSOT 기반 마련.
- **η₀≠0 에서의 계수 함수 제공 안 됨** — 일반 η₀ 에서는 Fermi-Dirac integral F_n(η) 평가가 필요 (polylogarithm). R-P2-02 은 "η₀=0 에서 0.07 까지 변화가 5-7% 에 불과" 라고 보고 — BBN 허용 범위에서는 η₀=0 값이 충분. η₀≠0 evaluator 는 별도 sub-track 에서.
- **δ 계수의 완전한 정당화 아님** — δ 는 Hessian 이 아닌 Liouville operator 에서 유래하며 gauge/normalization 관례에 의존. R-P2-02 은 `δ ∝ ∂I₄/∂ξ = -(5/24)F₄` 의 proportionality 는 확정하되 "exact numerical prefactor depends on gauge choice" 라 caveat 달음. 여기 저장된 값은 **R-P2-02 의 primary convention** 기준.
- **Conditioning 위험 해결 아님** — R-P2-02 는 `η₀ ≳ π` 에서 Gram matrix 의 condition number 가 `3η₀⁴/π²` 로 발산한다고 경고. BBN range (|η_ν| ≲ 0.07) 에서는 문제없지만, 고 degeneracy scenario 는 별도 regularization 필요.

---

## D_2 regression

`dump_dl_spectrum_sparse` (498/498 k-modes, 81.51 s):

| 측정 | D_2 | 핵심 ℓ |
|---|---|---|
| Pre (PR-010 Stage B + R-NORM-01) | 1002.086744 | 2954.415482 / 7362.079040 |
| **Post (ν Hessian SSOT 추가)** | **1002.086744** | 동일 |
| Δ | **0 (bit-identical)** | — |

SSOT amendment 로 production 경로 무접촉 확인.

---

## Promotion criteria (all satisfied)

- [x] Tests pass — 6 new tests + 35 total ssot PASS
- [x] D_2 bit-identical = 1002.086744 μK² 유지
- [x] Derived quantities (ratios) SSOT 저장 안 함
- [x] Physical sanity (signs, magnitude ranges) 검증
- [x] `cargo build --lib --release` : 0 errors, 40.85s

---

## Rollback triggers

- 저장된 α, β, γ, δ 값이 R-P2-02 문서와 불일치 → 재검
- β, γ 가 η₀=0 에서 비영 이라는 key finding 이 반증됨 → 재검
- D_2 bit-identical 위배 → 즉시 revert (SSOT amendment 라 위배 불가하나 방어적 확인)

---

## Next: PR-011 Sub-track 2 candidates

Sub-track 1 완료. 다음 옵션:

1. **Sub-track 2a** (small): η₀≠0 Taylor 전개 SSOT 함수 추가 — `nu_hessian_alpha_at(eta0)` 등, BBN bound 내 평가 지원
2. **Sub-track 2b** (medium): BASS two-field ν RHS 에 이 계수 실제 활용 (massive-ν completion — userMemory "16% RMS at ℓ≥100" 해소)
3. **Sub-track 2c** (large): Lensing infrastructure (κ, φ lensing powers, RECFAST/CAMB lensing table compatibility)
4. **Sub-track 2d** (large): High-ℓ σ̇ precision — on-the-fly RHS 또는 `dverk` (Verner 5/6 RK) port

**권장 순서**: 2a → 2b → 2c → 2d (점진적 복잡도 증가)

---

*Merged 2026-04-17. SSOT amendment, no production impact.*
