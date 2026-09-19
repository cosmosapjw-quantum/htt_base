# R10 continuation 01 — 부분 연구 반환

CURRENT_ADMISSION=HOLD. Owner: LOCAL_R10_CHECKPOINT_CONTINUATION.
실행한 탐색 결과를 반환한다. native 검수 복구, CAS, T9 수정, 관측 admission은 완료되지 않았다.

## 정확한 source와 plan

- TESTED_SOURCE=`99b8e433e0fca4e1384cdc6991e14f15ccddd407`
- TESTED_SOURCE_TREE=`0b48298ecd80cec834cbf1199afe6a3b14412ec5`
- PLAN_COMMIT=`ddd600e8a0c49382e644e5e7df56e272f40bde80`
- 최초 고정 원계획=`c8bd214a61088b684cad1d08873f05227cf5bfb0`, tree=`d66ccc669492c2b6f233d58b818c86b69fc3aaa7`
- 직전 RETURN=`748dbdeec56ac58ed0b440f04eb4d492ab2cb185`, tree=`cfd5849e7f61a2d1ac7dbbd69783dd93eaa8f274`
- 이전 optical/T9 TESTED_SOURCE=`dcc5c7c215c671dc8036771e520bcafa4056cd65`; 이전 결과를 재사용했다.
- RETURN_COMMIT / RETURN_TREE는 이 문서와 prompt만 추가한 **최종 delivery commit**이며
  MAIN 스레드의 immutable URL 및 최종 답변에 명시한다. 자기 commit hash를 자기 내용에
  넣는 순환 참조는 하지 않는다. `git log -1 --format=%H -- <이 파일>`과
  `git rev-parse <그 commit>^{tree}`로도 해석할 수 있다.
- 허용 branch=`research/r10-optical-mapping-local-20260920`; non-force push만 사용한다.

## COMPLETED_ACTIONS_AND_SCOPE

| Action | 상태 | 실제 범위 |
|---|---|---|
| RC-00 | 완료 | 원 native cwd와 isolated HEAD/tree, pending, source seal, donor 상태 확인 |
| RC-01 | BLOCKED | native client가 여전히 원 checkout; pending 미실행·미변경 |
| RC-02 | BLOCKED | independent review child/receipt 없음 |
| RC-03 | 탐색 완료 | 평탄 전단 source inner product → occupation → 밝기·온도 → STF → h 미분 |
| RC-04 | 부분 완료 | direct/moment/packed/time/caller 추적, mixed rank obstruction, 두 CAS draft |
| RC-05 | NOT_EXECUTED | 네 독립 축 실행 및 run-adjudicate 없음 |
| RC-06 | NOT_EXECUTED | 생산 T9 수정과 production regression/mutation은 미실행 |
| RC-07 | 탐색 완료 | 실제 saved SDSS mean response의 영점/monopole null 방향 |
| RC-08 | 반환 | 코드·원 실패·결과·검수 보류를 검토 후 isolated branch에 게시; merge/ready 없음 |

### ANISOTROPIC_ORACLE_RESULT

[실험 설명](../shear_ray/README.md), [수치 결과](../shear_ray/attempt02/result.json),
[수렴 그림](../shear_ray/attempt02/convergence.png).
다섯 STF basis와 혼합 한 개 × 7개 h. `dPi2/dh=-4Pi0 S`, `dTheta2/dh=-S`의
국소 우미분을 검사했다. 최대 점별 잔차 `8.89659e-14`, odd dipole/octupole 잔차
`2.63366e-15`, 최종 forward 상대오차 `4.74753e-4`, Richardson 상대오차 `1.78975e-6`.
wrong-sign 최소 상대오차 `1.99953`, wrong-power 최소 상대오차 `0.749991`로 오염 검출.
비영 Q/O/dipole 정규화·방향 반전과 timelike domain 검사 두 개도 통과했다.
고정 h의 격자 수렴과 h→0를 구별했다. 초기 source isotropy, source 면 x0=0,
h 길이/S inverse length, h||S||op<1 가정은 설명에 명시했다.
기존 Milne/Jacobi ODE는 수정하지 않았다. 기존 85 residual과 5 pytest는 반복하지 않았다.

### FIRST_PRESERVED_FAILURE

이번 최초 실패는 [attempt01.log](../shear_ray/attempt01.log)의 exit 1이다.
가장 거친 격자까지 최종 오차를 요구한 검사에서 실패했다. 원 source/config와
진단을 [attempt01](../shear_ray/attempt01/)에 보존했다. 한 번의 수정으로 최종 두
해상도 비교와 오차 감소를 요구했고, 수치 reference와 허용오차는 유지했다.
최초 실패를 덮어쓰거나 성공으로 바꾸지 않았다.
이전 local_execution의 환경 실패 및 의도적 exit-1 T9 진단도 그대로 남아 있다.

### T9_SCOPE_AND_PATCH_STATUS / CURRENT_CAS_CONTRACT_AND_ELIGIBILITY

현재 full/packed/public RHS의 초기 등방 ell=2 부호 불일치는 이전 source 진단과
이번 독립적인 host ray oracle에 부합한다. 이는 **native 독립 검수/CAS 통과가 아니다**.
`PATCH_REQUIRED_DIAGNOSIS`, production patch=`NOT_PERFORMED`.
[scope/caller 설명](../adapters/README.md),
[full/packed general-ell draft](../adapters/CAS_CONTRACT_FULL_PACKED_DRAFT.json),
[mixed draft](../adapters/CAS_CONTRACT_MIXED_DRAFT.json).
모든 축 NOT_EXECUTED; 계약은 draft이며 toolchain seal과 검수 후 freeze해야 한다.
FORMAL_T9 full/packed/mixed 모두 **NOT_ELIGIBLE**. 실제 `cas_gate.py run-adjudicate`
실행 없음. preflight/stored adjudicate/PASS 문자열로 승격하지 않는다.

Standalone mixed의 실제 isotropic-input shear map은 rank 1, 물리 STF는 rank 5다.
단순 부호/정규화 수정으로 해결할 수 없다. 이 함수의 tracked production caller는
검색 범위에서 발견되지 않았다. 실제 native `+A_mix @ y`는 다른 ver3 builder를
사용한다. 해당 경로에 standalone 진단을 자동 적용하지 않는다. 일반 ell 계수
수정에는 일반 ell 증명과 적용되는 public/shared massless-neutrino 검증이 필요하다.

### R9_ACTUAL_LAW_OR_NULL_RESULT / OBSERVED_METHODS_AND_ALPHA

[결과 설명](../r9/README.md), [실제 null 계산](../r9/result.json).
Donor `870bd67af159993ccde4ede9923424a475c01375`의 clean local 최신 상태를 확인했다.
저장 관측 response R(36×36), H(27×36), 초기 anchor T(36×36)를 직접 소비했다.
`A=[R,Rc]`, `v=(-c,1)`에 대해 `A v≈0`, R/A rank 36, H R rank 27, T R rank 36.
두 parameter tuple의 mean observation은 같고 자유 shell monopole 평균은 달라진다.
실제 CF3–SDSS 보정 전후도 검증했으며 최대 잔차 `6.60583e-15`.
이는 실제 additive eta mean-response의 unsupported target이다. selected law나
physical boost/tilt 응답의 구축은 아니다. covariance/noise law UNAVAILABLE,
CF4 selected law UNAVAILABLE, confidence/rejection NOT_COMPUTED, alpha spent **0**.
새 mock 실행 없음. arbitrary skew-G 결과는 orthogonal algebra control로 남긴다.

## INDEPENDENT_REVIEW_RECEIPT_OR_BLOCKER / BLOCKED_CONSUMERS

[resume_inspection](../resume_inspection.json)과 이전
[review_blocker](../../local_execution/review_blocker.json)를 함께 읽는다.
actual native client cwd는 `/home/cosmosapjw/Dropbox/bianchi/htt_base`이다.
등록된 source cwd는 `/mnt/sn850x2t/htt_base_e2e/HTT_R10_OPTICAL_MAPPING_LOCAL_RESEARCH/worktree`다.
`cl_57e1777283bfeda24c9ae6dcdb579394`는 child=null, unclaimed, 미실행이다.
원 등록 HEAD c8bd214와 현재 HEAD 차이도 있어 CLIENT_WORKTREE_MISMATCH 및
REGISTERED_IDENTITY_CHANGED가 보고됐다. frozen input 7개는 그대로 일치했다.
등록/hook/client identity를 편집하지 않았고 재-dispatch나 duplicate child를 만들지 않았다.
원 EXTERNAL-FUSION active run은 보존했다. [host_review](../host_review.json)는 host self-review다.

T9 full/packed/mixed promotion과 OP-07 이후 formal-dependent consumer는 차단된다.
missing physical jet/remainder provider는 whole-domain으로 유지한다. static Q/O는
JET_RESPONSE_LAW가 아니다. R9의 독립 경로는 원 의존성을 따르며 일괄 중단하지 않는다.
원 36-node DAG, canonical T9 v4/30·candidate40, R8 STOP_INVALID/unresolved pools,
P0 quarantine, PR284 deferred, PR4/NPIPE exclusion, alpha 배분은 변경하지 않았다.

## CHANGED_FILES / EXACT_COMMANDS_AND_EXIT_CODES

신규 파일은 전부 `docs/research_program/optical_mapping_r10_20260919/continuation_execution/`
아래다. source commit은 ray 코드·시도별 결과/실패·그림·두 검사, mixed probe/contract,
R9 null 계산, runtime/host review/명령 기록 27개다. return-only commit은 이 문서와
재개 prompt를 추가한다. 전체 목록은 `git diff --name-only 748dbdee <RETURN_COMMIT>`로 확인한다.
생산 코드·기존 결과·원 dirty checkout·다른 ref는 바꾸지 않았다.

[실행 명령과 exit code](../commands.json): 첫 oracle exit 1, 수정 후 oracle 0,
mixed probe 0, R9 0, 두 unittest 0, diff check 0. 최종 source 정리 후 R9를 새
`/tmp/htt-r10-r9-99b8e433-readback.json`에 실행해 저장 결과와 `cmp`했고 둘 다 exit 0이다.
수치 계산을 바꾸지 않은 미사용 경로 제거 후 정확한 committed source를 확인한 것이다.
source commit과 return-only commit을 구분하며 반환 문서 commit을 재검증된 물리 source로
세지 않는다. 게시 성공은 과학 admission이 아니다.

기존 storage 수정도 보존했다. `/dev/sda2`의 실제 mount는 `/mnt/extdrive`, data root는
`/mnt/extdrive/workdir`다. `/mnt/sn850x2t/htt_base_e2e/workdir` compatibility link는 정상이다.
원 checkout의 앞선 external_store/README/progress 경로 수정은 dirty 상태로 보존했고
연구 source commit에 섞지 않았다. bulk 복사나 새 다운로드는 없었다.

## NEXT_MINIMAL_ACTION

정확한 isolated worktree에서 **실제 native Codex client**를 열고
[CONTINUATION_PROMPT](CONTINUATION_PROMPT.md)를 사용한다. pending 등록을 먼저 inspect하고,
현재 source seal에 맞춰 지원되는 resume 또는 auditable supersede를 사용한다.
원 checkpoint의 bounded 독립 검수를 한 번 끝낸 뒤, 검수 finding에 맞춰 general-ell
full/packed 및 mixed 계약을 분리하여 동결하고 네 축을 실행한다. mixed rank obstruction은
먼저 범위/유효 부분공간을 해결해야 한다. 이번 host exploratory 성공으로 생산 부호를
즉시 바꾸지 않는다. 독립 R9 경로는 actual provider가 있는 action만 이어간다.
