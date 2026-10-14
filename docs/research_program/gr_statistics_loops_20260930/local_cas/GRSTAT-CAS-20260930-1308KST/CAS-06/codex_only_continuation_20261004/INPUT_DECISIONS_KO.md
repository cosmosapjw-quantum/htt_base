# CAS06 성분별 입력 후보 — 채택 전

owner=research_program, scope=입력 준비성 및 독립 scalar calculus 부분목표, claim_tier=C0/non_claim_bearing, transfer_source=none, scientific_admission=HOLD.

원 계약 `bdec00798440d84909b8e3f79d95d963d58b7e73857dc32e33f6d204ada562b0`과 기존 CAS_CONFLICT는 그대로다. `NEUTRAL_SUCCESSOR_CANDIDATE.json`은 실행 계약이 아니며 현재 `NEEDS_OWNER_DECISION`이다. provenance-only 원문과 다른 축 proof/result에서 정의나 답안을 가져오지 않았다.

| 성분 | 실제 허용 입력 / 준비성 | 제안 / 필요한 결정 |
|---|---|---|
| C01 | 원 계약+COMMON_SPEC; metric/ODE는 원 계약의 uncontracted reference다 | spherical chart와 positive-root orthonormal frame, metric/ODE를 blind author의 중립 입력으로 명시 채택 |
| C02 | matched-event 목표는 있으나 frame·Weyl 미분 성분 미정의 | C01 frame을 공통 사용; Lambda0를 Lambda=0으로 해석하고 (nabla_e1 Weyl)(e0,e1,e0,e1)을 미분 목표로 채택 |
| C03 | 고정 양의 Pstar, 양의 X, 0<alpha<1의 monomial calculus는 독립 허용 부분목표 | 전체 metric stress/current는 C01 입력 채택 및 실제 변분·current 유도가 필요 |
| C04 | 발산량 및 fixed/varying family가 누락됨 | 후보는 |A|와 고정 c,kappa,alpha,epsilon0,p0,Pstar,q,mu,Lambda; r0=y/sqrt(C)만 변동 |

C04 후보의 정확한 식은 `|A|(y)=(c²|B|/sqrt(C)) y/sqrt(1-y²)`, `0<y<1`, `B≠0,C>0`이다. 이는 기존 인접 acceleration target에서 만든 **미채택 후보**이며 원문 발산량을 확인했다는 뜻이 아니다. 원래 의도한 발산량이 다른 것이면 그 식과 고정·변동 변수를 지정해야 한다. F0=0, alpha=0, r0=0은 허용 멤버가 아니다. distinct smooth germs의 존재·DEC persistence는 별도 해석 의무다.

`C03_SCALAR_CONTRACT.json`은 원 C03를 대체하지 않는다. 양의 실수 monomial의 실제 1·2차 미분과 algebraic E=2XP′−P, derivative ratio를 검증한다. 이 정의를 metric stress energy나 물리적 sound speed로 동일시하는 증명은 포함하지 않는다. 전체 C03 stress/current, C01/C02/C04 및 전체 CAS06 PASS로 집계하지 않는다.

네 축 작성자는 이 입력 후보나 이전 helper proof/result를 받지 않으며 같은 봉인 scalar 계약과 COMMON_SPEC만 받는다. 실제 engine execution·입력/도구 결속·독립 review·publication·scientific admission을 구분한다.
