# 2026-10-15: 동일 Planck 하늘의 고차 누출 공동통계

등급: **실제 SMICA 관측-모의 산출물에 대한 탐색적 조건부 결과.**

보정 이후 p-rank는 해당 모형의 actual/null 교환가능성이 참일 때만 유효.
동일 하늘의 여러 mask/처리방식을 독립 사건으로 세지 않았다.

| Mask/feature | observed standardized score | marginal p-rank | joint-max adjusted p-rank |
|---|---:|---:|---:|
| 0:baseline | 1.51823 | 0.713693 | 0.987552 |
| 0:0.25 | 8.01883 | 0.572614 | 0.576763 |
| 0:1 | 4.42724 | 0.672199 | 0.879668 |
| 0:4 | 2.63636 | 0.73029 | 0.966805 |
| 1:baseline | 1.39224 | 0.73029 | 0.987552 |
| 1:0.25 | 7.93033 | 0.585062 | 0.589212 |
| 1:1 | 4.43325 | 0.676349 | 0.879668 |
| 1:4 | 2.64414 | 0.713693 | 0.962656 |

8-feature same-sky joint max-rank: 139/241 = 0.57676349

대조변수 H는 ell12,ell5 fit 차이이므로 물리적 high-mode coefficient의 독립적인 측정이 아니다.
추정된 회귀 B는 training60 하늘에서만 추정하고 관측 및 나머지 240 null 하늘에는 같은 변환을 적용한다.
CP는 주어진 관측 문턱의 iid null exceedance q 구간이지 finite rank 자체의 CI가 아니다.
source-surrogate boost Fisher는 물리적 속도/기울기 posterior나 Bianchi/전단 검출이 아니다.

원전: Planck Collaboration IV (2020); Phipson & Smyth (2010); Hemerik & Goeman (2018); HTT GR/STAT report and prior processed Jacobian.
