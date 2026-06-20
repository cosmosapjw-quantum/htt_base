# Audit VER2 Response Matrix

owner: COMMON
implementation_scope: external_research_input_intake
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
config_hash: `sha256:4e7afaf16c97c5d1aeb174238c7ac9ef3cd19038fb0a0fb7a7730353cf4fd163`
generating_command: `Codex REV-R088 archive copy and response matrix`
git_commit_or_worktree_state: `working-tree input snapshot hash-bound during REV-R088`

## Priority Rule

Strict audit controls conflicts: `true`.

When `audit_ver2.md` and `RESEARCH_AUDIT_REPORT.md` disagree, the strict audit controls the revision path. The near-pass report is retained for quick wording and hygiene fixes only.

## Archived Inputs

| Input | Role | SHA256 | Archive copy | Status |
| --- | --- | --- | --- | --- |
| `audit_ver2.md` | `strict_external_reaudit` | `4c7cda3a41ea58c15d6382be7a523c57c2a2b0314250a2c78beada7bff515ddb` | `docs/audits/external_research_inputs_2026-06-20_reaudit/audit_ver2.md` | `raw_external_or_plan_input_hash_preserved` |
| `RESEARCH_AUDIT_REPORT.md` | `near_pass_external_reaudit` | `08c30c1df76a7808bfcbc31959d33660f10a45aaba2735935ed4ee1daa665b2d` | `docs/audits/external_research_inputs_2026-06-20_reaudit/RESEARCH_AUDIT_REPORT.md` | `raw_external_or_plan_input_hash_preserved` |
| `2026-06-20-audit-ver2-research-hardening.md` | `repo_authored_execution_plan` | `18f1b0b3886af572ea3ad4282a4197d9735fc37360455cba289d6c0baa1298c1` | `docs/audits/external_research_inputs_2026-06-20_reaudit/2026-06-20-audit-ver2-research-hardening.md` | `raw_external_or_plan_input_hash_preserved` |

## Fatal Blockers

| Blocker | Required policy | Next REV | Claim status | Summary |
| --- | --- | --- | --- | --- |
| `F1` | `positive_lnb_reclassified_as_amplitude_fit` | `REV-R089` | `blocked_source_identification` | Current configured likelihood cannot identify whether the admitted dipole amplitude is cosmological or systematic. |
| `F2` | `normal_frame_vorticity_zero_until_threading_identity` | `REV-R093` | `blocked_frame_identity` | Normal-frame Bianchi slicing and matter-threading vorticity are mixed in the current prose. |
| `F3` | `scalar_qf_proxy_until_channel_matched_or_joint_ceiling` | `REV-R094` | `blocked_scalar_occupancy` | Scalar Q and F denominator use is not an admissible occupancy certificate when numerator and ceiling channels differ. |
| `F4` | `no_single_jeffreys_label_without_prior_error_surface` | `REV-R096` | `blocked_prior_error_sensitivity` | Prior cutoff and external error budget sensitivity can reverse or inflate the configured evidence value. |

## Action Rows

| Category | Priority | Source | Next REV | Owner | Action | Safe wording |
| --- | --- | --- | --- | --- | --- | --- |
| `fatal_blocker` | P0 | `audit_ver2.md:F1` | `REV-R089` | HTT | Downclass positive Bayes-factor prose to premise-conditioned amplitude fit and bind the audited contamination-null failure as a blocker. | Given admitted amplitudes and selected priors, the configured likelihood admits a nonzero beta-like amplitude; source origin is not established. |
| `fatal_blocker` | P0 | `audit_ver2.md:F2` | `REV-R093` | BASS_COMMON | Separate hypersurface-normal slicing from any matter-threading vorticity candidate and block vortical rows until the full threading identity is derived. | The signed comparator coordinate is currently safe only in the stated irrotational normal-frame sector. |
| `fatal_blocker` | P0 | `audit_ver2.md:F3` | `REV-R094` | MIO | Replace scalar occupancy prose with channel-matched occupancy vectors or proxy-score language. | Scalar Q and F are diagnostic proxy scores unless channel-matched ceilings or a joint admissible ceiling are supplied. |
| `fatal_blocker` | P0 | `audit_ver2.md:F4` | `REV-R096` | HTT | Replace single Jeffreys-label evidence prose with a prior/error sensitivity gate and robust-range report. | Large likelihood-ratio values are prior- and error-budget-sensitive conditioned inputs until robustness gates pass. |
| `major_required_fix` | P1 | `audit_ver2.md:major findings` | `REV-R099` | OBSSTAT_HTT | Classify low-ell scalar likelihood rows into deterministic mean-template or covariance branches and block central scalar chi-square shortcuts. | Configured scalar D2/D3 rows provide no positive support for the shared beta-like parameter without the appropriate branch gates. |
| `major_required_fix` | P1 | `audit_ver2.md:major findings` | `REV-R097` | HTT | Create a joint survey hierarchy gate before multiplying CatWISE, radio, CF4, or local-flow amplitudes. | The current rows are heterogeneous conditional inputs, not a shared-source inference. |
| `major_required_fix` | P1 | `audit_ver2.md:statistics audit` | `REV-R098` | HTT | Treat the registered PPC failure and missing LOOCV as evidence blockers. | The single-beta likelihood or covariance model fails the registered predictive adequacy criterion for that channel. |
| `major_required_fix` | P1 | `audit_ver2.md:figure audit` | `REV-R092` | COMMON | Downgrade current figure lanes that are display-only, proxy-only, degeneracy, or appendix-only surfaces. | The figure is a diagnostic or negative-result surface, not evidence or discrimination proof. |
| `minor_repair_from_near_pass_audit` | P0 | `RESEARCH_AUDIT_REPORT.md:major findings` | `REV-R089` | COMMON | Remove legacy/oracle discovery wording, harmonize Pi namespaces, disambiguate F labels, and replace manual counts with generated-source status. | The neutrino quadrupole row is a derived transfer-conditional result; Pi and F labels carry their owner and definition. |
| `defensible_boundary_statement` | P0 | `audit_ver2.md:safe claims` | `REV-R089` | COMMON | Use only the strict audit defensible-boundary lane until hardening gates complete. | The framework provides a signed comparator coordinate in the single-perfect-fluid irrotational normal-frame sector; MIO and OBSSTAT outputs remain diagnostic, and Bianchi family claims remain blocked. |

## Caveats

- response matrix only; no scientific result is promoted
- canonical PR DAG status is not rewritten
- external/proxy transfer remains transfer-conditional
- native low-ell morphology atlas remains absent
- MIO diagnostics remain separate from HTT evidence
