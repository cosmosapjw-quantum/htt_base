# Project State

Current DAG position: PR-032 complete after commits PR-000, PR-001, PR-002,
PR-003, PR-004, PR-005, PR-020, PR-010, PR-021, PR-011, PR-013, PR-014,
PR-040, PR-012, PR-022, PR-070, PR-015, PR-050, PR-041, PR-023, PR-071,
PR-080, PR-030, PR-113, PR-051, PR-042, PR-072, PR-081, PR-031, PR-052,
PR-043, PR-073, PR-082, and PR-032.

Progress after PR-032: 34/62 complete = 54.84%; dependency-weighted
completion = 59.49%; critical-path completion = 8/21 = 38.1%.

Current framework status: L0 orchestration and harness bootstrap. The repo has
inventory, editable install/import stabilization, pytest taxonomy, DAG/progress
harnessing, repo-scoped Codex asset/install verification, and generated
five-PR checkpoint artifacts with no-progress replan detection, and a
deterministic Codex pytest subset runner for collect/smoke/fast/package
commands. PR-010 adds canonical ownership, claim-tier, implementation-scope,
and bundle-role firewall contracts. Legacy `TSC`/`tsc` inputs normalize to the
canonical `TSC_LEGACY` owner/scope in canonical contract rows. PR-021 adds a
COMMON optional dependency registry and machine-local diagnostic report for
skip/blocker attribution. PR-011 adds COMMON artifact manifest validation
helpers and a generated diagnostic-only quarantine inventory for current
unmanifested figure/PDF assets. PR-013 adds an executable MIO/HTT type
firewall for the new HTT posterior bundle path, rejecting direct
`MioCertificate` objects, MIO-shaped payloads, MIO cross-check reports, and
MIO diagnostic scalar keys as HTT likelihood inputs. PR-014 adds COMMON
transfer-provenance contracts and a registry for source, family, valid range,
observable kind, normalization, calibration status, caveats, and validation
gates. PR-040 adds COMMON sky-support metadata and geometry guards for
coordinate frame, deterministic mask hash, sky fraction, completeness status,
sky-facing manifest validation, and unit-vector spherical means. This is not
scientific readiness evidence. PR-012 adds the generated COMMON DAG status
snapshot, claim ledger, and status matrix under `docs/generated/*`, and turns
the old manual `docs/status_matrix.md` and `docs/claim_ledger.md` surfaces into
generated-authority indexes. These rows are diagnostic project bookkeeping
only, with `production_validated` false for every PR-DAG row. PR-022 adds a
COMMON PR_DELTA/review-artifact generator and template with owner normalization,
overwrite protection, web-check status, and structured safe-default claim
metadata for future PR closeouts. PR-070 adds `htt.obsstat` as an OBSSTAT
facade over the canonical COMMON `ObservableVector`, with diagnostic-only
feature packaging for alm/scalar/morphology/null/template/covariance/BiPoSH
blocks plus recursive guards against HTT inference/evidence keys, MIO
certificate semantics, premature family-identification/ranking keys or values,
p-values without non-empty null/look-elsewhere provenance, and transfer-derived
blocks without COMMON transfer metadata. The installed `htt` wrapper aliases
the top-level `obsstat` package as `htt.obsstat`, and package smoke covers
temp-CWD imports. PR-015 adds `common.semantic_guards.no_overclaim` plus
`scripts/check_claim_language.py` as a COMMON claim-language hard-fail guard
for active docs/manuscripts/reports. The linter blocks pre-native scalar or
low-ell surrogate wording used for blocked geometry/family claims, TSC/Teff
full-solver or full-polarisation wording, MIO diagnostic promotion into
posterior/evidence wording, and external-transfer/native conflation while
allowing explicit negative guardrails and skipping archive/provenance surfaces
by default. PR-050 adds `mio.formalism` with a MIO diagnostic-only
`DepartureBundle` for signed `x_C` comparator projections. The bundle records
complete finite `B_C` components, signs, comparator, frame, units,
cancellation index, config/input hashes, caveats, and PR-014 transfer metadata
validation for transfer-derived bundles. It preserves negative `x_C` values and
does not expose a norm, positive-part score, inference field, native solver
validation, or geometry/family claim. PR-041 adds `htt.zoa.selection_ladder`
as an HTT diagnostic support ladder with separate raw, ZoA-masked,
angular-completeness, and mock-calibrated summaries, COMMON sky-support
metadata, config/input hashes, caveats, fail-closed diagnostic-axis export, and
production-mode strictness that forbids uniform fallback and requires adequate
mock-calibration weights without promoting support metadata to posterior
evidence. PR-023 extends the COMMON progress harness with explicit skipped-PR
accounting, deterministic scoreboard output, checkpoint markdown that lists
blocked/skipped/unblocked-next/replan state, and hard failures when skipped PRs
overlap completed/blocked/in-progress states. PR-071 adds
`htt.obsstat.alm_conventions` as an OBSSTAT diagnostic convention registry for
harmonic feature export. It requires channel-local convention metadata for
alm-like payloads, records `scipy.special.sph_harm_y` evaluator provenance,
healpy m-major storage, coordinate frame, scalar/spin reality metadata,
Q-then-U spin-2 input order, no E/B sign export, and coefficient-shape checks,
and rejects unknown convention fields or coordinate-frame mismatches against
`SkySupport`. PR-080 adds `bass.transfer` as a BASS_PY provenance wrapper for
current external/proxy legacy transfer callables. It registers
AniCLASS-calibrated low-ell scalar and shear-to-D2/D3 paths as
`AniCLASS_external`, the BASS power-law comparison path as `empirical_proxy`,
and records callable path, callable input domain, PR-014 transfer metadata,
canonical `conditional` claim tier, `diagnostic_only` production status,
`transfer_conditional=True`, and `native_solver_result=False`. The PR card
path `htt/src/bass/transfer/...` is stale for this checkout; the live BASS
package root is `htt/bass`. PR-030 freezes TSC/Teff as `TSC_LEGACY`
legacy-reproduction and import-compatibility surface only. It adds the
`tsc_legacy` metadata package and manifest helper, keeps `import tsc` quiet for
warning-as-error harnesses, updates TSC deprecation docs,
normalizes old raw `owner="TSC"` pack refs to canonical `TSC_LEGACY` manifests
in bridge loaders, adds package-discovery checks, and pins current production
`tsc.*` imports to an advisory/caveat-only allowlist. PR-113 adds
`scripts/audit_manuscript_figures.py` as a COMMON/MANUSCRIPT diagnostic-only
inventory tool. It parses manuscript `\includegraphics` and `\graphicspath`
usage, joins current PR-011 figure quarantine state, scans text through the
COMMON claim guard plus manuscript-specific manual-status and claim-risk
patterns, and writes `docs/generated/manuscript_figure_inventory.md` and
`docs/generated/missing_figure_references.md`. The current inventory records
94 includegraphics refs, 0 manifest-backed resolved refs, 72 quarantined refs,
22 missing refs, and 23 text audit findings. It is not a LaTeX build proof, not
a figure promotion path, not transfer validation, not HTT evidence, not a MIO
certificate, and not a family-identification claim. PR-051 adds
`mio.formalism.BudgetSpec` as a MIO diagnostic-only denominator-policy
contract. It separates `MES_linear`, `external_transfer`, `atlas_quantile`, and
`observational` policies; requires positive finite denominators; preserves
PR-014 transfer metadata through transfer-dependent sensitivity points; uses
controlled pre-solver atlas status vocabulary; requires observational
sky-support/covariance/null status metadata; and restricts the legacy
COMMON/BASS descriptive report bridge to explicit `MES_linear`/`linear_MES`.
It does not implement Q/F/Pi/G_F, certified filling, HTT evidence/posteriors,
MIO certificates, native solver validation, morphology compatibility, or
geometry/family-classification surface.

Scientific boundaries remain active:

- no native low-ell Bianchi solver implementation in this repo;
- external transfer outputs remain transfer-conditional;
- MIO diagnostics do not produce posterior odds or truth certificates;
- HTT owns model-dependent posterior/evidence semantics;
- Bianchi family identification is blocked until native low-ell morphology
  atlas plus null/mask/covariance/equivalence/rank/PPC gates.

Latest progress scoreboard: `docs/generated/progress_checkpoints/progress_scoreboard.md`.
Latest checkpoint artifact: `docs/generated/progress_checkpoints/checkpoint_035.md`.
Next checkpoint is due at 40 completed PRs.

Next topological PR: PR-074. Other unblocked candidates after PR-053 are
PR-083 and PR-054.

## PR-032 update

PR-032 adds `scripts/codex_harness/generate_theorem_to_test_map.py`,
`docs/generated/theorem_to_test_map_legacy_tsc.json`,
`docs/deprecation/theorem_to_test_map.md`, and
`tests/contracts/test_theorem_to_test_map.py`. The generated map is
COMMON-owned, diagnostic-only audit metadata derived from
`tsc.validation.theorem_map` with `TSC_LEGACY` provenance. It records legacy
theorem labels, validation obligations, and live witness pytest node paths, but
does not provide production validation, HTT evidence, a MIO certificate,
transfer/native validation, morphology compatibility, or
geometry/family-identification evidence.

Latest unblocked candidates after PR-032 are PR-053, PR-074, and PR-083. The
next topological PR is PR-053. The next five-PR checkpoint is due after one
more completed PR, at 35/62.

## PR-053 update

PR-053 adds `mio.formalism.CertifiedFillingFraction` and
`tests/mio/test_filling_fraction.py`. F is a MIO diagnostic-only certified
filling fraction computed sample-wise as signed sign-clean `x_C / U` under a
PR-051 admissible certified ceiling. Invalid negative sectors, non-positive or
non-finite ceilings, and values outside `0<=F<=1` fail closed without
clipping. `F_Bayes` is the arithmetic mean of sample-wise F values, not a
ratio of means. F payloads require owner/scope/claim tier, config/input
hashes, generating command, git or worktree provenance, transfer provenance,
and sky/covariance/null status metadata.

Checkpoint 035 was written after PR-053. Progress is 35/62 = 56.45%;
dependency-weighted completion is 61.54%; critical path is 9/21 = 42.86%;
no blocker or replan was reported. Latest unblocked candidates are PR-074,
PR-083, and PR-054. PR-053 does not create HTT evidence or posterior content,
a MIO certificate, native solver validation, transfer validation, morphology
compatibility, or geometry/family-identification evidence.
