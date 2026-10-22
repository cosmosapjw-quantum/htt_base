# G12-D independent mathematical review

Decision: `PASS_SCOPED_MATHEMATICAL_REVIEW` for final Lean source SHA-256
`77fed344f590155fdbdb35a4bceb55b5470a2a40aa5c4bd41c2bec1f0cbc560b`.
Requested reviewer runtime: `gpt-6-astra/ultra`; independently observed runtime:
`UNKNOWN`. The reviewer was fresh, read-only, and did not author the source.

The initial blocking finding was a missing typed specialization from a.e.
`0 < T(s) ≤ Tmax` to the beta-based mixture envelope. The additive theorem
`G12D.temperature_mixture_and_reference_envelope` at source line 285 closes it
without changing the twelve frozen target types. Removing the additive theorem,
its universe declaration, and audit lines recovers the pre-repair source hash
`9c451adb6acca510e2da9be433160403071fe6090e5f1af074268a2363287ba3`.

The reviewer checked the actual right-sided IR input, both pointwise bounds and
positive UV denominators, radial near-zero/tail coverage, finite-angular product
measure, a.e. kernel measurability, nonnegative measurable finite `withDensity`
density, probability mixture and independent reference bounds, temperature
specialization, and all thirteen printed theorem types/axioms. The independent
source-bound build receipt is `PARENT_SOURCEBOUND_COMPILE.json`, SHA-256
`4084c4a983fbfceaa13fbbfcd10d440637f3587f7fa907fc21b82d883fe9afcd`.
The build recompiled PlanckIR, the interface, and the candidate from source;
each binary matched the author's binary. Every audited theorem depends only on
`propext`, `Classical.choice`, and `Quot.sound`.

The kernel theorem covers exactly an a.e. single-monomial bound
`|K(E,ω)| ≤ M E^n`, `n : ℕ`, not arbitrary polynomial sums. It does not infer
`Tmax` or `b` from bolometric energy, prove physical condensate exclusion,
validate unsupplied channel kernels, promote historical four-axis status, or
admit the scientific model.

Evidence limitation: original separated stdout/stderr for nine failed interim
compiles was not captured. Their source snapshots and transcript chunk IDs are
retained in `lean/raw/FAILURE_INDEX.json`; original streams are explicitly
`UNAVAILABLE`. Therefore `strict_failure_retention_requirement=UNMET` even
though the final source-bound mathematical proof passes. No failed output was
fabricated from reruns.
