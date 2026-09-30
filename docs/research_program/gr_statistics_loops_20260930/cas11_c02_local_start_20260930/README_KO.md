# 새 local Codex 세션: CAS11-C02 유한 Gram 검증

다음 실행 단위는 **CAS11-C02 version 3의 순방향 정리**다. 이 패키지는 기존 정리의 새 로컬 검증을 준비한다. 새 CAS 실행이나 형식 증명 PASS를 포함하지 않는다. C04 reviewer launch의 identity 문제는 별도 운영 차단으로 보존하며, C02의 수학적 전제가 아니다.

임의의 양의 정수 `n`, 실대칭 양의 준정부호 행렬 `R`, 실벡터 `e`, `ε≥0`에 대해 다음을 검증한다.

\[
\left[\forall a\in\mathbb R^n:\ |a^Te|^2\le 2\varepsilon a^TRa\right]
\Longrightarrow
\left[e\in\operatorname{range}R,\quad e^TR^\dagger e\le2\varepsilon\right].
\]

`R†`는 원 계약의 실대칭 Moore–Penrose 의사역행렬이다. 모든 유한 차원과 모든 rank, 영행렬, 특이 비영행렬, `ε=0`을 포함한다. 원 계약의 PSD 결론은 이미 주어진 PSD 가정을 반복한다. 이 계약은 실제 물리적 잔차 Gram 구성의 타당성을 새로 증명하지 않는다.

## 읽기와 실행

새 스레드의 Host는 [LOCAL_CODEX_START_KO.md](LOCAL_CODEX_START_KO.md)를 먼저 읽는다. 단계와 실행기 인터페이스는 [EXECUTION_PLAN.json](EXECUTION_PLAN.json), 입력 위치·해시는 [INPUT_RESOLUTION.json](INPUT_RESOLUTION.json)에 있다. [HOST_COVERAGE.md](HOST_COVERAGE.md)는 Host와 사후 reviewer용이며, 독립 축 작성자에게 전달하지 않는다.

축 작성자에게는 [원 계약](contracts/CAS11-C02-FINITE-GRAM.json), [NEUTRAL_AXIS_BRIEF.md](NEUTRAL_AXIS_BRIEF.md), 원 계약이 허용한 중립 입력만 전달한다. Host의 기존 Gram 유도나 다른 축의 소스·결과는 adjudication 전까지 차단한다. 반환은 [LOCAL_RETURN.schema.json](LOCAL_RETURN.schema.json)에 맞춘다.

## 재개에 필요한 실제 로컬 입력

동결 계약 SHA-256: `c66d7d00bf60786417336873dfeb97f5602d0e60a110c110ebacd9dff824b47a`.
이 패키지의 계약 파일은 이미 게시된 version 3 원문을 바이트 그대로 복사했다.

원 계약이 가리키는 `local_cas/GRSTAT-CAS-CORR-20260930-1420KST/contracts/NEUTRAL_PROPOSAL.json`은 이 패키지에 없다. 사용자 로컬의 보존 원본에서 SHA-256 `2ad07222bd0231cb778d08d9a6430952595561dd561529352a88a88fc0fe7534`를 확인해야 한다. 없으면 `BLOCKED_INPUT_MISSING`으로 반환하며 설명문으로 재구성하지 않는다.

환경 원본 `CAS_ENVIRONMENT.json`은 역사적 기록이다. 그 안의 이전 Lean probe timeout을 새 실행의 실패로 복사하지 않는다. 원본을 유지하고 현재 고정 toolchain의 실제 관측을 새 run에 남긴다. 당시 고정 Lean은 `leanprover/lean4:v4.31.0`이었다. 로컬의 `formal/lean-toolchain`, 실제 사용할 mathlib 프로젝트와 lock의 관계를 확인한다.

## 이번 세션의 종료 기준

준비 확인에서 멈추지 않고, 지원된 실행 경로가 있으면 축별 소스 작성과 실제 `run-adjudicate` 실행까지 진행한다. 종료 결과는 실행 근거와 범위 판정, 또는 정확한 입력·증명·환경·정책 blocker다. 네 축 전체의 근거가 닫히지 않으면 전체 PASS를 만들지 않는다. 등록 reviewer의 완료 여부는 CAS aggregate와 별도로 기록한다.

C02 성공 후 다음 별도 단위는 C03의 가중 사영·Gram 연결이다. 이어서 물리적 오차 표현과 예산 상계를 다룬다. C02만으로 C01/C03, 연속체 Taylor/Hessian 단계, 관측 likelihood 또는 CAS-11 전체를 승격하지 않는다. 역방향 동치 확장도 이번 실행 범위에 넣지 않는다.

이번 준비 패키지는 관련 문서·계약 사본만 추가한다. C04 차단 기록, 원 계약, 기존 소스·실패 기록과 production 코드를 바꾸지 않는다. 원격 게시 뒤 R1과 고정 commit을 인계한다. 복구가 필요하면 이 문서 추가 commit을 revert하며 이전 기록을 덮어쓰지 않는다.

준비 검사는 계약 사본의 SHA-256·바이트 동일성, JSON 파싱, 상대 링크 7개, Draft 7 schema 및 합성 정상 사례 2개·변조 사례 10개의 수용/거절 동작을 확인했다. 검증기는 scratch에만 설치한 `jsonschema 4.25.1`이다. 별도 읽기 전용 준비 검토에서 blocker는 없었고, 완료 선언 시 실행 근거 누락을 막는 schema 보완을 반영했다. 이 검사는 실제 CAS, Lean 컴파일 또는 등록된 과학 reviewer의 완료 근거가 아니다.
