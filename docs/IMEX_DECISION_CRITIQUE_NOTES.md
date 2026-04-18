# IMEX Decision — Critique Notes (archived)

> **STATUS — HISTORICAL RECORD / ABSORBED (2026-04-18)**
>
> This document is the **critique trail** that refined the initial first-pass
> "pure IMEX-ARK4 is obviously right" analysis into the final decision. Its
> six corrections (overclaims → refined claims) are summarised in
> [`IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md) §3.
>
> **Authoritative decision**: [`docs/IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md)
>
> **Kept here** as historical record — the reasoning chain it contains
> supports re-auditing the decision if circumstances change. Do **not**
> treat this document as an action plan; its specific recommendations are
> subsumed by the authoritative decision above.

---

## 짧은 요약

이 반론은 **상당히 강한 비판**이고, 특히 **(1) composite order 문제**, **(2) 현재 `mats_flat` 기반 메모리 병목**, **(3) pure IMEX-ARK가 갖는 문헌적 방어력**에 대해서는 수용할 부분이 많다.
하지만 반론은 몇 군데서 **과도하게 단정**하고 있어. 특히 **“이건 사실상 그냥 IMEX다”**, **“IMEX가 자동으로 메모리 문제를 해결한다”**, **“4–8주 vs 3–6개월”**, **“hybrid는 literature-free”** 같은 결론은 엄밀한 의미에선 과장이다.
내 최종 판정은 이거야: **현재 스케치된 hybrid를 곧바로 주력 생산 경로로 밀어붙이기엔 반론이 맞다.** 다만 그걸 곧바로 **“그러므로 pure IMEX-ARK4가 유일한 정답”**으로 점프하는 것도 논리적으로는 아직 한 단계 과하다. 반론문이 제기한 위험은 매우 진짜고, 그래서 **IMEX-ARK4를 1순위 reference branch로 올리고, hybrid는 backup/benchmark branch로 내리는 전략**이 가장 합리적이다.  ([sundials.readthedocs.io][1])

핵심 bullet

* **수용해야 할 비판**

  * 현재 hybrid 스케치에는 **formal global order 보장**이 없다.
  * `mats_flat`류의 **백엔드 메모리 병목**은 split만으로 해결되지 않는다.
  * 논문 defensibility만 보면 **Kennedy–Carpenter ARK / ARKODE / IMEX kinetic literature** 쪽이 더 강하다.

* **반박해야 할 비판**

  * “이건 그냥 IMEX인데 이름만 바꿨다”는 말은 **부정확**하다.
  * “kernel hysteresis = LSODA 재판”은 **부분 유사성은 있지만 동치가 아니다**.
  * “IF tail은 1차라서 hybrid는 본질적으로 저차”는 **현재 스케치에는 맞지만, 방법 계열 전체에 대한 판정으로는 틀리다**.
  * “IMEX가 메모리 문제를 자동 회피한다”도 **구현 세부를 생략한 과장**이다.

* **최종 판단**

  * 반론은 **현재 hybrid 설계의 production 승격을 막는 데는 충분히 강하다**.
  * 그러나 **pure IMEX-ARK4 채택을 ‘증명’한 것은 아니다**.
  * 가장 보수적이고 정직한 대응은:

    1. **IMEX-ARK4를 주력 reference path로 착수**
    2. **hybrid는 frozen branch로 두고 A/B benchmark only**
    3. **둘 다 동일 baseline contract와 ablation ladder 아래 비교**
       이다.   ([sundials.readthedocs.io][1])

---

## 1) “이건 사실상 IMEX다”라는 반론

이건 **반쯤 맞고, 반쯤 틀려**.

맞는 부분부터 말하면, 네 반론이 지적하듯 현재 hybrid 스케치는

* core implicit,
* mixed explicit,
* tail integrating factor
  로 나뉜 **partitioned / additive / multirate 성격**을 갖는다. 그리고 Kennedy–Carpenter류 ARK는 분명히 이런 additive framework의 정식 문헌적 기반이다. NASA 문헌도 ARK를 “general case when N different Runge Kutta methods are grouped into a single composite method”로 놓고, (N=2)의 implicit-explicit ARK methods를 3–5차까지 전개한다. SUNDIALS의 ARKStep도 (M(t)\dot y=f^E(t,y)+f^I(t,y)) 꼴의 additive split을 전제로 explicit/implicit RK를 결합한다고 못 박고 있다.  

하지만 **틀린 부분**은, 그래서 곧바로 “이건 사실상 IMEX고 이름만 바꾼 것”이라고 결론내리는 대목이야.
왜냐하면 네가 앞서 스케치한 방법은 **교과서적 ARKStep**이 요구하는 형태와 같지 않다. ARKStep은 explicit part (f^E), implicit part (f^I)라는 **한 쌍의 coupled tableau**를 전제로 한다. 반면 현재 hybrid는

* 바깥은 RODAS5P macro-stepper,
* 안쪽은 low-(\ell) core Rosenbrock solve,
* tail은 IF-treated damping,
* mixed는 predictor-corrector,
* accept/reject는 heterogeneous error proxy의 합성
  이라는 **비대칭적 3-way kernel decomposition**이다. SUNDIALS 자체도 additive ARK 외에 ForcingStep, MRIStep처럼 별도 hybrid/multirate 모듈을 따로 둔다. 이건 곧 “모든 분할이 곧바로 같은 class는 아니다”는 뜻이다. 따라서 “IMEX가 아니다”를 너무 절대화할 필요는 없지만, **“classical symmetric IMEX-RK pair가 아니다”**라는 구별은 여전히 유효하다.   ([sundials.readthedocs.io][1])

내 판정:
**수정 수용.**
표현은 바꿔야 해. “IMEX가 아니다”보다
**“classical two-tableau IMEX-ARK가 아니라, Rosenbrock-centered partitioned hybrid다”**
라고 쓰는 게 더 엄밀하다.

---

## 2) composite order 비판

이건 **반론의 가장 강한 지점**이고, 거의 그대로 수용해야 해.

반론의 요지는 간단하지:

* RODAS5P core는 5차,
* tail IF는 현재 스케치상 frozen coefficient + 저차 quadrature,
* mixed는 predictor-corrector,
  이렇게 되면 전체 차수는 깔끔한 ARK-style order condition을 따르지 않고, 실제 recombination transition에선 **낮은 유효차수**로 떨어질 위험이 크다. 네 이전 문서도 이미 “classical IMEX pair가 아니고, global order는 따로 검증해야 한다”고 인정하고 있었다. 그러니까 이 비판은 사실상 네 문서 안의 경고를 공격적으로 재진술한 셈이다.   

여기서 다만 한 가지는 **반박**해야 해.
그건 “integrating factor가 들어가면 본질적으로 1차쯤으로 무너진다”는 식의 일반화야. 그건 **현재 스케치된 구현**에는 맞을 수 있어도, 방법 계열 전체에 대한 말로는 틀리다. Exponential integrator는 별도의 수학적 order theory가 있고, B-series/order conditions도 정식으로 정리돼 있으며, stiffness-independent error bounds를 노리는 고차 exponential integrator들도 이미 잘 확립돼 있다. 즉 문제는 **IF라는 아이디어 자체**가 아니라, **지금 네 hybrid 스케치가 그 고차 coupling을 갖추지 못했다**는 데 있다. ([Cambridge University Press & Assessment][2])

내 판정:
**핵심 비판은 수용, 일반화는 반박.**
정확히는:

* “현재 hybrid sketch는 formal order가 약하다” → **맞다**
* “그래서 hybrid family 전체가 본질적으로 저차다” → **과장이다**

---

## 3) “tail IF는 diagonal만 처리하니 이득이 제한적”이라는 비판

이것도 **부분 수용**이 맞아.

반론이 맞는 부분은,
tail RHS가 실제로
[
y_T'=-\kappa' D_T y_T + G_T
]
이고, 여기서 IF가 먹는 건 diagonal damping뿐이라서 free-streaming tridiagonal coupling과 metric/source coupling은 여전히 남는다는 점이야. 따라서 “tail 전체를 거의 공짜로 없애는” 식의 기대는 틀렸다. 특히 low-(\ell)까지 implicit에 넣는 full scheme 대비, speedup ceiling이 생각보다 높지 않을 수도 있다.  

하지만 **반론이 너무 빨리 넘겨짚는 부분**도 있어.
대형 kinetic/transport 계에서 가장 비싼 게 항상 “모든 matvec” 자체인 건 아니고, **stiff damping이 강해서 step size를 망치거나 implicit block을 불필요하게 키우는 것**이 더 큰 병목일 수도 있다. Exponential/integrating-factor 계열은 հենց 그런 stiff linear part를 떼어내기 위해 발전해 온 계열이다. 즉 diagonal damping만 빼는 게 “의미 없다”는 건 아니다. 다만 이득의 크기는 **이론으로 말할 수 없고 profiling으로만 말할 수 있다**는 게 정확하다. ([Cambridge University Press & Assessment][2])

내 판정:
**speedup ceiling 비판은 수용. “의미 없다”는 결론은 반박.**

---

## 4) “kernel hysteresis = LSODA의 재판”이라는 비판

이건 **강한 비유이긴 하지만, 동치는 아니다.**

LSODA/DLSODA는 명시적으로 **automatic method switching for stiff and nonstiff problems**를 수행하고, nonstiff에선 Adams, stiff에선 BDF 계열을 쓴다. 즉 solver family 자체를 바꾼다. 반면 네 hybrid sketch는 outer solver를 계속 RODAS5P로 유지하고, 내부에서만 tail correction 횟수나 Jacobian refresh 강도 같은 **kernel policy**를 바꾸겠다는 거였지, 적분기 family 자체를 바꾸겠다는 건 아니었다. 이 둘은 failure mode가 유사할 수는 있어도, 같은 알고리즘 클래스는 아니다. ([Jacob Williams][3])

다만 반론이 짚은 **실질 위험**은 맞아.
진입/이탈 임계값 (\chi_{\rm on},\chi_{\rm off}) 기반의 hysteresis는, 이름이 무엇이든 간에 **regime-boundary oscillation**과 tuning burden을 부른다. 즉 “LSODA와 다르다”는 말이 thrashing 가능성 자체를 없애주는 건 아니다. 이 점은 받아들여야 한다.  

내 판정:

* “LSODA와 동일하다” → **틀림**
* “LSODA류 thrashing 리스크가 살아 있다” → **맞음**

---

## 5) 메모리 비판: `mats_flat` 124 GB

이건 **매우 중요한 비판**이고, 거의 전면 수용해야 해.

네 반론은 current backend가 `integrate_linear_profile_rodas5p`에서 `mats_flat (n_vis × n²)`류 구조를 요구한다면, Bianchi full 5566 DOF에서
[
500 \times 5566^2 \times 8 \approx 124\ \mathrm{GB}
]
가 되어 물리적으로 말이 안 된다고 지적한다. 이 계산 자체는 맞다. 그리고 이 문제는 **core/mixed/tail로 state를 나누는 것만으로는 해결되지 않는다.** stepper interface를 callback/Jacobian-action 중심으로 다시 짜야 한다는 결론도 타당하다. 

다만 여기서도 반론의 마지막 점프는 조심해야 해.
**“그러므로 IMEX-ARK가 자동으로 해결한다”**는 말은 엄밀히 틀리다. ARKODE는 user가 `fe`와 `fi` RHS를 함수로 제공하는 callback-style 인터페이스를 취하므로 giant pre-tabulated (n_{\rm vis}\times n^2) storage를 강제하지는 않는다. 하지만 그건 **좋은 구현을 했을 때**의 이야기지, IMEX라는 이름만 붙이면 자동으로 메모리 문제를 없애준다는 뜻은 아니다. 잘못 구현한 IMEX도 얼마든지 giant stage storage를 만들 수 있다. 즉 이건 **pure IMEX의 본질적 승리라기보다, callback-based stage assembly로 stepper interface를 재설계해야 한다는 백엔드 요구**다. ([sundials.readthedocs.io][4])

내 판정:
**메모리 비판은 거의 전면 수용.**
단, 결론은
“hybrid는 끝, IMEX는 자동 승리”가 아니라
“현 backend 인터페이스는 어떤 solver를 쓰든 재설계가 필요”
가 더 정확하다.

---

## 6) full-state defect norm 비판

이것도 **꽤 설득력 있다**.

반론이 지적한 핵심은,

* (e_C): RODAS embedded estimator
* (e_M): predictor-corrector defect
* (e_T): IF residual / local defect
  를
  [
  |e|^2=|e_C/W_C|^2+|e_M/W_M|^2+|e_T/W_T|^2
  ]
  로 합치는 게 **동일한 asymptotic meaning을 갖는 error estimator의 결합이 아니다**는 거지. 이건 맞는 말이다. 적어도 “이 합성 norm이 classical adaptive RK의 embedded error처럼 이론적으로 clean하다”라고 주장하면 안 된다. 

하지만 이것도 “불법”은 아니야.
partitioned/multirate/hybrid integrator에서는 practical controller가 formal estimator보다 더 messy한 경우가 흔하고, 그런 이유로 따로 order/stability analysis가 붙는다. SUNDIALS도 ARK 외에 ForcingStep, MRIStep 같은 별도 hybrid 모듈을 갖고 있고, multirate–IMEX hybrid 문헌도 따로 존재한다. 즉 “단일 embedded estimator가 아니면 원천적으로 안 된다”는 식으로 말할 수는 없다. 다만 **논문-grade production path**로 갈 때는 이 합성 norm을 그냥 믿지 말고, 꼭 consistency/order 실험으로 정당화해야 한다. ([sundials.readthedocs.io][1])

내 판정:
**이론적 약점 지적은 수용.**
하지만 **즉시 폐기 사유**라고까지는 못 간다.

---

## 7) “hybrid는 literature가 없고, IMEX는 literature가 풍부하다”

이건 **절반만 맞다**.

맞는 부분:

* IMEX-ARK는 Kennedy–Carpenter 이후 정식 문헌이 풍부하고,
* ARKODE 같은 production library가 있으며,
* kinetic/Boltzmann 쪽도 Dimarco–Pareschi 류의 AP/AA 조건까지 정리돼 있다.
  이건 pure IMEX 쪽의 엄청 큰 장점이다. 특히 네가 나중에 방법론을 글로 방어해야 한다면, **“나는 Kennedy–Carpenter/ARKODE/Dimarco–Pareschi 위에 서 있다”**는 말은 힘이 세다. 

틀린 부분:

* “hybrid는 literature-free”는 과장이다. exponential integrator literature 자체가 방대하고, SUNDIALS에도 additive ARK 외에 ForcingStep, MRIStep 같은 hybrid/multirate 카테고리가 있으며, IMEX와 multirate를 결합한 MRI-GARK 계열도 있다. 즉 **현재 네 exact recipe는 bespoke**일 수 있어도, **partitioned / exponential / multirate hybrid라는 더 큰 클래스는 충분히 문헌적 기반이 있다.** ([sundials.readthedocs.io][1])

내 판정:
**“IMEX 쪽 문헌적 우위”는 수용.**
**“hybrid literature 부재”는 반박.**
정확한 표현은
“현재 제안 hybrid의 exact coupling은 bespoke라 방어력이 약하다”
가 맞다.

---

## 8) timeline / 코드양 / “4–8주 vs 3–6개월”

이건 **가장 약한 비판** 중 하나다.

왜냐하면 이건 거의 전부 프로젝트 내부 사정에 의존하는 추산이기 때문이야.
반론문은 hybrid는 2000+ line, IMEX는 400–600 line이라고 쓰지만, adaptive controller, dense output, Jacobian hook, benchmark harness, validation script, Bianchi extension, error norm, callback interface까지 다 넣기 시작하면 “400–600 line ARK4”는 지나치게 낙관적일 수 있다. 반대로 hybrid도 네가 어디까지를 prototype으로 인정하느냐에 따라 훨씬 줄일 수 있다. 즉 **코드 줄 수와 주 단위 일정은 증거가 아니라 가설**이다. 

다만 방향성 수준에서는 맞다.
**이론이 더 정리된 single-tableau IMEX-ARK가, 현 시점의 bespoke hybrid보다 구현 surface area가 작을 가능성은 높다.** 그건 인정할 수 있다. 하지만 “그러므로 4–8주 보장”은 아니다.

내 판정:
**방향성은 수용, 숫자 추정은 반박.**

---

## 9) 그럼 최종 결론은?

내 최종 평가는 이렇게 정리된다.

### 반론이 성공한 부분

이 반론은 **현재 스케치된 hybrid를 바로 mainline production solver로 채택하는 계획**에는 치명타를 줬다.
특히

1. formal composite order 부재,
2. current backend memory model 미해결,
3. heterogeneous acceptance estimator의 이론적 취약성,
   이 셋은 “좋은 아이디어” 수준과 “production-ready 방법론” 사이의 간극을 정확히 찔렀다.  

### 반론이 과장한 부분

하지만 반론은 동시에

1. 현재 hybrid를 너무 쉽게 “그냥 IMEX”로 환원했고,
2. hybrid-related literature를 너무 축소했고,
3. IMEX가 memory/backend 문제를 거의 자동으로 해결하는 것처럼 말했고,
4. 일정/라인 수를 너무 단정적으로 썼다.
   이 부분은 엄밀하지 않다. ARKODE 문서만 봐도 additive ARK, forcing, MRIStep가 서로 다른 모듈로 존재하고, hybrid/multirate literature도 따로 있다. 즉 **분류와 구현 리스크를 한 줄로 압축해버린 게 문제**다. ([sundials.readthedocs.io][1])

### 내가 내리는 실무 판정

지금 시점에서 가장 보수적이고 합리적인 결정은:

* **pure IMEX-ARK4를 1순위 reference implementation으로 채택**
* **현재 hybrid plan은 mainline이 아니라 frozen benchmark/backup branch로 보류**
* **두 경로 모두 동일한 baseline contract와 ablation ladder 아래 비교**
* **특히 memory backend는 solver와 독립된 공통 인프라 과제로 먼저 분리**

이거야.

즉 반론의 결론을 약간 고쳐서 말하면:

> **“지금 당장은 pure IMEX-ARK4가 더 설득력 있는 주력 후보”**
> 는 맞다.
> 하지만
> **“hybrid는 원리적으로 inferior하고 버려야 한다”**
> 는 아직 증명되지 않았다.

---

## 10) 내가 권하는 대응 문구

문서나 회의에서 이렇게 정리하면 좋다.

> 반론은 현재 hybrid 스케치의 세 가지 실제 위험—formal composite order 미정, current backend memory infeasibility, heterogeneous error controller의 이론적 취약성—을 정확히 지적한다. 따라서 현 단계에서 hybrid를 production mainline으로 승격하는 것은 보류한다. 다만 이로부터 pure IMEX-ARK4의 자동적 우월성이 곧바로 따라오는 것은 아니며, 메모리 문제는 callback-based stage assembly라는 공통 backend 재설계를 필요로 한다. 따라서 IMEX-ARK4를 1순위 reference path로, RODAS5P-centered hybrid를 2순위 benchmark path로 두고, 동일한 ablation/validation contract 하에 head-to-head 평가한다.

이게 제일 정직하다.

[1]: https://sundials.readthedocs.io/en/latest/arkode/Mathematics_link.html "2.2. Mathematical Considerations — Documentation for SUNDIALS  documentation"
[2]: https://www.cambridge.org/core/journals/acta-numerica/article/exponential-integrators/8ED12FD70C2491C4F3FB7A0ACF922FCD "Exponential integrators | Acta Numerica | Cambridge Core"
[3]: https://jacobwilliams.github.io/odepack/sourcefile/dlsoda.inc.html "dlsoda.inc – odepack"
[4]: https://sundials.readthedocs.io/en/v7.4.0/arkode/Usage/ARKStep/User_callable.html "2.4.7.1. ARKStep User-callable functions — User Documentation for SUNDIALS  documentation"

---
---

핵심 bullet

* 가정

  * 현재 레이아웃은 species-first / m-major / fixed-(m)에서 (\ell)-contiguous다. photon intensity는 ((L_\gamma+1)^2), (E/B)는 각각 ((L_\gamma+1)^2-4), massless neutrino 두 hierarchy는 각각 ((L_\nu+1)^2), metric+baryon+CDM low-order block은 19 DOF다. 
  * recombination은 ODE 내부 동역학이 아니라 외부 pretabulation이라 (\kappa'(\eta))는 time-dependent coefficient로 공급된다. 이것 자체는 callback-based solver와 완전히 양립 가능하다.  ([sundials.readthedocs.io][1])
  * 네가 유지하려는 “SymBoltz류 approximation-free 전략”은 **선택한 perturbation system 안에서 TCA/UFA/RSA 없이 푸는 것**이지, 아직 채택하지도 않은 더 큰 상태공간까지 미리 끌어안는 걸 뜻하진 않는다. SymBoltz도 “linear Einstein–Boltzmann equations”를 approximation switching 없이 푼다고 소개한다. ([arXiv][2])

* 결론

  * **5566 DOF는 현재 논의 중인 (L_\gamma=25, L_\nu=15) checkpoint를 대표하는 숫자가 아니다.**
  * 같은 체크포인트에서

    * current full all-(m) layout이면 **2551 DOF**,
    * 여기에 massive-(\nu) 130 DOF를 더해도 **2681 DOF**다.
  * 더 나아가 네가 말한 **1/2차 perturbative scope**에 맞춘 reduced active-(m) bookkeeping을 쓰면

    * 1차 SVT-complete 수준: **531 DOF** ((+130 \Rightarrow 661))
    * 2차까지 확장: **901 DOF** ((+130 \Rightarrow 1031))
      로 내려간다.
  * 따라서 124 GB 주장은 **현재 단계 메모리 상한을 과장**한다. 하지만 **현재 `mats_flat \sim N_{\rm snap}n^2` 구조가 장기적으로 부적절하다는 판정 자체는 유지**된다.

* 주의점

  * 다만 reduced-(m) counting을 너무 과하게 밀면 안 된다.
  * **배경을 truly nonperturbative로 두고 그 background-induced (m\to m\pm1,\pm2) mixing을 끝까지 정확히 누적**하면, 장기 exact-Bianchi branch에서는 결국 더 넓은 (m)-support가 살아날 수 있다.
  * 즉 **“5566은 과장”**은 맞지만, 그것이 곧 **“항상 (m\le4)면 충분”**을 뜻하진 않는다.

---

## 1) 5566 숫자가 왜 과장인가

네가 올린 fact-check 문서 기준으로 현재 코드 레이아웃은

[
N_{\rm full}
============

19
+\underbrace{(L_\gamma+1)^2}*{\gamma_I}
+\underbrace{2\big[(L*\gamma+1)^2-4\big]}*{\gamma_E,\gamma_B}
+\underbrace{2(L*\nu+1)^2}*{\nu*\Theta,\nu_\eta}
+N_{\nu,{\rm massive}}
]

이야. 여기서 19는 metric 11 + baryon 4 + CDM 4다. 

그러면 checkpoint로 계속 쓰고 있던
[
L_\gamma=25,\qquad L_\nu=15
]
에서

[
N_{\rm full}
============

## 19+676+2\cdot672+2\cdot256

2551
]

이고, massive-(\nu) 130 DOF를 더해도

[
N_{\rm full,+massive}=2681
]

이다.

즉 **같은 체크포인트에서 “full Bianchi = 5566”은 수학적으로 안 맞아.**
5566은 더 큰 (L), 더 큰 neutrino sector, 혹은 더 많은 추가 블록을 전제해야 나온다. 실제로 네 반론문 자체도 5566을 “target”이라고만 쓰고, 그게 어떤 ((L_\gamma,L_\nu))와 어떤 species set에서 나오는지 수학적으로 못 박지 않는다. 그게 첫 번째 약점이다.

---

## 2) 네 현재 물리 범위에 맞는 reduced DOF counting

여기서 더 중요한 건 네가 방금 scope를 명시했다는 거야.

* background: **only time-dependent**, but nonperturbative
* perturbations: temporal/spatial fluctuation, but **주로 1/2차**
* strategy: **approximation-free** in the SymBoltz sense

이걸 엄밀히 해석하면, “채택한 perturbation theory의 order 안에서는 approximation switching 없이 exact하게 푼다”가 핵심이지, 아직 채택하지도 않은 더 높은 angular content를 선반영하라는 뜻은 아니다. SymBoltz도 정확히 이 철학을 쓴다. 선택한 **linear** Einstein–Boltzmann system을 approximation switching 없이 푸는 거지, 물리 모델의 order 자체를 무한히 키우는 건 아니다. ([arXiv][2])

### 2.1 first-order SVT-complete bookkeeping: ( |m|\le 2 )

현재 네 low-order matter sector가 이미 (v^{m=-1,0,+1})를 갖고 있고, radiation polarization sector는 (\pm2)까지 자연스럽게 등장하니까, **1차 SVT-complete unified bookkeeping**의 자연스러운 active set은

[
m\in{-2,-1,0,+1,+2}
]

이다.

이때 fixed active (m_{\max}=M)에 대해 각 hierarchy DOF는

[
N_I(L;M)=\sum_{m=-M}^{M}(L-|m|+1)
=(2M+1)(L+1)-M(M+1),
]

[
N_E(L;M)=N_B(L;M)
=\sum_{m=-M}^{M}\big(L-\max(2,|m|)+1\big)
=(2M+1)L + M - M^2 - 3
\qquad (M\ge2).
]

따라서 (M=2)이면

[
N_I(L;2)=5L-1,\qquad N_E(L;2)=N_B(L;2)=5L-5.
]

그리고 massless neutrino two-hierarchy는 polarization 없이 intensity-type count를 두 번 쓰면 된다.

그래서
[
L_\gamma=25,\quad L_\nu=15
]
에서

[
N_{\rm red}^{(M=2)}
===================

19 + (5\cdot25-1)+2(5\cdot25-5)+2(5\cdot15-1)
=531.
]

massive-(\nu) 130 DOF를 더하면

[
N_{\rm red,+massive}^{(M=2)}=661.
]

이건 5566과는 비교가 안 될 정도로 작다.

### 2.2 second-order bookkeeping: ( |m|\le 4 )

네가 perturbations를 “주로 1/2차”라고 했으니, second-order angular content까지 포함한 보수적 reduced model은

[
m\in{-4,-3,-2,-1,0,1,2,3,4}
]

즉 (M=4)가 자연스럽다.

같은 공식으로

[
N_I(L;4)=9(L+1)-20=9L-11,
]

[
N_E(L;4)=N_B(L;4)=9L-15.
]

그래서
[
L_\gamma=25,\quad L_\nu=15
]
이면

[
N_{\rm red}^{(M=4)}
===================

## 19+214+2\cdot210+2\cdot124

901,
]

massive-(\nu) 130을 더하면

[
N_{\rm red,+massive}^{(M=4)}=1031.
]

이 수치가 네가 말한 “1/2차 perturbative program”에 더 정직한 near-/mid-term DOF다.

---

## 3) 하지만 여기서 과감하게 브레이크를 걸어야 하는 부분

여기서 **내가 일부러 너 편 안 들고 브레이크 거는 부분**이 있다.

위 reduced counting은 **현재 네가 채택한 perturbative angular scope**에 대해선 맞는 bookkeeping이지만,
그걸 곧바로 **“nonperturbative time-dependent Bianchi background에서도 all-(m)가 필요 없다”**로 일반화하면 안 된다.

왜냐하면 배경이 truly nonperturbative이면, background operator가 시간에 따라 (m\to m), (m\pm1), (m\pm2) 같은 coupling을 계속 누적할 수 있고, 충분히 오래/강하게 가면 결국 higher-(m) support가 점점 채워질 수 있기 때문이야. 네가 올린 문서도 Bianchi (m)-mixing을 explicit block 구조로 이미 적고 있다.

그러니까 더 정확한 표현은 이거야.

* **현재 단계의 5566은 과장**
* 그러나 **ultimate exact full-Bianchi branch에서 all-(m) envelope 자체가 원리적으로 불필요하다고 말할 수는 없음**

즉,

* **near-term reduced target**과
* **ultimate exact target**
  을 분리해야 해.

이 구분을 안 하면, 한쪽은 숫자 공포 마케팅이 되고, 다른 쪽은 근거 없는 낙관론이 된다.

---

## 4) reduced DOF 기준으로 다시 계산한 메모리

반론문이 쓴 메모리 모델은

[
{\rm Mem} \approx 8,N_{\rm snap},n^2 \quad {\rm bytes}
]

즉 `f64` dense matrix를 snapshot마다 하나씩 쌓는 `mats_flat` lower bound였지.
반론은 여기에 (N_{\rm snap}=500), (n=5566)을 넣어 124 GB라고 썼다. 

같은 공식을 **정직한 reduced DOF**에 넣으면:

| 상태공간 가정                                                        | DOF (n) | (500\times n^2\times 8) bytes | 대략 GiB |
| -------------------------------------------------------------- | ------: | ----------------------------: | -----: |
| reduced, (M=2), no massive-(\nu)                               |     531 |             (1.13\times 10^9) |   1.05 |
| reduced, (M=2), +130 massive-(\nu)                             |     661 |             (1.75\times 10^9) |   1.63 |
| reduced, (M=4), no massive-(\nu)                               |     901 |             (3.25\times 10^9) |   3.02 |
| reduced, (M=4), +130 massive-(\nu)                             |    1031 |             (4.25\times 10^9) |   3.96 |
| current full all-(m), (L_\gamma=25,L_\nu=15), no massive-(\nu) |    2551 |          (2.60\times 10^{10}) |  24.24 |
| current full all-(m), same +130 massive-(\nu)                  |    2681 |          (2.88\times 10^{10}) |  26.84 |
| rebuttal worst-case target                                     |    5566 |          (1.24\times 10^{11}) | 115.41 |

이 표에서 드러나는 건 두 가지야.

### 4.1 124 GB는 현재 단계에 대한 정직한 숫자가 아니다

맞아. 이건 과장이다.

### 4.2 그런데 `mats_flat`가 좋은 설계라는 뜻도 아니다

이건 더 중요하다.

* **1–4 GiB**는 “돌릴 수는 있는” 수준처럼 보일 수 있다.
* 하지만 이건 **dense matrix one family, one solver instance, one precision lower bound**에 불과하다.
* 여기에

  * 추가 operator family,
  * LU/factorization work arrays,
  * stage buffers,
  * output buffers,
  * 여러 (k)-mode batch,
  * debug/profile duplication
    이 붙으면 금방 2배, 3배, 4배로 뛴다.

즉 reduced target에선 catastrophic 124 GB는 아니지만, **아키텍처 자체가 장기적으로 잘못된 (O(N_{\rm snap}n^2)) scaling**이라는 평가는 여전히 맞다.

그리고 이건 solver-neutral한 얘기야.
SUNDIALS ARKODE도 RHS, Jacobian, preconditioner를 **user-supplied callback**으로 받는 구조라 giant `mats_flat` prestore를 요구하지 않는다. time-dependent pretabulated background는 내부에서 continuous fit/interpolation으로 evaluation하면 된다. 네 recombination/visibility data 흐름은 정확히 이 방식과 양립 가능하다. ([sundials.readthedocs.io][1])

---

## 5) 그러면 내 이전 평가는 어떻게 더 강해지나?

여기가 핵심이야.

### 이전 평가에서 약해져야 하는 부분

* “5566 → 124 GB라서 hybrid는 물리적으로 불가능”
  이런 식의 강한 문장은 **약해져야 한다**.
* 왜냐하면 5566 자체가 현재 단계엔 과장됐으니까.

### 그런데 더 강해지는 부분

오히려 결론은 더 강해진다. 이유는:

1. **나쁜 숫자를 빼도 결론이 남는다.**
   즉 내 비판이 “과장된 worst-case 숫자”에 의존하지 않는다는 뜻이다.

2. **문제의 본질이 solver choice보다 backend scaling이라는 점이 더 선명해진다.**
   reduced (n\sim 500\text{–}1000)에선 당장 메모리 재앙이 아니더라도, exact full-Bianchi branch로 갈수록 다시 폭증한다.
   그러니까 지금부터 callback/stage-assembly/sparse-Jacobian 방향으로 가야 한다.

3. **SymBoltz류 전략과도 더 잘 맞는다.**
   SymBoltz의 핵심은 approximation switching을 없애는 동시에, symbolic knowledge로 Jacobian과 sparsity를 자동화하고 full stiff equations를 implicit solvers로 푸는 데 있다. 그러니까 “approximation-free”의 바른 귀결은 **불필요하게 부풀린 DOF로 dense snapshots를 쌓는 것**이 아니라, **선택한 perturbative system을 정확히 두고 sparse/callback/structured linear algebra로 푸는 것**이다. ([arXiv][2])

즉 더 강한 판정은 이렇게 바뀌어.

> 5566 기반 124 GB 주장은 현재 단계엔 과장이다.
> 하지만 그걸 걷어내도, `mats_flat \sim N_{\rm snap}n^2` 백엔드는
> (a) 현재 reduced branch에서는 수 GB급 불필요한 overhead이고,
> (b) 장기 exact-Bianchi branch에서는 다시 폭증하는 구조다.
> 따라서 메모리 비판의 숫자는 고쳐야 하지만, **아키텍처 비판은 오히려 더 정직하고 더 강해진다.**

---

## 6) 그럼 hybrid vs pure IMEX 평가는 어떻게 수정되나?

여기서도 더 정교하게 가야 해.

### 수정 전의 너무 강한 문장

* “5566이니까 hybrid는 끝, IMEX가 답”

이건 과했다.

### 수정 후의 더 강한 문장

* **현재 reduced DOF 기준에선 hybrid도 당장 메모리 때문에 즉사하진 않는다.**
* 하지만 **formal order / heterogeneous error control / bespoke coupling** 문제는 그대로 남는다.
* 반면 **IMEX-ARK는 single-tableau, literature support, cleaner embedded estimator**라는 장점이 여전히 남는다. Kennedy–Carpenter ARK는 additive RK를 일반 composite method로 다루고, implicit-explicit ARK2 3–5차 schemes를 제시한다. 
* 따라서 **메모리 공포를 걷어낸 뒤에도**, pure IMEX-ARK를 1순위 reference branch로 두는 쪽이 여전히 더 설득력 있다.

즉 이제 논쟁의 무게중심은

* “메모리만 보면 hybrid는 불가능”
  에서
* “메모리를 정직하게 다시 계산해도, mainline 주력으론 pure IMEX가 더 clean”
  으로 이동한다.

이게 훨씬 강한 평가야.
왜냐하면 이건 **과장된 숫자 없이도 살아남는 결론**이니까.

---

## 7) 내 최종 판정

내 판정은 아주 명확해.

### 수용

* **5566 DOF를 현재 단계의 대표 숫자로 쓰는 건 과장**이다.
* 네 물리 범위를 반영하면 near-/mid-term reduced target은

  * (M=2): 531 / 661
  * (M=4): 901 / 1031
    쪽이 더 정직하다.
* 따라서 124 GB 메모리 비판은 **현재 단계 수치로는 철회/수정**해야 한다.

### 유지

* 그래도 `mats_flat \sim N_{\rm snap}n^2` 백엔드는 **안 좋다**.
* reduced branch에서도 수 GB급 lower bound가 나오고,
* exact full-Bianchi future branch에선 다시 10–100 GB대로 커질 수 있다.
* 따라서 **callback-based RHS/Jacobian assembly + sparse/structured linear algebra**로 가야 한다는 평가는 유지된다. ([sundials.readthedocs.io][1])

### 강화

* 이 수정 뒤에는 메모리 argument가 덜 선정적이면서 더 강해진다.
* 그리고 hybrid에 대한 비판도 **“메모리 공포”가 아니라 “formal order/estimator/back-end cleanliness”** 중심으로 재배열된다.
* 그래서 실무적으로는 여전히

  * **pure IMEX-ARK = mainline reference path**
  * **RODAS5P-centered hybrid = benchmark / backup path**
    가 맞다.

[1]: https://sundials.readthedocs.io/en/latest/arkode/Usage/User_supplied.html "2.4.4. User-supplied functions — Documentation for SUNDIALS  documentation"
[2]: https://arxiv.org/abs/2509.24740 "[2509.24740] SymBoltz.jl: A symbolic-numeric, approximation-free, and differentiable linear Einstein-Boltzmann solver"