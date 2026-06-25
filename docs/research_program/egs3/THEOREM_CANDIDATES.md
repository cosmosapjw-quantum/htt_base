# EGS3 Theorem Candidates (three axes)

Each is a strong conditional statement with a runnable gate. `make egs3-gates`
covers A1–A4 + B1–B3; B4 is `make egs3-wolfram`; C1–C4 are the data-axis
discharges (mechanics landed, real-data runs ticketed).

## Axis A — math/statistics (Fisher/information on the variables)

| # | Statement | Module / gate | Status |
|---|---|---|---|
| A1 ★ | identifiable subspace of `g=(Σ²,W²,Ω_tilt,Ω_k)` from {CMB-T, radial-v} is rank 2; `W²,Ω_k` in the joint null | `obsstat/egs3_graded_comparator.py` · `test_egs3_axis_a::A1*` | proved |
| A2 | the NT2-A1 Fisher–CR floor is reparametrization-invariant → one floor bounds all five scalars | `egs2_fisher` · `test_egs3_axis_a::A2*` | proved |
| A3 | `Π` is a calibrated **e-value**: `E=1[x>t]/α`, null mean 1, Markov `P(E≥1/β)≤β`; S4 domination ⇒ conservative | `obsstat/egs3_calibration.py` · `A3*` | proved (MC) |
| A4 | `(a₂,a₃,dipole)` Rao-Blackwell-dominates any raw estimator (`Var_RB ≤ Var_raw`) | `egs3_calibration.py` · `A4*` | proved |

## Axis B — GR/cosmology (1+3 covariant Boltzmann on the variables)

| # | Statement | Module / gate | Status |
|---|---|---|---|
| B1 ★ | semi-native shear→multipole transfer `r_ℓ`; the genuine floor is a **k-profile**, saturating at 0.632 for super-horizon shear and below at finite k | `bass/transfer/shear_quadrupole_seminative.py` · `test_egs3_axis_b::B1*` | proved (sharpens NT2-A1) |
| B2 | depth gap is a **Volterra functional** of `Π` with kernel `exp(−3∫H)`; verified == ODE + Grönwall | `obsstat/egs3_volterra_memory.py` · `B2*` | proved |
| B3 | vorticity re-opens in the **transverse** velocity channel (`n·Ω·m≠0`, rank 3); CMB B-modes named | `obsstat/egs3_vorticity_channels.py` · `B3*` | proved |
| B4 | covariant bracket constants: H3 coefficient `κ/(1+R)`, nondegeneracy `C_up κ(1+R)>1` (κ=4/21,C_up=9) | `wolfram/egs3_bracket_constants.wls` · `make egs3-wolfram` | symbolic PASS |

## Axis C — data interpretation (discharge → publishable)

| # | Statement | Mechanics | Real-data status |
|---|---|---|---|
| C1 ★ | K1 **global** p on public Planck FFP10/NPIPE E2E (max-scan) | `lowell_global_calibration.e2e_maxscan_from_summaries` | ticket `tickets/k1_ffp10_npipe.yaml` |
| C2 | K6/K5 posteriors via Hoffman–Ribak CR + WF/CR forward mocks | `constrained_realizations.curl_posterior`, `bulkflow_mle.hierarchical_coverage_experiment` | ticket `tickets/cf4_wfcr.yaml` |
| C3 | graded-comparator joint pushforward: measured rank-2 sectors + proven 2-sector no-go | `egs3_graded_comparator` on K1/K4/K5/K6 | runnable once C1/C2 land |
| C4 | independent 2MRS cross-reconstruction (no covariance merge) | `../pr07/PR08-005...` | contract |

## The publishable headline (anti-tone-down)

A1 + C3: a **measured** rank-2 graded comparator on real Planck/CF4 data,
**together with** the proven two-sector no-go (W², Ω_k are forever unreachable
from CMB-T + radial velocities) and the B3 named re-opening channels. Strong,
honest, novel — a result, not a hedge.
