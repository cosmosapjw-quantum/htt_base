# PMG-WU-011 Task 5B Repair Contract

## Authority

- Repository: `cosmosapjw-quantum/htt_base`
- Draft PR: `#444`
- Frozen audited head: `a1368d05af4f98e6413e328b5027e6e7ba3fa1dc`
- Disposition: `TASKS_1_TO_6_GREEN / TASK5B_REPAIR_REQUIRED_BEFORE_TASK7_SCIENTIFIC_RECEIPT`

## Mathematical contract

Source coordinate:

`(T0,a_lm for ell=1..6)`, dimension 49, with `a00=sqrt(4*pi)*T0`.

Retained output:

`a_lm for ell=2..5`, dimension 32.

Processed Jacobian:

`J[i,alpha,j]=d^2 R_proc,alpha/(d beta_i d s_j)|_{beta=0}`, shape `(3,32,49)`.

Scientific stored-real metrics:

`G_ell=diag(1,2,2,...,2)`,

`G_S=diag(4*pi,G1,...,G6)`,

`G_R=diag(G2,G3,G4,G5)`.

Metric-whitened stacked matrix:

`J_tilde=(I3 tensor G_R^(1/2)) J_stack G_S^(-1/2)`.

Structural null:

`J[:,:,T0]=0`, `rank(J_aniso)=48`, full 49-column condition is infinite.

Exact full-sky singular-value squares by source ell 1..6:

`{8/3,27/5,13,21,125/11,216/13}`

with multiplicities `{3,5,7,9,11,13}` and restricted condition

`sqrt(63/8)=2.806243040080...`.

## ell=6 decomposition

The whole `ell=6` source block is not alias. Require

`J^(6)=J_neighbour^(6->5)+J_alias^(6->7->fit)`.

Store:

- `ell6_source_response_block`;
- `ell6_expected_neighbor_l5_block`;
- `ell6_cutsky_alias_residual`.

Require `processing_lmax>=7`.

## Centered mixed derivative oracle

For every registered source column and beta axis where feasible, verify

`Jhat[i,:,j]=[R(+eps e_i;s+h e_j)-R(-eps e_i;s+h e_j)-R(+eps e_i;s-h e_j)+R(-eps e_i;s-h e_j)]/(4 eps h)`.

All four source skies must remain strictly positive.

## Required implementation changes

1. Add metric-whitened rank/singular/condition diagnostics.
2. Keep raw-coordinate SVD only under an explicitly numerical label.
3. Set the default scientific Jacobian T0 column exactly to zero.
4. Store HEALPix monopole replay leakage separately.
5. Exclude replay leakage from the default scientific predictor.
6. Split ell=6 physical-neighbour and alias terms.
7. Type the first source coordinate as physical `T0`, not `a00`.
8. Add columnwise centered mixed finite-difference tests.

## Stop rule

Do not generate or promote Task 7 scientific spectra, condition numbers, monopole response, or ell=6 alias figures until this contract passes focused CI and fresh PHYS–MATH / PHYS–MATH–CODE audit.

## Claim boundary

Synthetic local-observer scalar boost only. No admitted Planck absolute temperature, observed rank, empirical beta, boost subtraction, global tilt, polarization, foreground exclusion, Bianchi-family attribution, causal inference, or P01–P27 replay.
