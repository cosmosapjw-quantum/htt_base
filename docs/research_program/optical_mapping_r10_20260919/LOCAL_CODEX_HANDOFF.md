# Local Codex execution prompt — HTT R10 optical mapping

Copy the following prompt. The dispatch message must include the immutable publication commit containing this file; do not resolve it from a moving branch if a fixed commit is supplied.

```text
ROLE=LOCAL_CODEX_RESEARCH_EXECUTOR
PROJECT=cosmosapjw-quantum/htt_base
WORK_UNIT=HTT_R10_OPTICAL_MAPPING_LOCAL_RESEARCH
PLAN_DIR=docs/research_program/optical_mapping_r10_20260919
RESEARCH_BASE=5e4e899c0dfa2028d81a82ca68ccd11203947470
RESEARCH_BASE_TREE=dbfcdc9abc2298534b65f50ae6a19ab0012aa999
IMPLEMENTATION_ANCESTOR=efc5f30666b96782f946375551f0068bb3a30f74

사용자는 추가 광학 연구를 반영한 연구를 Local Codex에서 진행하도록 요청했다. 계획만 다시 쓰고 끝내지 말고, 아래 한정된 연구와 실제 구현/계산을 수행하라. 원래 목적은 full Q/O 형태·관측 응답·공유 보정·조건부 물리집합의 연결이다. 단순 배경 fit이나 신호 검출 여부를 전체 목표 달성으로 바꾸지 말라.

1. CURRENT-TURN START
현재 cwd, git status/HEAD/worktree, 진행 중인 동일 작업과 반환 결과를 확인한다. dirty checkout, 미추적 파일, 원 실패를 보존하고 이 전달 commit에서 분리 worktree를 만든다. 전체 clone이 이미 있으면 재취득하지 않는다. publication SHA/tree와 PLAN_DIR의 MANIFEST.sha256을 확인한다. README→PLAN_KO→SCIENTIFIC_CONTRACT→campaign_dag→SOURCE_PROVENANCE→PLAN_REVIEW 순으로 읽는다. 원본 source_addition의 PASS는 raw receipt가 없는 imported assertion이다.

Python은 print(6*7) 같은 실제 최소 실행으로 확인한다. C++/Wolfram 등은 필요한 action에서 독립 probe한다. 이전 스레드의 runtime failure를 상속하지 않는다. PYTHON_PASS/CPP_PASS/TOOL_NOT_EXPOSED/COMPILER_MISSING/PACKAGE_MISSING/EXECUTION_FAILED/SERVICE_ERROR를 정확히 구분한다. transport failure는 최소 probe 1회 재시도 후 두 번 연속이면 해당 실행경로 DEGRADED로 보존한다. 다른 available path는 계속한다.

2. AUTHORITY AND HARNESS
현행 R9는 PR468이며 PR463/464/465-only 상태로 되돌리지 않는다. R8 구현·STOP_INVALID와 R9 bounded research evidence를 해당 source/method 범위로 재사용한다. 현재 user 승인에 따라 pre-observation Local 연구를 시작할 수 있다. 제품법칙·production math·mock qualification은 기존 action별 admission을 따른다. 모든 M1/M2/M3를 새 MAIN 승인 절차로 다시 만들지 않는다.

repo AGENTS.md와 해당 하위 AGENTS, .agents/skills의 DAG·physics·observable·local/global·claim·handoff 지침을 읽는다. 사용자의 physmath-research-loop가 있으면 실제 선택 모델과 명시한 버전에 맞는 research/coding 하네스를 읽고 적용한다. GPT-6 Astra v4.0.0 및 GPT-5.6 v3.1.0을 이름만 바꿔 동일시하지 말라. 현재 설치된 canonical harness identity를 기록하고, 모델 변경이나 새 global harness 설치는 이 작업으로 수행하지 않는다. 호스트가 모델 identity를 제공하지 않으면 하네스 선택 근거와 불명확함을 따로 기록한다.

subagent를 쓸 때 먼저 python3 .agent-harness/scripts/build_context_pack.py를 실행하고 new_assignment.py를 통해 등록한다. RUN_ID/ASSIGNMENT_ID/CONTEXT_VERSION/INDEPENDENCE_MODE header와 한정 evidence slice를 제공한다. 하나의 source mapper와 shared writer, 동시 4명/총 8명/depth 2를 지킨다. 네 CAS 축은 독립 script/result로 current CAS_CONTRACT를 소비한다. run-adjudicate만 현재 observed-execution eligibility를 낼 수 있다. 저장된 PASS 문자열/과거 aggregate나 두 CAS 비교를 네 축으로 올리지 말라.

3. FIRST SUBSTANTIVE RESULT
OP-00/01 source·단위·부호를 고정한 다음 OP-02..05를 수행한다. first-jet→H,V→central-ray/Jacobi→collisionless T/I→STF Q/O의 작은 end-to-end fixture와 residual plot을 실제 생성하라. 전역 Bianchi solver를 새로 만들지 말라. PLAN의 O01..O15에 적힌 적용되는 exact/finite fixture를 독립 oracle로 사용한다. 관측 product가 없어도 이 연구를 완결할 수 있다.

vorticity axial dual, n=-e, c/time, Riemann 및 tetrad rotation을 명시한다. ideal 12-component inverse와 실제 drift/proper-motion response를 구별한다. Jacobi가 absolute endpoint map을 대체하지 않으며, null shear/matter shear/Q는 서로 다르다. L_IJ의 coordinate/orthonormal 변환이 확인되지 않으면 invariant K_z=(D_z)D^-1로 진행한다. z turning point/caustic에서 chart나 inverse를 강제하지 않는다. Thomson finite-anisotropy에서는 single-temperature closure를 자동 유지하지 않는다.

4. T9 LANE
현재 terms.py/packed_operators.py/hierarchy_rhs.py/mode_mixing_blocks.py와 normalization/time adapter를 읽어 OP-06을 실행한다. T9라는 term과 canonical T9 v4 ledger를 혼동하지 않는다. 초기 isotropic brightness의 독립 kinetic reference dPi_2/deta=-4 a sigma Pi0, energy integration, +8/15 intensity normalization을 실제 current consumer와 비교한다. 독립 reference는 T9 계수표를 import하지 않는다.

confirmed mismatch이면 required scoped math admission을 충족하고 OP-07에서 최소 candidate repair를 수행한다. source-unresolved이면 source-seal/production repair만 보류하고 derivation과 다른 branch를 계속한다. already-fixed/convention-equivalent이면 sign을 다시 바꾸지 않는다. negative coefficient만 grep해 즉시 패치하지 말라. packed/full parity는 공유 oracle이므로 물리 검증을 대신하지 않는다. 잘못된 candidate sign mutation이 code-to-reference assertion을 실패시키는지 확인하고 RED/GREEN·영향받은 결과 목록을 보존한다. RHS 전체 부호 반전, unrelated refactor, 과거 failure 재작성은 하지 않는다.

5. R9 INTEGRATION AND ACTUAL SCIENCE
기존 R9-03..18 작업을 독립 분기로 진행한다. shared theta/eta embedding, selected-product law, source uncertainty·reverse mixing을 포함한 CMB joint response, threshold-directed full Q/O rank를 재사용·구현한다. 어떤 optical candidate를 선택하는 경우에만 OP-08/09 및 FORMAL_OPTICAL_MAP과 method-matched law를 소비한다. optical fixture가 R9의 모든 관측 결과 앞에 놓이는 공통 gate가 아니다.

CF4 새 distance-modulus law만 사용하고 P0 headline은 격리한다. JWST shared anchors/selection, DESI conditional compressed law, Union3 approximate scenario를 구분한다. PR3/FFP10 unique realization/product matching을 검증하고 same-sky components·posterior draws를 independent null로 세지 않는다. PR4/NPIPE는 기존 제외 상태를 유지한다. R9 alpha family=1/20; CF4/distance-calibration/DESI 각각 1/80; CMB rank/candidate 각각 1/160. 누락 branch alpha 재배분·old seed/row/statistic/budget 변경 금지.

source/law/metric/target가 고정된 실제 mocks→method qualification→제품별 관측→shared-tuple 교차 후 사영 순으로 진행한다. missing law는 justified partial law/scenario/whole domain이다. R9-19 actual jet derivatives/remainder가 없으면 empirical MES physical image를 만들어내지 않는다. ideal H,V inverse, 광학 L2 fixture, local beta를 global matter tilt나 native family 근거로 승격하지 않는다.

6. AUTONOMY, CHECKPOINT, RETURN
ordinary implementation/numerical/parsing/plotting defects는 같은 bounded objective 안에서 원인을 찾아 수정하고 실제 재검증한다. 고정 scientific premise/target를 바꾸어 PASS를 만드는 것은 허용하지 않는다. 한 action이 blocked이면 직접 영향받는 consumer만 보류한다. 유효한 negative/partial/unidentified result도 연구 결과다. 불필요한 blanket rerun, 큰 DB 복원, 대형 자료 복사, 설치 archive 실행, 기존 PDF 재조판은 하지 않는다.

긴 실행은 action 종료와 재개 가능한 checkpoint에서 코드·원 로그·결과·source/contract identity를 Git에 보존한다. 다음 context에는 active action·frozen decision·새 evidence·exact next command만 담고 큰 로그 전문을 반복 주입하지 않는다. 실제 hard wall cap이면 외부 preemption을 사용하며 R8 cooperative overrun을 지우지 않는다.

RETURN_TO_MAIN.md에는 무엇이 derived/numerically checked/implementation verified/blocked인지, 실제 source/command/exit/engine, T9 판정, optical/data admissibility, 기존 R9 성과와 남은 작업, 다음 최소 행동을 기록한다. 결과 tables/plots와 생성 코드, source patch, 원 실패, 조건부 claim을 같이 commit한다. 새 전체 연구 요약만 반복하지 말라.

모든 terminal failure 또는 partial checkpoint에서 Git return이 가능하다. 독립 reviewer가 해당 source와 결과 범위를 검토한 뒤 격리 branch에 non-force push한다. fixed commit/tree와 RETURN_TO_MAIN·결과·다음 MAIN continuation prompt의 immutable Git links를 반환한다. WORK_THREAD나 수동 ZIP relay는 요구하지 않는다. 기존 승인된 cloud backup 경로가 실제 확인될 때만 사용하며 provider 성공 없이 dual backup이라고 말하지 않는다. merge/ready/canonical promotion/public visibility change는 수행하지 않는다.
```

## Required return-to-MAIN prompt

Local Codex writes a completed version, replacing bracketed fields with observed values:

```text
ROLE=MAIN_RETURN_REVIEW
PROJECT=HTT
WORK_UNIT=HTT_R10_OPTICAL_MAPPING_LOCAL_RESEARCH
RETURN_COMMIT=[actual commit]
RETURN_TREE=[actual tree]
RETURN_ENTRY=[immutable RETURN_TO_MAIN URL]
TESTED_SOURCE=[actual tested commit or exact worktree/diff identity]
COMPLETED_ACTIONS=[evidence-qualified IDs and scopes]
BLOCKED_ACTIONS=[IDs, exact reason, preserved failure URL]
T9_DIAGNOSIS=[confirmed/already-fixed/convention-equivalent/unresolved]
OBSERVED_METHODS=[actually qualified and executed, or none]

반환 문서·원 source/diff·실행근거를 읽고 각 결론의 범위와 잔여 과학 문제를 판정하라. 계획 완료나 node exit를 science PASS로 승격하지 않는다. 기존 R8/R9 결과를 전부 재실행하지 않는다. 원래 Q/O 형태·관측 응답·공유 보정·조건부 물리해석에 무엇이 추가됐는지 설명하고, 미해결 문제가 막는 정확한 consumer와 다음 최소 연구를 정하라.
```
