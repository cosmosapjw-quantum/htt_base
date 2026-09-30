# TEFF number–energy interval: immutable mathematical input for CAS-13

This file specifies targets for independent rederivation. It contains no CAS execution, proof-checker result, or renewed scientific acceptance. The mathematical statements below are transcribed from the user-supplied manuscript, not from another CAS axis. Each axis must derive its own interpolation coefficients, reductions and proof obligations.

## Source identity and inspected locations

- Source: *Effective-Temperature Multipoles for Relativistic Kinetic States. II. Number–Energy Refinement and Velocity-Dressed Coarse-Graining Geometry*, user manuscript.
- Uploaded PDF: `upload/TEFF_PAPER_II_revised(2).pdf`.
- PDF SHA-256: `299870d7174ed560393c87e8dd6193643a614e7a1185ab1be2c5c2dc73c9b5f9`.
- Extracted text: `gr_statistics_loops_20260930/references/TEFF_PAPER_II_revised.txt`.
- Text SHA-256: `241a9c63242b077ca56d87ffe0936d4971249ee08a7d0fe27659e2ab768bf6a0`.
- Printed/PDF page 13: §VIII.A–B, Eqs. (119)–(126), Proposition 14.
- Printed/PDF page 14: Eqs. (127), (129)–(130), used below only for polynomial and fixed-prior counterexample targets.
- Printed/PDF page 20: Appendix E heading and feasibility setup.
- Printed/PDF page 21: Appendix E.1, Eqs. (E1)–(E5), elementary interpolation certificates.
- No source numerical percentages, plots, archive outputs, or whole-manuscript validation are part of this contract. Manuscript p. 14 asymptotic Eq. (128) is not an additional task here.

## 1. Common prior, dimensions and retained data

Let \(0<a<b\), let \(\pi\) be a probability measure on \([a,b]\), and put
\[
m_p=\int_a^b y^p\,d\pi(y).
\]
The variable \(y=T/T_*\) and all \(m_p\) are dimensionless. The thermal occupation is
\[
f(E)=\int_a^b
 \frac{d\pi(y)}{\exp[E/(k_BT_*y)-\eta_0]-\xi},
\]
with fixed statistics \(\xi\), one common admissible log-fugacity \(\eta_0\), one normalization, one positive \(T_*\), and one support prior. Number and energy are proportional respectively to \(m_3,m_4\) with the common statistics factors specified in source Eq. (120). The retained numbers \(m_3,m_4\) already have those factors removed.

The oracle target is \(m_p\), \(p>4\). Reaction-number and energy-deposition examples \(p=5,6\) use idealized massless \(E^2\) kernels. They are not automatically CMB observation kernels. Do not vary fugacity/support/normalization between the energy-only and number–energy comparisons.

## 2. Interior feasible data and two principal measures

The strict interior contract is
\[
a^3<m_3<b^3,\qquad
m_3^{4/3}<m_4<
a^4+\frac{m_3-a^3}{b^3-a^3}(b^4-a^4).
\tag{S121}
\]
Define the nodes \(u,d\) by
\[
u\in(m_3^{1/3},b),\qquad
\frac{u^4-a^4}{u^3-a^3}=\frac{m_4-a^4}{m_3-a^3},
\]
\[
d\in(a,m_3^{1/3}),\qquad
\frac{b^4-d^4}{b^3-d^3}=\frac{b^4-m_4}{b^3-m_3}.
\tag{S122}
\]
The weights and proposed extremizers are
\[
w_u=\frac{m_3-a^3}{u^3-a^3},\qquad
w_b=\frac{m_3-d^3}{b^3-d^3},
\]
\[
\pi_L=(1-w_u)\delta_a+w_u\delta_u,\qquad
\pi_U=(1-w_b)\delta_d+w_b\delta_b.
\tag{S123}
\]
Required targets include unique admissible nodes, \(0<w_u,w_b<1\), normalization, and exact matching of both \(m_3,m_4\). Clearing denominators is permitted only after retaining their positivity/nonzero conditions.

The source monotonicity identity to independently reproduce is
\[
\frac{d}{du}\frac{u^4-a^4}{u^3-a^3}
=
\frac{u^2(3a^2+2au+u^2)}{(a^2+au+u^2)^2}>0.
\tag{SE1}
\]
The corresponding upper-node monotonicity must be derived independently with the same positive interval restrictions.

## 3. Sharp interval and minimax target

Define
\[
L_p=(1-w_u)a^p+w_u u^p,\qquad
U_p=(1-w_b)d^p+w_b b^p.
\tag{S124}
\]
The target statement is \(L_p\le m_p\le U_p\) for every measure in the same retained-moment class, with equality attained by the displayed measures.

For a positive interval \([L_p,U_p]\), the specified loss is
\[
\sup_{m\in[L_p,U_p]}\left|\frac{\widehat m-m}{m}\right|.
\]
The proposed relative-minimax predictor and worst loss are
\[
\widehat m_p=\frac{2L_pU_p}{L_p+U_p},\qquad
\epsilon_p=\frac{U_p-L_p}{U_p+L_p}.
\tag{S125}
\]
The positivity domain is essential; this is not the minimax solution for absolute squared error or a stochastic risk.

Under the same support prior with only \(m_4\) retained, the comparison interval is
\[
L_p^{(E)}=m_4^{p/4},\qquad
U_p^{(E)}
=\frac{(b^4-m_4)a^p+(m_4-a^4)b^p}{b^4-a^4}.
\tag{S126}
\]

For all real \(p>4\), the source invokes a principal-representation theorem for a Chebyshev moment system. The finite Wronskian target is
\[
W(1,y^3,y^4,y^p)=12p(p-3)(p-4)y^{p+1}>0.
\tag{SE2}
\]
A Wronskian calculation alone is not a proof that the proposed principal measures bound all probability measures. Each axis must provide the general analytic extremizer theorem and its hypotheses, or mark the general-\(p\) assertion as an open analytic obligation. The \(p=5,6\) certificates below provide a separate bounded route.

## 4. Finite polynomial certificates for p=5 and p=6

For each \(p\in\{5,6\}\), define
\[
Q_{p,a,u}(y)=c_0+c_3 y^3+c_4 y^4
\]
by the three interpolation conditions
\[
Q_{p,a,u}(a)=a^p,\quad
Q_{p,a,u}(u)=u^p,\quad
Q_{p,a,u}'(u)=p u^{p-1}.
\]
Every axis must independently solve this system. No solved coefficients or intermediate reduction from another axis may be read.

Let
\[
\Delta_{a,u}=3a^2+2au+u^2.
\]
The exact source targets are
\[
y^p-Q_{p,a,u}(y)=
\frac{(y-a)(y-u)^2}{\Delta_{a,u}}P_p(y;a,u),
\tag{SE3}
\]
\[
P_5=\Delta_{a,u}y^2+(2a^2u+au^2)y+a^2u^2,
\tag{SE4}
\]
\[
\begin{split}
P_6={}&\Delta_{a,u}y^3
 +(3a^3+8a^2u+5au^2+2u^3)y^2\\
 &+(2a^3u+5a^2u^2+2au^3)y
 +a^3u^2+2a^2u^3.
\end{split}
\tag{SE5}
\]
The lower certificate uses \(a>0,u>a,y\in[a,b]\). The upper certificate replaces \((a,u)\) by \((b,d)\), with \(b>0,d>0\), and uses \(y-b\le0\). Denominators remain positive in both cases. The lower and upper interpolation-node measures must independently be checked to attain equality and match the same retained moments.

Required negative controls:

- Swapping a sourceward/observer convention is irrelevant here; do not import GR signs into this purely positive moment problem.
- The cases \(u=a\) or \(d=b\) are not admissible interior node equations.
- Feasibility boundary data must use limits of measures, not evaluation of \(0/0\) node formulas.
- A positive polynomial certificate for \(p=5,6\) cannot be labeled a proof for all real \(p>4\).
- Merely finding two feasible measures is not proof that their moments are extrema; the signed interpolation or full moment theorem is required.

## 5. Cubic local polynomial and fixed-prior MaxEnt distinction

On support \([1-s,1+s]\), \(0<s<1\), the source power-response polynomial is
\[
Q_p(y)=\frac{(p-3)(p-4)}{12}
+\frac{p(4-p)}{3}y^3+\frac{p(p-3)}4y^4.
\tag{S127}
\]
Its target is agreement with \(y^p\) through derivative order two at \(y=1\). This is a finite-algebra target; the integrated cubic remainder still needs a Taylor theorem and support assumptions.

A bounded source example for the statement “the entropy-selected matched frame need not lie in the fixed-fugacity mixture fibre” uses
\[
a=\frac45,\quad b=\frac65,\quad
m_3=\frac{26}{25},\quad m_4=\frac{3376}{3125}.
\]
For Maxwell–Boltzmann statistics and initial \(\eta_0=0\), the displayed matched-frame power responses are
\[
m_5^{\rm frame}=\frac{m_4^2}{m_3}
=\frac{5698688}{5078125},\qquad
m_6^{\rm frame}=\frac{m_4^3}{m_3^2}
=\frac{9619385344}{8251953125},
\]
and
\[
\eta_{\rm eff}-\eta_0=4\log m_3-3\log m_4
=\log\frac{2231328125}{2404846336}.
\tag{S129-130}
\]
If this example is executed, require exact algebraic root isolation or a proved rational/interval bound showing the frame values lie below the corresponding \(L_5,L_6\). Do not reuse printed decimals or percentages as evidence. No FD/BE numerical frame inversion is requested.

## 6. Evidence and promotion boundaries

The specification resolves missing formula inputs for CAS-13. It does not resolve the proof obligations. Record separately:

1. Exact polynomial/ratio/minimax algebra.
2. Node existence, feasibility and measure-extremality proof.
3. General real-\(p\) theorem versus bounded \(p=5,6\) theorem.
4. Bandpass Taylor/integrability assumptions.
5. Engine or proof-checker availability.

All current statuses are NOT_EXECUTED. No scientific claim is promoted by this transcription.

