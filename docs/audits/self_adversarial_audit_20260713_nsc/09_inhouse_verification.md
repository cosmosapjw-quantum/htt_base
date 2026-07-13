# NSC audit — in-session independent verification of the workflow's P0/P1 findings

_Executed 2026-07-13 in the main session (NOT by the lanes themselves) before any finding was
accepted into the PDR. Every number below is the output of a fresh in-session run._

## V1 — C3-P0: the pk_corr = (370/308)^2 premise (VERIFIED, P0 CONFIRMED)

Fresh CAMB 1.6.6 run at the exact fiducial (Om=0.3153, ob=0.0493, h=0.6736, ns=0.9649,
sigma8 rescaled to 0.8111), sigma_v_1d = sqrt((100f)^2/(6 pi^2) int P dk), k = 1e-4..50 h/Mpc:

```
EH98 in-repo sigma_v_1d          : 308.09 km/s
CAMB LINEAR sigma_v_1d           : 309.0 km/s   (f = 0.5296)
CAMB halofit(mead2020) sigma_v_1d: 373.1 km/s
```

EH98 agrees with the true linear value to 0.3% — there is NO ~15% linear deficit;
`SV_LINEAR_STD = 370.0` ("standard linear sigma_v,1D", `scripts/cf4_velocity_correlation_ml.py:57`,
`scripts/cf4_mv_bulkflow.py:59`) matches the NONLINEAR dispersion to 0.8%. The fsigma8
headline 0.40 +/- 0.02 = raw 0.486 / sqrt(1.4423) therefore rests on a refuted premise. In the
MV lane the same constant only INFLATES the covariance (conservative direction) — mislabelled,
not sign-wrong there.

## V2 — C2-P1: Hermitian-plane power deficit in the GRF generator (VERIFIED, P1 CONFIRMED)

`htt/obsstat/pv_forward_mocks.linear_velocity_grid` source contains no conjugate-symmetrization
of the kz=0 / Nyquist planes (checked: `'conj' not in source`). Fresh measurement, n=32,
box=500, 12 seeds, against the analytic band variance hf2/(6 pi^2) int_kf P dk:

```
per-component variance ratio (vx, vy, vz) = (0.843, 0.829, 0.997)
```

vx/vy deficient, vz intact — exactly the kz=0-plane half-power signature (in that plane
v ∝ (kx, ky, 0)). Matches the card's shipped cov_ratio 0.925 mechanism at production
resolution. Direction of the error: mock variance LOW -> calibrated sigma HIGH.

## V3 — C1-P0: radial-monopole leakage into the MV bulk flow (VERIFIED BIT-FOR-BIT, P0 CONFIRMED)

Fresh full re-run of the shipped pipeline (`_load_cf4 -> fit_sigma_star -> _bin_cells ->
pair_velocity_covariance -> ideal_window_target(200) -> mv_bulk_flow`), then the attack:

```
sigma_star = 50.0  (== fit grid floor np.linspace(50,600,56)[0] -> RAILED)
n_cells = 1389
inverse-variance shell means of the analysis-cell S values [km/s]:
  r =   0- 30: -32   |  30-60: -11  |  60-90: -5   |  90-120: -32
  r = 120-150: +38   | 150-180: +23 | 180-220: -85
  r = 220-270: -612  | 270-330: -1965 | 330-400: -3853 | 400-520: -5765
reproduced |B|(200)            = 405.22 km/s   (card: 405.22 — exact)
pure-monopole response |B|     = 473.49 km/s, direction dot(full estimate) = 0.993
data-minus-monopole |B|(200)   =  84.93 km/s
monopole-nulled constrained MV (uniform-flow unbiasedness preserved,
  max|G^T w - I| = 2.9e-15, max|U^T w| = 3.2e-15):
  |B|(200) = 94.8 km/s, per-comp err ~77, chi2_3 = 1.66, p = 0.647  ->  0.46 sigma
```

The deep-shell means are physically impossible as flow (linear-theory RMS ~300 km/s) — a
catalogue-level Vpec radial systematic (deep-end log-distance/Malmquist class). The MV
constraint G^T w = I nulls only uniform flows; anisotropic deep coverage converts the monopole
into a fake dipole aligned (dot 0.993) with the shipped headline. With shellwise monopole
patterns appended to the constraint set, the tension vanishes. The K5-MV headline
|B|(200) = 405 km/s and the 4.4-5.4 sigma range are REFUTED at their claimed tier; the
downstream K5-MOCKSIG 5.76 sigma calibrated an artifact its GRF mocks (no radial systematic by
construction) could not catch. NOTE: Watkins+2023's published 419 +/- 36 uses their own
bias-corrected velocity estimates, not the catalogue Vpec column, and its vector is 81.6 deg
from ours at R=200 — the published result is NOT automatically refuted by this finding; our
scalar-amplitude "consistency" with it was coincidental.

## V4 — C9-P1: rev-r195 cosmic-variance block computed with cz as Mpc (VERIFIED, P1 CONFIRMED)

`scripts/cf4_bulkflow_lcdm_variance.py:173-174` builds `pos` from SGX/SGY/SGZ (km/s, cz
supergalactic Cartesian — the very fact documented at `scripts/cf4_mv_bulkflow.py:84-87`) and
names its norm `r_mpc`. The window integral therefore sees a fake survey ~71x too deep
(median norm/Dist = 71.16 per the lane probe), collapsing sigma_cv to 35 km/s; the in-card
"~10% depth-scale residual" caveat is wrong by ~a factor 67. The card's significance was
WITHHELD (rev-r195 honesty call), so no false headline shipped — but the stated reason
("linear CV is a lower bound") understates the actual defect.

## Verification status of the remaining P1s (lane-evidenced, spot-checked, NOT independently rerun)

| Finding | Spot-check performed | Status |
|---|---|---|
| C2 pk_corr omission in mock lane | grep: no SV_LINEAR_STD/370 in mock lane; card cross-read | ACCEPTED |
| C4 z-grid quadrature (C_1 x1.36) | lane snippet nz=40 vs 800; code line desi_dipole_mock_significance.py:110 read | ACCEPTED (rerun = remediation) |
| C4 alpha not re-estimated in mocks | code lines desi_dipole_measure.py:65 vs number_count_dipole.py:130-134 read | ACCEPTED |
| C5 UL alm-space scoping | card + README:159-187 citations read | ACCEPTED (wording fix) |
| C6 0.009 = 2nd-order stencil floor | lane's 4th-order (0.00064) + analytic potential-flow floor (0.00893) snippets | ACCEPTED (no-go STRENGTHENED; label fix) |
| C7 manuscript stale sites | ch04:1054-1056,1114-1117 + ch09:266 cited; matches open-items rank-1 | ACCEPTED |
| C8 registry provenance contradiction | THEOREM_REGISTRY:55-56 vs :905-913 cited | ACCEPTED |
| C10 misattributed 1.0417->1.0239 + 9-vs-14 anchors | table rows 24 vs 77 self-contradiction confirmed in v9 table read | ACCEPTED |
