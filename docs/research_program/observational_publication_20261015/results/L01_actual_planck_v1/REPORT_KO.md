# Planck 실제 SMICA source의 lmax 민감도

Source K1 gated observed map과 조건부 FFP10 처음 48개 각각을 NSIDE64 동일 26,846 온도 픽셀의 l0..5/8/10/12 finite real harmonics로 적합했다. 모든 모델은 하나의 실제 하늘을 재분석한 결과이며 독립 새 관측이 아니다.

실제 observed source eps2/3 순서(lmax 5,8,10,12): [[1.0704565622300471e-05, 2.1863310035973762e-05], [1.2518270498462333e-05, 3.254655792494607e-05], [1.1298972662524553e-05, 2.9296631557323384e-05], [1.4843735107902735e-05, 2.482225835956647e-05]]. 동일 mask highmode l6..lmax spectral norms: [0.0, 1.4776121929674189, 1.59325274114674, 1.6586530089000686].

이 결과는 고차원 모형에 따른 저다중극 투영 이동이지 beam/foreground deconvolution, polarized T/E/B, 또는 물리 Planck anomaly p가 아니다. ell>12 highmode 영향은 계산하지 않았다. P2 L01 물리 beam/spin2 gate는 별도 미완.
