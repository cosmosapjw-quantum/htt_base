# Doi–Peliti–Mori–Zwanzig의 비시간 변수 응답 연구

**작성일:** 2026-11-23  
**연구 기준:** HTT `f8931fbef075d55c2c2a3caee8b8f5db5174b16b`  
**범위:** 통계적·물리적 매개변수를 진화 지표로 사용하는 구성, 직접 유도, 유한 판별 계산, 기존 R100 자료에서의 응답 계산. Git stage/commit/push는 수행하지 않았다.

## 핵심 결과

이번 연구에서는 DP와 MZ의 진화 변수를 물리적 시간 밖으로 확장하는 세 경로를 실제로 구성했다. 선택 문턱·누적 노출량에는 확률보존 count 생성자를, 분포 변형에는 정규화까지 포함한 Feynman–Kac 흐름과 score 응답을, 해상도 변화에는 구면 열핵 흐름과 정확한 MZ 기억항을 적용했다. 물리 모형의 source parameter와 관측 적색편이에 대해서도 기존 optical solver를 재사용할 tangent/event 미분식을 유도했다.

새 계산은 두 종류다. 유한 모형에서는 생성자·기억항·정규화·초기조건의 역할을 독립적인 표현으로 검산했다. 실제 프로젝트에서는 R100의 5개 전파 조사·19개 flux cut과 CF4 36차원 공분산을 읽어 새로운 유한 응답을 계산했다. 후자는 기존 자료를 재사용한 조건부 민감도 분석이며 새로운 관측 calibration을 뜻하지 않는다.

가장 유용한 결론은 **같은 자료를 관측 조건·해상도·통계법칙에 따라 연결하고, 그 변화에 대한 응답을 연구의 기본 객체로 삼을 수 있다**는 것이다. 단변량 법칙의 민감도는 score로, 동일 표본을 공유하는 경로는 DP로, 선택한 저차 상태 밖의 영향은 MZ 또는 충분상태 확장으로 계산한다.

## 1. 어떤 변수가 무엇을 변화시키는가

| 변수 | 변화시키는 객체 | 계산에 사용할 식 | 현재 연결 대상 |
|---|---|---|---|
| \(s=\log(S_{\min}/S_\star)\) | 같은 catalogue의 nested selection | pure-death DP 생성자, 공동 mark likelihood | 전파 source counts, CF4 selection |
| 누적 유효 노출량 \(u\) | 조건부 독립 증가량의 count law | Gamma–Poisson predictive birth 생성자 | count/exposure, NB2 모형 |
| 구면 smoothing scale \(\tau\) | 같은 하늘의 관측 해상도 | 열핵 semigroup, MZ 축약 | low-\(\ell\), beam/mask, Gaia/radio |
| likelihood power·covariance weight \(s,\alpha\) | 통계적 가중 법칙 | score response, Feynman–Kac, 분포 공간 흐름 | 5변수 pushforward, CF4 |
| source amplitude·boost·곡률 모수 \(\alpha\) | 물리 해와 관측 연산자 | tangent equation와 endpoint 미분 | Bianchi optical transfer, Gaia+CF4 |
| affine distance·\(N=\log a\)·\(\log(1+z)\) | 이미 정의한 경로의 매개화 | Jacobian이 포함된 생성자·기억항 변환 | 광선·깊이 응답 |

통계적 진행 지표가 물리적 시간일 필요가 없다는 점은 순차 Monte Carlo 원전에도 명확하다. Del Moral–Doucet–Jasra는 공통 공간 위의 분포열, 인공적인 중간 분포, 정규화 상수와 경로 coupling을 다룬다.[1] 여기서는 그 관점을 실제 DP/MZ 연산자와 프로젝트의 관측량에 연결했다.

각 흐름에는 최소한 변수의 단위, full state 또는 law, 초기조건, 관측 map, 서로 다른 매개변수 값 사이의 coupling이 명시되어야 한다. 단일 parameter의 주변분포만으로도 기대값의 국소 응답은 계산할 수 있지만, cross-parameter covariance와 기억항을 계산하려면 경로 구조가 추가로 필요하다.

## 2. 공통 응답 공식: 관측량 변화와 법칙 변화

공통 기준 측도에 대한 밀도 \(p_s\)와 관측량 \(A_s\)를 두자. 미분·적분 교환이 가능한 국소 지배조건과 정칙성을 가정한다. score를

\[
\mathcal S_s=\partial_s\log p_s,\qquad E_s\mathcal S_s=0
\]

로 정의하면

\[
\boxed{
\frac{d}{ds}E_s[A_s]
=E_s[\partial_s A_s]
+\operatorname{Cov}_s(A_s,\mathcal S_s).
}
\tag{1}
\]

증명은 \(E_s A_s=\int A_s p_s\,d\mu\)를 직접 미분하고, \(\partial_s p_s=p_s\mathcal S_s\)와 정규화를 적용하면 된다. 첫 항은 물리 해·관측 연산자·event 자체의 변화이며, 둘째 항은 법칙 또는 가중치의 변화다. 두 항의 단위는 모두 \([A]/[s]\)다. likelihood-ratio/score 방법의 원전 근거는 Glynn의 식 (3.1), (3.6)–(3.7)이다.[2]

또한

\[
\left|
\frac{dE_sA_s}{ds}-E_s\partial_s A_s
\right|
\le\sqrt{\operatorname{Var}_s(A_s)\,I_s},
\qquad I_s=E_s[\mathcal S_s^2].
\tag{2}
\]

이는 관측량과 법칙 변화 방향 사이의 결합을 정량화한다. 여러 nuisance parameter 중 목표 통계에 실제로 영향을 주는 방향을 고르는 데 유용하다. 새로운 posterior나 물리적 참값을 자동으로 만들어 주지는 않는다.

### 2.1 물리적 변수의 예

정준분포에서 \(\beta=1/(k_B T)\), 고정 에너지 함수 \(E\)를 쓰면

\[
\partial_\beta\langle A\rangle_\beta
=-\operatorname{Cov}_\beta(A,E),
\qquad
\partial_T\langle A\rangle_T
=\frac{\operatorname{Cov}_T(A,E)}{k_BT^2}.
\]

따라서 고정 부피에서는 \(C_V=\operatorname{Var}(E)/(k_BT^2)\)다. \(A\)나 Hamiltonian이 온도에 직접 의존하면 식 (1)의 직접 미분 및 해당 score 항을 포함한다. 이 예에서는 \(\beta\)의 단위가 에너지의 역수다. 이번 구성은 자연단위 채택을 요구하지 않는다.

## 3. 분포 변형을 DP와 MZ로 연결하기

### 3.1 정규화된 비선형 흐름과 선형 Feynman–Kac 표현

고정 함수 \(\ell(\omega)\)에 대해

\[
w_s=e^{s\ell}p_0,\quad
Z_s=\int w_s\,d\mu,\quad
p_s=\frac{w_s}{Z_s}
\]

를 정의한다. \(0<Z_s<\infty\)인 구간에서

\[
w_s'=\ell w_s,\qquad
p_s'=(\ell-\langle\ell\rangle_s)p_s,
\]
\[
(\log Z_s)'=\langle\ell\rangle_s,\qquad
(\log Z_s)''=\operatorname{Var}_s(\ell).
\tag{3}
\]

정규화 map \(\Phi_s(p)=e^{s\ell}p/\int e^{s\ell}p\)는 정의역에서
\(\Phi_s\circ\Phi_u=\Phi_{s+u}\)를 만족한다. 따라서 분포 자체가 실제 비선형 흐름을 이룬다.

비정규화 가중치의 선형 표현은 Feynman–Kac potential evolution이다. 일반적으로 \(w'=L_s^*w+V_sw\)라면
\(p'=L_s^*p+(V_s-E_sV_s)p\)다. 정규화 상수를 포함한 선형 상태에 MZ를 적용한 뒤 비율을 취하거나, 충분한 정규화된 moment를 유지하는 두 방법을 비교할 수 있다.[3]

### 3.2 확률보존 DP selection 과정

유형 \(i\)의 potential이 \(\ell_i\), 총 입자수가 \(N\)일 때

\[
X_i+X_j\longrightarrow2X_i,\qquad
r_{ij}=\frac{n_in_j}{N}(\ell_i-\ell_j)_+
\]

를 정의할 수 있다. 총수 \(N\)을 보존하는 정상정렬 생성자는

\[
\mathcal L_N
=\frac1N\sum_{i\ne j}(\ell_i-\ell_j)_+
\big[(a_i^\dagger)^2-a_i^\dagger a_j^\dagger\big]a_ia_j.
\tag{4}
\]

여기서는 \(\partial_s|P\rangle=\mathcal L|P\rangle\),
\(a|n\rangle=n|n-1\rangle\) convention을 쓴다.[4]
관측량에 작용하는 backward dual \(\mathcal A_N=\mathcal L_N^\top\)에 대해
\(f_i=n_i/N\)의 drift는 \(p_i(\ell_i-\bar\ell)\)다.

그러나 유한 \(N\)의 평균에는 \(E[p_i\bar\ell]\)가 나타난다. 따라서 유한 입자계의 기대값과 결정론적 normalized tilt를 동일시하지 않는다. \(N=20,40,80\)의 전체 유한 master matrix를 실제로 계산하여 그 차이를 아래에서 계측했다.

### 3.3 통계 매개변수에 대한 정확한 MZ 예제

무차원
\[
\ell=(-1,0,2),\qquad p_0=(0.2,0.5,0.3),\qquad0\le s\le1
\]
을 택했다. 그러면
\[
Z(s)=0.2e^{-s}+0.5+0.3e^{2s}.
\]

\(m_j=Z^{(j)}\)로 두면 점별 항등식 \(\ell^3=\ell^2+2\ell\)에 의해

\[
m_0'=m_1,\qquad m_1'=m_2,\qquad m_2'=2m_1+m_2,
\quad(m_0,m_1,m_2)_0=(1,0.4,1.4).
\tag{5}
\]

\(m_2\)를 제거하면

\[
\boxed{
m_1'(s)=1.4e^s+
2\int_0^s e^{s-u}m_1(u)\,du,
\qquad m_0'=m_1.
}
\tag{6}
\]

기억항은 통계 매개변수 \(s\)에 대한 것이며, 비정규화 weight 공간에서는 커질 수 있다. 그 사실은 \(p_s\)의 정상적인 정규화와 모순되지 않는다.

또 다른 상태를 선택하면 convolution 없이 닫힌다. \(m=\langle\ell\rangle_s\), \(v=\operatorname{Var}_s\ell\)에 대해

\[
m'=v,\qquad
v'=(1-3m)v-m^3+m^2+2m
\tag{7}
\]

가 정확하다. 이 결과는 세 점 support의 다항식 관계를 사용하며, 일반 연속분포에 대한 보편 closure를 주장하지 않는다.

실제 계산에서 \(s=1\)의 값은

| 계산 | \(\langle\ell\rangle_1\) |
|---|---:|
| 직접 정규화된 유한 합 | 1.562509102767 |
| 기억항을 제거하고 초기 force만 유지 | 1.166279059106 |
| 기억항·초기 force 모두 제거 | 0.285714285714 |

전체 matrix exponential·Volterra realization·직접 가중합의 최대 차이는 \(1.54\times10^{-11}\) 이하였고, 정규화된 2변수 ODE의 평균 오차는 \(2.24\times10^{-12}\) 이하였다. event \(\ell=2\)의 확률은 \(0.3\to0.7944388112\), \(s=1\)에서 응답은 \(0.3475597483\)이었다.

식 (4)의 유한 입자계와 결정론적 tilt 사이의 \(L^1\) 차이는 \(N=20,40,80\)에서 각각 \(0.0348537,0.0177026,0.00891443\)이었다. 이 수치는 유한 입자 효과를 보인 실행 결과이며, 세 값만으로 일반 수렴정리를 증명한 것은 아니다.

## 4. DP: flux cut과 exposure를 진화 변수로 사용

### 4.1 동일 catalogue의 nested threshold 과정

baseline \(S_\star\) 이상에서 선택한 모집단을 고정하고

\[
s=\log(S_{\min}/S_\star),\quad
q(s)=P(S\ge S_\star e^s\mid S\ge S_\star),\quad
h(s)=-\partial_s\log q(s)
\]

를 둔다. \(q>0\), 절대연속·비증가이며, \(N_0\)로 조건화한 표지가 같은 \(q\)를 갖는 iid이고 그 \(q\)가 \(N_0\)에 의존하지 않는다고 가정한다. 측정 flux는 한 번 부여한 뒤 고정한다.

각 객체의 생존 hazard가 \(h(s)\)이므로

\[
\boxed{\mathcal L_s=h(s)(1-a^\dagger)a},
\qquad
\partial_sG=h(s)(1-z)\partial_zG,
\]
\[
G_s(z)=G_0(1-q+qz),\qquad
N_{s_2}\mid N_{s_1}=n
\sim\operatorname{Binomial}\!\left(n,\frac{q(s_2)}{q(s_1)}\right).
\tag{8}
\]

이는 실제 천체 소멸을 의미하지 않는다. 문턱을 올릴 때 관측 목록에서 빠지는 객체를 나타낸다. marking/thinning의 원전 근거는 Last–Penrose다.[5]

\(E N_0=m_0\), \(\operatorname{Var}N_0=v_0\)일 때 total covariance로

\[
\boxed{
\operatorname{Cov}(N_s,N_t)
=m_0\min(q_s,q_t)+(v_0-m_0)q_sq_t.
}
\tag{9}
\]

여러 flux cut의 독립성 대신 동일 객체의 공유 구조가 들어간다. count-space 행렬과 binomial PMF의 최대 차이는 \(2.78\times10^{-16}\)였고, 뒤쪽 cut의 count가 앞쪽보다 큰 불가능한 joint mass는 0이었다.

### 4.2 실제 19개 cut의 새 응답

R100의 고정 support별 count와 fitted signed dipole vector를 재사용해

\[
\bar h_{ij}
=-\frac{\log(N_j/N_i)}{\log(S_j/S_i)},\qquad
\overline{\mathcal R}_{ij}\boldsymbol x
=\frac{\boldsymbol x_j-\boldsymbol x_i}{\log(S_j/S_i)}
\tag{10}
\]

를 계산했다. 이는 구간 secant이며, 무한소 미분이나 새 유의성 판정이 아니다. 원 코드의 survey별 고정 mask는 확인했지만, 집계 count의 단조성만으로 object-ID nesting이나 모든 per-cell 차분의 비음수성까지 검증한 것은 아니다. 이 검증은 공동 likelihood 구현에 포함한다.

| 조사 | cut (mJy) | 인접 구간 \(\bar h\) |
|---|---|---|
| NVSS | 15,20,30,50 | 0.866611, 0.927138, 1.007157 |
| RACS DR1 | 15,20,30,50,100 | 0.831152, 0.873270, 0.942955, 1.050891 |
| SPICE RACS | 20,30,50 | 0.864691, 0.940459 |
| SUMSS | 15,20,30,50 | 0.821255, 0.866863, 0.926381 |
| LoTSS legacy966 | 20,50,100 | 0.720341, 0.796455 |

NB1-MLE와 NB2 각각 14개 구간의 signed 3성분 응답을 저장했다. NVSS 15→20 mJy의 NB1 응답은

\[
(-0.00957699,-0.00115896,-0.01747447)
\]

per unit log-cut이다. NVSS의 세 번째 fitted 성분은 15→50 mJy에서
\(0.01593935\to-0.00547248\)로 바뀐다. 따라서 진폭만 추적하면 성분의 부호 변화와 방향 변화를 잃는다. 이 변화의 물리적 원인과 유의성은 공동 law를 통한 후속 분석 대상이다.

### 4.3 baseline 조건부 likelihood가 제거하는 blocker

\(M_j=N_j-N_{j+1}\), \(M_J=N_J\)라는 비중복 count를 만들면

\[
(M_0,\ldots,M_J)\mid N_0
\sim\operatorname{Multinomial}
\bigl(N_0;q_0-q_1,\ldots,q_{J-1}-q_J,q_J\bigr).
\tag{11}
\]

Gamma intensity를 추가한 경우에도 categorical mark law가 latent intensity와 독립이면 baseline count로 조건화한 뒤 같은 식이 남는다. 사실 식 (11) 자체에는 Gamma 가정이 필요 없다.

이 방식으로 현재 선택된 baseline 내부의 flux-shape 응답은 진행할 수 있다. baseline 아래 누락 모집단이나 절대 완전도는 복원되지 않는다. 위치·종류·강도에 따른 mark 의존성은 층화 또는 joint model로 다뤄야 한다. numerical factorization의 log-likelihood 오차는 \(8.88\times10^{-16}\)였다.

### 4.4 누적 노출량의 정확한 predictive DP 생성자

\[
\Lambda\sim\operatorname{Gamma}(r,b),\quad
N(u)\mid\Lambda\sim\operatorname{Poisson}(\Lambda u)
\]

에서 같은 homogeneous \(\Lambda\)를 공유하는 조건부 독립 증가량을 가정한다. \(b\)는 rate convention이며 \([\Lambda]=[u]^{-1}\), \([b]=[u]\)다. 관측 경로의 likelihood에서 \(\Lambda\) 의존 부분은 \(\Lambda^{N(u)}e^{-\Lambda u}\)이므로

\[
\Lambda\mid\mathcal F_u^N\sim\operatorname{Gamma}(r+N(u),b+u).
\]

따라서 정확한 predictive rate와 생성자는

\[
\lambda_{\rm pred}(n,u)=\frac{r+n}{b+u},
\]
\[
\boxed{
\mathcal L_u
=\frac r{b+u}(a^\dagger-1)
+\frac{(a^\dagger)^2-a^\dagger}{b+u}\,a.
}
\tag{12}
\]

\(\tau=\log(1+u/b)\)에서는 생성자가 일정하다. PGF와 두 지점 공분산은

\[
G_u(z)=\left[\frac b{b+u(1-z)}\right]^r,
\]
\[
\operatorname{Cov}(N(u),N(v))
=\frac rb\min(u,v)+\frac r{b^2}uv.
\tag{13}
\]

정적 latent intensity를 적분 제거했는데도 count+exposure가 충분상태여서 정확한 비균질 Markov 과정이 된다. **숨은 변수가 있다는 이유만으로 기억항이 필수인 것은 아니다.** Poisson–Gamma conjugacy의 일반 원전은 Rafler이며, 여기의 공통 scalar intensity 경로는 별도로 직접 유도했다.[6]

\((r,b,u,v)=(4,2,2,4)\)에서 행렬 PMF와 NB PMF 차이는 \(1.53\times10^{-16}\), 두 방식의 joint law 차이는 \(1.35\times10^{-16}\), covariance는 \(11.999999999999837\) 대 해석값 12였다. 공간적으로 변하는 일반 Cox law에 자동 확장한 결과는 아니다.

## 5. MZ: 해상도 변화의 기억항

정의된 full flow를

\[
y'=A_sy+B_sv,\qquad v'=C_sy+D_sv
\]

로 분리하자. \(\partial_sU_D(s,u)=D_sU_D(s,u)\), \(U_D(u,u)=I\)이면 variation of constants에서

\[
\boxed{
y'(s)=A_sy(s)+B_sU_D(s,s_0)v_0
+\int_{s_0}^sB_sU_D(s,u)C_uy(u)\,du.
}
\tag{14}
\]

이 유한 차원 항등식은 평형·물리적 시간·백색잡음 가정을 사용하지 않는다. 초기 hidden state가 확률변수라면 그 조건부 법칙이 force의 통계를 정한다. 투영과 기억의 일반 원전은 Chorin–Hald–Kupferman이다.[7]

### 5.1 구면 scale 흐름

단위구면에서

\[
\partial_\tau x=\frac12\Delta_{S^2}x,\qquad
a_{\ell m}(\tau)=e^{-\ell(\ell+1)\tau/2}a_{\ell m}(0)
\tag{15}
\]

를 정의했다. \(\tau\)는 단위구면에서 무차원이며 관습적으로 radian squared로 해석할 수 있다. 열핵 smoothing을 연속 적용하면 \(\tau\)가 더해진다. Bülow의 식 (28)과 semigroup 설명이 원전 근거다.[8]

전천구 harmonic coefficient의 고정 부분집합은 닫혀 있으므로 memory가 0이다. 선형 관측 \(y=Mx\)가 모든 full state에서 닫히는 조건은

\[
ML=A_{\rm obs}M
\tag{16}
\]

인 \(A_{\rm obs}\)가 존재하는 것이다. 관측 mask와 mode mixing이 이 조건을 깨면 보완 상태가 필요하다.

\(\ell=1,2\)의 두 mode를 섞어 \(y=x_1+x_2\), \(v=x_1-x_2\)라 두면

\[
y'=-2y+v,\qquad v'=y-2v,
\]
\[
\boxed{
y'=-2y+e^{-2\tau}v_0+
\int_0^\tau e^{-2(\tau-u)}y(u)\,du.
}
\tag{17}
\]

따라서 물리적 시간과 연결하지 않고도 해상도 memory가 실제로 생긴다.

\(x_0=(1,1/2)\)에서 \(\tau=1\)의 정확한 값은 \(0.392772975355\)였다. spectrum과 Volterra 계산의 최대 차이는 \(1.65\times10^{-12}\). 초기 force를 제거하면 −20.2466%, \(v\simeq y/2\)라는 heuristic local closure를 쓰면 −14.7866% 상대오차가 생겼다. 이 두 mode는 점근적 scale separation을 제공하지 않으므로 후자는 controlled approximation으로 표시하지 않았다.

### 5.2 동일한 smoothing에서도 tail 응답은 정의에 따라 달라진다

초기 두 mode가 독립 \(N(0,1)\)인 law를 선언하면

\[
V_\tau=e^{-2\tau}+e^{-6\tau}.
\]

고정 threshold 1을 넘는 확률은 \(\tau=0\)에서 \(0.479500\), \(\tau=1\)에서 \(0.00706584\)다. threshold를 \(\sqrt{V_\tau}\)와 함께 운반하면 모든 scale에서 \(0.3173105\)다. 따라서 body, 관측량, law 중 무엇을 고정하는지 명시해야 \(\Pi\) 응답이 정해진다.

또한 signed mixed carrier의 절댓값은 field 전체의 smoothing contraction을 그대로 따르지 않는다. \(x_0=(1,-2)\)이면 \(y=e^{-\tau}-2e^{-3\tau}\)는 \(\log2/2\)에서 0을 지나 다시 증가한다. 임의의 scalar gauge·occupancy의 단조성을 자동으로 가정하지 않는 이유다.

## 6. 경로 재매개화와 물리 모수의 관측 응답

### 6.1 두 Jacobian이 필요한 기억항 변환

이미 정의된 경로 \(t=t(s)\), \(g=dt/ds\)에서는

\[
A_s^{(s)}=g(s)A_{t(s)}^{(t)},\qquad
\eta_s^{(s)}=g(s)\eta_{t(s)}^{(t)},
\]
\[
\boxed{
K^{(s)}(s,u)=g(s)g(u)K^{(t)}(t(s),t(u)).
}
\tag{18}
\]

\([A_s]=[s]^{-1}\), \([K_s]=[s]^{-2}\)로 차원도 일치한다. \(t=e^s-1\) 예제의 올바른 잔차는 \(3.89\times10^{-16}\), 적분 안쪽 Jacobian을 생략하면 \(0.211446\)이었다.

이동 좌표 \(z=T(s)x\)에서는
\[
\widetilde L=T L T^{-1}+T'T^{-1}
\tag{19}
\]
를 써야 한다. moving-frame 예제에서 connection을 포함한 오차는 \(9.60\times10^{-13}\), 생략하면 \(0.071994\)였다.

### 6.2 실제 R100 optical solver와 연결

기존 `htt/bass/transport/position_drift_optics.py`는 \(N=\log a\)에 대한 22-state ray ODE와 관측 redshift에 맞는 emission root를 사용한다. 모형 parameter \(\alpha\)에 대해

\[
Y_N=f(N,Y,\alpha),\qquad
V_N=f_YV+f_\alpha,\quad V=\partial_\alpha Y|_N.
\tag{20}
\]

emission event를

\[
h=\log E+\log(D_e/D_o)-\log(1+z_{\rm target}(\alpha))=0
\]

로 두면

\[
N_{e,\alpha}
=-\frac{h_\alpha+h_YV}{h_N+h_Yf},
\]
\[
\boxed{
\frac{dO_e}{d\alpha}
=O_\alpha+O_YV+(O_N+O_Yf)N_{e,\alpha}.
}
\tag{21}
\]

\(C^1\) 정칙성, 단일 branch, \(h_N+h_Yf\ne0\)의 transversality가 필요하다. observer endpoint도 변하면 \(V(N_o)=Y_o'-f_oN_o'\)가 된다.

고정 적분 좌표에서의 미분과 고정 관측 redshift에서의 미분은 다르다. 간단한 exact event 예제에서 올바른 derivative는 −0.25였지만 endpoint를 고정하면 +0.5로 부호까지 달라졌다. **식 (20)–(21)의 production tangent 구현은 이번 연구에서 유도·소스 연결까지 완료했고, 기존 22-state solver에 추가하는 작업은 후속 구현이다.**

## 7. 실제 CF4 covariance continuation 계산

R100의 동일한 관측벡터 \(b=\mathrm{vec}(b_{\rm published,4\times9})\)를 고정하고

\[
C(\alpha)=C_{\rm inherited}
+\alpha(C_{\rm full\,k}-C_{\rm inherited}),\quad0\le\alpha\le1
\]

을 정의했다. \(\Delta C=C_{\rm full\,k}-C_{\rm inherited}\)라 하면

\[
T=b^\top C^{-1}b,\qquad
T'=-v^\top\Delta C\,v,\qquad v=C^{-1}b,
\]
\[
\boxed{
\partial_\alpha\log p_\alpha(b)
=\tfrac12\big[v^\top\Delta C\,v-\mathrm{tr}(C^{-1}\Delta C)\big].
}
\tag{22}
\]

이것은 36차원 zero-mean Gaussian benchmark의 band-inclusion 응답이다. R100의 nuisance-profiled 18-dof Schur statistic과 구분한다.

\(\Delta C\)의 최소 고유값은 \(5.8659\times10^{-8}>0\), trace는 \(6.62092\times10^{-4}\)였다.

| \(\alpha\) | \(T\) | \(dT/d\alpha\) | \(\partial_\alpha\log p_\alpha(b)\) |
|---:|---:|---:|---:|
| 0 | 52.410998 | −8.139706 | +0.498687 |
| 0.25 | 50.537053 | −6.920687 | +0.232021 |
| 0.50 | 48.923591 | −6.029729 | +0.058541 |
| 0.75 | 47.504818 | −5.348788 | −0.059694 |
| 1 | 46.237383 | −4.810442 | −0.143134 |

공분산 증가에 따라 \(T\)는 감소하지만 log likelihood에는 covariance-volume 항이 있으므로 단조증가하지 않는다. 이 좌표를 물리적으로 알려진 covariance를 임의로 조정하는 fitting knob로 사용한 것은 아니다.

중앙차분과 해석적 gradient의 차이는 \(5.54\times10^{-9}\) 이하였고, derivative 적분이 endpoint 변화를 복원하는 오차는 \(10^{-13}\) 정도였다. 변화하는 Gaussian law 아래 \(E_\alpha T_\alpha=36\)이며, 식 (1)의 직접 미분 \(-\mathrm{tr}(C^{-1}\Delta C)\)와 score covariance \(+\mathrm{tr}(C^{-1}\Delta C)\)가 상쇄된다.

## 8. 기존 5변수와 6대주제·7교차 축에 통합

5변수는 richer carrier와 law의 다섯 view로 유지한다.

| view | 매개변수 응답 |
|---|---|
| \(x_s\) | signed tensor/multipole/field의 tangent, DP 관측값 또는 scale response |
| \(Q_s\) | \(Q'=Dq[x]x'+\partial_s q\); body 변경과 eigenvalue/최적화 퇴화점 구분 |
| \(\Pi_s\) | matched law 및 strict tail event의 공동 변화 |
| \(F_s\) | event boundary 이동과 measure 변화의 합 |
| \(G_F\) | 기존 physical transport 의미를 보존하면서 \(\mathcal R_sF=dF/ds\) 또는 명시한 \(G_F[\gamma]\) 추가 |

정칙한 연속 event surface에서 \(F_s=P_s(f_s>0)\)이면

\[
F_s'
=E_s[\delta(f_s)\partial_s f_s]
+\operatorname{Cov}_s(1_{\{f_s>0\}},\mathcal S_s).
\tag{23}
\]

첫 항은 coarea boundary integral의 약기다. 이산 threshold jump나 support 변화는 exact difference/transition law로 처리한다. \(\Pi_s=P_s(T_s>t_s)\)에서도 \(\partial_s f_s=\partial_sT_s-t_s'\)를 사용한다. canonical strict-tail 의미를 유지한다.

### 8.1 여섯 대주제

| 기존 대주제 | 가장 직접적인 확장 | 완료에 도움을 주는 방식 |
|---|---|---|
| P1, tensorized 5변수 추론 | score·event·gauge response | law 변화와 functional 변화 분리, 동일 draw ID의 pushforward 유지 |
| P2, low-\(\ell\) morphology·복사 관측량 | beam/scale semigroup, mask-induced memory | 실제 혼합 연산자에서 필요한 보완 mode만 선택 |
| P3, 방향·깊이별 Hubble 관측량 | redshift/window/공분산 parameter 응답 | 관측 깊이 변화와 source/selection 변화를 분해 |
| P4, radio dipole·observer boost/tilt | nested-cut DP, 조건부 mark likelihood | 동일 catalogue 중복계수 방지, signed vector의 cut 응답 분석 |
| P5, 비등방·Bianchi 분류 | 한 class 내부의 물리 모수 tangent | 연속 모수의 식별 가능한 조합 탐색; class 간 비교는 이산적으로 유지 |
| P6, beyond-FLRW 운동학 | 광선·source·observer parameter 미분 | fixed-redshift endpoint와 frame response를 포함한 multi-probe 비교 |

### 8.2 일곱 PHY 교차 조합

정본 R78의 조합 자체를 유지했다.

| 교차 ID | 기존 구성 | 이번 보조 연구의 적용 |
|---|---|---|
| PHY-01 | P3/P6/P5 | 깊이·곡률·운동학 tangent와 optical endpoint 응답 |
| PHY-02 | P2/P6/P5 | 복사 morphology의 scale response와 물리 source response 분리 |
| PHY-03 | P2/P4 | 동일 boost 후보의 CMB·radio 응답 및 각 선택 연산자 연결 |
| PHY-04 | P6/P4/P5 | boost/tilt와 flux-selection nuisance 방향의 분리 |
| PHY-05 | P5/P6 | class 내부 tangent와 관측 frame/물리 등가성의 비교 |
| PHY-06 | P1/P2/P5/P6 | 하나의 선언된 joint law에서 5변수 response 적용 |
| PHY-07 | P1/P3/RADIO_DIPOLE | nested source/window law와 공동 uncertainty propagation |

이 표는 실행 연결이며 노드 완료 판정이 아니다. R78의 60개 노드·129개 간선을 변경하지 않았다.

## 9. 해소된 부분과 남은 입력

**이번 연구에서 확보한 것**

- 물리적 시간에 한정하지 않는 실제 생성자·흐름·기억항.
- 같은 sample을 공유하는 cut/exposure/scale coupling.
- 정규화된 법칙의 response와 충분상태 closure.
- baseline 조건부 likelihood로 전체 population amplitude nuisance를 제거하는 경로.
- 실제 R100 radio·CF4 자료에서 새로운 parameter response.
- optical fixed-redshift sensitivity를 구현할 정확한 미분식.

**외부 입력이나 후속 구현이 필요한 것**

CF4의 보정 전 원표·rejected population·부호 계보, LoTSS 내부 RMS/완전도, Gaia calibration, CMB matched split/noise law, 외부 native transfer atlas 등은 기존 상태를 유지한다. 한편 공동 per-cell cut likelihood, nuisance-profiled CF4 tangent, optical tangent/event 구현은 현재 코드로 이어갈 수 있다.

우선순위는 (1) 기존 per-cell maps의 conditional nested likelihood, (2) 실제 Schur/profile inference의 covariance response, (3) 22-state optical tangent와 endpoint correction, (4) 실제 mask operator의 scale closure 순이다. 각 단계는 새로운 데이터를 기다려야 하는 부분과 지금 가능한 조건부 계산을 분리한다.

## 10. 실행·검토·파일

세 연구 경로의 코드는 기존 checkout의 Python 3.12.3, NumPy 2.5.4, SciPy 1.18.1, SymPy 1.14.0에서 단일 BLAS/OpenMP/MKL/NumExpr thread로 실행했다. 독립적인 유한 합, count-space matrix, sparse matrix exponential, ODE, convolution quadrature 및 symbolic identity를 사용했다.

Wolfram 연결 요청은 실패했으므로 Wolfram 검산을 주장하지 않는다. 해당 대수식은 SymPy 및 별도 수치 표현으로 확인했다. DP 경로 첫 실행의 NumPy boolean JSON 직렬화 오류는 Python bool 변환으로 수정했으며 계산 모형은 바꾸지 않았다.

독립 검토는 한 번 수행했다. forward probability generator와 backward observable generator의 기호 구분, mark law가 baseline count/latent intensity에 의존하지 않는 전제의 명시를 문서에 반영했다. 이 수정은 수치 코드나 결과를 바꾸지 않았다. 독립 checker는 저자 코드를 import하거나 재실행하지 않고, 28개 finite count state의 backward drift를 유리수로 확인했다. 별도 clock의 kernel 잔차는 1.11×10⁻¹⁶, optical event chain-rule 잔차는 4.44×10⁻¹⁶였고, CF4를 Cholesky whitening/eigenmode로 재계산한 값은 저자 결과와 1.98×10⁻¹³ 이내로 일치했다. 같은 기계·수치 라이브러리를 사용한 별도 구현이라는 독립성 범위를 유지한다.

원본 연구·코드·결과 위치:

`/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/AUX_DP_MZ_PARAMETER_FLOW_20261123/`

- `DP_PARAMETER_THEORY.md`, `dp_parameter_checks.py`, `DP_PARAMETER_RESULTS.json`, `DP_PARAMETER_SOURCES.json`
- `MZ_PARAMETER_THEORY.md`, `mz_parameter_checks.py`, `MZ_PARAMETER_RESULTS.json`, `MZ_PARAMETER_SOURCES.json`
- `STATISTICAL_PARAMETER_THEORY.md`, `statistical_parameter_checks.py`, `STATISTICAL_PARAMETER_RESULTS.json`, `STATISTICAL_PARAMETER_SOURCES.json`
- `REVIEW.md`, `REVIEW_RESULTS.json`, `HANDOFF_LOCAL_AGENT.md`, `CONTEXT.json`, `README.md`, `END_STATE.json`

주요 입력 SHA256:

| 입력 | SHA256 |
|---|---|
| R100 radio 결과 | `4c2be49a7c3b391fc2151b1ffc84a199c3b0a4951308dbb2dea5e91785e235e9` |
| R100 CF4 covariance NPZ | `7d5ecd55b776b8b9b97ae32385fd4573db8916846bb4c0a6dc5eca85eab18093` |
| R78 canonical DAG | `90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11` |
| R100 optical source | `5abc53f7f611c9d47fefdbfdb443aba6daa842d7ab2442ce427ddfa870876e6a` |

종료 확인에서 HEAD는 기준 SHA와 같고 tracked working-tree 변경은 없었다. 보호한 AGENTS, canonical DAG, R69 이론 문서, R100 보고서 및 앞선 AUX 증거의 SHA가 모두 유지되었다. 이번 새 보조 연구 파일은 지정한 새 디렉터리에만 추가했고, stage·commit·push는 하지 않았다.

## 원전

1. Del Moral, P., Doucet, A., Jasra, A. (2006). *Sequential Monte Carlo samplers*. JRSS B 68(3), 411–436. Introduction, Sections 2–3. [저자 원문](https://www.stats.ox.ac.uk/~doucet/delmoral_doucet_jasra_sequentialmontecarlosamplersJRSSB.pdf).
2. Glynn, P. W. (1990). *Likelihood ratio gradient estimation for stochastic systems*. Communications of the ACM 33, 75–84. Section 3. [저자 원문](https://web.stanford.edu/~glynn/papers/1990/G90a.pdf).
3. Del Moral, P., Doucet, A., Singh, S. S. (2010). *A backward particle interpretation of Feynman–Kac formulae*. ESAIM M2AN 44, 947–975. DOI 10.1051/m2an/2010048, equations (1.1)–(1.3). [저자 원문](https://www.stats.ox.ac.uk/~doucet/delmoral_doucet_singh_backwardfeynmankac.pdf).
4. Peliti, L. (1985). *Path integral approach to birth-death processes on a lattice*. Journal de Physique 46, 1469–1483, Section 2. [저자 원문](https://www.peliti.org/Publications/pathIntegrals.pdf).
5. Last, G., Penrose, M. (2017). *Lectures on the Poisson Process*. Marking/thinning Theorems 5.6, 5.8, Corollary 5.9 및 Cox variance. [저자 원문](https://stoch.math.kit.edu/img/Last/lastpenrose2017.pdf).
6. Rafler, M. (2012). *The Pólya sum kernel and Bayes estimation*. arXiv:1202.4696v2, Theorem 2.1 및 Corollary 2.3. [원문](https://arxiv.org/html/1202.4696v2). [SciSpace 검색 연결](https://scispace.com/papers/the-p-olya-sum-kernel-and-bayes-estimation-1is3d3i0i4).
7. Chorin, A. J., Hald, O. H., Kupferman, R. (2002). *Optimal prediction with memory*. Physica D 166, 239–257, Section 2. [저자 원문](https://math.berkeley.edu/~chorin/CHK02.pdf).
8. Bülow, T. (2001). *Spherical Diffusion*. University of Pennsylvania Technical Report MS-CIS-01-38, equation (28)와 semigroup 설명. [대학 원문](https://repository.upenn.edu/bitstreams/b61cb570-80c6-4f39-9725-76369e48bc9d/download).
9. Meyer, H., Voigtmann, T., Schilling, T. (2017). *On the “generalized Generalized Langevin Equation”*. DOI 10.1063/1.5006980. [arXiv:1706.00658](https://arxiv.org/abs/1706.00658).

위 문헌은 외부 이론의 근거다. 유한 예제와 R100 parameter-response 수치는 이번 연구의 직접 유도·실행 결과이며, 문헌의 관측적 결론으로 돌리지 않는다. 별도 novelty 또는 일반적인 불가능성 정리는 주장하지 않는다.

## 부록: local agent 실행 인계 요약

기준 HEAD와 현재 변경분을 먼저 확인한 뒤 위 새 디렉터리의 CONTEXT, README, REVIEW, END_STATE 및 해당 경로의 theory/code/results를 읽는다. 기존 canonical DAG, source identities, five-view semantics와 사용자 no-push 지시를 유지한다. 초기 연구를 반복하지 않고 다음 작업을 실제 구현한다.

1. `scripts/r100/radio_exposure_selection.py`의 per-cell cut maps에서 동일 object/support를 보존한 차분 bins를 만들고 식 (11)의 conditional likelihood와 명시적인 joint Gamma-Cox 대안을 비교한다. 비음수 bins·normalization·nested support·공동 uncertainty·heldout cut/sky prediction을 확인한다.
2. `scripts/r100/cf4_upstream_and_kband.py`의 실제 Schur/profile 계산에 covariance tangent를 연결한다. 기존 R5 endpoint 12.116320633338589와 10.927665138389305를 복원하고, nuisance projection과 residual의 derivative를 함께 포함한다.
3. `htt/bass/transport/position_drift_optics.py`에 한 물리 모수의 tangent와 emission-event correction을 추가한다. 고정 관측 redshift에서 독립적으로 다시 푼 finite difference, FLRW/zero-source, 기존 equivariance 조건으로 판별한다.
4. 실제 harmonic/beam 및 mask mixing에서 \(ML=A_{\rm obs}M\)을 검사한다. 닫히지 않으면 작은 auxiliary-mode state나 검증된 memory를 사용하고, 같은 initial sky/law와 초기 force를 유지한다.

각 작업은 derived / numerically checked / implementation-verified / model-conditional / externally blocked 상태를 구분해 반환한다. 원래의 외부 데이터가 도착했다고 가정하거나 모든 과학 노드가 완료되었다고 표시하지 않는다. 새로운 policy 문서와 반복 감사보다 실제 결과 한 단위를 우선한다. push하지 않는다.

