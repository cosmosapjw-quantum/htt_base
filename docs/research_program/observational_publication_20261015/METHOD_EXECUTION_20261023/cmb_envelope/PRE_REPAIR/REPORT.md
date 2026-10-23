# R24-CMB-ENVELOPE: processed-carrier common-contaminant sensitivity

Owner: `obsstat`. Status: `CONDITIONAL`, C0 diagnostic. This uses the independently reviewed corrected R24-CMB-ORBIT `RESULT.json` with SHA-256 `107c0ab6af308213c91cb1c38477242864fc24c6e5e0739fe6fb93b9c195bdbb`. It concerns one Planck PR3 observed sky and separately processed E pseudoalm views of delivered QU. The hash-pinned primary L32 view is the primary experiment; cached zero-, 20-, and 30-degree windows are distinct processing experiments on that same sky. No native solver or transfer output enters this calculation.

## Fixed norm and conditional radius

For every full 12-coordinate carrier, use the same invariant STF norm

`||v|| = sqrt(||T2||_F²/q0² + ||T3||_F²/o0²)`, with `q0=o0=1e-5 K_CMB`.

The canonical real harmonic coordinates are converted to an orthonormal representation of that norm with factors `sqrt(15/(8π))/q0` on the five quadrupole coordinates and `sqrt(35/(8π))/o0` on the seven octupole coordinates. Reconstructing every stored STF tensor independently gives norm agreement below `1e-12`. No raw harmonic norm is mixed into the radii. Each operator's radius is `r=rho*||v_full||` for `rho={0,.05,.1,.25,.5,1}`. The full reference norm, each pair's two radii, and every result appear in `RESULT.json`.

For an orbit interval `[L,U]` from the corrected result, the certified outer interval is `[max(0,L-r1-r2), U+r1+r2]`. The lower uses the already certified R24 lower; the upper uses its feasible proper-rotation witness and the T3 Lipschitz inequality. This is a conservative *pairwise* envelope. For splits under the same processing operator, the contaminant is one shared processed `h`; choosing an independent `h` for each split would overstate joint sharpness. Across primary/cached/window operators, a source-to-operator nuisance response has not been supplied. Those rows are separate scenario envelopes, not one joint physical confidence set.

At primary L32, the invariant full norm is `0.04482329297137265`. The four split-vs-full lower bounds at zero radius are `0.01644129` (HM1), `0.01631026` (HM2), `0.01265095` (OE1), and `0.01801714` (OE2). Their lower-bound zero thresholds in `rho` are respectively `0.183401`, `0.181940`, `0.141120`, and `0.200980`. All four stay positive at `rho=.10`; all four are zero at `.25`. All 15 primary-versus-cached zero-window lower bounds are zero by `.05`. For the 30 cached window comparisons, 9 are zero at `.10`, 27 at `.25`, and all 30 at `.50`. The figure shows the primary L32 widening. These are loss-of-discrimination thresholds of this particular lower certificate, not proof that the true orbit distances vanish.

`RESULT.json` also recomputes support at 24 signed coordinate functionals of the orthonormal invariant representation. Each has dual norm one, so a radius `r` changes its finite-set support by at most `±r` in the same dimensionless invariant units. The five processed products within an operator form one finite set; its support summarizes the convex hull at these directions. It cannot recover disconnected, chiral, or other nonconvex processing strata, nor certify all unsearched directions. Separate support-direction endpoints generally require different `h` and are not simultaneously sharp.

## Common-mode obstruction and covariance

Write each observed split as `d_s=g+f_common+f_s+n_s`. For any tensor `h`, the transformation `g→g+h`, `f_common→f_common−h` leaves *every* `d_s` unchanged. The executable witness uses `||h||=1000||v_full||`, with maximum observed residual `1.10e-15` and exactly zero split-difference residual; scaling `h` remains unrestricted. A split contrast removes both `g` and `f_common`, so small split differences cannot set a finite bound on common foreground or identify a physical source.

Cross-split expected power includes `tr(N12)`. Its value is `UNKNOWN` here. A two-coordinate counterexample with correlated noises `n1=n2=(1,2)` and zero common field gives cross power 5, while a zero-cross-noise assumption would incorrectly predict zero. There is no matched total-field law, calibrated p-value, numerical Berger–Boos p-value, physical `Pi`, or physical attribution. A valid law would need the matched processed total-field/noise joint distribution, including split cross-noise, and a justified common-foreground nuisance set. A physical shared-`h` comparison across products additionally needs the source-to-each-operator response and frequency/template constraint with the same mask, beam, and windows. No available cached product here supplies those bindings.

| Claim | Owner | Status | Evidence | Ceiling |
| --- | --- | --- | --- | --- |
| Fixed-norm radius and pairwise widening | obsstat | CONDITIONAL | code, result, focused tests, T3 | processed-map sensitivity only |
| Finite directional support | obsstat | DIAGNOSTIC_ONLY | saved carriers, exact finite maxima | convex-hull summary at 24 directions |
| Unbounded common-mode ambiguity | obsstat | DERIVED | T5 kernel and executable witness | no physical source attribution |
| Calibrated total-field inference | htt | HOLD | matched law absent | no p, physical Pi, or family claim |

The original 17/42 and 18/42 obligations, R9 state, and ultra accounting are unchanged. No original acceptance is promoted. Execute from the repository root with `.venv/bin/python docs/research_program/observational_publication_20261015/METHOD_EXECUTION_20261023/cmb_envelope/envelope.py` and `.venv/bin/python -m pytest -q docs/research_program/observational_publication_20261015/METHOD_EXECUTION_20261023/cmb_envelope/test_envelope.py`.
