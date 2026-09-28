# 독립 결정 검토 — MES_FRESH_OPTICAL_TENSOR_R1

검토자: `/root/fresh_theory_decision`. 날짜: 2026-09-20.

판정: **PROMOTE — 다음 이론·통계 방법 연구 단계에 한정한다.** 끝점 온도 텐서와 유한 응력 잔차 구간을 결합한 파일럿은 이 단계로 진행하기에 충분하다. 실제 관측 추론, 새 MES 전역 정리, 논문 신규성 또는 저장소/native admission은 이 판정의 대상이 아니다.

후보 생성과 최초 검증 설계에 참여하지 않은 별도 검토자이다. 고정 후보 `evidence/candidate_v1.md`, Wolfram 원시 호출·응답 두 개를 먼저 읽고 직접 수식을 검토했다. 이후 `checks.py`, `evidence/finite_checks.json`, 원전 확인 메모 및 좁은 정정 diff를 읽었다. 과거 프로젝트 판정과 기존 native audit는 읽거나 전제로 삼지 않았다. 재귀 검토 또는 추가 하위 검토자는 사용하지 않았다. 검토한 최종 파일의 SHA256은 `decision.json`에 기록한다. 해시는 파일 식별 증거이며 과학적 타당성의 증거는 아니다.

## 판정 근거

| 대상 | 판정·근거 상태 | 직접 확인한 범위 |
|---|---|---|
| 양의 이차 역온도 끝점 사상 | 통과 — derived, literature-supported, numerically checked | 공간 병진 Killing 상수, 관측 삼각대 변환, SPD·단위·등방 극한과 역산 유일성 |
| 약한 비등방 전개와 형태 | 통과 — derived, numerically checked | 평균 정규화의 2차 계수, STF quadrupole과 ℓ=4, 회전·온도 보정 불변성, χ 범위 |
| 응력 적분식과 잔차 구간 | 통과 — derived, algebraically checked | 적분 인자, 역방향 적분 부호, 적분 순서 교환, Frobenius 부등식과 단위 |
| MES 백분율 변환 | 정정 후 통과 — derived, literature-supported | 노름 convention, 3/2 계수, 1차 MES 범위와 유한 나머지의 구분 |
| 추정기·원천 가정 | 다음 방법 연구에 적합 | 이상 역산과 잡음 추정의 구별, nuisance source의 식별 가능성 조건, 보정·마스크·beam·boost 필요성 |
| 관측 검증·완전한 Einstein–matter 실현 | 미수행 | 이번 PROMOTE에 포함되지 않음 |

**끝점 사상.** 관측 방향의 공변 운동량이 `p=−(E_o/c)B_o^T n`이면 에너지 제곱비와 `M=T_*^−2 B_o h_*^−1 B_o^T`가 바로 따른다. 임의 대칭 M에 대해 `〈Y〉=tr(M)/3`, `〈Y nn^T〉=[tr(M)I+2M]/15`이므로 후보의 역산식은 정확하다. 완전한 이상 온도장이 주어진 경우에 한한 유일성이다. 임의의 비균질 방출 온도까지 허용하면 같은 관측장의 원인 유일성은 성립하지 않는다. 알려진 대각 Bianchi I 순방향 관계와 일치하며 이를 새로운 redshift 법칙이라고 주장하지 않는다. [Fleury–Pitrou–Uzan, IV.A, 식(4.5)](https://arxiv.org/pdf/1410.8473)

**2차 전개.** `〈r〉=I2/3`, `〈s²〉=2I2/15`이므로 `〈T〉/Tbar_scale=1−2I2/15+O(K³)`이다. 따라서 후보의 `Theta=−s−r+3s²/2+2I2/15+O(K³)`와 ℓ=4 항은 맞다. 특성다항식의 판별식은 `I2³/2−3I3²≥0`을 주므로 `|χ|≤1`이다. K 자체를 보유하는 것은 부호와 관측 방향을 보존한다. 단, `I2=0`에서 χ는 정의되지 않는다. 서로 다른 고유값이 합쳐질 때 개별 고유벡터 추정은 불안정하므로 향후 통계 연구는 고유공간 또는 K를 직접 다루어야 한다.

**동역학 연결.** `a_o=1`에서 `a(t)³sigma(t)=sigma_o−∫_t^o a(s)³P(s)ds`를 적분하면 `K=I sigma_o−J`가 나온다. W는 음수가 아니므로 `||J||≤∫Wp=R_pi`; 따라서 구간과 상·하한에 부호 오류가 없다. `a`, `p`와 공통 비교 프레임이 주어져야 하며 이 외부 구간은 완전한 물질 실현 집합의 특성화가 아니다. 자기중력 CMB가 비등방 응력을 만들 수 있다는 제한을 후보가 명시했으므로 P=0을 일반적인 정확한 방사 우주로 잘못 승격하지 않는다. 고정 FLRW 배경의 backreaction 제어도 조건으로 남겨 두었다.

**MES 정규화.** 직접 읽은 원전은 공간 텐서 크기를 `sqrt(Q_A Q^A)`로 정의한다. 따라서 `||sigma||/theta≤B`, `theta=3H`에서 `x_sigma≤3B²/2`는 맞으며 별도의 sqrt(2) 보정이 필요하지 않다. 원전의 1차 계산과 도함수 가정 때문에 압축 B를 자동으로 유한 정확 상한이라 부를 수는 없다. `B_lin+Delta_sigma` 또는 명시적인 leading-order/reference ratio로 구별한 정정은 이 문제를 해결한다. [MES 원전, 표기와 식(42)–(45), (51), C1–C2, 식(59)](https://arxiv.org/pdf/astro-ph/9501016)

`100F_sigma`는 제곱 노름 예산의 비율이고 `100sqrt(F_sigma)`는 노름 예산의 비율이다. 이를 전체 시공간의 비-FLRW 분율로 해석하지 않는 구분이 옳다. `U_sigma=0`이면 유효한 bound는 sigma=0을 강제하지만 비율은 0/0이다. A, Q, F에는 `U_sigma>0` 정의역이 필요하다.

**추정과 원천.** 비제한 Gaussian pixel 온도를 역제곱하여 모멘트를 추정하면 0 부근 밀도로 인해 역모멘트가 발산할 수 있다는 지적은 수학적으로 맞다. 온도 공간의 순방향 적합은 건설적인 대안이다. 유한 선형 모형의 원천 covariance를 외부 가정으로 선언하면 조건부 통계 연구는 가능하다. 임의의 원천 nuisance에는 k와 상쇄하는 방향이 존재하므로 원천 가정 없이 homogeneous shear를 식별할 수 없다는 제한도 적절하다. 아직 likelihood, 식별 행렬의 rank, 오차 coverage를 검증한 결과는 없다.

## 실제 증거의 강도

- `wl_checks_1.json`의 재구성·2차/3차 각모멘트 잔차는 0이다. undefined-symbol 경고가 있지만 최종 대수식 결과를 확인했다. 이 파일의 `axisShapeValues`는 입력에 상수로 적혀 있으므로 그 항 자체는 검산으로 세지 않았다. 실제 형태 계산은 `wl_checks_2.json`에 있다.
- `wl_checks_2.json`은 같은 노름에 χ=0,−1을 계산하고, sourced toy의 미분식·끝점·적분 항등식 잔차를 0으로 반환한다.
- `finite_checks.json`과 그 생성 코드를 읽었다. 재구성·로그·보정 불변성 오차는 약 10^−15, 2차 나머지의 진폭 반감 비율은 7.997–8.000이다. 축대칭 ℓ=4 계수는 27/35에 접근한다. 이는 한 회전된 유한 비등방 사례와 작은 진폭 계열의 체크이며 관측 적합이나 전역 수치 증명이 아니다.
- 별도 표준 라이브러리 유리수 계산으로 평균의 −2/15, 축대칭 27/35, toy I=2, J/C=5/6, MES 3/2를 재확인했다. 결과는 `evidence/reviewer_checks.json`이다. SymPy가 두 runtime에 없어서 해당 엔진 검산은 실행되지 않았고, 이를 성공으로 세지 않았다.

## 강한 대안과 다음 단계의 비교

| 경로 | 실제로 더 강한 부분 | 바꾸어 요구하는 정보 |
|---|---|---|
| 일반 low-z 방향 우주운동학 | Bianchi 가정 없이 현지 sigma 자체를 H_obs의 quadrupole로 겨냥함 | 거리·적색편이 표본, 공통 emitter/observer congruence, peculiar motion, 방향별 비영 H_obs, 유한-z 나머지 제어 |
| tensor-valued 잔차 집합 | 각 항을 노름으로 압축하기 전 방향·상관관계와 상쇄 구조를 유지할 수 있음 | 닫힌 잔차 방정식, 비교 프레임, derivative/source 집합 또는 적분 제약의 독립 입력 |
| 현 후보: 끝점 K와 응력 구간 | CMB 형태를 정확한 조건부 사상으로 보존하고 수치 진화 없이 현재 sigma의 외부 구간을 줌 | 방출원·동축/transport 조건, a(t), p(t)의 물리적 근거 |

low-z 경로는 현재 shear가 목표일 때 중요한 병행 경로다. 후보의 가속도 부호는 바깥 관측 방향 n convention과 일치한다. 해당 거리 급수는 redshift의 국소 역함수와 유한 나머지 제어를 요구한다. 이는 endpoint 후보를 폐기할 이유가 아니라 독립적인 현지 anchor를 제공한다. [Heinesen, 식(2.11), (3.10), (4.1), §5](https://arxiv.org/pdf/2010.06534)

Tensor 잔차 집합은 방향 정보를 보존할 수 있다는 점에서 scalar MES bound보다 유리하다. 다만 그 집합을 관측 amplitude만으로 결정할 수 있다는 결론은 아직 없다. 이번 단계에서 전역 almost-EGS 확장 정리의 완성을 요구할 필요는 없다.

## 발견된 문제와 반영 조건

1. 최초 후보는 compact MES의 도함수 가정을 “명시해야 한다”고만 적었고 1차 bound와 정확한 유한 bound를 충분히 구별하지 않았다. owner의 제한된 정정에서 실제 가정과 Delta_sigma/reference 구분을 추가한 것을 검토했다. 핵심 끝점·응력 식은 바뀌지 않았다.
2. χ의 `I2>0`, 정규화 텐서·비율의 `U_sigma>0` 정의역을 명시해야 한다. 이 보완은 0/0을 수치 결과로 보고하는 것을 막는다. 최종 반영 상태는 `decision.json`에 기록한다.
3. 다음 단계에는 실제 사용할 원천 covariance/응력 budget과 목적 파라미터를 먼저 선언하고, 그 유한 모형의 식별 가능성·오차를 평가해야 한다. 이는 이번 파일럿의 실패가 아니라 후속 연구의 구체적 목적이다.

해당 단계의 핵심 치명 오류는 발견하지 못했다. 원래 목표인 CMB-운동학 연결, 물리적으로 선언된 bound에 대한 비율, 텐서 형태 보존을 유지하면서 각 가정의 역할을 드러냈다. PROMOTE는 이 제한된 후보의 추가 이론·통계 방법 개발에만 적용한다.

## 추가 고정 후보 검토 — 정확한 국소 텐서 잔차 정리

별도 판정: **PROMOTE — 국소 연산자 정리와 이를 이용한 조건부 잔차 집합 연구 단계.** `TENSOR_RESIDUAL_THEOREM.md`의 고정 유도, `evidence/wl_checks_3.json`의 원시 호출·응답을 검토했다. 후보 또는 최초 검증을 설계하지 않았으며, 독립 결정 검토 중 대수 검산만 추가했다. 최초 판정 파일·원래 검토문은 `evidence/decision_gate_initial.json`, `evidence/decision_review_initial.md`에 보존했다. 최초 추가 후보도 `evidence/tensor_residual_candidate_v1.md`에 보존했다.

**부호와 에너지 계수.** congruence shear에 의한 방향 변화는 `−w`, `w=(I−ee^T)Se`이다. 주파수 변화항의 에너지 적분은 `−s∫E⁴∂_E f dE=4s∫E³f dE`이며 끝점 `E⁴f→0`을 사용한다. 따라서 후보의 `−w·grad B+4sB`가 맞다. S가 물리적 시간 역수 단위를 가지면 L_B(S)와 r은 에너지 밀도/시간 단위이다.

**부분적분.** `w=grad(s)/2`, `Delta_S² s=−6s`이므로 `div w=−3s`. `mathcal E=ee^T−I/3`에 대해 `w·grad mathcal E=(Se)e^T+e(Se)^T−2s ee^T`. 구면 부분적분에서 −3s와 redshift의 +4s가 합쳐져 +s가 되고, 결과는 정확히

`L_B(S)=S M2+M2 S−M4:S−I(M2:S)/3`

이다. 출력 trace는 0이며 짝수 4차 이하의 angular kernel만 있으므로 brightness의 ℓ=0,2,4만 관여한다. 이는 전체 kinetic hierarchy가 닫힌다는 주장이 아니다.

**자기수반성과 coercivity.** `T:L_B(S)=∫B[2(Te)·(Se)−(e^TTe)(e^TSe)]dOmega`는 S,T에 대칭이다. Cauchy–Schwarz로 `s²≤|Se|²`이므로 `S:L_B(S)≥tr(S²M2)≥lambda_min(M2)||S||²`가 따른다. `rho>0`인 비음수 L1 밀도에서는 모든 대원의 면적 측도가 0이므로 M2는 자동으로 양의 정부호이다. 이 조건은 잘 조건화된 역행렬을 보증하지는 않는다. 한 방향으로 집중되는 밀도 계열에서는 가장 작은 고유값이 0에 접근할 수 있다.

**추가 원시 검산.** 직접 angular derivative가 포함된 원래 A_S B를 별도 sparse-polynomial 코드로 계산해 구면에 적분했다. 다섯 STF basis의 모든 짝에 대해 최종 쌍선형식과의 차이가 정확히 0이었다. `B=(1+3z²)²`에 `0.1 P6(z)+0.1x`를 더해도 같은 결과였고, ℓ=1,6 추가분은 L_B를 바꾸지 않았다. 정규직교 basis에서 고유값은 `176/105,352/105,176/105,64/21,64/21`, 등방 값은 모두 `8/15`, 제시된 coercivity 여유는 `24/35`로 WL 결과와 일치했다. 이는 구면 평균 convention이며 full-sky 적분 convention에서는 일괄적으로 4π가 곱해진다. 실행 코드와 결과는 `evidence/reviewer_tensor_checks.py`, `evidence/reviewer_tensor_checks.json`이다.

**해석 범위.** B와 독립적으로 선언한 잔차 집합 R가 주어지고 M2가 양의 정부호이면, 이 국소 block의 정확한 해집합은 `L_B^−1 R`이다. 실제 residual이 S 또는 다른 미지의 운동학 변수와 연결되어 있으면 공동 적합성 문제를 풀어야 한다. 현지 정적 CMB 밝기는 연산자를 정하지만 시간·공간 미분을 포함하는 r을 결정하지 않는다. 이 정리는 Bianchi 모형과 Einstein 방정식을 요구하지 않는 국소 전단 제약이며, 전역 거의-FLRW, 관측에 의한 shear 식별 또는 새로운 canonical percentage를 증명하지 않는다.

**실제로 발견하고 해결한 표현 오류.** 최초 추가 후보의 singular M2 문장은 매끄러운 비음수 밝기 class와 특이 측도 class를 구분하지 않았다. 최종 정정은 매끄러운 class에서 singular M2가 B=0을 강제함을 명시하고, 확대된 측도 class는 별도로 제한했다. 또한 support function이 비볼록 잔차 집합 자체를 복원하는 것처럼 읽힐 수 있던 문장을 closed convex hull까지만 복원한다고 고쳤다. 두 정정 diff를 직접 읽었다. 별도 `agent_optics_operator_addendum.md` 전체를 검토한 판정은 아니다.

문헌의 전문화된 식과 general hierarchy 사이에서 계수 표기 불일치를 발견했으므로, 특정 문헌식과 정확히 같다는 주장을 이 결정의 근거로 삼지 않았다. 해당 원전 열람은 [Maartens 2011 식(19), Appendix A37](https://arxiv.org/pdf/1104.1300), [Maartens–Gebbie–Ellis 1999 식(88)–(89), (98)](https://arxiv.org/pdf/astro-ph/9808163)에 한정했다. 후보 연산자는 위 직접 Liouville·부분적분 유도와 별도 raw-generator 검산으로 판정하며 신규성은 판정하지 않는다.

기존 DERIVATIONS의 χ와 U_sigma 영분모 정의역 보완도 최종 파일에서 확인했다. 다음 단계의 실질적 과제는 물리적으로 방어 가능한 공동 residual 집합을 구성하고, 역연산의 조건수와 실제 데이터 오차를 전달하는 것이다. 이번 PROMOTE에 남아 있는 필수 문서 정정은 없다.
