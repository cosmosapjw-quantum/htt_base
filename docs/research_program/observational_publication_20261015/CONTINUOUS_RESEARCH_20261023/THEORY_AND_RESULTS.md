# Fixed-design astrometry repair and retained-score continuation

Owner `htt`; status `CONDITIONAL`, claim tier C1; transfer source `none`.
Artifact mode: actual published-summary algebra, plus a finite-nuisance adapter
tested against manufactured designs. This is not new empirical sky coverage,
cosmic acceleration, global tilt or native Bianchi identification.
Source: PR561 intake `a8e66da28461a415f5da3b3d609c482554d2dcd1`,
`ADVERSARIAL_AUDIT_20261022/continuation/astrometry/RESULT.json`.
All plotted numbers derive from `ASTROMETRY_RESULT.json`; units are µas/yr.

## What the research loop changed

The original intuition survives in an exact, narrower form: depth contrasts can
remove an observer field common to every redshift bin, while retaining depth
dependence. The estimator and selection experiment matter. Subtracting posterior
means is not the same as forming an invariant, unpenalized GLS contrast.

Write the frozen selected-row experiment as
\(y=Dg+Ha+\epsilon\), with 18 signal coefficients ordered as E1xyz/B1xyz in
each of three reported-redshift bins. Let \(A\) repeat one E1 vector in every
bin, and let \(L\) take low-minus-high E1. Thus \(LA=0\).
For fixed known covariance \(C_m\) and an estimable unpenalized fit,

\[
\widehat g_m=(D^TC_m^{-1}D)^{-1}D^TC_m^{-1}y,
\qquad L\widehat g_m(y+DAc)=L\widehat g_m(y).
\]

Rows, bin membership, design, weights and covariance must stay fixed. A new
proper-motion-dependent catalogue selection is a different experiment. Neither
unequal bin sizes nor a mask invalidate the identity under those conditions.

With the actual signal prior variance \(p=10000\),
\(\Sigma_m=(V_m^{-1}+p^{-1}I)^{-1}\) and
\(\mu_m=(I-\Sigma_m/p)\widehat g_m\). Therefore posterior contrast leakage
is \(L(I-\Sigma_m/p)Ac\), generally nonzero. A two-bin example with
\(V=\operatorname{diag}(1,4),p=1,L=(1,-1)\) gives leakage \(0.3c\).
For the actual 32-model mixture the exact fixed-design counterfactual is

\[
\mu'_m=\mu_m+(I-\Sigma_m/p)\delta,\quad
w'_m\propto w_m\exp[-\delta^T\mu_m/p+\delta^T\Sigma_m\delta/(2p^2)],
\quad\delta=Ac.
\]

The implementation verifies this against a direct Gaussian mixture refit, not
against a second copy of the same formula. It also recovers GLS from every
published posterior via \(F=\Sigma^{-1}-p^{-1}I\) and \(f=\Sigma^{-1}\mu\).

## Actual data-summary results

Both cohorts and all 32 covariance models per cohort were processed.

| Quantity | Full cohort, 755850 rows | Known-cut margin, 558407 rows |
|---|---:|---:|
| Maximum common-E1 posterior leakage operator norm | 3.50670294e-5 | 3.27039928e-5 |
| Mixture contrast shift for common E1=(100,0,0) | (0.00271025, 0.00026054, -0.00043673) | (0.00147611, 0.00017242, -0.00044838) |
| GLS contrast at (lmax,tauA,tauT)=(3,10,30) | (-0.15858988,0.42467417,-0.01549751) | (1.12369092,0.60342836,0.07939390) |
| Corresponding coordinate SD | (0.86433745,0.78289362,0.80860079) | (1.18102899,1.12644530,1.24089745) |

This leakage is tiny. It does **not** explain or repair the earlier omitted-l4
coverage of 0.28418 or fixed-template-mean coverage of zero. Those failures remain
failed. More rows do not remove a misspecified nuisance mean.

The result file includes all fixed-model means/full covariances, low-minus-high
E1 and six independent contrasts (low-minus-high, middle-minus-high). For each
model define the three-dimensional 95% ellipsoid using chi-square threshold
7.814727903251179. The union over models covers at least 95% **if one of those
fixed zero-mean Gaussian covariance models is true**. The coordinate envelope in
the JSON/figure is a bounding box of this union; it is not a replacement for its
full covariance or a calibrated empirical confidence set under omitted fields.

## Actual compressed-summary limitation, with a constructive escape

A common sky field need not induce common fitted E1 coefficients: the angular
and error-weight distributions differ by bin. Let \(V_0=(D^TN^{-1}D)^{-1}\),
\(B=D^TN^{-1}H\), and \(C=H^TN^{-1}H\). With positive finite nuisance
prior covariance \(P\), Woodbury gives

\[
V_m-V_0=V_0B[P^{-1}+C-B^TV_0B]^{-1}B^TV_0.
\]

Thus its range is the contamination range of the baseline compressed GLS
estimator. For the actual full (3,10,10) model, this difference has rank18,
eigenvalue range 8.45567e-6 to 2.35346. After the six E1 contrasts it has rank6,
range 2.2573001869759178e-5 to 0.0033602163628226414. Margin ranks are also18/6. Relative numerical
rank tolerance1e-9 and all eigenvalues are in the generated JSON.

No nonzero linear combination of these baseline compressed E1 contrasts
annihilates every arbitrary original H-mean. This is a limitation of that
compressed estimator, not a no-go for the research program. The retained joint
scores preserve residual-field information discarded by those summaries.

## Finite nuisance quotient without a solver or catalogue replay

Use all102 retained columns:18 signal plus24 l2/l3 E/B,42 selection-template
responses and18 l4 E/B nuisance columns. Partition \(G=X^TN^{-1}X\),
\(b=X^TN^{-1}y\), \(X=[D,U]\), and compute

\[
F=G_{DD}-G_{DU}G_{UU}^{+}G_{UD},\quad
s=b_D-G_{DU}G_{UU}^{+}b_U.
\]

For an arbitrary fixed coefficient vector in the **included** U span,
\(E[s]=Fg\), \(\operatorname{Cov}(s)=F\), conditional on the supplied
Gaussian noise covariance. A contrast K is estimable iff \(K=KF^+F\); then
\(\widehat\theta=KF^+s\), with covariance \(KF^+K^T\).
The adapter reports the projector, numerical rank, estimability residual and
`null` for non-estimable requested components. It never turns a pseudoinverse
zero into an identified physical parameter. The printed covariance for an
unestimable row is only the projected-coordinate covariance.

The implementation first equilibrates each nonzero column by the square root
of its Gram diagonal. Exactly zero diagonals require exactly zero rows, columns
and scores. Symmetry, positive semidefiniteness and nuisance rank are checked in
these normalized coordinates, so changing nuisance units does not silently drop
a valid nuisance span. Positive nuisance eigenvalues between roundoff and the
rank threshold are ambiguous and are rejected. Numerical nuisance null vectors
must have compatible cross blocks and scores. Treating roundoff-null directions
as exactly null is an explicit conditional assumption, not a rigorous floating
point proof. The discarded quotient score is checked against a cancellation-aware
relative roundoff bound with no absolute unit floor.

Normalized quotient eigenvalues determine rank; they are not the physical Fisher
eigenvalues. Full-rank estimates and covariances transform back using the signal
column scales. At partial rank, a thin QR decomposition of the scaled retained
basis constructs the **physical Euclidean** range projector and minimum-norm
estimate/covariance in the supplied units. A conservative guard combines the
signal scale ratio, quotient roundoff and retained/discarded spectral gap; it
rejects unreliable physical projection. This is a conservative check, not a
rigorous error certificate. The output records column scales, accepted nuisance
rank, normalized rank/roundoff tolerances, contrast relative tolerance and the
physical transport guard value/threshold. Full-rank and rank-zero branches mark
that guard as not applicable; none of these diagnostics is a certificate.
Under anisotropic signal unit changes partial-rank
Euclidean minimum-norm estimates and projectors are not naively tensor-equivariant;
comparisons use an analytic physical reference in the current units and invariant
estimable contrasts. Every nonzero contrast uses a relative row-space residual
after normalization; an exact zero contrast is separately estimable. Rescaling
a nonestimable contrast cannot promote its `null` estimate to an identified zero.
If division by signal column scales underflows any nonzero contrast entry to
zero, the adapter explicitly rejects the input before testing for zero rows.
Estimable contrast estimates/covariances are computed directly in the normalized
quotient. A nonzero estimable contrast must have a positive finite computed
variance; a zero or nonfinite diagonal is rejected as outside floating-point
range. Exact zero contrasts remain valid with zero variance. These conservative
range checks do not certify the accuracy of every representable result.
Unestimable covariance entries describe physical projected coordinates
only; they are not uncertainties on an identified requested contrast.

Tests cover a direct row-residualized dense reference, unrestricted nuisance
means, redundant nuisance columns, exact rank loss, incompatible/indefinite
statistics, Gaussian covariance Monte Carlo and direct mixture refit. Additional
regressions cover nuisance/signal unit changes against independent row-space
references, scaled nonestimable contrasts, analytic partial-rank physical
projections, ambiguous positive nuisance rank and ill-conditioned transport
rejection, as well as exact-zero and fully confounded designs. Regressions also
include the extreme-unit contrast-normalization underflow reproduction
and nonzero estimable variance underflow/overflow rejection. These are
algorithm checks, not validation of Gaia's actual spatial/classifier law.

The public summary lacks the l4 cross-Gram. The two existing local NPZ files
are sufficient for the next real-data calculation: approximately84kB each for
uncompressed G/b alone, plus metadata; compressed file sizes were not observed.
No new755850-row extraction is required. They were inaccessible here because
the owner-machine transport hit its monthly quota. The adapter has **not** run
on those actual102-column files in this session.

```sh
P=docs/research_program/observational_publication_20261015
C=/mnt/extdrive/workdir/htt_open_data/a22_20261023/astrometry
python scripts/htt_astrometry_quotient.py stats --input "$C/full_stats.npz" \
  --expected-sha256 4d9406de69546e72dff79d4fc611703e8eb450944c4dcc254f8484c98a22d5da \
  --output "$P/CONTINUOUS_RESEARCH_20261023/execution/R23-Q/full.json"
python scripts/htt_astrometry_quotient.py stats --input "$C/margin_stats.npz" \
  --expected-sha256 e0148768bfdef02c9e9291ec0bd2b79e7b1e859a5c343dc2031259c876a671e5 \
  --output "$P/CONTINUOUS_RESEARCH_20261023/execution/R23-Q/margin.json"
```

Unrestricted deterministic means invalidate reuse of the old Gaussian-field
radial-cut Q guarantee. Selection requires a new sourcewise mean bound or an
explicit conditional selected-sample likelihood. The physical same-congruence
PM/NNR/clock response, arbitrary residual spatial covariance and classifier law
remain separate obligations. No K03/K04/K05 acceptance follows automatically.

## Ten-step theory and coding loop actually used

1. Freeze question: why continued numerical work did not meet42-node acceptance.
2. Read five commit deltas, actual failed controls, router and stage instructions.
3. Separate missing physical inputs, incorrect invariance, and dispatch defects.
4. Generate alternatives: de-shrink, nuisance projection, bounded deterministic bias.
5. Adversarially reject de-shrinking as a remedy for the large coverage failures.
6. Derive fixed GLS invariance, adaptive-mixture counterfactual and score quotient.
7. Execute64 actual summary models and independent dense-reference tests.
8. Route substantive coverage question to an actual Astra/ultra native worker;
   keep requested runtime separate from independently observed UNKNOWN.
9. Implement a durable whole-DAG host controller, exact cached-score consumer and
   figure; independently review code, math and claim limits.
10. Publish reviewed changes, then continue the next input/action. Preserve exact
    inaccessible inputs and a runnable local continuation, rather than inflating18/42.

## Publication contribution

The conditional contrast/invariance and information-loss analysis is a candidate
methods component. Its mathematical identities are standard GLS/Woodbury, so
novelty must come from the source-bound joint analysis and empirical robustness,
not renaming those identities. A publishable Gaia/redshift result additionally
needs actual augmented-score execution, defensible selection/spatial error law,
whole-field coverage, redshift-error sensitivity and independent scientific
comparison. All six manuscripts remain NOT_READY_TO_SUBMIT.
