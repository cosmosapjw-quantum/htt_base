# R24 full tensor scenario adapter

This adapter consumes the reviewed K03 reported-redshift fixed-design Gaussian
working result. Its original 24-coordinate mean and full covariance remain in
`RESULT.json`; the seeded 4096 by 8 by 3 sample-by-functional tensor is in
`SAMPLES.npz`. The eight rank-one vectors are the E1 polar and B1 axial xyz
blocks for three reported-redshift bins and the fitted slope. No physical
source response is inferred from these coordinates.

One common region family, `K03-full24-common-C-rho-reported-z-scenario`, uses
the full24 Gaussian covariance and radii 0, 1, 2, 4, and 8. `F` carries exact
finite plus/minus coordinate directional supports, sample pushforward under a
declared Gaussian replicate law, and reference occupancies. The Gaussian
occupancies are chi-square(24) calculations for this centered computational
region. They have no calibrated selected-survey coverage interpretation.

`Q_ref` uses a computational direct-sum ball of radius 10 microarcsec/year.
The matching physical MES anchor is unavailable. `Pi` is a strict-exceedance
frequency under the declared Gaussian replicate law for that reference score;
the physical probability remains `[0,1]` with unknown mass 1. Ties do not
exceed. Signed values, zero values, undefined denominators, unavailable
physical anchors, and unavailable cross covariance are kept distinct from zero.

`G_F` retains the 18-coordinate reported-z path and full transformed covariance
for `(Y0, Y1-Y0, Y2-Y1)`. This depth transformation is invertible. The map
from full24 to Y18 has rank 18 and a six-dimensional nullspace, so the full24
carrier stays alongside both depth representations. The figures illustrate
conditional estimates and reference occupancy; they are diagnostic only.

The numerical tests cover reconstruction, covariance and Gaussian quadratic /
Fisher invariance to relative tolerance 1e-10; map rank and null witnesses;
loss of the common mode on dropping Y0; missing cross covariance; denominator
states; strict ties and explicit law; and SO(3) / polar-axial parity. The first
test run exposed a parity broadcasting error and is recorded in
`TEST_INITIAL_FAILURE.txt`. The corrected run passed 5 tests. Review and
scientific admission are separate from this author result.
