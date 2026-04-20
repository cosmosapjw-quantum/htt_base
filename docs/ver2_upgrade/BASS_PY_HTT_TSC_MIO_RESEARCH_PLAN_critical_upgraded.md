# BASS_PY / HTT / TSC / MIO 연구계획 및 Manuscript 확장안 — critical upgrade

**기준일**: 2026-04-20  
**업그레이드 방식**: 이 v4 section이 아래 v3 본문보다 우선한다. 아래 v3 본문은 세부 inventory와 기존 WBS 보존용으로 남긴다.  
**검토 범위**: `main(2).tex`, `ch01`–`ch11`, `appendices`, `BASS_MIO_HTT_execution_plan(3).md`, 기존 `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md`.

---

## v4.0 핵심 판단

현재 연구는 이미 하나의 논문형 체계를 갖고 있다. 수학적 identity, Bianchi type별 bound, Teff/TSC formalism, SSOT pipeline, numerical evidence, robustness suite, error hierarchy까지 모두 존재한다. 따라서 다음 연구계획의 중심은 “더 많은 결과를 추가”가 아니라 **claim-tier를 코드 객체로 고정하고, direction-inclusive observable로 넘어가기 전의 gate를 닫는 것**이어야 한다.

가장 중요한 교정은 다음이다.

| v3 표현/구조 | 문제 | v4 교정 |
|---|---|---|
| MIO가 evidence/posterior/F,Q,Pi까지 갖는 듯한 표현 | MIO를 model-independent observatory로 재정의한 v3 내부 원칙과 충돌 | HTT가 posterior/evidence owner, MIO는 diagnostic/certificate owner |
| HTT를 local patch helper로만 축소 | 현재 HTT prototype은 15-model evidence, posterior, nulls, PPC/LOOCV까지 담당 | HTT = model-dependent inference owner. local patch는 그 안의 한 mode |
| BASS exact owner와 `bass_py` scope 혼재 | current Python plan과 long-term exact solver target이 섞임 | `BASS`/`bass_py`/`bass_rs` scope fields를 artifact마다 강제 |
| TSC/Teff 확장 기대가 direction-inclusive claim과 섞임 | tex 원고는 Teff가 scalar-amplitude surrogate이며 full \(a_{\ell m}\)에는 부족하다고 명시 | TSC는 trace/intensity source semantics까지만. \(a_{\ell m}\), BiPoSH, BB는 BASS/HTT/MIO validated path |
| 145 figures / 82 tables / 18k code line expansion | figure-first relapse 위험. status/test count도 문서 간 불일치 | “artifact-first, figure-second” gate와 CI-generated status snapshot 도입 |
| MIO HJ-01 비모수 \(\Sigma^2\) extraction | \(K_\ell\) atlas, covariance, sky mask가 없으면 “direct measurement”가 아님 | HJ-01은 BASS atlas/covariance prerequisite를 명시하고 없으면 diagnostic-only |
| ZoA redesign | 방향성은 맞지만 production promotion gate가 더 필요 | PreferredAxis/sky support/mock coverage 없으면 downstream synthesis 금지 |

---

## v4.1 tex 원고 기반 연구 진척사항 요약

### 1. 이미 닫힌 축

1. **수학적 spine**  
   Master departure identity \(x_C=\Sigma^2_{\rm std}-W^2_{\rm std}+\Omega_{\rm tilt}+\Omega_{k,\rm aniso}\), comparator FLRW, three-layer chain \(x\to Q\to \Pi\), three-frame problem이 논문 내부 구조로 이미 확립되어 있다.

2. **Bianchi type별 bound**  
   9개 Bianchi type의 orthogonal/tilted sector, MES three-bound hierarchy, vorticity/acceleration/shear hierarchy, obstruction/certification class가 논문 축으로 잡혀 있다.

3. **Teff/TSC formalism**  
   Teff는 scalar-amplitude pipeline에서 충분하고 빠른 surrogate로 정리되어 있다. 하지만 full direction, cascade morphology, family identification에는 \(a_{\ell m}\)/TAM/AniCLASS급 output이 필요하다는 경계도 이미 원고에 적혀 있다.

4. **SSOT pipeline and validation**  
   단일 소스 원칙, validation protocol, Route B transfer validation, solver architecture, FLRW recovery/linearity/AniCLASS overlap/reionization-polarization checks가 원고에 들어가 있다.

5. **Numerical result layer**  
   positive \(\ln\mathcal B\sim +26\) 계열 결과, filling fraction, null recovery, cross-pipeline consistency, solver-validated transfer function이 있다. 단 이 결과는 direction-marginalised summary-statistic likelihood 아래의 결과다.

6. **Robustness and identifiability**  
   null recovery와 systematics sweep은 강하지만, model identifiability와 direction-inclusive family separation은 아직 future/gated item이다.

7. **Error hierarchy**  
   5-level error hierarchy가 있고, Phase 1.0 dominant error가 Teff closure가 아니라 state-space / analytic gravitational potential 쪽이라는 결론이 있다. 따라서 Phase 2.0 self-consistent Poisson은 “nice-to-have”가 아니라 다음 solver bottleneck이다.

### 2. 아직 닫히지 않은 축

| 미해결 축 | 왜 중요한가 | v4 코드계획 반영 |
|---|---|---|
| direction-inclusive likelihood | scalar \(D_2\)만으로 Bianchi family/morphology 식별 불가 | W11/W14/W15를 claim-gated critical path로 승격 |
| \(a_{\ell m}\)/BiPoSH covariance | MIO non-parametric extraction과 HTT directional evidence의 공통 기반 | `AtlasEntry`, `BiposhCovariance`, `SkySupport` contracts 추가 |
| model-independent vs model-dependent 분리 | MIO certificate와 HTT posterior가 섞이면 논문 claim이 붕괴 | G19 hard-separation tests |
| status/test count inconsistency | main/ch06/md 사이 숫자 불일치가 public release에서 치명적 | CI-generated `status_snapshot.json` |
| TSC admissibility tests | 현재 tsc.admissibility test 부재는 inverse/reduction promotion을 막아야 함 | P0/P1 gate로 상향 |
| unresolved citations | ch02/ch03/ch11의 `[CITATION NEEDED]`는 final manuscript blocker | manuscript patch queue에 추가 |

---

## v4.2 Revised package roles

| Package | v4 role | Owns | Does not own |
|---|---|---|---|
| `bass_py` | current Python low-\(\ell\) forward/validation stack | Route B sentinel, low-\(\ell\) transfer, validation harness, BASS bridge prototypes | full exact nonperturbative solver claim |
| `BASS` canonical | runtime/reduction owner target | reduction decision, source adequacy consumption, validation labels, exact transport target | posterior/evidence/certificate truth |
| `HTT` | model-dependent inference owner | posterior, evidence, directional likelihood, local boost patch, null competition, PPC/LOOCV | model-independent certificate, BASS runtime allow/block |
| `MIO` | model-independent observatory | non-parametric extraction, coherence, FLRW tension diagnostics, residual atlas, `MioCertificate` | posterior, evidence gate, truth certificate |
| `TSC` | trace/intensity semantics controller | Teff charts, source bridge, admissibility, upgrade recommendation | full solver, full polarization, BB/family identification, runtime allow/block |
| `common/contracts` | semantic firewall | dataclasses, claim tier, artifact manifests, sky support contracts | physics computation |

---

## v4.3 P0 correction pack

### P0-A — Status and claim ledger

**Problem**: 문서마다 “tests/modules/lines/status” 숫자가 다르다.  
**Patch**:
- Add `src/common/status_snapshot.py`.
- Add `artifacts/status_snapshot.json`.
- Add `docs/status_matrix.md`.
- Forbid manually typed test/line counts in manuscript-facing docs unless generated.

**Tests**:
- `test_status_snapshot_schema`
- `test_no_manual_status_count_in_docs`
- `test_claim_tier_present_in_artifacts`
- `test_implemented_smoke_validated_manuscript_used_are_distinct`

**Acceptance**:
Every package row must contain:
```yaml
implemented: true|false
smoke_tested: true|false
production_validated: true|false
manuscript_used: true|false
claim_tier: exploratory|conditional|validated
source_commit: <hash>
```

### P0-B — Ownership firewall

**Problem**: MIO/HTT/TSC/BASS 책임이 문서 내부에서도 흔들린다.  
**Patch**:
- Add `src/common/contracts.py` or `workspace/contracts/ownership.py`.
- Add owner enum:
```python
Owner = Literal["BASS", "HTT", "MIO", "TSC", "COMMON"]
ClaimTier = Literal["exploratory", "conditional", "validated"]
ImplementationScope = Literal["bass_py", "bass_rs", "canonical_BASS", "htt", "mio", "tsc", "common"]
```

**Tests**:
- `test_runtime_decision_owner_bass_only`
- `test_mio_certificate_not_posterior`
- `test_htt_posterior_not_mio_certificate`
- `test_tsc_chart_diagnostic_not_allow_block`
- `test_common_contracts_have_no_physics_side_effects`

### P0-C — HTT ZoA / axis production lock

**Problem**: diagnostic ZoA axis가 production axis로 승격될 위험이 있다.  
**Patch**:
- `PreferredAxis.production_allowed=False` by default.
- uniform fallback production mode → `RuntimeError`.
- raw `(mean(l), mean(b))` 금지; unit vector spherical mean only.
- every axis artifact includes `sky_support_hash`, `mask_hash`, `mock_coverage_status`.

**Tests**:
- `test_uniform_fallback_raises_in_production`
- `test_raw_lb_mean_forbidden`
- `test_preferred_axis_default_not_production`
- `test_diagnostic_axis_cannot_rotate_a2m`
- `test_axis_requires_mock_coverage_ok`

### P0-D — TSC admissibility before inverse

**Problem**: TSC chart/inverse는 유용하지만 admissibility test 없이 production inverse가 열리면 위험하다.  
**Patch**:
- Move `tsc.admissibility.realizability` tests to P0/P1 boundary.
- Hard constraints: \(\Theta>0\), BE \(\eta\le0\), weights nonnegative, \(\sum_g w_g=1\).
- Add no-overclaim vocabulary scan.

**Tests**:
- `test_theta_positive`
- `test_be_eta_nonpositive`
- `test_weight_simplex`
- `test_inverse_blocks_outside_admissible_domain`
- `test_tsc_no_spin2_solver_claim`

### P0-E — BASS denominator and source/propagation split

**Problem**: Transfer/source adequacy가 propagation adequacy와 섞이면 Teff/TSC overclaim으로 이어진다.  
**Patch**:
- `RuntimeReductionDecision` object.
- `SourcePropagationStatus` enum.
- BASS-only `allow_reduction`.

**Tests**:
- `test_source_adequate_propagation_pending_allowed_label`
- `test_reduction_blocked_without_sigma_floor`
- `test_reduction_blocked_without_source_gate`
- `test_mixed_channel_pending_label_emitted`
- `test_route_b_sentinel_anti_regression`

---

## v4.4 Revised critical path

### Wave 0 — before Phase A continues

1. Status snapshot + claim ledger.
2. Ownership firewall dataclasses.
3. RuntimeReductionDecision owner=BASS.
4. HTT ZoA P0 patches.
5. TSC admissibility tests.
6. Artifact manifest schema.

### Wave 1 — denominator/source validation

1. FLRW denominator V-gate.
2. Route B sentinel and \(C_1,C_2\) fit.
3. Source/propagation label emitter.
4. Error hierarchy metrics per run.
5. Reionization on/off + low-\(\ell\) polarization smoke.

### Wave 2 — direction infrastructure

1. BiPoSH coefficient module.
2. \(a_{\ell m}\) / matrix LoS bridge spec.
3. `AtlasEntry` + covariance schema.
4. Directional likelihood with sky support.
5. Mock calibration and null family FPR.

### Wave 3 — HTT model-dependent production

1. WLS baseline.
2. Dynesty fiducial posterior.
3. 15-model evidence ranking.
4. Null competition production.
5. PPC/LOOCV model adequacy.

### Wave 4 — MIO model-independent observatory

1. HJ-02 directional coherence can start early if covariance is explicit.
2. HJ-01 non-parametric \(\Sigma^2\) extraction waits for \(K_\ell\)/atlas.
3. HJ-03 FLRW tension waits for null predictive distribution.
4. HJ-04 evidence anatomy waits for HTT evidence trace.
5. HJ-05 residual atlas waits for shared prediction/data schema.

### Wave 5 — manuscript/figures

Figures/tables only after:
- artifact exists,
- manifest exists,
- owner/claim tier exists,
- test gate passes,
- caveat text exists.

---

## v4.5 Revised deliverable table additions

Add these deliverables before or alongside the v3 D-list.

| ID | Deliverable | Owner | Status | Blocks |
|---|---|---|---|---|
| D0 | `StatusSnapshot` + `docs/status_matrix.md` | common | new P0 | all public status claims |
| D0b | `ClaimLedger` | common | new P0 | manuscript claim-tier consistency |
| D0c | `ArtifactManifest` | common | new P0 | figure/table generation |
| D0d | `RuntimeReductionDecision` | BASS | new P0 | reduction/inverse production |
| D0e | `SourcePropagationStatus` | BASS/TSC split | new P0 | TSC/BASS source bridge |
| D0f | `SkySupport` + `PreferredAxis` production gate | HTT/common | new P0 | \(a_{\ell m}\) synthesis |
| D0g | `MioCertificate` no-merge tests | MIO/common | new P0 | MIO Phase J |
| D0h | `AtlasEntry` covariance schema | BASS/common | new P1 | HJ-01, BiPoSH, direction likelihood |
| D0i | `TheoremToTestMap` | common | new P1 | hostile review / audit |
| D0j | unresolved citation patch queue | manuscript | new P0 | final submission |

---

## v4.6 MIO Phase J dependency correction

v3 says HJ-02 can start early; that is partly correct. But each MIO module must advertise whether it is **covariance-complete** or merely **diagnostic-only**.

| Module | Earliest start | Required for production-grade result | fallback status |
|---|---|---|---|
| HJ-02 directional coherence | Phase A/B | probe covariance + sky support + mask | diagnostic-only vector resultant |
| HJ-02b z-binned coherence | after catalog z-bins stable | z-bin covariance + selection function | descriptive only |
| HJ-01 \(\Sigma^2_{\rm MIO}(\ell)\) | after BASS \(K_\ell\) atlas | transfer kernel + covariance + mask | blocked |
| HJ-03 FLRW tension PPP | after null predictive mocks | calibrated FLRW null distribution | no PPP claim |
| HJ-04 evidence anatomy | after HTT evidence trace | channel logL/evidence decomposition | narrative-only |
| HJ-05 residual atlas | after shared prediction schema | data/model residual map + caveats | diagnostic-only |

---

## v4.7 Manuscript upgrade corrections

### ch01/ch09 claim wording

Use:
> decisive evidence for a non-zero tilt-compatible matter-dipole anomaly under the adopted summary-statistic likelihood.

Do not use:
> decisive evidence for anisotropic spatial geometry.

### ch05/ch11 Teff/TSC boundary

Use:
> Teff/TSC is adequate for scalar-amplitude source/trace diagnostics and fast scans; direction-inclusive morphology requires validated \(a_{\ell m}\)/BiPoSH or pixel-template path.

Do not use:
> Teff solves full polarization or Bianchi family identification.

### ch06/ch07 status numbers

All status numbers must be generated from `status_snapshot.json`. If `main(2).tex`, ch06, and md disagree, the manuscript uses snapshot values and includes a dated status table.

### unresolved citation queue

Add a manuscript P0 patch list:
- ch02: Chen/Han/Qiu axion isocurvature citation placeholder.
- ch03: Teff Paper III tangency/false-alarm placeholder.
- ch11: Teff Paper IV adequacy tightness placeholder.

### ch08/ch12 MIO wording

Use:
> MIO cross-validates and reports model-independent diagnostics.

Do not use:
> MIO certifies truth or adjudicates model posterior.

---

## v4.8 Concrete code-writing PR packets

### PR-C0 — contracts and manifests

**Files**
```text
src/common/contracts.py
src/common/artifact_manifest.py
src/common/status_snapshot.py
src/common/claim_tier.py
tests/contracts/test_ownership_firewall.py
tests/contracts/test_artifact_manifest.py
tests/contracts/test_status_snapshot.py
docs/status_matrix.md
docs/claim_ledger.md
```

**DoD**
- All artifacts can be traced to owner/scope/claim tier.
- No package can silently produce a production artifact without manifest.

### PR-BASS-C1 — runtime decision and source labels

**Files**
```text
src/bass/runtime/reduction_decision.py
src/bass/runtime/source_adequacy_consumer.py
src/bass/runtime/validation_label_emitter.py
src/bass/validation/route_b_sentinel.py
src/bass/validation/error_hierarchy_metrics.py
tests/bass/test_runtime_decision_owner.py
tests/bass/test_source_propagation_labels.py
tests/bass/test_route_b_sentinel.py
```

**DoD**
- BASS is the only owner of `allow_reduction`.
- Source adequate / propagation pending status can be represented.
- Route B sentinel is emitted in every serious run.

### PR-HTT-C2 — ZoA and axis gate

**Files**
```text
src/common/sky_geometry.py
src/common/healpix_selection.py
src/common/mock_calibration.py
src/htt/direction/preferred_axis.py
src/htt/zoa/selection_ladder.py
src/htt/zoa/axis_promotion.py
tests/htt/test_zoa_no_uniform_fallback.py
tests/htt/test_preferred_axis_gate.py
tests/htt/test_spherical_mean.py
tests/htt/test_mock_coverage_gate.py
```

**DoD**
- Diagnostic axis cannot become production axis.
- Axis promotion requires mock coverage and sky support metadata.

### PR-TSC-C3 — admissibility and no-overclaim

**Files**
```text
src/tsc/admissibility/realizability.py
src/tsc/admissibility/domain.py
src/tsc/diagnostics/no_overclaim.py
tests/tsc/test_realizability.py
tests/tsc/test_inverse_domain_block.py
tests/tsc/test_no_full_polarization_claim.py
```

**DoD**
- TSC inverse cannot run outside chart domain.
- TSC cannot emit full spin-2 solver labels.

### PR-MIO-C4 — certificate and G19 separation

**Files**
```text
src/mio/interface/mio_certificate.py
src/mio/interface/htt_cross_check.py
src/mio/diagnostics/caveats.py
tests/mio/test_certificate_schema.py
tests/mio/test_g19_no_merge.py
tests/mio/test_certificate_no_truth_language.py
```

**DoD**
- MIO certificate is not posterior, not truth certificate.
- Cross-check output cannot be summed with HTT evidence.

### PR-MIO-C5 — covariance-aware HJ modules

**Files**
```text
src/mio/extraction/shear_nonparametric.py
src/mio/extraction/kernel_atlas.py
src/mio/coherence/directional.py
src/mio/tension/flrw_tension.py
src/mio/decomposition/evidence_anatomy.py
src/mio/diagnostics/predictive_residuals.py
tests/mio/test_shear_extraction_requires_atlas.py
tests/mio/test_directional_coherence_requires_covariance.py
tests/mio/test_flrw_tension_requires_null_mocks.py
```

**DoD**
- Each MIO result knows whether it is production-grade or diagnostic-only.

---

## v4.9 Revised timeline gates

| Phase | v3 target | v4 gate before phase can count as complete |
|---|---|---|
| A | W10-02 + HTT ZoA P0 | status snapshot, ownership firewall, ZoA P0 tests green |
| B | W11 + common modules | artifact manifest + `PreferredAxis` gate + sky support schema |
| C | W12 + mock calibration | mock coverage report blocks production axis |
| D | W13 + dynesty | posterior bundle has manifest/claim tier |
| E | W14 3-signature | source/propagation labels and denominator V-gate green |
| F | W15 bridge + HJ-02 | HJ-02 may be diagnostic-only unless covariance complete |
| G | tsc + HJ-03/04 | HJ-03/04 production claims require null mocks/evidence trace |
| H | manuscript expansion | no figure without artifact manifest |
| I | submission | unresolved citation queue cleared |

---

## v4.10 Risk register additions

| Risk | Severity | Symptom | Kill / rollback criterion |
|---|---:|---|---|
| MIO/HTT merge relapse | P0 | certificate and posterior combined into one score | reject PR |
| TSC overclaim | P0 | trace chart emits spin-2/full polarization label | reject PR |
| direction claim from scalar amplitude | P0 | family identification without \(a_{\ell m}\)/BiPoSH | block manuscript claim |
| status drift | P0 | test/module count typed manually and conflicts | regenerate from snapshot |
| figure-first relapse | P1 | figure generated from non-manifest artifact | quarantine figure |
| external-event timeline drift | P1 | Euclid/DESI/LiteBIRD dates treated as fixed without verification | mark as planning assumption |
| covariance omission | P1 | MIO p-values without covariance | downgrade to descriptive diagnostic |
| null mock insufficiency | P1 | PPP/tension metric without calibrated null | block PPP claim |

---

## v4.11 Success criteria, revised

A v4 implementation is successful only if:

1. every artifact has owner, scope, claim tier, config hash, input hashes, and caveats;
2. BASS is the only production `allow_reduction` owner;
3. HTT posterior/evidence and MIO certificate cannot merge by type or schema;
4. TSC cannot emit full solver/polarization/family-identification labels;
5. HTT diagnostic axes cannot rotate \(a_{\ell m}\) unless production gate passes;
6. Route B sentinel and denominator V-gate run before scientific figures;
7. MIO production-grade results require covariance/atlas/null mocks as appropriate;
8. manuscript status numbers come from CI snapshot;
9. unresolved citation placeholders are removed before final manuscript freeze;
10. every figure/table is artifact-first, manifest-backed, and claim-tier labelled.

---

## v4.12 Immediate next actions

1. Write `src/common/contracts.py` first. Do not start new science modules before this.
2. Add `RuntimeReductionDecision` and owner tests.
3. Patch HTT ZoA production fallback and preferred-axis gate.
4. Add TSC admissibility tests.
5. Generate `status_snapshot.json` and reconcile all counts.
6. Add BASS Route B / denominator V-gate artifacts.
7. Start MIO HJ-02 in diagnostic mode only, unless covariance is ready.
8. Delay figure expansion until artifact manifests are available.

---

# v3 baseline retained below

The following v3 plan is retained for inventory, detailed WBS, and manuscript expansion content. Any conflict between v4 sections above and v3 text below is resolved in favour of v4.

---

# BASS_PY / HTT / TSC / MIO 연구계획 및 Manuscript 확장안 — v3

**버전**: bass_py-scope v3.0 (v2 전면 업그레이드, MIO 통합)
**기준일**: 2026-04-18
**범위 경계**: bass_rs (Rust 프로덕션 솔버) 제외. Python 측 forward + inference + observatory + analysis 스택.

**v2 → v3 주요 변경**

| 변경 항목 | v2 | v3 |
|---|---|---|
| 패키지 개수 | 3 (bass_py / htt / tsc) | **4 (+ MIO)** |
| MIO 역할 규정 | **누락** (잘못 서술된 "epistemic control" 표현이 §11 등에 산재) | **Model-Independent Observatory** — physics-producing, 모델 비가정 측정 |
| Epistemic control 소유 | MIO에 집중 (오해) | **분산 소유** — 각 모듈 자체 책임 |
| HTT ↔ MIO 관계 | 명시 없음 | **Hard separation** — cross-check만, 단일 inferential object로 병합 금지 (G19) |
| Interface 객체 | 명시 없음 | `HttForwardOutput`, `MioCertificate`, `AtlasEntry` |
| Manuscript MIO chapter | 없음 | **신규 ch12 "MIO Observatory Results"** |
| MIO Phase | 없음 | **Phase J (HJ-01~05)**: 비모수 shear extraction, directional coherence, FLRW tension, evidence decomposition, predictive diagnostics |
| Figure 수 | ~130 | **~145** (MIO 추가) |
| Table 수 | ~75 | **~82** (MIO 추가) |
| 코드 합계 | ~14,600 L | **~17,600 L** (MIO +3,000) |

---

## §0. Executive Summary

### 0.1 네 패키지 전체 상태

| 패키지 | 버전/상태 | 라인 | 테스트 | 역할 (v3 명확화) |
|---|---|---|---|---|
| `bass_py` | 14/24 prompt 완료 | ~25,000 | 1,503 | **Forward solver (low-ℓ)**. Self-gating: `runtime.canonical_decision` + `validation_labels` + `sigma_floor` |
| `tsc` | bass_py tree에 이미 통합 | ~3,500 | 351 | **Internal consistency**. Admissibility, tangency, charts (F↔T). Self-audit: realizability |
| `htt` | **v8.3.0 prototype 존재** | ~15,400 | 123 (일부 sys.path) | **Model-dependent inference**. 15 evidence models + posterior + BF. Self-audit: matched_complexity + null_competition + advanced_diagnostics (PPC/LOOCV) |
| **`mio`** | **신규 패키지** | **~0 (PR13AM 제외)** | **~0** | **Model-Independent Observatory**. Physics-producing. 비모수 Σ² 추출, directional coherence, FLRW tension, evidence decomposition. **NOT a certification gatekeeper** |

### 0.1bis Epistemic control은 "분산 소유"다 (v3 핵심 재정의)

v2에서 MIO를 "epistemic control / post-hoc certification" 역할로 잘못 기술했던 부분을 전면 교정. **epistemic hygiene은 어느 단일 모듈에도 집중되지 않는다** — 각 모듈이 스스로 책임진다.

| 도메인 | 책임 모듈 | 기존 매커니즘 |
|---|---|---|
| Forward solver 내부 검증 | `bass.runtime.*` | W3 gate, Σ² floor guard, 3-tier claim labels |
| 물리적 실현 가능성 (admissibility) | `tsc.admissibility.*`, `tsc.diagnostics.tangency` | realizability, tangency, entropy invariants |
| Posterior 적합성 (model-dependent) | `htt.infer.matched_complexity`, `htt.infer.null_competition`, `htt.advanced_diagnostics.*` | Posterior predictive, LOOCV, Savage-Dickey, cross-channel coherence |
| Model-independent 진단 보고서 | `mio.diagnostics.adequacy_certificates` | `MioCertificate` — **진단 보고서**, truth certificate 아님 |
| Interface 의미 경계 | `workspace/contracts/` | `HttForwardOutput`, `MioCertificate`, `AtlasEntry` 의미론적 계약 |
| Production axis gate | `src/common/contracts.py` (v2에서 확립) | `PreferredAxis.production_allowed` |

**핵심**: MIO는 "무엇이 True인지 판정"하지 않는다. MIO는 "무엇이 data에서 직접 보이는가" — 모델을 가정하지 않고 — 를 보고한다.

### 0.2 ZoA 재설계 요구에 따른 작업 분류 (v2 추가)

| 우선 | 조치 | 근거 |
|---|---|---|
| P0 (즉시) | `PR13AM_te_sign_d1d3_bridge.py`의 uniform fallback을 production 모드에서 **예외 발생**으로 교체 | 진단용 fallback이 조용히 inference에 섞이는 중 |
| P0 (즉시) | `PR13AJ_full_a2m_restoration.py`의 `PreferredAxis`에 `production_allowed` gate 추가 | ZoA-20° diagnostic axis가 `a20 → full a2m` 회전에 그대로 사용됨 |
| P0 (즉시) | `FLRW_tilt_zoa20_mean`을 downstream default에서 제거 | diagnostic 안정화값을 production 기본값으로 승격한 상태 |
| P1 | ZoA summary 생성 로직을 artifact가 아닌 `src/common/sky_selection.py`로 승격 | reproducibility gap — 현재 artifact-only |
| P1 | 4개 summary 분리 (raw / zoa_masked / selection_aware / mock_calibrated) | 지금은 raw mean과 masked mean이 같은 path에 섞임 |
| P2 | Null mock ZoA calibration suite | retention fraction + bias + coverage 측정 필요 |
| P2 | Angular completeness map (healpy 기반) | 현재 hard cut만 있음 |

### 0.3 본 문서에서 다루는 deliverable 통합 목록 (v3, MIO 포함)

**Legend**: 패키지 컬럼에 deliverable의 **1차 소유자** 표시. cross-check 관계는 "비고"에 기록.

| # | Deliverable | 출처 | 패키지 | Manuscript 위치 | 상태 | 비고 |
|---|---|---|---|---|---|---|
| D1 | 15-model Bianchi evidence ranking × 5 scenarios | htt.core.evidence_models | **HTT** | ch07 §7.1 | prototype | Model-dependent |
| D2 | 3-signature discriminator (local / cosmological / tilt²) | W14-01 + htt.directional_models | **HTT** | ch07 §7.6 | **W14 미착수** | Template fit은 HTT |
| D3 | Dipole direction posterior (Mollweide + HPD cone) | htt.catalog_likelihood_3D | **HTT** | ch07 §7.8 | prototype, dynesty 대체 필요 | Model-dependent posterior |
| D4 | Null competition FPR (5 families × 15 models) | htt.nulls.runner | **HTT** | ch08 §8.5 | prototype | Self-audit of HTT |
| D5 | Filling fraction F_Bayes (재검증) | htt.analysis_extended + tsc 신규 | **HTT + tsc** | ch07 §7.9 | 부분 완료 | tsc cross-check |
| D6 | Three-bound hierarchy B_σ > B_ω > B_u̇ | htt.bounds | **HTT** | ch04 §4.3 | 완료 | Algebraic, model-structured |
| D7 | β → D_2 transfer function curve | W13-02 | **bass_py** | ch07 §7.5 | 미착수 | Forward |
| D8 | MES boundary check + model identifiability audit | htt.pipeline phase 3f/3g | **HTT** | ch08 §8.3 | prototype | Self-audit |
| D9 | Depth tomography per z-bin (model-dependent) | htt.advanced_diagnostics.DepthTomography | **HTT** | ch07 §7.10 | prototype | HTT posterior × z-bin |
| D10 | Savage-Dickey ratios (hypothesis tests) | htt.advanced_diagnostics.SavageDickeyRatio | **HTT** | ch07 §7.11 | prototype | Model-dependent BF |
| D11 | Cross-channel coherence + LOOCV (posterior-conditioned) | htt.advanced_diagnostics | **HTT** | ch08 §8.6 | prototype | HTT self-audit |
| D12 | Posterior predictive checks (15 models) | htt.advanced_diagnostics.PosteriorPredictive | **HTT** | ch08 §8.7 | prototype | Model-dependent PPC |
| D13 | Matched-complexity protocol report | htt.infer.matched_complexity | **HTT** | ch06 §6.8 | prototype | HTT self-audit |
| D14 | Survey nuisance marginalisation | htt.infer.survey_nuisance | **HTT** | ch08 §8.4 | prototype | Model-dependent |
| D15 | Quadrupole axis + parity tests | htt.geometry_discrimination | **HTT** | ch07 §7.12 | prototype | Model-dependent |
| D16 | Shared-cause test (common origin of dipoles) | htt.infer.shared_cause | **HTT** | ch08 §8.8 | prototype | Model-dependent |
| D17 | Route B sentinel D_2(Σ²=1e-8)=0.1741 μK² | bass.spectrum.cl_assembly | **bass_py** | ch07 §7.1.a | **완료** | Forward |
| D18 | CAMB FLRW V-gate | W10-02 | **bass_py** | ch08 §8.1 | 미착수 | bass_py self-validation |
| D19 | BiPoSH coefficients A^{LM}_{ℓ₁ℓ₂} | W11-02 | **bass_py** | ch07 §7.4 | 미착수 | Forward |
| D20 | W_R window + frame-attribution bias | W12-01~02 | **bass_py** | ch07 §7.3, ch03 §3.X | 미착수 | Forward |
| D21 | ZoA-aware directional likelihood (3-mode) | htt re-design + src/common | **HTT + common** | ch06 §6.9, ch08 §8.9 | 재설계 요구 | Model-dependent path |
| D22 | Mock calibration coverage report | htt mock_calibration (신규) + src/common | **common + HTT** | ch08 §8.10 | 미착수 | Frequentist coverage |
| D23 | Depth-by-depth sensitivity (CF4++ z-bin) | htt.core.h0_sensitivity + advanced | **HTT** | ch08 §8.11 | prototype | Model-dependent |
| D24 | Type-by-type summary (orth × tilt) | htt.figures | **HTT** | ch07 §7.13 | prototype | Model-dependent |
| D25 | Equivalence class evidence | htt.figures | **HTT** | ch07 §7.14 | prototype | Model-dependent |
| D26 | Tilted-FLRW observables dictionary | htt.core.tilted_flrw | **HTT** | ch07 §7.15 | 완료 | Model-structured |
| D27 | Colin β constraints reproduction | htt.figures | **HTT** | ch09 §9.X | 완료 | Model-dependent |
| D28 | CatWISE vs CMB dipole + 3-signature interpretation | W14 + htt | **HTT + bass_py** | ch09 §9.X | 미착수 | Interpretation |

#### v3 신규 — MIO deliverable (Phase J)

| # | Deliverable | 출처 | 패키지 | Manuscript 위치 | 상태 | 비고 |
|---|---|---|---|---|---|---|
| **D29** | **Non-parametric Σ²_MIO(ℓ) extraction** | HJ-01 `mio.extraction.shear_nonparametric` | **MIO** | **ch12 §12.1** | **신규** | 모델 비가정 Σ² per ℓ. K_ℓ (bass_py atlas) 필요 |
| **D30** | ℓ-independence test for Σ²_MIO | HJ-01 | **MIO** | ch12 §12.1 | 신규 | "homogeneous shear" null 검정 χ² p-value |
| **D31** | STF shear components σ_2M from BiPoSH inversion | HJ-01 | **MIO** | ch12 §12.1 | 신규 | 5 STF component + preferred axis |
| **D32** | Cross-channel directional coherence | HJ-02 `mio.coherence.directional` | **MIO** | ch12 §12.2 | 신규 | 5 probe vector sum + isotropy p-value |
| **D33** | FLRW tension metric (PPP) | HJ-03 `mio.tension.flrw_tension` | **MIO** | ch12 §12.3 | 신규 | Posterior predictive p-value of FLRW null |
| **D34** | x_C direct estimate from data | HJ-03 `mio.tension.xc_estimator` | **MIO** | ch12 §12.3 | 신규 | x_C = Σ²−W²+Ω_tilt+Ω_{k,aniso} directly |
| **D35** | Evidence anatomy (model-indep. decomposition of ln B) | HJ-04 `mio.decomposition.evidence_anatomy` | **MIO** | ch12 §12.4 | 신규 | Channel/z-bin/parameter 별 기여 |
| **D36** | Predictive diagnostics (where models fail) | HJ-05 `mio.diagnostics.predictive_residuals` | **MIO** | ch12 §12.5 | 신규 | Model-agnostic residual atlas |
| **D37** | MioCertificate adequacy reports | HJ-05 `mio.diagnostics.adequacy_certificates` | **MIO** | ch11 §11.X | 신규 | Channel-specific, reduction-specific |
| **D38** | HTT ↔ MIO cross-validation table | `mio.interface.htt_cross_check` | **MIO** | ch12 §12.6 | 신규 | **Cross-check only, not merge (G19)** |
| **D39** | Interface contracts `{HttForwardOutput, MioCertificate, AtlasEntry}` | `workspace/contracts/*` | **contracts** | ch06 §6.7 | 신규 | DOC-03 기반 frozen dataclass |

### 0.4 시간표 요약 (외부 이벤트 정렬)

| Phase | 기간 | deliverable | 외부 이벤트 |
|---|---|---|---|
| A | Apr–May 2026 | W10-02 + HTT ZoA 재설계 (P0 3종) | — |
| B | May–Jun 2026 | W11-01~02 + HTT common 모듈 + `PreferredAxis` gate | — |
| C | Jun–Jul 2026 | W12-01~02 + HTT WLS baseline + mock calibration | — |
| D | Jul–Aug 2026 | W13-01~02 + HTT dynesty fiducial + posterior migration | — |
| E | **Aug–Sep 2026** | **W14-01 핵심 deliverable** + HTT null competition production | — |
| F | Sep–Oct 2026 | W15-01~02 + HTT bass_py bridge 정식 | Euclid DR1 (~Oct) |
| G | Oct–Nov 2026 | W15-03 + tsc 확장 + manuscript ch06/ch07 확장 | DESI DR2 |
| H | Nov–Dec 2026 | ch08/ch09 확장 + 60개 figure 최종 | — |
| I | Dec 2026–Jan 2027 | Revision + appendix + submission | — |

### 0.5 작업 총량 (정량, v3 + MIO)

| 항목 | 신규 라인 | 신규 테스트 |
|---|---|---|
| bass_py 남은 10 prompts | ~5,400 | ~600 |
| HTT common 재설계 7 모듈 | ~2,500 | ~200 |
| HTT 기존 모듈 patch (PR13AH/AJ/AM + evidence_models + pipeline) | ~800 수정 | ~80 patch |
| HTT mock calibration 스위트 | ~900 | ~60 |
| HTT scientific amplification modules (BMA, IC, Fisher, ABC, anomaly atlas) | ~3,500 | ~250 |
| **MIO package 신규 (5 subpackages, HJ-01~05)** | **~3,000** | **~250** |
| **MIO interface contracts** (`workspace/contracts/`) | **~400** | **~40** |
| tsc 확장 | ~1,500 | ~150 |
| **코드 합계** | **~18,000** | **~1,630** |
| Manuscript **core** 확장 | ≈ +70% (기존 ~15,335 L → ~26,000 L) | — |
| Manuscript **amplified + MIO ch12** 확장 | ≈ +162% (기존 ~15,335 L → **~40,200 L**) | — |
| Data products (JSON/HDF5/NPZ 전체, MIO artifacts 포함) | ~65 artifact, ~8 GB | — |

**Timeline 영향**: MIO Phase J 모듈을 Phase F~G (Sep–Nov 2026)에 삽입. Phase J는 HTT Phase I (HI-01~07) 에 의존 (HTT posterior → MIO cross-check). HJ-02 directional coherence는 **독립 실행 가능** (Phase A부터 시작).

---

## §1. Current State Inventory (detailed)

### 1.1 bass_py 서브패키지

| 서브패키지 | 주요 모듈 | 테스트 | 상태 |
|---|---|---|---|
| `bass.background` | `bianchi_types` (9 Bianchi type 구조상수), `einstein_bianchi` | ~15 | 완료 |
| `bass.closure` | `quadrupole_tca` | 94 | W6-04 완료 |
| `bass.collision` | Thomson + neutrino collision operators | ~50 | 완료 |
| `bass.los` | `flrw_bessel_projector` (W9-01), `bianchi_propagator` (W9-02) | 151 | W9 완료 |
| `bass.observational` | `planck_mes_bounds` | 80 | T_CMB, Planck D_ℓ 기준값 |
| `bass.perturbation` | Scalar/vector/tensor 섭동 변수 | 87 | 완료 |
| `bass.recombination` | `hyrec_emla`, `reionization` | 99 | R0/R2 fixture 분리 완료 |
| `bass.runtime` | `canonical_decision`, `validation_labels`, `sigma_floor` | 63 | W3 gate 완료 |
| `bass.spectrum` | `cl_assembly` (W10-01) | 63 | **Route B sentinel 완료** |
| `bass.tilt` | `baryon_only_policy`, `beta_policy_gate` | 64 | VT-07 완료 |
| `bass.transport` | multipole_hierarchy, bianchi_i_hierarchy (W5-C), shear_sources, visibility_polter_source (W8-03), emode_hierarchy (W7), dipole_driven_hierarchy (W6), baryon_fluid, cdm_fluid | 428 | W6~W8 완료 |
| `bass.validation` | `channel_routing` (TiltRouter) | 92 | W_R 라우팅 완료 |

### 1.2 tsc 서브패키지 (이미 통합)

| 서브패키지 | 모듈 | 라인 | 테스트 |
|---|---|---|---|
| `tsc.admissibility` | `realizability` | 402 | **0** (테스트 부재 — P1 복구 필요) |
| `tsc.diagnostics` | `tangency`, `species_tangency`, `entropy_invariants`, `spherical_quadrature` | 1,313 | 135 |
| `tsc.charts` | `laguerre_basis` (584), `forward_F_to_T` (379), `inverse_T_to_F` (602), `inverse_T_to_F_mc` (412), `boost_coefficients` (168), `boost_perturbative` (409) | 2,554 | 216 |

### 1.3 HTT prototype 상세 (v8.3.0)

#### 1.3.1 htt.core (18 modules, 7,906 L)

| 모듈 | 라인 | 주요 내용 |
|---|---|---|
| `ssot.py` | 184 | C class (T0_K=2.72548, Omega_m=0.3153, eta_udot=1/12 exact), eps_ell, D_ell_from_eps |
| `bounds.py` | 277 | B_sigma, B_omega, B_accel, B_sigma_corrected, Sig2_max_MES, W2_max_MES |
| `evidence_models.py` | 883 | **15개 Bianchi 모델** (FLRW, FLRW_tilt, 8 orth, 6 tilt) + chi² likelihood |
| `evidence_models_R03a.py` | 976 | R03a revision with inactive-parameter audit |
| `teff_extended.py` | 473 | B_sigma_lin, B_omega_lin, TeffMomentMap, EllMixingMatrix, EinsteinTeffODE, NonlinearCorrection, DefectPropagation |
| `tilted_flrw.py` | 398 | tilted_H_ratio, Delta_q (3-term), peculiar_jeans, velocity_growth, matter_vorticity, matter_acceleration, Omega_tilt, beta_from_colin |
| `analysis_extended.py` | 467 | FillingFraction, GrowingMode, ScenarioTable, ForecastTable, EvidenceComparison |
| `departure_posteriors.py` | 534 | DeparturePosterior class, weighted_hpd, weighted_quantile, comparator_sensitivity |
| `catalog_likelihood.py` | 605 | DistanceEngine, SyntheticCatalog, CatalogLikelihood + 3D variant, hellinger_distance, credible_cone_radius |
| `advanced_diagnostics.py` | 588 | **DepthTomography, SavageDickeyRatio, ChannelEstimate, CrossChannelCoherence, PosteriorPredictive, LeaveOneOutCV** |
| `directional_models.py` | 290 | FLRW_tilt_directional, BI_tilt_directional, DirectionalResult |
| `geometry_discrimination.py` | 430 | QuadrupoleAxisTest, ParityTest, VorticityShearContour |
| `source_discrimination.py` | 443 | DirectionalConsistencyResult, RedshiftBinnedDirection, SourceModelComparison |
| `h0_sensitivity.py` | 285 | H_0 sensitivity per model |
| `pipeline.py` | 855 | Monolithic 7-phase runner |
| `pipeline_config.py` | 32 | PipelineConfig dataclass |
| `plot_style.py` | 143 | Wong 2011 colourblind palette, 300 DPI |

#### 1.3.2 htt.infer (10 modules, 1,527 L)

| 모듈 | 라인 | 내용 |
|---|---|---|
| `control_registry.py` | 126 | ControlSpec, matched_complexity_check |
| `dipole_vector_likelihood.py` | 130 | DipoleVectorLikelihood |
| `directional_lowell.py` | 171 | angular_separation, alignment_probability, LowellLikelihood |
| `estimators.py` | 148 | tilt_velocity, delta_q, lambda_J_pec, delta_H, BridgeResult |
| `latent_axis.py` | 142 | LatentAxisParams, LatentAxisModel, dipole_projection |
| `lowz_ablation.py` | 116 | AblationResult, LowzAblation |
| `matched_complexity.py` | 182 | MatchedComplexityReport, enforce_matched_complexity |
| `null_competition.py` | 190 | NullCompetitionEngine, FamilyCompetitionResult |
| `shared_cause.py` | 78 | SharedCauseResult |
| `survey_nuisance.py` | 217 | SurveyCovariance, SurveyNuisance, combined_covariance |

#### 1.3.3 htt.nulls (6 modules, 525 L)

| 모듈 | 라인 | Null family |
|---|---|---|
| `common_interface.py` | 106 | NullDataset, NullFamilyResult, FalsePositiveRates, NullFamily (ABC) |
| `scanning_law.py` | 55 | **N1**: WISE scanning-law systematic |
| `mask_leakage.py` | 46 | **N2**: Galactic mask-leakage |
| `clustering.py` | 131 | **N3**: Clustering-dipole (Bashir-type), **N4**: Selection-response (von Hausegger-Dalang), **N5**: Survey-axis |
| `runner.py` | 156 | run_family, run_null_library |

#### 1.3.4 기타 서브패키지

| 서브패키지 | 라인 | 내용 |
|---|---|---|
| `htt.bridge` | 146 | estimators, metadata, runner — bass bridge exploratory |
| `htt.integration` | 126 | `from_bass.py` (BASSDirectionalBundle ingest), `to_mio.py` (PosteriorExportBundle) |
| `htt.tilt` | 66 | TiltHistory, SpeciesRelativeTilt |
| `htt.figures` | 5,026 | **27 figure generation scripts** |

#### 1.3.5 HTT 27개 figure scripts

| # | Script | 주제 | 데이터 의존 |
|---|---|---|---|
| 1 | `fig_3D_constraint_volume` | 3D 제약 공간 시각화 | none |
| 2 | `fig_4D_projection_atlas` | 4D projection atlas | none |
| 3 | `fig_MES_three_bounds` | **B_σ, B_ω, B_u̇ 계층** | none |
| 4 | `fig_cf4pp_sensitivity` | CF4++ 감도 분석 | none |
| 5 | `fig_certification_matrix` | Certification matrix | none |
| 6 | `fig_channel_ablation_heatmap` | Channel ablation | robustness_sweeps |
| 7 | `fig_colin_beta` | **Colin et al. β 제약** | none |
| 8 | `fig_departure_summary` | **x/Q/Π departure 요약** | FLRW_tilt_results |
| 9 | `fig_direction_posterior` | **dipole direction posterior** | none |
| 10 | `fig_equiv_class_evidence` | 동치류 evidence | none |
| 11 | `fig_evidence_decomposition` | **evidence channel 분해 (b/c/d/e/f/g/h)** | FLRW_tilt_results |
| 12 | `fig_experiment_timeline` | 실험 타임라인 | none |
| 13 | `fig_identified_reporting_split` | Identified/reporting 분리 | none |
| 14 | `fig_nonlinear_heatmap_vorticity_accel` | 비선형 vorticity/acceleration heatmap | none |
| 15 | `fig_peculiar_jeans` | Peculiar Jeans length | none |
| 16 | `fig_q0_pushforward` | **q_0 pushforward** | FLRW_tilt_results |
| 17 | `fig_q_decomposition` | 감속파라미터 분해 | none |
| 18 | `fig_repo_architecture` | repo 아키텍처 | none |
| 19 | `fig_rho_sweep` | Prior width sweep | robustness_sweeps |
| 20 | `fig_scale_hierarchy` | Scale hierarchy | none |
| 21 | `fig_sigma_accel_contour` | **σ-u̇ contour** | none |
| 22 | `fig_sigma_omega_contour` | **σ-ω contour** | none |
| 23 | `fig_status_architecture` | Status architecture | none |
| 24 | `fig_tilted_H0_depth` | tilted H_0 깊이 프로파일 | none |
| 25 | `fig_tilted_dictionary` | tilted 우주 사전 | none |
| 26 | `fig_type_by_type_summary` | **type-by-type 요약 (orth × tilt)** | none |
| 27 | `fig_v_pushforward` | velocity pushforward | FLRW_tilt_results |
| 28 | `fig_vorticity_hierarchy` | vorticity hierarchy | none |

#### 1.3.6 HTT 15개 Bianchi evidence models

| 그룹 | 모델 |
|---|---|
| Null | FLRW |
| Tilted base | FLRW_tilt |
| Orthogonal (8) | BianchiI_orth, BianchiVII0_orth, BianchiII_orth, BianchiVI0_orth, BianchiVIII_orth, BianchiIX_orth, BianchiVIIh_orth, BianchiVIIh_orth_grow |
| Tilt (6) | BianchiI_tilt, BianchiV_tilt, BianchiIII_tilt, BianchiIX_tilt, BianchiVIIh_tilt, BianchiVIIh_tilt_grow |

#### 1.3.7 HTT 5개 null families

| Family | Class | 모사 내용 |
|---|---|---|
| **N1** | `ScanningLawNull` | WISE scanning pattern → ecliptic-pole dipole (Bashir+2025 SBI) |
| **N2** | `MaskLeakageNull` | Galactic mask leakage, σ inflation |
| **N3** | `ClusteringDipoleNull` | Local LSS clustering dipole |
| **N4** | `SelectionResponseNull` | Redshift-dependent selection function (von Hausegger-Dalang 2025) |
| **N5** | `SurveyAxisNull` | CatWISE-Radio shared ecliptic/declination systematics |

#### 1.3.8 HTT 관측 시나리오 (figures 및 pipeline에서 사용)

| Scenario | ε_1 | 출처 |
|---|---|---|
| S1 | 1.233 × 10⁻³ | Ferreira-Quartin (standard CMB kinematic dipole) |
| S2 | 1.476 × 10⁻³ | CatWISE 2020 (Secrest et al.) |
| S2b | 2.096 × 10⁻³ | Intermediate |
| S2c | 2.586 × 10⁻³ | NVSS + RACS |
| S3 | 3.296 × 10⁻³ | Böhme+2025 |

### 1.4 MIO 현재 상태 (신규 패키지)

#### 1.4.1 이미 존재하는 MIO 관련 파일

| 파일 | 현 위치 | 역할 | 재배치 |
|---|---|---|---|
| `PR13AM_te_sign_d1d3_bridge.py` | `src/mio/` | TE-sign D1/D3 bridge (model-independent 패턴) | **유지** — MIO의 legitimate bridge, 단 §6.1 P0 patch 필요 |

PR13AM은 TE channel에서 D_1/D_3 sign 패턴 (모델 비가정 진단)을 검사하므로 MIO 소유가 적절하다. 단 v2에서 지적한 uniform fallback 문제는 §6.1 patch로 해결.

#### 1.4.2 신규 작성 필요 (Phase J)

| 모듈 | 라인 | 내용 | 프롬프트 |
|---|---|---|---|
| `mio.extraction.shear_nonparametric` | ~500 | Σ²_MIO(ℓ) + STF decomposition | HJ-01 |
| `mio.extraction.tilt_nonparametric` | ~300 | β²_MIO(ℓ) (신규 추가) | HJ-01b |
| `mio.extraction.biposh_inversion` | ~300 | σ_2M from BiPoSH | HJ-01 |
| `mio.coherence.directional` | ~350 | DirectionalProbe + resultant | HJ-02 |
| `mio.coherence.redshift_binned` | ~250 | z-binned coherence | HJ-02b |
| `mio.tension.flrw_tension` | ~400 | PPP + FLRW null | HJ-03 |
| `mio.tension.xc_estimator` | ~250 | x_C direct from data | HJ-03b |
| `mio.decomposition.evidence_anatomy` | ~500 | ln B 분해 | HJ-04 |
| `mio.decomposition.redshift_tomography` | ~300 | per-z evidence | HJ-04b |
| `mio.diagnostics.predictive_residuals` | ~400 | model-agnostic residuals | HJ-05 |
| `mio.diagnostics.adequacy_certificates` | ~350 | `MioCertificate` generator | HJ-05 |
| `mio.diagnostics.masked_sky_caveats` | ~250 | sky caveat tracking | HJ-05 |
| `mio.interface.mio_certificate` | ~200 | `MioCertificate` dataclass | HJ-05 |
| `mio.interface.htt_cross_check` | ~350 | MIO ↔ HTT cross-check (not merge) | HJ-06 |
| `mio.bridges.*` (PR13AM 등) | ~300 | bridge modules | HJ-07 |
| **합계** | **~5,000 L** | (초기 추정 3,000 상향, 세부 분할 반영) | |
| Tests | ~350 | pass criteria per module | |

#### 1.4.3 MIO는 certification gatekeeper가 아니다 (v2 오해 교정)

v2 문서에서 MIO를 "epistemic control / post-hoc certification"으로 잘못 기술. v3 교정:

| 오해 (v2) | 교정 (v3) |
|---|---|
| MIO가 "claim tier 강제" 담당 | **NO**. 각 모듈이 스스로 claim tier 자체 태그 |
| MIO가 "adversarial audit logs" 저장소 | **NO**. Per-package test suites가 이를 담당 |
| MIO가 "publication gate" 결정 | **NO**. Publication gate는 `src/common/contracts.py`의 `PreferredAxis.production_allowed` + per-module V-gate |
| MIO가 "scope guard registry" | **NO**. `OutOfScopeError` raise는 각 모듈 자체 |
| MIO가 "Rung 0→4 ladder 관리" | **NO**. Ladder 상태는 각 prompt packet에 기록 |
| MIO = **physics-producing observatory** | **YES**. 비모수 Σ², directional coherence, FLRW tension, evidence anatomy, predictive diagnostics |

**원리 (DOC-03 III-4.1)**: MIO owns the *model-independent or weakly model-structured diagnostic side*: extraction of departures from baseline / diagnostic certification / semantic reporting / tension or anomaly decomposition / cross-checks against theory families **without collapsing into them**.

---

## §2. bass_rs 와의 Scope 경계 (v1 유지)

### 2.1 능력 매트릭스

| 능력 | bass_py (Python) | bass_rs (Rust, 별도) |
|---|---|---|
| ℓ 범위 | ≤ 30 (low-ℓ 특화) | ≤ ~2000 (production CAMB 동등) |
| 스펙트럼 | TT, EE | TT, TE, EE, BB |
| Scalar mode evolution | **없음** (caller-supplied callable) | 완전 구현 |
| Bianchi 배경 | Type I 1차, m∈{0,±2} | Type I (비선형 포함) |
| 정확도 | 축소 scope 내 엄밀 + FLRW CAMB 일치 | 프로덕션 validator |
| Direction likelihood | **htt 서브패키지** | — |

### 2.2 반드시 Python 측에서 닫히는 것

1. Route B M-M lookup sentinel (**완료**)
2. 3-signature discriminator (W14-01) — **HTT**
3. Direction likelihood generator with ZoA (htt 재설계) — **HTT**
4. 15-model Bianchi evidence (htt prototype 안정화) — **HTT**
5. Null competition FPR (htt) — **HTT**
6. Mock calibration (htt 신규) — **common/HTT**
7. **Non-parametric Σ²_MIO(ℓ) extraction** (Phase J HJ-01) — **MIO**
8. **Cross-channel directional coherence** (HJ-02) — **MIO**
9. **FLRW tension metric + x_C direct estimator** (HJ-03) — **MIO**
10. **Evidence anatomy + predictive diagnostics** (HJ-04~05) — **MIO**
11. **HTT ↔ MIO cross-validation reports** — **MIO** (not merge)
12. Manuscript-ready 결과 스크립트

### 2.3 반드시 Rust 측에 남기는 것

1. 첫 원리 D_2 = 0.1741 μK² 재현
2. Full ℓ ≤ 2000 정밀도
3. Bianchi VIIh/IX full polarization rotation
4. Tilted Bianchi (ω_a ≠ 0)
5. 비선형 Σ 영역 (Σ² > 10⁻⁴)

### 2.4 인터페이스 (bass_py ↔ bass_rs)

| 방향 | 객체 | 상태 |
|---|---|---|
| rs → py | `BianchiTransferFunctions(k)` via JSON/CSV | **스펙 확정**, bass_rs 측 미구현 |
| py → rs | Route B (C_1, C_2) SSOT | **완료** |
| Bridge | Anti-regression guard (0.5% rtol) | **완료** — `assert_d2_anti_regression_vs_route_b` |

---

## §3. HTT ZoA 재설계 — 진단 및 방침

### 3.1 현재 상태 진단

#### 3.1.1 문제점 정리

| # | 파일 | 문제 | 심각도 |
|---|---|---|---|
| 1 | `PR13AH_observables_reintegration.py` | direction posterior를 `mean(l), mean(b)` raw로 요약 (sphere 상의 잘못된 평균) | P0 |
| 2 | `PR13AM_te_sign_d1d3_bridge.py` | directional weights 전부 0이면 **uniform fallback**을 조용히 적용 | P0 |
| 3 | `PR13AJ_full_a2m_restoration.py` | ZoA-20° diagnostic axis가 그대로 `a20 → full a2m` 회전에 사용 | P0 |
| 4 | `FLRW_tilt_zoa20_mean` | downstream **default axis**로 박혀 있음 | P0 |
| 5 | ZoA summary 로직 | artifact에만 존재, reproducible source 없음 | P1 |
| 6 | Angular completeness | 부재 — hard cut만 있음 | P1 |
| 7 | Mock calibration | 완전 부재 | P2 |
| 8 | `weights_all_zero_replaced_by_uniform` 필드 | 상태 표시가 혼란 (False 반복 출현) | P2 |

#### 3.1.2 합당한 부분 (유지)

- `|b| < b_cut` 절제로 plane alignment 민감도 진단
- 0 / 5 / 10 / 15 / 20 / 25 / 30° grid ablation
- Retention fraction + cross-model separation 기준
- 이 모든 것은 **진단 계층**으로 유지

#### 3.1.3 합당하지 않은 부분 (수정 대상)

- Uniform fallback을 production-like summary에 섞는 것
- ZoA 20°를 "preferred axis 기본값"으로 사용
- Angular cut만 있고 completeness/selection/mock이 없는 상태
- Data와 model에 같은 sky support를 강제하지 않은 채 directional 비교

### 3.2 재설계 원칙 (5개)

1. **진단 ≠ 추론**: 두 계층은 label과 gate로 완전히 분리
2. **Uniform fallback은 진단 전용**: production mode에서는 **예외 발생**
3. **sphere 평균은 단위벡터 기반**: `mean(l), mean(b)`는 영구 금지
4. **Sky support 일치**: data와 model에 같은 mask를 강제
5. **Mock calibration 의무**: null/injected mocks에 같은 mask/weight 적용 후 recovered bias + coverage 측정

### 3.3 컨벤션 고정

| 항목 | 값 |
|---|---|
| 좌표계 | Galactic (l, b) — astropy.coordinates로 변환 보장 |
| Velocity 단위 | km/s (β = V/c 변환은 최종 단계만) |
| Sky pixelization | HEALPix (NSIDE 결정은 §3.4) |
| ZoA mask 층위 | 3 tier: hard cut / completeness / mock calibration |
| Likelihood | Gaussian with σ_i,eff² = σ_i² + σ_*² |
| Posterior engine | dynesty (nlive=1200, sample='rwalk' for ndim≤4, resample_equal) |

### 3.4 HEALPix 해상도 결정

| NSIDE | N_pix | θ_pix | 용도 |
|---|---|---|---|
| 32 | 12,288 | 1.83° | Coarse mask bookkeeping |
| 64 | 49,152 | 0.92° | Angular completeness 추정 |
| 128 | 196,608 | 0.46° | CF4++ source density 스무딩 |
| 256 | 786,432 | 0.23° | posterior direction 시각화 |

**권장 기본값**: NSIDE=64 for completeness, NSIDE=128 for catalog binning, NSIDE=256 for final direction map.

### 3.5 Three-Layer 개념 분류 (ZoA review 반영)

Mode 0/1/2의 운영 분리와는 별도로, **코드 전체를 세 개의 개념 계층으로 라벨링**한다. 모든 함수 docstring과 artifact 파일명에 이 라벨 중 하나가 들어가야 한다.

| Layer | 목적 | Uniform fallback | 라벨 | artifact 접두 |
|---|---|---|---|---|
| **Diagnostic** | mask sensitivity, plane alignment control | **허용** (라벨 필수) | `diagnostic_only` | `diag_` |
| **Inference** | selection-aware directional likelihood + posterior | **금지** (production_mode → RuntimeError) | `inference` | `inf_` |
| **Downstream synthesis** | fiducial posterior → axis → `a_ℓm` 회전 복원 | 해당 없음 (gate만) | `synthesis_gated` | `synth_` |

#### 3.5.1 Layer 간 데이터 흐름 규칙

```
[Diagnostic artifact]  ─── (승격 금지) ───✗   [Production axis]
    │
    └── (Mode 0 lat-cut ladder만 허용) ──→ [Operational config 힌트]

[Inference posterior]  ─── (gate 통과 시) ───✓   [Production axis]
    │                                             │
    └── (Layer C dynesty 통과 + mock coverage OK)  └── PR13AJ a_2m 복원 허용
```

### 3.6 Constants 명명 규칙 (review 핵심 지적)

`FLRW_tilt_zoa20_mean`과 같은 diagnostic 안정화값을 production default로 쓰지 않기 위해, 상수는 **세 가지 이름으로 분리**한다.

| 상수 이름 패턴 | 의미 | 허용 사용처 |
|---|---|---|
| `recommended_zoa_half_angle_deg` | 문헌/경험적으로 권장되는 cut (예: 10°) | 문서 참조용 |
| `operational_default_zoa_half_angle_deg` | 진단 ladder 운영 기본값 (예: 20°) | Mode 0 diagnostic 기본 |
| `production_default_axis` | Mode 2 fiducial 통과한 axis | **None이 기본**, 조건부 할당 |

**금지 패턴**: `FLRW_tilt_zoa20_mean`을 any downstream default로 박는 모든 코드.

### 3.7 Weight composition 강제 규칙

모든 directional weight는 **세 요소의 곱**으로 분해되어 artifact에 저장되어야 한다.

$$w_i^{\rm total} = w_i^{\rm native} \times w_i^{\rm selection} \times w_i^{\rm measurement}$$

| 요소 | 의미 | 담당 모듈 |
|---|---|---|
| `w_native` | catalog 원본 weight (survey-reported) | catalog ingest |
| `w_selection` | completeness 기반 inverse-weight | `healpix_selection.compute_selection_weights` |
| `w_measurement` | $1/\sigma_{i,\rm eff}^2$ inverse-variance | `bulkflow_estimator` |

각 요소는 **별도로 로그**되어야 mock calibration이 재현 가능.

### 3.8 Reproducibility gap (review 지적)

| gap 종류 | 현상 | 조치 |
|---|---|---|
| ZoA summary provenance | artifact에는 결과만 있고 재생성 소스 path 불명확 | P1: `src/common/healpix_selection.py` + `src/common/mock_calibration.py`에 모든 로직 이주 |
| `weights_all_zero_replaced_by_uniform: False` 반복 | provenance flag의 의미가 혼란 | P2: flag를 `fallback_status: 'native_weights' \| 'uniform_fallback_diagnostic_only' \| 'error_in_production'` 로 대체 |
| ZoA ladder 출력 다중 버전 | diag / operational / production 섞임 | P2: 파일명 접두 `diag_` / `baseline_` / `fiducial_` 강제 |

---

## §4. HTT 4-Layer CPU Architecture

### 4.1 Layer 구조

| Layer | 이름 | 입력 | 출력 | 주 라이브러리 |
|---|---|---|---|---|
| A | **Sky geometry / support** | catalog (l, b, d, v, σ) | pixel id, ZoA mask, completeness map, usable mask | `healpy`, `astropy.coordinates` |
| B | **Fast estimator** | catalog + weights | WLS bulk-flow V̂, covariance | `numpy`, `scipy.linalg` |
| C | **Fiducial Bayesian** | catalog + full config | posterior samples + evidence | `dynesty` |
| D | **Downstream synthesis** | fiducial posterior | axis summary, a_ℓm restoration | (gated by `production_allowed`) |

### 4.2 Layer별 모듈 매핑

#### Layer A: Sky geometry / support

| 모듈 (신규) | 함수 | 서명 |
|---|---|---|
| `src/common/sky_geometry.py` | `lb_to_unitvec` | `(l_deg, b_deg) → (N, 3)` |
| | `unitvec_to_lb` | `(vec) → (l_deg, b_deg)` |
| | `spherical_mean` | `(l_deg, b_deg, w) → {l_mean, b_mean, resultant_R}` |
| | `angular_separation_matrix` | `(l, b) → (N, N)` |
| `src/common/healpix_selection.py` | `build_zoa_mask` | `(l_deg, b_deg, bcut_deg, nside) → mask_pix` |
| | `build_angular_completeness` | `(l_deg, b_deg, nside, smooth_sigma_pix) → C_pix` |
| | `compute_selection_weights` | `(l, b, M_pix, C_pix) → w_sel` |
| | `posterior_density_map` | `(l_samples, b_samples, nside) → density_pix` |

#### Layer B: Fast WLS estimator

| 모듈 | 함수 | 서명 |
|---|---|---|
| `src/common/bulkflow_estimator.py` | `wls_bulk_flow` | `(n_hat, u, w) → (V_hat, cov)` |
| | `bulk_flow_with_mask_ladder` | `(catalog, bcut_list) → per-cut V_hat` |
| | `bootstrap_covariance` | `(catalog, n_boot) → bootstrap cov` |

핵심 공식:

$$\mathbf{A} = \sum_i w_i\, \hat{n}_i \hat{n}_i^\top, \quad \mathbf{b} = \sum_i w_i\, u_i\, \hat{n}_i, \quad \hat{\mathbf{V}} = \mathbf{A}^{-1} \mathbf{b}$$

where $w_i = w_{\rm sel,i} / (\sigma_i^2 + \sigma_*^2)$.

#### Layer C: Fiducial Bayesian inference

| 모듈 | 함수 / 클래스 | 서명 |
|---|---|---|
| `src/common/bulkflow_likelihood.py` | `BulkFlowLikelihood` | class with `log_likelihood(theta)` |
| | `prior_transform` | `(u_cube) → theta` (dynesty API) |
| | `run_dynesty` | `(likelihood, prior, config) → DynestyResult` |

기본 likelihood:

$$u_i^{\rm model} = \mathbf{V} \cdot \hat{n}_i, \quad \sigma_{i,\rm eff}^2 = \sigma_i^2 + \sigma_*^2$$

$$\ln \mathcal{L} = -\frac{1}{2} \sum_i \left[ \frac{(u_i - u_i^{\rm model})^2}{\sigma_{i,\rm eff}^2} + \ln(2\pi \sigma_{i,\rm eff}^2) \right]$$

Parameters: θ = (V_x, V_y, V_z, σ_*, optionally α_C, f_out)
Priors: V_x, V_y, V_z ∈ U(-1500, 1500) km/s; σ_* ∈ U(0, 500) km/s

#### Layer D: Downstream synthesis

| 모듈 | 함수 | 역할 |
|---|---|---|
| `src/common/posterior_summary.py` | `samples_to_lb_posterior` | posterior → (l, b) samples |
| | `credible_cone` | `(l_samples, b_samples, level) → cone_radius` |
| | `hpd_region` | HEALPix HPD |
| | `axis_from_posterior` | posterior → `PreferredAxis(production_allowed=True)` |

### 4.3 Contracts module

| 모듈 (신규) | 내용 |
|---|---|
| `src/common/contracts.py` | `PreferredAxis`, `SkySelectionConfig`, `DirectionalSummary`, `DynestyResult` dataclasses |
| | 모든 downstream 모듈이 이 dataclass 계약만 본다 (validation + gate 포함) |

---

## §4.5 MIO Architecture — Model-Independent Observatory

### 4.5.1 Mission statement

MIO (Model-Independent Observatory)는 네 번째 기둥이자 **physics-producing observatory**다. 5개 subpackage로 구성되며, 각 모듈은 **Bianchi type을 가정하지 않고** 데이터로부터 직접 물리량을 측정한다.

| Subpackage | 핵심 질문 |
|---|---|
| `mio.extraction` | "데이터에 Σ²/H가 얼마나 있나, 모델 가정 없이?" |
| `mio.coherence` | "여러 probe가 같은 방향을 가리키나, 모델 없이?" |
| `mio.tension` | "FLRW에서 얼마나 벗어났나, 어떤 alternative도 가정하지 않고?" |
| `mio.decomposition` | "HTT의 ln B를 물리적으로 어떻게 쪼갤 수 있나?" |
| `mio.diagnostics` | "어느 ℓ에서 어떤 모델이 실패하나? Model-agnostic residual은?" |

**MIO는 posterior를 생성하지 않는다.** `MioCertificate` (진단 보고서) 만 생성한다.

### 4.5.2 Interface objects (DOC-03 기준)

| 객체 | 정의 | 소유 | 금지 해석 |
|---|---|---|---|
| `HttForwardOutput` | model-dependent theory-prediction bundle (BASS → HTT) | HTT | observational data로 취급 금지; adequacy 자체 certificate로 취급 금지 |
| `MioCertificate` | model-independent diagnostic report | MIO | HTT posterior sample로 취급 금지; truth certificate로 취급 금지; HTT evidence와 단일 score로 합산 금지 |
| `AtlasEntry` | theory atlas / interpolation lookup | BASS/HTT/MIO 공유 | empirical data로 취급 금지; atlas membership만으로 posterior 의미 추론 금지 |

#### 4.5.2.1 `MioCertificate` dataclass

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass(frozen=True)
class MioCertificate:
    """Model-independent diagnostic report. NOT a posterior, NOT a truth certificate."""
    # Identification
    report_type: str                       # 'shear_extraction' | 'directional_coherence' | 'flrw_tension' | ...
    probe_name: str                        # 'Planck_TT' | 'CatWISE' | 'CF4pp' | ...
    channel: str                           # 'low_ell' | 'biposh' | 'dipole' | ...

    # Diagnostic quantities (not model parameters)
    departure_variables: Dict[str, float]  # e.g., {'Sigma2_median': 1.2e-8, 'Sigma2_sigma': 4e-9}
    adequacy_indicators: Dict[str, bool]   # e.g., {'ell_independence_p_gt_0p05': True}
    consistency_metrics: Dict[str, float]  # e.g., {'chi2_per_dof': 1.02}

    # Caveats
    domain_caveats: List[str]              # ['masked_sky_partial', 'valid_only_below_ell_30']
    channel_caveats: List[str]
    reduction_status: str                  # 'theory-direct' | 'theory-approximate' | 'diagnostic-only'

    # Provenance
    generated_by: str                      # module version
    git_commit: str
    config_hash: str
    input_data_hashes: List[str]

    # Cross-check hints (not posteriors!)
    htt_cross_check_suggested: Optional[Dict[str, str]] = None
    # 예: {'compare_to': 'htt.evidence_models.BianchiI_tilt.Sigma2_posterior',
    #      'expected_relation': 'Sigma2_MIO within 2sigma of Sigma2_HTT_median'}

    def as_posterior_bundle(self):
        """이 method는 절대 구현되면 안 됨 — MIO는 posterior를 생성하지 않음."""
        raise NotImplementedError(
            "MioCertificate is a diagnostic report, not a posterior. "
            "Use HTT's PosteriorExportBundle for posterior operations."
        )
```

### 4.5.3 MIO 5 subpackage 상세

#### 4.5.3.1 `mio.extraction` — 비모수 kinematic 측정

| 모듈 | 주요 함수 | 입력 | 출력 |
|---|---|---|---|
| `shear_nonparametric.py` | `extract_Sigma2_per_ell(cl_obs, cl_lcdm, K_ell)` | 관측 C_ℓ + ΛCDM 예측 + BASS kernel K_ℓ | `(ell, Sigma2, sigma)` per ℓ |
| ↑ | `weighted_average_Sigma2` | per-ℓ extraction | `(Sigma2_best, chi2_consistency)` + **ℓ-independence p-value** |
| ↑ | `extract_sigma_2M(biposh_obs, cl_obs, alpha_D)` | BiPoSH A^{2M} + C_ℓ + Sobolev factor | 5 STF shear components |
| ↑ | `shear_direction(sigma_2M)` | 5 STF | `(l_gal, b_gal, cone_radius)` |
| `tilt_nonparametric.py` | `extract_beta2_per_ell` | 관측 low-ℓ TT + tilt transfer | β²_MIO(ℓ) per scenario |

**핵심 공식 (HJ-01)**:

$$\Sigma^2_{\rm MIO}(\ell) = \frac{C_\ell^{\rm obs} - C_\ell^{\Lambda{\rm CDM}}}{K_\ell}$$

- **FLRW null**: 모든 ℓ에서 Σ²_MIO ~ 0 (cosmic variance 내)
- **Bianchi injection**: 모든 ℓ에서 같은 값 (ℓ-independence p > 0.05)
- **Misspecification signal**: ℓ마다 다르면 model misspecification

#### 4.5.3.2 `mio.coherence` — Cross-probe directional statistics

| 모듈 | 역할 |
|---|---|
| `directional.py` | `DirectionalProbe(name, l, b, sigma_cone, weight)` dataclass; `resultant_vector`, `isotropy_pvalue` (Fisher distribution), `pairwise_separations`, `coherence_chi2` |
| `redshift_binned.py` | z-bin별 probe direction + drift rate |

**표준 probes** (hardcoded): CMB dipole, CatWISE, Radio (NVSS+RACS), CF4++, Planck BiPoSH.

**원리**: 완전히 frequentist + model-independent. "모든 probe가 같은 축을 가리키나?" 에 대한 p-value. HTT posterior와는 **별도 보고**.

#### 4.5.3.3 `mio.tension` — FLRW null 정량화

| 모듈 | 역할 |
|---|---|
| `flrw_tension.py` | `posterior_predictive_pvalue(data, flrw_model, test_stat, N_mock)` — FLRW mock과 data 비교; test statistics: T_directional, T_biposh, T_isotropy_per_ell |
| `xc_estimator.py` | `departure_parameter_estimate(data, transfer)` → `(x_C, sigma_x)` 직접 추정; FLRW 예측: x_C = 0 |

**원리**: "얼마나 FLRW에서 벗어났나?" 를 어떤 alternative도 가정하지 않고 측정. look-elsewhere correction 필수. HTT BF와 **대조 보고**, 합산 금지.

#### 4.5.3.4 `mio.decomposition` — Evidence anatomy

| 모듈 | 역할 |
|---|---|
| `evidence_anatomy.py` | Channel-by-channel Δln B (HI-05 기반); redshift-bin decomposition (recomb / post-recomb / reion); parameter decomposition (shear / tilt / spatial curvature); I(data; θ_i \| channel_j) information matrix; evidence flow diagram |
| `redshift_tomography.py` | per-z evidence slicing |

**원리**: HTT가 이미 생성한 ln B를 **model-independent analysis of model-dependent results** 로 쪼갠다. 분해 자체는 어떤 Bianchi type도 가정하지 않음.

**Consistency check**: Σ_channels Δln B ≈ total ln B (interaction terms ~ 10% 내)

#### 4.5.3.5 `mio.diagnostics` — Predictive residuals + adequacy

| 모듈 | 역할 |
|---|---|
| `predictive_residuals.py` | 어떤 모델에서 어느 ℓ/channel이 실패하나? Model-agnostic residual atlas |
| `adequacy_certificates.py` | `MioCertificate` 생성기 |
| `masked_sky_caveats.py` | Sky coverage + mask propagation 추적 |

### 4.5.4 MIO ↔ HTT Hard separation rule (G19)

**Allowed** (DOC-03 III-5.2):
- Cross-check HTT posteriors against MIO departures
- Compare predictive theory objects to MIO extraction products
- MIO diagnostics를 HTT workflow의 warning / filter / interpretive context로 사용

**Not allowed**:
- HTT posterior evidence와 MIO certificate score를 하나의 master score로 합산
- MIO output을 HTT likelihood term으로 relabel
- MIO validity를 model truth의 증명으로 해석

### 4.5.5 MIO 출력 → manuscript 흐름

| MIO module | manuscript | ch/section |
|---|---|---|
| `shear_nonparametric` + `biposh_inversion` | ch12 §12.1 "Non-parametric shear extraction" |
| `coherence.directional` | ch12 §12.2 "Cross-channel directional coherence" |
| `flrw_tension` + `xc_estimator` | ch12 §12.3 "FLRW tension metric and x_C estimate" |
| `evidence_anatomy` | ch12 §12.4 "Evidence anatomy (what drives ln B)" |
| `predictive_residuals` | ch12 §12.5 "Predictive diagnostics" |
| `htt_cross_check` | ch12 §12.6 "HTT ↔ MIO cross-validation summary" |

### 4.5.6 MIO의 신규 deliverable으로 가능해지는 것

| 주장 | 없이는 (v2 plan) | MIO 있으면 (v3 plan) |
|---|---|---|
| "데이터에서 Σ²/H가 검출되는가?" | HTT posterior만으로 답변 (model-dependent) | MIO Σ²_MIO(ℓ) 로 **model-independent 직접 답변** |
| "모든 dipole probe가 같은 축을 가리키는가?" | Ad-hoc alignment matrix | MIO `resultant_vector` + Fisher isotropy p-value |
| "FLRW이 얼마나 배제되는가?" | HTT BF만 (model-dependent) | MIO PPP + x_C direct estimate |
| "어떤 channel이 ln B를 이끄는가?" | HTT channel ablation | MIO evidence anatomy (cross-check) |
| "어느 ℓ에서 model이 실패하는가?" | HTT PPC only | MIO model-agnostic residual atlas |

---

## §5. HTT 3-Mode Operational Structure

### 5.1 Mode 정의

| Mode | 목적 | ZoA 처리 | Weight | Estimator | Fallback |
|---|---|---|---|---|---|
| **Mode 0: diagnostic** | Mask sensitivity test | Hard cut only (0~30° ladder) | Native or uniform (fallback **허용**) | WLS only | Uniform fallback OK |
| **Mode 1: analysis baseline** | 빠른 논리 검증 / regression | Hard cut + completeness weight | w_sel × w_meas | WLS + bootstrap | **금지** |
| **Mode 2: fiducial** | 논문용 최종 결과 | Hard cut + completeness + mock debiasing | w_sel × w_meas | dynesty posterior + evidence | **예외 발생** |

### 5.2 Mode별 dataclass flag 매트릭스

| `PreferredAxis` 필드 | Mode 0 | Mode 1 | Mode 2 |
|---|---|---|---|
| `source` | "raw_diagnostic" | "selection_aware" | "fiducial_posterior" |
| `weight_mode` | "uniform" or "native" | "native" (fallback 금지) | "native" + nuisance |
| `selection_mode` | "zoa_masked" | "selection_aware" | "mock_calibrated" |
| `production_allowed` | **False** | **False** | **True** |

### 5.3 Mode 전환 gate

```
Mode 0 → Mode 1: retention fraction >= 0.3 AND zoa_ladder_stable == True
Mode 1 → Mode 2: mock_coverage_68pct in [0.60, 0.76] AND mock_bias_amplitude < 5%
```

### 5.4 Mode별 artifact 분리

| Mode | JSON artifact | 사용처 |
|---|---|---|
| 0 | `diagnostic_zoa_ladder.json` | ch08 robustness, figure `fig_zoa_ladder` (신규) |
| 1 | `baseline_selection_aware.json` | ch07 중간 결과 |
| 2 | `fiducial_posterior_bundle.json` | ch07 **최종 결과** + ch09 interpretation |

---

## §6. Patch Plan — 파일별 수정안

### 6.1 `src/mio/PR13AM_te_sign_d1d3_bridge.py` (P0)

#### 현재 로직
```
_direction_weight_status():
  if weights all zero:
    → uniform fallback (조용히)
```

#### 수정안
```python
def _direction_weight_status(direction_npz, prefix, production_mode=False):
    w = np.asarray(direction_npz[f'{prefix}_dir_w'], dtype=float)
    if np.allclose(w, 0.0):
        if production_mode:
            raise RuntimeError(
                f"{prefix}: directional weights all zero; "
                f"production inference forbidden."
            )
        # Diagnostic-only path
        w = np.ones_like(w)
        fallback_status = 'uniform_fallback_diagnostic_only'
    else:
        fallback_status = 'native_weights'
    return {
        'weights': w / w.sum(),
        'fallback_status': fallback_status,
        'production_allowed': fallback_status == 'native_weights',
    }
```

### 6.2 `src/htt/PR13AJ_full_a2m_restoration.py` (P0)

#### `PreferredAxis` 확장
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class PreferredAxis:
    l_deg: float
    b_deg: float
    label: str
    # v2 신규 필드
    source: str                  # 'raw_diagnostic' | 'zoa_masked' | 'selection_aware' | 'fiducial_posterior'
    weight_mode: str             # 'uniform_fallback' | 'native' | 'native_with_nuisance'
    selection_mode: str          # 'none' | 'zoa_hard_cut' | 'angular_completeness' | 'mock_calibrated'
    production_allowed: bool = False
    provenance_hash: str = ""    # git commit + config hash
```

#### Gate 추가
```python
def restore_full_a2m(axis: PreferredAxis, a20_seed: complex) -> Dict[int, complex]:
    if not axis.production_allowed:
        raise RuntimeError(
            f"PreferredAxis (source={axis.source}, selection_mode={axis.selection_mode}) "
            f"is diagnostic-only. a20 → full a2m restoration forbidden."
        )
    # ... actual rotation
```

### 6.3 `src/htt/PR13AH_observables_reintegration.py` (P0)

#### 현재: raw mean만 계산

#### 수정: 4개 summary 분리 저장
```python
def reintegrate_observables(catalog, sky_config):
    # 1. raw: 그냥 catalog 평균 (진단 시작점)
    raw = spherical_mean(catalog.l, catalog.b, w=np.ones_like(catalog.l))
    # 2. ZoA-masked: hard cut 적용
    mask = galactic_plane_mask(catalog.b, sky_config.zoa_half_angle_deg)
    zoa_masked = spherical_mean(catalog.l[mask], catalog.b[mask],
                                 w=catalog.w[mask])
    # 3. selection-aware: completeness weight 적용
    w_sel = compute_selection_weights(catalog, healpix_completeness_map)
    selection_aware = spherical_mean(catalog.l[mask], catalog.b[mask],
                                      w=catalog.w[mask] * w_sel[mask])
    # 4. mock-calibrated: bias 교정
    mock_bias = load_mock_calibration(sky_config)
    mock_calibrated = apply_bias_correction(selection_aware, mock_bias)
    return {
        'raw_summary': raw,                      # diagnostic_only
        'zoa_masked_summary': zoa_masked,        # diagnostic_only
        'selection_aware_summary': selection_aware,  # Mode 1 baseline
        'mock_calibrated_summary': mock_calibrated,  # Mode 2 fiducial
    }
```

### 6.4 신규 모듈 (v2 Layer A~D 구현)

#### `src/common/sky_geometry.py` (~150 L)

| 함수 | 서명 | 목적 |
|---|---|---|
| `lb_to_unitvec(l_deg, b_deg)` | `(N,), (N,) → (N, 3)` | Galactic → Cartesian unit vector |
| `unitvec_to_lb(vec)` | `(N, 3) → (l_deg, b_deg)` | inverse |
| `spherical_mean(l, b, w)` | → `{l_deg, b_deg, resultant_R}` | **단위벡터 기반 평균** |
| `angular_separation_matrix(l, b)` | → `(N, N)` degrees | pairwise |
| `galactic_plane_mask(b_deg, half_angle_deg)` | → bool mask | ZoA hard cut |

#### `src/common/healpix_selection.py` (~250 L)

| 함수 | 서명 | 목적 |
|---|---|---|
| `build_zoa_mask(l, b, bcut_deg, nside)` | → pixel mask | Layer A |
| `build_occupancy_map(l, b, nside)` | → N_pix | source count per pixel |
| `build_angular_completeness(l, b, nside, smooth_sigma_pix)` | → C_pix | smoothed completeness |
| `compute_selection_weights(l, b, mask_pix, C_pix, eps=1e-6)` | → w_sel | per-source selection weight |
| `posterior_density_map(l_samples, b_samples, nside)` | → density | for `fig_direction_posterior` |
| `plot_healpix_mask(mask, title)` | → fig | visualization |

#### `src/common/bulkflow_estimator.py` (~200 L)

| 함수/클래스 | 목적 |
|---|---|
| `wls_bulk_flow(n_hat, u, w) → (V, cov)` | Fast closed-form WLS |
| `bulk_flow_mask_ladder(catalog, bcut_list)` | 0~30° 전부 돌림 |
| `bootstrap_covariance(catalog, n_boot=500)` | 신뢰 구간 |
| `ZoAResponseResult` dataclass | ladder 출력 |

#### `src/common/bulkflow_likelihood.py` (~250 L)

| 클래스/함수 | 목적 |
|---|---|
| `BulkFlowLikelihood` | dynesty에 전달하는 log_likelihood |
| `prior_transform` | U→θ, bounded priors |
| `BulkFlowConfig` | frozen dataclass |
| `run_dynesty(likelihood, prior, config)` | Layer C entry |
| `DynestyResult` dataclass | samples + evidence + diagnostics |

#### `src/common/posterior_summary.py` (~200 L)

| 함수 | 목적 |
|---|---|
| `samples_to_lb_posterior(samples)` | V-samples → (l, b) samples |
| `credible_cone(l, b, level=0.68)` | Gaussian cone radius |
| `hpd_region_healpix(l, b, level=0.68)` | HEALPix HPD |
| `axis_from_posterior(samples, level=0.5)` | posterior median → `PreferredAxis(production_allowed=True)` |
| `posterior_summary_dict(samples, evidence)` | production bundle |

#### `src/common/mock_calibration.py` (~300 L)

| 함수 | 목적 |
|---|---|
| `generate_isotropic_mock(catalog, n_mock, rng)` | null mock |
| `generate_injected_dipole_mock(catalog, V_true, n_mock)` | injected signal |
| `apply_same_mask(mock, sky_config)` | data와 동일한 mask/weight |
| `recovered_bias(true_V, estimated_V_list)` | amplitude + direction bias |
| `coverage_test(samples_list, truth, level=0.68)` | HPD coverage |
| `MockCalibrationReport` dataclass | bias + coverage + credible_radius |

#### `src/common/contracts.py` (~150 L)

| Dataclass | 필드 |
|---|---|
| `PreferredAxis` | l_deg, b_deg, label, source, weight_mode, selection_mode, production_allowed, provenance_hash |
| `SkySelectionConfig` | zoa_half_angle_deg, nside, smooth_sigma_pix, allow_uniform_fallback, production_mode |
| `DirectionalSummary` | raw, zoa_masked, selection_aware, mock_calibrated |
| `DynestyResult` | samples, logwt, logz, ncall, config |
| `MockCalibrationReport` | bias_amp, bias_direction_deg, coverage_68, credible_radius_deg |

### 6.5 파일 재배치 전체 요약

```text
src/common/                              # 신규
├── sky_geometry.py        ~150 L
├── healpix_selection.py   ~250 L
├── bulkflow_estimator.py  ~200 L
├── bulkflow_likelihood.py ~250 L
├── posterior_summary.py   ~200 L
├── mock_calibration.py    ~300 L
└── contracts.py           ~150 L
(합: ~1,500 L)

src/htt/                                 # 기존 수정
├── PR13AH_observables_reintegration.py  # 4-summary 분리
├── PR13AJ_full_a2m_restoration.py       # PreferredAxis gate
└── PR13AM_te_sign_d1d3_bridge.py        # production_mode param
```

### 6.6 SkySelectionConfig + normalize_weights (review 명시 코드)

`src/common/contracts.py`에 추가할 핵심 dataclass:

```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SkySelectionConfig:
    """모든 ZoA/selection 처리의 단일 설정 객체."""
    zoa_half_angle_deg: float
    # Review 3.5/3.6 핵심: production vs diagnostic
    allow_uniform_fallback: bool = False        # production_mode에서는 False 강제
    min_retention_fraction: float = 0.3         # Mode 0 → Mode 1 gate
    production_mode: bool = False               # 최상위 gate
    # HEALPix
    nside: int = 64
    smooth_sigma_pix: float = 1.0
    # Mock calibration
    n_mock: int = 1000
    require_mock_calibration: bool = True       # Mode 2에서 True 강제

    def __post_init__(self):
        # invariant check
        if self.production_mode and self.allow_uniform_fallback:
            raise ValueError(
                "production_mode=True and allow_uniform_fallback=True are mutually exclusive"
            )
        if self.production_mode and not self.require_mock_calibration:
            raise ValueError(
                "production_mode requires mock calibration"
            )
```

`src/common/sky_geometry.py`에 추가할 utility (review 3절 명시):

```python
import numpy as np

def normalize_weights(w: np.ndarray,
                      allow_uniform_fallback: bool = False) -> tuple[np.ndarray, str]:
    """Directional weights 정규화 + fallback 상태 라벨링.

    Returns
    -------
    w_norm : ndarray — sum=1 weights
    fallback_status : str — 'native_weights' | 'uniform_fallback_diagnostic_only' | (raise)

    Raises
    ------
    ValueError : weights가 모두 0이고 allow_uniform_fallback=False인 경우.
    """
    w = np.asarray(w, dtype=float)
    if np.allclose(w, 0.0):
        if not allow_uniform_fallback:
            raise ValueError(
                "All directional weights are zero; uniform fallback is forbidden "
                "under the current SkySelectionConfig."
            )
        w = np.ones_like(w)
        return w / w.sum(), 'uniform_fallback_diagnostic_only'
    s = w.sum()
    if s <= 0:
        raise ValueError(f"Non-positive weight sum: {s}")
    return w / s, 'native_weights'


def spherical_mean(l_deg: np.ndarray,
                   b_deg: np.ndarray,
                   w: np.ndarray) -> dict:
    """Unit-vector 기반 sphere 평균. mean(l), mean(b) 금지의 대체.

    Returns
    -------
    {'l_deg': ..., 'b_deg': ..., 'resultant_R': ...}
    """
    l = np.deg2rad(l_deg); b = np.deg2rad(b_deg)
    x = np.cos(b) * np.cos(l)
    y = np.cos(b) * np.sin(l)
    z = np.sin(b)
    vx = np.sum(w * x); vy = np.sum(w * y); vz = np.sum(w * z)
    R = np.sqrt(vx*vx + vy*vy + vz*vz)
    l_mean = np.rad2deg(np.arctan2(vy, vx)) % 360.0
    b_mean = np.rad2deg(np.arctan2(vz, np.sqrt(vx*vx + vy*vy)))
    return {'l_deg': float(l_mean), 'b_deg': float(b_mean),
            'resultant_R': float(R)}
```

### 6.7 Mock calibration 의무 서명 (review 명시)

`src/common/mock_calibration.py`에 추가할 핵심 함수:

```python
def run_zoa_null_mocks(catalog, sky_config, n_mock=1000, rng=None):
    """Null/isotropic mocks에 동일한 mask/weight 적용 후 recovered distribution.

    Returns
    -------
    MockCalibrationReport:
      - bias_amplitude_kmps : float
      - bias_direction_deg : float
      - coverage_68pct : float  (target ∈ [0.60, 0.76])
      - coverage_95pct : float  (target ∈ [0.90, 0.98])
      - credible_radius_median_deg : float
      - null_amplitude_distribution : ndarray
      - null_direction_R_distribution : ndarray
    """
    ...


def run_injected_dipole_mocks(catalog, V_true_kmps, sky_config,
                              n_mock=1000, rng=None):
    """Injected-signal mocks로 recovery bias 측정.

    Returns
    -------
    InjectedMockReport:
      - recovered_V_samples : (n_mock, 3)
      - amp_bias_fraction : float
      - direction_bias_deg : float
      - amp_spread_fractional : float
    """
    ...
```

### 6.8 PR13AM 구체 patch (review의 정확한 서명)

```python
def _direction_weight_status(direction_npz, prefix,
                             production_mode: bool = False):
    """Returns {'weights', 'fallback_status', 'production_allowed'}."""
    import numpy as np
    w = np.asarray(direction_npz[f'{prefix}_dir_w'], dtype=float)
    if np.allclose(w, 0.0):
        if production_mode:
            raise RuntimeError(
                f"{prefix}: all directional weights are zero; "
                f"production inference forbidden."
            )
        w = np.ones_like(w)
        return {
            'weights': w / w.sum(),
            'fallback_status': 'uniform_fallback_diagnostic_only',
            'production_allowed': False,
        }
    return {
        'weights': w / w.sum(),
        'fallback_status': 'native_weights',
        'production_allowed': True,
    }
```

### 6.9 Patch 우선순위 매트릭스 (review의 3대 핵심 수정)

| 우선 | 수정 | 파일 | 증가 라인 | 리스크 |
|---|---|---|---|---|
| **1순위 (P0)** | Uniform fallback을 production-mode에서 **예외** | `PR13AM_te_sign_d1d3_bridge.py` | +20 | 없음 — 기존 기본값 유지, 새 flag만 추가 |
| **2순위 (P0)** | ZoA 20° axis를 downstream default에서 제거, `PreferredAxis`에 `production_allowed` gate 추가 | `PR13AJ_full_a2m_restoration.py` | +40 | 중 — 기존 `FLRW_tilt_zoa20_mean` 사용처 검색 필요 |
| **3순위 (P1)** | ZoA summary 생성 로직을 artifact가 아닌 source (`src/common/healpix_selection.py`)로 승격 | 신규 모듈 | +250 | 중 — artifact 호환성 유지 필요 |

### 6.10 Regression test 추가 목록 (review 의무사항)

| 테스트 | 위치 | 목적 |
|---|---|---|
| `test_production_mode_rejects_uniform_fallback` | `src/common/test_sky_geometry.py` | `SkySelectionConfig(production_mode=True)` + all-zero weights → RuntimeError |
| `test_preferred_axis_gate_blocks_diagnostic` | `src/htt/test_PR13AJ_gate.py` | `production_allowed=False` → a2m 복원 거부 |
| `test_spherical_mean_vs_naive_mean_divergence` | `src/common/test_sky_geometry.py` | 극단 longitude (l≈0° / l≈360°) 데이터로 naive mean과 단위벡터 mean 불일치 확인 |
| `test_four_summary_consistency` | `src/htt/test_PR13AH.py` | raw / zoa_masked / selection_aware / mock_calibrated 4개 모두 생성 |
| `test_mock_coverage_within_bounds` | `src/common/test_mock_calibration.py` | coverage_68pct ∈ [0.60, 0.76] |
| `test_zoa_ladder_no_fallback_leak` | `src/common/test_sky_geometry.py` | Mode 0 ladder가 Mode 1/2로 누출되지 않음 |
| `test_weights_decomposition_logged` | `src/common/test_bulkflow_estimator.py` | native × selection × measurement 3요소 모두 로그됨 |

---

## §7. bass_py 남은 로드맵 (W10-02 → W15-03)

### 7.1 프롬프트 단위 전체 목록

| # | 프롬프트 | 의존 | Think | 라인 | 핵심 |
|---|---|---|---|---|---|
| 1 | W10-02 FLRW → CAMB V-gate | W10-01 | T3 | ~400 | 5% 수준 CAMB 일치 |
| 2 | W11-01 Direction-dependent C_ℓ(n̂) | W10-01, W9-02 | T3 | ~450 | 방향 의존 앵귤러 스펙트럼 |
| 3 | W11-02 BiPoSH 계수 A^{LM}_{ℓ₁ℓ₂} | W11-01 | T4 | ~500 | Wigner-3j 가중 off-diagonal |
| 4 | W11-03 Bianchi → bass_rs V2 게이트 | W11-02 | T3 | ~300 | bass_rs 완성 후 활성화 |
| 5 | W12-01 W_R window + regularity guards | R-TILT-02 | T3 | ~400 | Smoothstep C² 윈도우 |
| 6 | W12-02 Frame-attribution bias 채널 | W12-01 | T4 | ~450 | VT-07 Term 3 (16% 보정) |
| 7 | W13-01 Dynamical tilt source | W12 전체 | T4 | ~500 | β(η) 동역학 |
| 8 | W13-02 Full β → D_2 transfer | W13-01, W10-01 | T4 | ~550 | 전체 순방향 파이프라인 |
| 9 | **W14-01 3-signature separator** | W13-02, W11-02 | T4 | ~600 | **핵심 과학 deliverable** |
| 10 | W15-01 Sky geometry + ZoA handling | §6 common 완료 | T3 | ~450 | htt.common 연계 |
| 11 | W15-02 WLS + dynesty posterior | W15-01, W14-01 | T4 | ~700 | Mode 2 fiducial |
| 12 | W15-03 Mock calibration + production gate | W15-02 | T4 | ~600 | 최종 게이트 |

### 7.2 W14-01 상세 (핵심)

| 항목 | 내용 |
|---|---|
| **목적** | 관측 D_ℓ^{TT,EE}에서 세 signature를 구별 |
| **Signature 1** | Local motion $W_R v_{\rm loc}$: TT ✓, EE ✗ (Thomson isotropic in CMB frame) |
| **Signature 2** | Cosmological tilt $\bar\beta$: TT ✓, EE ✓ (Thomson scattering of tilted dipole) |
| **Signature 3** | Tilt² effective stress (6 cross-terms): TT ✓, EE ✓ scale-independent |
| **핵심 주장** | **Pure TT 로는 구별 불가 — EE가 결정적** |
| **Template 구조** | 3 × (T_ℓ^{TT}, T_ℓ^{EE}) templates |
| **Likelihood** | $\chi^2 = \sum_\ell [D_\ell^{obs} - \sum_i \alpha_i T_\ell^{i}]^2 / \sigma_\ell^2$ |
| **Prior** | α_i ≥ 0, F_Bayes = 0.093 ± 0.025 주입 가능 |
| **Output** | $(\alpha_{\rm local}, \alpha_{\rm cosmo}, \alpha_{\rm tilt²})$ + covariance |
| **Mock test** | Pure signal 복원 시 $(1,0,0)$ 등 recover, rel_err < 5% |

### 7.3 W15-01~03 (htt common 모듈 연계)

**핵심 의존성 역전**: W15 prompts는 §6의 `src/common/` 모듈이 먼저 구현되어야 한다.

| W15 prompt | 소비하는 common 모듈 |
|---|---|
| W15-01 | sky_geometry + healpix_selection |
| W15-02 | bulkflow_likelihood + posterior_summary + htt.integration.from_bass |
| W15-03 | mock_calibration + contracts (PreferredAxis gate) |

---

## §8. tsc 확장 계획

### 8.1 현재 tsc 상태 (다시 정리)

| 모듈 | 라인 | 테스트 | 상태 |
|---|---|---|---|
| `tsc.admissibility.realizability` | 402 | **0 (부재)** | P1 복구 필요 |
| `tsc.diagnostics.tangency` | 379 | 135 (4개 모듈 합산) | 완료 |
| `tsc.diagnostics.species_tangency` | 340 | ↑ | 완료 |
| `tsc.diagnostics.entropy_invariants` | 242 | ↑ | 완료, F_Bayes 추가 필요 |
| `tsc.diagnostics.spherical_quadrature` | 352 | ↑ | 완료 |
| `tsc.charts.*` (6 modules) | 2,554 | 216 | 완료 |

### 8.2 필요한 tsc 확장 (우선순위 순)

| 우선 | 모듈 | 라인 | 목적 |
|---|---|---|---|
| 1 | `tsc.admissibility.test_realizability` | ~300 | 기존 모듈 테스트 복구 (0 → 30~40개) |
| 2 | `tsc.diagnostics.filling_fraction` | ~400 | F_Bayes = E[Q \| D], Q = \|x\|/B, posterior mean |
| 3 | `tsc.diagnostics.three_bound_hierarchy` | ~350 | B_σ > B_ω > B_u̇ 검증, htt.bounds와 cross-check |
| 4 | `tsc.charts.theta4_bridge_verify` | ~250 | a₂ = 4Q + 4A² + (12/7)Q² + ... audit |
| 5 | `tsc.charts.michaelis_menten_export` | ~200 | W10-01 Route B와 SSOT 연계 |
| 6 | `tsc.integration.htt_bridge` | ~150 | htt.core.evidence_models 의 F_Bayes 일관성 확인 |

**tsc 확장 합계**: ~1,650 L + ~150 테스트

### 8.3 tsc × htt 일관성 체크 목록

| 양 | tsc | htt |
|---|---|---|
| F_Bayes | `tsc.diagnostics.filling_fraction` (신규) | `htt.core.analysis_extended.FillingFraction` |
| B_σ, B_ω, B_u̇ | `tsc.diagnostics.three_bound_hierarchy` (신규) | `htt.core.bounds` |
| Θ⁴ bridge coefficients | `tsc.charts.theta4_bridge_verify` (신규) | `htt.core.teff_extended` |
| Departure parameter x | `tsc.diagnostics.entropy_invariants` | `htt.core.departure_posteriors` |

**원칙**: tsc에서 정의, htt에서 소비. 두 값이 불일치하면 tsc 쪽이 정답.

---

## §9. 관측 데이터 통합 계획 (v2 확장)

### 9.1 데이터셋 × 스캐너 매트릭스

| 데이터셋 | CF4++ | CatWISE2020 | NVSS | RACS | Planck 2018 low-ℓ TT | Planck 2018 HFI EE | Planck SMICA map |
|---|---|---|---|---|---|---|---|
| 유형 | peculiar velocity | quasar/AGN | radio | southern radio | CMB TT | CMB EE | CMB map |
| 크기 | ~50k | ~1.9M | ~1.8M | ~2.5M | ℓ=2~30 | ℓ=30~2508 | 12·NSIDE² |
| 역할 | dipole direction + amplitude | kinematic dipole test | complementary | southern hemisphere | V-gate TT | V-gate EE | 3-signature input |
| ZoA 민감도 | 높음 (local LSS) | 중 (AGN ecliptic) | 높음 (Galactic plane) | 중 | — | — | 높음 |
| S-scenario mapping | — | S2 (ε_1=1.476e-3) | S2c (ε_1=2.586e-3) | (w/ NVSS) | S1 (ε_1=1.233e-3) | S1 | — |

### 9.2 관측 비교 타겟 값

| 양 | 값 | 출처 |
|---|---|---|
| CMB dipole amplitude | 1.2336 × 10⁻³ (ε_1_kin) | Planck 2018 / SSOT |
| CatWISE dipole amplitude | 1.55 × 10⁻² | Secrest et al. 2020 |
| NVSS+RACS dipole | ≈ 2.586 × 10⁻³ | S2c scenario |
| Böhme+2025 dipole | 3.296 × 10⁻³ | S3 scenario |
| CF4++ bulk flow (60 Mpc) | ~240 km/s | Tully et al. 2023 |
| D_2 (Planck Commander) | 225.9 μK² (obs), 1150 μK² (ΛCDM) | SSOT C.D2_obs, C.D2_LCDM |
| D_3 (Planck Commander) | 936.9 μK² (obs), 1000 μK² (ΛCDM) | SSOT |
| β̄ (this work) | 1.360 × 10⁻³ | W5-C analysis |
| F_Bayes (this work) | 0.093 ± 0.025 | Bianchi defect framework |
| ln B(FLRW_tilt) (this work) | +26.40 | evidence_models |

### 9.3 전처리 파이프라인 (v2, ZoA 재설계 반영)

| 단계 | 작업 | 모듈 | Mode |
|---|---|---|---|
| 1 | Raw catalog ingest | `htt.catalogs.*` (신규) or direct CSV | — |
| 2 | Galactic frame 변환 | `astropy.coordinates` + `sky_geometry.lb_to_unitvec` | — |
| 3 | HEALPix pixel 할당 | `healpix_selection.build_occupancy_map` | — |
| 4 | ZoA hard cut | `healpix_selection.build_zoa_mask` | 0, 1, 2 |
| 5 | Angular completeness | `healpix_selection.build_angular_completeness` | 1, 2 |
| 6 | Selection weight 계산 | `healpix_selection.compute_selection_weights` | 1, 2 |
| 7 | **Mode 0 WLS ladder scan** | `bulkflow_estimator.bulk_flow_mask_ladder` | 0 |
| 8 | **Mode 1 WLS + bootstrap** | `bulkflow_estimator` | 1 |
| 9 | **Mode 2 dynesty posterior** | `bulkflow_likelihood.run_dynesty` | 2 |
| 10 | **Mock calibration** | `mock_calibration.run_isotropic_mock` | 2 |
| 11 | **Bias correction** | `mock_calibration.apply_bias_correction` | 2 |
| 12 | Posterior summary → `PreferredAxis` | `posterior_summary.axis_from_posterior` | 2 |

### 9.4 ZoA ladder 운영 기준 (Mode 0 diagnostic)

| b_cut | retention | 용도 |
|---|---|---|
| 0° | 100% | 기준선 (진단 출발) |
| 5° | ~96% | 가벼운 cut |
| 10° | ~92% | 표준 Galactic plane 제거 |
| 15° | ~87% | 보수적 |
| 20° | ~82% | 현재 hardcoded default (제거 대상) |
| 25° | ~77% | 매우 보수적 |
| 30° | ~72% | 최대 cut |

**운영 지침**: 이 전체 사다리는 **Mode 0 diagnostic output**으로만 기록. Mode 2 production axis는 별도 mock-calibrated 결과에서 생성.

---

## §10. Cross-Package Integration

### 10.1 의존 그래프 (v3, MIO 포함)

```
                         bass_rs (외부)
                              │
                   Route B SSOT │ BianchiTransferFunctions (future)
                              │
                              ▼
  bass.spectrum.cl_assembly ──┬── bass.los.bianchi_propagator
          │                   │          │
          │                   │          ▼
          │                   │  bass.transport.*
          │                   │
          │          ┌────────┴────────┐
          ▼          ▼                 ▼
   W10-02 V-gate   W11-xx BiPoSH    W12-xx W_R
                    │                 │
                    └─────┬───────────┘
                          ▼
                    W13-xx β→D_2 transfer
                          │
                          ▼
               ╔══════════════════════╗
               ║  W14-01 discriminator ║  ← 핵심
               ╚══════════════════════╝
                          │
                    (HttForwardOutput)
                          │
          ┌───────────────┼──────────────┐
          ▼               ▼              ▼
     htt.directional  htt.integration  tsc.diagnostics
                         from_bass     (F_Bayes cross-check)
                          │
           ┌──────────────┼─────────────────────────┐
           ▼              ▼                         ▼
     src/common/A    src/common/B              MIO (Phase J)
     sky+healpix     WLS + dynesty             ╔═══════════════╗
                          │                    ║ mio.extraction ║◄─── K_ℓ (BASS)
                          ▼                    ║ mio.coherence  ║◄─── 관측 data
                    PreferredAxis              ║ mio.tension    ║◄─── HTT forward
                    (production_allowed)       ║ mio.decomp     ║◄─── HTT ln B
                          │                    ║ mio.diagnostics║
                          ▼                    ╚═══════════════╝
                  PR13AJ full a2m                     │
                  (gated)                       (MioCertificate)
                                                      │
                                                      ▼
                                   ╔══════════════════════════════╗
                                   ║ HTT ↔ MIO cross-check table  ║
                                   ║   (NOT merged into 1 score)  ║
                                   ╚══════════════════════════════╝
```

**핵심 관계**:
- **MIO는 HTT의 downstream이 아니라 병렬 observatory.** 같은 input data를 독립 소비.
- MIO `extraction`은 bass_py K_ℓ atlas만 필요 (HTT posterior 무관).
- MIO `decomposition`은 HTT ln B를 소비하지만 결과는 model-independent analysis.
- HTT의 `PosteriorExportBundle`은 cross-check의 **비교 대상**, MIO의 input이 아님.

### 10.2 패키지 간 인터페이스 객체 (v3, DOC-03 기반)

| From | To | 객체 | 정의 위치 | Hard rule |
|---|---|---|---|---|
| bass_py | htt | `HttForwardOutput` (DOC-03 III-2.1) | `workspace/contracts/bass_to_htt.py` | model-dependent theory bundle; observational data로 해석 금지 |
| bass_py | MIO | `AtlasEntry` (K_ℓ kernel, DOC-03 III-2.3) | `workspace/contracts/atlas.py` | atlas membership만으로 posterior 의미 추론 금지 |
| MIO | external | `MioCertificate` (DOC-03 III-2.2) | `mio.interface.mio_certificate` | **posterior 아님; truth certificate 아님; HTT evidence와 합산 금지** |
| htt | MIO | `PosteriorExportBundle` (**cross-check only**) | `workspace/contracts/htt_to_mio.py` | 비교 대상일 뿐, MIO가 자신의 결과에 통합 금지 |
| MIO | htt | `MioCertificate` (cross-check suggestion) | `mio.interface.htt_cross_check` | HTT는 warning/filter/interpretive context로만 사용. likelihood term으로 절대 금지 |
| tsc | htt | `FillingFractionReport` | `tsc.diagnostics.filling_fraction` | |
| src/common | htt.core | `PreferredAxis`, `DirectionalSummary` | `src/common/contracts.py` | |
| Mode 0 | Mode 1 | `ZoAResponseResult` | `bulkflow_estimator` | |
| Mode 1 | Mode 2 | `BaselineDirectionalSummary` | `PR13AH` (수정됨) | |
| Mode 2 | Downstream | `FiducialPosteriorBundle` | `posterior_summary` | |

### 10.2bis G19 (Hard Separation) 강제 매커니즘

| 검사 | 구현 위치 | 실패 시 |
|---|---|---|
| `MioCertificate.as_posterior_bundle()` 호출 | `mio.interface.mio_certificate` | `NotImplementedError` (의도적) |
| HTT likelihood가 `MioCertificate`를 직접 ingest | `htt.core.evidence_models` | type check에서 `TypeError` |
| `MioCertificate.evidence_score + HttLog BZ` 와 같은 합산 | linting rule | CI fail |
| MIO가 "posterior" 필드를 가진 output 생성 | `mio.diagnostics.adequacy_certificates` | `ValueError: MIO cannot generate posteriors` |

### 10.3 SSOT 관리

| 상수 | 위치 (v2) | 공유 |
|---|---|---|
| T_CMB_K, T_CMB_uK | `bass.observational.planck_mes_bounds` + `htt.core.ssot.C` | 동기화 필요 (현재 bass: 2.7255, htt: 2.72548) → **일관성 점검 필요** |
| Omega_m, h | `htt.core.ssot.C` (Planck 2018) | 단일 출처 |
| eps1_kin = 1.2336e-3 | `htt.core.ssot.C` | CMB kinematic dipole |
| eps2, eps3 | `htt.core.ssot.C` (Commander component-separation) | ℓ=2,3 dipole amp |
| eta_udot = 1/12 | `htt.core.ssot.C` (VT-07 exact) | w/(3(1+w)) for radiation |
| C_1, C_2 (Route B) | `bass.spectrum.cl_assembly.ROUTE_B_C1/C2` | `d2_convention.rs` mirror |
| F_Bayes | tsc (신규) → htt consumer | single output |

**SSOT 불일치 발견**: bass.observational은 T_CMB=2.7255, htt.core는 T_CMB=2.72548. 0.02 mK 차이. **Phase A 초반 정정 필요**.

---

## §11. Manuscript 확장 계획 (v2 대폭 확장)

### 11.1 전체 확장 규모 요약

| Chapter | 현 L | 목표 L | 증가 | 핵심 추가 |
|---|---|---|---|---|
| ch01 Introduction | 356 | ~700 | +97% | Tsagas killing, 3-signature 동기, htt + bass_py + tsc 삼각구조 |
| ch02 Dipole anomaly | 403 | ~800 | +99% | CatWISE vs CMB, ZoA-aware posterior, 15-model preview |
| ch03 Framework | 3,564 | ~4,700 | +32% | W_R + tilt² 6 cross-terms, R-TILT-02/03, Laguerre basis, sphere 평균 정의 |
| ch04 Bianchi bounds | 1,247 | ~1,700 | +36% | 3-bound hierarchy, F_Bayes 유도 심화, β dynamical |
| ch05 T_eff corrections | 2,474 | ~3,100 | +25% | CAMB 비교, Sobolev A1~A5, Θ⁴ bridge 정정 |
| ch06 Pipeline | 827 | **~2,500** | **+202%** | **bass_py + HTT + tsc + ZoA 재설계 + 4-layer + 3-mode** |
| ch07 Results | 1,319 | **~3,500** | **+165%** | **15-model evidence + 3-signature + direction posterior + depth tomography + …** |
| ch08 Robustness | 1,176 | **~2,200** | +87% | **5 null families + matched-complexity + survey nuisance + mock coverage + LOOCV** |
| ch09 Discussion | 1,928 | ~2,800 | +45% | CatWISE vs CMB 해석, Euclid/SO/LiteBIRD 전망, Tsagas 해석 |
| ch10 Future | 1,145 | ~1,600 | +40% | bass_rs 통합, MIO, patchy reion, 비선형 Σ, BiPoSH V2 |
| ch11 Error hierarchy | 596 | ~900 | +51% | 3-tier 재확인, validation ladder, scope guard 철학 |
| Appendices | ~300 | ~1,500 | +400% | 15-model 공식, null family 유도, dynesty config, matched-complexity 알고리즘, figure 재현 스크립트 |
| **Total** | ≈ 15,335 | **≈ 26,000** | **+70%** | — |

### 11.2 Chapter × Deliverable 매트릭스 (확장)

각 열은 "해당 deliverable의 주된 기술 위치". ✓ 핵심 추가, ◦ 보조 언급, · 간접 참조.

| Chapter | D1 evi | D2 3-sig | D3 dir posterior | D4 null FPR | D5 F_Bayes | D6 bounds | D7 β→D_2 | D8 MES audit | D9 depth tomo | D10 Savage-Dickey | D11 LOOCV | D12 PPC | D13 matched-compl | D14 nuisance | D15 geometry | D16 shared-cause | D17 Route B | D18 CAMB V | D19 BiPoSH | D20 W_R | D21 ZoA 3-mode | D22 mock cov | D23 depth sens | D24 type×type | D25 equiv class |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ch01 | ◦ | ✓ | | | | ◦ | | | | | | | | | | | ◦ | | | | ◦ | | | ◦ | |
| ch02 | · | ✓ | ✓ | | | | | | | | | | | | | | | | | | ✓ | | | | |
| ch03 | | | | | | ✓ | ✓ | | | | | | | | | | | | | ✓ | | | | | |
| ch04 | | | | | ✓ | ✓ | ✓ | | | | | | | | | | | | | | | | | | |
| ch05 | | ◦ | | | | ◦ | | | | | | | | | | | ◦ | ✓ | | | | | | | |
| ch06 | | ✓ | ✓ | ✓ | ✓ | ◦ | ✓ | ✓ | ◦ | ◦ | | | ✓ | ◦ | | | ✓ | ◦ | ✓ | ✓ | ✓ | ✓ | | | |
| ch07 | ✓ | ✓ | ✓ | | ✓ | ◦ | ✓ | | ✓ | ✓ | | | | | ✓ | | ✓ | | ✓ | | | | | ✓ | ✓ |
| ch08 | ◦ | | ◦ | ✓ | ◦ | | ◦ | ✓ | | | ✓ | ✓ | ✓ | ✓ | | ✓ | | ✓ | ◦ | ✓ | ✓ | ✓ | ✓ | | |
| ch09 | ◦ | ✓ | ✓ | ◦ | ◦ | | | ◦ | | | | | | | ◦ | ◦ | | | ◦ | ◦ | ✓ | ◦ | | ◦ | ◦ |
| ch10 | | | | | | | | | | | | | | | | | | | | | | | | | |
| ch11 | | | | ◦ | | ✓ | | | | | | | ✓ | | | | ✓ | | | | | | | | |

### 11.3 Chapter별 상세 확장 내용

#### ch01 Introduction (356 → ~700 L)

| 섹션 | 추가 내용 |
|---|---|
| §1.1 배경 | Tsagas fast-growth killing (arXiv:2603.14511) 반영, khronon 유일 잔존, DE/inflation 회의 |
| §1.2 동기 | 3-signature separator 과학적 중요성, CatWISE vs CMB 1 order 차이 |
| §1.3 thesis roadmap | bass_py (forward) + tsc (internal consistency) + htt (inference) 삼각 구조, bass_rs 경계 |
| §1.4 주요 결과 요약 | 15-model evidence, ln B(FLRW_tilt)=+26.40, β=1.360e-3, F_Bayes=0.093±0.025 preview |

#### ch02 Dipole anomaly (403 → ~800 L)

| 섹션 | 추가 내용 |
|---|---|
| §2.X CMB vs LSS dipole 텐션 | S1 vs S2/S2c/S3 scenario 분포 |
| §2.X+1 3-signature 동기 | local / cosmological / tilt² 가능성 언급 (증명은 ch07) |
| §2.X+2 ZoA 고려사항 | 왜 lat cut만으로 부족한가 — Bashir+2025, von Hausegger-Dalang |
| §2.X+3 기존 선행 연구 vs 본 연구 | Ellis, Maartens, Pontzen-Challinor, Tsagas, Clarkson 등과 본 thesis 위치 |

#### ch03 Framework (3,564 → ~4,700 L)

| 섹션 | 추가 내용 |
|---|---|
| §3.X W5-C m-channel 분해 | MChannelAmplitudes 수식 + 코드 레퍼런스 |
| §3.X+1 W_R window (R-TILT-02) | Smoothstep C² (C^{\infty} 대체), 경계 regularity 증명 |
| §3.X+2 Tilt² 6 cross-terms (R-TILT-03) | 완전 목록 + BMR mapping |
| §3.X+3 Θ⁴ bridge complete formula | a₂ = 4Q + 4A² + (12/7)Q² + (44/7)A²Q + (12/7)Q³ + (4/7)A⁴ + (16/7)A²Q² + (20/77)Q⁴ |
| §3.X+4 Laguerre basis (tsc.charts) | F↔T 변환 mathematical background |
| §3.X+5 Clarkson-Maartens killing | 2603.14511 상세 유도, khronon 유일 생존 |
| §3.X+6 Sphere mean 정의 | **단위벡터 기반 정의 명시** (v2 ZoA 재설계 근거) |
| §3.X+7 Selection-aware likelihood | w_sel × w_meas 구조, completeness 이론 |

#### ch04 Bianchi bounds (1,247 → ~1,700 L)

| 섹션 | 추가 내용 |
|---|---|
| §4.3 **3-bound hierarchy** | B_σ > B_ω > B_u̇ 수식 + htt.bounds + tsc 일관성 |
| §4.X departure parameter x_C | master identity 재확인, "departure parameter" 용어 고수 |
| §4.X+1 filling fraction F | F_Bayes = E[Q\|D], Q = \|x\|/B, posterior mean (not point est.) |
| §4.X+2 β-dynamical source | W13 결과 반영 |
| §4.X+3 MES boundary check | htt.pipeline phase 3f 결과 |

#### ch05 T_eff corrections (2,474 → ~3,100 L)

| 섹션 | 추가 내용 |
|---|---|
| §5.X W10-02 CAMB 비교 | FLRW limit 정확도, 플롯 |
| §5.X+1 Sobolev A1~A5 | validity conditions 엄밀화 (first order / angular avg / local linear / flat spectrum) |
| §5.X+2 Θ⁴ bridge 정정 | c_{A²Q}, c_{A⁴} P1 errors 수정 |
| §5.X+3 f(ω) ≡ 0 증명 | vorticity의 photon 에너지 비기여 |
| §5.X+4 teff_extended 블록 | EinsteinTeffODE, NonlinearCorrection, DefectPropagation |

#### ch06 Pipeline (827 → ~2,500 L) ★ 가장 큰 확장

| 섹션 (신규) | 내용 |
|---|---|
| §6.1 전체 아키텍처 | bass_py 12 + tsc 3 + htt 8 subpackage diagram |
| §6.2 bass_py W-stack | W3 → W10-01 체인, 각 prompt별 약술 |
| §6.3 HTT pipeline 7 phases | Data → MES → T_eff → Evidence → Statistical → Tables → Figures (+7 subphases) |
| §6.4 **4-layer CPU architecture** | Layer A/B/C/D (sky / WLS / dynesty / downstream) |
| §6.5 **3-mode operational structure** | diagnostic / baseline / fiducial, Mode 전환 gate |
| §6.6 SSOT 관리 | d2_convention.rs + obs_defaults.json + htt.ssot.C + 일관성 점검 |
| §6.7 Route B sentinel | 완료된 0.174112 μK² + anti-regression |
| §6.8 **Matched-complexity protocol** | htt.infer.matched_complexity + F-test parallel |
| §6.9 **ZoA handling** | 3 tier: hard cut / completeness / mock calibration |
| §6.10 **Mock calibration** | isotropic + injected-dipole mock, same-mask requirement |
| §6.11 Test infrastructure | 1,854 + 123 tests, regression workflow, banned vocab scan |
| §6.12 Independent verification scripts | 8-block pattern, W9-01/02/10-01 예시 |
| §6.13 Figure generation catalog | 27 HTT + ~33 신규 figures, plot_style 통일 |

#### ch07 Results (1,319 → ~3,500 L) ★ 최대 확장

| 섹션 (신규) | 내용 |
|---|---|
| §7.1 Route B sentinel | D_2(Σ²=1e-8)=0.174112 μK² (이미 완료) |
| §7.1.a M-M fitter Route B recovery | C_1, C_2 rel_err < 0.5% |
| §7.2 FLRW → CAMB V-gate | W10-02 CAMB 비교 plot |
| §7.3 W_R window profile | W12-01 결과, smoothstep C² |
| §7.4 BiPoSH coefficients | W11-02 A^{LM}_{ℓ₁ℓ₂} bar plot |
| §7.5 β → D_2 transfer function curve | W13-02, Route B와의 일치 |
| §7.6 **3-signature discriminator** | W14-01 핵심, TT vs EE 분리 figure |
| §7.6.a α_{local, cosmo, tilt²} 추정치 | 관측 데이터 fit 결과 |
| §7.7 Dipole direction posterior (Mollweide) | W15-02 + htt Mode 2 fiducial |
| §7.7.a HPD cone radius per scenario | S1, S2, S2c, S3 비교 |
| §7.8 15-model Bianchi evidence | 15 × 5 scenario 테이블 + ranking figure |
| §7.8.a Evidence decomposition per channel | b/c/d/e/f/g/h channels |
| §7.9 Filling fraction F_Bayes | 재검증 0.093 ± 0.025 + scan |
| §7.10 Depth tomography | z-bin별 direction + amplitude |
| §7.11 Savage-Dickey ratios | 각 hypothesis test (FLRW_tilt vs FLRW, Bianchi vs FLRW 등) |
| §7.12 Geometry discrimination | Quadrupole axis + parity tests |
| §7.13 Type-by-type summary | 8 orth × 6 tilt matrix |
| §7.14 Equivalence class evidence | orth vs tilt 클래스 단위 Bayes factor |
| §7.15 Tilted-FLRW observables dictionary | H₀, Δq, v_pec, λ_J |
| §7.16 Colin β reproduction | htt.core.beta_from_colin 결과 |
| §7.17 Tilted H₀ depth profile | 저z survey 비교 |
| §7.18 σ-ω-u̇ constraint plane | 4D projection atlas |

#### ch08 Robustness (1,176 → ~2,200 L)

| 섹션 | 내용 |
|---|---|
| §8.1 CAMB V-gate residuals | W10-02 rel_err(ℓ) 프로파일 |
| §8.2 k-grid sensitivity | 128 / 256 / 512 points 비교 |
| §8.3 **MES boundary check + identifiability audit** | htt.pipeline phase 3f/3g |
| §8.4 **Survey nuisance marginalisation** | htt.infer.survey_nuisance |
| §8.5 **Null competition FPR (5 families)** | N1~N5 × 15 models heatmap |
| §8.6 **Cross-channel coherence + LOOCV** | htt.advanced_diagnostics |
| §8.7 **Posterior predictive checks (15 models)** | χ²/ndof ≈ 1 확인 |
| §8.8 **Shared-cause test** | 여러 dipole signal 공통 원인? |
| §8.9 **ZoA 3-mode 안정성** | Mode 0 ladder / Mode 1 / Mode 2 posterior stability |
| §8.10 **Mock coverage test** | 1000 realization, 68% HPD coverage ≥ 65% |
| §8.11 **Depth-by-depth sensitivity** | CF4++ z-bin 분할 |
| §8.12 Prior width sweep | fig_rho_sweep 결과 |
| §8.13 Channel ablation | b, c, d, e, f, g, h 각각 제거 시 영향 |
| §8.14 Comparator sensitivity | flat / closed / matched prior |
| §8.15 Frame-choice η_{u̇} regression | htt.pipeline phase 3e, VT-07 재확인 |

#### ch09 Discussion (1,928 → ~2,800 L)

| 섹션 | 내용 |
|---|---|
| §9.X 3-signature implication | DE/inflation 표준 모형 함의 |
| §9.X+1 CatWISE vs CMB dipole discrepancy | 국소 vs 우주론적 해석 |
| §9.X+2 Lorentz 기준계 vs Bianchi 배경 | frame-attribution bias 해석 |
| §9.X+3 Filling fraction posterior mean > point | Q 비선형성 (+30%) |
| §9.X+4 Euclid DR1 예측 | ~Oct 2026 |
| §9.X+5 DESI DR2 연계 | dynamical DE 4.2σ |
| §9.X+6 Simons Observatory EE 전망 | 이미 운영 |
| §9.X+7 LiteBIRD (2033) 전망 | 차세대 EE 정밀도 |
| §9.X+8 Tsagas 해석 | khronon 유일 생존 |
| §9.X+9 shared-cause vs distinct-source | 다중 dipole origin |
| §9.X+10 bass_rs 상호보완 | 논문 scope 한계 명시 |
| §9.X+11 Inference philosophy | matched-complexity 왜 중요한가 |

#### ch10 Future (1,145 → ~1,600 L)

| 섹션 | 내용 |
|---|---|
| §10.X bass_rs 통합 | 차후 논문 예정 |
| §10.X+1 htt v2 확장 | MIO 통합 |
| §10.X+2 BiPoSH V2 gate | bass_rs 완성 후 |
| §10.X+3 Non-linear Σ regime | Σ² > 10⁻⁴ |
| §10.X+4 Patchy reionization | 역사적 inhomogeneity |
| §10.X+5 Euclid + DESI + SO 공동 분석 | 다중 probe |
| §10.X+6 LiteBIRD 차세대 | B-mode + EE 정밀도 |
| §10.X+7 Tilt² 6 cross-terms 관측 서명 | 개별 서명 검출 전망 |

#### ch11 Error hierarchy (596 → ~900 L)

| 섹션 | 내용 |
|---|---|
| §11.X 3-tier claim taxonomy 재확인 | ESTABLISHED / CONDITIONAL / NOT_ESTABLISHED |
| §11.X+1 Validation ladder (5 rungs) | Rung 0~4 도달 수준 |
| §11.X+2 scope-guard 철학 | OutOfScopeError 패턴 |
| §11.X+3 SSOT 규율 | d2_convention.rs + obs_defaults + htt.ssot + 일관성 |
| §11.X+4 **Production vs diagnostic 분리** | ZoA 재설계 핵심 원칙 |
| §11.X+5 **Uniform fallback 정책** | production_mode gate 철학 |
| §11.X+6 Matched-complexity 강제 | control_registry.py 목록 |

#### Appendices (300 → ~1,500 L)

| Appendix | 내용 |
|---|---|
| A1 | bass_py 프로덕션 루틴 (API signature list) |
| A2 | htt 15-model evidence model 공식 각각 |
| A3 | 5 null family 수학적 유도 |
| A4 | dynesty 설정 (nlive, sample, maxcall, dlogz) |
| A5 | Matched-complexity 알고리즘 전체 pseudocode |
| A6 | Mock calibration suite 세부 |
| A7 | 60+ figure 재현 스크립트 |
| A8 | tsc charts: Laguerre basis 선택 근거, F↔T 수치 안정성 |
| A9 | HEALPix NSIDE 선택 논리 |
| A10 | 3-mode transition gate 구현 |
| A11 | bass_rs 인터페이스 spec (future integration) |
| A12 | Regression report 포맷 (ML-serializable) |

### 11.4 전체 Figure 리스트 (60+)

#### A. HTT prototype 27개 (이미 작성됨, 정돈 필요)

| # | Fig | 출처 | Chapter |
|---|---|---|---|
| F01 | `fig_MES_three_bounds` | htt.bounds | ch04 §4.3 |
| F02 | `fig_sigma_omega_contour` | htt + tsc | ch04 §4.X |
| F03 | `fig_sigma_accel_contour` | htt | ch04 §4.X |
| F04 | `fig_3D_constraint_volume` | htt | ch04 §4.X |
| F05 | `fig_4D_projection_atlas` | htt | ch07 §7.18 |
| F06 | `fig_colin_beta` | htt | ch07 §7.16 |
| F07 | `fig_departure_summary` | htt | ch07 §7.9 |
| F08 | `fig_evidence_decomposition` | htt | ch07 §7.8.a |
| F09 | `fig_direction_posterior` | htt → 재생성 (Mode 2) | ch07 §7.7 |
| F10 | `fig_equiv_class_evidence` | htt | ch07 §7.14 |
| F11 | `fig_peculiar_jeans` | htt | ch07 §7.15 |
| F12 | `fig_q0_pushforward` | htt | ch07 §7.15 |
| F13 | `fig_q_decomposition` | htt | ch07 §7.15 |
| F14 | `fig_scale_hierarchy` | htt | ch03 §3.X |
| F15 | `fig_tilted_H0_depth` | htt | ch07 §7.17 |
| F16 | `fig_tilted_dictionary` | htt | ch07 §7.15 |
| F17 | `fig_type_by_type_summary` | htt | ch07 §7.13 |
| F18 | `fig_v_pushforward` | htt | ch07 §7.15 |
| F19 | `fig_vorticity_hierarchy` | htt | ch04 §4.X |
| F20 | `fig_cf4pp_sensitivity` | htt | ch08 §8.11 |
| F21 | `fig_channel_ablation_heatmap` | htt | ch08 §8.13 |
| F22 | `fig_nonlinear_heatmap_vorticity_accel` | htt | ch08 §8.14 |
| F23 | `fig_rho_sweep` | htt | ch08 §8.12 |
| F24 | `fig_certification_matrix` | htt | ch08 §8.15 |
| F25 | `fig_identified_reporting_split` | htt | ch11 §11.X |
| F26 | `fig_experiment_timeline` | htt | ch10 §10.X |
| F27 | `fig_repo_architecture` | htt | ch06 §6.1 |
| F28 | `fig_status_architecture` | htt | ch06 §6.1 |

#### B. bass_py 15개 (신규 생성)

| # | Fig | 출처 | Chapter |
|---|---|---|---|
| F29 | `fig_route_b_mm_curve` | bass.spectrum | ch07 §7.1 |
| F30 | `fig_d2_sigma2_scaling` | bass.spectrum | ch07 §7.1 |
| F31 | `fig_flrw_cl_vs_camb` | W10-02 | ch07 §7.2 |
| F32 | `fig_tensor_kernels` | bass.los.bianchi_propagator | ch03 §3.X |
| F33 | `fig_e_mode_projection` | bass.los | ch03 §3.X |
| F34 | `fig_visibility_g` | bass.recombination | ch06 §6.2 |
| F35 | `fig_g_pi_peak_near_lss` | W8-03 | ch06 §6.2 |
| F36 | `fig_m_channel_decomposition` | bass.transport (W5-C) | ch03 §3.X |
| F37 | `fig_sigma_m_channel_map` | W5-C + W9-02 | ch07 §7.4 |
| F38 | `fig_w_r_window` | W12-01 | ch07 §7.3 |
| F39 | `fig_biposh_bar` | W11-02 | ch07 §7.4 |
| F40 | `fig_beta_to_d2_transfer` | W13-02 | ch07 §7.5 |
| F41 | `fig_3_signature_templates` | W14-01 | ch07 §7.6 |
| F42 | `fig_3_signature_alpha_posterior` | W14-01 | ch07 §7.6.a |
| F43 | `fig_bianchi_flrw_recovery_ladder` | W9-02 | ch08 §8.2 |

#### C. HTT + bass_py 결합 / 신규 방법론 18개

| # | Fig | 출처 | Chapter |
|---|---|---|---|
| F44 | `fig_zoa_ladder_mode0` | htt Mode 0 신규 | ch08 §8.9 |
| F45 | `fig_healpix_completeness_map` | healpix_selection | ch06 §6.9 |
| F46 | `fig_4_summary_comparison` | PR13AH (수정) | ch06 §6.9 |
| F47 | `fig_wls_vs_dynesty_mode1_mode2` | bulkflow_estimator + likelihood | ch08 §8.9 |
| F48 | `fig_mock_coverage_histogram` | mock_calibration | ch08 §8.10 |
| F49 | `fig_null_competition_fpr_heatmap` | htt.nulls.runner | ch08 §8.5 |
| F50 | `fig_loocv_per_model` | htt.advanced_diagnostics | ch08 §8.6 |
| F51 | `fig_ppc_15_models` | htt.advanced_diagnostics.PosteriorPredictive | ch08 §8.7 |
| F52 | `fig_matched_complexity_table` | htt.infer.matched_complexity | ch06 §6.8 |
| F53 | `fig_survey_nuisance_cov_matrix` | htt.infer.survey_nuisance | ch08 §8.4 |
| F54 | `fig_depth_tomography_zbins` | htt.advanced_diagnostics.DepthTomography | ch07 §7.10 |
| F55 | `fig_savage_dickey_ratios` | htt.advanced_diagnostics.SavageDickeyRatio | ch07 §7.11 |
| F56 | `fig_quadrupole_axis_parity` | htt.geometry_discrimination | ch07 §7.12 |
| F57 | `fig_shared_cause_test` | htt.infer.shared_cause | ch08 §8.8 |
| F58 | `fig_catwise_vs_cmb_3sig_interp` | W14 + htt combined | ch09 §9.X+1 |
| F59 | `fig_euclid_forecast_templates` | analysis_extended.ForecastTable | ch10 §10.X+5 |
| F60 | `fig_hellinger_distance_matrix` | catalog_likelihood.hellinger_distance | ch07 §7.8 |
| F61 | `fig_redshift_binned_direction` | source_discrimination | ch07 §7.10 |

### 11.5 전체 Table 리스트 (30+)

| # | Title | Chapter |
|---|---|---|
| T01 | bass_py/tsc/htt subpackage inventory | ch06 |
| T02 | Completed vs pending prompts | ch06 |
| T03 | SSOT constants (T_CMB, Ω_m, h, eps_i, η_{u̇}, C_1, C_2) | ch06 |
| T04 | **15-model Bianchi evidence × 5 scenarios** (ln B matrix) | ch07 §7.8 |
| T05 | Evidence decomposition per channel (b/c/d/e/f/g/h) | ch07 §7.8.a |
| T06 | MES three-bound hierarchy numerical values | ch04 §4.3 |
| T07 | F_Bayes credible intervals per model | ch07 §7.9 |
| T08 | Departure posterior (x, Q, Π) per model | ch07 §7.9 |
| T09 | Comparator sensitivity (flat/closed/matched) | ch08 §8.14 |
| T10 | Hellinger distance matrix (15×15) | ch07 §7.8 |
| T11 | 3-signature discriminator α estimates per scenario | ch07 §7.6.a |
| T12 | Dipole direction medians + credible cones (S1–S3) | ch07 §7.7 |
| T13 | Tilted-FLRW observables at β=1.360e-3 | ch07 §7.15 |
| T14 | Colin+2025 β reproduction | ch07 §7.16 |
| T15 | **5 null families FPR matrix** (×15 models) | ch08 §8.5 |
| T16 | Matched-complexity report | ch06 §6.8 |
| T17 | Survey nuisance covariance summary | ch08 §8.4 |
| T18 | LOOCV per-model Δlog-evidence | ch08 §8.6 |
| T19 | Posterior predictive χ²/ndof per model | ch08 §8.7 |
| T20 | Shared-cause test results | ch08 §8.8 |
| T21 | ZoA 3-mode summary comparison | ch08 §8.9 |
| T22 | Mock calibration coverage (68%/95%) | ch08 §8.10 |
| T23 | Depth tomography per z-bin | ch07 §7.10 |
| T24 | Savage-Dickey BFs for hypothesis tests | ch07 §7.11 |
| T25 | Route B SSOT + anti-regression guard | ch07 §7.1 |
| T26 | CAMB V-gate residual summary | ch08 §8.1 |
| T27 | Type-by-type summary (8 orth × 6 tilt) | ch07 §7.13 |
| T28 | Equivalence class evidence | ch07 §7.14 |
| T29 | Observational data catalog | ch06 §6.X |
| T30 | Expected sensitivity (Euclid/SO/LiteBIRD) | ch10 §10.X |
| T31 | Scope-guard registry (OutOfScopeError catalogue) | ch11 §11.X+2 |
| T32 | Claim taxonomy by result | ch11 §11.X |

---

## §11.6 Scientific Amplification — 완성된 코드베이스가 제공하는 추가 과학적 가치

### 11.6.1 배경

현 §11.1–§11.5는 "기본 확장안"이다. 완성된 bass_py + htt + tsc 조합은 **훨씬 더 많은 과학적 deliverable을 가능하게 한다**. 본 섹션은 코드베이스 자체에서 도출 가능한 모든 추가 산출물을 과학적 가치 기준으로 분류한다.

### 11.6.2 추가 가능한 분석 카테고리 (전체 map)

| 카테고리 | 가능한 분석 | 현 manuscript 포함 여부 |
|---|---|---|
| **A. Bayesian 모델 선택 심화** | 15×15 pairwise BF, Jeffreys 분류, Occam 분해, 정보 기준 (DIC/WAIC/BIC/AIC), Bayesian model averaging | 기본만 (§7.8) |
| **B. 파라미터 posterior 심층** | 모델별 corner plots, 주변 분포, degeneracy 방향, nuisance marginalisation | 부분 (corner 없음) |
| **C. Evidence 기여 분해** | 채널별 (b/c/d/e/f/g/h), 데이터셋별, ℓ-range별, k-mode별 contribution | 부분 (§7.8.a) |
| **D. Cross-dataset tension / alignment** | Direction alignment 5×5, Suspiciousness, log-R, PTE, 공통 축 검정 | 미포함 |
| **E. Systematic propagation 심층** | Null family conditional evidence, foreground template, beam, calibration, mask inpainting | 일부 (§8.5) |
| **F. Redshift tomography 심층** | z-bin별 direction + amplitude, β(z) trajectory, axis migration rate | 기본만 (§7.10) |
| **G. CMB anomaly atlas** | Cold spot, axis of evil, 반구 비대칭, parity asymmetry 연계 | 미포함 |
| **H. Forecasting** | Fisher for Euclid/DESI/SO/LiteBIRD, ABC forward, 개선 factor | 간략만 (§10.X+5) |
| **I. MCMC / dynesty 수렴 진단** | Trace, autocorr, Gelman-Rubin, ESS | 미포함 |
| **J. Posterior predictive + residuals** | PPC, pull, Q-Q, Bayesian p-values | 기본만 (§8.7) |
| **K. Scale / k-mode 의존성** | ℓ-mode별 signature, k-range 지배성 | 미포함 |
| **L. 15-model 상세 dossier** | 각 모델 2-3 페이지 (prior, signature, posterior, BF) | 미포함 |
| **M. Dark sector 연계** | H_0 tension, S_8, dark energy 재해석 | 부분 (§9.X) |
| **N. SBI / ML 보조** | Neural posterior vs dynesty, Bashir+2025 forward model 재현 | 미포함 |

### 11.6.3 우선순위 선별 (과학적 가치 기준)

| 추가 | 가치 | 비용 | 우선 |
|---|---|---|---|
| 15×15 pairwise BF matrix | 모델 선택의 full picture | 저 | **필수** |
| 정보 기준 비교 (DIC/WAIC/BIC/AIC) | Bayes factor 보완적 검증 | 저 | **필수** |
| 모델별 corner plots (top-5) | 파라미터 물리 해석 | 중 | **필수** |
| Direction alignment matrix | CatWISE-CMB-CF4++ 텐션 정량화 | 저 | **필수** |
| CMB anomaly atlas | 타 우주론 anomalies와의 맥락 | 중 | 권장 |
| Systematic budget table | 체계 오차 정량화 | 중 | **필수** |
| Forecast tables (Euclid/SO/LiteBIRD) | 미래 probe와의 연결 | 중 | 권장 |
| Full 15-model dossier (appendix) | reproducibility + 심사위원 이해 | 고 | **필수** |
| MCMC diagnostics | inference 신뢰성 | 저 | **필수** |
| ABC / SBI forward model | Bashir+2025 재현 | 고 | 선택 |

---

## §11.7 Extended Figure Catalog (F62–F120)

59개 추가 figure. 총 120개.

### Category A — Bayesian 모델 선택 심화 (F62–F70)

| # | Fig | 데이터 소스 | Chapter |
|---|---|---|---|
| F62 | `fig_pairwise_bf_matrix` (15×15 Bayes factor heatmap) | htt.pipeline phase 3b | ch07 §7.19 |
| F63 | `fig_jeffreys_categorization` (inconclusive/moderate/strong/decisive 분류 플롯) | htt.pipeline | ch07 §7.19 |
| F64 | `fig_information_criteria` (DIC/WAIC/BIC/AIC × 15 models, stacked bar) | 신규 from posterior samples | ch07 §7.20 |
| F65 | `fig_bma_weights` (Bayesian model averaging posterior weights) | htt.analysis_extended | ch07 §7.21 |
| F66 | `fig_nested_test_tree` (FLRW ⊂ FLRW_tilt ⊂ BianchiI_tilt 트리 + Savage-Dickey BFs) | htt.advanced_diagnostics.SavageDickeyRatio | ch07 §7.22 |
| F67 | `fig_evidence_prior_sensitivity` (ln Z vs prior width, 15 models) | robustness_sweeps | ch08 §8.12 |
| F68 | `fig_occam_factor_decomposition` (prior volume penalty per model) | htt.core | ch07 §7.8.b |
| F69 | `fig_model_rank_stability_across_scenarios` (S1-S3에서 rank 변동) | htt.pipeline | ch08 §8.16 |
| F70 | `fig_bf_vs_null_conditional` (N1~N5 null 주입 후 BF 변화) | htt.nulls + analysis | ch08 §8.5.b |

### Category B — 파라미터 posterior corner plots (F71–F80)

| # | Fig | Model |
|---|---|---|
| F71 | `fig_corner_FLRW_tilt` (7D full corner) | FLRW_tilt |
| F72 | `fig_corner_BianchiI_tilt` (8D full corner) | BianchiI_tilt |
| F73 | `fig_corner_BianchiVIIh_tilt_grow` | VIIh_tilt_grow |
| F74 | `fig_corner_BianchiV_tilt` | V_tilt |
| F75 | `fig_corner_BianchiIX_tilt` | IX_tilt |
| F76 | `fig_beta_direction_joint` (β × (l,b) 3D heatmap × 5 scenarios) | top model |
| F77 | `fig_param_marginals_15models_grid` (모델 × 파라미터 matrix) | 전 모델 |
| F78 | `fig_degeneracy_directions` (PCA of posterior covariance per model) | top-5 models |
| F79 | `fig_nuisance_marginalization_effect` (before/after nuisance) | FLRW_tilt |
| F80 | `fig_parameter_shift_by_scenario` (동일 모델, 다른 scenario 간 β shift) | FLRW_tilt |

### Category C — Evidence 기여 분해 심층 (F81–F88)

| # | Fig | 내용 |
|---|---|---|
| F81 | `fig_channel_contribution_stacked` (b/c/d/e/f/g/h stacked bars per model) |
| F82 | `fig_dataset_contribution_sankey` (Planck / CatWISE / CF4++ / NVSS+RACS → 15 models) |
| F83 | `fig_l_range_evidence_breakdown` (ℓ=2, ℓ=3, ℓ>10 각각 ln Z 기여) |
| F84 | `fig_kmode_dominance_flrw_tilt` (k-mode별 BF 기여) |
| F85 | `fig_channel_ablation_delta_lnZ` (각 채널 제거 시 Δln Z × 15 models) |
| F86 | `fig_evidence_timeline_scenario_sequence` (S1→S2→S2b→S2c→S3 순으로 evidence 진화) |
| F87 | `fig_f_Bayes_conditional_on_channel` (채널 조건부 F_Bayes 분포) |
| F88 | `fig_channel_coherence_heatmap` (cross-channel coherence matrix 7×7) |

### Category D — Cross-dataset tension & alignment (F89–F96)

| # | Fig | 내용 |
|---|---|---|
| F89 | `fig_direction_alignment_matrix` (5×5: CMB / CatWISE / NVSS / RACS / CF4++) |
| F90 | `fig_dipole_sky_overlay_all_surveys` (Mollweide + 각 survey dipole direction) |
| F91 | `fig_suspiciousness_index` (dataset pair 별 log-R + Suspiciousness) |
| F92 | `fig_pte_matrix_between_datasets` (probability-to-exceed matrix) |
| F93 | `fig_catwise_vs_cmb_joint_posterior` (공통 parameter 공간) |
| F94 | `fig_redshift_alignment_drift` (z-bin별 direction drift angle) |
| F95 | `fig_cone_overlap_analysis` (68%/95% HPD cone 교집합 면적) |
| F96 | `fig_common_axis_test_posterior` (공통 축 ∃/¬∃ 가설 비교) |

### Category E — Systematic propagation 심층 (F97–F103)

| # | Fig | 내용 |
|---|---|---|
| F97 | `fig_null_conditional_evidence_heatmap` (15 models × 5 nulls × Δln Z) |
| F98 | `fig_galactic_foreground_residual_map` (Healpix template fit residual) |
| F99 | `fig_beam_uncertainty_propagation` (beam FWHM ± σ impact on D_ℓ) |
| F100 | `fig_calibration_uncertainty_impact` (A_planck ± σ → BF shift) |
| F101 | `fig_mask_inpainting_sensitivity` (apodization scale vs recovered direction) |
| F102 | `fig_retention_fraction_vs_posterior` (ZoA retention × posterior drift) |
| F103 | `fig_foreground_cleaning_comparison` (SMICA / Commander / NILC / SEVEM) |

### Category F — Redshift tomography 심층 (F104–F108)

| # | Fig | 내용 |
|---|---|---|
| F104 | `fig_direction_per_zbin_mollweide` (5 z-bin, 각각 Mollweide) |
| F105 | `fig_amplitude_vs_z_with_theory_bands` (관측 × 모델 예측 overlay) |
| F106 | `fig_beta_z_trajectory_per_model` (15 모델의 β(z) 이론 커브) |
| F107 | `fig_axis_migration_rate` (dz/dθ slope per model) |
| F108 | `fig_near_far_alignment_test` (z<0.02 vs z>0.05 HPD 중첩도) |

### Category G — CMB anomaly atlas (F109–F114)

| # | Fig | 내용 |
|---|---|---|
| F109 | `fig_anomaly_atlas_skymap` (cold spot, axis of evil, CatWISE axis, CF4++ bulk flow, Bianchi preferred axis 전부 한 sky map에) |
| F110 | `fig_axis_of_evil_vs_bianchi_axis` (quadrupole-octupole alignment × Bianchi preferred) |
| F111 | `fig_cold_spot_vs_direction_posterior` (cold spot 위치 × dipole posterior) |
| F112 | `fig_hemispherical_power_asymmetry_bianchi` (북/남 반구 power ratio per model) |
| F113 | `fig_parity_asymmetry_per_model` (even-odd ℓ power ratio) |
| F114 | `fig_anomaly_overlap_matrix` (anomaly 쌍별 공통 sky area) |

### Category H — Forecasting (F115–F120)

| # | Fig | 내용 |
|---|---|---|
| F115 | `fig_euclid_dr1_beta_sensitivity_forecast` (Fisher + ABC) |
| F116 | `fig_so_ee_detection_forecast` (per-model detection significance) |
| F117 | `fig_litebird_b_mode_upper_limits_per_model` |
| F118 | `fig_improvement_factor_per_survey` (parameter × survey grid) |
| F119 | `fig_fisher_ellipses_future_surveys` (2D ellipses in β-σ_* plane) |
| F120 | `fig_tension_resolution_timeline` (어떤 시점에 어떤 texture의 결정) |

### Category I — MCMC / dynesty diagnostics (F121–F125, appendix-bound)

| # | Fig | 내용 |
|---|---|---|
| F121 | `fig_trace_plots_top5` | dynesty trace |
| F122 | `fig_ess_per_parameter` | Effective sample size |
| F123 | `fig_autocorrelation_time` | Chain autocorrelation |
| F124 | `fig_gelman_rubin_diagnostic` | R̂ statistics |
| F125 | `fig_logz_convergence_history` | ln Z vs iteration |

### Category J — Posterior predictive + residuals (F126–F130)

| # | Fig | 내용 |
|---|---|---|
| F126 | `fig_ppc_tt_residuals_per_model` | D_ℓ^TT obs - model |
| F127 | `fig_ppc_ee_residuals_per_model` | D_ℓ^EE obs - model |
| F128 | `fig_pull_distribution_per_channel` | (obs-model)/σ 분포 |
| F129 | `fig_qq_plot_per_channel` | Q-Q plot for residuals |
| F130 | `fig_bayesian_pvalue_per_model` | p_B 히스토그램 |

### Summary — figure counts by chapter

| Chapter | 기존 (v2 §11.4) | 신규 (§11.7) | 최종 |
|---|---|---|---|
| ch01 | 0 | 0 | 0 |
| ch02 | 0 | 0 | 0 |
| ch03 | F14 (1) | — | 1 |
| ch04 | F01–F05, F19 (6) | — | 6 |
| ch06 | F27, F28, F34, F35, F45, F46, F52 (7) | — | 7 |
| ch07 | F06–F18 (excluding ch06/ch04), F29, F30, F36–F42, F54, F55, F56, F58, F60, F61 (~25) | F62–F96, F104–F114 (~46) | ~71 |
| ch08 | F20–F24, F31, F43, F47–F51, F53, F57 (~14) | F67, F69, F70, F97–F103, F126–F130 (~14) | ~28 |
| ch09 | F58 (1) | F94, F95 (2) | 3 |
| ch10 | F26, F59 (2) | F115–F120 (6) | 8 |
| Appendix | F25 (1) | F121–F125 (5) | 6 |

---

## §11.8 Extended Table Catalog (T33–T75)

43개 추가 table. 총 75개.

### Category A — Bayesian 모델 선택 심화 (T33–T40)

| # | Table | 내용 |
|---|---|---|
| T33 | **Pairwise Bayes factor matrix** (15×15) with Jeffreys scale labels | ch07 §7.19 |
| T34 | **Information criteria** (DIC / WAIC / BIC / AIC) × 15 models | ch07 §7.20 |
| T35 | **Bayesian model averaging weights** per scenario | ch07 §7.21 |
| T36 | Nested test tree — Savage-Dickey BFs | ch07 §7.22 |
| T37 | Occam factor × 15 models | ch07 §7.8.b |
| T38 | Evidence vs prior width Δln Z table | ch08 §8.12 |
| T39 | Model rank stability across S1–S3 | ch08 §8.16 |
| T40 | BF shift under null injection (15 × 5) | ch08 §8.5.b |

### Category B — 파라미터 posterior 심층 (T41–T47)

| # | Table | 내용 |
|---|---|---|
| T41 | **Full parameter posterior summaries** (median / 68% HPD / 95% HPD) × 15 models × all params | Appendix A13 |
| T42 | Parameter correlation matrix per top-5 model | ch07 §7.23 |
| T43 | Degeneracy directions (PCA eigenvectors) per model | ch07 §7.23 |
| T44 | Nuisance marginal correction table | ch08 §8.4 |
| T45 | β posterior shift across scenarios | ch07 §7.23 |
| T46 | (l, b) posterior median × 15 models | ch07 §7.8 |
| T47 | HPD cone radius (68% / 95%) × 15 models × 5 scenarios | ch07 §7.7 |

### Category C — Evidence decomposition (T48–T53)

| # | Table | 내용 |
|---|---|---|
| T48 | Channel contribution to ln Z (b/c/d/e/f/g/h) × 15 models | ch07 §7.24 |
| T49 | Dataset contribution to ln Z (Planck / CatWISE / CF4++ / NVSS+RACS) | ch07 §7.25 |
| T50 | ℓ-range contribution (ℓ=2, ℓ=3, ℓ>10) | ch07 §7.26 |
| T51 | k-mode dominance ranges per channel | ch08 §8.17 |
| T52 | Cross-channel coherence matrix (7×7) | ch08 §8.6.a |
| T53 | Channel ablation Δln Z | ch08 §8.13 |

### Category D — Cross-dataset tension (T54–T59)

| # | Table | 내용 |
|---|---|---|
| T54 | **Direction alignment matrix** (5×5: CMB / CatWISE / NVSS / RACS / CF4++) — angle + σ | ch07 §7.27 |
| T55 | **Suspiciousness / log-R / PTE** per dataset pair | ch07 §7.29 |
| T56 | Common-axis test BF | ch07 §7.28 |
| T57 | Posterior predictive overlay χ² | ch08 §8.18 |
| T58 | z-binned direction consistency | ch07 §7.10.a |
| T59 | Shared-cause vs distinct-source BF | ch08 §8.8 |

### Category E — Systematic budget (T60–T65)

| # | Table | 내용 |
|---|---|---|
| T60 | **Complete systematic budget** (foreground / beam / calibration / mask) | ch08 §8.19 |
| T61 | Galactic foreground template fit residuals per channel | ch08 §8.19.a |
| T62 | Beam uncertainty propagation (D_ℓ shift) | ch08 §8.19.b |
| T63 | Calibration (A_planck) sensitivity | ch08 §8.19.c |
| T64 | Foreground cleaning comparison (SMICA/Commander/NILC/SEVEM) | ch08 §8.19.d |
| T65 | ZoA cut retention vs posterior drift | ch08 §8.19.e |

### Category F — MCMC / dynesty diagnostics (T66–T69)

| # | Table | 내용 |
|---|---|---|
| T66 | ESS per parameter per model | Appendix A27 |
| T67 | Chain duration (nlive, ncall, wall time) per run | Appendix A27 |
| T68 | Gelman-Rubin R̂ per parameter | Appendix A27 |
| T69 | dlogz termination value per run | Appendix A27 |

### Category G — Posterior predictive + residuals (T70–T72)

| # | Table | 내용 |
|---|---|---|
| T70 | Posterior predictive χ²/ndof × 15 models × scenarios | ch08 §8.7 |
| T71 | Bayesian p-value per channel per model | ch08 §8.7.a |
| T72 | Pull distribution moments (mean / std) | ch08 §8.7.b |

### Category H — Forecasting (T73–T75)

| # | Table | 내용 |
|---|---|---|
| T73 | **Fisher forecast table** for Euclid / DESI / SO / LiteBIRD | ch10 §10.X+8 |
| T74 | ABC forward model forecast summary | ch10 §10.X+9 |
| T75 | Per-parameter improvement factor per survey | ch10 §10.X+10 |

---

## §11.9 Extended Chapter Content — 신규 subsection 제안

### 11.9.1 ch07 Results — §7.19 이후 추가 subsection

| § | 제목 | 핵심 결과 | Figure/Table |
|---|---|---|---|
| §7.19 | Pairwise Bayes factor matrix | 모델 선택의 full picture | F62, T33 |
| §7.20 | Information criteria cross-check | DIC/WAIC/BIC/AIC로 BF 보완 | F64, T34 |
| §7.21 | Bayesian model averaging | posterior weights → 안정적 파라미터 추정 | F65, T35 |
| §7.22 | Nested hypothesis tree | Savage-Dickey BFs로 nested 관계 | F66, T36 |
| §7.23 | Parameter posterior corner plots (top-5) | 물리 파라미터 joint 분포 | F71–F75, T41–T43 |
| §7.24 | Channel contribution to evidence | 어떤 channel이 BF를 이끄는가 | F81, T48 |
| §7.25 | Dataset contribution | 데이터셋별 증거 분해 | F82, T49 |
| §7.26 | ℓ-range evidence breakdown | ℓ=2 vs 나머지 기여 | F83, T50 |
| §7.27 | **Direction alignment matrix** (5×5) | 서베이 쌍별 방향 일치도 | F89, T54 |
| §7.28 | Common-axis hypothesis test | "모든 dipole이 같은 축?" BF | F96, T56 |
| §7.29 | Dataset tension quantification | Suspiciousness, log-R, PTE | F91, T55 |
| §7.30 | Redshift-binned direction consistency | z-bin별 axis 일치도 | F104, T58 |
| §7.31 | β(z) trajectory per model | 이론 예측 vs 관측 | F106 |
| §7.32 | Anomaly atlas overlay | 타 anomalies와 맥락 | F109, F110 |
| §7.33 | Hemispherical / parity asymmetry | per-model 예측 | F112, F113 |

### 11.9.2 ch08 Robustness — §8.16 이후 추가 subsection

| § | 제목 | 핵심 |
|---|---|---|
| §8.16 | Model rank stability across scenarios | S1-S3 변화 시 rank 변동 |
| §8.17 | k-mode dominance analysis | 어떤 k가 BF를 지배하는가 |
| §8.18 | Posterior predictive overlay χ² | 관측 data with best-fit overlay |
| §8.19 | **Complete systematic budget** (7-subpart) | foreground / beam / calibration / mask / ZoA retention / foreground cleaner comparison / cross-channel consistency |
| §8.20 | Cross-channel coherence matrix (7×7) | 채널 간 consistency 정량화 |
| §8.21 | Null-conditional evidence shift | N1–N5 주입 후 BF 이동 |
| §8.22 | Galactic foreground template fit residuals | per-channel chi² |
| §8.23 | Foreground cleaner comparison | SMICA / Commander / NILC / SEVEM |
| §8.24 | ZoA retention vs posterior drift | 3-mode sensitivity |
| §8.25 | Chain convergence full report | trace / ESS / R̂ / autocorr |
| §8.26 | Effective number of parameters (p_D) | DIC 구성요소 |
| §8.27 | Model identifiability audit | inactive parameters 검출 |

### 11.9.3 ch09 Discussion — 추가 subsection

| § | 제목 | 핵심 |
|---|---|---|
| §9.X+12 | Bayesian model averaging 해석 | posterior weight의 물리적 의미 |
| §9.X+13 | Tension 정량화 과학적 함의 | CatWISE vs CMB 1-order 차이 해석 |
| §9.X+14 | Anomaly atlas 종합 해석 | cold spot, axis of evil 통합 view |
| §9.X+15 | Axis migration 해석 | 국소 vs 우주론적 evolution |
| §9.X+16 | Galactic vs extragalactic 원인 | systematic vs physical |
| §9.X+17 | Cosmic variance vs systematic 분리 | 통계적 한계 |
| §9.X+18 | H_0 tension 과의 연결 | Δq 3-term (Tully+ 2023) 함의 |
| §9.X+19 | S_8 tension 과의 관계 (간접) | structure growth tilt 효과 |
| §9.X+20 | Dark energy 재해석 | Ω_Λ vs Ω_tilt averaged |
| §9.X+21 | Quintessence-like effective w(z) | Bianchi backreaction |
| §9.X+22 | Backreaction schemes (BMR) | tilt → T_D (not Q_D) |
| §9.X+23 | Parity / hemispherical asymmetry 연결 | per-model 예측 |
| §9.X+24 | Non-Gaussianity 함의 | Bianchi I에서 mode coupling |
| §9.X+25 | Inflation vs tilt 경쟁 | 양자택일? 공존? |

### 11.9.4 ch10 Future — 추가 subsection

| § | 제목 | 핵심 |
|---|---|---|
| §10.X+8 | Fisher forecast 종합 | 미래 survey × parameter 표 |
| §10.X+9 | Specific Euclid DR1 예측 | 특정 β 감도 |
| §10.X+10 | DESI DR2 dynamical DE 연계 | 4.2σ 결과 해석 대안 |
| §10.X+11 | LiteBIRD B-mode test per model | 모델별 upper limit |
| §10.X+12 | ABC / SBI 병행 계획 | Bashir+2025 재현 |
| §10.X+13 | ML-보조 neural posterior | dynesty 대체 cross-check |
| §10.X+14 | 15-model → 30+ model 확장 | Bianchi IV, non-tilt matter-filled 등 |
| §10.X+15 | Patchy reionization Bianchi 효과 | 21cm + CMB 공동 |
| §10.X+16 | 반물질 비대칭 연결 | baryogenesis × tilt |

---

## §11.10 Extended Appendix Structure (A13–A30)

### 기존 A1–A12 + 신규 A13–A30 = 총 30개

| Appendix | 제목 | 예상 분량 (L) | 주요 구성 |
|---|---|---|---|
| A1–A12 | (이미 정의) | 1,500 | §11.3에서 기술 |
| **A13** | **15-model full dossier** | 2,000 | 각 모델: prior spec / kinematic signature / channel contribution / BF / parameter posterior / pitfalls |
| A14 | 5 null family mathematical derivation | 600 | N1~N5 SBI forward, amplitude prior, sky pattern |
| A15 | Matched-complexity protocol pseudocode | 300 | control_registry 전수 + enforce_matched_complexity 알고리즘 |
| A16 | Savage-Dickey BF calculation | 250 | Nested 관계에서 BF의 posterior-to-prior 비율 유도 |
| A17 | LOOCV cross-validation | 300 | Leave-one-out predictive density 정의 + 구현 |
| A18 | Posterior predictive p-value | 250 | p_B 정의 + 해석 유의점 |
| A19 | Hellinger distance for posteriors | 200 | 정의, 해석, 거리 matrix 활용 |
| A20 | Information criteria (DIC / WAIC / BIC / AIC) | 400 | 각 기준 정의 + p_D, p_W 계산 + 상호 관계 |
| A21 | Tension statistics (Suspiciousness, log-R, PTE) | 400 | Handley-Lemos 유도 + 우리 적용 |
| A22 | Fisher forecasting mathematics | 350 | Fisher matrix inversion + marginalization + Gaussian approx 유효성 |
| A23 | ABC / SBI forward methodology | 400 | Bashir+2025 재현 + neural network architecture |
| A24 | ZoA 3-mode gate 수학 | 300 | Mode 전환 조건의 확률적 해석 |
| A25 | Mock calibration coverage test | 250 | coverage 정의 + frequentist vs Bayesian |
| A26 | HEALPix NSIDE 선택 이론 | 200 | Nyquist 조건 + pixel area / beam 비교 |
| A27 | **dynesty configuration + diagnostics** | 400 | nlive, sample, dlogz, termination + trace + ESS + R̂ |
| A28 | Channel likelihood (b/c/d/e/f/g/h) 정의 | 500 | 각 채널의 물리 + 수학 + normalisation |
| A29 | CMB anomaly alignment tests | 350 | axis of evil, cold spot, hemispherical asymmetry 수학 |
| A30 | Redshift tomography methodology | 300 | z-bin 선택 + 직교성 + 상관관계 처리 |

**Appendix 총 분량**: ~1,500 (A1–A12) + ~7,350 (A13–A30) = **~8,850 L**

### 11.10.1 A13 — 15-model full dossier 구조

각 모델에 대해 **2 페이지 (≈ 130 L) 표준 형식**:

| 항목 | 내용 |
|---|---|
| Model name | 예) BianchiVIIh_tilt_grow |
| Structural constants | 9-type Lie algebra assignment |
| Free parameters | β, σ_*, ω, (optional) A_a 등 |
| Prior specification | 각 파라미터 U / N / half-Gaussian |
| Kinematic signature | Σ²(t), W²(t), β(t) 예측 trajectory |
| Distinguishing channels | 어떤 채널에서 BF를 받는가 |
| Scenario-dependent BF | S1~S3 scenario에서 ln Z, ln B |
| Posterior summary | median + 68% HPD per parameter |
| Pitfalls / 주의사항 | Degeneracy, identifiability issue |
| 참조 figure | F-번호 |

15 models × 130 L ≈ 2,000 L

### 11.10.2 A14 — 5 null family mathematical derivation

각 null family에 대해 ~120 L:

| 항목 | 내용 |
|---|---|
| N-number | N1–N5 |
| Physical origin | WISE scanning / mask leakage / clustering / selection / survey axis |
| Forward model | amplitude prior + sky pattern |
| SBI reference | Bashir+2025 / von Hausegger-Dalang 2025 |
| Statistical signature | 어떤 channel / ℓ에서 주로 나타나는가 |
| False-positive prediction | FPR expected under hypothesis |

---

## §11.11 Scientific Novelty Claims Audit

### 11.11.1 **NEW** claims (본 연구 최초)

| Claim | 근거 deliverable | Manuscript 위치 |
|---|---|---|
| Departure parameter x_C master identity 전체 Bianchi 계열에 적용 | D6 + tsc | ch04 |
| Route B Michaelis-Menten D_2 lookup의 엄밀 sentinel 구현 | D17 | ch07 §7.1 |
| TT-vs-EE 3-signature separability의 관측 검증 | D2 | ch07 §7.6 |
| ZoA 3-mode production gate 체계 | D21 | ch06 §6.9 |
| 15-model pairwise BF matrix (5 scenarios × 5 null families 포함) | D1, D4 + F62 | ch07 §7.19 |
| Filling fraction F_Bayes posterior-mean 계산 (point estimate보다 +30%) | D5 | ch07 §7.9 |
| Three-bound hierarchy B_σ > B_ω > B_u̇ 전체 Bianchi 검증 | D6 | ch04 §4.3 |
| Clarkson-Maartens killing 이후 khronon 유일 생존 실증 확인 | — | ch09 §9.X+8 |
| Mock calibration 기반 production axis 게이트 (재현성 표준) | D22 | ch06 §6.10 |
| Matched-complexity protocol로 model 비교의 체계적 통제 | D13 | ch06 §6.8 |

### 11.11.2 **CONFIRMING** claims (기존 결과 독립 검증)

| Claim | 비교 대상 |
|---|---|
| CatWISE dipole amplitude ≈ 1.55×10⁻² | Secrest et al. 2020 |
| NVSS+RACS dipole ≈ 2.586×10⁻³ | 선행 publication |
| Colin β constraints 재생산 | Colin et al. |
| Peculiar Jeans length behavior | Tsagas 등 선행 |
| FLRW D_ℓ at ℓ ≤ 30 matches CAMB to 5% | W10-02 |

### 11.11.3 **EXPANDING** claims (기존 idea를 심화)

| Claim | 기존 문헌 | 본 연구 확장 |
|---|---|---|
| MES bound hierarchy | Maartens-Ellis-Stoeger 1995 | 9개 Bianchi type + departure parameter 재구성 |
| Ferreira-Quartin kinematic dipole | Ferreira & Quartin 2020 | S1 scenario 기준점 + 15-model 연결 |
| Tsagas multipolar cosmology | Tsagas et al. | bass_py + htt에서 양적 검정 |
| von Hausegger-Dalang selection effect | 2025 | N4 null family 구현 |
| Bashir+2025 SBI for WISE | 2025 | N1 null family 구현 |

---

## §11.12 Manuscript 분량 재추정 (Scientific Amplification 반영)

### 11.12.1 Chapter 별 최종 목표 분량

| Chapter | v2 §11.1 | 확장 반영 | 증가 근거 |
|---|---|---|---|
| ch01 | ~700 | ~700 | 변동 없음 |
| ch02 | ~800 | ~800 | 변동 없음 |
| ch03 | ~4,700 | ~4,900 | Laguerre basis A8 ref 추가 |
| ch04 | ~1,700 | ~1,800 | 3-bound hierarchy 심화 |
| ch05 | ~3,100 | ~3,200 | channel 정의 A28 ref |
| ch06 | ~2,500 | ~2,700 | systematic budget §8.19 cross-ref |
| **ch07** | ~3,500 | **~5,000** | 15개 신규 §7.19~§7.33 |
| **ch08** | ~2,200 | **~3,500** | 12개 신규 §8.16~§8.27 |
| **ch09** | ~2,800 | **~3,800** | 14개 신규 §9.X+12~§9.X+25 |
| **ch10** | ~1,600 | **~2,200** | 9개 신규 §10.X+8~§10.X+16 |
| ch11 | ~900 | ~900 | 변동 없음 |
| **Appendix** | ~1,500 | **~8,850** | A13–A30 신규 (15-model dossier 포함) |
| **Total** | ~26,000 | **~38,350** | +47% 추가 확장 |

### 11.12.2 Figure / Table 수 최종

| 항목 | v2 §11.4–§11.5 | §11.6 확장 반영 | 최종 |
|---|---|---|---|
| Figures | 61 | +69 | **~130** |
| Tables | 32 | +43 | **~75** |
| Appendix entries | 12 | +18 | **30** |

### 11.12.3 Thesis 합리성 체크

| 기준 | 값 | 판정 |
|---|---|---|
| 전체 L 수 | ~38,000 | 박사논문 기준 상한 (일반 박사논문 20k–40k L) |
| Figure 수 | ~130 | Data-heavy thesis 합리 범위 |
| Table 수 | ~75 | 정량 연구 합리 범위 |
| Appendix 분량 | 40% 이상 | 15-model dossier로 정당화 |
| 심사위원 기준 self-containedness | 달성 | 각 chapter + Appendix dossier 충분 |

**주의**: Appendix 비중이 매우 크므로 분리 제출 옵션 (e.g. supplementary material) 고려.

---

## §11.13 우선순위 분류 (실현 가능성 기준)

완성된 codebase 전제이지만, 박사논문 timeline 내 모든 확장을 실행하지 못할 가능성 고려.

### 11.13.1 Tier 1 — 반드시 포함 (과학 주장에 필수)

| 항목 | 근거 |
|---|---|
| F62 Pairwise BF matrix | 모델 선택 결정 |
| F64 Information criteria | BF 보완 |
| F71–F75 Corner plots top-5 | 물리 해석 |
| F89 Direction alignment matrix (**MIO**) | dataset tension (model-independent) |
| F97 Null-conditional evidence | systematic |
| **F131 Σ²_MIO(ℓ) (MIO)** | **비모수 shear 검출** |
| **F135 Resultant vector 5-probes (MIO)** | **cross-probe coherence** |
| **F138 FLRW tension PPP (MIO)** | **FLRW null 정량화** |
| T33 BF matrix | 데이터 표 |
| T34 Information criteria | 데이터 표 |
| T54 Alignment matrix | 데이터 표 |
| T60 Systematic budget | essential |
| **T76 Σ²_MIO(ℓ) table (MIO)** | 핵심 관측 결과 |
| **T82 HTT ↔ MIO cross-check (MIO)** | G19 enforcement 증거 |
| A13 15-model dossier | reproducibility |
| **A32 MioCertificate schema** | interface contract |

### 11.13.2 Tier 2 — 권장 포함 (과학 가치 높음)

| 항목 | 근거 |
|---|---|
| F109 Anomaly atlas (**MIO**) | 타 CMB anomalies 맥락 |
| F115 Euclid forecast | 미래 probe 연결 |
| F126–F130 Residuals / pulls | 모델 적합성 |
| **F133 STF shear components (MIO)** | 5 STF decomposition |
| **F140 Evidence anatomy flow (MIO)** | ln B 물리 해석 |
| **F142 Predictive residuals atlas (MIO)** | model failure mapping |
| T55 Tension statistics | 정량화 |
| T73 Fisher forecast | 전망 |
| **T80 PPP p-values (MIO)** | FLRW null per-test 결과 |
| **T81 Evidence anatomy decomposition (MIO)** | 분해 결과 표 |
| A14 Null family derivation | 방법론 |
| A20 Information criteria 정의 | 방법론 |
| **A34 Σ²_MIO derivation (MIO)** | HJ-01 수학 |
| **A38 HTT ↔ MIO cross-check protocol (MIO)** | G19 |

### 11.13.3 Tier 3 — 시간 허용 시 포함

| 항목 | 근거 |
|---|---|
| F121–F125 MCMC diagnostics | 기술적 완성도 |
| F116–F120 다른 forecasting | 장기 전망 |
| **F141 Redshift evidence tomography (MIO)** | per-z 분해 |
| A23 SBI methodology | 미래 방향 |
| **A37 Evidence anatomy consistency theorem** | 수학적 완결성 |

### 11.13.4 Tier 비상 계획

| Tier | 실패 시 조치 |
|---|---|
| Tier 1 실패 | Phase I 연장, submission 지연 |
| Tier 2 실패 | 해당 항목을 ch10 Future work로 이관 |
| Tier 3 실패 | post-submission publication으로 별도 |
| **MIO Phase J 전체 실패** | **HJ-02 directional coherence 단독 보존 (데이터만 필요), ch12를 ~5 페이지로 축소, 나머지는 post-submission** |

---

## §11.14 MIO Manuscript Content (v3 신규)

### 11.14.1 신규 ch12 "MIO Observatory Results"

Phase J (HJ-01~05) 결과를 집약하는 **완전히 새로운 chapter**. HK-08 (post-BASS programme) 에 대응.

#### 11.14.1.1 ch12 예상 분량 및 구조

| 섹션 | 분량 | 내용 |
|---|---|---|
| §12.0 | ~50 L | MIO 철학: model-independent observatory, not gatekeeper |
| §12.1 Non-parametric shear extraction | ~250 L | Σ²_MIO(ℓ), ℓ-independence test, STF decomposition |
| §12.2 Cross-channel directional coherence | ~200 L | 5-probe resultant, Fisher isotropy p-value |
| §12.3 FLRW tension metric + x_C | ~250 L | PPP p-values, x_C direct estimate |
| §12.4 Evidence anatomy (what drives ln B) | ~300 L | Channel/z-bin/parameter decomposition, evidence flow |
| §12.5 Predictive diagnostics | ~250 L | Model-agnostic residual atlas, where models fail |
| §12.6 HTT ↔ MIO cross-validation | ~200 L | Cross-check table, G19 enforcement 결과 |
| §12.7 MIO의 scope와 한계 | ~100 L | MioCertificate는 truth certificate 아님 재강조 |
| §12.8 MIO 결과와 HTT 결과 비교 요약 | ~150 L | Σ²_MIO vs Σ²_HTT_posterior, direction_MIO vs direction_HTT |
| **합계** | **~1,750 L** (약 18 pages @ 100 L/page) | HK-08 계획 ~15 pages 상향 |

#### 11.14.1.2 ch12 내부 교차 참조 구조

```
§12.1 Σ²_MIO(ℓ) ──────────────┐
                              │
§12.2 Directional coherence ─┼─── §12.6 HTT cross-check
                              │      │
§12.3 FLRW tension ──────────┘      │
                                    │
§12.4 Evidence anatomy ─────────────┤
                                    │
§12.5 Predictive residuals ────────┘
         │                          │
         └──────── §12.8 Summary ◄──┘
```

### 11.14.2 ch11 "Error hierarchy" 재구성 (v3 교정)

v2에서 ch11을 "error hierarchy (596 → ~900 L)"로 계획했으나, 그 contents 중 일부가 MIO로 혼동. 재구성:

| 구 분류 (v2) | 신 분류 (v3) |
|---|---|
| §11.X "claim taxonomy" | ch11에 **유지** (per-module 책임 명시) |
| §11.X "validation ladder (Rung 0-4)" | ch11에 **유지** (per-module Rung 상태) |
| §11.X "scope-guard 철학" | ch11에 **유지** (per-module `OutOfScopeError`) |
| §11.X "production vs diagnostic" | ch11에 **유지** (ZoA 3-mode 경계) |
| ~~§11.X "MIO as certification engine"~~ | **삭제** (MIO는 certification engine이 아님) |
| (신규) §11.X "`MioCertificate` semantic rule" | **ch11 추가** (DOC-03 III-4.3~4) |
| (신규) §11.X "Hard separation (G19) 실행" | **ch11 추가** |
| (신규) §11.X "Epistemic control 분산 소유" | **ch11 추가** (who-owns-what 테이블) |

ch11 새 분량 추정: 596 → **~1,100 L** (MIO semantic rule + G19 + 분산 소유 추가).

### 11.14.3 MIO 전용 Figures (F131–F145) — 15개 신규

| # | Fig | MIO 모듈 | Chapter | 내용 |
|---|---|---|---|---|
| F131 | `fig_Sigma2_MIO_per_ell` | `mio.extraction` | ch12 §12.1 | ℓ-by-ℓ Σ² extraction + cosmic variance error bars |
| F132 | `fig_ell_independence_test` | `mio.extraction` | ch12 §12.1 | p-value distribution + FLRW null |
| F133 | `fig_STF_shear_components` | `mio.extraction` | ch12 §12.1 | 5 STF component bar + preferred axis |
| F134 | `fig_MIO_shear_direction_mollweide` | `mio.extraction` | ch12 §12.1 | Preferred axis on sky |
| F135 | `fig_resultant_vector_5probes` | `mio.coherence` | ch12 §12.2 | 5 probe + resultant arrow |
| F136 | `fig_isotropy_pvalue_per_combination` | `mio.coherence` | ch12 §12.2 | Probe combination p-value |
| F137 | `fig_pairwise_separations_matrix` | `mio.coherence` | ch12 §12.2 | 5×5 angular separation |
| F138 | `fig_FLRW_tension_PPP` | `mio.tension` | ch12 §12.3 | T(data) vs T(FLRW mocks) |
| F139 | `fig_xC_direct_estimate` | `mio.tension` | ch12 §12.3 | x_C posterior-free estimate |
| F140 | `fig_evidence_anatomy_flow` | `mio.decomposition` | ch12 §12.4 | Channel → parameter → evidence flow diagram |
| F141 | `fig_redshift_evidence_tomography` | `mio.decomposition` | ch12 §12.4 | per-z ln B 분해 |
| F142 | `fig_predictive_residuals_atlas` | `mio.diagnostics` | ch12 §12.5 | Model × channel × ℓ residual heatmap |
| F143 | `fig_where_models_fail` | `mio.diagnostics` | ch12 §12.5 | Per-model fail region |
| F144 | `fig_htt_mio_cross_check_table` | `mio.interface` | ch12 §12.6 | Σ²_HTT vs Σ²_MIO (not merged) |
| F145 | `fig_mio_flow_diagram` | — | ch06 §6.X | MIO 5 subpackage + data flow |

### 11.14.4 MIO 전용 Tables (T76–T82) — 7개 신규 (v2 범주 재할당)

| # | Table | 소스 | Chapter |
|---|---|---|---|
| T76 | Σ²_MIO(ℓ) + errors × 5 scenarios | `mio.extraction` | ch12 §12.1 |
| T77 | ℓ-independence χ² + p-value × scenarios | `mio.extraction` | ch12 §12.1 |
| T78 | STF components σ_2M + direction | `mio.extraction` | ch12 §12.1 |
| T79 | Resultant vector + isotropy p-value | `mio.coherence` | ch12 §12.2 |
| T80 | PPP p-values per test statistic × scenario | `mio.tension` | ch12 §12.3 |
| T81 | Evidence anatomy (ch × z-bin × param) | `mio.decomposition` | ch12 §12.4 |
| T82 | HTT ↔ MIO cross-check summary | `mio.interface` | ch12 §12.6 |

### 11.14.5 기존 figures 재할당 (v2 오분류 교정)

v2에서 HTT로 분류된 일부 figure가 실제로는 **model-independent (MIO territory)** 였음. 재할당:

| Fig # | v2 분류 | v3 재분류 | 재할당 사유 |
|---|---|---|---|
| F89 `direction_alignment_matrix` | HTT | **MIO** | 완전 frequentist + model-free |
| F109 `anomaly_atlas_skymap` | HTT | **MIO** | Cold spot, axis of evil 등은 model-independent anomaly |
| F110 `axis_of_evil_vs_bianchi_axis` | HTT | **MIO** | 축 비교는 model-free |
| F112 `hemispherical_power_asymmetry` | HTT (per-model) | **MIO (data)** + HTT (model prediction) | Data는 MIO, 예측 비교는 HTT |
| F113 `parity_asymmetry` | HTT (per-model) | **MIO (data)** + HTT (model prediction) | 같은 이유 |

### 11.14.6 기존 Appendix A14→A15 재명명 + MIO 신규 appendix

| Appendix | 제목 | 분량 |
|---|---|---|
| A31 | **MIO full API catalog** | ~400 L |
| A32 | **`MioCertificate` schema** + 모든 필드 의미 | ~300 L |
| A33 | **`HttForwardOutput` + `AtlasEntry` schema** | ~250 L |
| A34 | **Non-parametric Σ² extraction 유도** (HJ-01 수학) | ~400 L |
| A35 | **Cross-channel directional coherence statistics** (Fisher distribution, Rayleigh test) | ~350 L |
| A36 | **FLRW posterior predictive p-value 유도** | ~300 L |
| A37 | **Evidence anatomy consistency theorem** (Σ channels Δln B ≈ total ln B) | ~200 L |
| A38 | **HTT ↔ MIO cross-check protocol** (G19 enforcement) | ~300 L |
| A39 | **Per-module epistemic ownership table** (분산 소유) | ~200 L |
| A40 | **PR13AM TE-sign D1/D3 bridge derivation** (MIO 소유) | ~250 L |
| **MIO appendix 합계** | | **~2,950 L** |

### 11.14.7 manuscript 전체 chapter 카운트 (v3)

| Chapter | 기존 (v2 plan) | v3 (MIO 포함) | 변경 |
|---|---|---|---|
| ch01 | ~700 | ~700 | — |
| ch02 | ~800 | ~800 | — |
| ch03 | ~4,900 | ~4,900 | — |
| ch04 | ~1,800 | ~1,800 | — |
| ch05 | ~3,200 | ~3,200 | — |
| ch06 | ~2,700 | **~3,000** | MIO pipeline subsection (§6.X MIO), `MioCertificate` 소개 |
| ch07 | ~5,000 | ~5,000 | — |
| ch08 | ~3,500 | ~3,500 | — |
| ch09 | ~3,800 | **~4,100** | MIO 결과 해석 추가 |
| ch10 | ~2,200 | ~2,200 | — |
| ch11 | ~900 | **~1,100** | MIO semantic + G19 + 분산 소유 |
| **ch12 (신규)** | — | **~1,750** | **MIO Observatory Results** |
| Appendix | ~8,850 | **~11,800** | MIO A31–A40 (~2,950) |
| **Total** | **~38,350** | **~40,200** | **+1,850 (+5%)** |

### 11.14.8 Figure / Table 수 최종 (v3)

| 항목 | v2 amplified | v3 MIO 포함 | 증가 |
|---|---|---|---|
| Figures | ~130 | **~145** | +15 MIO figures (F131-F145) |
| Tables | ~75 | **~82** | +7 MIO tables (T76-T82) |
| Appendix entries | 30 | **40** | +10 MIO appendix (A31-A40) |

---


## §12. 데이터 산출물 (figures/tables 외) — 확장판

### 12.1 JSON artifacts (Mode별 분리)

| 파일 | 생성 layer | 접두 | 내용 |
|---|---|---|---|
| `diag_zoa_ladder_vX.json` | Mode 0 | `diag_` | b_cut 0~30° 전체 ladder, retention, WLS V̂ per cut, axis instability 측정 |
| `diag_plane_alignment_vX.json` | Mode 0 | `diag_` | b_cut 변화 시 `(l, b)` 경로, resultant_R |
| `baseline_selection_aware_vX.json` | Mode 1 | `baseline_` | Hard cut + completeness weight 적용 WLS 결과, bootstrap cov |
| `fiducial_posterior_bundle_vX.json` | Mode 2 | `fiducial_` | dynesty posterior samples (HDF5 link), evidence, HPD cone, axis with `production_allowed=True` |
| `mock_calibration_report_vX.json` | Mode 2 전처리 | `fiducial_` | bias, coverage_68, credible_radius, null distribution summary |
| `matched_complexity_report_vX.json` | HTT inference | `report_` | 모델별 complexity score, passed/failed flag |
| `15model_evidence_matrix_vX.json` | HTT pipeline 3b | `report_` | 15 model × 5 scenario ln B matrix |
| `null_library_fpr_vX.json` | HTT nulls.runner | `report_` | 5 family × 15 model FPR heatmap data |

### 12.2 JSON artifacts — 확장 (Scientific Amplification + MIO)

| 파일 | 생성 | 내용 |
|---|---|---|
| `pairwise_bf_matrix_vX.json` | htt 신규 | 15×15 pairwise Bayes factor + Jeffreys category |
| `information_criteria_vX.json` | htt 신규 | DIC/WAIC/BIC/AIC × 15 models |
| `bma_weights_vX.json` | htt.analysis_extended 확장 | Bayesian model averaging posterior weights |
| `channel_contribution_vX.json` | htt.advanced_diagnostics.ChannelEstimate | 7 channels × 15 models ln Z 기여 |
| `dataset_contribution_vX.json` | htt 신규 | 4 datasets × 15 models |
| `lrange_contribution_vX.json` | htt 신규 | ℓ=2, ℓ=3, ℓ>10 contribution |
| `direction_alignment_matrix_vX.json` | htt.geometry_discrimination 확장 | 5×5 alignment + σ |
| `tension_statistics_vX.json` | htt 신규 | Suspiciousness / log-R / PTE per pair |
| `common_axis_bf_vX.json` | htt 신규 | 공통 축 가설 BF |
| `shared_cause_result_vX.json` | htt.infer.shared_cause | 결과 확장 |
| `systematic_budget_vX.json` | htt 신규 | foreground / beam / calibration / mask 기여 |
| `foreground_cleaner_comparison_vX.json` | htt 신규 | SMICA/Commander/NILC/SEVEM |
| `mask_inpainting_sensitivity_vX.json` | htt 신규 | apodization × posterior drift |
| `retention_vs_posterior_vX.json` | htt 신규 | ZoA ladder × posterior shift |
| `cross_channel_coherence_vX.json` | htt.advanced_diagnostics.CrossChannelCoherence | 7×7 matrix |
| `loocv_report_vX.json` | htt.advanced_diagnostics.LeaveOneOutCV | per-model Δln Z |
| `posterior_predictive_vX.json` | htt.advanced_diagnostics.PosteriorPredictive | χ²/ndof + p-value |
| `bayesian_pvalue_vX.json` | htt 신규 | 15 models × 7 channels |
| `pull_distribution_vX.json` | htt 신규 | (obs-model)/σ 분포 모수 |
| `qq_residuals_vX.json` | htt 신규 | residual Q-Q 통계 |
| `redshift_tomography_vX.json` | htt.advanced_diagnostics.DepthTomography | 5 z-bin 결과 |
| `beta_z_trajectories_vX.json` | htt.tilted_flrw + models | 15 models 이론 curves |
| `axis_migration_vX.json` | htt 신규 | dz/dθ slope per model |
| `anomaly_atlas_vX.json` | htt 신규 | cold spot / axis of evil / CatWISE / Bianchi 종합 sky meta |
| `hemispherical_asymmetry_vX.json` | htt 신규 | N/S power ratio per model |
| `parity_asymmetry_vX.json` | htt 신규 | even/odd ℓ ratio per model |
| `fisher_forecast_euclid_vX.json` | htt 신규 | Fisher matrix + parameter constraints |
| `fisher_forecast_so_vX.json` | ↑ | SO EE |
| `fisher_forecast_litebird_vX.json` | ↑ | LiteBIRD B-mode |
| `abc_forecast_vX.json` | htt 신규 | ABC forward model results |
| `mcmc_diagnostics_vX.json` | dynesty 래퍼 | trace / ESS / R̂ / autocorr |
| `model_identifiability_audit_vX.json` | htt.pipeline phase 3g | inactive parameter 검출 |

#### §12.2bis MIO 전용 artifacts (v3 신규, prefix `mio_`)

| 파일 | 생성 | 내용 |
|---|---|---|
| `mio_sigma2_per_ell_vX.json` | `mio.extraction.shear_nonparametric` | ℓ별 Σ²_MIO + cosmic variance error per scenario |
| `mio_ell_independence_test_vX.json` | `mio.extraction` | χ² + p-value for "Σ²(ℓ) = const" |
| `mio_stf_shear_components_vX.json` | `mio.extraction.biposh_inversion` | 5 STF components σ_2M + preferred direction + cone |
| `mio_beta2_nonparametric_vX.json` | `mio.extraction.tilt_nonparametric` | β²_MIO(ℓ) (v3 추가) |
| `mio_directional_coherence_vX.json` | `mio.coherence.directional` | 5-probe resultant R, (l_best, b_best), Fisher p-value |
| `mio_pairwise_separations_vX.json` | `mio.coherence` | 5×5 angular separation matrix + significance |
| `mio_redshift_coherence_vX.json` | `mio.coherence.redshift_binned` | z-bin별 probe direction + drift rate |
| `mio_flrw_tension_ppp_vX.json` | `mio.tension.flrw_tension` | T_directional, T_biposh, T_isotropy_per_ell PPP p-values |
| `mio_xc_direct_estimate_vX.json` | `mio.tension.xc_estimator` | x_C posterior-free estimate + σ_x |
| `mio_evidence_anatomy_vX.json` | `mio.decomposition.evidence_anatomy` | channel / z-bin / parameter 별 Δln B |
| `mio_evidence_flow_diagram_vX.json` | `mio.decomposition` | data → parameter → evidence flow metadata |
| `mio_redshift_evidence_tomo_vX.json` | `mio.decomposition.redshift_tomography` | recomb / post-recomb / reion 분해 |
| `mio_predictive_residuals_vX.json` | `mio.diagnostics.predictive_residuals` | per-model / per-channel residual atlas |
| `mio_model_failure_map_vX.json` | `mio.diagnostics` | where each model fails (ℓ × channel) |
| `mio_certificates/` directory | `mio.diagnostics.adequacy_certificates` | per-claim `MioCertificate` JSON files |
| `mio_masked_sky_caveats_vX.json` | `mio.diagnostics.masked_sky_caveats` | sky coverage + mask propagation meta |
| `mio_htt_cross_check_table_vX.json` | `mio.interface.htt_cross_check` | Σ²_HTT vs Σ²_MIO, direction_HTT vs direction_MIO (**not merged**, 단순 대조) |
| `mio_pr13am_te_sign_vX.json` | `mio.bridges.PR13AM` | TE sign from D1/D3 patterns |

**핵심 명명 규칙**: MIO artifact는 반드시 `mio_` 접두 + subpackage 이름 포함. HTT artifact와 **시각적으로 구분** (G19 enforcement의 첫 번째 방어선).

### 12.3 HDF5 / NPZ 데이터 제품 (확장)

| 파일 | 생성 | 내용 | 예상 크기 |
|---|---|---|---|
| `posterior_samples_<model>_<scenario>.hdf5` | Mode 2 dynesty | θ samples + logwt + logz + diagnostics | 10-50 MB × 75 runs = ~2 GB |
| `bass_py_cl_ensemble_vX.npz` | bass.spectrum (W10-02) | FLRW D_ℓ + Bianchi D_ℓ(m) channel-별 | ~10 MB |
| `w_r_window_ensemble.npz` | W12-01 | W_R(r/R_0) profile per R_0 | ~5 MB |
| `biposh_coefficients.npz` | W11-02 | A^{LM}_{ℓ₁ℓ₂} complex array | ~20 MB |
| `three_signature_templates.npz` | W14-01 | T_ℓ^{TT,EE} per signature | ~5 MB |
| `theta4_bridge_coeffs.json` | tsc.charts (신규) | a₂, a₄, a₆, a₈ ground-truth | < 1 MB |
| `healpix_completeness_map.fits` | healpix_selection | C_pix map | ~1 MB |
| **(신규) `evidence_cube.npz`** | htt.pipeline | 3D: 15 models × 5 scenarios × 5 nulls | ~5 MB |
| **(신규) `systematic_cube.npz`** | htt 신규 | 3D: 15 models × 5 foreground cleaners × 3 beam scenarios | ~5 MB |
| **(신규) `channel_contribution_matrix.npz`** | ChannelEstimate | 15 × 7 matrix with uncertainty | ~1 MB |
| **(신규) `cross_channel_coherence.npz`** | CrossChannelCoherence | 7×7 symmetric × 15 models | ~1 MB |
| **(신규) `ppc_residuals.hdf5`** | PosteriorPredictive | residual samples × 15 × 5 | ~500 MB |
| **(신규) `zbin_posterior_samples.hdf5`** | DepthTomography | 5 z-bin × 15 models × N samples | ~500 MB |
| **(신규) `fisher_matrices.npz`** | Fisher forecast | 7 params × 7 params × 4 surveys | < 1 MB |
| **(신규) `abc_forward_samples.hdf5`** | ABC / SBI | ~10⁵ forward simulations | ~1 GB |
| **(신규) `mcmc_chain_metadata.json`** | dynesty | per-run nlive, ncall, dlogz, wall time | < 1 MB |
| **(신규) `null_mock_bank.hdf5`** | htt.nulls + mock_calibration | 1000 realizations × 5 families | ~2 GB |
| **(신규) `injected_dipole_mocks.hdf5`** | mock_calibration | injected-signal mocks | ~500 MB |
| **(신규) `anomaly_meta.json`** | htt 신규 | cold spot, axis of evil, CatWISE 메타데이터 집계 | ~1 MB |

**총 data product 부피 추정**: ~8 GB (public release에는 subset만, 나머지 Zenodo link)

### 12.4 LaTeX table sources (자동 생성, 확장)

#### 기존

| 파일 | 출처 | 대상 chapter |
|---|---|---|
| `table_15model_evidence.tex` | pipeline phase 5 | ch07 T04 |
| `table_bounds.tex` | pipeline phase 5 | ch04 T06 |
| `table_departure.tex` | pipeline phase 5 | ch07 T08 |
| `table_nl.tex` | pipeline phase 5 | ch05 |
| `table_null_fpr.tex` | htt.nulls.runner | ch08 T15 |
| `table_matched_complexity.tex` | htt.infer.matched_complexity | ch06 T16 |
| `table_zoa_3mode.tex` | §6 patch 후 신규 | ch08 T21 |
| `table_mock_coverage.tex` | mock_calibration | ch08 T22 |

#### 신규 (§11.8 Table T33–T75 연동)

| 파일 | 출처 |
|---|---|
| `table_pairwise_bf.tex` | htt 신규 | T33 |
| `table_information_criteria.tex` | htt 신규 | T34 |
| `table_bma_weights.tex` | htt.analysis_extended | T35 |
| `table_nested_sd_bfs.tex` | htt.advanced_diagnostics.SavageDickeyRatio | T36 |
| `table_occam_factor.tex` | htt 신규 | T37 |
| `table_prior_sensitivity.tex` | htt 신규 | T38 |
| `table_param_posteriors_full.tex` | dynesty posteriors | T41 (A13 dossier 연계) |
| `table_correlation_topn.tex` | 신규 | T42 |
| `table_degeneracy_pca.tex` | 신규 | T43 |
| `table_nuisance_marginal.tex` | htt.infer.survey_nuisance | T44 |
| `table_channel_contribution.tex` | ChannelEstimate | T48 |
| `table_dataset_contribution.tex` | 신규 | T49 |
| `table_lrange_contribution.tex` | 신규 | T50 |
| `table_cross_channel.tex` | CrossChannelCoherence | T52 |
| `table_direction_alignment.tex` | 신규 | T54 |
| `table_tension_statistics.tex` | 신규 | T55 |
| `table_common_axis_bf.tex` | 신규 | T56 |
| `table_systematic_budget.tex` | 신규 | T60 |
| `table_foreground_cleaner.tex` | 신규 | T64 |
| `table_zoa_retention_drift.tex` | 신규 | T65 |
| `table_ess_per_param.tex` | dynesty wrapper | T66 |
| `table_chain_duration.tex` | dynesty wrapper | T67 |
| `table_gelman_rubin.tex` | 신규 | T68 |
| `table_ppc_chi2.tex` | PosteriorPredictive | T70 |
| `table_bayesian_pvalue.tex` | 신규 | T71 |
| `table_pull_moments.tex` | 신규 | T72 |
| `table_fisher_forecast.tex` | Fisher | T73 |
| `table_abc_forecast.tex` | ABC | T74 |
| `table_improvement_factor.tex` | 신규 | T75 |

### 12.5 공개 저장소 구조 (확장, Zenodo link 포함)

```
github.com/jiwon/bianchi-bass-py/
├── bass/                    # solver (Python 저-ℓ)
├── tsc/                     # admissibility/charts
├── htt/                     # inference (v8.3.0 안정화 후 v9.0 개명 후보)
├── src/common/              # §6 신규 공통 모듈
├── workspace/
│   ├── contracts/           # 패키지 간 dataclass 계약
│   ├── data/                # obs_defaults.json + external catalogs (large → external)
│   ├── pipeline/            # run_integrated.py
│   └── results/             # Mode별 artifact들 (lightweight metadata만)
├── docs/
│   ├── design/              # 본 문서 (v2) + MASTER_PROMPT_LIST
│   ├── packets/             # W3~W15 packet들
│   └── dossier/             # A13 15-model dossier markdown
├── manuscript/              # ch*.tex, figures/ (post-submission)
├── notebooks/               # 재현 jupyter notebooks
│   ├── reproduce_route_b.ipynb
│   ├── reproduce_15model_evidence.ipynb
│   ├── reproduce_3signature.ipynb
│   ├── reproduce_direction_posterior.ipynb
│   ├── reproduce_null_competition.ipynb
│   ├── reproduce_anomaly_atlas.ipynb
│   └── reproduce_fisher_forecast.ipynb
└── reproducibility/
    ├── env.yml              # conda env spec
    ├── docker/              # optional
    ├── scripts/
    │   ├── reproduce_d2.py
    │   ├── reproduce_15model.py
    │   ├── reproduce_3signature.py
    │   ├── reproduce_systematic_budget.py
    │   └── reproduce_fisher.py
    └── zenodo_link.txt      # HDF5 / big NPZ 외부 링크
```

### 12.6 Reproducibility 메타데이터 (artifact별 필수 필드)

모든 artifact에 다음 메타 필드를 embedded:

| 필드 | 예시 값 |
|---|---|
| `generated_by` | `bass_py.spectrum.cl_assembly.v2.3.1` |
| `git_commit` | `a1b2c3d...` |
| `config_hash` | SHA256 of config JSON |
| `input_data_hashes` | list of SHA256 for input files |
| `random_seed` | 42 (if stochastic) |
| `wall_time_sec` | integer |
| `python_version` | "3.12.1" |
| `numpy_version` | "1.26.4" |
| `dynesty_version` | "2.1.4" (if applicable) |
| `claim_tier` | "ESTABLISHED" / "CONDITIONAL" / "EXPLORATORY" |
| `scope_label` | "diagnostic" / "baseline" / "fiducial" |
| `production_allowed` | bool |

### 12.7 Analysis workflow 재현 (notebooks)

| Notebook | 실행 시간 (추정) | 의존 |
|---|---|---|
| `reproduce_route_b.ipynb` | < 1 분 | bass_py |
| `reproduce_15model_evidence.ipynb` | ~2 시간 | htt 전체 |
| `reproduce_3signature.ipynb` | ~30 분 | bass_py + htt |
| `reproduce_direction_posterior.ipynb` | ~15 분 (Mode 2 single model) | src/common + htt |
| `reproduce_null_competition.ipynb` | ~4 시간 (N=100 realizations) | htt.nulls |
| `reproduce_anomaly_atlas.ipynb` | < 5 분 | htt |
| `reproduce_fisher_forecast.ipynb` | < 5 분 | htt + Fisher module |
| **총** | ~7 시간 (전체 재현) | — |

---

## §13. Timeline (Phase별 상세)

### 13.1 Phase A — Apr–May 2026: Foundation + ZoA P0 수정

| Week | 작업 | 담당 영역 | Gate |
|---|---|---|---|
| Apr W3–W4 | §6 common 모듈 7종 초기 작성 (sky_geometry, healpix_selection 우선) | `src/common/` | unit test green |
| Apr W5 | PR13AM P0 수정 (production_mode 파라미터) + test | `src/mio/` | test_production_mode_rejects_uniform_fallback PASS |
| May W1 | PR13AJ P0 수정 (PreferredAxis gate) + test | `src/htt/` | test_preferred_axis_gate_blocks_diagnostic PASS |
| May W2 | `FLRW_tilt_zoa20_mean` downstream default 제거 + 전수 검색 | 전체 | grep 0 hits |
| May W3 | T_CMB SSOT 불일치 해결 (bass: 2.7255 vs htt: 2.72548) | SSOT | 단일 값 수렴 |
| May W4 | W10-02 FLRW → CAMB V-gate | `bass.spectrum` | rel_err < 5% |

### 13.2 Phase B — May–Jun 2026: Inference layer

| Week | 작업 | 담당 |
|---|---|---|
| Jun W1 | bulkflow_estimator.py + bulk_flow_mask_ladder | `src/common/` |
| Jun W2 | bulkflow_likelihood.py + prior_transform | `src/common/` |
| Jun W3 | dynesty runner + DynestyResult contract | `src/common/` |
| Jun W4 | W11-01 Direction-dependent C_ℓ(n̂) | `bass.los` |

### 13.3 Phase C — Jun–Jul 2026: Mock calibration + W12

| Week | 작업 | 담당 |
|---|---|---|
| Jul W1 | mock_calibration.py (run_zoa_null_mocks, run_injected_dipole_mocks) | `src/common/` |
| Jul W2 | W12-01 W_R window + regularity guards | `bass.validation` |
| Jul W3 | W12-02 Frame-attribution bias channel | `bass.tilt` |
| Jul W4 | W11-02 BiPoSH coefficients | `bass.los` |

### 13.4 Phase D — Jul–Aug 2026: β → D_2 + fiducial Mode 2

| Week | 작업 | 담당 |
|---|---|---|
| Jul W5 | W13-01 Dynamical tilt source | `bass.transport` |
| Aug W1 | W13-02 β → D_2 transfer function | `bass.spectrum` |
| Aug W2 | posterior_summary.py + axis_from_posterior | `src/common/` |
| Aug W3 | HTT pipeline.py refactor: 7 phases → 10 phases (ZoA 3-mode 분리 포함) | `htt.core` |

### 13.5 Phase E — Aug–Sep 2026: **W14-01 핵심 deliverable**

| Week | 작업 | 담당 |
|---|---|---|
| Aug W4 | W14-01 설계 고정 (templates spec + fit spec) | design review |
| Sep W1 | W14-01 module 초기 구현 (3 templates + α fit) | `bass.spectrum` / 신규 |
| Sep W2 | Synthetic mock fit 검증 (pure signal recover < 5%) | unit test |
| Sep W3 | Planck TT + EE 비교 1차 iteration | integration |
| Sep W4 | ch07 §7.6 초안 + figure F41, F42 | manuscript |

### 13.6 Phase F — Sep–Oct 2026: Null competition + HTT stabilization + **MIO HJ-02**

| Week | 작업 | 담당 |
|---|---|---|
| Oct W1 | HTT nulls.runner sys.path 정리 + smoke test green | `htt.nulls` |
| Oct W1 | **MIO HJ-02 Cross-channel directional coherence** (독립 실행 가능, 데이터만 필요) | `mio.coherence.directional` |
| Oct W2 | 5 null family FPR heatmap (N1~N5 × 15 models) | figure F49 |
| Oct W2 | **MIO HJ-02b Redshift-binned coherence** | `mio.coherence.redshift_binned` |
| Oct W3 | W15-01 Sky geometry + ZoA handling (common 모듈 통합) | `htt` |
| Oct W3 | **MIO interface contracts** (`MioCertificate`, `HttForwardOutput`) 정의 | `workspace/contracts/` |
| Oct W4 | W15-02 WLS + dynesty posterior (bulk-flow likelihood) | `htt` |
| Oct W4 | **MIO HJ-01 Non-parametric Σ² extraction** (K_ℓ atlas from bass_py 필요) | `mio.extraction.shear_nonparametric` |

### 13.7 Phase G — Oct–Nov 2026: W15-03 + tsc 확장 + **MIO HJ-03~04**

| Week | 작업 | 담당 |
|---|---|---|
| Nov W1 | W15-03 Mock calibration + production gate | `htt` + `src/common/` |
| Nov W1 | **MIO HJ-03 FLRW tension metric + x_C estimator** | `mio.tension.*` |
| Nov W2 | tsc.admissibility.test_realizability (300 L, 35 tests) | `tsc` |
| Nov W2 | **MIO HJ-04 Evidence anatomy + redshift tomography** (HTT posterior 필요 → HTT Phase F 완료 후) | `mio.decomposition.*` |
| Nov W3 | tsc.diagnostics.filling_fraction + three_bound_hierarchy | `tsc` |
| Nov W3 | **MIO HJ-05 Predictive diagnostics + adequacy certificates** | `mio.diagnostics.*` |
| Nov W4 | tsc.integration.htt_bridge (F_Bayes cross-check) | `tsc` |
| Nov W4 | **MIO htt_cross_check + G19 enforcement tests** | `mio.interface.*` |

### 13.8 Phase H — Nov–Dec 2026: Manuscript 확장 + **ch12 MIO Observatory Results**

| Week | 작업 | 담당 |
|---|---|---|
| Nov W5 | ch06 Pipeline 확장 (+1,700 L) + MIO pipeline 서술 | manuscript |
| Dec W1 | ch07 Results 확장 (+2,200 L) + figure 전체 regen | manuscript |
| Dec W1 | **ch12 MIO Observatory Results 초안** (§12.1~12.3 — Σ²_MIO, coherence, tension) | manuscript |
| Dec W2 | ch08 Robustness 확장 (+1,000 L) | manuscript |
| Dec W2 | **ch12 §12.4~12.6** (evidence anatomy, predictive residuals, HTT cross-check) | manuscript |
| Dec W3 | ch09 Discussion 확장 (+900 L) + CatWISE 해석 + MIO 결과 해석 | manuscript |
| Dec W3 | **ch11 재구성** (MioCertificate semantic rule + G19 + 분산 소유) | manuscript |
| Dec W4 | Appendix A1~A12 + A31~A40 MIO appendix 작성 (+4,200 L) | manuscript |

### 13.9 Phase I — Dec 2026–Jan 2027: Revision + submission

| Week | 작업 | 담당 |
|---|---|---|
| Jan W1 | 전체 banned-vocab scan (chapter별) | manuscript QA |
| Jan W2 | 60+ figure 300 DPI 재생성 + palette 통일 | pipeline |
| Jan W3 | Independent verification scripts 전체 실행 | regression |
| Jan W4 | arXiv + journal submission | final |

### 13.10 외부 이벤트 정렬

| 외부 이벤트 | 예상 시점 | 본 연구 영향 |
|---|---|---|
| Euclid DR1 release | ~Oct 2026 (불확실) | Phase F~G 중 Euclid 포함 옵션 추가 |
| DESI DR2 | 2026–2027 | Phase G 중 dynamical DE 비교 추가 |
| Simons Observatory | 이미 운영 | ch10 forecast 참조 |
| LiteBIRD | ~2033 (revised) | ch10 long-term outlook |

---

## §14. Risk Register (v2 확장)

### 14.1 과학적 리스크

| 리스크 | 영향 | 확률 | 완화 |
|---|---|---|---|
| W14 3-signature templates 선형 근사 붕괴 | High | Low | Σ² < 10⁻⁴ 영역으로 production claim 한정 |
| W13 β-dynamical source 수식 오류 | High | Medium | 2-step audit (PHYS-MATH → PHYS-MATH-CODE) + tsc cross-check |
| CAMB reference 불일치 > 5% | Medium | Medium | Sobolev A1~A5 가정 완화 명시 + rung-1 tag 유지 |
| 15-model evidence 간 degeneracy | Medium | High | matched-complexity 강제, evidence decomposition 분석 |
| Filling fraction F_Bayes 의존성 재확인 결과 불일치 | Low | Low | tsc 신규 모듈에서 independent 계산 |

### 14.2 HTT 재설계 리스크

| 리스크 | 영향 | 확률 | 완화 |
|---|---|---|---|
| **Uniform fallback 제거 후 기존 artifact 대량 재생성** | Medium | High | 호환 모드 (`allow_uniform_fallback=True`) 유지하되 production output에만 gate |
| **`FLRW_tilt_zoa20_mean` 참조 잔존** | High | Medium | grep 전수조사 + Phase A 종료 gate |
| Mock calibration coverage 목표 미달 | High | Medium | 실패 시 Mode 2 → Mode 1 강등 + ch08 §8.10에 한계 명시 |
| dynesty 수렴 실패 (15-model × 5-scenario = 75 runs) | Medium | Medium | nlive=1200 (upscale 시 2400), `sample='rwalk'` for ndim ≤ 4 |
| HEALPix completeness map 과적합 | Medium | Low | smooth_sigma_pix 다중 값 검증 (1, 2, 4 pix) |
| HTT 기존 test sys.path 의존성 | Low | High | Phase F에서 pytest conftest 정리 |

### 14.3 통합 리스크

| 리스크 | 영향 | 확률 | 완화 |
|---|---|---|---|
| bass_py → htt `BASSDirectionalBundle` 스펙 불일치 | High | Medium | Phase D에서 contracts.py에 frozen spec |
| htt ↔ tsc F_Bayes 값 ≠ | Medium | Low | Phase G에서 automated cross-check test |
| T_CMB SSOT 불일치 (2.7255 vs 2.72548) | Medium | **High (확인됨)** | Phase A W3에서 단일 값 결정 |
| Manuscript ch03 Framework 이미 3,564 L (최대) | Low | High | 필요시 ch03 분할 고려 (3a/3b) |

### 14.4 일정 리스크

| 리스크 | 영향 | 확률 | 완화 |
|---|---|---|---|
| W14 지연 (Aug–Sep → Oct로 slip) | High | Medium | Phase F 시작 지점 조정, Mode 1 baseline로 ch07 §7.6 작성 개시 |
| Euclid DR1 지연 (>Nov 2026) | Low | Medium | CF4++ + CatWISE + NVSS+RACS로 Phase F~G 진행 |
| Phase H 분량 폭주 | Medium | High | Appendix 적극 활용 + ch03 분할 |

### 14.5 MIO-specific 리스크 (v3 신규)

| 리스크 | 영향 | 확률 | 완화 |
|---|---|---|---|
| **G19 violation 조용히 발생** (MIO certificate score와 HTT BF가 코드 어딘가에서 합산) | **High** | Medium | CI lint rule: `grep -r "MioCertificate.*\\+.*ln_B\\|sum.*Mio.*Htt"`; `MioCertificate.as_posterior_bundle()` → NotImplementedError |
| HJ-01 K_ℓ atlas 의존성 — bass_py W10-02 V-gate 미통과 시 Σ²_MIO 부정확 | High | Medium | HJ-01은 W10-02 완료 후에만 production 승인; 그 전까지는 diagnostic-only tag |
| ℓ-independence test 실패 (Σ²_MIO(ℓ) varies with ℓ) | Medium | Medium | "model misspecification signal"로 보고 — 실패 자체가 과학적 결과 |
| HJ-04 evidence anatomy의 consistency check 실패 (Σ channels Δln B ≠ total ln B to 10%) | Medium | Low | Interaction terms 탐지 → ch08 §8.20에 별도 섹션으로 보고 |
| **PR13AM uniform fallback** (v2 §6.1 P0)이 MIO 소유 코드에 남아있음 | High | Low | Phase A gate에서 MIO-소유 bridge 전수 검색 + production_mode 강제 |
| `MioCertificate` schema 변경이 downstream 모듈 깨뜨림 | Medium | Medium | dataclass frozen + schema hash 검증 + backward compat test |
| MIO HJ-02 isotropic mock false detection (p < 0.05 by chance) | Low | Low | n_sim ≥ 10,000 + Bonferroni correction |
| MIO figure가 HTT figure와 혼동되어 재할당 실패 | Low | Medium | 모든 MIO figure filename에 `mio_` 접두 강제, caption에 "[model-independent]" 태그 |
| `MioCertificate`를 "truth certificate"로 오해하는 서술 | Medium | **High** | ch11 §11.X에서 "MioCertificate는 진단 보고서, truth certificate 아님" 명시; ch12 §12.7 scope 재강조; manuscript reviewer 1순위 체크 |
| MIO가 HTT에 "posterior" 이름의 output 생성하도록 코드 변경됨 | High | Low | `mio.diagnostics.adequacy_certificates`에 `ValueError: MIO cannot generate posteriors` runtime guard |

---

## §15. Success Criteria

### 15.1 Quantitative PASS 기준

| 항목 | 기준 | 측정 |
|---|---|---|
| W10-02 FLRW V-gate | rel_err < 5% vs CAMB (ℓ = 2~30) | 수치 비교 |
| W11-03 Bianchi V-gate | bass_rs와 rel_err < 1% (bass_rs 완성 후) | cross-check |
| W14 template recovery | pure signal 복원 rel_err < 5% | mock |
| W15 mock coverage | 68% credible ∈ [0.60, 0.76] | 1000 realization |
| Null competition FPR | FPR(N1~N5) < 0.05 per family | N=100 realizations |
| LOOCV Δlog-evidence | \|Δln Z\| < 0.5 per removed datum | 15 models |
| PPC χ²/ndof | ∈ [0.5, 2.0] (68% models) | 15 models |
| **MIO HJ-01 FLRW null** | Σ²_MIO consistent with 0 at all ℓ (all\|Σ²_MIO\| < 2σ_ell) | synthetic FLRW |
| **MIO HJ-01 BI injection** | Σ²_MIO recovers injected value ± 2σ at injection ℓ | synthetic BI |
| **MIO HJ-01 ℓ-independence** | p > 0.05 for homogeneous shear injection | χ² test |
| **MIO HJ-01 direction** | within 10° of injected shear axis | STF inversion |
| **MIO HJ-02 isotropic null** | p > 0.05 (no false detection) | n=10,000 mocks |
| **MIO HJ-02 aligned mock** | p < 0.01 (detection) when all probes within 20° | mock |
| **MIO HJ-02 literature reproduction** | angular separations match published values ± 2° | CMB / CatWISE / CF4++ |
| **MIO HJ-03 FLRW PPP** | p > 0.05 for FLRW injection | N_mock = 1,000 |
| **MIO HJ-03 BI PPP** | p < 0.01 for BI injection at Σ² = 10⁻⁶ | Planck sensitivity |
| **MIO HJ-03 x_C estimate** | consistent with 0 for FLRW, nonzero (>2σ) for BI injection | direct estimator |
| **MIO HJ-04 anatomy consistency** | \|Σ channels Δln B − total ln B\| / \|total ln B\| < 10% | channel ablation sum |
| **MIO HJ-05 adequacy certificate coverage** | MioCertificate 생성된 claim ≥ 90% of published results | audit |
| **G19 enforcement tests** | 모든 G19 violation test green (`test_miocertificate_no_posterior_access`, `test_htt_cannot_ingest_miocertificate_as_likelihood`) | pytest |
| Full regression | ≥ **2,800** bass+tsc+htt+mio tests passing at Phase I | pytest |
| Prompt correction cycles | ≤ 2 평균 | log |
| Banned vocab violations | 0 per chapter | scan |
| SSOT drift | d2_convention.rs 값 불변 | anti-regression guard |

### 15.2 Qualitative 성공 지표

| 지표 | 달성 방식 |
|---|---|
| Manuscript self-containedness | 심사위원이 외부 참조 없이 본문만으로 이해 |
| Reproducibility | `reproducibility/scripts/reproduce_*.py` 전체 PASS |
| SSOT 규율 | 모든 상수가 단일 파일에서 tracing 가능 |
| Scope 투명성 | out-of-scope 요청 시 explicit `OutOfScopeError` + redirect |
| Production vs diagnostic 분리 | 모든 artifact 파일명에 `diag_` / `baseline_` / `fiducial_` 접두 |
| Mock calibration 의무화 | Mode 2 artifact는 mock_calibration_report 링크 필수 |
| Claim taxonomy | 모든 결과에 ESTABLISHED / CONDITIONAL / NOT_ESTABLISHED 태그 |
| **MIO / HTT hard separation** | `mio_` 접두 + caption `[model-independent]` 태그 + G19 enforcement tests 전체 green |
| **MIO scope 명시** | ch11에서 "MioCertificate는 진단 보고서, truth certificate 아님" 4회 이상 명시 |
| **Epistemic 분산 소유** | ch11 §11.X 표에서 각 모듈의 self-gating 매커니즘 명시 |

### 15.3 실패 시 비상 계획

| 실패 항목 | 비상 조치 |
|---|---|
| W14 template 분리력 < 2σ | ch07 §7.6을 "preliminary discrimination"으로 재기술 + ch10 post-submission 보완 |
| Mock coverage < 60% | Mode 2 → Mode 1 강등, ch08 §8.10에 한계 + 재보정 계획 |
| dynesty 수렴 실패 (>5 runs) | nlive 2x 증량, 실패 시 emcee 대체 + ch08 §8.9에 명시 |
| CAMB V-gate > 5% | Sobolev A1~A5 중 A3 (local linear velocity gradient) 완화 |
| Euclid DR1 지연 | CF4++ + CatWISE + NVSS+RACS 4-point만으로 충분 (ch10 future work에 Euclid 이관) |
| ch03 분량 폭주 | ch03을 ch03a (covariant decomposition) + ch03b (tilt dynamics)로 분할 |
| **MIO HJ-01 K_ℓ atlas 의존성 실패** (bass_py V-gate 미통과) | Σ²_MIO를 "provisional diagnostic"로 강등 + ch12 §12.1 limitation 섹션 |
| **MIO HJ-04 anatomy consistency >10%** | interaction terms 명시적 보고, ch12 §12.4 proviso 추가 |
| **MIO Phase J 전체 지연** | HJ-02 directional coherence 단독 보존 (독립 실행 가능), ch12 → 5 pages 축소, 나머지 HJ-01/03/04/05는 ch10 Future work |
| **G19 violation 발견 (코드에서 MIO+HTT score 합산)** | 즉시 CI block, code freeze, 해당 claim 재검토 |


---

## §16. DAG Execution Order

### 16.1 Critical Path (v2, ZoA 재설계 반영)

```
[A-P0] PR13AM + PR13AJ + PR13AH patch
    │
    ▼
[A]  W10-02 CAMB V-gate ─── [A] src/common Layer A (sky_geometry, healpix_selection)
    │                            │
    ▼                            ▼
[B]  W11-01 dir-dep C_ℓ    [B] src/common Layer B (bulkflow_estimator)
    │                            │
    ▼                            ▼
[B]  W11-02 BiPoSH         [B] src/common Layer C (bulkflow_likelihood)
    │                            │
    └──────────────┬─────────────┘
                   ▼
            [C] mock_calibration.py
                   │
                   ▼
            [C] W12-01, W12-02
                   │
                   ▼
            [D] W13-01, W13-02
                   │
                   ▼
            ╔═════════════════════╗
            ║ [E] W14-01 (핵심)    ║
            ╚═════════════════════╝
                   │
            ┌──────┴──────┐
            ▼             ▼
     [F] htt.nulls    [F] W15-01 sky
     runner           handling
            │             │
            └──────┬──────┘
                   ▼
            [F] W15-02 dynesty
                   │
                   ▼
            [G] W15-03 production gate
                   │
                   ▼
            [G] tsc 확장
                   │
                   ▼
            [H] Manuscript ch06/ch07 확장
                   │
                   ▼
            [H] ch08/ch09 확장 + appendix
                   │
                   ▼
            [I] Submission
```

### 16.2 병렬 가능한 branch

| Branch | 시작 가능 시점 | 독립성 |
|---|---|---|
| HTT core stabilization (sys.path cleanup + test green) | 현재 | ✓ (다른 W-prompt와 독립) |
| tsc.admissibility 테스트 복구 | 현재 | ✓ |
| tsc.diagnostics.filling_fraction | 현재 | ✓ |
| Manuscript ch03 Framework 확장 (R-TILT-02/03) | 현재 | ✓ |
| Manuscript ch06 bass_py 완료분 서술 | 현재 | ✓ |
| HTT 27 figure script sys.path 정리 | 현재 | ✓ |
| tsc.charts.theta4_bridge_verify | 현재 | ✓ |
| **MIO HJ-02 directional coherence** | **현재 (데이터만 필요)** | **✓ 완전 독립 — K_ℓ, HTT posterior 불필요** |
| **MIO interface contracts (HttForwardOutput, MioCertificate, AtlasEntry)** | 현재 | ✓ (DOC-03 III 기반 spec 고정) |
| **MIO bridges (PR13AM 계열) 안정화** | 현재 (P0 patch 이후) | ✓ |
| **Manuscript ch11 재구성** (MioCertificate semantic + 분산 소유) | 현재 | ✓ |

### 16.2bis MIO 전용 의존 관계 (G19 포함)

| MIO 모듈 | 의존 | 의존 사유 |
|---|---|---|
| HJ-01 shear_nonparametric | bass_py W10-02 (K_ℓ atlas) | C_ℓ^LCDM 예측 + transfer kernel 필요 |
| HJ-01 biposh_inversion | W11-02 BiPoSH coefficients | σ_2M 역변환에 A^{LM}_{ℓ₁ℓ₂} 필요 |
| HJ-02 directional coherence | 없음 | 완전 데이터 기반 |
| HJ-03 flrw_tension | bass_py W10-02 | FLRW mock 생성에 K_ℓ 필요 |
| HJ-03 xc_estimator | tsc.diagnostics (departure 정의) | x_C = Σ²−W²+Ω_tilt+Ω_{k,aniso} 공식 |
| HJ-04 evidence_anatomy | HTT Phase F 완료 | HTT ln B 결과 분해 |
| HJ-04 redshift_tomography | HTT posterior + MIO HJ-03 | z-bin per-evidence |
| HJ-05 predictive_residuals | HTT 15-model posteriors | model-agnostic residual |
| HJ-05 adequacy_certificates | 모든 MIO + HTT 결과 | MioCertificate 생성 |
| htt_cross_check | HJ-01, HJ-03 + HTT posterior | Σ²_MIO vs Σ²_HTT 비교 (G19: merge 금지) |

### 16.3 블로킹 관계

| A | B | 블로킹 사유 |
|---|---|---|
| Phase A P0 patches | Phase B Layer A/B 구현 시작 | PreferredAxis / SkySelectionConfig 없이는 Layer 내부 gate 불가 |
| W13-02 | W14-01 | β → D_2 transfer 없이 3-signature template 미완 |
| W11-02 | W15-02 | BiPoSH 없이 direction likelihood 불완전 |
| W14-01 | htt.inference.likelihood 통합 | template이 likelihood 입력 |
| W15-02 | W15-03 | posterior 없이 coverage test 불가 |
| mock_calibration | Mode 2 production | 의무 전제 (review 지적) |
| ALL 완료 | ch07 Results | 결과 없이 결과 chapter 불가 |

---

## §17. 주간 / Phase 체크리스트

### 17.1 매주 금요일 체크리스트

- [ ] 이번 주 완료한 prompt가 DAG 순서와 일치하는가?
- [ ] Full regression (bass + tsc + htt + **mio**) 통과 확인
- [ ] 모든 신규 코드에 scope guard / `OutOfScopeError` 적용?
- [ ] 모든 새 artifact 파일명에 `diag_` / `baseline_` / `fiducial_` 접두?
- [ ] **모든 MIO artifact에 `mio_` 접두** + caption `[model-independent]` 태그?
- [ ] Banned-vocab scan 통과?
- [ ] Manuscript 해당 chapter에 reference 추가 (prose 증가 최소화)?
- [ ] d2_convention.rs + obs_defaults + htt.ssot 값 불변 확인?
- [ ] Independent verification script 작성?
- [ ] 신규 production 코드 경로에 uniform fallback 없음 확인?
- [ ] `FLRW_tilt_zoa20_mean` 참조 0건 유지 확인?
- [ ] **G19 enforcement tests green** (`test_miocertificate_no_posterior_access` 등)?
- [ ] **MIO 코드에 "posterior" 필드 생성 없음** 확인 (grep)?
- [ ] **MIO + HTT score 합산 없음** 확인 (lint)?
- [ ] **`MioCertificate` schema hash 불변** 확인 (backward compat)?


### 17.2 Phase 종료 체크리스트

- [ ] 해당 phase의 모든 prompt / patch 완료 + packet 작성
- [ ] Full regression + smoke test 통과
- [ ] Manuscript 해당 chapter에 결과 반영 (최소 1 figure + 1 table)
- [ ] Mock calibration 결과 (해당 phase가 Mode 2 경로 포함하는 경우) 검증
- [ ] `bass_py.zip` 재생성 + `present_files`
- [ ] 3-tier claim taxonomy 태그 모든 결과에 적용
- [ ] 다음 phase 설계안 작성 + 승인 gate

### 17.3 Phase A 종료 gate (특히 critical)

- [ ] **P0-1**: PR13AM production_mode flag 동작 확인 → test_production_mode_rejects_uniform_fallback PASS
- [ ] **P0-2**: PR13AJ PreferredAxis gate 동작 확인 → test_preferred_axis_gate_blocks_diagnostic PASS
- [ ] **P0-3**: `FLRW_tilt_zoa20_mean` downstream default 전수 제거 → `grep -r "zoa20_mean" src/` 0 hits
- [ ] T_CMB SSOT 단일값 수렴 → bass + htt 양측 같은 값
- [ ] W10-02 V-gate PASS (rel_err < 5%)
- [ ] 7종 `src/common/` 모듈 초기 구현 + unit test green
- [ ] Mock coverage smoke test (n=100, quick) 실행 가능

---

## §18. 결론 + 버전 히스토리

### 18.1 핵심 주장 정리 (v3, MIO 포함)

- **현 위치**: bass_py는 W10-01까지 완료 (14/24). HTT는 v8.3.0 prototype 이미 존재 (~15,400 L, 15 Bianchi evidence models + 5 null families + 27 figure scripts). tsc는 admissibility 테스트만 부재. **MIO는 신규 패키지 (PR13AM만 존재)**.
- **가장 critical한 블록**: (1) W14-01 Three-signature discriminator + (2) HTT ZoA 재설계 P0 3건 + (3) **MIO Phase J HJ-01~05 신규 구현**.
- **MIO의 정확한 역할 (DOC-03 기반)**:
  1. **Model-Independent Observatory** — physics-producing, 모델 가정 없이 측정
  2. 5 subpackage: `extraction` / `coherence` / `tension` / `decomposition` / `diagnostics`
  3. Output은 `MioCertificate` — **진단 보고서**, truth certificate 아님, posterior 아님
  4. HTT와 **hard separation (G19)** — 단일 inferential score로 절대 합산 금지
  5. Cross-check만 허용, merge 금지
- **Epistemic control 분산 소유**: 각 모듈이 자체 gating (bass.runtime, tsc.admissibility, htt.infer, mio.diagnostics). MIO는 더이상 중앙 certification engine이 아님 (v2 오해 교정).
- **HTT 재설계 요점**:
  1. ZoA 20°는 diagnostic 안정화값이지 production axis가 아님
  2. Uniform fallback은 diagnostic_only, production_mode에서는 예외
  3. Production axis는 mock-calibrated fiducial posterior에서만 생성
  4. 3 conceptual layer (diagnostic / inference / synthesis) 라벨링 전면 도입
  5. HEALPix + dynesty + SciPy + astropy 기반 CPU 4-layer, JAX 없음
- **bass_rs 경계**: 이 계획은 Rust 솔버 없이 닫힘. 첫 원리 D_2 재현은 Route B lookup으로 대체 (현재 완료).
- **외부 일정 정렬**: Euclid DR1 (~Oct 2026) → Phase F~G, DESI DR2 → Phase G.
- **총 작업량**: ~18,000 신규 코드 + ~5,800 manuscript 확장 + ~1,630 신규 테스트. 8~9개월 (Apr 2026 ~ Jan 2027).

### 18.2 Scientific impact (manuscript 완성 시 예상, MIO 포함)

| 결과 영역 | Impact |
|---|---|
| 15-model Bianchi evidence (HTT) | 본격적 model selection (점 추정이 아닌 Bayes factor 순서) |
| 3-signature discriminator (HTT + bass_py) | local / cosmological / tilt² 분리 — CatWISE vs CMB 텐션 해석 근거 |
| F_Bayes = 0.093 ± 0.025 (HTT + tsc) | Filling fraction으로 anomaly를 증거로 재해석 |
| 5 null family FPR (HTT) | anomaly claim의 systematic 기여 정량화 |
| Mock calibration 표준 (common) | 향후 tilt 우주론 inference의 reproducibility 기준 제시 |
| **Σ²_MIO(ℓ) 비모수 추출 (MIO)** | **모델 가정 없이 anisotropic shear 직접 측정 — "데이터에 Σ²/H가 있나?"** |
| **ℓ-independence test (MIO)** | **homogeneous shear 가설의 독립 검증 — model misspecification signal** |
| **5-probe resultant coherence (MIO)** | **CatWISE / CMB / CF4++ / NVSS / RACS가 같은 축을 가리키는지 frequentist 판정** |
| **FLRW tension PPP (MIO)** | **어떤 alternative도 가정하지 않고 FLRW 배제 정량화** |
| **Evidence anatomy (MIO)** | **HTT ln B의 physics-level 분해 — "무엇이 evidence를 이끄는가"** |
| **HTT ↔ MIO cross-check (MIO)** | **model-dependent와 model-independent 결과의 독립 검증 layer** |
| Tsagas killing 반영 | khronon = tilted-Bianchi dipole 유일 생존 source임을 실증 |

### 18.3 주요 한계 (본 연구 scope 내)

- ℓ > 30 영역은 bass_py scope 밖 — bass_rs 완성 시 다음 논문
- Full non-linear Σ regime (Σ² > 10⁻⁴) 미포함
- B-mode는 Bianchi I에서 구조상 0
- Patchy reionization / dynamical recombination은 scope 밖
- Tilted Bianchi (ω_a ≠ 0) 배경의 polarization rotation은 미포함

### 18.4 버전 히스토리

| 버전 | 날짜 | 주요 변경 |
|---|---|---|
| v1.0 | 2026-04-18 | 최초 — HTT "신규 작성" 전제 |
| v2.0 (core) | 2026-04-18 | HTT v8.3.0 prototype 발견 → 전면 재작성; ZoA review 반영 (3-layer / 4-layer / 3-mode / 7 common 모듈 / PreferredAxis gate / production vs diagnostic 분리); manuscript figure 15 → 60+, table 10 → 32 |
| v2.0 (amplified) | 2026-04-18 | §11.6–§11.13 scientific amplification 추가: figure 60 → ~130, table 32 → ~75, appendix A1–A12 → A1–A30, ch07/ch08/ch09/ch10 50+ 신규 subsection, data products ~20 → ~55, full 15-model dossier, anomaly atlas, Fisher/ABC forecasting, MCMC diagnostics, scientific novelty claims audit, tier 우선순위 분류 |
| **v3.0 (MIO 통합)** | **2026-04-18** | **MIO를 4번째 기둥으로 통합. v2의 "MIO = epistemic control" 오해 전면 교정. DOC-03 기반 Model-Independent Observatory로 재정의. Phase J (HJ-01~05) 모듈 신규 (Σ² extraction, directional coherence, FLRW tension, evidence anatomy, predictive diagnostics). Interface objects (`HttForwardOutput`, `MioCertificate`, `AtlasEntry`) 추가. G19 hard separation rule. Epistemic control 분산 소유 명시. ch12 "MIO Observatory Results" 신규 chapter (~1,750 L). MIO figures F131–F145 (15개), tables T76–T82 (7개), appendix A31–A40 (10개). 코드 +3,000 L, manuscript +1,850 L.** |

### 18.5 다음 단계 (즉시 실행, v3 최신)

1. **Phase A 시작**:
   - `src/common/` 모듈 7종 중 `sky_geometry.py`부터
   - **`workspace/contracts/mio_certificate.py` + `htt_forward_output.py` + `atlas_entry.py` 정의** (DOC-03 III-2 기반)
   - PR13AM P0 패치 + test_production_mode_rejects_uniform_fallback 작성
2. **T_CMB SSOT 단일값 결정 meeting** (bass 2.7255 vs htt 2.72548)
3. **W10-02 CAMB reference 데이터 준비 요청**
4. **MIO Phase J 준비**:
   - HJ-02 directional coherence 선행 (독립 실행 가능, 데이터만 필요)
   - HJ-01 K_ℓ atlas 의존성 확인 (bass_py W10-02 완료 후)
   - `mio/` 패키지 디렉토리 구조 초안
5. Manuscript ch06 Pipeline 기존 827 L 구조 audit 후 확장 설계
6. **Manuscript ch11 재구성 초안** (MioCertificate semantic rule + G19 + 분산 소유)
7. HTT 27 figure script sys.path cleanup (Phase F 준비)
8. **G19 enforcement CI rule 설계** (lint + pytest 조합)

---

**문서 끝 — BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN v3.0**

---
