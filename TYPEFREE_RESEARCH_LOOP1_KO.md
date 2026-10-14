# 유형 독립적 수학·물리·통계 연구 — Loop 1

2026-09-28 · 기준 main `96c0b2cb59765c36860da2049021c25a240d0c9b`

특정 Bianchi type에 의존하지 않는 연구 구조로 재편하고, 실제 정리·증명·후보
데이터를 다운로드한 뒤 첫 해석적 연구 루프를 수행했다. 새로 유도·강화한 8개와
기존 후보를 수정한 5개, 총 13개 항목을 별도 검토자가 조건을 명시한
`INDEPENDENTLY_REVIEWED_ANALYTIC` 수준으로 채택했다. 학술적 신규성,
CAS/Lean 검증, 실자료 관측 제약을 확보했다는 뜻은 아니다.

## 실제 확보와 판정 범위

| 항목 | 이번 결과 |
|---|---|
| 정리·증명 공개 DB 원본 export | 46파일, 263,371,196 bytes; Git blob/크기 일치 |
| 기존 명제 관련 레코드 | 40,282개 = 과거 confirmed 345 + unconfirmed 39,937 |
| 추가 구조화 제안/보조 section | 172 / 94개; 기존 레코드와 중복 가능 |
| 보존한 원문 occurrence | 104,780개 |
| 직접 읽고 계승 처리한 후보 | 20개 원문 section |
| 추가 범위 대조 | 기존 compiled-source declaration excerpt 4개 |
| 이번 독립 해석 판정 | 정확히 한정한 후속 항목 13개 채택 |
| 코드 DB 다운로드 | 하지 않음 |
| xAct / Lean / Sage·Singular | 실행하지 않음; 후속 local 계약 작성 |
| 기존 I2 / I3 | 기존 판정 유지 |

40,282는 서로 다른 수학 정리 수가 아닌 소스 문맥·버전별 레코드 수다. 파일 목록만
가져온 것이 아니라 공개 theorem/proof JSON 및 occurrence 원 바이트를 받았다.
이를 새 SQLite로 재구성했으며 원 통합 catalog SQLite 전체/코드 DB는 받지 않았다.
원 catalog baseline은 `efc5f30666b96782f946375551f0068bb3a30f74`다. 최신 I1/I2
702개 파일의 목록을 별도 계층으로 연결했고, 실제 사용한 R2/현재 첨부 formalism을
함께 보존했다. 모든 과거 원문 파일이나 이전 ChatGPT 대화를 이번에 전부 다시
읽었다는 주장은 하지 않는다.

## 1. 가장 중요한 물리 결과

**TF-P1: 기하와 한 점의 tilt 값은 임의 관측자장의 운동학을 제한하지 않는다.**
고정 metric에서 정규화 조건을 만족하는 관측자 1-jet의 12성분을 모두 국소적으로
실현할 수 있다. θ, STF 전단 5성분, 와도 3성분, 가속도 3성분을 임의로 정하는
구성적 증명을 얻었다. 고정 속도 ceiling도 속도 미분의 ceiling은 아니다.

**TF-P2: 물질/응력 고유벡터로 관측자를 선택하면 긍정적인 공동 상계가 생긴다.**

\[
T^a{}_b U^b=-\varepsilon U^a,\quad U^2=-c^2,
\quad L=hTh|_{\mathrm{rest}}+\varepsilon I,
\quad\delta=\min_i|\varepsilon+\lambda_i|>0.
\]

여기서 u=U/c, E₀=u인 rest tetrad에서
\(D_\mu=h(\nabla_{E_\mu}T)u\),
\(\|D\|^2=\sum_{\mu=0}^3\sum_i(D_\mu^i)^2\)는 양의 관측자 norm이다.

\[
\boxed{\nabla_{E_\mu}U=-cL^{-1}D_\mu},\qquad
\boxed{\frac{\theta^2}{3}+\|\sigma\|_F^2+2|\omega|^2+
\frac{|A|^2}{c^2}\le\frac{c^2\|D\|^2}{\delta^2}.}
\]

고유벡터 식을 미분하고 rest projection을 취하면 첫 식이 나온다. self-adjoint L의
inverse norm이 1/δ이고 운동학 분해가 Frobenius 직교이므로 두 번째 식이 따른다.
따라서 같은 상태에서 δ≥δ*>0, ||D||≤d*이면 B*=cd*/δ*라는 공동 rate budget을
얻는다. 특정 Bianchi type, 약한 비등방성 또는 numerical evolution을 요구하지 않는다.

이것은 **응력 미분 예산이 주어진 조건부 물리 상계**다. 실제 CMB가 d*,δ*를 측정해
주었다거나 원전 MES가 보증한 ceiling이라고 부르지 않는다. 이 ellipsoid에서
reference를 빼면 실제 옮겨진 feasible body를 사용해야 하며, 임의로 중심 0의
같은 ellipsoid라고 부르지 않는다. 총 응력 energy frame와 MES dust matter frame도
같다고 가정하지 않는다.

**TF-P3: Einstein 식까지 쓰더라도 metric 2-jet는 일반적으로 부족하다.**

\[
g_\lambda=e^{2\phi_\lambda}\eta,\qquad
\phi_\lambda=-b(x^0)^2-\frac b2|\mathbf x|^2
+\frac\lambda2(x^0)^2x^1,\quad b>0,\quad x^0=ct
\]

라는 국소 가족에서 T=G/κ의 미래 timelike 고유벡터를 선택했다. p=0의 metric
2-jet, T(p), U(p), β(p), spectral gap는 모두 같지만

\[
A^1(p)=\frac{c^2\lambda}{3b},\qquad \theta(p)=\sigma(p)=\omega(p)=0
\]

이다. 따라서 선택된 물리 energy congruence에서도 가속도가 임의로 커질 수 있다.
metric 3-jet는 ∇T를 정하므로 비축퇴 조건 아래 충분하다. 각 유한 λ의 충분히
작은 근방에서 strict type-I DEC를 유지할 수 있으나 이 구성은 dust EOS나
전역 우주해가 아니다. 임의 관측자와 응력에 의해 선택된 관측자의 차이가 핵심이다.

## 2. 원래의 MES 비교 구상을 유지한 통계 결과

현재 기본 정의는 x=공동 함수족, Q=gauge/margin, F=방향별 support 사용률,
Π=법칙에 따른 exceedance/envelope, G_F=공동 transport/coherence다.
외적 𝕼_R2=T⊗T와 F_rad=||T||²는 추가 파생량으로 구분한다.

공동 상태 Z에 분자 y, reference, 불확실 anchor Bχ, 여러 depth와 nuisance를
함께 넣으면 TF-S1은

\[
F_{\mathcal C}(u)=\sup_{Z\in\mathcal C}
\frac{\langle u,y(Z)\rangle}{h_{B_{\chi(Z)}}(u)},\qquad
\sup_{\|u\|=1}F_{\mathcal C}(u)
=\sup_{Z\in\mathcal C}\gamma_{B_{\chi(Z)}}(y(Z))
\]

를 준다. 분자와 분모는 같은 Z에서 평가한다. 몸체는 유효한 compact convex
anchor이며 0이 내부에 있어야 한다. dim=0이면 방향이 없으므로 profile을 만들지
않는다. 누락된 anchor를 0으로 채우지 않는다.

원래의 percentage는 **100(1−γ_B)**로 회수된다. shear-only 구형 anchor에서는
100(1−||σ||/σ_max)다. 이는 같은 전제 아래의 물리 예산 여유율이며 확률이나
유의수준이 아니다. 서로 다른 sector의 통계 검출력까지 같아지지는 않는다.

TF-S3은 관측 응답의 몫 p에서

\[
\gamma_{pB}(v)=\min_{py=v}\gamma_B(y)
\]

를 증명한다. 관측 가능한 조합의 사용률은 같은 관측을 설명하는 모든 전체 상태 중
**가장 작은 사용률**이다. 따라서 작은 관측 사용률이 실제 숨은 전단·회전·가속도까지
작다는 뜻은 아니다. 실제 물리 제약이 섬유를 좁히면 그 제한된 섬유를 따로 사용한다.

TF-S2는 실제로 보정된 공동 신뢰집합을 함수족 전체로 사상하면 같은 피복 사건을
보존함을 증명한다. 자료로부터 그런 신뢰집합을 구축했다는 뜻은 아니다. TF-S4는
같은 전체 자료법칙을 갖는 두 허용 상태에서 관심 텐서가 다르면 신뢰집합의 직경을
마음대로 줄일 수 없음을 정량화한다. local boost/global tilt의 응답 열이 같으면
redshift 이름을 늘리는 것만으로는 이 퇴화가 풀리지 않는다.

## 3. 약형을 이용한 실제 다음 연결

TF-W1은 채택한 정확 balance m′+Ak=s에 대해

\[
K_w=\int wAk=\int(ws+w'm)-[wm]_a^b
\]

를 쓰고, ||k(t)−k(t₀)||≤L|t−t₀|이면

\[
\|\bar A_wk(t_0)-K_w\|
\le L\int|w|\|A\||t-t_0|dt
\]

라는 유한 창 오차를 준다. 적분가능성, 동일 transported frame, 실제 source/moment
자료 및 유한 미분 예산을 명시했다. 수치 진화를 풀 필요 없이 동역학을 제약으로
넣을 수 있지만, static sky에서 없는 time/source 자료를 만들어내지는 않는다.

## 4. 원문 후보에서 수정한 다섯 부분

| 항목 | 원문에서 수정한 부분 | 이번에 채택한 내용 |
|---|---|---|
| TF-C1 | compact/nonconvex이면 항상 유한 구간 합 | 일반적으로 거짓; semialgebraic 조건이면 가능 |
| TF-C2 | 감소하는 response면 Fisher tail 수렴·충분성 | weighted square summability 필요; rℓ=ℓ⁻ᵖ는 p>1; 정확/근사 충분성 분리 |
| TF-C3 | Frobenius에서 보편 shear/vorticity 비례 | 임의 congruence 반례; branch별 추가 조건 필요 |
| TF-C4 | 일정한 source이면 depth growth=1 | 적분 길이/kernel/boundary 필요; q=sL 반례 |
| TF-C5 | octupole amplitude를 자동 차감하여 ceiling 축소 | 부호·미분 budget 없이는 plus bound; 물리 sharpening 재개 필요 |

원문의 모든 상태를 일괄 승격한 것이 아니다. 채택한 것은 수정된 정확한 후속 문장과
반례다. 과거 잘못된 보편 절의 기각 및 실제 transfer/충분성/sharpening의 미해결을
별도 기록했다.

## 5. 다음 local 루프와 현재 완성도

1. xAct: TF-P2/P3의 exact 곡률·stress·고유벡터 미분과 c/부호 재현.
2. Lean/mathlib: 공동 피복·동일법칙 직경·유한 행렬 gap 정리부터 실제 formal proof.
3. Sage/Singular: 미분류 Lie Jacobi 및 semialgebraic feasible-set의 특이 가지 분석.
4. 실제 관측 단계: 한 개의 정당한 moment/source 창을 정해 TF-W1의 입력과 오차를
   채우고, 같은 자료법칙에서 식별 가능한 tensor 조합 및 anchor부터 정한다.

이번 준비/해석 루프의 완료 조건은 충족했다. 전체 연구의 완료율을 임의의 퍼센트로
표시하지 않는다. 실제 모든 운동학량의 유한 MES body, 관측 source/derivative 예산,
보정된 joint likelihood, legacy scalar x 전체의 동치, 학술적 신규성은 미완이다.
원본 702개 통합의 과학적 판정이나 I2/I3의 상태도 자동 변경하지 않았다.

아래에는 가정 구조, **판정 이후 반드시 적용할 보완**, 원문 제출 증명,
수정 계승표와 local 전달 프롬프트를 모두 넣었다. 원고에 남아 있는
`pending independent review` 문구는 제출 당시 상태이며, 현재 판정은 위의
INDEPENDENTLY_REVIEWED_ANALYTIC과 다음 보완문을 따른다.


---

# 부록: RESEARCH_ARCHITECTURE_KO.md

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


---

# 부록: ADJUDICATED_AMENDMENTS_KO.md

# 독립 판정에 따른 정확한 채택 문장과 필수 보완

2026-09-28. 후보 원고의 범위보다 이 문서의 정확한 문장과 가정이 우선한다.
새 분석 항목 13개를 INDEPENDENTLY_REVIEWED_ANALYTIC으로 채택했다.
수치/CAS/Lean/관측 검증 및 학술적 신규성 승격은 없다. 원 historical 상태는 유지한다.

## TF-P1 — 임의 관측자 congruence 1-jet의 국소 실현

고정 smooth Lorentzian metric g, 사건 p 및 미래 timelike U0·U0=−c²를 주면, U0^b K_ab=0인 모든 K_ab는 U(p)=U0, ∇_aU_b(p)=K_ab인 smooth 정규화 미래 congruence의 1-jet로 국소 실현된다. 이 공간은 12차원이며 θ(1), σ_STF(5), ω(3), A(3)와 일대일 대응한다. 고정 Einstein (g,T)도 별도 관측자 U에 대한 결론을 바꾸지 않는다. 고정 N(p), β(p)는 U0만 정하므로 12개 미분 성분의 유한 보편 bound를 주지 않는다.

**필수 가정**

- 4차원, signature (−+++), x0=ct를 포함한 길이 좌표, U·U=−c², A=∇_U U.
- U는 독립 관측자장이다. U를 stress eigenvector, geodesic, dust flow, 공간균질 invariant flow 등으로 추가 제한하지 않는다.
- 각 유한 K마다 충분히 작은 근방을 허용한다. K 전체에 공통 근방 또는 uniform derivative bound는 요구하지 않는다.

**보완/적용 범위**

- 추가 수정 불필요. 표현 시 arbitrary observer와 physically selected matter congruence를 계속 구별하고 국소 존재만 표시한다.

## TF-P2 — stress eigenvector의 spectral-gap 복원 및 공동 상계

T^a_b U^b=−εU^a인 smooth 미래 timelike branch U를 물리 congruence로 선택한다. h=g+u⊗u, u=U/c, S=hTh|rest, L=S+εI, δ=min_i|ε+λ_i|>0 및 D_μ=h(∇_{Eμ}T)u를 정의하면 ∇_{Eμ}U=−cL^(−1)D_μ이고, θ²/3+||σ||_F²+2|ω|²+|A|²/c² ≤ c² Σ_μ|D_μ|²/δ²이다. δ≥δ*>0, ||D||≤d*<∞가 같은 상태에서 주어지면 B*=cd*/δ*라는 공동 rate budget을 얻는다.

**필수 가정**

- T는 symmetric C1 이상이고 선택된 timelike eigenvalue는 spatial eigenvalues와 분리된다.
- E0=u 및 right-handed orthonormal rest triad를 사용한다. D의 norm은 Σ_{μ=0}^3Σ_i(D_μ^i)²라는 observer-positive norm이며 Lorentzian contraction이 아니다.
- 이것은 stress 1-jet와 gap을 입력으로 받는 조건부 bound다. 실제 측정된 d*, δ* 또는 MES 원전의 상계가 제공되었다고 가정하지 않는다.
- T는 실제로 지정한 특정 smooth symmetric stress이다. 그 energy-frame congruence가 historical dust/matter congruence와 동일하다고 자동 가정하지 않는다.

**보완/적용 범위**

- 추가 수정 불필요. norm과 gap의 동일 상태 조건, 실제 stress derivative 예산의 미확보, β가 T와 N에서 결정된다는 범위를 그대로 유지한다.
- P2의 T-selected bound를 dust-MES 또는 다른 component/congruence의 광학 bound와 교차하려면 stress component, frame, congruence, epoch, units 및 같은 상태의 compatibility를 먼저 선언한다. energy frame와 dust rest frame를 조용히 동일시하지 않는다.

## TF-P3 — Einstein-selected congruence: metric 3-jet의 충분성과 2-jet 반례

상수 κ=8πG_N/c⁴, Λ와 Einstein 식 T=κ^(−1)(G+Λg), TF-P2의 비축퇴 timelike eigenvector 선택을 채택하면 metric 3-jet가 U(p), ∇U(p)를 정한다. 일반 smooth Einstein-source class에서는 metric 2-jet, T(p), U(p), β(p), gap를 모두 고정해도 ∇U(p)는 유계이지 않다. 명시적 conformal family g_λ=e^(2φ_λ)η, φ_λ=−b(x0)²−(b/2)Σ_i(xi)²+(λ/2)(x0)²x1, b>0에서 선택 가속도 A1(p)=c²λ/(3b), θ=σ=ω=0이다. 여기서 Einstein 식으로 복원되는 T는 선언한 Λ 배치 아래의 total stress이다. 별도 component stress는 그 split과 필요한 first derivative가 추가로 주어져야 복원할 수 있으며 total-energy congruence가 historical dust/matter congruence와 같다는 결론은 없다.

**필수 가정**

- p=0, x0=ct, b 단위 length^(−2), λ 단위 length^(−3), curvature convention [∇c,∇d]v^a=R^a_bcd v^b.
- 반례에서 Λ=0 및 T_λ=G[g_λ]/κ로 정의한다. congruence는 T의 unique 미래 timelike energy-eigenvector branch다.
- 각 유한 λ마다 충분히 작은 근방만 주장한다. 전역해, λ-공통 근방, dust EOS, perfect-fluid EOS 또는 고정 물질 작용은 가정하지 않는다.

**보완/적용 범위**

- 반례를 Einstein-dust solution으로 명명하지 않는다. p에서 pressureless인 사실은 근방의 EOS를 정하지 않는다.
- 3-jet의 최소 일반 충분 차수라는 말은 선택된 nondegenerate stress-eigenvector 계약에만 적용한다. arbitrary observer는 metric 전체 germ에도 별도 congruence 자료가 필요하다.
- metric 3-jet는 Einstein total stress를 정한다. 물질 성분별 split이 별도로 알려지지 않으면 historical geodesic dust congruence를 복원했다고 부르지 않는다. P2 body와 dust-MES를 합성할 때 explicit component/frame/congruence compatibility를 요구한다.

## TF-S1 — same-latent uncertain-body support/gauge 쌍대성

dim E≥1인 유한 차원 내적공간, 각 상태 Z의 compact convex Bχ(Z)⊂E 및 0∈int Bχ(Z), 비어 있지 않은 joint C를 사용한다. y(Z)=φ(X)−φ_ref(r), r_Z(u)=〈u,y(Z)〉/h_Bχ(Z)(u), U_C(u)=sup_Z r_Z(u)이면 γ_Bχ(y)=sup_{||u||=1}r_Z(u), sup_{||u||=1}U_C(u)=sup_Z γ_Bχ(Z)(y(Z))이다. 모든 Z에서 y(Z)∈Bχ(Z)인 것과 모든 방향 U_C≤1인 것은 동치다. E={0}인 별도 branch는 y=0, gauge=0, membership=true이며 direction profile은 NO_DIRECTIONS로 반환한다.

**필수 가정**

- 분자·기준·몸체가 동일 Z에서 함께 변한다. 서로 다른 marginal extrema나 독립 posterior 곱으로 대체하지 않는다.
- 각 body는 해당 functional output, frame, epoch, 단위, support에 적용 가능한 실제 anchor 또는 명시된 outer body여야 한다.
- maximum/witness를 주장하려면 C compact, y continuous, χ→Bχ Hausdorff-continuous, uniform b0>0 with b0 unit ball⊂Bχ가 추가로 필요하다.

**보완/적용 범위**

- S1의 sphere equality에는 dim E≥1을 추가한다. E={0}이면 sphere가 empty이므로 usual extended-real sup(empty)=−∞를 gauge 0과 동일시하지 않는다. gauge 0 및 NO_DIRECTIONS를 명시한다.
- body가 없거나 유한하지 않거나 0 interior 조건을 충족하지 않으면 본 정리와 비율을 적용하지 않는다. MISSING_ANCHOR/UNBOUNDED_ANCHOR/DEGENERATE_ANCHOR 등 typed 상태를 유지하며 ∞ support를 유한값이나 관측 0으로 바꾸지 않는다.
- 전체 공간에서 lower-dimensional body를 쓰려면 먼저 실제 affine/reference slice의 유한 차원 span으로 제한하고 membership를 확인한다. slice 밖 상태를 0으로 채우지 않는다.

## TF-S2 — joint confidence/predictive/posterior pushforward와 ratio domain

실제로 유효한 joint coverage P_Z{Z∈Cα(D)}≥1−α와 measurable Ψ/event를 가정하면 P_Z{Ψ(Z)∈Ψ(Cα(D))}≥1−α이다. 같은 사건에서 모든 registered functional, direction 및 depth profile의 inf/sup coverage가 동시에 따른다. joint posterior μ_d의 image mass도 같은 포함관계로 보존되지만 frequentist coverage와 다른 주장이다. G_rad=Fa/Fb는 Fb>0에서만 정의하며 이 domain에서 유한 upper bound의 필요충분조건은 모든 상태에 대해 Fa≤M Fb인 finite M의 존재다.

**필수 가정**

- Z에는 참 numerator, reference, anchor/body, 공유 nuisance, 여러 depth와 transport 입력을 함께 포함한다.
- Ψ가 모든 참 상태에서 정의되거나 undefined/unavailable을 명시적 반환값으로 보존한다. positive-denominator branch만 남기는 경우 그 조건부 대상과 coverage를 별도로 지정한다.
- 메커니즘의 calibration이나 실자료 posterior는 이 정리의 결론이 아니라 입력이다. 통계 사건과 random set image의 measurability를 가정한다.

**보완/적용 범위**

- Cα(D)=empty일 때 image도 empty로 유지한다. S1/S3의 nonempty profile을 무리하게 평가하지 말고 EMPTY_SET 상태로 기록한다.
- unavailable anchor 또는 Fb=0인 branch를 삭제한 뒤 원래 무조건 target의 coverage를 주장하지 않는다. typed undefined output 또는 명시된 restricted target/domain을 사용한다.
- 같은 데이터의 reference/body plugin은 참 joint axis를 삭제하므로 원 theorem의 보장이 자동 상속되지 않는다. 실제 joint set/law 또는 별도로 보정된 plugin target을 요구한다.

## TF-S3 — response quotient의 gauge는 fiber 최소값

TF-S1의 compact full-dimensional B와 고정 선형 p:E→V=p(E)에 대해 γ_pB(v)=min_{py=v}γ_B(y), h_pB(u)=h_B(p*u)이다. dim V≥1에서는 sup_{||u||V=1}U_C^p(u)=sup_Z min_{py′=py(Z)}γ_Bχ(Z)(y′)≤sup_Zγ_Bχ(Z)(y(Z))이다. V={0}이면 pB={0}, quotient gauge와 fiber minimum은 0, profile은 NO_DIRECTIONS다. quotient gauge≤1은 B 내부 lift 하나의 존재만 뜻한다.

**필수 가정**

- p는 해당 y-output에 실제 적용되는 response quotient다. k에 대한 response를 임의 nonlinear φ(k)에 그대로 적용하지 않는다.
- fiber minimum에서 각 Z의 χ를 고정한다. 이 algebraic fiber는 실제 coupled physical state C의 fiber와 같다고 가정하지 않는다.
- nonzero kernel 방향의 gauge divergence는 unrestricted full-E fiber에 한정한다. 제한된 physical domain에서는 허용 lift만 사용한다.

**보완/적용 범위**

- dim V=0이면 unit sphere가 없으므로 directional supremum formula를 적용하지 않는다. S3.1 및 S3.2는 그대로 유효하되 gauge/minimum=0, h_{0}(0)=0, NO_DIRECTIONS로 명시하며 0/0을 계산하지 않는다.
- min_{py=v}의 attained lift는 unconstrained fixed-body algebraic lift다. 실제 joint C나 nonlinear physical constraints 아래의 attainment로 확대하지 않는다. 그 경우 C의 허용 fiber에 제한해 별도 infimum을 평가한다.
- missing/unbounded/degenerate anchor에는 compact-body theorem을 적용하지 않는다. 필요시 적용 가능한 상대 span과 참 기준을 먼저 지정한다.

## TF-S4 — 동일 자료법칙의 fiber 및 confidence-diameter 한계

D=μ0+Rk+Nη+ε에서 ε의 전체 법칙이 (k,η)에 무관하고 Rh=Nc이면 두 허용 상태 (k,η),(k+h,η−c)는 동일 자료법칙 P를 갖는다. 함수 f는 허용 response-equivalence fiber마다 상수일 때에만 그 quotient로 내려간다. 동일 law인 두 상태의 f값이 f0≠f1이고 confidence set Aα가 각 상태에서 coverage≥1−α이면 P{diam Aα≥d(f0,f1)}≥max(0,1−2α)이다. 같은 linear response columns를 가진 local boost와 physical tilt는 그 실험에서 분리되지 않으며 모든 depth에서 같은 kernel이면 stacking도 이를 제거하지 않는다.

**필수 가정**

- 관심 함수와 equivalence quotient의 domain을 일치시킨다. full-state nuisance/reference/body가 변하면 실제 full-law 동등성을 확인한다.
- 정리의 실질적 lower bound는 0≤α<1/2에서 양수다. 모든 α∈[0,1]에서는 max(0,1−2α)로 쓴다.
- 두 서로 다른 동일-law 상태가 실제 physical domain에 존재해야 한다. Jacobian에만 성립하는 관계는 해당 선형 근사에만 적용한다.

**보완/적용 범위**

- quotient factorization의 증명은 set-theoretic이다. measurable/continuous quotient function이 필요한 통계 사용에서는 quotient measurable structure 또는 그 regularity를 별도로 명시한다.
- 동일 mean만으로 동일 law를 주장하지 않는다. nuisance 보상 두 상태의 admissibility와 전체 noise/covariance 법칙 고정을 함께 유지한다.

## TF-C1 — compact 선형상의 올바른 connected/semialgebraic 분기

nonempty compact F⊂R^d와 linear l에 대해 l(F)는 compact이고 extrema를 달성한다. F가 connected이면 l(F)는 closed interval이며, F가 semialgebraic이면 l(F)는 finitely many closed intervals and points의 합집합이다. compact와 nonconvex만으로 finite-union 결론은 성립하지 않는다.

**필수 가정**

- finite-dimensional real space, continuous linear l.
- finite-union 결론에는 semialgebraic 가정 또는 별도로 입증된 finite-component 성질이 필요하다.

**보완/적용 범위**

- 원문 general compact/nonconvex finite-union 명제와 corrected semialgebraic successor를 DB에서 별개 statement로 유지한다.
- support/convex hull가 같아도 nonconvex 내부 구조가 같다고 추론하지 않는다.

원 주장에 대한 별도 판정: {"decision": "REJECT", "scope": "compact/nonconvex이면 언제나 finite union이라는 보편 절", "reason": "Cantor counterexample", "preserve": "compact-extrema 부분과 조건을 보강한 successor는 유지; historical DB status는 덮어쓰지 않음."}

## TF-C2 — Gaussian Fisher tail의 수렴과 sufficiency의 구별

독립 full-sky real Gaussian mode degrees of freedom a_lm~N(0,C_l(q)) 또는 q-independent means, C_l(q)>0를 갖는 고정 실험에서 r_l=∂q log C_l at a declared q이면 tail Fisher information은 I_tail=(1/2)Σ_{l>L}(2l+1)r_l²이며 그 유한성은 이 합의 수렴과 동치다. r_l=l^(−p)이면 p>1에서만 수렴한다. Exact low-l sufficiency의 충분조건은 모든 q에서 p_q(dL,dH)=p_{L,q}(dL)g(dH|dL)이고 g가 q-independent인 것이다. Gaussian의 간단한 충분조건은 μH,CHH가 q-independent이고 CLH=0인 것이다. 작은 local Fisher tail만으로 global approximate sufficiency는 증명되지 않는다.

**필수 가정**

- tail formula의 means는 q-independent, modes는 full-sky independent, multiplicity는 real 2l+1이다. q가 log F이면 그것을 명시한다.
- Fisher score/미분은 선언한 regular parameter domain에서 존재한다. infinite sum은 finite-block information의 monotone limit로 해석할 수 있다.
- exact factorization은 특정 q의 한 점이 아니라 전체 parameter domain에서 성립해야 한다. approximate sufficiency는 별도 global law/domain/error metric를 요구한다.

**보완/적용 범위**

- 후보의 response가 정확히 0이라는 문구에는 모든 q와 q-independent mean을 명시한다. 한 parameter 점에서의 ∂qC=0은 exact sufficiency를 주지 않는다.
- cross-block도 q와 무관하게 factorize라는 문구는 위 conditional-factorization 식으로 교체하거나 Gaussian CLH=0의 간단한 충분조건으로 쓴다. 단순히 nonzero CLH가 q-independent인 것은 충분조건이 아니다.
- 수정본의 충분조건 표현을 유지한다. f_sky 곱은 일반 masked experiment의 exact covariance/Fisher law로 승격하지 않는다. r2=1, r_l>0 또는 실제 astrophysical transfer는 별도 검증 대상이다.

원 주장에 대한 별도 판정: {"decision": "REJECT", "scope": "any decaying r_l이면 Fisher tail 수렴이라는 절", "additional_decision": "REOPEN", "additional_scope": "실제 low-l approximate sufficiency 및 astrophysical response", "reason": "1/l 반례; 실제 law와 global error criterion 미제공"}

## TF-C3 — Frobenius에서 universal shear/vorticity ratio는 나오지 않음

timelike smooth congruence의 local hypersurface orthogonality와 vorticity 소멸은 동치지만, 모든 congruence에서 W²=R_WS²Σ²인 고정 universal positive proportionality는 성립하지 않는다. Minkowski에서 u=sqrt(1+|Bx|²)e0+(Bx)^i ei를 쓰면 p=0에서 antisymmetric nonzero B는 θ=σ=0, ω≠0이고 symmetric tracefree nonzero B는 θ=ω=0, σ≠0이다.

**필수 가정**

- 일반 smooth timelike congruence의 국소 진술이며 특정 EOS, spatial symmetry 또는 field equation branch를 추가하지 않는다.
- u·u=−1, physical U=cu. B는 length^(−1)이고 physical kinematic rates는 c를 곱한다.

**보완/적용 범위**

- 특정 물질·기하 branch에서 별도로 증명된 비례식은 그 branch에만 남긴다. 일반 joint budget은 실제 coupled constraints 또는 정당화한 별도 bounds로 만든다.

원 주장에 대한 별도 판정: {"decision": "REJECT", "scope": "Frobenius가 모든 congruence에 양의 고정 shear/vorticity 비례를 강제한다는 해석", "preserve": "추가 branch-specific 물리 가정이 있는 비례식은 별도 REOPEN/검증 가능"}

## TF-C4 — constant source는 depth-independent observable을 보장하지 않음

선언된 line-of-sight response q(L)=∫_0^L s dχ with constant s≠0에서 q=sL이고 F_rad(L)/F_rad(L0)=(L/L0)² for L0>0이다. 따라서 source가 depth-independent라는 사실만으로 accumulated observable 또는 그 radial growth가 depth-independent라는 결론은 나오지 않는다.

**필수 가정**

- 유한 L≥0, fixed nonzero constant source, identity kernel, 동일 units/frame, positive reference L0.
- 이 반례는 선형 integral-response 계약에 대한 것이다. 실제 Einstein–Boltzmann 우주해나 모든 cosmological kernel을 구성하지 않는다.

**보완/적용 범위**

- 현재 G_F는 structured depth/mask/feature transport와 coherence다. 이 반례의 scalar는 별도 G_rad alias로만 사용한다.
- 실제 shear-to-observable kernel, boundaries, visibility, redshift/time mapping가 없는 원 cosmological G_F≡1 주장은 해소되지 않은 것으로 남긴다.

원 주장에 대한 별도 판정: {"decision": "REJECT", "scope": "constant source alone implies constant accumulated observable라는 일반 함의", "additional_decision": "REOPEN", "additional_scope": "특정 물리 transfer에서 constant shear⇒G_F=1이라는 원 cosmological 명제"}

## TF-C5 — unsigned octupole amplitude의 자동 subtraction bound 불가

선형 residual 관계 Lσ=r2−D3에서 선언된 norm과 ||D3||≤b만 있으면 최악의 일반 upper bound는 ||Lσ||≤||r2||+b이며 부호 없는 b를 단순 차감할 수 없다. 작은 octupole amplitude만으로 그 spacetime derivative correction D3의 작은 bound도 얻지 못한다. 실제 추가 공동 제약은 feasible set를 줄일 수 있지만 임의 scalar 감소인자를 정당화하지 않는다.

**필수 가정**

- r2와 D3는 같은 vector/tensor space, norm, frame, epoch와 units에서 비교한다.
- octupole amplitude와 derivative가 다른 함수이면 그 사이의 derivative budget 또는 dynamical relation은 별도 가정이다.
- σ 자체의 bound는 L의 relevant inverse/quotient와 nuisance 조건을 추가해야 한다.

**보완/적용 범위**

- 원 scalar sharpening formula를 theorem으로 승격하지 않는다. exact adopted weak law, derivative budget, signed alignment 및 joint residual inverse-image로 후속 bound를 정의해야 한다.
- plus bound는 ||Lσ||의 bound다. invertibility/target kernel 조건 없이 ||σ|| 또는 MES ceiling로 바꾸지 않는다.

원 주장에 대한 별도 판정: {"decision": "REOPEN", "scope": "원 f=1−min(a3/a2,fmax) physical sharpening formula", "rejected_inference": "unsigned amplitude bound alone licenses subtraction", "reason": "signed opposite correction attains plus bound; amplitude does not control derivative"}

## TF-W1 — finite-window weak response와 bounded target criterion

고정 유한 차원 transported spaces에서 m∈AC([a,b]), s∈L1, A∈L1, w∈C1이고 m′+Ak=s a.e.라 하자. k0=k(t0), finite L≥0 및 ||k(t)−k0||≤L|t−t0| a.e.이면 K_w=∫wAk=∫(ws+w′m)−[wm]_a^b이고 ||Abar_w k0−K_w||≤L∫|w| ||A|| |t−t0| where Abar_w=∫wA. 유한 공통 residual budget를 가진 nonempty finite-dimensional feasible set에서 free linear nuisance를 project한 B=P_N^⊥M에 대해 target Pk가 유계일 필요충분조건은 ker B⊆ker P이다. domain이 k*+S이면 ker B∩S⊆ker P로 바꾼다.

**필수 가정**

- a<b finite, t0∈[a,b]. derivative와 integral는 동일 transported frame에서 비교하며 moving-frame connection은 채택한 balance에 이미 포함한다.
- matrix A는 conditional declared coefficient다. finite β 또는 불확실 A까지 unknown rate에 선형이라고 가정하지 않는다.
- s 및 A integrable, k0 finite와 uniform L finite로 Ak와 모든 displayed integrals가 정의된다. 더 약한 가정도 가능하지만 여기서는 이 충분조건을 채택한다.
- nuisance range는 고정 유한 차원 subspace이고 projected data/residual budget는 finite이며 admissible k에 uniform하다. target은 선형 P, feasible set은 nonempty다.

**보완/적용 범위**

- A 자체의 integrability, displayed weighted norm/error integrals의 finiteness 및 endpoint traces를 명시한다. balance가 Ak만 integrable이라고 보장할 뿐 Abar_w가 자동 정의되는 것은 아니다.
- kernel iff에는 finite-dimensional spaces, fixed projected operator, uniform finite residual bound 및 nonempty feasible set를 명시한다. proper affine domain k*+S이면 ker B∩S⊆ker P를 사용한다.
- 작은 singular value에 따른 큰 bound constant ||H||를 숨기지 않는다. kernel 조건은 boundedness criterion이며 자동 numerical stability나 useful empirical precision을 뜻하지 않는다.
- 실제 m(t),s(t) 또는 동등한 finite-window 자료가 입력되어야 한다. 하나의 static sky에서 확보되었다고 간주하지 않는다. redshift bins에는 dt/dz, source/congruence, path, selection 및 covariance 계약이 필요하다.



---

# 부록: PHYSICS_RESULTS_KO.md

# title_ko

관측자 1-jet의 자유도와 Einstein 물질 고유벡터의 spectral-gap 예산

# summary_ko

고정 Einstein 시공간과 고정 국소 tilt 값은 임의 관측자 congruence의 팽창·전단·와도·가속도 12성분을 제한하지 않는다. 반면 물질 응력텐서의 비축퇴 timelike 고유벡터가 congruence를 물리적으로 선택하면 그 1-jet은 응력의 1-jet에서 정확히 복원되며, spectral gap과 응력 미분 예산이 전 운동학 공동 타원체 상계를 준다. Einstein 식을 사용할 때 일반적으로 metric 3-jet가 충분하고 metric 2-jet는 부족하다. 후자의 부족성을 동일 metric 2-jet·동일 T(p)·동일 β(p)에도 선택된 가속도가 임의로 커지는 명시적 smooth local Einstein-source family로 증명한다.

# inherited_vs_strengthened

## inherited

- R2 §2의 정확한 12성분 국소 광학 사상과 inverse, §4의 Raychaudhuri residual, §5의 Lie 자료 부족성, §6의 local boost와 congruence tilt 구분을 그대로 인정한다.
- I1 §1의 고정 homogeneous geometry·고정 β branch에서는 tilt time jet 변화가 3차원이고 별도 compatibility 식을 만족한다. 이 branch를 일반 congruence에 확대하지 않는다.
- R2의 body gauge·radial tensor·Q/F/Π/G 및 likelihood 정의를 새 정리로 반복하거나 최신 functional-family 정의를 대체하지 않는다.

## strengthened_in_this_result

- R2의 'β(p)만으로 불충분'을 모든 정규화된 congruence 1-jet의 구성적 실현 정리로 강화한다.
- 물질 congruence 선택이 빠진 Einstein-only 조건과 실제 물질 고유벡터 조건을 분리하고, 후자에 정확한 미분 복원식·날카로운 공동 상계를 준다.
- metric 2-jet의 부족성을 물질 고유벡터 선택 후에도 유지되는 명시적 Einstein-source 반례로 보여 일반적인 충분 jet 차수를 판별한다.

## novelty_claim

프로젝트 내 이번 합성·유도 범위만 표시한다. 학술적 신규성 조사는 하지 않았으며 신규성은 unresolved다.

# conventions_and_domain

- 4차원 time-oriented Lorentzian manifold, signature (−,+,+,+). U·U=−c², u=U/c, h=g+u⊗u. 국소 좌표 x⁰=ct와 xⁱ는 길이 단위다. 물리 proper-time 가속도 A=∇_U U, a=A/c. H=θ/3. θ, H, σ, ω, a의 단위는 s⁻¹이고 β는 무차원이다.
- ∇_aU_b=−U_aA_b/c²+(θ/3)h_ab+σ_ab+ω_ab. ω_ab=D_[aU_b], ω_i=(1/2)ε_ijkω_jk, ε_123=+1. 따라서 U-rest triad에서 ω_ij=ε_ijkω_k이고 ||ω_ab||²_F=2|ω|². 이 부호는 R2의 derivative-first convention이다.
- 곡률은 [∇_c,∇_d]v^a=R^a_bcd v^b 및 R_bd=R^a_bad. Einstein 식은 G_ab+Λg_ab=κT_ab, κ=8πG_N/c⁴, 상수 Λ와 상수 G_N이다. T의 에너지밀도·압력·고유값 단위는 J m⁻³이다.
- j_p^r g는 고정된 좌표에서 p의 metric 성분과 r차까지의 편미분이며, 결과는 해당 tensor 조합으로 공변적으로 해석한다. 개별 좌표 jet 성분 자체를 관측량으로 부르지 않는다. 매끄러운 자료를 사용하며 eigenvector 1-jet에는 적어도 T의 C¹ 및 metric의 필요한 미분 가능성이 필요하다.
- N은 별도로 지정한 물리 기준 congruence, N·N=−c². γ=−U·N/c², β=(U/γ−N)/c이면 β·N=0, |β|<1, U=γ(N+cβ). 이는 관측자 값과 공간·시간 velocity field의 구분을 명시한다.
- 모든 주장은 사건 p 또는 충분히 작은 근방에 관한 것이다. 특정 Bianchi type, 공간균질성, 전역 completeness, 고정 시간구간의 균일 bound, 물질 EOS, 실제 광학 관측 가능성은 기본 가정에 없다.

# proposition_A

## name

고정 기하와 고정 β(p) 아래 arbitrary observer 1-jet의 완전 실현

## status

derived

## statement

고정된 smooth Lorentzian metric g와 p의 미래방향 정규화 벡터 U₀를 주자. U₀^b K_ab=0을 만족하는 모든 K_ab에 대하여 U(p)=U₀, ∇_aU_b(p)=K_ab인 smooth 미래방향 unit congruence가 p의 근방에 존재한다. 따라서 고정 U₀에 대한 admissible 1-jet 공간은 12차원이며 (θ,σ,ω,A)에 선형 일대일 대응한다. 고정 Einstein solution (g,T) 위에서도 U를 독립 관측자장으로 취하면 이 결론은 변하지 않는다.

## proof

- 필요성: ∇_a(U·U)=2U^b∇_aU_b=0이므로 K의 네 개 output-orthogonality 조건이 필요하다. 이 네 선형 조건은 독립이어서 16−4=12차원이다.
- 충분성: p를 원점으로 하는 normal coordinates를 택한다. g(p)=η, ∂g(p)=0이며 U₀=cE₀가 되도록 tetrad를 선택한다. W^b(x)=U₀^b+g^{bd}(p)K_ad x^a로 둔다. W는 p 근방에서 미래 timelike이다. U^b(x)=cW^b(x)/sqrt(−g_cd(x)W^c(x)W^d(x))로 정규화한다.
- p에서 분모는 c이다. ∂_a[g(W,W)](p)=2U₀^bK_ab=0이므로 정규화 인자의 1차 미분은 0이다. 따라서 U(p)=U₀ 및 ∇_aU_b(p)=K_ab가 정확히 성립한다. 미리 지정한 유한 K의 크기에 따라 필요한 근방이 작아질 수 있다.
- U-rest tetrad에서 K_a0=0, K_0i=A_i/c=a_i, K_ij=(θ/3)δ_ij+σ_ij+ε_ijkω_k이다. scalar trace 1개, symmetric tracefree 5개, antisymmetric 3개, temporal-spatial 3개가 서로 독립이며 모든 K를 유일하게 분해한다.
- 주어진 β₀와 N(p)에 대해 U₀=γ₀[N(p)+cβ₀]로 고정한 뒤 같은 구성을 적용한다. β(x)는 U와 N에서 정의되므로 동일 β(p)를 가지면서 모든 12성분 first jet를 실현한다. 연속성에 의해 각 실현의 충분히 작은 근방에서 |β|<1이 유지된다.
- Einstein 식은 g와 T의 관계이며, 그 식에 들어가지 않는 별도 observer U의 1-jet을 제한하지 않는다. 따라서 g,T를 고정해도 구성이 성립한다. 이는 T의 특정 timelike 고유벡터를 U로 요구하는 경우에는 적용되지 않는다.

## stronger_velocity_bound_observation

Minkowski 공간에서 β(p)=0인 경우에는 작은 compact support를 이용해 고정 속도 ceiling 0<b_*<1도 유지하면서 임의 K를 실현할 수 있다. 예를 들어 w_i(x)=χ(x/δ)K_ai x^a/c, U=(c sqrt(1+|w|²),cw)로 두면 ∇_aU_i(p)=K_ai이고 |β|=|w|/sqrt(1+|w|²)이다. χ는 p 근방에서 1인 smooth bump이며 δ를 K 크기에 반비례하도록 작게 택하면 |β|≤b_*이다. 유계 속도는 미분 bound가 아니다. 이 보조 예는 전역 우주론 congruence나 같은 spatial-homogeneous branch를 주장하지 않는다.

## consequence

기하·Einstein 2-jet·β(p)만으로 arbitrary observer의 θ, σ, ω, A에 유한 보편 국소 budget을 부여할 수 없다. R2 광학 사상은 이 12성분을 이상적인 local ray derivative 자료가 주어졌을 때 분리하지만, boost 값 또는 static sky의 측정이 그 derivative 자료를 자동 제공하지 않는다.

# proposition_B

## name

비축퇴 물질 고유벡터의 정확한 first-jet 복원과 전 운동학 공동 상계

## status

derived

## assumptions

- T_ab는 p 근방에서 smooth symmetric tensor이며 미래 timelike 고유벡터 branch U가 물리 congruence로 지정되어 있다: T^a_b U^b=−εU^a, U·U=−c².
- S_T=hTh를 U-rest space의 self-adjoint endomorphism으로 해석하고 L=S_T+εI를 정의한다. L의 고유값 ε+λ_i가 모두 0이 아니어야 한다. δ=min_i|ε+λ_i|>0. 이는 단순 timelike 고유값과 spatial 고유값 사이의 gap이다.
- 공동 미분 예산은 같은 U-rest frame에서 정의한다. E₀=u와 right-handed orthonormal E_i를 택하고 D_μ^a=h^a_b(∇_{E_μ}T^b_c)u^c, μ=0,1,2,3으로 둔다. 각 D_μ는 spatial vector이고 단위는 J m⁻⁴이다. ||D||²=Σ_μΣ_i(D_μ^i)²는 Lorentz 부호의 tensor contraction이 아니라 명시한 observer-positive norm이다.

## exact_formula

∇_{E_μ}U=−c L⁻¹D_μ. 동치로 ∇_aU^b=−(L⁻¹)^b_d h^d_e(∇_aT^e_f)U^f.

## bound

θ²/3+||σ||²_F+2|ω|²+|A|²/c² = Σ_μ|∇_{E_μ}U|² ≤ c²||D||²/δ².

## proof

- 고유벡터 식을 미분하면 (∇_aT)U+T∇_aU=−(∂_aε)U−ε∇_aU이다. 정규화에 의해 ∇_aU는 spatial이다. h를 적용하면 고유값 미분 항이 소거되고 [hTh+εh]∇_aU=−h(∇_aT)U를 얻는다. L이 가역이므로 정확 복원식이 따른다.
- T의 symmetry와 timelike eigenvector 조건 때문에 T는 U-rest space를 보존하며 S_T는 그 양의 Euclidean 내적에 대해 self-adjoint이다. 따라서 ||L⁻¹||₂=1/δ이고 Σ_μ|∇_{E_μ}U|²≤c²||D||²/δ²이다.
- K_0i=A_i/c, K_ij=(θ/3)δ_ij+σ_ij+ε_ijkω_k를 사용한다. trace, STF, antisymmetric 부분은 Frobenius 내적으로 서로 직교하므로 Σ_μ|∇_{E_μ}U|²=|A|²/c²+θ²/3+||σ||²_F+2|ω|²가 정확히 성립한다.
- Perfect fluid branch T_ab=(ε+P)U_aU_b/c²+Pg_ab에서는 L=(ε+P)I이다. ε+P≠0이면 ∇_aU^b=−h^b_d(∇_aT^d_e)U^e/(ε+P)이며 위 norm 부등식은 equality다. 더 일반적으로 D의 모든 nonzero column이 최소 절댓값 고유공간에 놓일 때 equality다. 따라서 1/δ 상수는 algebraic norm estimate로 날카롭다.

## positive_sufficient_budget

같은 상태에서 δ≥δ_*>0 및 ||D||≤d_*<∞가 실제 주어지면 B_*=c d_*/δ_* (단위 s⁻¹)에 대해 θ²/3+||σ||²_F+2|ω|²+|A|²/c²≤B_*²라는 공동 타원체 outer bound가 생긴다. 따라서 |θ|≤sqrt(3)B_*, ||σ||_F≤B_*, |ω|≤B_*/sqrt(2), |A|/c≤B_*이다. 이 타원체는 개별 marginal bound를 임의 조합한 것이 아니라 한 개의 선언된 joint derivative norm에서 유도되었다. 모든 boundary point의 Einstein-matter attainability까지 주장하지 않는다.

## tilt_and_degeneracy

- T(p)의 비축퇴 미래 timelike 고유벡터와 N(p)가 주어지면 β(p)는 U=γ(N+cβ)로 이미 결정된다. 따라서 β를 12개 derivative 성분과 별도의 자유 physical parameter로 다시 추가하지 않는다. 단, T/N이 불확실하면 동일 joint state에서 β도 함께 전파해야 한다.
- δ 또는 comoving ||D||의 크기만으로 기준 N에 대한 β ceiling은 얻을 수 없다. Lorentz-boosted stress는 같은 고유값·같은 comoving norm을 갖고도 N에 대한 speed가 임의로 1에 가까울 수 있다. 별도 상대-frame 정보가 필요하다.
- ε+P=0인 T_ab=−εg_ab 또는 vacuum은 L=0이다. 특히 상수 ε의 cosmological-constant stress는 모든 timelike vector를 고유벡터로 허용하며 ∇T=0이어도 U의 1-jet을 고르지 않는다. δ>0 가정은 제거할 수 없다.
- 고유값 gap이 작은 상태에서는 inverse bound가 악화된다. 유한 ||D||만으로 균일한 kinematic bound를 주장하려면 양의 하한 δ_*도 필요하다.

# proposition_C

## name

Einstein-selected congruence의 일반적 metric jet 차수: 3은 충분, 2는 부족

## status

derived

## sufficiency

Einstein 식에서 T^a_b=κ⁻¹(G^a_b+Λδ^a_b), ∇T=κ⁻¹∇G이다. 따라서 g의 3-jet와 상수 κ,Λ가 T(p),∇T(p)를 정하고, 명제 B의 단순 timelike 고유벡터 선택 및 δ>0 아래 U(p),∇U(p)를 정한다. Metric 2-jet는 T(p)와 U(p)를 정할 수 있으나 ∇T(p)를 일반적으로 정하지 않는다. 다음 family가 이 차수를 단순한 차원계산이 아니라 반례로 판별한다.

## counterexample_family

- p=0, x⁰=ct, η=diag(−1,1,1,1), b>0 (단위 m⁻²), λ∈R (단위 m⁻³)를 고정한다. φ_λ(x)=−b(x⁰)²−(b/2)[(x¹)²+(x²)²+(x³)²]+(λ/2)(x⁰)²x¹, g_λ=e^(2φ_λ)η로 둔다. Λ=0, T_λ=G[g_λ]/κ로 정의한다.
- 모든 λ에서 φ(0)=0, ∂φ(0)=0, φ_00(0)=−2b, φ_ij(0)=−bδ_ij, φ_0i(0)=0이다. 따라서 모든 g_λ는 같은 metric 2-jet를 갖는다. λ가 바꾸는 첫 미분은 φ_001=λ 및 그 순열인 3차 jet이다.
- 직접 Christoffel 식 Γ^a_bc=δ^a_bφ_c+δ^a_cφ_b−η_bcφ^a에서 R_ab=−2φ_ab−η_ab□_ηφ+2φ_aφ_b−2η_ab(∂φ)²_η, G_ab=−2φ_ab+2φ_aφ_b+2η_ab□_ηφ+η_ab(∂φ)²_η를 얻는다. p에서는 gradient 제곱 항이 0이고 □φ=−b이다.
- 따라서 G_00(p)=6b, G_0i(p)=0, G_ij(p)=0. 모든 λ에 대해 T^a_b(p)=diag(−6b/κ,0,0,0), ε=6b/κ>0, spatial pressure 고유값은 0이다. 선택된 미래 timelike eigenvector는 U(p)=c∂₀, spectral gap은 δ=6b/κ이다. 기준 N(p)=c∂₀로 두면 β(p)=0 역시 모든 λ에서 같다.
- p에서 Γ=0 및 ∂g=0이므로 covariant derivative와 좌표 derivative가 일치한다. G_i0=−2φ_i0+2φ_iφ_0이므로 ∂_μG_i0(p)=−2λ δ_μ0 δ_i1. Mixed tensor T^i_0에도 같은 값/κ가 적용된다. 따라서 명제 B에서 D_μ^i=−2λ δ_μ0 δ_i1/κ이다.
- 정확 복원식은 ∇_{E₀}U¹(p)=−c(−2λ/κ)/(6b/κ)=cλ/(3b), 나머지 spatial output first-jet 성분은 0을 준다. 그러므로 A¹(p)=c²λ/(3b), θ(p)=0, σ(p)=0, ω(p)=0이다. 모든 λ에서 g의 2-jet, T(p), U(p), β(p), spectral gap이 같은데 가속도는 λ에 비례하여 무한히 커진다.
- 수동 교차검산: ∂₁G_00(p)=0, ∂₁G_11(p)=−2λ, ∂₀G^0_1(p)=2λ여서 ∂_aG^a_1(p)=0이다. 이 운동량보존 식은 가속도 부호와 pressure-gradient balance에 맞는다. Norm 식도 |A|²/c²=c²λ²/(9b²)=c²||D||²/δ²로 equality를 준다.

## local_source_validity

- g_λ는 각 유한 λ에서 smooth Lorentzian metric이다. T_λ=G[g_λ]/κ이므로 Einstein 식과 contracted Bianchi identity에 따른 ∇·T=0을 정확히 만족한다. 수치 진화나 PDE solution을 호출한 것이 아니다.
- p의 timelike 고유값은 spatial 고유값에서 양의 gap으로 분리된다. 따라서 충분히 작은 근방에서 smooth 미래 timelike eigenvector branch가 유지된다. Spatial restriction은 positive definite rest metric에서 symmetric이므로 real spatial eigenvalues를 갖는다.
- p에서 ε>0 및 ε>|P_i|가 strict하므로 각 유한 λ에 대해 충분히 작은 근방에서는 type-I dominant-energy inequalities도 유지된다. λ 전체에 공통인 근방 크기나 미분 bound는 보장하지 않는다.
- p의 stress 형태는 pressureless이지만 근방 전체의 perfect-fluid 조건·dust EOS·특정 물질 작용은 가정하거나 증명하지 않았다. 따라서 이를 Einstein-dust solution family로 부르면 잘못이다. 이는 일반적 smooth Einstein-source 및 물리 eigenvector 선택 계약에 대한 반례다. 추가 EOS/대칭성/동역학 조건은 허용 family를 줄일 수 있다.

## interpretation

'metric 3-jet가 첫 일반적 충분 차수'는 비축퇴 stress-eigenvector 선택 계약에 관한 것이다. 특정 matter model이나 symmetry가 낮은 jet 자료를 추가 식으로 닫는 예외를 배제하지 않는다. Arbitrary observer는 metric의 전체 germ를 알아도 별도 congruence 1-jet가 필요하다.

# lie_geometry_and_optics_intersection

- 일반 Lie 구조상수 C_ij^k와 Jacobi만으로 이 결과에 numerical scale 또는 matter selection을 보태지 못한다. R2의 Koszul 연결에 metric·시간 metric jet·lapse·β field jet를 주면 kinematics를 계산할 수 있다는 기존 충분조건은 유지한다.
- 명제 A의 observer는 homogeneous geometry 위에서도 일반 smooth congruence이다. 'tilt의 invariant 공간 성분이 위치에 무관하다'라는 추가 제약을 넣으면 허용 1-jet가 줄어들며 I1의 3차원 fixed-geometry time-jet 식 같은 관계가 생긴다. A의 12차원 전사성을 그 restricted branch에 적용하지 않는다. 본 반례는 허용된 일반 manifold branch에 속하고 Bianchi type을 고르지 않는다.
- R2의 정확한 광학/복사 제약과 새로운 충분조건의 합성은 같은 물리 state ξ에서 K_joint={k(ξ): J_B(ξ)k(ξ)∈R(ξ), T(ξ)U(ξ)=−ε(ξ)U(ξ), δ(ξ)>0, ||D(ξ)||≤d_*}라는 교집합이다. δ≥δ_*까지 있으면 명제 B의 타원체를 이 집합의 outer bound로 사용할 수 있다.
- 타원체를 특정 MES 원전이 증명한 ceiling으로 부르지 않는다. 이는 명시한 stress first-jet 예산의 조건부 물리 bound다. 유용한 실제 δ_*와 d_*는 현재 입력에서 제공되지 않는다. 따라서 numerical percentage, 모든 15성분 데이터 추론, likelihood calibration은 산출하지 않는다.
- 공동 body로 사용할 때 선택한 reference state를 실제 physical feasible set에서 빼야 한다. 원점을 포함하는 상대 내부와 유계성 등 R2 gauge 조건은 따로 확인한다. β가 고정된 affine slice이면 15차원 full-interior body인 척하지 않고 해당 slice/식별공간을 사용한다. θ_ref를 빼는 문제와 θ 자체의 상계를 혼동하지 않는다.
- T,∇T,β와 optical residual을 같은 실험에서 추정한다면 동일 joint uncertainty를 전파해야 한다. 위 상계는 새로운 관측 정보를 생성하거나 분모와 분자를 독립화하지 않는다. Signed σ, axial ω, polar A 및 β 값은 norm 계산 뒤에도 보존한다.

# completion_and_limitations

## completed

- 임의 정규화 observer first-jet의 완전한 국소 실현 증명
- stress eigenvector spectral-gap inverse의 정확한 유도
- θ·σ·ω·A를 함께 포함하는 명시적 sharp joint norm 상계
- 동일 Einstein metric 2-jet와 동일 β에도 물리 선택 가속도가 임의로 커지는 analytic family와 부호·단위·보존 교차검산
- Lie/homogeneous 제한, vacuum degeneracy, static optical data, MES normalization과의 합성 경계

## unresolved

- 실제 관측/물질 모델이 제공하는 δ_*와 stress derivative 예산 d_*
- 특정 EOS·공간균질 invariant congruence·고정 시간구간을 추가한 경우의 더 강한 bound
- 전체 empirical likelihood 및 numerical MES budget fraction
- 학술적 신규성과 외부 문헌의 포괄 조사

## claim_ceiling

수동으로 재현 가능한 국소 analytic derivation 및 counterexample. 기존 I2/I3, repository CAS4, empirical fit, native solver, 전역 Einstein-matter 존재성의 상태는 변경하지 않는다. 독립 decision reviewer의 최종 판정 전에는 PROMOTE를 부여하지 않는다.



---

# 부록: STATISTICS_RESULTS_KO.md

# 동일 자료의 조건부 support profile, 응답 몫 게이지 및 공동 피복 정리

## 0. 범위·기호·출처 우선순위

이 결과는 수기 해석 유도이다. 수치 적분, ODE/PDE/Boltzmann 해법, CAS·형식엔진, 과학 코드 실행을 하지 않았다. Python은 입력 hash 확인과 이 JSON 직렬화에만 사용했다. 실제 자료에 대한 likelihood 적합, coverage 보정, 관측 백분율은 산출하지 않았다. 특정 Bianchi 형식을 선택하지 않는다.

현재 기본 객체는 첨부 보고서 §23의 공동 물리 상태 X와 함수족 φ_j(X)이다. x는 sample-by-functional 배열, Q는 premise-anchor gauge/margin·구간, F는 방향별 support-utilization profile, Pi는 선언한 법칙의 functional exceedance와 부분식별 envelope, G_F는 depth·mask·feature transport/coherence 경로이다. 이하 현재 F를 F_dir 또는 U_C로 쓴다. R2의 외적 mathbb Q=T⊗T, 양의 스칼라 F=||T||², tensor tail 및 성장비는 각각 mathbb Q_R2, F_rad, mathbb Pi_R2, G_rad로 별도 표기한다. 서로 같은 기호로 바꾸어 현재 formalism을 덮어쓰지 않는다.

R2 §3–7의 radial gauge, tensor normalization, projected body, tensor-tail trace, growth norm identity 및 같은 자료 분모에 대한 주의는 상속 결과이다. 첨부 §16의 같은 가능집합 위 최적화와 §23의 고정-body support profile도 상속한다. 여기서는 불확실 기준점·몸체를 포함하는 같은 상태별 비율의 support 쌍대성, 그 공동 피복 보존, 응답 몫의 섬유 최솟값 및 동일법칙의 신뢰집합 직경 하한을 증명한다. 이는 이번 루프의 엄밀한 강화이며 학술적 신규성 주장이 아니다.

물리 기호는 signature (−,+,+,+), c 명시를 유지한다. 하나의 선언된 congruence·frame·H_*>0에서 무차원 좌표의 예는 k=(δθ/H_*,σ/H_*,ω/H_*,A/(cH_*),β_RM,β_MO)이다. β_RM은 물리적으로 선택한 기준 congruence와 물질 사이의 tilt, β_MO는 물질과 관측자 사이의 local boost로 별도 슬롯을 둔다. θ·σ·ω는 s⁻¹, A는 m s⁻², β는 무차원이다. θ/θ로 새 팽창 정보를 만들지 않는다. 전체 유한 표현공간은 이 예에서 18차원이며, 한 속도 슬롯만 필요하면 R2의 15차원이다. ω는 axial, A·β는 polar, σ는 STF²이다. 방향·metric·rank 간 가중치는 분석 전에 정하며 회전 시 frame·response·body도 함께 변환한다.

이 정리들이 모든 슬롯을 수용한다는 사실은 모든 슬롯의 MES 상계가 확보되었다는 뜻이 아니다. 각 함수에는 실제로 허용된 premise와 같은 단위·frame·epoch·지지집합의 anchor가 있어야 한다. 유한 anchor가 없는 θ/A/β 또는 다른 함수는 unavailable/uncontrolled로 남긴다. 속도 인과 한계 |β|<1을 MES 관측상계로 바꾸지 않는다.

## 1. 정의와 가정

Z는 분자 X뿐 아니라 기준 r, 몸체 입력 χ, 공유 nuisance·source, 여러 depth의 상태와 필요한 transport 입력을 함께 포함하는 하나의 잠재/모수 상태이다. 같은 자료 d로 모두 추정할 수 있다. 독립성은 가정하지 않는다.

한 함수 j를 고정하여 y(Z)=φ_j(X)−φ_{j,ref}(r)∈E로 쓴다. E는 선언된 유한 차원 실수 내적공간이며 φ_j는 scalar·vector·tensor 또는 허용된 직접합일 수 있다. B_χ⊂E는 해당 y에 대해 사용이 허용된 compact convex body이고 0∈int B_χ이다. 비선형 φ_j를 쓸 때 B_χ는 그 함수의 출력공간에서 정당화된 body이어야 하며, 원래 물리 body를 임의로 같은 body라고 부르지 않는다. 필요하면 검증된 outer body라고 명시한다.

h_{Bχ}(u)=sup_{b∈Bχ}〈u,b〉, γ_{Bχ}(y)=inf{t≥0:y∈tBχ}이다. u≠0이면 h_{Bχ}(u)>0이다. 몸체는 비대칭이어도 된다. C=C(d)는 Z의 비어 있지 않은 공동 집합이다. 동일 상태별 방향 비율과 양 끝을

  r_Z(u)=〈u,y(Z)〉/h_{Bχ(Z)}(u),
  U_C(u)=sup_{Z∈C} r_Z(u),  L_C(u)=inf_{Z∈C} r_Z(u)

로 정의한다. 분자·기준·분모는 반드시 같은 Z를 사용한다. U_C는 현재 F의 uncertain-body 확장이다. 분모가 0이거나 유한하지 않거나 body premise가 적용되지 않으면 해당 방향의 비율을 정의하지 않고 별도 상태를 반환한다.

고정 외부 body B에서는 U_C(u)=h_{y(C)}(u)/h_B(u)이다. 따라서 유한 식별집합을 쓰는 첨부 §23의 F⁺를 정확히 회수한다. 그러나 χ가 변하면 일반적으로 sup_Z〈u,y(Z)〉/sup_Z h_Bχ(Z)(u)가 아니다.

## 2. 정리 S1: 불확실 몸체의 같은 상태별 support 쌍대성

위 가정과 모든 단위 방향 u에 대하여

  (S1.1) γ_{Bχ}(y)=sup_{||u||=1} 〈u,y〉/h_{Bχ}(u),
  (S1.2) sup_{||u||=1} U_C(u)=sup_{Z∈C} γ_{Bχ(Z)}(y(Z)).

따라서 C의 모든 상태가 각자의 조건부 body에 속하는 것과 U_C(u)≤1이 모든 방향에서 성립하는 것은 동치이다. RHS가 1 이하라는 것은 선언된 조건부 body와의 집합적 양립성이지 MES premise의 자료에 의한 독립 검증이나 공간 체적 비율이 아니다.

증명. compact convex B에 대해 y∈tB이면 모든 u에서 〈u,y〉≤t h_B(u)이므로 각 비율은 γ_B(y) 이하이다. 반대로 y≠0이고 0<t<γ_B(y)이면 y∉tB이다. 유한 차원에서 점과 닫힌 볼록집합의 엄격 분리에 의해 어떤 u≠0에 대해 〈u,y〉>t h_B(u)가 성립한다. 비율의 u-양의 동차성으로 u를 단위화할 수 있다. t↑γ_B(y)를 보내면 supremum≥γ_B(y)이다. y=0에서는 두 값이 0이다. 이로써 S1.1을 증명했다. S1.2의 양변은 같은 곱집합 C×{||u||=1}에서 같은 함수 r_Z(u)의 supremum이므로 supremum 순서를 교환해도 같다. 독립 χ, 고정 분모 또는 convex C를 요구하지 않는다. 마지막 동치는 S1.1과 y∈B ⇔ γ_B(y)≤1에서 따른다. 끝.

최대와 witness 존재. C가 compact, y가 연속, χ↦Bχ가 Hausdorff 연속이고 어떤 b₀>0에 대해 b₀ 단위공⊂Bχ가 C 전체에서 성립하면 r_Z(u)는 compact 곱집합 위 연속이다. 따라서 위 supremum은 maximum이고 상태–방향 witness (Z*,u*)가 존재한다. 이 조건이 없으면 supremum이라고만 한다. 유한 방향 grid의 최대는 전체 방향 supremum의 하한일 뿐이며 별도의 오차 인증 없이 전 구면 최대라고 할 수 없다.

Antipodal 주의. 현재 보고서 구현의 F±(u)=max{h_I(u),h_I(−u)}/h_B(u)는 그대로 그 정의를 보존한다. 반대 방향의 실제 anchor까지 비교하는 새 진단을 원하면 max{U_C(u),U_C(−u)}라고 별도 정의하여 각각 h_Bχ(u),h_Bχ(−u)를 사용해야 한다. 비대칭 B에서 이 둘은 다른 함수이다.

## 3. 정리 S2: 같은 자료의 공동 신뢰집합 사상은 모든 방향·함수·depth 피복을 동시에 보존한다

실제 고정 상태 Z₀의 자료법칙 P_{Z₀}에 대해 공동 집합 Cα(D)가

  inf_{Z₀∈Z_domain} P_{Z₀}{Z₀∈Cα(D)} ≥ 1−α

를 만족한다고 가정한다. 이것은 입력 가정이며 이 유도만으로 실제 관측에서 달성되었다고 주장하지 않는다. Ψ는 기준·몸체·여러 depth의 공유 변수를 모두 포함하는 Z의 선언된 measurable 함수족이다. 집합 사상과 사건의 measurability를 가정한다. 그러면

  P_{Z₀}{Ψ(Z₀)∈Ψ(Cα(D))} ≥ 1−α.

여기서 Ψ는 모든 r_Z(u), Q의 gauge/margin, raw φ_j, morphology tensor, 허용된 scalarization과 같은 상태별 비율, 정의된 depth transport/coherence를 한꺼번에 반환할 수 있다. 특히 확률 ≥1−α로 모든 j·모든 연속 방향 u·모든 등록 depth에 대해

  L_{Cα,j}(u) ≤ r_{Z₀,j}(u) ≤ U_{Cα,j}(u)

가 동시에 성립한다. α를 방향 개수로 나누는 새 Bonferroni는 필요하지 않다. 이미 원 상태의 하나의 공동 피복사건에서 전부 따라오기 때문이다.

증명. 각 D에 대해 {Z₀∈Cα(D)}⊂{Ψ(Z₀)∈Ψ(Cα(D))}이다. 따라서 사건의 확률 단조성으로 결론이 즉시 따른다. 같은 사건 위에서 모든 u와 j의 값이 각 inf/sup 사이에 놓이므로 동시 방향 피복도 성립한다. 독립 주변구간의 피복을 곱한 것이 아니다. 랜덤 latent Z를 대상으로 하는 predictive/joint coverage를 사용할 경우에도 P{Z∈Cα(D)}≥1−α라는 원 사건에 같은 포함관계를 적용한다. 이는 고정모수 빈도론 coverage와 구별해 표기한다. 끝.

같은 자료의 χ̂(D)·r̂(D)를 고정 외부값처럼 넣어 C의 χ/r 축을 삭제한 뒤, 원래 참 χ₀/r₀에 대한 피복을 위 정리로 주장할 수 없다. 그렇게 만든 사상은 다른 추정 대상이거나 검증되지 않은 plugin 근사이다. 정확한 χ·r의 joint set을 유지하거나, 그 plugin target 자체와 law를 따로 정의해야 한다.

Bayesian 대응. 선언한 공동 posterior μ_d(dZ)가 있을 때 법칙은 μ_d^Ψ=Ψ#μ_d로 정확히 사상한다. μ_d(C)≥1−α이면 μ_d^Ψ(Ψ(C))≥1−α이다. 이 posterior 질량 사실은 빈도론 coverage 증명이 아니다. 같은 자료에서 뽑은 numerator·body·reference를 서로 독립 posterior처럼 곱하지 않는다.

현재 Pi 연결. 사전 지정 scalarization s_j 또는 acceptance set으로 사건 E_{j,c}를 정하면 Π_j(c|d,η,L)=∫1_{E_{j,c}(Z)} μ_{d,η,L}(dZ)이다. 허용된 η 또는 law family H에 대한 inf/sup는 바로 이 공동 pushforward probability의 envelope이다. S2의 상태집합만으로 고유 Pi 값을 얻을 수 없으며 법칙이 없으면 unresolved이다. 각 envelope 끝점의 최적화 가능성도 별도로 증명해야 한다. R2 projector-tail tensor mathbb Pi_R2(q)는 μ_d를 같은 상태별 T에 사상한 뒤에만 계산한다. 그 trace=Pr(F_rad>q) 항등식은 R2 상속이며 현재 Pi 전체를 대체하지 않는다.

성장비 특수 경우. R2 양의 quadratic 진단으로 G_rad=F_rad,a/F_rad,b를 추가 보고할 때 두 depth를 포함한 같은 Z와 F_rad,b>0인 정의역에서 Ψ에 넣는다. C가 compact, 두 F가 연속, inf_C F_rad,b>0이면 유한 최솟값·최댓값이 존재한다. 더 일반적으로 정의역 C⁺={Z∈C:F_rad,b>0}에서 upper bound가 유한할 필요충분조건은 어떤 유한 M에 대해 F_rad,a≤M F_rad,b가 모든 C⁺에서 성립하는 것이다. 이는 비율 부등식 양변에 양의 F_rad,b를 곱하면 양방향으로 즉시 따른다. 양의 분모 하한은 충분조건이지 필요조건이 아니다. C에 F_rad,b=0 상태가 남으면 그 branch에서는 비율이 undefined이며 공동 (F_rad,a,F_rad,b)를 유지한다. 현재 G_F는 이 scalar ratio가 아니라 구조화된 경로이므로 signed tensor transport와 coherence도 동시에 유지한다.

MES 조건부 제한. 참 상태가 속한다고 가정한 물리 정의역 Dη 또는 MES 집합으로 C를 교차하면 그 가정 하에서만 원 피복을 보존한다. 제한 model에서 outside probability가 0인 것은 조건의 결과이며 MES의 검증 증거가 아니다. 빈 집합은 유지한 조건·자료영역 간 불일치로 기록하며 p-value로 바꾸지 않는다.

## 4. 정리 S3: 응답 몫의 게이지는 섬유 최소값이며 support는 관측 가능한 쌍대방향으로 제한된다

p:E→V=p(E)를 고정 선형 사상, K=ker p라고 하자. 물리적 관측 해석에는 이 p가 해당 y 좌표에 실제로 작용하는 response quotient여야 한다. k에 대한 선형 response를 비선형 함수 φ_j(k)에 그대로 적용할 수는 없으며, 그런 함수는 S4의 섬유별 값 범위로 처리한다. V의 내적은 선언하고 p*는 adjoint이다. 각 Bχ의 올바른 quotient body는 pBχ이다. 유한 차원이므로 pBχ는 compact convex이고 V에서 0이 상대내점이다. 모든 v∈V에서

  (S3.1) γ_{pBχ}(v)=min_{y:py=v} γ_Bχ(y),
  (S3.2) h_{pBχ}(u)=h_Bχ(p*u).

이에 따라 같은 상태별 관측 profile은

  U_C^p(u)=sup_{Z∈C} 〈p*u,y(Z)〉/h_Bχ(Z)(p*u),
  sup_{||u||_V=1}U_C^p(u)
    =sup_{Z∈C} min_{y':py'=py(Z)} γ_Bχ(Z)(y')
    ≤sup_{Z∈C}γ_Bχ(Z)(y(Z)).

증명. y∈tB이면 py∈tpB이므로 γ_pB(py)≤γ_B(y); 섬유의 모든 y에 대해 성립한다. v≠0에 대해 t*=γ_pB(v)>0이다. pB가 compact이고 원점을 내점으로 포함하므로 v∈t*pB이며, 어떤 b∈B가 v=t*pb를 만족한다. y*=t*b를 택하면 py*=v이고 γ_B(y*)≤t*. 앞 부등식과 합하면 등호이고 최솟값을 달성한다. v=0이면 y*=0이 달성한다. S3.2는 sup_{v∈pB}〈u,v〉=sup_{b∈B}〈p*u,b〉에서 바로 따른다. p가 V로 전사이므로 u≠0이면 p*u≠0이다. S1을 각 projected body에 적용하고 supremum의 순서를 교환하면 profile 식과 마지막 부등식이 따른다. 끝.

해석. γ_pB(v)>1이면 관측 v와 같은 모든 lift가 B 밖이다. γ_pB(v)≤1이면 그 섬유에 적어도 하나의 B 내부 lift가 존재한다는 뜻이다. 실제 미관측 lift가 B 내부라고 결론낼 수 없다. K≠{0}이고 전체 E를 허용하는 순수 대수 domain이면, h∈K\{0}, y_t=y₀+t h에서 γ_B(y_t)→∞이다. 실제로 B⊂R 단위공인 R<∞를 택하면 γ_B(y_t)≥||y_t||/R→∞이다. 따라서 같은 응답의 최소 게이지는 작은 반면 실제 가능한 게이지는 대수적으로 임의로 클 수 있다. 물리 domain·인과 속도·field constraint를 추가하면 섬유가 잘리므로 이 무한대 결론을 무조건 물리 상태에 적용하지 않는다. 다만 서로 다른 두 허용 lift만 있어도 아래 식별불가능성은 남는다.

이 결과는 R2의 'projection이지 intersection이 아니다'를 새 발견으로 반복하지 않는다. 그것을 섬유 최적화와 §23의 방향별 F에 연결하여 정확한 정보 손실 크기와 논리 방향을 추가한다. pE가 단순 tensor 표현공간이 아닐 수 있으므로 p y를 모든 원래 sector의 완전한 관측 tensor라고 부르지 않는다. 이는 response가 식별한 조합이다.

## 5. 정리 S4: 응답동등 상태의 함수·morphology·전역/국소 속도 구분 한계

관측모형은 D=μ₀+Rk+Nη+ε이고, ε의 전체 법칙은 (k,η)에 독립이라고 하자. 고정 covariance의 Gaussian은 한 특수 경우일 뿐이다. nuisance 계수는 아래 두 상태가 허용되는 범위에서 자유롭다. K_obs={h:Rh∈range N}라 두고, p의 kernel을 K_obs로 정한다. Rh=Nc이면

  R(k+h)+N(η−c)=Rk+Nη.

따라서 두 허용 상태 (k,η), (k+h,η−c)는 정확히 같은 자료법칙을 갖는다. 이 진술은 단순 Jacobian 선형화로 정의한 R에는 해당 선형 근사에서만 적용된다. 실제 비선형 response가 이 변환을 깨면 전역 동일법칙을 주장하지 않는다.

(a) 함수 f가 quotient에 내려갈 필요충분조건은 허용 domain 안의 모든 같은 응답 섬유에서 f가 상수인 것이다. 필요성은 f= f̄∘p이면 py₁=py₂에서 값이 같기 때문이다. 충분성은 f̄(v)를 v의 아무 허용 lift의 f값으로 정의하면 섬유 상수성으로 잘 정의되기 때문이다. 섬유 밖 존재는 요구하지 않는다. signed morphology·sector amplitude·legacy signed x·일반 φ_j는 이 조건을 별도로 확인해야 한다. anchor normalization의 가역 좌표변환은 이 조건이나 data rank를 늘리지 않는다.

(b) 동일 자료법칙 P를 갖는 두 허용 상태 Z₀,Z₁에서 실수 관심량 f₀≠f₁이라고 하자. 임의 신뢰집합 Aα(D)가 두 상태 각각에서 coverage≥1−α이면

  P{{f₀,f₁}⊂Aα(D)}≥1−2α,
  P{diam Aα(D)≥|f₁−f₀|}≥1−2α.

증명. 동일 P 아래에서 E_i={f_i∈Aα(D)}는 P(E_i)≥1−α이다. 합집합 상계로 P(E₀∩E₁)≥1−2α이고, 이 교집합 위에서는 집합이 두 값을 함께 포함하므로 직경 하한이 성립한다. 끝. metric-valued tensor 관심량에서도 |f₁−f₀|를 그 선언된 거리로 바꾸면 동일하다. 같은 이유로 어떤 rejection event의 확률도 두 상태에서 같아, 한쪽에 대한 power가 다른 쪽의 size를 넘는 자료 판별을 만들 수 없다. Bayesian prior는 한 lift를 선호할 수 있으나 응답동등성 자체를 측정으로 해소하지 않는다.

(c) 국소 boost b와 물리 tilt t가 response에서 같은 선형 column H를 가지면 D의 신호는 H(b+t)이다. h=(v,−v)는 kernel 방향이다. 임의 0<ε<1 및 단위 v에 대해 (b,t)=(0,0)과 (εv,−εv)는 둘 다 |b|,|t|<1이고 같은 해당 선형 response를 갖지만 서로 다른 속도 morphology를 갖는다. 더 작은 ε를 택해 선언된 선형화 domain 안에 둘 수 있다. 모든 depth a에서도 두 column이 같으면 각 R_a h=0이므로 stack한 response에도 h가 남는다. depth 이름을 추가하는 것만으로 rank가 늘지 않는다. 다른 physical kernel·aberration·기준 congruence 제약 등이 실제로 선형독립 정보를 줄 때에만 구분이 가능하다.

물리 제약 예외. 첨부 §16처럼 domain 제약으로 섬유와의 교집합이 한 점이면 rank 결손이어도 해당 domain에서 점 식별이 가능하다. 위 불가능성 정리는 서로 다른 두 admissible 동일법칙 상태의 존재를 요구한다. 특히 전체 열 rank가 점 식별의 필요조건이라고 주장하지 않는다. 또한 경계 한 점 식별이 안정성·coverage를 자동 보증하지 않는다.

## 6. 명시적 손계산 반례와 경계 사례

CE1 — sup 비율과 주변 sup 비율은 다르다. 1차원 u=+1에서 두 공동 상태 (y,b)=(1,1),(100,1000), B_b=[−b,b]를 둔다. 같은 상태 비율은 1과 1/10이므로 U_C=1이다. 주변 supremum끼리 나누면 100/1000=1/10이어서 실제 포화 witness를 놓친다. 반대로 max y/min b=100은 유효한 느슨한 상계일 수 있지만 C에서 실현되지 않는 조합이며 sharp profile이 아니다.

CE2 — 기준·분모·분자의 공변동. t∈[1,2]에 대해 k=2t, r=t, B_t=[−t,t]인 공동 C를 둔다. 모든 상태에서 y=k−r=t, γ=1, radial T=+1이다. 주변 projection k∈[2,4], r∈[1,2], b∈[1,2]를 Cartesian 곱으로 확대하면 γ가 0부터 3까지 가능해진다. 이 확대가 원 공동 C를 포함한다면 coverage를 해치지는 않지만 실제 불확실성을 과장하고 존재하지 않는 상태를 만들어 sharpness를 잃는다. 반대로 작은 plugin body만 남기면 원 C 포함관계 자체가 깨질 수 있다.

CE3 — 각 95% 주변구간은 95% 공동 ratio coverage가 아니다. 참 s,b>0인 실험에서 관측 D=(s Z_s,b Z_b)이고, noise pair (Z_s,Z_b)는 (2,1),(1,2),(1,1)을 각각 확률 1/20,1/20,9/10으로 취한다고 정의한다. 관측 가능한 통계량 S={D_s}, B={D_b}를 쓴다. 따라서 사건 e_s에서 S={2s},B={b}; e_b에서 S={s},B={2b}; e_0에서 S={s},B={b}이다. 각 주변구간은 자기 참값을 확률 19/20로 포함한다. 그러나 ratio set S/B는 앞 두 사건에서 각각 2s/b,s/(2b)이므로 참 s/b를 확률 9/10로만 포함한다. 이는 독립성을 가장한 곱의 문제가 아니라 처음부터 공동 95% 피복사건을 확보하지 못한 문제이다. 이 예는 일반 s,b>0에 대해 같은 coverage를 가진 완전한 통계 실험으로 정의할 수 있으며, set가 singleton이어도 interval이다.

CE4 — 0에 가까운 성장분모는 상관관계에 따라 다르다. t∈(0,1]에서 (F_rad,a,F_rad,b)=(t,t)이면 분모 하한은 0이지만 G_rad=1이다. 같은 domain에서 (1,t)이면 G_rad=1/t로 unbounded이다. t=0을 포함하면 첫 예도 지정되지 않은 0/0 branch가 생기며 연속 확장을 새 정의 없이 자동 적용할 수 없다.

CE5 — projected gauge 0은 실제 isotropy가 아니다. E=R², B는 Euclidean 단위공, p(y₁,y₂)=y₁이고 실제 y=(0,1)이면 γ_B(y)=1, γ_pB(py)=0이다. 실제 tensor가 body 경계에 있는데 관측 quotient는 0이다. 이 차이는 S3의 섬유 최솟값이며 실제 morphology를 0으로 대입할 근거가 아니다.

CE6 — 동일 marginal law와 scalar growth도 depth coherence를 결정하지 못한다. ||v||=1인 signed tensor v를 정한다. 공동 posterior가 (T_a,T_b)=(v,v), (−v,−v)를 각각 확률 1/2로 주면 모든 draw에서 〈T_a,T_b〉=1, T_a−T_b=0이다. 이 두 marginal을 독립 곱으로 대체하면 네 조합이 각각 1/4이고, 절반에서 〈T_a,T_b〉=−1이므로 평균 coherence가 0이 된다. 두 법칙 모두 F_rad,a=F_rad,b=1, G_rad=1이며 각 depth의 marginal 및 mathbb Q_R2도 같다. 따라서 현재 G_F의 공동 signed transport 정보는 scalar ratio·각각의 외적·marginal만으로 복원되지 않는다. R=identity transport를 썼으며 다른 transport에서는 사전 선언된 등거리 R을 넣는다.

CE7 — 비대칭 anchor의 antipodal denominator. B=[−2,1], I={−2}, u=+1이면 보고서의 해당 구현 F±(+1)=max(−2,2)/1=2이다. 반면 각 반대방향 body support를 사용한 max{U(+1),U(−1)}=max(−2,2/2)=1이고 γ_B(−2)=1이다. 둘은 정의가 다르므로 구현의 F±를 일반 gauge라고 바꾸어 부르면 안 된다.

## 7. x·Q·F·Pi·G_F 소스 호환성과 상속 범위

현재 x: φ_j(X_i) 배열을 그대로 유지한다. tensor/vector를 사전 지정 근거 없이 하나의 scalar로 줄이지 않는다. θ·σ·ω·A·β_RM·β_MO와 그 signed 혼합함수는 적용 가능한 정의역에서 함께 처리한다.
현재 Q: Q_anchor=(γ_B(y),1−γ_B(y),해당 joint-image 구간)이다. R2 mathbb Q_R2=T⊗T는 morphology의 한 quadratic 파생량이며 현재 Q의 대체가 아니다. T를 버리면 동시 부호가 소실된다.
현재 F: 방향별 support-utilization이다. 고정 body일 때 §23 F⁺를 회수하고, 불확실 body일 때 S1의 U_C를 사용한다. F_rad=γ_B²는 별도 radial quadratic 진단이다. amplitude 백분율은 D_B=100(1−γ_B)이며 100(1−F_rad)와 다르다. 어느 것도 등방인 공간의 비율·probability·유의수준이 아니다.
현재 Pi: law-dependent functional exceedance surface와 law/premise family의 envelope이다. S2는 joint pushforward와 그 정의역을 제공하지만 실제 posterior·sampling law가 없으면 수치를 내지 않는다. mathbb Pi_R2 trace identity는 보조 파생량으로 상속한다.
현재 G_F: 공유 자료를 가진 depth·mask·feature transport/coherence 경로이다. S2의 Ψ에 joint path를 포함해 same-state mapping하며 CE6처럼 cross-depth dependence를 보존한다. R2 scalar G_rad=F_rad,a/F_rad,b와 mathbb G_R2의 norm identity는 별도 호환 view이지 현재 경로 전체가 아니다.

역사 scalar x 호환: R2가 기록한 legacy x=Σ_std²−W_std²+Ω_tilt+Ω_k,aniso, Q_legacy=N(x)/U, F_legacy=x/U의 정확한 전체 component 정의와 source 동치는 여전히 unresolved이다. signed cancellation 때문에 이 x를 모든 sector의 양의 gauge나 norm으로 쓰지 않는다. Ω_tilt를 |β|²라고 가정하지 않고, curvature를 다섯 운동학군에 몰래 추가하지 않는다. R2의 조건부 shear-only 수식 동치 범위는 상속하되 이번 결과에서 새로 원문을 검증하지 않았으므로 exact full-x equivalence로 확대하지 않는다. 현재 함수족 formalism의 기본 지위와 legacy scalar 호환 여부는 별개이다.

## 8. 이번 유도로 확보한 것과 남은 필수 한계

확보: 같은 참 χ·기준·다중 depth 상태를 포함하는 집합에 대해 방향별 F와 gauge의 정확한 관계, 공동 coverage 사상의 충분조건, quotient에서의 최소 gauge 의미, 동일법칙에서 개별 sector·morphology 신뢰집합의 비축소 한계를 손계산으로 증명했다. 이는 R2의 고정/추정 body 경고를 정리 수준으로 강화하고 현재 §23 formalism에 연결한다.

미확보: 실제 자료의 calibrated joint Cα, 실제 tensor posterior, 모든 운동학군에 적용되는 유한 MES body, 전역/국소 속도를 구별하는 실제 물리 response, 원 historical x의 완전한 정의, 최적화 알고리즘·CAS 인증·real-data 판정·학술적 신규성. 실제 confidence region을 만들 때 nonlinear response remainder, covariance support·null residual, mask·beam·shared nuisance를 유지해야 한다. 원자료 likelihood의 동일법칙 여부를 먼저 점검하고, prior·물리조건 때문에 좁아진 구간을 새 관측 rank로 설명하지 않는다.

독립 reviewer 판정 전 상태는 derived / pending independent review이다. 이 파일은 PROMOTE를 수행하거나 이전 I2/I3 또는 현재 source 상태를 수정하지 않는다.


---

# 부록: ROOT_ANALYTIC_RESULTS_KO.md

# Type-independent Loop 1 — 원문 후보의 수정 계승과 약형 관측 계약

근거 상태: 아래 증명은 이번 루프의 직접 유도(derived)다. 새 수치 검산,
CAS/Lean 실행, 관측 적합, repository 과학 gate 통과를 뜻하지 않는다.
DB의 원 상태는 변경하지 않고 successor statement를 별도 등록한다.

## A. 현재 formalism과 이름 충돌의 해소

첨부 report(1).pdf §23(pp.21–23)는 현재 기본 객체를 다음처럼 지정한다.
x는 공동 상태 X 위의 함수족 phi_j(X), Q는 premise-anchor gauge/margin,
F는 방향별 support-utilization, Pi는 지정 law 아래의 functional exceedance,
G_F는 depth/mask/feature transport와 coherence의 경로다.
이 정의를 현재 기본 표기로 계승한다. 이전 R2의 tensor outer product는
mathbb Q_R2=T⊗T, 그 norm은 F_rad=||T||²라고 별도 표기한다.
둘은 목적에 맞는 추가 함수이며 현재 Q,F의 정의를 덮어쓰지 않는다.

운동학 상태는 같은 기준계·사건에서
K=(delta theta/H_*, sigma/H_*, omega/H_*, A/(c H_*), beta_RM, beta_MO)
로 둔다. H_*>0는 독립적으로 선언한 rate scale이다. beta 두 개를 별개로
추정하면 18성분이며, 하나만 쓰면 15성분이다. theta/theta=1 같은 자기 정규화는
팽창 제약이 아니다. beta_RM은 matter/reference congruence의 tilt,
beta_MO는 observer endpoint boost다. 각 vector/tensor의 polar/axial 유형,
frame, epoch, units, domain 및 함수값이 함께 보존되어야 한다.

## B. DB 후보 C1 — compact/nonconvex 선형상 정리의 수정

원문 anchor: role-a2b4ff30d2573081, T-JOINT-SUPPORT.
원문은 compact F에 대해 convex이면 interval, nonconvex이면 finite union을 제안한다.
뒤의 결론은 일반 compact 집합에서는 거짓이다.

**정리 TF-C1.** 비어 있지 않은 compact F⊂R^d와 선형함수 l에 대해 l(F)는
compact하고 extrema를 달성한다. F가 connected이면 l(F)는 닫힌 구간이다.
F가 semialgebraic이면 l(F)는 유한 개 닫힌 구간과 점들의 합집합이다.
일반 compact/nonconvex F에는 유한 합집합 결론이 없다.

**증명.** 연속상은 compact이고 connectedness를 보존한다. R의 connected
부분집합은 interval이다. semialgebraic인 경우 선형 projection의 상도
semialgebraic이며 R의 semialgebraic 집합은 유한 개 interval과 점의 합집합이다.
이는 표준 real algebraic geometry 정리의 적용이다. 반례는 R의 middle-third
Cantor set C와 l=identity다. C는 compact이며 무한히 많은 점을 갖고 interval을
포함하지 않으므로 유한 개 interval과 점의 합집합일 수 없다.

계승: compact extrema/connectedness 부분은 유지하고, finite-union 부분에
semialgebraic 가정을 추가한다. 이 가정이 없는 source-image는 그대로 compact set
또는 support outer representation으로 보존한다. convex hull의 support는 원 집합과
같아도 내부의 hole·비볼록 morphology는 다를 수 있다.

## C. DB 후보 C2 — Fisher 꼬리 합과 approximate sufficiency 분리

원문 anchor: role-ac63913e9a4082d8, NT2-A2; 관련 role-61db4486cf9c9245, NT2-A1.

**정리 TF-C2.** independent full-sky Gaussian modes라는 고정 실험에서
한 scalar parameter q에 대한 log-variance response를 r_l이라 할 때,
I_tail=(1/2)Σ_(l>L)(2l+1)r_l²의 유한성은 이 weighted-square sum의 수렴과 동치다.
r_l→0만으로는 충분하지 않다. r_l=l^(-p)이면 p>1일 때에만 수렴한다.

**증명.** 항은 l^(1−2p)에 비례하며 p-series 기준을 적용한다.
예를 들어 r_l=1/l은 0으로 감소하지만 I_tail은 harmonic divergence다.
원문 후보의 “any decaying r_l” 충분조건은 따라서 거짓이다.

응답이 고차에서 정확히 0이고 평균과 covariance의 그 부분 및 cross-block도
q와 무관하게 factorize하면 low-l가 해당 likelihood에서 정확히 sufficient다. 이는 충분조건으로 제시한다.
작은 Fisher tail은 국소 민감도 진술이며 전역 approximate sufficiency를 홀로 증명하지 않는다.
정확한 joint law, parameter domain 및 KL/total-variation 등 approximation 기준을
더해야 한다. mask를 사용한 f_sky 곱은 일반적인 exact covariance law가 아니다.

**수정 계승의 계산형.** 실제 finite Gaussian data law d~N(mu(q),C(q)), C≻0라면
I_ab=mu_,a^T C^{-1}mu_,b+(1/2)tr(C^{-1}C_,a C^{-1}C_,b).
따라서 mean-response가 같아도 covariance가 다르면 law-identifiability가 남을 수 있다.
위 식은 다음의 score를 곱해 평균하면 얻는다:
s_a=mu_,a^T C^{-1}r+(1/2)[r^T C^{-1}C_,a C^{-1}r−tr(C^{-1}C_,a)].
중심 Gaussian의 홀수 moment는 0이고
Cov(r^TAr,r^TBr)=2tr(ACBC)이므로 두 항의 합이 된다.
이는 새 천체물리 transfer를 제공하는 식이 아니라 채택한 Gaussian 법칙의 정확한 항등식이다.
r_2=1이나 r_(l>2)>0는 MES 부등식만으로 정해지지 않으며 별도 response가 필요하다.

## D. DB 후보 C3 — Frobenius를 보편 shear/vorticity 비율로 계승할 수 없음

원문 anchor: role-2a9e444fd4a3f8ab, NT-B2.
원문의 W²=R_WS² Sigma²를 모든 congruence에 대한 Frobenius 관계로 쓰지 않는다.
Frobenius의 내용은 timelike congruence의 hypersurface orthogonality와 vorticity
소멸의 동치이며, shear와 vorticity의 보편적인 양의 비례 상수가 아니다.

**직접 국소 반례.** Minkowski 좌표 X0=ct, x_i에서 단위 timelike field
u=sqrt(1+|v|²)e0+v_i e_i, v_i=B_ij x_j를 잡는다.
원점에서 ∇_i u_j=B_ji이고 ∇_0u_i=0이다. B를 nonzero antisymmetric로
택하면 theta=0, sigma=0, omega≠0다. symmetric trace-free B를 택하면
theta=0, sigma≠0, omega=0다. 실제 각 사건의 rate에는 c를 곱한다.
원점에서의 결과가 보편적인 고정 비례식을 반박하기에 충분하다.

계승: 특정 물질·공간대칭·프레임이 추가로 강제하는 비율은 그 가지에서만 유지한다.
일반 joint budget은 별도 bounds의 product 또는 실제 coupled constraint body로 구성한다.
signed scalar x에서 상쇄가 가능하다는 동기는 유지하되 이를 양의 norm으로 쓰지 않는다.

## E. DB 후보 C4 — 정적인 source와 depth-independent 관측은 다름

원문 anchor: role-ecd59621e1bd58ca, NT-B3.
constant shear만으로 G_F(z)=1이 된다는 함의는 일반적인 line-of-sight 적분에서 따르지 않는다.
명시적 반례는 q(L)=∫_0^L s dchi=sL, s≠0라는 상수 source의 선형 적분이다.
F_rad(L)=|q(L)|²이면 F_rad(L)/F_rad(L0)=(L/L0)²다.
이는 transfer의 적분구간·boundary·visibility가 필요함을 보이는 해석적 반례이며,
특정 Einstein–Boltzmann 우주해를 새로 구성한 결과는 아니다.

계승: structured G_F는 실제 frame/feature transport K_ab와 같은 source 이력 아래
delta phi=phi_a−K_ab phi_b, 그 joint covariance 및 admissible path를 우선 사용한다.
constant source를 일정한 endpoint observable로 바꾸려면 별도 kernel 정규화가 필요하다.

## F. DB 후보 C5 — 부호 없는 octupole amplitude로 자동 subtraction bound를 만들 수 없음

원문 anchor: role-df53f7b2871550ba, NT-B1.
제안된 f=1−min(a3/a2,f_max)는 exact hierarchy에서 유도된 식이 아니다.
선형 residual relation L sigma=r2−D3에서 |D3|≤b만 알면 최악값은
||L sigma||≤||r2||+b다. 같은 amplitude의 D3가 r2에 평행/반평행인 두 경우가
서로 다른 보정 부호를 주므로 b를 단순 차감할 수 없다.
작은 a3 자체가 spacetime derivative D3의 작은 bound를 보장하지도 않는다.
여기에 derivative budget 또는 부호·정렬·공동 집합 제약을 붙여야 한다.

계승 판정 제안: 원 candidate formula는 REOPEN_THEOREM이며,
R2의 exact weak law와 joint residual inverse-image로 다시 정의한다.
octupole 정보를 추가하면 feasible set이 줄 수 있다는 일반 사실은 유지되지만,
임의의 scalar 감소 인자로 바꿀 권리는 생기지 않는다.

## G. 직접 강화 TF-W1 — finite-window weak response와 endpoint 오차의 계약

기존 R2의 A_B k=r와 Raychaudhuri 약형을 계승한다. 이 정리는 새로운
Boltzmann closure를 가정하지 않고 실제로 채택한 moment balance를 입력으로 받는다.

시간 구간 [a,b], absolute-continuous moment vector m(t), 적분 가능한 source s(t),
rate vector k(t)와 matrix A(t)에 대해 정확히
m'(t)+A(t)k(t)=s(t)
가 성립한다고 하자. A에는 선택한 brightness moments, 관측자 frame 연결과
해당 순간의 beta를 명시적으로 포함한다. theta, sigma, omega, A/c는 선형 rate
slot으로 들어갈 수 있으나 미지 finite beta까지 선형이라는 뜻은 아니다.
w는 C1 시험함수다. 모든 벡터 성분의 단위·frame은 동일한 transport로 비교한다.

**정리.** K_w=∫_a^b w(t)A(t)k(t)dt는
K_w=∫_a^b [w(t)s(t)+w'(t)m(t)]dt−[w(t)m(t)]_a^b
로 정확하게 주어진다. endpoint t0에 대해 ||k(t)−k(t0)||≤L|t−t0|이면
Abar_w=∫w A에 대해
||Abar_w k(t0)−K_w||≤L∫|w(t)| ||A(t)|| |t−t0|dt.

**증명.** balance에 w를 곱해 적분하고 m' 항에 부분적분한다.
두 번째 식은 Abar_w k(t0)−K_w=∫wA[k(t0)−k(t)]에 삼각부등식과
induced operator norm bound를 적용하면 된다. w의 부호를 가정하지 않으며
|w|가 필수다. w(a)=w(b)=0이면 endpoint moment 항이 사라진다.

관측/source 오차를 δm,δs로 표시하면 같은 frame에서 추가 잔차는
∫(|w| ||δs||+|w'| ||δm||)dt + |w(b)| ||δm(b)||+|w(a)| ||δm(a)||
로 bounded하다. A 자체도 불확실하면 같은 latent state에서 A와 k를 함께
다뤄야 하며 ||δA||만 알고 ||k||가 자유인 경우 유한 추가오차를 만들 수 없다.

여러 w를 stack한 연산자를 M이라 하자. 자유 nuisance N이 있으면 사영 P_N^perp 후
kernel을 검사한다. 일반 unconstrained affine domain에서 endpoint target P k0가
잔차 오차로 유계해지는 조건은 ker(P_N^perp M)⊆ker(P)다.
이는 이전 quotient 정리의 적용이며 새로운 rank 식별 정보의 생성이 아니다.
물리 domain을 제약한 경우에는 feasible differences를 대상으로 다시 검사한다.

**차원과 극한.** m은 moment, s는 moment/time, k는 rate라면 A는 moment이고
w 무차원에서 K_w와 Abar_w k0는 moment 단위다. L은 rate/time이다.
L=0이면 endpoint 변환 오차는 0이지만 M의 kernel은 여전히 남는다.
하나의 static sky만 있으면 위 적분 입력 m(t),s(t)를 얻었다고 할 수 없다.
redshift bins를 t로 바꾸려면 d t/d z, 동일 source/congruence, 광로와 selection
계약이 필요하다. 관측 창 안의 자료를 사용할 수 있을 때 미분값 직접 추정 대신
약형 가중 적분을 쓰는 대안이며 numerical evolution solver는 요구하지 않는다.

## H. 현재 단계의 결론

첫 loop는 모든 과거 후보를 증명 완료로 승격하는 작업이 아니다. 20개 원문 후보를
직접 읽어 위 조건 누락과 수정 계승을 기록하고, 나머지 항목은 원문·버전·미확인
상태를 유지한 채 질의 가능한 형식으로 옮겼다. 기존 T1/T2 rank 결과는
fixed linear mean plus parameter-independent covariance의 범위에서 재사용한다.
가정 없는 tensor kinematic inference나 C_l-only morphology 복원은 주장하지 않는다.


---

# 부록: INHERITANCE_MAP_KO.md

# 원문 후보 20개 — 수정 계승표

| 출처 anchor | 처리 | 후속 명제 | 남은 조건/한계 |
|---|---|---|---|
| role-61db4486cf9c9245 | RESTRICT_AND_REOPEN_RESPONSE | TF-C2 | r₂=1, higher-mode response and strict improvement do not follow from MES. The old MC report is historical, not rerun. |
| role-ac63913e9a4082d8 | REPLACE_FALSE_SUFFICIENT_CONDITION | TF-C2 | Decay alone does not imply Fisher-tail convergence or approximate sufficiency. |
| role-2704b6f24d18dbee | HOLD_MISSING_PHYSICAL_BRIDGE | TF-W1, TF-S3 | KL cap alone is not a kinematic ceiling. No new KL-to-physics theorem is asserted. |
| role-adc6a1bcf36de1d4 | HOLD_SOURCE_DEFINITIONS | TF-P2, TF-P3 | Raychaudhuri is inherited; the particular Delta-q inversion formula is not rederived or generalized here. |
| role-7cce0a1e86175dce | INHERIT_CONDITIONAL_OPERATOR_RESULT | TF-W1, TF-S3 | A positive singular value cannot substitute for missing radiation derivatives. |
| role-229717dd6ca7353f | RESTRICT_DOMAIN_AND_LAW | TF-S4, TF-C2 | Physical boundary constraints can identify points despite ambient rank loss; covariance may also carry information. |
| role-a66c842a23c92854 | INHERIT_EXACT_LAW_NO_GO | TF-S4 | Mean-column collinearity alone is insufficient if the noise law or covariance changes. |
| role-c512d8fb1c4e1efb | REOPEN_UNIQUENESS_AND_SCOPE | TF-P1, TF-S4 | The claim that matter dipole is the unique low-order handle is not inherited; actual aberration and source responses matter. |
| role-df53f7b2871550ba | REOPEN_THEOREM | TF-C5, TF-W1 | The proposed subtraction factor is not an exact consequence of the moment hierarchy. |
| role-2a9e444fd4a3f8ab | REJECT_UNIVERSAL_RATIO | TF-C3, TF-P1, TF-P2 | Frobenius gives hypersurface orthogonality iff zero vorticity; it does not give a universal nonzero ratio to shear. |
| role-ecd59621e1bd58ca | REOPEN_TRANSFER_AND_DEPTH | TF-C4, TF-W1, TF-S2 | A constant source need not yield a constant integrated observable or unit growth. |
| role-fb115ecca130a85b | INHERIT_STACKED_RESPONSE_CONDITION | TF-S4, TF-W1 | Repeated identical columns remain degenerate even with additional depth labels. |
| role-2547259daf5ad54c | STRENGTHEN_JOINT_STATE_MAPPING | TF-S1, TF-S2 | New successors make support/gauge duality and joint coverage explicit. |
| role-3967c97bf66cb4b1 | INHERIT_PREMISE_BRANCHING | TF-P2, TF-P3, TF-W1 | Nongeodesic stress-gap bound is a separate conditional physical bound, not the original MES ceiling. |
| role-f8486acfcdb96895 | STRENGTHEN_FIBER_MINIMUM | TF-S3, TF-S4 | The quotient gauge is a minimum over lifts, not the actual hidden physical magnitude. |
| role-b939dc581755e9fc | STRENGTHEN_JOINT_STATE_MAPPING | TF-S1, TF-S2 | A common feasible set alone does not determine Pi or frequentist coverage. |
| role-a2b4ff30d2573081 | REPLACE_FINITE_UNION_CLAIM | TF-C1, TF-S1 | Generic compact nonconvex images can be Cantor sets. Support cannot recover holes. |
| role-a729e95805590b41 | INHERIT_CONDITIONAL_CEILING_SURFACE | TF-S1, TF-S2, TF-S4 | A free intrinsic dipole creates an envelope; fixing it is an extra assumption. |
| role-5c1e239533655199 | RESTRICT_TO_TYPED_FRAME_BRIDGE | TF-P1, TF-S4 | A point boost is not a congruence derivative; one normalization cannot supply missing response information. |
| role-aba6d0a88a843cba | RESTRICT_EXACT_RANK_SCOPE | TF-S4, TF-C2 | Rank theorem remains valid in its stated experiment, not as a universal nonlinear identification criterion. |


---

# 부록: LOCAL_CODEX_NEXT_LOOP_KO.md

# Local Codex 전달 프롬프트 — 유형 독립적 연구 Loop 2

아래부터 그대로 전달한다. 이 패키지는 여기서 수행한 해석적 연구 Loop 1의 결과다.
실제 xAct/Lean/Sage 실행 결과는 포함하지 않는다.

---

저장소 /home/cosmosapjw/Dropbox/bianchi/htt_base에서 기존 작업을 보존하며 연구를 계속해줘.
우선 현재 origin/main과 작업 디렉터리를 읽고, 이 패키지 기준 commit
96c0b2cb59765c36860da2049021c25a240d0c9b와 차이를 기록해줘. branch나 사용자 변경을
reset하지 마. 특정 Bianchi type을 기본값으로 선택하지 말고 아래 계약으로 진행해줘.

1. TYPEFREE_RESEARCH_LOOP1_KO.md, RESEARCH_ARCHITECTURE_KO.md,
   INDEPENDENT_DECISION.json, ADJUDICATED_AMENDMENTS_KO.md를 먼저 읽어줘.
   INHERITANCE_MAP.json의 원문→후속 명제 연결을 확인해줘.
2. THEORY_INHERITANCE.sqlite.gz를 새 파일명으로 풀고 integrity_check 및
   DELIVERABLE_MANIFEST.json의 hash를 확인해줘. 원본 historical tables/status를
   덮어쓰지 마. QUERY_EXAMPLES.sql로 후보·가정·출처·새 판정을 조회해줘.
3. gpt6 Astra harness는 사용자 지정 모델/effort에 맞춰 적용하되, 실제 이용 가능한
   모델과 도구 버전을 기록해줘. 기존 work-unit의 비용 예산을 임의로 초기화하지 마.
   새 코드 DB 전체 다운로드나 ODE/PDE/Boltzmann 진화 solver를 도입하지 마.

첫 우선순위는 TF-P2/P3를 Wolfram+xAct로 exact 재현하는 것이다.

- signature(−+++), x⁰=ct, U²=−c², κ=8πG/c⁴, 곡률 부호를 선언해줘.
- φ=−b(x⁰)²−b|x|²/2+λ(x⁰)²x¹/2, g=e^(2φ)η, b>0를 일반 b,λ,c로 계산해줘.
- p=0에서 metric 2-jet의 λ 독립성, G₀₀=6b, Gᵢⱼ=G₀ᵢ=0,
  ∇₀T¹₀=−2λ/κ와 A¹=c²λ/(3b), θ=σ=ω=0을 확인해줘.
- eigenvector 미분식 ∇_μU=−cL⁻¹D_μ와
  θ²/3+||σ||²+2|ω|²+|A|²/c²≤c²||D||²/δ²를 별도로 확인해줘.
- δ=0의 cosmological-constant stress는 선택 유일성이 깨지는 음성 대조다.
- stress는 총 Einstein source이다. 이를 근방 전체의 dust/perfect-fluid 해라고
  부르지 마. DEC는 각 유한 λ의 충분히 작은 근방에서만 유지한다.
- 축척 c, derivative-first vorticity 부호와 4-divergence/spatial divergence를 교차 확인해줘.

두 번째 우선순위는 Lean+mathlib의 실제 formal proof다.

- TF-S2의 공동 피복 사건 포함, TF-S4의 동일법칙 신뢰집합 직경 하한부터 시작해줘.
- TF-P2는 유한 차원 self-adjoint L, 양의 gap, column norm estimate와 trace/STF/
  antisymmetric 직교 분해를 분리해 증명해줘. 미분기하 전제와 finite matrix 정리를
  혼동하지 말고 어떤 연결 부분을 수기로 남겼는지 기록해줘.
- TF-S1/S3의 support-gauge/quotient 결과는 필요한 compactness, 0-interior,
  measurability와 dim=0 가지를 실제 statement에 넣어줘.
- sorry/admit/새 axiom으로 목표를 가정한 뒤 증명 완료로 보고하지 마.
  기존 native evaluation 기반 기록과 새 kernel proof를 구분하고 axiom 목록을 출력해줘.
- 설치된 Lean/mathlib 버전과 기존 repo 환경부터 확인하고 무단 업그레이드하지 마.

세 번째 우선순위는 SageMath+Singular의 유형 미지정 대수 연구다.

- Cᵢⱼᵏ=−Cⱼᵢᵏ 및 Jacobi를 symbolic 입력으로 유지해줘.
- gᵢⱼ의 양의정부호, lapse>0, β²<1 및 필요한 metric/velocity jets를 명시해줘.
  Lie algebra alone으로 크기 상계를 만들지 마.
- TF-C1의 semialgebraic source-image와 coupled feasible set을 분석해줘.
  denominator를 없애는 과정의 nonzero 조건과 singular strata를 보존해줘.
- Gröbner ideal은 부등식/양의정부호를 증명하지 않는다. real feasibility와
  ideal-membership을 별개로 보고해줘. 표본에서 rank가 크다는 사실을 모든
  parameters의 rank 정리로 승격하지 마.

그 다음의 실제 이론 과제는 TF-W1에 들어갈 입력을 구체화하는 것이다.

- 기존 R2 exact brightness weak law에서 한 개의 명시한 moment/source 창을 골라
  A(t),m(t),s(t),w(t), endpoint 오차 예산을 작성해줘. 가짜 derivative 자료를
  생성하지 말고 관측·가정·unavailable을 분리해줘.
- 한 장의 CMB 하늘을 redshift time series로 취급하지 마. 가능한 보조 관측의
  응답을 채택할 경우 source/selection/optical-depth/nuisance까지 명시해줘.
- 실제 자료법칙 아래 quotient/body와 모든 admissible source를 유지해 식별 가능한
  tensor 조합부터 결정해줘. local boost/global tilt 응답 열이 같으면 퇴화를 보존해줘.
- 다른 차수의 모든 운동학량을 x/Q/F/Π/G_F 함수족에 넣되, 유한 anchor가 없는
  성분은 unavailable/uncontrolled로 남겨줘. 조건부 물리 예산 비율과 p-value를
  따로 보고해줘.

각 엔진은 같은 claim contract와 입력 hash를 사용하고 raw transcript, 버전, exact
expression, domain/assumption differences, negative controls를 남겨줘. 서로의 수치
결과를 베껴 독립 검산이라고 부르지 마. 새 CAS/formal 근거와 독립 과학 판정을
별도 추가해줘. 이번 Loop 1의 수기 판정은 기존 I2 DEFENDED_CONDITIONAL이나
I3 HOLD_INPUT_INCOMPLETE를 자동 변경하지 않는다.

최종 반환물은 (a) 새 명제와 증명, (b) 반례/특이 가지, (c) 3개 local engine 결과,
(d) DB append migration과 source lineage, (e) 독립 판정 및 남은 가정으로 해줘.
계산 하나가 막혀도 이미 승인된 다른 독립 과제는 진행해줘. 원본 DB/Release ZIP,
repo history를 삭제하지 말고, 공개 push는 별도 승인된 작업 범위에서만 수행해줘.


---

# 부록: README_KO.md

# 유형 독립적 이론 연구 Loop 1

우선 TYPEFREE_RESEARCH_LOOP1_KO.md를 읽는다. 개별 증명은 PHYSICS_RESULTS_KO.md,
STATISTICS_RESULTS_KO.md, ROOT_ANALYTIC_RESULTS_KO.md에 있다. 후보 원고의 작은
범위 보정은 ADJUDICATED_AMENDMENTS_KO.md가 우선하며, 독립 판정 원본은
INDEPENDENT_DECISION.json이다. 새 결과는 수기 해석 증명과 독립 검토 수준이다.

## 실제 받은 데이터와 읽은 범위

- 기준 main: 96c0b2cb59765c36860da2049021c25a240d0c9b.
- tree: f11d29925a6ec29960ae2ec17b042b867f4f19b5.
- theorem/proof catalog를 게시한 branch:
  implementation/project-catalog-20260912. 이 export들은 현재 main에도 있다.
- docs/project_catalog/proofs 아래의 공개된 정리·증명·후보 데이터 파일 46개를
  실제 다운로드했다. 합계 263,371,196 bytes이며 Git blob 및 크기를 대조했다.
- original confirmed 345개, unconfirmed 39,937개, 합계 40,282개를 보존했다.
  이는 소스 버전·문맥별 레코드 수이며 서로 다른 수학 정리의 개수가 아니다.
- 연구 제안 section 172개, 보조 명제 section 94개도 보존했다.
- occurrence 967,813개를 스트리밍 조회하고 명제 관련 104,780개를 SQLite에 보존했다.
  비명제 863,033개 occurrence는 import하지 않았다.
- 후보 20개 원문 section을 직접 읽고 수정 계승표를 작성했다. 나머지 전부를
  이번에 증명 검토했다고 주장하지 않는다. 보조 query로 비전단/방법론 declaration을
  찾았고 지정한 4개 compiled-source excerpt의 범위를 추가로 대조했다.

원본 공개 형식은 JSON/JSONL.gz 등이며 이를 source-preserving SQLite로 재구성했다.
과거 통합 catalog SQLite 원본 자체나 코드 데이터베이스 전체를 다운로드한 것은 아니다.
증명 데이터 안의 Lean proof excerpt·코드 경로는 증명 출처로 보존했다.
코드 DB, 전체 repo archive, 코드 첨부 archive를 이번 작업에서 새로 받거나 풀지 않았다.

원 catalog의 baseline은 efc5f30666b96782f946375551f0068bb3a30f74다. 현재 main에서
다운로드했다고 catalog 내용의 기준 시점까지 최신으로 바뀌는 것은 아니다. 최신 I1/I2
702개 통합 파일은 별도 checkpoint_sources 목록으로 연결했다. 이 702개는 이번에
전부 본문을 다시 읽거나 과학 재검증했다는 뜻이 아니다. 이번 연구에 사용한 R2 결과,
독립 판정, 첨부 formalism은 evidence 폴더에 분리했다. 접근하지 못한 이전 ChatGPT
대화의 전체 원문까지 복원했다고 주장하지 않는다.

## 형식화의 의미

THEORY_INHERITANCE.sqlite는 원문, 가정, convention, 과거 상태, 이번 근거,
후속 명제, 남은 proof obligation, source linkage를 분리한다. 이 구조화 자체는
Lean kernel proof가 아니다. 원본 상태를 바꾸는 대신 loop_claims와 연결 표를 추가했다.
13개 새/수정 분석 항목의 정확한 채택 범위는 독립 판정과 보정문을 따른다.

## 파일 이용

- THEORY_INHERITANCE.sqlite.gz: 압축을 풀면 질의 가능한 SQLite.
- QUERY_EXAMPLES.sql: 검색·가정·후속 명제·출처 조회 예시.
- INHERITANCE_MAP.json: 우선 검토한 후보 20개의 원문→후속 명제.
- RESEARCH_ARCHITECTURE_KO.md: 일반 운동학/광학/Einstein/Lie/MES/통계의 가정 구조.
- LOCAL_CODEX_NEXT_LOOP_KO.md: xAct, Lean, Sage/Singular 후속 실행 프롬프트.
- proof_database_original/: 다운로드한 공개 정리·증명 DB export의 원 바이트.
- evidence/: 실제 사용한 기존 연구 결과, 첨부 보고서, 입력·검토 기록.
- DELIVERABLE_MANIFEST.json: 파일 크기와 SHA-256. 원본 46개는 별도의
  PROOF_DB_DOWNLOAD_RECEIPT.json에서 Git blob까지 확인할 수 있다.

SQL 압축 해제 예시(새 폴더에서 실행):

```bash
gzip -dk THEORY_INHERITANCE.sqlite.gz
sqlite3 THEORY_INHERITANCE.sqlite 'PRAGMA integrity_check;'
sqlite3 THEORY_INHERITANCE.sqlite < QUERY_EXAMPLES.sql
```

코드 DB 없이 다음 연구를 재개할 수 있다. 과학 엔진 실행은 local에서 수행하며,
이번 패키지로 repo push/merge 또는 기존 I2/I3 상태 변경을 수행하지 않았다.

재구성이 필요하면 새 별도 폴더에서 proof_database_original 및 evidence와 함께
`build_theory_database.py`, `prepare_inheritance.py`, `finalize_theory_database.py`
순서로 실행한다. 이 명령은 이미 있는 SQLite를 덮어쓰지 않는다. Python 표준
library의 sqlite3/FTS5를 사용한다. 다운로드를 다시 해야 하면 포함된 proof 전용
file index로 `acquire_proof_database.py`를 실행할 수 있다. 코드 목록은 필요 없다.
