# Legacy Teff F4: observational Planck ell2+ell3 power와 morphology 분해

실제 legacy TeffMomentMap의 F4를 정규직교 real Y_lm l2+l3에 정확히 연결. 이 소스는 하나의 관측 CMB 하늘 9 processing 결과와 원본 FFP10 999 CMB/300 noise에 대해 통일된 온도 공통 mask(26,846)를 사용한다.

Analytic variance identity: v=sum_m |a_lm|²/(4πT0²). Higher-order shape residual e=4<t³>+<t⁴>. 실제 9 결과 e 최대절대값=1.7434e-16, power 대비 보수적 비=6.88635e-07; SMICA_FULL s3=-0.101572088, k4=3.15955215.

Shape normalized statistic은 단순 C2/C3 재표현보다 형태 정보를 남길 수 있으나, 원본 계수의 함수이므로 독립 likelihood로 다시 곱할 수 없다. mask/beam/high-ell, observer dipole, FFP10 end-to-end null이 검증되기 전에는 형태 anomaly p나 physical shear/tilt 제약으로 승격하지 않는다.
