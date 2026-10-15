# P2 L01 실제 Planck+FFP10 Schur high-l masked source 분해

실제 K1 registered SMICA 온도 지도 한 개, 동일 NSIDE64 RING mask 26846개, FFP10 CMB 48개, noise 12개, 동일 ID로 paired CMB+noise 12개를 동시 l0..5 / l0..8 / l0..10 / l0..12 real harmonic으로 적합.

각 source에 대해 restricted minus joint l2/3은 full joint l6..12 coeff와 mask block K=GLL^-1GLH의 정확한 곱이다. 별도 profile Schur S=GLL-GLHGHH^-1GHL 구현으로 crosscheck.

Mask source high6..12 to low ell2/3 spectral norm=1.65865301; profile information minimum relative to original low Gram=0.022328226. Legacy F4 l2/l3 shape (s3,k4) 변화는 실제 observer source와 같은 ID FFP signal/noise에 따라 다르며, 곧바로 관측 우주론 anomaly라고 부르지 않는다.

Planck original 2018 IV는 source component filtering과 smoothing을 포함하며 여기서는 5 arcmin Gaussian×NSIDE64 pixel-window를 ONLY NOMINAL SCENARIO로 분리했다. 실제 released effective SMICA transfer/foreground/high ell>12는 미확인이다. CF4 FLRW source와 Planck 자료는 별개 관측으로 보존하고 physical shear/tilt/x/Q/Pi posterior로 묶지 않는다.
