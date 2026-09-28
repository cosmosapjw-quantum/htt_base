# MES R5 — 고정 tilt에서의 정확한 운동학 affine operator

2026-09-27 KST. 후보 유도자 `/root/r5_joint_operator`. 근거 상태: **derived**. R4 `closure_derivation.md` §7, `MES_R4_REPORT_KO.md`, `INDEPENDENT_REVIEW.md`, 하네스 `PROJECT_INSTRUCTIONS.md`, `docs/MODEL_ROUTING.md`, template `state/RESEARCH_STATE.md`를 읽었다. 원 하네스 template의 NOT_RUN은 과거 실행 증거가 아니다. 최종 승격은 별도 독립 reviewer의 소유다. 모델 신원이나 ultra 설정을 인증하지 않는다.

## 1. 고정 입력과 정확한 적용 범위

공간균질 spacelike slice, geodesic unit normal $n=E_0$, normal을 따라 Fermi–Walker transported orthonormal triad $E_i$를 쓴다. 모든 $E_A$는 길이 미분이고 계량은 $(-+++)$. 공간 Lie 구조상수와 순간 metric에서 얻는 orthonormal 구조상수 $f^k{}_{ij}$, Koszul 연결 $\gamma_{ij}{}^k=\langle\nabla^{(3)}_{E_i}E_j,E_k\rangle$은 R4 정의를 따른다. 미분 방향은 첫 index다.

\[
K_{ij}=\langle\nabla_{E_i}n,E_j\rangle=K_{ji},\qquad q=cK,
\qquad U=cg(E_0+p_iE_i),\quad p=\beta,\quad g=(1-p^2)^{-1/2},\quad b=cE_0p.
\]

$q,b$의 단위는 s$^{-1}$, $p$는 무차원, $|p|<1$, $E_ip_j=0$. 이는 finite tilt의 정확한 geometric jet 계산이다. 작은 비등방 전개도, Einstein/matter field equations도 이 절에서 사용하지 않는다. 반대로 lapse가 공간에 의존하거나 triad time rotation이 있으면 R4의 full connection adapter에 해당 성분을 추가해야 하며 아래 축약식은 그대로 적용하지 않는다.

rest frame의 orientation은 canonical proper Lorentz boost로 정한다. 다음 두 symmetric positive matrices는 $p=0$에서도 매끄럽다.

\[
S=I+\frac{g^2}{g+1}pp^T,\qquad
T=S^{-1}=I-\frac{g}{g+1}pp^T,
\qquad Sp=gp,\quad Tp=p/g,\quad\det S=g.
\tag{1}
\]

boosted rest triad는

\[
e'_i=gp_iE_0+S_{ij}E_j,\qquad
\langle e'_i,e'_j\rangle=\delta_{ij},\quad \langle e'_i,U\rangle=0.
\tag{2}
\]

여기서 $B_{ij}=\langle\nabla_{e'_i}U,e'_j\rangle$, $a_i=A(e'_i)/c$이며 $A=\nabla_UU$. 따라서 $B,a$는 모두 rate 단위다. 원문의 부호 약속에 따라

\[
\Theta=\operatorname{tr}B,\quad
\sigma=\tfrac12(B+B^T)-\Theta I/3,\quad
\Omega=\tfrac12(B-B^T),\quad
\omega_i=\tfrac12\epsilon_{ijk}\Omega_{jk},\quad\epsilon_{123}=+1.
\tag{3}
\]

## 2. rest-frame gradient와 acceleration의 explicit 식

geometry-only matrix를

\[
L_{ij}=-c\gamma_{ij}{}^kp_k,\qquad Z=q+L
\tag{4}
\]

로 둔다. Metric compatibility $\gamma_{ijk}=-\gamma_{ikj}$로 $Lp=0$이다. Normal-frame covariant gradient $F_{AB}=\nabla_{E_A}U_B$는 직접 미분하여

\[
F=g\begin{pmatrix}
-g^2(p\cdot b)&b^T+g^2(p\cdot b)p^T\\
-qp&q+L
\end{pmatrix}.
\tag{5}
\]

왼쪽 위 scalar와 아래쪽 column은 covariant time index의 부호를 포함한다. $F_{AB}U^B=0$은 $Zp=qp$로 확인된다. Eq.(2)의 두 spatial boost를 적용하고, $S-gpp^T=T$를 쓰면

\[
\boxed{B=gSZT+g^2p(Sb)^T},\qquad
\boxed{a=g^2\{Sb+TZ^Tp\}}.
\tag{6}
\]

둘째 식은 $a_j=(U^A/c)F_{AB}e_j'{}^B$이다. 이를 첫째에 대입하면 더 유용한 동일식이 나온다.

\[
\boxed{B=gTZT+pa^T.}
\tag{7}
\]

이로써 expansion, shear, vorticity, acceleration을 모두 남기는 finite affine map이 구성된다. 예컨대 trace는

\[
\Theta=g\operatorname{tr}(q+L)+g^3p\cdot b.
\tag{8}
\]

Eq.(6)의 $B$를 Eq.(3)에 넣으면 $\sigma$의 5개와 $\omega$의 3개 성분도 추가 미분 없이 산출된다. $\beta$는 이 map의 conditioning variable이며 최종 공동 상태에서 관측 nuisance/target로 함께 보존한다.

## 3. $12\times9$ affine operator의 명시적 열과 정확한 rank

대칭 행렬 공간에 Frobenius-orthonormal basis $H_\alpha$, $\alpha=1,\ldots,6$를 택하고 $q=\sum_\alpha q_\alpha H_\alpha$라 하자. 세 diagonal unit matrices와 세 $(e_ie_j^T+e_je_i^T)/\sqrt2$를 써도 된다. 입력

\[
j=(q_1,\ldots,q_6,b_1,b_2,b_3)^T
\tag{9}
\]

는 9차원이다. 출력 carrier는 $k=(\Theta,\sigma_{\mathrm{STF},1\ldots5},\omega_{1\ldots3},a_{1\ldots3})$, 즉 12차원으로 고정한다. $\mathcal E(B,a)$를 Eq.(3)의 trace/STF/axial/acceleration extraction이라 쓰면

\[
k=k_C+\mathsf A(p)j,
\quad k_C=\mathcal E(gSLT,g^2TL^Tp),
\tag{10}
\]

이고 각 열은 완전히 명시적으로

\[
\begin{aligned}
\mathsf A_{q,\alpha}&=\mathcal E(gSH_\alpha T,g^2TH_\alpha p),\\
\mathsf A_{b,r}&=\mathcal E(g^2p(Se_r)^T,g^2Se_r).
\end{aligned}
\tag{11}
\]

고정 $p$에서 선형 part $\mathsf A$는 C나 h에 직접 의존하지 않고 geometry는 affine offset $k_C$에 들어간다. 이것은 선택한 orthonormal basis 및 geodesic/Fermi frame에서의 진술이다. 입력 covariance나 기저 계수 norm을 바꾸면 그에 맞는 carrier metric을 함께 변환한다.

**정리.** 모든 $|p|<1$에서 $\operatorname{rank}\mathsf A(p)=9$이다.

**증명.** $B,a$를 알면 Eq.(7)에서

\[
\boxed{q=g^{-1}S(B-pa^T)S-L},\qquad
\boxed{b=T(a-B^Tp)}.
\tag{12}
\]

두 번째 식은 Eq.(6)에서 $B^Tp=g^2TZ^Tp+g^2p^2Sb$를 빼고 $g^2-g^2p^2=1$을 사용해 얻는다. 더 직접적으로 $a-B^Tp=Sb$이다. 따라서 $j\mapsto(B,a)$는 injective이며 Eq.(3)의 $(B,a)\leftrightarrow k$ 변환도 가역이므로 rank는 9다. $p=0$에서도 $B=q,a=b$로 같은 결과다. □

이 rank는 **고정 homogeneous jet의 자유도**이다. sky/거리 관측 응답의 식별 rank와 같다는 주장이 아니다. R3의 일반 관측 응답 ideal rank 12와 모순되지 않는다. 관측 map을 이 9차원 affine submanifold와 합성해야 한다. $p$가 불확실하면 하나의 affine subspace가 아닌 $p$-dependent image들의 공동 집합이다.

## 4. 세 exact affine relations: 와도·가속도·Lie geometry

Torsion-free relation에서

\[
L_{[ij]}=-\frac c2 f^k{}_{ij}p_k,
\qquad (w_C)_i=-\frac c4\epsilon_{ijk}f^l{}_{jk}p_l.
\tag{13}
\]

Eq.(7)의 antisymmetric part와 $\operatorname{axial}(T\Omega T)=\det(T)T^{-1}\operatorname{axial}(\Omega)$를 사용하면

\[
\boxed{\omega-\tfrac12p\times a=Sw_C.}
\tag{14}
\]

이는 exactly 3 independent affine relations다. Eq.(12)의 q가 symmetric이라는 조건과 동치이므로 다른 숨은 선형 제약은 없다. C=0인 flat spatial Lie algebra에서는 $\omega=\tfrac12p\times a$이다. 이는 homogeneous $p(t)$의 rest-space projected simultaneity가 normal slicing과 다르기 때문에 acceleration과 vorticity가 묶이는 결과다. 전체 일반 congruence의 관계식으로 확대하지 않는다.

특히 $p=0,b\ne0$이면 $a=b$, $\omega=0$, $\Theta=\operatorname{tr}q$, $\sigma=\operatorname{STF}q$. 따라서 한 사건의 local rest/boost 일치만으로 time jet까지 같다고 할 수 없다. 실제 acceleration의 차원은 $A=ca$이다.

## 5. time jet이 빠질 때의 정확한 unbounded directions

q, geometry, p를 고정하고 $b\mapsto b+\lambda v$라 하자. $z=g^2Sv$이면

\[
\delta a=\lambda z,\quad
\delta B=\lambda pz^T,\quad
\delta\Theta=\lambda p\cdot z,\quad
\delta\sigma=\lambda\operatorname{STF}(pz^T),\quad
\delta\omega=\tfrac\lambda2p\times z.
\tag{15}
\]

S가 가역이므로 z는 모든 3-vector를 순회한다. 이 jet family는 동일한 C,h,K,p를 유지한다. 임의로 큰 b도 한 사건 주변의 충분히 짧은 시간 구간에서는 $|p(t)|<1$인 smooth congruence로 국소 실현할 수 있으므로 단순 algebraic artifact가 아니다. 그러나 fixed-width temporal interval에서의 derivative budget이나 Einstein/matter evolution을 이미 가정했다면 그 추가 조건이 이 family를 제한할 수 있다.

- p=0이면 time-jet 불확실성은 a만 바꾼다. $\Theta,\sigma,\omega$에는 전달되지 않는다.
- p≠0이면 전체 a, 적절한 방향의 Θ와 σ에는 유한 상한이 없다. $\|\operatorname{STF}(pz^T)\|_F^2=p^2z^2/2+(p\cdot z)^2/6$이므로 nonzero z는 항상 nonzero shear perturbation을 준다.
- ω는 p에 수직한 2차원 방향에서만 unbounded하며 $p\cdot\omega=p\cdot Sw_C$는 고정된다.
- 다음 결합량은 b와 무관하다.

\[
\boxed{\Theta-p\cdot a,\quad
\sigma-\operatorname{STF}(pa^T),\quad
\omega-\tfrac12p\times a.}
\tag{16}
\]

앞 두 출력은 $gT(q+L)T$의 trace와 STF이고 마지막은 Eq.(14)다. 그러므로 time jet budget이 없을 때는 무조건 모두 포기하기보다 이 invariant combinations의 observational response를 검사할 수 있다. 개별 shear에 대한 finite bound가 없다는 사실과 결합량의 bound 가능성은 구별한다.

## 6. 부분 target의 boundedness에 대한 필요충분 조건

고정 geometry,p에서 nuisance jet domain이 $\mathcal J=\mathcal J_0+N$이며 $\mathcal J_0$는 비어 있지 않은 compact set, N은 자유롭게 허용된 linear subspace라고 하자. 선형 target $z=P k$의 정확 image는

\[
P k_C+P\mathsf A\mathcal J_0+P\mathsf A N.
\]

따라서

\[
\boxed{\text{target image가 bounded}\iff P\mathsf A N=\{0\}.}
\tag{17}
\]

오른쪽이면 compact image만 남고, 아니면 $v\in N$, $P\mathsf Av\ne0$를 택한 $\lambda v$가 unbounded ray를 준다. 이는 arbitrary nonconvex/nonclosed domain을 recession cone만으로 판정한다는 정리가 아니다. 위 compact-plus-subspace 계약 또는 명시적으로 허용된 ray에 대한 결과다.

관측 제약 $Rj\in\mathcal Y$까지 들어가고 $\mathcal Y$가 bounded라면 residual nuisance null direction은 $N\cap\ker R$다. 다만 전체 feasible domain이 실제로 compact transverse cross-section을 가진 cylinder인지 확인해야 Eq.(17)의 converse를 적용할 수 있다. 단지 null space가 작다는 이유로 모든 비선형 feasible set의 boundedness를 결론내리지 않는다.

## 7. claim boundary와 다음 결합

이 결과는 R4의 full projected jet adapter를 **고정 tilt의 affine finite operator와 3개 정확 compatibility equation**으로 닫는다. Tensor morphology, orientation, sign을 scalar bound 전에 유지한다. 후속 공동 집합에는 $(C,h,p,q,b)$, radiation time jets/source jets, data response, MES reference radius를 같은 latent state로 넣어야 한다. Source equations가 제공하는 b의 제약과 sky data로 측정한 독립 jet를 혼동하지 않는다.

물리적 compact domain과 $|p|\le p_*<1$이 주어지면 연속 image는 compact하다. 반대로 그 domain 또는 target에 필요한 quotient criterion이 없으면 observed percentage를 유한 수치로 만들 수 없다. 이 계산은 dynamics를 버린 것이 아니라 dynamics에 필요한 순간 K와 b를 명시적 입력으로 드러낸 것이다. Einstein/matter admissibility는 별도 gate이며 일반 비선형 MES 정리나 실관측 제약을 주장하지 않는다.

## 8. 실행 검산 상태

Wolfram Language evaluator에서 verification/CAS_KINEMATIC_AFFINE.wl을 실제 실행했다. Raw response는 verification/CAS_KINEMATIC_AFFINE_RAW_V1.json이며 tool isError=false이다. Python/C++ 과학 runtime 또는 evolution solver는 실행하지 않았다. 파일 정리에는 Python 표준 라이브러리의 문자·파일 연산만 사용했다.

공간 algebra fixture는 $[E_1,E_2]=\alpha E_2$, $[E_1,E_3]=\alpha E_3$이고 c와 $\alpha$, q의 6개 독립 성분 및 b의 3개 성분을 symbolic으로 유지했다. Tilt fixtures는 $(0,3/5,0)$, $(1/5,2/5,2/5)$, $(0,0,0)$이다. 처음 둘은 $g=5/4$, 마지막은 $g=1$이다.

모든 fixture에서 full tetrad gradient로 직접 계산한 rest B,a와 Eq.(6)가 일치하고, boost 정규직교성·U 수직성·Eq.(7)·Eq.(14)·두 역산식·trace·time-jet ray·b-free invariant의 exact residual이 모두 0이다. Affine rank는 모두 9, b-image rank는 모두 3, affine left-null dimension은 모두 3이다. b가 바꾸는 와도 부분의 rank는 각각 2,2,0이다. Eq.(15)의 STF norm identity도 exact symbolic residual 0이다. 첫 fixture에서

\[
\omega-\tfrac12p\times a=(0,0,-3c\alpha/10)
=(0,0,-c\alpha p_2/2)
\]

가 확인됐다. 정상극한의 $B=q,a=b$도 일치한다. **근거 상태: derived + finite-fixture CAS checked.** 해석적 일반 증명은 §§2–6 자체이며 유한 fixture 검산이 보편 증명을 대체하지 않는다.

검증 시점: 이 kinematic CAS는 root의 R5 PREREGISTRATION.json 고정 통지보다 앞서 실행·완료했다. 따라서 그 preregistration의 prospective test로 주장하지 않고, 실제 코드와 raw를 가진 선행 verification evidence로 기록한다.

초안 정리 기록: 최초 로컬 원고의 Eq.(12) 뒤 중간 항 $B^Tp$에 $g$가 하나 빠져 있었고, 정확히 $B^Tp=g^2TZ^Tp+g^2p^2Sb$로 수정했다. Boxed inverse는 처음부터 올바르며 실제 CAS에서 확인됐다. 이 오류는 문서의 중간 조판/대수 기재 오류로 분류하고, criterion 변경이나 실패 실행의 은폐가 아니다. CAS 코드는 호출 전에 마지막 trace expression의 bracket 오타를 바로잡았으며 첫 실제 evaluator 호출은 정상 완료했다.
