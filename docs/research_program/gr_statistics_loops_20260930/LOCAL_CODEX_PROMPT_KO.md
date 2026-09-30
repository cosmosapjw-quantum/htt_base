# Local Codex 시작 프롬프트 — GR·통계 연구 결과의 네 축 CAS 재검증

```text
ROLE=LOCAL_CODEX_ORCHESTRATOR
PROJECT=htt_base
TASK=GR_STATISTICS_20260930_CAS_REVALIDATION
MODE=THEORY_FIRST_NO_OBSERVATIONAL_FIT

목표는 게시된 연구 결과를 공통 수학 명세에서 독립 재구현하여 검증하는 것이다.
연구 결과의 저장소 보존과 과학적 성립, CAS 실행, Lean 형식 증명을 구별하라.

0. 기존 checkout에서 시작하라.
   /home/cosmosapjw/Dropbox/bianchi/htt_base
   현재 AGENTS.md, docs/harness/CURRENT_CODEX_RUNTIME.md, 현재 설치된 전역 실행 정책을 읽어라.
   git status --porcelain=v1, branch, HEAD, origin URL을 먼저 기록하라.
   git fetch origin main을 실행하고 전달받은 게시 commit이 origin/main의 ancestor인지 확인하라.
   기존 dirty/untracked 변경을 보존하라. 자동 stash/reset/clean, 새 clone/worktree는 금지한다.
   현재 main에서 fast-forward 가능하고 변경 경로와 사용자 수정이 충돌하지 않을 때만
   git merge --ff-only origin/main으로 반영하라. 충돌이나 diverged 상태면 변경을 덮지 말고
   구체적인 경로·차이를 보고한 뒤 안전하게 가능한 읽기·명세 준비를 계속하라.

1. 다음 디렉터리를 INPUT_ROOT로 사용하라.
   docs/research_program/gr_statistics_loops_20260930
   REPOSITORY_INTEGRATION_KO.md, cas/EXECUTION_INDEX.json,
   publication/SOURCE_TO_REPO.json, LOCAL_CODEX_RETURN_SCHEMA.json을 읽어라.
   연구 결과 해석과 기존 판정은 REPORT_KO.md와 DECISIONS.json을 따른다.
   원본 39개 파일과 그 판정은 수정하지 않는다. 새 오류는 정정 파일에 원문/반례를 함께 남긴다.
   Git commit identity, 원문 byte identity, 수학적 검증 상태를 별도 기록한다.

2. 먼저 네 축의 실제 환경을 확인하라.
   python -B .agent-harness/scripts/cas_gate.py preflight --axis wolfram_xact
   python -B .agent-harness/scripts/cas_gate.py preflight --axis sympy
   python -B .agent-harness/scripts/cas_gate.py preflight --axis sage_singular
   python -B .agent-harness/scripts/cas_gate.py preflight --axis lean
   공식 네 축만 사용한다. --all은 현재 구현에서 선택적 Rocq까지 실행하므로 사용하지 않는다.
   Wolfram/xAct, Python/SymPy, SageMath/Singular 실제 버전과 실행 파일을 기록한다.
   Lean은 formal/lean-toolchain 및 대응 Lake/mathlib lock을 따른다.
   다른 전역 Lean으로 조용히 바꾸거나 모든 환경을 최신 버전으로 갱신하지 않는다.
   preflight는 도구 준비 확인이며 수학적 PASS가 아니다.

3. cas/EXECUTION_INDEX.json의 우선순위와 의존관계에 따라 실행한다.
   준비된 schema-v2 계약을 보존하고, 해당 task의 local generation에 복사한 실행 계약에
   실제 환경 pin, source hash, 허용 입력과 모든 모호한 domain 조건을 결과 열람 전에 고정한다.
   exact target과 가정을 바꿔야 하면 새 version으로 기록하고 모든 해당 축에 같은 hash를 배포한다.
   환경 pin만 고친 경우에도 hash가 바뀌면 과거 결과를 새 계약 결과로 재사용하지 않는다.
   task별 실제 작업·증거 디렉터리:
   docs/research_program/gr_statistics_loops_20260930/local_cas/<run_id>/<task_id>/
   축별 scripts/, raw logs, proof/build output, result JSON을 분리한다.

4. 각 축은 공통 계약과 중립 명세만 받아 독립적으로 작성·실행한다.
   축 작성자에게 다른 축의 script/result/derivation, 기존 evidence/*.wl 또는 *.json,
   연구 증명 전문과 과거 reviewer verdict를 보내지 않는다. source hash 참조는 읽기 허가가 아니다.
   Host가 이미 읽은 문서를 fresh-context CAS worker가 읽었다고 취급하지도 말라.
   네 축의 의미를 유지하면서 동시성은 현재 local router와 RAM 한도를 따른다.
   동일 LLM 계열의 여러 축 작성 여부와 실제 author metadata는 그대로 공개한다.

   Wolfram+xAct: tensor 의무에는 실제 xAct 정의·정규화를 실행하고 version/transcript를 남긴다.
   SymPy: 독립 component 또는 exact rational 구현; 필요할 때만 고정된 고정밀 검산을 추가한다.
   Sage+Singular: 별도 exact algebra와 명시된 ideal reduction을 실제 Singular에서 수행한다.
   Lean+mathlib: 원 진술과 동치인 theorem을 kernel-check한다. sorry/admit나 대상 정리를
   가정한 새 axiom, target를 hypothesis로 재기재한 순환 증명을 금지한다.
   #print axioms 및 실제 compiler exit/log를 보존한다. 보조 항등식만 증명하면 범위를 표시한다.

5. 현재 저장소의 실제 실행 판정 경로를 사용하라.
   python -B .agent-harness/scripts/cas_gate.py run-adjudicate \
     --contract <고정한_repo_relative_contract.json> \
     --run-spec <task별_repo_relative_RUN_SPEC.json> \
     --out <task별_repo_relative_ADJUDICATION.json>
   RUN_SPEC은 schema_version=1, axes의 정확한 키는
   wolfram_xact / sympy / sage_singular / lean이다.
   각 값은 argv: 문자열 배열, cwd: 존재하는 repo 상대 디렉터리,
   timeout_seconds: 양의 정수다. shell 키나 네 축 공통 argv는 허용하지 않는다.
   각 축 wrapper는 자신의 실제 엔진만 호출하고 엔진 출력/실패를 증거로 보존한다.
   stdout에는 하나의 JSON 객체만 내보낸다. 로그는 별도 파일 또는 stderr에 둔다.
   payload에는 checks, domain_assumption_diff, counterexample이 필요하다.
   checks의 키는 계약 target.exact_test_obligations와 정확히 일치하며 값은 JSON boolean이다.
   true는 실제 독립 계산/증명 성공에서 얻어야 한다. 상수 true, 기존 결과 복사,
   파일 존재, import 성공, 단순 예제만으로 일반 명제의 true를 만들지 않는다.
   parser가 통과했더라도 adjudicator는 엔진별 raw log와 진술 충실성을 별도로 검토한다.
   check-axis/adjudicate만으로 현재 실행 eligibility를 만들지 않는다.

6. 경계·퇴화·반례를 계약대로 검사하라.
   c의 차원, (-,+,+,+), U=c u, derivative-first vorticity와 Ellis 관례 변환,
   sourceward sky와 photon propagation 방향, ray derivative와 observer drift를 구별한다.
   singular inverse, zero eigenvalue gap, parallel-direction degeneracy, rank-deficient Gram,
   zero entropy budget, zero-width mixture, redshift intercept, scale freedom을 포함한다.
   무작위 수치 일치는 exact proof를 대신하지 않는다.
   최소 반례가 있으면 raw failure를 보존하고 statement/domain 차이를 먼저 확인한다.
   majority vote 또는 결과가 맞도록 가정·부호·정규화를 사후 변경하지 않는다.

7. 판정은 CAS_4AXIS_PASS / CAS_CONFLICT / CAS_BLOCKED / CAS_FAIL을 구별한다.
   예외는 결과를 읽기 전 등록·비자기 승인된 경우만 별도 상태로 기록할 수 있으며,
   CAS_PASS_WITH_REGISTERED_EXCEPTION을 네 축 통과나 과학적 수락으로 부르지 않는다.
   도구 미설치·timeout·license는 환경/resource blocker이고 수학적 반례가 아니다.
   CAS가 닫은 유한 대수 성분과 남은 해석적 증명 의무를 claim별로 따로 보고한다.
   무한 차원/해석 명제를 유한 discretization으로 대체해 전체 정리를 PASS하지 않는다.
   기존 TEFF-H2와 원전 우선권·실제 관측 적용·Bianchi classification의 보류를 유지한다.

8. bounded task마다 결과를 저장하고 다음 실행 가능한 task로 이어가라.
   한 축의 환경 blocker가 다른 독립 task의 명세·검증 가능한 부분을 막지 않게 한다.
   기존 R9 task/자식 lifecycle/예산을 재개하거나 변경하지 않는다.
   과학 runtime 또는 parser 결함은 최소 수정으로 분리하고 validator를 약화하지 않는다.
   이번 범위에서 생산 통계 코드 이식, CF4/Union3 실제 적합, ODE/PDE/Boltzmann 진화는 하지 않는다.

9. LOCAL_CODEX_RETURN_SCHEMA.json에 맞는 반환 JSON과 짧은 한국어 보고서를 작성하라.
   task/claim별 source commit·contract hash·네 축·닫힌 범위·남은 의무·반례·실패 종류,
   raw evidence hash, Lean axioms, 최종 판정과 다음 한 작업을 포함한다.
   LOCAL_CODEX_RETURN_PROMPT_KO.md 형식으로 이 연구 스레드에 복붙할 반환문을 출력하라.
   모든 검증 결과를 영속 파일로 남기되 게시·merge·과학적 승격을 자동 동일시하지 않는다.
```
