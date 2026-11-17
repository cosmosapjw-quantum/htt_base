# R61 mixed vector–tensor invariant: bounded R5/C5 component

This component computes the global range of
\(\phi=\beta^T(K-Q_{\rm cal})\beta\), where \(K=\sum_A\kappa_A E_A\),
on a single projected simultaneous confidence ellipsoid with an independent
STF calibration ball. It retains all beta–kappa covariance. The derivation is
exact under the stated domain; the implemented enclosing bounds use float64
and a roundoff guard, and are **not a formal interval-arithmetic proof**.
Local multistart optimization generates feasible witnesses only. The reported
global numerical gap is supplied by an exhaustive branch-and-bound covering.

## Domain and conventions

Use dimensionless \(\beta=V/c\) with \(c=299792.458\) km/s. The five real
3-by-3 matrices \(E_A\) are symmetric, trace free and Frobenius orthonormal.
The R54/R58 ordering is xx−yy, xx+yy−2zz, xy, xz, yz, with the usual
\(1/\sqrt2\), \(1/\sqrt6\), and off-diagonal \(1/\sqrt2\) coefficients.

Let \(z=(\beta,\kappa)\in\mathbb R^8\), center \(h=(h_b,h_k)\), and SPD
covariance \(C\). The domain is

\[
(z-h)^T C^{-1}(z-h)\le c_*,\qquad
\|Q_{\rm cal}\|_F\le\sqrt{15/2}\,\rho.
\]

Here \(\rho^2=\langle(n^TQ_{\rm cal}n)^2\rangle_{S^2}\), since for an STF
tensor \(Q\), that average equals \(2\|Q\|_F^2/15\). For a calibration
full-sky magnitude RMS \(r_m\), the parent convention gives
\(\rho=r_m/(5/\ln10)\). All reported \(\phi\) values are dimensionless.

When extracting these eight coordinates from the R58 eleven-coordinate
ellipsoid, take the corresponding **principal covariance submatrix**, retain
the same cutoff \(c_*=\chi^2_{11}(.95)=19.67513757268249\), and rescale all
velocity rows and columns by \(1/c\). This is a projection, not a new
eight-degree-of-freedom confidence calibration. A witness can be lifted to
the eliminated dH coordinates with the usual conditional mean
\(h_d+C_{dz}C_{zz}^{-1}(z-h_z)\); the projected ellipsoid quadratic is then
unchanged.

## Elimination and feasible witnesses

Set

\[
R=C_{kb}C_{bb}^{-1},\qquad
D=C_{kk}-C_{kb}C_{bb}^{-1}C_{bk},\qquad
\bar\kappa=h_k+R(\beta-h_b).
\]

Completing the square yields

\[
(z-h)^TC^{-1}(z-h)=r_b^2+
(\kappa-\bar\kappa)^TD^{-1}(\kappa-\bar\kappa),\qquad
r_b^2=(\beta-h_b)^TC_{bb}^{-1}(\beta-h_b).
\]

For \(v_A=\beta^TE_A\beta\), the conditional support endpoints are

\[
v^T\bar\kappa\pm\sqrt{c_*-r_b^2}\sqrt{v^TDv}.
\]

Their exact-arithmetic witnesses are
\(\kappa_\pm=\bar\kappa\pm\sqrt{(c_*-r_b^2)/(v^TDv)}Dv\).
At \(v=0\), use the conditional center. Positivity of \(D\) follows from
the SPD joint covariance.

Write \(T_\beta=\beta\beta^T-\|\beta\|^2I/3\). Then
\(\|T_\beta\|_F=\sqrt{2/3}\|\beta\|^2\), so the calibration support is
\(\sqrt5\rho\|\beta\|^2\). For endpoint sign \(s=+1\) (maximum) or
\(s=-1\) (minimum), choose

\[
Q_{{\rm cal},s}=-s\sqrt{15/2}\rho\,
T_\beta/\|T_\beta\|_F.
\]

This makes \(-\beta^TQ_{{\rm cal},s}\beta=s\sqrt5\rho\|\beta\|^2\)
and saturates the allowed calibration norm. At \(\beta=0\), choose zero.

Let \(L L^T=C_{bb}\), \(B=\sqrt{c_*}L\), \(A=RB\), and
\(\beta=h_b+Bx\), \(\bar\kappa=h_k+Ax\), \(\|x\|\le1\). Define

\[
F_s(x)=s\,v(x)^T\bar\kappa(x)+\sqrt5\rho\|\beta(x)\|^2
 +\sqrt{c_*}\sqrt{(1-\|x\|^2)\,v(x)^TDv(x)}.
\]

Then \(\max\phi=\max F_+\), and \(\min\phi=-\max F_-\). This reduction
keeps the cross-covariance through \(A\) and the Schur complement \(D\).
No direction or tensor component is independently re-randomized.

## Global box upper bound

The normalized beta ball lies in \([-1,1]^3\). A box \([\ell,u]\) is empty
when its nearest point to zero has norm exceeding one. Otherwise use midpoint
\(m\), half widths \(d\), and \(x=m+\delta\), \(|\delta_i|\le d_i\).
Each vector component is an exact quadratic:

\[
v_A(m+\delta)=v_A+J_A\delta+\delta^TM_A\delta,
\quad M_A=B^TE_AB,\quad J_A=2\beta(m)^TE_AB.
\]

The non-root part \(P_s=s\,v^T\bar\kappa+\sqrt5\rho\|\beta\|^2\) is a
cubic polynomial, with its exact cubic remainder bounded in absolute value by

\[
v_2^T|A|d,\qquad (v_2)_A=d^T|M_A|d.
\]

For any \(t>0\), Young's inequality gives the polynomial majorant

\[
\sqrt{u_x q_x}\le\frac12(tu_x+q_x/t),\quad
u_x=1-\|x\|^2\ge0,\quad q_x=v(x)^TDv(x)\ge0.
\]

At an interior center, \(t=\sqrt{q_m/u_m}\) gives value and gradient
contact. The code regularizes this choice near box/ball boundaries; positivity
of \(t\), not tangency, is what proves the majorant. The resulting polynomial
\(U_s=P_s+\sqrt{c_*}(t u_x+q_x/t)/2\) has degree four. Its midpoint value,
gradient, and quadratic coefficient matrix are evaluated exactly as
polynomial expressions. The cubic and quartic remainder magnitudes are bounded
by

\[
R_3\le v_2^T|A|d+
\frac{\sqrt{c_*}}{t}(|J|d)^T|D|v_2,
\qquad
R_4\le\frac{\sqrt{c_*}}{2t}v_2^T|D|v_2.
\]

For a quadratic \(g^T\delta+\delta^TQ\delta\), valid upper bounds are
\(|g|^Td+\max(\lambda_{\max}(Q),0)\|d\|^2\) and the coordinate-wise
absolute-value bound. When \(Q\) is negative definite, the unconstrained
maximum \(-g^TQ^{-1}g/4\) is a third valid upper bound. The minimum of these
upper bounds remains an upper bound. Adding \(U_s(m)+R_3+R_4\) encloses
the box maximum.

A second bound uses the cubic bound for \(P_s\) and
\(\sqrt{\max u_x\,\max q_x}\), with
\(|v(x)|\le|v|+|J|d+v_2\). This is well behaved at \(v=0\) and the sphere
boundary. The smaller of the two valid bounds is retained.

Branch-and-bound bisects the longest box edge, evaluates feasible midpoints,
and prioritizes the largest upper bound. Fifteen SLSQP starts improve the
initial feasible witness but do not affect bound validity. The covering upper
bound includes all live leaves and the largest recorded upper bound of any
tolerance-pruned leaf. Therefore a node cap still returns an enclosing bracket
with an explicit nonzero gap. The cap is per endpoint. Returned minimum and
maximum brackets are respectively `[enclosing_lower, feasible_minimum]` and
`[feasible_maximum, enclosing_upper]`.

The real-arithmetic inequalities prove global enclosure. Floating-point
eigenvalues, solves and cancellation are not accompanied by directed rounding;
the scale-dependent guard does **not** upgrade this to formal certification.
This distinction is included in every API return.

## Validation and actual pilot

Execute `python -u r61_mixed_validation.py` in this directory. The verifier
reads the preserved 7-model numerical input extraction and writes
`r61_mixed_finalpilot.json`. Tests include:

- An independent radial analytic solution for zero center and covariance
  `diag(sigma_beta^2 I3, sigma_kappa^2 I5)`. If
  \(a=\sqrt5\rho\), \(b=\sqrt{2/3}\sigma_\kappa\), then
  \(y=(\sqrt{a^2+3b^2c_*}-a)/(3b)\) and
  \(\phi_{\max}=-\phi_{\min}=\sigma_\beta^2(c_*-y^2)(by+a)\).
  At \(\rho=0\), this is
  \(2\sqrt2\sigma_\beta^2\sigma_\kappa c_*^{3/2}/9\).
- A simultaneous spatial rotation of beta, kappa, and the entire covariance.
  The two feasible endpoints agreed to `3.414e-19` in the actual test.
- Reconstructed conditional kappa and calibration tensors; 20,000 direct
  eight-dimensional ellipsoid draws; 28,394 feasible point checks of box
  upper bounds; explicit zero-node cap behavior; zero cutoff; invalid inputs.
- Seven R58 covariance variants at four full-sky calibration magnitude RMS
  values `[0, 0.001, 0.005, 0.01]`, with covariance inflation lambda fixed to one.

All 28 actual R58 pilot runs attained absolute endpoint gaps below `1e-10`
(largest `9.996924350757372e-11`). The largest endpoint expansion count was
1,186. On this scale, `1e-10` is a meaningful tolerance compared with extrema
of order `1e-7`; it is numerical optimization accuracy, not observational
precision. The largest reconstructed witness ellipsoid excess was
`1.7763568394002505e-14` relative to cutoff `19.6751`, consistent with float64
roundoff. Calibration norm constraints were attained within roundoff.

For the primary `log` model, rho=0 gives outer range
`[-4.4826547258814994e-7, 3.836796305021553e-7]` and feasible range
`[-4.481685080097750e-7, 3.8358028746389197e-7]`. At calibration RMS `.005 mag`
(`rho=0.002302585092994046`), its outer range is
`[-5.221457959496523e-7, 4.4748258822903474e-7]`.

The optional same-law comparison is a **superset bound** from component supports
of the original ellipsoid, not an altered covariance or independent-component
confidence claim. If
\(b_i^{\max}=|h_{b,i}|+\sqrt{c_* C_{ii}}\) and
\(k_A^{\max}=|h_{k,A}|+\sqrt{c_* C_{3+A,3+A}}\), then

\[
|\phi|\le \sum_A k_A^{\max}(b^{\max})^T|E_A|b^{\max}
 +\sqrt5\rho\|b^{\max}\|^2.
\]

For primary rho=0 this loose bound is `3.953953833997154e-6`, whereas the joint
ellipsoid upper/lower endpoints above are about an order of magnitude tighter.

The symmetric analytic test exposes a real computational limitation: an entire
sphere of maximizing directions can require many subdivisions. With cutoff 3,
sigma_beta=.001, sigma_kappa=.01, rho=0, a separate `1e-10` stress run needed
59,111 nodes per endpoint. At rho=.01 the same 100,000-node cap left a
`1.5508435617294582e-9` gap. Both enclosing brackets contained the analytic
extrema; the latter was explicitly `NODE_CAP`. This result is preserved in
`r61_mixed_isotropic_stress.json`. The shorter automated radial tests also
retain their honest cap outcomes and verify enclosure and feasible exact values.

## Provenance and scope

The remote source HEAD was observed as
`fb6ae9f21585e194ef29dabc91d79a529e0ac57e`. A direct read-only `sha256sum`
matched the R58 carrier's recorded SHA256:
`42f6bc5158fdf2f876720db12c44b088bc2db9734887e0d84ae098b234a7e64d`.
Input extraction contains only seven estimates and covariance matrices, in
roundtrippable JSON. The module never edits the repository or raw source files.

Requested runtime settings were gpt-6-astra/xhigh; the observed model and
reasoning effort are UNKNOWN because they were not attested by runtime output.
This is the selected R5 constructive derivation/C5 implementation component
with necessary local validation. It does not mark later theory/coding stages
complete. The fixed-covariance Gaussian law, selected observational response,
and calibration domain remain inherited physical/statistical assumptions.
