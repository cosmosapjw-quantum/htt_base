# PR-271 Pillar-S exact/core statistical foundations

Status: proof-author artifact, independently reviewable
Claim ceiling: `diagnostic_only`
Observed-data effect: none
PR-268 source effect: none; every source row remains `NOT_ADJUDICATED`

This document proves only the typed successor statements recorded in
`pr271_spec.yaml`. The generated registry contains 34 legacy Pillar-S rows so
that omissions cannot be hidden, but its cardinality is not a proof count.
Twenty-nine untyped legacy rows remain `INCONCLUSIVE_MISSING_SIGNATURE`; the
five source-typed rows are reference-resolved with scalar-reduction tests, not
silently readjudicated.

## VT-S1

Let \(P,Q\) be probability laws on a common finite profile space and let
\(T\) be a deterministic scalarization. For every scalar cell \(B\),
\(P_T(B)=P(T^{-1}B)\) and likewise for \(Q\). The triangle inequality gives

\[
\frac12\sum_B |P_T(B)-Q_T(B)|
\leq \frac12\sum_x |P(x)-Q(x)|.
\]

The log-sum inequality on every fibre \(T^{-1}B\), followed by summation over
fibres, gives \(D_{\rm KL}(P_T\Vert Q_T)\leq D_{\rm KL}(P\Vert Q)\), including
the extended-value branch where \(P(x)>0,Q(x)=0\). Thus deterministic
scalarization cannot create identification information measured by these
divergences. It is sufficient only for a separately registered decision that
is constant on every scalar fibre; this is not a claim that scalar \(Q\) is a
sufficient statistic for the full state.

Probability-law admission is exact under the declared input encoding.
`Rational` and `Decimal` masses retain their exact values. A binary float is
decoded through its shortest round-trip decimal spelling, so the ordinary
declared law `(0.4, 0.1, 0.2, 0.3)` has unit mass while
`(1.0 + 5e-13,)` does not. No normalization tolerance can turn a non-law into
a probability law. KL is evaluated from those exact masses at high precision;
the working precision scales with the encoded rational mass size, and the
binary64 report must agree at two successive precisions while retaining the
data-processing order. A negative cancellation residue is never clipped into
an apparent certificate. Exhausted precision or an unrepresentable nonzero
projection refuses rather than emitting a misleading divergence.

## VT-S2

For an axis-aligned acceptance body
\(\mathcal B=\{x: |x_i|\le r_i\}\), \(r_i>0\), the Minkowski gauge is
\[
p_{\mathcal B}(x)=\max_i |x_i|/r_i.
\]
This covers coordinate thresholds, weighted max statistics, and the
one-dimensional legacy interval. For a covariance ellipsoid
\(\mathcal B=\{x:x^\mathsf TC^{-1}x\le1\}\) with symmetric positive-definite
\(C\),
\[
p_{\mathcal B}(x)=\sqrt{x^\mathsf TC^{-1}x}.
\]
The implementation solves the linear system and refuses rank deficiency; it
does not silently introduce a pseudoinverse or erase the active coordinate
set. Acceptance is decided from the exact encoded rational relation to the
unit boundary (`LT`, `EQ`, or `GT`). The floating `q_value` is a display value
only: even if a square root rounds to `1.0`, an exact `GT` result is rejected.

## VT-S4

For one typed probability law \(\nu\),
\(\Pi(t)=\nu\{X>t\}\). If \(t_1<t_2\), then
\(\{X>t_2\}\subseteq\{X>t_1\}\), so
\(\Pi(t_2)\le\Pi(t_1)\). The exactness is set-theoretic for the declared law.
For an empirical law it is exact for that empirical measure, not automatic
population coverage. Existing PR-265 contracts refuse objectives and
optimizer points where probability draws are required.

## VT-S7

Given registered samples \(X_1,\ldots,X_m\) and deterministic functional
\(F\), the empirical pushforward is
\[
\widehat\nu_F=m^{-1}\sum_i\delta_{F(X_i)}.
\]
Its summaries are derived from the sample-wise values. In general,
\[
\frac1m\sum_i \frac{N_i}{D_i}
\ne
\frac{\sum_iN_i/m}{\sum_iD_i/m},
\]
and neither side may replace the other. Missing or inadmissible functional
cells remain typed and block complete summaries rather than being imputed.

## VT-S8

For one paired joint law in a common feature basis,
\[
\operatorname{Cov}(X_a-X_b)
=C_{aa}+C_{bb}-C_{ab}-C_{ba}.
\]
If cross covariance is omitted, the reported covariance is
\(C_{\rm omitted}=C_{aa}+C_{bb}\), hence
\[
C_{\rm omitted}-C_{\rm actual}=C_{ab}+C_{ba},
\qquad
C_{\rm actual}-C_{\rm omitted}=-(C_{ab}+C_{ba}).
\]
Both ordered cross blocks are retained. Marginal-only inputs cannot be
relabeled as paired.

## TF-09-PARITY-SIGN-EXACTNESS

After conditioning on the nonzero registered pairs, assume the full sign
vector is uniform under coordinate-wise sign flips. Equivalently for the
implemented pooled test, the signs are conditionally independent fair
Bernoulli variables. Then the positive count is exactly
\(\operatorname{Binomial}(n,1/2)\), and the two-sided tail is a finite rational
sum of binomial coefficients. Zero ties are retained in the report but
excluded from \(n\). Global sign symmetry alone is insufficient, and dependent
nested rungs are not pooled.

## TF-11-MASK-PATH-MARTINGALE

Fix one finite atomic probability space, one common integrable target \(X\),
and partitions
\(\mathcal P_0\preceq\mathcal P_1\preceq\cdots\preceq\mathcal P_k\), where
each finer partition refines the preceding one and all cells have positive
mass. Direct finite summation within cells gives
\[
\mathbb E[\mathbb E(X\mid\mathcal P_{j+1})\mid\mathcal P_j]
=\mathbb E(X\mid\mathcal P_j).
\]
The implementation uses exact rational arithmetic. Support-set nesting
without explicit partitions, different targets at different rungs,
zero-mass cells, nonnested masks, optional stopping, convergence, and the
known unstable fast-oracle branch are outside this statement.

## Legacy scalar reductions

The five source-typed legacy rows are resolved to their immutable v2
signatures and exercised only on their declared scalar domains:
`SIG-P18`, `SIG-T1p`, `SIG-DL1`, `SIG-L-T2-EXIST`, and `SIG-T2G`. The remaining
29 titles receive no invented estimand, law, covariance, premise, or domain.

## Forbidden interpretations

These results are statistical-method foundations only. They create no MIO
posterior, HTT evidence result, observed-data result, native-solver or
morphology-atlas validation, geometry detection, or Bianchi-family
identification.
