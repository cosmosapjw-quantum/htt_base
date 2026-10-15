# Planck 실제 SMICA_FULL raw 2 GB Q/U 편광: spin2 ellmax5→8

원본 NSIDE2048 NESTED Stokes Q/U를 직접 읽되 수정하지 않고, 실제 Planck 공통 PMASK/halfmission/oddeven의 selected 30021 low pix에서만 nested chunk reduction 후 RING spin2 fit을 수행했다.

동일 ellmax5 source cached 저차 계수를 직접 재현한 max difference=0 microK.
ellmax5→8 진짜 raw same-sky E/B l2..5 finite coefficient 이동 norm=0.306411 microK, ell2 BB C ratio=1.18079.

This is a refit sensitivity under a fixed selection, NOT a physically unbiased full-sky E/B, primordial B detection, anomaly p, or Bianchi likelihood. Source beam, high-ell beyond 8, polarized systematics and physical null missing.
