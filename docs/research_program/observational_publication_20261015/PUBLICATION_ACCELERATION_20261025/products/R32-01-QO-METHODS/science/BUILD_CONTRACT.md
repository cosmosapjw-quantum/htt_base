# Scientific contract for the Q/O methods paper

The scientific author owns this `science/` directory. The lower-tier build worker owns the disjoint report/build directory and implements the equations, figures, numerical tables and manuscript layout below. This is a complete deterministic/conditional methods paper, not a physical-detection or original42 acceptance product. The execute result waits for the actual complete candidate; the host then records it to obtain the fresh review packet. Final product qualification follows independent review.

## Inputs and notation

Use the current `EVIDENCE_MANIFEST.json` and only its relevant retained inputs. Check their recorded SHA-256 values before consumption; do not rerun the historical scripts in place, since several write to retained source folders. The manuscript source is `MANUSCRIPT.md` here. `RESEARCH_NOTE.md` contains comparison/provenance and is not manuscript prose.

Write `C_Q:STF_3 -> R^3`, `C_Q O=O:Q`, `L_Q=C_Q^*`, and `M_Q=C_Q L_Q=t I/3+2Q^2/5`, with `t=Q:Q`. Full ordered-index Frobenius norms are mandatory. Distinguish `Q` the quadrupole tensor from the scalar policy score `Q_cpl`. Use `a` for the synthetic amplitude to avoid overloading `t`.

## Figure 1: attained geometry

Make a two-panel vector PDF. Left: the section `z_3=1/sqrt(3)` of the normalized contraction ball `z_1^2+z_2^2+z_3^2<=1`; draw its circle radius `sqrt(2/3)` and the four balanced points `(±1/sqrt(3),±1/sqrt(3))`. Caption says the complementary four extrema lie in `z_3=-1/sqrt(3)`. Color by the product sign; this is a section, not the entire 3D ellipsoid. Right: `E(r)=sqrt((1-6r)*(1+3r/40))`, with `0<=r<=1/6`, plot `±E(r)` and mark `(0,±1)` and `(1/6,0)`. These are analytic quantities, not sample probabilities.

Figure caption: "Attained contraction geometry. At fixed quadrupole and octupole norm the normalized contraction vector fills the unit ball. The displayed section contains four of the eight simple-spectrum extremizers; the remaining four lie in the opposite section. The fixed-norm fibre is a translated three-sphere in the interior and a singleton on the boundary. The right panel shows the sharp signed shape envelope, which reaches both global endpoints at a zero-cubic-trace quadrupole and vanishes at repeated eigenvalues."

## Figure 2: analytic extremizer and mirror

Use `Q*=diag(-1/sqrt(2),0,1/sqrt(2))`, `w*=(sqrt(10)/4,1,sqrt(10)/4)`, and the explicit lift `O*=L_Q* w*`. Construct tensor entries directly from the stated lift. `R=diag(-1,1,1)` gives `Q'=R Q* R^T`, `O'=R^{otimes3}O*`. Plot `Q*:nn+O*:nnn` and its reflected field on common Mollweide color limits. Show `C=+1`, `C=-1`. Optional separate quadrupole and octupole panels may be added if legible. Do not label these as sky data or optically realized exact fields.

Required targeted checks, absolute tolerance `1e-12`: STF traces, symmetry, both tensor norms equal one, `C=±1`, contraction equals `(2sqrt(10)/15,1/3,2sqrt(10)/15)`, reflected angular field parity. Compare numeric values against retained `evidence/baseline/output/geometry_checks.json`. The tolerance tests implementation of displayed analytic formulas; the general result is proved in the manuscript.

Figure caption: "An analytic pair attaining the sharp constant and its mirror. Both STF tensors have unit Frobenius norm. Reflection preserves their norms and reverses the determinant coordinate. The fields illustrate the algebraic theorem; the exact logarithmic optical response has its separately stated amplitude and remainder restrictions."

## Figure 3 and numerical table: retained optical calculation

Consume `evidence/baseline/research/theory_bridge_result.json` without repeating angular integration. It has 45 saved amplitudes, primary 40x80 and comparison 60x120 spherical quadratures, seven retained exact-rational checks, and maximum tensor difference `1.2046551275404449e-14`. Each row gives amplitude, epsilon_upper, coupled_exact_norm, coupled_quadratic_norm, pure_dipole_exact_norm, pure_dipole_cubic_norm, coupled_remainder_norm, remainder_bound, quadrature_difference.

Plot two log-log panels: (a) exact coupled versus quadratic and pure-dipole exact versus cubic octupole norms; (b) coupled remainder norm versus `E3(epsilon)` bound. Parameter family is `d=a*(1,2,3)/sqrt(14)`, `S=a*diag(.6,-.2,-.4)`, `0.002<=a<=0.25`, `epsilon=1.6a<=.4`. All norms and remainders are in magnitude units; `a,epsilon` are dimensionless. Validate finite values, monotone saved amplitudes, all 45 stored bound inequalities, and the formula for E3. The scalar check tolerance is `1e-12*max(1,abs(expected))`; no historical solver/CAS replay.

Generate a small table using saved row indices `0,11,22,33,44` (zero based), columns `a`, exact coupled norm, quadratic norm, actual remainder, analytic bound. Do not replace these by round target amplitudes. Use six significant digits with scientific notation as appropriate. A short prose line reports actual row count and maximum retained two-grid difference. This is numerical quadrature consistency evidence, not a rigorous quadrature-error bound.

Figure caption: "Nonlinear local magnitude response for the specified synthetic acceleration and shear. The coupled octupole is quadratic at small common amplitude, whereas the pure-dipole response begins at cubic order. The right panel compares the saved exact-logarithm projection error with its analytic finite angular envelope. Curves consume the retained 45-row quadrature result; finite-redshift propagation and observational errors are separate inputs."

## Build requirements and precise result boundary

Use a readable RevTeX research-paper layout and actual bibliography entries for the primary sources named in the manuscript. Preserve all equations, assumptions and undefined sectors when translating Markdown mathematics. Equation numbering/line breaking/layout are worker responsibilities. No need for a style pilot. The optional processed-map example is omitted: the paper is complete with the analytic and synthetic figures above.

Deliver the runnable retained-input consumer, generated numerical table/figures/data summary, complete English `main.tex` and `main.pdf`, build log and result metadata containing exact source/consumer/candidate identities. Return actual check/build commands, outcomes and candidate paths to the scientific author and root. Do not emit a qualified product or final controller PASS on the basis of this contract or the draft alone. The author will consume the actual candidate and return the execute-candidate result; root will record it and arrange one fresh independent scoped review.
