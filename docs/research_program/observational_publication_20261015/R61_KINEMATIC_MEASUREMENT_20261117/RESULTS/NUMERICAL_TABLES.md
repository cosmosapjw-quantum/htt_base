# R61 generated numerical tables

Generated from the four result JSON files named in NUMERICAL_SUMMARY.json. No refitting.
Ranges are conditional on the declared law, response and calibration family.

## Joint11 model union, covariance lambda=1

| Quantity | 0 mmag lower | 0 mmag upper | 5 mmag lower | 5 mmag upper |
|---|---:|---:|---:|---:|
| Sigma | 0 | 0.0625487635 | 0 | 0.0651231319 |
| acceleration_over_cH | 0 | 0.101538181 | 0 | 0.105526375 |
| relative_speed_over_c | 0 | 0.00420553056 | 0 | 0.00420553056 |
| directional_expansion_rms | 0 | 0.0604945034 | 0 | 0.0627970885 |
| beta_dot_a | -3.85992271e-05 | 0.000357356835 | -5.36401683e-05 | 0.000374129308 |
| beta^T s beta | -6.28151054e-07 | 5.04420598e-07 | -6.71943663e-07 | 5.59449945e-07 |

## Depth response and geometry comparison

| Variant | Slope nominal p5 | Depth RMS upper | Optimal z | z0/pivot RMS error | beta.a box ratio | Mixed exact-box ratio, 0 mmag |
|---|---:|---:|---:|---:|---:|---:|
| log | 0.94328692 | 0.057771385 | 0.055759111 | 3.0055675 | 3.6423487 | 4.9872019 |
| log_mono | 0.77816551 | 0.062565428 | 0.05554048 | 2.994154 | 4.5874309 | 5.0814847 |
| log_split | 0.86837339 | 0.064478613 | 0.054812752 | 2.9470074 | 4.3563627 | 5.8140773 |
| log_survey | 0.84967953 | 0.063162396 | 0.055166486 | 2.9590178 | 4.6664447 | 5.5266803 |
| log_mono_radial | 0.80388657 | 0.06332466 | 0.055227036 | 2.9528572 | 4.8129044 | 5.3447422 |
| log_mono_galactic | 0.56331909 | 0.163404 | 0.056384171 | 2.6902704 | 4.6153684 | 5.72386 |
| log_mono_error | 0.79860225 | 0.06348745 | 0.055538133 | 2.9923084 | 4.7976085 | 5.1447353 |

The box comparisons replace the whole joint ellipsoid by its coordinate-support box; they do not isolate covariance off-diagonals or compare with a different independent-data law.
The mixed legacy triangle-bound ratio is deliberately excluded from the geometry-comparison column.
