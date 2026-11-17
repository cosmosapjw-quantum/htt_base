# R62 R3: state-dependent Bianchi constraint contract

Owner: `/root/r62_bianchi_constraints`. Selected stage: R3 only. Base repository: `/home/cosmosapjw/Dropbox/bianchi/htt_base`, observed HEAD `c118982e56ee50d68dd0446aa10f16ffe65bd02b`, intended branch `research/r62-anisotropy-classification-20261117`. Read-only inspection and one in-memory numerical discriminator were performed on authorized device `edd1b263-56a0-4391-8a2a-677dd00eabf5`. No production edits, historical receipt changes, ODE integration, or Boltzmann implementation.

Read context: PhysMath Research Loop 1.3.0 SKILL, POLICY_INTEGRATION, THEORY_LOOP (R3); mathbox research-program SKILL and program-protocol; root AGENTS and htt/bass/AGENTS; targeted current code and R49 tests. Local artifact is a parent-owned integration input, not a publication-grade or four-axis CAS certificate.

## 1. Exact target and conventions

For a specified homogeneous slice, determine whether given `(a,n,sigma,H,matter)` satisfies Jacobi, Gauss and Codazzi. Distinguish this state question from the Bianchi Lie-algebra label and from observed morphology compatibility. A snapshot does not determine a unique cosmological history or CMB family.

Use signature `(-,+,+,+)`, epsilon_123=+1, the repo VER2 bracket

`C^k_ij = epsilon_ijl n_lk + a_i delta^k_j - a_j delta^k_i`,

with symmetric `n`, `n a=0`, and symmetric trace-free `sigma`. For the current geometric-unit API, define `q_i=T^{0i}` (normal-frame energy-current component). The active R49 sign is

`D_{a,n}(sigma)_i = -(sigma_jk epsilon_kil n_lj + 3 sigma_ij a_j)`,

`D_{a,n}(sigma) + kappa q_total = 0`.

This is the exact operator at convention_bridge.py:396–416 and the active residual at tilted_bianchi_state.py:755–759. In an n-eigenframe,

`D_1=(n3-n2)sigma23-3(sigma a)_1`,
`D_2=(n1-n3)sigma13-3(sigma a)_2`,
`D_3=(n2-n1)sigma12-3(sigma a)_3`.

The nearby convention_bridge.py:408 docstring instead says `D-kappa*q=0`; legacy constraints.py:122 actually uses that opposite residual. These are distinct code findings. The active R49 constructor and its R49 test at lines 113–116 use `q=-D/kappa`. Do not silently claim that all legacy constraint paths are repaired.

## 2. Operator rank and momentum range (direct derivation)

Choose the existing orthonormal STF-5 basis `E_A` and construct `M_iA=D(E_A)_i`. Rank, singular values, range projector, and target residual must be computed from the supplied `(a,n)`, not solely a family-name lookup. For nonzero kappa, the algebraic momentum range is `Range(M)` (multiplication by `-1/kappa` does not change that subspace). The exact compatibility condition is

`(I-M M^+)q_total=0`.

For supplied shear, require the stronger actual residual `M s+kappa*q_total=0`. If explicitly projecting shear, preserve its kernel component with

`s_out=s_in+M^+(-kappa*q_total-M s_in)`.

Use SVD with a documented relative threshold to distinguish numerical rank from an exact symbolic stratum. Uniform nonzero rescaling of `(a,n)` must leave the rank unchanged; an absolute-only threshold can violate this. Report near-degenerate singular values rather than inventing an exact family prohibition.

Class A: the diagonal formula above gives rank 0 when all n eigenvalues coincide, rank 2 when exactly two coincide, and rank 3 when all are distinct. In the repeated case `n2=n3!=n1`, the momentum range is `q1=0`. Type I always has rank 0. Type IX admits all three strata. Type II has rank 2. VI_0 has rank 3. VII_0 and VIII admit rank 2 or 3 depending on repeated eigenvalues. These are metric/state strata within Lie-algebra types.

Class B: rotate to `a=(a,0,0)`, `n=diag(0,n2,n3)`, `a!=0`. The first row is `(n3-n2)sigma23-3a sigma11`; the `(sigma12,sigma13)` block in rows 2–3 is

`B=[[-3a,-n3],[n2,-3a]]`, `det(B)=9a^2+n2*n3`.

Thus rank is 3 except at `n2*n3=-9a^2`, where rank is 2 and `n2*q2+3a*q3=0`. This is the exceptional `h=a^2/(n2*n3)=-1/9` stratum. Type V has rank 3 although its untilted subspace is restricted. The algebraic derivation covers all Class B parameter values satisfying Jacobi, without a family-wide rank approximation.

## 3. Matter and positive-energy contract (direct derivation)

For a single perfect fluid with rest-frame energy density `epsilon_hat`, pressure `p_hat`, physical speed `v`, and `beta=v/c`,

`gamma^2=1/(1-beta^2)`, `rho=gamma^2(epsilon_hat+p_hat)-p_hat`,
`q=gamma^2(epsilon_hat+p_hat) beta`.

Assumptions used for ordinary-fluid conclusions must be explicit: `epsilon_hat>0`, `epsilon_hat+p_hat>0`, `|beta|<1`, and vanishing intrinsic rest-frame flux/stress. Existing `SpeciesFluidCongruence` also accepts nonperfect sources; statements about perfect fluids must not be applied merely because one species has nonzero tilt. Summation, not count of active tilted species, defines total momentum. Vacuum energy has zero enthalpy and no physically distinct velocity.

At fixed positive rest enthalpy W, the beta-to-q map is onto R^3, with a stable inverse `beta=2q/(W+sqrt(W^2+4|q|^2))`. The geometric range condition alone therefore restricts momentum directions, but the Gauss equation and the chosen equation of state further restrict admissible states.

At fixed geometry and H, let `rho_req=(3H^2+R/2-sigma^2-Lambda)/kappa`, `sigma^2=sigma_ij sigma_ij/2`, and `q_req=-D(sigma)/kappa`. A positive-density dust source exists exactly when `rho_req>0` and `|q_req|<rho_req`; then `beta=q_req/rho_req`, `epsilon_hat=rho_req-|q_req|^2/rho_req>0`. For a fixed barotropic `p_hat=w epsilon_hat`, `-1<w<=1`, the positive-source ratio is `|q|/rho=(1+w)b/(1+w*b^2)`, strictly increasing on `0<=b<1`; it has range `[0,1)`. Different exotic source assumptions require their own conditions and must not be silently excluded by this ordinary-fluid contract.

## 4. Explicit c restoration

Treat the code's `H` and `sigma` as geometric inverse-length quantities `h=H_time/c`, `s=sigma_time/c`; physical `(a,n)` have inverse-length units and `Lambda` has inverse-length-squared units. With physical energy densities/pressures and `kappa=8*pi*G/c^4`, `q=T^{0i}` has energy-density units, physical energy flux is `F=c*q`, and momentum density is `q/c`. Then

`3 H_time^2 + c^2 R/2 - sigma_time^2 - (8*pi*G/c^2)rho - Lambda*c^2=0`,

`D(sigma_time)+(8*pi*G/c^3)q=0`.

The dimensionless variables are `Sigma=sigma_time/H_time`, `N=c*n/H_time`, `A=c*a/H_time`, `Omega=8*pi*G*rho/(3*c^2*H_time^2)`, and `Q=8*pi*G*q/(c^2*H_time^2)`. The stored tilt vector is beta, not a velocity in m/s. Do not change old numeric values by silently mixing a SI Hubble rate with inverse-length structure constants.

## 5. IX counterexample and current implementation observation

Set geometric `H=kappa=1`, `Lambda=0`, `a=0`, `n=diag(1,2,3)`, and only `sigma12=sigma21=s`. Direct contraction gives `R=4`, `sigma^2=s^2`, `rho=5-s^2`, `q=(0,0,-s)`, `beta=(0,0,-s/(5-s^2))`. The positive dust regime is `0<|s|<(sqrt(21)-1)/2`; at s=0 it continuously becomes untilted.

Read-only in-memory execution at s=0.1 gave:

- rho=4.989999999999999; epsilon_hat=4.9879959919839685; beta3=-0.02004008016032064.
- q3=-0.09999999999999998; D3=0.1; actual STF divergence rank=3.
- `evaluate_tilted_constraints`: admissible true, Gauss residual 8.881784197001252e-16, Codazzi norm 2.7755575615628914e-17, exact Ricci route error 0.
- `construct_admissible_tilted_state(...family='IX',algebra=custom,closure='hold_H',H=1)`: raises CodazziProjectionError claiming D sigma is identically zero.

Mechanism: tilted_bianchi_state.py:127–179 builds registry ranks on default factory representatives; default IX has `n=0.01 I` (not literally I). Lines 855 and 863–869 use this rank-zero metadata even when the caller supplies nonisotropic IX n. This is a reproduced implementation defect and an exact counterexample to the overbroad prohibition. It is not a new strong no-go theorem or a claim of literature novelty.

Runtime evidence: first attempt used the documented `venv/bin/python`, which is absent in this checkout; the diagnosed fallback `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=htt:htt/src python3` succeeded (remote process 1459921). No pytest suite or 4-axis CAS pass is claimed in R3.

## 6. Shear-only compatibility and the R48 quotient distinction

For untilted Type V, `n=0,a!=0,q_total=0` implies `sigma a=0`, hence det(sigma)=0. Conversely any STF sigma with a null vector admits a nonzero Type V a along that vector at the constraint level. This is a conditional slice criterion; matter closure and Gauss positivity still apply.

For any STF sigma, choose an eigenframe and a diagonal n of any Class A type. Then `[sigma,n]=0`, D sigma=0. Positive matter and sufficiently large H can satisfy Gauss. Therefore a shear spectrum alone does not identify a Class A family; this statement is constructive and limited to slice data with free H/source/structure scale.

For moments `p_k=beta^T n_hat^k beta` (k=0,1,2), in an eigenframe `p=Mw`, `w_i=beta_i^2`, and `M_ki=lambda_i^k`. Therefore `dp/d(beta_eigen)=2 M diag(beta_eigen)`, or invariantly the three Jacobian rows are `2 beta^T`, `2(n_hat beta)^T`, `2(n_hat^2 beta)^T`. `rank(M)` is the squared-component inverse rank, not the local Jacobian rank at a specified beta. At beta=0 the Jacobian is zero even with three distinct eigenvalues; this was reproduced against bianchi_similarity.py:270, which reports rank 3 for both fields.

Rotations inside a repeated n-eigenspace that preserve a are stabilizer gauge transformations of `(a,n)`. For example a=0,n=lambda I gives one SO(3) orbit for each beta speed, despite a two-dimensional direction sphere before quotienting. The existing `continuous_azimuth_degeneracy_dof` can be retained as a backward-compatible stabilizer-fibre dimension only with that documented meaning; it is not a dimension of inequivalent SO(3) orbits. A genuine observational inverse degeneracy would need an explicitly smaller observable map.

## 7. Smallest safe next-stage repair design

1. Add/reuse one state-dependent STF divergence-matrix helper from actual a,n; use it for projection/range checks. Stop consulting the canonical family boolean as an authoritative per-state prohibition. Preserve registry keys and canonical numeric values for compatibility, but label/document their representative scope and replace the IX family-wide prose. Existing default IX rejection remains correct.
2. Keep active R49 sign `D+kappa*q=0`; fix its stale nearby docstrings/comments. Preserve the legacy opposite-sign path as a separately tracked semantic issue unless the parent explicitly includes its dependent callers/tests in this repair.
3. Correct `moment_jacobian_rank` using the actual velocity Jacobian; retain `moment_rank` for M. Clarify repeated-eigenspace metadata as a stabilizer fibre. Parent may assign this separate disjoint file owner.
4. Target regressions: nonisotropic IX dust example passes; isotropic IX and Type I nonzero net perfect-fluid momentum fail; repeated IX permits only its rank-two momentum plane; exceptional VI_{-1/9} rejects out-of-range q; projection preserves the STF kernel; SO(3) covariance and nonzero uniform-scale rank invariance; zero/axis-aligned/generic moment-Jacobian cases. Preserve old frozen receipts; append current correction evidence.

This repair certifies conditional initial-slice consistency and diagnostic quotient semantics only. Native CMB transfer, Bianchi-family discovery from morphology, statistical confidence, and full evolution remain outside this artifact.

## Primary sources actually opened

- C. G. Hewitt, R. Bridson, J. Wainwright, *The asymptotic regimes of tilted Bianchi II cosmologies*, arXiv:gr-qc/0008037v1, Appendix A (printed pp.18–20): A.2–A.7 define normalized variables; A.16–A.18 are Jacobi/Gauss/momentum; A.19–A.26 define tilted perfect-fluid projections. The appendix begins with general SH equations, before its Bianchi II specialization. URL: https://arxiv.org/pdf/gr-qc/0008037 . Tool refs: turn774601970view0, turn215019171view0, turn327661963view0.
- N. Kwidzinski, W. Piechocki, *Curvature invariants for the Bianchi IX spacetime filled with tilted dust*, arXiv:1901.01790v2, Section II, Eqs.(1)–(10): independent published existence/formulation context for general tilted dust IX; its units and variables are not silently substituted into the repo. URL: https://arxiv.org/pdf/1901.01790 . Tool refs: turn774601970view1, turn133083012search2.

R3 outcome: established source equations aligned; exact slice-level counterexample and rank strata directly derived; one current-code counterexample numerically reproduced. Production repair remains NOT_ATTEMPTED pending the parent's R4/R5 scope assignment.
