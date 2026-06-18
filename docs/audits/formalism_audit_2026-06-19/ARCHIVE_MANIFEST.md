# Formalism Audit Archive Manifest

owner: COMMON
implementation_scope: audit_archive
claim_tier: diagnostic_only
transfer_source: mixed_none_external_and_conditioned_legacy
sky_support_status: not_directional
null_mock_status: not_applicable_archive_intake
config_hash: none_manual_REV_R063_archive_intake
generating_command: mkdir/cp/unzip archive intake; see command log in response matrix
git_commit_or_worktree_state: 40f789da0e8b70472d6384d1f7a7b12019b50329 with untracked REV-R063 inputs/archive

## Archive Event

- Archive directory: `docs/audits/formalism_audit_2026-06-19/`
- Extraction time: `2026-06-19T00:42:55+09:00`
- Source cwd: `/home/cosmosapjw/Dropbox/bianchi/htt_base`
- Source branch: `main`
- Source HEAD: `40f789da0e8b70472d6384d1f7a7b12019b50329`
- Commit policy: no commit made; main-thread owns commits for REV-R063.

## Git State At Archive

```text
## main
?? "AUDIT_REPORT (1).md"
?? docs/audits/formalism_audit_2026-06-19/
?? docs/superpowers/plans/2026-06-19-formalism-audit-originality-program.md
?? formalism_originality_program.zip
?? statistical_formalism_audit_report.zip
```

## Source Inputs

| Source filename | Archived path | SHA256 | Notes |
| --- | --- | --- | --- |
| `formalism_originality_program.zip` | `docs/audits/formalism_audit_2026-06-19/formalism_originality_program.zip` | `57c00c1f3868fe0e62270b9625d5e97386c57925363a9bfb21137d9d8348bbc9` | Originality/proposal program source zip. |
| `statistical_formalism_audit_report.zip` | `docs/audits/formalism_audit_2026-06-19/statistical_formalism_audit_report.zip` | `bdfb44061817bf01ca543356daaf3110cff70878edd14d3d4c5cc27cc4f34377` | External formalism audit report source zip. |
| `AUDIT_REPORT (1).md` | `docs/audits/formalism_audit_2026-06-19/AUDIT_REPORT (1).md` | `6da68d227f733049ac8664893534867db0dac0e6c9002f55b0650b84eb4e026c` | Root-level extracted markdown intake copy. |
| `AUDIT_REPORT.md` from `statistical_formalism_audit_report.zip` | `docs/audits/formalism_audit_2026-06-19/statistical_formalism_audit_report/AUDIT_REPORT.md` | `6da68d227f733049ac8664893534867db0dac0e6c9002f55b0650b84eb4e026c` | Hash matches `AUDIT_REPORT (1).md`. |
| `verify_formalism_claims.py` from `statistical_formalism_audit_report.zip` | `docs/audits/formalism_audit_2026-06-19/statistical_formalism_audit_report/verify_formalism_claims.py` | `97ecdb132444f4498d3a53ede3206cdfb9ba5a02dcce2d76b19f8d9894ac93d5` | Original archived verifier. |
| `verify_formalism_claims.py` copied to archive root | `docs/audits/formalism_audit_2026-06-19/verify_formalism_claims.py` | `97ecdb132444f4498d3a53ede3206cdfb9ba5a02dcce2d76b19f8d9894ac93d5` | Root path required by REV-R063 validation command. |
| `docs/generated/current_science_plot_payload.json` | existing tracked payload | `4cd77a839f275f54c39a73d44184179163c498747b5db8beb6c411aacb996d03` | Verification target for archived audit verifier. |

## Extracted Proposal Files

| Archived path | SHA256 |
| --- | --- |
| `formalism_originality_program/00_STRATEGIC_OVERVIEW.md` | `4d3ea8de2d639884bb947e44bb31a83d24e1c0b4b3e05a26a00a868f15e01924` |
| `formalism_originality_program/01_NOVELTY_LEDGER.md` | `586186ebc4c00e79bc53b3c212f995362206596a1bc0879bde32358714a5db50` |
| `formalism_originality_program/02_REFRAME_AND_REORG.md` | `fc28ff3d2f38a33896112687010fc5296bf30681ca81cc0670a75839a17bc363` |
| `formalism_originality_program/03_UPGRADE_PLAN.md` | `eb50d72bfe4e32a26245a2cd977413c238164d91632566319a4c176d52b1bc8f` |
| `formalism_originality_program/04_EXPERIMENT_PROGRAM.md` | `b4168e110f023c9a1fbbc4b528a95735c3fd4260d8ce69e558b68cf38c129d72` |
| `formalism_originality_program/05_DEFENSE_DOSSIER.md` | `eaedf11a66bc311eec36eedc1488970c4fe23a8e660f8223cafa14d09ee082ac` |
| `formalism_originality_program/06_PRIOR_ART_POSITIONING.md` | `0faa4b5f651f1a85417b01329c0856c4f174b009c0658245f3a688c656d5ee6f` |
| `formalism_originality_program/README.md` | `79b824311989bfd6360b76a215a1e94aa9b150519cfb0781987a2ff0c1c7a62c` |
| `formalism_originality_program/experiment_tracker.xlsx` | `1de9b43cd651908fd25dce2fc6ed28f41be7d5f93ec858ff8a7de49a43e79b41` |

## Extracted Proposal Scripts

| Archived path | SHA256 |
| --- | --- |
| `formalism_originality_program/code/reference_formalism.py` | `36aadbcafbc3bcef81f1eb4d4d90e0ed78b0a790c01d5cb70c4c2ea4da3e80c9` |
| `formalism_originality_program/code/run_all.py` | `db82f6d1405903c6f4edfe8ec1d90c354caf9ee7b1a64ce402b2c6d65d843989` |
| `formalism_originality_program/code/semantic_firewall_fuzz.py` | `8c23fb7eae3ec91ea256c18e251017c45eb5cc1de57eada5d527ec6989b90d62` |
| `formalism_originality_program/code/exp01_cancellation_null.py` | `e42f0da283c4c95147b0e1bd6c9033edc7f0736760f1fa323a7b1d0fbaca1fe9` |
| `formalism_originality_program/code/exp02_F_failclosed_coverage.py` | `d326c5e8bb113828035b53e2be809f9d6ce4696891cd573bd78e557c3bd6d685` |
| `formalism_originality_program/code/exp03_Pi_threshold_bias.py` | `22ddab314393997eea885f7e7f64f928eb0b7aa8603bdc54d64bec9f0bbd2c9a` |
| `formalism_originality_program/code/exp04_GF_matched_null_boost_vs_tilt.py` | `22b8cdfbf0bbbe15cac49f4129194185f9fc89f4297e318bdb4d1f6bbaa354b6` |
| `formalism_originality_program/code/exp05_comparator_sensitivity.py` | `d0cbc2d0297248c242eed5091f5277eac2841ad65047693e6fd2e0b73c52d7a4` |

## Archive Caveats

- This archive records incoming audit/proposal artifacts only.
- The archived proposal scripts are reference/proposal material, not production HTT/MIO implementation.
- No native solver output, Bianchi geometry/family result, MIO posterior, or external-transfer-as-native validation is recorded here.
