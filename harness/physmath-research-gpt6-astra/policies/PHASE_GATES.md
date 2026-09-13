# Phase gates

phase gate는 해당 증거와 완료기준을 검사하는 지점이다. 사용자 승인 checkpoint와 동일하지 않다. 현재 승인된 목표의 다음 필수 phase는 상태를 기록한 뒤 계속 실행한다.

- 연구계약: 원래 동기, 질문, 탐색/수렴 모드, scope, convention, 완료기준을 확인한다.
- 근거: 필요한 claim에 직접 근거가 있거나 gap과 그 영향이 명시된다. `UNSUPPORTED`/`MISATTRIBUTED`를 사실 전제로 사용하지 않는다.
- 가설: 실질적 대안과 null 설명, 판별가능성이 기록된다. 고정 후보 수로 탐색을 자르지 않는다.
- 검토/검산: relevant 물리·수학 조건을 확인하고 실제 독립 검토 여부를 밝힌다. 진단용 유도·계산은 승격 전에도 허용한다.
- 검증 실행: 설계만 필요한 요청이면 설계로 닫는다. 실제 연구 수행 요청이며 계산이 승인·가용하면 실행 증거를 산출한다. unavailable이면 `blocked`와 최소 해소 조건을 기록한다.
- 결정: claim별 scope·근거·fatal issue·검토 상태에 따라 `PROMOTE / HOLD / REJECT / REOPEN_*`를 기록한다. 최종 PROMOTE 판정은 후보 생성·검증 설계를 수행하지 않은 실제 독립 decision reviewer가 한다. owner는 근거를 통합하고 판정을 제안할 수 있으나 스스로 승격을 승인하지 않는다. PROMOTE는 명시한 다음 연구/보고 단계로의 승격이지 가설의 사실 확정이 아니다.
- 정리: 근거보다 높은 claim으로 승격하지 않는다. 최종 독립 decision reviewer가 없으면 `HOLD`와 `INDEPENDENT_REVIEW_UNAVAILABLE`을 기록하고 해당 claim ceiling을 유지한다. 승인된 국소 탐색·유도·검증 설계의 완료와 같은 범위의 correction은 계속할 수 있다.

부족한 항목만 reopen한다. 이미 완료된 전체 cycle을 반복하지 않는다. state에는 변경된 판단과 evidence pointer를 저장한다.
