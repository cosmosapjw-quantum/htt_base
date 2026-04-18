# Next Session Bootstrap Prompt (self-updating)

**How to use this file**:

1. A fresh Claude Code session copies the ````bash` fenced "Current handoff prompt" block (§2) and pastes it as the first message
2. That agent works through the tasks specified in the prompt
3. **Before the final commit**, the agent executes §3 "End-of-session self-update procedure" — replacing the §2 block with the next session's bootstrap prompt
4. The updated file is committed alongside the session's code

This way the file is a **living handoff contract**: one always-current prompt + a persistent recipe for rotating it.

**Last rotated**: 2026-04-19 (FB-0.1 complete → FB-0.2 bootstrap)
**Last audited**: 2026-04-19 — see `docs/audits/AUDIT_PHASE_FB0_2026-04-19.md`
**Current target session**: **FB-0.2** — `BianchiCosmology(β, v̂_e)` field expansion + `make_cosmology(type_label, beta=..., v_hat_e=...)` factory + `IntegratorConfig` tilt-parameter surface; β=0 must maintain LB-5 / LB-6 regression bit-for-bit
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
# FB-0.2 — Tilt-field exposure on BianchiCosmology + IntegratorConfig

## 프로젝트 컨텍스트

- **Repo**: /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot
- **venv**: venv/bin/python
- **테스트 명령**: `cd bass_py && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: 2,682 passing + 1 skipped (FB-0.1 직후; 감사 로그: `docs/audits/AUDIT_PHASE_FB0_2026-04-19.md`)
- **완료된 단계**: LB-0 … LB-6 + LB audits P2/P3 cleanup + **FB-0.1 Ellis σ×a³=const convention flip**
- **현재 phase**: **Full Bianchi Coverage (FB) — Phase FB-0 "Convention & dispatch SSOT"** (2/3 완료; FB-0.2 본 세션 + FB-0.3 LB-6 F2 carry)
- **전체 로드맵**: `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md` §4 FB-0

## 이 세션의 작업 범위 (FB-0.2 only)

**Goal**: `BianchiCosmology` 에 tilt 파라미터 (`beta: float = 0.0`, `v_hat_e: tuple = (1.0, 0.0, 0.0)`) 필드를 노출하고, `make_cosmology(type_label, ...)` 팩토리와 `IntegratorConfig` 가 이를 통과시키도록 확장한다. β=0 에서 LB-5 / LB-6 regression 이 bit-for-bit 보존되어야 한다. 실제 tilted physics 는 아직 걸지 않는다 (FB-3); 본 세션은 **파라미터 통로만** 확장.

### 기존 상태 (FB-0.1 이후)

`BianchiCosmology` 는 이미 `beta: float = 0.0` 필드를 가지고 있지만 (`bass/background/einstein_bianchi.py`), `v_hat_e` 는 없다. `IntegratorConfig` 는 `bianchi_cosmo` 전체를 받지만 tilt direction 접근자가 없다. `make_cosmology` / 11개 per-type factory 는 `beta` 만 kw-args 로 통과시킨다.

### 목표 상태 (FB-0.2 이후)

1. `BianchiCosmology.v_hat_e: Tuple[float, float, float] = (1.0, 0.0, 0.0)` 추가
   - Validation: ``|v_hat_e|² = 1`` at construction (norm-normalised unit vector, Ellis §11.3 convention)
   - Factory defaults: 모든 11 type factory가 `beta=0.0, v_hat_e=(1,0,0)` 을 통과
2. `make_cosmology(type_label, beta=..., v_hat_e=...)` 시그니처 확장 (kw-args only)
3. `IntegratorConfig` 는 별도 `beta` / `v_hat_e` 를 받지 않는다 (`bianchi_cosmo` 를 통해 전달) — 하지만 `IntegratorConfig` 수준에서 read-only accessor `.tilt_rapidity` / `.tilt_direction` property 를 추가해 하위 consumer 가 명시적으로 접근 가능하게
4. **Zero-impact guarantee (β=0)**: 모든 기존 2,682 테스트 green 유지; 새 factory/field validation 테스트 5–8개 추가

### FB-0.2 non-goals (선 밑에 고정)

- Non-perturbative β (FB-3 담당)
- Tilted Thomson kernel (FB-4)
- `TiltedSpeciesBackground` 커플링 (FB-3.1)
- `einstein_bianchi` 의 배경 소스 재도출 (이미 FB-0.1 완료)
- β-gate CanonicalDecision 재매개화 (FB-3.5)

## 우선 읽어야 할 문서 (순서대로)

1. `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md` §4 FB-0 (sub-phase 정의)
2. `docs/audits/AUDIT_PHASE_FB0_2026-04-19.md` (FB-0.1 완료 로그, 본 세션이 append)
3. `docs/lowell_bianchi/00_conventions.md` §2 (Frame split rule — n^a 대 u_e^a)
4. `bass/background/einstein_bianchi.py` (BianchiCosmology dataclass + 11 factory + make_cosmology)
5. `bass/hierarchy/integrator.py` (IntegratorConfig; bianchi_cosmo 전달 경로)
6. `bass/tilt/species_tilt.py` (Y-Block tilted species params — 기존 β/v̂ convention 레퍼런스)

## 핵심 원칙 (고정)

1. 외부 코드 금지 (프로덕션 트리)
2. Citation in every modified docstring (Ellis §11.3 / lowell §13 tilted velocity primitives)
3. PSTF invariants preserved
4. No silent fallbacks — `v_hat_e` norm violation 은 ValueError 로 즉시 raise
5. Determinism
6. β=0 default 에서 모든 기존 테스트 green 유지 (bit-for-bit)

## 검증 체크리스트 (최종 commit 전)

- [ ] `PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` — 전체 회귀 green (≥ 2,682)
- [ ] β=0 default 에서 LB-5 I-07..I-18 + LB-6-01..24 모두 bit-identical pass
- [ ] `make_cosmology("VII_h", beta=0.01, v_hat_e=(0.6, 0.8, 0.0))` 예외 없이 `BianchiCosmology` 반환
- [ ] `BianchiCosmology(structure=type_i_constants(), v_hat_e=(1.0, 1.0, 0.0))` 는 norm check 로 ValueError
- [ ] `docs/lowell_bianchi/00_conventions.md §2` 가 `v_hat_e` SSOT 을 명시 (optional — 이미 frame split rule 이 있으면 cross-ref 만)
- [ ] **Phase boundary audit**: 기존 `docs/audits/AUDIT_PHASE_FB0_2026-04-19.md` 에 "## FB-0.2 supplement" 섹션으로 append (신규 파일 아님)
- [ ] Gallery: FB-0.2 는 API 확장만 — visual no-op; 명시적 기록만
- [ ] `NEXT_SESSION_PROMPT.md §2` 를 **FB-0.3** bootstrap (LB-6 F2 carry: `detect_critical_events` → `eta_star` / `chi_star` 키) 로 rotate
- [ ] 최종 commit 메시지: `FB-0.2: tilt-field (β, v̂_e) exposure on BianchiCosmology + IntegratorConfig` + `+ rotate NEXT_SESSION_PROMPT for FB-0.3`

## 진행 순서

1. FB plan §4 FB-0.2 + FB-0.1 audit log + 00_conventions §2 + einstein_bianchi / integrator / species_tilt 읽기
2. `BianchiCosmology` dataclass 확장 — `v_hat_e: tuple = (1.0, 0.0, 0.0)` + `__post_init__` norm 검증
3. 11 per-type factory 가 `v_hat_e` kw-arg 을 수용하도록 업데이트 (default 통과)
4. `make_cosmology` 시그니처 + dispatch 업데이트
5. `IntegratorConfig.tilt_rapidity` / `.tilt_direction` read-only property (단순 forward)
6. 신규 테스트 5-8개 (bass/background/test_einstein_bianchi.py 또는 bass/hierarchy/test_integrator.py):
   - factory default v̂_e = (1, 0, 0)
   - factory custom v̂_e
   - norm validation
   - β=0 bit-identicality (Sigma_plus / a trajectory hash)
   - IntegratorConfig accessor
7. 전 회귀 녹색 확인 → FB-0 audit append
8. `NEXT_SESSION_PROMPT.md §2` → FB-0.3 bootstrap
9. commit

시작하세요. 본 세션은 API 표면 확장만 — 모든 tilted physics 는 FB-3 이 담당한다는 점을 잊지 말 것.
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
