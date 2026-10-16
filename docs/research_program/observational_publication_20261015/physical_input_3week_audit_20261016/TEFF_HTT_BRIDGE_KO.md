# TEFF I/II (사용자 첨부)와 HTT 관측 물리 입력의 관계

## 출처와 접근 범위

- 첨부 `TEFF_PAPER_I_arXiv(7).zip`: SHA256 `03e07321f702a533ac88f12d32739fe305c45924eae78cda3fec8975b9daa03d` CRC PASS. 원문 TeX·부록·reference 확인. 저작물 원본과 공개할 뜻이 확인되지 않은 내부 material은 public GitHub로 재게재하지 않음.
- 첨부 `TEFF_PAPER_II_arXiv(7).zip`: SHA256 `639fb8fc15e3889dedebc3b1c128879ca8670c267478c78643fd4954b947e2c4` CRC PASS.
- 이론적 주장 재활용 상태 `draft_source_derived`, 아직 해당 TEFF 원고의 독립 동료심사/학술 게재 검증을 의미하지 않음.

## Paper I → 물리 관측 정보 예산

고정된 관측자 event의 momentum energy radial variable와 angular resolution을 구별한다. Strict convex entropy + 지정한 admissible lift가 있으면 radial conditional information과 angular coarse-grained information의 Bregman chain rule을 쓸 수 있다. 이 해석은 `x_C,Q,F,Π,G_F`와 별도의 kinetic information object이며 둘 사이의 자료 기반 map은 부재. CMB map T/E/B, CF4 redshift, source frame/velocity, 관측 detector response를 무비판적으로 등치시키지 않는다.

관측 `p(y|forward(theta),selection,noise)`가 특정 kinetic radial functional을 식별하는지 검사하려면 해당 source operator의 row space에 response kernel이 속하는지, 아니면 null kernel로부터 서로 다른 kinetic states가 같은 measured moments를 만드는지 판별해야 한다.

## Paper II → number/energy refinement의 비충분성

허용된 number and energy score span `{1,E}` 또는 thermal moment constraints에 대해 target `K(E)=E²`, high-power response, polarization/Fisher/line-of-sight weighting이 들어간다면 원칙적으로 별도 spectral score/probe/shape assumption이 필요할 수 있다. `E²`가 finite Fisher Hilbert-space에서 span 밖이라면 projection residual은 양이고, 그 residual은 단순히 angular projection basis 수를 늘린다고 제거되지 않는다. 단, 실물리 instrument+source forward kernel이 다르면 다시 계산해야 하며 중력·우주론적 광학 Jacobi response는 TEFF의 정보 예산과 별개다.

## 새 제조 반례와 정확한 범위

`T/T* = (.7,1,1.4,2)` discrete Maxwell–Boltzmann mixtures `f(E)=Σ_j w_j exp[-E/(k_B T_j)]`를 취한다. 두 확률 vector는 `Σw=1`, `Σ w T³`, `Σ w T⁴`가 같고 `Σ w T⁵`, `Σw T⁶`는 다르다. 양의 스펙트럼 `f0,f1`에 대해 어느 하나의 공통 predictor g라도 상대 loss max(|g/f0-1|,|g/f1-1|)는 적어도 `|f1-f0|/(f1+f0)`이고 등호를 달성하는 `g=2 f0 f1/(f0+f1)`가 있다. E/(k_B T*)=40에서 98.91%, 60에서 99.985%다. 이것은 **정해진 제한 moments만 입력으로 주어진 두 후보 비교**에서 높은 E의 비식별에 대한 엄밀한 조건부 반례이지 TEFF 원고의 보편적인 high-E tail 상대오차 하한이나 관측우주론의 검출 결과가 아니다.

에너지가 무한대로 증가하며 dominant exponential tail slopes가 다르면 위 상대 minimax loss는 1에 접근할 수 있다. 반대로 추가 spectral samples, tail envelope, compact support, source kinetic closure, 또는 loss = absolute / instrument-weighted L2가 타겟이면 다른 bound 및 새로운 수용조건을 유도해야 한다.

추가 weighted Fisher manufactured 계산(일례 weight `E² e^{-E}` on [.2,10])은 K(E)=E²을 `{1,E}`에 사영했을 때 양의 residual, `{1,E,E²}`에 사영했을 때 1e-14 수준 오차를 확인했다. 이것 역시 photon spectrum의 검출기/교정 law가 아니다.

## HTT 적용 제안

- P1/S04: kinetic entropy budget 또는 local energy moments만으로 signed spacetime Gauss defect를 posterior로 승격하지 않는다. 대신 무엇이 관측됐고 어느 target kernel이 span 밖인지 certificate.
- P2/L03: angular harmonic leakage 수치만 줄여 Planck high-E frequency/foreground spectral error가 함께 해결됐다고 주장하지 않는다. Frequency-dependent transfer, beam, bandpass, thermodynamic K_CMB calibration, noise/foreground null과 spectral response/uncertainty block을 보유한다.
- P4/V03: bolometric dipole만으로 boost/global material tilt의 독립 history를 식별하지 않는다. time/frequency-dependent response를 source-matched rank test.
- P5/B02: AniCLASS near-FLRW polarization hierarchies에서 frequency-independent Thomson 한계를 넘는 spectral distortions를 가정한다면 새로운 collision/source terms와 소스 검증이 필요하다.
- P6/K04: moment-space null vector와 spacetime optical Jacobi null vector는 연산자 자체가 다르다. 합성 forward의 singular values/geometry units/source independence가 먼저다.

Acceptance: exact observable/source spectral response + inferred target kernel + declared norm & accuracy + heldout injection and tail bound. Until then status `TEFF_INFORMATION_AUDIT_ONLY`.
