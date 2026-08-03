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
