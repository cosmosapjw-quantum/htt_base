# R46: 관심 estimand posterior를 보존하는 데이터 압축

**2026-11-09 | 문헌 근거 + 직접 유도 + Wolfram 검산 + synthetic experiment**

## 질문과 결론

R45는 finite model-index posterior의 압축 손실을 다뤘다. R46은 물리적으로 더 직접적인 관심량 `Psi=g(Lambda)`의 posterior를 대상으로 한다. 전체 latent parameter `Lambda`의 posterior는 보존하지 못해도 지정된 estimand posterior만 보존할 수 있다. 답은 그렇다.

## 1. Target-posterior information-loss identity

하나의 prior-predictive 확률공간에서 latent variable `Lambda`, raw observation `Y`, measurable target map `g`, common deterministic summary map `T`를 둔다. `Psi=g(Lambda)`, `S=T(Y)`라 하자. 관련 공간이 standard Borel이면 필요한 regular conditional probability kernels를 선택할 수 있다. KL은 measure-theoretic extended-real KL로 해석한다.

[
\boxed{\mathbb E D_{\rm KL}(P_{\Psi\mid Y}\Vert P_{\Psi\mid S})
=I(\Psi;Y\mid S).}
\tag{1}
]
이는
[
I(\Psi;Y\mid S)
=\mathbb E D_{\rm KL}(P_{\Psi\mid Y,S}\Vert P_{\Psi\mid S})
]
와 `S=T(Y)`에 의한 `P(Psi|Y,S)=P(Psi|Y)`에서 곧바로 나온다.

`Psi=g(Lambda)`이므로 conditional chain rule:
[
I(\Lambda;Y\mid S)
=I(\Psi;Y\mid S)+I(\Lambda;Y\mid\Psi,S),
]
따라서
[
\boxed{0\le I(\Psi;Y\mid S)\le I(\Lambda;Y\mid S).}
\tag{2}
]
Target posterior 손실이 0일 필요충분조건은
[
\boxed{\Psi\perp Y\mid S
\iff P_{\Psi\mid Y}=P_{\Psi\mid S}\quad P_Y\text{-a.s.}}
\tag{3}
]
이다.

실수값 `Psi`가 square-integrable이면 squared-error Bayes risk에 대해
[
R_Y=\mathbb E\operatorname{Var}(\Psi\mid Y),\quad
R_S=\mathbb E\operatorname{Var}(\Psi\mid S)
]
이고 tower property/conditional variance decomposition으로
[
\boxed{R_S-R_Y
=\mathbb E[(\mathbb E[\Psi\mid Y]-\mathbb E[\Psi\mid S])^2]
=\mathbb E\operatorname{Var}(\mathbb E[\Psi\mid Y]\mid S).}
\tag{4}
]
를 얻는다. 식 (1)-(3)은 finite second moment가 필요 없고 식 (4)에만 `Psi in L2`가 필요하다. Vector target의 Euclidean loss에는 square를 squared norm으로, variance를 covariance trace로 바꾼다.

## 2. Gaussian linear model: exact row-space criterion

[
\Lambda\sim N_p(\mu,\Sigma),\qquad
Y\mid\Lambda\sim N_n(H\Lambda,R),
]
`Sigma ≻ 0`, `R ≻ 0`이고 H, Sigma, R과 prior가 고정·알려져 있다고 하자. 다음을 둔다.
[
V=H\Sigma H^T+R,\qquad
C=\Sigma-\Sigma H^TV^{-1}H\Sigma.
]
그러면
[
\Lambda\mid Y=y\sim N_p(\mu+\Sigma H^TV^{-1}(y-H\mu),C).
]

`Psi=A^T Lambda`에 대해
[
K=A^T\Sigma H^TV^{-1},\quad Q=A^TCA.
]
따라서
[
\Psi\mid Y=y\sim N_q(A^T\mu+K(y-H\mu),Q).
]
공통 선형 요약 `S=B^T(Y-Hmu)`에 대해 B의 열이 독립이고 target posterior covariance가 support에서 nondegenerate이면
[
\boxed{P_{\Psi\mid Y}=P_{\Psi\mid S}\ a.s.
\iff \operatorname{row}(K)\subseteq\operatorname{row}(B^T).}
\tag{5}
]
이다. 그러므로 target posterior를 보존하는 선형 summary의 최소 rank는
[
\boxed{r_{\min}=\operatorname{rank}
[A^T\Sigma H^T(H\Sigma H^T+R)^{-1}].}
\tag{6}
]
이고 K의 row-space 기저를 취해 달성한다. 최소성은 이 고정 prior/likelihood 아래의 **선형 요약 클래스**에 한정한다.

**증명 요지.** Full-data target posterior covariance Q는 data-independent이고 posterior mean의 data dependence는 Kx, x=Y-Hmu뿐이다. Row-space 포함이면 Kx가 B^Tx의 함수이므로 target posterior kernel 전체가 S로 결정된다. 역으로 두 posterior kernel이 같으면 Kx가 B^Tx로 복원 가능해야 한다. X는 양의 정부호 V를 갖는 nondegenerate Gaussian이므로 이는 K가 ker(B^T)를 소거하는 것과 동치이고, row-space 포함 조건을 준다. Target covariance가 singular하면 target affine support로 제한한다.

## 3. Synthetic examples

**A. Full latent posterior는 손실, target posterior는 보존.** `p=n=2`, `mu=0`, `Sigma=H=R=I2`. 그러면 `Lambda|y ~ N2(y/2,I2/2)`. `Psi=lambda1+lambda2`, `S=y1+y2`이면
[
\Psi\mid Y=\Psi\mid S\sim N(S/2,1).
]
Target loss는 0이나 full-latent posterior loss는 `0.5 log 2 = 0.3465735903 nats`이고 contrast direction은 버려진다.

**B. Non-aligned summary.** 같은 model에서 `Psi=lambda1`, `S=y1+y2`이면
[
\Psi\mid Y=y\sim N(y_1/2,1/2),\quad
\Psi\mid S=s\sim N(s/4,3/4).
]
이에 따라 expected KL은 `0.5 log(3/2)=0.2027325541 nats`, MMSE risk gap은 `1/4`. 40,000 prior-predictive draws에서 KL `0.2016912 ± 0.0011619` nats (MCSE), risk gap `0.2484380 ± 0.0017429`를 얻었다.

**C. Isotropic radial target.**
[
\Lambda\sim N_d(0,\tau^2I),\quad Y\mid\Lambda\sim N_d(\Lambda,\sigma^2I),\quad
\Psi=\|\Lambda\|^2.
]
`c=tau²/(tau²+sigma²)`, `v=tau² sigma²/(tau²+sigma²)`이면 `Lambda|y ~ N_d(cy,vI)`이며
[
\Psi/v\mid y\sim\chi'^2_d(c^2\|y\|^2/v).
]
따라서 target posterior는 `||Y||²`만으로 결정된다. d≥2에서 full vector posterior 방향은 보존하지 않는다.

**D. Anisotropic counterexample.** `Lambda~N(0,diag(1,4))`, `Y|Lambda~N(Lambda,I2)`, `Psi=||Lambda||²`. 같은 norm인 `ya=(1,0)`, `yb=(0,1)`에서 target posterior means는 각각 1.55, 1.94다. 차이 0.39이므로 norm summary는 불충분하다. radial quantity라는 이름이 아니라 prior-likelihood 회전 대칭성이 조건이다.

## 4. 17D mock 결과

Synthetic chart 17D, observation 23D, target 2D. 두 target은 서로 다른 chart block의 선형 결합이며 실제 STF invariant나 관측 추정량이 아니다. 고정된 Gaussian prior/design/noise 아래 40,000 prior-predictive draw:

| Quantity | Result |
|---|---:|
| Target-aligned summary rank | 2 |
| Exact target posterior KL | 1.11e-16 nats (roundoff; mathematically 0) |
| Full 17D posterior KL under exact target summary | 6.6203963 nats |
| Drop one target direction: target KL | 0.6805926 nats |
| Same lossy summary: full latent KL | 7.5262260 nats |
| 2D misaligned target KL | 0.2016912 ± 0.0011619 nats (MCSE) |
| Analytic 2D misaligned KL | 0.2027326 nats |
| Anisotropic same-norm target posterior-mean gap | 0.39 |

Target-MMSE risk gap from sample posterior means and covariance-trace difference agree within Monte Carlo uncertainty. Wolfram Language independently verified the 2D aligned/misaligned row-space conditions, `Log[3/2]/2`, `1/4`, and anisotropic gap `39/100`.

## 5. 문헌과 novelty 범위

Partial/target/Bayesian sufficiency는 기존 개념이다. 식 (1)-(4)는 conditional MI와 L2 conditional projection의 표준 항등식이다. 식 (5)-(6)은 fixed-prior Gaussian linear model의 exact specialization이며 새 일반 정리라고 주장하지 않는다.

- D. A. S. Fraser (1956), “Sufficient Statistics with Nuisance Parameters,” *Annals of Mathematical Statistics*. https://doi.org/10.1214/aoms/1177728191
- K. Furmańczyk & W. Niemiro (1998), “Sufficiency in Bayesian Models,” *Applicationes Mathematicae* 25, 113–120. https://doi.org/10.4064/am-25-1-113-120
- L. Giraldi, O. P. Le Maître, I. Hoteit & O. M. Knio (2018), “Optimal projection of observations in a Bayesian setting,” *Computational Statistics & Data Analysis* 124, 252–276. https://doi.org/10.1016/j.csda.2018.03.002
- A. F. Heavens, R. Jimenez & O. Lahav (2000), MOPED. https://arxiv.org/abs/astro-ph/9911102
- J. Alsing & B. Wandelt (2018), “Generalized massive optimal data compression,” *MNRAS Letters* 476, L60–L64. https://doi.org/10.1093/mnrasl/sly029

MOPED/score compression의 Fisher-information 보존은 finite-sample posterior-kernel의 완전 보존과 동치가 아니다. R46 row-space criterion은 prior-dependent target posterior의 exact preservation 조건이다.

## 6. HTT 연결 및 한계

R46 17D target functionals는 synthetic chart-space 예제다. 실제 shear/vorticity/acceleration invariant를 만들려면 authoritative tensor basis, STF Gram matrix, metric contraction, 단위와 convention을 먼저 고정해야 한다. STF component를 Gram 없이 Euclidean norm으로 취급하지 않는다.

Model-dependent covariance, selection, mask/window, calibration, foreground, transfer operator가 다르면 K도 모델에 따라 달라진다. 한 모델 내 target posterior 보존은 cross-model evidence/Bayes-factor나 model-index posterior 보존을 뜻하지 않는다. 비선형 target은 식 (1),(4)를 이용한 approximate-compression objective로 다루되 finite-dimensional exact summary의 존재를 가정하지 않는다.

All results are synthetic. Survey data, physical Bianchi transfer, Cobaya production sampling and empirical calibration are NOT RUN. Empirical detection/Bianchi-family identification remain HOLD. HTT `T=(x,Q,Pi,F,G_F)` remains one joint posterior/compatibility push-forward, not independent likelihood factors.
