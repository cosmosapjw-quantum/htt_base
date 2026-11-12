# L6 — Ordered Lorentz composition and per-observable response (theory, C0)

## 1. Ordered composition
Velocities are composed with the exact special-relativistic law, `u ⊕ v`, which is neither commutative nor associative in general; the order
(observer-frame boost first, then the matter/tilt boost) is part of the estimand definition. The composite carries a Thomas–Wigner rotation
`ω ≈ ½ |β₁ × β₂|` (small β). Exact check (`L6_wigner_rotation_bound.py`, receipt `L6_WIGNER_ROTATION_RECEIPT.json`): for two boosts of β≈1.2×10⁻³ the rotation is ≤ 7.2×10⁻⁷ rad;
exact and leading-order values agree to ≤ 9×10⁻⁷ relative. The repository composition returns the velocity only; the rotation is not carried (recorded limit, not a bug at this β).

## 2. Per-observable linear response (first order in β; each modelled separately, none inferred from another)
| observable | response to observer velocity relative to the tracer rest frame | sources of non-kinematic dipole |
|---|---|---|
| CMB temperature dipole | `ΔT/T = β·n̂` relative to the CMB frame | intrinsic/primordial large-scale mode `i_c` |
| CMB aberration / modulation | `β` relative to the CMB frame (independent of `i_c`) | lensing / foreground-mask leakage |
| source-count dipole, shell k | `D_k = [2 + x_k(1+α_k)] (β − τ_k)` | LSS shot/intrinsic dipole `s_k`, selection, evolution |
| source size / flux boosting | response not derived here (UNAVAILABLE) | — |
| redshift (peculiar velocity) | `z_obs = z(1 + β·n̂)` at first order, dipole of z/d_L tied to the L5 coefficients | cosmic-variance bulk flow |
| astrometric proper-motion glide | acceleration/vorticity modes (L3); **not** the boost | — |
Here `β` = observer velocity relative to the CMB rest frame and `τ_k` = matter-frame velocity relative to the CMB frame in shell k (the global tilt).
The count dipole is sensitive to `β − τ_k`; the CMB dipole to `β`; hence a single dipole never proves global tilt.

## 3. Estimand statement
Local-boost estimand: β. Global-tilt estimand: τ(z) with a declared depth-coherence model (shared τ, or per-shell τ_k). Nuisances (`α_k`, `s_k`, `i_c`) are projected out;
anchors are independent observables (CMB aberration for β). See `L6_LOCAL_GLOBAL_IDENTIFIABILITY.json`.

## 4. Limits
First order; no second-order Doppler/aberration cross terms in the dipole response; size/flux-boost and redshift responses not built; vector (3-component) case not run (collinear scalar model).
