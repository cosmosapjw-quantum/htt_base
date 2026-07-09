# 추가로 증명 가능한 정리 후보

아래 정리들은 현재 보고서의 약점을 줄이면서 논문 기여를 더 선명하게 만들 수 있는 후보들이야.

## T1. Signed curvature-coordinate domain theorem

**Statement.** \(\Omega_{k,{\rm aniso}}\)를 signed coordinate로 둘 때와 nonnegative magnitude로 둘 때, comparator \(x_C\), physical cone \(C_{\rm phys}\), endpoint decomposition의 필요충분 조건을 분류한다.

**Assumptions.** Registered congruence, fixed FLRW reference branch, explicit residual \(R_{\rm undeclared}\), declared curvature convention.

**Proof path.** Affine coordinate transformation과 cone image를 비교한다. signed case는 interval arithmetic, magnitude case는 non-linear absolute-value map 또는 split variables \(g_k^+,g_k^-\)로 처리한다.

**Numerical witness.** Random reference curvature를 뽑아 \(\Omega_k-\Omega_{k,ref}\)가 음수가 되는 예를 생성하고, 기존 nonnegative cone endpoint가 틀어지는 사례를 보여준다.

## T2. Component-cone sharpness versus GR-realizability theorem

**Statement.** P31의 sharpness는 registered convex component model에서는 성립하지만, full Einstein constraint/evolution admissible set에서는 일반적으로 더 좁아질 수 있다.

**Assumptions.** Abstract box/cone admissible set \(C_{\rm box}\), physical solution admissible set \(C_{\rm GR}\subseteq C_{\rm box}\).

**Proof path.** Linear functional image inclusion: \(c^TC_{\rm GR}\subseteq c^TC_{\rm box}\). Equality requires a realization theorem for every endpoint. 이 조건을 별도 lemma로 둔다.

**Numerical witness.** Toy coupled constraint \(g_W\le a g_\Sigma\)를 추가하면 기존 interval이 sharp하지 않음을 보인다.

## T3. Endpoint inference under active-set changes

**Statement.** Box/cone-constrained reachable estimator의 endpoint maps가 active-set 변화 지점에서 nonsmooth일 때, Gaussian endpoint CI 대신 directional bootstrap 또는 simulation calibration이 필요하다.

**Assumptions.** Local asymptotic normality, convex compact feasible set, endpoint map Hadamard directionally differentiable.

**Proof path.** Shapiro-style directional delta method. Smooth region에서는 IM critical value, kink에서는 bootstrap consistency 조건을 제시한다.

**Numerical witness.** True endpoint가 nonnegative boundary \(g_j=0\)에 있을 때 naive Gaussian endpoint CI가 왜곡되는 MC.

## T4. Joint feasible ratio interval compatibility theorem

**Statement.** Joint ratio interval \(\{N(s)/D(s):s\in S\}\)가 naive quotient interval과 같아지는 필요충분 조건은 numerator와 denominator의 extremizers가 common feasible point에서 호환되는 것이다. Strict inclusion은 generic하지만 unconditional은 아니다.

**Assumptions.** Compact convex \(S\), affine \(N,D\), \(D>0\) on \(S\).

**Proof path.** Naive interval은 \(S\times S\), joint interval은 diagonal \(\{(s,s)\}\). Equality iff product-space extrema intersect diagonal.

**Numerical witness.** `scripts/run_all_experiments.py`의 \(N=2+s,D=5-s\) 반례.

## T5. Prior-mediated null-direction update theorem

**Statement.** Likelihood가 null coordinate에 직접 의존하지 않으면 independent prior에서는 posterior marginal이 prior와 같고 KL=0이다. Coupled prior에서는 posterior marginal이 움직일 수 있지만, 그 update는 reachable coordinate와의 prior coupling을 통한 prior-mediated update로 분해된다.

**Assumptions.** Dominated Bayesian model, likelihood \(L(y|Rg)\), null column \(R_j=0\), prior conditional \(\pi(g_j|g_R)\).

**Proof path.** Posterior marginal \(p(g_j|y)=\int \pi(g_j|g_R)p(g_R|y)dg_R\). Independent case는 \(\pi(g_j)\). Coupled case는 likelihood update가 \(p(g_R|y)\)에만 직접 작용함을 보인다.

**Numerical witness.** Gaussian coupled prior KL 계산. 포함 코드에서 independent KL=0, coupled KL>0.

## T6. Estimated-covariance e-value calibration theorem

**Statement.** Whitening covariance가 finite simulation ensemble에서 추정될 때, Hartlap-corrected Gaussian route 또는 Sellentin–Heavens t route를 쓰지 않으면 nominal e-value/null calibration이 보수성 또는 size를 잃을 수 있다.

**Assumptions.** Wishart sample covariance, independent simulations, dimension \(m\), simulation count \(N_{sim}>m+2\).

**Proof path.** \(E[S^{-1}]=(N_{sim}-1)/(N_{sim}-m-2)C^{-1}\)에서 precision inflation을 보이고, corrected statistic의 expectation을 재계산한다.

**Numerical witness.** 포함 코드의 Hartlap experiment: \(N_{sim}=300,m=20\)에서 raw precision trace inflation \(\simeq1.076\), correction 후 \(\simeq1.001\).

## T7. Predeclared finite-cover scan validity theorem

**Statement.** Threshold/cell/window weights가 data-independent로 predeclared된 finite cover에서는 convex e-value merge가 arbitrary dependence에서도 e-value를 유지한다. Data-adaptive cover/weights는 별도 correction 없이는 보장되지 않는다.

**Assumptions.** \(E_0[E_k]\le1\), deterministic or predictable weights, finite \(K\).

**Proof path.** Linearity of expectation. Adaptive nonpredictable weight에 대한 counterexample를 appendix에 둔다.

**Numerical witness.** Common-factor dependent e-values와 post-hoc max-selected e-values 비교.

## T8. Response-class quotient theorem

**Statement.** Whitened response rows/columns의 equivalence relation으로 legacy family labels를 quotient하면 현재 관측 support에서 구별 가능한 response classes만 남는다.

**Assumptions.** Registered feature map, nuisance-projected whitened response matrix, tolerance policy.

**Proof path.** Identifiability equivalence \(\theta\sim\theta'\iff R\theta=R\theta'\). Quotient parameter space의 Fisher rank가 identifiable dimension.

**Numerical witness.** Column duplication/row duplication examples. 포함 코드에서 column duplication은 rank 증가 없음, row duplication은 noise correlation \(\rho\)에 따라 Fisher factor \(2/(1+\rho)\).

## T9. Data-promotion gate theorem

**Statement.** A diagnostic figure can be promoted to calibrated inference iff it has a registered observable vector, selection/window model, covariance/null ensemble, transfer response, predeclared statistic, and reproducible generator manifest.

**Assumptions.** Gate schema with monotone promotion rule.

**Proof path.** 이건 수학 정리보다는 software-contract theorem에 가깝다. Promotion predicate를 Boolean lattice로 정의하고, missing gate가 있으면 posterior/evidence claim이 type error임을 보인다.

**Numerical witness.** 현재 package sidecar 24개 모두 failed gates 때문에 diagnostic_only로 머무는 감사 스크립트.

## T10. Transverse/spin-2 vorticity reopening theorem

**Statement.** radial dyad response는 antisymmetric vorticity를 annihilate하지만, transverse screen/tensor 또는 spin-2 response basis가 충분한 rank 조건을 만족하면 vorticity-related sector가 row-space로 들어올 수 있다.

**Assumptions.** Screen basis completeness, noise whitening, nuisance projection, nonzero curl-sensitive template columns.

**Proof path.** Representation decomposition: radial scalar channel은 antisymmetric sector에 zero projection, transverse/spin-2 basis는 nonzero projection 가능. Rank condition을 necessary/sufficient로 제시.

**Numerical witness.** Toy response matrix rank 2에서 transverse/spin-2 rows 추가 시 rank 4가 되는 실험.
