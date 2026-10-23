# 남은 원래 acceptance와 재개 입력 — 2026-10-23

Owner: HTT campaign controller. 이 문서는 원래 scientific acceptance를 보존하는
미완료 checkpoint용 source/dependency 목록이다. 보편적인 자료 부재나 물리 no-go를
주장하지 않는다. 독립 branch-cut 검토와 K03 검토의 최종 상태는 아래 JSON에 연결한다.

## 원래 기준과 수정 범위

원래 external-output 기준은 **17/42**, V03 analytic alternate-output 범위는
**18/42**다. 이번 scoped 실험으로 원래 완료 수를 올리지 않았다.
원래 V03는 external Einstein–Boltzmann history response와 validation을 요구한다.
[별도 scope decision](../../ADVERSARIAL_AUDIT_20261022/V03_SCOPE_DECISION.json)의
`original_external_output_satisfied:false`를 유지한다. 기존 analytic subcase를
외부 산출물로 이름만 바꾸지 않았다.

[REMAINING_BRANCHES.json](REMAINING_BRANCHES.json)은 원래 V03를 메모리에서만
복원하여 원래25개 미충족 기준 전부와 의존 경로를 기록한다. 실제 DAG의 V03
scope decision이나 상태를 되돌리지 않는다. 명시적 외부 입력이 있는8개는
S02/S04/L03/H02/V03/B02/K03/K04이며, 나머지17개는 이 입력 경로에 의존한다.
S04와 K04는 자체 외부 조건과 upstream 의존성을 함께 가진다.

## 필요한 관측·처리·이론 입력

| 소비 노드 | 정확히 필요한 입력 | 확인한 공개 경로 및 현재 근거 |
|---|---|---|
| H02 → H04/H05/H06 | CF4 parent targeting·관측·탈락·quality/거리 selection의 ID/PGC/group/method 계보와 정규화, 공동 보정/군/PV 법칙, 해당 selection과 통계량의 source null/generator·seed | [새 intake](SOURCE_INTAKE/H02_ACQUISITION_RAW.json). CF4TF 및 combined CF4 논문은 realistic mocks를 저자 요청 경로로 명시한다. 공개 estimator 예제는 전체 source ensemble이 아니다. |
| S02 → S03/S04/S05/S06 | 실제 H03 source의 같은 congruence/frame/clock 광학→kinematic 응답, 유한-z/flow remainder, 방향·방법별 선택/공동 covariance, 기존2048 ID에 적용되는 normalized joint kernel | [새 intake](SOURCE_INTAKE/S02_ACQUISITION_RAW.json). 2048 ID·1/2048 가중치는 재사용했고 physical unknown mass=1을 보존했다. 97 LP 및 D07의9 endpoint crossing은 재실행하거나 해결된 것으로 바꾸지 않았다. |
| S04 | 위 source 아래 실제 selected likelihood 또는 물리적으로 정당한 더 좁은 functional의 유한 outer interval과 coverage | [CONGRUENCE 검토](R23-CONGRUENCE/INDEPENDENT_REVIEW.md). 형식적 광학 항등식만으로 실제 source law를 만들 수 없다. |
| L03 → L04/L05/L06, B03 | PR3 FULL/HM/OE의 같은 실현 CMB·noise·processed total/foreground, genealogy, split beam/weights/mask/QU, 공통/차등 잔차와 선택 법칙 및 해당 통계량 coverage | [새 intake와 primary URL](SOURCE_INTAKE/L03_ACQUISITION_RAW.json). Planck VIII은2018 half-mission FFP10 CMB 미제공과 FFP9 beam 차이를 설명한다. 기존8쌍과 split noise 계산은 재사용했다. PR4 quartet/ordering 수정은 PR3 공동 법칙의 대체물이 아니다. |
| V03 → V04/V05/V06, K05 | 원래 external-output에 맞는 calibrated global-tilt source/history transfer, 같은 frame·units·IC·시간 구간·검증 | [원래/수정 구분](../../ADVERSARIAL_AUDIT_20261022/V03_SCOPE_DECISION.json). analytic bolometric subcase는 재사용하되 원래 외부 응답은 미확보다. 새 native solver/ODE로 생산하지 않는다. |
| B02 → B03/B04/B05 | 실제 physical family/mode/history별 all-m T/E/B, IC/start·물질/전단/tilt 정규화, spin/frame/units/beam, recombination/constraint·equivalence 검증 | [atlas source intake 독립 검토](R23-ATLAS/INDEPENDENT_REVIEW.json). T-only 그림·chain·위치 covariance·temperature fixture는 불충분하다. 확인한 source 범위를 넘는 부재 주장은 없다. |
| K03 → K05/K06 | optical/radio centroid의 matter motion 법칙, true-depth·selection likelihood, Gaia spatial/calibration/time 응답, radio NNR/session-slope와 공동오차, 유한 remainder 및 curl/tilt 물리 전달 | [새 실제 PM 실험](K03_PM/REPORT.md). 이는 dust-following 가정을 실제 quasar에 부여하지 않는다. 조건부 rank6이라도 formal point가 small-velocity 영역 밖이며 원래 K03는 HOLD다. |
| K04 → K05/K06 | full CF4 selection·directional joint calibration/PV와 같은 normal/matter frame/source-clock의 물리 광학 응답 | [CONGRUENCE 검토](R23-CONGRUENCE/INDEPENDENT_REVIEW.md)와 H02 intake. null/undefined sector는 zero fill하지 않는다. |
| H04/V04 및 processing Jacobian | nominal PS1.nml, out_train_v7_1_bd17fix/SALT2.MODEL000의 INFO/error grids, CID010010/IDSURVEY15 observed nominal FITRES와 생성 binding; 이후 passband·attenuation·standardization·zHEL/zHD/PV의 공통 nuisance derivative | [R23-SN 검토](R23-SN/INDEPENDENT_REVIEW.json), [추가 공식/저자 경로 inventory](SOURCE_INTAKE/SN_SOURCE_EXTENSION.json). 고정 c447 release와 Dovekie953항목에서 미확인이다. 공개 README의 nominal-training 표현만으로 물리 byte 차이를 단정하지 않는다. |

628-target/274-distance의 새 조건부 likelihood는 실제 잔차 진단
T=4.5553218238, p=0.0009763241396으로 비판됐다. mock3890/4096 통과는
이 실패를 지우지 않는다. 공개 modulus 오차에 이미 포함된 보정/PV 성분을
임의로 다시 더하지 않는다. Pantheon 공개 total covariance도 한 번만 쓴다.
source-model K를 완전한 GR 광학 response라고 부르지 않는다.

## 취득·재개

실제 `/mnt/extdrive`는 `/dev/sda2`, fuseblk, rw다. 확인 시 여유 공간은
2,480,013,709,312 bytes였으며 용량 한도가 아니다. 데이터는 Git 밖에 둔다.
파일별·누적 다운로드 상한은 없고 기본2GiB reserve와 스트리밍 검사를 유지한다.
기존 receipt/hash/cache를 우선하고 새 제품은 release/schema/units/frame까지 검증한다.
인증 우회나 저자에게 메시지 전송은 수행하지 않았다.

```bash
.venv/bin/python scripts/htt_fetch_open_inputs.py --manifest docs/research_program/observational_publication_20261015/FRONTIER_20261020/ACQUISITION_MANIFEST.json
# 구체적으로 자격을 확인한 신규 제품의 ID만 선택한다. --budget-gib는 생략한다.
.venv/bin/python scripts/htt_fetch_open_inputs.py --manifest docs/research_program/observational_publication_20261015/FRONTIER_20261020/ACQUISITION_MANIFEST.json --ids "$QUALIFIED_PRODUCT_ID" --fetch
.venv/bin/python scripts/htt_open_input_packet.py
.venv/bin/python scripts/codex_harness/research_controller.py --state .agent-harness/runtime/r23-continuous/STATE.json summary
# 아래 두 값은 실제 신규 qualified receipt와 그 input identity로 설정한다.
.venv/bin/python scripts/codex_harness/research_controller.py --state .agent-harness/runtime/r23-continuous/STATE.json resume --task-id "$BLOCKED_TASK_ID" --evidence "$QUALIFIED_RECEIPT" --input-identity "$NEW_INPUT_IDENTITY"
.venv/bin/python scripts/codex_harness/research_controller.py --state .agent-harness/runtime/r23-continuous/STATE.json next --available-profile gpt-6.1-sol/medium --available-profile gpt-6-sol/high --available-profile gpt-6-astra/xhigh --available-profile gpt-6-astra/ultra
```

48-task campaign의 기존 state를 재초기화하지 않는다. `next`는 호출 계획이며,
실제 native spawn→ack→raw result record→별도 독립 검토를 host가 수행한다.
기존 R23-COMMON-E1/R23-Q ultra 사용과 실패/one-use/R9/UNKNOWN은 보존한다.
새로운 qualified 입력이나 검토 finding이 있으면 해당 가지를 즉시 재개한다.
K03의 별도 독립 검토는17개 검사를 통과했고 원래K03 input HOLD를 확인했다.
그 실제 결과를 record한 뒤 controller next를 실행한
[결과](CONTROLLER_FINAL_NEXT.json)는 `HOLD_UNRESOLVED_BRANCHES`, `ready:[]`다.
이 수치만으로 외부 제약을 판정하지 않고, 위25개 경로와 실제 source receipts를
별도 독립 reviewer가 확인했다. [검토와 closeout](REMAINING_BRANCHES_REVIEW.json)은
`PASS_SCOPED_INCOMPLETE_EXTERNAL_INPUT_CHECKPOINT`이며 open finding은 없다.
이 checkpoint는 원래42개 완주가 아니며 goal을 complete로 바꾸지 않는다.
