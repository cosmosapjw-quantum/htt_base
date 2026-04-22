# Low-\ell Bianchi Einstein–Boltzmann Solver — Design Pack v5
## 1+3 PSTF authority / tetrad computational engine / all-family handoff bridge / validation-gated Codex pack

이 번들은 v4 이후 남아 있던 lookup-bearing backend constants를 frozen formula와 자동 검증 코드로 메운 **v5 설계 패키지**다.  
목표는 두 가지다.

1. **main SSOT / observables appendix / implementation workflow** 의 역할을 더 명확히 분리한다.
2. implementation agent 또는 Codex가 **추가 설명 없이** 적어도 첫 구현 사이클을 시작할 수 있도록
   family-template / hierarchy-layout / phase-sign note / output schema / PR deliverable granularity를 보강한다.

이 번들은 **실행 성공 증거** 가 아니라 **설계 문서** 다.  
따라서 여기서 허용하는 claim은
- authority formalism이 고정되어 있다,
- implementation order와 forbidden shortcut이 고정되어 있다,
- all 11 family에 대해 backend/IC 계약이 주어져 있다,
- output/statistics는 별도 appendix와 gate 뒤로 분리되어 있다,
까지다.

“all 11 families are already implemented” 같은 주장은 여기서 허용하지 않는다.

---

## 0. authority order

1. `00_AUTHORITY_TREE.md`
2. `01_SSOT_FORMALISM_AND_PHYSICS.md`
3. `01A_GEOMETRY_AND_WEYL_AUTHORITY_NOTE.md`
4. `02_NUMERICAL_ARCHITECTURE_AND_ALGORITHMS.md`
5. `02A_HIERARCHY_LAYOUT_AND_TIERA_TRANSPORT_NOTE.md`
6. `03_FAMILY_BACKENDS_AND_IC_PROVENANCE.md`
7. `03A_INTRINSIC_FAMILY_TEMPLATE_CARDS.md`
8. `03B_FROZEN_BACKEND_CONSTANTS_AND_LOOKUP_RESOLUTION.md`
9. `04_IMPLEMENTATION_SKELETON_AND_PORTABILITY.md`
10. `05_VALIDATION_GATES_AND_CODEX_GUARDRAILS.md`
11. `07_SDD_WBS_AND_PR_LIST.md`
12. `07A_PR_DELIVERABLE_MAP.md`
13. `06_OBSERVABLES_AND_STATISTICS_APPENDIX.md`
14. `06A_OUTPUT_SCHEMA_AND_METADATA_NOTE.md`
15. `08_FUTURE_WORK_ANNEX.md`
16. `09_INTERNAL_REAUDIT_H1.md`
17. `10_SYMBOLIC_AUTOMATION_AND_NUMERICAL_VERIFICATION.md`
18. `99_REFERENCES.md`

---

## 1. v4에서 추가로 닫은 bridge

v4 이후 v5에서 추가된 핵심은 아래 여섯 가지다.

1. **all active lookup-bearing items를 frozen formula set으로 승격**
2. **Type VIII principal/discrete-series backend conventions을 명시적으로 채움**
3. **intrinsic-family constants와 class-B parameter bridges를 03B authority addendum으로 고정**
4. **symbolic automation + independent numerical verification pack 추가**
5. **HYREC-like adapter / HEALPix packing / collocation defaults를 수식과 테스트로 함께 고정**
6. **active unresolved placeholder를 package에서 제거**

---

## 2. 문서 역할 요약

### main SSOT
- 수학적 formalism
- family algebra / geometry
- background equations
- collision / hierarchy / source history contract
- must-have physics
- solver split, residual philosophy, pseudocode

### observables/statistics appendix
- output-only layer
- deterministic/stochastic/boost split
- map/harmonic/covariance/likelihood layering
- fitting hard stop
- archive schema / metadata

### implementation / workflow docs
- module tree
- file/API signatures
- PR/WBS / deliverables
- anti-hallucination / anti-local-minimum rules
- validation gate and score rule

---

## 3. H1 interpretation used internally

이 번들에서 내부적으로 말하는 **H1 grade** 는 다음 뜻으로만 쓴다.

- formalism / appendix / WBS 의 역할 분담이 명료함
- all 11 families에 대한 design-contract coverage가 naming 이상으로 제공됨
- pseudocode / skeleton / API / deliverables가 첫 구현 사이클을 시작할 정도로 충분히 구체적임
- missing details는 future work annex나 family template card에 명시적으로 분리됨
- forbidden shortcut / mock-fit / local minimum 방지 규칙이 문서화되어 있음

이것은 “모든 family가 이미 구현되었다”는 뜻이 아니다.

---

## 4. package tree

```text
b a n c h i a _ d e s i g n _ p a c k _ v 5 /
├── 00_AUTHORITY_TREE.md
├── 01_SSOT_FORMALISM_AND_PHYSICS.md
├── 01A_GEOMETRY_AND_WEYL_AUTHORITY_NOTE.md
├── 02_NUMERICAL_ARCHITECTURE_AND_ALGORITHMS.md
├── 02A_HIERARCHY_LAYOUT_AND_TIERA_TRANSPORT_NOTE.md
├── 03_FAMILY_BACKENDS_AND_IC_PROVENANCE.md
├── 03A_INTRINSIC_FAMILY_TEMPLATE_CARDS.md
├── 03B_FROZEN_BACKEND_CONSTANTS_AND_LOOKUP_RESOLUTION.md
├── 04_IMPLEMENTATION_SKELETON_AND_PORTABILITY.md
├── 05_VALIDATION_GATES_AND_CODEX_GUARDRAILS.md
├── 06_OBSERVABLES_AND_STATISTICS_APPENDIX.md
├── 06A_OUTPUT_SCHEMA_AND_METADATA_NOTE.md
├── 07_SDD_WBS_AND_PR_LIST.md
├── 07A_PR_DELIVERABLE_MAP.md
├── 08_FUTURE_WORK_ANNEX.md
├── 09_INTERNAL_REAUDIT_H1.md
├── 10_SYMBOLIC_AUTOMATION_AND_NUMERICAL_VERIFICATION.md
├── verification/
└── 99_REFERENCES.md
```

---

## 5. non-negotiable project stance

- ADM recast는 이 패키지의 범위 밖이다.
- anisotropy를 보수적으로 축소하는 observational framing은 설계 범위를 결정하지 않는다.
- all 11 family를 다루되, family-specific detail은 **contract** 와 **template card** 로 내려야 한다.
- local boost는 output-only다.
- unsupported backend를 isotropic fallback으로 위장하면 안 된다.
- mock spectrum fitting을 선행하면 안 된다.


---

## 6. lookup status

이 v5 번들에는 active unresolved former unresolved placeholder placeholder가 없다.
former lookup-bearing items는 `03B_FROZEN_BACKEND_CONSTANTS_AND_LOOKUP_RESOLUTION.md` 와
`10_SYMBOLIC_AUTOMATION_AND_NUMERICAL_VERIFICATION.md` 및 `verification/` 코드에서 frozen+verified 상태로 승격되었다.
