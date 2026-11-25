# R118-C2B: REC 비분리형 각도-주파수 native bridge

판정: IMPLEMENTATION_VERIFIED_SCOPED. 별도의 positivity 판정: COUNTEREXAMPLE_VERIFIED_FOR_FINITE_BAND. 물리 DAG promotion 없음.

- BASS 197f9c867d3fe555cfa5c2dc32f88e6f10ccd540, tree cd40fc855b7050ed1a47242a7f92e8f5897cb6f5. REC f67be237187372f4d89fe8c021819a38261b14eb.
- 원본 v050 35-state scalar COM-KHW pair moments/same-cell rate, 독립 real harmonics, Bose activity action 및 analytic JVP, normal/material-clock Newton-GMRES BE.
- 28 nonzero-time scoped cases: source/fixture 13, BASS collisionless characteristic 15 (FLRW+12 Bianchi families, two refinements). 4 dt=0 action counterexamples. 262 Rust + 3 example tests. 원본 action/JVP 상대차이 최대 4.833e-14/4.377e-15. 독립 BE 잔차 9.177e-14, number defect 5.173e-16. Direct force/Lorentz boost 비교 최대 8.774e-15. Atom force는 음의 photon force ledger이며 독립 event 적분은 아니다.
- PR04C z1300/1100/900 원본의 fixed red/blue packets와 BE updated occupations 재현, 최대 차이 1.672e-13. 실제 face energy 보존, centroid 차이는 unresolved correction, atom interface heat=0. 외부 동적 trajectory는 미구현.
- BASS는 실제 accepted collisionless histories에서 invariant Planck occupation을 source-owned frequency cells에 적분한 후 frozen normal-clock BE를 한 번 수행했다. 독립 GL32 occupation 차이 최대 4.803e-15. 기존 bolometric characteristic temperature 차이 6.662e-16. cell centroid energy closure defect 최대 5.033e-8. prescribed tilt, frozen source calibration (3000 K, n_HI=250 cm^-3), mixed spectra 및 active atomic feedback 미연결.
- L24 I07<-I10, mu=1에서 실제 finite-band conductance 음수. 양의 angular-localized 입력 4개에서 target occupation floor를 1e-8에서 1e-20까지 낮추어 C_target -> -2.14345e-8 s^-1 확인. 이는 finite-band operator의 unrestricted quasi-positivity 반례이지 정확한 물리적 event kernel의 no-go가 아니다. clipping 없음.
- 원본 source hash, binary/input/output hashes, 초기 trial/compile failures, test logs 및 재현 스크립트는 BASS research/r118c2b_rec_angular_bridge/에 보존. Native delegation 미제공으로 serial 실행. 과거 TSV byte parity는 재실행하지 않음. REC/REI 및 R78 그대로.

다음 ID: R118-C2C-POSITIVE-SOURCE-EVENT-MEASURE-AND-BOUNDARY-COUPLING-01. 양의 source event measure와 reversible conductance의 moment mismatch 검증을 우선하고, live exterior/bidirectional coupling 및 mixed-spectrum interface를 검증한 뒤 열·운동량·population feedback에 연결한다.
