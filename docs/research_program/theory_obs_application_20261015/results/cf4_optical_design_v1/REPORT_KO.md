# Cosmicflows-4 실제 관측방향/깊이와 HTT 광학 역산의 정보 구조

관측자료: 원본 38,053 groups; 조건을 만족하는 35970 groups.

**결과 등급:** SOURCE-BOUND geometric design only. 물리적 optical inverse 또는 geodesicity 검정이 아님.

| subset | N | principal sine (equal) | principal sine (eDM weight) | method dipole overlap (eDM weight) |
|---|---:|---:|---:|---:|
| all_z001_010 | 35970 | 0.39539 | 0.413385 | 0.282976 |
| dAproxy_20_200_Mpc | 18074 | 0.328391 | 0.317446 | 0.119193 |
| central_2pct_depth | 720 | 0.0102508 | 0.00827748 | 0.348714 |
| lower_depth_half | 17985 | 0.327917 | 0.316491 | 0.1186 |
| upper_depth_half | 17985 | 0.175952 | 0.168322 | 0.543501 |
| FP_only | 26916 | 0.329899 | 0.337637 | 0.464705 |
| TF_only | 7614 | 0.387951 | 0.394059 | 0.017954 |
| SN_only | 700 | 0.432001 | 0.413755 | 0.0367549 |

지금의 rank13은 실제 Einstein congruence 제약·확률법칙을 역산한 것이 아니다.
기하학적 rank가 존재해도 depth가 거의 상수이면 절편과 기울기 공간이 근접해 수치 식별성이 취약하다.
자유로운 방법별 영점 nuisance의 열공간에는 전역 상수 절편이 포함되어 rank가 12로 감소한다.
거리계수 오차는 redshift의 Gaussian 오차가 아니므로 가중 분석을 Fisher 측정으로 부르지 않는다.
이후 실제 redshift-dA joint latent/selection/calibration law를 CF4 provider와 결합해야 한다.
