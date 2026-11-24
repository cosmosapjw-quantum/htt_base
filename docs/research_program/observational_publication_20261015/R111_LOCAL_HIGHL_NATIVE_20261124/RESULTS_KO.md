# R111 로컬 네이티브 고다중극 검증 보고 (BASS / REC / REI / htt_base)

- **작성 기준**: 모든 수치와 해시는 R111 로컬 실행 출력 파일(`C1`–`C6` JSON, Rust/pytest 실행 로그)에서만 인용함.
- **과학적 청구 상한(Claim ceiling)**: 본 문서의 모든 산출물은 단일 결정론적 진화 이력(deterministic single-history template)이며, R78 60-노드 DAG 상태 승격은 **0건**임.

## 1. 사실 (검증 및 실행 결과)

### 1.1 F0–F3 검증 및 R111 결함 수정
- **F0 독립 코드 리뷰 (`fbdb2b3d-73fa-4403-8621-17d2b63e9006`)**: 4개 저장소 R110-CLOUD diff에서 CRITICAL 0, HIGH 1, MEDIUM 4, LOW 5건 식별(`F0_CLOUD_DIFF_REVIEW.json`).
- **R111 수정 내역**:
  - `BASS`: `los_sky`(`replay.rs`) 음의 횡단 스크린 고윳값(`min_eig < -1e-9 * min_i`) 차단 가드 추가, `recoil::trial` SDIRK2 양수성 초과 시 이분 분할(`Ok(None)`), `analyze_rings`(`sky_spectrum.rs`) Nyquist(`n_phi >= 2*lmax+1`) 검사 및 `|z| > 0.99999` 극점 부동소수점 분기, `homogeneous_sky.rs` 초기 `omega_lambda` 포함 Codazzi 로깅 수정 및 회귀 테스트 3종 추가.
  - `REC`: `anisotropic.rs` 중입자 정지좌표계 계약 명시 및 `tau0 < 1.0` 얇은 한계 상쇄 방지 분기 + 테스트 추가.
  - `REI`: `bass_ionization.rs` `z_match <= 0` 거부 및 `z_low == 0.0` 연속 분기 스킵, `examples/bass_ionization.rs` 안전한 CSV 열 조회 + 테스트 추가.
  - `htt_base`: `scripts/r109/commander_native.py` `--member-prefix` 인자 추가 및 `tests/obsstat/test_r111_commander_native.py` 작성.
- **F1–F3 검증 결과**:
  - `BASS`: 192개 테스트(`174 unit + 1 + 2 + 5 + 10`) + `sky_covariance` 3개 통과; `convergence_study.py` BE `~1.90..2.49`, SDIRK2 `3.94..4.05` 2차 수렴; R109 기본값 `recoil_VIIh` (`modes.tsv`, `cl.tsv`, `diagnostics.tsv`) 바이트 단위 SHA-256 일치(`run.txt`는 `schema=bass.homogeneous_sky.v2` 등 R110/R111 메타 키 10종 추가).
  - `REC`: 전체 통과(`tests/anisotropic.rs` 5개 포함). `REI`: `bass_ionization` 3개 통과.
  - **F3 재빌드**: `HIGHL_ATLAS.json` 대비 `los_modes.tsv` **32/32 SHA-256 완전 일치 (0 불일치)**.

### 1.2 Compute Lane C1–C6 요약
- **C1 (`C1_VISIBILITY_COVERAGE.json`, SHA `f8d08b23...`)**:
  - REC `4cffa8a0`(`c7c113af...`)에서 `z=1600..0`(1601행) 및 `z=1650..0`(1651행) 추출(`hyrec_xe_1600.tsv` `80c76287...`). BASS `9f10e114` HYREC2 대비 `max |d x_e| = 7.151e-5`.
  - 독립 FLRW 구적 `tau(1600->1100) = 31.41646520`, `tau(1600->0) = 32.54057408`(3차 스플라인 `32.54056915`).
  - BASS `sdirk2`: `32768`스텝 `proper_depth(0) = 32.5405746645`, `abs_err = 5.828e-7 <= 1e-6` (`rel_err = 1.791e-8`, `5.86s`); `1600->1100` `4096`스텝 `abs_err = 8.841e-8`; `z=1650` `32768`스텝 `37.6465995737`(`abs_err = 6.271e-7`).
  - `I` (`--dust-beta 1e-3,0,0`) 강결합 완화: `(4/3) beta_host` 대비 쌍극자 잔차 `1.333e-3 (z=1600) -> 2.361e-6 (z=1400, tau=18.64) -> 1.393e-5 (z=1100, tau=31.42)`. 장기 `VII_h` SDIRK2 안정(`min_screen = 7.606e-14 > 0`).
- **C2 (`C2_REI_JOIN.json`, SHA `aada277d...`)**:
  - AX08 5종(`ZERO`, `SHEAR_PLUS`, `SHEAR_MINUS`, `SHEAR_HALF_PLUS`, `SHEAR_HALF_MINUS`) 모두 `--z-emit 1600`에서 단일 소유 구간(`1580` REC `z>20`, `1001` REI `4<=z<=20`, `400` 연속 `0<=z<4`) 검증.
  - 전 케이스 `z=20` 점프 `+1.034919e-5`(`0.000210349 - 0.0002`).
  - `tau_reio(z<=20)`: `ZERO` `0.05434091` (`HyRec m_H`) / `0.05437034` (`AX08 m_p`, `+0.0541%` 계통 차이), `SHEAR_±` `0.05434077` / `0.05437019`, `SHEAR_HALF_±` `0.05434088` / `0.05437030`.
  - `VII_h ZERO` SDIRK2 재이온화 편광 시연(`7.75s`): `l=2 C_l^EE = 4.958e-11`, `C_l^BB = 3.564e-11`.
- **C3 (`C3_LONG_HIGHL_ATLAS.json`, SHA `16026836...`, 타르볼 `f463bfd4...`)**:
  - 12개 Bianchi 계열, `z_emit=1600`, `|A|,|N| <= 0.02`, `Sigma in [1e-4, 1e-3]`, `Lambda`, `SDIRK2 + congruence`, `LoS l<=128`, 총 **61회 실행** (`60회 기본 2875.53s + VI0 s8000 752.82s = 3628.35s`).
  - **61/61** `lie_type` 및 `h` 불변성 유지, 최대 해밀토니안 잔차 `2.156e-4` (`4000`스텝 `<= 5.39e-5`, `VI0 8000`스텝 `1.28e-5`).
  - **12/12 계열** 최정밀 축 쌍(`steps`, `mesh (14,36)->(20,52)`, `LoS (129,258)->(256,512)`) 상대 모드 변화 `<= 1e-3` 통과 (`I` 계열 `B` 모드는 `C_l^BB <= 1.018e-26`으로 `sky_max=1.737e-8` 대비 `5.9e-19`에 불과한 대칭 0 채널로 분류; `VI0`는 `l=5` 극점 `s2000->s4000` `1.526e-3`에서 `s4000->s8000` `3.818e-4`로 4배 수렴 확인).
- **C4 (`C4_BJS_HIGHL.json`, SHA `444848a5...`, `1914.06s`)**:
  - 개방형 더스트 `VII_h` (`Omega0 in {0.3,0.5,0.7}`, `x in {0.62,1.0}`, `--dust-fraction 0.9999`, `tau=0`, `z_E=1100`, `LoS l<=64`) 튜닝 없이 전 케이스 `>= 0.999` 통과:
    - `mcewen2006` (`protocol`): 상관 `0.999647`–`0.999784`, 상대 잔차 `2.08%`–`2.66%`
    - `mcewen2006` (`doppler`): 상관 `0.99999993`–`0.99999998`, 상대 잔차 `2.18e-4`–`3.75e-4`
    - BASS `--observer-beta` vs 해석적 도플러 부스트 일치 오차 `1.32e-8`–`1.14e-7`.
- **C5 (`C5_COMMANDER_LEAKAGE.json`, SHA `5f9239cb...`)**:
  - R108 커널(`4c4e0cce...`, `lmax=256 >= 128`)로 C3 `los_modes.tsv (l<=128)` 투영(`157.18s`), R109 원본 `ATLAS_MODES.tar.gz` 대비 `0.00e+00` (`sha_equal=True`), R110 Part A(`sdirk2+congruence`) 대 R109(`BE+additive`) 차이는 `1.77e-3`.
  - `l > 4` 고다중극 구조가 마스킹된 `l=2` 계수로 유입되는 최대 누출은 `III` (`E: 13.55%, B: 8.89%`), `VIstar` (`E: 13.53%, B: 4.92%`), `VIh` (`E: 8.49%`), `V` (`B: 5.41%, T: 4.17%`), `VIIh` (`T: 1.95%, B: 1.41%`)이며, 평탄 무플럭스 `I`에서는 전천 `E`->마스크 `B` 누출로 `|cut-full|/|full| = 2.91e7`이 관측됨.
- **C6 (`C6_LOS256_PERFORMANCE.json`, SHA `481bd1c3...`)**:
  - 36스텝 R109 `VII_h` `l=256` (`132,098` 광선): `1t` `12.12s` (LoS `11.95s`, `35.8 MiB`) -> `24t` `1.27s` (LoS `1.09s`, `53.3 MiB`), LoS `10.95x` 병렬 가속, 착지 오차 `2.41e-15`.
  - 장기 `z=1600` 4000스텝 `VII_h` `l=256` (`24t`): 총 `96.49s` (LoS `89.03s`), 피크 RSS `65.2 MiB` (`66,788 KiB`), 착지 오차 `3.26e-14`.

## 2. 물리·수치적 해석
- **정수 `z` 매듭 이산화 오차 vs 적분 정확도**: `hyrec_xe_1600.tsv`의 구간 선형 적분 기준으로는 `5.83e-7 <= 1e-6`이지만, 3차 스플라인 FLRW 구적과는 `dz=1` 표의 구간 선형화 차이 `4.93e-6` (`rel 1.5e-7`)만큼 구별됨.
- **다중 스레드 OpenBLAS 경합 해소**: Python/NumPy/SciPy 병렬 실행 시 `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1` 미지정 시 `healpy.rotate_alm` / `score_axis`가 492배까지 지연됨을 실측해 분리·해결함.
- **고다중극 마스킹 앨리어싱**: Class B(`III`, `VIstar`, `V`, `VIIh`)의 `l > 4` 비등방 특성이 갈락틱 마스크를 통해 Commander `l=2` 추정 계수를 최대 13.55%까지 변화시키므로, 저차 `l<=4` 절단만으로는 마스크 계통 오차를 포착할 수 없음.

## 3. 미해결·보류(HOLD) 및 차단 항목
- **HOLD 명세 (`T1_T2_T3_SPECIFICATIONS.md`)**: T1(차분 비등방 재결합 + `T_CMB,0`/He/`T_m` 결합), T2(이종 질량 2-유체 먼지 `f_b` 및 운동량 평형 반대 틸트), T3(`z < 4` REI `M1`–`M6` 물리 모델) — 설계 명세만 작성, 구현 보류.
- **차단 항목(외부 결측 입력)**: `SQ-CMB-NULL` (`300+` Commander 시뮬레이션 페어·스플릿 누락), `L03`, `SQ-CF4` / `H02`, `SQ-OPTICAL` / `SQ-GAIA`, T1/T3 외부 물리 앵커; 따라서 R78 과학 노드 승격 **0건** 유지.
