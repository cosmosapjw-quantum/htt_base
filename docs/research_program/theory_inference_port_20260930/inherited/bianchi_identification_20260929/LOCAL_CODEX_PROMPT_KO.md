# Local Codex 후속 연구 실행 프롬프트

이 패키지의 solver-free Bianchi 재탐색 결과를 local 수리·기호 연구로 이어가라. 먼저 REPORT_KO.md, CLAIMS.json, INDEPENDENT_DECISION.json, prior_audit.md, NEXT_TASKS.json을 읽어라. 계획 전체를 완료했다고 미리 보고하지 말고 가용한 작업을 실제 실행한 뒤 상태를 반환하라.

목표는 단일 Bianchi type을 반드시 출력하는 분류기가 아니다. 같은 완전 물리상태가 여러 simply-transitive action을 허용하면 그 집합을 보존하라. 충분한 입력이 있는 조건부 기하 복원과 sound outer prediction set에 의한 유형 배제를 구현·형식화하라. 실제 자료에서 full spatial tensor/derivative가 확보되지 않으면 BIC-07 HOLD를 유지하라.

현재 저장소의 AGENTS.md와 실제 branch/commit/tree를 읽고 지시를 따른다. 새 worktree를 만들지 말고 기존 dirty/untracked 변경을 보존한다. 이 패키지에 기록한 과거 pin을 최신 head로 간주하지 않는다. DB·원본 ZIP 삭제, 대용량 다운로드, 외부 Boltzmann solver, 무관한 production 개편은 범위 밖이다. 이 프롬프트 자체는 push/merge/외부 게시 권한을 새로 부여하지 않는다.

1. LOCAL-01의 convention/authority 계약부터 작성한다. Metric (-,+,+,+), c 명시, energy/mass density, shear full contraction, connection index order를 구분한다. Source u와 homogeneous normal N을 분리한다.
2. evidence/의 4개 WL을 bounded independent replay한다. 실제 Wolfram 버전·입력·출력·exit를 보존한다. 채팅에서 실행된 symbolic checks를 local 실행인 것처럼 재표기하지 않는다.
3. h와 simple-spectrum invariant T가 같은 G3를 보존하는 조건에서 Gamma와 bracket 복원을 일반식으로 검증한다. T=Ric와 T=sigma_N를 구분하고 eigenvalue gap이 사라질 때 분류를 유보한다. Arbitrary sky STF나 tilted-source shear를 T로 대체하지 않는다.
4. 모든 Bianchi 유형에 공통인 Lie/Jacobi/Gauss–Codazzi 제약에서 출발한다. Canonical type는 출력 label 또는 대조 예일 뿐 선험적 물리 class 선택이 아니다. Continuous h parameter와 III 등 명칭 convention을 등록한다.
5. Polynomial/interval outer set의 실제 포함성을 증명하고, 배제에는 검증 가능한 공집합/분리 인증서를 요구한다. Singular ideal 계산이나 optimizer 실패만으로 실수 부등식 feasibility를 결정하지 않는다. Nonempty jet set는 전체 Einstein 해의 존재 증명이 아니다.
6. 관측단은 낮은 z 거리 slope와 absolute position drift를 우선한다. Frame spin, source transverse motion, selection, distance/time remainder, 공동 covariance를 누락하지 않는다. 실제 입력이 없는 redshift drift나 공간미분을 만들지 않는다. 상대 각거리만으로 공통 vorticity를 복원하지 않는다.
7. 기존 x/Q/F/Pi/G_F 정의와 physical fibre를 계승한다. Gauge·signed margin을 유형 posterior로 이름만 바꾸지 않는다. Probability는 실제 joint law와 calibration에서만 얻는다.
8. Lean은 set inclusion/coverage, 동일 full-law fibre, 유한차원 대수의 좁은 증명부터 진행한다. 기존 Lean 범위보다 강한 전체 물리 정리를 검증했다고 보고하지 않는다.

NEXT_TASKS.json의 독립 가지는 병렬로 할 수 있다. 고차 accelerated cosmography의 sign errata 작업은 선도 geodesic 결과와 분리한다. 과학적 실패, 구현 오류, 환경 오류를 구분하고 최초 증거를 보존한다. 이미 해결된 검토를 반복하는 대신 미확보 입력과 실제 판별 계산을 처리한다.

반환물: RETURN_HANDOFF_KO.md, RETURN_STATUS.json, 실행 원 로그, 사용 버전/commit/tree, 변경 파일 목록, MANIFEST.sha256. 반환 상태에는 이론 유도·symbolic replay·형식 kernel·관측 적합을 각각 별도 표시한다. I2 DEFENDED_CONDITIONAL 및 I3 HOLD_INPUT_INCOMPLETE는 해당 결손이 실제 해소되고 독립 판정이 있을 때만 변경한다.

완료 기준: 현재 가능한 이론/기호 작업을 실행하고, 각 후보가 어떤 실제 입력으로 배제·복원 가능한지와 어떤 부분이 아직 missing인지 분리하여 반환할 것. 실제 우주의 Bianchi 유형을 억지로 선택하지 말 것.
