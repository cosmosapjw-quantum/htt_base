# HTT / SF10: Union3 chain-to-FITS compression, 2026-10-15

Status: **PARTIAL NUMERICAL SOURCE BINDING; SF10 still BLOCKED_INPUT**. Owner HTT; claim tier CONDITIONAL_DIAGNOSTIC. This analysis does not change the historical scientific HOLD/UNKNOWN decision. Native solver, joint likelihood certification, and physical family identification were not attempted.

## Question and sources

Can the public Union3 22-node Gaussian FITS precision matrix be reconstructed from the public MCMC chain? Does that identity prove the node prior or the original Stan executable and run settings? We test these as separate questions.

- Public release: https://github.com/rubind/union3_release (README, read_and_sample.py, stan_code_simple.txt, stan_code_fixed.txt, paramfile_Union3.txt, simple_Gaussian_check.py).
- Independent prior discussion: A. G. Kim (2024), arXiv:2412.14181, https://arxiv.org/abs/2412.14181 .
- Local predecessor: docs/solver_free_research_20261014/research/UNION_PRIOR.md .
- Current checkout at investigation start: obs/solver-free-dossier-20261014, HEAD 13d8d85fa470d645d008986e8f77d8d0f70fdf54; pre-existing dirty files intentionally left unchanged.

## Definition and reproducible calculation

For the original chain matrix `X` with N=600000 and p=22:
```
m_i = median(X[:, i])
C_ij = sum_k (X_ki - mean(X[:, i])) (X_kj - mean(X[:, j]))/(N-1)
P = inv(C).
```
The public `read_and_sample.py` uses the same median/inverse-covariance operations for its `mu_zbins` array. Public `simple_Gaussian_check.py` identifies the NPZ values as spline perturbations relative to flat LCDM Omega_m=0.3; the released FITS centers instead have physical distance-modulus scale. A candidate coordinate translation is

\[
\mu_{\rm FITS}(z_i) \stackrel{?}{=} m_i + \mu_{\rm flat\,LCDM}(z_i),
\quad
\mu_{\rm flat\,LCDM}=25+5\log_{10}\!\left[
 \frac{c(1+z)}{H_0\,\mathrm{Mpc}}\int_0^z \frac{dz'}{\sqrt{0.3(1+z')^3+0.7}}
\right],
\]
where c=299792.458 km/s and H0=70 km/s/Mpc. This independent 128-point Gauss-Legendre reference is **not the original get_mu routine**; the upstream read_and_sample.py imports get_mu from an external `$UNITY/other_cosmology/cosmo_functions` not available in the release at the checked paths.

## Results, code and tests

Input chain SHA-256: `68418da0b1b061754b3f94603f41acfbce5bac2d5e47b5972b3cb7109579c541`.
Input FITS SHA-256: `ef98b7dde1025ee7134f3242aaea3f1f0ed3f2b29a718458c550a8e4e24d0349`.

Generated machine-readable evidence: `CHAIN_PRODUCT_AUDIT.json`. Script: `scripts/audit_union3_chain_product_20261015.py`; tests: `tests/htt/test_union3_chain_product_20261015.py`.

- Precision relative Frobenius error **3.31326091938e-13**; max absolute precision entry error **1.69893610291e-9**; covariance/precision compression numerically checked.
- Direct raw center max difference **46.2835698193 mag**, because raw chain and release centers are not in the same coordinate basis.
- Flat-LCDM reference-candidate center maximum residual **3.90658335789e-4 mag** and RMS **1.58265975709e-4 mag**; not exact. Do not widen the original 1e-8 mag raw median gate to hide this discrepancy.
- Local command `OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests/htt/test_union3_chain_product_20261015.py tests/htt/test_solver_free_union_prior.py` finished **10 passed in 0.89 s**.
- Mathematica/Wolfram Language verified zero symbolic residual for the scalar Gaussian prior-removal quadratic identity under p>lambda; this is algebra, not generator attribution.

Replay from checkout root:
```bash
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python3 scripts/audit_union3_chain_product_20261015.py \
  --samples workdir/rrss_observational_inputs/union3_release-main/all_samples_union3_cosmo=2.npz \
  --fits workdir/rrss_observational_inputs/union3_release-main/mu_mat_union3_cosmo=2_mu.fits \
  --expected-samples-sha256 68418da0b1b061754b3f94603f41acfbce5bac2d5e47b5972b3cb7109579c541 \
  --expected-fits-sha256 ef98b7dde1025ee7134f3242aaea3f1f0ed3f2b29a718458c550a8e4e24d0349 \
  --out docs/solver_free_research_20261015/union3_source_binding/CHAIN_PRODUCT_AUDIT.json
```

## Prior conflict and stop condition

Kim (arXiv:2412.14181) describes independent standard-normal priors on the 22 perturbation nodes, whereas both public Stan sources contain an empty branch for `cosmo_model==2` or `6`; the visible `mu_zbins ~ normal(0,1)` appears only in their `else` branch. The public paramfile points to `stan_code_simple.txt`, but it is **not authenticated as the exact FITS generating run configuration**. The raw fit-to-FITS coordinate translation involves an unavailable upstream `get_mu` implementation or processing step.

Next minimum scientific requirement: obtain a source-bound executable/run manifest or original generation log for the exact FITS/chain, plus original cosmology reference transform, then compare exact chain parameters, selected prior, reference units, and source hash. Do not promote prior subtraction or a certified Union3 likelihood until that evidence exists.

Scope validation only: no native subagents were available for an independent second-context review. Code remains in the existing dirty checkout, uncommitted and unpushed by this research pass; pre-existing files were not altered.
