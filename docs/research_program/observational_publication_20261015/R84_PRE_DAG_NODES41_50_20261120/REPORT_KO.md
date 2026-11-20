# R84 | R78 DAG 41–50번 사전 코딩 C1–C10 결과

**작성 2026-11-20 KST.** 시작 HEAD \`bdb70b3682c80e4738f61a2b718c4819d1872245\`, 기존 브랜치 \`research/r69-observable-physics-bridges-20261118\`. R78 원본 과학 DAG는 42개 역사 과학 노드 + source qualifier 11개 + 조건부 물리 결합 7개, 총 60개 노드/129개 edge로 그대로 두었다. 이 문서는 **코드 준비 및 source-conditional 계산 검증**의 완료 보고서이지 H04, V04 등의 과학 단계 완료 또는 출판 판정이 아니다.

## 1. 열 개 노드별 실제 준비 범위

| 번호 | ID | 계산 코드 또는 source 계약 | 원래 과학 상태 |
|---:|---|---|---|
| 41 | H04 | 기존 R83 H03 4×9와 공동 36×36 working covariance, 독립 source C 입력의 rank/Schur 검산 준비 | pending |
| 42 | H05 | 기존 X02 선행모형 비교의 estimand, source/mask 차이 추적 계약 | pending |
| 43 | H06 | H04/H05 수용조건에 종속된 출판 HOLD 판정 | pending |
| 44 | V01 | 기존 관측자, 물질, 정상계 상대 rapidity·속도 정의 및 frame 계약 보존 | completed_scoped |
| 45 | V02 | 기존 Planck 유한 local-boost 응답과 동일 입력·마스크·beam source 계약 보존 | completed_scoped |
| 46 | V03 | local boost와 다른 radial/temporal global tilt 전달함수의 필수 입력 계약 | completed_scoped |
| 47 | V04 | signed local/global Jacobian whitening·projection과 rank API, 합성 6차원 반례 검증 | pending |
| 48 | V05 | **실제 R65 NVSS 33,000 pixel·185 ring·3 flux bin**의 조건부 \(F\), \(dF/d\beta\) Fortran/NumPy 배치 계산 | pending |
| 49 | V06 | source-qualified 공동 null/독립 전달 없을 때 출판 HOLD | pending |
| 50 | B01 | 11개 Bianchi 표준 유형의 \((a_i,N_{ij})\), Jacobi·Codazzi rank, VI\(_{-1/9}\) 내부 분기 검사 | completed_scoped |

각 노드의 구체적 API, 남은 source 조건 및 현재 과학 상태는 \`CONTRACTS.json\`, \`C10_NODE_MATRIX.json\`에 machine-readable로 저장했다. 기존 42개 과학 노드의 원본 SHA와 상태는 변경하지 않았고, 과학 DAG NEXT_ID는 **SQ-CF4**로 유지했다.

## 2. 수리물리적 계산식과 source 의미

원래 R65/R74 3개 flux bin에서 \(N_{bg}\)는 실제 ring \(g\)별 선택된 count, \(n_i\)는 ICRS sourceward 단위벡터, \(k_b>0\)는 원래 radio count response, \(v_b\)는 원래 fitted 2D count dipole이다. 원래 \(\ell_{bi}=v_{bx}n_{ix}+v_{by}n_{iy}\)를 각 ring별로 안정적으로 log-sum-exp 정규화해
\[
p_{bi}=\frac{\exp(\ell_{bi}-\max_{j\in g_i}\ell_{bj})}{\sum_{j\in g_i}\exp(\ell_{bj}-\max_{k\in g_i}\ell_{bk})},
\quad a_{bi}=\frac{N_{bg_i}}{\sum_g N_{bg}}p_{bi}.
\]
\(\mu_{bg}=\sum_{i\in g}p_{bi}n_i\)에 대해 조건부 first-order beta score의 픽셀 가중벡터는
\[
s_{bi}=k_ba_{bi}(n_i-\mu_{bg_i}),\qquad
F_b(u)=\sum_i a_{bi}\mathbf 1(n_i\cdot u>0),\qquad
\partial_\beta F_b(u)=\sum_i s_{bi}\mathbf1(n_i\cdot u>0).
\]
원래 ring count \(N_{bg}\)와 ring 내부 source 정규화를 보존하므로 \(\sum_i a_{bi}=1\), \(\sum_i s_{bi}=0\)가 모든 bin에서 성립한다. 이는 **조건부 count 모델의 score**이고 실제 물리적 \(\beta_{\rm RO}\), \(G_F\), tilt 또는 우주론적 \(p\)값은 아니다. 원래 R74 CMB축의 3개 \(F\) 값은 각각 **0.512137514587746**, **0.512711680614939**, **0.512609784917573**이며 원래 저장 값과의 최대 차이는 약 \(10^{-15}\) 이하로 재현했다.

V04는 local Jacobian column의 whitened span을 먼저 제거하고, **외부에서 주어진 독립적** global response column의 projected singular rank를 계산하는 작은 API로 준비했다. 이는 샘플 합성예제에서만 새 global 방향 한 개를 얻었으며, 원래 자료에서 global tilt를 새로 식별한 것이 아니다. B01 11개 sign-pattern 대표는 Jacobi \(N^{ij}a_j=0\)를 만족하며 Codazzi map의 소스별 rank를 검산했다. 예외 VI\(_{-1/9}\)은 VI\(_h\) 내부 분기이며 별도의 열두 번째 유형이 아니다. 일반 all-\(m\) 편극 Einstein–Boltzmann native transfer를 구현하거나 검증했다고 주장하지 않는다.

## 3. C1–C10 단계별 근거

C1은 원래 \`R65/NVSS_CONDITIONAL_CARRIERS.npz\`, R74 source, R78 DAG의 SHA를 확인하고 기존 단일 방향별 NumPy ring source 32축×3bin 계산 **약 0.384342초(1회 측정)**을 기준으로 고정했다.

C2는 H04–H06/V01–V06/B01 소스, 수식, 정상계와 observer frame, 원래 상태를 분리해 계약으로 고정했다. C3은 ring-profiled score 미분, source-SHA binding, local/global rank projection, Bianchi Jacobi 및 미확보 물리적 null의 상태를 유도했다. C4는 배치 Fortran 연산의 범위, 메모리, 누락 데이터 계약과 테스트 DAG를 설정했다.

C5는 실패하는 기능 테스트를 실제 관찰한 뒤 \`htt/obsstat/p4_bianchi_fast.py\`, \`htt/obsstat/native/p4_conditional_axis_scan.f90\`, \`htt/obsstat/p4_lane.json\`, source 인증 임시 빌드와 테스트를 구현했다. Fortran 코드는 단일 원본 픽셀 순서를 유지하며 방향축마다 독립적으로 정규화된 세 bin의 \(F\), \(\partial_\beta F\)를 Kahan 누적한다. No fast-math, SHA/source-certified temporary binary, NumPy 기준 비교가 유지된다. C6은 기존 관련 연구 R49/R61/R64/R65/R66/R67/R69/R79–R83와 신규 R84를 합쳐 **204 PASS**, R78 strict **32 PASS**를 기록했다.

C7은 실제 R65/R74의 세 bin, R75 Bianchi atlas 및 H03 36×36 working covariance, 원래 pending/blocked 상태를 검증했다. H03 working source의 첫 9×9 cross-window block은 0이 아니며, \(\min\lambda(C_{36})\approx0.00101644\)로 양정성을 확인했다. 이것을 H04의 물리적 완성 PV/method covariance로 치환하지 않는다.

C8의 같은 메모리 내 정확히 동일한 33,000 pixel/185 ring/3bin/sky axis benchmark (OpenBLAS=1, 5회 중앙값):
| 방향축 | 최적화 NumPy | Fortran 12-thread | 배속 |
|---|---:|---:|---:|
| 32 | 0.004198 s | 0.002256 s | 1.86× |
| 96 | 0.013901 s | 0.003423 s | **4.06×** |
| 256 | 0.027562 s | 0.006066 s | **4.54×** |

모든 축과 bin에서 NumPy 대비 최대 \(F\) 차이는 \(7.8\times10^{-16}\), \(\partial_\beta F\) 차이는 \(8.9\times10^{-16}\) 이하이며 그보다 큰 정확도 손실을 허용하지 않았다. 원본에서 ring별 precompute 시간 약 0.02228초는 위 스캔 커널 배속에 포함되지 않는다.

C9는 **동일한 \(N=33{,}000\)행을 갖는 다른 방향 배열로 이전의 prepared score를 잘못 재사용할 수 있는 버그**를 RED 테스트에서 발견했다. 준비된 score에 정규화된 C-order 방향벡터의 SHA-256을 결합하고 모든 실행에서 검사하도록 수정했으며, 원본 source/permutation 재준비 및 \(SO(3)\) 공변성 테스트를 추가했다. 후속 source-bound benchmark: 96축 NumPy 0.014136932초, Fortran 12-thread 0.003060127초, **4.62배**, 수치 차이 \(9\times10^{-16}\) 이내. C9 관련 회귀 **208 PASS**, R78 엄격 검증 **32/32 PASS**.

C10은 당시 C7 검산의 단계별 결과를 덮어쓰지 않고 원래 C7 Git 증거로 복원했으며, C9 새로운 자동 backend가 담긴 \`C9_AUTO_RECHECK.json\`을 별도로 보존했다. 동일 범위 테스트와 DAG 검사 재실행은 **208 PASS 및 32/32 PASS**였다. 10개 노드별 준비 상태, source hash, 단계별 commit, 재현 명령 및 다음 연구 인계는 C10_NODE_MATRIX.json, PROVENANCE.json, HANDOFF_KO.md에 기록한다.

## 4. 남은 과학적 조건과 다음 행동

**컴퓨팅 결과:** R84 수치 커널은 source-conditional implementation-verified로 수용한다. 빠른 경로는 충분히 큰 NVSS 다중축 계산에서 source-hash-certified Fortran 12-thread를 기본 선택하고, 작은 입력, 컴파일 불가능 또는 인증 source 변경 시 검증된 NumPy reference로 전환한다. 기존 R79–R83의 기본 빠른 경로도 그대로 유지한다.

**아직 수용하지 않은 물리:** H04의 full correlated PV/zero-point/selection covariance, V04의 독립적인 local/global source transfer, V05의 계통·LSS·selection이 포함된 matched null, V06의 관측 우주론적 p값, B01/B02의 모든 Bianchi 유형 편극 all-\(m\) transfer는 확보하지 못했다. H04/H05/H06와 V04/V05/V06는 pending이고 V01–V03, B01은 기존 completed_scoped이다. 이들을 출판 완료나 실제 새로운 모형 검출로 승격하지 않는다.

**다음 실제 과학 DAG 노드:** \`SQ-CF4\`. Source-selected CF4 35,970개 그룹의 method zero-point, physical PV/selection covariance 및 heldout 검정을 원자료와 같은 식별 조건으로 수행해야 한다. 이후 새로운 코딩 준비를 명시적으로 요청한다면 다음 ordinal 51–60은 R78 최신 본문을 다시 읽고 확인해야 한다.
