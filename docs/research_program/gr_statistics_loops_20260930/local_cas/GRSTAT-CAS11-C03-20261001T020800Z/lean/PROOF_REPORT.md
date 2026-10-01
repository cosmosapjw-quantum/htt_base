# CAS11-C03 Lean axis proof coverage

Contract: `CAS11-C03-WEIGHTED-PROJECTION.json` SHA-256 `a97dc88082095ba636d326ea390cf629b86ca333577a27638c83c2b7f9a55794`. Source, exact argv/cwd/exit, complete stdout/stderr, and tool version are recorded in `execution.json`, `AXIS_RESULT.json`, `compile.*.log`, and `version.*.log`. The runner prints one JSON payload and succeeds only when the pinned Lean compiler exits zero and six theorem axiom markers contain exactly `propext`, `Classical.choice`, and `Quot.sound`, with no `sorryAx`.

`WeightedProjection.lean` uses an arbitrary real inner product space `E` of arbitrary finite dimension. Its inner product is the positive-definite W-weighted product; no coordinate matrix or ordinary Euclidean product is substituted. An arbitrary real submodule `V` has an orthogonal projection by finite-dimensional completeness. There is no nonzero-dimension or proper-subspace condition. An arbitrary finite index type `ι` and arbitrary family `K : ι → E` include an empty family and dependent/zero residual vectors. `quadratic` is the literal double sum `ΣᵢΣⱼ aᵢ Rᵢⱼ aⱼ` for `Rᵢⱼ = ⟪rᵢ,rⱼ⟫_W`.

| Contract obligation | Lean theorem | Certificate |
|---|---|---|
| `P²=P` | `projection_idempotent` | `V.starProjection` is idempotent |
| `⟪v,(I-P)x⟫_W=0` for every `v∈V` | `projection_orthogonal` | Orthogonality characterization of `V.starProjection` |
| `aᵀRa=‖Σ aᵢrᵢ‖²≥0` for every coefficient family | `gram_quadratic_identity`, `gram_quadratic_norm_sq`, `gram_positive_semidefinite` | Bilinearity, symmetry, and nonnegative norm square |
| `|⟪x,y⟫_W|²≤⟪x,x⟫_W⟪y,y⟫_W` for every `x,y` | `weighted_cauchy_schwarz` | Explicit nonnegative square `⟪b x-c y,b x-c y⟫_W=b(b⟪x,x⟫_W-c²)`, with `b=⟪y,y⟫_W`, `c=⟪x,y⟫_W`; separate `y=0` branch |

The final Lean source compiles with Lean 4.31.0 and the repository-pinned mathlib. `#print axioms` emits only Lean's standard `propext`, `Classical.choice`, and `Quot.sound` for all six theorems. The finite mathematical component is proven locally; this does not close CAS-11's measure-space obligations or establish scientific admission. The independent four-axis adjudication remains Host-owned.

Requested runtime profile: `gpt-6-sol/high`. Observed author model/effort and cost: `NOT_MEASURED` in the available task metadata; this file does not self-attest the model. Prior interactive compile failures were parser errors from inner-product notation, a missing symmetry rewrite in the Gram identity, and an overbroad rewrite in the square certificate; all were repaired before the final run. Their raw tool responses remain in the task transcript; only final-run subprocess output was persisted in files.
