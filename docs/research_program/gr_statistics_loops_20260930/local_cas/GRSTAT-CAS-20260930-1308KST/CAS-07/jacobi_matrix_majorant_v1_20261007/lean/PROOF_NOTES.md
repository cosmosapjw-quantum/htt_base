# CAS-07-M04 Lean axis

The frozen contract and admitted-input hashes are checked by `run.py`. The proof uses `Plane = EuclideanSpace ℝ (Fin 2)` and `Op = Plane →L[ℝ] Plane`; `‖·‖` is the induced operator norm. All integrals in the matrix statements are Bochner integrals in `Op`.

`integral_taylor_two` applies the vector-valued fundamental theorem of calculus and integration by parts to `D`, `D1`, and `D2` on `[0,s]`. The supplied within-interval derivatives and continuity suffice, including the endpoints. Substituting `D(0)=0`, `D1(0)=Id`, and `D2(t)=-(R(t) ∘ D(t))` yields `volterra_identity`. The proof neither swaps the matrix factors nor assumes symmetry or commutation.

`scalar_premise` takes the norm of that identity. It uses `ContinuousLinearMap.opNorm_comp_le`, the nonnegative kernel on `0≤t≤s`, and the interval Bochner-integral norm inequality to establish continuity, nonnegativity, and `‖D(s)‖ ≤ s + K∫(s-t)‖D(t)‖dt`. No Frobenius norm enters.

`d_norm` invokes only the accepted, compiled M03 theorem `CAS07M03.scalar_volterra_comparison` with `u(s)=‖D(s)‖`. The module's `.olean` hash is checked; its source and proof were not inspected. `d_minus_si` invokes that same theorem with `w(s)=s+‖D(s)-s Id‖`. The triangle inequality gives `‖D(t)‖≤w(t)`, so the Volterra identity supplies the comparison premise for `w` and hence `‖D(s)-s Id‖≤f_K(s)-s`. This route does not add a fixed-point identity for `f_K` as a premise.

`zero_parameter_control` uses `‖R(t)‖≤0` to prove `R(t)=0` and hence `D(s)=s Id`. `zero_distance_control` proves the exact `s=0` norm equalities. Both endpoints are included in the main domain `s∈[0,L]`.

The result covers only the contracted matrix majorization component. It does not establish determinant positivity, a screen-transport existence theorem, physical applicability, observation, or scientific admission. Global runtime authority was absent during this direct owner-authorized execution; `launch_id` is null and observed model/effort remain unknown.
