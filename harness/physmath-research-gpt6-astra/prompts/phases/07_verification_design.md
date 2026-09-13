# Phase 7 — Decisive Verification Design and Execution

testable claim, required input, 후보와 강한 경쟁자의 예측, pass criterion, kill criterion, ambiguity condition, 최소 판별 작업, 비용·예산, escalation path를 적는다. tolerance·baseline을 결과를 본 뒤 유리하게 바꾸지 않는다.

요청이 계획 작성에 한정되면 실행을 수행했다고 주장하지 않는다. 실제 연구 수행 요청이며 작업이 승인·가용하다면 설계 후 계산·관측 비교·문헌 확인을 수행한다. 코드 개발이 필요한 경우 `docs/MODEL_ROUTING.md`의 대응 coding harness를 사용하되 연구계약과 불변조건을 유지한다.

실행 증거: source identity, 입력·초기조건, runtime/정밀도, 정확한 command 또는 notebook cell, actual exit, raw stdout/stderr, 수치 오차·수렴 및 관측량의 관련 한계. 수치 일치는 증명이나 일반 유효성으로 승격하지 않는다.

실패는 이론/수치해석/구현/runtime·환경/권한·정책으로 구분한다. 같은 범위에서 증거 기반 보완을 완료한다. 실제 blocker면 실행되지 않은 부분과 필요한 최소 조건을 보존한다.
