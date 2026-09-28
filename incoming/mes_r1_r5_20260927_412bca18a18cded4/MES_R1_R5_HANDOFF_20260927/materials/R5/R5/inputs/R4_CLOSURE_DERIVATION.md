# MES R4 — Lie algebra와 순간 metric으로 공간 미분을 닫는 정리

2026-09-27 KST. 독립 후보 유도자 산출물. 근거 상태: **derived**. 아래 정리는 해석적으로 유도했으며 이 문서에서 CAS 또는 과학 수치 runtime을 실행하지 않았다. 최종 독립 decision review 전이므로 후보 생성자가 PROMOTE를 선언하지 않는다.

입력: 현재 R3 보고서 전체, Astra v4.0.0 `PROJECT_INSTRUCTIONS.md`, `docs/MODEL_ROUTING.md`, `state/RESEARCH_STATE.md`를 읽었다. 원 하네스 state는 NOT_RUN template이며 과거 연구 증거가 아니다. 하네스 선택 근거는 사용자의 Astra 채택 선언이고 subagent의 실제 모델 identity를 별도로 인증하지 않았다.

## 1. 이번에 닫히는 범위

특정 Bianchi 이름을 고르지 않고 **Lie algebra + 순간 양의 공간 metric + 공간적 invariant radiation multipoles**로 R3의 공간 미분 연산자를 유한 행렬로 정확히 만든다. 순간의 시간 미분은 별도 jet 또는 검증된 물리식으로 제공한다. ODE/PDE 진화는 필요하지 않다.

이것은 전 운동학 성분이 자유로운 일반 congruence 정리가 아니다. 첫 정리는 homogeneous spacelike slice의 법선 congruence에 관한 것이다. 이 법선은 와도 0이며 lapse가 시간만의 함수이면 가속도도 0이다. Tilted congruence의 공간 projection은 이 slice의 Levi-Civita derivative와 다르다. 그 변환에는 extrinsic curvature, boost 및 그 미분이 필요하고 본 문서는 해당 확장을 승격하지 않는다.

## 2. 정확한 convention과 Koszul construction

한 순간의 3차원 Lie group에 invariant basis \(X_i\)를 잡고

\[
[X_i,X_j]=C^k{}_{ij}X_k,
\quad C^k{}_{ij}=-C^k{}_{ji},
\quad C^m{}_{[ij}C^l{}_{k]m}=0.
\]

양의 metric의 invariant 성분을 \(h_{ij}=\langle X_i,X_j\rangle\)라 하자. \(LhL^T=I\)인 행렬을 택하여 \(E_a=L_a{}^iX_i\)로 정규직교화한다. 공간 slice 내에서 \(L\)의 성분은 상수다. 구조계수와 connection은

\[
f^c{}_{ab}=L_a{}^iL_b{}^jC^k{}_{ij}(L^{-1})_k{}^c,
\quad [E_a,E_b]=f^c{}_{ab}E_c,
\]

\[
\gamma_{ab}{}^c:=\langle\nabla^{(3)}_{E_a}E_b,E_c\rangle,
\qquad
\boxed{2\gamma_{abc}=f_{abc}-f_{bca}+f_{cab}}.
\]

여기서 \(f_{abc}=f^d{}_{ab}\delta_{dc}\); \(\gamma_a\)의 행·열은 \((c,b)\)다. Covariant slot에는 그 transpose가 작용하며 아래 지표식을 권위로 한다. 따라서 metric compatibility \(\gamma_{abc}=-\gamma_{acb}\), torsion-free 조건 \(\gamma_{ab}{}^c-\gamma_{ba}{}^c=f^c{}_{ab}\)를 직접 확인할 수 있다. \(E_a\)를 물리 길이 미분으로 정하면 \(f,\gamma\)의 단위는 길이\(^{-1}\)이다. R3의 rate-normalized 미분은 \(\bar D_a=c\nabla^{(3)}_{E_a}\)이다.

## 3. 공간 jet closure 정리와 증명

Invariant covariant rank-\(r\) tensor \(T\)의 orthonormal 성분은 \(E_a T_{b_1\ldots b_r}=0\)이다. 정의

\[
(R_r(\gamma_a)T)_{b_1\ldots b_r}
=\sum_{j=1}^r\gamma_{ab_j}{}^dT_{b_1\ldots b_{j-1}d b_{j+1}\ldots b_r}
\]

를 쓰면

\[
\boxed{\bar D_a T=-cR_r(\gamma_a)T}.
\]

이 식은 근사가 아니고 homogeneous slice의 정확한 tensor derivative다. \(T\)가 symmetric/STF이면 마지막 \(r\)개 index의 성질은 보존되지만 새 derivative index까지 STF인 것은 아니다.

\[
G^2:=\sum_{a=1}^3\|\gamma_a\|_{\mathrm{op}}^2
\]

로 정의한다. 각 index slot에 작용하는 행렬의 tensor Hilbert-space operator norm은 \(\|\gamma_a\|_{\mathrm{op}}\)이므로 삼각부등식으로 \(\|R_r(\gamma_a)\|\le r\|\gamma_a\|\)이고,

\[
\boxed{\|\bar D T\|_F\le crG\|T\|_F}.
\]

두 번째 derivative에서는 첫 derivative index에도 connection이 작용한다. 전체 식은

\[
\boxed{
(\bar D_a\bar D_bT)_I
=c^2\left[R_r(\gamma_a)R_r(\gamma_b)
+\gamma_{ab}{}^dR_r(\gamma_d)\right]T_I.
}
\]

첫 항만 남기면 covariant Hessian이 아니다. 두 번째 항은 covariant index \(b\)의 connection이고 부호는 \(\bar D_bT=-cR_bT\)에 한 번 더 connection이 작용하여 양수가 된다. Invariant \(\bar DT\)는 rank \(r+1\) tensor이므로

\[
\boxed{\|\bar D^2T\|_F\le c^2r(r+1)G^2\|T\|_F}.
\]

이 상수들은 안전한 coarse bounds이고 sharp하다고 주장하지 않는다. 일반 \(m\)에 대해 \(\|\bar D^mT\|\le c^m(r)_mG^m\|T\|\)도 동일한 induction으로 따른다. \((r)_m=r(r+1)\cdots(r+m-1)\). Rank-0 invariant scalar의 모든 공간 미분은 0이다.

## 4. STF1/2/3 finite matrix와 sharp constant

\(\mathrm{STF}_r(\mathbb R^3)\)에 full Frobenius metric으로 정규직교화한 basis \(B_A^{(r)}\), \(A=1,\ldots,2r+1\)를 택한다. \(r=1,2,3\)의 입력 차원은 각각 3,5,7이다. 예를 들어 rank-2 basis에는

\[
\frac{\operatorname{diag}(1,-1,0)}{\sqrt2},\quad
\frac{\operatorname{diag}(1,1,-2)}{\sqrt6},\quad
\frac{e_i e_j^T+e_j e_i^T}{\sqrt2}\;(i<j)
\]

를 쓸 수 있다. Rank-3는 대칭 monomial tensors에 STF projector를 적용한 뒤 Gram matrix를 정규직교화하면 된다. 표현 계수 자체가 tensor norm인 것은 orthonormal basis를 썼을 때뿐이다.

\[
(M^{(r)}_1)_{aI,A}=-[R_r(\gamma_a)B_A^{(r)}]_I,
\]

\[
(M^{(r)}_2)_{abI,A}
=[R_r(\gamma_a)R_r(\gamma_b)+\gamma_{ab}{}^dR_r(\gamma_d)]B_A^{(r)}_I.
\]

이 행렬은 respectively \(3\cdot3^r\times(2r+1)\), \(9\cdot3^r\times(2r+1)\)의 redundant Cartesian representation으로 직접 만들 수 있다. Tensor 출력 norm은 일반 Frobenius이고 대칭 index 중복을 제거하면 그 multiplicity metric도 함께 변환해야 한다.

고정 \((C,h)\)에서 정확히 최적인 상수는

\[
\|\bar DT\|\le c\,s_{\max}(M_1^{(r)})\|T\|,
\quad
\|\bar D^2T\|\le c^2s_{\max}(M_2^{(r)})\|T\|.
\]

연산자별로 contraction/projector \(P\)를 먼저 적용한 \(PM\)의 최대 특이값을 쓰면 generic \(\sqrt3\) contraction bound보다 sharp하다. 필요한 연산자:

| R3 항 | 유한 행렬 정의 |
|---|---|
| \(\bar D_{\langle a}\vartheta_{b\rangle}\) | rank-1 \(M_1\) 출력 두 index의 symmetric tracefree projection |
| \(\bar D^b\vartheta_{ab}\) | rank-2 \(M_1\)의 derivative index와 둘째 tensor index contraction |
| \(\bar D^c\vartheta_{abc}\) | rank-3 \(M_1\)의 derivative index와 셋째 tensor index contraction |
| \(C_{ab}=\bar D_{[a}\vartheta_{b]}\) | rank-1 \(M_1\)의 antisymmetric projection |
| \(E_{ab}=\bar D_{[a}\bar D^c\vartheta_{b]c}\) | rank-2 \(M_2\)의 안쪽 derivative index와 둘째 tensor index contraction 후 \(a,b\) antisymmetrization |

마지막 행은 \(\tfrac12\sum_c[(\bar D_a\bar D_c\vartheta)_{bc}-(\bar D_b\bar D_c\vartheta)_{ac}]\)다. 순서가 있는 second derivative이고 connection derivative-index 항을 삭제하지 않는다. \(c\)와 \(c^2\)는 별도로 복원한다.

## 5. R3에 넣는 방식과 물리적 admission

\(S_1(C,h)\)를 STF-gradient, \(V_3(C,h)\)를 rank-3 divergence의 **길이 미분** 행렬이라 하면 R3 first-order radiation identity는

\[
\sigma=-\dot\vartheta_2-cS_1\vartheta_1-\frac{3c}{7}V_3\vartheta_3+\eta_2.
\]

따라서 독립적인 \(\bar D\vartheta_1,\bar D\vartheta_3\) 가정을 요구하는 대신 \(C,h,\vartheta_1,\vartheta_3\)의 공동 허용집합으로 공간항을 닫는다. 예를 들어 coarse scalar bound는

\[
\|\sigma\|\le\|\dot\vartheta_2\|+cG\|\vartheta_1\|
+\frac{9\sqrt3}{7}cG\|\vartheta_3\|+\|\eta_2\|.
\]

핵심 사용 방식은 이 scalar bound가 아니라 위 finite matrix image다. 방향·morphology와 입력 간 correlation을 보존할 수 있다.

법선 congruence는 \(\omega=0\). Homogeneous lapse이면 \(A=0\)도 성립한다. 따라서 같은 branch의 dipole/curl 식을 자유로운 nonzero \(A,\omega\)를 추정하는 공식으로 사용해서는 안 된다. 그 식들은 방사장/source jets 사이의 consistency equations로 남는다. Nonzero \(A,\omega\)를 보려면 tilted congruence 또는 덜 강한 symmetry의 별도 geometric jet admission이 필요하다.

\(\dot\vartheta_r\)는 공간 closure로 정해지지 않는다. \(\dot C_{ab}\)를 쓰려면 Fermi–Walker temporal frame에서 \(\dot M\vartheta+M\dot\vartheta\)가 필요하다. \(\dot M\)는 instantaneous metric/extrinsic-curvature jet와 tetrad rotation convention에서 대수적으로 정해질 수 있지만, 이를 입력하지 않고 \(\dot M=0\)이라 놓을 수 없다. Einstein constraints 또는 matter model을 요구하는 응용에서는 그 admissibility도 공동 집합에 포함한다.

## 6. Metric uncertainty와 Lie algebra만의 한계

고정 basis에서 \(h\mapsto\lambda^2h\)이면 \(L\mapsto L/\lambda\), \(f\mapsto f/\lambda\), \(\gamma\mapsto\gamma/\lambda\), \(G\mapsto G/\lambda\)이다. Abstract \(C^k{}_{ij}\)는 그대로다. 그러므로 Lie algebra alone은 물리적인 derivative rate를 제한하지 못한다. 이는 Bianchi classification의 문제가 아니라 metric scale의 문제다.

반면 \(mI\preceq h\preceq MI\), \(0<m<M<\infty\) 같은 compact positive metric domain \(\mathcal H\)와 고정 gauge의 연속 tetrad selection을 주면 모든 \(M(C,h)\)는 연속이고

\[
\sup_{h\in\mathcal H}s_{\max}(M(C,h))<\infty.
\]

그러면 유계 multipole/time-jet/source 집합 \(\mathcal U\)의 정확한 conditional image

\[
\mathcal K=\bigcup_{h\in\mathcal H}\{L(C,h)J:J\in\mathcal U(h)\}
\]

가 유계다. Compactness에는 \(\mathcal U(h)\)의 그래프도 compact해야 한다. Metric uncertainty와 radiation coefficients의 correlation을 지우지 않는다. 고정 metric에서는 선형 image, 불확실 metric에서는 일반적으로 union이며 convex일 필요 없다. Convex hull은 directional support를 보존하지만 물리적 attainable set과 같다고 주장하지 않는다. 다른 tetrad의 tensor 비교에는 명시한 common-frame map이 필요하다.

이것이 solver 없는 productive minimum: **Lie algebra + compact metric/extrinsic jet + finite radiation moments/time jets/source budgets**. 완전한 spacetime evolution은 필수 입력이 아니다. 모두를 한 사건에서 관측했다는 주장은 별도다.

## 7. 모든 운동학량을 유지하는 정확한 homogeneous tilt jet adapter

이 절은 parent의 후속 요청에 대한 추가 유도다. 앞 절의 normal branch를 nonzero \(A,\omega\)로 일반화하려면 radiation evolution 전체를 풀기보다 **순간 1-jet**를 추가하면 된다. 다음 식은 작은 tilt 전개가 아닌 정확한 geometric identity다. R3의 radiation equations에 대입할 때는 그 식 자체의 일차 근사 조건을 별도로 유지해야 한다.

Spacetime orthonormal tetrad를 \(E_0=n,E_i\), \(g(n,n)=-1\), \(\eta_{AB}=\operatorname{diag}(-1,1,1,1)\)로 정한다. 모든 \(E_A\)는 길이 미분이다. Connection coefficient convention은

\[
\nabla_{E_A}E_B=\Omega_{AB}{}^C E_C,
\qquad\Omega_{ABC}=\eta_{CD}\Omega_{AB}{}^D=-\Omega_{ACB}.
\]

Geodesic normal과 Fermi–Walker spatial frame이면 순간의 full connection은

\[
\Omega_{00}{}^A=0,\qquad\Omega_{0i}{}^A=0,
\]

\[
\Omega_{i0}{}^j=K_{ij},\qquad
\Omega_{ij}{}^0=K_{ij},\qquad
\Omega_{ij}{}^k=\gamma_{ij}{}^k,
\]

로 정해진다. 여기서 \(K_{ij}=\langle\nabla_{E_i}n,E_j\rangle\)는 길이\(^{-1}\) 단위의 geometric extrinsic-curvature tensor이며 symmetric이다. Normal congruence의 물리 팽창률은 \(\Theta_n=c\operatorname{tr}K\). 다른 sign의 extrinsic curvature convention을 쓰면 입력에서 먼저 변환한다. 시간 회전 gauge \(W_i{}^j=\Omega_{0i}{}^j\)를 허용할 때에는 이를 skew matrix로 명시하고 아래 \(\Omega\)에 그대로 넣는다. Homogeneous lapse를 벗어나면 normal acceleration connection도 별도 입력이다.

Homogeneous tilt field와 normal-frame 시간 coefficient derivative를

\[
U^A=c\gamma w^A,
\quad w^A=(1,\beta^i),\quad w_A=(-1,\beta_i),
\quad\gamma=(1-\beta^2)^{-1/2},
\]

\[
E_i\beta_j=0,\qquad b_j:=cE_0\beta_j
\]

로 둔다. \(b_j\)는 선택한 tetrad 성분의 시간 derivative이며 frame rotation을 자동으로 포함한 invariant derivative와 혼동하지 않는다. \(E_0\gamma=\gamma^3\beta\cdot b/c\)로부터

\[
\boxed{
B_{AB}:=\nabla_{E_A}U_B
=\delta_A{}^0\!\left[\gamma^3(\beta\cdot b)w_B
+\gamma(0,b_i)_B\right]
-c\gamma\Omega_{AB}{}^Cw_C.
}
\]

각 항은 시간\(^{-1}\). 필요한 입력은 \((C,h,K,\beta,b,W)\), 또는 이들의 동치인 full tetrad connection/tilt jet다. \(\beta\)의 값만으로는 \(b\)를 정할 수 없다.

\(u^A=U^A/c\), \(P_A{}^B=\delta_A{}^B+u_Au^B\), \(P_{AB}=\eta_{AB}+u_Au_B\)라 두면

\[
\Theta=\eta^{AB}B_{AB},\qquad
A_B=U^A B_{AB},\quad a_B=A_B/c,
\]

\[
\mathcal B_{AB}=P_A{}^C P_B{}^D B_{CD},
\quad\sigma_{AB}=\mathcal B_{(AB)}-\frac{\Theta}{3}P_{AB},
\quad\Omega^{(u)}_{AB}=\mathcal B_{[AB]}.
\]

\(u\)의 rest frame에서 \(\epsilon^{(u)}_{123}=+1\)인 오른손 orientation을 고정하여 \(\omega_A=\tfrac12\epsilon^{(u)}_{ABC}\Omega^{(u)BC}\)로 dualize한다. 이 derivative-first vorticity convention은 R3와 같다. \(B_{AB}U^B=0\), \(A\cdot U=0\), \(\sigma\)와 \(\Omega^{(u)}\)의 모든 index가 \(U\)에 수직인 것은 \(U^2=-c^2\)와 projectors에서 곧바로 따른다.

이것은 \(\Theta,\sigma,\omega,A,\beta\)를 동시에 출력하는 finite algebraic adapter다. \(\beta=0,b=0\)이면 \(\Theta=c\operatorname{tr}K\), \(\sigma=c(K-\operatorname{tr}K\,I/3)\), \(A=\omega=0\)으로 복귀한다. 한 사건에서 \(\beta=0\)이나 \(b\ne0\)인 경우에는 그 순간 정상계와 속도는 일치하더라도 \(A=cb\)가 남는다. 따라서 beta 값의 일치가 congruence jet의 일치를 뜻하지 않는다.

동일한 이유로 tilted spatial derivative는 invariant tensor에서도 시간 jet를 포함한다. Homogeneous spacetime covariant tensor \(T_{I_1\ldots I_r}\)에 대해 \(\dot T^{(n)}:=cE_0T\)를 tetrad coefficient derivative라 정의하면

\[
\boxed{
\bar D^{(u)}_A T_{I_1\ldots I_r}
=P_A{}^B\prod_{s=1}^rP_{I_s}{}^{J_s}
\left[
\delta_B{}^0\dot T^{(n)}_{J_1\ldots J_r}
-c\sum_{s=1}^r\Omega_{BJ_s}{}^K
T_{J_1\ldots K\ldots J_r}
\right].
}
\]

\(P_i{}^0=\gamma^2\beta_i\)이므로 \(\beta\ne0\)에서 시간 jet term을 지울 수 없다. \(\beta=0\)이고 \(T\)가 normal-spatial이면 앞의 pure spatial Koszul operator로 환원된다. Tilted second derivatives에는 이 projector/connection의 derivatives와 second time jets도 생기므로 rank-\(r\) normal bound를 그대로 전용하지 않는다.

Metric/connection/tilt/time-jet를 모두 포함하는 전체 joint input domain이 compact하고 \(|\beta|\le\beta_*<1\)이면 위 map은 연속이며 모든 출력 운동학량의 image가 compact하다. 단지 bounded한 b만으로 image의 closedness를 단정하지 않는다. 이 joint image를 R2/MES normalization과 연결할 수 있다. 그러나 \(\beta\to1\)을 허용하거나 time jet가 unbounded이면 이 결론은 사라진다. Einstein/matter constraints 및 관측으로 허용되는 입력은 이 geometric adapter와 별개의 admission 조건이다. 이 exact adapter는 **derived, CAS 미실행**이며 독립 검토 대상이다.

## 8. 표면 amplitude에서 spacetime jet가 나오지 않는 정확 witness

Minkowski에서 inertial observer \(U=\partial_t\), straight photon direction \(e\)와

\[
T_k(t,x,e)=T_0[1+\epsilon\sin(k(x^1-ce^1t))],\quad0<\epsilon<1,
\]

\[
f_k=\left[\exp\!\left(\frac{E}{k_BT_k}\right)-1\right]^{-1}
\]

를 택한다. \((\partial_t+ce^i\partial_i)T_k=0\)이므로 정확한 collisionless Liouville solution이며 방향별 Planckian이고 양수다. 모든 \(k\)에 대해 \(|T_k/T_0-1|\le\epsilon\), \((t,x)=(0,0)\)의 하늘은 정확히 isotropic이다. 그러나 그 사건에서

\[
\partial_1\ln\rho=4\epsilon k,
\quad \dot\vartheta_{1i}=-c\epsilon k\delta_{i1},
\quad \bar D_i\ln\rho=4c\epsilon k\delta_{i1}.
\]

따라서 \(k\)로 spacetime jets를 크게 만들 수 있다. R3의 acceleration 조합은 \(-\dot\vartheta_1-\bar D\ln\rho/4=0\)으로 정확히 상쇄된다. 이 witness는 개별 jet를 독립 ball로 놓는 방식이 실제 correlation을 잃을 수 있음도 보여준다.

범위 제한: 이것은 test radiation의 exact transport counterexample이지 self-consistent Einstein–matter spacetime family나 large-shear counterexample가 아니다. 따라서 특정 matter/symmetry 가정하의 MES-type kinematic bound를 반박했다고 해석하지 않는다. 관측된 한 하늘의 smallness에서 미분 예산을 자동 획득할 수 없다는 충분한 예시다.

생산적인 수리적 대안은 위 invariant spatial closure, 별도 derivative measurement, 또는 물리적으로 정당화된 spatial spectral cutoff/Sobolev budget이다. Angular \(\ell_{\max}\) cutoff만으로 spatial \(k_{\max}\)가 생기지는 않는다.

## 9. Cold Thomson/kSZ가 닫아주는 정확한 양

R3 convention에서 \(\delta:=\beta_e-\vartheta_1\)라 두면 \(\eta_1=\Gamma\delta\), \(\Gamma=cn_e\sigma_T\). 일차 Lorentz flux transformation으로 electron frame의 propagation-direction dipole는 \(-\delta\)이고 outward-sky dipole는 \(+\delta\)이다. Standard thin-scattering kSZ branch는

\[
y(n)=-\int d\tau\,\delta\cdot n+r,
\quad d\tau=n_e\sigma_Td\ell.
\]

그러므로 직접 측정하는 것은 optical-depth weighted line-of-sight remote dipole이다. Intrinsic radiation dipole를 제거하지 않고 \(\delta=\beta_e\)라고 동일시하지 않는다. Optical-depth attenuation을 쓰면 \(e^{-\tau}\)를 kernel 안에 포함하고 kernel mass를 그에 맞게 정의한다.

한 선택된 shell에서 positive kernel mass \(\tau\in[\tau_-,\tau_+]\), \(\tau_->0\), aggregate residual \(|r|\le r_*\)라면 weighted scalar mean \(\bar\delta_\parallel\)에 대해

\[
\bar\delta_\parallel\in
\bigcup_{\tau\in[\tau_-,\tau_+]}\left[\frac{-y-r_*}{\tau},\frac{-y+r_*}{\tau}\right],
\quad
|\bar\delta_\parallel|\le\frac{|y|+r_*}{\tau_-}.
\]

측정 잡음 confidence allowance는 동일 aggregate residual/joint likelihood에 넣는다. \(\beta_e\)로 바꾸려면 \(\vartheta_1\)의 공동 bound가 필요하다. Pointwise 값으로 바꾸려면 within-bin variation/coherence bound가 필요하다. 서로 다른 하늘 방향은 다른 사건이므로 하나의 3-vector를 세 방향에서 측정했다고 합칠 수 없다. Coherent bulk tensor/finite-basis 가정을 선언할 때만 finite response matrix로 결합한다.

유한 integrated \(\tau\)만으로 pointwise \(\Gamma_{\min}>0\), \(\Gamma_{\max}\), \(\bar D\Gamma\) bound가 생기지 않는다. 같은 적분의 smooth 좁은 positive bump와 density trough를 만들 수 있기 때문이다. 실제 quadratic kSZ estimator에는 galaxy–electron correlation의 multiplicative optical-depth bias가 추가로 있으며, map을 이미 보정된 \(\delta\) 관측으로 취급할 수 없다.

별도로 \(\Gamma\le\Gamma_+\), \(\|\delta\|\le d_*\), \(\|\bar D\Gamma\|\le g_*\), \(\|\bar D\delta\|_F\le m_*\)를 정당화하면

\[
\|\eta_1\|\le\Gamma_+d_*,\qquad
\boxed{\|\bar D_{[a}\eta_{1b]}\|_F
\le g_*d_*/\sqrt2+\Gamma_+m_*}.
\]

첫 항은 \(\|g_{[a}d_{b]}\|_F^2=(|g|^2|d|^2-(g\cdot d)^2)/2\)에서 나온다. 이때 R3 acceleration/curl budget가 닫힌다. Tilt 역산에는 추가 \(\Gamma_->0\)가 필요하지만 source의 순방향 upper bound에는 필요 없다. \(\Gamma=0\) branch에서 source는 0이고 해당 channel의 tilt response는 없어지는 것이 정상이다.

## 10. 원전 확인과 실행 경계

- Räsänen, *On the relation between the isotropy of the CMB and the geometry of the universe*, arXiv:0903.3013, §III Theorem 2 및 Eq.(20)–(22): anisotropy amplitude와 그 spacetime derivatives를 구별해야 함. 원문에서 해당 구간을 확인했다. Supports the information boundary; 본 counterexample와 Lie closure의 직접 유도 출처로 주장하지 않음. https://arxiv.org/pdf/0903.3013
- Deutsch et al., *Reconstruction of the remote dipole and quadrupole fields…*, arXiv:1707.08129, §II 및 Appendix A/B: kSZ remote dipole, shell averages, Doppler와 primordial 기여 및 bin cancellation. 해당 구간을 확인했다. https://arxiv.org/pdf/1707.08129
- Bloch–Johnson, *Kinetic Sunyaev Zel’dovich velocity reconstruction from Planck and unWISE*, arXiv:2405.00809v2, §II Eq.(1)–(3), (14)–(15): integral observable 및 estimator window, optical-depth modeling bias. 해당 구간을 확인했다. HTML abstract와 introduction에 서로 다른 수치 상한이 표시되어 있어 이 메모는 어느 수치도 채택하지 않는다. https://arxiv.org/html/2405.00809v2

웹 식별자는 root 전달용: `turn3view2`/`turn10view1` (Räsänen), `turn3view1`/`turn5view0` (Deutsch), `turn3view0`/`turn10view0` (Bloch–Johnson). Root 최종 citation 전에는 root가 해당 원문을 직접 열어야 한다.

실제 수행: 원문/첨부 읽기, 해석 유도, 이 메모 작성. 미수행: Wolfram 재실행, Python/C++ science runtime, 데이터 fit, source/repo mutation, 독립 decision review. Root가 finite matrices를 검산할 경우 second-derivative index-slot term 및 normal/tilted restriction을 핵심 acceptance 조건으로 삼는다.

### 최초 typesetting defect 보존

Root의 원문 검토에서 §3 boxed second-derivative 식의 두 항 사이 `+`가 빠진 조판 결함을 발견했다. §4 finite-matrix 식과 유도 설명에는 올바른 `+`가 이미 있었다. 최초 출력은 두 항이 곱인 것처럼 읽힐 수 있었으며, 지적 후 §3에 누락된 `+`만 복원했다. 이는 독립 decision 판정이나 과학 계산 재실행의 결과가 아닌 원문 조판 수정이다.

## 11. 후속 검산 연결

위 본문은 초기 직접 유도의 상태를 보존한다. 이어 수행한 exact Wolfram fixture 검산은 `verification/CAS_GEOMETRY_TILT_RECEIPT.json` 및 V2 raw에 있으며 rank1/2/3 두 geometry, finite-tilt projection과 정상 극한을 확인했다. 최초 V1 구현 오류도 원본 보존했다. Code gamma matrix는 row b,column d이므로 본문 row d,column b의 transpose다. 일반 정리는 해석적 증명이 근거이며 fixture 검산만으로 보편성을 주장하지 않는다.
