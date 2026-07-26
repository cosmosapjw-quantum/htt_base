# Overnight controller: publication-safe terminal contract

The controller may create internal findings, local commits, and one coherent
`changeset/` branch. It must not push, create or mutate a GitHub PR, or invoke
an external publisher.

A successful unattended terminal report contains:

- `work_unit_id`, canonical `change_set_id`, and `publication_group_id`;
- explicit target remote, branch, and starting SHA;
- local candidate branch and commit list;
- candidate seal path/hash, or `NO_FROZEN_CANDIDATE` with a reason;
- registered reviewer results and coverage disposition, if frozen;
- latest-target integration disposition, if frozen;
- `github_pr_created_by_harness=false`;
- one of `BLOCKED`, `CANDIDATE_READY_FOR_REVIEW`, or
  `READY_FOR_EXTERNAL_PUBLISHER`.

`READY_FOR_EXTERNAL_PUBLISHER` is a recommendation, not publication
authorization. Only the credential-isolated serialized publisher can consume a
short-lived authorization and create the single GitHub PR.
