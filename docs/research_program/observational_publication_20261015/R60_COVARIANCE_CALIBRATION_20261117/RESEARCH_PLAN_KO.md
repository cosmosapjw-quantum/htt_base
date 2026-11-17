# R60 수렴 연구계획: 실제 관측에서 물리적 결론으로

이 계획의 기준은 이번에 실제로 계산한 R60 결과와 R58의 원 관측 실험이다. 목표는 여러 연구주제의 이름을 하나의 우주론 주장으로 묶는 것이 아니라, **한 개의 primary 관측 estimand를 확정하고 그 물리 해석을 결정하는 의존성을 순서대로 닫는 것**이다. 아래는 프로젝트 계획이며 로컬 agent용 재개 프롬프트가 아니다.

## 1. Primary 논문과 완료 기준

Primary estimand는 CF4의 apparent angular log-distance STF tensor kappa와 그 방향별 함수 kappa:nn이다. 공동 carrier의 V,d_H와 cross-depth covariance는 nuisance/physical interpretation을 위해 함께 유지한다. Primary 결과는 하나의 p-value 대신 (covariance amplitude, calibration allowance, finite velocity-history allowance)에 대한 confidence set과 breakdown surface다.

가능한 원고 제목은 “Calibration sensitivity of tensor inference for local cosmic anisotropy”다. 현재 자료에서 다음 주장을 고정한다.

1. 실제 선택된 CF4 그룹에 조건부인 apparent tensor likelihood를 재현한다.
2. 물리적 shear/acceleration 해석에 필요한 calibration body를 명시하고 최소 허용량을 계산한다.
3. full tensor와 특정 scalar/axis reduction 사이에 실제 정보 손실이 있음을 관측 사례로 보인다.
4. 조건부 결론을 바꾸는 covariance·radial response 가정을 정량화한다.
5. strong cosmological detection이 없어도 이 측정과 검증을 결과로 채택한다.

제출 gate는 matched-source comparator, independently calibrated uncertainty, repeatable result package다. 새 universal tensor theorem 또는 모든 Bianchi 유형의 완결된 inverse problem을 primary 논문의 선행조건으로 요구하지 않는다. 동시에 그 물리 목표가 이미 해결됐다고 표시하지 않는다.

## 2. 완료된 실제 분석

| 단위 | 원 자료·기준 | 실행 결과 | 현재 상태 |
|---|---|---|---|
| CF4 full covariance sensitivity | 35,970 groups; R58 32D carrier; 7 nuisance operators | p11 crossing1.26462, p5 crossing1.24267 | complete_scoped |
| CF4 calibration Q/F | 같은 carrier; full-sky RMS body | robust STF threshold1.31475mmag | complete_scoped |
| CF4 shape classification | 5D marginal ellipsoids | 7/7 explicit axial witnesses | complete_scoped |
| Finite radial velocity | pinned raw data/operator 재구성 | rank14, weak slope, physical-range failure; finite budgets analyzed | complete_scoped |
| Commander lowell morphology | owned PR3 R51 coefficients | full STF + stable matched axes vs88.5deg axis-selector switch | complete_scoped |
| Quaia/NVSS dipole sensitivity | R54 vector and mock/receipt covariance | Quaia nominal crossing.253689; finite-mock tails preserved | complete_scoped |
| Legacy numerical repair | covariance-amplitude consumer | false boundary shortcut removed; independent counterexample and400mode regression | complete_scoped |

complete_scoped는 해당 관측/수학 질문을 계산했다는 뜻이다. cosmological shear, global tilt, omega 또는 Bianchi class의 검출을 뜻하지 않는다.

## 3. 후속 의존성 DAG

아래 노드는 연구 계획의 의존성이다. 요청하지 않은 자동 실행이나 새 PR 생성 예약이 아니다. 새로운 audit-only loop는 만들지 않는다.

- NEXT-01: 공통 raw sample에서의 경쟁 추론 비교.
- NEXT-02: empirical calibration body 및 covariance/coverage 검증.
- NEXT-03: NEXT-01+NEXT-02를 사용한 primary CF4 물리·통계 판정과 원고.
- NEXT-04: Commander 전용 stochastic law와 physical shear-history bridge.
- NEXT-05: source-redshift별 count/velocity response와 local boost–tilt 구별.
- NEXT-06: 검증된 transfer를 갖는 제한된 Bianchi families의 분류.

NEXT-01과 NEXT-02는 현재 primary의 필수 의무다. NEXT-04–NEXT-06은 각각의 물리 주장을 선택할 때 추가한다. 모든 것을 한 번에 joint likelihood에 넣어 불확실한 response를 숨기지 않는다.

## NEXT-01 — 동일 관측 실험의 comparator

### 입력과 설계

기존 selected_source_observables.npz의 group IDs, original distance-modulus records와 survey labels를 출발점으로 쓴다. R58의 four-window grouping과 겹치는 redshift 범위를 유지한 benchmark A, Vicente의 .01–.05 범위와 교집합한 benchmark B, Kalbouneh의 .01–.1 범위에 대응하는 benchmark C를 구별한다.

각 benchmark는 동일 row IDs·z·n·mask·measurement errors·cosmic covariance·monopole/zero-point nuisance·로그 정규화를 공유해야 한다. grouped catalogue와 ungrouped/Tully–Fisher subsample의 차이가 남으면 matched comparison으로 표시하지 않는다. raw linewidth/latent-distance calibration이 필요한 Stiskalek forward model은 그 원 입력과 selection law를 확보한 경우에만 직접 수치 비교한다.

### 실행할 분석

같은 likelihood에서 full harmonic/STF, fixed common-axis restriction, 기존의 scalar amplitude/axis summary를 비교한다. R60의 generic axial witness는 common-axis multi-ell/multi-shell fit을 대신하지 않으므로 그 제한을 source operator에 직접 적용한다. scalar summary 비교는 어느 likelihood information을 잃는지 likelihood ratio 또는 parameter-recovery loss로 정한다. 원 표현이 GLS와 수치적으로 같으면 tie로 채택한다.

표본선택·mask·모형 변경마다 다른 관측을 만들기보다, 공통 source-level forward model에서 operator별 response와 covariance를 유도한다. fixed32D compression과 raw catalogue inference를 소규모 동일 input subset에서 먼저 비교해 충분통계 손실을 측정한다. 축 또는 최대 direction은 data-dependent 선택이므로 해당 전체 선택 절차를 simulation에 포함한다.

### 산출물과 판정

공통 source manifest, forward-model contract, signed estimates/covariance, predictive residuals, method-by-method benchmark table을 생성한다. 논문의 reported significance 수치끼리 직접 우열을 비교하지 않는다. 조건이 맞는 비교에서 우월성 없으면 이를 명시하고 novelty를 calibration robustness application으로 제한한다.

이 작업이 아직 실행되지 않은 이유는 경쟁 논문에 맞춘 전체 원표본/latent-distance/selection 계약이 현재 R58 compact carrier에 포함되지 않기 때문이다. 새 pseudo-method를 만들어 특정 저자의 구현으로 부르지 않는다.

## NEXT-02 — Physical calibration과 stochastic coverage

### Calibration body를 실제 자료에서 정하기

R60의1.315mmag는 adversarial full-sky RMS quadrupolar **평균** bias다. 이 값을 per-object noise나 scalar zero-point uncertainty와 직접 비교하지 않는다. overlapping galaxies/groups, independently calibrated distance indicators, survey hemisphere and declination support를 이용해 calibration field를 같은 STF basis와 같은 O_m으로 전달한다.

원 자료가 허용하면 survey zero points, latitude/declination templates, depth-dependent calibration, indicator-dependent terms의 joint estimate/covariance를 구한다. angular support가 겹치지 않는 survey 사이의 zero point와 physical dipole은 별도 식별 문제로 남긴다. 양의 empirical calibration bound를 정당화하지 못하면 physical shear confidence set은 조건부 family로 발표한다.

### Cosmic covariance와 selection

현재 S는 선형 z=0 LCDM body다. 성장률/unequal-time evolution, distance versus redshift-space position, non-linear dispersion, catalogue grouping, distance-error distribution 및 selection이 관측 operator의 covariance에 미치는 영향을 같은 source law에서 평가한다.

우선 기존 cache의 source law와 정확히 일치하는 conditional recovery를 검증하고, 그다음 한 번에 하나씩 물리적 변경을 추가한다. conditional Gaussian draw에서 95% coverage를 얻었다는 사실만으로 실제 survey coverage를 인증하지 않는다. 필요시 source-level injection을 measurement pipeline 전체로 통과시키며 masks와 group selection까지 재실행한다.

새 pair sum의 비용은 N² pair count와 tile memory, 기존 profiler의 실제 runtime을 기반으로 pilot 측정한 뒤 정한다. 장시간 계산을 선언만 하고 실행된 것으로 표시하지 않는다. 사용할 cosmological spectrum·redshift evolution·window operator hash를 고정하고 cache identity와 semantic reuse를 구별한다.

### Validation 기준

Primary target은 kappa의 simultaneous95% confidence set과 지정된 directional support다. coverage를 평가할 실제 반복수는 binomial interval이 판정을 가를 만큼 확보한다. 예를 들어 N=2000에서 true95% coverage의 단순 binomial 표준오차는 약0.00487이다. 이는 설계 예시이고 실제 survey simulation이 실행되었다는 뜻이 아니다.

null false-positive, alternative recovery, calibration shifts at0/threshold/above threshold, covariance amplitude near1/1.24/1.27, bounded-flow cases를 동일 사전 지정 grid에서 검사한다. mock generator를 observed anomaly에 맞춰 재조정한 뒤 그 mock으로 발견 유의도를 인증하지 않는다.

NEXT-02의 산출물은 empirical calibration body 또는 정확히 조건부로 남긴 body, covariance uncertainty family, selection-aware coverage/power와 source-bound failure log다.

## NEXT-03 — Primary CF4 판정과 원고

NEXT-01과 NEXT-02가 끝나면 primary result는 다음 중 하나로 결정한다.

- 보정·covariance family 전체에서 physical target이 영점을 배제하고 selection-aware calibration도 유지되면, 그 family와 approximation order에 한정해 physical evidence를 보고한다.
- apparent kappa는 측정되지만 physical pullback이 영점을 포함하면, anisotropy의 관측과 원인 식별을 구분하여 calibration-limited measurement로 보고한다.
- 실제 survey law에서 apparent result가 유지되지 않으면, 그 원인과 threshold를 결론으로 채택한다.

그 이후 유의도를 되살리기 위한 새로운 cut/model 탐색을 자동으로 이어가지 않는다. 새로운 과학 질문이 있을 때만 별도로 scope를 정한다.

원고 구조는 observation/operator→single joint likelihood→calibration/velocity/covariance geometry→actual results→matched comparison→physical interpretation 순서다. CMB branch-switch는 tensor 정보 보존의 관측 검증 또는 별도 note로 배치한다. 서로 다른 source law를 결합한 joint cosmological fit처럼 서술하지 않는다.

## NEXT-04 — Low-ell physical observables

### 지금 보존한 관측

Commander primary Q_T, signed harmonic coefficients, eigenframe와 powers ell2..6을 그대로 사용한다. SMICA와의 결정론적 비교는 pipeline difference이며 독립 realization이 아니다. 두 pipeline을 독립 cosmic sample로 곱하지 않는다.

### 필요한 입력과 실제 실행

Commander-specific beam/transfer, map kinematic-quadrupole removal convention, same mask/finite-l estimator를 통과한 Commander matched simulations의 complete input receipt가 필요하다. 보유 incomplete simulation inventory에서 완전한 subset과 partial/noise-missing 파일을 명시하고 충분한 law가 될 때만 stochastic inference를 시작한다.

T-only history map을 먼저 검증하고, E를 추가할 때는 independent noise/foreground calibration이 통과해야 한다. 기존 E variance floor가 tested maps에서 조정되었다는 문제를 새로운 covariance receipt 없이 “claimable”로 되돌리지 않는다.

현재 sigma를 얻는 history는 perfect-fluid, finite stress basis, free late-time history 중 명시한 family로 제한한다. photon/neutrino anisotropic stress, initial conditions, Thomson kernels, boundary normalization을 원 논문/검증된 implementation과 연결한다. 외부 Bianchi solver/native new solver 없이 source-bound transfer를 활용하는 현재 repo 정책을 따른다.

### 완료 기준

temperature tensor→integrated shear functional의 response equality, zero/FLRW limit, sign/unit test, matched-null recovery를 통과한다. present shear inference는 허용한 history 전체에서 식별성을 검사한 뒤에만 보고한다. CMB morphology와 CF4 axes의 비교는 Galactic↔ICRS transform과 common rotational statistic을 먼저 고정한다.

## NEXT-05 — Dipole와 local boost/global tilt

### 관측 설계

관측자 O, radiation R, matter M, homogeneous normal N을 별도 endpoint로 기록한다. CMB aberration/Doppler estimator는 beta_OR에, source counts는 redshift/selection-weighted population response에, distances는 relative velocity와 kinematic field에 대응한다. 하나의 beta coefficient를 모든 관측에 공통으로 넣지 않는다.

Quaia/NVSS에서는 원 catalog selection, flux/spectral slope, redshift distribution, higher clustering, declination/latitude systematics를 포함한 null/injection을 만든다. R60의 mock-only tail과 receipt-systematic nominal tail을 모두 baseline으로 유지한다. 새 null은 같은 estimator·mask를 사용하고 추가 systematic이 empirical input인지 sensitivity family인지 구분한다.

### 판별량

finite radial response를 물리적으로 허용된 depth/velocity basis로 교체한다. original d_H와 flow coefficient의 covariance/identifiable combinations를 보존한다. 현재 formal free fit의 큰 속도는 initialization이나 prior center로 쓰지 않는다. first-order Doppler/log-distance 근사의 두 번째 차수 오차가 측정 정확도보다 작다는 것을 injection으로 검증한다.

global tilt를 말하려면 beta_MN(t), beta_RN(t)의 동역학과 source congruence가 필요하다. 두 서로 다른 probe가 같은 상대속도 조합만 측정하면 kernel이 줄지 않으므로, 추가 response가 실제로 kernel을 줄이는지 J_eff의 rank와 physical functional의 projection으로 확인한다. 임의 prior만 넣어 quotient를 좁힌 것을 새 측정으로 부르지 않는다.

### 완료 기준

observable-specific response, common frame and units, cross-probe covariance/independence justification, alternative recovery가 모두 갖춰져야 한다. universal boost/tilt no-go나 모든 tilt의 배제는 목표로 삼지 않는다. 지정한 finite family에 대한 구별 또는 미식별 결론을 채택한다.

## NEXT-06 — Anisotropy와 Bianchi family

Bianchi geometry에는 spatial structure constants, metric/curvature variables, matter source와 tilt constraints가 필요하다. apparent STF의 eigenvalues는 morphology 관측이다. R60의7개 axial witnesses는 이 계층을 구분하는 baseline으로 쓴다.

초기 비교 대상은 literature-bound near-isotropic transfer가 있는 제한된 families로 정한다. 동일 retained sky/catalogue estimator에서 forward templates를 평가하고, amplitude/orientation/history nuisance를 profile한다. Einstein-compatible dynamics와 Lie-algebra constraints를 어기는 임의 tensor template는 배제한다.

한 family가 맞는다는 posterior probability를 계산하려면 common data law와 prior measure가 필요하다. family별 서로 다른 normalized compressed likelihood를 그냥 비교하지 않는다. nonnested/singular family의 likelihood-ratio distribution은 mocks 또는 명시한 이론으로 보정한다.

완료 기준은 적어도 한 제한된 family pair의 실제 response 식별성 및 injection recovery다. 일반적인 강한 anisotropy와 arbitrary tilted Bianchi 전체를 모두 배제하는 결론은 별도의 미해결 목표로 남긴다.

## 4. 증거 재사용과 중단 조건

R58 source hashes·fixed-GLS tests·R60 exact normalization/convex witnesses·닫힌 reviewer findings는 입력/전제가 바뀌지 않는 한 재사용한다. 전제 변경이 없는 독립 감사를 반복하지 않는다.

작업은 scientific input이 없거나 결과가 정의된 physical model 밖으로 나갈 때 해당 claim을 멈추고, 계산된 관측량과 실패 기작을 보존한다. actual-data path가 닫히지 않았는데 문헌 목록이나 DAG 크기만 늘려 완료로 표시하지 않는다.

연구계획의 다음 선택은 NEXT-01/NEXT-02를 primary로 고정한 상태다. NEXT-04–NEXT-06은 현재 데이터를 통해 어느 추가 물리량을 얻을지 명시한 경우에만 primary에 합류한다. 모든 새 결과는 하나의 likelihood/identified set과 x,Q,Pi,F_support,G_F의 관계를 유지한다.
