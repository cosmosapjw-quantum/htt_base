# R65 R8: resolve the actual peak-versus-integrated-flux input

This bounded refinement was admitted after the registered R7 computations and
before a final review. It is not a successor research loop. The original raw-peak
experiment, bootstrap and results are retained without relabeling.

Observed defect: the existing raw NVSS FITS PEAK INT is genuinely raw peak
brightness in Jy/beam. Official NRAO documentation distinguishes it from
Gaussian-component integrated flux. Direct coordinate matches to the newly
released provider catalogue confirm the difference; for a resolved component,
raw peak82.667mJy/beam, provider peak82.9mJy/beam, integrated149.5mJy.
Applying the ideal integrated-flux boost response to the raw peak selection
therefore has an actual source/estimand qualification problem.

Concrete repair input: the version-pinned RACS paper release supplies
Full_NVSS_combined_named.dat (140767191bytes), advertised SHA256
52eb576c1e3e71837f2fca26121789ccc0b316152cca3f25ea2f37ea8ef5a38e.
Its integrated_flux and peak_flux are distinct; the provider's actual Figure2
code uses integrated_flux in mJy. The exact original extraction program was not
located; this remains provider-release provenance, not exact original pipeline
replay. The root performs full-file download/hash verification separately from
the lane's small source/header reads.

## Fixed additional experiment, before new fits

Use only the already registered base64 geometry: NSIDE64, pixel dec>-37deg,
|Galactic b|>10deg, and the same disjoint numerical bounds20,40,80,infinity.
On the same finite positive provider rows, fit provider peak selection in
mJy/beam and integrated-component flux selection in mJy. Each has dipole-only
and dipole+four-STF modes, giving four additional observed models. Reuse the
verified R65 conditional likelihood and response comparison code. Do not rerun
the earlier bootstrap or turn this refinement into another mask scan.

Retain the per-pixel four-by-four joint membership table, including the
below-threshold category in each field. This binds overlap and source migration.
Compute the common transverse-dipole influence of a source in bin b/pixel p:

    a_bp = (f_p - E_q[f|ring]) M_b C_theta[:, :2].

Here M_b is the exact common-dipole/per-bin-STF parameter map, and C_theta is the
inverse common-fit information. Ring-total profiling and free STF nuisance are
both included. Under an independent-source Poisson working model the empirical
paired sandwich blocks are

    C_LL = sum_bp N_L,bp a_L,bp a_L,bp^T,
    C_RR = sum_cp N_R,cp a_R,cp a_R,cp^T,
    C_LR = sum_bcp N_shared,bcp a_L,bp a_R,cp^T,
    C_delta = C_LL + C_RR - C_LR - C_LR^T.

The shared-source block must not be dropped. This is an influence/large-sample
source-Poisson covariance, not a complete clustering covariance or exact
finite-sample cosmological test. Different field selections have different
population mixtures: a measured difference is not automatically an instrumental
bias. Complete the actual field comparison and stop this refinement.

Only new overlap/source-adapter semantics receive focused checks. The already
passed base24tests are not repeated merely for another PASS. The original
bootstrap calibrates the original raw-peak common-vector question only.

## Scope of the repair

An available integrated column must no longer be described as missing. Its use
closes that input gap and permits an explicit integrated-flux response diagnostic.
It does not by itself supply the spectral distribution at bin boundaries, the
parent catalogue peak-detection selection, Gaussian-component grouping into
physical galaxies, bin-dependent redshift kernels or the LSS cross covariance.
Those inputs remain named publication obligations, not reasons to omit this
feasible calculation. No NVSS–RACS joint p-value or physical global-tilt result
is authorized by this refinement.
