# Generated Shared Context View

Context version: `aa860ee8fa76da4878ae08fc5d07598c21457fe665211698f642601f70f14c52`
Built at: `2026-08-02T17:39:42+00:00`

This compact view is generated from the machine context index. Live HEAD, DAG, status, and active-run context is computed by the hooks at use time. Reference-only files are read only when an assignment names them.

---

## Source: `.agent-harness/context/SYMBOLS.md`

SHA-256: `f601b0123a914a1f3f9977267ce6b3625cba9be76bd67dbe351bf1fad32c4a2e`

# Symbol and Interface Table

| Symbol / interface | Definition | Domain / type | Units / dimensions | Sign / branch convention | Source of truth |
|---|---|---|---|---|---|
| `EvidenceAxes` | Orthogonal process, evidence, and scientific status tuple | typed enum triple | dimensionless | no axis may promote another | `htt/src/common/evidence_graph.py` |
| `EvidenceGraph` | Typed acyclic content-addressed claim/evidence graph | immutable graph record | dimensionless | SHA-256 canonical JSON identity | `htt/src/common/evidence_graph.py` |
| `TestExecution` | Exact collected/executed/outcome/environment receipt | typed pytest evidence record | counts and SHA-256 refs | skipped/xfail are not passes | `htt/src/common/evidence_graph.py` |
| `ReleaseEvidencePin` | Typed view of literal-only fixed-point fields | repository-relative paths and SHA-256 refs | dimensionless | parsed without importing pin module | `htt/src/common/release_evidence_binding.py` |
| `AuthorityRegistry` | Exact principal/role/scope verifier registry | immutable principal records | dimensionless | correlated internal identities cannot promote science | `htt/src/common/remediation_state.py` |
| `MatchedNullCompetitionReport` | Canonical HTT matched-null adequacy report | exact typed report | report-defined | caller scalar or duck type is non-authoritative | `htt/htt/htt/infer/null_competition.py` |
| `MESAnchorSpec` | Typed MES anchor, normalization, domain, frame, and provenance authority | immutable contract | declared per component | anchor role and denominator policy are explicit | `htt/src/common/statistical_foundations.py` |
| `DepartureState` | Typed scalar/tensor departure components before joint kinematic/geometry assembly | immutable contract | declared component units | missing is typed; no implicit zero fill | `htt/src/common/statistical_foundations.py` |
| `JointAnisotropyState` | Current joint congruence, velocity-frame, geometry, unit, missingness, and transfer state authority | content-addressed immutable state | component-declared | no scalar beta or x_C auto-promotion | `htt/src/common/joint_anisotropy_state.py` |
| `SectorStress` | Per-sector anchor stress with value, bound, eligibility, and support kept distinct | immutable diagnostic record | sector-declared | point estimate is not a bound | `htt/src/common/statistical_foundations.py` |
| `IdentifiedDepartureSet` | Partial-identification set with recession and boundedness semantics | immutable set contract | state-coordinate units | missing directions are not zero | `htt/src/common/statistical_foundations.py` |
| `LegacyProjectionReport` | Explicit BC1/BC2 projection from typed state to legacy scalar views | immutable compatibility report | projection-declared | x_C is a lossy signed projection, never the state authority | `htt/src/common/statistical_foundations.py` |
| `AnisotropyTypeReport` | Abstaining orbit/response/local-global/depth compatibility report | immutable typed report | dimensionless identities plus declared units | unknown or indeterminate replaces nearest-family forcing | `htt/src/common/anisotropy_type_report.py` |
| `ConditionalExceedanceSurface` | Registered vector/tensor programme interface for law-typed exceedance envelopes; executable successor currently uses `ConditionalExceedanceProfile` | programme interface plus typed executable profile | probability with declared conditioning | optimizer output is never a sample or posterior | `docs/research_program/vector_tensor/VECTOR_TENSOR_PROOF_PROGRAM_V1.yaml`; `htt/src/common/conditional_exceedance.py` |
| PR4 scope firewall | User-directed ban on PR4 download/intake/reduction/analysis | execution policy | zero commands | complete skip, not inferred completion | `docs/research_program/long_horizon_rescue/pr122_spec.yaml` |

Record overloaded symbols explicitly. A CAS axis may introduce internal names,
but its result must map them back to this table.

---

## Source: `.agent-harness/context/FROZEN_DECISIONS.md`

SHA-256: `16e798e4d40dd41dcf9d679fc39b6dfa32eb61f8f9cf602a15f7cec0f9f26d6e`

# Frozen Decisions and Rejected Alternatives

| Decision ID | Decision | Rationale/evidence | Scope | Reopen condition |
|---|---|---|---|---|
| D-PR4-SKIP | Skip PR4 download, intake, reduction, and all data analysis | Explicit user instruction; PR4 data is absent | Entire roadmap execution | New explicit user direction plus authenticated inputs |
| D-NATIVE-BOUNDARY | Do not implement or simulate the future native low-ell solver | Repository mission and claim firewall | Pre-solver roadmap | Independently authenticated external delivery |
| D-PIN-LITERAL | Keep PR-122 release-pin fields literal-only and parse without module execution | Breaks verifier/graph fixed-point cycle while exposing a reviewable trust root | PR-122 release consumption | A stronger acyclic trust-root design with equivalent exact tests |
| D-AUTH-SNAPSHOT | Consume an immutable PR-122 exact-scope authority snapshot | Later global principal registration must not invalidate historical receipts | PR-122 only | Explicit migration with preserved historical verification |
| D-SINGLE-WRITER | Main agent alone edits production code, specs, shared gates, and shared context | Shared-context harness write-ownership rule | All multi-agent runs | Never within a run; only ownership reassignment before work |
| D-CLAIM-OPEN | Keep all 102 remediation findings OPEN and claim release false | PR-122 supplies mechanics, not scientific authority | PR-122 | Downstream gate evidence under its owning PR |
| D-PR150-RAW-RETAIN | Retain the roughly 731 GB PR3 raw ensemble | Compact replay is green, but PR4 replacement is not authenticated and no storage-swap authorization exists | PR-150/PR4 storage | Authenticated `PR4_REPLACEMENT_READY` receipt plus explicit deletion authorization |
| D-PR151-TWO-PHASE | Run PR-151 acquisition and tracked-artifact finalization as separate phases | Prevents a background downloader from racing the single foreground writer while preserving resumable `.part` files | PR-151 while another PR is foreground | PR-151 is terminal-ready and no foreground PR is being edited |
| D-PR154-SEPARATION | Keep CCHP and SH0ES observed analyses separate and keep unavailable covariance/CF4 overlap in a scenario product | Their sampling units and shared covariance differ; positional CF4 links do not establish physical identity | PR-154 | New authenticated common-covariance and identity data under a versioned scenario |
| D-PR154-T-CONVOLUTION | Keep the host effect Normal in every likelihood lane; Student-t applies only to the measurement residual and is convolved by an explicit Gamma-precision mixture | This is the registered hierarchical model and prevents a robust-measurement sensitivity from silently changing the host population model | PR-154 | A new preregistered model-comparison card with separate estimand and calibration |
| D-PR154-CF4-MATCHED | Require matched baseline coverage, width, and RMSE plus MC guards before any CF4 material-gain scenario | Earlier width-only classification produced false gains, including a zero-slope cell and worse RMSE | PR-154 | New prospective scenario specification with independent calibration data |
| D-ADVOCATE-ORDER | If PR-151 remains incomplete, run PR-167 then PR-168--171 and only the selected defensible queue | Explicit user-approved replan; hypothesis-only and native-dependent lanes remain quarantined | PR-167--183 scheduling | New explicit replan or terminal PR-151 switchback |
| D-ADVOCATE-CLAIM-CEILING | Treat PR-174/175/182 as internal hypothesis-only and PR-183 as native-dependent | Pre-native family/geometry claims remain forbidden | Advocate intake | Native atlas and registered external gates, or explicit scope change that preserves claim firewall |
| D-PR173-ORTHOGONAL | Keep input availability, replicate lineage, and numerical resolution on separate axes | Missing lineage is not evidence that the MC budget is small; partial input cannot produce a final rank | PR-173 and all downstream finite-ensemble consumers | A versioned schema migration with equivalent fail-closed null routing |
| D-PR173-RECONSTRUCTION | Validate reports against freshly reconstructed frozen-source targets and metadata, not self-consistent resealed fields | Independent review reproduced coordinated uncertainty and provenance false greens in the first validator | PR-173 result consumers | A stronger externally rooted verifier with the same or stricter mutation coverage |
| D-PR177-STRICT-SUPPORT | Interpret the canonical `40<L<763` support literally as integer multipoles 41..762 and use one frozen five-component score | The user-authorized plan and canonical backlog override an inclusive intake paraphrase; endpoint or scan drift changes the estimand | PR-177 and direct consumers | A separately preregistered estimand with its own null calibration and claim lane |
| D-PR177-AUTHORITY-REPLAY | Bind result eligibility to frozen PR-152 pins, complete feature/deep input maps, and a separate 401-unit raw-feature replay | Self-consistent card/cache or provenance resealing is not independent source authority; final reviews required complete-map reconstruction | PR-177 result consumers | A stronger external source-attestation mechanism preserving all current falsifiers |
| D-TYPED-FOUNDATION | Use `JointAnisotropyState` as current scientific state authority; expose scalar x_C only through `LegacyProjectionReport(BC1/BC2)` | PR-248--275 typed foundation and post-275 reconciliation; scalar projection loses state, frame, missingness, and orbit information | All current scientific consumers | A proof-bearing receipt demonstrates that BC1 is violated |
| D-GOVERNANCE-BRAKE-2026-08 | After two consecutive assurance-only PRs, require the next PR to deliver a named downstream scientific capability, data integration, experiment, or interpretable result unless a reproduced high-severity defect directly blocks it | Gate count and document volume are not research progress; assurance work must serve a named consumer | Post-275 scheduling and replan decisions | A versioned replacement names a downstream consumer and reproduces the failure it prevents |

Agents must not silently reopen a frozen decision. A proposed reversal is a
meta-finding with new evidence and an explicit reopen condition.
