# CF4 source-specific STF2 directional morphology consistency

The actual 5-component tensor orientations matter, not only the norm.
| comparison | STF2 normalized cosine | formal diagonal-only Mahalanobis |
|---|---:|---:|
| FP_only vs TF_only | 0.052629 | 6.9609 |
| FP_only vs SN_only | 0.561996 | 3.0663 |
| TF_only vs SN_only | 0.120833 | 3.7823 |
| low_depth_001_005 vs high_depth_005_010 | 0.456979 | 3.6706 |
| fiducial_slope_f015_v250_z01_10 vs FP_only | 0.841401 | 3.5511 |
| fiducial_slope_f015_v250_z01_10 vs TF_only | 0.462412 | 5.5918 |

Gaussian Mahalanobis is NOT a calibrated physical sigma or p-value: missing cosmic velocity covariance, method selection and common calibration.
FP vs TF can have similar tensor norms while their patterns are nearly orthogonal in the five-dimensional STF space.
The local source patterns cannot be interpreted as a single global shear tensor without a physics-qualified transfer.
