# Next Session Bootstrap Prompt (self-updating)

**How to use this file**:

1. A fresh Claude Code session copies the ````bash` fenced "Current handoff prompt" block (§2) and pastes it as the first message
2. That agent works through the tasks specified in the prompt
3. **Before the final commit**, the agent executes §3 "End-of-session self-update procedure" — replacing the §2 block with the next session's bootstrap prompt
4. The updated file is committed alongside the session's code

This way the file is a **living handoff contract**: one always-current prompt + a persistent recipe for rotating it.

**Last rotated**: 2026-04-19 (LB-2b complete → LB-3)
**Last audited**: 2026-04-19 — see `docs/audits/AUDIT_PHASE_LB2b_2026-04-19.md`
**Current target session**: LB-3 closure and truncation (HardCut / FreeStream / PowerLaw / TCA strategies)
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
# Phase LB 구현 계속 — LB-3 closure & truncation

## 프로젝트 컨텍스트

- **Repo**: /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot
- **venv**: venv/bin/python
- **테스트 명령**: `cd bass_py && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: 2,322 tests passing (직전 2,295 + 27 LB-2b)
- **완료된 세션**: LB-0 (external-code guard), LB-1 (species γ/ν/b/c/Λ), LB-2a (PSTF storage + T1/T2/T3/T8/T9), **LB-2b** (T4/T5/T6/T7 + hierarchy_rhs driver)

## 우선 읽어야 할 문서 (순서대로)

1. `docs/audits/AUDIT_PHASE_LB2b_2026-04-19.md` — LB-2b 감사 로그 (no P0/P1; F1 σ/Σ 변환 이미 처리; F4 collision fixture는 LB-4로 이관)
2. `docs/lowell_bianchi/03_closure_truncation_spec.md` — 이 세션 스펙 전체
3. 참조 (LB-2b 완료물): `bass_py/bass/hierarchy/` — `hierarchy_rhs_photon`, `hierarchy_rhs_neutrino`, `proper_shear_at_eta`, `HardCutClosure`, `ClosureStrategy` Protocol
4. 재사용 대상: `bass/closure/quadrupole_tca.py` (W6-04) — `solve_tca_closure`는 LB-3 `TCAClosure` 가 wrapping만 할 것. 재구현 금지.
5. 참조: `lowell_bianchi_solver_reference.md §6` (L=4/6/8 권고), Ma-Bertschinger 1995 §6 (hard-cut vs recursion truncation)

## LB-2b에서 확정된 사실 (LB-3에 참고)

- **Driver signature**: ``hierarchy_rhs_photon(eta, y_flat, *, L_max, bg_table, tetrad_state, closure, collision, collision_aux=None, nabla_operator=None, accel_vector=None, vorticity_vector=None)``. LB-3의 신규 closure 전략은 기존 driver 서명 변경 없이 plug-in.
- **Closure protocol**: ``ClosureStrategy.get_closure(state, ell_requested) -> PSTFTensor`` (`bass/hierarchy/closure_interface.py`). ``HardCutClosure`` 는 within-tower lookup 시 `state.tensors[ell].copy()` 로 aliasing 방지. LB-3 신규 전략도 같은 contract.
- **단위 convention**: T7/T8/T9 는 proper-time σ_ab [1/Mpc]. Driver ``proper_shear_at_eta`` 가 ``TetradBackgroundState.sigma_tensor / a(η)`` 로 변환. LB-3 closure 는 PSTFTensor 만 다루므로 단위 변환 없음.
- **σ interpolation**: 현재 nearest-grid-point (spec §8 명시). LB-5 에서 spline 업그레이드 예정 — LB-3 은 nearest-grid 로 일관성 유지.
- **PSTF 저장**: `(2ℓ+1,)` packing, `pstf_pack/unpack` round-trip 정밀도 ε × 3^ℓ (ℓ=8 에서 ~7e-11). closure 반환물도 `PSTFTensor` 여야 함.
- **외부 코드 가드**: `bass/validation/test_external_code_policy.py` 여전히 활성 — LB-3 신규 파일이 `import camb/classy` 하면 fail.

## 이 세션의 작업 (~500 LoC + 300 LoC tests, 1 세션)

`03_closure_truncation_spec.md §12` Implementation checklist 전체:

- **`bass/hierarchy/closure.py`** — 4 전략을 한 파일에 (기존 `closure_interface.py` 는 Protocol 전용 유지):
  - `HardCutClosure` — LB-2a 에서 이미 `closure_interface.py` 에 구현됨. 재활용 혹은 `closure.py` 로 이관 결정 필요.
  - `FreeStreamingClosure` — Π_{L+1} = recursion from Π_L, Π_{L-1} via free-streaming recursion (Ma-Bertschinger eq 64-65).
  - `PowerLawExtrapolationClosure` — Π_{L+1} = Π_L × (L / (L+1))^α, α from Π_{L-1} / Π_L ratio.
  - `TCAClosure` — ℓ=2 algebraic wrap of existing `bass/closure/quadrupole_tca.py` (W6-04 `solve_tca_closure`). **재구현 금지**.
- **`bass/hierarchy/closure_diagnostics.py`** — `measure_closure_error(state, driver, L_ref, L_test)` 함수, high-ℓ 기준과 저 ℓ 기준의 RHS 차이를 Frobenius norm 으로 돌려줌.
- **`build_default_closure(L_max, strategy_name)` factory** — name ∈ {'hardcut', 'freestream', 'powerlaw', 'tca'}; default 는 'freestream' (LB-3 권고 baseline).
- **테스트 C-01 ~ C-16** (spec §11):
  - C-01..C-04 각 전략이 `ClosureStrategy` Protocol 만족
  - C-05..C-08 각 전략의 수치 타깃 (free-streaming recursion 분석해 / power-law 지수 추정 정확도 / TCA W6-04 wrap 일치도)
  - C-09..C-12 Closure error diagnostic: L=4 와 L=8 RHS 차이 수렴
  - C-13..C-16 Integration smoke: 각 전략별 free-streaming 그리고 Bianchi I 쇼트 적분에서 sign / order of magnitude 일치

## LB-3 범위 제약 (고정)

- **TCA closure 재구현 금지** — `bass.closure.quadrupole_tca.solve_tca_closure` 만 wrapping
- **새 physics 안 함** — 9-term hierarchy 공식은 LB-2 가 고정
- **Stiffness handling 안 함** — LSODA / implicit scheme 은 LB-5 integrator
- **Bianchi type 확장 안 함** — 여전히 I / V / VII_0 만 공식 지원

commit 메시지: `LB-3: closure & truncation (HardCut + FreeStream + PowerLaw + TCA)`

## 핵심 원칙 (고정, 위반 시 PR 거부)

1. **외부 코드 금지**: CAMB/CLASS/HyRec/AniCLASS는 `scripts/generate_*_reference.py`와 `test_*.py`에만.
2. **Citation in every docstring**: Ellis §4.6 / Ma-Bertschinger 1995 §6 / Pitrou 2009 / lowell §6.
3. **PSTF tensors always symmetric-traceless**: `verify_pstf_invariants` 재활용 — closure 가 반환하는 Π_{L+1}, Π_{L+2} 도 PSTF 여야 함.
4. **No silent fallbacks**: 미구현 전략 이름 → ValueError.
5. **Closure must not mutate state**: `get_closure` 는 `state.tensors[...].copy()` 만 사용 (HardCut 선례 따름).
6. **FLRW limit**: σ = 0 에서 TCA 도 LB-2b 의 zero-shear quadrupole 과 bit-일치해야 함.

## 검증 체크리스트 (최종 commit 전)

- [ ] `PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` — 전체 회귀 green (baseline 2,322 이상)
- [ ] 신규 테스트 모두 spec 수치 타깃 일치 (C-01 ~ C-16)
- [ ] Closure protocol (PSTFTensor 반환, state 불변, rank 일치) 전 전략 준수
- [ ] 신규 LoC ≥ 25% 테스트 커버리지
- [ ] **phase-boundary audit**: `docs/audits/AUDIT_PROMPT.md` 실행 후 `AUDIT_PHASE_LB3_<date>.md` 생성
- [ ] **gallery refresh**: `plots/physics_gallery/09_pstf_hierarchy/` 에 closure-error 수렴 / 전략 비교 플롯 최소 1-2 개 추가
- [ ] **`NEXT_SESSION_PROMPT.md §2` 블록을 LB-4용으로 교체** (§4.3 템플릿)
- [ ] 최종 commit 메시지에 "+ rotate NEXT_SESSION_PROMPT" 라인 포함

## 진행 순서

1. LB-2b audit + LB-3 spec + `quadrupole_tca.py` 읽기
2. `HardCutClosure` 재배치 또는 재사용 결정
3. FreeStream / PowerLaw 구현 → C-05..C-08 수치 타깃
4. TCAClosure wrapping (`solve_tca_closure` 호출) → C-07 W6-04 기존 테스트와 bit-일치
5. `closure_diagnostics.measure_closure_error` → C-09..C-12
6. Integration smoke C-13..C-16
7. Gallery 확장 (closure 수렴 플롯)
8. 전 회귀 확인 → phase-boundary audit
9. `NEXT_SESSION_PROMPT.md §2` → LB-4 bootstrap
10. commit

시작하세요. 스펙과 다른 방향 제안 시 반드시 spec 문서 먼저 수정.
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
