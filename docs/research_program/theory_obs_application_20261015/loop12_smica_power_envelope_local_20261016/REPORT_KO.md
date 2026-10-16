# C8 유한 ℓ17–32 source response와 ℓ6–32 조건부 power envelope

2026-10-16 KST. Owner: `obsstat`. Claim tier: `SOURCE_CONDITIONAL_MASK_GEOMETRY_SCENARIOS_ONLY`. PR #536의 ℓ6–16 행렬과 PR #537의 로컬 ℓ17–32 알고리즘을 사용한다. PR #538의 ℓ6–16 power-envelope 계약은 읽기 전용으로 검토했고 12개 테스트를 재실행했다. 세 PR의 원본 코드를 덮어쓰지 않았다.

## 원본과 기하학

원래 checkout HEAD는 `13d8d85fa470d645d008986e8f77d8d0f70fdf54`이며 CF4 tracked 변경과 다수의 untracked 연구 파일을 보존했다. PR #537 HEAD는 `f85bb82ecdb308596dd283aa495dbcc01324facf`, PR #538 draft HEAD는 `fed86da78de1dafed9b89785b9c0a5664735cf8d`다. PR #536의 기존 ℓ6–16 NPZ SHA는 `a9aaeb393deba03c97ecf45bf4e1ab74e98e3a8747de7c4bc7a96bff27014007`다.

PR #537 runner는 common/HM/OE mask와 K1 cache를 SHA로 다시 확인하고, 동일 NSIDE64 RING support **26,846**픽셀에서 PR #536의 `K6..16`을 최대 `4.16e-17` 차이로 복원했다. 해당 runner는 full SMICA FITS의 바이트를 직접 읽거나 재해시하지 않는다. 본 로컬 단계에서 별도로 원본 full map **2,013,312,960 bytes**, SHA `60952c645eb33d151905ddf5837477e15ca02a3261feca4ceca3c3feece4f9ac`를 검증했고, 추가 envelope runner의 PR #536 source gate도 이를 포함한 모든 동결 입력을 재해시했다. 이 map은 harmonic response의 데이터 값으로 들어가지 않는다. response는 선택 mask의 유한 선형 기하학이다.

동일 `Y_L`의 unweighted QR projector를 적용하여 새로운 `K17..32`는 **36×800**, retained ℓ2,3은 **12×800**, ℓ2..5는 **32×800**이다. 열은 각 ℓ의 `m=0, sqrt(2)Re Y_lm, sqrt(2)Im Y_lm`이며 ℓ17은 이어 붙인 전체 행렬의 열 253에서 시작한다. 선택 mask SHA는 `98c90cbd186aceed02f6692ef83685b44d0f7f22569f218ea2936dcfafcedfbf`. 새 NPZ SHA는 `91f496ca7cd1cbaed65153c64d83cf7abf84b21c141d8955d0cd8e07ed480a35`다. ℓ17–32의 32차원 operator norm은 **0.9208432350**, 결합 ℓ6–32의 32×1053 norm은 **2.4328695606**이다. 가상 고차계수 주입의 OLS 재구성 최대 잔차는 `3.55e-15`이고, 실제 high-mode 하늘의 leakage 측정이 아니다.

## 선언한 가상 분산에 한정한 결과

각 `C_l`은 실수 harmonic 좌표당 **가상 분산**이다. 독립 shell 가정을 명시했을 때 `Cov(Δa_L)=K diag(C_l I) K^T`를 계산하고, 별도 집합 `sum_l ||a_l||²/R_l²≤1`, `R_l=sqrt((2l+1)C_l)`의 sharp output norm을 계산했다. 이 집합의 경계는 통계적 1σ 또는 credible region이 아니다.

| 가상 시나리오 (`C_6=1`) | 출력 trace ℓ6–32 | 그중 ℓ17–32 | 최대 출력 표준편차 | sharp ellipsoid norm |
|---|---:|---:|---:|---:|
| White `C_l=1` | 28.270962 | 4.273326 | 2.432870 | 11.312497 |
| Red `42/[l(l+1)]` | 15.875133 | 0.335266 | 1.898180 | 7.516870 |
| Blue `l(l+1)/42` | 111.132236 | 63.279111 | 4.673369 | 28.866503 |

PR #538의 기존 ℓ6–16 white trace `23.997635`를 새 행렬의 해당 열에서 재현했다. `rho=0,.25,.5,1`의 공유좌표 cross-shell 모형과 shell marginal만을 고정한 상관 무관 상한도 JSON에 있다. 모두 제조된 시나리오이며 실제 Planck cross-shell 또는 cross-product covariance가 아니다. **Empirical/forecast `C_l`, 실제 high-mode 계수 크기, beam, component separation, foreground, E2E covariance, ℓ>32 꼬리는 UNKNOWN**이다.

## 검증과 경계

PR #538 draft의 `tests/test_power_envelope.py`: **12 passed**. PR #537의 표적 테스트: **9 passed**. 새 확장 테스트: **6 passed**. PR #537의 실제 로컬 source runner와 확장 envelope runner: 각각 **exit 0**. 첫 확장 runner 시도는 주석 누락으로 `SyntaxError` exit 1이었고 바로 수정했다. 독립 검토 중 극소 양의 radius가 제곱 연산에서 0으로 underflow하는 결함을 발견해, radius를 최대값으로 정규화한 Gram·witness 계산으로 수정했다. `1e-200`과 `1e200` radius를 동결된 실제 행렬에서 SVD와 비교하는 회귀가 통과했다. 최종 결과는 create-only `power_envelope_v2`; 이전 `v1`은 로컬 첫 계산 증거로 보존하고 게시 대상에서 제외한다. 명령과 파일 SHA는 `RUN_RECEIPT.json`에 보존한다.

독립 read-only reviewer는 수치 underflow와 실행 receipt 불일치를 수정 후 확인해 **scoped PASS**를 권고했다. ℓ17/24/32의 독립 least-squares 최대 차이는 `6.18e-16`이다. 전체 800열의 독립 재생성은 reviewer가 별도로 수행하지 않았으며, PR #537 로컬 source runner의 전 열 계산·주입 검증을 근거로 둔다.

Mask-geometric finite response, 실제 하늘의 누설, physical covariant EGS ε, Bianchi geometry-frame shear/tilt는 서로 다른 주장이다. ε1, almost-EGS covariant 시간·공간 미분 및 물리적 transfer가 없으므로 물리적 admission은 **HOLD**다. main merge 또는 detection/family identification 주장은 없다.
