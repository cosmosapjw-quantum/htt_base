# MES 기준의 전 운동학 텐서 비교 — 두 번째 이론 연구 루프

2026-09-20 · `MES_GENERALIZED_TENSOR_R2` · 수치 우주 진화 없이 수행한 유도·유한 검산

## 연구 결론

원래의 목표는 **같은 관측·같은 물리 전제에서 허용되는 크기를 기준으로, 운동학적 유형에 관계없이 상대적인 이탈을 비교하는 것**으로 정식화할 수 있다. 이를 위해 서로 다른 rank의 물리량을 억지로 하나의 텐서에 합칠 필요는 없다. 팽창·전단·와도·가속도·tilt의 rank와 parity를 유지하는 텐서 묶음에 공통의 허용집합을 지정하고, 그 경계까지의 비율을 계산하면 된다. 크기 비율을 계산한 뒤에도 원래의 부호·방향·형태·성분 간 정렬을 남긴다.

이번에는 특정 Bianchi 유형을 선택하지 않았다. 새로 확보한 핵심은 (i) 모든 국소 운동학량을 분리하는 정확한 광학 사상과 안정성, (ii) 전 운동학에 대한 정확한 복사수송 약형, (iii) 관측 가능한 부분공간에서의 MES 기준 정규화와 likelihood, (iv) 기존 scalar 통계량을 수축으로 회복하는 새로운 tensor 통계량이다. 실제 CMB 관측 제약을 계산한 것은 아니다. 특히 정적인 하늘만으로 주어지지 않는 복사장의 시공간 미분을 숨기지 않는다.

저장소에서는 사용자가 허용한 MES-style bound와 그 정의·출처만 확인했다. R7–R10 등의 다른 저장소 선행연구는 이번 추론의 입력이 아니다. 바로 앞 R1의 정의와 국소 유도는 연속 작업으로 대조했으며, Bianchi I 예제를 일반화의 전제로 사용하지 않았다. VIGILODE는 요구 자료·미해결 의존성에서 제외했다. GPT-6 Astra 연구 하네스 v4.0.0을 적용했으며 실제 모델 성능 개선을 주장하지 않는다.

## 1. 정확히 무엇을 비교할 것인가

한 물리적 관측자 congruence와 기준 팽창률 \(H_*(z)>0\)를 고정한다. 차원 없는 대상은

\[
k=\left(\frac{\theta-\theta_{\rm ref}}{H_*},
\frac{\sigma_{ab}}{H_*},\frac{\omega_a}{H_*},
\frac{A_a}{cH_*},\beta_a\right)
\in\mathbb R\oplus\mathrm{STF}^2\oplus V_{\rm axial}
\oplus V_{\rm polar}\oplus V_{\rm polar}.
\tag{1}
\]

벡터인 가속도와 tilt도 서로 다른 성분 표지를 가진다. 와도는 공간 반사에서 axial vector이고 나머지 둘은 polar vector다. 총 표현 성분 수는 15이지만, 이들이 제약 없는 독립 물리 자유도 15개라는 뜻은 아니다. 동일 유체의 tilted kinematics를 계산한다면 \(\beta\)와 그 미분이 다른 성분을 묶는다. 국소 observer boost와 물질의 global tilt를 동시에 추론하면 별도 벡터 슬롯과 기준 congruence를 둔다.

\(H=\theta/3\)로 정의하면서 \(\theta/H\)를 추론하면 항상 3이 된다. 팽창의 크기 또는 이탈은 독립적인 차원 기준과 \(\theta_{\rm ref}\)가 필요하다. MES의 확장률 **구배** bound를 확장률 자체의 bound로 사용하지 않는다.

다른 시공간 지점의 텐서를 비교하려면 공통 tetrad 또는 명시한 경로를 따른 수송 사상을 정해야 한다. 곡률이 있으면 경로 독립인 비교가 자동으로 주어지지 않는다.

## 2. Bianchi 유형을 선택하지 않는 정확한 광학 정리

컨벤션은 \((-+++),\ U^aU_a=-c^2\), \(h_{ab}=g_{ab}+U_aU_b/c^2\), \(\epsilon_{123}=+1\)이다. 물리적 proper-time kinematics를

\[
\nabla_aU_b=-\frac{U_aA_b}{c^2}
+\frac{\theta}{3}h_{ab}+\sigma_{ab}+\omega_{ab},\qquad
\omega_{ab}=D_{[a}U_{b]},\quad
\omega^a=\frac12\epsilon^{abc}\omega_{bc}
\tag{2}
\]

로 정의한다. 여기의 와도 벡터는 양의 rigid rotation에 대해 \(+\boldsymbol\Omega\)다. Ellis 책의 p.82 (4.34)에 쓰인 벡터와는 부호가 반대다. 이 adapter는 norm bound에는 영향을 주지 않지만 signed morphology와 curl에는 필요하다.

광자의 진행 방향을 \(e\), 관측 하늘 방향을 \(n=-e\)라 하자. \(a=A/c\), \(S=\sigma\), \(H=\theta/3\)라 쓰고

\[
p^a=\frac{E}{c^2}(U^a+ce^a),\qquad
\mathscr D=(U+ce)^a\nabla_a
\]

를 정의한다. Null geodesic 식을 contraction하면

\[
\boxed{R(e):=-\mathscr D\ln E=H+a\cdot e+S:ee,}
\qquad
\boxed{V(e):=h\mathscr De=-P_e(a+Se)-\omega\times e,}
\tag{3}
\]

\(P_e=h-ee\)를 얻는다. \(R,V,H,a,S,\omega\)의 단위는 모두 \({\rm s}^{-1}\)이다. 식 (3)은 약한 비등방성, Einstein 방정식, 공간 균질성, 특정 Bianchi class를 요구하지 않는다. 미분 가능한 congruence와 geometric optics의 null propagation을 사용한다.

\(\langle f\rangle=(4\pi)^{-1}\int f\,d\Omega\), \(E_{ab}=e_ae_b-h_{ab}/3\)라 하면

\[
\boxed{H=\langle R\rangle,\qquad
a_a=3\langle e_aR\rangle,\qquad
S_{ab}=\frac{15}{2}\langle E_{ab}R\rangle,\qquad
\omega_a=-\frac32\langle(e\times V)_a\rangle.}
\tag{4}
\]

이는 이상적인 국소 \((R,V)\) 자료에 대한 12성분 역산이다. 와도는 scalar 적색편이율에서 사라지지만 vector 방향변화의 회전 성분에 남는다. 구면 위에서

\[
V=-\nabla_{S^2}(a\cdot e)-\frac12\nabla_{S^2}(S:ee)
+e\times\nabla_{S^2}(\omega\cdot e)
\tag{5}
\]

이므로 가속도는 gradient dipole, 전단은 gradient quadrupole, 와도는 toroidal dipole이다. 이것은 여러 유형을 공통의 광학 표현에서 다룰 수 있는 구체적인 이유다. 여기의 gradient/toroidal 구분은 CMB polarization의 E/B 관측량과 동일한 대상이 아니다.

구면 적분으로

\[
\langle R^2\rangle=H^2+\frac{|a|^2}{3}+\frac{2\|S\|_F^2}{15},
\qquad
\langle|V|^2\rangle=\frac{2|a|^2}{3}+\frac{\|S\|_F^2}{5}
+\frac{2|\omega|^2}{3}
\tag{6}
\]

를 얻는다. 두 자료에 동일한 \(L^2\) 가중치를 주는 수학적 convention에서 least-squares 역산은

\[
\hat a=\langle eR-V\rangle,\quad
\hat S_{ab}=3\langle E_{ab}R-e_{\langle a}V_{b\rangle}\rangle,
\quad\hat H=\langle R\rangle,\quad
\hat\omega=-\frac32\langle e\times V\rangle
\]

이고,

\[
\boxed{\|\delta k_{\rm rate}\|
\le\sqrt3\,\| (\delta R,\delta V)\|_{L^2},}
\quad
\|k_{\rm rate}\|^2=H^2+|a|^2+\|S\|_F^2+|\omega|^2.
\tag{7}
\]

이는 새로 유도한 유한 오차 bound다. 실제 자료의 서로 다른 noise·단위 변환·selection에는 실제 공분산을 사용해야 한다.

**관측과 연결할 때의 경계:** \(R\)는 유한 redshift 자체가 아니고 \(V\)는 관측 source proper motion 자체가 아니다. 실제 광로에서는

\[
\ln(1+z)=\int_s^oR\,d\tau_{\rm ray}.
\tag{8}
\]

고정 tetrad의 좌표 방향변화는 \(V\)에 triad의 회전과 공간 connection을 보정한 값이다. 따라서 식 (4)를 \(a_{\ell m}\)에 그대로 적용해 “CMB에서 관측한 전단·와도”라고 부르지 않는다. 일반 시공간의 저적색편이 거리 전개가 유한한 방향 multipole로 정리된다는 독립적인 문헌 경로도 있다. [Heinesen, JCAP 2021](https://arxiv.org/html/2010.06534v2)

## 3. 실제 복사 모멘트로 쓰는 전 운동학 연산자

편광 B와 혼동하지 않도록 bolometric brightness를 \(\mathscr B(e)\ge0\)로 쓴다. \(\rho_\gamma=\int\mathscr B\,d\Omega\), \(M_a=\int\mathscr B e_a\,d\Omega\), \(M_{ab}=\int\mathscr B e_ae_b\,d\Omega\)이다. 일반 스펙트럼에서도 에너지 적분 경계항 \(E^4f\to0\)이면

\[
\mathcal A_k\mathscr B
=-[P_e(a+Se)+\omega\times e]\cdot\nabla_{S^2}\mathscr B
+4(H+S:ee+a\cdot e)\mathscr B
\tag{9}
\]

가 정확하다. \(\mathscr B=a_RT^4/(4\pi)\), \(a_R=\pi^2k_B^4/(15\hbar^3c^3)\)를 사용할 때만 각 방향의 blackbody 가정을 추가한다. \(T\)와 \(T^4\)의 multipole은 구별한다.

\(\psi_\ell=e_{\langle A_\ell\rangle}\)의 동차 다항식 연장을 쓰면 구면 부분적분으로

\[
\boxed{J_{A_\ell}(k)=\int\mathscr B\left\{
(a+Se+\omega\times e)\cdot\partial_e\psi_\ell
+[4H+(1-\ell)S:ee+(2-\ell)a\cdot e]\psi_\ell
\right\}d\Omega.}
\tag{10}
\]

여기서 \(\partial_e\)는 **주변 3차원 동차 다항식의 미분**이다. 이를 구면 gradient로 바꾸려면 이미 사용한 동차 차수 항도 함께 바꾸어야 한다. 낮은 모멘트는

\[
J_0=4H\rho_\gamma+S:M_2+2a\cdot M_1,
\tag{11}
\]
\[
J_1=4HM_1+SM_1+\omega\times M_1+(\rho_\gamma I+M_2)a,
\tag{12}
\]
\[
J_2=4H\pi^\gamma+\mathcal L_{\mathscr B}(S)
+2a_{\langle a}M_{b\rangle}+[R_\omega,M_2],
\tag{13}
\]

이며 \(\pi^\gamma=M_2-\rho_\gamma I/3\), \(R_\omega v=\omega\times v\)다. \(\pi^\gamma\)는 아래 통계량 \(\mathbb\Pi\)와 다른 물리량이다. 전단 블록 \(\mathcal L_{\mathscr B}\)는 R1의 정확한 양의 자기수반 연산자다.

선택한 모멘트를 모으면

\[
\boxed{\mathsf A_{\mathscr B}k_{\rm rate}=r,\qquad
\mathcal K=\{k:\mathsf A_{\mathscr B}k\in\mathcal R\}\cap\mathcal C_{\rm phys}.}
\tag{14}
\]

\(r\)에는 충돌, 시공간 복사 미분, 명시한 frame connection의 나머지가 들어간다. \(\mathcal R\)는 그 허용집합, \(\mathcal C_{\rm phys}\)는 실제 채택한 물리 조건이다. 이 역상은 완전 hierarchy를 수치 진화하지 않고도 계산할 수 있는 **조건부 일반화 부등식**이다. 선형 부분공간에서 \(\mathsf A\)가 coercive하면 최소 singular value로 유한 잔차 오차를 제한한다. Null direction은 사라지지 않는다.

중요한 구성적 결과: 정확한 유리수 구면 적분에서, 차수 0–4의 35개 다항식 시험함수에 대한 12열 연산자는 등방 \(\mathscr B\)에서 rank 9, 이번에 명시한 양의 비등방 다항식에서 rank 12였다. 등방 하늘에는 회전할 texture가 없어 와도 3열이 0이다. 이는 **잔차가 알려진 연산자의 가능성**을 확인한 것이며 정적인 하늘의 관측 식별성을 증명한 것은 아니다. \(r\)를 임의로 허용하면 어떤 \(k\)에도 맞는 국소 복사 미분을 선택할 수 있다.

## 4. dynamics를 포함하면서 진화 solver를 피하는 범위

이 연구의 물리 제약은 단순 정규화 정의로 끝나면 안 된다. 가능한 경로는 국소 jet의 대수 제약, 약형 적분, 유계 잔차다. 예를 들어 proper time \(\tau\)에 대한 정확한 Raychaudhuri 식은 현재 norm convention에서

\[
\dot\theta+\frac{\theta^2}{3}+\|\sigma\|_F^2
-2|\omega|^2+R_{ab}U^aU^b-\nabla_aA^a=0.
\tag{15}
\]

\(\nabla_aA^a\)는 4차원 divergence다. 이를 spatial divergence로 바꾸면 해당 \(A^2/c^2\) 항도 포함해야 한다. 정해진 시험함수 \(w(\tau)\)로 적분하면

\[
\int w\left(\frac{\theta^2}{3}+\|\sigma\|_F^2-2|\omega|^2
+R_{UU}-\nabla\cdot A\right)d\tau
=\int w'\theta\,d\tau-[w\theta]_{\tau_1}^{\tau_2}.
\tag{16}
\]

이렇게 실제 동역학을 residual constraint로 넣을 수 있다. Einstein 방정식으로 \(R_{UU}\)를 물질 변수로 치환하려면 그 이론과 응력·에너지 조건을 추가로 선언한다. 모든 항이 기존 관측에서 자동으로 주어진다는 주장은 하지 않는다.

유한 구간의 jet/Taylor 표현도 \((p+1)\)차 미분의 bound \(M\)가 있을 때 remainder \(M|\Delta\tau|^{p+1}/(p+1)!\)와 함께 사용할 수 있다. 이는 작은 구간의 조건부 통제다. 저적색편이 전개를 마지막 산란면까지 무조건 외삽하지 않는다. 임의의 \(z\)를 쓰고 시간 적분으로 해석하려면 \(d\tau/dz\)와 선택한 congruence·광로가 필요하다.

## 5. Lie algebra만 주어진 경우

\([E_i,E_j]=C_{ij}{}^kE_k\)와 Jacobi identity를 만족하는 임의의 구조상수를 입력으로 유지한다. 이름 붙은 Bianchi type을 고르지 않아도 위 식은 성립한다. 그러나 대수만으로 크기·시간변화·광로가 정해지지는 않는다. invariant metric \(g_{ij}(t)\)를 주면

\[
2g(\nabla^{(3)}_{E_i}E_j,E_k)
=C_{ij}{}^lg_{lk}-C_{jk}{}^lg_{li}+C_{ki}{}^lg_{lj}
\tag{17}
\]

에서 connection을 구한다. 여기에 \(g,\dot g\), lapse, \(\beta,\nabla\beta\), 물질·source 제약을 넣어 유한한 국소 문제를 구성할 수 있다. 즉 class 이름 없이 일반식을 만들 수 있지만 \(C\)만으로 numerical prediction은 나오지 않는다.

균질한 lapse·zero shift의 hypersurface normal congruence는 \(\omega=0,A=0\)이다. 모든 운동학량을 연구하려면 tilted matter/observer congruence를 명시적으로 허용해야 한다. invariant 성분 \(\beta^i(t)\)의 ordinary spatial derivative가 0이어도 connection 때문에 covariant spatial derivative가 0일 필요는 없다.

## 6. local boost와 global tilt의 redshift 계약

\[
\widetilde U=\gamma(U+c\beta),\qquad
\gamma=(1-\beta^2)^{-1/2},\quad \beta\cdot U=0.
\]

한 사건에서는 \(D=\gamma(1-\beta\cdot e)\)에 대해

\[
\widetilde E=DE,\quad d\widetilde\Omega=D^{-2}d\Omega,\quad
\widetilde{\mathscr B}(\widetilde e)=D^4\mathscr B(e),\quad
1+\widetilde z=\frac{D_s}{D_o}(1+z).
\tag{18}
\]

반면 global congruence의 deformation은

\[
\boxed{\widetilde K_{ab}=\gamma\widetilde h_a{}^c\widetilde h_b{}^d
(\nabla_cU_d+c\nabla_c\beta_d).}
\tag{19}
\]

따라서 local \(\beta\) 값만으로 global tilt의 팽창·전단·와도·가속도를 정할 수 없다. 점에서의 frame transformation과 공간·시간에 걸친 물리적 velocity field는 구별한다.

1차 boost의 고정 하늘 좌표 작용은

\[
\delta_\beta\mathscr B=P_e\beta\cdot\nabla\mathscr B-4(\beta\cdot e)\mathscr B
=-\mathcal A_{{\rm acc},\beta}\mathscr B.
\tag{20}
\]

가속도 수송과 같은 angular generator지만 계수의 물리 차원은 다르다. 둘을 단일 하늘에 독립 template처럼 넣으면 인공적 퇴화·중복 계산을 만들 수 있다. 실제 CMB aberration과 modulation은 관측자 boost를 제약하는 독립적인 정보원이다. [Planck Doppler boosting 분석](https://arxiv.org/abs/1303.5087)

Redshift bin은 유용하지만 그 자체가 global tilt 판별 정리는 아니다. 선언한 합성 모델 \(d_i=\beta_o+g_i\beta_G\)에서 \(g_i\)가 상수면 rank 3, 깊이에 따라 독립적으로 달라지면 rank 6이다. source dipole를 각 bin마다 자유롭게 허용하면 이 이득이 다시 사라질 수 있다. 이 예의 \(g_i\)는 우주론적으로 유도한 예측이 아니다. 실제 분석에서는 source·selection·screen·electron optical depth 등을 포함한 응답이 필요하다. 한 장의 CMB 지도에 \(z\) 표지만 추가하여 tomography로 취급하지 않는다.

## 7. MES 분모: 확인한 것과 일반화할 것

현재 읽은 저장소 snapshot은 `50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb`다. 전단 외의 와도·가속도 MES-style 식이 실제 코드에 있음을 확인했다. 이것은 사용자가 말한 선행 bound의 존재를 확인한 것이다.

원전 MESa의 geodesic, 1차, 미분조건부 식과 C1/C2 축약을 직접 대조하면

\[
\frac{\|\sigma\|_F}{\theta}\lesssim
B_\sigma=\frac53\epsilon_1+3\epsilon_2+\frac37\epsilon_3,
\quad
\frac{\|\omega_{ab}\|_F}{\theta}\lesssim
B_{\omega,t}=\frac{10}{3}\epsilon_1+\frac{2}{15}\epsilon_2.
\tag{21}
\]

여기서 \(\lesssim\)는 이번 표기에서 1차 식과 derivative estimate의 상태를 드러낸다. 원문의 strict inequality를 finite-order exact theorem으로 승격하지 않는다. 벡터 와도는 \(\|\omega_{ab}\|_F=\sqrt2\|\omega_a\|\)를 적용한다. 원전에는 확장률 구배 bound도 있지만 \(\theta\) 자체의 상한은 아니다. [MESa 원문](https://arxiv.org/pdf/astro-ph/9501016), [SAG의 multipole norm 대조](https://arxiv.org/html/astro-ph/9904346v1)

| 대상 | 이번에 사용할 수 있는 근거 | 정규화 계약 |
|---|---|---|
| 전단 | 원전의 조건부 1차 식·norm 확인 | \(H_*\) 기준이면 \(b_\sigma=(\theta/H_*)B_\sigma\) |
| 와도 벡터 | 원전 tensor-vorticity 식 확인 | \(b_\omega=(\theta/H_*)B_{\omega,t}/\sqrt2\) |
| 가속도 | 저장소 별도 식은 존재; 확인한 geodesic 원전에서는 \(A=0\) | 별도 nongeodesic 정리 또는 선언한 reference radius 필요 |
| 팽창 | 원전에는 \(D\theta\)의 bound | \(\theta\) 이탈은 별도 관측·기준, \(D\theta\)는 추가 vector sector로 가능 |
| tilt | 확인한 원전 부분에서 MES \(\beta\) ceiling 미확보 | endpoint/aberration/source 조건으로 별도 반경; \(|\beta|<1\)과 구별 |

저장소의 별도 계수 \(B_\omega^{\rm reg}=(3/4,2,2/7)\cdot\epsilon\), \(B_A^{\rm reg}=(3/4,1,3/14)\cdot\epsilon\)는 확인한 원전과 귀속이 일치하지 않았다. 접근하지 못한 MESb 본문까지 포함해 반증했다고 주장하지 않는다. 이번 상태는 **식의 존재 확인 / 출처와 비측지 전제 미확인**이다. 과거의 부정적 판정을 새 연구의 전제로 채택하지 않는다.

이 때문에 일반화 연구를 멈출 필요는 없다. 식 (14)의 공동 residual body를 nongeodesic 조건 아래 유도하거나, 명시적으로 선언한 양의 reference radius를 써서 tensor 비교를 할 수 있다. 다만 모든 성분에 “원전 MES가 보증한 상한”이라는 이름을 붙이지 않는다. geodesic bound와 비측지 가속도 추론을 서로 다른 가정에서 가져와 공통 theorem처럼 조합하지 않는다.

\(\epsilon_\ell\)는 full STF norm이다. orthonormal \(Y_{\ell m}\), 온도 단위 \(a_{\ell m}\)에 대해

\[
\|\tau_{A_\ell}\|^2=\frac{(2\ell+1)!!}{\ell!}
\frac{\sum_m|a_{\ell m}|^2}{4\pi T_0^2}.
\tag{22}
\]

단순 sky RMS와 다르다. 또한 한 sky의 측정 amplitude를 MES가 요구하는 시공간 영역 전체의 derivative envelope로 자동 치환할 수 없다.

## 8. 원하는 deviation percentage의 정확한 일반화

동일한 관측 계약 \(\mathscr E\)와 물리 전제 \(\mathcal H\)에서, 차원 없는 displacement \(y=k-k_{\rm ref}\)의 허용/reference body \(\mathcal B\)를 정한다. 각 성분의 반경이 실제 달성되는 최대값일 필요는 없다. 외측 bound와 attainable supremum은 구별한다.

\(\mathcal B\)가 유계·닫힘·원점 내부를 갖는 convex body일 때 gauge를

\[
\gamma_{\mathcal B}(y)=\inf\{\lambda>0:y\in\lambda\mathcal B\}
\]

로 두면, rank에 상관없이

\[
\boxed{D_{\mathcal B}=100[1-\gamma_{\mathcal B}(y)]}
\tag{23}
\]

로 원래의 목적을 표현한다. 단일 sector ball이면 정확히

\[
D_s=100\left(1-\frac{\|k_s-k_{s,\rm ref}\|}{b_s}\right).
\]

100은 기준 대비 이탈 0, 0은 선언한 경계 도달, 음수는 경계 바깥이다. 확률이나 “우주의 몇 %가 FLRW인가”는 아니다. 사용자의 표현대로 **그 관측조건과 전제에서 기준 상한까지 남은 상대 여유**다. \(b_s=0\), 미확보, 무한인 경우 percentage를 정의하지 않는다.

방향 \(u\)의 radial boundary \(\rho_\mathcal B(u)=\sup\{r:ru\in\mathcal B\}\)와 선언한 회전불변 내적을 사용하면

\[
\boxed{T_\mathcal B(y)=\frac{y}{\rho_\mathcal B(y/\|y\|)},\quad
\|T_\mathcal B\|=\gamma_\mathcal B(y)}
\tag{24}
\]

가 morphology를 보존하는 normalization이다. \(y=0\)에서는 0으로 정의한다. 알고 있는 \(\mathcal B\)와 함께 보존하면 역변환 가능하며, 물리적 공간 회전에 대해 body와 tensor를 함께 회전시키면 공변적이다. 서로 다른 sector의 개별 percentage와 전체 body의 percentage를 별도로 저장한다.

각각의 scalar bound만 알고 있으면 공동 body는 product이고 gauge는 최대값이다:

\[
\mathcal B=\prod_s\{\|y_s\|\le b_s\},\qquad
\gamma_\mathcal B=\max_s\frac{\|y_s\|}{b_s}.
\tag{25}
\]

이를 임의로 제곱합 \(\le1\)인 타원체로 바꾸면 새로운 강한 제약을 발명하게 된다. 예를 들어 두 성분이 각각 80%인 상태는 product bound를 만족하지만 그 타원체는 만족하지 않는다.

## 9. \(T_{A_n}(a_{\ell m}^{X,Y},z,\ldots)\)와 likelihood

실제 자료 \(d\)에는 사용 가능한 \(a_{\ell m}^T,a_{\ell m}^E,a_{\ell m}^B\), 교차장 morphology, redshift 자료 및 관측 보정이 들어간다. \(C_\ell\)만으로는 phase·축을 복원할 수 없다. 동일 \(C_2\)라도 서로 다른 고유값 형태를 갖는 STF quadrupole이 존재함을 검산했다.

선택한 국소/약형 근사에서

\[
d=\mu_0+\mathsf R k+\mathsf N\eta+\varepsilon,\qquad
\varepsilon\sim\mathcal N(0,C)
\tag{26}
\]

를 실제 응답과 remainder 조건에서 도출한다. \(\eta\)는 source·calibration 등 nuisance다. 이 식은 자동으로 얻어진 CMB transfer model이 아니라, 현재 물리 identity를 관측 계약으로 닫을 때 충족해야 할 명시적 조건이다. 편광에는 별도의 spin-2 screen transport가 필요하며 이번 scalar intensity 유도로 이미 검증됐다고 하지 않는다.

무제약 선형 nuisance를 profile하면

\[
P=C^{-1}-C^{-1}\mathsf N(\mathsf N^TC^{-1}\mathsf N)^+
\mathsf N^TC^{-1},\quad
\mathcal I=\mathsf R^TP\mathsf R,
\quad \hat k_I=\mathcal I^+\mathsf R^TP(d-\mu_0).
\tag{27}
\]

식별 부분공간 \(I=\mathrm{range}(\mathcal I)\)에서
\(E\hat k_I=\mathsf P_Ik\), \(\mathrm{Cov}\hat k_I=\mathcal I^+\)다. pseudoinverse는 선언한 metric의 orthonormal component basis에서 취한다. 따라서 요청한 통계량의 관측 버전은

\[
\boxed{T_{A_n}^{(s)}(d,z;\mathscr E,\mathcal H)
=\left[T_{\mathcal B_I}
(\hat k_I-\mathsf P_Ik_{\rm ref})\right]_{A_n}^{(s)},
\qquad\mathcal B_I=\mathsf P_I\mathcal B.}
\tag{28}
\]

허용집합은 **투영**한다. \(\mathcal B\cap I\)를 쓰면 미관측 성분을 0으로 놓는 추가 가정이다. prior가 null direction을 좁힌 경우에는 자료가 그 성분을 측정한 것과 구별한다.

이론이 특정 \(k_{\rm th}\)를 예측하면 동일한 \(\mathcal B_I\)로 \(T_{\rm th}=T_{\mathcal B_I}(\mathsf P_Ik_{\rm th}-\mathsf P_Ik_{\rm ref})\)를 만들 수 있다. 두 텐서는 같은 공간에서 비교한다. MES가 허용집합만 줄 때는 하나의 \(T_{\rm th}\)가 아니라 집합과 비교해야 한다. Gaussian 선형 예에서는

\[
\Delta\chi^2_{\mathcal B}=\inf_{k\in\mathcal B,\eta}\chi^2(k,\eta)
-\inf_{k,\eta}\chi^2(k,\eta)
\tag{29}
\]

로 정량화할 수 있다. 경계·부등식·식별 rank가 있으므로 무조건적인 표준 \(\chi^2\) 귀속은 하지 않고 실제 null law로 calibration한다.

기본 likelihood는 자료 공간에 둔다:

\[
-2\log L=(d-\mu)^TC^{-1}(d-\mu)+\log\det C+\mathrm{const}.
\tag{30}
\]

정규화 텐서 공간의 likelihood를 쓰면 전체 pushforward law를 사용한다. 고정된 가역 선형 normalization에는 공분산을 함께 변환한다. 비선형/자료 의존 normalization에는 Jacobian 또는 유도된 sampling law가 필요하다. 분모와 분자가 같은 하늘에서 계산되면 공동 표본으로 전파한다. 예를 들어 \(s=e^Z,b=2e^Z\)이면 \(s/b=1/2\)의 불확실성은 0이다. 두 값을 독립이라고 취급하면 존재하지 않는 ratio variance가 생긴다. 반대로 이런 ratio 자체는 원 진폭 정보를 잃으므로 분모·자료도 함께 보존한다.

**두 가지 공평성:** 같은 \(\|k_s\|/b_s\)는 사용자가 원한 기준 대비 동일한 비율이다. 동일한 detection significance는 별도다. 3성분 vector와 5성분 STF가 각각 반경 60%, 성분 noise 20%이면 \(D=40\%\)는 같지만 영가설의 \(\chi^2\) tail은 각각 약 0.0293과 0.1091이다. 이 차이는 비교 목적을 무효화하지 않는다. percentage와 rank/covariance를 반영한 유의성을 나란히 보고하면 된다.

## 10. \(Q,F,\Pi,G_F\)의 명시적 tensor 승격

아래는 기존 의미와의 환원식을 갖는 **새 제안 정의**이며 전체 기존 \(x\)의 동일성을 자동 선언하지 않는다. 같은 내적에서

\[
\mathbb Q=T\otimes T,\qquad
F_\mathcal B=\mathrm{tr}\,\mathbb Q=\|T\|^2=\gamma_\mathcal B^2,
\qquad D=100(1-\sqrt{F_\mathcal B}).
\tag{31}
\]

따라서 amplitude 기준인 사용자의 \(1-\mathrm{observed}/\mathrm{bound}\)는 \(1-\sqrt F\)이고 \(1-F\)와 구별된다. \(\mathbb Q\)는 sector 간 cross block·정렬을 남기지만 \(T\to-T\)를 구별하지 못하므로 signed \(T\)도 반드시 보존한다. 실제 유효 bound 안에 있다는 조건이 확인된 경우에만 \(F\in[0,1]\)의 filling 해석을 쓴다. noisy estimator를 임의 clipping하지 않는다.

\(q\ge0\)에서 확률법칙을 지정하고

\[
\boxed{\mathbb\Pi(q)=E\left[\frac{T\otimes T}{F}
\mathbf1_{F>q}\right],\qquad
\mathrm{tr}\,\mathbb\Pi(q)=P(F>q)}
\tag{32}
\]

로 정의한다. \(F=0\)에서는 integrand를 0으로 둔다. 이 tensor tail은 scalar exceedance probability를 정확히 회복하면서 어느 방향·성분이 tail을 만드는지 남긴다. posterior law와 repeated-sampling law는 구별해 표기한다.

두 redshift/epoch의 공통 metric에 대한 등거리 수송 \(\mathsf U_{b\to a}\)와 \(F_b>0\)에서

\[
\boxed{\mathbb G_{ab}=\frac{T_a\otimes(\mathsf U_{b\to a}T_b)}{F_b},
\qquad\|\mathbb G_{ab}\|_{\rm HS}^2=\frac{F_a}{F_b}=G_F.}
\tag{33}
\]

성장 비율과 방향 변화를 함께 담는다. 각 epoch에서 다른 물리 반경으로 정규화했다면 \(G_F\)는 raw 운동학량의 성장률이 아니라 budget fraction의 변화다. \(F_b\approx0\)일 때는 joint law와 차이 \(T_a-\mathsf U T_b\)를 제시하고 임의 epsilon으로 유한 평균을 만들지 않는다.

앞 루프에 기록된 signed \(x=\Sigma_{\rm std}^2-W_{\rm std}^2+\Omega_{\rm tilt}+\Omega_{k,\rm aniso}\)는 양의 norm과 다르다. 이 정의 자체를 버리지 않고, 필요한 보조 변수를 포함한 별도 수축 \(x=\langle k,Jk\rangle+\cdots\)로 유지할 수 있다. 와도 항의 cancellation을 \(\|T\|\)가 재현할 이유는 없다. \(\Omega_{\rm tilt}=|\beta|^2\)라고 임의 정의하지 않는다. 전체 \(x\)와 이번 positive tensor 통계량의 완전한 환원에는 구성항의 정확한 정의가 더 필요하다. 전단 부문에서는 R1의 \(x_\sigma=\mathrm{tr}(\sigma/H)^2/6\), \(U_\sigma=3B_\sigma^2/2\)를 택하면 \(x_\sigma/U_\sigma=(\|\sigma\|/(\theta B_\sigma))^2\)로 일치한다.

## 11. 실제 검산과 판정 범위

| 검사 | 현재 실행 결과 | 무엇을 증명하지 않는가 |
|---|---|---|
| 광학 inverse/norm 8개 | 유리수 sphere arithmetic에서 정확 일치; Wolfram 독립 호출도 해당 residual 0 | 실제 \(R,V\) 취득 |
| weak/strong 적분 840개 | 정확 일치 | 모든 함수공간의 자동 증명; 일반 항등식 증명은 유도 참조 |
| 지정 연산자의 rank | 등방 9, 양의 비등방 예제 12 | 정적 CMB만의 역산 가능성 |
| nonpolynomial positive sky 검산 | 낮은 모멘트 최대오차 약 \(4.3\times10^{-14}\) | 실제 관측 pipeline |
| finite Lorentz 검산 | 최대 residual 약 \(8.9\times10^{-16}\) | global tilt 가설의 채택 |
| tensor tail/growth 환원 | 합성 표본에서 trace/norm 식 일치 | 실제 posterior fitting |
| 같은 반경비의 dimension 효과 | vector/STF 영가설 tail 차이 계산 | MES percent를 p-value로 해석 |

SymPy 미설치 실패와 Wolfram wrapper 문법 오류를 보존하고 stdlib Fraction 및 수정된 Wolfram 식으로 검산을 완료했다. 이는 package/구현 오류이며 물리 정리 실패가 아니다. Python runtime 자체는 현재 턴에 실제 실행됐다. 독립 최종 판정의 범위·대상 hash는 별도 `INDEPENDENT_DECISION` 기록이 권위를 갖는다.

## 12. 이번 수렴 결정과 다음 루프

선택한 경로는 **공변 광학·수송 identity → 유계 joint residual/jet 집합 → 관측의 식별 부분공간 → MES 기준 tensor normalization → 동일 자료 likelihood**다. 개별 Bianchi evolution solver나 solver atlas를 전제로 하지 않는다. 광학 inverse는 목표를 정의하고, weak transport는 관측 radiation과 연결하며, residual 조건과 보조 관측이 실제 식별성을 결정한다.

다음의 최소 과제는 단순히 더 많은 정리를 나열하는 것이 아니다. 하나의 고정된 관측 실험에서 \(\mathcal R\)의 물리적으로 유용한 유계를 정해야 한다. 우선 권장하는 좁은 과제는 **CMB 온도 morphology + local-boost aberration/modulation + 저적색편이 거리 multipoles**의 공통 선형/약형 응답을 만들고, \(\theta,\sigma,A,\beta\)의 식별 조합과 남는 와도 nullspace를 계산하는 것이다. 와도를 모든 경우에 측정한다고 가정하지 않고 회전 민감 관측을 더했을 때 rank가 무엇으로 증가하는지 판별한다. 편광·remote dipole/quadrupole은 별도 screen/source 계약을 갖는 추가 경로다.

실제 데이터를 바로 내려받기 전에 끝내야 할 일은 (i) 이 관측 실험의 frame/source/derivative 예산 고정, (ii) 허용집합이 유계가 되는 조합 확인, (iii) 같은 하늘을 쓰는 분모의 joint uncertainty와 estimator law 검산이다. 지금까지의 결과는 이 세 작업을 특정 Bianchi 유형 없이 수행할 수 있는 분석적 기반이다. **유용한 잔차 bound, 전체 15성분 관측 추론, 전역 비선형 MES 정리, 학술적 신규성은 아직 unresolved다.**

증명 상세: `agent_kinematics.md`, `agent_statistics.md`. MES 원문/코드 대조: `sources_agent/MES_BOUND_SOURCE_REVIEW.md`. 재현 entry point와 다음 DAG는 `README.md`, `RESEARCH_DAG.json` 참조.
