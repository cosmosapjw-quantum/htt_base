# L2-W1-B — independent review (verbatim final report of a fresh read-only reviewer)

# L2-W1-B independent review: fibre-image branches on bounded and curved domains

**Verdict: PASS_WITH_NOTES.** There are no blocking findings. Scientific admission stays **HOLD**.

- **Reviewer:** claude-opus-5-5 (Opus 5.5, self-reported). This was a fresh read-only review; I did not write the unit and spawned no subagents.
- **Unit:** `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/typefree_loop2_closeout_20260928/l2w1b_fibre_image_branches_v1_20261014/` (written T below).
- **Scratch:** all my outputs are in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/l2-w1-b_rerun/`. I edited no repository file and ran no state-changing git command. The unit directory is still untracked (`??`).

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 0 | Card read first | PASS | I read `unzip -p HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip …/tasks/L2-W1-B.json`: 4 lean_steps, 2 acceptance items, 1 pitfall, sources `CLAIM_CLOSEOUT.json` and `PORT_MAP.json`. |
| 1a | Citations in SOURCE_RECOVERY | PASS | All citations check out. `CLAIM_CLOSEOUT.json:11-12` is TF-W1-KERNEL-DOMAIN, with text and caveats matching. The F4 entry of `PORT_MAP.json` lists `rational_polytope_fiber_support` and the limit "No general nonlinear feasible-set solver". `ERRATA_F1_W1_KO.md` (about lines 21-39) has the affine `k0+V` text, the negative control B=0, P=id, K=[-1,1], and the three distinct judgements. `formalism_mapping.md:101` has the augmentation recipe and the boundedness precondition. `typefree_fibers.py` has sha `6f5f9a01…3947910` and `joint_feasible_set.py` has `d7903c00…dcfe3474`, both matching. Commits bc45fb92 and 5aa4e7f9 confirmed. Line numbers confirmed: `L2W1KernelBound.lean` 26, 62, 90; `P08EllipsoidImage.lean` 43, 47, 52, 56, 114, 215, 238, 250, 330, 372; P08-A `Fib`/`fiber_branches` at 145 and 164. `grep -rli polytope --include=*.lean docs htt` finds nothing outside this unit, which confirms the "not recoverable" note. |
| 1b | Identity of the "existing support certificate" | PASS | `CLAIM_CLOSEOUT.json` contains no polytope certificate. The PORT_MAP F4 entry points to `common.typefree_fibers.rational_polytope_fiber_support`, which calls `common.joint_feasible_set.exact_support` (exact Fraction vertex enumeration). This is the right object. In Python the rows are ordered A, then (e_j ≤ hi_j, −e_j ≤ −lo_j) interleaved per coordinate, then B, −B. Lean `augMat`/`augRhs` uses A, all upper rows, all lower rows, B, −B. That is a pure row permutation with identical row vectors and right-hand sides. The Python direction `P.T*u` is the Lean `Pᵀ *ᵥ w` in `support_transport`. |
| 1c | Frozen targets predate the first compile | PASS | `FROZEN_TARGETS.md` mtime is 12:04:28.37 KST. `compile_01` started at 03:04:55 UTC (12:04:55 KST). `freeze_hashes.txt` records FROZEN `7f95b0c0…` (matches now) and the Lean file at freeze `d188ac78…`, which equals the `compile_06` (failed) source. My signature diff script parses all 68 frozen declarations and finds 0 mismatches against the final source, and the two sets of names are identical. |
| 1d | Faithfulness to the card | PASS | Detail in the next subsection. |
| 2 | No assumed conclusions, no vacuity | PASS | My checks are in `audit/ReviewAudit.lean` (exit 0). (i) The affine A3 theorem with x1:=x0 (hypothesis discharged by `simp`). (ii) A concrete ellipsoid instance (n=r=m=q=1, L=B=P=1, c=0, y=1/2, X=1, N:Fin1×Fin0=0): all of `IsMoorePenrose`, `IsKerONB`, compatibility and η≤1 are satisfiable, and `ellipsoid_branch` gives the image `{![1/2]}`. (iii) `rfl` re-check of E1. No hypothesis restates a conclusion. The polytope instance proofs are honest: `instance_fibreImage_eq` is proved directly by elimination, and max/min come through `support_transport`, `polytope_fibre_eq_aug` and `dual_certificate_*`. |
| 3a | sha256 of sources and receipts | PASS | Main Lean `891d4e41…`, AxiomAudit `c5c28151…`, `run_compile.py` `031e5975…`, SOURCE_RECOVERY `85ef421c…`, FROZEN `7f95b0c0…`, and both probe .py/.json files all match AUTHOR_RETURN. All 8 receipts' stdout, stderr and source-snapshot hashes match their JSON. `compile_07` source equals the final Lean and `compile_08` source equals `AxiomAudit.lean` (byte-identical). |
| 3b | Exit codes and failed attempt kept | PASS | Steps 01-05 exit 0; 06 exit 1 (retained, `Unknown identifier image_subset` ×3); 07 exit 0; 08 exit 0. The 06→07 diff touches proof terms only (see Note 2). |
| 3c | Axioms and forbidden tokens | PASS | `grep` for sorry, admit, native_decide, axiom, set_option, unsafe, implemented_by, extern, opaque, macro, elab in T/lean and the audit file finds nothing. My own `#print axioms` over all 42 public theorems: 38 use exactly [propext, Classical.choice, Quot.sound] and 4 use [propext, Quot.sound] (`mem_fibreImage`, `iUnion_fibreImage`, `fibreImage_nonempty_iff`, `fibreImage_subsingleton_iff`). This matches the author output exactly. |
| 4 | Independent recompile | PASS | Toolchain confirmed: `lean-toolchain` v4.31.0, mathlib rev `fabf563a…`. I copied all 6 sources to `scratch/src`; the copies' hashes equal the reviewed hashes. Rebuilding from cwd `/home/cosmosapjw/lean_oracles/viii_oracle` with `lake env bash -c "LEAN_PATH=<scratch>/olean:$LEAN_PATH lean -R <scratch>/src -o <scratch>/olean/<M>.olean <scratch>/src/<M>.lean"` gives exit 0 for ProjectionBridge, G08AWhitening, P08EllipsoidFiber, P08EllipsoidImage, L2W1KernelBound and L2W1FibreImage, with no errors (see Note 6). The audit file compiles with exit 0. |
| 4b | Olean identity | PASS (explained) | Scratch-path oleans for Bridge, P08-A and P08-B are bit-identical to T/raw/imports. G08A, L2W1A and the main module differ because the olean embeds the source path (`strings` shows the path inside). Rebuilding L2W1A from its original path reproduces `45d0c095…` exactly. Rebuilding the main module from `T/lean` against T/raw/imports reproduces `5e6d5649…` exactly. All 5 import oleans equal the reviewed units' own `raw/imports` oleans, so the claim `olean_bit_identical_to_reviewed_unit_oleans` holds. |
| 5 | Polytope support [0, 3/2] recomputed | PASS | `scratch/indep_lp.py`. scipy HiGHS: max 1.5 at (0.5, 0.5), min 0 at (0, 0); its duals are A-row 1.5 and equality 0.5. My own exact rational vertex enumeration on the Lean-ordered 7-row system finds vertices {(0,0), (1/2,1/2)} with objective {0, 3/2}. By hand, the fibre is x0=x1=s with s ∈ [0, 1/2], so P = 3s ∈ [0, 3/2]. Exact Fraction check: Mᵀ·lamMax = (1, 2) with value 3/2, and Mᵀ·lamMin = (−1, −2) with −(λ·h) = 0. Re-running the author probe gives exit 0 and identical JSON (EXACT_BOUNDED_POLYTOPE 0..3/2, 7 vertices including duplicates; y=3 gives EMPTY_SET). Re-running the Sage PPL probe gives identical JSON. |
| 6 | Probe retention | CONCERN (non-blocking) | See Note 3. |

### Faithfulness to the card (check 1d)

- **Step 1.** `Fibre := F ∩ B⁻¹'{y}` and `FibreImage := P '' Fibre` are defined for arbitrary `F : Set E` and arbitrary maps. This is the most general reading of "admissible", and the recovery note says the sources give "admissible" no further meaning.
- **Step 2.** A1 and A2 reduce to L2-W1-A `kernel_bound_iff` and `affine_kernel_bound`, both called directly. The forward direction instantiates the domain at x0+v and x0. The "affine = declared variation space V" caveat from ERRATA is respected.
- **Step 3a.** E1 is a genuine `rfl`: P08-B `FibreImage := (P*ᵥ·) '' (Ell c L ∩ {B*ᵥx=y})`, which unfolds to the general definition. E2-E5 transport P08-B theorems unchanged. The support term sqrt(1−η)·‖(PLN)ᵀw‖ equals the Python `sqrt(uᵀ(1−η)PLNNᵀLᵀPᵀu)`.
- **Step 3b.** R1-R7 are as described in check 1b.
- **Step 4.** The curved branch claims only the general image theorems G1-G6, L2 and L4, plus exact counterexamples. No support or computability result is stated for curved sets, so the pitfall is honoured. No nonlinear solver obligation appears, so the acceptance item is honoured.
- **Acceptance (distinct names and types).** `FiniteDomainBound (F : Set E)` over arbitrary maps, `DomainCoercivity (F : Set E)` and `GlobalCoercivity (V : Submodule)` over linear maps are three distinct definitions with distinct types.
- **`bounded_branch_separation` is genuine.** FiniteDomainBound holds on [-1,1] with B=0, P=id, while GlobalCoercivity and KernelInclusion fail. I additionally proved `¬DomainCoercivity` on the same data.
- **Recorded adjustment.** A3/A4 are stated for the nonempty fibre value `B x1`. This is not a silent weakening: it is documented, and the empty-fibre case is trivial.

### Curved counterexample: genuine

- **C2 by hand.** |t²−s²| = |t+s|·|t−s| ≤ 2|t−s| on [−1,1]². C1: v=(0,1) has B v = 0 and P v = 1.
- **The arc is not a flat-set artefact.** In the audit file I proved that (1,1), (−1,1) and (0,0) lie on the arc, and that KernelInclusion fails already on span{(1,1), (−1,1)} = ℝ² (the arc's difference span). So comparing against ⊤ is the natural linear analogue.
- **C6/C7.** The unbounded parabola has subsingleton fibre images but no DomainCoercivity (the witness t=C+1 gives t² ≤ Ct, a contradiction). This genuinely separates identifiability from a coercive bound, matching the ERRATA's three distinct judgements.

## Blocking findings

None.

## Non-blocking notes

1. **`universal_linear_iff_false` is weak as stated.** A flat singleton also witnesses it: I proved in the audit that F={0} has DomainCoercivity with C=0 while KernelInclusion ⊤ fails. The evidence that curvature matters lives in `curved_linear_iff_fails` together with the span fact above, which the unit does not state. Suggested optional addition: a lemma `¬ KernelInclusion (Submodule.span ℝ {x - x' | x ∈ arc, x' ∈ arc}) Bc Pc`, or `affineSpan ℝ arc = ⊤`.
2. **The `first_failure.cause` in AUTHOR_RETURN is incomplete.** Besides the three `image_subset` to `image_mono` fixes, the 06→07 diff also removes `Fin.sum_univ_two` from two `simp` lists (lines 571 and 603). These are proof-only edits that answer linter warnings. Signatures are unchanged (verified).
3. **Probes were not run through the compile harness.** Their argv, stdout and exit codes are not retained as receipts; only the output JSONs exist, and AUTHOR_RETURN states this. `frozen_signatures.lean.txt` is a text extraction and was never compiled. `probe_sage_lp.sage.py` is a Sage-generated preparse file: its hash is not recorded and my regenerated copy differs from the stored one (expected, since it is environment-generated). Both probes re-ran for me with identical JSON, so I see no hidden failure.
4. **One probe field is not evidence.** The `abs_t_plus_s_le_2_on_box` value in the sympy probe just echoes the inequality string. The Lean proof C2 is the authority for that bound.
5. **The polytope link is limited by design.** The polytope branch is over ℝ, with rational numerals only in the instance. The link to the Python certificate is row-structure equivalence plus one exact instance plus dual-certificate soundness. It is not a proof that `exact_support`'s vertex enumeration is correct in general. This matches the card's reuse scope and is declared not-claimed.
6. **Unused section instances.** `[NormedAddCommGroup Y] [NormedSpace ℝ Y]` on `isBounded_fibreImage` and `isBounded_finiteDomainBound`, and `[FiniteDimensional ℝ E]` on `affine_fibreImage_subset_singleton`, reduce generality only and do not strengthen any conclusion.
7. **Olean hashes depend on the build path.** Byte-identity of the oleans holds only when building from the original source paths (see check 4b).

## Code defect versus method limit

I found no code defect. The limits are methodological and declared: the vertex-enumeration correctness is not formalised, curved-set support is not computable in general, and the ellipsoid floating-point status bands have no numerical link.

## Suggested VALIDATION_MATRIX scientific-row update (not applied)

`L2-W1-B | fibre-image branches (general F / affine→L2-W1-A / ellipsoid=P08-B rfl / box-polytope dual cert [0,3/2] / curved arc+parabola counterexamples) | formal: 42/42 theorems, axioms ⊆ {propext, Classical.choice, Quot.sound}, independent recompile exit 0, main olean bit-identical from original path | numeric: polytope [0,3/2] reproduced (scipy HiGHS, exact rational enumeration, adapter, Sage PPL) | review: PASS_WITH_NOTES (claude-opus-5-5, 2026-10-14) | scientific admission: HOLD`

## Not proved / not claimed

- **Scientific admission: HOLD.**
- General correctness of the `joint_feasible_set.exact_support` vertex enumeration.
- Computable support for general curved sets, and any general nonlinear feasible-set solver.
- A numerical or floating-point link for the `typefree_fibers` ellipsoid status rules (EMPTY_SET / BOUNDARY_NUMERICALLY_UNRESOLVED).
- Confidence, coverage or null calibration.
- Infinite-dimensional E.
- Physical units, R2 coefficients, and Q/F/Π/G_F numerics.
- Publication readiness.

## Relevant paths

- `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/typefree_loop2_closeout_20260928/l2w1b_fibre_image_branches_v1_20261014/lean/L2W1FibreImage.lean`
- `.../l2w1b_fibre_image_branches_v1_20261014/FROZEN_TARGETS.md`, `SOURCE_RECOVERY.md`, `AUTHOR_RETURN.json`, `raw/compile_0[1-8]_*`, `raw/probes/*`
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/htt/src/common/typefree_fibers.py`
- `/home/cosmosapjw/Dropbox/bianchi/htt_base/htt/src/common/joint_feasible_set.py`
- Scratch evidence: `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/l2-w1-b_rerun/`, containing `audit/ReviewAudit.lean` and `.out`, `indep_lp.py`, `sigcheck.py`, `probe_rerun.json`, `sage_rerun.json`, `olean/`, `det/`.
