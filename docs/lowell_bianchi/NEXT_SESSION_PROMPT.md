# Next Session Bootstrap Prompt (self-updating)

**How to use this file**:

1. A fresh Claude Code session copies the ````bash` fenced "Current handoff prompt" block (§2) and pastes it as the first message
2. That agent works through the tasks specified in the prompt
3. **Before the final commit**, the agent executes §3 "End-of-session self-update procedure" — replacing the §2 block with the next session's bootstrap prompt
4. The updated file is committed alongside the session's code

This way the file is a **living handoff contract**: one always-current prompt + a persistent recipe for rotating it.

**Last rotated**: 2026-04-19 (LB-6 complete → post-LB design session)
**Last audited**: 2026-04-19 — see `docs/audits/AUDIT_PHASE_LB6_2026-04-19.md`
**Current target session**: post-LB phase — design-only session to pick and scope one of options A / B / C (line-of-sight, perturbation sector, direction-dependent likelihood)
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
# Phase LB 완료 → post-LB 단계 기획 세션 (design-only)

## 프로젝트 컨텍스트

- **Repo**: /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot
- **venv**: venv/bin/python
- **테스트 명령**: `cd bass_py && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: 2,558 tests passing + 1 skipped (LB-5 2,534 + LB-6 24 new pass + 1 deferred LB-6-11)
- **완료된 세션**: LB-0 (external-code guard), LB-1 (species γ/ν/b/c/Λ), LB-2a/b (PSTF hierarchy T1..T9 + driver), LB-3 (HardCut + FreeStream + PowerLaw + TCA closures + measure_closure_error), LB-4 (Thomson PSTF + E-mode collision + lowell §11.3 TiltedVisibility Layer A), LB-5 (`LowellBianchiIntegrator` unified driver + real W3 `CanonicalDecision` wiring + TCA DAE dispatch), **LB-6** (end-to-end regression suite `bass/integration/test_lowell_bianchi.py` — Kolb thermal history + CAMB geometry match + Bianchi I shear invariants)
- **Phase LB 상태**: 완료. Low-ℓ Bianchi solver bedrock verified against textbook thermal history + CAMB Planck-2018 geometry.

## 이 세션의 작업 (설계만, 코딩 없음)

Phase LB 가 끝났으므로 post-LB 세 옵션 중 하나를 선택해서 **상세 design docs** 를 작성하는 것이 이 세션의 유일한 목표다.

**옵션 A — Line-of-sight projection + C_ℓ 추출** (lowell §7 matrix propagator)
- 목적: PSTF hierarchy 결과 → C_ℓ^{TT, EE, TE} 추출 (CAMB FLRW limit 매치 < 5 % 목표)
- 새 docs: `docs/lowell_bianchi/post_lb_A_line_of_sight/` — spec 문서 3~5개로 분해 (projection spec + source term assembly + regression spec + CAMB fixture binding)
- 첫 세션 예상 작업: visibility/source integrand 구성 + recombination-era Π_2 source integration

**옵션 B — Perturbation sector** (lowell §9, §13)
- 목적: 스칼라 perturbation equations을 PSTF hierarchy 에 얹기. CAMB regular adiabatic seed IC + tilted-boost rule (§13.5).
- 새 docs: `docs/lowell_bianchi/post_lb_B_perturbation/` — k-dispatch ∇̃ structure-constant logic (lowell §13), seed IC spec, PSTF-regularised boost
- 첫 세션 예상 작업: k=0 limit 에서의 regular seed spec 확정 + 기존 integrator 와의 composition rule

**옵션 C — Direction-dependent likelihood** (lowell §14)
- 목적: HTT 재설계 (§3의 P0 3종 해결) + 3-mode operational structure 구현
- 새 docs: `docs/lowell_bianchi/post_lb_C_htt/` — §14.2 HTT decomposition spec + §14.3 likelihood evaluation contract + tiered-resolution plan
- 첫 세션 예상 작업: HTT P0 3종 issue 정리 + likelihood evaluator contract 제안

## 우선 읽어야 할 문서 (순서대로)

1. `docs/audits/AUDIT_PHASE_LB6_2026-04-19.md` — LB-6 감사 로그 (no P0/P1; in-session spec 수정 6건 요약; carry-forwards F1/F2/F3)
2. `docs/lowell_bianchi/README.md` §6 (phase success criteria, LB 완료 상태) + §7 (post-LB 개요)
3. `lowell_bianchi_solver_reference.md` §7 (matrix propagator), §9.2 (perturbation sector), §13.5 (tilted-boost), §14 (HTT + likelihood) — 각 옵션의 기본 수학 소스
4. 기존 LB 모듈 (옵션 선택 후에만):
   - LB-5 unified integrator: `bass_py/bass/hierarchy/integrator.py`
   - LB-6 regression suite: `bass_py/bass/integration/test_lowell_bianchi.py`
   - LB-0..4 dependencies: spec + code per `README.md §3`
5. 참조 데이터:
   - `data/camb_ref_planck2018.npz` — C_TT, C_EE, C_TE, D_* at ell=2..30 (옵션 A gate)
   - HyRec fixture (LB-1)
   - Y-Block tetrad + shear source (`bass/background`) — 옵션 B 에서 재사용

## LB-6 carry-forward P2 items (post-LB 첫 세션이 decide)

- **F1 (LB-6)**: 서브그리드 z_* 감지기 (Currently integer-argmax on Δz=1 fixture → ±1 band). 옵션 A 에서 `η_*` / `χ_*` 정밀도가 재현율에 영향 주면 우선 해결.
- **F2 (LB-6)**: `detect_critical_events` 가 `eta_star` / `chi_star` 키 누락 — 옵션 A 시작 전에 tidy-up 1-commit 으로 처리 권장.
- **F2 (LB-5)**: `einstein_bianchi` Σ-convention (`Σ × a = const`) vs Ellis (`σ × a³ = const`). 전면 conversion 은 옵션 B perturbation 세션에서 자연스럽게 동반 — B 를 선택하면 B 의 첫 서브-세션으로.
- **F3 (LB-5)**: LSODA stiffness at dynamically-huge Γ_T — 옵션 A/B 에서 재현될 가능성 낮음 (override 는 test-only).

## post-LB 세션 범위 제약 (고정, 이 세션에서 위반 금지)

- **코딩 금지** — 오직 design docs. 기존 코드 수정 / 신규 production 파일 생성 금지.
- 옵션 A / B / C 중 **정확히 하나만 선택**. 여러 개 동시 기획은 session 분량 초과.
- 선택한 옵션의 design docs 는 LB 스펙 포맷을 준수 (§1 개요 → §N 구현 체크리스트 → 수치 타깃 → diagnostic playbook).
- 외부 코드 참조 제한은 **유효** — spec 문서가 `import camb` 예시를 적어도 실제 구현 트리에는 절대 침투 금지.
- 사용자가 특정 옵션을 지정 안 하면 **옵션 A 를 기본 추천** (LB-6 이 이미 CAMB 레퍼런스와 pin 된 상태라 가장 자연스러운 다음 단계).

## 핵심 원칙 (고정)

1. 외부 코드 금지 (프로덕션 트리)
2. Citation in every design docs section (lowell §N.M 참조 필수)
3. PSTF invariants preserved across any proposed new layer
4. No silent fallbacks
5. Determinism
6. FLRW limit 재현 (옵션 A/B 는 LB-6 regression 연장선)

## 검증 체크리스트 (최종 commit 전)

- [ ] 선택된 옵션의 design docs 완성 (`docs/lowell_bianchi/post_lb_X_*/` 하위)
- [ ] Session 분해 표 + 의존성 그래프 + 수치 타깃 표 포함
- [ ] `README.md §7` (post-LB 개요) 업데이트: 선택된 옵션 경로만 남기고 나머지 두 옵션은 "deferred" 표시
- [ ] `NEXT_SESSION_PROMPT.md §2` → 선택된 옵션의 **첫 구현 세션** 용 prompt 로 교체 (§4.6 template 보강 또는 옵션-specific 새 template 추가)
- [ ] 최종 commit 메시지: `post-LB: <option letter> design docs (<short description>)` + `+ rotate NEXT_SESSION_PROMPT`
- [ ] 회귀는 돌리지 않아도 됨 (코드 변경 없음) — 단, 기존 2,558 tests 가 여전히 green 인지는 git 상태만 확인

## 진행 순서

1. AUDIT_PHASE_LB6 + README §6/§7 + lowell §7 / §9 / §13 / §14 읽기
2. 사용자에게 A/B/C 중 하나를 확인 (없으면 A 를 추천)
3. 선택된 옵션의 design docs 스펙 5개 분해 (`post_lb_X/00_overview.md` … `04_regression_spec.md` 식)
4. Session 분해 표 작성 (각 서브-세션이 1~2 일 분량)
5. 의존성 그래프 확정 — LB-6 carry-forward P2 를 어느 서브-세션에 흡수할지 결정
6. `README.md §7` 갱신 + `NEXT_SESSION_PROMPT.md §2` 를 첫 구현 세션 prompt 로 교체
7. commit

시작하세요. 옵션 선택이 이 세션의 유일한 의사결정 포인트입니다 — 다른 방향 제안 시 반드시 문서 먼저 수정.
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
