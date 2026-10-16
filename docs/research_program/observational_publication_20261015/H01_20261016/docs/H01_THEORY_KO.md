# HTT six-paper publication DAG: P3/H01 source-window theory

2026-10-16 KST. Authoritative upstream six-paper DAG `research/htt-observation-publication-dag-20261015@58bb3fa00093e36b5915c8ba87f03d7b14568bd8`, schema `htt.observational_six_paper_dag/1`, 42 nodes. This task closes **only P3/H01**, not the six papers or their journal admission. The user's original dirty checkout is untouched.

## Precise observational working-law definition

For a selected, published Cosmicflows-4 **group** with CMB-frame redshift `z_i`, shifted published modulus `DMzp_i`, direction `n_i` in J2000 ICRS and reported formal modulus error, define `d_i=10^((DMzp_i-25)/5) Mpc` and **working redshift velocity** `u_i=cz_i km/s`, `c=299792.458 km/s`. This is a low-redshift *operational proxy*, not the exact cosmological luminosity distance law nor a measured physical 1+3 expansion scalar. Even the absolute zero-point of `DMzp` is subject to source release conventions. The `H_W` numerical proxy is conditional on these choices.

Choose a **fixed, declared** radial/sky weight (centres `z_c`=0.025, 0.040, 0.060, 0.080; bandwidth `s_z`=0.012),

`w_{iW}=exp[-(z_i-z_c)^2/(2s_z^2)] (1+alpha_W n_{iz})/[sigma_{i,W}^2]`, with `alpha_W` in {0,0.6}, where the declared *working diagonal proxy* is

`sigma_i^2 = (250 km/s)^2 + [(ln10)/5 * (70 km/s/Mpc) d_i e_{DMzp,i}]^2`.

This is an assumed diagonal velocity-proxy variance, **not** an empirical CF4 method-zero-point/velocity/selection law. Fix weights for analytic response and zero-point derivatives. Set

`D_W=sum_i w_i d_i^2`, `H_W=sum_i w_i d_i u_i/D_W`, `alpha_{Wi}=w_i d_i/D_W`.

Units: `H_W` km/s/Mpc, `D_W` sums `(Mpc/(km/s))²` under inverse velocity-square weights. The normalized linear response for a declared synthetic radial-speed model

`u_i=H0 d_i + d_i D·n_i + B·n_i + d_i n_i^T Q n_i`, `Q=Q^T`, `tr Q=0`

is exact:

`H_W=H0 + D·m_W + B·b_W + Q:Q_W`, where

`m_W = sum_i w_i d_i² n_i/D_W` (dimensionless),
`b_W = sum_i w_i d_i n_i/D_W` (`Mpc^-1`),
`Q_W = sum_i w_i d_i² (n_i n_i^T-I/3)/D_W` (dimensionless STF).

Thus a source-dependent angular window can mix a purely dipole or STF quadrupole **template** into the scalar `H_W`; without separate response these cannot be called measured anisotropic geometry. Antipodal equal-area `±x,±y,±z` exactly gives `m=b=Q_W=0`; an explicitly distorted north-weighted window breaks cancellation (tested numerically).

For **the same 35970 source groups reused across windows**, conditional covariance under this diagonal **working-law only** is `C_{WW'} = sum_i alpha_{Wi} sigma_i² alpha_{W'i}`; it is generally non-diagonal. Additional shared calibration terms would be `A C_shared A^T`, which is missing rather than set to zero as a physical statement. Full covariance is UNKNOWN.

In a fixed-depth source where `d_i=d_*`, the response design columns for `D·n` and `B·n` are proportional, giving an *exact local angular-dipole versus bulk velocity confounding*. Variable source depths can algebraically restore rank without proving robust separation. Report the 3 principal cosines of the two nuisance-projected column subspaces rather than call numerical rank a physical identification.

At **frozen weights** only, a uniform shift `mu_i->mu_i+Delta_mu`, thus `d_i->lambda d_i`, yields exactly `H_W -> H_W/lambda`, `lambda=10^(Delta_mu/5)` (Wolfram exact symbolic and direct numerical test). If weights are re-evaluated from errors that depend on `d_i`, the simple ratio no longer holds without a recomputation.

## Scientific boundaries and literature overlap

- Same CF4 Table3/4 release group source, one correlated group catalogue. This is a **working redshift/angular window estimator**. No exact `H(z,n)`, no deceleration `q(z)`, no volume expansion `Theta/3`, no global tilt, no rotation/covariant shear posterior.
- Selection function, calibration overlap, peculiar-flow reconstruction, redshift errors, and full method+sky covariance are unmeasured or unauthenticated here. A conditional diagonal Gaussian MC verifies algebra, not actual coverage or false-positive control.
- Source's `n_J2000` ICRS direction, not automatically Galactic. STF response orientation must retain that frame.
- Overlapping competing papers: Boubel et al., JCAP 03 (2025) 066, doi:10.1088/1475-7516/2025/03/066; Stiskalek/Desmond/Lavaux (2026), arXiv:2509.14997; Salzano et al., Phys. Dark Univ. (2026), doi:10.1016/j.dark.2026.102382; and **Kalbouneh et al., JCAP 03(2026), arXiv:2510.02510**, directly studying CF4/Pantheon+ redshift-dependent anisotropic expansion and covariant cosmography. The latest comparator was missing from the historical six-paper matrix and is essential at X02/H05. Window algebra by itself is NOT a new paper.

## H01 exit gate and next research action

H01 gate: source SHA verified; dimensional/mask and STF cancellation/injection tests PASS; overlap covariance and co-linearity tested; output interpretable only under an explicit working law. H01 can become `completed_scoped` in the six-paper **publication research DAG** with these receipts, NOT a published P3 result.

H03 becomes structurally READY after H01 but requires a carefully preregistered finite radial/method holdout, cross-window treatment and real-source coefficient/tomography. H02 remains external-data blocked pending actual release method-calibration and peculiar-velocity selection model. X01/X02/X03 remain pending, as are P1/P2/P4/P5/P6 paper milestones. No main merge/journal submission.
