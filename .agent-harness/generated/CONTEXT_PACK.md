# Generated Shared Context View

Context version: `2aadf7ee464f3801564eb811ce842dacce78a59d68206d10d6304fbb79a13fa4`
Built at: `2026-07-23T04:51:57+00:00`

This compact view is generated from the machine context index. Live HEAD, DAG, status, and active-run context is computed by the hooks at use time. Reference-only files are read only when an assignment names them.

---

## Source: `.agent-harness/context/SYMBOLS.md`

SHA-256: `5c51f848f93430c8b49d46bd66219162409f06b35fdf778ea9f44c0bf5d214cb`

# Symbol and Interface Table

| Symbol / interface | Definition | Domain / type | Units / dimensions | Sign / branch convention | Source of truth |
|---|---|---|---|---|---|
| `EvidenceAxes` | Orthogonal process, evidence, and scientific status tuple | typed enum triple | dimensionless | no axis may promote another | `htt/src/common/evidence_graph.py` |
| `EvidenceGraph` | Typed acyclic content-addressed claim/evidence graph | immutable graph record | dimensionless | SHA-256 canonical JSON identity | `htt/src/common/evidence_graph.py` |
| `TestExecution` | Exact collected/executed/outcome/environment receipt | typed pytest evidence record | counts and SHA-256 refs | skipped/xfail are not passes | `htt/src/common/evidence_graph.py` |
| `ReleaseEvidencePin` | Typed view of literal-only fixed-point fields | repository-relative paths and SHA-256 refs | dimensionless | parsed without importing pin module | `htt/src/common/release_evidence_binding.py` |
| `AuthorityRegistry` | Exact principal/role/scope verifier registry | immutable principal records | dimensionless | correlated internal identities cannot promote science | `htt/src/common/remediation_state.py` |
| `MatchedNullCompetitionReport` | Canonical HTT matched-null adequacy report | exact typed report | report-defined | caller scalar or duck type is non-authoritative | `htt/htt/htt/infer/null_competition.py` |
| PR4 scope firewall | User-directed ban on PR4 download/intake/reduction/analysis | execution policy | zero commands | complete skip, not inferred completion | `docs/research_program/long_horizon_rescue/pr122_spec.yaml` |

Record overloaded symbols explicitly. A CAS axis may introduce internal names,
but its result must map them back to this table.

---

## Source: `.agent-harness/context/FROZEN_DECISIONS.md`

SHA-256: `59b28e22613b2a8b1e1b04a679b9c822aa9d7d74ad15aea06c16537a7e0e8fd6`

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

Agents must not silently reopen a frozen decision. A proposed reversal is a
meta-finding with new evidence and an explicit reopen condition.
