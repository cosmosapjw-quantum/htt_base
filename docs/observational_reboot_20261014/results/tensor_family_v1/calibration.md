# Retrospective temperature tensor family; conditional delivered-simulation ranks

Fixed B=240; declaration `retrospective-STF-family8-pilot-coefficients-v1`.

| Feature | Tail | Signed value | p rank | Joint-max adjusted p | q interval (unadjusted) |
|---|---|---:|---:|---:|---|
| C2 | two-sided | -1.16137 | 0.112033 | 0.746888 | [0.071998, 0.154695] |
| C3 | two-sided | -0.627411 | 0.53527 | 0.991701 | [0.468058, 0.597775] |
| C4 | two-sided | -0.513247 | 0.568465 | 0.995851 | [0.501394, 0.630272] |
| C5 | two-sided | 1.00528 | 0.26971 | 0.871369 | [0.211833, 0.327365] |
| quadrupole_shape | two-sided | -0.0524634 | 0.975104 | 1 | [0.946383, 0.990771] |
| octupole_concentration | upper | -0.402342 | 0.639004 | 1 | [0.573194, 0.698363] |
| QO_contraction | upper | 2.43896 | 0.00414938 | 0.0705394 | [0, 0.0152528] |
| chirality | two-sided | -0.0100652 | 0.987552 | 1 | [0.963906, 0.997415] |

Global joint-null p_rank=0.0705394 (16 >= exceedances, 0 ties).
Global q interval=[0.038582841144730616, 0.10600647593045186] at confidence 0.95.

Conditional exploratory rank for this eight-feature family only; full historical selection and physical sky exchangeability remain unverified.
Marginal Clopper-Pearson interval for IID null exceedance probability q conditional on fixed observed threshold and training. Not an interval for realized p_rank; not simultaneous across features.
Global max-score test and single-step adjusted ranks control error under the complete joint null. Strong FWER under partial alternatives needs extra conditions, not asserted.
Observed feature calibration; no inferred shear, global tilt, Bianchi family detection, posterior or evidence.

Provenance attestations are validated mechanically and have not been independently verified.
