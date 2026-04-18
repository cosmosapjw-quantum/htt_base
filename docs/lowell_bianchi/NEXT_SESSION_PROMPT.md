# Next Session Bootstrap Prompt (self-updating)

**How to use this file**:

1. A fresh Claude Code session copies the ````bash` fenced "Current handoff prompt" block (§2) and pastes it as the first message
2. That agent works through the tasks specified in the prompt
3. **Before the final commit**, the agent executes §3 "End-of-session self-update procedure" — replacing the §2 block with the next session's bootstrap prompt
4. The updated file is committed alongside the session's code

This way the file is a **living handoff contract**: one always-current prompt + a persistent recipe for rotating it.

**Last rotated**: 2026-04-19 (FB plan approved → FB-0.1 bootstrap)
**Last audited**: 2026-04-19 — see `docs/audits/AUDIT_PHASE_LB6_2026-04-19.md`
**Current target session**: **FB-0.1** — Ellis Σ-convention flip (`σ × a³ = const`) in `einstein_bianchi`, propagate conversion to all downstream consumers, LB-5 F2 carry-forward resolution
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
# FB-0.1 — Ellis Σ-convention flip (einstein_bianchi 재정규화)

## 프로젝트 컨텍스트

- **Repo**: /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot
- **venv**: venv/bin/python
- **테스트 명령**: `cd bass_py && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: 2,558 passing + 1 skipped (LB-6 직후)
- **완료된 단계**: LB-0 … LB-6 전체 (low-ℓ Bianchi solver bedrock 검증 완료)
- **현재 시작하는 phase**: **Full Bianchi Coverage (FB)** — 11 Bianchi types × {orthogonal, tilted} = 22 configurations 까지 솔버 확장. 전체 로드맵은 `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md` (사용자 승인 2026-04-19; §11 체크리스트 5/5 green, §6 D1~D10 추천 기본안 lock-in).

## 이 세션의 작업 범위 (FB-0.1 only)

**Goal**: LB-5 F2 carry-forward 해결. `bass/background/einstein_bianchi.py` 의 shear convention 을 Ellis 표준 (`σ_ab × a³ = const`, `Σ_ab = a × σ_ab`) 으로 정규화하고, 이 변경을 downstream consumers 에 propagate 시킨다. Orthogonal-only scope (β=0); tilted sector 은 FB-3 이 담당.

### 현재 convention (LB-5 이후)

einstein_bianchi 의 `solve_bianchi_background` 는 `Σ_±` 를 `Σ̇ = -𝓗 Σ + source` 로 진행시켜 Type I flat 에서 `Σ × a = const` 보존. 이는 **Ellis 가 아님**. LB-5 F2 audit:
> The LB-5 integrator reuses einstein_bianchi verbatim so I-11 / I-12 had to pin the einstein_bianchi convention. Flipping to Ellis is a dedicated phase.

### 목표 convention (FB-0.1 이후)

- Ellis: `Σ_ab ≡ a × σ_ab`; Type I flat 에서 `σ_ab × a³ = const` ⇒ `Σ_ab × a² = const`
- Σ² (dimensionless shear squared) normalisation: `Σ² ≡ Σ^{ab} Σ_ab / (6 𝓗²)` (lowell §00_conventions §4 이미 Ellis)
- Background ODE: `Σ̇_ab = -𝓗 Σ_ab + shear_source_Ellis(type, ...)` 에서 shear_source 을 Ellis 규격으로 재도출 (Wainwright-Ellis §18)

### 구체적 변경 후보 (감사 후 확정)

1. `bass/background/einstein_bianchi.py::solve_bianchi_background` 의 `(Σ_+, Σ_-)` RHS 를 Ellis convention 으로 rederive
2. `bass/transport/shear_sources.py` 의 11 type source 함수 (source_I … source_IX) — 각각 Ellis convention 에서 재검증; 문헌 대조 표 (W-E §18, Pontzen-Challinor 2009) 확장
3. `bass/background/tetrad_state.py::proper_shear_at_eta` — `σ = Σ / a²` (Ellis) 로 변환
4. LB-5 `bass/hierarchy/integrator.py::_bg_rhs` 의 `compute_shear_source` 호출 인자 조정
5. LB-6 `bass/integration/test_lowell_bianchi.py::TestLBBianchiI::test_LB_6_15 / 16` 의 invariant 을 Ellis 표준으로 재정식화 (LB-6 session 에서는 einstein_bianchi convention 에 amend 되어 있음 — 이제 flip back)

### 수치 타깃 (FB-0.1 exit)

- 전 회귀 green (2,558 + 1 skipped 유지 또는 개선)
- LB-5 I-11 `Σ × a = const` → **LB-5 I-11-Ellis `Σ × a² = const`** 로 rename + 재측정; drift < 5 %
- LB-5 I-12 `Σ² × a² = const` → **LB-5 I-12-Ellis `Σ² × a⁴ = const`** 로 rename + 재측정; drift < 1 %
- LB-6-15 / 16 의 test-body 에 똑같이 반영
- `compute_shear_source` 의 Type I/V validated 소스는 `σ_ab × a³ = const` 을 analytically 재현 (Kasner exact solution)
- FB 플랜 §6 D2 locked default 를 docs/lowell_bianchi/00_conventions.md §4 에 명시 (이미 Ellis 라면 no-op; 아니면 Ellis 로 통일)

## 우선 읽어야 할 문서 (순서대로)

1. `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md` (전체 로드맵, 이 세션의 포지션 §4 FB-0.1 참조)
2. `docs/audits/AUDIT_PHASE_LB5_2026-04-19.md` F2 섹션 (convention mismatch 진단)
3. `docs/audits/AUDIT_PHASE_LB6_2026-04-19.md` §6 F2 carry-forward
4. `docs/lowell_bianchi/00_conventions.md` §4 (Σ² normalisation 현재 spec)
5. `bass/background/einstein_bianchi.py`, `bass/transport/shear_sources.py`, `bass/background/tetrad_state.py`
6. Ellis §18.3 (shear propagation); Wainwright-Ellis §18 (type-specific sources)

## FB-0.1 범위 제약 (고정)

- **convention flip only** — 새 type 추가 / 새 physics 추가 금지
- Tilted sector (β ≠ 0) 건드리지 않음 — FB-3 이 담당
- Non-perturbative boost 건드리지 않음 — FB-3/4
- Perturbation (k ≠ 0) 건드리지 않음 — FB-5
- 외부 코드 금지 조항 유지 (`test_external_code_policy` green 유지)
- LB-5 `IntegratorConfig` API / `IntegrationResult` layout 은 변경 금지 (state vector semantic stays)

## 핵심 원칙 (고정)

1. 외부 코드 금지 (프로덕션 트리)
2. Citation in every modified docstring (Ellis §18.3 / W-E §18 / Pontzen-Challinor 참조 필수)
3. PSTF invariants preserved across the flip
4. No silent fallbacks — convention 선택은 explicit + tested
5. Determinism
6. FLRW limit 재현: 모든 기존 FLRW regression 은 그대로 통과해야 함 (shear ≡ 0 이므로 convention flip 영향 없음)

## 검증 체크리스트 (최종 commit 전)

- [ ] `PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` — 전체 회귀 green
- [ ] LB-6 / LB-5 / Y-Block 기존 테스트 모두 유지 또는 Ellis convention 으로 명시적 amend (amend 은 session 내 commit body 에 문서화)
- [ ] `docs/lowell_bianchi/00_conventions.md §4` 가 Ellis convention 을 SSOT 로 명시
- [ ] `bass/transport/shear_sources.py::SOURCE_STATUS` 의 I / V 는 그대로 "VALIDATED" 유지 (Ellis 하에서 Kasner analytic recovery)
- [ ] 나머지 9 개 (II, III, IV, VI_0, VI_h, VII_0, VII_h, VIII, IX) 은 "PROVISIONAL" 유지 (FB-1 이 VALIDATED 로 올림)
- [ ] 새 Ellis-convention shear-decay invariant 2개 테스트 추가 (Σ × a², Σ² × a⁴)
- [ ] **phase-boundary audit**: `docs/audits/AUDIT_PROMPT.md` 실행 후 `docs/audits/AUDIT_PHASE_FB0_2026-04-XX.md` (phase FB-0 전체의 첫 세션이므로 생성 OK; FB-0.2, FB-0.3 은 append 로 확장)
- [ ] Gallery: convention flip 은 visual no-op (Σ² 의 수치값만 × a² 만큼 스케일) — LB-5 의 `11_integrator/` 플롯을 Ellis axis labels 로 재라벨 (optional)
- [ ] `NEXT_SESSION_PROMPT.md §2` 를 **FB-0.2** bootstrap (`BianchiCosmology(β, v̂_e)` field 확장 + IntegratorConfig tilt parameter 노출) 로 rotate
- [ ] 최종 commit 메시지: `FB-0.1: Ellis σ×a³=const convention flip + shear source rederivation` + `+ rotate NEXT_SESSION_PROMPT for FB-0.2`

## 진행 순서

1. FULL_BIANCHI_COVERAGE_PLAN.md §4 FB-0.1 + LB-5/6 F2 감사 로그 + 00_conventions §4 + einstein_bianchi / shear_sources / tetrad_state 코드 읽기
2. Convention flip map 작성 (어떤 quantity 가 어떤 factor 로 스케일되는지 명시적 표)
3. `solve_bianchi_background` RHS 재도출 (Ellis convention, Type I Kasner analytic 으로 단위 검증)
4. 11개 shear source 재검증 + `SOURCE_STATUS` 유지 (FB-1 가 PROVISIONAL 을 올림; FB-0.1 에서는 flip 만)
5. `proper_shear_at_eta` 에서 σ ↔ Σ 변환 flip
6. LB-5 integrator `_bg_rhs` 재배선 (API 변경 없이 RHS semantic 만 flip)
7. LB-6 `TestLBBianchiI` 테스트 body 의 invariant 표현 flip (Σ×a → Σ×a²; Σ²×a² → Σ²×a⁴)
8. 신규 Ellis-invariant 테스트 2개 추가
9. 전 회귀 녹색 확인 → phase-boundary audit (`AUDIT_PHASE_FB0_2026-04-XX.md` 첫 기입)
10. `NEXT_SESSION_PROMPT.md §2` → FB-0.2 bootstrap (`BianchiCosmology(β, v̂_e)` 확장) 로 교체
11. commit

시작하세요. Convention 변경은 광범위 propagation 이 필요하므로 Step 2 의 map 을 반드시 먼저 만들 것. 모호한 변환은 스펙 (`00_conventions.md §4`) 을 먼저 수정하고 코드를 따르게.
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
