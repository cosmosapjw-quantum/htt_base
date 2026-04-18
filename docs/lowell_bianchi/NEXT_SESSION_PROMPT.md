# Next Session Bootstrap Prompt (self-updating)

**How to use this file**:

1. A fresh Claude Code session copies the ````bash` fenced "Current handoff prompt" block (§2) and pastes it as the first message
2. That agent works through the tasks specified in the prompt
3. **Before the final commit**, the agent executes §3 "End-of-session self-update procedure" — replacing the §2 block with the next session's bootstrap prompt
4. The updated file is committed alongside the session's code

This way the file is a **living handoff contract**: one always-current prompt + a persistent recipe for rotating it.

**Last rotated**: 2026-04-19 (LB-5 complete → LB-6)
**Last audited**: 2026-04-19 — see `docs/audits/AUDIT_PHASE_LB5_2026-04-19.md`
**Current target session**: LB-6 Kolb thermal history + CAMB geometry regression
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
# Phase LB 구현 계속 — LB-6 Kolb thermal history + CAMB geometry 회귀

## 프로젝트 컨텍스트

- **Repo**: /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot
- **venv**: venv/bin/python
- **테스트 명령**: `cd bass_py && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: 2,534 tests passing (직전 2,441 + 93 LB-5)
- **완료된 세션**: LB-0 (external-code guard), LB-1 (species γ/ν/b/c/Λ), LB-2a (PSTF storage + T1/T2/T3/T8/T9), LB-2b (T4/T5/T6/T7 + hierarchy_rhs driver), LB-3 (HardCut + FreeStream + PowerLaw + TCA closure strategies + measure_closure_error), LB-4 (ThomsonPSTFCollisionOperator + EModeThomsonCollisionOperator + PolarizationHierarchyState + lowell §11.3 TiltedVisibility Layer A), **LB-5** (`LowellBianchiIntegrator` unified driver + pack_unpack / aux_state / ic / neutrino_reduced / event_detection + TCA DAE dispatch + real W3 `CanonicalDecision` wiring resolving LB-3/LB-4 F3)

## 우선 읽어야 할 문서 (순서대로)

1. `docs/audits/AUDIT_PHASE_LB5_2026-04-19.md` — LB-5 감사 로그 (no P0/P1; F1 η_reion 밴드 / F2 `einstein_bianchi` Σ-convention / F3 LSODA stiffness note)
2. `docs/lowell_bianchi/06_integration_tests_spec.md` — 이 세션 스펙 전체
3. `docs/lowell_bianchi/README.md` §3 (dependency graph) + §6 (phase success criteria)
4. 참조 (LB-1..LB-5 완료물):
   - `bass_py/bass/hierarchy/integrator.py` — `LowellBianchiIntegrator.run` 본체 + `IntegrationResult` 구조체
   - `bass_py/bass/hierarchy/pack_unpack.py`, `aux_state.py`, `ic.py`, `neutrino_reduced.py`, `event_detection.py` — LB-5 infrastructure
   - `bass_py/bass/hierarchy/closure.py`, `bass_py/bass/collision/` — LB-3/LB-4
   - `bass_py/bass/species/`, `bass_py/bass/background/` — LB-1 + Y-Block
5. 참조 (LB-5 이 남긴 hooks):
   - `IntegratorAuxState.gamma_T_override` — deep-TCA regime probe (LB-6 high-z tests 에서 사용 가능)
   - `IntegrationResult.tca_active_mask` — η-range 별 TCA 활성 여부 post-processing
   - `IntegrationResult.critical_events` — `z_eq`, `z_star`, `eta_reion_midpoint`, `eta_today` 자동 계산
6. 참조: `lowell §6`, `Kolb §3.5`, `Baumann §3.10` (thermal history targets)

## LB-5 에서 확정된 사실 (LB-6 에 참고)

- **State layout fixed at spec §2.1**: `(a, Σ_+, Σ_−, Π_{0..L}, E_{0..L}, Δ_ν, q_ν, π_ν, G_3)` — 총 `(L+1)² × 2 + 7` 엔트리. LB-6 이 이 layout 을 존중해야 pack/unpack 유틸 재사용 가능.
- **CanonicalDecision 실제 배선**: `build_integrator_canonical_decision(beta, sigma_squared)` 가 real VT-07 β gate + Σ² floor + one-field tangency 를 wire. LB-6 integration 테스트는 이 decision 이 production 에서 fail하는 scenarios (unsafe β, sub-floor σ²) 를 pinning 해야 함.
- **TCA dispatch DAE-style**: `combined_rhs` 가 `Γ_T/H > threshold` 에서 Π_2 m=0 / E_2 m=0 슬롯을 relaxation rate `a × Γ_T` 로 algebraic 값에 peg. 실제 Planck-2018 HyRec fixture 는 이 threshold 를 넘지 않으므로 LB-6 에서 `gamma_T_override` test hook 을 사용해 dispatch branch 를 regression 테스트 필요.
- **η_reion ≈ 5100 Mpc @ z=7.67**: spec §5.3 / §10.5 I-17 에 LB-5 amendment 로 수정됨 (pre-LB-5 draft 의 13800 Mpc 은 arithmetic 오류). LB-6 Kolb-table regression 은 이 amended 값을 사용.
- **`einstein_bianchi` Σ-convention mismatch (F2)**: 현재 integrator 가 `Σ × a = const` 를 보존 (Ellis convention `Σ² × a⁴` 대신). LB-6 shear-decay 테스트는 einstein_bianchi convention 기준. 뒤집기는 post-LB-6 phase 에서.
- **외부 코드 가드**: `bass/validation/test_external_code_policy.py` 여전히 활성 — LB-6 신규 파일이 `import camb/classy/hyrec/aniclass` 하면 fail.

## 이 세션의 작업 (~400 LoC tests, 1 세션)

`06_integration_tests_spec.md §11` Implementation checklist 전체:

- **`bass/integration/test_lowell_bianchi.py`** 신규 (지금은 존재하지 않으므로 디렉토리 + module 생성 필요)
- 테스트 LB-6-01 ~ LB-6-24 (spec 참조)
- Kolb thermal history regression: z_eq=3400±50, z_*=1089.94±0.3, τ_reion=0.0544±0.0073, T_ν/T_γ=(4/11)^(1/3)
- CAMB geometry regression: η_* ≈ 13873 Mpc (distance-to-LSS), η_0 ≈ 14153 Mpc
- Bianchi I shear-decay invariant: `Σ × a = const` (F2 convention)
- Full-run smoke: full Planck-2018 FLRW run 끝까지 완주 + 모든 invariant pass + < 30 s wall time
- 실패 시 diagnostic playbook (spec §12) 적용: 각 실패 테스트는 정확히 한 LB-N 세션으로 역추적 가능해야 함

## LB-6 범위 제약 (고정)

- **integration tests only** — 새로운 production code 금지
- 기존 `LowellBianchiIntegrator` API 수정 금지 (LB-5 접점이 frozen 된 상태)
- 외부 CAMB/CLASS 를 **테스트 oracle 로** 허용 (scripts/generate_*_reference.py + test_*.py 한정) — 실제 wire 는 pre-computed fixture 만
- 테스트 실패가 프로덕션 버그 를 드러내면 → `AUDIT(LB-6): …` prefix 로 in-session 수선
- 테스트 실패가 spec target 오류를 드러내면 → spec 먼저 수정 후 테스트 조정

commit 메시지: `LB-6: Kolb thermal history + CAMB geometry regression pass`

## 핵심 원칙 (고정, 위반 시 PR 거부)

1. **외부 코드 금지** (프로덕션 트리 한정)
2. Citation in every test docstring (Kolb / Baumann / Planck 2018 참조)
3. PSTF invariants preserved throughout integration
4. No silent fallbacks
5. Determinism: 동일 IC + params → 동일 test outcome (RNG 금지)
6. **FLRW limit**: σ = 0 에서 Kolb-table 매치 필수

## 검증 체크리스트 (최종 commit 전)

- [ ] `PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` — 전체 회귀 green (baseline 2,534 이상)
- [ ] LB-6-01 ~ LB-6-24 모두 spec 수치 타깃 일치
- [ ] Full-range smoke integration (eta 0.5 → 14147 Mpc) 완주 + 모든 post-integration invariants pass
- [ ] 신규 테스트 LoC ≥ 25% coverage (integration tests are thin by nature — coverage via existing production code)
- [ ] **phase-boundary audit**: `docs/audits/AUDIT_PROMPT.md` 실행 후 `AUDIT_PHASE_LB6_<date>.md` 생성
- [ ] **gallery refresh**: 가능하면 신규 topic `12_thermal_history/` 에 Kolb-table comparison 플롯 추가 (optional — LB-6 은 tests 중심)
- [ ] **`NEXT_SESSION_PROMPT.md §2` 블록을 post-LB (옵션 A/B/C) 용으로 교체** (§4.6 템플릿)
- [ ] 최종 commit 메시지에 "+ rotate NEXT_SESSION_PROMPT" 라인 포함
- [ ] LB-6 전부 green 이면 `Phase LB complete: low-ℓ Bianchi solver bedrock verified` summary commit 도 추가 고려

## 진행 순서

1. LB-5 audit + LB-6 spec + `LowellBianchiIntegrator.run` + `IntegrationResult` 구조체 읽기
2. `bass/integration/` 디렉토리 생성, `__init__.py` + `test_lowell_bianchi.py` 스켈레톤
3. LB-6-01..08 (FLRW baseline: z_eq, z_*, τ_reion, η_* — LB-5 critical_events + species registry 직접 사용)
4. LB-6-09..16 (Bianchi I shear-decay regression — einstein_bianchi convention 기준)
5. LB-6-17..20 (TCA dispatch regression — gamma_T_override 로 deep-TCA regime 재현)
6. LB-6-21..24 (full-range smoke + CAMB geometry match — η_0 − η_* 정확도)
7. Gallery (optional)
8. 전 회귀 확인 → phase-boundary audit
9. `NEXT_SESSION_PROMPT.md §2` → post-LB bootstrap (옵션 A/B/C)
10. commit (+ optional "Phase LB complete" summary commit)

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
