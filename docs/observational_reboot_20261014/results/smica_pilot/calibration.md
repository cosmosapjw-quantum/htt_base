# EXPLORATORY retrospective SMICA delivered-simulation ranks; NOT physical Planck p

Fixed B=240; declaration `smica-reboot-fixed-four-powers-train60-cal240-v1`.

| Feature | Tail | Signed value | p rank | Joint-max adjusted p | q interval (unadjusted) |
|---|---|---:|---:|---:|---|
| C_2_microK2 | two-sided | -1.16137 | 0.112033 | 0.53527 | [0.071998, 0.154695] |
| C_3_microK2 | two-sided | -0.627411 | 0.53527 | 0.946058 | [0.468058, 0.597775] |
| C_4_microK2 | two-sided | -0.513247 | 0.568465 | 0.975104 | [0.501394, 0.630272] |
| C_5_microK2 | two-sided | 1.00528 | 0.26971 | 0.697095 | [0.211833, 0.327365] |

Global joint-null p_rank=0.53527 (128 >= exceedances, 0 ties).
Global q interval=[0.4680579272179676, 0.5977753043684926] at confidence 0.95.

Exploratory delivered-simulation rank under assumed observed/paired-null exchangeability, conditional on independent training and fixed current feature family. Retrospective selection prevents confirmatory physical Planck p interpretation.
Marginal Clopper-Pearson interval for IID null exceedance probability q conditional on fixed observed threshold and training. Not an interval for realized p_rank; not simultaneous across features.
Global max-score test and single-step adjusted ranks control error under the complete joint null. Strong FWER under partial alternatives needs extra conditions, not asserted.
Observed feature calibration; no inferred shear, global tilt, Bianchi family detection, posterior or evidence.

Provenance attestations are validated mechanically and have not been independently verified.

Scientific admission: EXPLORATORY retrospective conditional delivered-simulation model only.

Residual foreground mean, residual systematics, fixed actual-data weights and the full physical null are unverified. Unique simulation IDs do not establish their law.

Input microK; fitted retained coefficients microK; powers microK^2. Full ell0..5 OLS fits nuisance monopole/dipole simultaneously before retaining ell2..5; no physical dipole/global-tilt/shear estimate.
