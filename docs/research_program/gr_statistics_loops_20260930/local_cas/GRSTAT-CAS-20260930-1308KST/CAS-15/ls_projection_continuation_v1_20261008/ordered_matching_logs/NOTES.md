# Ordered matching author evidence

The source `../OrderedMatchingBridge.lean` proves same-index ordered eigenvalue
matching for arbitrary real symmetric 3x3 matrices from the induced Euclidean
operator norm. Repeated eigenvalues are permitted. `orderedSpectrum` is exactly
mathlib's `LinearMap.IsSymmetric.eigenvalues` with an explicit proof that the
Euclidean vector space has dimension three; `orderedSpectrum_antitone` verifies
descending order. The proof intersects the high-B and low-A spectral spans:
their dimensions add to four in dimension three. The resulting nonzero vector
has the required two Rayleigh bounds. Cauchy--Schwarz and the operator norm give
the one-sided inequality, and swapping the operators gives the absolute bound.

`matrix_ordered_gap_bound` applies the existing
`CAS15Spectral.ordered_gap_from_pointwise_matches` to the proved matches.
For a descending triple the minimum adjacent gap represents the minimum
pairwise gap, including the zero-gap repeated-eigenvalue case.

The final fresh runner invocation was:

```
python3 docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-15/ls_projection_continuation_v1_20261008/ordered_matching_logs/run.py
```

Final evidence is `20261008T154153587005Z/execution.json` and companion stdout
and stderr. Version, necessary spectral dependency, and final source each exit
zero. Four theorem axiom outputs show only `propext`, `Classical.choice`, and
`Quot.sound`. Pinned Lean is 4.31.0, mathlib revision
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`. The repository and oracle toolchain
files both hash to
`efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee`.

The retained failed runner `20261008T154052289657Z` used the wrong namespace for
`finrank_bot`; its exit one and downstream `sorryAx` outputs are failures only,
not accepted proofs. The intermediate successful runner
`20261008T154124443567Z` predates the matrix wrappers. Earlier author attempts,
including a wrong relative copy path, a missing Lean `-R` argument, an unproved
dimension coercion, and a linear-map coercion in `nlinarith`, are preserved in
the native tool transcript; those pre-runner streams were not written to these
log directories. No mathematical counterexample was found.

Requested native runtime: gpt-6.1-sol/high. Observed runtime: UNKNOWN. No
independent review is supplied by this author, no historical four-axis
adjudication was run, and scientific admission remains HOLD. Existing sources
were read and compiled as temporary dependencies only; no existing source was
edited.
