# Blockers

Open blockers, owner, required resolution, and PR dependency impact.

## 2026-06-13

No active DAG blockers after PR-054. Progress report shows unblocked next
candidates `PR-075` and `PR-055`; use DAG ordering and policy priorities
before selecting the next node.

Manuscript-freeze blocker: `docs/generated/missing_figure_references.md`
records 22 missing manuscript figure references, 72 path-resolved but
quarantined references, and 23 text audit findings. Final manuscript freeze
remains rejected until each missing/quarantined reference and stale/manual
status or claim-risk finding is explained, regenerated with manifests, or
removed.

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

Residual non-blocking risk: PR-071 records harmonic/spin convention metadata
and blocks OBSSTAT alm exports without channel-local metadata, but it does not
compute alms, validate maps, assert E/B sign export, or provide transfer
provenance. Downstream obsstat/transfer PRs must keep convention provenance
separate from PR-014 transfer metadata and from any future native solver atlas
validation.

Residual non-blocking risk: PR-080 wraps existing legacy transfer-dependent
scalar callables with PR-014 metadata, but it does not rederive or recalibrate
the AniCLASS external calibration, execute CLASS/AniCLASS, validate a native
transfer solver, or migrate downstream HTT/MIO producers. Later PRs must
consume the registry without relabeling external/proxy outputs as native.

Residual non-blocking risk: PR-030 freezes TSC/Teff as `TSC_LEGACY`
legacy-reproduction and import-compatible advisory chart diagnostics only, but
current MIO/HTT/BASS production modules still have a small static allowlist of
legacy `tsc.*` imports. The allowlist is tested and must not expand without
explicit claim-gate review; PR-031 should extract generic semantic guards so
future framework code does not grow new TSC ownership.

Residual non-blocking risk: PR-113 inventories manuscript figure references
and text risks, but it does not regenerate figures, add manifests, edit
manuscript claims, or prove LaTeX buildability. Later manuscript/export PRs
must consume `docs/generated/manuscript_figure_inventory.md` and
`docs/generated/missing_figure_references.md` before promoting any figure or
status number into a publication-facing surface.

Residual non-blocking risk: PR-051 defines strict MIO `BudgetSpec`
denominator-policy and sensitivity metadata, but the older COMMON
`BudgetSpec` still exists as a weaker compatibility contract. The BASS legacy
bridge is restricted to explicit `MES_linear` only. PR-052 and later Q/F/Pi/G
work must consume the MIO contract directly rather than relabeling legacy
COMMON budgets as external-transfer, atlas, or observational policies.

Residual non-blocking risk: PR-053 adds a strict MIO certified F contract, but
it remains diagnostic bookkeeping. It does not calibrate F statistically,
provide PPC/LOOCV/null support, validate native transfer, or connect to a
native morphology atlas. Legacy BASS descriptive report code still has an old
proxy/clipping path; downstream PRs must use `mio.formalism.CertifiedFillingFraction`
for certified F semantics rather than the legacy report shell.

Residual non-blocking risk: PR-074 adds an OBSSTAT template-fit diagnostic with
orientation-scan and covariance-weighting metadata, but it does not provide a
matched-null tail probability, look-elsewhere correction, HTT posterior or
evidence semantics, MIO report content, transfer validation, native solver
output, morphology compatibility, or geometry/family-identification evidence.
Downstream template/null PRs must keep deterministic template-mean fits
separate from covariance anomaly statistics and matched-null calibration.

Residual non-blocking risk: PR-083 adds a BASS budget ceiling policy interface
and MIO reference bridge, but it does not compute downstream Pi/G_F report
cards, validate native solver output, validate external transfer as native, or
provide a native morphology atlas. Downstream MIO PRs must keep `U_C`
selection provenance visible, preserve rank/depth-gap gates, and reject any
threshold language that turns diagnostic exceedance or filling-fraction
bookkeeping into a truth probability or geometry/family-identification claim.

Residual non-blocking risk: PR-054 adds a MIO diagnostic Pi exceedance-curve
contract, but it does not calibrate p-values/FPR, perform PPC/LOOCV, validate
native transfer, or connect to a native morphology atlas. Downstream MIO/HTT
report-card and posterior-pushforward PRs must preserve the explicit
`measure_kind`, threshold-policy metadata, PR-014 transfer provenance, and
null/mock support gates, and must not promote Pi into truth probability,
posterior/evidence, native validation, morphology compatibility, or
geometry/family-identification language.
