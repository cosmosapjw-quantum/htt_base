# 수치 실험 종합 요약

| 실험 | 대상 주장 | 판정 | 핵심 수치 |
|---|---|---|---|
| exp01_parent_identity | P1/F1: 부모 항등식, c=(1,-1,1,1), 규약표(3배 결함), (3/2) 규칙 | **PASS** | omega_ab_omega_ab_eq_2_omega_a_omega_a=True; budget_identity_residual_zero=True |
| exp02_identified_set | P26/P31/A8: 등록 구간 [0.11,0.17] 재현 + Ω_k 부호 도메인 결함의 정량 효과 | **WARN** | registered_one_sided_interval=[0.11, 0.17]; matches_E1_[0.11,0.17]=True |
| exp03_two_stage_coverage | P35/E2/E3: 사양검정 크기·검정력, IM 끝점 보정 커버리지 순서, 나이브 붕괴 | **PASS** | stage1_size_at_a0=0.05175; power_curve(amps->rate)={'0.0': 0.0518, '0.1': 0.086, '0.2': 0.211, '0.4': 0.732, '1.0': 1.0} |
| exp04_joint_vs_naive_gf | P36: joint⊂naive 재현 + '엄격성: c_N,c_D≠0이면 항상' 진술 반례 | **REFUTED** | competing_regime_joint=[0.72727, 1.11111]; competing_regime_naive=[0.61538, 1.27778] |
| exp05_evalue_merge | P19/P29/E5/E7: 의존성-강건 병합, Ville 임의시점 유효성, §10 평균 정책 | **PASS** | merged_mean±SE=0.9971 ± 0.0042; markov_tails_ok(t=5,10,20)=True |
| exp06_shear_memory_bias | P13/F3: κ̂ 편향 0-교차 e0=1, 단조성, 끝점 수치의 구동-이력 종속성 | **PASS** | zero_crossing_A/B=[1.0, 1.0]; bias_at_e0=0_A/B=[0.4568, 0.3627] |
| exp07_rank_and_duplication | P8/P9/P18/P22/P30: 랭크 2→4, 방사 무감, 열/행 복제 정보 산술 | **PASS** | max|n·Ω·n|_over_200_draws=1.0986930380857832e-16; rank_current_channels=2 |
| exp08_cl_dispersion_fisher | P16/P17: 2/(2ℓ+1) 상대분산과 다중-ℓ Fisher 하한 | **PASS** | frac_var_l2_mc=0.39182; frac_var_l2_target=0.4 |
| exp09_prior_exposure | P28/E8: 인자화 사전 → 널 방향 KL=0; 결합 사전 → KL>0 (사전 구동 이동) | **PASS** | KL_factorized_prior=0.0; KL_coupled_prior=0.43691746196562486 |
| exp10_chi2_blindness | P32(iii)/P23: 중심 χ²는 L>0 공분산 방향에 1차 무감, score는 감지 | **PASS** | trace_of_modulation=0.0; chi2_mean_slope_vs_alpha=0.00439 |
| exp11_hartlap_effect | M5': Hartlap/SH 보정 크기 정량화 + 미보정 사양검정의 크기 왜곡 | **PASS** | hartlap_factor_table={'m=5,Nsim=300': 0.9799, 'm=5,Nsim=600': 0.99, 'm=10,Nsim=300': 0.9632, 'm=10,Nsim=600': 0.9816, 'm=20,Nsim=300': 0.9298, 'm=20,Nsim=600': 0.9649, 'm=30,Nsim=300': 0.8963, 'm=30,Nsim=600': 0.9482, 'm=50,Nsim=300': 0.8294, 'm=50,Nsim=600': 0.9149}; chi2_mean_uncorrected(m=10,Ns=300)=10.437 |
| exp12_bianchi_v_constraint | P5/F2: Σ²_BV 공식, (4/3)β² 보정, β² 오차 스케일링, Ω_K≤0 raise | **PASS** | small_tilt_formula_matches=True; first_correction_coeff=4/3 |

판정 의미: PASS=주장 재현 확인, REFUTED=진술문 그대로는 반증(반례 제시), WARN=주장 유지되나 도메인/전제 결함 확인.
