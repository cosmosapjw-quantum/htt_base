# L02 실제 통계 family 실행 결과

원본 Planck 공통지원 계수로부터 **9 T + 8 E + 8 B 필드 행**의 ell=2/3 STF
형태·방향 통계량과 동일 제품의 TE/TB/EB 24쌍을 실제 계산했다. 해당 정의의 T
Q²/O 주축은 제품 전반에서 거의 직교한다. E/B의 같은 통계량은 제품에 따라 훨씬
넓게 변한다. 이는 가공 계수의 기술적 결과이며, 귀무법칙이나 유의확률을 제공하지 않는다.

Owner `obsstat`; scope 원본 cut-sky 공통지원 추정량의 형태·방향 기술; claim tier
`C0`; status `DIAGNOSTIC_ONLY`; transfer source `none`. 아래 결과의 canonical L02
완료 여부는 L01/X03 수용 및 별도 독립 검토 뒤에 결정한다. 이 패키지는 스스로
L02를 수용하거나 기존 42노드 상태를 변경하지 않았다.

## 실제 입력과 고정 선택 family

`htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz`의 SHA256은
`900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459`이며 실행 시 확인했다.
출처 설명은 같은 입력 디렉터리 `planck_loop5_result.json`이다. T는 NSIDE64
26,846개, E/B는 30,021개 픽셀에서 얻은 원본 유한차수 최소제곱 계수다. 단위는
microK_CMB, 기저는 Condon--Shortley orthonormal real m0/cos/sin이다. E/B 열은
각 ell 내부에서 교차 배치되어 있어 NPZ의 `column_spin_metadata_json`으로 분리하고
모든 ell/m/phase 표지를 검사했다. 이들은 한 물리적 하늘의 분할·가공 대안이다.

[STATISTIC_FAMILY.md](STATISTIC_FAMILY.md)는 새 descriptor 계산 전에 작성되었다.
프로젝트가 이미 입력 하늘과 역사적 결과를 보았으므로 이번 적용은 retrospective다.
새로운 사전등록이라는 주장을 하지 않는다. 역사적 p=.039는 입력·결과·선택기준으로
사용하지 않았다. 향후 동일 source/processing을 통과하는 null 행에는 이 알고리즘을
prospective하게 적용할 수 있으나, L03/L04가 귀무법칙과 전체 선택 보정을 충족해야 한다.

고정 family는 모든 제품의 C2/C3, 네 signed SO(3) descriptor, 명시된 O(3) 요약,
Q²/O 주축의 projectors 및 joint overlap, 세 Galactic Cartesian 외부축 방향,
모든 동일 제품 TE/TB/EB contraction과 축 overlap이다. 깊이 정보는 없으므로 깊이
선택을 만들지 않았다. 하늘에서 유리한 방향·제품을 최적화하지 않았다. 이 목록은
이전 연구에서 수행한 추가 선택을 지우지 않는다. 네 descriptor는 불완전한 orbit
signature이며 완전한 궤도 분류나 orbit 거리 최적화 결과가 아니다.

## 수치 결과

q=Q/||Q||, o=O/||O||, A_ij=o_iab o_jab로 정의한다. 주축은 q²와 A의 최대
고유값에 대응하는 headless axis이며 overlap은 두 rank-one projector의 trace다.
통상 문헌의 angular-momentum-dispersion 축과 같은 정의라고 가정하지 않는다.

| 필드 | signed tr(q³) 제품 범위 | octupole concentration 범위 | joint axis overlap² 범위 | headless axis 각도 범위 |
|---|---:|---:|---:|---:|
| T, 9행 | -0.233891–-0.141213 | 0.518158–0.521463 | 0.000000382075–0.00212603 | 87.3572°–89.9646° |
| E, 8행 | 0.0350572–0.237218 | 0.418593–0.514231 | 0.113727–0.825508 | 24.6909°–70.2916° |
| B, 8행 | -0.398356–-0.110508 | 0.416098–0.552785 | 0.0268142–0.314020 | 55.9183°–80.5754° |

각도는 arccos(sqrt(overlap²))의 기술적 변환이다. 위 범위는 제품 간 min/max이며
신뢰구간이나 독립 표본 산포가 아니다. T가 작고 E/B가 넓다는 사실만으로
cosmic alignment/비등방성 또는 편광 검출의 유의성을 평가할 수 없다.

검토용 특정 원본행 `SMICA_FULL`의 실제 값은 다음과 같다.

| 필드 | C2 [microK²] | C3 [microK²] | tr(q²A) | signed h | joint overlap² |
|---|---:|---:|---:|---:|---:|
| T | 285.239724 | 364.158458 | 0.475990490 | -0.0152815501 | 0.000342297919 |
| E | 0.0881122349 | 0.0268991977 | 0.348837321 | 0.106211083 | 0.190897045 |
| B | 0.0956765526 | 0.00828159184 | 0.240987949 | 0.175260939 | 0.0285670690 |

SMICA_FULL의 normalized Q contraction은 TE=-0.0159248790,
TB=-0.0630093002, EB=-0.481208654이며 O contraction은
TE=-0.140923987, TB=-0.575729541, EB=-0.0773476480이다.
T/편광 지원이 다르므로 이것은 가공 feature geometry이며 full-sky cross-spectrum이 아니다.
완전한 값·projector·상태는 `results/L02_ACTUAL_STATISTICS.json`, 25행 표는
`results/L02_feature_vectors.csv`, 그림은 `results/L02_actual_shape_and_orientation.png`
및 `.pdf`에 있다. 그림은 생성 후 직접 확인했으며 라벨·패리티·한 하늘 caveat가 보인다.

## 물리적 반사 규약과 검증

활성 O(3) 변환 M에 대해 Q'=p M Q M^T, O'=p M³ O이며 T/E의 p=1,
B의 p=det(M)이다. 따라서 공간반전의 harmonic 계수 인자는 T/E에서 (-1)^ell,
B에서 (-1)^(ell+1)이다. 이 E/B 관례는
[Zaldarriaga & Seljak, Phys. Rev. D 55, 1830 (1997)](https://arxiv.org/abs/astro-ph/9609170)의
even/odd 구분에 따른다. 새 Boltzmann solver나 ODE는 사용하지 않았다.

v_i=o_ijk q_jk라 두면 A'=MAM^T, v'=Mv, q'v'=p Mqv, A'v'=MAv가 된다.
그러므로 signed s=tr(q³)는 p를, normalized triple product h는 p det(M)를
얻는다. 이 직접 변환식을 구현하고 수치적으로 검사했다. T/E에서는 s가 even,
h가 odd이며 B에서는 s가 odd, h가 even이다. 모든 필드의 k=lambda_max(A),
tr(q²A), projector overlap은 O(3) even이다. B를 scalar처럼 반사하는 잘못된
shortcut이 이 부호 규칙을 위반함을 별도 falsifier가 확인한다.

| 검증 | 실제 결과 | 해석 한계 |
|---|---|---|
| independent complex-harmonic synthesis 대 Qnn/Onnn | 통과 | 두 기존 변환 함수를 단순 재비교하는 시험을 넘어 기저·sine 부호 확인 |
| 실제 25행 × 18 SO(3)/improper/inversion/mirror 변환 | 450개 통과 | 표본 수치 검증, 모든 입력의 형식증명 아님 |
| 실제 24 cross-field 쌍 × 18 변환 | 432개 통과 | TB/EB odd 및 TE even 검사 |
| signed shape 최대 절대오차 | 1.88738e-15 | 허용오차 2e-11 |
| projector covariance 최대 절대오차 | 7.10543e-15 | fixed-axis 값 자체의 불변성을 주장하지 않음 |
| cross-field 최대 절대오차 | 3.38618e-15 | 통계적 covariance나 null calibration 아님 |
| zero/near-degenerate axis·chirality, scale 1e±200 | 통과 | undefined는 UNKNOWN, 유효한 h=0은 0으로 유지 |
| targeted tests | 16 passed, 2.73 s | 새 패키지 14개 + 기존 tensor feature 2개; 전체 repo 시험 아님 |

새 패키지에서 실질적 수치 실패는 관측되지 않았다. 최초 테스트 명령의 session ID를
출력에서 보존하지 못해 다음 진단에서 종료를 확인한 뒤 같은 테스트를 한 번 더
실행했고, 위 16-pass는 두 번째 실제 관측 출력이다. 첫 명령을 별도 수용 증거로
계수하지 않는다. 추가 실험이나 원본 계수 생성은 재실행하지 않았다.

공식 `.venv/bin/python` Python 3.12.3, NumPy 2.5.4, SciPy 1.18.1을 사용했고
BLAS/OMP/MKL 최대 thread를 2로 두었다. 시작 branch는
`research/htt-sixpaper-goals-robustness-20261018`, HEAD는
`1e095a2749cce9b28e45aac043a82218c21f84e5`다. 다른 lane의 untracked 파일을 보존하고
이 디렉터리만 작성했다. native worker 요청은 gpt-6.1-sol/high였으며 독립 runtime
metadata가 없으므로 관측 model/effort는 UNKNOWN이다.

실행 명령은 repo root에서 다음과 같다. 결과 생성은 create-only이므로 기존 결과가
있으면 덮어쓰지 않고 종료한다. 기존 결과를 확인하기 위한 재생성은 필요하지 않다.

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python -m pytest docs/research_program/observational_publication_20261015/CONTINUATION_20261018/L02_EXECUTION_20261018/test_statistic_family.py tests/obsstat/test_reboot_tensor_features.py -q
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/CONTINUATION_20261018/L02_EXECUTION_20261018/statistic_family.py
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/CONTINUATION_20261018/L02_EXECUTION_20261018/plot_statistic_family.py
```

## Claim audit와 다음 소비 단계

기존 `obsstat/reboot_tensor_features.py`와 `planck_lowell_irrep_projection.py`를
재사용했고 코드·수치 산물의 정체성은 결과 JSON 안에 기록했다. 신규 raw sky
data, independent sky, p-value, 물리적 posterior 또는 native family identification은 없다.
네 descriptor의 구현/실행과 metamorphic test 통과를 주장할 수 있고, 완전한 orbit
식별·물리적 parity violation·우주론적 anomaly는 이 증거로 주장할 수 없다.

실질적 kill switch는 입력 SHA/기저/support 변경, B axial factor 누락, 정의되지 않은
정규화·축을 숫자로 채움, 또는 이 제품들을 independent sky/null bank로 사용함이다.
원본 estimator의 E/B high-ell leakage와 편광 변화의 원인·uncertainty는 미측정이다.
이번 signed 값의 부호 자체가 물리적 반사대칭 위반 증거는 아니다.

다음 단계는 독립 검토자가 실제 코드·원본 metadata·출력·시험을 검토하는 것이다.
L01의 새 native matched 계수가 준비되면 원본 30,021-pixel 결과와 혼동하지 않고
명시된 estimator identity 아래 별도 적용해야 한다. L03 source-matched joint
signal/noise/systematics law가 없으므로 L04 corrected rank는 아직 생성할 수 없다.
