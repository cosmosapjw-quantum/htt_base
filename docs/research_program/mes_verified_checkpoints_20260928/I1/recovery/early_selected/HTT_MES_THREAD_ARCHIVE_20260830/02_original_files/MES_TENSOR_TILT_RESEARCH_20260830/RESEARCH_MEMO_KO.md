# MES tensor–tilt/boost 연구 루프: 결과와 유도

2026-08-30 · 수학적 유도와 합성 검증 · 관측자료 재분석 아님

## 0. 무엇을 실행했고 무엇을 실행하지 않았는가

첨부 PHYS–MATH RESEARCH HARNESS 5.6을 읽고, 기존 MES/Planck/1+3 PSTF/tilt formalism을 seed로 다음을 수행했다. 원 MES와 후속 정규화 논문, Bianchi-I 광전파, Lorentz aberration 및 원격 CMB multipole 문헌을 SciSpace로 탐색하고 primary source로 확인했다. 실제 repository의 고정된 code path를 읽었다. 대수적 후보들을 유도하고, 네 번의 외부 Wolfram 계산과 독립 angular-function oracle 및 Python 합성 실험으로 검증했다. 원시 지도·processed Planck array는 열지 않았으며, GitHub Actions나 원격 변경은 수행하지 않았다.

이 문서는 독립 과학 심사의 최종 승격 판정이 아니다. 첨부 하네스 Phase 5/8의 독립 reviewer는 새 후보에 대해 실행되지 않았다. 자체 반례 검토와 독립 CAS 계산을 독립 scientific reviewer로 둔갑시키지 않는다. 연구 후보의 publication/novelty 판정은 `HOLD_EXTERNAL_SCIENTIFIC_REVIEW_NOT_PERFORMED`다. 아래의 명시적인 대수 유도와 실제 합성실험 결과는 그 범위에서 보고한다.

원래 17쪽 WU-006 보고서의 Q/O 수치와 WU-006–008 물리 해석은 후속 `f5ae09d...` 보고·판정에서 철회되었다. 이 연구는 그것을 복권하지 않는다. 저장 기저 문제에 더해, 원 MES 입력의 PSTF norm과 sky RMS가 섞인 별도 문제를 발견했다.

증거는 `sources/SOURCES.md`, 실행 수치는 `results/research_results.json`, 재현 코드는 `code/`에 있다. 문헌에서 가져온 전제는 [S#], 읽은 코드 근거는 [G#]로 표시한다. 이하 새 algebra/응용 construction은 여기서 직접 유도한 것이며, 최초 발견이라는 priority claim은 하지 않는다.

## 1. Convention contract

시공간 signature는 (-,+,+,+), 공간은 해당 observer rest space의 양의 definite metric이다. c=1을 쓴다. H=Theta/3>0, sigma_ab는 선택한 congruence의 STF shear다. vorticity vector와 antisymmetric tensor는 같은 dualization convention으로 연결하며, norm은 omega_ab omega^ab=2 omega_a omega^a다. Triad rotation이나 Bianchi commutator vector를 physical vorticity/acceleration로 바꾸어 부르지 않는다.

CMB sky direction n은 바깥쪽 시선이며 photon propagation direction e=-n이다. Temperature PSTF의 홀수 rank는 이 방향 전환에 따라 부호가 바뀐다. Local boost 공식에서는 n, radiation hierarchy에서는 e를 사용하므로 adapter가 필요하다.

실제 저장된 orthonormal real block은

\[
c_\ell=(a_{\ell0},\sqrt2\Re a_{\ell1},-\sqrt2\Im a_{\ell1},\ldots).
\]

따라서 c의 metric은 Euclidean이며, unscaled complex-component 실수 벡터 a_R의 metric은 diag(1,2,2,...). 둘은 S_l=diag(1,sqrt2,-sqrt2,...)로 연결된다. 변환된 rotation은 D_c=S_l D_R S_l^{-1}이다. 혼합된 기저에서 round-trip이 성공하는 것은 충분하지 않다. 실제 spherical function과의 일치와 physical rotation equivariance를 검증해야 한다. [G1,G2]

Thermodynamic temperature와 linearized intensity-derived K_CMB map은 유한 boost에서 자동으로 같은 객체가 아니다. Frequency/bandpass 및 Doppler weight를 맞추지 않고 아래의 exact temperature 식을 모든 map에 적용하지 않는다. [S7]

## 2. R0 — 새로 확인한 MES epsilon 정규화 문제

### 2.1 Source-derived definition

MES/SAG의 epsilon_l은 covariant temperature multipole tau_A_l의 Euclidean tensor norm에 대한 bound다. Sky RMS/T0와 같지 않다. SAG Eq. (1), (15), (17)–(19)는 그 차이를 명시하며 quadrupole 및 octupole의 제곱 norm factor는 각각 7.5, 17.5다. [S1–S4]

Dimensionless temperature expansion을 tau_A_l n^{A_l}로 쓰면

\[
\int_{S^2}(\tau_{A_\ell}n^{A_\ell})^2d\Omega
=\Delta_\ell\tau_{A_\ell}\tau^{A_\ell},\qquad
\Delta_\ell=\frac{4\pi\,\ell!}{(2\ell+1)!!}.
\]

Parseval에 의해

\[
\|\tau_\ell\|^2=\frac{\|c_\ell\|^2}{T_0^2\Delta_\ell},\quad
 e_\ell^2\equiv\frac{(2\ell+1)C_\ell}{4\pi T_0^2},\quad
\|\tau_\ell\|=\sqrt{\frac{(2\ell+1)!!}{\ell!}}\,e_\ell.
\]

따라서 epsilon을 해당 row의 norm으로 구성하는 조건부 통계 경로에서는 epsilon2=sqrt(15/2)e2, epsilon3=sqrt(35/2)e3가 필요하다. 실제 물리 theorem의 epsilon은 전체 적용 domain에서 유효한 상한이어야 하며, 관측행의 norm 하나가 곧 그 상한을 증명하지는 않는다.

### 2.2 Code-derived mismatch

검사한 `3cdeaba.../htt/obsstat/mes_row_anchor.py::_epsilon_from_cl`은 e_l을 반환하고, `mes_theorem_authority.py`는 원 MES triple (5/3,3,3/7), (10/3,2/15,0)을 그대로 유지한다. `statistical_foundations.py`는 이를 바로 1.5*bound^2로 변환한다. 이 고정된 코드 경로에는 위 norm factor의 보상이 없다. 이것은 검사한 historical active path에 대한 finding이며, 모든 후속 branch가 같은지 전수 검사한 것은 아니다. [G3–G5]

원 MES coefficient를 유지하고 epsilon1=0을 가정하면

\[
U_\sigma=\frac32\left(3\sqrt{15/2}\,e_2+\frac37\sqrt{35/2}\,e_3\right)^2,
\quad U_\omega=\frac{C_2}{4\pi T_0^2}.
\]

과거 scalar 함수 W2=C2/(30 pi T0^2)는 물리적 epsilon 규약에서는 7.5배 작다. W축의 단순 양의 상수배는 기존 순위에 영향을 주지 않지만, Sigma축은 상대적인 ell2/ell3 weight도 변하므로 전체 family rank를 재계산해야 한다. 이 연구에서는 그 rank를 계산하지 않았다.

문서에서 인용된 C2=210.46184716646644, C3=482.02081141805786 microK^2와 명시적으로 T0=2.7255e6 microK를 사용한 산술 예시는 다음과 같다.

| 함수 | 과거 RMS 입력 | PSTF norm 입력 |
|---|---:|---:|
| Sigma squared ceiling | 2.4000517981e-10 | 2.2076753459e-9 |
| W squared ceiling | 3.0061446738e-13 | 2.2546085054e-12 |

각각 약 9.19845배, 7.5배다. 이 숫자는 normalization illustration이지 새 관측 shear/vorticity measurement 또는 새 confidence bound가 아니다. 과거 98/301 등의 저장된 산술 결과는 보존하되, 원 MES bound라는 해석은 별도 재검토가 필요하다.

## 3. R1 — scalar norm ceiling을 tensor feasible body와 cubic bound로 확장

MES 가정이 실제로 성립하는 동일 congruence에서

\[
S_{ab}=\frac{\sigma_{ab}}{\sqrt6H},\quad
w_a=\frac{\omega_a}{\sqrt3H},\quad
s_2=\mathrm{tr}S^2\le U_\sigma,\quad w^2\le U_\omega.
\]

여기서 U들은 one-way premise-conditioned ceiling이다. 가용 상태는 단일 scalar가 아니라

\[
\mathcal K(U_\sigma,U_\omega)=
\{S=S^T,\ \mathrm{tr}S=0,\ \mathrm{tr}S^2\le U_\sigma,\ w^2\le U_\omega\}
\]

라는 tensor/vector 영역으로 보존한다. 실제 물리 모델의 제약식·evolution을 추가하면 이 영역의 부분집합이 된다. U만으로 방향이나 특정 S를 고르지는 않는다.

### 3.1 Exact cubic inequality

s3=tr S^3라 두면 특성다항식은

\[
S^3-\frac{s_2}{2}S-\frac{s_3}{3}I=0.
\]

실수 고유값 세 개의 discriminant는

\[
\prod_{i<j}(\lambda_i-\lambda_j)^2
=\frac{s_2^3}{2}-3s_3^2\ge0.
\]

따라서 sharp bound는

\[
|s_3|\le\frac{s_2^{3/2}}{\sqrt6}
\le\frac{U_\sigma^{3/2}}{\sqrt6}.
\]

등호는 uniaxial spectrum (2a,-a,-a)에서 성립한다. 사용자가 요청한 sigma_ac sigma_b^c sigma^bc는 이 cubic trace이며,

\[
\frac{|\sigma_a{}^b\sigma_b{}^c\sigma_c{}^a|}{H^3}
\le6U_\sigma^{3/2}.
\]

또한

\[
J_S=\frac{\sqrt6s_3}{s_2^{3/2}}\in[-1,1],\quad
\|S\|_{op}\le\sqrt{2U_\sigma/3},\quad
|n^a\sigma_{ab}n^b|/H\le2\sqrt{U_\sigma}.
\]

J는 비영 shear의 shape를 나타낸다. J가 +/-1인 것만으로 boost인지 shear인지 판별할 수는 없다. Kinematic quadrupole STF(beta beta)와 uniaxial shear가 같은 J를 가질 수 있기 때문이다.

### 3.2 Tensor-square 및 higher order

\[
\mathrm{tr}S^4=\tfrac12s_2^2,\quad
\|\mathrm{STF}(S^2)\|_F^2=\tfrac16s_2^2.
\]

모든 higher trace는 r_k=(s2/2)r_{k-2}+(s3/3)r_{k-3}를 만족한다. 따라서 shear 하나에 quartic, quintic scalar를 계속 붙이는 것은 새로운 eigenvalue 정보가 아니다. 상대방향을 담은 실제 벡터나 다른 tensor와의 mixed contraction이 필요하다.

MES가 first-order S1에 대해 주어진 근사 theorem이면 이것이 곧 exact nonlinear MES theorem이 되지는 않는다. S=S1+R일 때

\[
|\mathrm{tr}S^3-\mathrm{tr}S_1^3|
\le3\|S_1\|_F^2\|R\|_F+3\|S_1\|_F\|R\|_F^2+\|R\|_F^3.
\]

R=O(epsilon^2)이면 cubic error는 O(epsilon^4)다. 이 remainder의 실제 크기는 별도 dynamics/assumption evidence다.

### 3.3 방향별 관측함수와 cubic의 연결

f(n)=sigma_ab n^a n^b에 대해 구면 평균을 직접 적분하면

\[
\langle f^2\rangle=\frac{2}{15}I_2,\quad
\langle f^3\rangle=\frac{8}{105}I_3,\quad
\frac{\langle f^3\rangle}{\langle f^2\rangle^{3/2}}
=\frac{2\sqrt5}{7}J_\sigma.
\]

여기서 I2=tr sigma^2, I3=tr sigma^3. 이것은 실제 방향별 expansion quadrupole을 측정할 때 cubic shear shape로 연결되는 식이다. Scalar norm에서 direction을 발명하는 과정이 아니다. Sky coverage/selection/measurement error를 별도로 처리해야 한다.

## 4. R2 — shear와 tilt/rotation vector의 joint geometry

v를 실제로 주어진 polar tilt/boost vector 또는 axial vorticity vector로 둔다. Scalar ceiling에서 구성한 가짜 vector는 허용하지 않는다.

\[
m_0=v^2,\quad m_1=v^TSv,\quad m_2=v^TS^2v.
\]

m1은 cubic mixed term, m2는 quartic mixed term이다. CH에 의해

\[
m_3=\frac{s_2}2m_1+\frac{s_3}3m_0,\quad
m_4=\frac{s_2}2m_2+\frac{s_3}3m_1.
\]

Krylov matrix X=[v,Sv,S^2v]의 Gram matrix는

\[
G=X^TX=\begin{pmatrix}m_0&m_1&m_2\\m_1&m_2&m_3\\m_2&m_3&m_4\end{pmatrix}\succeq0,
\quad \kappa^2=(\det X)^2=\det G.
\]

따라서 임의의 독립 box bound를 붙이기보다 이 joint body를 이용하는 것이 정확하다.

### 4.1 상대방향 복원

서로 다른 eigenvalue lambda_i에 대해 spectral projector

\[
P_i=\frac{S^2+\lambda_iS+(\lambda_i^2-s_2/2)I}{3\lambda_i^2-s_2/2}
\]

를 사용하면

\[
p_i=v^TP_iv
=\frac{m_2+\lambda_i m_1+(\lambda_i^2-s_2/2)m_0}{3\lambda_i^2-s_2/2}
=v_i^2\ge0.
\]

즉 (s2,s3,m0,m1,m2)는 eigenvalues와 v의 각 eigendirection에 대한 제곱성분을 정한다. Generic SO(3) orbit의 연속 차원은 5+3-3=5이며, kappa의 부호가 남은 handed branch를 구별한다. 이것은 smooth한 한 개의 global chart라는 주장이 아니다. 중복 고유값과 영성분 strata는 별도로 처리한다.

### 4.2 Sharp coupled bound

Eigenframe에서 kappa^2=p1 p2 p3*product_{i<j}(lambda_i-lambda_j)^2다. p1+p2+p3=m0에 AM-GM를 적용하면

\[
\kappa^2\le\frac{m_0^3}{27}\left(\frac{s_2^3}{2}-3s_3^2\right),
\quad
\frac{|\kappa|}{m_0^{3/2}s_2^{3/2}}
\le\frac{\sqrt{1-J_S^2}}{3\sqrt6}.
\]

균등한 p_i에서 sharp하다. 같은 크기의 shear라도 uniaxial shape에서는 이 orientation volume이 반드시 0이다. 무작위 12,000개 합성 state와 equality example을 검사했다.

v가 polar면 kappa는 O(3) pseudoscalar다. v가 axial이면 세 vector-column의 추가 parity와 determinant의 parity가 상쇄되어 kappa는 even scalar다. 이 distinction을 무시하면 chirality claim이 뒤집힌다.

Krylov rank가 낮아도 determinant는 정의되며 0이다. 정의된 zero와, q2=0 등으로 normalized field 자체가 존재하지 않는 경우를 구분한다.

### 4.3 추가 MES-compatible inequalities

\[
|m_1|\le\sqrt{2/3}\sqrt{U_\sigma}m_0,\quad
m_2\le\frac23U_\sigma m_0,
\]

\[
\|\mathrm{STF}(S_{(ab}v_{c)})\|^2
=\frac13s_2m_0+\frac25m_2
\le\frac35U_\sigma m_0.
\]

v=w로 두면 physical mixed term은

\[
|\sigma_{ab}\omega^a\omega^b|/H^3
\le6\sqrt{U_\sigma}U_\omega.
\]

반면 antisymmetric omega_ab의 tr(omega^3)는 항등적으로 0이다. Pure vorticity cubic trace 대신 위 mixed moments나 미분·다중 tensor 정보를 사용해야 한다.

### 4.4 Vorticity의 감쇠율을 cubic mixed term으로 제한

일반 geodesic congruence의 정확한 vorticity propagation [S5, Eq. (9)]은

\[
\dot\omega_{\langle a\rangle}+2H\omega_a=\sigma_{ab}\omega^b.
\]

따라서

\[
\frac{d\omega^2}{dt}=-4H\omega^2+2\sigma_{ab}\omega^a\omega^b.
\]

Section 3의 directional spectral bound를 쓰면 omega!=0에서

\[
-2H-2H\sqrt{U_\sigma}
\le\frac{d\ln|\omega|}{dt}
\le-2H+2H\sqrt{U_\sigma}.
\]

전 구간에 같은 MES bound가 유효할 때, N=integral H dt라 하면

\[
\exp\!\left[-2\Delta N-2\int\sqrt{U_\sigma}\,dN\right]
\le\frac{|\omega(t)|}{|\omega(t_0)|}
\le
\exp\!\left[-2\Delta N+2\int\sqrt{U_\sigma}\,dN\right].
\]

이는 cubic mixed geometry가 vorticity의 evolution에 직접 들어가는 예다. Accelerated congruence에서는 curl(A) source가 추가되므로 이 감쇠 bound를 그대로 쓰지 않는다. Hypersurface normal Bianchi-I congruence의 omega=0을 이 식으로 억지로 nonzero로 만들지도 않는다.

## 5. R3 — 실제 tilt가 shear cubic shape를 변화시키는 모델

### 5.1 Local boost와 congruence tilt는 다르다

u_m=gamma(n+v)에서 v(x,t)는 matter congruence의 장이다. Observer boost beta는 관측사건의 다른 tetrad/observer로 옮기는 Lorentz map이다. 점에서 같은 velocity를 가져도 derivatives가 다르면 shear, expansion, acceleration, vorticity가 다르다.

\[
\nabla_a u^{(m)}_b
=\gamma\nabla_a n_b+\gamma\nabla_a v_b+(n_b+v_b)\nabla_a\gamma.
\]

이를 u_m에 직교 투영해야 새로운 kinematics를 얻는다. 기존 geodesic MES bound에 beta만 대입해 tilted-congruence bound로 바꾸는 것은 정당화되지 않는다. [S1,S2,S5]

### 5.2 Tilted perfect fluid의 exact stress

Rest density rho, pressure p, h=rho+p라 하면 normal frame에서

\[
\rho_n=\gamma^2h-p,\quad q_a=\gamma^2h v_a,\quad
\pi_{ab}=\gamma^2h\,v_{\langle a}v_{b\rangle}.
\]

h>0이면 nonzero pi의 normalized cubic shape는 J_pi=+1이다. 하지만 uniaxial shape alone은 원인의 식별자가 아니다. [S5를 바탕으로 한 대수적 전개]

Bianchi I의 homogeneous momentum constraint는 q_total=0이다. 따라서 homogeneous normal-frame geometry에 arbitrary single tilted dust fluid를 무조건 추가하면 안 된다. 두 개의 equal/opposite tilted dust stream은 q가 상쇄되면서 anisotropic stress는 더해지는 물리적으로 일관된 counterexample이 된다.

### 5.3 Cubic evolution

Bianchi-I normal frame, 8piG=c=1, Lambda=0에서 spatial Einstein differences는

\[
\dot\sigma_{ab}+3H\sigma_{ab}=\pi_{ab}.
\]

I2=tr sigma^2, I3=tr sigma^3이면

\[
\dot I_2=-6HI_2+2\sigma:\pi,\quad
\dot I_3=-9HI_3+3(\sigma^2):\pi.
\]

한 tilt-stress term을 대입하면

\[
\dot I_2=-6HI_2+2h\gamma^2v^T\sigma v,
\]
\[
\dot I_3=-9HI_3+3h\gamma^2
\left(v^T\sigma^2v-\frac{I_2v^2}{3}\right).
\]

여기서는 S가 아니라 physical sigma를 쓴다. pi=0에서는 sigma가 a^-3으로 줄지만 J_sigma는 일정하다. Tilt stress는 방향·shape coupling을 통해 J를 변화시킨다. 즉 m1,m2는 장식적인 추가 통계가 아니라 cubic dynamics에 직접 등장한다.

### 5.4 실행한 counterstream 실험

입자 질량 1, conserved covariant z-momenta +/-P, P=.002, rho(0)=3, initial sigma=(2e-6,-1.2e-6,-.8e-6)로 적분했다. Number density N은 (a_x a_y a_z)^-1, physical p=P/a_z,

\[
E=\sqrt{1+p^2},\quad \rho=NE,\quad p_z=Np^2/E,
\quad \pi=\mathrm{diag}(-p_z/3,-p_z/3,2p_z/3).
\]

q_total=0를 만족한다. Main solution은 Friedmann으로 H를 구한다. 그 constraint residual만으로 검증을 주장하지 않고, 별도로 Raychaudhuri의 Hdot=-(rho+p_z/3+I2)/2를 적분하는 independent formulation을 비교했다.

결과는 J_initial=.9411151, J_min=-.9999941, J_final=.6391356이다. Non-tilted dust control의 J spread는 2.0e-15다. Main shape trajectory의 tolerance refinement 차이는 1.78e-9이며 independent Hamiltonian residual은 1.43e-11에서 더 엄격한 tolerance에서 2.30e-13으로 줄었다. 최소 I2는 6.73e-14로 0이 아니다.

이것은 새 합성 Einstein–matter toy result이지 native BASS validation, Planck fit 또는 MES theorem의 모든 가정을 만족한 cosmology라는 판정이 아니다. 여기서는 이 toy에 실제 MES 수치상한을 강제하지 않았다.

## 6. R4 — Q/O mixed vector를 구체적인 boost-response 좌표로 쓰기

### 6.1 First-order boost generator

Rest-frame thermodynamic temperature에 대해

\[
T_o(n)=\frac{T_r(n_r)}{\gamma(1-\beta\cdot n)},\quad
n_r=\frac{J_\beta n-\gamma\beta}{\gamma(1-\beta\cdot n)},
\quad J_\beta=I+\frac{\gamma^2}{\gamma+1}\beta\beta^T.
\]

따라서 beta의 1차에서

\[
\delta T=(\beta\cdot n)T-
[\beta-(\beta\cdot n)n]\cdot\nabla_{S^2}T.
\]

T_Q=Q_ab n^a n^b에 작용하면

\[
\delta T_Q=3(\beta\cdot n)(Q:nn)-2(Q\beta)\cdot n.
\]

STF decomposition으로

\[
\delta O_{abc}=3\mathrm{STF}(\beta_{(a}Q_{bc)}),\qquad
\delta d_a=-\frac45Q_{ab}\beta^b.
\]

이는 first-order boost의 spin/rank mixing이지 global tilt dynamics가 아니다. [S7의 온도 boost를 출발점으로 직접 유도]

### 6.2 Closed-form Q-to-O response inverse

Model O=3 STF(beta tensor Q)를 가정하고 v_a=O_abc Q^bc를 만들면 정확한 대수식은

\[
v=\left(q_2I+\frac65Q^2\right)\beta,
\quad q_2=Q:Q.
\]

따라서 q2>0에서

\[
\boxed{\widehat\beta_{Q\to O}=
\left(q_2I+\frac65Q^2\right)^{-1}(O:Q).}
\]

이 normal matrix는 positive definite이고 condition number는 9/5 이하라는 uniform upper bound를 갖는다. Q의 eigenvalue가 중복돼도 rank는 3이다. 단, q2 자체가 작아질 때 absolute noise amplification은 커지므로 좋은 matrix condition number가 좋은 statistical sensitivity를 뜻하지 않는다.

임의의 O에 대해서도 이 식은 3차원 boost-response subspace로의 least-squares projection을 준다. O_perp=O-3 STF(beta_hat tensor Q)는

\[
Q^{bc}(O_\perp)_{abc}=0
\]

를 만족하며, rank-three response가 설명하지 못하는 네 개의 STF3 자유도가 남는다. 200개의 exact synthetic inverse와 rotation covariance, residual orthogonality tests를 실행했다.

중요한 제한: intrinsic O, rest-frame ell4의 boost-down, finite-beta, monopole-induced terms, mask response가 없는 가정일 때만 beta로 해석할 수 있다. 일반적인 O=O_intrinsic+B_Q beta에서 O_intrinsic이 자유면 beta는 point identified가 아니다. 따라서 이 식을 바로 Planck peculiar velocity measurement로 보고하지 않는다. 대신 외부 beta estimate와 비교하는 coherent tensor-consistency statistic으로 사용할 수 있다.

### 6.3 Monopole와 finite-beta correction

Pure isotropic blackbody의 boost는

\[
Q^{kin}=T_0\beta_{\langle a}\beta_{b\rangle}+O(\beta^4),\quad
O^{kin}=T_0\beta_{\langle a}\beta_b\beta_{c\rangle}+O(\beta^5).
\]

작은 B의 ideal Bianchi-I rest sky에 대해

\[
O_{obs}-3\mathrm{STF}(\beta\otimes Q_{obs})
+2T_0\mathrm{STF}(\beta^{\otimes3})
=O(\beta\|B\|^2+\beta^3\|B\|+\beta^5).
\]

Pure-boost limit의 fifth-order residual scaling을 수치로 확인했다. 이 조건식은 외부 beta를 넣은 null-consistency test에 유용하나 arbitrary primordial sky에는 0이어야 할 이유가 없다.

Finite ell=2..5 carrier는 exact Lorentz transformation에 대해 닫혀 있지 않다. Monopole/dipole, 상단 ell boundary, estimator/boost 비가환성을 처리해야 한다. Masked estimator L이면 일반적으로 L B != B_low L이다. 이 연구는 그 production response를 검증하지 않았다.

## 7. R5 — ideal Bianchi-I에서 inverse-square temperature의 exact inverse

### 7.1 모델과 forward map

Homogeneous Bianchi I, 동일한 emission time의 isotropic blackbody, emission 이후 collisionless radiation, stochastic intrinsic anisotropy·foreground·scattering 없음, observer의 finite boost를 가정한다. Bianchi-I conserved photon covector로부터 exact redshift를 쓸 수 있다. [S6]

Commuting diagonal geometry에서

\[
B_i=\ln\frac{a_i(t_o)}{a_i(t_*)}-\ln\frac{a(t_o)}{a(t_*)},\quad
\sum_iB_i=0.
\]

Rotation-covariant matrix 형태로

\[
T_r(n)=\frac{T_{iso}}{\sqrt{n^T e^{2B}n}},\quad
M=T_{iso}^{-2}e^{2B}\succ0.
\]

Finite boost를 정확히 결합하면 Doppler denominator가 소거되어

\[
\boxed{F(n)\equiv T_o(n)^{-2}
=(J_\beta n-\gamma\beta)^T M(J_\beta n-\gamma\beta).}
\]

T 자체에는 무한개의 harmonics가 생기지만 F는 정확히 ell<=2이다. 이 nonlinear change of variable이 inverse construction의 핵심이다.

### 7.2 Null-cone quadratic representation

F=f0+f1 dot n+n^T F2 n, tr F2=0로 적합한다. 아홉 coefficients를

\[
A=\begin{pmatrix}f_0&-f_1^T/2\\-f_1/2&F_2\end{pmatrix},
\quad k=(1,-n),\quad \eta=\mathrm{diag}(-1,1,1,1)
\]

로 조립하면 F=k^T A k이다. k^T eta k=0이므로 A와 A+lambda eta는 동일한 sky function을 나타낸다. 이것은 한 개의 표현 gauge다.

Rest representative는 A0=diag(0,M). Lorentz boost의 congruence transformation은 eta A를 similarity transformation시키며, gauge는 모든 eigenvalue에 같은 lambda를 더한다. 따라서 eta A의 unique future timelike eigenvector u가 rest direction을 정한다.

\[
\boxed{\beta=-u_{spatial}/u_0.}
\]

Timelike eigenvalue lambda_t와 spacelike eigenvalues lambda_i의 차이 Delta_i=lambda_i-lambda_t는 양수이며 M의 eigenvalues다. 따라서

\[
\boxed{T_{iso}=(\Delta_1\Delta_2\Delta_3)^{-1/6},\qquad
B_i=\frac12\ln\frac{\Delta_i}{(\Delta_1\Delta_2\Delta_3)^{1/3}}.}
\]

Boost-back한 spatial eigenvectors로 B의 orientation도 복원한다. Gauge A→A+lambda eta는 u와 Delta_i를 바꾸지 않는다. Exact rational boost와 non-diagonal M에 대해 외부 Wolfram이 null quadratic, Lorentz identity, eigenvector와 characteristic polynomial을 검증했다.

### 7.3 무엇이 identified되는가

모델 안에서는 endpoint integrated anisotropy B, beta, Tiso가 identified된다. 이것이 일반 Planck-only local/global identification theorem은 아니다. 임의의 primordial anisotropy를 허용하면 그 anisotropy가 동일한 B/boost imprint를 흡수할 수 있다.

B는 instantaneous sigma(t_o)가 아니다. Commuting history에서만 B=integral sigma dt이며, noncommuting history에서는 endpoint matrix-log deformation으로 읽어야 한다. 오늘의 MES ceiling 한 개로 전체 line-of-sight B를 제한하지 못한다. 같은 frame에서 전 구간의 bounds가 있으면

\[
\|B\|_F\le\sqrt6\int_{t_*}^{t_o}H(t)\sqrt{U_\sigma(t)}dt
\]

를 얻을 수 있다. Source-free Bianchi-I shear law sigma(t)=sigma_o a(t)^-3와 background가 별도로 고정되면 B=G sigma_o, G=integral a^-3 dt로 sigma_o를 조건부 역추론할 수 있다. Arbitrary tilted/anisotropic-stress history에서는 이 환원이 성립하지 않는다.

### 7.4 합성 검증과 실패모드

400개 noiseless synthetic cases에서 max B error=1.27e-14, max beta error=9.69e-15, max Tiso error=1.29e-14, quadratic-fit residual=1.89e-15였다. Noise는 일곱 수준에서 각 50개 반복을 실행했다. Error가 noise에 따라 증가했고, intrinsic octupole을 추가하면 model residual을 숨기지 않고 남겼다.

이 inverse에는 full positive thermodynamic temperature와 monopole/dipole가 필요하다. 기존 ell2..5 compressed carrier만으로 exact F를 구성할 수 없으며, arbitrary pixel foreground나 linearized intensity map을 그대로 넣어도 안 된다. 이 연구에서는 실제 CMB fit을 수행하지 않았다. SciSpace/primary-source search만으로 이 construction의 학문적 최초성을 확립하지 못했다.

## 8. R6 — 실제 kinematics를 관측에서 추출하는 경로

### 8.1 MES 부등식 이전의 tensor equation을 역으로 사용

FLRW-linearized radiation hierarchy에서 photon-propagation 방향 e와 동일 observer frame을 쓰면

\[
\dot\tau_{\langle ab\rangle}+D_{\langle a}\tau_{b\rangle}
+\frac37D^c\tau_{abc}=-\sigma_{ab}+\mathcal C_{ab}.
\]

따라서

\[
\sigma_{ab}=\mathcal C_{ab}-\dot\tau_{\langle ab\rangle}
-D_{\langle a}\tau_{b\rangle}-\frac37D^c\tau_{abc}.
\]

이 식은 [S5] Eq. (93)의 brightness moments를 temperature PSTF로 바꾼 결과다. pi_gamma=(8/15)rho_gamma tau2, q_gamma=(4/3)rho_gamma tau1를 사용하면 spatial coefficient 3/7이 나오며 별도 angular projection test로도 확인했다. Collision term에 실제 polarized/tilted physics를 임의로 넣지는 않았다.

MES에서는 이런 tensor equation에 norm과 triangle inequality를 적용하고 derivatives를 upper bound한다. 따라서 방향 정보가 소실된다. 반대로 실제 tau fields와 derivatives를 측정·모델링하면 원래 tensor equation으로 돌아가 sigma 자체를 추론할 수 있다. 이것이 ceiling의 역함수를 만드는 것과 다른 점이다.

단일 observer CMB map은 dot tau2나 spatial derivatives를 주지 않는다. kSZ/pSZ tomography는 remote dipole/quadrupole의 projected field를 제공할 수 있지만 optical-depth/velocity degeneracy, light-cone derivative와 time derivative의 분리, transfer와 selection이 추가로 필요하다. [S8]

### 8.2 Low-z affine velocity gradient

저적색편이 local orthonormal physical coordinates의 affine approximation에서

\[
V(x)=V_0+(H_{loc}I+S_v+W)x,
\]

S_v는 symmetric trace-free velocity-gradient shear, W는 antisymmetric part다. Radial observable은

\[
v_r(r,n)=n\cdot V_0+r[H_{loc}+n^T S_vn],\quad n^TWn=0.
\]

여러 방향/거리에서 bulk 3개, expansion 1개, shear 5개를 jointly fit할 수 있다. 288개 synthetic directions에서 design rank9, shear reconstruction error8.68e-16을 확인했다.

이 radial channel은 solid-body rotation을 정확히 보지 못한다. CF4의 reconstructed 3D field를 미분하면 curl을 계산할 수 있지만, 그것은 reconstruction assumptions에 조건부인 결과이며 radial data만으로 새 독립 vorticity를 측정한 것이 아니다.

Tangential proper-motion field는 leading local approximation에서

\[
\mu(n,r)=P_nV_0/r+P_nS_vn+\Omega\times n.
\]

Shear term은 (1/2)grad_S(n S_v n)의 E-type quadrupole이고, rigid rotation은 B-type dipole이다. 그러나 astrometric reference-frame spin도 같은 B1 pattern을 만들므로 frame calibration 없이는 분리되지 않는다. 해당 3+3 parameter design의 rank가 3임을 test했다. Relativistic distance/drift extensions의 기반은 [S9]다.

### 8.3 Tilt/boost 분리의 실질적 조건

관측 depth별 response를 y_r=A_r beta_local+B_r v_global+nuisance로 쓰면, nuisance projection 후 [A,B]가 full column rank여야 한다. 단일 shell에서 동일 response로 들어오는 두 vector는 rank3이고, 두 독립 depth kernel이 있으면 rank6이 가능하다. 그러나 nuisance가 그 차이를 흡수하면 rank는 다시 감소한다. 두 survey가 있다는 사실만으로 rank가 늘어난다고 가정하지 않는다.

## 9. R7 — incomplete scalar catalogue 대신 complete generic observable chart

Q와 O의 총 자유도는 5+7=12, generic SO(3) orbit을 나누면 9다. 여덟 smooth scalar가 generic orbit을 분리할 수 없다는 기존 referee 지적은 유효하다. 단순히 새 scalar 하나를 추가한다고 global separation이 증명되는 것도 아니다.

더 직접적인 대안은 Q의 ordered simple eigenvalues 두 개와, 그 proper eigenframe에서 O의 일곱 STF3 성분을 모두 유지하는 것이다. Eigenvector sign ambiguity를 제거하려고 arbitrary axis를 선택하는 대신 네 가지 proper sign flip D2를 유한 equivalence class로 보존한다.

\[
\mathcal C(Q,O)=\{(\lambda_1,\lambda_2,O^{(Q,D)}):D\in D_2\}.
\]

이것은 simple-spectrum Q 영역에서 9-dimensional generic orbit의 complete set-valued chart다. Q가 degenerate이면 별도 chart가 필요하고, O가 parity reversal될 때 generic SO(3) orbit은 구별될 수 있다. Random proper-rotation tests와 parity counterexample을 실행했다.

이 chart는 observer Q/O의 형상을 보존한다. Physical sigma/tilt chart가 되려면 Sections 6–8 같은 actual forward response가 여전히 필요하다.

## 10. R8 — bound를 실제 confidence set으로 사용하는 통계 설계

### 10.1 Composite forward model

관측 vector y를

\[
y=\mathcal L\,\mathcal B_\beta\,
\mathcal T[S(t),v(t),\omega(t),\mathrm{geometry}]+f_{fg}+n
\]

로 나타낸다. L은 mask/pixel/beam/estimator, B는 observer transformation, T는 physical forward response다. Global tilt는 T와 matter evolution 안에 들어가고 observer beta는 B에 들어간다. 이 두 역할을 교체할 수 없다.

MES는 theta의 feasible domain을 제한한다. 별도의 데이터가 아니므로 같은 CMB에서 계산한 bound를 독립 prior likelihood처럼 곱하지 않는다. 데이터로 결정된 normalization은 모든 pseudo-observation에 동일한 절차로 다시 적용해야 한다.

### 10.2 Exact-rank inversion

각 고정된 theta에서 observation과 simulated rows가 joint exchangeable이고 entire scoring이 permutation-equivariant라면 conservative finite rank p_theta를 정의할 수 있다. 이때

\[
\mathcal C_\alpha(y)=\{\theta:p_\theta(y)>\alpha\}
\]

는 true model에서 coverage >=1-alpha다. 이는 새로운 covariance-free physical confidence set의 가능 경로다. 실제 null generator의 fidelity를 증명하지 않은 상태에서 unconditional coverage를 주장하지 않는다.

관심 parameter psi와 nuisance eta가 있으면

\[
p_{sup}(\psi)=\sup_{\eta\in\mathcal N(\psi)}p(\psi,\eta)
\]

를 사용하면 true nuisance가 영역에 있는 경우 conservative inference를 유지한다. Coarse grid 최대값이나 local optimizer가 그 supremum을 보장하지는 않는다.

MES feasible set 자체가 확률 1-delta의 별도 confidence statement라면 intersection의 coverage는 최소 1-alpha-delta다. 같은 관측에서 만든 경험적 epsilon을 보장 없이 intersect하면 coverage를 잃을 수 있다.

### 10.3 Synthetic statistical checks

31-row tied integer pool에서 exact LOO midrank, monotone-transform invariance, row permutation 및 observation-inclusive conservative superuniform count를 검사했다. 이는 finite arithmetic/algorithm evidence이지 실제 Planck exchangeability 증명이 아니다.

## 11. 후보 비교와 반례

| 후보 | 판정 | 결정적 증거 또는 제한 |
|---|---|---|
| MES norm -> cubic/tensor feasible domain | SUPPORTED algebra, physical premise-conditional | discriminant, spectral bound, CAS, equality cases |
| Shear + genuine vector moment cone | SUPPORTED algebra | Gram PSD, spectral-projector recovery, sharp kappa bound |
| Tilt stress changes cubic shear shape | SUPPORTED in explicit Einstein–matter toy | q_total=0, independent Raychaudhuri integration, zero-tilt control |
| Q/O boost-response projection | SUPPORTED linear-response construction | closed-form inverse, rank3, orthogonal residual; intrinsic O prevents unrestricted identification |
| Inverse-square T Bianchi-I inverse | SUPPORTED in stated ideal model; general-use HYPOTHESIS | exact null quadratic + Lorentz eigenvector, 400 synthetic cases |
| Radiation-derivative/low-z inverse | SUPPORTED structural response; observational implementation deferred | Eq. (93) reduction, rank tests, missing derivative/selection evidence |
| Generic Q-eigenframe O chart | SUPPORTED on simple-Q stratum | complete finite-sign quotient and rotation tests |
| Same-row scalar/cubic bound treated as extra independent data | REJECTED | deterministic dependence, duplicated information |
| Triad rotation or observer beta called physical omega | REJECTED | different object and derivative requirements |
| Pure tr(omega^3) as new nonzero signal | REFUTED | antisymmetric trace is identically zero |
| Radial velocities alone identify solid rotation | REFUTED | n^TWn=0; exact synthetic null |
| Round trip alone verifies stored basis | REFUTED | wrong-basis physical-rotation counterexample |
| New results restore withdrawn Planck ranks | NOT_ATTEMPTED and not asserted | no actual observed-array rerun |

## 12. 실제 검증 요약

`results/final_tests.log`에는 34 passed가 기록되어 있다. 이 개수로 과학적 완성도를 측정하지 않는다. Load-bearing 검증은 actual stored-basis map reconstruction, independent spherical harmonics, norm/rotation counterexample, exact tensor algebra, constrained matter dynamics의 별도 Einstein formulation, model-mismatch residual, exact finite-rank arithmetic이다.

무작위 probes는 theorem의 대체물이 아니다. Theorem 부분은 Sections 2–10의 유도와 외부 symbolic residual에 의존하고, random probes는 implementation/special-case 오류를 찾는 역할이다.

그림은 모두 합성 또는 reference algebra의 그림이다. Planck 점을 새로 그린 것이 없다. `joint_shape_domain`은 admissible tensor domain, `tilt_shear_shape`는 실제 tilt-stress toy, `inverse_noise_sensitivity`는 ideal-model noise sensitivity, `basis_rotation_counterexample`은 알려진 carrier 오류를 검출하는 반례다.

## 13. 현재 데이터에 연결할 때 필요한 구분

보유 데이터 자체에 대한 사항은 사용자가 제공한 operational handoff를 근거로 한다. 이 세션에서 host 파일을 검사한 것은 아니다.

- Corrected Planck carrier: Q/O projection과 source-normalized MES 입력을 먼저 별개로 교정한다. 필요한 map-free parents가 보존되었다면 기존 map worker를 자동 재실행할 이유가 없다.
- Planck full map: inverse-square T의 제한된 model test에는 monopole/dipole, spectral-temperature convention, estimator response가 추가로 필요하다. Primordial stochastic sky와 foreground를 버리고 geometric signal로 단정할 수 없다.
- CF4: radial affine shear와 reconstructed velocity-gradient tensor를 구분한다. Curl은 reconstruction-conditioned다.
- DESI: positions/redshifts와 catalogue weights는 그 자체로 measured 3D peculiar velocity가 아니다. Distance calibration/window/selection가 필요하다.
- HSC/KiDS SACC: EE/B bandpower와 covariance는 개별 m-phase를 보존한 directional field가 아니다. 이 파일만으로 kinematic tensor를 되살릴 수 없다.
- ACT lensing kappa: kSZ temperature/remote dipole와 다른 observable이다. kSZ/pSZ 경로는 별도 maps/electron-tracer/optical-depth response를 필요로 한다.
- Native Bianchi solver: 여기서는 전달·검증되지 않았다. 일반 physical response T의 자리에는 아직 진짜 solver/response evidence가 필요하다. Analytic Bianchi-I toy가 그 전체 solver를 대신하지 않는다.

## 14. 종료 판정

이 cycle은 계획문서만 만든 것이 아니라 수식·반례·정확한 CAS·합성 evolution/inverse 실험·reference code를 생성했다. 하네스 독립 심사/최종 승격은 미수행이다. Scientific novelty, 실제 관측 constraints, updated Planck family ranks, full nonlinear tilted Boltzmann inversion은 아직 주장하지 않는다.

가장 가까운 의미 있는 후속 검증은 실제 저장된 carrier에 대해 **c -> complex a -> STF -> 원래 sky function** 및 **C_l -> PSTF norm -> MES coefficient** 두 경계를 함께 검증하는 것이다. 그 후 Q/O response와 tensor feasible body를 붙여 corrected map-free data analysis를 재실행하면 된다. 이 문서는 repository mutation이나 push를 수행하지 않는다.
