# T4 — Exact finite-null ranks under row-equivariant analysis

Date: 2026-09-03  
Evidence grade: `DERIVED`, literature-supported, and exactly enumerated in
Wolfram for finite adversarial fixtures  
Observational data used: none

## 1. Statistical object

Let

\[
Z=(Z_0,\ldots,Z_{n-1})
\]

be the observation-plus-reference rows. The distinguished row `0` is a label
used after data collection; it must not change the analysis algorithm.

The finite-rank theorem concerns a complete map

\[
\mathcal A:\mathcal Z^n\longrightarrow\mathbb R^n,
\qquad
S=\mathcal A(Z),
\]

not merely a final scalar formula. Preprocessing, representation conversion,
chart selection, nuisance fitting, coordinate selection, score construction,
and tie policy are all part of `A`.

For a permutation `pi` of the row labels, write `pi Z` and `pi S` for the
correspondingly permuted tuples.

## 2. Main theorem

### Theorem T4.1 — exchangeable rows plus equivariant analysis

Assume:

1. `Z` is jointly exchangeable under the null,
   \(Z\overset d=\pi Z\) for every row permutation `pi`;
2. the complete analysis is row-permutation equivariant,
   \[
   \mathcal A(\pi Z)=\pi\mathcal A(Z);
   \]
3. the upper-tail direction and tie convention are fixed before evaluation.

Then `S=A(Z)` is exchangeable. Define

\[
p_i=\frac1n\sum_{j=0}^{n-1}\mathbf 1\{S_j\ge S_i\}.
\]

For every `alpha in [0,1]`,

\[
\boxed{\Pr(p_i\le\alpha)\le\alpha.}
\]

If the scores are almost surely tie-free, `p_i` is exactly uniform on

\[
\left\{\frac1n,\frac2n,\ldots,1\right\}.
\]

For the observed row this is equivalently

\[
\boxed{
p_{\rm obs}
 =\frac{1+\sum_{j=1}^{n-1}\mathbf 1\{S_j\ge S_0\}}{n}.
}
\]

The observation is included in the finite null distribution; the p-value is
never zero.

### Proof

Equivariance and exchangeability give

\[
\mathcal A(Z)\overset d=\mathcal A(\pi Z)
 =\pi\mathcal A(Z),
\]

so the score vector is exchangeable.

Condition on the unordered multiset of scores. Let its distinct values be
ordered from largest to smallest with group sizes `m_1,...,m_K` and cumulative
counts

\[
c_k=m_1+\cdots+m_k.
\]

Every row in tie group `k` has `p=c_k/n`. Conditional exchangeability makes
the label `i` uniform over the `n` multiset positions. The number of positions
with `p<=alpha` is either zero or one cumulative count `c_k` satisfying
`c_k/n<=alpha`. Therefore its conditional probability is at most `alpha`.
Averaging over score multisets proves super-uniformity. With no ties, every
cumulative count `1,...,n` occurs once, proving exact discrete uniformity.

## 3. Data-adaptive selection is allowed only through equivariance

Let a global tuning or statistic choice be

\[
\widehat\lambda=\Lambda(Z).
\]

If

\[
\Lambda(\pi Z)=\Lambda(Z)
\]

and the row scores constructed from that choice satisfy

\[
S_i=s(Z_i,Z,\widehat\lambda),
\qquad
S(\pi Z)=\pi S(Z),
\]

then the selected analysis remains covered by Theorem T4.1. Thus
“data-dependent” is not by itself the failure condition. The failure is
**label-asymmetric adaptation**.

Examples that can remain valid include choosing a common covariance estimator,
a common regularization parameter, or a common statistic family from the
unordered joint pool and then evaluating every row by the same leave-one-out or
fully symmetric rule.

The following are invalid without a separate correction:

- choosing a coordinate because it makes the observed row most extreme;
- tuning a tail or kernel using row `0` while treating the other rows as fixed
  competitors;
- deleting only simulation rows with an unavailable chart;
- estimating a nuisance from the observation by a different algorithm than is
  applied to the reference rows.

## 4. Exact asymmetric-selection counterexample

Consider four two-coordinate rows

\[
(-2,-2),\quad(-2,-1),\quad(-2,0),\quad(-1,-2),
\]

and let every one of the 24 row permutations be equally likely.

An invalid algorithm chooses the coordinate with the larger absolute value in
the distinguished first row, assigns an exact tie to coordinate 2 by a fixed
deterministic rule, and then ranks that row by absolute value in the chosen
coordinate. Exact enumeration gives

\[
p_0=\frac12\quad\text{for 12 permutations},
\qquad
p_0=\frac34\quad\text{for 12 permutations}.
\]

At `alpha=3/4`,

\[
\Pr(p_0\le3/4)=1>3/4,
\]

an exact size violation of `1/4`.

The numerical split depends on the declared tie-break. If exact ties are sent
to coordinate 1 instead, the counts are

\[
p_0=\frac12\quad\text{for 6 permutations},
\qquad
p_0=\frac34\quad\text{for 18 permutations},
\]

but the maximum size violation remains `1/4`.

If instead the coordinate is selected by the permutation-invariant pooled sum
of squares, the same fixture gives `p_0=3/4` for 18 permutations and `p_0=1`
for six; its maximum super-uniformity violation is zero.

Thus the counterexample isolates label-asymmetric selection rather than
blaming adaptation in general, and its exact count receipt is meaningful only
with the tie rule recorded.

## 5. Tie and tail rules

### Conservative ties

The `>=` rule in Theorem T4.1 is super-uniform for arbitrary ties. A randomized
within-tie rule can recover an exactly uniform continuous or discrete rank, but
its auxiliary randomization must be preregistered and reproduced.

### Monotone transformations

A strictly increasing common transformation of all scores preserves every
upper-tail rank. A strictly decreasing transformation swaps upper and lower
tails. A non-strict transformation may create ties and therefore changes the
finite distribution even when the conservative theorem remains valid.

### Two-sided statistics

“Two-sided” is not an operation applied after seeing the observed sign. It must
be encoded as one fixed row-equivariant score, such as an absolute value or a
predeclared symmetric discrepancy, before ranking.

## 6. Chart failure and typed missingness

The cleanest Report A policy is:

1. preserve every row and use a statistic defined on the full Q/O tensors when
a normalized orbit chart is unavailable; or
2. issue a pool-level typed abstention if the frozen statistic cannot be
evaluated symmetrically.

A more elaborate missingness-aware score is admissible only if the complete
status-and-score map is permutation equivariant and its ordering rule is fixed.
Unavailable values are not zeros. Observation-specific deletion and
simulation-only deletion both violate the theorem.

## 7. Null fidelity is independent of algebraic rank validity

Joint exchangeability is a scientific premise, not a consequence of having a
finite file with one observation and many simulations.

A noisy observed Planck product and noise-free CMB-only simulations are not
exchangeable merely because they share a harmonic representation. That lane is
descriptive sensitivity unless a faithful joint noise, mask, calibration, and
systematics model is supplied.

Similarly, two result lanes that share the observed sky or underlying CMB
realizations are statistically dependent. Their p-values cannot be multiplied
or described as independent replications without a dependence model.

## 8. Finite random permutations versus a finite simulation pool

Theorem T4.1 is an exchangeable-row result. Random-permutation tests use a
related but distinct group-invariance/randomization hypothesis. Exactness with
a random subset of permutations additionally requires a valid conditional
Monte Carlo construction that includes the identity/observed statistic.

The report cites:

- D. M. Ritzwoller, J. P. Romano, and A. M. Shaikh, *Randomization Inference:
  Theory and Applications*, arXiv `2406.09521`;
- B. Phipson and G. K. Smyth, *Permutation P-values Should Never Be Zero*,
  Statistical Applications in Genetics and Molecular Biology 9, Article 39
  (2010), DOI `10.2202/1544-6115.1585`;
- J. Hemerik and J. Goeman, *Exact testing with random permutations*, TEST 27,
  811--825 (2018), DOI `10.1007/s11749-017-0571-1`.

These references support the group-invariance and identity-inclusion boundary;
the row-equivariant formulation above is derived directly for the repository's
observation-plus-reference setting.

## 9. Exact Wolfram validation

A fresh exact enumeration checked every score vector over the alphabet
`{0,1,2}` for pool sizes `n=2,...,7`. For each fixed multiset, the distinguished
label was allowed to occupy every row position. The maximum violation of

\[
\Pr(p\le\alpha)\le\alpha
\]

was zero for every `n`, including all tie patterns.

Tie-free score sets gave one occurrence of every grid value `1/n,...,1`.
For the asymmetric fixture, tie-to-coordinate-2 and tie-to-coordinate-1 rules
gave counts `(12,12)` and `(6,18)`, respectively, with exact maximum size
violation `1/4` in both cases. The symmetric pooled rule gave counts `(18,6)`
at p-values `(3/4,1)` and zero maximum violation.

The machine-readable receipt is
`T4_WOLFRAM_FINITE_RANK_RECEIPT.json`.

## 10. T4 terminal

```text
PASS_FINITE_NULL_ROW_EQUIVARIANCE_THEORY
```

This terminal proves the finite-sample rank statement under its explicit
exchangeability and equivariance premises. It does not establish that any
particular Planck/FFP10 pool satisfies those premises, select the future tensor
statistic, or produce an observational p-value.
