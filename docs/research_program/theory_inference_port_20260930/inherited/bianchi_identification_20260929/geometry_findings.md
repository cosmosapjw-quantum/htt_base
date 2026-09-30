# Bianchi identification: independent geometry findings

Date: 2026-09-29. Scope: exact local geometry and conditional identifiability; no observational fit and no scientific-status promotion. Calculations reported by the coordinating agent are distinguished below from source reading and independent derivations.

## 1. The estimand must include the symmetry action

Three targets are different: (i) local spacetime isometry class, (ii) a chosen simply transitive spatial group action, and (iii) the maximal spacetime isometry algebra. A Bianchi label primarily describes the three-dimensional Lie algebra in (ii). A single metric can support distinct admissible actions. A scalar or tensor statistic built from that metric cannot distinguish which action was intended unless extra structure chooses it. A spatial-slice isometry need not preserve the complete spacetime evolution or matter fields. A fluid observer need not coincide with the homogeneous-orbit normal. Neither a tetrad's arbitrary anholonomy nor the kinematics of an arbitrarily chosen observer automatically gives the Bianchi algebra.

Kodama (2001), §3.2, explicitly discusses the Euclidean isometry group's distinct simply transitive subgroups of types I and VII0. This supports the group-action ambiguity; the following time-dependent construction is an independent explicit extension.

## 2. Exact ambiguity survives nonzero shear

For positive smooth A(t), B(t), consider

\[
g=-c^2dt^2+A(t)^2(dx^2+dy^2)+B(t)^2dz^2.
\]

The translations span a type-I algebra. For any constant q≠0 the fields

\[
X_1=\partial_x,\quad X_2=\partial_y,\quad
X_3=\partial_z+q(x\partial_y-y\partial_x)
\]

are also Killing fields, tangent to each t-slice, with

\[
[X_1,X_2]=0,\quad [X_3,X_1]=-qX_2,\quad
[X_3,X_2]=qX_1.
\]

Their spatial coefficient determinant is one. They generate a locally simply transitive type-VII0 action. The two actions preserve the same metric and the same normal congruence. If H_A=dot(A)/A and H_B=dot(B)/B, then

\[
\theta=2H_A+H_B,\qquad
\sigma_{ab}\sigma^{ab}=\frac23(H_A-H_B)^2.
\]

Thus the action ambiguity is present for genuinely shearing metrics, not only at the FLRW limit. Holding all matter, radiation initial conditions and detector laws fixed also holds every physically generated data law fixed. No number of redshift bins, morphology tensors, MES rescalings or CMB multipoles resolves this exact relabeling ambiguity. This is a failure of the unrestricted estimand to be a single-valued function of the physical model, before considering measurement noise.

The coordinating agent reports Wolfram checks of the Lie derivatives, commutators, determinant and shear contraction. Those transcripts should be attached by the coordinator. Invariant-coframe dual vectors must not be confused with the Killing generators displayed here. Global compact quotients can restrict the actions; no global-topology claim is made.

## 3. A useful algebraic exclusion certificate

For an oriented orthonormal left-invariant frame on a three-dimensional Riemannian homogeneous orbit, adopt

\[
C^k{}_{ij}=\epsilon_{ij\ell}n^{\ell k}
+a_i\delta^k_j-a_j\delta^k_i,
\qquad n=n^T,\qquad na=0.
\]

The last relation is Jacobi. Diagonalize n by an orthogonal transformation. Koszul's formula gives

\[
{}^3R=-6|a|^2-\tfrac12(n_1^2+n_2^2+n_3^2)
+n_1n_2+n_2n_3+n_3n_1. \tag{G1}
\]

Here n and a have inverse-length units. Their values depend on the orthonormal frame and metric scale, while algebra rank/signature information has the appropriate basis-invariant interpretation.

For class B, rotate a onto the first axis; Jacobi yields n1=0, hence

\[
{}^3R=-6a^2-\tfrac12(n_2-n_3)^2<0.
\]

For class A, the non-IX signatures give nonpositive curvature. In particular, for type VIII choose n1,n2>0 and n3<0; then

\[
{}^3R=-\tfrac12(n_1-n_2)^2-\tfrac12n_3^2+n_3(n_1+n_2)<0.
\]

Rank-zero, rank-one and rank-two cases follow directly from (G1). Therefore, assuming the orbit admits a simply transitive three-dimensional isometry group,

\[
{}^3R>0\quad\Longrightarrow\quad\text{its Bianchi algebra is IX}. \tag{G2}
\]

This is an established geometric fact, not a new theorem to claim priority for: Wald (1983), equations (15)–(16), uses precisely the nonpositive scalar-curvature property of all other Bianchi types. The present derivation makes it suitable for a polynomial/interval exclusion certificate. The coordinator reports an independent Wolfram Koszul derivation of (G1), the Jacobi residual and sign checks.

The converse is false. The IX signature n=(1,1,5), a=0 gives R3=-5/2. Also, R3=0 does not identify I. These statements concern spacelike group orbits; they do not cover Kantowski–Sachs geometries without a simply transitive G3, nor an arbitrary rotating observer's projected rest space. Spatial curvature inferred under an FLRW distance formula cannot be silently substituted into (G2).

## 4. A finite-jet sufficient condition in a regular homogeneous branch

**Candidate G3, with explicit proof.** Suppose a Riemannian orbit metric h is locally homogeneous on an open neighbourhood, and its Ricci tensor has three distinct eigenvalues λ_i there. Choose a smooth locally ordered orthonormal Ricci eigenframe e_i; its residual choices are constant signs and permutations. Every connected local isometry preserves the ordering and cannot continuously flip an eigenvector's sign. Consequently it preserves this frame. Transitivity makes the Ricci eigenvalues spatially constant.

Write D_{e_k}e_i=Γ^j_ki e_j. Metric compatibility gives Γ^j_ki=−Γ^i_kj. Taking a covariant derivative of the diagonal Ricci components therefore gives

\[
(D_{e_k}\operatorname{Ric})(e_i,e_j)
=e_k(\lambda_i\delta_{ij})-\Gamma^j{}_{ki}\lambda_j
-\Gamma^i{}_{kj}\lambda_i.
\]

The first term is zero by homogeneity. Hence, for i≠j,

\[
(D_{e_k}\operatorname{Ric})(e_i,e_j)
=(\lambda_i-\lambda_j)\Gamma^j{}_{ki},\qquad
\Gamma^i{}_{ki}=0.
\]

Thus the pointwise tensors h, Ric and D Ric determine every connection coefficient in that frame, then

\[
C^j{}_{ki}=\Gamma^j{}_{ki}-\Gamma^j{}_{ik}
\]

determines its commutator coefficients. They are spatial constants because the frame is invariant and the action transitive. The frame is the invariant (reciprocal) frame, generally **not** a frame of Killing vectors. Its algebra and the fundamental Killing-field algebra may differ by an overall bracket sign according to action conventions; the opposite Lie algebra is isomorphic through X↦−X, so the Bianchi type agrees.

Distinct Ricci eigenvalues also eliminate continuous isotropy: an infinitesimal orthogonal transformation preserving Ric must vanish. A local isometry fixing a point and its complete tangent frame is the identity. Thus the connected maximal spatial isometry group has dimension exactly three; any connected transitive G3 has that same local algebra. This branch avoids the I/VII0 ambiguity of §2 rather than falsely resolving it.

The orbit metric 3-jet is sufficient **conditional on neighbourhood homogeneity and simple Ricci spectrum**. It does not verify homogeneity from a lone point, give a universal 3-jet theorem in degenerate branches, or reconstruct that jet from a sky catalogue. For a spacetime assertion the same action must also preserve the extrinsic geometry and relevant physical fields. In particular, a time slice with homogeneous h but inhomogeneous extrinsic K is not thereby a Bianchi spacetime.

Ferrando–Sáez (2020), §4 and §5.4, supplies a coordinate-invariant formulation: a structure tensor can be recovered from Ricci and its first derivative on the algebraically general branch. Its degenerate branches require separate treatment. The elementary eigenframe calculation above exhibits why the inverse becomes ill-conditioned as a Ricci eigenvalue gap tends to zero. Near isotropy, normalizing amplitudes does not remove this loss of information.

### G3K extension: an invariant kinematic tensor can select the frame

The proof uses only a symmetric spatial tensor T that is invariant under the specified transitive action and has simple eigenvalues. Ric is one possible T. Another is the trace-free extrinsic curvature of the specified homogeneous foliation, equivalently the shear of its unit normal up to the fixed c convention. The same formula D_kT_ij=(λ_i−λ_j)Γ^j_ki reconstructs the algebra from h, T and D T.

This extends the constructive route to homogeneous slices with degenerate Ricci, including generic Bianchi I data with distinct principal expansion rates. The relevant symmetry is now that of the pair (h,T), or the full initial data (h,K), whose continuous isotropy is removed by T's simple spectrum. The LRS counterexample has repeated eigenvalues in both Ric and K, so it is not contradicted. A sky morphology tensor is not automatically such a spatial tensor; neither is arbitrary observer shear automatically invariant under the spatial action. For tilted matter, a declared projection onto the orbit-normal spatial bundle and proof of invariance are required. This extension does not claim a universal spacetime metric 2-jet theorem: the normal foliation and tensor-field inputs are additional structure.

## 5. Existing intrinsic classification supplies a realistic local-computation route

Sáez–Mengual–Ferrando (2024) develops intrinsic algorithms for identifying spatially homogeneous **perfect-fluid** metrics from curvature tensors and their derivatives, with separate regular and degenerate branches. Section 8 demonstrates an xAct/xIdeal route. This directly refutes any blanket assertion that geometrical Bianchi classification itself needs a Boltzmann solver. It does not supply a data-to-metric reconstruction theorem. The paper describes xIdeal as unfinished at its writing date; its present installed availability and version were not audited here.

The useful division of labour is: analytic/symbolic metric or metric-jet classification first; separately, an observational confidence region for the specific geometrical inputs. Unknown anisotropic stress, multi-fluid stress without a unique perfect-fluid representation, uncertain foliation, tilt and unmeasured derivatives prevent direct application of the perfect-fluid algorithm. They are conditions to retain, not nuisances to discard.

## 6. Recommended new research objects

1. **Set of compatible actions:** return all Bianchi labels admitted by a physical geometry and chosen foliation, with a separate maximal-isometry result. Preserve I/VII0 overlap exactly in regression examples.
2. **Curvature sign certificate:** over a joint uncertainty domain for orbit-normal expansion, shear, energy density, cosmological constant and tilt, bound R3 through the Hamiltonian constraint. A positive lower bound gives a conditional IX certificate; an interval straddling zero is inconclusive.
3. **Regular-branch reconstruction certificate:** record the Ricci eigengap, the full D Ric information required, resulting connection/commutator tensors, Jacobi residual and frame-equivalence class. Return an unresolved set near a degenerate spectrum.
4. **Observational exclusion, not automatic reconstruction:** use outer prediction sets for each action-compatible class. Separation excludes a class conditionally; an intersection does not prove realization or uniqueness. Establish the map from redshift/optical tensors to the geometrical input before claiming an empirical classification.
5. **Explicit exclusions from the current claim:** global topology, a unique preferred action in enhanced-symmetry cases, and a full recombination-era CMB likelihood are not delivered by these local certificates.

## Sources actually read

- Hideo Kodama, *Phase Space of Compact Bianchi Models with Fluid* (2001), https://arxiv.org/pdf/gr-qc/0109064 ; §3.1–3.2, PDF pp. 8–9 (zero-based pp. 7–8), Euclidean geometry, translations and I/VII0 subgroup discussion. Web refs turn63view2 and turn68view3. The OCR of one commutator equation appears unreliable; use the independently checked displayed vector fields above.
- Joan Josep Ferrando and Juan Antonio Sáez, *Homogeneous three-dimensional Riemannian spaces* (2020), https://arxiv.org/html/2004.01877v1 ; §§1–2 (group-action definition), §4 Lemmas 1–2 (structure tensor), §§5.3–5.4 and §6 (regular/degenerate and maximal/nonmaximal actions). Web refs turn63view1, turn72view0, turn72view1, turn72view2. No wholesale import of its flow chart or convention-specific h values was performed.
- Juan Antonio Sáez, Salvador Mengual and Joan Josep Ferrando, *Spatially-Homogeneous Cosmologies* (2024), https://arxiv.org/html/2409.15854v1 ; §§1–3, §7 introductory scope, §8 demonstration and package reference, plus inspected §6/appendix snippets. Web refs turn63view0, turn68view0, turn68view1. Specific singular-branch labels were not rederived and are not adopted here.
- Robert M. Wald, *Asymptotic behavior of homogeneous cosmological models in the presence of a positive cosmological constant*, Physical Review D 28, 2118–2120 (1983), https://doi.org/10.1103/PhysRevD.28.2118 ; author's paper scan at https://www.math.tecnico.ulisboa.pt/~jnatar/nonarxivpapers/Wald.pdf , p. 2119, equations (9), (15)–(16), including the distinction between orbit-normal shear and fluid shear. Web refs turn78search0 and turn79view0. The present curvature sign certificate uses only the geometric subargument, not the energy-condition/no-hair conclusion.

These source summaries are deliberately bounded; the explicit counterexample and elementary algebraic derivations form the present research synthesis. Parent should open source URLs itself before citing web references in its final response.
