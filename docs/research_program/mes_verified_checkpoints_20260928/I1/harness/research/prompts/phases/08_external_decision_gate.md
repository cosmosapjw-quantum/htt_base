# Phase 8 — Independent Decision Gate

`external`은 후보 생성·검증 설계와 분리된 실제 decision reviewer를 뜻하며 새 외부 게시나 사용자 승인 요청을 뜻하지 않는다. 원본의 독립 판정 조건을 유지한다. owner는 근거를 통합하고 판단을 제안할 수 있으나 자신의 후보를 최종 PROMOTE로 승인하지 않는다.

후보 생성과 검증 설계를 수행하지 않은 실제 독립 decision reviewer가 최종 PROMOTE 판정을 한다. reviewer identity, 검토한 고정 후보와 원본 증거, 독립성의 범위와 판정 근거를 남긴다. 단순 역할 전환이나 `OWNER_SELF_REVIEW`는 이 gate를 충족하지 않는다. reviewer가 없으면 `HOLD`와 `INDEPENDENT_REVIEW_UNAVAILABLE`을 기록하고 claim ceiling을 유지한다.

후보별 `PROMOTE / HOLD / REJECT / REOPEN_EVIDENCE / REOPEN_HYPOTHESIS / REOPEN_VALIDATION`의 근거를 기록한다. evidence, physical/math validity, novelty, testability, robustness, tractability, assumptions, original motivation의 보존 여부를 개별 검토한다. 근거 없는 aggregate score를 사용하지 않는다.

PROMOTE는 명시한 다음 연구/보고 단계에 한정한다. claim–evidence 연결, 관련 fatal issue 부재, 대안과의 구분, 해당 단계의 실제 완료기준, scope·불확실성·검토 상태와 독립 판정을 요구한다. 설계 완료와 실험 성공을 구분한다.

이 gate는 최종 후보 승격에 적용한다. 승인된 국소 탐색·진단 유도·검증 설계의 완료, 실제 계산, 같은 scope/invariants 안의 증거 기반 correction을 모두 독립 reviewer 대기로 바꾸지 않는다. reviewer가 없어도 해당 작업을 완료하고 미승격 상태로 결과를 전달할 수 있다.

결정 근거·반대 결과·claim ceiling·남은 gap을 `DECISION_LOG`에 기록하고 승인된 다음 작업을 계속한다.
