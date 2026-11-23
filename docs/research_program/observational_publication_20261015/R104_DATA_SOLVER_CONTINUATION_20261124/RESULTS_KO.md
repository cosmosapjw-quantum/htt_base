# R104 실자료 분석과 결합 solver 수렴

출발 커밋 `9aceac7d3436b764dcc1ed240e88b981c08c6762` (R103). 기계 판독 기록은 `R104_RESULTS.json`(노드 ID·원자료 SHA·산출물 SHA), 실행 명령·반환 코드·시간·메모리는 `EXECUTED_COMMANDS.json`. 환경: Python 3.12.3, NumPy 2.5.4, SciPy 1.18.1, healpy 1.19.0, astropy 8.0.2, Linux 7.0.0-43, `OPENBLAS/OMP/MKL_NUM_THREADS=1`(Commander 축약만 `OMP_NUM_THREADS=4`).

## 1. SQ-CF4

**R103 재현.** CF4 Table 2(`8e9089…332f`)와 6dFGSv Table 1(`08f3d4…a14d`)에서 모 표본 8,885, 선택 7,190, 군 적색편이 행 2,666(값 변경 2,653). R102 기준선 재현 오차 0.0. 5-fold 점수(무흐름 대비 held-out 로그 예측밀도, nats):

| 정책 | fold 0 | 1 | 2 | 3 | 4 | 합 |
|---|---|---|---|---|---|---|
| PGC fresh | 5.390 | 4.214 | 0.414 | 14.773 | 5.961 | 30.751 |
| PGC shared | 6.530 | 4.985 | −5.064 | 12.208 | 6.585 | 25.244 |
| PGC1 fresh | 6.495 | 9.932 | 4.541 | 4.125 | 1.614 | 26.707 |
| PGC1 shared | 6.834 | 7.902 | 6.403 | 4.348 | 0.001 | 25.489 |

군 적색편이 대체: PGC fresh/shared 30.117/24.865, PGC1 26.437/24.923. 부호와 크기 유지. PGC fold 2 shared만 음수.

**Manticore.** `manticore-data 2.0.1` 의존성 검사 통과. `fetch --indices 0 1`은 `manticore.web.data-2-osu.iap.fr:443/public-keys.json` ConnectTimeout으로 rc=1, 135.8 s, 수신 0 B. 두 IAP 호스트(194.57.221.153)는 DNS는 해석되나 20 s 내 TCP 연결 불성립. 같은 시각 PyPI는 HTTP 200. 실제 Manticore 실현 수 0 (`MANTICORE_FETCH_FAILURE.json`).

**속도 정규화 수정.** R103 `geometry()`는 z=0 속도(km/s)에 g=aH₀EfD(km s⁻¹ Mpc⁻¹)를 그대로 곱함. 프로젝트 배경에서 g(0)=35.5247255, g(0.05)/g(0)=1.00408763. 기존 가중치는 g(0)배 과대. `velocity_growth_ratio(g, g0)=g/g0`로 수정. z=0 항등과 일정 3-벡터 속도의 시선 투영(상대오차 1e-13) 테스트 추가.

**2MRS-NeuralNet (Lilow 등, 저자 ZIP `c12efc…bcd7`, 100,665,566 B).** vₓ,v_y,v_z float32 128³(`50edf1…4643`, `c125f3…c447`, `ae1e0d…07d6`), 셀 중심 (i−63.5)×3.125 h⁻¹Mpc, Galactic, CMB 기준, r>200 h⁻¹Mpc NaN. ICRS→Galactic 회전(은하중심 검산 l,b<2e-4°), h=0.6736, g(z)/g(0) 적용.

- CF4 35,970군 중 r≤200 h⁻¹Mpc 22,127, 8개 보간 이웃까지 유한 21,860(경계 267 제외).
- 공통 표본에서 4창×9계수 재적합. 전체-표본 영향행렬의 |A| 누락 비율, 창별: 0.0002, 0.0094, 0.257, 0.828.
- 측정 공분산만 쓴 36차원 χ²: 관측 496.4 → 2MRS 예측 제거 후 499.9. PV·장·보정 공분산이 없어 확률로 해석하지 않음. 36개 투영 성분과 관측 계수는 `CF4_2MRS_FIELD.json`.
- 6dFGSv(8,885 전체 장 정의) 5-fold, 무흐름 모형 대비 nats:

| 정책 | 전 fresh | 후 fresh (u+v₂ₘᵣₛ 혼합) | 전 shared | 후 shared | 2MRS 단독 fresh |
|---|---|---|---|---|---|
| PGC | 30.751 | 46.657 | 25.244 | 47.869 | 25.500 |
| PGC1 | 26.707 | 41.366 | 25.489 | 47.885 | 25.525 |

fold별: PGC fresh 후 10.79, 6.75, −1.36, 18.24, 12.23; PGC1 fresh 후 11.47, 15.02, 7.45, 4.89, 2.53. 10개 fresh 중 9개 개선, PGC fold 2만 악화. 단일 재구성장이므로 군 사이 posterior 공분산은 추정하지 않음(오차 지도 미사용).

**Courtois CF4 (Zenodo 20653238, MD5 `15a0b844…` 게시값 일치).** 헤더에 단위·격자 메타데이터 없음, 기록상 축 (SGZ,SGY,SGX), 1000 h⁻¹Mpc. 성분 순서 2 × 원점 2 변형 모두 공통 21,860군에서 2MRS 시선속도와 Pearson r=0.09–0.18, 최소제곱 척도 1.7–3.4 km/s/단위. 규약·단위 미확정으로 내부 비교 결론 없음.

## 2. Commander PR3

쌍 0(cmb `c84d83…7a27`, noise `7c25b9…74e3cb`)은 R102와 TT 최대 2.3e-13 μK². 쌍 1: 기존 cmb `73b775…6000` 재사용, noise `fd278b…1e43`(603,987,840 B) 스트리밍 후 해제, 87.7 s, RSS 4.19 GB. 마스크 SHA `23f49a…5fc4`, `c967e4…36d4`. 서명 있는 TT/EE/BB/TE/EB/TB(ℓ=2–64, μK²)는 `COMMANDER_PR3_0000{0,1}.json`. 300쌍 중 2쌍, 유효 빔·픽셀창·전경 전달 미동결 → null calibration·귀속 미실행.

## 3. Gaia 패치 영향

R98 정상방정식(634,233 Quaia, receipt `0a56bc…a800`). 48 delete-one, 1,128 delete-two 전부 재적합. 곡률(μas yr⁻¹ z⁻²) jackknife χ²:

| 행 | glide (3) | spin (3) | E2 (5) | B2 (5) |
|---|---|---|---|---|
| shells 0–2 | 5.32 | 14.56 | 4.70 | 2.03 |
| shells 1–3 | 6.06 | 27.35 | 1.94 | 4.54 |

delete-two 공분산 χ²는 1% 이내 동일. 최대 영향 패치: 행 0 전 섹터 47(E2 이동/노름 0.41, B2 0.57), 행 1 E2·B2는 8. 최악 쌍은 행 1 B2의 (8,42)를 제외하고 (43,47). E/B 곡률은 jackknife와 양립, spin 곡률은 affine 프레임으로 제거되지 않는 z-비선형 성분.

## 4. NVSS

R65 실행기를 원자료(`52eb57…5a38e`, 1,773,488행)에서 재실행: integrated−peak 대비와 공분산 차이 0, carrier SHA `a51da9…4e89` 동일. 이동 행렬은 상삼각(S_int ≥ S_peak). |b|>10°, δ>−40°, 20 mJy 선형 벡터합 쌍극 대비에서 HEALPix 블록 jackknife/Poisson 분산비(xy trace): N_side=4(166블록) 3.74, N_side=8(597블록) 2.56. R65 Poisson Wald 32.79(df 2)를 이 비율로 나누면 8.76(p=0.013) / 12.82(p=0.0016). 같은 소스 대비에서 군집·다중성·조사 계통이 Poisson 분산의 2.6–3.7배. 물리적 LSS 공분산은 미보정.

## 5. 결합 solver

**계측.** `CoupledSolverConfig.record_history`가 셀 끝마다 종별 q/E(하늘: −∫n I dΩ / ∫I dΩ, 유체: T⁰ⁱ/T⁰⁰), 하늘·유체 π/E, 하늘·유체 광자 T⁴로 계산한 Thomson 힘/E, Hamiltonian·Codazzi 잔차를 저장.

**첫 어긋남.** VII_h, ℓ=4, ε=2e-4, 16셀, Picard 2: 첫 셀 N=−7.378→−6.917(z 1600→1008), Δτ=30.4. 하늘/유체 광자 q/E 상대차 5.85e-2, 힘 차/힘 1.59. Picard 반복과 무관. 하늘 q/E는 셀 중점 baryon 속도의 평형값 4v/(3+v²)와 1% 내 일치. 원인: 불투명 셀의 이동 Thomson 충돌이 셀 전체에 중점 v_b를 고정. 초기 조건 v_b=0, v_γ=0.1ε·tilt에서 강결합 v_b(N)가 셀 안에서 변함.

**수정.** `_advance_moving_photon_cell`: SDIRK(2,2) 각 단계 시각(u_j+γh, u_j+h)의 v_b를 Einstein–Euler 조밀 출력에서 읽고, substep별 정확 광학깊이를 사용. 두 번째 단계가 결과이므로 강결합 극한에서 단계 끝 baryon 프레임으로 이완. 일정 속도에서 기존 셀 적분과 1e-12 일치, 선형 v_b 불투명 셀에서 끝점 평형 1e-3 내 회복(테스트 2개).

**A/B (`FIRST_DIVERGENCE.json`, Picard 4).** 첫 셀 불일치 16/32/64/128셀: 수정 전 5.85e-2/3.47e-2/2.25e-2/1.13e-2, 후 1.00e-2/8.4e-3/1.09e-2/6.5e-3. C₂ᵀ 극한(2.8628e-9) 대비 오차: 전 23.9/10.2/2.7/0.68%, 후 11.7/2.3/0.51/0.12%. 두 경로 모두 점근 2차. 수정은 오차 상수를 2–6배 줄임. 극한값은 ℓ=6·Picard 6·384셀 Richardson 값(ℓ·Picard 차이 ≤5e-4 상대). Picard 2에서는 수정 전후 모두 끝 시각 q/E 불일치가 1.4–1.5e-2에 정체(π 변화 1.1e-2) → Picard 2 미수렴.

**한 축 세분화 (VII_h·VI₋₁/₉·IX, 기준 48셀·Picard 3·ℓ=6·GL 16링, `SOLVER_AXIS_SWEEP.json`).**

- 각격자 10–32링: C₂–₄ 상대변화 ≤7.9e-9.
- ℓ_max 4–10: VII_h 5.2e-4, VI₋₁/₉ 2.2e-3, IX 5.1e-5.
- Picard 2→6: 3.4%/0.9%/5.5%(Picard 2 지배); Picard 4→6 C₂ᵀ 변화 2.4e-5(VII_h).
- 시간 셀(Picard 6, `SOLVER_CELLS_PICARD6.json`), 24/48/96/192/384셀:

| 계열 | C₂ᵀ(384) | 연속 차 비율 | 공통 시각 q/E 최대 불일치 |
|---|---|---|---|
| VII_h | 2.8624666e-9 | 4.75, 4.45, 4.24 | 1.05e-2, 2.59e-3, 6.42e-4, 1.60e-4, 3.99e-5 |
| VI₋₁/₉ | 2.9816500e-7 | 4.37, 4.21, 4.12 | 1.05e-2, 2.59e-3, 6.42e-4, 1.60e-4, 3.99e-5 |
| IX | 2.9791267e-9 | 4.76, 4.45, 4.24 | 1.05e-2, 2.58e-3, 6.41e-4, 1.60e-4, 3.99e-5 |

Hamiltonian·Codazzi 최대 ≤2.1e-9, Picard π 변화 ≤1.2e-8. 질량 없는 중성미자(N_eff=3.044, f_ν=0.4087) 기준 설정에서 중성미자 q/E 끝 불일치 VII_h 1.23e-3, VI₋₁/₉ 1.69e-3, IX 7.4e-5. 48셀 기준에서 C₂ᵀ 이산화 오차 약 1%. 정밀 비교에는 ≥192셀, Picard ≥4 필요.

R103 코드 재생: 중성미자, rec/REI, signed reference(AniLoS/AniCLASS), closed tensor, REI five-case 비트 동일. 인계 설정(ℓ6·48셀·Picard 3) native 실행은 커밋본(ℓ4·32셀·Picard 2)과 설정이 달라 비교 대상 아님.

## 6. 귀속 판정

공통 beam·mask·frame과 held-out null을 모두 갖춘 범위는 CF4/6dFGSv group-blocked fold(CMB 프레임, 같은 표본·선정 모형)뿐. 그 범위에서 2MRS 속도장은 무흐름 대비 held-out 점수를 높임. Commander(2/300쌍, 전달함수 미동결), Gaia(단일 잡음 실현 jackknife), NVSS(보정된 LSS null 없음)는 귀속 불가. `physical_Pi`, `physical_GF`, Bianchi 계열 귀속은 미정(B03/B04 pending).
