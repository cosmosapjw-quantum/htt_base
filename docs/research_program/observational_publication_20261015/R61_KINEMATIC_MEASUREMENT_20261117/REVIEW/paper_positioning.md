# R61 논문화 포지셔닝 초안 — 저자지원

기준: `fb6ae9f21585e194ef29dabc91d79a529e0ac57e` 및 현재 scratch `R61_THEORY.md`. 이 문서는 R2/C2에서 확인한 원전과 현재 이론 정식화를 이용한 논문 구조·주장 범위 제안이다. 새로운 문헌 전면조사, 원격 변경, 수치 실행 또는 독립 C9 심사를 수행하지 않았다. 아직 R61 실제 수치결과가 없으므로 아래의 측정 산출물과 검증 항목은 **목표 또는 claim gate**이며 성취를 뜻하지 않는다.

## 1. 중심 질문과 잠정 제목

논문의 중심 질문은 “현재 CF4 거리–적색편이 실험이 beyond-FLRW 운동학에 관해 어떤 공동 제약을 실제로 주며, 어떤 유한 깊이 변화가 공통 각방향 거리보정에 영향을 받지 않는가?”로 잡는 것이 적절하다. 그 답은 새로운 보편적 비등방 지표를 선언하는 대신, 보존된 관측 likelihood에서 직접 계산한 물리 함수의 confidence image와 명시한 깊이 응답의 contrast로 제시한다.

잠정 제목은 **“Joint kinematic constraints and depth contrasts from a finite-depth distance–redshift experiment”**로 둘 수 있다. 현재 계약대로라면 “local shear measurement”, “cosmic vorticity measurement”, “model-independent expansion tensor reconstruction”을 제목의 확정 주장으로 쓰기 어렵다. 실제 결과가 나온 뒤 제목에 CF4 또는 calibration-limited 같은 구체적 한정을 반영한다.

핵심은 두 산출물을 하나의 관측 법칙 아래 조직하는 데 있다. 첫째는 normalized angular coefficients와 상대속도의 공동 집합에서 얻는 nonlinear kinematic functionals다. 둘째는 같은 source operator에 유한 적색편이 응답을 추가했을 때 나타나는, **깊이에 무관한 공통 additive angular calibration을 정확히 소거하는 STF contrast**다. 둘 다 무엇을 측정하는지와 무엇이 calibration·response 가정에 달리는지를 수치적으로 구분해야 한다.

## 2. 가장 가까운 선행방법과 현재 기여의 관계

| 선행방법·원전 | 이미 성립하는 내용 | R61에서 남는 구체적 측정 대상 | 지금 주장할 수 없는 새로움 |
|---|---|---|---|
| [Heinesen 2021, arXiv:2010.06534v2](https://arxiv.org/html/2010.06534v2) | 일반 congruence의 leading directional Hubble rate, expansion/acceleration/shear multipole, higher-order distance cosmography | 고정된 CF4 operator의 apparent coefficients를 보정조건 아래 normalized physical images로 옮기는 실제 계산 | H_dir 공식, tensor/multipole 표현, 선도차수에서 omega가 사라진다는 사실의 최초 도입 |
| [Maartens et al., arXiv:2312.09875v3](https://arxiv.org/html/2312.09875v3) | matter congruence와 moving observer의 구별, Doppler·aberration, 거리와 적색편이를 일관되게 변환할 필요, finite-distance contamination | 현재 CF4의 frame conventions와 response bridge를 고정하고 그 한계를 결과에 부착 | dipole을 상대운동·기하학과 구분하는 발상의 최초 제안, redshift 재라벨링만으로 완성한 covariant reconstruction |
| [Stiskalek, Desmond & Lavaux, arXiv:2509.14997v2](https://arxiv.org/html/2509.14997v2) | calibration·latent distance·peculiar velocity 공동 forward model, zero-point dipole과 radial flow 구별, radially varying external velocity | grouped carrier에서 STF의 유한 깊이 응답과 공통 angular-calibration cancellation을 정량화하고 velocity-slope contamination을 별도 보존 | flow/calibration 분리의 최초 도입, 서로 다른 sample·likelihood 간 유의도 수치만으로 우열 판정 |
| [Heinesen & Korzyński 2024, arXiv:2406.06167v1](https://arxiv.org/html/2406.06167v1) | geodesic congruence의 leading proper-motion shear/rotation, redshift-drift cosmography, reference-frame 및 coarse-graining 주의 | CF4가 측정하지 못하는 omega·absolute H를 분명히 하고 향후 astrometric joint measurement의 입력조건 지정 | leading proper-motion 식, E2/B1과 shear/vorticity의 이론적 연결 자체, 고적색편이 quasar 계수의 무조건적 local 해석 |
| Gaussian linear model·GLS 및 confidence-set projection | fixed C의 joint ellipsoid, 선형 projection과 Schur complement, 하나의 confidence event를 함수의 image로 전달하는 원리 | 기존 retained32D CF4 실험에서 실제 simultaneous nonlinear ranges, covariance 상관을 제거했을 때의 정량 손실 | Gaussian GLS, confidence image, tensorization 자체가 새로운 일반 통계이론 또는 추가 Fisher information이라는 주장 |
| Partial identification 문헌: [Chernozhukov, Hong & Tamer 2007](https://www.econometricsociety.org/publications/econometrica/2007/09/01/estimation-and-confidence-regions-parameter-sets-econometric) | 점 식별 실패와 identified set의 confidence inference를 분리하는 기존 틀 | bounded deterministic calibration body가 만드는 조건부 물리 집합과 함수 범위 | 해당 논문의 일반 asymptotic theory를 R61의 유한 Gaussian 모형에 새 정리처럼 재포장 |
| 이 프로젝트 R58/R60 | retained carrier, full covariance, calibration support, covariance sensitivity, radial-velocity 대안, 기존 calibration threshold | 상관을 보존한 비선형 image와 새 STF depth response의 실제 결과 | R60 norm-zero threshold를 다른 좌표로 다시 표현한 것을 독립 검출 또는 새 과학결과로 계수 |

이 비교만으로 novelty가 확정되지는 않는다. 현재의 구체적 후보 기여는 **특정 실제 실험에서 이전에 산출하지 않은 함수 범위와 depth contrast를 완성하는 것**이다. 어떤 범위가 기존 scalar/multipole 분석에서 얻기 어려운 해석을 제공하는지, matched sample과 response에서 무엇이 달라지는지를 결과로 입증해야 한다. 새 변수를 정의했다는 사실이나 문헌에서 같은 이름을 찾지 못했다는 사실은 novelty 증거가 아니다.

## 3. 제안하는 8항목 논문 구성

1. **관측 질문과 실험의 단위.** CF4 retained32D observation, selected groups, 일곱 operator가 같은 source를 변환한다는 사실을 먼저 제시한다. 핵심 목표는 joint kinematic images와 지정한 depth contrast다. 여러 operator의 likelihood를 독립 표본처럼 곱하지 않는다.
2. **Local kinematics와 관측 response 사이의 연결.** signature, proper time, sourceward n, congruence와 observer frame을 고정한다. H_dir와 D_L의 local expansion을 선행식으로 제시한 뒤, 현재 finite-depth log-distance response와의 first-order bridge를 별도 가정으로 둔다. monopole 제거로 absolute H/Theta가 측정되지 않는다는 점을 이 절에서 확정한다.
3. **하나의 joint confidence domain과 calibration family.** fixed-C Gaussian law, 11D와 16D의 용도, calibration Gram과 magnitude RMS 변환, operator union을 정의한다. stochastic covariance uncertainty와 deterministic calibration allowance를 서로 다른 모수로 취급한다. 동시 coverage가 어떤 조건에 기대는지 명시한다.
4. **Nonlinear kinematic images와 covariance geometry.** |beta|, |a|, shear norm, angular RMS, beta.a, beta^T s beta를 같은 집합에서 산출한다. quadratic trust-region 및 conditional Schur reduction은 필요한 계산법으로 설명한다. exact/sharp endpoint, floating numerical enclosure, conservative outer bound를 항목별로 구분한다. component-box 결과는 같은 joint cutoff의 enclosing box와 비교한다.
5. **Finite-depth STF response와 calibration-free contrast.** K(z)=K_p+((z-z_p)/z_*)K_1을 실제 source operator로 구성한다. 공통 additive angular calibration의 cancellation을 affine-equivariance로 증명하고 DeltaK 및 방향별 G를 측정대상으로 제시한다. contrast는 observed-redshift slope이지 local shear의 proper-time derivative가 아니다.
6. **응답 타당성과 contaminant sensitivity.** pivot와 z=0 extrapolation 비용, omitted finite velocity slope, depth-dependent calibration, log closure의 선형화 오차를 제시한다. 같은 fixed-C data law 안의 response comparison과 full nonlinear GR reconstruction을 구별한다.
7. **실제 결과와 선행분석 대비.** 실제 수치 산출 후 joint intervals, feasible witnesses/optimality gaps, box loss, STF depth contrast 및 slope-zero test를 배치한다. 결과가 영점을 포함하거나 calibration allowance에 민감해도 그 범위와 원인을 측정 결과로 제시한다. Stiskalek 분석 등과는 source/sample/model 차이를 맞춘 범위에서만 비교한다.
8. **물리 해석과 다음 관측.** conditional finite-depth normalized kinematics의 의미를 정리한다. Gaia·redshift drift·absolute distance calibration이 각각 어떤 kernel을 줄일 수 있는지와 필요한 transfer를 제시한다. Bianchi class/global tilt 식별이나 모든 beyond-FLRW 운동학의 배제는 현재 논문의 결론으로 두지 않는다.

## 4. Claim gates

| 주장 후보 | 성립에 필요한 gate | 현재 원고에서 허용할 상태 |
|---|---|---|
| “현재 실험의 joint nonlinear interval을 계산했다” | 실제 carrier 입력, joint covariance, cutoff 차원, finite union 규칙을 고정하고 실행 receipt·endpoint/witness를 확인 | 수치결과 대기. 식과 알고리즘 계약만 존재 |
| “이 interval은 sharp하다” | 해당 공통 집합에 대한 global upper/lower enclosure와 feasible witness가 허용 오차 안에서 닫혀야 함 | norm/구조적 reduction과 실제 최적화 완료를 구분. capped 결과는 capped로 보존 |
| “simultaneous95%다” | 고정된 Gaussian law에서 true apparent parameter가 joint ellipsoid에 포함되는 event 및 true calibration이 body에 있다는 조건 | conditional statement만 허용. 함수마다 chi-square1로 cutoff를 바꾸지 않음 |
| “survey-realistic95%다” | 실제 selection, indicator errors, grouping, velocity/covariance law를 포함한 source-matched calibration 또는 독립적으로 정당화한 coverage 근거 | 현재 미확보. 기존 Gaussian injection만으로 승격 불가 |
| “physical shear constraint다” | finite-depth-to-local bridge, normalization H, congruence/frame, calibration body의 물리적 근거를 명시 | 기본적으로 normalized finite-depth response의 조건부 image. local sigma 검출로 승격하지 않음 |
| “angular calibration을 제거했다” | calibration이 실제로 X16의 공통 constant angular columns를 따라 이동함을 확인하고 affine-equivariance 및 수치 invariance test 통과 | 그 nuisance subspace에 한정한 exact cancellation. depth-dependent calibration에는 적용하지 않음 |
| “depth evolution을 측정했다” | full-rank depth response, cross-depth covariance, source depth leverage, omitted-V1와 response sensitivity 확인 | observed-redshift STF contrast의 측정. proper-time derivative 또는 homogeneous shear history로 부르지 않음 |
| “비선형 distance response에서도 결론이 유지된다” | 선언한 exact-log closure의 positivity, fit와 Jacobian 검증, remainder가 실제 추론 정밀도에 미치는 영향 확인 | 그 closure에 한정한 sensitivity. 전역 nonlinear confidence calibration은 별도 |
| “absolute expansion 또는 vorticity를 측정했다” | 새로운 monopole/absolute distance 정보 또는 astrometric response·reference-frame likelihood가 실제로 추가되어 관련 kernel을 줄임 | 현재 미지원. retained32D의 zero row/column을 측정값 0으로 쓰지 않음 |
| “출판 가능한 새 과학결과다” | 실제 비선형/contrast 산출물이 기존 결과의 좌표변환을 넘어 해석 가능한 정보를 주고, 가장 가까운 matched analysis와 차이를 입증 | 미확정. 본 초안은 과학적 포지셔닝이며 독립심사 판정이 아님 |

## 5. 반드시 유지할 네 가지 제한

**D_L와 log closure.** H_dir에 관한 local D_L=cz/H_dir+O(z²)는 이미 알려진 기하학적 expansion이다. 현재 D_L(z,n)=D_L,fid(z)/(1+h(n))로 두고 eta=log(1+h)를 사용하는 것은 별도의 finite-depth multiplicative angular closure다. h=d_H.n+K:nn를 그 선도 응답과 연결할 때 approximation order와 boost 처리까지 명시해야 한다. exact-log fit은 이 closure의 선형화 민감도를 검사하며, 일반 시공간의 Einstein–optics 해 또는 source-level latent-distance likelihood를 대신하지 않는다. velocity 부분도 현재 first-order Doppler kernel에 남는다면 전체 fit을 “fully nonlinear”이라고 부르면 안 된다.

**Finite depth에서 local 값으로의 이행.** K_p, K_1, K(0)는 현재 basis의 계수와 extrapolation이다. K(0)의 통계 오차를 잘 계산했다는 사실만으로 local sigma/H가 되지 않는다. higher-order distance terms, survey window와 smoothing, source congruence, observer frame, calibration 및 response remainder가 이행의 조건이다. trace-minimizing pivot는 covariance geometry의 결과이며, 관측 residual을 보고 최적 유의도를 찾는 적색편이 선택과 구분한다.

**Omega와 H.** retained32D는 monopole을 제거하고 vorticity response column을 갖지 않는다. 따라서 H와 Theta의 absolute 값, omega 또는 omega/H는 이 실험만으로 추정되지 않는다. A_H는 현재 normalized angular expansion의 RMS이며, 모든 FLRW 위반을 양의 정부호로 포착하는 총량이 아니다. A_H=0의 허용은 omega=0이나 FLRW geometry의 식별을 뜻하지 않는다.

**Calibration과 covariance.** rho는 full-sky angular calibration의 deterministic allowance이며 empirical posterior/measurement가 아니다. covariance amplitude 또는 fixed linear-LCDM C의 선택은 다른 stochastic-law 조건이다. rho와 lambda를 서로 대체하거나, 둘 중 하나를 변화시킨 안정성만으로 물리 식별과 survey coverage를 동시에 확보했다고 쓰지 않는다.

## 6. 추가 데이터의 최소 관측조건

현재 R61의 conditional CF4 함수와 공통-calibration-free contrast를 계산하는 데 새 관측은 필수는 아니다. 그러나 더 강한 물리 해석에는 목표별로 아래 조건이 필요하다. 각 조건은 유용한 입력이지, 단독으로 충분조건이라는 뜻은 아니다.

| 목표 | 최소로 추가·확보해야 할 관측 내용 | 반드시 함께 유지할 모델·통계 정보 |
|---|---|---|
| absolute H 및 Theta | 제거되지 않은 monopole 관측과 독립 absolute distance scale/zero point | 동일한 source selection, distance calibration과 velocity nuisance; angular-only carrier로 복원할 수 없음 |
| calibration-limited apparent tensor에서 physical s/a 분리 | 하늘 위치와 indicator/depth에 따른 distance-calibration modes를 실제로 제한하는 independent calibrator 또는 overlapping tracer observations | nuisance의 angular/depth response, cross-survey covariance, zero-point 연결. 임의 rho 선택을 관측으로 부르지 않음 |
| depth contrast를 실제 kinematic depth dependence로 해석 | 깊이별 calibration 차이와 지시자 구성 변화에 대한 bound 또는 계측, 충분한 source depth leverage | depth-dependent angular systematics와 omitted velocity mode의 cross-response; 같은 sky geometry를 무시한 독립-bin fit은 부족 |
| nearby proper-motion shear와 CF4의 joint consistency | 공통 또는 비교 가능한 smoothing scale의 nearby emitters에 대한 적색편이·거리·두 성분 proper motion | full astrometric covariance, sky mask, observer acceleration·frame-spin nuisance, controlled low-z remainder와 source congruence |
| 고적색편이 quasar E2/B1의 물리 해석 | source redshift distribution와 선정함수, reference-frame solution의 spin 제약·관련 계수 covariance | source-depth/history line-of-sight transfer 또는 명시한 geometry/history family. local leading 식을 source-independent gain으로 대체하지 않음 |
| cosmological vorticity 또는 omega/H | toroidal dipole를 실제로 구별하는 proper-motion data와 coarse-grained nonrotating frame의 독립 제약; omega/H에는 H도 필요 | catalog frame construction이 B1을 얼마나 고정·제거했는지, local rotations, mask mode coupling, full response rank. quasar-defined frame만으로 cosmological zero rotation을 보장하지 않음 |
| redshift drift를 통한 추가 기하학 정보 | 같은 source의 반복 분광과 시간기준·가속도/분광 drift calibration | matched depth/congruence, peculiar acceleration, drift transfer. 선도 drift에는 Ricci/Weyl 및 sigma/omega 항이 함께 들어가므로 독립 acceleration measurement로 단순 해석하지 않음 |

실제 source-level calibration/coverage가 확보되기 전에도 conditional experiment의 명확한 측정은 작성할 수 있다. 다만 그때의 논문은 “관측된 유한 깊이 응답이 허용하는 normalized kinematic functionals와 그 보정 의존성”을 결과로 삼아야 한다. 실제 결과가 기존 threshold의 재표현에 그치거나 contrast가 response/systematics에 의해 완전히 설명된다면, 이를 남은 새로움의 한계로 기록하고 출판 주장을 그에 맞춰 낮춘다.
