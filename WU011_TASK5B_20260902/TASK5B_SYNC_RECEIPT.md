# PMG-WU-011 Task-5B synchronization receipt

Generated: 2026-09-02 KST

## Exact authority

- Repository: `cosmosapjw-quantum/htt_base`
- Draft PR: `#444`
- Branch: `changeset/planck-mes-wu011-processed-local-boost-response-20260902`
- Verified head: `5e9f24b3b828e5b10f7346532a4cf8a4e8d4f13f`
- Base head: `ecf22552c22a35ce34ec58e9d98adab68c6823d7`
- WU-010 predecessor closeout: `29427a1f7f2c5d46e43ffe03053c4ac13e969228`
- Jira: `BASS-21`
- Confluence pages: `21823493`, `22151174`, `22347781`

## Current state

`PASS_TASKS_1_TO_6_AND_TASK5B_SYNTHETIC_PROCESSED_RESPONSE / TASK7_DETERMINISTIC_EVIDENCE_NEXT`

PR #444 remains open, draft, and unmerged. No merge or scientific claim promotion is authorized.

## Task-5B implementation

The processed Jacobian has shape `(3,32,49)`, with source coordinate
`(T0, stored-real a_lm for ell=1..6)` and retained output `ell=2..5`.

Conventions:

- metric signature `(-,+,+,+)`;
- outward sky direction `n=-e`;
- active local-observer boost `+beta`, `beta=v/c`;
- thermodynamic-temperature Doppler weight `d=1`.

The exact physical monopole satisfies

`J_scientific[:,:,T0] = 0`

after simultaneous `ell=0,1` nuisance profiling. HEALPix replay leakage is retained separately as `raw_replay_tensor` and `monopole_replay_leakage`.

For stored-real harmonic blocks,

`G_ell = diag(1,2,2,...,2)`,

`G_S = diag(4*pi,G_1,...,G_6)`,

`G_R = diag(G_2,G_3,G_4,G_5)`,

`J_tilde = (I_3 kron G_R^(1/2)) J_stack G_S^(-1/2)`.

The exact full-sky reference is

- `sigma_ell^2 = 8/3, 27/5, 13, 21, 125/11, 216/13`;
- multiplicities `3,5,7,9,11,13`;
- anisotropy rank `48`;
- structural `T0` nullity `1`;
- nonzero condition `sqrt(63/8) = 2.806243040080...`.

For source `ell=6`, `V_6 -> V_5 + V_7`. The code stores the total source response, physical `6->5` neighbour block, processed raised-`ell=7` alias contribution, and numerical decomposition residual separately.

All `3 x 49 = 147` registered Jacobian columns are tested by centered mixed finite differences.

## TDD and workflow evidence

- RED contract: `92cf76653d67f5ed9a2e1853cb4fbd119efa86be`, WU011 run `#21`.
- Implementation: `33abaaec017173437109a471329a4c91e4247be6`.
- Floating-closure repair: `c0bef0e92a2ae9005e8fbc709544696b0dcb493a`, WU011 run `#23`, `21 passed in 2.68s`.
- Complete 147-column regression: `5e9f24b3b828e5b10f7346532a4cf8a4e8d4f13f`.
- WU011 run `#24 / 33580567994`: SUCCESS, `22 passed in 6.83s`.
- PR04 run `#484 / 33580567977`: SUCCESS.
- PR07 run `#478 / 33580568028`: SUCCESS.
- Repository integrity run `#718 / 33580568016`: SUCCESS, including repository contracts, portable replay, architecture boundary, Python package smoke, and Rust compile.

The only intermediate post-implementation failure was an exact-byte assertion on a `2.02e-28` floating reassociation residual. The bounded repair changed only the assertion to a machine-precision tolerance; no equation or physics path was weakened.

## Next DAG node

`PMG-WU-011-TASK7A-DETERMINISTIC-EVIDENCE-AND-SENSITIVITY-RECEIPT`

Required outputs:

1. content-bound processed matrices and typed JSON receipt;
2. actual full-sky identity-transfer versus exact-irrep spectrum;
3. `nside`, processing-cutoff, mask, and transfer sensitivity ladders;
4. monopole replay leakage versus numerical resolution;
5. physical `ell=6->5` and raised-channel alias diagnostics;
6. finite-to-linear, sign, transfer-order, FWL, fixed-axis parity, and 147-column residual figures;
7. SHA-256 manifest and hostile figure audit;
8. fresh independent PHYS-MATH and PHYS-MATH-CODE reviews.

## Claim boundary

This receipt covers a synthetic processed local-observer scalar response only. It contains no admitted Planck absolute-temperature product, observed rank, empirical beta, boost subtraction, global matter-frame tilt, polarization result, foreground exclusion, Bianchi-family attribution, causal identification, or P01-P27 formal-dossier replay.
