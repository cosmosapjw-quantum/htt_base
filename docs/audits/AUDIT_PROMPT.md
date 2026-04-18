# Phase-boundary integrated phys-math-code audit prompt

**Purpose**: run this audit at the end of every Phase (LB-0, LB-1, …,
LB-6; post-LB A/B/C) before the phase-boundary commit. Produces a
fixed-format audit report at
`docs/audits/AUDIT_PHASE_<tag>_<YYYY-MM-DD>.md` with the verdict and
the repair-plan checklist.

**Trigger**:

* Manual: paste the prompt below into a fresh Claude Code session
  after the last phase commit lands on `main`.
* Automated (optional): register a `pre-push` git hook or
  `settings.json` `Stop` hook that invokes the prompt (see
  "Auto-trigger setup" at the bottom of this file).

**Non-negotiable rules** that must survive every audit rotation:

1. Do not propose framework swaps, mass refactors, or structural
   aesthetics fixes as the primary response.
2. Do not conflate "the equation is correct" with "the code
   implements it" with "the numeric result is trustworthy".
3. Always restore the contract/mapping first, then find failure
   modes, then propose the *smallest* patch that removes the most
   risk.
4. A spec claim is not implementation evidence. A smoke test is not
   validation. A passing test whose default mode is tautological is
   not a passing test.

## The prompt (paste verbatim)

```text
[INTEGRATED PHYS-MATH-CODE AUDIT]

목표:
새 아이디어를 내지 말고,
주어진 수식/증명/알고리즘/코드/수치 파이프라인 사이의 깨진 고리를 찾는 데 집중하라.
즉,
(1) 물리/수학적으로 맞는지,
(2) 그 내용이 코드에 정확히 구현되었는지,
(3) 수치적으로 신뢰 가능한지
를 한꺼번에 감사하라.

핵심 원칙:
- “수식이 맞다”와 “코드가 그 수식을 구현한다”와 “수치 결과가 믿을 만하다”를 절대 같은 것으로 취급하지 마라.
- 구현 미화, 구조 미화, 프레임워크 교체를 기본값으로 제안하지 마라.
- 먼저 contract와 mapping을 복원하고, 그 다음 오류와 failure mode를 찾고, 마지막에 최소 수정안을 제시하라.
- 필요한 경우에만 python으로 toy check / 차원 check / regression sketch / numerical sanity check를 수행하라.

우선 전략:
RE2 + Self-Ask + 물리 verifier + 코드 verifier (+ python/files 필요 시)

감사 순서:
STEP 0. AUDIT TARGET RECONSTRUCTION
- 먼저 아래를 분리해서 재구성하라:
  1) 핵심 물리/수학 주장
  2) 그 주장을 구현해야 하는 알고리즘/연산
  3) 실제 코드/파이프라인이 생산하는 출력
- 가능하면 “식/정의 → 변수/상태 → 함수/모듈 → 출력/테스트”의 대응표를 만들어라.
- 수식, 코드, 결과 중 무엇이 source of truth인지 명시하라.

STEP 1. CONTRACT / INTERFACE AUDIT
반드시 먼저 아래 contract를 복원하라.
- 입력/출력 정의
- 상태변수 의미
- shape/type
- units/dimensions
- normalization / sign convention
- domain / admissible range
- boundary / initial conditions
- expected invariants / conservation / positivity
- solver assumptions / regime assumptions
- test oracle / baseline expectation
여기서 contract가 불명확하면 그것 자체를 P0 또는 P1 문제로 간주하라.

STEP 2. PHYS-MATH AUDIT
다음 순서로 점검하라.
1) 정의/표기 충돌
2) 인덱스/trace/PSTF/projection 일관성
3) 부호/정규화
4) 단위/차원
5) known limit / baseline recovery
6) 경계조건/정칙성/positivity
7) 숨은 가정
8) 반례 special case
각 항목마다:
- 통과 / 의심 / 실패
- 왜 그런지
- 코드에 미치는 영향
을 적어라.

STEP 3. EQUATION-TO-CODE MAPPING AUDIT
다음을 반드시 점검하라.
- 핵심 식/정의가 코드 어디에서 구현되는가?
- 이름만 비슷한데 실제론 다른 quantity를 쓰고 있지 않은가?
- 수식의 approximation/regime이 코드에서 분명히 반영되는가?
- 본문 claim과 실제 구현 path가 어긋나지 않는가?
- dead code / placeholder / unused parameter / disconnected module이 있는가?
- reduced model / surrogate / helper path를 production path처럼 오해하고 있지 않은가?

STEP 4. NUMERICAL / PIPELINE AUDIT
다음을 점검하라.
- solver suitability (stiff/nonstiff, implicit/explicit, quadrature/Jacobian usage)
- tolerance sensitivity
- underflow / overflow / cancellation / negative states
- conditioning / instability / divergence
- interpolation / tabulation artifacts
- warm-start / cache / state leakage
- seed / reproducibility / determinism
- OOD / misspecification 위험
- postprocessing dependence
- baseline reproduction path 존재 여부
가능하면 “이건 물리 오류인지, 구현 오류인지, 수치 오류인지, diagnostics 오류인지” 분류하라.

STEP 5. FAILURE MODE SYNTHESIS
failure modes를 최대 7개로 정리하라.
각 failure mode에 대해:
- 유형: physics / math / implementation / numerical / interface / testing
- 심각도: P0 / P1 / P2 / P3
- 관측 증상
- 근본 원인
- 가장 싼 판별 테스트
- 잘못된 해석 위험
를 적어라.

STEP 6. VERIFIER FILTER
반드시 아래 verifier를 적용하라.
A. Physics verifier
- known limit recovery
- dimensional consistency
- sign/normalization consistency
- positivity / admissibility
- alternative explanation 가능성
B. Code verifier
- contract satisfaction
- actual code-path usage
- regression risk
- reproducibility
C. Numerical verifier
- tolerance robustness
- convergence / stability
- baseline reproducibility
- uncertainty / misspecification awareness
각 verifier별로:
- passed / partial / failed
를 판정하라.

STEP 7. MINIMAL REPAIR PLAN
대규모 리팩토링을 금지하고,
가장 적은 수정으로 가장 큰 신뢰성 향상을 주는 패치만 3개까지 제안하라.
각 패치에 대해:
- 무엇을 바꾸는가
- 왜 이 패치가 load-bearing한가
- 어떤 failure mode를 막는가
- 새로 필요한 테스트
- baseline / regression 영향
을 적어라.

STEP 8. MINIMAL TEST SET
바로 실행 가능한 최소 테스트 셋을 설계하라.
반드시 포함:
- baseline reproduction test 1개
- edge / adversarial test 1개
- physics sanity test 1개
- numerical stability or sensitivity test 1개
- regression test 1개
테스트마다 pass/fail 기준을 적어라.

금지:
- 프레임워크 전면 교체를 기본값으로 제안
- 대규모 리팩토링부터 요구
- 실제 bug/contract 문제를 architecture aesthetics로 덮기
- 수식 재서술만 하고 코드 path를 확인하지 않기
- smoke test를 validation으로 인정하기
- 논문/문서 claim을 구현 증거로 취급하기

출력 형식:
1) Audit target reconstruction
2) Contract/interface table
3) Phys-math audit ledger
4) Equation-to-code mapping audit
5) Numerical/pipeline audit
6) Ranked failure modes (P0~P3)
7) Verifier results
8) Minimal repair plan
9) Minimal test set
10) 최종 판정:
   - 치명적 오류 있음 / 부분 통과 / 통과
   - 지금 당장 구현/수정할 1개
   - 지금 손대면 안 되는 1개

(오류 하나 나왔다고 바로 종료하지 말고 계속 이어서 모든 오류들을 다 찾아내라)

세션 종료 시:
- 발견된 P0/P1 오류는 같은 세션에서 최소 수정안대로 구현하고 테스트
  추가하여 commit하라. commit 메시지 prefix는
  `AUDIT(<phase-tag>): <short>`.
- P2/P3 오류는 `docs/audits/AUDIT_PHASE_<tag>_<date>.md`에 기록만
  하고 다음 phase prerequisite에 추가한다.
- `docs/lowell_bianchi/NEXT_SESSION_PROMPT.md §1`에 "Last audited:
  <date>" 를 추가 갱신한다.
```

## Auto-trigger setup (optional)

To have Claude Code fire the audit automatically whenever a phase
completes, add to `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "commit.*Phase.*complete|rotate NEXT_SESSION_PROMPT",
        "command": "echo 'PHASE BOUNDARY DETECTED — run /audit before closing session.'"
      }
    ]
  }
}
```

The hook is advisory (prints a reminder). A strict pre-push
enforcement would instead register a git hook
`.git/hooks/pre-push` that invokes
`venv/bin/python -m bass.validation.audit_phase --tag <current>` —
this is deferred until a post-LB-6 CI/DevOps rotation.

## Audit log

Each run writes one file at `docs/audits/AUDIT_PHASE_<tag>_<date>.md`
containing:

* Header: phase, commit SHA, baseline test count, run date
* §1–§10 of the prompt output
* Patch diffs (or commit SHAs) for P0/P1 fixes applied in the same session
* Outstanding P2/P3 items carried forward

See `AUDIT_PHASE_LB1_2026-04-18.md` for the first reference log.
