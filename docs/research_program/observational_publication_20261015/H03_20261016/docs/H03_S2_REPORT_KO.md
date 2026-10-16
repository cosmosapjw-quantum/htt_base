# 2026-10-16 HTT six-paper P3/H03 scoped observational processing result

## Data and physical scope

- Source: **35,970 real published CF4 groups** via frozen Loop6 selected source, SHA256 `86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c`. Source is a derived CF4 group file, not full survey law.
- Assumed H01 retrospective window centers z={0.025,0.040,0.060,0.080}, Gaussian width 0.012, no post-result retuning, J2000/ICRS sky.
- d=10^((DMzp-25)/5) Mpc, u=cz_CMB km/s, **assumed** sigma_i²=250²+[70*(ln10/5)*d_i*e_dmzp]², fixed-weight WLS per window.
- 9D design: h0 + D·n + n^T Q_STF n, Q in Frobenius-orthonormal 5-tensor basis. These are **apparent working coefficients**, not covariant Θ/3, geometrical σ/H, tilt or velocity-corrected H0.

## Actual four-window nine-coefficient results

| z center | 9D h0 [km/s/Mpc] | H01 monopole-only | norm D [km/s/Mpc] | norm Q_STF [km/s/Mpc] | WLS condition | method FP distance weight |
|---:|---:|---:|---:|---:|---:|---:|
| 0.025 | 75.167996 | 74.629348 | 3.332161 | 2.166730 | 4.130 | 30.371% |
| 0.040 | 75.303212 | 74.343818 | 2.996321 | 3.175257 | 4.656 | 53.492% |
| 0.060 | 74.559217 | 72.516333 | 2.708324 | 3.753386 | 6.979 | 80.241% |
| 0.080 | 72.445152 | 70.810223 | 1.876692 | 1.952792 | 13.979 | 90.189% |

- H01 apparent monopole is not the same estimand as 9D nuisance-adjusted apparent monopole: differences are +0.53865, +0.95939, +2.04288, +1.63493 km/s/Mpc. The mask/redshift/method composition changes materially across windows.
- Baseline window FP source-distance weights increase from ~30.4% to ~90.2%. The method composition by window is a major open systematic, not a physical anisotropy measurement.
- Apparent dipole directions are reported as ICRS J2000 Cartesian derived from the fitted D; no Galactic axis identification or cosmological detection is claimed.

## Exact shared-row conditional covariance and contrast
- Four 9D estimates are *one catalogue reused*, not four independent cosmological observations. Full same-row conditional covariance is the 36×36 matrix C_rs=A_r diag(sigma_i²) A_s^T.
- The 36×36 matrix is symmetric and strictly positive in this working fixture: min eigenvalue 0.00101644, max 0.921140 (unit coefficients squared), under **diagonal group errors only**.
- Monopole correlations for successive z windows: 0.702, 0.563, 0.414; the z=.025 vs .040 difference formal SD with cross-correlation is 0.09610 compared with naive-independent 0.17590 km/s/Mpc. The variance model is NOT an empirically released CF4 method-calibration or flow covariance.
- Independent QR-versus-SVD reproductions at z=.025,.080 deviate only 2.89×10^-14 and 3.09×10^-14 km/s/Mpc; direct covariance recontraction max abs 5.55×10^-17.

## Method/patch sensitivity, not independent nulls
- Four existing method-family leaveouts (FP/OTHER/SN/TF) and twelve fixed sky-patch leaveouts (two ICRS north/south halves times six azimuth sectors) were actually executed.
- Max method-family deletion shifts across all windows: Δh0 up to 0.880 km/s/Mpc, dipole-vector Euclidean shift up to 1.559 km/s/Mpc, STF5 shift up to 2.726 km/s/Mpc; maximum shifts occur for different exclusions/windows.
- Max one-patch deletion shifts: |Δh0| 0.557 km/s/Mpc, dipole-vector 1.185, STF5 1.623 km/s/Mpc. These are correlated sensitivity analyses from one source cohort, not resampled independent evidence.
- The positive north-weight sensitivity branch is alpha=0.6 and uses the same rows, also not an independent H0 sky measurement.

## New exact first-order source-method mean-design gauge
- For four group methods m∈{FP,OTHER,SN,TF}, define Z_m = d_i 1_{method_i=m}. Then sum_m Z_m=d_i = X_{h0} row by row. The stacked [X9,Z4] **mean design has exact one-dimensional null** and rank 12, while (I-P_Z) X9 retains rank 8 if the eight angular columns remain independent.
- The actual source-window fixed-W calculations give rank 12 and nuisance-projected rank 8 for all four z centers. This is a **first-order fixed-distance/weight mean prediction** obstruction, not a no-go for full nonlinear empirical calibration models: calibration-anchor information or additional source laws can break it.
- A common method distance-modulus zero-point nuisance is mathematically collinear with apparent h0 mean normalization, not merely an insignificant error bar. P3/H02 must supply absolute external calibration and shared-method selection covariance before physical H0 inference.

## Literature novelty and open physical gates
- Kalbouneh et al., *The anisotropic expansion rate of the local Universe and its covariant cosmographic interpretation*, arXiv:2510.02510 (2026 version) already performs CF4/Pantheon+ redshift-dependent angular multipoles and covariant cosmography. Thus the present 9D fit by itself **does not establish a new-paper novelty claim**.
- Boubel et al., JCAP 2025/03/066, and Stiskalek et al., MNRAS 2026, show that a CF4 distance template dipole can be alternatively accounted for by velocity/bulk models and survey dependence.
- Required before P3/H04: empirical source-matched peculiar flow/selection/shared-calibration covariance with heldout controls, cross-tracer comparison, complete source model and literature comparison. No retrospective p-value, statistical significance or Bayes factor from current diagonal covariance.
- This result unlocks only the scoped P3/H03 node. Six manuscript statuses remain NOT_READY_TO_SUBMIT, and P1/P2/P4/P5/P6 states remain unchanged.

## Execution and evidence
- 16 focused tests passed in the sandbox; source runner exit 0 with exact SHA256 input; independent SVD source check and covariance recontraction passed. Native fresh-context subagent/reviewer NOT_RUN.
- Source NPZ, code, full result JSON, supplementary NPZ and plots are included in immutable recovery ZIP; GitHub draft PR retains code, JSON, report, paper DAG and ready queue with SHA identity.
