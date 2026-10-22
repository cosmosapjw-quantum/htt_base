# G15-B re-execution closeout — source recovery

Paths are relative to `docs/research_program/gr_statistics_loops_20260930/` unless they start
with `HTT_` or `docs/`. Hashes are sha256 values taken in this session.

## Inputs

| input | sha256 | role |
|---|---|---|
| zip member `HTT_ALL_OBLIGATIONS_20261011/tasks/G15-B.json` | 7d889a282e2e84d6aa2d4fe8c7a08ed6b023cd77f2cbf1ba7f8bba73ea34a12b | scope, lean_steps 1–5, acceptance, pitfall; re-read this session |
| `local_cas/.../CAS-15/g15b_sphere_divergence_ibp_v1_20261014/FROZEN_TARGETS.md` | 58469ea396138b7cab0174ce4b5fc5139f960838f1d22aa70f163be6c21671ec | Part A frozen statements (copied verbatim to `prior/FROZEN_TARGETS_prior_58469ea3.md`) |
| `local_cas/.../CAS-15/g15b_sphere_divergence_ibp_v1_20261014/SOURCE_RECOVERY.md` | ca97e9d72c317b6d758264ea9f187b44553b6e10211bd79f9ca052004bf5d280 | all definition bindings of Part A (copied verbatim to `prior/SOURCE_RECOVERY_prior_ca97e9d7.md`); not re-derived here |
| `local_cas/.../CAS-15/g15b_sphere_divergence_ibp_v1_20261014/lean/G15BSphere.lean` | d08907e948e85a0f58fe95cc59afd1f71eef1a5f56870434c5792c8cafafc6b8 | reviewed final source, copied UNCHANGED to `lean/G15BSphere.lean` |
| `local_cas/.../CAS-15/g15a_photon_energy_direction_v1_20261013/lean/G15APhoton.lean` | fc4d060643fc84a83beb729926df21b70480328dbf2eaab73bd5e31d541a7e39 | reviewed G15-A import, copied UNCHANGED to `lean/G15APhoton.lean` |
| `local_cas/.../CAS-15/g15b_sphere_divergence_ibp_v1_20261014/REVIEW.md` | ddff0afe6ce145c7e0fa912500d07aafd0294d9f6eae5d33f8578de9bf1ccbdc | note N1 (failure retention UNMET), note N2 (I-wise quantifiers of `B5_rank_le_four_moments`) |
| `local_cas/.../CAS-15/g15b_sphere_divergence_ibp_v1_20261014/ADDENDUM_20261014.md` | 71b9f0678e0896c377537cc26eb8ab71c380823f84ea91deaca62c96d7167afb | closure path: complete-retention re-execution + additive uniform form |
| `local_cas/.../CAS-15/g15b_sphere_divergence_ibp_v1_20261014/raw/AxiomAudit.lean` | 43fa287cdcf03896843884856444456ebee82cd22d7efdf2e6fc7f2c2bc3bbbd | prior audit, reused as the prefix of this unit's `raw/AxiomAudit.lean` (import line changed to `G15BUniform`) |

## Binding of the new target U

* `supplements/DOSSIER_POSITIVE_BRIDGE.md` (sha256 00c1fcb0b786bb874f13e52442af4b7b8a125287d84decb799ea68fd03915ebd) l.149 ("Only brightness moments through rank four … are
  needed") and `cas/contracts/CAS-15.json` (sha256 eccc10a3f5105970a46a73412d8c82a27a1e82a6116013bc0abc6656816f8eee) l.263 ("…; onlyrank<=4"), as cited in the prior
  SOURCE_RECOVERY.md (l.149 / l.263 bindings). The claim is uniform in the brightness I: one fixed
  angular polynomial of degree ≤ 4, so the (B5) integral is a fixed linear combination of brightness
  moments of rank ≤ 4. This binds `G15BU.B5_rank_le_four_uniform`.
* The prior binding of that dossier sentence to `G15B.B5_rank_le_four_moments` (∀ μ ∀ I ∃ p) is
  I-wise only (REVIEW.md N2); it is kept unchanged as a Part A statement and is not relabelled.
* `wB5` (the boxed (B5) bracket), `RotInv`, `S2`, `σS` are the reviewed G15-B definitions; no new
  physical definition is introduced.

## Nothing missing

No definition needed for this unit was unrecoverable.

## Prior failure history

The prior unit's development compiles (raw/probes/c1.lean) ran outside its harness. Their
stdout/stderr, exit codes and attempt count are UNAVAILABLE and are NOT recovered by this
re-execution (REVIEW.md N1; ADDENDUM_20261014.md).
