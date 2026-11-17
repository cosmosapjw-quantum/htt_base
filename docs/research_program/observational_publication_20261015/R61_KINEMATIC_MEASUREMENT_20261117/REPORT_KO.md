# R61 — beyond-FLRW 운동학 측정의 실제 제약과 논문화 판단

작성일: 2026-11-17. 기준 commit: `fb6ae9f21585e194ef29dabc91d79a529e0ac57e`. 이번 작업은 beyond-FLRW kinematic quantity measurement 한 가지에 한정한 10단계 이론·코딩 연구다. 기존 여섯 연구 가지를 다시 시작하지 않았다. 독립 심사 및 최종 게시 상태는 `RESEARCH_RECORD.json`과 `REVIEW/final_review.md`에서 확인한다.

## 1. 과학적 결론

현재 관측 자료로 완성할 수 있는 결과는 **고정된 CF4 거리–적색편이 실험의 공동 운동학 신뢰집합, 비선형 혼합량의 범위, 공통 각도 보정에 불변인 깊이 차이**다. 국소 shear·가속도·vorticity·팽창률 전체를 독립적으로 측정했다는 결론은 확보되지 않았다.

이번에는 연구계획만 작성하지 않고 기존 실제 35,970개 CF4 group의 32차원 관측량과 공분산을 재사용하여 다음을 계산했다.

- 동일한 공동 신뢰집합에서 normalized shear, acceleration, relative speed, directional expansion RMS 및 두 혼합 불변량의 범위.
- source 수준에서 구성한 16모수 STF 적색편이 응답과 $K(0.08)-K(0.02)$의 신뢰구간.
- 관측 범위에서 $z=0$으로 외삽할 때의 오차 증가와 exact-log 각도 응답으로 바꿨을 때의 적합 변화.
- 성분별 범위를 별도로 보관하는 방법과 공동 집합을 보존하는 방법의 실제 차이.

**출판 판단은 조건부 방법론·관측 응용 논문으로 수렴**하는 것이 타당하다. 새로운 중력이론이나 FLRW 위반의 검출 논문으로 제출할 근거는 부족하다. 새로운 범위·깊이 차이 계산은 실제 산출물이지만, survey selection/coverage와 물리 보정오차를 해결했다는 뜻은 아니다. 투고 가능성의 최종 판정에는 `RESEARCH_PLAN_KO.md`에 지정한 source-matched 비교와 독립적인 오차 예산이 필요하다.

## 2. 어떤 실험을 재사용했는가

입력은 R58의 `OWNED_TENSOR_CARRIERS.npz`이며 SHA256은 `42f6bc5158fdf2f876720db12c44b088bc2db9734887e0d84ae098b234a7e64d`다. 기존 R54 source operator, R58 full-covariance GLS, R60 calibration 및 velocity-slope 응답을 재사용했다. catalog의 관측 범위는 대략 $0.01<z<0.10$, 방향은 ICRS/J2000, sourceward convention이다. 정확한 sample·frame·error-law 근거는 [입력 감사](REVIEW/owned_inputs.md)와 결과 JSON의 source 필드에 남겼다.

일곱 변형은 `log`, `log_mono`, `log_split`, `log_survey`, `log_mono_radial`, `log_mono_galactic`, `log_mono_error`다. 모두 같은 source sample을 변환하므로 일곱 독립 관측처럼 likelihood를 곱하지 않는다. 각 변형의 신뢰집합을 합집합으로 보관하고, 표에는 그 함수 범위의 외피를 제시한다.

기본 법칙은 $C=N+S$인 고정 Gaussian likelihood다. 민감도 계산의 λ=1.25는 cosmic-covariance 성분 $S$만 25% 증가시킨 경우다. 이를 관측으로 추정한 covariance posterior라고 부르지 않는다. 각도 보정오차의 0, 1, 5, 10 mmag 역시 선언한 deterministic allowance이며 계측된 오차가 아니다.

## 3. 물리 변수와 likelihood

signature는 $(-,+,+,+)$, $U^aU_a=-c^2$, $H=\Theta/3>0$다. 선도 방향별 팽창계수는

$$
\mathfrak H(n)=H-\frac{A_an^a}{c}+\sigma_{ab}n^an^b.
$$

이는 기존 covariant cosmography의 결과다. 거리의 선도 계수 $D_L=cz/\mathfrak H_o(n)+O(z^2)$를 현재 유한 깊이 실험에 적용하려면 higher-order terms와 observer/source frame을 별도로 통제해야 한다. [Heinesen 2021](https://arxiv.org/html/2010.06534v2), [Maartens et al. 2024](https://arxiv.org/html/2312.09875v3).

현재 관측 모수는

$$
\alpha=(V_3,d_{H,3},\kappa_5),\qquad
\beta=V/c,\quad a=A/(cH),\quad s=\sigma/H,
$$

이며 선언한 1차 응답에서 $d_H=-a+d_{cal}$, $\kappa=s+q_{cal}$이다. 따라서

$$
L_m(\theta,\xi\mid y_m)\propto
\exp\{-\tfrac12[y_m-X_mR(\theta,\xi)]^T C_m^{-1}
[y_m-X_mR(\theta,\xi)]\}
$$

가 직접 운동학 성분을 넣는 likelihood다. calibration ξ와 물리 상태를 분리하지 않으면 일부 방향은 식별되지 않는다. 이 문제를 모수의 0 대입이나 임의 prior로 숨기지 않았다.

보정 몸체는

$$
\frac{|d_{cal}|^2}{3}+\frac{2\|q_{cal}\|_F^2}{15}\le\rho^2,
\qquad r_{mag}=\frac5{\ln10}\rho
$$

다. 주 결과는 α의 **동일한 11차원 95% 신뢰집합**, $t=\chi^2_{11}(.95)=19.67513757268249$, 의 함수상이다. 각 scalar마다 χ²₁ cutoff를 쓰지 않았다. 16모수 깊이 모형에는 χ²₁₆ cutoff를 사용한다. 이 coverage는 선언한 Gaussian 법칙과 calibration 몸체를 조건으로 한다.

네 monopole 행이 제거된 32차원 실험은 absolute $H,\Theta$를 독립적으로 측정하지 않는다. 거리 응답에는 vorticity 열이 없다. 따라서 해당 성분은 **미측정**이며 0이라는 결과가 아니다. 고적색편이 Gaia E2/B1을 국소 σ/ω로 바꾸는 물리 transfer도 새로 가정하지 않았다. [Heinesen–Korzyński 2024](https://arxiv.org/html/2406.06167v1)의 nearby/geodesic/Fermi–Walker 조건과 실제 owned astrometric 입력의 차이는 [원전 검토](REVIEW/kinematic_sources.md)에 명시했다.

## 4. 실제 공동 운동학 범위

아래는 λ=1, 일곱 모형의 합집합이다. 크기 변수의 하한은 모두 0이다. 이때 Σ는 $\|s\|_F/\sqrt6$, $\mathcal A_H$는 $\sqrt{|a|^2/3+2\|s\|_F^2/15}$다.

| 함수 | 추가 calibration 0 mmag | 추가 calibration 5 mmag |
|---|---:|---:|
| Σ | [0, 0.0625488] | [0, 0.0651231] |
| $\lVert A\rVert/(cH)$ | [0, 0.101538] | [0, 0.105526] |
| $\lVert\beta\rVert$ | [0, 0.00420553] | [0, 0.00420553] |
| $\mathcal A_H$ | [0, 0.0604945] | [0, 0.0627971] |
| $\beta\cdot a$ | [−3.85992×10⁻⁵, 3.57357×10⁻⁴] | [−5.36402×10⁻⁵, 3.74129×10⁻⁴] |
| $\beta^Ts\beta$ | [−6.28151×10⁻⁷, 5.04421×10⁻⁷] | [−6.71944×10⁻⁷, 5.59450×10⁻⁷] |

입력·전체 precision·witness는 [운동학 결과](RESULTS/IMAGES/KINEMATIC_IMAGES.json)와 [혼합 불변량 결과](RESULTS/MIXED/R61_MIXED_INVARIANT_RESULT.json)에 있다. β 상한은 현재 상대속도 응답에서 약 1,260.79 km/s다. 이를 global tilt 측정으로 바꾸지 않는다. $\mathcal A_H$ 역시 모든 beyond-FLRW 성분을 포착하는 총량이 아니며, vorticity를 포함하지 않는다.

λ=1.25, calibration 0 mmag에서는 Σ 상한 0.0656549, $\lVert a\rVert$ 상한 0.106931, $\lVert\beta\rVert$ 상한 0.00451645다. 이 값은 stochastic-law 선택에 대한 민감도다.

기존 5차원 shear 결과와 모순은 없다. 별도의 marginal5 confidence set에서는 가장 약한 모형의 Σ 하한이 0.000676929이고, 이를 0까지 허용하는 최소 full-sky 보정 RMS가 1.31474845 mmag다. 이번 simultaneous11 집합에서는 합집합의 Σ 하한이 이미 0이다. 서로 다른 null 차원과 cutoff를 혼용하면 주장을 과장하게 된다.

또한 모든 scalar 범위가 각각 0을 포함한다고 해서 동일한 한 상태에서 모든 성분이 동시에 0이라는 뜻은 아니다. λ=1, ρ=0의 전체 α=0 검정에서는 일곱 변형의 최대 nominal $p_{11}=0.0153427383$이다. 이는 현재 apparent-response null에 대한 결과이며 FLRW 자체의 배제나 물리 shear 검출이 아니다. scalar interval의 직적과 원래 공동 집합의 차이를 실제 자료가 보여 준다.

## 5. 혼합 불변량과 tensorized 방법의 기여

$\beta\cdot a$는 전체 velocity–dipole covariance를 보존한 이차형식 문제로 풀었다. 동일한 11차원 신뢰집합의 coordinate support로 만든 상자에서 정확히 계산한 곱의 범위는 공동 타원체 범위보다 약 **3.64–4.81배** 넓다. 이는 같은 자료를 성분별 범위만으로 축약할 때 생기는 기하학적 차이다. full-covariance GLS보다 새로운 Fisher 정보를 얻었다는 주장은 아니다.

$\beta^Ts\beta$는 β를 고정한 뒤 κ를 조건부 제거하여 3차원 최적화로 줄였다. $v_A=\beta^TE_A\beta$라 할 때

$$
v^T\bar\kappa\ \pm
\sqrt{t-r_\beta^2}\sqrt{v^TC_{\kappa|\beta}v}
\ \pm\sqrt5\rho\,|\beta|^2
$$

가 조건부 endpoint다. 이 계산에 beta–kappa cross-covariance가 직접 들어간다. 전역 enclosing bound와 feasible witness의 차이를 기록하는 branch-and-bound를 구현했고, 실제 7×4 조건 모두 endpoint 절대 gap이 $10^{-10}$ 이하에 도달했다. 원격 production의 최대 gap은 약 $9.9974\times10^{-11}$다. float64 계산이며 formal outward-rounded interval proof는 아니다.

처음 기록한 cubic componentwise absolute-value bound에는 상자화 외에도 triangle-inequality의 느슨함이 들어 있다. 그 비율을 순수한 covariance 보존 효과로 해석하지 않는다. R8의 별도 [BOX_COMPARISON](RESULTS/BOX_COMPARISON/R61_BOX_COMPARISON_RESULT.json)은 원래 endpoint를 재사용하면서 실제 coordinate box의 극값을 계산했다. 0 mmag에서 실제 box 폭은 joint enclosing 폭의 **4.987–5.814배**, 전체 28조건에서는 **4.386–5.814배**였다. 단순 triangle bound에는 여기서 추가로 **1.750–2.074배**의 느슨함이 있었다. 이 비교는 공동 영역을 상자로 교체한 효과이며, cross-covariance 항만의 기여나 full GLS에 대한 정보 이득을 분리해 측정한 것은 아니다.

5변수 틀의 이번 역할은 다음과 같다.

| 관점 | 현재의 실체 | 주의할 해석 |
|---|---|---|
| x | β, a, STF s, 깊이 계수 및 혼합 함수가 연결된 공동 상태 | 하나의 signed scalar x_c로 대체하지 않음 |
| Q | 선언한 likelihood 거리와 calibration-body gauge | 단위·정규화·고정 covariance를 명시 |
| Π | 해당 Gaussian null의 tail 및 confidence inversion | truth probability 또는 새 독립 관측이 아님 |
| F_support | 하나의 집합에서 얻은 방향별·비선형 함수 범위 | 원래 occupancy F와 동일시하지 않음 |
| G_support | cross-depth covariance를 포함하는 $n^T\Delta K n$ | occupancy-based G_F를 새로 계산했다고 하지 않음 |

원래 occupancy F에는 support measure와 physical ceiling이 필요하다. 이번에 이를 임의로 만들어 채우지 않았다. 이 틀의 실질적 기여는 모든 view가 같은 물리 가정·likelihood·보정 범위를 사용하게 하고, 혼합량에 필요한 공동 구조를 유지한다는 데 있다. Gaussian projection과 trust-region 원리 자체는 기존 수학이다.

## 6. 새 깊이 측정량: 공통 보정오차가 소거되는 차이

새 응답은

$$
K(z)=K_p+\frac{z-0.05}{0.05}K_1,
\qquad\Delta K=K(0.08)-K(0.02)=1.2K_1
$$

이다. 실제 source의 z와 방향을 이용해 response32x16을 만들었고 모든 변형에서 rank16이었다. joint16 confidence image의 cutoff는 26.29622760486423이다.

깊이에 무관한 additive calibration $d_{cal}\cdot n+Q_{cal}:nn$은 intercept 열에 들어간다. GLS의 affine equivariance 때문에 K1과 ΔK는 이 변화에 정확히 불변이다. 실제 calibration injection에서 slope의 최대 변화는 약 $4.90\times10^{-17}$이었다. 이 결과는 지정한 공통 nuisance subspace에 관한 것이며 depth-dependent calibration에는 적용되지 않는다.

| 관측량·진단 | 실제 결과 |
|---|---:|
| 기울기 0 검정의 nominal p 범위 | 0.563319–0.943287 |
| primary log의 $\sqrt{2/15}\|\Delta K\|_F$ 점 추정 | 0.00904397 |
| primary log의 joint16 범위 | [0, 0.0577714] |
| 7모형 union의 joint16 범위 | [0, 0.163404] |
| finite velocity slope $\|V_1\|\le1000$ km/s를 더한 union | [0, 0.163544] |
| $\|V_1\|\le3000$ km/s를 더한 union | [0, 0.163824] |
| covariance trace 최적 pivot | z=0.05481–0.05638 |
| $z=0$ RMS 성분 오차 / 최적 pivot 오차 | 2.690–3.006 |

근거는 [깊이 계산](RESULTS/DEPTH_CORRECTED/KINEMATIC_DEPTH.json)이다. 상대적으로 넓은 union 상한은 `log_mono_galactic`에서 나온다. 이 변형을 사후 제외하여 작은 상한만 대표값으로 쓰지 않았다. 앞의 velocity-slope 예산은 선언한 민감도 입력이고, R60의 비물리적으로 큰 자유 slope optimum을 prior로 사용하지 않았다. 보정이 같은 affine-z STF 응답에 속하는 경우에는 endpoint RMS 차이 ρ_delta만큼 contrast 범위를 넓힐 수 있다. 일반적인 깊이 의존 보정에서는 두 endpoint 차이만으로 충분하지 않다. 실제 GLS에 전달된 $\delta y=O b$에 대해 $B_\Delta=1.2S_{K1}V_{16}X_{16}^TC^{-1}$를 계산하고 $\sqrt{2/15}\lVert B_\Delta\delta y\rVert\le\rho_\Delta$를 예산으로 사용해야 한다. 새 결과에는 이 5×32 bias operator를 공개했다.

독립 심사가 제시한 $Q_{cal}(z)=0.01[(z-.02)/.05][(z-.08)/.05]E_0$는 두 endpoint에서 0이지만, 실제 일곱 source operator에 전달하면 fitted contrast RMS bias가 약 **0.000992–0.001413** 생긴다. 이 반례 때문에 일반 endpoint 예산 주장을 위와 같이 제한했다. 기존 수치표에는 그 일반 예산을 적용하지 않았으므로 기존 endpoint 수치는 유지된다.

이 자료에서는 STF 기울기를 추가해야 한다는 증거가 없다. 그러나 이 결과가 실제 shear가 시간에 따라 일정함을 입증하지는 않는다. 일반 cosmography에서

$$
\eta=\log(\mathfrak H_o/H_f)
+\tfrac12[\mathfrak Q_o(n)-q_f]z+O(z^2)
$$

이므로 관측 적색편이 기울기는 effective deceleration과 공간 미분, 응답 잔차까지 포함할 수 있다. **K1은 $\dot\sigma$가 아니다.** 상세 유도와 masked multipole mixing의 제한은 [THEORY.md](THEORY.md)에 있다.

## 7. 각도 선형화의 실제 영향

선언한 closure $D_L=D_{L,fid}/(1+h(n))$에서는 η의 각도 부분이 $\log(1+h)$다. 같은 자료와 covariance에서 이 형태를 적합하고 기존 선형 h 응답과 비교했다. Doppler 항은 기존 1차 kernel을 유지했으므로 전체 모형을 fully nonlinear GR likelihood라고 부르지 않는다.

7개 변형의 최대 성분 이동은 각 모형 내 linear standard error의 **0.0527–0.1368배**였다. fitted linear point에서 operator를 통과한 remainder의 Gaussian norm은 **0.0752–0.2490**이었다. 두 초기값의 적합이 일치했고 수치 parameter bounds는 활성화되지 않았으며, 적합된 $1+h(n)$의 전 하늘 하한도 양수였다.

임의 omitted response δy의 GLS bias b에는 $b^TV^{-1}b\le\|C^{-1/2}\delta y\|^2$가 성립한다. 따라서 실제로 통제해야 할 것은 단순 raw residual의 크기가 아니라 관측 operator와 covariance를 통과한 remainder다. 현재 수치는 fitted states에서의 한 closure 검사다. 전체 신뢰집합에서의 uniform remainder 또는 일반 시공간의 광학 응답 타당성을 증명하지 않았다.

## 8. 선행방법과 비교한 새로움

| 비교 대상 | 이미 알려진 부분 | 이번에 추가한 결과 |
|---|---|---|
| Heinesen의 일반 거리 cosmography | expansion·acceleration·shear multipoles | 실제 CF4 joint image와 finite-depth response의 정량 제약 |
| Maartens 등의 observer-dependent cosmography | source/matter frame과 observer boost의 구별 | 현재 응답의 frame 가정과 물리 승격 조건의 명시 |
| Stiskalek–Desmond–Lavaux의 forward analysis | calibration·거리·flow 공동 추론, radial flow가 apparent dipole을 흉내낼 수 있음 | STF 깊이 차이와 nonlinear joint functionals의 측정; 동일 likelihood에서의 우월성은 미입증 |
| Heinesen–Korzyński의 drift cosmography | nearby proper motion으로 shear/vorticity에 접근 | owned Gaia의 어떤 입력이 부족한지 특정; 직접 ω 측정은 추가하지 않음 |
| GLS·confidence projection·partial identification | 공동 타원체, Schur complement, 함수상과 집합 식별 | 실제 source-bound 계산, 혼합량의 numerical enclosure, 명시적인 calibration/depth 민감도 |

[Stiskalek et al. 2025](https://arxiv.org/html/2509.14997v2)는 CF4 W1 Tully–Fisher 등 원자료의 latent-distance/calibration/flow model을 사용한다. 현재 grouped32D fixed-C 실험과 sample, nuisance, selection이 다르므로 p값만 비교해 방법론의 우열을 판단할 수 없다. 비교 초안과 claim gate는 [paper_positioning.md](REVIEW/paper_positioning.md)에 있다.

현재의 새로움 후보는 **기존 자료의 관측 응답을 보존하면서, 물리적 해석에 필요한 공동 비선형 함수와 깊이 차이를 실제 범위로 완성했다는 점**이다. 국제 문헌에서 동등한 측정 결과가 전혀 없음을 증명했다거나 새 일반통계 정리를 얻었다고 주장하지 않는다. 이 결과가 논문으로 충분한 scientific significance를 가지려면, raw-source 분석과의 정합성 및 독립 오차 예산을 갖춘 비교가 필요하다.

## 9. 검증과 실패의 보존

기본 새 모듈의 unit/integration 검증 24개와 별도 box-extremum 수학 검증 10개가 통과했다. 최종 현재 코드에서 같은 34개를 한 번에 다시 실행하여 **34 passed**를 기록했다. [최종 검증](DAG_VALIDATION.json)에 종료 코드와 로그 해시가 있다. 실제 IMAGES, DEPTH, MIXED 세 실행은 모두 exit0이며 [BATCH_EXECUTION.json](RESULTS/BATCH_EXECUTION.json)에 명령·시간·로그 해시가 있다. source/operator parity, rank16, nested Wald–LR 일치, calibration injection, positivity, witness 재구성을 검사했다.

초기 독립 Cartesian SLSQP 검산은 unscaled 목적함수/제약에서 line-search 종료에 실패했다. 정규화 후 엄격한 feasible/value 기준을 유지하여 통과했고 원래 실패와 진단을 `DEVELOPMENT_TESTS.log`, `ORACLE_DIAGNOSTIC.json`에 보존했다. production trust-region 알고리즘을 그 실패에 맞춰 약화하지 않았다.

혼합 최적화의 회전 covariance·조건부 lift·직접 8차원 표본 검사는 [isolated validation](RESULTS/ISOLATED_MIXED_VALIDATION.json)에 있다. 대칭적인 등방 극값 manifold stress에서는 100,000 node cap에서 gap이 남은 사례를 `NODE_CAP`으로 보존했다. 실제 28개 관측 조건의 수렴 결과와 구분한다. Wolfram 상징 검산에서 발생한 경고 역시 [SYMBOLIC_CHECKS.json](RESULTS/SYMBOLIC_CHECKS.json)에 남겼다.

독립 최종 심사는 `PASS WITH MINOR REVISIONS`였고, R61-F1은 문장 범위의 교정과 실제 bias operator/반례 계산으로 닫았다. 교정 전후 기존 numeric leaf 6,159개와 원래 response 배열의 dtype·shape·bytes가 같았다. [교정 기록](REVIEW/R61_F1_CLOSURE.json), R8 box 비교의 추가 검증, 최종 figure manifest는 [VALIDATION.md](VALIDATION.md)에 연결한다. 관측적 식별 실패, 수치 최적화의 종료 문제, 환경의 pytest 부재와 원격 transport 문제를 서로 다른 종류로 기록했다.

## 10. 수렴 방향

한 편의 논문을 **“Joint kinematic constraints and depth contrasts in Cosmicflows-4”**라는 작업 제목으로 준비한다. 현재 결과로 작성 가능한 본문은 theory/likelihood, nonlinear images, actual finite-depth contrast, response sensitivity, observational interpretation이다. 후속 작업은 새 지표 발산보다 source-matched comparison, calibration budget, finite-z/selection uncertainty를 닫는 데 집중한다. 구체적 산출물과 종료 조건은 [연구계획](RESEARCH_PLAN_KO.md) 및 [DAG](RESEARCH_DAG.json)에 있다.

현재 관측에서 ω나 absolute H가 식별되지 않는 사실은 일반적인 측정 불가능 정리가 아니다. 적합한 monopole calibration과 nonradial response가 추가되면 다른 실험이 된다. 그 확장은 현재 단일 CF4 측정 논문의 자동 후속 루프로 실행하지 않는다.
