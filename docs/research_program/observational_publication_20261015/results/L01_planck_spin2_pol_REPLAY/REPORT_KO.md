# P2 L01: Planck PR3 실제 편광 처리 8개와 physical spin2 응답

한 실제 Planck 하늘 8개 처리 결과의 l2..5 E/B 모드를 source-hashed NPZ에서 사용. 물리적인 spin2 HEALPix Q/U 연산자로 원본 NSIDE2048 PMASK 세 개를 교집합, RING NSIDE64 선택 30021개를 원본과 재현. Temperature TMASK 26846개의 재사용을 명시적으로 거부.

Finite ell6..8의 저차 ell2..5 masked alias spectral norm: E<-E=1.11057; B<-E=0.934495; E<-B=0.934495; B<-B=1.11057. 원본 observed ell>5 E/B amplitudes는 지금 추출하지 않았으므로, 이 값은 실제 우주의 B-mode 누출량 상한이 아니고 finite mask transfer 연산자이다.

Planck 2018 VII 논문은 B polarization이 모든 scale에서 noise dominated임을 명시한다. 따라서 이 결과는 새로운 B 검출, cosmic parity violation, 물리적 Bianchi posterior, anomaly p를 제공하지 않는다. 완전한 beam/foreground/actual high-ell E/B map과 end-to-end null matched simulation은 아직 source qualification이 필요하다.
