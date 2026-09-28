---
title: "HTT 독립 연구 · 구현 감사"
subtitle: "제2권: native BASS, 충돌 · 편광, legacy 물리, MIO 통계와 심사 후속 이론"
author: "독립 원문 · 수식 · 소스 심사"
date: "2026년 9월 8일"
lang: ko-KR
fontsize: 11pt
geometry:
  - a4paper
  - margin=21mm
colorlinks: true
linkcolor: blue
urlcolor: blue
toc: true
toc-depth: 1
---

# 독립 판정과 제1권에 대한 보완

**HTT의 최신 후속 이론은 두 모의심사의 핵심 수학 지적에 상당 부분 대응한다. 실제 native BASS와 올바른 후기 충돌 커널도 존재한다. 그러나 관측 모형과 실험 명세는 아직 닫히지 않았고, 저장소의 일부 실제 실행 경로에는 물리적 결과를 바꾸는 오류가 남아 있다.** 따라서 가장 정확한 평가는 ‘실질적인 방법론 · 계산 자산을 가진, 여러 성숙도의 연구 계통’이다. 전 데이터의 통합 추론이나 일반 Bianchi Einstein-Boltzmann solver의 완성은 확인되지 않았다.

이번 심사는 내부의 PASS, exact, diagnostic, claim ceiling을 판정 근거로 쓰지 않았다. 정의 · 수식 · 소스 · 호출 경로와 해석적 반례를 기준으로 평가했다. 낮은 내부 등급도 올바른 결과를 기각하는 이유가 아니며, 높은 내부 등급도 실제 오류를 상쇄하지 않는다.

| 제1권의 판단 | 이번 추가 증거 | 유지 · 보완할 판단 |
|:--|:--|:--|
| 초기 충돌 블록에 성장 고유값이 있음 | 후기 orthogonal T/E 블록은 올바른 감쇠 고유값을 가짐 | 초기 경로의 오류를 후기 커널 전체로 확대하지 않는다 |
| 일부 exact/LOS 경로가 heuristic 계수에 의존 | 7,400줄 native 적분기와 실제 caller를 전문 읽음 | BASS 전체가 template 또는 skeleton이라는 평가는 부당하다 |
| 초기 log-likelihood 합산은 evidence가 아님 | 정규화된 Gaussian evidence, thermodynamic integration, bridge sampling 구현 존재 | 실제 evidence 알고리즘은 있다. 그것이 초기 우주론적 Bayes factor를 소급 검증하지는 않는다 |
| Q/O 방법론이 유망 | contraction fibre, 경계 안정성, post-review T1-T10을 추가 읽음 | 유효한 수학적 성과를 더 구체적으로 인정한다 |
| 단일 최신 파일을 기준으로 평가할 수 없음 | R3 원고 뒤 PR462-464가 별도 브랜치에서 수정 · 보완 | 보존된 원고의 미수정과 현재 이론의 미해결을 구분한다 |

**이 보고서 역시 모든 역사적 파일의 전수 정독 완료본은 아니다.** 제1권의 107개에 새로운 고유 Git blob 54개를 추가해 누적 161개를 전문 읽었다. 신규 전문의 합계는 1,495,052바이트이며, 부분 읽기 2건은 이 수에 넣지 않았다. 현재 브랜치 끝점 집합에서는 8,630개 중 150개를 전문 읽었다. 첨부 archive의 누적 전문 읽기는 제1권과 같은 20개 member다. 이 숫자는 정확성 점수나 연구 완성도가 아니다.

과학 코드 · CAS · solver · Monte Carlo · 관측 데이터 분석은 이번에도 실행하지 않았다. 원문 취득, Git metadata 처리, 해석적 검산과 보고서 제작만 했다. 아래 반례는 실행 로그와 구분되는 **소스에 대한 해석적 판정**이다. 실제 수치 영향과 수정 후 결과는 사용자가 지정한 Local Codex가 확인해야 한다.

# 실제 최신 연구를 읽는 방법

9월 8일 재확인한 182개 브랜치의 이름과 head는 제1권의 snapshot과 같았다. 기본 브랜치는 8월 20일의 코드 지점이고, 지정 handoff는 9월 7일 지점이다. 하지만 handoff tree 안에 모든 후속 연구 파일이 합쳐져 있는 것은 아니다. 일부 파일은 다음 별도 ref를 통해 읽어야 한다.

| 역할 | 고정 ref | 이번 읽기 |
|:--|:--|:--|
| 지정 handoff H | 5702024e… | native · 충돌 · legacy · 통계 소스, R3와 fibre, handoff 3문서 |
| PR462 직접 유도 | b4d04e62… | THEORY_RESULTS 전문 |
| PR463 활성 연구 계획 | 0e2d6e3a… | master · derivation · reuse contract · DAG 4파일 전문 |
| PR464 보완 연구 | fa86d940… | theory corrections · code/data map 2파일 전문 |

[H](https://github.com/cosmosapjw-quantum/htt_base/tree/5702024e06eff4979087f07f86ee7131d13961ac), [PR462 이론](https://github.com/cosmosapjw-quantum/htt_base/blob/b4d04e62d664997eb9e1858b6195c35e4ece3378/docs/research_program/post_review_20260907/THEORY_RESULTS.md), [PR463 master](https://github.com/cosmosapjw-quantum/htt_base/blob/0e2d6e3a890ae44303440e8534fb6080d1dac881/docs/research_program/referee_seeded_20260907/00_MASTER_PLAN_KO.md), [PR464 보완](https://github.com/cosmosapjw-quantum/htt_base/blob/fa86d940f6d954af554bae5b577d5eb465aa2ae1/docs/research_program/review_seeded_20260907/THEORY_RESULTS_AND_CORRECTIONS.md).

PR463은 기존 정리를 다시 증명했다고 세지 않고, M1_CMB_MODEL · M2_REDSHIFT_MODEL · M3_EXPERIMENT를 남은 과학 명세로 둔다. 이 상태 표시는 결론의 근거가 아니다. **실제 파일에도 primary statistic, 실제 low/high covariance, distance likelihood와 최종 실험 선택이 완성된 형태로 제시되지 않았다는 점**이 미완결 판정의 근거다. 반대로 master가 가리키는 이미 유도된 정리들을 또 미완료로 세는 것도 부당하다.

연구의 역사적 연속성은 강하다. 초기의 저다중극 · tilt · 운동학 · 적색편이 목표가 현재의 observable tensor, nuisance, frame, depth 연구로 이어진다. 그러나 같은 저장소에 남아 있는 legacy 수식, 별도 native solver, 최신 관측 방법론은 하나의 검증된 실행 체인이 아니다. ‘최신’은 파일 날짜 하나가 아니라 **과학적 역할별 ref와 실제 import · caller의 조합**으로 정의해야 한다.

# native BASS: 실질적인 solver와 실제 결함

## 인정할 성과

Ver2TierBIntegrator는 T/E/B, 중성미자 multipole, baryon/CDM 변수, residual mode와 source history를 함께 적분한다. 실행 entry point가 이 적분기에 도달하며 restart, checkpoint, 배경 보간, source extraction과 structured state contract도 존재한다. 이는 상당한 재사용 자산이다. packed operator의 basis-wise lowering은 원래 RHS가 옳다는 조건에서 합리적인 성능 최적화다. [native 소스](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/hierarchy/ver2_native_integrator.py), [실행 경로](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/runtime/ver2_execution.py).

이 긍정적 판정과 다음 오류는 동시에 성립한다. 아래 결함이 어떤 기존 그림 · JSON에 얼마의 영향을 주었는지는 각 producer의 solver flag와 source pin을 추적하고 로컬에서 재실행해야 알 수 있다.

## N01. 일부 IMEX 단계가 충돌 감쇠를 증폭으로 바꾼다

family operator가 제공하는 충돌 대각은 음수다. native 적분기는 이를 부호 변경 없이 읽어 일부 photon 성분을 $1+\Delta t\,d$로 나눈다. $d=-\lambda<0$인 감쇠 방정식에서는

$$
y'=-\lambda y,\qquad
y_{\rm BE}^{n+1}=\frac{y^n}{1+\Delta t\lambda},
\qquad
y_{\rm code}^{n+1}=\frac{y^n}{1-\Delta t\lambda}.
$$

$\Delta t\lambda=1/2$이면 올바른 backward Euler는 $2y^n/3$, 해당 단계는 $2y^n$다. stiffness나 허용오차만의 문제가 아니다. T/E quadrupole의 별도 2×2 solve는 올바른 부호 구조를 사용하므로 모든 성분을 같은 오류로 묶어서도 안 된다.

적용 범위는 signed diagonal을 받는 orthogonal IMEX 경로다. tilted 또는 scalar-metric 설정은 BDF로 우회하므로 이 반례를 모든 native 실행에 일반화하지 않는다. 또한 해당 대각은 초기 시각에 cache되고 후기 opacity에 맞춰 갱신되지 않는다. 부호 수정 뒤에도 고다중극의 시간 의존 충돌 계수는 별도로 고쳐야 한다. [대각 조립](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/hierarchy/ver3_layout_protocol.py), [operator 공급](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/los/family_backend_protocol.py).

## N02. 같은 적분 안에서 conformal time의 기준이 다르다

native background adapter는 주어진 배경의 conformal-time 배열을 그대로 쓰지 않고 $t=\int dN/H$, $\eta=\int dt/a$를 각각 0에서 재구성한다. 반면 opacity · matter · local-H 조회는 원래 eta_mpc를 사용한다. 입력 배경의 $\eta$ 원점만 이동해도 두 조회의 대응이 달라진다. 이는 단순 metadata 차이가 아니다.

배경 모듈의 자체 단위 convention을 쓰는 경우에는 $c$ 계수 차이도 존재한다. 최소 반례는 원점 불일치만으로 충분하다. 공통 epoch · 단위 · monotonic grid를 하나의 실제 변환으로 묶어야 한다. [배경 진화](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/background/evolution.py), [conformal-time contract](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/ver3_contracts.py).

## N03. 일반 Bianchi geometry의 시간 진화가 닫히지 않는다

읽은 배경 경로는 H와 다섯 shear 성분을 진화시키지만 초기 geometry를 반복 전달한다. native tetrad adapter는 anisotropic Ricci를 초기 값으로 유지하며 gamma_AB도 출력마다 항등행렬로 설정한다. homogeneous Lie-algebra의 좌표 구조상수가 고정이라는 사실은 orthonormal curvature가 고정임을 뜻하지 않는다. 등방적으로 팽창하는 curved FRW만으로도

$$ {}^{(3)}R=6k/a^2 $$

이므로 반례가 된다. 제한된 flat Type-I 활용 가능성은 남지만, 일반 all-type Einstein-consistent evolution으로 인정할 수 없다.

같은 hierarchy의 curvature lift는 문서상 차원이 $L^{-2}$인 Ricci와 multipole의 곱을, $L^{-1}$인 expansion rate와 multipole의 곱에 그대로 더한다. 보상 길이 또는 별도 무차원화가 구현 · contract에 없다. 또 homogeneous tensor components라는 이유로 공간 공변미분을 0으로 두지만 일반적으로

$$
D_c T_{ab}=-\Gamma^d{}_{ac}T_{db}-\Gamma^d{}_{bc}T_{ad}
$$

가 남는다. 별도의 residual operator까지 전부 0이라고 판정한 것은 아니다. 여기서 기각하는 것은 **읽은 native hierarchy 경로의 일반 물리적 정당화**다. [terms](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/hierarchy/terms.py), [hierarchy RHS](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/hierarchy/hierarchy_rhs.py).

## N04. 추가로 확인한 실제 경로의 오류

| 항목 | 소스에서 확인한 동작 | 과학적 영향 · 범위 |
|:--|:--|:--|
| scalar metric source | zero-opacity 또는 explicit-only에서 full RHS와 explicit RHS가 같은 배열을 공유한 뒤 둘에 source를 더함 | photon에 $2S$, neutrino에 $S$가 되는 해석 반례 |
| photon B 입력 | collision auxiliary 생성 caller가 진화 중인 photon_B를 넘기지 않음 | B state가 존재해도 해당 collision 입력은 0으로 대체 |
| 편광 transport | T/E/B를 같은 spin-0 photon RHS로 처리 | 이 경로만으로 spin-2 transport · E/B coupling을 입증할 수 없음 |
| rapidity seed | rapidity를 beta 인자로 그대로 전달 | $r$ 대신 $\tanh r$가 필요. 유효한 $r\ge1$도 거부될 수 있음 |
| cutoff campaign | config를 다시 만들면서 scalar metric/streaming flag를 누락 | $\ell_{\max}$만 바꾼 수렴 비교가 아니라 방정식도 바뀔 수 있음 |

[seed rule](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/perturbation/tilted_seed_rule.py), [native와 campaign caller](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/runtime/ver2_execution.py).

Tier-A 비교 경로도 실제 적분을 하지만 같은 hierarchy operator를 공유한다. 두 경로의 일치는 regression · 적분 구현 증거이고, 독립 물리 oracle과의 일치를 자동 의미하지 않는다. raw brightness의 팽창 희석과 dimensionless temperature source extraction의 연결도 추가로 확인해야 할 문제다. 이 마지막 항목은 완전히 추적된 정규화 반례가 아니라 **미확인 bridge**로 남긴다.

# 충돌 · 편광 · boost의 경로별 판정

## C01. 후기 T/E Thomson 블록은 살려야 한다

후기 PSTF와 polarization 구현의 quadrupole 충돌 블록은

$$
\frac{d}{d\eta}
\begin{pmatrix}\Theta_2\\E_2\end{pmatrix}_{\rm coll}
=\Gamma_T
\begin{pmatrix}
-9/10&-\sqrt6/10\\
-\sqrt6/10&-2/5
\end{pmatrix}
\begin{pmatrix}\Theta_2\\E_2\end{pmatrix}.
$$

고유값은 $-\Gamma_T,-3\Gamma_T/10$이다. 이 정상적인 커널과 N01의 적분 단계 오류는 별개다. 선형 편광 convention 아래 문헌의 충돌식과 맞으며 monopole 보존 · 고다중극 감쇠도 유효한 자산이다. [PSTF 구현](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/collision/thomson_pstf.py), [polarization 구현](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/collision/polarization.py), [Pontzen-Challinor, 식 55](https://arxiv.org/html/0706.2075v2).

## C02. B 충돌과 축방향 E/B boost에는 독립적인 반례가 있다

electron-frame의 정확한 zero-tilt 분기는 nonzero B 입력에도 B collision을 0으로 반환한다. tilted helper의 B quadrupole damping은 $-2\Gamma_T B_2/5$다. 선형 Thomson의 기존 B multipole는 모든 $\ell\ge2$에서 $-\Gamma_T B_{\ell m}$로 감쇠해야 한다.

또 축대칭 E/B helper는 $B'_{\ell0}=B_{\ell0}+6\beta E_{\ell0}/(\ell+1)$를 강제한다. 축대칭 pure-E 하늘을 그 대칭축 방향으로 boost해도 자오면 반사 대칭은 유지되므로 parity-odd $B_{\ell0}$를 만들 수 없다. 순수 $E_{20}$에서 $B'_{20}=2\beta E_{20}$를 만드는 코드가 직접 반례다. [electron frame](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/collision/electron_frame.py), [tilted E/B](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/collision/tilted_eb_mixing.py).

온도 boost helper의 axis fast path도 $+\hat x,+\hat y,+\hat z$를 동일한 고정 component recurrence로 처리한다. isotropic monopole에서 세 방향에 같은 dipole vector를 만들므로 회전 공변성을 만족하지 않는다. **이 발견은 BASS의 해당 helper에 대한 것이다. PR463이 선택한 별도의 local-observer boost donor까지 같은 오류라고 판정하지 않는다.** [BASS boost helper](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/hierarchy/boost_kernel.py).

## C03. Flux factor만으로 finite-tilt collision이 완성되지 않는다

angular 경로는 stationary Mueller operator에 $\gamma_e(1-\boldsymbol v_e\cdot\boldsymbol e)$를 곱한다. 이 flux factor는 필요하지만 aberration, Doppler/frequency 변환과 electron-frame screen 변환을 대신하지 않는다. 읽은 native caller에도 선행 Lorentz sky/screen 변환이 없다.

전자와 공운동하는 isotropic blackbody는 충돌 null mode다. 다른 frame에서 그 bolometric intensity는

$$
I(\boldsymbol e)=
\frac{I_*}{[\gamma_e(1-\boldsymbol v_e\cdot\boldsymbol e)]^4}
=I_*[1+4\boldsymbol v_e\cdot\boldsymbol e+O(v_e^2)].
$$

하지만 해당 stationary kernel은 lab dipole를 이미 1차에서 감쇠시킨다. 물리적 null mode를 보존하지 못한다. [tilted species 구현](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/species/tilted.py), [Portsmouth-Bertschinger의 공변 편광 전달](https://arxiv.org/pdf/astro-ph/0412094).

## C04. Angular screen과 quadrature 검증은 보강해야 한다

정확히 반대 방향인 두 ray에서는 코드가 incoming/outgoing screen을 서로 독립적인 산란 기준으로 고른다. octahedral grid에서 $+\hat z$ 입력만 $I=Q=1$로 두면 $-\hat z$ source는 $(Q,U)=(1/4,0)$이다. 그 outgoing screen만 $\pi/4$ 회전하면 같은 물리 source는 $(0,-1/4)$로 표시되어야 하지만 해당 분기 식은 계속 $(1/4,0)$를 준다. 기존 홀수 방위각 grid 시험은 정확한 antipodal pair를 피한다.

반면 비공선 Mueller map의 Stokes-cone 보존 구조는 가치가 있다. 공통 양의 normalization을 제외하면 $I'^2-Q'^2-U'^2=4\mu^2(I^2-Q^2-U^2)$이며, 양의 weight를 가진 source 합도 cone 안에 있다. 이를 보존하면서 screen 분기를 고치는 편이 전면 재작성보다 낫다.

또 weight 합이 $4\pi$라는 검사만으로 isotropic null mode를 인증할 수 없다. 한 방향에 weight $4\pi$를 놓으면 이 검사에는 합격해도 $KI=3I/2$다. 최소한 $\sum_iw_i e_i e_i^T=(4\pi/3)I$ 같은 모멘트 조건과 해당 harmonic 곱에 필요한 정확도가 필요하다. 이것은 모든 근사 quadrature를 기각하는 주장이 아니라 ‘정규화 검사만으로 exactness를 선언할 수 없다’는 판정이다.

## C05. 초기 Rust의 별도 잔존 문제

이번에 읽은 세 Rust 충돌 파일은 root와 H에서 같은 blob이다. no-polarization quadrupole damping의 $-\Gamma_T$는 실제 Thomson redistribution을 포함한 $-9\Gamma_T/10$와 다르다. 다른 polarization 파일은 MB의 $G_0,G_2$와 spin-E 표기를 일관되게 해석하기 어렵다. theta-fourth-power quadrupole helper는 scalar monopole variance만 있어도 nonzero quadrupole source를 반환한다. 등방 scalar shift는 quadrupole angular projection을 만들 수 없다.

이 파일들이 남아 있다는 사실과 모든 최신 결과가 이 파일을 소비한다는 사실은 다르다. 기존 결과별 실제 caller를 확인해야 한다. [Rust quadrupole](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/src/solver/pstf_primary/collision.rs), [theta-fourth source](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/src/collision/thomson.rs), [Ma-Bertschinger 원문](https://arxiv.org/abs/astro-ph/9506072).

# 오래된 물리 원고의 정량 주장

ch01 · ch05 · ch07 · ch11을 이번에 전문 읽었고, ch05는 초기 추적 버전과 H의 전체 diff도 대조했다. 6월의 일부 heading · 조건부 표현 수정 뒤에도 다음 식들은 남아 있다. 이를 최신 Q/O 정리와 혼합해서 정당화할 수 없다.

## L01. 온도 4차 평균의 angular coefficient가 틀리다

$\mu=\cos\theta$와 $P_2$를 쓰면

$$
\langle\mu^2P_2(\mu)\rangle_{S^2}=\frac{2}{15},
\qquad
\int_{-1}^1\mu^2P_2(\mu)\,d\mu=\frac4{15}.
$$

따라서 $\langle(1+A\mu+QP_2)^4\rangle$에서 $A^2Q$의 계수는 $8/5$이며 원고의 $16/5$가 아니다. 또한 $\langle x^2P_2(z)\rangle=-1/15$이므로 별도 방향의 dipole $Wx$가 있으면 $W^2Q$ 항 $-4W^2Q/5$가 남는다. 서로 다른 m의 cross term이 모든 차수에서 사라진다는 명제는 틀리다. $Q^3$의 $8Q^3/35$ 항도 생긴다. binomial coefficient만 맞는 것은 angular projection의 검증이 아니다. [ch05](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/docs/manuscript/ch05_teff_corrections.tex).

bolometric $T_{\rm eff}=(\rho/a_R)^{1/4}$ 자체는 유효한 정의다. 그러나 서로 다른 blackbody의 합을 하나의 온도로 표시했다고 그 스펙트럼까지 정확한 Planck 형태가 되는 것은 아니다. 방향 · 주파수 정보를 버리는 단계와 원래 intensity hierarchy를 구분해야 한다. [Khatri-Sunyaev-Chluba의 blackbody mixing](https://arxiv.org/abs/1205.2871).

## L02. 중성미자 ‘CMB 사중극 지배율’은 관측 응답과 연결되지 않는다

ch05는 photon · neutrino quadrupole moment 제곱에 에너지밀도 · degeneracy를 곱해 약 98%의 지배율을 제시한다. 그러나 관측 CMB 온도는 광자 intensity에서 나오며, 중성미자는 metric과 photon evolution을 통해 간접 작용한다. 필요한 분해는 광자 관측량까지의 response와 cross term을 포함해야 한다.

일반적으로 $a_{2m}=\sum_s a_{2m}^{(s)}$라면 power에는 $\sum_{s,t}\langle a_{2m}^{(s)}a_{2m}^{(t)*}\rangle$가 있다. species moment 제곱의 양의 합을 바로 CMB 기여율로 읽을 수 없다. 원고의 비율 정의는 그러한 response를 제공하지 않는다. 따라서 ‘중성미자가 대부분을 설명한다’는 **제시된 정량 귀속은 미입증**이다. 중성미자 anisotropic stress의 물리적 중요성 자체를 부정하는 판정은 아니다.

## L03. 상태 오차와 관측 power 오차를 동일시할 수 없다

ch11의 상태 오차는 제곱 상대 norm이다. 관측 amplitude $a=A u$라면

$$
\epsilon_{\rm state}=\frac{\|\Delta u\|^2}{\|u\|^2},
\qquad
\frac{\|\Delta a\|}{\|a\|}
\le\frac{\|A\|\|u\|}{\|Au\|}\sqrt{\epsilon_{\rm state}}
\equiv\delta.
$$

그때 power의 상대 오차 상계는 $2\delta+\delta^2$다. 동일한 백분율로 옮길 수 없다. source cancellation이나 작은 분모 때문에 앞의 관측 조건수가 커질 수도 있다. $\ell_{\max}=2$로 자른 collisionless neutrino가 일반적으로 정확하다는 주장도 finite-k free streaming의 상위 multipole 생성과 맞지 않는다. [ch11](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/docs/manuscript/ch11_error_hierarchy.tex).

## L04. 물리적 선택규칙과 evidence 논증도 다시 써야 한다

| legacy 주장 | 독립 판정 |
|:--|:--|
| vorticity가 일반적으로 $\ell\pm1$을 직접 결합 | 순수 회전 generator는 같은 $\ell$ 안에서 작용. 비선형 hierarchy의 acceleration · shear coupling과 구분 필요 |
| tensor mode에 vector vorticity/shear 비율을 적용해 강하게 배제 | mode-specific 관계의 범위를 벗어남. regular tensor와 vector의 제약은 같지 않음 |
| likelihood가 쓰지 않는 독립 parameter도 prior-volume Occam penalty 발생 | 정규화된 독립 prior이면 $\int L(\theta)\pi(\theta)\pi(\phi)d\theta d\phi=Z_\theta$ |
| 양의 표본만으로 beta=0의 Savage-Dickey Bayes factor 산출 | beta=0을 포함하지 않는 log-uniform prior에서는 해당 nested-null density ratio를 적용할 수 없음 |
| 임의 beta(z) 곡선의 적합이 global tilt 진화의 검증 | 동역학 · selection · window response가 따로 필요 |

[ch07](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/docs/manuscript/ch07_results.tex), [비선형 복사 hierarchy](https://arxiv.org/abs/astro-ph/9808163), [Saadeh 등의 mode별 Bianchi 제약](https://arxiv.org/abs/1605.07178).

2026년 closure 문헌도 ‘고차 closure는 전부 불안정’이라는 포괄 명제를 지지하지 않는다. Gnedin-Katz가 배제한 범위에는 pressure에 명시적으로 의존하지 않는 특정 local second-order closure가 있다. pressure를 보존했다는 사실만으로 HTT closure의 안정성이 증명되는 것도 아니다. 실제 closure의 hyperbolicity · realizability · 충돌 안정성 · 관측 오차를 각각 확인해야 한다. [Gnedin-Katz, 2026년 8월 개정본](https://arxiv.org/abs/2603.22400).

# Tensorized MES와 MIO 통계의 연결

## S01. 최신 이론의 tensor화는 실질적이다

최신 Report A와 post-review는 관측 온도 tensor Q/O와 물리적 congruence shear · vorticity · acceleration · frame velocity를 구분한다. MES의 radial constraint, tensor shape · orientation · parity, response-constrained feasible set을 함께 다루려는 설계는 유효하다.

특히 post-review는 background expansion을 norm 이전에 소거해 명시된 1차 geodesic collisionless 모형 안에서

$$
\sigma_{ab}=-\dot\vartheta_{\langle ab\rangle}
-D_{\langle a}\vartheta_{b\rangle}
-\frac37D^c\vartheta_{abc}
$$

를 얻는다. gradient-to-STF2 contraction의 $TT^*=(7/5)I$를 이용한 sharper coefficient도 맞는다. 이에 따른

$$
\frac{\|\sigma\|}{\Theta}
\le\frac{\epsilon_1}{3}+\frac{\epsilon_2}{3}
+\frac{\epsilon_3}{\sqrt{35}}
$$

는 **그 문서의 derivative envelopes를 추가한 모형 내부 결과**다. 한 관측자의 정확한 multipole amplitude에서 해당 derivative 가정을 얻은 것이 아니다. $\epsilon\sin(kx)$의 작은 amplitude와 커지는 derivative가 그 차이를 보여 준다. 이 정리의 잠재력은 무조건적 관측 상한보다, 가정별 identified set의 차이를 정량화하는 데 있다. [PR463 직접 유도](https://github.com/cosmosapjw-quantum/htt_base/blob/0e2d6e3a890ae44303440e8534fb6080d1dac881/docs/research_program/referee_seeded_20260907/01_DERIVATIONS_AND_REVIEW.md).

제1권에서 발견한 legacy MES의 상계 순서 검사 · normalization · 미식별 방향의 유한 상계 문제는 별도 consumer 문제로 남는다. 최신 이론이 옳다고 구형 consumer까지 자동 교정되는 것은 아니다.

## S02. MIO에서 같은 measure specification은 같은 귀무분포가 아니다

mio_joint_measure는 weights · pairing · depth policy를 동일하게 적용한다. 그러나 reference-scale null은 component별 독립 Gaussian draw이며 실제 joint dependence를 받지 않는다. 같은 함수를 썼다는 사실만으로 귀무분포가 맞지는 않는다.

한 row와 두 component, RAW · unpaired · 단위 weight를 생각하자. 실제 귀무분포가 $x_1=x_2=Z$, $Z\sim N(0,1)$이면 $F_{\rm obs}^2=2Z^2$다. 코드는 $F_{\rm null}^2=Z_1^2+Z_2^2\sim\chi_2^2$를 만든다. 한 row의 MAD는 0이므로 scale check도 이 경우를 배제하지 않는다. 무한 null-bank 극한에서

$$
p=e^{-Z^2},\qquad
\Pr(p\le\alpha)=2\{1-\Phi(\sqrt{-\log\alpha})\},
$$

이며 이는 $\alpha$와 다르다. component를 $|Z|$로 바꿔 nonnegative 입력으로 만들어도 F의 같은 반례가 유지된다. 이는 실제 자료에서 측정한 오검출률이 아니라, API가 허용하는 입력에 대한 analytic calibration 반례다.

추가로 paired Pi는 pair 내부의 앞 row에서 뒤 row를 뺀다. 값 $(3,1)$을 순서만 바꾸면 $+2$가 $-2$가 된다. pair ID만으로는 contrast의 방향이 정의되지 않는다. 의미 있는 before/after 또는 source/reference 역할이 필요하다. RAW가 아닌 depth-demeaned unpaired Pi는 bin별 합이 0이므로 항상 0인 별도 퇴화도 있다.

null 표준편차가 $10^{-9}$보다 작으면 무조건 퇴화로 거부하는 절대 threshold는 단위 rescaling에 따라 동일한 rank 실험의 성공 · 거부를 바꿀 수 있다. 이 모듈을 tensorized MES의 보편적 calibration engine으로 채택하기 전에 actual joint law · pair 역할 · scale-aware numerical policy를 고정해야 한다. [MIO 원문](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/src/common/mio_joint_measure.py).

sign-flip의 exactness도 해당 변환군에 대한 귀무분포의 불변성을 요구한다. component 이름, calibration label 또는 symmetric-looking histogram만으로는 충분하지 않다. [Canay-Romano-Shaikh의 symmetry 조건](https://ivancanay.com/papers/randomization-tests-symmetry-2017.pdf).

## S03. Information gain · joint survey · weight의 의미를 구분해야 한다

| 실제 구현 | 유효한 부분 | 추론으로 확대할 때 빠지는 내용 |
|:--|:--|:--|
| mes_information_gain | diagonal bound와 branch bound의 비율 · 비교 | Fisher/KL 정보량이나 joint confidence coverage는 아님 |
| JointSurveyHierarchy | covariance · selection · calibration · held-out 요구사항의 schema | status string이 채워졌다고 conditional independence가 성립하지 않음 |
| BulkFlowLikelihood | 명시된 precision model의 정규화된 Gaussian 우도 | selection/inclusion weight가 실제 precision인지 별도 근거 필요 |
| Cartesian cube prior | 정상적인 proper prior | 회전 불변 prior는 아님. 약한 방향의 posterior는 prior geometry에 민감 |

두 bound 중 작은 값을 택하는 것은 기술적 비교로는 가능하다. 각각의 pointwise confidence level을 선택 후에도 그대로 붙이려면 simultaneous calibration이 추가로 필요하다. 현재 ratio 함수가 그 자체로 잘못된 산술을 한다는 판정은 아니다.

BulkFlowLikelihood의 weight-normalized Gaussian도 무조건 잘못된 우도는 아니다. 같은 고정 weights를 사용하는 모형 사이에서는 일부 정규화 상수가 Bayes factor에서 상쇄될 수 있다. 문제는 inverse selection weight를 ‘같은 독립 측정을 여러 번 했다’는 precision으로 해석하는 데 있다. 이것은 PR462-464도 이미 지적한 문제이며 이번에 독립 소스로 확인했다. [bound ratio](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/htt/htt/statistics/mes_information_gain.py), [joint survey](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/htt/htt/infer/joint_survey_hierarchy.py), [bulk-flow likelihood](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/src/common/bulkflow_likelihood.py).

## S04. 실제 Bayesian evidence 자산도 있다

coherent_evidence는 $y_i|\mu\sim N(\mu,\sigma^2)$, $\mu\sim N(m_0,\tau^2)$의 정확한 evidence

$$ Z=N\!\left(y;m_0{\bf1},\sigma^2I+\tau^2{\bf1}{\bf1}^T\right) $$

와 thermodynamic integration · bridge sampling을 구현한다. power posterior와 normalized prior를 사용하며, integration Monte Carlo 오차와 ladder quadrature bias도 구분한다. 이 정도의 구현을 단순 evidence 이름표라고 평가해서는 안 된다.

이는 미래의 low/high joint Gaussian 모형에서 normalizer · prior sensitivity · sampling 검증을 재사용할 만한 자산이다. 실제 우주론적 likelihood나 제1권의 초기 $\log B$ 결과가 검증됐다는 증거는 아니다. 이번에는 소스를 판독했으며 새 sampling 결과를 만들지 않았다. [coherent evidence](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/src/common/coherent_evidence.py).

# Q/O 형태 연구의 객관적 잠재력

## P01. 기존 cyclic chart 밖에서도 정확한 부분정보가 남는다

단위 STF2 $q$를 고정하고 $L_q o=o:q$, $M_q=I+6q^2/5$라 하자. 최신 fibre 문서는

$$
L_qL_q^*=M_q/3,\qquad
R_q=\mathcal B_qM_q^{-1},\qquad
\eta=3v^TM_q^{-1}v
$$

에서 다음을 정확히 도출한다.

$$
\{o:\|o\|=1,\ L_qo=v\}=
\begin{cases}
\varnothing,&\eta>1,\\
\{R_qv\},&\eta=1,\\
R_qv+\sqrt{1-\eta}\,S^3_{\ker L_q},&0\le\eta<1.
\end{cases}
$$

kernel의 차원은 4이므로 unit fibre는 3-sphere다. $q$에 중복 고유값이 있어도 $M_q$는 positive definite다. 따라서 LRS · 축대칭 등 cyclic decoder가 실패하는 하늘에서도 **축약 관측량에 양립하는 octupole 집합**을 제공할 수 있다. 이것은 전 strata의 full morphology 복원이나 물리적 beta 측정과는 다른, 분명한 성과다.

또

$$ \|O:Q\|^2\le\frac35(Q:Q)(O:O) $$

의 상수는 sharp하다. saturation 근처 fibre radius는 $\sqrt{1-\eta}$이므로 matrix condition이 좋더라도 집합의 경계는 square-root sensitivity를 갖는다. 보완 Hausdorff 문서도 이를 올바르게 구분한다. [fibre 원문](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/docs/research_reports/notes/QO_CONTRACTION_FIBRE_GEOMETRY_20260907.md), [Hausdorff 보완](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/docs/research_reports/notes/QO_FIBRE_HAUSDORFF_STABILITY_20260907.md).

## P02. 심사의 3/7 결과는 이미 정확한 분포와 대립으로 확장됐다

post-review는 fixed Q 아래 구면적인 7차원 Gaussian octupole에서

$$
f_B=\frac{\|P_QO\|^2}{\|O\|^2}\sim\mathrm{Beta}(3/2,2),
\qquad \mathbb E f_B=3/7
$$

를 유도하고, 지정된 boost mean이 있을 때 singly noncentral beta로 확장한다. LS covariance의 factor 3과 trace 범위도 올바르게 처리한다. 이것은 이번 감사의 새 발견으로 다시 세면 안 되는 기존 연구 성과다.

특히 SO(3) isotropy만으로 uniform $S^6$ shape law를 얻을 수 없다는 구분이 중요하다. 이 ideal Beta는 synthetic oracle이며 실제 masked/noisy map의 p-value를 바로 주지 않는다. 실제 관측에서는 joint Q/O uncertainty를 통해 fibre · projection · 외부 방향을 평가해야 한다.

## P03. 무제한 nuisance의 rank와 실제 정보는 다르다

PR462-464의 bounded cost, joint Gaussian conditioning, soft-mask 결과는 수학적으로 실질적이다. 예를 들어

$$
\min_{Kh=d}h^TS^{-1}h=d^T(KSK^T)^+d
$$

는 $d\in\operatorname{Im}K$에서만 유효하고, 바깥에서는 비용이 무한대다. 두 radius-R nuisance 상태의 차이는 radius-2R까지 가능하다. Gaussian nuisance와 측정된 high modes가 있으면 Schur complement와 그 high-mode marginal likelihood까지 필요하다.

또 soft-mask path에서 $K_\epsilon=O(\epsilon)$인데 양의 작은 $\epsilon$에서 full row rank가 유지될 수 있다. 무제한 nuisance는 여전히 출력을 지울 수 있지만, bounded cancellation 비용은 커지고 stochastic contamination은 작아진다. 이 구분은 ‘rank가 0이면 관측 정보도 0’이라는 과도한 해석을 실제 정량 연구로 바꿀 수 있다. [post-review 이론](https://github.com/cosmosapjw-quantum/htt_base/blob/b4d04e62d664997eb9e1858b6195c35e4ece3378/docs/research_program/post_review_20260907/THEORY_RESULTS.md).

# 두 모의심사에 실제로 대응했는가

R1은 대폭 수정, R2는 research article의 positioning · 선행연구를 이유로 재구성을 요구했다. 두 심사자가 주장하는 독립 실행을 이번 실행 증거로 합산하지 않았다. 심사 원문의 검산 ZIP 링크만으로 그 코드와 로그를 읽었다고도 하지 않는다.

| 원래 요구 | 현재 후속 이론의 대응 | 독립 판정과 남은 일 |
|:--|:--|:--|
| R1 · R2: 기여도와 multipole-vector 대비 | PR463에 focused methods 방향과 기존 완전 표현 인정 | 방향은 타당. 동일 입력 · 조건에서의 계산 · 오차 · utility 비교가 필요 |
| R1 · R2 M1/M2: 최소 L=10, block count | PR462-464에서 명시적으로 유도 | 해당 axial continuum 결과는 해결. every-direction · finite-pixel로 확대 금지 |
| R1: deterministic delta | post-review에서 사후 slack 허용으로 교정 | 해결. 실제 error enclosure는 별도 미완 |
| R1: cancellation을 보존한 MES | sharper STF contraction까지 유도 | 명시된 1차 모형 내부에서 해결. 관측 derivative premise는 미입증 |
| R2 M3/M4: 규모 · dipole 귀속 | 조건별 규모와 귀속의 중요성을 인정 | 실제 product와 가정에 맞춘 비교표 · 추론이 M1/M3에 필요 |
| R2 M5: 한 하늘과 all-observer gap | amplitude-only inference 불가와 kernel null을 명시 | 논리적 해명은 상당히 해결. 단일 하늘에서 일반 전제를 검증한 것은 아님 |
| R2 M6: cyclic 경계 · 물리적으로 중요한 하늘 | fibre · Hausdorff 결과, 원 tensor 보존 | 부분집합 fallback은 유효. 실제 null의 failure rate · coverage는 미실행 |
| R2 M7: accidental projection 3/7 | 정확한 Beta · covariance · shape range | 해결. 실제 map의 attribution 검정은 별도 |
| R1: high-mode nuisance의 물리적 크기 | bounded/stochastic/data-conditioned 4모형 | 수학은 마련됨. 실제 S · joint covariance · positivity · tail 선택은 M1 |
| R1: source와 velocity Jacobian · finite beta | 분리하고 monopole 고차항까지 명시 | 이론 대응 완료. 선택한 observation pipeline에 구현 · 검증 필요 |
| R1: 하나의 완결 synthetic experiment | bias · coverage · size · power · abstention 계획 | 설계 선택과 수치 결과는 아직 없음 |
| R1 · R2: 유한 18사례의 재현 · 의미 | 과거 source disposition과 physical evidence를 구분 | source replay는 성과. 완결된 finite-pixel inference는 아님 |
| R2: 문헌 identity · 표준 결과 귀속 | Katz-Weeks/Land-Magueijo 오기를 교정 | 실제 교정은 타당. 전체 focused 원고의 novelty 비교는 미완 |
| R2: 분량 · register · 코드 공개성 | 55쪽 해설판 보존, 별도 연구논문 계획 | 해설판의 완료와 새 논문 출판 준비는 다른 상태 |

**‘데이터만 붙이면 두 심사에 모두 답할 수 있다’는 판정은 아직 불가하다.** 핵심 수학 대응은 상당히 진행됐지만, M1-M3에 남은 항목은 단순한 코딩이나 자료 로딩이 아니라 통계 모형과 실험 선택이다. 동시에 이미 해결된 L=10 · slack · Beta · bounded nuisance를 다시 미해결로 세어 작업을 늘릴 이유도 없다.

심사본 자체도 무비판적으로 채택하면 안 된다. R2가 Katz-Weeks로 적은 astro-ph/0502574는 다른 문헌이며, Katz-Weeks는 astro-ph/0405631이다. generic Bianchi I/V/VII0를 모두 축대칭으로 묶는 것도 LRS subset으로 좁혀야 한다. 조건수의 Gaussian Monte Carlo 분위값을 모든 관측 pipeline의 threshold로 쓰는 것은 정당하지 않다. [Katz-Weeks 원문](https://arxiv.org/abs/astro-ph/0405631), [Copi-Huterer-Starkman의 multipole-vector 표현](https://arxiv.org/abs/astro-ph/0310511).

# 웹 문헌 대조와 신규성

2026년 4월 14일 출판된 Chluba-Ravenni의 boost operator 논문은 중요한 근접 선행연구다. spin · Doppler weight · frequency dependence를 포함한 boost, low multipole와 primordial dipole의 한계, moving-electron Thomson corrections를 다룬다. 따라서 ‘저다중극만으로 primordial dipole를 일반적으로 분리할 수 없다’거나 boost recurrence 자체를 HTT의 독창적 기여로 제시하기 어렵다. HTT의 비교 대상은 **선택한 처리 연산자 · 물리적 nuisance 제약 · shape 보존 · 불확실성의 결합에서 무엇을 추가하느냐**다. [출판본](https://academic.oup.com/mnras/article/548/3/stag698/8653927), [2025년 preprint의 관련 유도](https://arxiv.org/html/2505.02080v1).

이번 대조로 첫 발견 · 유일한 방법이라는 신규성을 인증한 것은 아니다. 기존 multipole-vector의 완전 표현과 Bianchi polarized transport 문헌을 고려하면, Q/O 표현 자체 또는 편광 tower의 존재만으로 강한 novelty는 성립하지 않는다. 반면 정확한 contraction-fibre geometry, 처리 후 response의 bounded-nuisance 비용, 같은 자료의 high-mode conditioning을 하나의 검증 가능한 방법으로 묶는 방향에는 독립적인 논문 잠재력이 있다. 이는 심사의 내부 추천이나 repo의 ceiling을 채택한 결론이 아니라, 읽은 결과의 수학적 내용과 선행연구 범위를 비교한 평가다.

closure · boost 문헌의 ‘최신성’도 제품 가용성 또는 현 프로젝트의 구현 완료와 다르다. 이번 외부 문헌 검토는 관련 핵심 논문 · 절에 대한 대조이며 분야 전체의 모든 2026년 논문을 전수 읽은 문헌고찰은 아니다.

# 자산 재사용과 기존 DAG에 연결할 수정 우선순위

## 데이터 통합은 ‘모두 곱하기’가 아니라 공통 생성모형이다

owner inventory의 179 bundle · 456,933 path · 약 1.499TB는 소유 자료의 metadata다. 이번에 workstation의 원시 자료를 모두 읽거나 실제 보유 상태를 재검증한 수치가 아니다. PR463-464는 이 차이를 이미 잘 구분하고 있다. 다음의 제한은 data admission의 실제 의미를 정하기 위한 것이다.

| 자산 | 가장 경제적인 재사용 | 통합 시 보존할 의존성 |
|:--|:--|:--|
| PR3 SMICA · component maps · FFP10 | 기존 alm/STF · mask · null bookkeeping 활용 | component map들은 같은 cosmic sky. 파일 수와 독립 null ID 수를 구분 |
| WMAP · Cosmoglobe · BeyondPlanck | instrument · foreground sensitivity | 같은 하늘과 공유 입력 · prior. posterior draw는 독립 null sky가 아님 |
| CF4 원 distance/group | 기존 raw adapter와 calibration/group 필드 | reconstruction grid를 독립 Gaussian 관측으로 바꾸지 않음 |
| Carrick · CORAS · Lilow | 공유 구조 · reconstruction 가정의 sensitivity | 서로 독립 anchor로 likelihood를 곱하지 않음 |
| DESI catalogue · random · mock | ingestion · per-cap metadata 재사용 | window와 self-normalization response, coordinate frame · selection · LSS covariance |
| ACT lensing · 광학 shear · 기타 거리 자료 | 실제 측정 kernel에 맞춘 보조 분석 | kappa · lensing shear를 temperature 또는 congruence shear로 대체하지 않음 |
| 첨부 kinetic · Thomson · optics donor | 제한된 물리 oracle과 core primitive | 제1권에서 확인한 constraint · normalization · 관측조건 한계 유지 |

전 데이터를 하나의 연구프로그램 아래 관리할 수는 있다. 그러나 **현재 보유한 모든 product가 같은 parameter에 식별 정보를 주는 것은 아니다.** 공통 parameter와 shared nuisance가 정의된 channel은 joint law로 결합하고, 중복 reconstruction과 product control은 sensitivity로 사용하며, 필요한 observable이 없는 product는 제외 이유를 남겨야 한다. 이 방식이 많은 자료를 최대한 쓰면서도 허위 독립 표본을 만들지 않는 길이다. [PR464 data map](https://github.com/cosmosapjw-quantum/htt_base/blob/fa86d940f6d954af554bae5b577d5eb465aa2ae1/docs/research_program/review_seeded_20260907/REUSE_AND_DATA_MAP.md).

## 새 계획을 중복 생성할 필요는 없다

이번 감사 결과는 이미 있는 PR463의 M1-M3와 C0-C5에 연결한다. 아래는 **수정 요구의 위치**이며, 새 과학 모형을 닫았다는 선언이나 실행 허가는 아니다.

| 기존 노드 | 이번 감사가 요구하는 구체적 내용 | 완료를 판정할 산출물 |
|:--|:--|:--|
| M1 CMB model | 실제 low/high/foreground/noise joint law, observable · physical state bridge, selected local boost donor와 units | 수식 · parameter · covariance · source/tail · primary score가 고정된 모형 |
| M2 redshift model | 원 distance likelihood, calibration · selection · window, radial affine null과 공통 frame | 실제 측정에 대한 response와 supported functional, shared-catalog covariance |
| M3 experiment | MIO dependence · pair-order · scale 반례를 calibration 설계에 반영 | null · alternative · split · multiplicity · coverage · tolerance의 확정 값 또는 결정 규칙 |
| C0/C1 integration | 같은 이름의 donor를 구분하고 정상 커널을 선택 | 실제 import/source map, 새 consumer에 필요한 최소 patch |
| C2 synthetic | exact Beta · fibre · joint Gaussian · window 반례를 재사용 | 알려진 truth에서 bias · size · coverage · power · abstention과 MC uncertainty |
| C3/C4 intake · observed | 실제 matched product와 unique ID를 확인한 뒤 같은 처리 실행 | 허용 · 제외 product와 효과 · 불확실성 · sensitivity 결과 |
| C5 return | 실패도 포함한 readable result와 source 연결 | 어떤 결과가 어느 실제 bytes · flags · 자료에서 나왔는지 추적 가능 |
| 장기 native BASS | N01-N04 · C02-C05, geometry · spin transport · brightness bridge | 제한된 물리 branch의 독립 oracle · 관측량 오차 예산 후 점진적 확대 |

현재 finite HTT campaign이 별도 검증된 local boost donor를 쓰므로, **BASS의 모든 장기 오류를 먼저 고치는 일을 M1-M3의 새 필수 선행조건으로 넣을 근거는 없다.** 반대로 나중에 native Bianchi/global-tilt response를 과학 모형으로 소비할 때에는 해당 오류를 건너뛸 수 없다.

가장 유망한 단기 성과는 기존 Q/O · 처리 응답 · 유한 nuisance 수학을 실제로 닫힌 PR3/FFP10 실험에 연결하는 것이다. 중기에는 CF4/DESI의 실제 관측 kernel을 결합하고, 장기에는 검증된 native dynamics를 공급해야 한다. 이 순서는 프로젝트의 원래 목표를 버리지 않으면서 증거가 생기는 순서를 따른다.

# 감사의 완결성 · 재현성과 남은 조사

이번 신규 전문 읽기 54개는 native 13개, collision 15개, manuscript · fibre 11개, main의 통계 5개와 handoff · post-review 10개로 구성된다. main이 다시 읽은 fibre는 중복 제거했다. 신규 57개 독자 · 버전 기록에는 전문 55건과 부분 2건이 있으며, 모든 cache bytes의 Git blob SHA를 확인했다.

부분 2건은 family layout의 지정 구간과 초기 ch05의 전체 diff 판독이다. 초기 ch05의 다른 원문까지 전문 읽었다고 세지 않았다. 외부 논문은 절 · 식 · abstract · metadata 확인 수준을 구분했고, 원래 R1/R2의 사용자 제공 text는 이번에 별도로 읽었다.

제1권의 2,061개 도달 가능 commit 부모 그래프와 182개 head tree 목록을 재사용했다. 이번에는 중간 commit tree의 취득도 확대했다. **metadata 목록은 원문 정독이 아니다.** 전체 역사 tree와 고유 blob의 최종 취득 범위는 동봉 coverage summary에 기록하며, 읽지 않은 내용은 pending ledger로 남긴다.

주요 미독 범위는 모든 commit별 변경의 의미, 나머지 family layout · geometry/matter closure, 전체 spin-2 projector와 boost donor 계통, 모든 결과 JSON의 producer 연결, 전체 보고서 · 시험 · 첨부 archive다. 로컬의 거대한 원시 data volume도 이번 감사 범위에서 직접 읽지 않았다.

따라서 이번 결과는 제1권을 정교화한 독립 심사와 후속 조사 기록이다. 확인된 정상 자산과 반례는 다음 작업의 근거로 쓸 수 있다. ‘repo 전체를 정독했고 모든 잠재적 오류를 찾았다’거나 ‘새 물리 신호가 입증됐다’는 결론을 내릴 단계는 아니다.
