# R5 다음 연구루프 재개 계약

ROLE=CONTINUATION_THEORY_RESEARCH
PROJECT=MES_TENSOR_OPTICAL_COMPARISON
BASE=R5_FINITE_TILT_JOINT_OPERATOR
NO_ODE_PDE_BOLTZMANN_EVOLUTION=TRUE
VIGILODE_DEPENDENCY=NONE
NO_PRODUCTION_MUTATION=TRUE

R5 최종 보고서, KINEMATIC_OPERATOR_DERIVATION.md, INDEPENDENT_REVIEW.md, REGISTRATION_CHRONOLOGY.json, 실제 CAS raw, SOURCE_PROVENANCE.json, state/RESEARCH_STATE.json을 읽어라. R3–R5의 완료된 일반증명/CAS를 새 발견으로 반복하지 않는다. Runtime은 현재 도구 호출로 판별하며 과거 unavailable/성공 상태를 자동 상속하지 않는다. Astra v4.0.0 harness를 사용하되 모델 신원/ultra 설정을 인증하지 않는다.

원래 목표: Θ,σ,ω,A,β의 형태·방향·부호·상관을 유지하여 동일 관측/전제/MES reference 아래 비교하고 T,Q_outer,F_amp,Π_tail,G_tensor를 같은 latent state에서 계산한다. Θ,β에 보편적 MES ceiling을 만들지 않는다. 실제 data/reference 없이 observed percentage를 만들지 않는다.

닫힌 결과:

1. 고정 homogeneous geometry/p에서 k=k_C+A j, j=(symmetric q,b), exact rank9.
2. omega - beta cross (A/c)/2 = S w_C의 exact3 compatibility constraints.
3. Free b의 rank3 image 및 이를 소거하는 joint combinations.
4. Compact nonempty section+linear nuisance subspace의 target boundedness iff target nuisance image=0.
5. R3 retained radiation time-jet block rank8 for |beta|<1. 자유 v1,v2는 8개 residual을 모두 상쇄한다. 물리적 domain/비선형 law의 보편 no-go로 확대하지 않는다.
6. 비가환 finite-tilt correlated disk의 full tensor/reference/statistic sensitivity example. Uniform-disk law는 선언한 계산 예이며 posterior가 아니다.

다음 우선순위는 exact radiation branch로 권한다. 후보 생성과 독립 판정을 분리하고 한 번의 bounded loop만 실행한다.

목표: R3 retained equation의 residual을 교체할 exact dipole/quadrupole weak law를 선택한 target rest frame에서 유도한다. 원문 MGE Eq71의 마지막 shear 부호 불일치가 있으므로 Eq70와 독립 angular integration by parts로 직접 확인하라. sources/LITERATURE_AND_REGIME_AUDIT.md의 coercivity 및 finite-electron Thomson 식은 미검증 후보이지 채택 전제가 아니다.

- Brightness≥0, spectrum/energy integration endpoint, tensor normalization, derivative-first omega, direction e=-outward n, c factors를 먼저 고정.
- Exact low-l equation의 유한 순간 jet relation과 전체 hierarchy evolution closure를 구별.
- 새 L_B 연산자에 대한 self-adjointness/coercivity, degeneracy, l0/2/4 dependence를 검산. 이미 알려진 결과인지 primary source와 대조하고 novelty를 주장하지 말 것.
- Cold unpolarized/thermal/recoil/finite electron velocity 가정을 분리; polarized extension은 필요/승인범위 안에서만.
- Target-frame high moments가 원 frame의 유한 low-l 데이터만으로 충분히 주어지는지 검사. Finite boost tail 계약을 생략하지 않는다.
- Exact law가 free time/source nuisance를 실제로 제한하는지 R5 quotient와 결합; 암묵적으로 jet를 0에 놓지 않는다.
- 승인된 가벼운 CAS와 별도 reviewer를 한 번 실행하고 근거·실패·수정·판정을 저장.

관측 branch를 대신 선택한다면 먼저 실제 selected data, distance convention, calibration, frame, covariance를 고정하라. R4 shell curvature/source allowance 및 R5 time/source quotient를 임의로 0으로 놓지 않는다. 광범위 모델 진화나 새로운 repository mutation은 이번 재개 계약에 포함하지 않는다.
