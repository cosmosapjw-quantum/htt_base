# REV-R093 - Split Frame Vorticity Identities

owner: BASS
implementation_scope: canonical_BASS
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `Codex REV-R093 split frame vorticity identities`
git_commit_or_worktree_state: pending_rev_r093_commit

## Evidence Read

- `AGENTS.md`
- `docs/superpowers/plans/2026-06-20-audit-ver2-research-hardening.md` (Task 6)
- `htt/bass/hierarchy/frame_contracts.py`
- `htt/bass/background/constraints.py`
- `docs/manuscript/ch03_framework.tex`
- `docs/manuscript/ch04_bianchi_bounds.tex`

## DAG Rationale

Canonical `PR-*` status remains complete at `62/62`. This PR implements
supplemental REV task 6: separate the hypersurface-normal slicing vorticity
identity from the matter/threading-frame identity so a Bianchi VII_h vorticity
decomposition cannot be advertised as a current result without declaring its
frame and meeting the binding conditions.

## Role Split

- Physics/statistics auditor steelman: the group-orbit normal frame has
  `omega^(G) = 0` for every orthogonal-sector type; a VII_h table row claiming
  orthogonal-frame vorticity with `W_std = R^2 Sigma_std` mixed frames and must
  be demoted to a blocked threading-frame decomposition.
- Code cartographer steelman: add a small immutable contract rather than a new
  subsystem; the helper only reads scope attributes.
- Harness engineer steelman: pin both identities and the constraint guard with
  focused tests; the threading scope must record the missing boost/flux/stress/
  constraint terms.
- Claim-gate reviewer steelman: the threading-frame vorticity stays a blocked
  current result with an explicit manuscript frame caveat.

## Changes

- `htt/bass/hierarchy/frame_contracts.py`: added immutable `FrameIdentityScope`
  with `normal_frame_slicing()` (`W_std = 0`, vorticity forbidden, group-orbit
  Ricci substitution allowed) and `threading_candidate(...)` (blocked unless the
  full boost, flux, anisotropic-stress, and constraint terms are bound, with
  `blocked_reasons`).
- `htt/bass/background/constraints.py`: added
  `assert_vorticity_consistent_with_frame`, which rejects a nonzero vorticity
  term under a normal-frame scope. The `FrameIdentityScope` import is guarded by
  `TYPE_CHECKING` to avoid a runtime cycle through `bass.hierarchy`/
  `bass.species`.
- `docs/manuscript/ch04_bianchi_bounds.tex`: the VII_h kinematic-table row no
  longer claims orthogonal-frame vorticity; the `W_std = R^2 Sigma_std`
  relation is marked as a blocked threading-frame decomposition with an explicit
  frame caveat paragraph.
- `docs/manuscript/ch03_framework.tex`: the slicing-versus-threading discussion
  records the machine-checkable `FrameIdentityScope` split.
- `docs/generated/frame_vorticity_repair_note.md`: new note documenting the
  contract and the blocking conditions.

## Artifact Metadata

- owner: BASS
- implementation_scope: canonical_BASS
- claim_tier: diagnostic_only
- config_hash:
  - `htt/bass/hierarchy/frame_contracts.py:sha256:06fc21afc0febed2539bffb74f6b08bb8c9358f64f320a3d89cc2e6cfa91d796`
  - `htt/bass/background/constraints.py:sha256:ce19bbb2ded3e9a3bf66e512c79f509ccf7a3ead949dccd5f01d1ccd0f764db2`
- input_hashes:
  - `tests/bass/test_frame_vorticity_identity.py:sha256:094412abb668584a2fc61efd07fbbae1fdb18005f07a55345d013a0908d38ca4`
  - `docs/generated/frame_vorticity_repair_note.md:sha256:725eb1da799cc52cec28feed47e7e2c93b17106df550d72a1814a7a6e39bb051`
  - `docs/manuscript/ch03_framework.tex:sha256:c19b99320a56f42eebb59ac10cdafa230b3187b61c9845c1f0c13db881e5441f`
  - `docs/manuscript/ch04_bianchi_bounds.tex:sha256:8eec1ab114c26f2e0ff0cc829de57b32dd3bcacce8ff25409a3575dff155a565`
- caveats:
  - no native low-ell solver result is introduced;
  - threading-frame vorticity remains a blocked current result until the four
    binding conditions are met.

## TDD Red

- `venv/bin/python -B -m pytest -p no:cacheprovider tests/bass/test_frame_vorticity_identity.py -q` initially failed with `ImportError` because `FrameIdentityScope` and `assert_vorticity_consistent_with_frame` did not exist.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/bass/test_frame_vorticity_identity.py` | PASS | `4 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider --co -q tests/bass` | PASS | `62 tests collected`, no import cycle. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/check_claim_language.py --dry-run htt/bass/hierarchy/frame_contracts.py htt/bass/background/constraints.py docs/generated/frame_vorticity_repair_note.md docs/manuscript/ch03_framework.tex docs/manuscript/ch04_bianchi_bounds.tex` | PASS | `No forbidden claim language detected.` |
