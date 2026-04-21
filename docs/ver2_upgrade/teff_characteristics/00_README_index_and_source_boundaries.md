# Teff-Characteristics Upgraded MD Series v1

상태: 통합/업그레이드/재정렬본 v1  
목적: 기존 Paper I-V 원고와 Teff-characteristics md 논의들을 하나의 거대 파일로 합치지 않고, claim의 지위와 범위를 분리한 문서 시리즈로 재구성한다.  
핵심 수정: `characteristics = full transport closure` 표현을 폐기하고, `characteristics = closure-free full-state transport backbone/reference`로 고정한다.

---

## 0. 이 시리즈의 상위 판정

이 문서 시리즈는 다음 판정을 반영한다.

1. Teff는 full solver가 아니다.
2. Teff는 trace/intensity block의 reduced statistical chart, semantic layer, source bridge, diagnostic layer다.
3. characteristics는 closure가 아니다. full state를 truncation 없이 운반하는 transport representation/backbone이다.
4. characteristics를 `full Boltzmann hierarchy solver`라고 부르면 안 된다. continuum/full-resolution limit에서 collision kernel, angle, energy, tensor/polarisation, species degrees of freedom을 실제로 보존하는 경우에만 `full-Boltzmann-class characteristic transport solver`라고 조건부로 쓸 수 있다.
5. Paper V의 Table II 수치는 방어 가능하지만, 본문에서 `Q P_2` convention과 `Q(\mu^2-1/3)` convention이 섞이면 안 된다.

---

## 1. 세 개의 원 구별

이 시리즈는 claim을 세 원으로 분리한다. 서로 섞으면 심사에서 가장 먼저 무너진다.

### 원 A: 현재 Paper I-V에서 이미 주장 가능한 결과

이 원에는 각 논문 원고 안에서 직접 성립하거나, 해당 논문이 명시적으로 범위를 제한한 결과만 넣는다.

- Paper I: per-ray, instantaneous, collision-side tangency diagnostic.
- Paper II: direction-dependent chemical potential dipole의 structural non-redundancy.
- Paper III: two-field manifold의 Gram-Hessian identity와 tangency structure.
- Paper IV: observable semantics와 conditional local reconstruction bound.
- Paper V: trace/intensity sector의 nonlinear Thomson source bridge와 polarisation scope boundary.

### 원 B: md 통합으로 정리되는 synthesis claim

이 원에는 Paper I-V를 함께 읽으면 자연스럽지만, 단일 paper 하나가 혼자 증명하지 않는 구조적 해석을 넣는다.

- full state와 reduced chart의 blockwise 분리.
- trace/intensity block과 spin-2 polarisation block의 responsibility map.
- ambient defect와 projected defect의 구분.
- characteristics backbone 위에서 Teff가 diagnostics/source semantics로 작동한다는 architecture claim.

### 원 C: 아직 proof/validation obligation인 future program

이 원에는 아직 정리, 구현, 수치 검증이 더 필요한 것을 둔다.

- full 1+3 covariant characteristic solver의 well-posedness와 convergence.
- full tensor/species direct-sum implementation.
- TT/TE/EE/BB spectrum-level adequacy.
- adaptive switching, realizability invariance, production-grade transport validation.

권장 문장: `원 A results support 원 B architecture; 원 C remains obligation, not established theorem.`

금지 문장: `Papers I-V prove a full Boltzmann hierarchy solver.`

---

## 2. 문서 구성

| 파일 | 역할 | 읽어야 하는 사람 |
|---|---|---|
| `00_README_index_and_source_boundaries.md` | 전체 색인과 세 원 구별 | 모두 |
| `01_constitution_scope_and_claim_language.md` | 헌법 문장, 금지어, 허용 claim | abstract/introduction 수정자 |
| `02_papers_I_to_V_upgrade_ledger.md` | Paper I-V별 수정 ledger | 논문별 리라이트 담당 |
| `03_reduction_geometry_and_theorem_compendium.md` | theorem chain과 defect 구조 | 수학/증명 담당 |
| `04_characteristics_architecture_closure_free_backbone.md` | closure-free characteristics architecture | solver 설계 담당 |
| `05_trace_intensity_semantics_and_polarisation_bridge.md` | Paper IV-V, trace/polarisation bridge, Q convention | CMB/polarisation 담당 |
| `06_proof_obligations_and_claim_status.md` | established/conditional/programmatic claim 분류 | 심사 대응 담당 |
| `07_validation_protocol_and_test_matrix.md` | Layer A/B/C/R 검증 계획 | numerical validation 담당 |
| `08_red_team_reviewer_defense.md` | 적대적 심사 질문과 방어문 | response letter 담당 |
| `09_patch_map_for_existing_md_and_manuscripts.md` | 기존 md/원고에서 바꿀 문장 map | 실제 patch 담당 |

---

## 3. 전역 convention

- Metric signature: `(-,+,+,+)`.
- 자연단위는 기본 선언하지 않는다. `c`, `\hbar`, `k_B` 등은 필요할 때 유지한다.
- 권장 dimensionless energy coordinate:
  \[
  x = \frac{E}{k_B T_0}.
  \]
- `closure`라는 단어는 moment truncation 또는 unresolved degrees of freedom의 constitutive replacement에만 쓴다.
- characteristics에 대해서는 `closure-free`, `full-state`, `transport representation`, `reference/backbone`을 쓴다.

---

## 4. 핵심 correction ledger

### C1. Characteristics terminology

Bad:

> Method of characteristics is the full transport closure.

Good:

> Method of characteristics provides a closure-free full-state transport backbone/reference. Teff supplies a blockwise reduced chart, source bridge, and diagnostic layer on selected sectors.

### C2. Full Boltzmann hierarchy solver terminology

Bad:

> The characteristic method is the full Boltzmann hierarchy solver.

Good:

> A resolved characteristic implementation belongs to the full-Boltzmann-class transport family only when the phase-space, species, collision, tensor, angular, frequency, and polarisation degrees of freedom retained by the target equation are actually resolved and convergence-tested.

### C3. Teff scope

Bad:

> Teff closes the full polarised Boltzmann hierarchy.

Good:

> Teff parameterises the scalar trace/intensity sector and gives an exact nonlinear source bridge for the Thomson intensity quadrupole when the trace block is on the Teff manifold. The spin-2 sector remains independent.

### C4. Paper V Q convention

Adopt one convention. If Table II is retained, use

\[
\Theta(\mu)=1+A\mu+Q\left(\mu^2-\frac13\right)
=1+A P_1(\mu)+\frac{2Q}{3}P_2(\mu),
\qquad
P_2(\mu)=\frac{3\mu^2-1}{2}.
\]

Then the linear quadrupole contribution is `8Q/3`, not `4Q`.

---

## 5. Source anchors used in this consolidation

Primary manuscript anchors:

- `P1_main(16).pdf`: Paper I, tangency criterion and entropy-projection inequality.
- `P2_main(17).pdf`: Paper II, direction-dependent chemical potential.
- `P3_main(15).pdf`: Paper III, entropy geometry and two-field tangency.
- `P4_main(20).pdf`: Paper IV, observable semantics and reconstructive adequacy.
- `P5_main(17).pdf`: Paper V, intensity semantics inside polarised radiative transfer.

Existing md anchors:

- `teff_characteristics_theorem_compendium_v19(9).md`
- `teff_characteristics_solver_architecture_note_v1(5).md`
- `teff_characteristics_proof_obligation_note_v1(7).md`
- `teff_characteristics_validation_protocol_note_v1(7).md`
- `teff_characteristics_validation_test_matrix_v1(7).md`
- `teff_characteristics_validation_runbook_v1(7).md`

These anchors are not merged wholesale. They are reorganised by claim status, not by original file order.
