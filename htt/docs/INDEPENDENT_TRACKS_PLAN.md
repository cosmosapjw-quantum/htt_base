# 독립 트랙 작업 계획 — bass_py 병렬 실행

**기준일**: 2026-04-19
**상위 문서**: [BASS_PY_HTT_TSC_RESEARCH_PLAN.md](BASS_PY_HTT_TSC_RESEARCH_PLAN.md) (v2 amplified)
**목적**: `bass_py` 개발 세션(LB-2a PSTF hierarchy, `bass_py/bass/hierarchy/` 등)과 **디스크/깃 충돌 없이** 동시 진행 가능한 워크스트림 정리

---

## §0. 충돌 회피 원칙

### 0.1 bass_py 세션이 점유할 영역 (건드리지 말 것)

LB-2a 이후 로드맵(W10-02 → W15-03, MIDHIGH extension)을 고려할 때 다른 세션이 점유할 가능성이 높은 디렉터리:

- `bass_py/bass/hierarchy/` — PSTF hierarchy (현재 active, `hierarchy_rhs.py` 미커밋)
- `bass_py/bass/spectrum/` — W10-02 CAMB V-gate
- `bass_py/bass/los/` — W11 direction-dependent C_ℓ, BiPoSH
- `bass_py/bass/transport/` — W12/W13 W_R window, β-dynamics
- `bass_py/bass/validation/` — W12 channel routing
- `bass_py/scripts/make_physics_gallery.py` (현재 수정 중)
- `bass_py/bass/closure/`, `bass_py/bass/collision/` 가능성
- `plots/physics_gallery/` (LB-phase 종료 시 자동 regen)

### 0.2 본 계획이 점유할 영역 (독립)

| 영역 | 경로 | 근거 |
|---|---|---|
| HTT 전체 | `bass_py/htt/` | bass_py 세션은 `bass/` 하위만 만짐 |
| tsc 전체 | `bass_py/tsc/` | ↑ 동일 |
| 신규 `src/common/` | `bass_py/src/common/` (신규 디렉터리) | 기존 충돌 없음 |
| Manuscript | `project/`, `docs/design/` 하위 | 코드 경로 분리 |
| 상위 설계 문서 | 리포 루트의 `*.md` | scan만 |
| Audit/SSOT 점검 | `docs/audits/`, read-only grep | 파일 생성만 |

### 0.3 운영 규칙

1. **작업 시작 전 `git status` 확인** — 다른 세션의 미커밋 변경이 `htt/` / `tsc/` 에 있으면 중단 후 user에게 확인
2. **additive 커밋만** (메모리 규칙 `feedback_git_workflow.md`)
3. **커밋 단위를 본 문서의 Track ID로 prefix** (예: `HTT-P0-AM: ...`, `TSC-EXT-FF: ...`)
4. **Phase-boundary gate 준수** — 상위 트랙을 "완료"로 표시하기 전 `docs/audits/AUDIT_PROMPT.md` 자가 점검 (메모리 규칙 `feedback_phase_boundary_audit.md`)
5. **plots/physics_gallery 건드리지 않음** — bass_py 세션이 per-phase rule로 자동 관리

---

## §1. 트랙 카탈로그

| Track ID | 이름 | 우선 | 예상 L | 예상 시간 | 블로킹 | 상위 §참조 |
|---|---|---|---|---|---|---|
| **SSOT-01** | T_CMB 단일값 합의 + anti-regression | **P0** | ~50 | 2h | 없음 | §10.3, §13.1 (May W3) |
| **HTT-P0-AM** | `PR13AM` production_mode gate | **P0** | +20 | 3h | 없음 | §6.1, §6.8 |
| **HTT-P0-AJ** | `PR13AJ` PreferredAxis + production_allowed | **P0** | +40 | 4h | 없음 | §6.2 |
| **HTT-P0-AH** | `PR13AH` 4-summary 분리 | **P0** | +60 | 4h | 없음 | §6.3 |
| **HTT-P0-ZOA20** | `FLRW_tilt_zoa20_mean` downstream default 제거 전수조사 | **P0** | grep-driven | 4h | AM/AJ/AH 후 | §13.1 (May W2) |
| **COMMON-A** | `src/common/contracts.py` + `sky_geometry.py` | **P0** | ~300 | 6h | 없음 | §6.4, §6.6 |
| **COMMON-B** | `src/common/healpix_selection.py` | P1 | ~250 | 6h | COMMON-A | §6.4 |
| **COMMON-C** | `src/common/bulkflow_estimator.py` | P1 | ~200 | 4h | COMMON-A | §6.4 |
| **COMMON-D** | `src/common/bulkflow_likelihood.py` | P1 | ~250 | 8h | COMMON-A/C | §6.4 |
| **COMMON-E** | `src/common/posterior_summary.py` | P1 | ~200 | 4h | COMMON-D | §6.4 |
| **COMMON-F** | `src/common/mock_calibration.py` | P1 | ~300 | 8h | COMMON-C (최소) | §6.4, §6.7 |
| **HTT-STAB** | HTT 27 figure script + nulls sys.path cleanup | P1 | +80 수정 | 6h | 없음 | §16.2 |
| **HTT-NULL** | `htt.nulls.runner` smoke test 복구 | P1 | +60 | 4h | HTT-STAB 병렬 | §13.6 (Oct W1) |
| **TSC-01** | `tsc.admissibility.test_realizability` 테스트 복구 | **P0** | ~300 | 6h | 없음 | §8.2 item 1 |
| **TSC-02** | `tsc.diagnostics.filling_fraction` (F_Bayes) | P1 | ~400 | 8h | 없음 | §8.2 item 2, §10.2 |
| **TSC-03** | `tsc.diagnostics.three_bound_hierarchy` | P1 | ~350 | 6h | TSC-02 선호 | §8.2 item 3 |
| **TSC-04** | `tsc.charts.theta4_bridge_verify` | P2 | ~250 | 4h | 없음 | §8.2 item 4 |
| **TSC-05** | `tsc.charts.michaelis_menten_export` | P2 | ~200 | 3h | 없음 | §8.2 item 5 |
| **TSC-06** | `tsc.integration.htt_bridge` (F_Bayes 교차 검증) | P2 | ~150 | 3h | TSC-02 + HTT stable | §8.2 item 6, §10.2 |
| **DOS-A13** | 15-model dossier 템플릿 + prior spec | P1 | ~500 | 6h | 없음 | §11.10.1 |
| **DOS-A14** | 5 null family 수학 유도 markdown | P2 | ~600 | 8h | 없음 | §11.10.2 |
| **MANU-CH03** | ch03 Framework 섹션 확장 설계 (R-TILT-02/03 레퍼런스) | P1 | +~1100 | 16h | 없음 | §11.3 ch03 |
| **MANU-CH06** | ch06 Pipeline bass_py 완료분 prose | P2 | +~700 | 12h | bass_py zip freeze | §11.3 ch06 |
| **REG-01** | Regression test 신규 7건 (§6.10) | P1 | +~250 | 6h | 해당 P0 트랙 각각 | §6.10 |

**즉시 시작 가능 (의존 없음)**: SSOT-01, HTT-P0-AM, HTT-P0-AJ, HTT-P0-AH, COMMON-A, HTT-STAB, HTT-NULL, TSC-01, TSC-04, TSC-05, DOS-A13, DOS-A14, MANU-CH03

---

## §2. P0 트랙 상세

### 2.1 SSOT-01 — T_CMB 단일값 합의

**문제**: `bass.observational` = 2.7255 K vs `htt.core.ssot.C` = 2.72548 K (상위 §10.3).

**작업**:
1. `bass_py/bass/observational/planck_mes_bounds.py` T_CMB 값 확인 (read-only — **수정은 bass_py 세션 소관**)
2. `bass_py/htt/core/ssot.py` T_CMB 값 확인
3. 두 값의 출처 (Planck paper 인용) 추적 → `docs/audits/SSOT_TCMB_DRIFT_2026-04-19.md` 작성
4. 권장 방향: Planck 2018 = 2.72548 K (Fixsen 2009) 이 정식 → htt 쪽 유지, bass 쪽 수정 요청 **문서화만**
5. htt 쪽에 anti-regression guard: `test_tcmb_ssot_frozen` 추가 (`bass_py/htt/tests/test_ssot_drift.py`)

**산출물**:
- `docs/audits/SSOT_TCMB_DRIFT_2026-04-19.md` (권고안)
- `bass_py/htt/tests/test_ssot_drift.py` (1 testcase)

**Gate**: grep으로 양측 상수의 모든 참조 경로 확인 후 권고안에 기록.

**주의**: bass 측 상수는 **수정하지 않음** (bass_py 세션 충돌 방지). 본 트랙은 진단 + htt 측 guard + recommendation까지만.

---

### 2.2 HTT-P0-AM — PR13AM production_mode gate

**대상 파일**: `bass_py/htt/PR13AM_te_sign_d1d3_bridge.py` (또는 `bass_py/htt/htt/PR13AM_*.py`)

**작업**:
1. 파일 위치 Grep으로 확정 (HTT 구조 더블-nest: `htt/htt/` 가능성)
2. `_direction_weight_status()` 시그니처에 `production_mode: bool = False` 추가
3. 상위 §6.8의 정확한 코드로 교체
4. 호출처 전수 조사 + 기본값 유지 (backward compat)
5. 신규 테스트 `test_PR13AM_production_gate.py`:
   - `test_production_mode_rejects_uniform_fallback` — all-zero weights + production_mode=True → `RuntimeError`
   - `test_diagnostic_mode_allows_uniform_fallback` — 동일 입력 + production_mode=False → 정상 + `fallback_status='uniform_fallback_diagnostic_only'`

**Gate**: 두 테스트 PASS + HTT 기존 testsuite 무회귀.

---

### 2.3 HTT-P0-AJ — PreferredAxis production_allowed gate

**대상 파일**: `bass_py/htt/PR13AJ_full_a2m_restoration.py`

**작업**:
1. `PreferredAxis` dataclass에 다음 필드 추가 (`frozen=True` 유지):
   - `source: str`
   - `weight_mode: str`
   - `selection_mode: str`
   - `production_allowed: bool = False`
   - `provenance_hash: str = ""`
2. `restore_full_a2m()` 초입에 gate:
   ```python
   if not axis.production_allowed:
       raise RuntimeError(...)
   ```
3. 기존 호출처 전수조사 — `PreferredAxis(...)` 리터럴 생성자 호출 모두 신규 필드 채우도록 업데이트 (기본값으로도 허용)
4. 신규 테스트:
   - `test_preferred_axis_gate_blocks_diagnostic` — production_allowed=False → `RuntimeError`
   - `test_preferred_axis_gate_allows_fiducial` — production_allowed=True → 정상 복원

**Gate**: diagnostic axis로는 `a_2m` 복원 절대 불가능.

---

### 2.4 HTT-P0-AH — 4-summary 분리

**대상 파일**: `bass_py/htt/PR13AH_observables_reintegration.py`

**작업**:
1. `reintegrate_observables()`를 §6.3의 4-summary 스키마로 확장:
   - `raw_summary` (diagnostic_only)
   - `zoa_masked_summary` (diagnostic_only)
   - `selection_aware_summary` (Mode 1 baseline)
   - `mock_calibrated_summary` (Mode 2 fiducial) — **COMMON-F 이후 실제 구현, 그 전까지는 `selection_aware` 복제 + `calibration_pending=True` 플래그**
2. 4개 summary 모두 `spherical_mean` 기반 (COMMON-A 필요하지 않음; 이 단계에서는 기존 raw mean 로직을 임시로 재사용하되 접근점만 4개로 분리)
3. 테스트 `test_four_summary_consistency`: 4개 키 모두 존재 + dtype 일관

**주의**: 진짜 unit-vector `spherical_mean`은 COMMON-A가 제공하는 utility. AH 단계에서는 **구조만 분리**, 로직은 COMMON-A 이후 교체.

**Gate**: 4개 키 존재 + 기존 artifact 소비처(if any) 호환.

---

### 2.5 HTT-P0-ZOA20 — `FLRW_tilt_zoa20_mean` 전수제거

**작업**:
1. Grep 전수조사:
   ```
   grep -r "zoa20_mean" bass_py/htt/
   grep -r "FLRW_tilt_zoa20" bass_py/
   ```
2. 각 참조를 세 분류로 태깅:
   - **문서/주석**: 그대로 유지 (역사 기록)
   - **diagnostic 로직**: `operational_default_zoa_half_angle_deg` 상수로 교체 (§3.6)
   - **production downstream default**: 제거 or `production_default_axis = None` 기본값으로 교체
3. `recommended_zoa_half_angle_deg`, `operational_default_zoa_half_angle_deg`, `production_default_axis` 3 상수를 `bass_py/htt/core/constants.py` (신규) 또는 기존 ssot.py 에 추가
4. Phase-A gate: `grep -r "zoa20_mean" bass_py/htt/ | grep -v "# diagnostic\|# historical\|test_"` 0 hits

**Gate**: production 경로의 참조 0건 + 신규 3-tier 상수 체계 안착.

**의존**: HTT-P0-AJ 완료 후 실행 (`PreferredAxis` 구조가 안정화되어야 교체지점 파악 용이).

---

### 2.6 COMMON-A — contracts.py + sky_geometry.py

**대상 디렉터리**: `bass_py/src/common/` (신규 생성) — **충돌 주의**: bass_py 세션이 만약 `bass_py/src/` 를 쓰지 않는다면 문제 없음. 확인 후 진행; 만약 충돌 우려가 있으면 `bass_py/htt/common/` 로 대체.

**파일 1: `contracts.py` (~150 L)**:
- `PreferredAxis` (§6.2, frozen dataclass)
- `SkySelectionConfig` (§6.6, invariant check 포함)
- `DirectionalSummary` (4-summary dataclass)
- `DynestyResult` (samples, logwt, logz, ncall, config)
- `MockCalibrationReport` (bias, coverage_68, credible_radius)

**파일 2: `sky_geometry.py` (~150 L)**:
- `lb_to_unitvec`, `unitvec_to_lb`
- `spherical_mean` (§6.6의 정확한 구현)
- `angular_separation_matrix`
- `galactic_plane_mask`
- `normalize_weights` (§6.6)

**테스트** (`test_sky_geometry.py`, ~20 cases):
- `test_spherical_mean_vs_naive_mean_divergence` — l=[0,359,1,358] 등 extreme에서 naive mean과 차이
- `test_lb_to_unitvec_roundtrip`
- `test_normalize_weights_rejects_all_zero_in_production`
- `test_skyselection_config_invariants`

**Gate**: 테스트 PASS + 타 트랙이 import 가능.

---

### 2.7 TSC-01 — tsc.admissibility 테스트 복구

**대상**: `bass_py/tsc/admissibility/realizability.py` (402 L, **테스트 0건**).

**작업**:
1. `realizability.py` 읽고 public API 파악
2. `bass_py/tsc/admissibility/test_realizability.py` 작성 — ~35 testcases:
   - positivity of probability measures on simplex
   - marginal consistency
   - edge cases (zero mass, unit mass, degenerate)
   - cross-check with `spherical_quadrature` (tsc.diagnostics, 이미 있음)
3. Ground truth는 해당 파일 기존 로직 + spherical_quadrature 의 test fixture 참조

**Gate**: pytest `bass_py/tsc/` 무회귀 + 신규 35건 PASS.

**왜 독립인가**: tsc는 admissibility/diagnostics/charts 로 완전히 self-contained, bass 의존 0.

---

## §3. P1 트랙 상세 (순차 의존 있음)

### 3.1 COMMON-B ~ COMMON-F (Layer A → C → F)

COMMON-A 완료 후 병렬/순차 조합으로 진행:

```
COMMON-A ──┬── COMMON-B (healpix_selection) ──┐
           ├── COMMON-C (bulkflow_estimator) ─┤
           └── COMMON-E (posterior_summary) ──┼── COMMON-F (mock_calibration)
                                              │
                              COMMON-D (bulkflow_likelihood) ──┘
```

각 모듈 세부 서명은 상위 §6.4 표 그대로 따름. 테스트 파일명은 `test_<module>.py`, 각 5~10 cases.

### 3.2 TSC-02 — filling_fraction (F_Bayes)

**목표**: posterior mean $F_{\rm Bayes} = E[Q \mid D]$, $Q = |x|/B$ 계산 모듈.

**작업**:
1. `bass_py/tsc/diagnostics/filling_fraction.py` (~400 L):
   - `FillingFractionReport` dataclass
   - `compute_filling_fraction(samples, B_callable)` 함수
   - posterior-mean (not point estimate) 강제
2. `test_filling_fraction.py` (~30 cases):
   - synthetic posterior (Gaussian centered at x=0.3) → F_Bayes ≈ 0.093 ± 0.025 regression
   - point estimate vs posterior mean 차이 +30% 확인

**Gate**: ln B=+26.40 규모의 합성 posterior에서 기준값 복원.

### 3.3 TSC-03 — three_bound_hierarchy

**목표**: $B_\sigma > B_\omega > B_{\dot u}$ 계층 검증 모듈.

**작업**:
1. `bass_py/tsc/diagnostics/three_bound_hierarchy.py` (~350 L):
   - 각 bound 정의 (상위 §4.3)
   - `BoundReport` dataclass
   - hierarchy 위배 시 `ValueError` + 진단 메시지
2. `htt.core.bounds`와 cross-check하는 integration test

**Gate**: 9개 Bianchi type 전부에 대해 계층 성립.

### 3.4 HTT-STAB — figures sys.path cleanup

**문제**: §1.3.5 표 — 27개 figure script가 sys.path 조작을 통해 동작하여 pytest 환경에서 깨짐.

**작업**:
1. `bass_py/htt/figures/conftest.py` 신설 → `pyproject.toml`/editable install 기반으로 import path 정리
2. 27개 script 중 `sys.path.insert(...)` 패턴 grep + 제거
3. `pytest bass_py/htt/figures/` smoke test (import만, 실제 figure 생성은 skip marker)

**Gate**: `pytest --collect-only bass_py/htt/figures/` 에러 0건.

### 3.5 HTT-NULL — nulls.runner 복구

**문제**: §0.1 표 — htt 테스트 123건 중 "일부 sys.path 문제".

**작업**:
1. `bass_py/htt/nulls/` 디렉터리 전수점검
2. `runner.py` smoke test (`test_null_smoke.py`) 복구
3. 5 family (N1~N5) import 각각 가능 확인

**Gate**: `pytest bass_py/htt/nulls/` 전 PASS.

### 3.6 DOS-A13 — 15-model dossier 템플릿

**목표**: §11.10.1 의 15-model × 130 L 템플릿 구조 확정 (실데이터는 Phase H).

**작업**:
1. `docs/dossier/A13_template.md` — 단일 모델 표준 형식 (상위 §11.10.1 표 구조)
2. `docs/dossier/A13_00_FLRW.md` — null 모델 예시 작성 (기준 dossier)
3. `docs/dossier/A13_01_FLRW_tilt.md` — 메인 모델 예시 작성 (posterior는 placeholder)

**Gate**: 템플릿 reviewable.

### 3.7 MANU-CH03 — ch03 Framework 확장

**목표**: §11.3 ch03 표의 8개 신규 섹션 중 코드 의존이 작은 3~4개 선행.

**우선 대상 섹션** (코드 독립):
- §3.X+5 Clarkson-Maartens killing (이론만)
- §3.X+6 Sphere mean 정의 (수식 + COMMON-A reference)
- §3.X+7 Selection-aware likelihood (이론만)
- §3.X+3 Θ⁴ bridge complete formula (tsc 의존 — TSC-04 병행 시 활용)

**코드 의존 섹션**은 후행:
- §3.X+1 W_R window (W12-01 결과 필요)
- §3.X+2 Tilt² 6 cross-terms (W13 결과 필요)

**산출물**: 기존 ch03 소스(위치는 `project/` 또는 `docs/`)에 섹션 추가. 최소 +~800 L.

---

## §4. P2 트랙 상세

### 4.1 TSC-04 — theta4_bridge_verify

**목표**: $a_2 = 4Q + 4A^2 + \tfrac{12}{7}Q^2 + \tfrac{44}{7}A^2Q + \ldots$ (§11.3 ch03 §3.X+3) 계수 audit.

**작업**:
1. `bass_py/tsc/charts/theta4_bridge_verify.py` (~250 L) — 계수별 독립 유도
2. `htt.core.teff_extended` 의 값과 비교

**Gate**: 계수 불일치 시 명확한 진단.

### 4.2 TSC-05 — michaelis_menten_export

**목표**: W10-01 Route B SSOT (C_1, C_2 완료분) 를 tsc 쪽에서도 export.

**작업**:
1. `bass_py/tsc/charts/michaelis_menten_export.py` (~200 L)
2. `bass.spectrum.cl_assembly.ROUTE_B_C1/C2` 읽기 + tsc 쪽 frozen constant mirror
3. anti-regression test

**Gate**: D_2(Σ²=1e-8)=0.174112 μK² 재현.

### 4.3 TSC-06 — htt_bridge

**목표**: `tsc.diagnostics.filling_fraction` (TSC-02) 와 `htt.core.analysis_extended.FillingFraction` 값 교차검증.

**작업**: `bass_py/tsc/integration/htt_bridge.py` (~150 L) + `test_ff_consistency.py`.

**Gate**: 두 값 rel_err < 1%.

### 4.4 DOS-A14 — null family 수학 유도

각 N1~N5 에 ~120 L: physical origin, forward model, SBI reference, signature, FPR prediction. `docs/dossier/A14_N{1..5}.md`.

### 4.5 MANU-CH06 — ch06 Pipeline bass_py 완료분 prose

bass_py zip freeze 이후 시작. W10-01까지 완료된 W-stack (§11.3 ch06 §6.2) 서술.

---

## §5. REG-01 — Regression test 신규 7건 (§6.10)

P0 트랙과 **병행**하여 점진 추가:

| Test | 대응 트랙 | 위치 |
|---|---|---|
| `test_production_mode_rejects_uniform_fallback` | HTT-P0-AM | `bass_py/htt/tests/` |
| `test_preferred_axis_gate_blocks_diagnostic` | HTT-P0-AJ | ↑ |
| `test_spherical_mean_vs_naive_mean_divergence` | COMMON-A | `bass_py/src/common/tests/` |
| `test_four_summary_consistency` | HTT-P0-AH | `bass_py/htt/tests/` |
| `test_mock_coverage_within_bounds` | COMMON-F | `bass_py/src/common/tests/` |
| `test_zoa_ladder_no_fallback_leak` | COMMON-B | ↑ |
| `test_weights_decomposition_logged` | COMMON-C | ↑ |

---

## §6. 즉시 실행 추천 순서

bass_py 세션의 방해 없이 즉시 시작할 수 있는 **첫 한 달 루틴**:

### Week 1 (Apr 20–26)

1. **SSOT-01** (Day 1, ~2h) — T_CMB 드리프트 audit 문서 + htt 측 guard test
2. **HTT-P0-AM** (Day 1–2) — uniform_fallback production_mode gate
3. **HTT-P0-AJ** (Day 2–3) — PreferredAxis gate
4. **HTT-P0-AH** (Day 3–4) — 4-summary 구조만 분리
5. **REG-01 일부** (Day 4) — AM/AJ/AH 대응 3건 커밋
6. **TSC-01** (Day 5–7) — tsc.admissibility 테스트 복구 (35건)

### Week 2 (Apr 27 – May 3)

7. **COMMON-A** (Day 1–2) — contracts + sky_geometry + test_spherical_mean
8. **HTT-P0-ZOA20** (Day 3) — `zoa20_mean` 전수 제거 sweep
9. **HTT-STAB** + **HTT-NULL** (Day 4–5) — sys.path cleanup (병렬)
10. **DOS-A13** 템플릿 (Day 6–7)

### Week 3 (May 4–10)

11. **COMMON-B** + **COMMON-C** (병렬)
12. **MANU-CH03** — 코드 독립 4섹션 작성 시작

### Week 4 (May 11–17)

13. **COMMON-D** → **COMMON-E** → **COMMON-F** (순차)
14. **TSC-02** — filling_fraction 모듈
15. **DOS-A14** null family 유도

---

## §7. 완료 게이트 (본 계획 전체)

전 트랙 완료 기준:

- [ ] P0 트랙 6건 + 대응 REG-01 테스트 모두 PASS
- [ ] `grep -r "zoa20_mean" bass_py/htt/ | grep -v diagnostic` 결과 0 (HTT-P0-ZOA20)
- [ ] `bass_py/src/common/` 7 모듈 + 테스트 그린
- [ ] `bass_py/tsc/` 테스트 ≥ 350 + admissibility ≥ 35
- [ ] HTT 전체 smoke test (123 + 신규) green, sys.path 오염 0
- [ ] `docs/dossier/A13_template.md` 리뷰 통과
- [ ] `docs/audits/SSOT_TCMB_DRIFT_2026-04-19.md` user 승인
- [ ] Phase-boundary audit 자체점검 (`docs/audits/AUDIT_PROMPT.md`) 통과 — 상위 메모리 규칙

---

## §8. 본 계획 외 위임 (bass_py 세션 담당, 본 트랙 제외)

혼선 방지를 위해 **이 계획에서 다루지 않는** bass_py 세션 전담 항목 명시:

- W10-02 CAMB V-gate (`bass.spectrum`)
- W11-01/02/03 direction-dependent C_ℓ, BiPoSH, Bianchi V2 gate (`bass.los`)
- W12-01/02 W_R window, frame-attribution bias (`bass.validation`, `bass.tilt`)
- W13-01/02 Dynamical tilt source, β → D_2 transfer (`bass.transport`, `bass.spectrum`)
- W14-01 3-signature discriminator (신규 또는 `bass.spectrum`)
- W15-01/02/03 — 주의: `src/common/` 모듈에 **의존**. 본 계획의 COMMON-A~F 가 선행되면 W15 는 bass_py 세션에서 단순 소비 가능.
- LB-2a 이후 PSTF hierarchy 후속
- `plots/physics_gallery/` per-phase refresh

본 계획이 `src/common/` 스택을 선행 구축함으로써 bass_py 세션의 W15-xx 프롬프트 진입 조건을 갖추어준다.

---

## §9. 버전 히스토리

| 버전 | 날짜 | 변경 |
|---|---|---|
| v1.0 | 2026-04-19 | 최초 — bass_py 세션 (LB-2a active) 병렬 독립 트랙 정리 |
| v1.1 | 2026-04-19 | v3 MIO 통합 패치 (§10~§17 추가). 앞 §1~§8 불변 유지 |

---

# PART II — v3 MIO 통합 패치 계획 (2026-04-19 추가)

**상위 문서 갱신**: [BASS_PY_HTT_TSC_RESEARCH_PLAN.md](BASS_PY_HTT_TSC_RESEARCH_PLAN.md) → [BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md](BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md) (v3.0).

**핵심 변화**:
1. **4번째 기둥 MIO 추가** — Model-Independent Observatory (v2에서 "epistemic control" 오해 전면 교정; v3는 physics-producing observatory로 재정의)
2. **G19 Hard Separation Rule** — HTT ↔ MIO 결과 단일 inferential score로 합산 **금지**. Cross-check만 허용
3. **Interface contracts** — `HttForwardOutput` / `MioCertificate` / `AtlasEntry` (DOC-03 III-2 기반 frozen dataclass 3종)
4. **Epistemic distributed ownership** — 중앙 certification engine 없음. 각 모듈 자체 책임
5. **Phase J (HJ-01~07)** — MIO 5 subpackage 신규 구현 (~3,000~5,000 L)
6. **Manuscript ch12 신설** — "MIO Observatory Results" (~1,750 L)
7. **MIO 전용 artifact/figure/table prefix**: `mio_` 강제

본 Part II는 앞 §1~§9 트랙 카탈로그를 **수정하지 않고** 이어서 추가되는 패치다. 이미 실행된 트랙의 **후속 보정 작업**과 **v3 신규 트랙**을 분리 기술한다.

---

## §10. 기 실행 트랙 상태 점검 (v3 반영 회고)

### 10.1 현재 커밋/파일 기준 완료 상태

| Track ID | 상태 | 증거 | v3 재검토 필요 |
|---|---|---|---|
| SSOT-01 | ✓ 완료 | `docs/audits/SSOT_TCMB_DRIFT_2026-04-19.md`, `bass_py/htt/tests/test_ssot_drift.py` | v3 §10.3 SSOT 표 그대로 유지 — **OK** |
| HTT-P0-AM | ✓ 완료 | `bass_py/htt/htt/PR13AM_te_sign_d1d3_bridge.py`, `test_PR13AM_production_gate.py` | **PATCH-01**: 파일은 HTT 트리에 있으나 v3 §1.4.1에서 **semantic 소유 = MIO**. 재배치 or meta tagging 결정 필요 |
| HTT-P0-AJ | ✓ 완료 | `PR13AJ_full_a2m_restoration.py`, `test_PR13AJ_gate.py` | OK — `PreferredAxis.production_allowed` gate는 v3에서도 유효 |
| HTT-P0-AH | ✓ 완료 | `PR13AH_observables_reintegration.py`, `test_PR13AH.py` | **PATCH-02**: 4-summary 중 `mock_calibrated_summary`는 COMMON-F 이후 실제 로직 교체 필요 (현재 placeholder) |
| HTT-P0-ZOA20 | ✓ 완료 | `docs/audits/ZOA20_SWEEP_2026-04-19.md`, `test_zoa20_sweep.py` | OK |
| COMMON-A | ✓ 완료 | `bass_py/src/common/{contracts,sky_geometry}.py` + tests | **PATCH-03**: v3는 `workspace/contracts/`에 `HttForwardOutput`/`MioCertificate`/`AtlasEntry` 추가 요구. COMMON-A의 `contracts.py`는 **유지**, 신규 contract는 별도 위치 |
| COMMON-B | ✓ 완료 | `healpix_selection.py` + test | OK |
| COMMON-C | ✓ 완료 | `bulkflow_estimator.py` + test | OK |
| TSC-01 | ✓ 완료 | `test_realizability.py`, `test_realizability_extras.py` | OK |
| MANU-CH03 | ◐ 부분 완료 | ch03 §3.X+5~7 subsection 작성 (Week 3 audit 기록) | v3 §11.14.2 ch11 재구성 요구 — **CH11 신규 트랙** (§13.1) 참조 |

### 10.2 v3 플랜이 요구하는 사후 수정 (PATCH-NN)

| PATCH ID | 대상 | 목적 | 트리거 |
|---|---|---|---|
| **PATCH-01** | PR13AM (`bass_py/htt/htt/PR13AM_*.py`) | MIO semantic ownership 반영 — 파일 내 docstring + module-level `__mio_owned__ = True` 태그 + artifact 출력 시 `mio_` prefix 강제. 물리적 재배치는 MIO 패키지 신설(§12) 후 결정 | v3 §1.4.1 "PR13AM은 MIO의 legitimate bridge" |
| **PATCH-02** | `PR13AH_observables_reintegration.py`의 `mock_calibrated_summary` | COMMON-F (mock_calibration.py) 구현 후 실제 bias correction 로직으로 교체 | COMMON-F 완료 시점 |
| **PATCH-03** | 신규 `bass_py/workspace/contracts/` (디렉터리 신설) | v3 Interface contracts 3종 추가. `src/common/contracts.py`는 내부 ZoA/bulk-flow용으로 그대로 유지 | §11 CONTRACTS-01 트랙 |
| **PATCH-04** | `legacy/mio/` 디렉터리 | 구 HTT-certification-engine 오해 버전 확인 + v3 신규 `bass_py/mio/`와 구분. 혼동 방지 주석 | §12 MIO-BOOT-01 트랙 |
| **PATCH-05** | `src/common/contracts.py`의 `PreferredAxis` | v3 추가 필드 **불필요** (현재 필드로 충분). 단 provenance_hash 활용 강화 | optional |

### 10.3 진행 중/미착수 트랙 v3 재분류

| Track ID (v1.0) | 상태 | v3 변경 | 조치 |
|---|---|---|---|
| COMMON-D (bulkflow_likelihood) | 미착수 | 변경 없음 | v1.0 기획대로 진행 |
| COMMON-E (posterior_summary) | 미착수 | 변경 없음 | v1.0 기획대로 |
| COMMON-F (mock_calibration) | 미착수 | 변경 없음 + **PATCH-02 트리거** | v1.0 기획대로, 완료 시 PATCH-02 실행 |
| HTT-STAB | 미착수 | 변경 없음 | v1.0 기획대로 |
| HTT-NULL | 미착수 | 변경 없음 | v1.0 기획대로 |
| TSC-02 ~ TSC-06 | 미착수 | **TSC-06 (htt_bridge)**에 v3 G19 주의사항 추가 (§14.3 참조) | v1.0 기획대로 + G19 가드 |
| DOS-A13 | 미착수 | **v3 §11.10.1 그대로 유효** — 15-model dossier | v1.0 기획대로 |
| DOS-A14 | 미착수 | 변경 없음 | v1.0 기획대로 |
| MANU-CH06 | 미착수 | v3 §11.14.7 — ch06 목표 라인 `~2,700 → ~3,000` (MIO pipeline subsection 추가) | v1.0 기획대로 + MIO 서브섹션 |
| REG-01 | 진행 중 (AM/AJ/AH 대응 3건 완료) | **추가 3건** v3 G19 enforcement (§14.2) | REG-01 확장 → **REG-02** 트랙으로 승계 |

---

## §11. v3 신규 트랙 — Interface Contracts & G19 인프라

### 11.1 CONTRACTS-01 — `workspace/contracts/` 디렉터리 및 3종 계약 객체

**우선순위**: P0 (MIO 구현의 전제조건, Phase J 전 필수)
**예상 L**: ~450 (3 파일 + 테스트)
**독립성**: 완전 독립 — bass_py 세션과 무충돌
**블로킹**: 없음 (DOC-03 spec 확정 상태)

**대상**:

```text
bass_py/workspace/                     # 신규 디렉터리 (bass_py 내, src/와 병렬)
├── __init__.py
└── contracts/
    ├── __init__.py
    ├── htt_forward_output.py     (~150 L)
    ├── mio_certificate.py        (~180 L)
    ├── atlas_entry.py            (~120 L)
    └── tests/
        ├── test_htt_forward_output.py
        ├── test_mio_certificate.py
        ├── test_atlas_entry.py
        └── test_g19_enforcement.py   (§11.2와 공유)
```

**각 파일 내용 (v3 §4.5.2 + §10.2 기반)**:

- `htt_forward_output.py` — `HttForwardOutput` frozen dataclass. **Hard rule** (docstring): "observational data로 해석 금지; adequacy 자체 certificate로 취급 금지"
- `mio_certificate.py` — v3 §4.5.2.1 그대로. `as_posterior_bundle()` → `NotImplementedError` 의도적 구현. **Hard rule**: "posterior 아님; truth certificate 아님; HTT evidence와 합산 금지"
- `atlas_entry.py` — `AtlasEntry` (K_ℓ atlas lookup). **Hard rule**: "empirical data로 취급 금지"

**테스트**:
- `test_miocertificate_no_posterior_access` — `.as_posterior_bundle()` 호출 시 `NotImplementedError`
- `test_miocertificate_schema_frozen` — schema hash anti-regression
- `test_htt_forward_output_invariants` — 필드 타입/범위
- `test_atlas_entry_readonly` — 수정 시도 시 `FrozenInstanceError`

**Gate**: 4 테스트 PASS + `bass_py/workspace/contracts/` import 가능 + COMMON-A의 기존 `PreferredAxis`와 공존.

**주의**: `bass_py/workspace/` 디렉터리 신설은 bass_py 세션의 `bass/` 와 완전 분리이므로 충돌 없음. `src/common/contracts.py`는 그대로 유지 — 두 파일은 스코프가 다르다 (`src/common/` = ZoA/bulk-flow 내부 DTO; `workspace/contracts/` = 패키지 간 interface).

### 11.2 G19-ENFORCE-01 — Hard separation CI/lint/test 인프라

**우선순위**: P0 (CONTRACTS-01과 동시 실행 가능)
**예상 L**: ~200
**독립성**: 완전 독립
**블로킹**: CONTRACTS-01 필요 (import 대상)

**대상**:
- `bass_py/workspace/contracts/tests/test_g19_enforcement.py` (신규)
- `bass_py/pyproject.toml` 또는 `.claude/hooks/`에 lint rule 추가 (사용자 승인 필요)

**v3 §10.2bis 표 그대로 구현**:

| 검사 항목 | 구현 | 실패 시 |
|---|---|---|
| `MioCertificate.as_posterior_bundle()` 호출 | runtime | `NotImplementedError` (CONTRACTS-01에서 구현) |
| HTT likelihood가 `MioCertificate`를 직접 ingest | type-check + test | `TypeError` |
| `MioCertificate.evidence_score + HttLog BZ` 와 같은 합산 | grep lint (CI) | CI fail |
| MIO가 "posterior" 필드를 가진 output 생성 | module-level guard | `ValueError: MIO cannot generate posteriors` |

**신규 테스트**:
- `test_g19_no_scalar_sum_of_mio_and_htt` — text-based grep across codebase
- `test_g19_htt_cannot_ingest_miocertificate_as_likelihood` — runtime
- `test_g19_mio_output_has_no_posterior_field` — introspection

**Gate**: 3 enforcement tests PASS + grep pattern scan 로그 생성.

**하드 룰 (memory feedback 저장 권장)**: 본 계획에서 MIO 관련 코드를 작성할 때는 **항상 G19 enforcement test가 green인지 확인 후 커밋**.

### 11.3 CONTRACTS-02 — HTT↔MIO cross-check 프로토콜 스펙

**우선순위**: P1
**예상 L**: ~150 (문서 + 서명)
**독립성**: 완전 독립 (문서 중심)
**블로킹**: CONTRACTS-01 완료 필요

**산출물**:
- `docs/design/G19_cross_check_protocol.md` — v3 §4.5.4 + §10.2bis 기반 프로토콜 문서
- 서명 initial sketch: `bass_py/mio/interface/htt_cross_check.py` (빈 껍데기, `NotImplementedError` 플레이스홀더)

**Gate**: 문서 review + 빈 껍데기 import 가능.

---

## §12. v3 신규 트랙 — MIO Phase J 독립 실행 (HJ-02 단독 선행)

### 12.1 트랙 카탈로그 (MIO 전용)

| Track ID | 이름 | 우선 | 예상 L | 의존 | 상위 §참조 |
|---|---|---|---|---|---|
| **MIO-BOOT-01** | `bass_py/mio/` 패키지 스캐폴딩 + `__init__.py` + pyproject 등록 | **P0** | ~100 | CONTRACTS-01 | v3 §1.4.2 |
| **MIO-HJ-02a** | `mio.coherence.directional` — 5-probe resultant + Fisher isotropy p-value | **P0** | ~350 | MIO-BOOT-01 | v3 §4.5.3.2, HJ-02 |
| **MIO-HJ-02b** | `mio.coherence.redshift_binned` — z-bin별 probe direction + drift rate | P1 | ~250 | MIO-HJ-02a | v3 §1.4.2, HJ-02b |
| **MIO-HJ-06a** | `mio.interface.mio_certificate` — `MioCertificate` generator (스펙만, 내용은 각 HJ 모듈에서 주입) | P0 | ~200 | CONTRACTS-01 | v3 §4.5.3.5 |
| **MIO-BRIDGES-01** | PR13AM을 `bass_py/mio/bridges/` 하위로 심볼릭 재배치 + 소유권 docstring | P1 | +30 | MIO-BOOT-01 | PATCH-01 해결 |
| **MIO-HJ-05a-lite** | `mio.diagnostics.masked_sky_caveats` — sky coverage tracking | P1 | ~250 | MIO-BOOT-01 | v3 §1.4.2 HJ-05 |
| **MIO-HJ-07** | PR13AM 외 MIO bridge 모듈 stub (2026 이후 확장용) | P2 | ~100 | MIO-BOOT-01 | v3 §1.4.2 |

**bass_py 의존 트랙 (본 계획 밖, bass_py 세션 진행 후 실행 가능)**:
- HJ-01 shear_nonparametric (bass_py W10-02 K_ℓ atlas 필요)
- HJ-01 biposh_inversion (W11-02 필요)
- HJ-03 flrw_tension (W10-02 필요)
- HJ-03 xc_estimator (tsc.diagnostics 의존 — TSC-02 완료 후)
- HJ-04 evidence_anatomy (HTT Phase F 완료 필요)
- HJ-04 redshift_tomography (HTT posterior 필요)
- HJ-05a-full predictive_residuals (HTT posterior 필요)

### 12.2 MIO-BOOT-01 — 패키지 스캐폴딩

**대상**:

```text
bass_py/mio/                        # 신규 패키지
├── __init__.py                     # __version__, 공개 API
├── coherence/
│   ├── __init__.py
│   └── directional.py              # HJ-02a (§12.3)
├── extraction/                     # 빈 __init__.py (후속 단계)
├── tension/                        # 빈 __init__.py
├── decomposition/                  # 빈 __init__.py
├── diagnostics/                    # 빈 __init__.py
├── interface/
│   ├── __init__.py
│   └── mio_certificate.py          # HJ-06a (§12.4)
├── bridges/                        # 빈 __init__.py (PR13AM 재배치 대기)
└── tests/
    ├── __init__.py
    └── test_boot.py                # package import + 버전 테스트
```

**pyproject.toml 변경**: `bass_py/pyproject.toml` 에 `mio` 하위 패키지 등록 (또는 editable install 확인). 이 편집은 **bass_py 세션과 충돌 가능성 있음** — 별도 commit + 짧은 충돌 창 관리.

**Gate**: `import bass_py.mio` 성공 (또는 `import mio` — 기존 패키지 구조 규칙과 일치).

**주의**: `legacy/mio/` 와 혼동 금지. 새 `bass_py/mio/` 는 **v3 Model-Independent Observatory** 버전. `legacy/mio/` 는 v2 "certification engine" 오해 버전 보존용.

### 12.3 MIO-HJ-02a — `coherence.directional`

**왜 이 트랙이 최우선인가**: v3 §16.2 병렬 표에서 유일하게 **"완전 독립 — K_ℓ, HTT posterior 불필요"** 로 표기됨. 데이터 probe 5종 (CMB / CatWISE / Radio / CF4++ / BiPoSH)만 hardcoded 있으면 실행 가능.

**대상**: `bass_py/mio/coherence/directional.py` (~350 L)

**핵심 API**:

```python
from dataclasses import dataclass
from typing import List, Tuple

@dataclass(frozen=True)
class DirectionalProbe:
    name: str                # 'CMB' | 'CatWISE' | 'Radio' | 'CF4pp' | 'BiPoSH'
    l_deg: float
    b_deg: float
    sigma_cone_deg: float    # 1-sigma uncertainty cone half-angle
    weight: float = 1.0      # measurement inverse-variance

def resultant_vector(probes: List[DirectionalProbe]) -> Tuple[float, float, float]:
    """Unit-vector weighted sum → (l_best, b_best, R_resultant)."""
    ...

def isotropy_pvalue(probes: List[DirectionalProbe],
                    n_mock: int = 10_000,
                    rng=None) -> float:
    """Fisher distribution test (or permutation). p-value that probes are drawn
    from isotropic distribution, same σ_cone each. p < 0.01 indicates alignment."""
    ...

def pairwise_separations(probes: List[DirectionalProbe]) -> np.ndarray:
    """5x5 matrix of angular separations in degrees + significance vs cone sums."""
    ...

def coherence_chi2(probes: List[DirectionalProbe]) -> float:
    """χ² test for 'all probes point to common axis'."""
    ...

def to_mio_certificate(probes, p_iso, resultant, config_hash) -> 'MioCertificate':
    """Package results as a MioCertificate (from workspace.contracts)."""
    ...
```

**테스트**:
- `test_isotropic_null_pvalue_gt_0p05` — 10k isotropic mocks, no false detection
- `test_aligned_probes_pvalue_lt_0p01` — 5 probes within 20° → detection
- `test_resultant_vector_antipodal_probes_R_zero` — 정반대 probe → R=0
- `test_pairwise_separations_cmb_catwise_literature_ge_28deg` — CMB-CatWISE separation ≈ 28° (Secrest+2020)
- `test_to_mio_certificate_has_no_posterior_field` — G19

**Gate**: 5 테스트 PASS + artifact `mio_directional_coherence.json` 생성 가능 + `fig_resultant_vector_5probes` (F135) 플레이스홀더 스크립트.

**SSOT probe 위치 (hardcoded 초안)**:
```python
STANDARD_PROBES = [
    DirectionalProbe('CMB',     l_deg=264.021, b_deg=48.253, sigma_cone_deg=0.5, ...),  # Planck 2018
    DirectionalProbe('CatWISE', l_deg=238.2,   b_deg=28.8,   sigma_cone_deg=6.0, ...),  # Secrest+2020
    DirectionalProbe('Radio',   l_deg=251.0,   b_deg=38.0,   sigma_cone_deg=10.0, ...), # NVSS+RACS
    DirectionalProbe('CF4pp',   l_deg=289.0,   b_deg=30.0,   sigma_cone_deg=15.0, ...), # Tully+2023
    DirectionalProbe('BiPoSH',  l_deg=220.0,   b_deg=65.0,   sigma_cone_deg=20.0, ...), # preliminary
]
```

문헌 값은 해당 트랙 수행 시 정확한 논문 인용으로 update. SSOT constant는 `bass_py/mio/coherence/probes.py` (신규) 또는 `workspace/contracts/` 공통 상수로.

### 12.4 MIO-HJ-06a — `MioCertificate` generator API

**대상**: `bass_py/mio/interface/mio_certificate.py` (~200 L)

**역할**: `workspace/contracts/mio_certificate.py` 에서 정의된 `MioCertificate` dataclass를 **생성**하는 편의 API. 각 HJ 모듈이 자신의 결과를 이 generator에 넘기면 `MioCertificate` 인스턴스를 받는다.

**핵심 함수**:
```python
def build_mio_certificate(
    report_type: str,
    probe_name: str,
    channel: str,
    departure_variables: dict,
    adequacy_indicators: dict,
    consistency_metrics: dict,
    *,
    domain_caveats: list,
    reduction_status: str,
    generated_by: str,
    input_data_hashes: list,
    htt_cross_check_suggested: dict | None = None,
) -> MioCertificate:
    """validate + populate provenance → immutable MioCertificate."""
    ...
```

- `git_commit` + `config_hash` 자동 획득 (bass_py의 `runtime.provenance` 재사용)
- 호출 측에서 `posterior` 키워드가 포함된 필드 주입 시 `ValueError: MIO cannot generate posteriors`

**테스트**:
- `test_build_certificate_frozen`
- `test_build_rejects_posterior_keyword`
- `test_provenance_auto_populated` — git_commit 필드 비어있지 않음

**Gate**: 3 테스트 PASS + MIO-HJ-02a가 이 generator를 소비하는 integration test.

### 12.5 MIO-BRIDGES-01 — PR13AM 심볼릭 재배치 (PATCH-01 해결)

**목적**: v3 §1.4.1 — "PR13AM은 MIO의 legitimate bridge". 현재 `bass_py/htt/htt/PR13AM_te_sign_d1d3_bridge.py` 에 있는 파일을 **물리적으로 유지**하되 semantic 소유를 MIO로 이전.

**옵션 비교**:

| 옵션 | 장 | 단 |
|---|---|---|
| A. 파일 그대로 두고 re-export만 | 기존 테스트/import 경로 불변 | semantic 모호성 잔존 |
| B. 파일 이동 (`htt/htt/` → `mio/bridges/`) | semantic 깔끔 | import 경로 전체 업데이트, 기존 테스트 대량 수정 |
| C. 이동 + `bass_py/htt/htt/PR13AM_*.py`에 deprecation shim | 양쪽 호환 | 이중 유지 |

**권장**: **옵션 A + docstring/`__mio_owned__` 태그**. 옵션 B/C는 Phase H 이후 manuscript submission 전 cleanup 단계에서 검토.

**작업**:
1. `PR13AM_te_sign_d1d3_bridge.py` 최상단에 module-level 태그:
   ```python
   __mio_owned__ = True
   __mio_rationale__ = (
       "TE-sign D1/D3 pattern is a model-independent diagnostic bridge "
       "per v3 §1.4.1. Physical location retained in htt/ for import "
       "stability; semantic ownership is MIO."
   )
   ```
2. 생성되는 artifact의 파일명에 `mio_` prefix 강제 (기존 `pr13am_...` → `mio_pr13am_te_sign_v1.json`). §14.1 참조.
3. `bass_py/mio/bridges/__init__.py` 에 re-export:
   ```python
   from bass_py.htt.htt.PR13AM_te_sign_d1d3_bridge import *  # noqa
   ```
4. 테스트 `test_pr13am_mio_ownership_tag`: `__mio_owned__ is True`

**Gate**: 기존 `test_PR13AM_production_gate.py` 무회귀 + 신규 태그 테스트 PASS + MIO 쪽 import 가능.

### 12.6 MIO-HJ-05a-lite — `masked_sky_caveats` (경량 선행)

**왜 선행하는가**: Sky coverage / mask propagation 추적은 **데이터만 필요** (HTT posterior 불필요). MIO certificate 의 `domain_caveats` 필드를 채우는 핵심 소스.

**대상**: `bass_py/mio/diagnostics/masked_sky_caveats.py` (~250 L)

**API**:
```python
@dataclass(frozen=True)
class SkyCoverageReport:
    nside: int
    f_sky_effective: float                  # masked / total
    zoa_half_angle_deg: float | None
    ecliptic_pole_gap_deg: float | None
    mask_provenance: str                    # e.g. 'Planck_SMICA_common_mask_2018'
    caveats: list[str]                      # human-readable

def build_report(mask_pix, nside, zoa_cfg, provenance) -> SkyCoverageReport: ...
def as_caveats_list(report) -> list[str]: ...  # MioCertificate.domain_caveats용
```

**테스트**:
- `test_f_sky_consistency` — `sum(mask) / n_pix`
- `test_zoa_applied_then_f_sky_less_than_one`

**Gate**: 2 테스트 PASS.

---

## §13. v3 신규 트랙 — Manuscript 확장 (ch11 재구성 + ch12 신설)

### 13.1 MANU-CH11-REDESIGN — v3 ch11 재구성

**우선순위**: P1
**예상 L**: ~500 추가 (기존 596 → ~1,100)
**독립성**: 완전 독립 (manuscript 작업)
**블로킹**: CONTRACTS-01 완료 (schema 인용 필요)

**v3 §11.14.2 기반 신규 섹션**:

| 신규 § | 내용 |
|---|---|
| §11.X "`MioCertificate` semantic rule" | DOC-03 III-4.3~4. MioCertificate는 진단 보고서, truth certificate 아님. **4회 이상 명시** (v3 §15.2 정성 지표) |
| §11.X "Hard separation (G19) 실행" | v3 §10.2bis 표 + CI/lint/test 인프라 설명 |
| §11.X "Epistemic control 분산 소유" | v3 §0.1bis 표 + 각 모듈 self-gating 매커니즘 |

**삭제 대상 (v2 오해 잔존 시)**: "MIO as certification engine" 등 v2 문구 전수 검색 후 제거.

**Gate**: banned-vocab scan + "truth certificate" 언급 ≥ 4 + reviewer 1순위 체크리스트 통과.

### 13.2 MANU-CH12-NEW — 신규 ch12 "MIO Observatory Results"

**우선순위**: P1 (Phase H 상위 작업이지만 구조 설계는 지금 가능)
**예상 L**: ~1,750 (full chapter)
**독립성**: 완전 독립
**블로킹**: MIO Phase J 모듈 진행 + HJ-02a 최소 결과 필요 (§12.1~12.2 초안)

**v3 §11.14.1 그대로**:

| § | 분량 | 내용 |
|---|---|---|
| §12.0 | ~50 | MIO 철학 |
| §12.1 Non-parametric shear extraction | ~250 | Σ²_MIO(ℓ), ℓ-independence, STF |
| §12.2 Cross-channel directional coherence | ~200 | **HJ-02a 결과 선행 배치 가능** |
| §12.3 FLRW tension + x_C | ~250 | PPP, x_C |
| §12.4 Evidence anatomy | ~300 | ch/z/param decomposition |
| §12.5 Predictive diagnostics | ~250 | residual atlas |
| §12.6 HTT ↔ MIO cross-validation | ~200 | G19 enforcement 결과 |
| §12.7 MIO scope와 한계 | ~100 | truth certificate 아님 재강조 |
| §12.8 MIO 결과와 HTT 결과 비교 요약 | ~150 | Σ²_MIO vs Σ²_HTT_post (not merged) |

**선행 가능한 것**:
- §12.0 (철학 prose) — CONTRACTS-01 완료 후 즉시
- §12.2 (coherence) — MIO-HJ-02a 완료 후
- §12.6 (cross-validation 프로토콜 서술) — §11 CONTRACTS-02 완료 후
- §12.7 (scope 한계) — 즉시 가능

**후행**: §12.1, §12.3, §12.4, §12.5 는 bass_py/HTT 의존 완료 후.

**Gate**: 선행 가능 4 섹션 초안 + full chapter skeleton 리뷰.

### 13.3 DOS-A30-MIO — MIO appendix A31~A40

**우선순위**: P2
**예상 L**: ~2,950 (10 appendix)
**독립성**: 완전 독립

**v3 §11.14.6 그대로 10개 appendix**:

| Appendix | 제목 | 분량 | 선행 가능? |
|---|---|---|---|
| A31 MIO full API catalog | 400 | HJ 각 모듈 완료 후 |
| A32 `MioCertificate` schema | 300 | **CONTRACTS-01 후 즉시** |
| A33 `HttForwardOutput` + `AtlasEntry` | 250 | **CONTRACTS-01 후 즉시** |
| A34 Non-parametric Σ² 유도 | 400 | HJ-01 완료 후 |
| A35 Directional coherence 통계 | 350 | **HJ-02a 완료 후 즉시** |
| A36 FLRW PPP 유도 | 300 | HJ-03 완료 후 |
| A37 Evidence anatomy consistency theorem | 200 | Tier 3 |
| A38 HTT↔MIO cross-check protocol (G19) | 300 | **CONTRACTS-02 후 즉시** |
| A39 Per-module epistemic ownership 표 | 200 | **즉시 가능** (v3 §0.1bis 인용) |
| A40 PR13AM TE-sign D1/D3 bridge 유도 | 250 | **MIO-BRIDGES-01 후 즉시** |

**선행 대상 (P1 승격 권장)**: A32, A33, A38, A39 (모두 CONTRACTS-01/02 완료 조건으로 즉시 시작 가능).

---

## §14. v3 반영 명명 규칙 & artifact 정책

### 14.1 MIO artifact prefix 강제

**모든 MIO 생성 artifact**는 filename에 `mio_` prefix + subpackage 이름 포함 (v3 §12.2bis 마지막 줄).

| 구 prefix 후보 | v3 필수 prefix | 예시 |
|---|---|---|
| (없음) / ad-hoc | `mio_` | `mio_directional_coherence.json` |
| `pr13am_*` | **`mio_pr13am_*`** | `mio_pr13am_te_sign_v1.json` (PATCH-01 해결 일환) |
| `diag_*` / `baseline_*` / `fiducial_*` (기존 3-mode) | 그대로 유지 | — (MIO와 orthogonal) |

**Rationale**: G19 enforcement의 첫 번째 방어선은 "파일 이름부터 HTT와 구분 가능해야 함" (v3 §12.2bis).

**검증 lint**: `grep -r "mio\\." bass_py/mio/ | grep -v "mio_"` 에서 artifact 생성 call 발견 시 CI fail.

### 14.2 REG-02 — G19 enforcement regression 확장 (§5 REG-01 후속)

**§5 REG-01** (7건)은 v1.0 기준. v3에서 다음 4건 추가:

| Test | 대응 트랙 | 위치 |
|---|---|---|
| `test_miocertificate_no_posterior_access` | CONTRACTS-01 | `bass_py/workspace/contracts/tests/` |
| `test_htt_cannot_ingest_miocertificate_as_likelihood` | G19-ENFORCE-01 | ↑ |
| `test_mio_output_has_no_posterior_field` | G19-ENFORCE-01 | ↑ |
| `test_mio_artifact_filename_has_mio_prefix` | §14.1 lint | `bass_py/mio/tests/` |

**Gate**: 모든 REG-02 테스트 green + REG-01 7건 무회귀.

### 14.3 TSC-06 v3 주의사항 (G19 가드)

**§8.2 TSC-06** (tsc.integration.htt_bridge) 는 F_Bayes cross-check 트랙이지만 v3 G19 맥락에서 **cross-check만 허용, merge 금지** 원칙에 해당한다 (tsc와 htt도 별 관점의 독립 계산).

**추가 작업**:
- TSC-06 출력에 `is_cross_check=True` 태그 명시
- `tsc ↔ htt F_Bayes 단일 score 합산` 금지를 docstring으로 명시
- `test_tsc_htt_ff_cross_check_not_merged` regression

**Gate**: TSC-06 원래 gate + 상기 태그/테스트.

---

## §15. v3 기준 완료 게이트 (개정판)

§7 게이트를 다음으로 **대체**:

- [ ] **기존 §7 게이트 전부 충족** (SSOT-01, HTT-P0 4건, COMMON 7 모듈, tsc 확장, HTT 안정화, dossier, audit — 완료 또는 진행 중)
- [ ] **CONTRACTS-01** 3 파일 + 4 테스트 green
- [ ] **G19-ENFORCE-01** 3 enforcement 테스트 green + lint scan 로그 보존
- [ ] **REG-02** 4건 추가 테스트 green
- [ ] **MIO-BOOT-01** `bass_py/mio/` import 가능 + `test_boot.py` green
- [ ] **MIO-HJ-02a** 5 테스트 green + `mio_directional_coherence.json` artifact 생성 가능
- [ ] **MIO-HJ-06a** 3 테스트 green + MioCertificate generator 정상
- [ ] **MIO-BRIDGES-01** PR13AM `__mio_owned__=True` 태그 + `mio.bridges` re-export 작동
- [ ] **MIO-HJ-05a-lite** masked_sky_caveats 2 테스트 green
- [ ] **PATCH-01** 해결 (MIO-BRIDGES-01 완료로 충족)
- [ ] **PATCH-02** 해결 (COMMON-F 완료 + 실제 bias correction 로직 주입)
- [ ] **PATCH-03** 해결 (CONTRACTS-01 완료로 충족)
- [ ] **PATCH-04** 해결 (`legacy/mio/` 에 REDME.md — "이 디렉터리는 v2 오해 버전; 활성 코드는 `bass_py/mio/`" 추가)
- [ ] **MANU-CH11-REDESIGN** — "truth certificate" 재강조 ≥ 4회 + banned-vocab scan 0
- [ ] **MANU-CH12-NEW** — §12.0 + §12.2 + §12.6 + §12.7 4 섹션 초안 완료 (전체는 bass_py/HTT 의존 후)
- [ ] **DOS-A30-MIO** A32 + A33 + A38 + A39 + A35 + A40 초안 완료 (즉시 가능한 6개)
- [ ] **§14.1** 모든 MIO artifact 파일명 `mio_` prefix 준수 — lint 통과
- [ ] **Full regression** bass + tsc + htt + **mio** 합계 ≥ **2,800** (v3 §15.1 기준) — 현 단계에서는 **MIO 기여분 ≥ 15건** 중간 목표
- [ ] **Phase-boundary audit** (`docs/audits/AUDIT_PROMPT.md`) 완료 + `docs/audits/AUDIT_PHASE_MIO_INTEGRATION_2026-04-XX.md` 기록

---

## §16. v3 즉시 실행 추천 순서 (§6 확장)

§6 Week 4 이후 계속:

### Week 5 (2026-05-18 ~ 05-24)

1. **PATCH-04** (Day 1) — `legacy/mio/README.md` 주의사항 추가
2. **CONTRACTS-01** (Day 1–3) — 3 frozen dataclass + 4 테스트
3. **G19-ENFORCE-01** (Day 3–4) — enforcement tests
4. **REG-02** (Day 4) — 4건 regression
5. **MIO-BOOT-01** (Day 5) — 패키지 스캐폴드
6. **DOS-A30-MIO** A32 + A33 + A39 (Day 6–7) — schema appendix 초안

### Week 6

7. **MIO-HJ-06a** (Day 1–2) — MioCertificate generator
8. **MIO-HJ-02a** (Day 2–5) — directional coherence (핵심 선행 MIO 모듈)
9. **MIO-BRIDGES-01** (Day 5) — PR13AM 태그 + re-export (PATCH-01 해결)
10. **MIO-HJ-05a-lite** (Day 6–7) — masked_sky_caveats

### Week 7

11. **COMMON-D/E/F** 완료 (v1.0 로드맵)
12. **PATCH-02** — PR13AH 4-summary 중 mock_calibrated_summary 실제 로직 주입
13. **CONTRACTS-02** — cross-check 프로토콜 문서
14. **DOS-A30-MIO** A35 + A38 + A40 초안

### Week 8

15. **MANU-CH11-REDESIGN** — v3 3섹션 신규 + banned-vocab scan
16. **MANU-CH12-NEW** §12.0 / §12.2 / §12.6 / §12.7 초안
17. **Full regression audit** + Phase-boundary audit 수행 → `AUDIT_PHASE_MIO_INTEGRATION_*.md`

### Week 9 이후

- HTT-STAB / HTT-NULL / TSC-02~06 (원래 §6 후반 계획)
- DOS-A13, DOS-A14 (기존 v1.0 계획)
- MANU-CH06 (bass_py freeze 후)
- MIO-HJ-07 (P2 bridge stubs)

---

## §17. v3 위임 범위 업데이트 (§8 대체)

### 17.1 본 계획이 **소유**하는 작업 (independent)

**§1 v1.0 카탈로그** + **§11~§14 v3 신규** 전체. 요약:

| 영역 | 경로 |
|---|---|
| HTT P0 patches (완료) | `bass_py/htt/htt/PR13{AH,AJ,AM}*.py` + tests |
| HTT stabilization | `bass_py/htt/figures/`, `bass_py/htt/nulls/` (tests/conftest 정리) |
| `src/common/` (7 모듈) | `bass_py/src/common/*.py` + tests |
| `workspace/contracts/` (3 인터페이스) | `bass_py/workspace/contracts/*.py` |
| **`bass_py/mio/` (v3 신규 패키지)** | `bass_py/mio/*` — coherence, interface, bridges, diagnostics 하위 |
| tsc 확장 | `bass_py/tsc/{admissibility,diagnostics,charts,integration}/` |
| Manuscript | `project/`, `docs/design/`, `docs/dossier/` 하위 |
| Audit 문서 | `docs/audits/*.md` |

### 17.2 bass_py 세션 **전담** (본 계획 제외)

§8 그대로 유지:
- W10-02 CAMB V-gate (`bass.spectrum`)
- W11-01/02/03 direction-dependent C_ℓ, BiPoSH, Bianchi V2 gate (`bass.los`)
- W12-01/02 W_R window, frame-attribution bias (`bass.validation`, `bass.tilt`)
- W13-01/02 Dynamical tilt source, β → D_2 transfer (`bass.transport`, `bass.spectrum`)
- W14-01 3-signature discriminator (신규 또는 `bass.spectrum`)
- W15-01/02/03 (`src/common/` 의존 완료 후 bass_py 측 소비)
- LB-N PSTF hierarchy 후속
- `plots/physics_gallery/` per-phase refresh

### 17.3 bass_py 완료를 **기다리는** MIO 트랙 (본 계획 안이지만 선행 불가)

| MIO 트랙 | 기다리는 bass_py 이벤트 |
|---|---|
| MIO HJ-01 shear_nonparametric | bass_py W10-02 완료 + K_ℓ atlas 공개 |
| MIO HJ-01 biposh_inversion | bass_py W11-02 완료 |
| MIO HJ-03 flrw_tension | bass_py W10-02 완료 |
| MIO HJ-03 xc_estimator | **tsc TSC-02 완료** (본 계획 내부 의존) |
| MIO HJ-04 evidence_anatomy | HTT Phase F (15-model evidence 수렴) |
| MIO HJ-04 redshift_tomography | HTT posterior 완료 |
| MIO HJ-05a-full predictive_residuals | HTT 15-model posteriors |
| MIO `htt_cross_check` 본격 구현 | MIO HJ-01 + HJ-03 + HTT posterior 모두 |

본 계획 Week 5~9 범위에서는 **위 의존이 없는 MIO 모듈만 착수** — HJ-02a, HJ-05a-lite, 인프라 (boot/contracts/certificate/bridges/scope 문서).

---

# PART III — Week 5+ 실태 기반 재조정 (2026-04-19 코드 인스펙션)

**기준 커밋**: `115f505 LB-5: unified Lowell-Bianchi integrator + TCA dispatch`
**기준 세션 진도**: 독립 트랙 Week 1~4 착륙 (커밋 `94d2191`, `0fdf477`, `e08e418`), bass_py 세션 LB-0→LB-5.
**본 PART 목적**: 코드 수준 실태조사 결과를 Week 5+ 실행 계획에 반영. §1~§17 불변 유지, §18 이후 신규 섹션으로 이어 붙임.

---

## §18. 코드 인스펙션 결과 요약

### 18.1 Week 4 종료 시점의 실 상태 (파일 단위)

| 영역 | 상태 | 증거 / 메트릭 |
|---|---|---|
| `bass_py/src/common/` | **완성** 7 모듈 | `sky_geometry.py` 125 L, `contracts.py` 176 L, `healpix_selection.py` 308 L, `bulkflow_estimator.py` 384 L, `bulkflow_likelihood.py` 287 L, `posterior_summary.py` 322 L, `mock_calibration.py` 457 L. 합계 **~2,060 L + 테스트 ~1,375 L** |
| `bass_py/htt/htt/PR13AH.py` | **placeholder 남음** | `mock_calibrated_summary` 여전히 `selection_aware_summary` 복제 + `calibration_pending=True` (§2.4 PATCH-02 트리거 발화 — COMMON-F 존재에도 미해결) |
| `bass_py/htt/htt/PR13AJ.py` | gate OK, body 미구현 | `restore_full_a2m()` → `NotImplementedError` (a_{2m} rotation logic 미착륙) |
| `bass_py/htt/htt/PR13AM.py` | gate OK, MIO 태그 미적용 | `__mio_owned__` 플래그 부재, artifact prefix 미강제 |
| `bass_py/htt/tests/` | **195 passed, 1 failed, 23 skipped** | RED: `test_to_mio_builds_bundle` (workspace/contracts 미존재). Skip 23 = plot_style/bounds/mio/obs_defaults |
| `bass_py/tsc/` (admissibility + diagnostics + charts) | **615 passed** | TSC-01 + TSC-02 + TSC-04 완료. filling_fraction 22 tests green |
| `bass_py/tsc/integration/` | **부재** | TSC-06 htt_bridge 미착수 |
| `bass_py/tsc/charts/michaelis_menten_export.py` | **부재** | TSC-05 미착수 |
| `bass_py/tsc/diagnostics/three_bound_hierarchy.py` | **부재** | TSC-03 미착수 |
| `project/00_manuscript/ch03_framework.tex` | **4,101 L** (v3 §11.3 목표 ~4,900 L의 84%) | Clarkson–Maartens `sec:CM-consistency` / `prop:sphere-mean-unbiased` / `sec:selection-aware-likelihood` / `sec:theta4-bridge` 모두 존재 |
| `docs/dossier/A13_*` | **3/15** (template + FLRW + FLRW_tilt) | 13 모델 잔여 |
| `docs/dossier/A14_*` | **5/5 완료** | N1~N5 모두 커밋 |
| `docs/audits/` | **9 audits** (LB-1~5 + IND_TRACKS_W1W2/W3/W4 + 2 topical) | |
| `bass_py/workspace/` | **미존재** | v1.1 CONTRACTS-01 미착수 — RED 테스트 1건의 근본원인 |
| `bass_py/mio/` | **미존재** | v1.1 §12 MIO-BOOT-01 미착수 |

### 18.2 즉시 해결이 필요한 RED/오염

| ID | 문제 | 파급 | 진단 |
|---|---|---|---|
| **RED-01** | `test_to_mio_builds_bundle` FAIL — `from contracts.htt_to_mio import PosteriorExportBundle` | F3 carry-forward. Week 4 audit에서 `pre-existing failure`로 기록. HTT 전체 테스트 그린 차단 | `htt/htt/integration/to_mio.py:43` 에 `sys.path.insert(0, ..../workspace)` + `from contracts.htt_to_mio` — **workspace/ 디렉터리 자체가 repo에 없음** |
| **SKIP-17** | 17개 figure script: `No module named 'plot_style'` | HTT 27 figure 중 17개 smoke test 건너뜀 | `bass_py/htt/htt/core/plot_style.py` 존재 → 패키지 import path 해석 실패 (sys.path 조작 필요) |
| **SKIP-02a** | 2 figures: `No module named 'bounds'` | ↑ 동일 원인 — `core.bounds` 가 아닌 top-level `bounds` import |
| **SKIP-02b** | 2 figures: `No module named 'mio'` | MIO 패키지 미생성 (v1.1 §12 MIO-BOOT-01 의존) |
| **SKIP-02c** | 2 tests: `obs_defaults.json not found` | fixture 파일 누락 |
| **AMBIG-01** | `legacy/README.md` 가 "Bianchi Defect Framework" 타이틀로 **활성 코드처럼** 보임 | v3 §1.4.1 "legacy=v2 오해 버전" 원칙 위배 가능성 | v1.1 PATCH-04 미착수 |
| **PLACEHOLDER-01** | `PR13AH.mock_calibrated_summary` = `selection_aware_summary` 복제 + `calibration_pending=True` | 4-summary 구조 integrity 깨짐 (v3 §6.3 요구사항 위반) | COMMON-F `run_zoa_null_mocks` + `apply_bias_correction` 존재 → 배선만 필요 |
| **SEMANTIC-01** | `PR13AM.__mio_owned__` 미태그 + 생성 artifact 이름 `mio_` prefix 미강제 | v3 §1.4.1 + §12.2bis G19 1차 방어선 미작동 | v1.1 PATCH-01 (MIO-BRIDGES-01) 미실행 |

### 18.3 누락된 선행조건 (Week 5 이전에 풀어야 할 의존)

1. **`workspace/contracts/` 디렉터리** — v1.1 CONTRACTS-01 가 Week 5로 밀린 것이 실은 **F3 RED의 유일한 원인**. Week 5 Day 1 최우선.
2. **`PosteriorExportBundle` 최소 스펙** — `htt/htt/integration/to_mio.py` 가 현 코드에서 호출하는 필드 집합 (`x_median`, `ln_B_total`, …) 역추적 필요.
3. **HTT 27 figure script import 정책** — `core/plot_style.py`, `core/bounds.py` 를 top-level 처럼 쓰기 위한 `conftest.py` 또는 `__init__.py` 수정.

---

## §19. Week 5+ 신규 트랙 (인스펙션 기반)

v1.1 §11~§14 트랙 위에 **실태 대응용 신규 트랙 7종**을 추가한다.

| Track ID | 이름 | 우선 | 예상 L | 해결 대상 |
|---|---|---|---|---|
| **WS-BOOT-01** | `bass_py/workspace/` + `contracts/htt_to_mio.py` 최소 착륙 | **P0 (Day 1 blocker)** | ~200 | RED-01 해소 |
| **HTT-FIG-SHIM** | 27 figure script import path 정리 — `conftest.py` + top-level re-export | **P1** | ~80 | SKIP-17, SKIP-02a |
| **HTT-OBS-FIXTURE** | `obs_defaults.json` 최소 fixture 생성 | P1 | ~150 (JSON) | SKIP-02c |
| **LEGACY-README** | `legacy/README.md` 경고 추가 — "v2 오해 버전, 비활성" | P1 | ~50 | AMBIG-01 (v1.1 PATCH-04) |
| **PR13AH-v2-WIRE** | `mock_calibrated_summary` 실제 bias 연결 (COMMON-F 소비) | **P0 (PATCH-02 소멸)** | ~80 (패치) | PLACEHOLDER-01 |
| **PR13AM-MIO-TAG** | `__mio_owned__` + artifact `mio_` prefix helper | **P1 (PATCH-01 소멸)** | ~40 (패치) | SEMANTIC-01 |
| **FIG-MIO-SKIP-GATE** | figure smoke test의 `mio` skip을 MIO-BOOT-01 착륙 후 자동 활성 | P2 | ~20 | SKIP-02b |

### 19.1 WS-BOOT-01 — workspace/contracts/ 최소 착륙 (RED-01 해결)

**Day 1 우선순위 최상**. F3 RED가 W5 착수 전체를 막고 있으므로 본 트랙을 맨 앞으로.

**대상**:

```text
bass_py/workspace/                   # 신규 디렉터리 (bass_py 세션 점유 영역 외부)
├── __init__.py                      # 비어있음 OK
└── contracts/
    ├── __init__.py
    ├── htt_to_mio.py                # ~120 L — PosteriorExportBundle (아래)
    ├── htt_forward_output.py        # v1.1 §11.1 CONTRACTS-01 최소 skeleton
    ├── mio_certificate.py           # ↑
    ├── atlas_entry.py               # ↑
    └── tests/
        ├── __init__.py
        ├── test_htt_to_mio_roundtrip.py     # RED-01 유발 테스트의 counterpart
        ├── test_miocertificate_frozen.py    # v1.1 §11.1 규정
        ├── test_mio_no_posterior.py         # v1.1 §11.2 G19-ENFORCE-01
        └── test_htt_forward_output.py
```

**`htt_to_mio.PosteriorExportBundle` 최소 스펙** (`htt/htt/integration/to_mio.py` 역추적 기반):

```python
from dataclasses import dataclass, field
from typing import Mapping

@dataclass(frozen=True)
class PosteriorExportBundle:
    """HTT → MIO 비교용 posterior summary (G19: cross-check only, not merge)."""
    model: str
    x_median: float
    x_hpd_68: tuple[float, float]
    x_hpd_95: tuple[float, float]
    Q_median: float
    Q_hpd_68: tuple[float, float]
    Pi_median: float
    Pi_hpd_68: tuple[float, float]
    ln_B_total: float
    model_evidences: Mapping[str, float] = field(default_factory=dict)
    filling_fraction_summary: Mapping[str, float] = field(default_factory=dict)
    is_cross_check_only: bool = True

    def __post_init__(self):
        if not self.is_cross_check_only:
            raise ValueError(
                "PosteriorExportBundle must be cross-check only (G19). "
                "Cannot be merged into MIO evidence score."
            )
```

**`htt/htt/integration/to_mio.py` 동반 수정**:
- `sys.path.insert(...)` 제거
- `from contracts.htt_to_mio` → `from workspace.contracts.htt_to_mio`
- 이 한 줄 수정은 `htt/htt/` 에 속하므로 독립 트랙 스코프 ✓ (bass_py 세션은 `bass/` 만 점유)

**테스트**:
- `test_posterior_export_bundle_frozen` — mutation 시 `FrozenInstanceError`
- `test_cross_check_only_enforced` — `is_cross_check_only=False` 생성 시 `ValueError`
- `test_to_mio_builds_bundle` (기존) PASS 복구

**Gate**: F3 RED 소멸 + htt 테스트 전체 카운트 `196 passed, 0 failed, ≤23 skipped` (MIO 의존 skip은 별도 해결).

### 19.2 HTT-FIG-SHIM — 27 figure script import 정책 정리

**상황**: `bass_py/htt/htt/core/plot_style.py` 는 존재하지만 figure script가 `import plot_style` (top-level) 로 사용하려 함. 17건 skip.

**전략** (destructive 금지, additive만):

1. `bass_py/htt/htt/figures/conftest.py` 신설:
   ```python
   import sys
   from pathlib import Path
   # figures/ 가 core/ 의 모듈을 top-level로 참조 가능하도록
   sys.path.insert(0, str(Path(__file__).parent.parent / 'core'))
   ```
2. 또는 `bass_py/htt/htt/__init__.py` 에 re-export:
   ```python
   from .core import plot_style, bounds  # top-level visibility for figures/
   ```
3. `pytest` conftest 수준에서만 적용 → 프로덕션 import 오염 없음.

**권장**: 옵션 1 (conftest.py) — 가장 작은 impact.

**테스트**:
- `test_figures_smoke.py` 재실행 → skip 17 → 0 (parse 성공)
- 기존 PR13AH/AJ/AM 테스트 무회귀

**Gate**: `pytest bass_py/htt/tests/test_figures_smoke.py` green + skip 수 17 감소.

### 19.3 HTT-OBS-FIXTURE — `obs_defaults.json` 최소 fixture

**상황**: `test_infer.py` 가 `obs_defaults.json` 을 찾지 못해 2건 skip.

**작업**:
1. `bass_py/htt/tests/fixtures/obs_defaults.json` 생성 (v3 §9.2 표 기반 SSOT 값):
   ```json
   {
     "eps1_kin": 1.2336e-3,
     "eps2": 1.476e-3,
     "eps3": 2.586e-3,
     "T_CMB_K": 2.72548,
     "Omega_m": 0.3153,
     "h": 0.6736,
     "D2_obs_uK2": 225.9,
     "D2_LCDM_uK2": 1150.0,
     "D3_obs_uK2": 936.9,
     "D3_LCDM_uK2": 1000.0,
     "eta_udot_exact": 0.08333333333333333
   }
   ```
2. `test_infer.py` 에서 상대경로 기대 → `conftest.py` 가 path resolve 지원
3. `docs/audits/SSOT_TCMB_DRIFT_2026-04-19.md` 와 값 일치 확인 (T_CMB 2.72548 htt 측 확정값)

**Gate**: `test_infer.py` skip 2 → 0.

### 19.4 PR13AH-v2-WIRE — mock_calibrated_summary 실제 연결 (PATCH-02 소멸)

**목적**: v1.1 §10.2 PATCH-02 — COMMON-F 존재하므로 placeholder 로직 제거.

**수정 대상**: `bass_py/htt/htt/PR13AH_observables_reintegration.py` 라인 121–134.

**설계**:

```python
def reintegrate_observables(catalog, sky_config, *,
                            mock_bias_correction=None):
    # ... 기존 raw/zoa/selection 계산 ...

    # Mock-calibrated: COMMON-F bias correction 주입
    if mock_bias_correction is None:
        # 하위호환: bias 미주입이면 placeholder 로 유지 (기존 동작)
        mock_summary = ChannelSummary(..., calibration_pending=True, ...)
    else:
        # V2: 실제 COMMON-F 결과 소비 — InjectedMockReport
        corrected_lb = _apply_bias_to_direction(
            selection_summary.l_deg, selection_summary.b_deg,
            bias_report=mock_bias_correction,
        )
        mock_summary = ChannelSummary(
            l_deg=corrected_lb['l_deg'],
            b_deg=corrected_lb['b_deg'],
            resultant_R=selection_summary.resultant_R,
            source="mock_calibrated",
            selection_mode="mock_calibrated",
            diagnostic_only=False,
            calibration_pending=False,              # ★ 해제
            meta={
                'n_sources': selection_summary.meta['n_sources'],
                'bias_amp_corrected_kmps': mock_bias_correction.amp_bias_fraction,
                'bias_direction_corrected_deg': mock_bias_correction.direction_bias_deg,
            },
        )
    return {...}
```

**신규 helper** (~30 L): `_apply_bias_to_direction(l, b, bias_report) -> dict`.

**테스트 갱신**:
- `test_mock_calibration_flagged_pending_until_common_f` — 현재 pass하고 있으므로 그대로 유지 (인자 None 경로)
- **신규** `test_mock_calibration_wired_when_bias_provided` — bias 주입 시 `calibration_pending is False`
- **신규** `test_mock_calibration_direction_shift_matches_bias` — regression

**Gate**: 기존 8건 test_PR13AH 무회귀 + 신규 2건 PASS.

### 19.5 PR13AM-MIO-TAG — `__mio_owned__` 태그 + artifact prefix (PATCH-01 소멸)

**목적**: v1.1 §10.2 PATCH-01 해결. 물리적 재배치는 하지 않고 semantic tag만.

**수정 대상**: `bass_py/htt/htt/PR13AM_te_sign_d1d3_bridge.py` 최상단 + 1 helper 추가.

**작업**:

```python
# PR13AM_te_sign_d1d3_bridge.py 최상단에 추가
__mio_owned__ = True
__mio_rationale__ = (
    "TE-sign D1/D3 pattern is a model-independent diagnostic bridge. "
    "Per BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN v3 §1.4.1, semantic ownership "
    "is MIO; physical location in htt/ is retained for import stability."
)

def _mio_artifact_name(stem: str, version: int = 1) -> str:
    """Enforce v3 §12.2bis naming: 'mio_' prefix + subpackage 식별자."""
    if not stem.startswith('mio_'):
        stem = f'mio_pr13am_{stem}'
    return f'{stem}_v{version}.json'
```

**테스트 신규** (`test_PR13AM_production_gate.py` 에 추가 가능):
- `test_pr13am_mio_owned_flag` — `__mio_owned__ is True`
- `test_mio_artifact_name_enforces_prefix` — `_mio_artifact_name('te_sign')` → `'mio_pr13am_te_sign_v1.json'`

**Gate**: 기존 4건 PASS + 신규 2건 PASS + grep `__mio_owned__` sweep 1 hit.

### 19.6 LEGACY-README — 경고 주석 (AMBIG-01 해결, PATCH-04 소멸)

**작업**: `legacy/README.md` 최상단에 **추가 배너 블록** 삽입 (기존 내용 보존):

```markdown
> ## ⚠️ LEGACY DIRECTORY — v2 오해 버전
>
> 본 `legacy/` 트리는 v2 연구계획에서 "MIO = certification engine" 으로
> 잘못 규정했던 시기의 스냅샷입니다. v3 (2026-04-18) 부터 MIO는
> **Model-Independent Observatory** 로 재정의되었으며, 활성 코드는
> `bass_py/mio/` (Week 6 이후 착륙 예정) 를 참조하십시오.
>
> - 활성 연구계획: [BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md](../BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md) v3
> - 본 디렉터리는 history 보존용이며 신규 import / 신규 기능 추가 금지.

---

(아래는 원본 readme 유지)
```

**Gate**: 파일 diff 확인. 본문 0 byte 삭제.

### 19.7 FIG-MIO-SKIP-GATE — MIO figure skip 자동 활성

`test_figures_smoke.py:76` 의 skip 조건이 `No module named 'mio'` 일 때 작동. MIO-BOOT-01 완료 시 자동 해제되어야 한다.

**확인 작업 (패치 아님)**: MIO-BOOT-01 완료 후 해당 skip이 실제로 0이 되는지 검증하는 regression test 1건 추가:
- `test_figures_mio_skip_should_activate_after_mio_boot` — import `bass_py.mio` 시도 + `ImportError` **아닐 것** 확인.

**Gate**: MIO-BOOT-01 완료 시점과 **동시 통과**.

---

## §20. 기 트랙 수정 지시서 (v1.1 항목 업데이트)

| v1.1 Track ID | 원래 상태 | §18 조사 후 상태 | 액션 |
|---|---|---|---|
| v1.1 §11.1 CONTRACTS-01 | 미착수 | **Day 1 urgency 확정** (RED-01 차단) | WS-BOOT-01 를 CONTRACTS-01 의 선행 최소 버전으로 Week 5 Day 1 실행. 전체 CONTRACTS-01 는 Week 5 Day 2-3 실행 |
| v1.1 §11.2 G19-ENFORCE-01 | 미착수 | 변동 없음 | Week 5 Day 3-4 |
| v1.1 §11.3 CONTRACTS-02 | 미착수 | 변동 없음 | Week 7 |
| v1.1 §12.2 MIO-BOOT-01 | 미착수 | **SKIP-02b 의존 원인** | Week 6 Day 1 — FIG-MIO-SKIP-GATE 와 cascade |
| v1.1 §12.3 MIO-HJ-02a | 미착수 | 변동 없음 | Week 6 Day 2-5 |
| v1.1 PATCH-01 | 대기 | **PR13AM-MIO-TAG 로 해결** | §19.5 Week 5 Day 5 실행 |
| v1.1 PATCH-02 | 대기 | **PR13AH-v2-WIRE 로 해결** | §19.4 Week 5 Day 6 실행 |
| v1.1 PATCH-03 | 대기 | **WS-BOOT-01 로 최소 해결**, 완전 해결은 CONTRACTS-01 후 | §19.1 Day 1 + CONTRACTS-01 Day 2-3 |
| v1.1 PATCH-04 | 대기 | **LEGACY-README 로 해결** | §19.6 Week 5 Day 7 실행 |
| v1.1 §15 완료 게이트 | 부분 기준 | **추가 기준 통합** | §22 개정 게이트 참조 |

---

## §21. Week 5~9 실행 순서 (실태 반영, §16 대체)

**본 §21은 §16을 대체한다** (§16의 Week 5~9 순서는 인스펙션 전 예상값이었으므로).

### Week 5 (2026-05-18 ~ 05-24) — "RED 해소 + v1.1 PATCH 3종 소멸"

| Day | 작업 | 트랙 | 커밋 tag 권장 |
|---|---|---|---|
| 1 (월) | **WS-BOOT-01** — workspace/ + htt_to_mio.py 최소 착륙 + to_mio.py sys.path 제거 | §19.1 | `W5D1_RED: workspace contracts skeleton` |
| 2 (화) | **CONTRACTS-01 full** — MioCertificate + AtlasEntry + HttForwardOutput 3종 완성 | v1.1 §11.1 | `W5D2: frozen MIO/HTT/Atlas contracts` |
| 3 (수) | **G19-ENFORCE-01** — 3 enforcement 테스트 + grep lint | v1.1 §11.2 | `W5D3: G19 hard-separation tests` |
| 4 (목) | **REG-02 4건** + **HTT-FIG-SHIM** | §19.2 + v1.1 §14.2 | `W5D4_STAB: figures conftest + REG-02` |
| 5 (금) | **PR13AM-MIO-TAG** (PATCH-01 소멸) + **HTT-OBS-FIXTURE** | §19.5 + §19.3 | `W5D5: PR13AM mio tag + obs defaults` |
| 6 (토) | **PR13AH-v2-WIRE** (PATCH-02 소멸) | §19.4 | `W5D6: PR13AH mock calibration wiring` |
| 7 (일) | **LEGACY-README** + **DOS-A30-MIO A32/A33/A39** 초안 | §19.6 + v1.1 §13.3 | `W5D7: legacy banner + MIO appendix drafts` |

**Week 5 게이트**:
- [ ] `pytest bass_py/htt/tests/` = **196 passed, 0 failed, ≤4 skipped** (MIO 의존 2 + bounds 2 잔존; FIG-SHIM 으로 17 해소)
- [ ] PATCH-01/02/03/04 모두 "소멸" 상태
- [ ] CONTRACTS-01 4 테스트 green + G19-ENFORCE-01 3 테스트 green

### Week 6 (2026-05-25 ~ 05-31) — "MIO 패키지 부팅 + HJ-02 선행"

| Day | 작업 | 트랙 |
|---|---|---|
| 1 (월) | **MIO-BOOT-01** — `bass_py/mio/` 스캐폴드 + pyproject 등록 + `test_boot.py` | v1.1 §12.2 |
| 1 (월) | **FIG-MIO-SKIP-GATE** 검증 — MIO-BOOT 후 skip 2 건 자동 해제 | §19.7 |
| 2 (화) | **MIO-HJ-06a** — `mio.interface.mio_certificate.build_mio_certificate` | v1.1 §12.4 |
| 3~5 | **MIO-HJ-02a** — directional coherence + 5 probes SSOT + to_mio_certificate | v1.1 §12.3 |
| 6 | **MIO-BRIDGES-01** — PR13AM re-export via `mio.bridges` | v1.1 §12.5 |
| 7 | **MIO-HJ-05a-lite** — masked_sky_caveats | v1.1 §12.6 |

**Week 6 게이트**:
- [ ] `import bass_py.mio` 성공
- [ ] HJ-02a 5 테스트 green + `mio_directional_coherence.json` artifact 생성 확인
- [ ] HTT figure skip: 2 (`bounds` 관련만 남음) — MIO 관련 2 skip 은 0으로 해소
- [ ] `MioCertificate`.as_posterior_bundle() → NotImplementedError 실행 확인

### Week 7 (2026-06-01 ~ 06-07) — "tsc 잔여 + 선행 가능 appendix"

| Day | 작업 | 트랙 |
|---|---|---|
| 1~2 | **TSC-03** — `three_bound_hierarchy.py` + htt.bounds cross-check test | §3.3 (v1.0) |
| 3 | **TSC-05** — `michaelis_menten_export.py` + Route B SSOT mirror | §4.2 (v1.0) |
| 4~5 | **TSC-06** — `tsc/integration/htt_bridge.py` (`is_cross_check=True` + G19 가드) | §4.3 (v1.0) + v1.1 §14.3 |
| 6 | **CONTRACTS-02** — G19 cross-check 프로토콜 문서 | v1.1 §11.3 |
| 7 | **DOS-A30-MIO** A35 + A38 + A40 초안 | v1.1 §13.3 |

**Week 7 게이트**:
- [ ] `bass_py/tsc/` 테스트 ≥ 700 (현재 615 + TSC-03/05/06)
- [ ] tsc ↔ htt F_Bayes cross-check 자동화 + 불일치 시 fail
- [ ] TSC-06 출력에 `is_cross_check=True` 명시 확인

### Week 8 (2026-06-08 ~ 06-14) — "Manuscript ch11/ch12 + HTT stabilisation 완결"

| Day | 작업 | 트랙 |
|---|---|---|
| 1~3 | **MANU-CH11-REDESIGN** — v3 §11.14.2 3 신규 섹션 + v2 "certification engine" 잔존 sweep | v1.1 §13.1 |
| 4~5 | **MANU-CH12-NEW** §12.0 / §12.2 / §12.6 / §12.7 초안 (선행 가능 4 섹션) | v1.1 §13.2 |
| 6 | **HTT-STAB** 잔여 — 2 `bounds` skip 해소 + figure 300 DPI palette 통일 | v1.0 §3.4 |
| 7 | **HTT-NULL** smoke test 최종 green | v1.0 §3.5 |

**Week 8 게이트**:
- [ ] ch11 "truth certificate" ≥ 4회 언급 (v3 §15.2 정성지표)
- [ ] ch12 skeleton + 4 섹션 초안 작성
- [ ] HTT figure skip = 0

### Week 9 (2026-06-15 ~ 06-21) — "DOS-A13 잔여 + Phase-boundary audit"

| Day | 작업 | 트랙 |
|---|---|---|
| 1~5 | **DOS-A13 잔여 12 모델** — 하루 2~3개 페이스 | §3.6 (v1.0) |
| 6 | **Full regression** — bass + tsc + htt + mio + common 합계 (목표 ≥ 1,800 + MIO 기여분 ≥ 25) | v1.1 §15 |
| 7 | **Phase-boundary audit** → `docs/audits/AUDIT_PHASE_MIO_INTEGRATION_W5_W9_2026-06-XX.md` | memory 규칙 |

**Week 9 최종 게이트**: v1.1 §15 + §22 (아래) 통합 기준.

### Week 10 (2026-04-19, 실제 실행) — "DYNESTY 해소 + HJ-01 스켈레톤 + §12.3 초안"

v1.3 에서 §21 에 정식 추가 (W10 F4 후속). 실제 2026-04-19 세션에서
한 번에 소화된 압축 실행 순서를 정규화.

| Day | 작업 | 트랙 | 커밋 tag |
|---|---|---|---|
| 1~2 | **W5-DYNESTY-DEP 해소** — `venv/bin/pip install dynesty` 검증 + `fig_departure_summary.py` smoke 그린; pip-freeze 감사 로그 | §19 후속 (carry-forward) | `W10D1: AUDIT(W5-DYNESTY-DEP): install verified + smoke green` |
| 3~4 | **MIO HJ-01 스켈레톤** — `bass_py/mio/extraction/hj01_shear.py` + 19 테스트. `reduction_status='diagnostic-only'` 게이트; 부모 계획 §17.3 에 따라 bass_py W10-02 K_ℓ atlas V-gate 전까지 `DIAGNOSTIC_ONLY_CAVEAT` 동반 | v3 §4.5.3.1 | `W10D3: MIO HJ-01 shear extraction skeleton` |
| 5~6 | **MANU-CH12 §12.3** — `project/00_manuscript/ch12_mio_observatory_results.tex` 에 §12.3 mock-calibration tension metric 섹션 (≥150 L) 추가 + A14 N1–N5 null family 인용. **working-tree-only 착륙**: memory `feedback_project_local_only.md` 및 W8 FM1 (RESOLVED) 규칙에 따라 `/project` 경로는 **절대로 stage/commit 하지 않는다**. 감사 로그에서 "landed" 는 "working tree 갱신" 을 의미하며, 게이트 증거는 로그 §3-Code(W10D5) 에 수록. | v1.1 §13.2 | (커밋 없음; W10D7 감사 로그에서 증거 기록) |
| 7 | **Phase-boundary audit** → `docs/audits/AUDIT_PHASE_IND_TRACKS_W10_2026-04-19.md` + NEXT_SESSION 로테이션 | memory 규칙 | `IND_TRACKS_W10: phase audit + next-session prompt rotation` |

**Week 10 게이트** (실제 로그 §5 게이트 재정리):
- [x] dynesty 3.0.0 설치 확인 + `fig_departure_summary` smoke SKIP → PASS (touched-surface figures_smoke skip 4 → 3).
- [x] HJ-01 19 테스트 green; MIO contribution 37 → 56 (≥ 47 게이트).
- [x] §12.3 ≥ 150 L; A14 N1–N5 verbatim 인용; banned-vocab scan = 0. **`/project` 경로는 스테이지/커밋되지 않음** (`feedback_project_local_only.md` 준수).
- [x] Phase-boundary audit 로그 작성.
- [x] touched-surface 1026 / 0 / 4 (+19 vs W9; 0 regressions).

### Week 11 (2026-04-19, 진행 중) — "W10 P3 carry-forward 처리 + MIO HJ-02b / HJ-05a + DOS-A3x"

계획은 `docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §2 Week 11 참조.
요약: Days 1-2 W10 F4 + F5 마감, Days 3-4 HJ-02b 또는 HJ-05a 강화,
Days 5-6 DOS-A36/A37 등 A3x dossier 연속, Day 7 phase audit.

---

## §22. 개정 완료 게이트 (v1.1 §15 + §18 통합)

§15 (v1.1) 항목을 **유지**하고 다음을 추가:

- [ ] **RED-01 소멸** — `test_to_mio_builds_bundle` green
- [ ] **SKIP-17 해소** — figure_script smoke test 전부 parse 성공 (skip ≤ 2)
- [ ] **SKIP-02a 해소** — `bounds` 관련 2 skip 해소 (Week 8)
- [ ] **SKIP-02b 해소** — `mio` 관련 2 skip 해소 (Week 6 cascade)
- [ ] **SKIP-02c 해소** — `obs_defaults.json` fixture 활성 (Week 5 Day 5)
- [ ] **PLACEHOLDER-01 소멸** — `PR13AH.mock_calibrated_summary.calibration_pending=False` (bias 주입 시)
- [ ] **SEMANTIC-01 소멸** — `PR13AM.__mio_owned__=True` + artifact `mio_` prefix
- [ ] **AMBIG-01 해소** — `legacy/README.md` 경고 배너 반영
- [ ] **TSC-03/05/06** 완료 — 3 신규 모듈 + 테스트 각각 green
- [ ] **DOS-A13** 15/15 모델 완성
- [ ] **ch03 manuscript** v3 §11.3 목표 ~4,900 L 대비 현재 4,101 L → 차이 ~800 L 보강 (MANU-CH03 후속)

---

| 버전 | 날짜 | 변경 |
|---|---|---|
| v1.0 | 2026-04-19 | 최초 — bass_py 세션 (LB-2a active) 병렬 독립 트랙 정리 |
| v1.1 | 2026-04-19 | v3 MIO 통합 패치 (§10~§17 추가). 앞 §1~§8 불변 유지 |
| **v1.2** | **2026-04-19** | **코드 인스펙션 (기준 커밋 `115f505` LB-5, IND_TRACKS_W4) 결과 반영. §18 실태 요약 + §19 신규 트랙 7종 (WS-BOOT-01, HTT-FIG-SHIM, HTT-OBS-FIXTURE, PR13AH-v2-WIRE, PR13AM-MIO-TAG, LEGACY-README, FIG-MIO-SKIP-GATE) + §20 v1.1 트랙 업데이트 + §21 Week 5~9 실태 반영 실행 순서 (§16 대체) + §22 개정 게이트. PATCH-01/02/03/04 전부 Week 5 내 소멸 경로 확정.** |
| **v1.3** | **2026-04-19** | **W10 F4 후속 — §21 에 Week 10 + Week 11 항목 정식 추가. Week 10 Day 5-6 (`MANU-CH12 §12.3`) 에 **post-W8-FM1 rule** (`/project` 경로 stage/commit 금지; `feedback_project_local_only.md` 준수) 를 명시하여 stale "force-add contract" 표현의 재도입 여지를 제거.** |
