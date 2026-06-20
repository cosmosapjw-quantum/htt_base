# Frame-Vorticity Repair Note (REV-R093)

owner: BASS
implementation_scope: canonical_BASS
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `Codex REV-R093 split frame vorticity identities`
git_commit_or_worktree_state: pending_rev_r093_commit

## Purpose

Separate the two admissible vorticity identities so that a Bianchi VII_h
vorticity decomposition is never advertised as a current result without
declaring its frame. The split is enforced in code by
`bass.hierarchy.frame_contracts.FrameIdentityScope` and guarded for the
background constraints by
`bass.background.constraints.assert_vorticity_consistent_with_frame`.

## The two scopes

### Hypersurface-normal Bianchi slicing (`normal_frame_slicing`)

- The geometry-frame congruence is the group-orbit unit normal.
- `W_std = 0` by construction: `vorticity_term_allowed = False`.
- The intrinsic group-orbit Ricci substitution is allowed:
  `geometry_ricci_substitution_allowed = True`.
- Claim tier: `conditional` (descriptive group-orbit geometry only).

### Matter / threading candidate (`threading_candidate`)

- Vorticity may be discussed only if **all** of the following are bound:
  - full boost terms (`full_boost_terms_bound`),
  - energy-flux terms (`flux_terms_bound`),
  - anisotropic-stress terms (`anisotropic_stress_terms_bound`),
  - momentum-constraint terms (`constraint_terms_bound`).
- If any term is unbound the scope is `claim_tier = "blocked"` and records the
  missing terms in `blocked_reasons` (e.g. `full_boost_terms_missing`).
- `geometry_ricci_substitution_allowed = False`: the projected "spatial" Ricci
  is threading-frame algebra, not an intrinsic three-geometry.

## Manuscript impact

- `docs/manuscript/ch04_bianchi_bounds.tex`: the Bianchi VII_h kinematic-table
  row no longer claims a hypersurface-normal orthogonal vorticity; the
  `W_std = R^2 Sigma_std` Frobenius relation is marked as a blocked
  threading-frame decomposition with an explicit frame caveat.
- `docs/manuscript/ch03_framework.tex`: the slicing-versus-threading discussion
  records the machine-checkable `FrameIdentityScope` split.

## Status

- Normal-frame slicing: descriptive, conditional, no vorticity sector.
- Threading-frame vorticity: **blocked current result** until the four binding
  conditions above are met. No data-fitting headline may rely on a
  threading-frame vorticity decomposition while it is blocked.
