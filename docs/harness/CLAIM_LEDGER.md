# Claim Ledger

Each claim needs owner, status, evidence, transfer source, claim tier, and caveats.

## PR-011 - Quarantined figure inventory

| Claim | Owner | Status | Evidence | Transfer source | Claim tier | Caveats |
|---|---|---|---|---|---|---|
| `docs/generated/quarantined_figures.md` records the current manifest quarantine state for figure/PDF assets scanned under `figures` and `docs`. | COMMON | DIAGNOSTIC_ONLY | generated artifact plus `python scripts/check_artifact_manifests.py --dry-run` | none | diagnostic_only | The inventory does not promote, regenerate, inspect, or interpret listed assets; missing manifests keep listed assets non-claim-bearing. |
| `workspace.contracts.htt_posterior` enforces the PR-013 MIO/HTT type boundary for the new HTT posterior bundle path. | COMMON/HTT | IMPLEMENTED | `venv/bin/python -m pytest tests/contracts/test_mio_htt_no_merge.py -q`; adjacent ownership/G19/cross-check suites | none | conditional | The contract rejects MIO diagnostic inputs for this new bundle path; it does not migrate all legacy HTT inference entry points. |
| `common.transfer_registry.TransferFunctionSpec` records PR-014 transfer provenance metadata and blocks external/native validation spoofing. | COMMON | IMPLEMENTED | `venv/bin/python -m pytest tests/contracts/test_transfer_registry.py -q`; adjacent ownership/artifact/schema suites | none | conditional | The contract records provenance for downstream results; it does not migrate existing producers or validate transfer physics. |
| `common.sky_support` and `common.contracts.SkySupport` record PR-040 sky-support metadata and block raw lon/lat mean summaries. | COMMON | IMPLEMENTED | `venv/bin/python -m pytest tests/htt/test_sky_support_contract.py -q`; adjacent manifest/common/MIO/HTT directional suites | none | conditional | The contract records coordinate frame, deterministic mask hash, sky fraction, completeness status, and unit-vector spherical mean provenance; it does not provide null/mock/covariance readiness, transfer validation, morphology compatibility, or family-ID evidence. |
