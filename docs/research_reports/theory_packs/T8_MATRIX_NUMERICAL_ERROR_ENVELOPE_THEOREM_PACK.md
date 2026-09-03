# T8 — Invariant matrix-valued numerical-error envelope and robust-rank boundary

Date: 2026-09-03  
Evidence grade: `DERIVED`, fresh exact/high-precision Wolfram checks  
Implementation status: current PR #444 source present; exact-head runtime
`PRESTART_NO_EXECUTION`  
Observational data used: none

## 1. Scope

This pack formalizes numerical uncertainty in a processed response matrix. It
does not define a physical high-multipole prior or a stochastic signal model.
It answers the conditional question:

> Given a frozen deterministic class of additive numerical perturbations, which
> row-rank statements survive every perturbation in that class?

Let

\[
K_{\rm obs}\in\mathbb R^{m\times n}
\]

be a computed response and

\[
K_{\rm obs}=K_{\rm true}+\Delta
\]

its relation to the target numerical operator. All matrices must use the same
orthonormal output/source coordinates, or an explicitly equivalent metric
representation.

The response is dimensionless in WU-011. The error envelope below has squared
response units, and its whitened singular values are dimensionless.

## 2. Declared additive family class

For each nonempty family \(f=1,\ldots,N_{\rm fam}\), let

\[
E_{f1},\ldots,E_{fn_f}\in\mathbb R^{m\times n}
\]

be frozen calibration matrices and let \(r_f>0\) be a frozen deterministic
coefficient-ball radius. Define

\[
\Delta_f=\sum_{i=1}^{n_f}b_{fi}E_{fi},
\qquad
\|b_f\|_2\le r_f,
\]

and

\[
\Delta=\sum_{f=1}^{N_{\rm fam}}\Delta_f.
\]

The family partition, basis identities, radii, and calibration/holdout split
are part of the uncertainty contract. They may not be tuned after inspecting a
rank margin or held-out escape.

Define

\[
S_f=\sum_iE_{fi}E_{fi}^T.
\]

## 3. Single-family Loewner bound

For every output-space vector \(x\),

\[
\begin{aligned}
x^T\Delta_f\Delta_f^Tx
 &=\left\|\sum_i b_{fi}E_{fi}^Tx\right\|_2^2\\
 &\le \|b_f\|_2^2\sum_i\|E_{fi}^Tx\|_2^2\\
 &\le r_f^2 x^TS_fx.
\end{aligned}
\]

Therefore

\[
\boxed{
\Delta_f\Delta_f^T\preceq r_f^2S_f.
}
\]

No stochastic independence assumption is used.

## 4. Additive-family envelope

Applying Cauchy--Schwarz over the \(N_{\rm fam}\) family contributions gives

\[
\left\|\sum_f\Delta_f^Tx\right\|_2^2
\le
N_{\rm fam}\sum_f\|\Delta_f^Tx\|_2^2.
\]

Hence

\[
\boxed{
\Delta\Delta^T
\preceq
N_{\rm fam}\sum_fr_f^2S_f.
}
\]

Introduce a strictly positive numerical regularization scale
\(\lambda_{\rm reg}\), fixed independently of the observed rank outcome, and
define

\[
\boxed{
\Gamma_E
 =N_{\rm fam}\sum_fr_f^2
  \sum_iE_{fi}E_{fi}^T
  +\lambda_{\rm reg}^2I_m.
}
\]

Then

\[
\Delta\Delta^T\preceq\Gamma_E,
\qquad
\Gamma_E\succ0.
\]

The factor \(N_{\rm fam}\) is a simple uniform family-level bound. It need not
be the tightest outer ellipsoid, but it is transparent and audit-friendly.

## 5. Equivalent family reparameterizations

### 5.1 Compensated uniform scaling

For every \(c_f>0\), transform

\[
E_{fi}'=c_fE_{fi},
\qquad
r_f'=r_f/c_f.
\]

This leaves the declared family perturbation set unchanged. Moreover,

\[
(r_f')^2\sum_iE_{fi}'E_{fi}'^T
 =r_f^2S_f,
\]

so

\[
\boxed{\Gamma_E'=\Gamma_E.}
\]

The robust-rank certificate is therefore invariant under arbitrary unit changes
or uniform basis rescalings inside a frozen family.

### 5.2 Orthogonal mixing inside one family

If

\[
E_{fa}'=\sum_iU_{ai}E_{fi},
\qquad U^TU=I,
\]

then

\[
\sum_aE_{fa}'E_{fa}'^T=S_f.
\]

Thus \(\Gamma_E\) is invariant under orthogonal family-basis changes.

### 5.3 Family split and merge

Splitting one coefficient ball into two independent balls or merging two balls
changes the admissible perturbation set in general. The envelope is not
required to remain invariant under an uncertainty-class change.

## 6. Exactly zero families

An exactly zero family generates only the zero perturbation. Adding it leaves
the uncertainty set unchanged but would increase \(N_{\rm fam}\), inflating
every active contribution.

Therefore an exactly zero family must be omitted or rejected. The current
source fails closed rather than silently dropping it, because silent deletion
could hide a malformed calibration registry.

This guard is part of the uncertainty semantics, not merely input sanitation.

## 7. Error whitening

Because

\[
\Delta\Delta^T\preceq\Gamma_E,
\]

one has

\[
\Gamma_E^{-1/2}\Delta\Delta^T\Gamma_E^{-1/2}
\preceq I_m.
\]

Consequently

\[
\boxed{
\|\Gamma_E^{-1/2}\Delta\|_2\le1.
}
\]

Define the error-whitened observed response

\[
\widetilde K_{\rm obs}=\Gamma_E^{-1/2}K_{\rm obs}.
\]

Its squared singular values are the generalized eigenvalues of

\[
K_{\rm obs}K_{\rm obs}^Tu
 =g^2\Gamma_Eu.
\]

## 8. Robust rank lower bound

Since

\[
\Gamma_E^{-1/2}K_{\rm true}
 =\widetilde K_{\rm obs}-\Gamma_E^{-1/2}\Delta,
\]

Weyl's singular-value perturbation inequality yields

\[
\boxed{
\sigma_j(\Gamma_E^{-1/2}K_{\rm true})
\ge
\sigma_j(\widetilde K_{\rm obs})-1.
}
\]

Thus every observed error-whitened singular value strictly above one provides
one robustly nonzero singular direction. With a preregistered ambiguity margin
\(\delta_g>0\), define

\[
\boxed{
\underline r_{\rm rob}
 =\#\{j:\sigma_j(\widetilde K_{\rm obs})>1+\delta_g\}.
}
\]

Then

\[
\operatorname{rank}_{\rm alg}K_{\rm true}
\ge\underline r_{\rm rob}
\]

for every perturbation in the declared class.

If \(n\ge m\) and all \(m\) singular values exceed \(1+\delta_g\), then

\[
\boxed{
\operatorname{rank}_{\rm alg}K_{\rm true}=m
}
\]

is certified for the declared class.

A count of robustly nonzero singular values is a rank lower bound. It does not,
by itself, certify the orientation of a partial singular subspace.

## 9. Full-row containment consequence

For WU-011, \(m=32\). If

\[
\sigma_{32}(\widetilde K_{\rm obs})>1+\delta_g,
\]

then every admissible \(K_{\rm true}\) has full row rank and

\[
\operatorname{Im}K_{\rm true}=\mathbb R^{32}.
\]

Therefore the deterministic low-source survivor vanishes for every admissible
error realization.

This implication remains conditional on the premise that the true numerical
error belongs to the frozen family class.

## 10. Finite held-out validation

For each held-out perturbation \(H_a\), compute

\[
h_a=\|\Gamma_E^{-1/2}H_a\|_2.
\]

A preregistered finite holdout set is contained when

\[
\max_a h_a\le1+\delta_{\rm hold}.
\]

The holdout set must remain disjoint from calibration. An escape blocks the
certificate; it may not be used to retroactively enlarge the same envelope and
then relabel the holdout as independent.

Passing a finite holdout registry establishes only that finite validation
statement. It is not a universal proof that every unobserved numerical error is
inside \(\Gamma_E\).

## 11. Required error-family provenance

A publication-facing finite-operator certificate requires content-bound fields
for at least:

```text
family_partition_id
family_basis_registry_hash
family_radius_registry_hash
weight_policy_id
regularization_policy_id
calibration_registry_hash
holdout_registry_hash
source/output coordinate identity
resolution and transform settings
processing_lmax and fit identity
```

The family radii must be fixed before the signal rank and independent holdout
outcomes are inspected.

Candidate numerical families include full-sky replay, resolution differences,
map-to-alm iteration differences, processing-cutoff differences, and an
independent continuum discrepancy. Which of these belong in calibration and
which remain holdouts is a preregistered modelling decision, not an automatic
consequence of the theorem.

## 12. Partial-rank subspace lane

Suppose only \(r<m\) singular values are robustly nonzero. This certifies a
rank lower bound but not a stable nuisance projector.

Let \(U_r\) and \(\widehat U_r\) be true and computed left singular subspaces.
A Wedin-type theorem requires both a perturbation bound and a positive spectral
separation. Schematically,

\[
\|\sin\Theta(\widehat U_r,U_r)\|_2
\lesssim
\frac{\|\Delta\|_2}{\operatorname{gap}_r}.
\]

Only after a certified projector bound

\[
\|P_{\widehat U_r}-P_{U_r}\|_2\le\varepsilon_P
\]

may an observed survivor be lower-bounded by

\[
\|P_{U_r^\perp}J\|_2
\ge
\|P_{\widehat U_r^\perp}J\|_2
 -\varepsilon_P\|J\|_2.
\]

A positive right-hand side certifies a true survivor. Without the gap and
projector control, thresholded singular vectors are diagnostic only.

## 13. Current implementation and evidence boundary

The current PR #444 source implements:

- the invariant uniform-family envelope;
- compensated family scaling;
- exact-zero-family refusal;
- positive-definite regularization;
- finite holdout checking;
- error-whitened robust rank lower bounds;
- typed full-row, partial-rank, ambiguous, and unresolved statuses.

Its current exact-head GitHub workflow ended before runner assignment and ran
zero steps. Source-equivalent local execution provides debugging evidence but
is not a byte-exact checkout receipt.

The last accepted finite-operator scientific terminal remains

```text
PASS_TASK7C_MATCHED_CONTROL_RANK_UNRESOLVED.
```

No current error-family registry has been proved complete for the actual
finite-HEALPix numerical error. The mathematical theorem is closed; the
scientific admission premise remains open.

## 14. Fresh Wolfram verification

An exact rational two-family example gave positive eigenvalues for

\[
\Gamma_{E,0}-\Delta\Delta^T:
\]

\[
4.0824292538182697\ldots,
\qquad
1.2625048208537984\ldots.
\]

Compensated family rescaling produced the exact zero matrix residual.

Adding an exactly zero family while incorrectly incrementing the family count
produced the nonzero inflation matrix

\[
\begin{pmatrix}
57493/22050&104/2835\\
104/2835&39205/46656
\end{pmatrix}.
\]

For a positive-definite sample \(\Gamma_E\), generalized eigenvalues of
\((KK^T,\Gamma_E)\) agreed with singular-value squares of
\(\Gamma_E^{-1/2}K\) to 80-digit precision:

\[
1.6153590323339096685\ldots,
\qquad
3.2258536775033474679\ldots.
\]

The sample minimum whitened singular value was

\[
1.2709677542463104\ldots>1,
\]

so the two-row sample satisfied the conditional full-row certificate.

The machine-readable record is
`T8_WOLFRAM_EXACT_RECEIPT.json`.

## 15. T8 terminal

```text
PASS_INVARIANT_MATRIX_ERROR_ENVELOPE_THEORY
/
ROBUST_RANK_LOWER_BOUND_THEOREM_PASS
/
PARTIAL_SUBSPACE_REQUIRES_GAP_BOUND
/
ACTUAL_ERROR_CLASS_COMPLETENESS_UNRESOLVED
/
CURRENT_EXACT_HEAD_RUNTIME_UNOBSERVED
```

This terminal is sufficient for Report A as a conditional numerical-analysis
theorem with an explicit unresolved admission boundary. It does not authorize a
finite-HEALPix no-go, a tuned family registry, observational execution,
physical-source identification, publication, or merge.
