# Energy-frame derivative order: analytical candidate packet

Date: 2026-09-30. Role: proposer; independent decision is pending. Evidence status of the proofs below is **derived**. No numerical experiment, computer algebra, formal verifier, or Einstein–matter PDE solver is used or needed for the local proofs. Priority and research significance remain **unresolved**.

## 0. Contract, conventions, and source audit

Work in four dimensions with signature (−,+,+,+), length coordinates $x^0=ct$, $[\nabla_c,\nabla_d]v^a=R^a{}_{bcd}v^b$, $\kappa=8\pi G_N/c^4>0$, and constant $\Lambda$. Set $u=U/c$, $g(u,u)=-1$, $h^a{}_b=\delta^a{}_b+u^au_b$, $A=\nabla_UU=c^2\nabla_uu$, and $\theta=\nabla_aU^a$. Use a future orthonormal frame $E_0=u,E_i$. All norms on the rest space and on the frame index $\mu=0,1,2,3$ are positive Euclidean norms, never Lorentzian contractions.

The main source distinction is essential:

* **Unrestricted Einstein-source class:** $T=(G+\Lambda g)/\kappa$ is defined from a chosen metric. Conservation is automatic, but a specified matter EOS/action is absent. EF2–EF3 are in this class, even with strict dominant energy condition (DEC).
* **Fixed matter class:** EF5 constructs actual local solutions of one fixed causal barotropic Einstein–Euler model. EF5c additionally realizes them by one fixed scalar Lagrangian. This is a distinct, stronger assertion, proved below by local ODE existence and direct substitution.

Inspected supplied primary-source portions (identities and full archive provenance are in `../SOURCE_MANIFEST.json`):

| Source | Portions actually inspected | Relation to the claims |
|---|---|---|
| R01: Ellis, Maartens, MacCallum, *Relativistic Cosmology*, 2012 | pp. 91–94, equations (5.8)–(5.15); p. 97, equations (5.37)–(5.40); p. 100, discussion criticizing unrestricted reverse construction of stress | Supports the energy-frame definition, perfect-fluid Euler equations, and sound-speed restriction. **Limits** the physical interpretation of EF2–EF3. Does not establish the new candidate families or priority. |
| R05: Romatschke & Romatschke, *Relativistic Fluid Dynamics In and Out of Equilibrium*, 2019 | pp. 10–12, equations (2.2)–(2.10) | Supports the fluid projection identities and $dp/d\epsilon$ sound-speed formula in $c=1$ units. |
| R06: Andersson & Comer, *Relativistic fluid dynamics: physics for many different scales*, arXiv:2008.12069v1, 27 Aug 2020 | pp. 52–53, equations (5.11)–(5.20); pp. 58–59, equations (5.43)–(5.50) | Supports perfect-fluid thermodynamics/Euler and the distinction between particle and Landau–Lifshitz frames. |
| Earlier packet and blind review | `theory_blind_review_20260930/inputs/A.md`, `reviews/A.md`, the P2/P3 proof and novelty discussion | Starting derivations and review constraints, **not** primary proof of novelty. The cited general eigenvector-sensitivity prior art was not re-opened here. |

The supplied Ellis text uses some energy-condition labels differently from the modern pointwise convention adopted here. Our DEC assertion is independently defined and proved using the type-I criterion $\epsilon>max_i|p_i|$, $\epsilon>0$; it is not inferred from those labels.

## EF1. Exact spectral identity and the optimal common rate budget

**Statement.** Let $T^a{}_b$ be a $C^1$, (g)-self-adjoint stress endomorphism with a normalized future timelike eigenvector field (u): $Tu=-\epsilon u$. Write $S=hT|_{u^\perp}$, $L=S+\epsilon I$, and assume (L) is invertible. With

\[
D_\mu=h(\nabla_{E_\mu}T)u,\qquad
\delta=\min_i|\epsilon+p_i|>0,
\]

where $p_i$ are the spatial eigenvalues, one has

\[
\nabla_{E_\mu}U=-cL^{-1}D_\mu,
\qquad
\mathcal Q:=\frac{\theta^2}{3}+\|\sigma\|_F^2
+2|\omega|^2+\frac{|A|^2}{c^2}
=c^2\sum_{\mu,i}\frac{|D_{\mu i}|^2}{(\epsilon+p_i)^2}
\le\frac{c^2}{\delta^2}\sum_\mu|D_\mu|^2. \tag{1}
\]

Here $D_{\mu i}$ is resolved in a spatial eigenbasis, and $\omega_i=\frac12\varepsilon_{ijk}\omega_{jk}$. Equality in the inequality occurs exactly when each $D_\mu$ lies in the sum of eigenspaces with $|\epsilon+p_i|=\delta$. In particular, **every perfect fluid with $\epsilon+p\ne0$ saturates this gap estimate**; its usefulness is conditional on controlling the derivative input.

**Proof.** Differentiate $Tu=-\epsilon u$, use $\nabla_Xu\perp u$, and project orthogonally to (u). This gives $L\nabla_Xu=-h(\nabla_XT)u$. The rest metric is positive definite and (S) is self-adjoint, so diagonalizing (S) proves the exact sum and the optimal inverse norm $1/\delta$. The spatial matrix $B_{ij}=g(\nabla_{E_i}U,E_j)$ splits orthogonally into trace, symmetric trace-free, and antisymmetric parts. Its squared norm is $\theta^2/3+\|\sigma\|_F^2+2|\omega|^2$. The remaining temporal row has norm $|A|^2/c^2$. This proves (1).

Dimensions: (D) has energy-density/length, $\delta$ energy-density, and $\mathcal Q$ time$^{-2}$. The constant is optimal even in the Einstein-source subclass by EF2 and EF5. The spectral sensitivity principle and fluid decomposition are standard; the identity is not presented as a new perturbation theorem.

## EF2. Sharp conformal family, strict DEC, and no common admissible radius

Fix (b>0), $\Lambda<3b$, and let $\lambda\in\mathbb R$. On a coordinate neighborhood of the origin define

\[
g_\lambda=e^{2\phi_\lambda}\eta,\qquad
\phi_\lambda=-b(x^0)^2-\frac b2\sum_{i=1}^3(x^i)^2
+\frac{\lambda}{2}(x^0)^2x^1,\qquad
T_\lambda=\kappa^{-1}(G[g_\lambda]+\Lambda g_\lambda). \tag{2}
\]

All $g_\lambda$ have the same metric 2-jet at (0). For every finite $\lambda$ there is an open neighborhood of (0) on which $T_\lambda$ obeys strict DEC and has a unique normalized future timelike energy eigenvector. At (0),

\[
\epsilon_0=\frac{6b-\Lambda}{\kappa},\quad
p_{i0}=\frac{\Lambda}{\kappa},\quad
u_0=\partial_0,\quad
\delta_0=\frac{6b}{\kappa},\quad
A^1_0=\frac{c^2\lambda}{3b},\quad
\theta_0=\sigma_0=\omega_0=0. \tag{3}
\]

The spectral estimate (1) is an equality. These local admissible neighborhoods cannot contain one fixed positive coordinate ball for all $\lambda$.

**Direct calculation.** In four dimensions,

\[
G_{ab}=-2\phi_{,ab}+2\phi_{,a}\phi_{,b}
+2\eta_{ab}\Box_\eta\phi+\eta_{ab}(\partial\phi)^2.
\]

At (0), $\phi=d\phi=0$, $\phi_{,ab}=\operatorname{diag}(-2b,-b,-b,-b)$, and $G_{ab}=\operatorname{diag}(6b,0,0,0)$. The only off-diagonal Einstein-derivative entries relevant to (1) are $\partial_0G_{01}=-2\lambda$; all $\partial_iG_{j0}=0$. Hence $D_0^1=-2\lambda/\kappa$, other $D_\mu^i=0$, proving (3) and

\[
\mathcal Q_0=\frac{c^2\lambda^2}{9b^2}
=\frac{c^2}{(6b/\kappa)^2}\frac{4\lambda^2}{\kappa^2}.
\]

Strict DEC at (0) is precisely $6b-\Lambda>|\Lambda|$, equivalent to $\Lambda<3b$. Thus the original $\Lambda=0$ construction works, and the same construction works for any fixed $\Lambda$ after choosing $b>\max(0,\Lambda/3)$. The gap is independent of $\Lambda$.

**Neighborhood assertion.** An isolated timelike eigenline depends smoothly on a smooth (g)-self-adjoint endomorphism near a point where (L) is invertible; this also follows directly from the normalized eigenvector equation and the implicit function theorem, whose spatial linearization is (L). Timelikeness persists. Relative to this branch, the spatial stress is symmetric, its eigenvalues are continuous, and the positive strict-DEC margin persists. This supplies a neighborhood for each finite parameter. Bianchi supplies $\nabla^aT_{ab}=0$ there.

**Exact obstruction to a uniform radius.** Along the fixed slice line $x^0=x^2=x^3=0, x^1=s$, all off-diagonal stress entries vanish. In the conformal orthonormal frame,

\[
\kappa\epsilon=e^{bs^2}(6b-b^2s^2)-\Lambda,\qquad
\kappa p_2=\kappa p_3=e^{bs^2}(b^2s^2-2\lambda s)+\Lambda.
\]

Therefore

\[
\kappa(\epsilon+p_2)=e^{bs^2}(6b-2\lambda s). \tag{4}
\]

At $s=3b/\lambda$ for $\lambda\ne0$, the timelike and transverse spatial eigenvalues coincide. Strict DEC and the isolated eigenframe both fail. Beyond that point with $\lambda s>3b$, even the null energy condition fails in that transverse null direction. Hence any ball centered at (0) throughout which both advertised conditions hold has coordinate radius at most $3b/|\lambda|$. The slice's proper radial distance to this obstruction is $\int_0^{3b/|\lambda|}e^{-bs^2/2}ds\le3b/|\lambda|$, so the shrinking is not only a changing coordinate scale.

No EOS is imposed. At the origin, $\partial_1G_{ij}=-2\lambda\delta_{ij}$ while $\partial_1G_{00}=0$. In particular the family is not Einstein dust or any differentiable barotrope $p=p(\epsilon)$ to first order at (0) when $\lambda\ne0$. Strict DEC does not repair this matter-model limitation.

## EF3. All twelve velocity-derivative directions are realized at a fixed metric 2-jet

This upgrades the one acceleration direction in EF2 to a surjective, explicit metric-third-jet construction. It also answers the Bianchi-obstruction question without a large rank computation.

**Statement.** Fix the metric 2-jet at (0) of

\[
g^{(0)}=e^{2\phi_0}\eta,\qquad
\phi_0=-b(x^0)^2-\frac b2|\mathbf x|^2,\qquad \Lambda<3b.
\]

For every real $4\times3$ matrix $k_{\mu i}$ there is a smooth Lorentzian metric germ (g) with this same 2-jet, such that its Einstein-defined stress obeys strict DEC on some neighborhood and its energy frame satisfies

\[
u(0)=\partial_0,\qquad
g(\nabla_{E_\mu}u,E_i)(0)=k_{\mu i}. \tag{5}
\]

Thus every normalized timelike congruence 1-jet, equivalently every $(\theta,\sigma,\omega,A)$, occurs, with fixed (g)-2-jet, (T(0)), (u(0)), and gap. Each member saturates (1) at (0).

**Construction.** Let $q_i=-6b k_{0i}$, $M_{ij}=-6b k_{ji}$, $S=(M+M^T)/2$, $W=(M-M^T)/2$, and $r^2=\sum_i(x^i)^2$. Set $g=g^{(0)}+H$, where the symmetric cubic perturbation is

\[
H_{00}=0,\qquad
H_{ij}=-\frac12\delta_{ij}x^0S_{kl}x^kx^l,\qquad
H_{0i}=H_{i0}=-\frac12x^0r^2q_i-\frac15r^2W_{ij}x^j. \tag{6}
\]

The metric 2-jet is unchanged, and (g) remains Lorentzian on a sufficiently small neighborhood. Since $\partial g(0)=0$, the change in $\partial G(0)$ is exactly the linear flat principal expression applied to the cubic (H). There are no curvature-times-(H) or connection terms at this jet order, because $j^2H(0)=0$. In particular,

\[
(\delta G)_{0i}
=\frac12\left(\partial_j\partial_0H_{ij}
-\partial_i\partial_0H_{jj}
+\partial_i\partial_jH_{0j}-\Delta H_{0i}\right), \tag{7}
\]

as a homogeneous linear polynomial, is enough to determine the entire relevant derivative.

The three pieces in (6) give respectively

\[
(\delta G)_{0i}=S_{ij}x^j,\qquad
(\delta G)_{0i}=q_i x^0,\qquad
(\delta G)_{0i}=W_{ij}x^j.
\]

For the last identity use $\operatorname{div}(r^2W\mathbf x)=0$ and $\Delta(r^2W\mathbf x)=10W\mathbf x$. For the acceleration piece, $\partial_i\operatorname{div}(x^0r^2q)=2x^0q_i$ and $\Delta(x^0r^2q_i)=6x^0q_i$. For the symmetric piece, $H_{ij}=\delta_{ij}x^0f$, $f=-S_{kl}x^kx^l/2$, gives $-\partial_i f=S_{ij}x^j$.

The baseline has $\partial G(0)=0$. Consequently $\partial_0G_{0i}=q_i$ and $\partial_jG_{0i}=M_{ij}$. Formula (1) with $L=(6b/\kappa)I$ now gives exactly (5). Strict DEC and the isolated branch persist as in EF2.

**Why conservation imposes no lost direction.** Bianchi constrains the full forty-component derivative $\nabla_cT_{ab}$ by four divergence equations. It does not set the twelve chosen mixed derivatives independently to zero. The other stress derivatives generated by (6) automatically supply the required divergences. More fundamentally, the source is defined from an actual smooth metric, so the exact nonlinear Bianchi identity holds everywhere in the germ. Equation (7) also satisfies the linearized Bianchi identity. This establishes realizability, not merely dimension counting.

EF3 is restricted to unrestricted Einstein-defined sources. It is not a statement that twelve independent directions survive any fixed EOS/action. It is an explicit jet-surjectivity candidate whose priority has not been established.

## EF4. What a fixed perfect-fluid Euler equation actually supplies

For a conserved perfect fluid

\[
T_{ab}=(\epsilon+p)u_au_b+pg_{ab},\qquad w=\epsilon+p>0,
\]

the energy and momentum projections give the standard exact equations

\[
U(\epsilon)+w\theta=0,\qquad
A_a=-\frac{c^2}{w}D_ap.\tag{8}
\]

For $p=p(\epsilon)$, define $c_s^2=c^2p'(\epsilon)$. Then

\[
A_a=-\frac{c_s^2}{w}D_a\epsilon. \tag{9}
\]

Thus simultaneous bounds $w\ge w_*>0$, $|D\epsilon|\le M$, and $0\le c_s^2\le c^2$ imply $|A|\le c^2M/w_*$. An EOS and sound-speed bound without a density-gradient bound do not yield that acceleration bound. Equation (8) also gives $|\theta|\le|U(\epsilon)|/w_*$, but these scalar-gradient data alone do not control shear and vorticity.

At one normal-frame event, prescribed $k_{\mu i}=\nabla_\mu u_i$ and $p'(\epsilon_0)=\alpha>0$ satisfy the pointwise Euler equations if

\[
\partial_0\epsilon=-w\sum_i k_{ii},\qquad
\partial_i\epsilon=-\frac{w}{\alpha}k_{0i}.
\]

This is only algebraic compatibility of fluid 1-jets. It does not by itself prove Einstein–Euler realizability. EF5 below supplies a genuine realization for an unbounded acceleration subfamily.

For dust, $p\equiv0$ and $\epsilon>0$ imply $A=0$ identically. The conformal accelerating family cannot be transferred to dust. The same conclusion holds at any state of a differentiable barotrope with $p'=0$. Neither statement makes all remaining fluid derivatives functions of a metric 2-jet.

## EF5. Fixed causal EOS: local Einstein–Euler family with identical curvature and unbounded acceleration

This is the strongest candidate in this packet. Its physical restriction is fixed before solving the equations; the construction is local and exact.

### EF5a. General fixed-\Lambda local family

Fix $\epsilon_0>0$, $0<\alpha<1$, $p_0=\alpha\epsilon_0$, and constants $\mu,\Lambda$ such that

\[
C=2\mu+\Lambda/3>0,\qquad
B=\mu+\kappa p_0/2-\Lambda/3\ne0.\tag{10}
\]

For each $r_0\in(0,C^{-1/2})$, there is a smooth local static spherical solution of the same Einstein–Euler equations, the same $\Lambda$, and the same EOS $p=\alpha\epsilon$, with a chosen event at area radius $r_0$, such that:

1. $\epsilon=\epsilon_0$, $p=p_0$, and the energy gap $w_0=(1+\alpha)\epsilon_0$ at that event are fixed.
2. In identified comoving oriented orthonormal frames, the full Riemann tensor is fixed. Hence the metric 2-jets in the corresponding centered Riemann normal coordinates are identical.
3. $\theta=\sigma=\omega=0$, while

\[
|A|=c^2\frac{|B|r_0}{\sqrt{1-Cr_0^2}}\longrightarrow\infty
\quad \text{as }r_0\uparrow C^{-1/2}. \tag{11}
\]

4. Each member has strict DEC, a unique timelike energy frame, and fixed subluminal sound speed $c_s=c\sqrt{\alpha}$ throughout a sufficiently small open neighborhood.

**Existence and full field equations.** Use the static ansatz

\[
g=-e^{2\nu(r)}(dx^0)^2+\frac{dr^2}{F(r)}+r^2d\Omega^2,\qquad
F=1-\frac{2m(r)}r-\frac{\Lambda r^2}{3},\qquad
u=e^{-\nu}\partial_0. \tag{12}
\]

Here (m) has length units. Solve the first-order ODE system

\[
m'=\frac{\kappa}{2}r^2\epsilon,\qquad
\nu'=\frac{m+\kappa\alpha\epsilon r^3/2-\Lambda r^3/3}{r^2F},\qquad
\epsilon'=-\frac{1+\alpha}{\alpha}\epsilon\nu', \tag{13}
\]

with initial values

\[
m(r_0)=\mu r_0^3,\qquad \epsilon(r_0)=\epsilon_0,\qquad \nu(r_0)=0. \tag{14}
\]

At each allowed initial point $F_0=1-Cr_0^2>0$. The right side of (13) is smooth, indeed analytic, on $r>0,F>0,\epsilon>0$. The ordinary local existence theorem therefore gives an exact solution on some interval $r_0-\eta<r<r_0+\eta$, with all these inequalities preserved. Restricting to an angular coordinate patch and a time interval gives an open spacetime neighborhood.

For completeness the independent Einstein density/radial-pressure identities for (12) are

\[
\kappa\epsilon=\frac{1-F-rF'}{r^2}-\Lambda,\qquad
\kappa p_r=\frac{F-1+2rF\nu'}{r^2}+\Lambda. \tag{15}
\]

They follow directly from the spherical metric connection and are exactly the first and second equations of (13). The Einstein-defined source is diagonal and spherical, with two equal angular pressures $p_t$. Its radial Bianchi equation is

\[
p_r'=-(\epsilon+p_r)\nu'+\frac2r(p_t-p_r). \tag{16}
\]

The last ODE in (13) gives $p_r'=\alpha\epsilon'=-(\epsilon+p_r)\nu'$. Since (r>0), (16) forces $p_t=p_r=\alpha\epsilon$. Thus **all** Einstein components and Euler equations hold. This is not the arbitrary reverse-source procedure of EF2–EF3: the fixed EOS and isotropic stress are satisfied on an open set by an existence construction.

The strict-DEC criterion is immediate: $\epsilon>|p|=\alpha\epsilon$ for $\epsilon>0$. The gap is $w=(1+\alpha)\epsilon>0$, so the future normalized energy frame is unique. The sound speed is $c_s^2=c^2 dp/d\epsilon=\alpha c^2$.

**Acceleration and kinematics.** In the orthonormal frame

\[
E_0=e^{-\nu}\partial_0,\quad E_1=\sqrt F\partial_r,\quad
E_2=r^{-1}\partial_\vartheta,\quad
E_3=(r\sin\vartheta)^{-1}\partial_\varphi,
\]

one has $\nabla_{E_i}u=0$, and $\nabla_uu=\sqrt F\nu' E_1$. Therefore the spatial rate matrix vanishes, and (13) gives (11). For these perfect fluids, (1) is saturated; the growing input is the density/pressure gradient, not a vanishing gap.

**Full curvature matching.** The independent nonzero orthonormal Riemann components, with those generated by Riemann symmetries understood, are

\[
\begin{aligned}
R_{0101}&=\frac{\kappa}{2}(\epsilon_0+p_0)-2\mu-\Lambda/3,\\
R_{0202}=R_{0303}&=\mu+\kappa p_0/2-\Lambda/3,\\
R_{1212}=R_{1313}&=\kappa\epsilon_0/2-\mu+\Lambda/3,\\
R_{2323}&=2\mu+\Lambda/3.
\end{aligned} \tag{17}
\]

For a direct check, the last three expressions follow from

\[
R_{0202}=F\nu'/r,\quad
R_{1212}=-F'/(2r),\quad
R_{2323}=(1-F)/r^2,
\]

and the first follows from $R_{00}=\kappa(\epsilon+3p)/2-\Lambda=R_{0101}+2R_{0202}$. All mixed components vanish by the static spherical connection. Thus every component in (17) is independent of $r_0$. In normal coordinates centered at the selected event and initialized with the above frame,

\[
g_{ab}(y)=\eta_{ab}-\frac13R_{acbd}(0)y^cy^d+O(|y|^3).
\]

This establishes equality of the complete metric 2-jets, including $u(0)=\partial_{y^0}$, rather than merely equality of curvature scalar invariants. The normal charts and their domains may depend on $r_0$; the fixed jet assertion requires no common chart radius.

### EF5b. Transparent conformally flat-at-the-event choice

Take $\Lambda=0$, $\mu=\kappa\epsilon_0/6$. Then

\[
C=\frac{\kappa\epsilon_0}{3}>0,\qquad
B=\frac{\kappa\epsilon_0(1+3\alpha)}6>0,
\]

and (17) reduces to

\[
R_{0i0j}=B\delta_{ij},\qquad
R_{ijkl}=C(\delta_{ik}\delta_{jl}-\delta_{il}\delta_{jk}),\qquad
R_{0ijk}=0. \tag{18}
\]

The Weyl tensor vanishes at the event. The acceleration is still

\[
|A|=\frac{c^2\kappa\epsilon_0(1+3\alpha)r_0}
{6\sqrt{1-\kappa\epsilon_0r_0^2/3}},
\qquad0<r_0<\sqrt{\frac3{\kappa\epsilon_0}}, \tag{19}
\]

and is unbounded. This does not make the neighborhood conformally flat. For example the Weyl amplitude $W=m/r^3-\kappa\epsilon/6$ obeys at the chosen point

\[
W'=\frac{\kappa\epsilon_0}{2r_0}-\frac{3\mu}{r_0}
-\frac{\kappa\epsilon'}6
=-\frac{\kappa\epsilon'}6\ne0,
\]

because (B>0) makes $\nu'>0,\epsilon'<0$. At the special event (18) is spatially rotation invariant, so the identified initial spatial frame can align its first axis with any prescribed acceleration direction without changing the common 2-jet. Equation (19) ranges continuously from (0) as a limit at $r_0\downarrow0$ to infinity; every strictly positive magnitude occurs. No claim of an $r_0=0$ member is made.

### EF5c. One fixed scalar Lagrangian realizes the same family

If an explicit common matter Lagrangian is desired, fix $P_*>0$ and

\[
P(X)=P_*X^s,\qquad
X=-\frac12g^{ab}\partial_a\psi\partial_b\psi>0,\qquad
s=\frac{1+\alpha}{2\alpha}>1.\tag{20}
\]

The stress and field equation obtained by variation are

\[
T_{ab}=P_X\partial_a\psi\partial_b\psi+Pg_{ab},\qquad
\nabla_a(P_X\nabla^a\psi)=0.\tag{21}
\]

For every member of (12)–(14), take the same field-coordinate expression $\psi=qx^0$, where the fixed (q>0) is chosen so that $P_*(q^2/2)^s=p_0$. Then $X=(q^2/2)e^{-2\nu}$, $u_a=-\partial_a\psi/\sqrt{2X}$, and

\[
p=P,\qquad \epsilon=2XP_X-P=(2s-1)P=\frac P\alpha,\qquad
\epsilon=\epsilon_0e^{-2s\nu}.
\]

This is precisely the density solved by (13). The current $P_X\nabla^a\psi$ has only a time component; it and the metric determinant are time independent, so the scalar equation in (21) holds identically. Both $P_X>0$ and $P_X+2XP_{XX}>0$, and the linear sound-speed ratio is

\[
\frac{c_s^2}{c^2}=\frac{P_X}{P_X+2XP_{XX}}=\frac1{2s-1}=\alpha.
\]

Thus one fixed (P(X)) theory, not a parameter-dependent matter action, realizes the entire family on its timelike-gradient domain. This is an explicit matter-model construction, not a claim about every microscopic matter theory, shock development, global stability, or completeness.

### Scope and the dust limit

No regular center, asymptotic region, boundary matching, complete static star, global horizon, or uniform neighborhood is asserted. In particular $r_0\uparrow C^{-1/2}$ is a limit of **different local germs**, each with $F_0>0$; the limiting degenerate point is not included. Divergence of (11) cannot be interpreted as the surface acceleration of an admissible sequence of globally regular stars without additional work. The family does establish the intended local differential-order obstruction within a fixed, causal, strict-DEC matter class.

The limit $\alpha\downarrow0$ is singular in (13) and (20). Dust obeys $A=0$ by (8), so this is not an accelerating Einstein-dust construction.

## Consequences, evidence boundaries, and novelty ceiling

* An isolated total-stress energy frame and its first derivative are determined by the metric 3-jet (with fixed (\Lambda,\kappa) and future orientation), because (T) uses two metric derivatives and $\nabla T$ uses three. This is a conditional geometric sufficiency statement, not a data-reconstruction theorem.
* A metric 2-jet, fixed stress, fixed positive gap, and strict DEC do not bound **any direction collectively** in the unrestricted Einstein-source class: EF3 realizes the full twelve-dimensional space. EF2 explicitly shows the loss of any common strict-DEC/isolated-frame radius.
* More substantially, metric 2-jets do not even uniformly bound acceleration within the fixed causal EOS $p=\alpha\epsilon$, and even within the fixed scalar theory (20), in the class of local smooth germs constructed in EF5. This removes the arbitrary-source objection for that acceleration/order obstruction.
* The fixed-EOS result does not imply a full twelve-direction theorem for Einstein–Euler. That stronger claim is **unresolved and not asserted**. The dust acceleration case is false, not merely unproved.
* EF1 and EF4 are standard eigenvector sensitivity and Euler conservation identities. EF2 is an explicit sharp counterexample already checked in the earlier blind review. EF3 and EF5 supply new derivations within this session; this is not evidence that they are absent from the literature. Static spherical/TOV equations, local ODE existence, curvature decompositions, and (P(X)) perfect fluids are standard antecedents. The possible contribution is the matched-full-curvature, fixed-matter, unbounded-acceleration **assembly and its differential-order conclusion**. Exact priority and sufficient novelty for a research paper remain for external source audit and independent decision.

Only the local analytical claims above are ready for independent proof review. No statistical inference, observational noise model, cosmological Bianchi classification, or physical identification of distinct matter components is imported.
