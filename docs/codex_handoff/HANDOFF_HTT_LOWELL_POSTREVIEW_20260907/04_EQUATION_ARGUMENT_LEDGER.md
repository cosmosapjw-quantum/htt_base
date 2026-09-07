# 04 — EQUATION / ARGUMENT LEDGER

Default conventions: spacetime signature `(-,+,+,+)`, spatial orientation `epsilon_123=+1`, full Euclidean Frobenius norm for spatial tensors, `beta=v/c`. All conditionals retain their stated model/statistical premises.

| ID | Object | Canonical equation / statement | Assumptions | Derivation status | Verification | Known issue | Next check |
|---|---|---|---|---|---|---|---|
| E01 | Q/O response algebra | `L_Q O=O:Q`; `B_Q beta=3 STF(beta⊗Q)`; `B_Q*=3L_Q`; `B_Q*B_Q=3M_Q`; `M_Q=(Q:Q)I+(6/5)Q^2` | nonzero STF2 Q, declared Frobenius metrics | exact finite-dimensional derivation | inherited formal/source evidence + exact-source decoder contract | algebraic beta coordinate is not automatically physical velocity | M1 supplies actual observation law |
| E02 | Ideal projection law | `f_B=||P_Q O||_F^2/||O||_F^2 ~ Beta(3/2,2)`; density `(15/4)sqrt(f)(1-f)`, mean `3/7` | conditional centred spherical 7D Gaussian or uniform sphere direction relative to fixed Q | analytic derivation | post-review direct derivation; scalar calculator checks only | SO(3) statistical isotropy alone is insufficient | use as synthetic oracle only |
| E03 | Q/O LS covariance | `beta_hat=M_Q^{-1}L_Q O`; `Cov(beta_hat-beta|Q)=tau^2/3 M_Q^{-1}`; fixed-amplitude analogue `A_O^2/21 M_Q^{-1}` | specified linear mean model and spherical residual law | analytic | direct derivation | Gaussian and fixed-radius experiments differ beyond second moment | M1 decides whether this model is used |
| E04 | Unit-q inverse trace | `tr M_q^{-1}=90/(40+3s3^2)`, `0<=s3^2<=1/6`, hence `20/9<=tr<=9/4` | STF2 q with `q:q=1` | analytic | direct derivation | none inside scope | regression oracle if implemented |
| E05 | Corrected illustrative RMS | with stated D2=226, D3=1018 microK^2, RMS coefficient `0.8823505847–0.8878481493` | same ideal fixed-Q model and report normalisation | substitution | calculator-checked, not map fit | old 0.8435 is superseded | do not use as universal no-go |
| E06 | First-order radiation shear | `sigma_ab=-dot(vartheta_<ab>)-D_<a vartheta_b>-(3/7)D^c vartheta_abc` | explicit first-order, geodesic, collisionless radiation model | analytic cancellation before norms | direct derivation, not new native CAS | not general nonlinear almost-EGS; amplitudes do not bound derivatives | synthetic/formal oracle only if campaign uses branch |
| E07 | STF derivative contraction | for declared STF3-gradient contraction `T T*=(7/5)I`, `||T||=sqrt(7/5)` | declared Euclidean/STF operator | exact linear algebra | direct derivation | replaces loose sqrt(3) when claiming sharp coefficient | focused regression after implementation |
| E08 | Model-specific shear ceiling | `||sigma||/Theta <= eps2*+eps1'+3/sqrt(35) eps3' <= eps1/3+eps2/3+eps3/sqrt(35)` | E06 plus characteristic derivative envelopes | CONDITIONAL theorem within model | direct derivation | weak premises imply non-strict inequality | M3 states whether used |
| E09 | Model-specific vorticity | `omega_ab=-3/Theta dot C_ab-C_ab-(6/(5Theta))D_[a D^c vartheta_b]c`; final `<=2/3 eps1+2/15 eps2` under envelopes | same model, exact contracted derivative conditions | CONDITIONAL | direct derivation | radial survey response does not measure this automatically | M2 preserves unsupported/null modes |
| E10 | Deterministic error-whitened rank | if `Delta Delta^T <= Gamma`, `W=Gamma^{-1/2}`, then `s_m(WK_true)>=s_m(WK_obs)-1` | actual numerical error belongs to Gamma; common metric | exact matrix inequality | established math; historical error-family work separate | hard part is Gamma membership/completeness; not prechoice of descriptive slack | M1/M3 freeze selected finite target/error rule |
| E11 | Minimum bounded-nuisance cost | for `d in Im K`, `c(d)^2=d^T(KSK^T)^+d`, `h*=SK^T(KSK^T)^+d`; outside image cost infinity | `S` positive definite, fixed linear model | exact linear algebra | direct derivation | two admissible nuisance states use `2R`, not `R`; physical positivity separate | C1 exact tests after freeze |
| E12 | Joint Gaussian conditioning | `C_y|z=C_yy-C_yz C_zz^{-1}C_zy`; `A_c=A_y-C_yz C_zz^{-1}A_z`; joint Fisher is z term + conditional y term if covariance parameter-independent | declared joint Gaussian law | standard/direct derivation | direct derivation | same-data high modes are not independent; parameter-dependent covariance adds trace term | M1 freezes actual blocks |
| E13 | Soft-mask response | `K_e=-e P(I-e M_FF)^{-1}V_b`, so `||K_e||=O(e)` while generic rank may remain full | finite-band soft-mask path and bounded resolvent | analytic | direct derivation | rank alone is not quantitative nuisance size | C2 mask sweep after freeze |
| E14 | Continuum minimal cutoff | registered axial stored-real row rank 32 at `L=10`; `L<=9` impossible in m=0 block; almost-every-direction full rank by nonzero polynomial minor | registered continuum mask/fit/source/operator | direct deduction from existing exact minors | durable derivation, no new certificate execution | not every direction; no uniform singular bound; no finite-pixel theorem | M1 keeps exact scope |
| E15 | Radial affine null | for `u(x)=u0+A x`, radial `n.u(rn)` has zero sensitivity to antisymmetric `Omega=(A-A^T)/2` because `n^T Omega n=0` | local low-z Euclidean affine approximation | exact algebraic null | direct derivation | not a theorem for every light-cone observable | M2 defines supported functions |
| E16 | First-order frame closure | `beta_RO=beta_RM+beta_MO+O(beta^2)` | small velocities, declared frame chart | standard conditional kinematics | retained report theory | one dipole + intrinsic component cannot identify all frame velocities | M1/M2 keep labels and external response requirements |
| E17 | DESI masked self-normalised dipole | `E[Dhat]=3(<nn^T>_R-<n>_R<n>_R^T)d=3 Cov_R(n)d`; uniform northern hemisphere gives `diag(1,1,1/4)` | weak density dipole, normalisation fitted from same selection | direct source-level derivation | NOT EXECUTED as repaired code | inspected path also compares equatorial vector to Galactic reference | M2 freezes corrected estimator; C1 implements/tests |
| E18 | Reduced Q/O contraction fibre | `eta=3 v^T[I+(6/5)q^2]^{-1}v`; unit STF3 with `o:q=v` exists iff `eta<=1`; interior fibre is S^3 in four-dimensional affine kernel | unit q, fixed contraction v | direct companion derivation | no independent CAS | reduced consistency only, not full packet nor physical beta | optional companion result |
| E19 | Same-q fibre Hausdorff sensitivity | distance combines centre metric and `sqrt(1-eta)` radii; saturation has sharp square-root sensitivity | fixed q, feasible unit fibres | direct companion derivation | no independent CAS | not a decoder counterexample | optional companion result |

## Required checks on any future use

- **Sign/index:** preserve `n=-e`; frame and pseudotensor/parity conventions must be explicit.
- **Units:** Q/O temperature units; rate ratios use either geometric or inverse-time convention consistently with c.
- **Normalization:** full vs half shear contraction must be adapted explicitly.
- **Gauge/frame:** `beta_RO`, `beta_RM`, `beta_MO` are not interchangeable; spatial affine shear is not automatically congruence shear.
- **Approximation ordering:** E06–E09 are first-order model results; E13 is a small-mask path result; E15 is local affine/low-z.
- **Boundary/regularity:** derivative-envelope premises are not consequences of small multipole amplitudes.
- **Convergence/conditioning:** algebraic rank, numerical rank, robust rank and subspace orientation are distinct.
- **Statistical status:** identified sets, realised compatibility sets, confidence regions and null ranks are distinct.

## Notation conflicts

1. Companion notes sometimes denote the observable contraction `v=o:q`; this is **not physical velocity**. Rename it when `beta=v/c` also appears.
2. `affine_flow.py` uses `sqrt(0.5 sigma:sigma)`, whereas Report A MES uses `sqrt(sigma:sigma)`.
3. Raw-real and orthonormal real harmonic carriers have different Euclidean metrics.
4. Existing processed tensor `J` has shape `(3,32,49)`; a fixed-source velocity derivative has shape `(32,3)`. A source-coordinate `J_b` of shape `(32,48)` is not the same object.
