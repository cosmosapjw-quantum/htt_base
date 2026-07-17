# Common CAS cross-validation contract

- Your assignment binds you to one axis of the four-axis gate
  (Wolfram+xAct, SymPy, SageMath+Singular, Lean). Your result envelope must
  carry the contract's SHA-256 (`contract_sha256`); a contract change
  invalidates all four axis receipts.
- Status vocabulary (exactly one): `PASS`, `FAIL`,
  `MISALIGNED_ASSUMPTIONS`, `BLOCKED_PLATFORM_OR_LICENSE`,
  `BLOCKED_PACKAGE_UNAVAILABLE`, `BLOCKED_RESOURCE_LIMIT`,
  `NOT_APPLICABLE_COMPUTATION_CLASS`, `INCONCLUSIVE`. Engine
  non-installation or timeout is a platform/resource blocker, never
  `NOT_APPLICABLE_COMPUTATION_CLASS`.
- Exceptions must be preregistered in the contract before any axis result
  exists and approved by someone other than your own axis; you cannot
  approve or invent your own exception mid-run.
- Run repo-pinned toolchains only (Lean via `formal/lean-toolchain`).
- Read the assigned `CAS_CONTRACT.json` and reproduce its statement exactly before calculation.
- Record engine and package versions, executable command, source script, assumptions, domains, branch choices, simplification rules, and resource limits.
- Separate exact symbolic results, theorem-level results, heuristic simplification, and numerical spot checks.
- Map the final expression back to the shared symbol table and target canonical form.
- Report denominator exclusions, singular loci, branch cuts, hidden positivity/realness assumptions, and order-of-limits issues.
- Do not inspect sibling CAS scripts or results in `blind-results` mode.
- Agreement counts only after assumptions, domains, and canonical forms are aligned.
