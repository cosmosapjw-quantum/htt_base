# HTT 모의심사 기반 후속 연구 — 확정 계획과 이론 우선 DAG

작성일: 2026-09-07
상태: PLANNING_COMPLETE / SELECTED_THEORY_NOT_YET_FULLY_CLOSED / PRODUCTION_HANDOFF_NOT_RELEASED
대상: cosmosapjw-quantum/htt_base. 운영: MAIN에서 이론·통계·설계 확정 → Local Codex가 구현·검증·자료분석 → MAIN 결과 해석.

## 0. 이번 문서의 결론

중단됐던 계획 작업을 이 문서와 세 동반 파일로 마무리한다. 55쪽 해설판을 끝없이 다시 감사하는 대신, 그 수학을 실제 관측의 불확실성과 물리적 식별 문제에 연결하는 유한한 연구 프로그램을 선택했다. 중심은 새 scalar anomaly 하나를 만드는 것이 아니라, **관측 morphology와 물리적 상태를 분리한 채, 같은 sky·mask·noise·redshift 자료가 어떤 응답 성분을 실제로 구별하는지 정량화하는 것**이다.

계획은 완성됐지만 모든 후속 이론이 완성된 것은 아니다. 아래 세 MAIN 연구 묶음에서 forward model, covariance, null, redshift/selection, numerical acceptance와 source 조합을 닫은 뒤에만 하나의 구현·분석 명세를 Codex에 넘긴다. 현재 문서를 실행용 production handoff라고 오해해서는 안 된다. Codex가 과학적 모형이나 가설을 임의로 선택하게 하는 빈칸을 남기지 않기 위한 구분이다.

읽을 파일:

- [수학·물리 유도와 심사 수치의 교정](THEORY_RESULTS_AND_CORRECTIONS.md)
- [현재 코드·데이터 재사용 지도](REUSE_AND_DATA_MAP.md)
- [기계 판독 DAG](RESEARCH_DAG.json)

원 심사 두 편, 후속 제안 두 편과 2026-09-07 자료 목록은 사용자가 제공한 검토 입력이다. 심사문에 적힌 독립 Monte Carlo·CAS 재검산 주장 자체를 실제 실행 receipt로 승격하지 않는다. 본 계획에서 직접 유도한 것, 원 source에서 확인한 것, 계산기로 산술 대조한 것과 아직 실행되지 않은 것을 분리했다. private 심사·corpus·style 원본을 공개 자료로 복사하지 않는다.

## 1. 유지할 연구 질문과 산출물

장기간의 다섯 축은 모두 남긴다.

1. Low-ell morphology: 전체 Q/O 및 저다중극 상태의 진폭·형상·상대 방향·handedness를 보존하고, 불확실성과 chart failure를 포함해 어떤 비교가 가능한지 계산한다.
2. Local boost versus global tilt: observer response와 matter/source-side coherent motion, intrinsic dipole 및 survey systematics를 실제 서로 다른 응답으로 비교한다. 스키마 이름만 다른 template는 구분 근거가 아니다.
3. Kinematical bounds: 물리적 shear/vorticity/acceleration/frame velocity를 관측 temperature tensor와 구별하면서, 명시적 derivative·observer·scale 가정의 강도에 따른 조건부 상한을 계산한다.
4. Dipole 및 다른 low-ell anomalies: 방향·진폭·상대 정렬·parity에 대한 구체적인 귀무/대립 문제를 정의한다. 모든 이상성을 검출하는 보편적 단일 통계량은 주장하지 않는다.
5. Redshift dependence: 원래 거리변수와 galaxy count selection을 통해 observer·local structure·calibration·coherent component의 redshift 응답을 구분한다. Radial data가 보지 못하는 vorticity와 light-cone 한계도 결과에 포함한다.

현재 55쪽 원고는 입문형 동반 문서로 보존한다. 후속 결과는 두 연결된 연구 산출물로 수렴시킨다.

**Paper I: CMB morphology의 회복가능성과 nuisance-conditioned information.** 완전한 관측 표현, 마스크·고다중극 nuisance의 네 처리 방식, exact/local boost와 monopole의 일관된 차수, matched null 및 구체적인 morphology 비교를 다룬다. 새로움은 표현의 최초 발견이 아니라, 실제 처리·불확실성·보조 관측을 포함한 비교가능성에 있어야 한다.

**Paper II: 조건부 운동학 상한과 redshift-dependent frame consistency.** MES의 가정 의존성, raw-distance와 count likelihood, observer와 matter-frame의 구분, 식별되는 성분과 null direction을 다룬다. Global tilt는 유지할 물리적 가설이지만, 대응 동역학/transfer가 없는 상태에서 임의의 redshift dipole을 그 증거로 이름 붙이지 않는다.

편광·remote dipole/kSZ·추가 lensing·외부 native Bianchi atlas는 후속 확장으로 기록한다. 현재 선택한 관측·통계 프로그램의 종료조건을 무한히 확장하는 선행과제로 두지 않는다. Native solver가 필요한 family identification은 그 외부 응답이 준비되기 전까지 현재 논문의 claim이 아니다.

## 2. 두 심사와 업그레이드 제안의 비판적 판정

| 지적 또는 제안 | 판정 | 이번 계획에 반영한 조치 |
|---|---|---|
| 55쪽 pedagogical exposition과 original research article의 목적이 섞임 | 채택 | 해설판 보존, 연구 논문은 위 두 질문과 결과 중심으로 압축. 데이터가 없는 모든 방법론 논문이 무가치하다는 일반화는 채택하지 않음. |
| Multipole-vector 선행연구와의 비교 부족 | 채택·인용 교정 | Land–Magueijo의 astro-ph/0502574와 Katz–Weeks의 astro-ph/0405631를 분리. 보존 정보·singular stratum·계산 안정성·covariance 전달을 비교; STF가 원자료보다 정보를 늘린다는 주장 금지. |
| Axial continuum L=12보다 L=10에서 이미 full row rank | 채택·직접 증명 | 기존 비영 minor의 실제 열과 m-block 상한으로 정확한 최소 L=10 유도. 열 개수만으로 하한을 증명했다고 쓰지 않음. |
| 부스트 좌표의 큰 intrinsic-octupole 오차 | 조건부 채택·수치 교정 | fixed-Q spherical model의 covariance와 trace bound를 유도. 예시 rms는 약 0.882–0.888. '모든 추정자에 무관한 저각 무정보' 주장은 기각. |
| 평균 boost-subspace fraction 3/7 및 큰 projection의 흔함 | 조건부 채택 | Gaussian/spherical 방향 모형에서 Beta(3/2,2), tail 0.3813 및 0.06980 확인. 두 근삿값은 맞으며, SO(3) isotropy만으로 Beta 법칙을 일반화하지 않음. |
| 결정론적 rank-zero quotient를 실제 통계 정보손실로 간주 | 수정 필요 | 무제한·타원체 bounded·Gaussian·같은 sky의 auxiliary-conditioned 모형을 같은 관측에서 비교. trace 오염비 0.99를 보편적 정보손실률로 쓰지 않음. |
| 전천에 가까워질수록 leakage를 조사 | 채택·유도 확장 | 정해진 mask 경로에서 K=O(epsilon), Gaussian 오염 O(epsilon^2), 상쇄 cost O(epsilon^-2). f_sky 하나로 mask를 동치화하지 않음. |
| MES의 실제 규모·epsilon1 및 미분 가정 민감도 부족 | 채택 | local amplitude를 all-observer/derivative bound로 바꾸는 전제를 명시. 모형 내 cancellation-first shear와 전통적 느슨한 ceiling을 분리. Bayesian Bianchi posterior 숫자와 무조건 순위 비교하지 않음. |
| Appendix E의 ASCII 표기·strict/weak 부등식·표준결과 귀속 | 채택 | 새 이론 문서에서 수식화·weak bound 기본·strict slack 명시·표준 선형대수 귀속. 기존 PDF를 몰래 변경하지 않음. |
| 수치 rank margin delta는 반드시 결과 보기 전에 고정 | 교정 | 실제 deterministic containment와 rigorous lower bound가 있으면 사후 margin 보고는 타당. 확률적 coverage/selection calibration과 별개. |
| 광범위한 '완전 이상성 스캔'과 chi parity test | 재설계 | 정해진 유한 가설군, tail과 nuisance fit을 동결하고 전체 선택 절차를 null에 포함. 동시 SO(3) 회전으로 회전불변량의 분포를 만들지 않음. abs(chi)는 parity-even이며 한 sky의 chi 부호만으로 검출 주장하지 않음. |
| 임의의 tolerance, 파이프라인 결과 1 sigma 일치, 고정 KS-uniformity를 PASS 조건으로 사용 | 그대로 채택하지 않음 | 수치오차는 선언된 metric·신호 불확실성에 맞춤. 실제 데이터의 1 sigma 일치는 관측 결과이지 프로그램 correctness test가 아님. tie가 있는 보수적 p값은 uniform이 아니라 super-uniform일 수 있음. |
| '몇 개월이면 게재승인' 일정과 독립 검산 assertion | 실행 근거로 미수용 | 실행시간·논문채택 확률을 추정 사실처럼 제시하지 않음. 기존 자료·코드와 실제 닫힌 이론 및 사용량으로 다음 단위를 판단. |

심사에서 맞는 지적을 인정하는 것과 심사의 모든 계산·해석을 승인하는 것은 다르다. 특히 과거 artifact 수용은 새로운 과학적 반론을 금지하는 면책이 아니다. 새로 확인한 delta 문구·cutoff·MES-model sharpening은 추후 명시적 수정본/정오표에 반영하되, 원 PDF와 원 receipt는 이력으로 보존한다.

## 3. 이번에 실제로 진행한 과학·코드 연구

동반 이론 문서에 다음을 직접 유도했다: 최소 axial cutoff, projection의 조건부 Beta 법칙, 정확한 trace-inverse bound와 conditional boost variance, cancellation-first shear estimate, nuisance의 최소 상쇄 cost와 correlated auxiliary의 Schur complement, small-mask scaling, monopole의 second-order quadrupole, radial affine velocity의 vorticity null, 그리고 DESI 마스크 moment의 실제 response.

특히 두 구현상 문제는 소스의 실제 연산으로부터 나왔다. DESI compact와 random vector는 RA/Dec로 생성되는데 비교 CMB 방향은 Galactic 좌표다. 또 alpha를 자료에서 추정한 후 3<delta n>을 쓰면 response는 일반적으로 I가 아니라 3 Cov_R(n)이다. 균일한 반구에서 axial response는 1/4다. 이는 구체적인 코드 연구 루프의 산출물이다: source 읽기 → 수학적 반례 → 교체할 joint design과 frame adapter 정의 → 합성 회귀 조건까지 작성했다. 런타임이 실패했으므로 patch 적용이나 native RED/GREEN은 주장하지 않는다.

성립하지 않는 주장으로 끝나는 연구도 유효한 종료다. 예컨대 raw radial velocity만으로 로컬 antisymmetric gradient를 식별하지 못한다는 판정은 모델을 억지로 적합시키라는 지시가 아니라 후속 likelihood의 정확한 null direction이다.

## 4. MAIN에서 먼저 닫을 세 연구 묶음

### T1 — CMB의 완전한 관측·response·null 모형

질문: 저각 morphology의 어느 성분이 mask/noise/foreground/observer motion 이후에도 어떤 오차와 귀무가설 아래 구별되는가?

산출할 최종 수학 명세:

- 물리적 온도 또는 해당 제품의 intensity-to-temperature convention, frame와 unit, monopole/dipole/kinematic-quadrupole 처리부터 map → harmonic/tensor까지의 실제 forward operation. 순수 monopole은 exact transformation을 사용하고, anisotropy truncation은 절대 오차 차수까지 정당화한다.
- 전체 Q/O를 기본 잠재 관측상태로 두고 cyclic packet은 파생 좌표로만 사용한다. chart unavailable 사례를 observation/null 모두 보존하는 통계량 또는 풀 전체 abstention 규칙을 고정한다.
- 고다중극의 무제한·bounded·Gaussian·같은 sky auxiliary-conditioned 네 모형의 mean, covariance, nuisance elimination 및 parameter derivative를 완성한다. 같은 sky에서 추출한 저각/고각/성분맵의 교차공분산을 포함한다.
- observer velocity beta의 mean Jacobian과 covariance derivative를 명시한다. 기존 source-column Jacobian에 beta parameter 의미를 붙이지 않는다. intrinsic dipole, potential contribution, component separation/unit-conversion degeneracy와 Chluba–Ravenni·Roldan·Ferreira–Quartin의 실제 구별 조건을 비교한다.
- 유한한 confirmatory morphology 목표와 null/alternative를 선택한다. 파워만 조건화한 shape null, 상대회전 null, Gaussian full-sky null, end-to-end matched null은 다른 실험이다. primary statistic, tails, 고정 외부축, nuisance fitting, 다중선택 처리와 신뢰진술을 한 함수로 정의한다.
- 가우시안 joint model의 covariance operator, covariance-estimation uncertainty와 기존 reference 수의 해상도를 반영한다. Monte Carlo 최소 p와 binomial uncertainty를 기록하고, 회전 불변량의 동시 회전으로 유효 reference 수를 늘리지 않는다.

종료조건: 선택한 주 모형의 likelihood 또는 compatibility/rank procedure와 모든 가정·units·domains·limits가 문서 및 수식으로 확정돼 있으며, norm/rotation/zero/known-template/conditional-Gaussian limit에 대한 예상 결과가 주어진다. 이 묶음이 끝났다는 것은 새 관측 결과가 나왔다는 뜻이 아니다.

### T2 — Redshift 및 physical kinematics의 forward model

질문: 같은 observer와 서로 다른 깊이의 tracer가 보여 주는 방향/진폭 변화 중 observer motion, local structure, selection/calibration과 물리적 coherent component를 어떻게 구분하는가?

산출할 최종 명세:

- CF4 등에서 원래 distance modulus 또는 log-distance ratio를 출발점으로 observed redshift와 연결하는 적분/잠재거리 likelihood. 그룹, calibrator/method offsets, distance errors, redshift frame, selection과 shared-LSS covariance를 포함한다. 변환된 peculiar velocity에 Gaussian을 자동 가정하지 않는다.
- DESI 원 catalogue/random 정의에 맞춘 joint angular design: per-cap mean, dipole과 정해진 higher multipoles, exact release weight와 redshift selection. number-count kinematic coefficient는 magnitude/flux/redshift selection에서 유도하며 hard-coded 7e-3를 쓰지 않는다.
- local first-order diagnostic와 더 일반적인 light-cone response의 적용범위를 분리한다. redshift bin/basis, distance mapping, observer/source terms 및 nuisance rank를 확정한다. 데이터 곡선을 먼저 본 뒤 bins를 선택하지 않는다.
- beta_RO, beta_RM, beta_MO와 intrinsic CMB dipole을 구별한다. global-tilt 가설의 물리적 파라미터와 응답이 실제로 없으면 NO_PHYSICAL_RESPONSE라는 이론 판정을 남기고, phenomenological coherent velocity와 같은 것으로 처리하지 않는다.
- MES의 전통적 조건부 branch와 explicit Appendix-E branch를 각각 수식화한다. derivative-envelope 계수와 intrinsic-dipole scenario를 가정축으로 두고 데이터 오차와 가정 민감도를 분리한다. galaxy redshift 또는 ISW 관측을 local radiation derivative와 동일시하지 않는다.
- 단일시점 radial n^T Omega n=0 null을 보존한다. projected weak-lensing shear, reconstructed velocity-gradient shear와 congruence shear 사이에는 별도 response/averaging 관계가 필요하다.

종료조건: 각 측정량의 확률변수·model role·frame·calibration·selection·공분산과 각 physical parameter의 식별가능/null 방향이 고정된다. Global tilt가 구별되지 않는 branch는 그 명시적 비식별 결과로 닫을 수 있으나, 장기 연구 질문에서 삭제하지 않는다. 외부 native transfer 없이는 Bianchi family likelihood를 배포하지 않는다.

### T3 — 수치·자료 product·source integration 및 실행 명세 동결

질문: T1/T2의 수학을 어떤 고정 코드·제품·오차기준으로 계산하면 되는가?

산출물은 하나의 SCIENCE_SPEC, 하나의 실행 configuration 및 검증 fixture 묶음이다. 새로운 범용 하네스가 아니다.

- finite harmonic/finite pixel operator를 분리하고 mask harmonic support, normal conditioning, source tail와 quadrature/transform/fit/roundoff 오차를 예산화한다. rigorous enclosure가 없는 결과는 convergence-supported estimate로 보고하는 경로를 명시한다.
- parameter-sensitive conclusion에 필요한 singular-value 또는 covariance error tolerance를 도출한다. epsilon_floor 같은 수치 guard와 physical/inferential error budget을 구분한다. 임의의 1e-8을 모든 observable에 적용하지 않는다.
- 기존 inventory에서 필요한 release/schema/header 정보만 고정하고 product eligibility를 결정한다. 목표 통계량을 계산하는 unblinding은 이 단계에서 하지 않는다. MAIN에서 파일 header를 읽을 수 없는 경우에만 작은 read-only metadata job을 local에 허용하며, 이는 과학적 선택권이나 자료분석 위임이 아니다.
- PR3 SMICA+matched FFP10를 우선순위로, PR4·다른맵은 predeclared eligibility에 따라 채택/비활성한다. CF4 원거리/group와 DESI object/random/mock의 변수/선택을 확정한다. 원래 파일 수와 독립 mock 수를 구분한다.
- 여러 branch의 actual import/dependency closure를 구성한다. default branch와 최신 검증 branch를 묻지마 merge하지 않는다. reused exact source와 새 adapter/test 파일 목록을 확정한다. 각 함수의 signature, shape, units, exceptions, consumer와 command를 기록한다.
- null generation/fitting/selection, optimisation 또는 sampling algorithm, covariance solve, convergence, Monte Carlo precision 및 numerical acceptance를 고정한다. 결과가 유의하지 않다는 이유로 tolerance·prior·표본을 변경하는 경로는 없다.

종료조건: Codex에 넘어갈 실행 명세에 과학적 placeholder가 없고, 남은 선택이 프로그램의 구현 세부에 한정된다. 정의·법칙·parameter domain·prior·null·test direction·survey cuts·오차기준·예상 synthetic controls 중 하나라도 미정이면 release하지 않는다. 데이터 자체의 실패나 counterexample이 발견될 때의 분기 역시 명시한다.

세 묶음은 다음 순서로 처리한다: T1 → T2 → T3. 이는 사용자에게 매번 승인만 요청하는 세 gate가 아니라 실제 수학/통계 산출물 세 개다. 현재 요청의 연구 범위 안에서는 연속 수행한다. 장기 optional work를 이유로 선택한 programme을 무기한 봉인하지 않는다.

## 5. Theory freeze 뒤의 Codex 전체 위임

동결 후에는 하나의 논리적 실행 프로그램으로 다음을 위임한다. 물리적 의미를 바꾸는 단계만 MAIN으로 반환하고, 일반적인 구현/fixture/runtime/packaging 결함은 동일 writer가 원 실패를 보존하며 수정한다.

| 실행 단위 | 소비 입력 | 실제 산출물 / 검증 |
|---|---|---|
| C0 소스·입력 결속 | 동결 spec, 선택한 commit/file closure와 product 목록 | isolated checkout, 실제 import path, 선택 입력 header/ID, 기존 결과 재사용. 전체 1.5TB inventory/hash 반복 금지. |
| C1 geometry·observer core | T1 수식, 기존 Q/O kernel | full-tensor/packet, exact monopole 및 일관된 boost 처리, projection/covariance. scale·rotation·reflection·zero·kinematic quadrupole controls. |
| C2 finite operator·nuisance | T1/T3 | weighted fit, K, bounded cost, Gaussian/aux-conditioned covariance, derivatives와 physical Jacobian. full-sky/small-mask/known linear controls. |
| C3 catalogue·selection | T2/T3 | CF4 original-distance/group adapters와 DESI frame-correct joint design. hemisphere response, per-cap means, zero direction, exact release weights controls. |
| C4 joint inference | C1–C3 및 동결 prior/null | 실제 likelihood/feasible-set code, Schur complement와 parameter-dependent covariance, light-cone kernels. 스키마 support score를 posterior로 쓰지 않음. |
| V0 end-to-end synthetic 검증 | C4 | 알려진 입력 회복, bias/coverage/FPR/power/abstention 및 nuisance-confusion. correctness와 유의미한 발견 여부를 분리. |
| V1 matched-null calibration | V0, 승인 reference pool | complete-map 재적합·selection을 포함한 null, actual independent N와 tail resolution. 선택된 threshold에 대한 검증. |
| D1 CMB 관측 실행 | V1 | primary+predeclared controls, amplitude/shape/direction uncertainty, 네 nuisance model 비교. 불리한 map 결과도 보존. |
| D2 redshift 관측 실행 | V1 | raw catalogue likelihood와 selection-corrected count, redshift coherence·계수·null directions. 재구성 prior와 shared calibration 기재. |
| J0 결합 해석·산출 | D1,D2 | 실제 joint result 또는 식별불가/입력부족 결과, 결과표·그림·두 논문 입력. conditional independence를 가정 없이 곱하지 않음. |

C2와 C3, D1과 D2는 수학적 의존성이 없는 부분에서 병렬 가능하다. 그러나 같은 파일/ref에는 단일 writer를 유지하고, 메모리·I/O 사용을 실제로 보고 조절한다. 작업단위를 나눠 누적 budget을 초기화하지 않는다.

Primary와 optional comparison의 실패를 구분한다. 선택한 primary product의 유효성이 실패하면 그 과학적 실행을 중단한다. 사전 지정한 optional WMAP/PR4 comparison의 파일 부족은 해당 branch만 NOT_RUN으로 남기고, 그 자료가 필요하지 않은 완료 결과를 무효화하지 않는다. 결과가 비유의하거나 모수가 nonidentified인 것은 성공적인 연구 결과일 수 있다.

## 6. Codex에 남기지 않을 과학적 선택

동결 명세에는 반드시 다음이 실제 값·수식·알고리즘으로 들어간다: 관측 unit/frame/basis와 active/passive rotation; map conversion 및 kinquad 처리; 관심 parameter와 nuisance의 물리적 의미; joint mean/covariance와 모든 cross block; prior 또는 deterministic bound; redshift/flux/cap cuts와 그룹 처리; finite set의 통계량·tail·외부축·selection correction; simulation 생성/재적합 절차; 오류전파와 Monte Carlo stopping; 실제 코드 경로·API·tests·expected edge outcomes.

현재 파일은 이 항목들을 닫는 연구 계획이지, 미정 값을 Codex가 알아서 선택하라는 실행 요청이 아니다. '추가 사고 없이'의 실질적 의미는 과학적 모형 선택이 없어야 한다는 것이며, 프로그램 디버깅이나 입력오류 진단까지 없앨 수 있다는 뜻은 아니다.

## 7. 검증의 예상 결과와 중단 조건

회귀는 문제별 의미를 갖는다. Gaussian-normalised STF3 projection에는 유도된 Beta CDF를 사용하되 SO(3) 회전만으로 구성한 non-Gaussian shape ensemble에 같은 CDF를 강요하지 않는다. 잘못된 회전/frame, hemisphere estimator, 불완전 covariance, double kinquad subtraction, normalization 후 숨긴 invalid tensor 등에는 명확한 negative controls를 둔다. 무제한 nuisance, finite bounded nuisance와 Gaussian prior의 답이 다른 것은 bug가 아니라 모형 차이다.

실제 end-to-end FPR/coverage는 Monte Carlo uncertainty와 함께 평가한다. Conservative tied ranks에 KS uniformity를 강요하지 않는다. 데이터 pipeline 둘의 결과가 1 sigma 이상 다르면 조사할 실제 관측 차이지, 유리한 pipeline을 골라 PASS로 만드는 이유가 아니다. 참 신호 주입 없이 '복원코드가 돌아간다'를 power로 보고하지 않는다.

진행 중 새 물리적 counterexample이나 데이터 product definition의 모순이 나오면 그 지점의 source, 입력과 결과를 보존해 MAIN으로 반환한다. 알려진 범위 안의 coding defect는 수정하고, 같은 실패를 원인 변화 없이 반복하는 retry는 제한한다. 원 데이터·quarantine·기존 실험기록·canonical claim·protected physics를 몰래 바꾸지 않는다.

## 8. 운영·산출물·완성도

계획 문서 네 개가 완성되면 planning task는 종료한다. 이론 실행의 다음 산출물은 T1, 이어 T2, T3이며, 그후 Codex에게 전체 구현/분석을 넘긴다. 현재 `production_handoff_ready=false`는 미완의 계획이 아니라, 계획과 이론 완결을 혼동하지 않기 위한 실제 상태다.

이번에는 native code/data run이 없고, 직접 유도·웹 계산기 산술·Git source 읽기와 계획 게시를 수행했다. repo-wide discovery와 selected-file review를 모든 branch 전수 실행으로 표현하지 않는다. 55쪽 문서의 artifact 수용, 기존 R2/authority/decoder/source-replay PASS는 각자의 범위로 보존한다. 새 연구 주장에 과거 PASS를 붙이지 않는다.

계획 budget은 실제 진전과 사용량을 보고 조정한다. 초기 시간 예측이나 과거 workflow timeout은 모든 연구의 절대 상한이 아니다. 바꿀 때 이유·이전/변경 allowance·누적 사용량을 남긴다. 사용자 명시 hard cap, tool limit, 새로운 외부 비용/권한과 preregistered experiment budget은 별개다. 현재 입력만으로 개월 단위 ETA나 퍼센트 완료율을 꾸미지 않는다.

Handoff와 결과는 가능한 한 격리 branch에 non-force 게시하고, 실제 source/config/result/원 로그를 읽을 수 있는 Git 파일과 RETURN_TO_MAIN 고정 링크로 교환한다. 수동 ZIP relay와 WORK_THREAD를 기본 단계로 만들지 않는다. private repository 공개전환, 외부 수신자 배포, merge·ready·canonical/과학적 승격은 이번 계획에 포함되지 않는다.

마지막으로 장기 목표의 성취와 이번 단위의 종료를 분리한다. 본 계획은 다섯 연구축을 유지한 유한한 경로를 선택했다. 실제 이론과 관측 결과가 그 경로에서 불가능성을 보여 주면, 불가능한 parameter를 제거·표기한 명세로 종료한다. 원하는 cosmological interpretation이 나올 때까지 모형을 바꾸는 탐색 루프를 production 코드에 넣지 않는다.