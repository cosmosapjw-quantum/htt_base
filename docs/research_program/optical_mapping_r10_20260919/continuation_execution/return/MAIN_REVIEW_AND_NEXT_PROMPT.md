# MAIN review: 전단 oracle, mixed rank obstruction, R9 평균응답

Owner: HTT research. Scope: MAIN source/artifact review and continuation instructions.
Claim ceiling: DIAGNOSTIC_ONLY. Native independent review / CAS / production admission: **HOLD**.
새 연구 DAG를 만들지 않는다. 계획 `ddd600e8a0c49382e644e5e7df56e272f40bde80`의
9개 RC action 및 원 36-node campaign의 의존성을 유지한다.

## 고정 입력과 판정

RETURN_COMMIT=`48e77f8d05a01b9df78d37475e9fae48f65bad6d`
RETURN_TREE=`05c577d096ce6640442d1cc6338879dd6e018eb1`
TESTED_SOURCE=`99b8e433e0fca4e1384cdc6991e14f15ccddd407`
TESTED_SOURCE_TREE=`0b48298ecd80cec834cbf1199afe6a3b14412ec5`

[원 반환 문서](https://github.com/cosmosapjw-quantum/htt_base/blob/48e77f8d05a01b9df78d37475e9fae48f65bad6d/docs/research_program/optical_mapping_r10_20260919/continuation_execution/return/RETURN_TO_MAIN.md)를
code/results/attempt diff와 함께 검토했다. **부분 연구 checkpoint는 Caution으로 재사용**하고
RC-02/05/06의 미실행은 유지한다. 이번 MAIN 검토는 등록된 native reviewer 또는 CAS 축이 아니다.

- 두 return/source commit은 직전 `748dbdee` 위의 29개 추가 파일이며 모두
  `continuation_execution/` 아래다. production 및 이전 실행 결과는 변경되지 않았다.
- `shear_ray/run.py`의 Git 본문과 결과의 source SHA-256이 일치했다. 저장된 42행과
  6개 control, 요약 잔차 및 mixed 행렬의 유일한 비영 성분을 직접 대조했다.
- 원 source와 attempt02의 diff는 angular convergence acceptance 적용 범위 변경뿐이다.
- 두 CAS draft의 의미/축별 의무와 standalone/ver3의 관련 caller sections를 읽었다.
  대형 production 파일 전체를 재감사했다고 주장하지 않는다.
- 기존 실험·pytest·native/CAS 실행을 반복하지 않았다. R9 donor NPZ와 원 관측 배열을
  이번 MAIN에서 재취득해 replay하지 않았으므로 R9 수치 rank/잔차는 반환 근거에 한정한다.
  그림의 재시각검수 및 원 native launch receipt 확인도 하지 않았다.

## 과학적으로 유지하는 결과

| Action | MAIN 검토 결론 | 다음 소비의 한계 |
|---|---|---|
| RC-03 | 전단이 있는 flat characteristic의 에너지 내적→occupation 적분→brightness/temperature→STF가 구현됐고 국소 미분 reference와 일치하는 실행 근거가 있음 | 초기 등방, 정해진 source 면, timelike 영역의 탐색 결과. 일반 ell hierarchy·cosmological transfer의 admission이 아님 |
| RC-04 full/packed | 이전 isotropic ell2 부호 진단에 독립 구성의 광선 oracle이 추가됨 | 일반 ell 증명과 실제 source-bound four-axis eligibility가 필요. brightness -4와 temperature -1을 혼합하지 않음 |
| RC-04 standalone mixed | 저장 5×5 map은 한 성분만 비영이며 rank 1. 실제 `_C9`의 source/target ell 전달과 m guard가 이를 설명함 | rank 5 물리 STF map과의 가역 adapter가 존재할 수 없음. 해당 builder와 별개인 ver3 runtime의 결함으로 전이하지 않음 |
| RC-07 | 실제 saved response를 소비한 공통 영점/자유 shell monopole의 평균응답 null 결과 | 전체 확률법칙의 동등성, confidence, 물리 boost/tilt 응답이 아님. alpha 0 유지 |

RC-03의 `8.89659e-14`는 **점별 비교 잔차**이다. 미분의 최종 forward 상대오차는
`4.74753e-4`, Richardson 상대오차는 `1.78975e-6`이다. 이를 모두 1e-13 수준의
미분 정확도로 요약하지 않는다. 기존 `attempt01`은 FAIL로 남기고, `attempt02`는
수정된 convergence criterion 아래의 탐색 PASS로 쓴다. 허용오차 숫자가 같아도
검사 대상이 all-grid에서 finest-pair로 바뀌었으므로 acceptance 조건 변경이다.
이는 README에 적절히 공개돼 있다. 새 native reviewer는 이 변경의 타당성을 확인한다.

## 동결 전에 보완할 사항

### 1. 검수 대상과 실행 identity — RC-01/02의 실제 차단점

`resume_inspection.json`에는 `CLIENT_WORKTREE_MISMATCH`와
`REGISTERED_IDENTITY_CHANGED`가 함께 있다. 실제 client는 원 checkout이며,
pending 등록 HEAD는 과거 c8bd214인 것으로 반환됐다. frozen 7개 파일이 같다는 사실은
등록 HEAD/client identity의 일치를 뜻하지 않는다.

그 frozen 목록은 이전 `local_execution`과 SCIENTIFIC_CONTRACT이다. 이번
`shear_ray/run.py`, `adapters/probe_mixed.py`, `r9/response_null.py`, 두 새 CAS draft는
목록에 없다. 기존 assignment의 전체 scope는 로컬에서 추가 확인해야 하며, 과거 7개
input의 review를 이번 29개 결과에 대한 review라고 자동 확장해서는 안 된다.

다음 독립 검수는 **현재 tested source의 새 세 연구 경로와 최초 실패/acceptance 변경**을
명시적으로 포함해야 한다. 실제 client를 isolated worktree에서 열고, 기존 pending의
미실행 상태와 예산을 보존하면서 지원되는 continuation/supersede 절차로 source/scope를
결속한다. 기존 task를 새 이름으로 바꿔 예산을 우회하거나 hook/registration을 수동 편집하지 않는다.

### 2. General-ell 계약의 gradient — RC-04/05의 해석 위험

`P_m(x)=Pi_{A_m}x^{A_m}`는 R3의 homogeneous harmonic polynomial로 정의하고
아래 grad는 **ambient Cartesian derivative `partial/partial x_i`를 구한 후 |x|=1에 제한**한다고
contract의 symbol map에 명시한다. 현재 식의 의도는 맞지만 이 미분 정의가 생략돼 있다.

\[
L_S P_m=(S e)\cdot\nabla_{\mathbb R^3}P_m-(m+4)(e^TSe)P_m
       =(S e)\cdot\nabla_{S^2}P_m-4(e^TSe)P_m.
\]

Euler identity `e·grad_R3 P_m=m P_m` 때문에 두 표기는 위와 같이 동치다.
구면 gradient에 다시 `-(m+4)`를 붙이면 top harmonic 계수가 `-(2m+4)`가 된다.
기존 isotropic m=0 검사에서는 이 오류가 보이지 않는다. 일반 ell 증명을 준비할 때
하나의 `m=1`/`ell=3` exact discriminator를 포함한다. 예: `P1=e_x`,
`S=diag(1,-1,0)`; upper STF coefficient의 -5와 잘못된 -6을 구별해야 한다.
이것은 일반 ell 증명의 대체가 아니라 실제로 다른 미분 convention을 탐지하는 검사다.

동결할 axes 입력은 definitions/assumptions/target/test vectors로 한정한다.
현재 `conventions_ref=adapters/README.md`에는 host 유도와 rank 결론도 들어 있다.
blind-results 축에 그 전체 proof/result를 전달하지 말고 필요한 정의를 contract에
직접 담는다. target을 공유하는 것과 다른 풀이를 읽는 것을 구분한다.

### 3. Mixed negative theorem과 positive consumer eligibility 분리

가역 A,B와 0이 아닌 시간/부호 인자 k에 대해 `rank(k A M B)=rank(M)`이다.
rank 1 source의 4차원 kernel은 단순 정규화로 복구되지 않는다. 1차원 shear 부분공간에
제한한 모델은 따로 정의할 수 있지만 full STF shear의 동등성은 아니다.

따라서 mixed draft의 obstruction 명제를 네 축이 증명해도 그것은 **negative theorem의
검증**이다. standalone 또는 ver3에 대한 `T9_CONSUMER_ELIGIBLE`을 생산하지 않는다.
full/packed 일반 ell 부호 계약은 별도의 scope로 처리한다. 실제 ver3 supplier의 물리
동등성이 목표일 때만 해당 operator를 별도로 조사한다. 이름이 같은 `A_mix`를 연결 근거로 쓰지 않는다.

### 4. R9에서 남아 있는 식별 가능한 대상

반환된 모형과 rank를 전제로 `Y=R beta+R c delta`, R 가역이면 관측 평균은
`gamma=beta+c delta`를 정한다. 따라서 beta-only linear target `l^T beta`는

\[
l^T c=0
\]

일 때, 그리고 그때만 평균응답에서 식별된다. 남는 공간은 35차원이다. 네 shell
monopole의 상대 조합과 nonmonopole 성분은 이 조건을 따르며, 공통 절대 monopole은 남는다.
이는 저장 response와 선형 모형을 전제로 한 MAIN 대수적 결론이며 새 데이터 실행은 아니다.

`rank(HR)=27`인 depth contrast는 이 scalar nuisance 하나만 제거하는 것보다 8개의
추가 평균응답 조합을 버린다. 다른 nuisance 제거를 의도했다면 그 목적을 설명한다.
필요한 관측 target이 `row(HR)` 밖이면 원 R/T 경로에서 분석해야 한다. 단순히 더 높은
rank를 채택하는 것을 과학 목표로 삼지 않는다. 가역 T는 원 1차원 ambiguity를 없애지 않는다.

추가 calibration `z=a^T beta+b delta`는 원 null vector `(-c,1)`에 대해
`b-a^T c != 0`일 때 구조적 모호성을 깬다. 실제 외부 calibration/selected noise law가
있어야 통계적 분석으로 진전할 수 있다. hard constraint나 임의 prior를 데이터로 취급하지 않는다.
동일한 평균만으로 parameter-dependent covariance까지 동일하다고 결론내리지 않는다.

## Local 재개: 사람의 첫 실행과 prompt

로컬 terminal에서 native client를 다음처럼 시작한다. 이 명령은 시작 전 cwd를
명시한다. 앱/IDE를 쓰면 해당 worktree를 실제 project로 연다. 원 dirty 세션을
정리하거나 EXTERNAL-FUSION run을 종료할 필요는 없다.

```sh
codex --cd /mnt/sn850x2t/htt_base_e2e/HTT_R10_OPTICAL_MAPPING_LOCAL_RESEARCH/worktree
```

`--cd`의 의미는 [공식 Codex CLI 문서](https://developers.openai.com/codex/cli/reference/)에서
확인했다. 이것만으로 repository-native pending 등록까지 갱신된다고 보장하지 않는다.
그 client에 아래 prompt를 전달한다.

```text
ROLE=LOCAL_R10_REVIEW_AND_FORMAL_CONTINUATION
PROJECT=cosmosapjw-quantum/htt_base
WORKTREE=/mnt/sn850x2t/htt_base_e2e/HTT_R10_OPTICAL_MAPPING_LOCAL_RESEARCH/worktree
RETURN_COMMIT=48e77f8d05a01b9df78d37475e9fae48f65bad6d
RETURN_TREE=05c577d096ce6640442d1cc6338879dd6e018eb1
TESTED_SOURCE=99b8e433e0fca4e1384cdc6991e14f15ccddd407
TESTED_SOURCE_TREE=0b48298ecd80cec834cbf1199afe6a3b14412ec5
PLAN_COMMIT=ddd600e8a0c49382e644e5e7df56e272f40bde80
PENDING_RUN=HTT-R10-OPTICAL-LOCAL-20260920
PENDING_ASSIGNMENT=optical_review
PENDING_LAUNCH=cl_57e1777283bfeda24c9ae6dcdb579394
ADMISSION=HOLD

현재 native client의 실제 project/cwd/HEAD/tree를 먼저 확인하라. 위 RETURN 이후
변경은 scope별로 판정하고 무조건 reset하지 않는다. subprocess cwd만 고쳐 성공으로
간주하지 않는다. 원 dirty checkout, EXTERNAL-FUSION run, external data 경로
/mnt/extdrive/workdir 및 compatibility link, 기존 실패와 pending 기록을 보존한다.

고정 RETURN의 continuation_execution/return/RETURN_TO_MAIN.md와
CONTINUATION_PROMPT.md, 이 MAIN 검토의 보완사항, 현재 AGENTS와 repo skills를 읽는다.
기존 36-node/RC DAG를 재작성하지 않는다. 완료된 RC03/RC07을 반복 실행하지 않는다.

RC01/02: 기존 pending의 raw receipt/assignment/status와 남은 logical-task budget을
읽어 client mismatch 및 registered identity change 두 조건을 확인한다. 미실행 child의
중복 dispatch 없이 supported continuation/supersede로 현재 source를 결속한다.
새 run 이름이나 force/reset으로 예산·identity 검사를 우회하지 않는다.
build_context_pack/new_assignment와 네 필수 header 등 현재 repo 절차를 따른다.

이번 bounded review scope는 이전 frozen 7개만이 아니다. 현재 tested source의
shear_ray/run.py + test_projection.py + attempt01/source/config/log와 attempt02 결과,
adapters/probe_mixed.py + 두 CAS draft + 관련 standalone/ver3 caller,
r9/response_null.py + 결과 + donor 입력 근거를 포함한다.
필요한 파일은 동일 continuation_execution 아래에서 targeted read하고 broad 재탐색하지 않는다.
기존 reviewer scope가 이를 포함하는지 먼저 확인하고 정상 절차로 업데이트한다.
host review나 MAIN 논증을 native independent review receipt로 복사하지 않는다.

검수에서 angular all-grid→finest-pair criterion 변경을 명시적으로 판정한다.
attempt01 FAIL은 유지하고 attempt02만 변경된 기준의 exploratory PASS로 기술한다.
점별 오차 8.9e-14와 derivative Richardson 상대오차 1.8e-6을 구분한다.
실제 finding이 요구하는 changed cell만 검증한다. 옛 85 residual/5 pytest, R8/R9
mock pools, 전단 42행을 의무적으로 다시 돌리지 않는다.

RC04/05: full/packed 계약에 ambient grad_R3와 tangential grad_S2의 동치식을
명시하고 m1/ell3 discriminator를 포함하라. definitions-only contract를 동결하고
host proof/results를 blind 축 입력에서 제외하라. general ell 의무를 유지하라.
네 축과 실제 run-adjudicate가 필요하며 runtime readiness나 저장 PASS는 대체가 아니다.
mixed의 rank obstruction이 증명되어도 positive T9 consumer eligibility는 부여하지 않는다.
standalone map과 실제 ver3 builder를 분리하고 full/packed의 독립 scope를 유지한다.

RC06: 해당 source/scope의 formal eligibility와 review finding 해소 후에만 최소
candidate를 만들고 별도 physical RED→GREEN/old-sign mutation FAIL을 검사한다.
전체 RHS 반전, 단순 mixed 부호 수정, 원 실패 runner/결과 덮어쓰기는 금지한다.
현재 source가 이미 수리돼 있으면 재반전하지 않고 원 reuse 조건을 검증한다.

RC07의 다음 과학 action은 실제 목표 l에 대해 l.c=0 및 l∈row(HR)를 구분하는 것이다.
이미 저장한 null 결과를 쓰고, 새로운 외부 calibration/selected law가 실제 있을 때만
이를 결속한다. unsupported law를 발명하거나 arbitrary prior로 null을 닫지 않는다.
R9 독립 action을 T9 대기열에 넣지 않는다. 새 근거가 없으면 미평가로 반환한다.

공통 보호 상태와 alpha 배분은 그대로 둔다. 신규 관측법칙이 없으면 alpha0를 유지한다.
static Q/O는 JET_RESPONSE_LAW가 아니며 missing provider의 physical image는 whole-domain이다.
네 CAS 축 missing/timeout을 자동 예외로 바꾸지 않는다. 반복된 native blocker가 그대로면
완료된 연구 셀을 재실행하지 말고 실제 남은 identity/scope 문제와 필요한 사람 조치를 보고하라.

종료 시 새 코드/결과/최초 실패/독립 review receipt 또는 blocker/계약별 CAS eligibility와
RETURN_COMMIT, RETURN_TREE, TESTED_SOURCE를 허용된 isolated branch에 non-force push한다.
현재 branch가 사용 중이거나 원격이 앞섰다면 안전하게 조정하고 강제 갱신하지 않는다.
return-only 문서 commit을 tested physics source로 세지 않는다. merge/ready/admission
자동 승격 없이 이 MAIN 스레드에 다음 최소 action을 반환하라.
```

## Delivery와 검증 경계

이번 변경은 MAIN 검토·재개 prompt와 PR248 delta뿐이다. 원 runtime/contract/source는
수정하지 않았다. 문서 자체 검토와 링크·고정 pin·범위 검사를 수행하고 Git 본문을 대조한다.
등록된 독립 검수의 정상 완료는 아직 Local의 다음 event이며, 이 문서를 push하는 것으로
해결되지 않는다. 원격 문서 commit만 되돌리면 복구할 수 있고 데이터 migration은 없다.
