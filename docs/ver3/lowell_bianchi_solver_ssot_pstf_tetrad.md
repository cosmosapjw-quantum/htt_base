
# Low-\ell Bianchi Einstein–Boltzmann Solver SSOT
## 1+3 gauge-invariant covariant PSTF + tetrad formulation
### 수학적 기반 / 물리현상 구현 / 알고리즘 / SDD PR-WBS

---

## 0. 문서의 역할과 분리 원칙

이 문서는 **관측가능량/통계/likelihood 문서와 분리된**, low-\ell Bianchi Einstein–Boltzmann solver의
**수학적 SSOT(single source of truth)** 이다.
여기서는 다음만 다룬다.

1. **비섭동(nonperturbative) spatially homogeneous background** 의 기하와 물질장
2. **그 background 위의 선형 perturbation** 과 방사전달 hierarchy
3. **CMB 계산에 반드시 들어가야 하는 물리현상**
4. **수식에서 코드로 직접 내려갈 수 있는 알고리즘/적분법/상태벡터**
5. **SDD 기반 PR/WBS/검증 루프/환각 방지용 프롬프트**

의도적으로 아래는 별도 문서로 뺐다.

- 관측 map \(T,Q,U\), \(a_{\ell m}\), \(C_\ell\), full covariance
- 데이터셋 매칭
- likelihood
- 통계 추론
- model comparison
- evidence / posterior / null simulation

이 문서의 기본 철학은 다음과 같다.

\[
\boxed{
\text{1+3 gauge-invariant covariant PSTF formalism을 권위 형식으로 유지하고,}
\quad
\text{tetrad / invariant-basis algebra를 실제 계산 엔진으로 사용한다.}
}
\]

즉, **설명 언어는 1+3 PSTF**, **계산 엔진은 tetrad + Lie algebra + representation backend** 이다.

---

## 1. 가정, 컨벤션, 단위, 부호

### 1.1 시공간 및 중력 방정식

metric signature는

\[
(-,+,+,+)
\]

로 둔다.
아인슈타인 방정식은

\[
G_{ab} + \Lambda g_{ab} = \kappa T_{ab},
\qquad
\kappa \equiv \frac{8\pi G}{c^4}.
\]

수치 코드 내부에서 \(c=1\)을 쓰더라도, 문서 레벨에서는 위 식을 권위 정의로 유지한다.

### 1.2 1+3 분해

background foliation의 법선 congruence를 \(n^a\)라 하고,

\[
g_{ab} = - n_a n_b + h_{ab}, \qquad h_{ab} n^b = 0
\]

로 projector \(h_{ab}\)를 정의한다.
시간 미분과 spatial derivative는

\[
\dot X \equiv n^a \nabla_a X,
\qquad
D_a X \equiv h_a{}^b \nabla_b X
\]

이다.
PSTF는 angle bracket으로 표기한다.

### 1.3 기본 background congruence 선택

이 문서 전체에서 background congruence는 **homogeneous slice의 법선** \(n^a\)이다.
따라서 \(n^a\)는 hypersurface-orthogonal이고, 공간적으로 homogeneous한 Bianchi slicing을 따른다.
기본 선택은

\[
A_a \equiv n^b \nabla_b n_a = 0,
\qquad
\omega_a[n] = 0.
\]

즉 **가속도 0, background vorticity 0인 normal congruence** 를 사용한다.
그러나 **물질의 global tilt** 는 허용한다.
즉 물질 4-속도 \(u^a_{(s)}\)가 일반적으로 \(n^a\)와 같을 필요는 없다.

### 1.4 운동학 분해

\[
\nabla_a n_b
=
\frac13 \Theta h_{ab} + \sigma_{ab}
\]

이며, 여기서

\[
H \equiv \frac{\Theta}{3},
\qquad
\sigma^2 \equiv \frac12 \sigma_{ab}\sigma^{ab}.
\]

### 1.5 시간 변수

권장 시간 변수는 conformal time \(\eta\) 또는 proper time \(t\) 둘 다 허용한다.
권위 형태는 proper-time 식으로 적고, 실제 코드에는

\[
d\eta = \frac{dt}{a_{\rm iso}(t)}
\]

또는 선택한 기준 scale variable에 맞춘 변환 계층을 둔다.
Bianchi 배경에서는 단일 isotropic scale factor가 항상 자연스럽지 않으므로,
코드 내부의 시간 변수는 다음 셋 중 하나로 고정해야 한다.

1. proper time \(t\),
2. mean logarithmic scale \(\alpha\) with \(H=\dot\alpha\),
3. conformal time \(\eta\) tied to a chosen mean scale \(a_{\rm m}=e^\alpha\).

본 문서에서는
\[
a_{\rm m}(t) \equiv e^{\alpha(t)},
\qquad
H = \dot\alpha
\]
를 사용한다.

### 1.6 단위/차원 체크

- \(\Theta, H, \sigma_{ab}\): \([{\rm time}]^{-1}\)
- \(^{(3)}R_{ab}, {}^{(3)}R\): \([{\rm length}]^{-2}\)
- \(\kappa \rho, \kappa p\): \([{\rm length}]^{-2}\)
- Thomson rate \(\Gamma_T\): \([{\rm time}]^{-1}\)
- optical depth \(\tau\): dimensionless

---

## 2. Tetrad + invariant basis + 1+3 PSTF의 결합 구조

### 2.1 공간적 homogeneous Lie algebra

spatially homogeneous slice \(\Sigma_t\) 위에 시간에 독립인 invariant basis \(E_A\)를 두고,

\[
[E_A,E_B] = C^C{}_{AB} E_C
\]

로 Lie algebra를 정의한다.
여기서 \(A,B,C\in\{1,2,3\}\)는 **group-invariant basis index** 다.
\(C^C{}_{AB}\)는 공간 위치에 무관한 상수이다.

### 2.2 두 종류의 spatial basis

실제 구현에서는 spatial basis를 두 층으로 분리한다.

#### (i) invariant basis \(E_A\)
- 구조상수 \(C^C{}_{AB}\)를 고정한다.
- Bianchi type별 algebra를 정의한다.

#### (ii) orthonormal PSTF triad \(e_i = e_i{}^A E_A\)
- \(i,j,k\in\{1,2,3\}\)는 **orthonormal tetrad spatial index**
- 방사전달, PSTF multipole, Thomson operator, curl/div 연산을 여기서 수행한다.

따라서
\[
C^k{}_{ij}(t) = e^k{}_A\, e_i{}^B e_j{}^C\, C^A{}_{BC}
\]
는 일반적으로 시간의존적이다.
반면 \(C^A{}_{BC}\) 자체는 type을 고정하면 상수다.

### 2.3 commutator decomposition

3차원 Lie algebra의 구조상수는

\[
C^k{}_{ij}
=
\epsilon_{ij\ell} n^{\ell k}
+
a_i \delta^k{}_j
-
a_j \delta^k{}_i
\]

로 분해한다.
여기서 \(n^{ij}=n^{ji}\)이고 \(a_i\)는 spatial vector이다.
Jacobi identity는

\[
n^{ij} a_j = 0
\]

를 준다.
적절한 spatial rotation으로 canonical frame에서

\[
a_i = (a,0,0),
\qquad
n_{ij} = \mathrm{diag}(n_1,n_2,n_3)
\]

로 잡을 수 있다.

### 2.4 class A / class B

- class A: \(a_i=0\)
- class B: \(a_i\neq 0\)

class B는 momentum constraint와 compactness/topology, 그리고 일부 canonical Hamiltonian 전개에서
class A보다 더 조심해야 한다.
그러나 이 문서의 formulation 자체는 class A/B를 동일한 algebra interface로 다룬다.

### 2.5 Cartan 구조방정식

orthonormal triad coframe \(\omega^i\)에 대해 torsion-free Levi-Civita connection 1-form \(\omega^i{}_j\)는

\[
d\omega^i + \omega^i{}_j \wedge \omega^j = 0
\]

로 정해진다.
curvature 2-form은

\[
\Omega^i{}_j = d\omega^i{}_j + \omega^i{}_k \wedge \omega^k{}_j.
\]

이로부터 spatial Riemann/Ricci/scalar curvature를 얻는다.
실제 코드는 **commutator \(\to\) Levi-Civita connection \(\to\) \(^{(3)}R_{ij}\)** 순으로 자동 생성해야 한다.

---

## 3. 11개 Bianchi implementation family

여기서는 물리적/수치적 구현 관점에서 11개 family를 다음처럼 다룬다.

### 3.1 canonical table

| Type | Class | Canonical \(a_i\) | Canonical \(n_{ij}\) | 비고 |
|---|---|---:|---:|---|
| I | A | \((0,0,0)\) | \(\mathrm{diag}(0,0,0)\) | 평탄, Abelian |
| II | A | \((0,0,0)\) | \(\mathrm{diag}(n,0,0)\) | Heisenberg |
| III | B | \((a,0,0)\) | \(\mathrm{diag}(0,n,-n)\) with \(h=-1\) | \(VI_{-1}\) 특수형 |
| IV | B | \((a,0,0)\) | rank-1 nilpotent-like canonical form | solvable, isotropic limit 없음 |
| V | B | \((a,0,0)\) | \(\mathrm{diag}(0,0,0)\) | open FLRW limit |
| VI\(_0\) | A | \((0,0,0)\) | \(\mathrm{diag}(0,n,-n)\) | anisotropic open family |
| VI\(_h\) | B | \((a,0,0)\) | \(\mathrm{diag}(0,n,-n)\), \(h<0\) | \(h=-1/9\) exceptional sub-branch 분리 필요 |
| VII\(_0\) | A | \((0,0,0)\) | \(\mathrm{diag}(0,n,n)\) | flat FLRW limit |
| VII\(_h\) | B | \((a,0,0)\) | \(\mathrm{diag}(0,n,n)\), \(h>0\) | open FLRW limit |
| VIII | A | \((0,0,0)\) | signature \((+,+,-)\) | \(SL(2,\mathbb R)\)-like |
| IX | A | \((0,0,0)\) | signature \((+,+,+)\) | closed FLRW limit, \(SU(2)\) |

주의:
- 표의 canonical form은 **동형류를 고정하는 최소 data** 이다.
- 수치 코드에서 실제 curvature는 \(C^A{}_{BC}\)와 현재 spatial metric \(\gamma_{AB}(t)\)로 계산한다.
- Type III는 실제 구현에서는 \(VI_h\)의 \(h=-1\) special case로도 다룰 수 있지만,
  **문서/테스트/코드 스코어보드에서는 독립 family로 유지** 하는 편이 낫다.
- \(VI_h\)는 \(h=-1/9\)에서 동역학적/대칭적 특이성이 있어 solver branch를 별도로 두는 것이 안전하다.

### 3.2 isotropic-limit family와 intrinsically anisotropic family

#### isotropic limit가 자연스러운 family
\[
\mathrm{I}, \quad \mathrm{V}, \quad \mathrm{VII}_0, \quad \mathrm{VII}_h, \quad \mathrm{IX}
\]

이들에는 FLRW regular seed를 background anisotropy 0 limit와 연속적으로 매칭하는 전략이 가능하다.

#### isotropic limit가 자연스럽지 않은 family
\[
\mathrm{II},\ \mathrm{III},\ \mathrm{IV},\ \mathrm{VI}_0,\ \mathrm{VI}_h,\ \mathrm{VIII}
\]

이들에서는 “FLRW regular seed의 연속 변형”이 권위 정의가 될 수 없다.
이 경우 perturbation IC는
- background-consistent Frobenius expansion,
- local instantaneous eigenmode regularity,
- 또는 representation-theoretic regularity
로 잡아야 한다.



### 3.3 11개 type별 구현 매트릭스: orthogonal / global tilt / perturbation / local boost

아래 표는 **각 type을 실제 코드에서 어떻게 분기할지** 를 한 번에 정리한 것이다.

| Type | Orthogonal background | Globally tilted background | Perturbation backend | Local boost 처리 |
|---|---|---|---|---|
| I | 가장 단순. exact baseline. | 가능. homogeneous \(q_i\neq0\)를 Codazzi로 제어. | plane-wave / Cartesian Fourier | 출력 후 aberration만 적용 |
| II | 가능. non-Abelian curvature source 존재. | 가능하나 anisotropic stress와 momentum flux가 즉시 중요. | Heisenberg representation | geometry와 절대 혼동 금지 |
| III | 가능. \(VI_{-1}\) special family로 관리 가능. | 가능. class B momentum residual 감시 필수. | \(H^2\times\mathbb R\) or \(VI_{-1}\) backend | 출력 전용 |
| IV | 가능. class B testbed. | 가능하지만 초기 data projection 필수. | collocation / solv-representation | 출력 전용 |
| V | open FLRW anchor 가능. | 가능. tilted open-background validation 중요. | hyperbolic harmonics | 출력 전용 |
| VI\(_0\) | 가능. isotropic anchor 없음. | 가능. tilt가 있으면 background anisotropy와 flux 혼합 강함. | solvable-group backend | 출력 전용 |
| VI\(_h\) | 가능. \(h=-1/9\) 예외 branch 분리. | 가능하나 가장 까다로움. separate regression 필요. | general solv backend | 출력 전용 |
| VII\(_0\) | flat-limit anchor 가능. | 가능. helical transport + tilt coupling 확인 필요. | Euclidean helical backend | 출력 전용 |
| VII\(_h\) | open-limit anchor 가능. | 가능. production 우선순위 상위. | open helical backend | 출력 전용 |
| VIII | 가능. intrinsically anisotropic. | 가능하지만 no-FLRW-anchor + noncompact rep 모두 주의. | \(SL(2,\mathbb R)\) backend | 출력 전용 |
| IX | closed-limit anchor 가능. | 가능. compact slice + tilt consistency 필요. | \(SU(2)\)/Wigner \(D\) backend | 출력 전용 |

이 표의 핵심은 다음이다.

1. **11개 모든 type에 대해 orthogonal / globally tilted background는 원칙적으로 같은 Einstein–matter core로 다룬다.**
2. 달라지는 것은 \(C^A{}_{BC}\), representation backend, regularity rule이다.
3. **local boost는 11개 모든 type에서 동일하게 “출력 전용” 계층** 으로 분리한다.
4. 따라서 “Type을 늘리는 일”과 “observer boost artifact를 추가하는 일”은 서로 다른 PR이어야 한다.

### 3.4 11개 type별 IC provenance 규칙

family별 초기조건 provenance를 강제로 구분한다.

#### isotropic-limit family
\[
\mathrm{I},\ \mathrm{V},\ \mathrm{VII}_0,\ \mathrm{VII}_h,\ \mathrm{IX}
\]
- orthogonal: FLRW regular seed \(\to\) anisotropy \(0\) 연속한계
- globally tilted: electron-frame regular seed + inverse boost + constraint projection
- local boost: post-solve map/harmonic transform only

#### intrinsically anisotropic family
\[
\mathrm{II},\ \mathrm{III},\ \mathrm{IV},\ \mathrm{VI}_0,\ \mathrm{VI}_h,\ \mathrm{VIII}
\]
- orthogonal: background-consistent Frobenius / representation-regular IC
- globally tilted: 위 IC + background Codazzi-compatible \(q_i\) reconstruction
- local boost: post-solve only, seed generation과 무관

이 provenance를 문서화하지 않으면, 그 family의 perturbation 결과는 검증된 것으로 간주하면 안 된다.

### 3.5 background에서의 orthogonal / global tilt / local boost

모든 type마다 세 층을 구분한다.

#### Orthogonal background
\[
u^a_{(s)} = n^a
\]
즉 모든 species가 homogeneous slice에 직교한다.

#### Globally tilted background
\[
u^a_{(s)} = \Gamma_s (n^a + v^a_{(s)}(t)),
\qquad
D_i v^a_{(s)} = 0
\]
즉 **homogeneous하지만 non-orthogonal** 한 물질 흐름이다.
이는 background \(T_{ab}\), Codazzi constraint, Thomson frame, optical depth를 바꾼다.

#### Local boost / peculiar-velocity artifact
\[
u^a_{\rm obs} = \Gamma_{\rm obs}(n^a + b^a_{\rm obs}),
\qquad
\delta v^a(x,t) \neq 0
\]
이는 **background geometry를 바꾸지 않는다**.
출력 map/harmonic/post-processing 단계 또는 perturbation source로만 들어가야 한다.

이 세 층을 섞으면 안 된다.

---

## 4. Background nonperturbative Einstein–matter system

## 4.1 background state vector

실제 solver에서 최소 background 상태벡터는 다음처럼 둔다.

\[
\mathcal U_{\rm bg}
=
\{
\alpha,\ \sigma_{ij},\ \gamma_{AB},\ e_i{}^A,\ 
\hat\rho_s,\ \hat p_s,\ v^{(s)}_i,\ 
x_e,\ T_b,\ \cdots
\}.
\]

여기서
- \(\gamma_{AB}(t)\): invariant basis \(E_A\)에서의 spatial metric
- \(e_i{}^A(t)\): orthonormalization map
- \(v_i^{(s)}\): normal congruence \(n^a\)에 대한 species tilt

필요에 따라 \(^{(3)}R_{ij}\), \(E_{ij}\), \(H_{ij}\), \(q_i\), \(\pi_{ij}\)는
state로 저장하거나 diagnostic로 계산할 수 있다.
권장 순서는 **storage 최소화 + constraint diagnostics 강화** 다.

### 4.2 matter decomposition relative to \(n^a\)

species rest frame quantity를 \(\hat\rho_s,\hat p_s\)로 두고

\[
u^a_{(s)} = \Gamma_s(n^a + v^a_{(s)}),
\qquad
\Gamma_s = (1-v_s^2)^{-1/2}
\]

라 하면, \(n^a\)-frame decomposition은

\[
T^{(s)}_{ab}
=
\rho_s n_a n_b + 2 n_{(a} q^{(s)}_{b)} + p_s h_{ab} + \pi^{(s)}_{ab},
\]

\[
\rho_s
=
\Gamma_s^2(\hat\rho_s+\hat p_s) - \hat p_s,
\]

\[
q^{(s)}_a
=
\Gamma_s^2(\hat\rho_s+\hat p_s) v^{(s)}_a,
\]

\[
p_s
=
\hat p_s + \frac13 \Gamma_s^2(\hat\rho_s+\hat p_s)v_s^2,
\]

\[
\pi^{(s)}_{ab}
=
\Gamma_s^2(\hat\rho_s+\hat p_s)
v^{(s)}_{\langle a} v^{(s)}_{b\rangle}.
\]

따라서 global tilt가 있으면 background에서도
\[
q_a \neq 0,\qquad \pi_{ab}\neq 0
\]
가 일반적으로 성립한다.

### 4.3 algebraic spatial derivative on homogeneous tensors

group-invariant components를 orthonormal triad에서 표현하면,
homogeneous tensor는 공간좌표에 대한 explicit dependence가 없다.
그러나 covariant derivative는 connection 항 때문에 0이 아니다.

rank-\(r\) homogeneous tensor \(T_{j_1\cdots j_r}\)에 대해

\[
(D_B)_i T_{j_1\cdots j_r}
=
-\sum_{m=1}^r \Gamma^{k}{}_{i j_m}\,
T_{j_1\cdots k \cdots j_r},
\]

여기서 \(\Gamma^k{}_{ij}\)는 현재 orthonormal triad의 spatial Levi-Civita connection이다.
그러면 divergence, curl, Laplacian은

\[
(\mathrm{div}_B T)_{j_2\cdots j_r}
=
h^{i j_1}(D_B)_i T_{j_1 j_2\cdots j_r},
\]

\[
(\mathrm{curl}_B T)_{a_1\cdots a_r}
=
\epsilon_{bc\langle a_1}(D_B)^b T_{a_2\cdots a_r\rangle}{}^c,
\]

\[
\Delta_B T \equiv D_B^i D^B_i T
\]

로 정의한다.

이 정의는 **모든 Bianchi type에서 동일** 하고, 오직 \(\Gamma^k{}_{ij}\)만 type에 따라 달라진다.
따라서 solver의 geometry core는
\[
(C^A{}_{BC},\gamma_{AB}) \longrightarrow e_i{}^A \longrightarrow \Gamma^k{}_{ij}
\longrightarrow (\mathrm{div}_B,\mathrm{curl}_B,\Delta_B)
\]
를 생산하는 factory가 되어야 한다.

### 4.4 spatial curvature

권위 계산 경로는 Cartan 2nd equation이다.
즉
\[
(C^A{}_{BC},\gamma_{AB})
\to \Gamma^k{}_{ij}
\to {}^{(3)}R^i{}_{jkl}
\to {}^{(3)}R_{ij}
\to {}^{(3)}R
\]
로 간다.

class A/B를 통합한 compact formula로 쓰면

\[
{}^{(3)}R = -6 a^2 - n_{ij}n^{ij} + \frac12 (n^i{}_i)^2
\]

을 쓸 수 있고, trace-free part는

\[
{}^{(3)}S_{ij}
=
{}^{(3)}R_{\langle ij\rangle}
=
b_{\langle ij\rangle}
-
2 \epsilon_{k\ell\langle i} n_{j\rangle}{}^k a^\ell,
\qquad
b_{ij} \equiv 2 n_i{}^k n_{kj} - (n^k{}_k)n_{ij}.
\]

실제 코드에서는 이 compact formula와 Cartan-based formula를 **둘 다 구현하여 교차검증** 하는 것이 좋다.

### 4.5 Einstein equations in 1+3 PSTF form

background congruence \(n^a\)에 대해 \(A_a=\omega_a=0\)이면,
기본 식들은 다음으로 정리된다.

#### Gauss (Hamiltonian-like) constraint
\[
\frac13 \Theta^2
=
\kappa \rho + \Lambda + \sigma^2 - \frac12 {}^{(3)}R.
\]

#### Codazzi (momentum) constraint
\[
(\mathrm{div}_B \sigma)_a = \frac{2}{3} D_a \Theta + \kappa q_a.
\]

homogeneous scalar \(\Theta\)는 \(D_a\Theta=0\)이므로 실제로는

\[
(\mathrm{div}_B \sigma)_a = \kappa q_a.
\]

이 식이 **global tilt background의 핵심 제약** 이다.

#### Raychaudhuri
\[
\dot\Theta
=
-\frac13 \Theta^2
-2\sigma^2
-\frac12 \kappa \left(\rho + \frac{3p}{c^2}\right)c^2
+\Lambda c^2.
\]

\(c=1\) unit에서는 familiar form으로 줄어든다.

#### Shear propagation
\[
\dot{\sigma}_{\langle ab\rangle}
=
-\frac23 \Theta \sigma_{ab}
-\sigma_{c\langle a}\sigma_{b\rangle}{}^c
- E_{ab}
+\frac12 \kappa \pi_{ab}.
\]

#### magnetic Weyl constraint
\[
H_{ab} = (\mathrm{curl}_B \sigma)_{ab}.
\]

#### electric Weyl from Gauss-Codazzi-Ricci combination
\[
E_{ab}
=
{}^{(3)}S_{ab}
+ \frac13 \Theta \sigma_{ab}
-\sigma_{c\langle a}\sigma_{b\rangle}{}^c
-\frac12 \kappa \pi_{ab}.
\]

이 식은 sign convention에 민감하므로, 코드에서는
- Bianchi-identity evolution에서 구한 \(E_{ab}\),
- 위 algebraic/constraint 식에서 구한 \(E_{ab}\)
를 둘 다 계산해 residual을 추적해야 한다.

### 4.6 Bianchi identities as background constraint/evolution source

Bianchi identity는 background에서 단순한 “있으면 좋은 수식”이 아니라,
**제약 유지와 solver self-check의 핵심** 이다.
특히
- \(E_{ab}\) / \(H_{ab}\) propagation,
- matter conservation,
- momentum flux consistency,
- constraint propagation
을 감시하는 용도로 사용한다.

권장 전략은 다음이다.

1. primary evolution:
   \[
   \{\alpha,\sigma_{ab}, \hat\rho_s, v_a^{(s)}\}
   \]
2. derived geometry:
   \[
   {}^{(3)}R_{ab}, E_{ab}, H_{ab}
   \]
3. Bianchi residual monitor:
   \[
   \mathcal C_{\rm Gauss},\ \mathcal C_{\rm Codazzi},\ \mathcal C_E,\ \mathcal C_H
   \]

즉 background에서 constraint drift를 허용하지 않는다.

### 4.7 per-species conservation equations

각 species에 대해

\[
\nabla_b T_{(s)}^{ab}=0
\]

을 \(n^a\)-frame으로 분해하면

#### energy equation
\[
\dot\rho_s
+ (\rho_s + p_s)\Theta
+ (\mathrm{div}_B q_s)
+ 2\sigma^{ab}\pi^{(s)}_{ab}
= 0
\]

#### momentum equation
\[
\dot q^{(s)}_{\langle a\rangle}
+ \frac43 \Theta q^{(s)}_a
+ \sigma_a{}^b q^{(s)}_b
+ (\mathrm{div}_B \pi^{(s)})_a
= 0
\]

이 된다.
여기서는 homogeneous background에서 scalar pressure gradient는 0이므로 빠졌다.
tilted perfect fluid면 \(q^{(s)}_a,\pi^{(s)}_{ab}\)는 위의 boost 식으로 계산한다.

실제 수치에서는 species별로 다음 두 방식 중 하나를 선택한다.

- **rest-frame primitive update**
  \[
  \{\hat\rho_s, v^{(s)}_a\}
  \]
  를 update하고 \(n\)-frame stress tensor를 재구성

- **normal-frame conservative update**
  \[
  \{\rho_s, q^{(s)}_a\}
  \]
  를 직접 evolve하고 primitive recovery 수행

low-\ell Bianchi solver에서는 후자의 conservative update가 constraint 모니터링에 더 낫다.

### 4.8 electron–baryon sector

background reionization/recombination module은 일단 isotropic scalar history를 외부에서 공급받아도 되지만,
tilted case에서 scattering frame은 반드시 electron frame이다.
따라서 background level에서도
\[
u^a_e = \Gamma_e(n^a + v^a_e)
\]
를 유지해야 하며, baryon/electron comoving assumption을 쓸 때도
**\(v_b=v_e\)는 closure assumption이지 kinematic identity가 아니다.**

### 4.9 background initial conditions

#### orthogonal case
\[
v^{(s)}_i(t_i)=0,
\qquad
q_i(t_i)=0,
\qquad
\pi_{ij}(t_i)=0.
\]

이 경우 초기 constraint는
\[
(\mathrm{div}_B \sigma)_i = 0
\]
로 줄어든다.

#### globally tilted case
초기 \(v_i^{(s)}(t_i)\)를 임의로 넣으면 안 된다.
반드시
\[
(\mathrm{div}_B \sigma)_i - \kappa q_i = 0
\]
을 만족하게 맞추어야 한다.
즉 geometry가 먼저, tilt가 나중이 아니라,
**geometry–tilt pair를 constraint-satisfying data로 같이 생성** 해야 한다.

권장 procedure는:

1. Bianchi type와 \(\gamma_{AB}(t_i)\), \(\sigma_{ij}(t_i)\)를 선택
2. curvature와 \((\mathrm{div}_B \sigma)_i\) 계산
3. 원하는 species composition에 대해 허용 가능한 \(q_i\)를 계산
4. \(q_i = \sum_s \Gamma_s^2(\hat\rho_s+\hat p_s)v_i^{(s)}\) 를 풀어 \(v_i^{(s)}\) 복원
5. Gauss constraint까지 동시에 만족하도록 \(\rho\) 조정
6. residual이 tolerance 이하인 경우만 IC 채택

### 4.10 11개 type에 대한 background 구현 메모

#### Type I
- \(C^A{}_{BC}=0\)
- curvature 0
- 가장 쉬운 validation baseline
- tilted/orthogonal 둘 다 가장 먼저 구현

#### Type II
- rank-1 nonzero structure
- simplest non-Abelian testbed
- isotropic limit 없음
- homogeneous vector/tensor mode mixing이 즉시 나타남

#### Type III
- \(VI_{-1}\) 특수형
- open-like spatial behavior와 anisotropy가 함께 나타남
- class B machinery 검증용

#### Type IV
- class B 구현 확인용
- harmonic closed form보다 representation/collocation backend가 현실적

#### Type V
- open FLRW와 연속적으로 이어지는 baseline
- hyperbolic harmonics backend와 연결하기 좋음

#### Type VI\(_0\)
- class A지만 isotropic limit 없음
- sign-indefinite curvature sector test용

#### Type VI\(_h\)
- class B general family
- \(h=-1/9\) sub-branch는 별도 regression 필요
- 가장 먼저 완전 일반화 대상으로 잡기보다 backend interface 검증 후 단계적으로 올리는 것이 안전

#### Type VII\(_0\)
- flat isotropic limit
- helical mode coupling / spiral transport 테스트에 적합

#### Type VII\(_h\)
- open isotropic limit
- CMB Bianchi literature와 가장 직접적으로 연결되는 family 중 하나
- production-grade low-\ell path의 우선순위 상위

#### Type VIII
- negative-curvature class A
- \(SL(2,\mathbb R)\) representation backend 필요
- isotropic anchor 없음

#### Type IX
- closed family
- \(SU(2)\)/Wigner \(D\) backend 자연
- closed FLRW limit validation 가능

---

## 5. Radiation kinetic theory on a Bianchi background

### 5.1 권위 radiation variable 선택

원문처럼 \(I,Q,U\)만을 직접 evolve하면 energy-weight factor와 frame convention이 섞이기 쉽다.
권위 변수는 다음 둘 중 하나여야 한다.

#### Tier A (exact transport backend)
photon distribution matrix / brightness matrix
\[
\mathcal N_{ab}(x^c,p^i)
\]
또는 동등한 Liouville-invariant tensor-valued distribution.

#### Tier B (production low-\ell backend)
energy-integrated PSTF temperature/polarization multipoles
\[
\Theta_{A_\ell},\qquad E_{A_\ell},\qquad B_{A_\ell}.
\]

즉 **Tier A는 energy-dependent exact transport**, **Tier B는 low-\ell production hierarchy** 다.

### 5.2 photon momentum decomposition

orthonormal tetrad에서 광자 4-운동량은

\[
p^a = E(n^a + e^a),
\qquad
e_a e^a = 1,
\qquad
e_a n^a = 0.
\]

여기서 \(e^a\)는 photon propagation direction이다.
관측 line-of-sight \(\hat n\)과 부호를 혼동하지 않기 위해,
본 문서에서는 **transport direction은 \(e^a\)** 로 고정한다.
관측자 convention에서 sky direction을 \(\hat n=-e\)로 둘 수 있으나,
이는 오직 출력 단계에서만 허용한다.

### 5.3 geodesic transport

tetrad에서 광자의 에너지와 방향은 background geometry에 의해 운반된다.

\[
\frac{dE}{d\lambda}
=
- E^2 \left(H + \sigma_{ab} e^a e^b\right)
\]

이며, mean scale \(a_{\rm m}=e^\alpha\)를 사용한 comoving energy

\[
\epsilon \equiv E e^\alpha
\]

는

\[
\dot \epsilon
=
-\epsilon\, \sigma_{ab} e^a e^b
\]

를 따른다.
즉 isotropic redshift를 mean scale factor가 제거하고,
남는 것은 pure anisotropic shear redshift다.

방향 evolution은 connection으로부터

\[
\dot e^i
=
-\left(\delta^i{}_j - e^i e_j\right)\Gamma^j{}_{0k} e^k
-\Gamma^i{}_{jk} e^j e^k
\]

형태로 얻어진다.
Fermi-propagated spatial triad면 \(\Gamma^i{}_{0j}\)는 \(H\delta^i{}_j+\sigma^i{}_j\)로 정리된다.

### 5.4 polarization basis transport

screen projector는

\[
\mathcal H_{ab} = h_{ab} - e_a e_b
\]

이며, polarization tensor \(P_{ab}\)는
\[
P_{ab} n^b = 0,\qquad P_{ab} e^b = 0,\qquad P^a{}_a = 0
\]
를 만족하는 screen-space PSTF tensor다.

parallel transport 또는 선택한 polarization basis transport에 따라
gravitational basis rotation이 생기며,
이것이 \(E/B\) mixing source가 된다.
따라서 basis transport는 선택사항이 아니라 필수다.

### 5.5 PSTF multipole expansion

intensity와 polarization은 PSTF multipole로 전개한다.

\[
\mathcal I(E,e)
=
\sum_{\ell=0}^\infty
\mathcal I_{A_\ell}(E)\, e^{A_\ell},
\]

\[
P_{ab}(E,e)
=
\sum_{\ell=2}^\infty
\left[\mathcal E_{abA_{\ell-2}}(E)e^{A_{\ell-2}}\right]^{\rm TT}
+
\sum_{\ell=2}^\infty
\left[\epsilon_{cd(a} e^c \mathcal B_{b)}{}^{d}{}_{A_{\ell-2}}(E)e^{A_{\ell-2}}\right]^{\rm TT}.
\]

energy-integrated brightness 변수에서는 이를 \(\Theta_{A_\ell},E_{A_\ell},B_{A_\ell}\)로 바꿔 쓴다.

### 5.6 exact electron-frame Thomson scattering

collision operator는 반드시 electron rest frame에서 평가한다.
electron 4-속도는

\[
u_e^a = \Gamma_e (n^a + v_e^a).
\]

electron frame에서 photon energy/direction은

\[
\tilde E = -u_e^a p_a = \Gamma_e E (1 - v_e\cdot e),
\]

\[
\tilde e^a
=
\frac{1}{\Gamma_e(1-v_e\cdot e)}
\left[
n^a + e^a
\right]
-
u_e^a.
\]

따라서 **optical-depth prefactor의 권위 부호** 는 transport direction \(e^a\)를 쓰면

\[
\tilde\Gamma_T(e)
=
a_{\rm m}\, \tilde n_e \sigma_T\, \Gamma_e(1 - v_e\cdot e).
\]

만약 출력/관측 convention에서 \(\hat n=-e\)를 사용하면
\[
1-v_e\cdot e = 1+ v_e\cdot \hat n
\]
로 바뀐다.
이 두 convention을 문서/코드/플롯에서 섞으면 안 된다.

electron frame에서 intensity–polarization collision kernel의 schematic form은

\[
\tilde{\mathcal C}_I
=
-\tilde\Gamma_T \tilde I(\tilde e)
+
\frac{\tilde\Gamma_T}{4\pi}
\left[\tilde I_0 + \tilde\zeta_{ab}\tilde e^a \tilde e^b\right],
\]

\[
\tilde{\mathcal C}_{ab}^{\rm pol}
=
-\tilde\Gamma_T \tilde P_{ab}(\tilde e)
+
\frac{\tilde\Gamma_T}{4\pi}
\left[\tilde{\mathcal H}_a{}^c \tilde{\mathcal H}_b{}^d \tilde\zeta_{cd}\right]^{\rm TT},
\]

\[
\tilde\zeta_{ab}
=
\frac34 \tilde I_{ab}
+
\frac92 \tilde E_{ab}.
\]

실제 exact coefficient는 사용한 brightness normalization에 맞게 고정해야 하며,
Tier A와 Tier B에서 같은 normalization table을 공유해야 한다.

### 5.7 \(n\)-frame과 \(u_e\)-frame 사이의 boost

low-\ell production solver는 대부분 \(n\)-frame multipole을 저장하되,
collision 직전/직후에만 electron frame으로 boost하는 것이 효율적이다.
따라서 boost operator

\[
\mathcal B[v_e]:
\{\Theta_{A_\ell},E_{A_\ell},B_{A_\ell}\}_{n{\rm -frame}}
\leftrightarrow
\{\tilde\Theta_{A_\ell},\tilde E_{A_\ell},\tilde B_{A_\ell}\}_{u_e{\rm -frame}}
\]

를 독립 모듈로 둔다.

선형 small-tilt limit에서는 well-known multipole mixing이 나오며,
\(\ell\leftrightarrow \ell\pm1\) 섞임과 \(E/B\) 섞임이 포함된다.
이 모듈은 background global tilt와 local boost 모두에 재사용 가능하지만,
**해석은 분리해야 한다**.



### 5.8 low-\(\ell\) truncation은 개발 cutoff와 production cutoff를 분리

원문처럼 \(L=4/6/8\)만을 solver 권위 cutoff처럼 두면 안 된다.
이 값들은 **개발용 smoke/regression cutoff** 로는 유용하지만,
실제 low-\(\ell\) CMB 비교를 목표로 하는 production hierarchy에서는 별도의 \(L_{\rm solve}\) 정책이 필요하다.

권장 구분은 다음이다.

- 개발 smoke: \(L_{\rm dev}=4,6,8\)
- internal convergence: \(L_{\rm int}=12,16\)
- production low-\(\ell\): \(L_{\rm solve}\) 를 관측 출력 최대 \(\ell_{\rm obs}\)보다 충분히 크게 둔다

즉 본 문서에서는
\[
L_{\rm dev} \neq L_{\rm solve}
\]
를 강제한다.

핵심은 숫자 자체가 아니라,
1. truncation residual,
2. family-dependent mode mixing,
3. E/B leakage under basis transport,
4. collision block stability
를 함께 점검해야 한다는 점이다.

### 5.9 hierarchy

Tier B에서는 low-\(\ell\) truncated hierarchy를 푼다.

\[
\mathbf X
=
\{
\Theta_{A_\ell},
E_{A_\ell},
B_{A_\ell},
N^{(\nu)}_{A_\ell},
\Delta^{(s)},
v^{(s)}_a,
\cdots
\}_{0\le \ell\le L_{\rm solve}}.
\]

background anisotropy가 있으면
- SVT 분리가 일반적으로 깨지고,
- 서로 다른 \(m\),
- 때로는 서로 다른 mode family
사이에 coupling이 생긴다.
따라서 실제 선형 시스템은

\[
\dot{\mathbf X}
=
\mathsf A_{\rm geo}(t)\mathbf X
+
\mathsf A_{\rm coll}(t)\mathbf X
+
\mathsf A_{\rm matter}(t)\mathbf X
+
\mathbf S(t)
\]

형태의 block-sparse ODE/DAE system으로 작성해야 한다.

---

## 6. Perturbations on the Bianchi background

## 6.1 split

모든 변수는
\[
X(t,x^i)=\bar X(t)+\delta X(t,x^i)
\]
로 분해한다.
\(\bar X\)는 spatially homogeneous background,
\(\delta X\)는 linear perturbation이다.

### 6.2 gauge-invariant 1+3 variable set

background가 anisotropic이므로 FLRW-style scalar/vector/tensor 분리는 전역적으로 보존되지 않는다.
그러나 1+3 covariant perturbation 변수는 여전히 유용하다.
최소 perturbation set은 다음을 권장한다.

#### matter / geometry
\[
\Delta_a^{(s)} \equiv \frac{a_{\rm m}}{\bar\rho_s} D_a \rho_s,
\qquad
Z_a \equiv a_{\rm m} D_a \Theta,
\]

\[
\Sigma_{ab}^{(1)} \equiv a_{\rm m} D_{\langle a}\sigma_{b\rangle},
\qquad
\mathcal E_{ab}\equiv \delta E_{ab},
\qquad
\mathcal H_{ab}\equiv \delta H_{ab}.
\]

#### radiation
\[
\delta\Theta_{A_\ell},\qquad
\delta E_{A_\ell},\qquad
\delta B_{A_\ell}.
\]

#### neutrinos
\[
\delta N^{(\nu)}_{A_\ell}
\quad\text{또는}\quad
\delta \Theta_{A_\ell}^{(\nu)}
\]

#### baryon/electron/photon relative slip
\[
\delta v_b,\ \delta v_e,\ \delta v_\gamma.
\]

### 6.3 representation-theoretic spatial backend

모든 type에 대해 explicit closed-form harmonic을 강제하면 solver가 오히려 망가진다.
권위 backend는 다음 operator interface를 만족하는 basis family \(\{Q_\nu(x)\}\)만 요구한다.

\[
E_A Q_\nu = \sum_{\nu'} \Xi_{A,\nu\nu'} Q_{\nu'},
\]

\[
\Delta_B Q_\nu = - \sum_{\nu'} \Lambda_{\nu\nu'} Q_{\nu'},
\]

\[
\epsilon_{ABC} E^B E^C Q_\nu = \sum_{\nu'} \mathcal C_{A,\nu\nu'} Q_{\nu'}.
\]

즉 solver core는 “이 basis가 plane wave냐 hyperbolic harmonic이냐 Wigner \(D\)냐”를 모르고도
진행할 수 있어야 한다.
type-specific module은 오직
\[
\{\Xi_A,\Lambda,\mathcal C_A,\ \text{regularity rules}\}
\]
만 제공하면 된다.

이 인터페이스 덕분에 **11개 type 전체를 하나의 Boltzmann core로 묶을 수 있다.**

### 6.4 type별 perturbation spatial backend 권장안

#### I
- ordinary Fourier plane waves
- \(\Xi_A\) diagonal
- CAMB/CLASS regular seed와 직접 비교 가능

#### II
- Heisenberg group representation / nilmanifold Fourier-like basis
- explicit algebra action 구현 가능
- first non-Abelian perturbation regression target

#### III
- \(H^2\times \mathbb R\)-like separation 또는 \(VI_{-1}\) group basis
- hyperbolic-direction + line decomposition 가능

#### IV
- analytic closed harmonic보다 collocation / group-Fourier representation이 현실적
- first-pass는 pseudospectral backend 권장

#### V
- hyperbolic harmonics on \(H^3\)
- open FLRW limit와 연결

#### VI\(_0\)
- solvable-group representation backend
- isotropic regular seed 없음
- Frobenius IC 필요

#### VI\(_h\)
- general solvable-group representation backend
- \(h=-1/9\) 특별 branch는 별도 regularity solver

#### VII\(_0\)
- helical Euclidean basis
- axisymmetric / spiral-like mode coupling 확인 가능

#### VII\(_h\)
- open helical basis
- Bianchi CMB literature와 가장 직접 연결되는 production family

#### VIII
- \(SL(2,\mathbb R)\) unitary representation backend
- closed analytic harmonic보다 matrix-element 기반 backend 권장

#### IX
- \(SU(2)\) Wigner \(D\)-basis
- closed FLRW limit와 직접 비교 가능
- compact slice에서 spectral backend가 가장 깔끔

### 6.5 perturbation equations: generic operator form

모드 labels를 \(\nu\)라 하면 선형ized hierarchy는 abstract하게

\[
\dot{\mathbf X}_{\nu}
=
\sum_{\nu'}
\left[
\mathsf M^{\rm geo}_{\nu\nu'}(t)
+
\mathsf M^{\rm matter}_{\nu\nu'}(t)
+
\mathsf M^{\rm coll}_{\nu\nu'}(t)
\right]\mathbf X_{\nu'}
+
\mathbf S_\nu(t)
\]

로 쓴다.

여기서
- \(\mathsf M^{\rm geo}\): background shear/curvature/tetrad rotation에 의한 모드 혼합
- \(\mathsf M^{\rm matter}\): baryon/photon/neutrino/cdm coupling
- \(\mathsf M^{\rm coll}\): Thomson collision, TCA, visibility
- \(\mathbf S\): metric/Weyl/velocity source

anisotropic background에서는 \(\nu\)가 단순 \((k,\ell,m)\)가 아닐 수 있다.
따라서 코어는 \(\nu\)-space block matrix를 일반화된 sparse object로 다뤄야 한다.

### 6.6 global tilt vs perturbative velocity vs local observer boost

이 셋을 solver state에서 분리한다.

#### global tilt (background)
\[
\bar v_i^{(s)}(t)\neq 0,\qquad D_i \bar v_j^{(s)} = 0
\]
- background stress-energy를 변경
- Codazzi constraint에 직접 들어감
- Thomson frame/visibility를 변경
- background redshift와 quadrupole source를 바꿈

#### perturbative velocity
\[
\delta v_i^{(s)}(t,x)\neq 0
\]
- 선형 hierarchy의 dynamical variable
- source term과 baryon-photon slip에 들어감
- background geometry는 바꾸지 않음

#### local observer boost
\[
b_i^{\rm obs}
\]
- 최종 출력 map/harmonic에만 적용
- background/perturbation solver 자체는 건드리지 않음
- anomaly artifact 분리의 핵심

이 규칙을 어기면 “global geometry effect”와 “kinematic artifact”가 섞인다.

### 6.7 perturbation initial conditions

#### 6.7.1 isotropic-limit family의 regular seed

I, V, VII\(_0\), VII\(_h\), IX 에 대해서는
background anisotropy \(\to0\) limit에서 FLRW regular seed로 가야 한다.
즉 초기 epoch에서
\[
\mathbf X_\nu(t_i)
=
\mathbf X_\nu^{\rm FLRW,reg}(t_i)
+
\delta\mathbf X_\nu^{\rm aniso}(t_i),
\qquad
\delta\mathbf X_\nu^{\rm aniso}\to0
\]
가 되어야 한다.

#### 6.7.2 intrinsically anisotropic family의 seed

II, III, IV, VI\(_0\), VI\(_h\), VIII 에 대해서는 FLRW anchor가 없다.
이때는 다음 기준을 쓴다.

1. background-consistent regularity:
   모든 evolved variable이 \(t=t_i\)에서 유한
2. constraint consistency:
   선형ized Gauss/Codazzi/Bianchi residual 0
3. adiabatic/entropy labeling:
   species 간 상대 곡률/엔트로피 조합을 초기 data로 지정
4. representation regularity:
   spatial basis \(Q_\nu\)에 대해 선택한 regularity rule 만족

즉 이 family에서는 “CAMB seed를 억지로 boost/변형하는 것”이 권위 경로가 아니다.

#### 6.7.3 tilted IC

background가 globally tilted면,
collision/visibility의 자연 frame은 electron frame이다.
따라서 isotropic-limit family에서는 first-pass로 다음을 권장한다.

1. electron frame에서 regular seed 작성
2. \(n\)-frame으로 boost
3. linearized Codazzi/Gauss/Bianchi residual projection 수행
4. residual-corrected state를 사용

즉 “tilted IC”의 핵심은 **seed를 바꾸는 것이 아니라 seed를 주는 frame과 residual projection을 바꾸는 것** 이다.

---

## 7. CMB 계산에 반드시 들어가야 할 물리현상

이 절은 “무엇을 먼저 넣어야 진짜 low-\ell Bianchi CMB solver라고 부를 수 있는가”를 정리한다.

### 7.1 background anisotropic redshift
shear와 curvature가 광자 에너지와 방향을 바꾼다.
이게 없으면 Bianchi solver가 아니다.

### 7.2 polarization-basis transport
편광기저가 평행이동/회전하면서 \(E/B\) mixing을 일으킨다.
생략하면 anisotropic polarization이 위조된다.

### 7.3 exact electron-frame Thomson scattering
collision은 반드시 electron rest frame에서 평가해야 한다.
\(n\)-frame shortcut을 쓰면 global tilt와 local boost를 구분할 수 없다.

### 7.4 photon quadrupole and polarization source
편광은 quadrupole가 없으면 생기지 않는다.
따라서 \(\Theta_2\)와 \(E_2\)는 explicit state 또는 동등한 exact closure로 들어가야 한다.

### 7.5 baryon–electron–photon slip and tight coupling
recombination 전후에 stiffness를 지배하는 핵심.
이를 빼면 solver는 느리거나 거짓으로 안정화된다.

### 7.6 neutrino free streaming and anisotropic stress
low-\ell에서 metric/Weyl source와 phase에 직접 영향을 준다.
생략하면 background-anisotropy와 radiation-anisotropic-stress의 상쇄/증폭을 잘못 본다.

### 7.7 recombination visibility history
first-pass로 isotropic history adapter를 써도 되지만,
visibility 자체는 계산에 반드시 들어가야 한다.

### 7.8 homogeneous reionization rescattering
low-\ell polarization을 보려면 필수.
특히 EE/TE의 large-angle 구조를 완전히 바꾼다.

### 7.9 global tilt modulation of collision/visibility
tilted background를 주장하면서 \(\Gamma_T\)에 \(\Gamma_e(1-v_e\cdot e)\) factor가 없으면 틀린 구현이다.

### 7.10 local peculiar velocity / observer boost separation
kinematic dipole/quadrupole contamination을 geometry signal과 분리하는 데 필수.

### 7.11 representation-level mode mixing on anisotropic background
anisotropic background에서는 서로 다른 \((\ell,m)\) 또는 representation labels 사이의 coupling이 생긴다.
이걸 막아버리고 독립 mode처럼 풀면 mock solver가 된다.

### 7.12 constraint-preserving background evolution
constraint drift가 큰 background 위에 얹힌 Boltzmann hierarchy는 의미가 없다.

### 7.13 deferred but not forgotten
아래는 중요하지만 first-pass production requirement는 아니다.

- anisotropic atomic kinetics
- direction-dependent recombination escape probability
- patchy reionization
- nonlinear Compton / frequency redistribution beyond Thomson
- full high-\(\ell\) lensing/Born corrections

---

## 8. Numerical algorithms and integrators

## 8.1 solver decomposition

권장 분해는 4계층이다.

1. **Geometry core**
   \[
   (C^A{}_{BC}, \gamma_{AB})
   \mapsto
   \Gamma^i{}_{jk},\ ^{(3)}R_{ij},\ ^{(3)}R,\ \mathrm{div}_B,\mathrm{curl}_B,\Delta_B
   \]

2. **Background ODE core**
   \[
   \mathcal U_{\rm bg}' = \mathcal F_{\rm bg}(\mathcal U_{\rm bg})
   \]

3. **Perturbation/hierarchy core**
   \[
   \mathcal U_{\rm pert}' = \mathcal F_{\rm pert}(\mathcal U_{\rm pert}; \mathcal U_{\rm bg})
   \]

4. **Output/observable core**
   별도 문서

### 8.2 background integrator

background는 대개 nonstiff ODE + algebraic constraints 이다.
권장 순서는

- primary integrator: DOP853 또는 high-order explicit RK
- stiff tilt/matter closure가 있으면 Radau / Rosenbrock-W fallback
- 각 accepted step 후 constraint projection

constraint projection은

\[
\mathcal U_{\rm bg}^{n+1}
\to
\mathcal U_{\rm bg}^{n+1,\star}
=
\arg\min_{\mathcal U}
\|\mathcal U-\mathcal U_{\rm bg}^{n+1}\|_W^2
\quad
\text{s.t.}
\quad
\mathcal C_{\rm Gauss}=\mathcal C_{\rm Codazzi}=0
\]

형태의 local solve로 구현할 수 있다.

### 8.3 perturbation/hierarchy integrator

Thomson scattering 때문에 hierarchy는 재결합 전 stiff하다.
권장 전략은

#### phase A: tight-coupling regime
- reduced system + analytic closure
- \(\tau_c \equiv \Gamma_T^{-1}\) expansion
- \(\Theta_2,E_2\)까지 포함한 closure 유지

#### phase B: IMEX/Rosenbrock regime
- stiff collision block은 implicit
- free-streaming/background-advection block은 explicit
- sparse linear solve 사용

#### phase C: post-recombination free-streaming regime
- explicit or exponential integrator 가능
- 단, anisotropic advection와 basis rotation이 크면 IMEX 유지

### 8.4 recommended IMEX block split

\[
\dot{\mathbf X}
=
\underbrace{\mathsf A_{\rm free} \mathbf X + \mathsf A_{\rm geo}\mathbf X}_{\text{explicit}}
+
\underbrace{\mathsf A_{\rm coll}\mathbf X}_{\text{implicit}}
+
\mathbf S.
\]

여기서 \(\mathsf A_{\rm coll}\)는 block diagonal 또는 narrow-banded가 되도록
state ordering을 설계한다.

### 8.5 state ordering

권장 ordering은

\[
[\text{mode label } \nu]
\to
[\text{species}]
\to
[\ell]
\to
[m \text{ or PSTF slot}]
\]

또는 axisymmetric backend에서는
\[
[\nu]\to[\text{species}]\to[m]\to[\ell].
\]

핵심은 collision block, free-streaming block, boost block이
각각 sparse-friendly ordering을 가지도록 하는 것이다.

### 8.6 adaptive step controller

step-size controller는 단순 local truncation error만 보면 안 된다.
다음 scale을 동시에 감시해야 한다.

\[
H^{-1},\quad
|\sigma|^{-1},\quad
\Gamma_T^{-1},\quad
\lambda_{\rm mode}^{-1},\quad
\|\mathsf M_{\rm geo}\|^{-1}.
\]

권장 rule:

\[
\Delta t
=
\eta_{\rm saf}
\min
\left(
\frac{\epsilon_{\rm rel}}{\|\dot{\mathcal U}_{\rm bg}\|},
\frac{1}{\Gamma_T},
\frac{1}{\|\mathsf M_{\rm geo}\|},
\frac{1}{\lambda_{\max}}
\right)
\]

with safety factor \(\eta_{\rm saf}<1\).

### 8.7 interpolation / tabulation

background \(\mathcal U_{\rm bg}(t)\)는 perturbation solver에 고차 보간되어야 한다.
권장 방식:

- monotonic cubic Hermite for scalar histories
- piecewise polynomial with derivative continuity for tensor backgrounds
- visibility-related quantities는 log-space interpolation
- constraint residual이 큰 knot은 interpolation table에 넣지 않음

### 8.8 mandatory residuals

각 timestep 또는 checkpoint에서 반드시 저장할 residual:

\[
\mathcal C_{\rm Gauss},
\quad
\mathcal C_{\rm Codazzi},
\quad
\mathcal C_E,
\quad
\mathcal C_H,
\quad
\mathcal C_{\rm coll}^{\rm iso},
\quad
\mathcal C_{\rm boost}^{-1}.
\]

- \(\mathcal C_{\rm coll}^{\rm iso}\): isotropic radiation에서 polarization source가 0이어야 함
- \(\mathcal C_{\rm boost}^{-1}\): boost 후 inverse boost로 원상복귀되는지

---

## 9. 수식에서 코드로 내리는 pseudocode

## 9.1 Bianchi algebra factory

```python
def build_bianchi_algebra(bianchi_type, h_param=None, scale_params=None):
    # 1. canonical structure constants C^A_{BC} 생성
    C = canonical_structure_constants(bianchi_type, h_param, scale_params)

    # 2. class A/B, isotropic-limit family, exceptional branch metadata 반환
    meta = classify_bianchi_family(bianchi_type, h_param)

    return C, meta
```

## 9.2 geometry core

```python
def geometry_core(C_ABC, gamma_AB):
    # invariant basis -> orthonormal tetrad
    e_iA = orthonormalize_metric(gamma_AB)

    # time-dependent orthonormal commutator
    C_ijk = transform_structure_constants(C_ABC, e_iA)

    # Levi-Civita connection from Cartan equation
    Gamma_ijk = levi_civita_from_commutator(C_ijk)

    # spatial curvature
    R3_ij, R3 = spatial_ricci_from_connection(C_ijk, Gamma_ijk)

    # algebraic differential operators on homogeneous tensors
    ops = make_bianchi_diff_ops(Gamma_ijk)

    return e_iA, C_ijk, Gamma_ijk, R3_ij, R3, ops
```

## 9.3 background RHS

```python
def rhs_background(t, U_bg, params, C_ABC, meta):
    alpha, sigma_ij, gamma_AB, matter_state = unpack(U_bg)

    e_iA, C_ijk, Gamma_ijk, R3_ij, R3, ops = geometry_core(C_ABC, gamma_AB)

    rho, p, q_i, pi_ij = reconstruct_total_stress_energy(matter_state)

    # Einstein sector
    Theta = 3.0 * alpha_dot_from_state(U_bg)
    E_ij = electric_weyl_from_constraints(R3_ij, sigma_ij, Theta, pi_ij)
    H_ij = magnetic_weyl_from_curl_sigma(ops, sigma_ij)

    Theta_dot = raychaudhuri(Theta, sigma_ij, rho, p, R3, params)
    sigma_dot = shear_propagation(Theta, sigma_ij, E_ij, pi_ij)

    # matter sector
    matter_dot = []
    for species in matter_state:
        matter_dot.append(update_species_conservative(species, Theta, sigma_ij, ops))

    # metric / frame sector
    gamma_dot = metric_update_from_expansion_shear(gamma_AB, Theta, sigma_ij)
    alpha_dot = Theta / 3.0

    residuals = compute_background_constraints(Theta, sigma_ij, R3, q_i, ops)

    return pack(alpha_dot, sigma_dot, gamma_dot, matter_dot), residuals
```

## 9.4 exact electron-frame Thomson block

```python
def exact_thomson_block(rad_state_nframe, electron_velocity, xe, ne, a_mean):
    # n-frame -> electron frame
    rad_state_eframe = boost_to_electron_frame(rad_state_nframe, electron_velocity)

    # direction-dependent rate with transport convention e^a
    Gamma_tilde = a_mean * ne * xe * sigma_T * gamma(electron_velocity) * (1.0 - dot(v_e, e))

    # exact Thomson tensor in electron frame
    coll_eframe = thomson_tensor_operator(rad_state_eframe, Gamma_tilde)

    # back to n-frame
    coll_nframe = boost_from_electron_frame(coll_eframe, electron_velocity)

    return coll_nframe
```

## 9.5 perturbation backend interface

```python
class SpatialBackend:
    def derivative_action(self, A, mode_label):
        # returns Xi_A,nu,nu'
        ...
    def laplacian_action(self, mode_label):
        # returns Lambda_nu,nu'
        ...
    def regularity_projector(self, mode_label, family_meta):
        ...
```

## 9.6 hierarchy RHS

```python
def rhs_hierarchy(t, U_pert, bg_interp, spatial_backend, settings):
    bg = bg_interp(t)

    # geometry/matter matrices from background
    M_geo = build_geometry_matrix(bg, spatial_backend)
    M_mat = build_matter_matrix(bg, spatial_backend)
    S = build_metric_source(bg, spatial_backend)

    # collision block in electron frame
    M_coll = build_collision_matrix(bg)

    # IMEX split
    explicit_rhs = (M_geo + M_mat) @ U_pert + S
    implicit_rhs = M_coll @ U_pert

    return explicit_rhs, implicit_rhs
```

## 9.7 IMEX time step

```python
def step_imex(U, t, dt, rhs_builder):
    F_exp, F_imp = rhs_builder(t, U)

    # predictor
    U_star = explicit_predictor(U, dt, F_exp)

    # implicit solve on collision block
    U_new = solve_linear_implicit(U_star, dt, F_imp)

    return U_new
```

## 9.8 observer boost는 출력 전용

```python
def apply_local_observer_boost(output_map_or_alm, beta_obs):
    # do not feed back into background or hierarchy
    return aberration_doppler_transform(output_map_or_alm, beta_obs)
```

---

## 10. 개발 순서: production-grade로 살아남는 최소 PR stack

여기서는 수학적 dependency 순서대로 PR을 정렬한다.
“먼저 잘 맞는 mock spectrum을 만들고 나중에 수식을 메우는” 접근을 금지한다.

### PR-00 — conventions / geometry authority freeze
- 목적: sign, unit, frame, transport direction, electron-frame convention, boost convention freeze
- 산출물:
  - `CONVENTIONS.md`
  - `GEOMETRY_AUTHORITY.md`
  - `BOOST_AND_COLLISION_CONVENTIONS.md`
- done 조건:
  - transport direction \(e^a\)와 observer sky direction \(\hat n=-e\)가 명시적으로 분리됨
  - optical-depth prefactor sign regression test 통과

### PR-01 — Bianchi algebra factory (11 families)
- 목적: 11개 type canonical algebra + metadata registry
- 산출물:
  - `bianchi/algebra_registry.py`
  - `tests/test_all_11_types_registry.py`
- done 조건:
  - class A/B, isotropic-limit 여부, exceptional sub-branch metadata 반환

### PR-02 — geometry core
- 목적: \(C^A{}_{BC},\gamma_{AB}\to \Gamma^i{}_{jk},{}^{(3)}R_{ij},{}^{(3)}R,\mathrm{div/curl}\)
- 산출물:
  - `geometry/cartan.py`
  - `geometry/curvature.py`
  - `geometry/operators.py`
- done 조건:
  - Cartan-based curvature와 compact-form curvature 일치

### PR-03 — background Einstein–matter solver
- 목적: orthogonal + global tilt background ODE/constraint projection
- 산출물:
  - `background/einstein_matter.py`
  - `tests/test_gauss_codazzi_projection.py`
- done 조건:
  - orthogonal/tilted Type I baseline
  - Type V / VII_h / IX 중 하나 추가

### PR-04 — exact transport tier A
- 목적: energy-dependent exact ray + basis transport
- 산출물:
  - `transport/ray.py`
  - `transport/polarization_basis.py`
- done 조건:
  - isotropic redshift removed comoving energy \(\epsilon\) regression
  - pure-shear redshift test 통과

### PR-05 — exact electron-frame Thomson block
- 목적: collision operator authority path 확립
- 산출물:
  - `collision/thomson_exact.py`
  - `collision/boost.py`
- done 조건:
  - isotropic input \(\to\) polarization source 0
  - inverse boost regression 통과

### PR-06 — low-\ell projected hierarchy tier B
- 목적: PSTF multipole production solver
- 산출물:
  - `hierarchy/pstf_state.py`
  - `hierarchy/projected_solver.py`
- done 조건:
  - \(\Theta_\ell,E_\ell,B_\ell\) explicit state
  - background anisotropy에 의한 mode mixing block 구현

### PR-07 — tight coupling + electron-baryon slip
- 목적: stiff regime 안정화
- 산출물:
  - `tca/tca_aniso.py`
  - `tests/test_tca_switch.py`
- done 조건:
  - TCA on/off switching residual 제어

### PR-08 — recombination/reionization source wiring
- 목적: visibility source를 hierarchy와 연결
- 산출물:
  - `history/xe_adapter.py`
  - `history/reionization.py`
- done 조건:
  - isotropic history ingest
  - tilted \(\tilde\Gamma_T\) branch 구현

### PR-09 — spatial backends by family
- 목적: 11개 type 전체 perturbation backend interface 닫기
- 산출물:
  - `spatial_backends/typeI.py`
  - `...`
  - `spatial_backends/typeIX.py`
- 우선순위:
  1. I, V, VII\(_0\), VII\(_h\), IX
  2. II
  3. III, VI\(_0\)
  4. IV, VI\(_h\), VIII
- done 조건:
  - 각 family마다 \(\Xi_A,\Lambda,\mathcal C_A\) interface 동작

### PR-10 — perturbation IC package
- 목적: isotropic-limit family regular seed + intrinsically anisotropic family Frobenius seed
- 산출물:
  - `ics/flrw_regular.py`
  - `ics/aniso_frobenius.py`
- done 조건:
  - family별 IC provenance 문서화

### PR-11 — release gate before any statistical fitting
- 목적: observables/statistics로 넘어가기 전 물리적 완성도 gate
- 산출물:
  - `VALIDATION_GATE.md`
  - `run_validation.py`
- done 조건:
  - 아래 11절 체크리스트 통과

---

## 11. SDD WBS / 체크리스트 / 스코어보드

### 11.1 SDD 문서 구조

각 PR마다 최소한 아래 문서 6종을 강제한다.

1. `SPEC.md` — 수식/입출력/권위 경로
2. `INVARIANTS.md` — 보존량/제약/limit
3. `FAILURE_MODES.md` — 실패 패턴 최대 5개
4. `TEST_MATRIX.md` — smoke / regression / physics tests
5. `FIGURE_SEMANTICS.md` — 플롯이 무엇을 의미하는지
6. `NOT_ALLOWED.md` — 금지 shortcut/mock 목록

### 11.2 global checklist

#### geometry
- [ ] 11개 family registry 존재
- [ ] Cartan curvature와 compact formula 일치
- [ ] class A/B 둘 다 constraint drift 제어

#### background
- [ ] orthogonal/tilted 분리
- [ ] global tilt가 Codazzi를 만족
- [ ] local boost가 background를 절대 건드리지 않음

#### transport
- [ ] exact ray transport 존재
- [ ] polarization basis transport 존재
- [ ] electron-frame Thomson block 존재

#### hierarchy
- [ ] \(\Theta_2,E_2\) explicit 또는 exact-equivalent
- [ ] TCA branch 존재
- [ ] neutrino hierarchy 존재

#### source history
- [ ] recombination visibility ingest
- [ ] homogeneous reionization 존재
- [ ] tilted visibility prefactor 구현

#### validation
- [ ] isotropic limit recovery
- [ ] no-tilt vs tilt 비교
- [ ] local-boost-only vs global-tilt 비교
- [ ] family-specific backend regression

### 11.3 score rule

각 PR은 0–10점:

- 0–2: 메모/아이디어
- 3–4: 수식 freeze
- 5–6: 코드 skeleton + unit tests
- 7–8: physics smoke tests 통과
- 9–10: invariants + regression + failure modes 문서화

전체 progress는

\[
{\rm Progress}(\%) = \frac{\sum_i w_i s_i}{10\sum_i w_i}\times 100.
\]

권장 가중치:
- geometry core: 12
- background solver: 12
- exact transport: 12
- exact Thomson: 10
- hierarchy: 12
- TCA: 8
- recomb/reion: 8
- spatial backends: 14
- IC package: 6
- validation gate: 6

### 11.4 “통과 금지” 조건

아래 중 하나라도 참이면 **통계 fitting 단계로 넘어가면 안 된다.**

1. background constraint drift가 큰 상태
2. electron-frame collision이 빠진 상태
3. local boost와 global tilt를 구분하지 않은 상태
4. \(\Theta_2,E_2\)가 실제 state에 없는 상태
5. isotropic limit family에서 regular seed recovery 실패
6. intrinsically anisotropic family에서 IC provenance 없음
7. mock parameter fitting으로 spectra만 얼추 맞춘 상태

---

## 12. 메타인지 / 적대적 감사 / 환각 방지 / CRAG 프롬프트

이 절은 문서가 아니라 **프로젝트 운영 규칙** 이다.
LLM/에이전트/연구자 모두에게 강제한다.

### 12.1 Core anti-hallucination fence

```text
너는 절대 '관측량이 대충 맞는다'는 이유로 미구현 물리를 구현된 것으로 간주하지 마라.
다음 항목이 실제 코드/수식/테스트로 존재하지 않으면 존재한다고 쓰지 마라:

- exact electron-frame Thomson operator
- basis transport
- global tilt background constraint solver
- representation backend for the claimed Bianchi family
- family-specific perturbation IC
- TCA switch
- recombination/reionization source wiring
```

### 12.2 CRAG-forced search protocol

```text
외부 문헌/웹 서치가 필요한 모든 주장에 대해 다음 순서를 강제한다.

1. Claim decomposition:
   무엇을 사실 주장하는지 1문장씩 분리
2. Primary-source retrieval:
   review / original paper / code docs 우선
3. Adversarial retrieval:
   반례 또는 제한조건을 일부러 찾기
4. Evidence ledger:
   어떤 문장에 어떤 근거가 붙는지 기록
5. Uncertainty tag:
   확실/부분확실/미확실 명시
6. Doc update:
   근거가 없는 문장은 삭제하거나 '가정'으로 격하
```

### 12.3 mock-spectrum 금지 프롬프트

```text
다음 행위를 금지한다.

- underlying transport를 구현하지 않고 effective source를 임의로 조정해 low-\ell TT/EE만 맞추는 것
- global tilt와 observer boost를 자유롭게 섞어 anomaly를 설명하는 것
- family-specific spatial backend 없이 Type 이름만 바꿔 여러 Bianchi type을 지원한다고 주장하는 것
- hierarchy truncation 오차를 측정하지 않고 cutoff를 production으로 승격하는 것
```

### 12.4 local-minimum escape prompt

```text
현재 작업이 특정 파트 최적화에 갇혀 있는지 점검하라.
특히 아래 질문에 하나라도 '예'면 큰그림 점검으로 되돌아가라.

- geometry constraint residual이 해결되지 않았는데 런타임 최적화만 하고 있는가?
- collision convention이 freeze되지 않았는데 output plot tuning만 하고 있는가?
- perturbation IC provenance가 없는데 likelihood 인터페이스부터 만들고 있는가?
- family backend가 닫히지 않았는데 Type 이름만 늘리고 있는가?
```

### 12.5 adversarial audit loop

각 major PR 종료 후 아래 루프를 강제한다.

```text
[RE2 재독]
- 수식/표기/인덱스/부호 다시 읽기

[PHYS-MATH AUDIT]
- 제약식, limit, positivity, dimension, known recovery 점검

[CODE AUDIT]
- 입출력 contract, sparse layout, stiffness, edge case 점검

[RED TEAM]
- "이 구현이 실제로는 mock일 가능성"을 공격적으로 검토

[RELEASE DECISION]
- survive / revise / reject
```

### 12.6 survivor-only formalization rule

```text
검증을 통과하지 못한 수식/closure/backend는 절대 SSOT로 승격하지 마라.
형식화는 검증의 보상이지, 검증의 대체물이 아니다.
```

---

## 13. 최소 검증 매트릭스

### 13.1 background

- Type I orthogonal: exact Kasner/FLRW-adjacent regression
- Type I tilted: Codazzi-satisfying homogeneous tilt regression
- Type V or VII\(_h\): open-family curvature regression
- Type IX: closed-family curvature regression
- class B representative: III or IV or VI\(_h\)

### 13.2 transport/collision

- isotropic radiation \(\to\) polarization source zero
- quadrupole-only input \(\to\) expected polarization generation
- boost \(\to\) inverse boost identity
- basis rotation off/on \(\to\) \(E/B\) mixing 차이 확인

### 13.3 hierarchy

- TCA regime stable
- post-TCA free streaming stable
- neutrino anisotropic stress on/off difference
- global tilt on/off difference
- local observer boost only difference

### 13.4 backend

- I family plane-wave backend
- V family hyperbolic backend
- IX family Wigner \(D\) backend
- one intrinsically anisotropic family backend
- one class B general family backend

---

## 14. 문서 한 줄 결론

\[
\boxed{
\text{이 solver의 권위 경로는 }
\text{1+3 PSTF 설명 언어} + \text{tetrad/Lie-algebra 계산 엔진} + \text{exact electron-frame collision} + \text{family-specific spatial backend}
\text{ 이다.}
}
\]

\[
\boxed{
\text{모든 11개 Bianchi family는 동일한 algebra interface 위에서 다루되,}
\text{isotropic-limit family와 intrinsically anisotropic family의 IC/representation 규칙은 분리해야 한다.}
}
\]

\[
\boxed{
\text{global tilt는 background geometry/constraint 문제이고,}
\text{local boost는 출력/perturbation artifact 문제다. 둘을 섞으면 해석이 무너진다.}
}
\]
