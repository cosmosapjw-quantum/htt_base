# 03A. Intrinsic-Family Template Cards
## backend chart / discretization / label translator / seed object templates for the hardest families

---

## 0. purpose

이 문서는 intrinsic-family 및 class-B difficult branch에서 Codex handoff를 막는 공백을 줄이기 위한 template card 모음이다.
이 카드는 analytic closed form을 대신하지 않는다.
하지만 implementation agent가 임의 chart, 임의 seed, 임의 label order를 고르지 못하게 막는다.

Each card freezes:

1. preferred chart / model
2. minimum collocation discretization policy
3. native label and translator rule
4. allowed seed provenance
5. seed object schema
6. family-specific residuals
7. must-not-do list

---

## 1. Type II card

### preferred chart / model
Nilpotent Heisenberg-style invariant chart with one preferred nontrivial commutator direction.

### minimum collocation discretization policy
- finite-domain truncation with refinement study
- no periodic closure by default
- domain edge metadata mandatory

### native label / translator rule
- native mode label `mu_nil`
- explicit translator `mu_nil -> storage(mu, ell, m, sector)`
- no assumption that `mu_nil` is ordered by storage index

### allowed seed provenance
- family-adapted Frobenius series
- local regular series in nil chart
- residual-projected collocation seed

### seed object schema
```text
SeedPack(
    family="II",
    branch="intrinsic",
    chart="nil_heisenberg",
    seed_mode in {"frobenius","local_regular","collocation_projected"},
    normalization={"amp_ref": ..., "mu_ref": ...},
    variables={...},
    residual_summary={...}
)
```

### family-specific residuals
- nil-chart regularity residual
- label-translator roundtrip residual
- seed regularity residual

### must-not-do
- no FLRW seed reuse
- no implicit periodic boundary
- no unlabeled branch choice

---

## 2. Type III card

### preferred chart / model
Class-B hyperbolic branch chart, explicitly tagged as the Type III / \(VI_{-1}\) special branch.

### minimum collocation discretization policy
- truncated hyperbolic domain
- boundary metadata must record radial cutoff and refinement
- supercurvature-like sectors, if introduced, require explicit metadata flags

### native label / translator rule
- native labels `mu_hyp`, branch flag, parity flag if needed
- storage translator must preserve the branch flag

### allowed seed provenance
- class-B branch-specific Frobenius or local regular series
- residual-projected collocation seed

### seed object schema
same as above, with `family="III"` and explicit `branch="VI_-1_special"` when relevant.

### family-specific residuals
- class-B branch consistency residual
- hyperbolic cutoff residual
- seed branch-label consistency residual

### must-not-do
- no open-FLRW seed import without explicit branch justification
- no dropping the class-B special-branch flag

---

## 3. Type IV card

### preferred chart / model
Solvable-group chart with explicit choice of noncompact coordinate ordering.

### minimum collocation discretization policy
- finite truncation with anisotropic edge metadata
- no isotropic radial coordinate assumption
- coordinate remap must be logged in metadata

### native label / translator rule
- `mu_solv` plus coordinate-order metadata
- storage translator must record coordinate order

### allowed seed provenance
- local regular series in solvable chart
- residual-projected collocation seed
- no FLRW-like seed

### seed object schema
same pattern, with a mandatory `coordinate_order` field in metadata.

### family-specific residuals
- chart-order residual
- edge anisotropy residual
- seed regularity residual

### must-not-do
- no isotropic radial reduction
- no chart swap without translator update

---

## 4. Type VI0 card

### preferred chart / model
Class-A solvable / intrinsic chart with explicit mixed-sign spatial structure.

### minimum collocation discretization policy
- finite domain with mixed-sign directional bookkeeping
- refinement separately by principal direction

### native label / translator rule
- `mu_VI0` + directional sector tag
- storage translator must keep directional tag

### allowed seed provenance
- intrinsic-family Frobenius series
- local regular series
- residual-projected collocation seed

### seed object schema
same pattern, with `directional_tag` metadata.

### family-specific residuals
- directional truncation residual
- translator directional-tag residual

### must-not-do
- no borrowing Type I/VII seeds
- no isotropic-direction compression

---

## 5. Type VI_h card

### preferred chart / model
Class-B \(h<0\) branch chart with explicit \(h\)-value metadata and canonical-gauge record.

### minimum collocation discretization policy
- truncated class-B chart with `h`-dependent domain metadata
- branch refinement mandatory when `h` changes
- no reuse of a single translator across different `h` without explicit proof of equivalence

### native label / translator rule
- labels `mu_VIh`, `h`, branch tag
- translator must explicitly carry `h`

### allowed seed provenance
- class-B \(h\)-aware local regular series
- \(h\)-aware Frobenius seed where available
- residual-projected collocation seed

### seed object schema
same pattern, plus mandatory fields
```text
metadata = {"h": ..., "canonical_gauge": ..., "branch_tag": ...}
```

### family-specific residuals
- `h`-consistency residual
- branch-label residual
- cutoff refinement residual

### must-not-do
- no using VI\(_0\) seed at nonzero \(h\)
- no hiding `h` inside a generic branch label

---

## 6. Type VIII card

### preferred chart / model
Noncompact \(SL(2,\mathbb R)\)-type chart with explicit noncompact domain metadata.

### minimum collocation discretization policy
- noncompact truncation with convergence study
- no compact-group assumptions
- boundary policy must record truncation strategy and residual trend

### native label / translator rule
- native labels `mu_sl2r`, parity/helicity if used
- translator must preserve noncompact branch tags

### allowed seed provenance
- intrinsic-family local regular series
- group-adapted seed if available
- residual-projected collocation seed

### seed object schema
same pattern, with `noncompact_cutoff` and `branch_tag` metadata.

### family-specific residuals
- noncompact truncation residual
- branch-tag residual
- seed regularity residual

### must-not-do
- no compact \(SU(2)\) reuse
- no Wigner-\(D\) assumption unless explicitly documented as an approximation study

---

## 7. cross-card mode-label / parity / helicity translator rule

Every backend card must eventually supply a translator card of the form

```text
NativeLabelCard(
    family,
    native_labels = {...},
    parity_flag = ... or None,
    helicity_flag = ... or None,
    branch_flag = ... or None,
    to_storage(...),
    from_storage(...)
)
```

If parity/helicity do not apply, the card must store `None` explicitly rather than omitting the field.

---

## 8. cross-card collocation policy defaults

Unless a family card overrides them, the following defaults apply:

- store domain limits explicitly,
- refinement study is mandatory before opening the next gate,
- edge treatment is a metadata field, not an implicit choice,
- collocation-based seed generation must output residual summaries,
- any unavailable analytic normalization must be flagged as `LOOKUP_REQUIRED`.

---

## 9. one-line summary

이 카드들의 목적은  
**intrinsic-family에서 implementation agent가 임의 chart / 임의 seed / 임의 label order를 택해도 된다고 오해하지 못하게 하는 것** 이다.
