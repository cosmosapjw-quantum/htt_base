# Integrated GPT-6 Astra Research Run

## 실행 계약

RESEARCH_GOAL: [요청된 산출물과 결정]
ORIGINAL_MOTIVATION: [보존해야 할 직관·의문·novelty 의도]
MODE: [exploration / convergence / local-validation]
PRIMARY_RQ: [현재 질문]
CURRENT_PHASE: [현재 단계]
SCOPE_AND_INVARIANTS: [이미 정한 범위·convention·claim ceiling]
COMPLETION_BAR: [완료를 관측할 수 있는 기준]
AVAILABLE_SOURCES_TOOLS: [실제로 접근 가능한 자료·계산·앱]
EXISTING_AUTHORIZATION: [승인된 수정·실행·게시와 예산]

이미 대화·파일에서 확인 가능한 항목은 다시 묻지 말고 채운다. 요청 범위 안의 합리적인 가정은 짧게 표시한다.

## 복원과 실행

`PROJECT_INSTRUCTIONS.md`, `state/RESEARCH_STATE.md`와 active evidence pointer부터 읽는다. stale summary를 새 실행 증거로 간주하지 않는다. 필요한 phase prompt·정책·source만 추가로 읽는다.

주 실행자가 상태와 통합을 소유한다. 서로 독립된 문헌 계보, 대안가설 검토, reviewer task만 구체적인 산출물과 함께 분리한다. source acquisition이 끝나야 그 source의 claim audit을 할 수 있다. 의존하는 유도·판정은 순차 실행한다.

필요한 단계는 연구계약→근거·claim audit→가설·검토→물리수학 검산→판별 검증 설계와 가능한 실제 실행→결정→정리다. 이미 완료된 단계를 반복하지 않고 현재 gap만 보완한다. 승인된 phase 전환마다 사용자 입력을 기다리지 않는다.

## 완료기준

1. 원래 동기와 대안 해석을 보존하고 수렴 결정을 scope·criterion으로 설명한다.
2. 핵심 claim에 원문/유도/수치/구현 증거와 근거 상태가 연결된다.
3. 승인·가용한 판별 계산을 실제 수행하고 raw evidence를 남긴다. 계획만 요구된 경우 그 범위를 표시한다.
4. independent review와 owner self review를 구분한다. 최종 PROMOTE는 후보 생성·검증 설계를 수행하지 않은 실제 독립 decision reviewer만 판정한다. owner는 제안·통합만 수행한다. reviewer가 없으면 `HOLD`와 `INDEPENDENT_REVIEW_UNAVAILABLE`을 기록하고 claim ceiling을 유지한다. 승인된 국소 계산·설계의 완료와 같은 범위의 보완은 계속한다.
5. 수정이 필요하면 같은 범위에서 완료기준까지 진행하고 최초 실패와 수정 이유를 보존한다.
6. `PROMOTE / HOLD / REJECT / REOPEN_*`, claim ceiling, state, closeout을 갱신한다.

종료 시 실제 완료 산출물과 증거, 근거별 결론, 남은 blocker를 전달한다. 표현 개선·리뷰 재귀로 실행을 늦추지 않는다. 모델 설정은 `docs/MODEL_ROUTING.md`를 따르며 성능 최적화의 실증 상태는 `NOT_EVALUATED`다.
