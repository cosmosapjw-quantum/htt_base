# R3 restricted physical model: retained equation reference

Source: analytical R3 continuation, 2026-09-07. This extract preserves the equations needed by the R7 benchmark implementation. R7 THEORY/DESIGN determine its current role and assumptions; REUSE_MAP supersedes prior incomplete donor assessments. No scientific implementation, CAS, numerical or observational validation is claimed by this copy. Model: LRS Bianchi I, equal antipodal dust streams, initially isotropic Planck collisionless photons and Lambda; luminous test sources follow the positive stream. The observer boost is a separate endpoint input.

## 2. 규약과 source 정의

Signature는 \((-+++)\), cosmic proper time은 t, 공간좌표 \(x,y,z\)는 길이 단위, scale factors는 무차원이다.

\[
ds^2=-c^2dt^2+a_\perp^2(dx^2+dy^2)+a_\parallel^2dz^2,
\quad a_\perp=ae^{-b},\quad a_\parallel=ae^{2b}.
\tag{N1}
\]

\(H=\dot a/a,\ S=\dot b,\ H_\perp=H-S,\ H_\parallel=H+2S\)는 모두 s⁻¹이다. Normal unit vector는 \(n=c^{-1}\partial_t\); spatial orthonormal axes는 \(e_i=a_i^{-1}\partial_i\)다. Physical four-velocity는 \(cU\), \(U\cdot U=-1\)이다. 이 문서의 expansion/shear는 \(\nabla(cU)\) 또는 \(c\nabla n\)에서 정의한 proper-time rate다. \(\varepsilon,p,q\)의 단위는 energy density이며 실제 energy flux는 \(cq\)다.

\[
\sigma^{(n)}_{\hat i\hat j}=\operatorname{diag}(-S,-S,2S),
\quad \Theta_n=3H,\quad
\sigma_n^2\equiv\tfrac12\sigma^{(n)}_{ab}\sigma_{(n)}^{ab}=3S^2.
\tag{N2}
\]

두 dust stream을
\[
U_\pm=\gamma(n\pm\beta e_z),\quad
\beta=\tanh\chi,\quad \gamma=\cosh\chi
\]
로 쓴다. 여기서 \(\beta\)는 무차원 물리 속도이고 \(\chi\)는 rapidity다. 둘을 같은 변수 이름으로 사용하지 않는다.

### 2.1 Dust의 정확한 보존량

Spatial Killing vector \(\partial_z\)와 geodesic equation은
\[
\kappa=a_\parallel\sinh\chi
=a_\parallel\gamma\beta=\mathrm{constant}
\tag{N3}
\]
를 준다. 한 stream의 conserved comoving-coordinate number density를 N [m⁻³]이라 하면 number conservation은 \(a^3\gamma n_{\rm rest}=N\)이다. \(E_d=2mc^2N\)는 energy density 단위이고, 두 stream의 총 normal-frame source는
\[
\gamma=\sqrt{1+\kappa^2/a_\parallel^2},\qquad
\beta=\frac{\kappa}{\sqrt{a_\parallel^2+\kappa^2}},
\]
\[
\varepsilon_d=E_d\frac{\gamma}{a^3},\qquad
p_{\parallel d}=\varepsilon_d\beta^2,\qquad
p_{\perp d}=0,\qquad q_d=0.
\tag{N4}
\]

각 stream의 rest-frame energy density는 \(E_d/(2a^3\gamma)\)다. Flux는 각각 \(\pm\varepsilon_d\beta/2\)이므로 총합은 정확히 0이다. 압력은 속도의 제곱에 비례하므로 상쇄되지 않는다.

N3을 미분하면
\[
\dot\chi=-H_\parallel\tanh\chi,\qquad
\dot\beta=-H_\parallel\beta(1-\beta^2).
\tag{N5}
\]
따라서 FLRW limit의 \(d\chi/d\ln a\)는 \(-\tanh\chi\)다. Small tilt에서만 \(\beta\propto a^{-1}\)이다. \(-\sinh\chi\cosh\chi\)를 rapidity의 exact dust RHS로 쓰면 N3을 보존하지 못한다.

N4의 보존 검산은
\[
\dot\varepsilon_d
=-3H\varepsilon_d-H_\parallel p_{\parallel d},
\quad
\dot\varepsilon_d+
2H_\perp(\varepsilon_d+p_{\perp d})
+H_\parallel(\varepsilon_d+p_{\parallel d})=0.
\tag{N6}
\]
이다. 첫 식의 \(H_\parallel p_{\parallel d}\)를 빼면 tilted rest density와 normal density를 혼동한 것이다.

### 2.2 Collisionless radiation의 분포로 닫힌 stress

초기 \(a=a_i>0,\ b=0\)에서
\[
f_i(E_i)=\frac{1}{\exp(E_i/k_BT_i)-1},\qquad
\varepsilon_{\gamma i}
=\frac{\pi^2 k_B^4T_i^4}{15\hbar^3c^3}.
\]
두 polarization states를 포함한 값이다. 이후 collisionless Liouville equation은 보존된 covariant spatial momenta에서 \(f=f_i\)를 유지한다.

초기 momentum 방향의 cosine을 u, 평균을
\(\langle F\rangle=\frac12\int_{-1}^{1}F(u)\,du\)라 하고,
\[
A_\perp=\frac{a_i}{a_\perp},\quad
A_\parallel=\frac{a_i}{a_\parallel},\quad
r(u)=\sqrt{A_\perp^2(1-u^2)+A_\parallel^2u^2},\quad
J=(a_i/a)^3
\]
로 둔다. \(E=E_i r\), \(d^3p=Jd^3p_i\)이므로
\[
\varepsilon_\gamma=\varepsilon_{\gamma i}J\langle r\rangle,
\]
\[
p_{\parallel\gamma}=\varepsilon_{\gamma i}J
\left\langle\frac{A_\parallel^2u^2}{r}\right\rangle,\quad
p_{\perp\gamma}=\varepsilon_{\gamma i}J
\left\langle\frac{A_\perp^2(1-u^2)}{2r}\right\rangle.
\tag{N7}
\]

이는 angular distribution의 정확한 stress moments다. 유한 ℓ closure가 아니다. Radial momentum integral은 초기 Planck law로 이미 수행되었고, 남은 적분은 매 시점의 1차원 angular integral이다.

직접 확인할 항등식은
\[
2p_{\perp\gamma}+p_{\parallel\gamma}=\varepsilon_\gamma,\quad
q_\gamma=0,\quad p_{\perp\gamma},p_{\parallel\gamma}\ge0,
\]
\[
\dot\varepsilon_\gamma+
2H_\perp(\varepsilon_\gamma+p_{\perp\gamma})
+H_\parallel(\varepsilon_\gamma+p_{\parallel\gamma})=0.
\tag{N8}
\]
마지막 식은 \(\dot J=-3HJ\)와
\(\dot r=-[H_\perp A_\perp^2(1-u^2)+H_\parallel A_\parallel^2u^2]/r\)
를 N7에 넣어 얻는다. 반전 대칭과 축대칭은 \(q_\gamma=0\), off-diagonal stress=0을 보존한다.

## 3. Einstein evolution과 초기조건

\(\varepsilon=\varepsilon_d+\varepsilon_\gamma\),
\(p_\perp=p_{\perp d}+p_{\perp\gamma}\),
\(p_\parallel=p_{\parallel d}+p_{\parallel\gamma}\),
\(\bar p=(2p_\perp+p_\parallel)/3\)로 둔다. Λ는 이 ε에 넣지 않는다.

\[
H^2=\frac{8\pi G}{3c^2}\varepsilon+\frac{\Lambda c^2}{3}+S^2,
\qquad
\dot a=aH,\quad \dot b=S,
\]
\[
\dot S=-3HS+\frac{8\pi G}{3c^2}(p_\parallel-p_\perp).
\tag{N9}
\]

Expanding branch에서 H는 첫 식의 양의 제곱근이다. 보존식 N6/N8 및 N9는
\[
\dot H=-\frac{4\pi G}{c^2}(\varepsilon+\bar p)-3S^2
\tag{N10}
\]
를 준다. N10을 독립 Hamiltonian residual/propagation oracle로 사용한다. H를 별도로 적분해 constraint drift를 숨기는 방식은 primary가 아니다.

기하학과 source signs는 [Fleury–Pitrou–Uzan, v3 §II](https://arxiv.org/pdf/1410.8473)의 conformal-time 식을 proper time 및 energy-density units로 옮긴 결과와 일치한다. 그 논문에서 쓰는 shear norm과 본 N2의 scalar shear squared에는 factor 2 차이가 있다.

초기 입력은 \(a_i,b_i=0,\kappa,E_d,\varepsilon_{\gamma i},\Lambda,\zeta_i=S_i/H_i\)다. \(E_d,\varepsilon_{\gamma i}\ge0,\Lambda\ge0,|\zeta_i|<1\)을 primary 영역으로 정한다. H_i는
\[
H_i^2=
\frac{8\pi G\varepsilon_i/(3c^2)+\Lambda c^2/3}{1-\zeta_i^2},
\quad S_i=\zeta_iH_i
\tag{N11}
\]
로 정한다. \(\varepsilon_i\)는 N4/N7의 초기값이며 tilted dust의 \(\gamma_i\)를 포함한다.

a_i>0와 양의 scale factors 영역에서 N7의 integrands는 매끄럽고 r>0이다. 따라서 H>0인 열린 영역의 RHS는 locally Lipschitz이고 초기값 문제는 locally unique다. a=0 singularity, H=0 branch transition 또는 무한 시간까지의 정칙성을 이 국소 존재 진술로 보장하지 않는다.

### 3.1 선형 복사 feedback과 tilt의 차수

\(\bar\varepsilon_\gamma=\varepsilon_{\gamma i}(a_i/a)^4\)로 놓고 b를 전개하면
\[
\varepsilon_\gamma=\bar\varepsilon_\gamma+O(b^2),\quad
p_{\parallel\gamma}=\bar\varepsilon_\gamma(1/3-16b/15)+O(b^2),
\]
\[
p_{\perp\gamma}=\bar\varepsilon_\gamma(1/3+8b/15)+O(b^2).
\tag{N12}
\]
예컨대 \(r=(a_i/a)[1+b(1-3u^2)]+O(b^2)\),
\(\langle u^2\rangle=1/3,\langle u^4\rangle=1/5\)를 N7에 대입하면 나온다.

작은 κ와 \(\zeta_i=0\)에서 b=O(κ²)이며
\[
\ddot b+3H\dot b+
\frac{64\pi G}{15c^2}\bar\varepsilon_\gamma b
=\frac{8\pi G}{3c^2}\bar\varepsilon_d\frac{\kappa^2}{a^2}
+\text{고차항}.
\tag{N13}
\]
여기서 \(\bar\varepsilon_d=E_d/a^3\). 좌우 각 항은 s⁻²다. 복사 anisotropic stress는 이 차수에서 restoring term을 제공한다. 따라서 dust flux compensation은 geometry가 정확히 FLRW라는 뜻이 아니다. 초기 shear를 독립적으로 허용하면 \(b=O(\zeta_i)+O(\kappa^2)\)이고 이 둘을 같은 신호로 강제하지 않는다.

## 4. 정확한 온도장과 low-ℓ morphology

Normal observer가 시각 t에 보는 outward direction cosine을 \(\mu\)라 하면 각 방향은 계속 blackbody이고
\[
T_n(t,\mu)=\frac{T_i}{
\sqrt{(a_\perp/a_i)^2(1-\mu^2)+(a_\parallel/a_i)^2\mu^2}}
=\frac{T_i a_i}{a}
[e^{-2b}(1-\mu^2)+e^{4b}\mu^2]^{-1/2}.
\tag{N14}
\]

N14는 방향별 온도이며 방향을 평균한 spectrum이 하나의 blackbody라는 주장은 아니다. \(T_n(-\boldsymbol n)=T_n(\boldsymbol n)\)이므로 **normal-frame odd ℓ는 정확히 0**이다. b≠0이면 짝수 고다중극도 일반적으로 존재한다.

\(\bar T=T_i a_i/a\)에서
\[
T_n/\bar T=1-3b(\mu^2-1/3)+O(b^2),\quad
Q_{ab}=-3\bar T b\, e_{z\langle a}e_{zb\rangle}+O(b^2),
\quad O_{abc}=0.
\tag{N15}
\]
따라서 \(\|Q\|_F/\bar T=\sqrt6|b|+O(b^2)\). 이 진술은 현재 shear S가 아니라 \(b(t)-b_i=\int Sdt\)를 제약한다. 작은 endpoint b만으로 현재 |S|의 model-independent upper bound를 얻을 수 없다. 초기 shear와 sourced evolution의 상쇄도 허용된다.

관측자 \(U_o=\gamma_o(n+\boldsymbol\beta_o)\)는 별도다. 그 observer tetrad에서의 outward direction을 \(\boldsymbol n_o\), \(b_o=\boldsymbol\beta_o\cdot\boldsymbol n_o\)라 하면 cosmic outward direction과 thermal Doppler factor는
\[
\boldsymbol n_n=
\frac{\boldsymbol n_o+
[(\gamma_o-1)b_o/\beta_o^2-\gamma_o]\boldsymbol\beta_o}
{\gamma_o(1-b_o)},\quad
D_o=[\gamma_o(1-b_o)]^{-1},
\]
\[
T_o(\boldsymbol n_o)=D_o T_n(\boldsymbol n_n).
\tag{N16}
\]
β_o=0의 연속 극한은 identity다. Physical radiation transport는 N14에서 끝나며 N16의 observer transform을 Einstein source나 초기 photon collision에 다시 넣지 않는다.

True thermal variable에서 first-order local generator는
\(G_{\boldsymbol\beta}T=(\boldsymbol\beta\cdot\boldsymbol n)T-
[\boldsymbol\beta-(\boldsymbol\beta\cdot\boldsymbol n)\boldsymbol n]\cdot\nabla_{S^2}T\).
따라서 작은 b,β_o의 coherent octupole은
\[
O_{\rm obs}=B_Q\boldsymbol\beta_o+
O(\bar T|\beta_o|b^2+\bar T|\beta_o|^3),\quad
B_Qv=3\,{\rm STF}(v\otimes Q).
\tag{N17}
\]
Leading quadrupole-only response에서 Q≠0이고 leading O≠0이면 f_B=1이지만, 실제 Q_obs의 kinetic quadrupole, higher even multipoles, intensity variable 및 잡음이 이 등식을 바꾼다. Q=0 또는 O=0에서는 f_B가 정의되지 않는다. 따라서 관측 f_B≈1을 전역 tilt 발견으로 해석하지 않는다.

\(\zeta_i=0\)이면 coherent normal sky는 κ의 부호에 대해 even이고 κ=0에서 \(\partial_\kappa T_n=0\)이다. CMB-only mean response의 κ Fisher score가 그 점에서 0인 것은 implementation failure가 아니다. \(u=\kappa^2\ge0\)로 바꾸면 경계 parameter이고, axis도 u=0에서 정의되지 않는다. 표준 interior Wilks law를 자동 사용하지 않는다. Full stochastic covariance가 추가 parameter dependence를 갖는 경우에는 mean-score 진술과 구분해야 한다.

Collisionless unpolarized 초기장에서 polarization은 생성되지 않는다. 이 null limit은 Thomson scattering을 포함한 T/E/B 예측이 아니다. [Pontzen–Challinor §4–5](https://arxiv.org/pdf/0706.2075)의 scattering 및 type-dependent polarization과 분리한다.

## 5. Emitter와 observer를 포함한 광학

단위 timelike vector \(U_s,U_o\)를 쓰고, 과거 방향 affine tangent \(k=dx/d\lambda\)의 \(\lambda\)는 길이 단위로 정한다. 관측점에서
\[
k_o=-U_o+N_o,\quad U_o\cdot N_o=0,\quad N_o^2=1,
\quad E_o=U_o\cdot k_o=1.
\tag{N18}
\]
임의 emitter의 \(E_s=U_s\cdot k_s>0\)로부터
\[
1+z=E_s/E_o=E_s.
\tag{N19}
\]
Source는 + dust stream이다. k는 past-directed이므로 위 energy의 부호를 future-directed convention과 혼합하지 않는다.

Coordinate ODE는
\[
x'^\mu=k^\mu,\quad
k'^\mu=-\Gamma^\mu_{\alpha\beta}k^\alpha k^\beta,\quad
s_A'{}^\mu=-\Gamma^\mu_{\alpha\beta}k^\alpha s_A^\beta.
\]
초기 screen은 U_o,N_o에 수직인 orthonormal pair다. 평행 이동 screen은 null quotient를 표현한다. Emission에서
\(\tilde s_A=s_A-(U_s\cdot s_A)/(U_s\cdot k)\,k\)
로 옮기면 source-rest screen에 놓이며 inner products와 transverse area는 같다.

좌표 \(x^0=ct\)에서 필요한 Christoffel은
\[
\Gamma^0_{ii}=a_i^2H_i/c,\quad
\Gamma^i_{0i}=\Gamma^i_{i0}=H_i/c
\quad(\text{각 i, no sum})
\tag{N20}
\]
이며 나머지는 0이다. Riemann convention은
\(R^\rho{}_{\sigma\mu\nu}=\partial_\mu\Gamma^\rho_{\nu\sigma}
-\partial_\nu\Gamma^\rho_{\mu\sigma}
+\Gamma^\rho_{\mu\alpha}\Gamma^\alpha_{\nu\sigma}
-\Gamma^\rho_{\nu\alpha}\Gamma^\alpha_{\mu\sigma}\).
Orthonormal components는
\[
R_{\hat0\hat i\hat0\hat i}=-(\dot H_i+H_i^2)/c^2,\quad
R_{\hat i\hat j\hat i\hat j}=H_iH_j/c^2\ (i\ne j),
\tag{N21}
\]
및 Riemann symmetries로 완결된다.

Jacobi matrix는
\[
{\cal D}''_{AB}={\cal T}_{AC}{\cal D}_{CB},\quad
{\cal T}_{AB}=-R_{\mu\nu\rho\sigma}
s_A^\mu k^\nu s_B^\rho k^\sigma,
\quad {\cal D}(0)=0,\quad {\cal D}'(0)=I_2.
\tag{N22}
\]
Riemann contraction 전 coordinate 또는 orthonormal basis를 통일한다. Flat-space limit은 \({\cal D}=\lambda I\). FLRW transverse tidal term은 \(\dot H E_n^2/c^2\)로 Ricci focusing의 부호를 확인한다. 관측자에서 과거 방향으로 증가하는 λ를 썼기 때문에 future-affine 초기 미분의 음의 부호를 복사하지 않는다.

투명 전파와 reciprocity 아래
\[
D_A=\sqrt{|\det{\cal D}|},\quad D_L=(1+z)^2D_A,\quad
\mu=5\log_{10}(D_L/{\rm Mpc})+25.
\tag{N23}
\]
Primary domain은 관측점과 첫 conjugate point 사이다. Caustic 뒤 multiple images의 catalogue counting을 이 식 하나로 처리하지 않는다. Photon Killing quantities \(a_i^2k^i\), null norm, screen Gram 및 Wronskian \({\cal D}'{}^T{\cal D}-{\cal D}^T{\cal D}'=0\)는 별도 oracle다. 이 광학 구조는 [Fleury–Pitrou–Uzan §III–IV](https://arxiv.org/pdf/1410.8473)와 대조했다.

## 6. 깊이가 local/global degeneracy를 깨는 정확한 조건

이 절은 N1–N23의 FLRW, small-velocity, raw bolometric limit이다. \(\chi_r(z)=c\int_0^z dz'/H(z')\)는 comoving radial distance이며 rapidity χ와 다른 기호다. \(\boldsymbol K=\kappa\boldsymbol e_z\), \(a(t_o)=1\)인 FLRW gauge에서 source velocity는
\(\boldsymbol\beta_s(z)=(1+z)\boldsymbol K+O(\kappa^3)\)다.

R2의 fixed-observed-z law를 쓰면
\[
\delta\mu(z,\boldsymbol n)=\frac5{\ln10}
\boldsymbol n\cdot[f_o(z)\boldsymbol\beta_o+
f_g(z)\boldsymbol K]+O(v^2/c^2),
\]
\[
{\cal A}(z)=\frac{(1+z)c}{H(z)\chi_r(z)},\quad
f_o={\cal A},\quad f_g=(1+z)(1-{\cal A}).
\tag{N24}
\]
Low-z Taylor에는 velocity-induced redshift shift가 z보다 충분히 작아야 한다. 유한 속도의 실제 benchmark 계산은 N19/N23을 사용한다.

두 response의 비는
\[
r_f(z)=\frac{f_g}{f_o}
=\frac{H(z)\chi_r(z)}c-(1+z),\qquad
r_f'(z)=\frac{H'(z)\chi_r(z)}c.
\tag{N25}
\]
증명은 \(\chi_r'=c/H\)를 미분식에 넣으면 된다. H'>0이면 z>0에서 r_f가 엄격히 증가하므로 서로 다른 두 깊이는 이 이상적인 scalar response에서 선형 독립성을 제공한다. 그러나 실제 angular coverage와 nuisance projection까지 포함한 전체 rank는 따로 검사해야 한다.

\(q_0=-\ddot a a/\dot a^2|_o\), \(H(z)=H_0[1+(1+q_0)z+O(z^2)]\)이면
\[
r_f(z)=-1+\frac{1+q_0}{2}z^2+O(z^3).
\tag{N26}
\]
즉 **response ratio의 퇴화는 저 z에서 quadratic order에야 깨진다.** Bin 수를 늘리는 것과 충분한 물리적 분리능을 얻는 것은 다르다. 같은 amplitude의 \(\boldsymbol\beta_o=\boldsymbol K\) 조합에서는
\[
f_o+f_g=\tfrac12(1+q_0)z+O(z^2)
\]
이므로 leading \(1/z\) 속도 dipole이 상쇄된다.

하나의 고정 spatial component, independent Gaussian weights \(w_i>0\)에서
\[
F=\sum_i w_i
\begin{pmatrix}f_{o,i}^2&f_{o,i}f_{g,i}\\f_{o,i}f_{g,i}&f_{g,i}^2\end{pmatrix}.
\]
\(W=\sum_iw_if_{o,i}^2,\ p_i=w_if_{o,i}^2/W\)라 쓰면
\[
\det F=W^2\,{\rm Var}_{p}(r_f).
\tag{N27}
\]
이는 Cauchy–Schwarz equality condition의 직접 표현이다. 같은 깊이만 있으면 determinant는 0이다. H=constant인 de Sitter test-tracer limit에서는 모든 z에서 \(r_f=-1\), 깊이만으로는 분리할 수 없다. 이 limit은 nonzero self-gravitating dust가 있는 exact de Sitter 해라는 주장이 아니다.

Known covariance와 calibration/selection nuisance를 포함하면 R2의 projected design \(D=\Pi C^{-1/2}A\)로 판단한다. N27의 diagonal-weight determinant를 실제 CF4 정보 행렬로 대체하지 않는다. 자유로운 depth-dependent dipole nuisance가 N24 전체 span을 포함하면 이 물리 profile도 식별되지 않는다.

## 7. Kinematical quantities를 같은 모형에서 계산

Dust geodesic congruence의 covector는
\(U_\pm^\flat=-\gamma c\,dt\pm\kappa dz\)다. Exterior derivative가 0이므로 acceleration과 vorticity는 모두 0이다. 이는 해당 counterstreaming geodesic flow의 결과이며 모든 tilted cosmology의 결과가 아니다.

Dust-rest expansion eigenvalues는
\[
h_\perp^{(d)}=\gamma H_\perp,\quad
h_\parallel^{(d)}=H_\parallel/\gamma,
\]
\[
\Theta_d=2\gamma H_\perp+H_\parallel/\gamma
=\gamma(3H-H_\parallel\beta^2).
\tag{N28}
\]
\(\Delta_d=h_\parallel^{(d)}-h_\perp^{(d)}\)라 하면 rest-frame shear는
\(\operatorname{diag}(-\Delta_d/3,-\Delta_d/3,2\Delta_d/3)\).
따라서
\[
\frac{\|\sigma_n\|_F}{|\Theta_n|}
=\frac{\sqrt6|S|}{3|H|},\qquad
\frac{\|\sigma_d\|_F}{|\Theta_d|}
=\frac{\sqrt{2/3}|\Delta_d|}{|\Theta_d|}.
\tag{N29}
\]
분모 0은 UNDEFINED다. 표준 scalar shear를 쓰면 각 numerator를 √2로 나눈다. N28은 \(\nabla(cU)\)를 \(e_x,e_y,\gamma(\beta n+e_z)\)의 dust-rest triad로 투영하여 얻는다.

Local observer의 한 점 속도만으로 observer congruence의 \(\Theta,\sigma,\omega\)를 정의할 수는 없다. 공간·시간으로 연장한 velocity field가 필요하다. N29의 두 frame을 임의의 local observer kinematics와 혼동하지 않는다. 본 모형의 \(\omega=0\)은 vorticity anomaly의 설명 모형으로는 음의 결과다.

## 8. 관측 연결의 정확한 범위

CMB instrument map은 N14→N16 뒤에 spectral conversion, beam/bandpass, component combination, mask/fit을 순서대로 적용한다. 본 모형은 제거되기 전 full positive source sky를 제공하므로 R2-A의 hidden-lift ambiguity를 **이 모형의 전제 아래** 닫는다. 이것이 실제 cosmic source law가 확인되었다는 뜻은 아니다.

선택하는 counterfactual은 frozen release operator다. 실제 weights를 다시 fit하는 실험은 별도 response다. 임의 channel response \(r_c(\nu)\)에 대한 exact thermodynamic-linearized map은
\[
K_c(\boldsymbol n_o)=
\frac{\int d\nu\,r_c(\nu)[B_\nu(T_o(\boldsymbol n_o))-B_\nu(T_{\rm cal})]}
{\int d\nu\,r_c(\nu)\partial_T B_\nu(T_{\rm cal})}.
\tag{N30}
\]
Calibration temperature \(T_{\rm cal}\)은 native mean temperature와 별도 입력이다. Frozen combined map은 \(m=P[\sum_cW_cK_c-c_{\rm rel}]\). β_o와 κ의 derivative는 이 전체 map의 derivative이며 exact Planck function을 쓰면 β²T0와 βΔT 등을 별도로 누락하지 않는다.

실제 PR3 \(r_c,W_c,c_{\rm rel}\)의 완전한 bytes/상태는 이번에 확보하지 않았다. 공식 [PR3 문서](https://irsa.ipac.caltech.edu/data/Planck/release_3/docs/)와 overview를 읽은 것으로 수치 response가 승인되는 것은 아니다. 실제 β 추론은 RELEASE_RESPONSE_UNRESOLVED를 유지한다. Exact N30 자체는 이론적으로 명시되었으며 Taylor truncation으로 더 강한 유효범위를 주장할 이유가 없다.

거리 표본의 selected latent likelihood는 동반 문서 SELECTED_OBSERVATION_MODEL_R3_KO.md에 고정한다. 실제 CF4의 병합 DM을 raw flux likelihood로 자동 인정하지 않는다. 이번 결과와 문헌 원문·코드 재사용 한계·후속 검증은 LOCAL_CODEX_R3_CONTRACT_KO.md로 연결한다.


---

