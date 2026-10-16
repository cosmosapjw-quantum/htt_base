# HTT C8 유한 harmonic power-envelope: 실제 소스 응답 × 조건부 고차계수 분산 연구

날짜: 2026-10-16 KST. 연구 단위: PR #537를 따른 **독립 샌드박스 경량 연구**. 

## 목적과 보존된 결과

저장된 **실제 Planck 공통 mask processing-geometry**의 `K_ell2to5_32x253`를 그대로 사용해, 가능한 고차계수 통계 모형을 입력으로 *명시했을 때만* 저차 leakage 분산·worst-case 노름을 산출한다. `K`의 SHA는 `a9aaeb393deba03c97ecf45bf4e1ab74e98e3a8747de7c4bc7a96bff27014007`이며 PR #536 원본의 4:36 행 조건과 정확히 일치한다. 실제 원본 맵·고차계수·상관 공분산의 새로운 측정은 포함하지 않는다.

## 계산된 조건부 결과

각 `C_ell`을 독립 실수 harmonic 계수의 **가상 분산**으로 간주한다. 다음 세 모형은 모두 `C_6=1`로 맞추어 비교한다.

| 가상 `C_ell` 형태 | 출력 trace | 가장 큰 출력 표준편차 | ell6+7 trace 비중 | 선언된 ellipsoid의 sharp norm bound |
|---|---:|---:|---:|---:|
| White, `C_ell=1` | 23.997635 | 2.255720 | 0.548705 | 9.348685 |
| Red, `C_ell=42/[ell(ell+1)]` | 15.539867 | 1.881794 | 0.724647 | 7.320119 |
| Blue, `C_ell=ell(ell+1)/42` | 47.853125 | 3.108768 | 0.328293 | 14.045122 |

표의 sharp bound는 `R_ell=sqrt((2ell+1) C_ell)`이고 `sum ||a_ell||²/R_ell² <=1`이라는 **별도 불확실성 집합** 아래의 exact 최대치다. 위 분산법칙의 통계적 `1σ`나 실제 Planck 오차막대와 동일시해서는 안 된다. 각 모형에 대해 직접 구성한 포화 witness의 ellipsoid norm과 output norm을 별도로 확인했다.

같은 모든 shell marginal covariance `C_ell I`를 유지하면서 일부 좌표를 공유하는 **가상의 상관 모형**

    a_(ell,j)=sqrt(C_ell)*(sqrt(rho)*z_j+sqrt(1-rho)*xi_(ell,j))

에서는 white case 최대 출력 표준편차가 `rho=0`에서 **2.255720**, `rho=1`에서 **2.878626**으로 바뀌었다. Red는 1.881794→2.240161, Blue는 3.108768→4.075339다. `rho`는 계측된 Planck 상관이 아니다. 모형 선택에 따라 공분산 output이 변할 수 있음을 판별하는 falsifier다.

상관을 전혀 특정하지 않고 shell marginal `C_ell I`만 안다면 spectral standard deviation의 상한은 `sum sqrt(C_ell)||K_ell||_2`이다. White/Red/Blue는 각각 8.019489/5.813904/12.035956이다. 이 수치는 일반적으로 sharp하지 않으며 실제 noise budget이 아니다.

## 실제 실행 및 검증

- `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_power_envelope.py`: **12 passed (exit 0)**.
- 원본 SHA tamper 차단, GitHub-only 로컬 checkout에서 Loop9 원본 NPZ의 읽기 전용 자동 검색(복사 불필요), H shell과 32/12/36행 원본 identity, covariance의 두 독립 구성 비교, scalar Cℓ shell trace, explicit sharp witness, 단순 2-축 해석적 oracle, shell별 직교회전 불변성, 가상 cross-correlation의 PSD, zero-power, invalid 입력 fail-closed.
- 독립 Gaussian Monte Carlo 24,000회 출력 공분산 Frobenius 상대 차이 0.02131098; correlated toy 24,000회 0.02312060. 이는 시뮬레이션 통계 오차를 포함하므로 machine precision identity로 주장하지 않는다.
- Wolfram Language에서 2x2 Gram 합산 identity 및 explicit eigenvalue oracle `G=diag(97,13)`, `||[R_A A,R_B B]||=sqrt(97)`가 계산됐다.
- 결과 JSON 및 32x32 covariance NPZ는 create-only 생성. PNG 2개는 source geometry에 **가상 power**를 곱한 민감도 그림이다.
- 원래 26,846 mask geometry matrix `K`의 SVD, 시나리오 처리, 샌드박스 검증을 구분한다. 실제 `ell17..32` mask 행렬 자체는 이번 턴에서 얻지 못했다.

## 효용·다음 물리 입력

이 연구 결과는 기존 Loop9/10의 **기하학적 leakage norm**을 이후 물리 likelihood의 covariance carrier에 연결할 계산식을 제공한다. 그러나 아직 Cℓ는 시나리오 입력이고, 실제 Planck 고차 power·beam·component separation·noise/systematics·동일하늘 cross-covariance가 식별되어 있지 않다. 실제 covariant EGS epsilon1 및 derivative hierarchy와 Bianchi transfer는 HOLD다. 새로운 physical shear/tilt 추정 또는 우주론적 유의도는 주장하지 않는다.

다음 실제 수행 가능한 독립 작업은 사용자의 기존 로컬 2048 mask/K1 원본으로 **PR537 `C8-SMICA-ELL17-32` local runner**를 실행·소스검증하여 새로운 36x800/32x800 행렬을 생성하는 것이다. 그다음 본 계약을 새 행렬에 적용하되 물리적 Cℓ 입력을 외부 source와 별도로 결합해야 한다.

## 핵심 맥락 문헌

- Hivon et al., MASTER, https://doi.org/10.1086/338126.
- Brown, Castro & Taylor, CMB pseudo-Cℓ covariance, https://arxiv.org/abs/astro-ph/0410394.
- Planck 2018 Results IV, https://doi.org/10.1051/0004-6361/201833881.

본 사용자의 `K` 수치 재현·코드 검증 자체는 문헌을 인용하는 것만으로 성립하지 않으며, 소스 SHA·실행 기록·테스트로 별도 검증하였다.
