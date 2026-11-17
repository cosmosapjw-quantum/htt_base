# L2 count-dipole covariance and calibration sensitivity

Date: 2026-11-17. Read-only calculation on the existing owned R54 result. No new catalogue, simulation, likelihood product or repository mutation was performed.

## Input identity

- Source: `docs/research_program/observational_publication_20261015/R54_TENSOR_FRAME_TOMOGRAPHY_20261116/RESULTS/R54_L03_RESULT.json`
- SHA-256: `0df35f1d30505cea66a6087d341904fdcb2be07787ec413288b59a3a60fa0125`
- HEAD when read: `6fe19c5139004a1f281ec85c592e5ab4c7590d5f`
- Inputs per catalogue: saved `excess_tests[k].excess_icrs`, `excess_tests[k].covariance`, and `velocity_null[k].cov`.
- Full vectors, all matrices, 101 interpolation points, PSD spectrum, scalar derivatives and independent optimizer checks are retained in `l2_counts_sensitivity.json`.

## Definitions and conditional calculation

Keep the observed count-dipole excess vector e fixed. Set

    S_receipt = C_total - C_mock,
    C(lambda) = C_mock + lambda S_receipt,  0 <= lambda <= 1,
    W(lambda) = e^T C(lambda)^(-1) e.

S_receipt is positive semidefinite in both catalogues. Its eigenvalues are:

- Quaia_G20: [0.000016296155269209363,0.000023502163301656973,0.0002509210990732706]
- NVSS: [0,0,0.0025000000000000005]

For a fixed e, differentiation gives

    dW/dlambda = -(C(lambda)^(-1)e)^T S_receipt (C(lambda)^(-1)e) <= 0.

Thus the nominal Gaussian chi-square upper tail is nondecreasing. This statement does not apply automatically to a refitted CF4 Wald statistic whose estimate changes with covariance.

## Actual results

| Catalogue | Original finite-mock Pi | Nominal Gaussian tail, lambda=0 | Nominal Gaussian tail, lambda=1 | Nominal p=0.05 crossing |
|---|---:|---:|---:|---|
| Quaia_G20 | 0.005988023952095809 | 0.00041702301794998057 | 0.309208812103659 | lambda=0.25368911086800666 |
| NVSS | 0.32934131736526945 | 0.3227920348190415 | 0.42116777851279785 | None; already above 0.05 at lambda=0 |

The original finite-mock values use 500 realizations and remain a distinct Pi object. In particular, Quaia's 0.005988 finite-mock value must not be replaced by the nominal Gaussian value 0.000417. Both depend on the original data-conditioned mock construction.

For Quaia, the nominal crossing needs 25.3689% of the saved systematic covariance increment, equivalent to a standard-deviation multiplier 0.503676 relative to that receipt component. This is a sensitivity coordinate along the specific saved covariance family, not an empirical measurement of systematic contamination. For NVSS, the original Gaussian nominal conclusion remains above 0.05 for the whole interpolation.

At lambda=1, both saved Gaussian p-values are reproduced with absolute error zero in the executed environment. W is nonincreasing at all 101 recorded grid points and its analytic derivative is nonpositive.

## Deterministic calibration threshold

Separately, minimize the Euclidean count-dipole offset norm subject to the nominal mock-only ellipsoid:

    minimize_b ||b||,
    (e-b)^T C_mock^(-1)(e-b) <= chi2_3(0.95).

Let C_mock=U diag(c_j) U^T and f=U^T e. If e is outside the ellipsoid, strict convexity gives

    b = U diag[tau/(c_j+tau)] f,
    sum_j c_j f_j^2/(c_j+tau)^2 = chi2_3(0.95), tau>0.

The scalar equation was solved by Brent's method and independently checked by constrained SLSQP in scaled Cartesian coordinates. The same confidence threshold is 7.814727903251179.

Quaia_G20:

- Minimum norm: 0.0038996227210868497, in dimensionless count-dipole coefficient units.
- Offset vector: [-0.0027987261128552075,-0.00220401684765756,-0.001586347769967486].
- Offset ICRS direction (RA, Dec): [218.22068519836716,-24.003672068444626] degrees.
- Fraction of measured excess-vector norm: 0.32528178453364986.
- Root-versus-SLSQP vector discrepancy: 2.5027059581844538e-11.
- KKT stationarity residual: 1.9873754096201567e-18.

NVSS:

- Minimum norm is exactly zero because zero is already feasible in the nominal ellipsoid.
- Its calibration direction is undefined; the JSON records null, not an arbitrary axis.

This is a conditional calibration sensitivity threshold. No speed is inferred from it: that would require a justified population response and physical interpretation.

## Validity limits

C_mock was estimated from 500 data-conditioned realizations. The interpolated chi-square tails and 95% ellipsoid are therefore nominal fixed-covariance calculations, not exact finite-sample calibration. The stored finite-mock Pi values and Clopper–Pearson intervals are preserved unchanged. The calculation describes the dependence of the owned count-dipole result on the saved statistical/systematic law. It establishes neither a cosmological beta measurement nor a cross-catalogue anomaly probability.
