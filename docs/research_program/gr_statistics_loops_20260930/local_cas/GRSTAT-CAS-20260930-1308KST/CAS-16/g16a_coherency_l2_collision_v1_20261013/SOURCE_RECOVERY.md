# G16-A source recovery

Task card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip :: HTT_ALL_OBLIGATIONS_20261011/tasks/G16-A.json`
(`source_snapshot` a30d84c7918b54238a48fa62e2ef482f7e6d36fa). Repository HEAD at start: b976a27ca0c4fc038788e6ab8449e2d7e98b1b76
(branch proof/cas15-ls-matrix-synthesis-20261008). Read-only access only; no git state was changed.

Starting state: T did not exist when this (resumed) author run began; there were no partial files, no earlier
raw receipts and no earlier FROZEN_TARGETS.md to preserve.

## Inputs and hashes

| Input | sha256 |
|---|---|
| docs/research_program/gr_statistics_loops_20260930/supplements/DOSSIER_POSITIVE_BRIDGE.md | 00c1fcb0b786bb874f13e52442af4b7b8a125287d84decb799ea68fd03915ebd (matches CAS-16 contract `research_provenance_hashes`) |
| docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-16.json | c8c5c20c2d470a53dcf79dc8c3504e7a59874fed88a48917b8547755b37486cb |
| docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md | 4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897 (matches contract) |
| /home/cosmosapjw/Dropbox/bianchi/Dossier_IV_Restored_Revised.pdf | 8ce75785cf9d202d7baf8829b828faf04304f0ad2593df6532faf57b6dc188ef (matches ADDED_PDFS_MANIFEST.json:17-20) |
| CAS-16/c01_projector_frobenius_bridge_v1_20261011/ProjectorBridge.lean | e38b8f8a7079d3c6510f9d3836f7763232e916dc72c17d77ad532742dfa18abc (matches C01 RETURN.json `source_sha256` and REVIEW.md) |

## Recovered definitions (file:line)

1. **Operator (C1).** DOSSIER_POSITIVE_BRIDGE.md:195-198:
   `C_J(e) = Γ[-J(e) + 3/(8π) P_e (∫ J(e') dΩ') P_e]`, with `J(e)` the bolometric coherency and
   `Γ = c n_{e,rest} σ_T` (line 195). `P_e = I - e e^T` (line 78).
2. **Bound (C2) and proof sketch.** DOSSIER_POSITIVE_BRIDGE.md:200-204: "In matrix-Frobenius L²(S²),
   ‖C_J‖_{L²} ≤ (5/2) Γ ‖J‖_{L²}"; proof: ‖∫J‖ ≤ √(4π)‖J‖_{L²}, left/right multiplication by P_e contractive,
   gain ≤ 3/2, loss adds one. Line 204 also: coherency must not be replaced by intensity; electron tilt needs a
   transformed map (excluded here). Line 206: screen tensors embedded in one source tetrad before the angular
   integral (the "common frame" assumption).
3. **Coefficient field is complex.** Dossier IV (PDF printed p.13, §13, Eqs. (74),(76),(77)): "a physical photon
   coherency is Hermitian, transverse and positive semidefinite"; Eq. (77)
   `F_ij = ½ f_I S_ij + P_ij − (i/2) f_V ε_ijk e_k` — imaginary (circular-polarisation) part present.
   Hence the field is typed as `Matrix (Fin 3) (Fin 3) ℂ`, Cartesian components in one common frame.
4. **Projector.** Dossier IV §13 (p.13): `S_ij = δ_ij − e_i e_j` (identical to P_e).
5. **Rest-frame Thomson operator and Γ.** Dossier IV Eq. (89) (PDF p.14):
   `C_ℓ[F](e) = −κ_T F(e) + (3κ_T/8π) S(e) (∫ F(e') dΩ') S(e)`, κ_T = n_{e,rest} σ_T per path length,
   "Multiplication by c converts to physical seconds" ⇒ Γ = c κ_T, as in DOSSIER (C1). Cold electrons at rest,
   elastic, negligible recoil. Eq. (96) (p.14) moving electrons: D_e-dependent rate — excluded (THOM-TILT).
6. **Measure dΩ.** Unnormalized solid-angle measure on S² (Dossier IV Eq. (85): ∫ dΩ-moments with total 4π for
   r=0; Eq. (86) and the 3/(8π) coefficient presuppose total mass 4π). Formalised as Mathlib
   `(volume : Measure (EuclideanSpace ℝ (Fin 3))).toSphere` (Mathlib/MeasureTheory/Constructions/HaarToSphere.lean:52,
   polar decomposition `measurePreserving_homeomorphUnitSphereProd` :143), whose total mass is proved = 4π.
7. **Assumptions in contract.** CAS-16.json:43-44/58-59/79-80: "Coldrest-electron elasticThomson;Gamma>=0",
   "Fullcoherency incommonframe; L2Frobenius"; exclusions :67 "No optimality", "No spinquadrature
   generalization", "No fullBoltzmann"; singular loci :72 THOM-POL / THOM-TILT.
8. **Claim id.** supplements/DOSSIER_CLAIMS.json:135-141 (DP06): "Restricted rest-electron Thomson integral has
   L2 Frobenius norm <= (5/2) Gamma"; proof "Projection contraction and Cauchy–Schwarz".
9. **Reused component.** CAS16-C01 `finite_projector_bridge` / `sandwich_frobenius_le` (real 3×3, unit e):
   C01 RETURN.json status FORMALLY_CHECKED_SCOPED_FINITE_C01, review PASS_SCOPED. Imported unchanged.

## Physical normalization assumptions recorded explicitly
- dΩ has total mass 4π (proved for the chosen Mathlib measure, not assumed).
- L²(S², ℂ^{3×3}) norm: ‖J‖² = ∫ ‖J(e)‖_F² dΩ, ‖A‖_F² = Σ_ij |A_ij|² (Mathlib `Matrix.frobeniusNormedAddCommGroup`).
- Γ ≥ 0 is a real parameter; its physical identification Γ = c n_{e,rest} σ_T is not formalised.
- Equivalent normalized convention dΩ/(4π) with gain coefficient 3/2 is proved identical as an operator and
  to satisfy the same constants.

## Missing items
None blocking. The Hermitian / transverse / PSD structure of physical coherency (Dossier IV (74)-(75)) is not
imposed: the bounds are proved for every L² matrix field, which contains the physical subset.
