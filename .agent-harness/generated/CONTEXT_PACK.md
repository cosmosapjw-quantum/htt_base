# Generated Shared Context View

Context version: `af2a97b0542adbf5f4334814739aa5b4436bf757986fe5080f4429806292f249`
Built at: `2026-08-03T10:39:26+00:00`

This compact view is generated from the machine context index. Live HEAD, DAG, status, and active-run context is computed by the hooks at use time. Reference-only files are read only when an assignment names them.

---

## Source: `.agent-harness/context/SYMBOLS.md`

SHA-256: `ecd8f2f66183c201655262be08ef31ec5f125869d014fcb3782b5902b8c43570`

# Symbol and Interface Table

| Symbol / interface | Definition | Domain / type | Units / dimensions | Sign / branch convention | Source of truth |
|---|---|---|---|---|---|
| `EvidenceAxes` | Separate process/evidence/science states | enum triple | 1 | no cross-promotion | `htt/src/common/evidence_graph.py` |
| `EvidenceGraph` | Acyclic content-addressed evidence graph | immutable record | 1 | canonical JSON SHA-256 | `htt/src/common/evidence_graph.py` |
| `TestExecution` | Collected/executed/outcome/environment receipt | typed record | counts/hashes | skip/xfail are not pass | `htt/src/common/evidence_graph.py` |
| `ReleaseEvidencePin` | Literal-only fixed-point view | paths/hashes | 1 | no pin-module import | `htt/src/common/release_evidence_binding.py` |
| `AuthorityRegistry` | Principal/role/scope verifier registry | immutable records | 1 | correlated identities do not promote | `htt/src/common/remediation_state.py` |
| `MatchedNullCompetitionReport` | HTT matched-null adequacy report | typed report | declared | caller scalars are non-authoritative | `htt/htt/htt/infer/null_competition.py` |
| `MESAnchorSpec` | MES anchor/domain/frame/provenance authority | immutable contract | component-declared | explicit role/denominator | `htt/src/common/statistical_foundations.py` |
| `DepartureState` | Pre-joint scalar/tensor components | immutable contract | component-declared | typed missing; no zero fill | `htt/src/common/statistical_foundations.py` |
| `JointAnisotropyState` | Current congruence/frame/geometry/missingness/transfer state | content-addressed state | component-declared | no scalar auto-promotion | `htt/src/common/joint_anisotropy_state.py` |
| `SectorStress` | Separate sector value/bound/eligibility/support | diagnostic record | sector-declared | estimate is not bound | `htt/src/common/statistical_foundations.py` |
| `IdentifiedDepartureSet` | Partial-ID set with recession/boundedness | immutable set | state units | missing is not zero | `htt/src/common/statistical_foundations.py` |
| `LegacyProjectionReport` | BC1/BC2 typed-to-scalar projection | compatibility report | declared | x_C is lossy, not state | `htt/src/common/statistical_foundations.py` |
| `AnisotropyTypeReport` | Abstaining orbit/response/local-global/depth report | typed report | declared | unknown replaces nearest-family | `htt/src/common/anisotropy_type_report.py` |
| `ConditionalExceedanceSurface` | Law-typed programme interface; executable `ConditionalExceedanceProfile` | interface/profile | probability | optimizer is not sample/posterior | `docs/research_program/vector_tensor/VECTOR_TENSOR_PROOF_PROGRAM_V1.yaml`; `htt/src/common/conditional_exceedance.py` |
| PR4 firewall | Ban PR4 download/intake/reduction/analysis | policy | zero commands | skip is not completion | `docs/research_program/long_horizon_rescue/pr122_spec.yaml` |

Record overloaded symbols explicitly. A CAS axis may introduce internal names,
but its result must map them back to this table.

---

## Source: `.agent-harness/context/FROZEN_DECISIONS.md`

SHA-256: `dfa4d0cbe1eba10433c86378343724a5a3c56cc2b6a971ef31811b0a41c1cb00`

# Frozen Decisions and Rejected Alternatives

| Decision ID | Decision | Rationale/evidence | Scope | Reopen condition |
|---|---|---|---|---|
| D-PR4-SKIP | Skip PR4 download, intake, reduction, and all data analysis | Explicit user instruction; PR4 data is absent | Entire roadmap execution | New explicit user direction plus authenticated inputs |
| D-NATIVE-BOUNDARY | Do not implement or simulate the future native low-ell solver | Repository mission and claim firewall | Pre-solver roadmap | Independently authenticated external delivery |
| D-PIN-LITERAL | Keep PR-122 release-pin fields literal-only and parse without module execution | Breaks verifier/graph fixed-point cycle while exposing a reviewable trust root | PR-122 release consumption | A stronger acyclic trust-root design with equivalent exact tests |
| D-AUTH-SNAPSHOT | Consume an immutable PR-122 exact-scope authority snapshot | Later global principal registration must not invalidate historical receipts | PR-122 only | Explicit migration with preserved historical verification |
| D-SINGLE-WRITER | Main agent alone edits production code, specs, shared gates, and shared context | Shared-context harness write-ownership rule | All multi-agent runs | Never within a run; only ownership reassignment before work |
| D-CLAIM-OPEN | Keep all 102 remediation findings OPEN and claim release false | PR-122 supplies mechanics, not scientific authority | PR-122 | Downstream gate evidence under its owning PR |
| D-PR150-RAW-RETAIN | Retain the roughly 731 GB PR3 raw ensemble | No authenticated PR4 replacement or deletion authority | PR-150/PR4 storage | `PR4_REPLACEMENT_READY` plus explicit deletion authority |
| D-PR151-TWO-PHASE | Separate acquisition from tracked finalization | Avoid downloader/single-writer races; preserve `.part` files | PR-151 with foreground work | PR-151 terminal-ready and no foreground edit |
| D-PR154-SEPARATION | Keep CCHP/SH0ES analyses separate; model unavailable covariance/CF4 overlap only as a scenario | Sampling units/covariance differ; positional links are not identity | PR-154 | Authenticated common covariance and identity |
| D-PR154-T-CONVOLUTION | Host effect stays Normal; Student-t applies only to measurement residual via Gamma-precision convolution | Preserve the registered hierarchy | PR-154 | Preregistered replacement estimand/calibration |
| D-PR154-CF4-MATCHED | Require matched coverage, width, RMSE, and MC guards for CF4 gain | Width-only rules produced false gains | PR-154 | Prospective independently calibrated scenario |
| D-ADVOCATE-ORDER | While PR-151 is incomplete, run PR-167 then PR-168--171 and the selected queue | User-approved replan; other lanes stay quarantined | PR-167--183 | Explicit replan or PR-151 terminal switchback |
| D-ADVOCATE-CLAIM-CEILING | PR-174/175/182 are hypothesis-only; PR-183 is native-dependent | Pre-native family/geometry claims are forbidden | Advocate intake | Native atlas/gates or firewall-preserving scope change |
| D-PR173-ORTHOGONAL | Separate availability, lineage, and numerical-resolution axes | Missing lineage says nothing about MC budget | PR-173 finite-ensemble consumers | Equivalent fail-closed versioned migration |
| D-PR173-RECONSTRUCTION | Validate against reconstructed frozen-source targets, not self-resealed fields | First validator admitted coordinated false greens | PR-173 consumers | Stronger external verifier preserving mutations |
| D-PR177-STRICT-SUPPORT | `40<L<763` means integer multipoles 41..762 with one frozen five-component score | Endpoint/scan drift changes the estimand | PR-177 consumers | Separately preregistered estimand/null |
| D-PR177-AUTHORITY-REPLAY | Bind eligibility to PR-152 pins, complete maps, and separate 401-unit raw replay | Self-resealing is not source authority | PR-177 consumers | Stronger external attestation preserving falsifiers |
| D-TYPED-FOUNDATION | `JointAnisotropyState` is current; scalar x_C only via `LegacyProjectionReport(BC1/BC2)` | Projection loses state/frame/missingness/orbit | Current science | Proof-bearing BC1 violation |
| D-GOVERNANCE-BRAKE-2026-08 | After two assurance-only PRs, require named science/data/experiment output unless a reproduced severe blocker intervenes | Gates/doc volume are not progress | Post-275 scheduling | Versioned consumer-backed replacement |

Agents must not silently reopen a frozen decision. A proposed reversal is a
meta-finding with new evidence and an explicit reopen condition.
