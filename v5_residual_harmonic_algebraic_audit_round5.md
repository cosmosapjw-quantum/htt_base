## Q-16 — VER2 gauge identification

For the **FLRW / Bianchi-I orthogonal** limit, the clean answer is:

[
\boxed{\Theta_\ell^{\mathrm{VER2}}=\Theta_\ell^{\mathrm{MB}}\qquad\text{for all }\ell\ge 0}
]

provided the preferred 4-velocity (u^a) in the (1+3) covariant PSTF construction is the same physical observer congruence used by the FLRW extractor route, namely the orthogonal/fundamental FLRW congruence. In that case the PSTF intensity multipoles are just the gauge-invariant covariant realization of the standard scalar brightness multipoles, and there is **no extra (\alpha(\ell))** or metric-correction coefficient to insert by hand. The point of the covariant formalism is precisely that, once (u^a) is fixed, the radiation multipoles are physical observables relative to that congruence; around FRW, the higher multipoles are gauge-invariant and the mode-form hierarchy matches the standard line-of-sight hierarchy used in MB/Seljak–Zaldarriaga. ([ScienceDirect][1])

The one subtlety is (\ell=0). In general, the monopole is not Stewart–Walker gauge-invariant the way (\ell\ge1) multipoles are. But here the extractor is **not** trying to convert from an arbitrary synchronous variable into Newtonian gauge. It is using the same fundamental observer field (u^a) that the Tier-B FLRW/orthogonal route already uses to define the PSTF moments. Under that identification, the stored monopole is the same temperature monopole that enters (\delta_\gamma = 4\Theta_0), so for the extractor route it is consistent to take
[
\Theta_0^{\mathrm{VER2}}=\Theta_0^{\mathrm{MB}}.
]
If at some later point VER2 changes its fundamental frame or stores matter variables in a different gauge, then the MB §5 gauge transformation
[
\delta^{(N)}=\delta^{(S)}+3(1+w)\mathcal H \alpha,\qquad
\theta^{(N)}=\theta^{(S)}+k^2\alpha
]
would need to be inserted. But **for the present FLRW/Bianchi-I orthogonal extractor path, no such correction is needed**. ([Springer][2])

So the practical identification is simply:

[
\Theta_\ell(\eta,k)
===================

\texttt{photon_T_tower}[\eta,\mathrm{slot}(\ell,0)]
]

for the scalar (m=0) channel in the FLRW extractor.

---

## Q-17 — (\Psi(\eta,k)) extraction from VER2 state

### Q-17.1 — density extraction formulas

Using the slot dictionary you supplied for the local blocks, the correct extractions are:

[
\delta_b(\eta,k)=\texttt{baryon_local_history}[:,0],
\qquad
v_b(\eta,k)=\texttt{baryon_local_history}[:,1],
]
[
\delta_c(\eta,k)=\texttt{cdm_local_history}[:,0],
\qquad
v_c(\eta,k)=\texttt{cdm_local_history}[:,1].
]

I accept these **directly** as the Newtonian-gauge-style density and velocity variables used by the extractor route, because your own slot audit fixes slot 1 as the MB-style peculiar velocity entering the tight-coupling slip (3\Theta_1-v_b), and that is exactly the MB convention in which (v_b=\theta_b/k) and tight coupling gives (v_b=3\Theta_1). So for the present Round-5 extractor, no extra gauge-conversion coefficient is required on the local baryon/CDM slots. If that assumption is ever invalidated, the MB §5 synchronous-to-Newtonian formulas above are the correct repair path. ([Springer][2])

For photons and neutrinos, the correct scalar-monopole extraction is

[
\delta_\gamma = 4\Theta_0^\gamma,
\qquad
\Theta_0^\gamma = \texttt{photon_T_tower}[:,\mathrm{slot}(0,0)],
]
[
\delta_\nu = 4\Theta_0^\nu,
\qquad
\Theta_0^\nu = \texttt{neutrino_tower}[:,\mathrm{slot}(0,0)].
]

There is **no additional PSTF prefactor** at (\ell=0). The row-weight (d_\ell^{(X)}) bookkeeping controls evolution-operator normalization, not the physical identification of the stored scalar monopole with (\Theta_0). So the familiar radiation relation (\delta_r=4\Theta_0) holds exactly in the present storage convention. ([ScienceDirect][1])

Likewise, the radiation velocities are

[
v_\gamma = 3\Theta_1^\gamma
= 3,\texttt{photon_T_tower}[:,\mathrm{slot}(1,0)],
]
[
v_\nu = 3\Theta_1^\nu
= 3,\texttt{neutrino_tower}[:,\mathrm{slot}(1,0)],
]
because MB's (\theta_r=3k\Theta_1) and the stored (v)-type variables are (v=\theta/k). ([Springer][2])

### Q-17.2 — closed-form (\Psi(k,\eta))

For conformal Newtonian gauge, the Einstein constraint equations can be written as

[
k^2\Phi + 3\mathcal H\left(\Phi'+\mathcal H\Psi\right)=4\pi G a^2 \delta\rho,
]
[
k^2\left(\Phi'+\mathcal H\Psi\right)=4\pi G a^2 (\bar\rho+\bar p)\theta,
]
and, with anisotropic stress,
[
\Psi-\Phi
=========

\frac{12\pi G a^2}{k^2}(\bar\rho+\bar p)\sigma_{\rm tot},
]
using the sign convention in your prompt. Combining the first two gives

[
\Phi
====

\frac{4\pi G a^2}{k^2}
\left[
\delta\rho
----------

3\mathcal H,\frac{(\bar\rho+\bar p)\theta}{k^2}
\right].
]

Since (\theta_i = k v_i), this is

[
\Phi
====

\frac{4\pi G a^2}{k^2}
\left[
\delta\rho
----------

3\mathcal H,\frac{\sum_i (\bar\rho_i+\bar p_i) v_i}{k}
\right].
]

Then

[
\Psi
====

\Phi
+
\frac{12\pi G a^2}{k^2}(\bar\rho+\bar p)\sigma_{\rm tot}.
]

So the closed-form extractor is

[
\boxed{
\Psi(k,\eta)=
\frac{4\pi G a^2}{k^2}
\left[
\delta\rho_{\rm tot}
--------------------

3\mathcal H,\frac{\sum_i(\bar\rho_i+\bar p_i)v_i}{k}
+
3(\bar\rho+\bar p)\sigma_{\rm tot}
\right].
}
]

The required VER2 ingredients are therefore:

[
\delta\rho_{\rm tot}
====================

\bar\rho_b\delta_b+\bar\rho_c\delta_c+\bar\rho_\gamma\delta_\gamma+\bar\rho_\nu\delta_\nu,
]

[
\sum_i(\bar\rho_i+\bar p_i)v_i
==============================

\bar\rho_b v_b + \bar\rho_c v_c + \frac43\bar\rho_\gamma v_\gamma + \frac43\bar\rho_\nu v_\nu,
]

and

[
(\bar\rho+\bar p)\sigma_{\rm tot}
=================================

\frac43\bar\rho_\gamma \sigma_\gamma + \frac43\bar\rho_\nu \sigma_\nu.
]

Now, in MB normalization (F_{r2}=2\sigma_r) and (F_{r2}=4\Theta_{2,r}), so

[
\sigma_\gamma = 2\Theta_2^\gamma,
\qquad
\sigma_\nu = 2\Theta_2^\nu.
]

Therefore

[
(\bar\rho+\bar p)\sigma_{\rm tot}
=================================

\frac{8}{3}\bar\rho_\gamma\Theta_2^\gamma
+
\frac{8}{3}\bar\rho_\nu\Theta_2^\nu.
]

A crucial correction to the wording in your prompt: the Einstein anisotropic-stress correction depends on the **intensity quadrupoles** (\Theta_2^\gamma,\Theta_2^\nu), **not** directly on the polarization source (\Pi=\Theta_2-\sqrt6 E_2). (\Pi) enters the photon **collision/source** term, but the metric slip (\Psi-\Phi) is sourced by the stress-energy tensor, i.e. by intensity anisotropic stress. ([Springer][2])

### Required missing input

The exact formula above needs the background species densities (\bar\rho_b(\eta),\bar\rho_c(\eta),\bar\rho_\gamma(\eta),\bar\rho_\nu(\eta)). The schema excerpt for `BackgroundEvolutionResult` only exposes total (\rho,p), not the species components. So the **minimum additional requirement** for a compile-ready extractor is that either

1. `background_monitor` expose the four species density histories directly, or
2. `integration_result.config` expose enough cosmology to reconstruct them from (a(\eta)).

Without that, (\delta\rho_{\rm tot}) and ((\rho+p)\sigma_{\rm tot}) cannot be formed exactly. That is the one genuine missing documentary bridge here.

### Q-17.3 — MD limit check

In matter domination,
[
\bar\rho_m\propto a^{-3},\qquad \delta_m\propto a,
]
so
[
a^2 \bar\rho_m \delta_m \propto a^2\cdot a^{-3}\cdot a = \text{const}.
]
Also (\sigma_{\rm tot}\to 0) and radiation becomes negligible. Therefore
[
\Psi = \text{const},\qquad \Phi=\text{const},
]
so the extractor formula reduces to the canonical MD result. This is exactly the desired limit. ([Springer][2])

### Q-17.4 — small-(k) stability

The **subhorizon Poisson approximation**
[
\Psi \approx -\frac{3\mathcal H^2}{2k^2}\delta_{\rm tot}
]
breaks down when (k^2\lesssim \mathcal H^2). The full combined Einstein-constraint expression above is the correct all-scale formula. However it still contains an explicit (1/k^2), so numerically it becomes cancellation-sensitive as (k\to 0), because the bracket scales like (k^2) on adiabatic superhorizon modes. Therefore the extraction should be treated as reliable without special regularization only for
[
k/\mathcal H \gtrsim 1.
]
For modes with (k/\mathcal H\ll 1), a compensated evaluation or superhorizon series regularization is needed. The physics is regular; the numerical issue is cancellation, not a true divergence. ([Springer][2])

---

## Q-18 — (\dot\Phi+\dot\Psi) ISW driver

### Q-18.1 — decomposition

Using the prompt's convention
[
\Psi-\Phi = \frac{12\pi G a^2}{k^2}(\bar\rho+\bar p)\sigma_{\rm tot},
]
we have
[
\Phi+\Psi = 2\Psi - (\Psi-\Phi).
]
Therefore
[
\boxed{
\Phi' + \Psi'
=============

## 2\Psi'

\frac{12\pi G}{k^2}\frac{d}{d\eta}\left[a^2(\bar\rho+\bar p)\sigma_{\rm tot}\right].
}
]

With VER2 fields,
[
(\bar\rho+\bar p)\sigma_{\rm tot}
=================================

\frac{8}{3}\bar\rho_\gamma\Theta_2^\gamma
+
\frac{8}{3}\bar\rho_\nu\Theta_2^\nu.
]

So the ISW driver is

[
\boxed{
\Phi' + \Psi'
=============

## 2\Psi'

\frac{32\pi G}{k^2}\frac{d}{d\eta}\left[
a^2\left(\bar\rho_\gamma\Theta_2^\gamma+\bar\rho_\nu\Theta_2^\nu\right)
\right].
}
]

Again, (\Pi=\Theta_2-\sqrt6E_2) is **not** the Einstein anisotropic stress by itself. It enters the Thomson source; the metric slip uses the intensity quadrupoles. ([Springer][2])

### Q-18.2 — differentiation strategy

I recommend **(a)**: compute (\Psi(\eta)) (and (\Phi(\eta)), or equivalently the slip term) on the full stored (\eta)-grid, then differentiate numerically with

* 4th-order centered finite differences in the bulk,
* 2nd-order one-sided finite differences on the two boundaries.

Reason: the direct evolution-equation route would require additional explicitly stored Einstein-evolution variables and/or pressure-perturbation closures not present in the schema excerpt. The finite-difference route uses only quantities already available or already required by Q-17, and it keeps the extractor modular. With a smooth conformal-time grid and no extrapolation, this is the least assumption-heavy route. ([Science Explorer][3])

### Q-18.3 — MD limit

In matter domination,
[
\Psi' = 0,\qquad \sigma_{\rm tot}=0,
]
hence
[
\Phi'+\Psi' = 0.
]
So the formula reduces exactly to zero in the MD limit, as it should. ISW turns on only when the potential evolves, i.e. during radiation domination, dark-energy domination, or any epoch with non-negligible anisotropic stress. ([Springer][2])

---

## Q-19 — (v_b(\eta,k)) slot + (k) normalization

### Q-19.1 — slot identification

Using your direct code note, the exact dictionary is:

For `baryon_local_history` (shape `(N_eta, 4)`):

* slot 0: (\delta_b)
* slot 1: (v_b)
* slot 2: duplicate of slot 1, i.e. another stored copy of (v_b) (legacy / covered-mode buffer)
* slot 3: (3\Theta_1^\gamma - v_b) (photon–baryon slip)

For `cdm_local_history` (shape `(N_eta, 2)`):

* slot 0: (\delta_c)
* slot 1: (v_c)

So the extractor should use

[
\boxed{
\delta_b = \texttt{baryon_local_history}[:,0],\quad
v_b = \texttt{baryon_local_history}[:,1],\quad
\delta_c = \texttt{cdm_local_history}[:,0],\quad
v_c = \texttt{cdm_local_history}[:,1].
}
]

### Q-19.2 — (k)-normalization

Per your note, all local components are stored at the **solver's actual (k)** for the current Tier-B run, i.e. the `k_grid_mpc` value used by `execute_tier_b_solver`. Therefore (v_b(\eta,k)) is **not** a transfer function normalized to (k=1); it is the actual mode amplitude at the requested (k).

### Q-19.3 — sign convention

Again following your code note and the MB fluid equations, the stored (v_b) is the peculiar-velocity scalar obeying
[
\theta_b = k,v_b.
]
So (v_b) is the MB-style scalar velocity potential, not (-ik) times a vector component. That is exactly why the slip variable
[
3\Theta_1^\gamma - v_b
]
vanishes in tight coupling: MB gives (\theta_\gamma = 3k\Theta_1), so (v_\gamma = \theta_\gamma/k = 3\Theta_1). ([Springer][2])

### Q-19.4 — equality-era verification

Under the "no code execution" constraint I cannot numerically verify this. Algebraically, though, tight coupling implies
[
v_b \simeq v_\gamma = 3\Theta_1^\gamma
]
for (\eta\ll\eta_*), and around equality the two should still track closely until decoupling. So the verification condition you should check in code is

[
\left|\frac{v_b(\eta_{\rm eq}) - 3\Theta_1^\gamma(\eta_{\rm eq})}{v_b(\eta_{\rm eq})}\right| \ll 1.
]

That is the correct diagnostic.

---

## Q-20 — (\Pi = \Theta_2 - \sqrt6 E_2) PSTF prefactor check

### Q-20.1 — prefactor

Given the Round-1/2 operator fixes and the frozen VER2 storage convention, the correct source combination is

[
\boxed{
\Pi(\eta)
=========

# \Theta_2(\eta) - \sqrt6,E_2(\eta)

## \texttt{photon_T_tower}[:,\mathrm{slot}(2,0)]

\sqrt6,
\texttt{photon_E_tower}[:,\mathrm{slot}(2,0)]
}
]

**as written**, with no extra PSTF prefactor.

The reason is algebraic: the Tier-B operator patches already imposed the Thomson quadrupole block in the stored variables so that the collision/source structure matches the KKS/ZS form. If one inserted an extra (\alpha_T,\alpha_E) here, one would immediately break that consistency. The (\ell)-dependent PSTF row weights (d_\ell^{(X)}) belong to the evolution-operator normalization; they do not introduce an extra source-prefactor at extraction time. ([Physical Review Journals][4])

### Q-20.2 — exact formula

Therefore
[
\boxed{\alpha_T = 1,\qquad \alpha_E = -\sqrt6.}
]

### Q-20.3 — sign convention

Yes, the sign is correct:

[
\Pi = \Theta_2 - \sqrt6 E_2,
]
and the LoS source uses
[
S_T \supset +\frac14 \Pi,\qquad
S_E \supset -\frac{\sqrt6}{4}\Pi.
]

This is exactly the standard scalar-polarization source structure in the KKS / Zaldarriaga–Seljak normalization. ([Physical Review Journals][4])

### Q-20.4 — pre-recombination limit

Under the no-code-execution rule I cannot numerically verify the limit, but algebraically in tight coupling one has
[
\Theta_2 = O(\tau_c),\qquad E_2 = O(\tau_c),
]
so
[
\Pi = O(\tau_c)\to 0
]
as (\tau_c\to 0) before recombination. This is the standard tight-coupling behavior and is fully consistent with your stored slip diagnostic and the quadrupole-only source structure. ([MDPI][5])

---

## Q-21 — `extract_flrw_sources_from_tier_b` signature + verification

### Q-21.1 — turn-key pseudocode

Below is the exact pseudocode I recommend. It is "turn-key" except for one clearly marked required helper: the background species-density histories (\rho_b,\rho_c,\rho_\gamma,\rho_\nu). Those are mathematically required by Q-17 and must be exposed either by `background_monitor` or by `integration_result.config`.

```python
import numpy as np
from scipy.interpolate import PchipInterpolator
from dataclasses import dataclass

@dataclass(frozen=True)
class FLRWSourceTerms:
    theta_0: callable
    psi: callable
    phi_dot_plus_psi_dot: callable
    v_b: callable
    pi: callable

def _slot(l: int, m: int) -> int:
    return l * l + (m + l)

def _fd4_uniform_like(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    # 4th-order centered in the bulk, 2nd-order one-sided at the boundaries.
    dydx = np.zeros_like(y, dtype=float)
    n = len(x)
    # boundaries: 2nd-order
    dydx[0]  = (-3*y[0] + 4*y[1] - y[2]) / (x[2] - x[0])
    dydx[1]  = (y[2] - y[0]) / (x[2] - x[0])
    dydx[-2] = (y[-1] - y[-3]) / (x[-1] - x[-3])
    dydx[-1] = (3*y[-1] - 4*y[-2] + y[-3]) / (x[-1] - x[-3])
    # bulk: 4th-order centered
    for i in range(2, n-2):
        h = (x[i+1] - x[i-1]) / 2.0
        dydx[i] = (-y[i+2] + 8*y[i+1] - 8*y[i-1] + y[i-2]) / (12.0*h)
    return dydx

def _require_species_background_densities(background_monitor, integration_result):
    # REQUIRED documentary bridge:
    # must return rho_b, rho_c, rho_g, rho_nu arrays on the same eta grid.
    # This cannot be guessed from total rho/p alone.
    raise NotImplementedError(
        "Need species background densities {rho_b, rho_c, rho_g, rho_nu} "
        "from background_monitor or config."
    )

def extract_flrw_sources_from_tier_b(
    integration_result,
    background_monitor,
    k: float,
    *,
    anisotropic_stress: bool = True,
) -> FLRWSourceTerms:

    eta = np.asarray(background_monitor.eta, dtype=float)
    a   = np.asarray(background_monitor.a, dtype=float)
    Hc  = np.asarray(background_monitor.H, dtype=float)  # conformal Hubble 𝓗

    # scalar temperature / polarization multipoles (m=0)
    theta0_g = np.asarray(integration_result.photon_T_tower[:, _slot(0, 0)], dtype=float)
    theta1_g = np.asarray(integration_result.photon_T_tower[:, _slot(1, 0)], dtype=float)
    theta2_g = np.asarray(integration_result.photon_T_tower[:, _slot(2, 0)], dtype=float)
    e2_g     = np.asarray(integration_result.photon_E_tower[:, _slot(2, 0)], dtype=float)

    theta0_nu = np.asarray(integration_result.neutrino_tower[:, _slot(0, 0)], dtype=float)
    theta1_nu = np.asarray(integration_result.neutrino_tower[:, _slot(1, 0)], dtype=float)
    theta2_nu = np.asarray(integration_result.neutrino_tower[:, _slot(2, 0)], dtype=float)

    # Π = Θ2 - sqrt(6) E2  (no extra PSTF prefactor in frozen VER2 convention)
    Pi = theta2_g - np.sqrt(6.0) * e2_g

    # local matter slots
    delta_b = np.asarray(integration_result.baryon_local_history[:, 0], dtype=float)
    vb      = np.asarray(integration_result.baryon_local_history[:, 1], dtype=float)
    delta_c = np.asarray(integration_result.cdm_local_history[:, 0], dtype=float)
    vc      = np.asarray(integration_result.cdm_local_history[:, 1], dtype=float)

    # radiation velocities in MB convention: v = theta/k, theta = 3 k Θ1
    vg  = 3.0 * theta1_g
    vnu = 3.0 * theta1_nu

    # REQUIRED species background densities
    rho_b, rho_c, rho_g, rho_nu = _require_species_background_densities(
        background_monitor, integration_result
    )

    # density contrasts
    delta_g  = 4.0 * theta0_g
    delta_nu = 4.0 * theta0_nu

    # total density perturbation
    delta_rho = rho_b * delta_b + rho_c * delta_c + rho_g * delta_g + rho_nu * delta_nu

    # total momentum density: sum_i (rho_i + p_i) v_i
    mom = (
        rho_b * vb
        + rho_c * vc
        + (4.0 / 3.0) * rho_g * vg
        + (4.0 / 3.0) * rho_nu * vnu
    )

    # anisotropic stress from intensity quadrupoles only
    stress = (8.0 / 3.0) * rho_g * theta2_g + (8.0 / 3.0) * rho_nu * theta2_nu

    G = integration_result.config.newton_G  # must be exposed in config or module constants

    # Einstein constraints:
    # Φ = (4πGa²/k²) [δρ - 3𝓗 * mom / k]
    phi = (4.0 * np.pi * G * a * a / (k * k)) * (delta_rho - 3.0 * Hc * mom / k)

    if anisotropic_stress:
        psi_minus_phi = (12.0 * np.pi * G * a * a / (k * k)) * stress
    else:
        psi_minus_phi = np.zeros_like(phi)

    psi = phi + psi_minus_phi

    # ISW driver via numerical differentiation on full eta grid
    phi_plus_psi = phi + psi
    phi_dot_plus_psi_dot = _fd4_uniform_like(eta, phi_plus_psi)

    # No extrapolation outside eta-domain
    theta0_itp = PchipInterpolator(eta, theta0_g, extrapolate=False)
    psi_itp    = PchipInterpolator(eta, psi, extrapolate=False)
    isw_itp    = PchipInterpolator(eta, phi_dot_plus_psi_dot, extrapolate=False)
    vb_itp     = PchipInterpolator(eta, vb, extrapolate=False)
    pi_itp     = PchipInterpolator(eta, Pi, extrapolate=False)

    return FLRWSourceTerms(
        theta_0=theta0_itp,
        psi=psi_itp,
        phi_dot_plus_psi_dot=isw_itp,
        v_b=vb_itp,
        pi=pi_itp,
    )
```

This uses **PCHIP** rather than unconstrained cubic splines, because PCHIP is monotone/shape-preserving and much less likely to ring near recombination features. No extrapolation is permitted, satisfying your constraint.

### Q-21.2 — verification against (D_2)

Under the no-code-execution constraint I cannot numerically compute the resulting (D_2). The correct verification protocol is:

1. build `FLRWSourceTerms` with the extractor above at each (k);
2. feed them to the existing isotropic LoS projector;
3. assemble (C_\ell^{TT}) with the usual (k)-grid and primordial spectrum;
4. compute (D_2 = \ell(\ell+1) C_\ell /(2\pi)) at (\ell=2).

Acceptance criterion:

[
\boxed{
\left|\frac{D_2^{\rm extractor}-1002.086744}{1002.086744}\right|
\le 10^{-3}
}
]

i.e. within the expected (k)-grid quadrature error. Anything larger is almost certainly a bug in Q-16, Q-17, or Q-20.

### Q-21.3 — anisotropic-stress off/on toggle

With `anisotropic_stress=False`, the extractor sets
[
\Psi-\Phi = 0,\qquad \Phi=\Psi,
]
so the source becomes the standard SW + Doppler + ISW form with no stress correction:
[
S_T = g\left[\Theta_0 + \Psi + \frac14\Pi\right] + e^{-\kappa}(\Phi'+\Psi') + \frac{d}{d\eta}(g v_b),
]
but with (\Psi) coming from the full Einstein constraint rather than the toy MD (-3\zeta/5) relation. In the sharp-visibility / MD limit this should reproduce the physical SW plateau at the percent level. Under the no-code-execution rule I cannot numerically confirm the (1%) target, but that is the correct verification threshold.

### Q-21.4 — computational cost and (k)-dependence

At fixed (k), all five callables are genuinely (k)-dependent because the hierarchy solution itself is (k)-dependent. The only weak simplification is the explicit (1/k^2) factor in (\Psi), but the numerator
[
\delta\rho - 3\mathcal H,\frac{\sum_i(\rho_i+p_i)v_i}{k} + 3(\rho+p)\sigma
]
is also (k)-dependent, so you cannot safely precompute (\Psi) at one (k) and rescale it as (1/k^2) except perhaps in a strictly superhorizon asymptotic regime — and that would violate the "no toy SW approximation" rule for the main extractor path. So for the real path, treat all five callables as **full per-(k)** outputs. The safe acceleration strategy is not (k)-rescaling but reduced (k)-grid interpolation **after** verifying smoothness of the assembled transfer functions.

So the clean answer is:

[
\boxed{
\text{No, none of the five callables is generically safe to reuse across }k
\text{ by a simple analytic rescaling in the production path.}
}
]

That is the physically conservative answer consistent with your approximation-free constraint.

[1]: https://www.sciencedirect.com/science/article/abs/pii/S0003491600960342 "https://www.sciencedirect.com/science/article/abs/pii/S0003491600960342"
[2]: https://link.springer.com/article/10.1140/epjc/s10052-025-14208-8 "https://link.springer.com/article/10.1140/epjc/s10052-025-14208-8"
[3]: https://scixplorer.org/abs/1996ApJ...469..437S/abstract "https://scixplorer.org/abs/1996ApJ...469..437S/abstract"
[4]: https://journals.aps.org/prd/abstract/10.1103/PhysRevD.55.1830 "https://journals.aps.org/prd/abstract/10.1103/PhysRevD.55.1830"
[5]: https://www.mdpi.com/2218-1997/6/1/6 "https://www.mdpi.com/2218-1997/6/1/6"
