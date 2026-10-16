# C8-SMICA-FULL-MASK-FINITE-RESPONSE — source-bound 유한 조화 응답

2026-10-16 KST. **Owner:** obsstat. **Claim tier:** `SOURCE_CONDITIONAL_FINITE_HARMONIC_RESPONSE` / `DIAGNOSTIC_ONLY`. **Transfer:** released Planck PR3 full SMICA processed temperature map. 이 결과는 물리적 almost-EGS epsilon, Bianchi geometry, shear, tilt 또는 검출 결과가 아니다.

## 원본과 계산 규약

기준은 Loop 5의 공개 Planck PR3 full SMICA intensity map, 공식 common temperature mask, HM/OE missing-pixel mask, 고정 K1 temperature confidence다. 모든 source SHA-256은 `results/response_v1/result.json`의 `source_sha256`에 있다. map `60952c64…ce4f9ac`, common mask `23f49a34…a5fc4`, HM mask `f4fd9097…dfb2a0`, OE mask `ecb39152…28aff9`, K1 cache `86b792c8…bc5fadb`; Loop 5 결과·계수도 동결 SHA와 일치한다. 대형 FITS와 cache는 저장소/PR에 복제하지 않는다.

NESTED NSIDE2048의 유효 child 평균 및 coverage를 RING NSIDE64로 내린다. Loop 5와 같은 confidence `>0.5`, fine-mask coverage `>=0.995`의 공통 support는 **26,846/49,152**픽셀이다. 관측 온도는 `K_CMB`에서 thermodynamic `microK`로 변환한다. pixel 가중은 선택된 곳에서 `W=1`, 나머지는 `W=0`인 unweighted simultaneous OLS다. 전구면 직교정규 real harmonic 열 순서는 각 ell의 `m=0`, 이어서 `sqrt(2) Re Y_lm`, `sqrt(2) Im Y_lm`; SciPy의 Condon–Shortley 위상을 사용한다. 저차 ℓ0..5는 36열, 주입 고차 ℓ6..16은 253열이다.

선택 support에서 `Y_L=QR`를 계산하고, pixel projector의 명시적 역행렬 없이 `K_LH=R^{-1}Q^T Y_H`를 평가했다. baseline `A_L`는 36×26846, `K_LH`는 36×253; retained ℓ2,3 및 ℓ2..5는 각각 12×253, 32×253이다. 모든 singular value 및 ℓ별 block norm은 결과 JSON에, baseline 세 행렬은 NPZ에 있다.

## 실제 유한 결과

| 처리 | 픽셀 | low fit 조건수 | `||K_2,3||₂` | `||K_2..5||₂` | baseline 관측 32계수 변화 |
|---|---:|---:|---:|---:|---:|
| Loop 5 support, fit ℓ0..5 | 26,846 | 3.60138 | 1.755973 | **2.255720** | 0 |
| K1 confidence >0.8, fit ℓ0..5 | 26,846 | 3.60138 | 1.755973 | 2.255720 | 0 µK |
| fine coverage =1, fit ℓ0..5 | 26,363 | 3.63985 | 1.772956 | 2.275860 | 1.933315 µK |
| Loop 5 support, fit ℓ0..8 | 26,846 | 7.75577 | 3.093275 | 4.196669 | 65.980619 µK |
| Loop 5 support, fit ℓ0..12 | 26,846 | 24.4425 | 7.227228 | 10.167837 | 63.958316 µK |

Confidence >0.8가 같은 support를 택한다는 결과는 **이 source**의 선택 배열에 국한된다. fit 상한을 높이면 포함된 ℓ6..8 또는 ℓ6..12는 자기 계수로 복원되고 retained ℓ2..5로의 해당 leakage는 수치적 0이 된다. 그러나 새로 **미포함**된 고차 열의 전체 operator norm은 커진다. 서로 다른 fit에서 같은 물리량의 오차가 단조 감소한다는 주장이 아니다.

Baseline low identity 최대 잔차는 `3.55e-15`, low rank는 36, retained rank는 12/32다. `Y_00`, `Y_10`, `Y_11` 부호·규격과 Loop 5의 첫 36열이 대조되었다(차이 0, Cartesian check 최대 `1.03e-15`). QR fit으로 계산한 실제 full SMICA retained 계수는 Loop 5의 Cholesky 기반 저장 32계수와 최대 **`2.17e-13 microK`** 차이다. 같은 support의 관측 map에서 low fit 잔차 RMS `71.42 microK`는 foreground/noise 또는 물리적 high-mode norm 추정치로 해석하지 않는다.

단위 low·high 주입과 고정 seed의 random superposition을 검산했다. low max error `3.55e-15`, 고차 단위 주입의 독립 LAPACK least-squares 비교 max error `1.69e-15`, random 합성 max error `2.55e-15`. 해당 finite 주입에서 `||a_H||₂=16.9711 microK`, 실제 leakage `7.2756 microK`는 `||K||₂||a_H||₂=43.0282 microK` 이하이다. 이 수치는 **가정한 주입**이며 관측 하늘의 high-mode 계수 크기가 아니다. 같은 finite 공간에서 임의 `a_H`에 대해 `||Δa_L||₂ <= ||K_LH||₂ ||a_H||₂`가 성립한다. `||K_2..5||₂=2.255720`은 단위 `1 microK`의 *가정된* 고차 Euclidean norm당 계수 상한이다. ℓ2와 ℓ3 각각의 계수 Euclidean norm 상한 계수는 `1.383913`, `1.648856`이다. 여기에는 온도 정규화 또는 covariant MES 변환을 적용하지 않았다.

## 재현 및 claim 경계

실행: `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python3 -B run.py --output results/response_v1` (exit 0). `OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests/test_finite_response.py` (5 passed). 두 테스트 초반 실패는 import path 누락과 포함 고차 열의 identity를 leakage로 잘못 비교한 테스트 기대값 때문이며 수정 후 원본 과학 입력·수치를 바꾸지 않았다. 최종 재실행, 독립 검토, 백업 및 게시 신원은 별도 handoff/receipt에 기록한다.

**UNKNOWN/HOLD:** 전체 ℓ>16 꼬리, 실제 source high-mode norm, beam/component-separation transfer, foreground residual·E2E covariance, cosmological residual ε1, almost-EGS covariant 시간/공간 미분, observer congruence와 Bianchi geometry frame 사이의 물리적 response. 마스킹된 `sqrt(C_ell)/T0`를 MES covariant ε로 대입할 수 없다. PR124 geodesic strict 경계 `ε1 < (43/25)ε2+(9/35)ε3`의 물리 적용도 계속 HOLD다.
