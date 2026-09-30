# Bianchi 식별의 광학·cosmography 경로: 독립 조사

작성일: 2026-09-29. 실제 관측자료를 적합하지 않았다. 아래의 새 명제는 문헌의 관측식에서 독립적으로 유도한 것으로, 문헌의 Bianchi 분류 정리라고 주장하지 않는다. 단위는 별도 표시가 없으면 c=1, 계량 부호는 −+++이다.

## 1. 먼저 수정해야 할 판정

`외부 Boltzmann solver 없음 → kinematics 식별 불가능`은 지나치게 강하다. 국소 distance–redshift slope와 충분히 잘 보정된 position drift는 합쳐서 선택한 매끄러운 시간꼴 congruence의 θ, σ, ω에 접근할 수 있다. 일반 congruence의 가속도는 distance–redshift dipole 및 보정된 observer motion과 함께 다룬다. 그러나 `선택한 congruence의 kinematics 복원 → Bianchi Lie algebra 유일 결정`은 성립하지 않는다. 관측식에 구조상수 자체가 등장하는 정도와 그것을 다른 곡률·운동학 변수로부터 분리할 수 있는 정도가 별개의 문제이다.

이번에 찾은 가장 직접적인 문헌은 Heinesen–Korzyński (2024)의 position-drift cosmography이다. 기존 scalar MES 접근보다 높은 관측적 상한을 제공하지만, 자료의 식별성·프레임 보정과 Bianchi subgroup ambiguity를 제거하지 않는다.

## 2. 원문 열람 범위와 핵심 근거

| 출처 | 실제 열람 | 이번 작업에 필요한 내용 | 제한 |
|---|---|---|---|
| A. Heinesen, *Multipole decomposition of the general luminosity distance Hubble law*, arXiv:2010.06534v2, JCAP 2021(05)008. https://arxiv.org/pdf/2010.06534 | PDF 23쪽 텍스트; §2 식(2.11), §5 가정·boost, 부록의 위치 확인 | H(e)=θ/3−a·e+σ:ee; redshift coordinate invertibility 및 regularity | 높은 차수 식은 2024 errata 적용 필요. 9/25/61이라는 숫자를 독립적인 Lie-type 정보 수로 읽으면 안 됨 |
| A. Heinesen, *Redshift drift cosmography for model-independent cosmological inference*, arXiv:2107.08674, PRD 104,123527 (2021). https://arxiv.org/pdf/2107.08674 | PDF 10쪽 텍스트; 식(9)–(10), 자유도 설명, 결론 | redshift drift가 position drift와 결합되는 kinematic/curvature 조합에 의존 | 원문 식(10),(17) anisotropic Ricci 부호에 후속 errata 있음 |
| A. Heinesen & M. Korzyński, *Exploring the rich geometrical information in cosmic drift signals with covariant cosmography*, arXiv:2406.06167v1; PRD 110,043525 (2024). https://arxiv.org/pdf/2406.06167 | PDF 14쪽 텍스트; §II, 식(9)–(12), §VII, §IX, Appendix E. arXiv abstract version history도 조회 | geodesic congruence의 leading drift: κ=P(σ+ω)e; poloidal quadrupole와 toroidal dipole; redshift drift의 곡률 조합 | 일반 가속도는 본문의 단순화에서 제외. 아래 §7의 부호 충돌을 해결하기 전 고차식을 그대로 계승하지 않을 것 |
| M. Fontanini, M. Trodden & E. J. West, *Can Cosmic Parallax Distinguish Between Anisotropic Cosmologies?*, arXiv:0905.3727; PRD 80,123515 (2009). https://arxiv.org/pdf/0905.3727 | PDF 24쪽 텍스트; 서론, §IV 계산 방식, §V 결론 | Bianchi I의 특정 LRS 모형과 off-centre LTB의 drift를 비교; 제한된 dynamics 아래 신호 크기가 작음 | 이 논문의 작은 신호 수치를 모든 Bianchi 또는 모든 anisotropic stress 모형의 보편 no-go로 승격할 수 없음. 논문 자체는 null-geodesic 수치 적분 사용 |
| Gaia Collaboration, *Gaia EDR3: The celestial reference frame (Gaia-CRF3)*, A&A 667,A148 (2022), DOI 10.1051/0004-6361/202243483. https://doi.org/10.1051/0004-6361/202243483 | 공식 출판사 검색 발췌(원문 직접 열람 시 403, arXiv PDF fetch 실패) | quasar proper motion으로 astrometric frame spin을 결정한다는 설명 | 원문 전체를 읽었다고 표시하지 않음. 아래 frame-spin 퇴화 자체는 독립 대수 명제 |

위 2024 논문의 상세 공식·가정 요약은 본문에서 필요한 만큼만 사용했다. 해당 논문의 원문 자체를 배포하지 않는다. 웹 검색 ref: 2010 논문 turn66view0; 2021 논문 turn66view1; 2024 논문 turn69view0/turn73view1/turn73view2; 2009 논문 turn80view0; Gaia 공식 결과 turn80search2. 루트 응답에서 웹 citation을 쓰려면 루트가 해당 URL을 다시 열어야 한다.

## 3. 명제 O1: 거리 slope가 보는 9개 성분과 직접 보지 못하는 ω

공통 source/observer congruence u, k=E(u−e), e·u=0, e·e=1를 택한다. null geodesic을 따라

\[
\frac{dE}{d\lambda}=-E^2\mathcal H(e),\qquad
\mathcal H(e)=\frac\theta3-a_i e_i+\sigma_{ij}e_i e_j.
\]

반대칭 항은 e_i e_j ω_ij=0 때문에 소거된다. 이 때문에 선형 distance–redshift slope 단독으로 ω를 직접 복원하는 것은 불가능하다. 이것은 고차 distance 계수 또는 다른 관측량에서 ω가 영원히 보이지 않는다는 뜻은 아니다.

독립 복원식: ⟨·⟩를 전천 균등각 평균으로 두면

\[
\theta=3\langle\mathcal H\rangle,\quad
a_i=-3\langle\mathcal H e_i\rangle,\quad
\sigma_{ij}=\frac{15}{2}\langle\mathcal H(e_i e_j-\delta_{ij}/3)\rangle.
\]

이는 ⟨e_i e_j⟩=δ_ij/3, ⟨e_i e_j e_k e_l⟩=(δ_ijδ_kl+δ_ikδ_jl+δ_ilδ_jk)/15에서 바로 따른다. 실제로는 d_L의 slope가 1/H이므로 `d_L의 multipoles = H의 multipoles`라고 대치하면 안 된다. H를 포함한 forward regression을 사용하고 covariance와 distance calibration을 함께 추정해야 한다. 마스크 하에서는 전천 적분식 대신 같은 텐서 basis의 design matrix를 사용한다.

## 4. 명제 O2: geodesic position-drift의 명시적 shear/vorticity 역산

가정: (i) 관측자와 source가 같은 매끄러운 geodesic congruence에 속함, (ii) 관측자 triad가 Fermi–Walker transport 기준으로 보정됨, (iii) 충분히 가까운 source의 drift에서 거리 0차 계수 κ_0(e)를 분리할 수 있음, (iv) 전천 함수를 정확히 알거나 실제 design rank가 충분함.

S=σ는 symmetric tracefree, W=ω는 antisymmetric로 두고 P_e=I−eeᵀ라 하면 문헌의 leading 식은

\[
\kappa_0(e)=P_e(S+W)e.
\]

여기서 아래 역산과 안정성은 본 작업의 직접 계산이다. M=⟨κ_0(e)eᵀ⟩라 두면

\[
M=\frac15S+\frac13W,\qquad
S=5\operatorname{sym}M,\quad W=3\operatorname{anti}M.
\]

증명: A=S+W로 두면 tr A=0이고

\[
M_{ij}=\frac13 A_{ij}-\frac1{15}(A_{ij}+A_{ji}+\operatorname{tr}(A)\delta_{ij}).
\]

대칭·반대칭 부분을 나누면 결과가 따른다. 특히 `κ_0=0 on S² → S=W=0`이다. 동치로 P_eAe=0이면 모든 e가 A의 고유벡터이므로 A는 scalar matrix이고 tracefree 조건에 의해 0이다.

또한 L²(S²)의 정규화 평균 norm에서

\[
\langle|\kappa_0|^2\rangle=\frac15\|S\|_F^2+\frac13\|W\|_F^2.
\]

증명은 |Ae|²−(eᵀSe)²의 평균을 계산하면 된다. 따라서 이 이상적인 연산자는 두 부분 모두에 양의 singular values를 가지며, scalar power로 압축하면 사라지는 S/W 분리를 vector morphology가 보존한다. 이 식만으로 특정 Bianchi type을 정하지 못한다.

## 5. 명제 O3: frame-spin과 physical vorticity의 정확한 퇴화

unknown frame rotation이 drift에 Ωe를 더한다고 하자. Ω는 임의의 antisymmetric matrix이다. Ωe는 이미 e에 수직이므로

\[
\kappa_{obs}=P_e(S+W)e+\Omega e=P_e\{S+(W+\Omega)\}e.
\]

따라서 같은 sky geometry와 selection 아래 관측만으로는 W와 Ω를 분리할 수 없다. noise full law도 같고 Ω가 자유 nuisance이면 (W,Ω)→(W+Δ,Ω−Δ)가 정확한 likelihood fibre이다. 전천 shape를 모두 보존해도 이 퇴화는 남는다. 외부 회전 기준 또는 Ω prior/물리적 제약을 명시해야 한다.

또 다른 독립 결과: 상대 각도만 쓰는 pairwise cosmic parallax는 공통 rigid rotation을 제거한다. e₁,e₂에 대해 (Ωe₁)·e₂+e₁·(Ωe₂)=0이므로 leading W 자체도 이 관측에서 없어질 수 있다. 따라서 `절대 방향 drift`와 `두 source 사이 각거리 변화`는 와도 식별성에서 다른 데이터이다. 이는 old cosmic-parallax no-go를 재해석할 때 특히 중요하다.

Gaia reference frame은 quasars의 spin 조건으로 정의되어 있으므로 toroidal ℓ=1 결과를 물리적 우주 와도의 절대 상한으로 곧바로 해석하면 안 된다. publication의 frame calibration operator와 실제 분석 sample의 overlap을 확인해야 한다. 전천 공통 spin에는 위 대수적 퇴화가 있고, redshift별 변화·종별 차이는 추가 정보를 줄 수 있지만 이를 자동으로 absolute W로 승격하지 않는다.

## 6. 곡률까지의 연결과 끊기는 지점

1. 일반 distance cosmography의 방향별 유효 curvature parameter는 FLRW 공간곡률 scalar 또는 Bianchi 구조상수의 직접 측정값이 아니다.
2. geodesic 근사와 이미 알려진 S,W 아래 leading redshift drift의 monopole·quadrupole는 R_uu 및 electric Weyl와 STF spatial Ricci의 조합을 제약할 수 있다. 이것이 모든 Riemann 성분이나 곡률 jet의 복원을 뜻하지 않는다.
3. null optical tidal matrix 자체도 scalar-curvature 방향을 직접 보지 못한다. 독립 확인: R_abcd에 K(g_ac g_bd−g_ad g_bc)를 더하면 screen vectors s_A,s_B와 null k의 contraction s_A^a k^b s_B^c k^d는 0이다. 여러 방향을 더해도 이 algebraic kernel은 남는다. 실제 weak lensing은 더 나아가 line-of-sight 적분·source distribution·mass-sheet류 퇴화를 가진다.
4. optical screen shear는 null congruence의 2차원 변형량이고, σ_ab는 matter/reference congruence의 3차원 변형량이다. 둘을 MES 분모가 같다는 이유로 같은 변수로 넣으면 안 된다.
5. Bianchi 판정은 spacelike homogeneous orbits의 Lie algebra에 관한 것이다. ω(u)≠0이면 u의 rest spaces를 hypersurfaces로 동일시할 수 없다. normal n과 matter u의 tilt field를 정의한 뒤 Gauss/Codazzi constraints와 관측 projection을 연결해야 한다.
6. local boost는 한 사건에서의 observer u 교체이다. global tilt는 n에 대한 u(x)의 공간시간장 및 그 derivatives를 지정한다. 한 점의 β를 아는 것만으로 ∇u 또는 homogeneous spatial structure가 결정되지 않는다. 여러 redshift bins는 β(z), derivatives 또는 tensor transports에 추가 제약을 줄 수 있지만 새 response directions가 실제 생성되는지를 확인해야 한다.

## 7. 고차식 계승 시 발견한 errata gate

2024 논문 §VII는 다음 오류를 명시한다.

- 2010.06534 식(2.7)의 STF Ricci 항 `−1/2 R_<μν>`는 `+1/2 R_<μν>`여야 하며 식(B.2)에도 전파된다.
- 2107.08674 식(10),(17)의 대응 Ricci 항에도 같은 수정이 필요하다.
- 2010.06534 식(4.3)의 acceleration–vorticity 항도 수정한다고 쓰여 있다.

하지만 마지막 항에는 출처 자체의 정합성 문제가 남는다. 열람한 2406.06167v1 §VII에서는 +a^νω_μν→−a^νω_μν라고 쓰지만, 같은 PDF 식(29)의 추출식에는 다시 +a^νω_μν가 보인다. 따라서 해당 고차 항은 여기서 해결했다고 표시하지 않는다. 출판사 최종 PDF·고유 convention·xAct 직접 유도를 대조하는 좁은 local task가 필요하다. 위 O1–O3는 이 disputed 항을 사용하지 않는다.

독립 손계산으로는 errata의 음수가 지지된다. 해당 논문의 convention에서

\[
E^{-1}\frac{de^\mu}{d\lambda}=(e^\mu-u^\mu)\mathcal H-e^\nu(\theta h^\mu{}_\nu/3+\sigma^\mu{}_\nu+\omega^\mu{}_\nu)+a^\mu.
\]

따라서 E^−1dH/dλ의 −d(a·e)/dλ 항에서 나오는 와도 기여는 +a_μe^νω^μ_ν=−e^μa^νω_μν이다. 다른 항에는 방향의 1차 와도항이 없으므로 dipole에는 −a^νω_μν가 남는다. 이것은 일관된 convention 아래의 직접 대수 유도이며, 출판본·독립 xAct 재현을 대체하지 않는다. 구현 상속의 상태는 `손유도 음수 지지; 독립 계산 검증 대기`로 둔다.

## 8. 명제 O4: solver 없이 가능한 보장된 유형 배제 집합

각 Bianchi label t에 대해 현재 선택한 가정 A를 만족하는 실제 spacetime/congruence/nuisance 집합을 Θ_t라 한다. 관측 특징 f(θ)는 같은 관측조건, source selection, boost와 frame response를 통과한 tensor feature이다. Θ_t의 가능한 feature 집합 M_t={f(θ):θ∈Θ_t}를 완전히 계산하지 못하면 이를 포함하는 outer set M_t^out을 쓴다. 고차 redshift remainder 및 systematic error가 집합 B 안에 있다고 가정한다.

유효한 (1−α) simultaneous confidence region C(Y)가 실제 feature를 덮는다고 하자. 정의

\[
\widehat{\mathcal T}(Y)=\{t:C(Y)\cap(M_t^{out}\oplus B)\ne\varnothing\}.
\]

그러면 실제 모형이 label t_*를 갖고 가정이 성립할 때

\[
\Pr_{\theta_*}\{t_*\in\widehat{\mathcal T}(Y)\}\ge1-\alpha.
\]

증명: confidence event에서는 true feature가 C(Y)에도 실제 type prediction tube에도 들어간다. 모든 true admissible group representations가 동일 관측 feature를 공유하면 같은 event에서 그 label들이 동시에 보존된다. 별도의 type별 multiple-testing correction을 무작정 누적하는 대신 하나의 공통 feature confidence event를 쓰는 방식이다.

배제는 C(Y)와 outer prediction tube가 **불교집합임을 증명**했을 때만 한다. 단순 optimizer가 교집합을 찾지 못했다는 사실은 배제 증명이 아니다. 교집합이 남는 것은 필요조건 통과이며 실제 spacetime realization, posterior probability 또는 유일 식별을 보증하지 않는다. 최적화는 covariance/response가 확정된 공통 관측공간에서 수행한다.

MES 허용체 gauge γ_B는 공통 scale/shape normalization으로 쓸 수 있다. 그러나 가역 재표현은 기존 observational equivalence를 분리하지 않으며, 1−γ 또는 scalar maximum 비율로 다시 축약하면 morphology가 사라진다. γ≤1은 주어진 허용체와 사상의 전제에서 의미를 갖는 적합성 척도이지 Bianchi posterior가 아니다.

## 9. redshift jet의 오차와 계산 경계

Taylor 계수 존재와 유한 redshift interval에서의 정확도는 구분한다. q차 jet을 사용하려면 각 관측·방향에 대해 remainder R_q(z,e)를 통제해야 한다. 충분한 조건의 한 예는 0≤z≤z_max에서 |∂_z^(q+1)f|≤M(e)이며, 이 경우 |R_q|≤M(e)z^(q+1)/(q+1)!이다. 이 derivative bound는 cosmography가 자동으로 제공하지 않는다.

H(e)=0인 방향·ray, caustic, multi-stream coarse graining, calibration transition에서는 단일 z 전개를 강제하지 않는다. 더 높은 z를 쓰려면 piecewise expansions, analytic ray expressions 또는 선언된 optical evolution이 필요하며, 여기서는 그 계산을 실행하지 않았다. CMB last-scattering까지 낮은 z Taylor polynomial을 외삽해서 Bianchi likelihood를 만드는 것은 현재 명제로 정당화되지 않는다.

## 10. 이번 루프에서 제안하는 구체적 우선순위

1. 관측적 목표를 θ/σ/a의 distance multipoles와 σ/ω의 vector drift로 분리하고 공통 tensor feature와 calibration nuisance를 정의한다.
2. O2의 inverse·norm 항등식과 O3 frame kernel을 Wolfram으로 재현하고, 동일 법칙 fibre를 넣은 synthetic recovery에서 absolute ω가 잘못 식별되지 않게 확인한다.
3. 소유 자료 중 Union3/peculiar velocity 등은 낮은 z expansion morphology에 먼저 연결한다. Gaia/quasar proper motion은 별도 DR3 download/adapter task로 연결하되 frame-spin을 명시한다. 현재 redshift-drift 측정을 보유한다고 가정하지 않는다.
4. 각 type의 Lie/Jacobi/Gauss/Codazzi 필요조건을 finite-jet semialgebraic outer sets로 변환한다. local Wolfram·Singular가 feasibility와 certified emptiness를 처리하고, 필요하면 Lean으로 O4의 set inclusion/coverage argument를 정식화한다.
5. 고차 drift curvature terms를 추가하기 전에 §7의 errata와 convention 문제를 해결한다. 최종 출력은 `살아남은 유형 집합`, `배제된 유형+증명서`, `관측으로 분리할 수 없는 표현들의 집합`이다.

이 우선순위에는 외부 Boltzmann solver도 CMB transfer-function 계산도 필요하지 않다. 반면 실제 CMB 온도·편광 likelihood 전체 또는 특정 Bianchi의 열적 history 예측을 완성했다는 주장은 포함하지 않는다.
