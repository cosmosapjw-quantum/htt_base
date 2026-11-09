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

