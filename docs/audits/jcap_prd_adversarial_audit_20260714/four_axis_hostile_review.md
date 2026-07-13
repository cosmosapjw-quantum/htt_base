# Delta adversarial audit: four-axis hostile review

## Scope and decision object

This review audits the repository as shipped at
`8af39b36c1d5ed4f9b16f0bc71dbecd8b22548d4`; PR-116 at
`f8c90f918e1d6bf1187e8143ddccbf00eddc470c` only adds the isolated audit
harness. DAG completion (`62/62` at the baseline) is bookkeeping, not
scientific readiness.

The prior self-audit is not being relitigated. Its 55 findings are imported
unchanged as `KNOWN_OPEN` (`P0 2 / P1 14 / P2 17 / P3 22`), together with its
14 audit-completeness gaps. A candidate delta was admitted only for demonstrated
downstream propagation, regression, contradictory independent reproduction,
severity change, or historical antecedent. Multiple agent names for one
mechanism were merged by the root adjudicator.

**Delta result:** 33 new open atomic findings (`P1 22 / P2 11`), grouped into
13 remediation work packages, plus one P2 audit-harness finding repaired during
PR-117. Two additional candidates are explicit `REUSE_PRIOR` rows. There is no
new P0. The absence of a new P0 does not lower either imported P0. The atomic
census and one-to-one source assignment are authoritative in
`atomic_finding_ledger.json`; the tables below are work-package summaries.

**As-shipped scientific verdict:** **REJECT** as a positive anisotropy,
global-tilt, FLRW-violation, geometry, family, precision-growth, evidence, PPC,
LOOCV, or publication-readiness paper.

**Strongest defensible object after major surgery:** a claim-tiered,
transfer-conditional pre-solver methods and negative-audit paper about
identifiability, local/global discrimination design, and reproducible diagnostic
contracts. Current observational examples must be labelled conditional or
blocked. No present result identifies a Bianchi family or geometry.

## Evidence protocol

The initial CRAG packet contains 75 primary/official sources and is sealed by
`WEB_LOCK.json` at
`sha256:459fbbb67b8ef769b7b2b9f212ba2add28c22129638d206d7ce4e14e2c1668c5`.
After that seal, every hostile-review, recalculation, and debate agent declared
`web_used=false`; only the frozen packet, repository, Git history, legacy
archives, and hashed local data were allowed. Final candidate-specific web
checking is deferred to PR-118.

The workflow used root plus three agents per wave:

1. theory: anisotropy advocate, isotropy advocate, GR/convention auditor;
2. statistics: Bayesian evidence/PPC/LOOCV, frequentist null/trials,
   partial-identification/systematics;
3. code: numerical analyst, reproducibility engineer, oracle/provenance attacker;
4. data: CMB observer, CF4 observer, DESI/JWST survey analyst;
5. cross-debate: physics/observation, formalism/statistics,
   integrity/novelty;
6. three digest-blind referees, each restricted to sampled primary artifacts
   and a common rubric.

Raw prompts and responses are preserved under `agents/`; hashes and web receipts
are bound by `debate_bundle.json`. The detailed finding schema, defenses,
rebuttals, falsifiers, consumers, and merge decisions live in
`root_adjudications.json`.

The digest-blind theory referee independently reproduced the FLRW converse,
beta/EGS, NT-A3 floor, and linear-versus-quadratic `Omega_tilt` defects and
returned **reject/resubmit** after 79 direct tests passed. The digest-blind data
referee independently reproduced the malformed Hermitian CF4 generator,
reconstruction-dependent `f sigma_8`, prior DESI weighted-shot finding, and
stale/statistically mis-scoped JWST forecast; these map to existing prior or
canonical deltas rather than new IDs. The digest-blind reproducibility referee
independently obtained green freeze/package checks beside failed freshness and
canonical-manifest checks, returning **not release-ready**. Their agreement is
independent of the shared hostile-review digest by construction.

## Audit-only executions

No production result was overwritten. A process exit of zero means the audit
runner executed; it does not override a scientific `BLOCKED` status.

| Lane | Executed result | Hostile adjudication |
| --- | --- | --- |
| CF4 monopole | Standard MV `405.222 km/s`, constrained shell-null `94.155 km/s`, projected monopole `473.053 km/s`; constraint residual `1.10e-15`; 512 on-model injections reduce RMSE `274.4 -> 33.6 km/s` | The nuller is a valuable sensitivity, not corrected truth. It does not cover catalogue selection, nonlinear distance transform, reconstruction covariance, or realistic correlated fields. |
| CF4 downstream | Shipped GLS `340.726 km/s` maps to `Omega_tilt=4.073e-7`; constrained sensitivity maps to `3.110e-8` | Known P0 propagates into live theory consumers; measured global tilt is blocked. |
| CF4 `f sigma_8` | Raw fits move `0.299 -> 0.486` with depth; shell-centred values remain `0.292 -> 0.308`; Fisher error at full depth `0.0217` | The claimed precision and “4.9 sigma” comparison are unsupported without a valid likelihood and same-data joint covariance. |
| GRF | Current/reference component variance ratios `0.8245, 0.8346, 0.9840` over 16 fixed seeds | Independently reproduces the imported Hermitian-plane finding; no duplicate ID. |
| DESI | 400 mocks, alpha refit per mock; `p_rank=0.6833`; `n_z=200/400` C_ell agreement within `0.02%` | The in-house GRF null is numerically repaired and non-anomalous, but exact-selection official BGS_ANY mocks are absent. |
| ACT | 53 release files, 13 kappa alm products, 13 masks, 402 local simulation files, zero raw filtered-CMB/QE inputs | Same-release alm percentile is possible; native sky-power interpretation at `L=2..10` is `BLOCKED`, outside the frozen published `40<L<763` validation range. |
| K6 | Fourth/second-order residual ratio `13.66` at the native grid; errors decrease with grid/order | This is a discretization floor on a by-construction irrotational product, not a measured physical curl. Reuse the prior finding. |
| JWST | 14-anchor rerun, scenario gain `1.060`; shared 0.05 mag systematic gives `1.047`; committed result has 9 anchors | Arithmetic drift is fixed only in audit. Raw row provenance, per-host weighting, shared covariance, and object-identity crossmatch remain unresolved. |

The executable record also preserved scientifically important failures:

- clean-CWD `import htt.bass` fails despite passing packaging tests;
- current manuscript figure check fails on 5 stale surfaces;
- VER2 exporter fails on 15 stale surfaces;
- generic canonical manifest audit reports 31 quarantined figures and 98 issues;
- publication-freeze and external-package checks pass in the same worktree;
- the external package can contain 28/232 canonically invalid sampled figure
  manifests while reporting no package failed gate.

## Theory axis

### Steelman

The strongest theory contribution is not a detected Bianchi family. It is a
pre-solver programme of exact limits, cancellation witnesses, response rank,
equivalence classes, regular-tensor/shear response, and local-versus-global
discrimination. Several qualitative sign/nondegeneracy results survive. The
classical coupled VII_h temperature template is not the whole space of weak
homogeneous or regular tensor modes, so an isotropic null cannot prove exact
isotropy.

### Hostile result

| Canonical delta | Level | Ruling |
| --- | --- | --- |
| `D-THEORY-FLRW-EGS-SEMANTICS` | P1 | `x_C=0`, zero matter-radiation displacement, and a repaired frame condition are incorrectly used as sufficient FLRW/EGS premises. Explicit repository counterexamples defeat the converse. |
| `D-THEORY-COEFFICIENT-REGRESSIONS` | P1 | NT-A3 stale language reappears; NT2 uses the reciprocal coefficient; OMK linearity is promoted as global exactness; truncation convergence is called sufficiency. |
| `D-THEORY-PROVENANCE-OWNERSHIP` | P1 | Global quadratic and local linear `Omega_tilt` meanings are overloaded; D2 has no nonzero current Rust authority receipt; TEFF is active despite the legacy-only contract. |

The anisotropy advocate conceded that current CF4/CMB/survey products provide no
positive global-tilt, geometry, or family evidence and abandoned the classical
coupled VII_h explanation. The isotropy advocate conceded that current nulls do
not prove exact isotropy. The surviving position is deliberately asymmetric:
weak anisotropy remains a falsifiable research programme, not a result.

**Axis score:** as shipped `2/5`; post-surgery methods content `3/5` if every
converse, coefficient, authority and ownership defect is repaired.

## Statistics axis

### Steelman

The repository has a promising separation between model-dependent HTT
inference and model-family-independent MIO diagnostics, plus useful identified-
set and rank witnesses. Finite-mock rank corrections, explicit null status, and
blocked inputs are better than silent proxy substitution. A future normalized
generative model could support Bayesian evidence and posterior predictive work.

### Hostile result

| Canonical delta | Level | Ruling |
| --- | --- | --- |
| `D-STAT-BAYES-SEMANTICS` | P1 | The shared-cause “Bayes factor” is a fitted likelihood difference and changes from shipped `+29.7` to HEAD `-1035.461`; the null statistic degenerates near `-3893..-3899`; residual/ablation scaffolds are mislabeled PPC/LOOCV; readiness is unauthenticated. |
| `D-STAT-K1-EXCHANGEABILITY` | P1 | The asymmetric two-stage max-scan is anti-conservative: nominal 5% size is `5.790%` in 100000 null trials. Current conclusions remain non-anomalous after correction. |
| `D-STAT-PARTIAL-ID-MEASURE` | P2 | Coverage is not proved for stacked projection+IM intervals; positional pairing changes MIO F by about 4.9x; an old registry overstates unconditional identification. |

The Bayesian side conceded withdrawal of evidence, PPC, LOOCV and Jeffreys-scale
language. The frequentist side conceded that Gaussian/Wishart witnesses and
identified-set mechanics are legitimate under their stated assumptions. The
partial-identification novelty remains unranked until PR-118's permitted final
CRAG; current empirical applications do not change a scientific conclusion.

**Axis score:** as shipped `1/5` for inferential claims, `3/5` for formal
scaffolding; post-surgery methods object `3/5` only after real priors,
likelihoods, predictive draws, held-out scoring, matched nulls and coverage.

## Code/reproducibility axis

### Steelman

Ownership, claim-tier and transfer-provenance contracts are real and useful.
The focused HTT/MIO/OBSSTAT/BASS regression passed 94 tests; smoke passed 6;
collection reached `7872/7931` with 59 deselected after the seven new audit
tests. The package builder is deterministic and path-safe. Generator `--check`
modes correctly fail rather than silently rewriting stale products.

### Hostile result

| Canonical delta | Level | Ruling |
| --- | --- | --- |
| `D-CODE-CLEAN-IMPORT` | P1 | Two distributions claim the `htt` namespace; clean-CWD BASS import fails while packaging tests pass. |
| `D-CODE-FALSE-GREEN` | P1 | Freeze/package pass assertions do not compose canonical manifest validity, generator freshness or actually executed tests; contradictory green/red surfaces reach external handoff. |
| `D-AUDIT-HARNESS-SELF-REVIEW` | P2, repaired | The first negative leak test was whitespace-sensitive and early commands used changing runner bytes. Parsed JSON/YAML plus rendered-equivalent Markdown/TeX fixtures, atomic ID claims, exact evidence anchors, environment/data rehashing, and numeric-output binding now pass; all seven lanes share runner hash `614630a4...c3fa0c`, while ACT remains `BLOCKED_SCIENTIFIC`. |

These defects usually block reproducibility/readiness rather than invalidate a
mathematical derivation. Conversely, deterministic reproduction of a stale or
invalid artifact does not validate it. No quantity of schema/smoke tests is an
independent scientific oracle for estimator bias, coverage, transfer, or masks.

**Axis score:** as shipped `2/5`; post-surgery framework `4/5` only after a
single fail-closed release aggregator, clean-install import, quarantine-aware
packaging, and lane-specific independent science oracles.

## Data-analysis axis

### Steelman

The repaired DESI local-GRF exercise is a legitimate non-anomalous sensitivity;
the constrained CF4 projection is a useful nuisance diagnostic; same-release ACT
alms can support a release-simulation percentile; the JWST computation can be a
transparent scenario forecast. These negative/conditional outputs are useful
when their ceilings are explicit.

### Hostile result

| Canonical delta | Level | Ruling |
| --- | --- | --- |
| `D-DATA-CF4-PROPAGATION` | P1 | The imported CF4 P0 propagates to theory and `f sigma_8`; the 94 km/s projection is not truth; estimator-mismatched external corroboration and missing response rank block global tilt. |
| `D-DATA-ACT-VALIDATION` | P1 | Raw QE inputs and validated low-L transfer are absent; sky-power upper limit is blocked. |
| `D-DATA-CMB-SUPPORT` | P2 | Planck mask is recorded but not applied, real K1 bypasses the canonical convention, and a stale axis/p-value lacks joint covariance. |
| `D-DATA-DESI-SUPPORT` | P2 | Corrected local null stays conditional; exact-selection mocks and consistent promotion status are missing. |
| `D-DATA-JWST-PROVENANCE` | P1 | Acquisition, per-host weighting, covariance and crossmatch sensitivity prevent an observed-data gain claim. |

The data analysts and numerical engineer agreed that every surviving positive-
sounding number is either an on-model mechanics result, a conditional
consistency check, or a blocked interpretation. No correction creates an
anomaly. No current data lane changes cosmological practice.

**Axis score:** as shipped `1/5` for headline interpretation, `2/5` for the
conditional diagnostic suite; post-surgery applications `3/5` as transparent
methods examples, not competitive measurements.

## Archaeology and coverage

At commit `32a44e9`, the 31 contemporaneously counted broken/corrected/partial/
TODO records were recovered and classified as `historical_only 11 / resolved 10
/ still_open 9 / unmappable 1`. At `79483ed`, two deleted low-ell designs were
sampled against the current handoff. Seven priority legacy archives were safely
inventoried; no path traversal, encrypted member, symlink, or executable-suffix
entry was found. `bianchi_origin.zip` nested archives were recursively checked.
The session archive remains uncommitted; one email pattern in a defect archive
is recorded rather than copied.

Family-atlas, type-discrimination, shear-inference and Mori-Zwanzig ideas remain
interface hypotheses. Deleted toy Sachs-Wolfe and duplicate PSTF code must not be
revived. The 78-row generated table, current artifacts, Git history and legacy
archives have explicit `examined / sampled / blocked / not_examined` coverage in
`coverage_matrix.json`; absence of a finding never means clearance.

## Editor-facing disposition

| Object | Decision | Reason |
| --- | --- | --- |
| Current as-shipped corpus | **REJECT** | Imported P0s remain, 22 new atomic P1 deltas reach manuscript/inference/data/release consumers, and the positive headline layer is not calibrated or reproducible. |
| Minimal prose-only revision | **REJECT** | Most defects require estimator, likelihood, coverage, transfer, packaging or theorem reconstruction, not wording. |
| Major-surgery pre-solver methods paper | **REVISE AND RESUBMIT** | Potentially defensible if restricted to formal identifiability/diagnostic machinery and honest conditional negative examples, after all P0/P1 consumers are rebuilt or removed. |
| Positive anisotropy/global-tilt result | **ABANDON AT PRESENT** | Current data and statistics do not identify it. |
| Geometry/family claim | **NATIVE-SOLVER-DEPENDENT** | Requires native morphology atlas, family-equivalence, matched masks/nulls/covariance and external validation. |

One dissent remains: a charitable software referee may call the contradictory
green gates harmless because the package prose says “not publication ready.”
This audit rejects that defense for external handoff. A machine gate named
`pass` must enforce and state its domain; otherwise it accumulates authority it
does not possess.
