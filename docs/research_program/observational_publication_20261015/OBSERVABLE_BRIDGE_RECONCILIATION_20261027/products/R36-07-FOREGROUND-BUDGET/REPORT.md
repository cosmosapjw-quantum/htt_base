# R36-07 actual complex foreground response — conditional result

The seven released PR3 polarization maps supply actual S7 E2/E3/B2/B3
coefficients, and their native QQ/QU/UU columns supply per-pixel marginal
noise blocks. The R31/R32 nine-column operator has row rank seven. On the
actual 7×24 coefficient matrix, the corrected A_BT_1e-07 geometry gives
ell=3.11838142725, J0=1.2888528759e-08 K_CMB², and the **algebraic
minimum** rho=113.527656 microK_CMB. This minimum
is not a measured upper bound on physical foreground contamination.

The actual-data compensators in RESULT.json shift a B-centered CMB-equivalent
24-vector by 1, 10, and 100 microK_CMB while reproducing the seven observed
coefficient vectors to about 1.4e-16 K_CMB Frobenius error. This proves an
obstruction within the retained free signed-moment coefficient class. It does
not prove that each compensator is a positive-emissivity line-of-sight sky.
The conditional response curve and all six bandpass-convention rows are in
ACTUAL_TABLE.csv and BRANCH_SENSITIVITY.csv; the plot is
`/mnt/extdrive/workdir/htt_open_data/r36_foreground_budget_actual/conditional_geometry.png`. The saved derived-SMICA B residual is
0.379234212 microK_CMB after a different E-only
anchor fit. Its same-sky derivation and different statistic forbid treating it
as an independent frequency or direct radius threshold.

For each prespecified real spin direction v, the released marginal covariance
blocks imply the sharp worst-case scalar standard deviation
`sum_(band,pixel) sqrt(l_bp(v)^T Sigma_bp l_bp(v))` over all positive
semidefinite cross-pixel and cross-channel completions. The native-pixel
operator includes the actual mask, Q/U, spin-2 harmonics and QU covariance.
The center's 24-coordinate simultaneous covariance-only Euclidean radii are
0.01: 549143, 0.05: 245584, 0.1: 173654
microK_CMB for the listed alpha_N values. They use only a
mean-zero marginal model and Markov; unspecified calibration, leakage and
bias remain outside this noise bound. A direction chosen after seeing Y
requires the simultaneous bound, not a scalar Chebyshev interval.

An optically thin positive-intensity physical model could bound complex
polarization variation via |dnu|<=dmu_I. It must include all relevant
emitters and a supported spectral/sky domain. Two opposite polarization
phases can give M0=0, total variation 2, and nonzero spectral moments.
For declared domain radius d and variation A_TV, the explicit third-order
remainder is `||K r3|| <= A_TV d^3/6 sup_D ||K D^3 s||_op` in the stated
dimensionless beta_s, beta_d, t coordinates. Neither d nor A_TV has a
source-supported upper value here, so no numerical remainder was invented.

The [FIRAS Pass4 LOWF release](https://lambda.gsfc.nasa.gov/product/cobe/firas_dss_get.html)
was consumed with its [C vector](https://lambda.gsfc.nasa.gov/product/cobe/firas_cvect_get.html),
[frequency covariance](https://lambda.gsfc.nasa.gov/product/cobe/firas_cm_get.html),
and [model-error product](https://lambda.gsfc.nasa.gov/product/cobe/firas_moderr_get.html).
It has 6067 rows and 43 valid
frequency bins; the remaining 139 stored
zero columns are padding. The valid measured table contains
621 negative entries, which cannot be
zero-filled or read as negative physical source intensity. The original S7
has 31
pixel centres more than 3.5 degrees from the nearest FIRAS row centre,
maximum 4.49334 degrees.
This is a centre-distance diagnostic; the scan-elongated beam lower response
has not been certified, so it is not a physical uncovered-sky finding.
The separately released C-vector squared and covariance diagonal differ by
up to 3.81584e-05 relative; the exact source-format
relationship is unresolved and no equality tolerance admits it as a bound.

The finite physical radius remains HOLD on three precise inputs: a
source-calibrated absolute intensity upper set or positive response dual
covering every target atom; independently justified line-of-sight parameter
support and neglected-component bounds; and native component-dependent
response domination or a qualified common-response bridge. The R31 free
class and original 42-node acceptances retain their prior status. This
diagnostic has owner obsstat, tier C0, transfer source none, Galactic COSMO
Q+iU convention, signature (-,+,+,+), and c=299792458 m/s.
