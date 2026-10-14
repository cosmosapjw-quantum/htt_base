
# htt_base PMG-WU-009 비코딩 이론 수식 dossier 재구성

**기준시각:** 2026-08-31 (Asia/Seoul)  
**대상:** `cosmosapjw-quantum/htt_base`  
**최신 과학 PR:** #441, `changeset/planck-mes-wu009-full-replay-theorem-reconciliation-20260830`, HEAD `04680e99d56b9974fe1120854370af1fb94fb1d6`, OPEN/DRAFT  
**직전 이론 통합 PR:** #440, `changeset/mes-tensor-research-integration-20260830`, HEAD `687234128d7c12d04e68aad0f303c21d2d470393`, OPEN/DRAFT  
**provenance 판정:** 원래의 `MES_78_THEOREM_PROOFS_20260830_1be8c03c0c`가 저장소/업로드에 없으므로, 이 문서는 **새 독립 재유도 + CAS 교차검산**이며 원 dossier의 exact replay가 아니다.

## 0. 판정 요약

78개 row의 수학 내용 대부분은 다시 닫을 수 있다. 실제로 남은 “수학 자체의 미해결”은 없다. 다만 논문 authority로 승격하기 전에 다음 세 종류의 경계가 남는다.

1. **정의/계수 authority lock:** P12의 1+3 대 Bianchi-I reduced coefficient, P14의 endpoint \(B\)와 budget \(I\), P02의 chosen octupole Hilbert-basis normalization.
2. **보편정리 철회:** C18의 arbitrary \(T/Q/U\) finite-quadratic closure와 E05의 exhaustive null-shift taxonomy.
3. **데이터/게이트:** positive-quadratic inverse에 필요한 absolute \(T\), monopole, dipole 및 Gate E 이전 Paper A 재생성 금지.

현재 논문의 가장 중요한 수식 오류는
\[
\epsilon_\ell^{\rm draft}
 =\frac1{T_0}\sqrt{\frac{(2\ell+1)C_\ell}{4\pi}}
\]
를 MES의 PSTF norm으로 사용한 것이다. 정확한 변환은
\[
\boxed{\;
\epsilon_\ell^{\rm PSTF}
 =\sqrt{\frac{(2\ell+1)!!}{\ell!}}\,
   \frac1{T_0}\sqrt{\frac{(2\ell+1)C_\ell}{4\pi}}
\;}
\]
이며 특히
\[
\epsilon_2^2=\frac{75C_2}{8\pi T_0^2},\qquad
\epsilon_3^2=\frac{245C_3}{8\pi T_0^2}.
\]

---

## 1. 남은 blocker ledger

| ID | 우선순위 | 현재 상태 | 내용 | 남은 조치 |
|---|---:|---|---|---|
| T0 | P0 | OPEN | 원본 P01-P27 formal proof dossier 부재 | 원본 MES_78_THEOREM_PROOFS 패키지의 SHA-256 검증 또는 본 재구성 dossier를 새 authority로 명시 승인 |
| T1 | P0 | OPEN_UNTIL_GATE_E | Paper A의 MES epsilon 정규화가 sky-RMS로 남아 있음 | Gate E successor carrier가 동결된 뒤 재계산·원고 재생성 |
| T2 | P1 | CLOSED_BY_NOGO_REPLACEMENT | C18: 임의 T/Q/U의 보편 finite-quadratic projective closure | 없음; 긍정적 보편정리로 다시 쓰지 말 것 |
| T3 | P1 | CLOSED_BY_SCOPE_NARROWING | E05: 세 null-shift class의 소진성 | 소진성 문구 삭제 |
| T4 | P1 | CONDITIONAL_DERIVATION_READY | P12: vorticity/shear-evolution coefficient authority 미고정 | kappa_E=8 pi G/c^4 포함 여부와 reduced state normalization을 source line으로 동결 |
| T5 | P1 | RECONSTRUCTED_NEEDS_NOTATION_LOCK | P14: endpoint tensor B와 budget I의 원 dossier 표기 부재 | 원 theorem의 B/I가 이 정의와 동일한지 한 줄 authority lock |
| T6 | P2 | STRUCTURE_CLOSED_NORMALIZATION_OPEN | P02: 순수 octupole even Hilbert basis의 선택 정규화 | 논문에 explicit giant syzygy를 싣는 경우에만 basis normalization 동결 |
| T7 | P2 | FORMULA_CLOSED_METADATA_REQUIRED | P16: boost beta 방향 convention | carrier metadata에 beta orientation 기록 |
| T8 | P1 | NOT_A_THEORY_GAP | positive-quadratic inverse의 Planck 적용 입력 부재 가능성 | Gate D에서 input prerequisite 검사; 부재 시 typed NOT_ADMISSIBLE |
| T9 | P0 | OPEN_UNTIL_GATE_E | Paper A regeneration 금지 | Gate D/E seal 후 적용 |

### 즉시적인 논문 효과

현재 draft의 vorticity ceiling은 \(\epsilon_2\)만 사용하므로 정정 뒤 모든 row에서 정확히 \(15/2\)배가 된다:
\[
U_{\omega,\rm new}=\frac{15}{2}U_{\omega,\rm old}
 =\frac{C_2}{4\pi T_0^2}\qquad(\epsilon_1=0).
\]
따라서 **positive rescaling에 불변인 coordinate rank 자체는 유지**되지만, 보고된 물리적 숫자는 틀려 있다.

반면 shear ceiling은
\[
B_\sigma=\frac53\epsilon_1+3\epsilon_2+\frac37\epsilon_3
\]
에서 \(\ell=2,3\) 보정인자가 서로 다르므로 단일 공통배가 아니다. \(\epsilon_1=0\)일 때 octupole/quadrupole 상대가중은
\[
\frac17\longrightarrow \frac17\sqrt{\frac73},
\]
즉 약 \(1.5275\)배 커진다. 따라서 \(U_\sigma\)의 row ordering, local rank, MES family rank는 새 replay 없이는 보존된다고 말할 수 없다.

---

## 2. convention과 단위

- spacetime signature: \((- + + +)\);
- spatial metric: \(\delta_{ij}\), \(\epsilon_{123}=+1\);
- \(c,G,\hbar,k_B\)는 해당 식에서 소거되지 않는 한 유지한다;
- \(C_\ell\)은 \(T_0\)와 같은 온도단위의 제곱;
- \(Q_{ab}\in{\rm STF}_2(\mathbb R^3)\), \(O_{abc}\in{\rm STF}_3(\mathbb R^3)\);
- outward sky direction을 \(n^a\), \(n_an^a=1\)로 둔다;
- local observer boost, global matter tilt, Bianchi/background anisotropy는 서로 다른 객체다;
- observer-space \(Q,O\)는 spacetime shear/vorticity/Weyl tensor의 별칭이 아니다.

---

# Part I. P01--P08: harmonic/STF normalization과 orbit theory

## P01. stored-real Parseval 및 sky-RMS/PSTF 변환

실수 sky의 complex harmonic 계수는
\[
a_{\ell,-m}=(-1)^m a_{\ell m}^*.
\]
저장 실수 carrier를
\[
c_{\ell0}=a_{\ell0},\quad
c_{\ell m}^{(c)}=\sqrt2\,\Re a_{\ell m},\quad
c_{\ell m}^{(s)}=-\sqrt2\,\Im a_{\ell m}\quad(m>0)
\]
로 정의하면
\[
\sum_\mu c_{\ell\mu}^2
=|a_{\ell0}|^2+2\sum_{m=1}^{\ell}|a_{\ell m}|^2
=\sum_{m=-\ell}^{\ell}|a_{\ell m}|^2
=(2\ell+1)C_\ell.
\]
따라서 \(\sqrt2\)를 누락한 real carrier는 isometry가 아니며 norm과 모든 후속 tensor invariant를 바꾼다.

STF angular identity는
\[
\int_{S^2}n_{\langle A_\ell\rangle}n^{\langle B_\ell\rangle}\,d\Omega
=\Delta_\ell\,\delta_{\langle A_\ell\rangle}^{\langle B_\ell\rangle},
\qquad
\Delta_\ell=\frac{4\pi\,2^\ell(\ell!)^2}{(2\ell+1)!}.
\]
\(\Theta_\ell(n)=T_{A_\ell}n^{A_\ell}\)이면
\[
\int_{S^2}\Theta_\ell^2d\Omega
=\Delta_\ell\,T_{A_\ell}T^{A_\ell}
=(2\ell+1)C_\ell.
\]
그러므로
\[
T_{A_\ell}T^{A_\ell}
=\frac{(2\ell+1)!!}{\ell!}\frac{(2\ell+1)C_\ell}{4\pi}.
\]
\(\ell=2,3\)에서
\[
Q:Q=\frac{75}{8\pi}C_2,\qquad
O:O=\frac{245}{8\pi}C_3.
\]
Wolfram direct sphere integration도
\[
\int(Q_{ab}n^an^b)^2d\Omega=\frac{8\pi}{15}Q:Q,\qquad
\int(O_{abc}n^an^bn^c)^2d\Omega=\frac{8\pi}{35}O:O
\]
를 재현했다.

## P02. 순수 octupole의 O(3) 대 SO(3) chirality

순수 \(O_{abc}\)에서 degree-2 STF tensor와 degree-3 vector를
\[
A_{ij}=O_{ikl}O_{jkl}-\frac13\delta_{ij}O_{klm}O_{klm},
\qquad
a_i=O_{ijk}A_{jk}
\]
로 만든다. 그러면
\[
\boxed{\chi_{15}
=\epsilon_{ijk}a_i(Aa)_j(A^2a)_k}
\]
는 총 degree \(3+5+7=15\)의 pseudoscalar다. \(R\in SO(3)\)에서는 불변이고
\[
\chi_{15}(RO)=\det(R)\chi_{15}(O)
\]
이므로 improper rotation/mirror에서 부호가 뒤집힌다.

even invariant \(I_2,I_4,I_6,I_{10}\)만 쓰면 \(O\)와 mirror가 충돌한다. 따라서 그것들은 generic \(O(3)\) orbit을 기술할 수 있어도 \(SO(3)\) orbit의 handedness를 분리하지 못한다. \(\chi_{15}^2\)는 even invariants의 polynomial이지만 부호는 그들로 복원되지 않는다.

**남은 provenance 경계:** \(I_{2,4,6,10}\)의 정확한 conventional normalization과 거대한 syzygy는 원 dossier가 없으므로 고정하지 않았다. 논문이 handedness sign만 요구하면 위 식으로 충분하다.

## P03. \((Q,O)/SO(3)\) generic quotient dimension

\[
\dim{\rm STF}_2=5,\qquad \dim{\rm STF}_3=7.
\]
generic pair의 stabilizer는 discrete이므로 principal orbit dimension은 \(3\):
\[
\boxed{\dim[({\rm STF}_2\oplus{\rm STF}_3)/SO(3)]=5+7-3=9.}
\]
따라서 principal stratum의 연속적 완전표현을 8개 real scalar로 만드는 것은 불가능하다. 이는 단순 parameter counting만이 아니라 9차원 manifold의 open set을 \(\mathbb R^8\)에 연속 injective하게 넣을 수 없다는 dimension/invariance-of-domain obstruction이다.

## P04. cyclic Krylov reconstruction

\[
v_a=O_{abc}Q^{bc},\qquad
K=[v,Qv,Q^2v].
\]
\(Q={\rm diag}(\lambda_1,\lambda_2,\lambda_3)\), \(v=(x_1,x_2,x_3)^T\)이면
\[
\boxed{\det K=x_1x_2x_3\prod_{i<j}(\lambda_j-\lambda_i).}
\]
Wolfram 출력은 column convention에 따라
\[
-(\lambda_1-\lambda_2)(\lambda_1-\lambda_3)
(\lambda_2-\lambda_3)x_1x_2x_3
\]
이며 같은 식이다. 따라서 \(\det K\ne0\)는 simple spectrum과 모든 eigencomponent \(x_i\ne0\)를 동시에 뜻한다.

\(q_2=\mathrm{tr}Q^2\), \(q_3=\mathrm{tr}Q^3\)이면 eigenvalues는
\[
\lambda^3-\frac{q_2}{2}\lambda-\frac{q_3}{3}=0
\]
의 roots다. moments
\[
m_k=v^TQ^kv=\sum_iw_i\lambda_i^k,\qquad w_i=x_i^2
\]
에서
\[
\boxed{
w_i=\frac{m_2+\lambda_i m_1+(\lambda_i^2-q_2/2)m_0}
{3\lambda_i^2-q_2/2}}
\]
를 얻는다. moments가 \(x_i^2\)만 주는 반면
\[
\kappa=\det K=x_1x_2x_3\Delta(\lambda)
\]
가 proper-orientation sign product를 준다. \(Q\) stabilizer의 pairwise sign flips는 \(x_1x_2x_3\)를 보존하므로 \((q_2,q_3,m_0,m_1,m_2,\kappa)\)는 generic vector-plus-quadrupole orbit을 분리한다.

마지막으로 \(K_i=(v,Qv,Q^2v)\) basis에서 symmetric rank-3 tensor의 10개 독립성분
\[
O(K_i,K_j,K_k),\qquad 0\le i\le j\le k\le2
\]
를 기록하면 \(O\) 전체가 복원된다. 따라서 normalized \(Q,O\)에 대해
\[
2\ (q_2,q_3)+3\ (m_0,m_1,m_2)+1\ (\kappa)+10=16
\]
개의 contraction packet은 generic orbit의 injective overcomplete chart다. 원래 두 amplitude를 별도로 보존하면 normalization은 가역이다.

## P05. orientation-fixed chart와 3 gauge conditions

\(\det K\ne0\)에서 QR 또는 Cholesky로
\[
K=RT,\qquad R\in SO(3)
\]
를 만들고 \(T\)의 diagonal sign과 \(\det K\)를 고정하면 proper-oriented canonical frame가 정해진다. 이는 3차원 rotation freedom을 정확히 3개 gauge condition으로 제거한다. 같은 invariant packet을 가진 두 generic pair는 이 canonical representative에서 일치하므로 같은 \(SO(3)\) orbit이다.

## P06. global frame 및 scalar-to-tensor no-go

비자명 stabilizer \(H_x\)를 가진 \(x\)에서 equivariant frame \(F(x)\in SO(3)\)가 존재한다고 하자. \(h\in H_x\)이면
\[
F(x)=F(hx)=hF(x).
\]
SO(3)의 left action은 free이므로 \(h=e\)여야 한다. 따라서 nontrivial stabilizer strata를 포함하는 global equivariant full frame은 존재하지 않는다.

또한 trivial scalar \(s\)에서 nontrivial irrep \(V_\ell\), \(\ell>0\), 로의 equivariant map \(f\)는
\[
f(s)=Rf(s)\quad\forall R\in SO(3)
\]
를 만족해야 하므로 invariant subspace가 없는 \(V_\ell\)에서는 \(f(s)=0\)뿐이다. scalar MES ceiling에서 방향, vector, STF를 제조할 수 없다.

## P07. power/bispectrum 불완전성

repo witness는 \(Q=\mathrm{diag}(1,2,-3)\)와 explicit STF3 \(O\)에 대해
\[
(Q:Q,\ O:O,\ \mathrm{tr}Q^3,\ Q_{ij}O_{ikl}O_{jkl})
=(14,788,-18,-472)
\]
를 갖는다. \(O\to-O\)는 이 네 even invariant를 모두 보존하지만
\[
\kappa(Q,-O)=-\kappa(Q,O)\ne0.
\]
따라서 mirror pair가 low-order power/bispectrum에서 충돌하고 chirality-aware Krylov packet에서 분리된다. quotient dimension 9 대 4라는 dimension obstruction도 독립적인 반증이다.

## P08. quotient characteristic kernels

\(X/G\)가 standard Borel이고 injective Borel chart
\[
\phi:X/G\to\mathbb R^d
\]
가 Borel inverse를 image 위에 갖는다면 Gaussian
\[
k([x],[y])=\exp[-\|\phi([x])-\phi([y])\|^2/(2s^2)]
\]
의 mean embedding은 quotient probability measures를 분리한다.

chart 없이 compact group \(G\)를 평균할 때는 characteristic base kernel \(k_0\)로
\[
k_G(x,y)=\int_G\!\!\int_G k_0(gx,hy)\,dg\,dh
\]
를 쓰면 orbit measures의 mean-embedding inner product가 된다. constant base kernel은 characteristic하지 않고, one-sided average는 필요한 양변 불변성/대칭성을 자동 보장하지 않으므로 일반 정리가 아니다.

---

# Part II. P09--P15: STF geometry, moments, dynamics, convex bounds

## P09. STF2 orbit, cubic, recurrence, directional bound

tracefree eigenvalues \(\lambda_1+\lambda_2+\lambda_3=0\)에 대해
\[
Q^3-\frac{q_2}{2}Q-\frac{q_3}{3}I=0,
\quad q_2=\mathrm{tr}Q^2,\quad q_3=\mathrm{tr}Q^3.
\]
특성다항식의 discriminant는
\[
\Delta=\frac12q_2^3-3q_3^2\ge0,
\]
따라서
\[
\boxed{|q_3|\le\frac{q_2^{3/2}}{\sqrt6}.}
\]
Wolfram은
\[
q_3^2-\frac16q_2^3
=-\frac13(a-b)^2(2a+b)^2(a+2b)^2
\]
로 factor했다. equality는 repeated eigenvalue, 즉 uniaxial endpoint다.

모든 \(n\ge3\)에 대해
\[
p_n=\mathrm{tr}Q^n
=\frac{q_2}{2}p_{n-2}+\frac{q_3}{3}p_{n-3}.
\]
또
\[
\|Q\|_{\rm op}^2\le\frac23q_2,\qquad
|n^TQn|\le\sqrt{\frac23}\|Q\|_F,
\]
이며 uniaxial spectrum에서 sharp하다.

## P10. mixed moments와 feasibility

\[
m_k=v^TQ^kv
\]
는
\[
m_{k+3}=\frac{q_2}{2}m_{k+1}+\frac{q_3}{3}m_k
\]
를 만족한다. 특히
\[
m_3=\frac{q_2}{2}m_1+\frac{q_3}{3}m_0,\quad
m_4=\frac{q_2}{2}m_2+\frac{q_3}{3}m_1.
\]
Krylov Gram matrix는
\[
G=K^TK=
\begin{pmatrix}
m_0&m_1&m_2\\
m_1&m_2&m_3\\
m_2&m_3&m_4
\end{pmatrix}\succeq0,
\qquad
\det G=\kappa^2.
\]
따라서 \(G\succeq0\), \(\Delta\ge0\), \(\det G=\kappa^2\)가 기본 feasibility 조건이다. explicit determinant는
\[
\det G=\frac1{36}\left[
-36m_2^3+18m_1^2m_2q_2+18m_0m_2^2q_2
-9m_0m_1^2q_2^2-12m_1^3q_3
+36m_0m_1m_2q_3-12m_0^2m_1q_2q_3-4m_0^3q_3^2
\right].
\]

## P11. boost response algebra

정의
\[
(B_Q\beta)_{abc}=3\beta_{\langle a}Q_{bc\rangle}.
\]
3차원에서 explicit STF projection은
\[
(B_Q\beta)_{abc}
=\beta_aQ_{bc}+\beta_bQ_{ca}+\beta_cQ_{ab}
-\frac25\left[
\delta_{ab}(Q\beta)_c+\delta_{ac}(Q\beta)_b+\delta_{bc}(Q\beta)_a
\right].
\]
직접 contraction하면
\[
\boxed{(B_Q\beta)_{abc}Q^{bc}
=\left(q_2I+\frac65Q^2\right)_a{}^d\beta_d.}
\]
또
\[
\boxed{\|B_Q\beta\|_F^2
=3q_2\|\beta\|^2+\frac{18}{5}\|Q\beta\|^2.}
\]
\(Q\ne0\)이면
\[
R_Q=q_2I+\frac65Q^2
\]
는 positive definite다. response inverse는
\[
\boxed{\widehat\beta
=R_Q^{-1}(O:Q)}
\]
이며 이는 Frobenius least squares
\(\min_\beta\|O-B_Q\beta\|_F^2\)의 유일해다.

### sharp condition number \(5/3\)

tracefree spectrum의 absolute magnitudes를
\[
a=b+c,\qquad b\ge c\ge0,\qquad t=b/c\ge1
\]
로 쓰면
\[
\kappa(R_Q)=
\frac{16t^2+22t+16}{10t^2+10t+16}.
\]
미분은
\[
\kappa'(t)=
-\frac{3(t-4)(4+5t)}{(8+5t+5t^2)^2},
\]
따라서
\[
\boxed{\kappa(R_Q)\le\frac53}
\]
이고 \(t=4\), 즉 scale을 제외하면 spectrum \((-5,1,4)\)에서 equality다. \(q_2=1\) normalization에서는
\[
(-5,1,4)/\sqrt{42}.
\]

\({\rm STF}_3\) 차원은 7이고 \(B_Q\)의 rank는 3이므로
\[
\dim({\rm im}B_Q)^\perp=4.
\]
직교잔차 \(O_\perp=(I-P_{B_Q})O\)는 response model 밖의 성분을 검출하지만, \(\beta\) 비식별의 원인은 아니다. 반대로 unrestricted additive nuisance \(N\in{\rm STF}_3\)를 허용하면
\[
O=B_Q\beta+N
\]
에서 모든 \(\beta\)가 \(N=O-B_Q\beta\)로 흡수되어 비식별이다.

## P12. vorticity envelope와 tilt source

### B11: 일반 1+3 geodesic vorticity 식

\[
\dot\omega_{\langle a\rangle}
+\frac23\Theta\omega_a-\sigma_{ab}\omega^b
+\frac12(\mathrm{curl}\,A)_a=0.
\]
geodesic congruence \(A_a=0\), \(\Theta=3H\)이면
\[
\frac{d}{dt}\|\omega\|
\le\left[-2H+\|\sigma\|_{\rm op}\right]\|\omega\|,
\]
따라서
\[
\boxed{
\|\omega(t)\|\le\|\omega(t_0)\|
\exp\!\int_{t_0}^{t}\left[-2H+\|\sigma\|_{\rm op}\right]dt'.
}
\]
MES shear envelope가 같은 congruence와 전 시간구간에서 성립할 때에만 이를 삽입할 수 있다. homogeneous hypersurface normal은 별도로 vorticity-free이므로 tilted matter congruence와 혼동하면 안 된다.

### B12: \(\mathrm{tr}\sigma^3\)의 anisotropic-stress source

일반 shear propagation을
\[
\dot\sigma_{\langle ab\rangle}=\cdots+\alpha_\pi\pi_{ab}
\]
로 쓰면
\[
S_3=\mathrm{tr}\sigma^3,\qquad
\dot S_3=3(\sigma^2)^{\langle ab\rangle}\dot\sigma_{ab},
\]
그러므로
\[
\boxed{
(\dot S_3)_\pi
=3\alpha_\pi(\sigma^2)^{\langle ab\rangle}\pi_{ab}.
}
\]
tilted perfect fluid에서
\[
\pi_{ab}=(\rho+p)\gamma^2v_{\langle a}v_{b\rangle}
\]
이면
\[
(\dot S_3)_{\rm tilt}
=3\alpha_\pi(\rho+p)\gamma^2
v_a(\sigma^2)^{\langle ab\rangle}v_b.
\]
이는 scalar norm만이 아니라 tilt direction과 shear eigenframe의 mixed moment다.

**authority lock 필요:** geometric units의 일반 1+3 식에서는 흔히
\(\alpha_\pi=\kappa_E/2\), \(\kappa_E=8\pi G/c^4\)이나, repo의 Bianchi-I reduced state가 \(\pi\)를 이미 재정규화했다면 계수는 달라진다. 이 한 줄을 source equation으로 고정하기 전에는 숫자계수를 논문 정리로 승격하지 않는다.

## P13. product bodies, ellipsoids, extrema, SOS

독립 block \(x_j\in K_j\)와 linear image
\[
y=\sum_jA_jx_j
\]
에 대해
\[
Y=\sum_jA_jK_j,\qquad
\boxed{h_Y(u)=\sum_jh_{K_j}(A_j^Tu).}
\]
각 \(K_j\)가 ball이면 maximizer를 \(A_j^Tu\) 방향에 맞추어 equality가 달성되므로 sharp하다.

ellipsoid
\[
K_j=\{c_j+L_jz_j:\|z_j\|_2\le1\}
\]
의 image membership은
\[
y=\sum_jA_j(c_j+L_jz_j),\qquad\|z_j\|_2\le1
\]
이라는 SOCP feasibility다.

extreme value theorem은 domain이 closed and bounded인 경우에만 바로 적용된다. polynomial compact semialgebraic set에서 quadratic module이 Archimedean이면 Putinar/Lasserre hierarchy는 optimum으로 수렴하지만 일반적으로 어떤 finite relaxation order에서 exact하다는 정리는 없다.

## P14. noncommuting shear-history endpoint

원 dossier notation을 자연스럽게 재구성한다. deformation gradient를
\[
\dot F=\sigma(t)F,\qquad F(t_0)=I,\qquad\mathrm{tr}\sigma=0
\]
로 두고 right stretch와 logarithmic strain을
\[
U=(F^TF)^{1/2},\qquad B=\log U\in{\rm STF}_2
\]
로 정의한다. integrated budget은
\[
I=\int_{t_0}^{t_1}\sqrt{\frac{\sigma:\sigma}{6}}\,dt.
\]

모든 \(\sigma(t)\)가 서로 commute하면 time ordering이 사라져
\[
F=\exp\!\int\sigma dt,\qquad
\boxed{B=\int\sigma dt.}
\]

noncommuting인 경우에도 SPD manifold의 endpoint distance는 path length 이하이고, singular-log velocity의 Euclidean norm은 \(\|\sigma\|_F\) 이하이므로
\[
\boxed{\|B\|_F\le\int\|\sigma\|_Fdt=\sqrt6\,I.}
\]
P09 cubic bound를 적용하면
\[
\boxed{|\mathrm{tr}B^3|
\le\frac{\|B\|_F^3}{\sqrt6}
\le6I^3.}
\]
constant commuting uniaxial history
\[
\sigma(t)=s(t)\,\mathrm{diag}(2,-1,-1)
\]
에서 두 상한이 동시에 포화되므로 상수는 sharp하다.

**provenance 경계:** 원 P14의 \(B,I\)가 정확히 위 log-stretch/budget 정의인지 authority 한 줄이 필요하다. 수학적 정리는 이 정의 아래 완결된다.

## P15. one-sided error와 Hausdorff

\[
e(A,B)=\sup_{a\in A}\inf_{b\in B}d(a,b)
\]
만 작다고 \(d_H(A,B)\)가 작지는 않다. \(A=\{0\},B=[0,1]\)이면 \(e(A,B)=0\), \(e(B,A)=1\).

반면 동일 parameter domain \(\Theta\)에서
\[
A=\{f(\theta)\},\quad B=\{g(\theta)\},\quad
\sup_\theta d(f(\theta),g(\theta))\le\varepsilon
\]
이면 양방향 대응이 있으므로
\[
d_H(A,B)\le\varepsilon.
\]

---

# Part III. P16--P21: Lorentz boost, positive quadratic sky, likelihood, polarization

## P16. exact Lorentz pullback과 first-order \(Q\to O\)

\(u'=\gamma(u+\beta)\)로 convention을 잡고 photon distribution의 scalarity를 쓰면
\[
\frac{E}{k_BT_u(n)}
=\frac{E'}{k_BT_{u'}(n')}.
\]
\(E/E'=\gamma(1+\beta\cdot n')\)이므로
\[
\boxed{
T_{u'}(n')
=\frac{T_u(n(n'))}{\gamma(1+\beta\cdot n')}.
}
\]
inverse aberration은
\[
n=
\frac{
n'+\left[\gamma+\frac{\gamma-1}{\beta^2}(\beta\cdot n')\right]\beta
}{
\gamma(1+\beta\cdot n')
}.
\]
반대 방향으로 정의한 deboost parameter는 \(\beta\to-\beta\)를 준다.

first order에서 pure quadrupole의 octupole response는 convention 부호를 제외하고
\[
\boxed{\delta O_{abc}=\pm3\beta_{\langle a}Q_{bc\rangle}.}
\]
repo의 accepted response operator는 \(B_Q\beta=+3\beta_{\langle a}Q_{bc\rangle}\)다. carrier metadata는 \(\beta\)가 observer-to-CMB인지 CMB-to-observer인지 명시해야 한다.

## P18. ideal Bianchi-I blackbody의 positive quadratic inverse

### C08: \(T^{-2}\) closure

Bianchi I에서 spatial Killing covector \(p_i\)는 null geodesic을 따라 보존된다. emission과 observation에서
\[
E^2=c^2g^{ij}p_ip_j.
\]
collisionless Planck distribution의 exponent \(E/(k_BT)\)가 보존되므로
\[
T_o(n)=T_e\frac{E_o}{E_e}.
\]
관측 orthonormal direction \(n\)으로 \(p_i\)를 쓰면 어떤 SPD matrix \(M\)에 대해
\[
\boxed{T_o(n)^{-2}=T_e^{-2}\,n^TMn.}
\]
local Lorentz boost를 포함하면 일반 quadratic
\[
F(n)\equiv T(n)^{-2}
=a+2b_in^i+C_{ij}n^in^j
\]
가 된다. 중요한 점은 **\(T\) 자체가 아니라 \(T^{-2}\)** 가 \(\ell\le2\)로 닫힌다는 것이다.

### C09: null-cone gauge kernel

\(k^\mu=(1,n^i)\)이면 \(k^\mu\eta_{\mu\nu}k^\nu=0\)이고
\[
F(n)=k^TAk.
\]
따라서
\[
A\sim A+h\eta.
\]
역으로 모든 null \(k\)에서 \(k^THk=0\)이면 odd part로 \(H_{0i}=0\), sphere의 quadratic restriction으로 \(H_{ij}=h\delta_{ij}\), \(H_{00}=-h\), 즉
\[
\boxed{\ker(A\mapsto F)=\mathrm{span}\{\eta\}.}
\]

### C10--C11: unique finite boost + positive \(M\)

mixed operator \(L=\eta^{-1}A\)의 generalized eigensystem을 쓴다. strict positivity
\[
F(n)>0\quad\forall n\in S^2
\]
는 한 timelike eigenvalue \(\lambda_0\)와 세 spacelike eigenvalues \(\lambda_i\) 사이에
\[
\lambda_i-\lambda_0>0
\]
를 강제한다. gauge representative
\[
A_+=A-\lambda_0\eta
\]
는 timelike eigenvector \(u\)를 kernel로 갖고 \(u^\perp\)에서 positive definite다.

future unit \(u\)로부터
\[
\beta^i=\frac{u^i}{u^0},\qquad|\beta|<1
\]
를 얻고, \(e_0\to u\)인 standard rotation-free boost로 \(A_+\)를 rest frame으로 옮긴 spatial block을 \(M>0\)로 둔다. 반대로 finite \(\beta\)와 \(M>0\)는 모든 null direction에서 strict-positive quadratic을 만든다. 따라서
\[
\boxed{
\{\text{strictly positive quadratic skies}\}
\longleftrightarrow
\{|\beta|<1,\ M\in{\rm Sym}^+(3)\}
}
\]
가 rotation-free boost convention 아래 유일하다. 이는 representation uniqueness이지 physical-cause uniqueness가 아니다.

boundary \(F=0\)에서는 \(M\) singular 또는 infinite-boost limit가 가능하여 정리가 깨진다.

### C12--C14

- \(F=T^{-2}\)에 \(\ell>2\)가 유의하게 남으면 ideal Bianchi-I, collisionless blackbody, exact calibration/bandpass, correct frame 중 적어도 하나가 실패했다.
- 같은 Planck spectrum의 exact channel inversion이면 모든 channel이 같은 \(T(n)\)를 복원해야 한다.
- incoherence는 common model을 기각하지만 foreground, calibration, bandpass, spectral distortion, beam/mask, model failure 중 원인을 유일하게 선택하지 않는다.

## P20. direct-temperature likelihood와 local bias

\(Y\sim N(T,\sigma^2)\)의 direct-temperature model에서 WLS는 Gaussian likelihood다. 그러나
\[
\mathbb E[Y^{-2}]=\infty
\]
이다. 실제로 density를 포함한 integrand에 대해
\[
\lim_{y\to0}y^2\frac{e^{-(y-\mu)^2/(2\sigma^2)}}{y^2}
=e^{-\mu^2/(2\sigma^2)}>0,
\]
따라서 \(1/y^2\) nonintegrable singularity가 남는다. iid sample에서
\(\overline{Y^{-2}}\to\infty\) a.s.이므로 inverse-square constant fit을 다시 \(T\)로 변환하면 0으로 붕괴한다.

일반 regular model
\[
y=f(\theta_0)+s+\epsilon,\qquad J=\partial_\theta f|_{\theta_0}
\]
에서 first-order parameter bias는
\[
\boxed{
\delta\theta=(J^TWJ)^{-1}J^TWs.
}
\]
따라서
\[
J^TWs=0
\]
이면 first-order bias가 사라진다. 이는 finite contamination 또는 nonlinear second order의 무편향을 뜻하지 않는다.

## P21. arbitrary polarization no-go

\(P(n)=Q_{\rm Stokes}(n)+iU(n)\)는 spin-\(-2\) section이며 arbitrary smooth field는 무한한 spin-harmonic 자유도를 갖는다. scalar quadratic \(T^{-2}\)의 9차원 closure를 arbitrary \(P\)로 functorially 확장하는 finite-dimensional injective/equivariant map은 존재할 수 없다.

또 local boost는 aberration, Doppler weight, screen-basis phase를 함께 작용시키므로 \(Q,U\)를 독립 scalar로 취급하는 quadratic ansatz는 convention-covariant하지 않다.

교체 가능한 정확한 statement는 다음뿐이다.

1. strict unpolarized subspace \(Q=U=0\)는 collisionless Lorentz pullback 아래 invariant다.
2. 미리 고정한 finite \(\ell_{\max}\) spin-2 carrier는 유한차원 representation으로 다룰 수 있지만 “quadratic closure”가 아니다.
3. full sky thermodynamic \(d=1\)에서는 exact boost kernel의 E/B mixing 구조를 별도 spin representation으로 다뤄야 하며, cut sky leakage는 estimator 문제다.

---

# Part IV. P19, P22--P27: finite-null, low-z identification, robust statistics

## P19. exchangeable finite rank

\(N\) rows가 jointly exchangeable이고 전체 scoring pipeline \(S\)가 row permutation과 commute하면 score vector도 exchangeable하다. weak upper-tail rank
\[
p_i=\frac1N\sum_{j=1}^N{\bf1}\{S_j\ge S_i\}
\]
는
\[
\Pr(p_i\le\alpha)\le\alpha
\]
인 superuniform p-value다. ties가 없을 때만 discrete uniform이다.

midrank
\[
u_i=\frac{L_i+\frac12E_i}{N}
\]
는 strictly decreasing transform 아래
\[
u_i\mapsto1-u_i
\]
이므로 upper/lower tail도 바꿔야 한다.

feature/tail/reducer를 adaptive하게 고르더라도 그 선택과 scoring을 각 pseudo-observation에 대해 통째로 다시 실행하여 row-equivariance를 유지하면 validity가 남는다. observation row에서만 선택하고 null rows에 freeze하면 깨진다.

conditional label probability \(w_i\)를 정확히 알면 weighted tail
\[
p_i=\sum_jw_j{\bf1}\{S_j\ge S_i\}
\]
가 같은 random-label argument로 valid하다.

## P22. low-z affine identifiability

radial field를
\[
y_\alpha=n_\alpha\cdot v
+r_\alpha H
+r_\alpha n_\alpha^i\Sigma_{ij}n_\alpha^j
\]
로 쓰면 unknown은 \(3+1+5=9\). design matrix가 full column rank일 때에만 식별된다.

solid rotation \(W_{ij}=-W_{ji}\)는
\[
n^iW_{ij}n^j=0
\]
이므로 radial velocity로 식별 불가다.

두 shell의 알려진 response \(g_1\ne g_2\)가
\[
v_s=v_{\rm loc}+g_sv_{\rm glob}
\]
로 들어가면 2x2 inversion으로 local/global vectors를 분리할 수 있다.

nuisance \(Z\gamma\)가 있으면 weighted residual projector \(P_Z^\perp\)에 대해
\[
P_Z^\perp X
\]
가 full rank일 때에만 target parameter가 식별된다.

free optical-depth amplitude \(\tau\)와 amplitude \(\theta\)가 \(\tau X\theta\)로만 나타나면
\[
(\tau,\theta)\sim(c\tau,\theta/c)
\]
scaling degeneracy가 있다.

## P23. physical intersection과 confidence inversion

exact physical set \(\mathcal P\)를 intersect하면
\[
\Theta_{\rm id}\cap\mathcal P\subseteq\Theta_{\rm id}
\]
이므로 identified set을 키울 수 없다.

각 \(\theta\)에 대해 size-\(\alpha\) test가 있으면
\[
C(Y)=\{\theta:\text{test at }\theta\text{ does not reject}\}
\]
는 true point를 \(1-\alpha\) 이상 포함한다. 하나의 joint confidence set의 모든 projection은 같은 event \(\theta_0\in C\) 위에서 동시에 참값을 포함한다. 그러나 이는 population identified set 전체를 덮는다는 뜻이 아니다. estimated physical set과 intersect하면 그 set의 miss probability도 합산해야 한다.

paired contrast는 유효성의 필요조건이 아니다. joint calibrated statistic, permutation-equivariant score, Bonferroni 등 반례가 있다.

## P24. null-shift taxonomy와 distance control

“세 가지 null shift가 모든 가능성을 소진한다”는 theorem은 ambient model과 equivalence relation 없이는 정의되지 않는다. 세 label은 predeclared diagnostic examples로만 유지한다.

total variation은 모든 event에 대해
\[
|P(A)-Q(A)|\le d_{\rm TV}(P,Q)
\]
를 준다. Wasserstein-1은 indicator를 직접 제어하지 않는다. \(P=\delta_0,Q=\delta_\varepsilon,A=\{0\}\)이면 \(W_1=\varepsilon\)인데 event 차이는 1이다.

coupling된 scalar statistics \(U,V\)와 threshold \(t\)에는
\[
|\Pr(U\le t)-\Pr(V\le t)|
\le\Pr(|U-t|\le\delta)+\frac{\mathbb E|U-V|}{\delta}
\]
처럼 anti-concentration term을 붙여야 한다.

## P25. cone GLRT와 sum-vs-max

\(Z\sim N(\mu,I)\), \(H_0:\mu=0\), \(H_1:\mu\in C\)에서 \(C\)가 closed convex cone이면 Moreau decomposition으로
\[
2\log\Lambda
=\|Z\|^2-\mathrm{dist}(Z,C)^2
=\|\Pi_CZ\|^2.
\]
bounded body \(K\)에는 마지막 등식이 없다. \(K=[0,1],z=2\)이면
\[
4-\mathrm{dist}(2,K)^2=3,\qquad|\Pi_K2|^2=1.
\]

iid \(Z_i\sim N(\delta,1)\), common \(\delta>0\) 대안에서는 likelihood ratio가 \(\sum_iZ_i\)에 monotone하므로 same-size sum test가 Neyman-Pearson/MLR test다. \(d\ge2\), \(0<\alpha<1\)에서 max test와 rejection region이 a.s. 같지 않으므로 모든 \(\delta>0\)에서 sum test가 적어도 강하고 일반적으로 strictly stronger다.

## P26. e-process

\[
\mathbb E[E_t\mid\mathcal F_{t-1}]\le1,\qquad E_t\ge0
\]
이면
\[
M_t=\prod_{s\le t}E_s
\]
는 nonnegative supermartingale이고 \(\mathbb E M_t\le1\). lane 선택이 \(\mathcal F_{t-1}\)-measurable이고 선택된 increment도 conditional e-valid이면 predictable adaptation이 허용된다.

marginal e-values만으로 곱하면 안 된다. \(B\sim{\rm Bernoulli}(1/2)\),
\[
E_1=E_2=2B
\]
이면 각각 평균 1이지만
\[
\mathbb E[E_1E_2]=2.
\]

## P27. selection symmetry와 single-query limitation

selection independence는 필요조건이 아니다. 선택 rule이 label-blind이고 permutation-equivariant라면 data-dependent selection 뒤에도 queried label의 conditional symmetry가 유지될 수 있다.

reference 수를 늘리면 single-query rank의 resolution은 좋아지지만 일반 two-sample consistency는 자동으로 생기지 않는다. 고정 score가 alternative를 구분하지 못하거나 query가 하나뿐이면 reference \(N\to\infty\)에서도 power가 1로 갈 이유가 없다.

---

# Part V. Paper A 교체식

PSTF MES coordinates는
\[
\epsilon_1=\text{residual cosmological PSTF dipole norm},
\]
\[
\epsilon_2=\frac1{T_0}\sqrt{\frac{75C_2}{8\pi}},
\qquad
\epsilon_3=\frac1{T_0}\sqrt{\frac{245C_3}{8\pi}},
\]
\[
B_\sigma=\frac53\epsilon_1+3\epsilon_2+\frac37\epsilon_3,\qquad
B_\omega=\frac{10}{3}\epsilon_1+\frac{2}{15}\epsilon_2,
\]
\[
\boxed{
U_\sigma=\frac32B_\sigma^2,\qquad
U_\omega=\frac32B_\omega^2.
}
\]
이것들은 premise-dependent one-way upper-ceiling coordinates이며 measured shear/vorticity가 아니다.

### 적용 금지선

이 식을 현재 `main.tex`에 넣는 것만으로는 충분하지 않다. \(U_\sigma\) row ordering이 달라질 수 있으므로 paired-300 및 모든 predeclared family variant를 successor recipe로 다시 계산하고 Gate E에서 freeze한 뒤 표, figure, abstract를 동시에 재생성해야 한다.

---

# Part VI. proof-module 상태

| Module | 연결 rows | 판정 |
|---|---|---|
| P01 | A01, A02, B01 | CLOSED_CAS_CHECKED |
| P02 | A03 | STRUCTURE_CLOSED_BASIS_NORMALIZATION_OPEN |
| P03 | A04 | CLOSED |
| P04 | A05, A06 | CLOSED_CAS_CHECKED |
| P05 | A07, A08, A09 | CLOSED |
| P06 | A10, B22 | CLOSED_BY_NO_GO |
| P07 | A11 | CLOSED_BY_COUNTEREXAMPLE_AND_DIMENSION |
| P08 | A12, A13 | CLOSED_WITH_STANDARD_BOREL_ASSUMPTIONS |
| P09 | B02, B03, B04, B05 | CLOSED_CAS_CHECKED |
| P10 | B06, B07, B08, B09 | CLOSED_CAS_CHECKED |
| P11 | B10, C03, C04, C05, C06 | CLOSED_CAS_CHECKED |
| P12 | B11, B12 | CONDITIONAL_ON_EQUATION_NORMALIZATION |
| P13 | B13, B14, B15, B16 | CLOSED |
| P14 | B17, B18, B19, B20 | RECONSTRUCTED_NEEDS_B_I_NOTATION_LOCK |
| P15 | B21 | CLOSED_BY_COUNTEREXAMPLE |
| P16 | C01, C02 | CLOSED_UP_TO_BETA_ORIENTATION_METADATA |
| P17 | C07 | CLOSED_BY_LINEAR_IDENTIFIABILITY |
| P18 | C08, C09, C10, C11, C12, C13, C14 | THEOREM_CLOSED_EMPIRICAL_INPUT_GATED |
| P19 | A14, E01, E02, E03, E04, E08 | CLOSED |
| P20 | C15, C16, C17 | CLOSED |
| P21 | C18 | CLOSED_BY_NOGO_AND_RESTRICTED_REPLACEMENT |
| P22 | D01, D02, D03, D04, D05 | CLOSED |
| P23 | D06, D07, D08, E10, E11 | CLOSED |
| P24 | E05, E06 | E06_CLOSED_E05_NARROWED_TO_DEFINITION |
| P25 | E07, E09 | CLOSED |
| P26 | E12, E13, E14 | CLOSED |
| P27 | E15, E16 | CLOSED |

---

# Part VII. 78-row theorem map

| Row | verdict | module | 재구성 statement |
|---|---|---|---|
| A01 | PROVED | P01 | stored-real carrier의 Parseval isometry |
| A02 | PROVED | P01 | harmonic-STF map은 bijective SO(3) intertwiner |
| A03 | CORRECTED | P02 | even generators는 O(3) orbit만; SO(3)는 degree-15 chirality 필요 |
| A04 | PROVED | P03 | generic (STF2,STF3)/SO(3) quotient dimension은 9 |
| A05 | PROVED | P04 | simple-spectrum cyclic pair는 moments+chirality로 재구성 |
| A06 | PROVED | P04 | det[v,Qv,Q^2v]의 Vandermonde factorization |
| A07 | PROVED | P05 | det K != 0에서 orientation-fixed QR generic chart |
| A08 | PROVED | P05 | canonical pair의 generic uniqueness |
| A09 | PROVED | P05 | chart는 3개 회전 gauge 조건으로 quotient를 고정 |
| A10 | REFUTED | P06 | 비자명 stabilizer strata를 포함하는 global equivariant full frame |
| A11 | REFUTED | P07 | power+저차 bispectrum이 full Krylov data와 동등 |
| A12 | PROVED | P08 | injective Borel chart에서 Gaussian pullback characteristic |
| A13 | PROVED | P08 | quotient kernel은 characteristic base+double Haar가 안전 |
| A14 | PROVED | P19 | equivariant quotient score의 finite-rank superuniformity |
| B01 | PROVED | P01 | sky RMS와 PSTF norm의 정확한 변환 |
| B02 | PROVED | P09 | STF2 normalized orbit interval과 uniaxial endpoints |
| B03 | PROVED | P09 | |tr Q^3| <= (tr Q^2)^(3/2)/sqrt(6), sharp |
| B04 | PROVED | P09 | trace power의 Cayley-Hamilton recurrence |
| B05 | PROVED | P09 | operator/directional sharp bound |
| B06 | PROVED | P10 | mixed moments의 Cayley-Hamilton closure |
| B07 | PROVED | P10 | simple spectrum에서 spectral weights 재구성 |
| B08 | PROVED | P10 | moment Hankel/Gram PSD와 det G=kappa^2 |
| B09 | PROVED | P10 | discriminant 및 determinant feasibility |
| B10 | PROVED | P11 | 3 beta_<a Q_bc>의 norm identity와 ceiling |
| B11 | PROVED | P12 | geodesic congruence vorticity decay-rate envelope |
| B12 | PROVED | P12 | tilt anisotropic stress가 d tr(sigma^3)/dt에 주는 mixed source |
| B13 | PROVED | P13 | product uncertainty body의 sharp support function |
| B14 | PROVED | P13 | ellipsoid Minkowski image의 SOCP characterization |
| B15 | PROVED | P13 | closed compact domain에서만 extrema 보장 |
| B16 | PROVED | P13 | Archimedean SOS hierarchy의 asymptotic convergence; finite exactness 불보장 |
| B17 | PROVED | P14 | commuting shear history에서 B=int sigma dt |
| B18 | STRENGTHENED | P14 | noncommuting history에서도 ||B||_F <= sqrt(6) I |
| B19 | STRENGTHENED | P14 | |tr B^3| <= 6 I^3, sharp |
| B20 | PROVED | P14 | budget 위반은 premise conjunction 중 하나 이상의 실패만 뜻함 |
| B21 | CORRECTED | P15 | one-sided remainder는 Hausdorff 안정성이 아님 |
| B22 | PROVED | P06 | trivial scalar representation은 nonzero vector/STF를 equivariantly 생성 불가 |
| C01 | PROVED | P16 | thermodynamic blackbody의 exact Lorentz pullback |
| C02 | PROVED | P16 | first-order quadrupole-to-octupole response 3 beta_<a Q_bc> |
| C03 | PROVED | P11 | (B_Q beta):Q=(q2 I+6 Q^2/5) beta |
| C04 | STRENGTHENED | P11 | Q != 0 response SPD, sharp condition number <=5/3 |
| C05 | PROVED | P11 | closed Frobenius least-squares boost inverse |
| C06 | PROVED | P11 | STF3의 response image 직교잔차 차원은 4 |
| C07 | REFUTED | P17 | 직교잔차 자체가 beta nonidentification을 유발; 실제로는 unrestricted additive O nuisance가 유발 |
| C08 | PROVED | P18 | ideal Bianchi-I blackbody에서 T^-2의 quadratic closure |
| C09 | PROVED | P18 | quadratic-form kernel은 A~A+h eta |
| C10 | PROVED | P18 | strict domain에서 Lorentzian generalized eigendata 재구성 |
| C11 | STRENGTHENED | P18 | strictly positive quadratic sky의 unique finite boost+positive-M representation |
| C12 | PROVED | P18 | T^-2의 ell>2 residual은 최소 하나의 ideal premise 실패 witness |
| C13 | PROVED | P18 | exact blackbody/bandpass inversion의 channel coherence |
| C14 | CORRECTED | P18 | channel incoherence는 common model을 기각하지만 원인을 유일하게 식별하지 않음 |
| C15 | PROVED | P20 | direct-T Gaussian WLS는 likelihood; inverse-square fit은 infinite-moment로 부적절 |
| C16 | PROVED | P20 | regular local tangent-projected first-order bias |
| C17 | PROVED | P20 | tangent-orthogonal contamination의 first-order bias cancellation |
| C18 | UNDEFINED | P21 | arbitrary projective T/Q/U universal finite-quadratic generalization 없음 |
| D01 | PROVED | P22 | full-rank affine radial design이 bulk3+expansion1+shear5 식별 |
| D02 | PROVED | P22 | radial velocity는 solid rotation을 식별하지 못함 |
| D03 | PROVED | P22 | 서로 다른 알려진 shell response가 local/global vector를 분리 |
| D04 | PROVED | P22 | free linear nuisance 하에서 projected design full rank iff 식별 |
| D05 | PROVED | P22 | free optical-depth amplitude의 scaling degeneracy |
| D06 | PROVED | P23 | exact physical set intersection은 identified set을 확대하지 않음 |
| D07 | PROVED | P23 | pointwise-valid test inversion의 true-point coverage |
| D08 | REFUTED | P23 | paired contrast가 validity에 필수 |
| E01 | PROVED | P19 | ties가 있는 weak finite rank는 superuniform이지 일반 uniform 아님 |
| E02 | CORRECTED | P19 | decreasing transform은 midrank u -> 1-u 및 tail swap |
| E03 | PROVED | P19 | outer adaptation 전체를 row-equivariantly replay하면 validity 유지 |
| E04 | PROVED | P19 | exact conditional label weights의 weighted-rank validity |
| E05 | UNDEFINED | P24 | 세 null-shift class의 소진성 정리 |
| E06 | CORRECTED | P24 | TV는 event를 제어; Wasserstein 단독은 아님 |
| E07 | PROVED | P25 | cone GLRT projection 공식은 bounded MES body에 그대로 적용 불가 |
| E08 | PROVED | P19 | equivariant cone/body score도 finite-pool calibration 가능 |
| E09 | STRENGTHENED | P25 | iid Gaussian equal-positive-shift에서 same-size sum test가 max보다 강함 |
| E10 | PROVED | P23 | pointwise p-value inversion의 true-point coverage |
| E11 | PROVED | P23 | 한 confidence set의 projection은 simultaneous true-point coverage; population identified set 전체가 아님 |
| E12 | PROVED | P26 | product e-process에는 conditional-valid increments 필요 |
| E13 | PROVED | P26 | predictable lane choice는 conditional e-validity 보존 시 허용 |
| E14 | PROVED | P26 | shared-data marginal e-values의 독립 곱 금지 |
| E15 | REFUTED | P27 | selection independence가 queried-label validity에 필요 |
| E16 | PROVED | P27 | single-query rank의 reference 증가가 일반 two-sample consistency를 보장하지 않음 |

---

# Part VIII. Wolfram/CAS receipt 요약

1. **Krylov determinant**
\[
\det K=-(\lambda_1-\lambda_2)(\lambda_1-\lambda_3)
(\lambda_2-\lambda_3)x_1x_2x_3.
\]

2. **STF cubic**
\[
q_3^2-\frac16q_2^3
=-\frac13(a-b)^2(2a+b)^2(a+2b)^2.
\]

3. **boost contraction and norm**
\[
(B_Q\beta):Q=(q_2I+\tfrac65Q^2)\beta,
\]
\[
\|B_Q\beta\|^2=3q_2\beta^2+\tfrac{18}{5}\beta\cdot Q^2\beta.
\]

4. **condition number**
\[
\max\kappa(R_Q)=\frac53
\]
at \(q_2=1\), spectrum \((-5,1,4)/\sqrt{42}\).

5. **sphere-integral normalization**
\[
\Delta_2=\frac{8\pi}{15},\qquad
\Delta_3=\frac{8\pi}{35}.
\]

6. **Gaussian inverse-square singularity**
\[
\lim_{y\to0}y^2\phi_{\mu,\sigma}(y)y^{-2}
=\phi_{\mu,\sigma}(0)>0.
\]

재실행용 Wolfram Language 파일은 동봉된
`htt_base_WU009_wolfram_receipts_20260831.wl`이다.

---

# Part IX. 최종 claim boundary

## 지금 논문에 안전하게 쓸 수 있음

- stored-real/complex harmonic Parseval identity;
- exact sky-RMS/PSTF conversion;
- generic Krylov orbit reconstruction과 degeneracy abstention;
- O(3)와 SO(3) chirality 구별;
- STF2 sharp inequalities와 moment feasibility;
- \(Q\to O\) boost response algebra, inverse, \(5/3\) condition bound;
- positive-quadratic **representation theorem**;
- finite-rank superuniformity의 정확한 조건;
- low-z linear identifiability 조건;
- C18/E05의 no-go/narrowing.

## Gate/authority lock 전에는 쓰면 안 됨

- 현재 \(98/301\), \(74/301\) 등을 corrected PSTF result로 재라벨링;
- quadratic-sky inverse를 Planck physical inference로 표현;
- scalar ceiling으로 direction/STF/Bianchi family를 식별;
- \(P12\)의 \(\pi_{ab}\) source 숫자계수를 normalization lock 없이 인쇄;
- \(P14\)의 \(B,I\)가 원 dossier와 동일하다고 exact replay 주장;
- arbitrary polarization finite-quadratic closure;
- three-class null taxonomy의 exhaustiveness;
- theory dossier가 locally replayed/certified되었다는 문구.

---

# References used for cross-checking

- R. Maartens, G. F. R. Ellis, W. R. Stoeger, *Limits on anisotropy and inhomogeneity from the cosmic background radiation*, Phys. Rev. D 51, 1525 (1995).
- R. Maartens, G. F. R. Ellis, W. R. Stoeger, *Improved limits on anisotropy and inhomogeneity from the cosmic background radiation*, Phys. Rev. D 51, 5942 (1995).
- W. R. Stoeger, M. E. Araujo, T. Gebbie, *The Limits on Cosmological Anisotropies and Inhomogeneities from COBE Data*, astro-ph/9904346.
- J.-P. Börnsen, A. E. M. van de Ven, *Tangent Developable Orbit Space of an Octupole*, arXiv:1807.04817.
- L. Dai, J. Chluba, *New operator approach to the CMB aberration kernels in harmonic space*, Phys. Rev. D 89, 123504 (2014), arXiv:1403.6117.
- S. Mukherjee, A. De, T. Souradeep, *Statistical Isotropy violation of CMB polarization sky due to Lorentz boost*, Phys. Rev. D 89, 083005 (2014), arXiv:1309.3800.
- O. Roldan, A. Notari, M. Quartin, *Interpreting the CMB aberration and Doppler measurements: boost or intrinsic dipole?*, JCAP (2016), arXiv:1603.02664.

---

## One-line verdict

**수학 내용은 대부분 재구성 완료됐지만, Paper A는 PSTF normalization successor replay와 P12/P14 notation authority lock 전까지 이론적으로도 출판 가능한 final 상태가 아니다.**
