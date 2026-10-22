# Independent review — CAS12-C04 oscillatory derivative bridge

Decision: `PASS_SCOPED` for `OscillatoryDerivative.lean`, SHA-256
`0f0082138f0be18711221a068921f4b2dda21ebf6f3a137a35d9ea68bd6e5d2d`.

The fresh reviewer independently ran the declared `lake env lean` command from
`/home/cosmosapjw/lean_oracles/viii_oracle`, obtaining exit zero with Lean 4.31.0
and mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`. All six audited
declarations depend only on `propext`, `Classical.choice`, and `Quot.sound`.

The source proves the pointwise `HasDerivAt` product/chain rule for
`g + a*sin(n*x)*q`, retaining the `q'` term, and the abstract real-linear
moment annihilation/preservation statements. It does not construct a compact
moment-orthogonal `q`, differentiate an actual integral, establish weighted
Cauchy or a norm result, or assert C02, collision, physical, historical
four-axis, or scientific conclusions.

Requested reviewer runtime: `gpt-6-astra/ultra`; observed model and effort:
`UNKNOWN`. The review was read-only.
