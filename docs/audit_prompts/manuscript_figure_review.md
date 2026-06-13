# Manuscript And Figure Review

Review manuscript and figure audit materials.

Required checks:

- Missing and quarantined figure references remain blockers for a freeze.
- No figure is used without manifest metadata.
- Manual status numbers are treated as audit findings until regenerated.
- Generated reports quote hashes or source locations instead of unsafe source
  text where needed.
- Claim-risk rows are audit rows, not scientific results.

Return the smallest set of missing manifests, removed figure references, or
regenerated report inputs needed before a freeze.
