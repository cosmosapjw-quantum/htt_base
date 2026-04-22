# 03B. Frozen Backend Constants and Lookup Resolution
## all former unresolved backend/normalization items frozen into explicit formulas

---

## 0. purpose

이 문서는 v4 bundle에 남아 있던 former unresolved placeholder policy 대상들을
**실제 frozen formula / constant / adapter contract** 로 바꾸기 위한 authority addendum이다.

이 문서의 목적은 두 가지다.

1. implementation agent가 unresolved backend detail을 추측으로 채우지 못하게 한다.
2. symbolic / numerical verification script가 바로 읽을 수 있는 frozen formulas를 한곳에 모은다.

이 문서에 적힌 식은
- primary literature에서 직접 가져온 것,
- 그 식들 사이의 algebraic bridge를 package convention에 맞게 변환한 것,
- 또는 package-wide collocation fallback으로 명시적으로 채택한 것
중 하나다.

---

## 1. intrinsic-family seed normalization convention

이제 intrinsic-family seed card에는 unresolved normalization placeholder를 남기지 않는다.

패키지-wide frozen convention은

\[
\langle \phi,\psi\rangle_h \equiv \sum_{q\in\mathcal G} w_q\,\phi_q^\ast\psi_q,
\qquad
\|\phi\|_h^2 = \langle \phi,\phi\rangle_h.
\]

SeedPack normalization metadata는 아래와 같이 고정한다.

```text
normalization = {
    "amp_ref": "disc_L2_unit",
    "mu_ref": "native_cross_section_label",
    "inner_product": "<phi,psi>_h = sum_q w_q phi_q^* psi_q",
    "norm_rule": "<phi,phi>_h = 1",
    "phase_rule": "phi(q_anchor) in R_{>0}"
}
```

analytic normalization이 나중에 추가되더라도,
release convention은 위 discrete weighted \(L^2\) normalization이다.
analytic normalization은 refinement limit에서 위 convention과 일치함을 보여야만 선택적으로 허용된다.

---

## 2. canonical class-B gauges and parameter bridges

패키지 canonical gauge는 다음으로 동결한다.

\[
\begin{array}{c|c}
\text{Type} & (n_1,n_2,n_3;a)\\
\hline
VI_0 & (0,1,-1;0)\\
VI_h & (0,1,-1;\sqrt{-h}),\quad h<0\\
VII_0 & (0,1,1;0)\\
VII_h & (0,1,1;\sqrt{h}),\quad h>0
\end{array}
\]

class-B parameter는

\[
h=\frac{a^2}{n_2 n_3}
\]

으로 정의한다.

### VI\(_h\) ↔ solvable-family \(q\) bridge

패키지에서 채택하는 bridge는

\[
h=-\left(\frac{1-q}{1+q}\right)^2,
\qquad
q=\frac{1-\sqrt{-h}}{1+\sqrt{-h}}.
\]

이 식은 다음 branch를 포함한다.

- \(q=0 \iff h=-1\): Type III special branch
- \(q=1 \iff h=0^{-}\): Type VI\(_0\) limit
- \(q>0\) corresponds to \(-1 < h < 0\)
- \(q<0\) corresponds to \(h < -1\)

### VII\(_h\) ↔ \(p\) bridge

패키지에서 채택하는 bridge는

\[
p=\sqrt{h},\qquad h=p^2,\qquad h>0.
\]

---

## 3. explicit backend data for solvable intrinsic families

아래 식은 backend card에서 직접 쓸 수 있는 frozen constants다.

### Type II

\[
K_{II}=\mathbb R\setminus\{0\},\qquad
\check k_0(k)=(0,k),\qquad
\rho_{II}(k,r)=|k|,\qquad
\dot\nu_{II}(k)=|k|.
\]

### Type III \((VI_{-1})\)

\[
K_{III}=\mathbb R\times\{\pm1\},\qquad
k=(k_1,k_2),\qquad
\check k_0(k)=(k_2,k_1),
\]
\[
\rho_{III}(k,r)=e^{-r},\qquad
\dot\nu_{III}(k)=1.
\]

### Type IV

\[
K_{IV}=\mathbb R_0^+\times\{\pm1\},\qquad
k=(k_1,k_2),\qquad
\check k_0(k)=(k_2,k_2 k_1),
\]
\[
\rho_{IV}(k,r)=e^{-2r}(1+k_1),\qquad
\dot\nu_{IV}(k)=1+k_1.
\]

### Type VI\(_0\)

이는 \(q=1\) branch로 취급한다. native labels는
\[
k=(k_1,k_2)\in\mathbb R_0^+\times\mathbb Z_4
\]
로 잡고,
\[
\check k_0(k)=R_{\pi/2}^{\,k_2}(1,k_1),\qquad
\dot\nu_{VI_0}(k)=1.
\]

### Type VI\(_h\)

#### \(q>0\) branch \((-1<h<0)\)

\[
K=\mathbb R_0^+\times\mathbb Z_4,\qquad
\check k_0(k)=R_{\pi/2}^{\,k_2}(1,k_1),
\qquad
\dot\nu=q^{\,k_2 \bmod 2}.
\]

#### \(q<0\) branch \((h<-1)\)

\[
K=\mathbb R/2\pi\mathbb Z,\qquad
\check k_0(k)=(\cos k,\sin k),
\qquad
\dot\nu=\cos^2 k-q\sin^2 k.
\]

### Type VII\(_h\)

\[
K_{VII_h}=(-e^{\pi p},-1]\cup[1,e^{\pi p}),
\qquad
\check k_0(k)=(k,0),
\]
\[
\rho_{VII_h}(k,r)=e^{-2pr}|k|,
\qquad
\dot\nu_{VII_h}(k)=|k|.
\]

---

## 4. Type VIII analytic principal/discrete-series backend

Type VIII는 \(\widetilde{SL}(2,\mathbb R)\)-type noncompact backend로 동결한다.

### continuous/principal-series sector

label을
\[
(\mu,s),\qquad -\frac12 \le \mu < \frac12,\qquad s\ge 0
\]
로 잡고, continuous Plancherel density를

\[
\rho^{\mathrm{cont}}_{VIII}(\mu,s)
=
\frac{1}{(2\pi)^2}
\frac{s\,\sinh(2\pi s)}{\cosh(2\pi s)+\cos(2\pi\mu)}
\]

로 동결한다.

### discrete-series sector

label을
\[
D_\lambda^\pm,\qquad \lambda\ge \frac12
\]
로 잡고, discrete Plancherel density를

\[
\rho^{\mathrm{disc}}_{VIII}(\lambda)
=
\frac{1}{(2\pi)^2}\left(\lambda-\frac12\right)
\]

로 동결한다.

### special reductions

\[
\rho^{\mathrm{cont}}_{VIII}(0,s)
=
\frac{1}{(2\pi)^2}s\,\tanh(\pi s),
\]
\[
\rho^{\mathrm{cont}}_{VIII}\!\left(\frac12,s\right)
=
\frac{1}{(2\pi)^2}s\,\coth(\pi s).
\]

이 둘은 parity-restricted sector check로 사용한다.

### native label card for Type VIII

```text
NativeLabelCard(
    family="VIII",
    native_labels={"mu": mu, "s": s} or {"lambda": lam, "series": "D+"|"D-"},
    parity_flag=None,
    helicity_flag=None,
    branch_flag="principal"|"discrete",
    to_storage(...),
    from_storage(...)
)
```

analytic backend를 쓰지 않더라도,
collocation fallback은 반드시 이 label/measure convention을 metadata로 기록해야 한다.

---

## 5. generic scalar spectral ODE contract for II–VII solvable families

solvable groups II–VII에서는 scalar eigenfunction을

\[
\zeta(\check x,z)
=
e^{i\langle \check k_C,\check x\rangle}P(z)
\]

로 두고, \(P\) 가 아래 ODE를 만족하도록 동결한다.

\[
\check h_{33}P''
+
i\,\check k_C^\top F(z)\!\left[\check h_{\bullet3}+(\check h_{3\bullet})^\top\right]P'
-
\Big(
\lambda
+
\check k_C^\top F(z)\check h_{2\times2}F^\top(z)\check k_C
-
i\,\check h_{3\bullet}F^\top(z)M^\top\check k_C
\Big)P
=0.
\]

orbit parameterization
\[
\check k_C = F^\perp(r)\check k_0(-k)
\]
를 쓰면 shifted basis는
\[
P_{\lambda,k,r}(z)=P_{\lambda,k}(z-r)
\]
로 동결한다.

---

## 6. cross-card collocation defaults

analytic backend가 없는 family는 아래 finite-difference collocation fallback을 쓴다.

1D grid
\[
x_i=x_{\min}+ih,\qquad i=0,\dots,N
\]
에서 trapezoid weights는

\[
w_0=w_N=\frac h2,\qquad w_i=h\quad (1\le i\le N-1).
\]

4th-order centered bulk stencil:

\[
f'_i=\frac{f_{i-2}-8f_{i-1}+8f_{i+1}-f_{i+2}}{12h},
\qquad
f''_i=\frac{-f_{i-2}+16f_{i-1}-30f_i+16f_{i+1}-f_{i+2}}{12h^2},
\quad i=2,\dots,N-2.
\]

default boundary derivative closure:

\[
f'_0=\frac{-3f_0+4f_1-f_2}{2h},
\qquad
f'_N=\frac{3f_N-4f_{N-1}+f_{N-2}}{2h}.
\]

이제 collocation default 자체는 unresolved item이 아니다.
family card가 따로 spectral backend를 선언하지 않는 한, 위 stencil/weight/closure가 package default다.

---

## 7. HEALPix / healpy harmonic packing freeze

\(a_{\ell m}\) packed order는 m-major로 동결한다.
index formula는

\[
\mathrm{idx}(\ell,m;\ell_{\max})
=
\frac{m(2\ell_{\max}+1-m)}{2}+\ell,
\qquad
0\le m\le \ell\le \ell_{\max}.
\]

real sky field는
\[
a_{\ell,-m}=(-1)^m a_{\ell m}^\ast
\]
를 강제한다.

FITS map metadata는 다음을 동결한다.

- `PIXTYPE='HEALPIX'`
- `ORDERING='RING'` or `'NESTED'`
- `NSIDE`
- `FIRSTPIX=0`
- `LASTPIX=12 NSIDE^2 - 1`
- polarized map일 때 `POLAR=T`, `POLCCONV='COSMO'`

---

## 8. frozen HYREC-like adapter contract

default recombination backend는 HYREC-2-compatible adapter다.

solver-facing I/O contract:

inputs:
\[
h,\ T_0,\ \Omega_b,\ \Omega_{cb},\ \Omega_k,\ w_0,\ w_a,\ N_{m\nu},\ m_{\nu i},\ Y_{\rm He},\ N_{\rm eff},\dots
\]

outputs:
\[
(z,\ x_e(z),\ T_m(z)).
\]

opacity contract:

\[
n_H(z)=\frac{(1-Y_{\rm He})\rho_b(z)}{m_H},
\qquad
n_e(z)=x_e(z)\,n_H(z),
\]
\[
\dot\kappa(\eta)=a(\eta)\,n_e(\eta)\,\sigma_T\,c,
\qquad
\tau'(\eta)=-\dot\kappa(\eta),
\qquad
g(\eta)=\dot\kappa(\eta)e^{-\tau(\eta)}.
\]

modified recombination engine를 써도, 위 I/O와 opacity contract는 유지해야 한다.

---

## 9. documentary status

이 문서가 존재한다는 뜻은
**이제 v4에 남아 있던 literal former unresolved placeholder 대상은 active unresolved item이 아니라 frozen formula set으로 승격되었다** 는 뜻이다.

향후 새 unresolved item이 생기면, 이 문서와 같은 형식의 frozen addendum을 먼저 만들어야 한다.
