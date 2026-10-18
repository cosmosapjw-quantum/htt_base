# Source-bound calibration-envelope extension for H02/P3 (candidate)

Date 2026-10-18. Owner: publications worker. Baseline: htt_base@967ef7c8f0b132ecaaba343045d333d4ebf299c1. Scope: R4 candidate and stage-local algebra check; no native physical solver, ODE, canonical DAG change or astronomical inference. This is elementary robust inference, not a novelty claim.

## Question that can be answered before global calibration is identified

H02 already proves the selected-source gauge X=ΣD_mX. Rather than turning an arbitrary Gaussian calibration prior into a physical result, ask:

**How much angular calibration variation is minimally required to reconcile the method-specific measurements with one common angular coefficient? For a declared calibration allowance, what common coefficient values remain compatible?**

The calculation uses the method contrasts themselves, so it can quantify source incompatibility even while the unanchored global coefficient remains unidentified. It must be described as a test of the joint working law, not evidence that calibration is the actual cause.

## Scalar contrast construction

Freeze one angular contrast c and identical sky/depth estimand. Fit each method's coefficient vector bvec_m under the same source law and define b_m=cᵀbvec_m, in magnitudes. Different method footprints require explicit window matching, otherwise the differences may be different physical estimands.

For M methods use

    b_m = theta + gamma_m + epsilon_m,
    |gamma_m| <= r_m,
    |epsilon_m| <= q_m,   simultaneously for every m.

The r_m are externally justified calibration bounds or declared sensitivity assumptions. The q_m are a simultaneous uncertainty event, derived from the *joint* covariance or source-matched mocks. Neither is supplied by source geometry alone.

Let

    L = max_m(b_m-r_m-q_m),
    U = min_m(b_m+r_m+q_m).

Then the feasible common-contrast set is [L,U] if L<=U and empty otherwise. Under independent box freedoms for the nuisance values this set is sharp. Necessity follows from each row bound. For sufficiency, for each theta in the intersection, d_m=b_m−theta lies in [−r_m−q_m,r_m+q_m]; choose gamma_m=clip(d_m,−r_m,r_m), epsilon_m=d_m−gamma_m. This gives a simultaneous witness. This construction does **not** imply independent statistical errors.

If cross-method physical restrictions couple gamma or epsilon, this box calculation is only an outer set. Preserve the common witness/coupling when solving the more constrained model; do not call the coordinatewise interval sharp for a general vector/ellipsoid problem.

## Calibration budget threshold

If all r_m=R, define

    A = max_m(b_m-q_m), B = min_m(b_m+q_m).
    R_min = max(0,(A-B)/2).
    I(R) = [A-R,B+R] when R>=R_min.

R_min is the minimum common scalar calibration allowance compatible with the stated error bounds and common-theta model. For Gaussian marginal errors with valid V_mm, one conservative simultaneous choice is q_m=Phi^−1(1−alpha/(2M))*sqrt(V_mm). Bonferroni coverage does not require cross-method independence, but it still requires those marginal distributions to be correct. A joint mock quantile generally uses the covariance more efficiently.

If the simultaneous error event has probability >=1−alpha and the true calibration obeys r_m, the feasible set contains true theta with probability >=1−alpha. No coverage claim follows when either assumption is unverified.

An empty set rejects the conjunction of common estimand, stated calibration bounds and uncertainty law. It does not determine which assumption fails and is not a rejection of FLRW.

## Manufactured checked example

Four contrasts b=(.010,.030,−.010,.020) mag and q=(.005,.005,.005,.005) mag give A=.025, B=−.005 and R_min=.015 mag. At R=.010 the set is empty; at R=.015 it is the singleton theta=.010; at R=.020 it is [.005,.015] mag. Python evaluated the endpoints and reconstructed every nuisance witness with errors within q (floating tolerance 1e−14). These are manufactured values, not CF4 fits.

## Minimal implementation contract for the parent

1. Reuse the actual selected CF4 source and method-specific coefficient estimates; carry exact IDs, frame, window and angular contrast.
2. Read actual cross-method covariance if available; otherwise label diagonal/supplied-error runs CONDITIONAL_WORKING_LAW and plot sensitivity in q.
3. Compute R_min and I(R) across a fixed grid. Include unbounded-calibration limit, where theta remains unrestricted.
4. Repeat under predeclared matched-depth/matched-sky estimands; quantify changes due to the window rather than rebranding them as calibration.
5. Produce one plot of interval endpoints versus R and a table of method differences. A physical H0 interpretation additionally needs TF zero-point calibration assumptions: h(n)/hbar=10^[a0(n)/5] in Boubel's convention. A covariant H(n) interpretation requires the optical/frame law.
6. Accept the output as real-source sensitivity only after the actual source/covariance run. It does not close H02, H04 or S04 by itself.

Literature context: Manski missing-data partial identification; Giacomini–Kitagawa robust posterior identified sets; Boubel JCAP03(2025)066 Eqs.(3.4–3.6); Stiskalek et al. MNRAS546 staf2048 uses the data-template/physical-flow distinction. The contribution to test is the calibrated CF4 method/window application, not this interval algebra.

