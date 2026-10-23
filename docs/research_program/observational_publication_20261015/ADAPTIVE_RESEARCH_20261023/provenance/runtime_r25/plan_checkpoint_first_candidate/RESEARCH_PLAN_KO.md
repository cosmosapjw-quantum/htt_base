# 조건부 관측 연구를 실제 논문 질문으로 연결하는 계획

Owner: HTT 연구 종합. 기준일 2026-10-23. Branch `research/htt-adaptive-methods-20261023`, 상속 source `10f3ea585c6608e794900efe7e4f8f42c0747a3b`. **현재 진행 checkpoint 후보 / 새 factual·claim 검토 대기**. 기존 Astra 계약과 [일차 문헌 intake](METHOD_SOURCE_NOTES.md), [blind audit](BLIND_FRAMEWORK_AUDIT.md)를 종합한다. 자문·실행·독립 검토·물리적 수용은 구별한다. 요청/transport-selected `gpt-6.1-sol/medium`, observed runtime `UNKNOWN`. provider capacity 중단 뒤 같은 작업을 재개했으며 과학 실패나 새로운 task/budget으로 처리하지 않는다.

목표는 여섯 논문에 사용할 실제 관측 결과, 식별 가능 조합과 반례를 얻는 것이다. packet 발행이나 gate 수를 성과로 세지 않는다. 새로운 방법을 시험할 자유와 기존 물리 acceptance를 보존하는 일은 함께 가능하다. 원래 external **17/42**, analytic alternate **18/42**는 그대로이며 여기의 새 방법 노드는 그 분모에 더하지 않는다. [ADAPTIVE_DAG](ADAPTIVE_DAG.json)는 연구 계획으로서만 읽는다. 실제 실행 truth는 `.agent-harness/runtime/r23-continuous/STATE.json`에 append된 frontier와 native dispatch/ACK/raw/record/review다. 이 JSON을 controller 입력으로 직접 넣지 않는다.

## 왜 정체했는가: 원인과 반증

[blind source audit](BLIND_FRAMEWORK_AUDIT.md)의 기준은 소유자의 연구·보존·실행 요구와 독립 state-machine reasoning이었다. skill/harness는 평가 대상이며 스스로의 승인 기준이 아니다. baseline에서 두 입력 실패가 연구 의무의 종료로 바뀌고, 이미 쓴 ultra 뒤의 별개 unit-conversion correction이 막혔다. 이는 수치 연구의 불가능성 증거가 아니다. ACK가 아직 생길 수 없는 candidate를 요구한 것도 실제 launch 기록을 막았다. 반대로 ID/path만 바꾼 동등 method가 attempt0으로 열리는 것은 개선이 아니라 budget 우회다. correction은 같은 packet lineage/accounting을 보존하고, 새로운 method는 어떤 관측 질문·operative change·예측 차이가 생겼는지 밝혀야 한다. 같은 failure를 이름만 바꾸어 재실행하지 않는다.

원인에 대한 metacognitive 질문은 다음과 같다. 지금 막힌 것은 물리 target 자체인가, 불필요하게 넓은 target인가, 아니면 host 상태전이인가? 다음 계산은 어떤 두 설명을 구별하며 결과가 같으면 무엇을 버릴 것인가? 현재 불확실성 반경을 관측치로 가장하고 있지는 않은가? 예측 실패가 estimator 오류인지 source law 오류인지 구별하는 negative control은 무엇인가? 이 질문에 답이 없는 새 ledger나 gate는 연구 increment가 아니다.

물리적 반례도 남는다. split 관측 `g+f_common+f_split+noise`에서 `g→g+h`, `f_common→f_common−h`는 관측을 보존한다. 더 많은 optimizer로 common-mode를 제한할 수 없다. 실제 response가 없는 B02 atlas, S02 congruence, K03 source-class mapping도 계산 횟수로 생기지 않는다. 그러나 더 좁은 observable contrast, covariance/bias frontier, 조건부 shape law, 압축의 nonidentifiability는 지금 연구할 수 있다. 따라서 모든 방법이 소진되었다고 말하지 않는다.

## 상속할 실제 결과와 바꿀 연구 질문

[이전 한국어 종합](../METHOD_EXECUTION_20261023/README_KO.md), [13개 결과·review identity](../METHOD_EXECUTION_20261023/report_results/RESULT_SUMMARY.json), [실행 checkpoint](../METHOD_EXECUTION_20261023/SCIENCE_EXECUTION_CHECKPOINT.json)를 그대로 상속한다. report 자체와 개별 author RETURN의 작성 당시 pending 표시는 뒤의 독립 review와 구별한다. 최초 48개 task object, R24 history와 raw 실패, 소진된 R23-COMMON-E1/R23-Q ultra, R9 UNKNOWN을 삭제·초기화하지 않는다. 현재 결과의 후보·review는 변할 수 있으므로 새 R25 admission은 아래의 실제 결과·현재 exact-hash review에 한정하며 원래 물리 acceptance로 확대하지 않는다.

| 상속한 실제 발견 | 다음 과학 질문 |
|---|---|
| 동일274행 거리 A/B 순위가 covariance에 따라 반전; 354/628 undefined | 그 순위가 정확한 conditional likelihood comparison에서도 지속하는가? selection unknown을 별도 식별구간으로 남길 때 가능한 주장은 무엇인가? |
| SN277행 total covariance 1회, calibration–flow cross block | source-overlap와 cross-catalog covariance를 알거나 제한할 때 CF4와 공통 target을 비교할 수 있는가? nominal producer parity는 별개 HOLD |
| selection Gamma=1에서도 최소 폭354/628 | auxiliary totals로 overlap 가능 여부를 먼저 반증할 수 있는가? balance를 MAR/parent propensity로 잘못 해석하지 않는가? |
| full CMB STF는 scalar-equal phase를 구별; common foreground unbounded | same Gram 아래 shape와 orientation의 차이는 무엇이며, 실제 processing에 그 reference law를 적용할 수 있는 조건은 무엇인가? |
| K03 755850행 1회 pass, slope 정보1.584853%, weak working-law tail | slope6와 다른 세 depth full-vector constancy는 어떤 covariance/bias에서 사라지는가? |
| optical STF8개 ellipsoid 모두 zero 포함; boost calibration 퇴화 | nonlinear quotient의 남은 cubic shape가 remainder보다 큰가? 필요한 independent response는 무엇인가? |
| full24/4096 empirical row 및 보정 Y18/Z18 | joint covariance와 common mode를 유지할 때 각 functional image가 얼마나 달라지는가? |
| CMB chirality finite carrier 비영이나 processing 부호변화 | mirror-sensitive 결정론적 지표와 cosmological parity를 분리할 관측 law는 무엇인가? |

## 모든 root blocker를 다루는 방법 공간

일차 출처와 적용 한계는 [METHOD_SOURCE_NOTES](METHOD_SOURCE_NOTES.md)의 절별 표를 따른다. 아래는 동등한 입력을 제조하는 방안이 아니라 명시적 가정 아래 더 좁은 질문을 푸는 연구다.

| 원래 root / 논문 | 실제 부족 입력 | 현재 가능한 방법과 downstream 조건 |
|---|---|---|
| S02/S04, P1 | common-congruence response, physical anchor, selected joint law | Fieller/geometric ratio inversion, marginal-coupling partial identification, selection/calibration feasibility; 실제 numerator/anchor 공동 law가 와야 물리 Q interval. 임의 radius10은 대체 불가 |
| L03, P2 | matched total-field/split/noise/foreground/weights/selection law와 common-mode 제한 | SO3/O(d) conditional reference, spectral nullspace witness, constrained/moment ILC의 실제 response feasibility. Gram law와 fixed-marginal bound는 별도 가정; source invariance와 null qualification 후에만 L04로 연결 |
| H02/H04, P3 | parent targeting/detection/rejection, group/shared calibration/PV covariance | marginal-variance worst coupling, covariance scenarios와 group conditional e-values, calibration overlap 검사. released SN total covariance를 다시 더하지 않는다. coverage는 source law로 별도 입증 |
| V03/V04, P4 | 외부 history의 same-frame 서로 다른 channel/depth response | optical cosmography, nuisance quotient, joint bias/remainder identified sets, canonical response rank. analytic alternate가 original external history를 충족하지 않는다 |
| B02, P5 | native polarized family/mode/history atlas 및 matched likelihood | 기존 문헌의 physical response 비교와 observable equivalence proof. response kernel에서 구별 불가능한 조합이라는 유효한 결과는 가능하지만 atlas completion은 아님. 내부 solver/ODE를 만들지 않는다 |
| K03/K04, P6 | centroid/matter/source-class, reported→true depth/PM, residual Gaia spatial/cross-source law | full24 depth covariance/bias frontier, source-class contrast design과 nonradial response acquisition. reported-z target은 true-depth history나 physical sigma/omega/A 측정이 아니다 |

Bayesian workflow의 반복적 model criticism은 가정 수정의 동기다. Berk 등의 simultaneous inference, Howard 등의 confidence sequence, Talts 등의 simulation calibration은 각각 지정 family·stochastic process·generative model에서 쓰는 도구다. 이미 본 한 sky를 다시 처리해 fresh independent validation을 만들거나 source law를 증명하지 않는다. parent selection·nonradial response·atlas acquisition은 정확한 missing payload를 찾는 독립 branch로 지속한다.

## 실제 실행 상태와 다음 전이

현재 요약은 [진행 checkpoint](PROGRESS_CHECKPOINT_KO.md)와 [ADAPTIVE_DAG](ADAPTIVE_DAG.json)의 `status_at_checkpoint`를 따른다. 과거 intake 당시 pending 표시는 이 checkpoint로 갱신한다. live state가 이후 진전하면 실제 packet·결과·review를 다시 reconcile한다.

| 방법 | 현재 실제 상태 | 결과와 다음 전이 |
|---|---|---|
| Depth covariance | 독립 검토된 조건부 completed | [결과](depth_covariance/RESULT.json), [review](reviews/COVARIANCE_REVIEW.json). 세 depth full-vector 귀무12restriction. 다음 bias 연구도 이미 완료했으므로 replay하지 않는다. |
| Depth bias frontier | 독립 검토된 조건부 completed | [결과](depth_bias/RESULT.json), [review](reviews/BIAS_REVIEW.json). full24 최소 zero-residual radius10.178814272459688 µas/year는 scenario metric 값이며 Gaia 실제 bias 상계가 아니다. |
| CMB conditional Gram | 수리 후 독립 검토된 조건부 completed | [결과](cmb_conditional_gram/RESULT.json), [최종 review](reviews/CMB_REVIEW_CLOSEOUT.json). 같은60view 공동 action의 reference law이며 physical observed p가 아니다. 실패 후보와 누적 비용을 보존한다. |
| Auxiliary overlap | 실제 실행 candidate, 독립 검토 대기 | [잠정 결과](auxiliary_overlap/RESULT.json). full628exact infeasible, coarse625positive weights, fine625even-signed infeasible; shared12model tensor law 보존. 다음은 해당 후보 독립 검토다. |
| Distance conditional evidence | 실제 실행 candidate, 독립 검토 대기 | [잠정 결과](distance_conditional_evidence/RESULT.json). fold arithmetic average E≈0.00018321835875531898. 탐색적 fixed-working-law 계산이며 실제 e-valid scientific claim admission은 아니다. training normalization의 이론과 실제 null-bound 수치 검토를 구별한다. |
| SMICA spectral nullspace | live execute-ready, 아직 실제 실행 안 됨 | 실제 queued packet을 dispatch·ACK·record할 차례다. 압축된 데이터의 정확 response-nullspace 질문이며 B02 atlas를 완료하지 않는다. |
| PR3 frequency acquisition | 실제 acquisition running | worker가30/44/70GHz LFI제품을 local validated로 기록했다.7개 전체와 독립 acquisition qualification은 pending이다. [사전 동결 tensor draft](R25-PR3-FREQUENCY-TENSOR_DRAFT.json)는 실제 acquisition manifest를 묶기 전 controller 입력이 아니다. |
| Gaia pair separation | 독립 contract review 완료, discovery append 전 | [입력](R25-GAIA-PAIR-SEPARATION_INPUT.json), [정확 hash closeout](reviews/GAIA_PAIR_WHITENING_CLOSEOUT.json). 직접 관측 pair response d와 beta를 구별하며 complete image/whitening이 없는 full-model tail은 unresolved다. 실제 계산은 아직 하지 않았다. |
| Gaia source-property intake | 독립 contract review 완료, discovery append 전 | [입력](R25-GAIA-SOURCE-PROPERTY-INTAKE_INPUT.json), [closeout](reviews/GAIA_PROPERTIES_CONTRACT_CLOSEOUT.json). source-ID-only exact join으로 host/class tags를 받는 계획이며 실제 속성 query/qualified product는 아직 없다. |

현재 source review-only patch는 **IN_REPAIR_PENDING_CLOSEOUT**다. [독립 counterexample](reviews/REVIEW_ONLY_SOURCE_FIRST.json)은 nested contract가 `INPUT→CHILD→running acquisition/data`로 숨겨진 경우와 candidate label은 같지만 실제 artifact가1→999로 바뀐 경우의 ACK 허용을 재현했다. 이 새 patch의 activation/PASS는 주장하지 않는다. 앞서 독립 closeout된 controller source candidate `4c3ff07ac861ad17334c5d6418d4ff21bf032c13f9eee9364e33dcaf9e329c45`는 실제 depth-bias·auxiliary·conditional-evidence 세 consumer 결과까지 사용되었다. 새 검토 경로의 결함은 이미 저장된 그 결과의 과학 verdict를 자동으로 바꾸지 않는다.

## acquisition endpoint의 정확한 뜻

아래 세 endpoint는 새 실행 가능 method task가 아니라 **외부 payload를 기다리는 명시적 의무**다. availability는 UNKNOWN이다. ADAPTIVE_DAG의 `external_live_obligations`가 입력·연결을 정의하며 이 이름만으로 controller task나 준비 완료를 만들지 않는다.

- `SOURCE_CLASS_RESPONSE_ACQUISITION`: original K03/K04에 연결된다. centroid/matter/source-class response, selected reported→true-depth/PM law와 residual Gaia spatial/cross-source covariance가 필요하다. depth-bias 결과를 이 payload 평가의 질문으로 전달하지만 acquisition 시작의 선행 조건으로 삼지 않는다.
- `MATCHED_PROCESSING_LAW_ACQUISITION`: original L03에 연결된다. actual FULL/HM/OE operator/weight estimation, total-field/noise/foreground/selection joint law, common-mode 제약과 cross-operator response가 필요하다. CMB conditional-Gram와 spectral witness는 관련 진단이며 payload 확보와 독립적으로 진행한다.
- `SOURCE_SELECTION_AND_COVARIANCE_ACQUISITION`: original H02/H04/S04에 연결된다. parent targeting/detection/rejection와 shared/group/PV calibration covariance 및 source/frame-qualified law가 필요하다. distance conditional-evidence는 이 의무를 완료하지 않는다. SN nominal parity product는 별도 미충족 입력이다.

## full tensor (x,F,Pi,Q,G_F)의 통계 적용

x는 coordinate scalar의 목록이 아니라 rank/parity/unit/frame이 있는 joint carrier다. K03 full24의 bin/slope cross block을 보존하고 Y18/Z18는 함수상으로 보유한다. CMB는 같은60 view의 full12 harmonic/STF와 공동 action을 유지한다. 네 scalar shape statistic은 등록된 projection이지 x의 대체물이 아니다. catalogue 간 joint law는 UNKNOWN이며 독립 product를 만들지 않는다.

F는 선형 support, convex outer, nonlinear image와 occupancy를 구별한다. 단위가 있는 bias/covariance ball의 support를 T2로 계산하며 sign-clean F 또는 분모가 필요한 항은 미정의 strata를 따로 둔다. Q_ref10 µas/year와 fixed CMB scale은 계산 gauge다. physical MES anchor가 없으면 physical Q는 undefined다. Pi_K03는 보유4096 공동 row의 **uniform empirical strict exceedance**이며 연속 Gaussian 확률이 아니다. CMB Pi는 명시된 conditional Haar law의 finite-MC reference이고 error interval도 그 reference만 대상으로 한다. physical Pi는 [0,1], unknown mass1이다. 기존2048 physical-unknown sample을 새 reference로 채우지 않는다. G_F는 anchored depth image와 모든 cross block을 유지하며 CMB processing-window path를 physical depth라고 부르지 않는다.

새 표본에 대한 prospective 통계는 지금의 data-adapted exploration과 분리한다. standalone reference alpha와 MC-check error budget을 명명하고 기존 R9 allocation을 재사용하지 않는다. source-qualified law와 selection을 동결하고 독립 검토한 뒤에만 새로운 coverage/confirmatory 결정을 고려한다. 식과 증명은 [THEOREMS](THEOREMS.md)에 있다. T7–T10과 T4 training-normalization clarification은 [별도 exact-hash blind SCOPED_PASS](reviews/THEOREM_SUPPLEMENT_REVIEW.json)를 받았다. theorem/source-note의 동결 당시 pending 표시는 역사 상태이므로 파일을 다시 쓰지 않았다. 이 검토는 데이터별 count, 관측 covariance qualification, numerical candidate admission이나 CAS4축을 승인하지 않는다.

## 실행 전이와 실제 종료 조건

host는 live state의 actual packet/agent/raw/record를 먼저 reconcile한다. actual dispatch 즉시 ACK하고 candidate는 record 시점에 묶는다. 하나의 독립 검토가 scoped PASS하면 downstream의 실제 준비된 action을 실행한다. 별개 counterexample와 bounded correction은 기존 cumulative usage 아래 승인된 연구 범위로 검토하며, exhausted ultra를 채우지 않는다. original HOLD의 descendants는 original acceptance용으로 차단하되 새 conditional DAG의 좁은 target은 독립적으로 실행 가능하다.

원래42개는 [ADAPTIVE_DAG](ADAPTIVE_DAG.json)의 original_acceptance_mapping에 ID/acceptance/dependency/source pointer/evidence를 하나씩 보존했다. dependency 변경은 new conditional method graph에만 있다. 원래 V03의 파일상 completed_scoped와 external17/alternate18의 구별을 그대로 노출하며 새 수용을 추론하지 않는다. 원래 결과와 새 결과를 합쳐42/42라고 세지 않는다.

현재 다음 executable checkpoint는 실행된 auxiliary/evidence 후보의 독립 검토, running PR3의 실제 partial/receipt reconciliation, queued SMICA의 실제 dispatch다. 새 review-only source patch는 counterexample repair와 독립 closeout 뒤에만 활성화한다. 별도로 검토된 두 Gaia 계약은 그 뒤 actual discovery/append할 수 있으며, PR3 tensor 실행은 qualified acquisition manifest binding을 기다린다. physical input이 필요한 branch는 exact payload HOLD를 남긴다. source push, 설치, live activation, merge, 투고는 서로 별도이며 이 계획은 어느 것도 완료했다고 보고하지 않는다.
