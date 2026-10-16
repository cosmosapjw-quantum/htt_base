# HTT six-paper DAG: L01 최소 고차모드 lift와 S02 source-conditioned sharp interval 연구

2026-10-17 KST. 이전 Draft PR #551 HEAD `6c97e3be2fae0fbbdb5a7392258f3a78cdc3556c`에서 이어진 **독립적인 두 bounded work unit**이다. 관측 자료 재생은 이미 PR #542/#545와 이전 실험에서 저장한 바이트 고정 원본을 사용한다. 이번 작업에서는 사용자의 Ubuntu에서만 존재하는 새로운 `table2.dat`, `table3.dat`, `table4.dat`의 실제 바이트나 Planck native Pol FITS를 읽지 않았다. 새로 실행한 계산은 Planck source-derived T-mask 행렬과 CF4 H03의 36x36 공동 working covariance를 사용했다. 물리 학계 주장 또는 posterior admission은 하지 않는다.

## 1. L01: 정확한 유한 T mask leakage 역문제

정의: `retained_common_support_coefficients.npz`에 저장된 동일 하늘의 9개 T 처리본의 cut-sky low-ℓ coefficient vector `y\in R^32`(ℓ=2..5, 단위 µK), source mask geometry response `K = [K_{6:16} | K_{17:32}] \in R^{32×1053}`. 253+800=1053. K는 실제 PR3 temperature mask geometry에서 추출된 source-conditioned finite operator이고 빔, T/Pol jointly-calibrated pipeline, ℓ>32와 foreground/null law가 포함되지 않는다.

행 rank가 32라는 것을 수치 확인했으므로 모든 `y`에 `K h = y` 해가 존재한다. 고차 모드 계수의 Euclidean norm을 최소화하는 유일한 최소노름 해는

`h_* = K^T (K K^T)^{-1} y`와 `R_min(y)^2 = y^T (K K^T)^{-1}y`.

이는 양의 정부호 Gram 행렬에 대한 라그랑주 승수 또는 행 공간 / null 공간의 직교분해에서 바로 따른다. 임의의 다른 해는 `h_* + z, z\in ker K`이므로 `||h||²=||h_*||²+||z||²`. 독립 SVD와 Cholesky 해를 비교했으며 회전/열 permutation 불변성도 검산했다. Wolfram 별도 2×3 기호 예제는 잔차 `(0,0)`, Gram 제곱노름 차이 0을 반환했다.

- 실제 source `K`: rank 32, nullity 1021, operator norm 2.4328695605629203, smallest singular value 0.1295760656186035, condition number 18.775609129265.
- **SMICA FULL** `||y||=99.48487 µK`, `R_min,ell6..32=273.1509463 µK`.
- ℓ=6..16만 이용하면 `R_min=353.3113283 µK`, ℓ=17..32만 이용하면 `R_min=527.2121411 µK`. 두 subband도 rank 32. Source stored coefficient basis에서만 정의되는 수치임을 주의한다.
- SMICA HM1 − HM2 차이 `||Δy||=0.8494471 µK`, 이 차이를 같은 finite mask 선형연산자 하에서 `K Δh=Δy`로만 설명하는 최소노름은 `2.1435511 µK`. 동일 하늘 처리본의 차이에 대한 역문제 diagnostic이며 실제 처리 차이가 고차 하늘 모드로 인한 것이라는 claim은 아니다.
- 제약 `||h||≤R`일 때 임의의 고정 저모드 선형 contrast `v^T b`, `y=b+K h`의 **정확한** 범위는 `[v^T y - R||K^T v||, v^T y+R||K^T v||]`. Cauchy–Schwarz로 bound를 얻고 `h=±R K^Tv/||K^Tv||`가 극값을 구성하므로 sharp하다. 선형 contrast만 해당하고 데이터로 선택한 `v`에 대한 사후 선택 보정은 포함하지 않는다.

**강한 주장 금지:** `R_min`은 실제 Planck 높은 harmonic tail의 norm을 측정하거나 true low-ℓ=0을 증명한 것이 아니다. 원 source cut-sky coefficient `y`와 finite geometry `K`의 선형 algebra 최적해다. 실제 high-harmonic norm, ℓ>32, beam, foreground, component separation, noise E2E covariance가 제공되지 않아 L01 pending, L03 physical null hold다.

원전은 Hivon et al. (2002, MASTER, DOI 10.1086/338126), Smith (2006, pure pseudo-Cl, arXiv:astro-ph/0511629), Alonso (2025, anisotropic Q/U weighting, arXiv:2410.07077). 수학적 finite rowspace inequality 자체는 선행 pseudo-Cl 방법에 기반하므로 새로운 우주론적 신호 발견이라고 주장하지 않는다.

## 2. S02: 공동 CF4 draw의 sharp working ratio event bounds

H03의 실제 35,970개 그룹 cohort SHA `86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c`, four-window 4x9 source mean and 36x36 source-conditioned Gaussian covariance, archive SHA `303c78ff655237edf87db972ce882142837fac8588d269d6cd861c76346fb219`을 고정한다. 동일 Sobol scrambled seed `160916`과 antithetic 2,048 36D draw를 재현하며, 각 draw가 4개 겹치는 적색편이 창의 **하나의 공동 실현**이다. 각 draw의 정규화 가중치는 1/2,048, 총합 1이다. 이 measure는 posterior가 아닌 working-error conditional Gaussian ensemble이다.

`H_j > 0`, `s_j=||STF5_working_j||₂`, `q_app_j=s_j/H_j`이다. 외부에서 잠재적 오차볼 `||δs_j||₂≤b_j`, `|δH_j|≤a_j<H_j`를 **hard bound로 공급했다고 가정**하면

`l_j=max(0,s_j-b_j)/(H_j+a_j)`와 `u_j=(s_j+b_j)/(H_j-a_j)`.

양 끝은 δs를 원래 STF5 방향으로 축소/증가시키고 δH=+a/-a로 선택하면 도달한다. 사건 `q_j>t`의 unconditional **working measure** lower/upper는 `Σ_i w_i 1(l_ij>t)` 및 `Σ_i w_i 1(u_ij>t)`이다. 네 창에서 **at least one** 사건은 `any_j`로, **all windows** 사건은 `all_j`로 결합하지만 weight는 공동 draw i마다 딱 한 번 사용한다. 각각의 sample/window perturbation이 서로 독립적으로 허용된 box/ball 곱집합이라는 명시적 구성공간에서는 이 계산이 sharp하다. 동일 기하학적 shear history 제약 등 창 간 상관된 물리 제약을 넣으면 더 작은 식별집합이 될 수 있다. strict `>` 문턱 equality는 exceedance가 아니다.

역치 0.05, 적어도 하나의 창 exceedance에서:

| 조건부 hard bounds km/s/Mpc | 하한 | 상한 |
|--|--:|--:|
| `b=0,a=0` | 0.60302734375 | 0.60302734375 |
| `b=0.5,a=0.2` | 0.14697265625 | 0.95654296875 |
| `b=1,a=0.5` | 0.00830078125 | 0.9990234375 |

이 수치들이 실제 물리적 calibration uncertainty를 정량화하는 것은 아니다. 다른 assumed radii를 넣어 단조적인 식별범위를 분석할 수 있도록 코드를 제공한다. source real Gaussian pairing을 보존하지만 physical `x_C`, signed `Q=x_C/U_sigma`, certified `F` 및 `G_F`는 모두 출처 및 기하학적 congruence가 아직 없다. 따라서 physical unknown mass는 **1.0**, 물리적 `Pi_Q` 외부구간은 `[0,1]` 그대로다. Working `q_app`를 물리적 `Q`로 rename/zero-fill/renormalize하면 안 된다.

## 3. 검증, 한계, 다음 acceptance

- 원본 NPZ SHA 3개 + H03 원본 ZIP과 source group 35,970 고유성 확인, source mean/cov 4x9/36x36 PSD/Cholesky, exact 2,048 seed/weight가 성립한다.
- 실제 source T 마스크 32x1053 SVD, Cholesky/SVD와 Null-space 직교성, contrast attainability, split minimum norm, high-mode change of basis, source-tamper fail-close.
- S02 threshold strictness, bounds endpoint attainable, joint any/all, weight normalization, draw permutation, zero denominator fail-close, source corruption fail-close, enlarging hard balls monotonicity, physical unknown=1 검증.
- Native spin2 Planck Q/U mask NESTED2048->RING64, real E/B ℓ6..8 response, channel-specific beam, actual FFP10 end-to-end null calibration 및 physical CF4 joint selected likelihood는 **이번 실행에서 수행되지 않았다**.
- **DAG 판정:** L01, S02 `pending` 유지. S04/L03/H02/V03/B02/K03/K04 외부 물리 입력 `unresolved`, 총 14/42 `completed_scoped`, six papers `NOT_READY_TO_SUBMIT`.

다음 실제 수용 실험은 로컬 native Planck polarization mask와 healpy source-alm/Wigner convention에서 `K^P_{LH}`의 E/B leak operator를 재계산하고, FFP10의 같은 mask/beam/processing matched signal+noise independent sky null을 만드는 것이다. 다른 lane에서는 CF4 W1-TF physical parent selection/calibration/velocity common law에 source-certified physical shear/tilt/curvature mapping을 연결하기 전까지 `S02`의 working-only 결과를 physical evidence로 승격하지 않는다.

## 4. 추가 S02: 부호 있는 물리적 Gauss–MES sector의 sharp box map

기존 legacy에서 혼란이 있었던 `x_C>=0` 선언을 제거하고, metric signature (-,+,+,+)에서

`x_C=[sigma_ab sigma^ab - omega_ab omega^ab]/(6 H²) + Omega_tilt + DeltaOmega_k`,
`H=Theta/3>0`, `U_sigma=(3/2) B_sigma²>0`, `Q=x_C/U_sigma`를 정의한다. 여기서 `sigma_ab sigma^ab`, `omega_ab omega^ab`는 각각 0 이상의 비음수 제곱노름이며 **그 차이의 부호는 제한되지 않는다**.

각 독립 물리 sector가 box로만 지정된 경우 `N=[sig_min²−omega_max²,sig_max²−omega_min²]`로 놓고 `N/(6H²)`의 최솟값·최댓값을 `N`의 두 끝과 `H`의 두 끝을 조합한 네 꼭짓점에서 계산한다. Tilt·curvature 구간을 각각 더하고, `U_sigma`의 양의 두 꼭짓점으로 나눈 `Q`의 네 비율 중 최솟값·최댓값을 사용한다. 각 단계가 연속 함수의 rectangular product-domain extrema에 해당하므로 **독립적인 자유 box일 경우** sharp하다. 물리적으로 서로 상관된 shear–H–tilt 관계가 추가되면 이 값은 가능한 outer bound이나 sharp라고 볼 수 없다. 이는 식별불능 정리가 아니라 관측·transfer 입력을 정확히 어디에 대입할지 정한 constructive adapter다.

전적으로 제조된 illustrative 입력 `H∈[68,72] km/s/Mpc`, `sigma_ab sigma^ab∈[0,16] (km/s/Mpc)^2`, `omega_ab omega^ab∈[0,25] (km/s/Mpc)^2`, `Omega_tilt∈[0,.001]`, `DeltaOmega_k∈[-.002,.003]`, `B_sigma∈[.03,.05]`에서 `x_C∈[-.0029010957,.0045767013]`와 `Q∈[-2.1489598,3.3901491]`. 부호 있는 모델의 interval crossing은 양의 filling fraction `F` 또는 physical Q posterior를 뜻하지 않는다. 현재 CF4는 동일 congruence의 shear, vorticity, curvature 및 tilt sector를 실제로 제약하지 못했으므로 `physical_exceedance_unknown_mass=1`을 유지한다. 모든 2^6 꼭짓점 열거와 경계반례 검산. 파일 `src/signed_sector_box.py`, `results/S02_SIGNED_MES_INTERVAL_THEOREM.json`.

## 5. 실제 이번 실행·증거 경계

`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q tests`로 **23 tests PASS**. 다섯째 테스트 모듈은 signed sector math만 검증한다. source materialized SHA를 고정한 결과 JSON 3개를 clean directory에서 재현한다. Wolfram의 2×3 matrix pseudoinverse 상징 계산은 `K h_*-y=(0,0)`, `||h_*||² - y^T(K K^T)^-1 y=0`을 확인했다. No native independent subagent tool available. Do not count supplied source metadata as astrophysical physical-input proof. Original DAG, six-paper publication submission holds, seven physical blockers unchanged.
