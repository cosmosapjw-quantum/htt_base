# Independent review — open inputs and finite anchor theory

**Verdict: PASS_SCOPED_AFTER_TARGETED_REPAIR.** No unresolved blocking finding remains in the candidate identified below. This verdict covers the acquisition tooling, evidence and input checks, CI fragment synchronization, finite anchor mathematics, and continuation packet. It does not certify a joint observational likelihood, manuscript readiness, or a physical shear/tilt result.

Review date: 2026-10-18. Reviewer: independent agent `/root/open_frontier_independent_review`; requested model/effort `gpt-6-astra/xhigh`, observed runtime identity **UNKNOWN**. The reviewer did not author candidate changes, publish, or delegate. Repairs were made by the authoring team and checked by this same reviewer. This is one review with targeted repair closeout.

## Candidate and governing context

- Intake: PR #560, commit `4a68995507bf8e672b2551d9030f3ad9f0d2152e`.
- Selected candidate: `patches/`, **47 files, 722,511 bytes**.
- Manifest: `CANDIDATE.json`; SHA256 of its canonical JSON serialization (`sort_keys=True`, separators `(',', ':')`): `843ce7a58632e97d6df41e982a9a5da27388b692bc4cc3cca9d858e82bcb38b8`.
- Independently checked every manifest entry's file length and SHA256 against the final candidate. This report is outside that manifest.
- Read the pinned authoritative `source/AGENTS.md`, continuation `RESUME_NATIVE_20261018.md`, and the applicable `c40/physmath-research-loop` R6 independent-review instructions and policy/theory/subagent references. The source directory is a selected-file fixture, not a complete checkout.

The final documentation retains **17/42** original tasks complete, **8** external blocks, **0** ready tasks, and all six paper states **NOT_READY**. Public access is consistently distinguished from the qualification of a joint sampling law. No original DAG change or ODE/solver work is included.

## Findings and targeted closeout

### 1. Calibration transport in the anchor bridge — substantive, closed

The initial raw optical-minus-geometric distance equation omitted the H02 method-specific calibration contribution. This could produce a false positive even with exact distances: take `s_x = 0.010`, `eta_x = 0.015`, `gamma_m,x = -0.015`, and an allowed calibration bound `delta = 0.020`. The raw anchor sees `eta_x + gamma_m,x = 0`, while the physical component is `theta_x = s_x - eta_x = -0.005`. Treating that anchor as `eta_x = 0` would incorrectly certify a positive component.

The final report now gives the raw equation `r_raw = A p + G gamma + e`, requires actual contributor labels or mixture weights, and shares the same calibration variable with H02 in the joint feasible set. The known-relative-calibration calculation is explicitly an ideal corrected scenario. For uncertain corrections it includes the valid outer bound

`|l^T p - l^T A^+ r_corr| <= R ||w|| + sum_j delta_j |(G^T w)_j|`, with `w = (A^+)^T l`.

The report and figure no longer present the ideal precision target as sufficient under the unresolved calibration uncertainty. The single-method calibration floor is **0.020 mag**, larger than the approximately **0.009956 mag** H02 target. I independently checked the bound against a direct inverse calculation and 100 feasible two-method examples, in addition to the repaired tests. Closed.

### 2. Minimum number of directions — mathematical scope, closed

An unconditional nine-row minimum would be wrong for identification of the dipole alone: three antipodal axis pairs have six rows, full-design rank six, even-nuisance rank three, and dipole quotient rank three. The final text restricts the nine-row minimum to identification of all nine coefficients, or augmentation of these particular six existing directions whose nuisance block already has rank six. An explicit antipodal regression test was added; I also constructed the counterexample independently. Closed.

### 3. Source adapters, CI provenance, and evidence packaging — closed

- The HI analyzer now accepts the standard manifest names `ReadMe`, `table2.dat`, and `table4.dat`, with legacy probe-name fallback and frozen source-hash checks. A rerun using standard names reproduces all outcome sets and telescope sets. Plot counts are computed from the result.
- The stale `AGENTS.md.fragment` is synchronized to policy already present in authoritative `AGENTS.md`; authoritative AGENTS is unchanged. The original fragment was restored in the selected baseline fixture before comparison. I extracted and ran the complete unchanged `test_shared_context_packet_is_merged_and_versioned` against a disposable fixture: the baseline failed, and replacing only the fragment passed. No acceptance condition was weakened.
- The compact CMB HTTP receipt and distance access receipts are present. Full locally retained web pages are not represented as distributed artifacts. The A3 claim now links to the exact prior P2 report and JSON; the fetched current-head report supports its stated angular and residual numbers. Closed.

## Verification and independent falsifiers

### Acquisition and filesystem behavior

The final acquisition suite passed **14/14**. The tool defaults to a plan and requires explicit `--fetch`; it restricts HTTPS hosts, rejects URL credentials, checks redirects, bounds compressed and expanded data, and verifies the required transport/source properties. It neither executes nor extracts downloaded code. Existing unknown or mismatching destination files are preserved; failed transfers retain a `.part` without claiming resumability.

Additional reviewer checks rejected HTTP **206, 401, and 403** without creating a final file, confirmed the request carried no Cookie/Authorization/Proxy-Authorization header, rejected a receipt symlink, and simulated a concurrent destination creation immediately before the create-only link operation. The competing bytes were preserved and the partial transfer remained. These checks passed. The manifest contains **17** entries, with **9** default automatic entries bounded in aggregate to **127,000,000 bytes**. The four full split-noise files are not promoted from header probes to validated downloaded payloads.

### Actual HI cohort

Independent parsing from the fixed-byte ReadMe schema and source tables reproduced:

| Quantity | Count |
|---|---:|
| Actual GBT target cohort | 628 |
| Accepted, error at most 20 | 385 |
| Non-detections, error 500 | 192 |
| Confused, error 100 | 29 |
| Other, error between 20 and 100 | 22 |
| Table 4 rows | 1,274 |
| Table 4 Nançay / GBT rows | 889 / 385 |

The accepted PGC set equals the table-4 GBT PGC set exactly. The report confines these fractions to the actual 628-target cohort and does not infer a global CF4 selection probability. The primary article supports the error-code interpretation and 385 accepted targets; the inconsistent CDS prose number is not used as the computed result. The figure is readable and matches these counts.

### Pantheon+ full covariance input check

Independent calculations on the actual full table and covariance reproduced **1,701 rows**, **1,543 distinct CID strings**, **285 rows with repeated CIDs**, **77 calibrator rows**, **43 calibrator CIDs**, and **2,893,401 covariance entries**. Both raw file hashes and byte lengths matched.

The raw covariance's maximum asymmetry is `3.0000000000038676e-08 mag²`; the strict `1e-10` symmetry check correctly remains failed. For the explicitly diagnostic symmetric part, I obtained minimum eigenvalue `0.0008027816532258978` and minimum Cholesky diagonal `0.06046040535001106`. There are **191** same-CID pairs; their correlation minimum/median/maximum are approximately `-0.00500423 / 0.40777515 / 0.91549265`. The candidate does not promote symmetrization to an adopted likelihood covariance or repeated rows to independent observations.

### Public CMB evidence

The actual weights archive hash/length and its eight-member inventory matched. E/B weights have shape **14 × 4001**, matching the supplied propagation code's **2 × 7 × 4001** interpretation. T weights have full/high-frequency shapes **9 × 4001** and **6 × 4001**. Beam/LFI normalization and the stated high-pass treatment are source-bound.

The inspected split FITS headers identify RING, NSIDE 2048, three I/Q/U `1024E` columns in K_CMB, and a table-data size of **603,979,776 bytes**. These are header facts, not verification of the complete split realizations. The linear covariance propagation is correct under its declared fixed-operator and independence assumptions. The Planck release limitation is stated with release scope, not as a universal absence claim or a strong no-go theorem.

### Finite anchor mathematics and geometry

The final theory suite passed **12/12**. I checked the nuisance-quotient/row-space identifiability argument, the nullspace-unbounded case, empty residual balls, the sharp residual-ball interval, the augmentation determinant identity, the explicit STF normalization, and the stated coordinate-perturbation bound.

Independent numerical checks, separate from the producer's nullspace shortcut, gave:

- Existing six anchors: design rank **6**, nuisance rank **6**, dipole quotient rank **0**; nuisance smallest singular value `0.09349940591871214`; nullspace witness residual at most `1.5265566588595902e-16`.
- Full nine-by-nine determinant enumeration over **41,664** candidate triples: winner **(37, 39, 56)**, augmented rank **9**, smallest singular value `0.09633574406725137`.
- Directional gains approximately **2.88787940, 4.00768472, 5.61942657**; ideal L2 residual target `0.0034475837532184322 mag`; ideal uniform-error target `0.0017589713026624654 mag`.

The source H02 directions are equatorial/J2000, as shown by the preserved RAdeg/DEdeg construction check; the maser positions use the same frame. Primary-source distances and positions were checked. Distance duality uses the observed redshift with its stated conditions. The Wolfram receipt retains its failed protected-symbol attempt and successful renamed exact representative check; it does not claim an exact proof for rounded observed coordinates. The three prospective directions remain design points, not observed galaxies. No optical/geometric residual fit or physical identification has been performed.

### Continuation packet and claim consistency

The new read-only packet reads the live DAG and validates original task IDs, acceptance contracts, and dependencies against its plan. All **42** original IDs, paper labels, dependency lists, acceptance conditions, and objectives agree with the pinned original DAG. It reports **17/42**, **8 external**, **0 ready**, and D01/D08 entry points. S06 traces to D02/D03/D07 acquisition routes. A copied H02 acceptance mutation is rejected, while removing a copied external block changes readiness dynamically. No status file is written.

The final handoff, verification, observational-data, publication-candidate, and development-DAG documents preserve the distinction between completed checks and missing scientific inputs. The reused A3 range **55.6426–73.7213 degrees** and residual bound **at least 82.5533%** agree with the linked prior P2 report; this review did not rerun that campaign.

## Limits and disposition

The executed focused suites comprise **26 tests (14 acquisition + 12 theory)**, plus the complete original CI-fragment test and the independent checks described above. Earlier versions of the theory suite are not counted again. The reviewer used Python 3.12.14 and NumPy 2.3.5 in the available runtime, did not install dependencies, and did not claim a repository-wide test run or use of the repository `.venv`.

No full scientific raw-data campaign, new joint-law qualification, complete split-noise download, ODE/solver validation, or manuscript-readiness assessment was performed. The final scope is internally consistent and adequately evidenced for this bounded open-input/theory increment. Publication remains the parent's responsibility.

Primary-source cross-checks included [Pesce et al.](https://arxiv.org/pdf/2001.09213), [Villaraos et al.](https://arxiv.org/pdf/2207.06594), the [HI cohort article](https://www.aanda.org/articles/aa/full_html/2021/02/aa39025-20/aa39025-20.html), [Planck 2018 VIII](https://www.aanda.org/articles/aa/full_html/2020/09/aa33886-18/aa33886-18.html), and the [NGC 4258 coordinate source](https://science.nasa.gov/asset/hubble/ngc-4258/), alongside the pinned local source evidence.
