# HTT R95 Local Science Execution Report

- R78 DAG SHA256: `90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11` (60 nodes, 129 hard edges, `NEXT_ID=SQ-CF4`)
- `original_science_status_changed = false`, `actual_r95_physical_science_acceptance = false`

## Group Summary (Source-Conditioned vs Publication Gate)
- **G02 / SQ-CF4 (P3)**: R36 36D parity=2.42e-13; R5 H0=72.93+/-0.36 (cal=0.05 -> 72.01+/-1.11); K02 Fortran 35,970-group backend=fortran_source_info_cross. (`SQ-CF4 = BLOCKED_INPUT` 유지; `sigma_cal^2 I_7`는 비승인 sensitivity curve)
- **G03 / Gaia (P6) + K02**: SO(3)/STF5 oracle max=5.11e-14; Scan-law ecliptic m=0 fraction=0.9976; Quaia inv-noise 10x10 JK Wald10=17.71. (`actual_normal_vorticity = None`; K02 CF4 Fortran + Gaia P6 연계)
- **G04 / Radio (P4)**: 5 surveys (19 flux thresholds): d_obs/d_EB in [2.83, 19.80], JK/Poisson in [1.01, 4.73], RACS source-rms bias=4.69x. (`joint_five_survey_covariance_qualified = False`)
- **G05 / Planck (P2)**: 999/999 CMB + 300 unique noise (NSIDE=2048, lmax=48); C++/NumPy Gaunt max_abs={'T': 1.27675647831893e-15, 'E': 1.1657341758564144e-15, 'B': 1.4432899320127035e-15}; SMICA 20D p300 (T,E,B)=(0.3322, 0.3721, 0.3156); 60D TEB p300=0.2591. (`commander_null_qualified = False`)
- **G06 / P1**: 2048 coupled draws Manski unk=0.25 W3=[0.0049, 0.2549]; neg-ctrl isotropic 50-draw mean_rank_p=0.459; physical_Pi=None, physical_GF=None. (`physical_Pi = None, physical_GF = None`)
- **G07 / Bianchi (P5)**: 17 Einstein-Euler evolutions max(Ham=2.02e-10, Cod=7.49e-11, BASS-HTT=1.67e-17); HyRec-2+tanh z_star=1088.80, tau_reion=0.05411; Rank-9 Thomson energy=4.38e-15, L60 m0_TE_dim=120 (projected all-m T+E+B dim=11155, not executed). (`SQ-NATIVE, B02-B05` 미승격)
- **G08 / PHY-01..07**: 7개 교차 경로 모두 R95 실계산으로 연결 완료 (`cross_probe_joint_likelihood_qualified = False`).
