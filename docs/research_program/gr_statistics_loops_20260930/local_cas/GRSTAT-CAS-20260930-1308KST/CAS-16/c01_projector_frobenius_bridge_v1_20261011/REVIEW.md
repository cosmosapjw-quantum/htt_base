# Independent review — CAS16-C01 finite projector/Frobenius bridge

Decision: `PASS_SCOPED` for `ProjectorBridge.lean`, SHA-256
`e38b8f8a7079d3c6510f9d3836f7763232e916dc72c17d77ad532742dfa18abc`.

The fresh read-only reviewer independently ran `lake env lean ProjectorBridge.lean`
from `/home/cosmosapjw/lean_oracles/viii_oracle`: exit 0 with Lean 4.31.0 and
mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`.  The source, imports,
toolchain, and manifest binding matched the receipt.

The checked theorem quantifies over all `e : Fin 3 -> Real` and all real 3x3
matrices `J`, under the explicit unit hypothesis `sum_i e_i*e_i=1`.  It uses
`P = I - ee^T`, establishes symmetry and idempotence, and proves the entrywise
Frobenius-square contraction of `P*J*P` through the separately checked row and
column square identities.  All eight audited declarations use only `propext`,
`Classical.choice`, and `Quot.sound`; there is no `sorry` or custom target axiom.

This is not a Hilbert-space collision norm, a physical coherency claim, CAS16-C02
degree accounting, a quadrature theorem, a historical four-axis verdict, or a
scientific admission.  All remain outside scope/HOLD.

Requested reviewer runtime: `gpt-6-astra/ultra`; observed model and effort:
`UNKNOWN`. The reviewer made no edits.
