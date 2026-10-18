# CF4 raw-group directional Hubble residual → STF2: observed-source conditional distribution

자료: CF4 표3,4의 원본 Vcmb·DMzp·eDMzp·RA/Dec, 35970개 z∈[.01,.1] 그룹.
독립적인 거리모듈러스 분포를 가진 것으로 **가정**한 forward 모델을 바탕으로
directional quadrupolar Hubble modulus residual의 5개 계수 분포를 계산한다.

| model | n | nominal ||S/H|| | sigma/Theta proxy | normalized chi2 |
|---|---:|---:|---:|---:|
| fiducial_slope_f015_v250_z01_10 | 35970 | 0.033276 | 0.011092 | 0.7659 |
| no_method_depth_slope_f015_v250 | 35970 | 0.033511 | 0.01117 | 0.768 |
| floor030_slope_v250 | 35970 | 0.033041 | 0.011014 | 0.5932 |
| velocity500_floor015 | 35970 | 0.032733 | 0.010911 | 0.7298 |
| low_depth_001_005 | 16414 | 0.033848 | 0.011283 | 0.7564 |
| high_depth_005_010 | 19556 | 0.033198 | 0.011066 | 0.7732 |
| FP_only | 26916 | 0.046093 | 0.015364 | 0.7511 |
| TF_only | 7614 | 0.048816 | 0.016272 | 0.8258 |
| SN_only | 700 | 0.031049 | 0.01035 | 0.5853 |

Units are dimensionless; the data source uses cosmological CMB-rest Vcmb, not uncorrected source z.
No physical Bianchi kinematic measurement, full-C likelihood, true selection normalizer, optical Jacobi remainder or external cosmological validation is implied.
The large method/depth sensitivity is part of the scientific result, not an uncertainty estimate from independent universes.
LOO HEALPix patches attempted: 12
