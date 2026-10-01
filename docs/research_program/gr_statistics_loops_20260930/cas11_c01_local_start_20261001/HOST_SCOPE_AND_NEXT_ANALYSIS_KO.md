# C01 입력 정렬과 다음 해석적 의무

Owner: research_program. Scope: 다음 유한 CAS 작업의 Host 준비 및 기존 해석적 경계의 구체화.
상태: 아래 식의 직접 유도와 입력 명세. 새 CAS 실행·형식 증명·과학적 admission·novelty 승격은 없다.
이 문서는 독립 축별 작성자에게 adjudication 이전에 전달하지 않는다.

## 1. C03 반환에서 받아들일 범위

C03의 원 계약·관측 판정·독립 검토는 일치한다. 보조 Wolfram receipt 두 개의 오래된 해시는 수학 오류가 아닌 packaging metadata 오류로 분류되었고, 수정 후 원 수학 소스 14개는 변하지 않았다. 원 검토와 이전 seal을 그대로 보존한다. 이는 C02/C03 재실행 사유가 아니다.

C02는 PSD R에 대해 모든 a의 이차 부등식에서 range와 의사역행렬 bound를 얻는다. C03는 유한 W-직교투영에서 잔차 Gram의 PSD와 Cauchy–Schwarz를 준다. 다음 최소 실행은 이미 존재하는 C01 version 3의 Bregman 항등식과 정확한 moment cancellation이다.

## 2. C01의 식과 입력

E는 유한 차원 실수 벡터공간이고 dPhi(x)∈E*이다. 공통 정의역의 f,g,h에서
`D_Phi(x||y)=Phi(x)-Phi(y)-dPhi(y)[x-y]`를 사용한다.
함수값을 소거하면

```text
D_Phi(f||h)-D_Phi(g||h)
 = Phi(f)-Phi(g)-dPhi(h)[f-g],

D_Phi(f||g)
 = D_Phi(f||h)-D_Phi(g||h)
   +(dPhi(h)-dPhi(g))[f-g].
```

M:E→R^m, M(f-g)=0와 dPhi(h)-dPhi(g)=M*lambda를 함께 주면
`(M*lambda)[f-g]=lambda[M(f-g)]=0`이다.
따라서 부호는 원 계약과 맞는다. 모든 항은 Phi와 같은 단위를 갖는다.
미분가능성은 미분을 정의하기 위한 조건이다. convexity는 이 대수 항등식이나 span cancellation에 필요하지 않으며, entropy bound의 비음수성·Hessian 추정과 별개다.

원 C01의 짧은 정의는 moment matching의 작용 대상이 모호하다. 원 부모 [CAS-11](../cas/contracts/CAS-11.json)의 span 조건을 위처럼 명시한다. 원 계약 SHA는 유지하며, 새 실행에서 이 해석을 모든 축이 같은 statement_alignment로 확인한다. 정렬이 되지 않으면 차이를 보존하고 범위를 임의 축소해 PASS를 내지 않는다.

새 중립 명세 자체는 v3의 네 permitted_inputs에 열거되어 있지 않다. 문서 SHA와 이 차이를 명시하고, 로컬의 지원된 입력 허용 절차를 확인한 뒤 전달한다. 추가 입력이 금지되는 경우에는 dispatch 전 불일치를 반환한다. 이는 원 계약의 과거 허용 목록이나 독립성 기록을 소급 변경하지 않는다.

**조건을 빠뜨렸을 때의 control — 직접 유도, CAS 미실행.**
E=R², Phi(x)=||x||²/2, M(x)=x₁, g=(0,0), f=h=(0,1)이면 Mf=Mg=0이다. 그러나 gradient 차=(0,1)는 M*의 range에 속하지 않으며 교차항은 1이다. D(f||g)=1/2, D(f||h)-D(g||h)=-1/2다. 정확한 항등식은 성립하지만 moment matching만으로 교차항을 지울 수 없다. 이는 전체 span 조건을 갖춘 원 명제의 반례가 아니다.

## 3. 유한 성분 다음에 남는 연결

[기존 positive bridge](../supplements/TEFF_POSITIVE_BRIDGE.md)의 Proposition A는 다음 별도 입력을 요구한다. 원 유도문은 역사적 연구 자료이며 이번 준비에서 전부 재검증하지 않는다.

| 의무 | 필요한 입력·주장 | 현재 처리 |
| --- | --- | --- |
| entropy 정의 | 동일 observer·측도·정규화에서 H(f), D_H(f||g), 미분과 각 적분의 존재 | 후속 해석적 명세 |
| Taylor/Hessian | segment 전체의 정규성과 h''(z)≥1/w>0; 경계에서는 유효한 극한 증명 | C01 유한 항등식으로 대체 불가 |
| 상태 norm budget | D_H(f||g)≤epsilon에서 ∫(f-g)²/w dnu≤2epsilon | 별도 해석적 의무 |
| Hilbert 실현 | w>0 a.e.; scores·kernels∈L²(w dnu), 유한 moments·observable 적분, 영함수 동치류 처리 | 연속체 전제를 명시해야 함 |
| 보편 오차 부등식 | 모든 a에 대해 |a·e|²≤2epsilon aᵀRa | 확보되면 기존 C02 적용 |
| 물리적 인증 | 실제 epsilon 상계, 양 상태를 덮는 envelope, calibrated kernels·moments·오차 집합 | 관측/물리 입력은 아직 미제공 |

여기서 w는 연속체의 스칼라 weight다. C03의 유한 내적 W와 같은 종류의 대상으로 혼동하지 않는다. delta=f-g라 하면 Hilbert 공간 L²(w dnu)의 상태 대표는 delta/w이고, 그 제곱 norm이 ∫delta²/w dnu다. 정확한 moments는 이 대표가 retained score span과 직교한다는 조건으로 옮겨진다. 잔차 kernel의 Gram은 R_ij=∫w r_i r_j dnu다. 이 실현을 정당화한 뒤에야 모든 계수의 dual bound를 얻는다.

동결된 정규화의 occupation entropy kernel에서는 h''(z)=1/[z(1+xi z)]이므로 reciprocal-Hessian envelope는 w≥z(1+xi z)다. 물리 entropy에 k_B 등 정규화 상수를 곱하면 Hessian·divergence budget·weight의 스케일도 일관되게 바꿔야 한다. 상수를 암묵적으로 1로 두지 않는다.

BE의 저에너지 endpoint·FD 포화 endpoint 및 무한 tail은 단순한 유한 대수 검산으로 닫히지 않는다. 특히 원 유도문의 endpoint-limit 문장을 사용할 때는 적절한 lower-semicontinuity/수렴 가정과 적용 영역을 명시해야 한다. epsilon은 fitted reference의 entropy나 retained moments만으로 얻지 않는다.

## 4. 이번 결정

C01의 원 계약 SHA와 입력 7개를 고정하여 finite identity+span cancellation을 다음 로컬 단위로 실행한다. 위 해석적 의무는 후속 연구용 목록이며 이번 C01 실행 계약에 섞지 않는다. C01이 통과하더라도 CAS-11 부모의 닫힘은 따로 판정한다.

C02/C03와 CAS13-C04의 기존 결과·실패·launch를 보존한다. deterministic residual Gram을 관측 noise covariance로 해석하거나, 정리의 성립을 catalogue fit·kinematic identification으로 확대하지 않는다. 관측 likelihood, Bianchi 분류, 연속체/물리 closure, novelty의 승격은 없다.
