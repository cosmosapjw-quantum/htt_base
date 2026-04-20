# Anisotropic / Inhomogeneous Reionization Solver Design
## Self-Contained Tetrad-Based Radiative Transfer Architecture Beyond Teff

**Document status:** design-spec / self-contained implementation blueprint  
**Authoritative transport path:** `S_N angular discretization + short-characteristics sweep + operator splitting (+ ALI for Lyα/scattering-heavy sectors)`  
**Reference / validation path:** `long characteristics`  
**Non-authoritative paths:** `pure excursion-set ionization barrier`, `M1-only closure for line-centered anisotropic transport`

---

## 0. 목적과 설계 철학

이 문서의 목적은 anisotropic/inhomogeneous한 시공간에서의 **reionization**을, 21cmFAST류의 빠른 반수치적(semi-numerical) 파이프라인을 유지하면서도, 그 핵심 물리 커널을 **tetrad-based radiative transfer**로 재구성하는 것이다.

핵심 원칙은 다음과 같다.

1. **Teff류 reduced manifold를 주 solver로 쓰지 않는다.**  
   reionization의 핵심은 ionizing UV/X-ray/Lyα field의 방향 의존 전달과 local chemistry의 결합이며, 이 문제는 본질적으로 radiative transfer problem이다.

2. **21cmFAST의 실용적 파이프라인은 유지한다.**  
   즉,
   \[
   \text{ICs}
   \to
   \text{density/velocity/source fields}
   \to
   \text{ionization/heating/Ly}\alpha
   \to
   \text{spin temperature}
   \to
   \delta T_b
   \]
   의 workflow는 유지한다.

3. **하지만 ionization kernel 자체는 excursion-set barrier에서 characteristic photon-budget law로 교체한다.**

4. **주 transport 방법은 }S_N\text{ + short characteristics}** 로 둔다.  
   이유는 다음과 같다.
   - 재이온화는 다수 광원 + 다중 주파수군 + 3D 격자 문제라서 grid-based deterministic sweep이 유리하다.
   - short-characteristics는 production sweep에서 long-characteristics보다 비용이 낮고 병렬화가 쉽다.
   - line-centered Lyα 및 scattering-heavy sector는 ALI/approximate-\(\Lambda\) iteration과 결합하기 쉽다.
   - pure moment closure(M1 등)는 crossing beams와 direction-selective shadowing을 잘못 처리할 수 있으므로 authoritative path로 부적합하다.

5. **long characteristics는 기준해 / 검증해로 남긴다.**  
   production default가 아니라 validation path로 둔다.

---

## 1. 21cmFAST를 기준점으로 삼되, 어디를 넘어서야 하는가

21cmFAST류 반수치 모델의 장점은 명확하다.

- 밀도, 속도, ionization fraction, spin temperature, brightness temperature까지 대형 3D 박스에서 빠르게 생성 가능
- halo/source prescription을 쉽게 바꿀 수 있음
- lightcone과 inference workflow에 잘 연결됨

하지만 anisotropic/inhomogeneous spacetime으로 가면, 기존 핵심 근사 몇 개가 더 이상 주 solver로 정직하지 않다.

### 1.1 유지할 것

- coeval / lightcone workflow
- source field construction
- redshift stepping
- cached previous-box dependence
- ionization / heating / Lyα / brightness temperature를 모듈 분리하는 구조

### 1.2 교체할 것

기존 excursion-set 핵심 판정:
\[
\zeta f_{\rm coll}(\mathbf x,R,z)\ge 1
\]

이를 다음과 같은 **retarded directional photon-budget inequality**로 교체한다:
\[
\sum_{m=1}^{N_\Omega} w_m
\sum_{b=1}^{N_E}
\int_0^{s_{\max}} ds\,
\Phi_{bm}(\mathbf x_m^{\rm ret}(s),t_m^{\rm ret}(s))
\exp[-\tau_{bm}(s)]
\ge
n_{\rm H}(\mathbf x,t)\,\Delta V\,
\Big[(1-x_{\rm HII})+N_{\rm rec}^{\rm eff}\Big].
\tag{1}
\]

즉 기존의 spherical barrier를 **direction-resolved retarded photon accounting**으로 대체한다.

### 1.3 왜 이게 필요한가

anisotropic/inhomogeneous background에서는
- path length가 방향 의존적이고,
- redshifting이 방향 의존적이며,
- attenuation과 self-shielding이 source와 observer 사이의 실제 ray history에 의존하고,
- 21-cm brightness mapping 자체가 scalar \(H(z)\)가 아니라 line-of-sight expansion tensor를 본다.

따라서 scalar filtering으로 닫는 순간 geometry signal이 주 커널에서 탈락한다.

---

## 2. 방법 선택: 왜 `S_N + short characteristics + ALI` 인가

### 2.1 후보군

1. **Long characteristics**
2. **Short characteristics**
3. **Discrete ordinates (\(S_N\))**
4. **Monte Carlo / packet transport**
5. **Moment closures (M1, VET-less FLD 등)**
6. **Hybrid ray + diffusion / reduced transport**

### 2.2 최종 선택

이 문서는 다음을 채택한다.

- **Angular representation:** \(S_N\) discrete ordinates
- **Spatial transport:** short characteristics
- **Scattering / stiff coupling acceleration:** ALI
- **Validation baseline:** long characteristics

즉,
\[
\boxed{
\text{Authoritative path}
=
S_N + \text{short characteristics} + \text{ALI} + \text{operator splitting}
}
\]

### 2.3 선택 이유

#### (a) reionization에서는 source 수가 많다
point source마다 individual long-ray bundle를 추적하는 것은 비싸다.  
반면 \(S_N\) sweep은 source 수보다 **grid + angle + frequency**에 의해 비용이 정해진다.

#### (b) anisotropic shadowing과 crossing beams가 중요하다
M1 closure는 beam crossing을 artificial merge로 바꾸기 쉽다.  
이는 reionization bubble overlap, shadowing behind sinks, anisotropic source clustering에 부적절하다.

#### (c) Lyα sector는 scattering-heavy다
Lyα pumping이나 near-line redistribution은 단순 흡수-방출보다 강한 coupling을 갖는다. 이런 경우 ALI는 전통적 \(\Lambda\)-iteration보다 훨씬 안정적이다.

#### (d) short characteristics는 production path로 적절하다
long characteristics보다 interpolation error는 생기지만, 3D grid production sweep에서 훨씬 현실적이다.

---

## 3. 기하 배경: 1+3 covariant + tetrad formalism

기본 congruence는 baryon rest frame \(u^a\)다.

\[
u^a u_a=-1,
\qquad
h_{ab}=g_{ab}+u_a u_b.
\]

### 3.1 속도구배 분해

\[
\nabla_b u_a
=
- A_a u_b
+ \frac13\Theta h_{ab}
+ \sigma_{ab}
+ \omega_{ab}.
\tag{2}
\]

여기서
\[
A_a=u^b\nabla_bu_a,
\qquad
\Theta=\nabla_a u^a,
\qquad
\sigma_{ab}=D_{\langle a}u_{b\rangle},
\qquad
\omega_{ab}=D_{[a}u_{b]}.
\]

### 3.2 tetrad decomposition

국소 orthonormal tetrad를
\[
e_{\hat 0}^a=u^a,
\qquad e_{\hat i}^a,
\qquad \hat i=1,2,3
\]
로 둔다.

photon 4-momentum은
\[
p^a=E\,(u^a+n^{\hat i}e_{\hat i}^a),
\qquad n^{\hat i}n_{\hat i}=1.
\tag{3}
\]

### 3.3 characteristic equations

\[
\frac{dx^a}{d\lambda}=p^a,
\qquad
\frac{dp^{\hat\alpha}}{d\lambda}
=
-\omega^{\hat\alpha}{}_{\hat\beta\hat\gamma}
 p^{\hat\beta}p^{\hat\gamma}.
\tag{4}
\]

energy drift는 leading order에서
\[
\frac{dE}{d\lambda}
=
-E^2
\left(
\frac13\Theta + A_{\hat i}n^{\hat i}+\sigma_{\hat i\hat j}n^{\hat i}n^{\hat j}
\right).
\tag{5}
\]

방향 drift는
\[
\frac{dn^{\hat i}}{d\lambda}
=
-E\,\mathcal P^{\hat i}{}_{\hat j}
\left(
A^{\hat j}+\sigma^{\hat j}{}_{\hat k}n^{\hat k}+\omega^{\hat j}{}_{\hat k}n^{\hat k}
\right)
-E\,\Omega^{\hat i}{}_{\hat j}n^{\hat j},
\qquad
\mathcal P^{\hat i}{}_{\hat j}=\delta^{\hat i}{}_{\hat j}-n^{\hat i}n_{\hat j}.
\tag{6}
\]

FLRW limit:
\[
\Theta\to 3H,
\qquad A_a,\sigma_{ab},\omega_{ab},\Omega^{\hat i}{}_{\hat j}\to 0.
\]

---

## 4. radiation species와 주파수군 구조

reionization solver는 최소한 다음 radiation sector를 분리해야 한다.

1. **Ionizing UV continuum**
   - H I ionization threshold above 13.6 eV
   - He I / He II threshold 포함 가능
2. **X-ray heating continuum**
3. **Lyα pumping field**
4. (선택) **recombination radiation / diffuse emissivity**

주파수군을
\[
E_b \in [E_{b-1/2},E_{b+1/2}],
\qquad b=1,\dots,N_E
\]
로 둔다.

방향군은
\[
\{n_m^{\hat i},w_m\}_{m=1}^{N_\Omega}
\]
로 둔다.

각 셀 \(i\), 주파수군 \(b\), 방향군 \(m\)마다 specific intensity 또는 photon occupation proxy를 저장한다:
\[
I_{i,b,m},
\qquad 
N_{i,b,m},
\qquad 
\Phi_{i,b,m}.
\]

권장 초기값:
- continuum UV/X-ray: upwind source-driven zero floor
- Lyα: background plus source injection

---

## 5. source model: halo/source field를 어떻게 연결할 것인가

21cmFAST의 장점 중 하나는 source modeling flexibility다. 이건 유지한다.

### 5.1 입력 source field

다음 중 하나를 지원한다.

1. **collapsed-fraction field 기반 source**
2. **halo catalogue 기반 source**
3. **stochastic halo sampling 기반 emissivity grid**
4. **external galaxy model / hydro sim snapshot ingestion**

### 5.2 source emissivity tensor/scalars

기본 emissivity는 baryon frame isotropic source로 시작한다.

\[
j_{\rm UV}(x,E,n)=\frac{1}{4\pi}j_{\rm UV}^{(0)}(x,E).
\tag{7}
\]

필요하면 anisotropic escape fraction / beaming을 허용해
\[
j_{\rm UV}(x,E,n)=\frac{1}{4\pi}j_{\rm UV}^{(0)}(x,E)
\left[1+\mathcal A_a n^a + \mathcal A_{ab}n^an^b+\cdots\right].
\tag{8}
\]

### 5.3 source normalization

실용적 source law 예:
\[
j_{\rm UV}^{(0)}(x,E)
=
\epsilon_\star f_{\rm esc}^{\rm ion}(M_h,z,x)
\,\dot\rho_\star(x)
\,s_{\rm ion}(E),
\tag{9}
\]
\[
j_X^{(0)}(x,E)
=
L_X/\mathrm{SFR}\times \dot\rho_\star(x)\,s_X(E),
\tag{10}
\]
\[
j_{\alpha}^{(0)}(x,\nu)
=
\dot\rho_\star(x)\,s_\alpha(\nu).
\tag{11}
\]

여기서
- \(s_{\rm ion}(E)\): ionizing SED
- \(s_X(E)\): X-ray SED
- \(s_\alpha(\nu)\): Lyα / near-Lyα emission profile

---

## 6. transport 방정식: continuum UV/X-ray

continuum sector에서는 scattering을 약하거나 무시 가능한 것으로 두고, absorption + emissivity 중심의 transport를 주 solver로 둔다.

각 \((b,m)\)에 대해 baryon tetrad frame RTE는
\[
\left[
\partial_t
+ c\,n_m^{\hat i}e_{\hat i}{}^a\nabla_a
+ \dot E_{bm}\partial_E
+ \dot n_{bm}^{\hat i}\nabla^{(\Omega)}_{\hat i}
\right] I_b(x,n_m)
=
\eta_b - \chi_b I_b.
\tag{12}
\]

multi-group discrete form에서는
\[
\frac{d I_{b,m}}{d\lambda}
=
\eta_{b,m}-\chi_{b,m}I_{b,m}.
\tag{13}
\]

opacity는
\[
\chi_{b,m}
=
 n_{\rm HI}\sigma_{\rm HI}(E_b)
+n_{\rm HeI}\sigma_{\rm HeI}(E_b)
+n_{\rm HeII}\sigma_{\rm HeII}(E_b)
+\chi_{\rm subgrid}.
\tag{14}
\]

formal short-characteristics solution:
\[
I_{\rm out}
=
I_{\rm in}e^{-\Delta\tau}
+
\int_0^{\Delta s} ds\,\eta(s)
\exp[-(\Delta\tau-\tau(s))].
\tag{15}
\]

cellwise linear/parabolic interpolation을 써서
\[
I_{i,b,m}^{n+1}=I_{\rm upwind}e^{-\Delta\tau_{i,b,m}} + \Psi_{i,b,m}[\eta],
\tag{16}
\]
형태로 구현한다.

---

## 7. Lyα sector: scattering-heavy transfer와 ALI

Lyα는 단순 흡수-방출보다 강한 redistribution을 갖기 때문에 continuum과 분리해야 한다.

### 7.1 master equation

\[
\left[
\partial_t
+ c\,n^{\hat i}e_{\hat i}{}^a\nabla_a
+ \dot\nu\,\partial_\nu
+ \dot n^{\hat i}\nabla^{(\Omega)}_{\hat i}
\right] I_\alpha
=
\eta_\alpha
-\chi_\alpha I_\alpha
+\partial_\nu\left(D_{\nu\nu}\partial_\nu I_\alpha\right)
+\mathcal S_{\rm redist}.
\tag{17}
\]

여기서
\[
\frac{d\ln\nu}{d\lambda}
=
-
\left(
\frac13\Theta + A_{\hat i}n^{\hat i}+\sigma_{\hat i\hat j}n^{\hat i}n^{\hat j}
\right)
\tag{18}
\]
이므로, line-center drift는 geometry-dependent다.

### 7.2 ALI splitting

source function을
\[
S_\alpha = (1-\epsilon_\alpha) J_\alpha + \epsilon_\alpha B_\alpha + S_{\rm ext}
\tag{19}
\]
로 두면,
\[
J_\alpha = \Lambda[S_\alpha].
\tag{20}
\]

ALI에서는
\[
\Lambda = \Lambda^\ast + (\Lambda-\Lambda^\ast)
\tag{21}
\]
로 쪼개고,
\[
J^{(k+1)}
=
\Lambda^\ast[S^{(k+1)}]
+
(\Lambda-\Lambda^\ast)[S^{(k)}].
\tag{22}
\]

여기서 \(\Lambda^\ast\)는 diagonal 또는 nearest-neighbour approximate operator를 권장한다.

### 7.3 왜 ALI가 필요한가

Lyα pumping / redistribution은 local source와 mean intensity가 강하게 결합되어 ordinary \(\Lambda\)-iteration이 느리다. 따라서 production path로 ALI를 기본값으로 둔다.

---

## 8. local chemistry와 thermal evolution

### 8.1 hydrogen ionization fraction

\[
u^a\nabla_a x_{\rm HII}
=
(1-x_{\rm HII})\Gamma_{\rm HI}
-
\alpha_B(T_k)\,C_{\rm eff}\,n_{\rm H}\,x_{\rm HII}^2
-
\Lambda_{\rm shld}.
\tag{23}
\]

photoionization rate는
\[
\Gamma_{\rm HI}(x)
=
\int d\Omega_n\int_{\nu_{\rm HI}}^\infty d\nu\,
\sigma_{\rm HI}(\nu)
\frac{I_\nu(x,n)}{h\nu}.
\tag{24}
\]

\(S_N\) discrete form:
\[
\Gamma_{\rm HI}(x)
\approx
\sum_{m=1}^{N_\Omega} w_m
\sum_{b\in \mathrm{ion}}
\sigma_{\rm HI}(E_b)
\frac{I_{b,m}(x)}{E_b} \Delta E_b.
\tag{25}
\]

### 8.2 helium fractions

\[
u^a\nabla_a x_{\rm HeII}
=
(1-x_{\rm HeII}-x_{\rm HeIII})\Gamma_{\rm HeI}
-
\alpha_{\rm HeII}(T_k)n_e x_{\rm HeII}
- x_{\rm HeII}\Gamma_{\rm HeII} + \cdots
\tag{26}
\]

\[
u^a\nabla_a x_{\rm HeIII}
=
 x_{\rm HeII}\Gamma_{\rm HeII}
-
\alpha_{\rm HeIII}(T_k)n_e x_{\rm HeIII}.
\tag{27}
\]

### 8.3 cumulative recombinations per baryon

\[
u^a\nabla_a N_{\rm rec}
=
\alpha_B(T_k)\,C_{\rm eff}\,n_{\rm H}\,x_{\rm HII}^2.
\tag{28}
\]

### 8.4 gas kinetic temperature

\[
u^a\nabla_a T_k
+ \frac23\Theta T_k
=
\frac{2}{3k_B n_{\rm tot}}
\left(
\mathcal H_X
+\mathcal H_{\rm UV}
+\mathcal H_{\rm Compt}
-\Lambda_{\rm cool}
\right).
\tag{29}
\]

X-ray heating term:
\[
\mathcal H_X
=
\int d\Omega_n \int dE\,
 n_{\rm HI}\sigma_{\rm HI}(E)
\left(E-E_{\rm HI}\right)
\frac{I_X(x,E,n)}{E}.
\tag{30}
\]

---

## 9. Lyα coupling and spin temperature

Lyα mean intensity로부터 Wouthuysen–Field coupling coefficient를 만든다.

\[
x_\alpha(x)
=
\mathcal A_\alpha
\int d\Omega_n\int d\nu\,
\varphi_\alpha(\nu)
I_\alpha(x,n,\nu).
\tag{31}
\]

collision coupling \(x_c\)와 함께 spin temperature는
\[
T_s^{-1}
=
\frac{T_\gamma^{-1}+x_c T_k^{-1}+x_\alpha T_c^{-1}}
{1+x_c+x_\alpha}.
\tag{32}
\]

scattering limit에서 흔히
\[
T_c\simeq T_k
\tag{33}
\]
를 쓴다.

### 9.1 21cmFAST-like 구현 관점

기존 `compute_spin_temperature()`는 redshift history를 따라 \(T_k, x_\alpha, T_s\)를 업데이트한다. 이 구조는 유지하되, 입력 field를 scalar filtered source field가 아니라 **characteristic-solved X-ray/Lyα radiation field**로 교체한다.

---

## 10. generalized ionization criterion

기존 excursion-set criterion을 replacement law로 다시 쓰면 다음이 authoritative form이다.

\[
\mathcal N_{\gamma}^{\rm in}(x,t)
=
\sum_{m,b} w_m
\int_0^{s_{\max}} ds\,
\Phi_{bm}(x_m^{\rm ret}(s),t_m^{\rm ret}(s))
\exp[-\tau_{bm}(s)]
\tag{34}
\]

그리고 셀 ionization update는
\[
\mathcal N_{\gamma}^{\rm in}\,\Delta t
\ge
n_{\rm H}\Delta V
\left[(1-x_{\rm HII})+N_{\rm rec}^{\rm eff}\right].
\tag{35}
\]

실제 time-continuous form은 chemistry equation (23)로 가고, (35)는
- thresholded fully-ionized flagging
- source-balance diagnostics
- subgrid photon-accounting

에 쓴다.

### 10.1 photon conservation diagnostics

기존 21cmFAST가 photon conservation correction option을 갖는다는 점을 감안하면, 새 코드에서는 correction fit이 아니라 **직접 진단량**을 기본 출력으로 둔다.

\[
\epsilon_{\rm pc}(t)
:=
\frac{N_{\gamma,\rm emitted}-N_{\rm ionized}-N_{\rm recombined}-N_{\gamma,\rm escaped}}
{N_{\gamma,\rm emitted}}.
\tag{36}
\]

authoritative production run의 acceptance criterion은
\[
|\epsilon_{\rm pc}| < \epsilon_{\rm pc}^{\rm max}
\tag{37}
\]
형태로 둔다.

---

## 11. generalized 21-cm brightness temperature

관측 방향 \(s^a\)에 대해 line-of-sight expansion scalar를
\[
\Xi_{21}(x,s)
:=
 s^a s^b \nabla_a u_b
=
\frac13\Theta + \sigma_{ab}s^a s^b
\tag{38}
\]
로 둔다.

velocity split을 따로 두고 싶으면
\[
\Xi_{21}
=
\frac13\bar\Theta + \bar\sigma_{ab}s^as^b + s^as^bD_av_b.
\tag{39}
\]

optical depth는
\[
\tau_{21}(x,s)
=
\frac{3 c^3 h_{\rm P} A_{10} n_{\rm HI}}
{16 k_B \nu_{21}^2 T_s\,|\Xi_{21}(x,s)|}.
\tag{40}
\]

brightness temperature contrast는
\[
\delta T_b(x,s)
\simeq
\frac{T_s-T_\gamma}{1+z_{\rm obs}}
\left(1-e^{-\tau_{21}(x,s)}\right)
\approx
\frac{T_s-T_\gamma}{1+z_{\rm obs}}\tau_{21}(x,s).
\tag{41}
\]

optically thin limit:
\[
\delta T_b(x,s)
\propto
x_{\rm HI}(1+\delta_b)
\left(1-\frac{T_\gamma}{T_s}\right)
\frac{1}{\Xi_{21}(x,s)}.
\tag{42}
\]

즉 FLRW의
\[
\frac{H}{H+\partial_r v_r}
\]
보정이 일반 background에서는
\[
\frac{1}{\Xi_{21}(x,s)}
\]
로 승격된다.

---

## 12. orthogonal Bianchi와 tilted Bianchi specialization

### 12.1 orthogonal Bianchi

\[
u^a=n^a
\]
이면 baryon frame = normal frame이다.

- source가 isotropic여도 propagation이 anisotropic
- chemistry background는 homogeneous라면 time-only ODE로 유지 가능
- radiation field는 \(I(t,E,n)\) 형태의 angle dependence 유지

이 경우 geometry-induced anisotropy의 대부분은 propagation에 있다.

### 12.2 tilted Bianchi

\[
u^a=\Gamma(n^a+v^{\hat i}e_{\hat i}^a)
\tag{43}
\]
이면 source emissivity가 baryon frame isotropic여도 normal frame에선 anisotropic하게 보인다.

에너지 boost:
\[
E_{(u)}=\Gamma E_{(n)}(1-v_{\hat i}n^{\hat i}).
\tag{44}
\]

따라서
- source emissivity
- local chemistry input \(\Gamma_{\rm HI}\)
- line-of-sight brightness mapping

이 모두 baryon frame 기준으로 재해석되어야 한다.

---

## 13. authoritative module architecture

권장 모듈 구조:

### 13.1 `geometry_cov_rt`
역할:
- metric / tetrad / connection
- \(\Theta,\sigma_{ab},\omega_{ab},A_a\) 계산
- ray drift coefficients 제공

출력:
- `GeometryState`
- `RayCoeffField`

### 13.2 `source_model`
역할:
- halo / collapsed-fraction / external source ingestion
- UV/X-ray/Lyα emissivity 생성

출력:
- `UVSourceBox`
- `XraySourceBox`
- `LyaSourceBox`

### 13.3 `line_rt_sn`
역할:
- \(S_N\) ordinates
- short-characteristics sweep
- continuum transport
- optional ALI for Lyα

출력:
- `IntensityBox[species, freq, angle]`
- `PhotonBudgetBox`

### 13.4 `chemistry_reion`
역할:
- \(x_{\rm HII},x_{\rm HeII},x_{\rm HeIII},N_{\rm rec},T_k\) update
- self-shielding and subgrid sink correction

출력:
- `IonizationBox`
- `ThermalBox`

### 13.5 `spin_temp_rt`
역할:
- Lyα coupling
- X-ray heating linkage
- \(T_s\) 계산

출력:
- `TsBox`

### 13.6 `brightness_21cm_cov`
역할:
- \(\tau_{21}\), \(\delta T_b\), RSD/geometry-aware mapping

출력:
- `BrightnessTempBox`
- `LightconeSlices`

---

## 14. 상태벡터와 데이터 레이아웃

### 14.1 grid variables

각 spatial cell \(i\)에 대해 저장:

- matter:
  - `rho_b[i]`, `delta_b[i]`, `u^a[i]`
  - `Theta[i]`, `sigma_ab[i]`, `omega_ab[i]`, `A_a[i]`
- chemistry:
  - `xHII[i]`, `xHeII[i]`, `xHeIII[i]`, `Nrec[i]`
  - `Tk[i]`, `Ts[i]`, `xalpha[i]`
- radiation:
  - `I_uv[i,b,m]`
  - `I_x[i,b,m]`
  - `I_lya[i,q,m]`
- diagnostics:
  - `GammaHI[i]`, `GammaHeI[i]`, `GammaHeII[i]`
  - `HeatingX[i]`, `PhotonConsResidual[i]`

### 14.2 memory strategy

naive storage는 비싸다. production path에선 다음을 권장한다.

1. continuum UV/X-ray는 angle sweep 중 streaming buffer 사용
2. Lyα만 persistent field 저장
3. multi-group compression:
   - UV 8–16 groups
   - X-ray 8–24 groups
   - Lyα core/wings adaptively refined grid
4. ordinates:
   - coarse production: \(N_\Omega=12\)–24
   - validation: \(N_\Omega=48\)–96

---

## 15. 수치 알고리즘: operator splitting

### Step A. Geometry update
입력 redshift / time slice에서 `geometry_cov_rt` 호출.

### Step B. Source construction
`source_model`이 UV/X-ray/Lyα emissivity grid 생성.

### Step C. Continuum transport sweep
각 frequency group과 ordinate에 대해 upwind short-characteristics sweep:

\[
I_{i,b,m}^{n+1}
=
I_{\rm upwind}e^{-\Delta\tau_{i,b,m}}
+\Psi_{i,b,m}[\eta].
\tag{45}
\]

### Step D. Lyα ALI loop
\[
J_\alpha^{(k+1)}
=
\Lambda^\ast[S_\alpha^{(k+1)}] + (\Lambda-\Lambda^\ast)[S_\alpha^{(k)}].
\tag{46}
\]
수렴 기준:
\[
\max_i \frac{|J_{\alpha,i}^{(k+1)}-J_{\alpha,i}^{(k)}|}{J_{\alpha,i}^{(k)}+\epsilon}
< \varepsilon_{\rm ALI}.
\tag{47}
\]

### Step E. Rate and heating compression
\[
\Gamma_{\rm HI},\ \Gamma_{\rm HeI},\ \Gamma_{\rm HeII},\ \mathcal H_X,\ x_\alpha
\]
계산.

### Step F. Chemistry and thermal update
(23), (26), (27), (28), (29)를 explicit/implicit IMEX 형태로 적분.

### Step G. Spin temperature update
(32) 사용.

### Step H. 21-cm observable update
(40)–(42)를 사용해 \(\tau_{21}\), \(\delta T_b\) 계산.

### Step I. Photon conservation diagnostics
(36) 계산 및 acceptance check.

---

## 16. pseudocode skeleton

```python
for z_hi, z_lo in redshift_steps:
    geom = geometry_cov_rt.update(metric_state, fluid_state, z_hi, z_lo)

    src_uv, src_x, src_lya = source_model.build(halo_state, astro_params, geom)

    I_uv = line_rt_sn.solve_continuum(
        prev_I_uv, src_uv, geom, opacity_state, groups_uv, ordinates
    )
    I_x = line_rt_sn.solve_continuum(
        prev_I_x, src_x, geom, opacity_state, groups_x, ordinates
    )
    I_lya = line_rt_sn.solve_lya_ali(
        prev_I_lya, src_lya, geom, lya_params, ordinates, nu_grid
    )

    rates = chemistry_reion.compress_rates(I_uv, I_x, I_lya, opacity_state)

    ion_state = chemistry_reion.update_ionization(
        prev_ion_state, rates, geom, dt
    )
    therm_state = chemistry_reion.update_temperature(
        prev_therm_state, rates, geom, dt
    )

    ts_state = spin_temp_rt.update(
        ion_state, therm_state, I_lya, cmb_state, geom
    )

    bt_state = brightness_21cm_cov.compute(
        ion_state, therm_state, ts_state, geom, observer_dirs
    )

    diag = diagnostics.compute_photon_conservation(
        src_uv, ion_state, prev_ion_state, geom, dt
    )

    cache.write_all(z_lo, geom, ion_state, therm_state, ts_state, bt_state, diag)
```

---

## 17. 검증 ladder

### Level 0: transport-only analytic tests
- homogeneous slab absorption/emission
- point source inverse-square + attenuation check
- isotropic FLRW limit against analytic redshifting

### Level 1: continuum RT vs long-characteristics
- same source field, same opacity field
- compare `S_N + short-char` to long-characteristics reference

Acceptance:
\[
\|I^{\rm SC}-I^{\rm LC}\|/\|I^{\rm LC}\| < 1\% \text{ (coarse)}
\tag{48}
\]

### Level 2: Lyα ALI tests
- homogeneous scattering atmosphere benchmark
- frequency redistribution convergence test

### Level 3: FLRW reduction test
anisotropy off:
\[
\sigma_{ab}=\omega_{ab}=A_a=0,
\qquad
\Theta=3H(z)
\tag{49}
\]
에서 기존 21cmFAST-like global history와 정성/정량 비교.

### Level 4: anisotropic toy models
- Bianchi I with diagonal shear
- shadowing by single dense absorber
- anisotropic source cluster

### Level 5: photon conservation
\[
|\epsilon_{\rm pc}| < 10^{-3}
\tag{50}
\]
를 production aspiration으로 둔다.

---

## 18. 성능 전략

### 18.1 production path
- short characteristics
- low-order but balanced ordinates
- adaptive frequency grouping
- only Lyα sector on ALI
- hybrid persistent + streaming memory

### 18.2 validation path
- long characteristics reference
- higher \(N_\Omega\), higher \(N_E\)
- tighter ALI tolerance

### 18.3 future acceleration
- source clustering with domain decomposition
- frequency-parallel sweep
- angle-parallel sweep
- GPU-friendly sweep kernels
- multigrid ALI preconditioner

---

## 19. 최소 구현 목표(MVP)

### Phase 1
- FLRW + inhomogeneous density
- UV continuum only
- hydrogen-only ionization
- no Lyα scattering ALI yet
- generalized brightness with scalar \(H+\partial_r v_r\) fallback

### Phase 2
- full tetrad geometry support
- \(S_N\) short-char UV/X-ray
- hydrogen + helium ionization
- recombination counting

### Phase 3
- Lyα ALI
- full \(T_s\) coupling
- lightcone outputs
- photon-conserving acceptance gates

### Phase 4
- orthogonal Bianchi
- tilted Bianchi
- calibration against long-char and external RT code(s)

---

## 20. 최종 설계 판단

이 문서의 최종 판단은 다음과 같다.

1. **reionization의 authoritative physics path는 radiative transfer여야 한다.**
2. **그 RT의 production choice로는 }S_N + \text{short characteristics} + \text{ALI}\text{ 가 가장 균형이 좋다.}**
3. **21cmFAST의 workflow는 살릴 수 있지만, excursion-set ionization barrier는 authoritative kernel이 될 수 없다.**
4. **anisotropic/inhomogeneous geometry를 seriously 다룰수록, scalar filtering 대신 retarded directional photon accounting이 중심이 되어야 한다.**
5. **21-cm observable 자체도 단순 RSD correction이 아니라 geometry-aware line-of-sight expansion law를 보아야 한다.**

가장 압축된 헌법식은 이거다.

\[
\boxed{
\text{21cmFAST-like workflow}
+
\text{tetrad-based }S_N\text{ short-characteristic RT}
+
\text{ALI for Ly}\alpha
+
\text{local chemistry/thermal solver}
+
\text{geometry-aware }\delta T_b
}
\]

---

## 21. 부록: 구현시 절대 금지할 과장

- `excursion-set barrier만 잘 고치면 anisotropic reionization도 충분하다`
- `M1 closure로도 line anisotropy와 shadowing을 무리 없이 잡을 수 있다`
- `Lyα는 단순 local coupling coefficient table로 충분하다`
- `photon conservation correction fit이 있으니 authoritative RT를 대체할 수 있다`
- `brightness temperature에서 geometry는 source morphology보다 덜 중요하다`

이 다섯 개는 이 설계 문서의 기준에선 금지 문장이다.

