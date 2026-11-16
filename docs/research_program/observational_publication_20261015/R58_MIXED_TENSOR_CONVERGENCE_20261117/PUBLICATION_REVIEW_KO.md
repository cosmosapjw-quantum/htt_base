# R58 출판성 심사와 수렴 판정

기준: 2026-11-17. 저장소 baseline은 `77f61c17ba33ff28ff4f16a7d42621d8041e5ce4`다. 이번 판정은 기존 selected CF4 자료의 재분석 결과, 해당 코드의 독립 검토, R54의 방법론 평가 및 아래 원전 비교를 결합한다. 새 관측 자료를 받지 않았다.

**현재 결과는 좁은 방법론·관측 응용 논문의 후보가 되었다. 텐서 5변수 자체의 통계적 우월성이나 전역 비등방 우주론의 발견을 주장하는 논문은 아직 지지되지 않는다.** 이번에 확보한 구체적 결과는 기존 CF4 압축 관측량에서 polar–STF 교차 공분산이 상당하며, 이를 제거한 factorized 분석의 명목 95% 신뢰영역이 선언한 Gaussian 모형 아래 약 93.2–93.6%만 덮는다는 것이다. 동일 관측 실험의 직접 GLS와 R58 carrier는 일치한다. 따라서 추가 기여의 중심은 새로운 optimal estimator 발명이 아니라, 실제 보유 카탈로그의 보정 취약성과 혼합 신뢰영역을 정량화하는 데 있다.

## 확인된 결과와 정확한 의미

재분석은 35,970 selected groups에서 유도된 32개 관측 요약, 기존 일곱 nuisance 처방, 고정된 선형 \(\Lambda\)CDM cosmic covariance cache를 사용했다. 적합 대상은
\[
\vartheta=(V_x,V_y,V_z,dH_x,dH_y,dH_z,\kappa_0,\ldots,\kappa_4)
\]
의 11성분이다. \(V\)는 km/s 단위의 coherent velocity, \(dH\)와 \(\kappa\)는 apparent log-H dipole/STF 계수다. \(dH\)를 곧바로 four-acceleration으로, \(\kappa\)를 유일한 cosmological shear로 해석하지 않는다.

| 검증 대상 | 실제 결과 | 근거 상태와 범위 |
|---|---:|---|
| 32-row joint response | 일곱 모델 모두 rank 11 | numerically checked; 선언된 수치 rank와 고정 response |
| polar–STF 최대 canonical correlation | 0.80365–0.84256 | 관측 operator와 고정 covariance에 조건부인 값 |
| 같은 covariance의 직접 GLS와 carrier | TIE | independent implementation-verified; 같은 retained experiment |
| split-covariance 명목 95% ellipsoid | 93.205–93.560% coverage | 20,000 Gaussian parameter-error draws, seed 20261117 |
| full-GLS 기준, 같은 20k draws | 94.960% coverage | 같은 고정 Gaussian 법칙 |
| 독립 60k Gaussian 재검산 | split 93.288–93.728%, full 94.972–95.067% | 다른 독립 구현·seed; 같은 과학적 covariance 가정 |
| 공통 11계수 0 가설, 모델별 p의 최댓값 | 0.0153427383 | 고정 Gaussian coefficient Wald test |
| 전체 32개 row 평균 0 가설, 모델별 p의 최댓값 | 0.1122128922 | 다른 차원의 omnibus null test |
| physical+nuisance pullback | 22성분 중 rank 11 | \(\sigma,\omega,A\)의 개별 방향은 자유 calibration 아래 unbounded |

수치 원본은 `RESULTS/OWNED_TENSOR_RESULT.json`, carrier는 `RESULTS/OWNED_TENSOR_CARRIERS.npz`, 5개 view는 `RESULTS/FIVE_VIEW_RESULT.json`이다. 독립 검산은 `REVIEW/DATA_INDEPENDENT_REVIEW.json`과 `r58_review_checks.json`에서 확인한다. 통합 시 이 이름의 원본과 hash를 보존해야 한다.

20k calibration의 Monte Carlo 표준오차는 대략 0.17–0.18 percentage points다. 이 calibration은 관측 카탈로그의 실제 coverage를 측정한 것이 아니다. 관측으로부터 고정한 \(X,C\)에 대해 Gaussian 오차를 생성하여 nominal covariance 처리가 정확한지를 시험했다. selection, 실제 covariance의 misspecification, nonlinear evolution, 알려지지 않은 systematic을 이 실험으로 검증했다고 보고하지 않는다.

두 null p-value는 모순되지 않는다. 첫 번째는 정해진 11차원 coherent response의 계수들이 함께 0인지 묻는다. 두 번째는 32차원 관측 평균 전체가 0인지 묻는다. 이 관측 자료에서 전자는 더 표적화된 검정이다. 일곱 선언 모델 아래의 joint coefficient 결과는 조건부 5% 기준에서 유의하지만, 분석 선택과 모형 misspecification까지 보정된 cosmological discovery p-value는 아니다. 또한 모든 좌표별 interval hull이 0을 포함한다는 사실은 11차원 joint ellipsoid union이 원점을 포함한다는 뜻이 아니다. 투영된 구간과 joint set을 구분해야 한다.

기존 cosmic cache는 재적분하지 않았다. row/model identity와 일곱 모델의 수치 재현을 확인했고, 원래 operator fingerprint와 현재 부동소수점 바이트의 불일치는 명시적으로 남겼다. “exact-byte replay”나 독립 cosmic-model 검증으로 격상하지 않는다.

## 기존 5변수의 기여를 어디에 둘 것인가

R54의 판정대로 5개 view 자체는 reporting convention이다. R58은 이를 유지하면서 \(x\)를 signed vector+STF likelihood carrier로 실제 구현했다. precision은 \(J\), directional support utilization은 \(F_{\rm support}\), measure occupancy는 \(F_{\rm occupancy}\)로 구분한다.

- \(x\): 혼합 11계수의 signed estimate와 full covariance를 전달한다. 기존 scalar norm에서 사라지는 방향별 likelihood 차이를 보존한다.
- \(Q\): 선언된 coefficient-noise ellipsoid를 기준으로 측정한 gauge다. 현재의 통계적 ellipsoid를 물리적 ceiling으로 부르지 않는다.
- \(\Pi\): 정확히 이름 붙인 Gaussian null의 tail이다. \(Q\)와 공유하는 정보를 독립 p-value처럼 결합하지 않는다.
- \(F\): mixed contrast의 directional support와 interval hull을 제공한다. physical ceiling과 점유 measure가 없으므로 occupancy는 unavailable로 남긴다.
- \(G_F\): 초기 level을 보존한 depth contrast의 가역적 표현이다. full covariance를 함께 변환하여 likelihood가 보존된다. 이 재표현을 새로운 독립 데이터나 global-tilt evidence로 세지 않는다.

직접 GLS는 \(J=X^TC^{-1}X,\ t=X^TC^{-1}y\)라는 동일 정보를 사용한다. score compression 역시 이 Gaussian 선형 평균 모형에서는 이에 해당하는 고전적 표현이다 [L09]. 이 관계를 정직하게 공개하면 비교 대상이 분명해지고, 5개 view의 기여를 **결론이 바뀌는 원인·식별 가능한 물리 조합·보정 민감도를 일관되게 전달하는 구조**에 둘 수 있다. 그 구조의 실용적 가치 역시 실제 분석 예제로 보여야 한다.

## 여섯 연구주제별 출판 가능성

| 연구주제 | 현재 도달한 범위 | 출판 후보 기여 | 남은 최소 작업 / 불가 비교 처리 |
|---|---|---|---|
| low-\(\ell\) morphology와 physical observables | vector/STF의 방향정보 보존과 scalar-loss 반례; R58 데이터는 CF4 | 실제 owned CMB 자료에서 같은 가설을 대상으로 morphology와 physical response의 연결을 검증하면 확장 가능 | 기존 \(a_{\ell m}\), mask, MC, transfer가 있을 때만 MV/BipoSH와 비교. CF4와 CMB를 “anisotropy”라는 이름으로 같은 estimand로 만들지 않는다 [L01,L02] |
| dipole anomaly | CF4 apparent dipole와 coherent \(V\)를 함께 적합 | calibration 처방에 따른 apparent dipole 신뢰영역의 변화 | CMB dipole/aberration/Doppler의 독립 측정과 공통 response가 없으면 NOT_COMPARABLE. intrinsic dipole·lensing·boost의 조건부 가정을 유지 [L05,L06] |
| beyond-FLRW kinematical variables | 11 apparent 계수와 22성분 physical+nuisance pullback의 rank 구조 | 무엇을 측정하고 어떤 성분은 분리할 수 없는지 실제 likelihood로 보이는 결과 | \(\sigma,\omega,A\)의 prior-free 개별 제약을 주장하지 않는다. 정확한 closure/response가 있는 조합만 분석 [L03] |
| anisotropy 및 Bianchi 분류 | STF morphology를 보존하나 Bianchi transfer 적합 미수행 | 기존 validated Bianchi templates가 있으면 class-dependent response와 혼합 통계의 역할 시험 | STF eigenvalue를 Lie-algebra type로 바꾸지 않는다. source-bound 구조상수·진화·광전파가 없으면 해당 class는 BLOCKED_EXISTING_INPUT [L07] |
| \(H(z,\hat n)\) | 기존 CF4 depth 자료의 apparent angular coefficients와 full depth covariance | 교차 상관·zero-point 처방에 따른 confidence geometry와 calibration fragility | owned catalogue 범위에서 직접 GLS/cosmography와 동일 조건 비교. \(O(z)\) 식을 모든 redshift의 전역 \(H\)로 확대하지 않는다 [L03,L04,L10] |
| local boost와 global tilt 구별 | specified constant-\(V\) response와 혼합 계수; 임의 global tilt 미구현 | 기존 source-bound 전파 kernel이 있으면 식별 가능한 조합/degeneracy의 정확한 characterization | CONST_V 결과를 evolving homogeneous tilt의 배제로 확대하지 않는다. CMB/CF4 frame와 transfer가 없으면 분리 주장 보류 [L04–L06] |

일반 spacetime의 directional Hubble 분해는 이미 알려져 있고 [L03], 관측자 boost의 shear-dependent aberration과 distance 변환도 선행연구가 있다 [L04]. Bianchi의 near-isotropic shear modes를 temperature/polarization으로 제한하는 연구도 존재한다 [L07]. 그러므로 넓은 “비등방 우주론을 측정하는 최초의 텐서 방법”이라는 framing은 기각 위험이 높다. 이번 데이터가 직접 지지하는 좁은 calibration·혼합 inference 결과를 논문의 중심에 두는 편이 타당하다.

## 심사 시 가장 중요한 약점

**첫째, 선택된 카탈로그와 고정 covariance의 결과다.** 35,970 groups의 원자료 likelihood에 대한 sufficiency를 증명한 것이 아니라, 보유한 32-row carrier에서 동등성을 확인했다. whole-survey selection과 nonlinear model discrepancy를 포괄한다고 서술하면 scientific scope가 달라진다.

**둘째, 교차 공분산을 사용한다는 아이디어는 고전적이다.** 실제 novelty는 이 자료에서 나타나는 영향의 크기, 물리적 해석, 기존 연구가 놓친 보정 경로 및 재현 가능한 분석에 달렸다. 이것을 확인할 동일 CF4 estimand의 closest prior-art 비교가 아직 필요하다. 광범위한 cosmography/BipoSH 비교만으로 그 문헌 의무를 대신할 수 없다.

**셋째, 유의성과 물리적 식별성을 구분해야 한다.** 11 apparent 계수의 joint null과 자유 calibration을 포함한 22성분 물리 모형은 같은 문제가 아니다. \(\sigma,\omega,A\) 개별 성분의 unbounded 결과는 코드 실패가 아니라 선언한 모형의 rank 구조다. 추가 prior를 넣으면 conditional inference로 이름을 바꿔야 한다.

**넷째, 관측값을 본 뒤 구성한 연구의 선택효과가 남아 있다.** 5개 view·일곱 nuisance model·방향·depth·가설을 변경하면서 유의한 결과만 채택하면 confidence claim이 달라진다. 기존 null mocks가 해당 선택을 재현할 수 있으면 재현하고, 그 수가 tail을 분해하지 못하면 UNDERPOWERED_NOT_COMPARABLE로 기록한다. 새로운 자료를 요구하지 않고도 조건부 방법론 응용으로 논문을 닫을 수 있다 [L08].

## 남은 로컬 benchmark를 수렴시키는 규칙

실행 규약은 `BENCHMARK_CONTRACT.json`이 정한다. 이미 통과한 고정 입력의 GLS/score 동등성 검사를 의미 없이 반복하지 않는다. 코드나 입력 identity가 바뀐 의무만 다시 검증한다.

우선순위는 (1) existing end-to-end mocks의 실제 존재·선택·frame·covariance provenance 확인, (2) 존재한다면 고정된 full/split/zero-point 분석을 그대로 적용해 empirical calibration 범위를 확장, (3) 동일 카탈로그·관측량을 다룬 closest prior art와 exact-estimand 비교, (4) inference table·figure·논문 claim 정리다. 각 비교는 같은 데이터, response, nuisance, target, calibration budget을 사용한다.

existing CMB/Bianchi products가 없거나 공통 estimand를 정당화할 수 없으면 그 비교를 NOT_COMPARABLE로 종료한다. “비교 불가능”을 method 승리로 점수화하지 않는다. 적은 mock 수 때문에 차이가 식별되지 않으면 UNDERPOWERED_NOT_COMPARABLE이다. 데이터 다운로드 확대나 새로운 Bianchi solver 전체 개발을 이번 논문의 필수조건으로 추가하지 않는다.

## 현재 권고

주 논문 경로는 **selected CF4의 vector–STF joint likelihood, 교차 공분산 제거가 만드는 confidence miscalibration, calibration model family에 대한 mixed confidence geometry**로 고정하는 것이 좋다. 5개 view는 이 결과의 해석·보고 구조로 쓰고, 직접 GLS와의 TIE를 명시한다. global tilt나 Bianchi classification은 기존 자료·validated transfer가 바로 지원하는 부분만 보조 결과로 넣는다.

현재 결과는 conditional methods application의 초안을 작성할 근거를 제공한다. novelty의 최종 판정은 같은 CF4 target에 대한 가까운 문헌과의 차이, existing mocks가 지원하는 calibration 범위, 관측 결론의 견고성을 확인한 뒤 내린다. 결과가 기존 연구의 재현 또는 미미한 correction으로 수렴하면 그 판정을 유지하고 과장된 physical-discovery framing을 채택하지 않는다.

## 원전

이전 문헌 검토와 조회 범위는 `LITERATURE_REVIEW_KO.md`, 원문 확인 수준·버전은 `LITERATURE_SOURCES.json`에 있다. 이 파일은 해당 source records를 재사용한다.

[L01] Copi, Huterer & Starkman, [multipole vectors](https://arxiv.org/abs/astro-ph/0310511v2).  
[L02] Hajian & Souradeep, [BipoSH/BiPS formalism](https://arxiv.org/abs/astro-ph/0501001v1).  
[L03] Heinesen, [general luminosity-distance Hubble law](https://arxiv.org/abs/2010.06534v2).  
[L04] Maartens et al., [observer-dependent covariant cosmography](https://arxiv.org/abs/2312.09875v3).  
[L05] Ferreira & Quartin, [intrinsic dipole constraints](https://arxiv.org/abs/2011.08385v2), [estimator pipeline](https://arxiv.org/abs/2107.10846).  
[L06] Roldan, Notari & Quartin, [boost or intrinsic dipole](https://arxiv.org/abs/1603.02664v2).  
[L07] Saadeh et al., [Bianchi anisotropy constraints](https://arxiv.org/abs/1605.07178v2).  
[L08] Planck Collaboration, [2018 isotropy and statistics](https://www.aanda.org/articles/aa/full_html/2020/09/aa35201-19/aa35201-19.html).  
[L09] Alsing & Wandelt, [score compression](https://arxiv.org/abs/1712.00012v2).  
[L10] Cowell, Dhawan & Macpherson, [quadrupolar Hubble expansion in Pantheon+](https://arxiv.org/abs/2212.13569v1).

