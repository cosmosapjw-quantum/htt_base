# R70 / P2: 일반 Bianchi 광자 kinetic theory와 저다중극 5뷰 물리 해석

**연구일:** 2026-11-19 KST. **범위:** P2 10단계 이론 연구 R1–R10, 실제 PR3/PR4 Commander 원결과 read-only 분석. 다른 다섯 논문·일곱 R69 PHY 조합의 조건부 정리 적용은 APPLICATIONS.json. 원래 42개 DAG 및 R66/R69 입력 변경 없음. 본 결과는 새로운 CMB 이방성 검출이나 Bianchi family identification이 아니다.

## 결론 요약
이론의 가장 직접적인 증가량은 **동일한 Lie algebra로 photon redshift, celestial E1/E2/B2 angular advection, 볼츠만 brightness 및 stress transport를 하나의 계산식으로 연결한 것**이다. 물질 tilt는 Einstein 제약과 Thomson electron source로 들어오며, non-tilted Type I을 전제할 필요가 없다. signed STF5 하나만으로 물리적 다음 상태나 energy angular occupancy를 알 수 없다는 것을 *매끄러운 P4 brightness 반례*로 직접 구성했다. 이는 가설적 통계력 향상이 아니라 모형의 설명력·closure 선택의 실질적인 제약이다.

## 정리 P2-T1. 임의의 정상계 Bianchi Lie 연결에서의 photon-sky E/B 분해
(-,+,+,+), c 유지. 미래 법선 n^a, 정상계 Fermi 정규직교 invariant frame e_i. 광자 진행 단위방향 u∈S². Lie 구조상수는
C^k_ij=epsilon_ijl mathcalN^{lk}+a_i delta^k_j-a_j delta^k_i, mathcalN^T=mathcalN, mathcalN a=0.
Geodesic에서는
 d log E/dt=−H−sigma_ij u_i u_j,
 dot u=−P_u sigma u−c P_u a−c u×(mathcalN u), P_u=I−uu^T.
이 방향 흐름은 S² 위 Hodge-type
 V=grad_S Phi_E + u×grad_S Phi_B,
 Phi_E=−(sigma:uu)/2−c(a·u), Phi_B=−c(mathcalN:uu)/2.
결과적으로 shear가 **E2**, Class B a가 **E1**, 공간 곡률의 mathcalN_STF가 **B2 방향 advection**을 만든다. 이는 CMB polarization의 B-mode를 직접 계산한 식이 아니다. 일반 시공간의 비균질 source gradient, electron Thomson scattering과 선편광 기저의 spin rotation은 별도이다.

## 정리 P2-T2. 유한 시간 collisionless moment equation
동질적인 collisionless photon occupation에서 주파수 적분 밝기 I(u)=K∫E³f_occ dE에 대해
 (∂t+V·∇_S)I=−4(H+sigma:uu)I,
 div_S V=3sigma:uu+2c a·u.
p(u)=I/ρ, ρ=∫I dΩ이면 임의의 시간독립 h에 대해
 d<h>/dt=<V·∇h>−Cov_p(h,sigma:uu−2c a·u).
따라서
 dotρ+4Hρ+sigma:π−2a·q=0, π=ρS, q=ρc m.
초기 정상계 angular-isotropic p=1/(4π)에서 모든 Bianchi class에 대해 즉시
 dot m_i=0, dot S_ij=−(8/15)sigma_ij.
이는 **한 순간의 정확한 source response**이지 임의 유한 integrated shear에서 정확히 tensor proportionality가 유지된다는 뜻은 아니다.

## 정리 P2-T3. 동일 STF5의 서로 다른 진화와 점유율
고정 축대칭 sigma=s diag(−1/3,−1/3,2/3), μ=u_z에서
 p_ε(μ)=[1+εP4(μ)]/(4π), ε∈[0,1].
모두 m=0,S=0으로 동일한 STF5 초기조건과 Q_stress=0을 갖는다. 그러나
 dot S_zz=−16s/45+(8 ε s)/315,
 F_{|μ|>.9}=0.1+0.05707125 ε.
결론은 physical angular energy F와 미래 photon stress의 진화가 5개 STF 성분만으로 닫히지 않는다는 것이다. 즉 Thomson/kinetic closure 또는 고차 brightness multipole 정보가 필요하다. Positive smooth distribution으로 구성했으므로 δ-beam artifact가 아니다.

## 정리 P2-T4 및 T5. Positivity, cap bound, nonlinear 온도
m_i=<u_i>, P_ij=<u_i u_j>=δ_ij/3+S_ij라 두면
 M=[[1,m^T],[m,P]] ⪰0 ↔ P-mm^T⪰0.
그래서 모든 v에 (m·v)²≤v^TPv. 보정된 두 모멘트만으로 energy-cap event A={|u_z|>t}를 확정할 수는 없지만
 max(0,(Pzz−t²)/(1−t²)) ≤F_A≤min(1,Pzz/t²)
이라는 **물리적으로 필연적인 interval**은 얻는다.
Locally thermodynamic photon sky의 bolometric stress는
 S_ij={⟨STF(u_i u_j)(1+Θ)^4⟩}/{⟨(1+Θ)^4⟩}.
Gaunt coupling은 ell=3과 ell=1의 곱도 ell=2 stress에 연결한다. 실제 R66은 이를 이미 실행했으며 이 식 자체는 새 novelty가 아니다.

## 실제 PR3/PR4의 단위·shape·DQ 감도
R66 OBSERVABLES.json 원본 SHA256: 6d9c3f11a23995565dca25fe8ae02ef1ad79b3bc3f8ddf99f3c8c0a497b39d01. Finite-band ell<=6 release-dependent **temperature STF5 full carrier**를 사용했으며 exact T^4 nonlinear stress를 다시 측정했다고 하지 않는다. PR3 χ_full=-0.2928943624,FΩ=0.5414087522; PR4 χ_full=-0.3033583226,FΩ=0.5422803409. 미지의 DQ template 진폭 α를 [-2,2] 범위에서 단지 민감도 좌표로 움직이면 PR4 χ는 -0.7980에서 +0.2069까지, signed positive-solid-angle FΩ는 0.5702에서 0.4666까지 바뀐다. 이것은 **물리적 deboost나 α의 신뢰구간이 아니다.** 다른 R69의 exact retained radiation pi/rho signed shape와 혼용하지 않는다.
같은 하늘의 PR4 ell6→ell8 quotient 변화는 약 66.60%, NSIDE64→128 ell6 약 4.07%였다. 실제 Commander end-to-end T MC 승인 수는 0이므로 cosmic Pi는 UNAVAILABLE.

## 5뷰 판정
- **x:** R66 source-specific signed STF5 full carrier와 4D nuisance quotient를 구분. 진짜 부호·tensor 방향을 보존한다.
- **Q:** 광자 positive-moment body의 Q_stress는 선형/보존된 원천일 때 source-qualified algebraic feasibility score; q_flux가 없는 상태의 joint Q_gamma는 UNAVAILABLE.
- **Π:** 실제 Commander matched physical sky null/beam/foreground missing → NOT_CALIBRATED. 기존 이상적 Gaussian χ² tail만 source-model 조건부 수치이다.
- **F:** 온전한 intensity와 angular event가 주어지면 energy occupancy. STF5만 주어진다면 상·하한 또는 명시한 closure에서만 값; 보조 signed-orbit χ 및 solid-angle FΩ는 물리적 에너지 점유율과 다르다.
- **G_F:** 실제 last-scattering sky 한 개에는 NOT_APPLICABLE. Einstein–Boltzmann history와 동일 frame/sky transport를 얻었을 때만 epoch 변화로 도출.

## 검증과 반증 가능성
SymPy Koszul/Gamma exact residual=0 on unit sphere; arbitrary class B sky tangency max 8.7e-18, divergence residual 6.0e-12; initial photon Sdot residual 1.15e-16; smooth P4 cap/transport integration agreement <=2e-16. R66 actual source key and quotient projection identity 확인. 기존 R66/R69 41 focused tests PASS. 재실행 결과 JSON의 의미론적 일치도 검증. 독립 native subagent 심사는 미수행이므로 self-adversarial scope만 인정한다.

## 수렴 결과와 후속 연구
실측된 cosmological p-value 증가는 **없다**. 대신 Lie 구조 → 하늘 방향 흐름 → 복사 모멘트 → 물질 tilted anisotropic stress → Einstein shear 형태라는 인과 사슬을 명확히 얻었다. 다음 계산은 원래 R66의 source operator와 일치시키는 작은 Type II/V/VII_h characteristic angular-injection benchmark이며, actual physical significance 전에는 full T/E/B instrument null과 전송 경로가 필요하다.
여섯 논문(P1–P6)과 R69 PHY-01..PHY-07 각각의 수리적 정리 대응·입력 자격·중단조건은 APPLICATIONS.json과 THEORY.md R9에 기록했다. 발산 후보 R4와 수렴·stop decision R8을 보존하고, 원래 원고·DAG의 admission은 변경하지 않았다.

**Git 게시 규약:** 사용자 지시에 따라 R1–R10 각 연구 단계의 진짜 변경을 개별 commit/push한다. R1에서는 AGENTS.md에도 이 규칙을 명시했다. 원격 push 실패 시 false-success를 표기하지 않고 blocker로 남긴다. 기존 318건 이상의 다른 미추적 파일은 작업 소유권·source가 다르므로 포함하지 않는다.
