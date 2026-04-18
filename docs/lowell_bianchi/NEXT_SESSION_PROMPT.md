# Next Session Bootstrap Prompt (self-updating)

**How to use this file**:

1. A fresh Claude Code session copies the ````bash` fenced "Current handoff prompt" block (§2) and pastes it as the first message
2. That agent works through the tasks specified in the prompt
3. **Before the final commit**, the agent executes §3 "End-of-session self-update procedure" — replacing the §2 block with the next session's bootstrap prompt
4. The updated file is committed alongside the session's code

This way the file is a **living handoff contract**: one always-current prompt + a persistent recipe for rotating it.

**Last rotated**: 2026-04-19 (LB-2a complete → LB-2b)
**Last audited**: 2026-04-19 — see `docs/audits/AUDIT_PHASE_LB2a_2026-04-19.md`
**Current target session**: LB-2b PSTF multipole hierarchy (second half)
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
# Phase LB 구현 계속 — LB-2b PSTF multipole hierarchy (second half)

## 프로젝트 컨텍스트

- **Repo**: /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot
- **venv**: venv/bin/python
- **테스트 명령**: `cd bass_py && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: 2,295 tests passing (직전 2,141 + 154 LB-2a hierarchy)
- **완료된 세션**: LB-0 (external-code policy guard), LB-1 (species γ/ν/b/c/Λ), **LB-2a** (PSTF storage + T1/T2/T3/T8/T9)

## 우선 읽어야 할 문서 (순서대로)

1. `docs/audits/AUDIT_PHASE_LB2a_2026-04-19.md` — LB-2a 감사 로그 (F1 주의: σ_ab 단위 변환 필요)
2. `docs/lowell_bianchi/02_multipole_hierarchy_spec.md` — 이 세션 스펙 §4-§9 (RHS driver, integration with TetradBackgroundState)
3. 참조: `lowell_bianchi_solver_reference.md` §6 (9-term 원본)
4. 참조 (LB-2a 완료물): `bass_py/bass/hierarchy/` — `PSTFTensor`, `PSTFHierarchyState`, `sym_trace_free`, `T1_expansion..T9_shear_down`, `HardCutClosure`, `ZeroCollisionOperator`
5. 참조: Y-Block `bass_py/bass/background/tetrad_state.py` (Σ_ab → σ_ab 변환 필요 지점)

## LB-2a에서 확정된 사실 (LB-2b에 참고)

- **PSTF 저장**: real sph harm 기반 ``(2ℓ+1,)`` packing. ℓ=0..8 STF basis ``Q_ℓ`` import 시 사전계산 (~110 KB total). Flat-orthonormal: ``Q_ℓ^T Q_ℓ = I``.
- **`sym_trace_free(T)`**: rank-ℓ 텐서 → PSTF projection. ℓ ∈ {0, 1}은 identity; ℓ ≥ 2는 Q @ Q^T @ flat.
- **`pstf_pack/unpack`**: 라운드트립 정밀도 ε_mach × 3^ℓ (ℓ ≤ 4 machine, ℓ=8 ~7e-11). 테스트 atol scales.
- **구현된 term**: T1 (expansion), T2 (gradient via nabla_op), T3 (divergence via nabla_op), T8 (shear stays at ℓ), T9 (shear → ℓ-2). 모두 pure function, rank 검증 포함.
- **지연된 term**: T4 (accel × divergence), T5 (accel × gradient), T6 (vorticity), T7 (shear → ℓ+2) — 현재 ``NotImplementedError`` 스텁.
- **단위 convention (F1 감사 결과, 중요)**: T1의 ``Theta``는 proper-time Θ = 3H (1/Mpc). T8/T9의 ``sigma_tensor``는 proper-time σ_ab (1/Mpc) — **NOT** ``TetradBackgroundState.sigma_tensor`` (그쪽은 Pontzen-Σ 규약이므로 1/a 변환 필요). LB-2b 드라이버에서 이 변환을 반드시 명시.
- **Closure/collision hook**: ``HardCutClosure`` (Π_{>L} = 0), ``ZeroCollisionOperator`` (K = 0). LB-3/LB-4에서 확장.
- **외부 코드 가드**: `bass/validation/test_external_code_policy.py` 활성. LB-2b 신규 파일이 `import camb/classy/...` 하면 fail.

## 이 세션의 작업 (LB-2 second part, ~500 LoC + 400 LoC tests)

`docs/lowell_bianchi/02_multipole_hierarchy_spec.md §12` Implementation checklist 나머지:

- **T4, T5, T6, T7 구현** — orthogonal Bianchi에서는 A=ω=0이라 T4/T5/T6는 실질적으로 zero 경로; T7은 σ ≠ 0일 때 non-trivial. 모두 PSTF-projected.
  - T7 prefactor: `−((ℓ−1)(ℓ+1)(ℓ+2)/((2ℓ+3)(2ℓ+5))) σ^{bc} Π_{A_ℓ bc}` — Π_{ℓ+2} 참조, closure strategy로 잡음.
  - T4/T5/T6는 현재 ``NotImplementedError`` 스텁을 유지하고 (LB-2c tilted/vorticity에서 구현) OR 0을 반환하는 orthogonal-only 경로만 추가.
- **`bass/hierarchy/hierarchy_rhs.py`** — ``hierarchy_rhs_photon(eta, y_flat, L_max, bg_table, tetrad_state, ..., closure, collision) -> dy/deta`` driver
  - σ_ab 변환: ``TetradBackgroundState.sigma_tensor[i_eta] / a[i_eta]`` (proper σ)
  - Θ from ``FLRWBackgroundTable.Theta`` (proper, 1/Mpc)
  - dy/dη = a × (-Σ Tn + K) (오버도트 → η 프라임 변환)
  - ``solve_ivp``-compatible signature
- **중립미자 driver** (선택): ``hierarchy_rhs_neutrino`` — 동일 hierarchy로 Γ_T = 0, `ZeroCollisionOperator`
- **테스트 H-18 ~ H-26** (spec §11.4, §11.5):
  - H-18: zero state + FLRW → zero dy/dη
  - H-19: Γ_T=0, Π_1=0, σ=0: free-streaming tower recovers
  - H-20: Π_1=1, Π_ℓ≥2=0: only T2 couples (gradient operator required OR NotImplementedError/zero)
  - H-21: Γ_T → ∞, v_b=1: RHS at ℓ=1 = +Γ_T (needs K hook wired; might defer until LB-4)
  - H-22: σ≠0, Π_0=1: RHS at ℓ=2 picks up T9 = −4 σ
  - H-23: L_max=4, HardCut closure: T3, T7 at ℓ=L 0
  - H-24..H-26: solve_ivp integration smoke (minimal setup, Bianchi I constant Σ_+)

## LB-2 범위 제약 (고정)

- **Orthogonal Bianchi I, V, VII_0만 대상** — 나머지 type은 `NotImplementedError`
- **Tilted species는 LB-2c로 더 분리** — v_(s) = 0 assumption 유지
- **collision은 LB-4 hook으로 남김** — LB-2b에서는 `ZeroCollisionOperator`만 테스트; `ThomsonCollisionOperator`는 LB-4
- **closure는 HardCut만 구현** — FreeStream/PowerLaw/TCA는 LB-3

commit 메시지: `LB-2b: PSTF hierarchy driver + T4/T5/T6/T7 (orthogonal)`

## 핵심 원칙 (고정, 위반 시 PR 거부)

1. **외부 코드 금지**: CAMB/CLASS/HyRec/AniCLASS는 `scripts/generate_*_reference.py`와 `test_*.py`에만.
2. **Non-perturbative everywhere**: sinh(β), cosh(β) 유지 (tilted extension 시).
3. **Citation in every docstring**: Ellis §X.Y / Kolb §X.Y / Baumann §X.Y / lowell §X.
4. **PSTF tensors always symmetric-traceless**: LB-2a의 `verify_pstf_invariants` 재활용.
5. **No silent fallbacks**: 미구현 Bianchi type = `NotImplementedError`.
6. **FLRW limit test**: σ=0 한계에서 tower가 단순 T1 damping으로 환원.
7. **단위 변환 명시**: σ_ab proper 대 Σ_ab conformal — driver에서 1/a 변환 코드에 docstring으로 명확히.

## 검증 체크리스트 (최종 commit 전)

- [ ] `PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` — 전체 회귀 green (baseline 2,295 이상)
- [ ] 신규 테스트 모두 spec 수치 타깃 일치 (H-18 ~ H-26)
- [ ] LB-2a 단위 변환 convention (Σ → σ = Σ/a) driver에 명시
- [ ] 신규 LoC ≥ 25% 테스트 커버리지
- [ ] **phase-boundary audit**: `docs/audits/AUDIT_PROMPT.md` 실행 후 `AUDIT_PHASE_LB2b_<date>.md` 생성
- [ ] **`NEXT_SESSION_PROMPT.md §2` 블록을 LB-3용으로 교체** — §3 절차 따르기
- [ ] 최종 commit 메시지에 "+ rotate NEXT_SESSION_PROMPT" 라인 포함

## 진행 순서

1. LB-2a audit 읽기 (F1 unit convention 주의)
2. LB-2a 코드 빠른 스캔 (`bass/hierarchy/__init__.py`, `terms.py`)
3. T4/T5/T6/T7 구현 → 단위 테스트
4. `hierarchy_rhs.py` driver 구현 (Σ→σ 변환 포함) → H-18..H-23
5. solve_ivp integration smoke → H-24..H-26
6. 전 회귀 확인 → phase-boundary audit
7. `NEXT_SESSION_PROMPT.md §2` → LB-3 bootstrap (§4.2 템플릿)
8. commit

시작하세요. 질문 있으면 중간에 멈추고 명확히 하기 먼저. 스펙과 다른 방향 제안 시 반드시 spec 문서 먼저 수정.
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
