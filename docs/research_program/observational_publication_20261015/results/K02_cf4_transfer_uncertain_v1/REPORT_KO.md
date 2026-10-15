# P6 K02: 실제 CF4 apparent STF와 물리 광학 response 미식별성

35,970 grouped source, z_CMB/DMzp/eDMzp/J2000 및 4개 method family. 기존 source 14 nuisance 및 .15 mag +250 km/s diagonal working error를 고정하고, 서로 다른 선언적 radial shape g(z)에 대한 5차원 apparent STF를 다시 계산했다. g(z)는 실제 Bianchi/GR light-cone transfer가 아니다.

Baseline g=1 source STF norm=0.0332577424, 기존 exact Schur regression max=0. Four radial-shape direction cosines and conditional eigenvalues in result.json.

두 구성적 비식별성 증명: (1) unknown positive physical transfer gain lambda가 있으면 fitted gamma~1/lambda, covariance~1/lambda²로 재변환되어 실제 physical Sigma amplitude는 유한하게 식별되지 않는다. (2) 방향별 STF calibration을 네 method 각각에 자유롭게 허용하면 global STF template B=sum_m B_m, 실제 source nuisance projection residual=3.366e-16; 따라서 정확히 5개 global 템플릿이 상대 nuisance 공간에 소거된다. 이 calibration 모형은 **가상의 worst-case 시스템atics**이며 CF4가 실제로 이런 오차를 가지고 있다는 증거는 아니다.

K01에서 도출한 한 사건 -dlnE/dt_u = H-A dot skylook+sigma_nn 는 CF4 광도거리 residual mu_i를 직접 계산하는 광선수송함수가 아니며, 그 중간 source-time/geodesic/peculiar covariance를 구현하지 않고 physical sigma, omega, A, beta를 fit한 것으로 판정하지 않는다. Legacy signed x,F,Pi,Q,G_F full posterior도 식별되지 않았다.
