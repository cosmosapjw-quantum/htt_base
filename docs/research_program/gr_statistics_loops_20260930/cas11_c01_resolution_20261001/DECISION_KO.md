# C01 입력 차단 정정과 후속 계약 제안

소유: `research_program`. 범위: 유한 Bregman 성분의 실행 준비. `claim_tier=non_claim_bearing`, `transfer_source=none`.
기준 commit: `2423cb6a362e43a844462cad63605a5955fe2e4d`, tree: `549b21242bc3c574d4ae1edf09ab57f93cb0792e`.

## 현재 결정

C01 v3는 실행 전 차단 상태를 유지한다. 이전 인계에서 원 v3를 고정하면서 별도 `NEUTRAL_AXIS_BRIEF.md`를 요구한 것은 현재 지원된 입력 허용 경로로 실행할 수 없는 준비였다. 이 추가 brief를 요구하는 실행 경로를 철회한다. 원 계약과 이전 인계는 역사적 기록으로 보존한다.

brief를 제외해도 자동으로 재개할 수는 없다. v3는 moment matching의 정확한 조건을 정의하지 않은 채 교차항 소거를 요구한다. 네 허용 외부 입력에도 C01의 gradient-span 조건이 명시되어 있지 않다. 부모 CAS-11의 `/semantics/exact_statement/0`에는 그 조건이 있지만, 부모 계약은 v3의 출처 해시 목록에만 있고 작성자 허용 입력 목록에는 없다. 출처 해시와 작성자 열람 허용은 다르다. 그 내용을 축 프롬프트에 옮겨 넣는 방식으로 제한을 우회하지 않는다.

저장소 runner에서 확인한 `exceptions_adjudication.preregistered_exceptions`는 축 예외를 처리한다. supplemental source input 허용 인터페이스로 확인된 것이 아니다. 입력 제한의 코드 강제가 보이지 않는다는 이유로 목록을 열린 것으로 취급하지 않는다.

사용자가 전달한 로컬 반환에 따르면 reviewer 등록은 실제 `gpt-6.1-sol/high`를 처리하지 못해 `REVIEW_HIERARCHY_UNSATISFIED`로 종료했다. 로컬 authority와 원시 로그는 여기서 읽지 못했다. 실제 모델을 다른 이름으로 대체하거나 지원되지 않는 tier를 지정하지 않는다. 이 문서의 게시로 입력 차단이나 라우팅 차단이 해결되었다고 주장하지 않는다.

## 제안하는 유한 명제

검토 가능한 후보는 [C01_SUCCESSOR_PROPOSAL.json](C01_SUCCESSOR_PROPOSAL.json)의 `proposed_contract`에 있다. v3를 수정하는 예외가 아니라, 별도 정체성을 가진 **미승인 version 4 제안**이다. 기존 run/task `GRSTAT-CAS11-C01-20261001T031553Z`와 비용·실패 이력을 계승하는 지원 절차가 확인되어야 한다.

유한 차원 실벡터공간 \(E\), 공통 열린 정의역 \(U\), \(f,g,h\in U\), 이 점들에서 미분 가능한 \(\Phi:U\to\mathbb R\)를 둔다. 미분 \(d\Phi(y)\in E^*\)와 쌍대 평가를 이용하여

\[
D_\Phi(x\Vert y)=\Phi(x)-\Phi(y)-\langle d\Phi(y),x-y\rangle
\]

를 정의한다. 첫 번째 검증 대상은 별도 moment 조건 없이 성립하는 세 점 항등식이다.

\[
D_\Phi(f\Vert g)=D_\Phi(f\Vert h)-D_\Phi(g\Vert h)
+\langle d\Phi(h)-d\Phi(g),f-g\rangle.
\]

두 번째 대상은 선형 사상 \(M:E\to\mathbb R^m\), 공변벡터 \(\lambda\in(\mathbb R^m)^*\), 쌍대 사상 \(M^*\)에 대해

\[
M(f-g)=0,\qquad d\Phi(h)-d\Phi(g)=M^*\lambda
\]

라는 **두 전제** 아래 교차항이 사라진다는 함의다. 소거 결론 자체를 전제로 쓰지 않는다. 볼록성, 내적, Lorentz norm, Hessian bound는 이 두 유한 목표의 전제가 아니다. 차원 0, \(m=0\), 영 사상과 rank 결손 사상도 범위에 포함한다.

공통 열린 정의역과 Fréchet 미분을 지정하는 것은 이번 후보의 명시적 선택이다. 모호한 v3의 모든 가능한 해석과 동치라고 주장하지 않는다. 이 문서는 목표만 제시하며 축별 증명이나 CAS 판정을 제공하지 않는다. 각 축은 임의 유한 차원의 양화와 미분·좌표 해석의 연결을 스스로 입증해야 한다.

후보는 계약 자체와 기존 네 외부 중립 입력만을 허용한다. 이 설명 문서, proposal wrapper, 이전 brief, Host 풀이, 부모 결과를 축 작성자에게 주지 않는다. 승인·봉인 이후 추출한 동일 계약만 네 축에 제공한다.

## 필요한 결정과 남은 작업

| 선택 | 현재 가능한 일 | 판정 |
| --- | --- | --- |
| v3만 유지 | 차단 기록을 보존하고 지원된 입력 허용 절차를 기다림 | 현재 실행 경로 없음 |
| v4 후보 채택 | 사용자의 명시적 채택 후 지원된 동일 task 계약 갱신·봉인 절차를 확인 | 권장; 아직 실행 승인 아님 |
| 로컬 라우팅 수리 | 현재 authority의 지원된 모델 등록/parent-decision 절차로 실제 저자 모델을 처리 | 별도 필수 전제; 여기서는 미해결 |

원 v3 및 로컬 기록 보존 요구 때문에 v4 채택은 별도 결정이 필요하다. 자동으로 예외를 만들거나 v3의 허용 목록을 고치지 않는다. `C01_SUCCESSOR_PROPOSAL.json`은 proposal wrapper이므로 runner에 전달하지 않는다. 이 주의문은 runner가 기술적으로 실행을 거절한다는 시험 결과가 아니다.

사용자가 제공한 반환은 기계 판독 파일에 **사용자 보고 요약**으로 기록했다. 원 로컬 `RETURN.json`의 바이트를 복원하거나 그 raw manifest를 검증했다는 뜻이 아니다. 실제 로컬 반환과 raw의 보존·게시는 [다음 인계](LOCAL_CODEX_HANDOFF_KO.md)에서 다룬다.

C02/C03는 재실행하지 않는다. C04 launch `cl_000fce20034122657b6cdf509703df23`, R9, 이전 실패·비용 기록, 사용자 변경은 보존한다. CAS-11/CAS-13 전체, 연속체 해석, 실제 entropy budget 및 관측 연결은 계속 열려 있으며 과학적 conditional/HOLD는 유지된다.
