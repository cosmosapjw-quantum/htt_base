# Phase 6 — Physics and Mathematics Validation

현재 판단을 바꿀 후보·claim에 대해 정의→전제→유도→중간 점검→극한/반례/차원 검사→결론을 재현 가능하게 남긴다. 근거 상태를 문헌·직접 유도·수치·구현으로 구분한다.

관련 검사: 표기, 단위, 부호·normalization, symmetry/covariance, conservation, known limits, initial/boundary conditions, convergence/regularity, positivity/realizability, gauge dependence, theorem assumptions, approximation order, validity regime. 기본 signature `(-,+,+,+)`; natural units를 정하지 않았다면 c, ħ, k_B 보존.

각 검사는 `PASS / CONCERN / FAIL / NOT_APPLICABLE / NOT_YET_TESTABLE`와 실제 근거를 갖는다. 자동 체크리스트 전 항목 실행을 요구하지 않는다. `NOT_YET_TESTABLE`은 PASS가 아니다.

fatal issue는 claim 승격을 막는다. 같은 scope의 최소 개념 수정은 필요한 만큼 수행하고 검산한다. 새 가정·보호된 의미 변화는 승인 경계를 확인한다. 최초 실패와 수정 후 결과를 모두 보존한다.
