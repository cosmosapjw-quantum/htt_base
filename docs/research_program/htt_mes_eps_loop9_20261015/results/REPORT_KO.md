# 실제 Planck 저다중극과 공변 MES epsilon 연결 진단

PR3 아홉 처리 산출물은 하나의 공통 하늘이며, FFP10 캐시는 **조건부 시뮬레이션 모델**이다. mask·beam·공변 미분 response가 보장되지 않아 실제 물리적 MES 상한은 산출하지 않는다.

- SAG(1997) Eqs 15,17: sqrt(C2)/T0 -> ||tau2|| factor 1.727470747, sqrt(C3)/T0 -> ||tau3|| factor 3.122217203.
- SMICA_FULL observed tensor norm eps2=1.07046558e-05, eps3=2.18607629e-05 (masked projected-source expression).
- Across 9 one-sky products eps2=[1.0504894471853183e-05, 1.0735580690128218e-05], eps3=[2.183186478345521e-05, 2.202663288906679e-05].
- FFP10 999 matched sky mask-vs-full eps RMS=[2.6519927336704803e-06, 3.9062408866097115e-06]; 300 paired-noise RMS=[6.849047651169784e-08, 9.203378396856747e-08].
- Finite source l6..8 -> estimated ell2/3 mask-leak operator spectral norm=1.47761; NOT a global no-leakage bound for ell>8.
- Assumed geodesic eps1=0 algebraic sigma-sector anchor range: [2.510832881485534e-09, 2.593321486240546e-09]. Not observational bound.

**Unresolved:** true sky response/beam/filter; unmeasured CMB intrinsic eps1; Copernican spatial and temporal derivatives; radiation/matter observer motion; actual CMB Bianchi transport and empirical covariance/exchangeability. No new physical detection or physical-null p-value.
