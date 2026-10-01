# 새 local Codex 작업: CAS11-C01

```text
ROLE=LOCAL_CAS11_C01_BREGMAN
PROJECT=htt_base
REPO=/home/cosmosapjw/Dropbox/bianchi/htt_base
PACKAGE=docs/research_program/gr_statistics_loops_20260930/cas11_c01_local_start_20261001
CONTRACT=docs/research_program/gr_statistics_loops_20260930/cas_corr_followup_20260930/intake/contracts/CAS11-C01-BREGMAN.json
CONTRACT_SHA256=57202993c9305a15deda1fc142c538473ec17e93453471063f04a5e04bb36624
PRESERVED_C04_LAUNCH=cl_000fce20034122657b6cdf509703df23
```

HANDOFF_COMMIT과 HANDOFF_TREE는 사용자가 최종 반환 메시지에서 전달한 실제 게시 값을 사용한다. 조사 기준 `ec1384fa31a4f5dcacf953a1de801fd02ad0d046`은 이 패키지의 게시 commit이 아니다.

첫 명령은 기존 repo에서 `git status --short --branch`다. HEAD·dirty/untracked를 기록하고 사용자 변경을 보존한다. AGENTS.md, 관련 repo skill, docs/harness/CURRENT_CODEX_RUNTIME.md와 현재 선택된 global authority를 읽는다. 새 clone/worktree, reset, stash, clean을 만들지 않는다.

## 1. 이전 결과와 이번 입력

C02/C03는 고정된 유한 성분의 네 축 PASS와 독립 검토 PASS다. 새 finding 없이 재실행하지 않는다. C03의 비차단 receipt 정정과 이전 seal·실패 기록을 보존한다. C04의 기존 blocked launch는 재등록·dispatch·identity 변경·임의 종결하지 않는다. R9, 비용·실패 기록도 보존한다.

동일 C01 작업이 이미 존재하면 해당 RUN_ID와 비용·실패·source identity를 계승한다. 완료된 결과가 있으면 먼저 그 반환을 읽고 중복 실행하지 않는다. 새 작업일 때만 RUN_ID를 한 번 생성한다. 실행 전에 원격을 fetch하여 고정 handoff를 읽고 안전한 fast-forward일 때 반영한다. 기존 변경과 충돌하면 보존하고 정확한 blocker를 반환한다.

HANDOFF_STATE.json과 원 계약의 source_input_hashes 7개를 실제 바이트로 확인한다. 원 계약은 변경하지 않는다. 새 NEUTRAL_AXIS_BRIEF.md는 v3의 네 permitted_inputs 밖에 있는 공통 statement-clarification 문서이며, 원래 목록의 일부가 아니다. 작성자에게 전달하기 전에 그 SHA와 현재 지원되는 입력 허용·정렬 근거를 기록한다. 목록을 배타적으로 적용하는 경우 지원된 추가 입력 허용 절차가 없으면 dispatch 전에 실제 불일치를 반환한다. 허용 절차를 임의로 만들거나 v3를 수정하지 않는다.

허용이 확인되면 M, dual/adjoint, lambda, 공통 pairing을 중립 명세에 맞춰 선언하고, 다음을 실행 전 statement_alignment에 기록한다.

```text
M(f-g)=0
dPhi(h)-dPhi(g)=M*lambda
```

이는 부모 계약의 gradient-span 조건을 구체화하는 입력이다. 교차항=0을 가정하거나 moment matching만으로 소거하지 않는다. 모든 축의 의미 정렬이 불가능하면 차이를 반환하고 old v3를 고쳐 통과시키지 않는다.

BASE_HEAD를 결정하고 이 작업의 writer/reviewer launch가 지원된 방식으로 처리될 때까지 HEAD를 유지한다. 별도 소스 SHA는 등록 HEAD identity의 대체물이 아니다. 현재 엔진·실행 파일·Lean/mathlib pin과 원 환경 기록의 차이는 분리하여 관측하고 정렬한다.

## 2. 네 축의 독립 작업과 실제 실행

현재 지원되는 router·비용·sandbox 규칙을 따른다. 네 필수 축은 Wolfram+xAct, SymPy, Sage+Singular, Lean+mathlib다. 현재 policy가 고른 적절한 모델/effort를 사용하고 요청값과 관측값을 구별한다. 과거 C03의 gpt-6-sol/high 배정은 현재 배정의 증거가 아니다.

작성자마다 fresh context와 별도 디렉터리·쓰기 소유권을 준다. 입력은 원 계약·허용 중립 자료·NEUTRAL_AXIS_BRIEF.md다. HOST_SCOPE_AND_NEXT_ANALYSIS_KO.md, Host 판정, 형제/기존 증명·결과는 adjudication 전에 주지 않는다. nested child를 만들지 않는다. 누적 비용과 불가피한 입력 노출은 기록한다.

실행 경로가 있으면 계획 작성에서 멈추지 않고 전체 유한 항등식·span cancellation의 소스를 작성·검사한다. 대수 인증과 보편 진술의 연결을 설명하고 고정 차원/이차 함수 예제를 전체 증명으로 대체하지 않는다. Lean은 실제 미분 가능한 Phi에 대한 진술 정렬, 전체 정량자와 axiom/dependency를 확인한다. 추상 값·covector 보조정리를 쓰면 원 계약으로의 적용 관계를 명시한다.

현재 실행기의 인터페이스를 확인하고 봉인 소스·실제 argv/cwd/timeout으로 RUN_SPEC.json을 만든다. repo root에서 확인된 interpreter로 실행한다.

```bash
"${GRSTAT_CAS11_PYTHON}" -B .agent-harness/scripts/cas_gate.py run-adjudicate \
  --contract "${GRSTAT_CAS11_CONTRACT_REL}" \
  --run-spec "${GRSTAT_CAS11_RUN_SPEC_REL}" \
  --out "${GRSTAT_CAS11_ADJUDICATION_REL}"
```

변수는 실제 interpreter 및 repo-relative 경로로 정의한다. 네 축 argv는 구분하고 shell 필드를 쓰지 않는다. stdout payload는 원 obligation key `CAS11-C01-BREGMAN`의 checks, domain_assumption_diff, counterexample을 사용한다. 원시 aggregate를 보존하고 별도 범위 판정을 반환한다. 저장된 envelope의 adjudicate로 실제 실행을 대신하지 않는다.

wrapper 오류·timeout·marker 부재를 수학적 false check로 만들지 않는다. 실제 오류·반례·미증명·가정 불일치를 구분한다. 전체 엔진 stdout/stderr·argv/cwd/version/exit와 source/input seal을 보존한다. 요구된 telemetry wrapper를 사용하되 exporter 실패를 계산 실패로 바꾸지 않는다.

## 3. 검토·게시·반환

계약·봉인 소스·실행 근거를 받는 독립 검토를 한 번 수행한다. Host의 선행 판정을 주입하지 않는다. 구체적 finding만 좁게 수정하고 이전 실패를 보존한다. 실제 child 결과 없이 reviewer 완료를 주장하지 않는다.

이번 C01 launch가 지원된 방식으로 처리된 뒤 해당 작업 파일만 stage하여 commit·non-force push한다. 기존 사용자 변경을 포함하지 않는다. 원격이 전진하면 안전하게 통합하며 force하지 않는다. 게시가 lifecycle 정책으로 막히면 로컬 결과와 정확한 blocker를 반환한다.

RETURN.json과 raw manifest에는 RUN_ID·BASE_HEAD·계약 SHA·statement_alignment·네 축 상태·관측 aggregate·실제 reviewer 결과·범위/gap·환경과 소스·원시 로그·누적 비용·기존 결과 보존을 기록한다. 미측정 비용은 NOT_MEASURED다. source-manifest와 원시 evidence의 소비자·순환 해시 제외 범위를 명시한다.

원격 commit/ref/tree로 R1을 확인하고 고정 commit의 handoff를 반환한다. 자기 commit SHA를 채우기 위한 반복 commit은 만들지 않는다. 부모 CAS-11/CAS-13·과학적 HOLD와 catalogue fit/novelty/Bianchi 상태는 자동 승격하지 않는다.

다음 최소 작업은 C01 완료 후 HOST_SCOPE_AND_NEXT_ANALYSIS_KO.md의 Taylor/Hessian·Hilbert 실현 의무를 독립적인 해석적 연구 단위로 정하는 것이다. 이번 실행에 그 과제나 데이터 분석을 섞지 않는다.
