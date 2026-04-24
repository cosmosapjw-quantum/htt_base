## Q-8.1 — Taxonomy of the 10 scales

The Round-2 theorem already forces the key conclusion: **the family dependence cannot live in ten empirical scalars.** In a (1+3) PSTF formulation with tetrad/invariant-basis engine, family dependence enters through projected contractions of (a^\alpha), (n^{\alpha\beta}), (C^\gamma{}*{\alpha\beta}), (\sigma*{\alpha\beta}), and the mode-basis projectors. Therefore the correct objects are operator-valued in the (\mu)-label space, and only reduce to scalars in special isotropic-anchor subclasses. This is exactly the structural lesson of the Ellis–van Elst tetrad formalism, the covariant CMB hierarchy of Maartens–Gebbie–Ellis, and the nearly-FRW Bianchi transfer hierarchy of Pontzen–Challinor. ([ResearchGate][1])

Let (X\in{T,E,B,\nu}) denote a channel, let (\mu,\mu') index the family mode labels, and let ((\ell,m)) denote the spherical/PSTF tower slot. Then:

| placeholder          | correct object after replacement                                                                                                                                       | reason from (1+3) PSTF/tetrad hierarchy                                                                                     | minimum tower connectivity                                                        |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `transport_scale`    | (M_{\mu\mu'}) (often diagonal in a frozen backend basis)                                                                                                               | mode-eigenvalue / transport generator depends on family harmonic analysis                                                   | (\ell'!=!\ell\pm1) from free streaming; no extra (\ell)-mix from the scale itself |
| `mix_scale`          | (M_{(\mu,\ell m)(\mu',\ell' m')}), but in FLRW this collapses to (\delta_{\mu\mu'}\delta_{\ell2}\delta_{\ell'2}) times (\dot\kappa)-derived (T\leftrightarrow E) block | Thomson quadrupole source, not a family scalar                                                                              | only (\ell=\ell'=2), (m'=m)                                                       |
| `twist_mix_scale`    | (M_{(\mu,\ell m)(\mu',\ell' m')})                                                                                                                                      | (a^\alpha) is a rank-1 geometric coupling; it changes (\ell) by (\pm1) and (m) by (q=0,\pm1) depending on axis choice       | (\ell'=\ell\pm1), (m'=m+q)                                                        |
| `polarization_scale` | genuine scalar (s=1) in a fixed storage convention                                                                                                                     | no independent family physics; channel normalization belongs in state definition, not family law                            | none                                                                              |
| `source_scale`       | (M_{(\mu,\ell m)(\mu',\ell' m')}) **if** geometry/source coupling is kept inside source assembly; otherwise no independent "scale" at all                              | curvature/shear/twist affect source operators, not a scalar multiplier                                                      | source-specific, but at minimum (\ell) local and (\mu)-mixed                      |
| `mass_scale`         | (s_\mu) (vector diagonal in (\mu))                                                                                                                                     | effective local momentum/expansion drag is mode-dependent but does not mix (\mu) at linear order in the local block         | no tower connectivity                                                             |
| `local_drag_scale`   | (s_\mu) (vector diagonal in (\mu))                                                                                                                                     | (R_\mu^{-1}) is mode-dependent once class-B tilt projects on (a^\alpha), but still local                                    | no tower connectivity                                                             |
| `cross_mode_scale`   | (M_{\mu\mu'})                                                                                                                                                          | this is exactly the (\mu)-mixing kernel and cannot be scalar                                                                | none by itself; tower structure supplied elsewhere                                |
| `collision_scale`    | genuine scalar (s=1)                                                                                                                                                   | (\dot\kappa) is universal once background electron density is fixed; family dependence does not enter Thomson cross section | no tower connectivity                                                             |
| `mode_plus_scale`    | (M_{\mu\mu'})                                                                                                                                                          | helicity-partner weighting is a basis choice in the (\mu)-space, not a scalar law                                           | none by itself                                                                    |
| `mode_minus_scale`   | (M_{\mu\mu'})                                                                                                                                                          | same as above                                                                                                               | none by itself                                                                    |

So the correct summary is:

[
\boxed{
\begin{aligned}
&\text{operator-valued in }\mu: && \texttt{transport_scale},\ \texttt{cross_mode_scale},\ \texttt{mode_plus/minus},\
&\text{operator-valued in }(\mu,\ell,m): && \texttt{mix_scale},\ \texttt{twist_mix_scale},\ \texttt{source_scale},\
&\mu\text{-diagonal vectors}: && \texttt{mass_scale},\ \texttt{local_drag_scale},\
&\text{true scalars}: && \texttt{collision_scale}=1,\ \texttt{polarization_scale}=1.
\end{aligned}
}
]

For the explicitly geometric tower couplings, the minimal (1+3) connectivity is standard:

* vector-type couplings ((a^\alpha)) induce (\ell\to\ell\pm1),
* tensor-type couplings ((n^{\alpha\beta}), (\sigma^{\alpha\beta})) induce (\ell\to\ell,\ell\pm2),

with (m)-selection governed by the corresponding Wigner/Clebsch coefficients in the chosen real basis. ([ScienceDirect][2])

---

## Q-8.2 — mu-mode cross-coupling matrices (5 families)

### General form

The family-conditioned (\mu)-mixing must be built from **projected algebra tensors**, not hand-tuned scalars. In the frozen canonical real storage basis ((\mu_0,\mu_+,\mu_-)), the minimal replacement is

[
C^{(X)}_{\mu\mu'}(\ell,m)
=========================

\alpha^{(X)}*{\ell m},\mathcal N*{\mu\mu'}
+
\beta^{(X)}*{\ell m},\mathcal A*{\mu\mu'},
\qquad X\in{T,E,B,\nu},
]

where

[
\mathcal N_{\mu\mu'} \equiv \Pi_\mu{}^\alpha, n_{\alpha\beta},\Pi_{\mu'}{}^\beta,
\qquad
\mathcal A_{\mu\mu'} \equiv \Pi_\mu{}^\alpha, \hat a_\alpha \hat a_\beta,\Pi_{\mu'}{}^\beta,
\qquad
\hat a_\alpha = \frac{a_\alpha}{|a|}\ \ (|a|>0).
]

Here (\Pi_\mu{}^\alpha) is the frozen backend basis map from the canonical algebra axes to the real mode-label basis. In the simplest canonical real basis used by the prompt, (\Pi = I_3), so (\mathcal N=n) and (\mathcal A=\hat a\hat a^T). The (\alpha^{(X)}*{\ell m}) and (\beta^{(X)}*{\ell m}) are **not empirical sector constants**; they are the Wigner/PSTF projection coefficients already present in the ((\ell,m))-operator, i.e. they should be 1 once those coefficients are factored into the slot-level tables. This is the cleanest way to interpret the Round-2 conclusion that the current `0.18/0.16/0.12` sector multipliers are placeholders rather than physics. ([ScienceDirect][2])

So the correct statement for part (c) is:

[
\boxed{
\text{After factoring the slot/Wigner/PSTF coefficients into the tower operator, }
C^{(ph_I)}=C^{(\nu_I)}=\mathcal N+\mathcal A,\quad
C^{(ph_E)}=C^{(ph_B)}=\mathcal N+\mathcal A,
}
]
up to any fixed channel-normalization similarity transform already frozen in the storage basis. There is **no independent** `0.18/0.16/0.12` physics.

### (a) Class-A families: Type II and Type VIII

For class A, (a=0), so only (\mathcal N) survives.

#### Type II

Canonical data:
[
n = \operatorname{diag}(1,0,0),\qquad a=0.
]

Hence
[
\mathcal N_{II}
===============

\begin{pmatrix}
1&0&0\
0&0&0\
0&0&0
\end{pmatrix},
\qquad
C^{(X)}*{II} = \alpha^{(X)}*{\ell m},\mathcal N_{II}.
]

This matrix has
[
\operatorname{rank}(\mathcal N_{II})=1.
]

So Type II is rank-1 in (\mu)-space: there is one commutator direction and two null directions. This is exactly what the nilpotent Heisenberg structure should do.

#### Type VIII

Canonical data:
[
n = \operatorname{diag}(-1,1,1),\qquad a=0.
]

Hence
[
\mathcal N_{VIII}
=================

\begin{pmatrix}
-1&0&0\
0&1&0\
0&0&1
\end{pmatrix},
\qquad
C^{(X)}*{VIII} = \alpha^{(X)}*{\ell m},\mathcal N_{VIII}.
]

This has
[
\operatorname{rank}(\mathcal N_{VIII})=3.
]

So Type VIII is semisimple and full-rank in (\mu)-space, as expected.

### (b) Class-B families: Type V and Type III

For class B with (a\neq 0), the minimal additional (\mu)-mixing comes from the projector along (a), i.e. (\mathcal A).

#### Type V (pure twist)

Canonical data:
[
n=0,\qquad a=(1,0,0).
]

Then
[
\hat a = (1,0,0),\qquad
\mathcal A_V = \hat a\hat a^T =
\begin{pmatrix}
1&0&0\
0&0&0\
0&0&0
\end{pmatrix},
]
and therefore
[
C_V^{(X)} = \beta^{(X)}_{\ell m},\mathcal A_V.
]

So Type V is again rank-1 in (\mu)-space, but now through the twist vector rather than (n^{\alpha\beta}).

#### Type III

Canonical data:
[
n=\operatorname{diag}(0,1,-1),\qquad a=(1,0,0).
]

Hence
[
\mathcal N_{III}
================

\begin{pmatrix}
0&0&0\
0&1&0\
0&0&-1
\end{pmatrix},
\qquad
\mathcal A_{III}
================

\begin{pmatrix}
1&0&0\
0&0&0\
0&0&0
\end{pmatrix}.
]

So
[
C^{(X)}_{III}
=============

\alpha^{(X)}*{\ell m},
\begin{pmatrix}
0&0&0\
0&1&0\
0&0&-1
\end{pmatrix}
+
\beta^{(X)}*{\ell m},
\begin{pmatrix}
1&0&0\
0&0&0\
0&0&0
\end{pmatrix}.
]

This is the minimal real (3\times 3) class-B replacement consistent with the frozen canonical gauge.

### (c) Sector-dependent prefactors (0.18/0.16/0.16/0.12)

These numbers are **not** physical coefficients. The correct sector dependence comes from:

1. the channel row scaling (d^{(X)}_\ell),
2. the spin-dependent Wigner/PSTF coefficient already sitting in the ((\ell,m))-raising/lowering tables,
3. for collision-generated (T/E) mixing only, the Thomson coefficient (\sqrt6/10).

For the **geometric (\mu)-mixing** at issue here, there is no separate Thomson factor. Therefore the correct sector coefficients are simply those induced by the chosen slot normalization; after factoring that out, the family matrix is the same (\mathcal N+\mathcal A) object across sectors. In particular:

[
\boxed{
0.18,\ 0.16,\ 0.16,\ 0.12\ \text{must be deleted, not re-fitted.}
}
]

### (d) Type-I limit

Type I has
[
n=0,\qquad a=0.
]
Therefore
[
\mathcal N_I=0,\qquad \mathcal A_I=0,
]
and hence
[
C^{(X)}_{I}=0
\quad\text{for all }X\in{T,E,B,\nu}.
]

So every proposed (\mu)-mode coupling matrix collapses to the zero matrix in the Type-I limit, which preserves the FLRW invariant manifold (r_h\equiv 0,\ b_{hh}\equiv 0) and therefore leaves the (D_2) anchor algebraically protected.

### Explicit (3\times 3) matrices for the five representative families

Using the canonical real basis ((\mu_0,\mu_+,\mu_-)) and factoring all ((\ell,m)) Wigner/PSTF coefficients out of the (\mu)-matrices, the minimal (\mu)-space transport/cross-mode kernels are:

[
C^{(T)}_{II}
============

\begin{pmatrix}
1&0&0\
0&0&0\
0&0&0
\end{pmatrix},
]

[
C^{(T)}_{III}
=============

\begin{pmatrix}
|a|&0&0\
0&1&0\
0&0&-1
\end{pmatrix}
\quad\text{with }|a|=1,
]

[
C^{(T)}_{V}
===========

\begin{pmatrix}
|a|&0&0\
0&0&0\
0&0&0
\end{pmatrix}
\quad\text{with }|a|=1,
]

[
C^{(T)}_{VII_0}
===============

\begin{pmatrix}
0&0&0\
0&1&0\
0&0&1
\end{pmatrix},
]

[
C^{(T)}_{VIII}
==============

\begin{pmatrix}
-1&0&0\
0&1&0\
0&0&1
\end{pmatrix}.
]

The same matrices apply to (E,B,\nu) once the slot-level spin normalization is handled elsewhere. These all reduce continuously to the zero matrix when (a\to0,\ n\to0). The nearly-FRW Bianchi literature supports exactly this kind of geometry-first, family-by-family operator construction rather than empirical scalar family factors. ([OUP Academic][3])

---

## Q-8.3 — transport_scale as mode-eigenvalue matrix

The replacement for `transport_scale` is **not** a family scalar. It is the backend mode-eigenvalue matrix

[
Q_\mu = \operatorname{diag}(q_{\mu_0},q_{\mu_+},q_{\mu_-})
]
in the frozen real storage basis, or more generally the real-symmetric matrix representing the backend transport generator in that basis. This follows directly from the spectral ODE in the prompt: the transport scale is the spectral parameter (\nu_\mu) / Laplace–Beltrami eigenvalue label, not a scalar norm of (n,a,R,\sigma). Pontzen–Challinor's linearized Bianchi treatment and the harmonic-analysis program behind Bianchi mode decompositions both support this reading. ([ResearchGate][4])

### Type II

Given the frozen backend data
[
\dot\nu_{II}(k)=|k|,\qquad \rho_{II}(k,r)=|k|,
]
the transport eigenvalue is
[
q_{II}(k)=|k|.
]
So
[
Q_{II}(k)=|k|,I_3.
]

Comparison with the placeholder:
[
1.10\cdot \sqrt{1^2+\cdots}
]
shows the placeholder is dimensionless and mode-independent, whereas the correct object is mode-dependent and scales linearly with (|k|).

### Type III

The frozen data give
[
\dot\nu_{III}(k)=1,\qquad \rho_{III}(k,r)=e^{-r}.
]
So the **operator eigenvalue** is
[
q_{III}=1,
]
while the radial weight (e^{-r}) belongs to the measure / basis normalization, not to the transport coefficient. Therefore
[
Q_{III}=I_3.
]

The current `1.16` placeholder is just a family-tuned scalar and has no spectral meaning.

### Type V

This one is the open-hyperbolic anchor family. In the standard open-FRW harmonic normalization, the scalar Laplacian eigenvalue is
[
-(k^2+1),
]
so the transport wavenumber is
[
q_V(k)=\sqrt{k^2+1}.
]
Therefore the transport matrix is
[
Q_V(k)=\sqrt{k^2+1},I_3.
]

If the backend uses a different spectral parameter (for example (\beta) itself rather than (k)), then the exact symbol changes by reparameterization, but the content does not:
[
\boxed{Q_V \text{ is diagonal and open-FRW hyperbolic, not a fixed family scalar.}}
]

### Type VII(_0)

The helical family requires the **v5 §03A Type VII(_0) helical-basis card** to be completely explicit. What is fixed already is:

1. the real basis is ((\mu_{\rm hel},\mu_{\rm hel+},\mu_{\rm hel-}));
2. the (+) and (-) partners are degenerate in norm in the real cosine/sine basis;
3. therefore
   [
   Q_{VII_0} = \operatorname{diag}(q_0,\ q_h,\ q_h)
   ]
   in the real frozen storage basis.

What is **not** fixed from the excerpt alone is the exact map
[
q_h = q_h(k,\text{helical basis card}).
]
So the exact (q_h) requires the helical-basis card; it cannot be guessed honestly.

### Type VIII

For the principal-series branch, the frozen Plancherel density is
[
\rho^{\rm cont}_{VIII}(\mu,s)
=============================

\frac{1}{(2\pi)^2}
\frac{s\sinh(2\pi s)}{\cosh(2\pi s)+\cos(2\pi\mu)}.
]
The standard (SL(2,\mathbb R)) principal-series Casimir is
[
\lambda = \frac14 + s^2,
]
so the transport wavenumber is
[
q_{VIII}(s)=\sqrt{s^2+\frac14}.
]

Hence, on the parity-restricted (\mu=0) real branch,
[
Q_{VIII}(s)=\sqrt{s^2+\frac14},I_3,
]
and as (s\to\infty),
[
q_{VIII}(s)=s+\frac{1}{8s}+O(s^{-3}).
]

This is the correct (O(1)) asymptotic transport scale, not a fixed family scalar like `1.20`.

### Summary

The replacement is

[
\boxed{
Q_\mu =
\begin{cases}
|k|,I_3, & \text{Type II},[4pt]
I_3, & \text{Type III (with }e^{-r}\text{ in the measure, not the operator)},[4pt]
\sqrt{k^2+1},I_3, & \text{Type V},[4pt]
\operatorname{diag}(q_0,q_h,q_h), & \text{Type VII}_0\ \text{(exact }q_h\text{ needs the helical card)},[4pt]
\sqrt{s^2+\tfrac14},I_3, & \text{Type VIII principal series}.
\end{cases}
}
]

---

## Q-8.4 — twist_mix_scale as Wigner-3j projector

The twist-mixing placeholder
[
\texttt{twist_scale}=
\texttt{branch_scale},\frac{|a|}{1+|a|+|h|}
]
is not a first-principles coefficient. In the covariant kinetic hierarchy, the twist vector (a^\alpha) enters linearly as a rank-1 geometric insertion. So the raw coefficient is (|a|) itself; the saturation (1/(1+|a|+|h|)) is purely numerical and must be removed. This is exactly the kind of rank-1 tetrad coupling described in the (1+3) covariant/tetrad formalism and the covariant CMB hierarchy. ([ResearchGate][1])

### (a) Raw coefficient

[
\boxed{
\text{raw twist coefficient} = |a|
}
]

not
[
\frac{|a|}{1+|a|+|h|}.
]

### (b) Class A vs class B

If (a=0) (all class-A families), then
[
\boxed{\text{every }E\leftrightarrow B\text{ twist-induced entry vanishes identically.}}
]

If (|a|>0) (class B), the coupling is parity odd. In a circular/helicity basis the two helicity eigenblocks carry opposite signs:
[
+\tau_{\ell m}\quad\text{and}\quad -\tau_{\ell m}.
]
In the real ((E,B)) basis this becomes an antisymmetric (2\times2) block.

### (c) Wigner (3j) form

For a rank-1 insertion acting on a spin-2 tensor tower, the matrix element is

[
\left[T_a^{(2)}\right]_{\ell m,\ell' m'}
========================================

|a|
\sum_{q=-1}^{1} a_q,
(-1)^m
\sqrt{(2\ell+1)(2\ell'+1)}
\begin{pmatrix}
\ell & 1 & \ell'\
-m & q & m'
\end{pmatrix}
\begin{pmatrix}
\ell & 1 & \ell'\
-2 & 0 & 2
\end{pmatrix},
]

with
[
\ell'=\ell\pm1,\qquad m'=m+q.
]

In the canonical axis (a^\alpha=|a|,\delta^\alpha_1), only the (q=\pm1) spherical components contribute, so the allowed transitions are
[
(\ell,m)\to(\ell\pm1,m\pm1).
]

That is the minimal physically correct tower connectivity.

### (d) Type III and Type V

Both have (|a|=1), so the raw twist projector is the same:

[
P_a =
\begin{pmatrix}
1&0&0\
0&0&0\
0&0&0
\end{pmatrix}.
]

Thus the family-specific twist kernel is

[
\left[\mathcal T_{\rm twist}\right]_{\mu\mu';\ell m,\ell' m'}
=============================================================

(P_a)*{\mu\mu'},
\left[T_a^{(2)}\right]*{\ell m,\ell' m'}.
]

So for Type V:
[
\mathcal T_{\rm twist}^{(V)} = P_a \otimes T_a^{(2)},
]
and for Type III:
[
\mathcal T_{\rm twist}^{(III)} = P_a \otimes T_a^{(2)}
]
as well; Type III differs from V in the additional (n)-driven semisimple/nilpotent couplings, not in the twist projector itself.

For all class-A families,
[
\mathcal T_{\rm twist}=0.
]

---

## Q-8.5 — local_drag, mass, collision mu-dependence

### (a) `local_drag_scale = 1/R_\mu`

This must be a (\mu)-vector, not a family scalar. The universal definition is

[
R_\mu(\eta)=\frac{4\rho_{\gamma,\mu}}{3\rho_{b,\mu}},
\qquad
\texttt{local_drag_by_mu} = R_\mu^{-1}.
]

For class-A families with homogeneous background and no class-B twist projection, the background is (\mu)-independent:
[
R_\mu = R,\qquad
\texttt{local_drag_by_mu}=R^{-1}(1,1,1)^T.
]

For class-B families (III, V), the (\mu)-dependence first appears at (O(|a|^2)), because the linear (a)-projection changes sign between partner modes and cancels in the real basis. So the generic expansion is

[
R_\mu^{-1}
==========

R^{-1}
\Bigl[
1+\zeta_R,|a|^2,(\hat a\cdot e_\mu)^2 + O(|a|^4)
\Bigr].
]

With (a=(1,0,0)), this becomes

[
R_\mu^{-1}
==========

R^{-1}
\begin{pmatrix}
1+\zeta_R |a|^2\
1\
1
\end{pmatrix}
+O(|a|^4).
]

For Type III and Type V, (|a|=1), so

[
\texttt{local_drag_by_mu}^{(III)}
=================================

# \texttt{local_drag_by_mu}^{(V)}

R^{-1}
\begin{pmatrix}
1+\zeta_R\
1\
1
\end{pmatrix}
+O(a^4).
]

The coefficient (\zeta_R) **cannot** be fixed from the operator excerpt alone; it depends on the v5 background tilt closure (how (\rho_{\gamma,\mu}) and (\rho_{b,\mu}) are projected onto the (\mu)-basis).

### (b) `mass_scale`

The local baryon momentum equation in anisotropic expansion picks up the isotropic Hubble drag plus anisotropic shear corrections. Therefore

[
\texttt{mass_by_mu}
===================

3H,\mathbf 1_\mu + \delta M_\mu.
]

For Type I,
[
\delta M_\mu = 0,
\qquad
\boxed{\langle \texttt{mass_by_mu}\rangle = 3H.}
]

For Type II with
[
n=\operatorname{diag}(1,0,0),
]
the minimal nilpotent correction is the (n)-projected shear trace:

[
\delta M^{(II)}
===============

\zeta_M
\begin{pmatrix}
\sigma_{11}\
0\
0
\end{pmatrix},
\qquad
\sum_\mu \delta M_\mu
=====================

# \zeta_M,\operatorname{Tr}(\sigma n)

\zeta_M,\sigma_{11}.
]

So the requested anisotropic correction is exactly the (\operatorname{Tr}(\sigma\cdot n)) projection in canonical gauge.

### (c) `collision_scale`

This one is simplest. The (\ell\ge2) Thomson rate is just (\dot\kappa), independent of the Bianchi family once the background electron density has been computed.

So:

[
\boxed{\texttt{collision_scale}=1}
]

for all five representative families, and the current 1.03–1.05 deviations have no physical basis.

---

## Q-8.6 — minimal patch recipe and FLRW-limit verification

### (a) Shapes

The replacement pack should be:

* `transport`: shape `(mu_count, mu_count)`
  real matrix in (\mu)-space; for the five representative families it is diagonal in the frozen real basis.

* `mu_mode_coupling_t`, `mu_mode_coupling_e`, `mu_mode_coupling_b`, `mu_mode_coupling_nu`: shape `(mu_count, mu_count)`
  real matrices in (\mu)-space.

* `twist_mix_kernel`: shape `(ell_max+1, 2*ell_max+1, 2, 2)`
  convention: indices are `(ell, m_offset, delta_ell_index, delta_m_index)` with
  `delta_ell_index = 0,1 ↔ Δℓ = -1,+1`,
  `delta_m_index = 0,1 ↔ Δm = -1,+1`,
  and the actual (E/B) action is by multiplication with the fixed antisymmetric (J_{EB}=\begin{pmatrix}0&1\-1&0\end{pmatrix})`.

* `local_drag_by_mu`, `mass_by_mu`: shape `(mu_count,)`

* `collision`: scalar `1.0`

This keeps everything real-valued in the storage basis, satisfying the user's real-basis constraint.

### (b) Explicit (3\times 3) matrices for the five families

Using the canonical real basis and factoring all ((\ell,m))-dependent Wigner/PSTF coefficients out of the (\mu)-matrices, define

[
P_a =
\begin{pmatrix}
1&0&0\
0&0&0\
0&0&0
\end{pmatrix},
]

[
N_{II}=
\begin{pmatrix}
1&0&0\
0&0&0\
0&0&0
\end{pmatrix},
\quad
N_{III}=
\begin{pmatrix}
0&0&0\
0&1&0\
0&0&-1
\end{pmatrix},
]

[
N_{V}=0,
\quad
N_{VII_0}=
\begin{pmatrix}
0&0&0\
0&1&0\
0&0&1
\end{pmatrix},
\quad
N_{VIII}=
\begin{pmatrix}
-1&0&0\
0&1&0\
0&0&1
\end{pmatrix}.
]

Then the minimal (\mu)-coupling matrix for the intensity channel is

[
\mu_mode_coupling_t^{(F)}
=========================

\alpha_t,N_F + \beta_t,|a_F|,P_a,
]
with the obvious specializations:

[
\mu_mode_coupling_t^{(II)}
==========================

\alpha_t
\begin{pmatrix}
1&0&0\
0&0&0\
0&0&0
\end{pmatrix},
]

[
\mu_mode_coupling_t^{(III)}
===========================

\alpha_t
\begin{pmatrix}
0&0&0\
0&1&0\
0&0&-1
\end{pmatrix}
+
\beta_t
\begin{pmatrix}
1&0&0\
0&0&0\
0&0&0
\end{pmatrix},
]

[
\mu_mode_coupling_t^{(V)}
=========================

\beta_t
\begin{pmatrix}
1&0&0\
0&0&0\
0&0&0
\end{pmatrix},
]

[
\mu_mode_coupling_t^{(VII_0)}
=============================

\alpha_t
\begin{pmatrix}
0&0&0\
0&1&0\
0&0&1
\end{pmatrix},
]

[
\mu_mode_coupling_t^{(VIII)}
============================

\alpha_t
\begin{pmatrix}
-1&0&0\
0&1&0\
0&0&1
\end{pmatrix}.
]

The corresponding (E,B,\nu) matrices are identical up to the fixed channel-normalization similarity transform already encoded in the row scales or storage conventions:
[
\mu_mode_coupling_{e,b,\nu}
===========================

S_{e,b,\nu},
\mu_mode_coupling_t,
S_{e,b,\nu}^{-1}.
]
If the v5 storage basis uses the same real normalization in all sectors, then simply
[
\mu_mode_coupling_e
===================

# \mu_mode_coupling_b

# \mu_mode_coupling_\nu

\mu_mode_coupling_t.
]

For Type I, (N_I=0) and (a_I=0), so every proposed matrix is exactly zero, preserving the FLRW anchor as required.

### (c) Patch diff

A minimal patch recipe is:

```diff id="16qkdu"
@@
- def _family_conditioned_kernel_law(bg, backend):
-     ...
-     return dict(
-         transport_scale = ...,
-         mix_scale = ...,
-         twist_mix_scale = ...,
-         polarization_scale = ...,
-         source_scale = ...,
-         mass_scale = ...,
-         local_drag_scale = ...,
-         cross_mode_scale = ...,
-         collision_scale = ...,
-         mode_plus_scale = ...,
-         mode_minus_scale = ...,
-     )
+ @dataclass(frozen=True)
+ class FamilyKernelPack:
+     transport: np.ndarray                  # (mu_count, mu_count)
+     mu_mode_coupling_t: np.ndarray        # (mu_count, mu_count)
+     mu_mode_coupling_e: np.ndarray        # (mu_count, mu_count)
+     mu_mode_coupling_b: np.ndarray        # (mu_count, mu_count)
+     mu_mode_coupling_nu: np.ndarray       # (mu_count, mu_count)
+     twist_mix_kernel: np.ndarray          # (ell_max+1, 2*ell_max+1, 2, 2)
+     local_drag_by_mu: np.ndarray          # (mu_count,)
+     mass_by_mu: np.ndarray                # (mu_count,)
+     collision: float                      # scalar, fixed = 1.0
+
+ def _family_conditioned_kernel_operator(backend, ell_max):
+     algebra = backend.family_spec.algebra
+     family  = backend.family_spec.family
+     mu_count = len(backend.mode_labels)
+
+     n = np.asarray(algebra.n, dtype=float)
+     a = np.asarray(algebra.a, dtype=float)
+     a_norm = float(np.linalg.norm(a))
+
+     # canonical real-basis projectors in frozen mode-label basis
+     P_a = np.zeros((mu_count, mu_count), dtype=float)
+     if a_norm > 0.0:
+         P_a[0,0] = 1.0
+
+     if family == "II":
+         N = np.diag([1.0, 0.0, 0.0])
+     elif family == "III":
+         N = np.diag([0.0, 1.0, -1.0])
+     elif family == "V":
+         N = np.zeros((mu_count, mu_count), dtype=float)
+     elif family == "VII_0":
+         N = np.diag([0.0, 1.0, 1.0])
+     elif family == "VIII":
+         N = np.diag([-1.0, 1.0, 1.0])
+     else:
+         N = np.zeros((mu_count, mu_count), dtype=float)
+
+     transport = _backend_transport_matrix(backend)     # diagonal q_mu matrix
+     C_mu = N + a_norm * P_a
+
+     return FamilyKernelPack(
+         transport = transport,
+         mu_mode_coupling_t  = C_mu.copy(),
+         mu_mode_coupling_e  = C_mu.copy(),
+         mu_mode_coupling_b  = C_mu.copy(),
+         mu_mode_coupling_nu = C_mu.copy(),
+         twist_mix_kernel    = _build_twist_mix_kernel(algebra.a, ell_max),
+         local_drag_by_mu    = _build_local_drag_by_mu(backend),
+         mass_by_mu          = _build_mass_by_mu(backend),
+         collision           = 1.0,
+     )
```

Then the assembly path must stop multiplying by scalar family laws and instead apply the (\mu)-matrices explicitly. Schematically:

```diff id="9x0qax"
@@
- scales = _operator_scales(bg, backend, geometry)
+ kernel = _family_conditioned_kernel_operator(backend, ell_max)

@@ assemble_free_streaming_block
- coeff *= scales["transport_scale"] * scales["cross_mode_scale"]
+ # for each (mu_i, mu_j), apply the family transport/cross-mode matrix
+ coeff_matrix = kernel.transport @ kernel.mu_mode_coupling_t

@@ assemble_mixing_block
- coeff *= scales["twist_scale"] * scales["mode_plus_scale"] * scales["mode_minus_scale"]
+ coeff_matrix = kernel.twist_mix_kernel[ell, m_offset, ...]   # E/B block only

@@ assemble_explicit_block
- local_drag = scales["local_drag_scale"]
- collision  = scales["collision_scale"]
+ local_drag = kernel.local_drag_by_mu[mu_index]
+ collision  = kernel.collision
```

This modifies only (A_{\rm right}), never (b_{hh}). In the Type-I limit (N=0), (a=0), and all (\mu)-mode coupling matrices collapse to zero, so the FLRW invariant manifold and (D_2) anchor remain protected.

### (d) Expected post-patch (\lambda_{\max})

Post-patch, the instantaneous residual-joint operator splits into

[
A_{\rm right}
=============

K_{\rm stream}
+
D_{\rm coll}
+
K_{\rm geom},
]

where

* (K_{\rm stream}) is weighted-skew free streaming,
* (D_{\rm coll}) is symmetric negative-semidefinite Thomson relaxation,
* (K_{\rm geom}) is the exact family-dependent geometric coupling assembled from (n), (a), and the Wigner/PSTF projectors.

Because the geometric Liouville transport is still conservative — it redistributes amplitude among mode labels and tower slots but does not create it — the exact family-dependent transport part is again weighted-skew (or diagonally similar to weighted-skew) once the placeholder scalar laws are removed. The Bianchi-family "growing modes" of the background are statements about the **time dependence of the background coefficients**, not about positive real eigenvalues of the frozen transport/collision operator at a given snapshot. Hawking's classic analysis and the later nearly-isotropic Bianchi linearization literature both separate background mode growth from the conservative transport structure of the radiation hierarchy. ([Astrophysics Data System][5])

Therefore the expected post-patch behavior is:

[
\boxed{
\Re\lambda_{\max}\le 0
\quad\text{at}\quad \gamma_T=0
\quad\text{and}\quad \gamma_T=1
}
]

for all five representative families (II,III,V,VII_0,VIII), provided the family kernels are assembled from the exact (n/a) projections rather than empirical positive scalar laws.

At (\gamma_T=0):

* Type I gives (\Re\lambda_{\max}=0) exactly,
* non-Type-I families still give (\Re\lambda_{\max}\le 0), with the real part expected to vanish if the geometry block is purely weighted-skew in the chosen snapshot basis.

At (\gamma_T=1):

* any strictly negative real parts are from physical Thomson relaxation (dipole drag, quadrupole polarization relaxation, higher-(\ell) damping),
* not from family-conditioned tuning constants.

So the final answer is:

[
\boxed{
\text{Replace the scalar family law by a real }\mu\text{-matrix kernel pack; then the FLRW anchor is preserved, and }
\Re\lambda_{\max}\le 0\text{ is the correct post-patch expectation.}
}
]

[1]: https://www.researchgate.net/publication/1977532_Cosmological_models_Cargese_lectures_1998 "https://www.researchgate.net/publication/1977532_Cosmological_models_Cargese_lectures_1998"
[2]: https://www.sciencedirect.com/science/article/pii/S0003491600960330 "https://www.sciencedirect.com/science/article/pii/S0003491600960330"
[3]: https://academic.oup.com/mnras/article-abstract/380/4/1387/1060314 "https://academic.oup.com/mnras/article-abstract/380/4/1387/1060314"
[4]: https://www.researchgate.net/publication/46586244_Linearization_of_homogeneous_nearly-isotropic_cosmological_models "https://www.researchgate.net/publication/46586244_Linearization_of_homogeneous_nearly-isotropic_cosmological_models"
[5]: https://adsabs.harvard.edu/pdf/1966ApJ...145..544H "https://adsabs.harvard.edu/pdf/1966ApJ...145..544H"
