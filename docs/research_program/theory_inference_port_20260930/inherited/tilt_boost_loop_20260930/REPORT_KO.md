# Tilt, 물질 기준계와 관측자 운동의 조건부 식별

2026-09-30 KST · 이론 연구 루프  
상태: 조건부 수학적 도출 및 소규모 기호 검산. 실제 관측자료 적합과 형식증명 커널 검증은 미실행. 최종 명제별 판정은 INDEPENDENT_DECISION.json을 따른다.

## 1. 이번 연구가 추가한 것

외부 Boltzmann solver 없이도 물질 흐름과 관측자 사이의 상대운동을 식별하는 충분조건을 제시할 수 있다. 공간적 균질면의 법선까지 독립적으로 정하면 이를 실제 cosmological tilt의 판별로 연결할 수 있다. 둘 사이를 잇는 관측 역문제가 자동으로 해결되는 것은 아니다.

이번 결과의 중심은 다음 세 경로다.

| 식별 대상 | 충분한 입력 | 연산 | 현재 한계 |
|---|---|---|---|
| 관측자와 물질의 상대운동 | 식별 가능한 방향별 영거리 redshift intercept | monopole/dipole의 정확한 역변환 | 실제 catalogue의 영거리 외삽과 source congruence |
| 관측자와 geodesic 물질의 상대운동 | 보정된 Hubble sky의 9개 다중극, 유일한 timelike eigenline | 대칭 4-텐서 복원과 고유벡터 계산 | acceleration, 퇴화, 유한거리 잔차와 관측오차 |
| 물질과 균질면 법선의 상대운동 | 곡률 scalar clock와 물리적 물질 속도, 또는 Codazzi flux와 유체 조건 | invariant 또는 대수적 flux 역변환 | 기하 입력의 관측적 복원, 다성분 물질 |

여기서 “global tilt”는 선언된 균질 구조에 대한 물질 흐름의 성질이다. 속도가 시간에 무관한 상수라는 뜻도, 한 사건의 결과가 우주 전체 시간에 증명됐다는 뜻도 아니다.

## 2. 세 배타적 분류 대신 두 축

부호는 \((-+++)\), 물리적 four-velocity의 제곱은 \(-c^2\)로 고정한다.

- \(N\): 선언된 spacelike homogeneous orbit의 미래방향 법선.
- \(U\): 선택한 물질 성분의 물리적 흐름.
- \(O\): 관측 사건에서 검출기의 four-velocity.
- \(R\): 따로 정의하고 존재를 확인한 복사 기준계. 항상 \(N\)이나 \(U\)와 같지는 않다.

\[
\gamma_{XY}=-\frac{g(X,Y)}{c^2},\qquad
\eta_{XY}=\operatorname{arcosh}\gamma_{XY},\qquad
\beta_{XY}^2=1-\gamma_{XY}^{-2}.
\]

| 물질/균질면 | 관측자/물질 | 해석 |
|---|---|---|
| \(U=N\) | \(O=U\) | non-tilted, 물질 공운동 관측자 |
| \(U=N\) | \(O\ne U\) | non-tilted, 관측자의 추가 운동 |
| \(U\ne N\) | \(O=U\) | tilted, 물질 공운동 관측자 |
| \(U\ne N\) | \(O\ne U\) | tilted, 관측자의 추가 운동도 존재 |

따라서 기본 판별 출력은 \((\eta_{UN},\eta_{OU})\)의 공동 허용집합이다. CMB로 추정한 \(\eta_{OR}\)는 별도 축이다. 서로 다른 rest space의 3-속도를 직접 빼지 않고, 같은 사건의 four-vector와 Lorentz 변환으로 비교한다. 복사 에너지 flux가 0인 기준계와 복사 분포 전체가 등방적인 기준계도 구별해야 한다.

Tilt를 균질면에 대한 유체의 운동으로 정의하는 기존 연구와 일치하는 구성이다. King–Ellis의 정의 및 Sandin의 다유체 예가 기준이 된다.[1,2]

## 3. 관측자–물질 운동의 정확한 복원

### 3.1 영거리 intercept

\(u=U/c,\ o=O/c\)라 하고 관측자 tetrad에서 과거방향 null vector를
\[
K=-o+n,\qquad n^2=1,\quad o\cdot n=0
\]
로 정한다. 동일한 smooth source congruence가 관측 사건까지 연장되고, 방향별 \(d_A\to0\) 한계가 물리적으로 식별된다고 가정한다. 동일 spectral standard로 측정한 redshift는
\[
Z(n):=\lim_{d_A\to0}(1+z)=K\cdot u
=\zeta_0+\zeta_i n^i.
\]
\(u=\gamma(o+\beta_{U/O})\)를 대입하면
\[
\zeta_0=\gamma,\qquad
\boldsymbol\zeta=\gamma\boldsymbol\beta_{U/O},
\qquad
\zeta_0^2-|\boldsymbol\zeta|^2=1,
\qquad
\boldsymbol\beta_{U/O}=\frac{\boldsymbol\zeta}{\zeta_0}.
\]

이 도출에는 Einstein 방정식, geodesic source, 특정 Bianchi type이나 expansion eigenvalue gap이 필요하지 않다. 대신 측정 대상인 intercept의 존재와 식별 가능성이 강한 전제다. 단순히 근처 은하의 유한한 redshift catalogue를 갖고 있다는 사실만으로 충족되지 않는다. 은하 내부/virialized 영역을 넘어 정의한 cosmological matter flow를 관측점까지 외삽할 때는 smoothing scale과 외삽 오차를 포함해야 한다.

또한 \(z(0,n)=0\)을 강제하면 바로 이 정보를 제거한다. \(\boldsymbol\beta_{U/O}\)는 관측자가 본 물질의 속도이며, 반대 pair의 방향을 쓰려면 변환을 명시한다.

### 3.2 Hubble 다중극에서 물질 eigenframe 복원

이번 두 번째 경로는 Maartens et al.의 covariant cosmography를 출발점으로 삼는다. 그 연구는 관측자의 운동이 Hubble dipole과 shear의 해석에 미치는 영향을 구하고, 거리 보정의 필요성을 설명한다.[3] 아래는 null quadratic form의 역문제로 다시 쓴 직접 도출이다.

\[
B_{ab}:=\nabla_{(a}U_{b)},\qquad A_a=U^b\nabla_b U_a.
\]
정규화 미분으로 \(B_{ab}U^b=A_a/2\)다. 따라서 geodesic source이면 \(B_{ab}u^b=0\). 실제로 식별된 방향별 기울기를
\[
\mathcal H_O(n)
:=c\left.\frac{\partial z}{\partial d_A}\right|_{0,n}
=B_{ab}K^aK^b
=h_0+h_{1i}n^i+q_{ij}n^in^j,\qquad \operatorname{tr}q=0
\]
로 쓴다. 이때 \(z/d_A\)와 \(\partial z/\partial d_A\)는 intercept가 0이 아니면 다르다. 관측량으로 luminosity distance를 쓰면 reciprocity 조건에서
\[
d_A=\frac{d_L}{(1+z)^2}
\]
를 사용한다.

관측자 orthonormal tetrad에서
\[
S_{00}=h_0,\qquad S_{0i}=-\frac12h_{1i},\qquad S_{ij}=q_{ij}
\]
를 만든다. 동일 null-sky를 주는 모든 대칭 텐서는 \(S+\lambda g\)다.

증명은 간단하다. 대칭 \(Z\)가 모든 단위 \(n\)에 대해
\(Z_{00}-2Z_{0i}n^i+Z_{ij}n^in^j=0\)을 만족하면 홀수 부분으로 \(Z_{0i}=0\)이다. 짝수 부분이 구면 위에서 상수이므로 \(Z_{ij}=a\delta_{ij}\), \(Z_{00}=-a\)다. 따라서 \(Z=ag\), 그리고 역은 \(g(K,K)=0\)으로 성립한다.

이제 \(S^a{}_b\)의 유일한 미래 timelike eigenline이 고유값 \(s_t\)를 갖는다고 하자. 그러면
\[
u=\text{future normalized timelike eigenvector}(S^a{}_b),
\qquad
B_{ab}=S_{ab}-s_tg_{ab}.
\]
이를 통해 \(\gamma_{UO}\), 물질 expansion과 shear가 함께 복원된다. 물질 rest space에서 \(B\)의 세 고유값이 모두 0이 아니면 충분하다. 공간 고유값끼리의 중복은 문제가 아니며, timelike branch와의 분리가 중요하다.

이 도출은 geodesicity를 사용하지만 vorticity가 0일 필요는 없다. 반대칭 \(\nabla_{[a}U_{b]}\)는 \(K^aK^b\) contraction에 나타나지 않기 때문이다. 반대로 \(\omega\)를 이 Hubble sky만으로 복원할 수도 없다. 논문의 전체 관측 분석이 회전하는 물질 흐름까지 구현됐다고 주장하는 것은 아니다.

퇴화의 정확한 범위도 정해진다. \(B=\operatorname{diag}(0,0,b_2,b_3)\)이면 모든
\(u_\chi=(\cosh\chi,\sinh\chi,0,0)\)가 timelike kernel에 속한다. 따라서 동일한 **기울기**는 속도의 연속적인 집합을 허용한다. 이는 한 사건의 운동학적 jet 반례다. 앞 절의 intercept까지 식별되면 이 퇴화를 해소할 수 있으므로 전체 거리–redshift 자료의 불가능성 정리로 확대하지 않는다.

유한오차 문제에서는 고유벡터 하나를 숫자로 반환하는 것만으로 부족하다. 허용된 다중극 집합 전체에서 timelike branch의 존재, 분리와 속도 범위를 전파해야 한다. Source acceleration이 자유로우면 \(B\cdot U=0\) 자체가 성립하지 않으므로 이 경로는 보류한다.

## 4. 물질 운동을 실제 cosmological tilt로 연결하기

### 4.1 곡률 scalar clock

열린 영역에 spacelike homogeneous \(G_3\) orbit이 있고, metric으로 만든 scalar \(I\)의 gradient가 nonzero timelike이라고 하자. Killing vector는 \(I\)를 보존하므로 \(\nabla I\)가 orbit에 수직이다. 미래방향 정규화로 \(N\)을 얻는다.

\[
\Xi_I(U)
=\frac{h_U^{ab}\nabla_aI\nabla_bI}{-\nabla_cI\nabla^cI}
=\frac{(U^a\nabla_aI)^2}{c^2[-(\nabla I)^2]}-1
=\gamma_{UN}^2-1,\qquad
h_U^{ab}=g^{ab}+\frac{U^aU^b}{c^2}.
\]
따라서
\[
\Xi=0\iff U=N,\qquad
\Xi>0\iff U\ne N,\qquad
\beta_{UN}^2=\frac{\Xi}{1+\Xi}.
\]

관측자 \(O\)를 바꿔도 이 판정은 변하지 않는다. \(U\)도 균질 대칭을 보존하면 같은 connected orbit에서 같은 판정이다. 여러 시각에 대한 결론에는 그 시각들의 입력이 따로 필요하다.

Einstein 방정식과 단일 perfect fluid의 \(\epsilon+p\ne0\)을 가정하면 Ricci의 유일한 timelike eigenline이 \(U\)를 선택한다. \(I\)가 metric의 2차 미분까지만 쓰는 곡률 scalar이면 \(\nabla I\)까지 포함한 metric 3-jet이 충분한 **조건부** 입력이다. 실제 관측으로 그 3-jet을 복원했다는 주장은 아니다.

예를 들어 trace-free radiation에서 \(R\)이 상수면 \(I=R\)은 실패한다. 다른 invariant가 작동할 수 있지만, 모든 invariant가 상수인 영역에서는 이 방법으로 normal을 고정하지 못한다. 총 stress의 energy frame과 선택된 물질 성분의 흐름도 구별해야 한다.

추가적인 필요조건은 모든 nonzero metric-scalar gradient가 timelike이고, \(dI\wedge dJ=0\)이라는 것이다. 이 조건의 위반은 선언된 spacelike homogeneity를 배제한다.

### 4.2 Codazzi momentum constraint

\(n=N/c\), \(h=g+n\otimes n\)이고 다음 ADM 부호를 고정한다.
\[
K_{ab}=-h_a{}^ch_b{}^d\nabla_c n_d,\qquad
J_a=-h_a{}^bT_{bc}n^c,\qquad
\kappa=\frac{8\pi G}{c^4}.
\]
\(K\)는 inverse length, \(J\)는 energy density 단위다. 물리적 energy flux는 \(cJ\), momentum density는 \(J/c\)다.
\[
D_bK^b{}_a-D_aK=\kappa J_a.
\]

단일 perfect fluid에 대해
\[
T_{ab}=(\epsilon+p)u_au_b+pg_{ab},\qquad
u=\gamma(n+\beta),\quad n\cdot\beta=0
\]
이면
\[
E_N+p=(\epsilon+p)\gamma^2,\qquad
J_a=(\epsilon+p)\gamma^2\beta_a,\qquad
\beta_a=\frac{J_a}{E_N+p}.
\]
공간 stress \(S^{(N)}\)에는
\[
S^{(N)}_{ab}-ph_{ab}
=\frac{J_aJ_b}{E_N+p}
\]
라는 추가 일관성 조건이 있다.

균질 invariant frame에서는 \(C^k{}_{ij}\)와 \(K_{ij}\)가 spatial connection 및 \(J\)를 대수적으로 정한다. 전체 evolution을 풀 필요가 없다. 예를 들어 \(C=0\)인 Bianchi I에서는 \(J=0\)이므로 단일 perfect fluid와 \(\epsilon+p\ne0\) 아래 tilt가 배제된다. 여러 유체의 counterflow에서는 총 flux가 상쇄되므로 같은 결론을 각 유체에 적용할 수 없다. 이 차이는 Sandin의 두 유체 Bianchi I 연구에서도 명시적이다.[2]

\(w=\epsilon+p>0,\ j=|J|\)라 두면
\[
r=\frac jw=\frac{\beta}{1-\beta^2},\qquad
\beta=f(r)=\frac{2r}{1+\sqrt{1+4r^2}}.
\]
\(f\)는 증가함수다. Sound simultaneous bounds
\(j\in[j_-,j_+]\), \(w\in[w_-,w_+]\), \(w_->0\)가 있으면
\[
f(j_-/w_+)\le\beta\le f(j_+/w_-).
\]
작은 flux만으로 작은 tilt가 보장되지는 않는다. Enthalpy의 양의 하한도 필요하다. 벡터 방향과 shear에 대한 정렬 정보는 이 scalar bound와 별도로 보존한다.

## 5. Local boost를 제거하는 정확한 조합

Photon propagation 방향을 \(e\)라 하면 \(D=\gamma(1-\beta\cdot e)\)다. Sourceward sky 방향 \(n=-e\)를 쓰면 \(D=\gamma(1+\beta\cdot n)\)이다. 동일 경로의 emitter와 observer를 각각 normal frame에 비교하면
\[
1+z_{\rm obs}=\frac{D_s}{D_o}(1+z_N).
\]
\(z_N\)은 선언된 geometry와 normal에 의존한다. 관측에서 이미 알려진 background redshift로 취급하지 않는다.

관측자만 같은 사건에서 바꾸면, aberration으로 방향을 다시 지정한 동일 source/ray에 대해
\[
1+z'=(1+z)/D_o,\quad
d_A'=D_od_A,\quad
d_L'=d_L/D_o.
\]
따라서
\[
\mathcal R=(1+z)d_A=\frac{d_L}{1+z}
\]
는 endpoint boost에 불변이다. Luminosity 표현에는 photon conservation과 reciprocity가 필요하다. 이는 Hubble slope를 위한 보정 \(d_L/(1+z)^2=d_A\)와 서로 다른 양이다.

같은 incoming null generator의 source/absorber를 같은 사건에서 비교할 수 있으면 \((1+z_1)/(1+z_2)\)에서도 \(D_o\)가 소거된다. 다른 방향 사이에서는 일반적으로 소거되지 않는다. 방향 간격 \(\delta\), \(|\beta|\le b_{\max}<1\)이면
\[
|\Delta\log D_o|\le
\frac{2b_{\max}\sin(\delta/2)}{1-b_{\max}}
\]
의 보수적 상계가 있다. 이는 logarithm의 평균값 부등식으로 직접 따른다.

이 조합들은 source 운동과 geometry를 남긴다. 따라서 boost 오염의 제어량이지 그 자체가 tilt 검출량은 아니다. 같은 observed redshift로 bin을 정의한 뒤 그 bin의 redshift를 비교하는 것은 독립적인 depth 정보가 아니다.

## 6. CMB가 줄 수 있는 것과 줄 수 없는 것

정확히 등방적인 blackbody 온도/intensity sky가 한 번의 boost만 겪었다는 매우 제한된 null에서는
\[
T_O(n)=\frac{T_0}{\gamma(1-\boldsymbol\beta_{O/R}\cdot n)}.
\]
양의 절대 thermodynamic temperature에 대해 그 필요충분조건은
\[
T_O(n)^{-1}=a+\boldsymbol b\cdot n,\qquad a>|\boldsymbol b|.
\]
이때 boost 축을 맞춘 convention에서
\[
\boldsymbol\beta_{O/R}=-\boldsymbol b/a,\qquad
T_0=(a^2-|\boldsymbol b|^2)^{-1/2}.
\]
역으로 이 \(T_0,\beta\)를 대입하면 원래 온도 sky가 복원되므로 충분성도 성립한다. 이 검사는 임의의 polarization까지 포함한 복사장 전체의 등방성을 보장하지 않는다.

실제 CMB는 intrinsic anisotropy를 갖는다. 이 엄격한 null의 위반을 global tilt의 증거로 해석하면 안 된다. Monopole를 제거한 component map에 \(1/T\) 검사를 그대로 적용해서도 안 된다.

보다 현실적인 방법은 제한된 intrinsic covariance family와 정확한 observer Lorentz response를 결합하는 것이다. Planck의 Doppler boosting 연구는 dipole 자체 외에 aberration/modulation을 이용한 관측 경로의 선례다.[4] Boltzmann 결과를 새로 계산하지 않고 관측적으로 제약된 \(C_\ell\)를 nuisance로 쓸 수는 있지만, covariance와 intrinsic anisotropy에 대한 가정을 함께 명시해야 한다.

반대로 intrinsic sky를 완전히 자유롭게 두면, 모든 \(\beta\)에 대해
\[
f_\beta=\mathcal B_\beta^{-1}f_{\rm obs}
\]
를 선택할 수 있다. 허용된 source family가 이 역변환에 닫혀 있으면 endpoint 데이터만으로 \(\beta\)를 정하지 못한다. 같은 pushforward와 noise law로 구성하면 분포 전체에 대한 퇴화도 성립한다. 이는 제한된 물리적 source family나 독립적인 물질 자료가 있는 경우의 불가능성 정리가 아니다.

CMB에서 \(O/R\), 거리–redshift에서 \(O/U\)를 구하면 matter–radiation streaming을 시험할 수 있다. \(U/N\)의 판정에는 여전히 normal의 기하학적 입력이 필요하다.

## 7. 모든 운동학량과 tensor 통계로의 연결

순간 boost와 congruence의 미분은 서로 다른 입력이다.
\[
U^a=\gamma(N^a+c\beta^a)
\]
를 미분하면 \(\nabla\beta\), \(\nabla N\), \(\nabla\gamma\)가 모두 나타난다. 같은 사건에서 같은 \(\beta\)를 갖더라도 \(\theta,\sigma,\omega,A\)가 다를 수 있다.

명시적인 운동학적 예로 Minkowski의 \(c=1\) 좌표에서
\(U=(\cosh r(t),\sinh r(t),0,0)\)를 택하면
\[
\theta=\dot r\sinh r,\quad
A^2=\dot r^2\cosh^2r,\quad
\sigma_{ab}\sigma^{ab}=\frac23\theta^2,\quad
\omega_{ab}=0.
\]
\(r\)을 고정해도 \(\dot r\)은 바뀔 수 있다. 이 예는 test congruence의 미분 자유도를 보인 것이며, 자가중력 단일 유체의 Bianchi I 해라고 주장하지 않는다.

물질의 nonzero vorticity가 독립적으로 확인되면 열린 근방 전체에서 hypersurface-normal field와 같을 수 없다. 한 사건에서 두 속도값이 같은 것까지 배제하는 명제는 아니다. 공간 대칭을 물질도 보존한다는 전제가 있으면 nonzero vorticity는 해당 orbit에서의 일치도 배제한다. 반면 \(\omega=0\)은 non-tilt의 충분조건이 아니다.

균질 lapse 아래 normal이 geodesic이라는 전제에서 \(A_U\ne0\) 역시 근방 전체의 field equality를 배제한다. 그러나 바로 위 예에서 \(r(t_0)=0,\dot r(t_0)\ne0\)이면 한 시각의 orbit에서는 \(U=N\)이면서 \(A_U\ne0\)이다. 따라서 acceleration만으로 순간 tilt를 선언하지 않는다. 관측자 acceleration을 물질 acceleration으로 대체해서도 안 된다.

기존 tensorized 관측량 \(T_{A_n}(a_{\ell m}^{X,Y},z,\ldots)\)과 \((x,Q,\Pi,F,G_F)\)는 다음 순서로 연결한다.

1. Frame, source component, \(z\), 거리, mask, beam, selection을 선언한 공동 관측 모형을 만든다.
2. 같은 모형에서 관측자 속도, 물질 kinematics, normal geometry의 허용집합을 구한다.
3. Tensor contraction, directional support, joint exceedance, depth coherence를 그 공동집합에 적용한다.
4. MES denominator는 같은 관측조건과 물리적 전제에서 구한다. 모수에 의존하면 분모도 공동추론 안에 남긴다.

예컨대 \(1-Q_{\rm obs}/Q_{\max}\)는 선언된 전제에 대한 상대적 여유 또는 차이다. 그 자체가 tilt 확률이나 다른 양과의 보편적인 통계적 유의도는 아니다. 물리적으로 유한한 공통 분모가 없으면 percentage를 생성하지 않는다. Scalarization 이전의 방향·shape 정보도 함께 남긴다.

## 8. 판정은 공동 허용집합으로

물리 상태와 nuisance를 포함하는 sound joint confidence set \(\mathcal C_\alpha\)를 가정한다. Bianchi action, normal, 선택된 물질 flow를 명시한 뒤
\[
\mathcal L_\alpha
=\{(B,\eta_{UN},\eta_{OU},T_{A_n},\ldots):s\in\mathcal C_\alpha\}
\]
로 pushforward한다. 참 상태가 \(\mathcal C_\alpha\)에 포함되면 참 label이 \(\mathcal L_\alpha\)에 포함되므로 같은 coverage 하한이 유지된다. 이 확률론적 명제는 실제로 calibrated \(\mathcal C_\alpha\)를 구성했다는 주장과 다르다.

- 모든 허용 상태에서 \(\eta_{UN}>0\)이면 선언된 모형에서 non-tilt를 배제한다.
- 상한이 사전 지정한 \(\varepsilon\)보다 작으면 그 tolerance에서 practical non-tilt라고 표현한다.
- 0과 양수가 함께 남으면 판별 미완료 또는 upper bound를 반환한다.
- 특정 observer-boost null을 배제해도, non-tilted anisotropic geometry가 남으면 global tilt를 주장하지 않는다.
- Exact \(U=N\)을 확정하는 구조적 정리와 유한오차에서 0과 양립하는 결과는 구별한다.

이전 루프의 Bianchi type 비유일성도 보존한다. 동일한 geometry에 여러 action label이 허용되면 한 label을 임의로 고르지 않는다.

## 9. 보유 자료에서 먼저 할 분석

아래는 사용자가 제공한 목록에 근거한 작업 배치이며, 이번에 해당 파일들의 실제 column이나 calibration 상태를 감사한 것은 아니다.

| 우선순위 | 자료 | 계산 목표 | 선행 조건 |
|---|---|---|---|
| 1 | CF4, SDSS PV, Union3 및 거리 앵커 | Free intercept와 방향별 Hubble 다중극의 공동 적합 | 원래 redshift frame, 독립 거리, calibrator, 중복 source와 covariance 확인 |
| 2 | Planck/ACT 지도 및 대응 시뮬레이션 | 제한된 intrinsic covariance 아래 \(O/R\), 1의 \(O/U\)와 비교 | phase·방향을 가진 지도/계수, mask·beam·foreground·Lorentz 처리 |
| 3 | 같은 source/ray의 거리–redshift 자료 | \(\mathcal R\), 가능한 동일 sightline contrast로 endpoint 제어 | source identity, ray matching, 독립 depth 및 오차 |
| 4 | Gaia 등 proper motion 자료를 실제 확보한 경우 | 추가 kinematic tensor 및 frame-spin 통제 | 절대 astrometric frame, source model, 거리·depth 응답; 기존 I3 입력 충족 |
| 5 | 위 추론과 geometric constraints | \(N\)과 \(J\)를 포함한 \(U/N\)의 공동 범위 | 아직 미완료인 관측→geometry 응답과 physical feasibility |

CMB power spectrum만으로 morphology와 observer 방향을 모두 복원하지 않는다. DESI redshift만을 독립 거리로 간주하지 않는다. 현재 목록에 실제 redshift-drift 측정이 있다고 가정하지 않는다.

가장 먼저 진행할 구체적인 local 작업은 CF4/SDSS PV/Union3의 공통 source·거리 계약을 검사하고, 자유로운 intercept와 covariant distance slope를 분리하는 것이다. 원래 heliocentric/barycentric/CMB 보정 이력을 복원하지 못하면 같은 local boost를 두 번 제거할 위험이 있으므로 해당 source는 보류한다.

## 10. 이번 검산과 다음 완료 조건

Wolfram evaluator에서 5개의 소규모 입력을 실행했다.

| 계산 | 확인한 내용 | 검증 범위 |
|---|---|---|
| flux_tilt | 에너지·flux·stress 관계, 역함수와 단조성 | 대수적 perfect-fluid identity |
| hubble_lift | Lorentz 변환, metric ambiguity, timelike eigenvector, 퇴화 | 대각 공간 expansion과 한 축 boost의 기호 예; 일반 증명은 본문 |
| endpoint_temperature | 거리·redshift 불변량, inverse-temperature affine 관계 | endpoint algebra |
| clock_and_velocity_jet | \(\Xi\), \(\theta,A,\sigma,\omega\)의 명시적 예 | 운동학적 항등식 |
| intercept_and_temperature_followup | intercept 정규화·속도 역변환, rest temperature 복원 | 마지막 temperature 식의 명시적 치환 포함 |

초기 temperature 출력은 \(\gamma=(1-\beta^2)^{-1/2}\) 관계를 가정식만으로 소거하지 않았다. 원본을 보존하고 마지막 계산에서 명시적으로 치환해 잔차 0을 확인했다. 단순화되지 않은 식을 성공으로 기록하지 않았다.

이 검산은 general relativity 전체, 관측 likelihood의 coverage, 전체 source law, Lean/mathlib proof를 검증한 것이 아니다. 일반 명제는 제시한 증명과 독립 검토에 근거한다. 독립 판정은 INDEPENDENT_REVIEW.md 및 INDEPENDENT_DECISION.json에 보존한다.

다음 local 단계는 (i) 부호·단위가 고정된 xAct 검증, (ii) null-cone lemma와 eigenspace 조건의 Lean/mathlib 정식화, (iii) 데이터 계약과 finite-distance remainder를 포함하는 통계 calibration이다. 조건을 통과하지 못한 분기는 unresolved로 반환한다. 기존 I2의 DEFENDED_CONDITIONAL, I3의 HOLD_INPUT_INCOMPLETE는 유지한다. 이전 BIC-07의 전체 관측→공간 jet 복원 역시 닫히지 않았다.

## 참고문헌과 출처 범위

[1] A. R. King and G. F. R. Ellis, “Tilted homogeneous cosmological models,” Communications in Mathematical Physics 31, 209–242 (1973). DOI: https://doi.org/10.1007/BF01646266 . 이번에는 publisher 초록 및 서지 확인.

[2] P. Sandin, “Tilted two-fluid Bianchi type I models,” General Relativity and Gravitation 41, 2707–2724 (2009). https://arxiv.org/html/0901.0800v1 . 원문 §2, momentum constraint 및 다성분 flux 상쇄 확인.

[3] R. Maartens et al., “Covariant cosmography: the observer-dependence of the Hubble parameter,” JCAP 09 (2024) 070. https://arxiv.org/html/2312.09875v3 . 원문 §§2–4 확인. 이 보고서의 null-form 역문제, intercept와 scope 구분은 제시된 직접 도출을 함께 따른다.

[4] Planck Collaboration, “Planck 2013 results. XXVII. Doppler boosting of the CMB: Eppur si muove,” Astronomy & Astrophysics 571, A27 (2014), corrected arXiv v3 (2015). https://arxiv.org/abs/1303.5087 . 이번에는 초록과 서지 확인; 발표된 속도값을 재현하지 않았다.

[5] A. Challinor and F. van Leeuwen, “Peculiar velocity effects in high-resolution microwave background experiments,” Physical Review D65, 103001 (2002). https://arxiv.org/abs/astro-ph/0112457 . 원문 Lorentz 변환 및 관측 covariance 전제 확인.

[6] A. A. Coley, S. Hervik and W. C. Lim, “Fluid observers and tilting cosmology,” Classical and Quantum Gravity 23, 3573–3591 (2006). https://arxiv.org/abs/gr-qc/0605128 . 이번에는 초록 및 서지 확인.

선행 내부 근거는 이전 Bianchi 연구 루프와 이미 보존한 T5/T6 observer-response 자료다. 이번에는 새 remote HEAD를 감사하거나 대용량 데이터베이스를 다시 다운로드하지 않았다. 새 이론 명제의 novelty나 논문 수준의 우선권을 주장하지 않는다.
