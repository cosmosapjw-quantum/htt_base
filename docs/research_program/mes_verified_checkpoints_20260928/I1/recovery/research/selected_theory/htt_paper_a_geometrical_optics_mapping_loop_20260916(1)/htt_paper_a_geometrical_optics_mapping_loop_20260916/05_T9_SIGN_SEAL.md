# T9 independent sign re-derivation and oracle

The exact phase-space hierarchy contains the massless shear-down term

-[E^2 dF_{l-2}/dE -(l-2)E F_{l-2}] sigma.

For

I_l=Delta_l ∫_0^∞ E^3 F_l(E)dE,

multiply the phase-space equation by Delta_l E^2 and integrate. The shear-down piece is

-Delta_l[∫E^4F' dE -(l-2)∫E^3F dE].

Assuming E^4F vanishes at both endpoints,

∫E^4F' dE=-4∫E^3F dE,

therefore

+Delta_l(l+2)∫E^3F dE.

Wolfram exact:

Delta_l/Delta_{l-2}
=l(l-1)/[(2l-1)(2l+1)],

so the book-intensity coefficient is

+(l-1)l(l+2)/[(2l-1)(2l+1)].

At l=2: +8/15.

For direct brightness coefficients Pi_l with I_l=Delta_l Pi_l:

+(l+2) sigma_<a_l a_{l-1} Pi_{A_{l-2}>}

on the left-hand side.

The current repository uses the opposite T9 sign. Because the hierarchy driver returns
-a*sum_T, current l=2 behavior is

dPi_ab/deta=+4 a sigma_ab Pi_0,

whereas the source-grounded result is

dPi_ab/deta=-4 a sigma_ab Pi_0.

## Minimal fix candidate

Do not mutate production code in this research loop.

Candidate:
- T9 prefactor -(l+2) -> +(l+2);
- mode-mixing pre9 same sign flip;
- copied specs/docs same correction.

Required independent tests before promotion:

1. instantaneous isotropic-monopole/shear oracle:
   Pi_0=1, Pi_l>0=0, theta=A=omega=grad=collision=0
   => dPi_2/deta=-4 a sigma;

2. energy integration oracle using F(E)=exp(-E);

3. normalization cross-check against +8/15 in the specialized quadrupole equation;

4. mutation test: deliberate sign flip must fail all physics oracles.
