# External Research Input Inventory

owner: COMMON
implementation_scope: external_research_input_intake
claim_tier: diagnostic_only
transfer_source: none
config_hash: sha256:4126d40877fc558463f07dba1c1653e747c4ec4697df4b143b35381f65af3be8
sky_support_status: not_directional
null_mock_status: not_statistical
archive_directory: `docs/audits/external_research_inputs_2026-06-20`
archive_manifest: `docs/audits/external_research_inputs_2026-06-20/ARCHIVE_MANIFEST.md`
generating_command: `venv/bin/python scripts/inventory_external_research_inputs.py --write`
git_commit_or_worktree_state: working-tree input snapshot hash-bound; uploaded root inputs were untracked at intake

## External-Input Status

Files copied into this directory are raw external audit/proposal inputs. They are hash-preserved for traceability and are not repo-authored current research claims, validation artifacts, publication evidence, or native-solver outputs.

## Canonical Sources

| Lane | Canonical input |
| --- | --- |
| `manuscript_audit` | `RESEARCH_AUDIT_REPORT.md` |
| `data_analysis_program` | `htt_publishable_novel_analysis_program_2026-06-19.zip` |
| `theorem_program` | `htt_beyond_mes_egs_theorem_program_2026-06-19.zip` |

## Inputs

| Input | Role | SHA256 | Size | Archive copy | Zip entries | Supersession | Top-level summary |
| --- | --- | --- | ---: | --- | ---: | --- | --- |
| `RESEARCH_AUDIT_REPORT.md` | `external_current_manuscript_audit` | `c2e57931109cdbdeb40c2a469db50a64626bb85d05c266f53fad369494d0a065` | 15.4 KiB | `docs/audits/external_research_inputs_2026-06-20/RESEARCH_AUDIT_REPORT.md` | n/a | canonical immediate manuscript-audit input for REV-R075 | n/a |
| `publishable_data_analysis_program.zip` | `external_compact_data_analysis_precursor` | `e2590f1ca79b63feecd77151de2f7f00b583f4f7f4b828d6e0d7642b00dba038` | 51.6 KiB | `docs/audits/external_research_inputs_2026-06-20/publishable_data_analysis_program.zip` | 19 | precursor cross-check; superseded for implementation by htt_publishable_novel_analysis_program_2026-06-19.zip | 00_STRATEGY_AND_PIPELINE.md (1 files, 0 dirs); 01_DIVERGENCE.md (1 files, 0 dirs); 02_METACOGNITION_AND_VERIFICATION.md (1 files, 0 dirs); 03_CONVERGENCE_EXPERIMENTS.md (1 files, 0 dirs); 04_THEOREM_CANDIDATES.md (1 files, 0 dirs); 05_AXIS_A_math_stats.md (1 files, 0 dirs); 06_AXIS_B_gr_cosmo.md (1 files, 0 dirs); 07_AXIS_C_data.md (1 files, 0 dirs); ... 4 more |
| `htt_publishable_novel_analysis_program_2026-06-19.zip` | `external_canonical_data_analysis_program` | `bb66be05bc94b1441519a5db7be31ec62eb501f463a9bea5c81bf555ef081393` | 23.6 MiB | `docs/audits/external_research_inputs_2026-06-20/htt_publishable_novel_analysis_program_2026-06-19.zip` | 186 | canonical joint rest-frame/data-analysis proposal input | htt_publishable_novel_analysis_program_2026-06-19 (149 files, 37 dirs) |
| `htt_beyond_mes_egs_theorem_program_2026-06-19.zip` | `external_canonical_theorem_extension_program` | `4c3c61a2ff3f98d1cdcf758476ea7ed6ec1499edb3b236d94b54c98be195037b` | 1.5 MiB | `docs/audits/external_research_inputs_2026-06-20/htt_beyond_mes_egs_theorem_program_2026-06-19.zip` | 119 | canonical beyond-MES/EGS theorem-extension proposal input | htt_beyond_mes_egs_theorem_program_2026-06-19 (107 files, 12 dirs) |
| `egs_theorem_program.zip` | `external_compact_egs_theorem_precursor` | `ea0ed4a05bbefff546f21a65df80474f254999bf854100d16e523fd9d384fed3` | 44.7 KiB | `docs/audits/external_research_inputs_2026-06-20/egs_theorem_program.zip` | 18 | precursor cross-check; superseded for implementation by htt_beyond_mes_egs_theorem_program_2026-06-19.zip | 00_STRATEGY_AND_PIPELINE.md (1 files, 0 dirs); 01_DIVERGENCE.md (1 files, 0 dirs); 02_METACOGNITION_AND_VERIFICATION.md (1 files, 0 dirs); 03_CONVERGENCE_EXPERIMENTS.md (1 files, 0 dirs); 04_THEOREM_CANDIDATES.md (1 files, 0 dirs); 05_AXIS_A_math_stats.md (1 files, 0 dirs); 06_AXIS_B_gr_cosmo.md (1 files, 0 dirs); 07_AXIS_C_data.md (1 files, 0 dirs); ... 4 more |

## Selected Documents

### `RESEARCH_AUDIT_REPORT.md`
- `RESEARCH_AUDIT_REPORT.md`

### `publishable_data_analysis_program.zip`
- `00_STRATEGY_AND_PIPELINE.md`
- `04_THEOREM_CANDIDATES.md`
- `07_AXIS_C_data.md`
- `08_PRIOR_ART_CRAG.md`

### `htt_publishable_novel_analysis_program_2026-06-19.zip`
- `docs/00_executive_strategy.md`
- `docs/03_flagship_joint_rest_frame_analysis.md`
- `docs/04_theorem_candidates_and_proofs.md`
- `docs/06_data_null_and_validation_requirements.md`
- `machine_readable/pr_dag.yaml`
- `machine_readable/experiment_registry.yaml`
- `machine_readable/theorem_registry.yaml`

### `htt_beyond_mes_egs_theorem_program_2026-06-19.zip`
- `docs/02_math_statistics_axis.md`
- `docs/03_gr_cosmology_axis.md`
- `docs/04_boltzmann_kinetic_axis.md`
- `docs/05_egs_synthesis_and_data_axis.md`
- `docs/07_proof_obligations_and_kill_switches.md`
- `docs/15_theorem_dependency_and_promotion_dag.md`

### `egs_theorem_program.zip`
- `00_STRATEGY_AND_PIPELINE.md`
- `04_THEOREM_CANDIDATES.md`
- `08_PRIOR_ART_CRAG.md`


## Input Hash List

- `RESEARCH_AUDIT_REPORT.md`: `c2e57931109cdbdeb40c2a469db50a64626bb85d05c266f53fad369494d0a065`
- `publishable_data_analysis_program.zip`: `e2590f1ca79b63feecd77151de2f7f00b583f4f7f4b828d6e0d7642b00dba038`
- `htt_publishable_novel_analysis_program_2026-06-19.zip`: `bb66be05bc94b1441519a5db7be31ec62eb501f463a9bea5c81bf555ef081393`
- `htt_beyond_mes_egs_theorem_program_2026-06-19.zip`: `4c3c61a2ff3f98d1cdcf758476ea7ed6ec1499edb3b236d94b54c98be195037b`
- `egs_theorem_program.zip`: `ea0ed4a05bbefff546f21a65df80474f254999bf854100d16e523fd9d384fed3`

## Caveats

- diagnostic/proposed inputs
- not publication evidence
- no native low-ell solver output or validation is present
- no Bianchi family identification
- no geometry-detection wording or evidence promotion
