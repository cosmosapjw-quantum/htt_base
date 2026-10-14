# SYNTHETIC Gaussian joint-null diagnostic; NOT Planck science

Fixed B=999; declaration `synthetic-fixed-v1-seed-20261014-B-999`.

| Feature | Tail | Signed value | p rank | Joint-max adjusted p | q interval (unadjusted) |
|---|---|---:|---:|---:|---|
| synthetic_feature_0 | upper | -0.79474 | 0.819 | 1 | [0.793506, 0.842236] |
| synthetic_feature_1 | two-sided | -0.10828 | 0.898 | 0.977 | [0.877434, 0.91598] |
| synthetic_feature_2 | lower | -0.884317 | 0.165 | 0.574 | [0.14171, 0.188617] |
| synthetic_feature_3 | upper | -0.832928 | 0.819 | 1 | [0.793506, 0.842236] |

Global joint-null p_rank=0.574 (573 >= exceedances, 0 ties).
Global q interval=[0.5422260367232565, 0.6044862749379087] at confidence 0.95.

Conservative finite Monte Carlo p under declared exchangeability conditional on independent training; ties use >=.
Marginal Clopper-Pearson interval for IID null exceedance probability q conditional on fixed observed threshold and training. Not an interval for realized p_rank; not simultaneous across features.
Global max-score test and single-step adjusted ranks control error under the complete joint null. Strong FWER under partial alternatives needs extra conditions, not asserted.
Observed feature calibration; no inferred shear, global tilt, Bianchi family detection, posterior or evidence.

Provenance attestations are validated mechanically and have not been independently verified.
