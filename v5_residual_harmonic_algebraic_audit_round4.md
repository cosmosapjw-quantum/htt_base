## Q-10 — q_h for Type VII₀ helical partners

Under the frozen VII₀ slice-Laplacian convention stated in the prompt,
[
\Delta \psi = \bigl(k_1^2+k_3^2+k_{\rm twist}^2\bigr)\psi,
]
with the anchor mode carrying (k_{\rm twist}^2=0) and the helical partner modes carrying the discrete helical Casimir shift (k_{\rm twist}^2=+1), the transport eigenvalues are forced to be

[
q_0(k_1,k_3)=\sqrt{k_1^2+k_3^2},
\qquad
q_h(k_1,k_3)=\sqrt{k_1^2+k_3^2+1}.
]

So among the options in the prompt, the correct one is **(a)**:
[
\boxed{q_h=\sqrt{k_1^2+k_3^2+1}}.
]

This is the unique closed form compatible with the prompt's frozen unit helical eigenvalue and with the VII(_h)(\to)VII(_0) limit in which the helical partners remain degenerate in the real ((\cos,\sin)) basis. The general helical-mode structure of VII(_0)/VII(_h) and the fact that the family harmonic analysis is spectral rather than scalar-tuned are consistent with Pontzen's Bianchi mode treatment and the explicit harmonic/spectral analysis of Bianchi I–VII groups. ([Physical Review Journals][1])

In code units where (|k|=\sqrt{k_1^2+k_3^2}), the dimensionless ratio is
[
\frac{q_h}{|k|}=\sqrt{1+\frac{1}{|k|^2}}.
]
Hence:

* as (|k|\to\infty),
  [
  q_h = |k|+\frac{1}{2|k|}+O(|k|^{-3}),
  \qquad
  \frac{q_h}{|k|}\to 1,
  ]
  so the helical shift does **not** approach a fixed nonzero asymptote in units of (|k|); it asymptotically becomes negligible;
* at small (|k|), the helical partners remain gapped by the unit twist Casimir.

A small numerical table is therefore

| (|k|) | (q_0) | (q_h) | (q_h/|k|) |
|---:|---:|---:|---:|
| 1 | 1 | (\sqrt2 \approx 1.4142) | (1.4142) |
| 2 | 2 | (\sqrt5 \approx 2.2361) | (1.1180) |
| 5 | 5 | (\sqrt{26} \approx 5.0990) | (1.0198) |
| 10 | 10 | (\sqrt{101} \approx 10.0499) | (1.0050) |

So the real-basis transport matrix is indeed

[
\boxed{
\text{transport}_{VII_0}(k_1,k_3)
=================================

\operatorname{diag}!\bigl(q_0,\ q_h,\ q_h\bigr),
}
]
which is a real diagonal (3\times 3) matrix for all (k\ge 0). The (\mu_+) and (\mu_-) entries are degenerate because they are the real (\cos/\sin) decomposition of one complex helical pair. ([Physical Review Journals][1])

Finally, the Type-I limit is immediate: if the helical eigenvalue is sent to zero together with the VII(*0) structure constants, then
[
q_h \to \sqrt{k_1^2+k_3^2}=q_0=|k|,
]
so
[
\text{transport}*{VII_0}\to |k|,I_3,
]
which is exactly the isotropic Type-I transport and therefore preserves the FLRW invariant manifold and (b_{hh}\equiv0). ([ResearchGate][2])

A turn-key code expression is therefore:

```python
import numpy as np

def transport_VII0(k1: float, k3: float, twist_eigenvalue: float = 1.0) -> np.ndarray:
    q0 = float(np.sqrt(k1*k1 + k3*k3))
    qh = float(np.sqrt(k1*k1 + k3*k3 + twist_eigenvalue))
    return np.diag([q0, qh, qh])
```

---

## Q-11 — ζ_R for class-B R_μ correction

Here the exact **structure** is derivable, but the exact **numerical coefficient** (\zeta_R) is **not** uniquely closable from the prompt alone because it depends on the v5 class-B tilt closure card: specifically, one needs the precise map from species tilt amplitudes ((v_b^\alpha,v_\gamma^\alpha)) to the stored real (\mu)-basis and the normalization convention for the real partner pair. What *is* derivable without guessing is the linear species-density correction and the resulting quadratic (\mu)-diagonal correction. That follows from the (1+3) energy conservation law plus the class-B divergence identity. ([ResearchGate][3])

For a species (s) with equation-of-state parameter (w_s), linearized energy conservation in a homogeneous class-B background gives
[
\dot{\delta\rho_s} + (1+w_s)\rho_s,D_\alpha v_s^\alpha = 0.
]
Using the class-B identity quoted in the prompt,
[
D_\alpha v_s^\alpha = -a_\alpha v_s^\alpha,
]
one gets
[
\dot{\delta\rho_s}
==================

(1+w_s)\rho_s,a_\alpha v_s^\alpha.
]
On a slow background over one Hubble time (H^{-1}), the algebraic closure is therefore
[
\frac{\delta\rho_s}{\rho_s}
\approx
\frac{1+w_s}{H},a_\alpha v_s^\alpha.
]
With (a^\alpha = |a|\hat a^\alpha) and projection onto the (\mu)-axis,
[
\delta_{s,\mu}^{(1)}
====================

\frac{1+w_s}{H},|a|,v_{s,\parallel},(\hat a!\cdot e_\mu),
]
where (v_{s,\parallel}\equiv v_s^\alpha \hat a_\alpha). For baryons ((w_b=0)) and photons ((w_\gamma=\tfrac13)), this becomes

[
\boxed{
\delta_{b,\mu}^{(1)} = \frac{|a|}{H}v_{b,\parallel}(\hat a!\cdot e_\mu),
\qquad
\delta_{\gamma,\mu}^{(1)} = \frac{4|a|}{3H}v_{\gamma,\parallel}(\hat a!\cdot e_\mu).
}
]

Now
[
R_\mu^{-1}
==========

# \frac{3\rho_{b,\mu}}{4\rho_{\gamma,\mu}}

R^{-1}\frac{1+\delta_{b,\mu}}{1+\delta_{\gamma,\mu}}
]
so to first order
[
R_\mu^{-1}
==========

R^{-1}\left[
1+\left(\delta_{b,\mu}^{(1)}-\delta_{\gamma,\mu}^{(1)}\right)
\right]
+O(a^2).
]
Substituting the species results gives
[
R_\mu^{-1}
==========

R^{-1}\left[
1+\frac{|a|}{H}\Bigl(v_{b,\parallel}-\frac43 v_{\gamma,\parallel}\Bigr)(\hat a!\cdot e_\mu)
\right]
+O(a^2).
]

However, in the frozen real ((\mu_0,\mu_+,\mu_-)) storage basis the linear term is odd under partner exchange and therefore does **not** survive as a diagonal correction for the (\mu_\pm) pair. The surviving diagonal correction is quadratic:

[
\boxed{
R_\mu^{-1}
==========

R^{-1}
\left[
1+\zeta_R,|a|^2,(\hat a!\cdot e_\mu)^2 + O(|a|^4)
\right].
}
]

The structurally correct dimensionless coefficient is

[
\boxed{
\zeta_R
=======

c_{\rm rb}
\left(
\frac{v_{b,\parallel}-\tfrac43 v_{\gamma,\parallel}}{H}
\right)^2,
}
]
where (c_{\rm rb}) is a **real-basis normalization factor**:

* (c_{\rm rb}=1) if the diagonal entry is taken directly on the anchor axis;
* (c_{\rm rb}=\tfrac12) if the ((\mu_+,\mu_-)) pair is normalized as equal-weight real ((\cos,\sin)) parts of one complex helicity mode.

That last factor is the missing v5 specification. So the honest answer is:

[
\boxed{
\text{the closed algebraic form of }\zeta_R\text{ is fixed up to }c_{\rm rb},
\text{ and }c_{\rm rb}\text{ requires the class-B real-basis normalization card.}
}
]

For Type III and Type V, both have (|a|=1) and (a) aligned with axis 1, so the **structural** form is the same:
[
R_\mu^{-1,(III)}
================

R^{-1}
\begin{pmatrix}
1+\zeta_R^{(III)}[2pt]
1[2pt]
1
\end{pmatrix}
+O(a^4),
\qquad
R_\mu^{-1,(V)}
==============

R^{-1}
\begin{pmatrix}
1+\zeta_R^{(V)}[2pt]
1[2pt]
1
\end{pmatrix}
+O(a^4).
]
But (\zeta_R^{(III)}) and (\zeta_R^{(V)}) are **generically different**, because the species longitudinal tilts (v_{b,\parallel},v_{\gamma,\parallel}) evolve on different class-B backgrounds when (n\neq 0) (Type III) versus (n=0) (Type V). They coincide only in the special sublimit where those longitudinal tilt amplitudes happen to coincide. ([ResearchGate][4])

The Type-I limit is immediate: if (a=0), then (\zeta_R |a|^2=0), so
[
R_\mu^{-1} = R^{-1}(1,1,1),
]
recovering the isotropic FLRW result and preserving the (D_2) anchor. This is the non-negotiable safe limit.

A turn-key provisional code expression — explicit about its limitation — is:

```python
import numpy as np

def local_drag_by_mu_classB(R_inv: float, a_abs: float, H: float,
                            v_b_par: float, v_g_par: float,
                            c_real_basis: float = 1.0) -> np.ndarray:
    # Requires v5 class-B tilt-normalization card to fix c_real_basis.
    zeta_R = c_real_basis * ((v_b_par - (4.0/3.0)*v_g_par) / H)**2
    return R_inv * np.array([1.0 + zeta_R * a_abs*a_abs, 1.0, 1.0], dtype=float)
```

---

## Q-12 — ζ_M for class-B mass correction

Here the prompt's "(\zeta_M\cdot n_{\alpha\alpha})" ansatz is **only schematic**. The exact first-order mass drag is obtained directly from the local momentum equation, and it is the shear eigenvalue — not (n_{\alpha\alpha}) itself — that enters. The correct coefficient in front of (\sigma_{\alpha\alpha}) is exactly (1). If one insists on re-expressing (\sigma_{\alpha\alpha}) through the structure constants, then the relevant object is the anisotropic 3-Ricci tensor (^{(3)}S_{\alpha\beta}), and the coefficient depends on the background normalization; there is no universal numerical (\zeta_M) multiplying (n_{\alpha\alpha}). ([ResearchGate][3])

From the tetrad-form local momentum equation,
[
\dot v_\alpha + \frac{\Theta}{3}v_\alpha + \sigma_\alpha{}^\beta v_\beta = \text{forces} + \text{Thomson drag},
]
so in a diagonal canonical frame the coefficient multiplying the velocity component (v_\mu) is simply
[
H + \sigma_{\mu\mu},
\qquad H\equiv \Theta/3.
]
Therefore the exact relative correction is

[
\boxed{
\texttt{mass_by_mu}^{\rm rel}
=============================

1 + \frac{\sigma_{\mu\mu}}{H}.
}
]

This is the right kernel-pack quantity, because it is dimensionless and reduces to ((1,1,1)) in Type I. So the correct answer to Q-12.3/Q-12.4 is **option (b)**, not option (a):

[
\boxed{
\text{kernel pack should return the relative correction }1+\sigma_{\mu\mu}/H.
}
]

If one further imposes a slow-evolution closure from the shear propagation equation,
[
\dot\sigma_{\alpha\beta} + \Theta \sigma_{\alpha\beta} + {}^{(3)}S_{\alpha\beta} \approx 0,
]
then at lowest adiabatic order
[
\sigma_{\alpha\beta}\approx -\frac{{}^{(3)}S_{\alpha\beta}}{\Theta}
= -\frac{{}^{(3)}S_{\alpha\beta}}{3H}.
]
Hence
[
\boxed{
\texttt{mass_by_mu}^{\rm rel}
\approx
1 - \frac{{}^{(3)}S_{\mu\mu}}{3H^2}.
}
]

This is the correct structure. If you insist on writing
[
\texttt{mass_by_mu}^{\rm rel} = 1 + \zeta_M,n_{\mu\mu}^{\rm sig},
]
then (\zeta_M) is **not universal**; it is family- and normalization-dependent via (^{(3)}S_{\mu\mu}). So the honest statement is:

[
\boxed{
\zeta_M\text{ is not a single family-independent constant; the exact object is }\sigma_{\mu\mu}/H
\text{ or equivalently }-{}^{(3)}S_{\mu\mu}/(3H^2).
}
]

Qualitatively, the sign patterns the prompt wrote are the right ones if one replaces (\zeta_M) by the appropriate family-dependent (-{}^{(3)}S_{\mu\mu}/(3H^2)):

* **Type II**: one distinguished axis,
  [
  \texttt{mass_by_mu}^{(II)} = \left(1+\frac{\sigma_{11}}{H},\ 1+\frac{\sigma_{22}}{H},\ 1+\frac{\sigma_{33}}{H}\right),
  ]
  with (\sigma_{11}) the anisotropic direction.

* **Type III**:
  [
  \texttt{mass_by_mu}^{(III)} = \left(1+\frac{\sigma_{11}}{H},\ 1+\frac{\sigma_{22}}{H},\ 1+\frac{\sigma_{33}}{H}\right),
  ]
  and in canonical sign language this is the ((0,+,-)) pattern from (n=\operatorname{diag}(0,1,-1)).

* **Type V**:
  [
  \texttt{mass_by_mu}^{(V)}=(1,1,1),
  ]
  because (n=0) and there is no class-A curvature anisotropy feeding (\sigma) in the same way.

* **Type VII(_0)**:
  [
  \texttt{mass_by_mu}^{(VII_0)}=(1+\sigma_{11}/H,\ 1+\sigma_{22}/H,\ 1+\sigma_{33}/H),
  ]
  with the ((+,0,+)) / canonical ((0,+,+)) pattern depending on the projector convention of Q-15.

* **Type VIII**:
  [
  \texttt{mass_by_mu}^{(VIII)}=(1+\sigma_{11}/H,\ 1+\sigma_{22}/H,\ 1+\sigma_{33}/H),
  ]
  with the ((-,+,+)) sign pattern inherited from the semisimple canonical signature.

The Type-I limit is exact:
[
n=0,\ \sigma_{\mu\mu}=0
\quad\Longrightarrow\quad
\texttt{mass_by_mu}^{(I)}=(1,1,1).
]
So the current Round-3 Type-I placeholder is consistent **provided it is interpreted as a relative correction**.

A turn-key provisional code expression is therefore:

```python
import numpy as np

def mass_by_mu_relative(sigma_diag: np.ndarray, H: float) -> np.ndarray:
    # sigma_diag = [sigma_11, sigma_22, sigma_33] in the canonical μ-projector basis
    return 1.0 + np.asarray(sigma_diag, dtype=float) / H
```

If one wants a slow-evolution fallback in terms of (^{(3)}S_{\mu\mu}) instead:

```python
def mass_by_mu_relative_slow_background(S3_diag: np.ndarray, H: float) -> np.ndarray:
    return 1.0 - np.asarray(S3_diag, dtype=float) / (3.0 * H * H)
```

---

## Q-13 — Wigner-3j numerical table for twist_mix_kernel

The rank-1 twist insertion (a^\alpha) acts as a spin-1 spherical tensor on the spin-2 polarization tower, so the correct (\ell\to\ell\pm1) / (m\to m\pm1) kernel is

[
T^{(2)}_{a}[\ell,m;\ell',m']
============================

|a|
\sum_{q=\pm1}
a_q,
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
\ell'=\ell\pm1,
\qquad
-m + q + m' = 0
\quad\Longrightarrow\quad
m' = m-q.
]

So the prompt's (m' = m+q) wording should be corrected to
[
\boxed{m' = m - q}
]
for the (3j)-symbol convention written above. This is just the standard selection rule (m_1+m_2+m_3=0). The angular-momentum literature and standard Condon–Shortley convention support this exactly. ([BibBase][5])

For the second (3j) factor, the prompt already gave the closed forms:

[
\begin{pmatrix}
\ell & 1 & \ell+1\
-2 & 0 & 2
\end{pmatrix}
=============

(-1)^{\ell-2}
\sqrt{\frac{(\ell-1)(\ell+3)}{(2\ell+1)(2\ell+2)(2\ell+3)}},
]

[
\begin{pmatrix}
\ell & 1 & \ell-1\
-2 & 0 & 2
\end{pmatrix}
=============

(-1)^{\ell-1}
\sqrt{\frac{(\ell-2)(\ell+2)}{(2\ell-1)(2\ell)(2\ell+1)}},
]
and these vanish automatically for (\ell<2). The remaining ((\ell,m))-dependent (3j) can be computed exactly by `sympy.physics.wigner.wigner_3j`, which is the cleanest turn-key implementation. ([BibBase][5])

### Spherical-tensor convention

I adopt the Condon–Shortley / Racah convention
[
a_0=a_z,\qquad
a_{\pm1}=\mp\frac{a_x\pm i a_y}{\sqrt2}.
]
For the canonical real class-B twist axis (a^\alpha = |a|,\delta^\alpha_1 = |a|,e_x), this gives

[
\boxed{
a_0 = 0,\qquad
a_{+1} = -\frac{|a|}{\sqrt2},\qquad
a_{-1} = +\frac{|a|}{\sqrt2}.
}
]

That is exactly the real-basis convention stated in the prompt, and it ensures that the resulting kernel is real once the complex helicity pair is decomposed into the real ((\cos,\sin)) storage basis. The final (2\times2) structure is carried by the ((\Delta\ell,\Delta m)) axes of the stored kernel and then multiplied by the fixed (E/B) parity matrix in the assembly step. ([BibBase][5])

### Turn-key Python generator

A direct drop-in generator for
[
\texttt{twist_mix_kernel}[\ell,m_{\rm off},\Delta\ell{\rm_index},\Delta m{\rm_index}]
]
is:

```python
import numpy as np
from sympy import N, sqrt
from sympy.physics.wigner import wigner_3j

# delta_ell_index: 0 -> Δℓ = -1, 1 -> Δℓ = +1
# delta_m_index:   0 -> Δm = -1, 1 -> Δm = +1
# selection rule: m' = m + Δm = m - q, so q = -Δm

def build_twist_mix_kernel(ell_max: int, a_abs: float) -> np.ndarray:
    K = np.zeros((ell_max + 1, 2 * ell_max + 1, 2, 2), dtype=float)

    # Condon-Shortley spherical components for a = a_abs * e_x
    a_q = {+1: -a_abs / np.sqrt(2.0), -1: +a_abs / np.sqrt(2.0)}

    for ell in range(2, ell_max + 1):
        for m in range(-ell, ell + 1):
            m_off = m + ell_max

            for dli, d_ell in enumerate((-1, +1)):
                ellp = ell + d_ell
                if ellp < 1:
                    continue

                for dmi, d_m in enumerate((-1, +1)):
                    q = -d_m
                    mp = m + d_m
                    if abs(mp) > ellp:
                        continue

                    val = (
                        a_q[q]
                        * ((-1) ** m)
                        * np.sqrt((2 * ell + 1) * (2 * ellp + 1))
                        * float(N(wigner_3j(ell, 1, ellp, -m, q, mp)))
                        * float(N(wigner_3j(ell, 1, ellp, -2, 0, 2)))
                    )
                    K[ell, m_off, dli, dmi] = val

    return K
```

This is the correct turn-key table generator. It already carries the overall (|a|) factor, so the Type-I limit is automatic:

[
|a|=0 \quad\Longrightarrow\quad \texttt{twist_mix_kernel}\equiv 0.
]

That proves Q-13.4 immediately.

### Small (\ell=2) check block

For (\ell=2), the only nonzero transitions are to (\ell'=3). For (m=0) one finds
[
K_{2,0}^{(\Delta\ell=+1,\Delta m=-1)}=+\frac{1}{\sqrt{21}},|a|,
\qquad
K_{2,0}^{(\Delta\ell=+1,\Delta m=+1)}=-\frac{1}{\sqrt{21}},|a|.
]
This is a useful sign/phase sanity check for the Condon–Shortley convention above.

---

## Q-14 — Sector similarity S_{e,b,ν} confirmation

### Q-14.1

**Confirmed:** in the frozen BASS storage basis with uniform real (\mu)-normalization, the (\mu)-space family kernel is channel-agnostic:

[
\boxed{
\mu\texttt{_mode_coupling}_{t}
==============================

# \mu\texttt{_mode_coupling}_{e}

# \mu\texttt{_mode_coupling}_{b}

# \mu\texttt{_mode_coupling}_{\nu}

N_{\rm family}+|a|P_a.
}
]

The reason is exactly the one stated in the prompt: all channel dependence lives at the ((\ell,m)) slot level through
[
d^{(X)}_\ell,\qquad \texttt{pstf_weight}(\ell),
]
and the (T/E/B/\nu) storage basis is already real and uniformly normalized in (\mu)-space. The (\mu)-space matrix is therefore a family-geometry object, not a channel object. This is consistent with the covariant PSTF hierarchy and with the usual (E/B) decomposition in which spin-2 structure is carried by the angular/tower basis rather than by a separate family-space similarity. ([ScienceDirect][6])

So for the five Tier-A families (II,III,V,VII_0,VIII), there is **no** additional (\mu)-space similarity transform between (T,E,B,\nu).

### Q-14.2

Because the answer to Q-14.1 is "identity," there is no nontrivial (S_E,S_B,S_\nu) to derive. If one insisted on introducing one, it would be
[
S_E=S_B=S_\nu=I_3.
]

### Q-14.3

So the final confirmation is:

[
\boxed{
S_{e,b,\nu}=I_3
}
]
in the frozen BASS storage basis.

This is supported by the stated convention that the (\ell)-dependent PSTF and spin-2 normalization is carried slot-wise, not (\mu)-wise, and therefore the family-conditioned (\mu)-kernel is common across channels.

---

## Q-15 — Π_μ^α projector confirmation

The generic proposal
[
\Pi_\mu{}^\alpha = \texttt{axis_permutation}
]
is **not sufficient as a universal rule**. For some families it works, but for VII(_0) in particular it does not put the unique anchor eigenvalue into (\mu_0). So the right answer is: use a **family-specific mode-basis permutation table**, not one global class-A/class-B rule. The Bianchi classification data and the canonical (n)-signatures support exactly this kind of per-family choice. ([SciPost][7])

We require
[
\Pi,\operatorname{diag}(n),\Pi^T = N_{\rm canonical},
]
with (N_{\rm canonical}) the Round-3 target signature.

### Type II

Code:
[
n_{\rm code}=\operatorname{diag}(1,0,0),
\qquad
N_{\rm canonical}=\operatorname{diag}(1,0,0).
]
So
[
\boxed{
\Pi_{II}=I_3.
}
]

### Type III

Code:
[
n_{\rm code}=\operatorname{diag}(0,1,-1),
\qquad
N_{\rm canonical}=\operatorname{diag}(0,1,-1).
]
The zero eigenvalue is already on axis 1 and (a) is already on the same axis. So

[
\boxed{
\Pi_{III}=I_3.
}
]

The existing generic class-B swap ((1,0,2)) would send ((0,1,-1)) to ((1,0,-1)), which is **not** the desired canonical signature. So the stored class-B generic permutation must **not** be used blindly for the kernel pack.

### Type V

Here (n=0), so (N_{\rm canonical}=0) regardless of permutation. However the twist projector (P_a) must place the twist axis on (\mu_0). Since the code already stores (a) along axis 1, the correct choice is

[
\boxed{
\Pi_V = I_3.
}
]

### Type VII(_0)

Code:
[
n_{\rm code}=\operatorname{diag}(1,0,1),
]
while the Round-3 canonical signature is
[
N_{\rm canonical}=\operatorname{diag}(0,1,1).
]

So we must move the **unique zero eigenvalue** to the anchor slot (\mu_0). The needed permutation is the swap of axes 0 and 1:

[
\boxed{
\Pi_{VII_0}
===========

\begin{pmatrix}
0&1&0\
1&0&0\
0&0&1
\end{pmatrix}.
}
]

Indeed,
[
\Pi_{VII_0},\operatorname{diag}(1,0,1),\Pi_{VII_0}^T
====================================================

\operatorname{diag}(0,1,1).
]

This is the required answer to Q-15.2.

Because the two positive eigenvalues are degenerate, the choice of (\mu_+) and (\mu_-) inside that 2D subspace is not unique mathematically. The frozen **canonical convention** should therefore be:

1. assign (\mu_0) to the unique anchor / zero-eigenvalue axis;
2. assign (\mu_+) to the lower code-axis index in the remaining degenerate subspace;
3. assign (\mu_-) to the higher code-axis index.

For VII(*0), that means
[
\mu_0 \leftarrow \text{axis 1 (zero)},
\qquad
\mu*+ \leftarrow \text{axis 0},
\qquad
\mu_- \leftarrow \text{axis 2}.
]

### Type VIII

Code:
[
n_{\rm code}=\operatorname{diag}(-1,1,1),
\qquad
N_{\rm canonical}=\operatorname{diag}(-1,1,1).
]
So
[
\boxed{
\Pi_{VIII}=I_3.
}
]

### Final table

[
\boxed{
\Pi_{II}=
\begin{pmatrix}
1&0&0\0&1&0\0&0&1
\end{pmatrix},\quad
\Pi_{III}=
\begin{pmatrix}
1&0&0\0&1&0\0&0&1
\end{pmatrix},\quad
\Pi_{V}=
\begin{pmatrix}
1&0&0\0&1&0\0&0&1
\end{pmatrix},
}
]

[
\boxed{
\Pi_{VII_0}=
\begin{pmatrix}
0&1&0\1&0&0\0&0&1
\end{pmatrix},\quad
\Pi_{VIII}=
\begin{pmatrix}
1&0&0\0&1&0\0&0&1
\end{pmatrix}.
}
]

So the generic stored `axis_permutation` is **not** sufficient; the kernel pack needs a dedicated per-family (\Pi_\mu{}^\alpha) table, and VII(_0) is the nontrivial case among the five requested families.

### Type-I limit check

For Type I, (n=0) and (a=0), so any permutation is irrelevant. The kernel-pack matrices vanish, the diagonal vectors reduce to ones, and the transport reduces to isotropic (|k|I_3). Therefore the FLRW (D_2) anchor remains protected.

[1]: https://journals.aps.org/prd/abstract/10.1103/PhysRevD.79.103518 "https://journals.aps.org/prd/abstract/10.1103/PhysRevD.79.103518"
[2]: https://www.researchgate.net/publication/233982277_Explicit_harmonic_and_spectral_analysis_in_Bianchi_I-VII_type_cosmologies "https://www.researchgate.net/publication/233982277_Explicit_harmonic_and_spectral_analysis_in_Bianchi_I-VII_type_cosmologies"
[3]: https://www.researchgate.net/publication/1977532_Cosmological_models_Cargese_lectures_1998 "https://www.researchgate.net/publication/1977532_Cosmological_models_Cargese_lectures_1998"
[4]: https://www.researchgate.net/publication/1968519_A_dynamical_systems_approach_to_the_tilted_Bianchi_models_of_solvable_type "https://www.researchgate.net/publication/1968519_A_dynamical_systems_approach_to_the_tilted_Bianchi_models_of_solvable_type"
[5]: https://bibbase.org/network/publication/edmonds-angularmomentuminquantummechanics-2016 "https://bibbase.org/network/publication/edmonds-angularmomentuminquantummechanics-2016"
[6]: https://www.sciencedirect.com/science/article/pii/S0003491600960330 "https://www.sciencedirect.com/science/article/pii/S0003491600960330"
[7]: https://scipost.org/SciPostPhysLectNotes.73/pdf "https://scipost.org/SciPostPhysLectNotes.73/pdf
