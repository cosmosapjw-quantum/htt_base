# R63 R7 CF4 published frame-correction check
Date:2026-11-17. Scope:deterministic source-contract check only; no likelihood/covariance/observer inference. Requested gpt-6.1-sol/high; observed UNKNOWN/UNKNOWN. Source device and checkout:/home/cosmosapjw/Dropbox/bianchi/htt_base on cosmosapjw, edd1b263-56a0-4391-8a2a-677dd00eabf5; HEAD f29bbab420a33aecb1c398ddd961fd45097f536b.

## Finding

**Numerically checked:** For the same35,970selected group IDs, the published correction V3k−Vh is reproduced by one fixed additive sourceward-ICRS dipole to integer-km/s rounding scale. A fixed vector for the logarithmic-redshift correction q_i=c ln[(1+V3k/c)/(1+Vh/c)] is materially less accurate, because the chart transform induces depth dependence. This is a correction-map diagnostic, not independent evidence about the observer's physical velocity or proof of the exact upstream conversion algorithm.

The published Table4 source bytes and selected-source parity are the same as the earlier r63_cf4_contract.md. Actual checks returned maxabs0 for dmzp,e_dmzp,z_CMB−V3k/c and J2000 unit vectors. No raw catalogue was copied and no file was written on the remote device.

## Fitted charts

All fits are unweighted deterministic least squares. n points from observer to source, in ICRS/J2000 Cartesian axes. Coefficients have km/s units. q/c is dimensionless; q is a logarithmic redshift-coordinate difference, not automatically a complete Lorentz rapidity.

|Fit|Vector amplitude km/s|RA deg|Dec deg|Residual RMS km/s|Maximum absolute residual km/s|
|---|---:|---:|---:|---:|---:|
|V3k−Vh=n·a|370.975268016|168.013873870|−6.989188223|0.289466972|0.508069724|
|q=n·b|353.651885981|168.056523288|−7.525351040|5.497646977|15.473242170|
|q=b0+n·b|355.166410390|168.117000517|−7.291319511|5.167405561|18.814331164|
|q from additive fit through exact scalar chart transform|same a as first row|same|same|0.274728835|0.500327698|

The additive fit vector is
  a=(-360.1906667937984,76.46973555544672,−45.141029879506874) km/s.
The fixed-q fit vector is
  b=(-343.0160520140622,72.55670669794794,−46.315967349817846) km/s.
The intercept in the third fit is b0=−2.4574388748210985km/s. It does not remove the depth mismatch. No fit-parameter covariance, standard error, confidence interval or stochastic significance has been assigned.

The three-column n design has rank3, singular values(143.086476757,97.336874784,77.600212478), condition number1.843892848. This establishes algebraic conditioning for this finite deterministic fit, not survey coverage or physical parameter identifiability.

## Depth check

Separate fitted amplitudes in disjoint fixed z_CMB bins:

|z_CMB range|N|Median z_CMB|Additive amplitude km/s|Fixed-q amplitude km/s|Global-additive residual RMS km/s|Global-fixed-q residual RMS km/s|
|---|---:|---:|---:|---:|---:|---:|
|0.01–0.02|4107|0.0157142|370.974539|365.335239|0.291015|8.058278|
|0.02–0.04|8582|0.0295821|370.975833|360.577947|0.288621|5.517511|
|0.04–0.06|6884|0.0493425|370.968141|353.763411|0.290670|2.045860|
|0.06–0.08|8189|0.0717463|370.979444|346.277471|0.288411|3.832664|
|0.08–0.100001|8208|0.0881493|370.980065|341.232943|0.289615|7.068525|

All five additive fits are within0.012km/s in amplitude. The monotone fixed-q amplitude decrease is expected from the measured additive correction's change of chart; it is not a discovered cosmological velocity history.

Given the raw published scalar velocities, the **exact arithmetic identity** is
  q_i=c log1p[(V3k_i−Vh_i)/(c+Vh_i)].
For the fitted additive correction,
  q_pred,i=c log1p[(n_i·a)/(c+Vh_i)].
At first order in |a|/c while retaining source redshift,
  q_pred,i≈(n_i·a)/(1+Vh_i/c).
The next term is −(n_i·a)^2/[2c(1+Vh_i/c)^2]. This explains why q/c≈n·constant_beta is not the correction law faithfully encoded by the CF4 published velocity pairs over0.01<z<0.1. Replacing Vh/c by V3k/c changes the expansion at higher order in the frame correction; the exact arithmetic formula uses actual Vh.

## Rounding comparison

Table4 velocities are stored as integer km/s fields. Conditional on two independently rounded nearest-integer underlying velocities, their difference has absolute rounding bound1km/s and RMSsqrt(1/6)=0.408248km/s. Conditional on an exact stored Vh plus one rounded correction output, the single rounding RMS is1/sqrt12=0.288675km/s with half-unit bound. The observed additive residual RMS0.289467km/s and max0.508070km/s are consistent with a rounding-scale additive rule; small extra direction rounding/grouping/parameter differences can affect a strict half-unit bound. These comparisons are diagnostics, not an established stochastic law for the catalogue. No exact original algorithm is certified by residual size.

Every global-additive residual and every q residual from the additive chart transform has absolute value<1km/s. Only15.34percent of the global fixed-q residuals do. An exact finite observer boost additionally involves direction aberration, transverse terms and frame/tetrad convention; the successful scalar chart fit does not certify those components.

## Implication for existing R63 calculation

Use the published row-level q_i if the selected experiment needs the actual applied redshift operation. It can be re-read by group_id from the existing Table4 using the script. If a small parametric approximation is needed, the measured additive rule followed by q_pred above preserves the observed depth dependence far better than a fixed log-redshift dipole. Treat a as the fitted catalogue operation, not as an independent measurement of beta_O|F or beta_O|R.

The photometric/distance transformation p remains unresolved. This source check does not promote the current g=(A−1)/c source coefficient to a complete physically verified observer-response contract for heterogeneous CF4 DMzp.

## Reproduction and artifact identity

Small standalone script:r63_cf4_q_check.py. It reads only existing selected NPZ and raw Table4, verifies the pinned NPZ SHA and raw parity, performs the deterministic fits, and writes JSON to stdout. Its source was passed through stdin to python3 on the authorized device; the remote script was not saved. RDC process1877406 finished successfully. JSON summary:r63_cf4_q_check.json.

Parent can run, from a location where the small script has been installed by the sole writer:
  python3 r63_cf4_q_check.py --root /home/cosmosapjw/Dropbox/bianchi/htt_base
No output argument is provided; saving stdout remains the caller's action.

Frozen source identities:
- selected NPZ SHA25686dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c.
- table4.dat.gz SHA256be91d4fae6fa01552ab3bc85db695411fca3249eeae08b566a712e6ea790bd99.
- decompressed Table4 SHA256b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94.

## Relevant primary novelty context (reused; no new broad search)

Nusser & Tully, arXiv:2608.14265v1(2026-08-14), https://arxiv.org/html/2608.14265v1 , SecIII and AppA.2:
  D_L,z=(1+zHEL)D_C(zCMB) [EqA5].
It explicitly retains different redshift roles, and its EqA6 conversion distinguishes comoving-coordinate u from physical v=u/(1+z). Thus using catalogue-specific frame/redshift definitions and source-matched logarithmic-distance responses is existing primary work. The R63 check above adds a bounded empirical source-contract fact about the existing grouped release: its published V3k−Vh field is approximately additive, whereas a constant logarithmic correction misses depth dependence. It neither claims priority for frame separation nor imports that paper's inference/likelihood into this experiment.
