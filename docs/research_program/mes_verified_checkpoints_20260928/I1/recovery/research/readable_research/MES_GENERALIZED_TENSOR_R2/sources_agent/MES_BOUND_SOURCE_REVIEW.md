# MES bound source review — R2

Read scope: only MES bound code, MES bound attribution/convention files, and original MES/SAG papers. No other repository research was used. User's exclusion of VIGILODE is respected. This is an independent source-acquisition task, not the final independent decision review.

## Verified source identities

Repository: `cosmosapjw-quantum/htt_base`; code-search resolved default snapshot `50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb`. `REPOSITORY_SOURCE_INDEX.json` records nine files/excerpts, upstream Git blobs, local SHA-256 and read scope. Eight complete file contents were checked against their upstream Git blob IDs; all matched. The theorem-authority excerpt covers original lines 1–235 and is not claimed to match the full-file blob.

Original sources opened in the current turn:

- MESa, *Limits on anisotropy and inhomogeneity from the cosmic background radiation*, PRD 51, 1525 (1995), [arXiv:astro-ph/9501016](https://arxiv.org/pdf/astro-ph/9501016), v1. Read conventions/assumptions pp. 2–4, derivative hypotheses pp. 7–8, equations (50)–(64) pp. 9–10, C1/C2 reduction. The re-typeset PDF prints a later compile date; arXiv v1/source identity takes precedence.
- MES companion, *Anisotropy and inhomogeneity of the Universe from ΔT/T*, [arXiv:astro-ph/9510126](https://arxiv.org/pdf/astro-ph/9510126), v1. Read pp. 3–5, equations (6)–(8), residual-dipole and derivative hypotheses.
- Stoeger–Araujo–Gebbie, *The Limits on Cosmological Anisotropies and Inhomogeneities from COBE Data*, ApJ 476,435 (1997), [arXiv:astro-ph/9904346](https://arxiv.org/html/astro-ph/9904346v1). Read §§2–3, equations (1)–(8), (15)–(19); archived TeX identifies incorporated 1999 erratum corrections.
- MESb, *Improved limits…*, PRD 51, 5942 (1995), [APS abstract](https://link.aps.org/doi/10.1103/PhysRevD.51.5942). Abstract only. Full PDF was inaccessible via the current web tool; no claim about its complete acceleration or non-geodesic content is verified here.

## Source formulas and conditions

The original MESa convention is `c=1`, metric `(-,+,+,+)`, `Θ=3H>0`, and full spatial contraction norm `|X_A|=(X_A X^A)^(1/2)`. Its matter congruence is geodesic (`A_a=0`) and the evolution is first order in almost-isotropy. The covariant multipole amplitudes and their time/spatial derivatives must be small throughout a spacetime domain. The following are source-supported first-order conditional statements, not exact finite-anisotropy theorems.

Let `ε_l` bound the full PSTF temperature-multipole norm, primes spatial derivatives and stars proper-time derivatives, normalized by powers of Θ. MESa:

\[
\frac{\|\sigma\|}{\Theta}
 < \frac83\epsilon_2+\epsilon_2^*+5\epsilon_1'
       +\frac97\epsilon_3' \qquad (51),
\]
\[
\frac{\|\omega_{ab}\|}{\Theta}
 <9\epsilon_1'+3\epsilon_1^{\prime *}
       +\frac65\epsilon_2'' \qquad (52).
\]

The reduced formulas additionally use C1 (spatial/mixed bounds no greater than same-order temporal bounds) and C2 (characteristic-time estimate `ε_l^{*(d)} ≃ ε_l/3^d`):

\[
B_\sigma=\frac53\epsilon_1+3\epsilon_2+\frac37\epsilon_3 \qquad (59),
\quad
B_{\omega,\mathrm{tensor}}=\frac{10}{3}\epsilon_1+\frac{2}{15}\epsilon_2 \qquad (60).
\]

\[
\frac{\|D_a\Theta\|}{H\Theta}
 <\left[\frac{205}{3}+4(2\Omega_R+\Omega_M)\right]\epsilon_1+8\epsilon_2
 \qquad (62).
\]

The expansion result bounds a spatial gradient; it does not bound Θ itself. With physical time rates and a physical inverse-length spatial gradient, the dimensionless LHS is `c ||DΘ||/(H Θ)`. For `ω_a=(1/2) ε_abc ω^{bc}`, `||ω_ab||=sqrt(2)||ω_a||`, hence the vector-vorticity ceiling differs by `1/sqrt(2)`. Source σ is the full tensor norm; scalar conventions `σ²=(1/2)σ_abσ^ab` require the same attention.

The C2 step is an estimated derivative closure. To call the reduced expression a mathematically rigorous upper bound one must separately impose sufficient derivative inequalities, plus any retained perturbation-remainder bound. Using it as a declared first-order reference radius is valid but must retain that label.

There is no nonzero acceleration ceiling in the verified geodesic equations: `A_a=0` is a hypothesis. There is no verified MES tilt-beta ceiling in these opened portions. A nonzero A or beta normalization must have a separately declared/derived reference, not a zero denominator.

## What actually exists in the repository

`htt/tsc/admissibility/three_bound_hierarchy.py` really defines

\[
B_\sigma=(5/3,3,3/7)\cdot\epsilon,\quad
B_\omega^{\rm registered}=(3/4,2,2/7)\cdot\epsilon,\quad
B_A^{\rm registered}=(3/4,1,3/14)\cdot\epsilon.
\]

The existence of shear-external MES-style formulas is therefore confirmed, as the user said. The latter two coefficient rows do not match the opened original equations. Earlier repository prose attributes them to MESb; the later MES-only provenance/authority files explicitly withhold these as verified source bounds. The current source review does NOT inherit their historical verdict as a proof: absence from accessible text shows **unverified attribution**, not universal mathematical falsity. MESb full text remains unresolved.

`htt/bass/observational/planck_mes_bounds.py` also preserves a different legacy set, `2ε2`, `sqrt(3) ε2`, `max(3ε1_res,2ε2,ε3)`, and declares `LEGACY_REPRODUCTION_ONLY=True`. Its scalar-rms epsilon convention differs from the full PSTF norm. These should not be mixed into a common denominator without translating both norm and assumptions. No Planck values or other repo science were imported into this research loop.

The theorem-authority bound table itself gives the accessible geodesic shear and vorticity rows above, structural zero acceleration, and unverified non-geodesic rows. No attempt was made to execute repository governance or certify all live consumers.

## Multipole norm translation

For orthonormal `Y_lm` and dimensionless temperature `τ(n)=Σ_l τ_{A_l} n^{A_l}=Σ_lm a_lm Y_lm`,

\[
\|\tau_{A_l}\|^2=\frac{(2l+1)!!}{l!}
    \frac{1}{4\pi}\sum_m|a_{lm}|^2.
\]

If `a_lm` carry temperature units, divide the RHS by `T0²`. For an empirical `C_l=(2l+1)^{-1}Σ_m|a_lm|²`, this introduces the factor `(2l+1)!!/l!` beyond the scalar sky RMS. At l=2,3 the factors are `15/2` and `35/2`, agreeing with SAG equations (18),(19). This is an exact representation/norm identity, not an inference of kinematics from `C_l`.

## Recommended source boundary for the R2 construction

Use conditional radii `b_s(d,z; H)` with explicit norm, congruence, derivative hypotheses and approximation order. The general tensor/likelihood construction can admit an arbitrary positive user-declared reference radius while only selected radii carry a literature MES claim. It need not block generalization to A, omega, theta or beta because an old acceleration attribution is unresolved. A zero/missing radius is represented as zero-radius/null or uncalibrated, not silently assigned a finite MES ceiling. No particular Bianchi class is selected in this source review.

Evidence states: bound implementation existence **verified by current source/blob read, not runtime-certified**, original geodesic formulas and hypotheses **literature-supported**, norm translation **derived and source-crosschecked**, non-geodesic A/omega attribution and MESb full content **unresolved**. Exact rational reductions were executed independently in Python and recorded in `EXACT_REDUCTION_CHECK.json`; no imported repository module was executed. No observational inference or universal generalized MES theorem is claimed.
