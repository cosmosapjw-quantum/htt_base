# CF4 방향 Q/가속도 유사 통계의 정보 결손 계량

**결론:** 실제 CF4에서는 등록된 q_cat gate가 여전히 WITHHELD다. 점추정 또는 p-value를 내지 않는다.

| Fold | 등록 q 정보잔여비율 | 재매개화 불변 최약 상대 Fisher 정보 | 목표 0.05까지의 정규화 추가 정보 trace |
|---|---:|---:|---:|
| 0 | 0.00928671 | 0.00275395 | 0.129087 |
| 1 | 0.0097366 | 0.00287834 | 0.128619 |
| 2 | 0.00834363 | 0.00267348 | 0.129468 |
| 3 | 0.00947112 | 0.00267408 | 0.129509 |
| 4 | 0.00898791 | 0.00229616 | 0.129039 |

현재 관측 템플릿 행렬에서 계산한 상대정보 고유값은 모델의 nuisance, 부호, 단위와 불변성에 조건부.
기준 0.05는 기존 PR179의 사전 등록 임계비율을 새로운 generalized eigen geometric target으로 옮긴 **가상 정보제공자 설계 기준**이지 기존 gate의 소급 수정이 아니다.
스칼라 basis 회전/재매개화는 실제 부족한 관측 정보의 독립된 증가를 만들지 않는다.
외부 independent directional channel, 실제 selection/calibration likelihood, physical congruence response 없이는 q를 과학적 결론으로 승격하지 않는다.
기존 H_ONLY conditional result와 등록된 prospective verdict를 불변 보존했다.
