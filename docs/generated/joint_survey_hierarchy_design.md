# Joint Multi-Survey Hierarchy Design (REV-R097)

owner: HTT
implementation_scope: htt
claim_tier: blocked
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `Codex REV-R097 add joint survey hierarchy gate`
git_commit_or_worktree_state: pending_rev_r097_commit

## Purpose

Define the minimum schema that must be bound before CatWISE / radio / CF4 (and
the spectroscopic data-random dipole) amplitudes may be multiplied or compared
as a shared source model. This is a schema-only contract, not an observed-data
inference.

## Contract

`htt.infer.joint_survey_hierarchy.build_joint_hierarchy_contract(...)` returns a
contract whose `as_payload()` blocks the conditional-independence product until
**all** of the following fields are bound:

| Field | Blocked reason when unbound |
| --- | --- |
| `cross_probe_covariance` | `cross_probe_covariance_not_bound` |
| `mask_selection_metadata` | `mask_selection_metadata_not_bound` |
| `survey_calibration_nuisance` | `survey_calibration_nuisance_not_bound` |
| `shared_lss_covariance` | `shared_lss_covariance_not_bound` |
| `heldout_predictive` | `heldout_predictive_not_run` |

- `conditional_independence_product_allowed` is `False` while any field is
  unbound.
- `claim_tier` is `blocked` while any field is unbound, `conditional` once all
  are bound.

## Catalog hooks

- `htt.obsstat.catalogs.cf4.joint_survey_combination_status()` and
  `htt.obsstat.catalogs.spectroscopic_dipole.joint_survey_combination_status()`
  declare each probe non-combinable with others until the contract is satisfied,
  referencing the contract module by name (no obsstat -> infer import).

## Status

- The joint hierarchy is `blocked` by default; multiplying or comparing survey
  amplitudes as a shared source model is forbidden until the schema is bound.
- No observed-data inference is performed here.
