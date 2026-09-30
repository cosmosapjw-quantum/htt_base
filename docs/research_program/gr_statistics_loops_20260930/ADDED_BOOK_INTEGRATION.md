# 추가 책의 실질적 반영: 인과구조, 척도, 관측 역산의 입력

2026-09-30. 대상은 사용자 제공 `upload/book.pdf`, **RBK 프로젝트, 『Reichenbach 상대성이론 공리화: 현대적 재구성과 비평적 주해』, 2026-01-22**, 404 PDF쪽이다. Reichenbach 원전이나 독립 심사를 마친 연구서로 취급하지 않는다. 책 자체의 PDF5/인쇄1 §§1.1–1.2는 L0 원전 인용, L1 주장 추출, L2 현대 재구성, L3 외부 비평을 구분한다. 이 추가 검토는 그 구분을 유지한다. 404쪽 완독이나 원전 대조 전체 완료를 주장하지 않는다.

## 1. 읽은 위치와 근거 수준

PDF3–4의 차례는 실질적 항목이 없는 상태여서 목차로 범위를 확인할 수 없었다. 추출문 검색 뒤 아래 본문을 직접 읽었다. PDF 페이지는 1부터 세며, 확인한 본문에서는 인쇄 페이지=PDF−4이다. PDF135,193,323은 실제 렌더도 확인했다.

| PDF / 인쇄 | 정확한 위치 | 역산에 반영할 내용 |
|---|---|---|
| 5 / 1 | §§1.1–1.2 | 프로젝트 재구성과 원전의 지위를 구분 |
| 24 / 20 | §4.7.2, Definition 2 | 순서보존 시각 부여가 곧 물리적 proper-time calibration은 아님 |
| 28–29 / 24–25 | §§4.8.4–4.8.5 | 좌표 동기화 `t'=t+σ(x)`와 왕복 관측 불변성; 실제 observer 변경과 구분 |
| 135 / 131 | §§24.1–24.3 | null/conformal 및 free-fall/projective 정보와 clock 조건을 분리하는 EPS 로드맵 |
| 189–190 / 185–186 | §§36.1–36.2 | rod/clock 도입, scale connection과 물질의 정규성은 추가 가정 |
| 193–194 / 189–190 | §37.1.2 주해 CR-015, CR-016; §37.2.1 Theorem 26 | 단위 동일성·운반성은 빛 공리의 자동 귀결이 아님; 기준 막대와 실수값 비율 측정이 증명에 추가됨 |
| 204 / 200 | §§39.1.1–39.1.4 | 빛/자유낙하/물질 측정 가정의 별도 관리 |
| 295–296 / 291–292 | §58.1.5.2 CR-022; §58.1.6.1.3 C3 | clock hypothesis를 기하 공리와 분리; 인과복원 정리의 정규성·구별성 조건 |
| 323–324 / 319–320 | §65.5.1 Theorem 40.7, §65.5.2 Lemma 40.8, §65.6 | 무매개 null 경로는 등각류까지만 정함; 정적 optical metric과 proper clock rate의 차이 |

책의 번호는 **RBK 재구성의 번호**다. “Reichenbach의 원전 Theorem 40.7을 확인했다”고 인용하면 안 된다. PDF323의 논증은 등각변환이 null 경로를 보존한다는 방향을 설명한다. 주어진 모든 null 경로에서 등각류를 유일하게 재구성하는 역방향의 정규성·데이터 가정까지 이 한 쪽이 증명한 것은 아니다.

## 2. 일차 문헌과의 제한된 대조

- **EPS**: Ehlers–Pirani–Schild, 1972, 원래 pp63–84; 2012 재출판 *GRG*44,1587–1609, [DOI](https://doi.org/10.1007/s10714-012-1353-4). 출판사 초록에서 4차원 manifold의 compatible conformal/projective structures를 통한 Lorentzian geometry 재구성이라는 범위를 확인했다. 본문은 구독벽이 있어 이번에 읽지 못했다. 그러므로 second-clock 조건의 정확한 필요충분 정리를 EPS 원문 검증 완료로 기록하지 않는다.
- **Malament**: 1977, *JMP*18,1399–1404, [출판사 원문 페이지](https://pubs.aip.org/aip/jmp/article-abstract/18/7/1399/460709/The-class-of-continuous-timelike-curves-determines?redirectedFrom=PDF). 출판사 검색 제공 초록은 past/future distinguishing 조건에서 causal structure가 topology를 정한다는 corollary를 명시한다. 직접 DOI open은 실패했고, 전체 증명은 읽지 않았다. “인과순서만 있으면 임의 시공간의 calibrated metric이 정해진다”는 주장에 사용할 수 없다. 이 논문은 동시성 관습성에 관한 별개의 Malament 1977 논문과 구분한다.
- **Wheeler**: [arXiv:2404.03815v2](https://arxiv.org/html/2404.03815v2), 초록과 §§1.1–1.3을 확인했다. EPS류 결론이 허용 connection과 reparameterization 가정에 의존한다는 최근 원저의 문제 제기를 참고한다. 그 일반화 전체를 채택하거나 EPS 반박이 확정되었다고 하지 않는다. 이번 inverse는 기존 Levi-Civita 설정에 머문다.
- **Ellis R01**: 이미 확인한 (4.2),(4.38),(7.17),(7.40)–(7.48)이 실제 역산의 수학적 근거다. 새 책은 이 식에 숨어 있던 **입력 정보의 종류**를 드러내는 데 사용한다. 아래 척도 식은 원문 인용이 아니라 이 표준 식으로부터의 직접 유도다.

## 3. 기존 정리에 추가할 입력 계약

기존 fixed-metric local inverse의 결론은 유지하되 가정에 다음을 명시해야 한다.

| 입력 계층 | 명시할 가정 | 생략 시 허용되는 결론 |
|---|---|---|
| 기하 | 충분히 매끄러운 Lorentz metric **representative g**와 그 Levi-Civita connection; 방향성 | causal order나 무매개 null 경로만으로 동일 역산 불가 |
| 물질 | vertex까지 정의된 매끄러운 source congruence와 물리적 observer worldline; unit normalization | source가 무엇인지와 source jet은 빛 구조만으로 주어지지 않음 |
| 시계·분광 | proper-time clock 모델, 동일 transition에 대한 endpoint frequency ratio, 절편 calibration | 단순 시간좌표·왕복 사건의 순서와 calibrated redshift는 다른 입력 |
| 거리 | absolute area-distance scale, 또는 luminosity calibration과 distance duality의 적용 조건 | 미지 공통 거리 scale이 남으면 dimensionful jet은 scale orbit까지만 |
| 광학·유한 거리 | caustic-free 범위, source 대응, smoothness와 derivative/curvature 상계 | local identity만으로 실제 finite-distance certificate가 생기지 않음 |

“주어진 g”가 이미 물리 단위까지 고정되어 있다면 마지막 공통 scale nuisance를 다시 넣을 필요는 없다. 반대로 독립적인 절대 거리/clock scale 없이 causal reconstruction에서 출발하는 확장 정리에는 아래 quotient를 반영해야 한다. **임의 가속도를 허용한 source worldline들은 EPS의 freely falling test particles가 아니다.** 이 source 궤적들을 projective geodesic 자료로 대체하면 별도의 물질 가정을 추가하는 것이다.

## 4. 표준 척도 보조명제: 절편은 보존되고 slope는 재척도화된다

양의 상수 λ에 대해 같은 manifold에서

\[
g_\lambda=\lambda^2g,\quad
u_\lambda=\lambda^{-1}u,\quad
o_\lambda=\lambda^{-1}o,\quad
n_\lambda=\lambda^{-1}n,\quad
K_\lambda=\lambda^{-1}K
\]

로 둔다. u,o는 g-unit이고, K=−o+n, g(K,o)=1이다. 상수 scale이므로 Levi-Civita connection은 같다. 같은 null 곡선의 observer-normalized affine 길이는 rλ=λr이다. 따라서

\[
I_\lambda(n)=g_\lambda(K_\lambda,u_\lambda)=g(K,u)=I(n),
\quad Z_{0,\lambda}=Z_0,
\quad \beta_\lambda=\beta.
\]

여기서 I=Z0=m+b·n이며 **절편은 바뀌지 않는다**. 상수 conformal scale이 절편과 상대속도를 동시에 비식별적으로 만든다는 주장은 옳지 않다. 광선의 양 끝 frequency ratio도 같은 공통 scale에서는 보존된다. solid angle은 그대로이고 area는 λ²배이므로

\[
D_{A,\lambda}=\lambda D_A,\qquad
D_{L,\lambda}=\lambda D_L,\qquad
H_\lambda(n):=c\frac{\partial z}{\partial D_{A,\lambda}}\Big|_0
=\lambda^{-1}H(n).
\]

`B_ab=∇_(a U_b)`인 기존 rate tensor는 같은 좌표 covariant 성분으로 Bλ=λB이다. 그러나 orthonormal tetrad가 λ⁻¹배이므로 **측정 tetrad 성분은 Bλ_αβ=λ⁻¹B_αβ**다. 마찬가지로 θ,σ의 tetrad rate와 물리적 가속도 크기는 λ⁻¹배다. 가속도 vector의 같은 좌표 성분은 Aλ^a=λ⁻²A^a이며, norm은 |Aλ|=λ⁻¹|A|이다. 좌표 성분 scaling과 측정 성분 scaling을 혼용하지 않는다.

어떤 coefficient Kc 또는 M2가 `d²z/dr²` 또는 `d²z/dD_A²`의 상계로 정의되었다면 그 상계는 λ⁻²배가 된다. 일반적으로 p차 거리 미분은 λ⁻p배이다. 별도 정의의 기호에 이 규칙을 무조건 적용하지 않는다. 예컨대 |R_z|≤M2 r²/2는 M2λ=λ⁻²M2, rλ=λr에서 같은 dimensionless 오차를 준다.

따라서 관측에 거리 scale만 미지라면 scale-covariant reconstruction이 맞는 목표다. β와 정규화된 방향 비율은 유지되지만, 절대 H·전단·|A|를 유일한 수치로 복원할 수 없다. A=0 여부는 **이 상수 scale family 안에서는** 불변이다. λ에 상계가 없다면 A≠0인 한 orbit에도 |Aλ|→0이므로 단순 null 배제에서 보정 독립적인 양의 절대 하한이 나오지는 않는다. 알려진 비영(非零) 절대 길이 또는 동등한 calibrated clock/거리 측정 하나가 공통 scale을 고정할 수 있지만, 모든 calibration nuisance가 자동 해결된다는 뜻은 아니다.

이것은 표준 단위·등각 scaling의 귀결이며 신규성 후보로 승격하지 않는다. distance-modulus nuisance를 쓰는 경우 D_A→λD_A와 compensating zero point의 동시 변환 여부를 해당 관측모형에서 따로 검사해야 한다.

## 5. 더 큰 등각 자유도는 geodesicity도 보존하지 않는다

상수 family를 일반 conformal class 전체로 확대해선 안 된다. g'=e^{2φ}g, U'=e^{-φ}U, U²=−c²이면 connection 변환을 직접 대입하여

\[
A'^a=e^{-2\phi}\bigl(A^a+c^2h^{ab}\nabla_b\phi\bigr),
\qquad h^{ab}=g^{ab}+U^aU^b/c^2
\]

를 얻는다. φ(p)=0이어도 공간 gradient를 바꾸면 p의 가속도가 달라지며 null cones와 무매개 light paths는 보존된다. 따라서 **인과/등각류만 주어진 문제에서는 A=0도 고정되지 않는다**. 표준 connection 변환식에서 나오는 별도 negative control이다.

이 family는 기존 관측자료 전체를 보존하는 반례가 아니다. 같은 eikonal covector를 대응시키면 ν'=e^{-φ}ν이므로

\[
1+z'=e^{\phi_o-\phi_e}(1+z).
\]

일반 φ에서는 finite-distance spectrum과 거리 slope가 달라진다. “빛 경로가 같다”를 “calibrated redshift–distance data가 같다”로 바꾸는 오류를 막는 데 이 예를 사용한다. 이 변화는 fixed-g inverse의 반증이 아니다.

## 6. 동기화·basis boost·물리적 tilt의 분리와 검증 항목

`t'=t+σ(x)`라는 좌표 변경에서 같은 g,u,o,k를 tensor 법칙으로 변환하면 endpoint redshift, area distance, −g(u,o)는 그대로다. 이 동기화 변경은 물리적인 CMB/matter tilt를 제거하지 않는다. 한 사건에서 tetrad 성분만 Lorentz 변환하는 경우도 같은 scalar 관측은 불변이다. 반면 **실제 observer o를 다른 unit timelike vector로 교체**하면 energy, sky direction과 aberration이 변한다. 이때가 Maartens의 observer dependence다. 한 사건의 o만으로 observer의 가속도·와도 같은 congruence derivative는 정해지지 않는다.

다음은 이번 책의 사용으로 추가되는 실제 검증 계약이다. 이번 addendum에서는 아래 covariance를 대수적으로 확인했으며 대규모 수치 suite는 돌리지 않았다.

| ID | 변환/자료 | 요구 결과 |
|---|---|---|
| AB-T1 | λ>0 상수 scale | I,β 불변; D→λD,H→H/λ; tetrad B→B/λ |
| AB-T2 | 동일 scale의 Taylor certificate | M2→M2/λ²로 바꿀 때 dimensionless 잔차 상계 불변 |
| AB-T3 | 공간 gradient가 있는 φ, φ(p)=0 | null paths 동일이어도 A'−A=c²h∇φ 가능; finite-distance z는 보존 요구하지 않음 |
| AB-T4 | 같은 물리적 관측을 synchronization diffeomorphism으로 표현 | scalar redshift·distance·relative rapidity 불변 |
| AB-T5 | physical observer o→o' | I와 angular energy pattern이 boost 법칙에 따라 변함; 이를 synchronization nuisance로 지우지 않음 |
| AB-T6 | 입력에 metric representative/거리 scale 미제공 | absolute dimensionful jet의 고유값 반환을 완료로 인정하지 않고 scale quotient 또는 미해결 scale을 명시 |

이 가정·검증 계약은 기존 심사 파일을 덮어쓰지 않고 추가 문서로 남긴다. 이전 REPORT_KO.md와 inputs/C.md의 작업 전후 SHA-256은 `ADDITIONAL_REFERENCE_MAP.json`에 보존했다. 최종 채택·우선권 판정은 하지 않는다.
