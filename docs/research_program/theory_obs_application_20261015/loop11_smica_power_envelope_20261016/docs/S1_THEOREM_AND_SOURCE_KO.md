# C8: 실제 SMICA 저차 응답행렬의 finite power / covariance envelope

날짜: 2026-10-16 KST. 기존 `htt_base` PR #536 → #537을 따르는 새 독립 연구 단위.

## 자료와 claim tier

- 실제 Planck PR3 처리 기하에서 얻은 PR #536의 저장된 `K_ell2to5_32x253`와 형제 `K_full_36x253`, `K_ell23_12x253`를 **읽기 전용**으로 이용한다.
- `baseline_response_matrices.npz` SHA-256 = `a9aaeb393deba03c97ecf45bf4e1ab74e98e3a8747de7c4bc7a96bff27014007`. 세 행렬의 정확한 4:36 / 4:16 행 동일성 확인.
- 관측된 하늘의 고차계수, 실제 C_l 또는 FFP10 empirical covariance는 입력되지 않았다. 아래 숫자는 **실제 mask geometry × 선언된 가상 고차계수 분산법칙**의 함수다.

## 1. 소스 고정 저차 회귀와 정확한 전달

동일한 NSIDE64 source mask에 대한 저차 OLS 설계 행렬 `Y_L` (ℓ=0..5)와 omitted high-shell `Y_H` (ℓ=6..16)를 고정하고

    K := Y_L^+ Y_H,     δa_L = K a_H.

ℓ=2..5의 32개 실수 직교정규 기저 계수만 보존한 행렬을 `K32∈R^(32×253)`이라 부른다. 각 shell ℓ의 열들은 `[ℓ²−36,(ℓ+1)²−36)`이고 차원은 `(2ℓ+1)`이다.

평균을 제거한 임의의 고차 유한 공분산 `C_H`가 주어진 **선형 실험**에서 정확하게

    Cov(δa_L) = K32 C_H K32^T

가 성립한다. 독립이고 등방적인 shell별 실제 정규화 `C_ℓ I_(2ℓ+1)`를 *추가 가정*하면

    C_leak = sum_(ℓ=6)^16 C_ℓ K_ℓ K_ℓ^T.

교차 ℓ 상관이나 동일 하늘의 공통 처리 systematic이 있다면 그 항은 위 가정식에 없다. 제시한 모든 template `C_ℓ`는 단지 선언된 입력값이다.

## 2. 가상 불확실성 ellipsoid의 exact sharp bound

정해진 음이 아닌 반경 `R_ℓ`로

    U_R = {a: a_ℓ=0 if R_ℓ=0, sum_(R_ℓ>0) ||a_ℓ||²/R_ℓ² <= 1}

을 가정하면

    sup_(a∈U_R) ||K32 a|| = sqrt(λ_max(sum_ℓ R_ℓ² K_ℓ K_ℓ^T)).

이는 단순한 보수적 상한이 아니라 정확한 최댓값이다. 우세 왼쪽 고유벡터를 `u`라 하면 포화 witness는

    a_ℓ = R_ℓ² K_ℓ^T u / sqrt(λ_max)

로 명시적으로 만들 수 있다(`λ_max>0`). 직접 대입하면 ellipsoid norm은 1, 저차 출력 norm은 `sqrt(λ_max)`다. 해당 ellipsoid는 **임의 선언된 불확실성 집합**이지 관측 credible region이 아니다.

## 3. 임의의 cross-shell 상관에 대한 분산 상한

각 shell의 marginal covariance가 `C_ℓ I`이되 다른 ℓ끼리 임의로 상관된다면, 임의 단위 방향 `u`에 대해 확률론적 Minkowski 부등식으로

    sqrt(Var(u^T δa_L)) <= sum_ℓ sqrt(C_ℓ) ||K_ℓ^T u||
                                 <= sum_ℓ sqrt(C_ℓ) ||K_ℓ||_2.

따라서 위 마지막 합은 알 수 없는 cross-ℓ 공분산을 고려하는 (일반적으로 sharp하지 않은) 방향 불변 상한이다. 독립 Gaussian covariance의 최대고유값만 실제 공분산 상한이라고 가정하면 안 된다.

## 4. 실제 K에서 확인한 값

`||K32||_2 = 2.255720291177002`, `||K32||_F² = 23.99763523078023`.

모든 실수 고차계수에 **같은 가상 분산 C_ℓ=1**을 주면 출력 공분산 trace는 23.99763523078023이고, ℓ=6,7의 contribution 비율은 `0.5487045164919341`이다. 이는 진짜 Planck `C_ℓ` 입력의 결과가 아니다. 상관 모형, red/blue power template, 포화 witness, 엄밀한 Monte Carlo 대조는 `results/source_power_v1/RESULT.json`을 참조한다.

## 5. 과학적 한계와 다음 작업

- 새로운 실제 17..32 mask operator 자체는 PR #537의 로컬 runner를 통해서만 얻을 수 있다. 현재 ChatGPT 샌드박스에서는 원본 2048 Planck mask/K1 cache가 없어 `NOT_RUN`이다.
- `ell>32`, 실제 하늘의 계수 세기, beam, foreground, component separation, E2E noise/covariance, covariant almost-EGS 미분 및 observer→Bianchi 전송은 UNKNOWN이다.
- 본 연구는 `SOURCE_BOUND_PROCESSING_GEOMETRY_TIMES_DECLARED_POWER_MODEL`, NOT physical shear/tilt detection, NOT physical EGS epsilon, NOT Bayesian posterior admission.
- 매개변수별 `C_ℓ`를 실제 raw/FFP source와 정합시키고 cross-shell response/covariance를 별도로 확보해야 물리적 likelihood로 이동할 수 있다.

## 문헌 위치

- Hivon et al. (2002), *MASTER of the CMB Anisotropy Power Spectrum*, https://doi.org/10.1086/338126: sky window의 mode coupling과 spectrum/covariance calibration.
- Brown, Castro & Taylor (2005), *CMB temperature and polarization pseudo-Cℓ estimators and covariances*, https://arxiv.org/abs/astro-ph/0410394: covariance의 마스크/sky 모형 의존성.
- Planck 2018 Results IV, https://doi.org/10.1051/0004-6361/201833881: PR3 component separation 및 map/processing noise caveats.

이 문헌들은 본 사용자 코드의 수치 검증을 독립적으로 수행한 것이 아니라, 방법론적 맥락과 관측 physics scope를 제공한다.
