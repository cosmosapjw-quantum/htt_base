# Source/implementation sign conflict: shear -> radiation quadrupole

Status: BLOCKED_PHYSICS_SIGN_SEAL
Severity: high for any theorem or production result using the generic T9 coefficient.
Production mutation: NO.

## 1. Independent exact photon-energy law

For k^a=E(u^a+e^a) and signature (-,+,+,+),

d ln E/dt along a collisionless ray contains

- sigma_ab e^a e^b.

For an initially isotropic distribution f_0(E), with shear as the only anisotropic driver,

dot f = E sigma_ab e^a e^b f_0'(E).

The quadrupole brightness moment therefore contains

dot Pi_ab ∝ sigma_ab ∫_0^∞ E^4 f_0'(E)dE
          = -4 sigma_ab ∫_0^∞ E^3 f_0(E)dE

assuming the boundary term E^4 f_0(E) vanishes at 0 and infinity.

Hence

dot Pi_ab = -4 sigma_ab Pi_0

under the standard positive multipole normalization.

Wolfram exact check with f_0=e^{-E}:
ratio of the two energy integrals = -4, boundary term = 0.

## 2. Räsänen 2009

The exact collisionless blackbody directional-temperature law gives the same sign:
the quadrupole coefficient of the directional derivative is -sigma_ab.

## 3. Maartens/Gebbie/Ellis specialized equations

Their specialized radiation anisotropic-stress/quadrupole equations contain
+ (8/15) rho_R sigma_ab on the LEFT-HAND SIDE.

Using
Pi_0=rho_R/(4π),
Pi_ab=15 pi_ab/(8π),

this is equivalent to
dot Pi_ab + 4 sigma_ab Pi_0 + ... =0,

hence dot Pi_ab = -4 sigma_ab Pi_0 in the homogeneous collisionless source-only limit.

The 1995 MES primary-source transcription likewise has the positive shear source on the
left-hand side of the anisotropic-stress evolution equation.

## 4. Generic hierarchy conflict

The generic hierarchy printed in the same lineage contains

-(ell+2) sigma_<a_l a_{l-1}> Pi_{A_{l-2}}

on the left-hand side.

At ell=2 this gives -4 sigma_ab Pi_0 on the left, hence the opposite source sign.

Wolfram normalization conversion:
generic Eq71 -> -8 rho/15 sigma,
specialized Eq89 -> +8 rho/15 sigma,
difference = 16 rho/15 sigma.

Thus the generic formula and the specialized/normalized equations cannot all be correct
under the same positive brightness convention.

## 5. Current repository

At commit 50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb:

htt/bass/hierarchy/terms.py implements

prefactor = -(ell+2)

for T9_shear_down and explicitly documents ell=2 as
-4 sigma_ab * Pi_monopole.

Existing tests check shapes/PSTF properties but no sign-sensitive physical oracle for the
ell=2 isotropic-monopole shear injection was found.

## 6. Decision

Do NOT silently repair the sign in PAPER-A or production code.

Scientific seal required:
1. independent first-principles derivation in the repository's exact normalization;
2. compare against at least one independent primary source not copying the same generic line;
3. add a sign-sensitive test using the exact photon redshift law / anisotropic-stress equation;
4. only then mutate production T9 and downstream fixtures if indicated.

For PAPER-A until seal:
- the collisionless exact temperature directional law may be used directly from Räsänen;
- any theorem relying on the repository generic T9 quadrupole source is BLOCKED;
- previous draft formulas with dot T_ab=+sigma_ab are WITHDRAWN under the present convention.
