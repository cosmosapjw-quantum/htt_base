# 이 스레드로 돌아온 뒤 Local Codex에서 재개할 prompt

이 파일의 immutable Git URL과 함께 아래 내용을 전달한다. 실제 native client를
지정 worktree에서 열어야 하며 subprocess cwd 변경만으로 대체하지 않는다.

```text
ROLE=LOCAL_R10_CHECKPOINT_CONTINUATION
PROJECT=cosmosapjw-quantum/htt_base
WORK_UNIT=HTT_R10_OPTICAL_MAPPING_LOCAL_RESEARCH
WORKTREE=/mnt/sn850x2t/htt_base_e2e/HTT_R10_OPTICAL_MAPPING_LOCAL_RESEARCH/worktree
BRANCH=research/r10-optical-mapping-local-20260920
PLAN_COMMIT=ddd600e8a0c49382e644e5e7df56e272f40bde80
PLAN_PATH=docs/research_program/optical_mapping_r10_20260919/continuation_01/PLAN_KO.md
DAG_PATH=docs/research_program/optical_mapping_r10_20260919/continuation_01/continuation_dag.json
TESTED_SOURCE=99b8e433e0fca4e1384cdc6991e14f15ccddd407
TESTED_SOURCE_TREE=0b48298ecd80cec834cbf1199afe6a3b14412ec5
PREVIOUS_CHECKPOINT=748dbdeec56ac58ed0b440f04eb4d492ab2cb185
ORIGINAL_TESTED_SOURCE=dcc5c7c215c671dc8036771e520bcafa4056cd65
RETURN_PATH=docs/research_program/optical_mapping_r10_20260919/continuation_execution/return/RETURN_TO_MAIN.md
PENDING_RUN=HTT-R10-OPTICAL-LOCAL-20260920
PENDING_ASSIGNMENT=optical_review
PENDING_LAUNCH=cl_57e1777283bfeda24c9ae6dcdb579394
CURRENT_ADMISSION=HOLD

먼저 actual native cwd/runtime identity, status/HEAD/tree/worktrees를 확인하고
immutable URL이 지정하는 delivery commit/tree를 RETURN_COMMIT/RETURN_TREE로 기록하라.
TESTED_SOURCE 이후 return-only 문서와 다른 변경을 구분하라. plan은 git show
PLAN_COMMIT:PLAN_PATH 및 DAG_PATH로 읽고 checkout 전환은 하지 않는다.
위 RETURN_PATH와 현재 AGENTS/SCIENTIFIC_CONTRACT/해당 skills를 전체 읽어라.
원 dirty checkout과 EXTERNAL-FUSION active run, 기존 실패/등록/hook을 보존하라.

RC03은 새 shear_ray/attempt02에서 탐색 실행 완료다. 42개 h-direction 셀과
nonzero Q/O projection/domain 2개 검사 결과를 재사용하라. 첫 attempt01의
격자검사 실패, source/config/log를 보존하라. h 극한과 fixed-h resolution을 구별하고
기존 Milne/Jacobi 85 residual/5 pytest를 의무적으로 반복하지 말라.

RC04는 direct/moment/packed/sigma/time/caller 추적과 CAS draft까지 진행됐다.
standalone mixed isotropic-input shear map rank1과 physical STF rank5의 불일치를
확인했다. 해당 builder의 tracked production caller를 찾지 못했고 실제 native
A_mix는 다른 ver3 builder다. 둘을 동일시하지 말라. mixed 단순 부호 수정은 금지다.
full/packed 일반 ell coefficient 변경은 일반 ell 의무와 public/shared neutrino
영향 범위를 포함해야 한다. draft는 frozen formal contract나 eligibility가 아니다.

RC01/02는 이 이전 세션의 native client가 원 checkout에 있어 BLOCKED였다.
pending은 unclaimed/child=null이며 HEAD 변화도 있다. pending/source/receipt를
먼저 읽고 지원되는 inspect/plan-continuation 절차로 resume 가능성을 판단하라.
재사용 불가하면 auditable supersede 절차를 쓰고 duplicate child를 만들지 말라.
원 checkpoint 독립 검수 1회를 실제 native identity에서 완료하라. 기존 source,
T9 consumer, 기존 5pytest의 실제 범위로 검수를 한정하고 broad rediscovery 금지다.
subagent 전 build_context_pack/new_assignment와 4-field header를 반드시 사용하라.

RC05는 NOT_EXECUTED다. 검수 해소 후 scope별 실제 source-bound CAS_CONTRACT를
동결하고 Wolfram+xAct, SymPy, Sage+Singular, Lean+mathlib 네 독립 축과
cas_gate.py run-adjudicate를 실행하라. tool 미설치/timeout을 예외로 자동 바꾸지 말라.
RC06은 finding 해소 + PATCH_REQUIRED + 해당 scope FORMAL_T9 eligible일 때만 수행한다.
전체 RHS 반전 금지, minimal candidate, 별도 physical RED->GREEN 및 old-sign mutation
FAIL, shared neutrino regression이 필요하다. 기존 exit1 t9_diagnosis.py를 수정하지 말라.
현재 source가 이미 고쳐졌으면 NO_PATCH_NEEDED를 새 scope 증거로 확인하고 재반전하지 말라.

RC07은 donor 870bd67af159993ccde4ede9923424a475c01375의 실제 저장 SDSS R/H/T를
소비해 A=[R,Rc], v=(-c,1) null 결과를 냈다. rank R/A=36, H R=27, T R=36이다.
이는 자유 shell monopole/공통 영점의 mean-response 식별 불가능성이다.
CF3–SDSS 294행은 CF4 law가 아니고 selected/noise/physical boost-tilt law는 UNAVAILABLE다.
alpha0/mock0를 보존하라. 더 최신 donor 작업을 먼저 확인하고 준비된 원 DAG action만
실제 법칙/응답 계산으로 진전시켜라. 하나의 blocked lane으로 모두 중단하지 말라.

원 36-node DAG와 T9 v4/30·candidate40, R8 STOP_INVALID, unresolved pools, P0 quarantine,
PR284 deferred, PR4/NPIPE exclusion, alpha 배분, missing-provider whole-domain을 보존하라.
static Q/O에서 JET_RESPONSE_LAW를 만들지 말라. 새로운 한정된 work contract를 쓰되
소진된 이전 native logical task 예산을 새 이름으로 우회하지 말라.

코드/결과/원 실패/검수 상태/RETURN_TO_MAIN/재개 prompt를 허용된 isolated branch에
non-force push하고 source commit과 return-only commit을 분리해 immutable Git 링크로
이 MAIN 스레드에 반환하라. 실행/native 검수/CAS/관측 admission 상태를 각각 보고하라.
merge/ready 승격은 하지 않는다.
```
