# 실제 연구 진행 checkpoint — 전체 완료 아님

기준일2026-10-23, owner HTT. 이 문서는 live state·실제 결과·exact-hash 독립 review를 읽어 갱신한 **factual checkpoint 후보**다. 별도 사실·claim 검토 대기이며 과학 실행, 새 query, source code/state 변경, commit/push는 하지 않았다. 원래 external **17/42**, analytic alternate **18/42**와13개 R24 상속 결과는 그대로다. 기존48/62task object·원래 packet/cost·one-use·소진 ultra·R9 UNKNOWN은 보존한다.

## 완료와 후보를 구별하는 현재 상태

- **조건부 연구3개 independently completed:** [depth covariance](depth_covariance/RESULT.json)와 [review](reviews/COVARIANCE_REVIEW.json), [depth bias](depth_bias/RESULT.json)와 [review](reviews/BIAS_REVIEW.json), [CMB Gram](cmb_conditional_gram/RESULT.json)와 [최종 review](reviews/CMB_REVIEW_CLOSEOUT.json). 이 완료는 original physical K03/L03를 승격하지 않는다.
- **실행된 후보2개, independent review pending:** [auxiliary overlap](auxiliary_overlap/RESULT.json), [conditional evidence](distance_conditional_evidence/RESULT.json). 결과 수치는 아래처럼 잠정 표시한다.
- **실제 외부 acquisition running:** PR3 frequency task에서30/44/70GHz LFI3제품이 worker receipt상 local validated다. 전체7제품 qualification·independent review는 pending이다. raw 파일과 실제 receipt는 external cache에 있으며 이 문서 작업에서 다운로드나 큰 파일 재검증을 하지 않았다.
- **SMICA executable queued:** live state상 ready/execute다. 실제 dispatch/결과를 아직 주장하지 않는다.
- **Gaia2계약 independently reviewed, discovery append 전:** [pair exact-hash closeout](reviews/GAIA_PAIR_WHITENING_CLOSEOUT.json)와 [properties closeout](reviews/GAIA_PROPERTIES_CONTRACT_CLOSEOUT.json). contract PASS는 실제 pair production이나 metadata intake의 실행·qualification이 아니다.

## 현재 결과가 말해 주는 것

[Covariance 결과](depth_covariance/RESULT.json)의 tau0 contrast statistic은381.19923194468424다. standalone .05 Gaussian-reference crossing tau≈2.139565358456088 µas/year, moment-reference crossing≈0.3775523774040789다. 이것은 선택한 covariance upper-envelope 가정 아래 sensitivity이며 실제 Gaia covariance ceiling·관측 p가 아니다. [Bias 결과](depth_bias/RESULT.json)는 full24에서 zero residual 최소 scenario radius10.178814272459688 µas/year와 witness를 보존한다. measured physical bias라고 부르지 않는다.

[Auxiliary 잠정 후보](auxiliary_overlap/RESULT.json)는 전체 628개 frame의 세 unsupported cell에서 exact gap−1/628을, supported625coarse calibration에서 positive weights와 concentration ESS271.53708568525417을 기록했다. fine velocity functional은 target sum2547, 관측0으로 signed balance조차 불가능하다.625는 바뀐 estimand이고351outcomes가 여전히 missing이다. quality269accepted/1other/3confused/1nondetection은274observed의 분류이며354undefined의 quality는 UNKNOWN이다. 같은 weights를 모든12scalar/vector/STF carrier에 적용해 joint atomic law를 유지했다. 이 결과는 아직 독립 numerical review 전이며 MAR나 outcome transport law를 입증하지 않는다.

[Conditional-evidence 잠정 후보](distance_conditional_evidence/RESULT.json)는274행/5whole-group folds에 대한 fixed eight-component numerator mixture와 four-null supremum의 fold arithmetic average를 계산했다. log average≈−8.604831899198585, E average≈0.00018321835875531898이다. 현재 자료·가정의 탐색적 계산이며 독립 review와 실제 selected/adaptive law 및 outward null-bound numerical qualification이 필요하다. normalized training-measurable q 자체는 training-fit uncertainty 적분을 필요로 하지 않는다는 이론과 이 실제 후보의 acceptance는 구별한다. frozen candidate 보고서 문구는 별도 실제 review/repair로 다룬다.

## 수학 검토와 controller source 수리의 범위

[T7–T10/T4 별도 blind review](reviews/THEOREM_SUPPLEMENT_REVIEW.json)는 theorem SHA `3a4d900390be3eda276f6bbb549f3b2066aa56138326e9fbb97c8ca7ac93429e`, source-note SHA `a992055234dcb01a4c40bfaccc3f0bf2f005b72d66ec7fa1368b6be9074af707`에 SCOPED_PASS다. frozen 문서의 당시 pending label은 보존했다. 데이터별 witness count, numerical certificate, physical coverage, 전체 scientific admission은 그 review 밖이다.

현재 새 review-only source patch는 **IN_REPAIR_PENDING_CLOSEOUT**다. [최초 blind review](reviews/REVIEW_ONLY_SOURCE_FIRST.json)는 nested declared contract `INPUT→CHILD→running acquisition/data`의 충돌/변경을 seal하지 못한 사례와, candidate label 동일 상태에서 실제 artifact1→999변경을 ACK한 사례를 재현했다. 기존 supplied tests9개가 통과해도 이 구체적 결함은 남았다. source repair와 독립 closeout 전 새 patch의 활성화를 주장하지 않는다. 앞선 source candidate `4c3ff07ac861ad17334c5d6418d4ff21bf032c13f9eee9364e33dcaf9e329c45`는 실제 depth-bias·auxiliary·conditional-evidence3consumer결과에 사용되었다. source push·local install·fresh-session activation·현재 새 source patch는 구별하며 background daemon을 주장하지 않는다.

## 다음 실제 전이와 외부 residual

1. 이미 실행된 auxiliary/evidence의 exact candidate·raw를 독립 검토한다. concrete repair가 필요하면 최초 실패·후보와 cumulative limits를 보존한다.
2. running acquisition의 실제 partials·HTTP receipts를 reconcile하여7제품을 검증한다. success/manifest/독립 review 없이 `pr3_frequency_maps`를 qualified로 표시하지 않는다. [PR3 tensor draft](R25-PR3-FREQUENCY-TENSOR_DRAFT.json)는 actual acquisition manifest가 묶여야 실행 계약이 된다.
3. queued SMICA packet을 실제 dispatch·ACK·record하고 결과를 검토한다. 새 review-only controller source는 현재 두 결함의 repair/independent closeout 후에만 활성화한다.
4. [Gaia pair 입력](R25-GAIA-PAIR-SEPARATION_INPUT.json), SHA `620d92030d235ee6ed8fb5e6d7ff999f4777f7540abbcb1841c23af50e878d50`와 [properties 입력](R25-GAIA-SOURCE-PROPERTY-INTAKE_INPUT.json), SHA `00508df7ec44ab6680ab8291868acaa203247aba18aaabfe2eaf029fc6ddad60`는 actual discovery/append를 기다린다. 결과를 미리 가정하지 않는다.

P1에는 common-congruence response와 physical anchor/selected joint law, P2에는 matched processing·noise/foreground/common-mode law, P3에는 parent selection와 source-qualified shared calibration/group/PV covariance, P4에는 original external same-frame history response, P5에는 external native polarized family atlas, P6에는 source-class/nonradial/true-depth response와 actual Gaia joint law가 여전히 필요하다. 조건부 observable result나 metadata tag가 이 payload를 제조하지 않는다. [전체 계획](RESEARCH_PLAN_KO.md)과 [ADAPTIVE_DAG](ADAPTIVE_DAG.json), 기존 METHOD_FRONTIER는 계획이며 current controller input이 아니다. 원래42acceptance와 dependency는 그대로이고 전체 방법 소진·42/42·publication 완료를 주장하지 않는다.
