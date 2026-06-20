# Channel-Occupancy Repair Report (REV-R094)

owner: MIO
implementation_scope: mio
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `Codex REV-R094 block scalar occupancy overclaim`
git_commit_or_worktree_state: pending_rev_r094_commit

## Purpose

Promote the channel-matched occupancy vector as the only surface allowed to use
occupancy language, and block scalar `Q`/`F` displays from using occupancy
wording unless their numerator and denominator channels match or a joint
admissible-ceiling proof is attached.

## Contract

`mio.formalism.channel_occupancy_vector` exposes two surfaces:

- `channel_matched_occupancy(rows, ...)` — strict bounded occupancy vector
  `F_i = X_i / U_i` with a per-row channel-matched denominator. Cross-channel
  denominators are rejected at construction.
- `classify_occupancy_language(numerator_channel, denominator_channel,
  requested_phrase, joint_admissible_ceiling_proof=None)` — language classifier
  for scalar rows. It returns:
  - `allowed = True`, `status = "channel_matched_occupancy"` when the channels
    match;
  - `allowed = True`, `status = "joint_admissible_ceiling"` when a joint
    admissible-ceiling proof is attached;
  - `allowed = False`, `status = "proxy_score_only"` with
    `blocked_reasons = ["channel_mismatch", ...]` otherwise.

## Scalar Q/F status

The scalar `Q = x / x_max` and `F = x_C / U` ratios place a departure
(tilt-sector dominated) numerator over a shear-sector ceiling, so their channels
do not match. They are therefore `proxy_score_only`: the generated current
science payload records
`departure_display_contract.scalar_q_f_occupancy_language` as
`proxy_score_only` with `channel_mismatch`, and the manuscript (Chapter 3
Layer 2, Chapter 9 filling diagnostic) labels them channel-mismatched proxy
scores, not physical occupancy.

## Status

- Channel-matched occupancy vector: promoted; the only occupancy-language lane.
- Scalar `Q`/`F`: `proxy_score_only`; occupancy/physical-occupancy wording is
  blocked unless the channels match or a joint admissible-ceiling proof exists.
