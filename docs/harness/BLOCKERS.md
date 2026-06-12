# Blockers

Open blockers, owner, required resolution, and PR dependency impact.

## 2026-06-12

No active PR blockers after PR-040. Progress report shows unblocked next
candidates `PR-012`, `PR-022`, `PR-070`, `PR-015`, `PR-050`, and `PR-041`;
use DAG ordering and policy priorities before selecting the next node.

Residual non-blocking risk: `docs/generated/quarantined_figures.md` lists 96
existing figure/PDF assets without valid sidecar manifests. They are
diagnostic quarantine rows only and remain non-claim-bearing until future PRs
add valid provenance.

Residual non-blocking risk: PR-013 adds the new `HTTPosteriorBundle` type
firewall but does not migrate every legacy HTT inference path to that
constructor. Downstream HTT inference PRs should reuse
`reject_mio_likelihood_inputs` rather than creating new MIO/HTT merge helpers.

Residual non-blocking risk: PR-014 defines `TransferFunctionSpec` and an
in-memory registry, but existing transfer-dependent producers are not yet
migrated to emit those specs. Adapter PRs should attach this contract rather
than inventing local transfer metadata shapes.

Residual non-blocking risk: PR-040 defines rich sky-support metadata
validation, but existing producers are not yet migrated to validate every
sky-facing artifact through `validate_sky_facing_artifact_metadata`. Legacy
generated VER2 artifacts still load through backward-compatible
`SkySupport` defaults until migration PRs attach explicit coordinate-frame,
mask-hash, sky-fraction, and completeness payloads.
