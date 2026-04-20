# VER2 Execution Ledger

**Authority**: `docs/ver2_upgrade/*`  
**Status**: live execution ledger for VER2 packets

## 0. Rules

1. Every executed packet appends one row.
2. Rows are append-only; corrections go in a new row.
3. If a packet changes shared schema, mark `shared_schema_touched=yes`.
4. If a packet stops before commit, record `commit_status=aborted` and explain why.

## 1. Packet Rows

| Date | Packet | Lane | Scope | Shared schema touched | Verification status | Commit status | Notes |
|---|---|---|---|---|---|---|---|
| 2026-04-20 | SK-00 | supervisor | schema barrier, ledgers, audit stubs, owner tests | yes | static green, targeted tests pending/see audit | local changes staged in workspace only | canonical common schema freeze and VER2 docs barrier established |
| 2026-04-21 | SK-01C | C | shared contracts, wrapper aliases, owner hooks, contract tests, audit note | yes | static green; targeted pytest `58 passed`; `py_compile` passed | committed | canonical common layer now includes atlas-lite, departure, TSC overlay, claim-ledger row, and thin workspace aliases/hooks without widening into solver physics |
| 2026-04-21 | SK-05T | T | TSC service skeletons, domain guard, no-overclaim lint, overlay builder, advisory adapters, theorem map, tests | no | static green; targeted pytest `97 passed`; `py_compile` passed | committed | TSC now exposes active-service skeletons without taking runtime or posterior ownership; overlay/lint/adapters remain package-local and manifest-backed |
| 2026-04-21 | SK-09D | D | exporter skeleton, generated manuscript hooks, figure-manifest audit, phase placeholder index, audit note | no | static green; `py_compile` passed; exporter `--check` passed | committed | solver-independent D-lane scaffold now blocks legacy paper figures without manifests and routes manuscript status/claim hooks through generated VER2 surfaces |
| 2026-04-21 | SK-07M | M | MIO manifest/status plumbing, residual-atlas skeleton, certificate payload export, MIO tests, audit note | no | static green; targeted pytest `153 passed`; internal-doc + web-CRAG + integrated audit complete | committed | every touched MIO certificate producer now attaches VER2 manifest-backed production status and explicit covariance/atlas/null-mock caveats; predictive residual atlas exists as a blocked skeleton rather than an implicit future hook |
| 2026-04-21 | SK-06H | H | HTT directional shell contracts, axis/scope gates, local-vs-global discrimination shell, bridge promotion gate, HTT tests, audit note | no | static green; targeted pytest `44 passed`; full `htt/htt/tests` `265 passed`; internal-doc + integrated audit complete; web-CRAG not needed | committed | HTT now has common-contract-bound directional shell inputs, closed-fail production axis/promotion guards, explicit matched-complexity/null-competition hooks, and hard blocks on MIO certificate merge / TSC posterior correction within the H-lane skeleton scope |
| 2026-04-21 | SK-01S1 | S1 | VER2 algebra object, tetrad geometry operators, constraint residuals, orthogonal/tilted IC shells, background RHS shell, Weyl hooks, background tests, audit note | no | static green; targeted pytest `174 passed`; touched-surface pytest `696 passed`; `py_compile` passed; internal-doc + web-CRAG + integrated audit complete | committed | BASS now exposes canonical 11-type algebra/geometry/background skeleton interfaces beside the legacy reduced solver, with explicit class-B axis reconciliation and machine-readable constraint residuals |
| 2026-04-21 | SK-02S2 | S2 | VER2 frame split, geodesic shell, PSTF radiation shell, electron-frame Thomson shell, scalar history/visibility shell, quadrupole startup shell, seed-compatibility shell, S2 tests, audit note | no | static green; targeted pytest `22 passed`; touched-surface pytest `1742 passed`; `py_compile` passed; internal-doc + web-CRAG + integrated audit complete | committed | BASS now freezes the S2 ownership split (`n^a` transport vs electron-frame collision/visibility), explicit low-ell radiation/truncation metadata, scalar-history-first-pass visibility/reionization hooks, startup/seed shells, and a tiny negative `Gamma_T` numerical floor for legacy integrator stability |
| 2026-04-21 | SK-03S3 | S3 | VER2 runtime/execution controls, source-propagator shell, cutoff campaign shell, observer-neutral solver-output builder, S3 tests, audit note | no | static green; targeted pytest `13 passed`; selected touched-surface pytest `437 passed`; `py_compile` passed; internal-doc + web-CRAG + integrated audit complete; full `htt/bass/runtime` collection still blocked by a pre-existing `bass.background`/`bass.tilt` import cycle outside S3 write scope | committed | BASS now exposes canonical Tier A/Tier B execution-plan shells, explicit exact/approximate/disabled flags, anisotropic propagator metadata, cutoff/convergence campaign hooks, and a manifest-backed `SolverCoreOutput` builder without embedding observational interpretation |
| 2026-04-21 | SK-04O | O | VER2 observable-vector builder, sparse covariance proxy, atlas-lite builder, full-cov MES no-claim gate, xQPiFG descriptive plumbing, workspace aliases, O-lane tests, audit note | no | static green; targeted pytest `103 passed`; touched-surface pytest `65 passed`; `py_compile` passed; internal-doc + web-CRAG + integrated audit complete | committed | BASS now exposes manifest-backed `ObservableVector`, covariance/BiPoSH proxy, `AtlasEntryLite`, `FullCovMESReport`, and descriptive `DepartureReport` producers without promoting diagonal-only compression, rank-deficient covariance, or uncertified filling language into production claims |

## 2. Next Row Template

| YYYY-MM-DD | <packet> | <lane> | <write scope summary> | yes/no | static/dynamic/audit verdict | committed/aborted | <short note> |
