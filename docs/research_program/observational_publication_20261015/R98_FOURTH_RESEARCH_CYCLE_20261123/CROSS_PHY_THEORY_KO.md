# R98 교차 물리 경로 PHY01–07

부호 있는 관측 요약량 및 조건부 전방 계수를 입력으로 일곱 계산을 실행했다. 기준은 R97-REM 52fee3f277d715cdb982dfbe751fefac10513060와 R98의 각 생산자 산출물이다. CF4와 Gaia의 STF 계수, 전파원의 수밀도 쌍극자, 광자의 운동량 모멘트는 단위·좌표·관측 과정이 다르다. 개별 항목의 입력 및 결과는 CROSS_PHY_RESULTS.json에 수록했다.

| 경로 | 실제 입력과 계산 | 유한 범위에서 확인한 결과 | 물리적 추론에 남은 입력 |
|---|---|---|---|
| PHY01 | CF4 Table 3/4에서 일치하는 35,970개 그룹, R98의 보정속도·거리모듈러스·4개 가우시안 적색편이창. 각 창에서 monopole/dipole 4열에 STF 5열을 투영하고 관측 9열 적합 및 축소모형을 재적합 | STF 사중극 5계수를 모두 생략할 때 생기는 관측 로그 쌍극자 변화의 2-노름은 차례로 0.0037931, 0.0034986, 0.0159575, 0.0203485. 직접 재적합과의 최대 성분차 $2.78\times10^{-16}$ | 보정·selection의 공동 오차법칙, 거리–광학 응답 |
| PHY02 | 조건부 Bianchi L12 하늘의 부호 있는 복소 T 전 성분을 복원. 방향 온도로 양의 흑체 bolometric intensity를 만들고 방향 1차·2차 모멘트를 구적 | 32×64 대 40×80의 2차 모멘트 최대차 $1.89\times10^{-15}$. VI$_{-1/9}$의 $\|S-I_3/3\|_F=5.374\times10^{-4}$, $\lambda_{\min}(S-mm^T)=0.3330445$. FLRW의 $m$은 수치 0 | 관측 photon intensity, 정상계와 관측자 변환, 다른 물질종의 독립 flux |
| PHY03 | 5개 survey의 일정한 survey별 mask 아래 19개 flux cut. NB1 4계수 log-link가 예측한 정확한 전천 count dipole 및 누적 source count slope에서 조건부 boost 벡터를 계산 | 최대 working $\|\beta\|=0.0265580$. 19개 벡터 각각에서 $D^4$ 수치구적과 부호 있는 analytic $4\boldsymbol\beta/(3+\beta^2)$ 간 최대 거리 $2.95\times10^{-16}$ | 실제 spectral-index/selection, 공동 source covariance, 독립 frame 측정 |
| PHY04 | R69 tangent templates의 전천 E2/B2 Gram을 구적하고 Gaia CRF3 전체 1,614,173개, Quaia join 692,154개 중 적합 자격을 갖춘 634,233개가 참여한 실제 R98 10종 적합·48개 patch covariance를 사용 | 전천 평균 Gram $I_{10}/5$와의 최대차 $3.34\times10^{-16}$. 실제 weighted Fisher E/B 최대 교차상관은 샘플별 0.0322–0.0567. CRF3 전체와 각 적합의 10차원 차분 공분산을 160차원 joint block 및 leave-patch 차분 두 방식으로 복원, 최대차 $6.22\times10^{-15}\,(\mu{\rm as}/{\rm yr})^2$ | source별 systematics와 광학 응답, 거리 및 관측자 모델 |
| PHY05 | VI$_h$의 실제 초기 대수에서 $A_1$만 0.99, 1.00, 1.01배로 바꾸어 3×5 signed momentum map 구성. R49 covariant divergence와 R90 성분식 직접 비교 | $h=-0.108900,-1/9,-0.113344$에서 rank 3,2,3. 예외점 최소 특이값 $5.42\times10^{-20}$, 이웃은 $3.39,3.40\times10^{-6}$. R49 정상계 초기 flux를 넣은 Codazzi 잔차 $2.27\times10^{-22}$ | 독립적으로 측정한 종별 flux 및 shear/geometry와의 공동 오차 |
| PHY06 | I/V/VII$_h$/VI$_h$ 각각 $z_v=1600$에서 현재까지 실제 R49 161개 시점의 전단 텐서를 추적 | VII$_h$와 VI$_h$에서 초기 대비 상위 고유선 최대각 80.57°, 89.79°. 정규화 전단 교환자 최대 0.39087, 0.46836. 더 엄격한 IVP 허용오차에서 두 해 고유선 간 최대차 $6.95\times10^{-5}$°, $2.57\times10^{-6}$° | 교란·frame/observer 광학변환 및 관측 가능한 transport law |
| PHY07 | CF4의 9열 로그모형에 $100\,{\rm Mpc}\,\hat{\boldsymbol n}/r$ 3열을 더하고 같은 4개 창에서 12차원 적합. 각 survey 창의 실제 거리구간과 $r=100$ Mpc 고정 반례를 계산 | 모든 창의 정규화 Gram rank는 실제 12, 고정거리 9. 관측 working weighted RSS 감소 8.3223, 12.6364, 19.4595, 15.3060. 생략항 항등식 최대차 $9.64\times10^{-17}$ | 실제 거리–특이속도 상관, selection 및 독립 관측자 운동 prior |

## 유도와 해석

**PHY01/07.** $y=\log(v_{\rm corrected}/H_{\rm ref})-(\ln10/5)(\mu-25)$이고 $X_4=[1,\hat n_i]$, $M_5=[\hat n^iE^a_{ij}\hat n^j]$, $X_9=[X_4,M_5]$. 각 창의 R98 고정 가중치 $W$에서 $L=(X_4^TWX_4)^{-1}X_4^TWM_5$이므로 $\hat b_{4,\rm reduced}-\hat b_{4,\rm joint}=L\hat b_5$. 구현은 가중 최소제곱으로 계산한다. PHY07도 $X_9$와 $U=100\,{\rm Mpc}\,\hat n/r$를 넣은 같은 항등식이다. $r=cz_{\rm CMB}/(70\,{\rm km\,s^{-1}\,Mpc^{-1}})$는 이 비교에서 선택한 저적색편이 거리 좌표다. 실제 로그거리지수 적합의 기준 $H_{\rm ref}=74.6$과 역할을 구분한다. 이 창의 표본 중복 때문에 네 RSS 차이를 합쳐 검정하지 않는다.

**PHY02/03.** 하늘 도래방향을 $\hat n$, 광자 진행방향을 $-\hat n$으로 둔다. $m=\langle\hat n I\rangle/\langle I\rangle$와 $S=\langle\hat n\hat n^T I\rangle/\langle I\rangle$를 쓰면 임의 $u$에 대해 $u^T(S-mm^T)u={\rm Var}_I(u\cdot\hat n)\ge0$이다. R98 선형 시험장 $T$에 $I/I_0=(1+T)^4$를 적용한 흑체 후처리는 선택한 강도 복원식이다. 광자 운동량 방향의 부호는 $-m$이다. 흑체 boost에서는 $D=[\gamma(1-\boldsymbol\beta\cdot\hat n)]^{-1}$이고 방사 유체의 boost된 에너지와 운동량 성분의 비 또는 $D^4$의 직접 적분이 $4\boldsymbol\beta/(3+\beta^2)$를 준다. 전파원 자료에 대해서만 $x=-d\ln N(>S_\nu)/d\ln S_\nu$의 수치기울기와 $\alpha=0.75$를 고정해 $\boldsymbol\beta_{\rm work}=\boldsymbol d/[2+x(1+\alpha)]$를 썼다. 기울기는 끝점에서 한쪽 차분이다. 이 count law는 1차 운동학 근사이고 별도로 대조한 흑체 변환은 유한 boost 항등식이다. [Ellis & Baldwin (1984)](https://doi.org/10.1093/mnras/206.2.377).

동일 R98 CMB 캐시의 신호–잡음 조합 999개, 고유 잡음 300개에 대해 held-out ridge-minus-raw NLL 차를 다시 묶었다. 잡음군 균등 평균은 0.0315871 nat, pair 균등 평균은 0.0318312 nat였다. 이는 실제 grouped prediction 목적함수의 측도 의존성을 보여 준다. 오염성분·mask·단위·측정 연산자가 다르므로 이 목적함수로 조건부 photon 모멘트의 관측 불확실성을 보정하지 않았다.

**PHY04/05.** STF 기저 $E^a:E^b=\delta^{ab}$에서 접벡터 장은 $P_n E^a\hat n$와 $\hat n\times E^a\hat n$이다. 등방 2차·4차 구면모멘트를 수축하면 두 대각블록은 $\delta^{ab}/5$, 교차블록은 구면 반전 홀짝성으로 0이다. 관측에서는 상관된 pmra*/pmdec 가중치와 선택함수가 이 Gram을 바꾼다. R49의 부호 있는 momentum map은 $\kappa q_i=-(D_j\sigma^j{}_i)$이다. R90의 STF 성분행렬을 같은 $a,n$에 그대로 대입하면 최대 원소차가 0.00212132이고, 이 chart의 VER2 $n$을 R90 식에서 $-n$으로 변환하면 세 지점 모두 $5.43\times10^{-20}$ 이내로 일치한다. Rank 검사는 부호 오류에 둔감하다. 과거 oriented witness나 signed flux를 재사용할 때는 대수의 기하적 정의, tetrad orientation, 이 부호 변환을 먼저 맞춰야 한다. 원본은 보존했다. [Mignard & Klioner (2012)](https://arxiv.org/abs/1207.0025) · [Pontzen & Challinor (2007)](https://arxiv.org/html/0706.2075v2).

**PHY06.** $\hat S=(\sigma/H)/\|\sigma/H\|_F$, $\chi=\sqrt6\,{\rm tr}\hat S^3$, $J(N)=\|[\hat S(N_i),\hat S(N)]\|_F$. 공통 rigid rotation은 $\chi$를 보존하며 최대 오차는 $8.89\times10^{-16}$였다. 실제 궤적에서는 $\chi$ 자체도 변한다. 예컨대 VII$_h$에서 −0.98463부터 0.92445까지이다. 큰 고유선 회전각의 경우 전단 절대진폭도 함께 봐야 한다. VII$_h$의 최소 $\|\sigma/H\|$는 $4.38\times10^{-10}$이며, 161개 표본에서 정규화한 상위 고유값 gap은 항상 0.0827 이상이었다. 고유선 각도는 $\cos^{-1}|\boldsymbol e_{\max}(N)\cdot\boldsymbol e_{\max}(N_i)|$로 부호를 제거했다. 같은 점을 두 tolerance로 풀어 수치 민감도를 따로 기록했다.

## 재실행과 판정

실행 파일은 scripts/r98/cross_phy.py, 회귀검사는 tests/obsstat/test_r98_cross_phy.py다. canonical R98 생산자의 다섯 JSON, CF4 원본과 선택표, solver·기저의 SHA-256은 결과에 저장했다. Gaia patch cache는 생산자가 고정한 SHA-256으로 재확인했다. 7.73초의 실제 실행 및 결과 전체는 CROSS_PHY_RESULTS.json에 있다.

~~~bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
.venv/bin/python -B -m scripts.r98.cross_phy --output "$HOME/Downloads/CROSS_PHY_R98_replay.json"
.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/obsstat/test_r98_cross_phy.py
~~~

이 실행의 범위는 일곱 경로의 유한 계산과 자료 조건부 모형 비교다. 공통 물리 body, null, 측도 또는 수송법칙이 주어질 때까지 물리적 $Q,\Pi,F,G_F$는 미정이다. R78의 원래 node 수용문구와 개별 출판 gate는 상위 결정에 남겨 두었다.

## C9: 두 시각의 프레임과 표본 극값

PHY06의 각도와 commutator는 같은 geodesic normal을 따라 Fermi–Walker 수송한 R49 삼각틀에서 두 시각의 전단을 비교한다. 시간 의존 프레임 회전을 가하면 두 시각 사이의 수송 사상을 함께 삽입해야 한다. 실제 VIIh 성분을 순간 고유틀로 회전한 뒤 단순 비교하면 80.57°를 거의 0°로 만들 수 있지만, 그 수송을 포함한 비교에서는 원래 각도가 복원된다. 한 시각의 고유값·정규화 gap은 회전 불변이다. 이 고유선 회전으로 물리적 vorticity 또는 G_F를 추론하지 않는다.

원래 표의 최대각은 161개 시점에서의 표본 최대값이다. 독립 검산에서 VIh를 641개 시점으로 세분하면 89.787233°에서 89.970396°로 바뀌며, 최소 정규화 gap은 0.045389에서 0.042607로 바뀐다. 따라서 IVP 허용오차 안정성과 연속시간 최대각의 수렴을 구분한다. 상세한 독립 접속 유도, frame-rotation witness 및 양의 강도 모멘트 재구성은 review/cross_phy_independent.py와 review/CROSS_PHY_C9.json에 있다.
