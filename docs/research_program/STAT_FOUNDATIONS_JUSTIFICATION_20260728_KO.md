# Premise anchor·response geometry 정당화 — 한국어 추적 요약

정본은
`docs/research_program/STAT_FOUNDATIONS_JUSTIFICATION_20260728.md`이다.
이 문서는 정본의 claim-ID별 한국어 추적 요약이며 독립 권위가 아니다.

상태:

- machine claim tier: `diagnostic_only`
- roadmap claim level: `roadmap_rescue_v1:C2`
- scientific status: `OPEN`
- PR-151 부분 자료 사용: 없음
- observed/native/external-transfer validation: 없음

## 채택된 토대

| 추적 ID | 한국어 요약 | 허용 경계 |
|---|---|---|
| `PA-THM-GAUGE-SUBLEVEL` | 등록된 closed·convex·absorbing anchor body에서 Minkowski gauge의 unit sublevel은 그 body다. | typed anchor geometry |
| `PA-THM-PRODUCT-BALL` | product block ball의 gauge는 block별 norm/radius의 최댓값이다. | typed block만 |
| `PA-THM-ONE-WAY-MES` | \(H_{\rm lin}\subseteq\mathcal A_{\rm MES}\)이면 \(H_{\rm lin}\Rightarrow\rho_{\rm MES}\le1\)만 허용된다. | 역명제 금지 |
| `PA-THM-RANK-INVARIANCE` | invertible anchor coordinate scaling은 등록된 supported subspace의 response rank를 만들지 않는다. | missing/singular sector 확장 금지 |
| `PR258-SQUARED-METRIC` | equivalence·unknown·margin은 모두 `OBSERVABLE_COVARIANCE_SQUARED_DISTANCE_V1`의 \(d^2\) 공간에서 계산한다. | anchor scaling은 identity |
| `PR258-GEOMETRY-BINDING` | equivalence report는 numeric nuisance tangent와 class provider·convention·nuisance-policy identity를 봉인한다. covariance-null operator는 nuisance projection 전에 보존한다. 양의 분산 channel의 correlation-null 잔차는 무차원화하고, 정확히 zero-variance인 channel은 임의 scale의 tolerance 대신 exact structural equality로 보존한다. | 단위 변경에 따른 판정 변화, nuisance orbit의 covariance-null 재명명, metadata-only rebinding 금지 |
| `PR258-EQUIVALENCE-CLOSURE` | tolerance edge의 connected component를 보수적 equivalence closure로 보고 direct edge와 전체 pairwise table을 보존한다. | pairwise equality 표현 금지 |
| `PR258-OPEN-SET-ABSTENTION` | native/missing, covariance null, equivalence, unknown, margin tie, PR-256 rank gate를 candidate보다 우선한다. | nearest-known 강제 배정 금지 |
| `PR258-SOURCE-GATE-TYPING` | neutral class와 local/global source-specific class는 하나의 collection-level source gate 아래 섞지 않는다. source-specific gate는 exact PR-256 report facade에서 만들고 동일 class·observable 순서·covariance·nuisance·provider/response·transfer 계약에 결속한다. | neutral은 `NOT_APPLICABLE`만 허용; 임의 status+digest, 다른 차원/library gate 재사용 금지; crosswalk가 필요하면 target 공간에서 geometry를 재계산 |
| `PR258-REOPENING-JOINT` | added observable은 support-node ID, joint covariance/cross-covariance, joint nuisance를 묶고 전체 graph를 다시 계산한다. | physical kernel reopening 자동 주장 금지 |
| `PR258-FINITE-SUPPORT-SENSITIVITY` | duplicate, refinement, expansion, contraction, boundary restriction의 typed class relation과 report identity를 검증한 뒤 별도 sensitivity로 보고한다. | baseline report 재라벨링 및 prior/volume robustness 명명 금지 |

## 폐쇄된 오해

- \(1-\rho\): additive radial margin
- \(1/\rho\): boundary까지의 multiplicative scale
- \(1/\rho-1\): relative boundary growth
- \(\max(\rho-1,0)\): raw anchor excess

raw excess는 e-value가 아니다. e-value에는 별도 joint null law와
calibration receipt가 필요하다.

`J1-EXACT`와 `J2-UNIFORM`의 강한 일반형은 등록된 counterexample lane에서
`REFUTED_OR_RESTRICTED`다. 더 좁은 정리를 제안하려면 새 domain·assumption·
joint law·검증 계약이 필요하다.

MES는 normalizer benchmark에서 universal winner가 아니며
`ONE_ANCHOR_AMONG_FAMILY`로 분류된다. 목적별 Pareto 비교는 가능하지만
invertible reparameterization을 information gain으로 부르지 않는다.

## PR-258 benchmark 추적

정본 artifact:
`docs/generated/pr258_open_set_response_classes/open_set_benchmark.json`

artifact는 `owner=common`, `artifact_mode=internal_exploratory`이며
synthetic feature space라 sky support가 적용되지 않는다. null 상태는
관측 null calibration이 아닌 등록된 synthetic generator cell이고,
covariance는 exact-byte로 고정된 synthetic covariance다.

- seed: `20260728`
- cell별 held-out draw: 20,000
- false response-class candidate rate: 0
- equivalence-class coverage: 1
- preregistered unknown-generator conditional detection: 1
- 전체 registered mixture abstention rate: \(2/3\)
- maximum MCSE: 약 0.001925
- 등록된 finite-support perturbation의 decision-change rate: 모두 0

이는 synthetic software cell만 검증한다. 관측 우주, FLRW departure,
물리 source 또는 Bianchi family에 대한 결과가 아니다. unknown rate도
등록된 synthetic generator에 조건부이며 uniform open-set theorem이 아니다.
benchmark envelope은 known/unknown baseline, equivalence cell, 다섯
support perturbation의 각 equivalence report identity를 개별적으로 묶고
typed baseline/perturbed class 관계와 하나의 frozen decision protocol을
강제한다.

## 금지된 승격

- 역사적 \(x_C\)의 동결된 값과 허용 용도는
  `BC1_LEGACY_PROJECTION`으로만 보존하며, 이를 FLRW
  distance·occupancy·evidence로 해석
- 표현 또는 report type이 세분화되었다는 이유만으로 \(x_C\)나
  역사적 결과의 claim tier를 올림
  (`BC2_NO_REPRESENTATION_PROMOTION`)
- anchor stress나 response distance로 source/family를 판정
- prior-induced rank를 data identification으로 보고
- missing covariance/response/transfer를 0으로 대체
- PR-151 부분 자료나 old Rust science output을 validation에 사용
- pre-native analytic/synthetic response를 native로 재명명
- `RESPONSE_CLASS_CANDIDATE`를 Bianchi family identification으로 서술

현재의 최종 문장은 다음까지다.

> PR-258 후보는 typed premise anchor와 covariance-supported response
> geometry를 explicit abstention을 가진 검증 가능한 중간층으로
> 구현하도록 제안한다. 구현·검증 완료 상태는 candidate seal,
> read-only review, latest-target integration과 병합 뒤에만 기록한다.

FLRW departure 검출이나 Bianchi family identification은 주장하지 않는다.
