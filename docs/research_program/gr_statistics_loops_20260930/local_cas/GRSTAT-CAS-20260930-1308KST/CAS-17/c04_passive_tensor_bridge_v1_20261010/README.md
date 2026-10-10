# CAS-17-C04 passive tensor bridge

Owner: `common`. Scope: the frozen C04 pointwise finite contraction component.
Transfer source: none. Independent review is separate; historical four-axis
status and scientific `HOLD` remain unchanged.

`PassiveTensorBridge.lean` proves contraction invariance for arbitrary dimension
`n`, arbitrary finite tensor ranks `p,q`, an arbitrary tensor and its arguments,
and a single invertible real linear equivalence `L`. Contravariant tensor slots
accept covectors transformed by inverse pullback; covariant slots accept vectors
transformed by `L`; the tensor is pulled back by the inverse slot transformations.
The equality is proved from those transformation definitions and inverse laws,
without assuming the target scalar equality.

The proof also covers finite summed contractions, complete internal contractions
of a type-`(r,r)` tensor with arbitrary index pairing and basis/dual basis, and
trace conjugation of a type-`(1,1)` tensor. Universal parameters include rank zero
and dimension zero where the supplied tensor/basis types admit them.

Physical observer replacement is outside passive invariance. An exact scope
witness in signature `(-,+,+,+)` proves that observers `(1,0,0,0)` and
`(5/3,4/3,0,0)` are future unit timelike, while the same null vector `(-1,1,0,0)`
has contractions `1` and `3`. Operational calibration availability is an external
scope condition and is not proved. There is no differential coordinate-map,
connection, solver, Bianchi-family, physical-input-existence, or scientific
admission theorem here.

Reproduce the narrow kernel check using the authorized existing fallback:

```bash
cd /home/cosmosapjw/lean_oracles/viii_oracle
lake env lean /home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-17/c04_passive_tensor_bridge_v1_20261010/PassiveTensorBridge.lean
```

Final exit code: `0`. All seven theorem axiom audits report only `propext`,
`Classical.choice`, and `Quot.sound`; no `sorryAx`, admitted proof, or new axiom.
Lean `4.31.0` and mathlib revision `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`
were observed. Broken primary cache symlinks were preserved. The fallback and
primary Lake manifests differ as packaging metadata; package-by-package cache
identity is not asserted.

Final source SHA-256:
`49f371401016466361d7f02012ba840de0f5d600327722ac4e843602c95da8fb`.
`AUTHOR_RECEIPT.json` binds the frozen contract/common inputs, toolchain,
requested/observed runtime, dependency identity locators, exact command, and
attempt history. `COMPILE_01.combined` through `COMPILE_08.combined` retain raw
tool outputs, including failed elaborations. The tool returned a combined stream;
separate stdout/stderr identity is unavailable. First-attempt output was copied
verbatim from this task's tool transcript; later outputs were captured directly
from returned tool text. Failed-attempt `sorryAx` output is not an accepted proof.

Author requested: `gpt-6.1-sol/high`. Observed author model/effort: `UNKNOWN`.
No CAS01/CAS07 proof content or old CAS17/sibling axis proof/results were consumed.
Dependency bindings are identity receipts only. Review must resolve and verify
the exact final source identity independently.
