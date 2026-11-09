# R48 Cobaya-independent analysis inventory

**Conclusion:** Cobaya is not required for several useful, bounded analyses. It is required only for the current R42 MCMC runner as written. A direct optimizer, deterministic Monte Carlo, physical response kernels and unit tests can proceed separately. "No Cobaya" does not mean "empirically admissible"; source integrity, covariance, frame and selection gates still apply.

## Executable or near-executable paths

| Path | Dependencies | What it can do without Cobaya | Current evidence and limitation |
|---|---|---|---|
| scripts/r46/run_target_posterior_compression.py | NumPy, SciPy | Exact Gaussian target posterior, score-row compression, target-KL and MMSE loss via seeded Monte Carlo | Independently reproduced at 40,000 draws below. Synthetic only. |
| tests/r46/test_target_posterior_compression.py | NumPy, pytest | Four tests for Gaussian KL/MMSE identities, target-score sufficiency, lossy summary and radial/isotropy counterexample | PR #570 historical receipt reports 4 passed; not rerun here. |
| scripts/r42/run_r42_two_layer_benchmark.py | NumPy, SciPy, five source-bound inputs | Direct evaluate_likelihood plus SciPy minimize competitor fits and leave-one-probe-out variants | No Cobaya/GetDist imports. However operators initialize with verify_sha=False and objective sums five probe log-likelihoods. Not currently admissible as observed-data result. |
| tests/r42/test_five_variable_repair.py and family-gate tests | NumPy, pytest, project common modules | Quadrature, support functions, anchor/gauge statuses, numerical geometry and policy gates | Cobaya-free but synthetic fixtures have known blind spots: vector-sum velocity, pseudo-null labelled MC100, explicit count constants. Not rerun here. |
| htt/src/common/relativistic_velocity_closure.py | NumPy and htt common modules | Exact SR composition, first-order residual, Wigner rotation and kinematic STF2 map | Source exists. Bundle and R42 runner bypass exact closure on some zero-boost/legacy paths. |
| R47 Bianchi-I temperature response | analytic formula + NumPy/SciPy quadrature | Geodesic temperature map and spherical harmonic/quadrature oracles without Boltzmann transfer or Cobaya | R47 has solver-free derivation/specification, not a production module. Suitable for R48-T2. |

## R46 numerical reproduction

The R46 source blob is f519e2cab14305c298fcd004583f15e0c0abdf06. I independently reproduced its joint17 calculation, same seed mapping and 40,000 prior-predictive draws, in Python 3.13.5 / NumPy 2.3.5 / SciPy 1.17.0. This is numerical reproduction of the published algorithm, not a local execution of the repository module.

| Metric | Target-aligned rank-2 summary | One score direction dropped |
|---|---:|---:|
| Expected target posterior KL (nats) | \(1.11\times10^{-16}\) | \(0.68059\pm0.00261\) |
| Direct target MMSE risk gap | \(8.49\times10^{-31}\) | \(1.14656\pm0.00810\) |
| Target posterior covariance trace | 0.938558 | 2.093452 |
| Full latent-posterior information loss (nats) | 6.62040 | 7.52623 |

The rank-2 row-space summary preserves the declared 2-component target posterior to floating-point precision while discarding substantial latent-state information (6.62 nats). Dropping one of the two target score directions makes the target posterior materially lossy. This illustrates target-specific compression, not empirical sufficiency of a physical HTT carrier.

## Immediate safe commands on the local checkout

After verifying the branch and a clean or explicitly preserved worktree:

    export PYTHONPATH=htt/src:htt/htt
    python scripts/r46/run_target_posterior_compression.py --seed 20261109 --replications 40000 --output work/r48/R46_MOCK_REPRO.json
    pytest -q tests/r46
    pytest -q tests/r42/test_five_variable_repair.py tests/r42/test_family_identification_gate_repair.py

Do NOT run scripts/r42/run_r42_two_layer_benchmark.py as an observed-data result until source SHA verification is enabled, fixed response defaults are replaced by source-bound operators, nuisance/cross-probe covariance is handled, and input manifests pass admission. Do not treat R42 MCMC receipt fallback as a valid Cobaya execution path.

## Recommended next work

1. Complete local R48-T1 runtime replay on the exact remote head.
2. Run R48-T2 as a solver-free map/harmonic oracle, reusing WU-009 P18 and separating it from WU-010/011 local-observer Lorentz response.
3. Carry WU-011 Task-5A findings into the exact local-observer operator: metric whitening, physical monopole/a00 typing, complete ell=6 block and rotation-complete finite-difference columns.
4. Keep Cobaya out of the critical path until each direct likelihood, source covariance and injection/recovery gate is independently valid.