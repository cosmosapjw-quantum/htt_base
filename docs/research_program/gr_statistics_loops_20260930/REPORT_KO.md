# 관측 광학의 국소 역산과 운동학 식별: GR·통계 연구 보고서
2026-09-30. 이번 연구는 특정 Bianchi type을 선택하지 않는다. 광학적 운동학, Einstein–물질계의 국소 존재, 관측 추론을 구별하여 연구했다.

## 1. 이번에 달라진 결론

순수 GR 연구에서는 **절대 적색편이 절편과 면적거리 기울기를 함께 알면, 가속도를 미리 0으로 놓지 않고도 광원계의 속도와 대칭 속도 미분을 정확히 복원할 수 있다**는 완전한 국소 역산을 정리했다. 와도 세 성분은 이 관측 채널에 남는 자유도다. 이를 부정적 결론으로 끝내지 않고, 별도의 정보가 어떤 자유도를 제거하는지 명시하는 방향으로 확장한다.

물질계에서는 기존의 “임의 metric에서 stress를 정의한 반례”보다 강한 결과를 얻었다. **하나의 고정된 causal EOS, 나아가 하나의 고정된 scalar 작용에서도, 한 점의 전체 곡률과 stress 및 energy-frame gap을 같게 유지하면서 가속도를 무한히 크게 만들 수 있다.** 필요한 것은 전역 별 모형이 아니라 국소 해의 존재이며, 이 범위는 증명에서 유지된다. 대응하는 긍정적 결과는 stress의 미분 또는 metric의 3차 미분까지 제공하면 비퇴화 energy frame의 전체 1차 미분을 복원한다는 것이다.

통계 연구에서는 “tensor가 scalar보다 좋다”는 일반적 표어를 구체화했다. **다중극별 power가 정확히 같아도 geodesic 여부가 다른 두 광원계를 구성했다.** 동시에 교차 수축을 보존하는 하나의 회전 불변 스칼라로 geodesicity를 판별할 수 있음을 보였다. 정보 손실의 원인은 스칼라 표현 자체가 아니라, 서로 다른 성분의 상대 방향을 지우는 압축이다.

첫 GR 묶음 18개 진술과 후속 통계 묶음 12개 진술에 대해서는 별도 작성자가 아닌 검토자가 증명을 재구성했다. 확정 판정과 조건은 각각 [GR 독립 검토](reviews/GR_INDEPENDENT_DECISION.md), [통계 독립 검토](reviews/STATISTICS_INDEPENDENT_DECISION.md)에 있다. 추가 PDF에서 전개한 복원·오차경계는 [긍정적 확장 독립 검토](reviews/POSITIVE_EXTENSION_DECISION.md)에 별도로 판정했다. 추가 16개 기록 중 15개는 명시한 범위에서 성립하며, 전체 nonlinear CMB 정확도·parameter identification이라는 더 강한 목표는 보류했다. 이 수는 신규 정리의 수가 아니다. 여기서 분석적 성립은 문헌상 우선권이나 투고 준비 완료를 뜻하지 않는다. 표준 항등식과 이번에 구성한 예·역산·오차경계를 구별했다.

## 2. 원전 대조로 교정한 사항

| 항목 | 교정 후 사용하는 진술 |
|---|---|
| Ellis의 와도 규약 | 책의 velocity-first 인덱스와 본 연구의 derivative-first 인덱스는 부호가 반대다. \(U=cu\), \(\Omega_{ab}=D_{[a}U_{b]}\)라면 \(\omega^{\rm Ellis}_{ab}=-\Omega_{ab}/c\). signed drift 행렬과 혼용하지 않는다. |
| 가속도 단위 | \(B_{ab}=\nabla_{(a}U_{b)}\)이면 \(A_a=2c B_{ab}u^b\). \(B\)를 unit \(u\)의 미분으로 정의할 때만 계수가 \(2c^2\)다. |
| 광선 미분과 시간 drift | 한 광선을 따른 에너지·방향 미분은 관측자의 시간에 따라 같은 source를 추적하는 drift와 다르다. |
| boost와 tilt | 한 사건의 두 4-속도 비교는 local boost다. 물질의 global tilt에는 비교할 공간 궤도와 그 법선이 추가로 필요하다. |
| 절편 | boost가 있으면 \(Z_0=\lim(1+z)\)가 방향별로 1과 다를 수 있다. fit에서 이를 강제로 1로 두면 정보가 사라진다. |
| 거리 | reciprocity와 photon conservation 아래 \(d_A=d_L/(1+z)^2\). boosted observer의 \(d_L\) 기울기를 그대로 \(d_A\) 기울기로 쓰지 않는다. |
| hierarchy와 MES 확장 | low moment가 작다는 사실은 그 시간·공간 미분이나 collision residual의 상계를 주지 않는다. 분포의 moment 제약과 transport의 폐쇄는 별도 입력이다. |
| almost-EGS | 한 관측자의 작은 정적 CMB anisotropy만으로 영역 전체의 물질·복사·미분 가정을 확인했다고 할 수 없다. |

Ellis–Maartens–MacCallum의 관련 식은 인쇄 pp.74–85, 92–108, 154–165, 283–287을 중심으로 대조했다. 일곱 책의 완독을 주장하지 않으며, 실제 읽은 절·페이지·시각 확인 여부는 [원전 대조표](REFERENCES_AND_CORRECTIONS.md)와 [출처 지도](REFERENCE_MAP.json)에 기록했다.

Maartens 등의 **arXiv:2312.09875v3 식 (37)**에는 다음과 같은 적용 범위 교정이 필요하다. 식 (34b)를
\[
d=-2(HI+\Sigma)v+O(|v|^2)
\]
로 쓰면, 표시된 역산 근사는
\[
-\frac{(HI-\Sigma)d}{2H^2}
=\left(I-\frac{\Sigma^2}{H^2}\right)v+O(|v|^2)
\]
를 반환한다. 고정된 임의 크기의 전단에서 누락항은 속도에 대해 1차다. 따라서 사용식은
\[
v=-\tfrac12(HI+\Sigma)^{-1}d+O(|v|^2)
\]
로 교체하며, 역행렬의 존재와 크기를 명시한다. 기존 근사를 사용하려면 별도의 small-shear 차수 조건이 필요하다. 이는 대조한 v3 식의 arbitrary-shear 해석에 대한 직접 대입 결과이며, 논문 전체의 정확한 boost 법칙이나 발행된 정오표에 관한 주장이 아니다.

## 3. CQG 방향: 통계를 제외한 분석적 결과

### 3.1 완전한 국소 광학 역산과 남는 자유도

서명은 \((-+++)\), \(U=cu\), \(u^2=-1\)로 고정한다. 관측자 unit vector를 \(o\), 하늘의 sourceward 방향을 \(n\), 과거향 null tangent를 \(K=-o+n\), \(o\cdot K=1\)로 정규화한다. 이상적인 절대 절편과 기울기를
\[
Z_0(n)=\zeta_0+\zeta\cdot n,\qquad
H(n)=c\,\partial_{d_A}z|_0=h_0+h_1\cdot n+h_2:nn
\]
로 둔다. \(h_2\)는 대칭 trace-free다.

정확한 운동학적 허용집합은
\[
\zeta_0^2-|\zeta|^2=1,\quad \zeta_0\ge1,
\qquad (h_0,h_1,h_2)\text{는 임의의 실수 계수}
\]
이다. 정의
\[
u=(\zeta_0,\zeta),\quad
S=\begin{pmatrix}h_0&-h_1^{T}/2\\-h_1/2&h_2\end{pmatrix}
\]
에 대해
\[
\boxed{B=S+S(u,u)g,\qquad A=2c\,B u.}
\]
따라서 source frame의 팽창과 전단도 \(hBh\)의 trace와 trace-free 부분으로 복원된다.

증명의 핵심은 두 가지다. 모든 null 방향에 같은 이차형식을 주는 대칭 텐서의 차이는 \(\lambda g\)뿐이고, 정규화 조건 \(B(u,u)=0\)가 그 \(\lambda\)를 결정한다. 모든 허용쌍은 정규좌표에서 선형 속도장을 만든 뒤 정규화하여 실제 매끄러운 국소 광원계로 실현된다.

\(b=Bu\)라 하면 전체 미분은 정확히
\[
\nabla_aU_b=B_{ab}+b_au_b-u_ab_b+\Omega_{ab},
\qquad \Omega_{ab}=-\Omega_{ba},\quad \Omega_{ab}u^b=0.
\]
광학적 scalar 1차 채널은 \(\Omega\)의 세 성분을 고정하지 않는다. 이 진술은 특정 물질의 Einstein 해를 자동으로 구성하지 않는다.

이상적 데이터의 복원 오차도 유한 차이로 제어된다. 두 허용쌍의 rapidity가 \(R\) 이하이고 \(M=\sqrt{\cosh 2R}\), \(L_S=\min(\|S\|_{\rm op},\|\widetilde S\|_{\rm op})\)이면
\[
\|\Delta B\|_F\le(1+2M^2)\epsilon_H+4ML_S\epsilon_Z,
\]
\[
\epsilon_Z=|\Delta u|_E,\qquad
\epsilon_H^2=(\Delta h_0)^2+\tfrac12|\Delta h_1|^2+\|\Delta h_2\|_F^2.
\]
팽창행렬의 eigengap을 요구하지 않는다. norm은 하나의 고정된 관측자 tetrad에서의 Euclidean norm이다. 상수의 최적성은 주장하지 않는다.

### 3.2 기울기만 사용할 때의 정확한 복원 조건

\(A(p)=0\)를 추가하면 \(S^a{}_b\)가 timelike eigenvector를 갖는 것이 필요충분하다. 해당 eigenvalue와 \(B\)는 유일하다. source velocity까지 유일하려면 source-rest spatial expansion의 zero eigenvalue가 없어야 한다. zero eigenvalue가 있으면 호환되는 속도들의 연속집합이 남으며, 그 퇴화에 접근할수록 slope-only 속도 역산은 불안정해진다.

**극복 방법:** 독립적인 절대 절편 또는 source velocity anchor를 추가하면 3.1의 역산을 사용할 수 있다. 전단의 단순한 eigenvalue 중복 자체가 문제가 되는 것은 아니다.

전체 증명: [OPTICAL_THEOREMS.md](gr/OPTICAL_THEOREMS.md), OPT01–OPT09.

### 3.3 energy frame의 전체 운동학: 충분한 미분 차수와 날카로운 상계

\(T u=-\epsilon u\), spatial stress eigenvalues \(p_i\), gap \(\delta=\min_i|\epsilon+p_i|>0\)라 하자. \(D_\mu=h(\nabla_{E_\mu}T)u\)이면
\[
\nabla_{E_\mu}U=-c(\epsilon I+S_T)^{-1}D_\mu.
\]
따라서
\[
\boxed{
\frac{\theta^2}{3}+\|\sigma\|_F^2+2|\omega|^2+\frac{|A|^2}{c^2}
=c^2\sum_{\mu i}\frac{|D_{\mu i}|^2}{(\epsilon+p_i)^2}
\le \frac{c^2}{\delta^2}\sum_\mu |D_\mu|^2.}
\]
이는 알려진 eigenvector 미분 원리를 물리적 rate 분해로 쓴 것이다. perfect fluid는 이 gap estimate를 포화한다. 분모만 알려져서는 수치적 상계가 완성되지 않는다.

**극복 방법:** \(T,\nabla T\) 및 비퇴화 energy-frame 정보를 제공하면 \((\theta,\sigma,\omega,A)\) 전체가 복원된다. Einstein 방정식과 고정된 상수 아래에는 metric 3-jet가 충분하다. 유체 EOS를 사용하는 경우 \(A=-c_s^2D\epsilon/(\epsilon+p)\)이므로 density-gradient 측정·상계가 가속도의 입력을 제공한다.

### 3.4 고정 물질계에서도 2-jet만으로 부족하다는 정확한 예

일례로 \(p=\epsilon/3\), \(\Lambda=0\), 하나의 고정된 작용 \(P(X)=P_*X^2\)를 택한다. \(\epsilon_0>0\), \(C=\kappa\epsilon_0/3\), \(\kappa=8\pi G/c^4\)를 고정하면, \(0<r_0<C^{-1/2}\) 각각에 대해 국소 static Einstein–Euler 해가 존재하며 선택한 사건에서
\[
R_{0i0j}=C\delta_{ij},\quad
R_{ijkl}=C(\delta_{ik}\delta_{jl}-\delta_{il}\delta_{jk}),\quad
R_{0ijk}=0
\]
로 전체 곡률이 같다. stress, source velocity, 양의 enthalpy gap도 같다. 그러나
\[
\boxed{|A|=\frac{c^2 C r_0}{\sqrt{1-Cr_0^2}}\longrightarrow\infty.}
\]
strict DEC와 \(c_s=c/\sqrt3\)도 유지한다. Weyl=0은 선택한 한 사건에서의 진술이다.

증명은 TOV 초기값 \((m(r_0),\epsilon(r_0),\nu(r_0))=(\kappa\epsilon_0r_0^3/6,\epsilon_0,0)\), 매끄러운 ODE의 국소 존재, radial Bianchi에 의한 angular Einstein 방정식 확인, 전체 orthonormal curvature 계산으로 이루어진다. 물질 작용의 scalar 방정식은 시간 성분만 갖는 정적 current의 발산으로 직접 확인된다. 전역 적분 또는 수치적 진화가 필요하지 않다.

이것은 서로 다른 **국소 해**의 계열이다. 정규 중심을 갖는 완전한 별, 공통 크기의 영역, global horizon의 존재를 주장하지 않는다. 보존되는 양의 밀도 dust에는 적용할 수 없다. dust는 Euler 방정식으로 \(A=0\)이다.

고정 EOS를 요구하지 않고 \(T=(G+\Lambda g)/\kappa\)로 정하는 더 넓은 계에서는 명시적인 cubic metric perturbation으로 12개 velocity-gradient 성분 전체를 독립적으로 실현했다. 그 12방향 결과를 고정 EOS로 확장했다는 주장은 보류한다.

전체 증명: [ENERGYFRAME_THEOREMS.md](gr/ENERGYFRAME_THEOREMS.md), EF1–EF6.

### 3.5 유한 거리에서도 쓸 수 있는 오차 보증

관측자 정규화 affine length를 \(s\)라 하자. 전체 \(0\le s\le L\)에서
\[
\|\mathcal R_{\rm opt}\|_{\rm op}\le K_c,\qquad |Z''|\le M_2
\]
를 추가 정보로 제공한다. \(\eta(s)=\sinh(\sqrt{K_c}s)/(\sqrt{K_c}s)-1\), \(\eta(L)<1\)이면
\[
s(1-\eta)\le d_A\le s(1+\eta),
\]
\[
\boxed{|Z-Z_0-H_0d_A/c|
\le \tfrac12M_2s^2+\frac{|H_0|}{c}s\eta(s).}
\]
Jacobi 방정식의 Volterra majorant와 Taylor 적분 잔차를 결합한 직접적인 증명이다. \(K_c=0\)일 때 \(\eta=0\). 관측거리만을 쓰는 외부 envelope도 제공했다.

**극복 방법:** 정적 한 점의 곡률 대신 구간 전체의 tidal·source-derivative bound를 제공하고, 그 잔차를 추론에 포함한다. 이를 고정된 보편적 작은 수로 임의 대체하지 않는다. 충분조건 \(\eta(L)<1\)의 실패는 caustic의 존재를 뜻하지 않는다.

전체 증명: [FINITE_DISTANCE_THEOREM.md](gr/FINITE_DISTANCE_THEOREM.md).

## 4. JCAP 방향: 무엇을 검정하고 어떤 정보를 보존할 것인가

### 4.1 목표를 “dipole 검출”에서 geodesic 가정의 검정으로

새 목표는 지정한 매끄러운 광원계에 대해 \(A(p)=0\)를 미리 가정하지 않고 검정하는 것이다. 실제 galaxies가 이러한 유효 congruence를 표본화하는지, 어느 smoothing scale에서 그러한지 역시 관측 모형의 일부다. 이 검정의 기각은 GR 위반이나 가속되는 conserved dust의 발견을 뜻하지 않는다.

거리 오차를 무시하지 않기 위해 원래 관측량 \(y=(z_{\rm obs},\mu_{\rm obs})\)와 잠재적인 true \(r_i=d_{A,i}\)를 사용한다:
\[
Z_i=Z_0(n_i)+r_iH(n_i)/c+\rho_i,\qquad
\mu_i=5\log_{10}\!\frac{r_iZ_i^2}{10\,{\rm pc}}+\text{calibration}.
\]
\(\rho_i\)는 3.5에서 얻은 허용범위 안에 둔다. 이 범위는 실제 공통 시공간의 필요조건을 확장한 외부집합이며, 허용되는 모든 점이 물리적 시공간으로 실현된다는 주장은 아니다. 실제 데이터 제품이 luminosity-distance modulus를 제공하는지도 별도로 확인해야 한다.

### 4.2 정확한 조건부 coverage

전체 covariance \(C\)와 고정된 선형 nuisance 공간 \(F\) 아래
\[
y=m(\vartheta_*)+F\beta_*+\varepsilon,\quad
\varepsilon\sim N(0,C)
\]
를 가정한다. \(W C W^T=I\), \(P\)를 \(\operatorname{col}(WF)\)의 직교여공간 projector라 하면
\[
\mathcal C_\alpha=
\{\vartheta\in\Omega:\|PW[y-m(\vartheta)]\|^2
\le\chi^2_{\nu,1-\alpha}\},\quad
\nu=\operatorname{rank}P
\]
는 true complete parameter에 정확한 \(1-\alpha\) coverage를 갖는다. \(\nu\)에서 nonlinear fit parameter 수를 다시 빼지 않는다. 이는 표준 Gaussian/Neyman inversion이며 새로운 일반 통계정리로 주장하지 않는다.

동일 집합을 \(A,\theta,\sigma\)와 정해진 morphology 함수로 사상하면 공동 coverage가 유지된다. 출력은 다음 네 가지를 구별한다.

- 전체집합은 비어 있지 않지만 geodesic 부분은 비어 있음: 선언한 가정 아래 geodesicity 기각.
- 양쪽 모두 비어 있지 않음: geodesicity 미배제.
- 전체집합이 비어 있음: 해당 관측·잔차 모형의 부적합.
- 수치적 feasibility/exclusion이 증명되지 않음: 계산 미결정.

국소 최적화 실패를 null exclusion의 증거로 쓰지 않는다. selection, 추정된 covariance, non-Gaussian distance indicators는 위 Gaussian pivot을 자동으로 상속하지 않는다. 서로 다른 허용 잔차 시나리오 중 하나가 참인 경우까지 보장하려면 집합의 합집합을 사용한다.

### 4.3 morphology를 버리면 실제로 잃는 과학적 구분

정확한 예는
\[
u=(5/4,3/4,0,0),\quad
h_0=7H/4,\quad
h_2=\operatorname{diag}(3H/8,-3H/16,-3H/16)
\]
와 \(h_1=(15H/8,0,0)\)이다. 이때 \(A=0\). \(u,h_0,h_2\)를 그대로 두고 \(h_1\)만 \((0,15H/8,0)\)로 바꾸면 모든 **성분별** power는 같지만 \(A\ne0\)이다.

독립적인 isotropic Gaussian coefficient-block noise를 가정한 정확한 benchmark에서는 power들의 결합분포까지 동일하다. 따라서 powers-only test는 이 대안에 대해 size를 넘는 power를 갖지 못한다. full coefficient likelihood는 양의 KL divergence를 가지며 잡음이 작아질수록 두 점을 구분한다. 실제 mask나 covariance가 이 대칭을 만족한다고 가정하지 않는다.

긍정적인 복원 통계량은
\[
\boxed{
J_{\rm geo}
=g^{ab}(S_{ac}u^c)(S_{bd}u^d)+[S(u,u)]^2
=\frac{A_aA^a}{4c^2}\ge0.}
\]
허용된 계수 위에서 \(J_{\rm geo}=0\iff A=0\). 이 식은 \(\zeta\cdot h_1\), \(\zeta^Th_2\zeta\), \(h_1^Th_2\zeta\) 같은 교차 정보를 보존한다. 따라서 모든 scalar statistic이 실패한다는 주장은 틀리다. \(J_{\rm geo}\)는 기존 프로젝트의 \(Q,F,\Pi,G_F\)를 재정의하지 않는 별도 이름이다.

MES 상계로 나눈 비율도, 분자와 분모가 모두 별도 sector power만의 함수이면 같은 반례를 구분하지 못한다. 반대로 cross-contraction 또는 적절한 joint tensor를 보존하는 MES 표현에는 이 결론을 적용하지 않는다. normalization 자체가 p-value나 공통 검정력을 제공하는 것도 아니다.

### 4.4 추가 거리 정보가 주는 실제 개선과 남는 한계

이상적으로 true distances가 알려지고 잔차가 없는 경우,
\[
X=[E_4,\operatorname{diag}(r_i/c)E_9]
\]
의 rank가 13이면 unconstrained 절편·기울기가 모두 분리된다. \(E_4,E_9\)는 각각 \(\ell\le1,\ell\le2\) angular evaluation matrix다. 물리적 mass-shell chart에서는 12차원 Jacobian의 rank를 사용한다.

구체적 충분조건은 한 거리에서 degree-2를 결정하는 9방향을 관측하고, 그중 degree-1을 결정하는 4방향을 **다른 거리에서** 다시 관측하는 것이다. 13개 이상적 관측으로 full rank를 얻으며 충분히 작은 배치 교란에도 유지된다. 단순히 거리 범위가 넓다는 것만으로 충분하지 않다. 예컨대 \(r_i=R/(1+\epsilon n_{iz})\)는 거리와 방향이 얽혀 다시 aliasing을 만든다.

한편 내부 \(r<a\)를 전혀 관측하지 않고 \(|Z''|\le M\)만 아는 넓은 test-source class에서는, 외부 redshift–distance 자료가 전부 같아도 내부 source rapidity가
\[
\delta=\frac1{25}\min(1,Ma^2)
\]
만큼 다른 매끄러운 장을 구성할 수 있다. 이 예의 두 local slopes는 모두 0이다. 그러므로 이 정리가 acceleration의 비식별성을 추가로 증명한다고 해석하면 안 된다.

**극복 방법:** 관심 source field에 관한 독립적인 근거리 anchor, 안쪽까지 들어오는 표본과 적절한 regularity bound, 또는 별도로 검증한 물질·공간 구조가 필요하다. 동일 외부 자료를 더 많이 모으는 것만으로 정확한 vertex 정보를 얻는다고 주장하지 않는다.

통계 증명 전체: [NATIVE_INFERENCE_THEOREMS.md](statistics/NATIVE_INFERENCE_THEOREMS.md), [INFORMATION_LIMIT_THEOREMS.md](statistics/INFORMATION_LIMIT_THEOREMS.md).

## 5. 추가 PDF에서 받아들인 관측·정보의 구분

추가된 \`book.pdf\`는 *Reichenbach 상대성이론 공리화: 현대적 재구성과 비평적 주해*라는 프로젝트 재구성본이다. 관련 절을 원전·표준 기하와 대조하여 사용하며 Reichenbach 원본이나 별도의 동료심사 증명으로 취급하지 않는다.

이 자료가 이번 역산에 실제로 바꾸어 준 것은 **causal/light-ray 구조, metric의 scale, clock과 distance calibration을 구분하는 입력 조건**이다. 상수 \(\lambda>0\)에서
\[
g\mapsto\lambda^2g,\quad u,o,K\mapsto(u,o,K)/\lambda
\]
이면 \(Z_0\)와 dimensionless 상대속도는 그대로이지만 \(d_A\mapsto\lambda d_A\), \(H\mapsto H/\lambda\), \(|A|\mapsto|A|/\lambda\)다.

관측식에서도 자유로운 공통 modulus zero-point가 있으면
\[
r_i\mapsto\lambda r_i,\quad H\mapsto H/\lambda,\quad
\kappa_{\rm cal}\mapsto\kappa_{\rm cal}-5\log_{10}\lambda
\]
가 같은 평균 관측을 준다. 고정된 외부 거리·곡률 bound가 있으면 그 domain 안에서 실제로 허용되는 변환인지 다시 확인한다. 절대 가속도 크기에는 척도 보정이 필요하지만, 유한한 상수 재척도에서 \(A=0\) 여부는 보존된다. 비콤팩트한 scale orbit에서는 null을 제외해도 \(\inf|A|=0\)일 수 있다.

일반적인 비상수 conformal 변환은 이 상수 척도 자유와 다르다. \(\widetilde g=e^{2\phi}g\)일 때
\[
\widetilde A^a=e^{-2\phi}(A^a+c^2h^{ab}\nabla_b\phi)
\]
이므로 causal cone만으로 geodesicity가 결정되지 않는다. 전체 redshift·clock 자료는 일반적으로 이 변환에서 보존되지 않는다. 좌표 동기화 변경, 한 사건의 Lorentz boost, 물리적으로 다른 congruence도 구분한다.

구체적인 읽기 범위와 직접 유도는 [ADDED_BOOK_INTEGRATION.md](ADDED_BOOK_INTEGRATION.md)에 있다. 이어 첨부된 TEFF I–II 및 Dossier I–V의 추가 정보에 의한 복원 결과는 다음 절에서 통합한다.


## 6. TEFF·Dossier를 사용한 긍정적 복원 경로

### 6.1 TEFF: 추가 spectral moment를 관측·collision 오차경계로 바꾸기

TEFF I–II의 정적 coarse-graining을 운동학 미분과 동일시하지 않고, **선택한 관측 kernel의 불확실성을 줄이는 입력**으로 연결했다.

같은 관측자와 measure \(d\nu\)에서 두 occupation \(f,g\)가 retained moments \(\phi_a\)를 일치시키며 \(D_H(f\Vert g)\le\varepsilon\)라고 하자. 두 상태 사이에서 reciprocal entropy Hessian을 제어하는 공통 envelope \(W\)와 적분가능성을 추가한다. \(V=\operatorname{span}\{\phi_a\}\)이면
\[
\boxed{|\langle K,f-g\rangle|
\le\sqrt{2\varepsilon}\,\operatorname{dist}_{L^2(Wd\nu)}(K,V).}
\]
이는 작은 섭동에 국한되지 않는 convexity와 Cauchy–Schwarz의 결과다. retained moment를 늘리면 target kernel에서 이미 알려진 성분을 더 많이 제거한다.

여러 kernel \(K_j\)에 대해 \(r_j=K_j-P_VK_j\), \(R_{ij}=\langle r_i,r_j\rangle_W\)이면 공동 residual은
\[
\boxed{e\in\operatorname{range}R,\qquad e^TR^\dagger e\le2\varepsilon}
\]
를 만족한다. 이 집합은 채널마다 서로 무관한 bias bar를 붙이는 것보다 공유되는 제약을 보존한다. \(R\)은 noise covariance가 아니라 **결정론적 kinetic residual의 Gram 행렬**이다.

고정된 선형 collision operator \(\mathcal L\)에는 \(K\) 대신 \(\mathcal L^*K\)를 사용한다. \(\mathcal L^*K\in V\)이면 해당 collision moment는 retained moments만으로 정확히 결정된다. 그렇지 않으면 위 타원체로 제어한다. nonlinear Compton, 미지의 electron distribution 또는 편광 전달까지 자동 확장하지 않는다.

BE photon에는 \(f,g\le F_b(E)=(e^{bE}-1)^{-1}\)와 \(W=F_b(1+F_b)\)가 한 가지 충분조건이다. \(d\nu\propto E^2dE\,d\Omega\)이므로 infrared에서 weight가 적분가능하다. \(\varepsilon\)와 \(b\)는 bolometric energy만으로 결정되지 않으며, spectral 자료 또는 외부 허용집합으로 보장해야 한다.

또 다른 구체적 결과는 **number와 energy를 함께 측정하면 일반 bandpass에 cubic 오차보증을 준다**는 것이다. 같은 shape·fugacity를 갖는 thermal mixture의 temperature ratio가 \(y\in[1-s,1+s]\)에 있고 \(m_3=\langle y^3\rangle,m_4=\langle y^4\rangle\)를 안다고 하자. calibrated response \(\psi\in C^3\)에 대해
\[
\widehat O=c_0+c_3m_3+c_4m_4,
\]
\[
c_3=\psi'(1)-\psi''(1)/3,\quad
c_4=\psi''(1)/4-\psi'(1)/2,\quad
c_0=\psi(1)-\psi'(1)/2+\psi''(1)/12
\]
는
\[
|O-\widehat O|
\le\frac{s^3}{6}\sup|\psi'''(y)-6c_3-24c_4y|
\]
를 만족한다. 같은 prior에서 energy-only estimator는 일반적으로 \(O(s^2)\) bound를 준다. 이는 모든 photon distribution 또는 모든 bandpass에서 sharp minimax 향상을 주장하는 것이 아니다. 실제 광대역 kernel의 endpoint와 calibration은 따로 확인한다.

**실제 추가 정보 선택:** 임의로 더 높은 hierarchy를 계산하기보다 \(K-P_VK\), 또는 \(\mathcal L^*K-P_V\mathcal L^*K\)와 관련된 spectral band/moment를 우선 측정한다. 이로써 필요한 observable의 오차를 줄인다. TEFF II의 number–energy representative와 fixed-prior minimax predictor는 서로 다른 대상을 최적화하므로 구분한다.

전체 증명과 TEFF 식·페이지 대응: [TEFF_POSITIVE_BRIDGE.md](supplements/TEFF_POSITIVE_BRIDGE.md).

### 6.2 와도: 추가 정보가 자유도 세 개를 실제로 제거하는 방법

광학 역산으로 \(u,B\)를 알고 source-rest frame를 정했다고 하자. 광원 속도의 공간 미분을 독립적으로 제공하면, 알려진 대칭 부분을 뺀 directional residual은 와도에 대한 선형식이 된다. 하나의 방향은 그 방향 주위의 회전을 구분하지 못하지만 **서로 평행하지 않은 두 방향**은 와도 세 성분을 모두 고정한다. 충분조건은 명시적인 \(3\times3\) Gram 행렬의 양의 최소 고유값이며, 측정 오차도 그 값으로 제한한다.

복사장을 사용하는 별도의 경로에서는 source-frame brightness뿐 아니라 **독립적으로 지정된 시공간 미분과 collision moments**가 필요하다. Dossier의 광선 전달식에서 이미 복원한 \(\theta,\sigma,A\)의 기여를 제거하면 남는 angular rotation response가 와도의 선형 관측 연산자가 된다. \(M=\int\mathcal I ee^T d\Omega\), 잔차 moment를 \(R\)라 하면
\[
R=[M,\Omega],\qquad \Omega_{ij}=R_{ij}/(m_i-m_j).
\]
서로 다른 세 eigenvalue는 하나의 충분조건이다. 각 quadrupole이 axisymmetric여도 서로 평행하지 않은 두 축을 갖는 독립 채널을 함께 쓰면 공통의 미정 회전이 사라져 복원된다. 이를 stacked operator의 양의 최소 singular value로 판정하고 오차도 제한했다. finite spectral band에는 boundary flux를 포함한다. 이는 정적 CMB 한 장에서 와도를 추출했다는 주장이 아니다.

필요한 추가 derivative 채널, source-frame 회전 규약, 식의 부호와 유한 angular integration 조건은 [DOSSIER_POSITIVE_BRIDGE.md](supplements/DOSSIER_POSITIVE_BRIDGE.md)에 있다. 동일 부록에서 궤도 법선이 별도로 주어진 경우 local boost와 homogeneous tilt를 구별하는 충분조건도 다룬다.

### 6.3 막힌 부분과 복원에 필요한 정보를 한 쌍으로 정리

| 현재 정보에서 막히는 부분 | 추가하면 복원·제어가 가능한 정보 | 이번에 얻은 긍정적 결과 |
|---|---|---|
| arbitrary acceleration에서 slope만으로 source velocity가 모호함 | 절대 절편 또는 해당 source의 독립 velocity anchor | \(u,B,A,\theta,\sigma\)의 정확한 역산 |
| 같은 거리 shell의 절편–기울기 혼합 | 적절한 angular sampling과 두 거리의 독립 관측 | 구체적인 full-rank 13행 설계 |
| sector power가 상대 방향을 지움 | signed coefficients 또는 필요한 cross-contractions | \(J_{\rm geo}\)의 정확한 geodesicity 판별 |
| 절대 거리 척도가 자유로움 | 공통 zero-point/거리 표준의 외부 보정 | dimensionful rate와 acceleration scale 고정 |
| scalar optical 1차에서 와도 세 성분이 남음 | 두 비평행 spatial velocity-derivative 채널 | 전체 source 1-jet 복원과 오차 bound |
| radiation residual이 미지임 | spacetime derivative 자료, collision inputs, rank를 갖는 angular response | 조건부 와도 역산 |
| spectral coarse-graining bias가 불명확함 | 추가 number/band moments와 entropy·occupation envelope | 공동 observable/collision residual 타원체 |
| energy-only thermal prediction의 불확실성 | 같은 support·shape prior의 number+energy | 일반 bandpass의 명시적 cubic-width bound |
| metric 2-jet로 energy-frame rate가 결정되지 않음 | \(T,\nabla T\) 또는 비퇴화 metric 3-jet | 모든 \(\theta,\sigma,\omega,A\) 복원 |
| 한 점의 curvature로 유한 거리 오차를 모름 | ray segment의 curvature·source-derivative 상계 | Jacobi–Taylor 잔차 보증과 confidence set 전파 |
| local boost를 global tilt로 해석하기 어려움 | 독립적으로 정당화한 homogeneity-orbit normal | 해당 normal에 대한 tilt의 대수적 계산 |

이 표의 오른쪽 결과는 입력을 실제로 확보했을 때의 충분조건이다. 추가 정보가 현재 catalogue에 이미 들어 있다는 주장과 구별한다. 현재 실행 우선순위는 CF4·Union3의 native 관측 계약과 거리·방향 leverage 확인이며, 와도와 spectral residual 경로는 별도 채널의 가용성을 먼저 확인하는 연구다.

## 7. 원고 구성과 다음 단계

**CQG용 중심 질문:** “어떤 국소 기하·광학 정보가 물질 또는 광원계의 1차 운동학을 결정하는가?” 중심은 완전한 optical image/fibre, 추가 정보에 의한 completion, 고정 물질계에서의 미분 차수 한계와 그에 대응하는 충분조건이다. 통계 likelihood와 catalogue 분석은 이 원고에서 제외한다. 단순한 부호 교정, 표준 분해, elementary matrix inverse만을 독창성의 중심으로 삼지 않는다. 고정 EOS·고정 작용의 동일 곡률 계열과 복원/안정성 결과를 기존 invariant fluid characterization과 직접 비교하는 일이 우선이다.

**JCAP용 중심 질문:** “geodesic source를 미리 가정하지 않으면서, 동일 관측 조건에서 어떤 morphology 정보가 그 가정을 실제로 검정하게 하는가?” native likelihood, free intercept, finite-distance residual, cross-sector invariants, TEFF 기반 bias set을 묶고, 기존 harmonic cosmography와 같은 sampling·covariance에서 비교해야 한다. 최근 Kalbouneh 등의 CF4·Pantheon+ 연구는 이미 coefficient covariance와 방향 정렬을 사용한다. 따라서 그 선행연구를 powers-only straw man으로 제시하지 않는다.

JCAP에서 검증할 실질적 이득은 잘못된 dust/boost 귀속을 줄이는지, 포함확률을 유지하는지, 어떤 추가 band·거리 정보가 uncertainty를 줄이는지다. 데이터 분석을 끝냈다는 사실만으로 신규성이 생기지는 않는다. CQG 역시 관심 주제와 맞는다는 것과 충분히 새로운 연구라는 것은 별개다. 공식 범위상 이 연구 주제들은 각 저널과 연결되지만, 현재 투고 준비 완료나 채택 가능성을 수치로 판정하지 않는다.

후속 순서와 기계 판독 가능한 완료 조건은 [RESEARCH_HANDOFF.json](RESEARCH_HANDOFF.json)에 있다. 이미 통과한 bounded analytic proof를 위해 모든 과거 과학 계산을 반복하는 단계는 두지 않았다. 새로운 물질계 확장, 실제 covariance·selection, 수치적 confidence-set 계산은 각각의 새 주장에 필요한 검증만 수행한다.

## 8. 근거와 수행 범위

원전 대조, 직접 유도, 별도 작성자에 의한 증명 검토, 네 개의 경량 Wolfram 보조 확인을 수행했다. Wolfram은 null-jet algebra/Jacobi majorant, Maartens 역산 대입, TOV curvature, morphology 반례의 정확한 유리수 계산을 확인했다. 이 계산은 수학적 증명을 대신하지 않는다.

이번에 다룬 문헌은 supplied Ellis 및 관련 6개 책의 지정 절, Maartens 등의 pinned v3, Heinesen 및 관련 후속 원전, 추가 RBK 재구성본의 지정 절, TEFF I–II, Dossier I–V다. 실제 읽기 범위는 각 부록과 manifest에 있다. Dossier의 제목에 적힌 검증 상태를 전체 식의 새 독립 인증으로 옮기지 않는다. [원전 대조표](REFERENCES_AND_CORRECTIONS.md)에 적힌 2608.07008 본문 접근 공백 때문에 최신 문헌의 완전한 novelty exclusion도 완료되지 않았다.

주요 외부 일차 문헌:
- Maartens et al., *Covariant cosmography: the observer-dependence of the Hubble parameter*, [arXiv:2312.09875v3](https://arxiv.org/html/2312.09875v3), JCAP 09 (2024) 070.
- Heinesen, *Multipole decomposition of the general luminosity distance Hubble law*, [arXiv:2010.06534v2](https://arxiv.org/html/2010.06534v2).
- Heinesen & Korzyński, [arXiv:2406.06167v1](https://arxiv.org/html/2406.06167v1), position/redshift drift.
- Kalbouneh et al., *The anisotropic expansion rate of the local Universe and its covariant cosmographic interpretation*, [arXiv:2510.02510v1](https://arxiv.org/html/2510.02510v1).
- Macpherson & Heinesen, *A theoretical prediction for the dipole in nearby distances using cosmography*, [arXiv:2507.01095v3](https://arxiv.org/html/2507.01095v3), 관련 smoothing/convergence discussion.
- Hills & Heinesen, *Cosmography with Λ-Szekeres Models*, [arXiv:2601.16844v1](https://arxiv.org/html/2601.16844v1).
- Ehlers–Pirani–Schild, *The geometry of free fall and light propagation*, [2012 republication](https://doi.org/10.1007/s10714-012-1353-4), abstract/metadata cross-check only for this addition.

저널의 공식 설명: [CQG scope](https://publishingsupport.iopscience.iop.org/journals/classical-and-quantum-gravity/about-classical-quantum-gravity/), [JCAP referee criteria](https://jcap.sissa.it/jcap/help/helpLoader.jsp?pgType=referee). 조회된 공식 설명은 주제 적합성 및 originality·quality 요구를 뒷받침하며, 본 연구에 대한 편집부 판단을 대신하지 않는다.
