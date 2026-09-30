# T5 — Exact full-sky local-observer response theorem pack

Date: 2026-09-03  
Repository authority: PR #442 at
`29427a1f7f2c5d46e43ffe03053c4ac13e969228`  
Evidence grade: `DERIVED`, literature-supported, independently Wolfram-checked,
and implementation-verified at the frozen WU-010 scope  
Observational data used: none

## 1. Domain and conventions

Use metric signature `(-,+,+,+)`, a unit timelike observer `u^a`, and

\[
p^a=\frac{\epsilon}{c}(u^a+e^a)
    =\frac{\epsilon}{c}(u^a-n^a),
\qquad n^a=-e^a,
\]

where `n^a` is the outward sky direction. The actively boosted observer is

\[
\widetilde u^a=\gamma(u^a+\beta^a),
\qquad
\gamma=(1-\beta^2)^{-1/2},
\qquad
\beta^a u_a=0.
\]

The observable is strictly positive absolute thermodynamic blackbody
temperature, with Doppler weight `d=1`. Frequency-dependent intensity,
spectral distortions, polarization, foreground conversion, and a global
matter-frame tilt are outside this theorem.

## 2. Exact Lorentz pullback

The boosted photon energy is

\[
\widetilde\epsilon=-c p_a\widetilde u^a
 =\gamma(1+\boldsymbol\beta\cdot\boldsymbol n)\epsilon
 \equiv D\epsilon.
\]

The same Doppler factor can be written in the observed direction as

\[
D=\frac{1}{\gamma(1-\boldsymbol\beta\cdot\widetilde{\boldsymbol n})}.
\]

Lorentz invariance of the photon occupation number and the Planck form imply
that `epsilon/T` is invariant along corresponding rays. Hence

\[
\boxed{
\widetilde T(\widetilde{\boldsymbol n})
 =\frac{T(\boldsymbol n(\widetilde{\boldsymbol n}))}
        {\gamma(1-\boldsymbol\beta\cdot\widetilde{\boldsymbol n})}
 =D\,T(\boldsymbol n).
}
\]

Aberration also gives

\[
\boxed{d\widetilde\Omega=D^{-2}d\Omega.}
\]

These formulas agree with the exact `d=1` CMB boost-operator literature. Dai
and Chluba show that the full-sky `d=1` kernels are matrix elements of a unitary
boost operator; Yasini and Pierpaoli explicitly distinguish other Doppler
weights and frequency-dependent observables; Ferreira and Quartin separate
Doppler modulation, aberration, dipole, masks, and instrumental effects.

## 3. First-order generator

Differentiating the exact pullback at `beta=0` gives

\[
\boxed{
\delta_\beta T
 = (\boldsymbol\beta\cdot\boldsymbol n)T
 -[\boldsymbol\beta
   -(\boldsymbol\beta\cdot\boldsymbol n)\boldsymbol n]
   \cdot\nabla_{S^2}T.
}
\]

The first term is thermodynamic-temperature Doppler modulation; the second is
aberration. The sign follows from the fixed outward direction `n=-e` and the
active observer boost `+beta`.

For a quadrupole

\[
T_Q(\boldsymbol n)=Q_{ab}n^an^b,
\]

the tangential gradient is

\[
\nabla_{S^2}T_Q
 =2[Q\boldsymbol n-T_Q\boldsymbol n].
\]

Therefore

\[
\delta_\beta T_Q
 =3(\boldsymbol\beta\cdot\boldsymbol n)T_Q
  -2(Q\boldsymbol\beta)\cdot\boldsymbol n.
\]

## 4. STF3 response and dipole decomposition

Define

\[
(B_Q\beta)_{abc}=3\beta_{\langle a}Q_{bc\rangle}.
\]

In Cartesian components,

\[
\begin{aligned}
(B_Q\beta)_{abc}
={}&\beta_aQ_{bc}+\beta_bQ_{ca}+\beta_cQ_{ab}\\
&-\frac25\bigl[
 \delta_{ab}(Q\beta)_c+
 \delta_{ac}(Q\beta)_b+
 \delta_{bc}(Q\beta)_a
 \bigr].
\end{aligned}
\]

The tensor is fully symmetric and trace-free. Contracting with `n^a n^b n^c`
gives

\[
(B_Q\beta)_{abc}n^an^bn^c
 =3(\beta\cdot n)T_Q-\frac65(Q\beta)\cdot n.
\]

Thus the exact first-order selection rule is

\[
\boxed{
\delta_\beta T_Q
 =(B_Q\beta)_{abc}n^an^bn^c
 -\frac45(Q\beta)_a n^a.
}
\]

A pure quadrupole produces only `ell=3` and `ell=1` at first order. The two
terms must not be combined into an octupole-only response.

## 5. Adjoint and normal matrix

Use the Euclidean vector inner product and the STF3 Frobenius product. For any
STF3 tensor `O`, trace terms vanish and

\[
O:B_Q\beta
 =3\beta_a O_{abc}Q_{bc}.
\]

Hence

\[
\boxed{(B_Q^*O)_a=3O_{abc}Q_{bc}.}
\]

Let

\[
q_2=Q:Q,
\qquad
M_Q=q_2I+\frac65Q^2.
\]

Direct contraction gives

\[
(B_Q\beta)_{abc}Q_{bc}=(M_Q\beta)_a,
\]

and therefore

\[
\boxed{B_Q^*B_Q=3M_Q},
\qquad
\boxed{\|B_Q\beta\|_F^2=3\beta^TM_Q\beta}.
\]

For every nonzero `Q`, `q_2>0` and `Q^2` is positive semidefinite, so `M_Q` is
positive definite. Consequently `B_Q` is injective and has rank three.

## 6. Algebraic inverse and orthogonal projector

Define the contraction vector

\[
c_a=(O:Q)_a\equiv O_{abc}Q_{bc}.
\]

The least-squares local-boost coordinate in the octupole response image is

\[
\boxed{\widehat\beta=M_Q^{-1}c.}
\]

The STF3 Frobenius-orthogonal projector onto `Im B_Q` is

\[
\boxed{
P_{\operatorname{Im}B_Q}O
 =B_QM_Q^{-1}(O:Q).
}
\]

Indeed,

\[
(P_{\operatorname{Im}B_Q}O):Q
 =M_QM_Q^{-1}(O:Q)=O:Q,
\]

so

\[
O_\perp=O-P_{\operatorname{Im}B_Q}O
\quad\Longrightarrow\quad
\boxed{O_{\perp\,abc}Q_{bc}=0.}
\]

The same identity proves idempotence, while the adjoint formula proves
self-adjointness. Since `dim STF3=7` and `rank B_Q=3`,

\[
\boxed{\dim(\operatorname{Im}B_Q)^\perp=4.}
\]

This four-dimensional residual is response-orthogonal at fixed nonzero `Q`.
It is not automatically intrinsic, cosmological, foreground-free, or
Bianchi-generated.

## 7. Sharp condition-number bound

Let the eigenvalues of nonzero trace-free `Q` be ordered so that the largest
absolute value has the opposite sign from the other two. After scale, sign,
and permutation, write

\[
(\lambda_1,\lambda_2,\lambda_3)=(-1,1-t,t),
\qquad 0\le t\le\frac12.
\]

The eigenvalues of `M_Q` are

\[
\mu_i=q_2+\frac65\lambda_i^2,
\qquad
q_2=2(1-t+t^2).
\]

Thus

\[
\kappa_2(M_Q)
 =\frac{q_2+6/5}{q_2+(6/5)t^2}
 =\frac{8+5(t-1)t}{5+t(-5+8t)}.
\]

Differentiation yields

\[
\frac{d\kappa_2}{dt}
 =\frac{3(t-5)(5t-1)}{(5-5t+8t^2)^2}.
\]

The unique interior maximum occurs at `t=1/5`, while the endpoints give
`8/5` and `3/2`. Therefore

\[
\boxed{\kappa_2(M_Q)\le\frac53.}
\]

Equality holds for spectra proportional to

\[
\boxed{(-5,4,1)}
\]

up to scale, sign, and permutation. The inverse is therefore uniformly
well-conditioned on every nonzero quadrupole; the singularity is only at
`Q=0`, where a quadrupole-induced velocity coordinate is undefined.

## 8. Independent exact validation

A fresh Wolfram calculation verified:

```yaml
STF3_trace_vector: [0,0,0]
BstarB_minus_3M: 0
condition_number_maximum: 5/3
maximum_location: t=1/5
equality_spectrum: proportional_to_[-5,4,1]
generator_decomposition_on_unit_sphere_residual: 0
projector_residual_contraction_with_Q: [0,0,0]
projector_idempotence_contraction_residual: [0,0,0]
projector_self_adjoint_exact_witness_residual: 0
```

For the registered exact STF witness `Q=diag(1,2,-3)`, the independent
projector check obtained

\[
M_Q=\operatorname{diag}(76/5,94/5,124/5),
\qquad
O:Q=(24,38,47),
\]

and the projected residual contracted with `Q` vanished exactly.

The machine-readable receipt is
`T5_WOLFRAM_AND_EXECUTION_RECEIPT.json`.

## 9. Repository execution evidence

The WU-010 implementation candidate and independent audit report exact-head
success for:

```text
PR07 audit-repair gates       run 33529400104  SUCCESS
PR04 theory/integration       run 33529400157  SUCCESS
Repository integrity          run 33529400115  SUCCESS
```

The accepted scope is the exact full-sky local-observer temperature response.
No Planck absolute-temperature product, empirical velocity fit, processed
cut-sky operator, global tilt, polarization result, or Bianchi attribution was
admitted.

## 10. Literature matrix

- Liang Dai and Jens Chluba, *New operator approach to the CMB aberration
  kernels in harmonic space*, Phys. Rev. D 89, 123504 (2014), DOI
  `10.1103/PhysRevD.89.123504`: exact nonlinear full-sky boost operator and
  `d=1` kernel structure.
- Siavash Yasini and Elena Pierpaoli, *Generalized Doppler and aberration
  kernel for frequency-dependent cosmological observables*, Phys. Rev. D 96,
  103502 (2017), DOI `10.1103/PhysRevD.96.103502`: observable-dependent
  Doppler weight, frequency dependence, masks, and polarization boundaries.
- Pedro da Silveira Ferreira and Miguel Quartin, *Disentangling Doppler
  modulation, aberration and the temperature dipole in the CMB*, Phys. Rev. D
  104, 063503 (2021), DOI `10.1103/PhysRevD.104.063503`: realistic separation
  of modulation, aberration, intrinsic dipole, beaming, noise, and masks.

The repository-specific STF inverse and sharp `5/3` condition bound are
reported as derived results rather than attributed to those papers.

## 11. T5 terminal

```text
PASS_WU010_EXACT_LOCAL_OBSERVER_RESPONSE_SYNTHESIS
```

This terminal closes the scoped full-sky theory and its implementation
readback. It does not authorize empirical `beta`, boost subtraction,
local-boost/global-tilt equivalence, processed cut-sky identification, or
observational execution.
