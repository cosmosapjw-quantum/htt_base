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
