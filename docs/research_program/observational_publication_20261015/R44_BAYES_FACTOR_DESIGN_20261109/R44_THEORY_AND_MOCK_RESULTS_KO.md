# R44: Bayes-factor 충분성 정리와 nuisance-aware redshift/anchor 설계

- 기준일: 2026-11-09 (Asia/Seoul)
- 부모 기준: R43 \`8e70c15da595ecfcd25e097e44fbd13f3aa59903\`
- 연구 범위: 최신 tensorized posterior-pushforward \`T=(x,Q,Pi,F,G_F)\`와 물리적 generative competitor/readout의 비교. scalar \`x_C\` 대 tensor 5변수의 비교가 아님.
- 상태: exact statistical results + synthetic linear-Gaussian experiment
- seed: \`20261109\`

## 1. 연구 질문과 결론

R43은 nuisance score를 제거한 local functional-identifiability criterion과 deterministic-readout data-processing inequality를 확립했다. R44는 그 다음 질문을 다룬다.

> 동일한 raw observation에 작용하는 공통 readout가 경쟁 generative model 사이의 Bayes factor를 정확히 보존하려면 무엇이 필요한가? 또한 실제 연구 설계에서 redshift shell과 independent anchor를 어떻게 배분해야 관심 contrast를 식별·추정할 수 있는가?

주요 결론은 다음과 같다.

1. 임의의 두 model-predictive law \`P0,P1\`에서 공통 deterministic statistic \`T(Y)\`가 exact Bayes factor를 보존할 필요충분조건은 likelihood ratio \`dP1/dP0\`가 \`sigma(T)\`-measurable인 것이다.
2. 모든 competitor가 동일한 nuisance-integrated covariance와 하나의 고정 linear design chart의 submodel인 Gaussian family에서는 \`q=X^T C^{-1}(y-mu)\`가 모든 pairwise Bayes factor의 공통 sufficient statistic이다. 같은 chart와 고정 prior의 full Gaussian reference posterior \`N(m,V)\`는 \`q=V^{-1}m-B^{-1}b\`를 복원한다. 이때 \`V\`가 data-independent이므로 posterior mean \`m\`만으로도 충분하다.
3. 이는 일반 명제가 아니다. 모델별 covariance, selection/window, nuisance marginalization 또는 model-dependent readout이 달라지면 추가 quadratic/selection 통계가 필요할 수 있고, 같은 고정-covariance score를 갖는 두 데이터가 서로 다른 covariance-model Bayes factor를 가질 수 있다.
4. \`||beta_MO||\`는 spherical prior와 rotationally invariant data metric 같은 특수 대칭 아래에서만 sufficient할 수 있다. anisotropic survey geometry에서는 방향이 model evidence에 중요하다.
5. \`delta=beta_RM-beta_MO\` 추정에서 c-optimal shell/anchor 설계는 D-optimal information-volume 설계와 다르다. 이 synthetic design에서는 c-optimal allocation이 D-optimal allocation보다 해당 contrast variance를 14.1% 줄였다. independent beta_MO anchor가 없으면 beta_MO와 intrinsic dipole 사이에 null fibre가 남아 contrast가 식별되지 않는다.

## 2. 정리 A: common deterministic readout의 exact Bayes-factor 보존 조건

**전제.** 관측공간의 두 probability law \`P0,P1\`가 \`P1 << P0\`를 만족한다고 하자. \`T:Y -> Z\`는 두 모델에 동일하게 적용하는 measurable deterministic map이고, \`P_i^T=P_i o T^{-1}\`를 push-forward law라 쓰자. Raw likelihood ratio는

\[
L(Y)=\frac{dP_1}{dP_0}(Y)
\]
이다. Prior odds를 고정하면 Bayes factor는 \`L(Y)\`와 같은 정보를 가진다.

**정리.** \`T\`가 모든 관측에서 exact binary Bayes factor를 보존할 필요충분조건은

\[
\boxed{L(Y)=g(T(Y))\quad P_0\text{-a.s.}}
\]
를 만족하는 measurable \`g\`가 존재하는 것이다. 즉 raw likelihood ratio가 \`sigma(T)\`-measurable이어야 한다.

**증명.** Push-forward likelihood ratio는 conditional expectation으로 주어진다.

\[
\frac{dP_1^T}{dP_0^T}(T(Y))
=\mathbb E_{P_0}[L(Y)\mid\sigma(T)]\quad P_0\text{-a.s.}
\]
따라서 readout에서 계산되는 Bayes factor는 raw likelihood ratio의 \`T\`-조건부 평균이다. 이것이 모든 raw observation에서 \`L(Y)\`와 일치할 필요충분조건은 \`L=E[L|T]\` a.s.이며, 이는 \`L\`이 \`sigma(T)\`-measurable인 것과 동치다. regular conditional distributions가 존재하는 표준 Borel setting에서는 동등하게

\[
P_1(\cdot\mid T=t)=P_0(\cdot\mid T=t)
\quad P_0^T\text{-a.e. }t
\]
로 쓸 수 있다. 즉 readout이 주어진 뒤 남는 raw-data conditional experiment가 model label에 의존하지 않아야 한다. □

다중 model family \`{P_M}\`에서는 기준 model \`M0\`에 대한 모든 likelihood ratios \`dP_M/dP_M0\`가 \`sigma(T)\`-measurable이면 전체 pairwise Bayes factors를 보존한다. model-dependent map \`T_M(Y)\`들은 공통 statistic이 아니므로 이 정리를 바로 적용할 수 없다. 그런 경우 각 model이 생성한 readout distribution과 그에 대한 likelihood를 별도로 정의해야 한다.

## 3. 정리 B: KL/TV data processing 및 equality의 범위

\`T\`가 deterministic이므로

\[
D_{KL}(P_1^T\Vert P_0^T)\le D_{KL}(P_1\Vert P_0),\qquad
TV(P_1^T,P_0^T)\le TV(P_1,P_0).
\]

KL chain rule은

\[
D_{KL}(P_1\Vert P_0)=D_{KL}(P_1^T\Vert P_0^T)
+\mathbb E_{P_1^T}\!\left[D_{KL}\{P_1(\cdot\mid T)\Vert P_0(\cdot\mid T)\}\right]
\]
를 준다. 유한 KL 및 regular conditional law 아래 KL equality는 conditional laws가 일치하는 경우, 즉 위 likelihood-ratio measurability 조건과 동치다. TV equality는 더 약하다. TV는 optimal binary decision region의 보존만 요구할 수 있으므로 likelihood ratio 전체 보존을 뜻하지 않는다. equal prior의 minimum binary error \`(1-TV)/2\`는 deterministic compression으로 개선될 수 없다.

이 결과는 five-family readout이 raw observation보다 더 많은 model evidence를 만들어낸다고 주장하는 것을 막는다. readout의 가치는 gauge/null-fibre의 의미 보존, calibration, directional functionals, covariance-aware depth, robustness 또는 특정 decision task에서의 usability로 정식화해야 한다.

## 4. 정리 C: 공통 covariance Gaussian submodel family에서의 exact sufficient score

**전제.** nuisance Gaussian block를 적분한 후

\[
y\mid\beta\sim\mathcal N(\mu+X\beta,C),\qquad C\succ0
\]
라 하자. 모든 후보 model \`M_k\`는 하나의 고정 chart \`X\`의 submodel이며 \`beta=A_k theta_k\`로 표현된다. 모든 model은 동일한 \`mu,C\`를 사용하지만 proper prior \`pi_k(theta_k)\`는 달라도 된다. 다음을 정의한다.

\[
r=y-\mu,\qquad q=X^TC^{-1}r,\qquad G=X^TC^{-1}X.
\]

그러면

\[
p(y\mid\theta_k,M_k)=h(y)\exp\left[\theta_k^TA_k^Tq
-\frac12\theta_k^TA_k^TGA_k\theta_k\right]
\]
이고

\[
h(y)=(2\pi)^{-n/2}|C|^{-1/2}\exp[-r^TC^{-1}r/2]
\]
는 모든 후보 model에 공통이다. 따라서

\[
p(y\mid M_k)=h(y)\int\exp\left[\theta^TA_k^Tq
-\frac12\theta^TA_k^TGA_k\theta\right]\pi_k(d\theta)
\]
이며 임의의 pairwise Bayes factor \`BF_{k l}\`는 \`q\`와 고정 design Gram \`G\`, model mapping 및 priors만으로 계산된다. Gaussian coefficient prior는 필요조건이 아니다.

**Full Gaussian reference posterior.** 하나의 model-independent reference chart에서 \`beta ~ N(b,B)\`를 쓰면

\[
V=(B^{-1}+G)^{-1},\qquad m=V(B^{-1}b+q),
\]

따라서

\[
\boxed{q=V^{-1}m-B^{-1}b.}
\]
\`X,C,B,b\`가 고정이면 \`V\`는 데이터에 의존하지 않는다. 그러므로 \`m\` 자체가 \`q\`의 invertible encoding이며, full posterior \`(m,V)\`와 동일한 model evidence를 보존한다. 이는 **고정된 공통 covariance와 하나의 full chart 내 submodel family**에 대한 exact result이다.

**중요한 적용 경계.** 실제 \`x\`가 이 full-chart posterior score를 충분히 인코딩하는지는 별도 구현 질문이다. \`x\`에 일부 tensor carriers, norm, samplewise functionals만 존재한다는 사실만으로 위 sufficient-statistic 조건을 만족하지 않는다. \`Q,Pi,F,G_F\`가 \`x\` 및 고정 design/null metadata의 deterministic post-processing이라면 evidence를 추가 생성하지 않는다. 다만 x가 충분하지 않은 경우 다른 family가 보완적인 진단·decision utility를 제공할 수는 있다.

## 5. Counterexample: covariance가 달라지면 fixed-C score는 충분하지 않다

두 model이 각각 \`P0=N(0,C)\`와 \`P1=N(0,C+tau^2 vv^T)\`를 생성하도록 하자. \`q=X^T C^{-1}y\`의 null space에서 \`h\`를 골라 \`q(0)=q(h)=0\`으로 만들 수 있다. 그런데 covariance-model log Bayes factor는 residual quadratic form에 의존하므로 일반적으로 \`log BF(0) != log BF(h)\`다.

이번 mock은 \`q\` 차이가 \`9.1e-13\` 이하인 두 자료를 만들었지만 covariance-alternative log BF 차이는 **0.2222222**였다. 따라서 fixed-C mean score는 model-dependent covariance/transfer/noise competition을 보존하지 못한다. 실 관측에서 mask, window, selection, foreground, calibration covariance가 model-dependent하면 이 항을 실제 likelihood에 포함해야 한다.

## 6. Counterexample: scalar norm와 beta_MO-only readout

### 6.1 Norm의 대칭 조건

\`y|beta ~ N(beta,C)\`와 spherical prior \`beta~N(0,tau^2 I)\`에서 \`C=sigma^2 I\`이면 binary null-vs-boost Bayes factor는 \`||y||\`만으로 표현된다. 이 특수 대칭은 scalar norm의 sufficiency를 허용한다. 반면 anisotropic \`C=diag(0.35,1,2.8)\`에서는 posterior mean norm이 정확히 같은 두 관측에도 log BF 차이가 **0.3555556**이었다. 따라서 불완전한 sky mask나 anisotropic noise/window가 존재하는 실제 실험에서 방향을 norm으로 압축하려면 별도의 symmetry proof가 필요하다.

### 6.2 beta_MO vector만 보존하면 global-tilt competitor가 누락된다

full common-chart reference posterior에서 \`m_betaMO\`가 수치적으로 동일한 두 자료를 구성했다. 두 자료의 beta_MO posterior mean-vector 차이는 \`2.4e-20\`였지만, \`M1=local boost\`와 \`M2=global tilt + local boost\`의 log-BF 차이는 각각 \`0.00293\`, \`0.12707\`이었다. beta_MO-only vector readout는 beta_RM가 포함된 경쟁 model을 식별하는 공통 sufficient statistic이 아니다.

## 7. Nuisance-aware redshift-shell/anchor design

관심 물리 parameter \`beta=(beta_RM,beta_MO)\`와 nuisance \`eta=(d_intrinsic,c_z)\`를 둔다. synthetic shell mean은

\[
\mu_s=g(z_s)\beta_{RM}+\beta_{MO}+d_{intrinsic}+c_z z_s,
\qquad g(z)=\frac{z}{z+0.12},
\]
이고 independent low-z anchor는 \`beta_MO\`를 측정한다. 모든 response, noise 및 shell geometry는 synthetic이다.

shell covariance는

\[
C_{ss'}=\delta_{ss'}\frac{\sigma_{stat}^2}{n_s}
+\sigma_{cv}^2\exp[-|z_s-z_{s'}|/L_{corr}],
\]
이며 anchor variance는 \`sigma_anchor^2/n_anchor\`다. 전체 Fisher를 \`(beta,eta)\`로 partition하면 nuisance-projected information은

\[
I_{eff}(w)=F_{\beta\beta}(w)-F_{\beta\eta}(w)F_{\eta\eta}(w)^{-1}F_{\eta\beta}(w).
\]

관심 contrast \`delta=c^T beta\`, \`c=(1,-1)\`에 대한 c-optimal allocation은

\[
w_c^*=\arg\min_{w\in\mathcal W}c^TI_{eff}(w)^{-1}c,
\]
이고 D-optimal allocation은 \`log det I_eff\`를 최대화한다. singular nuisance block에서는 projection/generalized inverse를 사용하고 target이 \`range(I_eff)\`에 속하는지 검사한다. cross-shell covariance를 독립 shell sum으로 대체하지 않는다.

