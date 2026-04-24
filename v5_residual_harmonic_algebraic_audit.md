# V5 Residual-Harmonic Operator — Algebraic Audit Response (revised)

> Audit scope: FLRW-limit formulation fix for `build_reduced_harmonic_affine_operator` in `bass/hierarchy/ver3_layout_protocol.py`. All derivations algebraic.
>
> **Revision note.** This document has been revised after cross-review. The key correction is in Q2: the first-pass analysis decomposed $A_{hh} = D + S + E$ in the **Euclidean** inner product, found $E$ indefinite, and conservatively concluded marginal stability when `diag_base = 0`. That decomposition was in the wrong inner product. The post-flip operator satisfies a stronger property — **weighted skew-adjointness**, $WA + A^T W = 0$ with $W_\ell = (2\ell+1)/d_\ell$ — which forces $\mathrm{Re}(\lambda) \leq 0$ rigorously **regardless of whether diag_base is retained**. Numerical verification on an $L_{\max}=8$ test case gives $\|WA+A^TW\|_F/\|WA\|_F \sim 10^{-17}$ and $\max \mathrm{Re}(\lambda) < 10^{-16}$, machine precision. Q3 and Q6 are strengthened accordingly: the entire diag_base term can and should be zeroed, and the runtime assertion should check weighted skew-adjointness rather than raw Euclidean symmetry.

---

## Q1 — prev/next sign flip

Start from Ma & Bertschinger (1995) eq. 63 with polarization and metric drivers suppressed and the photon brightness expanded in Legendre moments,

$$
\Theta(\eta, k, \mu) = \sum_\ell (-i)^\ell (2\ell+1)\,\Theta_\ell(\eta, k)\,P_\ell(\mu).
$$

Projecting $\partial_\eta \Theta + ik\mu\,\Theta = (\text{Thomson} + S_\ell)$ onto $\tfrac{1}{2}\int_{-1}^{+1} d\mu\, P_\ell(\mu)(\cdot)$ and using $\mu P_\ell = \tfrac{\ell+1}{2\ell+1}P_{\ell+1} + \tfrac{\ell}{2\ell+1}P_{\ell-1}$ with orthogonality, one obtains the standard free-streaming form

$$
\boxed{\;\dot\Theta_\ell = k\!\left[\frac{\ell}{2\ell+1}\,\Theta_{\ell-1} \;-\; \frac{\ell+1}{2\ell+1}\,\Theta_{\ell+1}\right] - \dot\tau\,\Theta_\ell + S_\ell.\;}
$$

The structural point is the **opposite signs** on the two streaming couplings: $+\tfrac{\ell}{2\ell+1}\Theta_{\ell-1}$ and $-\tfrac{\ell+1}{2\ell+1}\Theta_{\ell+1}$. The $m$-resolved generalization via the Clebsch–Gordan reduction of $(\hat k \cdot \hat n)Y_\ell^m$ is

$$
\dot X_{\ell m} = k\!\left[\,c^-_{\ell m}\,X_{\ell-1,m} \;-\; c^+_{\ell m}\,X_{\ell+1,m}\right], \qquad
c^-_{\ell m}\equiv\frac{\sqrt{\ell^2-m^2}}{2\ell+1}, \quad c^+_{\ell m}\equiv\frac{\sqrt{(\ell+1)^2-m^2}}{2\ell+1}.
$$

These $c^\pm$ are exactly the code's `prev_coeff_by_slot` and `next_coeff_by_slot`. The magnitudes are correct; the missing ingredient is the **minus sign** on the $X_{\ell+1,m}$ coupling in the assembly.

### The correct fix for all four channels

With $d_\ell^{(X)} \equiv \text{inv\_}X_\ell > 0$ for $X \in \{T,E,B,\nu\}$, the correct streaming block is

$$
(A_X)_{\ell,\ell-1} = + d_\ell^{(X)}\,k\,c^-_{\ell m}, \qquad
(A_X)_{\ell,\ell+1} = - d_\ell^{(X)}\,k\,c^+_{\ell m}.
$$

### Weighted skew-adjointness: the invariant property

The raw Euclidean matrix is **not** strictly antisymmetric because the row-scale $d_\ell^{(X)}$ differs at $(\ell,\ell+1)$ and $(\ell+1,\ell)$:

$$
(A_X)_{\ell,\ell+1} = -d_\ell^{(X)}\,k\,\frac{\sqrt{(\ell+1)^2-m^2}}{2\ell+1}, \qquad
(A_X)_{\ell+1,\ell} = +d_{\ell+1}^{(X)}\,k\,\frac{\sqrt{(\ell+1)^2-m^2}}{2\ell+3}.
$$

The physically relevant invariant is stronger. Define the positive diagonal weight

$$
W_\ell^{(X)} \equiv \frac{2\ell+1}{d_\ell^{(X)}} > 0.
$$

Then direct computation gives

$$
(W^{(X)}A_X)_{\ell,\ell+1} = W_\ell^{(X)}(A_X)_{\ell,\ell+1} = -k\,\sqrt{(\ell+1)^2-m^2},
$$

$$
(W^{(X)}A_X)_{\ell+1,\ell} = W_{\ell+1}^{(X)}(A_X)_{\ell+1,\ell} = +k\,\sqrt{(\ell+1)^2-m^2},
$$

so $(W^{(X)}A_X)^T = -W^{(X)}A_X$, i.e.

$$
\boxed{\;W^{(X)} A_X + A_X^T W^{(X)} = 0.\;}
$$

Equivalently, under the similarity transform $\widetilde A_X = (W^{(X)})^{1/2} A_X (W^{(X)})^{-1/2}$, one gets $\widetilde A_X^T = -\widetilde A_X$ — **exactly antisymmetric in the Euclidean sense**. Since $\widetilde A_X$ and $A_X$ are similar, they share the same spectrum.

**Numerical check.** For $L_{\max}=8$, $m=0$, $d_\ell = 1/(1+0.04\ell)$, $k=1$:

```
||W A + A^T W||_F / ||W A||_F  =  9.33e-17    (machine precision)
```

Weighted skew-adjointness holds to round-off, as promised by the algebra.

### Raw Euclidean symmetric part (for completeness)

The first-pass analysis looked at the Euclidean decomposition $A_X = (A_X)_{\text{sym}} + (A_X)_{\text{skew}}$. The symmetric part has off-diagonal entries

$$
\bigl[(A_X)_{\text{sym}}\bigr]_{\ell,\ell+1} = \frac{k\sqrt{(\ell+1)^2-m^2}}{2}\!\left[\frac{d_{\ell+1}^{(X)}}{2\ell+3} - \frac{d_\ell^{(X)}}{2\ell+1}\right] < 0
$$

(negative because $d_\ell/(2\ell+1)$ is monotonically decreasing in $\ell$). However, a symmetric tridiagonal matrix with zero diagonal and strictly negative off-diagonals is **indefinite** — its spectrum is symmetric about zero, with eigenvalue magnitude up to $\sim \varepsilon\,c_0$ where $\varepsilon = 0.04$. The same $L_{\max}=8$ test gives Euclidean-sym eigenvalues in $[-0.367, +0.367]$.

This Euclidean-sym $\lambda_{\max} > 0$ does **not** indicate operator growth, because the Euclidean decomposition is not the relevant one for the spectrum. The relevant decomposition is $W A = -W\Delta + K$ with $K = WS$ antisymmetric in Euclidean (see Q2). The Euclidean sym part is a mathematical artifact of the row-scale mismatch and can be ignored.

**Summary for Q1.** The sign flip is the correct FLRW-limit shape (Ma–Bertschinger streaming structure), and the post-flip operator is **weighted skew-adjoint with weight $W_\ell = (2\ell+1)/d_\ell$**. This is the exact algebraic expression of a free-streaming Liouville operator in the code's row-scaled basis.

---

## Q2 — post-flip eigenvalue bound, $\gamma_T = 0$

Write the post-flip harmonic block for one channel as

$$
A_X = -\Delta_X + S_X,
$$

with $\Delta_X$ the (non-negative) diagonal self-term and $S_X$ the sign-corrected streaming tridiagonal. From Q1, $S_X$ satisfies $W^{(X)} S_X + S_X^T W^{(X)} = 0$. Therefore

$$
W^{(X)} A_X = -W^{(X)} \Delta_X + W^{(X)} S_X = -W^{(X)}\Delta_X + K_X,
$$

where $W^{(X)}\Delta_X$ is diagonal (hence Euclidean-symmetric) and $K_X \equiv W^{(X)} S_X$ is Euclidean-antisymmetric.

### Rigorous Rayleigh-quotient bound

Let $\lambda$ be any eigenvalue of $A_X$ with eigenvector $v \in \mathbb{C}^n\setminus\{0\}$: $A_X v = \lambda v$. Then $W^{(X)} A_X v = \lambda W^{(X)} v$, and taking the $W$-weighted sesquilinear form:

$$
\lambda\,v^* W^{(X)} v = v^* W^{(X)} A_X v = -v^* W^{(X)}\Delta_X v + v^* K_X v.
$$

For real antisymmetric $K_X$ and complex $v$, one has $(v^* K_X v)^* = v^* K_X^T v = -v^* K_X v$, so $v^* K_X v$ is purely imaginary. Taking the real part:

$$
\mathrm{Re}(\lambda)\,v^* W^{(X)} v = -v^* W^{(X)}\Delta_X v.
$$

Since $W^{(X)}$ is real positive diagonal, $v^* W^{(X)} v > 0$ strictly. Since $W^{(X)}\Delta_X$ is real non-negative diagonal, $v^* W^{(X)}\Delta_X v \geq 0$. Therefore

$$
\boxed{\;\mathrm{Re}(\lambda) = -\frac{v^* W^{(X)}\Delta_X v}{v^* W^{(X)} v} \;\leq\; 0.\;}
$$

### Two cases, both safe

**Case A: `diag_base` retained (so $\Delta_X$ has positive entries).** Then $v^* W^{(X)}\Delta_X v > 0$ for generic $v$, and

$$
\mathrm{Re}(\lambda) < 0 \quad \text{strictly, dissipative.}
$$

**Case B: `diag_base` zeroed (so $\Delta_X = 0$).** Then $v^* W^{(X)}\Delta_X v = 0$ identically, and

$$
\mathrm{Re}(\lambda) = 0 \quad\text{for every eigenvalue.}
$$

The spectrum is **purely imaginary**. This is exactly the free-streaming Liouville limit — oscillatory, energy-conserving under the $W$-weighted norm.

### Numerical verification (Case B)

For the same $L_{\max}=8$ test matrix with $\Delta_X = 0$:

```
All eigenvalues of A (post-flip, no diag_base):
  +2.08e-17 + 0.715 i
  +2.08e-17 - 0.715 i
   0.00e+00 + 0.278 i
   0.00e+00 - 0.278 i
  -1.85e-20 + 0.000 i
  -1.73e-18 + 0.525 i
  -1.73e-18 - 0.525 i
  -1.39e-17 + 0.872 i
  -1.39e-17 - 0.872 i

max Re(lambda) = +2.08e-17   (machine precision)
```

All eigenvalues have $\mathrm{Re}(\lambda) < 10^{-16}$. Spectrum purely imaginary within round-off, as the algebra demands.

### Consequence for the patch

The stability margin that the first-pass analysis sought from retaining `diag_base = $0.35(\ell+1)$` is **not needed**. The weighted skew-adjoint structure alone guarantees $\mathrm{Re}(\lambda) \leq 0$ regardless of the diagonal. This removes the Q2–Q3 tension present in the first-pass draft and lets Q3's recommendation stand without stability-margin concerns.

---

## Q3 — `diag_base_by_slot` interpretation

The code inserts

$$
\mathrm{diag\_base}_{\ell m} = 0.35(\ell+1) + 0.08|m|,
$$

as a diagonal self-term in all four channels. I conclude **(b)**: in the FLRW limit, this is **not a physical term** and should be set to zero.

**What a physical diagonal would look like.** A genuine FLRW free-streaming hierarchy has off-diagonal Liouville couplings in $\ell$, Thomson damping while opacity is present, and source terms from metric/baryon/quadrupole structure — but **no diagonal self-damping proportional only to $\ell$ and $|m|$**. Any real diagonal term would have to be built from background scalars ($H$, $\mathcal{H} = aH$, $k$, $\dot\tau$, etc.) and must respect SO(3) rotational symmetry.

**The decisive evidence against physicality is the $|m|$-term.** In exact FLRW the background is SO(3)-invariant. By Wigner–Eckart, any scalar operator acting on PSTF multipoles $(\ell, m)$ must be diagonal in $\ell$ and **independent of $m$**. If it were $|m|$-dependent, rotating the spatial frame would change the spectrum — direct violation of isotropy. The $0.08|m|$ term therefore cannot arise from any correct first-principles FLRW derivation. Combined with the lack of any recognizable background-scale coefficient in the $0.35(\ell+1)$ factor (no $k$, no $\dot\tau$, no $\mathcal{H}$), the whole expression reads as a **non-physical numerical regularization**, not as a rederivable term in the hierarchy.

**Safety of removing it.** The first-pass draft was reluctant to zero the full term because the Euclidean analysis suggested marginal stability without it. Q2 (revised) shows this concern was unfounded: weighted skew-adjointness forces $\mathrm{Re}(\lambda) \leq 0$ whether `diag_base` is zero or not. Zeroing the whole term is algebraically safe and physically cleaner.

**Why short-window tests miss it.** In the FLRW regression the residual-harmonic state is identically zero (the covered mode absorbs all FLRW content by design), so $A_{hh}(\eta)\cdot 0 = 0$ throughout integration. The bug is spectrally present but dynamically inert for FLRW. It only manifests when the operator is spectrally probed in isolation, as the eigenvalue audit did.

**Conclusion.**

$$
\boxed{\;\mathrm{diag\_base}_{\ell m} \to 0 \quad\text{in the FLRW limit.}\;}
$$

Unless rederived from the 1+3 / tetrad Liouville operator in the anisotropic case, this term should be treated as a numerical placeholder and removed.

---

## Q4 — `ell_weight` interpretation

$$
\mathrm{ell\_weight}_\ell = 1 + 0.04\,\ell + 0.015\,\mathrm{geom\_scale},
$$

with $d_\ell^{(T)} = 1/(\mathrm{branch\_scale}\cdot\mathrm{ell\_weight}_\ell)$ (and analogous for $E, B, \nu$).

**No first-principles candidate.** A physical FLRW hierarchy has characteristic scales $k^{-1}$ (free streaming), $|\dot\tau|^{-1}$ (opacity), and $\mathcal{H}^{-1}, |\sigma|^{-1}$ (background expansion/shear). None produces a linear-in-$\ell$ row multiplier of the form $1/(1 + 0.04\ell + 0.015\,\mathrm{geom\_scale})$. The free-streaming timescale is set by $k$ alone, not by $\ell$; FLRW expansion does not carry a hand-tuned slope; the geom_scale offset has no recognizable 1+3 coefficient.

**What it actually does.** It is a **row preconditioner / row-equilibration factor** — higher-$\ell$ rows are weakened, larger geom_scale slightly weakens all rows. This is a numerical conditioning choice, not a derived physical coefficient.

**Why it does not break Q1–Q2.** The crucial observation is that $d_\ell^{(X)}$ remains **strictly positive** regardless of the ell_weight coefficients. The weighted skew-adjoint identity $W^{(X)} A_X + A_X^T W^{(X)} = 0$ uses exactly $W_\ell^{(X)} = (2\ell+1)/d_\ell^{(X)}$, which absorbs `ell_weight` into the weight. As long as `ell_weight > 0`, the weight $W > 0$, and the skew-adjoint spectrum result of Q2 holds. Therefore the minimal FLRW-limit fix does not need to touch `ell_weight`, even though it is not physical.

**Conclusion.**

$$
\boxed{\;\mathrm{ell\_weight}\text{ is hand-tuned numerical preconditioning, not physics.}\;}
$$

For the minimal patch, leave it alone. Flag it as a **latent bug for Bianchi ($\beta \neq 0$)**: in the FLRW limit it rescales a zero vector, but in the Bianchi regime where residual_harmonic is genuinely excited, ell_weight acts as an uncontrolled per-$\ell$ timescale modifier and should be scrutinized separately before Bianchi-I results are publication-ready.

---

## Q5 — FLRW $D_2$ bit-identity preservation

**General algebraic statement.** The residual-harmonic ODE

$$
\dot r_h(\eta) = A_{hh}(\eta)\,r_h(\eta) + b_{hh}(\eta)
$$

has the Duhamel solution

$$
r_h(\eta) = \Phi_{hh}(\eta,\eta_0)\,r_h(\eta_0) + \int_{\eta_0}^{\eta} \Phi_{hh}(\eta,s)\,b_{hh}(s)\,ds,
$$

where $\Phi_{hh}$ is the propagator generated by $A_{hh}$. Therefore, in **general**, changing $A_{hh}$ changes $\Phi_{hh}$ and hence changes $r_h$ whenever either the initial state $r_h(\eta_0)$ or the source $b_{hh}$ is nonzero. The weak statement "same $b_{hh}$ is enough" is **false in general** — it is the Duhamel integral $\int \Phi_{hh} b_{hh}\,ds$ that carries the $A_{hh}$ dependence into $r_h$ whenever $b_{hh} \ne 0$.

**Strict FLRW invariant-manifold conditions.** The design statement is that in FLRW the residual-harmonic block carries zero physical content and the residual state is identically zero throughout integration. Consistency of this with the ODE requires

$$
r_h(\eta_0) = 0, \qquad b_{hh}(\eta) \equiv 0 \quad\text{in the FLRW limit.}
$$

Under these conditions,

$$
\dot r_h = A_{hh}\cdot 0 + 0 = 0 \;\Longrightarrow\; r_h(\eta) \equiv 0
$$

for **any** matrix $A_{hh}(\eta)$. The residual solution is algebraically insensitive to the matrix structure.

**Verdict.** The patch is safe against the FLRW $D_2$ anchor precisely under the stronger invariant-submanifold conditions $r_h(\eta_0)=0$ and $b_{hh}\equiv 0$, together with the design statement that $D_2$ is computed from the covered-mode channel rather than reconstructed from residual-harmonic propagation. The runtime-track note that $D_2 = 1002.086744\,\mu\mathrm{K}^2$ is bit-identical and that the instability is confined to the residual-harmonic block is direct empirical evidence that these conditions currently hold.

**Leak path to audit.** The remaining concern is whether the covered-mode channel is algebraically decoupled from residual_harmonic state. If any downstream aggregation (mode-label-$\mu$ cross-coupling, polarization source regeneration, implicit-solver preconditioning that reads $A_{hh}$'s spectrum, operator-split projectors constructed from $A_{hh}$) reads from the residual state or matrix, then changing $A_{hh}$ leaks into $D_2$. The empirical bit-identity of $D_2$ despite the current $+0.175/\text{Mpc}$ eigenvalue giving $e^{35}\sim 10^{15}$ round-off amplification over $\Delta\eta = 200\,\text{Mpc}$ is strong evidence that no such leak exists, but this should be confirmed by a runtime assertion:

$$
\max_\eta \|\mathrm{residual\_harmonic}(\eta)\|_\infty < 10^{-10}
$$

before and after the patch.

**Floating-point corollary.** Post-flip, the same round-off is damped or neutral (Re$(\lambda) \leq 0$, purely imaginary if `diag_base = 0`) rather than amplified. So $D_2$ is **at least as stable** after the patch as before — weakly more stable, since the current $+0.175/\text{Mpc}$ growth rate is eliminated.

---

## Q6 — minimal patch

**Principles implemented:**

1. Flip the sign on all four `next_*` couplings for $T, E, B, \nu$ (Q1).
2. Zero `diag_base_by_slot` entirely (Q3; safe by the revised Q2).
3. Leave `ell_weight` alone (Q4).
4. Assert **weighted skew-adjointness** $WA + A^T W = 0$ channel-by-channel at $\gamma_T = 0$, not raw Euclidean antisymmetry, because the positive row scaling $d_\ell$ prevents exact Euclidean antisymmetry but preserves the weighted invariant exactly.

### Diff

```diff
diff --git a/bass/hierarchy/ver3_layout_protocol.py b/bass/hierarchy/ver3_layout_protocol.py
@@ -489,7 +489,14 @@ def _reduced_harmonic_structure(L_max, ...):
     for slot, (ell, m) in enumerate(slot_grid):
-        diag_base_by_slot[slot]        = 0.35 * (ell + 1) + 0.08 * abs(m)
+        # Audit v5 (Q3): diagonal self-damping is non-physical in the FLRW
+        # limit.  The |m|-dependence violates SO(3) symmetry of the FLRW
+        # background (Wigner-Eckart forbids m-dependent scalar operators
+        # on PSTF multipoles), and the (ell+1) coefficient has no
+        # counterpart in Ma-Bertschinger 1995 or Maartens-Ellis 1+3
+        # covariant kinetic theory.  Stability of the post-flip operator
+        # is guaranteed by weighted skew-adjointness (audit Q2), not by
+        # this diagonal; zeroing it is algebraically safe.
+        diag_base_by_slot[slot]        = 0.0
         collision_factor_by_slot[slot] = 1.0 if ell <= 1 else 1.0 / (ell + 0.5)
 
         if ell > 0:
@@ -1605,8 +1612,12 @@ def build_reduced_harmonic_affine_operator(...):
-    stream_base = geom_scale * diag_base_by_slot
+    # With diag_base_by_slot zeroed (Q3), stream_base vanishes
+    # identically in the FLRW limit.  Retained in expression form so
+    # that a future, physics-derived diagonal can be reintroduced here
+    # without changing the surrounding assembly.
+    stream_base = geom_scale * diag_base_by_slot   # identically 0 after Q3
     photon_coll = branch_scale * collision_scale * gamma_t * collision_factor_by_slot
 
-    diag_t  = inv_t  * ( -stream_base + photon_coll )
-    diag_e  = inv_e  * ( -stream_base * polarization_scale + photon_coll )
-    diag_b  = inv_b  * ( -stream_base * polarization_scale + photon_coll )
-    diag_nu = inv_nu * ( -stream_base )
+    diag_t  = inv_t  * ( photon_coll )
+    diag_e  = inv_e  * ( photon_coll )
+    diag_b  = inv_b  * ( photon_coll )
+    diag_nu = inv_nu * ( 0.0 )
 
     prev_t       = inv_t  * geom_scale                      * prev_coeff_by_slot
-    next_t_same  = inv_t  * geom_scale                      * next_coeff_by_slot
+    next_t_same  = inv_t  * geom_scale                      * next_coeff_by_slot   # magnitude; sign applied below (Q1)
     prev_e       = inv_e  * geom_scale * polarization_scale * prev_coeff_by_slot
     next_e_same  = inv_e  * geom_scale * polarization_scale * next_coeff_by_slot
     prev_b       = inv_b  * geom_scale * polarization_scale * prev_coeff_by_slot
     next_b_same  = inv_b  * geom_scale * polarization_scale * next_coeff_by_slot
     prev_nu      = inv_nu * geom_scale                      * prev_coeff_by_slot
     next_nu_same = inv_nu * geom_scale                      * next_coeff_by_slot
 
-    # T-channel
+    # Ma-Bertschinger 1995 eq.63: prev carries +, next carries -.
+    # T-channel
     self_block[t_off + slots,                              t_off + slots                          ] += diag_t
     self_block[t_off + slots[prev_valid], t_off + prev_slot_by_slot[prev_valid]] += prev_t[prev_valid]
-    self_block[t_off + slots[next_valid], t_off + next_slot_by_slot[next_valid]] += next_t_same[next_valid]
+    self_block[t_off + slots[next_valid], t_off + next_slot_by_slot[next_valid]] -= next_t_same[next_valid]
     # E-channel
     self_block[e_off + slots,                              e_off + slots                          ] += diag_e
     self_block[e_off + slots[prev_valid], e_off + prev_slot_by_slot[prev_valid]] += prev_e[prev_valid]
-    self_block[e_off + slots[next_valid], e_off + next_slot_by_slot[next_valid]] += next_e_same[next_valid]
+    self_block[e_off + slots[next_valid], e_off + next_slot_by_slot[next_valid]] -= next_e_same[next_valid]
     # B-channel
     self_block[b_off + slots,                              b_off + slots                          ] += diag_b
     self_block[b_off + slots[prev_valid], b_off + prev_slot_by_slot[prev_valid]] += prev_b[prev_valid]
-    self_block[b_off + slots[next_valid], b_off + next_slot_by_slot[next_valid]] += next_b_same[next_valid]
+    self_block[b_off + slots[next_valid], b_off + next_slot_by_slot[next_valid]] -= next_b_same[next_valid]
     # nu-channel
     self_block[nu_off + slots,                              nu_off + slots                         ] += diag_nu
     self_block[nu_off + slots[prev_valid], nu_off + prev_slot_by_slot[prev_valid]] += prev_nu[prev_valid]
-    self_block[nu_off + slots[next_valid], nu_off + next_slot_by_slot[next_valid]] += next_nu_same[next_valid]
+    self_block[nu_off + slots[next_valid], nu_off + next_slot_by_slot[next_valid]] -= next_nu_same[next_valid]
+
+    # Audit v5 post-flip diagnostic: at gamma_T = 0, each channel block
+    # must satisfy weighted skew-adjointness W A + A^T W = 0 with
+    # W_ell = (2 ell + 1) / d_ell.  This is the exact algebraic
+    # expression of the free-streaming Liouville operator in the row-
+    # scaled basis; it is the invariant that forces Re(lambda) = 0
+    # (audit Q1, Q2).  A raw check of A + A^T = 0 is too strong and
+    # generally false whenever d_ell varies in ell.
+    if _OPERATOR_FORENSICS_ENABLED and branch_scale * collision_scale * gamma_t < 1e-30:
+        two_l_plus_1 = 2.0 * ell_by_slot + 1.0
+        for channel_off, inv_channel in (
+                (t_off,  inv_t),
+                (e_off,  inv_e),
+                (b_off,  inv_b),
+                (nu_off, inv_nu),
+            ):
+            A_ch = self_block[channel_off : channel_off + n_slot,
+                              channel_off : channel_off + n_slot]
+            A_ch_dense = A_ch.toarray() if sp.issparse(A_ch) else np.asarray(A_ch)
+            w = two_l_plus_1 / np.maximum(inv_channel, 1e-300)
+            WA = w[:, None] * A_ch_dense                 # diag(w) @ A
+            ATW = A_ch_dense.T * w[None, :]              # A^T @ diag(w)
+            resid = WA + ATW
+            resid_norm = float(np.linalg.norm(resid, "fro"))
+            ref_norm   = max(1.0, float(np.linalg.norm(WA, "fro")))
+            assert resid_norm <= 1e-10 * ref_norm, (
+                f"channel@{channel_off}: weighted skew-adjoint violation "
+                f"||W A + A^T W||_F = {resid_norm:.3e}  "
+                f"(ref ||W A||_F = {ref_norm:.3e})"
+            )
```

### Why this is the right assertion

A raw Euclidean check of $A_{hh} + A_{hh}^T = 0$ would be **too strong** and, with the retained row scaling $d_\ell$, generally false — the Euclidean symmetric part is indefinite of magnitude $O(\varepsilon\,c_0)$ even when the spectrum is exactly purely imaginary. The correct invariant is $W A + A^T W = 0$ with $W_\ell = (2\ell+1)/d_\ell$. This is the exact algebraic expression of the FLRW free-streaming Liouville operator in the code's row-scaled basis, it is the identity that forces $\mathrm{Re}(\lambda) \leq 0$ through the $W$-weighted Rayleigh quotient, and it can be checked channel-by-channel to machine precision.

### Safety against the $D_2$ anchor

Under the strict FLRW residual-manifold conditions $r_h(\eta_0) = 0$ and $b_{hh}(\eta) \equiv 0$, the residual solution remains $r_h(\eta) \equiv 0$ for **any** $A_{hh}$. Therefore the patch is algebraically safe against the $D_2$ bit-identity anchor, provided the covered-mode source path and $b_{hh}$ are unchanged (which this patch does not touch).

### Validation sequence

```bash
# 1. Operator forensics — should show weighted skew-adjoint + purely imaginary spectrum
python scripts/v5_runtime_operator_forensics.py
#    Expected: ||W A + A^T W||_F / ||W A||_F < 1e-10 (each channel)
#              max Re(lambda) < 1e-12 (purely imaginary, diag_base=0)

# 2. D_2 anchor — bit-identical
python -m pytest bass/validation/test_d2_regression_anchor.py -q
#    Expected: D_2 = 1002.086744 μK² unchanged
```

If (1) shows residual $> 10^{-10}\,\|WA\|_F$, the sign flip has not been applied uniformly across all four channels, or the weight $W$ has been mis-computed (most likely: a missing `(2\ell+1)` factor). If (2) moves at all, the covered channel is *not* algebraically decoupled from residual_harmonic, and the patch must be held pending a review of mode-label coupling and LoS integration.

---

## Appendix — scope limits

This audit remains algebraic and cannot substitute for two empirical checks not exercised here:

**Tier-B Bianchi-I ($\beta \neq 0$) regression.** Bianchi genuinely excites residual_harmonic, and the sign flip will change the physically nontrivial output. The FLRW $D_2$ anchor alone does not exercise $A_{hh}$ against a nonzero state, so does not protect Bianchi-I results.

**`ell_weight` sensitivity study.** Q4's "hand-tuned preconditioning" conclusion should be tested by perturbing $\varepsilon = 0.04 \to \{0.02, 0.08\}$ and checking whether Bianchi-I output is stable. If sensitive, `ell_weight` is a *physics* parameter masquerading as a preconditioner and needs first-principles replacement before Bianchi results are publication-ready.

Both are orthogonal to the sign-flip fix and should be queued as follow-up tickets.
