# Next Session Bootstrap Prompt

Copy the fenced block below into a fresh Claude Code session to pick up
Phase LB implementation exactly where the design session ended. Update
this file after each session to point at the next concrete task.

**Last updated**: 2026-04-18 (design phase closed, implementation pending)

**Next task**: LB-0 closing guard test + LB-1 species background.

---

```
# Phase LB 구현 시작 — LB-0 마무리 + LB-1 species background

## 프로젝트 컨텍스트

- **Repo**: /home/cosmosapjw/Dropbox/bianchi/bass_phase1_snapshot_2026-04-18/bass_phase1_snapshot
- **venv**: venv/bin/python (pytest, camb, matplotlib, numpy, scipy 설치됨)
- **테스트 명령**: `cd bass_py && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
- **현재 baseline**: 2,027 tests passing (1,854 초기 + 105 B1 + 68 Y-Block)
- **설계 단계 완료**: 8개 spec 문서가 `docs/lowell_bianchi/`에 있음

## 우선 읽어야 할 문서 (순서대로)

1. `docs/lowell_bianchi/README.md` — 메타 인덱스, 세션 의존성 그래프, 불변량
2. `docs/lowell_bianchi/00_conventions.md` — signature/단위/PSTF packing/SSOT/Ellis↔bass_py 매핑/외부 코드 정책
3. `docs/lowell_bianchi/01_species_background_spec.md` — 이 세션의 직접 구현 스펙
4. (참조용, 필요 시) Y-Block 기존 모듈 — `bass_py/bass/background/tetrad_state.py`, `bass_py/bass/tilt/species_tilt.py`, `bass_py/bass/closure/quadrupole_tca.py`

## 이 세션의 두 가지 작업

### 작업 1 — LB-0 closing task (30분, ~50 LoC)

설계 문서 `00_conventions.md §11`과 `README.md §5`의 불변량 #3을 강제하기 위한 **외부 코드 의존성 가드 테스트** 1개 추가:

- 새 파일: `bass_py/bass/validation/test_external_code_policy.py`
- 동작: `bass_py/bass/`와 `bass_py/tsc/` 아래의 모든 `.py`에서 `import camb`, `import classy`, `import aniclass`, `import hyrec` 같은 외부 코드 import가 있으면 실패. `test_*.py`와 `bass_py/bass/recombination/fixtures/`는 예외
- 테스트가 실제로 guard 기능하는지 검증 (의도적 violation을 삽입해서 테스트가 catch하는 parametrize)
- commit 메시지: `LB-0: external-code policy guard test`

### 작업 2 — LB-1 species background 구현 (메인 작업, ~800 LoC + 600 LoC tests)

`docs/lowell_bianchi/01_species_background_spec.md`의 Implementation checklist (§9)를 그대로 따라가면 됩니다. 스펙에 있는 모든 것:

- Subpackage 레이아웃 (§2.1)
- `SpeciesBackground` ABC + 5 concrete classes (photon, neutrino, baryon, CDM, lambda)
- `SpeciesBackgroundRegistry` + `from_planck2018` factory
- `FLRWBackgroundTable` helper
- 25개 테스트 (T-01 ~ T-25, §8)
- Citation map (§10): 모든 public method는 Ellis/Kolb/Baumann 참조 docstring

LB-1 범위 제약:
- **Orthogonal Bianchi only** (tilted species extension은 LB-1b, 별도 세션)
- **Massive neutrino는 NotImplementedError** (m_nu_eV=0.0 hard default)
- **Integration은 없음** — LB-1은 analytic/interpolation 제공만. 실제 solve_ivp는 LB-5에서
- commit 메시지: `LB-1: species background evolution (γ, ν, b, c, Λ)`

## 핵심 원칙 (모두 위반 시 PR 거부)

1. **외부 코드 금지**: CAMB/CLASS/HyRec/AniCLASS는 `scripts/generate_*_reference.py`와 `test_*.py`에만. production code (`bass/*.py`)에 절대 import 안됨
2. **Non-perturbative everywhere**: β 처리는 sinh(β), cosh(β) 유지 (linearise 금지)
3. **Citation in every docstring**: 모든 public method/class에 Ellis §X.Y / Kolb §X.Y / Baumann §X.Y 인용
4. **PSTF tensors always symmetric-traceless**: `verify_pstf_invariants()` 통과
5. **No silent fallbacks**: 미구현 Bianchi type은 `NotImplementedError` raise
6. **FLRW limit test**: 모든 신규 모듈은 σ=0 한계에서 기존 테스트 재현

## 검증 체크리스트 (commit 전)

- [ ] `PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q` — 전체 회귀 green
- [ ] 신규 테스트 모두 spec 수치 타깃 일치 (T-01 ~ T-25 + 새 guard test)
- [ ] 스펙 §10 Cite map 준수 — 모든 public method에 citation docstring
- [ ] 스펙 §11 "What LB-1 does NOT do" 내용은 실제로 안 함 (범위 guard)
- [ ] 신규 LoC ≥ 25% 테스트 커버리지

## 진행 순서

1. `docs/lowell_bianchi/README.md`, `00_conventions.md`, `01_species_background_spec.md` 읽기
2. 기존 Y-Block 모듈 빠른 스캔 (`species_tilt.py`, `tetrad_state.py`, `ssot.py`)
3. 작업 1 (LB-0 guard test) → commit
4. 작업 2 (LB-1 species) 구현 — spec checklist 순서대로
5. 전체 회귀 확인 → commit

## 다음 세션 (이 세션 완료 후)

LB-2 (PSTF multipole hierarchy) — `docs/lowell_bianchi/02_multipole_hierarchy_spec.md`. 2 세션 소요 예상 (~1200 LoC).

시작하세요. 질문 있으면 중간에 멈추고 명확히 하기 먼저. 스펙과 다른 방향 제안 시에는 반드시 spec 문서를 먼저 수정한 뒤 구현.
```

---

## Maintenance notes for this file

**When to update**:
- After each LB-N session completes, replace the prompt body above with
  the next LB-(N+1) bootstrap prompt
- When `docs/lowell_bianchi/0N_*.md` gets significantly revised, update
  the "Priority reading" section to reflect new line references

**What to keep stable**:
- The top block (repo path, venv location, test command, regression
  baseline count)
- The "Core principles" list — these are phase-wide invariants, not
  session-specific
- The verification checklist — always identical in form

**Template for future sessions** (copy from this structure):

```
# Phase LB 구현 계속 — LB-N task_name

## 프로젝트 컨텍스트
(same as above but with updated regression count)

## 우선 읽어야 할 문서
1. README.md
2. 0N_<spec>.md
3. (Y-Block 또는 직전 세션 산출물)

## 이 세션의 작업
(single task or two tasks, matching the spec's Implementation checklist)

## 핵심 원칙 (6개, 위와 동일)

## 검증 체크리스트 (commit 전)

## 진행 순서
```

Always produce a prompt that is **self-contained**: a fresh agent with
zero prior context must be able to start from exactly that prompt
without hunting for information elsewhere.
