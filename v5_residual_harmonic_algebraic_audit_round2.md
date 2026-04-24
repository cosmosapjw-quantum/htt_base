## Q-5.1 — local ↔ harmonic Thomson coupling coefficients and signs

Let the baryon dipole variable be (v_b) and the photon dipole variable be (\Theta_1), with (\dot\kappa = a n_e \sigma_T > 0) and the user’s convention
[
R \equiv \frac{4\rho_\gamma}{3\rho_b}.
]
Then the Thomson-only dipole sector is
[
\dot v_b = \frac{\dot\kappa}{R},(3\Theta_1-v_b),
\qquad
\dot\Theta_1 = -\dot\kappa\left(\Theta_1-\frac{v_b}{3}\right).
]
So the exact (2\times 2) collision block in the ((v_b,\Theta_1)) basis is
[
A_{b\gamma}
===========

\dot\kappa
\begin{pmatrix}
-\dfrac1R & \dfrac{3}{R}[4pt]
\dfrac13 & -1
\end{pmatrix}.
]
This is the Ma–Bertschinger dipole-drag structure, modulo whatever positive row scalings the code inserts. ([OSTI.gov][1])

### (a) `local <- harmonic(theta_1)` coefficient

The code uses
[
A[v_b,\Theta_1]_{\rm code}
==========================

+\frac{0.25,\gamma_T,\texttt{local_drag_scale}}{\lvert \texttt{baryon_base_diag}[1]\rvert}.
]

If `local_drag_scale` is intended to represent (1/R), the code coefficient is
[
A[v_b,\Theta_1]_{\rm code}
==========================

+\frac{0.25}{\lvert \texttt{baryon_base_diag}[1]\rvert},\frac{\gamma_T}{R}.
]

The physical coefficient is
[
A[v_b,\Theta_1]_{\rm phys}=+\frac{3\gamma_T}{R}.
]

Hence the ratio is
[
\frac{A_{\rm code}}{A_{\rm phys}}
=================================

\frac{0.25}{3,\lvert \texttt{baryon_base_diag}[1]\rvert}.
]

In the FLRW-like branch of the code,
[
\texttt{baryon_base_diag}[1]
============================

1+0.08,\texttt{geom_scale}+0.03.
]
At the fiducial FLRW placeholder (\texttt{geom_scale}\simeq 1), this is
[
\texttt{baryon_base_diag}[1]\simeq 1.11,
]
so
[
\frac{A_{\rm code}}{A_{\rm phys}}
\simeq
\frac{0.25}{3\times 1.11}
\approx 0.075.
]

So the code underestimates the baryon response by a factor
[
\approx 13.3.
]

Now, using the user’s stated regime (R\in[0.6,3]), the physical coefficient range is
[
\frac{3}{R}\in [1,5].
]
The code’s hard constant (0.25) is not remotely consistent with that range. Even before the extra division by (\lvert \texttt{baryon_base_diag}[1]\rvert), it is too small by a factor between (4) and (20). With the denominator included, it is worse.

So the answer is:

[
\boxed{\text{The }0.25\text{ coefficient is not consistent with }3/R.}
]

### (b) `harmonic <- local(baryon velocity)` coefficient

The code uses
[
A[\Theta_1,v_b]_{\rm code}
==========================

-\texttt{inv_t_dipole},\bigl(0.25,\texttt{local_drag_scale},\gamma_T\bigr).
]

The physical coefficient is
[
A[\Theta_1,v_b]_{\rm phys}
==========================

+\texttt{inv_t_dipole},\frac{\gamma_T}{3},
]
because the photon row is row-scaled but the Thomson coefficient itself is still (+\dot\kappa/3).

So there are **three** problems:

1. **Sign**: code negative, physics positive.
   This is a genuine sign error.

2. **Magnitude**: (0.25) versus (1/3).
   Even ignoring everything else, the ratio
   [
   \frac{0.25}{1/3}=\frac34
   ]
   is a (25%) error. In a relaxation block, that is material, not negligible.

3. **Wrong (R)-dependence**: the code multiplies by `local_drag_scale`.
   If `local_drag_scale=1/R`, then the code is using
   [
   -\frac{0.25}{R}\gamma_T
   ]
   where the physics requires
   [
   +\frac{1}{3}\gamma_T.
   ]
   So the harmonic-row coupling should **not** carry the baryon-loading factor (1/R).

Therefore:

[
\boxed{
A[\Theta_1,v_b]_{\rm code}\text{ has the wrong sign, the wrong magnitude, and the wrong }R\text{-dependence.}
}
]

### (c) Corrected (2\times 2) block and eigenvalues

Let
[
\alpha \equiv \frac{\gamma_T}{\lvert \texttt{baryon_base_diag}[1]\rvert},
\qquad
\beta \equiv \gamma_T,\texttt{inv_t_dipole},
\qquad
\texttt{local_drag_scale}\equiv \frac{1}{R}
]
if that identification is intended.

Then the corrected code-basis block is
[
A_{b\gamma}^{\rm corr}
======================

\begin{pmatrix}
-\alpha/R & +3\alpha/R[4pt]
+\beta/3 & -\beta
\end{pmatrix}.
]

Its trace is
[
\operatorname{tr} A_{b\gamma}^{\rm corr}
========================================

-\left(\frac{\alpha}{R}+\beta\right)<0.
]

Its determinant is
[
\det A_{b\gamma}^{\rm corr}
===========================

# \left(-\frac{\alpha}{R}\right)(-\beta)-\left(\frac{3\alpha}{R}\right)\left(\frac{\beta}{3}\right)

# \frac{\alpha\beta}{R}-\frac{\alpha\beta}{R}

0.

]

So the eigenvalues are
[
\lambda_1 = 0,
\qquad
\lambda_2 = -\left(\frac{\alpha}{R}+\beta\right)\le 0.
]

Thus
[
\boxed{\Re\lambda \le 0\ \text{for both eigenvalues, with one exact relaxation zero-mode and one strictly negative mode.}}
]

The zero mode is the momentum-sharing direction (v_b=3\Theta_1).

### (d) Minimal patch for defect ❺

The safe algebraic patch is:

```diff
@@
-        local_theta_coeff = float(
-            0.25 * local_drag_scale * gamma_t / max(abs(float(baryon_base_diag[1])), 1.0e-30)
-        )
+        # local_drag_scale MUST encode 1/R = 3 rho_b / (4 rho_gamma).
+        # If v5 §03A defines otherwise, introduce inv_R explicitly.
+        local_theta_coeff = float(
+            3.0 * local_drag_scale * gamma_t / max(abs(float(baryon_base_diag[1])), 1.0e-30)
+        )

@@
-        harmonic_baryon_coeff = float(inv_t_dipole * (-0.25 * local_drag_scale * gamma_t))
+        # Photon dipole receives +kappa_dot/3 * v_b, independent of R.
+        harmonic_baryon_coeff = float(inv_t_dipole * (+gamma_t / 3.0))
```

This patch changes only (A), not (b). Since the FLRW invariant manifold satisfies (r_h(\eta_0)=0) and (b_{hh}(\eta)\equiv 0), the FLRW (D_2) regression anchor remains algebraically protected under any (A)-only patch. The previous runtime-track note already established that the instability is entirely in the residual-harmonic block while the (D_2) anchor remains bit-identical. 

A final note: the identification
[
\texttt{local_drag_scale}=1/R
]
is **not derivable from the excerpt alone**. It is the only identification that makes the baryon row physically meaningful, but this must be frozen explicitly in the v5 §03A spec.

---

## Q-5.2 — full 3×3 / 4×4 block stability with corrected coupling

The corrected Thomson dipole block is dissipative. The remaining question is whether the surrounding free-streaming couplings to (\Theta_0) and (\Theta_2) can turn that into growth.

They cannot.

### Step 1: rescale the dipole

Define
[
X \equiv 3\Theta_1.
]

Then the Thomson subsystem becomes
[
\dot v_b = \frac{\dot\kappa}{R}(X-v_b),
\qquad
\dot X = -\dot\kappa (X-v_b).
]

So in the ((v_b,X)) basis the collision block is
[
M_{bX}
======

-\dot\kappa
\begin{pmatrix}
1/R & -1/R\
-1 & 1
\end{pmatrix}.
]

### Step 2: show dissipativity

Take the positive diagonal weight
[
H_{bX}=\operatorname{diag}(1,\ 1/R).
]

Then
[
H_{bX}M_{bX}+M_{bX}^T H_{bX}
============================

-2\dot\kappa
\begin{pmatrix}
1/R & -1/R\
-1/R & 1/R
\end{pmatrix}
\le 0.
]

Equivalently, the quadratic form
[
\mathcal E_{bX}=\frac12\left(v_b^2+\frac{X^2}{R}\right)
]
obeys
[
\frac{d\mathcal E_{bX}}{d\eta}
==============================

-\frac{\dot\kappa}{R}(X-v_b)^2 \le 0.
]

So the (v_b)-(X) Thomson coupling is a pure relaxation operator.

### Step 3: add (\Theta_0,\Theta_2)

The surrounding photon free-streaming couplings are
[
\dot\Theta_1 \supset k\left(\frac13\Theta_0-\frac23\Theta_2\right),
]
or equivalently
[
\dot X \supset k(\Theta_0-2\Theta_2).
]

These are exactly part of the Liouville/free-streaming operator. By the Round-1 result, the harmonic streaming block is weighted-skew-adjoint:
[
W_h A_h + A_h^T W_h = 0.
]

Therefore, after the dipole rescaling (X=3\Theta_1), there still exists a positive diagonal weight (\widetilde W_h) on the photon block such that the full streaming operator is skew-adjoint in that weight. (Diagonal similarity preserves weighted skew-adjointness.)

Hence the enlarged ((\Theta_0,X,\Theta_2,v_b)) block decomposes as
[
A_{\rm full} = K_{\rm stream} + D_{\rm Thomson},
]
with
[
\widetilde H K_{\rm stream} + K_{\rm stream}^T \widetilde H = 0,
\qquad
\widetilde H D_{\rm Thomson} + D_{\rm Thomson}^T \widetilde H \le 0
]
for a suitable positive diagonal weight (\widetilde H).

Then for any eigenpair (A_{\rm full} z = \lambda z),
[
2\Re\lambda, z^\dagger \widetilde H z
=====================================

z^\dagger\left(\widetilde H A_{\rm full}+A_{\rm full}^T \widetilde H\right) z
\le 0.
]

Therefore
[
\boxed{\Re\lambda_{\max}\le 0.}
]

So the corrected ((\Theta_0,\Theta_1,\Theta_2,v_b)) enlargement cannot generate a positive eigenvalue. The streaming couplings to (\Theta_0) and (\Theta_2) only add imaginary/oscillatory structure; they do not create growth. This is exactly the expected behavior of the FLRW Liouville operator plus Thomson relaxation. ([OSTI.gov][1])

The trace check is consistent with this:

* streaming contributes zero trace,
* Thomson contributes only negative diagonal terms,
  so
  [
  \operatorname{tr}A_{\rm full}<0
  ]
  whenever (\dot\kappa>0).

---

## Q-6.1 — correct T↔E mix_t / mix_e form (γ_T-proportional)

The reference polarization hierarchy is

[
\dot\Theta_\ell
===============

## k c^-*\ell \Theta*{\ell-1}

## k c^+*\ell \Theta*{\ell+1}

\dot\kappa,\Theta_\ell
+
\dot\kappa,\Pi,\delta_{\ell 2}/10,
]

[
\dot E_\ell
===========

## k c^-*\ell E*{\ell-1}

## k c^+*\ell E*{\ell+1}

## \dot\kappa,E_\ell

\dot\kappa,\sqrt6,\Pi,\delta_{\ell 2}/10,
]

[
\dot B_\ell
===========

## k c^-*\ell B*{\ell-1}

## k c^+*\ell B*{\ell+1}

\dot\kappa,B_\ell,
]

with
[
\Pi = \Theta_2 - \sqrt6,E_2.
]

Substitute (\Pi) into the (\ell=2) rows:

[
\dot\Theta_2
============

\cdots
-\dot\kappa \Theta_2
+
\frac{\dot\kappa}{10}\left(\Theta_2-\sqrt6 E_2\right)
=====================================================

\cdots
-\frac{9}{10}\dot\kappa,\Theta_2
-\frac{\sqrt6}{10}\dot\kappa,E_2,
]

[
\dot E_2
========

\cdots
-\dot\kappa E_2
---------------

# \frac{\sqrt6\dot\kappa}{10}\left(\Theta_2-\sqrt6 E_2\right)

\cdots
-\frac{\sqrt6}{10}\dot\kappa,\Theta_2
-\frac{2}{5}\dot\kappa,E_2.
]

So the **only** Thomson-induced (T\leftrightarrow E) mixing is the quadrupole block, and it is proportional to (\dot\kappa) at all times. In particular:

[
\boxed{
A[T_\ell,E_{\ell'}]_{\rm Thomson}
=================================

# A[E_\ell,T_{\ell'}]_{\rm Thomson}

0
\quad\text{unless}\quad
\ell=\ell'=2.
}
]

Thus the code’s
[
\texttt{mix_scale} = \texttt{branch_scale}\cdot (0.08+0.04\min(\texttt{geom_scale},3))
]
cannot be physical, because it survives at (\gamma_T=0). That is incompatible with Thomson scattering. The T/E quadrupole source comes entirely from Thomson polarization physics, as standard polarization treatments make clear. ([APS Journals][2])

### Correct code-basis form

Let (\gamma_T) denote the code’s (\dot\kappa), and let (w^{\rm PSTF}_{\ell m}) be the storage normalization factor for the slot. Then the general code-basis form is

[
\texttt{mix_t}_{\ell m}
=======================

*

\texttt{inv_t}*{\ell m},
\gamma_T,
\frac{\sqrt6}{10},
\mathcal N^{(TE)}*{\ell m},
]

[
\texttt{mix_e}_{\ell m}
=======================

*

\texttt{inv_e}*{\ell m},
\gamma_T,
\frac{\sqrt6}{10},
\mathcal N^{(ET)}*{\ell m},
]

where
[
\mathcal N^{(TE)}*{\ell m},\ \mathcal N^{(ET)}*{\ell m}
\propto \delta_{\ell 2}
]
and differ only by the slot-normalization convention.

If `structure.pstf_weight_by_slot` is exactly the map from the canonical ((\Theta_2,E_2)) normalization to the stored slot normalization, then one may take
[
\mathcal N^{(TE)}_{\ell m}
==========================

# \mathcal N^{(ET)}_{\ell m}

\delta_{\ell 2},\texttt{pstf_weight_by_slot}_{\ell m}.
]

If that interpretation of `pstf_weight_by_slot` is **not** frozen in v5 §03A/§03B, then the precise numerical slot factor cannot be fixed from the excerpt alone. But two facts are algebraically fixed:

1. the coupling is **quadrupole-only**;
2. it is **proportional to (\gamma_T)** and hence
   [
   \boxed{\gamma_T\to 0\quad\Rightarrow\quad \texttt{mix_t},\texttt{mix_e}\to 0.}
   ]

A further necessary correction follows immediately from the same algebra:

[
\texttt{diag_t}(\ell=2) = -\texttt{inv_t},\frac{9\gamma_T}{10},
\qquad
\texttt{diag_e}(\ell=2) = -\texttt{inv_e},\frac{2\gamma_T}{5},
]
not the generic (-\texttt{inv_X}\gamma_T) form. So **fixing only the off-diagonal mix terms is incomplete**; the (\ell=2) diagonals must also be specialized to the Thomson-derived values.

---

## Q-6.2 — sign structure of T↔E coupling

In the canonical ((\Theta_2,E_2)) basis, the collision block is

[
A_{TE}^{(\ell=2)}
=================

-\dot\kappa
\begin{pmatrix}
9/10 & \sqrt6/10[4pt]
\sqrt6/10 & 2/5
\end{pmatrix}.
]

Therefore:

* (A[T_2,E_2]) and (A[E_2,T_2]) have the **same sign**;
* specifically, in this convention they are both **negative**.

This is not a problem. Thomson scattering is **dissipative**, not conservative. So the (T/E) quadrupole block is not skew-adjoint; it is a (weighted) **symmetric negative-definite** collision block.

Indeed, the matrix
[
M =
\begin{pmatrix}
9/10 & \sqrt6/10[4pt]
\sqrt6/10 & 2/5
\end{pmatrix}
]
has
[
\operatorname{tr} M = \frac{13}{10} >0,
\qquad
\det M = \frac{9}{10}\cdot\frac25 - \left(\frac{\sqrt6}{10}\right)^2
= \frac{36}{100}-\frac{6}{100}
= \frac{3}{10}>0.
]
So (M) is positive definite, and therefore
[
-\dot\kappa,M
]
has both eigenvalues strictly negative for (\dot\kappa>0).

Thus the correct answer is:

[
\boxed{
A[T_2,E_2]\text{ and }A[E_2,T_2]\text{ carry the same sign, and the collision block is dissipative, not skew.}
}
]

After row scaling, the raw stored matrix need not be literally symmetric, but it must remain diagonally similar (or weighted equivalent) to a symmetric negative-definite quadrupole collision matrix.

---

## Q-6.3 — eb_*  (E↔B, T↔B) and twist_scale in FLRW limit

In isotropic FLRW Thomson scattering:

* there is **no primary (B)-mode source**,
* there is **no (T\leftrightarrow B)** collision coupling,
* there is **no (E\leftrightarrow B)** collision coupling.

That is the whole point of the (E/B) decomposition: for parity-even scalar Thomson scattering, (B) is not sourced. This is a standard result of the polarization formalism. ([APS Journals][2])

Therefore in the FLRW limit:

[
\boxed{
eb_e = eb_b = eb_{bt} = 0.
}
]

Now, could these couplings represent a **different** physical effect? Yes, but only if they are **geometric transport** couplings, not Thomson collision couplings.

* In anisotropic/twisted backgrounds, basis transport and parity mixing can generate (E/B) conversion through the Liouville/transport operator.
* But then those terms belong in the **transport block**, not in the Thomson collision block.

So the correct interpretation is:

* as **collision** terms, `eb_e`, `eb_b`, `eb_bt` must vanish at (\gamma_T=0) and in fact vanish identically in FLRW;
* if they are intended to represent Bianchi/twist-driven basis rotation, they must be rederived in the transport operator under the v5 geometry spec.

Finally, on `twist_scale`:

* for Bianchi I / FLRW, the structure-constant (a)-vector vanishes,
* so any twist-derived scale must satisfy
  [
  \boxed{\texttt{twist_scale}=0\quad\text{in FLRW/Bianchi I}.}
  ]

That part is structurally correct.

---

## Q-6.4 — minimal patch for ❻

The minimal physically consistent patch is:

1. remove the hand-tuned `mix_scale` from the physical operator,
2. insert only the **quadrupole** Thomson (T\leftrightarrow E) couplings,
3. zero all (B)-couplings in this collision block,
4. correct the (\ell=2) diagonal entries at the same time.

```diff
@@
-    mix_t = inv_t * mix_scale * structure.pstf_weight_by_slot
-    mix_e = inv_e * (0.5 * mix_scale * structure.pstf_weight_by_slot)
+    # Thomson-derived T<->E coupling exists only on the quadrupole.
+    quad_mask = (ell_by_slot == 2)
+    te_weight = np.zeros_like(structure.pstf_weight_by_slot)
+    te_weight[quad_mask] = structure.pstf_weight_by_slot[quad_mask]
+
+    mix_t = -inv_t * gamma_t * (np.sqrt(6.0) / 10.0) * te_weight
+    mix_e = -inv_e * gamma_t * (np.sqrt(6.0) / 10.0) * te_weight

@@
-    eb_base   = twist_scale * structure.eb_base_by_slot
-    eb_e      = inv_e * 0.75 * eb_base
-    eb_b      = inv_b * (-1.0) * eb_base
-    eb_bt     = inv_b * 0.25 * eb_base
+    # No Thomson E<->B or T<->B coupling in FLRW.
+    # Any geometric/twist-driven B-mixing belongs in the transport block,
+    # not in the collision block.
+    eb_e  = np.zeros_like(inv_e)
+    eb_b  = np.zeros_like(inv_b)
+    eb_bt = np.zeros_like(inv_b)

@@
+    # Quadrupole Thomson diagonals from Pi = Theta_2 - sqrt(6) E_2
+    diag_t[quad_mask] = -inv_t[quad_mask] * (9.0 * gamma_t / 10.0)
+    diag_e[quad_mask] = -inv_e[quad_mask] * (2.0 * gamma_t / 5.0)
+    diag_b[quad_mask] = -inv_b[quad_mask] * gamma_t

@@
-    ge2_slots = slots[structure.ge2_mask]
-    self_block[t_off + ge2_slots, e_off + ge2_slots] += mix_t[ge2_mask]
-    self_block[e_off + ge2_slots, t_off + ge2_slots] += mix_e[ge2_mask]
-    self_block[e_off + ge2_slots, b_off + ge2_slots] += eb_e[ge2_mask]
-    self_block[b_off + ge2_slots, e_off + ge2_slots] += eb_b[ge2_mask]
-    self_block[b_off + ge2_slots, t_off + ge2_slots] += eb_bt[ge2_mask]
+    quad_slots = slots[quad_mask]
+    self_block[t_off + quad_slots, e_off + quad_slots] += mix_t[quad_mask]
+    self_block[e_off + quad_slots, t_off + quad_slots] += mix_e[quad_mask]
```

This patch changes only (A), not (b), so it is algebraically safe for the FLRW (D_2) anchor under the invariant-manifold condition (r_h(\eta_0)=0,\ b_{hh}\equiv 0). 

---

## Q-7.1 — taxonomy of _operator_scales formulas

I will classify each expression as requested.

### 1. `geom_scale = sqrt(Σ n² + twist² + 0.25 · |R_scalar| + |R_pstf|² + |σ|²)`

**Classification:** **(b)** — derivable intent, but currently using placeholder scalarization and placeholder coefficient.

Reason:

* The **ingredients** ((n,a,{}^{(3)}R_{\langle ab\rangle},\sigma_{ab})) are physically correct.
* In a 1+3 covariant treatment, geometry-induced couplings are indeed built from shear, structure constants, curvature anisotropy, etc. ([ScienceDirect][3])
* But the specific scalar collapse
  [
  \sqrt{\sum n_i^2 + a^2 + 0.25|R| + |R_{\rm PSTF}|^2 + |\sigma|^2}
  ]
  is **not** a first-principles coefficient in the Boltzmann hierarchy.

The correct symbolic replacement is not a scalar constant but an operator-valued object such as
[
|\mathcal L_{\rm geom}[n,a,\sigma,{}^{(3)}S]|*\mu
]
or the backend mode-eigenvalue / transport norm (q*\mu).

The placeholder pieces that must be replaced are:

* the (0.25) coefficient,
* the root-sum-square scalarization,
* any use of this scalar as a direct substitute for a true mode transport scale.

### 2. `mix_scale = branch_scale · (0.08 + 0.04 · min(geom_scale, 3))`

**Classification:** **(c)** — entirely ad hoc.

Reason:

* (T\leftrightarrow E) collision mixing is exactly Thomson-derived and proportional to (\gamma_T).
* There is no first-principles FLRW or 1+3 kinetic coefficient of the form (0.08 + 0.04,\mathrm{geom_scale}).

So:
[
\boxed{\texttt{mix_scale} \text{ should be removed from the physical operator.}}
]

### 3. `twist_scale = branch_scale · twist / (1 + twist + h_abs)`

**Classification:** **(b)** — derivable intent, but current formula is placeholder.

Reason:

* Twist/(a^a)-driven geometric transport is real physics in class-B families.
* But the specific rational saturation
  [
  \frac{\texttt{twist}}{1+\texttt{twist}+|h|}
  ]
  is not a first-principles coefficient.

The correct symbolic form should be an operator norm or explicit coupling coefficient derived from the twist part of the transport operator:
[
\texttt{twist_scale}
\rightsquigarrow
|\mathcal L_{\rm twist}[a^a,h,\mu]|
\quad\text{or}\quad
C^{(\mu)}_{\rm twist}[a^a,h].
]

Without v5 §03A/§03B, the exact replacement cannot be fixed numerically.

### 4. `polarization_scale = 1 + 0.35 · twist_scale`

**Classification:** **(c)** — entirely ad hoc.

Reason:

* Any physical polarization modification from geometry should arise from the exact transport/collision operators, not from a universal scalar multiplier (1+0.35,\texttt{twist_scale}).
* There is no first-principles (0.35) here.

So this should be replaced by
[
\boxed{\texttt{polarization_scale}=1}
]
until a proper operator-level derivation is inserted.

### 5. `source_scale = 1 + 0.25 · min(|R_pstf| + |σ|, 2)`

**Classification:** **(c)** — entirely ad hoc as a physics coefficient.

Reason:

* Source terms do depend on curvature/shear in anisotropic backgrounds.
* But that dependence belongs in the actual source operator, not in a scalar fudge factor with coefficients (0.25) and a hard cap at (2).

So as a physics coefficient this is ad hoc. If used only as a numerical preconditioner **outside** the physics operator, that is a separate numerical-design question. But inside the physical operator, it should be neutralized.

---

## Q-7.2 — family_conditioned_kernel_law per-family deviations

The per-family law
[
\texttt{transport_scale},\ \texttt{mix_scale},\ \texttt{twist_mix},\ \texttt{polarization},\ \texttt{source},\ \texttt{local_drag},\ \texttt{cross_mode},\ \texttt{collision},\ \texttt{mode_plus},\ \texttt{mode_minus}
]
with 1–16% deviations from Type I is **not** a first-principles object.

### Classification

[
\boxed{
\text{These are not derived family constants; they are empirical / hand-tuned placeholders.}
}
]

### Why

A true family dependence must come from the actual algebra:

* class A/B split,
* structure constants (n^a{}_b),
* twist vector (a^a),
* curvature tensors,
* mode label (\mu),
* operator normalization.

That dependence is **matrix-valued** and mode-dependent. It is not a fixed set of ten numbers per family.

### Type II and Type III specifically

* **Type II**: class A, (a^a=0), one nonzero nilpotent structure-constant sector.
* **Type III**: class B (or special branch of VI(_h) with (h=-1)), nonzero (a^a), nontrivial anisotropic curvature.

The correct transport and mixing operators for these families must be assembled directly from their structure constants and the family backend. There is no physically unique scalar such as
[
\texttt{transport_scale}=1.10\quad\text{(Type II)}
]
or
[
\texttt{transport_scale}=1.16\quad\text{(Type III)}
]
that can be derived from first principles **without** first choosing:

* the backend basis,
* the mode-label normalization,
* the operator norm used to compress the matrix to a scalar.

So the requested “derive the correct Type-II and Type-III scalar values” cannot be done from the excerpt alone. The right statement is:

[
\boxed{
\text{There are no unique correct scalar replacements. The correct family dependence is the explicit operator itself.}
}
]

This is exactly what a 1+3 covariant/tetrad treatment implies: family structure enters through explicit tensor couplings, not a global 1.10 or 0.96 modifier. ([ScienceDirect][3])

---

## Q-7.3 — FLRW reduction of _operator_scales

Take the strict FLRW limit:

[
n^a{}*b = 0,\qquad a^a=0,\qquad \sigma*{ab}=0,\qquad {}^{(3)}R_{\langle ab\rangle}=0.
]

Then the physical reductions are:

### 1. `geom_scale`

If this quantity is intended to control the **transport** magnitude, then in FLRW it must reduce to the **mode transport scale**,
[
\boxed{\texttt{geom_scale} \to q_\mu \quad (\text{or } k \text{ in MB notation}),}
]
not to a hard-coded floor value of (1).

So the current reduction
[
\texttt{geom_scale} = \max(0,1)=1
]
is not a physically meaningful transport reduction. It is only a placeholder floor.

### 2. `mix_scale`

Since (T\leftrightarrow E) mixing is purely Thomson quadrupole physics,

[
\boxed{\texttt{mix_scale}\to 0 \quad \text{in free-streaming FLRW}.}
]

The code gives
[
0.08+0.04\cdot 1 = 0.12,
]
which is wrong.

### 3. `twist_scale`

Since (a^a=0) in Bianchi I / FLRW,

[
\boxed{\texttt{twist_scale}\to 0.}
]

The code does satisfy this structurally.

### 4. `polarization_scale`

If this is a **neutral multiplicative modifier** of the channel normalization, then in FLRW it should reduce to
[
\boxed{\texttt{polarization_scale}\to 1.}
]

That is acceptable.

### 5. `source_scale`

This depends on interpretation.

* If `source_scale` is a neutral multiplier on an already explicit source operator, then in FLRW it should reduce to
  [
  \boxed{\texttt{source_scale}\to 1.}
  ]
* If it is meant to encode anisotropic-source physics by itself, then it should reduce to (0).

From the excerpt alone, I cannot tell which role it plays. So this is a **v5 spec ambiguity**. The current formula yields (1), which is acceptable only under the first interpretation.

### Summary

The consistent FLRW reduction is therefore:

[
\boxed{
\texttt{geom_scale}\to q_\mu\ (\text{not }1),\quad
\texttt{mix_scale}\to 0,\quad
\texttt{twist_scale}\to 0,\quad
\texttt{polarization_scale}\to 1,\quad
\texttt{source_scale}\to 1\ \text{(if neutral)}.
}
]

So the code mismatch is definite for `mix_scale`, structurally problematic for `geom_scale`, and interpretation-dependent for `source_scale`.

---

## Q-7.4 — minimal patch for ❼ and expected post-patch spectrum

### Minimal patch

There are two parts:

1. **remove all hand-tuned scalar physics from the FLRW / near-FLRW operator path**;
2. **defer any true family-dependent reintroduction to the operator-level v5 §03A/§03B derivation.**

The exact replacement for `geom_scale` in the anisotropic case **cannot** be fixed from this excerpt alone, because the physical transport scale must come from the family backend’s mode eigenvalue / transport operator norm, not from a scalar formula built from (n,a,R,\sigma). So the patch below is the minimal *safe* one.

```diff
@@ def _operator_scales(...):
-    geom_scale = sqrt(Σ n² + twist² + 0.25·|R_scalar| + |R_pstf|² + |σ|²)
-    geom_scale = max(geom_scale, 1)
+    # Physical transport scale must come from the backend mode eigenvalue /
+    # transport operator norm (v5 §03A/§03B), not from a heuristic geometry norm.
+    # Keep a diagnostic norm if desired, but do not use it as physics.
+    geom_diagnostic = sqrt(Σ n² + twist² + |R_pstf|² + |σ|²)
+    geom_scale = backend_transport_scale  # REQUIRES v5 spec; do not guess here.

@@
-    mix_scale            = branch_scale · (0.08 + 0.04 · min(geom_scale, 3))
-    twist_scale          = branch_scale · twist / (1 + twist + h_abs)
-    polarization_scale   = 1 + 0.35 · twist_scale
-    source_scale         = 1 + 0.25 · min(|R_pstf| + |σ|, 2)
+    # Remove hand-tuned physics surrogates from the operator.
+    mix_scale          = 0.0
+    twist_scale        = 0.0
+    polarization_scale = 1.0
+    source_scale       = 1.0

@@
-    family_law = _family_conditioned_kernel_law(bg, backend)
+    # Until v5 §03A/§03B derives operator-level family dependence,
+    # do not inject hard-coded 1-16% family tunings into the physics operator.
+    family_law = _identity_kernel_law()
```

### What this means algebraically

* defect ❺ fixes the baryon–dipole Thomson relaxation block,
* defect ❻ restores the quadrupole-only, (\gamma_T)-proportional (T/E) collision block,
* defect ❼ removes the remaining ad-hoc positive-growth surrogates from the physical operator.

Then:

#### FLRW free-streaming limit ((\gamma_T=0))

The full (A_{\text{right}}) reduces to:

* weighted-skew free-streaming in the harmonic sector,
* no (T/E) or (E/B/T/B) collision mixing,
* no hand-tuned positive diagonal/mixing terms,
* local and source residual blocks either decouple or remain neutral.

Therefore
[
\boxed{\Re\lambda_{\max}=0.}
]

The spectrum is purely imaginary (plus possibly exact zero modes), exactly as expected for collisionless free streaming.

#### FLRW with (\gamma_T>0)

The real part comes only from physical Thomson relaxation:

* baryon–photon dipole relaxation,
* ((\Theta_2,E_2)) quadrupole polarization relaxation,
* diagonal damping of higher photon/polarization multipoles.

So after defects ❺❻❼ are fixed:

[
\boxed{\Re\lambda_{\max}\le 0.}
]

Any nonzero negative real part is physical Thomson relaxation. The only possible zero real parts are conserved/neutral directions (e.g. common-velocity or covered-mode directions), not unstable growth. Neutrino free streaming remains conservative in the collisionless limit; it does not create positive or negative real parts by itself. The FLRW (D_2) anchor remains protected because all these patches modify only (A), not (b_{hh}), and the FLRW invariant manifold keeps (r_h\equiv 0). 

[1]: https://www.osti.gov/biblio/278910 "https://www.osti.gov/biblio/278910"
[2]: https://journals.aps.org/prd/abstract/10.1103/PhysRevD.55.1830 "https://journals.aps.org/prd/abstract/10.1103/PhysRevD.55.1830"
[3]: https://www.sciencedirect.com/science/article/pii/S0003491600960342 "https://www.sciencedirect.com/science/article/pii/S0003491600960342"
