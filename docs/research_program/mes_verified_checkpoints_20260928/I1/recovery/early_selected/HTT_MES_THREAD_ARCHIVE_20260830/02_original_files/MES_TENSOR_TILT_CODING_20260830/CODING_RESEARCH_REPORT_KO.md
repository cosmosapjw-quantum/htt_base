# MES tensor/tilt 코딩 연구 루프 — 실제 실행 보고

## 0. 결론과 범위

첨부 연구 패키지 전체를 불변 seed로 보존하고, 새 코딩 하네스에서 세 루프를 실행했다. 결과는 (1) 올바른 기저와 scale 안정성을 유지하는 배치 tensor kernel, (2) inverse-square temperature와 direct-temperature의 통계적 차이를 드러내는 역산 비교, (3) nuisance에 따른 식별성과 exact finite-rank confidence calibration이다.

새 관측 결과나 production 패치는 아니다. 원시 지도/processed Planck 배열/사용자 환경/Actions/remote write는 없었다. 기존 두 C_l 숫자는 원 seed의 MES 정규화 산술회귀에만 사용됐다. 독립 reviewer를 실행할 별도 도구가 없으므로 독립 diff/scientific review는 NOT_RUN이다. 아래의 코드·합성 검증과 외부 과학적 수용을 구분한다.

## 1. Seed 복원과 실제 출발점

`seed/MES_TENSOR_TILT_RESEARCH_20260830`는 원 ZIP의 모든 항목을 그대로 보존한다. 원 manifest 불일치 0건, 기존 테스트 34개 통과, 원 `run_experiments.py` 재실행의 JSON 전체가 원 numerical summary와 동일했다. Counterstream tilted dust, 원 nonlinear inverse, generic chart, 저-z affine response 등 이번에 새 구현으로 대체하지 않은 결과도 이 재현 범위에 포함된다. 단, seed 테스트 통과가 해당 결과의 독립 심사나 full HTT integration을 뜻하지 않는다.

중간 출력 단계에서 임시 runtime이 초기화됐다. 코드·테스트를 복구하고 RED→GREEN을 재실행한 뒤 모든 campaign을 다시 생성했다. 이전 임시 git commit이나 transcript 숫자는 현재 authority가 아니다. 복구 후 독립 두 번째 campaign의 deterministic CSV/JSON 10개는 byte-identical이며, 마지막 입력 guard 수정 이후 final execution도 같은 10개 결과를 정확히 재현했다.

## 2. 루프 1 — 기저, cubic/mixed geometry, 배치화

### 실제 저장 규약

c=(a_l0, sqrt(2) Re a_lm, -sqrt(2) Im a_lm)이며 c의 Euclidean norm이 harmonic energy다. l=2,3에 대해

Q:Q = 15/(8π)||c2||²,   O:O = 35/(8π)||c3||².

`basis.py`는 이 규약의 변환 행렬을 한 번 만들고 임의의 batch 선행 차원을 처리한다. 자기 역변환뿐 아니라 독립적인 complex spherical-harmonic 합성으로 Q:nn, O:nnn를 비교했다. SciPy sph_harm_y의 theta=colatitude, phi=azimuth 및 Condon–Shortley convention을 명시했다. Proper rotation의 tensor action, real carrier action, 군 합성 및 norm을 별도 검사한다.

### Scale 안정화

Q/O response는 O=3 STF(beta⊗Q), beta_hat=(q2 I+6Q²/5)^(-1)(O:Q)다. 기존 seed는 원시 차원의 Q²를 직접 계산하고 절대 STF tolerance를 사용했다. 새 코드는 Q,O를 각각 최대 절댓값으로 나누어 solve한 뒤 비율을 복구한다. 동일 scale을 곱했을 때 beta와 relative residual이 변하지 않아야 한다.

실제 common scale 10^-200..10^200 검사에서 새 beta 오차는 최대 약 1.4e-16이었다. seed는 10^-200에서 nonzero quadrupole 판단이 실패했고, 10^-160에서는 유한 숫자를 반환했지만 beta 오류가 약 0.01784였다. 큰 scale에서는 단위 의존적인 absolute STF check가 정상 tensor를 거부했다. `projection_scale_stress.csv`에 에러 종류와 원인을 보존했다.

### 성능

최종 단일-BLAS-thread 측정, 동일 입력, 3회 median:

| Kernel | 행 수 | Seed Python loop | Batch | Speedup |
|---|---:|---:|---:|---:|
| Q 변환 | 20,000 | 193.575 ms | 0.385 ms | 502.5x |
| O 변환 | 20,000 | 318.418 ms | 1.342 ms | 237.3x |
| Q/O projection | 3,000 | 383.311 ms | 5.882 ms | 65.2x |

Q/O coefficient 최대 차이는 각각 8.9e-16, 4.4e-16이고 projection 차이는 1.8e-15 이하였다. 이는 이 작은 kernel과 Python loop 사이의 비교이지 전체 Planck pipeline의 speedup이 아니다. Runtime은 환경에 따라 변하며 replay scientific gate가 아니다.

### Cubic와 mixed quantities

`joint_shape`는 J=√6 tr(S³)/(tr(S²))^(3/2), normalized vSv, vS²v, det[v,Sv,S²v], Gram eigenvalue를 반환한다. Zero S 또는 v는 shape undefined로 거부한다. Sharp J boundary, Gram PSD, κ²≤(1-J²)/54를 검사했다. 절대 sky 방향이나 물리 shear를 scalar로부터 생성하지 않는다. MES 함수는 PSTF norm을 입력으로 받는다는 점을 API와 scope string으로 명시한다.

## 3. 루프 2 — exact algebra를 noisy estimator로 사용할 때

### Scaled inverse-square fit

Ideal isotropic-emission, collisionless Bianchi-I와 finite observer boost에서는 F=T^-2가 quadratic sky function이다. F의 9계수를 적합하고 ηA의 timelike eigensystem에서 beta, B, T_iso를 얻는다. η는 indefinite이므로 positive-definite generalized `eigh(A,η)`를 사용하지 않는다. 일반 eigenproblem과 Euclidean positive-rest-matrix diagonalization을 분리했다.

새 `QuadraticDesign`는 고정 directions/weights의 rank-revealing SVD를 재사용하고, T/median(T)를 먼저 계산해 thermal scale을 분리한다. Rank<9, complex/non-type-I spectrum, nonpositive spatial gaps, invalid temperature는 성공으로 처리하지 않는다.

400개의 noiseless 사례에서 ||B||를 10^-12..0.5, |beta|를 0..0.75, T_iso를 10^-150..10^150에서 바꾸었다. 최대 B오차 4.4e-15, beta오차 3.9e-15, T_iso 상대오차 5.9e-15였다. 이는 절대 parameter accuracy이며 B→0에서 eigen-axis나 normalized shape가 정확히 식별된다는 뜻은 아니다.

B≈0에서 log-eigenvalue 평균을 빼는 상쇄오차가 trace를 남기는 결함을 실제 재현했다. 반환 B를 정의상 STF(log M)/2의 다섯 independent coordinates로 구성해서 해결했다. 외부 입력에 대한 STF tolerance는 완화하지 않았다.

### Direct-temperature fit

실험에서 선언한 noise는 T_obs=T_model+epsilon, epsilon~N(0,sigma²)다. 따라서 nonlinear F=T_obs^-2의 오류는 원래의 independent homoscedastic Gaussian 오류가 아니다. Uniform F least squares는 이 T noise에 대한 likelihood가 아니다.

새 후보는 5개 STF B와 3개 rapidity 좌표를 nonlinear least squares로 적합한다. 각 후보에서 T_iso는 양의 scale로 analytic profile한다. 알려진 sigma를 사용하며 quadratic inverse를 명시적인 초기값으로 받는다. Initialization 실패/optimizer nonconvergence/경계 도달/rank deficiency는 기록하고 성공으로 바꾸지 않는다. Gaussian 관측이 음수가 되면 현 API는 거부하고 trial을 실패로 남긴다. 이번 800개 등록 trial에는 그런 실패가 없었다.

154개 선택된 방향, 4개 sigma, 각200회, 같은 random realization을 두 후보에 사용했다. T_iso=1에서:

| sigma | B RMSE: F fit | B RMSE: direct T | T_iso 평균오차: F fit | T_iso 평균오차: direct T |
|---|---:|---:|---:|---:|
| 0.003 | 0.002035 | 0.001823 | -0.00000061 | +0.00000136 |
| 0.02 | 0.013602 | 0.012152 | -0.0004337 | +0.0000319 |
| 0.07 | 0.049050 | 0.042554 | -0.005968 | +0.000346 |
| 0.14 | 0.110319 | 0.085385 | -0.024691 | +0.001356 |

sigma=.14에서 T_iso RMSE는 .029874→.014609, beta RMSE는 .044522→.037730이었다. Direct fit은 한 trial당 대략11–20 ms, quadratic inverse는 .34–.40 ms였다. 따라서 선택은 **빠른 초기화/진단 + 명시한 T-noise model에 따른 refinement**다. 항상 nonlinear fit으로 교체하라는 결론이 아니다.

이 noise 수준과 beta는 알고리즘 stress test이며 실제 Planck noise나 cosmological signal power를 뜻하지 않는다. Gaussian의 0 근처 support 때문에 inverse-square의 무조건부 모멘트는 특이해질 수 있다. 흔한 Taylor 기대값 전개를 전 Gaussian support에서 성립하는 정확한 모멘트식으로 쓰지 않았다. 실제 finite trial과 실패 조건을 보고한다.

### 모델이 틀리면 더 좋은 optimizer도 틀린 답을 준다

Fitted model에 없는 intrinsic P3(n_z)를 더했다. Masked sky에서 amplitude .1일 때 B오류는 F fit .02424, direct T .03826이었다. Direct T가 자기 noise objective를 더 잘 풀더라도 model error를 parameter에 흡수해 더 편향될 수 있다. 이는 폐기하지 않고 `model_mismatch.csv`와 그림에 보존한 음성 결과다. Convergence, 낮은 cost 또는 exact algebra만으로 모형 validity를 주장하지 않는다.

## 4. 루프 3 — nuisance-aware inverse와 finite-rank confidence set

Linear carrier response y=R(Q) beta+N eta+noise에서 covariance를 Cholesky whitening하고 nuisance span을 투영한다. 남은 R의 SVD가 full column rank일 때만 conditional point estimate를 반환한다. Rank deficient이면 `IDENTIFIED_SET` 또는 `NONIDENTIFIED`와 null basis를 반환하고 point estimate는 None이다.

실행 결과: intrinsic nuisance 없음 rank3; response 방향 하나 nuisance로 허용 rank2; arbitrary intrinsic octupole N=I7이면 rank0. N=R처럼 response span 전체를 허용한 경우도 roundoff가 가짜 rank3을 만들지 않도록 원래 response scale을 rank threshold에 썼다. Whitening, covariance rotation, invertible measurement reparameterization, seed isotropic least-squares와 대조했다.

Finite rank는 p=(1+# reference_score>=query_score)/(Nref+1). Tie는 보수적이며 정수 numerator를 유지한다. int64를 float64로 바꾸면서 2^53 이상 인접값을 tie로 만드는 실제 결함을 재현하고 수정했다. Reference threshold도 integer면 integer로 유지한다. Mixed boolean list가 float coercion 안에 숨는 경로도 거부한다.

5000개의 **서로 독립적인** complete201-row pool을 생성했다. 각 pool은 reference200+query1이며, Gaussian response 오류의 true-parameter Mahalanobis score를 사용한다. Alpha1/20에서 rejecting numerator≤10, 연속 exchangeable target coverage=191/201이다. 한 reference pool을 반복 재사용해 독립 시행처럼 세지 않았다.

- Matched noise: 4748/5000=0.9496.
- Monte Carlo Wilson95% interval: [0.94318,0.95533].
- Discrete theoretical target: 0.9502488.
- Query noise sigma만 reference의 두 배로 바꾼 negative control: coverage0.4222.

이 결과는 정확한 rank arithmetic만으로 null mismatch를 해결할 수 없음을 보여준다. 이것은 synthetic confidence-set coverage이지 Planck p-value, MES premise coverage 또는 astrophysical null fidelity의 검증이 아니다.

## 5. 테스트·반례·재현성과 심사 상태

최종 테스트는104개: 새70개+seed34개. 별도 임시 copy에 세 결함을 다시 넣어 현재 테스트가 각각 실패함을 확인했다: weak-B trace residue, integer rank cast, nuisance-projection roundoff rank. 원본 source는 변경되지 않았다. Finite array, dtype, covariance positivity, nonconvergence, rank, zero shape, improper rotation도 검사했다.

최초 복구 후 campaign, 독립 replay, 최종 guard 수정 후 execution의10개 deterministic numerical files는 동일하다. Timing은 별도다. 그림5개는 실제 생성된 CSV/JSON에서 matplotlib으로 작성했고 PNG/PDF를 직접 확인했다. Generator는 visual PASS를 자동 생성하지 않는다.

Self review는 implementer의 별도 PHYS-MATH / PHYS-MATH-CODE pass다. 별도 독립 reviewer 또는 Skillquiver 실행을 가장하지 않았다. Skillquiver discovery는 no tool, codex/coderabbit CLI도 없었다. 따라서 independent review와 production/publication adoption은 HOLD다. `review/INDEPENDENT_REVIEW_BRIEF.md`로 다음 reviewer가 정확한 후보를 검사할 수 있다.

## 6. 다음 작업에 주는 실제 의미

이미 증명한 algebra를 관측 pipeline에 옮길 때 필요한 방어가 구체화됐다. 원 stored basis 그대로 batch 변환하고, 미분/회전/단위를 독립 oracle로 검사하며, nuisance를 허용했을 때 정보가 사라지는 경우를 코드가 표현한다. MES norm body는 그대로 conditional constraint로 재사용할 수 있지만 source-correct physical premise와 nuisance consistency가 먼저다.

현재 할 수 있는 후속 일은 별도 reviewer의 code/science audit, 실제 HTT API adapter의 thin integration, noise/beam/mask response를 명시한 synthetic end-to-end test다. 원시 지도 재계산이나 철회 rank 복권은 이 패키지에서 수행하지 않는다. Bianchi-I inverse, Q/O projection, finite rank 중 하나의 성공을 다른 층의 성공으로 자동 승격하지 않는다.
