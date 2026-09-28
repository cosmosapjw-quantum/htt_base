# I1 — 정확한 복사 residual에서 time-jet 소거 전단 조합으로

2026-09-28. 근거: R2의 exact weak law와 R5의 fixed homogeneous finite-tilt affine geometry를 합성한 **derived** 결과. 가벼운 Wolfram fixture 검산은 별도 원시 증거에 있다. 새로운 MES 보편정리, 관측 추론, 신규성 또는 repository admission을 주장하지 않는다.

## 1. 이번에 선택한 대상과 전제

한 사건에서 R5의 공간균질 branch, geodesic normal과 Fermi transported triad, 고정 geometry와 tilt \(p=\beta\), \(|p|<1\)을 쓴다. \(U^aU_a=-c^2\), \(a=A/c\), \(H=\Theta/3\), \(\sigma\), \(\omega\)의 단위는 모두 s\(^{-1}\)다. 와도는 derivative-first \(\Omega_{ij}=D_{[i}U_{j]}\), \(\omega_i=\epsilon_{ijk}\Omega_{jk}/2\), \(\epsilon_{123}=1\)이다. 전파 방향은 \(e=-n\). 아래 \(B\)는 brightness이며 R5 deformation matrix가 아니다.

\[
\mathcal C_p z:=\operatorname{STF}(p z^T),\qquad
Z:=\sigma-\mathcal C_p a . \tag{1}
\]

STF는 대칭화의 1/2와 trace 제거의 1/3을 포함한다. \(Z\)는 physical shear 자체가 아니다. R5에 의해 normal-frame geometry/\(q=cK\)/\(p\)를 고정하고 tilt time jet \(b=cE_0p\)만 바꾸면
\[
\delta a=z,\quad\delta H=p\cdot z/3,\quad
\delta\sigma=\mathcal C_p z,\quad
\delta\omega=\tfrac12p\times z,
\]
따라서 \(\delta Z=0\)이다. 같은 branch에서는
\[
\omega=w_0+\tfrac12p\times a,
\quad w_0=S_{\rm boost}w_C
\tag{2}
\]
가 고정 geometry의 정확한 compatibility 식이다. 일반 congruence에 (2)를 강요하지 않는다.

입력 brightness는 **target rest frame 자체의** 비음수 \(L^1(S^2)\) 밀도 \(B(e)\), \(\rho=\int B\,d\Omega>0\)이다. Bolometric energy integration에는 \(E^4f\to0\) endpoint가 필요하다. Planck spectrum은 가정하지 않는다. 관측자 frame의 유한 low-ell 온도 자료로 이 입력 전체를 정확히 얻었다는 전제도 없다. 실제 finite boost에는 source spectrum, angular tail, mask 및 공통 frame 변환 계약이 별도로 필요하다.

## 2. 이미 채택된 R2 식의 실제 합성

\(m=\int Be\), \(M=\int Bee^T\), \(M_4=\int Be^{\otimes4}\), \(\pi=M-\rho I/3\)와
\[
L_B(S)=SM+MS-M_4:S-I(M:S)/3
\]
를 사용한다. 구면 적분 기호에는 \(d\Omega\)를 생략했다. R2의 정확한 순간 운동학 항은
\[
\begin{aligned}
J_0&=4\rho H+\sigma:M+2a\cdot m,\\
J_1&=4Hm+\sigma m+\omega\times m+(\rho I+M)a,\\
J_2&=4H\pi+L_B(\sigma)+2\operatorname{STF}(a m^T)
       +[R_\omega,M],\qquad R_\omega v=\omega\times v.
\end{aligned}\tag{3}
\]
여기서 \(J_\ell=r_\ell\)의 우변 \(r\)은 충돌·복사 시간/공간 미분·선언한 frame connection을 옮긴 **공동 residual**이다. 단일 순간 brightness가 \(r\)을 측정해 주지 않는다. 미지 derivative/source를 0으로 놓지 않는다. (3)은 hierarchy의 시간발전 closure가 아니며 \(\ell\le4\) target-frame 순간 모멘트로 정해지는 operator다.

\(X=(H,a,\sigma)\in\mathbb R\oplus\mathbb R^3\oplus\mathrm{STF}_2\)를 선언한 Euclidean/Frobenius 직합 내적에 놓는다. 이 내적은 비교를 위한 수학적 좌표이며 데이터 covariance가 아니다. (2)를 (3)에 대입하고 알려진 offset
\[
b_0=(0,\ w_0\times m,\ [R_{w_0},M])
\]
을 빼서 다음 **명시적인 9×9** 연산자를 얻는다:
\[
\begin{aligned}
(\mathsf A_{B,p}X)_0&=H+\frac{\sigma:M+2a\cdot m}{4\rho},\\
(\mathsf A_{B,p}X)_1&=\frac3{4\rho}
 \{4Hm+\sigma m+\tfrac12(p\times a)\times m+(\rho I+M)a\},\\
(\mathsf A_{B,p}X)_2&=\frac{15}{8\rho}
 \{4H\pi+L_B(\sigma)+2\operatorname{STF}(a m^T)
                  +[R_{(p\times a)/2},M]\}.
\end{aligned}\tag{4}
\]
\[
\widehat r=\left(\frac{r_0}{4\rho},\frac{3(r_1-b_{0,1})}{4\rho},
                   \frac{15(r_2-b_{0,2})}{8\rho}\right),
\quad \mathsf A_{B,p}X=\widehat r .\tag{5}
\]
각 항의 단위는 s\(^{-1}\)다. (4)는 finite \(p\)에서 정확하며 \(\sigma a\) 등을 버린 retained expansion이 아니다. 다만 branch의 (2), target-frame moments, residual이 모두 같은 물리 상태에서 와야 한다.

\(\mathsf A\)가 가역이면
\[
\boxed{Z=\mathsf P_p\mathsf A_{B,p}^{-1}\widehat r,
\qquad \mathsf P_p(H,a,\sigma)=\sigma-\mathcal C_pa.}\tag{6}
\]
이는 **residual-known conditional inverse**이다. 역산 가능성이 source/jet 관측을 만들지는 않는다. Singular \(\mathsf A\)에서도 \(\mathsf P_p\ker\mathsf A=0\)이면 consistent residual에 대한 target만은 유일할 수 있다. 아니라면 feasible target image를 집합으로 유지한다. Nonempty 조건과 실제 물리 domain의 제약을 삭제하지 않는다.

## 3. 등방 순간장의 완전한 식과 꼭 필요한 residual

\(B=\rho/(4\pi)\)이면 \(m=0\), \(M=\rho I/3\), \(L_B(S)=8\rho S/15\). 따라서 \(\mathsf A=I_9\), \(b_0=0\)이고
\[
\boxed{Z=\frac{15}{8\rho}r_2-rac3{4\rho}\operatorname{STF}(p r_1^T).}\tag{7}
\]
\(r_0\)는 이 경우 \(Z\)에 필요하지 않다. Expansion의 b-free 조합은 부수적으로 \(H-p\cdot a/3=(r_0-p\cdot r_1)/(4\rho)\)다. 순간 등방성은 모든 사건에서 등방이라는 EGS 전제가 아니며 \(\sigma=a=0\)을 뜻하지 않는다.

**Dipole residual을 모르면 어떻게 되는가?** \(r_2\)만 고정하고 \(a\)를 자유롭게 허용하면 \(\sigma=15r_2/(8\rho)\)는 고정되지만 \(Z\)는 \(-\operatorname{im}\mathcal C_p\) 방향으로 변한다. 이 family에서는 \(q\)가 고정된다고 주장하지 않는다. R5 inverse로 각 \((H,\sigma,a)\)에 맞는 symmetric \(q\)와 \(b\)를 재구성할 수 있는 unconstrained geometric-jet domain을 사용한다.
\[
\|\mathcal C_p z\|_F^2=\frac{|p|^2|z|^2}{2}+\frac{(p\cdot z)^2}{6},
\quad
\mathcal C_p^*\mathcal C_p=\frac{|p|^2}{2}I+\frac{pp^T}{6}.\tag{8}
\]
그러므로 \(p\ne0\)에서는 rank 3이고, \(Z\)의 5개 선형 성분 중 단지 **2차원 quotient**만 \(r_2\)만으로 유일하다. \(\mathcal Q_p=I-\mathcal C_p(\mathcal C_p^*\mathcal C_p)^{-1}\mathcal C_p^*\)라 쓰면
\[
\mathcal Q_pZ=\frac{15}{8\rho}\mathcal Q_pr_2.\tag{9}
\]
이는 \(p\)에 수직인 평면의 두 transverse STF 성분이다. \(p=0\)에서는 \(\mathcal C_p=0\), 전체 5성분이 복원된다. \(p\to0\)이나 자유 \(a\)를 먼저 무한 범위로 두는 순서는 교환되지 않는다. 유한 \(\|a\|\)가 따로 주어지면 불확실성은 \(|p|\)와 함께 줄어든다.

따라서 “time jet를 소거한 target이므로 quadrupole 식 하나로 충분하다”는 주장은 틀리다. **target의 nuisance 불변성과 관측 operator의 nuisance 소거는 다른 조건**이다. 이 등방 limit에서는 \(r_1\)의 full 3-vector 또는 \(\mathcal C_pr_1\)의 유계 joint 정보가 추가돼야 전체 \(Z\)를 제한할 수 있다. Fixed Einstein–matter/source/time interval 조건은 이 자유 domain을 더 줄일 수 있으며 이 결과가 모든 물리 cosmology의 no-go는 아니다.

## 4. 오차·source 예산을 실제로 어디에 넣는가

Fixed \(\rho,p\)의 등방식에서 공동 residual error set \(\mathcal E_{12}\)의 target error는 정확히
\[
\mathcal E_Z=\left\{\frac{15}{8\rho}\delta r_2-rac3{4\rho}\mathcal C_p\delta r_1:
(\delta r_1,\delta r_2)\in\mathcal E_{12}\right\}.\tag{10}
\]
독립성을 가정하지 않는다. Marginal ball bounds만 알면 안전한 triangle 상계는
\[
\|\delta Z\|_F\le\frac{15}{8\rho}\epsilon_2+
\frac3{4\rho}\sqrt{\frac23}|p|\epsilon_1.\tag{11}
\]
여기서 \(\epsilon_\ell\)는 residual norm budget이며 MES temperature amplitude \(\epsilon_\ell\)와 동일하지 않다. 실제 값은 이번 입력에 없다. 식 (11)의 이름 혼동을 막기 위해 실행 계약에서는 `delta_r1_radius`, `delta_r2_radius`를 쓴다. Bounds가 없으면 유한 관측 interval을 출력할 수 없다. Source를 복사식 자체로 추정해 다시 독립 예산으로 넣지 않는다.

일반 brightness에서는 \(E=\mathsf A-I\), \(\eta=\|E\|_2<1\)이 **충분조건**이다. Neumann bound와 (8)로
\[
\|\delta Z\|_F\le
\frac{\sqrt{1+2|p|^2/3}}{1-\eta}\|\delta\widehat r\|.\tag{12}
\]
\(\eta\ge1\)은 실패 증명이 아니다. 직접 \(s_{\min}(\mathsf A)>0\)와 \(\|\mathsf P_p\mathsf A^{-1}\|\)를 평가할 수 있다. Norm은 앞서 선언한 수학적 직합 norm이며 statistical whitening과 혼동하지 않는다.

\(B,p,w_0,\rho\)가 불확실하면 (12)는 fixed-operator 오차만 다룬다. 올바른 결과는 동일 \(\xi\)에 대해 (4)–(6)을 동시에 만족하는 공동 집합의 image/union이다. 고정한 surrogate operator의 오차 bound를 input uncertainty 전체로 확대하지 않는다. Reference denominator도 같은 \(\xi\)에서 전파한다.

## 5. 현재 실행한 판별 검산

Wolfram 계산은 물리량 단위를 임의로 없애지 않고 coefficient algebra의 \(\rho\)-정규화에 해당한다. 밝기 fixture는
\[
B(e)=\frac{\rho}{4\pi}\left[1+\frac{e_z}{5}+
\frac{3e_z^2-1}{10}\right],\quad
p=(1/5,2/5,2/5),\quad |p|=3/5,\quad w_0=0.\tag{13}
\]
대괄호는 \(\ge7/10>0\), 평균 1이며 axis-aligned tilt가 아니다. \(w_0=0\)인 spatially Abelian branch의 순간 fixture다. Einstein–matter solution이나 observed CMB fit을 제공하지 않는다.

Frobenius-orthonormal STF basis와 rational spherical monomial integral로 (i) R2 weak form 직접 적분과 (ii) (3)의 moment formula를 별도로 조립했다. 9개 잔차는 정확히 0이다. 등방 response는 정확히 \(I_9\), fixture response는
\[
\det\mathsf A=\frac{25945272314037}{26260937500000}\ne0,
\quad\operatorname{rank}\mathsf A=9,
\quad\|E\|_F^2=\frac{1164053}{5040000}<1.\tag{14}
\]
\(\|E\|_2\le\|E\|_F\simeq0.480586\)이므로 (12)의 sufficient certificate가 닫힌다. 이것은 이 fixture에 대한 판별 결과이지 모든 positive anisotropic brightness의 rank 정리가 아니다. Positive density만으로 전체 9×9 invertibility를 이번에 증명하지 않았다.

General-symbolic \(p,z\)로 (8)의 norm와 Gram 식을 확인했고, \(\mathsf P_p\delta X=0\), 누락 dipole의 target ambiguity rank 3, quotient 차원 2도 확인했다. 구면 normalization 1/3, 1/5, 1/15, 1/7과 \(\Gamma(7/2)\)를 별도로 확인했다. Special Functions plugin의 60-digit gamma 값은 Wolfram 표시값과 반올림 정밀도 내에서 일치하며 일반 증명을 대신하지 않는다.

최초 실행 V1은 exact radical coefficient를 RawJSON으로 출력할 때 `Export::jsonstrictencoding`으로 실패했다. 출력 직렬화만 InputForm string 값으로 바꾸어 V2에서 결과를 회수했다. V1 raw와 code, 최소 진단, 수정 후 raw를 모두 보존했다. 이는 물리식/허용오차 수정이 아니며 V1을 PASS로 소급 표기하지 않는다. `isError=false`만으로 성공을 판정하지 않았다.

## 6. 이 결과의 채택 범위와 남은 단계

새로 연결된 것은 기존 exact R2 순간식과 R5 fixed-tilt geometry의 구체적 target response다. 기존 L_B coercivity, rank9 geometric theorem, rank8 retained timejet theorem을 새로운 발견으로 반복하지 않았다. 관측 광학 drift는 emitter/observer와 광로의 공동 문제이며 ray generator를 그대로 proper motion으로 쓰지 않는 기존 경계를 유지한다. 원문 근거: Marcori et al., arXiv:1805.12121 §II; Heinesen–Korzyński, arXiv:2406.06167v1 §II–III,IX. 이 문헌은 (6)의 프로젝트별 조합이 새롭다는 근거가 아니다.

다음 최소 물리 입력은 target-frame \((B,\rho,p,w_0)\)와 (10)의 **같은 상태에서 오는 residual 조합에 대한 유용한 예산**이다. 특정 source model 또는 independent optical/time data가 이를 제공하는지부터 판별한다. 현재 첨부와 최신 main은 그 수치 budget을 공급하지 않는다. 단일 정적 CMB sky만으로는 이 gap이 닫히지 않는다.

상태: analytic response **derived**; 명시 fixture **symbolically checked**; source/jet budget **unresolved**; real-data likelihood/empirical percentage **not run / HOLD**; production implementation와 repository CAS4 admission **NOT_RUN**. 전체 프로젝트 gate나 과거 판정을 변경하지 않는다.
