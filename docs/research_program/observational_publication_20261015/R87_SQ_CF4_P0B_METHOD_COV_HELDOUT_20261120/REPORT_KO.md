# R87 · SQ-CF4 P0-B 실제 그룹별 방법 보정·PV·selection/heldout 연구

**일시 2026-11-20 KST. 과학 판정: SOURCE-DIAGNOSTIC VERIFIED, FULL PHYSICAL C / INDEPENDENT COVERAGE BLOCKED.**

## 1. 실제 수행한 source 분석과 재현

원본 CDS CF4 table3/table4/ReadMe (38,053 group)와 기존 R54/R58 selected CF4 35,970-group NPZ의 byte SHA를 확인하고 1PGC group-ID를 정확하게 조인했다. 원본 raw group moduli, position, source category는 수정하지 않았다. Table3의 일곱 presence indicator와 **실제 각 방법별 group modulus 및 일부 per-method error**를 추출했다.

| 방법 | 원본 method-present group | 선택 group | 선택 비율 |
|---|---:|---:|---:|
| CAL | 336 | 11 | 3.27% |
| SNIA | 945 | 854 | 90.37% |
| FP | 27,602 | 27,509 | 99.66% |
| TF | 10,035 | 8,343 | 83.14% |
| SBFO | 175 | 15 | 8.57% |
| SBFI | 55 | 46 | 83.64% |
| SNII | 94 | 60 | 63.83% |

**이 비율은 이번 분석에서 published CF4 catalog 그룹이 포함되는 조건부 비율**이지 CF4에 실리지 않은 은하까지 포함한 survey selection/completeness가 아니다. Source-selection angle별로 RA [0,90),[90,180),[180,270),[270,360)에서 선택/원본 group 비율은 3737/4194, 13421/14066, 15810/16443, 3002/3350이다. 4개 정해진 방향영역은 source deterministic mask stratification이다.

원본 일곱 indicator의 multi-positive group은 926개다. CAL의 별도 e_DMcal이 제공되지 않으므로 weighted contrast는 SNIA,FP,TF,SBFO,SBFI,SNII만 사용한다. 여기서 **둘 이상 방법+실제 sigma가 존재하는 group은 922개**. 나머지 4개는 CAL+한 개의 error-bearing 방법만 있다. 일곱 presence가 모두 0인 group 185개 외에 CAL만 기록된 2개 group(ID 20679, 59927)이 존재한다. 따라서 여섯 방법 sigma-bearing zero group은 187개. 여러 method rows를 galaxy group의 독립적인 cosmological replication으로 세지 않았다.

## 2. 그룹 내 method contrast와 source-conditioned 식별성

동일 물리 그룹의 여러 방법 distance modulus에 대해 group-common amplitude a_g를 nuisance profile하는 정확한 weighted graph Laplacian:
\[
  P_g={\rm diag}(w_g)-{w_gw_g^\top\over\sum_mw_{gm}},\quad
  F=\sum_gP_g,\quad b=\sum_gP_g\mu_g,\quad P_g\mathbf1=0.
\]
Source 실제 six-method network는 **rank=5**다. SNIA=0은 calibration reference 좌표 gauge이며 실제 SN Ia 절대 zero-point 보정이 확실하다는 뜻이 아니다. Source post-intercalibrated residual moduli의 동일 그룹 common-shift/PV 부재 방향과 method offset을 구분한 결과:
| 방법 | 잔여 \(\delta_m-\delta_{\mathrm{SNIA}}\) (mag) | 가정된 diagonal law working SE (mag) |
|---|---:|---:|
| SNIA | 0 (gauge) | 미정 |
| FP | −0.12135 | 0.01568 |
| TF | −0.17740 | 0.01653 |
| SBFO | −0.29381 | 0.06721 |
| SBFI | −0.11105 | 0.02335 |
| SNII | +0.04683 | 0.08131 |

**주의:** 이 SE는 조건부 residual weights의 수치 Fisher inversion 값일 뿐 실제 독립 posterior의 1σ가 아니다. 원본 table3 그룹 방법별 값은 이미 CF4 MCMC intercalibration을 거친 산물이므로 교차방법 독립 likelihood나 true calibration systematic uncertainty \(\Sigma_{\rm cal}\)을 이 표만으로 추론할 수 없다. 원본 그룹을 method-pair 독립 sky draws로 복제하지 않았다.

4개의 fixed ICRS RA block에서 training method graph를 추정하고 test 그룹의 profile contrast loss를 out-of-sample 평가했다. 모든 train/test 1PGC group ID 교집합은 정확히 0이고 모든 training source rank 5다. Test group 3737,13421,15810,3002, overlap-contributing test group 196,252,337,137. Heldout residual loss \(L_{\rm heldout}(\widehat\delta)-L_{\rm heldout}(0)\) 는 약 −30.66,−4.22,−42.07,−25.20. **이는 global upstream calibration을 거친 데이터의 spatial residual predictive diagnostic**이며 진짜 independent upstream calibration heldout coverage/null 또는 해당 loss에 대한 cosmological p-value가 아니다.

## 3. PV covariance의 물리적 해석과 정확한 식별성 한계

기존 htt.obsstat.pv_covariance의 bulk+shear 공간 coherent mode source U를 실제 선택 CF4 그룹 위치에 투영하고, 아직 **관측에서 보정되지 않은 진폭을 시나리오 가정**으로 넣어 Woodbury로 계산했다.

| 조건부 PV prior 시나리오 | H03 최대 계수 이동 (km/s/Mpc) | 계수 공분산 trace 비율 |
|---|---:|---:|
| shear 1.5 km/s/Mpc만, bulk=0 | 3.3e−12 | 31.75 |
| bulk 150 km/s만, shear=0 | 4.8983 | 1.48 |
| 두 coherent prior 함께 | 4.8983 | 32.22 |

왜 이런 차이가 발생하는지는 THEORY_KO.md에 증명했다. \(U=XA\), \(C=D+U\Lambda U^\top\)이면 generalized least squares \(\hat\beta_C=\hat\beta_D\)이지만 \({\rm Cov}_C\hat\beta={\rm Cov}_D\hat\beta+A\Lambda A^\top\). 실제 source PV shear \(d\,n_iE_{Aij}n_j\)가 H03 STF design과 정확히 겹치는 반면 radial PV bulk \(n_i B^i\)와 apparent Hubble dipole \(d\,n_i D^i\)는 원본 거리 변화로 구분된다. 실제 source shear-only projection residual ~1e−15 및 algebraic covariance identity relative residual ~1.41e−14으로 검산했다. 따라서 **추정 평균이 안정적이라는 것만으로 coherent PV uncertainty가 작다는 결론을 낼 수 없다.**

진짜 \(S_{\rm PV}\)는 잘 정의된 source-matched cosmological velocity field ensemble/linear covariance, observed positions/frame 및 uncertainty model을 필요로 한다. 위 assumed sigma_bulk/shear는 그 실제 source를 대체하지 않는다. 완전한 N×N correlated physical covariance를 구성·보정했다고 주장하지 않는다.

## 4. SQ-CF4 본래 P0-B 조건의 완수·차단 분리

| 과제 | 판정 | 직접 증거 |
|---|---|---|
| 원본 table3/table4 + selected 35,970 identity | VERIFIED | Pin SHA, selected group join, 7 method parity |
| 926 method overlaps / 922 error-bearing groups | NUMERICALLY CHECKED | RESULT + 13 source unit tests |
| Group-profiled method residual and gauge/graph theorem | DERIVED + NUMERICALLY CHECKED | Laplacian, independent two-method edge implementation |
| Exact 4 RA sky-block group-disjoint residual predictive diagnostic | NUMERICALLY CHECKED | 1PGC train/test overlap 0, loss differences |
| Source-selected method/sky **analysis** inclusion | NUMERICALLY CHECKED | released 38,053 vs selected 35,970 footprint |
| Low-rank PV model/normal-frame sensitivity | CONDITIONAL WORKING SCENARIO | source H03 and assumed bulk/shear priors |
| Independent CF4 pre-intercalibration zero-point posterior and J_cal | **BLOCKED_INPUT** | Published group moduli already calibrated; e_DMcal missing |
| Qualified true S_PV and selection covariance C_sel | **BLOCKED_INPUT** | No matched full independent source field ensemble and selection mock law |
| True independent upstream calibration heldout/astronomical coverage | **BLOCKED_INPUT** | Four sky splits occur downstream of global calibration |
| Actual physical H04 H(z,n), normal sigma, Pi or cosmic anomaly | NOT ADMITTED | R78 science gates unchanged, null absent |

**Result:** P0-B의 실제 가능한 code/source 분석은 실행했다. 그러나 원래 full physical C 및 독립 heldout calibration을 source-supported하게 완료할 수 없으므로 SQ-CF4 science gate는 계속 ready_scoped diagnostic, true physical likelihood status는 **BLOCKED_PHYSICAL_PV_CALIBRATION_SELECTION_AND_HELDOUT**이다. 원래 R78 DAG status/next SQ-CF4, P1–P6 paper claim gates, 291 software PR backlog를 변경하지 않는다. 물리적으로 정당한 \(\Pi\) / \(G_F\) / Bianchi family 판정은 여전히 미정이다.

## 5. 다음 최소 입력과 연구 순서

진짜 P0-B physical closure에는 원래 방법별 pre-intercalibration distance data/posterior chain 또는 CF4 intercalibration parameter covariance와 grouping Jacobian, selected 35,970 group에 대응하는 physically calibrated coherent PV field realizations/velocity covariance, unobserved selection function과 true selection-matched independent mock/heldout가 필요하다. Failing that, publish this **source-conditioned residual identification and real no-independent-posterior obstruction**. Next software step is **P0-C**, a fail-closed R78 60-node source-typed SQ-CF4 read-only dry-run adapter. This can run without pretending P0-B's physical covariance exists, but must return blocked on missing physics, never dispatch local agent. Do not run P0-C inside this P0-B request.

**References:** Tully et al. 2023 ApJ 944, 94 (doi:10.3847/1538-4357/ac94d8), EDD original CF4 group columns http://edd.ifa.hawaii.edu/describe_columns.php?table=kcf4allgroup; Duangchan et al., A&A 708 (2026), DOI 10.1051/0004-6361/202556645 (selection-matched CF4 mock forward modelling); Watkins et al., MNRAS 524 (2023), DOI 10.1093/mnras/stad1984 (group peculiar velocity covariance/estimator). Theoretical references motivate systematic separation; R87 real numbers are computed locally rather than copied from these papers.

**Current verification at P0-B (2026-11-21):** new R87 tests **13 PASS**; enlarged related R79–R87 **281 PASS**; R86 readiness **9 PASS**; R78 strict **32 PASS**. The 281 tests are a **scoped existing checkout**, not whole-repository clean CI. Two extra R87 regression tests verify the exact saved source-array SHA and JSON result, and the create-only CLI refuses to overwrite an existing output. Full physical PV/calibration/selection C, independent raw-method heldout and new astronomical significance remain **BLOCKED_INPUT**. No local agent START is issued.
