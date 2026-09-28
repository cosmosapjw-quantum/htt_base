# Measurement, symmetry and statistics contract

## 1. Do not conflate four operations

### A. Gauge quotient
Remove mathematical redundancy:
Diff(M), affine-null normalization, internal screen-basis rotations where appropriate.

### B. Physical observer transformation
u -> u' by a Lorentz boost changes measured E, n, temperature multipoles and generally
the decomposition of stress-energy/radiation.
This is a different physical measurement frame, not gauge.

### C. Representation change
Change coordinate/tetrad/harmonic basis while representing the same physical state.
Components transform equivariantly.

### D. Statistical nuisance marginalization
Foreground amplitudes, calibration gain, polarization angle, beam, selection functions,
optical-depth bias, source evolution, response uncertainty.
These are not GR gauge transformations.

---

## 2. When SO(3) should and should not be quotiented

Internal rotation of an arbitrary computational triad is representation redundancy.

A global rotation of a sky map is NOT automatically a nuisance if the science question includes
orientation relative to a physical axis:
- Galactic plane,
- ecliptic,
- measured CMB dipole,
- survey window,
- remote-tracer directions.

Recommended representation:
split morphology into
(i) internal rotation invariants and
(ii) explicitly retained orientation variables relative to declared physical frames.

Do not discard orientation by default.

---

## 3. Screen SO(2)

For a 2D STF screen tensor

G=[[g1,g2],[g2,-g1]],

a basis rotation by psi produces the spin-2 transformation with angle 2 psi.
Wolfram exact checks:
Tr(G^2) and det(G) are unchanged.

For polarization, Q±iU are representation components; the basis-independent polarization
tensor or rotational invariants should be used in likelihood construction unless an instrument
polarization-angle calibration is explicitly modeled.

---

## 4. Affine scaling

For one null ray k->c k,
endpoint photon energies scale by c, so

(ck·u_s)/(ck·u_o) = (k·u_s)/(k·u_o).

Redshift is affine-normalization independent.
Wolfram exact residual: 0.

---

## 5. Observer boosts

A local Lorentz boost changes
E=-u·k and measured sky direction by Doppler + aberration while preserving k^2=0.

Therefore:
- observer boost is a physical response/nuisance parameter if observer velocity is uncertain;
- it must not be quotient out as gauge;
- the exact STF local-boost response belongs in the forward model.

---

## 6. Representation-covariant linear inference

Suppose

y = R x + N eta + epsilon,
Cov(epsilon)=C.

Under invertible representation changes

y' = B_y y,
x' = B_x x,

the correctly transformed objects are

R' = B_y R B_x^{-1},
N' = B_y N,
C' = B_y C B_y^T.

The physical identifiable subspace is representation invariant:
rank(R modulo Im N) is unchanged.

Fisher information transforms by congruence:

F'=B_x^{-T} F B_x^{-1}.

### Important practical-rank consequence

Ordinary Euclidean singular values and condition numbers of a component matrix are invariant
only under orthonormal basis changes.

Under a non-orthonormal rescaling they change even though physical identifiability does not.

Wolfram exact toy check:
R=diag(1,eps), x'=diag(s,1)x.
Ordinary Gram matrix changes.
With the transformed state-space metric, the generalized eigenvalues remain {1,eps^2}.

Therefore PAPER-A should define practical rank using:
- physically declared state/observation metrics, or
- covariance whitening plus an orthonormal physical parameterization,
not arbitrary raw coefficient Euclidean norms.

This directly systematizes the existing R3 warning about raw-real versus orthonormal harmonic
carriers.

---

## 7. Recommended future likelihood graph

Latent physical/relational state:
S = [g_ab, matter fields, photon distribution, source/observer worldlines, physical frame labels]
    / Diff(M)

            |
            v

Relativistic optics + kinetic forward map

            |
            v

Operational observables:
O_op = {tau_o, nu_o, sky angle, spectral intensity/polarization, line redshift,
        image/Jacobi observables, repeated-time drifts}

            |
            v

Instrument/calibration map C_inst(eta_inst)

            |
            v

Raw data d

            |
            v

Map-making / component separation / estimators

            |
            v

Derived data products:
{T(n), a_lm, Q/O, d_L, D_A, H(n) coefficients, remote dipole/quadrupole, ...}

            |
            v

Physical inference:
p(d | x_kin, eta_phys, eta_inst, response uncertainty).

Gauge quotient occurs in the physical description.
Nuisance marginalization occurs in the statistical model.
They are not the same operation.
