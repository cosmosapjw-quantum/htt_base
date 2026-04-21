# Patch Map for Existing MD and Manuscripts

문서 목적: 기존 md 문서와 원고에서 실제로 바꿔야 할 표현을 find/replace 수준으로 정리한다. 기계적 치환만으로 끝내면 안 되는 곳은 `manual rewrite`로 표시한다.

---

## 1. Global terminology replacements

### Replacement 1

Find:

```text
characteristics가 full transport closure
```

Replace:

```text
characteristics가 closure-free full-state transport backbone/reference
```

Manual note: 문장 전체가 `Teff는 ...로만 남는다`와 연결되어 있으면 다음처럼 고쳐라.

```text
characteristics는 closure-free full-state transport backbone/reference이고, Teff는 trace/intensity block의 statistical semantics, exact source bridge, diagnostic layer로만 남는다.
```

### Replacement 2

Find:

```text
characteristics is the full transport closure
```

Replace:

```text
characteristics provides the closure-free full-state transport backbone/reference
```

### Replacement 3

Find:

```text
full closure
```

Replace contextually with one of:

```text
full-state transport reference
closure-free transport backbone
resolved transport layer
```

Do not perform blind replacement if the sentence discusses actual moment closure.

### Replacement 4

Find:

```text
covariant full closure
```

Replace:

```text
covariant full-state transport reference
```

### Replacement 5

Find:

```text
full Boltzmann hierarchy solver
```

Replace:

```text
full-Boltzmann-class characteristic transport implementation, only in the resolved phase-space/tensor/species/collision limit and after convergence validation
```

If too long for abstract, write:

```text
closure-free characteristic transport reference
```

---

## 2. Architecture note patch

### Old constitution sentence

```text
characteristics가 full transport closure이고, Teff는 trace/intensity block의 statistical semantics, exact source bridge, diagnostic layer로만 남는다.
```

### New constitution sentence

```text
characteristics는 closure-free full-state transport backbone/reference이고, Teff는 trace/intensity block의 statistical semantics, exact source bridge, diagnostic layer로만 남는다.
```

### Old explanatory sentence

```text
이것이 “characteristics가 full closure”라는 말의 정확한 수학적 의미다.
```

### New explanatory sentence

```text
이것이 “resolved characteristic block에는 closure가 필요 없다”는 말의 정확한 수학적 의미다.
```

---

## 3. Proof-obligation note patch

### Old top-level claim

```text
characteristics가 full transport closure이고, Teff는 trace/intensity block의 statistical semantics, exact source bridge, diagnostic layer로만 남는다.
```

### New top-level claim

```text
full tensor/species state는 closure-free characteristics로 직접 운반되고, Teff는 trace/intensity block의 statistical semantics, exact source bridge, diagnostic layer로만 작동한다.
```

### Old cluster title

```text
PO-C: covariant full closure and channelwise observables
```

### New cluster title

```text
PO-C: covariant full-state characteristic transport and channelwise observables
```

---

## 4. Theorem compendium patch

### Old framing

```text
characteristics = full transport closure
```

### New framing

```text
characteristics = closure-free full-state transport reference
```

### Old formula-like narrative

```text
full characteristics transport + Teff semantics
```

### New narrative

```text
closure-free full-state characteristic transport + blockwise Teff semantics
```

### Old theorem title

```text
1+3 covariant full nonperturbative Einstein-Boltzmann characteristics solver architecture theorem
```

### New theorem title

```text
1+3 covariant closure-free characteristic transport architecture theorem
```

Manual note: theorem can still discuss nonperturbative transported state, but should not imply completed production solver or global well-posedness unless proved.

---

## 5. Paper V patch

### Q convention declaration to insert before Table II

```text
In this axisymmetric example we use
Theta(mu)=1+A mu+Q(mu^2-1/3)=1+A P1(mu)+(2Q/3)P2(mu),
with P2(mu)=(3mu^2-1)/2. Therefore the linear quadrupole contribution is (8/3)Q.
```

### Replace linear-bridge statement

Find:

```text
I_ab ≈ 4 c_xi T_ab
```

Manual rewrite depending on convention:

If `T_ab` is the coefficient of `P2`, `4Q` may be right. If `Q` is the coefficient of `mu^2-1/3`, the scalar table's linear coefficient is `8Q/3`. The manuscript must define `T_ab` and scalar `Q` consistently.

### Replace dominance sentence

Find:

```text
the dipole-squared term dominates at (A,Q)=(0.30,0.15)
```

Replace:

```text
the dipole-squared term is already comparable to the linear quadrupole contribution at (A,Q)=(0.30,0.15) and can dominate at stronger dipole amplitudes
```

---

## 6. Validation docs patch

Keep Layer A/B/C/R structure, but sharpen the separation.

### Add to Layer A

```text
Layer A validates the characteristic reference only. It does not validate Teff reduction adequacy.
```

### Add to Layer B

```text
Layer B validates reduced trace-block adequacy only. It does not validate spin-2 propagation or BB observables.
```

### Add to Layer C

```text
Layer C must separately report trace-source error, spin-2 propagation error, and final spectrum error.
```

### Add test B4

```text
B4. Q-normalization regression test: reproduce Table II only under Theta=1+A mu+Q(mu^2-1/3), linear term 8Q/3.
```

---

## 7. Suggested file reordering

Existing giant compendium sections should be split into the current series as follows.

| Old material | New file |
|---|---|
| global positioning and source map | `00_README_index_and_source_boundaries.md` |
| constitution phrases | `01_constitution_scope_and_claim_language.md` |
| Paper I-V scope map | `02_papers_I_to_V_upgrade_ledger.md` |
| theorem chain and defect identities | `03_reduction_geometry_and_theorem_compendium.md` |
| solver architecture | `04_characteristics_architecture_closure_free_backbone.md` |
| Paper V polarisation bridge | `05_trace_intensity_semantics_and_polarisation_bridge.md` |
| proof obligations | `06_proof_obligations_and_claim_status.md` |
| validation protocol/test matrix/runbook | `07_validation_protocol_and_test_matrix.md` |
| hostile reviewer questions | `08_red_team_reviewer_defense.md` |
| actual replacements | `09_patch_map_for_existing_md_and_manuscripts.md` |

---

## 8. Final manuscript-level synthesis paragraph

Use this in a series overview:

```text
The Teff programme should be read as a reduced trace-sector framework embedded in unreduced transport, not as a replacement for Boltzmann transport. Papers I-III establish the reduced-manifold diagnostic and entropy geometry; Paper IV gives observable semantics and a conditional local reconstruction bound; Paper V gives an exact nonlinear intensity-source bridge inside polarised transfer. The full-state transport reference is provided by closure-free characteristics, while Teff supplies semantics, source reconstruction, and diagnostics only on selected reduced blocks.
```
