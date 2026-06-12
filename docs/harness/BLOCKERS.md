# Blockers

Open blockers, owner, required resolution, and PR dependency impact.

## 2026-06-12

No active PR blockers after PR-022. Progress report shows unblocked next
candidates `PR-070`, `PR-015`, `PR-050`, `PR-041`, and `PR-023`; use DAG
ordering and policy priorities before selecting the next node.

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

Residual non-blocking risk: PR-012 makes `docs/generated/*` the generated DAG
status authority, but older VER2 manuscript generated snippets are still owned
by `scripts/ver2_artifact_export.py`. Downstream manuscript/export PRs should
consume or cross-check the PR-012 sidecars rather than reintroducing manual
status counts.

Residual non-blocking risk: PR-022 standardizes PR_DELTA scaffolds, but it
cannot force future agents to complete every section truthfully. Downstream PRs
still need claim scans, tests, generated artifacts, and reviewer loops before
commit.
