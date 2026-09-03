# Report A R2D — MES primary-source equation and premise audit

Date: `2026-09-03`  
Scope: HTT theory/methods only; no observational execution

## Terminal

```text
PASS_MES_PRIMARY_SOURCE_EQUATION_AND_PREMISE_BINDING
/
FRESH_SYMPY_NORMALIZATION_REPLAY_PASS
/
FRESH_WOLFRAM_REPLAY_BLOCKED_BY_UPSTREAM_502
/
NO_OBSERVATIONAL_OR_PHYSICAL_PARAMETER_PROMOTION
```

## 1. Primary-source identities

The coefficient and premise chain is bound to three distinct sources.

1. Roy Maartens, George F. R. Ellis, and William R. Stoeger,
   *Limits on anisotropy and inhomogeneity from the cosmic background
   radiation*, Phys. Rev. D **51**, 1525 (1995),
   DOI `10.1103/PhysRevD.51.1525`, arXiv `astro-ph/9501016`.
2. Roy Maartens, George F. R. Ellis, and William R. Stoeger,
   *Improved limits on anisotropy and inhomogeneity from the cosmic background
   radiation*, Phys. Rev. D **51**, 5942 (1995),
   DOI `10.1103/PhysRevD.51.5942`.
3. William R. Stoeger, Marcelo E. Araujo, and Tim Gebbie,
   *The Limits on Cosmological Anisotropies and Inhomogeneities from COBE
   Data*, Astrophys. J. **476**, 435 (1997), DOI `10.1086/303633`,
   arXiv `astro-ph/9904346`.

The second paper is used as the bibliographic authority for the improved
observational-premise programme. The equation-level coefficient and
normalization binding below comes from the accessible first and third primary
texts rather than from a secondary summary.

## 2. Premises in the 1995 derivation

The 1995 derivation uses signature `(-,+,+,+)` and a fundamental matter
congruence whose four-velocity is geodesic. It studies freely propagating CMB
radiation after last scattering in an expanding domain and assumes almost
isotropy for all relevant fundamental observers, not merely one local
observer.

The final numerical bounds additionally introduce the explicitly named
estimates:

- **C1:** spatial gradients of the CMB multipoles are not larger than the
  corresponding characteristic time derivatives;
- **C2:** characteristic time derivatives are estimated by a radiation
  timescale, producing the stated reduced derivative bounds.

These are premises of the implication. Report A does not infer C1, C2, or the
all-observer Copernican extension from one observed sky.

## 3. Equation-level coefficient binding

After C1 and C2, Eqs. (59) and (60) of arXiv `astro-ph/9501016` give

\[
\boxed{
\frac{|\sigma_{ab}|}{\Theta}
 < \frac53\epsilon_1+3\epsilon_2+\frac37\epsilon_3
}
\]

and

\[
\boxed{
\frac{|\omega_{ab}|}{\Theta}
 < \frac{10}{3}\epsilon_1+\frac{2}{15}\epsilon_2
}.
\]

The same coefficient pair is printed as Eqs. (3) and (4) in the COBE bridge.
The coefficients are therefore literature-supported; Report A does not claim
to have independently rederived the complete Einstein--Liouville estimate
leading to C1/C2 and Eqs. (59)/(60).

## 4. Harmonic-to-PSTF normalization

The COBE bridge gives

\[
\Delta T_\ell^2
 =\frac{1}{4\pi}\sum_m|a_{\ell m}|^2
 =\frac{2\ell+1}{4\pi}C_\ell
\tag{15}
\]

and

\[
\tau_{A_\ell}\tau^{A_\ell}
 =\frac{(2\ell+1)(2\ell)!}{2^\ell(\ell!)^2}
  \frac{\Delta T_\ell^2}{T_0^2}.
\tag{17}
\]

For `ell=2,3`, the factorial coefficients are

\[
\frac{15}{2},\qquad \frac{35}{2},
\]

which correspond to Eqs. (18) and (19) in that paper. Therefore

\[
\boxed{
\epsilon_2^2=\frac{75C_2}{8\pi T_0^2}
},
\qquad
\boxed{
\epsilon_3^2=\frac{245C_3}{8\pi T_0^2}
}.
\]

A fresh exact SymPy calculation reproduced both factorial coefficients and
both zero residuals. With

\[
U_\omega=\frac32
\left(\frac{10}{3}\epsilon_1+\frac{2}{15}\epsilon_2\right)^2,
\]

it also reproduced

\[
\left.U_\omega\right|_{\epsilon_1=0}
 =\frac{C_2}{4\pi T_0^2}
\]

with exact zero residual.

## 5. Residual dipole semantics

Equation (12) of the COBE bridge adopts `epsilon_1=0` by attributing the
observed CMB dipole to peculiar motion. The same text acknowledges the
possibility of a non-Doppler residual. Consequently:

```text
epsilon_1=0 = declared attribution scenario
not = measured intrinsic-dipole theorem
```

This is consistent with Report A's local-observer/global-state firewall.

## 6. Claim classification

| Item | Evidence grade | Allowed report role |
|---|---|---|
| coefficients in the shear/vorticity inequalities | `LITERATURE_SUPPORTED` | premise-conditioned scalar bounds |
| harmonic/PSTF conversion | `DERIVED_EXACT` and source-bound | normalization theorem |
| conversion to `U_sigma,U_omega` | `DERIVED_EXACT` | standard-variable algebra |
| one-way implication | `ESTABLISHED_WITH_PREMISES` | claim ceiling |
| `epsilon_1=0` | `SCENARIO_INPUT` | sensitivity branch only |
| physical shear/vorticity estimate | `NOT_PERFORMED` | forbidden |
| converse almost-FLRW certificate | `NOT_ESTABLISHED` | forbidden |

## 7. Tool receipt

A fresh Wolfram replay was attempted during R2D but the evaluator returned an
upstream HTTP 502. The exact normalization was therefore independently replayed
with SymPy. Earlier durable Wolfram receipts remain valid at their bound source
identity, but the failed fresh call is not counted as a new Wolfram pass.

## 8. Remaining Report-A blockers after this audit

The MES equation/premise P1 is closed. The remaining load-bearing P1 items are:

1. exact-head GitHub execution remains `PRESTART_NO_EXECUTION` for PR #450,
   PR #451, and the report branch;
2. PR #451's packet decoder still lacks a sealed forward/inverse numerical
   stability domain and final round-trip certificate.

No observation-bearing result or BASS/native-solver result is introduced.
