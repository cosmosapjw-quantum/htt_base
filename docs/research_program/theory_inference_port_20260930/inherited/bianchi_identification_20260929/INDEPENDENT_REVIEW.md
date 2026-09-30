# 독립 최종 검토

2026-09-29 · reviewer `/root/bianchi_independent_decision`

후보 생성과 계산 설계에 참여하지 않은 별도 에이전트로서 후보 원문, 선행 감사, 네 개 Wolfram 입출력 기록을 읽고 논증을 독립적으로 확인했다. 이는 역할상 독립 검토이며 다른 모델 계열·기관·인간의 외부 심사를 뜻하지 않는다. Wolfram을 재실행하거나 실제 관측을 분석하거나 proof kernel을 실행하지 않았다. 선행 감사가 인용한 저장소 원문 전체를 다시 읽었다고 주장하지 않는다.

**결정: BIC-01–06 및 BIC-03b는 아래 제한을 문서에 반영하는 조건으로 정의된 이론 결과와 후속 형식화 단계에 PROMOTE. BIC-07은 HOLD_MISSING_RESPONSE, BIC-08은 NOT_RUN/HOLD.** 치명적인 수학 오류는 발견하지 않았다. 이미 검증된 결과의 신규성 주장이나 실제 우주 유형 판정은 승인하지 않는다. 기존 I2 `DEFENDED_CONDITIONAL`, I3 `HOLD_INPUT_INCOMPLETE`는 그대로다.

## 명제별 판정

| 후보 | 판정 | 독립 확인과 필수 제한 |
|---|---|---|
| BIC-01 | PROMOTE | 표시된 Killing 장은 정확히 VII0 대수를 이루며 행렬식은 1이다. 같은 LRS 계량에는 translation I 작용도 있고 normal shear가 비영일 수 있다. 물리적 동일법칙 반례에는 두 action의 domain 모두에 허용되는 **동일한 완전 물리상태**를 고정해야 한다. 계량만 같다고 임의의 radiation/source law까지 같아지지는 않는다. |
| BIC-02 | PROMOTE | Jacobi와 scalar curvature식에 따른 모든 non-IX 부호 배제가 맞다. IX의 음의 curvature 예도 맞고 역명제는 거짓이다. spacelike simply-transitive homogeneous orbit를 전제해야 하며 Kantowski–Sachs나 회전하는 물질 rest spaces에 자동 적용되지 않는다. |
| BIC-03 | PROMOTE | Simple Ricci eigenframe에서 off-diagonal derivative가 연결계수를 모두 복원하고 torsion-free identity가 bracket을 준다. **이미 neighborhood의 local homogeneity가 가정된** 경우의 slice algebra 충분성이다. 유한 jet로 homogeneity를 인증하는 정리가 아니다. |
| BIC-03b | PROMOTE | 같은 유효·국소 추이적 G3가 h와 T를 보존하면 같은 증명이 성립한다. 목표는 h와 T의 공통 symmetry algebra이며 h만의 maximal isometry algebra가 아니다. T가 simple이고 DT=0이면 연결계수와 bracket이 0이라는 조건부 결론도 맞다. |
| BIC-04 | PROMOTE | geodesic/Fermi frame의 leading absolute direction drift에 대해 구면 모멘트 역산이 정확하다. source 쌍의 각거리 변화만으로는 공통 rigid rotation이 사라져 이 ω 복원이 불가능하다. |
| BIC-05 | PROMOTE | compensation이 domain 안에 있고 전체 noise law가 고정이면 정확한 same-law fibre가 성립한다. 평균의 퇴화만으로 전체 law 퇴화를 주장하면 안 된다. |
| BIC-06 | PROMOTE | 하나의 simultaneous mean confidence event에 의한 type-set coverage 증명은 맞다. 다만 sound outer containment와 **증명된** 불교차가 필요하다. 수치 탐색 실패는 배제 증명서가 아니다. |
| BIC-07 | HOLD | 실제 관측에서 complete spatial curvature/derivative input을 재구성하는 response·나머지·보정이 없다. |
| BIC-08 | HOLD / NOT_RUN | 실제 자료 적합과 유형 confidence set 계산을 수행하지 않았다. |

## 출판·인계 전에 유지해야 할 교정

1. **관측 가능한 label의 정의.** Bianchi type은 선언한 공간 군작용의 대수다. 같은 metric에서 여러 action이 가능하면 target을 label 집합으로 두거나, 어떤 추가 물리구조가 action을 선택하는지 밝혀야 한다. BIC-01의 반례를 일반적인 모든 I/VII0 우주 사이의 동등성으로 일반화하지 않는다. 국소/비콤팩트 구성은 임의의 compact quotient에 자동으로 내려가지 않는다.
2. **기하 충분성과 관측 충분성의 분리.** h3jet 또는 (h,T,DT)는 관측 distance/position drift의 작은 multipole 집합과 동일하지 않다. Slice action이 전체 시공간의 동일 G3가 되려면 시간에 따른 h 및 extrinsic data의 보존도 필요하다. T를 normal shear로 택할 때는 그 normal과 symmetry invariance를 고정해야 한다.
3. **조건수.** Γ 복원에 `(lambda_i-lambda_j)^(-1)`가 들어간다. 수학적 simple spectrum은 작은 eigenvalue gap에서 정확한 noisy classification을 보장하지 않는다. Near-isotropy regime에는 gap lower bound, covariance 및 remainder를 함께 전달해야 한다. Repeated-spectrum branch는 이번 결과의 밖이다.
4. **단위와 hypersurface.** BIC-02의 `Sigma_N²`는 `sigma_Nab sigma_N^ab`이며 half-contraction convention이 아니다. θ와 σ는 physical proper time의 역수, R3·Λ는 길이의 역제곱, ε_N은 에너지 밀도일 때 표시된 Hamiltonian 식의 c 차원이 맞는다. Tilted u의 θ·σ를 normal N의 변수에 대입하지 않는다.
5. **Drift 데이터의 종류.** BIC-04는 보정된 비회전 기준에서 측정한 absolute direction drift의 local coefficient다. Pairwise angular separation, 유한 관측기간의 catalog proper motion, 유한 redshift의 fit coefficient는 같은 입력이 아니다. Frame spin을 제한하지 않으면 BIC-05가 정확히 다시 적용된다.
6. **Set inference의 통계적 상한.** Random/data-dependent outer enclosure를 쓰면 그 포함 보장 event와 실패확률까지 confidence 계산에 합쳐야 한다. Mean-image rule은 covariance 또는 다른 distributional feature에만 있는 유형 정보를 쓰지 않을 수 있다. 이 한계는 coverage를 깨지 않지만 완전한 classifier라는 해석을 막는다. Nonempty outer intersection은 물리적 실현 가능성이나 posterior probability가 아니다.

## 직접 조회한 외부 근거

- [Heinesen–Korzyński, arXiv:2406.06167v1](https://arxiv.org/html/2406.06167v1): assumptions, geodesic/Fermi-Walker conventions, 식 (9)–(12)를 직접 조회했다. `κ₀=P(σ+ω)e`의 제한된 물리식과 일치한다. 고차 acceleration 부호 문제는 이번 승인 범위에 넣지 않았다.
- [Sáez–Mengual–Ferrando, arXiv:2409.15854v1](https://arxiv.org/html/2409.15854v1): 서론 및 invariant-frame connection tensor 구성을 직접 조회했다. 기하 불변량을 통한 알고리즘적 분류가 가능함을 뒷받침하지만, 실제 sky data가 필요한 기하 입력을 제공한다는 주장은 아니다.
- [Ferrando–Sáez, arXiv:2004.01877](https://arxiv.org/abs/2004.01877): metadata/abstract와 PDF 접근을 확인했다. 세부 증명 전체를 독립적으로 정독한 근거로 사용하지 않았다. BIC-03 판정은 후보의 elementary eigenframe 논증을 독립적으로 검토한 결과다.

Wolfram의 BIC-03 예제는 하나의 비자명한 consistency check이며 일반 증명을 대신하지 않는다. BIC-01/02/04는 명시된 정확 계산과 분석적 항등식이 서로 일치한다. 이번 결과는 “외부 Boltzmann solver가 없으면 아무런 분류 논증도 불가능하다”는 포괄적 ceiling을 좁힐 수 있지만, 미완성된 관측 재구성과 실제 우주 식별을 완료하지는 않는다.
