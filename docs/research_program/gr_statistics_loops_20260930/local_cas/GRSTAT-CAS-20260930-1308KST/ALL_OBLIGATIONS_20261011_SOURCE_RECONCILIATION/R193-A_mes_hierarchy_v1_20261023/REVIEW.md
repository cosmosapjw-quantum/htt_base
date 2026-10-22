# R193-A — independent review (verbatim final report of a fresh read-only reviewer)

# R193-A independent review: MES primary source and covariant hierarchy

**Verdict: PASS_WITH_NOTES.** The packet is sound and internally honest, and nothing blocks the packet itself. Its main finding is confirmed independently: the ε''₂ coefficient 6/5 in MESa (52) has a genuine derivation gap. That puts the live geodesic W² anchor (3.3789e-13) at risk. This is a finding about the source and the anchor; it is not a defect in the packet. Status PARTIAL is correct. Scientific admission: HOLD.

Reviewer model: claude-opus-5-5 (Opus 5.5). This was a fresh read-only review. No repository file was edited and no git state was changed. Scratch files are only in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r193-a_rerun/`.

Task directory (T): `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/ALL_OBLIGATIONS_20261011_SOURCE_RECONCILIATION/R193-A_mes_hierarchy_v1_20261023/`

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Card read; SOURCE_RECOVERY citations | PASS | `unzip -p …/tasks/R193-A.json \| sha256sum` = `ace3eddc…6efb`, same as `raw/card_R193-A.json`. Package hash = `2d0b6da9…af6f`. Every cited file was re-hashed and matches its recorded prefix: pr_backlog `5cf688f2…b935`, crosswalk `92b7332a…b496`, EXEC_PLAN `fdffc914…924f`, MESa layout `4ffe1173…a6c`, plain extraction `d500ffee…217e`, companion `95f30a3c…bdab`, SAG TeX `00bb2c7c…370e`, revival_mes_attribution `a0bad4d4…d25d`, mes_theorem_authority `d149d859…87af8`, egs3 `8051e61e…ec6f`. I spot-read the cited line ranges: MESa conventions at ll.117-134, (5)-(14), (26)-(29), (41), B1-B3, (46)-(52), C1/C2 and (59)/(60); SAG (3)/(4) and erratum (17)-(19); companion l.167-171; PR-193 at l.6150. All are as described. |
| 1b | FROZEN_TARGETS predates first compile | PASS | FROZEN_TARGETS.md mtime is 03:09:13. `raw/FROZEN_TARGETS.presha256` (03:09:27.242) records `c265083f…9d36`, which equals the current hash. compile_01 started at 18:09:27.286Z (03:09:27.286 KST). The diff between compile_01 and compile_02 sources changes only proofs (sum_comm/gcongr rewrites, `noncomputable section`, simp args). No statement changed. |
| 1c | Frozen-target faithfulness (quantifiers, norms, signs, branches) | PASS (notes N3, N4) | Norm is Frobenius, matching MESa's \|Q\|=(QQ)^½. Strict `<` matches B1-B3 and (51)/(52). One-event pointwise quantification is used, and this is the same structure as MESa's "any event after last scattering". `ShearRel` matches MESa (12)/(14)/(41) with μ̇⁽⁰⁾ = −(4/3)Θμ (the ∇̂·q correction is O[2] when it multiplies τ₂). `VortRel` matches MESa's stated route for (52): "(27), using ∇̂_b(13) to get \|∇̂_a∇̂_bμ\|", plus (26) for an O[1] vector, which MESa states for "any O[1] spatial tensor". `VortBounds` matches (44)/(45). The `kq ≥ 0` hypothesis covers both branches. |
| 1d | Key identities by hand and numerically | PASS | See the adversarial items below. Scripts: `…/r193-a_rerun/check_gw.py` and an inline python run. |
| 2 | No assumed conclusions, no vacuity | PASS (note N4) | I instantiated `ShearRel 2`, `VortRel` and `MomRel` from the packet's own witnesses in my audit file. All three typecheck, so no hypothesis set is empty. No physical-necessity theorem takes an `Adopted*` predicate as a hypothesis. |
| 3 | Integrity | PASS | Lean `2f19f903…b3bcb` equals the compile_02 snapshot. AxiomAudit `ca166af9…3ac1` equals the compile_03 snapshot. Receipts: compile_01 exit 1, with the failure kept (stdout hash `9cb5990e…` verified); compile_02 exit 0; compile_03 exit 0; all stderr are empty (`e3b0…`). Running `grep -nE "sorry\|admit\|native_decide\|^\s*axiom\|set_option\|opaque\|implemented_by\|extern\|unsafe\|macro\|elab"` on the Lean returns no matches (rc=1). compile_02 stdout contains only linter and deprecation warnings. |
| 4 | Independent recompile and axiom audit | PASS | In cwd `/home/cosmosapjw/lean_oracles/viii_oracle` (Lean 4.31.0, toolchain v4.31.0, manifest mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`) I ran `lake env bash -c "LEAN_PATH=$S:$LEAN_PATH lean -R $S/src -o $S/R193AMesHierarchy.olean $S/src/R193AMesHierarchy.lean"`. Exit 0, 0 errors, 55 s. My own `audit/ReviewAudit.lean` runs `#print axioms` on all 62 theorem/lemma declarations; it exits 0 and all 62 report `[propext, Classical.choice, Quot.sound]`. The olean hash differs from the author's (`56d75b0f…` vs `b35db3c1…`). That is expected for a different output path and is not significant. |

## Adversarial focus items

**(1) MESa (52) ε''₂ = 6/5. Confirmed as a genuine derivation gap in MESa, not a formalisation that is too weak.**
- **Witness tensor recomputed in numpy.** Gw is symmetric in (b,c) (True), symmetric in (a,d) (True), and trace-free in (a,d) (True). ‖Gw‖² = 40, ‖contrB Gw‖² = 50, ‖asym contrB Gw‖² = 50.
- **Gw is extremal.** The typed subspace (symmetric derivative pair × STF tensor pair) has dimension 30. On it, the operator norm of asym∘contrB is 1.1180340 = √(5/4). Gw reaches it: 50/40 = 5/4.
- **W3 numbers.** ‖ω‖ = (6/5)·√50 = 6√2 = 8.4853, against the printed right-hand side 7.92. At the tight ε''₂ = ‖Gw‖ the ratio is exactly √(5/4).
- **The formalised relation set is MESa's own relation set.** I re-derived MESa's route by hand. MESa (49), |(∇̂q)˙| < (4/9)μΘ²(3ε'*₁ + 4ε'₁), is exactly the Lean `dqdot` relation. Adding (Θ/3)∇̂q from (26) and (4/3)Θ∇̂q, then multiplying by 3/((4/3)μΘ²), reproduces 9ε'₁ + 3ε'*₁ exactly. The only remaining step is ‖∇̂_b∇̂^cπ_ac‖ against ‖∇̂∇̂π‖, and the printed 6/5 needs a contraction factor κ = 1 there.
- **MESa's own convention elsewhere is κ = 3 per single contraction.** (50) gives 3·κ·(8/15)·3H·ε'₂ = 72/5 only when κ = 3. (51) gives κ·(3/7) = 9/7 only when κ = 3. With κ = 3, (52) would read 18/5 and (60) would read (2/5)ε₂. So MESa is internally inconsistent.
- **Could extra structure rescue 6/5?** I checked for anything MESa might use beyond typing:
  - B3 bounds the full tensor norm.
  - The Ricci identities (28)/(29) only add an O[1] antisymmetric piece of size k/S² in curved backgrounds. They do not shrink the space; the witness is the k = 0 case.
  - The constraints (20)-(24) involve the free fields E, H and σ, so they do not restrict the 2-jet of π at an event.
  - I found no such structure.
- **Caveat.** It is open whether a full Einstein-Boltzmann solution realises the violation. The packet correctly does not claim this.

**(2) MESa (14) ∇q coupling, printed 2 against derived 2/5. Confirmed.** I multiplied (10) by (8π/15)E² and integrated:
- −(1/3)Θ∫E⁴∂_EF_ab gives +(4/3)Θπ.
- −σ∫E⁴∂_EF gives (8/15)μσ.
- The ∇̂_<aF_b> term with coefficient 1 gives (8π/15)/(4π/3) = 2/5.
- The (3/7)∇̂·F₃ term gives (3/7)(35/15) = 1.

Coefficient 1 on ∇̂_<aF_b> in (10) is the standard harmonic projection, and the 2/5, 1/3 and 3/7 couplings in (8)-(10) are also standard.

**(3) (51) coefficients. PASS.** The no-cancellation route gives (8/15)μΘ[(8/3)ε₂ + ε*₂], 2·(4/3)/(8/15) = 5, and 3·(8/35)/(8/15) = 9/7. Reduction under C1/C2: 8/3 + 1/3 = 3 (whereas 3/8 + 1/3 ≠ 3), and (9/7)/3 = 3/7 (whereas 7/27 ≠ 3/7). SAG (3) in clean LaTeX gives 5/3, 3, 3/7. The layout fraction glyph order is mixed: "34" is 4/3 but "13" is 1/3. So the reduction argument is the decisive adjudication, as the packet says. The Lean proves (51) as a consequence (√3·3/7 ≤ 9/7), and S3 shows the sharper kq = 2/5 bound implies it.

**(4) SAG erratum (17) and MESa (46)/(41). PASS.** Lean proves `sagFactor_eq` for all L. I checked it independently with exact fractions for L ≤ 11, and L = 2, 3 give 15/2 and 35/2. The (46)×(41) coefficient products are 1, 1, 1. The identity ⟨τ_Aτ^A⟩ = (2L+1)!!/L! ΔT_L² matches Σ|a_lm|² = (2L+1)C_L with ∫e^<A>e_<B> dΩ/4π = κ_L Δ (prose only; not derived in Lean, and the packet discloses this).

**(5) No acceleration ceiling (A2). The witness is genuine and physically realisable.** The witness sets ∇̂μ = −4μu̇, which is exactly radiation-fluid Euler balance, (4/3)μu̇ = −(1/3)∇̂μ: a radiation-comoving frame with zero dipole and a pressure gradient. The coupling (4/3)μu̇ matches standard radiation momentum conservation. The claim that (14) and the O[1]-tensor (26) gain no O[1] acceleration term is right, since every such term is u̇ × O[1] = O[2].

**(6) Physical necessity vs adopted assumptions, and print-only coefficients. PASS.**
- P1-P3 have no `Adopted*` hypotheses.
- C1, C2, ε₁ = 0 and the strict hierarchy are separate defs.
- `reduce_*` take C1/C2 as explicit, labelled hypotheses.
- `grep 2/7|3/14|MESb` in the Lean finds nothing, so MESb coefficients are never used.
- H3 refutes the forbidden claim "ε₁ = 0 unique by hierarchy".

## Blocking findings

None for the packet.

**Downstream finding to route to the anchor owner.** This is outside the scope of this packet. The frozen anchor `FROZEN_W2_MAX = 3.3789222980376e-13` (`htt/src/common/revival_mes_attribution.py` l.16-36) is exactly (3/2)((2/15)ε₂)², with ε₂ = 3.5596e-6. It therefore rests on the unsupported 6/5. By PR-193's DoD (a coefficient that disagrees with its derivation fails the admissibility claim), the anchor and ε₁_crit = (43/25)ε₂ + (9/35)ε₃ cannot be presented as derived from MESa plus C1/C2.

Valid replacements at the same ε₂:

| Basis | W² factor | Ceiling | ε₁_crit coefficient on ε₂ |
|---|---|---|---|
| Formally proved, √3 (`cs_ceiling_factor`) | ×3 | 1.01368e-12 | 1.6614 |
| Sharp typed √(5/4), numerical only | ×5/4 | 4.22365e-13 | 1.7106 |
| MESa-internal κ = 3 convention | ×9 | 3.04103e-12 | 1.56 |

The current anchor is tighter than any valid bound, so it is not conservative.

Smallest fixes:
- Either mark `MESa_52_omega_eps2pp` as DERIVATION_GAP in the anchor's provenance and keep the number only as a labelled historical value,
- or adopt the proved √3 ceiling.

The missing test is a regression asserting that the ε₁ = 0 ceiling equals 3×(3/2)((2/15)ε₂)² under the proved coefficient, or else that the anchor carries a derivation-gap flag.

## Non-blocking notes

- **N1.** "Glyph unresolved" for (14) is more cautious than needed. The printed coefficient is 2, and three facts inside the source show it:
  - The trace term is −(2/3)h∇̂·q. That pairs with 2·STF; the 2/5 reading would need −2/15, so two glyphs would have to be lost.
  - (51) contains 5ε'₁, which needs 2.
  - The plain extraction agrees.

  So the branch is a source error (2 printed, 2/5 by physics), not a transcription question. Both readings give a valid (51), so nothing changes in outcome.
- **N2.** The packet's "valid coefficient (6/5)√3" is valid but not sharp. On the typed space the sharp value is (6/5)√(5/4) ≈ 1.342 (numerical only, `raw/probes/opnorm.out` and my rerun). Reports should say "valid, non-sharp".
- **N3.** `AdoptedC2Jet` is an equality-at-the-jet proxy for MESa's C2, which is an estimate on bound constants. That makes `C2_not_forced` close to trivial. `strict_hierarchy_not_forced` is purely arithmetic about constants, and its ShearRel state is decoration. Both are honest, but they are weak evidence. `AdoptedEps1Zero` is defined and never used.
- **N4.** W3 uses O(1) amplitudes (ε''₂ = 13/2). The statement is homogeneous of degree 1, so it is equivalent to any small amplitude, but a remark saying so would help readers.
- **N5.** `dust_forces_geodesic` is close to a tautology: it takes ρu̇ = 0 as given. Its physical content is in the hypothesis, which comes from the dust equation of state.
- **N6.** Observed runtime is recorded as UNKNOWN, which is consistent with policy. Independent review is now done; the other axes (Wolfram/xAct, sympy, Sage/Singular) remain NOT_RUN.

## Counting recommendation

Count R193-A as **PARTIAL**. All 31 frozen target groups (62 declarations) are proved at one-event, O[1], one-jet scope. Do not count it as closing PR-193's "source coefficient equality".

Coefficient branches:

| Branch | Status |
|---|---|
| MESa (51) σ (8/3, 1, 5, 9/7) | SOURCE_EQUAL (valid, non-sharp) |
| MESa (59) σ (5/3, 3, 3/7) | SOURCE_EQUAL under ADOPTED C1/C2 |
| MESa (52) ε'₁ = 9, ε'*₁ = 3 | SOURCE_EQUAL |
| MESa (52) ε''₂ = 6/5, hence (60) 2/15 | DERIVATION_GAP / FAILED, **not** source-blocked (transcription is confirmed) |
| MESa (14) ∇q coupling | SOURCE_INTERNAL_INCONSISTENCY (2 printed, 2/5 derived); not consequential for (51) |
| MESb non-geodesic ω/A coefficients (3/4, 2, 2/7), (3/4, 1, 3/14) | **SOURCE_BLOCKED** (print-only, absent from repo) |
| Pre-erratum SAG eq (17) | **SOURCE_BLOCKED** (only for historical reconciliation; the corrected form is verified) |
| Angular moment identity κ_L | DERIVATION_BLOCKED (not formalised) |

## VALIDATION_MATRIX scientific row (proposed; not applied)

`R193-A | scientific | PASS_WITH_NOTES (independent review 2026-10-23, claude-opus-5-5) | (51) PASS; (52) ε'1,ε'*1 PASS; (52) ε''2 6/5 FAIL (derivation gap, Gw witness ‖asym∘contr‖²=50>40, typed op-norm √(5/4)); (14) source error 2 vs 2/5 (non-consequential); SAG (17) PASS ∀L; A2 PASS; physical/adopted separation PASS; MESb + pre-erratum SAG SOURCE_BLOCKED; downstream: FROZEN_W2_MAX and ε1_crit rest on the failed branch → admission HOLD`

## Not proved (always)

- Scientific admission: HOLD.
- That MESa (52) fails for actual Einstein-Boltzmann solutions (W3 is relative to `VortRel`).
- O[2] remainder control.
- The angular moment identity κ_L, and the Boltzmann harmonic projection itself (prose and ledger only).
- The sharp constants √(5/3) and √(5/4) (numerical only).
- MESb coefficients and the pre-erratum SAG eq (17).
- Physical validity of the adopted C1/C2 and of the strict hierarchy (shown not forced).
- Any re-freeze of FROZEN_W2_MAX (not done, and not authorised by this review).
- CAS-axis agreement.

## Reviewer scratch files

All in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r193-a_rerun/`:
- `src/R193AMesHierarchy.lean`
- `R193AMesHierarchy.olean`
- `main.stdout`, `main.stderr`
- `audit/ReviewAudit.lean`
- `audit.stdout`
- `check_gw.py`
- `decls.txt`
