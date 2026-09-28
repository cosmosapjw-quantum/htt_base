# 특정 Bianchi 유형을 선택하지 않는 연구 구조

2026-09-28. 이 문서는 연구의 가정과 연결 구조를 정한다. 개별 새 정리의 판정은
INDEPENDENT_DECISION.json을 따른다. 여기서 model-independent는 특정 우주론 해나
Bianchi type에 독립이라는 뜻이며, 관측자·광학·물질·통계 가정이 없다는 뜻은 아니다.

## 1. 공통 상태와 가정 가지

기본 상태 ξ는 (g, 선택된 congruence U, 기준 congruence N, 복사분포,
필요한 시공간 jet, 경계/source, 관측 연산자, nuisance, reference/anchor)를 포함한다.
기하에 관한 공통 가지와 통계에 관한 공통 가지를 합성하며, 특정 Bianchi 예제는
그 아래의 선택적 특수화로만 둔다.

| 가지 | 입력/가정 | 확보 가능한 내용 | 자동으로 주어지지 않는 것 |
|---|---|---|---|
| K: 일반 운동학 | Lorentzian g, U²=−c², ∇U | θ, σ, ω, A의 정확 분해; TF-P1 | 유한 상계, 특정 물질 관측자 |
| O: 상대론적 광학 | K + geometric optics/null ray + 복사장 | R2 국소 광학/정확 brightness 약형; TF-W1 | 정적 CMB에서 모든 ray/time derivative 복원 |
| E: Einstein 결합 | K + Einstein 식 + 명시한 응력 및 관측자 선택 | Ricci/Raychaudhuri 제약; TF-P2/P3 | EOS, 물질 성분 분해, 전역해 |
| L: 미분류 Lie 대수 | Jacobi를 만족하는 Cᵢⱼᵏ + gᵢⱼ(t), lapse, tilt jet | Koszul 연결과 대수적 국소 제약 | C만으로 길이·시간 척도/수치 예측 |
| M: MES 특수 가지 | 명시한 거의 등방성·미분 예산·물질·frame·차수 | 해당 원문 범위의 조건부 ceiling | nongeodesic 모든 운동학에 같은 ceiling |
| S: 공동 관측/통계 | 위 중 선택한 가지 + joint data law | support/gauge, likelihood, Π, 공동 피복 | 새 관측 rank, prior 없는 모든 성분 식별 |

E, L, M은 서로 같은 가지가 아니다. 조건을 합칠 때는 같은 ξ와 같은 congruence에서
모두 성립하는지 확인한다. 총 응력 T의 energy eigenframe은 dust의 matter frame과
다를 수 있다. Einstein 식이 정하는 것은 총 응력이며 성분 응력은 별도 분해가 필요하다.
기존 Bianchi I I2는 특수 예제/반례 자료로 보존하고 전체 연구의 뿌리로 사용하지 않는다.

## 2. 모든 운동학량과 텐서 함수족

H_*>0를 독립적으로 정하고

\[
k=(\delta\theta/H_*,\;\sigma/H_*,\;\omega/H_*,\;A/(cH_*),
\beta_{RM},\beta_{MO})
\]

를 쓴다. 두 속도를 분리하면 18개의 표현 성분이며 물리 독립 자유도 18개라는 뜻은
아니다. σ는 STF², ω는 axial vector, A와 β는 polar vector다. 서로 다른 rank는
직접합과 함수족으로 보존한다. tensor를 단순한 한 scalar norm으로 교체하지 않는다.

T_Aₙ(a_ℓm^{X,Y},z,...)라는 표기는 해당 자료로부터 정의된 출력 함수일 수 있다.
그 표현공간이 물리 σ와 같아도 둘이 동일하거나 역산 가능하다는 뜻은 아니다.
사용하는 각 φ_j에 frame·epoch·단위·parity·관측 선택·source·정의역을 붙인다.
다른 사건의 텐서는 선언한 경로/연결을 통한 수송 후 비교한다.

현재 첨부 보고서 §23의 기본 정의를 유지한다.

| 객체 | 이번 계승 정의 |
|---|---|
| x | 공동 상태의 sample-by-functional 배열 φ_j(ξ_i); raw tensor도 보존 |
| Q | premise anchor의 gauge γ_B, margin 1−γ_B, 공동 불확실성 구간 |
| F | 방향별 support 사용률; 불확실 body에는 TF-S1의 같은 상태별 비율 |
| Π | 명시한 확률법칙과 scalarization/acceptance set의 exceedance 및 envelope |
| G_F | depth/mask/feature를 잇는 signed transport·coherence의 공동 경로 |

R2의 외적 𝕼_R2=T⊗T, F_rad=||T||², tensor tail 𝚷_R2, scalar growth G_rad는
별도의 파생량으로 보존한다. 기존 signed scalar x의 전체 정의와 정확한 동치는
아직 unresolved다. Ω_tilt를 근거 없이 |β|²로 바꾸지 않는다.

## 3. MES 퍼센트의 의미와 불확실한 분모

같은 상태 ξ에서 y=φ(ξ)−φ_ref(ξ), 유효한 convex anchor B_χ(ξ)를 정한다.

\[
d_B(\xi)=100[1-\gamma_{B_{\chi(\xi)}}(y(\xi))],\qquad
F_{\mathcal C}(u)=\sup_{\xi\in\mathcal C}
\frac{\langle u,y(\xi)\rangle}{h_{B_{\chi(\xi)}}(u)}.
\]

shear-only 구형 anchor라면 γ는 ||σ||/σ_max가 되어 원래 구상을 회수한다.
음의 margin은 조건부 경계 초과이고 0으로 잘라 버리지 않는다. 이 수치는 체적의
등방성 비율, p-value, 관측 신뢰도와 다르다. 같은 관측 조건과 가정 아래의
물리 예산 사용률을 비교할 수 있지만 통계 검출력까지 같아지는 것은 아니다.
rank, covariance, mask, source와 nuisance를 같은 likelihood에서 별도로 평가한다.

분자와 분모를 같은 자료로 추정하면 공동 ξ에서 비율을 계산한다. 주변 최대값들의
비율은 이 값과 다르다. anchor가 없거나 0/무한 분모인 방향은 unavailable로 남긴다.
0-dimensional observable quotient에는 비율 방향이 없고 gauge=0이다. 이 0을
실제 우주의 등방성 판정으로 해석하지 않는다.

## 4. 광학·redshift·dynamics의 solver 없는 연결

R2에서 이미 얻은 정확한 국소 식을 계승한다. U²=−c², e는 광자 진행방향,
a=A/c, H=θ/3, S=σ, 𝒟=(U+ce)·∇일 때

\[
R=-\mathcal D\ln E=H+a\cdot e+S:ee,
\qquad V=h\mathcal D e=-P_e(a+Se)-\omega\times e.
\]

이는 이상적인 local ray 자료의 식이다. 실제 endpoint redshift 및 source proper
motion과 동일하지 않다. 관측 연결에는 광로, source, tetrad, beam/mask가 필요하다.
한 사건의 boost에서는 D=γ(1−β·e), Ẽ=DE,
1+z̃=(D_s/D_o)(1+z)라는 R2 계약을 유지한다.
global tilt field의 ∇β는 한 점의 boost 값에서 나오지 않는다.

동역학은 유한 jet, 약형 잔차, 미분 remainder budget으로 넣는다. 대표적인
R2 Raychaudhuri 제약은

\[
\dot\theta+\theta^2/3+\|\sigma\|_F^2-2|\omega|^2
+R_{ab}U^aU^b-\nabla_aA^a=0.
\]

여기서 마지막 항은 4차원 divergence이며 spatial divergence로 바꾸면 A²/c²가
따로 생긴다. TF-W1은 정확 moment balance를 시험함수로 적분하여 직접 time
derivative 추정의 부담을 줄인다. 실제 창의 moment/source 자료와 endpoint 변환을
위한 Lipschitz budget은 여전히 필요하다. 저적색편이 Taylor 제어를 CMB의 마지막
산란면까지 무조건 외삽하지 않는다. z bin 이름만 추가해 time series로 취급하지 않는다.

## 5. 기존 비전단 결과의 계승 위치

원전 MES의 shear뿐 아니라 tensor vorticity 및 expansion-gradient bound를
유지한다. 와도 convention은 ||ω_ab||_F=√2|ω_a|를 적용한다. expansion-gradient는
θ 자체가 아니다. 확인한 geodesic 원전에서는 A=0이므로 저장소에 식이 존재한다는
이유만으로 nongeodesic A ceiling으로 쓰지 않는다.

DB의 PR168 compiled-source 두 항목은 acceleration/kinematic source의 비례 열과
합 불변성에 대한 정확 대수 명제다. 이는 해당 basis·차수에서의 퇴화 근거이며
모든 source/모든 redshift에서의 보편 퇴화로 확대하지 않는다. PR190 normal
vorticity=0은 지정 normal-frame 명제다. 임의 tilted congruence에 적용하지 않는다.
PR323 Fisher congruence는 가역 정규화가 관측 rank를 만들지 않는다는 방법론의
대수적 바탕이다. 과거 Lean 성공 기록과 이번 재실행 여부를 구분한다.

## 6. 관측 likelihood의 위치

자료 d에는 필요하면 a_ℓm, 편광, 다중 source/redshift 및 별도 광학 관측을 함께 넣는다.
μ(ξ)=M_obs T_theory(ξ)+Nν와 전체 C(ξ), 또는 실제 비Gaussian 법칙 P_ξ를 선언한다.
Gaussian일 때 양의 공분산의 지지공간에서

\[
-2\log L=(d-\mu)^TC^{-1}(d-\mu)+\log\det C+\mathrm{const}
\]

를 사용한다. singular covariance이면 같은 support와 null residual 계약을 따로
유지한다. tensor 통계는 이 법칙의 사상이며 변환이 sufficient/가역이라는 증명 없이
원자료 likelihood와 정보가 같다고 하지 않는다. T_theory와 T_observed의 대응도
동일 observation operator 위에서만 정의한다.

현재 단계에는 실제 law·calibrated joint Cα·모든 성분의 유한 anchor가 없으므로
수치 likelihood·MES deviation percentage를 산출하지 않았다.

## 7. 읽은 외부 근거

- Maartens–Ellis–Stoeger, astro-ph/9501016, §§1–2: expanding dust/geodesic,
  열린 영역의 복사 정보, 1차 근사 및 미분 조건을 확인했다.
  https://arxiv.org/pdf/astro-ph/9501016
- Stoeger–Araujo–Gebbie, astro-ph/9904346, §2 식(2)–(8): shear, tensor-vorticity,
  expansion-gradient 및 multipole norm의 구분을 확인했다.
  https://arxiv.org/pdf/astro-ph/9904346
- Ellis–van Elst, gr-qc/9812046, §2 식(29)–(32): 일반 1+3 방정식의 조건·convention
  대조에 사용했다. https://arxiv.org/pdf/gr-qc/9812046
- 사용자 첨부 Ellis 책 Chapter 7, pp.155–163: ray/observer 분해와 flux·redshift·광학
  면적 연결의 관련 부분을 읽었다. 책 전체를 이번에 읽었다는 뜻은 아니다.
- 사용자 첨부 HTT Research Compendium, §§16,23: 이번 함수족 formalism의 직접 근거.

이 문헌 대조는 기존 조건의 확인이다. 이번 TF-P/S/W 결과의 학술적 신규성 조사는
완료하지 않았으며 신규성을 주장하지 않는다.
