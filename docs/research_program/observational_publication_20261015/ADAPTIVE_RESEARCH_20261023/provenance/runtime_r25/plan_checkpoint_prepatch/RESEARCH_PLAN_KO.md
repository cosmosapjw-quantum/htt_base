# 조건부 관측 연구를 실제 논문 질문으로 연결하는 계획

Owner: HTT 연구 종합. 기준일 2026-10-23. Branch `research/htt-adaptive-methods-20261023`, 상속 source `10f3ea585c6608e794900efe7e4f8f42c0747a3b`. **초안 / 독립 검토 대기**. 기존 Astra 계약과 [일차 문헌 intake](METHOD_SOURCE_NOTES.md), [blind audit](BLIND_FRAMEWORK_AUDIT.md)를 종합한다. 자문·실행·독립 검토·물리적 수용은 구별한다. 요청/transport-selected `gpt-6.1-sol/medium`, observed runtime `UNKNOWN`. provider capacity 중단 뒤 같은 작업을 재개했으며 과학 실패나 새로운 task/budget으로 처리하지 않는다.

목표는 여섯 논문에 사용할 실제 관측 결과, 식별 가능 조합과 반례를 얻는 것이다. packet 발행이나 gate 수를 성과로 세지 않는다. 새로운 방법을 시험할 자유와 기존 물리 acceptance를 보존하는 일은 함께 가능하다. 원래 external **17/42**, analytic alternate **18/42**는 그대로이며 여기의 새 방법 노드는 그 분모에 더하지 않는다. [ADAPTIVE_DAG](ADAPTIVE_DAG.json)는 연구 계획으로서만 읽는다. 실제 실행 truth는 `.agent-harness/runtime/r23-continuous/STATE.json`에 append된 frontier와 native dispatch/ACK/raw/record/review다. 이 JSON을 controller 입력으로 직접 넣지 않는다.

## 왜 정체했는가: 원인과 반증

[blind source audit](BLIND_FRAMEWORK_AUDIT.md)의 기준은 소유자의 연구·보존·실행 요구와 독립 state-machine reasoning이었다. skill/harness는 평가 대상이며 스스로의 승인 기준이 아니다. baseline에서 두 입력 실패가 연구 의무의 종료로 바뀌고, 이미 쓴 ultra 뒤의 별개 unit-conversion correction이 막혔다. 이는 수치 연구의 불가능성 증거가 아니다. ACK가 아직 생길 수 없는 candidate를 요구한 것도 실제 launch 기록을 막았다. 반대로 ID/path만 바꾼 동등 method가 attempt0으로 열리는 것은 개선이 아니라 budget 우회다. correction은 같은 packet lineage/accounting을 보존하고, 새로운 method는 어떤 관측 질문·operative change·예측 차이가 생겼는지 밝혀야 한다. 같은 failure를 이름만 바꾸어 재실행하지 않는다.

원인에 대한 metacognitive 질문은 다음과 같다. 지금 막힌 것은 물리 target 자체인가, 불필요하게 넓은 target인가, 아니면 host 상태전이인가? 다음 계산은 어떤 두 설명을 구별하며 결과가 같으면 무엇을 버릴 것인가? 현재 불확실성 반경을 관측치로 가장하고 있지는 않은가? 예측 실패가 estimator 오류인지 source law 오류인지 구별하는 negative control은 무엇인가? 이 질문에 답이 없는 새 ledger나 gate는 연구 increment가 아니다.

물리적 반례도 남는다. split 관측 `g+f_common+f_split+noise`에서 `g→g+h`, `f_common→f_common−h`는 관측을 보존한다. 더 많은 optimizer로 common-mode를 제한할 수 없다. 실제 response가 없는 B02 atlas, S02 congruence, K03 source-class mapping도 계산 횟수로 생기지 않는다. 그러나 더 좁은 observable contrast, covariance/bias frontier, 조건부 shape law, 압축의 nonidentifiability는 지금 연구할 수 있다. 따라서 모든 방법이 소진되었다고 말하지 않는다.

## 상속할 실제 결과와 바꿀 연구 질문

[이전 한국어 종합](../METHOD_EXECUTION_20261023/README_KO.md), [13개 결과·review identity](../METHOD_EXECUTION_20261023/report_results/RESULT_SUMMARY.json), [실행 checkpoint](../METHOD_EXECUTION_20261023/SCIENCE_EXECUTION_CHECKPOINT.json)를 그대로 상속한다. report 자체와 개별 author RETURN의 작성 당시 pending 표시는 뒤의 독립 review와 구별한다. 최초 48개 task object, R24 history와 raw 실패, 소진된 R23-COMMON-E1/R23-Q ultra, R9 UNKNOWN을 삭제·초기화하지 않는다. 현재 결과의 후보·review는 변할 수 있으므로 새 R25 admission을 미리 쓰지 않는다.

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

## 첫 다섯 방법 노드와 성공·반증 기준

1. **R25-K03-DEPTH-COVROBUST — independent reviewer scoped PASS, host record 재확인.** 독립 reviewer가 candidate `sha256:bee5babe4f0610df53656beb2fd6dc69a99028d5d91e2e847e30be320ab61e9e`에 scoped PASS를 반환했다는 host 전달을 반영한다. live state에는 이 결정의 record가 아직 필요할 수 있으며 original K03 physical HOLD는 그대로다. 보정 M과 full24로12 restrictions를 만들고 C24+τ²I의 Gaussian reference와 moment upper-tail을 비교한다. 계약의 rank/common-mode/rotation/parity/permutation/Cholesky controls와 crossing residual을 통과하면 조건부 robustness curve가 성공 산출물이다. rank 실패나 cross-block 손실은 구현 반증이다. 작은 τ에 discrimination이 사라져도 과학적으로 유익한 null robustness 결과다. downstream은 bias frontier이며 K03 물리 acceptance는 유지한다.
2. **R25-K03-DEPTH-BIAS-FRONTIER — next, contract freezing 필요.** 기존 covariance curve에 coefficient bias ball을 추가하고 [T2](THEOREMS.md)의 exact witness/δ0, τ별 boundary를 구한다. 성공은 어느 bias·variance 조합에서 contrast가 설명 가능한지 재현 가능한 frontier와 witness다. 단위·metric·radius를 정하지 못하면 execution 전 해당 입력을 돌려준다. raw Gaia 재통과나 새로운 replicate는 불필요하다. 물리 Gaia bias 상계는 미측정이다.
3. **R25-CMB-CONDITIONAL-GRAM — running at planning intake; final review 미정.** 같은60 carrier에 공유 SO3와 O5/O7 action을 적용해 Gram/second moment는 유지하고 intrinsic shape와 relative orientation을 구별한다. 계약의 independent4096 pilot/16383 evaluation, joint max-rank, tie/zero/STF controls가 성공 기준이다. per-view 독립 회전이나 orthonormal→STF convention 오류는 반증이다. finite-MC rank가 작아도 실제 masked Planck invariance가 입증되기 전 cosmological p가 아니다. downstream은 spectral-response/processing qualification이다.
4. **R25-DISTANCE-CONDITIONAL-EVIDENCE — proposed, 실행 계약 미동결.** Universal Inference §§5–6의 기존 dependent averaging/non-iid conditional likelihood를 correlated catalogue에 특수화한다. 새 방법의 novelty를 주장하지 않는다. retained274행과 whole-group fold, full authored covariance를 써 T4의 normalized training conditional density/null supremum을 구성할 수 있는지 확인한다. 성공은 고정 covariance scenario마다 재현 가능한 conditional e-value/유효 fixed average 또는 null supremum·conditional law의 정확한 결손 보고다. correlated folds의 곱, validation으로 선택한 covariance를 confirmatory로 쓰기, plug-in score를 e로 이름바꾸기는 반증이다. 원래 H02/S02 부족 입력을 지우지 않는다.
5. **R25-SMICA-SPECTRAL-NULLSPACE — proposed, 실제 operator intake 우선.** 공개 weight/beam/recalibration identity를 읽어 M을 정의하고 target L에 ker M⊆ker L 여부를 검사한다. 성공은 actual operator의 식별 가능한 contrast 또는 Mh=0,Lh≠0 witness다. beam-corrected weight를 단순 frequency weight로 가정하면 실패다. 필요하면 source별 moment/constraint design을 비교한다. 이는 L03 common foreground의 정보 한계를 구체화하며 B02를 완료하지 않는다.

## acquisition endpoint의 정확한 뜻

아래 세 endpoint는 새 실행 가능 method task가 아니라 **외부 payload를 기다리는 명시적 의무**다. availability는 UNKNOWN이다. ADAPTIVE_DAG의 `external_live_obligations`가 입력·연결을 정의하며 이 이름만으로 controller task나 준비 완료를 만들지 않는다.

- `SOURCE_CLASS_RESPONSE_ACQUISITION`: original K03/K04에 연결된다. centroid/matter/source-class response, selected reported→true-depth/PM law와 residual Gaia spatial/cross-source covariance가 필요하다. depth-bias 결과를 이 payload 평가의 질문으로 전달하지만 acquisition 시작의 선행 조건으로 삼지 않는다.
- `MATCHED_PROCESSING_LAW_ACQUISITION`: original L03에 연결된다. actual FULL/HM/OE operator/weight estimation, total-field/noise/foreground/selection joint law, common-mode 제약과 cross-operator response가 필요하다. CMB conditional-Gram와 spectral witness는 관련 진단이며 payload 확보와 독립적으로 진행한다.
- `SOURCE_SELECTION_AND_COVARIANCE_ACQUISITION`: original H02/H04/S04에 연결된다. parent targeting/detection/rejection와 shared/group/PV calibration covariance 및 source/frame-qualified law가 필요하다. distance conditional-evidence는 이 의무를 완료하지 않는다. SN nominal parity product는 별도 미충족 입력이다.

## full tensor (x,F,Pi,Q,G_F)의 통계 적용

x는 coordinate scalar의 목록이 아니라 rank/parity/unit/frame이 있는 joint carrier다. K03 full24의 bin/slope cross block을 보존하고 Y18/Z18는 함수상으로 보유한다. CMB는 같은60 view의 full12 harmonic/STF와 공동 action을 유지한다. 네 scalar shape statistic은 등록된 projection이지 x의 대체물이 아니다. catalogue 간 joint law는 UNKNOWN이며 독립 product를 만들지 않는다.

F는 선형 support, convex outer, nonlinear image와 occupancy를 구별한다. 단위가 있는 bias/covariance ball의 support를 T2로 계산하며 sign-clean F 또는 분모가 필요한 항은 미정의 strata를 따로 둔다. Q_ref10 µas/year와 fixed CMB scale은 계산 gauge다. physical MES anchor가 없으면 physical Q는 undefined다. Pi_K03는 보유4096 공동 row의 **uniform empirical strict exceedance**이며 연속 Gaussian 확률이 아니다. CMB Pi는 명시된 conditional Haar law의 finite-MC reference이고 error interval도 그 reference만 대상으로 한다. physical Pi는 [0,1], unknown mass1이다. 기존2048 physical-unknown sample을 새 reference로 채우지 않는다. G_F는 anchored depth image와 모든 cross block을 유지하며 CMB processing-window path를 physical depth라고 부르지 않는다.

새 표본에 대한 prospective 통계는 지금의 data-adapted exploration과 분리한다. standalone reference alpha와 MC-check error budget을 명명하고 기존 R9 allocation을 재사용하지 않는다. source-qualified law와 selection을 동결하고 독립 검토한 뒤에만 새로운 coverage/confirmatory 결정을 고려한다. 식과 증명은 [THEOREMS](THEOREMS.md)에 있으며 상태는 DERIVED_PENDING_INDEPENDENT_REVIEW다.

## 실행 전이와 실제 종료 조건

host는 live state의 actual packet/agent/raw/record를 먼저 reconcile한다. actual dispatch 즉시 ACK하고 candidate는 record 시점에 묶는다. 하나의 독립 검토가 scoped PASS하면 downstream의 실제 준비된 action을 실행한다. 별개 counterexample와 bounded correction은 기존 cumulative usage 아래 승인된 연구 범위로 검토하며, exhausted ultra를 채우지 않는다. original HOLD의 descendants는 original acceptance용으로 차단하되 새 conditional DAG의 좁은 target은 독립적으로 실행 가능하다.

원래42개는 [ADAPTIVE_DAG](ADAPTIVE_DAG.json)의 original_acceptance_mapping에 ID/acceptance/dependency/source pointer/evidence를 하나씩 보존했다. dependency 변경은 new conditional method graph에만 있다. 원래 V03의 파일상 completed_scoped와 external17/alternate18의 구별을 그대로 노출하며 새 수용을 추론하지 않는다. 원래 결과와 새 결과를 합쳐42/42라고 세지 않는다.

현재 다음 executable checkpoint는 covariance scoped PASS를 실제 state에 기록하고 CMB의 아직 대기 중인 독립 검토를 host가 마친 뒤, depth bias frontier의 frozen contract를 받아 기존 요약자료만으로 수행하는 것이다. 그와 독립적으로 distance conditional-law 계약 및 actual SMICA operator intake를 준비한다. physical input이 필요한 branch는 exact payload HOLD를 남긴다. source push, 설치, live activation, merge, 투고는 서로 별도이며 이 계획은 어느 것도 완료했다고 보고하지 않는다.
