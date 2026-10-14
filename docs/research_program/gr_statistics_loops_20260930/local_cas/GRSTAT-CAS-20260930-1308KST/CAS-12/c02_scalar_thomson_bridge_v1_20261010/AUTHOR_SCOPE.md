# CAS12-C02 scalar Thomson finite bridge

The independently authored `ScalarThomson.lean` proves actual interval Lebesgue
integrals, with exact polynomial primitives, for the scalar elastic phase kernel
`P(mu)=3*(1+mu^2)/(16*pi)`, where `mu=e dot e'`. The convention is
`p_l=2*pi*integral[-1,1] P(mu)*L_l(mu) dmu`.

The declared finite set is `l=0,...,6`. Its kernel-checked results are `p0=1`,
`p2=1/10`, and `p1=p3=p4=p5=p6=0`. A separate pointwise identity is
`P(mu)=(L0(mu)+5*(1/10)*L2(mu))/(4*pi)`. The theorem concerns all real `mu`
where appropriate and exact continuous integrals, not samples or quadrature.

The frozen CAS12-C02 statement supplies no harmonic cutoff. The finite declaration
here is explicit author scope and does not change that frozen statement. Therefore
the overall contracted C02 coverage remains HOLD. In particular this proof does
not establish all-degree Legendre orthogonality, sphere-measure coordinate
reduction, harmonic completeness, or an addition/Funk-Hecke theorem. The exact
phase expansion alone is not used to claim those analytical bridges.

Final compilation (attempt 4) exited zero in the verified external oracle.
Six theorem dependency audits each returned only `propext`, `Classical.choice`,
and `Quot.sound`. Earlier attempts and their raw errors are retained; the
automatic error-recovery axioms printed during failed attempts are not admitted
evidence. Final source contains no `sorry`, `admit`, or new axiom declaration.

The oracle and frozen primary use Lean 4.31.0 and the same Mathlib/dependency
revisions. Their manifest byte hashes differ only in the mathlib URL spelling,
mathlib scope metadata, and project name. This is a packaging metadata mismatch;
historical exact-environment eligibility is not claimed. The unavailable primary
package path and its symlinks were not repaired or modified.

CAS11 receipts are bound by path and SHA only; their contents and statuses were
not consulted. No sibling engine proof/script/result or historical Lean proof
was read. Requested native runtime was `gpt-6.1-sol/high`; independent observation
of model/effort is UNKNOWN. Separate review is pending at author handoff.

The scientific admission remains HOLD. This theorem does not validate nonlinear
or polarized Compton scattering, CAS16 quadrature, a continuum solver,
BE-reference integrability, derivative-budget bounds, or a cosmological claim.
