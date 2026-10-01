# CAS11-C01 중립 실행 명세

원 계약: `GRSTAT-20260930-CAS11-C01-BREGMAN`, version 3.
경로: `docs/research_program/gr_statistics_loops_20260930/cas_corr_followup_20260930/intake/contracts/CAS11-C01-BREGMAN.json`.
SHA-256: `57202993c9305a15deda1fc142c538473ec17e93453471063f04a5e04bb36624`.

이 문서는 실행할 입력 의미를 명시한다. 원 계약의 바이트, 판정 기준 또는 과거 결과를 변경하지 않는다.

입력 provenance: 이 새 공통 명세는 v3의 `independence.permitted_inputs` 네 경로에 포함되어 있지 않다. 그 사실과 문서 SHA를 HANDOFF_STATE.json에 별도 기록한다. Host는 현재 지원되는 입력 허용·정렬 절차를 확인한 뒤에만 축별 작성자에게 이 문서를 전달한다. 동결 목록이 배타적이고 지원된 추가 명세 허용 경로가 없으면 실행 전 불일치를 반환한다. 원 계약을 몰래 바꾸거나 원래 허용된 파일이라고 표시하지 않는다.

## 공간·미분·방향

E는 임의 유한 차원 실수 벡터공간이다. 공통 정의역의 f,g,h에서 Phi의 미분 dPhi를 사용하며 E*와 E의 표준 dual pairing을 쓴다. grad 표기를 사용하는 축은 하나의 양의 정부호 내적을 명시하고 그 Riesz 표현과 adjoint를 일관되게 사용한다. Lorentz 계량은 이 명제의 pairing이 아니다.

`D_Phi(x||y)=Phi(x)-Phi(y)-dPhi(y)[x-y]`로 정의한다.

목표는 다음 원 계약의 정확한 방향과 부호다.

`D_Phi(f||g)=D_Phi(f||h)-D_Phi(g||h)+(dPhi(h)-dPhi(g))[f-g]`.

유한 항등식은 임의의 미분 가능한 Phi에 대해 검증한다. convexity나 Hessian 하한, divergence 비음수성을 이 항등식의 필수 가정으로 추가하지 않는다. 추상 함수값·미분값으로 일반 대수 보조정리를 증명할 수 있지만, 이를 주어진 미분 가능한 Phi에 적용하는 진술 정렬도 제시한다.

## 정확한 moment cancellation의 입력

M:E→R^m은 선언된 실수 선형 moment map, M*: (R^m)*→E*는 dual map이다. R^m의 표준 pairing으로 lambda를 covector로 식별한다. 다음 두 조건을 함께 선언한다.

- `M(f-g)=0`.
- 어떤 lambda에 대해 `dPhi(h)-dPhi(g)=M*lambda`.

내적·gradient 표현에서는 동일한 조건을 adjoint로 적는다. 이는 원 부모 CAS-11의 `gradient difference lies in the span of matched linear moments`를 구체화한 것이다. 교차항이 이미 0이라는 결론 자체를 가정으로 넣지 않는다. moment matching만으로 gradient-span 조건을 생략하거나, M(gradient difference)=0으로 바꾸지 않는다.

원 C01 문구와 이 parent-consistent 해석의 대응을 실행 전 statement_alignment에 명시한다. 계약 의미가 이보다 강하거나 다르다고 판단하면 해당 차이를 반환하고 임의로 v3를 수정하거나 PASS를 만들지 않는다.

목표: 위 정확한 입력하에서 원 항등식의 교차항 소거와 해당 divergence 차의 등식을 증명한다.

## 범위와 반환

임의 유한 차원, 영차원, 빈 moment map, rank-deficient/중복 moments, f=g, gradient 차=0을 다룬다. 빈 map에서는 span 조건도 함께 적용된다. M의 가역성·full rank·특정 Bianchi 유형은 요구하지 않는다.

보편 항등식의 부호 control과 gradient-span 조건을 제거한 경우의 음성 control을 각 축이 독립적으로 구성한다. 특정 이차 Phi나 작은 차원 예제만으로 보편 PASS를 내지 않는다. 실제 물리 entropy functional의 미분가능성, 적분·경계 극한과 Hessian envelope는 별도 의무다.

원 계약과 허용 중립 입력, 이 명세만으로 작업한다. Host용 유도·상태 판정, 과거 또는 형제 축의 증명·결과를 adjudication 이전에 읽지 않는다. 실제 노출은 기록한다. 원 obligation key `CAS11-C01-BREGMAN`, 네 축, raw 출력과 source seal을 유지한다.
