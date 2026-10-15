# Legacy Teff exact O(3) source moment: quadrupole→octupole 확장

기존 TeffMomentMap의 ell<=2 dipole/quadrupole finite ansatz를, 실제 Planck 사중극 5개+팔중극 7개 real harmonic source field의 exact spherical fourth moment로 확장하였다. 적분은 16 Gauss–Legendre×32 azimuth nodes를 사용하고 24×48로 차수 독립 검산했다.

같은 실제 하늘 9 processing products의 deltaF4(ell2+l3) 범위=[2.5316823133488804e-10, 2.5714313513385205e-10]; quadrupole-only 이전 결과 재현 residual=1.16e-25; quadrature convergence max residual=4.14e-25.

source FFP10 CMB-only 999, noise-only 300, 첫300 같은 ID pairing 조건부 배열을 실제 Planck 공통 temperature mask 26846개의 operator로 처리했다. 이것은 l>=4, 실제 intrinsic dipole, beam, foreground/cosmic physics가 빠진 정확한 유한차원 통계량이지 실제 복사장 전체의 F4 측정이나 새 확률적 likelihood가 아니다. Legacy filling F와도 구별한다.
