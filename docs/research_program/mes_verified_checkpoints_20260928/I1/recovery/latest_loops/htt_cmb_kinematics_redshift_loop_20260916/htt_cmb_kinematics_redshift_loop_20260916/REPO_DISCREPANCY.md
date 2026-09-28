# REPOSITORY DISCREPANCY — ell=0 radiation hierarchy documentation

Repository ref inspected:
50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb

## Documentation statement
docs/lowell_bianchi/02_multipole_hierarchy_spec.md states in its special-case table that
ell=0 keeps only T1 and T3.

## Direct coefficient audit
From the general hierarchy written immediately above the table:

T4 coefficient at ell=0:
-((ell+1)(ell-2)/(2ell+3)) = +2/3.

T7 coefficient at ell=0:
-((ell-1)(ell+1)(ell+2)/((2ell+3)(2ell+5))) = +2/15.

Therefore, for a general non-geodesic/non-isotropic radiation field the monopole equation
contains acceleration × dipole and shear × quadrupole terms.

This agrees with the standard radiation energy conservation equation:
dot rho_r + (4/3)theta rho_r + D_a q_r^a
= -2 A_a q_r^a - sigma_ab pi_r^{ab}
(up to moving all terms to a common side and the brightness normalization).

## Code inspection
htt/bass/hierarchy/terms.py:
- T4_accel_divergence explicitly evaluates ell=0.
- T7_shear_up explicitly evaluates ell=0.

htt/bass/hierarchy/hierarchy_rhs.py:
- T4 is added at ell=0 whenever has_accel.
- T7 is added at ell=0 whenever has_sigma.

## Classification
DOCUMENTATION_BUG / IMPLEMENTATION_PATH_CONSISTENT.

No production mutation was performed in this loop.
