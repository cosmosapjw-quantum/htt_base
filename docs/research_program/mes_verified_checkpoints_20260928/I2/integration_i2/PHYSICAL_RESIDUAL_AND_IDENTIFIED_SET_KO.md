# I2 — 순간 등방 복사와 Einstein–Vlasov 전단: 반례족과 조건부 허용집합

2026-09-28. I1의 후속 **derived** 결과다. 기존 R2의 exact weak law와 Einstein–Vlasov 원문 식을 사용하며, 새 학술적 신규성이나 관측적 발견을 주장하지 않는다. 최종 독립 판정은 `INDEPENDENT_DECISION.json`을 따른다.

## 1. 질문과 선택한 분기

I1은 복사 residual을 알 때
\[
Z=\sigma-\operatorname{STF}(p a^T),\qquad a=A/c
\]
를 복원했다. 등방 순간장에서는 \(Z=15r_2/(8\rho)-3\operatorname{STF}(p r_1^T)/(4\rho)\)다. 이번 질문은 물리적으로 acceleration을 없애면 아직 미지인 residual도 제한되는가이다.

다음 분기를 명시적으로 선택한다. Einstein 중력, \(\Lambda=0\), Bianchi I, collisionless massless radiation만을 응력원으로 사용한다. Target \(U=\partial_t\)는 homogeneous slice의 측지 정규 congruence이고 \(U\cdot U=-c^2\), \(p=0\), \(a=0\), \(\omega=0\)다. 따라서 이 분기에서는 정확히 \(Z=\sigma\)다. Radiation을 dust로 취급한 것이 아니며, 이 특수 분기로 finite-tilt 일반 문제를 대체하지 않는다.

서명은 \((-+++ )\), proper time \(t\)는 초다. 대각 frame에서
\[
ds^2=-c^2dt^2+\sum_{i=1}^3 b_i(t)^2(dx^i)^2,\qquad
H_i=\dot b_i/b_i,\quad H=\tfrac13\sum_iH_i,\quad
S=\operatorname{diag}(H_i-H).
\tag{1}
\]
\(b_i(t_0)=1\)로 좌표 scale을 고정한다. \(S=\sigma\)는 rate 단위의 전단이며 \(\|S\|_F^2=\operatorname{tr}(S^2)\); 흔히 쓰는 shear scalar는 이 값의 절반이다. 물리적 회전으로 일반 STF 초기 텐서를 다룰 수 있다.

## 2. 실제 물리 source를 닫기

보존되는 covariant spatial momenta를 \(q_i\)라 쓰고
\[
f(t,q_i)=f_0(q_i)=F(|q|),\quad F\ge0,
\tag{2}
\]
로 둔다. \(F\)는 0이 아니고 매끄러우며 \(0<q_{\min}<|q|<q_{\max}<\infty\) 안에 compact support를 갖는다. 이는 massless Vlasov 식의 정확한 해 형태다. Collision term은 실제로 0이며 임의의 source를 radiation equation에 맞춰 조절하지 않는다.

물리적 운동량 \(p_i^{\rm phys}=q_i/b_i\), 에너지 \(E=c\sqrt{\sum_iq_i^2/b_i^2}\)다. Polarization degeneracy를 포함한 phase-space 상수를 \(C_\gamma=2/(2\pi\hbar)^3\)라 하면
\[
\rho(b)=\frac{C_\gamma}{b_1b_2b_3}\int F(|q|)\,c\sqrt{\sum_j q_j^2/b_j^2}\,d^3q,
\]
\[
P_i(b)=\frac{C_\gamma}{b_1b_2b_3}\int F(|q|)\,
\frac{c q_i^2/b_i^2}{\sqrt{\sum_j q_j^2/b_j^2}}\,d^3q,
\qquad\sum_iP_i=\rho.
\tag{3}
\]
\(\rho\)와 \(P_i\)는 energy density와 압력, 단위 J m\(^{-3}\)다. \(F\)에 degeneracy를 이미 흡수했다면 \(C_\gamma\)를 그에 맞춰 바꾸며 아래 관계는 동일하다. 초기에는 \(P_i=\rho_0/3\), momentum density는 0이다. 이후 anisotropic stress를 \(P_i=\rho/3\)로 고정하지 않는다.

\(\kappa=8\pi G/c^2\)로 놓으면 evolution과 constraint는
\[
\dot b_i=b_iH_i,\qquad
\dot H_i=-3HH_i+\kappa P_i(b),
\qquad
3H^2=\kappa\rho+\tfrac12\|S\|_F^2.
\tag{4}
\]
여기서 \(\kappa\)는 \(8\pi G/c^4\)라는 Einstein tensor 계수와 다른, **rate 방정식용 표기**다. Rendall §2 Eqs. (2.1)–(2.14)의 \(k^i{}_j=-\operatorname{diag}(H_i)\), \(\operatorname{tr}k=-3H\)를 사용하고 \(c,G\)를 복원했다. 원문의 자연단위나 mean-curvature 부호를 그대로 혼합하지 않았다.

국소 해의 존재는 직접 확인할 수 있다. \(b_i>0\)인 임의의 compact 근방에서 (3)의 integrand와 metric 미분은 \(F\)의 고정 annulus support에서 유계다. 따라서 \(\rho(b),P_i(b)\)는 매끄럽고 (4)는 매끄러운 6차원 ODE다. 표준 국소 존재·유일성 정리를 적용할 수 있다. Reflection symmetry로 off-diagonal stress와 momentum은 0으로 유지된다.

또한 \(\dot\rho=-3H\rho-\sum_iH_iP_i\)이고,
\[
\mathcal C=(\sum_iH_i)^2-\sum_iH_i^2-2\kappa\rho
\quad\Longrightarrow\quad
\dot{\mathcal C}=-2(\sum_iH_i)\mathcal C.
\tag{5}
\]
초기 constraint가 이후에도 보존되므로 이 구성은 임의로 지정한 배경 위 test radiation에 그치지 않는다. **선언한 물질 모형의 국소 Einstein–Vlasov 해**다. 이는 실제 numerical evolution이나 공통 시간폭의 전역 해를 계산했다는 뜻은 아니다.

## 3. 등방 snapshot이 time jet를 결정하지 않음

Bolometric brightness \(B\)는 energy density per solid angle로 정규화한다. \(\rho=\int B\,d\Omega\), \(\pi=\int B(ee^T-I/3)d\Omega\)다. \(q_i=b_i(E/c)e_i\)를 (2)에 넣고 에너지 적분 변수를 바꾸면
\[
B(t,e)=\frac{\rho_0}{4\pi}
\left(\sum_i b_i(t)^2 e_i^2\right)^{-2},\qquad |e|=1.
\tag{6}
\]
이 식은 \(F\)의 radial form과 유한 에너지 moment만 사용한다. Blackbody spectrum은 필요하지 않다. Compact support 때문에 R2의 \(E^4f\to0\) 양 끝점 조건도 충족된다. (6)은 metric 해가 존재하는 구간의 정확한 운동학 표현이며, 지수함수 scale factor를 Einstein 해라고 임의 지정하지 않았다.

초기 brightness와 모든 비등방 multipole은
\[
B(t_0,e)=\rho_0/(4\pi),\qquad m(t_0)=0,\quad\pi(t_0)=0
\]
로 같다. 하지만
\[
\dot B(t_0,e)=-4\frac{\rho_0}{4\pi}\{H+S:ee\},\quad
\dot\rho(t_0)=-4H\rho_0,\quad
\boxed{\dot\pi(t_0)=-\frac8{15}\rho_0S.}
\tag{7}
\]
마지막 식은 \(\langle e_ie_je_ke_l\rangle=(\delta_{ij}\delta_{kl}+\delta_{ik}\delta_{jl}+\delta_{il}\delta_{jk})/15\)로 직접 적분한다. R2의 순간 등방 weak law와도 부호·계수가 일치한다. 이 frame에서는 homogeneous transport residual이 \(r_2=-\dot\pi=8\rho_0S/15\)다. 충돌·공간항을 제거해도 **시간미분은 사라지지 않는다**.

## 4. 같은 snapshot과 임의의 절대 전단을 갖는 반례족

고정 \(F,\rho_0>0\)와 \(\lambda\ge0\)에 대해
\[
S_\lambda=\lambda\operatorname{diag}(2,-1,-1),\qquad
H_\lambda=\sqrt{\lambda^2+\kappa\rho_0/3}
\tag{8}
\]
를 초기자료로 선택한다. 식 (4)의 constraint가 정확히 성립하며 세 방향 팽창률은 \(H_\lambda+2\lambda,H_\lambda-\lambda,H_\lambda-\lambda\)로 모두 양수다. 따라서 수축축의 존재를 이용해야만 얻는 반례도 아니다.

모든 \(\lambda\)에서 complete instantaneous \(f_0\)와 \(B_0\)는 동일하지만
\[
\|Z_\lambda\|_F=\|S_\lambda\|_F=\sqrt6\lambda\to\infty.
\tag{9}
\]
그러므로 **이 domain에서 정적인 등방 복사 자료만의 함수인 유한한 절대 전단 상한은 존재하지 않는다.** 이것은 source/jet를 자의적으로 지정하는 형식적 모호성이 아니라 Einstein–matter constraint를 만족하는 국소 해들의 모호성이다.

무한히 변하는 것은 dimensional shear다. 동시에 \(H_\lambda\)도 변하며
\[
\frac{\|S_\lambda\|_F}{H_\lambda}\to\sqrt6,
\qquad
\frac{\|S_\lambda\|_F}{\Theta_\lambda}\to\sqrt{\frac23},
\quad\Theta=3H.
\tag{10}
\]
따라서 정규화 전단이 무한하다는 결론은 틀리다. 정확한 등방 snapshot조차 normalized shear를 0 또는 작은 값으로 강제하지 못한다는 것이 핵심이다. 공통 관측 \(H\), 동일한 past light cone/source history, 실재 CMB spectrum 및 recombination 역사에 대한 적합성은 이 반례에 포함하지 않는다. 큰 \(\lambda\)마다 존재구간이 짧아질 수 있으며 균일한 관측 시간폭도 주장하지 않는다.

이는 EGS/almost-EGS와 충돌하지 않는다. 단일 시간의 등방성과 시공간 영역에서의 등방성·작은 derivative 조건은 다르다. Ellis–van Elst §8.5.1 Eqs. (283)–(284)는 derivative smallness를 별도 전제로 명시한다. 이 반례의 (7)은 바로 그 미충족 조건을 보여준다.

## 5. 독립적인 H 정보가 들어오면 닫히는 허용집합

이제 동일 물리 상태의 \((H,\rho)\)가 별도 정보로 제한된다고 하자. \(H>0,\rho>0\)이고 mean expansion만 요구할 때 정확한 순간 전단 집합은
\[
\boxed{\mathcal S(H,\rho)
=\{S\in\mathrm{STF}_2:\|S\|_F^2=6H^2-2\kappa\rho\}.}
\tag{11}
\]
우변이 음수면 **empty**, 0이면 \(\{0\}\), 양수면 5차원 STF 공간의 4차원 sphere다. 양의 반지름에서 tensor 방향과 eigenvalue shape를 식별하지 못한다. 임의의 해당 \(S\)를 diagonalize하고 radial 초기분포를 유지하면 §2의 국소 구성이 적용된다. 모든 방향별 팽창을 추가로 요구한다면 \(HI+S\succ0\)와 교집합을 취해야 한다; (11)의 sphere 전체를 그대로 사용할 수 없다.

관측/물리 input이 공동 집합 \(\mathcal D\subset\{(H,\rho):H>0,\rho>0\}\)라면
\[
\mathcal S(\mathcal D)=\bigcup_{(H,\rho)\in\mathcal D}\mathcal S(H,\rho).
\tag{12}
\]
\(H\)와 \(\rho\)의 상관은 이 union에서 유지한다. Rectangular envelope \(0<H\le H_+\), \(\rho\ge\rho_->0\)만 주어지면 비어 있지 않은 허용집합에 대해
\[
\|Z\|_F\le\sqrt{6H_+^2-2\kappa\rho_-}.
\tag{13}
\]
이 식의 radicand가 음수면 입력과 모형이 양립하지 않는 것이므로 \(\sqrt{\max(0,\cdot)}\)로 조용히 0을 반환해서는 안 된다. 양수인 경우에도 원 \(\mathcal D\)가 비어 있거나 correlation 때문에 feasible pair가 없을 수 있다. Rectangle bound는 exact joint set을 대체하지 않는 안전한 외접 상계다.

식 (11)–(13)은 **모형과 독립적인 same-state expansion/energy 입력에 조건부인 결과**다. 정적 CMB anisotropy에서 얻은 MES 상한이 아니며, small almost-FLRW radius를 보장하지 않는다. 실제 \(H_+,\rho_-\) 자료는 이번에 취득하지 않았다. FLRW/ΛCDM에 고정된 \(H_0\) posterior를 이 Bianchi I branch에 검토 없이 대입하지 않는다. 같은 radiation 방정식에서 역산한 \(H\)나 \(\dot\pi\)를 독립 측정처럼 다시 넣는 것도 금지한다.

## 6. 실제 검산과 근거 수준

`verification/EXACT_BIANCHI_I_WITNESS.wl`을 이번 턴 Wolfram에서 실제 실행했다. 일반 STF의 \(\dot\pi+8\rho S/15\), Hamiltonian 분해, (8)의 constraint, constraint propagation 잔차가 정확히 0이다. 모든 방향 팽창의 양성은 True, normalized-shear limit는 \(\sqrt6\)이다.

Brightness derivative 비교의 첫 raw 출력은 \(-4H(e\cdot e-1)\)였다. 이는 선언한 단위구면에서는 0이지만 주변 \(\mathbb R^3\) 전체의 항등식은 아니다. 검산 원문과 이 domain reduction을 함께 보존한다. 이 출력을 무조건 비영 오류 또는 주변공간의 zero identity로 표기하지 않는다. 추가로 이 비교 하나만 구면 다항식 ideal로 환원해 numerator remainder 0을 실제 확인했다(`UNIT_SPHERE_REDUCTION.wl`, `UNIT_SPHERE_RAW.json`). 분모는 \((e\cdot e)^3\)라 단위구면에서 1이다. 완료된 전체 fixture를 재실행하지 않았다.

직접 유도: (3)–(13), 특히 annulus support의 smooth ODE local existence와 counterfamily/target set. 문헌 지지: Bianchi I Einstein–Vlasov 기본 식 및 almost-EGS의 derivative 전제. Exact-symbolic checked: 명시한 algebraic identities와 moment 계수. 미실행: evolution solver, 일반 finite-tilt Einstein–matter 존재 정리, four-axis repository admission, 실관측 inference. 현재 결과를 다른 R9/R10 gate에 전파하지 않는다.

## 7. 다음 최소 작업

이번 루프는 source를 collisionless로 닫아도 snapshot만으로 residual이 닫히지 않는다는 점과, 독립 \((H,\rho)\) 입력이 주는 제한된 양의 결과를 함께 고정한다. 다음은 새 formalism을 늘리는 것이 아니라 **같은 congruence에서 독립적으로 얻은 expansion/optical shear 또는 radiation time-jet 입력 하나**를 선택하는 일이다. Norm만 필요하면 joint \((H,\rho)\) 경로, tensor morphology가 필요하면 directional optical/radiation-jet 경로를 구별한다. 데이터와 물리 모형이 정해지기 전에는 수치 percentage나 likelihood를 만들지 않는다.

원전: [Rendall, arXiv:gr-qc/9505017v1, §2](https://arxiv.org/pdf/gr-qc/9505017v1); [Ellis–van Elst, arXiv:gr-qc/9812046v5, §8.5.1](https://arxiv.org/pdf/gr-qc/9812046v5). 실제 읽은 범위와 보조 경로는 `source_review/LITERATURE_LEDGER.md`에 있다.
