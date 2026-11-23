# Doi–Peliti·Mori–Zwanzig와 5변수 연구의 결합
## 기존 연구 축의 완료와 수렴을 위한 보조 연구

2026-11-23 KST  
대상: HTT/MIO/BASS/obsstat의 기존 6개 대주제·7개 교차 물리 주제·60개 science node  
기준 checkout: research/r69-observable-physics-bridges-20261118  
기준 HEAD: 397a86613b6d9548d3750ff956e3ebf8a6e49368  
범위: 추가 문헌 연구, 직접 유도, 유한 구별 계산, 기존 코드의 읽기 전용 재사용  
게시: 사용자의 지시에 따라 push하지 않음. 이번 보조 작업은 stage/commit도 수행하지 않음.

## 1. 결론과 이번에 실제로 얻은 것

두 형식을 결합하는 가장 생산적인 방법은 **공통 생성법칙을 정하고, 숨은 자유도의 효과를 기억·초기조건 항으로 유지한 뒤, 기존 다섯 뷰의 오차를 직접 제한하는 것**이다. Doi–Peliti(DP)는 계수·선택·반응 과정의 공동 확률법칙을 구성하는 데, Mori–Zwanzig(MZ)는 이미 주어진 동역학의 축약을 정당화하거나 반박하는 데 쓰는 것이 적합하다.

이번 보조 연구에서는 다음을 실제로 수행했다.

1. 정상순서 jump generator, 선택/thinning 연산, 중첩 표본의 공동 PGF, 공통장 조건부 likelihood를 유도하고 구현했다.
2. 비정상 선형 block의 정확 기억식, 초기 조건부 평균·잡음·상관, 국소 Markov 근사의 잔차와 오차경계를 유도했다.
3. DP count 생성계에서 숨은 환경을 제거하면 정확한 기억식이 나오는 완결된 작은 모형을 계산했다.
4. 축약된 carrier의 오차가 Q, F, Pi, G_F로 전달되는 조건부 경계를 정리했다.
5. 기존 legacy MZ 실패와 R98/R99 코드·이론을 대조하여 채택할 부분과 아직 실제 source 입력이 필요한 부분을 분리했다.

중요한 수치 결과는 세 가지다. 중첩 Gamma–Cox 표본의 공분산은 정확히 36이며, 검출을 잘못 독립화하면 33.6이 된다. 평균 count가 20인 두 상태 환경 모형에서 N>=35 꼬리는 기억을 유지하면 0.0283647, Poisson 평균 근사에서는 0.00148903으로 약 19.05배 다르다. 초기 resolved/hidden 상관을 생략한 MZ 예제는 특정 시각의 분산을 20.855% 과소평가했다.

이는 선언한 유한 모형의 결과다. 관측 카탈로그에서 같은 크기의 효과를 측정했다는 뜻은 아니다. 기존 science node의 완료 상태는 변경하지 않았다.

## 2. 기존 다섯 변수의 의미를 그대로 유지한다

기준은 R69의 GENERAL_LOWELL_TILTED_BIANCHI_KO.md와 repository의 htt-xqpi-fg-formalism이다.

| 뷰 | 유지할 의미 | 이번 결합에서의 역할 |
|---|---|---|
| x | 부호·방향·frame·epoch·관측 연산자를 가진 tensor/multipole/function carrier | 축약의 직접 대상과 오차 기준 |
| Q | 선언한 물리적 허용 body의 gauge 또는 물리적으로 정규화된 제약량 | 허용성·경계 민감도 검사 |
| Pi | 지정된 matched-null/source law 아래의 tail probability | 전체 생성법칙과 꼬리오차 검증 |
| F | 지정된 support·measure·event 아래의 occupancy | threshold 부근의 불안정성 검사 |
| G_F | 실제 같은 계의 수송에 따라 정의한 F들의 사전 지정 functional | cross-depth 공분산과 분모 조건 검사 |

다섯 뷰는 동일한 물리·통계 객체에서 나온 상관된 결과다. 이들을 다섯 개 독립 likelihood로 곱하거나, 다섯 개 scalar가 자동으로 닫힌 Markov 상태를 이룬다고 가정하지 않는다. HTT의 model-dependent posterior와 MIO의 diagnostic tail을 합쳐 하나의 진리 확률로 만들지도 않는다.

MZ의 resolved state는 방정식에 근거하여 선택한다. 예컨대 signed STF shear, 보존량, 필요한 photon moments와 frame 관계를 남길 수 있다. 최종 출력 label 수에 맞추어 상태의 차원을 정하지 않는다.

## 3. DP: 공동 생성모형에서 가장 빨리 쓸 수 있는 부분

### 3.1 정상순서 generator와 그 한계

반응 r이 species 점유수 alpha_r를 beta_r로 바꾸고 propensity가
k_r prod_i n_i^(underline alpha_ri)라고 하자. 조합계수 alpha!를 rate에 포함하는지는 명시해야 한다. 확률벡터에 대한 convention을 partial_t |P>=L_DP |P>로 잡으면

\[
 {\cal L}_{\rm DP}
 =\sum_r k_r\left[
 \prod_i(a_i^\dagger)^{\beta_{ri}}
 -\prod_i(a_i^\dagger)^{\alpha_{ri}}
 \right]\prod_i a_i^{\alpha_{ri}} .
\]

생성 연산자를 왼쪽에 두는 정상순서는 propensity와 확률보존을 결정한다. Peliti의 원문은 이 연산자와 시간분할 경로적분의 관계를 제시한다.[1] 이번 코드는 닫힌 유한 반응계의 직접 jump matrix와 이 표현을 대조했다.

Coherent-state 변수를 도입하면 bulk action에는

\[
 S_{\rm bulk}
 =\int dt\,[\bar\phi\dot\phi-{\cal L}_{\rm DP}(\bar\phi,\phi)]
\]

가 나타난다. 초기 분포, 최종 PGF/source 및 endpoint 인자는 별도로 유지해야 한다. DP_THEORY.md에는 해당 경계 convention이 포함되어 있다.

다만 DP field를 실수 입자밀도 표본으로 해석할 수는 없다. 예를 들어 pair annihilation의 shifted response quadratic은 형식적으로 음의 noise variance처럼 보일 수 있지만, 원래 jump process의 확률은 양수다. factorial moment와 ordinary moment를 구별해야 한다. Wiese는 coherent-state noise와 실제 coarse-grained density noise가 다른 구성임을 명시적으로 분석한다.[2]

### 3.2 두 표본의 겹침을 보존하는 PGF

하나의 latent field Psi에 조건부로 천체들이 intensity Lambda(dxi|Psi)의 Poisson process를 이룬다고 하자. xi에는 위치, flux, SED, redshift 등 필요한 mark를 포함한다. 같은 물체에 대한 검출 indicator I_A,I_B에 대해

\[
 q_A=P(I_A=1|\xi,\Psi),\quad
 q_B=P(I_B=1|\xi,\Psi),\quad
 q_{AB}=P(I_A=I_B=1|\xi,\Psi)
\]

를 정의한다. 확률의 허용범위는

\[
 \max(0,q_A+q_B-1)\le q_{AB}\le\min(q_A,q_B)
\]

이다. 독립적인 다른 물체들의 marking을 가정하면 공동 PGF는

\[
 {\cal Z}(z_A,z_B|\Psi)
 =\exp\!\int\Lambda(d\xi|\Psi)
 \left[q_A(z_A-1)+q_B(z_B-1)
       +q_{AB}(z_A-1)(z_B-1)\right].
\]

이 식은 00,10,01,11의 네 범주를 먼저 분리한 뒤 Poisson 생성함수를 곱해서 얻는다. 실제 공동법칙은 그 뒤 Psi에 대해 평균한다. 이는 marking 및 Cox-process 이론에 근거한 프로젝트용 구성이다.[3]

M_A(Psi)=int q_A Lambda, M_B(Psi)=int q_B Lambda로 쓰면

\[
 \boxed{
 {\rm Cov}(N_A,N_B)
 =E_\Psi\!\int q_{AB}\Lambda
  +{\rm Cov}_\Psi(M_A,M_B).
 }
\]

첫 항은 동일 천체의 중복 기여, 둘째 항은 공통 밀도장·환경 기여다. 조건부 독립 검출에서만 q_AB=q_A q_B이고, 같은 실현된 flux mark의 nested cuts에서는 q_AB=min(q_A,q_B)다. 별도의 noisy 측정으로 만든 두 cut은 중첩성이 자동으로 성립하지 않는다.

Radio source가 여러 component로 분해되면 물체당 Bernoulli mark도 충분하지 않다. 물체당 component 수의 PGF를 써야 한다. 실제 계산한 단순 예에서는 Poisson source 평균 10, source당 component 2개일 때 component 평균 20, 분산 40이었다. 독립 Poisson component 모델의 분산 20과 다르다.

### 3.3 수행한 Gamma–Cox 계산

통합 intensity를 Lambda~Gamma(shape=4, rate=0.2)로 두었다.
E Lambda=20, Var Lambda=100이다. 동일 mark에 대한 중첩 선택을

\[
 q_A=0.4,\quad q_B=0.7,\quad q_{AB}=0.4
\]

로 정하면

\[
 E(N_A,N_B)=(8,14),\qquad
 {\rm Cov}(N_A,N_B)=0.4(20)+0.4(0.7)(100)=36.
\]

- 공동 PMF 적분, PGF 미분, 별도 수치 구적을 대조했다.
- seed 20261123으로 300,000개 생성한 공분산은 35.96748, 추정 Monte Carlo SE는 0.13543이었다.
- q_AB를 0.28로 잘못 바꾸면 예측 공분산은 33.6이다.
- A가 stricter cut이면 항상 N_A<=N_B여야 한다. 올바른 모델은 (9,6)에 확률 0을 주지만, 잘못 독립화한 모델은 약 2.29714e-4를 준다.

이 마지막 검사는 단순히 covariance 값을 맞추는 것보다 강하다. 과학적 표본 정의에 반하는 결과를 모형이 생성하는지 직접 판별한다.

### 3.4 R99의 selection 정규화와 결합

R99에서 이미 정리한 selected-record likelihood는 공통장을 적분한 뒤 정규화하는 구조를 가진다.

\[
 p(y|E)=
 \frac{\int p(d\Psi)\prod_i B_i(y_i,\Psi)}
      {\int p(d\Psi)\prod_i\alpha_i(\Psi)}.
\]

이를 unconditional p(dPsi) 아래의 prod(B_i/alpha_i) 평균으로 바꾸면 다른 법칙이 된다. 안쪽에서 선택을 조건화하려면 Psi의 분포도 p(dPsi|E)에 맞게 바꾸어야 한다.

또한 고정된 선택 표본 수를 조건화한 likelihood와 random total count를 포함한 point-process likelihood는 서로 다르다. 어느 쪽을 쓰는지 먼저 선언한다. DP는 이 기존 정규화를 연산자/PGF 수준에서 구현하는 데 쓰며, 이미 있는 likelihood를 이름만 바꾸는 것은 연구 진전으로 세지 않는다.

### 3.5 반응·화학 쪽의 제한된 기여

닫힌 hydrogen cell에서

\[
 H\to p+e:\ \Gamma N_H,\qquad
 p+e\to H:\ (\alpha/V)N_pN_e
\]

를 두고 N_H+N_p=M, N_p-N_e=0을 보존했다. e와 p는 다른 species이므로 중성 support에서 propensity는 n²이며 n(n−1)이 아니다.

\[
 {dE n\over dt}
 =\Gamma(M-E n)-{\alpha\over V}[(E n)^2+{\rm Var}(n)].
\]

M=40, Gamma=0.4 s^-1, alpha/V=0.015 s^-1의 예에서 정확 정상 평균은 21.84576, mean-field 평형은 21.94335, Fano factor는 0.314742였다. 보존·stationarity·상세균형을 직접 확인했다.

이 예는 R98의 effective hydrogen window를 확장할 때 조합률과 moment closure를 어떻게 점검할지 보여준다. 실제 재결합의 temperature law, radiative escape, 다준위 원자, perturbation transfer를 검증한 결과는 아니다. 실제 우주론적 coarse cell에서 이 작은-count 보정이 크다고 주장하지 않는다. 현재 M09/B02/SQ-NATIVE의 전체 source 의무는 남는다.

## 4. MZ: 정확 소거와 허용 가능한 근사를 구별한다

### 4.1 자율계의 정확 항등식

완전 동역학의 backward/Koopman generator를 L, projector를 P_mz, complement를 R_mz=I−P_mz라고 하자. generator·semigroup와 공통 정의역이 존재하는 범위에서, resolved observable g=P_mz g에 대해

\[
 \frac{d}{dt}e^{tL}g
 =e^{tL}P_{\rm mz}Lg
 +e^{tR_{\rm mz}L}R_{\rm mz}Lg
 +\int_0^t e^{(t-s)L}
       P_{\rm mz}L e^{sR_{\rm mz}L}R_{\rm mz}Lg\,ds .
\]

이 식은 Duhamel/Dyson identity에서 나온다. 무한차원 일반 generator에 대한 정의역·well-posedness를 자동으로 보증하지는 않는다. 조건부 기대 projector를 쓰려면 그 기대를 정의하는 실제 ensemble law가 필요하다. Chorin–Hald–Kupferman의 원문은 이 초기 미해결 분포와 기억을 함께 다룬다.[4]

따라서 MZ는 없는 generator나 초기 통계를 만들어주는 방법이 아니다. formal exactness와 계산 가능한 closure의 정확도는 구별한다.

### 4.2 현재 코드로 연결하기 쉬운 비정상 block 공식

정해진 배경과 선형화에서, 같은 frame·basis로 표현한 resolved carrier a와 hidden component b가

\[
 \dot a=A(t)a+B(t)b,\qquad
 \dot b=C(t)a+D(t)b
\]

를 만족한다고 하자. U_D는 partial_t U_D(t,s)=D(t)U_D(t,s), U_D(s,s)=I를 만족한다. 그러면

\[
 b(t)=U_D(t,t_0)b_0+
       \int_{t_0}^t U_D(t,s)C(s)a(s)\,ds,
\]

따라서

\[
 \boxed{
 \dot a(t)=A(t)a(t)+B(t)U_D(t,t_0)b_0+
       \int_{t_0}^t K(t,s)a(s)\,ds,\qquad
 K(t,s)=B(t)U_D(t,s)C(s).
 }
\]

시간에 따른 D들이 교환하지 않으면 U_D를 단순한 exp[(t−s)D(t)]로 바꾸지 않는다. 일반 비정상 기억은 lag만의 함수가 아니다. 비정상 projection과 초기조건 의존 fluctuating force의 문헌적 근거도 확인했다.[5]

초기 joint law가 제공되면

\[
 b_0=E[b_0|a_0]+\zeta_0,\qquad E[\zeta_0|a_0]=0
\]

로 분해할 수 있다. H_t=B(t)U_D(t,t_0)라 쓰면

\[
 {\rm Cov}[\eta(t),\eta(s)|a_0]
 =H_t\Sigma_{b|a_0}H_s^\mathsf T,\qquad
 \eta(t)=H_t\zeta_0 .
\]

초기 conditional mean은 별도 deterministic initial-slip 항으로 남는다. 초기 resolved/hidden 상관을 제거하거나 noise를 백색으로 만드는 것은 추가 가정이다.

이 raw block 소거의 D와 모든 Mori projection의 orthogonal generator가 같지는 않다. 선형 Gaussian 회귀 H_0=Sigma_ba Sigma_aa^-1를 사용하여 w=b−H_0 a로 좌표를 바꾸면 hidden block은 D−H_0B가 된다. 두 분해의 kernel과 초기항을 서로 섞지 않는다.

### 4.3 언제 local closure를 쓸 수 있는가

상수 block, 외부 forcing 없음, invertible D, ||exp(Dt)||<=M exp(−gamma t), gamma>0를 가정하자. 정확한 방정식은

\[
 \dot a=(A-BD^{-1}C)a+r(t)
\]

로 쓸 수 있고,

\[
 r(t)=Be^{Dt}(b_0+D^{-1}Ca_0)
 +\int_0^tBe^{D(t-s)}D^{-1}C\dot a(s)\,ds.
\]

따라서 L_t=sup_{s<=t}||dot a(s)||에 대해

\[
 \|r(t)\|\le
 \|B\|M e^{-\gamma t}\|b_0+D^{-1}Ca_0\|
 +{\|B\|M\|D^{-1}C\|\over\gamma}
  (1-e^{-\gamma t})L_t.
\]

첫 항은 초기 준비의 불일치, 둘째 항은 hidden relaxation에 비해 resolved state가 변화하는 효과다. resolved propagator의 증폭까지 적분해야 상태오차 bound가 된다. 비정상 확장에서도 외부 forcing을 0으로 두고 D(t)의 가역성 및 E(t)=−D(t)^-1C(t)의 C¹ 정칙성을 가정한다. E의 시간미분도 포함해야 하며, 외부 hidden forcing이 있으면 그 항을 bound에 추가해야 한다.

기억이 짧다는 말, D의 순간 eigenvalue가 안정하다는 말, 몇 개 pole을 썼다는 말은 이 전체 조건을 대신하지 못한다. 보존·zero·slow mode는 resolved set에 남기거나 정확 기억으로 유지한다.

### 4.4 실제 계산 결과

무차원 시간 s=t/T, epsilon=tau_hidden/T를 사용한 안정한 모형

\[
 a'=-a+0.8b,\qquad
 \epsilon b'=-b-0.5a
\]

를 전체 matrix exponential, 정확 memory embedding, local closure로 비교했다. 초기값 a(0)=1,b(0)=0, 구간 [0,8]에서의 명시된 격자 최대오차는 다음과 같다.

| epsilon | 정확 기억 오차 | local Markov 오차 |
|---:|---:|---:|
| 0.001 | 2.212e-13 | 0.0003936 |
| 0.01 | 1.028e-10 | 0.0036185 |
| 0.1 | 2.721e-13 | 0.024628 |
| 1 | 3.070e-12 | 0.079871 |
| 10 | 1.102e-12 | 0.115739 |

준비된 hidden 초기값도 별도로 계산했고, 전체 실행 범위의 exact-memory 오차는 1.440e-10 이하였다. 유도한 해석적 상태오차 상한이 계산 격자 오차를 덮었다.

epsilon=1에서는 완전 해 a가 음수로 내려가지만 local 해 exp(−1.4s)는 양수다. signed carrier의 형태까지 달라질 수 있다. 한 번의 feedback만 계산한 해는 epsilon→0에서도 고정 결합에 대한 feedback을 모두 합하지 않으므로 약 0.034의 오차가 남았다.

비정상 예제에서는 같은 lag 0.5에 대해 K(0.8,0.3)=−0.0985365, K(2.0,1.5)=−0.1821275였다. 별도 직접 Volterra 구적의 hidden reconstruction 잔차는 5.592e-13 이하였고, local closure 오차는 0.018578이었다.

또한 명시한 Gaussian 초기 law에서 cross covariance를 생략하면 t=0.5의 resolved 분산을 20.855% 낮게 계산했다. 이는 실제 CF4/Gaia null이 아니라 초기 상관의 효과를 구별하기 위한 계산이다.

## 5. DP에서 MZ 기억으로 이어지는 정확한 결합 예제

관측 event intensity가 숨은 상태 h=±1에 따라 lambda_h=barlambda+h delta이고, h가 각 방향으로 kappa의 rate로 전이한다고 하자. barlambda>=|delta|, N(0)=0, 두 초기 상태의 확률은 1/2다.

G_±(z,t)=E[z^N 1_{h=±}], G=G_++G_−, H=G_+−G_−를 정의하면

\[
 \dot G=a_zG+b_zH,\qquad
 \dot H=b_zG+(a_z-2\kappa)H,
\]
\[
 a_z=\bar\lambda(z-1),\qquad b_z=\delta(z-1).
\]

숨은 H를 정확히 소거하면

\[
 \boxed{\dot G=a_zG+
 b_z^2\int_0^t e^{(a_z-2\kappa)(t-s)}G(s)\,ds.}
\]

closed PGF는 omega=sqrt(kappa²+b_z²)에 대해

\[
 G=e^{(a_z-\kappa)t}
 [\cosh(\omega t)+(\kappa/\omega)\sinh(\omega t)]
\]

다. 이 memory는 PGF의 z에 의존하며 전체 count law를 담는다. PGF를 개별 물체의 물리 궤적으로 해석하지 않는다.

조건부 Poisson law에서 직접 얻는 모멘트는

\[
 EN=\bar\lambda t,\qquad
 {\rm Var}N=\bar\lambda t+
 \delta^2\left[{t\over\kappa}
 -{1-e^{-2\kappa t}\over2\kappa^2}\right].
\]

kappa→0에서 두 Poisson의 mixture, delta=0 또는 고정 delta의 kappa→infinity에서 단일 Poisson으로 간다. 이 극한도 계산했다.

barlambda=5, delta=3, t=4일 때의 수치는 다음과 같다. 시간과 rate는 임의의 양의 관측시간 단위 tau_star로 무차원화했다. redshift를 시간으로 바꾼 모형이 아니다.

| kappa | 평균 | 분산 | P(N>=35) | Poisson 꼬리 대비 |
|---:|---:|---:|---:|---:|
| 0 | 20 | 164.000000 | 0.16038308 | 107.71 |
| 0.2 | 20 | 110.213358 | 0.09613004 | 64.56 |
| 1 | 20 | 51.501510 | 0.02836470 | 19.05 |
| 5 | 20 | 27.020000 | 0.00551945 | 3.71 |
| 50 | 20 | 20.718200 | 0.00180368 | 1.21 |

Poisson(mean=20)의 꼬리는 0.001489033861이다. kappa t=200에서도 이 threshold의 상대 꼬리오차가 약 21% 남는다. 따라서 시간척도 비만으로 Pi의 정확도를 선언해서는 안 된다.

count-space forward generator를 n=128까지 계산하고, closed PGF·2×2 matrix exponential·Volterra embedding과 대조했다. 잘린 count 확률의 Chernoff 상한은 1.06e-36이다. 이는 확률적 truncation bound이며 floating-point 전체의 interval certification은 아니다.

## 6. 다섯 뷰를 실제 수렴 기준으로 바꾸는 경계

아래는 같은 frame, support, 단위, source/null law 계약 아래에서 직접 유도한 조건부 경계다. 새로운 우주론 정리나 새로운 식별력의 주장으로 사용하지 않는다.

### 6.1 Carrier와 Q

||x−x_hat||<=epsilon_x를 얻었다고 하자. 물리적 body K가 반지름 r>0의 norm ball을 포함하는 convex body이고 Q=p_K이면 subadditivity에서

\[
 |Q(x)-Q(\hat x)|\le\epsilon_x/r.
\]

실제 Q가 이 형태일 때만 쓴다. 특히

\[
 Q_H(d,S)=-\min_{\|n\|=1}(d\cdot n+S:nn)
\]

에는

\[
 |Q_H-\hat Q_H|
 \le\|d-\hat d\|_2+\|S-\hat S\|_{\rm op}
\]

가 바로 성립한다. Lie flux/rho_N처럼 분모가 있는 Q에는 rho_N의 양의 하한과 분모 오차가 추가로 필요하다.

### 6.2 F: threshold 주변의 질량이 결정한다

고정 finite measure mu와 event f(u)>0에 대해

\[
 F=\mu(U)^{-1}\int_U1_{f(u)>0}\,d\mu(u)
\]

라 하자. sup|f−f_hat|<=epsilon_f이면 indicator가 달라지는 곳은 |f_hat|<=epsilon_f 안에만 있으므로

\[
 |F-\hat F|
 \le{\mu\{|\hat f|\le\epsilon_f\}\over\mu(U)}.
\]

따라서 평균적 field 오차가 작아도 threshold 근처에 질량이 집중되면 occupancy는 수렴하지 않을 수 있다. 실제 sky/exposure measure로 margin band를 계산해야 한다. 자기 sky mean을 뺀 event field라면 기본 field 오차 epsilon에 대해 centered field 오차는 최대 2epsilon이다.

### 6.3 Pi: matched-null 분포와 observed threshold를 함께 제한한다

full/reduced null 통계량을 coupling하여
P(|T−T_hat|>epsilon_T)<=delta_law이고
|t_obs−t_hat_obs|<=epsilon_obs이면

\[
 |\Pi-\hat\Pi|\le\delta_{\rm law}+
 \hat P_0\bigl(
 |\hat T-\hat t_{\rm obs}|\le\epsilon_T+\epsilon_{\rm obs}
 \bigr).
\]

tail indicator가 바뀌는 사건을 나누어 얻은 경계다. 평균과 covariance의 일치만으로 delta_law를 얻지는 못한다. 이 점이 위 MMPP 계산의 실질적 교훈이다.

### 6.4 G_F: 사전 지정 functional과 cross-depth law를 유지한다

차이 G_F=F_2−F_1가 선언된 경우에는

\[
 |G_F-\hat G_F|\le\epsilon_{F_1}+\epsilon_{F_2}.
\]

비율이 선언되고 F_1,hat F_1>=d>0이면

\[
 \left|{F_2\over F_1}-{\hat F_2\over\hat F_1}\right|
 \le{\epsilon_{F_2}\over d}
 +{|\hat F_2|\epsilon_{F_1}\over d^2}.
\]

이는 G_F를 보편적으로 비율로 재정의하는 식이 아니다. 깊이별 mock은 공통장·calibration·selection을 공유해야 한다. 독립 draw로 각 marginal만 맞추면
Var(F_2−F_1)=Var(F_2)+Var(F_1)−2Cov(F_2,F_1)를 보존하지 못한다.

### 6.5 다섯 뷰만의 자동 closure를 가정하지 않는다

모든 admissible initial states/laws에 대해 동일한 reduced Markov dynamics를 요구하는 strong lumpability에서는 L(f o r)가 r만의 함수여야 한다. 특정 초기 law에서만 되는 weak closure는 이 조건과 구별한다.

예를 들어 dot x=v, dot v=0에서 x만 남기면 (x=0,v=1)과 (x=0,v=−1)의 instantaneous x와 그 진단량은 같아도 미래는 반대다. 필요한 hidden variable을 더 남기거나 기억·초기 조건부 law를 제공해야 한다. 이것이 현재의 모든 full carrier에 대한 불가능 정리는 아니며, actual generator에 맞춰 resolved set을 고르는 기준이다.

## 7. GR·광학·legacy에 적용할 때의 구체적 제한

기본 metric은 (-,+,+,+), c와 G는 SI대로 유지한다. R69의 Lie convention에서

\[
 {\cal C}_i=-3\sigma_{ij}a^j+
 \epsilon_{ijk}\sigma^j{}_\ell N^{\ell k}
 =-{8\pi G\over c^3}j_i^N,\qquad Na=0,
\]
\[
 D_t\sigma+3H\sigma
 ={8\pi G\over c^2}\pi^N-c^2({}^3R)_{\rm STF}.
\]

projector의 ensemble은 허용 constraint surface에 지지되어야 한다. 선형화는 제약 tangent 위에서 수행하고, 시간에 따라 바뀌는 tangent basis와 tetrad의 연결항도 남긴다. nonlinear constraint가 0이라는 사실이 constraint(E state)=0을 뜻하지는 않는다.

GR에 MZ를 적용한 te Vrugt–Hossenfelder–Wittkowski(2021)의 선행연구가 이미 존재한다.[6] 이 논문의 Buchert irrotational-dust 예제는 formal memory identity 뒤에 noise 생략, exponential memory ansatz, 빠른 일부 kernel 및 near-Friedmann 근사를 추가한다. 그 jerk 결과를 R69 tilted multifluid tensor closure로 그대로 읽을 수 없다. 이 작업은 GR-MZ의 신규성을 주장하지 않는다.

legacy의 CO-08은 downclaimed rejection sentinel이고 TH-08은 native-solver-dependent다. 실제 archive에서 naive imaginary-axis recursion, 전 대역 1–4 pole 적합, Teff leading closure, underconverged reference의 실패를 확인했다. 해당 문서와 CSV를 보존했다. 손상된 legacy summary.json은 새 결과로 덮지 않았다.

R98 radiation_feedback_audit의 1-loop 계산은 유용한 기존 reference다. 그러나 self-consistent memory resummation을 하려면 동일 배경에서 A,B,C,D, collision exchange, radiation response와 constraint tangent가 실제로 필요하다. 기존 radiation_moment_operators를 읽기 전용으로 실행한 STF trace 잔차 6.939e-17은 그 구적 검산이며 full hierarchy 검증은 아니다.

R99의 Jacobi/광선족 계는 이미 작고 명확하다. 거리를 구하려면 displacement·screen·energy·source-redshift root를 유지하는 편이 현재 더 직접적이다. 최종 상태 확인에서 기존 R100의 position_drift_optics.py 및 OPTICAL_DRIFT_RESULTS.json도 확인했다. 이 결과는 FLRW/I/V/VII_h/VI_h의 model-conditional position drift와 source/observer response를 이미 계산한다. 따라서 광학 구현을 처음부터 다시 만드는 대신 해당 결과를 reference로 사용한다. 실제 source motion·observer 조건·공통 covariance의 관측적 qualification은 별도다.

## 8. 6개 대주제의 수렴 방향

| 기존 축 | 이번 보조 연구의 채택 항목 | 실제 완료를 위해 남은 것 |
|---|---|---|
| P1: five-view/formal inference | 공통 law의 correlated pushforward; Q/Pi/F/G_F 오차경계 | physical anchor, 공통 congruence와 qualified joint law |
| P2: CMB·photon | positivity/고차 moment/초기 slip을 보존하는 축약 조건 | release-matched null, 독립 normal photon flux, external transfer |
| P3: CF4·방향별 H | R99 selected-mark 정규화와 공동 source/calibration law를 연결 | 새 intake의 calibration·selection·overlap qualification |
| P4: radio·count·frame | q_AB, 공통 Cox field, nested support, component multiplicity | completeness/RMS/SED·parent matching·LSS law |
| P5: Bianchi·kinetic·chemistry | 반응 보존법칙·moment closure·제약면 위의 MZ | 실제 source blocks, 독립 rho/j/pi, 외부 evolving hierarchy/atlas |
| P6: Gaia·광학·kinematics | 초기/공통 상관, frame 연결항, 기존 R100 position-drift reference | AGN/scan calibration law, 실제 source-motion·observer 조건과 joint qualification |

현재 local R100 SOURCE_INTAKE_RECEIPT에는 SDSS PV 34,059행과 6dFGSv 8,885행의 전체 파일 취득 기록이 있다. 이번 보조 연구에서 새로 다운로드한 것은 아니다. 따라서 이 둘의 다음 단계는 원파일 취득의 반복보다 실제 calibration/selection/source-law 결합이다. 취득 기록만으로 SQ-CF4를 완료했다고 판정하지 않는다.
최종 읽기 시 기존 R100에는 RADIO_EXPOSURE_SELECTION_RESULTS.json도 존재했다. 상태는 MODEL_CONDITIONAL_EXPOSURE_RESELECTION_EXECUTED이며, optical 결과의 상태는 MODEL_CONDITIONAL_NUMERICALLY_CHECKED다. 두 결과 모두 physical_Pi와 physical_GF가 null이다. Radio 기록은 내부 RMS/valid-pixel holes, flux-size completeness 및 source association을 여전히 외부 입력으로 남긴다. 이번 DP/MZ 연구는 이 실행을 수행했다고 귀속하지 않으며 기존 결과를 보존하여 후속 reference로 재사용한다.


### 교차 7개 주제에 대한 정확한 연결

| 교차 ID | 이번에 제공한 구조 | 계속 필요한 실제 입력 |
|---|---|---|
| PHY-01 | CF4/shear 응답의 common-field·축약 오차 관리 | finite-z physical response와 velocity/calibration law |
| PHY-02 | photon moment의 initial slip·PSD/제약 보존 | 독립 normal flux·higher moments |
| PHY-03 | shared beta radio count의 joint marking·cross covariance | 공동 3D beta, SED/LSS/selection |
| PHY-04 | Gaia/B2/radio/E2 sector의 frame·초기 covariance 관리; R100 drift reuse | scan/AGN law와 model-conditional optical transfer의 관측 qualification |
| PHY-05 | Lie–Codazzi constraint tangent에 한정한 projection | shear 역산과 독립된 normal rho,j,pi |
| PHY-06 | R98 1-loop와 exact feedback의 차이 및 기억 오차경계 | 동일 Einstein–kinetic history와 heldout higher multipoles |
| PHY-07 | radial/depth 비교의 공동 선택·공통장·G_F 오차 | actual same-system transport와 cross-depth law |

기존 60-node DAG에 새 node를 추가하지 않았다. 구조적으로 해결한 수학적 소문제와 실제 과학적 admission은 구분한다.

## 9. 다음 개발을 좁히는 결정

**우선 채택: radio/overlap의 joint selected-count kernel.** 기존 R100 exposure·reselection 결과를 재사용하여 SQ-RADIO, V04/V05, PHY-03/PHY-07 및 SQ-CROSS-COV 경로에 exact q_AB와 common-field PGF를 연결한다. 중첩성, source/component 구별, 실제 mask/mark/SED를 입력으로 받는다. joint support 위반과 cross-covariance를 acceptance로 삼는다. D05와 M06의 자료·law 의무를 제거했다고 표시하지 않는다.

**기존 CF4 경로에는 R99 law를 보존한 source qualification을 이어 붙인다.** 새 R100 intake를 사용하여 method zero-point, group membership, 중복 source, selection과 common velocity field를 함께 명시한다. DP를 써도 현재 copula scenario가 관측으로 확인된 physical velocity law로 바뀌지는 않는다. D02/M01, SQ-CF4/H02/H04의 completion은 이 qualification에 달려 있다.

**MZ는 하나의 source block이 준비될 때만 physics 적용으로 진입한다.** 가장 가까운 조건부 대상은 R98 복사–전단 feedback이다. 실제 constrained A,B,C,D와 initial law를 확보한 뒤 full/reference, exact memory, local surrogate를 동일 관측량으로 비교한다. pole 수를 고정해 맞추기보다 x와 특히 Pi/F/G_F의 허용오차로 필요한 기억 차수를 정한다.

**Optical·CMB·Lie flux의 외부 입력은 별도 의무로 남긴다.** 직접 optics가 이미 효율적이면 그대로 사용한다. 관측 covariance, normal flux, native low-ell transfer를 DP/MZ formalism으로 대신하지 않는다. 없는 source 값은 가정값·scenario로 표시하거나 unresolved로 유지한다.

이렇게 하면 새로운 거대 연구축을 하나 더 만드는 대신, 기존 축의 “어떤 근사를 언제 충분하다고 볼 것인가”와 “어떤 입력을 실제로 더 가져와야 하는가”가 구체화된다.

## 10. 재현 가능한 산출물과 검증 범위

실제 작업 디렉터리:

/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/AUX_DP_MZ_20261123/

| 파일 | 내용 |
|---|---|
| DP_THEORY.md, DP_SOURCES.json | DP 유도·source map·blocker별 적용 범위 |
| dp_checks.py, DP_RESULTS.json | 정상순서·thinning·joint PGF/PMF·selection·chemistry 검산 |
| MZ_THEORY.md, MZ_SOURCES.json | MZ 유도·비정상/초기 law·제약/frame·legacy 판정 |
| mz_checks.py, MZ_RESULTS.json | exact/local/1-loop 비교·초기 covariance·R98 모멘트 검산 |
| INTEGRATION_THEORY.md | 결합 MMPP 유도·five-view 오차경계·수렴 원칙 |
| combined_checks.py, COMBINED_RESULTS.json, COMBINED_MANIFEST.json | count generator–PGF–memory 교차 계산과 재현 metadata |
| README.md, REVIEW.md, END_STATE.json | 재사용 안내·독립 심사·최종 파일 및 보호한 입력의 identity |
| CONTEXT.json | 기준 checkout·pre-existing 변경·NO PUSH 범위 |

기존 checkout에서 다음과 같이 재현한다. 각 명령은 자신의 결과 JSON을 갱신하므로, 현재 결과를 보존해야 하면 별도 사본을 먼저 둔다.

~~~bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B docs/research_program/observational_publication_20261015/AUX_DP_MZ_20261123/dp_checks.py
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=htt .venv/bin/python -B docs/research_program/observational_publication_20261015/AUX_DP_MZ_20261123/mz_checks.py
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B docs/research_program/observational_publication_20261015/AUX_DP_MZ_20261123/combined_checks.py
~~~

관측 환경은 Python 3.12.3, NumPy 2.5.4, SciPy 1.18.1이며 DP의 유한 symbolic 검산은 SymPy 1.14.0을 사용했다. 세 스크립트의 실제 실행은 완료되었다. 검증 주장은 선언한 유한 모형과 범위에 한정된다.

Wolfram context/evaluator는 연결·내부 오류로 사용할 수 없었다. 따라서 Wolfram 검증이나 네 축 CAS 통과를 주장하지 않는다. 직접 유도와 별도 수치 표현 사이의 대조가 이번 근거다. 첫 MZ 실행의 import-path 실패와 수정 이력은 결과 JSON에 보존되어 있다.

## 11. 확인한 문헌

[1] L. Peliti (1985), Path integral approach to birth-death processes on a lattice. J. Physique 46, 1469–1483.  
[저자 원문](https://www.peliti.org/Publications/pathIntegrals.pdf) · [DOI](https://doi.org/10.1051/jphys:019850046090146900)

[2] K. J. Wiese (2016), Coherent-state path integral versus coarse-grained effective stochastic equation of motion: From reaction diffusion to stochastic sandpiles. Phys. Rev. E 93, 042117.  
[arXiv:1501.06514](https://arxiv.org/abs/1501.06514) · [DOI](https://doi.org/10.1103/PhysRevE.93.042117)

[3] G. Last and M. Penrose, Lectures on the Poisson Process, author version 2017-08-21. Marking theorem §5.2, Cox variance §13.2.  
[저자 원문](https://stoch.math.kit.edu/img/Last/lastpenrose2017.pdf)

[4] A. J. Chorin, O. H. Hald and R. Kupferman (2002), Optimal prediction with memory. Physica D 166, 239–257.  
[저자 원문](https://math.berkeley.edu/~chorin/CHK02.pdf)

[5] H. Meyer, T. Voigtmann and T. Schilling (2017), On the “generalized Generalized Langevin Equation.”  
[arXiv:1706.00658](https://arxiv.org/abs/1706.00658) · [DOI](https://doi.org/10.1063/1.5006980)

[6] M. te Vrugt, S. Hossenfelder and R. Wittkowski (2021), Mori–Zwanzig Formalism for General Relativity: A New Approach to the Averaging Problem. Phys. Rev. Lett. 127, 231101.  
[arXiv:2107.11497](https://arxiv.org/abs/2107.11497) · [DOI](https://doi.org/10.1103/PhysRevLett.127.231101)

보조 비교: Rubin, Lawler, Sollich and Ng의 biochemical subnetwork memory 연구는 숨은 bulk의 noise와 memory를 함께 남기는 선행 경로다. nonlinear 저잡음 근사 등의 조건을 따로 읽어야 하며 cosmological chemistry validation을 대신하지 않는다.  
[arXiv:1402.0749](https://arxiv.org/abs/1402.0749)

## 12. 근거 상태

- Established / literature-supported: DP의 정상순서·경로적분, marking/Cox 구조, MZ projection과 memory, GR-MZ 선행연구.
- Derived: 이 문서의 specified-model 공동 선택/covariance, raw 비정상 소거, 국소 잔차, MMPP bridge, 다섯 뷰의 조건부 오차경계.
- Numerically checked / implementation-verified: 지정한 Gamma–Cox, closed-cell, 유한 MZ/MMPP 사례와 기존 R98 모멘트 구적.
- Unresolved / blocked: 실제 survey/source law, full kinetic Jacobian, 외부 transfer/독립 flux/optical motion 입력 및 canonical node admission.
- 이번 범위 밖: production likelihood 통합, 새로운 native solver, DAG 상태 승격, Git 게시.


## 13. 독립 심사와 종료 상태

작성에 참여하지 않은 별도 reviewer가 세 theory note, 세 script, 실제 결과 파일과 canonical 의미를 한 차례 검토했다. Reviewer는 계산을 재실행하지 않았으며, 원문을 새로 검색하거나 파일/Git를 수정하지 않았다. 핵심 generator·PGF·MMPP·MZ 항등식에서 채택을 막는 부호·정규화 오류를 찾지 않았다. 다음의 적용 범위는 명시적으로 보강했다.

1. Generator closure 조건은 모든 admissible initial states/laws의 strong lumpability에 대한 것이며, 특수 초기 law의 weak closure와 구별한다.
2. 비정상 local-error bound는 homogeneous forcing, invertible D, C¹ E의 조건에서 사용한다. Hidden forcing d가 있으면 추가항을 유지한다.
3. DP density dilution의 3H는 물질 고유시간에 대한 d ln(V)/d tau이며 normal-frame H와 자동 동일시하지 않는다.
4. 기록된 covariance 28 비교모형은 공통 intensity 아래 별도 Poisson catalogs다. q_A=.4,q_B=.7인 같은 parent의 q_AB=0 thinning으로 해석하지 않는다.

첫 두 수정은 reviewer가 실제로 다시 읽어 확인했고, 뒤의 명시 보강은 root가 최종 본문과 author closeout을 확인했다. 수치 모형·결과·tolerance는 바꾸지 않았다. 이 심사는 production admission이나 네 축 CAS 판정이 아니다.

최종 identity 확인에서 HEAD는 시작과 동일했고 stage된 파일은 0개였다. Canonical science DAG, R69 정의 문서, R100 intake receipt의 hash는 시작과 같았다. 세 실행 script의 실제 hash는 결과에 기록한 hash와 일치하며, 결합 계산 결과의 hash도 manifest와 일치한다. 기존 R99의 두 tracked 변경은 그대로 남아 있다. 이번 보조 연구는 그 파일들을 수정하지 않았다.

현재 R100 참조 결과의 identity:
- OPTICAL_DRIFT_RESULTS.json: 22a18d49b675f0c7ee889ef545a1abb7904364eea6540de72470f0b17515eab7
- RADIO_EXPOSURE_SELECTION_RESULTS.json: bb769fe05e7cdd715e8ec5f7fe419d61c5bd33d030103d4f4200aefc5d81b142

보고서의 수치들은 각 RESULTS에 연결되며, 전체 유도·원전 위치·실패 이력·재현 명령은 위 실제 작업 디렉터리에 보존되어 있다. 여기서 완료한 것은 보조 이론과 유한 구현 검산이며, 외부 입력이 필요한 science node의 완결로 표시하지 않았다.
