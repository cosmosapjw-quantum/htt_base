# R97 결과 독립 검토 — 2026-11-23

## 판정

R97에서 CF4 원천 계보, CMB 저다중극 통계, Bianchi 비축대칭 각도 수송은 실제로 진전됐다. 그러나 현재의 수치를 그대로 물리적 보정 경계와 수렴한 편광 전달함수로 채택할 수는 없다. 이번 검토는 Thomson 편광 부호, 시간 적분, CF4 원천 보정의 계산식, P1 비율 경계, CMB 학습·검정 분리에서 재현 가능한 결함을 확인했다. 폐기할 대상은 해당 해석과 아직 교정되지 않은 수치이며, 기존 원천·행렬·조화계수·각도 수송 코드는 계속 사용할 수 있다.

검토 대상은 `dc080cb48b7bc20682078d4c215143b22794a7b2` (R97), 기존 branch `research/r69-observable-physics-bridges-20261118`이다. 원본 root는 `/home/cosmosapjw/Dropbox/bianchi/htt_base`이다. 현재 요청의 R6 검토만 수행했다. 새로운 전체 10단계 연구루프를 시행하거나 원본 R95–R97 코드·결과를 덮어쓰지 않았다. 이 폴더는 독립 진단 코드와 관측 출력, 수정 명세를 보존한다.

별도 fresh-context native 검토자 3명이 CF4/P1, CMB, Bianchi를 분담했다. 주 검토자는 실제 코드·원출력을 대조했고 P1 비율 문제를 별도로 검산했다. R96/R97 관련 테스트 18개는 2.03초에 통과했고, R78 strict authority 검사도 32개 통과했다. 이 통과 결과와 아래 오류가 공존하는 이유는 기존 검사에 해당 의미론적 반례·시간 수렴·signed 충돌 투영이 없기 때문이다. 전체 저장소 CI는 재실행하지 않았다.

## 중요한 결과와 처리

| ID | 분야 | 판정 | 현재 필요한 처리 |
|---|---|---|---|
| F1 | Thomson 충돌 | 기존 sky convention과 T2–E2 결합 부호 불일치 | signed Q/U, TE/TB를 쓰기 전에 수정 |
| F2 | Bianchi 시간 적분 | 같은 유한 계층에서 E/B power 약 4배 차이 | 시간 전파와 격자 오차부터 해결 |
| F3 | CF4 영점 보정 | 고정 가산모형과 실제 거리보정 재적합이 다름 | 물리적 nuisance map 재정식화 |
| F4 | P1 보정 상한 | 동일 R97 타원체 내부에서 명시적 반례 | 현재 upper bound 주장 철회·재계산 |
| F5 | CMB null | heldout sky가 feature 가중치 적합에 참여 | 모든 적합을 train 안으로 이동 |
| F6 | MASTER 검산 | 평균의 비와 비의 평균을 비교 | 동일 추정대상으로 검산 |
| F7 | CF4 식별 차원 | 미추정 DirectCal 대비를 거의 고정, ridge가 차원 증가 | 조건부 가정과 nuisance 차원 명시 |
| F8 | Bianchi ray 검증 | 원래 oracle 입력이 Jacobi 위반 | 적합한 VII_h 양성 대조로 재검증; 이번 검토에서 유한 국소 검사 통과 |

F1–F7은 해당 결과를 해석·이용하기 전에 수정할 구체적 문제다. F8은 기존 검증 숫자의 의미가 제한됐다는 문제이며, 이번 양성 대조는 각도 수송 연산자를 살릴 근거를 제공한다. 어느 항목도 일반 Bianchi 연구나 CF4 식별 문제에 대한 보편적 no-go가 아니다.

## F1. Thomson 충돌의 signed 편광 규약

위치: `scripts/r97/bianchi_coupled_m_transport.py:154–157`. 비교 규약은 `scripts/r95/bianchi_polarized_hierarchy.py:326–338,359–368`의 J–Stokes 변환 및 `htt/bass/transport/general_bianchi_transfer.py:468–472`의 Q/U 합성이다. 모든 상대경로의 기준은 위에 명시한 절대 root다.

구현에서 쓰는 Q+iU = −sum (E_lm+i B_lm) spin2Y_lm 규약 아래, 단위 T20/E20/B20를 각도상 coherency tensor에 넣고
C[J] = (3/(8 pi)) P (integral J dOmega) P − J
를 적용한 뒤 원래 합성·투영으로 복귀했다. 그 결과 (T2,E2) 생성자는 다음과 같다.

```text
독립 각도구적: [[-0.9, +sqrt(6)/10],
               [+sqrt(6)/10, -0.4]]
R97 구현:     [[-0.9, -sqrt(6)/10],
               [-sqrt(6)/10, -0.4]]
B2 생성자: -1 (양쪽 일치)
```

수치 비대각 성분은 +0.244948974 vs −0.244948974다. Wolfram의 독립 m=0 기호적 구적도 +sqrt(6)/10을 반환했다. 두 행렬의 고유값은 모두 {−1,−0.3}이며 diag(1,−1) 유사변환으로 연결되므로 기존 고유값 검사로 구별할 수 없다. 단일 CAS 축과 각도구적을 실행한 것이며 역사적 네 축 CAS 승인을 의미하지 않는다.

현재 온도 원천만 존재하고 초기 편광이 0인 계층에서는 E와 B를 함께 뒤집는 결과다. 그러므로 EE, BB, EB, B/E는 이 부호에 불변이지만 TE, TB와 signed Q/U는 바뀐다. E/B convention을 바꿔 해결하려면 합성·투영·원천·관측 비교까지 모두 변환해야 한다. 최소 수정은 기존 sky convention을 유지하고 충돌행렬의 두 비대각 부호를 교정한 뒤 단위 T/E/B의 signed angular projection을 회귀검사하는 것이다.

재현: `repro/bianchi_collision.py`, 원출력 `outputs/bianchi_collision.txt`.

## F2. 시간 적분 오차가 편광 power를 크게 바꾼다

위치: `scripts/r97/bianchi_coupled_m_transport.py:586–598`. R97은 z=1600부터 0까지 155개 구간마다 backward Euler 한 스텝을 적용한다. 관측된 최대 k Delta_eta=2.869273, 최대 Delta_tau=2.170406이다. 순수 진동 고유모드에서도 backward Euler의 norm-squared 증폭률은 1/(1+(omega Delta_eta)^2)이므로 안정성이 정확성을 보장하지 않는다.

원래 각 구간의 midpoint 행렬, 불투명도, 원천을 완전히 유지하고 affine system을 augmented matrix exponential로 적분했다. 이는 시간격자상의 piecewise-constant 문제에 대한 독립 전파이며, 배경이나 물리모형을 바꾼 비교가 아니다.

| VI_-1/9, L=60, m=−2..2 | 원래 backward Euler | frozen-interval matrix exponential |
|---|---:|---:|
| B/E mode-norm ratio | 1.3948601141 | 1.4672400900 |
| sum of squared E coefficients | 4.31010199e−13 | 1.72971715e−12 |
| sum of squared B coefficients | 8.38588415e−13 | 3.72372381e−12 |
| m != 0 T power fraction | 0.76327358 | 0.74875564 |

E power는 4.01배, B power는 4.44배다. 이 값은 현재 prescribed-source 유한 계층의 mode-power이며 관측된 우주론적 C_l 측정치가 아니다. 비교에는 원본 충돌 부호를 유지했다. F1의 전역 편광 부호는 이 표의 power와 B/E를 바꾸지 않는다.

L=16 순수 m=0 시드의 경우 B/E는 0.90377256에서 1.07248084, m != 0 T fraction은 0.24582089에서 0.26389196으로 변한다. 따라서 비축대칭 산란의 존재는 유지된다. 같은 frozen 구간을 1,2,4,8,16,32로 세분한 backward Euler도 이 방향으로 변화한다. L=60 B/E의 세분 변화는 단조롭지 않으므로 32분할 결과도 최종 수렴값으로 선언하지 않았다.

최소 수정: 우선 이미 구성된 sparse operator를 그대로 살려 affine exponential/Krylov 또는 적절한 정확도의 stiff/IMEX 전파를 도입한다. 그 뒤 시간격자를 바꾸면서 계수와 원천을 다시 평가해 시간오차, L 절단오차, m 절단오차를 별도로 측정한다. L=32와 60의 작은 차이만으로 시간 수렴을 주장할 수 없다. 여기의 matrix-exponential 값은 원래 midpoint 문제를 교정한 비교 기준이며 연속 배경의 최종 해가 아니다.

재현: `repro/bianchi_backward_euler.py`, `repro/bianchi_frozen_exact.py`; 대응 원출력은 `outputs/`에 있다.

## F3. CF4 가산 속도 근사와 실제 거리 영점 보정을 구별해야 한다

위치: `scripts/r97/cf4_genealogy_and_partial_id.py:53–54,421–422,447–455,477–492`.

R97의 J7_ivw는 H_fid=70 km/s/Mpc에서 등방 속도잔차를 바꾸고 원래 거리 설계행렬을 고정한다. W7의 행합이 1이므로 공통 보정 방향은 H만 바꾸며 dipole/STF5 변화는 roundoff다. 이는 정의한 고정 선형모형에서는 계산 가능한 정확한 식이다.

그러나 원천 modulus를 delta만큼 바꾸면 d가 10^(delta/5)d로 변하며 H03의 모든 설계열도 같은 배율을 받는다. 가중치를 고정한 실제 재적합에서는
beta(delta)=10^(−delta/5) beta(0)
가 성립한다. 따라서 d beta/d delta = −(ln10/5) beta이고 dipole/STF도 함께 변한다. 같은 35,970개 원천에서 직접 재적합하여 이 식을 8.6e−14 이하의 절대오차로 재현했다.

| 공통 delta_mu=±0.087 mag | R97에 보고된 구간 (반올림) | 실제 X 재적합, 가중치 고정 |
|---|---|---|
| R95 공분산 family의 H | [70.10,75.75] | [70.06211645,75.90724905] |
| R36 공분산 family의 H | [69.43,75.04] | [69.40116848,75.19115959] |

R95에서 STF5 변화의 norm은 0.11661–0.12137 km/s/Mpc로 나타난다. 원천 working weight까지 재계산했을 때도 H 양단은 [70.06511200,75.90382890]이다. 이 실험은 두 번째 단계의 공분산/GLS 결합을 유지했으며, 완전한 물리 posterior를 재추정한 것이 아니다. 그 제한 안에서도 현재의 'physical sharp calibration bound' 해석을 지지하지 못한다.

특히 균일 거리 스케일과 고정 가중치에서는 STF와 H가 함께 변하므로 q=||STF||/H는 불변이다. 이 실제 원천 변환과 R97의 frozen-design 가산모형을 한 설명에서 섞으면 안 된다.

최소 수정: physical distance-modulus perturbation, frozen-design residual approximation, working covariance sensitivity를 명시적으로 구분하고 실제 원천 변화의 Jacobian 또는 nonlinear refit을 사용한다. 기존 Woodbury/GLS와 대칭 양정치 검산은 그대로 재사용한다.

Tully et al.의 원문은 H0=74.6, 통계 ±0.8, 잠재 systematic 약 3 km/s/Mpc를 제시한다. 이를 modulus로 선형 환산한 약 0.087 mag는 민감도 규모 선택으로 사용할 수 있다. 이것 자체가 독립적으로 추정한 7채널 Gaussian calibration posterior는 아니다. 원문에 따로 등장하는 0.087 mag는 16개 TRGB–CPLR 비교의 rms다. [원 논문](https://arxiv.org/pdf/2209.11238).

## F4. P1 초과질량 상한의 명시적 반례

위치: `scripts/r97/phy_and_60node_synthesis.py:144–157`.
원래 P1 지표는 각 draw와 각 창의 q_j=||STF5_j||/H_j다. 그러나 R97은 4창을 결합한 9D GLS 추정량의 최대 STF 변화량을 고정 H0로 나눈 0.007380153988983002를 모든 창의 q에 똑같이 더한다. 창별 Jacobian도 분모 변화도 반영되지 않는다.

다음 단일 공통 nuisance 벡터는 원래 R97이 지정한 7D 타원체의 엄격한 내부점이다. 단위는 mag이며 채널 순서는 SNIa,FP,TFR,SBFm,SBFir,SNII,DirectCal이다.

```text
delta = [0.315481238721, 0.301087828206, 0.304561550799,
         0.305795937348, 0.308176649253, 0.321630403743,
         0.315480198825]
delta^T Sigma^(-1) delta = 14.064326442202892
chi2_7(0.95)             = 14.067140449340169
```

동일한 원래 2048개 draw에 창별 J7_ivw를 적용하고 비율을 다시 계산하면 세 번째 창의 q>0.05가 1972/2048=0.962890625이다. 저장된 upper bound는 1971/2048=0.96240234375다. 가장 가까운 양의 초과 여유도 3.46886546e−5여서 threshold roundoff 문제가 아니다. 타원체는 대칭이므로 nuisance 부호의 표기 선택은 반례의 존재에 영향을 주지 않는다.

이는 원래 가산 근사모형 안에서 성립하는 유한 반례다. F3의 물리적 원천 재보정과는 별도로 성립한다. 반례의 초과 크기는 전체 오류의 최대치가 아니며 진짜 최대 tail을 추정한 것도 아니다.

최소 수정: 현재 숫자를 uniform-width sensitivity로만 표시한다. 실제 bound는 공유 delta를 각 창의 signed 9-vector에 전파한 뒤 q를 계산해야 한다. 예를 들어 창별 분자 변화 norm<=bQ, |deltaH|<=bH이고 H>bH라면
max(0,||Q||−bQ)/(H+bH) <= q <= (||Q||+bQ)/(H−bH)
는 보수적 outer bound다. Sharpness를 원하면 각 창 및 공동 any/all 사건의 상관 nuisance 최적화가 추가로 필요하다. physical_Pi=None은 유지한다.

재현: `repro/cf4_p1.py`, 원출력 `outputs/cf4_p1.txt`.

## F5. CMB heldout의 feature-fit 누출 및 전처리 불일치

위치: `scripts/r97/cmb_injection_and_eb_leakage.py:497–516`.
E/B의 ell별 Gaunt 가중치를 300개 EE/BB 평균으로 먼저 추정한 뒤 150/150을 나눈다. 검정 하늘도 feature 가중치 적합에 참여한다. 또한 MC의 온도 monopole/dipole은 NSIDE64에서 적합했지만 관측의 primary cache는 NSIDE2048 적합이다. 관련 전처리는 `scripts/r95/stream_fullres_fast.py:235–242,327–330,390–399`, 선택은 `scripts/r96/cmb_crossfit_null.py:89–90`이다.

저장된 low-ell 계수와 masked monopole/dipole basis의 네 실수 모멘트로 NSIDE2048 OLS를 맞출 수 있었다. 원본 999개 FITS를 다시 처리하지 않았다. 관측의 64→2048 캐시 재구성 max error는 1.8494e−13, 교정된 MC 300개의 저차 모멘트 max는 2.7756e−17이다.

| 적합 방식, shrinkage=0.2 | raw tail rank | ridge tail rank |
|---|---:|---:|
| 원래 feature 가중치 300개 사용, 원래 전처리 | 26/151=0.17218543 | 26/151=0.17218543 |
| 가중치부터 train 150개만 사용 | 24/151=0.15894040 | 25/151=0.16556291 |
| train-only + 관측/MC 모두 NSIDE2048 OLS | 24/151=0.15894040 | 25/151=0.16556291 |

마지막 경우 Q_obs는 raw 91.69148333, ridge 92.68979765다. 이는 선택된 null, feature, shrinkage 아래의 heldout 순위다. 전역 유의성이나 Bianchi family의 확률로 해석하지 않는다. 현재의 비이상 진단 방향은 유지된다. 원래 데이터는 NSIDE2048이지만 분석된 조화계수는 ell<=48이며 independent noise는 300개다.

최소 수정: ID 분할을 가장 먼저 수행하고 weights, mean field, standardization, ridge, covariance 적합을 전부 train subset 안에 둔다. 양쪽 T 전처리를 일치시킨다. 캐시 재사용으로 이 수정은 가볍게 수행 가능하다.

## F6. MASTER의 이론·MC가 서로 다른 양을 비교했다

위치: `scripts/r97/cmb_injection_and_eb_leakage.py:546–568`.
이론은 각 ell에서 E[BB]/E[EE]를 계산하지만 MC는 E[BB/EE]를 계산한다. 둘은 유한 표본에서만 다른 것이 아니라 서로 다른 population estimand다.

실제 NSIDE2048 mask의 L<=96 모멘트로 band-limited 입력·출력 ell<=48을 투영했다. 동일 seed=9703의 8개 pure-E 하늘에서 기존 0.05398796을 저비용 NSIDE128 투영으로 0.05398806까지 재현했다. 같은 8개에서 평균 스펙트럼의 비를 사용하면 0.04854437이다. 이론은 0.04957597이다.

512개 NSIDE64 band-limited 검산에서는 비의 평균 0.05481970, 평균들의 비 0.04948492이고 후자의 근사 batch SE는 0.00025109다. 512개에는 최초 8개가 포함된다. 이 계산은 원래 band-limited pure-E mask operator를 지지하며, 원래 8.17%를 operator accuracy로 사용할 근거는 제공하지 않는다. 미포함 high-ell power, 실제 전파함수 또는 전체 편광 likelihood의 검증은 아니다.

최소 수정: ell별 평균 스펙트럼을 먼저 구한 뒤 같은 비율을 비교하고, MC 오차를 함께 보고한다. [masked BiPoSH 원 논문](https://arxiv.org/abs/1506.00550)은 마스크가 신호의 응답 자체를 바꾼다는 이론적 배경을 제공한다.

### ridge와 injection 해석도 한정해야 한다

R97의 train-only, matched-OLS heldout B 특징 총분산 비는 0.99597049다. 적합을 고정한 paired bootstrap(150개 홀수 sky, 1500 resamples, seed112296) 95% 구간은 [0.99100363,1.00063162]다. 따라서 약 0.4% 감소의 점추정이며 물리적 E→B 누설 제거량을 입증한 결과가 아니다.

주입은 a+sqrt(A)d를 넣고 같은 d에서 만든 template로 복원한다. 이차 통계량의 평균은 c0+c_cross sqrt(A)+A이다. 저장 여섯 점은 c0=−0.1641118518, c_cross=−0.1822811055, A 계수=1에 9.2e−16 이내로 일치한다. 따라서 선형회귀 기울기 0.9332285는 동일 150개 배경의 교차항을 포함한 유한 template 응답이다. 별도의 multiplicative synthetic sky 6개에서는 점수가 모두 증가했고 평균 86.03→202.90이므로 제한된 검출 민감도 실험은 남는다. 실제 Bianchi 진폭·축의 blind recovery로 승격할 근거는 없다.

재현: `repro/cmb_split_rank.py`, `repro/cmb_master_injection.py`와 대응 원출력.

## F7. CF4 covariance와 nuisance 차원의 가정

위치: `scripts/r97/cf4_genealogy_and_partial_id.py:434–436,457–492`.
여섯 velocity method의 SNIa 기준 상대보정은 rank5이고, 7채널 common mode를 추가하면 rank6이다. 1e−8 I를 넣은 뒤 rank7이 된다. 원래 overlap 모델에서 추정하지 않은 SNIa−DirectCal 대비는 ridge 이전에 0으로 고정되며, ridge 뒤 표준편차는 0.000141421 mag다. 이는 데이터가 그 대비를 매우 정확히 추정한 결과가 아니다.

R95의 동일 가정에서 95% H 반폭은 chi2_7을 사용하면 10.58648, ridge를 제외한 6차원 타원체로 계산하면 10.01587이다. 어느 차원을 채택할지는 nuisance의 실제 과학적 모형에 따라 결정해야 한다. 수치적 양정치화를 위해 넣은 ridge를 물리적 새 불확실성 차원처럼 해석해서는 안 된다. '1-sigma'라는 이름도 우선 r=1 Mahalanobis 경계라는 의미를 밝혀야 한다.

K4와 J7의 98.84868%는 binary 지원 S7에서 재현되며 IVW W7에서는 99.51353%다. 높은 trace 포함률은 두 모형의 동일성이나 calibration posterior 복원을 뜻하지 않는다. 최대 주각은 각각 63.55도와 69.27도다.

R36 원천 생성 스크립트 `docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-02-CF4-CORRELATED/run_correlated.py:234–249,277–296`에는 EH98 no-wiggle의 k=[0.005,0.02],[0.02,0.05] h/Mpc 대역, R=5/10/20 h^−1 Mpc, stipulated 150 km/s 독립 그룹 잡음, 0.4 km/s/Mpc 독립 4방법 오프셋이 명시돼 있다. 계보가 복원됐다는 성과는 유지되지만 전체 nonlinear PV+calibration covariance가 확보된 것은 아니다.

또한 네 Gaussian 창은 모두 동일 35,970개에 양의 가중치를 준다. Schur 예측은 상관된 window summary의 내부 일관성 검사이며 독립 원천 holdout이 아니다. 실제 바깥 중심은 z=0.06,0.08인데 출력 키 z055_z070는 수정이 필요하다.

## F8. Jacobi 조건과 긍정적 국소 수송 검증

위치: `scripts/r97/bianchi_coupled_m_transport.py:386–391,427–439`.
기존 4D ray oracle에서 a=(0.04,−0.02,0.03), n의 주어진 대칭행렬은
n a=(0.0011,0.0028,0.0006)
을 준다. normalized residual=0.52662671이므로 Bianchi Lie algebra의 Jacobi 조건을 만족하지 않는다. 공표된 약 1e−9의 일치는 임의 연결계수에 대한 국소 두 구현 비교로는 남지만 허용되는 Bianchi 배경의 물리 검증 수치로 인용하면 안 된다.

원래 함수의 입력 세 텐서만 메모리에서 R49의 admissible tilted VII_h state로 교체해 동일 검사를 실시했다. Jacobi=0, Hamiltonian residual=2.22e−16, Codazzi norm=1.42e−15였다. dN=1e−5 국소 ray 증분의 T/E/B 오차는 2.4084e−9,1.6730e−9,3.2368e−9로 기존 1e−8 기준을 만족했다. 따라서 각도 수송 연산자 자체를 새로 버릴 필요는 없다. 이는 한 admissible slice의 국소 검증이며 전체 시간 이력이나 collision까지 포함한 검증은 아니다.

재현: `repro/bianchi_ray_control.py`, `outputs/bianchi_ray_control.txt`.

## 실제로 확보된 기반과 남은 solver 범위

- CF4: 35,970개 원천 ID, 944개 다방법 그룹, 35,968개에서 DMzp−DMav=−0.147 mag, W7 partition of unity, R36 K4 생성식, Woodbury/GLS 구현을 재사용할 수 있다. R95/R36 기본 공분산 최소 고유값은 0.00382000/0.00189271이다.
- CMB: 기존 NSIDE2048→ell<=48 T/E/B cache와 masked harmonic basis, Gaunt projection을 그대로 사용했다. 새 대용량 FITS 캠페인 없이 split/preprocessing 결함을 정량화하고 교정 가능한 수치를 얻었다.
- Bianchi: sparse coupled-m 행렬, spin-2 projection, screen rotation, admissible VII_h local ray kernel은 유효한 부품이다. L=60은 m=−2..2만, all-m 실행은 L=8,12다.
- 광학 입력: R95가 쓰는 HyRec-2 Planck2018-like reference table과 선택한 tanh 재이온화·FLRW H(z)의 prescribed opacity는 추적 가능하다. 새로운 전역 비등방 recombination 계산을 실행한 것은 아니다.
- 배경 결합: R97은 N=0..2에서 얻은 R49 해의 끝점을 재규격화한다. redshift 원천에는 [(1+z)/1100]^−1/4를 곱하지만 광선 이류의 sigma/H는 고정한다. 같은 전단 이력을 두 항에 일관되게 적용하는 전체 배경 수송, electron/observer frame의 결합은 남아 있다. [Pontzen–Challinor](https://arxiv.org/abs/0706.2075)의 nearly-FRW 전달계층과 연결할 때도 가정과 전단 이력을 분리해야 한다.

소스 색인·archive 스캔의 파일 개수를 이론 검증 개수로 세지 않았다. 이번 검토는 R97이 의존하는 코드·계산·입력을 집중적으로 조사했고, 9만여 파일을 다시 전부 읽거나 원자료 전체를 재처리하지 않았다.

## 60노드 상태와 다음 실행

R78 SHA256은 90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11이며 60 nodes/129 edges/NEXT_ID=SQ-CF4가 유지됐다. R97 원장에는 22개 노드가 A/B/C 결과 파일을, 28개가 synthesis를, 10개가 R95 재사용 파일을 참조한다. 이는 원장 연결 방식이며 22개의 서로 다른 과학적 acceptance를 새로 통과했다는 뜻이 아니다. 기존 completed_scoped 18개도 그 제한된 범위에서만 유지된다. 새로운 original scientific acceptance는 없다.

local coding agent는 아래 순서로 한 번의 유한 수정 작업을 수행하면 된다.

1. 기존 signed sky convention을 고정하고 F1의 Thomson 부호를 각도구적으로 수정·검증한다.
2. sparse geometry를 유지한 채 시간 전파를 고치고, frozen exponential parity 다음에 시간·L·m 수렴을 따로 검사한다. admissible background를 oracle의 기본 입력으로 바꾼다.
3. CF4의 원천 modulus 변화에 따른 실제 fit/Jacobian을 구현하고, 공통 스케일의 beta 변환과 q 불변성 대조를 포함한다. DirectCal 대비와 sensitivity prior의 조건을 명시한다.
4. P1은 동일 nuisance를 4창 signed 9-vector에 전달해 비율을 재계산한다. 위 내부점 반례를 회귀검사로 남기고, 보수적 outer bound부터 확립한다.
5. CMB는 모든 feature 적합을 train-only로 이동하고 양쪽 monopole/dipole OLS를 맞춘다. 기존 cache를 재사용한다.
6. MASTER를 같은 estimand로 비교하고 ridge/injection 결과를 정확한 검증 범위로 보고한다. template ±쌍과 독립 recovery는 실제로 요구되는 물리량에 맞춰 추가한다.
7. 변경된 의존성의 검사만 재실행해 R97 결과의 후속 교정본을 생성한다. 원래 raw/legacy/R78와 독립 진단의 실패 증거는 보존하고, 다음에야 제약을 만족하는 시간변화 배경 전체와 all-m 확대를 진행한다.

## 재현과 보존

각 진단의 정확한 명령·소스/출력 SHA256은 `REVIEW_EVIDENCE.json`에 있다. 예:

```bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=. .venv/bin/python -B docs/research_program/observational_publication_20261015/R97_REVIEW_20261123/repro/cf4_p1.py
```

Python3.12.3 / NumPy2.5.4 / SciPy1.18.1 / healpy1.19.0을 관측했다. 원격 기기의 기존 raw data와 native cache를 사용하므로 이 진단 폴더만 다른 기기로 옮겼다고 데이터 없이 실행되는 것은 아니다. 새로운 dependency 설치는 하지 않았다. 기존 unrelated untracked 1084개는 보존 대상이다.

이 보고서의 판정은 도구 관측과 보존한 유한 계산에 근거한다. source provenance, numerical correctness, physical validity, original DAG acceptance는 각각 별도의 결론으로 유지했다.
