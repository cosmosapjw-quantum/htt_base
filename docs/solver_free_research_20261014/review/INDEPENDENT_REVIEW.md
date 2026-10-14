# Independent review of the solver-free research candidate

**Verdict: PASS_SCOPED_CONDITIONAL_DELIVERY. No open findings within the reviewed scope.** This permits the parent to deliver the bounded methods/diagnostic package. It is not full scientific admission, a physical detection claim, exhaustive novelty clearance, or READY_TO_SUBMIT. Historical HOLD/UNKNOWN states remain unchanged.

Reviewer: `solver_free_review_r2`, fresh read-only context, no production authorship and no spawned agents. Requested runtime: `gpt-6-astra/xhigh`; observed model/effort: `UNKNOWN`. Review date: 2026-10-14. Primary checkout: `/home/cosmosapjw/Dropbox/bianchi/htt_base`, branch `obs/solver-free-dossier-20261014`, starting HEAD `89621f4c9a6f63449813587a0fadeb13287f8e10`. This was one coherent independent pass followed by targeted repairs, not repeated assurance campaigns.

## Scope and evidence read

Reviewed the four new scientific scripts, their tests, compact publication summary script, task-packet reader, mathematical derivation, Gaia/Union explanations, integrated CF4 report/results/provenance, scientific report, publication/future lists, continuation plan/DAG/context/handoff, final claim ledger and figure manifest. Inspected the relevant existing CF4 law/generator interfaces and Union fitter, including analytic offset marginalization and fixed quadrature. Checked dossier VI current-flux, observer normalization, matched-detector, finite-bin and fold passages and VII finite-remainder/boundary/detector bounds. Four consulted source chapters are now preserved under `sources/dossier/`, with exact hashes matching the declared archive members.

Final identities for 33 reviewed files are in `REVIEW_SCOPE.json` and `FINAL_CANDIDATE_IDENTITY.json`. Reviewed patch bytes match the primary checkout. The final Gaia envelope differs from its preceding primary version only in generating-command metadata; its replay receipt records exact parity of all other fields. Original CF4 execution code, campaign bytes and mapped integration provenance remain available.

## Physics, mathematics and statistical audit

| Component | Assessment | Assumptions and limits |
|---|---|---|
| Selected-observable response | Correct quotient-rule derivative, including kernel response and the normalizer term | Common fixed labels, differentiated-product majorants, positive selected mass; observed-coordinate statistics require the full joint kernel |
| Gaussian measurement bin | First/second derivatives, signs and sigma powers correct; displayed uniform bounds valid | Fixed positive sigma, or a positive lower bound; sharp zero-noise limits need another boundary law |
| Finite discrepancy bound | Accepted-weight L1 decomposition and ratio bound correct | A positive mass margin is essential; no empirical completeness estimate is inferred |
| Shared calibration selection | PRE and selected-slot integrals represent different normalized experiments | They agree only when the selected eta prior is transformed consistently; fixed independent slots do not model unknown counts/overlap |
| Robust nuisance contrast | Singular-value triangle inequality and inverse Loewner bound correct | Parameter units/scales fixed; nuisance-space leakage separately bounded; rectangular underdetermined matrices have zero parameter-space minimum singular value |
| CLASS interval ranks | Sharp under the independent nonnegative score-interval box, including `>=` ties | Frozen training transform and assumed error budgets; no exchangeability repair or physical CLASS p-value |
| Tail probability and TV arithmetic | Clopper–Pearson/TV statements correctly scoped | IID null scores conditional on training and observed threshold; not a confidence interval for the realized rank |
| Gaia geometry | Disk support/witness, matched tangent rotations, exact ellipsoid image and Minkowski sum correct | Disk and same-number coordinate box are different sets; total whitened budget is distinct from a per-source budget |
| Gaia confidence interpretation | Radius q+rho gives at least 95% coverage for all admissible fixed biases under the stated Gaussian law | Exact at zero budget, generally conservative otherwise; outcome selection and actual cross-source covariance remain unresolved |
| Union prior sensitivity | Centered Gaussian division, information-vector identity and additive constant correct | The assumed prior and reference are scenarios; exact FITS-to-generator/prior binding is unresolved |
| CF4 cross-law experiment | Correct eta semantics, paired fits and descriptive summary arithmetic | Real fixed design with generated observations; 16 catalogues per law do not establish universal performance or survey coverage |

The dossier uses signature −+++ and observer-normalized affine length. The added finite calculations do not identify a passive frame change with physical species tilt. A current-flux/finite-bin formula provides a lawful observation construction only when its actual population, detector and physical response inputs are supplied. No inverse redshift slope appears in the new fold calculation. Zero selected mass is rejected. Failure of the robust-rank lower bound is not a global no-go.

Gaia raw tangent and coefficient units are mas/year, with displayed values converted to microas/year; K acts on a dimensionless whitened vector and V has squared units. The simultaneous ellipsoid and its coordinate projections are not interchangeable with a marginal 1.96-sigma rectangle. The claim of a sharp enclosing Minkowski radius does not assert the smallest possible uniformly valid confidence region.

Union uses proper parameter priors and the same analytic M marginal once per scenario. The fixed 96-point radial quadrature is not ODE integration. The primary paper's sections II/V describe prior division; the supplied pinned Stan text has an empty prior branch for cosmo_model 2/6. This source conflict supports the retained sensitivity study, not selecting either removal or no-removal as certified truth. The paper was independently opened at `https://arxiv.org/html/2412.14181v1`; direct GitHub web retrieval failed, so the pinned code inspection is explicitly based on the supplied source text.

## Numerical and artifact checks

- Reviewer directly ran the initial three-lane unittest suite in the primary checkout: **17 passed**, 0.048 s. Tests include derivative finite differences, constant-statistic normalization, tie/attainment cases, rectangular rank, disk witnesses and rotation invariance, minimum-norm ellipsoid preimages, covariance/input rejection, independent logpdf identities and a known-law stress check.
- Directly inspected the final integrated pytest log and execution receipt: **23 passed in 5.72 s** (6.359 s command wall time). The added six CF4 tests exercise unchanged PRE generation, selected eta semantics, grid moments, descendant/source guards and fresh-output rejection.
- Independently recomputed CF4 bias, RMSE, paired mean and MCSE from all 32 retained rows: exact numerical agreement. All 64 fits were successful and accepted. All generated NPZ hashes and selected-modulus support checks passed. Maximum recorded quadrature difference was **1.817835482e−8**, below the unchanged 1e−6 criterion.
- Read the bounded CF4 post-guard smoke and execution provenance. The large campaign was not rerun to validate packaging changes. Numerical function bodies are unchanged between the retained execution copy and installed replay script.
- Inspected the Gaia command-metadata replay, canonical DAG validation (**245 PRs**), synchronized mirrors and task-packet validation (**15 tasks**); all reported exit code 0.
- Cross-checked all **12 figure-manifest entries** against actual figure bytes, source-result bytes and installed replay-script bytes: no mismatch. Selection/fold, rank-budget, Gaia operator/directional, Union marginal and CF4 paired plots are legible. The Union preview inspected matches the primary PNG exactly. Figures consistently distinguish hypothetical budgets, conditional laws and actual observations.
- Verified the four integrated dossier chapter hashes and the updated source map. No archive code was executed. No native Bianchi solver construction or ODE integration is present in the reviewed changes.

The final four result identities are:

| Result | SHA256 |
|---|---|
| observation_bounds/result.json | `acfbbab4267b9318cbdc4c80787bd8ec63d56dcbf119565288e61076fcdf6079` |
| gaia_geometry/result.json | `ee9880560aa1d811da8b7310a56427c745b4e25356227e7efa3673d4537008d0` |
| union_prior/result.json | `7aae24dd3b7b2c2d8031a542167b1b40b22e20000e119c05352c1361d814318b` |
| cf4_crosslaw/result.json | `1270c3137753885763db288083ee7e3accb784c8336221ac67f4e504a1cbbaed` |

## Findings and targeted closeout

| Finding | Final status | Repair verified |
|---|---|---|
| RV01: Gaia stale generating/reproduction paths | CLOSED | Actual interpreter, resolved installed script and options recorded; integrated docs/replay metadata corrected |
| RV02: CF4 exact-HEAD guard prevented committed replay | CLOSED | Starting-checkpoint ancestry plus actual imported scientific source hashes; descendant and rejection cases tested |
| RV03: CF4 seed-only resume could relabel stale rows | CLOSED | Fresh-output requirement and collision rejection; original executed source/campaign preserved separately |
| RV04: stale publication state and conflicting future IDs | CLOSED | Completed analyses incorporated; source ambiguity retained; F01–F09 aligned across lists |
| RV05: Union disposable reproduction paths/HEAD wording | CLOSED | Installed commands and ancestry/pinned-fitter/input wording |
| RV06: worker-vs-primary Gaia residual/runtime prose | CLOSED | Primary values identified accurately; no numerical re-interpretation |

The integrated CF4 tests also define the repository root during module import and use the installed script name, so normal discovery works. The final publication inventory distinguishes four existing methods, eleven result entries and nine future directions without promoting standard algebra into novel theorem priority.

## Claim audit, remaining risks and handoff

HTT owns the conditional inference/geometry outputs. None is presented as an MIO posterior, native-transfer result, Bianchi family identification, physical MES/Jacobi bound, or global-history measurement. The four-lane claim ledger retains the correct source/law restrictions. The new results improve concrete methods and reproducibility evidence; submission readiness and literature novelty remain unresolved.

Actual survey selection/completeness, shared calibration/overlap/source motion, Gaia cross-source covariance and outcome selection, physical error budgets, the Union release-generator binding, and distinct global-history responses remain substantive inputs. Small conditional generated samples and synthetic known-law stress do not replace empirical coverage. This review is not a raw-data or full-repository audit, exhaustive literature search, or independent execution of every historical analysis.

No new scientific gate or additional experiment is required to close this candidate. The parent may complete SF06, update canonical/remote publication statuses and refs, run `--ready`, and push the authorized delivery. Those mechanical closing updates do not require revalidating unchanged science. The handoff should then expose SF07/SF08/SF09; it explicitly installs no unattended scheduler. Changes to scientific code/results or broader physical claims require review of that changed scope.
