# HTT R100 최종 연구 보고서 (SQ-CF4 Source-Law Completion · Bianchi Optical Transfer · Multi-Probe Analysis)

## 0. 요약 및 과학적 경계 (Claim Firewall)
- **연구 범위**: R99를 출발점으로 22 MB 상한 내 상위 원자료 수집(`SDSS_PV_public.dat`, `6dFGSv table1.txt`), CF4 계보·부호 감사 및 `[1e-4, 1.0] h/Mpc` 3-band matrix-free 상관 특이속도 공분산(`R=5,10,20 Mpc/h`, 4 관측량), 유한 적색편이 위치 드리프트(cosmic parallax) 전이핵 $T_C/T_G$, LoTSS DR3 외곽 노출·음수이항(`NB1`/`NB2_CoxLSS`)·재선택 비선형 쌍극자, Gaia/Quaia rank-47 부분공간 결합 식별성, 그리고 `Radau` 자체일관적 Bianchi 복사-전단-바리온 Thomson 결합 반작용(`k=0..4`, `PHY01–07`)을 실제로 구현·실행·검증하였다.
- **불변 경계 보존**: 정본 R78 `INTEGRATED_DAG.json` (`60` 노드, `129` 간선, SHA-256 `90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11`), 원 42개 과학 게이트 (`e3264e10...`), R99 동결 오버레이 (`7bcf0163...`)는 전혀 완화·승격하지 않았으며, 모든 미보정 결과에서 `physical_Pi = null`, `physical_GF = null`, `calibrated_p = null`, `Bianchi_family_attribution = null`, `next_id = SQ-CF4` (`SCIENCE_BLOCKED`, exit `3`)를 엄격히 유지하였다.

---

## 1. Part A (`SQ-CF4`): 상류 원자료 수집 · 부호 계보 발견 · 전체 k-대역 공분산 · 선택우도
- **제한 용량 원자료 취득 ([SOURCE_INTAKE_RECEIPT.json](SOURCE_INTAKE_RECEIPT.json))**:
  - `SDSS_PV_public.dat`: `20,231,640 B`, `34,059`행, MD5 `b5b6e31caf7ea469c2ac2cb775fa8d14` 일치, 64비트 정수 `objid`/`PGC`/`IDgroupT17` 정밀 파싱 (`specobjid` `E18` 문자열 보존).
  - `table1.txt` (`6dFGSv`): `696,070 B`, `8,885`행 (`-1` 비그룹 sentinel `6,219`개, 유효 그룹 `2,666`개), MD5 `2cf556179ef4ae089e8e4669c76a5633` 일치. 총 `20,927,710 B` (`22,000,000 B` 상한 내).
- **핵심 과학적 발견 — SDSS vs 6dFGSv `DMfp` 부호 불일치 ([CF4_UPSTREAM_KBAND_RESULTS.json](CF4_UPSTREAM_KBAND_RESULTS.json))**:
  - SDSS `34,045`/`34,059`개가 CF4 `table2`에 PGC 정밀 일치하고, 6dFGSv `7,190`/`8,885`개가 `15 arcsec · 500 km/s` 내 유일 매칭된다(`45`개 공통 은하에서 원자료 `logdist_corr` vs `delta_d` 상관계수 `+0.7733`, 차이 표준편차 `0.0544`).
  - SDSS 내부 Fundamental Plane 잔차 `r - r_FP(s, i)`와의 상관 검증(`corr = +0.9311` vs `logdist`, `+0.9059` vs `logdist_corr`, 기울기 `1.0201`)으로 **두 원자료 모두 $\mu_H = \mu_{\mathrm{fid}} - 5\eta$ ($\eta = \log_{10}(D_z / D_H)$)** 로 동일 부호 정의임을 입증하였다.
  - 그러나 실제 `CF4 table2 DMfp`에서 **6dFGSv는 `-5.0268 * delta_d + 0.5793` (`std = 0.0888`, `H0 = 76.58 km/s/Mpc`)**, **SDSS는 반대 부호인 `+4.9779 * logdist_corr + 0.6359` (`std = 0.0335`, `H0 = 74.61 km/s/Mpc`)** 로 합류되어 있으며, `Dec > 0` 영역에서도 TF·SNIa와 SDSS `CF4 FP` 쌍극자 부호가 반전된다. 출판된 `35,970` 그룹 토모그래피를 보존한 채 SDSS 부호 재조정 민감도를 병렬 계측한 결과 `4x9` 최대 절대 차이는 `0.003605`이다.
- **전 대역 `[1e-4, 1.0] h/Mpc` 상관 특이속도 및 4항 공분산 분해**:
  - 1점 속도 분산 비율(`R=5 Mpc/h`): `low [1e-4, 0.005] = 0.02659`, `inherited [0.005, 0.05] = 0.55763`, `high [0.05, 1.0] = 0.41578`.
  - 패널별 `FINUFFT` 대 직접합/Bessel 검증: `low_k` 프로브 오차 `5.39e-12` (Bessel 20원 `rel_fro = 4.81e-7`), `hi1 [0.05, 0.15]` `2.43e-11`, `hi2 [0.15, 0.35]` `3.91e-11`, `hi3a [0.35, 0.55]` `3.85e-11`.
  - `WF_log R=5` 전체 `k` 공분산 `C_total trace = 0.012751` (`S_PV_full trace = 0.003808`, `min_eig = 1.550e-6`, `cond = 4474.9`), 4항 trace 항등식 오차 `1.73e-18`. 18 자유도 Schur 통계량 `12.116 -> 10.928`, 8-octant OOS `rms_mag = 0.4569`, `mean standardized^2 = 0.8766`.
  - 6단계 선택원장(`SDSS 34,059 -> 34,018`, `6dF 8,885 -> 7,109`)·probit 포함모형·`joint_selected_logpdf`를 산출하였으며, 상류 미보정 표 및 union rejected 모수 부재로 `D01`/`D02`/`M01`은 `BLOCKED_DATA`/`MODEL_CONDITIONAL`로 유지된다.

---

## 2. Part B (`SQ-OPTICAL` / `SQ-FRAME`): 유한 적색편이 위치 드리프트 $T_C/T_G$
- **구현**: [position_drift_optics.py](../../../htt/bass/transport/position_drift_optics.py), [optical_drift.py](../../../scripts/r100/optical_drift.py) → [OPTICAL_DRIFT_RESULTS.json](OPTICAL_DRIFT_RESULTS.json), [OPTICAL_DRIFT_TEMPLATES.npz](OPTICAL_DRIFT_TEMPLATES.npz).
- **검증 정밀도**:
  - 22-상태 편차-드리프트 ODE (`DOP853`, `z = 0.01..2.461`, `n_min = -ln 4`)가 비스듬한 Bianchi I 3D 좌표 광선 오라클과 상대오차 `< 1e-7`, Milne Type V에서 `0`, `VII_h` 수렴 `rel_TG = 5.650e-5`, `VI_h` $SO(3)$ 등변성 `1.504e-12 uas/yr`, 세속 수차(secular aberration) 항등 오차 `3.109e-15 uas/yr`를 달성하였다.
- **물리적 핵심 결과**:
  - 평탄 FLRW에서 상수 $(\boldsymbol{\beta}_o, \boldsymbol{\beta}_e)$는 Gaia 64D에서 $\cos = -1.00000$ (`cond = 1.662e9`), CF4 36D에서 $\cos = -0.99985$ (`cond = 115.63`)의 구조적 근사 공선성을 보인다.
  - 반면 곡률이 존재하는 `VI_h`는 `z=2.0`에서 `z->0` 국소 전단 외삽 대비 `15.06%` 유한 적색편이 잔차를 보이며, Quaia `z=2.461`에서 helical `B2/E2` 고유운동 비가 `4.623%`까지 성장한다.

---

## 3. Part C (`SQ-RADIO`): LoTSS DR3 외곽 노출 감사 · Offset GLM · 비선형 재선택
- **구현**: [radio_exposure_selection.py](../../../scripts/r100/radio_exposure_selection.py) → [RADIO_EXPOSURE_SELECTION_RESULTS.json](RADIO_EXPOSURE_SELECTION_RESULTS.json).
- **핵심 결과**:
  - `LoTSS DR3` `1,580`개 모자이크 메타데이터(`4.038e11` 총 픽셀, `1.615 TB` FITS 메타)와 `NSIDE=16` 외곽 지원(`1,771` 셀 = 경계 `184` + 내부 `1,587`, 기존 밀도 마스크 `966`)을 감사하였고, 내부 weight hole 및 RMS 지도(`HP-misc-*.tar`)는 SURF 테이프(`storage_class="M"`, HTTP 202 deferred)에 의해 외부 차단됨을 재확인하였다.
  - 전 `5`개 전파 서베이·`19`개 플럭스 컷에서 빈 셀(`y=0`, `e>0`) 보존 및 노출 스케일 불변성(`Poisson`, `NB1_Pearson`, `NB1_MLE`, `NB2_CoxLSS`)과 4-fold 공간 교차검증을 완료하였다.
  - **중요 발견**: 미보정 외곽 경계(`LoTSS_DR3_outer_b15`, `1,338`셀)에는 내부 결측 112개 빈 셀이 포함되어 50 mJy NB1 쌍극자가 `0.01098` (`legacy966`)에서 **`0.84688`**로 왜곡된다. 완전내부 5-서베이 공통 $\beta / \beta_{\mathrm{CMB}}$는 `5.589` (`chi2 = 86.03` vs 고정 Planck CMB `117.29`), `outer_b15` 민감도는 `5.667`이다.
  - 유한 $\beta$ 도플러·수차·SED 적분(Dirac & Gauss-Hermite) 비선형 재선택 곡률 보정은 `3 x v_CMB`에서도 `< 1e-4` 수준이어서 관측된 `~5.6x` 초과 진폭을 비선형 운동학 효과만으로 설명할 수 없음을 보였다.

---

## 4. Part D (`SQ-GAIA` / `SQ-CROSS-COV`): Rank-47 부분공간 & Gaia+CF4 결합 식별성
- **구현**: [gaia_optical_joint.py](../../../scripts/r100/gaia_optical_joint.py) → [GAIA_OPTICAL_JOINT_RESULTS.json](GAIA_OPTICAL_JOINT_RESULTS.json).
- **핵심 결과**:
  - 특이 행렬인 160D/64D 공분산 역행렬을 원천 회피하고, rank-47 양의 고유공간 백색화 `W_jk_64`만 수행하였으며(`unsupported_frac_64D = 0.22274`, `chi2_null = 1921.49`), 15/30/60° 체계오차 `C_sys` (`trace = 15.94, 32.06, 36.26`)를 `C_jk`에 합산하지 않고 독립 분리하였다.
  - 47차원 부분공간 내 nested 모형 적합: `16D z-무관 scan 바닥` (`chi2 = 189.14`), `+ beta_o` (`118.38`, `cond = 1806.3`), `+ beta_o + beta_e` (`cond = 5.00e12`로 $\boldsymbol{\beta}_o/\boldsymbol{\beta}_e$ 완전 공선 붕괴 확인).
  - Gaia 16D 상수 바닥과 CF4 9D 상수 평균을 동시에 주변화한 결합 프로파일 Fisher 특이값은 `[3.456, 2.992, 2.359, 5.60e-8, 2.98e-8, 0.0]`으로, 평탄 FLRW에서 상수 영점/스캔 바닥을 동시 주변화할 경우 결합 관측만으로도 $\boldsymbol{\beta}_o + \boldsymbol{\beta}_e$ 공선 모드가 남아 독립 물리 보정(`D04`, `M05`)이나 곡률(`VI_h`)이 필수임을 정량 입증하였다.

---

## 5. Part E (`SQ-PHOTON-FLUX` / `SQ-LIE-FLUX` / `P2` / `PHY01–07`)
- **구현**: [bianchi_selfconsistent_and_phy.py](../../../scripts/r100/bianchi_selfconsistent_and_phy.py) → [BIANCHI_SELFCONSISTENT_AND_PHY_RESULTS.json](BIANCHI_SELFCONSISTENT_AND_PHY_RESULTS.json).
- **자체일관적 Bianchi 배경+복사+바리온 결합 (`Radau`, `L=12`, `refinement=2`, `k=0..4`)**:
  - R98 `DOP853` 대비 무충돌 `Radau` 일치 (`I` `< 1e-7`), `FLRW` 완벽 영점 보존(`d_geom4 = 0`, `d_teb4 = 0`, `cod = 0`, `v_b = 0`).
  - 비등방 복사응력 $\pi_\gamma(N)$와 공변 탄성 Thomson 4-힘(`u_b . F == 0` 정밀도 `3.46e-14`, 총 4-운동량 보존 오차 `0`)을 결합한 `k=0..4` 고정점 반복 결과, `I, V, VII_h, VI_h` 전 모형에서 `k=4` 차분 `delta_geom <= 1.30e-11`, `delta_teb <= 7.52e-11`, Hamiltonian 잔차 `<= 1.10e-8`, Codazzi 잔차 `<= 1.04e-8`로 수렴하였다. `VI_h` 기준 비결합 `v_b(z=0)=0`이 결합 후 `9.727e-10`으로 끌리며, $\pi_\gamma$ 반작용 최대 전단 변동 `max|Delta sigma/H| = 3.685e-7`, 종단 `T_norm = 1.303e-3`, `E_norm = 4.540e-6`, `B_norm = 1.788e-7`을 산출하였다. AniLoS 근등방 `kappa` 오차는 `1.11e-16`이다.
- **P2 CMB SHA 가드 & PHY01–07 갱신**:
  - `CMB_GROUPED_FULL_CACHE.json` (`9cbaf55d...`) 및 `CMB_OBSERVED_SPLITS.json` (`ab55c5ab...`)의 무결성을 검증하였고 (`commander_null_qualified = false`, `fold0 raw SMICA = 78.003`), `PHY01–PHY07` 전 7개 교차 경로에 R100 결과를 반영하였다.

---

## 6. Part F 검증 · 남은 차단 요인 ([NODE60_EXECUTION_PREPARATION.json](NODE60_EXECUTION_PREPARATION.json), [BLOCKER_ACTIONS.md](BLOCKER_ACTIONS.md))
- R100 오버레이 및 전체 검증 게이트(`pytest tests/obsstat/test_r100_*.py`, `scripts.r100.validate_cycle`, `scripts.r99.validate_cycle`, `validate_unified.py --strict-authority`)를 통과하는 조건부 실행 구조를 완성하였다.
- **여전히 외부 데이터·물리 보정이 필요한 차단 항목**: `D01`(CF4 보정 전 원표 및 SDSS 부호 계보), `D02`(전체 서베이 rejected 분모), `D03`/`M04`(PR4/NPIPE 분할 및 FFP12형 모의잡음), `D04`/`M05`(Gaia AGIS 스캔/AGN 중심 보정), `D05`/`M06`(SURF 테이프 내부 LoTSS RMS·완전도), `M08`/`M09`/`SQ-NATIVE`(외부 네이티브 전모형 Boltzmann 아틀라스 및 비등방 재결합).
