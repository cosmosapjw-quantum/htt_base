# 추가 증명 가능한 정리 후보 (T1–T9)

각 후보는 (진술 — 증명 스케치 — 난이도 — 프로그램 내 역할 — 수치 검증 훅) 형식이다. T1/T2/T4/T5/T8은 현 보고서의 기법만으로 완결 증명이 가능하고, T3/T6은 표준 GR/조화해석 재료가 추가로 필요하며, T7/T9는 문헌 정리의 이식이다. LaTeX 진술은 v7 본문에 그대로 넣을 수 있는 형태로 작성했다.

---

## T1. 부호 있는 널-박스에 대한 식별구간 (P26의 양측 일반화)

**진술.**
```latex
\begin{theorem}[Signed-box partial-identification interval]
Let ${\cal G}(y)$ be the feasible set of \S3.3 with null columns of $R$,
${\cal C}_{\rm phys}=\{\bm g:\ g_\Sigma,g_W,g_t\ge0\}\times\R_{(k)}$, and
signed ceiling boxes $g_j\in[L_j,U_j]$ ($L_j\le0\le U_j$ allowed) on the
null components.  If ${\cal G}(y)\ne\emptyset$, the image
$\{c^T\bm g\}$ is the closed interval with endpoints
\[
x_C^\pm=\Bigl(\hbox{extremes of }c_R^T\bm g_R\Bigr)
+\sum_{j\in{\rm null}}
{\textstyle\bigl[\min(c_jL_j,c_jU_j),\ \max(c_jL_j,c_jU_j)\bigr]}^{\mp},
\]
and the one-sided case $L_j=0$ recovers P26.  In particular a two-sided
curvature box $|\Omega_{k,\rm aniso}|\le U_k$ moves the LOWER endpoint by
$-U_k$ relative to the one-sided declaration.
\end{theorem}
```
**증명 스케치.** P26과 동일: 볼록성 + 선형 함수 상 구간; 널 방향 인수분해; 박스 끝점에서의 극값은 \(c_j\) 부호에 따라 \(c_jL_j\) 또는 \(c_jU_j\). 새 내용은 부호 있는 박스의 min/max 정리(one-liner)뿐이므로 완결 증명 난이도는 낮다.
**난이도**: 하. **역할**: F1(치명 결함)의 수리 그 자체. **검증 훅**: exp02 (하한 0.11→0.09, 끝점 attainment 확인 완료).

---

## T2. Joint-대-naive 구간의 엄격성 판별 정리 (P36 교정)

**진술.**
```latex
\begin{theorem}[Strictness criterion for the joint depth-gap interval]
In the setting of P36 with box ${\cal S}=\prod_j[s_j^-,s_j^+]$ and $D>0$
on the feasible set, the joint and naive upper endpoints coincide iff the
set $\arg\max_{s}\,c_N\!\cdot\!s\ \cap\ \arg\min_{s}\,c_D\!\cdot\!s$ is
nonempty, which for a box holds iff $c_{N,j}\,c_{D,j}\le0$ for every $j$
with a nondegenerate interval (aligned regime).  Hence the inclusion of
P36 is strict at the upper endpoint iff some shared component competes,
$c_{N,j}c_{D,j}>0$ with $s_j^-<s_j^+$; the lower endpoint is analogous
with $\arg\min c_N\cdot s\cap\arg\max c_D\cdot s$.
\end{theorem}
```
**증명 스케치.** (⇐ 일치) 정렬 레짐이면 성분별로 \(c_{N,j}>0 \Rightarrow c_{D,j}\le 0\)이므로 \(s_j=s_j^+\)가 분자 최대·분모 최소를 동시에 달성(반대 부호도 대칭). 공통 최적점 \(s^\*\)에서 naive 상한 = joint 상한. (⇒ 엄격) 경쟁 성분 \(j\)가 있으면 naive는 분자에 \(s_j^+\), 분모에 \(s_j^-\)를 따로 쓰지만 joint는 하나의 \(s_j\)만 허용; 분수의 단조성으로 상한이 진성으로 작아짐. 박스 구조 덕에 argmax/argmin이 성분별로 분리된다는 사실만 쓰면 된다.
**난이도**: 하. **역할**: M1 수리; DER 등급 항목의 신뢰 회복. **검증 훅**: exp04 (정렬 레짐 등식 재현, 교정 기준 예측 일치 93/94 — 나머지 1건은 수치 허용오차 경계 사례).

---

## T3. 박스 극점의 제약-적합성 (P31 승격용 보조정리)

**진술.**
```latex
\begin{lemma}[Constraint compatibility of ceiling-box extremes]
Fix reachable values $(\Sigma^2,\Omega_t)$ with $w>-1$ and any null-box
values $(W^2,\Omega_k)$ with $x_C\le x_{\max}<1$.  Then there exists a
1+3 initial-data set (an LRS tilted-fluid configuration plus, if needed,
an antipodal kinetic stream pair) satisfying BOTH the Gauss constraint
\eqref{eq:parent} and the momentum constraint, with $\mu\ge0$,
$\Omega_\Lambda$ free of sign, and the weak energy condition on the
matter sector, whose normalized invariants realize the four prescribed
values.  Consequently the interval of T1 is sharp as a statement about
physically admissible configurations, not merely about the convex program.
\end{lemma}
```
**증명 스케치.** (1) Gauss: \(\Omega_m+\Omega_\Lambda=1-x_C>0\)로 예산 마감 — \(\Omega_m\ge0\) 선택 후 \(\Omega_\Lambda\) 부호 자유. (2) 운동량: LRS Bianchi V형 구성에서 \(2A\Sigma_+=(1+w)\Omega_m\beta\) (P5의 제약)가 shear–tilt 균형을 명시적으로 제공 — 임의의 \((\Sigma^2,\Omega_t,\Omega_k>0)\) 조합은 \((A,\beta,\Omega_m)\) 조절로 도달, \(\Omega_k<0\)쪽은 Kantowski–Sachs/Bianchi IX형 LRS 구성으로 동일 절차. (3) vorticity: LRS 회전 계열(예: tilted LRS class III) 또는 국소 kinetic 구성으로 \(W^2\) 주입 후, 유도되는 \(q_a\), \(\Pi_{ab}\)를 P11 스트림으로 흡수. (4) 에너지 조건은 작은-예산 영역(\(x_{\max}\ll1\))에서 열린 조건으로 성립. 주의: (3)이 실제 부담이며, 회전+틸트 LRS 제약대수의 명시적 해(Hewitt–Wainwright 계열)에 기대는 것이 최단 경로다. 완전 일반 증명이 무거우면 "각 극점의 실현 가능 분기 목록"으로 약화해도 P31 승격에는 충분하다.
**난이도**: 중~상 (프로그램 내 최대 가치). **역할**: M2 해소 — sharpness를 물리 명제로 승격. **검증 훅**: 신규 sympy seal 1개(제약 양변 대입 검증) 권장; P5 seal(exp12)이 부분 원형.

---

## T4. 추정 공분산 하 두-단계 커버리지 (P35의 유한-\(N_{\rm sim}\) 판)

**진술.**
```latex
\begin{theorem}[Two-stage coverage with simulation-estimated covariance]
Let $\widehat C_y$ be a Wishart covariance estimate from $N_{\rm sim}$
independent Gaussian simulations, $N_{\rm sim}>m+3$.  Replace the stage-1
and stage-2 thresholds by the Hotelling-type quantiles
\[
\tau_1'=\frac{(m-r)\,(N_{\rm sim}-1)}{N_{\rm sim}-(m-r)}\,
F_{m-r,\ N_{\rm sim}-(m-r),\ 1-\alpha_1},\qquad
\tau_2'\ \hbox{analogously with }r .
\]
Then statement (i) of P35 holds exactly at finite $N_{\rm sim}$; the
$\chi^2$ thresholds are recovered as $N_{\rm sim}\to\infty$; and the
uncorrected procedure has stage-1 size
$\alpha_1'=1-F_{m-r,N_{\rm sim}-(m-r)}\!\bigl(\tfrac{N_{\rm sim}-(m-r)}{(m-r)(N_{\rm sim}-1)}\chi^2_{m-r,1-\alpha_1}\bigr)>\alpha_1$,
quantifying the refutation-inflation of an uncorrected EMPTY verdict.
\end{theorem}
```
**증명 스케치.** 잔차 부분공간으로의 직교 사영 후 표준 Hotelling \(T^2\) 분포론: \(x^T\widehat C^{-1}x\)의 사영 성분은 \(T^2_{k,N-1} = \frac{k(N-1)}{N-k}F_{k,N-k}\). 사영들의 독립성(가우스 직교 사영)은 known-covariance 경우와 동일하게 성립하되, \(\widehat C\) 공유로 stage 1/2의 임계값 결합이 필요하면 Bonferroni로 처리(그대로 P35의 (i) 구조). IM 끝점 부분은 \(\widehat\sigma^\pm\)의 일치성만 요구하므로 asymptotic 문장은 유지.
**난이도**: 중 (표준 다변량 분포론). **역할**: M3 해소; K1 lane의 등록요건을 §3.4 본문 정리로 승격. **검증 훅**: exp11 (미보정 크기 0.072 재현; F-임계값 MC는 동일 코드 1줄 교체).

---

## T5. 결정론적 폭 레짐에서 IM 구간의 정확(비점근) 커버리지

**진술.**
```latex
\begin{proposition}[Exact finite-sample IM coverage under deterministic width]
In the registered regime where both endpoint estimators share one
Gaussian reachable noise, $\widehat x^\pm = x^\pm + \varepsilon$,
$\varepsilon\sim{\cal N}(0,\sigma^2)$ with $\sigma$ known and
$\Delta=x^+-x^-$ DETERMINISTIC, the Imbens--Manski interval
$[\widehat x^--C_N\sigma,\ \widehat x^++C_N\sigma]$ has EXACT coverage
$\ge1-\alpha$ for every $\theta\in[x^-,x^+]$, with equality at the
endpoints; no asymptotics and no Stoye-type uniformity condition are
needed.
\end{proposition}
```
**증명 스케치.** 끝점 \(\theta=x^-\)에서 커버리지 = \(\Prob(-C_N\sigma\le\varepsilon\le C_N\sigma+\Delta)=\Phi(C_N+\Delta/\sigma)-\Phi(-C_N)=1-\alpha\) (IM 방정식 그 자체). 내부점은 단조성으로 \(\ge\). \(\Delta\) 추정 불확실성이 0이므로 Stoye 조건은 공허하게 성립. 이 관찰은 보고서가 이미 산문으로 언급한 것("the exact regime")의 정식화이며, 비용 없이 P35를 강화한다.
**난이도**: 하. **역할**: P35(iii)의 점근 문구를 정확 문장으로 승격 — 심사자 관점에서 가장 값싼 강화. **검증 훅**: exp03 (커버리지 0.9465 ≈ 0.95, Δ→0에서 0.953).

---

## T6. 횡속도 채널의 vorticity Fisher 하한 (P22의 정량판)

**진술.**
```latex
\begin{proposition}[Quantitative reopening of the vorticity sector]
Let the observable set add a transverse-velocity template
$t_a = P_{ab}\,\omega^{bc} n_c$ (screen projector $P_{ab}$) with white
noise level $\sigma_t$ over $N_{\rm src}$ sources of mean depth $\chi$.
Then the Fisher information for $W^2$ satisfies
\[
{\cal I}(W^2)\ \ge\ \frac{N_{\rm src}}{4\,\sigma_t^2}\,
\frac{(3H^2)\,\overline{\chi^2}\,\xi_{\rm geom}}{W^2},
\qquad \xi_{\rm geom}=\E\bigl[\|P\,\hat\omega\times n\|^2\bigr]>0
\]
for isotropic source distributions, with $\xi_{\rm geom}=2/3$ in the
full-sky limit.  Hence the structural null of P9 is broken at a
computable rate, not merely qualitatively.
\end{proposition}
```
**증명 스케치.** 횡속도 응답 \(v_\perp = \omega\times r\)의 스크린 사영 놈 기대값 계산(구면 평균 → \(2/3\)); 가우스 잡음 하 진폭 파라미터의 Fisher는 응답 제곱합/σ²; \(W^2 = \omega^2/(3H^2)\)로 변수 변환 시 야코비안 \(1/(2\sqrt{W^2}\cdot)\)에서 \(1/W^2\) 인자. full-sky 극한 상수는 exp07류 MC로 검증 가능.
**난이도**: 하~중. **역할**: P22를 "재개방 가능"에서 "얼마나 빨리 재개방되는가"로 승격 — K6 lane의 요구 데이터 양 산정 근거. **검증 훅**: 소형 MC 추가 (스크립트 1개, exp07 확장).

---

## T7. 임의 의존 하 e-값 병합의 본질적 유일성 (문헌 이식)

**진술.** Vovk–Wang의 정리를 프로그램 어휘로 이식: "임의 의존 e-값들에 대해 admissible한 대칭 병합 함수는 convex 결합(과 그 지배 함수)뿐이다." 따라서 P29의 convex 병합 선택은 임의가 아니라 **본질적으로 유일**하다.
**증명 스케치.** 문헌 정리 인용 + 프로그램의 finite-cover 세팅으로의 사상(셀 e-값의 교환 가능성 확인)만 필요. 새 증명 부담 없음.
**난이도**: 하 (이식). **역할**: P29 선택의 최적성 주장 — "왜 곱이 아니라 합인가"라는 표준 심사 질문의 선제 차단(독립 시에는 곱이 우월하나 의존 미지 시 합이 유일 admissible). **검증 훅**: exp05 (ρ=0.9 최대 의존에서 합 병합 유효 확인).

---

## T8. 사양검정의 검정력 단조성과 일치성 (E3의 정리판)

**진술.**
```latex
\begin{proposition}[Monotone power of the stage-1 refutation test]
Under Gaussian noise the stage-1 statistic is noncentral
$\chi^2_{m-r}(\lambda)$ with $\lambda=\|P_\perp\mu_{\rm mis}\|^2$.  Its
rejection probability at any fixed threshold is strictly increasing in
$\lambda$ (MLR property of the noncentral $\chi^2$ family), equals
$\alpha_1$ at $\lambda=0$, and tends to $1$ as $\lambda\to\infty$.
Hence EMPTY-as-refutability is a consistent test against any
misspecification with a residual-space component, and is BLIND to
misspecification inside the reachable column space.
\end{proposition}
```
**증명 스케치.** 비중심 χ² 족의 단조우도비 성질(표준); \(\lambda\)의 정의에서 도달-공간 성분은 사영으로 소거 — 마지막 문장이 과학적으로 중요한 부분(반증력의 사각지대 명시).
**난이도**: 하. **역할**: E3 곡선을 정리로 승격 + "reachable-space 오설정은 EMPTY로 잡히지 않는다"는 한계의 정직한 명문화. **검증 훅**: exp03 검정력 곡선 (0.0518 → 1.000).

---

## T9. 다성분 틸트 예산의 정확 분해 (m1의 정리판)

**진술.**
```latex
\begin{proposition}[Exact multi-component tilt budget]
For $K$ non-interacting perfect-fluid components with equations of state
$w_i$ and rapidities $\beta_i$ relative to the normal frame,
\[
1=\sum_i\Omega_i+\Omega_\Lambda+\Omega_k+\Omt^{\rm tot}+\Sig-\Wsq,
\qquad
\Omt^{\rm tot}=\sum_i(1+w_i)\,\Omega_i\sinh^2\beta_i ,
\]
EXACTLY in every $\beta_i$; the boost-induced energy fluxes and
anisotropic stresses enter only the momentum constraint and the
evolution equations, not the Gauss budget.
\end{proposition}
```
**증명 스케치.** 성분별 \(T^{(i)}_{ab}n^an^b=\mu_i+(\mu_i+p_i)\sinh^2\beta_i\)의 합산(정확식, exp01의 단일 성분 계산과 동일); Gauss 제약은 총 \(T_{ab}n^an^b\)만 본다는 사실로 마감. CMB-물질 상대 틸트가 있는 시대(예: 재결합 전후)로 comparator를 확장할 때 필요한 정확한 형태.
**난이도**: 하. **역할**: m1 수리 + \(\Omega_{\rm tilt}\) 정의의 다성분 일반화 — Paper A의 완결성 요건. **검증 훅**: exp01 확장 1줄 (성분 합 잔차 0).

---

## 우선 증명 순서 권고

| 순위 | 후보 | 이유 |
|---|---|---|
| 1 | T1 | 치명 결함 F1의 수리 그 자체, 증명 비용 최소 |
| 2 | T2 | 이미 반증된 진술(P36)의 교정 — 방치 시 등급 체계 신뢰 훼손 |
| 3 | T5 | 비용 대비 강화 효과 최대 (P35 점근→정확) |
| 4 | T4 | EMPTY 판정(반증 주장)의 실무 유효성 조건 |
| 5 | T8, T9 | 저비용, Paper A 완결성 |
| 6 | T3 | 최대 가치·최대 비용 — P31 승격, 프로그램의 물리적 내용 강화 |
| 7 | T6, T7 | Paper B/C 및 K6 lane 설계 근거 |
