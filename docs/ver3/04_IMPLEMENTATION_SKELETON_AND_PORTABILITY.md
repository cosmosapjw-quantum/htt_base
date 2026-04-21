# 04. Implementation Skeleton and Portability
## module tree / dataclasses / function signatures / portability rules

---

## 0. purpose

이 문서는 설계문서와 실제 skeleton code 사이의 번역층이다.
목적은 Codex나 implementation agent가
- 어떤 파일을 만들고,
- 어떤 dataclass를 정의하고,
- 어떤 helper를 공통화해야 하는지
를 추가 질문 없이 시작하게 만드는 것이다.

---

## 1. recommended module tree

```text
src/lowell_bianchi/
    __init__.py
    conventions.py
    registry.py
    geometry.py
    background.py
    collision.py
    transport.py
    hierarchy.py
    visibility.py
    backends.py
    output.py
    validation.py
```

Optional family-specific submodules:

```text
src/lowell_bianchi/families/
    type_ii.py
    type_iii.py
    type_iv.py
    type_vi0.py
    type_vih.py
    type_viii.py
```

---

## 2. mandatory dataclasses

```python
@dataclass
class FamilySpec: ...
@dataclass
class BackgroundState: ...
@dataclass
class GeometryDiagnostics: ...
@dataclass
class SpeciesRestFrameState: ...
@dataclass
class SpeciesProjectedState: ...
@dataclass
class SeedPack: ...
@dataclass
class ModeOps: ...
@dataclass
class ResidualPack: ...
@dataclass
class OutputMetadata: ...
```

### portability rule
Dataclasses may be translated to structs/classes in another language, but the field semantics must remain identical.

---

## 3. required helper layer

The helper layer is mandatory and cannot be bypassed:

```text
gamma_trace
gamma_norm2_tensor
pstf_gamma
raise_vector
lower_vector
gamma_from_vsq
eta_from_t_grid
opacity_from_physical_inputs
```

Forbidden:
- direct Euclidean contractions on invariant-basis tensors,
- hardcoding family-dependent contractions inside high-level solvers.

---

## 4. file-level responsibilities

| file | responsibility | must not do |
|---|---|---|
| `conventions.py` | tensor helpers / bridges | no family logic |
| `registry.py` | family metadata and canonical data | no geometry assembly |
| `geometry.py` | triad, commutators, connection, Ricci, diagnostics | no matter projection |
| `background.py` | background RHS and matter projection | no hierarchy ordering |
| `collision.py` | exact electron-frame Thomson block | no output boost |
| `transport.py` | tier-A ray/basis transport | no tier-B storage assumptions |
| `hierarchy.py` | tier-B operator assembly and IMEX packing | no family metadata storage |
| `visibility.py` | opacity/history adapters | no statistics |
| `backends.py` | backend protocol and builders | no solver loop |
| `output.py` | output-only boost, archive writing | no background physics |
| `validation.py` | residual and gate logic | no physical evolution |

---

## 5. required signatures

```text
build_geometry(family_spec, gamma_AB, theta, sigma_AB) -> GeometryDiagnostics
project_species_to_normal_frame(species_rest, tilt, gamma_AB) -> SpeciesProjectedState
background_rhs(t, background_state, family_spec, eos_model) -> (rhs, residuals)
exact_thomson_source(e_dir, I_dir, I0, P_dir, I2, E2_pol, opacity_data) -> SourceTerms
build_backend(family_spec, truncation, chart_options) -> Backend
assemble_hierarchy_ops(bg, backend, truncation, source_data) -> ModeOps
observer_boost_output(alm_det, alm_stoch, boost_params, metadata) -> BoostArchive
hard_gate_before_fitting(gates, residuals, metadata) -> GateDecision
```

---

## 6. skeleton philosophy

### safe-now
The following are safe to skeletonize immediately:
- dataclasses
- helper layer
- registry
- geometry interface
- background interface
- collision interface
- gate interface
- archive schema

### do-not-fake-yet
The following must not be given fake numerical content:
- intrinsic-family analytic backend internals
- unavailable seed series
- tier-A “exact” transport
- tier-B production coefficients
- any fitting result

---

## 7. portability rules

1. no implicit numpy layout assumptions in the document-level API
2. all array shapes must be documented in module docstrings
3. storage order must be metadata, not hidden convention
4. NaN fail rules must survive language translation
5. output-only boost must remain a separate module boundary

---

## 8. implementation starter checklist

Before code generation starts, the agent must verify:

- authority order read
- family registry table frozen
- tensor helper layer understood
- time-gauge bridge understood
- intrinsic-family cards read for relevant family
- PR deliverable map selected
- gate rules copied into implementation context

---

## 9. one-line summary

이 문서는  
**formalism 문서를 실제 module / dataclass / signature / portability contract로 번역하는 middle layer** 다.
