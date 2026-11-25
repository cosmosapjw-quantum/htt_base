# R118-C2: 원자물리 source-calibrated resonance diffusion

상태: IMPLEMENTATION_VERIFIED_SCOPED. 기존 R118-C1 보존 구조를 전제로 실제 H I Lyα 및 He I 584 Å 원자 상수로 보정한 국소 scalar material-frame FP 패치와 Bose stimulated collision을 구현했다. 전 우주 주파수-각도 운반 또는 활성 원자 population feedback에 연결한 결과는 아니다. p_sc는 명시적 입력이며 실제 destruction branching은 아직 미연결이다.

## 계산
- BASS resonance.rs, resonance_patch.rs, r118c2_resonance.rs 및 research/r118c2_calibrated_resonance/ 참고.
- 양의 Voigt quadrature, RD dipole second-moment correction, equilibrium-preserving edge conductance, 안정적인 양의 tridiagonal BE solve, scalar Bose nonlinear solve, signed frequency shift와 exterior number/energy ledger.
- REC 실제 Hummer source 및 HYREC frozen reference 상태 사용. neutral species를 ground-state abundance로 근사. He I multiplet/upper-state broadening 및 exact angular redistribution은 미포함.
- 88개 실행, 8410 steps, 258 Rust + 3 example tests, 신규 6 tests. 기존 출력 44 TSV byte parity. 원시 결과 및 source hash 검사 완료.
- number/energy 최대 정규화 ledger 잔차 각각 2.7978e-14, 2.7882e-14. 독립 Voigt/dipole profile 상대오차 1.0991e-13, 7.7027e-13. 70-digit stiff oracle 최대 상대 L1 차이 2.7843e-16. scalar Bose root oracle 최대 4.5548e-15. BE 시간 수렴은 1차.
- Hummer center bin [-0.25,0.25]의 conditional second moment 0.3291377922, dipole FP 0.3293217618, uncorrected FP 1.0. binned vs continuous 비교이므로 exact equality는 아니다.
- angular quadrupole의 주파수 조건부 분리 가정 G2=0.1 G0의 L1 결함 0.1203821589. 실제 비분리 REC kernel 연결이 필요하다.
- H z=1100에서 pure-scattering Γ_peak/H ≈1.356e13; He z=2800에서 ≈1.940e10. source snapshot에서 계산한 국소 stiffness이지 재결합률 예측은 아니다.
- prescribed signed drift He stress: extent 40, 128/256/512 intervals의 exterior loss ≈0.07402/0.05695/0.04717. 미수렴이며 physical escape probability가 아니다.
- 진단 zero-mass 0/0 가능성, 독립 finite-difference root 실패, 요약 JSON 변수명 충돌을 각각 수정/보존했다. native subagent dispatch는 호스트 도구 미제공으로 미실행. 독립 수치 oracle과 원전 검색은 실행했다.

## 다음 작업
R118-C2B-REC-NATIVE-ANGULAR-REDISTRIBUTION-BRIDGE-01. REC PR04C split-domain contract, full_scalar_com_khw_v050.npz 및 nonlinear_bose_runtime.py의 원본 의미/정규화를 보존하면서 BASS 각도-주파수 operator bridge를 구현한다. 국소 FP를 분리형 각도 kernel로 승격하지 않는다. 실제 경계 결합 및 atomic/thermal feedback 이전에 number/energy/momentum ledger와 기존 source parity를 검증한다.

REC/REI 및 R78 science DAG는 이번 루프에서 변경하지 않았다. 상세 source hash, solver evidence 및 residual은 ACCEPTANCE.json과 해당 BASS research directory를 사용한다.
