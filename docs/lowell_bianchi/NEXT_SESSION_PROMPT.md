# Next Session Bootstrap Prompt (self-updating)

**How to use this file**:

1. A fresh Claude Code session copies the ````bash` fenced "Current handoff prompt" block (§2) and pastes it as the first message
2. That agent works through the tasks specified in the prompt
3. **Before the final commit**, the agent executes §3 "End-of-session self-update procedure" — replacing the §2 block with the next session's bootstrap prompt
4. The updated file is committed alongside the session's code

This way the file is a **living handoff contract**: one always-current prompt + a persistent recipe for rotating it.

**Last rotated**: 2026-04-19 (FB-1.2 complete → FB-1.3 bootstrap; Class A fully VALIDATED — 4+2 = 6 of 9 PROVISIONAL sources promoted; only Class B III/IV/VI_h/VII_h remain)
**Last audited**: 2026-04-19 — see `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` (FB-1.1 + FB-1.2 supplement; FB-1.3 / 1.4 placeholders reserved at the bottom)
**Current target session**: **FB-1.3** — Class B background validation: III / IV / V / VI_h / VII_h — twist-coupled shear source; Pontzen-Challinor 2009 VII_h spiral calibration; promote `shear_sources.SOURCE_STATUS` Class B types (V already VALIDATED) to VALIDATED; gallery extension for Class B
**Phase-boundary audit prompt**: `docs/audits/AUDIT_PROMPT.md` (run before every next-phase commit)

---

## 1. Self-updating contract (STABLE — do not modify per session)

Every agent that consumes §2 inherits this contract:

- The **last substantive action before final commit** is to update this file's §2 block so the next agent can bootstrap themselves
- Update the "Last rotated" timestamp at the top of this file
- Update the "Current target session" line
- The update recipe is in §4 (Template library); pick the template corresponding to the NEXT LB-N session
- Commit message for the final commit MUST include a line mentioning the next-session handoff (e.g. "+ rotate NEXT_SESSION_PROMPT for LB-N+1")
- If the next session is not obvious (unexpected scope change, blocker discovered), replace §2 with an explicit "BLOCKED" prompt describing what the following agent needs to unblock before coding resumes

This contract is **non-negotiable**. Skipping it breaks the chain.

---

## 2. Current handoff prompt (ROTATE at end of each session)

Copy the block below into a fresh Claude Code session:

```text
# FB-1.3 — Class B background validation (III / IV / V / VI_h / VII_h) + Pontzen-Challinor VII_h spiral match

## 프로젝트 컨텍스트

- **Repo**: /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot
- **venv**: venv/bin/python
- **테스트 명령**: `cd bass_py && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: 2,800 passing + 1 skipped (FB-1.2 직후; 감사 로그: `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` — FB-1.1 + FB-1.2 섹션, FB-1.3/1.4 placeholder 예약됨)
- **완료된 단계**: LB-0 … LB-6 + LB audits P2/P3 cleanup + **Phase FB-0 전체** + **FB-1.1 + FB-1.2**:
  - FB-0.1..0.3 (Ellis convention flip + tilt-field surface + LB-6 F2 seal)
  - FB-1.1 (Class A I/II/VI₀/VII₀ SOURCE_STATUS → VALIDATED; 4 gallery PNGs 03..06; `TestClassAFixedPoints` 61 runs)
  - FB-1.2 (Class A VIII/IX SOURCE_STATUS → VALIDATED + `solve_bianchi_background(events=...)` + `bianchi_ix_recollapse_event(cosmo, floor)`; 2 gallery PNGs 07..08; `TestClassAFixedPoints` +47 runs = 108 total)
- **현재 phase**: **Full Bianchi Coverage (FB) — Phase FB-1 "Per-type background validation" (4 sessions)** 의 3/4 번째
- **전체 로드맵**: `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-1.3`
- **Carry-forward P2 (알고만 있을 것, 절대 건드리지 말 것)**:
  - F3 → `TetradBackgroundState.shear_magnitude_sq` dimensionless-Σ² normalisation → **FB-2.4 예약**
  - FB02-F1 → `00_conventions.md §2` 에 `v̂_e` default cross-reference → **FB-3.1 예약**
  - FB11-F1 → W-E Table 11.1 fixed-point *coordinates* 는 fixed-N 프레임워크에서 직접 도달 불가 → **FB-5 / FB-6 cross-type continuity**; 본 세션도 formula-level validation 유지, Hubble-normalised coordinate chasing 금지
  - FB12-F1 (new, FB-1.2) → IX 은 isotropic limit 에서 leading-order residual `S_+ = +(2/3) n² ℋ²` (W-E 의 pathology) 가 있음; full resolution 은 **FB-5 / FB-6** Mixmaster / BKL 동적 시스템에서. 본 세션 Class B 는 이와 무관하지만 정보로 보관.
  - FB12-F3 → `bianchi_ix_recollapse_event` 는 `_hubble_squared(a, cosmo)` 에 coupling; FB-5 의 vacuum-IX H² 변경 시 event detector 재도출 필요 → **FB-5 / FB-6 예약** (본 세션 Class B 에는 영향 없음)

## 이 세션의 작업 범위 (FB-1.3 — Class B: III / IV / V / VI_h / VII_h)

**Goal**: `bass/transport/shear_sources.py` 의 Class B 5 타입 소스를 W-E §18 + Pontzen-Challinor 2009 (VII_h spiral) 에 대해 per-type 검증하고 `SOURCE_STATUS` 를 `PROVISIONAL → VALIDATED` 로 승격. Class B 의 구분되는 특징: twist parameter `a` ≠ 0 + Jacobi constraint `n_2 = 0`. VII_h 은 spiral coupling (`ω_spiral × Σ_⊥`) 이 추가되는 principal CMB type 이므로 sign + magnitude 양쪽을 Pontzen-Challinor literature fixture 에 맞춰야 함.

### 기준이 되는 문헌 타깃

| 타입 | 해석해 / 수치 타깃 | 테스트 앵커 |
|---|---|---|
| III | III = VI_{h=-1} (특수 케이스). `source_III` 는 `source_VIh` 에 dispatch. h = -1 일 때 formula 유효성 pin. | `test_type_III_dispatches_to_VIh_at_h_minus_1` |
| IV | (0, 0, +) with a > 0. S^{WE}_+ = -(2/3) N_3² + (2/3) A². S^{WE}_- = 0. Cosmologically marginal (no FLRW limit). | `test_type_IV_WE_source_formula` |
| V | (0, 0, 0) with a > 0. Open FLRW (k=-1). S = (0, 0) shear-specifically (A² 는 curvature 로 흡수). 이미 VALIDATED; FB-1.3 은 benchmark reference 업데이트 + explicit formula pin만. | `test_type_V_shear_zero_pin` (regression) |
| VI_h | (+, 0, −) with a > 0, h ∈ (-∞,-1)∪(-1,0). S^{WE}_+ = -(2/3)(n_1-n_3)² + (2/3)A²/(1+\|h\|). S^{WE}_- = -(2/√3)(n_1+n_3)(n_1-n_3). | `test_type_VIh_WE_source_formula` |
| VII_h | **principal CMB type**. (+, 0, +) with a > 0, h > 0. W-E: S^{WE}_+ = -(2/3)(n_1-n_3)² + (2/3)A²/(1+h), S^{WE}_- = +(2/√3)(n_1+n_3)(n_1-n_3). **+ spiral coupling** `ω_spiral = √(\|n_1 n_3\|) × √h × ℋ` applied via `+ω × Σ_-` to dSp, `−ω × Σ_+` to dSm. **Pontzen-Challinor 2009 near-FLRW spiral signature**: rotation in (Σ_+, Σ_-) plane preserves Σ_+² + Σ_-² up to W-E decay. | `test_type_VIIh_WE_source_formula_and_spiral_signature` + `test_type_VIIh_spiral_rotation_conserves_amplitude` |
| 공통 | `compute_shear_source` signature / Ellis conformal ℋ² lift (FB-0.1) / Σ-independence (except VII_h) 보존 | 기존 `TestDimensionalConsistency` / `TestVII_h_Spiral` 유지 + 확장 |

### 구체 작업 항목

1. **문헌 재확인 (먼저, 코딩 전)**:
   - Wainwright-Ellis 1997 §18 Table 11.1 Class B rows + §6 Class B algebras (III = VI_{-1}, IV = Bianchi-IV, V = k<0 FLRW, VI_h 전반, VII_h)
   - Pontzen & Challinor, *PRD* 79, 103518 (2009) — VII_h spiral signature in CMB; `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` FB12-F1 의 교훈 (formula-level validation)
   - `bass/transport/shear_sources.py::source_{III,IV,V,VIh,VIIh}` 현 구현 + SOURCE_STATUS PROVISIONAL 주석

2. **Validation 테스트 5개 추가** (III + IV + V regression + VI_h + VII_h):
   - `bass/transport/test_shear_sources.py::TestClassBFixedPoints` 새 클래스:
     - `test_type_III_dispatches_to_VIh_at_h_minus_1`: III factory 가 h=-1 의 VI_h 와 동일한 결과를 내는지 rel 1e-12 pin
     - `test_type_IV_WE_source_formula`: (n_3, A, ℋ) grid 에서 공식 rel 1e-12 match
     - `test_type_V_shear_zero_pin`: (A, ℋ) grid 에서 S_± = 0 exactly (regression)
     - `test_type_VIh_WE_source_formula`: (n_1, n_3, A, h, ℋ) grid 에서 공식 rel 1e-12 match; h-dependent prefactor 확인
     - `test_type_VIIh_WE_source_formula_and_spiral_signature`: W-E piece (Σ=0) rel 1e-12 + spiral piece (Σ≠0 - Σ=0) antisymmetric coupling + `ω_spiral ∝ √h` scaling
     - `test_type_VIIh_spiral_rotation_conserves_amplitude`: Spiral-only (Σ=0 baseline 제거) 상황에서 `(Σ_+, Σ_-)` 의 회전으로 인한 `Σ_+² + Σ_-²` amplitude invariant — Pontzen-Challinor 의 rotation 시그니처
   - Tolerance: 공식 rel 1e-12; FB-1.1/1.2 precedent 준수. `_CALH_GRID` 재활용.

3. **SOURCE_STATUS 승격**: III / IV / VI_h / VII_h 을 `"PROVISIONAL"` → `"VALIDATED"` 로 변경. V 은 이미 VALIDATED 이므로 reference / benchmark 필드만 FB-1.3 cross-ref 로 업데이트.

4. **Gallery 확장** (FB-1.3 의 non-no-op visual — 예상 3-4 PNG):
   - `plots/physics_gallery/11_integrator/09_fb13_classB_typeIV_WE_source.png`: IV 의 N_3²/A² twist 구조
   - `plots/physics_gallery/11_integrator/10_fb13_classB_typeVIh_WE_attractor.png`: VI_h h-dependent prefactor 시각화
   - `plots/physics_gallery/11_integrator/11_fb13_classB_typeVIIh_spiral.png`: VII_h spiral signature — (Σ_+, Σ_-) plane rotation trace (Pontzen-Challinor 2009 의 CMB 시그니처와 qualitative match)
   - (optional) `12_fb13_classB_typeV_shear_zero.png`: V 의 shear-vanishing + A²-in-curvature visualisation (regression 성격)
   - `scripts/make_physics_gallery.py` 에 `plot_11_09`..`plot_11_12` 추가 + CATALOG 등록
   - 각 PNG 눈으로 확인 (Read tool)

5. **Audit append**: `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` 에 **FB-1.3 supplement** 섹션 append (§1..§10 template).

6. `NEXT_SESSION_PROMPT.md §2` 를 **FB-1.4** (`anisotropic_3_curvature` 11-type consolidation — `tetrad_state.py` ³R_{ab}^{aniso} explicit per type; Phase FB-1 exit) bootstrap 으로 rotate.

### FB-1.3 non-goals (선 밑에 고정)

- **VII_h spiral coefficient κ 의 quantitative calibration 은 FB-5/FB-6** — 본 세션은 sign + scaling (∝ √h) + rotation 시그니처 pin 만
- **`anisotropic_3_curvature` 11-type 구현은 FB-1.4** — 본 세션은 shear source 만
- **Hierarchy RHS T4-T7 wire-up** 은 FB-2
- **Tilted sector** 은 FB-3 (β=0 유지)
- **Class B full Hewitt-Wainwright reduction** (Δ, Ñ 변수) 은 FB-5/FB-6
- **F3 / FB02-F1 / FB11-F1 / FB12-F1 / FB12-F3 carry-forwards**: 건드리지 말 것

## 우선 읽어야 할 문서 (순서대로)

1. `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` §FB-1.2 + §10 + FB-1.3 placeholder (본 세션이 append 할 곳)
2. `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-1.3`
3. `bass/transport/shear_sources.py::{source_III, source_IV, source_V, source_VIh, source_VIIh}` (현 구현 + SOURCE_STATUS PROVISIONAL 주석)
4. `bass/transport/test_shear_sources.py::TestClassAFixedPoints` + `TestVII_h_Spiral` + `TestDimensionalConsistency` (FB-1.2 precedent; 본 세션은 새 `TestClassBFixedPoints` 클래스)
5. Wainwright-Ellis 1997 §18 Table 11.1 Class B rows + §6; Pontzen & Challinor 2009 Sec. III (VII_h spiral)
6. `docs/audits/AUDIT_PROMPT.md` (phase-boundary audit template — 본 세션 전에 self-invoke)

## 핵심 원칙 (고정)

1. 외부 코드 금지 (프로덕션 트리)
2. Citation in every modified docstring (W-E §18 + Pontzen-Challinor 2009 §III 인용 필수 for VII_h)
3. PSTF invariants preserved; Ellis convention (FB-0.1) 유지
4. No silent fallbacks
5. Determinism
6. **VALIDATED 승격은 수치 검증 후에만**; PROVISIONAL 유지가 안전한 default
7. **Gallery PNG 는 눈으로 확인 후 commit**; physics 이상 시 즉시 in-session fix
8. **FB11-F1 + FB12-F1 교훈**: fixed-point coordinate chasing 금지, formula-level pin + qualitative signature (spiral rotation) 이 operative contract

## 검증 체크리스트 (최종 commit 전)

- [ ] `PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` — 전체 회귀 green (baseline 2,800 + 신규 테스트)
- [ ] `TestClassBFixedPoints::test_type_{III,IV,V,VIh,VIIh}_*` green
- [ ] `shear_sources.SOURCE_STATUS["III"|"IV"|"VI_h"|"VII_h"]` 모두 `"VALIDATED"` + cross-ref 주석 (V 는 reference 업데이트)
- [ ] `plots/physics_gallery/11_integrator/{09..1N}_fb13_classB_*.png` 생성 + 시각적 inspection 완료
- [ ] `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` 에 FB-1.3 supplement append (§1..§10)
- [ ] `docs/audits/AUDIT_PROMPT.md` self-invoke 로 P0/P1 스캔 완료 (결과 audit log FB-1.3 §6 에 기록)
- [ ] `NEXT_SESSION_PROMPT.md §2` → **FB-1.4** (`anisotropic_3_curvature` 11-type consolidation) bootstrap 으로 rotate
- [ ] 최종 commit 메시지: `FB-1.3: Class B background validation + VII_h spiral signature match` + `+ rotate NEXT_SESSION_PROMPT for FB-1.4`

## 진행 순서

1. `docs/audits/AUDIT_PROMPT.md` self-invoke (pre-phase scan)
2. FB plan §4 FB-1.3 + Pontzen-Challinor 2009 §III + shear_sources Class B 섹션 읽기
3. 각 Class B type 에 대해 `compute_shear_source` 를 REPL 로 먼저 돌려 behaviour 확인 (특히 VII_h spiral 회전)
4. `TestClassBFixedPoints` 에 테스트 6개 추가 (rel 1e-12 formula + spiral signature)
5. `SOURCE_STATUS` III/IV/VI_h/VII_h 승격 + cross-ref 주석 (V reference 업데이트)
6. Gallery 3-4 PNG 추가
7. 각 PNG Read tool 로 inspect → physics 검증
8. `AUDIT_PHASE_FB1_2026-04-19.md` 에 FB-1.3 supplement append
9. 전체 회귀 green 확인
10. `NEXT_SESSION_PROMPT.md §2` rotate to FB-1.4
11. commit

시작하세요. 본 세션은 **Class B 완주** — FB-1.2 의 formula-level pinning 방식을 Class B (twist-coupled) 에 확장하고, VII_h 의 Pontzen-Challinor spiral 시그니처를 qualitative 하게 (sign + scaling + rotation 보존) 고정합니다. FB-1.4 가 Phase FB-1 의 마지막 rotation 이며 `anisotropic_3_curvature` 로 닫힙니다.
```

---

<!-- Prior (FB-1.2) handoff prompt (saved for reference only; do not re-run). -->

<details>
<summary>Previous FB-1.2 handoff prompt (archived 2026-04-19)</summary>

```text
# FB-1.2 — Class A VIII / IX background validation + Bianchi IX recollapse event

## 프로젝트 컨텍스트

- **Repo**: /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot
- **venv**: venv/bin/python
- **테스트 명령**: `cd bass_py && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: 2,753 passing + 1 skipped (FB-1.1 직후; 감사 로그: `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` — FB-1.1 섹션, FB-1.2/1.3/1.4 placeholder 예약됨)
- **완료된 단계**: LB-0 … LB-6 + LB audits P2/P3 cleanup + **Phase FB-0 전체** + **FB-1.1**:
  - FB-0.1..0.3 (Ellis convention flip + tilt-field surface + LB-6 F2 seal)
  - FB-1.1 (Class A I/II/VI₀/VII₀ SOURCE_STATUS → VALIDATED; 4 new gallery PNGs `plots/physics_gallery/11_integrator/{03..06}_fb11_classA_*.png`; `TestClassAFixedPoints` 61 parametrised runs)
- **현재 phase**: **Full Bianchi Coverage (FB) — Phase FB-1 "Per-type background validation" (4 sessions)** 의 2/4 번째
- **전체 로드맵**: `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-1.2`
- **Carry-forward P2 (알고만 있을 것, 절대 건드리지 말 것)**:
  - F3 → `TetradBackgroundState.shear_magnitude_sq` dimensionless-Σ² normalisation → **FB-2.4 예약**
  - FB02-F1 → `00_conventions.md §2` 에 `v̂_e` default cross-reference → **FB-3.1 예약**
  - FB11-F1 (new, FB-1.1) → W-E Table 11.1 fixed-point *coordinates* 는 fixed-N 프레임워크에서 직접 도달 불가 — **FB-5 / FB-6 cross-type continuity 에서 재검토**. 본 세션 FB-1.2 도 formula-level validation 에 집중, Hubble-normalised coordinate chasing 금지.

## 이 세션의 작업 범위 (FB-1.2 — Class A 나머지: VIII + IX)

**Goal**: `bass/transport/shear_sources.py` 의 Class A 남은 2 타입 (VIII / IX) 배경 소스를 literature ground truth 에 대해 per-type 검증하고 `SOURCE_STATUS` 를 `PROVISIONAL → VALIDATED` 로 승격. 동시에 Bianchi IX recollapse 처리를 위한 `solve_ivp` event detection (FB plan D5 "event-terminated" 옵션) 을 `einstein_bianchi.solve_bianchi_background` 에 도입.

### 기준이 되는 문헌 타깃

| 타입 | 해석해 / 수치 타깃 | 테스트 앵커 |
|---|---|---|
| VIII | Wainwright-Ellis §18 Table 11.1 row "VIII" (sl(2,ℝ) algebra, one negative eigenvalue). Ellis conformal source (현 구현) `S^{WE}_+ = -(2/3)[2N₁² - N₂² - N₃² + N₂N₃]`, `S^{WE}_- = (2/√3)[N₂² - N₃²]`. **Leading-order near-FLRW** form — full nonlinear Mixmaster dispatch 는 FB-5 로 유지. |
| IX | W-E §18 Table 11.1 row "IX" (so(3), Mixmaster, recollapse). Ellis conformal source `S^{WE}_+ = -(2/3)[2N₁² - N₂² - N₃² - N₂N₃]`, `S^{WE}_- = (2/√3)[N₂² - N₃²]`. Isotropic limit n₁ = n₂ = n₃ 에서 `S_± = 0` 확인 (W-E 가 지적한 pathology 유의 — current impl 에서 `2n² - n² - n² - n² = -n² ≠ 0` 이 되어 완전히 0 은 아님; FB-1.2 에서 이 값이 small 한지 확인만). |
| 공통 | `rho_shear ∝ 1/a⁶` (shear energy monotonic decay on non-recollapsing branches); `compute_shear_source` return signature / sign structure 변경 없음. |
| 추가 (IX 전용) | **Bianchi IX recollapse**: `solve_ivp(event=IX_recollapse)` 를 도입. 이벤트 정의: `a'(η) = a × ℋ → 0` 점 (즉 ℋ(a) = 0 지점 in vacuum; Planck-2018 FLRW background 에서는 Ωm + ΩΛ > 0 이므로 ℋ > 0 항상 — 실 recollapse 는 vacuum IX 에만 발생, 즉 non-representative fixture 에서 synthetic 하게 트리거). **FB-1.2 의 event branch 는 integrator 가 NaN/inf 없이 event 를 감지하고 종료하는지 smoke 만** — 실제 production IX 는 FB-5 / FB-6 에서. |

### 구체 작업 항목

1. **문헌 재확인 (먼저, 코딩 전)**:
   - Wainwright-Ellis 1997 §18 Table 11.1 VIII / IX rows + §6 sl(2,ℝ) / so(3) algebra 확인
   - Bianchi IX Mixmaster literature: BKL oscillation (Belinsky-Khalatnikov-Lifshitz 1970) — 본 세션은 axisymmetric smoke 만, full BKL oscillation 은 FB-5/FB-6 deferred
   - `lowell_bianchi_solver_reference.md §18` — anisotropic fixed-point additional notes
   - `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` FB11-F1 의 "formula-level validation" 프레이밍 준수

2. **Validation 테스트 2개 추가** (VIII + IX):
   - `bass/transport/test_shear_sources.py::TestClassAFixedPoints` 클래스에 append:
     - `test_type_VIII_WE_source_formula_and_signs`: (n1, n2, n3) 파라미터 grid 에서 S_+ / S_- 공식이 W-E Table 11.1 VIII 에 대해 rel 1e-12 match. Σ-independence pin. `n1 < 0` 조건 (sl(2,ℝ) algebra) 유지.
     - `test_type_IX_WE_source_formula_and_isotropic_near_limit`: 공식 match + isotropic n₁=n₂=n₃ 에서 `S_±` 가 small (W-E 의 알려진 pathology) — `|S_+| < 10 × (2/3) n² × ℋ²` band 같은 것 허용; 완전 zero 주장 안 함.
   - Tolerance: 공식 rel 1e-12; FB-1.1 precedent 준수. 기존 `_CALH_GRID` 재활용.

3. **`solve_ivp(event=IX_recollapse)` 도입** (production-safe smoke):
   - `bass/background/einstein_bianchi.py::solve_bianchi_background` 에 optional `event=recollapse_event` 인자 추가 (default None = 기존 동작; Type IX default factory 가 event 를 set). Event 정의: `ℋ → 0` 또는 `a' ≤ 0`. `solve_ivp` 의 `events=` 파라미터 사용.
   - Test: `test_bianchi_IX_recollapse_event_fires_on_synthetic_vacuum_background`. FLRW 배경이 대체로 확장 중이므로 synthetic vacuum (H ∝ sqrt(-k/a²)) 시나리오를 작게 시뮬 — 또는 `a_end = small` 로 짧은 window 테스트만. Realistic Bianchi IX 는 FB-5/FB-6 이라 명시.

4. **SOURCE_STATUS 승격**: VIII / IX 을 `"PROVISIONAL"` → `"VALIDATED"` 로 변경. 각 entry 에 FB-1.2 audit cross-ref 주석 추가.

5. **Gallery 확장** (FB-1.2 의 두 번째 non-no-op visual):
   - `plots/physics_gallery/11_integrator/07_fb12_classA_typeVIII_WE_attractor.png`: VIII S_+ / S_- 트라젝토리 + W-E formula 시각화
   - `plots/physics_gallery/11_integrator/08_fb12_classA_typeIX_recollapse_trace.png`: IX 배경 trace + (event branch on 에서) event-fire 시점 표시
   - `scripts/make_physics_gallery.py` 에 `plot_11_07_fb12_classA_typeVIII_WE_attractor` / `plot_11_08_fb12_classA_typeIX_recollapse_trace` 추가 + CATALOG 등록
   - 각 PNG 눈으로 확인 (Read tool) — physics 이상 시 즉시 in-session fix

6. **Audit append**: `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` 에 **FB-1.2 supplement** 섹션 append (§1..§10 template).

7. `NEXT_SESSION_PROMPT.md §2` 를 **FB-1.3** (Class B: III / IV / V / VI_h / VII_h — twist-coupled source, Pontzen-Challinor VII_h spiral 매치) bootstrap 으로 rotate.

### FB-1.2 non-goals (선 밑에 고정)

- **Class B (III / IV / V / VI_h / VII_h)** 는 FB-1.3 — twist-coupled source, Pontzen-Challinor spiral 매치 필요
- **`anisotropic_3_curvature`** 11-type 구현은 FB-1.4
- **Hierarchy RHS T4-T7 wire-up** 은 FB-2 (배경만 본 세션)
- **Tilted sector** 은 FB-3 (β=0 유지)
- **Bianchi IX full BKL oscillation / Mixmaster**: FB-5 / FB-6 (본 세션은 event-branch smoke 만)
- **W-E fixed-point *coordinates* (Σ̂_+ → specific values)** 추구 금지 — FB11-F1 deferred 이므로 formula-level pin 만 수행
- **F3 carry (`shear_magnitude_sq`)** 는 FB-2.4
- **FB02-F1 carry (`00_conventions §2` 교차참조)** 는 FB-3.1
- **Spectrum extraction / C_ℓ** 은 FB-7

## 우선 읽어야 할 문서 (순서대로)

1. `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` §FB-1.1 + §10 + FB-1.2 placeholder (본 세션이 append 할 곳)
2. `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-1.2` + §6 D5 (Bianchi IX recollapse 처리 옵션 — (a) event-terminated solve_ivp 가 권장)
3. `bass/transport/shear_sources.py::source_VIII, source_IX` (현 구현 + SOURCE_STATUS PROVISIONAL 주석)
4. `bass/transport/test_shear_sources.py::TestClassAFixedPoints` (FB-1.1 precedent; 본 세션이 동일 클래스에 VIII/IX 추가)
5. `bass/background/einstein_bianchi.py::solve_bianchi_background` (ODE integrator — event 파라미터 추가 지점)
6. Wainwright-Ellis 1997 §18 Table 11.1 VIII/IX rows + §6 (sl(2,ℝ) / so(3) algebra)
7. `docs/audits/AUDIT_PROMPT.md` (phase-boundary audit template — 본 세션 전에 self-invoke)

## 핵심 원칙 (고정)

1. 외부 코드 금지 (프로덕션 트리)
2. Citation in every modified docstring (W-E §18 Table 11.1 row VIII / IX 인용 필수; BKL reference optional)
3. PSTF invariants preserved; Ellis convention (FB-0.1) 유지
4. No silent fallbacks — event-branch 는 `None` default 에서 이전 거동 유지
5. Determinism
6. **VALIDATED 승격은 수치 검증 후에만**. PROVISIONAL 상태 유지가 항상 허용되는 안전한 default. **FB11-F1 의 교훈: fixed-point coordinate chasing 금지**, formula-level pin 이 operative contract.
7. **Gallery PNG 는 눈으로 확인 후 commit**. Physics-이상 (예: IX event 가 realistic 배경에서 잘못 발화, VIII S_+ 가 sign 반전) 은 즉시 in-session fix.

## 검증 체크리스트 (최종 commit 전)

- [ ] `PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` — 전체 회귀 green (baseline 2,753 + 신규 테스트)
- [ ] `TestClassAFixedPoints::test_type_VIII_*` / `test_type_IX_*` green
- [ ] `test_bianchi_IX_recollapse_event_*` green (synthetic fixture)
- [ ] `shear_sources.SOURCE_STATUS["VIII"]` / `["IX"]` 모두 `"VALIDATED"` + cross-ref 주석
- [ ] `plots/physics_gallery/11_integrator/{07_fb12_classA_typeVIII_WE_attractor.png, 08_fb12_classA_typeIX_recollapse_trace.png}` 생성 + 시각적 inspection 완료
- [ ] `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` 에 FB-1.2 supplement append (§1..§10)
- [ ] `docs/audits/AUDIT_PROMPT.md` self-invoke 로 P0/P1 스캔 완료 (결과 audit log FB-1.2 §6 에 기록)
- [ ] `NEXT_SESSION_PROMPT.md §2` → **FB-1.3** (Class B III/IV/V/VI_h/VII_h; twist-coupled source, Pontzen-Challinor spiral) bootstrap 으로 rotate
- [ ] 최종 commit 메시지: `FB-1.2: Class A VIII/IX background validation + Bianchi IX recollapse event` + `+ rotate NEXT_SESSION_PROMPT for FB-1.3`

## 진행 순서

1. `docs/audits/AUDIT_PROMPT.md` self-invoke (pre-phase scan)
2. FB plan §4 FB-1.2 + §6 D5 + W-E §18 Table 11.1 VIII/IX rows + shear_sources 소스 구현 읽기
3. VIII / IX 각각에 대해 `solve_bianchi_background` trajectory 를 Jupyter-style REPL 로 먼저 돌려 behaviour 확인
4. `TestClassAFixedPoints` 에 VIII / IX 테스트 추가 (rel 1e-12 formula pin)
5. `solve_bianchi_background` 에 `events=` 파라미터 추가 + synthetic vacuum-IX recollapse smoke test
6. `SOURCE_STATUS` VIII / IX 승격 + cross-ref 주석
7. Gallery 2 PNG 추가 (`scripts/make_physics_gallery.py` 에 `plot_11_07`, `plot_11_08`)
8. 각 PNG Read tool 로 inspect → physics 검증
9. `AUDIT_PHASE_FB1_2026-04-19.md` 에 FB-1.2 supplement append
10. 전체 회귀 green 확인
11. `NEXT_SESSION_PROMPT.md §2` rotate to FB-1.3
12. commit

시작하세요. 본 세션은 **Class A 완주** — FB-1.1 의 formula-level pinning 방식을 그대로 VIII / IX 에 확장하고, Bianchi IX 의 recollapse 처리를 위한 event-detection 인프라를 도입합니다. FB11-F1 의 교훈 (fixed-N 프레임워크에서 self-similar coordinate chasing 금지) 을 반드시 준수: W-E Table 11.1 "asymptotic" 언어는 formula-match 로 구체화, dynamical system 재매개화는 FB-5/FB-6 으로 유지.
```

</details>

---

## 3. End-of-session self-update procedure

At the end of a session, before the final commit:

### Step 1 — Determine the next session target

- If the current session's tasks all completed successfully → next target is the subsequent LB-N per README.md §3 "Session sequence"
- If a task partially completed → next target is the same LB-N with the remaining items
- If a blocker was discovered → next target is "unblock: {description}" with an explicit issue list

### Step 2 — Pick the right template from §4

Each LB-N → LB-(N+1) transition has a pre-written template in §4 below. Copy the matching template.

### Step 3 — Customize the template with session-specific numbers

Fill in:

- **baseline test count** (after this session's commits): run `pytest bass/ tsc/ -q` and read the tail line
- **updated "완료된 작업" list** (what's now green and shouldn't be re-done)
- **anything surprising from the session** (performance cliffs, physics subtleties, solver quirks) — add as a "Session N notes" block

### Step 4 — Replace §2 with the customized template

Edit this file. Only §2 rotates; §1, §3, §4 stay intact.

### Step 5 — Update the header

Change:

- `Last rotated: {old date}` → `Last rotated: {today ISO}`
- `Current target session: {old}` → `Current target session: LB-(N+1) {topic}`

### Step 6 — Final commit

Include this file in the final commit of the session. Commit message example:

```text
LB-N: {session accomplishment}

{body}

+ rotate NEXT_SESSION_PROMPT for LB-(N+1)
```

---

## 4. Template library (§2 replacements for each LB-N → LB-(N+1) transition)

### 4.1 After LB-1 → bootstrap for LB-2 (PSTF multipole hierarchy)

```text
# Phase LB 구현 계속 — LB-2 PSTF multipole hierarchy

## 프로젝트 컨텍스트

- **Repo**: /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot
- **venv**: venv/bin/python
- **테스트 명령**: `cd bass_py && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: {FILL IN}
- **완료된 세션**: LB-0 (external-code guard), LB-1 (species backgrounds γ/ν/b/c/Λ)

## 우선 읽어야 할 문서

1. `docs/lowell_bianchi/README.md` §3 (dependency graph)
2. `docs/lowell_bianchi/00_conventions.md` §5 (PSTF packing), §4 (Σ² normalisation)
3. `docs/lowell_bianchi/02_multipole_hierarchy_spec.md` — 이 세션 스펙
4. 참조: `lowell_bianchi_solver_reference.md` §6 (9-term hierarchy 원본)

## 이 세션의 작업 (LB-2는 2 세션 분량 ~1200 LoC — 첫 파트)

`02_multipole_hierarchy_spec.md §12` Implementation checklist 앞 절반:

- `bass/hierarchy/` 서브패키지 생성
- `PSTFTensor`, `PSTFHierarchyState` + packed-full 변환 (Clebsch-Gordan ℓ≤8 사전계산)
- `sym_trace_free` utility
- T1~T9 중 T1, T2, T3, T8, T9 (orthogonal Bianchi에서 활성화되는 subset)
- 테스트 H-01 ~ H-17

두 번째 파트 (다음 세션)에서:
- T4, T5, T6, T7 나머지 term (tilted/vorticity/Bianchi-curved 용)
- `hierarchy_rhs_photon` driver
- 통합 테스트 H-18 ~ H-26

LB-2 범위 제약:
- **Orthogonal Bianchi I, V, VII_0만 대상** — 나머지 type은 NotImplementedError
- **collision은 LB-4 hook으로 남김** — LB-2에서는 K_{A_ℓ} 인터페이스만 정의
- **closure는 HardCut만 구현** — 나머지 (FreeStream/PowerLaw/TCA) 는 LB-3

## 핵심 원칙 (고정)

1. 외부 코드 금지
2. Non-perturbative everywhere
3. Citation in every docstring (Ellis §4.5-4.6, lowell §6 인용 필수)
4. PSTF tensors always STF
5. No silent fallbacks
6. FLRW limit test 필수

## 검증 체크리스트 (최종 commit 전)

- [ ] 전체 회귀 green
- [ ] 신규 테스트 spec 수치 타깃 일치
- [ ] Cite map 준수
- [ ] NEXT_SESSION_PROMPT.md §2 교체 (LB-2 두번째 파트 또는 LB-3용, 완료도에 따라)
- [ ] 최종 commit 메시지에 "+ rotate NEXT_SESSION_PROMPT" 포함

## 진행 순서

1. 스펙 3개 읽기 (README, 00_conventions, 02_hierarchy)
2. Subpackage 레이아웃 생성
3. PSTFTensor + 변환 행렬 → 테스트 H-01..H-08
4. Term 함수 T1/T2/T3/T8/T9 → 테스트 H-13..H-16
5. 부분 회귀 확인
6. NEXT_SESSION_PROMPT.md §2 교체
7. commit

이 세션이 LB-2 전체를 끝낼 수 있으면 그대로 진행하고, 끝나면 LB-3용 prompt로 교체.
```

### 4.2 After LB-2 → bootstrap for LB-3 (closure & truncation)

```text
# Phase LB 구현 계속 — LB-3 closure & truncation

## 프로젝트 컨텍스트
- Repo/venv/테스트 명령 (§4.1과 동일, baseline count만 갱신)
- **현재 baseline**: {FILL IN}
- **완료**: LB-0, LB-1, LB-2

## 우선 읽어야 할 문서
1. `docs/lowell_bianchi/03_closure_truncation_spec.md`
2. (기 완료) LB-2의 `bass/hierarchy/pstf_tensor.py`, `hierarchy_rhs.py`
3. (기 구현) `bass/closure/quadrupole_tca.py` (W6-04) — TCAClosure가 재사용

## 이 세션의 작업 (~500 LoC + 300 LoC tests, 1 세션)

03_closure_truncation_spec.md §11 Implementation checklist 전체:

- `bass/hierarchy/closure.py` — ClosureStrategy Protocol + HardCut/FreeStream/PowerLaw/TCA
- `bass/hierarchy/closure_diagnostics.py` — measure_closure_error
- `build_default_closure` factory
- 테스트 C-01 ~ C-16

LB-3 범위 제약:
- TCA closure는 W6-04 `solve_tca_closure` 재사용 (재구현 금지)
- 새 physics 안 함 — closure만
- Stiffness handling 안 함 (LB-5)

## 핵심 원칙 + 검증 체크리스트 (§4.1과 동일)

## 진행 순서
(§4.1과 동일, NEXT_SESSION_PROMPT는 LB-4용으로 교체)
```

### 4.3 After LB-3 → bootstrap for LB-4 (Thomson collision + tilted visibility)

```text
# Phase LB 구현 계속 — LB-4 Thomson PSTF collision + lowell §11.3 tilted visibility

## 프로젝트 컨텍스트
- **현재 baseline**: {FILL IN}
- **완료**: LB-0..LB-3

## 우선 읽어야 할 문서
1. `docs/lowell_bianchi/04_thomson_collision_spec.md` — §8 (tilted visibility Layer A in-scope) 주의
2. `lowell_bianchi_solver_reference.md §11.1-§11.3` (scalar x_e 유지 + direction-dep boost 원칙)
3. (기 완료) LB-1 `bass/species/baryon.py` (`tau_dot`, `visibility`), LB-2 `bass/hierarchy/*`, LB-3 `closure.py`
4. (기 구현) `bass/collision/thomson_tensor.py` (W3), `bass/closure/quadrupole_tca.py` (W6-04), Y-Block `bass.tilt.species_tilt`
5. 참조: `lowell §4, §9.2, §11.3`

## 이 세션의 작업 (~600 LoC + 450 LoC tests, 1 세션)

04_thomson_collision_spec.md §11 Implementation checklist 전체:

- `bass/collision/polarization.py` — PolarizationHierarchyState, E-mode source
- `bass/collision/thomson_pstf.py` — ThomsonPSTFCollisionOperator (orthogonal PSTF kernel)
- `bass/collision/tilted_visibility.py` — **lowell §11.3 Layer A**: TiltedVisibility wrapper에서 Γ̃_T, κ̃, g̃ 를 scalar × 비선형 Lorentz boost factor B(η, e) = cosh β + sinh β (ê·v̂_e) 로 제공
- 테스트 TC-01 ~ TC-16 + TV-01 ~ TV-08 (총 24+개)

LB-4 범위 제약:
- **PSTF kernel 자체의 full Lorentz boost는 LB-4b**로 분리 유지 (LB-1b tilted species registry 의존)
- Tilted visibility는 **Layer A만** — scalar 보정인자 제공, hierarchy moment projection은 LB-4b
- B-mode는 LB-4c
- 2nd-order v_e² 보정 금지 (LB-4d)
- **Non-perturbative β 엄수**: `1 + v_e · e` 선형근사 금지. 반드시 `cosh β + sinh β (ê·v̂_e)` 형태 유지 (TV-04, TV-07이 lint로 강제)
- **scalar x_e(η), T_m(η) 재계산 금지** — `BaryonBackground` LB-1 HyRec fixture 유지 (lowell §11.1)

## (나머지 §4.1과 동일, NEXT_SESSION_PROMPT는 LB-5용으로)
```

### 4.4 After LB-4 → bootstrap for LB-5 (unified integrator)

```text
# Phase LB 구현 계속 — LB-5 unified background + hierarchy integrator

## 프로젝트 컨텍스트
- **현재 baseline**: {FILL IN}
- **완료**: LB-0..LB-4

## 우선 읽어야 할 문서
1. `docs/lowell_bianchi/05_integrator_spec.md`
2. LB-1..LB-4 결과물 (species, hierarchy, closure, collision)
3. `bass/background/einstein_bianchi.py` (기존 FLRW limit)

## 이 세션의 작업 (~500 LoC + 400 LoC tests)

05_integrator_spec.md §11 Implementation checklist 전체:

- `bass/hierarchy/pack_unpack.py` — state vector utilities
- `bass/hierarchy/aux_state.py` — IntegratorAuxState
- `bass/hierarchy/ic.py` — IC constructors (zero IC baseline)
- `bass/hierarchy/neutrino_reduced.py` — 4-scalar ν fluid RHS
- `bass/hierarchy/event_detection.py` — 임계 η 이벤트
- `bass/hierarchy/integrator.py` — LowellBianchiIntegrator main driver
- 테스트 I-01 ~ I-18

LB-5 범위 제약:
- k = 0 (배경만)
- L_max = 6 기본
- 아직 tilted 안 함 (v_species = 0)

## (나머지 §4.1과 동일, NEXT_SESSION_PROMPT는 LB-6용으로)
```

### 4.5 After LB-5 → bootstrap for LB-6 (integration regression)

```text
# Phase LB 구현 계속 — LB-6 Kolb thermal history + CAMB geometry 회귀

## 프로젝트 컨텍스트
- **현재 baseline**: {FILL IN}
- **완료**: LB-0..LB-5

## 우선 읽어야 할 문서
1. `docs/lowell_bianchi/06_integration_tests_spec.md`
2. LB-5 `LowellBianchiIntegrator` 결과

## 이 세션의 작업 (~400 LoC tests, 1 세션)

06_integration_tests_spec.md §11 Implementation checklist 전체:

- `bass/integration/test_lowell_bianchi.py` 신규
- LB-6-01 ~ LB-6-24 테스트
- Kolb thermal history 매치 (z_eq=3400, z_*=1089.94)
- CAMB geometry 매치 (η_* ≈ 13873, η_0 ≈ 14153)
- Bianchi I shear-decay 불변량

실패 시 diagnostic playbook (§12) 참조. 각 실패 테스트는 정확히 한 LB-N 세션으로 역추적 가능.

## 세션 완료 시 다음 할 일

LB-6 전부 green이면:
- `NEXT_SESSION_PROMPT.md §2`를 **Phase LB 완료 + post-LB 단계 기획** 용으로 교체
- Phase LB 전체 요약 commit ("Phase LB complete: low-ℓ Bianchi solver bedrock verified")

LB-6 부분 실패면:
- 실패한 테스트별로 diagnostic playbook 적용
- `NEXT_SESSION_PROMPT.md §2`를 "LB-N re-open to fix {specific failure}" 로 교체

## (나머지 §4.1과 동일)
```

### 4.6 After LB-6 → bootstrap for post-LB phase

```text
# Phase LB 완료 → post-LB 단계 기획 세션

## 프로젝트 컨텍스트
- **현재 baseline**: {FILL IN}
- **완료**: LB-0..LB-6 전체. Low-ℓ Bianchi solver bedrock 검증 완료

## 이 세션의 작업 (설계만, 코딩 없음)

다음 중 하나를 선택해서 상세 design docs 작성:

**옵션 A — Line-of-sight projection + C_ℓ 추출** (lowell §7 matrix propagator)
- `bass/spectrum/lowell_cl_projection.py` 설계
- PSTF hierarchy 결과 → C_ℓ^{TT,EE,TE} 추출
- CAMB FLRW limit 매치 < 5% 목표

**옵션 B — Perturbation sector** (lowell §9, §13)
- 스칼라 perturbation equations을 PSTF hierarchy에 얹기
- CAMB regular adiabatic seed IC
- Tilted boost rule (§13.5)

**옵션 C — Direction-dependent likelihood** (lowell §14)
- HTT 재설계 (§3의 P0 3종 해결)
- 3-mode operational structure 구현

각 옵션별 `docs/lowell_bianchi/` 하위 새 spec 디렉토리 생성, 세션 분해, 의존성 그래프 작성.

## (나머지 §4.1과 동일, NEXT_SESSION_PROMPT는 선택된 옵션의 첫 세션용)
```

---

## 5. Meta-notes for long-term maintenance

**When Phase LB is fully done** (LB-6 green):
- `NEXT_SESSION_PROMPT.md` rotates into post-LB territory (lowell §7, §9, §13, §14)
- This file can either continue (§4 grows with post-LB templates) or be renamed / archived
- Recommendation: keep it as the single rotating handoff for **all** multi-session work; add new template sections as needed

**When handing off between humans**:
- §2 is the "start here" block — a colleague can read only §2 and bootstrap
- §1, §3 are the mechanism; read once, ignore afterwards
- §4 is reference — consult only when rotating

**When something unexpected happens**:
- Scope change / blocker / external event → write a free-form §2 that explicitly says "BLOCKED — next agent needs to handle X before resuming LB-N"
- Do not try to hide the anomaly in a normal-looking prompt

**Commit discipline**:
- Every commit that includes a §2 rotation must have "+ rotate NEXT_SESSION_PROMPT" in its commit message — this makes the handoff auditable via git log
