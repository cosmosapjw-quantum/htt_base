# Concrete CMB optical-kinematic mapping

## Collisionless blackbody

A blackbody distribution depends on E/T(x,e). Collisionless Liouville transport preserves
E/T along the photon phase-space trajectory, so

D_gamma ln T = D_gamma ln E = -H(e).

For an energy-independent blackbody temperature sky,

D_gamma T =
[(u+e)^a∇_a + V^A∇^S2_A]T,

therefore

[(u+e)^a∇_a + V^A∇^S2_A + H]T = 0

in the collisionless blackbody sector.

With Thomson/reionization physics, the collision/source operator belongs on the right-hand
side.

## Endpoint map

Specific intensity obeys the collisionless geometric-optics phase-space law

I_nu/nu^3 = invariant along a ray.

For blackbody radiation,

T_o(n_o)=T_e(x_e(n_o),e_e(n_o))/(1+z(n_o)).

The source direction/location is set by the null-geodesic/Jacobi map. Schematically,

e_e=Phi_J[n_o],

so

T_o(n)=[1+z(n)]^{-1} T_e(Phi_J[n]).

This exposes two distinct lanes:

A. frequency/redshift lane:
   H -> z -> temperature amplitude;

B. beam/Jacobi lane:
   Ricci/Weyl -> {vartheta,varsigma} -> Jacobi map -> angular remapping.

Geometric focusing does not simply multiply the pointwise specific intensity of a diffuse
background by an inverse-square factor; it changes the angular/source mapping.

## STF projection

For Theta_o(n)=T_o(n)/Tbar_o-1,

Theta_{A_l}^{obs}
= Delta_l^{-1} ∫Theta_o(n)n_<A_l>dOmega

for a declared STF normalization.

Then Q_ab and O_abc are the l=2 and l=3 STF products.

Full forward factorization:

(theta,A,sigma,omega)
   -> (H,V)

Riemann
   -> Sachs optical variables
   -> Jacobi map

{source radiation, H,V,Jacobi map, collisions}
   -> observed T/I/polarization
   -> STF Q/O/...

This is the concrete map; no direct algebraic Q->sigma identification is used.
