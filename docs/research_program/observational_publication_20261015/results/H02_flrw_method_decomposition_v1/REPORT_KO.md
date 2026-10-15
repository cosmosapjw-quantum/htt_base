# P3 H02: 실제 CF4 source의 FLRW 거리곡선 분리 + 방법 구성 분해

입력은 원래 선택된 35,970 CF4 grouped source, z_CMB, DMzp, e_DMzp, 4가지 방법 FP/OTHER/SN/TF다. 같은 H01 네 겹치지 않는 적색편이 bin과 동일 대각 working covariance 및 sigma_v=250 km/s만 사용한다.

Observed apparent H_eff=[74.08727281722821, 73.68044194436881, 71.31155782744051, 68.88624490075603] km/s/Mpc; flat LCDM H0=74.6, Ωm=0.3153 baseline=[73.44320231835002, 72.45937507301674, 71.22963509023018, 70.17123987912899]; source mean residual ln(cz/Dobs)−ln(cz/dLref)=[0.008731410783342435, 0.016711329099347746, 0.0011494606513893202, -0.01848201926160422].

원시 apparent H_eff의 적색편이 의존성 상당 부분은 FLRW luminosity distance 자체의 정상적인 광학적 redshift dependence를 포함하므로 관측 H_eff를 물리 H(z), shear 또는 global tilt로 읽으면 안 된다.

Far-near raw two-term={'total': -0.07278724120414934, 'composition': 0.008467047160573074, 'within_method': -0.08125428836472214, 'closure_residual': 2.7755575615628914e-16}; FLRW baseline={'total': -0.04557381115920269, 'composition': -0.0021548031902601777, 'within_method': -0.04341900796894245, 'closure_residual': 6.245004513516506e-17}; source residual={'total': -0.027213430044946658, 'composition': 0.010621850350833024, 'within_method': -0.03783528039577968, 'closure_residual': 3.469446951953614e-18}.

Symmetric method-mix decomposition에서 composition term은 실제 near/far downward residual을 반대로 상쇄하고, within-method term은 음수로 남는다. 이는 model-free causal attribution이 아니라 source weight를 고정한 정확한 대수적 회계이다.

Common method min-share π=[0.7195949415789461, 0.004382562481477358, 0.26382839707238626, 0.012194098867190339]; standardized source residual far-near=-0.0431454347. 원거리 OTHER 및 TF의 소수 객체는 extrapolation/coverage 문제이며, method-standardized result도 true cosmological H(z)나 selection-bias correction으로 승격하지 않는다.

물리적 보고서 진행에 필요한 입력: redshift-dependent method selection, group/zero-point shared covariance, peculiar-velocity field and observer/source frame redshift model, independent tracer validation. 정규 FLRW의 비등방성 없는 예측도 후보 모델에 반드시 포함한다.
