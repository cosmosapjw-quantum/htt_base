# CAS15 formal spectral-closure review

Scope: `CoercivityBridge.lean`, `OrderedMatchingBridge.lean`,
`FullSynthesis.lean`, their direct existing dependencies, and final fresh build
receipt `../build_logs/20261009T000200000000Z/execution.json`.

Requested reviewer runtime: `gpt-6-astra/ultra`. Observed runtime: `UNKNOWN`;
the request is not treated as an observation. The reviewer was fresh-context,
read-only, and did not author the candidate.

## Verdict

**PASS_SCOPED — no blocking finding.** The reviewer independently inspected the
declarations and proof bodies. It confirmed that rotated coercivity derives
skew preservation, Frobenius invariance, commutator covariance, and the
diagonal gap estimate without an `hcoerc` input; zero gap remains valid. It
confirmed same-index decreasing-spectrum matching from the induced Euclidean
operator norm, including multiplicities and without a permutation or `hmatch`
premise. The final synthesis keeps arbitrary `Rhat`, uses the Frobenius and
operator norms in their respective roles, and divides only under `hdelta > 0`.

The final receipt binds the eight Lean source hashes and records version plus
eight Lean compilation steps, all exit 0. Its axiom reports contain only
`propext`, `Classical.choice`, and `Quot.sound`, with no `sorryAx`. Earlier
integration receipts `20261009T000000000000Z` and `20261009T000100000000Z`
remain failed type/interface attempts and are not success evidence.

## Residual scope

`FullSynthesis.lean` accepts an explicit orthogonal diagonalization and
pairwise observed-gap witness; it does not construct that witness from the
symmetric-matrix hypothesis. The inverse perturbation bound requires a
positive observed gap, while ordered matching itself permits repeated
eigenvalues. The build receipt records source hashes but not a separate
`build.py` hash. These are stated scope/provenance limits, not reviewed
blocking findings.

This is a formal finite linear-algebra component only: historical four-axis
adjudication remains `NOT_RUN`, and scientific admission remains `HOLD`.
