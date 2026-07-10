# External anisotropic-curvature prior survey (C3 branch 2, 2026-07-10)

Executed for ticket `EGS3-K5-omega-k-higher-order-ceiling` exit-gate branch 2
("binding the finite ceiling to an external registered anisotropic-curvature
prior with documented applicability"). Web survey of the primary literature
(full texts read: Planck 2015 XVIII; Saadeh et al. 2016; Barrow–Juszkiewicz–
Sonoda 1985 ADS scan; Campanelli–Cea–Tedesco 2006).

## Headline (honest null)

**No published direct upper limit on anisotropic spatial curvature
Omega_k^aniso exists.** In every Bianchi VII_h CMB analysis the FLRW-limit
curvature of the anisotropic model is a *marginalized geometry/prior
parameter* (Saadeh 2016: uniform Omega_K in (1e-5, 0.5)), entangled with the
Collins–Hawking spiral parameter x/h — it is never bounded to smallness. The
quantities actually bounded are the **shear (sigma/H)_0** and **vorticity
(omega/H)_0**. Substituting the isotropic Planck 2018 Omega_K = 0.0007 ±
0.0019 would conflate a different quantity and is NOT done. Registering a
fabricated Omega_k^aniso ceiling is forbidden; the Omega_k component of the
K5 card therefore stays PLUGIN/BLOCKED, with this survey as the documented
obstruction for branch 2 (branch 1, the higher-order re-opening transfer,
remains the substantial GR-transfer item recorded in the ticket).

## Literature-defensible external anchors (registered as cross-checks only;
## all are Bianchi-VII_h-model-conditional, NOT model-independent)

| Quantity (their notation) | 95% limit | Source |
|---|---|---|
| (omega/H)_0, open-coupled VII_h, T | < 7.6e-10 | Planck 2015 XVIII (A&A 594, A18; arXiv:1502.01593) |
| (omega/H)_0, vector-mode recast | < 5.2e-11 | Saadeh et al., PRL 117, 131302 (2016; arXiv:1605.07178) |
| (sigma_S/H)_0 (scalar) | (-6.7, +9.6)e-11 | Saadeh et al. 2016, Table II (Planck, all-mode) |
| (sigma_V/H)_0 (vector) | < 4.7e-11 | Saadeh et al. 2016 |
| (sigma_T,reg/H)_0 (weakest mode) | < 1.0e-6 | Saadeh et al. 2016 |
| (sigma_T,irr/H)_0 | < 3.4e-10 | Saadeh et al. 2016 |

Context values that are NOT limits: Planck 2015 XVIII open-coupled VII_h fit
Omega_k = 0.09 ± 0.05 (Table 3) is a fitted geometry value for a *disfavored*
model (polarization template amplitude -0.10 ± 0.04 vs +1 expected); the
Campanelli–Cea–Tedesco "ellipsoidal universe" (PRL 97, 131302, 2006) is
spatially FLAT — its eccentricity 0.50e-2..0.74e-2 at decoupling is a
*required* shear proxy, not a curvature bound. Classic vorticity limits:
Barrow–Juszkiewicz–Sonoda, MNRAS 213, 917 (1985): (omega/H)_0 < 1e-7 (VII_0),
< 7e-7 (VII_h, Omega_0=0.7), < 5e-9 (V, Omega_0=0.3); their eq (4.22) pattern
Delta T/T = sqrt(A^2+B^2) (omega/H)_0 cos(theta_0 + phi) bounds
shear/vorticity through the quadrupole, with curvature entering only through
the Bianchi type and x — again no Omega_k bound.

## Internal derived route (checked, vacuous)

The v8-update interior-family lane derives the exact Bianchi V slaving
|curl v|^2 = a^2 v_perp^2 (egs3_interior_family.py), suggesting
Omega_k ~ W^2 / v_perp^2 (up to convention factors). With the registered MES
ceiling W2_max = 1.309e-6 and v_perp = beta_CF4 = 1.137e-3 the implied ceiling
is O(10) — greater than unity, hence VACUOUS as a bound (and it would in any
case be conditional on the vorticity being Bianchi-V-tilt-sourced). Recorded
so the route is not re-attempted naively.

## Bibliography gaps flagged (manuscript maintenance, out of this cycle's scope)

`docs/manuscript/references.bib` lacks standalone entries for Planck 2015
XVIII (arXiv:1502.01593), Planck 2013 XXVI (arXiv:1303.5086),
Barrow–Juszkiewicz–Sonoda 1985 (MNRAS 213, 917), Campanelli–Cea–Tedesco
2006/2007 (astro-ph/0606266, 0706.3802); `Saadeh2016`/`Saadeh2016b` are
duplicates; `Pontzen2011` has a key/year mismatch (year=2007).

Claim boundary: literature survey + documented null; no data claim, no
signal-discovery claim, no Bianchi-class-identification-of-the-sky claim, no
probabilistic-inference claim.
