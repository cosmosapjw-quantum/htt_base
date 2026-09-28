---
title: "HTT 연구 저장소 독립 분석"
subtitle: "후속 심사: 물리 커널·tensorized MES·통합 통계·역사적 주장"
date: "2026년 9월 8일"
lang: ko-KR
fontsize: 10pt
geometry: [a4paper, margin=22mm]
colorlinks: true
urlcolor: blue
toc: true
toc-depth: 1
---

# 판정과 범위

**확인한 HTT 계통에는 독립적인 수학적 성과와 재사용 가능한 물리·관측 코드가 있다. 그러나 그 성과를 모두 연결한 우주론적 공동 추론이나 일반 Bianchi solver의 완성은 현재 확보한 증거로 입증되지 않는다.** 가장 유망한 부분은 Q/O의 proper-rotation 표현과 수축 fibre, 조건부 tensorized MES의 식별집합, 일부 Thomson 커널 및 실제 Planck·ACT 분석 경로다. 가장 중요한 결함은 관측 전방응답 없이 물리적 기여도를 부여하는 논증, 선택·상관을 보존하지 않는 통계 경로, 그리고 정의역을 넘어선 구간 계산이다.

이 판정은 저장소의 claim ceiling, PASS, exact, diagnostic, legacy 문구를 기준으로 삼지 않는다. 유효한 제한 모형은 그 수학적 범위에서 인정한다. 반대로 조건부라고 표시한 Bayes factor도 계산 근거가 틀리면 인정하지 않는다. 새 코드가 존재하는 것과 구형 분석이 그 코드로 교체된 것은 구분한다.

**이 문서는 전수조사의 후속 중간보고서다. 사용자가 요청한 모든 역사적 코드·JSON·문서의 전수 정독은 아직 완료하지 못했다.** 아래 분모와 읽기 기록을 숨기지 않는다. 자료 부재와 미열람을 혼동하지 않으며, 읽지 않은 경로를 유효 또는 무효라고 판정하지 않는다.

| 조사 항목 | 확보 상태 | 의미 |
|---|---:|---|
| 기존 브랜치 census | 182개 | 보존된 접근 가능 ref 집합 |
| 기존 reachable commit graph | 2,061개 | 당시 missing parent 0개 |
| 기존 브랜치 끝점 고유 blob | 8,630개 | 모든 역사적 blob의 분모는 아님 |
| 복구된 누적 전문 읽기 | 161개 고유 blob | 전 단계의 읽기 ledger에 근거 |
| 이번 추가 전문 읽기 | 1개 고유 blob | `egs3_gf_interval.py`, 새 취득·해시 확인 |
| 누적 전문 읽기 기록 | 162개 고유 blob | 이번 재검토의 중복 읽기는 가산하지 않음 |
| 그중 끝점 집합에 속한 blob | 151개 | 8,630개의 약 1.75% |
| 모든 역사적 파일 정독 | 미완료 | 중간 커밋에서만 존재한 내용의 전체 분모도 미확정 |

기존 v2 읽기 기록은 54개 신규 고유 blob, 약 1.50 MB의 전문 읽기를 포함한다. 이번에는 그중 핵심 코드를 다시 읽고 두 독립 검토로 확인했다. 기존 ledger에 적힌 전문 읽기를 이번 turn에서 새로 전부 수행했다고 표현하지 않는다. 역사적 tree 취득 재개 기록도 남아 있지만 미완결이므로 전체 역사 파일 집합을 확보했다고 하지 않는다.

주 기준은 사용자가 지정한 handoff의 고정 commit `5702024e06eff4979087f07f86ee7131d13961ac`이다. 이번 GitHub 연결에서 기본 브랜치는 여전히 `research/pr04-multicomponent`였고, handoff의 MIO 파일은 보존된 blob과 일치했다. 모든 live ref의 새 census를 수행한 것은 아니다. 웹에서 GitHub 페이지 직접 열기는 실패했으나 GitHub 연결은 작동했다. 원논문 검색·열람은 웹으로 수행했다. [고정 handoff](https://github.com/cosmosapjw-quantum/htt_base/tree/5702024e06eff4979087f07f86ee7131d13961ac)

과학 코드, CAS, 수치 적분, 관측 데이터 분석은 실행하지 않았다. 아래 반례는 직접 유도이며, 저장된 관측 수치는 기존 결과 기록이다. 코드·원자료의 실행 검증은 사용자가 지정한 워크스테이션 Local Codex에 남는다. 문서 제작과 파일 무결성 검사는 과학 실행과 분리했다.

# 연구사의 독립 해석

복구된 이력 조사에서 첫 reachable commit은 2026년 4월 18일의 `b16f145380683845eb4ea9eb166fb8fd6f081161`이다. 그 안에 4월 12일 보고서도 있으므로 이 날짜를 연구 자체의 출발일로 단정할 수는 없다. 초기 Rust BASS에서 저차 CMB와 departure 지표를 연결하고, 이후 Python 물리 커널·관측 분석·회전 불변량·tensorized MES로 확장한 흐름은 일관된다. [첫 reachable commit](https://github.com/cosmosapjw-quantum/htt_base/commit/b16f145380683845eb4ea9eb166fb8fd6f081161)

| 계통 | 확인된 진전 | 아직 분리해야 할 주장 |
|---|---|---|
| 초기 Rust/BASS | 배경·계층·추론 구조와 baseline 기록 | 테스트 개수와 물리 정확성, likelihood 합과 evidence |
| 후기 Python BASS | PSTF 충돌·screen 적분·배경 RHS | 커널 유효성과 전체 자기일관적 동역학 |
| MIO | departure·깊이·공동 정렬의 표현 | 지표 정의와 검출 유의성 |
| obsstat | Planck·ACT·CF4 등 실제 분석 경로 | downstream mock과 raw-data 응답 검증 |
| tensorized MES | Q/O 정보 보존과 부분 식별의 명세 | 관측 텐서와 물리 텐서 사이의 응답 |

low-ell morphology, local boost와 global tilt, 운동학적 경계, 여러 깊이의 자료를 연결한다는 동기는 유지된다. 다만 연구 목표가 이어졌다고 해서 모든 수식·결과의 증거도 이어지는 것은 아니다. 오래된 source와 새 source가 병존하므로 논문별 실제 호출 경로를 지정해야 한다.

이 프로젝트의 객관적 성숙도를 단일 백분율로 표현하는 것은 부적절하다. 정리의 정확성, solver의 유효범위, 데이터 우도의 타당성, 독창성은 서로 다른 평가축이다. 현재 정독률도 과학적 완성도가 아니라 조사 범위의 척도다.

# 새로 확인한 MIO·통합 우도의 결함

## 1. 같은 처리 규칙을 적용했다고 같은 null 법칙이 되는 것은 아니다

`mio_joint_measure.py`의 `reference_scale` 분기는 각 행·성분에 독립 Gaussian 난수를 만든다. MAD 기반 scale 일치 검사는 주변 척도만 검사하며 cross-component covariance, cross-row covariance, selection, shared sky를 검사하지 않는다. 이는 코드에 지정된 독립 Gaussian 모형에서는 사용할 수 있지만, 일반적인 물리 departure table의 calibrated null을 보장하지 않는다. [고정 MIO 소스](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/src/common/mio_joint_measure.py)

직접 반례를 보자. 각 행에서 두 성분의 주변분포는 모두 $N(0,1)$이지만 실제 null은 $(X_{i1},X_{i2})=(Z_i,Z_i)$라고 하자. 단위 weight, raw·unpaired 정책에서

$$F^2=\frac1n\sum_i(X_{i1}^2+X_{i2}^2).$$

실제 null에서는 $F^2=2\chi_n^2/n$이므로 평균 2, 분산 $8/n$이다. 코드의 독립 Gaussian null에서는 $F^2=\chi_{2n}^2/n$이므로 평균 2, 분산 $4/n$이다. 두 성분의 주변 MAD는 같아도 검정 분포는 다르다. 이 반례는 새 모의실험이 아니라 Gaussian 제곱합의 해석적 계산이다. 실제 관측 p-value의 오차량은 원자료의 공동법칙을 확인하기 전에는 알 수 없다.

또한 `Sigma2`, `W2`처럼 비음수 물리 성분을 raw 모드에서 Gaussian 부호 대칭 변수로 대체하는 것은 그 자체로 물리 null이 아니다. signed residual이나 정규화 estimator를 입력한다면 그것을 별도 estimand로 정의해야 한다. row sign-flip도 행 단위의 부호 불변성이라는 추가 귀무가설이 필요하다.

finite-null 식 $p=(1+\#\{T_i\ge T_0\})/(N+1)$은 score의 교환가능성에 근거한다. 같은 weights·pairing·depth 코드를 썼다는 사실은 필요할 수 있지만 충분하지 않다. 이 원리는 기존 randomization 통계학과 일치한다. [Randomization Inference: Theory and Applications](https://arxiv.org/abs/2406.09521)

## 2. pair의 방향이 배열 순서에 의존한다

`_apply_pairing`은 같은 pair ID의 첫 행에서 둘째 행을 뺀다. A/B 또는 before/after role은 입력에 없다. 따라서 한 pair의 두 행 순서를 바꾸면 $\Pi$가 바뀐다. 여러 pair 중 하나만 뒤집으면 전체 절댓값도 달라질 수 있다. 예컨대 두 signed difference가 1, 2이면 평균은 $3/2$이고, 첫 pair만 뒤집으면 $1/2$이다.

$F$는 각 pair 전체 부호 반전에 불변이지만 $\Pi$는 그렇지 않다. 그러므로 paired $\Pi$의 행 순열 불변성을 주장하려면 role label을 함께 보존하고 차분 방향을 그 label에서 정해야 한다. 통계적 pairing과 물리적 contrast의 방향은 별도 정보다. 같은 소스의 `permutation_invariant`가 랜덤하게 검사하는 것만으로 정의가 정정되지는 않는다.

## 3. 주변 구간으로 얻는 범위와 공동집합의 정확한 범위

`feasible_range_GF`는 성분별 interval의 Cartesian product에서 $\sqrt{\sum_jw_jx_j^2}$를 최소·최대화한다. 이 상자에 대해서는 공식이 맞다. 그러나 일반적인 공동 identified set에 대해서는 정확한 attainable range가 아니라 외부 포락이다.

정확한 반례는

$$\Theta=\{(x_1,x_2):x_1,x_2\ge0,\ x_1+x_2=1\},\quad w_1=w_2=1.$$

각 주변 구간은 $[0,1]$이므로 코드의 상자 계산은 $[0,\sqrt2]$이다. 실제 공동집합에서는

$$x_1^2+x_2^2=2(x_1-1/2)^2+1/2,$$

따라서 범위는 $[1/\sqrt2,1]$이다. 이를 정확한 공동범위라고 쓰면 없는 상태를 허용한다. 외부 포락으로 보고하면 유효한 보수적 계산이다. 이 함수의 `GF`는 아래 obsstat의 ratio형 $G_F$와 정의가 다르므로 이름만으로 연결하지 않는다.

## 4. bulk-flow 선택 가중치는 정밀도 가중치로 구현되어 있다

`bulkflow_likelihood.py`는

$$\log L(\mathbf V)=-\frac12\sum_i\left[\frac{w_i(u_i-\hat n_i\cdot\mathbf V)^2}{\sigma_{i,\rm eff}^2}+\log\frac{2\pi\sigma_{i,\rm eff}^2}{w_i}\right]$$

를 구현한다. 이는 $u_i\mid\mathbf V\sim N(\hat n_i\cdot\mathbf V,\sigma_{i,\rm eff}^2/w_i)$라는 정규화 Gaussian 우도다. 그러나 문서의 “같은 오차의 독립 측정 $w_i$개”와는 정규화가 다르며, inverse-selection weighting이 실제로 오차를 줄인다는 뜻도 아니다. [bulk-flow 소스](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/src/common/bulkflow_likelihood.py)

고정 오차·고정 weight에서 posterior의 모수 의존 부분은 반복 측정 또는 power likelihood와 같을 수 있다. 이 제한된 등가성은 일반 evidence, 가변 분산, selection parameter 추론으로 확장되지 않는다. 검출된 자료의 분포를 쓰려면, 예를 들어 관측값 $d$에 의존하는 selection $S(d)$와 고정 표본 수의 독립 표본 가정 아래

$$p(d\mid\theta,\mathrm{selected})=\frac{S(d)p(d\mid\theta)}{\alpha(\theta)},\qquad\alpha(\theta)=\int S(d)p(d\mid\theta)\,dd$$

가 필요하다. latent-variable selection이면 그 적분을 먼저 포함해야 하고, 표본 수도 추론하면 count likelihood를 추가한다. 천체 population inference에서 이 구조가 명시적으로 유도되어 있다. [Mandel, Farr & Gair](https://arxiv.org/abs/1809.02063)

또한 “active source 4개 이상”은 3차원 방향 design의 full rank를 보장하지 않는다. 네 방향이 모두 평행한 반례가 있다. bounded prior 때문에 posterior가 proper일 수는 있지만 관측 정보에 의한 3차원 식별과는 다르다.

## 5. 통합 survey 계약은 아직 통합 likelihood가 아니다

`joint_survey_hierarchy.py`는 covariance·selection·calibration·shared LSS·heldout 상태 문자열을 검사한다. 실제 covariance matrix, latent field, selection normalizer를 계산하지 않는다. 모든 필드가 `bound`라고 표시되어도 조건부 독립성이 증명되는 것은 아니다. [joint contract 소스](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/htt/htt/infer/joint_survey_hierarchy.py)

이것은 유용한 입력 계약이지만 과학적 전방법칙의 대체물이 아니다. 다중 관측자료를 최대한 활용하려면

$$p(D\mid\theta)=\int p(\lambda\mid\theta)\,p(D_1,\ldots,D_K\mid\theta,\lambda)\,d\lambda$$

에서 shared field·calibration $\lambda$를 먼저 지정해야 한다. 그 조건에서 실제 잔차가 독립일 때만 내부 joint density를 곱으로 쓸 수 있다. 공통 데이터의 재가공 제품에는 이 조건이 특히 중요하다.

# 새 obsstat 구간 반례

이번에 전문을 새로 취득한 `htt/obsstat/egs3_gf_interval.py`의 Git blob은 `f0827837db208c5dada3120e3aeac349b2f910b6`, 크기는 16,935 bytes다. base64 원문을 복원하여 Git blob을 확인했다. [고정 소스](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/obsstat/egs3_gf_interval.py)

## 양수 분모만으로 numerator/denominator 극값 조합을 고정할 수 없다

함수는 shared box의 각 corner에서

$$\frac{n_{\rm lo}+c_Ns}{d_{\rm hi}+c_Ds},\qquad\frac{n_{\rm hi}+c_Ns}{d_{\rm lo}+c_Ds}$$

만 계산한다. 그러나 $D>0$에서도

$$\frac{\partial(N/D)}{\partial D}=-\frac{N}{D^2}$$

의 부호는 $N$에 의존한다. 입력 함수는 분자의 비음수성을 강제하지 않는다.

| 입력 | 실제 범위 | 소스 산식의 결과 |
|---|---|---|
| $N=-1$, $D\in[1,2]$, shared $s\in[0,0]$, 두 계수 0 | $[-1,-1/2]$ | float helper는 $(-1/2,-1)$로 역전 |
| $N\in[-2,-1]$, $D\in[1,3]$, 같은 shared 입력 | $[-2,-1/3]$ | 두 corner 값만 쓰는 exact helper는 $[-1,-2/3]$ |

두 번째 반례는 Fraction 연산이어도 잘못된 극값 후보를 고를 수 있음을 보여 준다. 이것은 반올림 문제가 아니라 정의역·알고리즘 문제다. 위 숫자는 코드 실행 결과가 아니라 소스 식에 직접 대입한 결과다.

수정식은 각 shared corner에서 reachable numerator·denominator의 네 endpoint 조합을 전부 평가하는 것이다. 분모가 양수인 compact box에서는 linear-fractional 함수가 각 좌표에 대해 단조 또는 상수이므로 이 후보 집합으로 극값을 얻는다. 또는 물리적 적용을 $N\ge0$로 제한하고 전체 feasible set에서 그 조건을 입증·검사할 수 있다. 분모가 0에 닿거나 부호가 바뀌는 경우에는 별도 unbounded/disconnected 판정이 필요하다.

## “공유 nuisance가 있으면 반드시 더 좁다”도 조건부다

`gf_strictness_criterion`은 비퇴화 성분의 $c_Nc_D>0$을 양쪽 strict narrowing의 조건으로 사용한다. 하지만

$$N=-2+s,\quad D=2+s,\quad 0\le s\le1$$

이면

$$\frac{d}{ds}\frac{-2+s}{2+s}=\frac4{(2+s)^2}>0,$$

공동 범위는 $[-1,-1/3]$이다. 독립 주변 구간 $N\in[-2,-1]$, $D\in[2,3]$의 quotient도 정확히 같다. 두 계수의 곱은 양수지만 strict하지 않다. 분자가 양수인 intended domain에 맞춘 정리라면 그 조건을 명시해야 한다.

공유 nuisance를 함께 최적화하려는 연구 방향은 옳다. 그러나 이 반례 때문에 모든 기존 수치 예제가 틀렸다는 결론은 나오지 않는다. 그 예제들이 양수 numerator 영역에 있었는지와 실제 caller를 확인해야 한다. 필요한 Local 검증은 signed·zero-crossing 입력, 네 endpoint 비교, 물리 입력의 정의역 확인이다.

# BASS 충돌·배경 계통의 독립 판정

## 유효한 Thomson kernel과 잘못된 no-polarization 경로가 공존한다

정지한 전자에 대한 무편광 Thomson angular kernel은

$$K(\mu)=\frac{3}{16\pi}(1+\mu^2)=\frac1{4\pi}\left[1+\frac12P_2(\mu)\right].$$

따라서 quadrupole gain eigenvalue는 $1/10$이고, 양의 산란률 $\Gamma_T$에서 $C_2=-(9/10)\Gamma_TF_2$이다. `src/collision/thomson.rs`의 no-pol 경로는 polarization source 전체를 0으로 주어 $-\Gamma_TF_2$를 반환한다. 편광 변수를 추적하지 않는 것과 온도 quadrupole self-gain을 제거하는 것은 다르다. [Rust Thomson](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/src/collision/thomson.rs)

반면 Python PSTF·polarization 계통에는, 그 packed convention에서,

$$C=-\Gamma_T\begin{pmatrix}9/10&\sqrt6/10\\\sqrt6/10&2/5\end{pmatrix}\binom{\Pi_2}{E_2}$$

가 구현되어 있다. 감쇠 고유값은 $1,3/10$이며 monopole 보존·고차 감쇠와 일관된다. 따라서 전체 collision 코드를 skeleton 또는 전부 실패라고 평가하면 틀리다. 이 판정은 coefficient의 정적 검토이며 SH 정규화·consumer·수렴까지 실행 검증한 것은 아니다. [Python PSTF](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/collision/thomson_pstf.py)

같은 Rust 파일의 nonlinear quadrupole helper는 scalar $\langle\Theta^2\rangle$에 $6/50$을 곱한다. 등방장 $\Theta=A$에서 실제 STF quadrupole은 0인데 helper는 $3A^2/25$를 준다. 필요한 것은 $[\Theta^2]_{2m}$의 Gaunt projection이다. binomial coefficient 6이 맞다는 사실은 angular projection의 정확성을 보장하지 않는다.

## 유한 tilt의 collision은 방향별 rate 변경만으로 완성되지 않는다

`electron_frame.py`에는 screen 회전과 $I,Q,U$ Mueller 적분이 실제 구현되어 있다. 다만 읽은 API는 $V$를 포함하지 않아 이름의 full Stokes보다 범위가 좁다. native integrator의 해당 consumer는 같은 sphere에서 tower를 복원·산란·재투영하고 tilt를 방향별 opacity에 반영한다. 그 입력이 normal-frame tower라면 electron-frame 변환과 역변환이 추가로 필요하다. [electron frame](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/collision/electron_frame.py), [native consumer](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/hierarchy/ver2_native_integrator.py)

개념적으로 $C_n=\mathcal B^{-1}C_e[\mathcal B f]$에 frequency·brightness·aberration·screen·rate 변환을 일관되게 포함해야 한다. 이미 electron-frame state라는 consumer 계약이면 그 전제를 검증할 수 있다. 별도 `tilted_thomson_layer_b.py`에는 forward/collision/backward 구조가 있으므로 저장소 전체에 boost가 없다는 주장은 하지 않는다. [별도 Layer B](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/collision/tilted_thomson_layer_b.py)

## 배경 ODE와 물질 closure의 연결

`background/evolution.py`의 ODE 상태는 $H$와 shear 5성분이다. 물질은 `state_at_scale_factor(a)`로 공급되고 geometry는 초기 객체가 전달된다. fixed-velocity tilted closure는 일반적인 자기일관적 tilted radiation 해가 아니다. [배경 integrator](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/bass/background/evolution.py)

에너지밀도 단위의 $\rho,\pi^{ab}$와 proper time을 쓰는 homogeneous orthogonal radiation sector에서

$$\dot\rho+4H\rho+\sigma_{ab}\pi^{ab}=0$$

이므로 일반적인 shear feedback을 처리하려면 radiation 상태와 동적 배경의 연결이 필요하다. 그 RHS·packing·diagnostics는 재사용할 수 있다. 외부의 적절한 closure를 사용하는 제한 사례까지 기각하지 않는다.

# tensorized MES의 성과와 관측 연결

## Q/O의 수축 fibre와 안정성은 살릴 수 있는 결과다

고정된 Euclidean frame에서 unit Frobenius norm의 $q\in\mathrm{STF}_2$, $o\in\mathrm{STF}_3$를 쓰고 $v=o:q$로 두자. 이 $v$는 무차원 contraction vector이며 물리 속도가 아니다. 기존 노트의

$$L_qo=o:q,\quad M_q=I+\frac65q^2,\quad L_qL_q^*=\frac13M_q,\quad R_q=\mathcal B_qM_q^{-1}$$

는 명시된 full-contraction convention에서 일관된다. $\ker L_q$의 차원은 4이며

$$\eta=3v^TM_q^{-1}v,\qquad\mathcal F_q(v)=R_qv+\sqrt{1-\eta}\,S(\ker L_q)$$

이다. $\eta<1$이면 affine 4차원 공간 안의 3-sphere, $\eta=1$이면 singleton, $\eta>1$이면 empty다. contraction과 norm만으로 octupole 전체가 결정되지 않는 양을 정확히 나타낸다. [fibre 노트](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/docs/research_reports/notes/QO_CONTRACTION_FIBRE_GEOMETRY_20260907.md)

같은 고정 $q$에서 두 nonempty fibre의 Hausdorff 거리는

$$d_H^2=3(v-w)^TM_q^{-1}(v-w)+\left(\sqrt{1-\eta_v}-\sqrt{1-\eta_w}\right)^2.$$

경계 $\eta_{v_*}=1$에서 $v_t=(1-t)v_*$를 택하면 $d_H=\sqrt{2t}$이다. 따라서 이 집합 복원의 경계 민감도는 sharp $1/2$-Hölder이며 균일 Lipschitz가 아니다. 선형 right inverse의 conditioning과 sphere constraint의 경계 민감도를 분리한 점에 의미가 있다. 단, noisy $q$까지 함께 변하는 문제 또는 전체 invariant packet 복원의 안정성을 이 식이 대신하지는 않는다.

cyclic Krylov packet의 proper-rotation 궤도 분리도 유효한 제한 정리다. 그러나 multipole vector와 multipole invariant 연구는 이미 존재한다. 신규성은 텐서 표현 자체가 아니라 구체적 separating packet, singular-domain 처리, 잔여 fibre, 관측 오차·물리 응답과의 결합에서 입증해야 한다. [Copi, Huterer & Starkman](https://arxiv.org/abs/astro-ph/0310511), [Land & Magueijo](https://arxiv.org/abs/astro-ph/0407081)

## 최신 보고서의 공동식별 구조는 이전 약점을 일부 고친다

최신 integrated Report A는

$$\Theta(y;\eta)=D_\eta\cap B_{\rm MES}(y;\eta)\cap\mathcal R_\eta^{-1}(C_y(\eta))$$

를 명시하고, exact affine fibre와 noisy compatibility region을 구분한다. 같은 자료에서 만든 MES anchor를 독립 관측으로 곱하지 말아야 한다는 점도 분명히 적혀 있다. 이는 구형 명세에 대한 실질적 개선이다. [integrated Report A](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/docs/research_reports/final_candidate_20260907/HTT_REPORT_A_EVIDENCE_INTEGRATED_R3.md)

이 구조를 최대한 활용하는 관측 분석의 대상은 단일 $f_B$가 아니라 다음 세 층이다.

1. 측정된 $Q,O$ 및 필요시 외부 벡터의 공동 관측분포. mask·calibration·frame·단위 변환을 포함한다.
2. 물리 상태 $x$에서 이 관측량으로 가는 response $\mathcal R_\eta$. local boost와 global tilt의 시간·공간 역할을 구별한다.
3. 공동집합 위의 물리 functional $g(x)$의 image 또는 support. 식별 안 되는 방향은 남겨 둔다.

단순 sector ball $\prod_j\{\|x_j\|\le R_j\}$의 gauge는 $\max_j\|x_j\|/R_j$이다. 이것은 sector 간 signed cancellation을 막지만 방향·handedness를 복원하지는 않는다. 반대로 full Q/O morphology가 있다고 해서 물리 shear·vorticity가 자동 식별되는 것도 아니다.

MES의 물리적 해석에는 congruence, perturbative order, observer-domain 및 multipole derivative 가정이 남는다. 한 지점의 작은 CMB anisotropy만으로 일반 spacetime의 작은 anisotropy를 무조건 결론낼 수 없다. 원 MES와 almost-isotropy 반례를 함께 기준으로 삼아야 한다. [MES 1995](https://arxiv.org/abs/astro-ph/9501016), [Nilsson et al. 1999](https://arxiv.org/abs/astro-ph/9904252)

따라서 tensorized MES는 현재 **관측 표현 + 조건부 물리 제약 + 부분 식별의 구조**로 평가하는 것이 정확하다. $\mathcal R_\eta$, $C_y$, random anchor의 공동법칙이 실제 지정되기 전에는 완성된 관측 likelihood라고 부를 수 없다.

# 오래된 원고의 정량적 주장 재심사

## posterior 표본이 양수라는 사실은 Bayes factor의 하한이 아니다

`ch07_results.tex`는 finite posterior 표본이 모두 $F>0$이라는 사실로 Savage–Dickey Bayes factor $>5\times10^4$를 제시한다. 연속분포에서는 finite sample이 정확히 0에 오지 않는 것이 정상이다. $F\sim\mathrm{Uniform}(0,1)$인 prior와 posterior가 동일한 예에서도 표본은 거의 확실히 모두 양수지만 null에서 density ratio는 1이다. [원고 ch07](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/docs/manuscript/ch07_results.tex)

Savage–Dickey에는 호환되는 nested model·prior 및 null에서 prior/posterior density가 필요하다. 경계 null이면 해당 정칙성을 추가로 정해야 한다. 논문에 legacy 또는 conditional 표기를 붙여도 이 추론상의 결손은 사라지지 않는다. 별도의 올바른 evidence 실행이 있다면 그 증거를 연결해야 한다.

후기 `coherent_evidence.py`에는 정규화 Gaussian prior를 적분한 정확한 evidence와 thermodynamic/bridge sampling 경로가 실제 존재한다. $\mathrm{Cov}(y)=\sigma^2I+\tau^2\mathbf1\mathbf1^T$라는 conjugate 예제는 올바른 benchmark 구조다. 이는 초기 evidence 결함을 수정할 유용한 자산이지만 우주론 likelihood의 타당성을 입증하는 실자료 결과는 아니다. [후기 evidence benchmark](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/src/common/coherent_evidence.py)

## neutrino의 큰 물질 quadrupole과 관측 CMB 기여율은 다르다

`ch05_teff_corrections.tex`는 $N_2/F_2\simeq\dot\tau/H$와 density-weighted 제곱합을 이용하여 neutrino의 CMB quadrupole 기여율 약 98.4%를 해석한다. 그러나 그 유도는 collisionless neutrino의 quasi-steady 상태와 $\Gamma_2^{(\nu)}\sim H$를 추가 가정한다. 임의 초기조건·shear history에 대한 일반 해석은 아니다. conformal opacity라면 비교할 expansion rate도 conformal $\mathcal H$로 맞춰야 한다. [원고 ch05](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/docs/manuscript/ch05_teff_corrections.tex)

관측 photon multipole을 $a^{\gamma}_{2m}=\sum_s a^{\gamma\leftarrow s}_{2m}$로 분해한다면

$$\sum_m|a^{\gamma}_{2m}|^2=\sum_{s,t,m}a^{\gamma\leftarrow s}_{2m}\,a^{\gamma\leftarrow t*}_{2m}.$$

species anisotropic stress에서 metric을 거쳐 photon으로 가는 transfer와 cross terms가 필요하다. 단순한 $\rho_s^2N_{2,s}^2$의 합은 이를 제공하지 않는다. 이 식을 물질 sector budget으로 한정할 수는 있지만 관측 CMB power의 기여율로 사용하려면 새로운 response 근거가 필요하다.

또한 collisionless spectral ansatz가 유지되는 것과 finite angular hierarchy가 닫히는 것은 별개다. free streaming이라는 이유만으로 angular closure의 exactness를 결론낼 수 없다.

## TAM과 nonlinear observable 변환의 비교

같은 원고는 선형 TAM transport의 인접 multipole 결합과 $T^4$의 quadratic harmonic product를 비교하여 고차에서 두 형식이 구조적으로 불일치한다고 해석한다. 그러나 $T\mapsto T^4$를 같은 하늘에 적용하면 어떤 표현에서도 Gaunt product가 생긴다. 표현의 차이를 물리 차이로 판정하려면 같은 변수·관측량·섭동 차수·truncation에서 비교해야 한다. 이 지점은 계수 하나를 맞추는 수치 검사만으로 해소되지 않는 논증 문제다.

# 기존 관측 결과와 자산의 재사용

아래는 **보존된 제1권의 JSON·CSV 판독 결과**다. 이번 원자료 재분석이나 runtime 재현 결과가 아니다. 강한 물리 결론의 근거로 승격하지 않고 후속 조사의 출발점으로 유지한다.

| 자료 계통 | 보존된 결과·자산 | 독립 해석과 최소 보완 |
|---|---|---|
| Planck PR3 | Generic12 $133/301$, MES10 $98/301$ 등 ablation | 같은 관측 p의 크기로 방법 우열을 정하지 말고 matched alternatives의 power·coverage 비교 |
| Planck PR150 | 999 CMB와 300 noise 재사용 | 행 수를 독립 null 수로 간주하지 않기 |
| ACT | in-band modulation·row별 covariance·주입 경로 | reconstructed-alm 주입과 raw response 검증 구분 |
| CF4 | 그룹·cell 압축, MV·깊이·curl 코드 | 압축 $A$와 covariance $ACA^T$ 및 raw injection 일치 |
| DESI | random catalog·cap 정규화·mock별 nuisance refit | footprint moment와 물리 dipole response 구분 |
| JWST 거리 | host identity·중복 구분과 일관성 비교 | 공통 calibration·selection·이분산의 공동법칙 |
| CatWISE·radio | 방향 요약 및 통합 목적의 계약 | 실제 catalog likelihood와 shared LSS를 추가 확인 |

[Planck ablation](https://github.com/cosmosapjw-quantum/htt_base/blob/d62c24887a4b91ab063085d5785b3cf18e0e36b5/docs/generated/planck_mes_first_paper/family_ablation_table.csv), [PR150 기록](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/docs/generated/pr150_e2e_pooled_rank.json), [CF4 역사적 카드](https://github.com/cosmosapjw-quantum/htt_base/blob/f94e409c85d4c9c5f1dbd9081c34e798b35b599c/docs/generated/cf4_mv_bulkflow_card.json), [DESI mock 경로](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/obsstat/desi_exact_selection_mock.py)

새 데이터를 모두 하나의 scalar에 합칠 필요는 없다. 우선 같은 latent physical state와 관측자 frame에 연결되는 자료만 joint model로 묶고, 나머지는 posterior predictive 또는 독립적인 model check로 남기는 편이 과학적이다. HSC·KiDS·2MRS 등 모든 소유 데이터의 가용성과 adapter를 이번에 전수 확인한 것은 아니다. 외부 코드 보유와 실제 검증된 consumer 연결도 구분한다.

# 잠재력과 작업 우선순위

가장 명확한 학술 기여는 새 이상현상 검출을 먼저 선언하는 데 있지 않다. **저차 하늘의 형태를 어떤 요약이 보존하고 잃는지, 그 손실이 물리적 부분 식별과 오차에 어떻게 반영되는지**를 정확히 보여 주는 연구가 현재 자산과 가장 잘 연결된다. 이는 기존 연구 동기를 유지하면서 실제 검증 가능한 주장을 만든다.

| 기여 | 현재 객관적 근거 | 다음 결정적 증거 |
|---|---|---|
| Q/O shape·proper orientation | 구성적 정리·fibre·경계 오차기하 | 기존 invariant 표현과 명시적 비교, noisy 공동 Q/O 처리 |
| tensorized conditional MES | sector·anchor·response set의 수학적 구별 | 실제 response, 공동법칙, 식별 functional |
| 제한 Bianchi solver | 실제 유효 kernel과 재사용 인프라 | 제약면 위 배경, 소비 경로, 보존·수렴 검증 |
| 관측 morphology | 실제 자료·mock·ablation 기록 | raw replay와 선택·상관을 보존한 calibration |
| local/global·깊이 분석 | 일관된 장기 질문과 일부 전방식 | source dynamics·observer effect·selection의 공동 likelihood |

Planck Bianchi 제약은 mode에 따라 크게 달라진다. 다른 논문의 더 작은 숫자와 경쟁하려면 동일한 물리량·congruence·mode·prior·confidence 정의가 필요하다. 일반적인 “더 강한 MES bound”라는 표현만으로는 비교할 수 없다. [Saadeh et al., How isotropic is the Universe?](https://arxiv.org/abs/1605.07178)

Local Codex로 넘길 다음 실행 단위는 이론 선택과 분리해야 한다. 여기서 확정할 것은 (i) signed ratio의 정의역과 extremum 규칙, (ii) MIO의 공동 null과 pair role, (iii) 사용할 collision 경로와 frame, (iv) 관측 response와 shared nuisance다. Local은 이 계약을 받아 다음을 검증한다.

1. signed·zero-crossing ratio 반례와 four-endpoint reference, 기존 positive-domain 회귀를 한 work unit에서 검증한다.
2. MIO는 상관된 Gaussian 반례, pair-role 순열, simplex identified-set 예제를 검증한다. 실제 데이터에 적용할 null은 별도로 명시한다.
3. Thomson은 isotropic null, 무편광 quadrupole의 $9/10$ 감쇠, packed coupled eigenmodes, frame-conjugation을 실제 consumer에서 확인한다.
4. 기존 관측 결과는 raw product·compression·selection·calibration을 묶은 source-input-output replay로 확인한다. 새 통계에 같은 데이터를 다시 썼다면 그 의존성을 보존한다.

이 목록은 전체 구현을 즉시 release한다는 뜻이 아니다. 먼저 미지정 과학 입력을 닫아야 한다. scope를 고정한 뒤의 코드 수정·검증은 워크스테이션 Local Codex가 담당한다.

# 전수조사에 남은 구체적 범위

이번 보고서로 요청한 저장소 전수조사가 끝났다고 할 수 없다. 남은 큰 항목은 모든 reachable historical tree와 고유 content의 목록 완결, 미독 blob의 전문 읽기, archive 내부 member의 분리, 보고서의 숫자별 JSON·producer·실행 source·입력 provenance 연결이다. 생성 파일의 중복은 내용 동일성으로 한 번 읽을 수 있지만, 서로 다른 내용은 파일명이 같아도 별도로 판정해야 한다.

그 다음 각 역사적 결함이 어느 시점에 수정됐고 어떤 현행 caller가 여전히 소비하는지 추적해야 한다. 지금 발견한 signed ratio의 public API 결함을 실제 관측 결과의 오류로 단정하지 않는 이유도 caller/domain 추적이 아직 없기 때문이다. 접근 가능한 ref 밖의 삭제 이력과 로컬 전용 자료는 현재 census가 포괄하지 못한다.

현재 독립 판정은 **주요 수정 필요, 동시에 유효한 수학·관측 자산의 잠재력은 상당함**이다. 전체 원고를 폐기하거나 전체 solver를 새로 작성할 근거는 없다. 유효한 정리와 kernel을 실제 관측 연산자에 연결하고, 구형 주장에 붙은 잘못된 정량적 해석을 교정하는 것이 우선이다.

# 근거 상태와 이번 검토 기록

이번 핵심 반례의 상태는 derived 및 static-source-checked다. 새 runtime 검증에 해당하는 implementation-verified 또는 numerically checked는 부여하지 않았다. 관측 수치는 inherited artifact evidence다. 신규성의 우선권, 실제 관측 유의성의 교정량, 미독 코드의 상태는 unresolved다.

두 독립 검토는 충돌·native 소비 경로와 원고·tensorized MES를 나누어 수행했다. 조정자는 MIO·bulk-flow·새 obsstat 전문과 중요한 충돌·원고 구간을 직접 대조했다. signed-ratio 반례는 독립 수학 확인도 받았다. 양수 numerator를 전제로 쓰인 기존 결과의 오염 여부는 판정하지 않았다.

문헌 검색은 MES·multipole invariants·randomization·selection likelihood 및 Bianchi mode 제약에 한정했다. 가장 가까운 선행연구의 완전한 novelty census는 미완료다. 웹 검색에서 반환된 무관 결과는 근거로 쓰지 않았다. GitHub 공개 페이지 접근 실패는 연결 도구로 우회했으며, 권한 변경이나 게시·push는 하지 않았다.
