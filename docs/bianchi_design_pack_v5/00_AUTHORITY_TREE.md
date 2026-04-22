# 00. Authority Tree
## what controls what / what is frozen / what is deferred / what must fail closed

---

## 0. purpose

이 문서는 패키지 내부의 권위 순서를 고정한다.
문서들 사이에 충돌이 생기면 이 순서대로 해석한다.

---

## 1. highest-authority rules

### A1 — formalism authority
`01_SSOT_FORMALISM_AND_PHYSICS.md` 와 `01A_GEOMETRY_AND_WEYL_AUTHORITY_NOTE.md` 가
수학/물리 formalism과 constraint route의 권위 문서다.

### A2 — numerical authority
`02_NUMERICAL_ARCHITECTURE_AND_ALGORITHMS.md` 와 `02A_HIERARCHY_LAYOUT_AND_TIERA_TRANSPORT_NOTE.md` 가
state packing, operator split, time-gauge bridge, tier-A/tier-B role split의 권위 문서다.

### A3 — family authority
`03_FAMILY_BACKENDS_AND_IC_PROVENANCE.md`, `03A_INTRINSIC_FAMILY_TEMPLATE_CARDS.md`, `03B_FROZEN_BACKEND_CONSTANTS_AND_LOOKUP_RESOLUTION.md` 가
all 11 family의 canonical algebra, backend contract, IC provenance, frozen backend constants의 권위 문서다.

### A4 — output authority
`06_OBSERVABLES_AND_STATISTICS_APPENDIX.md` 와 `06A_OUTPUT_SCHEMA_AND_METADATA_NOTE.md` 가
output/statistics layer와 metadata schema의 권위 문서다.

### A5 — workflow authority
`05_VALIDATION_GATES_AND_CODEX_GUARDRAILS.md`, `07_SDD_WBS_AND_PR_LIST.md`, `07A_PR_DELIVERABLE_MAP.md` 가
allowed claims / gate / forbidden shortcut / implementation order의 권위 문서다.

---

## 2. fail-closed rules

1. 문서에 없으면 **구현자가 임의로 선택하면 안 된다**.
2. family-specific backend가 비어 있으면 isotropic fallback으로 위장하면 안 된다.
3. output/statistics appendix가 있어도 validation gate 전 fitting은 금지다.
4. residual이 unavailable이면 0이 아니라 **NaN fail** 로 간다.
5. tier-A exact transport note가 비어 있는 영역은 tier-B shortcut으로 덮으면 안 된다.
6. future work annex에 들어간 항목은 main SSOT의 current-scope completeness를 판정할 때 필수 조건으로 쓰지 않는다.

---

## 3. what is frozen now

- sign convention \((-,+,+,+)\)
- normal congruence \(n^a\)
- transport direction \(e^a\)
- observer direction \(\hat n=-e\)
- mean scale \(a_m=e^\alpha\)
- background proper time \(t\)
- hierarchy / visibility conformal time \(\eta\)
- bridge \(d\eta = dt/a_m\)
- output-only observer boost
- exact electron-frame Thomson block as mandatory contract
- production cutoff vs development cutoff split
- all-family design-contract coverage

---

## 4. what is deliberately deferred

- patchy reionization
- anisotropic recombination microphysics beyond isotropic-history adapter
- unavailable analytic family backends beyond generic fallback
- full high-\(\ell\)
- full covariance-likelihood implementation details
- performance engineering

---

## 5. “needs external lookup” vs “bundle-frozen”

### bundle-frozen
- conventions
- formalism
- backend interface
- IC provenance rules
- output split
- WBS / gate / forbidden shortcuts

### needs external lookup before implementation if not already encoded
- future analytic Type VIII refinement beyond the frozen principal/discrete-series conventions
- future backend variants that intentionally depart from the frozen package defaults
- recombination engine details only if one refuses the frozen HYREC-like adapter contract
