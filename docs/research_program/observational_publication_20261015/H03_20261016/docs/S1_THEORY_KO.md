# HTT six-paper P3/H03 S1, windowed angular tomography theory

Source authority: `research/htt-sixpaper-p3-h01-window-20261016` PR #540, six-paper `PUBLICATION_DAG.json`, exactly `H03` (P3); do not change any other paper node. Existing CF4 35,970 group source NPZ SHA256 `86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c`. This is a real-data processing-geometry, **not** a physical expansion, peculiar-velocity or source-selection likelihood.

## Typed model and estimator

At input group i, d_i[Mpc]=10^((DMzp_i-25)/5), u_i[km/s]=c z_CMB,i. ICRS/J2000 unit n_i. Let {T_A}_A=1..5 be real 3x3 Frobenius-orthonormal STF basis. The 9-vector row is X_i=d_i[1,n_ix,n_iy,n_iz,n_i^T T_1 n_i,...,n_i^T T_5 n_i], and coefficients theta_w=(h0_w,D_wx,D_wy,D_wz,q_w1...q_w5) in km/s/Mpc. This corresponds to a *working* directional proxy H_w(n)=h0_w+D_w.n+n^T Q_w n; Q_w=sum q_wA T_A and ||Q_w||_F=||q_w||_2. It is neither Theta/3 nor a Bianchi shear measurement. Contrasts in different w windows need joint covariance.

For four **fixed before inspection** Gaussian windows at z_c=.025,.04,.06,.08, bandwidth .012, define g_i=exp[-(z_i-z_c)^2/(2*.012^2)], assumed source variance sig_i^2=250^2+[70*(ln 10/5)*d_i*e_dmzp,i]^2 (km/s)^2, and w_i=g_i/sig_i^2. Solve WLS by thin QR of sqrt(W) X: 

 theta_w=(X^T W_w X)^-1 X^T W_w u = A_w u,    A_w=R_w^-1 Q_w^T sqrt(W_w).

We keep one symbol Q_w for the physical tensor only where clear; QR Q matrix is computational and unrelated. The exact *declared diagonal working-noise* joint covariance for overlapping windows is Cov(theta_w,theta_v) = A_w diag(sig_i^2) A_v^T. Four windows yield 36x36 covariance. No independent multiplication of four likelihoods is justified. All four use the same 35,970 groups and hence share source noise and systematic channels.

A 9-dimensional fit can remove apparent monopole leakage from dipole and quadrupole columns on an incomplete sky, so h0_w differs from H01's monopole-only H_W. The response of the fit to an injected peculiar bulk B[km/s] is A_w n B and has coefficients (km/s/Mpc); its dipole component has 1/Mpc units. The expansion-dipole response to d*n D[km/s/Mpc] is exactly D under full-rank WLS. If all distances equal d0, the two input sets d*n D and n*B are linearly dependent, so a single shell cannot distinguish these causes; with varying distance the design rank may increase without validating physical models.

## Scope, selection and independent tests

The window centers, fixed sigma, masks and 9D angular basis are retrospective working choices inherited from H01, not prospective cosmological-null declarations. The source methods FP/TF/SN/OTHER are pooled by a preexisting group release; we will perform four deterministic family-delete sensitivity fits and 12 ICRS patch deletes (2 hemispheres x 6 equal azimuth sectors), always using the same distance data and the same fixed noise *assumption*. These deletes are correlated perturbations of one catalogue, not independent field measurements.

Acceptance for *H03 scoped descriptive completion* requires: 35,970 source hash; four 9D WLS fits and an exact 36x36 PSD shared-window covariance; injection and QR-vs-independent least squares; method and 12 sky-patch delete stress; difference versus H01 monopole-only calculations and explicit categorical physical blockers; source-bound create-only replay and benchmark/manifest. Covariant H, true selection, peculiar velocity likelihood, independent source calibration, detection sigma, novel publishable result and physical Bianchi claims remain HOLD.

## Literature comparison

- Tully et al. 2023, Cosmicflows-4 (ApJ 944,94), DOI 10.3847/1538-4357/ac94d8: method-overlap source catalogue; raw group releases do not automatically provide full method/source covariance.
- Boubel et al. 2025, JCAP03(2025)066, DOI 10.1088/1475-7516/2025/03/066: TF zeropoint dipole and local-flow alternative. A new single apparent dipole fit is not enough novelty.
- Stiskalek, Desmond & Lavaux 2026, MNRAS 546(2), DOI 10.1093/mnras/staf2048: data-template dipole does not imply expansion anisotropy with radial local-flow freedom.
- Kalbouneh et al. 2026 arXiv:2510.02510: CF4/Pantheon+ multipole tomographies and covariant cosmography. The present 9D WLS is an **estimator/assumption comparison only**, not an independent novelty or replication of their physically motivated cosmographic model.

Native subagents NOT_RUN if no such host dispatch available; a serial NumPy and Wolfram basis/Gram check is not a second independent reviewer.
