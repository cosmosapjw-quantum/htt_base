# Relativistic-optics type registry

The registry uses FOUR INDEPENDENT AXES. A quantity is not assigned one vague label such as
"invariant" or "observable"; it receives a tuple.

## Axis G — geometric / representation status

G0  relational scalar or basis-independent invariant.
G1  covariant geometric object (vector/tensor/operator/bundle section).
G2  components/coefficients in a coordinate, tetrad, screen or harmonic basis.

## Axis O — observer/frame dependence

O0  observer-independent spacetime structure.
O1  congruence-relative physical state.
O2  endpoint-relational optical quantity (physically depends on source/observer worldlines).
O3  detector-frame quantity.

## Axis M — measurement status

M0  raw detector data.
M1  calibrated operational observable.
M2  derived observable.
M3  reconstructed field / estimand.
M4  latent physical/model state.

## Axis R — transformation / redundancy status

R_diff     spacetime coordinate/diffeomorphism redundancy.
R_affine   null tangent affine normalization redundancy.
R_SO3      spatial tetrad/harmonic representation rotation.
R_SO2      polarization/screen basis rotation.
R_Lorentz  physical observer change when u^a changes.
R_cal      instrument/calibration nuisance.
R_stat     statistical/foreground nuisance.
R_model    model-label redundancy or parameter non-identifiability where applicable.

---

## Registry

### Spacetime metric g_ab
Type: G1 / O0 / M4.
Coordinate components are G2 and transform under R_diff.
The geometric metric is not an operational detector observable.

### Physical observer/congruence u^a
Type: G1 / O1 / M4.
Changing coordinates is R_diff.
Changing u^a by a physical Lorentz boost is NOT gauge: it selects a different observer.

### h_ab=g_ab+u_a u_b
Type: G1 / O1 / M4.
A rest-space projector relative to the declared u^a.

### theta=∇_a u^a
Type: G0 as a spacetime scalar once u is fixed / O1 / M4.
Coordinate invariant does NOT mean observer independent.

### A_a, sigma_ab, omega_a
Type: G1 / O1 / M4.
Their contractions/norms may be G0 under coordinate/tetrad changes but remain u-dependent.
This distinction is mandatory.

### Photon null tangent k^a
Type: G1.
R_affine: k^a -> c k^a for an affine rescaling.
Its normalization becomes physical only after comparison with a measuring observer.

### Measured photon energy E=-u·k
Type: G0 relational scalar / O3 / M1.
Invariant under coordinate changes and simultaneous tensor transformation.
Not observer invariant: a physical boost changes E by Doppler shift.

### Sky direction n^I
Type: G2 detector-tetrad components / O3 / M1.
Transforms equivariantly under R_SO3.
The point/direction on the observer celestial sphere is operational; component labels depend
on detector attitude/tetrad.

### Screen projector and screen basis
Screen 2-plane/projector: G1 / O3.
Chosen basis s_A^a: G2 with R_SO2 redundancy.
A screen-basis rotation is not a new observer.

### Jacobi map J^A_B
Type: screen-basis-equivariant propagation object.
Components: G2.
det J and singular-value/eigen-shape invariants with the proper screen metric are
basis-independent.
D_A^2=|det J| (up to orientation/sign convention).

### Redshift z
1+z=(u_s·k_s)/(u_o·k_o).
Type: G0 endpoint-relational / O2 / M1-M2.
Invariant under coordinates and common affine scaling of k.
Physically depends on source/observer velocities and spacetime propagation.

### D_A and D_L
Type: G0 endpoint-relational optical scalars / O2 / M2.
D_A is derived from area/solid angle.
D_L additionally involves flux/source luminosity; Etherington reciprocity requires the
usual geometric-optics/photon-conservation assumptions.

### Redshift drift and direction drift
Type: O2-O3 / M2.
Operationally defined by repeated measurements along the observer worldline.
Not local spacetime scalars independent of the observer.

### Photon distribution f(x,p)
Type: phase-space scalar / M4 or latent radiation state.
Its value is coordinate-covariant/invariant on phase space.
The split f(E,e) and its moments require a chosen u/tetrad.

### Specific intensity I_nu
Type: O3 / M1.
Observer/frame dependent.
I_nu/nu^3 is the natural invariant phase-space combination in collisionless geometric optics.

### Polarization tensor / coherency matrix
Basis-free screen tensor: G1 / O3 / M1-M2.
Stokes Q,U: G2 spin-2 components with R_SO2 redundancy.
Q±iU -> exp(∓2 i psi)(Q±iU) under screen-basis rotation.
Polarization amplitude/eigenvalues are basis-independent.

### CMB blackbody temperature T(n)
Type: O3 / M2.
A derived spectral observable after assuming/fitting a blackbody temperature parameter.
Not Lorentz-observer invariant.

### a_lm and observable STF Q_ab, O_abc
Type: G2/equivariant sky representation / O3 / M2.
They transform under sky SO(3) and under observer boosts.
Q:Q, O:O and internal orbit invariants remove basis rotation but NOT observer dependence.

### Radiation brightness PSTF multipoles Pi_Aell[u]
Type: G1 / O1 / M3-M4.
Covariant tensors in the u-rest space.
Not direct detector readouts.
Do not confuse them with temperature STF beyond the declared blackbody/linear adapter.

### Directional cosmographic H(n)
Type: scalar function on observer sky / O1-O3 / M3.
Its multipoles reconstruct theta, A and sigma under the local cosmographic assumptions.
It is an estimand, not a single raw datum.

### Remote CMB dipole/quadrupole
Type: M3 reconstructed fields.
Derived from kSZ/pSZ plus electron/tracer/optical-depth modeling.
Do not label as direct measurements of local velocity/shear without response assumptions.

### MES bounds
Type: conditional theoretical constraints.
Not observables and not posterior probabilities.

### Bianchi type / model-family labels
Type: M4 model state.
Require a forward model and identification argument; never inferred from representation
morphology alone.
