# \((x,Q,\Pi,F,G)\) formalism 업그레이드: model-independent observatory framework와 local/global discrimination

**작성일**: 2026-04-20  
**대상**: 기존 \((x,Q,\Pi)\) departure formalism에 filling fraction \(F\)와 anisotropy/isotropy-gap variable \(G\)를 추가한 확장안  
**목표**: low-\(\ell\) solver 이후, 관측→후처리 통계량이 아니라 theory atlas ↔ observatory extraction ↔ model-dependent inference를 연결하는 재현 가능한 discrimination framework로 승격한다.

---

## 0. 압축 결론

기존 \((x,Q,\Pi)\) framework는 유지하되, 이제는 다음 다섯 층으로 재정의하는 것이 좋다.

\[
\boxed{
\mathbf B_C \longrightarrow x_C \longrightarrow Q_{C,U,N} \longrightarrow F_{S,C,U} \longrightarrow \Pi(q),G(z_a,z_b)
}
\]

여기서 핵심은 \(Q\)와 \(F\)를 같은 말로 쓰지 않는 것이다. \(Q\)는 denominator policy가 붙은 **normalized departure score**이고, \(F\)는 sign-clean sector와 admissible ceiling 조건이 만족될 때만 “filling fraction”이라는 물리적 해석을 허용받는 **certified occupancy variable**이다. 즉 기본 수식은 같아 보여도 semantic status가 다르다.

또한 \(G\)는 원고에서 가장 자연스럽게는

\[
\mathcal G_F(z_0,z_*) := \frac{F(z_0)}{F(z_*)}
\]

로 정의되는 **isotropy gap / anisotropy-filling evolution variable**이다. 이건 단순한 부가량이 아니라 local boost와 global tilt를 구분하는 데 필요한 시간축/깊이축 통계량이다. 단, “anisotropy budget 자체”는 \(G\)가 아니라 denominator \(U_C\) 또는 ceiling/budget policy로 따로 보존해야 한다. 표기상 혼동을 막기 위해 문서와 코드에서는 다음처럼 분리한다.

\[
U_C = \text{available anisotropy budget / ceiling},
\qquad
F = \frac{x^+}{U_C},
\qquad
G_F = \frac{F(z_a)}{F(z_b)}.
\]

최종적으로 이 framework는 다음 판별 문제까지 확장되어야 한다.

1. isotropy vs anisotropy: \(F,\Pi\)만으로는 부족하고, direction/BiPoSH/low-\(\ell\) morphology와 mock-calibrated FPR까지 요구한다.
2. local boost vs global tilt: \(F(z)\), \(G_F\), 방향 coherence, CMB–low-z cross-channel consistency가 핵심이다.
3. global tilt vs Bianchi geometry: scalar \(x,Q,F\)가 아니라 low-\(\ell\) solver가 주는 \(a_{\ell m}\), TE/EE/BB, BiPoSH, handedness, family atlas compatibility로만 올라갈 수 있다.

---

## 1. 표기 정리: 왜 \(F\)와 \(G\)를 다시 넣어야 하는가

### 1.1 기존 세 변수의 역할

현재 기본 구조는 다음이다.

\[
x_C
= \Sigma_{\rm std}^2
- W_{\rm std}^2
+ \Omega_{\rm tilt}
+ \Omega_{k,{\rm aniso}}^{(C)}.
\]

여기서 실제 원 객체는 scalar \(x_C\)가 아니라 departure bundle

\[
\mathbf B_C
=
\left(
\Sigma_{\rm std}^2,
W_{\rm std}^2,
\Omega_{\rm tilt},
\Omega_{k,{\rm aniso}}^{(C)}
\right)
\]

이고,

\[
x_C = a^T\mathbf B_C,
\qquad
 a=(1,-1,1,1)
\]

는 그 signed projection이다.

기존 세 변수는 다음 의미를 가진다.

| 변수 | 수학적 의미 | 안전한 해석 | 위험한 해석 |
|---|---|---|---|
| \(x_C\) | comparator-conditioned signed departure coordinate | exact algebraic bookkeeping coordinate | geometry invariant, direct observable |
| \(Q\) | \(x\)를 ceiling/budget scale로 나눈 normalized score | denominator-policy-dependent score | universal occupancy |
| \(\Pi(q)\) | \(P(Q>q)\) exceedance | threshold statistic | anisotropy truth probability |

이 구조는 좋지만, 두 가지가 빠져 있으면 논문 narrative가 흔들린다.

첫째, \(Q\)와 물리적 filling fraction \(F\)가 같은 것처럼 보인다. 원고는 이미 \(F_C\)의 sign-clean 조건을 명시하고 있는데, 코드/문서 layer에서 \(Q\)와 \(F\)가 섞이면 그 장점이 사라진다.

둘째, redshift/depth evolution을 나타내는 \(G\)가 빠지면 local boost와 global tilt를 나누는 핵심 축이 사라진다. \(z=0\) snapshot만으로는 local peculiar velocity와 cosmological tilt가 관측적으로 너무 쉽게 섞인다.

---

## 2. 확장된 다섯 변수의 권장 정의

### 2.1 \(x_C\): signed departure coordinate

\[
X_C[\mathbf B]
:=
\Sigma_{\rm std}^2
- W_{\rm std}^2
+ \Omega_{\rm tilt}
+ \Omega_{k,{\rm aniso}}^{(C)}.
\]

권장 표기에서는 소문자 \(x\)는 sample value, 대문자 \(X_C\)는 random variable 또는 state functional로 쓴다.

**Status**: exact state coordinate.  
**주의**: comparator, frame, sector label이 없으면 export 금지.

---

### 2.2 \(Q_{C,U,N}\): normalized departure score

\[
Q_{C,U,N}
:=
\frac{N(X_C)}{U_C}.
\]

여기서

- \(C\): comparator policy, 예: flat / matched / closed
- \(U_C\): denominator 또는 available budget / ceiling
- \(N\): numerator policy

이고 numerator policy는 최소 세 가지를 둔다.

\[
N_{\rm signed}(X)=X,
\qquad
N_{+}(X)=\max(X,0),
\qquad
N_{|\cdot|}(X)=|X|.
\]

권장 기본값은

\[
Q^{\rm lin}_{C}
:=
\frac{X_C^+}{x_{\max}^{\rm MES}}
\]

이다. 단 이때 status는 **linear-budget-normalised score**이지 theorem-backed occupancy가 아니다.

---

### 2.3 \(F_{S,C,U}\): certified filling fraction

\(F\)는 \(Q\)의 단순 별명이 아니다. \(F\)는 다음 조건이 통과될 때만 물리적 filling interpretation을 갖는 변수다.

\[
F_{S,C,U}
:=
\frac{X_C}{U_C}
\]

with certification conditions

\[
S = \text{irrotational non-negative sector},
\qquad
X_C\ge0,
\qquad
U_C>0,
\qquad
U_C\ge X_C
\]

and therefore

\[
0\le F_{S,C,U}\le 1.
\]

이 조건이 깨지면 \(F\)는 다음 중 하나로 내려가야 한다.

1. `invalid_filling_fraction`: filling interpretation 금지
2. `signed_saturation_coordinate`: \(F_C^\pm=X_C/|U_C|\), appendix-only diagnostic
3. `proxy_filling_score`: \(Q\)로 보고하되 occupancy language 금지

즉 코드와 원고에서 다음 규칙을 강제한다.

\[
\boxed{
F \Rightarrow \text{certified physical semantics},
\qquad
Q \Rightarrow \text{generic normalized score}.
}
\]

---

### 2.4 \(F_{\rm Bayes}\)와 \(F_{\rm MIO}\)

HTT posterior에서 나온 filling summary와 MIO measurement에서 나온 filling estimate는 반드시 이름을 분리한다.

HTT model-dependent posterior:

\[
F^{\rm HTT}_{T,C,U}
=F_{S,C,U}(\theta_T),
\qquad
F^{\rm Bayes}_{T,C,U}
:=
\mathbb E_{p_T(\theta\mid D)}[F_{S,C,U}(\theta)].
\]

MIO model-independent measurement law:

\[
\widehat F^{\rm MIO}_{C,U}
:=
\frac{\widehat X_C^+}{\widehat U_C},
\qquad
F^{\rm meas}_{C,U}
\sim
\nu_{\rm noise/mask/mock}.
\]

권장 output은 평균 하나가 아니라 다음 묶음이다.

\[
\mathcal F_{\rm report}
=
\left(
F_{\rm median},
F_{16},F_{84},
F_{2.5},F_{97.5},
F_{\rm Bayes},
P(F>0),
P(F>F_*)
\right).
\]

단 \(P(F>F_*)\)는 \(\Pi\)와 중복되므로, 실제 구현에서는 \(\Pi_F(q)\)로 통합하는 편이 좋다.

---

### 2.5 \(\Pi(q)\): exceedance curve

\[
\Pi_{C,U,N,\nu}(q)
:=
P_\nu\!\left(Q_{C,U,N}>q\right).
\]

\(F\)가 certified 상태일 때는

\[
\Pi_F(q)=P(F>q)
\]

라고 부를 수 있다. 그렇지 않으면 반드시 \(\Pi_Q(q)\)라고 부르고, filling language는 금지한다.

권장 summary는 threshold 하나가 아니라 curve 전체다.

\[
q\mapsto \Pi(q),
\qquad
q_{50}:=\sup\{q:\Pi(q)>0.5\},
\qquad
q_{95}:=\sup\{q:\Pi(q)>0.95\}.
\]

---

### 2.6 \(G\): anisotropy-filling gap / isotropy gap

원고의 자연스러운 \(G\)는 다음이다.

\[
\mathcal G_F(z_a,z_b)
:=
\frac{F(z_a)}{F(z_b)}.
\]

특히 현재 epoch와 기준 redshift \(z_*\) 사이에서는

\[
\boxed{
\mathcal G_F(0,z_*)
:=
\frac{F(0)}{F(z_*)}
}
\]

가 된다.

이 양의 의미는 “available anisotropy budget 그 자체”가 아니라 **occupied anisotropy fraction이 시간/깊이에 따라 얼마나 변했는가**다. 따라서 더 정확한 이름은 다음 중 하나다.

- isotropy gap
- anisotropy-filling growth factor
- budget-occupation gap
- redshift filling ratio

문서 표기는 다음을 권장한다.

\[
\boxed{
G \equiv \mathcal G_F
\quad\text{only for filling-ratio/gap quantities.}
}
\]

반면 denominator budget 자체는

\[
U_C(z),
\quad
x^{\rm MES}_{\max}(z),
\quad
U_{T,C}^{\rm atlas}(z),
\quad
U_{C}^{\rm NP}(z)
\]

로 써야 한다. \(G\)를 denominator로 쓰면 \(G_{\rm id}\), geometry frame \(G\), geometry norm \(\mathcal G_u\)와 표기 충돌이 난다.

---

## 3. \(F\)와 \(G\)의 확장/변형 제안

### 3.1 sector-conditioned \(F\)

\[
F_{S,C,U}
=
\frac{X_C}{U_C}
\quad
\text{valid only if}\quad
S\in\mathcal S_{\rm clean}.
\]

여기서

\[
\mathcal S_{\rm clean}
=
\{\text{irrotational, non-negative, admissible-ceiling sector}\}.
\]

코드에서는 `FillingFraction.status`를 다음처럼 둔다.

```text
certified_occupancy
linear_proxy_score
signed_saturation_diagnostic
invalid_negative_sector
invalid_vortical_sector
invalid_ceiling_not_admissible
```

이 status가 없으면 \(F\) artifact를 만들지 않는다.

---

### 3.2 component-resolved filling fraction

전체 \(F\)는 cancellation과 dominance를 숨길 수 있다. 따라서 component filling vector를 추가한다.

\[
\mathbf F_C
:=
\left(
F_\Sigma,
F_W,
F_{\rm tilt},
F_k
\right)
=
\frac{1}{U_C}
\left(
\Sigma^2,
-W^2,
\Omega_{\rm tilt},
\Omega_{k,{\rm aniso}}^{(C)}
\right).
\]

보고값은 다음이어야 한다.

\[
F_{\rm total}=\sum_i F_i,
\qquad
f_i=\frac{|F_i|}{\sum_j |F_j|},
\qquad
s_i={\rm sign}(F_i).
\]

특히 local/global discrimination에서는

\[
f_{\rm tilt}
=\frac{\Omega_{\rm tilt}}{\Sigma^2+W^2+\Omega_{\rm tilt}+|\Omega_k|}
\]

가 중요하다. \(f_{\rm tilt}\simeq1\)이면 tilt-dominated departure이고, \(f_\Sigma\) 또는 \(f_W\)가 크면 geometry-dominated 또는 vortical morphology를 의심해야 한다.

---

### 3.3 channel-conditioned filling fraction

관측 channel별로 response가 다르므로

\[
F^{(j)}_{C,U}
=
\frac{X^{(j),+}_C}{U_C^{(j)}}
\]

를 둔다. 여기서 \(j\)는 예를 들어

```text
TT_lowell, TE_lowell, EE_lowell, BB_lowell, BiPoSH, dipole, bulk_flow, depth_bin
```

이다.

이 양은 “전체 우주의 filling”이 아니라 “해당 channel이 요구하는 effective filling”이다. channel별 \(F\)가 서로 불일치하면 model failure 또는 unmodelled systematic 후보가 된다.

---

### 3.4 redshift-dependent \(F(z)\)

local boost와 global tilt를 나누려면 \(F(z)\)가 필수다.

\[
F(z)=\frac{X_C^+(z)}{U_C(z)}.
\]

권장 parameterization은 세 층으로 둔다.

1. nonparametric bins:

\[
F_i=F(z_i),
\qquad i=1,\ldots,N_z.
\]

2. smooth trend:

\[
\log F(z)=a_0+a_1\log(1+z)+a_2[\log(1+z)]^2.
\]

3. physics-motivated tilt models:

\[
\beta(z)=\beta_0,
\quad
\beta(z)=\beta_0(1+\alpha z),
\quad
\beta(z)=\beta_0e^{-z/z_d},
\quad
\beta(z)=\beta_0\left[1-\alpha\frac{z}{1+z}\right].
\]

\(F(z)\)는 \(\beta(z)^2\)에 민감하므로, uncertainty propagation은 linear error가 아니라 log-space 또는 sample-wise ratio로 해야 한다.

---

### 3.5 \(G_F\)의 robust 변형

단순 ratio

\[
G_F(z_a,z_b)=F(z_a)/F(z_b)
\]

는 \(F(z_b)\approx0\)에서 불안정하다. 따라서 세 가지 버전을 둔다.

#### A. ratio gap

\[
G_F^{\rm ratio}(z_a,z_b)
=
\frac{F(z_a)}{F(z_b)}.
\]

사용 조건: \(F(z_b)\)가 zero-compatible하지 않을 때.

#### B. log gap

\[
g_F(z_a,z_b)
=
\log\frac{F(z_a)+\epsilon_F}{F(z_b)+\epsilon_F}.
\]

사용 조건: plotting, regression, hypothesis testing.

#### C. difference gap

\[
\Delta F(z_a,z_b)=F(z_a)-F(z_b).
\]

사용 조건: denominator instability가 클 때.

권장 reporting은 세 개를 함께 내되, headline은 log gap으로 둔다.

\[
\boxed{
G\text{ headline} := g_F(0,z_*)
}
\]

ratio는 직관적이지만 수치적으로 약하고, difference는 안정적이지만 multiplicative growth 의미가 약하다.

---

### 3.6 budget scale \(U_C\)의 확장

\(G\)를 제대로 쓰려면 denominator \(U_C(z)\)도 고정되어야 한다. 가능한 budget scale은 다음 hierarchy로 둔다.

| budget scale | 정의 | status | 용도 |
|---|---|---|---|
| \(x_{\max}^{\rm MES}\) | 기존 MES linear ceiling | conditional | 기존 결과와 continuity |
| \(U_{T,C}^{\rm NP}\) | family-specific nonperturbative supremum | strong if solved | true occupancy 후보 |
| \(U_{\mathcal A,C}^{\rm atlas}\) | theory atlas envelope | solver-conditioned | model-independent atlas summary |
| \(U_{C,\alpha}^{\rm CMB}\) | CMB-only budget quantile | conservative | observation-driven ceiling |
| \(U_{j,C}\) | channel-specific effective budget | diagnostic | channel tension |

low-\(\ell\) solver 이후에는 \(x_{\max}^{\rm MES}\)만 쓰는 것이 약하다. 최소한 \(U^{\rm atlas}\)와 \(U^{\rm CMB}\)를 병행해서 denominator sensitivity를 figure로 보여줘야 한다.

---

## 4. 확장된 reporting object

최종 artifact는 scalar tuple이 아니라 다음이어야 한다.

\[
\mathcal R(D)
=
\left(
\widehat{\mathbf B}_C,
\widehat X_C,
Q_{C,U,N},
F_{S,C,U},
\Pi_{C,U,N,\nu}(q),
G_F(z_a,z_b),
\mathcal C_{\rm dir},
\mathcal A_{\rm atlas},
\mathcal I_{\rm id}
\right).
\]

각 항목의 의미는 다음과 같다.

| 항목 | 의미 | owner |
|---|---|---|
| \(\widehat{\mathbf B}_C\) | departure component bundle | MIO/HTT, semantics separated |
| \(\widehat X_C\) | signed scalar coordinate | MIO/HTT |
| \(Q\) | normalized score | MIO/HTT |
| \(F\) | certified filling fraction | MIO/HTT, with status |
| \(\Pi\) | exceedance curve | MIO measurement or HTT posterior |
| \(G_F\) | redshift/depth filling gap | MIO/HTT |
| \(\mathcal C_{\rm dir}\) | directional coherence | MIO |
| \(\mathcal A_{\rm atlas}\) | solver atlas compatibility | BASS/MIO/HTT bridge |
| \(\mathcal I_{\rm id}\) | identifiability gate | common/reporting |

절대 금지할 것:

\[
\text{single headline score}=x+Q+F+\Pi+G.
\]

이 다섯 변수는 같은 층위가 아니다. 한 점수로 합치면 논리적 장점이 사라진다.

---

## 5. isotropy/anistropy discrimination framework

### 5.1 판별할 가설군

최소 가설군은 다음처럼 둔다.

\[
\mathcal H_0:
\text{FLRW isotropic sky + local boost + survey systematics}.
\]

\[
\mathcal H_{\rm LB}:
\text{FLRW + local peculiar velocity / local bulk flow only}.
\]

\[
\mathcal H_{\rm GT}:
\text{global matter-frame tilt relative to geometry frame}.
\]

\[
\mathcal H_{\rm BG}:
\text{Bianchi geometric anisotropy: shear/vorticity/curvature morphology}.
\]

\[
\mathcal H_{\rm mix}:
\text{local boost + global tilt + survey contamination mixture}.
\]

핵심은 \(\mathcal H_{\rm aniso}\)를 하나로 두지 않는 것이다. “anisotropy detected”와 “Bianchi geometry identified”는 다른 claim이다.

---

### 5.2 isotropy rejection은 세 단계로 분리

#### Stage I — amplitude departure

\[
F>0,
\qquad
\Pi_F(q_*)\text{ large},
\qquad
X_C\neq0.
\]

의미: FLRW comparator에서 departure가 필요하다는 scalar-level evidence.

한계: local boost, tilt, geometry, systematics를 구분하지 못한다.

#### Stage II — directional coherence

\[
\mathcal C_{\rm dir}
=
\left\|
\sum_j w_j\hat n_j
\right\|.
\]

여기서 \(j\)는 CMB dipole, CatWISE, radio dipole, CF4 bulk flow, low-\(\ell\) axis, BiPoSH axis, depth-bin axes 등이다.

의미: 여러 독립 channel이 같은 방향을 요구하는가.

한계: common survey systematic도 방향 coherence를 만들 수 있다.

#### Stage III — morphology / atlas compatibility

\[
\Delta_T^2
=
\min_{\theta\in\Theta_T}
\left(\widehat{\mathcal O}-\mathcal O_T(\theta)\right)^T
C_{\mathcal O}^{-1}
\left(\widehat{\mathcal O}-\mathcal O_T(\theta)\right).
\]

여기서

\[
\mathcal O
=
\left(
C_\ell^{TT,TE,EE,BB},
D_\ell,
a_{\ell m}^{T,E},
A_{\ell_1\ell_2}^{LM},
\hat n(z),
\text{depth tomography}
\right).
\]

의미: scalar amplitude가 아니라 full low-\(\ell\) morphology가 어떤 theory family와 맞는가.

한계: solver atlas coverage, mask response, covariance model에 의존한다.

---

### 5.3 claim tiers

권장 claim tier는 다음과 같다.

| Tier | claim | 필요한 조건 |
|---|---|---|
| C0 | no claim | \(F\) invalid 또는 \(\Pi\) inconclusive |
| C1 | scalar departure | \(F\) certified, \(\Pi_F(q_*)\) high |
| C2 | anisotropy-like coherence | C1 + directional coherence + null mock FPR 통과 |
| C3 | global tilt candidate | C2 + redshift/depth \(G_F\)가 local boost와 불일치 + HTT tilt evidence |
| C4 | Bianchi geometry candidate | C3 + low-\(\ell\) solver morphology/BiPoSH/TE/EE compatibility |
| C5 | family identification | C4 + scalar equivalence class broken + FPR below threshold + PPC/LOOCV 통과 |

현재 scalar \((x,Q,\Pi,F)\)만으로는 C1 이상을 단정하기 어렵다. \(G\), direction, morphology가 들어가야 C2/C3로 올라간다. Bianchi family claim은 반드시 C4/C5에서만 허용한다.

---

## 6. local boost vs global tilt discrimination

### 6.1 관측 dipole의 분해

관측 dipole 또는 bulk-flow-like signal은 다음처럼 분해해서 모델링한다.

\[
\mathbf d_{\rm obs}(z,\lambda)
=
\mathbf d_{\rm LB}(z,\lambda)
+
\mathbf d_{\rm GT}(z,\lambda)
+
\mathbf d_{\rm BG}(z,\lambda)
+
\mathbf d_{\rm sys}(z,\lambda)
+
\epsilon.
\]

- LB: local boost / peculiar velocity / local structure
- GT: global tilt, matter frame vs geometry frame
- BG: Bianchi geometric anisotropy, shear/vorticity/curvature morphology
- sys: survey mask, selection, calibration, foreground, scanning law

이 분해를 하지 않으면 “dipole excess = global tilt”로 과도하게 읽히기 쉽다.

---

### 6.2 local boost signature

local boost가 주된 원인이라면 기대되는 패턴은 다음이다.

1. low-z에서 강하고, 깊이가 증가하면 LSS contribution 또는 peculiar-flow contribution이 약해진다.
2. CMB aberration/modulation과 호환되는 kinematic pattern이 우선한다.
3. \(F(z)\) 또는 \(G_F\)가 global cosmological growth law와 맞지 않는다.
4. BiPoSH 또는 Bianchi-specific low-\(\ell\) morphology가 약하거나 local correction으로 설명된다.
5. survey null families, 특히 mask leakage / scanning law / selection response와 경쟁해야 한다.

Local boost adequacy statistic:

\[
A_{\rm LB}
=
\chi^2_{\rm null+boost}-\chi^2_{\rm null}.
\]

그리고 global tilt를 주장하려면

\[
\Delta\chi^2_{\rm GT-LB}
=
\chi^2_{\rm LB}-\chi^2_{\rm GT}
\]

만으로는 부족하고, mock-calibrated FPR와 depth trend까지 통과해야 한다.

---

### 6.3 global tilt signature

global tilt라면 다음이 보여야 한다.

1. \(\Omega_{\rm tilt}\) component가 \(x\) 또는 \(F\)를 지배한다.
2. \(F(z)\)가 local-flow damping이 아니라 cosmological tilt evolution law와 호환된다.
3. \(G_F(0,z_*)\)가 local boost-only mock distribution의 tail에 놓인다.
4. CMB dipole, number-count dipole, bulk-flow direction, low-\(\ell\) axis 사이에 방향 coherence가 있다.
5. BASS low-\(\ell\) solver가 예측하는 TE/EE/BiPoSH residual과 모순되지 않는다.

Global tilt score는 단일 Bayes factor가 아니라 다음 tuple로 보고한다.

\[
\mathcal D_{\rm GT}
=
\left(
F_{\rm tilt},
G_F,
\mathcal C_{\rm dir},
\Delta\chi^2_{\rm GT-LB},
{\rm FPR}_{\rm null},
\Delta_{\rm atlas}^{\rm tilt}
\right).
\]

---

### 6.4 Bianchi geometry signature

Bianchi geometry claim은 global tilt보다 훨씬 강한 요구조건을 가져야 한다.

필수 조건:

1. scalar amplitude: \(F\), \(\Pi_F\)가 nonzero departure를 지지한다.
2. geometry component: \(F_\Sigma\), \(F_W\), 또는 \(F_k\)가 식별 가능해야 한다.
3. direction-inclusive morphology: \(a_{\ell m}\), TE/EE, BiPoSH, parity/handedness가 family template와 맞아야 한다.
4. equivalence class breaking: scalar-equivalent family들이 directional observable에서 갈라져야 한다.
5. local boost and survey nulls fail: local-only model과 systematic families가 posterior predictive 또는 mock calibration에서 실패해야 한다.

따라서 \(x,Q,F,\Pi\)는 Bianchi detection의 입구이지 결론이 아니다.

---

## 7. low-\(\ell\) solver 이후 framework 확장

### 7.1 theory atlas entry

각 Bianchi family \(T\)와 parameter \(\theta\)에 대해 다음을 저장한다.

```python
AtlasEntry = {
    "family_id": T,
    "theta": theta,
    "comparator": C,
    "departure_bundle": B_C(theta),
    "x": X_C(theta),
    "q_scores": {policy: Q_policy(theta)},
    "filling_fraction": F_status_and_value(theta),
    "redshift_filling": F_z(theta, z_grid),
    "gap_G": G_F(theta, z_pairs),
    "cl": {"TT": ..., "TE": ..., "EE": ..., "BB": ...},
    "alm": {"T": ..., "E": ...},
    "biposh": ...,
    "directional_axes": ...,
    "source_adequacy": ...,
    "propagation_adequacy": ...,
    "claim_tier": ...,
}
```

이렇게 하면 \((x,Q,F,\Pi,G)\)가 theory-side prediction coordinate로도 작동한다.

---

### 7.2 two-sided comparison

기존 one-way pipeline:

\[
D_{\rm obs}\to p(\theta\mid D,T)\to p(x,Q,\Pi\mid D,T).
\]

업그레이드 후 two-sided pipeline:

\[
\text{Theory path:}\quad
\theta_T
\xrightarrow{\rm BASS}
\mathcal O_T(\theta_T),\mathbf B_T,x_T,Q_T,F_T,G_T.
\]

\[
\text{Observatory path:}\quad
D_{\rm obs}
\xrightarrow{\rm MIO}
\widehat{\mathcal O},\widehat{\mathbf B},\widehat x,\widehat Q,\widehat F,\widehat G.
\]

\[
\text{Inference path:}\quad
D_{\rm obs},\mathcal A_T
\xrightarrow{\rm HTT}
 p_T(\theta\mid D),\ln\mathcal B_T,\Pi_T(q),F^{\rm Bayes}_T,G_T^{\rm Bayes}.
\]

이 세 경로가 서로 다른 artifact를 만들고, 마지막에 cross-check table만 공유한다. MIO certificate를 HTT likelihood term으로 더하면 안 된다.

---

### 7.3 solver-calibrated \(U\), \(F\), \(G\)

low-\(\ell\) solver 이후 가장 중요한 새 연구는 denominator calibration이다.

\[
U_{T,C}^{\rm atlas}(z)
=
\operatorname{Quantile}_\alpha
\left\{
X_C^+(\theta,z):
\theta\in\Theta_T,
\mathcal O_T(\theta)\text{ passes low-}\ell\text{ constraints}
\right\}.
\]

그 다음

\[
F_{T,C}^{\rm atlas}(z)
=
\frac{X_C^+(z)}{U_{T,C}^{\rm atlas}(z)},
\qquad
G_{T,C}^{\rm atlas}(z_a,z_b)
=
\frac{F_{T,C}^{\rm atlas}(z_a)}{F_{T,C}^{\rm atlas}(z_b)}.
\]

연구 질문:

1. MES linear ceiling과 solver atlas ceiling이 같은가?
2. \(F\)의 값이 denominator policy에 얼마나 민감한가?
3. \(G_F\)가 local boost-only mocks에서 얼마나 자주 가짜로 생기는가?
4. 어떤 Bianchi family가 같은 \(F\)를 만들지만 다른 \(G\) 또는 BiPoSH morphology를 만드는가?
5. \(F\)-equivalence class를 깨는 최소 observable set은 무엇인가?

---

## 8. statistical model redesign

### 8.1 joint hierarchical model

관측 channel \(j\), redshift bin \(b\), sky mode \(m\)에 대해

\[
Y_{jbm}
=
R_{jbm}\!ig(\mathbf B_C(z_b),\alpha_{\rm dir},\psi_j\big)
+
L_{jbm}(\mathbf v_{\rm local})
+S_{jbm}(\eta_{\rm sys})
+\epsilon_{jbm}.
\]

여기서

- \(R\): global tilt / geometry response
- \(L\): local boost / local structure response
- \(S\): survey systematic response
- \(\psi_j\): channel nuisance
- \(\eta_{\rm sys}\): null-family nuisance

\(F\)와 \(G\)는 primitive parameter가 아니라 posterior/generated functional이다.

\[
F_b=F(\mathbf B_C(z_b),U_C(z_b)),
\qquad
G_{ab}=F_a/F_b.
\]

---

### 8.2 model-independent MIO version

MIO는 posterior를 만들지 않고 constrained estimator를 만든다.

\[
\widehat{\mathbf B}(z)
=
\arg\min_{\mathbf B,\psi}
\left[
(Y-R\mathbf B-L\widehat{\mathbf v}_{\rm local}-S\widehat\eta)^T
C^{-1}
(Y-R\mathbf B-L\widehat{\mathbf v}_{\rm local}-S\widehat\eta)
+\lambda\mathcal R(\mathbf B)
\right].
\]

그리고 mock/bootstrap으로

\[
\nu_{\rm MIO}
=\mathcal L\left(\widehat{\mathbf B},\widehat X,\widehat Q,\widehat F,\widehat G\right)
\]

를 생성한다. 이건 posterior가 아니라 measurement law다.

---

### 8.3 HTT model-dependent version

HTT는 theory atlas likelihood를 쓴다.

\[
\ln\mathcal L_T
=
-\frac12
(\mathcal O_{\rm obs}-\mathcal O_T(\theta)-\mathcal O_{\rm LB}(v)-\mathcal O_{\rm sys}(\eta))^T
C^{-1}
(\mathcal O_{\rm obs}-\mathcal O_T(\theta)-\mathcal O_{\rm LB}(v)-\mathcal O_{\rm sys}(\eta)).
\]

그 다음 pushforward:

\[
p_T(F,G,Q,x\mid D)=
(F,G,Q,x)_\#p_T(\theta,v,\eta\mid D).
\]

HTT output에는 반드시 다음 model comparison이 들어가야 한다.

\[
\ln\mathcal B(\mathcal H_{\rm GT}:\mathcal H_{\rm LB}),
\quad
\ln\mathcal B(\mathcal H_{\rm BG}:\mathcal H_{\rm GT}),
\quad
\ln\mathcal B(\mathcal H_{\rm mix}:\mathcal H_{\rm LB}).
\]

---

### 8.4 local/global mixture model

가장 현실적인 production model은 mixture다.

\[
\mathbf d_{\rm obs}(z)
=
(1-\lambda_z)\mathbf d_{\rm LB}(z)
+
\lambda_z\mathbf d_{\rm GT}(z)
+
\mathbf d_{\rm sys}(z)
+\epsilon.
\]

여기서 \(\lambda_z\in[0,1]\)는 global fraction이다. 이를 통해

\[
F_{\rm global}(z)=\lambda_z F(z),
\qquad
F_{\rm local}(z)=(1-\lambda_z)F(z).
\]

를 정의한다.

local/global discrimination의 핵심 통계량:

\[
\Lambda_{\rm glob}
:=P(\lambda_z>1/2\mid D),
\qquad
G_{\lambda}(z_a,z_b)=\frac{\lambda_{z_a}}{\lambda_{z_b}}.
\]

단 \(\lambda_z\)는 HTT posterior object다. MIO에서는 \(\widehat\lambda_z\)를 regularized estimate로만 보고해야 한다.

---

## 9. concrete code design

### 9.1 common contracts

파일:

```text
src/common/departure_contracts.py
```

권장 dataclass:

```python
from dataclasses import dataclass
from typing import Dict, Literal, Optional, Tuple
import numpy as np

ComparatorPolicy = Literal["flat", "matched", "closed", "custom"]
NumeratorPolicy = Literal["signed", "positive_part", "absolute"]
CeilingKind = Literal[
    "linear_MES", "family_NP", "atlas_envelope", "cmb_quantile", "channel_effective", "custom"
]
UncertaintyKind = Literal[
    "htt_posterior", "mio_measurement", "bootstrap", "mock_calibrated", "profile_likelihood"
]
FillingStatus = Literal[
    "certified_occupancy",
    "linear_proxy_score",
    "signed_saturation_diagnostic",
    "invalid_negative_sector",
    "invalid_vortical_sector",
    "invalid_ceiling_not_admissible",
]
GapKind = Literal["ratio", "log", "difference"]

@dataclass(frozen=True)
class DepartureBundle:
    comparator: ComparatorPolicy
    Sigma2_std: float
    W2_std: float
    Omega_tilt: float
    Omega_k_aniso: float
    covariance: Optional[np.ndarray]
    frame_convention: str
    sector: str
    provenance: Dict[str, str]

    @property
    def x_signed(self) -> float:
        return self.Sigma2_std - self.W2_std + self.Omega_tilt + self.Omega_k_aniso

    @property
    def x_positive(self) -> float:
        return max(self.x_signed, 0.0)

@dataclass(frozen=True)
class BudgetSpec:
    kind: CeilingKind
    value: float
    uncertainty: Optional[float]
    family_id: Optional[str]
    channel: Optional[str]
    redshift: Optional[float]
    confidence_level: Optional[float]
    assumptions: Tuple[str, ...]
    is_admissible_ceiling: bool

@dataclass(frozen=True)
class NormalizedScore:
    q_value: float
    x_value: float
    numerator_policy: NumeratorPolicy
    budget: BudgetSpec
    comparator: ComparatorPolicy
    status: str

@dataclass(frozen=True)
class FillingFraction:
    value: Optional[float]
    status: FillingStatus
    score_if_invalid: Optional[float]
    comparator: ComparatorPolicy
    budget: BudgetSpec
    sector: str
    redshift: Optional[float]
    component_breakdown: Dict[str, float]
    provenance: Dict[str, str]

@dataclass(frozen=True)
class ExceedanceCurve:
    q_grid: np.ndarray
    pi_grid: np.ndarray
    uncertainty_kind: UncertaintyKind
    target: Literal["Q", "F"]
    threshold_labels: Dict[str, float]
    q50: float
    q95: float
    provenance: Dict[str, str]

@dataclass(frozen=True)
class IsotropyGap:
    value: Optional[float]
    kind: GapKind
    z_a: float
    z_b: float
    F_a: FillingFraction
    F_b: FillingFraction
    epsilon_floor: float
    status: str
    uncertainty_kind: UncertaintyKind
    provenance: Dict[str, str]
```

---

### 9.2 MIO modules

```text
src/mio/formalism/
  departure_bundle.py
  budget_spec.py
  normalized_score.py
  filling_fraction.py
  isotropy_gap.py
  exceedance.py
  component_breakdown.py
  channel_filling.py
  local_global_discrimination.py
  atlas_compatibility.py
```

필수 함수:

```python
def compute_filling_fraction(bundle, budget, *, require_certified=True) -> FillingFraction:
    ...


def compute_filling_samples(x_samples, budget_samples, sectors, policy) -> list[FillingFraction]:
    ...


def compute_isotropy_gap(F_a, F_b, *, kind="log", epsilon_floor=1e-12) -> IsotropyGap:
    ...


def component_filling_vector(bundle, budget) -> dict[str, float]:
    ...


def local_global_discrimination_report(obs, local_model, global_model, null_mocks) -> dict:
    ...
```

---

### 9.3 HTT modules

```text
src/htt/departure/
  posterior_pushforward.py
  filling_posterior.py
  gap_posterior.py
  local_global_mixture.py
  theory_atlas_likelihood.py
  discrimination_evidence.py
```

필수 함수:

```python
def pushforward_F_G(samples, weights, model_family, comparator, budget_policy, z_grid):
    """Return posterior samples for F(z), G(z_a,z_b), Pi_F(q)."""


def compare_local_boost_global_tilt(data, atlas, local_nulls, config):
    """Return BF/LOOCV/PPC tuple for LB vs GT vs BG vs mixture."""


def scalar_equivalence_breaking_report(atlas_entries, observables, covariance):
    """Find families with same x/Q/F but different morphology."""
```

---

### 9.4 BASS atlas modules

```text
src/bass/atlas/
  atlas_entry.py
  family_grid.py
  lowell_observable_export.py
  budget_ceiling_optimizer.py
  redshift_filling_export.py
  morphology_signature.py
```

`AtlasEntry`에 추가할 fields:

```python
filling_fraction: dict[str, FillingFraction]
redshift_filling: dict[float, FillingFraction]
isotropy_gaps: dict[tuple[float, float], IsotropyGap]
component_filling: dict[str, float]
local_global_signature: dict[str, float]
```

---

## 10. 필수 tests

### 10.1 \(F\) semantics tests

```text
test_F_equals_Q_only_in_certified_sector
test_negative_x_blocks_filling_language
test_vortical_sector_blocks_filling_language
test_nonadmissible_ceiling_blocks_F_certification
test_signed_saturation_is_appendix_only
test_F_Bayes_is_sample_mean_not_ratio_of_means
test_component_filling_sums_to_total_signed_F
test_F_report_contains_status_and_budget_kind
```

### 10.2 \(G\) tests

```text
test_G_ratio_matches_F_ratio_when_denominator_nonzero
test_G_log_uses_epsilon_floor
test_G_difference_stable_near_zero_F
test_G_rejects_invalid_F_unless_allow_proxy_true
test_G_records_redshift_pair_and_uncertainty_kind
test_local_boost_mock_G_distribution_available
test_global_tilt_injected_G_recovered_with_coverage
```

### 10.3 discrimination tests

```text
test_scalar_departure_does_not_trigger_geometry_claim
test_directional_coherence_requires_null_mock_FPR
test_local_boost_model_can_absorb_pure_kinematic_dipole
test_global_tilt_claim_requires_depth_trend
test_bianchi_geometry_claim_requires_morphology_signature
test_mio_certificate_not_used_as_htt_likelihood
test_atlas_entry_not_empirical_data
test_equivalence_class_breaking_requires_directional_observable
```

---

## 11. manuscript patch plan

### ch03 Framework

추가할 절:

```text
§3.X Five-layer departure formalism: x, Q, F, Pi, G
§3.X+1 Q versus F: normalized score vs certified filling fraction
§3.X+2 Budget scale U and why G is not the denominator
§3.X+3 Redshift filling gap G_F and local/global discrimination
§3.X+4 Claim tiers from scalar departure to geometry identification
```

핵심 문장:

> The filling fraction is not an additional invariant beyond \(Q\); it is the sector-certified semantic promotion of a normalized score. The gap variable \(G_F\), by contrast, is genuinely new information: it tracks the redshift evolution of the occupied anisotropy budget and is therefore essential for separating local boost contamination from global tilt.

---

### ch07 Results

기존 filling section은 다음처럼 재구성한다.

```text
§7.X Normalized score Q_lin
§7.X+1 Certified filling fraction F
§7.X+2 F_Bayes and measurement filling estimates
§7.X+3 Redshift filling F(z)
§7.X+4 Isotropy gap G_F
§7.X+5 Local boost vs global tilt discrimination using F(z), G_F, and directional coherence
```

Figure 변경:

- `fig_filling_fraction_posterior` → \(F\) status panel 추가
- `fig_filling_z_evolution` → ratio \(G\), log gap \(g_F\), local boost mock band 추가
- `fig_departure_summary` → \(Q\)와 \(F\)를 분리: score panel vs certified filling panel

---

### ch08 Robustness

추가할 robustness checks:

1. denominator policy: MES vs atlas vs CMB quantile
2. \(F\) certification status under comparator changes
3. \(G\) denominator instability / epsilon floor sensitivity
4. local boost-only mock distribution for \(G\)
5. global tilt injection recovery
6. survey-null induced false \(G\) trend
7. direction + depth combined FPR

---

### ch09 Discussion

해석 문장을 다음 hierarchy로 고친다.

1. \(F\ll1\): universe remains close to FLRW under the chosen ceiling.
2. \(F>0\): scalar departure if anomaly is physical.
3. \(G_F\neq1\): possible evolution of occupied anisotropy budget, but local boost/systematics must be ruled out.
4. direction coherence: anisotropy-like signal, not geometry identification.
5. low-\(\ell\) morphology: only route to Bianchi family claim.

---

### ch12 MIO Observatory Results

권장 구조:

```text
§12.1 Direct MIO extraction of B_C and X_C
§12.2 Q as policy-normalized score
§12.3 F as certified filling fraction
§12.4 Redshift filling F(z) and gap G_F
§12.5 Local boost vs global tilt MIO diagnostics
§12.6 BASS atlas compatibility and geometry claim gate
§12.7 HTT posterior cross-check: same variables, different semantics
```

---

## 12. research programme after low-\(\ell\) solver

### R1. solver-calibrated filling fraction

목표:

\[
F^{\rm MES},
\quad
F^{\rm atlas},
\quad
F^{\rm CMB-quantile}
\]

를 같은 data와 같은 theory atlas에서 비교한다.

산출물:

```text
filling_policy_comparison.json
fig_F_denominator_sensitivity.pdf
table_F_status_by_model.tex
```

---

### R2. redshift gap discrimination

목표:

\[
G_F^{\rm obs}
\]

가 local boost-only null에서 얼마나 자주 생기는지 mock으로 측정한다.

산출물:

```text
gap_local_boost_null_mocks.h5
fig_G_local_vs_global.pdf
table_G_FPR_by_depth_bin.tex
```

---

### R3. scalar-equivalence breaking

목표:

\[
T\sim_F T'
\quad\text{but}\quad
T\not\sim_{\rm morphology}T'
\]

인 family pair를 찾는다.

산출물:

```text
scalar_equivalence_classes.json
morphology_breaking_matrix.csv
fig_equivalence_breaking_biposh.pdf
```

---

### R4. local/global mixture posterior

목표:

\[
\lambda_z
\]

를 도입해 signal의 local fraction과 global fraction을 분리한다.

산출물:

```text
local_global_mixture_posterior.npz
fig_lambda_z_depth.pdf
table_BF_LB_GT_BG_mix.tex
```

---

### R5. component filling anatomy

목표:

\[
\mathbf F_C=(F_\Sigma,F_W,F_{\rm tilt},F_k)
\]

를 model family와 redshift별로 산출한다.

산출물:

```text
component_filling_by_model.json
fig_component_filling_stack.pdf
table_tilt_fraction_by_family.tex
```

---

## 13. final recommended notation

최종 notation은 다음으로 고정하는 것을 권한다.

\[
\boxed{
X_C=a^T\mathbf B_C
}
\]

\[
\boxed{
Q_{C,U,N}=\frac{N(X_C)}{U_C}
}
\]

\[
\boxed{
F_{S,C,U}=\frac{X_C}{U_C}
\quad
\text{only if certified in sector }S
}
\]

\[
\boxed{
\Pi_{C,U,N,\nu}(q)=P_\nu(Q_{C,U,N}>q)
}
\]

\[
\boxed{
G_F(z_a,z_b)=\frac{F(z_a)}{F(z_b)},
\qquad
g_F(z_a,z_b)=\log\frac{F(z_a)+\epsilon_F}{F(z_b)+\epsilon_F}
}
\]

그리고 다음 naming rule을 코드/문서에 강제한다.

| symbol | allowed meaning | forbidden meaning |
|---|---|---|
| \(x\) or \(X_C\) | signed departure coordinate | direct observable geometry detector |
| \(Q\) | normalized score | certified filling fraction |
| \(F\) | certified filling fraction | generic ratio in invalid sector |
| \(\Pi\) | exceedance curve | truth probability |
| \(G_F\) | redshift/depth filling gap | denominator budget itself |
| \(U_C\) | ceiling / available budget | posterior probability |

---

## 14. 가장 중요한 수정 포인트

1. \(F\)는 \(Q\)와 같은 산식에서 나오더라도 같은 변수가 아니다. \(F\)는 semantic promotion이고, sector certification이 필요하다.
2. \(G\)는 denominator budget이 아니라 \(F\)의 redshift/depth evolution을 나타내는 gap variable로 쓰는 것이 가장 안전하다.
3. \(F\)와 \(G\)가 들어가면 local boost/global tilt 판별력이 생긴다. \(x,Q,\Pi\) snapshot만으로는 이 판별이 약하다.
4. isotropy rejection은 \(F\)와 \(\Pi\)로 시작할 수 있지만, anisotropic geometry claim은 direction/BiPoSH/low-\(\ell\) morphology 없이는 금지해야 한다.
5. low-\(\ell\) solver는 \(U\), \(F\), \(G\)를 theory-side에서도 계산하게 해주므로, 이제 framework는 관측 후처리 layer가 아니라 theory atlas와 직접 연결된 model-independent observatory coordinate system이 될 수 있다.

최종 headline 문장은 다음이 가장 안전하다.

> We use \((x,Q,F,\Pi,G)\) not as a single anisotropy detector, but as a comparator-explicit, budget-explicit, sector-certified coordinate system for separating scalar departure, certified budget filling, exceedance support, redshift evolution, and morphology-based geometry identification.

