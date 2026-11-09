# R45: finite-model posterior information loss

**2026-11-09 | Derived standard information-theory identity; numerically checked synthetic Gaussian experiments**

R45 extends the R44 common-statistic Bayes-factor result to a finite model index. It is not a novelty claim: the core identity follows from conditional mutual information and its chain rule. The contribution here is to make model-index posterior loss, within-model parameter posterior loss, and their numerical diagnostics explicit for the HTT compression question.

## Theorem

Let M take values 1,...,K with pi_m>0, Y|M=m~P_m, and S=T(Y) for one common measurable deterministic map T. Define Pbar=sum_m pi_m P_m, P_m^S=P_m o T^{-1}, and Pbar^S=Pbar o T^{-1}. For regular conditional posterior versions r_m(Y)=P(M=m|Y) and q_m(S)=P(M=m|S),

[
L_M(T):=E_{Pbar} KL(r(Y)||q(T(Y)))=I(M;Y|S)=I(M;Y)-I(M;S).
]

Equivalently,

[
L_M(T)=\sum_m pi_m\{KL(P_m||Pbar)-KL(P_m^S||Pbar^S)\}.
]

For finite K and positive prior, P_m is dominated by Pbar and dP_m/dPbar<=1/pi_m, so these KL terms are finite. Pairwise mutual absolute continuity is not required. Standard-Borel spaces suffice for the conditional probability kernels used in the proof.

## Proof and zero-loss criterion

Since S is a function of Y, P(M|Y,S)=P(M|Y), hence the conditional-KL representation gives E KL(P(M|Y)||P(M|S))=I(M;Y|S). The chain rule and I(M;Y,S)=I(M;Y) yield the first identity. The mixture-KL representation is the standard expression for mutual information with a finite discrete index.

L_M=0 iff M is conditionally independent of Y given S, equivalently p(M|Y)=p(M|S) almost surely. Thus all posterior odds and pairwise Bayes factors on the active prior support are preserved. In a dominated notation, this is equivalent to each dP_m/dPbar having a sigma(S)-measurable version. If some pi_m=0, no conclusion is available about that excluded model.

For TV(P,Q)=0.5||p-q||_1, Pinsker plus Jensen yields

[
E\,TV(p(M|Y),p(M|S))\le\sqrt{L_M/2}.
]

For optimal 0-1 model classification, R_Y=1-E max_m p(m|Y), R_S=1-E max_m p(m|S). Since p(M|S)=E[p(M|Y)|S] and max is convex,

[
0\le R_S-R_Y\le E\,TV(p(M|Y),p(M|S))\le\sqrt{L_M/2}.
]

This is a population Bayes-risk statement; it does not imply that finite-sample trained, regularized, or compute-limited classifiers cannot benefit from preprocessing.

## Model-index versus continuous-parameter information

For a joint latent variable (M,Theta_M), the chain rule gives

[
I((M,\Theta_M);Y|S)=I(M;Y|S)+I(\Theta_M;Y|M,S).
]

The two terms are distinct. A statistic may preserve the model posterior while losing within-model parameter information, or preserve each within-model parameter posterior while losing model-selection information. R45 includes both directions as explicit Gaussian constructions.

## Gaussian score results

For finite models P_m=N(mu_m,Sigma) with common known Sigma, the K-1 log-likelihood ratios relative to a reference model are affine functions of the discriminant scores (mu_m-mu_K)^T Sigma^{-1}Y. These scores therefore preserve the full model-index posterior exactly. A projection that drops discriminant directions does not.

With model-dependent Sigma_m, log-likelihood ratios generally contain a quadratic term -0.5 Y^T(Sigma_m^{-1}-Sigma_K^{-1})Y. A mean-only score can then lose model information. The K-1 exact log-likelihood-ratio vector remains sufficient for the finite model index, though it may be as expensive to compute as the raw likelihoods.

## Synthetic experiments

Seed 20261109; 60,000 replications per experiment; natural logarithms; TV uses one-half L1.

| Experiment | Summary | E posterior KL (nats) | E posterior TV |
|---|---|---:|---:|
| K=4, common covariance | exact K-1 discriminant scores | 2.41e-16 | 3.63e-16 |
| K=4, common covariance | one-score projection | 0.143764 | 0.208698 |
| K=3, model-dependent covariance | mean-only projection | 0.077642 | 0.133952 |
| K=3, model-dependent covariance | exact log-LR vector | 1.88e-16 | 2.63e-16 |
| sign-reflected means | norm only | 0.268733 | 0.303071 |
| zero-mean isotropic scale models | squared norm | 1.57e-16 | 1.91e-16 |

For the lossy one-score projection, direct posterior-KL and the Monte Carlo mutual-information difference were 0.143764 and 0.143522 nats, respectively; their discrepancy (0.000242) is within the combined Monte Carlo standard error (0.000810). The model-dependent covariance mean-only case showed 0.077642 versus 0.077419 nats, with discrepancy 0.000223. The exact summaries are zero up to floating-point roundoff.

Parameter-posterior separation:
- Case A: model-index information loss 0; within-model parameter loss 0.347661 +/- 0.001443 nats (MCSE), agreeing with analytic 0.5 log 2 = 0.346574.
- Case B: within-model parameter loss 0; model-index information loss 0.290260 nats.

Wolfram Language checks returned Log[2]/2 for Case A and confirmed that unequal-variance Gaussian log-likelihood ratios retain a quadratic y^2 term, while the common-variance ratio is linear in y.

## Literature context

The result is standard information theory, Blackwell comparison, and statistical sufficiency. The ABC model-choice literature emphasizes that within-model sufficiency need not imply cross-model sufficiency. Heavens et al. (2023) study joint model-wise score/MOPED compression in Gaussian linear settings; their construction should not be read as a universal guarantee for arbitrary covariance or selection models.

- Blackwell, *Equivalent Comparisons of Experiments*, Ann. Math. Stat. 24 (1953), 265-272. https://doi.org/10.1214/aoms/1177729032
- Robert et al., *Lack of confidence in approximate Bayesian computation model choice*, PNAS 108 (2011). https://doi.org/10.1073/pnas.1102900108
- Marin et al., *Relevant Statistics for Bayesian Model Choice*, JRSS B 76 (2014), 833-859. https://doi.org/10.1111/rssb.12056
- Barnes et al., *Considerate Approaches to Achieving Sufficiency for ABC model selection* (2011). https://arxiv.org/abs/1106.6281
- Heavens et al., *Extreme data compression for Bayesian model comparison*, JCAP 11 (2023) 048. https://arxiv.org/abs/2306.15998 ; https://doi.org/10.1088/1475-7516/2023/11/048

## Verification and scope

Local Python environment: Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, pytest 9.0.2. `python -m compileall -q scripts/r45 tests/r45` passed; `pytest -q tests/r45`: 5 passed; same-seed JSON replay was byte-identical; JSON/YAML strict parsing passed. The exact driver and test Git blob IDs were subsequently read back from the repository and match their local Git blob identities.

All results are synthetic statistical experiments. No Planck/Gaia/Quaia/NVSS/Pantheon/DESI observations, physical Bianchi transfer, Cobaya production sampling, or end-to-end observational calibration were run. These mocks do not establish cosmological detection or Bianchi-family identification. The HTT five-variable object T=(x,Q,Pi,F,G_F) remains a joint posterior/compatibility push-forward, not a product of independent likelihood factors.
