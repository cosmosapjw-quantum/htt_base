# HyRec-Cov-RT 설계문서
## Teff-free Primordial Recombination Solver on Anisotropic/Inhomogeneous Backgrounds
### S_N + Short-Characteristics + ALI + Effective Multilevel Atom

---

## 0. 문서 목적

이 문서는 기존 `HyRec-Cov` 설계문서에서 **Teff라는 전제를 완전히 제거**하고, recombination 문제에서 실제로 널리 쓰이는 방사수송 방법들 가운데 **가장 적절한 주 solver 조합**을 채택하여 다시 형식화한 설계문서다.

이 문서의 최종 입장은 다음과 같다.

1. **주 solver는 characteristic-based deterministic radiative transfer** 이다.
2. angular discretization은 **discrete ordinates \(S_N\)** 를 기본으로 한다.
3. spatial/frequency transport는 **short-characteristics sweep** 를 기본으로 하고, **long-characteristics** 는 기준해/검증해로만 둔다.
4. line–level coupling은 **ALI (Accelerated Lambda Iteration)** 또는 이에 준하는 operator-splitting/preconditioned \(\Lambda\)-iteration을 쓴다.
5. atomic structure는 **effective multilevel atom (EMLA)** 를 유지한다.
6. **M1 / diffusion / single-temperature reduced manifold** 는 recombination의 주 solver가 될 수 없다. 이들은 필요하면 coarse diagnostic 또는 preconditioner로만 쓴다.

즉 최종 architecture는

\[
\boxed{
\text{EMLA}
+
S_N\text{ angular discretization}
+
\text{short-characteristics transport}
+
\text{ALI / operator-preconditioned line iteration}
}
\]

이다.

---

## 1. 방법 선택: 왜 이 조합이 가장 적절한가

### 1.1 비교 대상

후보군은 대략 다음과 같다.

- long characteristics
- short characteristics
- hybrid characteristics
- discrete ordinates \(S_N\) sweep
- moment methods (M1, diffusion, flux-limited diffusion)
- Monte Carlo
- escape-probability / Sobolev-only closure

### 1.2 recombination에서 요구되는 조건

primordial recombination은 다음 특성을 가진다.

1. **line-centered problem** 이다.
   - Ly\(\alpha\)
   - He I resonance lines
   - two-photon/Raman/feedback
2. **매우 큰 광학깊이** 와 **frequency redistribution** 이 있다.
3. **높은 정밀도** 가 필요하다.
   - percent가 아니라 \(10^{-3}\) 또는 그 이하의 history error도 CMB에 영향 가능
4. **stochastic noise가 불리** 하다.
5. **crossing-beam / anisotropic illumination / directional redshifting** 을 잃으면 안 된다.
6. atomic populations와 radiation field를 같이 iterate해야 한다.

이 조건을 만족시키려면, 주 solver는 deterministic하고 line-angle-frequency 구조를 직접 다루어야 한다.

### 1.3 최종 권고

권고 조합은 다음이다.

- **Angular space**: discrete ordinates \(S_N\)
- **Transport**: short characteristics (production path)
- **Reference / verification**: long characteristics
- **Line coupling**: ALI / approximate-operator iteration
- **Atomic network**: EMLA
- **Fallback**: directional Sobolev only as diagnostic/preconditioner, never authoritative

### 1.4 왜 long characteristics 단독이 아니라 short characteristics인가

long characteristics는 가장 직관적이고 기준해로 좋지만, 모든 cell–direction–frequency 조합마다 source-to-cell ray integration을 직접 하면 비용이 너무 커진다. 반면 short characteristics는 neighbour-to-neighbour interpolation을 써서 훨씬 싸고, deterministic sweep 구조와 결합하기 좋다. production 코드에서는 short characteristics가 기본이고, long characteristics는 regression/reference test용으로만 두는 것이 맞다.

### 1.5 왜 M1이 아니라 \(S_N\) 인가

M1은 radiation energy density와 flux까지만 진화시키고 closure relation으로 intensity를 복원한다. 하지만 recombination line transfer는

- crossing beams,
- strong angular anisotropy,
- narrow resonant line redistribution,
- direction-dependent escape,

를 직접 다뤄야 하므로 two-moment closure는 구조적으로 너무 거칠다. 특히 crossing beams를 인공적으로 섞는 문제는 line transport에서 치명적일 수 있다. 따라서 M1은 주 solver가 아니라 coarse radiation background 또는 보조 프리컨디셔너 정도로만 가능하다.

### 1.6 왜 Monte Carlo가 아니라 deterministic인가

Monte Carlo는 일반 geometry/transport엔 강하지만, primordial recombination처럼

- low-noise precision,
- smooth time history,
- small correction extraction,

이 중요한 상황에서는 sampling noise가 근본적 약점이다. 따라서 MC는 baseline truth generator나 stress test 용도로는 쓸 수 있어도, HyRec를 대체하는 production history solver의 1순위는 아니다.

---

## 2. 설계 범위와 비범위

### 2.1 포함 범위

- hydrogen recombination
- helium recombination
- matter temperature evolution
- line-centered radiative transfer
- anisotropic/inhomogeneous background compatibility
- orthogonal / tilted Bianchi specialization
- visibility / optical-depth history output
- future CMB source bridge를 위한 interface

### 2.2 제외 범위

- full polarization transport
- final \(a_{\ell m}\), \(C_\ell\) extraction
- rigorous global well-posedness proof
- realizability-preserving high-order theorem
- full GRMHD-like radiation backreaction on geometry

---

## 3. 기본 기하와 1+3 covariant/tetrad 세팅

### 3.1 유체와 projector

baryon-electron congruence를 \(u^a\)로 둔다.

\[
u^a u_a = -1,
\qquad
h_{ab}=g_{ab}+u_a u_b.
\]

시간/공간 미분은

\[
\dot X := u^a\nabla_a X,
\qquad
D_a X := h_a{}^b\nabla_b X.
\]

속도구배 분해는

\[
\nabla_b u_a
=
- A_a u_b
+ \frac13\Theta h_{ab}
+ \sigma_{ab}
+ \omega_{ab},
\tag{3.1}
\]

where

\[
A_a=u^b\nabla_bu_a,
\qquad
\Theta=\nabla_a u^a,
\qquad
\sigma_{ab}=D_{\langle a}u_{b\rangle},
\qquad
\omega_{ab}=D_{[a}u_{b]}.
\]

### 3.2 tetrad

국소 orthonormal tetrad를

\[
e_{\hat0}^a=u^a,
\qquad e_{\hat i}^a\quad (\hat i=1,2,3)
\]

로 둔다. photon 4-momentum은

\[
p^a=E\,(u^a+n^{\hat i}e_{\hat i}^a),
\qquad n^{\hat i}n_{\hat i}=1.
\tag{3.2}
\]

### 3.3 phase-space characteristic

ray는

\[
\frac{dx^a}{d\lambda}=p^a,
\qquad
\frac{dp^{\hat\alpha}}{d\lambda}
=
-\omega^{\hat\alpha}{}_{\hat\beta\hat\gamma}
 p^{\hat\beta}p^{\hat\gamma}
\tag{3.3}
\]

를 따른다.

energy/direction 방정식의 leading form은

\[
\frac{dE}{d\lambda}
=
- E^2
\left(
\frac13\Theta + A_{\hat i}n^{\hat i} + \sigma_{\hat i\hat j}n^{\hat i}n^{\hat j}
\right),
\tag{3.4}
\]

\[
\frac{dn^{\hat i}}{d\lambda}
=
- E\,\mathcal P^{\hat i}{}_{\hat j}
\left(
A^{\hat j}+\sigma^{\hat j}{}_{\hat k}n^{\hat k}+\omega^{\hat j}{}_{\hat k}n^{\hat k}
\right)
- E\,\Omega^{\hat i}{}_{\hat j}n^{\hat j},
\qquad
\mathcal P^{\hat i}{}_{\hat j}=\delta^{\hat i}{}_{\hat j}-n^{\hat i}n_{\hat j}.
\tag{3.5}
\]

FLRW limit에서는 \(\Theta/3\to H\), 나머지 항이 사라진다.

---

## 4. radiation discretization: S_N + frequency grid

### 4.1 angular discretization

unit sphere를 \(N_\Omega\)개의 ordinate \(n_m^{\hat i}\)와 quadrature weight \(w_m\)로 이산화한다.

\[
\sum_{m=1}^{N_\Omega} w_m = 4\pi.
\tag{4.1}
\]

대표 선택지는 Lebedev, level-symmetric quadrature, product Gauss rules다.

line radiation state는

\[
\mathcal N_L(x^a,\nu,n^{\hat i})
\;
\longrightarrow
\;
\mathcal N_{L,q,m}(x)
\equiv
\mathcal N_L(x,\nu_q,n_m)
\tag{4.2}
\]

로 저장한다.

### 4.2 frequency discretization

각 line \(L\)에 대해 line-centered frequency grid를 둔다.

\[
\nu_q = \nu_L + \Delta\nu_q,
\qquad q=1,\dots,N_\nu^{(L)}.
\tag{4.3}
\]

Hydrogen Ly\(\alpha\)와 He I resonance는 separate adaptive window를 권장한다.

- core region: fine grid
- near wings: logarithmic 또는 stretched grid
- far wings: optional truncated asymptotic treatment

### 4.3 state compression

continuum block이 필요하면 angular moments를 따로 압축할 수 있지만, **line solver의 authoritative state는 \(\mathcal N_{L,q,m}\)** 이다.

---

## 5. line radiative transfer master equation

각 핵심 line \(L\)에 대해, baryon tetrad frame에서 radiation transfer는

\[
\left[
\partial_\ell
+
\frac{d\ln\nu}{d\ell}\,\nu\partial_\nu
+
\frac{dn^{\hat i}}{d\ell}\,\nabla^{(\Omega)}_{\hat i}
\right]
\mathcal N_L
=
\eta_L
-
\chi_L\mathcal N_L
+
\partial_\nu\!\left(D^{(L)}_{\nu\nu}\partial_\nu \mathcal N_L\right)
+
\mathcal S_{2\gamma}^{(L)}
+
\mathcal S_{\rm Raman}^{(L)}
+
\mathcal S_{\rm fb}^{(L)}.
\tag{5.1}
\]

여기서

- \(\eta_L\): emission/source function
- \(\chi_L\): true absorption opacity
- \(D^{(L)}_{\nu\nu}\): frequency diffusion coefficient
- \(\mathcal S_{2\gamma}^{(L)}\): two-photon source/sink
- \(\mathcal S_{\rm Raman}^{(L)}\): Raman terms
- \(\mathcal S_{\rm fb}^{(L)}\): line feedback coupling

이다.

(3.4)를 대입하면 frequency drift는

\[
\frac{d\ln\nu}{d\ell}
=
-
\left(
\frac13\Theta + A_{\hat i}n^{\hat i}+\sigma_{\hat i\hat j}n^{\hat i}n^{\hat j}
\right).
\tag{5.2}
\]

즉 isotropic scalar Hubble drift가 directional kinematic drift로 바뀐다.

---

## 6. short-characteristics discretization

### 6.1 transport sweep equation

grid cell \(c\), direction \(m\), frequency \(q\)에 대해 short-characteristics update는

\[
I^{\rm out}_{cqm}
=
I^{\rm in}_{cqm}\,e^{-\Delta\tau_{cqm}}
+
\Psi_{cqm}\,S_{cqm}
+
\Phi_{cqm}\,S^{\rm up}_{cqm}
+
\Xi_{cqm}\,S^{\rm dn}_{cqm},
\tag{6.1}
\]

형태를 갖는다.

여기서

- \(I^{\rm in}_{cqm}\): upwind intensity (interpolated)
- \(\Delta\tau_{cqm}\): cell optical depth increment
- \(S_{cqm}\): local source function
- \(S^{\rm up}_{cqm},S^{\rm dn}_{cqm}\): interpolation stencil용 source values

이다.

### 6.2 optical-depth increment

\[
\Delta\tau_{cqm}
=
\chi_{cqm}\,\Delta\ell_{cqm},
\tag{6.2}
\]

with

\[
\Delta\ell_{cqm}
=
\text{proper path length of ordinate }m\text{ through cell }c.
\tag{6.3}
\]

anisotropic background에선 \(\Delta\ell\)뿐 아니라 frequency drift도 ray마다 다르므로, sweep ordering은 단순 Cartesian 정렬이 아니라 **direction-dependent dependency graph** 또는 ordered upwind traversal이 필요하다.

### 6.3 operator splitting in frequency

line core에서 diffusion term이 stiffness를 유발하므로

\[
\mathcal L
=
\mathcal L_{\rm adv}^{(x,\Omega)}
+
\mathcal L_{\rm drift}^{(\nu)}
+
\mathcal L_{\rm diff}^{(\nu)}
+
\mathcal L_{\rm src}
\tag{6.4}
\]

로 split하고,

- spatial/angle advection: transport sweep
- frequency drift/diffusion: implicit tridiagonal solve
- local source update: ALI/preconditioned fixed point

로 나누는 것이 안전하다.

---

## 7. ALI / approximate-operator iteration

### 7.1 왜 ALI가 필요한가

line transfer는 높은 optical depth와 strong coupling 때문에 naive \(\Lambda\)-iteration이 매우 느리다. 따라서 source-function iteration에는 ALI 또는 approximate lambda operator가 필요하다.

formal solution을

\[
\mathcal N_L = \Lambda_L[S_L]
\tag{7.1}
\]

라 하면, ALI는

\[
\Lambda_L = \Lambda_L^* + (\Lambda_L-\Lambda_L^*)
\tag{7.2}
\]

로 쪼개고,

\[
S_L^{(k+1)}
=
\mathcal F\!
\left[
\Lambda_L^*[S_L^{(k+1)}]
+
(\Lambda_L-\Lambda_L^*)[S_L^{(k)}],
\text{level populations}^{(k+1)}
\right]
\tag{7.3}
\]

식으로 반복한다.

### 7.2 권장 \(\Lambda^*\)

초기 권장은

- diagonal \(\Lambda^*\)
- 또는 cell-local + nearest-neighbour block \(\Lambda^*\)

이다. 이후 line core coupling이 강하면 frequency-blocked tridiagonal 또는 block-banded approximate operator로 확장한다.

### 7.3 HyRec-Cov-RT에서의 역할

ALI는 여기서

- line source function update,
- level population coupling,
- feedback line coupling,

을 한꺼번에 안정화하는 핵심 iteration layer다.

---

## 8. effective multilevel atom (EMLA)

### 8.1 interface-state system

Hydrogen interface states \(i\in\mathcal I_{\rm H}\)에 대해

\[
0
=
 n_{\rm H}x_ex_p\,\alpha_i^{\rm eff}
+
\sum_{j\in\mathcal I_{\rm H}} x_j R^{\rm eff}_{j\to i}
+
 x_{1s}\,\beta^{\rm eff}_{1s\to i}
-
 x_i\left(
\beta_i^{\rm eff}
+
\sum_j R^{\rm eff}_{i\to j}
+
\Gamma^{\rm eff}_{i\to1s}
\right).
\tag{8.1}
\]

Helium interface states \(I\in\mathcal I_{\rm He}\)에 대해

\[
0
=
 n_e n_{\rm HeII}\,\tilde\alpha_I^{\rm eff}
+
\sum_J Y_J\tilde R^{\rm eff}_{J\to I}
-
Y_I\left(
\tilde\beta_I^{\rm eff}
+
\sum_J \tilde R^{\rm eff}_{I\to J}
+
\tilde\Gamma^{\rm eff}_{I\to g}
\right).
\tag{8.2}
\]

### 8.2 effective rate dependence

FLRW HyRec류와 달리 여기서는 effective rates가 일반적으로

\[
\alpha_i^{\rm eff}
=
\alpha_i^{\rm eff}[T_m,\mathcal J_{\rm cont}],
\qquad
\beta_i^{\rm eff}
=
\beta_i^{\rm eff}[T_r^{(0)},\mathcal J_{\rm cont}],
\tag{8.3}
\]

\[
\Gamma^{\rm eff}_{i\to1s}
=
\Gamma^{\rm eff}_{i\to1s}[\mathcal E_L],
\qquad
\tilde\Gamma^{\rm eff}_{I\to g}
=
\tilde\Gamma^{\rm eff}_{I\to g}[\mathcal E_{\rm HeI},\chi_{\rm HI}^{\rm cont},\mathcal E_{\rm fb}].
\tag{8.4}
\]

즉 line escape operator가 EMLA를 닫는 핵심 입력이다.

---

## 9. recombination history equations

### 9.1 free-electron fraction

history 변수는 scalar time function이 아니라 field일 수 있다. 가장 일반적으로는

\[
u^a\nabla_a x_e
=
\mathcal F_{\rm H}
\big[x_e,T_m,\{x_i\},\mathcal E_\alpha,\mathcal E_{2\gamma},\mathcal E_{\rm fb}\big]
+
\mathcal F_{\rm He}
\big[x_e,T_m,\{Y_I\},\mathcal E_{\rm HeI},\chi_{\rm HI}^{\rm cont}\big].
\tag{9.1}
\]

### 9.2 matter temperature

\[
u^a\nabla_a T_m
+
\frac23\Theta T_m
=
\Gamma_C(T_r^{(0)}-T_m)
+
\frac{2}{3k_B n_{\rm tot}}
\left(
\dot Q_{\rm ff}
+
\dot Q_{\rm bf}
+
\dot Q_{\rm bb}
+
\dot Q_{\rm inj}
\right).
\tag{9.2}
\]

여기서

\[
\Gamma_C
=
\frac{8\sigma_T a_R (T_r^{(0)})^4}{3m_e c}
\frac{x_e}{1+f_{\rm He}+x_e}.
\tag{9.3}
\]

### 9.3 optical depth and visibility

observer photon \(k^a\)에 대해

\[
\frac{d\tau}{d\lambda}
=
\sigma_T n_e (-u_a k^a),
\qquad
g(\eta)=\dot\tau e^{-\tau}.
\tag{9.4}
\]

anisotropic/tilted case에서는 \((-u_a k^a)\)가 direction dependent다.

---

## 10. directional and nonlocal escape operator

### 10.1 full nonlocal operator

line \(L\)에 대해 formal solution에서 유도되는 escape operator를

\[
\mathcal E_L[S_L](x,n)
:=
\int_0^{\infty} d\ell\,
\mathcal K_L(x_{\ell},\nu_{\ell},n_{\ell})
S_L(x_{\ell},\nu_{\ell},n_{\ell})
\exp\!\left[-\int_0^{\ell}d\ell'\,\chi_L(\ell')\right]
\tag{10.1}
\]

로 정의한다.

angle-averaged operator는

\[
\bar{\mathcal E}_L[S_L](x)
=
\frac{1}{4\pi}
\int d\Omega_n\,\mathcal E_L[S_L](x,n).
\tag{10.2}
\]

### 10.2 directional Sobolev fallback

production fallback/preconditioner로는

\[
\Xi_{\parallel}(x,n)
:=
n^a n^b\nabla_a u_b
=
\frac13\Theta + \sigma_{ab}n^a n^b,
\tag{10.3}
\]

\[
\tau_{S,L}(x,n)
=
\frac{A_{ul}\lambda_L^3}{8\pi}
\frac{\left(\frac{g_u}{g_l}n_l-n_u\right)}{|\Xi_{\parallel}(x,n)|},
\tag{10.4}
\]

\[
\beta_{S,L}(x,n)
=
\frac{1-e^{-\tau_{S,L}(x,n)}}{\tau_{S,L}(x,n)},
\qquad
\bar\beta_{S,L}(x)=\frac{1}{4\pi}\int d\Omega_n\,\beta_{S,L}(x,n).
\tag{10.5}
\]

를 사용한다.

그러나 이 경로는 **authoritative path가 아니라 fallback/preconditioner** 이다.

---

## 11. orthogonal / tilted Bianchi specialization

### 11.1 orthogonal Bianchi

\[
u^a=n^a
\tag{11.1}
\]

이면 baryon frame = normal frame이다.

- chemistry background는 homogeneous라면 time-only ODE로 남을 수 있다.
- 그러나 line radiation은
  \[
  \mathcal N_L = \mathcal N_L(t,\nu,n^{\hat i})
  \tag{11.2}
  \]
  로 남아 angle dependence를 유지한다.
- directional frequency drift는
  \[
  \frac{d\ln\nu}{dt} = -\left(\frac13\Theta+\sigma_{\hat i\hat j}n^{\hat i}n^{\hat j}\right).
  \tag{11.3}
  \]

### 11.2 tilted Bianchi

\[
u^a = \Gamma(n^a+v^{\hat i}e_{\hat i}^a),
\qquad \Gamma=(1-v^2)^{-1/2}.
\tag{11.4}
\]

이 경우 line transfer는 normal frame에서 transport하고 microphysics는 baryon frame에서 계산하는 **two-frame formulation** 이 필요하다.

energy transform은

\[
E_{(u)}=\Gamma E_{(n)}(1-v_{\hat i}n^{\hat i}),
\tag{11.5}
\]

so first-order tilt에서 line monopole는

\[
\mathcal N_L^{(u,0)}
=
\mathcal N_L^{(n,0)}
-
v_{\hat i}\mathcal N_L^{(n,1)\hat i}
+
O(v^2).
\tag{11.6}
\]

즉 baryon-frame rates는 normal-frame dipole/quadrupole와 섞인다.

---

## 12. 모듈 설계

새 코드는 `HyRec-Cov-RT` 로 부른다.

### 12.1 `geometry_cov_rt`

역할:
- \(g_{ab},u^a\) 또는 Bianchi parameters 입력
- tetrad 구성
- connection coefficients 계산
- \(\Theta,\sigma_{ab},\omega_{ab},A_a\) 계산
- ray dependency graph 구축

출력:
- geometry snapshot
- ray drift coefficients
- path metrics

### 12.2 `line_rt_sn`

역할:
- \(S_N\) ordinates 관리
- short-characteristics sweep
- frequency drift/diffusion solve
- ALI iteration driver
- line feedback coupling

입력:
- geometry fields
- line opacities/sources
- current populations

출력:
- \(\mathcal N_{L,q,m}\)
- \(\mathcal E_L\), \(\bar{\mathcal E}_L\)
- low moments \(J^{(L)},J_a^{(L)},J_{ab}^{(L)}\)

### 12.3 `hydrogen_emla_cov`

역할:
- hydrogen effective matrix assembly
- interface-state solve
- hydrogen contribution to \(\dot x_e\)

입력:
- \(T_m\), continuum diagnostics, \(\mathcal E_\alpha\), \(\mathcal E_{2\gamma}\), feedback terms

### 12.4 `helium_emla_cov`

역할:
- helium effective matrix assembly
- H continuum opacity coupling
- He line feedback inclusion

### 12.5 `history_cov_rt`

역할:
- 전체 orchestration
- redshift/time stepping
- line RT substep 호출
- atomic solve 호출
- \(x_e,T_m\) update
- visibility output

### 12.6 `reference_longchar`

역할:
- selected snapshots에 대해 long-characteristics 기준해 계산
- short-characteristics production path와 비교
- regression testing

---

## 13. 상태벡터와 데이터 구조

### 13.1 minimal authoritative state

\[
Y_{\rm rec}
=
\Big(
 x_e,
 T_m,
 \{x_i\}_{i\in\mathcal I_{\rm H}},
 \{Y_I\}_{I\in\mathcal I_{\rm He}},
 \{\mathcal N_{L,q,m}\}_{L,q,m}
\Big).
\tag{13.1}
\]

### 13.2 optional diagnostic state

- continuum radiation monopole/dipole
- accumulated residual norms
- directional Sobolev indicators
- ALI convergence monitors

### 13.3 recommended memory layout

for cache locality:

\[
\texttt{N[L][q][m][cell]}
\tag{13.2}
\]

또는 sweep ordering에 따라

\[
\texttt{N[m][L][q][cell]}
\tag{13.3}
\]

중 하나를 선택한다. production에서는 direction-major layout이 sweep에 유리할 가능성이 높다.

---

## 14. 시간적분 / iteration 순서

### 14.1 outer time step

각 \(t^n\to t^{n+1}\)에서:

1. geometry refresh
2. continuum refresh (optional)
3. line source/opacities build
4. line RT solve (\(S_N\)+short-char+ALI)
5. EMLA interface solve
6. \(x_e,T_m\) update
7. visibility/output update
8. adaptive error check / substep decision

### 14.2 pseudocode

```text
for step n:
    geom = build_geometry(state_metric, state_fluid)

    cont = update_continuum_diagnostics(state, geom)

    line_coeff = build_line_coefficients(state, cont, geom)

    for each line L:
        N_L = short_characteristics_sweep(N_L, line_coeff[L], geom)
        N_L = implicit_frequency_diffusion(N_L, line_coeff[L], geom)
    end

    N_all = ALI_iterate(N_all, state_populations, line_coeff, geom)

    escape_ops = compress_escape_operators(N_all, geom)

    H_rates = build_hydrogen_effective_system(state, escape_ops, cont)
    He_rates = build_helium_effective_system(state, escape_ops, cont)

    x_interface = solve_linear_system(H_rates.matrix, H_rates.source)
    y_interface = solve_linear_system(He_rates.matrix, He_rates.source)

    dx_e = rhs_xe(state, x_interface, y_interface, escape_ops, cont, geom)
    dT_m = rhs_Tm(state, x_interface, y_interface, escape_ops, cont, geom)

    state.x_e += dt * dx_e
    state.T_m += dt * dT_m
    state.interface_H = x_interface
    state.interface_He = y_interface

    update_visibility(state, geom)
    validate_step(state, diagnostics)
end
```

---

## 15. authoritative / fallback / diagnostic path

### 15.1 authoritative production path

\[
\boxed{
S_N + \text{short characteristics} + \text{ALI} + \text{EMLA}
}
\]

### 15.2 reference path

\[
\boxed{
\text{long characteristics} + \text{same EMLA backbone}
}
\]

### 15.3 diagnostic-only path

- directional Sobolev
- M1 or low-moment continuum background
- coarse angular compression

이들은 **inference-forbidden** 또는 최소한 **production-forbidden** 으로 표시한다.

---

## 16. 검증 ladder

### V0. isotropic FLRW recovery

목표:
- \(\Theta/3\to H\), \(\sigma,\omega,A\to0\)에서 isotropic HyRec-like history 복원
- \(x_e(z)\), \(T_m(z)\), visibility peak 비교

### V1. directional Sobolev sanity

목표:
- small-shear limit에서
  \[
  \bar\beta_{S,L}\to \beta_{S,L}^{\rm FLRW}
  \]
- \(\sigma/H\ll1\)에서 directional asymmetry scaling 확인

### V2. short vs long characteristics

목표:
- selected snapshots에서
  \[
  \|N_{\rm short}-N_{\rm long}\| < \epsilon_{\rm ref}
  \]
- production path의 interpolation bias 정량화

### V3. ALI convergence

목표:
- line source and populations의 coupled iteration이 monotone/contractive하게 수렴하는 영역 파악
- stiff regime에서 preconditioner 조정

### V4. orthogonal Bianchi regression

목표:
- homogeneous but anisotropic background에서 history 및 line anisotropy 재현
- angle-averaged history vs directional line field 분리 확인

### V5. tilted Bianchi regression

목표:
- frame transform consistency
- baryon-frame and normal-frame rate agreement to expected order in \(v\)

### V6. inhomogeneous patch test

목표:
- single overdense/underdense patch에서 line trapping, local delay/advance, gradient dependence 확인

---

## 17. MVP / release plan

### MVP-1

- hydrogen only
- orthogonal Bianchi / weakly inhomogeneous background
- Ly\(\alpha\) only
- \(S_N\)+short-char production
- long-char reference snapshots

### MVP-2

- hydrogen + two-photon + Raman
- He I resonance 추가
- ALI block operator 고도화

### MVP-3

- tilted Bianchi
- full H/He coupled history
- visibility/source bridge stabilization

### RC-1

- adaptive angular/frequency refinement
- performance tuning
- regression suite freeze

---

## 18. 구현 우선순위

1. geometry/tetrad kernel 고정
2. line RT toy solver 작성
3. directional Sobolev fallback 및 비교 harness 작성
4. hydrogen EMLA coupling
5. FLRW recovery 통과
6. short vs long regression 통과
7. helium coupling 추가
8. tilted/inhomogeneous extension

---

## 19. 최종 권고 문장

이 설계문서의 최종 메시지는 하나다.

> anisotropic/inhomogeneous primordial recombination에서 Teff 같은 reduced spectral manifold를 주 solver로 삼는 것은 부적절하다.
> HyRec 수준의 물리 정직성을 유지하려면,
> **EMLA + deterministic \(S_N\) angular transport + short-characteristics + ALI**
> 가 주 경로가 되어야 한다.
> long characteristics는 기준해로 남기고,
> Sobolev와 low-moment closures는 fallback/diagnostic으로만 써야 한다.

즉 `HyRec-Cov-RT`의 헌법 문장은 다음이다.

\[
\boxed{
\text{Authoritative path}=
\text{EMLA} + S_N + \text{short-char} + \text{ALI}
}
\]

---

## 20. 참고문헌 / 기준 문헌

1. Ali-Haimoud & Hirata, *HyRec: A fast and highly accurate primordial hydrogen and helium recombination code* (2010/2011).
2. Ali-Haimoud, Hirata & Dickinson, *A refined effective multilevel atom method for primordial hydrogen recombination* (2010).
3. Chluba et al., *Towards a complete treatment of the cosmological recombination problem* (2010).
4. Gnedin & Madau, *Modeling cosmic reionization* (2022 review) — RT algorithm landscape and 21cmFAST context.
5. Peter et al., *The Sweep Method for radiative Transfer in Arepo* (2022) — discrete ordinates sweep in cosmological RT.
6. Razoumov & Scott, *Three-dimensional numerical cosmological radiative transfer in an inhomogeneous medium* (1999).
7. Dumont et al., *Escape probability methods versus “exact” transfer* (2003) — exact transfer vs escape methods.
8. General ALI literature: Rybicki & Hummer 1991/1992; Hubeny and related reviews.

