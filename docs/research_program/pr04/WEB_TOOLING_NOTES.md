# Current repository-tooling notes (2026-06-23)

- The CI scaffold uses a Python-version matrix and explicit `setup-python`.
- Structured research execution tickets are provided as a GitHub issue form.
- A parent research issue should group the LR-06 tickets as dependency-ordered sub-issues.
- The hosted-runner workflow uses current major GitHub actions; self-hosted runners must be current enough for their Node runtime.

These are workflow conveniences only. They do not alter scientific gates or
claim ownership.

- Gate logs are uploaded with `actions/upload-artifact@v4`; matrix jobs use unique artifact names.
- The workflow tests the declared minimum Python 3.10 as well as 3.11–3.13.
