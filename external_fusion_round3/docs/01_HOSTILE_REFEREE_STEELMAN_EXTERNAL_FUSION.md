# External-Fusion Round-3 Hostile Referee Steelman

이 문서는 외부 패키지와 redshift/depth low-ell pole programme에 대해 가능한 가장 강한 반론을 구성한다. 비판의 목적은 scope를 줄이는 것이 아니라 각 주장을 살아남게 할 load-bearing upgrade를 정의하는 것이다.

## H3-01 — Dependency theatre

외부 패키지 수가 늘어도 기존 계산을 wrapper로 재현할 뿐이면 과학적 독창성은 0이다. package count가 evidence count로 오인될 위험이 크다.

## H3-02 — False independence of external codes

CAMB, CLASS, CCL, emulators와 여러 map package가 같은 perturbation equations, cosmological priors와 upstream data를 공유하므로 코드 간 agreement를 독립 검증으로 셀 수 없다.

## H3-03 — Version, license and API drift

빠르게 변하는 JAX·S2·SBI 생태계를 pin하지 않으면 결과와 gradient가 재현되지 않으며, 라이선스 조건을 놓치면 공개 패키지 자체가 불가능하다.

## H3-04 — Fail-open optional dependencies

optional package import 실패 때 toy fallback을 조용히 사용하면 production 결과가 외부 oracle을 거친 것처럼 보이는 false green이 된다.

## H3-05 — Tool-selection multiplicity

수십 개 statistic·simulator·inference engine 중 잘 작동하는 것만 고르면 package selection 자체가 look-elsewhere effect다.

## H3-06 — Toy DGP masquerading as cosmology

dependency-free shell mock은 software test에는 유용하지만 실제 SW/ISW/Doppler, reionization, selection physics를 포함하지 않으므로 cosmological conclusion을 지지할 수 없다.

## H3-07 — Shared FLRW assumption

CAMB·CLASS·nanoCMB는 FLRW perturbation theory를 전제로 하므로 global anisotropic geometry 또는 Bianchi tilt를 검증하는 oracle이 아니다.

## H3-08 — GLASS/lognormal limitations

GLASS의 빠른 shell mock은 저차 통계와 비선형 velocity·rare structure를 충분히 재현하지 않을 수 있어 local-structure dipole와 kSZ small-scale coupling을 과소모델링할 수 있다.

## H3-09 — The phrase redshift-dependent CMB pole is ill-defined

우리는 한 위치에서 하나의 CMB sky만 본다. shell contribution, cumulative line-of-sight pole, remote dipole field, remote quadrupole field를 구분하지 않으면 서로 다른 object를 같은 pole(z)로 부르게 된다.

## H3-10 — Pole definition non-uniqueness

maximum angular-momentum axis, minimum axis, multipole vectors와 area normals는 동일하지 않다. 결과가 pole definition 선택에 따라 바뀔 수 있다.

## H3-11 — Eigenvalue degeneracy instability

low power 또는 nearly degenerate power tensor에서는 작은 noise·mask 변화가 pole을 큰 각도로 회전시킨다. pole direction이 식별되지 않았는데 finite cone을 보고할 수 있다.

## H3-12 — Mask and foreground rotation

Planck mask, inpainting, monopole/dipole removal, foreground complexity와 component separation이 low-ell poles를 회전시킬 수 있다.

## H3-13 — Planck component maps are not independent skies

SMICA, Commander, NILC, SEVEM 일치는 독립 확인이 아니라 같은 sky의 pipeline sensitivity다. 이를 replicate count로 세면 과신한다.

## H3-14 — Boost operator order and convention risk

local Doppler modulation, thermodynamic temperature, aberration direction remapping과 beam/pixel effects를 동일 order와 convention으로 처리하지 않으면 local-boost signature가 잘못된다.

## H3-15 — Phenomenological global tilt strawman

간단한 fixed-axis injection을 global tilt로 부르면 실제 Bianchi/multi-fluid transfer보다 구분하기 쉬운 대안을 만들어 method performance를 부풀린다.

## H3-16 — Arbitrary shell decomposition

SW/early-ISW/late-ISW/Doppler를 redshift shell에 분배하는 방식과 cumulative convention이 pole trajectory를 바꿀 수 있다.

## H3-17 — Shells are correlated and cosmic-variance limited

redshift bins의 remote fields와 cumulative poles는 같은 primordial modes를 공유한다. 독립 bin으로 취급하면 유효 정보량을 과대평가한다.

## H3-18 — kSZ optical-depth bias

remote dipole reconstruction amplitude는 galaxy-electron cross-correlation과 optical-depth bias에 강하게 의존한다. pole와 amplitude를 cosmological velocity로 직접 읽을 수 없다.

## H3-19 — pSZ is currently low signal-to-noise

현재 Planck/ACT/unWISE/CIB remote-quadrupole constraints는 O(1) S/N 수준이므로, 강한 global-tilt 판정을 낼 정보가 없다.

## H3-20 — kSZ/pSZ foreground and mean-field bias

tSZ, CIB, Galactic foreground, mask mean field와 estimator monopole가 remote-field pole을 만들 수 있다.

## H3-21 — Published remote-field products may be unavailable

논문 결과만 있고 full reconstruction maps/code가 공개되지 않으면 exact data comparison은 재현 불가능할 수 있다.

## H3-22 — Source superposition defeats single-label classification

local boost, local structure, calibration and global mode가 동시에 존재할 수 있는데 single-class classifier는 가장 가까운 잘못된 source를 강제한다.

## H3-23 — Model-list misspecification

source library에 실제 mechanism이 없으면 evidence와 neural classifier 모두 confidence를 내면서 틀릴 수 있다.

## H3-24 — SBI overconfidence

neural SBI는 simulator와 training prior가 null direction을 닫아 좁은 posterior를 만들 수 있으며, identification이 아니라 model restriction을 학습할 수 있다.

## H3-25 — Partial identification can be vacuous

identified interval이 [0,1]에 가깝다면 정직하지만 과학적 leverage가 없다. favourable nuisance bounds를 골라 interval을 줄일 위험이 있다.

## H3-26 — Adaptive scan multiplicity

새 package, statistic, depth bin을 결과를 보며 추가하면 fixed-analysis p-value와 coverage가 무효가 된다.

## H3-27 — Local LSS simulator mismatch

CONCEPT/JaxPM/PySCo의 box size, resolution, force solver와 missing long modes가 bulk-flow/tilt identifiability를 바꾼다.

## H3-28 — Cross-code agreement is not truth

두 N-body code가 같은 initial conditions와 approximations를 사용하면 agreement가 common bias를 숨길 수 있다.

## H3-29 — Storage and provenance creep

100 GB ceiling 안에서도 partial downloads, cached files, generated maps와 summaries가 뒤섞이면 실제 input lineage와 재현성이 무너진다.

## H3-30 — Track-I/Track-II leakage

phenomenological coherent source 또는 FLRW remote field가 native Bianchi transfer인 것처럼 family/geometry claim에 소비될 위험이 있다.

## H3-31 — Native solver adapter mismatch

Bianchi solver가 다른 tetrad, harmonic phase, epoch, polarization convention을 쓰면 adapter가 수치적으로 작동해도 물리적으로 틀릴 수 있다.

## H3-32 — Actual-data anomaly mining

Planck pole, redshift bins, tracer와 source statistics를 사후 선택하면 local/global distinction이 새로운 anomaly catalogue가 된다.

## H3-33 — Unoriented-axis ambiguity

pole은 p와 -p가 같은 축이다. signed dipole, handedness와 unoriented quadrupole axis를 같은 alignment statistic에 넣으면 의미가 사라진다.

## H3-34 — Benchmark novelty may be dismissed

새 benchmark만 제시하고 실제 cosmological design 또는 data conclusion을 못 내면 methodology contribution이 niche software exercise로 평가될 수 있다.
