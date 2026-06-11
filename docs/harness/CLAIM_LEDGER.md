# Claim Ledger

Each claim needs owner, status, evidence, transfer source, claim tier, and caveats.

## PR-011 - Quarantined figure inventory

| Claim | Owner | Status | Evidence | Transfer source | Claim tier | Caveats |
|---|---|---|---|---|---|---|
| `docs/generated/quarantined_figures.md` records the current manifest quarantine state for figure/PDF assets scanned under `figures` and `docs`. | COMMON | DIAGNOSTIC_ONLY | generated artifact plus `python scripts/check_artifact_manifests.py --dry-run` | none | diagnostic_only | The inventory does not promote, regenerate, inspect, or interpret listed assets; missing manifests keep listed assets non-claim-bearing. |
