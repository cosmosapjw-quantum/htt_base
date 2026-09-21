# MAIN review 후 Local 부분 반환 — 2026-09-21

Owner: HTT research. Claim ceiling: **DIAGNOSTIC_ONLY**. Native independent
review / four-axis CAS / production / observational admission: **HOLD**.
기존 부분 연구 checkpoint는 Caution으로 재사용한다. 이 반환은 전체 campaign 완료가 아니다.

## 정확한 입력과 이번 source

- 입력 RETURN_COMMIT: `48e77f8d05a01b9df78d37475e9fae48f65bad6d`
- 입력 RETURN_TREE: `05c577d096ce6640442d1cc6338879dd6e018eb1`
- 기존 물리 TESTED_SOURCE: `99b8e433e0fca4e1384cdc6991e14f15ccddd407`
- 기존 물리 TESTED_SOURCE_TREE: `0b48298ecd80cec834cbf1199afe6a3b14412ec5`
- 이번 TESTED_CORRECTION_SOURCE: `ef85e7c9292f0c4a96381c51ef3c62e509e2efd4`
- 이번 TESTED_CORRECTION_TREE: `b47eaa999579f0de1403979fe9ed573680da5abe`
- 계획: `ddd600e8a0c49382e644e5e7df56e272f40bde80`; 원 9 RC action과
  36-node campaign, canonical DAG/status 및 기존 보호 상태를 유지한다.

이번 source는 두 draft의 정의/범위, 유한 exact discriminator, 설명 및 검수 blocker를
수정·추가한 7개 파일이다. 기존 shear/R9 물리 코드를 실행한 새 source로 세지 않는다.
새 RETURN_COMMIT/TREE는 이 문서와 재개 prompt만 추가한 delivery commit이며 최종
응답과 원격 readback에서 명시한다. `git log -1 --format=%H -- <이 문서>` 및 그
commit의 `^{tree}`로도 해석할 수 있다. 자기 commit hash를 문서에 삽입하지 않는다.

## 실행 결과와 남은 차단점

| RC | 이번 상태 | 근거와 범위 |
|---|---|---|
| RC-00 | 확인 | 실제 CLI session metadata의 cwd/초기 HEAD가 입력 RETURN과 일치 |
| RC-01 | 부분 해결 / BLOCKED | client cwd는 맞음. 과거 source/sandbox/scope 및 동일 task continuation 미해결 |
| RC-02 | NOT_EXECUTED | original pending은 unclaimed, child=null; 새 등록/중복 dispatch 없음 |
| RC-03 | 기존 탐색 결과 재사용 | 42행·6 controls·최초 실패를 재실행하지 않음 |
| RC-04 | draft 보완 + 유한 검사 PASS | ambient/tangent 정의, m1/ell3 discriminator, blind 입력 분리, mixed negative 범위 |
| RC-05 | NOT_EXECUTED | RC-01 미해결; 네 축·toolchain seal·freeze·run-adjudicate 없음 |
| RC-06 | NOT_EXECUTED | review와 해당 formal eligibility가 없어 production candidate를 만들지 않음 |
| RC-07 | 조건부 target 설명 보완 | 새 target/calibration/law가 없어 추가 row(HR) 판정 UNEVALUATED; alpha0 |
| RC-08 | 부분 반환 | source와 이 delivery 문서를 분리; 허용 branch에 non-force 게시, merge/ready 없음 |

[native_blocker.json](../main_review_followup/native_blocker.json)은 native CLI
session `01a0c1b2-cc3d-7760-8724-ea144882d474`의 실제 metadata excerpt,
기존 launch 원문, 7개 frozen input 비교, 새 검수 대상·질문과 명령의 관측 출력을 담는다.
shell의 `pwd`만으로 client 일치를 주장하지 않았다.

`cl_57e1777283bfeda24c9ae6dcdb579394`는 여전히 등록 HEAD `c8bd214...`,
`danger-full-access` sandbox, 과거 `optical_review` assignment에 결속돼 있다.
현재 실제 client는 `workspace-write`다. read-only inspect의 남은 오류는
`REGISTERED_IDENTITY_CHANGED`; sandbox 차이는 Host가 따로 비교한 사실이다.
frozen 7개 입력과 assignment 파일 hash는 그대로 맞지만 새 세 연구 경로를 포함하지 않는다.

지원되는 다음 명령을 **기존 run**에 실제 실행했다.

```sh
python3 /mnt/sn850x2t/local_ai_foundry/60_runtime/cuhg/policy-authorities/fd1069a655bdf365d4242cb375f17e94dc884863/scripts/codex_harness/native_workspace_job.py plan-continuation --run-dir .agent-harness/runs/HTT-R10-OPTICAL-LOCAL-20260920
```

exit 2, `WORKSPACE_JOB_UNAVAILABLE: Cannot read workspace_job.json.`이다.
launch에도 `continuation_context=null`이다. 현재 지원 CLI에는 이 과거 미실행
registration을 새 source/scope로 이행할 수 있는 확인된 절차가 없다.
남은 spendable logical-task 예산은 **UNAVAILABLE**로 보존한다. 기존 reservation 1개와
실제 bound child 0개를 새로운 예산으로 해석하지 않았다. 새 job/run/assignment를
만들거나 hook/registration을 수동 편집하지 않았다. 따라서 subagent용 context 재생성과
new_assignment/4-field spawn은 dispatch 재개 전의 미실행 절차로 남는다.

다음 사람 조치는 client를 다시 여는 것이 아니라 runtime 담당자가 **동일 run/task의
기존 job이 있다면 그 귀속을 복구하거나, 미실행 launch의 지원되는 supersede 절차를
제공하는 것**이다. 그 절차는 원 reservation/예산, 과거 sandbox/source와 새 검수 scope를
보존·결속해야 한다. 새 이름으로 등록하는 것은 이 조치의 대체가 아니다.

## 계약 및 유한 exact 검사

[full/packed version-2 draft](../adapters/CAS_CONTRACT_FULL_PACKED_DRAFT.json)는
`P_m(x)=Pi_A_m x^{A_m}`를 R³의 homogeneous harmonic polynomial로 정의한다.
`grad_R3`는 ambient Cartesian 미분 후 `x=e`에 제한하며,
`grad_S2=(I-ee^T)grad_R3`다. Euler identity에 따라 목표 generator는

```text
(S e).grad_R3(P_m) - (m+4)(e^T S e)P_m
  = (S e).grad_S2(P_m) - 4(e^T S e)P_m.
```

새 [test_gradient_discriminator.py](../adapters/test_gradient_discriminator.py)는
`P1=x`, `S=diag(1,-1,0)`에서 유리수 다항식을 미분하고 degree-3 trace를 제거한다.
올바른 ambient/tangent 식 모두 upper harmonic 계수 **-5**, 잘못된
`grad_S2`와 `-(m+4)` 조합은 **-6**으로 분리됐다. trace 제거 reference도 정확히
검사했다. 두 검사는 통과했으며 general-ell 증명 또는 등록 CAS 축이 아니다.

두 draft는 표현·단위·시간 정의를 직접 담고 Host 유도/결과가 있는 README,
SCIENTIFIC_CONTRACT, probe와 이번 검사/반환 문서를 blind 축 입력에서 제외한다.
source hash 목록을 전달 allowlist로 읽지 않는다. target과 test vector는 공유하되
Host 풀이를 증거로 제공하지 않는다. full/packed 일반 ell 의무는 그대로 남는다.

[mixed version-2 draft](../adapters/CAS_CONTRACT_MIXED_DRAFT.json)의 결과 종류는
`NEGATIVE_THEOREM_ONLY`다. `rank(k A M B)=rank(M)`의 obstruction 증명은
standalone/ver3/full-packed positive `T9_CONSUMER_ELIGIBLE`을 부여하지 않는다.
1차원 제한 모델은 full STF와 구별한다. `_C9`와 실제 ver3 supplier/caller의 해당
부분만 읽었으며 대형 production 파일 전체를 재감사하지 않았다.

| 계약 | Wolfram+xAct | SymPy | Sage+Singular | Lean | Positive consumer eligibility |
|---|---|---|---|---|---|
| full/packed | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | false |
| mixed negative | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | NOT_EXECUTED | false, theorem PASS도 부여 불가 |

현재 두 파일 모두 `DRAFT_NOT_FROZEN_NOT_ELIGIBLE`이다. 실제 four-axis와
`run-adjudicate`를 대신하는 preflight/stored adjudicate도 실행하지 않았다.

## 재사용 결과의 정확한 한계

RC-03의 `8.89659e-14`는 점별 잔차, `4.74753e-4`는 최종 forward 미분 상대오차,
`1.78975e-6`는 Richardson 상대오차다. attempt01은 FAIL로 보존한다.
attempt02는 all-grid→finest-pair라는 **변경된 acceptance criterion** 아래의
exploratory PASS다. 숫자 허용오차가 같다는 이유로 동일 acceptance라고 하지 않는다.
그 변경의 타당성은 expanded native review의 명시적 미해결 질문이다.

R9는 저장 선형 모형과 rank를 전제로 평균이 `gamma=beta+c delta`를 정하므로
beta-only target은 `l.c=0`일 때 식별된다. 35차원 공간과 `rank(HR)=27`인 contrast를
구별했다. 기존 네 monopole 평균은 `l.c=1`로 식별되지 않는다. Owner가 이번 turn에
"no new target"이라고 확인했으므로 추가 membership 계산을 하지 않았다. 고정 donor의 H 대표 행을
읽어 인접 깊이의 같은 angular 성분을 빼는 정의만 확인했다. donor NPZ나 원 null/
rank/잔차 계산을 replay하지 않았다. 외부 calibration의 구조적 조건은
`b-a.c != 0`이며 실제 calibration/noise law 없이 통계 결과를 만들지 않는다.
이 논의는 conditional mean-response이며 parameter-dependent covariance까지의
law equivalence, confidence 또는 물리 boost/tilt 응답이 아니다.

## 검증·보존·반환 경계

[validation.json](../main_review_followup/validation.json)에 실제 명령·exit code·출력과
Host self-review 범위를 기록했다. 새 exact tests 2개, JSON/고정 source binding,
blind 입력·mixed eligibility 범위, `git diff --check`가 통과했다. 기존 실험/원 실패/
반환 등 48개 파일의 Git 본문을 확인했다. production, canonical DAG/status와
campaign, 기존 pending/assignment는 변경되지 않았다.

원 dirty checkout, EXTERNAL-FUSION run, 외부 data root/link를 변경하지 않았다.
기존 85 residual/5 pytest, RC-03/07, R8/R9 pools, figure 시각검수, native/CAS,
production RED→GREEN 및 mutation, CI는 반복하지 않았다. 새 함수는 Host가 작성했고
local inference 0회, native dispatch 0회다. 새 draft 보완의 routing fallback은
기존 native optical_review의 예산이나 identity를 변경하지 않는다.

Canonical T9 v4/30·candidate40, R8 STOP_INVALID/unresolved pools, P0 quarantine,
PR284 deferred, PR4/NPIPE exclusion과 alpha 배분은 유지한다. static Q/O는
JET_RESPONSE_LAW가 아니며 missing physical provider의 image는 whole-domain이다.

다음 최소 action은 [재개 prompt](CONTINUATION_PROMPT_MAIN_REVIEW.md)의 동일-task
identity/scope 복구다. 이것이 해결되면 현재 세 연구 경로와 최초 실패/acceptance 변경을
한 번 독립 검수하고, 적용되는 계약의 정의만 전달하여 네 축을 진행한다. R9는 별개로
실제 target/provider가 들어왔을 때 진행한다. 게시 성공은 admission이 아니다.
