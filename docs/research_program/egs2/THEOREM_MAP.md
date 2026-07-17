# EGS2 Theorem-to-Module Map

All theorems are backed by a runnable gate. `make egs2-gates` (13 gates) covers
the NT2-* set; the T1–T6 candidates reuse already-implemented repo modules and
are exercised by the publishable-next integration runner.

## NT2-* (EGS extension; new theorems)

| Theorem | Statement (conditional) | Module | Gate | Status |
|---|---|---|---|---|
| NT2-A1 ★ | genuine multi-ℓ Fisher–CR floor `σ(F)/F ≥ [Σ(2ℓ+1)/2·f_sky·r_ℓ²]^{−1/2}`, strictly below 0.632; MLE-achievable | `obsstat/egs2_fisher.py` | `test_egs2_fisher_bracket::FisherFloorTests` | provable |
| NT2-A2 | Fisher tail beyond the octupole converges (strictly positive at every finite L); the former sufficiency reading is superseded by the PR-130 gate (`common/nt2_tail_convergence.py`) | `obsstat/egs2_fisher.py:octupole_sufficiency_tail` | `..::test_octupole_information_saturates` | superseded_reading_pr130 |
| NT2-B1 ★ | two-sided bracket `a₂κ/(1+R_EGS) ≤ Σ ≤ C_up a₂` under H3; zero shear-filling excluded | `obsstat/egs2_shear_bracket.py` | `..::TwoSidedBracketTests` | conditional |
| NT2-B2 | `Π(z)` GR-sources `dG_F/dz` via `σ̇=−3Hσ+3H²Π` | `obsstat/egs2_transport.py:sourced_depth_transport` | `test_egs2_transport::SourcedTransportTests` | conditional |
| NT2-B3 | vorticity is a joint blind sector of CMB-T + radial velocity | `obsstat/egs2_transport.py:vorticity_blind_sector` | `test_egs2_transport::BlindSectorTests` | provable |

NT2-A1 is the genuine floor that the report's NT-A3 label asserted but did not
prove (rev-r119 relabelled NT-A3 to a single-estimator sampling dispersion).

## T1–T6 (publishable-next candidates; already-implemented repo modules)

| Cand. | Statement | Repo module(s) | Exercised by |
|---|---|---|---|
| T1 | registered max-scan calibration (`p_global ≥ max p_local`, +1) | `obsstat/lowell_global_calibration.py` | next-runner `quadrupole_filling`/K1 max-scan |
| T2 | rank-exact local/global identifiability | `htt/departure/paper_a_closure.py` | next-runner `response_rank` |
| T3 | Boltzmann collision-gap memory bound (Grönwall; γ≤0 blocks "forgetting") | `bass/kinetic/boltzmann_memory.py` | next-runner `kinetic_and_egs_gates` |
| T4 | visibility-cancellation inverse-source no-go | `bass/kinetic/visibility_rigidity.py` | next-runner `kinetic_and_egs_gates` |
| T5 | almost-EGS promotion gate (needs accel + ∇T + derivative + Weyl bounds) | `bass/geometry/egs_rigidity.py` | next-runner `kinetic_and_egs_gates` |
| T6 | potential-flow curl non-identifiability | `obsstat/affine_flow.py:curl_suppression_ensemble` | next-runner `synthetic_data_mechanics` |

T2/T6 coincide with PAPER-A radial-novortex and the PR07 K6 no-go; T3/T4/T5 are
the existing `bass.kinetic`/`bass.geometry` gates. The publishable-next package's
contribution is the integration runner + claim ledger + the PR08 blocker DAG.
