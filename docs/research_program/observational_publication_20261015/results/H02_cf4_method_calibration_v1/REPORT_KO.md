# H02: 실제 CF4 깊이별 가중치와 calibration 영점 시나리오

35,970개 실제 CF4 grouped source, method order=['FP', 'OTHER', 'SN', 'TF']. 한 하늘의 overlapping windows and original source errors, no new independent samples.

Near/far delta lnH=-0.0727872412; assuming independently free absolute method offsets up to 0.1 mag, support shift=0.07163771, ratio=0.984207. **0.1 mag is a hypothetical stress scale, NOT CF4 empirical method calibration uncertainty**.

Under assumed independent 0.05-mag method zero-point uncertainty, contrast std=0.0220118431; perfectly common 0.05-mag offset cancels between depth windows. One fixed-source injection residual=3.08e-15. Seven overlapping window covariance rank=4 because four shell basis components; do not invert seven-window covariance without source-aware reduction.

Conclusion: distance-trend is strongly confounded by indicator method composition; this computation does NOT claim the trend is caused by calibration or measured physical H(z), and does not calibrate the true CF4 selection/flow covariance. Thus DAG H02 remains BLOCKED_PHYSICAL_EMPIRICAL_LAW with useful scoped evidence.
