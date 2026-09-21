# 다음 동일-task 재개

```text
ROLE=LOCAL_R10_REVIEW_AND_FORMAL_CONTINUATION
WORKTREE=/mnt/sn850x2t/htt_base_e2e/HTT_R10_OPTICAL_MAPPING_LOCAL_RESEARCH/worktree
BRANCH=research/r10-optical-mapping-local-20260920
PLAN_COMMIT=ddd600e8a0c49382e644e5e7df56e272f40bde80
INPUT_RETURN_COMMIT=48e77f8d05a01b9df78d37475e9fae48f65bad6d
INPUT_RETURN_TREE=05c577d096ce6640442d1cc6338879dd6e018eb1
TESTED_SOURCE=99b8e433e0fca4e1384cdc6991e14f15ccddd407
TESTED_SOURCE_TREE=0b48298ecd80cec834cbf1199afe6a3b14412ec5
TESTED_CORRECTION_SOURCE=ef85e7c9292f0c4a96381c51ef3c62e509e2efd4
TESTED_CORRECTION_TREE=b47eaa999579f0de1403979fe9ed573680da5abe
PENDING_RUN=HTT-R10-OPTICAL-LOCAL-20260920
PENDING_ASSIGNMENT=optical_review
PENDING_LAUNCH=cl_57e1777283bfeda24c9ae6dcdb579394
ADMISSION=HOLD

먼저 이 prompt의 delivery commit/tree와 actual client cwd/HEAD/tree를 확인한다.
TESTED_SOURCE_TREE는 RETURN_TO_MAIN_REVIEW_FOLLOWUP.md 및 Git object와 대조한다.
return 문서 commit은 tested physics source가 아니다.
현재 AGENTS와 해당 repo skills, 고정 RETURN 및 새 RETURN_TO_MAIN_REVIEW_FOLLOWUP.md,
main_review_followup/native_blocker.json과 validation.json을 읽는다.
새 연구 DAG나 예산을 만들지 않고 9 RC action과 원 36-node 의존성을 유지한다.

RC-01: actual client cwd는 이미 맞았지만 pending은 c8bd214 source 및 과거 sandbox,
7개 input만 묶여 있었다. 기존 run의 plan-continuation은 exit2 WORKSPACE_JOB_UNAVAILABLE였다.
기존 job 귀속을 복구하거나 지원되는 동일-task unclaimed-launch supersede가 제공됐다는
새 근거가 있을 때만 재개한다. 이전 blocker를 그대로 재시도하거나 새 prepare/job/run 이름,
수동 registry/hook 편집으로 우회하지 않는다. 원 reservation과 누적 예산, pending 원문을
보존한다. 남은 예산을 확인하지 못하면 UNAVAILABLE로 반환한다.

RC-02: 지원 절차가 마련되면 build_context_pack/new_assignment로 등록한 scope와
RUN_ID, ASSIGNMENT_ID, CONTEXT_VERSION, INDEPENDENCE_MODE를 정확히 결속한다.
새 검수는 current shear_ray/run.py/test_projection/attempt01 source/config/log와
attempt02 결과, probe_mixed와 두 version2 CAS draft 및 실제 standalone/ver3 caller,
r9/response_null.py/결과/donor 근거를 포함한다. native_blocker의 prospective 목록은
등록된 assignment가 아니다. 현재 source hash와 함께 정상 절차로 결속해야 한다.
최초 FAIL과 all-grid→finest-pair acceptance 변경을 명시적으로 판정하고,
점별 8.9e-14와 Richardson 미분 상대오차 1.8e-6을 구별한다. Host/MAIN review를
native receipt로 복사하지 않는다. completed RC03/RC07/85 residual/5 pytest를 재실행하지 않는다.

RC-04/05: version2 draft의 ambient grad_R3, tangential grad_S2 및 m1/ell3 target을
유지한다. Host exact checker는 CAS 축이 아니다. 정의/가정/target/vector와 필요한 source
정의만 freeze하고 README, SCIENTIFIC_CONTRACT의 Host 풀이, probe/Host tests/results,
return 문서를 blind 축에서 제외한다. source identity 목록은 delivery allowlist가 아니다.
일반 ell 의무를 축소하지 않고 Wolfram+xAct, SymPy, Sage+Singular, Lean 네 축과
실제 source-bound run-adjudicate를 수행한다. missing/timeout을 자동 예외로 바꾸지 않는다.
mixed negative theorem은 통과해도 positive T9_CONSUMER_ELIGIBLE을 생산하지 않는다.
full/packed와 별도이며 standalone verdict를 실제 ver3 supplier에 전이하지 않는다.

RC-06: 해당 source/scope의 independent finding 해소 및 positive formal eligibility가
있을 때만 최소 candidate/재사용을 판단한다. 전체 RHS 반전, 단순 mixed 부호 수정,
원 실패 runner/result 덮어쓰기는 금지한다. 별도 physical RED→GREEN/old-sign mutation
FAIL 및 영향 받는 shared 경로를 검사한다. 이미 수리됐으면 두 번 반전하지 않는다.

RC-07: 새 실제 target l이 있으면 l.c=0와 l in row(HR)를 각각 판단한다.
35 대 27 차원을 구별하며 더 높은 rank를 목표로 만들지 않는다. 기존 공통 monopole
평균은 l.c=1이다. calibration은 b-a.c !=0 및 실제 law 근거가 있어야 한다.
새 target/provider/law가 없으면 UNEVALUATED, alpha0를 유지하고 독립 R9를 T9 대기열에 넣지 않는다.
Owner는 2026-09-21 이번 turn에 "no new target"이라고 명시했다. 임의 target을 선택하지 않는다.

원 dirty checkout, EXTERNAL-FUSION, external data/link, 모든 원 실패/보호 상태를 보존한다.
현재 client 재시작만으로 missing job/scope가 해결된다고 하지 않는다. 같은 blocker면
완료 셀을 반복하지 말고 남은 runtime-maintainer 조치를 반환한다.
새 결과/source/review receipt 또는 blocker와 계약별 eligibility를 허용 branch에
non-force push하고 정확한 source/return pin을 구별한다. merge/ready/admission 자동 승격 금지.
```
