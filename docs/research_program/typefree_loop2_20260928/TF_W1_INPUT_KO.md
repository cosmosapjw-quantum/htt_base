# TF-W1: R2 brightness monopole의 유한 창

## 명제와 원천

원천은 I1에 보존된 R2의 agent_kinematics.md §4의 정확한 bolometric brightness 약형이다. 관측자 rest frame과 같은 수송 규칙을 고정한다. τ는 선택한 timelike congruence의 proper time이고, Δ=τ_b−τ_a>0, τ₀∈[τ_a,τ_b]다. 한 장의 CMB 하늘을 이 τ 구간의 시계열로 취급하지 않는다.

R2의 monopole은

\[
J_0=4H\rho+S:M_2+2a\cdot M_1,\quad
\rho=\int_{S^2}B\,d\Omega,\quad M_r=\int_{S^2}B e^{\otimes r}d\Omega,
\]

여기서 \(a=A/c\), \(H=\theta/3\), \(S=\sigma\), \(B\ge0\)는 bolometric brightness다. \(k=(H,S_{\rm STF},a,\Omega)\)로 놓고, 같은 τ의 moments를 이용하여

\[
A_0(\tau)k=4\rho(\tau)H(\tau)+M_2(\tau):S(\tau)
+2M_1(\tau)\cdot a(\tau)+0\cdot\Omega(\tau).
\]

마지막 0은 이 monopole 연산자에서 와도가 보이지 않는다는 뜻이다. 다른 통계에서의 무관함을 뜻하지 않는다. R2의 \(\mathscr D_{\rm hor}B+\mathcal A_kB=\mathcal C\)를 동일한 transported frame의 선택한 ray/worldline에 따라 적분하고, \(\mathscr D_{\rm hor}\)의 spatial/connection 잔여항을 \(r_{\rm tr}\)로 정의하면
\[
m'=s-A_0k,\quad m=\rho,\quad
s=\int_{S^2}\mathcal C\,d\Omega-r_{\rm tr}.
\]
이것은 정의된 source decomposition이며 \(s\)를 관측했다는 주장이 아니다.

## 명시한 창과 예산

\[
w(\tau)=\frac{6(\tau-\tau_a)(\tau_b-\tau)}{\Delta^3}
\quad(\tau_a\le\tau\le\tau_b).
\]
\(w\in C^1\), \(w(\tau_a)=w(\tau_b)=0\), \(\int w d\tau=1\)이다. \(m\in AC\), \(s,A_0\in L^1\), \(\|k(\tau)-k(\tau_0)\|\le L|\tau-\tau_0|\)라면
\[
K_w=\int w A_0k\,d\tau
=\int(ws+w'm)d\tau-[wm]_{\tau_a}^{\tau_b},
\quad [wm]_{\tau_a}^{\tau_b}=0,
\]
\[
\left\|(\int wA_0d\tau)k(\tau_0)-K_w\right\|
\le L\int |w|\,\|A_0\|\,|\tau-\tau_0|d\tau .
\]
관측/모형 오차가 \(\|\delta s\|\le\epsilon_s(\tau)\), \(\|\delta m\|\le\epsilon_m(\tau)\), endpoint error \(\epsilon_a,\epsilon_b\)라면 추가 예산은 \(\int(|w|\epsilon_s+|w'|\epsilon_m)d\tau+|w(\tau_b)|\epsilon_b+|w(\tau_a)|\epsilon_a\); 이번 창에서 끝점 계수는 정확히 0이다. \(A_0\)도 불확실하면 \(\int|w|\|\delta A_0\|\|k\|d\tau\)가 필요하고, \(\|k\|\)가 자유이면 유한 숫자로 바꿀 수 없다. \(K_w\) 단위는 energy density/time이다.

## 입력 상태

| 입력 | 상태 | 근거/필요 계약 |
|---|---|---|
| R2 moment 식과 \(A_0\)의 계수 | exact analytic, conditional | 위 R2 원문 §4 |
| 실제 \(\rho(\tau),M_1(\tau),M_2(\tau)\) | UNAVAILABLE | 한 정적 하늘에서 proper-time trajectory를 얻을 수 없음 |
| \(\mathcal C\), source/selection/optical depth, \(r_{\rm tr}\) | UNAVAILABLE | 광로, emission/collision, source population, tetrad 및 nuisance 미제공 |
| \(L\), \(\epsilon_m\), \(\epsilon_s\), \(\epsilon_A\) | UNAVAILABLE | derivative 또는 calibrating law 없음 |
| \(w\) 및 endpoint 계수 | DECLARED | 위 유한 창; 수치 관측량 아님 |
| redshift-bin 보조 관측 응답 | NOT_ADOPTED | 채택 시 \(d\tau/dz\), source/selection/optical depth, nuisance, covariance와 동일 congruence를 먼저 지정해야 함 |

## quotient, 함수족, 판정

하나의 monopole 창은 \(k\)에 대한 선형 row를 최대 하나 제공한다. source/nuisance가 자유이면 그 row도 보정된 target이 아니므로 현재 실제 자료법칙 아래 확인된 식별 tensor 조합은 **없다**. source가 유계인 선언된 조건부 모델에서는 \(\ker(P_N^\perp\bar A_w)\subseteq\ker P\)인 target \(Pk\)만 유계 가능하며, 실제 coupled feasible set의 fiber를 사용한다. local boost/global tilt의 응답 열이 같으면 그 차이는 kernel에 남는다.

\(x\)는 \(\theta/H_*\), \(\sigma/H_*\), \(\omega/H_*\), \(A/(cH_*)\), 두 상대속도의 각 rank/parity 및 source-dependent 관측 functional을 함께 담는다. \(Q\)는 실제 joint anchor \(B_\chi\)가 있을 때의 gauge/margin, \(F\)는 방향별 support 사용률, \(\Pi\)는 선언한 자료법칙의 exceedance, \(G_F\)는 depth/transport coherence다. 현재는 \(B_\chi\), joint likelihood, 두 depth의 time/source response가 없어 이들 중 수치 \(Q,F,\Pi,G_F\)를 계산할 수 없다. TF-P2의 \(\delta,d_*\)도 실측되지 않았다. 조건부 물리 비율 \(100(1-\gamma_{B_\chi})\)과 p-value는 서로 다른 객체이고 **둘 다 이번에는 UNAVAILABLE**이다.
