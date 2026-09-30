# 외부 Boltzmann solver 없는 Bianchi 우주 식별의 범위

2026-09-29 UTC / 2026-09-30 KST · 이론 연구루프

## 1. 재탐색의 결론

**Bianchi 식별 전체를 불가능으로 묶을 이유는 없다. 기하학적 유형 복원, 관측에 의한 조건부 유형 배제, 남는 유형 집합의 추정은 각각 가능성을 연구할 수 있다.** 반면 모든 허용 상태에 유일한 Bianchi label을 부여하는 관측 분류기는 존재하지 않는다. 동일한 시공간에 서로 다른 simply-transitive 군작용이 존재하기 때문이다.

보존된 선행 문서를 다시 읽은 결과, 기존 판정은 보편적인 Bianchi 분류 불가능 정리가 아니었다. 당시 반응함수와 입력으로 family identification을 승인하지 않는다는 제한, 특정 동일 관측법칙 반례, 순간 정보의 미분 결손이 핵심이었다. 이번 결과는 이를 폐기하지 않고 별도의 기하 입력과 식별 논증을 추가한다. 원문 위치는 prior_audit.md에 있다.

이번에는 기존 연구의 보존 문서와 당시 고정된 코드 조사본을 이용했다. 최신 원격 main 전체 감사나 전체 코드 정독을 새로 수행한 것은 아니다. 이전 I2 DEFENDED_CONDITIONAL, I3 HOLD_INPUT_INCOMPLETE는 유지한다. 실제 관측자료의 우주 유형 판정은 실행하지 않았다.

독립 reviewer는 아래 BIC-01–06 및 BIC-03b의 **7개 조건부 이론 명제**를 후속 연구·형식화에 사용할 수 있다고 판정했다. BIC-07 관측 재구성은 HOLD, BIC-08 실제 분석은 NOT_RUN/HOLD다. PROMOTE는 새 발견의 우선권이나 실자료 과학 판정을 뜻하지 않는다.

## 2. 식별 대상과 계산 범위

국소 시공간 기하, 선택한 spacelike foliation 위의 3차원 군작용, 실제 관측법칙으로 구별되는 모형은 서로 다른 대상이다. Bianchi label은 주로 simply-transitive 군작용의 Lie 대수를 분류한다. 공간 slice의 대칭이 시간에 따른 metric, extrinsic curvature와 필요한 물질장까지 보존하는지는 별도 조건이다. 임의 tetrad의 anholonomy는 그 자체로 Bianchi 구조상수가 아니다. 국소 분류는 전역 topology를 결정하지 않는다.

이번 계산은 직접 대수 유도, 원 문헌의 기하·광학 정리, Wolfram 기호 검산이다. Boltzmann 코드, 수치 ODE/PDE evolution, 실제 자료 likelihood 적합은 실행하지 않았다. 대수 제약·명시적 해·국소 광학 전개와 오차집합으로 다음 연구를 이어갈 수 있다.

Convention: signature \((-+++)\), 물리적 4-속도 \(u^a u_a=-c^2\). \(\theta,\sigma,\omega\)는 시간의 역수, \(A^a=u^b\nabla_bu^a\)는 가속도다. Homogeneous slice의 normal \(N\)과 source congruence \(u\)는 다를 수 있다. \(\omega(u)\ne0\)이면 그 rest spaces를 hypersurface로 동일시할 수 없다.

## 3. BIC-01: 비영 shear에서도 I형과 VII₀형이 겹친다

양의 매끄러운 \(A(t),B(t)\)에 대해
\[
 ds^2=-c^2dt^2+A(t)^2(dx^2+dy^2)+B(t)^2dz^2
\]
를 생각한다. 세 translation은 I형이다. 동시에 \(q\ne0\)에 대해
\[
 K_1=\partial_x,\quad K_2=\partial_y,\quad
 K_3=\partial_z+q(x\partial_y-y\partial_x)
\]
도 Killing 벡터이고
\[
 [K_3,K_1]=-qK_2,\quad [K_3,K_2]=qK_1,\quad [K_1,K_2]=0
\]
이다. 공간 성분 determinant는 1이므로 국소 simply-transitive VII₀ 작용을 얻는다. 두 작용은 동일 metric과 normal congruence를 보존한다. 그 shear는
\[
 \sigma_{ab}\sigma^{ab}
 =\frac23(H_A-H_B)^2,\quad H_A=\dot A/A,\quad H_B=\dot B/B.
\]
따라서 isotropic limit에만 있는 퇴화가 아니다.

관측적 반례에서는 **동일한 완전 물리상태가 양쪽 label domain에 모두 허용**되어야 한다. 예컨대 정상 congruence와 두 작용에 invariant한 source·복사·경계자료를 함께 택한다. 같은 metric만 두고 서로 다른 물질/초기조건을 몰래 바꾸면 동일법칙 결론을 쓸 수 없다. 이 admissibility 조건을 만족하는 쌍에서는 label 선택만으로 관측법칙이 달라지지 않는다.

Wolfram에서 Killing 조건, bracket, determinant, coframe metric과 shear contraction을 확인했다. 모든 I형과 VII₀형이 동등하다는 주장이 아니다. 대칭이 증가한 영역에서는 허용 action 집합이 정답이며, generic branch의 구별 가능성은 남는다.

## 4. BIC-02: 공간곡률 부호에 의한 조건부 배제

Simply-transitive \(G_3\)가 작용하는 spacelike homogeneous orbit의 정규직교 invariant frame에서
\[
 C^i{}_{jk}=\epsilon_{jk\ell}n^{\ell i}
 +a_j\delta^i_k-a_k\delta^i_j,\quad n=n^\top,\quad na=0
\]
로 쓴다. 마지막 식은 Jacobi 조건이다. \(n,a\)는 길이의 역수 차원이다. \(n\)을 대각화하면 Koszul 공식으로
\[
 {}^3R=-6|a|^2-\frac12(n_1^2+n_2^2+n_3^2)
       +n_1n_2+n_2n_3+n_3n_1. \tag{1}
\]
Class B에서는 \(a=(a,0,0)\), \(n_1=0\)를 택하여
\({}^3R=-6a^2-(n_2-n_3)^2/2<0\)를 얻는다. Class A의 rank 0,1,2인 경우도 nonpositive다. VIII에서는 \(n_1,n_2>0,n_3<0\)로 두면
\[
 {}^3R=-\frac12(n_1-n_2)^2-\frac12n_3^2+n_3(n_1+n_2)<0.
\]
그러므로
\[
 \boxed{{}^3R>0\Longrightarrow\mathrm{Bianchi\ IX}}
 \quad\text{(위 homogeneous-orbit 가정 아래).} \tag{2}
\]
알려진 기하학적 결과이며 Wald (1983), p.2119, 식 (15)–(16)이 문헌 근거다. 이번에는 다항식 배제 인증서로 쓰도록 다시 유도했다. No-hair 정리의 에너지 조건은 식 (2) 자체의 필수 가정이 아니다.

역은 거짓이다. IX인 \(n=(1,1,5)\)는 \({}^3R=-5/2\)를 준다. \({}^3R=0\)도 I형을 유일하게 정하지 않는다. Kantowski–Sachs 등 assumed \(G_3\) 밖의 공간이나 임의 회전 congruence의 rest curvature에는 이 판정을 적용하지 않는다.

Wolfram으로 연결과 곡률을 직접 구성하여 식 (1), Jacobi residual, Class B 식, VIII 부호 및 IX 반례를 검산했다.

Einstein 방정식과 결합하는 연결은 Hamiltonian constraint다. \(\epsilon_N=T_{ab}N^aN^b/c^2\), \(\Sigma_N^2=\sigma^{(N)}_{ab}\sigma_{(N)}^{ab}\)로 정의하면
\[
 {}^3R=\frac{16\pi G}{c^4}\epsilon_N+2\Lambda
 -\frac{2\theta_N^2}{3c^2}+\frac{\Sigma_N^2}{c^2}. \tag{3}
\]
이는 energy-density convention이며 \(\Sigma_N^2\)에 \(1/2\)를 넣지 않았다. 모든 항을 같은 상태·normal에서 평가해야 한다. Tilted source의 \(\theta,\sigma,\epsilon\)를 그대로 대입할 수 없다. 공동 신뢰집합 전체에서 식 (3)의 하한이 양수라면 조건부 non-IX 배제가 가능하다. FLRW distance law 아래의 단일 \(\Omega_k\)를 이 일반 공간곡률로 대체하지 않는다.

## 5. BIC-03/03b: 불변 텐서와 공간미분으로 Lie 대수 복원

이미 국소 공간동질성이 성립하는 열린 영역에서 \(h\)와 spatial symmetric tensor \(T\)를 **함께 보존하는 유효한 국소 추이적 \(G_3\)**를 가정한다. \(T\)의 세 고윳값 \(\lambda_i\)가 모두 다르다고 하자.

정렬된 정규직교 eigenframe \(e_i\)는 connected symmetry에 invariant다. 남는 부호·순열은 대수의 동형류를 바꾸지 않는다. 동질성 때문에 고윳값은 공간적으로 일정하다. \(D_{e_k}e_i=\Gamma^j{}_{ki}e_j\)이면
\[
 (D_kT)_{ij}=(\lambda_i-\lambda_j)\Gamma^j{}_{ki},
 \quad i\ne j,\qquad \Gamma^i{}_{ki}=0.
\]
따라서
\[
 \boxed{\Gamma^j{}_{ki}=\frac{(D_kT)_{ij}}{\lambda_i-\lambda_j},
 \qquad C^j{}_{ki}=\Gamma^j{}_{ki}-\Gamma^j{}_{ik}.} \tag{4}
\]
모든 연결계수와 구조상수를 얻는다. 이 frame은 일반적으로 Killing frame 자체가 아니라 reciprocal invariant frame이다. 반대 Lie 대수가 나오는 convention 차이는 전체 부호 변경으로 동형이므로 Bianchi 유형은 같다. Simple spectrum은 \(h,T\)를 보존하는 continuous isotropy를 제거하므로 해당 connected symmetry algebra는 3차원이다.

| 선택한 \(T\) | 충분한 입력 | 결과 | 제한 |
|---|---|---|---|
| 공간 Ricci | \(h,\mathrm{Ric}(h),D\mathrm{Ric}(h)\) | generic homogeneous 공간의 Lie 유형; 공간 metric 3-jet 충분 | 반복 고윳값 branch 제외 |
| normal shear 또는 tracefree extrinsic curvature | \(h,T,DT\) | 이들을 함께 보존하는 \(G_3\)의 유형 | normal/source 변환과 모든 공간미분 필요 |

특히 simple \(T\)이고 \(DT=0\)이면 \(\Gamma=C=0\)이므로 I형이다. LRS I/VII₀ 반례는 Ricci도 normal shear도 반복 고윳값을 가지므로 이 충분조건과 모순되지 않는다.

Ricci 선택은 Ferrando–Sáez (2020), §§4–5의 intrinsic classification과 연결된다. 여기서는 eigenframe의 직접 유도를 제시했다. Wolfram의 비퇴화 예 \(n=(1,2,4)\)에서는 \(\mathrm{Ric}=\mathrm{diag}(-3/2,-5/2,15/2)\)이며 연결과 bracket 복원이 정확히 일치했다. 일반 정리의 근거는 위 증명이고 예제 검산은 보조 근거다.

식 (4)는 임의 한 점의 유한 jet로 동질성을 증명하지 않는다. 동질성을 가정한 영역의 대수를 복원한다. 시공간 유형을 말하려면 동일 작용이 시간에 따른 기하도 보존해야 한다. \(\delta_T=\min_{i\ne j}|\lambda_i-\lambda_j|\to0\)이면 역산이 불안정하다. Weak anisotropy에서 정확한 generic 식별성과 유한 오차의 통계적 식별성은 다르며, 경계 부근에는 유형 집합을 유지해야 한다.

Sáez–Mengual–Ferrando (2024)는 perfect-fluid metric의 Ricci/Weyl와 미분을 이용하는 더 넓은 intrinsic classification 및 xAct 예를 제시한다. 입력은 metric 기하다. 관측 tensor statistic이 그 입력 전체를 제공한다는 정리는 아니며 모든 stress 모델에 자동 적용되지 않는다.

## 6. 관측 연결: \(\theta,\sigma,A,\omega\)를 어디까지 볼 수 있는가

Source와 observer가 같은 매끄러운 congruence에 속하고 \(e\)가 observer에서 source로 향하는 단위방향이면
\[
 \mathcal H(e)=\frac{\theta}{3}-\frac{A_ie_i}{c}
 +\sigma_{ij}e_ie_j,\qquad
 d_L(z,e)=\frac{cz}{\mathcal H(e)}+O(z^2). \tag{5}
\]
\(\mathcal H\ne0\)인 정칙 방향에서 사용하는 국소 식이다. 전천 평균으로
\[
 \theta=3\langle\mathcal H\rangle,\quad
 A_i=-3c\langle\mathcal H e_i\rangle,\quad
 \sigma_{ij}=\frac{15}{2}
 \langle\mathcal H(e_ie_j-\delta_{ij}/3)\rangle. \tag{6}
\]
이는 구면 2차·4차 moment로 직접 따른다. 반대칭 \(\omega\)는 이 scalar slope에서 소거된다. 실제 거리 slope는 \(1/\mathcal H\)이므로 거리 multipole를 \(\mathcal H\) multipole로 대체하지 않는다.

**BIC-04.** Geodesic source/observer congruence와 보정된 Fermi–Walker frame에서 근거리 absolute-direction position drift의 0차 계수는
\[
 \kappa_0(e)=P_e(\sigma+W)e,\qquad P_e=I-ee^\top.
\]
여기서 \(W\)는 이 식에 등장하는 antisymmetric vorticity matrix convention이다. \(M=\langle\kappa_0(e)e^\top\rangle\)라 하면
\[
 M=\sigma/5+W/3,\qquad
 \boxed{\sigma=5\,\mathrm{sym}\,M,\quad W=3\,\mathrm{anti}\,M.} \tag{7}
\]
Wolfram으로 symbolic 역산 residual이 모두 0임을 확인했다. Heinesen–Korzyński (2024)의 식 (9)–(12), Appendix E를 사용하는 조건부 복원이다. 유한 거리와 임의 accelerated congruence에 이 0차식을 그대로 적용하지 않는다.

또한 \(\langle|\kappa_0|^2\rangle=\|\sigma\|_F^2/5+\|W\|_F^2/3\)이다. Scalar power는 서로 다른 shear/vorticity 조합을 겹치게 하지만 vector morphology는 이상적인 조건에서 분리한다. Tensorization의 구체적인 이득이다. 그러나 식 (7)은 식 (4)의 공간미분을 공급하지 않는다.

**BIC-05.** Unknown frame spin \(\Omega\)가 있으면
\[
 \kappa_{\rm obs}=P_e\{\sigma+(W+\Omega)\}e.
\]
자유 spin nuisance 아래 \(W\)와 \(\Omega\)는 정확히 퇴화한다. 같은 전체 noise law와 허용 상태쌍을 가정하면 full-law 동일성이다. 모든 depth에서 같은 모드를 공유하면 단순 stacking도 해결하지 못한다. 두 source 사이 각거리 변화만 쓰면 공통 rigid rotation 자체가 사라진다. Relative-angle parallax와 absolute-direction drift는 다른 실험이다.

Gaia/QSO 분석에는 실제 frame calibration, source velocity, 유한 관측기간·거리 응답, selection, cross-source covariance가 필요하다. 기존 I3 HOLD는 이 이상적 역산만으로 해제되지 않는다.

## 7. 적색편이·광학·tilt와 남는 정보

적색편이별 tensor는 서로 다른 response와 source window를 비교하게 한다. 하지만 bin 차이는 자동으로 시간·공간미분이 아니다. Transport와 공동 covariance가 필요하다. Leading redshift drift는 운동학을 알고 있을 때 \(R_{uu}\), electric Weyl와 STF spatial Ricci의 조합을 제약한다. 전체 공간 Ricci 및 그 모든 공간미분의 복원으로 승격하지 않는다.

Null optical tidal contraction에는 constant-curvature algebraic 방향이 소거되는 kernel도 있다. 이것은 projection 단계의 한계이며 모든 실제 광학 관측의 동일법칙 정리는 아니다. Sachs screen shear는 null congruence의 2차원 변형이고 normal/source shear는 3차원 운동학이다.

Local boost는 한 사건에서 observer를 바꾸는 변환이다. Global tilt는 \(u=\gamma(N+v)\), \(\beta=v/c\)라는 장과 그 미분을 요구한다. 한 점의 \(\beta\)로 \(\nabla u\) 또는 Lie 구조를 결정할 수 없다.

국소 \(z\)-전개를 유한 범위에 적용하려면 remainder가 필요하다. 예컨대
\[
 |\partial_z^{q+1}f(z,e)|\le M(e)
 \ \Longrightarrow\
 |R_q(z,e)|\le M(e)|z|^{q+1}/(q+1)!.
\]
Derivative bound는 Taylor 계수의 존재만으로 주어지지 않는다. Caustic, redshift 비단조성, source congruence 파손, coarse-graining 변경을 처리해야 한다. 낮은 \(z\) polynomial을 CMB last scattering까지 외삽하는 경로는 승인하지 않는다.

고차 cosmography에는 후속 sign errata가 있다. Heinesen–Korzyński (2024) §VII와 식 (29)의 acceleration–vorticity 항은 convention·최종판본·xAct 유도를 대조할 좁은 과제로 남겼다. 독립 손유도는 errata의 음수를 지지하지만 이번 루프에서 고차식 구현을 검증한 것은 아니다. BIC-01–06의 승격된 내용은 이 disputed 항에 의존하지 않는다.

## 8. BIC-06: MES와 tensor 통계로 보장된 부분식별

각 action label \(t\)에 대해 \(\Theta_t\)를 기하·물질·복사·프레임·경계·nuisance의 공동 허용집합으로 둔다. 같은 처리 관측공간의 실제 예측집합을 \(\mathcal M_t\), 이를 포함하는 검증된 outer set을 \(\mathcal M_t^{out}\)으로 둔다. Truncation과 systematic 허용오차도 포함한다.

전체 모형 합집합에 대해 uniform coverage \(1-\alpha\)인 공동 신뢰영역 \(\mathcal C_\alpha(Y)\)가 있으면
\[
 \widehat{\mathcal T}_\alpha(Y)
 =\{t:\mathcal C_\alpha(Y)\cap\mathcal M_t^{out}\ne\varnothing\} \tag{8}
\]
는 참 유형을 확률 \(1-\alpha\) 이상으로 보존한다. 신뢰영역이 참 feature를 덮는 사건에서는 그 feature가 참 유형의 outer image에도 들어가기 때문이다. 동일 완전 물리상태가 복수 action에 admissible하면 같은 사건에서 그 labels가 함께 보존된다.

이것은 조건부 배제의 보장이다. Nonempty intersection은 non-exclusion이며 물리적 realization이나 posterior가 아니다. Optimizer가 witness를 못 찾았다는 사실은 공집합 증명이 아니다. 하나의 보정된 공동 region과 별도 threshold들의 반복검정은 구별한다. Mean region은 covariance 차이의 식별 정보를 활용하지 못할 수 있다. Outer enclosure 자체가 확률 \(1-\beta\)로만 sound하면, 별도 의존성 가정 없이 보장은 적어도 \(1-\alpha-\beta\)로 낮아진다.

| 객체 | 이번 문제에서의 역할 | 해석 상한 |
|---|---|---|
| \(x\) | 같은 상태에서 평가한 tensor·functional 배열 | sky STF와 physical shear 구별 |
| \(Q,\gamma_B,1-\gamma_B\) | 전제에 대응하는 공동 body와 signed margin | 유형 확률·유의도 아님 |
| \(F\) | 같은 상태·방향의 support 이용률 | scalar 숫자만으로 유형 유일성 없음 |
| \(\Pi\) | 명시된 공동 law의 exceedance | law 없는 posterior 불가 |
| \(G_F\) | depth·mask·feature transport/coherence | z bin 차이와 물리 미분 구별 |

기존 PR142/scalar 계열의 동명 통계는 별도 정의로 보존한다. 가역 정규화는 정보를 보존하고 lossy scalarization은 정보를 잃을 수 있으며, 정규화는 동일 full-law 상태를 분리하지 않는다. 음의 margin은 0으로 자르지 않는다.

Quotient gauge \(\gamma_{pB}(v)=\min_{py=v}\gamma_B(y)\)는 대수 fibre의 최소 lift다. Type별 Einstein/Lie/matter 조건을 가진 physical fibre를 별도로 교차해야 한다. 비선형·유계 허용집합의 식별을 단순 rank 부족만으로 금지하지 않는다.

## 9. 보유 자료와 연결할 순서

다음은 사용자가 제시한 목록에 대한 연결안이며, 현재 파일 schema·품질을 검증한 결과는 아니다.

| 자료 | 첫 목표 | Bianchi 주장 상한 |
|---|---|---|
| Union3·JWST anchors·CF4·SDSS PV | 개별 방향과 공동 보정을 유지한 낮은 z distance/velocity tensor | 선택 congruence의 morphology; 유형 판정은 추가 기하 입력 필요 |
| DESI 개별 source 및 mocks | selection·window·교차 covariance | redshift만으로 거리 측정 불가; 압축 BAO의 가정 유지 |
| 선택적 Gaia/QSO proper motion | vector harmonic과 frame/source nuisance 공동 분석 | 절대 vorticity는 spin 기준 없으면 미식별 |
| CMB map·FFP10·WebSky | morphology·mask·foreground·noise 대조 | 주어진 simulation 생성모형 범위; Bianchi transfer library 아님 |
| HSC·KiDS·ACT lensing | projected optical tidal 제약 | 2D lensing을 normal shear나 전체 3D curvature로 대체 불가 |

현재 redshift-drift 실측을 확보했다고 가정하지 않는다. 우선순위는 기존 관측 response가 식 (3)–(4)의 어느 입력을 제한할 수 있는지 밝히는 것이다.

## 10. 실행 증거와 다음 연구루프

| 실제 Wolfram 실행 | 확인된 출력 |
|---|---|
| LRS metric | Killing residual 0, VII₀ bracket, determinant 1, shear 공식 |
| Lie curvature | Koszul scalar·Jacobi·부호 분석·IX 반례 |
| Sky moments | shear/vorticity 역산 residual 모두 0 |
| Spatial jet 예 | connection recovery 및 bracket recovery 모두 True |

입력과 원 출력은 evidence/의 4개 WL 및 4개 JSON이다. Reviewer는 이 기록과 증명·원문을 읽었으며 동일 계산을 재실행하거나 형식증명 kernel을 돌린 것으로 표시하지 않았다. 최종 결정은 INDEPENDENT_DECISION.json, 검토 범위는 INDEPENDENT_REVIEW.md에 있다.

다음 local 연구루프는 세 경로를 잇는다.

1. Wolfram/xAct: 식 (4), Gauss–Codazzi, normal/tilted-source 변환을 같은 convention으로 정리한다. 반복 고윳값 branch와 고차 광학 errata를 분리한다.
2. SageMath/Singular: Lie/Jacobi/물리 제약으로 유한 jet outer sets를 구성하고 공집합 인증서를 만든다. 다항식 해와 실제 시공간 해의 존재는 구별한다.
3. Lean/mathlib 및 기존 통계 코드: 식 (8)의 set inclusion/coverage와 exact algebraic recovery를 형식화하고, 준비된 response에서 남는 유형 집합을 계산한다.

가장 큰 미해결 문제는 **관측 tensor/적색편이 자료로부터 spatial tensor와 공간미분의 공동 허용집합을 구성하는 것**이다. 이를 해결하면 solver 없이도 조건부 분류 연구가 진전된다. 미확보 입력을 MES 정규화나 numerical rank로 대체하지 않는다.

## 참고문헌과 실제 열람

- Wald (1983), Phys. Rev. D 28,2118–2120. https://doi.org/10.1103/PhysRevD.28.2118 . 원문 p.2119 식 (9),(15)–(16).
- Ferrando–Sáez (2020), Homogeneous three-dimensional Riemannian spaces. https://arxiv.org/abs/2004.01877 . §§2,4–5의 정의·분류·제약.
- Sáez–Mengual–Ferrando (2024), Spatially-Homogeneous Cosmologies. https://arxiv.org/abs/2409.15854 . §§2–3,5,7–8; 모든 singular branch를 재증명하지 않음.
- Heinesen–Korzyński (2024), Phys. Rev. D 110,043525. https://arxiv.org/abs/2406.06167 . §§II,IV,VI–VII,IX, Appendix E의 관련 식·가정.
- Heinesen (2021), Multipole decomposition of the general luminosity distance Hubble law. https://arxiv.org/abs/2010.06534 . 후속 errata와 함께 취급.

추가 문헌의 열람 범위는 geometry_findings.md와 optics_findings.md에 기록했다. SciSpace metadata의 연도 오류는 원 논문 식별자로 보완했다. 문헌 정리, 직접 유도, 기호 검산, 관측 적용, 형식증명은 서로 다른 증거 단계다.
