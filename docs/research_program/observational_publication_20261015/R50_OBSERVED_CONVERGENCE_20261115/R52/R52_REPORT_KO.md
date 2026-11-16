# R52: 방향 의존 관측량과 boost/tilt 부분식별

기준: R51 커밋 `1dbdc6baa`. claim tier C0. 상세: `R52_RESULT.json`, `R52_JOINT_RESULT.json`, `joint_posterior_summary.json`, `identified_combinations.npz`.

## 정의 (공통 Galactic triad, 1차)

θ(17) = σ/H₀(STF5, 오늘, 물질 congruence), ω/H₀, A/(cH₀)(물질 4-가속도), β_RM(0)=v_R−v_M(국소 복사 frame), β_MO=v_O−v_M.

| probe | 응답 (원전) | 상태 |
|---|---|---|
| CMB Σ (R51) | Σ = I_hist σ/H₀, I_hist=3.927×10⁴ | conditional (비등방 stress 없음) |
| Gaia E2 (R50, Quaia G<20.0, 755,850) | A_PM=2c(B_o−B_s)/D−Ḃ_o → s = H₀[μas/yr]·K_eff·σ/H₀, K(z)=2J(z)/χ(z)−1, K_eff=4.49 (16–84%: 2.76–7.04) | conditional; 정보가중 근사 |
| Quaia/NVSS/RACS | d = c_EB β_MO (Ellis–Baldwin) | c_EB: Quaia x 측정·α 가정, radio 가정값 |
| Planck 2018 dipole | v_O−v_R = β_MO − β_RM(0) | 공개 측정 |
| CF4 H03 (4 창 × [H, dipole, STF5]) | δH_n = −n·a + σ_nn (Heinesen 2021) → dipole −H₀A~, STF H₀σ~; source bulk = −cβ_RM(0) via AN | 공분산은 R36 조건부 법칙 |

Pantheon+는 제외: CF4와 host·속도장 공유, z_HD에 2M++ PV 보정이 있어 대상 bulk flow를 제거한다.

## 식별 (prior 전)

- likelihood rank 14/17. ω(3)은 source-bound 응답 없음 → null (Gaia B1은 frame spin과 퇴화).
- A: baseline rank 3이지만 CF4 방향 거리보정 dipole nuisance를 넣으면 rank 0 → **물리적으로 식별되지 않음**.
- CF4 각 창 단독은 A와 β_RM이 거의 퇴화(약한 고유값 3개); 창 간 깊이 의존성(AN ∝ 1/d)이 둘을 분리한다.
- 그 뒤에만 proper Gaussian prior(σ, β: 10⁻², ω, A: 1)를 추가.

## 결과

- β_MO = (−294, −27, 329) ± (136, 139, 125) km/s, |β_MO| = 442 km/s.
- frame-offset β_RM(0) = (−268, 218, 53) ± (136, 139, 125) km/s. 0 검정 Wald 5.8 (측정 공분산만); ΛCDM bulk 분산 250 km/s를 넣으면 2.8, CF4 보정 dipole을 넣으면 1.1. **전역 tilt의 증거가 아니다.**
- counts+CMB dipole과 CF4+CMB dipole의 β_RM(0) 불일치: χ²₃ = 16.7, working tail 8×10⁻⁴. counts 단독 β_MO는 1156 km/s, CF4 단독 frame offset은 557 km/s (Wald 14.0, 측정 공분산만). 둘은 한 frame을 공유하지 않는다: count-dipole 초과(체계오차 예산 미포함)와 국소 CF4 bulk flow로 읽는다.
- σ/H₀: CMB가 지배(sd ~2.5×10⁻¹⁰, 조건부). Gaia E2 χ² 110.4/5 → CMB 허용 shear로는 E2를 설명할 수 없다: E2 계통오차 또는 nuisance 불완전.
- PPC(유효 자유도): CF4 84.8/26.6 (p=6×10⁻⁸), Quaia 9.8/2.7 (p=0.016), NVSS/RACS 적합, CMB Σ·CMB dipole은 포화되어 검정 없음.
- 민감도: c_EB ±10%, count clustering 상관 ρ=0.5, CF4 bulk 150/250 km/s, PPC 공분산 확대, leave-one-probe-out (`R52_JOINT_RESULT.json#sensitivity`).

## 검증

- Cobaya: 기존 MCMC kernel, 외부 Likelihood, affine whitened 좌표. 해석 posterior와 평균 차 ≤0.024 sd, sd 비 0.99–1.02. affine map이 해석 공분산을 쓰므로 이는 sampler 검사다; 독립 대수 검사는 stacked GLS (평균 차 5×10⁻⁹ sd).
- 첫 Cobaya 시도(u 좌표)는 sd 비 1.5–3.9로 미수렴 → 폐기, 로그 보존.
- 테스트 55 passed (tests/r49–r52), frame-composition 부호 회귀 포함.
- 독립 심사 1회: critical 1 (CMB dipole 부호 β_MO+β_RM, CF4는 −cβ_RM로 서로 모순), major 3, minor 4. 모두 수정·재실행. 수정 전 결론(“counts와 CF4 일치, Wald 21”)은 부호 오류의 산물이었다.

## 다섯 view

x = 17D signed joint posterior. Q·F·Pi: unavailable (K0 gauge, anchor, 같은 추정량 joint null 없음). G_F: CF4 창별 dipole 잔차(기술적 대비, 보정된 depth law 없음).

## 남은 의무

count-dipole 계통오차 예산, CF4 경험적 공분산, Gaia E2 공간계통·per-source 가중, ω 식별, β_RM(z*)→β_RM(0) 진화 map, 같은 추정량 velocity null.
