# TSC Active Service Upgrade v3 — RE2 재독 기반 SDD/WBS/PR 실행계획

**작성일**: 2026-04-20  
**대상 문서**: `TSC_active_service_SDD_WBS_PR_plan_v2_deepgrounded.md`의 정제본  
**추가 입력**: `00_README`–`09_patch_map` 10개 문서 + `teff_characteristics_statmech_foundation_v1.zip` 내부 6개 문서  
**목표**: TSC를 단순한 수학적 형식화/검증 모듈이 아니라, SSoT를 깨지 않으면서 BASS/HTT/MIO/Observable Atlas에 적극적으로 도움을 주는 **active trace-source adequacy service**로 승격한다.

---

## 0. 압축 결론

이번 정제의 핵심은 TSC의 역할을 다음처럼 다시 고정하는 것이다.


defensible:

\[
\boxed{
\mathrm{TSC}
=
\text{trace/intensity statistical chart}
+
\text{statistical-mechanical projection kernel}
+
\text{exact on-manifold trace-source bridge}
+
\text{diagnostic and adequacy overlay}
+
\text{claim-ceiling firewall}
}
\]

not defensible:

\[
\boxed{
\mathrm{TSC}
\neq
\text{full solver},
\quad
\mathrm{TSC}
\neq
\text{full polarisation closure},
\quad
\mathrm{TSC}
\neq
\text{BASS/HTT/MIO owner}
}
\]

`characteristics`는 더 이상 `full transport closure`라고 부르면 안 된다. 정확한 문장은 다음이다.

> Characteristics provides a closure-free full-state transport backbone/reference. Teff/TSC does not replace the transport law. It supplies a blockwise statistical chart, trace/intensity semantics, an exact source bridge where the relevant block is on-manifold, and diagnostics for reduced-block failure.

TSC가 능동적으로 해야 할 일은 “최종 판정”이 아니라 **증거를 구조화해서 다른 owner가 올바르게 판단하도록 만드는 것**이다.

- **BASS에는** trace-source adequacy, state/collision residual split, source-to-propagation warning, switch recommendation, channel burden metadata를 제공한다. 단, BASS의 final runtime allow/block은 침범하지 않는다.
- **HTT에는** likelihood/evidence/posterior를 바꾸지 않는 caveat overlay, model-result claim ceiling, trace-only vs full-covariance morphology 구분을 제공한다. 단, posterior/evidence owner는 HTT다.
- **MIO에는** `MioCertificate`에 들어갈 source adequacy, trace/spin-2/high residual caveat, diagnostic-only label을 제공한다. 단, MIO의 model-independent certificate를 truth certificate로 바꾸지 않는다.
- **Observable Atlas에는** `ObservableVector`/`AtlasEntryLite`마다 block responsibility와 theorem/validation coverage를 붙인다. 단, TSC가 BiPoSH/BB/Bianchi family identification을 수행했다고 주장하지 않는다.

이번 v3에서 v2 대비 크게 추가된 것은 네 가지다.

1. zip 내부 통계역학 foundation을 반영해 `StatMechKernel` 서비스를 추가한다. Fisher/Gram/entropy Hessian, Hilbert projection, one-field/two-field residual monotonicity, admissibility를 코드 객체로 만든다.
2. Paper V의 `Q` convention 오류를 재발하지 않도록 `QuadrupoleConvention` registry와 regression test를 PR 단위로 추가한다.
3. `D_coll`, `D_state`, `Delta_obs`를 타입 차원에서 분리하고, collision-side diagnostic을 observable adequacy로 자동 승격하지 못하게 한다.
4. validation을 “테스트가 돈다”가 아니라 theorem/PO/claim/status와 연결된 artifact package로 만든다.

---

## 1. RE2 재독 요약 — 외부 md 10개

아래 요약은 문서별 핵심 claim, TSC 설계에 내려오는 제약, v3 반영사항을 분리한다.

| 문서 | 짧은 요약 | TSC v3에 반영한 사항 |
|---|---|---|
| `00_README_index_and_source_boundaries.md` | 전체 시리즈의 source boundary 문서. Paper I–V에서 이미 주장 가능한 것, md synthesis claim, 아직 proof/validation obligation인 future program을 세 개의 원으로 분리한다. 핵심 correction은 `characteristics = closure-free transport backbone`, `Teff = trace/intensity reduced chart`, Paper V `Q` convention 고정이다. | TSC SDD 맨 앞에 source boundary를 둔다. TSC가 established result, synthesis, future validation을 한 상태로 섞지 못하도록 `ClaimStatus` enum을 도입한다. |
| `01_constitution_scope_and_claim_language.md` | 헌법 문장과 금지어를 제공한다. `full transport closure`, unqualified `full Boltzmann hierarchy solver`, `full polarisation closure` 같은 표현을 금지하고, trace/spin-2/high block ontology를 고정한다. | `no_overclaim` lint를 P0로 올린다. 모든 public artifact에 `block_scope={trace,spin2,high,mixed}`와 `claim_status`를 붙인다. |
| `02_papers_I_to_V_upgrade_ledger.md` | Paper I–III는 Teff manifold geometry/diagnostic, Paper IV는 observable semantics/local reconstructive adequacy, Paper V는 trace-intensity source bridge와 spin-2 independence를 세운다는 revised narrative를 제시한다. | TSC 결과를 Paper I–V 중 어느 정리 cluster에서 온 것인지 매핑한다. Paper V 기반 source bridge가 EE/BB propagation claim으로 승격되는 것을 차단한다. |
| `03_reduction_geometry_and_theorem_compendium.md` | parent kinetic structure, reduced manifold, projection, tangency diagnostic, entropy projection, two-field geometry, observable semantics, polarisation source, ambient/projected defect 구분을 재정렬한다. | `TscDefectReport`에서 ambient defect와 projected defect를 다른 필드로 저장한다. projected defect의 1차항이 0이라는 correction을 regression test로 만든다. |
| `04_characteristics_architecture_closure_free_backbone.md` | characteristics는 full-state transport reference이고 Teff는 selected trace/intensity sector에만 적용된다는 architecture를 고정한다. Minimal algorithmic loop와 TT/TE/EE/BB channel responsibility map을 제공한다. | TSC는 BASS loop의 full-state transport를 대체하지 않고, trace block extraction 이후의 source/diagnostic/admissibility service로만 들어간다. |
| `05_trace_intensity_semantics_and_polarisation_bridge.md` | polarised distribution matrix의 trace part와 traceless spin-2 part를 분리한다. Teff는 `I=tr P`에 적용되고, E/B hierarchy에는 적용되지 않는다. nonlinear Thomson trace-source bridge와 Q convention correction을 정리한다. | `TscSourceBridgeReport`에 `trace_source_exact_on_manifold`, `spin2_propagation_required`, `quadrupole_convention`을 필수 필드로 둔다. |
| `06_proof_obligations_and_claim_status.md` | theorem이 engineering claim을 자동으로 대신하지 않는다는 원칙을 세우고, PO-A/B/C/D/E/R와 claim levels E/C/S/V/F/X를 정리한다. Kill switches로 diagnostic-state mismatch, poor Jacobian conditioning, spin-2 contamination, characteristic convergence failure를 둔다. | `TheoremRegistry`, `ProofObligationRegistry`, `KillSwitchReason`을 만든다. `sigma_min(J)`와 state residual이 없으면 observable adequacy를 claim하지 못하게 한다. |
| `07_validation_protocol_and_test_matrix.md` | validation을 Layer A full characteristic transport, Layer B Teff adequacy, Layer C observable/spectrum adequacy, Layer R realizability/switching robustness로 나눈다. 모든 test는 config, metrics, summary, log, figure, passfail artifact를 남겨야 한다. | `TscValidationArtifactSet`을 도입하고, TSC validation dashboard가 standard metric keys를 강제한다. |
| `08_red_team_reviewer_defense.md` | reviewer objections와 방어 가능한 답변을 정리한다. collision diagnostic이 observables를 직접 control하지 못함, Paper V가 polarisation solver가 아님, novelty 과장 금지, on-manifold exactness의 한계를 명시한다. | PR마다 red-team acceptance question을 붙인다. TSC가 hidden owner가 되거나 trace source adequacy를 full observable adequacy로 바꾸면 PR fail. |
| `09_patch_map_for_existing_md_and_manuscripts.md` | 기존 md/원고의 find/replace 및 manual rewrite map. `closure`, `full solver`, `Paper V Q convention`, validation docs patch를 구체화한다. | `docs_lint`와 `claim_language_patch_report`를 PR-TSC-18로 추가한다. 문서와 코드 contract가 같은 claim language를 쓰게 한다. |

---

## 2. RE2 재독 요약 — zip 내부 문서 6개

zip 파일 `teff_characteristics_statmech_foundation_v1.zip` 내부에는 다음 6개 문서가 있었다.

| 내부 파일 | 짧은 요약 | TSC v3에 반영한 사항 |
|---|---|---|
| `00_README.md` | statistical-mechanical foundation 묶음의 index. 핵심 결론은 characteristics가 closure가 아니고, Teff는 trace/intensity block chart/source bridge/diagnostic이라는 것. Fisher weight, entropy Hessian, tangency projection kernel이 같은 구조에서 나온다는 점과 Paper V Q convention 수정 필요성을 강조한다. | `StatMechKernel`을 새 P0/P1 service로 올린다. Fisher/Gram/projection을 단순 수식 문서가 아니라 TSC residual 계산의 표준 backend로 둔다. |
| `01_draft_statmech_formalization.md` | 기본 상태공간, 통계역학 구조, entropy Hessian, tangency diagnostic, characteristics, defect, observable bridge, Thomson source의 초안을 잡는다. | v3 문서에서는 draft 내용 자체보다 final/audit에서 살아남은 구조만 채택한다. Draft-only claim은 `draft_or_superseded`로 표기한다. |
| `02_audit_report_calculation_and_claims.md` | 통계 부호, entropy Hessian, Hilbert projection, characteristics terminology, ambient/projected defect, observable bound, Paper V axisymmetric quadrupole, eta-dipole correction을 감사한다. 안전한 claim과 제거해야 할 claim을 나눈다. | `QuadrupoleConvention`, `EtaSourceSemantics`, `DefectType`를 contract에 추가한다. `dominates` 같은 과장어는 convention/parameter 조건 없이는 금지한다. |
| `03_final_theoretical_foundation.md` | 정의–가정–정리–증명 순서로 최종 이론 foundation을 제시한다. closure-free characteristics theorem, one/two-field Teff families, Fisher Hilbert space, Gram–Hessian identity, tangency biconditional, Pythagorean monotonicity, conditional entropy projection, ambient/projected defect, conditional observable reconstruction bound, Thomson source bridge, Q convention, eta-dipole theorem을 포함한다. | TSC의 수학 kernel을 이 문서 기준으로 만든다. 특히 `D_coll`과 `D_state`, `sigma_min(J)`, `Theta>0`, BE domain, state-side high-mode residual이 없는 경우의 no-claim rule을 넣는다. |
| `04_survival_revision_ledger.md` | 살아남는 claim, 수정 후 살아남는 claim, 제거해야 하는 claim, 필수 manuscript patch를 정리한다. Paper IV bound는 state residual, Jacobian conditioning, local regularity 조건이 필요하고, Paper V는 trace source semantics만 제공한다고 강조한다. | PR acceptance criteria에 “survival ledger compliance” 항목을 넣는다. 각 result card에 `survives_as`, `conditional_on`, `forbidden_upgrade`를 남긴다. |
| `05_axisymmetric_quadrupole_symbolic_check.md` | axisymmetric ansatz의 두 convention을 계산으로 확인한다. `theta=A mu+Q_mu(mu^2-1/3)`와 `theta=A mu+qP_2(mu)` 사이의 변환 및 Paper V 숫자 재현을 제공한다. | `test_quadrupole_convention_regression.py`를 별도 PR gate로 추가한다. 모든 Paper V source bridge artifact에는 convention tag가 필수다. |

---

## 3. v2 문서에 대한 핵심 교정점

### 3.1 `closure` 언어의 완전 제거

v2에도 대부분 반영되어 있었지만, 일부 문장에는 `characteristics = full closure`처럼 읽힐 수 있는 흔적이 있었다. v3에서는 다음 규칙을 강제한다.

금지:

```text
characteristics is the full transport closure
characteristics completes the full Boltzmann hierarchy solver
Teff closes polarisation
TSC validates BB from trace semantics
```

허용:

```text
characteristics provides a closure-free full-state transport backbone/reference
Teff/TSC supplies a blockwise trace/intensity statistical chart and source semantics
spin-2 polarisation remains independently transported or validated
```

### 3.2 TSC의 능동성은 owner 권한이 아니라 evidence service다

TSC가 적극적으로 도움을 준다는 말은 “BASS/HTT/MIO 대신 판단한다”가 아니다. 정확한 설계는 다음이다.

\[
\text{TSC output}
\longrightarrow
\text{owner policy consumes it}
\longrightarrow
\text{owner emits final claim/status}.
\]

따라서 TSC output은 다음 상태 중 하나여야 한다.

- `evidence`: owner가 사용할 수 있는 수치/진단량.
- `warning`: owner가 claim ceiling을 낮출 때 사용할 caveat.
- `recommendation`: switch 또는 upgrade 제안. 자동 실행 금지.
- `quarantine`: TSC contract상 public claim으로 올리면 안 되는 결과.

### 3.3 TSC에 새로 들어오는 statistical-mechanical kernel

기존 v2는 source adequacy service는 있었지만, Fisher/Gram/entropy Hessian 구조가 code-level service로 충분히 내려가지 않았다. v3에서는 다음을 TSC core로 추가한다.

\[
W_{\xi,p}=f(1+\xi f)x^p,
\qquad
\langle a,b\rangle_*=\int_0^\infty a(x)b(x)W_{\xi,p}(x)dx.
\]

\[
G_{ij}=\langle v_i,v_j\rangle_* ,
\qquad
\delta^2S_\xi=-a^TG a.
\]

\[
D_V=\|G_\xi-\Pi_VG_\xi\|_*.
\]

이 kernel은 다음 service를 제공한다.

- `gram_matrix(statistics, theta, eta, p)`
- `entropy_hessian_metric(...)`
- `project_to_tangent(collision_source, tangent_basis)`
- `diagnostic_norm(D_coll)`
- `one_to_twofield_residual_split()`
- `conditioning_report(sigma_min_G, sigma_min_J)`

### 3.4 `D_coll`, `D_state`, `Delta_obs`의 타입 분리

가장 위험한 혼동은 collision-side diagnostic을 observable error로 직접 읽는 것이다.

v3에서는 다음 타입을 분리한다.

\[
D_{\ge2}^{\rm coll}:
\text{collision/source field residual},
\]

\[
D_{\ge2}^{\rm state}:
\text{state residual relative to reduced manifold},
\]

\[
\Delta_{\rm obs}:
\text{observable reconstruction/spectrum error}.
\]

허용되는 bridge는 조건부다.

\[
\Delta_{\rm obs}
\le
\frac{C_{\rm loc}}{\sigma_{\min}(J)}D_{\ge2}^{\rm state}
+O((D_{\ge2}^{\rm state})^2).
\]

`D_coll`에서 `D_state`로 가려면 별도 dynamical accumulation bridge 또는 numerical validation이 필요하다.

### 3.5 Paper V `Q` convention은 코드 contract로 고정

두 convention을 동시에 쓰면 숫자가 무너진다.

Convention A:

\[
\Theta(\mu)=1+A\mu+Q_\mu(\mu^2-1/3).
\]

Convention B:

\[
\Theta(\mu)=1+A\mu+qP_2(\mu),
\qquad
q=\frac{2}{3}Q_\mu.
\]

v3에서는 모든 source bridge output에 다음 필드를 필수화한다.

```python
quadrupole_convention: Literal[
    "mu2_minus_one_third",  # Q_mu
    "legendre_P2"           # q
]
quadrupole_parameter_name: Literal["Q_mu", "q"]
conversion_to_legendre_q: float
```

### 3.6 eta-dipole는 source semantics에서 조심스럽게 처리

zip final foundation의 결론에 따르면 pure \(\eta\)-dipole은 intensity quadrupole에 선형으로 기여하지 않고, dipole-only sector에서는 2차부터 기여한다.

따라서 TSC는 다음 warning을 발행해야 한다.

- `eta_dipole_linear_quadrupole_absent`
- `eta_quadrupole_needed_for_linear_eta_source`
- `eta_degenerate_fd_unproved_if_eta_positive`
- `be_domain_requires_z_positive`

---

## 4. SSoT-preserving target architecture

### 4.1 Architecture one-liner

> TSC is an active trace-source adequacy service. It computes statistical-mechanical projection diagnostics, exact on-manifold trace-source bridges, channel burden annotations, and claim-ceiling overlays, while leaving full transport, posterior inference, and model-independent certificates to their canonical owners.

### 4.2 Owner boundary table

| Capability | BASS | HTT | MIO | TSC |
|---|---:|---:|---:|---:|
| closure-free full-state / low-\(\ell\) transport reference | owner | consumes | consumes | no |
| final runtime allow/block | owner | no | no | no; recommendation only |
| posterior/evidence/Bayes factor | no | owner | no | no; caveat only |
| model-independent diagnostic certificate | no | no | owner | supplies adequacy overlay |
| trace/intensity Teff chart | consumes | consumes | consumes | owner |
| Fisher/Gram/entropy projection kernel | consumes | consumes | consumes | owner |
| exact on-manifold trace-source bridge | consumes | consumes | consumes | owner |
| spin-2 propagation | BASS/full solver path | may consume | may report caveat | no |
| BB/BiPoSH/Bianchi family identification | BASS/HTT/MIO validated path | owner where model-dependent | diagnostic only | no |
| claim-language lint | consumes | consumes | consumes | service owner |

### 4.3 TSC service graph

```text
Resolved or reduced trace block
        |
        v
[TSC DomainGuard] -- fail --> quarantine/admissibility error
        |
        v
[StatMechKernel: Fisher/Gram/projection]
        |
        +--> D_coll report
        +--> one/two-field split
        +--> conditioning report
        |
        v
[StateResidualBridge] -- if D_state unavailable --> no observable adequacy claim
        |
        v
[TraceSourceBridge: nonlinear Thomson / Q convention / eta semantics]
        |
        v
[ChannelBurdenBudget: TT/TE/EE/BB trace-spin2-high split]
        |
        v
[TscAdequacyOverlay]
        |
        +--> BASS RuntimeReport overlay
        +--> HTT InferenceResult caveat overlay
        +--> MIO Certificate caveat overlay
        +--> Observable Atlas metadata
```

---

## 5. Core contracts

### 5.1 Enumerations

```python
from enum import Enum

class ClaimStatus(str, Enum):
    ESTABLISHED = "E"       # current manuscripts establish the statement
    CONDITIONAL = "C"       # theorem under hypotheses
    SYNTHESIS = "S"         # architecture-level synthesis
    VALIDATION = "V"        # numerical validation obligation
    FUTURE = "F"            # future theorem/programmatic
    FORBIDDEN = "X"         # forbidden as written

class BlockScope(str, Enum):
    TRACE = "trace"
    SPIN2 = "spin2"
    HIGH = "high"
    MIXED = "mixed"

class ResidualKind(str, Enum):
    COLLISION_SIDE = "D_coll"
    STATE_SIDE = "D_state"
    OBSERVABLE = "Delta_obs"

class DefectKind(str, Enum):
    AMBIENT = "ambient"       # first derivative Q_g G(g)
    PROJECTED = "projected"   # first derivative zero

class QuadrupoleConvention(str, Enum):
    MU2_MINUS_ONE_THIRD = "mu2_minus_one_third"  # Q_mu
    LEGENDRE_P2 = "legendre_P2"                  # q

class Owner(str, Enum):
    BASS = "BASS"
    HTT = "HTT"
    MIO = "MIO"
    TSC = "TSC"
    COMMON = "COMMON"
```

### 5.2 `TscStatMechState`

```python
@dataclass(frozen=True)
class TscStatMechState:
    statistics: Literal["MB", "FD", "BE"]
    xi: int                       # 0, -1, +1
    moment_weight_p: int          # p=3 intensity, p=2 number
    theta_min: float
    eta_max: float | None
    admissible: bool
    admissibility_caveats: tuple[str, ...]
    proven_domain_status: ClaimStatus
```

### 5.3 `TscProjectionReport`

```python
@dataclass(frozen=True)
class TscProjectionReport:
    basis_name: str
    gram_condition_number: float
    sigma_min_gram: float
    d_coll_onefield: float | None
    d_coll_twofield: float | None
    residual_monotonicity_holds: bool
    eta_tangent_component_norm: float | None
    high_energy_residual_norm: float | None
    claim_status: ClaimStatus
```

### 5.4 `TscResidualBridgeReport`

```python
@dataclass(frozen=True)
class TscResidualBridgeReport:
    d_coll: float | None
    d_state: float | None
    delta_obs: float | None
    sigma_min_J: float | None
    c_loc: float | None
    bridge_status: Literal[
        "not_attempted",
        "state_residual_bound_available",
        "dynamical_accumulation_validated",
        "blocked_collision_state_mismatch",
    ]
    no_claim_reasons: tuple[str, ...]
```

### 5.5 `TscDefectReport`

```python
@dataclass(frozen=True)
class TscDefectReport:
    defect_kind: DefectKind
    ambient_first_derivative_norm: float | None
    projected_first_derivative_norm: float | None
    expected_projected_first_derivative_zero: bool
    numerical_tolerance: float
    passfail: Literal["PASS", "WARN", "FAIL"]
```

### 5.6 `TscSourceBridgeReport`

```python
@dataclass(frozen=True)
class TscSourceBridgeReport:
    trace_on_manifold: bool
    theta4_quadrupole_value: float | dict[str, float]
    linear_quadrupole_value: float | dict[str, float]
    nonlinear_enhancement_ratio: float | None
    quadrupole_convention: QuadrupoleConvention
    q_mu: float | None
    q_legendre: float | None
    eta_source_semantics: dict[str, str]
    exact_on_manifold: bool
    spin2_propagation_required: bool
    claim_status: ClaimStatus
```

### 5.7 `TscChannelAdequacyBudget`

```python
@dataclass(frozen=True)
class TscChannelAdequacyBudget:
    channel: Literal["TT", "TE", "EE", "BB", "BiPoSH", "template"]
    trace_burden: float | None
    spin2_burden: float | None
    high_residual_burden: float | None
    source_adequacy: Literal["adequate", "marginal", "inadequate", "unknown"]
    propagation_adequacy: Literal["adequate", "marginal", "inadequate", "unknown"]
    claim_ceiling: ClaimStatus
    public_claim_allowed: bool
    caveats: tuple[str, ...]
```

### 5.8 `TscSwitchRecommendation`

```python
@dataclass(frozen=True)
class TscSwitchRecommendation:
    recommended_action: Literal[
        "stay_onefield",
        "upgrade_twofield",
        "upgrade_resolved_trace",
        "full_spin2_required",
        "quarantine_result",
    ]
    reason_codes: tuple[str, ...]
    hysteresis_passed: bool
    min_dwell_time: float | None
    owner_must_decide: Owner
```

### 5.9 `TscAdequacyOverlay`

```python
@dataclass(frozen=True)
class TscAdequacyOverlay:
    overlay_schema_version: str
    source_documents_hash: str
    statmech_state: TscStatMechState
    projection_report: TscProjectionReport | None
    residual_bridge: TscResidualBridgeReport | None
    defect_report: TscDefectReport | None
    source_bridge: TscSourceBridgeReport | None
    channel_budgets: tuple[TscChannelAdequacyBudget, ...]
    switch_recommendation: TscSwitchRecommendation | None
    no_overclaim_flags: tuple[str, ...]
    owner_boundary_flags: tuple[str, ...]
```

---

## 6. Channel responsibility map

TSC must always report channel responsibility in this form.

| Channel/result | What TSC can certify | What TSC cannot certify | Default claim ceiling |
|---|---|---|---|
| TT trace/intensity source | trace chart admissibility, nonlinear intensity source bridge, state residual condition if available | full sky fit, CMB likelihood, Bianchi geometry identification | Conditional or validation-backed |
| TE | trace source side plus caveat that E propagation is independent | TE spectrum adequacy without spin-2 propagation validation | Validation obligation |
| EE | source contribution to E from intensity quadrupole, if spin-2 path is separately validated | final EE adequacy from trace alone | Validation obligation |
| BB | no trace-only adequacy; can flag full spin-2 necessity | BB prediction/control | Forbidden as trace-only |
| BiPoSH/off-diagonal covariance | can label trace-source contribution and claim ceiling | morphology/family identification | Forbidden unless BASS/HTT/MIO validated path supplies it |
| HTT posterior/evidence | caveat overlay only | posterior correction or evidence owner role | HTT-owned |
| MIO certificate | adequacy/caveat fields | truth certificate or model selection | MIO-owned |

---

## 7. BASS/HTT/MIO interaction model

### 7.1 BASS interaction

BASS owns transport, runtime decision, and final validation labels. TSC helps BASS by supplying:

1. `TscStatMechState`: admissibility and proven-domain status.
2. `TscProjectionReport`: one-field/two-field residual split.
3. `TscResidualBridgeReport`: state/collision residual separation.
4. `TscSourceBridgeReport`: exact on-manifold trace-source quadrupole with convention tags.
5. `TscSwitchRecommendation`: upgrade advice only.
6. `TscChannelAdequacyBudget`: channel burden metadata.

BASS consumes but does not delegate:

```text
BASS canonical runtime decision = BASS policy(TSC overlay, BASS transport metrics, BASS validation metrics)
```

TSC may never write:

```python
allow_reduction = True
validation_label = "production_validated"
```

TSC may write:

```python
recommended_action = "upgrade_twofield"
reason_codes = ("onefield_eta_false_trigger", "d_coll_reduced_by_twofield")
owner_must_decide = Owner.BASS
```

### 7.2 HTT interaction

HTT owns model-dependent likelihood, posterior, evidence, null competition, PPC/LOOCV. TSC helps HTT by attaching caveats to model outputs.

Examples:

- `htt_result.tsc_overlay.channel_budgets["TE"].claim_ceiling = "V"`
- `htt_result.tsc_overlay.no_overclaim_flags += ("trace_source_only_not_spin2_propagation",)`
- `htt_result.public_claim = min(htt_policy_claim, tsc_claim_ceiling)`

But TSC must not modify:

- posterior samples,
- log evidence,
- Bayes factors,
- nuisance marginalisation,
- model ranking.

If HTT chooses to use TSC caveats to exclude a model in a policy run, that exclusion must be performed by HTT and logged as `htt_policy_exclusion_using_tsc_caveat`, not as a TSC decision.

### 7.3 MIO interaction

MIO owns model-independent diagnostic certificates. TSC helps MIO by providing block and adequacy metadata.

Useful fields in `MioCertificate`:

```python
source_adequacy = overlay.source_bridge.exact_on_manifold
state_residual_available = overlay.residual_bridge.d_state is not None
spin2_required = any(b.spin2_burden for b in overlay.channel_budgets)
reduction_status = "diagnostic_only" | "source_validated" | "observable_validated"
```

MIO must not convert TSC overlay into:

- truth certificate,
- model posterior,
- Bianchi family selection,
- final production gate.

### 7.4 Observable Atlas interaction

Every `AtlasEntryLite` or `ObservableVector` should carry:

```python
tsc_overlay_id: str | None
block_scope: BlockScope
claim_status: ClaimStatus
source_bridge_status: str
spin2_burden_status: str
validation_layer_coverage: tuple["A"|"B"|"C"|"R", ...]
```

This lets the atlas distinguish:

- scalar trace amplitude result,
- trace-source result inside polarised transfer,
- full spin-2 observable result,
- direction-inclusive morphology result.

---

## 8. Validation and artifact policy

### 8.1 Mandatory artifact package

Every serious TSC validation test emits:

```text
config_<test-id>.yaml
metrics_<test-id>.json
summary_<test-id>.md
log_<test-id>.txt
figures_<test-id>/...
passfail_<test-id>.json
```

Standard metric keys:

```text
runtime_sec
max_memory_mb
state_l2_error
observable_error
spectrum_error
trace_residual
spin2_residual
high_residual
theta_min
eta_max
switch_count
min_dwell_time
status
claim_status
owner_boundary_flags
```

### 8.2 Validation layer mapping

| Layer | Meaning | TSC role |
|---|---|---|
| A | closure-free characteristic/full transport correctness | consume BASS reference metrics; cannot certify alone |
| B | reduced-block Teff adequacy | primary TSC validation layer |
| C | observable/spectrum adequacy | only conditional; requires BASS/HTT/MIO observable references |
| R | realizability/switching robustness | TSC supplies guards and switch recommendations; owner executes |

### 8.3 Minimum campaign order

1. `B4` Q convention regression.
2. `B1` one-field vs two-field false-trigger test.
3. `B2` trace source adequacy test.
4. `B3` spin-2 invisibility test.
5. `R1/R2` admissibility boundary tests.
6. `R3` no-chattering switch test.
7. `C1` TT adequacy with state residual.
8. `C4` TE mixed adequacy.
9. `C3` BB full-spin-2 necessity demonstration.

---

## 9. 적대적 감사와 정제 결과

### Attack 1 — “TSC가 hidden BASS runtime owner가 됐다.”

**위험**: switch recommendation이 사실상 automatic allow/block으로 쓰임.  
**정제**: 모든 recommendation에는 `owner_must_decide` 필드가 있고, BASS adapter는 BASS runtime decision object를 수정하지 않고 overlay만 반환한다.

### Attack 2 — “collision diagnostic을 observable error로 팔고 있다.”

**위험**: `D_coll`이 작다는 이유만으로 TT/TE/EE adequacy claim.  
**정제**: `TscResidualBridgeReport`에서 `D_state`가 없으면 `Delta_obs`는 `None`이고 `bridge_status=blocked_collision_state_mismatch`다.

### Attack 3 — “Paper V source bridge가 polarisation solver처럼 읽힌다.”

**위험**: intensity quadrupole source bridge를 EE/BB prediction으로 승격.  
**정제**: `spin2_propagation_required=True`를 source bridge report의 필수 필드로 둔다. BB channel은 trace-only면 `public_claim_allowed=False`.

### Attack 4 — “Q convention이 다시 섞인다.”

**위험**: `Q` 하나로 `P_2` coefficient와 `mu^2-1/3` coefficient를 혼용.  
**정제**: `QuadrupoleConvention` 없는 source artifact는 validation fail. Worked point \((A,Q_\mu)=(0.30,0.15)\) regression을 필수화한다.

### Attack 5 — “TSC가 HTT posterior를 조용히 바꾼다.”

**위험**: caveat overlay가 likelihood weighting처럼 작동.  
**정제**: HTT adapter는 posterior/evidence fields를 immutable로 받고, overlay-only object를 별도로 반환한다.

### Attack 6 — “MIO certificate가 truth certificate로 변한다.”

**위험**: MIO가 TSC adequacy를 model truth로 해석.  
**정제**: MIO adapter output에는 `diagnostic_report_not_truth_certificate=True`가 강제된다.

### Attack 7 — “active service가 너무 커져 단기 결과를 늦춘다.”

**위험**: TSC가 별도 full subsystem으로 비대해짐.  
**정제**: P0는 contracts, convention registry, source bridge, channel budget, overlays만 구현한다. Fisher kernel과 validation dashboard는 P1로 가되 interface는 P0에서 freeze한다.

### Attack 8 — “statistical-mechanical theorem이 production solver adequacy로 과장된다.”

**위험**: Gram–Hessian identity 또는 projection theorem을 global solver theorem처럼 소개.  
**정제**: 모든 theorem registry entry는 `establishes`, `requires`, `does_not_establish` 세 필드를 가진다.

---

## 10. SDD 기반 WBS

### Wave 0 — Source-grounded SDD and claim language freeze

목표: v3 문서 시리즈와 zip foundation을 SDD source of truth로 연결한다.

Deliverables:

- `docs/tsc/SDD_TSC_active_service_v3.md`
- `docs/tsc/source_summary_RE2.md`
- `docs/tsc/claim_language_firewall.md`
- `src/tsc/contracts.py`

Exit criteria:

- forbidden phrase scanner 통과.
- 모든 contract가 owner boundary를 명시.
- source documents hash가 artifact manifest에 저장.

### Wave 1 — Contracts and theorem registry

목표: claim status, proof obligations, validation layers, theorem-to-test mapping을 코드 객체로 만든다.

Deliverables:

- `src/tsc/ontology/claim_status.py`
- `src/tsc/ontology/theorem_registry.py`
- `src/tsc/ontology/proof_obligation_registry.py`
- `src/tsc/ontology/validation_registry.py`

Exit criteria:

- 각 public TSC output이 theorem/PO/validation link를 가짐.
- `FORBIDDEN` claim은 artifact promotion 불가.

### Wave 2 — Statistical-mechanical kernel

목표: Fisher Hilbert, Gram–Hessian, tangent projection, residual norm을 구현한다.

Deliverables:

- `src/tsc/statmech/fisher_weight.py`
- `src/tsc/statmech/gram_hessian.py`
- `src/tsc/statmech/tangent_projection.py`
- `src/tsc/statmech/residual_monotonicity.py`

Exit criteria:

- Gram positive-definiteness tests pass on admissible regimes.
- one-field residual ≥ two-field residual regression pass.
- inadmissible BE/Theta inputs are rejected.

### Wave 3 — Convention and trace-source bridge

목표: Paper V source bridge와 Q convention을 안전하게 production metadata로 내린다.

Deliverables:

- `src/tsc/source/quadrupole_conventions.py`
- `src/tsc/source/thomson_trace_bridge.py`
- `src/tsc/source/eta_source_semantics.py`
- `tests/tsc/test_quadrupole_convention_regression.py`

Exit criteria:

- \((A,Q_\mu)=(0.30,0.15)\) nonlinear quadrupole 0.842140... and linear 0.400 regression pass.
- source bridge artifact without convention tag fails.

### Wave 4 — Residual and defect semantics

목표: ambient/projected defect, collision/state/observable residual split을 타입 차원에서 분리한다.

Deliverables:

- `src/tsc/defects/ambient_projected.py`
- `src/tsc/residuals/collision_state_split.py`
- `src/tsc/residuals/observable_bridge.py`

Exit criteria:

- projected defect first derivative zero test pass.
- collision residual cannot populate observable error field without bridge.

### Wave 5 — Channel burden and switch advisor

목표: TT/TE/EE/BB/BiPoSH/template channel마다 trace/spin2/high burden과 claim ceiling을 산출한다.

Deliverables:

- `src/tsc/adequacy/channel_budget.py`
- `src/tsc/control/switch_advisor.py`
- `src/tsc/control/hysteresis.py`

Exit criteria:

- BB trace-only result is blocked.
- TE mixed burden is labelled mixed.
- switch recommendation never mutates owner state.

### Wave 6 — BASS/HTT/MIO/Atlas adapters

목표: owner를 침범하지 않는 overlay-only integration을 만든다.

Deliverables:

- `src/tsc/adapters/bass_overlay.py`
- `src/tsc/adapters/htt_overlay.py`
- `src/tsc/adapters/mio_overlay.py`
- `src/tsc/adapters/atlas_overlay.py`

Exit criteria:

- BASS runtime decision immutable in tests.
- HTT posterior/evidence immutable in tests.
- MIO certificate remains diagnostic, not truth certificate.

### Wave 7 — Validation runbook and dashboard

목표: theorem-indexed validation artifacts and coverage dashboard.

Deliverables:

- `src/tsc/validation/artifact_set.py`
- `src/tsc/validation/test_matrix.py`
- `src/tsc/validation/passfail_policy.py`
- `src/tsc/reports/validation_dashboard.py`

Exit criteria:

- every validation run emits mandatory files.
- dashboard shows Layer A/B/C/R coverage separately.

### Wave 8 — Red-team lint and manuscript patch support

목표: claim-language consistency를 코드와 문서 양쪽에서 강제한다.

Deliverables:

- `src/tsc/audit/no_overclaim.py`
- `src/tsc/audit/doc_patch_lint.py`
- `docs/tsc/manuscript_patch_map_TSC_v3.md`

Exit criteria:

- forbidden phrase scanner catches closure/full solver/polarisation closure misuse.
- source bridge claims include trace-only caveat.

### Wave 9 — Result packs

목표: 단기 novelty 결과를 생성한다.

Result packs:

1. Trace-source adequacy dashboard.
2. Channel responsibility map.
3. One-field/two-field false-trigger map.
4. HTT/MIO caveat-enriched report cards.
5. Validation theorem coverage dashboard.

---

## 11. PR dependency graph

```text
PR-TSC3-00  SDD/source summaries/claim freeze
   |
PR-TSC3-01  contracts/schema
   |
PR-TSC3-02  theorem/PO/validation registry
   |\
   | PR-TSC3-03  statmech kernel
   |       |\
   |       | PR-TSC3-04 one/two-field projection residual
   |       | PR-TSC3-05 admissibility/domain guard
   |
PR-TSC3-06  Q convention registry
   |
PR-TSC3-07  nonlinear Thomson trace-source bridge
   |
PR-TSC3-08  eta source semantics
   |
PR-TSC3-09  ambient/projected defect service
   |
PR-TSC3-10  residual bridge D_coll/D_state/Delta_obs
   |
PR-TSC3-11  channel burden budget
   |
PR-TSC3-12  switch advisor
   |
PR-TSC3-13  BASS overlay
PR-TSC3-14  HTT overlay
PR-TSC3-15  MIO overlay
PR-TSC3-16  Atlas overlay
   |
PR-TSC3-17  validation artifact set
PR-TSC3-18  red-team and doc lint
   |
PR-TSC3-19  acceptance dashboard and result packs
PR-TSC3-20  manuscript/SDD sync
```

---

## 12. Detailed PR list

## PR-TSC3-00 — Source-grounded SDD v3 and RE2 summary ledger

### Goal

Rebuild the v2 plan into a v3 SDD that explicitly incorporates the 10 external md documents and 6 zip-internal documents.

### SDD delta

- Add source-summary section.
- Replace all closure language with closure-free backbone language.
- Add survival/revision ledger compliance.
- Define owner boundaries before module design.

### Files

```text
docs/tsc/SDD_TSC_active_service_v3.md
docs/tsc/source_summary_RE2.md
docs/tsc/source_hashes.json
```

### WBS

1. Record source filenames and hashes.
2. Add one-paragraph RE2 summary for every source.
3. Extract mandatory constraints.
4. Mark superseded claims.
5. Freeze v3 architecture one-liner.

### Tests

- `test_source_hashes_present`
- `test_forbidden_closure_language_absent`
- `test_all_sources_have_summary`

### Definition of done

Every source document is summarized and each major design rule points back to at least one source cluster.

### Rollback / kill criterion

Rollback if the SDD still contains `characteristics = closure` or if zip-internal Q convention corrections are absent.

---

## PR-TSC3-01 — Contracts, schema versioning, and owner firewall

### Goal

Create the core dataclasses and enums used by all later PRs.

### SDD delta

- Add `ClaimStatus`, `BlockScope`, `ResidualKind`, `DefectKind`, `QuadrupoleConvention`, `Owner`.
- Add immutable overlay objects.
- Add schema version and source document hash fields.

### Files

```text
src/tsc/contracts.py
src/tsc/schema.py
tests/tsc/test_contracts.py
```

### WBS

1. Implement enums.
2. Implement `TscAdequacyOverlay` and subreports.
3. Add serialization/deserialization.
4. Add immutability tests.
5. Add backward-compatibility note.

### Tests

- Round-trip JSON serialization.
- Immutable owner fields.
- Reject missing `claim_status` and `block_scope`.

### Definition of done

A TSC overlay can be attached to external objects without modifying their owner-owned fields.

---

## PR-TSC3-02 — Theorem, proof-obligation, validation, and claim registry

### Goal

Encode theorem/claim status and proof-obligation mapping so TSC outputs are always claim-scoped.

### SDD delta

- `TheoremEntry(establishes, requires, does_not_establish)`.
- PO-A/B/C/D/E/R registry.
- Layer A/B/C/R validation registry.

### Files

```text
src/tsc/ontology/theorem_registry.py
src/tsc/ontology/proof_obligation_registry.py
src/tsc/ontology/validation_registry.py
docs/tsc/theorem_to_claim_map.md
tests/tsc/test_theorem_registry.py
```

### WBS

1. Encode Paper I–V theorem clusters.
2. Encode zip final foundation theorem clusters.
3. Encode claim status levels.
4. Map each channel to needed obligations.
5. Add no-claim checks.

### Tests

- `test_forbidden_claim_not_promotable`
- `test_bb_trace_claim_forbidden`
- `test_observable_claim_requires_state_residual_and_validation`

### Definition of done

Every TSC report can state what it establishes and what it does not establish.

---

## PR-TSC3-03 — Statistical-mechanical Fisher/Gram kernel

### Goal

Implement the Fisher Hilbert space and Gram–Hessian kernel used by tangency diagnostics.

### SDD delta

- Add `W_xi_p=f(1+xi f)x^p`.
- Add tangent generators `v_theta=x/theta^2`, `v_eta=1`.
- Add Gram matrix and entropy Hessian identity check.

### Files

```text
src/tsc/statmech/fisher_weight.py
src/tsc/statmech/gram_hessian.py
src/tsc/statmech/quadrature.py
tests/tsc/statmech/test_gram_hessian.py
```

### WBS

1. Implement statistics sign convention.
2. Implement admissible distribution evaluators.
3. Implement weighted quadrature.
4. Implement Gram matrix.
5. Implement positive-definite checks.

### Tests

- MB/FD/BE admissible positivity.
- Gram symmetric positive definite for linearly independent tangent generators.
- Entropy second variation equals `-a^T G a` numerically.

### Definition of done

TSC can compute statistical metric and conditioning for one-field and two-field trace charts.

### Rollback / kill criterion

Kill if BE admissibility or FD proven-domain caveats are ignored.

---

## PR-TSC3-04 — Tangency projection and one/two-field residual monotonicity

### Goal

Compute projection residuals and quantify false triggers removed by two-field extension.

### SDD delta

- Implement Hilbert projection.
- Implement `D_coll_onefield`, `D_coll_twofield`.
- Implement Pythagorean residual decomposition.

### Files

```text
src/tsc/statmech/tangent_projection.py
src/tsc/charts/twofield_decomposition.py
tests/tsc/statmech/test_projection_residuals.py
```

### WBS

1. Implement finite-dimensional projection.
2. Compute residual norm.
3. Decompose one-field residual into eta-tangent and high residual.
4. Add monotonicity test `D_two <= D_one`.
5. Emit `TscProjectionReport`.

### Tests

- Exact tangent source gives residual zero.
- Constant energy mode is obstruction for one-field and tangent for enlarged per-ray family.
- Two-field residual never exceeds one-field residual within tolerance.

### Definition of done

TSC can tell BASS/HTT/MIO when a one-field failure is actually an eta-degree false trigger.

---

## PR-TSC3-05 — Domain, admissibility, and realizability guard

### Goal

Enforce \(\Theta>0\), statistical admissibility, and current proven-domain restrictions.

### SDD delta

- Add `DomainGuard` for MB/FD/BE.
- Add proven-domain caveat for degenerate FD extension.
- Add `theta_min`, `eta_max`, `z_min` metrics.

### Files

```text
src/tsc/admissibility/domain.py
src/tsc/admissibility/realizability_guard.py
tests/tsc/test_domain_guard.py
```

### WBS

1. Implement theta positivity.
2. Implement `f>0`, `1+xi f>0` checks.
3. Implement BE `z>0` grid/quadrature check.
4. Implement FD positive-eta caveat.
5. Export `TscStatMechState`.

### Tests

- Reject nonpositive theta.
- Reject BE domain violation.
- Mark FD degenerate regime as conditional/future unless explicitly enabled.

### Definition of done

No TSC source bridge or projection report can be generated outside declared domain without caveats.

---

## PR-TSC3-06 — Quadrupole convention registry and regression tests

### Goal

Prevent Paper V Q-normalization mistakes from reappearing.

### SDD delta

- Introduce canonical convention registry.
- Require convention tags in source bridge outputs.
- Add symbolic/numerical regression.

### Files

```text
src/tsc/source/quadrupole_conventions.py
tests/tsc/source/test_quadrupole_conventions.py
docs/tsc/quadrupole_convention_policy.md
```

### WBS

1. Implement `q = 2 Q_mu / 3` conversion.
2. Implement full nonlinear polynomial for both conventions.
3. Add worked-point regression.
4. Add artifact validation: missing convention fails.
5. Add doc patch snippets.

### Tests

- `A=0.30`, `Q_mu=0.15` gives `I2=0.842140259740260...`.
- Linear value is `8Q_mu/3=0.400`.
- Same physical input in `q` convention gives identical result.

### Definition of done

Every trace-source artifact is convention-safe.

---

## PR-TSC3-07 — Exact on-manifold nonlinear Thomson trace-source bridge

### Goal

Expose Paper V's trace/intensity source bridge as a safe service.

### SDD delta

- Implement \(I(\hat e)\propto\Theta^4\) source bridge.
- Implement quadrupole projection.
- Mark source exactness as on-manifold only.

### Files

```text
src/tsc/source/thomson_trace_bridge.py
src/tsc/source/theta4_projection.py
tests/tsc/source/test_thomson_trace_bridge.py
```

### WBS

1. Implement \(\Theta^4\) expansion.
2. Implement angular quadrupole projection.
3. Support scalar eta0.
4. Emit nonlinear enhancement ratio.
5. Add spin-2 propagation caveat.

### Tests

- Isotropic theta gives zero quadrupole.
- Small anisotropy linear term matches expected expression.
- Dipole-squared term appears at quadratic order.
- Output always sets `spin2_propagation_required=True` for polarisation channels.

### Definition of done

BASS can consume exact trace-source input without treating TSC as a spin-2 solver.

---

## PR-TSC3-08 — Two-field eta source semantics

### Goal

Handle direction-dependent eta without overclaiming its linear source effect.

### SDD delta

- Add eta-dipole linear decoupling warning.
- Add quadratic onset formula for dipole-only sector.
- Add eta quadrupole caveat.

### Files

```text
src/tsc/source/eta_source_semantics.py
tests/tsc/source/test_eta_source_semantics.py
```

### WBS

1. Implement spectral moment derivative relation.
2. Implement pure eta-dipole linear quadrupole zero test.
3. Implement quadratic dipole-only formula.
4. Add warning if user expects linear eta-dipole quadrupole.
5. Add future hook for `L_eta=2`.

### Tests

- Pure eta dipole has zero quadrupole at linear order.
- Quadratic formula matches direct polynomial expansion.
- Eta quadrupole path marked unsupported/future unless implemented.

### Definition of done

TSC can recommend two-field upgrades without inventing false linear polarisation source claims.

---

## PR-TSC3-09 — Ambient/projected defect service

### Goal

Enforce the ambient vs projected defect correction in code.

### SDD delta

- Ambient defect first derivative equals normal leakage.
- Projected defect first derivative equals zero.
- Never use projected defect as first-order normal leakage.

### Files

```text
src/tsc/defects/ambient_projected.py
tests/tsc/defects/test_defect_split.py
```

### WBS

1. Implement abstract finite-dimensional test harness.
2. Compute ambient first derivative.
3. Compute projected first derivative.
4. Add tolerance and report.
5. Add misuse detector.

### Tests

- Ambient derivative matches `Q_g G(g)`.
- Projected derivative is zero to tolerance.
- Regression catches swapped labels.

### Definition of done

No TSC report can confuse first-order normal leakage with projected reduced error.

---

## PR-TSC3-10 — Collision/state/observable residual bridge

### Goal

Keep `D_coll`, `D_state`, and `Delta_obs` separate and conditionally bridgeable.

### SDD delta

- Add residual kind types.
- Add conditional local observable bound only for state residual.
- Add dynamical accumulation placeholder.

### Files

```text
src/tsc/residuals/collision_state_split.py
src/tsc/residuals/observable_bridge.py
tests/tsc/residuals/test_residual_bridge.py
```

### WBS

1. Implement residual report.
2. Implement observable bound formula requiring `D_state` and `sigma_min_J`.
3. Block `D_coll -> Delta_obs` direct mapping.
4. Add bridge status values.
5. Add warnings for missing state residual.

### Tests

- `D_coll` alone gives no observable adequacy claim.
- `D_state + sigma_min_J` gives conditional bound.
- `sigma_min_J <= floor` triggers no-claim.

### Definition of done

Observable claims from TSC are impossible without state-side residual control or validated dynamical bridge.

---

## PR-TSC3-11 — Channelwise adequacy budget and claim ceiling

### Goal

Annotate every channel with trace/spin-2/high burden and maximum safe claim level.

### SDD delta

- Add TT/TE/EE/BB responsibility matrix.
- Add BiPoSH/template warning.
- Add claim ceiling computation.

### Files

```text
src/tsc/adequacy/channel_budget.py
tests/tsc/adequacy/test_channel_budget.py
```

### WBS

1. Implement channel table.
2. Compute source vs propagation adequacy.
3. Assign claim ceiling.
4. Block trace-only BB.
5. Block morphology/family identification from TSC alone.

### Tests

- TT trace success can be conditional.
- TE marked mixed.
- EE requires spin-2 propagation validation.
- BB trace-only is forbidden.

### Definition of done

All downstream result cards know exactly which block carries the burden.

---

## PR-TSC3-12 — Diagnose-before-switch advisor with hysteresis

### Goal

Provide actionable upgrade advice without becoming the runtime owner.

### SDD delta

- Add switch reasons.
- Add hysteresis/dwell-time fields.
- Add owner-must-decide field.

### Files

```text
src/tsc/control/switch_advisor.py
src/tsc/control/hysteresis.py
tests/tsc/control/test_switch_advisor.py
```

### WBS

1. Define thresholds.
2. Map residual/domain/channel warnings to actions.
3. Add no-chattering policy.
4. Emit recommendation object.
5. Validate owner boundary.

### Tests

- One-field false trigger recommends two-field.
- Spin-2 burden recommends full spin-2 path.
- Recommendation never changes BASS runtime state.

### Definition of done

BASS can consume TSC switch advice while retaining final decision authority.

---

## PR-TSC3-13 — BASS overlay adapter

### Goal

Attach TSC overlays to BASS runtime/transport artifacts without SSoT drift.

### SDD delta

- Overlay-only adapter.
- BASS runtime decision remains owner field.
- TSC fields are caveats/recommendations.

### Files

```text
src/tsc/adapters/bass_overlay.py
tests/tsc/adapters/test_bass_overlay.py
```

### WBS

1. Define accepted BASS input stubs.
2. Build overlay from trace block metrics.
3. Attach overlay to runtime report copy.
4. Validate no mutation of `allow_reduction`.
5. Add manifest entry.

### Tests

- BASS object hash unchanged except overlay path.
- TSC cannot set validation labels.
- Source bridge warnings visible in BASS report.

### Definition of done

BASS receives useful TSC service with no ownership drift.

---

## PR-TSC3-14 — HTT overlay adapter

### Goal

Attach TSC caveats to HTT inference results without touching posterior/evidence.

### SDD delta

- Immutable posterior/evidence fields.
- Claim ceiling and caveat overlay.
- Model-ranking untouched.

### Files

```text
src/tsc/adapters/htt_overlay.py
tests/tsc/adapters/test_htt_overlay.py
```

### WBS

1. Define `HttInferenceResultView` input.
2. Compute channel claim ceilings.
3. Attach caveat overlay.
4. Validate posterior/evidence immutability.
5. Add public-report formatter.

### Tests

- log evidence unchanged.
- posterior samples unchanged.
- public summary shows TSC caveats.

### Definition of done

HTT can report model-dependent results with trace-source caveats but no hidden likelihood change.

---

## PR-TSC3-15 — MIO overlay adapter

### Goal

Attach TSC diagnostic caveats to MIO certificates.

### SDD delta

- MIO certificate remains diagnostic.
- TSC overlay supplies adequacy fields.
- Truth-certificate language forbidden.

### Files

```text
src/tsc/adapters/mio_overlay.py
tests/tsc/adapters/test_mio_overlay.py
```

### WBS

1. Define `MioCertificateView`.
2. Add reduction status mapping.
3. Attach source/spin2/high caveats.
4. Validate no truth/model posterior fields.
5. Add certificate rendering test.

### Tests

- `diagnostic_report_not_truth_certificate=True` enforced.
- No posterior/evidence fields appear.
- Caveats survive serialization.

### Definition of done

MIO certificates become more informative without becoming model-selection claims.

---

## PR-TSC3-16 — Observable Atlas overlay integration

### Goal

Make TSC adequacy visible in `ObservableVector` and `AtlasEntryLite`.

### SDD delta

- Add `tsc_overlay_id`.
- Add block scope and claim status.
- Add validation layer coverage.

### Files

```text
src/tsc/adapters/atlas_overlay.py
tests/tsc/adapters/test_atlas_overlay.py
```

### WBS

1. Define atlas metadata schema.
2. Attach overlay id.
3. Attach channel budget summaries.
4. Validate morphology claims not attributed to TSC.
5. Add report card integration.

### Tests

- BiPoSH result cannot claim TSC-only validation.
- Trace-only atlas entry marked trace.
- Full spin2 entries require external validation link.

### Definition of done

Observable atlas gains claim hygiene and block responsibility metadata.

---

## PR-TSC3-17 — Validation artifact set and runbook integration

### Goal

Implement theorem-indexed validation outputs and pass/warn/fail policy.

### SDD delta

- Mandatory artifact package.
- Standard metric keys.
- Layer A/B/C/R coverage.

### Files

```text
src/tsc/validation/artifact_set.py
src/tsc/validation/passfail_policy.py
src/tsc/validation/test_matrix.py
tests/tsc/validation/test_artifact_set.py
```

### WBS

1. Implement artifact paths.
2. Implement metric schema validation.
3. Implement pass/warn/fail policy.
4. Map tests to theorem/PO links.
5. Build minimal campaign runner.

### Tests

- Missing mandatory artifact fails.
- Missing standard metric warns/fails according to severity.
- Layer B success cannot automatically mark Layer C success.

### Definition of done

TSC validation becomes structurally tied to theorem/claim obligations.

---

## PR-TSC3-18 — Red-team no-overclaim and document patch lint

### Goal

Prevent unsafe public claims in code-generated reports and md/manuscript text.

### SDD delta

- Forbidden phrase scanner.
- Manual rewrite hints.
- Claim ceiling enforcement.

### Files

```text
src/tsc/audit/no_overclaim.py
src/tsc/audit/doc_patch_lint.py
docs/tsc/claim_patch_report_template.md
tests/tsc/audit/test_no_overclaim.py
```

### WBS

1. Encode forbidden phrases.
2. Encode allowed replacements.
3. Scan generated reports.
4. Scan selected docs/manuscripts.
5. Emit patch report.

### Tests

- Catches `full transport closure`.
- Catches `full polarisation closure`.
- Catches `BB controlled by Teff`.
- Allows closure-free backbone wording.

### Definition of done

Generated artifacts and docs cannot accidentally reintroduce unsafe language.

---

## PR-TSC3-19 — Acceptance dashboard and result packs

### Goal

Produce the short-term scientifically useful outputs enabled by active TSC.

### SDD delta

- Dashboard for source adequacy, channel burden, false triggers, validation coverage.
- Export to BASS/HTT/MIO report cards.

### Files

```text
src/tsc/reports/acceptance_dashboard.py
src/tsc/reports/channel_responsibility_table.py
src/tsc/reports/false_trigger_map.py
src/tsc/reports/validation_coverage.py
```

### WBS

1. Aggregate overlays.
2. Build summary tables.
3. Export markdown/JSON.
4. Add figure hooks.
5. Integrate with artifact manifest.

### Tests

- Dashboard refuses to aggregate forbidden claims.
- Source adequacy and propagation adequacy columns distinct.
- All result packs include caveats.

### Definition of done

The project can show how TSC actively improves BASS/HTT/MIO outputs without claiming solver ownership.

---

## PR-TSC3-20 — SDD, documentation, and manuscript sync

### Goal

Keep implementation, SDD, and public manuscript language synchronized.

### SDD delta

- Add SDD sync checklist.
- Add manuscript-safe wording.
- Add release gate.

### Files

```text
docs/tsc/SDD_TSC_active_service_v3.md
docs/tsc/manuscript_safe_wording.md
docs/tsc/release_gate_TSC_v3.md
```

### WBS

1. Update SDD with implemented APIs.
2. Update PR list status.
3. Run doc patch lint.
4. Produce release gate report.
5. Tag v3 baseline.

### Tests

- SDD APIs match exported contracts.
- No forbidden language in docs.
- Release gate requires passing PR-TSC3-06, 07, 10, 11, 17, 18.

### Definition of done

TSC v3 can be referenced by BASS/HTT/MIO planning without ambiguity.

---

## 13. Cross-PR acceptance matrix

| Acceptance rule | Enforced by |
|---|---|
| Characteristics never called closure | PR-00, PR-18 |
| Teff/TSC never called full solver | PR-00, PR-18 |
| Trace and spin-2 separated | PR-01, PR-11, PR-16 |
| `D_coll`, `D_state`, `Delta_obs` separated | PR-10, PR-17 |
| Ambient/projected defect separated | PR-09 |
| Q convention fixed | PR-06, PR-07 |
| Eta-dipole source semantics safe | PR-08 |
| BASS owner boundary preserved | PR-12, PR-13 |
| HTT posterior/evidence untouched | PR-14 |
| MIO certificate not truth certificate | PR-15 |
| Validation artifacts mandatory | PR-17 |
| Red-team claims blocked | PR-18 |

---

## 14. Minimal near-term implementation order

If code time is limited, do this sequence first:

1. **PR-TSC3-01** contracts/schema.
2. **PR-TSC3-06** Q convention registry.
3. **PR-TSC3-07** Thomson trace-source bridge.
4. **PR-TSC3-10** residual bridge type separation.
5. **PR-TSC3-11** channel burden budget.
6. **PR-TSC3-13/14/15** BASS/HTT/MIO overlay adapters.
7. **PR-TSC3-18** no-overclaim lint.
8. **PR-TSC3-19** dashboard.

This gives immediate scientific value without building a new solver.

---

## 15. Enabled short-term result packs

### Result Pack TSC-A — Trace-source adequacy dashboard

Questions answered:

- Which runs are trace-on-manifold?
- Which need two-field upgrade?
- Which have source adequate but propagation pending?

Outputs:

```text
tsc_trace_source_adequacy_dashboard.md
tsc_trace_source_adequacy.json
fig_trace_source_status_matrix.png
```

### Result Pack TSC-B — Channel responsibility map

Questions answered:

- TT/TE/EE/BB claims rely on trace, spin-2, or high residual?
- Which claims are diagnostic-only?

Outputs:

```text
table_channel_responsibility.md
fig_trace_spin2_high_burden.png
```

### Result Pack TSC-C — False-trigger and two-field upgrade map

Questions answered:

- How much one-field residual is eta-tangent rather than true spectral distortion?
- Where does two-field extension reduce false alarms?

Outputs:

```text
tsc_twofield_false_trigger_map.json
fig_onefield_vs_twofield_residual.png
```

### Result Pack TSC-D — HTT/MIO caveat-enriched science reports

Questions answered:

- Which HTT evidence results are trace-source safe but morphology-limited?
- Which MIO certificates are diagnostic-only vs source-validated?

Outputs:

```text
htt_tsc_caveat_overlay_report.md
mio_tsc_certificate_overlay_report.md
```

### Result Pack TSC-E — Theorem/validation coverage dashboard

Questions answered:

- Which theorem/PO claims have tests?
- Which public claims remain validation obligations?

Outputs:

```text
tsc_theorem_validation_coverage.md
tsc_claim_status_matrix.json
```

---

## 16. Manuscript-safe wording

Safe:

> TSC provides trace/intensity statistical semantics and exact on-manifold source reconstruction for selected blocks. It also reports diagnostics and adequacy caveats used by the transport, inference, and observatory layers.

Safe:

> The source bridge supplies the intensity quadrupole entering polarised transfer; spin-2 propagation remains an independent transport problem.

Safe:

> A small collision-side residual is a diagnostic. Observable adequacy additionally requires state-side residual control, conditioning, and validation.

Forbidden:

> TSC closes the full Boltzmann hierarchy.

Forbidden:

> Characteristics is the full transport closure.

Forbidden:

> Teff controls BB or BiPoSH morphology by itself.

Forbidden:

> MIO/TSC certifies the true cosmological model.

---

## 17. Final definition of done

TSC v3 is complete when:

1. All source documents and zip internals are summarized and hashed.
2. All public TSC outputs carry claim status, block scope, owner boundary, and validation layer coverage.
3. Q convention regression passes.
4. `D_coll`, `D_state`, `Delta_obs` cannot be conflated by type or serializer.
5. BB and BiPoSH claims are blocked unless validated outside TSC.
6. BASS, HTT, and MIO adapters are overlay-only and cannot mutate owner-owned fields.
7. Validation artifacts follow Layer A/B/C/R protocol.
8. No-overclaim lint passes on generated docs/reports.
9. The acceptance dashboard can generate the five result packs.

---

## 18. Final recommendation

Do not make TSC bigger by making it a solver. Make it stronger by making it the **semantic and statistical-mechanical conscience** of the stack.

The most productive near-term architecture is:

\[
\boxed{
\text{BASS solves / HTT infers / MIO reports / TSC annotates, bounds, warns, and prevents overclaim.}
}
\]

That division keeps SSoT intact while making TSC materially useful to every other part of the codebase.
