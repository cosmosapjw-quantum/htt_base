# R36-03-PM-HISTORY conditional design table

Owner: obsstat response / htt conditional information. Claim tier: C0. Transfer source: none.
Source: retained 755850-row A22 full_stats 102x102 Gram; reported marginal 2x2 errors and stipulated cross-source independence.
Radii are design variables in full-five Frobenius microarcsec/year. Values are fixed-design Gaussian working power, not measured physical limits.

| Profile | Rank | Eigenvalues (microarcsec/year)^-2 | rho80 best | rho80 worst |
|---|---:|---|---:|---:|
| common spin/glide6 | 5 | 2.43693, 2.65563, 3.17145, 3.67145, 4.95102 | 1.60963 | 2.29431 |
| all97 sensitivity | 5 | 0.503015, 0.629927, 1.13946, 1.46083, 2.38294 | 2.32015 | 5.0499 |

| rho (microarcsec/year) | Sphere RMS | Best noncentrality | Worst noncentrality | Best power | Worst power |
|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 0.05 | 0.05 |
| 0.01 | 0.00447214 | 0.000495102 | 0.000243693 | 0.0500212 | 0.0500104 |
| 0.1 | 0.0447214 | 0.0495102 | 0.0243693 | 0.0521336 | 0.0510464 |
| 1 | 0.447214 | 4.95102 | 2.43693 | 0.359204 | 0.184859 |
| 3 | 1.34164 | 44.5591 | 21.9324 | 0.999918 | 0.969002 |
| 10 | 4.47214 | 495.102 | 243.693 | 1 | 1 |
| 30 | 13.4164 | 4455.91 | 2193.24 | 1 | 1 |
| 100 | 44.7214 | 49510.2 | 24369.3 | 1 | 1 |

For q=s, T_ref=Delta_t: k=0,0.1,1,2,10 gives signed gain -1,-0.9,0,+1,+9 respectively; power multiplier is gain squared. This fixed common-history family is conditional.
