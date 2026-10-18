# Planck 고차누출 모드의 실제 mask 기하 기반 저차원 제어

대상: 동일 실제 SMICA 관측 하늘, 저장된 300 paired FFP10 CMB+noise 모의 하늘.
조건부 순위 및 예측력만 평가하며 실제 FFP10=observed sky 완전한 물리 null은 검증되지 않았다.

| mask | 선택 train-only | CV MSE 변화 | heldout MSE 변화 | paired 95% 구간 |
|---|---|---:|---:|---|
| 0.5 | rank3_rho4 | -0.7328% | 0.2345% | [-0.134%,0.605%] |
| 0.8 | rank3_rho4 | -0.7641% | 0.2600% | [-0.074%,0.641%] |

Conditional 2-mask joint rank: 172/241 = 0.7136929

상위 고차 누출 기하모드를 이용한 통계적 회귀는 반드시 예측력이 개선된다는 뜻이 아니다.
같은 하늘의 mask 변형·모드 상한을 독립 모의실현으로 취급하지 않았고, 240 heldout 행에서 모델을 선택하지 않았다.
대체로 현재 원본의 noise/systematics와 CMB cosmic variance에 대한 물리적 모델 확인이 필요하다.
선행 연구: Gruetjen & Shellard (arXiv:1212.6945), Planck 2018 IV (A&A 641 A4), HTT prior processed boost/Jacobian.
