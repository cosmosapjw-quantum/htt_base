# TSC Active Service Upgrade for BASS / HTT / MIO
## SDD 기반 WBS 및 PR 실행계획

**Version**: v1.2-tsc-active-service-integrated  
**Date**: 2026-04-21  
**Document role**: root master plan. 이 문서는 기존 root-path PR list / WBS / SDD 문서를 유지하면서, `teff_characteristics` 하위에 추가된 source bundle과 RE2 refined plan을 통합한 현재 기준 실행 문서다.

---

## 0. Canonical source integration

이 문서는 계속 루트 경로에 남긴다. 이유는 다른 `ver2` 문서들이 이미 아래 경로를 참조하고 있기 때문이다.

- `docs/ver2_upgrade/TSC_active_service_SDD_WBS_PR_plan.md`

동시에, 이번에 추가된 `teff_characteristics` 문서군을 이제 TSC 확장의 핵심 semantic input으로 간주한다.

### 0.1 Companion documents

- Narrative companion:
  - [teff_characteristics/TSC_active_service_SDD_WBS_PR_plan.md](teff_characteristics/TSC_active_service_SDD_WBS_PR_plan.md)
- Refined execution decomposition:
  - [teff_characteristics/TSC_active_service_SDD_WBS_PR_plan_v3_RE2_refined.md](teff_characteristics/TSC_active_service_SDD_WBS_PR_plan_v3_RE2_refined.md)
- Root compatibility pointer:
  - [TSC_active_service_SDD_WBS_PR_plan_v3_RE2_refined.md](TSC_active_service_SDD_WBS_PR_plan_v3_RE2_refined.md)

### 0.2 Source bundle integrated in this document

| Source | Integrated role in this master plan |
|---|---|
| [teff_characteristics/00_README_index_and_source_boundaries.md](teff_characteristics/00_README_index_and_source_boundaries.md) | source boundary, reading order, canonicality rules |
| [teff_characteristics/01_constitution_scope_and_claim_language.md](teff_characteristics/01_constitution_scope_and_claim_language.md) | constitution, claim-language hard limits, owner firewall |
| [teff_characteristics/02_papers_I_to_V_upgrade_ledger.md](teff_characteristics/02_papers_I_to_V_upgrade_ledger.md) | Paper I-V theorem contributions and upgrade ledger |
| [teff_characteristics/03_reduction_geometry_and_theorem_compendium.md](teff_characteristics/03_reduction_geometry_and_theorem_compendium.md) | reduction geometry, theorem map, proof obligations |
| [teff_characteristics/04_characteristics_architecture_closure_free_backbone.md](teff_characteristics/04_characteristics_architecture_closure_free_backbone.md) | `characteristics` ontology correction and full-state backbone scope |
| [teff_characteristics/05_trace_intensity_semantics_and_polarisation_bridge.md](teff_characteristics/05_trace_intensity_semantics_and_polarisation_bridge.md) | exact trace/intensity semantics, nonlinear Thomson bridge, polarisation boundary |
| [teff_characteristics/06_proof_obligations_and_claim_status.md](teff_characteristics/06_proof_obligations_and_claim_status.md) | claim status taxonomy and validation obligations |
| [teff_characteristics/07_validation_protocol_and_test_matrix.md](teff_characteristics/07_validation_protocol_and_test_matrix.md) | validation protocol, Layer A/B/C/R matrix, artifact policy |
| [teff_characteristics/08_red_team_reviewer_defense.md](teff_characteristics/08_red_team_reviewer_defense.md) | adversarial wording defense, no-overclaim policy |
| [teff_characteristics/09_patch_map_for_existing_md_and_manuscripts.md](teff_characteristics/09_patch_map_for_existing_md_and_manuscripts.md) | doc/manuscript patch targets and wording synchronization |

### 0.3 Interpretation rule

- 이 root 문서는 umbrella-level SDD/WBS/PR master plan이다.
- 세분화된 file-level WBS, dependency graph, tests, done criteria는 refined companion이 더 자세하다.
- 두 문서가 다르면 `teff_characteristics`의 refined companion이 세부 실행 기준으로 우선한다.

---

## 1. Executive summary

기존 SSoT는 유지한다. full-state transport backbone과 runtime reduction authority는 BASS/`characteristics` 쪽에 있고, HTT는 model-dependent inference owner이며, MIO는 model-independent observatory/certificate owner다. TSC는 이 권한 구조를 침범하면 안 된다.

하지만 `teff_characteristics` 문서군은 TSC를 단순 chart checker나 사후 lint 층으로 두기에는 이미 근거가 충분히 확장되었음을 보여준다. trace residual이 Thomson source error를 제어하고, source mismatch가 field/spectrum adequacy chain으로 이어지며, one-field failure의 일부가 실제로는 `eta` tangent deficiency일 수 있다는 점이 정리되어 있다. 따라서 TSC는 bounded but active service layer로 승격되어야 한다.

TSC가 능동적으로 제공해야 하는 것:

- BASS에 대해:
  - trace-source bridge
  - domain/admissibility guard
  - trace/source/channel caveat
  - diagnose-before-switch recommendation
- HTT에 대해:
  - likelihood-scope caveat
  - channel claim ceiling
  - source/propagation split metadata
  - scalar-only overclaim warning
- MIO에 대해:
  - diagnostic certificate caveat
  - trace/spin-2/high burden labeling
  - diagnostic-only trigger
- common / atlas / report cards에 대해:
  - `TscAdequacyOverlay`
  - `tsc_overlay_id`
  - block scope / claim status / validation coverage

핵심 설계 문장:

> TSC is an active trace-source adequacy service, not a runtime authority, posterior owner, truth certificate owner, or spin-2 solver.

---

## 2. Source-grounded SDD constraints

### 2.1 Ontology and owner boundary

- `characteristics`는 closure가 아니라 closure-free full-state transport backbone이다.
- Teff/TSC는 full transport law를 대체하지 않는다.
- TSC의 직접 의미론은 trace/intensity block에 한정된다.
- spin-2 block과 high residual block을 TSC가 지우거나 대체하면 안 된다.

### 2.2 Defect and residual separation

이번 source bundle은 다음 분리를 hard requirement로 만든다.

- ambient defect vs projected defect
- collision residual `D_coll` vs state residual `D_state`
- observable discrepancy `Delta_obs`
- source adequacy vs propagation adequacy vs observable adequacy

따라서 TSC는 하나의 단일 `error` 필드로 모든 의미를 접어버리면 안 된다.

### 2.3 Trace-source adequacy boundary

- on-manifold trace/intensity source bridge는 exactness를 가질 수 있다.
- off-manifold에서는 source mismatch bound만 말할 수 있다.
- TSC는 `source_budget`까지는 강하게 말할 수 있지만, `field_budget`과 `spectrum_budget`은 propagation constant 또는 validation status가 있을 때만 조건부로 말할 수 있다.

### 2.4 Polarisation and morphology boundary

- TT는 trace block adequacy가 강한 역할을 가질 수 있다.
- EE는 trace-source adequacy와 spin-2 propagation adequacy를 둘 다 요구한다.
- TE는 mixed responsibility다.
- BB는 TSC-only trace semantics로 제어 또는 validation claim을 하면 안 된다.
- BiPoSH, morphology, family identification은 TSC-only claim이 금지된다.

### 2.5 Paper I-V integration

- Paper I: per-ray instantaneous tangency diagnostic
- Paper II: direction-dependent `eta`가 non-redundant tangent degree
- Paper III: Gram-Hessian identity, Pythagorean decomposition, two-field tangency
- Paper IV: observable semantics and reconstructive adequacy
- Paper V: trace/intensity transparency와 nonlinear Thomson source parameterisation, 그러나 full spin-2 propagation parameterisation은 아님

---

## 3. Integrated SDD/WBS approach

이 master plan은 기존 `PR-TSC-*` list를 umbrella packet으로 유지하되, 실제 refined execution은 `PR-TSC3-*` decomposition으로 세분화한다.

### Wave A. Constitution and owner firewall

- scope language freeze
- owner boundary freeze
- theorem / proof-obligation / claim-status vocabulary freeze

Primary packets:

- `PR-TSC-00`
- `PR-TSC-10`
- `PR-TSC-11`
- `PR-TSC-13`

### Wave B. Stat-mech and trace kernel

- Fisher/Gram/Hessian structure
- one-field / two-field tangency projection
- domain / admissibility / realizability guard
- quadrupole convention registry
- nonlinear Thomson trace-source bridge
- eta-source semantics

Primary packets:

- `PR-TSC-01`
- `PR-TSC-02`
- `PR-TSC-03`
- `PR-TSC-04`

### Wave C. Adequacy budgets and switching

- `D_coll`, `D_state`, `Delta_obs` separation
- channel burden and claim ceiling
- diagnose-before-switch advisor

Primary packets:

- `PR-TSC-02`
- `PR-TSC-03`
- `PR-TSC-05`

### Wave D. Downstream overlays and extension bridges

- BASS overlay/handoff
- HTT caveat adapter
- MIO certificate adapter
- atlas / observable coverage integration

Primary packets:

- `PR-TSC-06`
- `PR-TSC-07`
- `PR-TSC-08`
- `PR-TSC-09`
- `PR-TSC-12`

### Wave E. Validation, red-team defense, and outward-facing outputs

- theorem-indexed artifact set
- Layer A/B/C/R validation protocol
- document/manuscript patching
- acceptance dashboard and result packs

Primary packets:

- `PR-TSC-10`
- `PR-TSC-11`
- `PR-TSC-12`
- `PR-TSC-13`

---

## 4. Original `PR-TSC-*` umbrella list with integrated source deltas

| PR | Umbrella goal | Integrated source deltas | Refined packets | Current status |
|---|---|---|---|---|
| `PR-TSC-00` | contracts, ownership firewall, SSoT guard | `00`, `01`, `06`, `08` | `PR-TSC3-00`, `01`, `02` | `seeded` at skeleton level, refined scope pending |
| `PR-TSC-01` | chart domain and admissibility guard | `01`, `02`, `06` | `PR-TSC3-05` | `seeded` |
| `PR-TSC-02` | residual and defect reports | `02`, `03`, `06`, `07` | `PR-TSC3-09`, `10` | `planned` beyond skeleton |
| `PR-TSC-03` | one-field/two-field false-trigger decomposition and upgrade advisor | `02`, `03`, `06` | `PR-TSC3-03`, `04`, `12` | `planned` beyond skeleton |
| `PR-TSC-04` | nonlinear Thomson trace-source bridge | `02`, `05`, `06` | `PR-TSC3-06`, `07`, `08` | `seeded` for bridge skeleton, refined scope pending |
| `PR-TSC-05` | source-to-channel adequacy budget | `05`, `06`, `07` | `PR-TSC3-10`, `11` | `seeded` at skeleton / claim-ceiling boundary |
| `PR-TSC-06` | BASS adapter and runtime handoff | `01`, `04`, `06`, `08` | `PR-TSC3-13` | `seeded` |
| `PR-TSC-07` | HTT inference caveat adapter | `01`, `06`, `08` | `PR-TSC3-14` | `seeded` |
| `PR-TSC-08` | MIO certificate adapter | `01`, `06`, `08` | `PR-TSC3-15` | `seeded` |
| `PR-TSC-09` | observable atlas coverage map | `04`, `06`, `07`, `08` | `PR-TSC3-16` | `planned` |
| `PR-TSC-10` | validation theorem map and runbook integration | `03`, `06`, `07` | `PR-TSC3-02`, `17` | `seeded` for theorem-map skeleton, refined artifact layer pending |
| `PR-TSC-11` | no-overclaim lint and quarantine | `01`, `06`, `08`, `09` | `PR-TSC3-18` | `seeded` |
| `PR-TSC-12` | overlay builder and artifact exporter | `06`, `07`, `08`, `09` | `PR-TSC3-13`, `14`, `15`, `16`, `19` | `seeded` for base overlay, full aggregation pending |
| `PR-TSC-13` | documentation, SDD sync, manuscript snippets | `01`, `06`, `08`, `09` | `PR-TSC3-20` | `planned` |

Status vocabulary:

- `seeded`: skeleton interfaces, guards, or advisory-only surfaces already landed or audited.
- `planned`: theorem-backed, numerically complete, or full downstream-connected packet remains open.

---

## 5. Refined `PR-TSC3-*` portfolio now absorbed by this plan

`teff_characteristics/TSC_active_service_SDD_WBS_PR_plan_v3_RE2_refined.md`는 기존 umbrella packets를 다음처럼 세분화한다.

### Foundation / governance

- `PR-TSC3-00` source-grounded SDD v3 and RE2 summary ledger
- `PR-TSC3-01` contracts, schema versioning, and owner firewall
- `PR-TSC3-02` theorem, proof-obligation, validation, and claim registry

### Mathematical / physics kernel

- `PR-TSC3-03` statistical-mechanical Fisher/Gram kernel
- `PR-TSC3-04` tangency projection and one/two-field residual monotonicity
- `PR-TSC3-05` domain, admissibility, and realizability guard
- `PR-TSC3-06` quadrupole convention registry and regression tests
- `PR-TSC3-07` exact on-manifold nonlinear Thomson trace-source bridge
- `PR-TSC3-08` two-field eta source semantics
- `PR-TSC3-09` ambient/projected defect service
- `PR-TSC3-10` collision/state/observable residual bridge
- `PR-TSC3-11` channelwise adequacy budget and claim ceiling
- `PR-TSC3-12` diagnose-before-switch advisor with hysteresis

### Cross-module overlays

- `PR-TSC3-13` BASS overlay adapter
- `PR-TSC3-14` HTT overlay adapter
- `PR-TSC3-15` MIO overlay adapter
- `PR-TSC3-16` Observable Atlas overlay integration

### Validation / outward-facing outputs

- `PR-TSC3-17` validation artifact set and runbook integration
- `PR-TSC3-18` red-team no-overclaim and document patch lint
- `PR-TSC3-19` acceptance dashboard and result packs
- `PR-TSC3-20` SDD, documentation, and manuscript sync

이 root 문서에서는 위 세분화가 기존 `PR-TSC-*` umbrella를 깨지 않고 흡수되도록 매핑을 유지한다.

---

## 6. Cross-module extension map

| Downstream surface | TSC service attachment | What TSC may say | What TSC must not own |
|---|---|---|---|
| BASS runtime / transport artifacts | source bridge, domain guard, channel burden, switch recommendation, caveat overlay | source adequacy, propagation pending, chart invalidity, switch recommendation | `allow_reduction`, final runtime authority, full transport ownership |
| HTT likelihood / posterior result surfaces | claim ceiling, channel caveat, scalar-only warning, manifest-backed overlay | inference-scope caveat, response validity flag, source/propagation split metadata | posterior arithmetic, evidence updates, ranking ownership |
| MIO certificates | diagnostic adequacy fields, source/spin-2/high caveats, diagnostic-only trigger | trace-covered vs spin-2-required vs propagation-pending diagnostics | truth certification, posterior language, model adjudication |
| Observable atlas / report cards | `tsc_overlay_id`, block scope, claim status, validation coverage | trace/source/mixed/safe-to-claim labels with caveat | morphology authority, family identification, spin-2 proof ownership |

---

## 7. Acceptance requirements integrated from the new docs

| Requirement | Owner packet(s) |
|---|---|
| `characteristics` is never described as closure | `PR-TSC-00`, `PR-TSC-11`, `PR-TSC-13` |
| TSC is never described as full solver / posterior owner / truth certifier | `PR-TSC-00`, `PR-TSC-11`, `PR-TSC-13` |
| ambient defect and projected defect stay separate | `PR-TSC-02` |
| `D_coll`, `D_state`, `Delta_obs` stay separate | `PR-TSC-02`, `PR-TSC-05`, `PR-TSC-10` |
| Q convention is explicit and regression-tested | `PR-TSC-04` |
| eta-source semantics do not invent false linear claims | `PR-TSC-03`, `PR-TSC-04` |
| BB / morphology / family-identification TSC-only claims are blocked | `PR-TSC-05`, `PR-TSC-09`, `PR-TSC-11` |
| BASS final runtime authority is preserved | `PR-TSC-06` |
| HTT posterior/evidence immutability is preserved | `PR-TSC-07` |
| MIO certificate stays diagnostic | `PR-TSC-08` |
| theorem-indexed artifact validation exists | `PR-TSC-10` |
| doc/manuscript wording stays synchronized with scope guard | `PR-TSC-11`, `PR-TSC-13` |

---

## 8. Current implementation reading

현재 코드베이스 관점에서는 다음이 이미 skeleton 또는 advisory-only 수준으로 시드되었다.

- shared-contract re-export and owner firewall
- chart-domain guard
- no-overclaim lint
- theorem-map skeleton
- overlay builder skeleton
- BASS / HTT / MIO advisory adapter surfaces

반면 아직 refined scope에서 남아 있는 핵심 확장:

- Fisher/Gram stat-mech kernel
- one-field / two-field projection geometry
- explicit Q convention registry
- theorem-backed `D_coll` / `D_state` / `Delta_obs` bridge
- atlas overlay integration
- full validation artifact package
- acceptance dashboard / result packs
- doc/manuscript sync automation

---

## 9. Near-term execution order

코드 시간 대비 효과가 가장 큰 순서는 refined companion의 권고를 따른다.

1. `PR-TSC3-01` contracts/schema firewall
2. `PR-TSC3-06` quadrupole convention registry
3. `PR-TSC3-07` exact Thomson trace-source bridge
4. `PR-TSC3-10` collision/state/observable residual bridge
5. `PR-TSC3-11` channel burden and claim ceiling
6. `PR-TSC3-13`, `PR-TSC3-14`, `PR-TSC3-15` downstream overlay adapters
7. `PR-TSC3-18` no-overclaim lint and doc patch gate
8. `PR-TSC3-19` acceptance dashboard and result packs

기존 umbrella packet 순서로 보면 다음에 해당한다.

1. `PR-TSC-00`
2. `PR-TSC-04`
3. `PR-TSC-05`
4. `PR-TSC-06`, `PR-TSC-07`, `PR-TSC-08`
5. `PR-TSC-11`
6. `PR-TSC-12`
7. `PR-TSC-13`

---

## 10. Reading order for future work

이 TSC lane을 다시 열 때는 다음 순서로 읽는다.

1. 이 root master plan
2. [teff_characteristics/TSC_active_service_SDD_WBS_PR_plan.md](teff_characteristics/TSC_active_service_SDD_WBS_PR_plan.md)
3. [teff_characteristics/TSC_active_service_SDD_WBS_PR_plan_v3_RE2_refined.md](teff_characteristics/TSC_active_service_SDD_WBS_PR_plan_v3_RE2_refined.md)
4. `teff_characteristics/00-09` source bundle

이 순서를 통해 기존 root reference stability를 유지하면서도, 실제 semantic expansion과 execution granularity는 `teff_characteristics` 문서군을 기준으로 따라갈 수 있다.

---

## 11. Final recommendation

TSC를 solver로 키우는 것이 아니라, stack 전체의 semantic/adequacy service로 더 강하게 연결하는 것이 맞다.

요약하면:

> BASS solves, HTT infers, MIO reports, TSC annotates/bounds/warns/guards.

이 구조가 SSoT를 유지하면서도 BASS/HTT/MIO/Atlas 전부에 실제 엔지니어링 가치를 제공한다.
