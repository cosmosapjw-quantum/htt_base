# Part II. What the observable tensors retain

## 4. Rotations, invariant information and reconstruction

### 4.1 A pattern and its rotated copies

A proper rotation is a real matrix \(R\) satisfying \(R^TR=I\) and \(\det R=1\). The collection of such matrices is the group \(SO(3)\). Allowing determinant \(-1\) gives \(O(3)\), which also contains reflections. We keep this distinction because a reflection can reverse handedness without changing many ordinary scalar summaries.

Under a rotation,

\[
Q\longmapsto RQR^T,\qquad
O_{ijk}\longmapsto R_{ia}R_{jb}R_{kc}O_{abc}.
\tag{4.1}
\]

The orbit of \((Q,O)\) is the set of all its rotated copies. An invariant has the same value on an orbit. A collection of invariants separates orbits on a specified domain if equal invariant values imply that the two states are related by a proper rotation. This does not mean that it generates every invariant polynomial, nor that it supplies independent coordinates without algebraic relations.

A useful invariant description should permit reconstruction, at least on a clearly identified domain. Let us construct one rather than infer its existence from a dimension count.

### 4.2 Amplitudes, a contraction vector and a Krylov frame

For nonzero tensors define

\[
A_Q=\sqrt{Q:Q},\quad A_O=\sqrt{O:O},\quad
q=Q/A_Q,\quad o=O/A_O,\quad v_i=o_{ijk}q_{jk}.
\tag{4.2}
\]

The amplitudes have temperature units; \(q,o,v\) are dimensionless. The vector \(v\) transforms as an ordinary spatial vector because all contracted rotation matrices cancel in pairs. It is not a physical velocity.

Form the ordered matrix

\[
K=[v,qv,q^2v].
\tag{4.3}
\]

Such a matrix is called a Krylov matrix: it collects a vector and its successive images under a linear operator. We call a pair cyclic here when \(A_Q,A_O>0\) and \(\det K\ne0\). Then these three vectors form a basis of space.

**Proposition 4.1 — cyclicity criterion.** In an orthonormal eigenframe of \(q\),

\[
\det K=v_1v_2v_3\prod_{i<j}(\lambda_j-\lambda_i).
\tag{4.4}
\]

Thus cyclicity is equivalent to three distinct quadrupole eigenvalues and a nonzero contraction component along each eigenvector.

**Proof.** In that frame,
\(K=\operatorname{diag}(v_1,v_2,v_3)V\), where the rows of \(V\) are \((1,\lambda_i,\lambda_i^2)\). Subtract the first row from the second and third, factor their eigenvalue differences, and expand the remaining \(2\times2\) determinant. It gives \(\lambda_3-\lambda_2\), proving Eq. (4.4). Nonzero factors are necessary and sufficient. \(\square\)

Repeated eigenvalues or a zero contraction component are therefore genuine boundaries of this coordinate chart. An arbitrary choice of a missing axis would change the construction rather than complete its proof.

### 4.3 The invariant packet

Define

\[
s_2=\operatorname{tr}q^2=1,\quad s_3=\operatorname{tr}q^3,\quad
\mu_r=v^Tq^rv\quad(r=0,1,2),\quad\chi=\det K,
\tag{4.5}
\]

and the ten distinct symmetric trilinears

\[
\tau_{ijk}=o(q^iv,q^jv,q^kv),\qquad0\le i\le j\le k\le2.
\tag{4.6}
\]

The arguments \(0,1,2\) in \(\tau\) label powers of \(q\), not spatial axes. There are ten unordered triples. Together with the amplitudes, these values give more entries than the number of independent shape parameters. Redundancy allows us to test whether an arbitrary numerical packet really comes from a tensor pair.

Every entry except the signed-volume distinction is invariant under all orthogonal frame changes. Under an improper rotation, \(\chi\) changes by the determinant of that transformation. It is a pseudoscalar: invariant under proper rotations and sign-changing under reflection.

### 4.4 Recovering the Gram matrix

For a trace-free symmetric \(3\times3\) matrix, the eigenvalues satisfy
\(\lambda_1+\lambda_2+\lambda_3=0\),
\(\sum_{i<j}\lambda_i\lambda_j=-s_2/2\), and
\(\lambda_1\lambda_2\lambda_3=s_3/3\).
The last identity follows from \(a^3+b^3+c^3-3abc=(a+b+c)(a^2+b^2+c^2-ab-bc-ca)\).
The characteristic polynomial is consequently
\(z^3-(s_2/2)z-s_3/3\). Diagonalise \(q\) and apply this polynomial to each eigenvalue. This proves the required form of Cayley–Hamilton without an additional matrix theorem:

\[
q^3=\frac{s_2}{2}q+\frac{s_3}{3}I.
\tag{4.7}
\]

Multiplying by \(v^T\) and \(v\), and then by one further \(q\), gives

\[
\mu_3=\frac{s_2}{2}\mu_1+\frac{s_3}{3}\mu_0,\qquad
\mu_4=\frac{s_2}{2}\mu_2+\frac{s_3}{3}\mu_1.
\tag{4.8}
\]

Thus the packet determines the Gram matrix

\[
G=K^TK=
\begin{pmatrix}
\mu_0&\mu_1&\mu_2\\
\mu_1&\mu_2&\mu_3\\
\mu_2&\mu_3&\mu_4
\end{pmatrix},\qquad \det G=\chi^2.
\tag{4.9}
\]

On the cyclic domain it is positive definite, since \(x^TGx=\|Kx\|^2>0\) for nonzero \(x\).

### 4.5 Why a Cholesky convention is needed

A matrix satisfying \(B^TB=G\) is not unique. Multiplication on the left by any orthogonal matrix preserves this equation. A determinant condition alone still leaves all proper rotations. We use the unique upper-triangular positive-diagonal Cholesky factor from Section 2,

\[
B_+^TB_+=G,
\quad S_\chi=\operatorname{diag}(1,1,\operatorname{sgn}\chi),
\quad B=S_\chi B_+.
\tag{4.10}
\]

Then \(B^TB=G\) and \(\det B=\chi\), because \(\det B_+=\sqrt{\det G}=|\chi|\). We have specified a deterministic convention rather than leaving an unspoken rotation freedom.

With the coordinate basis \(e_0,e_1,e_2\) for the three columns of \(K\), define

\[
C=\begin{pmatrix}0&0&s_3/3\\1&0&s_2/2\\0&1&0\end{pmatrix}.
\tag{4.11}
\]

Equation (4.7) implies \(qK=KC\). The proposed representative is

\[
q_{\rm can}=BCB^{-1},\qquad
(o_{\rm can})_{abc}
=(B^{-1})_{ia}(B^{-1})_{jb}(B^{-1})_{kc}\,\tau_{ijk},
\tag{4.12}
\]

where the ten trilinears are extended to all index orderings by symmetry.

**Theorem 4.2 — reconstruction on the nonzero cyclic image.** A packet obtained from a nonzero cyclic real STF2/STF3 pair determines that pair up to one proper rotation. Equations (4.8)–(4.12) give a representative.

**Proof.** Put \(U=KB^{-1}\). Then
\(U^TU=B^{-T}GB^{-1}=I\) and
\(\det U=\det K/\det B=1\), so \(U\in SO(3)\).
From \(qK=KC\), we obtain \(q=Uq_{\rm can}U^T\).
The trilinears are evaluations of \(o\) on the basis columns of \(K\). A trilinear form is determined by its values on a basis, so changing those basis coordinates using \(K=UB\) yields
\(o=U^{\otimes3}o_{\rm can}\).
The reconstructed tensors inherit symmetry, trace-freeness and unit norms because they are rotated copies of the original pair. Restoring \(A_Q,A_O\) recovers their amplitudes.

If two cyclic pairs have the same packet, they construct the same \(B,C,o_{\rm can}\). Their matrices \(U_1,U_2\) differ by the proper rotation \(U_2U_1^T\), which maps one pair to the other. This proves separation. \(\square\)

The theorem assumes the packet belongs to the forward image. It does not say that every list of numbers satisfying only \(\det G=\chi^2\) is valid. In particular, an implementation must test that the reconstructed tensor is STF and correctly normalised and that

\[
\boxed{o_{\rm can}:q_{\rm can}=Be_0}
\tag{4.13}
\]

holds. It must also recompute the complete packet. These are consistency checks on one reconstructed object, not independent opportunities to replace an invalid input by a nearby projection.

One useful direct check is that \(GC=C^TG\), using Eq. (4.8). Multiplying this identity by the appropriate inverse Cholesky factors shows \(BCB^{-1}\) is symmetric. Its trace and quadratic trace are those of \(C\). Nevertheless, trace and norm constraints on the reconstructed octupole do not follow for arbitrary trilinears; they must still be checked.

### 4.6 A worked mirror example

Take the unnormalised quadrupole \(Q=\operatorname{diag}(1,2,-3)\). Specify the ten independent octupole entries by

\[
\begin{array}{c|rrrrrrrrrr}
ijk&111&112&113&122&123&133&222&223&233&333\\\hline
O_{ijk}&1&2&3&4&5&-5&6&7&-8&-10
\end{array}
\tag{4.14}
\]

All permutations have the same value. The three traces are \(1+4-5=0\), \(2+6-8=0\), and \(3+7-10=0\). Multiplicity-weighted summation gives \(Q:Q=14\) and \(O:O=788\). Direct contraction gives

\[
O:Q=(24,38,47).
\tag{4.15}
\]

The eigenvalues are distinct and all three components are nonzero, so normalising does not destroy cyclicity. The unnormalised determinant is
\(24\cdot38\cdot47\,(2-1)(-3-1)(-3-2)=857280\ne0\).

Apply spatial inversion \(R=-I\). It leaves \(Q\) unchanged and sends \(O\) to \(-O\). The four scalars
\(Q:Q\), \(O:O\), \(\operatorname{tr}Q^3\), and \(Q_{ij}O_{ikl}O_{jkl}\) are unchanged. In contrast, \(v\mapsto-v\) and \(\chi\mapsto-\chi\). No proper rotation can connect the two pairs, because it would have to preserve \(\chi\). This proves that the named four-scalar summary does not separate this mirror pair. It says nothing about every possible invariant collection.

### 4.7 Dimension and numerical refusal

A cyclic pair has no nontrivial proper-rotation stabiliser. If a rotation fixes \(Q\) and \(O\), it fixes \(v,qv,q^2v\); since these form a basis, it is the identity. The local rotation freedom therefore has three independent parameters. The twelve-dimensional tensor-pair space has a nine-dimensional quotient on this domain. Equivalently, two amplitudes and seven normalised shape parameters remain. The smooth Cholesky frame supplies a local separation of these rotation parameters from the shape; the dimension statement is not extended through singular strata.

The exact inverse in Eq. (4.12) can magnify numerical errors when \(K\) is poorly conditioned. The retained numerical method instead expands \(o\) in a Frobenius-orthonormal seven-element STF3 basis, evaluates its ten trilinears, and solves the resulting row-scaled \(10\times7\) least-squares system. For invertible \(K\), that design has rank seven: a trilinear form vanishing on all triples of a basis vanishes everywhere. Numerical rank and accuracy, however, need a finite tolerance and conditioning domain. A typed refusal reports that the chosen inverse chart is unavailable; it is not a reconstructed zero tensor.

This completes the observable problem on the stated domain. We next ask what the physical tensors mean.

# Part III. Physical kinematics and conditional isotropy bounds

## 5. Observers, motion and the physical state

### 5.1 A spacetime observer and its rest space

Spacetime indices \(a,b,c\) run from 0 to 3. The metric has signature \((-,+,+,+)\). An observer direction \(u^a\) is future-directed and unit timelike, \(u^au_a=-1\). If proper time is measured in seconds, the physical four-velocity is \(cu^a\). This convention keeps the speed of light explicit.

The projector onto the observer's instantaneous rest space is

\[
h_{ab}=g_{ab}+u_au_b.
\tag{5.1}
\]

Indeed, \(h_{ab}u^b=0\), and \(h_a{}^ch_c{}^b=h_a{}^b\). The restriction of \(h\) to that rest space is positive definite. Spatial Euclidean formulas used earlier apply in an orthonormal frame in this space.

The covariant derivative \(\nabla\) differentiates tensors while accounting for the variation of the coordinate basis. For example,
\(\nabla_aX^b=\partial_aX^b+\Gamma^b{}_{ac}X^c\), where the Levi-Civita connection is
\(\Gamma^a{}_{bc}=\tfrac12g^{ad}(\partial_bg_{dc}+\partial_cg_{bd}-\partial_dg_{bc})\).
It preserves the metric. We use a dot for \(u^a\nabla_a\), and \(D\) for projecting both the derivative index and every free tensor index into the rest space. These definitions fix the geometric, inverse-length rate convention; physical inverse-time rates are obtained by multiplying by \(c\).

### 5.2 Expansion, shear, rotation and acceleration

Define

\[
A_a=u^b\nabla_bu_a,\quad
\Theta=D_au^a,\quad H_g=\Theta/3,\quad
\sigma_{ab}=D_{(b}u_{a)}-H_gh_{ab},\quad
\omega_{ab}=\tfrac12(D_bu_a-D_au_b).
\tag{5.2}
\]

The derivative decomposition is

\[
\nabla_bu_a=H_gh_{ab}+\sigma_{ab}+\omega_{ab}-A_au_b.
\tag{5.3}
\]

To prove it, differentiate \(u^au_a=-1\), so the first index of \(\nabla_bu_a\) is spatial. Split its second index with \(\delta_b{}^c=h_b{}^c-u_bu^c\). The spatial part then splits uniquely into its trace, symmetric trace-free and antisymmetric parts. These are exactly the definitions in Eq. (5.2).

Expansion changes all lengths at the same local fractional rate. Shear changes relative lengths along different directions without contributing to that trace. Vorticity is local rotation, and acceleration measures departure from geodesic motion. Their component counts are one, five, three and three. An observer family is called geodesic here when \(A_a=0\).

Fix a spatial orientation \(\epsilon_{123}=+1\). The vorticity vector is
\(\omega^a=\tfrac12\epsilon^{abc}\omega_{bc}\), with inverse
\(\omega_{ab}=\epsilon_{abc}\omega^c\). Therefore

\[
\omega_{ab}\omega^{ab}=2\omega_a\omega^a.
\tag{5.4}
\]

This factor prevents a vector norm from being silently substituted for an antisymmetric-tensor norm. It follows by contracting two Levi-Civita symbols, \(\epsilon_{abc}\epsilon^{abd}=2\delta_c{}^d\).

A polar vector changes by \(R\) under an orthogonal transformation. An axial vector changes by \((\det R)R\). Vorticity is axial because its definition uses the orientation tensor. Hence the dot product of a physical velocity with vorticity is a pseudoscalar. This is a precise parity statement, not an inference that a particular parity signal has been observed.

### 5.3 Photon energy and sky direction

For future-directed null momentum \(p^a\), the measured energy is

\[
E_\gamma=-c\,p_au^a>0.
\tag{5.5}
\]

Define \(e^a=cp^a/E_\gamma-u^a\). Direct contraction gives \(u\cdot e=0\) and \(e\cdot e=1\). Conversely,

\[
p^a=\frac{E_\gamma}{c}(u^a+e^a)
\tag{5.6}
\]

has \(p^2=0\) and energy Eq. (5.5). The photon propagates along \(e\); the outward direction on the observer's sky is \(n=-e\). This sign is used in the Doppler formula of Section 9.

These elementary identities follow from local metric contractions. They do not require solving a photon geodesic or specifying the full spacetime history.

### 5.4 Which velocity relates which frames?

We distinguish radiation, matter and observer frames. Write \(\beta_{\rm RO}\), \(\beta_{\rm RM}\), and \(\beta_{\rm MO}\) for radiation–observer, radiation–matter and matter–observer relative velocities divided by \(c\). The direction of each relative velocity is fixed by this convention. At first order in small velocities,

\[
\beta_{\rm RO}^a=\beta_{\rm RM}^a+\beta_{\rm MO}^a+O(\beta^2).
\tag{5.7}
\]

To see the order, a boost matrix has the form \(I+\beta_iK_i+O(\beta^2)\), where \(K_i\) mixes the time component and spatial component \(i\). Multiplying two such matrices adds the linear terms; products of velocities first appear at second order. This proves the stated first-order composition, not an exact three-vector addition law.

The word velocity here concerns physical frames. It is not the contraction vector \(v=o:q\) in Section 4. A temperature response to \(\beta_{\rm RO}\) does not determine the other two terms in Eq. (5.7) without further information.

### 5.5 Geometry and functionals

For later interpretation we retain a physical state with three groups: congruence kinematics \((\sigma_{ab},\omega_a,A_a)\), the specified frame velocities, and geometry or matter quantities supplied by a chosen model. The core geometry coordinate \(\Delta\Omega_k\) denotes a signed scalar curvature-budget difference in that model; it is not the anisotropic curvature tensor. Its numerical definition must be supplied with the model, and an unavailable definition is not replaced by zero.

Where a spatial hypersurface is specified, its trace-free Ricci tensor is \({}^{(3)}S_{ab}={}^{(3)}R_{ab}-\tfrac13{}^{(3)}R h_{ab}\). This refers to that hypersurface; a vortical congruence need not have orthogonal rest spaces fitting into such hypersurfaces. The electric and magnetic Weyl tensors are projections of the trace-free spacetime curvature, \(E_{ab}=C_{acbd}u^cu^d\) and \(H_{ab}=\tfrac12\epsilon_{acd}C^{cd}{}_{be}u^e\), with the stated orientation. Anisotropic stress is \(\pi_{ab}=T_{\langle ab\rangle}\). They are optional STF2 blocks, not quantities inferred in this report. The Weyl tensor itself is

\[
C_{abcd}=R_{abcd}-\tfrac12(g_{ac}R_{bd}-g_{ad}R_{bc}-g_{bc}R_{ad}+g_{bd}R_{ac})
+\tfrac16R(g_{ac}g_{bd}-g_{ad}g_{bc}).
\tag{5.8}
\]

Here curvature is defined by \([\nabla_c,\nabla_d]X^a=R^a{}_{bcd}X^b\), and the Ricci tensor and scalar are its contractions. These definitions suffice to identify the optional blocks; no field equation for them is solved below. The covariant background follows the conventions of [@ELLIS_VAN_ELST_1999].

If \(\beta_{\rm RO}\) is treated as the derived first-order relation, the unconstrained core has
\(5+3+3+3+3+1=18\) raw components. On a locally free rotation stratum its quotient has dimension 15. Imposing the geodesic condition removes three components, giving 15 raw and 12 quotient components on such a stratum. Each optional STF2 block adds five raw components before any dynamical constraints. These are parameter counts, not counts of Einstein-equation solutions or identified parameters.

A physical functional is a specified map \(\phi\) of this state. Examples are \(\operatorname{tr}\sigma^2\), \(\operatorname{tr}\sigma^3\), \(\omega_a\omega^a\), \(\beta_{\rm RM}\cdot\omega\), and \(\beta_{\rm RM}^a\sigma_{ab}\beta_{\rm RM}^b\). The first shear invariant records a magnitude; the cubic invariant carries shape information. Each functional must retain its frame, congruence, epoch, scale and units. Defining it does not measure it.

## 6. What MES bounds do and do not imply

### 6.1 The physical input is conditional

The Maartens–Ellis–Stoeger programme links almost-isotropic freely propagating radiation to restrictions on spacetime kinematics under explicit assumptions. The retained application concerns an expanding domain, a declared geodesic matter congruence, Einstein–Liouville dynamics, almost-isotropy for all relevant fundamental observers, and bounds on spatial and temporal derivatives of radiation multipoles. A single local temperature map does not establish the all-observer or derivative premises. The original and improved analyses and their COBE-era normalisation are the physical sources. [@MES_1995_LIMITS; @MES_1995_IMPROVED; @SAG_1999_COBE]

To state exactly what is supplied, let \(\tau_{A_\ell}\) be the fractional-temperature PSTF multipole field, where \(A_\ell\) denotes \(\ell\) spatial indices. Write \(\epsilon_\ell\) for a bound on its full tensor norm. Dimensionless derivative bounds are denoted by \(\epsilon_\ell^*\), \(\epsilon_\ell'\), \(\epsilon_\ell^{\prime *}\), and \(\epsilon_\ell^{\prime\prime}\); one derivative is normalised by \(\Theta\), two by \(\Theta^2\). A star means a derivative along \(u\), and a prime means a projected spatial derivative. These are derivative-envelope parameters, not derivatives of the scalar numbers \(\epsilon_\ell\).

**Physical input M — retained MES derivative estimates.** On the stated branch, the following norm bounds are supplied by the radiation–geometry analysis:

\[
\frac{\|\sigma\|_F}{\Theta}
<\frac83\epsilon_2+\epsilon_2^*+5\epsilon_1'
+\frac97\epsilon_3',
\qquad
\frac{\|\omega_{ab}\|_F}{\Theta}
<9\epsilon_1'+3\epsilon_1^{\prime *}+\frac65\epsilon_2^{\prime\prime}.
\tag{6.1}
\]

The amplitude-only application further adopts the characteristic-derivative estimates

\[
\epsilon_2^*\le\epsilon_2/3,\quad
\epsilon_1'\le\epsilon_1/3,\quad
\epsilon_3'\le\epsilon_3/3,\quad
\epsilon_1^{\prime *}\le\epsilon_1/9,\quad
\epsilon_2^{\prime\prime}\le\epsilon_2/9.
\tag{6.2}
\]

In their original physical use these substitutions are scale assumptions about the variation of the radiation field. They are not forced by small multipole amplitudes. Equations (6.1)–(6.2) make the input of our conditional deduction explicit. We do not relabel their full Einstein–Liouville derivation as a theorem proved here.

**Proposition 6.1 — the retained amplitude ceilings.** Conditional on M,

\[
\frac{\|\sigma\|_F}{\Theta}<B_\sigma
:=\frac53\epsilon_1+3\epsilon_2+\frac37\epsilon_3,
\qquad
\frac{\|\omega_{ab}\|_F}{\Theta}<B_\omega
:=\frac{10}{3}\epsilon_1+\frac{2}{15}\epsilon_2.
\tag{6.3}
\]

**Proof.** Insert Eq. (6.2) into Eq. (6.1). The quadrupole coefficient in the shear bound is \(8/3+1/3=3\), the dipole coefficient is \(5/3\), and the octupole coefficient is \((9/7)/3=3/7\). For vorticity, \(9/3+3/9=10/3\), and \((6/5)/9=2/15\). All coefficients and norm envelopes are nonnegative, so these substitutions preserve the upper-bound direction. \(\square\)

This is the full coefficient reduction used in the report. It is exact arithmetic under the stated derivative estimates, not a proof that the derivative estimates hold in our Universe. Treating a characteristic-time estimate as an unconditional measured bound would remove a physical premise without justification.

### 6.2 Connecting multipole powers and physical-sector norms

From Proposition 3.3, the corresponding local normalisers are

\[
\epsilon_2=\frac{\sqrt{Q:Q}}{T_0}
=\frac1{T_0}\sqrt{\frac{75C_2}{8\pi}},\qquad
\epsilon_3=\frac{\sqrt{O:O}}{T_0}
=\frac1{T_0}\sqrt{\frac{245C_3}{8\pi}}.
\tag{6.4}
\]

Using these as the all-observer envelopes in M requires the declared extension premise. The residual dipole \(\epsilon_1\) also requires an attribution scenario. Setting it to zero does not follow merely from removing a measured Doppler dipole.

Let \(H=\Theta/3>0\) in the common geometric rate convention. Define

\[
\psi_\sigma=\frac{\sigma_{ab}\sigma^{ab}}{6H^2},\qquad
\psi_\omega=\frac{\omega_{ab}\omega^{ab}}{6H^2}.
\tag{6.5}
\]

Squaring Eq. (6.3) gives

\[
\boxed{\psi_\sigma<U_\sigma:=\frac32B_\sigma^2},\qquad
\boxed{\psi_\omega<U_\omega:=\frac32B_\omega^2}.
\tag{6.6}
\]

The factor \(3/2\) is \(\Theta^2/(6H^2)\). Both numerator and denominator must use the same rate convention: \(H_t=cH_g\), \(\sigma^{(t)}=c\sigma^{(g)}\) and \(\omega^{(t)}=c\omega^{(g)}\) leave the ratios unchanged. Equation (5.4) specifies the separate vector/tensor conversion for vorticity. The norms here are full contractions, not half-contraction scalars.

For the additional scenario \(\epsilon_1=0\), Eq. (6.4) gives
\(U_\omega=(3/2)(2\epsilon_2/15)^2=C_2/(4\pi T_0^2)\). This is a useful units and coefficient check. It is not an observational determination of the intrinsic dipole.

### 6.3 Necessary conditions do not reconstruct a state

The implication is M \(\Rightarrow\) Eq. (6.6). The converse is not supplied. A state may happen to satisfy two norm bounds without satisfying the derivative, matter or all-observer assumptions used to obtain them. Likewise, small shear and vorticity by themselves do not characterise an FLRW spacetime.

A norm bound also loses direction. Let \(B_R=\{x:\|x\|\le R\}\). For any orthogonal representation of rotations, \(\|Rx\|^2=x^TR^TRx=\|x\|^2\), so membership in the ball cannot select one orientation. It also cannot distinguish different shape invariants at the same norm.

**Proposition 6.2 — no direction from rotational scalars alone.** An equivariant map from rotation-invariant scalar inputs to a vector or STF2/STF3 tensor has zero output.

**Proof.** Equivariance says \(F(s)=F(Rs)=RF(s)\), since a rotation leaves the scalar input unchanged. A nonzero vector cannot be fixed by all rotations: a half-turn about a perpendicular axis reverses it. A symmetric rank-two tensor fixed by all rotations must have equal eigenvalues, hence be proportional to \(I\); trace-freeness then gives zero. For STF3, associate the homogeneous harmonic cubic \(p(x)=F(s)_{ijk}x_ix_jx_k\). Rotational invariance makes its restriction to the sphere constant, while oddness makes the value at \(-n\) its negative. The constant is zero, and homogeneity implies \(p=0\) everywhere. All its coefficients therefore vanish. \(\square\)

This does not prohibit forming scalars from observed tensors. It prohibits reversing that information-losing operation without additional directional data or a model.

### 6.4 Several sectors: gauges and non-cancellation

Suppose a finite collection of Euclidean blocks has positive radii \(R_j\), and let \(B=\prod_j\{x_j:\|x_j\|\le R_j\}\). Its gauge is the least common dilation needed to include a point,

\[
\rho_B(x)=\inf\{t>0:x\in tB\}.
\tag{6.7}
\]

**Proposition 6.3 — product gauge.**

\[
\rho_B(x)=\max_j\frac{\|x_j\|}{R_j},\qquad
\rho_B(x)^2=\max_j\frac{\|x_j\|^2}{R_j^2}.
\tag{6.8}
\]

**Proof.** Membership in \(tB\) is equivalent to \(\|x_j\|/R_j\le t\) for every block. The smallest common upper bound is their maximum. Squaring is order-preserving for nonnegative numbers. \(\square\)

A large shear excess cannot be cancelled by a negative contribution from an unrelated sector. The gauge is neither a probability nor a posterior. Its square has the same threshold one but a different numerical excess margin.

The product formula need not survive additional coupled constraints. With \(B_0=[-1,1]^2\) and \(F=B_0\cap\{x_1+x_2\le1\}\), the point \((1,1)\) has \(\rho_{B_0}=1\). In \(tF\), however, its coordinate sum requires \(2\le t\), so \(\rho_F=2\). This exact example separates an anchor product from a full physical feasible body.

Ratios require the same sector, invariant, frame, congruence, epoch, units and approximation branch. For a fixed \(U>0\), a numerator interval \([a,b]\) becomes \([a/U,b/U]\) by monotonicity. A data-dependent random denominator needs a joint sampling model; separate marginal intervals do not justify the same operation. A missing anchor is not a zero-radius ball, and a missing numerator is not a measured zero. In the geodesic branch \(A_a=0\) is a physical domain condition; absence of a numerical acceleration anchor is a different statement.
