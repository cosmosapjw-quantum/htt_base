# L5 — Directional Hubble law and optical distance–redshift jet

Date: 2026-11-11. Status: **PASS_SCOPED (theory + synthetic oracle; first-order exact, second-order numerical in Bianchi I only)**. No supernova distances were read.

## 1. Conventions
Signature (−,+,+,+), c explicit. `u^a` is the unit congruence of comoving observers **and** sources (observer congruence = source congruence); `∇_a u_b = σ_ab + ω_ab + (Θ/3) h_ab − u_a A_b`. `n` is the unit line-of-sight direction from the observer toward the source; the photon propagates along `e = −n`. `A_a` is the acceleration `u^b∇_b u_a` (units 1/s when divided by c).

## 2. First order (exact)
For a null geodesic `k^a = E(u^a + e^a)` the energy seen by the congruence obeys `dE/dλ = −k^a k^b ∇_a u_b`. Contracting the decomposition above,

```
k^a k^b ∇_a u_b = E² [ Θ/3 + σ_ab e^a e^b + A_a e^a ]          (vorticity drops: ω_ab is antisymmetric)
```
so, with `ℓ` the proper (affine, E-normalised) distance and `e = −n`,

```
z = ℓ H(n) + O(ℓ²),     H(n) = Θ/3 + σ_ab n^a n^b − A_a n^a / c.                    (L5.1)
```
Checks (L5_bianchi_I_optical_jet_oracle.py): the contraction identity holds to 3.6e-15 for 200 random tensors; in exact Bianchi I (`a_i = t^{p_i}`) the limit z/(look-back time) equals `Σ n_i² H_i = Θ/3 + σ_nn` (deviation 1.6e-4 at z=1e-4, an O(z) effect); the sky average of H(n) equals Θ/3 to 7e-16.

* **Vorticity** does not enter (L5.1) at all: `e^a e^b ω_ab = 0`. Its first appearance is at second order (not derived here, see §6) and, in the proper-motion channel (L3), at first order as the B1 mode.
* **Curvature** does not appear in (L5.1) either; it can only enter at second order through the evolution of Θ, σ.
* **Different source and observer congruences.** A relative velocity `v` between the source frame and the observer congruence adds a Doppler shift `δz = n·β` of order z⁰ (not ℓ¹). In `d_L(z)` it therefore appears as a `1/z` dipole; the observer boost β_MO and a local bulk flow have the *same* shape and are structurally degenerate (L5_PANTHEON_STRUCTURAL_RESULT.json: rank 12 of 15, nullity 3).

## 3. Ratio versus difference; local versus finite-z
* Difference: `ΔH(n) = H(n) − H̄`; ratio: `R(n) = ΔH(n)/H̄`. At first order `H̄ = Θ/3` is the full-sky mean (verified), so the quadrupole amplitude of R in a Frobenius-orthonormal STF chart is `σ_k/H̄`, and the dipole is `−A_k/(cH̄)`. With partial sky coverage the sample mean is **not** Θ/3, so ratio and difference are not interchangeable; the monopole must be a free parameter (M0 in the operator).
* **Finite z.** `d_L = (z/H(n)) [1 + c0(n) z + O(z²)]`. Numerically (exact Bianchi I, area distance from geodesic deviation) `c0(n)·H(n)²` is a polynomial of degree ≤ 4: harmonic amplitudes at ℓ = 0, 2, 4 only (ℓ = 5…8 and all odd ℓ ≤ 1.2e-7, fit residual 7e-9). The isotropic limit reproduces the exact FLRW formula (5e-9) and `c0 = (1−q0)/2`.
* **Quadrupole at finite z (numerical finding, power-law Bianchi I only).** The ℓ=2 part of the second-order term of `H_eff = z/d_L` equals the first-order ℓ=2 part (ratio 1.0000–1.0087 per unit z for p̄ = 0.5, 0.6, 0.667, 0.9 and anisotropy 1.1–17%; 1.0001 or closer for anisotropy ≤ 2%). I.e. the quadrupole of `z/d_L` is `H₂ (1 − z + …)` independent of q0 to this accuracy. This is **not proven** and was tested only for one anisotropic family.

## 4. Truncation remainder (exact distance vs jet, p̄ = 2/3, H_i spread ±4.5%, 24 directions)
| z | first-order law, max rel. error | second-order law, max rel. error |
|---|---|---|
| 0.01 | 2.7e-3 | 1.3e-5 |
| 0.03 | 8.2e-3 | 1.1e-4 |
| 0.10 | 2.6e-2 | 1.2e-3 |
| 0.20 | 5.1e-2 | 4.4e-3 |
| 0.30 | 7.3e-2 | 9.1e-3 |

First-order error ≈ 0.27 z; second-order error ≈ 0.12 z² (relative), i.e. the O(z³) term of d_L. The anisotropic part of the first-order error is ≈ 0.06 z.

## 5. Estimator consequence
A first-order directional-Hubble fit at redshift z is biased by an O(z) fractional change of the quadrupole (≈ −z·(true quadrupole)), and its monopole is biased by (1−q0)z/2. The monopole must be fitted with free z-dependence (M0, q0, j0-like terms) and the quadrupole/dipole interpreted through (L5.1) only for z ≲ 0.05–0.1, or with the second-order structure of §3 declared as nuisance (degree-≤4 polynomial in n).

## 6. Not established
* Second-order terms with **vorticity** and **spatial curvature** (non-Bianchi-I types, tilt) — Bianchi I has ω = 0 and flat sections, so the oracle cannot test them. UNAVAILABLE.
* Inhomogeneous (gradient) corrections at second order; peculiar-velocity covariance beyond a flow nuisance.
* Any real-data estimate. CF4 remains conditional; DESI compressed BAO vectors give background distances only and carry no angular information (background control only).
