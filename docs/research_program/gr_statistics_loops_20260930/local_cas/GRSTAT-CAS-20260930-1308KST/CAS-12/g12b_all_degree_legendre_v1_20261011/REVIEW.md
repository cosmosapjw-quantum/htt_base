# Independent endpoint-jets review

Verdict: `PASS_SCOPED_ENDPOINT_JETS` for final `lean/EndpointJets.lean` SHA-256 `404a831a8b4bce6a920dc53139cdcedb56e2d9fd3ef989c3d558588f1f2e53b7`. Requested reviewer `gpt-6-astra/ultra`, independently observed runtime `UNKNOWN`. Reviewer was fresh and read-only.

The theorem has unrestricted `n k : ℕ`, sole hypothesis `k < n`, and both endpoint evaluations of `X^n(1-X)^n` over `ℝ[X]`. The proof uses pinned Mathlib divisibility to retain multiplicity `n-k>0` after differentiation. It handles `k=0` and has vacuous `n=0`; no finite cutoff or hidden integral assumption appears. Contract, source card, Fin7 context and Mathlib source hashes match the pinned checkout. The author's final compile and independent `PARENT_COMPILE.json` both exit 0; the parent's separated stdout/stderr match hashes and print only `propext`, `Classical.choice`, `Quot.sound`.

Evidence limitation: the first failed attempt has exact argv/cwd, exit 1, source hash and raw **combined** diagnostics. Its failed-source bytes and distinct stdout/stderr were not retained. This cannot be retroactively presented as complete first-attempt replay. The final theorem remains independently compiled and mathematically reviewed; the frozen full first-failure capture requirement is only partially met.

No proof/type/import/normalization blocker remains. This helper does not prove repeated analytic integration by parts, shifted-Legendre orthogonality, the all-degree interval moment, sphere/Funk-Hecke, historical four-axis acceptance or scientific admission. Those remain separate.
