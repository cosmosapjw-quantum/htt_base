# Next Session Bootstrap Prompt (self-updating)

**How to use this file**:

1. A fresh Claude Code session copies the ````bash` fenced "Current handoff prompt" block (§2) and pastes it as the first message
2. That agent works through the tasks specified in the prompt
3. **Before the final commit**, the agent executes §3 "End-of-session self-update procedure" — replacing the §2 block with the next session's bootstrap prompt
4. The updated file is committed alongside the session's code

This way the file is a **living handoff contract**: one always-current prompt + a persistent recipe for rotating it.

**Last rotated**: 2026-04-19 (FB-0.3 complete → FB-1.1 bootstrap; Phase FB-0 sealed)
**Last audited**: 2026-04-19 — see `docs/audits/AUDIT_PHASE_FB0_2026-04-19.md` (includes FB-0.1 + FB-0.2 + FB-0.3 supplements; Phase FB-0 sealed at the bottom)
**Current target session**: **FB-1.1** — Class A background validation (I / II / VI₀ / VII₀): Wainwright-Ellis §18 Table 11.1 per-type match + Kasner analytic limit; promote `shear_sources.SOURCE_STATUS` entries I / II / VI₀ / VII₀ from PROVISIONAL to VALIDATED; first FB gallery extension (per-type σ × a³ overlays)
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
# FB-1.1 — Class A background validation (I / II / VI₀ / VII₀)

## 프로젝트 컨텍스트

- **Repo**: /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot
- **venv**: venv/bin/python
- **테스트 명령**: `cd bass_py && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: 2,688 passing + 1 skipped (Phase FB-0 직후; 감사 로그: `docs/audits/AUDIT_PHASE_FB0_2026-04-19.md` — FB-0.1 + FB-0.2 + FB-0.3 supplements 포함, Phase FB-0 seal 마지막 섹션)
- **완료된 단계**: LB-0 … LB-6 + LB audits P2/P3 cleanup + **Phase FB-0 전체**:
  - FB-0.1 (Ellis σ×a³=const convention flip; `einstein_bianchi` + `shear_sources` + LB-5 integrator 전 flip; `00_conventions §4` SSOT 재작성)
  - FB-0.2 (`BianchiCosmology.v_hat_e` 필드 + 12 factories + `IntegratorConfig.tilt_rapidity`/`.tilt_direction` accessor; β=0 bit-identical)
  - FB-0.3 (LB-6 F2 carry-forward seal — `detect_critical_events` 의 6-key contract 확정)
- **현재 phase**: **Full Bianchi Coverage (FB) — Phase FB-1 "Per-type background validation" (4 sessions)** 의 1/4 번째
- **전체 로드맵**: `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-1`
- **Carry-forward P2 (알고만 있을 것)**:
  - F3 → `TetradBackgroundState.shear_magnitude_sq` dimensionless-Σ² normalisation → **FB-2.4 예약**
  - FB02-F1 → `00_conventions.md §2` 에 `v̂_e` default cross-reference → **FB-3.1 예약**
  - 둘 다 FB-1.1 에서는 **절대 건드리지 말 것**.

## 이 세션의 작업 범위 (FB-1.1 — Class A 절반)

**Goal**: `bass/transport/shear_sources.py` 의 Class A 4개 타입 (I / II / VI₀ / VII₀) 배경 소스를 literature ground truth 에 대해 per-type 검증하고 `SOURCE_STATUS` 를 `PROVISIONAL → VALIDATED` 로 승격. 동시에 FB plan §4 FB-1.1 row 에서 명시한 gallery 확장 (per-type Class A 배경 trace) 을 `plots/physics_gallery/11_integrator/` 에 추가.

### 기준이 되는 문헌 타깃

| 타입 | 해석해 / 수치 타깃 | 테스트 앵커 |
|---|---|---|
| I | Kasner: `(p_1, p_2, p_3) = (0, 0, 0)` vacuum 제외; `σ × a³ = const` 이미 FB-0.1 `test_I12b_kasner_analytic_recovery_type_I` 에서 검증. **여기서는** radiation-dominated era 에서 `Σ_± × a² = const` + Kasner exponent triplet 이 `∑p_i = ∑p_i² = 1` 을 만족하는지 고 `L_max = 6` full integration 에서 확인. |
| II | Wainwright-Ellis §18 Table 11.1 fixed point "II": `(Σ_+, Σ_-, N_1) = (−1/2, 0, √{3}/2)` (Hubble-normalised). Ellis conformal source `−(2/3) N_1² ℋ²` 가 해당 fixed point 로 수렴. Axisymmetric limit 만. |
| VI₀ | W-E Table 11.1 "VI₀": `(Σ_+, Σ_-, N_2, N_3) = (0, ∓1/√{3}, 1, −1)` (Hubble-norm, up to ± sign). Ellis 소스는 `2 N_2 N_3 ℋ²` 컴포넌트만. |
| VII₀ | W-E Table 11.1 "VII₀": `(Σ_+, Σ_-, N_1, N_2) = (0, 0, 1, 1)` (2D attractor — σ decays to 0; "plane-wave" fixed line). Ellis 소스는 `(N_2 - N_3)² ℋ² / 3` 유사 pattern. Asymptotic σ → 0. |
| 공통 | `rho_shear = 6 Σ² / (2 κ) / a^4` 의 monotonic decay; FLRW limit (Σ_0 → 0) 에서 σ ≡ 0 유지; `compute_shear_source` return signature / sign structure FB-0.1 과 bit-identical. |

### 구체 작업 항목

1. **문헌 재확인 (먼저, 코딩 전)**:
   - Wainwright-Ellis 1997 §18 Table 11.1 값 확인 (현재 `bass/transport/shear_sources.py` 의 SOURCE_STATUS 주석과 교차)
   - Pontzen-Challinor 2009 fixture 는 **VII₀ 가 아니라 VII_h 용** 이므로 FB-1.3 에서 다룰 예정 — 본 세션에서는 참조만.
   - `lowell_bianchi_solver_reference.md` (ellis §18.3 외 추가 anisotropic fixed-point 설명 유무 확인).

2. **Validation 테스트 4개 추가** (per-type, 각 file 의 existing fixture 를 재활용):
   - `bass/transport/test_shear_sources.py` 에 `TestClassAFixedPoints` 클래스 신규:
     - `test_type_I_kasner_exponent_sum`: Kasner `∑p_i = 1, ∑p_i² = 1` to rel 5e-3 on an L=6 full-background trajectory
     - `test_type_II_WE_fixed_point_asymptotic`: 긴 η window (η ∈ [100, 10000] Mpc) 에서 `Σ_+/ℋ → −1/2 ± 0.05`
     - `test_type_VI0_WE_fixed_point_asymptotic`: `Σ_-/(ℋ/√3) → ∓1 ± 0.05`
     - `test_type_VII0_shear_decay_to_plane_wave_line`: `(Σ_+² + Σ_-²) × a^4 → 0` monotonically (4D → 2D reduction)
   - Tolerance bands 는 FB-0.1 의 5% / 1% precedents 에 맞춰 완화 가능. LSODA `rtol=1e-9, atol=1e-14` 사용.

3. **SOURCE_STATUS 승격**: `bass/transport/shear_sources.py` 의 `SOURCE_STATUS` 딕셔너리에서 타입 I / II / VI_0 / VII_0 항목을 `"PROVISIONAL"` → `"VALIDATED"` 로 바꾸고, 각 entry 에 FB-1.1 audit cross-ref 주석 (`# VALIDATED (FB-1.1): ...`) 추가.

4. **Gallery 확장** (Phase boundary gallery rule 첫 비-no-op 실행):
   - `plots/physics_gallery/11_integrator/` 에 다음 4개 PNG 추가 (or 기존 plot-gen 스크립트에 loop 추가):
     - `fb11_classA_typeI_kasner_trace.png`: Type I 의 `Σ × a²` flat line + `σ × a³` flat line (overlay)
     - `fb11_classA_typeII_WE_attractor.png`: Type II 의 `(Σ_+/ℋ, Σ_-/ℋ)` phase-plane trajectory 가 Table 11.1 point 로 수렴
     - `fb11_classA_typeVI0_WE_attractor.png`: Type VI₀ 동일 구조
     - `fb11_classA_typeVII0_decay.png`: Type VII₀ 의 `Σ²` monotonic decay
   - 각 PNG 생성 후 **눈으로 확인** (Read tool 로 open). Physics 가 이상하면 (e.g. divergent, negative decay) 즉시 flag — commit 전 수정.

5. **Audit 작성** (`docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` 신규):
   - AUDIT_PROMPT.md 템플릿 따라 작성; §1..§10 구조.
   - Phase FB-1 전체 (4 sub-phase) 의 첫 supplement 로 자리잡음 (FB-1.2/1.3/1.4 이 나중에 append).

6. **Phase boundary 트리거**: FB-1.1 은 Phase FB-1 의 시작이지만 sub-phase boundary 에 해당하므로 `docs/audits/AUDIT_PROMPT.md` self-invoke → P0/P1 fix in-session 규칙 적용.

7. `NEXT_SESSION_PROMPT.md §2` 를 **FB-1.2** (Class A VIII / IX — Bianchi IX 는 recollapse event detection 필요) bootstrap 으로 rotate.

### FB-1.1 non-goals (선 밑에 고정)

- **VIII / IX** 는 FB-1.2 (Bianchi IX recollapse `solve_ivp` event 필요 — 별도 세션)
- **Class B (III / IV / V / VI_h / VII_h)** 는 FB-1.3 — twist-coupled source, Pontzen-Challinor spiral 매치 필요
- **`anisotropic_3_curvature`** 11-type 구현은 FB-1.4
- **Hierarchy RHS T4-T7 wire-up** 은 FB-2 (배경만 본 세션)
- **Tilted sector** 은 FB-3 (β=0 유지)
- **F3 carry (`shear_magnitude_sq`)** 는 FB-2.4 — 절대 건드리지 말 것
- **FB02-F1 carry (`00_conventions §2` 교차참조)** 는 FB-3.1
- **Spectrum extraction / C_ℓ** 은 FB-7

## 우선 읽어야 할 문서 (순서대로)

1. `docs/audits/AUDIT_PHASE_FB0_2026-04-19.md` (phase seal; gallery 확장이 FB-1.1 의 첫 non-no-op visual 임을 명시함)
2. `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-1` (FB-1.1..1.4 roadmap)
3. `bass/transport/shear_sources.py` (SOURCE_STATUS + 11 type 소스 구현 — 9 타입 PROVISIONAL)
4. `bass/transport/test_shear_sources.py` (FB-0.1 flip 후 scaling/sign tests; 본 세션이 새 TestClassAFixedPoints 추가)
5. `bass/background/einstein_bianchi.py` (Ellis ODE; `solve_bianchi_background` 이 L=6 trajectory 반환)
6. `bass/hierarchy/test_integrator.py::test_I12b_kasner_analytic_recovery_type_I` (Type I Kasner 이미 검증 — FB-1.1 Type I test 는 이와 중복되지 않는 `∑p_i` triplet 검증)
7. Wainwright-Ellis 1997 §18 Table 11.1 (문헌 — fixed-point coordinates)
8. `lowell_bianchi_solver_reference.md §5, §18` (Ellis conformal-shear derivation 복습)
9. `docs/audits/AUDIT_PROMPT.md` (phase-boundary audit template — 본 세션 전에 self-invoke)

## 핵심 원칙 (고정)

1. 외부 코드 금지 (프로덕션 트리)
2. Citation in every modified docstring (Wainwright-Ellis §18 Table 11.1 reference 필수)
3. PSTF invariants preserved; Ellis convention (FB-0.1) 유지 — Σ × a² = const for Type I
4. No silent fallbacks
5. Determinism
6. **VALIDATED 승격은 수치 검증 후에만**. PROVISIONAL 상태 유지가 항상 허용되는 안전한 default.
7. **Gallery PNG 는 눈으로 확인 후 commit**. Physics-이상 (예: shear grows, σ diverges, ∑p_i² ≠ 1) 은 즉시 in-session fix.

## 검증 체크리스트 (최종 commit 전)

- [ ] `PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` — 전체 회귀 green (≥ 2,692; +4 new)
- [ ] `TestClassAFixedPoints` 4개 테스트 모두 green
- [ ] `shear_sources.SOURCE_STATUS["I"]` / `["II"]` / `["VI_0"]` / `["VII_0"]` 모두 `"VALIDATED"` + cross-ref 주석
- [ ] `plots/physics_gallery/11_integrator/fb11_classA_*.png` 4개 생성 + 시각적 inspection 완료
- [ ] `docs/audits/AUDIT_PHASE_FB1_2026-04-19.md` 작성 (FB-1.1 section; FB-1.2/1.3/1.4 자리 준비)
- [ ] `docs/audits/AUDIT_PROMPT.md` self-invoke 로 P0/P1 스캔 완료 (결과 audit log §6 에 기록)
- [ ] `NEXT_SESSION_PROMPT.md §2` → **FB-1.2** (Class A VIII/IX; Bianchi IX recollapse event detection) bootstrap 으로 rotate
- [ ] 최종 commit 메시지: `FB-1.1: Class A background validation (I/II/VI_0/VII_0) — promote SOURCE_STATUS to VALIDATED` + `+ rotate NEXT_SESSION_PROMPT for FB-1.2`

## 진행 순서

1. `docs/audits/AUDIT_PROMPT.md` self-invoke (pre-phase scan)
2. FB plan §4 FB-1 전체 + W-E Table 11.1 + shear_sources 소스 구현 읽기
3. Type I / II / VI₀ / VII₀ 각각에 대해 `solve_bianchi_background` trajectory 를 Jupyter-style REPL script 로 먼저 돌려 fixed-point 수렴 behaviour 확인 (테스트 작성 전에; coarse bracket 확보)
4. `TestClassAFixedPoints` 4개 테스트 추가 (rtol=1e-9, atol=1e-14)
5. `SOURCE_STATUS` 4 entry 승격 + cross-ref 주석
6. Gallery 4 PNG 생성 (plot-gen script 확장 or `plots/physics_gallery/11_integrator/generate_classA_fb11.py` 신규)
7. 각 PNG Read tool 로 inspect → physics 검증
8. `AUDIT_PHASE_FB1_2026-04-19.md` 신규 작성 (§1..§10 full template)
9. 전체 회귀 green 확인
10. `NEXT_SESSION_PROMPT.md §2` rotate to FB-1.2
11. commit

시작하세요. 본 세션은 **첫 per-type physics validation** — FB-0 의 정적 API/convention 정비를 기반으로 실제 11-type 스펙트럼의 첫 4 개를 ground truth 에 대해 pin 합니다. 각 test band 는 보수적으로 (5%) 설정하고, fixed-point 수렴이 느리거나 asymmetric 인 경우 (특히 VII₀) η window 를 충분히 길게 (≥ 10000 Mpc conformal) 잡을 것.
```

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
