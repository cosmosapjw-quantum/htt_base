# Generated Shared Context View

Context version: `e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019`
Built at: `2026-08-03T13:58:43+00:00`

This compact view is generated from the machine context index. Live HEAD, DAG, status, and active-run context is computed by the hooks at use time. Reference-only files are read only when an assignment names them.

---

## Source: `.agent-harness/context/SYMBOLS.md`

SHA-256: `64b2361ff8ce7e9c40b573918a4b2e41c861dc8f8ef116ef5c33c1dc19a578db`

# Symbol and Interface Table

| Symbol / interface | Definition | Domain / type | Units / dimensions | Sign / branch convention | Source of truth |
|---|---|---|---|---|---|
| `EvidenceAxes` | Separate process/evidence/science states | enum triple | 1 | no cross-promotion | `htt/src/common/evidence_graph.py` |
| `EvidenceGraph` | Acyclic content-addressed evidence graph | immutable record | 1 | canonical JSON SHA-256 | `htt/src/common/evidence_graph.py` |
| `TestExecution` | Collected/executed/outcome/environment receipt | typed record | counts/hashes | skip/xfail not pass | `htt/src/common/evidence_graph.py` |
| `ReleaseEvidencePin` | Literal-only fixed-point view | paths/hashes | 1 | no pin-module import | `htt/src/common/release_evidence_binding.py` |
| `AuthorityRegistry` | Principal/role/scope verifier registry | immutable records | 1 | correlated identities do not promote | `htt/src/common/remediation_state.py` |
| `MatchedNullCompetitionReport` | HTT matched-null adequacy report | typed report | declared | caller scalars non-authoritative | `htt/htt/htt/infer/null_competition.py` |
| `MESAnchorSpec` | MES anchor/domain/frame/provenance authority | immutable contract | component-declared | explicit role/denominator | `htt/src/common/statistical_foundations.py` |
| `DepartureState` | Pre-joint scalar/tensor components | immutable contract | component-declared | typed missing; no zero fill | `htt/src/common/statistical_foundations.py` |
| `JointAnisotropyState` | Current congruence/frame/geometry/missingness/transfer state | content-addressed state | component-declared | no scalar auto-promotion | `htt/src/common/joint_anisotropy_state.py` |
| `SectorStress` | Separate sector value/bound/eligibility/support | diagnostic record | sector-declared | estimate not bound | `htt/src/common/statistical_foundations.py` |
| `IdentifiedDepartureSet` | Partial-ID set with recession/boundedness | immutable set | state units | missing not zero | `htt/src/common/statistical_foundations.py` |
| `LegacyProjectionReport` | BC1/BC2 typed-to-scalar projection | compatibility report | declared | x_C lossy, not state | `htt/src/common/statistical_foundations.py` |
| `AnisotropyTypeReport` | Abstaining orbit/response/local-global/depth report | typed report | declared | unknown replaces nearest-family | `htt/src/common/anisotropy_type_report.py` |
| `ConditionalExceedanceSurface` | Law-typed programme interface; executable `ConditionalExceedanceProfile` | interface/profile | probability | optimizer not sample/posterior | `docs/research_program/vector_tensor/VECTOR_TENSOR_PROOF_PROGRAM_V1.yaml`; `htt/src/common/conditional_exceedance.py` |
| `VersionedClaimIdentity`; `ClaimCapabilityDecision`; `CapabilityBlocker` | Six-part successor identity; factory-issued capability; scoped blocker | content-addressed immutable records | 1 | new identity on change; derived grant; graph blockers mandatory | `htt/src/common/remediation_state.py`; `htt/src/common/evidence_graph.py` |
| PR4 firewall | Ban PR4 download/intake/reduction/analysis | policy | zero commands | skip not completion | `docs/research_program/long_horizon_rescue/pr122_spec.yaml` |

Record overloaded symbols explicit. CAS axis may add internal names, but result must map them back to this table.

---

## Source: `.agent-harness/context/FROZEN_DECISIONS.md`

SHA-256: `dd3f880356ad67d39b75bb654a9b7e9d80852f3d75da72d903ea45c862a9a66b`

# Frozen Decisions and Rejected Alternatives

| Decision ID | Decision | Rationale/evidence | Scope | Reopen condition |
|---|---|---|---|---|
| D-PR4-SKIP | Skip PR4 download, intake, reduction, all data analysis | User instruction; PR4 data absent | Whole roadmap execution | New user direction + authenticated inputs |
| D-NATIVE-BOUNDARY | No implement/simulate future native low-ell solver | Repo mission + claim firewall | Pre-solver roadmap | Independently authenticated external delivery |
| D-PIN-LITERAL | Literal-only PR-122 release pins; parse without import | Avoid fixed-point cycle; reviewable trust root | PR-122 | Equivalent stronger acyclic trust root + exact tests |
| D-AUTH-SNAPSHOT | Immutable PR-122 exact-scope authority snapshot | Later principals cannot invalidate old receipts | PR-122 | Migration preserving historical verification |
| D-SINGLE-WRITER | Main agent edits production/specs/shared gates+context | Harness write ownership | Multi-agent runs | Pre-work ownership reassignment only |
| D-CLAIM-OPEN | Keep all 102 remediation findings OPEN; claim release false | PR-122 supplies mechanics, not scientific authority | PR-122 | Downstream gate evidence under owning PR |
| D-PR150-RAW-RETAIN | Retain ~731 GB PR3 raw ensemble | No authenticated PR4 replacement/deletion authority | PR-150/PR4 storage | `PR4_REPLACEMENT_READY` + deletion authority |
| D-PR151-TWO-PHASE | Separate acquisition from tracked finalization | Avoid downloader/single-writer races; preserve `.part` files | PR-151 with foreground work | PR-151 terminal-ready + no foreground edit |
| D-PR154-SEPARATION | Separate CCHP/SH0ES; unavailable covariance/CF4 overlap is scenario-only | Different sampling/covariance; position not identity | PR-154 | Authenticated common covariance+identity |
| D-PR154-T-CONVOLUTION | Host effect stays Normal; Student-t only on measurement residual via Gamma-precision convolution | Preserve registered hierarchy | PR-154 | Preregistered replacement estimand/calibration |
| D-PR154-CF4-MATCHED | Require matched coverage, width, RMSE, MC guards for CF4 gain | Width-only rules produced false gains | PR-154 | Prospective independently calibrated scenario |
| D-ADVOCATE-ORDER | While PR-151 incomplete, run PR-167 then PR-168--171 + selected queue | User-approved replan; other lanes stay quarantined | PR-167--183 | Replan or PR-151 terminal switchback |
| D-ADVOCATE-CLAIM-CEILING | PR-174/175/182 hypothesis-only; PR-183 native-dependent | Pre-native family/geometry claims forbidden | Advocate intake | Native atlas/gates or firewall-preserving scope change |
| D-PR173-ORTHOGONAL | Separate availability, lineage, numerical-resolution axes | Missing lineage says nothing about MC budget | PR-173 finite-ensemble consumers | Equivalent fail-closed versioned migration |
| D-PR173-RECONSTRUCTION | Validate reconstructed frozen targets, not self-resealed fields | First validator admitted false greens | PR-173 | Stronger external verifier preserving mutations |
| D-PR177-STRICT-SUPPORT | `40<L<763` means integer multipoles 41..762 with one frozen five-component score | Endpoint/scan drift changes estimand | PR-177 consumers | Separately preregistered estimand/null |
| D-PR177-AUTHORITY-REPLAY | Bind eligibility to PR-152 pins, complete maps, separate 401-unit raw replay | Self-resealing not source authority | PR-177 consumers | Stronger external attestation preserving falsifiers |
| D-TYPED-FOUNDATION | `JointAnisotropyState` current; scalar x_C only via `LegacyProjectionReport(BC1/BC2)` | Projection loses state/frame/missingness/orbit | Current science | Proof-bearing BC1 violation |
| D-GOVERNANCE-BRAKE-2026-08 | After 2 assurance PRs, require named science/data/experiment unless severe reproduced blocker | Gates/docs not progress | Post-275 | Versioned consumer-backed replacement |
| D-EVIDENCE-CONDITIONED-CAPABILITY | No capability from DAG/caller; require exact evidence+adjudication, bound request, graph blockers | PR-277 reproduced three laundering paths | Post-277 claims | Independently adjudicated versioned replacement only |

Agents must not silently reopen frozen decision. Proposed reversal = meta-finding
with new evidence + explicit reopen condition.
