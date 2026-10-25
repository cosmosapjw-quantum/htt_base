# Scientific provenance and interpretation: optical inverse product

Task R32-05-P6-OPTICAL, execute packet `4061878216a65321d922f6c919d44fd3406ce3e8bfefe7d7e02a1329d703ceec`, input `sha256:f900ec93d972751795cdd825ee0f362eabed3a2aae60b59e4c24d265ee6ec132`. Scientific author requested Astra/xhigh; observed runtime UNKNOWN. Initial checkout was the existing primary repository, branch `research/htt-adaptive-methods-20261023`, HEAD `dff1f6a330bffec122225c3b0e8edb19e8b7d122`, origin `https://github.com/cosmosapjw-quantum/htt_base.git`. Existing dirty/untracked state is preserved. Author wrote only this product's science directory, with no Git/state changes or numerical-code execution.

## Research result and relation to retained work

The companion Q/O manuscript already proves the complete-field optical inverse and the finite magnitude quadrupole remainder. The new note reuses those results and supplies a direct stability proof for a uniformly perturbed complete field. It composes sampling, working whitening, nuisance projection and the local logarithmic response, and identifies the exact finite linear sector with its residual-compatible error set. The finite support formula includes the observational kernel rather than assigning its components zero. The full nonlinear equivalence relation and feasible set are given separately, avoiding any inference of global nonlinear injectivity from a tangent rank.

The linear-algebra ingredients are standard pseudoinverse, range compatibility, support functions and norm inequalities. No claim of priority for these generic ingredients is made. The research contribution is their explicit optical composition, finite remainder support, retained corrected tensor illustration, and the numerical qualification target for a physical bound. Formula-specific prior-art comparison beyond the cited local cosmography and companion results would be needed before asserting broader novelty. The manuscript makes no such assertion.

The retained CF4 tensor and five-coordinate working matrix give new small downstream figures/tables without repeating the catalogue extraction. Its dimensionless convention is confirmed by the producer design `B=-kappa*(T:nn)` and exact source basis. Historical magnitude labels and the reversed T1 prose are not followed. The physical-radius plots are conditional designs, not estimates of an actual error radius. The complete qualification must relate the selected finite-window response to the same-event congruence tensor. This stronger physical input is a branch-local requirement, not a prerequisite to the stated conditional methods product.

## Claim-to-source map for generated JSON

Every row has owner `mio` for deterministic diagnostic images or `common` for algebraic response/units, transfer_source `none` except the apparent CF4 statistic `empirical_proxy`, and claim_tier `C0`. The manuscript is a non-claim-promoting conditional methods candidate. Use the source paths rooted at `PUBLICATION_ACCELERATION_20261025`.

| ID | Statement / manuscript equations | Owner | Status | Evidence and exact source |
|---|---|---|---|---|
| P6-01 | Same-congruence optical law, units and sign; (1)–(4) | common | DERIVED, CONDITIONAL | Companion `products/R32-01-QO-METHODS/science/MANUSCRIPT.md` (20)–(24); Heinesen 2010.06534v2; frame distinction Maartens 2312.09875v3 |
| P6-02 | Complete-field inverse and uniform-error bound; (5)–(8) | common | DERIVED, CONDITIONAL | Complete proof here; inverse reused from companion (38)–(39); positive full sphere and bounded field perturbation required |
| P6-03 | Composed nonlinear map and finite remainder support; (9)–(15) | common | DERIVED, CONDITIONAL | Complete construction/proof here; `evidence/research/physical_derivations.md` P3; row total variation and epsilon<1 required; box is an outer set |
| P6-04 | Identifiable sector, range-compatible finite inverse/support; (16)–(19) | common | DERIVED | Complete proof here; unrestricted linear parameter model, compact error set for finite support, exact kernel criterion; physical domains intersect separately |
| P6-05 | Product error region and tensor support; (20)–(22) | mio | DERIVED, CONDITIONAL | Direct proof here; deterministic adopted shape/radii, no probability inferred |
| P6-06 | Apparent CF4 tensor, rank, units and basis; (23)–(26) | mio | DIAGNOSTIC_ONLY | `evidence/research/latest_results.json`, `units_correction`, `cf4_calibration_quotient`; `evidence/research/latest_physical_results.md` source-unit correction; `evidence/RESULT_OBSERVABLE_MAP.json` CF4_QUOTIENT; source-bound measured finite statistic, not physical shear |
| P6-07 | Magnitude quadrupole error is distinct from dimensionless quotient; (27) | common | DERIVED, CONDITIONAL | Companion (36); proof via (11) and STF spherical norm here |
| P6-08 | Conditional normalized/dimensional shear bounds; (28)–(32) | mio | DERIVED, CONDITIONAL | Proof here; `evidence/research/physical_derivations.md` P7–P8; `evidence/RESULT_OBSERVABLE_MAP.json` SHEAR_ERROR_BOUNDS; response/error/H inputs assumed, not observed |
| P6-09 | Tensor carrier and unavailable sectors; (33)–(35) | mio | SPECIFIED, CONDITIONAL | Explicit definitions here; same-congruence observation kernel and repository xqpi formalism; no F/Pi/G_F measure/law invented |

Required caveats in the generated claim map: P6-04 exact statements apply to the declared finite linear model, not unrestricted nonlinear global inversion; P6-05 assumes a product error set; P6-06 working covariance is not empirically calibrated; P6-08 qualification is not supplied by the retained point estimate; P6-09 all absent physical sectors remain unknown/undefined.

## Physics/math audit

**Verdict:** complete conditional derivation ready for literal build and fresh independent review; no scientific acceptance yet.

**Assumptions and conventions:** signature (-+++), n points observer to source, ell=-u+n, proper length c tau; physical H/sigma/omega have inverse-time units and acceleration length/time squared. d=-A/(cH), S=sigma/H are dimensionless in a common orthonormal rest frame. All tensor coordinates are Frobenius orthonormal. Magnitude, rate and dimensionless tensor conventions are distinct. Full-sphere averages are normalized to one. CF4 coordinates use the retained J2000 basis and source-selection design.

| Audit item | Finding | Required implementation action |
|---|---|---|
| Logarithm and inverse | Defined only for positive 1+q; finite tail uses epsilon<1 | Preserve domains and complete-field versus finite-map distinction |
| Finite rank and kernel | Exact theorem for A; tangent rank alone is not global nonlinear identification | Preserve E_z, compatibility test, rank-zero case and kernel |
| Units | Corrected CF4 coefficient is dimensionless; kappa is already in B | No second kappa division; H multiplies dimensional interval |
| Physical shear | Only under (28), with all applicable response errors | Label radii assumed and preserve source gap |
| Degenerate limits | q=0 gives isotropic field; delta=0 gives zero field bound; A=0 gives no identifiable sector; r_Q>=t removes positive lower bound | Check the stated small-matrix/source limits only |
| Statistical law | None adopted for physical coverage; C is an illustrative shape | No chi-square/credible/confidence labels on figures |
| x/F/Pi/Q/G_F | Full tensor carrier retained; scalar policy requires positive denominator; occupancy/law/depth functional absent | Emit explicit undefined/unknown statuses, never zeros |

No fatal scientific blocker was found in preparing this conditional contract. A later concrete build/review failure should name its exact claim and failing example before a bounded repair. Missing physical null calibration blocks stronger physical probability statements only.

## Claim audit and required consumer outputs

Evidence read: FRONTIER task, README, OUTPUT_DAG, current handoff, manifest references, corrected retained CF4 sufficient statistics, physical derivations, observable map, companion optical manuscript/build/result, project physics/claim/xqpi skills, and personal WRITING_PROTOCOL_V4. Bibliographic metadata for Heinesen and Maartens was checked at the primary arXiv abstract pages on 2026-10-25. Those checks verify source identity/context; the present explicit derivations carry the mathematical argument.

Proposed scientific content is MANUSCRIPT.md; the literal numerical/layout actions, source checks and figures are in BUILD_CONTRACT.md. Risks addressed are nonlinear/linear domain conflation, dropping range compatibility, dividing the dimensionless quotient twice, inventing a physical error radius, replacing tensor carriers with a norm, and attaching probability to the working matrix. A source mismatch, wrong unit/basis, nonpositive shape matrix or failed finite support test stops the consumer and returns the exact evidence.

No claim is upgraded to physical detection, family identification, original42 completion or independent validation by this draft. The only proposed qualified product is `optical_inverse_note`, conditional on the actual complete candidate and fresh independent review. No permanent registry, extra acceptance gate or new budget is introduced. The generated result must retain x/F/Pi/Q/G_F statuses, raw implementation/build outcomes and the exact candidate manifest identity.

## Stronger physical branch requirements

To turn the apparent CF4 tensor into a physical interval, supply a same-frame, same-event response qualification with a joint error set covering the applicable finite-redshift, peculiar-motion, selection, calibration and frame terms. To attach coverage, additionally supply the corresponding joint sampling law or an independently justified coverage event. To obtain dimensional sigma, supply positive H normalization and its joint dependence. To fill the rest of x_C, supply its vorticity, tilt, curvature and energy conventions/data. These are exact requirements for stronger claims, not missing prerequisites for the present deterministic inverse and error-budget frontier.
