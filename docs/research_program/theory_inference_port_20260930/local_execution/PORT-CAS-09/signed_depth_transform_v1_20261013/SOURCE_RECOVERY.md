# P09-A source recovery (PORT-CAS-09, signed joint depth transform)

Repository HEAD at recovery: `f97fd5f806642a8274ffe474c75c4767fa7f3c2b`.
All paths relative to the repository root. Hashes are sha256 of the working-tree file at recovery.

| file | sha256 |
|---|---|
| htt/src/common/depth_path.py | 7b3115ced6d68ec1ede814df6662127719bc2a12cb4cebe97098c50e6274432f |
| htt/src/common/typefree_depth.py | c4f61af0aba73810eb94e31791aef5146ae5ef0e38223f2bc2845ceb2e1e34a9 |
| htt/htt/htt/infer/r9_depth_law.py | 4a5a06a3a8534d731a109c8299cc060a2958913cb09b1820e94daedfdd0c5783 |
| docs/research_program/tensor_joint_r9/revision2/THEORY_EXTENSION.md | befeef7feab9a845186b81fb9d7ce84b755b332bd0bf2fd6f93d0e1c36e89529 |
| docs/research_program/theory_inference_port_20260930/PORT_MAP.json | d0050aa349b56946d39bf2751e4f4687029c98e17203ed1740ab797ad44ce5e0 |
| docs/research_program/theory_inference_port_20260930/SOURCE_TO_REPO.json | ac5aa450924f522e85bc30bbce56852e9d9315aca17543220789578cefffbcf0 |
| docs/research_program/theory_inference_port_20260930/CAS_CONTRACT.json | 904d95fe49402e9589f48bf4dcfdf69e4680a069693545580e4892e83c389fad |

## Contract and map

- `CAS_CONTRACT.json:111-114` — id `CAS-09`, title "Signed joint depth transform",
  identity `contrast=H x; Cov=H C H^T; initial-plus-contrast T invertible`,
  assumptions `same full joint law and all cross blocks; fixed transport`.
- `PORT_MAP.json:48-60` — family F5 "Signed depth and existing R9 law"; APIs
  `common.typefree_depth.signed_depth_transport`, `htt.infer.r9_depth_law`;
  limits "All cross-covariance blocks or one full covariance required",
  "Fitted transport remains scenario-only; no independent contrast likelihood",
  "Redshift labels do not supply elapsed time or dynamics"; `scientific_admission: false`.
- `SOURCE_TO_REPO.json` — contains no depth/R9 entry (keys: base_commit, new_preserved_sources,
  prior_repository_checkpoints, not_downloaded_or_modified, not_republished, scope). The
  operative definitions are therefore recovered from the live code and the R9 D1/D3 theory note below.

## Depth vector (blocks)

- `htt/src/common/depth_path.py:13-18` — `DepthRepresentation(dimensions, kernels, feature_ids,
  procedure_id, transport_policy="FIXED_BEFORE_OBSERVATION")`.
- `depth_path.py:23-24` — dimensions are positive integers (one block per depth step).
- `depth_path.py:27-28` — exactly `len(dims)-1` kernels: "one transport per adjacent block".
- `depth_path.py:31-32` — kernel j has shape `(dims[j+1], dims[j])`, i.e. K_j : R^{d_j} -> R^{d_{j+1}}
  (arbitrary fixed finite real matrix; rectangular/singular allowed).
- `depth_path.py:29-30` — transport policy is `FIXED_BEFORE_OBSERVATION` or `FITTED_REQUIRES_JOINT_LAW`.
- `typefree_depth.py:79` — the depth vector is the concatenation of the ordered blocks
  (`np.concatenate([r.difference ... for r in rows])`).

Lean model: depth `d : ℕ` means `d+1` blocks indexed by `Fin (d+1)` with sizes `n : Fin (d+1) → ℕ`
(zero sizes allowed — a harmless generalization of the positivity check); full index
`Σ i : Fin (d+1), Fin (n i)`; transports `K j : Matrix (Fin (n j.succ)) (Fin (n j.castSucc)) ℝ`,
`j : Fin d`, arbitrary fixed real matrices.

## Contrast H

- `depth_path.py:41-51` — `H` has `sum(dims[1:])` rows and `sum(dims)` columns; row block j has
  `-K_j` in column block j (`:48`) and the identity in column block j+1 (`:49`); every other block 0.
  So `(Hx)_j = x_{j+1} - K_j x_j`.
- `THEORY_EXTENSION.md:7-15` (D1) — `r_j = Y_{j+1} - K_j Y_j`, `r = HY`, `E[r] = Hμ`, `V = HCH^T`,
  `V_jk = C_{j+1,k+1} - C_{j+1,k}K_k^T - K_j C_{j,k+1} + K_j C_jk K_k^T`.
- `THEORY_EXTENSION.md:19-23` — three independent unit scalars, K=1 give `V = [[2,-1],[-1,2]]`.
- `THEORY_EXTENSION.md:40` — three copies of the same variable: C all ones, V = 0.

## Initial-plus-contrast T and its inverse

- `depth_path.py:53-55` — `T = vstack(I[:dims[0]], H)`: first block rows copy x_0, remaining rows
  are H. Since contrast block j has size dims[j+1], T is square with the same block layout.
- `depth_path.py:57-62` — `restore`: sequential in-place recursion
  `y[block j+1] += K_j @ y[block j]`, i.e. `Y_0 = a_0`, `Y_{j+1} = r_j + K_j Y_j`.
- `THEORY_EXTENSION.md:44-58` (D3) — `T : Y -> (Y_0, HY)` square block lower triangular with
  identity diagonal, det T = 1, inverse `Y_{j+1} = r_j + K_j Y_j`; retain the full `TCT^T`.

## Full joint covariance (all cross blocks)

- `depth_path.py:65-81` — `full_covariance_blocks`: every ordered block (j,k) is required; a missing
  block returns None, so no independence is silently inserted.
- `typefree_depth.py:39-46,74-75,81,95` — the covariance is "the original full ordered joint
  covariance"; contrast covariance `h@c@h.T`, anchored covariance `t@c@t.T`.
- `htt/htt/htt/infer/r9_depth_law.py:79-80` — non-fixed transport returns `SCENARIO_ONLY`
  ("fitted transport needs full repeated pipeline or conditional law").
- `r9_depth_law.py:81-83,94-95` — views are ORIGINAL or INITIAL_AND_CONTRASTS only;
  `observed = T@y`, `covariance = T@C@T.T`, `mean = T@mean` (contrasts alone are refused).
- `typefree_depth.py:120-121` — status `SCENARIO_ONLY` whenever the transport is not fixed.

## Modelling decisions

- Transports are fixed (deterministic) real matrices, a parameter of every definition; nothing
  depends on ω. Random/fitted transport is outside scope.
- No independence hypothesis appears in any theorem; the covariance matrix is the full
  `cov[x_p, x_q]` for all ordered pairs p, q.
- The block index is an ordering label only; nothing is interpreted as elapsed time/redshift dynamics.
