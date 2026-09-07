# K4 — exact-scope manuscript replacement text

Date: 2026-09-05  
Status: CORRECTION_TEXT_WRITTEN_NOT_YET_APPLIED_TO_FULL_MANUSCRIPT

Target: `docs/research_reports/drafts/HTT_REPORT_A_FULL_KINEMATICAL_MES_DRAFT_K3_20260905.md`  
Target Git blob: `3d509ebcb178bd26b96d994690668e225a133dc9`  
Reviewed target head: `228ce70267fcdd27942a371a54a8c30b0bc1e696`.

These blocks are complete replacement prose for the named sections. They are
not a new canonical manuscript or a machine-applied patch. Preserve the target
and its source provenance. If its bytes have changed, compare the live text
rather than blindly applying these replacements. Do not modify production
physics, thresholds, the T5 theorem, or the canonical claim ledger to implement
this editorial correction.

## Replacement A — Section 5.1 only

### 5.1 Multipole normalisation, rate convention and inherited ceilings

In the retained PSTF normalisation,

\[
\epsilon_2=\frac1{T_0}\sqrt{\frac{75C_2}{8\pi}},
\qquad
\epsilon_3=\frac1{T_0}\sqrt{\frac{245C_3}{8\pi}}.
\]

These quantities are dimensionless when the harmonic coefficients and the
positive monopole temperature \(T_0\) use consistent temperature units. The
residual dipole amplitude \(\epsilon_1\) is a declared attribution scenario,
not a result obtained by inverting a scalar bound. The observed multipole
normaliser is not, by itself, proof of the all-observer anisotropy or derivative
bounds required by the physical MES implication.

The retained theorem is used on its expanding geodesic branch. Choose a common
rate convention with \(H=\Theta/3>0\). For rates defined geometrically from
the unit observer, \(\Theta_g=\nabla_a u^a\) and \(H_g=\Theta_g/3\) have
inverse-length units. The corresponding inverse-time rates satisfy

\[
H_t=cH_g,\qquad \sigma^{(t)}_{ab}=c\sigma^{(g)}_{ab},
\qquad \omega^{(t)}_{ab}=c\omega^{(g)}_{ab}.
\]

The dimensionless quadratic ratios below are identical in those two consistent
conventions. A geometrical numerator must not be combined with an
inverse-time Hubble denominator without the conversion.

The source magnitude is the full tensor contraction,
\(|\sigma|^2=\sigma_{ab}\sigma^{ab}\) and
\(|\omega|^2=\omega_{ab}\omega^{ab}\), rather than the alternative
half-contraction scalar convention. The source defines this norm and prints
the retained coefficient combinations in its MES equations. The independent
PSTF conversion factors are \(15/2\) for the quadrupole and \(35/2\) for the
octupole. [@SAG_1999_COBE]

After the maintained gradient and characteristic-time estimates, write

\[
B_\sigma=\frac53\epsilon_1+3\epsilon_2+\frac37\epsilon_3,
\qquad
B_\omega=\frac{10}{3}\epsilon_1+\frac{2}{15}\epsilon_2.
\]

The inequalities \(|\sigma|/\Theta<B_\sigma\) and
\(|\omega|/\Theta<B_\omega\) then imply

\[
\psi_\sigma(X)=\frac{\sigma_{ab}\sigma^{ab}}{6H^2}
<U_\sigma=\frac32B_\sigma^2,
\qquad
\psi_\omega(X)=\frac{\omega_{ab}\omega^{ab}}{6H^2}
<U_\omega=\frac32B_\omega^2.
\]

The factor \(3/2\) follows from \(\Theta^2/(6H^2)\); it is not altered by
changing consistently between inverse-length and inverse-time rates. The
vorticity vector-to-tensor adapter remains part of the registered convention.
An axial-vector norm cannot be substituted for the antisymmetric-tensor
contraction without that adapter. [@MES_1995_LIMITS; @MES_1995_IMPROVED;
@SAG_1999_COBE]

For maintained choices \(\eta\), the closed outer sector body uses
\(\psi_j(X)\le U_j(y;\eta)\). This non-strict form is a conservative
closure of the source restriction, not a claim of physical saturation.
The data argument is retained when the ceiling is constructed from the same
sky as other parts of the analysis. A fixed external or ensemble calibration
is a distinct conditioning regime.

All-observer or Copernican extension, the declared frame and congruence,
geodesic almost-EGS branch, derivative-hierarchy reduction and residual-dipole
scenario remain substantive premises. Compliance with the sector body does not
establish those premises, a converse FLRW result or an observation of shear or
vorticity. Optional sectors receive no anchor by analogy, and degenerate
zero-radius cases are not admitted to the positive-radius division formulas.

## Replacement B — Section 8.2 only

### 8.2 Quadrupole-to-octupole response, adjoint and inverse

Use the Euclidean vector inner product and the full STF3 Frobenius contraction
\(\langle O_1,O_2\rangle_F=(O_1)_{abc}(O_2)_{abc}\). For the registered
STF projection convention,

\[
(B_Q\beta)_{abc}=3\beta_{\langle a}Q_{bc\rangle}.
\]

For STF3 \(O\), symmetry and trace-freeness give

\[
O:B_Q\beta=3\beta_aO_{abc}Q_{bc},
\qquad (B_Q^*O)_a=3(O:Q)_a.
\]

Define the contraction matrix

\[
M_Q=q_2I+\frac65Q^2,\qquad q_2=Q:Q.
\]

Direct contraction of the Cartesian STF response yields

\[
(B_Q\beta):Q=M_Q\beta,
\qquad
\boxed{B_Q^*B_Q=3M_Q},
\qquad
\|B_Q\beta\|_F^2=3\beta^TM_Q\beta.
\]

Thus \(M_Q\) is one third of the Frobenius normal matrix, not the unscaled
normal matrix itself. The distinction affects absolute response norms, even
though a common positive scalar does not change a condition number.

For \(Q\ne0\), \(q_2>0\) and \(Q^2\succeq0\), so \(M_Q\succ0\).
The algebraic least-squares response coordinate is

\[
\widehat\beta_{\rm LS}
=(B_Q^*B_Q)^{-1}B_Q^*O
=M_Q^{-1}(O:Q),
\]

and the Frobenius-orthogonal response projector is

\[
P_{\operatorname{Im}B_Q}O=B_QM_Q^{-1}(O:Q).
\]

The factor of three cancels between the two sides of the normal equation.
The residual \(O_\perp=O-P_{\operatorname{Im}B_Q}O\) satisfies
\(O_\perp:Q=0\). Since \(B_Q\) has rank three and STF3 has dimension seven,
the response-orthogonal residual space is four dimensional.

The sharp conditioning result also survives unchanged. Up to scale, sign and
permutation, take the quadrupole spectrum as \((-1,1-t,t)\) with
\(0\le t\le1/2\). Then

\[
\kappa_2(M_Q)=\frac{8-5t+5t^2}{5-5t+8t^2},
\qquad
\frac53-\kappa_2(M_Q)
=\frac{(5t-1)^2}{3(5-5t+8t^2)}\ge0.
\]

Consequently

\[
\kappa_2(M_Q)=\kappa_2(B_Q^*B_Q)\le\frac53,
\qquad \kappa_2(B_Q)\le\sqrt{\frac53}.
\]

Equality is obtained for spectra proportional to \((-5,4,1)\). These are
conditioning bounds on the nonzero-quadrupole domain. They do not give a
quadrupole-amplitude-independent bound on absolute inverse sensitivity as
\(Q\to0\).

The algebraic coordinate and projector are response-space constructions, not
an empirical velocity analysis. The residual is not automatically a physical
intrinsic octupole, and local-boost and intrinsic-dipole interpretations remain
distinct physical hypotheses. [@ROLDAN_NOTARI_QUARTIN_2016]
The response closes only the stated \(\beta_{\rm RO}\) lane; it does not
identify \(\beta_{\rm RM}\), \(\beta_{\rm MO}\), shear or global matter-frame
tilt.

## Replacement C — Section 11.2 only

### 11.2 Conditional robust rank and subspace limits

Write \(K_{\rm obs}=K_{\rm true}+\Delta\) and
\(W=\Gamma_E^{-1/2}\), using the same declared source/output metric. If the
actual numerical error belongs to the frozen class, then

\[
\Delta\Delta^T\preceq\Gamma_E,
\qquad \|W\Delta\|_2\le1.
\]

The singular-value perturbation bound gives

\[
s_i(WK_{\rm true})\ge s_i(WK_{\rm obs})-1.
\]

Therefore

\[
\operatorname{rank}K_{\rm true}
\ge\#\{i:s_i(WK_{\rm obs})>1\}.
\]

For an \(m\times n\) response with \(m\le n\), a sufficient full-row-rank
criterion is

\[
s_m(WK_{\rm obs})\ge1+\delta,
\qquad \delta>0,
\]

where \(\delta\) is fixed before rank inspection. This places the margin
explicitly above the unit perturbation floor. Whitening makes the criterion
dimensionless in the declared metric; preregistration alone would not make a
threshold at or below one a positive-rank certificate.

The implication remains conditional. It does not establish that the present
finite-HEALPix family registry contains the actual error, and it does not
permit tuning radii after inspecting the signal. Coverage of the numerical
error class is a separate mathematical and computational obligation.

A rank lower bound also does not certify singular-subspace orientation. A
stable nuisance projector requires perturbation control relative to a positive
singular-value gap. Singular-subspace perturbation results supply that
additional type of bound; it does not follow from counting singular values
above one. [@CAI_ZHANG_2018; @LI_1999; @LYU_WANG_2020]

## Application boundary

Only the three named passages are replacement targets. Preserve the twelve
section structure, the forty candidate IDs, existing numerical tables, original
source identities and deferred-observation/no-native-solver boundaries.
The new adjoint and inverse text restores T5's explicit normalisation; it must
not be used to relabel an old numerical result or silently alter a runtime
implementation. The common rate convention makes the existing MES implication
explicit. The robust-rank margin makes the existing unit perturbation floor
explicit. None of these changes requires a new physical response provider.

The full K3 manuscript remains unchanged until these blocks are deliberately
applied and read back. This file is not proof of that application, a compiler
receipt, a CAS result, a PDF build or publication approval.
