# BASS SSOT Policy

> **Single Source of Truth 정책** — v2.0 (2026-04-17)
>
> **v1.0 → v2.0 확장 출처**:
> - `BASS_Implementation_SSOT_Hardening_v1_0.md`
> - `BASS_Physics_Cosmological_Evolution_Compendium_v1_0.md`
> - `BASS_PR_WBS_TDD_SDD_v1_0.md`
> - `DOC-BASS_Design_v1_3_with_recomb_reion_EFT_backreaction.md`

이 문서는 BASS 코드·문서 전체에서 **동일 물리량이 서로 다른 규약으로 재구현되지 않도록** 강제하는 정책이다. 4건의 감사(2026-04-17) 에서 공통으로 지적된 "authoritative physics dictionary 가 저장소 전체에서 하나로 잠기지 않았다" 를 구조적으로 해소.

**Companion 문서**:
- `docs/KNOWN_LIMITS.md` — 6 카테고리 복원 테이블 (§10 상세)
- `docs/STATUS_TAGS_AND_EXPORTS.md` — 태그 사전 + export schema (§11-§12 상세)
- `docs/PR_CONSTITUTION.md` — TDD/SDD/Promotion/Critical-Path 규약 (§14 상세)

---

## §1. 최상위 원칙

### 1.1 Source-of-truth 우선순위

> **어떤 물리량의 정의·규약·정규화·부호가 두 곳 이상에 존재하면, 그것은 버그다.**

BASS 내부 정보 흐름의 권위 순서는:

1. **exact / full transport branch**
2. **basis-normalized hierarchy variables**
3. **canonical source primitives**
4. **LoS / observable assembly**
5. **export bridge**

즉, raw code variable 이 곧 source of truth 가 아니다. 항상 한 번 **canonical internal representation** 으로 들어온 뒤 source/observable/export 로 나간다.

### 1.2 No direct raw-to-source rule

**금지**:
```
raw hierarchy variables  →  source assembly  (직접)
```

**허용**:
```
raw hierarchy variables
  → basis-normalized internal multipoles
  → canonical primitives (polter / Π_BASS / ...)
  → source assembly
```

### 1.3 Solver / Report separation

> solver-side effective variable ≠ report-side quantity

Bridge object 없이는 export semantics 를 주장할 수 없다.

### 1.4 Stack ownership boundary

```
BASS owns physics   ≠   HTT owns observation bridge   ≠   MIO owns reporting semantics
```

이 분리는 editorial 이 아니라 **design boundary** 다. ownership 이 무너지면 stack 전체가 semantically unstable 해진다.

---

## §2. Canonical Basis Choice

### 2.1 FLRW denominator basis

BASS 내부 정규 multipole basis:

| 양 | 기호 | 비고 |
|---|---|---|
| temperature/intensity hierarchy | `Θ_ℓ` | Hu-White/TAM 표준화 |
| scalar E-polarization | `E_ℓ` | |
| scalar B-polarization | `B_ℓ` | (scalar FLRW: 0) |
| massless neutrino | `N_ℓ` | |
| baryon velocity | `v_b` | collision: `−κ̇(v_b − 3Θ₁)/r_b` |
| metric (Newtonian branch) | `Ψ, Φ` | `Ψ = −Φ` 시 `π_iso = 0` 조건 |
| metric (sync branch) | `h_sync, η_sync` | |

### 2.2 Exact-transport basis

Exact anisotropic branch 는 `Θ_ℓ, E_ℓ, B_ℓ` 를 primitive ontology 로 **선택하지 않는다**. 대신 covariant 운반된 state:

```
𝔛 = ( I, 𝒫, ν, direction_data, species_labels )

D𝔛/dλ  =  𝔖_fs  +  𝔊  +  𝔠
```

여기서 `𝔖_fs` = 자유류, `𝔊` = 기하결합, `𝔠` = 충돌/지역 source.

**Rule**: exact-branch implementation 은 이 3-way split 을 semantic 으로 우회 불가. 수치적으로 결합되어 계산되더라도 개념적 분리는 유지.

### 2.3 Canonical Thomson primitive — `Π_BASS`

```
Π_BASS ≡ Θ₂ + E₀ + E₂
```

이 primitive 는 **FLRW scalar TT/TE/EE source assembly 의 유일한 canonical polarization source** 다 (Hu-White 관례).

**코드 권위 위치**: `core::ssot::pi_bass(θ₂, E₀, E₂, has_pol)` + `pi_bass_from_hw_like` / `pi_bass_from_class_like`.

### 2.4 `polter` vs `Π_BASS` — 구분 필수

BASS 에는 **두 가지 polarization combination** 이 공존하며, 둘은 같은 물리량이 **아니다**:

| 양 | 공식 (pol ON) | 사용처 |
|---|---|---|
| `polter` | `2·Θ₂/5 + 3·E₂/5` | CAMB-style temperature quadrupole collision, `s_quad` integrand |
| `Π_BASS` | `Θ₂ + E₀ + E₂` | Hu-White visibility sources `S_T^vis`, `S_E^vis`, exact branch |

pol OFF 환원:
- `polter → Θ₂ / 10`
- `Π_BASS → Θ₂`

**Rule**: 모든 모듈은 어느 쪽을 쓰는지 call-site 에서 명시. `core::ssot::polter()` 와 `core::ssot::pi_bass()` 는 **별개 함수**. 혼용 금지.

### 2.5 External basis translation

외부 코드 스타일에서 BASS canonical 로의 변환 맵은 `core::ssot::pi_bass_from_*` 에 고정:

| 외부 style | BASS 변환 |
|---|---|
| HW/TAM-like `(Θ₂, E₀, E₂)` | `Π_BASS = Θ₂ + E₀ + E₂` (identity) |
| CLASS-like `(F_ℓ, G_ℓ)` | `Π_BASS = F₂ + G₀ + G₂` |
| CAMB-like (TAM-compat) | `Π_BASS = Θ₂ + E₀ + E₂` (identity) |
| CAMB-like (rescaled pol) | `raw → (E₀, E₂) canonical → Π_BASS` 2단계 |

---

## §3. Time Convention Dictionary

### 3.1 Canonical derivatives

| 기호 | 정의 |
|---|---|
| `X'` | `dX/dη` (conformal time) |
| `Ẋ` | `dX/dt` (cosmic time) |
| `D_u X` | `u^a ∇_a X` (observer proper-time) |
| `DX/dλ` | affine parameter (exact transport) |

**Universal identity** (`ds² = −a²dη² + a²dχ²`, `dτ_proper = a·dη`):
```
D_u X = (1/a) · X'        (항상 성립)
```

**Branch-specific** (명시적으로 채택한 모듈에서만):
```
Ẋ = D_u X
```

**Rule**: 한 모듈이 세 derivative 를 모두 **silently 교환 가능** 으로 취급 금지.

### 3.2 Module-by-module time convention (frozen)

| Module family | Primary convention |
|---|---|
| FLRW denominator / CMB hierarchy | `'` (conformal) |
| LoS / visibility / source construction | `'` (conformal) |
| Recombination / history | `D_u` (proper observer) |
| Reionization / 21-cm | `˙` (cosmic) |
| Exact transport | `D/dλ` (affine) |
| Backreaction wrapper / background | `˙` or scale factor `a` |
| Export / metadata | convention-free (태그 필수) |

코드 권위 위치: `core::ssot::TimeConvention` enum.

### 3.3 Rate conversion rule

Proper-time atomic rates `α_i^eff, β_i^eff, R_{i→j}^eff, Γ_{i→1s}^eff, Γ_C^(t)` 는 conformal-time integrator 에 들어가기 전에:
```
Γ^(η) = a · Γ^(t)
```

코드 권위 위치: `core::ssot::convert_rate_proper_to_conformal(Γ, a)`.

### 3.4 Opacity sign convention

Canonical opacity `χ` 는 **항상 non-negative**:
```
χ ≡ a · n_e · σ_T ≥ 0
τ' = −χ
g = χ · e^{−τ} ≥ 0
```

코드 권위 위치: `core::ssot::opacity_chi(a, n_e, σ_T)`, `visibility_g(χ, τ)`.

**금지**: `τ'` 를 직접 저장/전달하는 새 코드 금지. `χ` 또는 `κ̇` (with `κ̇ = χ`) 로 통일.

### 3.5 Legacy `dopac` 규약

`CambBackground::dopac` 필드는 **FENCED to 0.0** (Phase B-1 post-audit bug E3). 재활성화 전제는 본 문서 §15.2.

---

## §4. Operator Split SSOT

### 4.1 Exact-branch split (canonical)

```
D𝔛/dλ = 𝔖_fs[𝔛] + 𝔊[𝔛; A_a, ϑ, σ_ab, ω_ab] + 𝔠[𝔛]
```

| 연산자 | 의미 | 소유권 |
|---|---|---|
| `𝔖_fs` | free streaming / advection / redshift transport | transport 모듈 |
| `𝔊` | geometry coupling (4-가속도 `A_a`, 확장 `ϑ`, shear `σ_ab`, vorticity `ω_ab`, tetrad/frame transport) | geometry 모듈 |
| `𝔠` | collisions and source-like local interactions | collision 모듈 |

**Rule**: exact-branch 구현은 이 3-way split 을 semantic 으로 우회 불가.

### 4.2 Free-streaming hierarchy pattern

Minimal skeleton:
```
𝔖_fs,ℓ  ~  k·(α_ℓ X_{ℓ-1}  −  β_ℓ X_{ℓ+1})
```

FLRW scalar recovery:
```
Θ_ℓ'  =  (k / (2ℓ+1)) · [ ℓ·Θ_{ℓ-1}  −  (ℓ+1)·Θ_{ℓ+1} ]  +  ...
```

### 4.3 Collision sub-split

```
𝔠  =  𝔠_Th  +  𝔠_line  +  𝔠_chem  +  𝔠_eff  +  𝔠_ext
```

| 연산자 | 소유권 |
|---|---|
| `𝔠_Th` | Thomson scattering / visibility source |
| `𝔠_line` | Recombination / history line-transfer |
| `𝔠_chem` | Reionization chemistry / heating |
| `𝔠_eff` | Effective / coarse backreaction |
| `𝔠_ext` | Externally injected branch-specific source |

**Rule**: 이 sector 가 활성화되면 implementation 은 monolithic opaque "collision/source" block 유지 금지.

---

## §5. Canonical Source Contracts

### 5.1 Thomson source contract

**Visibility source** (Hu-White convention):
```
S_T^vis = g · (Θ₀ + Ψ + Π_BASS / 4)
S_E^vis = (3/4) · g · Π_BASS
```

코드 권위 위치: `core::ssot::hw_visibility_source_temperature`, `hw_visibility_source_emode`.

**Collision target**:
```
Π_BASS^coll ≡ Λ_T[Π_BASS]
```
여기서 `Λ_T` 는 basis-fixed linear map.

**Rule**: 모든 scalar TT/TE/EE source assembly 는 `Π_BASS` 경유 필수.

### 5.2 LoS radial-channel contract

```
Δ_ℓ(k) = ∫ dχ_los [ S_0(k, χ_los) · j_ℓ(kχ_los)  +  S_1(k, χ_los) · j_ℓ'(kχ_los) / k ]
```

with `S_0 = S_SW + S_ISW + ...`, `S_1 = g · v_b`.

**Rule**: Doppler 를 `j_ℓ`-only source path 안에 silently 숨기지 말 것.

### 5.3 Recombination line-source contract

Central line-transfer bottleneck 은 operator `ℰ_L` 가 담당. Effective rate 의존성:
```
Γ_{i→1s}^eff = Γ_{i→1s}^eff[ℰ_L]
```

Frozen model hierarchy:
- isotropic Sobolev baseline
- **directional-Sobolev reduced branch** (`DirSob` tag)
- **FullChar reference branch** (`FullChar` tag)

with `ℰ_L^DirSob ⊂ ℰ_L^FullChar`.

### 5.4 Reionization sweep/source contract

**Frozen sweep order** (mandatory):
1. geometry query
2. source build
3. UV sweep
4. X-ray sweep
5. Ly_α sweep
6. local rates
7. chemistry update
8. spin-temperature update
9. `δT_b`
10. diagnostics / export

**Rule**: Transport-first ordering 강제. Scalar barrier 나 source field 는 명시적 tagged reduced branch 로만 허용.

### 5.5 Effective / coarse source contract

Backreaction 은 solver-side effective tensor sector 로 들어간다:
```
τ_ab = ρ^τ · u_a u_b + p^τ · P_ab + 2·q^τ_{(a} u_{b)} + π^τ_ab
```

**Rule**: 이것은 solver-side 객체. Report-side summary 로 취급하려면 반드시 explicit bridge 경유 (`status_metadata::ForwardBridge<BackreactionExport>`).

---

## §6. Authoritative Locations (구현 레지스트리)

| 물리 카테고리 | 권위 코드 위치 | 형식 |
|---|---|---|
| N_eff 상수 | `core::ssot::constants::{NEFF_TOTAL, NEFF_MASSLESS_WHEN_SPLIT, NEFF_PER_MASSIVE_EIGENSTATE}` | `use` |
| N_eff baseline 선택 | `core::ssot::neff_massless_baseline(nq_massive)` | 함수 |
| `polter` (CAMB 관례) | `core::ssot::polter(θ₂, E₂, has_pol)` | 함수 |
| `Π_BASS` (HW 관례) | `core::ssot::pi_bass(θ₂, E₀, E₂, has_pol)` | 함수 |
| LoS Doppler | `core::ssot::doppler_source(...)` | 함수 |
| LoS quadrupole | `core::ssot::quad_source_no_polterddot(...)` | 함수 |
| HW visibility source (T) | `core::ssot::hw_visibility_source_temperature(...)` | 함수 |
| HW visibility source (E) | `core::ssot::hw_visibility_source_emode(...)` | 함수 |
| Friedmann 보정 | `core::ssot::apply_friedmann_grho_correction(H², Δgrho)` | 함수 |
| Canonical opacity `χ` | `core::ssot::opacity_chi(a, n_e, σ_T)` | 함수 |
| Visibility `g` | `core::ssot::visibility_g(χ, τ)` | 함수 |
| Rate 변환 | `core::ssot::convert_rate_proper_to_conformal(Γ, a)` | 함수 |
| Time convention enum | `core::ssot::TimeConvention` | `enum` |
| Admissibility validators | `core::ssot::{assert_opacity_positive, assert_ionization_bounded, assert_temperature_positive, ...}` | 함수 |
| External basis translation | `core::ssot::pi_bass_from_{hw,class}_like(...)` | 함수 |
| Layout invariants | `core::ssot::{validate_layout, assert_layout_valid}` | 함수 |
| Config invariants | `ProductionConfig::validate()` | 메서드 |
| Frozen tag dictionary | `core::ssot::tags::*` + `validate_tag(t)` | 상수 + 검증자 |
| Export metadata | `core::status_metadata::StatusMetadata` | `struct` + builder |
| Forward bridge | `core::status_metadata::ForwardBridge<T>` | `struct<T>` |
| Export schemas | `core::status_metadata::{RecombinationExport, EorSnapshotExport, EorLightconeExport, BackreactionExport, UnresolvedAngularExport}` | `struct` |
| D₂ convention | `forward::d2_convention` | 기존 SSOT (유지) |
| PSTF dict (doc-only) | `core::convention` | 주석 참조 |

---

## §7. 금지 규칙 (Hard rules)

신규 코드 / PR 에서 절대 금지:

1. **N_eff, polter, Friedmann normalization, Π_BASS 를 inline 재유도**.
2. **CambLayout 을 validator 없이 구성**. 새 래핑 factory 는 `assert_layout_valid` 호출 누락 금지.
3. **"env flag 로 known-bad 경로 살려두기"**. 실패한 실험 코드는 삭제하거나 `#[cfg(experimental)]` 같은 compile-time feature gate 로 분리. 런타임 env 로 production 에서 켜는 것 금지.
4. **stale convention 모듈 재사용**. `#[deprecated]` 또는 `stale_path_panic` 모듈을 호출하는 새 코드 금지.
5. **문서는 A 식, 코드는 B 식**. 주석과 구현이 다르면 둘 중 하나는 반드시 틀린 것. 즉시 동기화.
6. **IC 규약을 경로별로 다르게** (예: `v_b = Θ₁` vs `v_b = 3·Θ₁`).
7. **polter 와 Π_BASS 혼용** — 두 객체는 별개 함수를 통해서만 접근.
8. **raw code variable 을 직접 source assembly 에 주입** (§1.2 금지).
9. **`dopac` 를 production 코드에서 읽기**. 재활성화 요건은 §15.2.
10. **time convention 을 silently 교환** (§3).
11. **Thomson opacity `τ'` 를 직접 저장** — `χ` 사용.
12. **export 산출물에 `StatusMetadata` 누락** — production-facing export 는 반드시 metadata 동반.
13. **솔버→HTT/MIO 로 `ForwardBridge` 우회** — §5.5 대로 bridge 필수.

---

## §8. PR 체크리스트

새 PR 은 다음을 만족해야 머지 가능:

- [ ] 추가된 물리 상수가 있다면 `core::ssot::constants` 에 있는가?
- [ ] 새 `CambLayout` 생성자가 있다면 validator 를 호출하는가?
- [ ] 새 source term 계산이 있다면 `core::ssot` 헬퍼를 쓰거나, 그에 상응하는 정의를 SSOT 에 추가했는가?
- [ ] `polter` / `Π_BASS` 를 쓴다면 어느 쪽인지 명시했는가?
- [ ] time convention 이 명시되어 있는가? (`TimeConvention` enum 참조)
- [ ] `#[deprecated]` 함수를 호출하지 않는가?
- [ ] 주석/docstring 이 실제 계산과 일치하는가?
- [ ] `BASS_*` 환경변수를 신설하는가? production 경로 밖에서만 영향을 주는가?
- [ ] Export 를 추가한다면 `StatusMetadata` 를 carry 하는가?
- [ ] HTT/MIO 로 가는 export 가 있다면 `ForwardBridge` 경유하는가?
- [ ] `cargo check --lib --release` 통과?
- [ ] 관련 물리 문서 (`BASS_STATUS_*`, `README`) 가 함께 갱신되었는가?
- [ ] TDD gate 통과 — identity/limit/channelwise/regression/caveat test 존재?
- [ ] SDD delta 문서 작성 — 무엇을 owns 하고 무엇을 claim 안 하는지 명시?

TDD/SDD 상세는 `docs/PR_CONSTITUTION.md`.

---

## §9. Audit Trail (grep patterns)

SSOT 규약 위반 탐지:

```bash
# 매직 넘버 외부 사용
grep -rn "2\.0328\|3\.044\|1\.0132" --include="*.rs" src/ \
  | grep -v "core/ssot.rs" | grep -v "^.*//"

# has_pol 우회
grep -rn "lmax_pol > 0" --include="*.rs" src/ | grep -v "has_pol"

# 미세 τ' 직접 저장 (χ 가 아닌)
grep -rn "tau_prime\|tau_dot\b" --include="*.rs" src/

# 분리된 polter 규약 혼용
grep -rn "2\.0/5\.0.*theta2\|3\.0/5\.0.*e2" --include="*.rs" src/ \
  | grep -v "core/ssot.rs"

# dopac 신규 참조 (E3 fence 우회)
grep -rn "\.dopac\|bg\.dopac" --include="*.rs" src/

# StatusMetadata 없는 export 구조체
grep -rn "pub.*Export\b" --include="*.rs" src/ \
  | grep -v "StatusMetadata\|status:"

# ForwardBridge 없는 HTT/MIO 경계
grep -rn "fn export_to_htt\|fn export_to_mio" --include="*.rs" src/
```

정기적으로 (각 phase 완료 시) 위 grep 결과를 audit log 에 기록.

---

## §10. Known-Limit Recovery Tables (요약)

모든 branch 는 reduction limit 에서 명시된 reference 를 **반드시 복원** 해야 한다. 상세 27개 항목은 `docs/KNOWN_LIMITS.md` 참조.

- 10.1 **FLRW denominator** (7 limits): Sachs-Wolfe, tight coupling, `R_b → 0`, scalar FLRW, visibility off, reionization off, backreaction off
- 10.2 **Exact anisotropic** (6 limits): Minkowski, isotropic FLRW, homogeneous Bianchi, scalar branch, local patch off, global tilt off
- 10.3 **Recombination / history** (6 limits): Saha, Peebles, HyRec-FLRW, DirSob→isotropic, FullChar→DirSob, hydrogen-only
- 10.4 **Reionization** (6 limits): isotropic FLRW, homogeneous box, Stromgren, photon accounting, weak anisotropy, channel-off
- 10.5 **Backreaction** (4 tiers): Tier-1 (background-only), Tier-2 (imperfect fluid), Tier-3 (response-aware), off
- 10.6 **Unresolved high-ℓ** (4 limits): `L → ∞`, scalar FLRW BB, refinement off, trace-benign residual

---

## §11. Admissibility / Positivity SSOT

Universal hard invariants:
```
χ ≥ 0,           g ≥ 0,
0 ≤ x_e ≤ 1,     0 ≤ x_HII ≤ 1,
T_m > 0,         T_k > 0,         T_s > 0.
```

코드 권위 위치: `core::ssot::assert_*` 계열.

**Branch-specific**:
- Reduced branches → adequacy tag 필수 (`reduced-branch`)
- Unresolved sectors → closure/caveat tag 필수 (`caveat-required`)
- Tier-3 backreaction → research-mode tag 필수

---

## §12. Status Metadata & Export Schemas

모든 serious export 객체는 다음을 carry:

```rust
pub(crate) struct StatusMetadata {
    pub(crate) branch_tags:        Vec<String>,   // e.g. "denominator", "DirSob"
    pub(crate) approximation_tags: Vec<String>,   // e.g. "hydrogen-only"
    pub(crate) caveat_tags:        Vec<String>,   // e.g. "caveat-required"
}
```

**18-tag frozen dictionary** (`core::ssot::tags::*`):
```
denominator, prototype-tier, research-mode, reduced-branch,
reference-branch, fixed-history, hydrogen-only, helium-off,
visibility-off, reionization-off, backreaction-off, refinement-off,
wrapper-only, response-aware, DirSob, FullChar,
production-default, caveat-required
```

태그 사용 예시, 조합 규칙, 6개 export schema 의 구체적 payload 구조는 `docs/STATUS_TAGS_AND_EXPORTS.md`.

**Forward bridge rule**:
```
solver-side object  →  ForwardBridge<T>  →  HTT / MIO export
```

---

## §13. Minimal Test SSOT (canonical test families)

### 13.1 Canonical source tests
- `test_pi_bass_from_hw_basis`
- `test_pi_bass_from_class_like_basis`
- `test_temperature_source_uses_pi_bass_over_4`
- `test_polarization_source_uses_3gpi_over_4`

### 13.2 Exact hierarchy tests
- `test_exact_hierarchy_split_fs_geom_coll`
- `test_scalar_flrw_recovery_from_exact_branch`
- `test_no_spurious_B_from_scalar_branch`

### 13.3 Recombination / history tests
- `test_recomb_rates_are_proper_time_rates`
- `test_conformal_conversion_multiplies_rates_by_a`
- `test_recomb_export_contains_xe_tm_tau_g_chi`
- `test_fullchar_reduces_to_dirsob_in_weak_limit`

### 13.4 Reionization tests
- `test_transport_first_sweep_order_is_fixed`
- `test_photon_accounting_budget_is_reported`
- `test_deltaTb_export_contains_required_fields`
- `test_lightcone_export_contains_metadata`

### 13.5 Backreaction tests
- `test_tier1_is_background_only`
- `test_tier2_exposes_imperfect_fluid_components`
- `test_tier3_carries_response_metadata`
- `test_solver_tau_sector_not_aliasing_mio_reports`

### 13.6 Unresolved angular tests
- `test_unresolved_sector_log_contains_blockwise_terms`
- `test_sigma_and_xi_are_separated`
- `test_bb_residual_not_folded_into_trace_metric`
- `test_refinement_reads_unresolved_diagnostics`

**Rule**: 각 test family 는 PR 머지 전제. 누락 시 rollback.

---

## §14. PR Constitutional Rules (요약)

**TDD rule**: core burden 은 test 로 먼저 표현되지 않으면 PR 머지 불가.
- identity / limit / channelwise / regression / caveat 5 카테고리 모두 필요.

**SDD rule**: major PR 은 solver design delta 문서 동반 필수.
- 무엇을 owns 하는지 / 어떤 semantics 인지 / 어떤 파일 경계인지 / 어떤 theorem/validation 을 target 하는지 / 무엇을 claim 하지 **않는지**.

**Promotion rule**: tests pass + semantic burden explicit + rollback conditions known + channelwise burden 평탄화 없음 → 그때만 승진.

**Critical path rule**:
1. preserve FLRW denominator
2. stand up exact anisotropic transport backbone
3. add source ownership
4. add recombination / history realism
5. then adaptive reduction, reionization, backreaction

**9 programme tracks**: A (FLRW denominator) → B (exact transport) → C (source registry) → D (recomb HyRec-Cov) → E (reion char) → F (hybrid low/mid/high-ℓ) → G (EFT backreaction) → H (HTT/MIO atlas bridge) → I (validation campaigns).

상세는 `docs/PR_CONSTITUTION.md`.

---

## §15. 예외 / 완화 절차

SSOT 를 깨야 하는 상황 (예: 새로운 물리 섹터 도입):

1. **SSOT 에 먼저 추가** — `core::ssot` 에 새 상수/헬퍼 등록 후 call-site 작성
2. **대안 제시** — 기존 헬퍼로 해결 안 되는 이유를 PR 에 명시
3. **Bridge 문서화** — 본 문서 §6 표에 새 항목 추가
4. **Validator 갱신** — invariant 추가/완화 시 `validate_layout` / `assert_*` 수정
5. **Test family 확장** — §13 canonical tests 에 신규 test 이름 등록

이 절차 없이 SSOT 우회는 audit 회수 1회에서는 경고, 2회부터는 revert.

### 15.1 폐지된 경로 (Phase B-1 post-audit 2026-04-17)

**런타임 panic**:
- `species::photon::PhotonState::polarisation_pi`
- `los::source::evaluate_source`

**`#[deprecated]` 경고만**:
- `collision::polarisation::polarisation_pi` (3-arg)
- `solver::multispecies::build_stacked_rhs` (Bianchi pipeline, convention 재검토 대기)

**코드 자체 영구 삭제**:
- `BASS_POLTER_DDOT=1` env 경로
- `BASS_POLTERDDOT_DUMP=1` 진단 출력
- `production_source_v1` 내 polterddot closed-form 9-term 계산
- `build_inner` dopac FD 계산 (필드는 유지, 값은 0 고정)

### 15.2 `dopac` / `polter_ddot` 재활성화 조건

만족해야 PR 진행 가능:
1. 부호 규약 확정 (`g_dot` 의 `-dX/dη` 와 일치)
2. CAMB `equations.f90:2746-2751` term-by-term reference dump 수행
3. `k² · polter + 3 · polter_ddot` cancellation 수치 확인
4. SSOT amendment — `core::ssot::quad_source_*` 에 새 변종 함수 추가
5. Regression test — `dump_dl_spectrum_*` 에서 RMS 목표 (<3% at ℓ≤300)

---

## §16. 향후 SSOT 확장 대상

현재 SSOT 에 포함되지 않았으나 편입 예정인 항목:

- Bianchi tilt 규약 (`σ_ab` vs `Σ²`, tilt-3-level decomposition)
- 재이온화 모델 파라미터 (`VisibilityParams` 내 산재)
- `MassiveNuConfig` hardcoded Planck minimal-mass → runtime parameter 승격
- `CL_PREFACTOR_SYNC` step-function 보정 완결 (`R-NORM-01`)
- endpoint FD 처리 비대칭 (`nonuniform_fd_3pt` endpoint zero vs one-sided)
- sparse-ell positivity guard (natural cubic overshoot)
- TCA (tight-coupling approximation) coefficient tables
- Exact anisotropic hierarchy full coefficient tables
- FullChar recombination PDE/characteristic solver details
- Tier-3 response-kernel library

각 항목 편입은 별도 PR. 본 문서 §6 표 갱신 동반 필수.

---

## §17. Formalism Scope — MB-95 Oracle vs PSTF Primary (2026-04-17)

본 저장소는 **두 종류의 Boltzmann formalism** 을 병행 운용한다. 두 형식의 역할과 경계를 명시적으로 잠근다.

### 17.1 Two formalisms present

| Formalism | 출처 | 위치 | 역할 |
|---|---|---|---|
| **MB-95** (Ma–Bertschinger synchronous gauge, brightness multipole) | Ma & Bertschinger 1995; Lewis & Challinor 2000 (CAMB) | `src/solver/sync_gauge_camb.rs` | **Verified FLRW oracle.** CAMB 와 직접 비교 가능. |
| **PSTF** (1+3 covariant, symmetric trace-free tensor hierarchy `I_{A_ℓ}`) | Ellis–Maartens–MacCallum; Challinor–Lasenby 1999; Tsagas et al. 2008 | `src/pstf/` (현재) → `src/solver/pstf_primary/` (예정) | **Production target.** Bianchi extension 의 자연 frame. |

### 17.2 Role assignment

- **MB-95 는 production 이 아니다.** 현재 `sync_gauge_camb::solve_production_spectrum` 이 D_ℓ 을 생산하지만, 그 역할은 **검증된 oracle** (verified equivalence target) 이지 final production 이 아니다. 논문에서는 "intermediate validation step" 으로 서술한다.
- **PSTF 가 production target 이다.** `x_C` 의 정의(`Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}`)와 tetrad-based departure decomposition 은 PSTF/tetrad frame 에서만 well-defined. 최종 production D_ℓ 은 PSTF 경로에서 나와야 한다.
- **FLRW 극한 일치가 진짜 validation 이다.** "PSTF(FLRW limit) → MB-95 → CAMB" 의 체인에서 인접한 두 쌍이 각각 ≤0.5% 일치해야 end-to-end validation 이 성립한다.

### 17.3 Hard boundaries

다음은 MB-95 code 에만 적용, PSTF code 에서는 재유도 필요:

- **Gauge 변수 `σ` 의 의미**: MB-95 에서 `σ ≡ (h'+6η')/(2k)` 는 synchronous gauge metric shear (gauge artifact). PSTF 에서 `σ_{ab}` 는 tetrad extrinsic curvature (geometric, gauge-invariant). **코드 변수 이름 collision 금지** — PSTF 구현에서는 `sigma_ab` 또는 `shear_geom` 같은 distinct naming 을 사용한다.
- **ℓ-mixing recursion**: MB-95 는 `k/(2ℓ+1)·[ℓΘ_{ℓ-1} − (ℓ+1)Θ_{ℓ+1}]`. PSTF 는 covariant divergence `D^{a_{ℓ+1}} I_{A_ℓ a_{ℓ+1}}` 와 symmetric projection. Bianchi 에서는 structure constant `C^a_{bc}` 가 얹힘. **두 재귀를 같은 함수로 구현 금지.**
- **Initial conditions**: MB-95 의 adiabatic IC (`bootstrap_ic_camb`) 는 `η`, `k·η` 조합 기반. PSTF 의 adiabatic IC 는 `I_0^{(γ)}`, `I_0^{(ν)}`, covariant gradient 기반. **별도 유도, 별도 SSOT helper.**

### 17.4 Shared (formalism-agnostic) layer

다음은 두 formalism 모두 동일하게 사용:

- `core::ssot::constants::*` (NEFF_*, NU_HESSIAN_*, MIN_LMAX_*)
- Background expansion history (a, ℋ, Ω_i)
- HyRec recombination (xe, τ, g, g', g'')
- Bessel / LoS integrator infrastructure
- ODE integrator backends (Rodas5P, IMEX-ARK4)
- k-grid / ℓ-grid strategy
- `core::ssot::cl_prefactor_at_k` (R-NORM-01 step function)
- `core::ssot::friedmann_hsq_from_grho_sum`
- Governance layer (PR_CONSTITUTION, KNOWN_LIMITS, STATUS_TAGS_AND_EXPORTS, BASS_STACK_OWNERSHIP)

### 17.5 Formalism-specific SSOT (separate namespaces)

MB-95 변수 위에 정의된 SSOT helper 는 `core::ssot::mb95::*` namespace 로 이동 예정:

- `polter`, `polter_dot` → `ssot::mb95::polter`, `ssot::mb95::polter_dot` (MB-95 brightness multipole 변수)
- `doppler_source`, `quad_source_no_polterddot` → `ssot::mb95::doppler_source`, `ssot::mb95::quad_source_no_polterddot`

대응하는 PSTF SSOT 는 새로 유도·구현:

- `ssot::pstf::pi_abc` — PSTF polarization tensor source
- `ssot::pstf::doppler_covariant` — PSTF Doppler source from covariant velocity gradient
- `ssot::pstf::quad_covariant` — PSTF quadrupole collision source

현재 `source::registry::{source_sw, source_doppler, source_polter_quad, source_emode}` 의 **signature 는 formalism-agnostic 유지**, 내부 구현이 두 경로로 분기 (feature flag 또는 별도 registry submodule).

### 17.6 Migration 경로 — Parallel Dual-Track (2026-04-17 승인)

두 formalism 을 **동시에** 유지하며 단계적 전환:

- **Phase 1**: PSTF primary 를 FLRW scalar sector 에 한해 production-ready 로 완성 (PR-020..PR-024 예상). 이 단계에서 MB-95 는 그대로 production 유지.
- **Phase 2**: FLRW-limit equivalence test — 모든 ℓ ∈ [2, 300] 에서 MB-95 D_ℓ ≡ PSTF(FLRW) D_ℓ 이 ±0.5% 이내 일치 검증 (PR-025).
- **Phase 3**: `solve_production_spectrum` backend 를 PSTF 로 switch. MB-95 는 `#[cfg(test)] oracle` 로 격하 (PR-026).
- **Phase 4**: Bianchi extension — tetrad layer, σ_{ab}, tilt velocity 도입 (PR-050..PR-080).

Big-bang 재작성 금지. 각 Phase 마다 D_ℓ regression guard 유효.

### 17.7 Hard rule

> **새 물리량 SSOT 를 만들 때는 formalism scope 를 명시해야 한다.**
>
> - Formalism-agnostic → `core::ssot::*` (namespace root)
> - MB-95 전용 → `core::ssot::mb95::*`
> - PSTF 전용 → `core::ssot::pstf::*`
> - Bianchi 전용 → `core::ssot::bianchi::*` (Phase 4 도입)
>
> Scope 를 명시하지 않은 SSOT helper 는 PR review 에서 반려.

---

## §18. 버전 이력

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-04-17 | Phase B-1 post-audit 제정. A/B/C/D/E groups (14 bugs) 반영. |
| 2.0 | 2026-04-17 | 업로드 4문서 반영. §2-§5, §10-§14 전면 확장. Companion 문서 3개 분리. |
| 2.1 | 2026-04-17 | §17 Formalism Scope 신설. MB-95 oracle vs PSTF primary 경계 명시. Parallel dual-track migration 경로 승인. |

---

*본 문서는 BASS 저장소에서 SSOT 규약 변경 시 반드시 함께 수정되어야 한다.*
