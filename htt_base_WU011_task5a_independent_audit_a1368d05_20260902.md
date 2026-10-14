# PMG-WU-011 Current-Head Cross-System Audit

# PMG-WU-011 Task 5A Independent Jacobian Audit and Task 5B Repair Gate

## Frozen authority

- Repository: `cosmosapjw-quantum/htt_base`
- Draft PR: `#444`
- Audited head: `a1368d05af4f98e6413e328b5027e6e7ba3fa1dc`
- State at readback: `OPEN / DRAFT / MERGEABLE`
- WU-010 predecessor closeout: `29427a1f7f2c5d46e43ffe03053c4ac13e969228`
- Joint estimator: `joint_weighted_real_harmonic_l0_l5_retain_l2_l5:v1`
- Current scoped result: Tasks 1–6 are implemented and exact-head workflows are GREEN; Task 7 evidence generation is blocked by the Task 5B semantic repair below.

## Fixed conventions

`g_ab=(-,+,+,+)`, outward sky direction `n=-e`, active local-observer boost `+beta`, `beta=v/c`, thermodynamic-temperature Doppler weight `d=1`.

This node concerns a local observer boost only. It is not global matter-frame tilt, finite-electron-tilt collision physics, or Bianchi geometry.

## Processed operator

`R_proc(beta)=H_ret D_com J_W Y_src D_src B_beta S_abs`

`G_proc(beta)=H_ret D_com J_W Y_src D_src G_beta S_abs`

Mandatory local gate:

`||R_proc(beta)-R_proc(0)-G_proc(beta)||=O(|beta|^2)`

above the disclosed HEALPix replay floor.

## Correct source and output coordinates

The 49-dimensional source coordinate is

`s_abs=(T0,a_1,...,a_6)`, with `1+sum_{ell=1}^6(2ell+1)=49`,

not a uniform `ell=0..6` stored-harmonic registry. The physical constant temperature and harmonic monopole satisfy

`a00=sqrt(4*pi)*T0`.

The retained output is `(a_2,a_3,a_4,a_5)` in 32 scientific stored-real coordinates. The coefficient Jacobian is

`J[i,alpha,j]=d^2 R_proc,alpha/(d beta_i d s_j)|_{beta=0}`

with shape `(3,32,49)`.

## Invariant metrics and structural null

For each scientific stored-real multipole block,

`G_ell=diag(1,2,2,...,2)`.

Hence

`G_S=diag(4*pi,G1,...,G6)` and `G_R=diag(G2,G3,G4,G5)`,

and the invariant stacked diagnostic is

`J_tilde=(I3 tensor G_R^(1/2)) J_stack G_S^(-1/2)`.

A constant thermodynamic monopole generates only a first-order dipole and is removed by the simultaneous `ell=0,1` nuisance solve. Therefore the continuum scientific Jacobian obeys

`J[:,:,T0]=0`, `rank(J)<=48`, and `condition(J_96x49)=infinity`.

The implementation must distinguish this exact null from retained numerical HEALPix replay leakage.

## Exact full-sky reference spectrum

For retained output set `{2,3,4,5}`, the metric-whitened singular-value squares for source `ell=1,...,6` are

`{8/3, 27/5, 13, 21, 125/11, 216/13}`

with multiplicities `{3,5,7,9,11,13}`. The healthy full-sky anisotropy block has rank `48` and nonzero-subspace condition

`sqrt(63/8)=2.806243040080...`.

Raw Euclidean SVD in stored-real coordinates may be retained only as an explicitly coordinate-dependent numerical diagnostic.

## Correct ell=6 decomposition

The complete `ell=6` source block is not an alias block. On the full sky, `V6 -> V5 + V7`. The physically meaningful decomposition is

`J^(6)=J_neighbour^(6->5)+J_alias^(6->7->fit)`.

Required stored objects:

- `ell6_source_response_block`;
- `ell6_expected_neighbor_l5_block`;
- `ell6_cutsky_alias_residual`.

`processing_lmax>=7` remains mandatory so the raised `ell=7` channel is not silently truncated before fitting.

## Centered mixed derivative gate

For source basis vector `e_j`, boost axis `e_i`, positive baseline sky `s`, and steps `h,epsilon`, verify analytic columns with

`Jhat[i,:,j]=[R(+epsilon e_i;s+h e_j)-R(-epsilon e_i;s+h e_j)-R(+epsilon e_i;s-h e_j)+R(-epsilon e_i;s-h e_j)]/(4 epsilon h)`.

All four skies must remain strictly positive. Prefer complete coverage of all 147 `(axis,source)` columns; a reduced gate must be preregistered and rotation-complete.

## Current code-audit findings

### P1 — metric whitening missing

The current module computes SVDs directly on raw scientific stored-real arrays. Those condition numbers depend on coordinate scaling and cannot be promoted to invariant response conditioning.

### P1 — physical monopole null mixed with replay leakage

The current builder stores `monopole_response/reference` in `tensor[:,:,0]`, and the default predictor contracts it with physical `T0`. The scientific tensor must instead contain an exact zero `T0` column, with numerical replay leakage stored and predicted through a separately named diagnostic API.

### P1 — `ell6_alias_block` misclassifies the physical neighbour response

The current field includes the genuine `ell=6 -> ell=5` response. A nonzero total norm is therefore not evidence of cut-sky aliasing.

### P1 — finite-difference validation is not column-complete

A mixed sky and one beta direction can hide compensating sign/order errors. Use the centered mixed derivative column oracle.

### P2 — first source-registry row is type-ambiguous

`ScientificMode(0,0,"REAL")` does not distinguish physical `T0` from harmonic `a00`. Add an explicit coordinate role and harmonic adapter, or use a separate source-coordinate type.

## Task 5B acceptance gates

1. Add `G_S`, `G_R`, metric-whitened singular values, rank, and nonzero-subspace condition.
2. Set the scientific `T0` Jacobian column exactly to zero.
3. Store `monopole_replay_leakage` separately and keep raw replay prediction out of the default scientific API.
4. Split the `ell=6` block into physical neighbour and cut-sky alias residual.
5. Replace the ambiguous first registry row with a typed physical-monopole coordinate.
6. Add centered mixed finite-difference checks across the registered columns.
7. Regenerate Task 7 matrices and plots only after these gates pass.
8. Run fresh PHYS–MATH, PHYS–MATH–CODE, hostile-figure, and residual-error audits at the frozen repaired head.

## Disposition

`TASKS_1_TO_6_GREEN / TASK5B_REPAIR_REQUIRED_BEFORE_TASK7_SCIENTIFIC_RECEIPT`

No P0 was found inside the declared synthetic WU-011 scope. The P1 findings do not invalidate the already scoped finite/linear/FWL/parity implementations, but they block response spectra, condition numbers, monopole columns, and `ell=6` plots from being interpreted as invariant scientific evidence.

## Claim boundary

No Planck absolute-temperature product, observed rank, empirical `beta`, boost subtraction, global matter-frame tilt, polarization result, foreground exclusion, Bianchi-family attribution, causal identification, or replay of the unavailable P01–P27 formal dossier is admitted here.

## Runtime/readback state

- PR: https://github.com/cosmosapjw-quantum/htt_base/pull/444
- Frozen audited head: `a1368d05af4f98e6413e328b5027e6e7ba3fa1dc`
- Current PR body reports Tasks 1–6 exact-head workflow success and keeps the PR open/draft.
- Current Jacobian module still performs raw-coordinate SVD, retains numerical monopole leakage in `tensor[:,:,0]`, labels the complete ell=6 block as alias, and contracts the full tensor with physical `T0`.
- Therefore the repair gate above remains live at this head.

## Evidence package

- Package: `WU011_TASK5A_JACOBIAN_CONTRACT_ORACLE_20260902.zip`
- SHA-256: `8ae2f58d0c88bcbe9da411dfa9ae7e375dfd669a148b9574359fce68e99df580`
- Full-sky oracle: 2,048 deterministic quadrature nodes, numerical rank 48, structural null singular value at numerical zero, metric-whitened restricted condition `sqrt(63/8)`.
