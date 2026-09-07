# HTT repository-wide theory-surface audit

**Date:** 2026-09-03  
**Repository:** `cosmosapjw-quantum/htt_base`  
**Purpose:** revise the HTT-only theory-report programme after a repository-wide authority, code, document, and execution-receipt audit.  
**Observational state:** `DATA_DEFERRED_BY_OWNER`.  
**Excluded scope:** native BASS solver construction, Bianchi background evolution, recombination/reionization, native family-level transfer or likelihood claims.

## 1. Audit method and completeness boundary

The repository has no single branch that contains every current scientific authority. The default branch `research/pr04-multicomponent` is at `50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb`, while the current tensor correction, theorem-reconciliation, local-observer response, processed-response, external-verifier, and report lineages live in later open draft pull requests. Consequently, “latest repository state” must be reconstructed as a set of exact branch authorities rather than inferred from the default HEAD.

This audit used two levels of coverage.

1. **Repository-surface inventory.** The default tree and changed-file manifests for the report-relevant PR lineages were enumerated at path/metadata level. Code, documents, generated evidence, workflows, tests, and execution records were assigned an owner and a report role.
2. **Load-bearing semantic audit.** Every code/document/log surface that can directly support or invalidate Report A was read in detail: the vector/tensor foundation, tensorized MES correction, theorem reconciliation, theory-promotion audit, adversarial survivor audit, WU-010, WU-011, external verifier contracts, current report files, and their workflow receipts.

Unrelated solver, download, legacy reproduction, and observational pipelines were classified by path and scope but not line-by-line re-audited. This is deliberate: they are outside the report claim surface, and importing them would violate the HTT-only/BASS-excluded boundary.

## 2. Repository authority is a federation, not a linear HEAD

### 2.1 Default branch

```yaml
branch: research/pr04-multicomponent
head: 50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb
tree: 42ef66d9746f4c9049fcfdf723ed10eb1301914e
last_merge_date: 2026-08-20
role: MERGED_FRAMEWORK_BASE_NOT_CURRENT_REPORT_AUTHORITY
```

The default branch is useful for merged common contracts and historical code, but it predates PR #440, PR #441, WU-010/WU-011, and this report branch.

### 2.2 Report-relevant authority lineages

| Lineage | Exact head | Present role | Admission state |
|---|---|---|---|
| PR #367 vector/tensor foundation | `6bafca66285ef071081453313bb7d2d6b261599c` | typed state, tensor functional, orbit, statistical and synthetic-validation infrastructure | merged framework; no admitted observation; broad source obligations not all adjudicated |
| PR #405 theory-promotion audit | `463f0999949bf8534c60ad7973b7342705c2e3d6` | candidate-universe and provisional scoped dispositions | `STOP_INVALID_FOR_CURRENT_PROMOTION`; discovery/audit source only |
| PR #408 survivor-closeout audit | `40dce3ab9328c1f3acb99adba11046056c639737` | P0/P1 audit and work-unit compiler | planning evidence; survivor selection not mechanically closed |
| PR #440 tensorized MES correction | `687234128d7c12d04e68aad0f303c21d2d470393` | current scalar-retirement, stored-real/STF, MES-normalization, and Q/O-repair semantics | source implementation present; science admission and supported-runtime replay pending |
| PR #441 WU-009 theorem reconciliation | `04680e99d56b9974fe1120854370af1fb94fb1d6` | 78-row theorem wording/counterexample inventory | `USER_SUPPLIED_SUMMARY / FORMAL_DOSSIER_PENDING`; not proof authority |
| PR #442 WU-010 | `29427a1f7f2c5d46e43ffe03053c4ac13e969228` | exact full-sky thermodynamic local-observer response | scoped implementation/theory authority with exact-head successful CI |
| PR #444 WU-011 | `de73549c16ac6ceb63f924c86611e0a5ceb4711d` | processed cut-sky response and Task-7C numerical uncertainty engineering | last byte-exact scientific terminal is `PASS_TASK7C_MATCHED_CONTROL_RANK_UNRESOLVED`; later A4 source is not exact-head CI verified |
| PR #446 verifier axis | `033e0d19d61448492489ed1469bc687b2ecb4552` | Wigner/SymPy/Arb/DUCC verifier contracts and exact z-axis artifact | source/artifact authority only; workflow never started |
| PR #447 verifier axis | `bf6cc2dd75336ec5584b86dccd8de5cb352ab8f3` | JAS/Octave/Julia independent verifier implementations | source authority only; workflow never started |
| PR #449 report line | updated by this audit | HTT-only report, inventories and revised DAG | draft; no release or merge authority |

The tensorized-method lineage and WU-009–011 response lineage are Git-diverged. Report integration is therefore semantic and evidence-indexed. No document may imply that one branch is a linear descendant of the other.

## 3. Code-surface findings

### 3.1 Merged vector/tensor foundation

The merged foundation supplies useful typed infrastructure:

- `joint_anisotropy_state_v1.py` separates congruence kinematics, inter-frame velocities, and geometry; missing components are typed and a legacy scalar `beta` is not silently assigned a physical frame role.
- `tensor_functionals.py` separates value, domain, codomain/O(3) type, anchor status, admissibility, and stress; outputs are diagnostic-only.
- `orbit_catalogue_v3.py` records O(3)/SO(3), parity, stabilizers, and local chart conditioning, while explicitly leaving generic orbit separation and global chart completeness `UNPROVEN`.
- `conditional_exceedance.py` separates matched-null laws, profile objectives, and posterior laws; optimizer points cannot be relabelled as draws.
- `statistical_foundations.py` separates signed budget coordinates, anchor stress, and identified sets; MES anchors remain one-way conditional bounds.

These modules are reportable as **typed framework architecture**, but not as proof that the temperature `STF2 ⊕ STF3` orbit problem has been globally solved.

### 3.2 Tensorized Q/O correction

PR #440 contains a focused seven-file additive bridge. Its scientific core is:

```text
stored-real harmonic input
→ independently projected STF Q/O tensors
→ correct radial C_l identities
→ original-PSTF MES conditional functions
→ conditioned generic SO(3) Krylov chart
→ typed chart failure with tensors/rows preserved
```

The source implementation and synthetic tests are concrete, but the PR head has no executed GitHub test receipt: all exact-head workflows ended before runner assignment. Therefore the report may state that the implementation exists and that its algebra is independently re-derived; it may not state that PR #440 has supported-runtime exact-head verification.

### 3.3 WU-010 local-observer response

WU-010 is the strongest closed implementation surface in the report. It has exact formulas, independent harmonic/STF checks, adversarial numerical tests, and successful exact-head PR04, PR07, and repository-integrity runs. It may be treated as scoped implementation-verified evidence, subject to its positive thermodynamic-temperature, full-sky, local-observer, `d=1` domain.

### 3.4 WU-011 processed response

WU-011 correctly factorizes the processed operator into source-sky construction, Lorentz pullback, transfer, HEALPix synthesis, the authoritative weighted joint fit, commonization, and retained scientific stored-real output. It content-binds masks, transfers, operators, and evaluations and prohibits empirical `beta`, global tilt, or Bianchi attribution.

The later Task-7C error-envelope source implements a matrix-valued deterministic perturbation class and a sufficient error-whitened row-rank condition. However, current-head workflows did not start, and the complete numerical error-family/radius provenance is not sealed. The finite-HEALPix containment conclusion remains unresolved.

## 4. Representation-family firewall

Two distinct orbit problems coexist in the repository and must not be conflated.

### 4.1 Temperature morphology target

```text
representation: STF2(Q) ⊕ STF3(O)
ambient dimension: 5 + 7 = 12
generic SO(3) quotient dimension: 12 - 3 = 9
```

This is the representation relevant to the corrected low-ell temperature report and the PR #440 Krylov16 construction.

### 4.2 Merged vector/tensor observatory target

The PR #367/PR #408 VT-T8 local-Jacobian result concerns a different registered slice, effectively one STF2 object plus four vectors:

```text
representation: STF2 ⊕ V1 ⊕ V1 ⊕ V1 ⊕ V1
ambient dimension: 5 + 4*3 = 17
generic SO(3) quotient dimension: 17 - 3 = 14
```

Its fourteen-coordinate local Jacobian is not a proof of the nine-dimensional `Q/O` quotient chart. It remains useful as a separate typed-state/local-geometry result. The report must retain distinct theorem IDs, dimensions, source paths, and evidence grades for these two representation families.

Fresh exact algebra confirmed both dimension counts, the trace-free 3-by-3 Cayley–Hamilton identity used in Krylov reconstruction, `det(K^T K)=det(K)^2`, the processed-response quotient-rank identity on a finite example, and compensated error-family scaling invariance.

## 5. Document and claim-ledger findings

### 5.1 PR #367 proof atlas

The generated PR #367 report correctly says that 123 source rows and 28 two-pillar obligations remain `NOT_ADJUDICATED`; evidence-layer results do not mutate those source rows. This historical layer must not be summarized as a completed theorem programme.

### 5.2 PR #405 provisional promotion audit

PR #405 inventories 157 candidates and proposes 36 scoped promotions, but explicitly retains `STOP_INVALID_FOR_CURRENT_PROMOTION`. Its row counts are evidence dispositions, not unique theorem counts. It is a valuable discovery source, not the final claim ledger.

### 5.3 PR #408 adversarial audit

PR #408 finds that the survivor selection was manually narrowed before a mechanical triage of all eligible exact/conditional and synthetic rows. Its P0 correction is load-bearing for Report A: every eligible row must receive `INCLUDE`, `EXCLUDE`, or `DEFER`, with a source identity and without using provisional role labels to decide truth.

### 5.4 WU-009 theorem ledger

The 78-row WU-009 ledger is a typed wording/counterexample inventory derived from a user-supplied summary. Its own metadata states `FORMAL_DOSSIER_PENDING`. Rows may seed proof obligations, but their `PROVED` labels cannot be copied into Report A as independent proof evidence without direct derivation or another accepted source.

### 5.5 Existing Report A synthesis

The current synthesis has the correct high-level thesis and correctly excludes current observational ranks. It nevertheless needs three authority corrections before it can become a manuscript source:

1. distinguish the `Q/O` orbit theorem from PR #367’s different vector/tensor orbit programme;
2. grade continuum all-direction evidence by execution lineage rather than summarize all verifier axes as equivalently executed;
3. replace the previous “authority freeze complete” assumption with repository-wide survivor triage and an execution-receipt index.

## 6. Execution and log findings

Workflow conclusions alone are misleading in this repository. The report must classify execution at job-step level.

- PR #442 WU-010: exact-head PR04, PR07, and repository-integrity workflows completed successfully. This is `EXECUTED_SUCCESS`.
- PR #440: PR04, PR07, and repository-integrity jobs failed with empty step lists. This is `PRESTART_NO_EXECUTION`, not a failed theorem or test.
- PR #444 current head: all nine relevant workflows failed before runner assignment. This is `PRESTART_NO_EXECUTION`. The earlier frozen `f635d873...` artifact remains the last byte-exact Task-7C scientific execution.
- PR #446 and #447: external-verifier workflows have empty step lists. Their scripts and generated source artifacts exist, but no GitHub-executed verifier result exists.
- PR #449 pre-audit head: repository-integrity jobs also ended with empty step lists.
- PR #367: targeted slice receipts exist, while its recorded full repository suite remained non-green. This is `MIXED_EXECUTED_EVIDENCE`, not a global green status.

A separate `EXECUTION_RECEIPT_INDEX.yaml` now makes these distinctions machine-readable.

## 7. External literature findings

The literature search supports the architecture but does not close the project-specific theorems.

- Orbit/invariant literature provides generic separating-set, orbit-space, and symmetry-class methods for tensor representations, but no retrieved source directly proves the precise PR #440 Krylov16 `STF2 ⊕ STF3` reconstruction contract. This remains an independent theory obligation.
- Exact permutation validity requires exchangeability/invariance of the full operation. Dependence or unmatched observation/simulation laws cannot be repaired by rank notation alone.
- CMB aberration literature supports exact full-sky boost operators and the necessity of explicit mask/beam/noise treatment. Matrix-valued transfer and singular-subspace perturbation literature supports WU-011’s response-matrix and error-envelope approach.

Primary papers must be read directly before final bibliography freeze. SciSpace discovery metadata is not itself proof evidence.

## 8. Revised scientific disposition

### Included now

- scalar-only MES methodology is retired for the forthcoming analysis;
- old WU-006–008 tensor/foreground/injection interpretations remain withdrawn;
- stored-real/STF and original-PSTF normalization corrections are valid theory targets;
- merged vector/tensor code supplies typed diagnostic/statistical architecture;
- WU-010 is scoped implementation-verified;
- processed-response quotient and nested-image identities are exact finite-dimensional results;
- the z-direction continuum `L=12` rank-32 artifact has an exact rational nonzero-minor witness;
- all-direction continuum rank-32 remains strong multi-lineage numerical evidence, not a formal all-direction interval theorem;
- finite-HEALPix robust containment remains unresolved;
- current corrected Planck tensorized result remains absent by design.

### Excluded or deferred

- all historical scalar ranks as current results;
- all withdrawn Q/O, foreground, and injection results;
- PR #367/408 fourteen-coordinate local chart as evidence for the Q/O nine-dimensional chart;
- PR #405 provisional promotions without survivor triage;
- PR #441 `PROVED` labels without direct proof reconstruction;
- external-verifier scripts as if their GitHub jobs had executed;
- any BASS/native-solver physics;
- every observation-bearing analysis while the data gate is closed.

## 9. Revised DAG consequence

The previous `T0 authority freeze → T1 claim ledger` entry was premature. It is replaced by:

```text
A0 repository-surface inventory
→ A1 authority precedence and supersession
→ A2 registered survivor triage
→ A3 representation-family firewall
→ A4 execution-receipt index
→ A5 contradiction/notation closure
→ T1 report claim ledger
```

A0, A1, A3, and the first A4 index are completed by this audit. A2 is the current active node. No theorem-pack or manuscript claim may be finalized until every eligible source row has an explicit disposition.

## 10. Current terminal

```text
REPO_SURFACE_INVENTORIED
/
AUTHORITY_FEDERATION_RECONSTRUCTED
/
REPRESENTATION_FAMILY_CONFLATION_BLOCKED
/
EXECUTION_RECEIPTS_RECLASSIFIED
/
REGISTERED_SURVIVOR_TRIAGE_ACTIVE
/
OBSERVATIONAL_DATA_DEFERRED
/
NO_MERGE_OR_CLAIM_PROMOTION
```
