# R114 로컬 인수인계 결과 보고서 (`R113-CLOUD -> R114`)

> **적용 범위 및 주장 한계**: 본 문서의 모든 산출물은 단일 결정론적(deterministic single-history) 네이티브 Rust/Python 검증 결과이며, **R78 60노드 과학 DAG의 신규 승격은 0건**이고 **원본 42개 수용 게이트(`INTEGRATED_DAG.json`, SHA-256 `e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d`)는 무변경**이다. 파이썬 계층(`htt/bass/`)의 비강제·일반 리(Lie) PSTF 디스패치는 `T5` HOLD 하에 fail-closed 상태를 유지하며, 본 결과는 앙상블 공분산·가족 식별·보정된 $p$값을 주장하지 않는다.

---

## (1) 사실 (Facts)

### 1.1 원격 핀 확인, `--no-ff` 병합, 커밋 및 푸시

`git ls-remote`로 클라우드 R113 핀(`NATIVE_PINS.json`)과 원격 헤드 일치를 먼저 확인한 뒤, 각 작업 브랜치에 `--no-ff` 병합하고 R114 수정(F0-1~F0-10)을 커밋·푸시하였다(`main` 푸시·리베이스·force-push 없음).

| 저장소 | 작업 브랜치 (체크아웃 경로) | R112 기반 SHA | R113 핀 / `--no-ff` 병합 SHA | R114 최종 HEAD SHA (원격 검증 완료) |
|---|---|---|---|---|
| **REC** | `research/r109-finite-tilt-ray-thomson-20261124` (`/home/cosmosapjw/Downloads/htt_r109_original_rec`) | `3752213099ccb35998c22f1aaf0d42fb674184e4` | `05db5451a97c66b9a87de98ae35b88ab820d368f` / `845d03389d9aa8bc5f6cd39f239aefc1e3c4a330` | **`6ad757d232a9833e984d18657d169766b27e33a4`** |
| **BASS** | `research/r109-native-nonlinear-sky-20261124` (`/home/cosmosapjw/worktrees/bass-r109-native-20261124`) | `40626723bcee34b3c02d1827344b2ee5ac3b368d` | `db72d1bcf8341d1fdeed3f1f03b169f00594efb6` / `c6b7dbf645027e9e2521c147fc31accdb67d89de` | **`4abb1d3b81a68711aa3438570f5a80f8cca42216`** |
| **REI** | `research/htt-tilted-thomson-20261124` (`/home/cosmosapjw/worktrees/rei-htt-thomson-20261124`) | — | — | **`503508f1c82a968bebc57900d43a65135c3db185`** (기존 일치) |
| **htt_base** | `research/r69-observable-physics-bridges-20261118` (`/home/cosmosapjw/Dropbox/bianchi/htt_base`) | `e810a4f705c3785e06f9f998f5c57e64c3baef22` | `5a9a4fc455ac800c3b8491efe2c94a4953991a0e` / `4f0de307fe80f8aef36d02190639739e71f39d90` | R114 마감 커밋 반영 (실행 커맨드 기록 참조) |

- 검증된 주요 바이너리 SHA-256:
  - R112 사전 스냅샷 `homogeneous_sky_r112_40626723b`: `027d3cde2a542a5c4da1817704344b78c01c1ae40fe017153439b161e2f04900`
  - R114 최종 `homogeneous_sky` (`/home/cosmosapjw/Downloads/htt_r114/bin/homogeneous_sky_r114`): **`3b775cf326921797d9488f00c8e78261aa58e2b436b2128ee0ec8cefd6c38686`**
  - REI `bass_ionization`: `7c6cde5e9d5086909f1ca4e57979a97c8753e7903d3aa2fc30a729119b32731e`

### 1.2 `F0` 독립 diff 리뷰 및 R114 수정 요약 (`F0_CLOUD_DIFF_REVIEW.{json,md}`)

읽기 전용 서브에이전트(`332962c3-66c8-4c98-b99d-628a1a5c811d`)의 R113 diff 독립 리뷰 및 `C1` 장기 적분 파일럿 검증에서 **CRITICAL 0, HIGH 1 (`F0-1`), MEDIUM 5 (`F0-2..5, F0-10`), LOW 4 (`F0-6..9`)**를 식별하고 모두 테스트 완화 없이 수정·회귀 검증하였다.
- **`F0-1` (HIGH)**: `BASS solve.rs` `--recombination-stop-eta` 게이트를 스텝 시작점 `node.eta < stop_eta`에서 종점 `next.eta <= stop_eta + 32*EPSILON*(1+stop_eta)`으로 교정 + 비격자 `stop_eta` 회귀 테스트 추가.
- **`F0-2` (MEDIUM)**: `BASS geom/lie.rs`에서 `n2*n3 == 0`인 Type IV(`rank(N)=1`)의 $10^{-17}$ 반올림 오차로 $h \sim -1.30\times 10^{16}$이 생성되는 문제를 `{III, VI_h, VI*_{-1/9}, VII_h}`로 역산 제한해 차단 + 회전 Type IV 테스트 추가.
- **`F0-3` (MEDIUM)**: `REC matched_history.rs` `isotropic_peebles_rate`에서 `Some(temperature_k)` 직접 전달(`6ad757d2`), `BASS solve.rs`에서 `x_ref_next >= X_MAX` 사전 단락화 및 Illinois 루프 밖 `compton_temperature_k(&rsky)` 1회 사전 계산.
- **`F0-4` / `F0-5` (MEDIUM)**: `homogeneous_sky.rs` `--route harmonic` Nyquist 검증(`nt>=lmax+1, np>=2*lmax+1`) 선행 및 개방 기하 `omega_lambda >= 1.0 + matched recombination` 거부 게이트 추가.
- **`F0-6..9` (LOW)**: `recoil.rs` 비양수 입력 즉시 실패, `ionization.rs` `added.is_finite()` 및 0깊이 필터, `frames.rs` `gf^2/(1+gf)`, `spin_sht.rs` 영벡터 가드, `AGENTS.md` 기존 체크아웃 우선 준수 및 클라우드 문서 불일치(`THEORY.md:211,239,357`, `README_KO.md:144,150-153`) 기록.
- **`F0-10` (MEDIUM)**: `C1` 장기 파일럿 중 얇은 조화 충돌 셀마다 $O(1)$ 단극 전체를 비중심화 SHT로 덮어쓰며 $4000$ 반스텝 동안 $10^{-14}$ 드리프트가 누적되는 현상 확인 → `HarmonicSky::absorb_delta`, `SpinSht::analyze` 링·GL 평균 중심화, `projector(&e)` 비편광 투영, 해석적 $l\le 2$ `HarmonicSky::moments`(격자 양의 강도/고윳값 검증 유지) 적용으로 `I/IX` `frame_rad <= 7e-17` 달성 및 초기 격자 의존성 0 제거.

### 1.3 `F1`–`F3` 클라우드 기준선 재현 및 `F0-10` 이후 최종 검증 (`F1_F3_REPRODUCTION.json`)

- **사전 재현 (`c6b7dbf6`, 바이너리 `724cda54...`)**:
  - `BASS cargo test --release --locked`: `218 passed` + `--examples 3 passed`, **R112 `V1` 20/20 TSV 바이트 일치**.
  - `REI cargo test --release --locked --lib --tests`: `271 passed, 0 failed`.
  - `F3` 4개 드라이버: `RECOMBINATION_DEMO.json` (`256.26s`, 수치 차 `0.0`), `CROSS_ROUTE_ATLAS.json` (`39.54s`, `0.0`), `TRUNCATION_STUDY.json` (`54.52s`, `rays_seconds` 3개 벽시계 필드만 차이), `LONG_EPOCH_DEMO.json` (`24.36s`, `--ionization` 경로 문자열 1개만 차이, 수치 차 `0.0`).
- **최종 검증 (`REC 6ad757d2`, `BASS 4abb1d3b`, 바이너리 `3b775cf3...`)**:
  - `REC cargo test --release --locked`: **`129 passed, 0 failed`**.
  - `BASS cargo test --release --locked` 및 `--examples`: **`221 passed` (`187+1+2+5+10+3+2+6+5`) + `3 examples passed`, `0 failed`, `0 warnings`**.
  - `V1` 하위 호환: **20/20 TSV 바이트 일치** (`SHA-256` 전수 동일).
  - `recomb_f010.json`: `max_peak_rel_vs_R113 = 2.189147029833629e-10`; `long_small` (`rays_table 5.421s`, `rays_matched 13.350s`, `harmonic16_matched 16.597s`, `delta_xe_final = 2.8235e-8`, `delta_xe_route_gap_max = 9.71e-17`); `window_strong` (`0.823s / 2.135s / 2.884s`, `delta_xe_final = 3.1004e-8`, `delta_xe_route_gap_max = 2.29e-16`).

### 1.4 Compute Lane (`C1`–`C6`) 결과

| 단계 | 실행 명령 (`htt_base` 기준) | 산출물 SHA-256 | 실행 시간 | 핵심 결과 / 합격 여부 |
|---|---|---|---|---|
| **C1** | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:htt:htt/src .venv/bin/python -B -m scripts.r114.c1_harmonic_long_atlas` | `3060f718bd9b6ee4b2a79afe8322f7fa725e0e259f77f5bf5ad7af1c749d84ca` | `1480.47s` (91 runs) | 11/12 엄격 $C_\ell \le 10^{-6}$ (`IX`만 $l=4$ $EE/BB=1.878\times 10^{-6}$, `delta_cl/sky_max_cl <= 1.285e-16` sub-ULP); 12/12 sub-ULP 제외 PASS, 12/12 전역 모드 $\le 10^{-6}$, `FLRW <= 4.05e-14`, 전 91실행 유형·$h$ 불변 |
| **C2** | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:htt:htt/src .venv/bin/python -B -m scripts.r114.c2_tight_coupling_matched` | `756ae1740f1395cf094b3d981532fa0b69463dcb530a64ed20264d19942c6950` | `715.05s` (합산) | FLRW $z=1600/1800$ 2차 반감 비 `3.994..3.998`, $z=1800$ $x_e \ge 1$ 구간 $\delta x_e = 0.0$ (엄밀 차단), 전 실행 `min_screen > 0` |
| **C3** | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:htt:htt/src .venv/bin/python -B -m scripts.r114.c3_rei_matched_join` | `312b3a5421d32e1e2fd0f06774814c20067650b534fdb26a181d89e436bf1e86` | `271.80s` (합산) | 5개 AX08 케이스 모두 `jump_at_z20 = 1.0349e-5`, $\tau_{\rm reio}(z\le 20)=0.054341$, `last_active_z = 20.0578`, `stop_eta` 이후 드리프트 `0.0` |
| **C4** | `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:htt:htt/src .venv/bin/python -B -m scripts.r114.c4_bjs_harmonic_highl` | `eada206b858e218c18bd96284a159d26830bf7a4cd223e88f77f15c25610bebc` | `2389.42s` | 비산란 $VII_h$ ($L=32$ 6건 + $L=48$ 1건) vs BJS McEwen2006: `min_protocol = 0.99964713`, `min_doppler = 0.99999993` (`all >= 0.999`), 전 케이스 $VII_h$·$h$ 보존 |
| **C5** | `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:htt:htt/src .venv/bin/python -B -m scripts.r114.c5_commander_c1_leakage` | `d64abf5b7759a56041642e01e2c63b28ee3bff047c980a6514fb763ad1bd9e83` | `118.08s` (`113.76s+4.33s`) | R108 커널 $l_{\max}=256 \ge 128$, `FLRW max|a_lm(l>=1)| = 7.933e-15`, `trunc_vs_pad = 4.19e-16`; 최대 `l>4 -> l<=4` masked 누출 `VIstar E 13.53%`, `III E 13.48%`, `III B 8.90%`, `V T 4.26%` |
| **C6** | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:htt:htt/src .venv/bin/python -B -m scripts.r114.c6_performance_benchmarks` | `7362e0c3b6cf91e35bce9db0eef71c5a1ee0139d7553f441357e92e33e24e7ea` | 개별 계측 | matched step 비율 `rays 2.34..2.65x`, `harmonic 1.85..2.06x`; `harm L=16..64` (24t) `0.82s..14.24s`; `LoS l=256` 1t→24t `10.37x` (`12.683s -> 1.223s`); 장기 $z=1600$ (2000스텝, 24t) `wall=108.66s`, `los=62.64s`, `rss=62.86MiB`, `err=2.473e-14` |

#### `C1` 가족별 상세표 (`h32_s2000`, `h24->h32`, `h16` 3점 `s500->s1000->s2000`, 제약 잔차)

| 가족 | `h24->h32` $C_\ell^{TT}$ 상대차 | `h24->h32` $C_\ell^{EE}$ 상대차 | `h24->h32` $C_\ell^{BB}$ 상대차 | `h16` 3점 $s$-수렴 비 (`LoS`) | `max \|Gauss\|` | `max Codazzi` | `max \|Jacobi\|` | 유형·$h$ 보존 |
|---|---|---|---|---|---|---|---|---|
| `FLRW` | `0.0` (등방 $4.05\times 10^{-14}$) | `0.0` | `0.0` | `0.747` (절대 0 바닥) | `2.108e-4` | `3.161e-30` | `0.0` | True |
| `I` | `1.180e-9` | `1.314e-8` | `0.0` | `3.818` | `2.108e-4` | `1.535e-21` | `0.0` | True |
| `II` | `2.346e-9` | `8.945e-10` | `1.890e-9` | `3.995` | `2.094e-4` | `1.953e-11` | `0.0` | True |
| `III` | `2.424e-10` | `8.007e-11` | `6.313e-11` | `3.994` | `1.906e-4` | `1.302e-10` | `3.468e-19` | True |
| `IV` | `2.175e-10` | `4.325e-11` | `7.544e-11` | `3.994` | `1.928e-4` | `1.094e-10` | `1.526e-19` | True |
| `V` | `5.499e-7` | `6.629e-8` | `5.970e-8` | `4.051` | `1.936e-4` | `1.137e-10` | `0.0` | True |
| `VI0` | `4.605e-10` | `1.402e-10` | `1.003e-10` | `3.994` | `2.054e-4` | `3.251e-11` | `0.0` | True |
| `VIh` | `7.449e-11` | `7.778e-11` | `1.401e-10` | `3.994` | `2.015e-4` | `7.595e-11` | `1.184e-19` | True |
| `VIstar` | `3.884e-10` | `6.116e-11` | `4.625e-11` | `3.994` | `2.010e-4` | `7.079e-11` | `4.163e-20` | True |
| `VII0` | `3.665e-7` | `7.771e-8` | `2.245e-8` | `4.026` | `2.108e-4` | `1.953e-11` | `0.0` | True |
| `VIIh` | `2.250e-7` | `6.598e-8` | `1.558e-7` | `4.018` | `2.062e-4` | `6.012e-11` | `2.006e-20` | True |
| `VIII` | `1.123e-10` | `5.510e-11` | `8.991e-10` | `3.994` | `2.039e-4` | `3.906e-11` | `0.0` | True |
| `IX` | `5.395e-7` | `1.878e-6` (`9.87e-17*`) | `1.864e-6` (`1.28e-16*`) | `4.078` | `2.156e-4` | `5.904e-20` | `0.0` | True |

`*`: `IX`의 $l=4$ `delta_cl / sky_max_cl` 값($C_4 \sim 5.2\times 10^{-11} C_2$ 수준). 전역 모드 상대 변화는 `6.37e-10` (`<= 1e-6`).

#### `C3` REI $z=20$ 정합 요약표 (전 5개 AX08 케이스)

| AX08 케이스 | $z=20$ 점프 | $\tau_{\rm reio}(z\le 20)$ | `matched` 최종 $\delta x_e$ | $\delta x_e^{\rm peak}$ | 마지막 활성 $z$ | `stop_eta` 후 드리프트 | $C_2^{EE}$ 상대차 |
|---|---|---|---|---|---|---|---|
| `ZERO` | `1.0349e-5` | `0.054341` | `2.9120e-8` | `5.0278e-7` | `20.0578` | `0.0` | `+3.6093e-6` |
| `SHEAR_PLUS` | `1.0349e-5` | `0.054341` | `2.9120e-8` | `5.0278e-7` | `20.0578` | `0.0` | `+3.6093e-6` |
| `SHEAR_MINUS` | `1.0349e-5` | `0.054341` | `2.9120e-8` | `5.0278e-7` | `20.0578` | `0.0` | `+3.6093e-6` |
| `SHEAR_HALF_PLUS` | `1.0349e-5` | `0.054341` | `2.9120e-8` | `5.0278e-7` | `20.0578` | `0.0` | `+3.6093e-6` |
| `SHEAR_HALF_MINUS` | `1.0349e-5` | `0.054341` | `2.9120e-8` | `5.0278e-7` | `20.0578` | `0.0` | `+3.6093e-6` |

### 1.5 `GAP_REGISTER.json` 갱신 및 회귀·R86 감사 검증

- `scripts/r107_cloud/gap_register.py`에서 **`SQ-NATIVE`, `B02`, `B03`, `SQ-P1-ANCHOR`** 4개 행의 `route` 및 `owner` 설명만을 R114 검증 결과(`Route::Harmonic`, `REC matched_history`, C1–C6, `T1`–`T5` HOLD)로 업데이트해 `GAP_REGISTER.json`을 재생성하였다(`n_nodes = 60`, `n_open = 42`, R78 과학 노드 승격 **0건**).
- `pytest`(`tests/r107_cloud/test_gap_register.py`, `test_r109_*`, `test_r111_*`, `test_r114_universal_lie_sky.py`, `test_r86_preexecution_readiness.py`, 단일 스레드 OpenMP 설정) **32 passed, 0 failed** 및 `scripts/r86_audit_preexecution.py` `pass=true` (`nodes=60`, `edges=129`, `actual_next_sci=SQ-CF4`, `agent_start=BLOCKED_NOT_DISPATCHED`)를 확인했다.
- 읽기 전용 독립 리뷰 서브에이전트(`a5acc029-d6e3-48ba-8b66-c95f3942454c`) 검증을 완료하고 지적된 테스트·문구 보완사항(`total_standard_runs`, `C1/C2` 세부 단언, `OutOfScopeError` 검증, C1/C5 해석 문구 정밀화)을 반영해 재검증하였다.

---

## (2) 해석 (Interpretation)

1. **보편 리(Lie) 조화-스핀 PSTF 경로의 물리·수치적 일관성**: `Route::Harmonic`은 10개 `co-flow` 가족(`II, III, IV, V, VI_0, VI_h, VI*_{-1/9}, VII_0, VII_h, VIII`)과 0-tilt `I/IX` 전부에 대해 `Route::Rays` 대비 2차 스텝 수렴(`s1000->s2000` 경로 차 반감 비: `direct_l1_4` `3.938..4.005`, `los_l1_128` `3.887..4.157`; `IX`만 $1.04\times 10^{-10}$ 바닥에서 `2.139/2.196`) 및 $s=2000$ 기준 `LoS` 상대 차 `6.54e-12..1.35e-8`(`direct`는 `4.31e-11..1.32e-7`) 일치를 달성했으며, `C4`에서 비산란 $VII_h$ BJS 비교기 대비 `0.99965..1.00000` 상관을 유지하면서 모든 리 유형과 불변량 $h$를 보존한다.
2. **`F0-10` 근본 해결과 `IX` sub-ULP 바닥의 정확한 분리**: `SpinSht::analyze` 평균 중심화·`HarmonicSky::absorb_delta`·해석적 $l\le 2$ 모멘트로 얇은 조화 충돌 셀에서의 $O(1)$ 단극 누적 오차를 제거하자 11개 비등방 가족이 엄격 $C_\ell \le 10^{-6}$을 통과했다. 유일한 `IX` 예외($1.878\times 10^{-6}$ at $l=4$)는 `recoil::gain_map`의 `1.5e-14` 고유분해 지터가 장기 적분($1+z=1601$)과 $C_4/C_2 \approx 5.2\times 10^{-11}$ 스케일 계층에서 $10^{-16}$ sub-ULP 바닥(`delta_cl / sky_max_cl <= 1.285e-16`)으로 증폭된 것이므로, 허용오차를 완화하거나 V1 20/20 바이트 일치를 깨는 변경 없이 현상 그대로 투명 보고한다.
3. **`REC` 정합 $\delta x_e$ + `REI` 단일 소유 구간 결합**: `C2`에서 밀결합($z=1800, x_e \ge 1$)의 $\delta x_e = 0$ 엄밀 차단이, `C3`에서 `stop_eta` 이후 드리프트 `0.0` 및 $\sim +3.61\times 10^{-6}$ 저-$l$ $EE$ 보정이 검증되었다.
4. **고-$l$ 템플릿의 Cut-Sky 누출 영향 (`C5`)**: `l=128` 템플릿을 R108 커널(`lmax=256`)로 투영한 결과 `l>4` 모드가 Masked cut-sky `l<=4` 계수에 최대 `13.53%` (`VIstar E`), `13.48%` (`III E`), `8.90%` (`III B`), `4.26%` (`V T`) 누출을 일으키며, `FLRW` 제어는 `7.93e-15`로 영점이다. 이는 결정론적 단일 이력 템플릿 단계에서 $l>4$ 포함 필요성을 시사할 뿐, 관측 우도·가족 식별을 의미하지 않는다.

---

## (3) 미해결·보류(`T1`–`T5` HOLD) 및 차단 항목

### 3.1 `T1`–`T5` HOLD 설계 사양 (`T1_T5_HOLD_SPECIFICATIONS.md`, 코드 미구현)
- **`T1` HOLD**: 수소 1변수 Compton 평형($T_m = T_C$)을 넘어, 헬륨(He II/I $584\text{ \AA}$) 및 $z \lesssim 800$에서의 독립 물질 온도 $T_m(\eta)$를 정합 스텝 상태 변수로 편입하는 사양(열용량·비단열 가열/냉각 규약 필요).
- **`T2` HOLD**: $\eta$-스텝 선단 1차 고정 대신 반스텝($\Delta\eta/2$) 보간을 사용하는 2차 Strang 연산자 분리 규약(현재 $O(\Delta\eta^2)$ 반스텝 SDIRK2 결합 검증 완료 후 별도 게이트로 보류).
- **`T3` HOLD**: 이동전자 조화 충돌에서 Wigner 소행렬·비대각 결합을 통한 격자-프리(grid-free) 조화 충돌 연산자 사양.
- **`T4` HOLD**: $y$-형 Compton 왜곡 모멘트 $\mathcal{Y}_{ab}(\hat{n})$ 및 `rec_microphysics::anisotropic` 방향별 왜곡 결합 사양.
- **`T5` HOLD**: `htt_base` 파이썬 계층의 소유 디스패치 경계 — 비강제 6가족(`{II, III, IV, VI_0, VI_h, VIII}`) 및 off-axis 일반 리 PSTF 요청은 `htt/bass/inference/envelope.py` (`STRONG_FAMILIES = {FLRW, I, V, VII_0, VII_h, IX}`) 및 `general_bianchi_transfer.py`에서 계속 fail-closed(`EnvelopeError` / `OutOfScopeError`)로 차단되며, Rust 산출물 소비를 위한 `AtlasEntryLite` 승격 계약을 별도 완료하기 전까지 해제하지 않는다.

### 3.2 차단된(BLOCKED) R78 과학 노드 및 누락 입력
- **`SQ-CMB-NULL` / `L03` (`B03`~`B05` 차단)**: 동일 릴리스 Planck/Commander $\ge 300$ matched 시뮬레이션 페어·분할 차분($HM/OE$) 널 뱅크 및 전경/마스크 선택 법칙 부재.
- **`SQ-CF4` / `H02`**: 비-2MRS/CF3-독립 원시 영점 교정 공분산 및 held-out 예측 검증 세트 부재(R86/R87 `BLOCK_LOCAL_AGENT_START` 유지).
- **`SQ-GAIA`**: ICRF3 중심 제어, scan-law 모의, AGN 교차식별 널 입력 부재.
- **`SQ-RADIO`**: LSS 군집 $C_1$ 사전분포 및 RACS-low 교차 $C_1$ 입력 부재.
- **`T3` (R111 이월)**: $z < 4$ 구간(`τ_cont_0_to_4 = 0.02239`)의 물리적 선원/SED/흡수체 모델 부재(현 `bass_ionization`의 `z<4` 구간은 조건부 연속 자리표시자).
