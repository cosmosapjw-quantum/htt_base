# Theorem Extension Registry

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
covariance_status: synthetic_only
null_mock_status: synthetic_only
native_solver_result: false
family_identification: false
config_hash: `c617a51f5028461257e8a60ee3abbae504b0cb3825dd4c2f04907fc5f80a8a46`
generated_on: `2026-06-20T02:50:07+00:00`
generating_command: `/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python scripts/generate_theorem_extension_assets.py --write`
git_commit_or_worktree_state: `7b3ded5+dirty`
source_paths:
- `scripts/generate_theorem_extension_assets.py`
- `htt/src/common/theorem_registry.py`
- `htt/mio/formalism/dynamic_budget.py`
- `htt/mio/formalism/bound_pushforward.py`
- `htt/bass/kinetic/boltzmann_memory.py`
- `htt/bass/kinetic/tight_coupling_bounds.py`
- `htt/bass/kinetic/visibility_rigidity.py`
- `htt/bass/geometry/egs_rigidity.py`
- `tests/contracts/test_theorem_registry.py`
- `tests/mio/test_dynamic_budget.py`
- `tests/bass/test_boltzmann_memory_bounds.py`
- `tests/bass/test_egs_rigidity_theorems.py`
input_hashes:
- `scripts/generate_theorem_extension_assets.py:8832af75b29bc8f9a5a0b0ea4ba8a49ad743610d75ffa0f9a558d09798095be4`
- `htt/src/common/theorem_registry.py:a83a86c952fe2bf4bda78a8fb0868231b6c302a76f3e7a4679b3bdd4fdc2e43d`
- `htt/mio/formalism/dynamic_budget.py:11132baea55ce3d879a03ded84a11cce42252a893f51bcf2d5a346c82ea168e4`
- `htt/mio/formalism/bound_pushforward.py:250da9000a61bb1210b6aa63662988612a40304f960e55f21bb53f2703a9a76a`
- `htt/bass/kinetic/boltzmann_memory.py:65900d82579773ba3935dd222e9db9191ffe357f988e9b7ac1149342a2874ce1`
- `htt/bass/kinetic/tight_coupling_bounds.py:b70879061d9d0f748121ca5e9c0816d43b0e19e6391e16cd75271e59f3ae99f4`
- `htt/bass/kinetic/visibility_rigidity.py:f33eb3f0ef0e02e1b43168008486433f261802dc1986039837db3e8ff9a0475a`
- `htt/bass/geometry/egs_rigidity.py:65ed1bbc7bd1813755c21fb84e8f7decaa9988e52e81607e8c82286e5651c5b0`
- `tests/contracts/test_theorem_registry.py:45265116be36217e387dd59d0e120fc63163e03d5b394d343b1058216019492b`
- `tests/mio/test_dynamic_budget.py:cda433d79e86e4217e360ee89010e0bb9d017fd76e788dbfb02c7cc3e5cbd5b9`
- `tests/bass/test_boltzmann_memory_bounds.py:b57b3bb7a98991aa92427f787046c5a2037afceed09ff4f4de1c6c93dc95832f`
- `tests/bass/test_egs_rigidity_theorems.py:ca16d0a03cebf4d870a95b936f4b7d77f037744d0f947d16c6d48f02aac0e424`
caveats:
- synthetic/manufactured verification only
- diagnostic-only
- not HTT evidence
- not a MIO certificate
- not native solver validation
- not geometry or family identification

This registry is synthetic/manufactured verification only. It is diagnostic-only, not HTT evidence, not a MIO certificate, not native solver validation, and not geometry or family identification.

| Theorem | Status | Proof Status | Implementation Test Status | Claim Status | Key Kill Switches |
|---|---|---|---|---|---|
| B4 | convention_conditional | convention_conditional | synthetic_manufactured_only | diagnostic_observational_use_blocked | collision_gap_nonpositive_blocks_exponential_forgetting_language, source_rank_near_zero_blocks_inverse_source_claim, line_of_sight_sign_phase_incoherence_blocks_source_upper_bound, visibility_gap_kernel_mask_not_bound_blocks_source_upper_bound |
| G2 | observational_blocked | observational_blocked | synthetic_manufactured_only | diagnostic_observational_use_blocked | acceleration_temp_gradient_block_missing_blocks_flrw_egs_promotion, derivative_weyl_diagnostics_missing_blocks_almost_egs_promotion, bianchi_i_assumptions_missing_blocks_g4_exact_flow_use, data_residual_provenance_not_bound_blocks_data_facing_residual |
| G5 | observational_blocked | observational_blocked | synthetic_manufactured_only | diagnostic_observational_use_blocked | stiff_fluid_singularity_blocks_g3_inversion, slope_degeneracy_blocks_slope_only_source_discrimination |
| S1 | convention_conditional | convention_conditional | synthetic_manufactured_only | diagnostic_observational_use_blocked | unbounded_multipole_bridge_blocks_s2_observational_use, harmonic_convention_not_bound_blocks_kl_bound_use |
| S3 | program_theorem | program_obligation | synthetic_manufactured_only | diagnostic_observational_use_blocked | collision_gap_nonpositive_blocks_exponential_forgetting_language, channel_operator_mismatch_blocks_dynamic_budget_certification |
| S4 | program_theorem | program_obligation | synthetic_manufactured_only | diagnostic_observational_use_blocked | samplewise_bound_violation_blocks_pi_domination |
| S5 | convention_conditional | convention_conditional | synthetic_manufactured_only | diagnostic_observational_use_blocked | metric_mask_lipschitz_not_bound_blocks_physical_cover_use |

## Required Kill Switches

- acceleration_temp_gradient_block_missing_blocks_flrw_egs_promotion
- bianchi_i_assumptions_missing_blocks_g4_exact_flow_use
- channel_operator_mismatch_blocks_dynamic_budget_certification
- collision_gap_nonpositive_blocks_exponential_forgetting_language
- data_residual_provenance_not_bound_blocks_data_facing_residual
- derivative_weyl_diagnostics_missing_blocks_almost_egs_promotion
- harmonic_convention_not_bound_blocks_kl_bound_use
- line_of_sight_sign_phase_incoherence_blocks_source_upper_bound
- metric_mask_lipschitz_not_bound_blocks_physical_cover_use
- samplewise_bound_violation_blocks_pi_domination
- slope_degeneracy_blocks_slope_only_source_discrimination
- source_rank_near_zero_blocks_inverse_source_claim
- stiff_fluid_singularity_blocks_g3_inversion
- unbounded_multipole_bridge_blocks_s2_observational_use
- visibility_gap_kernel_mask_not_bound_blocks_source_upper_bound
