# R62 selected classification experiment

Baseline c118982e56ee50d68dd0446aa10f16ffe65bd02b. User scope: one ten-stage anisotropy-classification study, including conditional Bianchi and tilt inference, without a Boltzmann solver. Signature (-+++), physical c retained. Existing checkout only; root is sole remote writer.

## A. Actual observable classification

R58 retains y32=(four dipole3 blocks, four orthonormal STF5 blocks), with full joint C32. Windows share the same 35,970 CF4 groups, centres z=(.025,.04,.06,.08), Gaussian width .012. These are angular-estimator windows, not disjoint physical shells. Start with their 20D STF marginal and its known fixed Gaussian law. For any selected carrier (h,V) use one E_d={x:(x-h)^T V^-1(x-h)<=chi2_d(.95)}; different d have explicitly separate confidence objects.

Fit exact set-membership witnesses for these finite tensor-series classes, retaining amplitudes of either sign and zero states:

1. ZERO: every K_j=0.
2. SHARED_FRAME: K_j=R diag(l_j1,l_j2,-l_j1-l_j2) R^T for one R in SO(3).
3. SHARED_AXIS: K_j=b_j sqrt(3/2)(u u^T-I/3) with a common unoriented u.
4. SHARED_ZERO_EIGENVALUE_SHAPE: K_j=b_j R diag(1,-1,0)R^T/sqrt2.
5. SHARED_GENERAL_SHAPE: K_j=b_j S with one arbitrary unit STF S. This is rank-one in tensor-series coefficient space; it is a stronger restriction than SHARED_FRAME.

At fixed R, axis or STF shape, amplitudes are linear GLS nuisance parameters. Variable projection uses the full V. A finite optimizer candidate proves intersection if its reconstructed exact-class state is inside E_d. A failed local search or an outside candidate does not prove exclusion. Label objective values as feasible upper bounds, not certified global minima, and do not use naive Wilks degrees of freedom at zero/repeated-eigenvalue strata.

For SHARED_FRAME, real symmetric tensors commute pairwise iff they have a simultaneous orthonormal eigenbasis. Use the existing R61 global quadratic solver to bound selected signed components/projections of each commutator over E_d. Any component range excluding zero proves disjointness; otherwise retain UNRESOLVED unless a feasible class witness proves intersection. These are numerical quadratic enclosures with declared gaps, not formal interval proofs.

## B. Common angular calibration quotient and actual source response

With D_j=K_j-K_0, a common additive STF C cancels. There exists some common C for which all K_j-C commute iff all D_j commute: necessity is pairwise commutativity of T_j-T_0; sufficiency uses C=K_0. The corresponding equivalence holds for common one-dimensional tensor shapes. This quotient allows arbitrary common calibration and must not be called a measured calibration bound. Keep cross-window covariance: V_D=L V L^T. Constant dipole/quad source calibration cancellation is checked through the actual source operator, not assumed from window labels.

A separate source-bound experiment reuses R54 source operators and R58 fixed covariances. Its explicit finite mean model is eta_i=g_i n_i.V+n_i.d+sum_{j=0}^J P_j(t_i) E_A:n_i n_i k_jA, J=2 primary, J=3 response-order sensitivity, t=(z-.055)/.045. Legendre polynomials are a declared finite phenomenological response, not a physical shear history or a complete GR optical expansion. The source design is O_m D; no diagonal-window substitution. Fit 21 or26 parameters, require matching numerical rank and source/operator parity. Classify the source coefficient tensors and the j>=1 contrast tensors using their proper marginal covariance. Common additive angular calibration only shifts j=0 and d. Also generate an actual-mask injection showing that a fixed source eigenframe can acquire noncommuting apparent window tensors when amplitudes vary with z. This measures the need for the source response, not an instrumental anomaly.

Raw data products and R61 results are unchanged. New extended response carriers and their identities are released. No new catalog-size cosmic covariance is computed.

## C. Bianchi compatibility and relevant repairs

Reuse canonical (a,n), na=0, exact Ricci and momentum helpers. Correct the active constructor's inference from the canonical IX n proportional I to all IX states: evaluate the actual algebra's divergence map/range and source momentum. Preserve the valid I and isotropic-n special-state restrictions. Check the exceptional VI_h rank stratum h=-1/9. Distinguish canonical representative rank from typewide admissibility and audit family/actual-algebra consistency.

Correct the physical-velocity moment Jacobian: D_v(p0,p1,p2)=2*[v,nv,n²v]^T, rank equals the number of distinct eigenspaces with nonzero v projection; rank(M) instead describes squared-component moments. Repeated-eigenspace azimuth is stabilizer freedom in the simultaneous SO(3) quotient. Preserve legacy receipt values as history.

For an untilted Type-V normal congruence, n=0,a!=0 and q=0 imply sigma a=0. For unknown a, det(sigma)=0 is exactly the momentum-only existence condition. In Class A, commuting n and sigma give q=0; selecting diagonal n in each Class-A type yields same-shear initial-slice candidates with different intrinsic curvature after the Hamiltonian/source conditions are supplied. These are explicit conditional constructions, not a theorem forbidding all observable classification.

Boltzmann-free geometric reconstruction is possible if actual normal-frame H,sigma,D_t sigma and normal-frame stress are available: R3=16piG epsilon_N/c^4+2Lambda-6H²/c²+sigma:sigma/c²; S3=8piG pi_N/c^4-(D_t sigma+3Hsigma)/c². Generic intrinsic action classification additionally needs spatial connection/curvature derivative data. Current CF4 apparent tensors alone do not supply that map; the paper plan names the missing response and observations.

## Resources and end condition

Use existing .venv/bin/python, one BLAS thread, small dense covariance operators and bounded low-dimensional optimization. Checkpoint before actual runs. Perform one affected-code verification pass and one fresh independent final review. Complete R1-R10/C1-C10 once, update the P5-scoped DAG and paper plan, non-force push the authorized branch. Do not generate a local-agent restart prompt or start an automatic new loop.
