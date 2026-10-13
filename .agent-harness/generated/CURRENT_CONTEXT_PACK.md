# Generated Shared Context View

Context version: `598074d109cc2fa66c6ba11a57875034a01682a7edc2b026a230d500fcd28b9e`
Built at: `2026-10-08T11:59:42+00:00`

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

## Source: `.agent-harness/context/CURRENT_FROZEN_DECISIONS.md`

SHA-256: `4f57d8eaf9f4f7920e8dcf738609b1ab12ade79e6c9316e70d067999c90d31a5`

# Current execution and scientific boundaries

- Work in the existing repo root. Isolate only after explicit owner approval of a concrete reason. Preserve unrelated edits, task IDs, cumulative costs and historical directory bindings.
- New tasks use owner-directed native subagents with explicit supported model/effort, fresh context, disjoint authors and a separate read-only reviewer. Requested settings are not observed runtime. Removed CUH-G registration/descriptor are not prerequisites; actual system/developer and managed restrictions still apply. Reload revised SessionStart guidance in a fresh session when an old instruction is already injected.
- Adaptive budgets are planning targets; continue the same scientific task by replanning. Explicit hard limits and scientific tolerances remain binding. No default 30-minute worker cutoff.
- Use verified summaries and original references for context. Removed Bonsai/CUH-G telemetry are not new-task prerequisites and are not restored. Preserve available historical usage; unknown measurements remain unknown.
- HTT owns inference; MIO owns diagnostics; obsstat extracts features. Native low-ell family identification remains blocked. External transfer stays conditional. PR4 remains outside authorized work.
- Preserve frozen assignment/context and CAS contracts. Historical four-axis admission still requires its original tools and validators. New tasks use strength-based proof division, core kernel validation and separate independent review; shared author lemmas are not independent rediscovery, and the new procedure does not pass old validators. No scientific promotion.
- R1 routine publication uses provider success and remote identity. R2 adds an existing manifest. R3 is required for authority/recovery/destructive changes or explicit content verification. Do not clone/download routinely for R1.
- Source identity, numerical reproducibility and byte replay are distinct. Diagnose a differing field before changing any expected hash or tolerance. Runtime/test/review/publication success does not promote scientific claims.

## Historical decisions: read only when the assignment touches their scope

The original decisions, rationales and reopen conditions are retained without alteration in `.agent-harness/context/FROZEN_DECISIONS.md`:

D-PR4-SKIP, D-NATIVE-BOUNDARY, D-PIN-LITERAL, D-AUTH-SNAPSHOT, D-SINGLE-WRITER, D-CLAIM-OPEN, D-PR150-RAW-RETAIN, D-PR151-TWO-PHASE, D-PR154-SEPARATION, D-PR154-T-CONVOLUTION, D-PR154-CF4-MATCHED, D-ADVOCATE-ORDER, D-ADVOCATE-CLAIM-CEILING, D-PR173-ORTHOGONAL, D-PR173-RECONSTRUCTION, D-PR177-STRICT-SUPPORT, D-PR177-AUTHORITY-REPLAY.

No decision is reopened by moving its full text out of the injected core.
