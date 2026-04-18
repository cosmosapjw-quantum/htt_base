# PR-010 Stage B — Production Migration (Closure)

> **Status**: ✅ **STAGE B MERGED** (2026-04-17)
> **Track**: A (FLRW denominator hardening)
> **Builds on**: PR-010 Stage A (scaffold) ✅
> **Next**: PR-011 (neutrinos + lensing + high-ℓ)

---

## What Stage B delivered

### 1. `production_source_v1` migration to `source::registry`

`src/solver/sync_gauge_camb.rs::production_source_v1` 이 이제 inline 계산 대신
`source::registry` 의 pure function 경유:

```rust
let inp = crate::source::registry::SourceInputs { /* ... */ };
let s_sw   = crate::source::registry::source_sw(&inp);
let s_dop  = crate::source::registry::source_doppler(&inp);
let s_quad = crate::source::registry::source_polter_quad(&inp, polterdot);
let s_e    = crate::source::registry::source_emode(&inp,
    crate::source::registry::EmodeConvention::Polter);
```

### 2. SSOT helper 확장

- `core::ssot::polter` — **bit-identical contract** 명시 (production 의
  `2.0 * θ₂ / 5.0 + 3.0 * E₂ / 5.0` / `4.0 * θ₂ / 10.0` 와 동일한 계산 순서 사용)
- `core::ssot::polter_dot` — **신규 추가** (polterdot 계산의 SSOT 승격,
  production 의 `2.0 * (pigdot/4.0) / 5.0 + 3.0 * e2dot / 5.0` 등과 bit-identical)

### 3. Latent SSOT bug 해결 (byproduct)

**Discovered**: 이전 `ssot::polter` pol-OFF 분기는 `theta2 * 0.1` (= 0.1·Θ₂)
이었으나, 올바른 값은 `pig/10 = 4·Θ₂/10 = 0.4·Θ₂` (Production 은 항상 이것을
inline 으로 사용). SSOT 가 **4× 작은 값** 을 반환하는 잠복 버그.

**Impact before**: Production 은 inline 이라 영향 없음.
Downstream (`los::source::evaluate_source` deprecated 포함 모든 SSOT 사용자) 는
모두 잘못된 값 수신. 하지만 현재 코드에서 `ssot::polter()` 를 호출하는 코드는
없었으므로 (production_source_v1 이 inline 이었고, deprecated 된 다른 모듈들은
panic 하거나 #[deprecated] 경고만), 실제 물리 결과에는 영향 없었음.

**Fix**: SSOT 의 pol-OFF 분기를 production 과 bit-identical 한
`4.0 * theta2 / 10.0` 로 교체. Pol-ON 분기도 `POLTER_W_THETA2 * θ₂`
(= `(2/5) · θ₂`) 에서 `2.0 * θ₂ / 5.0` 로 교체 (수학적으로 동일,
f64 계산 순서는 bit 수준에서 다를 수 있음).

### 4. Tests

**Registry (12, all PASS)**: PR-010 Stage A 의 12 tests 모두 변경된 SSOT 공식에 맞춰 업데이트 후 통과.
- `caveat_no_pol_reduction_emode` — `expected = g · (4·θ₂/10)` 로 수정
- `limit_pol_off_reduces_polter_quad` — E₂=0 에서 pol-ON/OFF bit-identical 확인

**SSOT (25, all PASS)**: 2 개 test 업데이트:
- `polter_pol_off` — `expected = 0.4` (기존 0.1 은 버그 기반 예상치)
- `neff_splits` — `2.0328 + 1.0132 = 3.0460 vs 3.044` CAMB 관례 인정, 0.1% tolerance

---

## D_2 regression (핵심 검증)

`dump_dl_spectrum_sparse` (498/498 k-modes, 68.73 s):

| ℓ | Pre-Stage-B D_ℓ [μK²] | Post-Stage-B D_ℓ [μK²] | Δ |
|---|---|---|---|
| 2 | 1002.086744 | **1002.086744** | **0 (bit-identical)** |
| 3 | 982.718007 | 982.718007 | 0 |
| 4 | 955.957268 | 955.957268 | 0 |
| 100 | 2954.415482 | 2954.415482 | 0 |
| 200 | 7046.157388 | 7046.157388 | 0 |
| 220 (peak) | 7362.079040 | 7362.079040 | 0 |
| 300 | 4562.790217 | 4562.790217 | 0 |

**SSOT bit-identical contract 성공**. Stage B 는 semantics 보존한 pure migration.

---

## What this PR owns (Stage B additions)

- `production_source_v1` 이 registry 경유 의무 — inline 재계산 금지
- `ssot::polter` 와 `ssot::polter_dot` 의 **bit-identical contract** (주석 명시)
- Pol-OFF `polter = pig/10 = 4·θ₂/10` 이 canonical (이전 `θ₂/10` 은 버그)

---

## What this PR explicitly does NOT claim

- **ISW 활성화 아님** — 여전히 `s_isw = 0.0` (production 은 post-processing FD 사용)
- **PiBass production 채택 아님** — `EmodeConvention::Polter` 만 사용
- **CAMB accuracy 개선 아님** — D_2 bit-identical 은 semantics-preserving 증명일 뿐
- **Performance change 아님** — 컴파일러 inline 으로 function call 오버헤드 0

---

## Promotion criteria (all satisfied)

- [x] Tests pass — registry 12/12, ssot 25/25
- [x] D_2 = 1002.086744 bit-identical (anti-regression guard ✓)
- [x] Semantic burden explicit — 이 문서
- [x] Rollback trivial — `git revert` 한 번
- [x] `cargo build --lib --release` : 0 errors

---

## Rollback triggers

- D_2 1002.086744 에서 drift → revert
- 다른 test 회귀 발생 → revert
- `registry::assemble` 과 `production_source_v1` 출력 불일치 → revert

---

## Next PR → PR-011

PR-010 **전체 완료** (Stage A + B). 다음은 PR-011:

**Title**: FLRW denominator hardening: neutrinos, lensing, high-ℓ integration
**Scope candidates**:
1. Massive ν completion (userMemory "16% RMS at ℓ≥100" 해소)
2. Lensing infrastructure (κ, φ 렌즈화 powers)
3. High-ℓ σ̇ precision (on-the-fly RHS or higher-order solver)
4. `CL_PREFACTOR_SYNC` step function 완결 (R-NORM-01)

**Dependency**: PR-010 Stage A+B ✅
**Complexity**: PR-010 보다 ~2× (여러 sub-track)

---

*Merged 2026-04-17. D_2 verified bit-identical. Latent SSOT polter bug resolved as byproduct.*
