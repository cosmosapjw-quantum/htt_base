# R85 · 통합 R78 DAG 51–60번 노드 사전 코딩 C1–C10 최종 보고서

**2026-11-20 KST**, repository cosmosapjw-quantum/htt_base, branch research/r69-observable-physics-bridges-20261118. 시작 HEAD bcb1a26af18d6005a675caf1e87fde7563799855. 이 범위는 B02–B05와 K01–K06의 수치 구현·source 검증이며 원래 R78 과학 DAG의 60개 노드, 129개 의존 edge, 원본 42개 과학 node payload SHA e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d와 상태를 변경하지 않았다. NEXT science ID=SQ-CF4 유지.

## 1. 10개 노드별 실제 코드와 미해결 조건

| 순번 | ID | 구현 또는 검증한 계산 | 과학 상태 |
|---:|---|---|---|
| 51 | B02 | 외부 진짜 all-(ell,m) T/E/B 전달자료의 NPZ·SHA·mode/history/IC/units/frame schema 및 압축 제한 검사 | pending, 실제 source 부재 |
| 52 | B03 | 외부 response×polarized template의 직사각형 연산, source-conditional 선형대수 | pending, B02·Planck 실제 response 미확보 |
| 53 | B04 | source covariance로 whitening한 Bianchi-family template 공통 방향 principal angles와 rank, Bayes evidence는 없음 | pending |
| 54 | B05 | 독립 P5 논문 입력·claim gate HOLD | pending |
| 55 | K01 | 단일 정상계 \(\Theta,\sigma_{ij},A_i/c,\omega_i\)의 국소 optical directional H와 anti-symmetric radial blindness | completed_scoped 유지 |
| 56 | K02 | 실제 CF4 35,970 group × 네 거리창, 4 method intercept+8 apparent shape, 4×8 계수 및 32×32 source cross covariance, Fortran 가속 | completed_scoped 유지 |
| 57 | K03 | 진짜 Gaia 비방사형 source cross moment A(6,6), K(6,102), qH(6), n=755850의 byte SHA·SPD·whitened rank=6 | pending |
| 58 | K04 | 실제 전이행렬·noise C 입력이 있을 때만 적용 가능한 Cholesky whitening/rank 식별성 API | pending |
| 59 | K05 | CF4/Gaia/CMB의 동일 정상계·독립 source/cross covariance가 확보되지 않으면 통계 결합 HOLD | pending |
| 60 | K06 | P6 독립 논문 게이트 HOLD | pending |

구현과 물리적 근거 상태를 machine-readable로 R85/C10_NODE_MATRIX.json에 보존했다. B02를 위한 **물리적 all-m polarized Einstein–Boltzmann native solver를 개발하거나 생성하지 않았다.** 실제 T/E/B 전이·상태·이온화·recombination history, spectral convention, source frame과 null이 없기 때문이다. 외부 자료 구조를 통과한 합성 NPZ는 numerical fixture이며 source-qualified physical result가 아니다.

## 2. K02 물리식·이산화·재현

동일한 원본 CF4 group IDs 35,970개, selection NPZ SHA-256 86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c. 네 fixed retrospective windows zbar=(.025,.040,.060,.080), width .012. Source-conditional d_i=10^((DMzp_i-25)/5) Mpc, y_i=c z_CMB (c=299792.458 km/s), sigma_i=hypot(250,70 ln(10)/5 d_i eDM_i) km/s. 수학적으로 원래 K02 H03의 작업 모델이다. Source 12D design X=(4 method one-hot intercept d_i, 3 dipole d_i n_i, 5 orthonormal signed STF d_i T_A[n_i,n_i]); 원래 13-column 전체 monopole 추가항은 정확히 네 method intercept의 합이므로 rank 12다. 이 rank는 물리적 광학 \(\Theta/3,\sigma,A\) 식별성 판정이 아니고 source working profile의 8개 apparent 방향계수 식별성이다.

각 창의 w_ij=exp[-.5((z_i-zbar_j)/.012)^2]/sigma_i², F_j=X^T W_j X, b_j=X^T W_j y, \(\widehat\theta_j=F_j^{-1}b_j\). Full 32×32 shape covariance block:
\[
C^{(8)}_{jk}=\bigl[F_j^{-1}\,X^\top\operatorname{diag}(w_jw_k\sigma_i^2)X\,F_k^{-1}\bigr]_{4:12,4:12}.
\]
이 식은 동일 source를 중첩 사용한 4개 창의 off-diagonal block을 보존한다. 원래 QR+4개 12×35970 influence operator를 계산하는 대신 최적화된 NumPy BLAS 및 Fortran ISO_C_BINDING/OpenMP/Kahan source reducer에서 4개 12×12 정보행렬·score와 10개 쌍의 48×48 raw cross-information을 계산한 후 12×12 SPD Cholesky를 적용한다. n² covariance, 개별 source influence 전체 저장과 원본 파일 수정은 불필요하다.

원래 K02 소스의 4×8 방향별 계수와 비교한 Fortran 최대 절댓값 차이는 3.2068792066e-13 km/s/Mpc, 원래 32×32 covariance 차이 1.6098233857e-15 (km/s/Mpc)^2. 첫 비대각 8×8 cross block Frobenius norm 0.1751776127로 0이 아니다. 원본 K02 C32 최소 고유값 0.0031987567381873. Scalar optical leading z observer-to-source convention \(H_{\rm opt}(n)=\Theta/3-A\cdot n/c+\sigma_{nn}\), radial \(\omega_i\) null은 Wolfram에서 반대칭 n^T W n=0으로 검산했다. 이 물리식과 CF4 apparent shape8 사이의 적합한 source transfer는 아직 없다.

## 3. 실제 K03 Gaia 모멘트의 범위

External original source /mnt/extdrive/workdir/htt_open_data/k03_pm_20261023/cross_moments.npz, SHA256 70fc2fee88803a7211c1c157ff87b4adb05b0807a00c03dc38d51f31b3842662, sample n=755850, redshift approx [0.086345,4.62746], A (6×6), K (6×102), qH (6). Original A is symmetric SPD with minimum eigen ~6.832, whitened K rank=6. 이것은 **source-conditional moment의 기하학적 rank**이며 observed independent matter vorticity/acceleration or source-matched Gaia+CF4 joint normal-frame posterior가 아니다. K03 자체의 source/selection/scan covariance, high-z optical/Jacobi transport, 대응 normal frame과 calibrated null은 미해결이다.

## 4. 10단계 수치 작업과 실제 성능

C1: immutable CF4/K03/B01 source SHA와 original four-window K02 QR/32D output baseline 고정. 기존 원본 QR 3-run median ~0.104368s. C2: 열 노드 source/body/frame/null/claim typed 계약. C3: 원래 12D gauge, 32D shared source covariance, K01 radial blindness, B02 external all-m authenticity acceptance 유도. C4: 메모리 O(N×12+N×4+48²), OpenMP/NumPy, 외부 solver 범위 금지, 순차 checkpoint와 정확도 계약.

C5: 신규 API htt/obsstat/p5p6_fast.py, source-hash native k02_joint_source.f90, policy p5p6_lane.json, source 빌드 스크립트, 신규 12개 TDD RED→GREEN 회귀. C6: 기존 R79–R84 관련 테스트까지 256 PASS, R78 32/32 strict. C7: 원본 K02 독립 QR source replay + K03 진짜 6×102 + B01 11 canonical types + B02 source report. 초기에 source verifier가 첫 네 method one-hot 열을 방향벡터로 읽는 오류를 발견, n_J2000 원본을 직접 사용하도록 수정하고 재현했다. C8: 동일 원본 35,970개 그룹, 4×12+32D, BLAS=1 반복 실행:
| 계산 경로 | 5-run median | 기존 QR 대비 |
|---|---:|---:|
| 원래 K02 QR/influence | 0.095092 s | 1.00× |
| 최적화 NumPy BLAS | 0.008568 s | 11.10× |
| Fortran 12-thread | 0.005672 s | **16.76×** |

Fortran은 이미 벡터화된 NumPy 대비 1.51045×였고 원본 수치 오차 ≤2e-10 relative acceptance를 만족해 default auto로 선정했다. 독립 auto 5-run에서는 source+binary certification 후 NumPy 대비 1.593×, original QR 대비 17.68×. 모두 **in-memory K02 working core**이며 CF4 full input, calibrated \(C_{\rm PV}\)/method, total Einstein–Boltzmann/CMB null 계산을 포함하지 않는다.

C9: 적대적 TDD에서 같은 35,970행의 서로 다른 X와 W를 조합해도 초기 backend가 입력을 받아들이는 source alignment bug를 검출했다. Source group_id, X, W, sigma, y의 canonical C-order SHA-256을 최초 준비에 고정하고 매 계산 호출 검사. 또 B03 유효한 비정방 전달·template 곱에서 비정방 shape의 공동 np.isfinite([M,T])가 실패하던 문제를 독립 finite 검사로 해결. 최종 회귀 **259 PASS**, R78 strict **32/32 PASS**. Source SHA 확인 비용을 포함해 재측정한 Fortran12/NumPy 배속 **1.4487169×**, 이전 저장 원본 QR 대비 **12.4947×**. 해시 검산 후에도 원래 수치 차이 최대 7.19e-12 (shape8 vs optimized NumPy), 2.0e-15 (C32 vs NumPy)로 정확도 유지.

C10: 원래 R78 60/42 science states unchanged, 현재 SQ-CF4, source/code hashes, 10노드 software/physics matrix, 검증·수치성능의 범위, 원격 Git SHA, 다음 실제 연구 인계 저장. User의 기존 unrelated untracked/dirty R83 files는 stage-scoped Git에서 제외한다. Whole repository clean-checkout test 및 native independent solver verification은 수행했다고 주장하지 않는다.

## 5. 다음 과학 실행

컴퓨팅적으로 R78의 1–60번 노드에는 각 주제에 맞는 범위 한정 수치 준비·source validation 또는 명시적 누락 입력 계약이 갖추어졌다. 이것은 **60개 과학 노드가 완료됐다는 뜻이 아니다**. 실제 R78 다음 ID=SQ-CF4를 변함없이 유지하며, 원래 CF4 selected 35,970 group method-family/zero-point, correlated peculiar velocity/selection covariance와 heldout coverage가 먼저 필요하다. 이후 B02 외부 genuine polarized transfer/T/E/B all-m/primordial mode/history source, K03 비방사형 normal-frame observable, K04–K05 optical and joint-null 확보가 과학적 종속 단계다. 기존 P5/P6 journal 준비는 pending/HOLD다.
