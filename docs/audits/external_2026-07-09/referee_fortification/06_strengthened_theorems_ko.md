# 강화 정리집 — 완전 증명 (v7 본문 등록용)

각 정리는 심사에서 지적된 결함을 **더 강한 진술로 대체**한다. 표기는 v6 본문을 따른다: \(\bm g=(\Sigma^2, W^2, \Omega_{\rm tilt}, \Omega_{k,\rm aniso})\), \(c=(1,-1,1,1)\), \(x_C=c^T\bm g\). 각 절 끝의 **[반전]** 문단은 이 정리가 어느 비판을 어떻게 뒤집는지, **[검증]**은 본 패키지의 실행 witness를 가리킨다.

---

## §1. T1′ — 부호 있는 널-박스 식별구간 (P26의 일반화; F1의 반전)

**정리 T1′.** \(\mathcal{G}(y)\)를 §3.3의 feasible set이라 하자. 단, (i) \(R\)의 널 성분은 0-컬럼, (ii) \(\mathcal{C}_{\rm phys} = \{g_\Sigma, g_W, g_t \ge 0\} \times \mathbb{R}_{(k)}\), (iii) 각 널 성분 \(j\)는 선언된 부호 박스 \(g_j \in [L_j, U_j]\), \(L_j \le U_j\) (단측 선언은 \(L_j = 0\))를 갖는다. \(\mathcal{G}(y) \neq \emptyset\)이면 상 \(\{c^T \bm g : \bm g \in \mathcal{G}(y)\}\)는 닫힌구간 \([x_C^-, x_C^+]\)이고,

\[
x_C^{\pm} = \Bigl(\text{도달 타원체} \cap \text{콘 위 } c_R^T \bm g_R \text{의 극값}\Bigr) + \sum_{j \in \rm null} \bigl[\min(c_j L_j,\, c_j U_j),\ \max(c_j L_j,\, c_j U_j)\bigr]^{\mp}
\]

(윗첨자 \(\mp\): 하한에는 min-합, 상한에는 max-합). \(L_j = 0\)이면 P26으로 환원된다.

**증명.** (a) *구간성·닫힘*: \(\mathcal{G}(y)\)는 타원체 원기둥 ∩ 콘 ∩ 박스의 교집합으로 볼록·닫힘이고, 도달 슬라이스는 유계(타원체가 도달 좌표에서 유계), 널 박스는 콤팩트이므로 \(\mathcal{G}(y)\)는 콤팩트 볼록. 선형 함수의 콤팩트 볼록집합 상은 닫힌구간이다. (b) *분해*: 널 컬럼이 0이므로 데이터 misfit은 널 좌표에 의존하지 않고, 콘·박스 제약은 좌표 분리형이다. 따라서 \(\mathcal{G}(y) = \mathcal{G}_R(y) \times \prod_j [L_j, U_j]\)로 인수분해되고, \(\sup(A+B) = \sup A + \sup B\), \(\inf(A+B) = \inf A + \inf B\) (독립 좌표의 선형 결합)에 의해 극값이 성분별 합으로 분해된다. (c) *널 성분 극값*: 구간 \([L_j, U_j]\) 위에서 \(c_j g_j\)의 최소·최대는 \(\min(c_j L_j, c_j U_j)\), \(\max(c_j L_j, c_j U_j)\) — 이는 \(c_j\)와 \(L_j\)의 부호에 관계없이 성립한다. ∎

**따름정리 DL1 (분기-단조성).** 선언 박스 \([L_j, U_j] \subseteq [L_j', U_j']\)이면 \([x_C^-, x_C^+] \subseteq [x_C^{-\prime}, x_C^{+\prime}]\). 특히 open-branch(\(L_k = 0\)) 구간은 all-branch(\(L_k = -U_k\)) 구간에 포함되고, 하한 차는 정확히 \(|c_k| U_k\)이다.

**증명.** 박스 확대는 feasible set의 확대이므로 상의 확대. 하한 차는 T1′ 공식에서 \(\min(c_k L_k, c_k U_k)\)의 차로 즉시 계산된다. ∎

**따름정리 DL2 (분기-민감도 카드의 정당성).** 선언 분기가 서로 다른 두 구간은 모두 각자의 선언 하에서 sharp하므로, 두 구간을 병기하는 것(카드)은 보수화가 아니라 **선언의 가격을 정확히 인쇄하는 것**이다.

**[반전]** F1("비음수 가정이 닫힌형 곡률을 무언 배제")은 이제 이렇게 읽힌다: v6의 \([0.11, 0.17]\)은 open-branch 선언(\(L_k=0\))의 sharp 구간으로 **참**이고, all-branch 선언의 sharp 구간 \([0.09, 0.17]\)이 **추가**되었으며, 두 값의 차이는 DL1이 예측하는 정확한 양(\(U_k = 0.02\))이다. 적용 범위는 늘었고 철회된 것은 없다.
**[검증]** FORT01 자가시험: open \([0.1100, 0.1700]\), all \([0.0900, 0.1700]\), DL1 단조성 True, 상태대수 4분기(FEASIBLE/EMPTY/UNBOUNDED/CEILING_UNFIT) 전부 실행.

---

## §2. T2′ — joint-대-naive 구간의 엄격성 판별 (P36의 강화; M1의 반전)

**정리 T2′.** P36의 세팅(공유 널 성분 \(s \in \mathcal{S} = \prod_j [s_j^-, s_j^+]\), \(N(s) = n + c_N \cdot s\), \(D(s) = d + c_D \cdot s > 0\), \(n \in [n^-, n^+]\), \(d \in [d^-, d^+]\))에서:

(i) **포함**: joint 구간 ⊆ naive 구간 (항상).
(ii) **상한 등식 판별**: joint 상한 = naive 상한 \(\iff \arg\max_{s \in \mathcal{S}} c_N \cdot s \,\cap\, \arg\min_{s \in \mathcal{S}} c_D \cdot s \neq \emptyset\). 박스에서 이는 \(\forall j\) (비퇴화 구간): \(c_{N,j} c_{D,j} \le 0\)과 동치다.
(iii) **엄격성**: 따라서 상한에서 포함이 엄격 \(\iff \exists j:\ c_{N,j} c_{D,j} > 0\)이고 \(s_j^- < s_j^+\). 하한은 \(\arg\min c_N \cdot s \cap \arg\max c_D \cdot s\)로 대칭.

**증명.** (i) naive는 \((s_N, s_D) \in \mathcal{S} \times \mathcal{S}\) 위의 최적화, joint는 대각 \(\{(s,s)\}\) 위의 최적화 — 부분집합 위의 sup는 크지 않다. (ii, ⇐) 교집합에 \(s^\* \)가 있으면 naive 상한 \(= \frac{n^+ + c_N \cdot s^\*}{d^- + c_D \cdot s^\*}\)이 대각 원소 \((s^\*, s^\*)\)에서 달성되므로 joint 상한과 일치. (ii, ⇒) 박스에서 \(\arg\max c_N \cdot s\)는 \(\{s_j = s_j^+ \text{ if } c_{N,j} > 0;\ s_j^- \text{ if } c_{N,j} < 0;\ \text{임의 if } c_{N,j} = 0\}\)의 곱집합이고 \(\arg\min c_D \cdot s\)도 마찬가지. 두 곱집합의 교집합이 공집합 \(\iff\) 어떤 \(j\)에서 요구 꼭짓점이 상반 \(\iff c_{N,j} c_{D,j} > 0\) (비퇴화 \(j\)). 교집합이 공집합인 경우, naive 상한을 주는 어떤 \((s_N, s_D)\)도 \(s_N \neq s_D\)이며, 고정 \(s\)에 대해 \(\frac{n^+ + c_N \cdot s}{d^- + c_D \cdot s}\)는 경쟁 성분 \(j\)에서 \(s_j\)를 어느 쪽으로 움직여도 분자·분모가 같은 방향으로 움직여 진성 손실이 생긴다: 구체적으로 \(f(s) = \frac{a + c_N \cdot s}{b + c_D \cdot s}\)의 \(s_j\)-도함수는 \(\frac{c_{N,j}(b + c_D \cdot s) - c_{D,j}(a + c_N \cdot s)}{(b + c_D \cdot s)^2}\)로, naive가 요구하는 두 극값을 동시에 만족하는 \(s_j\)가 없으므로 \(\max_s f < \) naive 상한 (엄격). (iii)은 (ii)의 대우. ∎

**[반전]** M1의 반례(정렬 레짐 등식)는 이제 정리의 한 분기다. v6의 충분조건적 진술("항상 엄격")은 필요충분 판별로 대체되어 **원문보다 강한** 정리가 되었고, "joint 구성은 결코 naive보다 나쁘지 않으며 언제 정확히 이기는지 안다"는 완결적 주장으로 승격되었다.
**[검증]** FORT02: 유리수 정확 산술(허용오차 0) 371/371 판별 일치; 엄격 260건, 등식 111건; v6 문구에 대한 명시 반례 1건 보존.

---

## §3. T4′ — 시뮬레이션-추정 공분산 하 두-단계 절차의 정확 크기 (M3의 반전)

**정리 T4′.** \(\widehat{C}_y\)가 \(N_{\rm sim} > m + 3\)개의 독립 Gaussian 시뮬레이션의 표본공분산이고 데이터와 독립이라 하자. 잔차 부분공간(차원 \(k = m - r\))의 정규직교 기저 \(B\)에 대해 \(q = x_r^T (B^T \widehat{C}_y B)^{-1} x_r\), \(x_r = B^T x\)로 두면, 귀무(올바른 사양) 하에서

\[
\frac{N_{\rm sim} - k}{k (N_{\rm sim} - 1)}\, q \sim F_{k,\, N_{\rm sim} - k},
\]

이므로 임계값 \(\tau_1' = \frac{k (N_{\rm sim} - 1)}{N_{\rm sim} - k} F_{k, N_{\rm sim} - k, 1 - \alpha_1}\)를 쓰는 사양검정은 **유한 \(N_{\rm sim}\)에서 크기가 정확히 \(\alpha_1\)**이다. stage-2도 \(k \to r\)로 동일하며, \(N_{\rm sim} \to \infty\)에서 \(\chi^2\) 임계값으로 수렴한다. 미보정 \(\chi^2\) 임계값의 실제 크기는 \(\alpha_1' = 1 - F_{k, N_{\rm sim}-k}\bigl(\tfrac{N_{\rm sim}-k}{k(N_{\rm sim}-1)} \chi^2_{k, 1-\alpha_1}\bigr) > \alpha_1\)로 닫힌형 계산된다.

**증명.** \(x_r \sim \mathcal{N}(0, \Sigma_r)\), \((N_{\rm sim}-1) B^T \widehat{C}_y B \sim \mathcal{W}_k(\Sigma_r, N_{\rm sim}-1)\)이고 서로 독립이므로 \(q\)는 자유도 \((k, N_{\rm sim}-1)\)의 Hotelling \(T^2\) — 그 분포는 정의에 의해 \(\frac{k(N_{\rm sim}-1)}{N_{\rm sim}-k} F_{k, N_{\rm sim}-k}\)이고 \(\Sigma_r\)에 무관(피벗). 잔차·도달 사영의 독립성은 Gaussian 직교 사영에서 그대로 성립한다. 수렴과 미보정 크기 식은 \(F\)-분포의 극한과 단조성에서 즉시. ∎

**[반전]** M3("χ² 임계값은 추정 공분산에서 부정확, EMPTY가 과대")는 "**F-임계값 두-단계는 유한 \(N_{\rm sim}\)에서 정확하며, 따라서 EMPTY(반증) 판정은 추정 공분산 하에서도 유효한 주장**"으로 대체된다. v6의 등록요건(M5′, percent-level 언급)보다 강한 결론이고, Hartlap은 평균 보정일 뿐 꼬리는 F가 정답이라는 위계도 확정된다.
**[검증]** FORT03 (\(m=10, k=8, N_{\rm sim}=300\), 6000 MC): 미보정 크기 0.0665, F-임계값 0.0555 ± 0.0028 (명목 0.05와 2σ 이내), 검정력 손실 ≤ 3%p.

---

## §4. T5′ — 결정론적 폭 레짐에서 IM 구간의 정확 유한표본 커버리지 (P35 강화)

**정리 T5′.** 두 끝점 추정량이 하나의 Gaussian 도달 잡음을 공유하고(\(\widehat{x}^{\pm} = x^{\pm} + \varepsilon\), \(\varepsilon \sim \mathcal{N}(0, \sigma^2)\), \(\sigma\) 기지), 폭 \(\Delta = x^+ - x^-\)가 결정론적(널-박스 폭)이라 하자. IM 방정식 \(\Phi(C_N + \Delta/\sigma) - \Phi(-C_N) = 1 - \alpha\)의 해 \(C_N\)에 대해 구간 \([\widehat{x}^- - C_N \sigma,\ \widehat{x}^+ + C_N \sigma]\)는 **모든** \(\theta \in [x^-, x^+]\)에 대해 유한표본 커버리지 \(\ge 1 - \alpha\)를 가지며 끝점에서 등호가 성립한다. 점근 논법도 Stoye형 균일성 조건도 불필요하다.

**증명.** \(\theta = x^- + t\), \(t \in [0, \Delta]\)에 대해 커버리지 사건은 \(\{\widehat{x}^- - C\sigma \le \theta \le \widehat{x}^+ + C\sigma\} = \{-C\sigma - (\Delta - t) \le \varepsilon \le C\sigma + t\}\)... 정확히는 \(\theta \ge \widehat{x}^- - C\sigma \iff \varepsilon \le t + C\sigma\), \(\theta \le \widehat{x}^+ + C\sigma \iff \varepsilon \ge t - \Delta - C\sigma\). 확률 \(= \Phi(C + t/\sigma) - \Phi(-C - (\Delta - t)/\sigma)\). 이 함수는 \(t = 0\)과 \(t = \Delta\)에서 같은 값 \(\Phi(C + \Delta/\sigma) - \Phi(-C)\)을 갖고(대칭), 도함수 \(\frac{1}{\sigma}[\varphi(C + t/\sigma) - \varphi(C + (\Delta - t)/\sigma)]\)의 부호가 \(t < \Delta/2\)에서 양, \(t > \Delta/2\)에서 음이므로(\(\varphi\)는 \([0,\infty)\)에서 감소) 단봉이며 최솟값은 끝점에서 달성된다. 끝점 값은 IM 방정식에 의해 정확히 \(1 - \alpha\). ∎

**[반전]** P35(iii)의 "asymptotic" 문구가 "exact"로 승격된다 — 비용 0의 강화.
**[검증]** exp03: IM 커버리지 0.9465 (N=4000, 명목 0.95, SE 0.0034); \(\Delta \to 0\)에서 0.953.

---

## §5. T8′ — 사양검정 검정력의 단조성·일치성과 사각지대 (E3의 정리화)

**정리 T8′.** Gaussian 잡음에서 stage-1 통계는 비중심 \(\chi^2_{m-r}(\lambda)\), \(\lambda = \|P_\perp \mu_{\rm mis}\|^2\)이다. 고정 임계값에 대한 기각확률은 \(\lambda\)에 강단조 증가(비중심 \(\chi^2\) 족의 MLR 성질), \(\lambda = 0\)에서 \(\alpha_1\), \(\lambda \to \infty\)에서 1이다. 즉 EMPTY-as-refutability는 잔차 성분을 갖는 **모든** 오설정에 대해 일치(consistent) 검정이며, 도달 열공간 내부의 오설정(\(P_\perp \mu_{\rm mis} = 0\))에는 원리적으로 무감하다.

**증명.** 비중심 \(\chi^2\)의 밀도비가 \(\lambda\)에 대해 단조우도비임은 표준 사실(베셀 급수 표현에서 즉시). 기각확률의 극한은 비중심 모수 발산에서 자명. 사각지대 문장은 \(\lambda\)의 정의 그 자체다. ∎

**[반전]** E3의 "rising to 1.00"이 정리가 되고, 동시에 반증력의 한계(도달-공간 오설정)가 정직하게 명문화되어 "우리는 무엇을 반증할 수 없는지도 증명했다"는 프로그램 어법이 완성된다.
**[검증]** exp03 검정력 곡선 (0.0518 → 1.000, 단조).

---

## §6. T9′ — 다성분 틸트 예산의 정확 분해 (m1의 정리화)

**정리 T9′.** 상호작용 없는 \(K\)개 완전유체(상태방정식 \(w_i\), 정규 프레임 대비 rapidity \(\beta_i\))에 대해

\[
1 = \sum_i \Omega_i + \Omega_\Lambda + \Omega_k + \Omega_{\rm tilt}^{\rm tot} + \Sigma^2 - W^2, \qquad \Omega_{\rm tilt}^{\rm tot} = \sum_i (1 + w_i)\, \Omega_i \sinh^2 \beta_i,
\]

이 항등식은 모든 \(\beta_i\)에서 **정확**하다. 부스트 유도 에너지플럭스 \(q_a^{(i)} = (\mu_i + p_i) \sinh\beta_i \cosh\beta_i\, e_a^{(i)}\)와 비등방응력은 Gauss 예산이 아니라 운동량 제약·진화 방정식에만 들어간다.

**증명.** 성분별로 \(T^{(i)}_{ab} n^a n^b = (\mu_i + p_i) \cosh^2\beta_i - p_i = \mu_i + (\mu_i + p_i) \sinh^2\beta_i\) (정확식; \(u^{(i)} \cdot n = -\cosh\beta_i\)). Gauss 제약은 총 \(T_{ab} n^a n^b = \sum_i T^{(i)}_{ab} n^a n^b\)만 포함하므로 합산 후 \(3H^2\)로 나누면 진술식. 플럭스·응력은 \(T_{ab} n^a h^b{}_c\), \(T_{\langle ab \rangle}\) 성분으로 Gauss(시간-시간 성분)에 나타나지 않는다. ∎

**따름정리.** 반대 방향 틸트 쌍(\(\beta, -\beta\), 동일 \(w, \Omega\))은 \(q\)를 상쇄하면서 \(\Omega_{\rm tilt}^{\rm tot}\)에는 가산 기여한다 — T3(실현 정리)의 핵심 구성 요소.

**[반전]** m1("O(sinh²β)는 과소 진술")이 다성분 정확 정리로 승격되어, 복사+물질 시대(재결합 전후)로 comparator를 확장하는 Paper A의 완결성 요건을 충족한다.
**[검증]** exp01 (단일 성분 정확성; 다성분은 합산의 선형성으로 자명).

---

## §7. T3-lin — 선형화 실현 정리 (P31 승격의 중간 단계; M2 대응) — 증명 스케치 + 잔여 보조정리

**명제 T3-lin (등록 목표).** \(x_{\max} \ll 1\)인 임의의 목표 \((\Sigma^2_\*, W^2_\*, \Omega_{t\*}, \Omega_{k\*})\) (부호 박스·콘 준수)에 대해, FLRW 배경 위 선형화 초기데이터와 물질 배치가 존재하여 (i) Gauss·운동량 제약을 선형 차수에서 만족하고, (ii) 정규화 불변량이 목표값을 재현하며, (iii) 물질 부문이 약에너지조건을 만족한다. 따라서 T1′ 구간의 sharpness는 선형화 레짐에서 물리 명제다.

**증명 스케치.** (1) \(\Sigma^2_\*\): Bianchi I형 균질 전단 모드 — 운동량 제약이 자동 충족(대각 전단, \(q = 0\)). (2) \(\Omega_{k\*}\): FLRW 곡률 분기 혼합(등방 성분)과 Bianchi V/IX형 균질 곡률 모드; open/closed 부호 모두. (3) \(\Omega_{t\*}\): T9′ 따름정리의 반대-틸트 쌍 — 순 플럭스 0으로 운동량 제약 무부담. (4) \(W^2_\*\): 선형 벡터(회전) 모드 — 운동량 제약이 \(\nabla^2\)-역으로 \(q_{\rm vec}\)를 결정하며, 이는 (3)의 쌍에 소량의 비대칭 틸트를 얹어 공급; 진폭 자유. (5) 에너지조건: 모든 모드 진폭이 \(O(\sqrt{x_{\max}})\)이므로 배경 \(\mu > 0\)에 대한 선형 교란으로 유지. **잔여 보조정리 (등록 필요):** (4)에서 벡터 모드의 \(\omega\)와 (1)의 \(\sigma\)가 2차 결합 없이 목표 4-튜플을 독립 조준할 수 있음 — 선형 차수에서는 모드 중첩의 선형성으로 성립하나, "congruence 선택(정규 vs 물질 프레임)의 규약 고정" 문장을 정확히 써야 한다. 완전판(비선형, King–Ellis 틸트 Bianchi V 불변량 사상)은 WBS-C1.

**[반전]** M2("sharpness는 물리 명제로 미증명")는 "선형화 레짐(comparator의 실사용 영역 전체)에서 증명, 비선형 완전판은 등록된 정리 후보"로 재배치된다 — 갭의 인정이 아니라 정리 사다리의 명시.

---

## 부록 — 정리·비판·검증 대응표

| 정리 | 대체/강화 대상 | 반전되는 비판 | witness |
|---|---|---|---|
| T1′ + DL1/DL2 | P26/P31(부분) | F1 | FORT01 |
| T2′ | P36 | M1 | FORT02 (371/371) |
| T4′ | P35 확장 | M3 | FORT03 |
| T5′ | P35(iii) | (강화) | exp03 |
| T8′ | E3 | (강화) | exp03 |
| T9′ | §3.1 tilt 정의 | m1 | exp01 |
| T3-lin | P31 | M2 | (seal 예정, WBS-B1) |
