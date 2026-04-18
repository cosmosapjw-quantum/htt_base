# Low-ℓ 전용 tetrad-based Bianchi CMB solver 설계 문서

## 0. 목적과 범위

이 문서는 low-ℓ 전용 CMB solver를 **tetrad 기반 orthogonal/tilted Bianchi background + 선형 fluctuation** 위에서 구성하기 위해, 이번 세션에서 유도·정리한 식들을 한데 모은 self-contained reference note다. 목표는 다음 세 가지다.

1. exact Bianchi background transport를 중심으로 low-ℓ TT/TE를 계산할 수 있는 최소 수식계를 정리한다.
2. orthogonal/tilted Bianchi에서 species별 background equation, perturbation equation, initial condition(IC)을 일관되게 정리한다.
3. 최종적으로 direction-dependent likelihood 생성까지 가는 forward model의 수학적 구조를 명시한다.

이 문서의 원칙은 다음과 같다.

- background는 가능한 한 **nonperturbative**하게 다룬다.
- fluctuation은 **linear perturbation**으로 다룬다.
- recombination/reionization microphysics는 first pass에서 **isotropic scalar history**를 유지한다.
- 그러나 source evaluation, visibility weighting, transport, collision, LoS는 **anisotropic / frame-aware**하게 처리한다.
- Thomson kernel은 classical limit에서 **linear**로 두되, tilt와 shear 때문에 moment equation은 **비선형 coupling**을 가질 수 있음을 분명히 한다.

이 문서는 low-ℓ 전용 solver를 기준으로 쓰여 있으므로, high-ℓ production solver 전체를 닫는 full Einstein–Boltzmann hierarchy를 제공하지는 않는다. 대신 high-ℓ로 확장할 때도 유지되는 IC prescription과 frame rule은 명시한다.

---

## 1. 기본 컨벤션과 아키텍처

### 1.1 시공간 분해와 부호

metric signature는

\[
(-,+,+,+)
\]

로 두고, 기본 관측자 congruence를 \(n^a\)라 하여

\[
g_{ab}=-n_a n_b+h_{ab},\qquad h_{ab}n^b=0
\]

로 \(1+3\) 분해한다.

운동학 분해는

\[
\nabla_a n_b=-n_aA_b+\frac13\Theta h_{ab}+\sigma_{ab}+\omega_{ab}
\]

이다. 여기서 \(A_a\)는 acceleration, \(\Theta\)는 expansion, \(\sigma_{ab}\)는 shear, \(\omega_{ab}\)는 vorticity다.

### 1.2 기본 프레임 선택

이 문서 전체의 기본 선택은 다음과 같다.

\[
\boxed{\text{transport는 }n^a\text{-frame},\qquad \text{collision/source/visibility는 }u_e^a\text{-frame}}
\]

즉,

- exact Bianchi geodesic, redshift, angular advection, polarization-basis transport는 **normal frame** \(n^a\) 기준으로 쓴다.
- Thomson scattering, optical depth, visibility, quadrupole source tensor는 **electron rest frame** \(u_e^a\) 기준으로 쓴다.

이 선택은 orthogonal/tilted Bianchi를 하나의 프레임워크 안에 가장 안정적으로 묶는다.

### 1.3 low-ℓ solver의 최소 상태벡터

low-ℓ production baseline에서는 photon/polarization sector를

\[
\{\Theta_0,\Theta_1,\Theta_2,E_2\}
\]

로 두고, 필요하면

\[
\{\Theta_3,E_3\}
\]

를 보조로 추가한다. cutoff는

\[
L=4 \quad \text{(최소 self-consistent)},\qquad
L=6 \quad \text{(실전 baseline)},\qquad
L=8 \quad \text{(수렴 검증)}
\]

으로 둔다.

---

## 2. tetrad 기반 exact Bianchi background

### 2.1 background 변수

background는 보통

\[
\alpha(\eta),\qquad \beta_{ab}(\eta),\qquad \Sigma_{ab}(\eta)=e^{\alpha}\sigma_{ab},\qquad {}^{(3)}R_{ab}(\eta)
\]

로 나타낸다. 여기서

- \(\alpha\): isotropic expansion
- \(\beta_{ab}\): anisotropic shape deformation
- \(\Sigma_{ab}\): conformal shear
- \({}^{(3)}R_{ab}\): anisotropic 3-curvature

이다.

실전 코드에선 background state를 대략

\[
\{\alpha,\beta_{ab},\Sigma_{ab},{}^{(3)}R_{ab},C^i{}_{jk}\}
\]

로 두는 게 좋다. \(C^i{}_{jk}\)는 Bianchi type을 정하는 structure constants다.

### 2.2 background Einstein–Bianchi 진화

구체적 Bianchi type(I, V, VII\(_h\), IX 등)에 따라 background ODE는 달라지지만, 구조적으로는

\[
\{\alpha,\beta_{ab},\Sigma_{ab},{}^{(3)}R_{ab}\}' = \mathcal F_{\rm Bianchi}[\alpha,\beta,\Sigma,{}^{(3)}R;C^i{}_{jk},T_{ab}^{\rm tot}]
\]

와 같은 닫힌 계를 형성한다.

이 문서에서 중요한 건 배경이 **정확한 Bianchi tetrad evolution**을 따른다는 점이며, fluctuation source를 억지로 배경에 섞지 않는다는 점이다.

---

## 3. species별 background equation

최소 species 집합은

- CDM \(c\)
- baryon/electron fluid \(b,e\)
- photons \(\gamma\)
- massless neutrinos \(\nu\)

이다.

### 3.1 matter species: orthogonal case

orthogonal Bianchi에서는 background matter flow가 normal congruence와 정렬되므로

\[
u_{(s)}^a = n^a
\]

이다. 따라서 background momentum density와 anisotropic stress는

\[
q_a^{(s)}=0,\qquad \pi_{ab}^{(s)}=0
\]

가 된다.

배경 continuity는 표준형

\[
\dot\rho_s+\Theta(\rho_s+p_s)=0
\]

이다.

pressureless CDM이면

\[
p_c=0,\qquad \dot\rho_c+\Theta\rho_c=0.
\]

baryon/electron fluid도 first pass에서는 dust-like로 두면

\[
p_b\simeq 0,\qquad \dot\rho_b+\Theta\rho_b=0.
\]

### 3.2 matter species: tilted case

tilted background에서는 species별 4-속도를

\[
u_{(s)}^a=\gamma_s(n^a+v_{(s)}^a),\qquad \gamma_s=(1-v_s^2)^{-1/2}
\]

로 둔다.

species rest frame에서 perfect fluid면

\[
T^{(s)}_{ab}=(\hat\rho_s+\hat p_s)u^{(s)}_a u^{(s)}_b+\hat p_s g_{ab}.
\]

이를 normal frame으로 분해하면

\[
T^{(s)}_{ab}=\mu_s n_a n_b+2n_{(a}q^{(s)}_{b)}+p_s h_{ab}+\pi^{(s)}_{ab}
\]

이며, 계수는

\[
\mu_s=\gamma_s^2(\hat\rho_s+\hat p_s)-\hat p_s,
\]
\[
q_a^{(s)}=\gamma_s^2(\hat\rho_s+\hat p_s)v_a^{(s)},
\]
\[
p_s=\hat p_s+\frac13\gamma_s^2(\hat\rho_s+\hat p_s)v_s^2,
\]
\[
\pi_{ab}^{(s)}=\gamma_s^2(\hat\rho_s+\hat p_s)v_{\langle a}^{(s)}v_{b\rangle}^{(s)}.
\]

small tilt이면

\[
q_a^{(s)}\simeq (\hat\rho_s+\hat p_s)v_a^{(s)},\qquad \pi_{ab}^{(s)}=O(v_s^2).
\]

즉 tilted background에서 matter sector의 핵심 추가 변수는 \(v_{(s)}^a\)와 그로부터 생기는 \(q_a^{(s)}\)다.

또 Bianchi에선 total momentum density가 배경 shear/structure constants와 연결되므로

\[
8\pi P_i^{\rm (tot)}
=
e^{-\alpha}\left(\sigma_{jk}C^j{}_{ki}-\sigma_{ij}C^k{}_{kj}\right)
\]

을 만족하도록 species tilts를 골라야 한다.

### 3.3 photons: exact background transport

광자 4-운동량은

\[
K^a=E(n^a+p^a),\qquad p^a p_a=1,\qquad p^a n_a=0.
\]

comoving energy를

\[
\epsilon\equiv Ee^\alpha
\]

로 두면 exact Bianchi redshift는

\[
\epsilon'=-\epsilon\,e^\alpha p^ip^j\sigma_{ij}=-\epsilon\,\Sigma_{ij}p^ip^j.
\]

즉 background shear가 photon energy를 직접 direction-dependent하게 바꾼다.

ray direction \((\theta,\phi)\)와 polarization basis angle \(\psi\)도 background geometry에 의해 진화한다. 따라서 exact Stokes PDE는

\[
\left[\partial_\eta+\theta'\partial_\theta+\phi'\partial_\phi-\Sigma_{ij}p^ip^j\partial_{\ln E}\right]I(E,\theta,\phi,\eta)=\mathcal C_I,
\]
\[
\left[\partial_\eta+\theta'\partial_\theta+\phi'\partial_\phi-\Sigma_{ij}p^ip^j\partial_{\ln E}\right](Q\pm iU)
\pm 2i\psi'(Q\pm iU)=\mathcal C_\pm.
\]

이것이 Tier A의 exact angular transport equation이다.

### 3.4 neutrinos: collisionless background transport

massless neutrinos는 collisionless radiation이므로, exact angular PDE는

\[
\mathcal L_B[f_\nu]=0
\]

형태다. isotropic limit에선 배경 continuity가

\[
\dot\rho_\nu+\frac43\Theta\rho_\nu=0
\]

로 내려간다.

---

## 4. exact Thomson collision tensor

classical Thomson limit에서 collision은 electron frame에서 가장 단순하다. intensity와 polarization tensor에 대한 exact source는 schematically

\[
\tilde{\mathcal C}_I(E,\tilde e)
=-\tilde n_e\sigma_T I(E,\tilde e)
+\frac{\tilde n_e\sigma_T}{4\pi}
\left[\tilde I(E)+\tilde\zeta_{ab}(E)\tilde e^a\tilde e^b\right],
\]

\[
\tilde{\mathcal C}_{ab}(E,\tilde e)
=-\tilde n_e\sigma_T P_{ab}(E,\tilde e)
+\frac{\tilde n_e\sigma_T}{4\pi}
\left[\tilde H_a{}^{c_1}\tilde H_b{}^{c_2}\tilde\zeta_{c_1c_2}(E)\right]^{TT},
\]

\[
\tilde\zeta_{ab}(E)=\frac34\tilde I_{ab}(E)+\frac92\tilde E_{ab}(E).
\]

핵심은 다음 두 줄이다.

\[
\boxed{\text{Thomson kernel 자체는 classical limit에서 선형이다.}}
\]
\[
\boxed{\text{하지만 tilt와 shear 때문에 projected moment equations는 비선형 coupling을 가질 수 있다.}}
\]

즉 필요한 것은 “nonlinear Thomson kernel”이 아니라 **exact Bianchi transport + exact electron-frame Thomson tensor**다.

---

## 5. radiation 변수: \(\Theta,E,B\)와 \(I,Q,U\)

온도 섭동은 분포함수 수준에서

\[
f(K;\eta)=\bar f(\epsilon)\left(1-\frac{d\ln\bar f}{d\ln\epsilon}\Theta\right)
\]

로 정의하고, 편광은

\[
(q\pm iu)(K;\eta)= -\frac{d\bar f}{d\ln\epsilon}(Q\pm iU)
\]

로 정의한다.

PSTF 표현은

\[
\Theta(x,e,\eta)=\sum_{\ell\ge0}\Theta_{A_\ell}(x,\eta)e^{A_\ell},
\]
\[
E_{A_\ell}(x,\eta),\qquad B_{A_\ell}(x,\eta).
\]

수치 구현용 harmonic 표현은

\[
\Theta(\hat n)=\sum_{\ell m}\Theta_{\ell m}Y_{\ell m}(\hat n),
\]
\[
Q\pm iU = \sum_{\ell m}(E_{\ell m}\pm iB_{\ell m})\,{}_{\pm2}Y_{\ell m}(\hat n).
\]

exact Bianchi에서는 parity breaking과 basis rotation 때문에 generically \(TB,EB\)도 생길 수 있다.

---

## 6. exact multipole hierarchy와 low-ℓ cutoff의 의미

에너지 적분된 brightness multipoles \(\Pi_{A_\ell}\)에 대해 exact \(1+3\) covariant hierarchy는

\[
\dot\Pi_{\langle A_\ell\rangle}
+\frac43\Theta \Pi_{A_\ell}
+\tilde\nabla_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle}
+\frac{\ell+1}{2\ell+3}\tilde\nabla^b\Pi_{A_\ell b}
\]
\[
-\frac{(\ell+1)(\ell-2)}{2\ell+3}A^b\Pi_{A_\ell b}
+(\ell+3)A_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle}
+\ell\omega^b\eta_{bc\langle a_\ell}\Pi_{A_{\ell-1}\rangle}{}^c
\]
\[
-\frac{(\ell-1)(\ell+1)(\ell+2)}{(2\ell+3)(2\ell+5)}\sigma^{bc}\Pi_{A_\ell bc}
+\frac{5\ell}{2\ell+3}\sigma^b{}_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle b}
-(\ell+2)\sigma_{\langle a_\ell a_{\ell-1}}\Pi_{A_{\ell-2}\rangle}
=K_{A_\ell}.
\]

orthogonal Bianchi에서는 보통 \(A_a=\omega_a=0\)로 두므로

\[
\dot\Pi_{\langle A_\ell\rangle}
+\frac43\Theta \Pi_{A_\ell}
+\tilde\nabla_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle}
+\frac{\ell+1}{2\ell+3}\tilde\nabla^b\Pi_{A_\ell b}
\]
\[
-\frac{(\ell-1)(\ell+1)(\ell+2)}{(2\ell+3)(2\ell+5)}\sigma^{bc}\Pi_{A_\ell bc}
+\frac{5\ell}{2\ell+3}\sigma^b{}_{\langle a_\ell}\Pi_{A_{\ell-1}\rangle b}
-(\ell+2)\sigma_{\langle a_\ell a_{\ell-1}}\Pi_{A_{\ell-2}\rangle}
=K_{A_\ell}.
\]

\(\ell=2\)에서 보면

\[
\dot\Pi_{\langle ab\rangle}
+\frac43\Theta \Pi_{ab}
+\tilde\nabla_{\langle a}\Pi_{b\rangle}
+\frac37\tilde\nabla^c\Pi_{abc}
-\frac{4}{21}\sigma^{cd}\Pi_{abcd}
+\frac{10}{7}\sigma^c{}_{\langle a}\Pi_{b\rangle c}
-4\sigma_{ab}\Pi
=K_{ab}.
\]

즉

\[
-4\sigma_{ab}\Pi
\]

가 monopole \(\to\) quadrupole shear injection이고, 동시에 \(\Pi_{abcd}\)가 들어간다. 이 때문에

\[
L=2
\]

는 self-consistent closure가 아니다. low-ℓ에서

\[
L=4\quad\text{(최소)},\qquad L=6\quad\text{(권장)},\qquad L=8\quad\text{(검증)}
\]

이라는 결론이 나온다.

---

## 7. low-ℓ Tier B 상태벡터와 LoS 형식

low-ℓ projected solver는 상태벡터를

\[
\mathbf X(\eta)=\{\Theta_{\ell m},E_{\ell m},B_{\ell m}\}_{\ell\le L}
\]

로 잡는다. 그러면 진화는 구조적으로

\[
\mathbf X' = \mathsf L_B[n]\,\mathbf X + \mathsf C_T[v_e]\,\mathbf X + \mathbf S_{\rm pert}[v_e]
\]

이다.

- \(\mathsf L_B[n]\): exact Bianchi background transport (redshift, advection, polarization rotation)
- \(\mathsf C_T[v_e]\): electron-frame Thomson block
- \(\mathbf S_{\rm pert}[v_e]\): boosted quadrupole / Doppler / visibility source

formal LoS 해는

\[
\mathbf X(\eta_0)
=
\mathcal P\exp\!\left[\int_{\eta_*}^{\eta_0}d\eta\,(\mathsf L_B+\mathsf C_T)\right]\mathbf X(\eta_*)
+\int_{\eta_*}^{\eta_0}d\eta\,
\mathcal P\exp\!\left[\int_{\eta}^{\eta_0}d\eta'\,(\mathsf L_B+\mathsf C_T)\right]\mathbf S_{\rm pert}(\eta).
\]

즉 FLRW의 단일 \(j_\ell\) kernel 대신 **background-dependent matrix propagator**를 쓴다.

---

## 8. low-ℓ source sector: SW/ISW와 redshift source

low-ℓ TT/TE의 원초적 source는 exact Bianchi background 위의 redshift operator로 쓰는 게 자연스럽다.

generic spacetime에서 광자 에너지 변화는

\[
\frac{dE}{dv}
=-\left[\frac13\Theta + A_a e^a + \sigma_{ab}e^a e^b\right]E^2.
\]

배경과 섭동을 분리하면

\[
\Theta=\Theta^{(B)}+\delta\Theta,
\qquad
A_a=A_a^{(B)}+\delta A_a,
\qquad
\sigma_{ab}=\sigma_{ab}^{(B)}+\delta\sigma_{ab}.
\]

보통 background에서는 \(A_a^{(B)}=0\)로 둘 수 있으므로, fluctuation redshift source는

\[
\frac{d}{d\eta}\delta\ln\epsilon
=-\left[
\frac13\delta\Theta+
\delta A_a p^a+
\delta\sigma_{ab}p^ap^b
\right]_{\rm along\ exact\ Bianchi\ ray}.
\]

즉 low-ℓ SW/ISW source의 최소 공변 변수는

\[
\delta\Theta,\qquad \delta A_a,\qquad \delta\sigma_{ab}
\]

이다.

---

## 9. species별 perturbation equation

이 문서에서는 gauge-specific long form보다 low-ℓ tetrad solver에 직접 쓰기 좋은 **공변 구조**를 우선 적는다.

### 9.1 matter species (CDM, baryon/electron fluid)

최소 perturbation 변수는

\[
\Delta_s,\qquad q_s,\qquad v_s
\]

다.

구조적으로 continuity는

\[
\dot\Delta_s + (1+w_s)Z + \tilde\nabla^a v_a^{(s)} + \cdots =0
\]

형태이고, momentum/Euler는

\[
\dot q_a^{(s)}+\frac43\Theta q_a^{(s)}+\tilde\nabla_a p_s+\cdots = \text{forces/couplings}
\]

형태다.

baryon/electron fluid는 photon Thomson drag와 직접 결합되므로 \(v_b\)와 photon dipole/TCA가 함께 들어간다.

tilted background에서는

\[
u_{(s)}^a=\bar\gamma_s(n^a+\bar v_{(s)}^a)+\delta u_{(s)}^a
\]

로 두고, perturbation equations에는 \(\bar v_s\)-boost correction이 붙는다.

### 9.2 photons

photon sector이 low-ℓ solver의 핵심이다.

collision/source-free transport skeleton은 위의

\[
\mathbf X' = \mathsf L_B\mathbf X + \mathsf C_T\mathbf X + \mathbf S_{\rm pert}
\]

이고, Thomson polarization source tensor는

\[
\zeta_{ab}=\frac34 I_{ab}+\frac92 E_{ab}
\]

이며, harmonic normalization에선

\[
\Pi^m=\Theta_2^m-\sqrt6\,E_2^m
\]

를 쓰면 편하다.

collision term은

\[
\left.\frac{D\Theta_\ell^m}{D\eta}\right|_{\rm coll}
=
\Gamma_T\left[
-\Theta_\ell^m(1-\delta_{\ell0})
+\frac{1}{10}\delta_{\ell2}(\Theta_2^m-\sqrt6 E_2^m)
+\delta_{\ell1}\tilde u^m
\right],
\]

\[
\left.\frac{D(E_\ell^m\pm iB_\ell^m)}{D\eta}\right|_{\rm coll}
=
\Gamma_T\left[
-(E_\ell^m\pm iB_\ell^m)
+\frac35\delta_{\ell2}\left(E_2^m-\frac{1}{\sqrt6}\Theta_2^m\right)
\right],
\]

\[
\Gamma_T\equiv a n_e x_e\sigma_T>0.
\]

즉 photons는 최소한

\[
\Theta_0,\Theta_1,\Theta_2,E_2
\]

를 explicit하게 들고 있어야 한다.

### 9.3 neutrinos

collisionless low-ℓ neutrino solver의 최소 retained set은

\[
\Delta_\nu,\qquad q_\nu,\qquad \pi_\nu,\qquad G_3
\]

다. 즉 density contrast, heat flux, anisotropic stress, next moment까지는 seed와 startup에 직접 필요하다.

---

## 10. Quadrupole-aware TCA

low-ℓ solver의 최소 TCA는 baryon-photon slip만 닫는 게 아니라 **\((\Theta_2,E_2)\) subsystem**을 같이 닫는 것이다.

non-collision source를

\[
S_{2,T}^m 
= (\Theta_2^m)'_{\rm advec} + (\Theta_2^m)'_{\rm shear} + S_{2,\rm pert}^m,
\]
\[
S_{2,E}^m 
= (E_2^m)'_{\rm advec} + S_{E,\rm pert}^m
\]

로 두면, tight coupling에서

\[
0 \approx S_{2,T}^m + \Gamma_T\left(-\frac{9}{10}\Theta_2^m-\frac{\sqrt6}{10}E_2^m\right),
\]
\[
0 \approx S_{2,E}^m + \Gamma_T\left(-\frac25E_2^m-\frac{3}{5\sqrt6}\Theta_2^m\right).
\]

행렬식으로 쓰면

\[
\Gamma_T
\begin{pmatrix}
9/10 & \sqrt6/10\\
3/(5\sqrt6) & 2/5
\end{pmatrix}
\begin{pmatrix}
\Theta_2^m\\
E_2^m
\end{pmatrix}
=
-\begin{pmatrix}
S_{2,T}^m\\
S_{2,E}^m
\end{pmatrix}.
\]

역행렬을 취하면 leading closure는

\[
\Theta_2^m
=-\Gamma_T^{-1}\left(\frac43 S_{2,T}^m-\frac{\sqrt6}{3}S_{2,E}^m\right)+O(\Gamma_T^{-2}),
\]
\[
E_2^m
=-\Gamma_T^{-1}\left(-\frac{\sqrt6}{3}S_{2,T}^m+3S_{2,E}^m\right)+O(\Gamma_T^{-2}).
\]

만약 \(S_{2,E}^m\)가 subleading이면

\[
E_2^m\simeq -\frac{\sqrt6}{4}\Theta_2^m,
\qquad
\Pi^m\simeq \frac52\Theta_2^m.
\]

이게 low-ℓ production startup의 최소 quadrupole-aware TCA다.

---

## 11. recombination과 reionization 모델

### 11.1 first-pass recombination

first pass에서는 recombination microphysics를 anisotropic하게 다시 짤 필요가 없다. 즉

\[
x_e(\eta),\qquad T_m(\eta)
\]

는 isotropic scalar history로 둔다.

필요한 visibility 변수는

\[
\Gamma_T(\eta)=a(\eta)n_e(\eta)x_e(\eta)\sigma_T,
\]
\[
\kappa(\eta)=\int_\eta^{\eta_0}\Gamma_T(\eta')\,d\eta',
\qquad
 g(\eta)=\Gamma_T(\eta)e^{-\kappa(\eta)}.
\]

중요한 건 \(x_e\) 자체보다

\[
g(\eta)\Pi^m(\eta)
\]

형태의 visibility-weighted quadrupole source다.

### 11.2 first-pass reionization

low-ℓ \(EE/TE\)에서는 reionization이 필수다. 최소 model은 homogeneous tanh history면 충분하다:

\[
x_e^{\rm rei}(z)
=
\frac{x_{e,\rm post}}{2}
\left[1+\tanh\frac{y(z_{\rm re})-y(z)}{\Delta y}\right],
\qquad y(z)=(1+z)^{3/2}.
\]

source는

\[
S_{E,\rm rei}^m(\eta)\propto g_{\rm rei}(\eta)\Pi^m(\eta)
\]

로 들어간다. 핵심은 rescatter되는 local quadrupole \(\Pi^m\)다.

### 11.3 tilted visibility

tilt가 있으면 optical depth는 electron frame 기준으로 방향의존이 된다.

\[
d\tilde\tau = \tilde n_e\sigma_T\,\gamma_e(1+v_e\cdot p)\,dt.
\]

따라서 conformal-time scattering rate의 최소 tilt-aware 정의는

\[
\tilde\Gamma_T(\eta,e)=a(\eta)\tilde n_e(\eta)x_e(\eta)\sigma_T\,\gamma_e(1+v_e\cdot e),
\]
\[
\tilde\kappa(\eta,e)=\int_\eta^{\eta_0}\tilde\Gamma_T(\eta',e)d\eta',
\qquad
\tilde g(\eta,e)=\tilde\Gamma_T(\eta,e)e^{-\tilde\kappa(\eta,e)}.
\]

즉 recombination/reionization의 최소 exactification은

\[
g(\eta)\Pi \quad\to\quad \tilde g(\eta,e)\,\tilde\zeta_{ab}(\eta,e)\tilde e^a\tilde e^b
\]

라고 볼 수 있다.

---

## 12. orthogonal vs tilted: 방정식의 차이

### 12.1 orthogonal Bianchi

- background transport frame과 electron frame이 background에서 일치한다.
- background matter momentum density는 0이다.
- source/collision/visibility가 frame split 없이 단순화된다.
- perturbation seed는 normal frame에서 바로 CAMB regular mode를 준다.

즉 가장 단순한 low-ℓ tetrad solver다.

### 12.2 tilted Bianchi

- transport는 여전히 \(n^a\)-frame에 고정한다.
- collision/source/visibility는 electron frame에서 계산한다.
- species별
  \[
  u_{(s)}^a=\gamma_s(n^a+v_{(s)}^a)
  \]
  를 도입한다.
- background momentum density와 perturbation dipole가 자연스럽게 생긴다.
- visibility가 \(\tilde g(\eta,e)\)로 방향의존이 된다.
- moment language로 내리면 collision이 \(\ell\leftrightarrow \ell\pm1\) mixing을 추가로 만든다.

즉 tilted의 차이는 “새 항 하나 더 넣는 것”이 아니라, **모든 source/collision/visibility를 electron-frame corrected form으로 바꾸는 것**이다.

---

## 13. 초기조건(IC)

### 13.1 background IC

#### orthogonal

\[
v_{(s)}^a(\eta_i)=0,
\qquad
q_a^{(s)}(\eta_i)=0,
\qquad
\pi_{ab}^{(s)}(\eta_i)=0
\]

for matter species.

#### tilted

species별

\[
v_{e,i},\qquad v_{b,i},\qquad v_{c,i},\dots
\]

를 주어야 하며, total momentum constraint

\[
8\pi P_i^{\rm (tot)}=e^{-\alpha}\left(\sigma_{jk}C^j{}_{ki}-\sigma_{ij}C^k{}_{kj}\right)
\]

와 일치시켜야 한다.

### 13.2 perturbation IC: CAMB regular adiabatic mode

low-ℓ solver의 perturbation seed는 FLRW limit에서 CAMB standard IC로 가야 한다. superhorizon startup \(x=k\tau\ll1\)에서 regular seed는

\[
\eta_{\rm cov}
=
2\mathcal B_K^2\left[1-\frac{x^2}{12}\left(\mathcal B_K^2-\frac{10}{4R_\nu+15}\right)\right],
\]
\[
\Delta_\gamma=\Delta_\nu
=
\frac{\mathcal B_K^2}{3}x^2-\frac{\mathcal B_K^2}{15}\omega k^2\tau^3,
\]
\[
\Delta_c=\Delta_b
=
\frac{\mathcal B_K^2}{4}x^2-\frac{\mathcal B_K^2}{20}\omega k^2\tau^3,
\]
\[
q_\gamma=\frac{\mathcal B_K^2}{27}x^3,
\qquad
q_\nu=\frac{\mathcal B_K^2}{27}\frac{4R_\nu+23}{4R_\nu+15}x^3,
\]
\[
\pi_\nu=-\frac{4}{3(4R_\nu+15)}x^2+\cdots,
\qquad
G_3=-\frac{4}{21(4R_\nu+15)}x^3,
\]
\[
Z=-\frac{\mathcal B_K^2}{2}k\tau+\frac{3\mathcal B_K^2}{20}\omega k\tau^2.
\]

flat FLRW limit에서는 \(\mathcal B_K^2\to1\)로 내려간다.

### 13.3 photon quadrupole/polarization startup

explicit \((\Theta_2,E_2)\)를 evolve할 경우 startup은 TCA manifold 위에 두는 게 좋다:

\[
\pi_\gamma=\frac{32}{45}k\tau_c(v_b+\sigma),
\qquad
E_2=\frac{\pi_\gamma}{4}.
\]

즉 orthogonal이든 tilted든 **quadrupole를 0으로 두는 것보다 TCA startup을 쓰는 게 안정적**이다.

### 13.4 orthogonal perturbation IC

orthogonal에선 normal frame에서 바로 CAMB regular seed를 준다:

\[
\delta X(\eta_i)=X_{\rm CAMB}^{\rm reg}(\eta_i).
\]

즉

\[
\delta\Delta_i,\ \delta q_i,\ \delta\pi_\nu,\ \delta G_3,\ \delta\eta,\ \delta Z
\]

를 그대로 넣고, photons는

\[
\delta\pi_\gamma=\frac{32}{45}k\tau_c(\delta v_b+\delta\sigma),
\qquad
\delta E_2=\frac14\delta\pi_\gamma.
\]

전체값은

\[
X_{\rm tot}=\bar X_{\rm Bianchi}+\delta X.
\]

### 13.5 tilted perturbation IC

tilted에선 먼저 electron frame에서

\[
\delta\tilde X(\eta_i)=X_{\rm CAMB}^{\rm reg}(\eta_i)
\]

를 주고, 그 다음 normal frame으로 boost한다:

\[
\delta X(\eta_i)=\mathrm{Boost}^{-1}_{\bar v_e}\left[\delta\tilde X(\eta_i)\right].
\]

boost rule의 leading-order exact PSTF form은

\[
\tilde I_{A_\ell}
=
\tilde h_{\langle A_\ell\rangle}{}^{B_\ell} I_{B_\ell}
-(\ell-2)v^b I_{bA_\ell}
-\frac{\ell(\ell+3)}{2\ell+1}v_{\langle a_\ell}I_{A_{\ell-1}\rangle},
\]

\[
\tilde E_{A_\ell}
=
\tilde h_{\langle A_\ell\rangle}{}^{B_\ell} E_{B_\ell}
-\frac{\ell(\ell+3)}{2\ell+1}v_{\langle a_\ell}E_{A_{\ell-1}\rangle}
-\frac{(\ell-2)(\ell-1)(\ell+3)}{(\ell+1)^2}v^bE_{bA_\ell}
-\frac{6}{\ell+1}v^b\epsilon_{bc\langle a_\ell}B_{A_{\ell-1}\rangle}{}^c,
\]

\[
\tilde B_{A_\ell}
=
\tilde h_{\langle A_\ell\rangle}{}^{B_\ell} B_{B_\ell}
-\frac{\ell(\ell+3)}{2\ell+1}v_{\langle a_\ell}B_{A_{\ell-1}\rangle}
-\frac{(\ell-2)(\ell-1)(\ell+3)}{(\ell+1)^2}v^bB_{bA_\ell}
+\frac{6}{\ell+1}v^b\epsilon_{bc\langle a_\ell}E_{A_{\ell-1}\rangle}{}^c.
\]

startup visibility도 electron frame 기준으로

\[
\tilde\Gamma_T(\eta_i,e)=a\tilde n_e x_e\sigma_T\,\gamma_e(1+v_e\cdot e)
\]

를 써야 한다.

즉 tilted IC의 핵심은 **CAMB seed 자체를 바꾸는 게 아니라, 어느 frame에서 seed를 주느냐를 바꾸는 것**이다.

---

## 14. observer-side 출력과 direction-dependent likelihood

solver 내부 표현은 \(\Theta_{\ell m},E_{\ell m},B_{\ell m}\)가 유리하지만, direction-dependent likelihood의 최종 데이터 표현은 대개 \(T,Q,U\) 또는 observer-projected \(a_{\ell m}^{T,E,B}\)가 더 자연스럽다.

### 14.1 observer-side 출력

최소 산출물은

\[
T(\hat n),\qquad Q(\hat n),\qquad U(\hat n)
\]

또는

\[
a_{\ell m}^{T},\qquad a_{\ell m}^{E},\qquad a_{\ell m}^{B}
\]

이다.

### 14.2 harmonic-space likelihood

low-ℓ full-sky likelihood에서는

\[
\mathbf d = \{a_{\ell m}^{T},a_{\ell m}^{E},a_{\ell m}^{B}\}
\]

를 데이터 벡터로 잡고

\[
-2\ln\mathcal L
=
(\mathbf d-\mathbf m)^T\mathbf C^{-1}(\mathbf d-\mathbf m)+\ln\det\mathbf C
\]

형태로 가는 것이 자연스럽다.

exact Bianchi에선 통계적 등방성이 깨지므로 단순 \(C_\ell\)만이 아니라

\[
\langle a_{\ell m}^{X}a_{\ell' m'}^{Y*}\rangle
\]

의 full covariance를 고려하는 것이 더 정직하다.

### 14.3 map-space likelihood

현실 데이터(마스크, beam, 비등방성 노이즈)를 직접 다루려면

\[
\mathbf d = \{T_p,Q_p,U_p\}_{p=1}^{N_{\rm pix}}
\]

와 같은 pixel likelihood가 더 자연스럽다.

따라서 추천 구조는

\[
\boxed{
\text{solve in }\Theta_{\ell m},E_{\ell m},B_{\ell m}
\ \to\ 
\text{evaluate likelihood in }T/Q/U\text{ or }a_{\ell m}^{T,E,B}.
}
\]

이다.

---

## 15. low-ℓ 전용 solver의 최소 완성형 요약

### background state
\[
\{\alpha,\beta_{ab},\Sigma_{ab},{}^{(3)}R_{ab},C^i{}_{jk}\}
\]

### matter state
\[
\{\rho_c,\rho_b,v_c,v_b,v_e\}
\]

orthogonal이면 \(v_s=0\), tilted면 species별 \(v_s\neq0\).

### radiation state
\[
\{\Theta_0,\Theta_1,\Theta_2,E_2\}
\]
필요하면
\[
\{\Theta_3,E_3\}
\]

### neutrino state
\[
\{\Delta_\nu,q_\nu,\pi_\nu,G_3\}
\]

### visibility / ionization state
\[
\{x_e(\eta),\Gamma_T,\kappa,g\}
\]

tilted면
\[
\{\tilde\Gamma_T(e),\tilde g(e)\}
\]

### evolution equation
\[
\mathbf X' = \mathsf L_B[n]\mathbf X + \mathsf C_T[v_e]\mathbf X + \mathbf S_{\rm pert}[v_e]
\]

### IC rule
- background: orthogonal 또는 tilted prescription
- perturbation: CAMB regular adiabatic seed
- photon quadrupole/polarization: TCA startup manifold
- tilted면 electron-frame seed 후 boost

---

## 16. 무엇이 이 문서의 범위 밖인가

이 문서는 의도적으로 다음을 production first pass 범위 밖으로 둔다.

1. anisotropic HyRec/RECFAST/Peebles \(C\)-factor
2. direction-dependent escape probability
3. patchy reionization
4. full high-ℓ Einstein–Boltzmann hierarchy
5. full vector/tensor primordial regular series의 상세 계수
6. non-classical Thomson/Compton kernel

이들은 모두 2차 패스 이후의 주제로 남긴다.

---

## 17. 최종 한 줄 요약

\[
\boxed{
\text{low-ℓ tetrad-based Bianchi CMB solver의 핵심은 }
\text{exact Bianchi transport + exact electron-frame Thomson tensor + explicit }(\Theta_2,E_2)
\text{ + scalar }x_e(\eta)\text{ + anisotropic LoS/likelihood이다.}
}
\]

그리고 orthogonal/tilted의 차이는 background exactness 자체보다

\[
\boxed{
\text{frame split, visibility, source evaluation, IC prescription의 차이}
}
\]

에 있다.
