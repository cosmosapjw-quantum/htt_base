# Union3 assumed node-prior sensitivity

Full removal of the **assumed** independent one-magnitude node prior shifts the conditional flat-LCDM distance fit only slightly: Ωm by +0.0613 baseline SD and H₀rd by −0.0223 SD. The common offset M shifts by −0.2742 SD and its SD increases by 9.83%. This quantifies the blocker under the specified prior assumption; it does not certify a likelihood correction.

Owner: HTT. Claim tier: CONDITIONAL_DIAGNOSTIC. Artifact mode: ASSUMED_NODE_PRIOR_SENSITIVITY. Allowed use: quantify sensitivity to the declared node prior. Transfer source: none, distance only. Null status: not evaluated. Covariance status: exact frozen release precision with assumed P−λI removal, ρ=0. Forbidden uses: certified Union3 likelihood correction, physical/native posterior promotion, Bianchi family identification, or cross-scenario model evidence.

## Why likelihood certification remains blocked

[Alex G. Kim (2024), arXiv:2412.14181v1](https://arxiv.org/html/2412.14181v1), sections II/V and equation 13, describes the released Gaussian as a node posterior using independent standard-normal perturbation priors, and prescribes dividing that posterior by its prior for a joint likelihood. The public [Union3 source](https://github.com/rubind/union3_release/blob/a141f8f6f72c46b653e4d324f2ecf9c5684bf15a/stan_code_fixed.txt), commit `a141f8f6f72c46b653e4d324f2ecf9c5684bf15a` (2024-09-30), instead has an empty prior branch for `cosmo_model` 2 and 6. The `mu_zbins ~ normal(0,1)` statement appears only in the `else` branch (lines 427–430).

The public source is not proven to be the generator of the exact frozen FITS matrix. Therefore neither removing the assumed prior nor treating it as absent can be certified from these materials. The ambiguity is in release generation provenance, and a small numerical shift does not resolve it. The Gaussian approximation and approximate spline embedding remain additional qualifications.

The public-file SHA256 is `ed156b739f7bffd208f1dec48ddbe7039b1c88c8ac85ee3703195ae4e5f23c2d`. The originally materialized local text had an extra terminal newline and SHA256 `a9df56f6cf620e9605cee90ecab27a8ce5ee880dda033d902f220b4500963c39`; the parent normalized it to exact provider bytes. This transport-format difference is not a scientific source change.

## Declared experiment and exact identity

Let the released node Gaussian be `q₀(x)=N(x;μ,P⁻¹)`. Assume `π(x)=N(x;μref,I)` where

\[
\mu_{\rm ref}(z)=5\log_{10}[(1+z)\,r(0.3,z)]+5\log_{10}(c/70)+25.
\]

For λ∈{0,½,1}, the conditional scenario is `qλ(x) ∝ q₀(x)/π(x)^λ`, with

\[
P_\lambda=P-\lambda I,\qquad
\mu_\lambda=P_\lambda^{-1}(P\mu-\lambda\mu_{\rm ref}).
\]

The implementation solves the centered equivalent `μλ=μref+(P−λI)⁻¹P(μ−μref)` to reduce cancellation. Define δ=μ−μref and δλ=μλ−μref. Expanding the quadratic establishes

\[
\log q_0(x)-\lambda\log\pi(x)=\log q_\lambda(x)+C_\lambda,
\]

\[
C_\lambda=-\tfrac12\delta^TP\delta
+\tfrac12\delta_\lambda^TP_\lambda\delta_\lambda
+\tfrac12\log\frac{\det P}{\det P_\lambda}
+\tfrac{22\lambda}{2}\log(2\pi).
\]

The smallest eigenvalue of P is 5.1211250555; that of P−I is 4.1211250555, so all three scenarios are proper Gaussians. An independent `scipy.stats.multivariate_normal.logpdf` calculation checks the identity at 128 random nodes and four additional points. Maximum absolute error is 2.25×10⁻¹², below the 10⁻⁸ gate.

All scenarios use the original `fit_reboot_joint.fit_grid` and `table`, identical DESI qiso data and variance, ρ=0, Ωm∼U(.01,.99), H₀rd∼U(5000,20000) km/s, and M∼N(43,5) mag. The proper M integral is analytic and appears once. Cosmological distances use fixed 96-point Gauss-Legendre quadrature; no ODE or Bianchi solver is implemented or called. Jacobians are not introduced by evaluating the assumed likelihood directly at predicted node values with the stated parameter priors.

## Results

| Assumed removal λ | Ωm mean ± SD | H₀rd mean ± SD (km/s) | M mean ± SD (mag) | Joint grid TV from λ=0 |
|---:|---:|---:|---:|---:|
| 0 | 0.3574565 ± 0.0270843 | 9974.6253 ± 204.1810 | 43.0888971 ± 0.0886680 | 0 |
| 0.5 | 0.3582116 ± 0.0271844 | 9972.5559 ± 204.2240 | 43.0779427 ± 0.0926969 | 0.0111152 |
| 1 | 0.3591168 ± 0.0273019 | 9970.0772 ± 204.2732 | 43.0645811 ± 0.0973807 | 0.0243559 |

The maximum absolute node-location change at λ=1 is 0.0724222 mag. The marginal plot shows the three scenarios at the same quadrature nodes. Its curves use node mass divided by the Gauss-Legendre integration weight, so the displayed ordinate is a marginal density.

The 128/256 comparisons pass the existing 10⁻³ criterion for every mean shift divided by posterior SD and every relative SD change. The largest metric is 1.40×10⁻¹⁰. Absolute changes of normalized scenario log integrals are below 8.60×10⁻¹³. These scenario integrals are not original-data evidences; their changes are not Bayes factors. Boundary mass is negligible in this conditional experiment. Catalogue coverage, cross-probe covariance measurement, CF4, and CMB combination are not established by it.

## Reproduction and readiness

Frozen primary checkout HEAD: `89621f4c9a6f63449813587a0fadeb13287f8e10`. Fitter SHA256: `26cfce541d47fce302c609ca3bdf2b3032c61c1d06aabb99232514ef70638138`. Union3 FITS SHA256: `ef98b7dde1025ee7134f3242aaea3f1f0ed3f2b29a718458c550a8e4e24d0349`. DESI JSON SHA256: `c9382695890142c1b0917429f9606cd845fd36b5e3950b34d6bb336cff4a7465`.

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 /usr/bin/python3 scripts/run_solver_free_union_prior.py \
  --repo-root "$PWD" --outdir /tmp/htt-union-prior-replay
PYTHONPATH=scripts /usr/bin/python3 -m pytest -q tests/htt/test_solver_free_union_prior.py
```

The delivered script can be placed at another path; it imports the fitter from `--repo-root/scripts/fit_reboot_joint.py`. It requires the pinned upstream commit to remain an ancestor and seals the fitter and input hashes. Descendant commits containing this delivery can replay unchanged scientific sources; changing a sealed scientific input requires an explicit new binding. The native run used `/usr/bin/python3` 3.12.3, NumPy 2.4.2, SciPy 1.17.0, Astropy 7.2.0, and Matplotlib 3.10.8. Five narrow tests pass, including rejection of an improper precision after prior removal. Artifact bytes and script hash were checked against the remote result. The 2D plot was visually inspected. A Matplotlib warning about unavailable Axes3D was emitted; computation and 2D rendering succeeded.

An initial strict source check failed before computation because the local fitter text had one extra terminal newline. Exact function-source hashes for input loading, radial integration, table, covariance, grid fitting, moments, and convergence matched between local and remote. The parent identified and repaired the formatting discrepancy. The worker ran against the exact remote fitter. The primary checkout remained clean before and after the worker run. All remote writes were disposable `/tmp/htt-r2-union-*` files; the worker did not mutate the repository.

Requested worker: gpt-6.1-sol/high. Observed worker runtime: UNKNOWN. No runtime attestation is inferred from the requested setting.

Integration is ready as a conditional sensitivity artifact. The remaining admission gate is an authoritative binding of the exact FITS bytes to their actual generator commit, parameters, node prior and reference definition, nuisance treatment, and Gaussian compression method. This worker does not promote the physical posterior, alter current inference code, or impose an expensive raw-chain rerun as a substitute for the missing binding.
