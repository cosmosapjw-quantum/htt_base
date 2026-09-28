# Workflow

짧은 국소 연구는 `prompts/quick/ultralight.md`, 연속 연구는 `prompts/00_integrated_work_run.md`를 쓴다. phase 파일은 순서표가 아니라 필요한 작업을 위한 국소 계약이다. 완료된 phase를 되풀이하지 않는다.

1. 원래 동기·질문·탐색/수렴 모드·scope·완료기준·기존 승인을 복원한다.
2. 필요한 source를 취득하고 claim support를 확인한다.
3. 가설 공간과 강한 대안·null 설명을 비교한다. 진단용 유도는 이때도 한다.
4. 실제 독립 검토 여부를 명시하고 관련 물리·수학 조건을 검산한다.
5. 판별 검증을 설계하고 요청·승인·가용 범위에서 실행한다.
6. 발견된 오류를 같은 범위에서 수정하고 관련 기준을 충족할 때까지 검증한다.
7. 근거 수준에 맞는 결정을 기록하고 결과·실패·증거 포인터를 저장한다.

상태 검사가 통과한 다음 phase는 기존 승인에 따라 계속한다. gap이 생기면 관련 phase만 reopen한다. 신규 전면 review를 자동 반복하지 않는다. 최종 PROMOTE는 후보 생성·검증 설계를 수행하지 않은 실제 독립 decision reviewer가 판정한다. owner는 자료 통합·제안만 한다. reviewer가 없으면 `HOLD`와 `INDEPENDENT_REVIEW_UNAVAILABLE`을 기록하고 claim ceiling을 유지한다. 국소 탐색·유도·설계 완료나 승인된 보완까지 중단하지 않는다.
