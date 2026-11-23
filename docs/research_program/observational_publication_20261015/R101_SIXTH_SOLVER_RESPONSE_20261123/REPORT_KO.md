# R101 — 여섯 번째 이론·코딩 연구: CF4 응답, 편광 수송, 화학시계, 이동 투영

작성일: 2026-11-23. 출발 commit: `f8931fbef075d55c2c2a3caee8b8f5db5174b16b`. 연구 branch: `research/r69-observable-physics-bridges-20261118`. 실제 출판 commit과 원격 확인은 이 디렉터리의 `PUBLICATION_RECEIPT.json`을 따른다.

## 결과와 범위

SQ-CF4에서 다시 시작하여 이론 R1–R10과 코딩 C1–C10을 수행했다. 이전 네 연구를 원문·provenance와 함께 통합하고, 현재 R100 코드 위에 CF4 예측 응답, 전체 공개-parent 매칭 패턴의 조건부 우도, 편광 충돌의 정확 전파, 강한 충돌을 포함하는 Fourier 수송, proper-time 화학반응과 광학깊이 tangent, 이동 투영의 기억항을 구현했다. 소유자의 기존 checkout에서 원표 분석과 다섯 조건부 작업을 실제 실행했다.

가장 큰 관측 결과는 같은 7,190개 6dFGSv 거리 mark에서도 나머지 1,695개 공개 행의 매칭 실패 상태를 조건에 포함하면 혼합장 대 영장의 log density 차이가 −11.942159에서 +27.341020으로 바뀐다는 것이다. 가장 중요한 구현 교정은 기존 Thomson Mueller 연산자의 선편광 부호와 강성 극한의 보존 모드 손실이다. 가장 중요한 물리적 구분은 normal-frame 팽창시계, baryon proper-time 화학시계, 광자 주파수 drift 및 선 탈출의 역할이다.

현재 결과가 닫은 것은 명시된 통계·수치 부분문제다. R78의 60개 노드·129개 간선과 원래 42개 과학 판정 조건은 유지했다. 조건부 실행은 공유 계산 다섯 개이며, 60개의 독립적인 관측 검증을 수행한 것으로 집계하지 않는다. 새 과학적 승격은 0이다. 데이터·보정 부족과 남은 native 기하 수송의 개발을 아래에서 구별한다.

### 권위와 기존 정책의 교정

사용자의 이번 명시적 지시에 따라 직접 native solver 개발과 연구 branch push를 허용하도록 `AGENTS.md`와 current context를 교정했다. 과거 R78의 원문에 남은 “외부 solver만 기다림/직접 구현 금지”는 역사적 기록이다. 이번 실행 overlay의 M08·M09·A03은 실제 코드·이론 개발 항목이다. main/merge/force-push는 이번 작업에 포함하지 않는다.

`docs/SSOT_POLICY.md`의 보편적 `D_u=(1/a)∂η` 표현도 교정했다. 이 식은 normal congruence의 경우이고, 공간적으로 균일한 스칼라에 대해 tilted baryon의 미분은 `D_ub=Γ D_n`이다. 공간 기울기가 있으면 advective 항이 추가된다. 잘못된 기존 식을 유지하여 새 코드만 우회하지 않았다. 반면 canonical DAG를 새 결과에 맞춰 느슨하게 고치지는 않았다.

## 1. 앞선 네 연구의 실제 재사용

| 선행 연구 | 이번에 유지한 구조 | 구현·검증으로 확장한 부분 |
|---|---|---|
| DP–MZ 보조연구 | 생성자가 있는 상태변수와 함수적 관측량 구별; 공유 latent field 아래 선택 정규화 | 유한 양의 화학상태 전파, 지연 채널, 초기 hidden-state 보존; 객체별 우도를 장 수준에서 공동 정규화 |
| 비시간 모수 응답 연구 | 진화 좌표와 외부 모수 분리; 변화하는 내적과 투영의 미분 | CF4 covariance path tangent, 반응률·팽창·tilt·방향·밀도 tangent, `V′,W′`를 포함한 이동 MZ |
| 첫 legacy 정독·통합 | 동일 관측 사건·측도·좌표와 원천 provenance; 편광 tensor carrier | 기존 BASS의 rank-nine Thomson exponential을 현재 `bass`로 이식하고 연속 원천 및 I/Q/U/V 인터페이스 추가 |
| 추가 legacy 정독·통합 | 순서가 있는 전파, Lie/Jacobi·경계 결함, 이동 projector와 Kato 구조 | 직접 Jones 비교, stiff Schur 해법, 원 HYREC 입력 복구, 범용 재사용 코드와 전체 카탈로그의 저장소 편입 |

네 원문은 `prior_studies/`에 있다. 과거 결과의 범위와 당시의 미실행 상태를 그대로 보존했다. `legacy/research_supplements_20261123/FILE_CATALOGUE.json.gz`에는 4,073개 항목이 들어 있다. 이 중 기존 정독 기록은 코드 1,354개(전체 1,263, diff 91), archive 23개·member 5,038개·정확 중복 965개다. 이번 회차에서 이들 전부를 새로 실행하거나 다시 정독했다고 집계하지 않는다. 카탈로그의 과거 `canonical_path`는 당시 delivery bundle의 경로이며 현재 checkout에 모든 원본이 설치됐다는 뜻이 아니다.

압축 카탈로그 SHA-256은 `dd6e013fc8702e6451b8ec518b3d2405fd4528faf6b58946cc3c17b8f47f2254`, 압축 해제 내용은 `732faefb69567b9a9bc6c394007a19e9606df9aaf6ed6a377c9d6caeac7c90f5`다. 전체 archive 중복을 추가로 쌓지 않고 원문 보고서, 파일 계보, 공통 helper, 실제 port를 통합했다.

## 2. SQ-CF4: 평균·공분산·선택 법칙의 응답

### 2.1 nuisance를 유지하는 예측 응답 — derived / implementation-verified

기존 4×9 요약을 앞의 18성분 훈련, 뒤의 18성분 평가로 나누고 공통 평균 9개를 훈련에만 적합한다. 고정 설계에서 `E[y_t]=Xβ`, `E[y_s]=Hβ`로 둔다. `U`는 `Xᵀ`의 영공간 기저, `L=HX⁺`, `T=(Uᵀ,0)`, `W=(-L,I)`라 하자. 공분산 경로는 `C(α)=C₀+αD`다. 다음 행렬은 미지 평균을 소거한다.

\[
V=TCT^T,\quad K=WCT^TV^{-1},\quad B=W-KT,
\qquad e=By=y_s-m,\quad S=BCB^T.
\]

`BCTᵀ=0`이므로 미분에서 교차항이 소거되어

\[
m'=BDT^TV^{-1}Ty,\qquad S'=BDB^T.
\]

`v=S⁻¹e`, `q=eᵀv`, `ℓ=−[q+log det S+n_s log(2π)]/2`이면

\[
q'=-2m'^Tv-v^TS'v,\qquad
\ell'=-\tfrac12\{q'+\operatorname{tr}(S^{-1}S')\}.
\]

이 식은 error contrast를 사용하는 Gaussian fixed-effect 예측의 직접 미분이다. 통계적 고정효과 처리의 기존 근거는 [Harville (1974)](https://doi.org/10.1093/biomet/61.2.383), 프로젝트 식·구현·원표 정체성은 [CF4_THEORY_KO.md](CF4_THEORY_KO.md)에 있다. 양정치 공분산과 full-rank training design이 전제이며, rank가 부족한 경우 jitter로 문제를 바꾸지 않고 실패를 반환한다.

| covariance 위치 | q | log predictive density |
|---|---:|---:|
| α=0 | 12.116320633 | 65.698955588 |
| α=0.5 | 11.435438 | 65.294925 |
| α=1 | 10.927665138 | 64.930844207 |

중점의 `q′`는 평균 이동 `+0.35948256`, 공분산 변화 `−1.50796389`, 합 `−1.14848133`이다. `q`의 감소와 log density의 감소가 동시에 일어난다. 후자에는 예측 부피의 변화가 들어간다. 기존 양 끝점과의 최대 차이는 `5.69×10⁻¹⁴`; 미분의 구적값으로 복원한 `Δq,Δℓ`의 오차는 각각 `1.60×10⁻¹⁴,4.59×10⁻¹⁴`였다. 이는 기존 동일 압축 자료의 응답이며 새로운 원시자료 독립 holdout은 아니다.

### 2.2 관측되지 않은 mark를 적분한 공개-parent 선택 — numerically checked

공유 장 지표 `h`에 대해 `η_i|h ~ N(m_hi,s_i²)`, 포함확률을 `Φ(a_i+b_iη_i)`로 놓으면

\[
\pi_{hi}=\Phi\!\left(\frac{a_i+b_i m_{hi}}{\sqrt{1+b_i^2s_i^2}}\right).
\]

고유 매칭 행을 `I`, 공개 표에 있으나 고유 매칭되지 않은 행을 `J`라 하자. `J`의 mark를 적분 소거한 조건부 밀도는

\[
p(\eta_I\mid I,J)=
\frac{\sum_h p_h\prod_{i\in I}N(\eta_i;m_{hi},s_i^2)\Phi(a_i+b_i\eta_i)
\prod_{j\in J}(1-\pi_{hj})}
{\sum_h p_h\prod_{i\in I}\pi_{hi}\prod_{j\in J}(1-\pi_{hj})}.
\]

음의 매칭 사건은 단일 장에서는 상쇄되지만, 여러 장을 혼합하면 장마다 다른 가중치를 준다. `μ=μ₀−5η` 변환은 joint log density에 `−|I|log 5`를 더한다. native η의 부호와 표본의 선택 방향을 혼동하지 않았다.

소유자 환경의 실제 입력은 공개 6dFGSv 8,885행, CF4 고유 매칭 7,190행, 나머지 1,695행(미매칭 1,691·ambiguous 4)이다. 장은 R100의 전역 radial shift 다섯 값 `[-300,-100,0,100,300] km/s`이며 Gaussian mark 폭과 bolometric mean template를 고정했다.

| 같은 7,190개 mark의 비교 | log p(mixture) − log p(zero) |
|---|---:|
| 종전 예시 soft cut | −224.664087 |
| fitted match probit, 양의 매칭 사건만 | −11.942159 |
| 같은 fitted probit, 전체 8,885개의 매칭 패턴 | +27.341020 |

fitted 두 경우의 영장 log density는 모두 `−5727.256929`다. 변화량 `39.283180`은 선택 패턴에 따른 혼합장 재가중에서 나왔다. 구 예시 컷 재현 오차는 `2.01×10⁻¹¹` 이하, 전체 패턴 score의 중앙차분 오차는 `1.12×10⁻⁶`였다. 자세한 관측값과 원표 SHA는 [CF4_RAW_SOURCE_RESULTS_KO.md](CF4_RAW_SOURCE_RESULTS_KO.md), 실제 출력은 [CF4_PREDICTIVE_RESPONSE.json](CF4_PREDICTIVE_RESPONSE.json)에 있다.

이 비교를 물리적 bulk-flow 검출이나 모델 evidence로 승격하지 않는다. probit 계수는 같은 공개 코호트에 적합한 plug-in 값이고, Gaussian 폭 근사·유한 시나리오를 사용했으며 독립 calibration/holdout이 없다. 공개 표 내부의 매칭 실패는 전 방법 CF4의 survey-target rejection 전체가 아니다. 이 결과가 직접 요구하는 다음 분석은 selection 계수의 불확실성, 원 영점·부호의 계보, 그룹 단위 holdout, source-level 공분산을 포함하는 재분석이다.

## 3. 직접 개발한 편광 solver

### 3.1 기존 Mueller 부호 오류와 정확한 충돌 — established / ported / implementation-verified

차가운 비자화 전자 rest frame, `ℏω≪m_ec²`, 진행 방향 `n`, 오른손 screen `u×v=n`을 사용한다. `J_uv=(U−iV)/2`이고 `P=1−nnᵀ`이다. 전자 proper-time의 양의 광학깊이를 `ds=n_e σ_T c dt`로 두면

\[
\frac{dJ}{ds}=-J+\mathcal D(M),\qquad
M=\int J\,d\Omega,\qquad
\mathcal D(M)=\frac{3}{8\pi}PMP.
\]

구면 2차·4차 모멘트를 적분하면

\[
\int\mathcal D(M)d\Omega=\frac35M+\frac1{10}M^T+
\frac1{10}\operatorname{tr}(M)I.
\]

trace, real STF, imaginary antisymmetric 성분의 gain 고유값은 `1,7/10,1/2`이고 차원은 `1,5,3`이다. 잔여 sky의 loss rate는 1이다. trace는 보존되고 원편광 dipole의 감쇠율은 `1/2`; 초기 `V=0`이면 이 충돌만으로 V가 생기지 않는다. 이 homogeneous exponential은 과거 BASS에 있던 구조를 복구·이식했다. 새 발견으로 취급하지 않는다. 연속 affine source의 정확 적분과 현재 IQUV API를 추가한 것이 이번 개발이다. 텐서 산란의 원전과 식 위치는 [SOLVER_THEORY.md](SOLVER_THEORY.md)에 정리했다.

기존 구현은 산란면 안쪽을 첫 screen 축으로 택한 뒤 수직축용 Mueller 식을 적용했다. 90° 산란에서 물리적으로 `Q/I=−1`인 fixture가 `+1`을 반환했고 기존 시험은 절댓값만 확인했다. raw/cached 경로를 함께 고치고 별도 Jones 곱으로 대조했다. 무작위 sky에서 generator 최대 차이는 `0.4118251`에서 `4.44×10⁻¹⁶`으로 줄었다. 거의 평행한 광선의 cross product도 안정화했고 `10⁻¹⁴ rad` 사례에서 `2.22×10⁻¹⁶` 차이를 얻었다.

### 3.2 강성이 큰 Fourier 수송 — numerically checked

평탄 FLRW tetrad에서 `Re[S_k(n)exp(+ik·x)]`, `k[rad/Mpc]`, 셀 길이 `Δχ=cΔη[Mpc]`를 사용한다. frozen cell의 식은

\[
\frac{dS}{du}=\{-i\Delta\chi(k\cdot n)+\Delta\tau\,\mathcal C\}S+F.
\]

streaming과 collision은 일반적으로 비가환이다. 기본 시간적분에는 `γ=1−1/√2`인 2단계 L-stable SDIRK2를 사용했다. collision gain의 rank-nine 구조를 이용해 각 stage를 대각 연산과 `6×6,3×3` 선형계로 계산한다. 큰 `Δτ`에서 trace pivot을 `1−거의1`로 계산하지 않고 보존 모드 Schur 형태로 평가한다. zero-k/zero-opacity에도 같은 이산식을 써 수치 함수의 불연속을 없앴다. 정확한 subflow의 Strang 선택지도 남겼다. 방법 계열의 원전은 [Alexander (1977)](https://doi.org/10.1137/0714068)이고, 안정한 보존 pivot과 현재 tensor factorization은 코드·독립 dense 비교로 검증했다.

강성 monopole fixture `Δτ=1000`에서 한 번의 Strang 오차는 `0.80478`, 한 SDIRK2 step은 `8.48×10⁻⁶`, 8 substep은 소유자 실행에서 `1.07×10⁻¹²`였다. 그러나 generic 복소 원천에서는 한 step의 오차가 더 크다. 독립 검토의 `Δτ=3`, 16·32·64 substep 오차 `7.99×10⁻⁴,1.98×10⁻⁴,4.93×10⁻⁵`가 2차 수렴을 보였다. L-stability는 임의 입력에서의 한-step 고정 정확도를 뜻하지 않는다.

### 3.3 실제 이력·signed modes·비용

R100 harmonic builder의 angular advection을 0으로 둔 독립 collision/source 비교에서 L=6의 signed `I49+E45+B45+V49=188`개 complex slot을 모두 대조했다. ±m reality가 있으므로 188개의 독립 실수 자유도는 아니다. 소유자 실행의 최대 오차는 I/E/B/V 각각 `1.35×10⁻¹⁵,1.22×10⁻¹⁵,1.06×10⁻¹⁵,7.89×10⁻¹⁶`였다.

현재 HYREC reference table의 z=1150→950, 200개 셀로 `Δτ=1.7710404`, `Δχ=41.02159085 Mpc`를 얻고 `k=(.03,−.015,.011)/Mpc`를 전파했다. 시간 해상도 두 배에서 최대 harmonic 차이는 `1.744×10⁻¹⁰`; 최종 I/E/B/V norm은 약 `5.594×10⁻⁵,1.141×10⁻⁵,4.077×10⁻⁶,2.960×10⁻⁵`였다. 표준 opacity와 지정한 초기 sky·원천을 쓰는 계산이다. CMB 관측 적합과 nonlinear 모든 Bianchi family의 해는 별도다.

N=8192에서 cached 각도 배열은 1,441,792 B이며 exact homogeneous action의 소유자 실행 시간은 약 0.760 ms였다. 같은 N의 전체 `4N×4N` float64 matrix는 산술적으로 8,589,934,592 B이지만 이를 실제 할당하여 비교하지 않았다. N=32의 native action은 약 28.5–30.2 μs, 매번 새로 구성하는 dense exponential+action은 0.586–1.875 ms였다. 한 고정 깊이의 dense propagator를 캐시하는 비교와는 다르다. 소유자 Python 3.12.3/NumPy 2.5.4/SciPy 1.18.1, 단일 BLAS thread의 측정이며 scratch author benchmark와 섞지 않는다.

## 4. DP와 REC/REI: 생성자를 가진 상태의 시계와 응답

### 4.1 proper chemistry와 opacity의 분리 — derived

공간적으로 균일한 class A, 보존 수소 핵류, 공통 전자/반응계 bulk velocity, `N=ln a`, `H_n>0`, `β=v_b/c`, `Γ=(1−β²)⁻¹/²`를 가정한다. proper-time 열 생성자 `R[s⁻¹]`는 비대각 비음수이고 `1ᵀR=0`이다. 상태 점유 `p`, 상태별 수소 핵당 전자 수 `y`에서

\[
\frac{dN}{d\tau_b}=\Gamma H_n,\qquad
\frac{dp}{dN}=\frac{R}{\Gamma H_n}p,\qquad x_e=y^Tp,
\qquad n_{H,rest}\Gamma a^3=\mathcal N_H.
\]

전자 proper density와 광자의 상대 flux를 결합하면

\[
\frac{d\kappa}{dN}=
\frac{\sigma_Tc\mathcal N_H}{H_n}e^{-3N}
(1-\beta\cdot\hat n)x_e.
\]

`σ_T[m²] c[m/s] N_H[m⁻³]/H_n[s⁻¹]`은 무차원이다. opacity의 명시적인 Γ는 소거되지만 `p`의 화학시계에는 Γ가 남는다. tilted 상황에서 `H→ΓH`를 모든 HYREC 항에 일괄 대입하면 광자 drift/escape까지 잘못 바뀔 수 있다. 고유시간의 속도만 변환하는 이번 반응망과 실제 원자·방사선 모형을 구별했다.

DP의 생성/소멸 연산자 표현은 주어진 양의 반응 generator를 조직화하는 수단이다. 임의 covariance 보간 모수에 Markov generator를 붙이는 근거는 되지 않는다. 이번 코드는 공급한 유한 선형 rate generator의 점유·지연 상태를 계산한다. 비선형 원자 반응망과 radiation feedback을 DP 명칭으로 완성했다고 간주하지 않는다.

### 4.2 구간 해와 tangent — implementation-verified

한 셀에서 `A=R/(ΓH_n)`를 고정하면 `P_h=exp(hA)`와

\[
w_h=\int_0^h e^{-3u}y^T e^{uA}du,
\quad P_{2h}=P_h^2,\quad w_{2h}=w_h+e^{-3h}w_hP_h
\]

로 점유·광학깊이를 함께 계산할 수 있다. 작은 셀의 block exponential에서 시작해 보존 열 정규화와 그 미분을 포함하여 합성한다. 초기 점유·R·y·H_n·β·광자 방향·N_H의 일곱 입력 tangent를 전달한다. 초기 hidden state와 지연 중간상태를 유지하며, 이후 셀에 재이온화 전이를 넣을 수 있다. 관측자 경계 `κ_M=0`에서 last-scattering bin 확률의 합은 `1−exp(−κ_0)`이다.

별도 proper-time DOP853와의 점유·깊이 오차는 `1.55×10⁻¹⁵,6.38×10⁻¹⁶`; 일곱 입력 동시 교란에 대한 다섯 출력의 중앙차분 최대 오차는 `3.13×10⁻¹²`였다. `10¹⁵ transitions/e-fold` 두 상태 극한도 별도 정확식과 비교했다. 고정 셀의 해와 미분은 정확한 행렬함수이며, 연속 이력을 midpoint로 고정하는 전체 근사는 해상도 수렴이 필요하다.

β=0에서 이 광학깊이를 정확 coherency propagator와 연결했다. 64셀의 `κ=13.63644092`에서 fused/sequential sky 차이는 `1.55×10⁻¹⁵`, tangent 중앙차분 오차는 `2.44×10⁻¹¹`였다. 방향별 tilted opacity를 공통 angular collision depth로 잘못 쓰지 않도록 nonzero β 또는 β-tangent 입력은 이 결합 fixture에서 명시적으로 거절한다.

### 4.3 사라진 원 입력의 실제 복구

BASS commit `ee298e24a6bac85bb11a81393f37499a8b0ddbe3`의 git object에서 H2248, 원 입력, source report를 복구했다. HYREC-2 commit `038dc8d71baed5c30a4fdd55576b97637ba5b879`에서 공식 원자표 다섯 개도 다운로드하여 과거 manifest의 SHA-256과 비교했다. 합계 8개·481,990 B가 정확히 일치했다. 사라진 live worktree 경로는 더 이상 입력 복구 blocker가 아니다. 기존 기준 commit 여섯 개의 object도 확인했다. [RESOURCE_RECOVERY.json](RESOURCE_RECOVERY.json)

원 H2248 생성기의 `N=ln[(1+1700)/(1+z_mean)]`, `(ln H)′=−(1+q)`를 읽어 해당 H가 normal-frame H임을 확인했다. 과거 proper-current runner는 밀도에 `Γ(1700)/Γ(z)`를 넣었지만 반응시계와 방사선 항의 H는 그대로 사용했다. 따라서 이력은 H+density 조건부 결과로 유지하며, 실제 tilted HYREC closure에는 chemistry clock, density, photon drift/escape, thermal expansion을 별도로 연결해야 한다. HYREC의 유효 원자·선 탈출 가정은 [Lee & Ali-Haïmoud, HYREC-2](https://arxiv.org/html/2007.14114v2)와 [Ali-Haïmoud & Hirata (2010)](https://arxiv.org/abs/1006.1355)를 재사용한다.

## 5. MZ: 물리시간 이외의 좌표와 움직이는 관측량

`dx/ds=A(s)x`가 실제로 정의된 선형 carrier를 생각한다. `V(s)`는 resolved basis, `W(s)>0`는 내적이고 rank는 일정하다. `L=(V*WV)⁻¹V*W`, `P=VL`, `Q=1−P`, `a=Lx`, `q=Qx`로 두면 직접 미분하여

\[
a'=(LAV-LV')a+(L'+LA)q,
\qquad q'=(QAV-QV')a+(Q'+QA)q.
\]

`D=Q′+QA`, `G_D(s,r)`를 그 전파자로 정의하면 기억과 초기 hidden 힘은

\[
K(s,r)=[L'(s)+L(s)A(s)]G_D(s,r)
[Q(r)A(r)V(r)-Q(r)V'(r)],
\]
\[
f_0(s)=[L'(s)+L(s)A(s)]G_D(s,s_0)q(s_0).
\]

이동 observable에서 생기는 항을 보존한다는 원리는 시간 의존 투영의 문헌과 일치한다([te Vrugt & Wittkowski, 2019](https://doi.org/10.1103/PhysRevE.99.062118)). 위의 유한 차원 식은 직접 미분으로 구성했고 `moving_projection.py`에 구현했다. full-rank positive Gram에 Cholesky를 쓰며 임의 jitter 또는 rank clipping은 없다. q의 n차원 보조계를 보존하는 reference 구현이지, 이미 계산 비용을 줄인 축약 solver라는 주장은 하지 않는다.

판별 예제는 `A=0`, `V=(cos s,sin s)ᵀ`, `W=I`, `x(0)=(1,0)`이다. 상태 x는 고정이어도 `a=cos s`이고 정확 kernel은 `K=−1`이다. 단순히 물리 generator가 0이라는 이유로 기억항을 지울 수 없다. Wolfram 계산은 `{{0,0},{−1},0}`을 반환하여 연립식 residual·kernel·해 residual을 확인했다. 실제 수치 kernel 오차는 `4.92×10⁻¹¹`; 복소 위상 사례는 `6.54×10⁻¹⁴`이다. 처음 실수인 배열이 나중의 복소 generator 성분을 버리던 IVP dtype을 수정했다.

비시간 변수 s에는 세 경우가 있다. 양의 단조 시계 변경이면 원 generator와 속도의 변환을 사용한다. scale·해상도 등의 독립적인 semigroup가 있으면 그 generator를 별도로 유도한다. covariance·cut·calibration 같은 모수 경로만 있으면 분포·관측량의 직접 미분을 계산한다. 세 번째 경우를 이름만 바꿔 동역학으로 취급하지 않는다. 프로젝트의 `x,Q,Pi,F,G_F`는 같은 carrier와 관측 사건에서 나오는 서로 의존하는 다섯 표현이며, 임의의 닫힌 5차원 Markov 상태는 아니다.

## 6. 6개 대주제·7개 교차 주제·60개 노드에 대한 실행 연결

| 대주제 | 이번 계산을 연결하는 곳 | 다음 과학적 조건 |
|---|---|---|
| P1: 다섯 함수적 표현 | covariance 응답, 이동 관측기저, 조건부 선택 | 같은 source law·sample identity에서 Q/Pi/F/G_F의 공동 pushforward |
| P2: CMB 저다중극·광자 | signed I/E/B/V, Thomson, 공급된 HYREC 이력 | Commander paired null, 실제 beam/mask, 기하·원자 feedback |
| P3: 방향별·깊이별 Hubble 관측 | SQ-CF4의 parent-pattern 우도와 훈련 전용 예측 | calibration 원자료, 방법 간 covariance, 독립 group holdout |
| P4: 상대 운동·frame | moving projection, photon/matter clock 구분 | 동시 source frame·radio/Gaia 계통오차·optical mapping |
| P5: Bianchi atlas | rank-nine collision, 강성 Fourier 전파, R100 signed modes | general-Lie/angular/screen transport, constraints, 모든 admissible family |
| P6: 같은 congruence 운동학 | tangent·투영·proper clock와 normal flux 경계 | 독립 normal-frame flux 및 Sachs/관측 연산자 |

| 교차 ID | 이번에 제공한 계산 | 유지되는 식별 의무 |
|---|---|---|
| PHY-01 | CF4 covariance·selection response와 moving projection | mask shear leakage와 physical expansion/flux의 분리 |
| PHY-02 | coherency moment·광학깊이·signed modes | 같은 frame의 photon PSD와 독립 Einstein flux |
| PHY-03 | REC/REI 반응 응답·상대 flux 시계 | radio count selection과 photon source frame 일치 |
| PHY-04 | 관측기저 및 내적 변화의 미분 | Gaia E/B2 optical map·AGN/AGIS systematics |
| PHY-05 | projection과 native collision | exceptional Lie rank와 독립 noisy flux covariance |
| PHY-06 | 다섯 실행 모듈 모두 | higher angular moments·회전하는 eigenframe·완전한 기하 수송 |
| PHY-07 | CF4 shared-field likelihood와 covariance tangent | radial support·radio selection·공동 covariance |

전체 node별 dependency·원 acceptance·과학 상태·실행 job·잔여 입력은 [NODE60_EXECUTION.md](NODE60_EXECUTION.md)와 [NODE60_EXECUTION.json](NODE60_EXECUTION.json)에 기록했다. 18개는 inherited scoped-completed, 42개는 과학적 조건이 남아 있다. 이 수치는 원래 42개의 canonical 연구노드와 개념적으로 다른 집계다. `program science --node SQ-CF4`의 exit 3은 유지된 과학 판정이며 실행 실패를 숨긴 성공으로 바꾸지 않았다.

## 7. 실제 수행한 이론 R1–R10 및 코딩 C1–C10

| 단계 | 수행 내용·직접 산출물 | 판정 |
|---|---|---|
| R1 연구 위치·계약 | 최신 branch/HEAD·R100·원60 DAG 확인, SQ-CF4 재진입, 사용자 native/push 지시 반영 | scope fixed |
| R2 근거·재사용 | 네 연구 원문, 4,073 항목 catalogue, 원 BASS/HYREC, Gaussian·MZ·DIRK 원전 | source identity checked |
| R3 주장·전제 | 실측 mark/통계 경로/생성자/물리 시계·frame·단위 구별 | explicit assumptions |
| R4 가설·표현 | error contrast vs GLS, positive-only vs full pattern, split vs joint implicit, fixed vs moving projector | alternatives computed |
| R5 구성적 유도 | predictive tangent, selected likelihood, rank-nine gain/source, proper-clock reward, moving MZ | derived |
| R6 독립 검증 | Jones 부호, Γ·단위, 보존 모드, 복소 위상, rank·degenerate limit | concrete defects repaired |
| R7 판별 검증 | 실제 8,885행 패턴, R100 요약, HYREC 200셀, dense/IVP/Wolfram 계산 | numerical evidence saved |
| R8 결과 판정 | 조건부 likelihood 민감도와 실제 물리 검출 구별, rate/input/native geometry 의무 분류 | no science promotion |
| R9 정식 결과·코딩 연결 | 별도 CF4·solver·chemistry 이론문서, API·단위·경계·validation 연결 | reusable computational contracts |
| R10 종료·재개 | 통합 보고서·node map·원표·원문·데이터 계획·인계 | durable research package |
| C1 목표·baseline | f8931fb 기준, 기존320 untracked 보존, 기존 owner checkout 사용 | baseline recorded |
| C2 식–데이터–코드 | 각 이론식→현재 R99/R100/BASS 함수·원표·단위 경로 추적 | mapped |
| C3 수치 설계 | error contrast Cholesky, stable moments/Schur, SDIRK2, positive reward semigroup | algorithms implemented |
| C4 실행 DAG·자원 | 독립 CF4/solver/chemistry 작업 분담, shared five jobs, exact recovery·bounded download | executable commands |
| C5 구현 | 추론·충돌·수송·화학·투영 모듈, 연결 driver와60-node runner | complete for declared modules |
| C6 구현 검증 | owner55 tests+26 subtests, 기존R100 validator21 tests, 취득도구 별도 경계 시험 | receipts and logs |
| C7 과학 검증 | Jones/구면모멘트/proper-time IVP/직접 mark 적분/독립 GLS 및 dtype 반례 | equation-to-code checked |
| C8 수치·재현성 | time/angular refinement, stiff modes, source hashes, 환경별 정확도·속도 비교 | measured with scope |
| C9 독립 검토 | fresh reviewer의 실제 반례·수정·owner byte identity 확인, 취득 경계 추가 검토 | review files |
| C10 판정·인계 | 명시 allowlist commit, 연구 branch push, 원격SHA 확인, local 분석·native 개발 인계 | publication receipt authority |

전체 목표의 현재 완료 기준은 위 명시된 부분문제의 수학·구현·실행과 재개 가능한 전달이다. 보정되지 않은 물리 likelihood, 미완성 all-family native atlas를 이 20단계 실행으로 완료했다고 표기하지 않는다. 새 strong no-go 정리는 제안하지 않았다.

## 8. 검증 기록과 잔여 blocker

실제 소유자 실행에서 다섯 조건부 job은 8.98초에 종료코드 0을 반환했다. 범위 지정 pytest는 **55 passed, 26 subtests passed**(57.41초), 기존 R100 validator는 **21 passed**와 `overall=true`를 기록했다. 일부 시험의 범위가 겹치므로 두 숫자를 독립 시험 수로 더하지 않는다. 취득도구 추가 시험은 **9 passed, 8 subtests passed**(0.76초)였고 default plan은 과학 payload 0 B로 완료됐다. 경계 초과 read를 고친 최종 파일의 실행·리뷰는 `ACQUISITION_EXECUTION_RECEIPT.json`·`ACQUISITION_REVIEW.md`에 있다. 실행 직후 tracked diff whitespace 검사는 통과했다. 최종 전체 staged 검사에서는 보존 원문 `prior_studies/DP_MZ_AUXILIARY.md`와 `PARAMETER_RESPONSE.md`의 기존 Markdown hard-break 공백 및 끝 빈 줄만 검출됐다. 두 파일의 원 SHA를 보존하고, 이 두 원문만 제외한 현재 변경의 staged 검사는 exit 0이었다. 전체 staged 검사를 무조건 PASS로 기록하지 않는다. `STAGING_VERIFICATION.json`에 이 범위와 결과를 남겼다. 전체 저장소의 모든 test를 실행한 것은 아니다.

기존 R100 validator가 재생성한 역사적 `VALIDATION.json`은 새 디렉터리에 `R100_REPLAY_VALIDATION.json`으로 보존하고 원래 파일을 baseline 바이트로 복원했다. `R100_REPLAY_PRESERVATION.json`에서 두 SHA를 확인할 수 있다. 원래 과학적 기록을 새 runtime 측정으로 덮어쓰지 않았다.

| blocker 종류 | 이번 처리 | 남은 최소 작업 |
|---|---|---|
| 입력 경로 상실 | BASS/HYREC8개 exact bytes 복구·원자표 실제 다운로드 | 입력은 현재 사용 가능; 물리적 적합성은 별도 검증 |
| 구현/수치 오류 | 편광 부호, near-collinear screen, stiff trace pivot, complex MZ, zero-axis continuity, CLI 계약 | 독립 리뷰의 해당 회귀는 닫힘 |
| 데이터 부족 D01–D02 | 공개 SDSS/6dF 재사용, full release-parent match pattern 실행, bounded acquisition | 원 영점·보정 covariance·전 방법 reject parent·독립 split |
| 데이터 부족 D03–D06 | 정확 URL·size·checksum·사용처·명령 준비 | Commander paired noise, AGIS/AGN, LoTSS weights/RMS, 독립 flux |
| 이론/물리 closure M09 | proper reaction clock·positive response·opacity 유도 | anisotropic radiation/atomic rate와 thermal/drift/escape의 분리 결합 |
| native 개발 M08/A03 | 실제 IQUV collision, strong-stiff Fourier transfer, harmonic 연결 | general Lie angular/screen advection, moving electron frame, Einstein/species feedback, all-family convergence |

다음 자료 여섯 개는 [DATA_ACQUISITION_PLAN.json](DATA_ACQUISITION_PLAN.json)에 정확 바이트·checksum 유무와 함께 준비했다. Commander paired noise 603,987,840 B, SDSS randoms 284,000,071 B, SDSS mocks 10,643,218,721 B, 6dF reconstruction mocks 17,344,070,928 B, LoTSS 355/1078 tar 각각 6,025,820,160/4,507,238,400 B다. LoTSS의 과거 HTTP 200/202는 현재 가용성의 확인이 아니다. 실행 시 HEAD를 확인하고 202면 보류한다. 큰 자료는 이번에 전송하지 않았다. 공급자 checksum 없는 자료의 계산된 local SHA는 원본 독립 인증과 구별한다.

## 9. 로컬에서 이어갈 순서

[HANDOFF_LOCAL_AGENT_KO.md](HANDOFF_LOCAL_AGENT_KO.md)가 실행 지시문이다. 기존 checkout에서 SQ-CF4 source qualification부터 시작하여 선택/영점 불확실성 및 group holdout, Commander matched pair, mock·radio·Gaia 분석을 우선한다. 현재 제공된 모듈을 다시 쓰거나 처음부터 카탈로그를 재감사하지 않는다.

native 의무는 외부 solver를 기다리는 상태로 되돌리지 않는다. R100의 실제 Lie connection과 새 rank-nine 충돌을 결합하는 angular/screen transport를 구현하고, 일반 Lie advection에서 대각 inverse를 가정할 수 없으므로 sparse/structured base solve와 low-rank correction을 사용한다. 이어 moving electron-frame aberration·frequency·screen 변환, 실제 REC/REI Jacobian, Einstein–Boltzmann 4-force 및 제약 보존을 결합한다. I–IX/exceptional branch, signed all-m T/E/B/V, k·ell·시간 수렴과 독립 FLRW 한계를 검증해야 atlas가 완료된다. 관련 입력/방정식이 열려 있는 경우 정확히 그 항을 구하고 나머지 독립 코드 작업은 계속한다.

### 핵심 파일

- 실행 진입점: `scripts/r101/program.py`, `scripts/r101/acquire.py`, `scripts/r101/recover_legacy_resources.py`.
- CF4: `htt/htt/htt/infer/cf4_predictive_response.py`.
- native: `htt/bass/collision/coherency.py`, `electron_frame.py`, `htt/bass/transport/stokes_fourier.py`.
- 물질·관측 응답: `htt/bass/recombination/clocked_chemistry.py`, `htt/bass/kinetic/moving_projection.py`, `scripts/r101/chemistry_coherency.py`.
- 검토: [INDEPENDENT_REVIEW.md](INDEPENDENT_REVIEW.md), [ACQUISITION_REVIEW.md](ACQUISITION_REVIEW.md).
- 실제 실행: [OWNER_RUN_RECEIPT.json](OWNER_RUN_RECEIPT.json), [EXECUTION_RECEIPT.json](EXECUTION_RECEIPT.json), 각 JSON·log.
