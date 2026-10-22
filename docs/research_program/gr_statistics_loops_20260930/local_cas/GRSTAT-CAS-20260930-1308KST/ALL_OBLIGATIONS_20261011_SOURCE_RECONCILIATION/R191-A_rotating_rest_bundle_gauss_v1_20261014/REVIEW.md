# R191-A — independent review (verbatim final report of a fresh read-only reviewer)

# R191-A independent review: rotating rest-bundle canonical Gauss object

**Reviewer model:** Claude Opus 5.5 (`claude-opus-5-5`). I ran a fresh, read-only review. I edited no repository file, ran no state-changing git command and spawned no subagents. All scratch work is under `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r191-a_rerun/`.

## Verdict: PASS_WITH_NOTES
- **Formal proof:** passes in its pointwise / chart scope.
- **Scientific admission:** HOLD.
- **Blocking findings:** none.

**Key finding confirmed independently.** Take the projected rest-bundle connection ∇^H = h∇ and compute its curvature with the full bracket. Its double trace is projR − θ² + V_ab V^ba. That is the transposed (Ellis, −ω²) contraction. The source's same-order R3 = projR + V_ab V^ab − θ² is larger by exactly 2 ω_ab ω^ab.

I confirmed this three ways:
1. **By hand.** F(X,Y)Z = hR(X,Y)Z + ⟨u,∇_Y Z⟩∇_X u − ⟨u,∇_X Z⟩∇_Y u. This gives F_{ij,kl} = R_{ijkl} − V_ki V_lj + V_li V_kj, whose trace over i=k, j=l is projR − θ² + V_kl V_lk.
2. **By exact rational sympy** on random charts.
3. **By an independent field-level computation.** I worked in coordinates with a real metric 2-jet and a real Riemann tensor, using coordinate 2-form slots, so no frame or bracket bookkeeping is involved.

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Card read first | PASS | `unzip -p …zip …/tasks/R191-A.json`. The card hash is a5160d07…a9b, which equals `raw/card_R191-A.json`. The zip hash 2d0b6da9… matches what SOURCE_RECOVERY records. |
| 1b | Source citations | PASS with a minor error | Hashes match the recorded values: pr_backlog 5cf688f2…b935, egs3 608b4cf9…b236, roadmap 869e11f9…a306, DOSSIER 00c1fcb0…5ebd, COMMON_SPEC 4714827e…97ff. PR-191 sits at :6004-6077 with targets :6022, dod :6035, kill :6040, forbidden :6053. Roadmap :269-297, steelman H03 :27-31 and H17 :111-115, backlog :55-63, crosswalk :25, plan :138-142, DOSSIER :86, COMMON_SPEC :10-11, egs3 :195, :210-221, :371-412 (ordering disclosure :378-386), :481-485, registry :731-752 and Wolfram :108-122 all read verbatim. **Error:** the Riemann convention is cited as egs3 `:120-121`, which is the metric. The real definition is `:132-151` (R^l_{mkn} = ∂_kΓ^l_{nm} − …), i.e. Rdn[l][m][k][n] = ⟨∂_l, R(∂_k,∂_n)∂_m⟩. That is the same convention as Lean `riem A B C D = ⟨e_A,R(e_C,e_D)e_B⟩`, so nothing else is affected. |
| 1c | Resume addendum is append-only | PASS | `git diff` on SOURCE_RECOVERY.md shows 22 insertions and 0 deletions. The first 103 lines are byte-identical to `git show HEAD:` (blob from commit 6365e36d). |
| 1d | FROZEN_TARGETS written before the first compile | PASS (mtime evidence only; untracked) | FROZEN mtime is 02:46:42 KST. compile_01 started 17:46:48Z, and the first main compile (compile_04) started 17:48:54Z. Diffing compile_04→05→06→07 shows only proof-script changes, plus `def`→`noncomputable def restOmega` and a new helper `vec111_apply`. No theorem statement changed. |
| 1e | Faithfulness to the card | PASS_WITH_NOTES | **lean_step 1:** projector, jet and connection are recovered verbatim; there is no PR-187 module, so the card's fallback was used. **lean_step 2:** T1–T4. **lean_step 3:** T7/T9 exact equalities. **lean_step 4:** T10/T11/T12. **A1:** T8/T9. **A2:** T13–T17. **Pitfall:** the canonical object is called `restCurv` and "orthogonal metric" appears only in a disclaimer (see note N2). **Strengthenings, all acceptable:** T7 holds for any symmetric ginv; T10 drops the second-order O(3) constraint on ν; `riem` takes arbitrary dγ. **Weakenings, all disclosed in FROZEN / AUTHOR_RETURN:** Frobenius is pointwise only; the gauge result covers the fibre only; T5 is frame-evaluated only; the xAct / SymPy / Sage axes were not run. |
| 1f | Key finding (transposed contraction; gap of 2ω²) | CONFIRMED | Hand derivation above. `num_check.py`: 200 random Compat γ and dγ give \|T4\| ≤ 1.8e-15, \|rest − trans\| ≤ 3.6e-15 and \|rest − (same − 2ω²)\| ≤ 5.3e-15, while min \|same − rest\| = 0.082 (≠ 0). `chart_exact.py`: 5 exact rational Lorentzian charts with unit u give same − trans − 2ω² = 0 exactly, and the verbatim source `trVV` pattern h^{ac}h^{bd}V_ad V_cb equals same-order exactly. `jet_check.py` is the independent field-level run (results below). |
| 1g | T7 / T9 numerics on random data | PASS | T9: frame residual ≤ 5.3e-15 over 200 trials. T7: exact zero on 5 rational charts. (A float chart run showed ~1e-5 residuals; these come from conditioning, and the exact runs remove them.) |
| 1h | T10/T11: fibre O(3) covariance vs dependence on slice-type convention | PASS | Random O ∈ O(3) from QR, l = O·K with K skew, ν with prescribed skew part and random symmetric part. \|curvForm′ − OᵀFO\| ≤ 1.2e-14. \|sliceForm′ − (Oᵀ S O + c⁰_CD Oᵀ l₀)\| ≤ 1.2e-14, and the shift itself is about 1.05, so it is not trivially zero. The by-hand Leibniz expansion matches `gaugeA` / `gaugeDA`. |
| 1i | T12 index-convention flip | PASS, correctly labelled | Transposing D leaves both scalars unchanged (float ≤ 3e-5 from conditioning; the Lean proof is exact) and flips the sign of ω. The theorem is honest: the derivative-first vs velocity-first convention cannot absorb the 2ω² same/trans gap, so that gap is real content and not an index-order artefact. |
| 1j | Negative controls are real | PASS | N2: the (0,1) entry differs by −1 for every dγ. N3: same-order minus canonical equals 1 for every dγ; by hand, ω² = 1/2 at γW, so 2ω² = 1. N4: the vertical bracket cW⁰₁₂ = 2 ≠ 0 and the shift is nonzero, though the witness uses only O = 1, A = 0. N1 instantiates Compat with ω ≠ 0. |
| 2 | No circular hypotheses or vacuity | PASS | I checked that each hypothesis is satisfiable: Compat by γW; ω = 0 by γ = 0; the T10 hypotheses by `gauge_witness_hyps`. My own `example`s prove `∃ γ, Compat γ ∧ restOmega γ ≠ 0` and gaussSame ≠ restScalar at γW for every dγ. |
| 3 | Integrity | PASS | Recomputed sha256 of the main source, AxiomAudit.lean, run_compile.py, the card, all 8 `.source.lean` / stdout / stderr receipts and the 4 oleans: all match AUTHOR_RETURN and the receipts. compile_07 (final) equals the live `lean/` file and compile_08 equals the live AxiomAudit.lean. Exit codes: 01–03 are 0; 04 and 05 are 1, failed attempts kept; 06 is 0 with one unused-simp-arg warning; 07 is 0 with empty stdout; 08 is 0. The imported P03-A / VelocityJetRest / PortCas01 sources hash to f67b8822…, 0d696565… and e289039f… and are git-clean. P03-A RETURN is FORMALLY_CHECKED_SCOPED with review PASS_WITH_NOTES. Grep for sorry, admit, native_decide, axiom, set_option, opaque, implemented_by, extern, unsafe, #eval in `lean/` finds nothing (rc = 1). |
| 4 | Independent recompile | PASS | Toolchain `leanprover/lean4:v4.31.0`, mathlib rev fabf563a7c95a166b8d7b6efca11c8b4dc9d911f. I rebuilt all imports from source into scratch `imports/` without using the author's oleans: VelocityJetRest exit 0, PortCas01 exit 0, P03-A exit 0 with a lint warning. Then `lake env bash -c "LEAN_PATH=$S/imports:$LEAN_PATH lean -R $S/src -o $S/imports/RotatingRestBundleGauss.olean $S/src/RotatingRestBundleGauss.lean"` gave **exit 0 with empty output**. My audit `audit/ReviewerAudit.lean` runs `#print axioms` on all 47 public theorems. All show [propext, Classical.choice, Quot.sound], except `ring_core`, which shows [propext]. Restated T7, T9 and T13 type-check against the frozen text. Exit 0. My list of public theorems matches the author's audit list exactly. |

**Independent field-level check (`jet_check.py`).** It uses exact 2-jets of a random curved metric and a random velocity field over 6 seeds. ω² ranges from 0.031 to 1.01.
- \|rest − (projR − θ² + V_kl V_lk)\| ≤ 1.6e-15.
- rest − same equals −2ω² to 9 digits in every seed.
- The 4-index F matches the T4 pattern to ≤ 9.7e-16.

## Blocking findings
None.

## Non-blocking notes
- **N1 – how independent is the "tensor derivation"?** In Lean, the tensor side (`gaussTensor` / `gaussTrans`) is a posited formula. SOURCE_RECOVERY §4 says its index pattern was "forced by the frame identity". Both sides are proved from the same frame data model, so A1 "two independent derivations" holds formally only in a weak sense. My coordinate computation supplies the missing independence numerically, not as a proof.
  - *Smallest fix:* add a chart-level tensor lemma F(X,Y)Z = hR(X,Y)Z + ⟨u,∇_Y Z⟩∇_X u − ⟨u,∇_X Z⟩∇_Y u, or run the xAct axis the card requests.
- **N2 – naming next to the pitfall.** The contrast object is named `sliceCurv` / `sliceForm`. It is disclaimed in docstrings and shown to be frame-dependent (T11, N4), but an identifier that reads as "slice curvature" sits uncomfortably close to the pitfall.
  - *Suggestion:* rename in a future version (e.g. `verticalDroppedForm`); the current file is acceptable as is.
- **N3 – "canonical" scalar is only half proved invariant.** Invariance of `restScalar` under a triad rotation needs both fibre covariance (T10) and tensoriality in the 2-form slots. The second is not proved; this is disclosed. My coordinate computation is tensorial by construction and corroborates it numerically.
- **N4 – where the source's same-order R3 comes from.** I verified it numerically: in the co-rotating triad gauge ⟨e_k, ∇_u e_l⟩ = ω_kl, the slice-type scalar equals the source same-order R3 to within 1.8e-15. So the source's β = +1 object is a gauge-fixed, convention-dependent slice-type expression, not the curvature of the rest-bundle connection. This fits T11 and is worth recording for the PR-191 kill criterion ("convention-dependent quantity described as invariant").
- **N5 – downstream wording to propagate (read-only flag, not an R191-A defect).** Two places describe the β = +1 identity R3 = 2G_uu − ⅔Θ² + σ² + ω² as "(3)R on the non-integrable rest space": `docs/research_program/THEOREM_REGISTRY.yaml:731-752` (KE-FRAME, C2 ACTIVE) and `docs/research_program/egs3/tickets/t3_king_ellis.yaml:123-125`. The canonical rest-bundle curvature has −ω² instead, which matches Ellis. The egs3 module docstring discloses the ordering choice; the registry and ticket entries do not. The Wolfram twin uses the same contraction (`:115-116`), so it gives no independent check of the ordering.
- **N6 – small inaccuracies in AUTHOR_RETURN and FROZEN.** `first_failure` attributes the `noncomputable` error to compile_05, but it already appears in compile_04 stdout line 1. The helper `vec111_apply`, added in compile_05 after the freeze, is not in FROZEN's helper list. Also the egs3 `:120-121` citation error noted in row 1b.
- **N7 – `riem` has no Riemann symmetries.** It is built from free dγ. The identities hold anyway, which is a strengthening, but none of the theorems says anything about the 2G_uu identification (disclosed).

## Not proved (scientific admission HOLD)
- Field-level realization: frame fields, brackets as Lie derivatives, dγ as true derivatives.
- The real Frobenius theorem (existence of u-orthogonal hypersurfaces at ω = 0) and exact recovery of the standard ³R of an actual hypersurface; only pointwise algebra is proved.
- Tensoriality in the 2-form slots, so full triad-rotation invariance of `restScalar` is not proved.
- A chart-general 4-index `gaussTensor` identity and a chart-level tensor derivation of F.
- h h R = 2G_uu and any Einstein or field-equation content.
- The PR-191 maximal-class KE obstruction / existence classification.
- The Wolfram/xAct, SymPy-high-precision, Sage/Singular and Rocq axes required by the PR-191 `cas_contract` (missing axes mean CAS_BLOCKED for PR-191 as a whole).
- The independent-adjudication gate, which stays OPEN.
- publication_use, which stays false.

## Suggested VALIDATION_MATRIX scientific row (for the owner to record; I did not write it)
`R191-A | rest-bundle curvature (full bracket) double trace = projR − θ² + V_ab V^ba (Ellis −ω²); same-order source R3 − canonical = 2ω_abω^ab | Lean scoped PASS (47 theorems, std axioms, independent rebuild exit 0) + reviewer field-level 2-jet check (6 seeds, ≤1.6e-15) + exact rational chart check | PASS_WITH_NOTES | notes N1 (tensor side posited), N3 (slot tensoriality unproved), N5 (KE-FRAME β=+1 wording needs a convention qualifier) | scientific admission HOLD`

## Files
**Scratch (reviewer), in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r191-a_rerun/`:**
- `audit/ReviewerAudit.lean`
- `audit.out`
- `num_check.py`
- `chart_exact.py`
- `jet_check.py`
- `num_check_lib.py`
- `imports/` (rebuilt oleans)
- `src/` (source copies)

**Reviewed (task directory `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/ALL_OBLIGATIONS_20261011_SOURCE_RECONCILIATION/R191-A_rotating_rest_bundle_gauss_v1_20261014/`):**
- `lean/RotatingRestBundleGauss.lean`
- `FROZEN_TARGETS.md`
- `SOURCE_RECOVERY.md`
- `AUTHOR_RETURN.json`
- `raw/compile_0[1-8]_*`
- `raw/AxiomAudit.lean`

**Sources cited above:**
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/htt/obsstat/egs3_king_ellis_frame.py`
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/THEOREM_REGISTRY.yaml`
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/egs3/tickets/t3_king_ellis.yaml`
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/wolfram/ke_rotating_congruence.wls`
