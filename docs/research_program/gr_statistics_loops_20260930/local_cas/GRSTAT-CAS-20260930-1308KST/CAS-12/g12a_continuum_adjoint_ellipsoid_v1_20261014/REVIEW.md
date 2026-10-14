# G12-A — independent review (verbatim final report of a fresh read-only reviewer)

# G12-A fresh independent review: continuum adjoint of a fixed collision operator and the collision-moment ellipsoid

**Verdict: PASS_WITH_NOTES.** Nothing blocks. Scientific admission stays HOLD.

- **Reviewer model:** claude-opus-5-5 (Opus 5.5). I did not author G12-A.
- **What I did:** read-only review. I edited no repository files, ran no state-changing git commands and spawned no subagents.
- **Scratch:** everything I wrote is under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g12-a_rerun/`.
- **Target directory:** T = `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-12/g12a_continuum_adjoint_ellipsoid_v1_20261014`

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 0 | Task card read first | PASS | `unzip -p HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip …/tasks/G12-A.json`. Scope is TEFF-A3 ⟨K,L(f−g)⟩=⟨L*K,f−g⟩ plus the ellipsoid. Acceptance has 4 items; pitfall: no nonlinear, polarized or frequency-redistributing extension. |
| 1a | Source citations and hashes | PASS | `sha256sum`: TEFF_POSITIVE_BRIDGE f04d96fe…, CAS-12.json 5a682716…, TEFF_CLAIMS 9654e73e…, DECISIONS a05b3053… all match SOURCE_RECOVERY.md. I opened every cited line range (S:37-74, 93-100, 120-141; C:44-84, 245-260; TC:64-80; D:515-534) and each says what is claimed. |
| 1b | Operator, medium, dν and domain (TEFF-A3) | PASS | Source S:133 is (Lf)(E,e)=τ(E)[∫P(e,e')f(E,e')dΩ' − f(E,e)] with P=3[1+(e·e')²]/(16π). This matches `collOp` (gain uses `P x.2 e'`, the loss term has its minus sign, τ multiplies both). `thomsonP` is the literal kernel on `Sphere2`. dν: `nu_eq_prod` is `rfl` against the G11-A `nu C` = (Lebesgue on (0,∞)) with density C E², times `dOmega`. Medium enters only through τ(E) and P, as the source's fixed-scatterer-rest-frame model says. |
| 1c | Adjoint direction | PASS | `collAdj` is the same τ with the transposed kernel, so L*K(E,e)=τ(E)[∫P(e',e)K(E,e')dΩ' − K(E,e)]. A numerical test with a deliberately non-symmetric kernel shows that using L in place of L* gives a different pairing (for example 2.558e-3 vs 2.704e-3), while `collAdj` matches to about 1e-15. |
| 1d | Frozen targets match the card's quantifiers, domains, measures, signs and branches | PASS | A mechanical whitespace-normalized diff of every FROZEN signature against the Lean source: all theorem statements MATCH. The only differences are the `noncomputable` keyword (not captured by my extraction) and `BoundedRoute.transpose` making implicit binders explicit. The abbreviated (BH)/"…" targets match on manual check. The adjustments are listed under the T1–T10 rows of check 2 and are either strengthenings or disclosed sufficient conditions. |
| 1e | FROZEN predates the first proof compile | PASS (mtime only) | FROZEN_TARGETS.md sha 27c98672… matches raw/FROZEN_TARGETS.sha256. Its mtime is 21:55:12Z; the first proof compile `compile_14_main` started 2026-10-13T22:02:11Z. Only dependency builds and probes ran before it (probe02 at 21:58 is a `#check` probe). The 14→16 source diff changes proofs only, plus two true instances (`energyMeasure_sFinite`, `dOmega_isFinite`). |
| 1f | Hand and numerical checks | PASS | `numcheck.py` (24×48 Gauss-Legendre × uniform-φ sphere grid, 400-node energy grid, b=1.3, C=0.7, τ(E)=1+0.5 tanh(E−2), f and g random inside F_b). Results: ∫P dΩ'=1 to 7e-16; P symmetric; bounds [0.0597, 0.1194=3/(8π)]. Funk–Hecke gives p_0=1, p_1=0, p_2=0.1 (to 1e-14), p_3=p_4=p_5=0; Rayleigh quotients on Y_lm agree to about 1e-16. Adjoint pair ⟨K,L(f−g)⟩=⟨L*K,f−g⟩ holds to relative error ≤3e-15 for Thomson and for the non-symmetric kernel. Linearity ⟨K,Lf−Lg⟩=⟨K,L(f−g)⟩ to 1e-17. L²(W dν) self-adjointness (Thomson) and the transposed Hilbert adjoint (non-symmetric kernel) hold to 1e-16. ‖L‖ is empirically 0.94, under the Lean bound 3.75. |
| 1g | τ(E) × kernel-score product kept (pitfall 2) | PASS | `collEvec_eigen`: e_j=(p_j−1)∫τK_j(f−g)dν. Numerically, for K=E e^{-0.2E}Y_20, ⟨K,Ld⟩ = −7.2595e-3 equals (p_2−1)∫τKd = −7.2595e-3, while dropping τ gives −5.441e-3. |
| 1h | Negative control T8 is genuine | PASS | `energy_dependent_tau_counterexample`: τ=(2,1), P=½ (symmetric), K=sgn(e), eigenvalue p=0, ∫K(f−g)=0, f>0. I recomputed by hand and in Python: collEvec = 2 ≠ 0 with energy-dependent τ, and 0 with constant τ=2. It exercises exactly the COLL-TAU singular locus. |
| 1i | Scope guards | PASS | `collOp` acts only on angle at fixed E, is scalar and linear. No polarized, frequency-redistributing or nonlinear object is defined. CAS12-C01 is not imported: grep finds only a comment, and the import chain is BregmanThreePoint (CAS-11 C01 v2, a Bregman identity, not the finite adjoint) → … → G12DCardClosure. No `LinearMap.adjoint` is used; the Hilbert adjoint comes from `ContinuousLinearMap.adjoint` on the actual L². |
| 2a | T2 is proved, not assumed | PASS | `adjoint_pair` takes only absolute integrability of `fubKernel` on (ν⊗σ) and of the loss term. The identity comes from `integral_prod` (Fubini) twice plus `MeasurePreserving.integral_comp'` for `angSwap`, ((E,e),e')↦((E,e'),e). Measure preservation is built from prodAssoc and swap. The domain is explicit. |
| 2b | Hypotheses hLK, hG, hloss | PASS | In layer-1 T4 and T6 they are explicit premises, as the source's conditional wording "If L*K_j satisfies the weighted integrability assumptions" asks. In T5 all three are discharged and returned as conjuncts: `collAdj_memLp` (Cauchy–Schwarz on a finite σ plus |P|≤Pmax, |τ|≤τmax) and `fubKernel_integrable` (AM-GM \|ab\| ≤ (wa²+b²/w)/2, using δ²/W integrable from G11-C `z_memLp`). In T9 they are discharged through T5. No premise assumes a conclusion. |
| 2c | T7 eigen-relation is a hypothesis and is disclosed | PASS | `heig: ∫P(e',e)K(E,e')dσ = pK` (the transposed relation, correct for L*) is a premise. SOURCE_RECOVERY §3, FROZEN T7 and AUTHOR_RETURN `scope_and_caveats` all state that the p_l values belong to G12-B / CAS12-C02. My Funk–Hecke check confirms the source values. |
| 2d | T10 Hilbert adjoint | PASS | `collCLM_adjoint` comes from `ContinuousLinearMap.eq_adjoint_iff` plus `collLp_inner_adjoint`. That lemma applies `adjoint_pair` to w(E)K and uses the fact that w(E) commutes with the angular operator (`hcomm`), which is why the L²(w dν) adjoint equals the dν adjoint. Boundedness is proved by `collLp_norm_le`, ‖L‖ ≤ max(τmax,0)(\|Pmax\|σ(S)+1). `photon_collCLM_selfAdjoint` shows the Thomson operator is self-adjoint on L²(F_b(1+F_b)dν). |
| 2e | Non-vacuity | PASS with note N1 | `nonvacuity_bounded_witness` instantiates every T5 hypothesis (MB statistics, Bool×Bool, counting measure) with f≠g and collEvec≠0. T9 (BE, photon, envelope A5) has no Lean witness. My numerical check shows its hypotheses are satisfiable with f≠g: g=F_b/2, f=g(1+0.5μ), b=C=1 gives D_BE=0.5793 (finite), ∫δ²/W=0.5236 ≤ 2D. For K=Eμ, e=−6.80 and e²/(‖L*K‖²·2D)=0.367 ≤ 1, consistent with (A4) when m=0. |
| 3a | Integrity of hashes | PASS | Recomputed for all 19 receipts: the stdout/stderr hashes and every `.source.lean` snapshot hash match. Current sources match compile_16 (main), compile_18 (hilbert) and compile_19 (audit). The 11 import source paths hash as recorded. All 13 oleans in raw/imports match AUTHOR_RETURN. `compile_14`/`compile_15` intentionally mismatch the current file: they are the retained failed attempts (exit 1, errors at :176/:346/:517 and :519). Probes 12, 13 and 17 also exit 1 and are retained. |
| 3b | Forbidden tokens | PASS | `grep -nE "\b(sorry\|admit\|native_decide\|sorryAx\|axiom\|set_option\|maxHeartbeats\|unsafe\|implemented_by\|extern)\b"` over both lean/*.lean: no hits. The only hit in raw/AxiomAudit.lean is the word "axiom" in a doc comment. |
| 3c | Axioms | PASS | The author's compile_19 stdout shows 72 of 72 declarations with [propext, Classical.choice, Quot.sound]. My own audit file `MyAudit.lean` (72 `#print axioms`, one per public decl/instance/structure of both modules, enumerated by grep) gives the same: 72 of 72, nothing else. |
| 4 | Independent recompile | PASS | Copied the 11 dependency sources from their original paths plus both target sources to `scratchpad/g12-a_rerun/src`. From cwd `/home/cosmosapjw/lean_oracles/viii_oracle` I ran `lake env bash -c "LEAN_PATH=$SC/imports:$LEAN_PATH lean -R $SC/src -o $SC/imports/<M>.olean $SC/src/<M>.lean"` for all 13 modules in dependency order. Every exit was 0; output was linter warnings only (unused section variable, unused simp argument). The audit run also exited 0. Toolchain: Lean 4.31.0 (commit 68218e87), mathlib fabf563a7c95a166b8d7b6efca11c8b4dc9d911f. The G12AHilbertAdjoint olean is bit-identical (068436f5…). The G12AContinuumAdjoint olean differs by 64 bytes, which is path-dependent metadata and not a concern. |

## Blocking findings
None.

## Non-blocking notes
- **N1. T9 has no formal witness.** There is no Lean witness that the photon BE instance (envelope A5) has f≠g with finite ε. I showed it numerically above. *Optional fix:* add a `photon_nonvacuity` theorem, e.g. g=F_b/2 and f=g(1+½μ) with a finite Dext bound, or reuse G12-D's `nonvacuity_temperature_instance` pattern.
- **N2. The literal (A7) form is only conditionally bridged.** The source writes e_j=⟨K_j,Lf−Lg⟩. The theorems use ⟨K_j,L(f−g)⟩, and `collEvec_eq_sub` connects the two only under the section-integrability premise `hsec`. That premise is not discharged in T5/T9, though it is immediate for the photon instance since \|P f\| ≤ Pmax·F_b(E), which is finite for E>0, and σ is finite. *Optional fix:* a corollary `photon_hsec`.
- **N3. g must be strictly positive.** The reference occupation needs g>0 a.e. (`dom .BE = Ioi 0`), while source A5 says 0≤f,g. This is the inherited G11-A convention, and since D_BE=∞ where g=0 and f>0 it is a mild narrowing. AUTHOR_RETURN does not mention it explicitly; it should be disclosed.
- **N4. Layer 2 needs an energy-only weight.** T5 and T10 require W=w(E). Source (A2) allows W(E,e). Layer 1 (T4/T6) covers a general W with hLK/hG/hloss kept as premises. This is disclosed.
- **N5. The freeze is evidenced only by mtimes.** The evidence is file mtimes plus the sha file, and the whole T directory is untracked in git (`?? …g12a…/`). The timestamps are internally consistent.
- **N6. Generalizations beyond the source are harmless.** τ and P are sign-unconstrained (only \|·\| ≤ max is assumed). C is unconstrained; C≤0 makes the measure zero, so statements are trivially true. Symmetry and normalization of P are not assumed outside T9 (normalization is checked numerically, not proved).
- **N7. Process items.**
  - T10 sits in a second module; this amendment is disclosed.
  - The author's observed runtime is UNKNOWN.
  - Lint warnings only.

## Code defect vs method limitation
- No code or proof defect found.
- Method limitations (disclosed, not defects):
  - The bounded-route sufficiency conditions (bounded τ, bounded kernel, finite σ, energy-only W).
  - The unbounded-τ / unbounded-kernel adjoint domain is only reached through the layer-1 premises.
  - The scalar elastic rest-frame model.

## Not proved
- Scientific admission: **HOLD**.
- Legendre eigenvalues p_0=1, p_2=1/10, p_l=0 and kernel normalization: these belong to G12-B / CAS12-C02. I checked them numerically only.
- A Lean non-vacuity witness for the T9 photon instance (N1), and discharge of `hsec` for the literal (A7) Lf−Lg form (N2).
- Physical certification of τ(E), the medium and scatterer frame, ε, W and the actual channel kernels.
- Polarized, frequency-redistributing or nonlinear (Compton) collision operators.
- Unbounded-rate or unbounded-kernel adjoint domains beyond the explicit layer-1 hypotheses.
- Any real-data, solver or production use.

## Proposed VALIDATION_MATRIX scientific-row update (not applied)

`G12-A | TEFF-A3 continuum adjoint + collision ellipsoid | Formal: FORMALLY_CHECKED_SCOPED (fresh independent review PASS_WITH_NOTES, claude-opus-5-5, 2026-10-14; independent recompile of 11 deps + 2 modules exit 0, 72/72 decls axioms ⊆ {propext, Classical.choice, Quot.sound}) | Scientific checks: operator/adjoint/dν faithful to S:130-141; adjoint pair numerically verified (Thomson and non-symmetric kernel, rel err ≤3e-15); p_l Funk–Hecke values reproduced numerically; τ(E)×score product and COLL-TAU control verified | Notes N1–N7 (T9 Lean witness absent; hsec undischarged; g>0 convention; energy-only W for layer 2; mtime-only freeze) | Scientific admission: HOLD`

## Relevant paths
- Under T:
  - `T/FROZEN_TARGETS.md`
  - `T/SOURCE_RECOVERY.md`
  - `T/AUTHOR_RETURN.json`
  - `T/lean/G12AContinuumAdjoint.lean`
  - `T/lean/G12AHilbertAdjoint.lean`
  - `T/raw/AxiomAudit.lean`
  - `T/raw/compile_14..19_*.json`
- Reviewer scratch (`/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/g12-a_rerun/`):
  - `build.sh`, `build.log`
  - `MyAudit.lean`, `MyAudit.out`
  - `numcheck.py`
  - `src/`, `imports/`

