# L2-W1-B source recovery

Task card: `HTT_ALL_OBLIGATIONS_20261011_PACKAGE.zip :: HTT_ALL_OBLIGATIONS_20261011/tasks/L2-W1-B.json`
(read with `unzip -p`; card `source_snapshot` a30d84c7918b54238a48fa62e2ef482f7e6d36fa,
status `PLANNED_NOT_EXECUTED`, requires `L2-W1-A`, `P08-B`).

Card text (Korean, quoted in substance):

- scope_original: connect the linear whole-space theorem with direct fibre-image analysis of
  bounded / curved feasible sets.
- existing_reuse: P08-A/B ellipsoid image and the existing exact rational polytope support.
- lean_steps: (1) define fibre `F ∩ B⁻¹{y}` and target image `P(F ∩ B⁻¹{y})` for a general
  admissible set `F`; (2) prove the affine-unbounded branch reduces to L2-W1-A; (3) connect the
  ellipsoid branch to the P08-B exact image and the original rational bounded polytope to the
  existing support certificate; (4) for curved general `F` claim only the source-defined image
  theorem and leave an exact counterexample where the universal linear iff fails.
- acceptance: finite-domain bound and global coercivity kept under different names/types; no
  general nonlinear solver invented as an extra obligation.
- pitfall: one ellipsoid success does not give computable support for every curved set.

## Recovered definitions and their sources

| Item | Source (file:line) | Use here |
|---|---|---|
| Claim TF-W1-KERNEL-DOMAIN: uniform bound `‖Pv‖ ≤ C‖Bv‖` iff `ker B ⊆ ker P` for unconstrained finite-dimensional linear variations; bounded/curved sets need direct fibre-image analysis | `docs/research_program/typefree_loop2_closeout_20260928/CLAIM_CLOSEOUT.json:11-12` | `GlobalCoercivity`, `KernelInclusion`; branch split |
| Affine domain `k0 + V` uses the declared variation space; kernel condition is not necessary for bounded/curved `K`; negative control `B=0, P=id, K=[-1,1]`; three distinct judgements (image boundedness, singleton identifiability, calibration) | `docs/research_program/typefree_loop2_closeout_20260928/ERRATA_F1_W1_KO.md:21-39` | `AffineDomain`, `FiniteDomainBound` vs `GlobalCoercivity`, subsingleton theorem kept separate |
| L2-W1-A Lean theorems `kernel_bound_iff`, `affine_kernel_bound`, `bounded_set_negative_control` | `docs/research_program/typefree_loop2_closeout_20260928/l2w1a_kernel_bound_v1_20261013/lean/L2W1KernelBound.lean:26,62,90` (sha256 5556288e…9f55, reviewed PASS_WITH_NOTES per `RETURN.json`) | imported unchanged |
| F4 port: APIs `ellipsoid_quotient_gauge`, `ellipsoid_fiber_image`, `rational_polytope_fiber_support`; limits "Exact rational result applies only to the explicitly bounded supplied polytope", "No general nonlinear feasible-set solver" | `docs/research_program/theory_inference_port_20260930/PORT_MAP.json` (F4 entry; `python3 -m json.tool` lines 32-46) | scope limits honoured; no nonlinear solver |
| Ellipsoid fibre image `P(K ∩ {Bx=y})`, `K = c + U^{1/2}·ball` | `htt/src/common/typefree_fibers.py:136-171` (sha256 6f5f9a01…3947910) | ellipsoid branch = P08-B `Ell`, `FibreImage` |
| P08-B Lean `Ell`, `FibreImage`, `EllImage`, `IsKerONB`, `fibreImage_eq_of_le`, `boundary_eq_one`, `boundary_gt_one`, `incompatible_empty`, `fibreImage_nonempty_iff`, `support_function` | `docs/research_program/theory_inference_port_20260930/local_execution/PORT-CAS-08/ellipsoid_image_v1_20261013/lean/P08EllipsoidImage.lean:43-58,114,215,238,250,330,372` (sha256 0cb88696…cd0a, reviewed PASS_WITH_NOTES) | imported unchanged |
| P08-A Lean `Fib`, `fiber_branches` (dependency of P08-B) | `.../PORT-CAS-08/ellipsoid_fiber_mp_v1_20261013/lean/P08EllipsoidFiber.lean:145-193` (sha256 a69fb0ad…c8ab) | imported unchanged |
| G08-A `IsMoorePenrose` and its dependency ProjectionBridge (dependencies of P08-A/B) | `docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-08/g08a_whitening_gls_v1_20261013/lean/G08AWhitening.lean` (sha256 e6228021…bf045); `.../CAS-08/c01_c02_projection_bridge_v1_20261011/ProjectionBridge.lean` (sha256 440e3820…2219) | imported unchanged |
| "Existing exact rational polytope support certificate": `BoundedRationalPolytope` = `{A x ≤ b, lower ≤ x ≤ upper}` (box part of the declared domain) and `rational_polytope_fiber_support`, which appends box rows and the equality rows `B x ≤ y`, `−B x ≤ −y`, and evaluates `exact_support(P^T u, …)` | `htt/src/common/typefree_fibers.py:185-247`; `htt/src/common/joint_feasible_set.py:43-74` (sha256 d7903c00…dcfe3474; vertex enumeration with boundedness precondition) | Lean `BoxPoly`, `augMat`/`augRhs` (same rows up to a permutation), `support_transport` (direction `Pᵀu`), dual-certificate soundness |
| Augmentation recipe and boundedness precondition ("Only call no vertices EMPTY_SET if the original K is already known bounded") | `docs/research_program/theory_inference_port_20260930/implementation_review/formalism_mapping.md:101` | `polytope_fibre_eq_aug`, `polytope_finiteDomainBound` |
| Port commit for `typefree_fibers.py` | `git log`: bc45fb92 "PR-TYPEFREE-INFERENCE-PORT"; `joint_feasible_set.py` from 5aa4e7f9 "PR-189" | provenance only |

The CLAIM_CLOSEOUT.json file does not itself contain a polytope certificate; the "existing exact
rational polytope support certificate" was located through the F4 port entry
(`PORT_MAP.json`, which lists `common.typefree_fibers.rational_polytope_fiber_support`) and is the
exact-rational Python adapter above. It is not a Lean object. It is cited unchanged and
exercised read-only (`raw/probes/probe_polytope_and_curved.py`); the Lean side proves the
reduction it relies on (augmented H-representation, `Pᵀu` support transport, boundedness from the
box) and the soundness of an LP dual certificate, and checks one exact instance whose interval
equals the adapter output.

## Items not recoverable as formal objects

- Correctness of the vertex-enumeration algorithm in `joint_feasible_set.exact_support` (that the
  maximum over enumerated vertices equals the supremum over the polytope) is not formalised
  anywhere in the repository. Searched: all `*.lean` under `docs/` and `htt/` (`grep -rli polytope`
  returns none). Unlock: a Lean proof of the vertex (fundamental LP) theorem or a per-instance
  dual certificate, which is what this unit supplies for the frozen instance only.
- "Admissible" has no further formal meaning in the sources beyond "supplied feasible set"; it is
  therefore taken as an arbitrary `Set E`.
