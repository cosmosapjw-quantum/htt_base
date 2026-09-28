# PAPER-A V2 theorem spine

## Main Theorem A — Instantaneous radiation quadrupole non-invertibility

### Statement
On any state class in which the radiation quadrupole obeys a first-order transport
equation containing its proper-time derivative, there is no universal instantaneous
algebraic inverse

    sigma_ab = F(Pi_ab)

from the value of the CMB/radiation quadrupole alone.

This remains true even in the homogeneous, collisionless, near-isotropic reduction

    dot Pi_ab + (4/3) theta Pi_ab - 4 sigma_ab Pi_0 = 0.

For fixed Pi_0, theta and instantaneous Pi_ab, two distinct shears sigma^(1)_ab and
sigma^(2)_ab are both admissible if the corresponding derivatives are chosen as

    dot Pi_ab^(i)
      = -(4/3)theta Pi_ab + 4 Pi_0 sigma_ab^(i).

Hence an instantaneous quadrupole does not identify instantaneous shear.

### Wolfram check
With a common remainder c,

    dq_1 = c + 4 Pi_0 sigma_1,
    dq_2 = c + 4 Pi_0 sigma_2,

both transport residuals vanish exactly while

    dq_2-dq_1 = 4 Pi_0 (sigma_2-sigma_1).

### Role
HEADLINE NEGATIVE THEOREM.
It formalizes the paper's typed-state claim:
same STF representation does not imply physical attribution.

Novelty status:
- underlying transport: ESTABLISHED;
- explicit cosmological identifiability/no-inverse formulation: NOVELTY-CANDIDATE;
- priority not certified.

---

## Main Theorem B — Near-isotropic radiation–cosmography residual decomposition

### Assumptions
1. declared unit timelike congruence u^a;
2. blackbody radiation to first order in anisotropic temperature/brightness multipoles;
3. first order in A_a, sigma_ab, omega_a and radiation anisotropies;
4. no assumption of spatial homogeneity;
5. generic linear collision multipoles K_0, K_a, K_ab retained;
6. proper-time hierarchy;
7. n^a=-e^a converts photon propagation to outward-sky odd multipoles.

Let Pi_0 be the brightness monopole and define, to linear order,

    T_a^sky  = - Pi_a/(4 Pi_0),
    T_ab     =   Pi_ab/(4 Pi_0).

Let the local directional cosmographic Hubble/redshift generator be

    H(n) = theta/3 - A_a n^a + sigma_ab n^a n^b.

The linearized covariant brightness hierarchy gives

    dot ln Tbar
      = -theta/3
        - (D^a Pi_a)/(12 Pi_0)
        + K_0/(4 Pi_0),

    dot T_a^sky
      = A_a
        + (D_a Pi_0)/(4 Pi_0)
        + (D^b Pi_ab)/(10 Pi_0)
        - K_a/(4 Pi_0),

    dot T_ab
      = sigma_ab
        - (D_<a Pi_b>)/(4 Pi_0)
        - 3(D^c Pi_abc)/(28 Pi_0)
        + K_ab/(4 Pi_0).

Therefore the bridge residual

    B(n)
      := H(n)
         + dot ln Tbar
         + dot T_a^sky n^a
         - dot T_ab n^a n^b

has the irreducible form

    B(n) = B_0 + B_a n^a + B_ab n^a n^b

with

    B_0
      = -(D^a Pi_a)/(12 Pi_0) + K_0/(4 Pi_0),

    B_a
      = (D_a Pi_0)/(4 Pi_0)
        + (D^b Pi_ab)/(10 Pi_0)
        - K_a/(4 Pi_0),

    B_ab
      = (D_<a Pi_b>)/(4 Pi_0)
        + 3(D^c Pi_abc)/(28 Pi_0)
        - K_ab/(4 Pi_0).

### Wolfram check
Exact symbolic simplification reproduces all coefficients:
1/12, 1/4, 1/10, 3/28.

### Corollary B1 — homogeneous collisionless bridge
If the projected spatial-derivative terms and K_0,K_a,K_ab vanish,

    B(n)=0

and

    dot ln Tbar=-theta/3,
    dot T_a^sky=A_a,
    dot T_ab=sigma_ab.

### Corollary B2 — exact isotropic-radiation kinematics
If Pi_a=Pi_ab=Pi_abc=...=0 is preserved and collisions do not generate anisotropy,

    dot ln Tbar=-theta/3,
    A_a=-D_a ln Tbar,
    sigma_ab=0.

This is the classic isotropic-radiation / EGS-side kinematic limit, and is not claimed
as new.

### Interpretation
The new object is not another CMB anomaly statistic. It is a typed consistency residual:
it says exactly why a local optical kinematic reconstruction and a radiation-multipole
time-evolution reconstruction disagree at first order.

Novelty status:
STRONG NOVELTY-CANDIDATE as a synthesis/derived residual theorem.
Each ingredient is prior art; the compact residual decomposition was not found explicitly
in the bounded literature audit.

---

## Main Theorem C — Information equivalence of the strict bridge lanes

Define the 12-dimensional local kinematic state

    x = (theta, A_a, sigma_ab, omega_a)

with dimensions 1+3+5+3.

The irreducible coefficient response of the directional Hubble map is

    R_H x = (theta/3, -A_a, sigma_ab).

Under Corollary B1, the radiation-derivative response is

    R_T x = (-theta/3, A_a, sigma_ab).

There is an invertible output sign map

    S = diag(-1, -I_3, I_5)

such that

    R_T = S R_H.

Therefore

    ker R_H = ker R_T = {pure omega_a sector},

    rank R_H = rank R_T = 9,

and

    rank [R_H ; R_T] = 9.

Wolfram exact matrix check:
rank optical = 9;
rank radiation derivative = 9;
rank stacked = 9;
nullity = 3;
R_T-S R_H = 0 exactly.

### Statistical interpretation
The second lane can improve precision and test assumptions/systematics, but it does not
add a new structural kinematic direction in the strict bridge limit. With positive-definite
noise covariance, its Fisher information has the same vorticity null.

Role:
HEADLINE INTERPRETIVE COROLLARY.
This prevents the paper from overselling a second observable as new structural rank.

---

## Main Theorem D — Redshift-lift / tomographic identifiability

Let m source components x_r transform in the same angular irrep V_l of dimension d.
For an ideal redshift-separable response

    y_alpha = sum_r f_r(z_alpha) x_r + epsilon_alpha,

the response is

    R = T_z ⊗ I_d,
    (T_z)_{alpha r}=f_r(z_alpha),

and

    rank R = d rank T_z.

Thus redshift tomography separates same-irrep physical sources if and only if their sampled
redshift kernels are linearly independent.

More generally,

    rank(T_z⊗B) = rank(T_z) rank(B).

### Corollary D1 — old single-shell theorem
For two dipole sources with kernels

    f_1(z)=1,
    f_2(z)=1/z,

one exact shell has only d=3 identifiable dimensions.
Two distinct depths z_1 != z_2 give rank 6, since

    det T_z = (z_1-z_2)/(z_1 z_2).

### Corollary D2 — old temporal-STF theorem
For STF2 histories,

    rank(T⊗I_5)=5 rank(T).

This subsumes the old standalone A-temporal-tensor-rank row.

### Corollary D3 — conditioning warning
Formal full rank does not imply practical separability.
As sampled kernels become nearly proportional, the smallest singular value tends to zero.
Parameter scaling, covariance whitening and nuisance projection must precede numerical
condition-number claims.

Role:
HEADLINE METHODS THEOREM, but not a claim of new linear algebra.
Novelty lies in typed cosmological source ownership / experiment-design use.

---

## Supporting Proposition E — Directional cosmographic inversion

For

    H(n)=theta/3-A_a n^a+sigma_ab n^a n^b,

full-sky projections recover

    theta   = (3/4pi) ∫H dOmega,
    A_a     = -(3/4pi) ∫H n_a dOmega,
    sigma_ab= (15/8pi)∫H n_<a n_b> dOmega.

The vorticity sector is an exact null.

Status:
ESTABLISHED / WOLFRAM-EXACT.
Use as a physical adapter, not a novelty claim.

---

## Supporting Proposition F — Vorticity channel selection

Scalar local radial/distance response:
    n^a omega_ab n^b = 0 exactly.

Radiation hierarchy:
omega_a enters at fixed l as an angular-rotation generator acting on pre-existing
anisotropic multipoles; it is not a direct first-order monopole-to-anisotropy source.

Therefore:
- scalar cosmography cannot identify omega;
- the strict bridge lanes retain the same 3D omega null;
- vorticity is not globally unobservable.

Primary-literature context now includes explicit late-time vorticity estimators using
kSZ + moving-lens information (Coulton, Akitsu & Takada, PRD 108, 123528).

Disposition:
keep as a no-go/selection proposition; do not make a new vorticity estimator part of PAPER-A.

---

## Supporting Theorem G — Exact local-observer STF response

Retain the previously derived local-boost response as the one fully solved low-ell response
example:

    (B_Q beta)_abc = 3 beta_<a Q_bc>,

    M_Q = (Q:Q) I + (6/5) Q^2,

    (B_Q beta):Q = M_Q beta,

    B_Q^* B_Q = 3 M_Q,

    beta_hat = M_Q^{-1}(O:Q),

with exact orthogonal boost-compatible / boost-incompatible decomposition and

    kappa_2(M_Q) <= 5/3.

Role in V2:
not a second paper inside PAPER-A.
Use it as a worked example of an exactly invertible, explicitly conditioned response channel
and as the observer-frame nuisance adapter for Q/O morphology.

Novelty:
STRONG PURE-THEOREM NOVELTY-CANDIDATE, subject to final hostile literature audit.
