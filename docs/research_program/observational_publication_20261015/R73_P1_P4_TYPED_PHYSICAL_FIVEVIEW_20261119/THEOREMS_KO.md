# R73 · P1–P4 물리적 5뷰 도구: x → Q, Π, F, G_F의 계산 가능한 정리

Date 2026-11-19 KST. Repo cosmosapjw-quantum/htt_base, branch research/r69-observable-physics-bridges-20261118; pinned input HEAD 06886d0d4038cabe75d2270c69c19b89722f698a.
Scope: a NEW bounded cross-paper **theory-and-validation research package**, not a new P5/R74 paper loop, and no unsolicited ten-stage gate ceremony. All original P1–P6 science/42 DAG nodes unchanged. Publish real bounded substantive checkpoints to existing research branch as owner requested, no other untracked/dirty files. Native subagent unavailable (NOT_RUN), independent source math + Wolfram/SymPy checks recorded separately.

## 0. Semantic contract and exact sources

Reuse R68 THEOREM/typed fiveview \`R68_FIVEVIEW_GEOMETRIC_RECONSTRUCTION_20261118/THEORY_AND_PROOFS_KO.md\` and R69 \`R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118/X_TO_FIVEVIEW_PHYSICAL_RESPONSE_KO.md\`, their actual data atlas and source corrections. Reuse R69_P1_FIVEVIEW_PHYSICS_LOOP2 for signed STF sky shape; R70-P2 for collisionless moment nonclosure; R71-P3 for source-computed H_D and a 39/39 rank with weak nonlinear domain certification; R72-P4 for observer boost/selected finite-bin kappa and same-source NVSS covariance.
Here \(\mathcal E=(P(y\mid\theta,\psi),{\cal T}_{GR/kinetic/optical},{\cal O}_{source},C,{\cal K},\mu)\) is a *typed experiment*. \(x\) is a signed field or vector together with units/frame/source/covariance, **not necessarily a five-component vector**. Its four dependent views:
\(Q_{\mathcal K}(x)=\inf\{t>0:x\in t\mathcal K\}\) for a convex physical body (or \`Q_stat\` for a named noise reference),
\(\Pi_{\mathcal L}=\Pr_{\mathcal L}[T(Y)\ge T(y_{\mathrm{obs}})]\) for a named experiment-matched null,
\(F_{\mu,\mathcal K}(E_x)=\mu(E_x\cap\mathcal K)/\mu(\mathcal K)\) for a specified **finite measure**,
\(G_F=F_j-F_i\) only for comparable physically transported source measure/event and joint law.
A different, intentionally named \(F_{\mathcal E}(\mathcal K):=\mu(\mathcal E\cap\mathcal K)/\mu(\mathcal E)\) uses *confidence-region* volume normalization and is NOT the same F as \(F_{\mu,\mathcal K}(E)\). It is still a valid typed occupancy if explicitly registered as such, but no Bayesian posterior/physical truth probability follows. Full-sky signed quadrupole positive-lobe fraction \(F_{\Omega,2}\) and orbit shape \(\chi\) are auxiliary geometric diagnostics, not unregistered independent stochastic laws. Tensor path \(G_x\) is not \(G_F\).

P1 authoritative source: P1_SELECTED_TENSOR_LAW_20261024/SCIENTIFIC_SCOPE.md (actual selected 274 rows, 15D full signed carrier and four fixed covariance shapes). Physical \(\sigma/H\) is NOT selected-data apparent STF. R62_ANISOTROPY_CLASSIFICATION_20261117/RESULTS/CLASSIFICATION/log__J2_coefficients.json is a separate 15D CF4 apparent STF coefficient+covariance for **demonstration**, not the original P1 274-row fit.
P2 source: R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/RESULTS/OBSERVABLES.json, finite-band actual PR3/PR4 signed \(\pi_\gamma/\rho_\gamma\), no same-frame photon flux or Commander full T null.
P3 source: R64_DIRECTIONAL_HUBBLE_20261117/RESULTS/AUGMENTED/{AUGMENTED_CARRIERS.npz,AUGMENTED_RESULT.json}; fixed \`mono_method+24\` same-source 68D working Gaussian (35,970 selected CF4 groups), 3 models J1/J2/J3, with Q=distance derivative D>0 and 54 ICRS evaluation directions; H_D is not \(\mathcal H\).
P4 source: R65_DIPOLE_ANOMALY_20261117/RESULTS/INTERPRETATION_SUMMARY.json and R72_P4_LORENTZ_COUNT_TILT_20261119/RESULTS.json, same-provider peak/integrated transverse signed count contrast with shared source covariance (241,892 common components); R63 compensated-history low power separate. Radio log-intensity \(\widehat d\) is NOT the full 3D physical \(\boldsymbol\beta\).
Most important primary prior art: Heinesen arXiv:2010.06534, Maartens et al. arXiv:2312.09875, Takeuchi arXiv:2602.07389v2. Existing R68 Gaussian nuisance profile, radiation moment PSD and STF orbit theorem are established math, NOT new probability/SR firsts.

## 1. Universal theorem: identifiable physical view and physical-score firewall

For a full source model \(y=J\theta+N\gamma+\epsilon\), \(\epsilon\sim N(0,C)\) with \(C\succ0\), nuisance-profile Fisher is
\[
\mathcal I_{\theta|\gamma}=J^\top[C^{-1}-C^{-1}N(N^\top C^{-1}N)^+N^\top C^{-1}]J.
\]
A linear target \(L\theta\) is identifiable on unrestricted parameter fibres iff \(\ker\mathcal I_{\theta|\gamma}\subseteq\ker L\). For a nonlinear target, vanishing derivative on the kernel only provides **local first-order** identifiability, not a global no-go. In particular a physical \(Q\) or \(F\) cannot be computed on an observed nuisance quotient if its value changes along the quotient fibre. \(\Pi\) cannot be invented from a manifold constraint without an actual null. The five dependent views are deterministic/posterior-law functions of the same source experiment; a full-sky shape \(\chi\) and \(F_{\Omega,2}(\chi)\) carry no new Fisher information.

**Q-Pi deterministic relation, exact under a fixed full-rank Gaussian null:** for \(r\) Gaussian signed coordinates with null \(x_0\), \(Q_{\rm stat}=\sqrt{(\hat x-x_0)^\top\Sigma^{-1}(\hat x-x_0)}\) and \(\Pi_{\chi^2_r}=\mathrm{SF}_{\chi^2_r}(Q_{\rm stat}^2)\). Neither is a physical feasibility gauge. For R65 same-provider selected 2D contrast \(r=2\), \(\Pi=\exp(-Q_{\rm stat}^2/2)\). Statistical Q and Pi are just two presentations of one working-law reference, not independent confirmations.

## 2. Theorem R73-T1: exact physical-feasibility confidence support

Take a regular Gaussian coefficient experiment \(\hat\theta,\Sigma\succ0\), one simultaneous ellipsoid
\[
{\cal E}_\alpha=\{\theta:(\theta-\hat\theta)^\top\Sigma^{-1}(\theta-\hat\theta)\le c_\alpha\}.
\]
A family of **affine physical restrictions** \(g_n(\theta)=b_n+a_n^\top\theta\ge0\), for \(n\in\Omega\) (sky directions, photon intensity moments etc.), is satisfied throughout \({\cal E}_\alpha\) iff
\[
\boxed{\inf_{n\in\Omega}\left[g_n(\hat\theta)-\sqrt{c_\alpha\,a_n^\top\Sigma a_n}\right]\ge0.}
\]
Proof: Cauchy–Schwarz after whitening gives exact ellipsoid support at each fixed n, and infima over product sets commute. If \(a_n^\top\Sigma a_n>0\), an explicit feasible ellipsoid **boundary counter-witness** is
\[
\theta_*(n)=\hat\theta-\sqrt{c_\alpha}\,\Sigma a_n/\sqrt{a_n^\top\Sigma a_n}.
\]
If its \(g_n<0\), robust feasible-domain inclusion fails. This tests confidence-region containment, NOT whether the true universe violates a physical condition. Strict \(g_n>0\) requires a strict positive infimum. If Fisher rank deficient and the physical restriction varies along its null, the entire confidence cylinder is unconstrained in that direction; do not replace it with the pseudoinverse ellipse unless target estimability is established.
Applications:
- P1 **only if physically qualified** \(\theta=(H,d_i,S_A)\), \(g_n=H+d\cdot n+\sum_A S_A nE_A n\). The observed P1/R62 apparent STF lacks the optical \(\sigma/H\) transfer required for direct GR admission.
- P2 (stress only) \(g_n=1/3+n S n\) for all n, iff \(I/3+S\succeq0\), and flux-inclusive moment constraint requires additional \(f\); use this theorem for a full signed STF5 confidence ellipse only if its actual source covariance and null are qualified.
- P3 \(\theta=(V_3,a_0,\ldots,a_J)\), \(g_n=1-B(z)\eta_z(\theta,z,n)\), and \(a_n=-B(z)\times\) \`r64_directional_hubble.field_rows(z,n,J)[1]\`.
- P4 a **physical** linear-count density \(1+d\cdot n\) has \(g_n=1+d\cdot n\), but R65 uses an **exponential log-link** that is automatically positive and must not be falsely assigned this physical count gauge. The causal domain \(|\beta|<1\) requires actual source-qualified 3D \(\beta\), not R65 2D projected count coefficients.
