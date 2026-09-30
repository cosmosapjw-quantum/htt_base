# Local Codex: C04 두 미완료 축의 보편 인증 마무리

ROLE=LOCAL_C04_CERTIFICATE_EXECUTOR
PROJECT=htt_base
SOURCE_RUN=GRSTAT-CAS-CORR-20260930-1420KST
SOURCE_PUBLICATION_COMMIT=11602167b64e4f0c50c1f57c37fe9df2292f9725
EXACT_COMPONENT=CAS13-C04-RELATIVE-MINIMAX
CONTRACT_SHA256=0002809c73fd5de362deded39735fe884183bb953029f671552a525f74086f63

첨부 FOLLOWUP_REPORT_KO.md, C04_CERTIFICATE_THEOREM.md, 두 축의 SCOPE 문서와 소스를 읽고 C04 한 건만 끝내라. 목표는 SymPy·Sage의 기존 부분 인증을 동일 원자 명제의 일반 인증으로 보완하는 것이다. 새로운 이론 가정을 넣거나 다른 17개를 재실행하지 않는다.

## 원본과 실행 범위

- 현재 checkout의 AGENTS.md, CAS runner schema, 환경을 읽고 dirty/untracked 변경을 보존한다. 새 clone/worktree/reset을 만들지 않는다.
- 원 계약은 `docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-CORR-20260930-1420KST/contracts/CAS13-C04-RELATIVE-MINIMAX.json`이다. 위 hash와 일치해야 한다.
- 원 run·version 1/2/3 계약·raw verdict·실패·timeout 기록은 덮어쓰지 않는다. 새 run 폴더를 만든다. 수학적 계약을 바꾸지 않는 소스 보완이다. 환경이나 허용 입력을 바꿔야 한다면 새 identity를 기록하고 기존 결과와 구분한다.
- 두 새 작성자는 동일 target만 받은 별도 작업자였으며, 독립 모델 증거는 없다. 사용되는 공통 수학과 orchestrator의 source exposure를 기록한다. 이전 Lean 증명을 새 독립 저자 증명이라고 표기하지 않는다.

## 실행할 내용

1. 새 폴더에 `c04_sympy_certificate.py`, `c04_sage_certificate.py`를 배치한다. 두 파일은 `--contract <원 계약 경로>`로 hash를 고정한다. `--self-test` 지원과 정확한 실행법은 각 SCOPE 문서를 따른다.
2. 실제 local SymPy 환경과 SageMath/Singular에서 자체 변조 거절 검사를 실행하고 raw stdout/stderr·argv·exit·version을 저장한다. 범위 검사 또는 인증 규칙이 실패하면 해당 코드를 고치고 같은 목표 안에서 재검증하라. `domain_assumption_diff`를 비우거나 false 결과를 상수 true로 바꾸는 방식으로 통과시키지 마라.
3. 보편성 연결을 직접 확인한다: 0<L≤U, 전 구간 x, L=U, 모든 실수 경쟁자 a, 양의 분모, 두 endpoint 달성, 절댓값/최댓값에서 얻는 부등식. 유리수 예제나 endpoint 대입은 일반 증명의 대체물이 아니다.
4. Sage/Singular가 다항식 인증에 실제 기여했는지 확인하고, 임의 다항식을 자기 자신으로 나눈 나머지를 과학 인증으로 기록하지 않는다. 명제-인증서 연결과 작은 order-rule checker는 별도 신뢰 경계임을 적는다.
5. 새 runner spec에 두 새 프로그램을 넣고, 기존 C04의 Wolfram·Lean 소스는 바이트를 보존하여 새 실행 위치에 복사한다. 그 스크립트의 repo-root 계산과 cwd를 확인한다. Lean은 `formal_mathlib`와 저장소 고정 `leanprover/lean4:v4.31.0`을 사용한다. 비고정 `lean --version` timeout을 반복하지 않는다.
6. 이 C04 한 건의 네 축을 `run-adjudicate`로 실제 관측한다. 기존 raw log를 새 실행으로 재사용하지 않는다. 실행 오류·파싱 실패는 수학적 반례와 구별한다.
   두 보완 프로그램은 인증 거절·실행 실패 시 stdout target Boolean을 내지 않고 비영 종료한다. 이 경로를 wrapper가 `checks[target]=false`로 합성하지 않도록 한다. 실패 원인에 따라 실행 오류 또는 인증 미완료로 기록한다.
7. 원 계약과 명제 정렬을 읽기 전용으로 검토한다. 등록 비용 범위 때문에 reviewer가 여전히 차단되면 그 상태를 유지하고 지원된 routing으로만 해결한다. hook·비용 정책을 우회하거나 이 대화의 소스 검토를 로컬 등록 완료로 치환하지 않는다.

## 반환

새 RUN_ID, 사용 계약/hash, 소스/hash, engine version/argv/cwd/exit, 자체검사 결과, 실제 네 축 aggregate, 각 축의 수학적 범위, source exposure, reviewer admission, raw manifest를 반환한다. 원 CAS-13 전체와 관측 구간 포함·coverage·floating-point 구현은 별도 의무로 남겨라. 기존 scientific conditional/HOLD·novelty·Bianchi classification은 자동 변경하지 않는다.

수용 기준: 세 목표 모두에 정확한 대수 및 부호 인증이 대응하고, 실제 실행이 성공하며, 누락된 논리 연결이 없어야 한다. 이 성분이 닫히면 추가 메타감사를 반복하지 말고 결과를 반환하라. 현재 요청은 C04의 제한된 마무리이며, 새로운 catalogue fit이나 전체 통계 파이프라인 구현은 시작하지 않는다.
