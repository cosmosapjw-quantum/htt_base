# Canonical-tree rehearsal report

The PREP-05 overlay was applied to a fresh extraction of
`htt_base_code_capability_audit_package.zip`.

| Check | Result |
|---|---|
| Source archive SHA-256 | `90c2d9cc4af7829ff89b5fba87ebadd12b09657f0472d4b3bd6b25435a2742f1` |
| Source tree | supplied `code_capability_audit` disclosure |
| Dry-run path discovery | PASS |
| New production files | 9 |
| Non-identical overwrite conflicts | 0 |
| Repeated application idempotence | PASS; all 9 files reported identical |
| External theorem/property tests | 23/23 PASS |
| Python compileall | PASS |
| Raw data used | no |
| Old Rust FLRW/Bianchi output used | no |

This rehearsal proves path compatibility with the supplied disclosure tree, not
with an unseen later local commit. The local preflight must therefore compare
the actual repository and fail on conflicts before any merge.

## Final fresh-snapshot rehearsal

- preflight: PASS
- production overlay: 9 files, 0 conflicts
- repository scaffold: 21 files
- full-tree `compileall`: PASS
- import smoke: PASS
- theorem/property gates: 23/23 PASS
- forbidden old-Rust science dependency scan: PASS
- raw data analysis: not run
- canonical private/full regression: delegated to LR-06A

The verifier fixes BLAS/OpenMP thread counts to one for deterministic execution.
