# Blockers

Open blockers, owner, required resolution, and PR dependency impact.

## 2026-06-12

No active PR blockers after PR-023. Progress report shows unblocked next
candidates `PR-071`, `PR-080`, `PR-030`, `PR-113`, `PR-051`, and `PR-042`;
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

Residual non-blocking risk: PR-012 makes `docs/generated/*` the generated DAG
status authority, but older VER2 manuscript generated snippets are still owned
by `scripts/ver2_artifact_export.py`. Downstream manuscript/export PRs should
consume or cross-check the PR-012 sidecars rather than reintroducing manual
status counts.

Residual non-blocking risk: PR-022 standardizes PR_DELTA scaffolds, but it
cannot force future agents to complete every section truthfully. Downstream PRs
still need claim scans, tests, generated artifacts, and reviewer loops before
commit.

Residual non-blocking risk: PR-070 packages OBSSTAT observable features in the
canonical COMMON `ObservableVector`, but payload values remain descriptive
mappings. Later obsstat PRs should add richer harmonic-convention, shape, and
feature-family validation without importing HTT inference or MIO certificate
surfaces.

Residual non-blocking risk: PR-015 adds focused semantic regexes and CLI
enforcement, but it is not a complete natural-language classifier. Later claim
firewall PRs should add targeted rules from concrete drift findings and avoid
turning the active linter into a noisy word blacklist. Archive/provenance paths
are skipped by default; use `--include-archives` for historical audits.

Residual non-blocking risk: PR-050 validates signed `x_C` projection metadata
and transfer provenance, but component values remain caller-supplied. It does
not calibrate component physics, implement frame transforms, provide
covariance/null calibration, build certificates, or validate any native solver
output. Later MIO/obsstat/HTT PRs must attach those gates before stronger
statistical or morphology language is allowed.

Residual non-blocking risk: PR-041 separates ZoA support modes and records
mock-calibrated support metadata, but it does not validate a mock ensemble,
calibrate directional bias/coverage/FPR, or produce a posterior-derived
production axis. PR-042/PR-043 must preserve the fail-closed axis gate and add
statistical mock-coverage evidence before any production directional claim can
move beyond diagnostic support.

Residual non-blocking risk: PR-023 prevents explicit skipped PRs from inflating
completion percentages or satisfying dependencies, but it cannot prove that a
manually marked completed PR was genuinely reviewed. Continue enforcing the
per-PR loop: PR_DELTA, tests, claim scans, generated artifacts, self-review,
and commit evidence.
