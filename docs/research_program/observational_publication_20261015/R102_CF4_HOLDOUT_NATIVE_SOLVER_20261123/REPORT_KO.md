# R102 통합 연구 보고서: SQ-CF4 Selection·Holdout, Commander/SDSS 원자료 분석 및 Native Bianchi Solver (`M08/M09/A03`)

- 기준 연구 브랜치: `research/r69-observable-physics-bridges-20261118`
- 선행 R101 HEAD: `c69fa980c5efb360f38e0b01c4c9476a292d1350`
- 과학 정본(SSOT): `docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json` (SHA-256 `90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11`)
- Canonical 42-노드 기준선: `PUBLICATION_DAG.json` (정규 정렬 JSON SHA-256 `e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d`)
- 권고 `next_id`: `SQ-CF4` (`new_science_acceptances = 0`)

---

## 1. 과학적 주장 계층 분리 (Claim Quarantine Summary)

본 작업(R102)은 네 가지 계층을 엄격히 분리하여 보고합니다.

| 계층 | R102 상태 | 근거 및 제한 조건 |
|---|---|---|
| 1. Native 구현·수치 검증 (`M08/M09/A03`) | `COMPLETE_SCOPED_R102` | General-Lie $T,E,B,V$ transport, 이동 전자 프레임 Thomson 산란, 4채널 tilted HYREC-2, 결합 Bianchi Einstein–Boltzmann 7개 패밀리 수렴 및 geodesic Sachs oracle 일치를 $10^{-9}\text{--}10^{-15}$ 정밀도로 검증 |
| 2. 원자료 기반 source-conditioned 분석 (`SQ-CF4`, `D03` 1쌍) | `PARTIAL_SCOPED` | 8,885행 6dFGSv group-blocked 5-fold CV, 35,970개 CF4 Table-3 군·4,000,000행 SDSS randoms 기하 검증, Commander PR3 + FFP10 `00000` 1쌍 정렬·pseudo-$C_\ell$ 항등성 검사 완료 |
| 3. 교정된 관측 추론 (`calibrated_p`, `physical_Pi`, `physical_GF`) | `BLOCKED_MISSING_UPSTREAM_INPUTS` | raw FFP10 다중 앙상블(`N>=300`+beam 보정), 원시 CF4 독립 영점/선택/상관 $S_{PV}$ 공분산 부재 → 모든 영점/물리 초과 확률은 `null` 유지 |
| 4. Bianchi 패밀리 귀속 (`Bianchi_family_attribution`) | `BLOCKED_ATLAS_UNQUALIFIED_AND_MISSING_NULL` | `atlas_qualified_for_planck_family_id = false`, `commander_null_qualified = false`, `Bianchi_family_attribution = null` |

---

## 2. 외부 원자료 Bounded 취득 및 Commander PR3 / FFP10 `00000` 정렬 (`D03`)

### 2.1 Bounded 취득 ([`ACQUISITION_RECEIPT.json`](ACQUISITION_RECEIPT.json))
- **SDSS randoms (`SDSS_randoms_public.dat`)**: `284,000,071 B`, MD5 `8627b4063e8a71572e333e0ac65d6657`, SHA-256 `2ec2853acd263b91bf679764fed22fd2b1edc34d4d08dd5d1c4f4e311e44f848`, 4,000,000행(`# RA Dec zcmb nbar`), 상태 `FETCHED_PROVIDER_MD5_VERIFIED`.
- **Planck PR3 FFP10 Noise MC `00000` (`dx12_v3_commander_noise_mc_00000_raw.fits`)**: `scripts/r102/acquire_commander_pair.py`가 `HTTP 200`, `Content-Type: image/fits`, `Content-Disposition` 파일명, `Transfer-Encoding: chunked` 단일 프레이밍, 엄격한 `<= 603,987,840 B` 상한 및 FITS 구조(`NSIDE=2048`, `RING`, `K_CMB`, 채널당 `50,331,648` 유한 픽셀) 검증 후 무덮어쓰기(`os.link`) 설치. MD5 `573a0706a101015ff77ea9aafce9258e`, SHA-256 `7c25b9674652e117362c69f57948d4b5346f14c7426486241c39de316c74e3cb`, `commander_null_qualified: false`.

### 2.2 Commander Signal+Noise 1쌍 vs 관측치 정렬 검사 ([`COMMANDER_PAIR_00000_CHECK.json`](COMMANDER_PAIR_00000_CHECK.json))
- `scripts/r102/commander_pair_check.py` (`runtime_s = 304.49`):
  - `NESTED` 지도(`observed_commander_pr3`, `mask_int`, `mask_pol`)를 `RING`으로 정확히 재배열(`reordered_nested_to_ring_for_analysis = true`)하고, `K_CMB` 단위 및 `INT`(`fsky = 0.779412`) / `POL`(`fsky = 0.781440`) 분리 마스크를 적용.
  - `TT, EE, BB`에서 $C_\ell(s+n) = C_\ell(s) + C_\ell(n) + 2C_\ell(s\times n)$ 항등성 상대 오차 `7.5939e-16`.
  - 신호 vs 잡음 픽셀 강도 상관계수 `-0.004946`; $\ell=2..64$ 평균 $C_\ell^{TT}\,[\mu\mathrm{K}^2]$: `sig = 31.5901`, `noi = 0.001073`, `s_plus_n = 31.5722`, `obs = 18.8903` (raw MC에는 PR3 관측 map과 달리 `5'` 빔 HDU 보정이 포함되지 않음을 명시, `commander_null_qualified = false`).

---

## 3. SQ-CF4 Selection·Group Holdout, SDSS Randoms 및 36D 성분별 탄젠트 ([`CF4_SELECTION_HOLDOUT_RESULTS.json`](CF4_SELECTION_HOLDOUT_RESULTS.json))

### 3.1 6dFGSv 8,885행 Selection Uncertainty & Zero-Leakage 5-Fold Group CV
- R101/R100 기준선 정확 재현: `r101_replay_mix_minus_zero = 27.34102020`, `r100_probit_beta_replay_max_abs_err = 2.5900e-8` (`grad_norm = 3.74e-13`, `beta_hat = [0.83897, -0.17491, -0.98518, 0.18097]`).
- **선택 매개변수 $\beta$ 불확실성 전파 (`htt/htt/htt/infer/cf4_group_holdout.py`)**:
  - 전 코호트 plug-in $\Delta\log L_{\rm mix-zero} = 27.3410$; 해석적 기울기 + Laplace Fisher 공분산 delta-method 표준편차 `3.0480`, Laplace 주변화 `30.3900`; 40회 군집 부트스트랩 delta-method 표준편차 `3.2047`, 부트스트랩 주변화 `29.4749`.
- **Zero-Leakage Group-Blocked 5-Fold CV**:
  - `6dF groupid_raw`(-1 비군집 센티넬 보존) + Table-2 `pgc` 연결(`7,183`개 클러스터): train/test 클러스터 교집합 0건 검증, held-out probit 로그우도 합 `-4282.2460`, held-out plug-in 합 `30.7511`, held-out 주변화 합 `31.2203`.
  - **CF4 `pgc1` 연결 민감도 (`pgc1_linked_group_cv`)**: Table-2 `pgc1`까지 연결 시 `6,254`개 클러스터(6dF 미군집 쌍 929건 통합), zero leakage 확인, held-out probit 로그우도 `-4283.8750`, plug-in 합 `26.7070`, 주변화 합 `27.3839`.
- **다중 매칭 모호성 4행 민감도 (`15"`, `500 km/s`)**: `unique_only_r101 = 27.3410` (7,190/1,695), `resolve_closest = 27.4151` (7,194/1,691), `exclude_ambiguous = 27.2504` (8,881행 평가, `counts <= 1`).

### 3.2 4,000,000행 `SDSS_randoms_public.dat` 선택 기하 및 SDSS Holdout
- `RA=[109.744, 261.878] deg`, `Dec=[-3.749, 70.279] deg`, `zcmb=[0.00334, 0.10007]` (`mean=0.06717`), `NSIDE=32` 마스크 내 포함률 `1.0` (전체 `0.9796`).
- Footprint 구면조화 교차상관($\ell=1..6$): `[0.9978, 0.9913, 0.9773, 0.9690, 0.9390, 0.8890]`; 마스크 내 적색편이 분포 총변동 거리(TVD) `0.02431`.
- SDSS 마스크 내 34,059행 `25,545`개 클러스터(`idgroupt17 == 0` 비군집 보존) 5-fold CV: `r100_beta_replay_max_abs_err = 2.7124e-7`, full probit 로그우도 `-4102.2366`, 5-fold held-out 합 `-4110.1123`.

### 3.3 CF4 36D 6성분 예측 공분산 탄젠트 & Quadrant/Calibrator 감사
- 6개 물리 성분(`diag_meas_plus_nl150`, `cal_plus_cut`, `sel_mag_tilt`, `spv_low_k`, `spv_inherited_k`, `spv_high_k`) 분해 trace 항등성 오차 `5.4210e-19`, `cal_plus_cut` 유한차분(FD) 검증 오차 `5.3915e-9`.
- **오일러 동차성 항등식 검증**: 최대 오차 `6.3949e-14` (`mean` 차수 0: `1.82e-17`, `predictive_cov` 차수 1: `2.17e-18`, `chi2` 차수 -1: `8.88e-15`, `logdet` 차수 $m_{\rm test}=18$: `6.39e-14`, `log_density`: `3.46e-14`).
- `cal_plus_cut` trace `0.006612` (`51.9%` of total trace `0.01275`), `spv_inherited_k`가 $\chi^2$ 및 $\log\det$ 민감도의 최대 성분(`chi2_tangent = -5.9478`, `logdet_tangent = +8.1118`).
- Table-3 `35,970` 선택 군 중 유한 영점 교정기(calibrator) 중첩 군은 **11개**뿐임(RA 사분면 Q0: 3,737/2, Q1: 13,421/1, Q2: 15,810/6, Q3: 3,002/2) → 독립 영점·selection 공분산 대체 불가 확인.

---

## 4. Native Low-$\ell$ Polarized Bianchi Solver (`M08`, `M09`, `A03`)

### 4.1 구현 아키텍처
1. **`M08` 일반 Lie 군 Polarized Transport ([`htt/bass/transport/general_lie_stokes.py`](../../../../htt/bass/transport/general_lie_stokes.py))**:
   - 임의의 적격 3D Lie 대수 $(a, n)$ (`Jacobi n·a = 0`)에서 공간 연결 $\Gamma^k{}_{ij}$와 screen-transport spin 연결을 구성, $T, E, B, V$ 스핀 조화 사다리($\ell_{\max}$ 결합-$m$)를 진화.
   - Rank-9 Thomson 산란과 $+\sqrt{6}/10$ `T2-E2` 결합 부호 일치, Alexander SDIRK(2,2) + $9\times 9$ Schur 축약으로 강직(stiff) $s=10^{20}$까지 모노폴 보존.
2. **`M08` 이동 전자 프레임 Thomson 충돌 ([`htt/bass/collision/moving_thomson.py`](../../../../htt/bass/collision/moving_thomson.py))**:
   - cancellation-free $D=\Gamma(1-\boldsymbol{\beta}\cdot\hat{\mathbf{n}})$, $D^4$ 복사이동, $d\Omega_{\rm normal}=D^2 d\Omega'$, Wigner null-gauge screen 회전, `rest_time` vs `conserved_anchor` 시계 분리 및 상대론적 4-force 직교성($u_b\cdot F_{\rm rad}=0$).
3. **`M09` 4채널 Tilted HYREC-2 재결합 ([`htt/bass/recombination/tilted_hyrec.py`](../../../../htt/bass/recombination/tilted_hyrec.py))**:
   - 금지된 전역 $H \to \Gamma H$ 대체를 제거하고 `reaction_clock_rate_s = Gamma * H_n`, `proper_hydrogen_density_cm3 = N_H / (Gamma * a^3)`, `lya_escape_expansion_s = H_esc` (수정된 물리적 Sobolev 광학 깊이 $\tau_S(\hat{\mathbf{n}}) = A_{\mathrm{Ly}\alpha} n_{1s} / (\mathrm{LYA\_FACT\_CGS} \cdot K(\hat{\mathbf{n}}))$, $A_{\mathrm{Ly}\alpha}=6.2649\times 10^8\,\mathrm{s}^{-1}$), `matter_expansion_rate_s = Theta_b/3`로 분리.
   - Planck 2018 FLRW 기준선 일치 및 `x_HII, T_m` vs 4채널 야코비안/탄젠트 유한차분 일치 검증.
4. **`M08/A03` 결합 Einstein–Euler–Boltzmann Solver ([`htt/bass/transport/coupled_einstein_boltzmann.py`](../../../../htt/bass/transport/coupled_einstein_boltzmann.py))**:
   - 동차 Bianchi 배경 $(H_n, \sigma_{ij}, a_i, n_{ij})$, tilt 바리온 유체 $\mathbf{v}_b$, CDM 속도, 복사 모멘트 피드백($\pi_\gamma$, `n_picard=2`)을 결합하고 Class-A (`a == 0` 수치 잡음 $10^{-24}$ 가드 포함)에서 Bianchi IX의 구조 고윳값 보존.

### 4.2 7개 패밀리 수치 수렴·제약·Oracle 결과 ([`NATIVE_SOLVER_CONVERGENCE.json`](NATIVE_SOLVER_CONVERGENCE.json))

| 패밀리 ($\epsilon=10^{-5}$) | Class | `max_jacobi` | `max_hamiltonian` | `max_codazzi` | `IX`/`family` `L8 vs L12` ($B$) | 시간 격자 비율 (`d12/d24`) | Lie vs Ray Oracle ($T,E,B,V$ max) |
|---|---|---|---|---|---|---|---|
| `FLRW` ($\epsilon=0$) | A | `0.0` | `1.323e-09` | `0.0` | `—` | `—` | `—` |
| `I` | A | `0.0` | `1.204e-09` | `7.735e-09` | `7.169e-06` | `3.293` | `1.257e-14` |
| `V` | B | `2.848e-22` | `6.489e-10` | `7.702e-09` | `9.454e-09` | `3.291` | `1.495e-14` |
| `VII_h` (+1) | B | `1.250e-20` | `9.403e-10` | `7.983e-09` | `4.693e-09` | `3.292` | `1.542e-14` |
| `VII_h_minus` (-1) | B | `1.274e-20` | `8.349e-10` | `7.994e-09` | `—` | `—` | `—` |
| `VI_h` | B | `2.697e-21` | `8.032e-10` | `5.212e-09` | `5.976e-09` | `3.556` | `—` |
| `VI_-1/9` | B | `2.215e-21` | `7.988e-10` | `7.496e-09` | `1.592e-09` | `3.806` | `9.101e-14` |
| `IX` | A | `1.514e-22` | `7.843e-10` | `4.744e-09` | `1.077e-09` | `3.286` | `2.188e-14` |

- Moving Thomson: 평형 잔차 `1.013e-15`, 4-force 각적분 vs 공변 상대차 `2.429e-13`, 직교성 오차 $u_b\cdot F_{\rm rad} \le 4.359\times 10^{-15}$.
- Tilted HYREC vs 금지 $H \to \Gamma H$: `|beta|=0.04984`에서 `max_rel_xe_diff = 0.001234`, `|beta|=0.09968`에서 `0.004943` (정확한 $4.01\times$, $O(\beta^2)$ 스케일링).
- Coupled `ref 1 -> 2 -> 4` 전체 결합 세분화(`VII_h`, `VI_-1/9`, `IX`): 상태 상대 변화가 각각 `5.987e-3 -> 1.691e-3`, `9.878e-5 -> 2.524e-5`, `1.871e-3 -> 5.291e-4`로 2차 이상 감소하며, `ref4` 제약 오차도 `max_jacobi <= 2.203e-20`, `max_ham <= 1.139e-9`, `max_codazzi <= 8.743e-9` 유지.

---

## 5. R78 60-노드 과학 DAG 보존 & 테스트·독립 검토 검증

- `scripts/r102/program.py` → [`NODE60_EXECUTION.json`](NODE60_EXECUTION.json), [`NODE60_EXECUTION.md`](NODE60_EXECUTION.md):
  - `INTEGRATED_DAG.json` SHA-256 `90aba8c1...`, 42-노드 `PUBLICATION_DAG.json` 정규 해시 `e3264e10...`, 60노드/129간선/`new_science_acceptances = 0`/`next_id = "SQ-CF4"` 모두 엄격 보존.
  - `scripts.r102.program check-node --node SQ-CF4 --phase science` 실행 시 `"science_status": "ready_scoped"`, `"title": "CF4 selected-group method/PV calibration"`, 종료 코드 `3` 반환 확인.
- **독립 검토([`INDEPENDENT_REVIEW.md`](INDEPENDENT_REVIEW.md))**: read-only `research` subagent(`6c76c752-9941-40a7-8ee2-1c74f3ff5dc0`)가 초기 `CHANGES_REQUESTED`(CRITICAL 1건, MAJOR 2건, MINOR 4건)를 보고했으며, 4건의 필수 조치와 관련 MINOR 항목을 모두 수정·재생성 후 재검증 완료.
- **전체 R102 + R101 + R86 최종 회귀 테스트** (13개 파일, 마지막 코드/아티팩트 수정 이후 실행):
  - `75 passed, 34 subtests passed in 212.71s (0:03:32)` (실패 0건, 스킵 0건).
