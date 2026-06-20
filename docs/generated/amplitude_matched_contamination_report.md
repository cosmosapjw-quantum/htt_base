# Amplitude-Matched Contamination Report (REV-R095)

owner: HTT
implementation_scope: htt
claim_tier: blocked
transfer_source: none
sky_support_status: not_directional
null_mock_status: externally_audited_amplitude_matched_contamination
config_hash: `sha256:26837bcc31cc2f281414fbf67f5bfa2e5ca7f549ced6bf0be6bd32490d3c90e5`
input_hashes:
- audit_ver2.md:externally_audited_amplitude_matched_contamination
generating_command: `venv/bin/python -m htt.infer.amplitude_matched_contamination`
git_commit_or_worktree_state: `externally_audited_fixture`

## Negative result

Trigger `lnB_gt_5` fired on 95 of 100 amplitude-matched contamination-only mocks.

- Raw false-positive rate: 0.95
- Wilson 95% interval: [0.8882, 0.9785] (wilson_score_z_1.96)
- Tolerated contamination ceiling: 0.05
- Source identification status: failed
- Headline Bayes factor allowed: false

## Caveats

- amplitude-matched contamination null is a negative result
- a high false-positive rate blocks source identification
- no positive Bayes-factor headline may be drawn while blocked
- no native low-ell solver output is introduced
