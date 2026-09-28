# MES R5 — 유한 tilt 공동 텐서 연산자와 시간 jet 식별 조건

작성: 2026-09-27 KST · 기준: R4 conditional theory · 방식: 해석적 유도, 가벼운 Wolfram CAS, 별도 독립 판정

## 0. 이번 루프의 결론

R4의 homogeneous tilted 1-jet를 **12개 운동학 성분으로 가는 rank 9 affine map**으로 정리했다. Normal에 대한 tilt \(p=\beta\)와 Lie geometry를 고정하면 다음 세 성분 관계가 정확하다.
\[
\boxed{\omega-\tfrac12\beta\times(A/c)=S w_C.}\tag{1}
\]
이 관계는 \(\dot\beta\)와 extrinsic curvature의 미지 성분에 의존하지 않는다. 시간 jet를 제한하지 않아도 남는 joint 정보이며, 개별 전단이나 가속도의 상한과 구별된다.

반면 R3의 retained 1차 복사식에서는 dipole·quadrupole coefficient의 시간 미분 8개가 자유로우면 해당 8개 식이 운동학에 추가 제약을 주지 않는다. 이를 모든 \(|\beta|<1\)에서 가역인 Schur complement로 증명했다. 필요한 정보는 관심 target으로 전달되는 시간·산란 nuisance 조합의 제한이다.

비가환 Lie algebra와 \(\beta=(0,3/5,0)\)에서 전단·와도·가속도의 정확한 공동 원판을 구성했다. 같은 latent state로 \(T,Q_{\rm outer},F_{\rm amp},D,\Pi_{\rm tail},G_{\rm tensor}\)까지 계산하며 확률법칙이 필요한 출력은 구별했다.

이 결과는 한 사건의 조건부 기하·식별성 정리다. Einstein/matter admissibility, 전 우주의 비선형 MES 정리, 실관측 백분율은 확인하지 않았다. 새 exact quadrupole·finite-electron Thomson 유도는 미검증 탐색 후보로 보관하고 이번 채택에서는 제외했다.

## 1. 입력 계약과 기준의 연속성

R4 보고서·기하 유도·독립 판정의 SHA-256을 현재 세션에서 확인했다. 원 동기는 모든 운동학량의 방향·부호·상관을 유지한 동일 관측조건/MES 기준 비교다. R4 공간 미분 정리나 세 거리 보상식은 다시 증명하지 않았다.

고정 시점 입력은
\[
(C,h,\text{frame gauge},p,q,b,\rho,t_1,t_2,t_3,v_0,v_1,v_2,v_3,\eta,\mathcal R,\nu).
\]
\(C\)는 Lie 구조상수, \(h>0\)는 순간 공간 metric, \(q=cK=q^T\), \(b=cE_0p\), \(t_\ell=\vartheta_\ell\)는 target rest frame의 brightness-normalized PSTF multipole, \(v_\ell=cE_0t_\ell\), \(v_0=cE_0\log\rho\)다. \(\eta\)는 source, \(\mathcal R\)은 생략한 비선형 항의 allowance, \(\nu\)는 관측·frame·거리 nuisance다. \(\rho>0\)를 전제한다. Planckian 조건 없이 brightness multipole를 온도 multipole라고 부르지 않는다.

| 입력 또는 가정 | R5 상태 |
|---|---|
| Lie Jacobi, positive \(h\), geodesic normal, Fermi triad | 명시한 기하 branch의 전제 |
| \(p\) 고정, \(|p|<1\) | 정확 affine 연산자의 조건 |
| 불확실 \(p\), metric/source/jet domain | 동일 joint set에서 처리; compactness에는 \(|p|\le p_*<1\) 등 추가 조건 필요 |
| Einstein constraints, matter closure, evolution | 미검증 gate |
| 실제 selected catalog·CMB likelihood·joint covariance | 이번 입력에 없음 |
| 실제 MES denominator | R3–R4의 premise-matched reference 유지 |
| \(\Theta,\beta\)의 보편적 MES ceiling | 도입하지 않음 |

\(p=\beta_{U|n}\)와 electron의 \(\beta_{e|U}\)는 다르다. 유한 상대속도 합성을 단순 뺄셈으로 대체하지 않는다.

## 2. 정확한 기하 연산자

계량은 \((-+++)\), \(U^2=-c^2\), 길이 미분 tetrad \(E_A\)를 사용한다. Normal은 \(E_0\), \(E_ip_j=0\). Orthonormal 구조상수 \(f^k{}_{ij}\)와 spatial connection은
\[
[E_i,E_j]=f^k{}_{ij}E_k,\qquad
2\gamma^k{}_{ij}=f^k{}_{ij}-f^i{}_{jk}+f^j{}_{ki}.
\]
첫 index는 미분 방향이다. Lorentz factor는 connection과 구별하여 \(g=(1-p^2)^{-1/2}\)로 쓴다.
\[
S=I+\frac{g^2}{g+1}pp^T,\quad
W=S^{-1}=I-\frac{g}{g+1}pp^T,\quad
L_{ij}=-c\gamma^k{}_{ij}p_k.\tag{2}
\]
Companion의 역 boost 행렬 \(T\)를 이 보고서에서는 \(W\)로 쓴다. Normalized tensor \(T\)와 구별하기 위해서다. \(Sp=gp,\ Wp=p/g,\ Lp=0\).

Proper boost로 \(e'_0=g(E_0+p_iE_i)=U/c,\ e'_i=gp_iE_0+S_{ij}E_j\)를 정한다.
\[
B_{ij}=\langle\nabla_{e'_i}U,e'_j\rangle,\quad a_i=A(e'_i)/c
\]
이면
\[
\boxed{
B=gS(q+L)W+g^2p(Sb)^T,\qquad
a=g^2\{Sb+W(q+L)^Tp\}.
}\tag{3}
\]
\(b\)를 제거하면
\[
\boxed{B-pa^T=gW(q+L)W.}\tag{4}
\]
\(B,a,q,b,L\)의 단위는 \({\rm s}^{-1}\), \(A=ca\)다. 운동학은
\[
\Theta=\operatorname{tr}B,\quad \sigma=\operatorname{STF}B,\quad
\Omega=(B-B^T)/2,\quad \omega_i=\tfrac12\epsilon_{ijk}\Omega_{jk},
\quad\epsilon_{123}=1.\tag{5}
\]
Derivative-first 와도 convention이며 \(\|\Omega\|_F=\sqrt2\|\omega\|\). 다른 문헌의 와도 부호를 무조건 가져오지 않는다.

### 2.1 명시적 12×9 map과 역산

Symmetric Frobenius-orthonormal basis \(H_\alpha\) 6개에 \(q=\sum q_\alpha H_\alpha\), \(j=(q_1,\ldots,q_6,b_1,b_2,b_3)\)를 둔다. Eq. (5)의 extraction을 \(\mathcal E(B,a)\)라 쓰면
\[
k=(\Theta,\sigma_{1..5},\omega_{1..3},a_{1..3})=k_C+\mathsf A(p)j,
\]
\[
\begin{aligned}
k_C&=\mathcal E(gSLW,g^2WL^Tp),\\
\mathsf A_{q,\alpha}&=\mathcal E(gSH_\alpha W,g^2WH_\alpha p),\\
\mathsf A_{b,r}&=\mathcal E(g^2p(Se_r)^T,g^2Se_r).
\end{aligned}\tag{6}
\]
Scalar norm 전에 이 carrier를 유지한다. \(\beta\)는 conditioning input이면서 joint state의 보존 대상이다.

역산은
\[
\boxed{q=g^{-1}S(B-pa^T)S-L,\qquad b=W(a-B^Tp).}\tag{7}
\]
따라서 모든 \(|p|<1\)에서 \(\operatorname{rank}\mathsf A=9\). 유한 CAS fixture가 아니라 이 injective inverse가 일반 증명이다.

\(q=q^T\)와 동치인 세 affine compatibility equations는
\[
(w_C)_i=-\frac c4\epsilon_{ijk}f^l{}_{jk}p_l,\qquad
\boxed{\omega-\tfrac12p\times a=Sw_C}.\tag{8}
\]
증명: \(L_{[ij]}=-cf^k{}_{ij}p_k/2\)와
\(\operatorname{axial}(W\Omega W)=\det(W)W^{-1}\operatorname{axial}(\Omega)\),
\(g\det W=1\)을 Eq. (4)에 적용한다. 이 세 식 이외의 숨은 선형 compatibility constraint는 없다.

Rank 9는 이 homogeneous branch의 잠재 자유도다. 관측 응답의 rank 또는 R3 일반 congruence의 ideal rank 12와 동일하지 않다. 불확실 \(p\)를 넣으면 \(p\)-dependent affine images의 합집합이다.

## 3. 자유 시간 jet가 남기는 정보

고정 \(q,C,h,p\)에서 \(g^2S\)가 가역이므로 \(b\) 변화는 임의 \(z\in\mathbb R^3\)에 대해
\[
\delta a=z,\quad \delta B=pz^T,\quad
\delta\Theta=p\cdot z,\quad
\delta\sigma=\operatorname{STF}(pz^T),\quad
\delta\omega=\tfrac12p\times z\tag{9}
\]
를 만든다.

- \(p=0\): \(B=q,a=b,\omega=0\). 자유 시간 jet는 가속도에만 영향을 준다.
- \(p\ne0\): 가속도·전단 및 적절한 방향의 expansion에 유한 상한이 없다.
  \(\|\operatorname{STF}(pz^T)\|_F^2=p^2z^2/2+(p\cdot z)^2/6\).
- 와도의 자유 변화는 \(p^\perp\)의 2차원뿐이다. \(p\cdot\omega=p\cdot Sw_C\)는 고정된다.

다음 결합량은 \(b\)와 무관하다.
\[
\boxed{\Theta-p\cdot a,\quad
\sigma-\operatorname{STF}(pa^T),\quad
\omega-\tfrac12p\times a.}\tag{10}
\]
가운데 결합량을 물리적 shear로 재명명하지 않는다. 구성량들의 공동 관측 응답이 필요하다.

임의로 큰 \(b\)도 한 사건 근방의 충분히 짧은 구간에서는 \(|p(t)|<1\)인 smooth congruence로 실현할 수 있다. Fixed-duration derivative budget이나 matter evolution을 부여했다면 그 제약이 추가된다. 위 family를 모든 물리적 cosmology의 반례로 확대하지 않는다.

### 3.1 부분 target boundedness 정리

고정 geometry와 \(p\)에서 \(\mathcal J=\mathcal J_0+N\)을 가정한다. \(\mathcal J_0\)는 **비어 있지 않은 compact set**, \(N\)은 제한 없이 허용된 linear subspace다. 선형 target \(Pk\)의 image는
\[
P k_C+P\mathsf A\mathcal J_0+P\mathsf A N
\]
이므로
\[
\boxed{\text{target image bounded}\iff P\mathsf A N=\{0\}.}\tag{11}
\]
우향이면 compact image, 아니면 \(P\mathsf Av\ne0\)인 \(v\in N\)의 무한 ray가 증명한다.

이는 arbitrary nonconvex domain의 recession cone만 검사하는 일반 정리가 아니다. 관측으로 domain을 자른 후에도 compact transverse section 계약을 확인해야 converse를 적용한다. Empty feasible set는 모형/자료 불일치이며 “강한 상한”으로 보고하지 않는다.

## 4. 정확한 frame·시간 미분 adapter

\(e'_\alpha=\Lambda_\alpha{}^AE_A\)로 쓰자. Full normal connection은
\[
\Gamma^A{}_{00}=\Gamma^A{}_{0i}=0,\quad
\Gamma^j{}_{i0}=K_{ij},\quad
\Gamma^0{}_{ij}=K_{ij},\quad
\Gamma^k{}_{ij}=\gamma^k{}_{ij}.
\]
Exact transformed connection은
\[
\Gamma'^\delta{}_{\alpha\beta}
=\Lambda_\alpha{}^A
\left(E_A\Lambda_\beta{}^C+\Lambda_\beta{}^B\Gamma^C{}_{AB}\right)
(\Lambda^{-1})_C{}^\delta.\tag{12}
\]
\(\Lambda\)의 시간 미분은 \(b=cE_0p\)로 계산한다. \(c\Gamma'\)는 고정 \(C,h,p\)에서 \(q,b\)의 affine 함수다. Normal lapse acceleration/triad rotation이 있으면 해당 성분을 먼저 추가해야 한다.

Rest triad 성분 \(t_{i_1\cdots i_r}\)가 homogeneous이고 \(v=cE_0t\)이면 projected derivatives는
\[
\begin{aligned}
\dot t_{i_1\cdots i_r}
&=g v_{i_1\cdots i_r}
-c\sum_m\Gamma'^j{}_{0i_m}t_{i_1\cdots j\cdots i_r},\\
\bar D'_i t_{i_1\cdots i_r}
&=gp_i v_{i_1\cdots i_r}
-c\sum_m\Gamma'^j{}_{ii_m}t_{i_1\cdots j\cdots i_r}.
\end{aligned}\tag{13}
\]
Scalar에는 slot sum이 없으므로 \(\bar D'_i\log\rho=gp_i v_0\).
Normal spatial homogeneity가 tilted-rest spatial derivative를 0으로 만들지는 않는다.

이 adapter는 finite \(p\)에서 정확하다. 다음 retained 복사식을 finite-anisotropy exact law로 만드는 것은 아니다.

## 5. R3 retained radiation operator의 rank 8

R3 1차 dipole·quadrupole 식에 signed nonlinear residual \(\mathcal R\)을 쓰면
\[
\begin{aligned}
0={}&a+\dot t_1+\tfrac14\bar D'\log\rho
+\tfrac25\operatorname{div}'t_2-\eta_1-\mathcal R_a,\\
0={}&\sigma+\dot t_2+\operatorname{STF}(\bar D't_1)
+\tfrac37\operatorname{div}'t_3-\eta_2-\mathcal R_\sigma .
\end{aligned}\tag{14}
\]
Exact nonlinear model 없이 \(\mathcal R=0\)으로 놓고 비선형 결론을 내리지 않는다.

고정 \(p,C,h,t_\ell\)에서 Eqs. (6),(12),(13)을 대입하면
\[
\mathsf E j+g\,\mathsf F_{12}(v_1,v_2)
+g\left(\tfrac14pv_0,\ \tfrac37(v_3\cdot p)\right)
-\eta-\mathcal R=d.\tag{15}
\]
\(\mathsf E,d\)는 위 slot formulas로 완전히 구성되며 \(q,b\)는 기하식과 **동일한** latent variables다. 시간 jet의 8×8 block은
\[
\boxed{\mathsf F_{12}(x,Y)=
\left(x+\tfrac25Yp,\quad Y+\operatorname{STF}(px^T)\right)},
\quad x\in\mathbb R^3,\ Y\in{\rm STF}_2.\tag{16}
\]

**정리.** 모든 \(|p|<1\)에서 \(\mathsf F_{12}\)는 가역이다.

**증명.** 둘째 식으로 \(Y\)를 제거하면
\[
M_px=\left[\left(1-\frac{p^2}{5}\right)I-\frac1{15}pp^T\right]x,\tag{17}
\]
왜냐하면 \(\operatorname{STF}(px^T)p=p^2x/2+(p\cdot x)p/6\)이기 때문이다.
\(M_p\)의 고유값은 \(p^\perp\)에서 \(1-p^2/5\) 두 개, 평행방향에서 \(1-4p^2/15\) 하나다. 모두 양수이며
\[
\det\mathsf F_{12}=(1-p^2/5)^2(1-4p^2/15)>0.\tag{18}
\]
Actual derivative block \(g\mathsf F_{12}\)의 determinant에는 \(g^8\)이 곱해진다. □

따라서 \((v_1,v_2)\)가 전공간을 자유롭게 순회하는 retained algebraic model에서는 Eq. (14)만으로 \(a,\sigma\)에 추가 제약이 생기지 않는다. Source/remainder를 고정해도 그렇다. Source \(\eta\) 8성분이 자유인 경우도 마찬가지다.

이는 물리적 시간발전이 임의라는 주장이 아니다. 큰 jets가 weak-regime, positivity, finite-time data, matter constraints를 벗어나면 해당 영역을 joint domain에서 제거해야 한다. 위 논증으로 실제 우주의 무한 전단을 주장하지 않는다.

### 5.1 최소 추가 정보의 형식

일반 관계 \(\mathsf E j+\mathsf Fv-\eta=d+\mathcal R\)에서
\(\mathcal N_{\rm rad}=\operatorname{im}(\mathsf F|_{\rm free})+\operatorname{im}(\eta|_{\rm free})\)
를 자유 nuisance image로 두고 이를 소거하는 quotient projection \(P_\perp\)를 쓰면
\[
P_\perp\mathsf E j=P_\perp(d+\mathcal R-\text{bounded nuisance})\tag{19}
\]
만 남는다. Eq. (16)의 두 time jets가 자유면 \(\mathcal N_{\rm rad}=\mathbb R^8,\ P_\perp=0\).

Bound에 필요한 입력은 (i) target에 전달되는 \(\mathsf Fv-\eta-\mathcal R\)의 공동 제한, (ii) 자유방향을 자르는 독립 시간·광학 관측, 또는 (iii) Eq. (10)과 같은 nuisance 소거 target이다. 개별 jet norm을 모두 제한하는 것은 충분하지만 필수보다 강할 수 있다. 같은 복사식을 역산해 만든 jet를 다시 독립 관측으로 넣으면 순환이다.

Cold, small electron-relative-velocity Thomson의 \(\eta_1=\Gamma(\beta_{e|U}-t_1)\)는 속도값의 source 관계이지 \(\dot\beta_{U|n}\)의 독립 측정이 아니다. \(\tau\) 적분값만으로 점별 \(\Gamma>0\) 하한을 만들지 않는다.

## 6. 하나의 joint feasible set

데이터가 주어지면
\[
\Xi(d_{\rm obs})=\{\xi\in\mathcal D:
k=k_C+\mathsf Aj,\quad\text{Eq. (15)},\quad
\mathcal H(\xi)\in\mathcal Y(d_{\rm obs})\}.\tag{20}
\]
\(\mathcal D\)는 metric, tilt, time/source/remainder 및 matter 계약, \(\mathcal H\)는 관측 응답이다. \(\mathcal Y\)의 confidence coverage에는 별도 근거가 필요하다. 이번에는 실제 \(\mathcal Y\)를 입력하지 않았다.

고정 \(p,C,h\)에서 \(j=j_0+Ez,\|z\|\le1\)이면
\[
\mathcal K=k_C+\mathsf Aj_0+\mathsf AE\,\mathbb B,\quad
h_{\mathcal K}(w)=w\cdot(k_C+\mathsf Aj_0)+\|E^T\mathsf A^Tw\|.\tag{21}
\]
추가 복사·관측 제약은 실제 교집합/투영으로 반영한다. 불확실 geometry union도 일반적으로 ellipsoid가 아니다.

R3–R4의 동일 조건 reference body로 normalization/gauge를 구성한다. 구형 shear 예는
\(T_\sigma=\sigma/[3HB_\sigma]\)이며 양의 denominator와 동일 data/premise가 필요하다. MES domain으로 사전 clipping하지 않는다. Numerator와 denominator가 자료를 공유하면 같은 \(\Xi\)에서 극값을 구한다.

\[
Q_{\rm outer}=T\otimes T,\quad F_{\rm amp}=\|T\|^2,\quad
D=100(1-\sqrt{F_{\rm amp}}).\tag{22}
\]
\(D\)는 기준 경계 대비 여유이며 확률이나 FLRW 물질 성분비가 아니다. Signed \(T\)를 유지한다. \(Q\)만으로 global sign은 사라진다. Legacy signed \(x,Q_{\rm gauge},F_{\rm support},G_{\rm path}\)는 별개 정의로 보존한다.

## 7. 비가환 finite-tilt 공동 원판

이 절은 연산자·상관·reference를 확인하는 sensitivity fixture이며 실제 우주 모형 선택이나 관측 posterior가 아니다.
\[
[E_1,E_2]=\alpha E_2,\quad[E_1,E_3]=\alpha E_3,\quad[E_2,E_3]=0,
\quad\alpha\ne0,\quad p=(0,3/5,0),\ g=5/4.
\]
\(\alpha\) 단위는 길이\(^{-1}\). \(L_{21}=3c\alpha/5\)만 비영이고
\[
w_0=Sw_C=(0,0,-3c\alpha/10),\quad
q=\begin{pmatrix}
4H_*/5&-3c\alpha/10&0\\
-3c\alpha/10&5H_*/4&0\\
0&0&4H_*/5
\end{pmatrix}.\tag{23}
\]
\(\Omega_0\)의 axial vector를 \(w_0\)로 정하면 \(gW(q+L)W=H_*I+\Omega_0\).

\(a_*>0,\ x^2+z^2\le1\)에서
\[
a=a_*(x,0,z),\quad B=H_*I+\Omega_0+pa^T,\quad b=W(a-B^Tp)\tag{24}
\]
이면 모든 점이 동일 \(C,h,p,q\)의 exact geometric image다.
\[
b=\left(\frac{-9c\alpha+32a_*x}{50},-\frac{12H_*}{25},\frac{16a_*z}{25}\right),
\]
\[
\Theta=3H_*,\quad
\sigma=\frac{3a_*}{10}\begin{pmatrix}0&x&0\\x&0&z\\0&z&0\end{pmatrix},\quad
\omega=w_0+\frac{3a_*}{10}(z,0,-x).\tag{25}
\]
전단·와도·가속도의 독립 ball 세 개를 택하는 것과 다르다. 같은 \((x,z)\)가 모든 tensor를 결정한다. \(\Theta,\beta\)도 joint state에 남지만 여기서는 고정이다.

### 7.1 선언한 공통 reference와 set-valued output

Sensitivity reference를
\[
r_\sigma=\frac{3a_*}{5\sqrt2},\quad r_\omega=\frac{3a_*}{10},\quad r_a=a_*
\]
로 **선언**한다. 관측 MES radius가 아니며 와도는 비영 기준 \(w_0\)에 대한 displacement다.

Equal-block mean-square convention으로
\[
T=\frac1{\sqrt3}\left(\frac{\sigma}{r_\sigma},
\frac{\omega-w_0}{r_\omega},\frac a{r_a}\right)
=J\binom{x}{z},\quad J^TJ=I_2.\tag{26}
\]
Matrix block은 Frobenius, vector는 Euclidean 내적이다. Full 3×3 shear embedding의 off-diagonal multiplicity도 CAS에 반영했다.
\[
\begin{aligned}
\mathcal T&=\{Js:\|s\|\le1\},\\
Q(s)&=Jss^TJ^T,\quad F(s)=x^2+z^2,\\
D(s)&=100(1-\sqrt{x^2+z^2}),\quad
h_{\mathcal T}(w)=\|J^Tw\|,\quad D(\mathcal T)=[0,100].
\end{aligned}\tag{27}
\]
이는 선언한 domain/reference의 범위이며 “우리 우주의 0–100%” 추정이 아니다. 각 sector의 normalized squared norm도 \(x^2+z^2\)지만 이 fixture의 상관·reference 선택 때문이다. \(1/\sqrt3\)을 없애면 joint \(F=3(x^2+z^2)\). 같은 fraction은 같은 유의확률을 뜻하지 않는다.

### 7.2 확률과 두 상태 비교

확률법칙 없이 \(\mathcal T\)에서 \(\Pi\)를 만들지 않는다. **계산 예로 선언한 uniform area law on the unit disk** 아래 \(0\le q_0\le1\)에서는
\[
\Pi_{\rm tail}(q_0)=
\mathbb E\left[\frac QF\mathbf1(F>q_0)\right]
=\frac{1-q_0}{2}JJ^T,\quad\operatorname{tr}\Pi_{\rm tail}=1-q_0.\tag{28}
\]
\(F=0\)의 integrand는 0. \(q_0<0\)에서는 \(JJ^T/2\), \(q_0\ge1\)에서는 0이다. \(JJ^T\)는 rank 2 projector다. 이 법칙은 관측 posterior도 물리적 prior도 아니다.

같은 frame/reference의 \(s_A,s_B\)를 identity transport로 비교하고 \(s_B\ne0\)이면
\[
G_{AB}=\frac{(Js_A)\otimes(Js_B)}{\|s_B\|^2},\qquad
\|G_{AB}\|^2=\frac{\|s_A\|^2}{\|s_B\|^2}.\tag{29}
\]
다른 redshift에는 실제 transport/frame이 필요하다. \(s_B=0\)에서는 정의하지 않는다.

## 8. 문헌·근사영역 감사

원문 [Maartens, Gebbie & Ellis (1999), arXiv:astro-ph/9808163v2](https://arxiv.org/pdf/astro-ph/9808163v2)를 SciSpace 탐색 후 직접 확인했다. 루트도 원문을 열었다.

Eqs. (64)–(68)의 scattering은 electron/baryon 상대속도 전개를 포함하고, Eqs. (91)–(94)는 FLRW 선형화 식이다. Exact finite-tilt 기하 adapter와 결합한다고 arbitrary nonlinear radiation law가 되지 않는다.

Eq. (71)의 마지막 lower-multipole shear 부호는 PDF 화면에서도 음수다. Eq. (70)의 에너지 부분적분과 Eq. (89)의 isotropic shear 항은 양수를 요구한다. 이 국소 원문 불일치를 보존했으며 공식 erratum의 존재·원인은 확인하지 않았다. R5 채택 정리는 disputed coefficient에 의존하지 않는다.

Exact quadrupole coercivity, finite-boost higher-moment tail, finite electron-velocity source에 관한 추가 유도는 companion의 **미검증 탐색 후보**다. 이번 확정 결과나 검증된 closure로 인용하지 않는다.

## 9. 실제 검산·등록 순서·판정

검산 계획은 탐색 유도 뒤 작성했다. Kinematic 담당자의 첫 CAS는 그 파일 고정보다 먼저 완료되었다. 따라서 기하 CAS는 **선행 검산 증거**이며 preregistered discovery/confirmatory check라고 주장하지 않는다. Radiation/disk CAS는 등록 뒤 실행했다.

| 실제 Wolfram 검산 | 결과 |
|---|---|
| 비가환 class B, \(p=(0,3/5,0)\), symbolic \(q,b\) | 4D projection와 Eq. (3), 역산·compatibility·trace 일치 |
| \(p=(1/5,2/5,2/5)\) | 같은 항등식 참; 축 정렬에만 의존하지 않음 |
| \(p=0\) | \(B=q,a=b\); affine rank 9 |
| 세 fixture의 jet image | full rank 9, \(b\)-rank 3, left nullity 3; \(\omega\)의 \(b\)-rank 2,2,0 |
| 일반 \(p\) radiation block | Schur 및 determinant factorization 잔차 0 |
| \(p=(0,3/5,0)\) radiation block | rank 8; determinant \(1520528/1953125\); Schur 고유값 \(116/125,116/125,113/125\) |
| joint disk | \(q-q^T=0\), adapter와 와도 관계 잔차 0 |
| tensor normalization | \(J^TJ=I_2,\operatorname{rank}J=2,F=x^2+z^2\); 세 sector norm 동일 |
| probability fixture | radial tail \(1-q_0\), direction coefficient \((1-q_0)/2\) |

Radiation/disk 계산은 최초 정상 결과 후 **같은 code를 한 번 재실행하여 원시 응답을 파일에 보존**했다. 새로운 test나 독립 확인으로 이중 계산하지 않는다. 실제 Wolfram 실행에 근거하며 호스트 모델 신원/ultra 설정이나 모든 runtime 가용성을 인증하지 않는다.

기하 companion의 탐색 중간 설명에서 \(B^Tp\)의 Lorentz factor 하나가 누락된 것을 고쳤다. Boxed 결과와 CAS는 정확했고 최초 CAS 실패는 없었다. 등록 순서, 수정, 원문 부호 불일치를 revision ledger에 보존한다.

**독립 판정: PROMOTE_CONDITIONAL_THEORY.** 후보 생성에 참여하지 않은 reviewer가 frozen candidate, 일반 증명, 실제 CAS code/raw를 검토했다. Critical/major 문제는 없었고 minor 2건(동반 유도의 nonempty 가정, 등록 순서의 별도 machine-readable 기록)을 반영한 뒤 열린 지적 0건으로 종료했다. 채택 범위는 위 조건부 기하·retained radiation 식별성·공동 sensitivity 계산이다. 실관측 interval/percentage와 새 exact radiation/Thomson 후보는 HOLD다. 판정 원문은 INDEPENDENT_REVIEW.md에 있다.

## 10. 닫힌 작업과 다음 루프

이번에 닫힌 항목은 exact affine geometry, 자유 time-jet 방향, retained radiation time-jet rank, 동일 latent tensor/statistic output의 완결 fixture다.

다음 우선 연구는 두 branch 중 하나다.

1. **Exact radiation:** Target frame의 brightness/source로 exact dipole·quadrupole weak identities를 독립 유도해 R3 remainder를 대체한다. \(l=4\), source 편광·electron velocity, finite-boost tail을 검증한다. 한 사건의 constraint와 hierarchy evolution closure를 구별한다.
2. **관측:** Eq. (10)에 selected data response·frame·거리·covariance를 붙여 식별되는 nuisance quotient를 결정한다. R4 shell 잔차·source gate를 임의로 0으로 놓지 않는다.

현재 두 branch를 더 진행하지 않는다. 채택 연산자를 독립 판정하고 이 루프를 종료한다.

## 파일 안내

KINEMATIC_OPERATOR_DERIVATION.md에는 일반 유도·역산, verification/에는 실제 Wolfram code/raw, sources/에는 문헌 감사와 미채택 후보가 있다. PREREGISTRATION.json, REVISION_LOG.md, INDEPENDENT_REVIEW.md는 등록·수정·판정 기록이다. state/와 NEXT_PROMPT_KO.md는 재개 상태, inputs/는 실제 사용한 R4 기준 자료다. 원문 PDF·전체 추출 텍스트·렌더는 검토용이며 배포 ZIP에는 포함하지 않는다.
