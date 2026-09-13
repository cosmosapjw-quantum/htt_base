# Research Loop — Deep Once GPT-6 Astra

한 번의 연속 실행에서 요청된 연구 산출물을 완성한다. `prompts/00_integrated_work_run.md`의 실행 계약을 따른다.

- core·현재 state·활성 증거 포인터를 읽고 필요한 phase만 추가한다.
- 문헌 지형, 가설 공간, 강한 대안, 실제 검산·판별 계산을 질문에 필요한 범위에서 수행한다.
- 탐색 후보·serious candidate를 고정 개수로 자르지 않는다. 수렴 시 원래 동기, 판별기준, 비용과 명시 예산을 함께 고려한다.
- 주 실행자가 자료를 통합하고 판정을 제안한다. 후보의 최종 PROMOTE는 후보 생성·검증 설계를 수행하지 않은 실제 독립 decision reviewer가 판정한다. 가용하지 않으면 `HOLD`와 `INDEPENDENT_REVIEW_UNAVAILABLE`을 기록한다. owner self review로 최종 독립 판정을 대체하지 않는다. claim ceiling을 유지하며 승인된 국소 탐색·계산·설계의 완료와 같은 범위의 보완은 계속한다.
- 근거 변화 없는 검색·재시도와 리뷰 재귀를 종료한다. 같은 scope의 evidence-driven 보완은 완료기준까지 수행한다.
- phase별 재승인 없이 기존 승인 범위에서 계속한다.

산출물은 audited evidence ledger, 필요한 가설 비교·유도·실행증거, 검토 상태, 결정과 closeout이다. 이미 있는 파일에 통합해도 된다. 모델간 품질·속도·비용 비교는 실제 matched run 전까지 `NOT_EVALUATED`다.
