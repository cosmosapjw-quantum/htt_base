# 07. SDD WBS and PR List
## specification-driven implementation order / checklists / scoreboard / verification loop

---

## 0. scope

이 문서는 구현 순서를 specification-driven 방식으로 고정한다.
목표는 세 가지다.

1. 수식과 물리보다 mock fitting이 먼저 가는 것을 방지
2. implementation agent가 local minima에 빠지는 것을 방지
3. branch별 claim opening을 gate와 함께 통제

---

## 1. SDD principles

### SDD-1
formalism → operator contract → residual contract → skeleton → gate → output → fitting

### SDD-2
unsupported family isotropic fallback 금지

### SDD-3
development cutoff를 production evidence로 승격 금지

### SDD-4
gate failing 상태에서 새로운 관측/통계 해석 금지

### SDD-5
all-family naming coverage를 backend completeness로 오독 금지

---

## 2. PR dependency chain

### PR-00 — authority freeze
freeze authority order, signs, scopes, gate semantics

### PR-01 — invariant-basis tensor helpers
gamma-trace, PSTF, raise/lower, bridge helpers

### PR-02 — family registry and canonical data
all-family metadata, class, isotropic anchor, \(h\)-consistent branches

### PR-03 — geometry core
triad, commutators, connection, dual-route Ricci, S_AB, diagnostics

### PR-04 — matter projection and background source pack
tilted fluid projections, total source pack

### PR-05 — background Einstein–matter core
Raychaudhuri, shear, metric RHS, background residuals

### PR-06 — exact electron-frame Thomson block
scalar/tensor source separation, isotropic null limit, tilt-modulated opacity

### PR-07 — visibility and homogeneous reionization adapter
opacity, optical depth, visibility, rei history baseline

### PR-08 — family backend protocol and intrinsic template instantiation
backend builders, label translators, seed factories

### PR-09 — hierarchy layout and IMEX packing
sector order, sparse blocks, TCA microblock, neutrino block

### PR-10 — output split layer
det/stoch/boost archive split, metadata schema, no fitting yet

### PR-11 — validation gate and fitting hard stop
gate bundles, score rule, fitting prohibition until all prior gates open

---

## 3. scoreboard meaning

| band | meaning |
|---|---|
| 0–2 | idea / memo only |
| 3–4 | authority frozen |
| 5–6 | skeleton and gate contract exist |
| 7–8 | branch gate bundle exists |
| 9–10 | branch complete with required diagnostics |

This is a gate-readiness scoreboard, not a polish scoreboard.

---

## 4. per-PR checklist template

Each PR must define:
- purpose
- dependencies
- files touched
- API signatures
- regression artifacts
- opened claim
- forbidden shortcuts

---

## 5. metacognitive verification loop

At the end of each PR:

1. check the highest unopened lower gate
2. verify no unsupported family fallback was introduced
3. verify no output/statistics logic leaked upstream
4. verify no local boost leaked into background/hierarchy
5. verify no mock spectrum or fake fit was used as validation
6. record unresolved items explicitly

---

## 6. one-line summary

이 WBS의 핵심은  
**formalism과 물리 빈칸이 닫히기 전에 statistics나 mock spectrum으로 도망치지 못하게 구현 순서를 통제하는 것** 이다.
