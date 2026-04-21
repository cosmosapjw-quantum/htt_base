# 03. Family Backends and IC Provenance
## all 11 families / orthogonal vs global tilt / backend contract / seed rules / maturity matrices

---

## 0. scope

이 문서는 all 11 Bianchi family 각각에 대해 다음을 고정한다.

- canonical algebra data
- class A/B and isotropic-limit status
- orthogonal / global-tilt / local-boost interpretation
- preferred backend and generic fallback
- IC provenance rule
- minimum documentary maturity level

Detailed intrinsic-family template cards live in `03A_INTRINSIC_FAMILY_TEMPLATE_CARDS.md`.

---

## 1. maturity language

For this design pack:

- `registry-complete`: canonical metadata, class, branch, and sign conventions are frozen
- `backend-contract-complete`: preferred backend + generic fallback + translator contract are frozen
- `IC-contract-complete`: allowed seed provenance paths are frozen
- `release-complete`: all of the above plus implementation-side gates have passed

This pack claims at most:
- `registry-complete`
- `backend-contract-complete`
- `IC-contract-complete`

for all 11 families at the documentary level.

---

## 2. family completeness matrix

| family | class | isotropic anchor? | orthogonal/global tilt/local boost split | preferred backend | generic fallback | IC provenance status |
|---|---|---|---|---|---|---|
| I | A | yes | frozen | plane-wave / Cartesian | generic collocation | strong |
| II | A | no | frozen | nil-group / Heisenberg | generic collocation | template-card |
| III | B | no | frozen | hyperbolic / class-B branch | generic collocation | template-card |
| IV | B | no | frozen | solvable-group chart | generic collocation | template-card |
| V | B | yes | frozen | hyperbolic / open modes | generic collocation | strong |
| VI\(_0\) | A | no | frozen | solvable / intrinsic modes | generic collocation | template-card |
| VI\(_h\) | B | no | frozen | class-B \(h<0\) family backend | generic collocation | template-card |
| VII\(_0\) | A | yes | frozen | helical / Euclidean-like modes | generic collocation | strong |
| VII\(_h\) | B | yes | frozen | helical/open \(h>0\) modes | generic collocation | strong |
| VIII | A | no | frozen | \(SL(2,\mathbb R)\)-type backend | generic collocation | template-card |
| IX | A | yes | frozen | Wigner \(D\) / compact harmonic backend | generic collocation | strong |

---

## 3. local boost and global tilt across all families

### rule 1
Orthogonal and globally tilted backgrounds are background-layer concepts.

### rule 2
Local observer boost is never a background variable and never a perturbation backend variable.

### rule 3
All family cards must preserve this split:
- orthogonal background
- global tilt background
- output-only local boost

No family may fuse global tilt into the output-only boost layer.

---

## 4. backend contract shared by all families

Every family backend must expose the following interface.

```text
backend = build_backend(family_spec, truncation, chart_options)

backend.operator_factory(background_state) -> ModeOps
backend.seed_factory(seed_request) -> SeedPack
backend.label_translator(native_labels) -> storage_labels
backend.inverse_label_translator(storage_labels) -> native_labels
backend.backend_residuals(...) -> dict
backend.required_metadata() -> dict
```

### required backend metadata
- chart/model name
- native mode labels
- parity/helicity/branch flags if relevant
- truncation metadata
- boundary policy
- seed provenance mode
- release status

---

## 5. family notes

### 5.1 isotropic-limit families
I, V, VII\(_0\), VII\(_h\), IX admit an isotropic anchor family branch.
This permits FLRW-like regular seed logic, provided the chosen backend documents the limit and the branch.

### 5.2 intrinsically anisotropic families
II, III, IV, VI\(_0\), VI\(_h\), VIII do not admit a generic FLRW regular branch.
They require family-adapted regularity data.  The design templates are mandatory and live in `03A`.

### 5.3 class-B \(h\)-families
For VI\(_h\) and VII\(_h\), the backend metadata must store:
- `h`
- canonical gauge used to realize `h`
- chart restriction if any
- mode-label translator aware of `h`

---

## 6. IC provenance rules

### 6.1 isotropic-limit rule
Allowed paths:
1. FLRW-like regular seed in the isotropic anchor branch
2. family-aware continuation away from the anchor
3. tilted variant via electron-frame seed + inverse boost + residual projection

### 6.2 intrinsic-family rule
Allowed paths:
1. family-adapted Frobenius series
2. local regular series in the preferred chart
3. residual-projected collocation seed

Forbidden:
- flat-FLRW seed reuse
- isotropic-limit seed import without an explicit family justification

### 6.3 seed object schema

Every seed factory must return

```text
SeedPack(
    family,
    branch,
    chart,
    seed_mode,
    variables,
    normalization,
    residual_summary,
    metadata
)
```

---

## 7. minimal family-specific validation set (design level)

Each family card must define at least:
- one algebra consistency check
- one chart/boundary check
- one seed regularity check
- one label-translator roundtrip check
- one orthogonal vs global-tilt split check

These are design-level requirements even before executable tests exist.

---

## 8. what this document does not claim

This document does **not** claim that all-family backends are already implemented.  
It claims that all-family backend and IC **contracts** are now present and separated from future work.

---

## 9. one-line summary

all 11 family coverage means  
**taxonomy + canonical data + orthogonal/tilted/boost split + backend interface + IC provenance rule** 가 패키지 안에서 family별로 고정되어 있다는 뜻이지, 구현 완료를 뜻하지 않는다.
