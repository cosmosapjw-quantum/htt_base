# H03 conditional replay and exact covariance projection

Owner: `/root/covariance_replay_20261027`. Scope: C2–C8 static scientific replay and an input adapter. Skill context actually read: PhysMath Research Loop 1.3.0, `CODING_LOOP.md` C2–C8, `POLICY_INTEGRATION.md`, and repository `htt-scientific-code-validation` / `htt-local-global-discrimination`. No recursive delegation, raw-catalogue run, native solver, ODE, or source-state mutation.

## Replayed result and repaired interpretation

The input is `H03_SOURCE_TOMOGRAPHY.json` from commit `a55036ad09c53a9215dee3282e425d37cfb95443`, extracted in the parent baseline under `docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/evidence/sources/`. The source supplies four observed working-law dipoles and a joint 36-dimensional covariance. We retain its 12-by-12 dipole block, including every cross-window block. These are ICRS/J2000 Cartesian coordinates in km s^-1 Mpc^-1. The source assumes row-independent scatter while the overlapping windows are correlated; it does not supply an empirical correlated peculiar-velocity, calibration, or selection law.

Let y be the twelve saved coordinates, C their inherited covariance and X one declared mean design. With C=LL^T, whiten b=L^-1 y and W=L^-1 X. Scale nonzero columns of W to unit Euclidean norm before the SVD. For numerical rank r, the statistic is T=||(I-U_r U_r^T)b||^2. No inverse of C or normal equations is used in the implementation. Rank-deficient designs return the fitted mean and residual, but no purported unique physical parameter estimate.

| Mean columns | T | Residual dof | Raw condition | Unit-column condition | Uniform covariance multiplier needed to reach Gaussian 95% reference |
|---|---:|---:|---:|---:|---:|
| Saved bulk R | 79.987013 | 9 | 1.390 | 1.136 | 4.72765 |
| Constant | 94.598317 | 9 | 1.526 | 1.177 | 5.59125 |
| Bulk + constant | 23.396721 | 6 | 384.439 | 5.096 | 1.85812 |
| 1/z-center + constant | 39.460673 | 6 | 113.595 | 4.467 | 3.13389 |
| Bulk + z-center | 22.668786 | 6 | 9.284 | 2.162 | 1.80031 |
| Bulk + constant + z-center | 15.316002 | 3 | 1495.736 | 34.237 | 1.95989 |

All six T values reproduce the external audit's rounded values. Its T12 code was not included in the uploaded archive; `replay_h03.py` now provides the executable path. Gaussian reference tails in the JSON are explicitly conditional on this fixed working covariance and declared design. They are not calibrated cosmological p-values. Since all six designs were inspected, choosing the best tail would additionally require model/scan calibration.

The raw condition number combines columns with different units, so its numerical magnitude is not invariant under a change from km/s to m/s. In particular, the change from 384.4 to 5.10 for bulk+constant is a units effect, not a scientific cure for near-collinearity. Unit-column conditioning and whitened subspace angles are the relevant diagnostics once the metric is fixed.

The whitened principal angles between the saved R and the `1/z_center` proxy are 4.81248, 7.16771 and 8.91852 degrees. Their concatenated design has rank six and scaled condition 25.4134. Thus those particular finite designs are nearly overlapping, not exactly rank degenerate. Moreover, a redshift-center proxy is not the actual source-level observer response. At leading fixed-distance radial-velocity order, with the same row directions N and the same linear extraction A,

    delta y_i = n_i dot (b - v_o),
    delta theta = A N (b - v_o).

The exact same-operator blocks are `[A N, -A N]`, with null vectors `(delta b,delta v_o)=(h,h)` and rank at most three. Replacing one block by a center-based proxy can manufacture apparent rank. Finite-distance magnitude/redshift responses or independent observer information can change this statement, but must be supplied explicitly. The new test verifies the leading-order degeneracy directly.

The bulk-only fit gives 294.950637 km/s toward Galactic (286.562924,-5.499875) degrees. Propagating its saved parameter covariance by the radial delta method gives 19.441892 km/s, not the external report's undocumented 18 km/s. This is a working-law standard deviation, not a physical uncertainty measurement. The Galactic conversion is a fixed ICRS/J2000 rotation; the fitted coordinates and source covariance remain ICRS.

## Exact covariance transport that can run before physical claim admission

For a fixed selected catalogue and extraction operator A, write input perturbations

    delta y = epsilon + V z + B alpha,
    Cov(epsilon)=diag(D), Cov(z)=I, Cov(alpha)=Sigma.

The three source groups are mutually uncorrelated under this factorization. Let K=A B, or supply an equivalent already-projected calibration response K. Then

    C_out = A diag(D) A^T + (A V)(A V)^T + K Sigma K^T.

This is an exact linear covariance pushforward, not an approximation to the supplied covariance model. A may stack all windows, so it retains cross-window covariance automatically. Correlation between the named source groups must instead be represented by a joint latent factor; setting an unknown cross-covariance to zero is not licensed by the formula. Data-dependent selection or estimated weights require either conditioning on the fixed design or repeating the full estimator in mocks.

For N sources, p output coordinates and latent rank r, the implementation streams input-column blocks and stores no N-by-N covariance. Main work is O(p^2 N + p N r), beyond storage of the supplied A and V. This is a route to evaluating a supplied linear-theory/mocked low-rank velocity model at the actual CF4 positions. It does not require solving a Boltzmann hierarchy. It also does not create the missing physical covariance by itself.

When nuisance parameters are fitted, use the actual producer's response A after its nuisance projection. For a fixed WLS design containing science and nuisance columns, A is the science-row block of `(X^T W X)^-1 X^T W` (computed with QR/SVD, not by this displayed inverse). Distinct H03 and R32 estimators must retain their own exact operators. A list of 19 nuisance columns from a different estimator cannot silently be imposed on this nine-component-per-window H03 product.

**Uncertainty ownership:** the old 250 km/s weighting/scatter term is already part of the saved C. Adding a new PV model to that saved C without separating overlapping terms double counts uncertainty. Reconstruct `D` as its declared independent remainder and supply the correlated component once. A diagonal limit check is needed against the old producer. The adapter rejects overlapping declared source labels, but provenance and physical completeness remain caller obligations.

For a certified factor approximation error E with `-epsilon D <= E <= epsilon D` in Loewner order, congruence gives `-epsilon A D A^T <= A E A^T <= epsilon A D A^T`. This supplies a useful projected error bound without requiring an N-dimensional output norm. A merely numerically good low-rank approximation does not establish a physical source law.

## Covariance sensitivity

For a scalar diagnostic C_lambda=lambda C with fixed X, T_lambda=T_1/lambda. The last table column therefore marks where each working Gaussian threshold is crossed. These multipliers are sensitivity parameters; they are not estimates of missing cosmic variance, a license to inflate errors until a null passes, or evidence that the observed discrepancies are physical.

## Executed checks and remaining input

`python test_covariance_bridge.py` passes eight unittest methods, including dense-vs-factored transport, retained cross-window blocks, semidefinite rank, zero covariance, unit rescaling, singular design handling, same-operator boost/bulk degeneracy, and invalid input/ownership cases. The parametrized invalid cases check negative variances, duplicate labels, absent ownership, nonsymmetric/negative calibration covariance, NaNs, bad block size, and invalid GLS covariance. The first attempted pytest invocation failed because pytest is absent in this sandbox; the suite was rewritten using the standard library. This was an execution-environment failure, not a failed scientific check.

`python replay_h03.py --source <H03_SOURCE_TOMOGRAPHY.json> --out <output-dir>` writes the six-fit JSON and two-panel figure. It does not query the network. NumPy and SciPy are required; Matplotlib is needed for the figure. The figure was rendered and visually inspected.

The remaining production input is the exact source-row operator and source identities, a disjoint calibrated measurement/PV/calibration decomposition, and either a stated conditional-on-design target or a selection-aware repeat-estimator ensemble. Supplying a different survey's covariance or a formal PSD factor alone does not satisfy this requirement. The narrow code/archival gap is closed; original H02/H04/H05 and empirical null admission remain open.
