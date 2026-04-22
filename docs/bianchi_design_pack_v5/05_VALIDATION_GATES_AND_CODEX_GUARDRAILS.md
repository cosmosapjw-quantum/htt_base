# 05. Validation Gates and Codex Guardrails
## fail-closed rules / forbidden shortcuts / literature lookup discipline / handoff gating

---

## 0. purpose

이 문서는 implementation agent가 가장 흔히 빠지는 실패 모드를 막기 위한 규칙을 고정한다.

1. unsupported family를 fake support로 위장
2. mock spectrum fitting으로 물리 빈칸을 덮기
3. local boost로 global tilt 효과를 흉내 내기
4. development cutoff 결과를 production evidence로 승격
5. unavailable residual을 0으로 처리
6. literature lookup이 필요한 항목을 문서 완결성으로 오독

---

## 1. gate ladder

The gate order is

1. authority freeze
2. tensor helper correctness
3. family registry freeze
4. geometry diagnostics gate
5. matter projection gate
6. exact Thomson gate
7. visibility/history gate
8. family-backend gate
9. hierarchy layout gate
10. output split gate
11. fitting gate

A lower gate failing makes all higher gates unavailable.

---

## 2. hard-stop rules

### HS-1
No fitting before output split gate opens.

### HS-2
No output split gate before
- exact electron-frame Thomson contract,
- local boost/global tilt separation,
- family-specific backend contract,
- IC provenance contract,
- production cutoff policy
are frozen.

### HS-3
No residual unavailable \(\rightarrow 0\) conversion.

### HS-4
No unsupported family may borrow an isotropic-limit seed without an explicit family card justification.

### HS-5
No transport exactness claim may be opened by tier-B code.

---

## 3. NaN-fail policy

Any of the following implies immediate FAIL:

- NaN or Inf in residuals
- negative optical depth where monotonic opacity is expected
- missing backend translator
- unlabeled branch in class-B \(h\)-family
- boost metadata missing when output boost is applied

---

## 4. required validation bundles

Every opened gate must produce a machine-readable bundle containing:

```text
gate_name
family
branch
backend
truncation
residual_summary
known_limit_checks
forbidden_shortcut_checks
metadata
```

---

## 5. NOT_ALLOWED list for implementation agents

1. no mock spectrum fitting before hierarchy/output gates
2. no “temporary” isotropic fallback for unsupported family
3. no folding local boost into global tilt
4. no hiding unavailable analytic data behind silently generated constants
5. no treating development cutoff as production cutoff
6. no skipping translator metadata
7. no Euclidean contractions on invariant-basis tensors
8. no unlogged chart or boundary choice

---

## 6. FAILURE_MODES list

- family naming coverage mistaken for backend completeness
- tier-A placeholder mistaken for exact transport
- directional intensity mistaken for monopole in Thomson source
- collocation seed mistaken for regular series without residual summary
- output archive without split metadata
- residual pack present but dimensionless normalization absent
- CRAG lookup deferred indefinitely by “bundle seems enough”

---

## 7. literature / web-search CRAG discipline

Resolved lookup-bearing formulas are frozen in `03B_FROZEN_BACKEND_CONSTANTS_AND_LOOKUP_RESOLUTION.md`.

This v5 bundle carries no active unresolved backend placeholders.
If a future patch introduces a new unresolved item, the implementation agent must:
1. search the project bundle first,
2. then consult the primary source listed in `99_REFERENCES.md`,
3. then record the resolved formula or convention in a frozen addendum before coding.

The agent must not fill unresolved items with guessed formulas.

---

## 8. codex-facing prompt block

```text
You are implementing from a validation-gated scientific design pack.
Never open a higher gate by faking a lower gate.
If a future family card introduces an unresolved item, stop and retrieve the cited primary source before coding.
Do not substitute isotropic-limit formulas for intrinsic families.
Do not move local observer boost into background or hierarchy code.
Do not report observables-ready or statistics-ready unless the corresponding gate bundle exists.
```

---

## 9. score rule

| score band | meaning |
|---|---|
| 0–2 | idea only |
| 3–4 | authority frozen |
| 5–6 | module contract exists |
| 7–8 | gate bundle exists for named branch |
| 9–10 | branch complete with required diagnostics |

This score is a **gate score**, not a style score.

---

## 10. one-line summary

이 문서의 목적은  
**Codex가 설계문서를 읽고 제일 먼저 할 일과 절대로 하면 안 되는 일을 강제하는 것** 이다.
