# Optical variable redefinition

## Four distinct spin/STF objects

### Timelike congruence shear sigma_ab[u]
3D PSTF; 5 dof; part of ∇_b u_a; congruence-relative.

### Null optical shear varsigma_AB[k]
2D screen STF; 2 dof; differential beam/image distortion; propagated by Sachs equations.

### Observed lensing/image shear gamma_AB
Endpoint/integrated distortion derived from the Jacobi map; not pointwise varsigma_AB.

### CMB quadrupole Q_ab
STF coefficient of the observed/derived sky temperature field; not sigma_ab or varsigma_AB.

## Three distinct rotations

- matter/congruence vorticity omega_a: physical first-jet variable;
- null twist: zero for the light-cone congruence k_a=grad_a psi;
- screen-basis SO(2): representation redundancy.

## Proposed primary optical state

E=-u.k,
k^a=E(u^a+e^a),
s_ab=h_ab-e_a e_b.

Define

H(x,e) := -D_gamma ln E,
V^a(x,e) := D_gamma e^{<a>}.

For a narrow bundle,

B_AB := s_A^a s_B^b ∇_a k_b
      = varsigma_AB + (1/2) vartheta delta_AB.

The observational state is

O_opt={H(e),V_A(e),B_AB(v,e),z,D_A,Jacobi distortion,I_nu,polarization}.

The timelike first jet (theta,A,sigma,omega) is an inverse target, not the primary
measurement variable.

## Redshift-parametrized affine-free Sachs variables

With B:=dv/dz and D=D_A in the book's observational coordinates,

vartheta = 2/(B D_A) dD_A/dz,
varsigma_IJ = D_A^2/(2B) dL_IJ/dz.

Define

K^(z)_IJ := B B_IJ
          = [d ln D_A/dz] delta_IJ
            + [D_A^2/2] dL_IJ/dz.

Then

tr K^(z)=B vartheta=2 d ln D_A/dz,
TF K^(z)=B varsigma_IJ.

This product is invariant under constant affine re-normalization v->a v+b.
