# Planck FFP10 실제 원본 Q/U의 소수 코호트 matched pilot

실제 NSIDE2048 RING FFP10 SMICA CMB-only 12개 + noise-only 12개 실현을 고유 ID로 읽어 실제 Planck observed PMASK selected 30021 NSIDE64 픽셀의 물리적 spin2 Q/U 응답으로 투영했다. 선택한 independent source-cohort paired ID 수=12.

실제 관측 한 하늘의 8 processing product를 simulation realization이라고 세지 않았다. 원본 파일의 POLCCONV와 COORDSYS는 지정되지 않았으며 U+ chart 가정만 사용했다. 여기서 scalar E/B power 값은 finite source/mask estimator의 output이고 실제 Planck physical conditional null probability가 아니다.

실제 source observed EE2/BB2/EE3/BB3=[0.08811223492230193, 0.09567655257669655, 0.02689919771629623, 0.008281591842100543]; noise median=[0.021884756016932634, 0.019789532898218047, 0.012612947241137998, 0.008178140969168197]; matched median=[0.04415218437659302, 0.01898293157346286, 0.04348631120578931, 0.008007026405200297].

Source CMB+noise harmonic power identity residual=2.494e-17 microK². Noise covariance rank=11 of 64D, not enough for a full 64D inverse and no significance rank claim. Physical E/B cov/Planck frame, component-separation noise and source selection simulation adequacy still require validation.
