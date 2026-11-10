# L1 — Bianchi-I endpoint temperature map: derivation, adversarial limits, tests

Date: 2026-11-10. Status: **PASS_SCOPED (theory + synthetic oracle only)**. Not a Planck result. Temperature only. All numbers below are SYNTHETIC (noiseless full-sky maps generated from the formula).

## 1. Model and assumptions (each is a scope restriction)

- Signature (-,+,+,+), c explicit: `ds² = -c²dt² + g_ij dx^i dx^j`, `g_ij = a²(t) [e^{2B(t)}]_ij`, B symmetric trace-free, `a(t0)=1`, `B(t0)=0`.
- Homogeneous Bianchi I (translations `∂_i` Killing) → covariant spatial photon momenta `p_i` are conserved.
- Emitters are comoving (fluid-orthogonal; no tilt) on a sharp, isotropic last-scattering surface `t=t*`, blackbody `T*`. Propagation afterwards is collisionless; the observer is comoving at `t0`.
- Observer orthonormal triad: `p_i = E0 n_i`, `|n|=1`.

## 2. Derivation

Emission-frame energy: `E*² = g^{ij}(t*) p_i p_j = a*⁻² E0² nᵀ e^{-2B*} n`. A collisionless photon population keeps a Planck shape with every frequency scaled by the same factor `E0/E*`, so

```
T_obs(n) = T* E0/E* = a* T* [ nᵀ e^{-2B*} n ]^{-1/2},      T̄ ≡ a* T*.        (L1.1)
```

(`B*` is the endpoint value of B at `t*`.) For a fixed commuting principal-axis history `Ḃ = σ`, `B* = -∫_{t*}^{t0} σ dt`. For non-commuting histories the componentwise integral is NOT valid; the endpoint metric from the evolution is authoritative. This relation to `σ(t)` is documented in R47 METHODS_NO_BOLTZMANN.md §2 and was **not** re-derived or tested here.

Exact facts used below: `e^{-2B}` is symmetric positive definite, so `T>0` for any finite B; for an eigenvector `v` of B with eigenvalue λ, `T(v)=e^{λ}`, hence `e^{λ_min} ≤ T/T̄ ≤ e^{λ_max}`. `T(n)=T(−n)` exactly (all odd multipoles vanish).

## 3. Small-B expansion (with `u_k(n)=nᵀB^k n`)

```
T/T̄ − 1 = u1 − u2 + (3/2)u1² + (2/3)u3 − 3 u1u2 + (5/2)u1³ + O(‖B‖⁴)     (L1.2)
```
Sphere averages for trace-free B: `⟨u1⟩=0, ⟨u2⟩=trB²/3, ⟨u1²⟩=2trB²/15, ⟨u3⟩=trB³/3, ⟨u1u2⟩=2trB³/15, ⟨u1³⟩=8trB³/105`, giving the monopole

```
⟨T/T̄⟩ − 1 = −(2/15) tr B² + (4/315) tr B³ + O(‖B‖⁴).                      (L1.3)
```
Order-k terms are polynomials of degree ≤2k in n, so only even ℓ ≤ 2k appear: ℓ=2 at O(B), ℓ=4 at O(B²), ℓ=6 at O(B³).

## 4. Tests run (oracle: `L1_bianchi_I_endpoint_oracle.py`)

| Check | Result |
|---|---|
| Algebra from `E*²=g^{ij}p_ip_j` vs (L1.1) | max err 2.2e-16 (restates the algebra; not an independent physics test) |
| CAS (sympy) series of `(1+x)^{-1/2}`, `x=nᵀe^{-2B}n−1`, vs (L1.2) | **match** (my first check omitted the leading 1 and returned False; fixed) |
| Sphere moments (GL quadrature, random traceless B) vs closed forms | max abs err 1.4e-17 |
| Monopole residual after 3rd order, ε=0.2…0.025 | ratio of consecutive residuals 15.87, 15.95, 15.98 → scales as ε⁴, as expected |
| Parity: odd-ℓ amplitudes, ℓ=1,3,5,7 | ≤ 3.0e-17; `T(n)−T(−n)` = 0 |
| ℓ-content: amplitude ratio when ε is halved (ℓ=2,4,6,8) | 1.992, 3.979, 7.948, 15.88 vs expected 2, 4, 8, 16 (ε^{⌈ℓ/2⌉}) |
| Rotation: `T_{QBQᵀ}(Qn)−T_B(n)` | max 8.9e-16; `C_ℓ` rotation invariance rel. 4.4e-11 |
| Quadrature convergence (B-norm 0.3): N=8,12,16,24 GL nodes | a₂ power rel. err 3.2e-6, 1.0e-9, 6.6e-14, 5.5e-15; monopole abs err 6e-8, 2e-11, 2.9e-15, 8.7e-16 |
| Eigenvector exactness `T(v)=e^{λ}` | 1.1e-15 |
| Large B (‖B‖ scale 1.5): sampled range of T | [0.41933, 3.2524] inside `[e^{λmin}, e^{λmax}]=[0.41928, 3.2603]` |
| B→0 | max deviation 2.2e-16 |
| Pixel vs harmonic: `C_ℓ` from HEALPix `anafast` vs GL harmonic quadrature (B-norm 0.1), nside 16→128 | ℓ=2: 1.8e-9→4.0e-11; ℓ=8: 2.7e-5→4.8e-7 (error ∝ nside⁻², ratios 3.5, 4.0, 4.0) |

Environment: numpy 2.4.2, scipy 1.17.0, sympy 1.14.0, healpy 1.19.0, python 3.12.3; seed 20261110.

## 5. Adversarial limits

Items below come from an independent free-model critique (single provider answered; the three-provider consensus **did not** complete, so these are leads, each checked by me):

| Lead | Verdict |
|---|---|
| Sign of B (`e^{+2B}` vs `e^{-2B}`) | Scope: formula holds for `g=a²e^{2B}`; the opposite convention needs `B→−B`. Must be fixed in every operator/test. |
| Arrival vs propagation direction `n→−n` | **Harmless**: (L1.1) is even in n (checked, 0.0). The claim that it breaks the formula was rejected. |
| Tilted (non-orthogonal) fluid | Scope: excluded by assumption; a Doppler term would be needed. Not implemented. |
| Non-commuting B history | Scope only for relating `B*` to `σ(t)`; (L1.1) itself needs only the endpoint `B*` because `p_i` is exactly conserved. The claim that a path-ordered exponential enters (L1.1) was rejected. |
| Redshift definition | Harmless once `T̄=a*T*` is fixed. |
| Spectral distortion by shear | Not for collisionless propagation of a Planck spectrum (uniform frequency scaling). Rejected for the stated assumptions; it does limit the model if post-`t*` scattering matters (excluded by assumption). |
| Polarization | Scope: (L1.1) is intensity only. No E/B prediction follows. |
| Perturbations / ISW / finite last-scattering thickness / foregrounds | Scope: absent from the model. The map is a homogeneous-background template, not a full likelihood. |

## 6. Explicitly UNAVAILABLE

- E/B (and T-E cross) physical transfer for Bianchi I: UNAVAILABLE. No zero-filled E/B prediction is to be used as a physical prediction.
- Bianchi V/VIIh transfer: UNAVAILABLE; Bianchi I must not be relabeled as VIIh.
- Link between `B*` and today's shear: not provided; `B*` is a history integral.
- Masked-sky, beamed, noisy, foreground and frequency-map behaviour: NOT_RUN (no mask-injection test was done).
- Doppler/aberration of the local observer (WU-010/011 operator) is a separate operator and is not part of (L1.1).

## 7. Link to CORE-03 findings
The CMB low-ell predictors in the repository (`tau`-based transfer in `tensor_joint_multiprobe_likelihood.py:491` and `source_bound_planck_lowell_operator.py`) are not derived from (L1.1) and remain UNAVAILABLE as physical operators (see PHYSICAL_STATE_CONTRACT_AUDIT.json). The STF5 chart must use the Gram metric when quoting a shear amplitude.
