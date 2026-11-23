# Legacy 전수 코드 통합 v2와 DP–MZ 보조 연구 R1–R10

**기준일:** 2026-11-23 (사용자 기준). **연구 모드:** 발산 탐색. **상태:** 첨부 source 정독·중복 통합, 조건부 유도, 명시된 유한 검산, 현행 코드 연결 계약 완료. 원격 저장소 source 수정·stage·commit·push와 60개 science node의 완료 승격은 수행하지 않았다.

이번 확장은 새 첨부의 실제 미시물리·표현론·관측자 계산을 기존 세 연구 단계에 연결한다. 가장 직접적인 결과는 **숨은 상태의 체류시간과 물리적 clock를 구분하는 Schur memory 보정**, **화학 proper clock와 photon escape/opacity를 분리하는 native adapter**, **VIII 유한창 경계 결함의 명시식**, **공통 양의 사건법칙에서 rate·mark·관측창 응답을 함께 계산하는 구성**이다. 실제 계산과 source 분석으로 좁혀진 다음 구현 단위를 제시한다.

## R1. 현재 위치와 완료 범위

앞선 세 결과는 (i) DP–MZ와 richer carrier 및 five-view의 결합, (ii) 물리시간 이외의 통계적·물리적 매개변수 응답, (iii) 첫 legacy 카탈로그 및 R1–R10 연구다. 이를 재시작하지 않고 동일 source의 근거를 재사용했다. 이번의 새 질문은 **새 source가 실제로 어떤 generator·measure·metric·clock·observable을 제공하며, 그 구조를 현재 연구 축의 해결 가능한 부분에 어떻게 붙일 수 있는가**다.

최신 GitHub `cosmosapjw-quantum/htt_base`의 main은 `f1007dd3e41c07eccd64024dd6b44fb5a40a3612`, 연구 branch `research/r69-observable-physics-bridges-20261118`은 `f8931fbef075d55c2c2a3caee8b8f5db5174b16b`다. GitHub compare 및 별도 read-only `git ls-remote`가 이전 기준과 동일함을 확인했다. 기존 R100 과학 commit `11f906a06f340ab96f9c35899600d205ef02a46b`, R78의 60 nodes/129 edges, 이전 R100 실행 근거를 재사용한다. 현재 repo 전체를 새로 전수 정독하거나 R100을 재실행했다고 주장하지 않는다. [G1]

| 항목 | 범위 |
|---|---:|
| 통합한 top-level 첨부 ZIP | 23개: 기존18 + 신규5 |
| 중첩 ZIP/TAR를 포함한 원본 위치 | 5,038 |
| SHA-256 기준 고유 바이트 파일 | 4,073 |
| 동일 바이트 중복 occurrence 통합 | 965 |
| 고유 코드 본문 | 1,354 |
| 이번 신규 코드 본문 | 362 |
| 동일 SHA로 재사용한 이전 정독 코드 | 992 |
| 본문별 source review 누락 | 0 |
| supporting artifact 형식 검사 | 2,719개, 코드 정독과 별도 |
| 추가 의미 검토가 있는 비코드 근거 | 전문 문서·계약135개, 전행 수치표32개, 링크 메타데이터5개 |

이번 신규 본문은 356개 전문, 6개 전문 기준본+완전 diff 방식이다. 차분 검토는 기준본과 바뀐 모든 hunk를 읽은 기록이며, 단순 filename 비교나 AST만의 확인이 아니다. 전체 방식·SHA·위치는 `COVERAGE.json`, `reviews/*.jsonl`에 있다. 원본 파일의 모든 텍스트·증명을 정독했다는 뜻으로 supporting format parse를 확대하지 않는다. 선택된 과학 원고·계약은 별도 전문 장부에 기록했다.

`bass.zip`은 16개 dirty-worktree snapshot이다. 10개 `tar.zst`에 실제 payload가 있고 6개는 dirty file0개라 committed baseline이 포함되지 않는다. 110개 symbolic-link member는 5개 외부 table target의 경로만 제공한다. 이 경로를 table 내용으로 세지 않았다. 파일명상 binary로 잠정 분류됐던27개 `.dat`는 실제 UTF-8 수치표임을 전행 파싱으로 확인해 분류를 교정했다.

## R2. 근거와 재사용

### 2.1 새 첨부의 실제 역할

| 묶음 | 새 고유 코드 분담 | 읽어서 확인한 과학·구현 자산 |
|---|---:|---|
| Lowell C179 PATCH59R | 214 | full-m hierarchy packing, native-facing API/schema, Lie/geometry fixture, Rust/Python contract·build 경로. 실제 kernel과 zero/identity 골격을 구별 |
| BASS ALL BIANCHI LOOP10 | 110 | 일반 Lie-frame 제약 다항식, positive paired event·Bose 수정, Gram/moving basis, 광선·screen·Jacobi tangent, delayed/observational 계산. 문서 generator도 별도 분류 |
| bass dirty payload + VIII kit | 27 | HYRec C real/virtual Schur·radiation history, proper-density adapter, SU(1,1) ladder/Casimir, original mode history 출력 |
| Scholarly Dossiers | 11 |6개 finite calculation, observer Jet/model, data validator 및 TeX builder |

위 분담은 **전역에서 새로 발견한 고유 본문 수**다. archive별 중첩 파일 수와 같지 않다. 각 파일의 역할, 입출력, 의존성, 핵심 동작, 한계, 재사용 함수, DP–MZ 연결, 모든 원경로를 HTML/JSON/TSV catalogue에 보존했다.

이전 라운드의 코드 외 잔여 실행 계약도 보완했다. 18개 build/config/dependency/mode-only patch를 전문으로 읽었다. 새5개 `.diff`는 모두 읽었으며, `PROPER_HYDROGEN_REPLACEMENT_PATCH.diff`는 replacement 수를 적은72바이트 기록일 뿐 실제 source hunk가 없다는 점을 구별했다.

### 2.2 문헌이 제공하는 토대와 적용 범위

Ali-Haïmoud–Hirata의 effective multilevel atom 방법은 excited-state network를 interface state용 effective rates로 분리하는 원전이다. HYREC-2 원문의 §II.2–III.1은 quasi-steady atomic equations, recombination history에 의존하는 radiative rates, `R_Lyα∝H/(n_H x_1s)`를 명시한다. 따라서 첨부의 static Schur와 photon history를 이해하는 외부 근거가 되며, 임의 tilted/Bianchi radiation field에 동일 correction을 적용할 정리가 되지는 않는다. [L1,L2]

te Vrugt–Wittkowski의 시간의존 MZ 연구는 nonautonomous generator와 명시적 시간의존 observable을 다룬다. 여기서는 그 결과의 모든 functional-analytic 범위를 이전하지 않고, 직접 유도 가능한 유한 block propagator와 full-frame connection을 사용한다. [L3] SciSpace·Exa·Parallel의 발견 결과는 `research/LITERATURE_SEARCH_RECEIPTS.json`에 보존했고, 핵심 주장은 primary publisher/arXiv/official source로 확인했다. HYREC-2는2020 논문이다. HTML 재렌더링의2026 날짜를 신규 논문 발표일로 쓰지 않는다.

## R3. 정의와 물리적 계약

metric은 `(-,+,+,+)`, 물리 상수 `c,ħ,k_B`를 유지한다. 정상 관측자 시간은 `t_n`[s], proper-length 시간은 `s_c=c t_n`[m], baryon proper time은 `τ_b`[s], `N=ln a`는 무차원이다. `H_n=dN/dt_n`[s^-1]와 geometry 원고의 `H_geom=dN/ds_c=H_n/c`를 구별한다. 속도는 `β=v/c`, Lorentz factor는 `Γ_b`, Thomson rate는 `ν_T`로 적어 Γ의 충돌을 피한다.

| 연구 view | 유지한 의미 | 새 source의 관련 변수와 구별 |
|---|---|---|
| x | signed tensor/multipole/field carrier 또는 선언된 contraction | electron fraction x_e, atomic population, PSTF5와 동일시하지 않음 |
| Q | 명시된 admissible body/anchor에 대한 gauge | transient atomic matrix Q와 기호만 같음 |
| Π | 지정된 strict/inclusive event와 qualified joint law의 확률 | Poisson 가정이나 source counts만으로 qualification 완료 아님 |
| F | 공통 정규화 measure에서의 사건·support occupancy | coefficient trace·mean gauge와 다름 |
| G_F | floor·depth·path가 명시된 transport functional | parameter derivative 자체를 G_F로 이름 바꾸지 않음 |

DP의 count algebra는 실제 positive propensity와 stoichiometry를 필요로 한다. numerical weighted packet을 integer photon law로 해석하려면 volume·weight·sampling semantics를 먼저 준다. 임의 likelihood/covariance/boost parameter는 기본적으로 score/variational response의 변수다. 실제 transition law가 주어진 경우에만 그 변수에 Markov evolution을 부여한다.

이론은 `derived`, 문헌상 토대는 `literature-supported`, 유한 수치는 `numerically checked`, 실제 소프트웨어 수행은 범위가 붙은 `implementation-verified`로 구분한다. source를 읽어 확인한 미완성·결함은 `source-derived`이고, 미확보 입력은 `unresolved/blocked`다.

## R4. 여덟 발산 경로

| 경로 | 실제 구성 | 검산·source 판별 | current 연결 |
|---|---|---|---|
| N1 | Schur의 체류 질량과 line-delay moment | full resolvent, exact mass identity, finite bins, positivity 반례 | atomic response→opacity→carrier |
| N2 | chemistry proper clock·radiation drift·opacity tangent | actual HYRec H 사용처와 mode history 재분석 | R100 `_opacity_per_efold`와 Thomson force |
| N3 | positive matrix measure·detector error | noncommuting Hankel PSD, detector off-diagonal, polynomial envelope | photon flux·polarization·five-view bound |
| N4 | moving Gram·analyzer·physical response | physical trace derivative0과 coefficient trace의 차이 | optical drift/finite detector/source endpoint |
| N5 | vector Jacobi·Frobenius STF·constraint-compatible reduction | scalar cancellation 반례, full-m packing | R100 Bianchi 제약·native adapter |
| N6 | VIII projected Casimir·K-tail memory | 실제 PEQEP boundary correction | SQ-NATIVE/B02 native atlas |
| N7 | 공동 event rate·mark·Bose response | corrected LOOP5 law, score identity | DP reaction/selection 및 same-parent inference |
| N8 | 비단조 redshift·finite-bin response | fold의 sqrt ε law와 branch integral | H_W/window·source-redshift optics |

탐색을 여덟 개의 동등한 production 후보로 간주하지 않는다. N1/N3/N4/N7/N8은 바로 재사용할 작은 수학 연산을 제공한다. N2/N5/N6의 현재 물리 적용은 실제 background, clock, emitter, source law가 필요하다. 다음 단계에서 N2의 native input/clock 복구와 N5의 representation 계약을 먼저 고정하면 다른 경로가 공통 입력을 사용할 수 있다.

## R5. 직접 유도와 구성

### 5.1 N1: Schur 소거는 숨은 체류시간을 남긴다

유한 column probability generator를

\[
L=\begin{pmatrix}A&B\\C&D\end{pmatrix},\qquad
\mathbf1^TL=0
\]

로 나누고 `D`는 transient Hurwitz Metzler, `B,C≥0`라 하자. 동일 clock에서

\[
\dot x=Ax+By+f,\quad \dot y=Cx+Dy+g
\]

이면 정확히

\[
\dot x=Ax+B e^{D(t-t_0)}y_0+f+
\int_{t_0}^t B e^{D(t-u)}[Cx(u)+g(u)]\,du.
\tag{1}
\]

초기 hidden population과 hidden forcing이 모두 남는다. Laplace kernel과 저주파 전개는

\[
\Sigma(z)=B(zI-D)^{-1}C
=-BD^{-1}C-zBD^{-2}C+O(z^2),
\]

\[
zI-A-\Sigma(z)=zM-L_0+O(z^2),\quad
L_0=A-BD^{-1}C,\quad M=I+BD^{-2}C.
\tag{2}
\]

이는 `|z|‖D^{-1}‖<1`에서 Neumann expansion으로 직접 얻는다. nonnormal block에서는 고유값 gap만으로 resolvent remainder를 제어하지 않는다. inverse와 semigroup norm을 실제 domain에서 추정한다.

column conservation은 `1_r^TA=−1_u^TC`, `1_r^TB=−1_u^TD`를 주므로

\[
\mathbf1_r^TL_0=0,\qquad
\mathbf1_r^TM=\mathbf1_r^T-\mathbf1_u^TD^{-1}C=:m^T.
\tag{3}
\]

quasi-static hidden occupation `y_*=-D^{-1}Cx`를 포함한 전체 질량은 `m^Tx`다. `L_0`는 retained set의 trace-process generator가 되지만, 숨은 체류시간을 생략한 clock의 기술이다. 원래 물리적 시간의 낮은 주파수 응답에는 `M`이 나타난다. 초기 forcing은 식(1)에서 별도로 운반해야 하므로 `M xdot=L_0x`만으로 초기층까지 복원했다고 할 수 없다.

3-state 사례 `a=1,b=0.5,c=20,d=30 s^-1`에서

\[
L_0=\begin{pmatrix}-.6&.2\\.6&-.2\end{pmatrix}\,s^{-1},\quad
M=\begin{pmatrix}1.008&.004\\.012&1.006\end{pmatrix},\quad m^T=(1.02,1.01).
\]

전체 정상분포는 `(20,60,1)/81`, retained conditional distribution은 `(1/4,3/4)`다. 이 둘을 같은 물리 질량으로 정규화하면 숨은 점유 `1/81`을 잃는다.

| z [s^-1] | static symbol 오차 | first-memory symbol 오차 |
|---:|---:|---:|
| .20 | 3.21205e−3 | 1.28482e−5 |
| .10 | 1.60923e−3 | 3.21847e−6 |
| .05 | 8.05420e−4 | 8.05420e−7 |

symbol은 `zI-A-Σ(z)`이며 표는2-norm이다. 정적 오차는1차, memory 보정 후는2차로 감소한다. 완전 resolvent의 절대오차는 보존 pole `z=0` 때문에 같은 scaling을 자동 따르지 않으며, 별도 원자료에 기록했다.

**양성 반례.**

\[
A=\begin{pmatrix}-a&q&r\\0&-q&0\\0&0&-r\end{pmatrix},\quad
B=(0,c,d)^T,\quad C=(a,0,0),\quad D=-(c+d)
\]

인 valid4-state chain에서

\[
(M^{-1}L_0)_{32}=-\frac{adq}{(c+d)^2}<0.
\tag{4}
\]

따라서 first-memory ODE를 전체 시간·전체 positive cone에서 Markov jump law로 쓰는 것은 정당하지 않다. 원 positive chain, exact memory, positivity를 유지하는 auxiliary state realization을 대안으로 유지한다. 이 특정 finite approximation의 반례를 MZ 축약 일반의 불가능성으로 확대하지 않는다. 식(3)과(4)는 SymPy와 Wolfram15.0.1로 독립 확인했다. [C1,C3]

### 5.2 N1: 총 방출량과 관측창의 응답을 분리

transient atomic generator `Q_at`, line reward row `ell^T`, positive injection `p`에서

\[
K_e(t)=\ell^Te^{Q_{at}t}p,\qquad
M_{e,n}=n!\ell^T(-Q_{at})^{-n-1}p.
\tag{5}
\]

적분 by parts와 transience로 얻으며, n번째 moment의 차원은 `yield×time^n`이다. `H_at=(-Q_at)^-1`에 대해 `∂H_at=H_at(∂Q_at)H_at`이므로 **generator·line rate·injection 세 곳의 변화**를 모두 미분한다. finite bin `[t0,t1]`의 응답은 `ell^T∫exp(Q_at u)p du`이고, source onset 이전 구간의 mass는0이다.

첨부 two-stage toy `a=2,c=5 s^-1,b=.3`에서 `M0=.3`, `M1=.21s`, `M2=.234s²`, `M3=.3654s³`다. `[.4,1.2]s`의 line yield는 `0.1527341992019155`, birth-time instantaneous approximation은0이다. `∂_c M0=0`이지만 `∂_c M1=−b/c²=−.012s²`다. 총량만 같은 surrogate는 유한창·source derivative를 놓칠 수 있다.

새 공통 구현은 augmented exponential로 finite bin을 적분하여 작은 구간에서 두 큰 inverse/exponential 값을 빼는 cancellation을 줄였다. `a=c` repeated-rate limit도 `b a²t e^{-at}`의 직접 quadrature와 대조했다. real atom의 수치 calibration이 아니라 source-defined toy의 정확 구조다. [C1,C2]

### 5.3 N2: proper density와 chemical clock를 함께 전달

Class A homogeneous conserved hydrogen current, spatially uniform scalar composition을 가정한다. baryon velocity `u_b=Γ_b(n+β)`이면

\[
\frac{dN}{d\tau_b}=\Gamma_b H_n,\qquad
n_{H,rest}\Gamma_b a^3=\mathcal N_H.
\]

rest-time chemical source `R=dx_e/dτ_b`의 식은

\[
\frac{dx_e}{dN}=\frac{R}{\Gamma_bH_n}.
\tag{6}
\]

첨부의 proper-density factor가 `Γ_anchor/Γ_b`를 구현해도 source H가 `H_n`인지 `dN/dτ_b`인지 확인해야 한다. H2248 원 generator가 빠져 있으므로 **clock 해석 미확정**으로 남긴다. 실제 HYRec H는 `dx/dln a` 분모 외에 `R_Lyα∝H/n_H`, photon-bin `Dtau∝n_H/H`에도 사용된다. 모든 H를 `Γ_b H_n`로 치환하는 패치는 허용되는 수학적 결론이 아니다. `density`, `chemical_clock`, `radiation_frequency_drift`, `matter_expansion`을 별도 계약으로 분리한다. [A1,L2]

normal photon 방향 e에서 electron-current contraction은

\[
\gamma_N(e)=\frac{\sigma_T c}{H_n}
 x_e n_{H,rest}\Gamma_b(1-\beta\cdot e)
=\frac{\sigma_T c}{H_n}x_e\mathcal N_H e^{-3N}(1-\beta\cdot e).
\tag{7}
\]

명시적 Γ는 상쇄되지만 `x_e`의 proper-clock 의존성은 남는다. 고정 N에서

\[
\partial_\theta\log\gamma_N
=\partial_\theta\log x_e+\partial_\theta\log\mathcal N_H
-\partial_\theta\log H_n
-\frac{\partial_\theta(\beta\cdot e)}{1-\beta\cdot e}.
\tag{8}
\]

e의 ray tangent와 `H_ref(θ)`를 사용한 normalization도 미분에 포함한다. `κ=∫γ_NdN`, `g_N=γ_Ne^{-κ}`의 응답은 `∂g=e^{-κ}∂γ−g∂κ`이며 움직이는 endpoint에는 Leibniz 항을 더한다. 이 식은 H가0인 곳에서 사용하는 clock chart가 아니다. 그런 구간은 proper-time equation으로 돌아간다.

정상 단원자 gas의 adiabatic 부분도 동일 가정에서 `dT/dN=−2T−(2/3)T dlnΓ_b/dN`이다. 조성 변화는 별도의 heat-capacity 항을 추가한다. Class B spatial divergence나 다른 material congruence에서는 이 단순화를 재유도한다.

저장된6개 native history는 전행 재분석했다. `300≤z≤1700`의 max absolute `Δx_e`는 SWIFT−FULL TypeII `3.199145239e−4`, EMLA−FULL `7.935201379e−3`, FULL TypeII−FLRW `1.006330667e−2`로 첨부 report와 일치한다. 이는 **archived output의 재계산**이며 native solver를 새로 돌리거나 anisotropic physical validity를 입증한 결과가 아니다. [A1]

### 5.4 N3/N4: 양의 spectral measure와 physical Gram을 유지

준비된 source amplitudes `v(x)`와 positive measure가 있을 때 `dM=v v†dμ`, `K_p=∫x^p dM`, `0≤x≤1`로 둔다. 임의 a,b에 대한 `∫(a+xb)†dM(a+xb)≥0`로

\[
\begin{pmatrix}K_0&K_1\\K_1&K_2\end{pmatrix}\succeq0,
\qquad 0\preceq K_2\preceq K_1\preceq K_0
\tag{9}
\]

를 얻는다. K들이 서로 commute할 필요는 없다. singular K0는 range와 kernel을 보존한 pseudoinverse를 사용한다. 원자 spin-average scalar rate에는 미지의 coherence가 들어 있지 않으므로 그 수치로 임의 polarized matrix를 만들지 않는다.

detector effect `0≤E≤I`와 endpoint interpolant l에 대해

\[
|D_E[f]-D_E[l]|\le\frac{\|f''\|_\infty}{2}
\operatorname{tr}E(K_1-K_2).
\tag{10}
\]

첨부 `v=(1,x+1/2)` 예에서 K0의 off-diagonal을 버리면 `(1,1)/√2` detector 응답이 정확히1 변한다. `f=e^{-x}`에는 실제 오차 `.1032248008`, bound `.16875`를 얻었다. finite moment PSD만으로 spectral measure의 유일성을 주장하지 않는다. [C1,C2]

비직교 full-frame `V(s)`의 coefficient covariance R은 physical density `ρ=VRV†`, Gram `G=V†V`를 갖는다. `Γ=V^{-1}V'`이면

\[
G'=G\Gamma+\Gamma^\dagger G,\qquad
R'=-\Gamma R-R\Gamma^\dagger
\tag{11}
\]

일 때 `d tr(GR)/ds=0`이다. analyzer도 `E_c=V†EV`로 pullback한다. 새2×2 예에서 physical trace derivative는0, ordinary coefficient-trace derivative는 `.8658256`이었다. 표현 변화가 물리적 population 변화로 잘못 읽힐 수 있음을 보여준다. rectangular moving subspace에는 complement leakage가 추가되므로 식(11)만으로 닫지 않는다. 현재 Gaia physical beta null을 basis rotation으로 제거했다는 결론도 얻지 않는다.

### 5.5 N5: full-m와 constraint-compatible projection

Bianchi structure `N=N^T,a`의 Jacobi 조건은 벡터 `Na=0`이다. source의 diagonal test `n_diag·a=0`는 충분하지 않다. `n=(1,1,0)`, `a=(1,−1,0)`이면 scalar는0, `Na=(1,−1,0)`다. 새 helper는 벡터를 반환한다. [A2,C1]

STF는 Frobenius-orthonormal basis를 명시해야 한다. raw off-diagonal entry1인 tensor의 norm²은2다. 원 source의 basis tag만으로 raw5component의 Euclidean norm을 같은 물리 norm으로 정하지 않는다. Scholarly geometry의 명시 basis를 공통 adapter로 사용했다.

Lowell의 ell-only draft layout는 `L=6`에서24, full-m I/V/E/B packed layout는 `4(L+1)²−8=188`이다. 이 둘은 같은 상태가 아니다. MZ partition을 수행하기 전에 실제 state ordering·source/mask·Gram을 고정한다.

constraints `C(X,s)=0`, exact propagation `∂s C+D C F=A_C C`가 주어지면 approximation defect r에 대해

\[
\frac{d}{ds}C(\hat X,s)=A_C C+D C\,r.
\tag{12}
\]

따라서 tangent-compatible projection의 `DC r`를 직접 제한한다. omitted stress나 zero placeholder를 물리 kernel로 쓰면 이 forcing을 잘못0으로 만들 수 있다. source의 실제 Thomson draft가 zero를 반환한다는 사실은 **물리적인 memoryzero 결과가 아니다**. constrained current generator와 projection을 결합한 뒤 식(12)를 평가한다.

### 5.6 N6: VIII 유한창의 경계항을 계산

첨부 SU(1,1) convention에서

\[
E_2|n\rangle=in|n\rangle,\quad
A_+|n\rangle=(n+1/2+i\nu)|n+1\rangle,\quad
A_-|n\rangle=-(n-1/2-i\nu)|n-1\rangle,
\]

`E0=(A++A−)/2`, `E1=i(A+−A−)/2`다. Casimir `C=E0²+E1²−E2²=−(ν²+1/4)I`. retained window P, Q=I−P이면

\[
C(PEP)=P C(E)P-\sum_{a=0}^2\eta_a PE_aQE_aP,
\quad\eta=(1,1,-1).
\tag{13}
\]

`PE_a²P=(PE_aP)²+PE_aQE_aP`를 삽입한 정확한 식이다. 경계 `n_min,max=τ∓N_K`의 두 diagonal defect는

\[
\Delta_{min}=\tfrac12[(n_{min}-1/2)^2+\nu^2],\quad
\Delta_{max}=\tfrac12[(n_{max}+1/2)^2+\nu^2].
\tag{14}
\]

원 code의 C3 boundary item은 `True` 상수였다. 이번에는 한 site 넓은 operator에서 cross-boundary term을 실제 계산했다.

| ν,τ,N_K | raw boundary maximum | correction 후 최대 잔차 |
|---|---:|---:|
| .7,.3,4 | 11.765 | 4.48e−16 |
| .7,.3,12 | 82.165 | 9.10e−15 |
| 0,.5,4 | 12.5 | 0 |

raw norm이 커지는 것은 cutoff convergence 실패의 증거가 아니라, 경계의 높은 ladder coefficient를 반영한다. 물리 수렴은 실제 generator L과 state y에 대한 `‖QLP y‖`, retained observable 및 확대창 trajectory 비교로 판별한다. tail memory는 `PLQ U_QLQ QLP`로 구성한다. metric scalar Laplacian을 Casimir와 자동 동일시하지 않으며 spin coupling·emitter·Hilbert/ensemble measure를 추가한다. [A1,C4]

또한 `p(n)q(n+1)=−[(n+1/2)²+ν²]≤0`이지 모든realν에서 `<0`가 아니다. `ν=0,n=−1/2`의 zero를 Wolfram으로 확인했다. 무한차원 domain·global irreducibility는 이 계수 대수 검사보다 추가 정리가 필요하다.

### 5.7 N7: rate와 conditional mark를 한 사건법칙에서 미분

무편극의 scalar angular toy `fγ(μ)=η(1+aμ)`, `η≥0, |a|≤1`에서 Bose factor를 유지하면

\[
p_\eta(\mu)=\frac{1+\eta(1+a\mu)}{2(1+\eta)},\quad
Z=1+\eta,
\]

\[
\langle\mu\rangle=\frac{\eta a}{3(1+\eta)},\quad
\operatorname{Var}\mu=\frac13-\langle\mu\rangle^2,
\quad \partial_\eta\langle\mu\rangle=\frac{a}{3(1+\eta)^2}.
\tag{15}
\]

`η=2,a=.6`에서 평균 `.1333333`, variance `.3155556`, derivative `.0222222`이며 quadrature와 score covariance가 일치한다. total rate `λ=λ0(1+η)`와 mark가 같은 measure에서 나와야 한다. `∂η[λ〈μ〉]=λ0a/3`이다. total rate만 고친 뒤 conditional angle을 isotropic으로 두면 signed response를 잃는다. 이는 LOOP4에서 발견되고 LOOP5 이후 수정된 항목을 이용한 확장이며, 수정된 최신 legacy에 같은 오류가 남았다고 재보고하지 않는다. [A3,C1]

실제 independent marked-event law가 주어지면 DP/PGF에는

\[
\partial_t\log Z[J;t]
=\lambda_t\left[\int e^{J\cdot m}p_t(dm)-1\right]
\tag{16}
\]

가 들어간다. 단일 사건의 daughter-photon 에너지와 다른 daughter 에너지를 같은 mark로 두면 eventwise conservation과 covariance를 함께 보존한다. 이 법칙의 η 미분은 통계적 response이지 η가 자동 physical jump time이라는 뜻이 아니다. matrix coherency의 stimulated law는 scalar Bose factor 대신 원본 paired jump/positive matrix construction을 사용한다.

state-dependent monotone clock `ds/dt=v(X)>0`에서는 backward generator가 `L_s f=v^-1 L_t f`, forward가 `L_s* p=L_t*(p/v)`다. forward operator 밖에 `v^-1`을 잘못 놓지 않는다. DP jump propensity는 departure state에서 `a_r(n)/v(n)`로 바뀐다. stationary law·sampling measure도 이 time change에 맞춰 구분한다.

### 5.8 N8: turning point에서는 유한 bin 응답을 계산

`t∈[−1,1]`, `z=t²−ε`, positive event density `r exp[−r(t+1)]dt`를 두자. bin `z≤0`의 질량은

\[
B(\varepsilon)=2e^{-r}\sinh(r\sqrt\varepsilon)
=2r e^{-r}\sqrt\varepsilon+O(\varepsilon^{3/2}).
\tag{17}
\]

r=.3에서 `B/√ε→.4444909324`. `ε=10^-2,10^-4,10^-6,10^-8`을 직접 branch 적분과 비교했다. `B/ε`는 `4.4456→4444.9093`으로 커진다. 이 원점에는 일반 Lipschitz derivative가 없다. 그러나 positive pushforward measure와 유한 bin 변화는 명확히 계산할 수 있다.

따라서 nonmonotone redshift를 단일 time coordinate로 바꿀 때는 root branch·coarea Jacobian·event crossing을 보존하고, fold 근방에서는 pointwise derivative 대신 bin·weak response 또는 해당 regularity bound를 사용한다. 이 사례가 모든 optical observable을 미분 불가능하게 만드는 것은 아니다. 정칙 branch의 endpoint tangent는 기존 식을 계속 사용한다.

구현은 `exp[−r(1−√ε)]·[−expm1(−2r√ε)]`로 평가한다. 독립 검토에서 원 표현의 `ε=1,r=1000`의 `0×∞`를 발견해 이 안정식으로 바꿨고 정확한 finite limit을 확인했다. [C1]

### 5.9 N4/N5 확장: 움직이는 부분공간과 통계 내적의 정확한 memory

전체 가역 frame의 connection과 실제 resolved subspace의 변화는 다르다. 유한 ambient 공간에서 `X′=A(θ)X`, full-column-rank `V(θ)`를 주고

\[
G=V^\dagger V,\quad L=G^{-1}V^\dagger,\quad P=VL,\quad Q=I-P,
\quad \Gamma=LV',\quad B=QV'
\]

로 정의한다. θ가 시간 이외의 변수이면 `X′=AX`라는 transport law 자체가 추가 전제다. `a=LX`, `q=QX`에 대해 직접 미분하면

\[
a'=(LAV-\Gamma)a+(L'+LA)q,\qquad
q'=(Q'+QA)q+(QAV-B)a.
\]

따라서 `∂θ U_Q(θ,u)=(Q′+QA)(θ)U_Q(θ,u)`의 propagator를 사용한 정확 kernel은

\[
K(\theta,u)=(L'+LA)(\theta)U_Q(\theta,u)
[QAV-B](u).
\tag{18}
\]

초기항 `(L′+LA)(θ)U_Q(θ,θ₀)q₀`도 유지한다. `Q′`는 unresolved vector가 움직이는 `ran Q`에 머물게 한다. 직접 반례 `A=0`, `X₀=(1,0)`, `V=(cos θ,sin θ)^T`에서는 `G=1,Γ=0`인데 `B≠0`이다. 정확히 `a′=b,b′=−a`이므로 `a=cos θ`이며 kernel은 −1이다. Γ만 포함한 구현의 `a′=0`와 다르다. 이는 좌표 선택이 만드는 memory이며 실제 물리 감쇠라고 읽지 않는다.

통계 내적까지 바뀌어 `G=V†WV`, `L=G⁻¹V†W`라면 같은 block 소거는 `LV=I`로 성립하지만,

\[
G'=G\Gamma+\Gamma^\dagger G+V^\dagger W'V
\tag{19}
\]

가 된다. `W′`는 normalized law의 score와 결합한다. `pη∝wη p0` 아래
`∂η⟨A⟩=⟨∂ηA⟩+Cov(A,∂η log wη)`이므로 projection의 covariance/Gram도 함께 변한다. N7의 `b=aη/(1+η)`에 대해서는

\[
\mathcal I_\eta=\frac{a^2}{(1+\eta)^4}
\frac{\operatorname{artanh}b-b}{b^3},\qquad
\lim_{b\to0}\frac{\operatorname{artanh}b-b}{b^3}=\frac13.
\tag{20}
\]

`a=0`이면 조건부 방향분포의 Fisher 정보는0이지만 총 rate는 η에 따라 변한다. 따라서 Fisher 길이만으로 counting 정보까지 보존했다고 할 수 없다. 해당 통계변수를 clock로 부르려면 이 구분과 실제 transport law를 먼저 고정해야 한다.

현재의 `x,Q,Π,F,G_F`는 richer carrier와 그 관측 view들이다. 위 `a∈R^k`를 무조건 다섯 scalar와 동일시하지 않는다. 이미 정의된 view들에서 사용할 observable map과 실제 reference covariance를 구체화한 뒤 그 차원에 맞는 P를 구성한다. [A2,A3]

### 5.10 N5 확장: 제약 chart와 작은 Thomson memory 모델

`C(s,χ(s,z))=0`인 정칙 chart로 근사 상태를 `Xhat=χ(s,z)`라 두면
`r=∂sχ+D_zχ f−F(s,χ)`는 정확 제약 전파식의 constraint surface에서 `D_X C r=0`를 만족한다. 이는 closure residual이 정확도를 떨어뜨리는 일과 제약을 깨는 일을 분리하는 구성이다. positivity와 좋은 statistical fit은 별도 조건이다. 두 종의 보존 반응을 한 종 frozen closure로 바꾸면 inventory가 깨지는 반례와, `χ(u)=(u,1−u)`를 이용한 보존형 축약을 [A3]에 전개했다.

Lowell 00D의 **선언된 moment normalization**에서 electron-frame collision subproblem은

\[
\frac{d}{d\eta}\binom{I}{E}
=\kappa(\eta)\begin{pmatrix}-.9&.6\\.1&-.4\end{pmatrix}
\binom{I}{E}.
\]

상수 κ에서 E를 제거한 memory는 `0.06 κ² exp[−0.4κ(η−u)]`다. κ>0인 구간의 누적 opacity `s=∫κdη`에서는 `0.06 exp[−0.4(s−v)]`가 된다. 이 normalization의 `I²+6E²`는 `d/ds≤−0.6(I²+6E²)`를 만족한다. moment matrix는 column-conservative Markov generator가 아니므로 I,E를 그대로 확률 population이라고 해석하지 않는다. 보존 Markov 부분과 diagonal potential의 명시 분해를 [A2]에 제시했다. 실제 angular coherency integral과 이 moment normalization의 동등성은 다음 작은 판별 대상이다.

같은 Lie type 안의 parameter response에는 `N=FN₀Fᵀ`, `a=det(F)F⁻ᵀa₀`를 사용할 수 있다. `N₀a₀=0`이면 Jacobi·rank/inertia가 유지되며, `B_i=(∂iF)F⁻¹`에 대해 `∂iN=B_iN+NB_iᵀ`, `∂ia=(tr B_i I−B_iᵀ)a`다. crossing에서는 정렬된 개별 eigenvector 대신 외부 spectrum과 분리된 cluster projector의 contour derivative를 사용하는 경로를 [A3]에 구성했다. 이는 같은 orbit을 벗어나는 실제 parameter 변화를 대신하지 않는다.

**근거 상태:** 이 두 확장절과 [A2,A3]의 추가 보조정리는 직접 유도다. 아래32개의 실행 검산은 앞선 명시된 finite fixture 범위이며, moving-rectangular projector·W′·Thomson angular projection·Lie cluster의 새 구현을 시험했다고 확대하지 않는다.

## R6. 독립 검증과 근거의 수준

한 번의 독립 source·수식 검토를 수행했다. Schur 부호·weighted mass·moment derivative·Gram/detector·moment envelope에서 지정 finite 결과를 뒤집는 오류는 찾지 못했다. 실제 발견한 세 사항은 수정했다: fold의 large-rate overflow, finite-bin 함수의 positive-generator/reward·finite-endpoint 계약, detector의 Hermitian/effect 계약. 기존27항목에 해당 corner5개를 추가해 최종32항목을 실행했다. 이 추가는 이름 있는 잔여 위험의 해소이며 임의 범위 확대가 아니다. [C1,A2]

Wolfram은 이번에 실제 동작했다. 이전 보고서의 연결실패를 현재 상태로 복사하지 않았다. VIII algebra13개와 Schur mass/counterexample을 확인했다. Schur 추가검산의 첫 시도는 protected symbol C/D 사용 때문에 무효였으며 실패 기록을 별도 보존한 뒤 변수명을 수정했다. 성공 출력은 exact zero vector/matrix와 `−12/25`를 반환했다. Lean/lake proof checker는 실행하지 않았다.

수치 결과의 scope를 실제 iterator에 맞췄다. 표본·quadrature·finite chain 결과는 일반 continuum proof가 아니며, Scholarly의 certificate를 읽고 재조립한 것은 그 certificate producer의 directed continuum 계산을 새로 수행한 것이 아니다.

## R7. 실제 계산 수행

| 작업 | 실제 수행 | 결과 범위 |
|---|---|---|
| 신규 source 정독 |362개 body + 명시된 complete diffs | 누락0, source semantics·role catalog |
| Scholarly six calculation | original portable scripts/input hash 고정, assertions 활성, 격리 실행 |6/6 성공, 입력 hash 전후 불변 |
| 새 response primitives |8개 수학 경로,32 finite assertions | full resolvent/quadrature/analytic counterexample·contract corners |
| 원 VIII SymPy/mpmath | original local kit 실행 |16 reported items; C3 상수True는 실제검사에서 분리 |
| Wolfram |13 VIII algebra + Schur 확장 | independent symbolic finite identities |
| 새 VIII boundary |3 finite window cases | PEQEP correction identity |
| native HYRec archived output |6 history와 관련CSV 전행 파싱·재분석 | original source-reported 수치 재현; 새 native run 아님 |
| current R100 | immutable identity 확인 | 기존 실행 증거 재사용 |

실행 명령·버전·시간·입력 전후 hash·outputs는 `research/COMPUTATION_MANIFEST.json`, `runs/scholarly_reproduction/COMPUTATION_MANIFEST.json`, `analysis/bass_viii_runs/`에 있다. 원 source의 전체 test suite, Rust build, native HYRec 재실행, physical VIII full atlas, all60 science execution은 이번 범위에서 수행하지 않았다.

## R8. 결과 판정과 blocker의 정확한 변화

### 해결하거나 작게 만든 부분

- 전수 code review의 남은 목록을0으로 만들고 exact duplicate를 하나로 모았다.
- basename에 의존하지 않고 byte identity와 의미/환경 identity를 분리했다. density input은 `positive_hydrogen_ratio.dat` alias로 이미 존재함을 확인해 불필요한 재취득을 없앴다.
- Schur memory의 물리 clock·weighted mass 식, finite observation-bin 응답, positive matrix detector bounds를 재사용 코드로 만들었다.
- VIII boundary의 상수 통과 항목을 실제 계산 가능한 식과 oracle로 보완했다.
- full-m/STF/Jacobi/clock 혼동을 concrete adapter 계약과 counterexample으로 바꿨다.
- 이미 수정된 LOOP4→5 Bose-law 문제와 여전히 남은 Lowell source 문제를 구분했다.

### 남은 입력·구현 의무

| 분류 | 정확한 내용 | 다음 최소 실행 |
|---|---|---|
| 데이터/원본 누락 | H2248와 calibrated cosmoparams, atomic table5개, zero-payload baseline6개 | DATA_RECOVERY_PLAN의 exact SHA/commit/owner 경로로 복구 |
| 물리 정의 미확정 | H의 clock·frame, radiation drift/escape, actual rate capacity | original generator와 current convention을 연결해 adapter를 명시 |
| 구현 미완성 | zero Thomson fixture·identity streaming·24/188 layout·Rust names/enum | actual nonzero authority kernel 연결 전 최소구현 수정 |
| 이론/closure | arbitrary tilted radiation의 effective atomic correction, VIII physical Hilbert/atlas measure | 외부원전 적용역 검토 + project-specific source/ray/metric 구성 |
| 관측 외부입력 | CF4 calibration/selection/velocity law, radio RMS/completeness/association, Gaia scan/AGN law, independent flux | 기존 R100 취득물을 재사용하고 부족한 law/metadata를 확보 |

특히 Rust residual IDs의 unqualified enum entries, missing match arms, summary-name mismatch 및 shell을 Python으로 실행하는 offline script 경로는 source-derived 결함이다. 원 crate의 실제 compiler diagnostics를 이번에 얻었다고 표기하지 않는다. 반대로 vendor/wheelhouse 부재와 수학적 미완성을 하나의 ‘환경 문제’로 묶지도 않는다. 상세 SHA와 위치는 `LOWELL_RESEARCH.md`와 파일별 장부에 있다.

새 일반 strong no-go를 제시하지 않는다. 식(4)는 특정 first-memory local approximation의 양성 반례, 식(17)은 지정 fold의 regularity 반례다. 둘 다 실제 positive realization 또는 weak/bin response라는 다음 경로를 제공한다.

## R9. 6대주제·7교차 축·60노드에 적용

`NODE_APPLICATIONS_60.json/.md`는 원 node ID60개 각각에 새 경로, legacy SHA, 실제 current hook, additional inputs, 다음 계산을 연결한다. 원 status·acceptance·external_missing을 보존했다. 6대주제와7개 PHY는 다음처럼 연결된다.

| 축 | 이번 확장의 주된 기여 |
|---|---|
| P1 five-view | common positive law·detector bound·finite-bin response를 같은 draw의 x,Q,Π,F,G_F에 전달 |
| P2 low-l/morphology | native xe/opacity tangent, coherency moments, full-m/K-tail의 observable error |
| P3 directional Hubble | source-redshift branch·survey window·same-parent law와 actual covariance |
| P4 boost/tilt·radio | fixed-pixel analyzer/aberration, global history와 local endpoint 분리, mark/rate joint response |
| P5 Bianchi | vector Jacobi, exceptional Codazzi, physical STF metric, VIII boundary와 native atlas 계약 |
| P6 beyond-FLRW kinematics | common congruence·screen/Gram·finite-redshift tangent 및 nonradial law의 qualification |

| 교차 | 기존 구성 보존 | 적용 |
|---|---|---|
| PHY-01 | P3/P6/P5 | window·geometry·optical endpoint/branch response |
| PHY-02 | P2/P6/P5 | positive photon moments와 normal-flux/Codazzi constraints |
| PHY-03 | P2/P4 | 동일 beta의 CMB/radio response를 각 선택법칙에 전달 |
| PHY-04 | P6/P4/P5 | observer Gram과 실제 Lie-frame B2/local E2 구분 |
| PHY-05 | P5/P6 | exceptional rank와 admissible native modes·physical flux |
| PHY-06 | P1/P2/P5/P6 | delay/ell4/eigenframe 변화를 common five-view law로 pushforward |
| PHY-07 | P1/P3/RADIO_DIPOLE | radius/selection-conditioned common event law와 covariance |

Saha→kinetic tangent의 초기화, proper density→chemical/radiation clock, atomic/static Schur→actual dynamic memory, retained modes→physical detector의 네 interface를 구현하면 서로 독립이던 legacy 계산을 한 forward-response 경로로 결합할 수 있다. 다섯 view는 그 경로에서 나온 상관된 관측 결과로 유지한다. 개별 summary를 독립 likelihood로 곱하거나 five-scalar closure를 가정하지 않는다.

## R10. 다음 재개점과 산출물

첫 실행점은 기존 checkout의 dirty state를 보존한 read-only identity 확인이다. 최신 current AGENTS의 existing-checkout 정책에 맞춰 `/home/cosmosapjw/Dropbox/bianchi/htt_base`를 기준으로 하고, 자동으로 새 worktree를 만들도록 했던 이전 handoff 문구를 교정했다. 현 사용자 no-push 조건을 유지한다. 이번 연구 자체는 별도 scratch 산출물로 완결했다.

local agent의 구체적 첫 개발 단위는 다음과 같다.

1. DATA_RECOVERY_PLAN에서 already-present density alias를 재사용하고 H/table/cosmoparams의 exact identity와 clock를 복구한다.
2. `NativeHistoryAdapter`의 density, chemical clock, radiation drift, expansion, x_e convention을 분리하고 FLRW/zero-tilt 회귀와 actual parameter tangent를 비교한다.
3. 실제 rate/capacity block이 있는 한 구간만 골라 full tangent, exact memory, static Schur, first-memory response를 같은 finite observable로 비교한다. initial layer·source forcing을 유지한다.
4. actual hierarchy layout를 full-m으로 고정하고 zero fixture를 실제 Thomson kernel과 분리한다. vector Jacobi/Gram/physical units의 concrete failures를 수정한다.
5. VIII는 algebra boundary와 state/observable tail을 별도 기록하며 actual five-emitter L에 QLP leakage와 memory를 붙인다.
6. source-qualified joint law가 준비된 관측 경로에서만 five-view output과 uncertainty를 갱신한다.

전체 전달물은 `README_KO.md`, `CATALOGUE.html`, `FILE_CATALOGUE.json`, `FILE_OCCURRENCES.tsv`, `CONSOLIDATION_DECISIONS.md`, `canonical/`, 이번 보고서, node map, data recovery plan, `HANDOFF_LOCAL_AGENT_KO.md`, 원 근거 및 실행 manifest다. source byte 보존/복구 검증과 과학적 성립은 각각의 장부로 남겼다.

## 근거 목록

- [G1] `current/CURRENT_STATUS.json`, `CURRENT_BRIDGE.md`, `HEAD_CHECK_RECEIPTS.json`; 이전 `CURRENT_REFERENCE_PROVENANCE.json`.
- [A1] `reviews/BASS_VIII_RESEARCH.md`, `BASS_VIII.jsonl`, `BASS_ARCHIVED_DATA_RECHECK.json`, `BASS_CSV_DATA_RECHECK.json`.
- [A2] `reviews/LOWELL_RESEARCH.md`, `LOWELL.jsonl`, `LOWELL_DOCUMENTS.jsonl`, `INDEPENDENT_RESPONSE_REVIEW.md`.
- [A3] `reviews/LOOP10_RESEARCH.md`, `LOOP10.jsonl`, `LOOP10_DOCUMENTS.jsonl`.
- [C1] `canonical/response_primitives.py`, `research/response_discriminators.py`, `RESPONSE_RESULTS.json`, `COMPUTATION_MANIFEST.json`.
- [C2] `runs/scholarly_reproduction/BASS_Scholarly_Dossiers/calculations/results/RUN_SUMMARY.json` 및 여섯 결과와 입력 hash.
- [C3] `research/WOLFRAM_SCHUR_RECEIPT.json`; 무효 protected-symbol 시도는 `WOLFRAM_SCHUR_FAILED_ATTEMPT.json`.
- [C4] `analysis/bass_viii_runs/PROJECTED_CASIMIR_RESULT.json`, `WOLFRAM_CONNECTOR_RESULT.json` 및 원 script/adapter.
- [L1] Y. Ali-Haïmoud and C. M. Hirata (2010), *Ultrafast effective multilevel atom method for primordial hydrogen recombination*, Phys. Rev. D82,063521. https://doi.org/10.1103/PhysRevD.82.063521 . effective interface-rate network의 원전; 이번 확인은 publisher abstract의 범위.
- [L2] N. Lee and Y. Ali-Haïmoud (2020), *HYREC-2: a highly accurate sub-millisecond recombination code*, Phys. Rev. D102,083517, §II.2–III.1. https://arxiv.org/html/2007.14114v2 ; https://doi.org/10.1103/PhysRevD.102.083517 . quasi-steady equations, history-dependent radiative rates, escape H dependence와 parameter correction 범위.
- [L3] M. te Vrugt and R. Wittkowski (2019), *Mori-Zwanzig projection operator formalism for far-from-equilibrium systems with time-dependent Hamiltonians*, Phys. Rev. E99,062118. https://doi.org/10.1103/PhysRevE.99.062118 . 시간의존 형식화의 문헌 근거; 이 보고서의 finite block identity는 직접 유도.
- [L4] HYREC-2 official source: https://github.com/nanoomlee/HYREC-2 . 파일 복구 후보이며 latest upstream과 legacy parent의 byte identity는 미확정.
