# R62 R2 bounded source and implication map

Checked 2026-11-17 UTC. Baseline supplied by parent: c118982e56ee50d68dd0446aa10f16ffe65bd02b; branch research/r62-anisotropy-classification-20261117. This is source work and constructive notation translation, not a review of the parent's candidate. No remote writes, new code, or nested agents.

skill_context_used: cloud physmath-research-loop 1.3.0 SKILL.md, references/THEORY_LOOP.md R2, references/POLICY_INTEGRATION.md; mathbox literature-check SKILL.md. observed_model: UNKNOWN. Native dispatch: parent-assigned child; no descendants. Read existing R48 BIANCHI_TYPE_SIMILARITY_METHODS_KO.md, R49 BIANCHI_CONVENTION_BRIDGE.json, R49_GENERAL_TILTED_BIANCHI_KO.md on authorized Desktop Commander device edd1b263-56a0-4391-8a2a-677dd00eabf5, repository /home/cosmosapjw/Dropbox/bianchi/htt_base.

## Primary source table and exact reuse contract

| Source/version | Exact location checked | Result and hypothesis | Project implication |
|---|---|---|---|
| Ferrando–Sáez, Homogeneous three-dimensional Riemannian spaces, CQG37(2020)185011, arXiv:2004.01877v1 (2020-04-04), DOI10.1088/1361-6382/ab9880. https://arxiv.org/abs/2004.01877v1 | Eqs6–13; §4; Theorems4,7; AppendixA | Oriented positive-definite 3-metric with transitive isometry action. Defines structure tensor Z, symmetric N and a; N(a)=0. Eq10 computes Ricci from N,a. Theorem4 gives flat I/VII0 and negative constant-curvature V/VIIh actions on the same intrinsic spaces. Theorem7 assumes algebraically general Ricci and a maximal G3 and uses Z(S), including spatial derivatives of Ricci. | VERIFIED known after notation translation for structure-action classification and exact degeneracies. CONDITIONAL for observable inference: requires actual spatial Ricci derivative information or equivalent connection, not only its spectrum or time history at one point. |
| Sáez–Mengual–Ferrando, Spatially-Homogeneous Cosmologies, CQG41(2024)205013, arXiv:2409.15854v1 (2024-09-24), DOI10.1088/1361-6382/ad7664. https://arxiv.org/abs/2409.15854v1 | Theorems1,3,4; Eqs7–11,39–41; §§5–6 | Perfect-fluid spacetime; regular case admits Riemann frame. Theorem3 characterizes maximal G3 with spacelike orbits, including a timelike m from a derivative concomitant. Eq40 n=m/sqrt(abs(m²)), induced gamma=g+n n. Eq41 projects connection H to orbit structure Z; Theorem4 then invokes 2020 classifier. Singular/extra-isometry cases treated separately in §6. | VERIFIED known intrinsic classification. Does not establish recovery from a finite list of sky amplitudes. Nearest strong overlap for any claim of a new Bianchi classifier. |
| Hewitt–Bridson–Wainwright, The asymptotic regimes of tilted Bianchi II cosmologies, GRG33(2001)65–94, arXiv:gr-qc/0008037v1 (2000-08-15), DOI10.1023/A:1002075902953. https://arxiv.org/abs/gr-qc/0008037v1 | AppendixA A.1–A.29, especially A.2–A.7,A.11–A.18,A.22–A.27 | Appendix begins with GENERAL spatially homogeneous normal-frame equations; Bianchi II specialization begins only A.32. Hubble normalization assumes H nonzero; fluid is homogeneous barotropic perfect fluid in its own frame, ptilde=(gamma−1)mutilde, v²<1. Source/frame must be specified to close equations. | VERIFIED general momentum/shear/curvature and boost relations. Strong direct basis for all-type, state-dependent admissibility. A.27 HTML has an erroneous repeated index; A.18 is correctly contracted and should be cited instead. |
| Kwidzinski–Piechocki, Curvature invariants for the Bianchi IX spacetime filled with tilted dust, EPJC79(2019)199, arXiv:1901.01790v2 (2019-02-27), DOI10.1140/epjc/s10052-019-6701-z. https://arxiv.org/abs/1901.01790v2 | Intro and §II general model | Non-diagonal/general IX coupled to tilted dust. The subsequent singularity approximations do not restrict the mere existence of the general tilted-dust system. | VERIFIED primary counter-comparator to any typewide IX no-tilt claim. Do not substitute axisymmetric models with additional heat conduction for perfect-fluid evidence. |
| Betschart–Clarkson, Scalar field and electromagnetic perturbations on Locally Rotationally Symmetric spacetimes, CQG21(2004)5587–5608, arXiv:gr-qc/0404116v3 (2004-11-17), DOI10.1088/0264-9381/21/23/018. https://arxiv.org/abs/gr-qc/0404116v3 | §3 Eqs23–24 | LRS has a covariantly defined common preferred axis and one-dimensional rotational isotropy. All sheet vectors and sheet STF tensors vanish. LRS II additionally has zero fluid/axis twist scalars and magnetic Weyl scalar. | VERIFIED LRS criterion; a repeated eigenvalue of one instantaneous shear tensor does not verify the full set of conditions. |
| Sung–Coles, Temperature and Polarization Patterns in Anisotropic Cosmologies, arXiv:1004.0957v2 (2010-04-15). https://arxiv.org/abs/1004.0957v2 | §4.4 Eqs58–68, §5 | Near-FRW families I,V,VII0,VIIh,IX. Direction transport Eqs63–64 drops shear effects; polarization rotation examples Eqs66–68 use FRW curvature limits. §5 varies initial radiation quadrupole and describes focusing/twisting morphology. | VERIFIED adjacent morphology/symmetry work; it includes radiation transport, so it is not a solver-free all-family exact theorem. Its geometric mechanisms remain usable without building a Boltzmann solver. |
| Pontzen, Rogues' gallery: the full freedom of the Bianchi CMB anomalies, PRD79(2009)103518, arXiv:0901.2122v2 (2009-05-11), DOI10.1103/PhysRevD.79.103518. https://arxiv.org/abs/0901.2122v2 | Main text linear freedoms and morphology | Homogeneous anisotropy close to isotropic backgrounds, classified through available linear scalar/vector/tensor dynamical freedoms; not a generic all-nonlinear-Bianchi inverse theorem. | VERIFIED adjacent/overlapping morphology classification; generic CMB pattern taxonomy is known, but does not preclude a new concrete cross-observable conditional map. |
| Marcori–Pitrou–Uzan–Pereira, Direction and redshift drifts for general observers and their applications in cosmology, PRD98(2018)023517, arXiv:1805.12121v1 (2018-05-30), DOI10.1103/PhysRevD.98.023517. https://arxiv.org/abs/1805.12121v1 | General drift derivation; Bianchi I application | General observer drift splitting; specialized anisotropic results within Bianchi I. Peculiar velocity dipole and anisotropic-shear quadrupole have stated approximation and congruence contracts. | VERIFIED adjacent solver-free kinematic observation bridge. Does not supply general Bianchi type inference. |

## Equations available immediately

HBW uses geometrized sources (8piG=c=1). Its symbols are normal-frame quantities:

Sigma_ab=sigma_ab/H, N_ab=n_ab/H, A_a=a_a/H, Omega=mu/(3H²), Q_a=q_a/H², Pi_ab=pi_ab/H², Sigma²=Sigma_ab Sigma_ab/6, K=−R3/(6H²).

The complete momentum relation, A.18, is

Q_a=3 Sigma_a^b A_b − epsilon_a^{bc} Sigma_b^d N_dc.

For N diagonal this reads

Q=((N2−N3)Sigma23,(N3−N1)Sigma13,(N1−N2)Sigma12)+3 Sigma A.

A.7 gives B=2N²−tr(N)N,

S3/H²=B−tr(B)I/3−2 epsilon^{mn}{}_(a N_b)m A_n,

K=tr(B)/12+A².

A.17: Omega=1−Sigma²−K. A.25–A.26 for a single fluid:

Gv=1+(gamma−1)v², Q=3 gamma Omega v/Gv, Pi=3 gamma Omega STF(vv)/Gv.

These are matter-rest-frame perfect-fluid equations; nonzero tilt gives normal-frame anisotropic stress.

### IX correction, exact constructive initial data

IX requires definite N, not N proportional to identity. Take A=0, N=diag(1,2,3), Sigma12=Sigma21=s, all other Sigma=0. Then

K=−2/3, Sigma²=s²/3, Omega=(5−s²)/3, Q=(0,0,−s).

For dust gamma=1, A.25 gives v=(0,0,−s/(5−s²)); for sufficiently small nonzero s this has positive density and subluminal nonzero tilt. This is an explicit constraint-admissible initial state. The full fluid/evolution system remains to be integrated for any particular history. An isotropic-N canonical fixture supports only its state-specific momentum result, not a universal IX no-tilt rule. Equal eigenvalues make specific momentum components vanish; all-equal N makes all Class-A momentum components vanish at that state.

### Untilting V, exact constructive initial-slice condition

V has N=0,A nonzero. For total Q=0 the momentum constraint is Sigma A=0. Thus det(Sigma)=0 is necessary. For unknown nonzero A it is sufficient for this momentum equation alone: choose A in ker(Sigma). A real symmetric tracefree Sigma then has spectrum {lambda,−lambda,0}, including lambda=0. For fixed measured A, det(Sigma)=0 alone is insufficient; alignment with the kernel must also hold. Positive density, matter assumptions and the Hamiltonian constraint are additional conditions.

A.7 simultaneously gives S3=0 and K=A², hence Ric3_ij=−2 a² delta_ij, even if the normal shear is nonzero. This is spatial curvature isotropy on the slice. It does not imply a four-dimensional isometry to FLRW or I. The latter would require extrinsic curvature, source, congruence and evolution data to agree.

## Strongest constructive solver-free route and exact missing input

Use a geodesic, hypersurface-orthogonal homogeneous normal congruence, proper time t in seconds, a Fermi-propagated orthonormal frame, H and sigma in s^−1, intrinsic spatial Ricci in m^−2, energy density epsilon_N and anisotropic stress pi_N in energy/volume. With Einstein coupling kappa=8piG/c^4 and cosmological constant Lambda in m^−2:

R3 = 2 kappa epsilon_N + 2 Lambda − 6H²/c² + sigma_ab sigma_ab/c²,

S3_ab = kappa pi_Nab − (D_t sigma_ab+3H sigma_ab)/c².

The second follows by undoing HBW A.11 normalization with frame rotation zero; the first follows from A.17/Hamiltonian, allowing Lambda explicitly. These are DERIVED notation/unit translations of established equations, not new theorems. Each term has dimensions m^−2. Non-Fermi frames require the commutator rotation term. Accelerated normals require lapse-Hessian/acceleration terms. A tilted matter congruence has to be converted to the normal, and source pi_N must be supplied or inferred.

Thus actual normal-frame histories H(t),sigma(t),epsilon_N(t),pi_N(t) reconstruct Ric3(t) without a Boltzmann solver. Missing input is the observational response/inverse map that gives these histories and their common frame; a sky STF amplitude cannot silently be declared the normal shear. With unknown pi_N, the shear equation alone constrains S3−kappa pi_N, leaving a concrete curvature/stress degeneracy. The scalar additionally needs density/Lambda information.

Ric3(t) at one worldline does not automatically provide spatial derivatives D_i Ric3 needed by the Ferrando–Sáez intrinsic classifier. To identify a generic maximal-G3 action one must additionally reconstruct the invariant spatial connection, equivalently (a,n) up to frame, or enough spatial curvature derivative data; alternatively solve an explicitly constrained candidate-set inverse problem using the known homogeneous dynamics. Constant-curvature action degeneracies persist and should return {I,VII0} or {V,VIIh} where appropriate, unless extrinsic/source/connection data distinguish the selected action. This is a constructive input contract, not a theorem forbidding all inference.

For pure instantaneous shear, rotational invariants tr(sigma²),tr(sigma³) fix its eigenvalues, including uniaxial/triaxial degeneracy, but not the spatial bracket. Interpreting axial shear as full LRS further requires common-axis invariance of curvature, matter and their derivatives, as in Betschart–Clarkson. Source-conditioned momentum constraints can yield useful type restrictions, such as the V kernel condition above; no blanket claim that shear can never exclude a type is justified.

## Novelty classification and bounded search evidence

Used Exa semantic searches for homogeneous Bianchi equivalence, exact momentum formulas, Milnor Ricci, LRS, and tilted IX; SciSpace natural-language queries for solver-free morphology/kinematics and intrinsic Ricci classification; web engines for exact identifiers and primary source locations. Search horizon 2026-11-17, English mathematics/relativity/cosmology. Backward/adjacent leads from R48 and R49 reused. This is a focused finite comparison, not a comprehensive citation graph.

Labels: structure classification, curvature degeneracies and boost/momentum formulas are known after notation translation; the IX/V applications are formal corollaries not stated in this project form; CMB focusing/twist and scalar/vector/tensor taxonomy are partial or adjacent overlapping work; observationally reconstructing a specific common-frame history and integrating it with repository-specific conditional candidate sets requires an explicit new result and has no novelty verdict here. No apparently-new or strong-no-go claim is admitted from search absence.

Authentication caveats: arXiv renderer can insert current 2026 dates in old manuscripts; version tables on canonical abstract pages, rather than rendering date, were used. A web result labelled Milnor1976 pointed to a Utah gelbart-elliptic-curves.pdf; Exa full extraction returned Gelbart's elliptic-curves article. That candidate was rejected. Milnor1976 DOI10.1016/S0001-8708(76)80002-3 metadata is authenticated, but original theorem4.3 full text was not acquired here; Ferrando2020 Eq10 and HBW A.7 suffice for the actual Ricci implication. No raw external full text was written to the repository or retained as a tracked artifact.
