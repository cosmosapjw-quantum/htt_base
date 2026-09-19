# Local Codex 재개 prompt

아래 prompt를 **정확한 isolated worktree에서 연 native Codex client**에 전달한다.
원 checkout에서 subprocess cwd만 바꾸면 기존 blocker를 해소하지 못한다.
계획을 읽기 위해 먼저 checkout을 바꾸거나 pending registration을 덮어쓰지 않는다.

```text
ROLE=LOCAL_R10_CHECKPOINT_CONTINUATION
PROJECT=HTT
WORK_UNIT=HTT_R10_OPTICAL_MAPPING_LOCAL_RESEARCH
PLAN_BRANCH=research/r10-checkpoint-continuation-20260919-r1
PLAN_PATH=docs/research_program/optical_mapping_r10_20260919/continuation_01/PLAN_KO.md
DAG_PATH=docs/research_program/optical_mapping_r10_20260919/continuation_01/continuation_dag.json
RETURN_COMMIT=748dbdeec56ac58ed0b440f04eb4d492ab2cb185
RETURN_TREE=cfd5849e7f61a2d1ac7dbbd69783dd93eaa8f274
TESTED_SOURCE=dcc5c7c215c671dc8036771e520bcafa4056cd65
TESTED_SOURCE_TREE=ef6bb19ea87c0fd6fcc0a45d1f46522be39c567c
WORKTREE=/mnt/sn850x2t/htt_base_e2e/HTT_R10_OPTICAL_MAPPING_LOCAL_RESEARCH/worktree
PENDING_RUN=HTT-R10-OPTICAL-LOCAL-20260920
PENDING_ASSIGNMENT=optical_review
PENDING_LAUNCH=cl_57e1777283bfeda24c9ae6dcdb579394
CURRENT_ADMISSION=HOLD

위 worktree에서 실제 native client를 열었는지 먼저 확인하라. 원 dirty checkout
/home/cosmosapjw/Dropbox/bianchi/htt_base 및 그 EXTERNAL-FUSION active run은 보존한다.
이전 registration 파일, hook, client identity를 임의 편집하거나 우회하지 말라.

0. RC-00: 정확한 cwd에서 git status --short, git rev-parse HEAD, git rev-parse HEAD^{tree},
   git worktree list와 현재 native runtime identity를 확인한다. 기존 결과/실패를 보존한다.
   반환 이후 변경이 있으면 scope별 영향을 확인한다. 고정 source를 맞춘다는 이유로
   reset/clean/stash 강제 수행, unrelated 변경 폐기, 원 active run 교체를 하지 않는다.
   원 R10 계획·SCIENTIFIC_CONTRACT·현재 AGENTS와 적용되는 .agents/skills를 읽는다.
   htt-dag-orchestrator, physics-math-audit, scientific-code-validation,
   claim-firewall, claim-provenance-ledger, ssot-handoff-maintainer를 적용한다.

1. 계획 branch가 로컬에 없으면 origin URL이 cosmosapjw-quantum/htt_base인지 확인하고
   git fetch origin research/r10-checkpoint-continuation-20260919-r1 을 수행한다.
   git show origin/research/r10-checkpoint-continuation-20260919-r1:<PLAN_PATH> 와
   같은 ref의 <DAG_PATH>를 읽는다. <...>는 위 실제 path로 치환한다.
   처음 읽은 계획 ref의 commit을 기록한다. 이 단계에는 checkout 전환이 필요 없다.

2. RC-01, RC-02: pending launch와 assignment, frozen source, native receipt를 먼저 읽는다.
   이전 dispatch가 실제로 실행되지 않았는지 확인한다. valid pending registration은
   지원되는 절차로 1회 재개한다. HEAD/source seal 변화 때문에 재사용 불가하면
   기존 것을 auditable하게 supersede하는 정상 절차를 쓰고 duplicate child를 만들지 않는다.
   subprocess cwd/prompt/환경변수를 조작해 native source identity를 흉내 내지 않는다.
   원 source checkpoint를 대상으로 독립 검수 1회를 완료한다. findings는 원 코드·결과,
   T9의 현재 consumer, 5 pytest가 실제 다루는 범위로 제한한다. broad repo rediscovery 금지.
   native runtime 복구와 review 통과, CAS 통과, scientific admission을 각각 구분한다.

3. RC-03: PLAN_KO의 평탄 전단 characteristic 실험을 별도 attempt에서 실행하라.
   목표는 source energy inner product→occupation/brightness→STF Q/O→h→0 derivative의
   연결이다. h는 길이, S는 inverse-length이며 h||S||op<1이다.
   예상 reference는 dPi2/dh=-4Pi0 S, dTheta2/dh=-S, odd multipoles=0이다.
   초기 isotropy와 source hypersurface 가정을 명시하라. h 극한과 고정 h 수치해상도
   수렴을 혼동하지 말라. 첫 실패·negative controls를 보존하라. 새 Bianchi solver는 만들지 않는다.
   이것은 아직 제안된 실험이며 완료된 것으로 복사하지 않는다.

4. RC-04, RC-05: Pi direct coefficient/적분 moment/packed/mixed 5m, sigma/시간 adapter,
   실제 mixed caller의 LHS/RHS 부호와 valid subspace를 추적하고 scope별 CAS_CONTRACT를
   준비하라. 일반 ell에 영향을 주는 계수 수정은 일반 ell 의무를 포함해야 한다.
   실제 source/contract가 결속된 네 축(Wolfram+xAct, SymPy, Sage+Singular,
   Lean+mathlib) 독립 실행과 cas_gate.py run-adjudicate만 신규 formal eligibility로
   인정한다. 미설치/timeout/누락을 자동 예외로 바꾸지 않는다. preflight나 stored
   adjudicate 결과, 문장 속 PASS 문자열은 admission이 아니다.

5. RC-06은 checkpoint review finding이 해소되고 PATCH_REQUIRED가 유지되며 해당
   consumer scope의 FORMAL_T9가 실제 eligible일 때만 수행한다. 실제 영향을 받는
   scope가 contract보다 크면 candidate를 진행하지 말고 의무를 정렬하라.
   전체 RHS 반전은 금지. terms/packed cache/mixed 중 실제 필요한 최소 수정만 한다.
   unresolved mixed 경로에는 eligibility를 주지 않는다. 별도 physical regression의
   RED→GREEN 및 old-sign mutation FAIL, 영향받는 public/shared neutrino path를 검증하라.
   기존 t9_diagnosis.py는 mismatch를 assert하며 의도적으로 exit 1인 기록용 runner이다.
   원 log/JSON을 덮어쓰거나 그 runner의 성공 조건을 바꿔 실패를 지우지 말라.
   candidate 결과는 별도 attempt/output path로 저장하라. 생산 admission은 자동 부여하지 않는다.
   현재 source가 이미 올바르면 NO_PATCH_NEEDED를 검증하고 원 OP-07 reuse 분기를
   사용한다. 재차 부호를 뒤집지 말라. 이 분기도 해당 scope formal eligibility가 필요하다.

6. RC-07은 optical/T9 readiness와 독립적이다. R9 donor
   870bd67af159993ccde4ede9923424a475c01375 및 더 최신 local 연구를 먼저 재사용한다.
   원 R9 action별 의존성이 준비된 product 하나를 골라 실제 selected law/response
   계산으로 진전시키거나 구체적인 unsupported target/nullspace를 산출하라.
   준비되지 않은 법칙을 발명하거나 CF3–SDSS 294-row 진단을 CF4 selected law로
   취급하지 않는다. arbitrary skew-G covariance check는 orthogonal algebra control이다.
   물리 응답을 주장하려면 actual generator/metric/selection/noise law를 결속한다.
   CMB/CF4/JWST/DESI는 원 DAG 의존성을 지키고 하나의 실패로 전부 대기시키지 않는다.

공통 규칙:
- subagent 전에 build_context_pack.py를 실행하고 new_assignment.py로 등록한다.
  RUN_ID/ASSIGNMENT_ID/CONTEXT_VERSION/INDEPENDENCE_MODE header, assignment-first read,
  고유 result path와 repo budget을 지킨다. 네 CAS 축은 결과를 서로 보지 않는다.
- 기존 optical 85 residual/5 pytest와 R8/R9 mock pools를 의무적으로 반복하지 않는다.
  실제 changed cell만 검증한다. Milne/Jacobi ODE가 바뀌면 pytest 5개만으로 끝내지 않는다.
- 원 36-node DAG, canonical T9 v4/30 및 candidate40, R8 STOP_INVALID와 unresolved
  pools, P0 quarantine, PR284 deferred, PR4/NPIPE exclusion, alpha 배분을 보존한다.
  static Q/O로 JET_RESPONSE_LAW를 만들지 않는다. missing physical provider는 whole-domain이다.
- 한 action이 막혀도 독립적인 exploratory/R9 action을 진행한다. 무제한 새 gate·receipt를
  만들지 말고 named scientific result를 낸다. 신규 법칙이 없으면 alpha를 쓰지 않는다.
- RC-08: terminal/부분 checkpoint에서 코드+원 실패+실행근거+검수상태를 검토하고
  허용된 isolated research branch에 non-force push한다. 충돌 시 force하지 않는다.
  원 dirty checkout과 사용자의 다른 ref는 변경하지 않는다. merge/ready 승격은 하지 않는다.

MAIN 반환에는 아래를 제공하라:
RETURN_COMMIT / RETURN_TREE / TESTED_SOURCE / PLAN_COMMIT
CHANGED_FILES / COMPLETED_ACTIONS_AND_SCOPE / BLOCKED_CONSUMERS
EXACT_COMMANDS_AND_EXIT_CODES / FIRST_PRESERVED_FAILURE
INDEPENDENT_REVIEW_RECEIPT_OR_BLOCKER / CURRENT_CAS_CONTRACT_AND_ELIGIBILITY
ANISOTROPIC_ORACLE_RESULT_OR_NOT_EXECUTED / T9_SCOPE_AND_PATCH_STATUS
R9_ACTUAL_LAW_OR_NULL_RESULT / OBSERVED_METHODS_AND_ALPHA / NEXT_MINIMAL_ACTION

실행·검수·formal·관측 admission의 상태를 별도로 쓰고, 부분 성공을 전체 연구 완료로
승격하지 말라. source commit과 return-only 문서 commit을 구분하라.
```
