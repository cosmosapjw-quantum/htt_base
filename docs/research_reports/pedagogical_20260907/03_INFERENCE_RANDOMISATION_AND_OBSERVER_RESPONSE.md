# Part IV. From a physical model to an inference

## 7. Responses, feasible sets and identification

### 7.1 A forward map is needed before inversion

Let \(X\) denote a physical state, and let \(\eta\) collect maintained choices: frame, congruence, epoch, model branch, nuisance policy and the observation procedure. A response \(\mathcal R_\eta\) maps a physical state to a predicted observable. A response may be nonlinear. A missing response is not the zero map; it means that the corresponding inference has not been specified.

Let \(D_\eta\) be the physical domain, \(B_{\rm MES}(y;\eta)\) the premise-matched sector body, and \(C_y(\eta)\) the set of predictions judged compatible with data \(y\). We define

\[
\Theta(y;\eta)
=D_\eta\cap B_{\rm MES}(y;\eta)
\cap\mathcal R_\eta^{-1}(C_y(\eta)).
\tag{7.1}
\]

A preimage \(\mathcal R^{-1}(C)\) is the set of states whose predicted observations lie in \(C\); it does not assume that \(\mathcal R\) has an inverse function. Equation (7.1) is a definition. Its scientific content comes from the actual domain, response and compatibility criterion, not from writing an intersection symbol.

The same sky may be used to set a multipole ceiling and to define \(C_y\). Those are then two restrictions constructed from shared data. Writing them as separate factors does not make them independent observations. A probabilistic factorisation requires a joint-law argument. This is the point at which physical modelling and statistical modelling meet.

### 7.2 Exact response fibres

Suppose for the moment that the response is linear and the observable vector is exact, so \(C_y=\{y\}\). Let \(X_0\) be any state with \(\mathcal R X_0=y\), and put \(F_y=D_\eta\cap B_{\rm MES}(y;\eta)\). Linearity gives

\[
\{X:\mathcal RX=y\}=X_0+\ker\mathcal R,
\qquad
\Theta(y;\eta)=F_y\cap(X_0+\ker\mathcal R).
\tag{7.2}
\]

The translate of a kernel is called an affine fibre. It contains every exact solution before the domain and inequality restrictions are applied.

**Theorem 7.1 — uniqueness within the maintained feasible domain.** If \(X_0\in F_y\), then

\[
\Theta(y;\eta)=\{X_0\}
\quad\Longleftrightarrow\quad
\{h\in\ker\mathcal R:X_0+h\in F_y\}=\{0\}.
\tag{7.3}
\]

**Proof.** A second compatible point \(X\ne X_0\) gives a nonzero displacement \(h=X-X_0\) with \(\mathcal Rh=0\) and \(X_0+h\in F_y\). Conversely, every such nonzero displacement gives a distinct compatible state. Negating the existence of these equivalent objects proves the equivalence. \(\square\)

Full column rank makes the kernel zero and is sufficient for uniqueness whenever a feasible solution exists. It is not necessary. In the example \(\mathcal R=(1\ \ 1)\), \(y=0\), \(F_y=\{x_1,x_2\ge0\}\), the kernel is the line spanned by \((1,-1)\), but no nonzero displacement from the origin stays in the nonnegative quadrant. The origin is therefore unique. This is the example of Section 1 now written as a general criterion.

An empty feasible set means that the maintained constraints are mutually incompatible with the observation. It is not a detection of a preferred physical state. A bounded non-singleton set represents remaining ambiguity; an unbounded set leaves some directions unrestricted. A disconnected set can encode several separated alternatives. If a required response has not been supplied, none of these geometries can be inferred by calling the state zero.

### 7.3 Realised compatibility and statistical identification

The previous theorem concerns exact data and a declared deterministic map. Statistical identification is a different question: can two physical parameters generate the same probability law for observations? If a model assigns law \(P_{X,\eta}\) to a random observation, a population identified set consists of states producing the same specified population law, after any allowed nuisance variation. A confidence region is instead a random set \(C(Y)\) designed to contain a true state with probability at least a declared coverage level under repeated sampling.

These definitions distinguish a distribution, one realised dataset and a random procedure. A realised set can happen to contain one point without the sampling model being identifiable or the set having confidence coverage. Equation (7.3) does not prove a confidence theorem. Partial-identification and constraint-qualification literature discusses these distinctions in general settings; our specific deterministic fibre argument has been proved directly above. [@MOLINARI_2020; @KAIDO_MOLINARI_STOYE_2022]

For a CMB analysis, the sampling law must account for whatever is random in the comparison: sky realisation, instrumental noise, masks, calibration and any data-derived anchor. A model that changes an observable has demonstrated a response. It has not yet demonstrated a distinguishable physical signature.

## 8. Finite-null ranks and the complete analysis

### 8.1 Why a rank needs a probability argument

A common analysis compares an observed score with scores from simulated or transformed references. A small rank looks unusual, but this interpretation is valid only when the observation could legitimately occupy the reference positions under the null hypothesis.

Let \(Z=(Z_0,\ldots,Z_{n-1})\) contain one labelled observation and \(n-1\) reference rows. Joint exchangeability means that permuting all row labels does not change their joint probability law. This is weaker than independence, but stronger than having identical one-row distributions. Correlations are permitted if the whole law has the required symmetry.

Let \(S=\mathcal A(Z)\in\mathbb R^n\) be the output of the complete analysis. It includes preprocessing, tensor conversion, chart selection, nuisance estimation, MES construction, adaptation, missingness handling and final scoring. Row equivariance means

\[
\mathcal A(\pi Z)=\pi\mathcal A(Z)
\tag{8.1}
\]

for every permutation \(\pi\). In words, changing the labels changes only the labels of the results, not the algorithm applied to a preferred row.

### 8.2 A deterministic counting lemma

For a fixed real score vector \(s\), define

\[
p_i(s)=\frac1n\#\{j:s_j\ge s_i\}.
\tag{8.2}
\]

**Lemma 8.1.** For every \(0\le\alpha\le1\), at most \(\alpha n\) indices satisfy \(p_i\le\alpha\).

**Proof.** Arrange distinct score values from largest to smallest. If their tie groups have sizes \(m_1,\ldots,m_k\), every member of group \(r\) has rank \((m_1+\cdots+m_r)/n\). The included groups must therefore end at a cumulative size no larger than \(\alpha n\). Counting their members proves the statement, including arbitrary ties. \(\square\)

The non-strict inequality \(\ge\) is important. It counts all members of a tie at the conservative edge of that tie group.

**Theorem 8.2 — exchangeable-row rank validity.** If \(Z\) is jointly exchangeable and \(\mathcal A\) is equivariant, then, for any fixed row \(i\),

\[
\Pr\{p_i(\mathcal A(Z))\le\alpha\}\le\alpha.
\tag{8.3}
\]

If the scores have no ties almost surely, the rank is uniform on \(\{1/n,2/n,\ldots,1\}\).

**Proof.** The vector of scores is exchangeable because
\(\mathcal A(Z)\overset d=\mathcal A(\pi Z)=\pi\mathcal A(Z)\).
Thus all events \(p_i\le\alpha\) have the same probability. Averaging their indicators and using Lemma 8.1 gives
\(\Pr(p_i\le\alpha)=n^{-1}\mathbb E\sum_j\mathbf1\{p_j\le\alpha\}\le\alpha\).
Without ties, each fixed score vector has each rank \(1/n,\ldots,1\) exactly once. Exchangeability makes the probability at every rank \(1/n\). \(\square\)

For the observed row and \(N=n-1\) references, Eq. (8.2) becomes

\[
p_0=\frac{1+\sum_{j=1}^{N}\mathbf1\{S_j\ge S_0\}}{N+1}.
\tag{8.4}
\]

The observation contributes the one in the numerator. The fraction is never zero. It is valid because of the preceding symmetry argument, not because the denominator looks familiar.

### 8.3 A finite transformation group is a different reference set

Let a finite group \(\mathcal G\) act on the dataset, and suppose the null law is invariant under that action. For a fixed statistic \(T\), define

\[
p_{\mathcal G}(Z)=\frac1{|\mathcal G|}
\sum_{g\in\mathcal G}\mathbf1\{T(gZ)\ge T(Z)\}.
\tag{8.5}
\]

**Theorem 8.3 — finite-group rank validity.** Under the stated invariant law, \(\Pr(p_{\mathcal G}\le\alpha)\le\alpha\).

**Proof.** For fixed \(z\), form the score list \(T(gz)\), with one position for each group element. Stabiliser duplicates are allowed. Since \(h\mapsto hg\) is a permutation of the group, \(p_{\mathcal G}(gz)\) is precisely the upper-tail rank of the position \(g\) in this list. Lemma 8.1 implies that at most a fraction \(\alpha\) of these positions have rank at most \(\alpha\). Group invariance lets us average the event over all transformed datasets before taking its expectation, giving the same bound. \(\square\)

The relevant positions in this proof are group elements, not arbitrary simulation rows. A sampled subset of transformations needs a construction giving the corresponding conditional exchangeability, including the observed statistic. Merely appending the identity to an arbitrary selected list does not prove that condition. The distinction is the basis of the cited randomisation results. [@RANDOMIZATION_2024; @PHIPSON_SMYTH_2010; @HEMERIK_GOEMAN_2018]

Here is an exact counterexample to enlarging the reference set without enlarging the symmetry. Give equal probability to

\[
(10,0,-100,-100),\qquad(0,10,-100,-100).
\tag{8.6}
\]

The law is invariant under swapping the first two coordinates. Ranking the first coordinate against all four gives \(1/4\) or \(1/2\), each with probability one half. At \(\alpha=1/2\), the rejection probability is one, not at most one half. Ranking over the genuine two-element orbit instead gives \(1/2\) or \(1\), which has the correct finite-group behaviour. Every number follows by counting the two displayed possibilities.

### 8.4 An adaptive counterexample with all counts visible

Consider the four two-coordinate rows

\[
A=(-2,-2),\quad B=(-2,-1),\quad C=(-2,0),\quad D=(-1,-2),
\tag{8.7}
\]

and assign probability \(1/24\) to every ordering. An asymmetric rule chooses the coordinate with the larger absolute value in the distinguished first row, breaking an exact tie towards coordinate 2. It then ranks that row by absolute value in the chosen coordinate.

| First row | Selected coordinate | Number of rows at least as extreme | Rank | Orderings with this first row |
|---|---:|---:|---:|---:|
| A | 2 | 2 | 1/2 | 6 |
| B | 1 | 3 | 3/4 | 6 |
| C | 1 | 3 | 3/4 | 6 |
| D | 2 | 2 | 1/2 | 6 |

The remaining three labels can be ordered in \(3!=6\) ways, proving the final column. Thus the ranks split into twelve at \(1/2\) and twelve at \(3/4\). At \(\alpha=3/4\), all 24 are rejected, giving a size excess of \(1/4\). If exact ties go to coordinate 1, row A joins B and C: there are six ranks at \(1/2\) and eighteen at \(3/4\), with the same maximal excess.

Now choose a coordinate from the pooled sums of squares instead. The first coordinate has sum 13 and the second sum 9, independent of row ordering. Selecting the larger pooled sum always chooses coordinate 1. Rows A, B and C then have rank \(3/4\), while D has rank 1. The probabilities are \(3/4\) and \(1/4\), and Eq. (8.3) holds. The problem was label-asymmetric adaptation, not adaptation itself.

### 8.5 Missing charts, shared data and null fidelity

A chart refusal must remain part of the complete analysis. Deleting only reference rows whose inverse chart is unavailable changes the law of the comparison while treating the observed row differently. One may instead use a full-tensor statistic defined for every row, a genuinely symmetric status-aware construction, or abstain for the pool. Replacing an unavailable value by zero is not the same operation.

Similarly, the same data-dependent MES prescription must be included in every symmetrically treated row if the row theorem is invoked. A different anchor construction for the observation violates the hypothesis even if the final score formula is identical.

Finally, exact rank arithmetic cannot repair an unsuitable null law. A noisy observation and noise-free reference skies do not become exchangeable merely by using the same harmonic coordinates. Shared sky realisations also prevent several analysis outputs from being automatically independent replications. No current observational p-value is produced by this report.

# Part V. A concrete response: changing the observer

## 9. Doppler response and its STF form

### 9.1 Relative observers and the temperature transformation

Let \(\beta^a\) be spatial relative to \(u\), with \(\beta^2<1\), and define

\[
\widetilde u^a=\gamma(u^a+\beta^a),\qquad
\gamma=(1-\beta^2)^{-1/2}.
\tag{9.1}
\]

Its norm is \(\gamma^2(-1+\beta^2)=-1\). The physical relative velocity is \(c\beta\); this is the radiation–observer response, not a statement about a global matter-frame tilt.

Using \(p=(E_\gamma/c)(u-n)\) from Section 5,

\[
\widetilde E_\gamma=-c\,p\cdot\widetilde u
=\gamma E_\gamma(1+\beta\cdot n).
\tag{9.2}
\]

A Lorentz transformation parallel and perpendicular to \(\widehat\beta\) gives the outward direction

\[
\widetilde n=
\frac{n+[(\gamma-1)(\widehat\beta\cdot n)+\gamma|\beta|]\widehat\beta}
{\gamma(1+\beta\cdot n)}.
\tag{9.3}
\]

At \(\beta=0\) the formula is understood by continuity. To obtain the inverse, replace \(\beta\) by \(-\beta\) and interchange the two observers. In particular,
\(\gamma(1+\beta\cdot n)=1/[\gamma(1-\beta\cdot\widetilde n)]\).

For thermodynamic temperature, the photon occupation number has directional Planck form \(f=[\exp(E_\gamma/(k_BT(n)))-1]^{-1}\). Occupation number is a scalar on photon phase space. Equating it in the two frames leaves \(E_\gamma/T\) unchanged for the same ray, giving

\[
\boxed{\widetilde T(\widetilde n)
=\frac{T(n(\widetilde n))}{\gamma(1-\beta\cdot\widetilde n)}}.
\tag{9.4}
\]

This derivation states the physical input: a scalar occupation number and thermodynamic temperature, often called Doppler weight one. A frequency-dependent intensity or another observable has a different transformation law and cannot silently use Eq. (9.4). [@DAI_CHLUBA_2014; @YASINI_PIERPAOLI_2017]

### 9.2 The first-order generator

Expand the inverse of Eq. (9.3) at fixed \(\widetilde n\):
\(n=\widetilde n-\beta+(\beta\cdot\widetilde n)\widetilde n+O(\beta^2)\).
The displacement is tangent to the sphere. Since \(\gamma=1+O(\beta^2)\), Taylor expansion of Eq. (9.4), dropping the tilde on its argument, yields

\[
\delta_\beta T(n)
=(\beta\cdot n)T(n)
-[\beta-(\beta\cdot n)n]\cdot\nabla_{S^2}T(n).
\tag{9.5}
\]

The surface gradient is the tangential projection of an ambient gradient. The first term is Doppler modulation; the second shifts the angular argument. Both signs follow from the outward-sky convention. This is a first-order expansion for sufficiently smooth positive temperature fields and small \(\beta\), not an exact finite-velocity truncation.

For a constant monopole, the gradient term vanishes, so \(\delta_\beta T_0=T_0\beta\cdot n\): a pure dipole. For a quadrupole \(T_Q=Q_{ij}n_in_j\), the surface gradient is
\(2[Qn-(Q_{ij}n_in_j)n]\). Consequently,

\[
\delta_\beta T_Q
=3(\beta\cdot n)Q_{ij}n_in_j-2(Q\beta)\cdot n.
\tag{9.6}
\]

The cubic term contains both octupole and dipole parts. To separate them, apply the STF projection rather than reading the polynomial degree alone.

### 9.3 The quadrupole-to-octupole map

Define the linear map \(B_Q:\mathbb R^3\to\mathrm{STF}_3\) by

\[
(B_Q\beta)_{ijk}=3\beta_{\langle i}Q_{jk\rangle}.
\tag{9.7}
\]

Using Eq. (2.4), its complete Cartesian form is

\[
(B_Q\beta)_{ijk}
=\beta_iQ_{jk}+\beta_jQ_{ik}+\beta_kQ_{ij}
-\frac25[\delta_{ij}(Q\beta)_k+\delta_{ik}(Q\beta)_j+\delta_{jk}(Q\beta)_i].
\tag{9.8}
\]

The trace of the first three terms is \(2(Q\beta)_i\), explaining the coefficient \(2/5\). Contracting with \(n_in_jn_k\) and using Eq. (9.6) shows
\(\delta_\beta T_Q=(B_Q\beta)_{ijk}n_in_jn_k-\tfrac45(Q\beta)\cdot n\).
Thus \(B_Q\beta\) is precisely its octupole contribution. This calculation is independent of a coordinate-specific spherical-harmonic table.

**Proposition 9.1 — adjoint and normal matrix.** In the full Frobenius metric,

\[
(B_Q^*O)_i=3(O:Q)_i,\qquad
(B_Q\beta):Q=M_Q\beta,
\quad M_Q=(Q:Q)I+\frac65Q^2,
\tag{9.9}
\]

and hence \(B_Q^*B_Q=3M_Q\).

**Proof.** Contract Eq. (9.8) with an STF3 tensor. The delta terms vanish by trace-freeness, and symmetry makes the first three terms equal to \(\beta_iO_{ijk}Q_{jk}\). This proves the adjoint formula. Next contract Eq. (9.8) with \(Q_{jk}\). The first three terms give \((Q:Q)\beta+2Q^2\beta\). The first two delta terms contribute \(-\tfrac45Q^2\beta\), while the last contains \(\operatorname{tr}Q=0\). The total is Eq. (9.9). Apply the adjoint formula once more to obtain \(3M_Q\). \(\square\)

For \(Q\ne0\), \(M_Q\) is positive definite since
\(x^TM_Qx=(Q:Q)\|x\|^2+\tfrac65\|Qx\|^2>0\).
The map therefore has rank three.

### 9.4 Least-squares response coordinates and the residual

**Theorem 9.2 — inverse on the response image and orthogonal residual.** For nonzero \(Q\), the minimum of \(\|O-B_Q\beta\|_F^2\) occurs uniquely at

\[
\widehat\beta_{\rm LS}=M_Q^{-1}(O:Q).
\tag{9.10}
\]

The corresponding projection is
\(P_QO=B_QM_Q^{-1}(O:Q)\), and the residual \(O_\perp=O-P_QO\) satisfies \(O_\perp:Q=0\). The residual subspace has dimension four.

**Proof.** The normal equation is \(B_Q^*B_Q\beta=B_Q^*O\). Both sides contain the same factor three by Proposition 9.1, giving Eq. (9.10). Since \(M_Q\succ0\), the minimiser is unique. Its residual is orthogonal to the image, equivalently \(B_Q^*O_\perp=0\), which is the contraction statement. Rank–nullity gives \(7-3=4\). \(\square\)

An image vector has the form \(B_Q\beta\), so Eq. (9.10) also recovers that \(\beta\) exactly. For a general observed octupole it is only an algebraic response coordinate. An arbitrary intrinsic octupole can have a component in the same image. Without a physical model separating those contributions, the coordinate is not an empirical observer velocity. The residual is not automatically an identified intrinsic octupole. [@ROLDAN_NOTARI_QUARTIN_2016]

### 9.5 A sharp relative-conditioning bound

**Theorem 9.3.** For every nonzero real STF2 quadrupole,

\[
\kappa_2(M_Q)\le\frac53,\qquad
\kappa_2(B_Q)\le\sqrt{\frac53}.
\tag{9.11}
\]

**Proof.** Diagonalise \(Q\). Up to an overall scale, sign and permutation, any nonzero trace-free spectrum can be written \((-1,1-t,t)\), with \(0\le t\le1/2\): choose the eigenvalue of the isolated sign, scale its magnitude to one, and order the other two. The largest squared eigenvalue is 1 and the smallest is \(t^2\). Substitution into Eq. (9.9) gives

\[
\kappa_2(M_Q)=\frac{8-5t+5t^2}{5-5t+8t^2},\qquad
\frac53-\kappa_2(M_Q)
=\frac{(5t-1)^2}{3(5-5t+8t^2)}\ge0.
\tag{9.12}
\]

The denominator is positive. Equality occurs at \(t=1/5\), or spectra proportional to \((-5,4,1)\). Finally, singular values of \(B_Q\) are square roots of eigenvalues of \(3M_Q\), proving the second bound and its sharpness. \(\square\)

This is a relative condition bound. Multiplying \(Q\) by a small amplitude multiplies \(B_Q\) by that amplitude, so the absolute inverse sensitivity still diverges as \(Q\to0\). A small condition number does not remove the need for a nonzero signal or a physical error model.
