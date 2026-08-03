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
