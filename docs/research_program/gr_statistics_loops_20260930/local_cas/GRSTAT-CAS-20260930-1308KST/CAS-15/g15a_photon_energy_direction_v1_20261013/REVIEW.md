# G15-A — independent review (verbatim final report of a fresh read-only reviewer)

# G15-A (CAS15-C01) independent review: photon energy and rest-direction derivatives from the velocity jet

**Verdict: PASS_SCOPED.** The pointwise (B1) identities are proved correctly in Lean, with the source's signs, c-factors and conventions. That holds inside the stated model (a parallel orthonormal frame along the ray). There are no blocking findings.

**Reviewer model:** Claude Opus 5.5. This is self-reported and not externally attested. The author also self-reports `claude-opus-5-5`, so author and reviewer are the same model family. This review is a fresh, separate session but not independent across model families.

**Scope:** read-only. No repository file was edited and no state-changing git command was run. All scratch files are under `…/scratchpad/g15a_rerun/`.

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Sources and conventions recovered correctly | OK | I read COMMON_SPEC lines 4–17, dossier (P0) lines 6–12 and (B1) lines 74–84, and CAS-15 C01 plus line 261. Their sha256 values match the receipts (`4714827e…`, `00c1fcb0…`, `eccc10a3…`). The zip (`2d0b6da9…`), the G15-A card member (`41b79b1f…`) and CAS-01 (`9f1bbb01…`) also match. In the Lean file, `Qjet` matches (P0) exactly: θ/3·h + σ + W − (u·X)(A·Y)/c, derivative slot first. `Lvec`, `pvec`, `accel`, `Rrate` and `Fcov` match (B1). |
| 1b | H1 checked by hand | OK | L·L = −c² + 2c(e·U) + c² = 0 and L·U = −c². With p = (E/c²)L: −p·U = E, u·p = −E/c, and h p = (E/c)e. Decomposition: e = (c/E)p − U/c gives e·U = 0, e·e = 1 and p = (E/c²)(U + ce). This matches `H1_*`. |
| 1c | H2 checked by hand | OK | Contracting the jet with L: h(U,·) = 0 and u·L = −c, so ∇_L U·Y = A·Y + c(θ/3 e·Y + σ(e,Y) + W(e,Y)). This equals the dossier's spatial part "A + c(De − We)", because W(e,Y) = −(We)·Y. Also U'·U = 0. From the constraint, e'·U = −[A·e + c(θ/3 + σee)]. Contracting E(U' + ce') + E′L = 0 with U gives −c²E′ − cE(A·e + cθ/3 + cσee) = 0, so E′/E = −(θ/3 + a·e + σ:ee) with a = A/c. Sign and c-normalization agree with the dossier and with the CAS-01 cross-check (B(K,K) at n = −e gives R(e); I verified CAS-01 line 41). |
| 1d | H3 checked by hand (covector form) | OK | ∇_L L = R L gives e'·Y = R(u·Y) + R(e·Y) − a·Y − θ/3(e·Y) − σ(e,Y) − W(e,Y). Since u·e' = −R, h e'·Y = (a·e + σee)(e·Y) − a·Y − σ(e,Y) + W(Y,e) = −F·Y + (We)·Y. The θ/3 term cancels. F·U = 0 and W(U,e) = 0, so the ∀Y covector form is equivalent to the rest-space vector identity (the metric is nondegenerate). |
| 1e | Independent symbolic cross-check | OK | `check_b1.py` (sympy) uses a Lorentz-boosted frame, a generic STF σ, W_ij = ε_ijk ω_k, spatial A and e on the unit sphere. It solves the 4 geodesic equations plus the constraint for (E′, e′). Output: `energy: 0`, `direction: [0,0,0,0]`, the flipped-W residual is nonzero, and u·F = u·We = 0. It also confirms the jet is self-consistent: c·uᵀQ = A and Q u = 0. |
| 1f | Is the model a legitimate encoding? | OK, scoped | In a parallel-propagated orthonormal frame along a curve, the metric is the constant η and ∇_L V has components dV^μ/ds. That makes the model a faithful encoding of a pointwise statement along the ray. The tangent L enters only through `hjet`, which is enough for these identities. The assumption is stated in the Lean header, SOURCE_RECOVERY §Modelling 1, and AUTHOR_RETURN `not_claimed`. |
| 1g | Quantifiers and domain | OK | The theorems are universal over all data with c > 0 and E(t) > 0, for one e at one event, which is the (B1) scope. Fewer constraints are assumed than the source has: σ need not be trace-free, and U·U and e·e are required only at t. The results therefore hold a fortiori. Nothing is claimed as a tensor-field theorem over all directions, so the pitfall is respected. |
| 1h | H4 negative controls and witness | OK | H4a refutes the conclusion with W flipped whenever some W(Y,e) ≠ 0. H4b refutes the energy law with e → −e whenever A·e ≠ 0. I checked the witness by hand: L = (1,1,0,0) gives Q(L,Y) = Y1 − Y2 − Y1 + Y2 = 0 = U'·Y. Also R = 1 − 1 = 0, F·Y = Y2 = W(Y,e), the flipped version gives −2Y2 ≠ 0, and R(−e) = 2. Every JetRay hypothesis is discharged, and the witness goes through H2, H3, H4a and H4b. |
| 2 | No hypothesis assumes the conclusion | OK | The inputs are `hjet` (the (P0) jet contracted with L in the derivative slot) and `hgeo` (∇_L p = 0). Neither is the conclusion. `core` derives E′ = −R·E and then the direction law from them. ∇_L L = R L appears only as the derived intermediate `hdir`. My probe derives `E' = -Rrate…*E t` from `ray_core` and compiles. The `heU` neighbourhood constraint is definitional, since e is the rest direction at every point of the ray. |
| 3a | Hashes and exit codes | OK | Recomputed: lean `fc4d0606…`, audit `d42a240f…`, olean `0c15d3c2…`, SOURCE_RECOVERY `ee9be51f…`, FROZEN `d6ed4138…`. All `compile_0N` source, stdout and stderr hashes match their JSON receipts. Exit codes: 01 = 1, 02 = 1 (failures kept), 03 = 0 (linter warnings only), 04 = 0 (empty output), 05 = 0. `compile_04.source.lean` is identical to `lean/G15APhoton.lean`. The 03→04 diff only removes unused simp arguments. The frozen statements match the final `#check` output. |
| 3b | Axioms and forbidden tokens | OK | Grep for `sorry`, `admit`, `native_decide`, `axiom`, `sorryAx`, `unsafe`, `implemented_by`, `extern`, `opaque` and `set_option` in `lean/` and `raw/AxiomAudit.lean`: none. The author audit's stdout lists only [propext, Classical.choice, Quot.sound] for all 10 printed declarations. |
| 4 | Independent recompile | OK | From cwd `/home/cosmosapjw/lean_oracles/viii_oracle` I ran `lake env bash -c "lean -R $S/src -o $S/out/G15APhoton.olean $S/src/G15APhoton.lean"` on a scratch copy (sha `fc4d0606…`). Exit 0, stdout and stderr empty, 11.3 s. The olean sha256 is `0c15d3c2…`, byte-identical to the author's. Toolchain: Lean 4.31.0 (commit 68218e87), mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f` from lake-manifest. My audit `ReviewAudit.lean` printed axioms for `mink_comm`, `hasDerivAt_mink`, all H1–H4 theorems, `core`, `ray_core` and `Ww`; every one is [propext, Classical.choice, Quot.sound]. Exit 0. |

## Blocking findings
None.

## Non-blocking notes
1. **Reparametrization is informal.** The geodesic enters as ∇_L p = 0, not ∇_p p = 0. These are equivalent for E > 0 because L = (c²/E)p, but that step is not formalized. It is documented. Suggested fix: add one sentence to the theorem docstring.
2. **The witness is degenerate.** It has E′ = 0, e′ = 0 and R(e) = 0, so it shows the hypotheses can all hold but never exercises a nonzero energy rate or direction change. Suggestion: add a second witness with R ≠ 0, for example E(s) = exp(−R s) with matching U′ and e′.
3. **The negative controls are weak.** H4a and H4b flip the conclusion, not the input convention. They follow from uniqueness of the identity. They are genuine but low-power; a stronger control would put a velocity-first W into `Qjet`.
4. **∇_L L = R L is not exported** as its own theorem. It is derived inside `core`. Exporting it would make the "derived, not assumed" requirement directly auditable.
5. **Minor citation inconsistencies.** SOURCE_RECOVERY cites "(P0) 6-13; (B1) 72-84", while AUTHOR_RETURN cites "6-12; 74-84".
6. **Independence is limited.** The dossier is on the blind-forbidden list for CAS workers. The author correctly claims no CAS-axis independence, and this lean-only lane cannot support CAS_4AXIS_PASS. Author and reviewer share a model family, as noted above.

## Not proved
- That a parallel orthonormal frame exists along the ray, or that covariant derivatives reduce to component derivatives there (a modelling assumption).
- The step from ∇_p p = 0 to ∇_L p = 0 (informal), and that a null geodesic exists at all.
- Anything about all directions at once as a tensor field, or any global or non-pointwise statement.
- The horizontal-derivative / brightness transport step (B2), sphere integration by parts (C02), and C03/C04.
- The other CAS-15 axes (wolfram_xact, sympy, sage). My sympy script is reviewer scratch only, not an axis run.
- Publication readiness and scientific admission; both are NOT_EVALUATED.
