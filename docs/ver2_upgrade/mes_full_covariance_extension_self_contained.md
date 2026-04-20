# Full-covariance MES extension

## Off-diagonal CMB covariance, BiPoSH admissible sets, and morphology-aware bounds

**Status:** self-contained mathematical-physics research note, manuscript-insertion candidate  
**Scope:** extension of the diagonal MES kinematic bounds using full harmonic covariance / BiPoSH information  
**Main output:** a theorem-level framework for deriving new bounds on shear, vorticity, acceleration, local boost, global tilt, and anisotropic curvature from off-diagonal low-\(\ell\) covariance.

---

## 0. Executive claim

The existing MES use in the manuscript compresses the CMB anisotropy information into diagonal low-multipole amplitudes,
\[
(\epsilon_1,\epsilon_2,\epsilon_3)
\quad\Longrightarrow\quad
(B_\sigma,B_\omega,B_A),
\]
where \(\sigma_{ab}\) is shear, \(\omega_{ab}\) is vorticity, and \(A_a\equiv \dot u_a\) is four-acceleration.  This is robust, but it discards directional covariance information.  In Bianchi or tilted models the harmonic covariance is generally not diagonal:
\[
\langle a^X_{\ell m}a^{Y*}_{\ell' m'}\rangle
\neq
C^{XY}_\ell\delta_{\ell\ell'}\delta_{mm'}.
\]
The missing information lives in the off-diagonal covariance, equivalently in the non-scalar BiPoSH coefficients \(A^{LM,XY}_{\ell\ell'}\) with \(L>0\).  Once the low-\(\ell\) solver produces theory-side \(a^{T,E,B}_{\ell m}\), map templates, or covariance-response matrices for each Bianchi family, the MES programme can be upgraded from a scalar ceiling to a full-covariance admissible-set framework.

The correct safe statement is not
\[
\text{``BiPoSH replaces MES.''}
\]
It is
\[
\boxed{
B_j^{\rm final}
=
\min\{B_j^{\rm diag},B_j^{\rm cov},B_j^{\rm dyn}\}
}
\]
for each normalized kinematic/geometric block \(j\), where \(B_j^{\rm diag}\) is the inherited diagonal MES bound, \(B_j^{\rm cov}\) is the new full-covariance response bound, and \(B_j^{\rm dyn}\) is any independent Einstein-constraint, Bianchi-Jacobi, Frobenius, momentum-constraint, or type-specific dynamical bound.

The key diagnostic is the morphology information gain
\[
\boxed{
\mathcal I_j^{\rm morph}
:=
\frac{B_j^{\rm diag}}{B_j^{\rm final}}
\ge 1.
}
\]
If \(\mathcal I_j^{\rm morph}>1\), diagonal MES compression has genuinely lost observable information.  This is the clean way to formulate the proposed backreaction point: anisotropic background geometry changes not only scalar low-\(\ell\) power but the full covariance geometry of the observed sky.

---

## 1. Conventions and basic objects

### 1.1 Metric, units, and kinematic normalization

We use metric signature \((-,+,+,+)\).  Let the physical four-velocity be \(U^a\), normalized by
\[
U^aU_a=-c^2.
\]
It is convenient to define the dimensionless unit timelike vector
\[
u^a:=U^a/c,
\qquad
u^a u_a=-1.
\]
In the rest of the note, \(u^a\) denotes this dimensionless unit timelike vector.  The rest-space projector is
\[
h_{ab}=g_{ab}+u_a u_b.
\]
The kinematic decomposition is
\[
\nabla_bu_a
= -A_a u_b+\frac{1}{3}\Theta h_{ab}+\sigma_{ab}+\omega_{ab},
\]
where
\[
\Theta:=\nabla_a u^a,
\]
\[
\sigma_{ab}:=h_{\langle a}{}^c h_{b\rangle}{}^d\nabla_cu_d,
\]
\[
\omega_{ab}:=h_{[a}{}^c h_{b]}{}^d\nabla_cu_d,
\]
\[
A_a:=u^b\nabla_bu_a.
\]
Here \(\langle\cdots\rangle\) denotes projected, symmetric, trace-free part.  The Hubble scalar is
\[
H:=\frac{1}{3}\Theta.
\]

The dimensionless normalized variables are
\[
\Sigma_{ab}:=\frac{\sigma_{ab}}{\Theta},
\qquad
W_{ab}:=\frac{\omega_{ab}}{\Theta},
\qquad
\mathcal A_a:=\frac{A_a}{\Theta},
\qquad
\beta:=\frac{v}{c}.
\]
No hidden \(\hbar\) or \(k_B\) convention enters; CMB anisotropy amplitudes and covariance ratios are dimensionless.

### 1.2 Standardized scalar norms

The manuscript’s standardized shear variable is
\[
\Sigma^2_{\rm std}
:=\frac{\sigma_{ab}\sigma^{ab}}{6H^2}.
\]
Since \(H=\Theta/3\),
\[
\Sigma^2_{\rm std}
=\frac{\sigma_{ab}\sigma^{ab}}{6(\Theta/3)^2}
=\frac{3}{2}\frac{\sigma_{ab}\sigma^{ab}}{\Theta^2}.
\]
Thus
\[
\frac{\sqrt{\sigma_{ab}\sigma^{ab}}}{\Theta}<B_\sigma
\quad\Longrightarrow\quad
\Sigma^2_{\rm std}<\frac{3}{2}B_\sigma^2.
\]
Similarly,
\[
W^2_{\rm std}<\frac{3}{2}B_\omega^2,
\qquad
A^2_{\rm std}<\frac{3}{2}B_A^2,
\]
provided the acceleration norm is standardized with the same \(H=\Theta/3\) convention.  This \(3/2\) factor is not optional; it is a pure normalization consequence.

### 1.3 Harmonic data vector

Let
\[
a^X_{\ell m},
\qquad
X\in\{T,E,B\},
\]
be low-\(\ell\) harmonic coefficients.  We gather them into a finite vector
\[
\mathbf a=(a_i),
\qquad
 i=(X,\ell,m),
\qquad
\ell_{\min}\le \ell\le L_{\max}.
\]
Typically \(\ell_{\min}=2\); \(\ell=1\) should be included only when the frame, local-boost subtraction, and kinematic dipole convention have been explicitly fixed.

The covariance is
\[
K_{ij}:=\langle a_i a_j^*\rangle.
\]
For an exactly statistically isotropic FLRW covariance model,
\[
K^{(0),XY}_{\ell m,\ell'm'}
=C^{XY}_\ell\delta_{\ell\ell'}\delta_{mm'}.
\]
A Bianchi or tilted model generically gives
\[
K=K^{(0)}+\Delta K,
\]
where \(\Delta K\) has off-diagonal structure in \(\ell,m\) and channel space.

---

## 2. Baseline diagonal MES theorem

The full-covariance extension below takes the established diagonal MES theorem as its baseline input.  It does not modify the original MES hierarchy.  The theorem is stated here in the form needed for the extension.

### Theorem 2.1 — diagonal MES kinematic ceiling

Assume the MES all-observer near-isotropy hypotheses: for every fundamental observer, the dimensionless CMB multipoles and their first covariant time and spatial derivatives are bounded by small quantities \(\epsilon_\ell\), at least for \(\ell=1,2,3\).  In the first-order PSTF free-streaming hierarchy, the low multipoles obey
\[
\ell=1:
\quad
\dot I_a+\frac{4}{3}\Theta I_a+\tilde D^bI_{ab}-\frac{1}{3}\tilde D_aI+\frac{4}{3}IA_a=0,
\]
\[
\ell=2:
\quad
\dot I_{ab}+\frac{4}{3}\Theta I_{ab}+\tilde D^cI_{abc}-\frac{2}{5}\tilde D_{\langle a}I_{b\rangle}-\frac{8}{15}I\sigma_{ab}=0,
\]
\[
\ell=3:
\quad
\dot I_{abc}+\frac{4}{3}\Theta I_{abc}+\tilde D^dI_{dabc}-\frac{3}{7}\tilde D_{\langle a}I_{bc\rangle}=0.
\]
Then
\[
\frac{\sqrt{\sigma_{ab}\sigma^{ab}}}{\Theta}<B_\sigma,
\qquad
B_\sigma:=\frac{5}{3}\epsilon_1+3\epsilon_2+\frac{3}{7}\epsilon_3,
\]
\[
\frac{\sqrt{\omega_{ab}\omega^{ab}}}{\Theta}<B_\omega,
\qquad
B_\omega:=\frac{3}{4}\epsilon_1+2\epsilon_2+\frac{2}{7}\epsilon_3,
\]
\[
\frac{\sqrt{A_aA^a}}{\Theta}<B_A,
\qquad
B_A:=\frac{3}{4}\epsilon_1+
\epsilon_2+\frac{3}{14}\epsilon_3.
\]
Equivalently,
\[
\Sigma^2_{\rm std}<\frac{3}{2}B_\sigma^2,
\qquad
W^2_{\rm std}<\frac{3}{2}B_\omega^2,
\qquad
A^2_{\rm std}<\frac{3}{2}B_A^2.
\]

### Proof-status note

This note is a self-contained proof of the full-covariance extension conditional on Theorem 2.1.  Theorem 2.1 itself is the already-established diagonal MES input in the manuscript: shear follows by inverting the \(\ell=2\) equation, acceleration by inverting the \(\ell=1\) equation, and vorticity indirectly through the Einstein momentum constraint and direction equation.  No theorem below assumes more than these three diagonal ceilings.

---

## 3. BiPoSH decomposition of the covariance

### 3.1 Definition

For fixed channels \((X,Y)\), define
\[
K^{XY}_{\ell m,
\ell'm'}:=\langle a^X_{\ell m}a^{Y*}_{\ell'm'}\rangle.
\]
The BiPoSH coefficients are
\[
A^{LM,XY}_{\ell\ell'}
:=
\sum_{mm'}(-1)^{m'}
\langle \ell m,\ell' {-m'}|LM\rangle
K^{XY}_{\ell m,
\ell'm'}.
\]
The inverse relation is
\[
K^{XY}_{\ell m,
\ell'm'}
=
\sum_{LM}(-1)^{m'}
\langle \ell m,\ell' {-m'}|LM\rangle
A^{LM,XY}_{\ell\ell'}.
\]

### Lemma 3.1 — invertibility and Parseval identity

For fixed \((\ell,
\ell',X,Y)\), the BiPoSH transformation is unitary up to phase.  Hence
\[
\sum_{mm'}|K^{XY}_{\ell m,
\ell'm'}|^2
=
\sum_{LM}|A^{LM,XY}_{\ell\ell'}|^2.
\]

### Proof

The Clebsch-Gordan coefficients implement the unitary change of basis
\[
|\ell m\rangle\otimes|\ell' {-m'}\rangle
\longleftrightarrow
|LM\rangle.
\]
Their orthogonality gives
\[
\sum_{mm'}
\langle \ell m,
\ell' {-m'}|LM\rangle
\langle \ell m,
\ell' {-m'}|L'M'\rangle^*
=
\delta_{LL'}\delta_{MM'}.
\]
Multiplication by \((-1)^{m'}\) is a phase and preserves norms.  Therefore the transform has the stated inverse and preserves the squared norm by Parseval’s identity.  \(\square\)

### Theorem 3.2 — statistical isotropy iff only scalar diagonal BiPoSH survives

A covariance matrix is statistically isotropic,
\[
D(R)KD(R)^\dagger=K
\qquad\forall R\in SO(3),
\]
if and only if
\[
K^{XY}_{\ell m,
\ell'm'}=C^{XY}_\ell\delta_{\ell\ell'}\delta_{mm'}.
\]
Equivalently,
\[
A^{LM,XY}_{\ell\ell'}=0
\quad\text{unless}\quad
L=0,
\;M=0,
\;\ell=\ell'.
\]

### Proof

For each \(\ell\), \(a_{\ell m}\) spans the irreducible representation \(V_\ell\) of \(SO(3)\).  The full harmonic space is a direct sum
\[
\mathcal H=\bigoplus_{X,
\ell}V_{X\ell},
\]
where the channel label is not rotated by spatial rotations.  A statistically isotropic covariance is an intertwining operator commuting with every \(SO(3)\) action.  By Schur’s lemma, a block mapping \(V_{Y\ell'}\to V_{X\ell}\) must vanish for \(\ell\ne\ell'\), and for \(\ell=\ell'\) must be proportional to the identity in \(m\)-space.  Thus
\[
K^{XY}_{\ell m,
\ell'm'}=C^{XY}_\ell\delta_{\ell\ell'}\delta_{mm'}.
\]
Conversely, any covariance of this form is manifestly invariant under rotations because each irreducible block is proportional to the identity.  The BiPoSH statement follows because the scalar representation in \(V_\ell\otimes V_\ell^*\) is exactly the \(L=0\) piece.  \(\square\)

### Corollary 3.3 — diagonal \(C_\ell\) compression loses anisotropic information

Two anisotropic models can have identical diagonal \(C^{XY}_\ell\) but different \(L>0\) BiPoSH coefficients.  A likelihood depending only on \(C_\ell\) cannot distinguish them.

### Proof

The diagonal spectra are the \(L=0,\ell=\ell'\) sector.  Lemma 3.1 says the \(L>0\) sectors are orthogonal covariance components.  A functional of only \(C_\ell\) is constant under changes in the orthogonal \(L>0\) sector.  Hence it cannot distinguish covariance matrices differing only by those components.  \(\square\)

---

## 4. Off-diagonal observable vector and solver response

### 4.1 Observable vector

Choose a finite index set \(\mathcal I\) of anisotropy-sensitive BiPoSH modes, for example
\[
\mathcal I
=\{(L,M,
\ell,
\ell',X,Y):L>0,
2\le\ell,
\ell'\le L_{\max},
X,Y\in\{T,E,B\}\}.
\]
Define
\[
\mathbf s
:=
\bigl(A^{LM,XY}_{\ell\ell'}\bigr)_{\mathcal I}.
\]
Let \(\widehat{\mathbf s}\) be the data estimator and let
\[
N:=\operatorname{Cov}(\widehat{\mathbf s})
\]
be its covariance, including cosmic variance, instrumental noise, mask leakage, beam effects, foreground residuals, and estimator covariance.  On the retained subspace, assume \(N\) is positive definite.  If not, first quotient by exact null directions or add an explicit regularization prior.

Whiten the observable:
\[
\mathbf y:=N^{-1/2}\widehat{\mathbf s}.
\]
For a theory prediction \(\mathbf s(\mathbf p)\), define
\[
\boldsymbol\mu(\mathbf p):=N^{-1/2}\mathbf s(\mathbf p).
\]

### 4.2 Parameter blocks

Let
\[
\mathbf p
=(
\boldsymbol\Sigma,
\boldsymbol W,
\boldsymbol{\mathcal A},
\boldsymbol\beta_{\rm loc},
\boldsymbol\beta_{\rm tilt},
\boldsymbol\kappa_{\rm aniso}
)
\]
collect dimensionless blocks:

* \(\boldsymbol\Sigma\): 5-component STF shear block \(\sigma_{ab}/\Theta\);
* \(\boldsymbol W\): 3-component vorticity block \(\omega_{ab}/\Theta\), equivalently a pseudovector;
* \(\boldsymbol{\mathcal A}\): 3-component acceleration block \(A_a/\Theta\);
* \(\boldsymbol\beta_{\rm loc}\): observer-side local boost \(v_{\rm loc}/c\);
* \(\boldsymbol\beta_{\rm tilt}\): source/background-side global tilt;
* \(\boldsymbol\kappa_{\rm aniso}\): anisotropic-curvature block.

The low-\(\ell\) solver gives a differentiable map
\[
\mathbf s(\mathbf p)=R\mathbf p+
\mathbf r(\mathbf p),
\]
where
\[
R=
\left.\frac{\partial \mathbf s}{\partial\mathbf p}\right|_{\mathbf p=0}
\]
and the nonlinear remainder obeys, within a validity ball,
\[
\|N^{-1/2}\mathbf r(\mathbf p)\|
\le
\frac{1}{2}M\|\mathbf p\|^2.
\]
The whitened response is
\[
\widetilde R:=N^{-1/2}R.
\]

---

## 5. Covariance admissible set

For a confidence radius \(\rho_\alpha>0\), define the linear covariance admissible set
\[
\mathcal C^{\rm lin}_{\rm cov}(\alpha)
:=
\{\mathbf p:
\|\widetilde R\mathbf p-
\mathbf y\|^2\le \rho_\alpha^2\}.
\]
When the extracted off-diagonal vector is consistent with zero after nuisance subtraction, a conservative null-centered upper-limit set is
\[
\mathcal C^{\rm lin}_{\rm cov,0}(\alpha)
:=
\{\mathbf p:
\|\widetilde R\mathbf p\|^2\le\rho_\alpha^2\}.
\]
A frequentist implementation can set \(\rho_\alpha^2=\chi^2_\nu(\alpha)\), where \(\nu\) is the number of retained whitened modes.  A Bayesian/mock-calibrated implementation can choose \(\rho_\alpha\) from posterior predictive or injection-recovery coverage.  The algebra below only requires \(\rho_\alpha>0\).

The combined admissible region is
\[
\mathcal C_{\rm all}
:=
\mathcal C^{\rm diag}_{\rm MES}
\cap
\mathcal C^{\rm lin}_{\rm cov}(\alpha)
\cap
\mathcal C_{\rm dyn},
\]
where \(\mathcal C_{\rm dyn}\) contains Bianchi type constraints, Frobenius couplings, momentum constraints, curvature signs, and frame-admissibility conditions.

### Proposition 5.1 — adding covariance information cannot weaken the MES bound

For any block \(j\), define
\[
B_j^{\rm final}
:=
\sup_{\mathbf p\in\mathcal C_{\rm all}}\|\mathbf p_j\|.
\]
If
\[
B_j^{\rm diag}
:=
\sup_{\mathbf p\in\mathcal C^{\rm diag}_{\rm MES}}\|\mathbf p_j\|,
\]
then
\[
B_j^{\rm final}\le B_j^{\rm diag}.
\]

### Proof

Because
\[
\mathcal C_{\rm all}\subseteq\mathcal C^{\rm diag}_{\rm MES},
\]
the supremum of \(\|\mathbf p_j\|\) over \(\mathcal C_{\rm all}\) cannot exceed the supremum over \(\mathcal C^{\rm diag}_{\rm MES}\).  Hence \(B_j^{\rm final}\le B_j^{\rm diag}\).  \(\square\)

---

## 6. Singular-value covariance bounds

### Theorem 6.1 — no-nuisance bound

Assume a single block \(\mathbf p_j\in\mathbb R^{d_j}\) contributes linearly:
\[
\boldsymbol\mu=
\widetilde R_j\mathbf p_j.
\]
If
\[
\|\widetilde R_j\mathbf p_j\|
\le\rho_\alpha
\]
and \(\widetilde R_j\) has full column rank, then
\[
\boxed{
\|\mathbf p_j\|
\le
B_j^{\rm cov}
:=
\frac{\rho_\alpha}{s_{\min}(\widetilde R_j)}.
}
\]

### Proof

For a full-column-rank matrix,
\[
\|\widetilde R_j\mathbf p_j\|
\ge
s_{\min}(\widetilde R_j)\|\mathbf p_j\|.
\]
Combining this with the admissibility condition gives
\[
s_{\min}(\widetilde R_j)\|\mathbf p_j\|
\le
\rho_\alpha.
\]
Since \(s_{\min}>0\), division proves the bound.  \(\square\)

### Theorem 6.2 — nuisance-projected bound

Suppose
\[
\boldsymbol\mu
=
\widetilde R_j\mathbf p_j+
\widetilde R_n\mathbf q,
\]
where \(\mathbf q\) is a nuisance block.  Let
\[
P_n^\perp
:=
I-
\widetilde R_n(\widetilde R_n^T\widetilde R_n)^+\widetilde R_n^T
\]
be the orthogonal projector onto the complement of the nuisance column space.  If
\[
\|\widetilde R_j\mathbf p_j+
\widetilde R_n\mathbf q\|
\le\rho_\alpha
\]
for some \(\mathbf q\), and if \(P_n^\perp\widetilde R_j\) has full column rank, then
\[
\boxed{
\|\mathbf p_j\|
\le
\frac{\rho_\alpha}{s_{\min}(P_n^\perp\widetilde R_j)}.
}
\]

### Proof

Apply \(P_n^\perp\):
\[
P_n^\perp(
\widetilde R_j\mathbf p_j+
\widetilde R_n\mathbf q)
=
P_n^\perp\widetilde R_j\mathbf p_j
+P_n^\perp\widetilde R_n\mathbf q.
\]
The second term vanishes by definition of \(P_n^\perp\), so
\[
P_n^\perp(
\widetilde R_j\mathbf p_j+
\widetilde R_n\mathbf q)
=
P_n^\perp\widetilde R_j\mathbf p_j.
\]
Orthogonal projectors are contractions, hence
\[
\|P_n^\perp\widetilde R_j\mathbf p_j\|
\le
\|\widetilde R_j\mathbf p_j+
\widetilde R_n\mathbf q\|
\le
\rho_\alpha.
\]
Full column rank gives
\[
\|P_n^\perp\widetilde R_j\mathbf p_j\|
\ge
s_{\min}(P_n^\perp\widetilde R_j)\|\mathbf p_j\|.
\]
Combining these inequalities proves the result.  \(\square\)

### Corollary 6.3 — rank failure is a theorem-level no-claim condition

If
\[
s_{\min}(P_n^\perp\widetilde R_j)=0,
\]
then no finite covariance-only bound on \(\|\mathbf p_j\|\) exists without an additional prior, nonlinear constraint, or dynamical/type-specific constraint.

### Proof

If the smallest singular value is zero, there exists \(\mathbf v\ne0\) such that
\[
P_n^\perp\widetilde R_j\mathbf v=0.
\]
For \(\mathbf p_j=\lambda\mathbf v\), the nuisance-orthogonal signal vanishes for every \(\lambda\), while
\[
\|\mathbf p_j\|=|\lambda|\|\mathbf v\|
\]
can be arbitrarily large.  Thus no finite upper bound follows from this covariance space.  \(\square\)

---

## 7. Nonlinear remainder control

The linear covariance bound is production-safe only within the response validity radius.

### Theorem 7.1 — perturbative validity radius

Assume
\[
\|N^{-1/2}\mathbf r(\mathbf p)\|
\le
\frac{1}{2}M\|\mathbf p\|^2
\]
and assume \(\widetilde R\) has smallest singular value \(s_{\min}>0\).  If
\[
\|N^{-1/2}\mathbf s(\mathbf p)\|
\le\rho_\alpha
\]
and
\[
\|\mathbf p\|<\frac{s_{\min}}{M},
\]
then
\[
\|\mathbf p\|
\le
\frac{2\rho_\alpha}{s_{\min}}.
\]

### Proof

The whitened signal is
\[
N^{-1/2}\mathbf s(\mathbf p)=
\widetilde R\mathbf p+N^{-1/2}\mathbf r(\mathbf p).
\]
By the reverse triangle inequality,
\[
\|N^{-1/2}\mathbf s(\mathbf p)\|
\ge
\|\widetilde R\mathbf p\|-
\|N^{-1/2}\mathbf r(\mathbf p)\|.
\]
Using the singular-value lower bound and the remainder bound,
\[
\|N^{-1/2}\mathbf s(\mathbf p)\|
\ge
s_{\min}\|\mathbf p\|-\frac{1}{2}M\|\mathbf p\|^2.
\]
If \(\|\mathbf p\|<s_{\min}/M\), then
\[
\frac{1}{2}M\|\mathbf p\|^2<\frac{1}{2}s_{\min}\|\mathbf p\|.
\]
Therefore
\[
\|N^{-1/2}\mathbf s(\mathbf p)\|>
\frac{1}{2}s_{\min}\|\mathbf p\|.
\]
Together with \(\|N^{-1/2}\mathbf s(\mathbf p)\|\le\rho_\alpha\), this yields
\[
\|\mathbf p\|<\frac{2\rho_\alpha}{s_{\min}}.
\]
Closure gives the non-strict bound.  \(\square\)

---

## 8. Concrete new bounds

### 8.1 Component-wise shear bound

Set \(\mathbf p_j=\boldsymbol\Sigma\in\mathbb R^5\).  If
\[
s_\Sigma:=s_{\min}(P_n^\perp N^{-1/2}R_\Sigma)>0,
\]
then
\[
\|\boldsymbol\Sigma\|
\le
B_\Sigma^{\rm cov}
:=
\frac{\rho_\alpha}{s_\Sigma}.
\]
The scalar standardized shear ceiling becomes
\[
\Sigma^2_{\rm std}
<
\frac{3}{2}
\min\left\{
B_\sigma^2,
(B_\Sigma^{\rm cov})^2,
(B_\Sigma^{\rm dyn})^2
\right\}.
\]
This is the highest-priority extension because shear is already the direct \(\ell=2\) source in the diagonal MES hierarchy.

### 8.2 Vorticity / handedness bound

Vorticity is structurally different: it is weak or indirect in diagonal TT because the antisymmetric contraction in the photon energy equation vanishes.  The full-covariance route should target parity-odd or handed morphology:
\[
TB,
\quad EB,
\quad
E\leftrightarrow B\text{ mixing},
\quad
L=1\text{ or handed }L=2\text{ BiPoSH}.
\]
If
\[
s_W:=s_{\min}(P_n^\perp N^{-1/2}R_W)>0,
\]
then
\[
\|\boldsymbol W\|
\le
B_W^{\rm cov}
:=
\frac{\rho_\alpha}{s_W}.
\]
If \(s_W=0\), this route provides no vorticity bound; one must fall back to diagonal MES plus Einstein constraints, a Bianchi Frobenius coupling, or a prior.

### 8.3 Acceleration bound

Acceleration appears in the \(\ell=1\) MES equation, so it is entangled with dipole handling and local boost.  The production model must separate
\[
\mathcal A_a=A_a/\Theta
\quad\text{from}\quad
\beta_{\rm loc}=v_{\rm loc}/c.
\]
With local boost as nuisance,
\[
\boldsymbol\mu=
\widetilde R_A\boldsymbol{\mathcal A}
+
\widetilde R_{\rm loc}\boldsymbol\beta_{\rm loc}+\n\cdots.
\]
Then
\[
\|\boldsymbol{\mathcal A}\|
\le
\frac{\rho_\alpha}{s_{\min}(P_{\rm loc}^\perp\widetilde R_A)}.
\]
If the projected singular value vanishes, acceleration is not separable from local boost in the selected covariance channels.

### 8.4 Anisotropic-curvature bound

For curvature-bearing Bianchi types, define a finite block \(\boldsymbol\kappa_{\rm aniso}\) with
\[
\Omega_{k,\rm aniso}=\mathcal Q_k(\boldsymbol\kappa_{\rm aniso}).
\]
The response model is
\[
\mathbf s
=R_\kappa\boldsymbol\kappa_{\rm aniso}
+R_\Sigma\boldsymbol\Sigma
+
\text{nuisance}
+
\text{nonlinear terms}.
\]
A curvature bound requires shear and nuisance projection:
\[
\|\boldsymbol\kappa_{\rm aniso}\|
\le
\frac{\rho_\alpha}{s_{\min}(P_{\Sigma,n}^\perp N^{-1/2}R_\kappa)}.
\]
If this projected response is rank-deficient, the correct statement is that anisotropic curvature is not separable from shear in the chosen covariance basis.

---

## 9. Local boost versus global tilt discrimination

### 9.1 Two-template theorem

Let the whitened morphology be
\[
\mathbf y
=
\alpha_{\rm loc}\mathbf r_{\rm loc}
+
\alpha_{\rm tilt}\mathbf r_{\rm tilt}
+
\mathbf n,
\]
where \(\mathbf r_{\rm loc}\) is the local-boost template and \(\mathbf r_{\rm tilt}\) is the global/source-tilt template.  Define
\[
\rho_{\rm loc,tilt}
:=
\frac{\mathbf r_{\rm loc}^T\mathbf r_{\rm tilt}}
{\|\mathbf r_{\rm loc}\|\|\mathbf r_{\rm tilt}\|}.
\]

### Proposition 9.1 — identifiability criterion

The two amplitudes are linearly identifiable if and only if
\[
|\rho_{\rm loc,tilt}|<1.
\]
When \(|\rho_{\rm loc,tilt}|=1\), local boost and global tilt are exactly degenerate in the selected covariance space.

### Proof

The Fisher matrix is
\[
F=
\begin{pmatrix}
\mathbf r_{\rm loc}^T\mathbf r_{\rm loc}
&
\mathbf r_{\rm loc}^T\mathbf r_{\rm tilt}
\\
\mathbf r_{\rm tilt}^T\mathbf r_{\rm loc}
&
\mathbf r_{\rm tilt}^T\mathbf r_{\rm tilt}
\end{pmatrix}.
\]
Its determinant is
\[
\det F
=
\|\mathbf r_{\rm loc}\|^2\|\mathbf r_{\rm tilt}\|^2
-(\mathbf r_{\rm loc}^T\mathbf r_{\rm tilt})^2
=
\|\mathbf r_{\rm loc}\|^2\|\mathbf r_{\rm tilt}\|^2
(1-\rho_{\rm loc,tilt}^2).
\]
Assuming both templates are nonzero, \(F\) is invertible exactly when \(1-\rho^2>0\), i.e. \(|\rho|<1\).  \(\square\)

### 9.2 Physical discrimination channels

Local boost and global tilt can both look dipolar.  They separate only through channels where the templates are not collinear:

1. **Depth/redshift law:** observer-side boost and source/background tilt scale differently with survey depth.
2. **TE/EE/BB morphology:** global tilt changes source/transport; local boost remaps the observed sky.
3. **BiPoSH coupling pattern:** local aberration has a specific \(\ell\leftrightarrow\ell\pm1\) structure; Bianchi tilt can create family-specific extra coupling.
4. **Parity and handedness:** vorticity/screen rotation can generate signatures not reproduced by scalar local boost.
5. **CMB/LSS coherence:** global tilt should correlate with matter-frame observables differently from pure observer remapping.

Production output must report \(\rho_{\rm loc,tilt}\) and injection-recovery leakage.  Geometry claims are blocked when the overlap is too high or mock leakage is not under threshold.

---

## 10. Isotropy/anistropy discrimination framework

Define nested hypotheses:
\[
H_0:
K=K^{(0)}
\quad\text{FLRW statistical isotropy},
\]
\[
H_{\rm kin}:
K=K^{(0)}+
\Delta K_{\rm loc}(\beta_{\rm loc})
\quad\text{local boost only},
\]
\[
H_{\rm tilt}:
K=K^{(0)}+
\Delta K_{\rm tilt}(\beta_{\rm tilt})
\quad\text{global/source tilt without anisotropic spatial geometry},
\]
\[
H_{\rm geom}:
K=K^{(0)}+
\Delta K_{\rm geom}(\Sigma,W,
\mathcal A,
\kappa_{\rm aniso},T)
\quad\text{Bianchi geometry candidate}.
\]

The inference chain should be:

1. Test \(H_0\) with calibrated \(L>0\) covariance power.
2. Project nuisance templates: mask, beam, foreground, scanning law, local boost, survey axis.
3. Separate \(H_{\rm kin}\) and \(H_{\rm tilt}\) using \(\rho_{\rm loc,tilt}\), depth dependence, and channel morphology.
4. Compare \(H_{\rm tilt}\) and \(H_{\rm geom}\) only with direction-inclusive likelihood.
5. Promote to type-family evidence only after matched-complexity, null competition, and injection-recovery leakage gates pass.

Claim tiers:

* **C0:** covariance extraction only.
* **C1:** isotropy tension: calibrated \(L>0\) covariance excess.
* **C2:** anisotropy-like morphology survives nuisance projection.
* **C3:** local/global separation passes overlap and mock leakage gates.
* **C4:** Bianchi geometry candidate under matched-complexity comparison.
* **C5:** type-family evidence with cross-channel/depth consistency.

The forbidden inference is
\[
\text{off-diagonal covariance detected}
\quad\Rightarrow\quad
\text{Bianchi geometry detected}.
\]

---

## 11. Morphological MES theorem

### Theorem 11.1 — full-covariance MES extension

Let
\[
B_j^{\rm diag}
:=
\sup_{\mathbf p\in\mathcal C^{\rm diag}_{\rm MES}}\|\mathbf p_j\|,
\]
\[
B_j^{\rm cov}
:=
\sup_{\mathbf p\in\mathcal C^{\rm lin}_{\rm cov}(\alpha)}\|\mathbf p_j\|,
\]
\[
B_j^{\rm dyn}
:=
\sup_{\mathbf p\in\mathcal C_{\rm dyn}}\|\mathbf p_j\|.
\]
If these suprema are finite, then
\[
\boxed{
B_j^{\rm final}
:=
\sup_{\mathbf p\in
\mathcal C^{\rm diag}_{\rm MES}
\cap
\mathcal C^{\rm lin}_{\rm cov}(\alpha)
\cap
\mathcal C_{\rm dyn}}
\|\mathbf p_j\|
\le
\min\{B_j^{\rm diag},B_j^{\rm cov},B_j^{\rm dyn}\}.
}
\]

### Proof

Let
\[
\mathcal C_*:=
\mathcal C^{\rm diag}_{\rm MES}
\cap
\mathcal C^{\rm lin}_{\rm cov}(\alpha)
\cap
\mathcal C_{\rm dyn}.
\]
Then
\[
\mathcal C_*\subseteq\mathcal C^{\rm diag}_{\rm MES},
\qquad
\mathcal C_*\subseteq\mathcal C^{\rm lin}_{\rm cov}(\alpha),
\qquad
\mathcal C_*\subseteq\mathcal C_{\rm dyn}.
\]
The supremum of \(\|\mathbf p_j\|\) over a subset cannot exceed its supremum over any larger set.  Hence
\[
B_j^{\rm final}\le B_j^{\rm diag},
\qquad
B_j^{\rm final}\le B_j^{\rm cov},
\qquad
B_j^{\rm final}\le B_j^{\rm dyn}.
\]
Therefore
\[
B_j^{\rm final}
\le
\min\{B_j^{\rm diag},B_j^{\rm cov},B_j^{\rm dyn}\}.
\]
\(\square\)

### Corollary 11.2 — morphology information gain

Define
\[
\mathcal I_j^{\rm morph}:=
\frac{B_j^{\rm diag}}{B_j^{\rm final}}.
\]
Then
\[
\mathcal I_j^{\rm morph}\ge1.
\]
Strict inequality occurs exactly when covariance or dynamical/type-specific information removes parameter states allowed by diagonal MES alone.

### Proof

Theorem 11.1 gives \(B_j^{\rm final}\le B_j^{\rm diag}\).  Since both bounds are positive, division gives \(\mathcal I_j^{\rm morph}\ge1\).  Strictness is equivalent to \(B_j^{\rm final}<B_j^{\rm diag}\), i.e. to exclusion by at least one additional constraint.  \(\square\)

---

## 12. Backreaction interpretation

This framework does not by itself prove Buchert-style averaged backreaction.  It proves a sharper and safer statement:
\[
\boxed{
\text{anisotropic background kinematics alter the observable covariance manifold.}
}
\]
The map is
\[
(\Sigma,W,
\mathcal A,
\beta_{\rm tilt},
\kappa_{\rm aniso})
\longmapsto
\Delta K
\longmapsto
A^{LM}_{\ell\ell'}.
\]
Diagonal \(C_\ell\) compression keeps only a scalar projection of this map.  The full covariance extension measures the lost information through \(\mathcal I_j^{\rm morph}\).  A careful manuscript phrase is:

> The full-covariance MES extension quantifies the background-to-photon-covariance response of anisotropic geometry.  It is a backreaction diagnostic in the limited sense that anisotropic background kinematics alter the observable covariance manifold, yielding bounds unavailable from diagonal power spectra alone.

Avoid:

> Off-diagonal covariance proves cosmological backreaction.

That is too strong.

---

## 13. Implementation contracts

### 13.1 BASS theory artifact

Each Bianchi or tilted family should emit a response artifact:

```python
@dataclass(frozen=True)
class CovarianceResponseEntry:
    family: str
    channels: tuple[str, ...]
    ell_min: int
    ell_max: int
    biposh_index: tuple
    parameter_blocks: tuple[str, ...]
    response_matrix: NDArray      # unwhitened R
    theory_covariance: NDArray | None
    validity_radius: float
    nonlinear_remainder_bound: float | None
    frame: str                    # geometry, matter, observer
    production_allowed: bool
    caveats: tuple[str, ...]
```

### 13.2 MIO data artifact

MIO should extract
\[
\widehat{\mathbf s},
\quad N,
\quad
\text{mask/beam/foreground nuisance templates},
\quad
\text{mock calibration reports}.
\]
MIO reports diagnostics and certificates.  It does not own the model-dependent posterior.

### 13.3 HTT inference artifact

HTT receives theory/data artifacts and owns model-dependent posterior/evidence:
\[
\mathcal L_{m cov}
\propto
\exp\left[-\frac{1}{2}
(\widehat{\mathbf s}-\mathbf s_T(\theta))^T
N^{-1}
(\widehat{\mathbf s}-\mathbf s_T(\theta))
\right],
\]
with nuisance projection or marginalization made explicit.

---

## 14. Required gates

A bound is production-eligible only if every gate below passes.

1. **Isotropic limit:** \(R_T=0\) for all anisotropic blocks in the FLRW limit.
2. **Rotation covariance:** scalar conclusions use rotational invariants or correctly transformed likelihoods.
3. **PSD covariance:** \(K^{(0)}+\Delta K\succeq0\).
4. **Mask/mock calibration:** isotropic mocks recover correct coverage.
5. **Nuisance projection:** local boost, mask, beam, foreground, and survey-axis templates are included or shown negligible.
6. **Rank gate:** \(s_{\min}(P_n^\perp\widetilde R_j)>0\) for every block claimed bounded.
7. **Nonlinearity gate:** the claimed confidence region lies within the response validity radius, or the nonlinear likelihood is used.
8. **Claim-tier gate:** geometry claims require direction-inclusive likelihood and injection-recovery leakage below threshold.

---

## 15. Adversarial audit and pruning

### 15.1 Surviving candidates

1. **Shear BiPoSH-MES bound:** most direct and highest priority.
2. **Local/global tilt discrimination:** necessary for separating peculiar velocity from geometry/source tilt.
3. **Vorticity handedness/parity bound:** conditional but valuable because diagonal TT is weak for vorticity.
4. **Anisotropic-curvature response bound:** type-sensitive and requires shear-curvature degeneracy audit.
5. **Morphological information gain:** scalar summary of the information lost by diagonal compression.

### 15.2 Rejected or downgraded claims

1. **“BiPoSH replaces MES.”** Rejected.  It adds a covariance admissible set; it does not replace the all-observer derivative-boundedness theorem.
2. **“Off-diagonal covariance equals Bianchi geometry.”** Rejected.  Mask, beam, foreground, local boost, and survey systematics also generate off-diagonal covariance.
3. **“Diagonal \(C_\ell\) is enough for family identification.”** Rejected.  Family identification requires direction-inclusive \(a_{\ell m}\), BiPoSH, or map likelihood.
4. **“TSC/Teff scalar trace semantics closes full polarization morphology.”** Rejected.  TSC can supply trace/source diagnostics, not full spin-2 transport ownership.
5. **“High-\(\ell\) damping-tail modulation already gives a bound.”** Downgraded.  It needs an explicit tilted-frame Boltzmann covariance template.

---

## 16. Final consistency checks

### 16.1 Dimension check

\(\Sigma,W,
\mathcal A,
\beta,
\Omega_{k,\rm aniso}\) are dimensionless.  \(\widehat{\mathbf s}\) has covariance units before whitening, but
\[
\mathbf y=N^{-1/2}\widehat{\mathbf s}
\]
is dimensionless.  Therefore singular values of \(\widetilde R=N^{-1/2}R\) are dimensionless, and
\[
B_j^{\rm cov}=\rho_\alpha/s_{\min}
\]
is dimensionless.

### 16.2 Isotropic limit check

Set all anisotropic blocks to zero:
\[
\Sigma=W=
\mathcal A=
\beta_{\rm tilt}=
\Omega_{k,
\rm aniso}=0.
\]
Then \(\Delta K=0\), so all \(L>0\) BiPoSH coefficients vanish by Theorem 3.2.  Any solver returning nonzero signal here fails.

### 16.3 Rotation covariance check

Individual \(M\)-components are frame-dependent.  Scalar reporting must use either
\[
\sum_M|A^{LM}_{\ell\ell'}|^2,
\]
a whitened quadratic form
\[
\mathbf s^\dagger N^{-1}\mathbf s,
\]
or a likelihood with correct Wigner rotation behavior.  A single-\(M\) bound without frame convention is invalid.

### 16.4 PSD check

The predicted covariance must satisfy
\[
K^{(0)}+
\Delta K\succeq0.
\]
A necessary two-mode condition is
\[
|K_{ij}|^2\le K_{ii}K_{jj}.
\]
Any response template violating this at claimed amplitude is unphysical.

### 16.5 Diagonal compression check

If all off-diagonal channels are discarded, then \(\widetilde R\) is zero on the morphology vector and
\[
s_{\min}=0.
\]
Corollary 6.3 correctly returns no covariance-derived morphology bound, leaving the diagonal MES bound as the only ceiling.

### 16.6 Local/global degeneracy check

The determinant
\[
\det F
=
\|\mathbf r_{\rm loc}\|^2
\|\mathbf r_{\rm tilt}\|^2
(1-
\rho_{\rm loc,tilt}^2)
\]
vanishes at \(|\rho|=1\).  Therefore the framework has an explicit no-claim condition when local boost and global tilt templates are collinear.

### 16.7 Squared-variable conversion check

From \(H=\Theta/3\),
\[
\frac{\sigma^2}{6H^2}
=
\frac{\sigma^2}{6\Theta^2/9}
=
\frac{3}{2}\frac{\sigma^2}{\Theta^2}.
\]
Thus every bound on \(\sqrt{\sigma_{ab}\sigma^{ab}}/\Theta\) converts to \(\Sigma^2_{\rm std}\) with the factor \(3/2\), not \(1/2\), not \(1\), and not \(3\).

---

## 17. Minimal manuscript insertion paragraph

> The MES hierarchy used above is diagonal in spirit: it converts low multipole amplitudes into algebraic ceilings for \(\sigma/\Theta\), \(\omega/\Theta\), and \(\dot u/\Theta\).  This is conservative but incomplete for Bianchi or tilted backgrounds, because such models also predict off-diagonal harmonic covariance and nonzero BiPoSH coefficients.  Given a solver response \(\mathbf s=R\mathbf p\) for the off-diagonal covariance vector and an empirical covariance \(N\), the whitened response \(\widetilde R=N^{-1/2}R\) yields the bound \(\|\mathbf p_j\|\le\rho_\alpha/s_{\min}(P_n^\perp\widetilde R_j)\) after nuisance projection.  The final admissible ceiling is the intersection of diagonal MES, full-covariance response, and type-specific dynamical constraints.  This construction cannot weaken the original MES bound and quantifies the information gain from anisotropic covariance morphology through \(\mathcal I_j^{\rm morph}=B_j^{\rm diag}/B_j^{\rm final}\).

---

## 18. Immediate research tasks

1. Implement `mio.covariance.biposh_extractor`: map or \(a_{\ell m}\) input \(\to\widehat{\mathbf s},N\).
2. Implement `bass.lowell.covariance_response`: Bianchi/tilted parameters \(\to R_T\).
3. Implement `common.nuisance_projection`: local boost, mask, beam, foreground, survey-axis projection.
4. Implement `mio.bounds.covariance_mes`: singular-value bounds, rank gates, morphology information gain.
5. Implement `htt.discrimination.local_global_overlap`: \(\rho_{\rm loc,tilt}\), Fisher determinant, injection-recovery leakage.
6. Add mock suite: isotropic mocks, local-boost mocks, global-tilt mocks, geometric Bianchi mocks, systematic mocks.
7. Require each reported bound to ship with \(s_{\min}\), \(\rho_\alpha\), nuisance list, \(L_{\max}\), channel list, PSD status, nonlinearity radius, and claim tier.

---

## 19. Bottom line

The final framework is
\[
\boxed{
\text{diagonal MES ceiling}
\;\cap\;
\text{full-covariance BiPoSH response ceiling}
\;\cap\;
\text{Bianchi dynamical admissibility}
}
\]
and it produces rank-certified, nuisance-audited, morphology-aware bounds.  It is the correct next step once the low-\(\ell\) solver can predict direction-inclusive \(a_{\ell m}\), map templates, or covariance responses for each Bianchi family.

---

## Appendix A. Independent algebra spot-check

As a final sanity check, the two central linear-algebra inequalities were tested on random full-rank matrices:

1. no-nuisance inequality
\[
\|R p\|\ge s_{\min}(R)\|p\|;
\]
2. nuisance-projected inequality
\[
\|P_n^\perp R_jp\|\ge s_{\min}(P_n^\perp R_j)\|p\|.
\]

For 2000 random no-nuisance trials and 2000 random nuisance-projection trials, the maximum observed violation was zero to floating-point precision.  This numerical check is not used as a proof—the proofs are already given above—but it catches sign, projection, and singular-value normalization mistakes.
