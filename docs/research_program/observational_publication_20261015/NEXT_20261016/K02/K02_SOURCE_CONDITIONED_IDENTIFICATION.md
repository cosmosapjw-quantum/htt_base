# K02: CF4 source-conditioned shape identification and optical limits

2026-10-16 KST; branch parent PR #544 head da712f30605fcf3c94dff1ca2ff623719d70005c.

**Source:** 35,970 unique CF4 group IDs, locked NPZ SHA-256 `86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c`. Four fixed Gaussian redshift windows z=(0.025,0.040,0.060,0.080), width 0.012. The working WLS law uses `d=10**((mu-25)/5) Mpc`, `y=cz_CMB km/s`, and fixed illustrative variance `sigma_y²=250²+(70 ln(10)/5 d sigma_mu)²` in (km/s)². This is NOT a calibrated physical velocity likelihood.

Method-profiled design `[M4|X8]` has `M_m = d 1[method=m]` (four zero-point intercepts) and `X8=d[n_x,n_y,n_z,n_i T_a^{ij} n_j]` for five Frobenius-orthonormal spatial STF tensors. The phenomenological monopole `d=sum_m M_m`, so the unregularized 13-column augmentation has exact rank 12. Each of four actual windows identifies the **eight apparent directional shape coefficients** under the stated noise/source; the physical monopole does not survive unrestricted four-method intercepts.

A four-window joint estimator keeps original shared-group correlations. Numerical results: conditioned 32x32 angular-shape covariance eigenvalues min `0.0031987567381872987`, max `0.8559175912456349` in (km/s/Mpc)²; dipole norms by window `[3.11405108,2.83227807,2.69400454,1.26450039]` km/s/Mpc, STF5 norms `[2.26014698,3.16522733,3.74780954,2.11791488]`. Different nuisance model means do not compare naively to earlier raw 9D H03 fits. Numerical JSON `K02_CF4_CONDITIONED_SHAPE_RESULT.json` SHA256 `4bcc02e7a01f87926eb3b460d49d6e8c9fc9e42c9f4e2f1f0e52474523d4df05`.

The established *observer-local*, leading-redshift optical coefficient for one congruence `u.u=-c²` and source-looking sky direction `n` is `H_opt(n)=Theta/3-(A.n)/c+sigma_ab n^a n^b`. `H,sigma`: s^-1; `A`: m/s²; `c`: m/s. Its 9 physical directions decompose 1+3+5; vorticity does not enter this scalar at leading order. See [Heinesen 2021 JCAP](https://doi.org/10.1088/1475-7516/2021/05/008). **Do not equate** the survey's eight fitted apparent coefficients to physical acceleration/shear without source-selected optical/Jacobi, common-congruence, peculiar-velocity and calibration response. This is a conditional WORKING_LAW rank result, not physical beyond-FLRW detection.

Sandbox verification: source hash, STF orthonormality, exact method rank deficiency, PSD correlated covariance, O(3) metamorphic check, four single-method deletion checks: **7/7 PASS**. Full result arrays, test code, source NPZ and clean replay in recovery ZIP `HTT_SIXPAPER_X02_K02_S02_L01_20261016.zip`, SHA256 `e14d946b246c2325b6f680f94deb1797f764ec128bdd12a19a0002f8046b8a62`. Clean extraction 27/27 scoped tests across X02/K02/S02/L01/external prerequisites. Repo-wide CI and native independent subagent NOT_RUN.

**Scoped K02 admission:** source-conditioned apparent rank/identified-subspace ONLY. K04 true physical posterior retains external missing.
