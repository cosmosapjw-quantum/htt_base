# Proof Obligations and Claim Status

문서 목적: theorem이 engineering claim을 자동으로 대신하지 않는다는 원칙을 고정한다. 이 문서는 what-is-proved와 what-remains-to-be-proved를 분리한다.

---

## 1. Top-level claim, corrected

Defensible top-level claim:

> Full state transport should be carried by a closure-free characteristic reference. Teff remains a blockwise reduced chart for trace/intensity semantics, source reconstruction, and diagnostics.

Not defensible:

> Characteristics is the full transport closure and Teff completes the full Boltzmann hierarchy solver.

---

## 2. Claim levels

| Level | Meaning | Example |
|---|---|---|
| E | established in current manuscripts | Paper I tangency diagnostic |
| C | conditional theorem | Paper IV local observable bound |
| S | synthesis/architecture | closure-free characteristics + Teff trace chart |
| V | validation obligation | TT/TE/EE/BB adequacy tests |
| F | future theorem/programmatic | full 1+3 covariant production solver |
| X | forbidden as written | characteristics as full closure |

---

## 3. PO-A: abstract reduction geometry

### PO-A1. Tangency and defect

Obligation: distinguish ambient defect from projected defect.

Required equations:

\[
\left.\frac{d}{dt}(U_tg-S_tg)\right|_0=Q_g\mathcal G(g),
\]

but

\[
\left.\frac{d}{dt}(\Pi U_tg-S_tg)\right|_0=0
\]

under the usual smooth projection setup.

Status: synthesis theorem/geometry obligation; must be stated with assumptions.

### PO-A2. Collision-side vs state-side residual

Obligation: connect collision production residual to state residual if using diagnostic to claim observable adequacy.

Status: open dynamical obligation unless proven or numerically validated.

---

## 4. PO-B: blockwise reduction architecture

### PO-B1. Direct-sum consistency

Need to prove or assume the state decomposition

\[
\mathscr H=\mathscr H_{\rm res}\oplus\mathscr H_{\rm red}
\]

is respected by the intended projection and source splitting.

### PO-B2. Resolved block non-closure

Need to state that resolved characteristic blocks are not closed by Teff. They are transported as part of the reference state.

Status: architectural definition, not a theorem about numerical accuracy.

---

## 5. PO-C: covariant characteristic transport

### PO-C1. Local characteristic existence

Need local existence of phase-space characteristics for the chosen metric/tetrad/observer split.

### PO-C2. Screen-basis transport

For polarisation, need screen-basis consistency and gauge/basis transformation control.

### PO-C3. Collision/source integration

Need source/collision integration consistent with target Boltzmann equation.

### PO-C4. Convergence

Need numerical convergence in:

- timestep,
- ray/angle resolution,
- energy/frequency resolution,
- source quadrature,
- screen-basis transport,
- spatial interpolation.

Status: validation + numerical analysis obligation.

---

## 6. PO-D: dynamical adequacy

A local diagnostic does not imply global adequacy. Need estimates of the schematic form

\[
\|X_{\rm exact}(t)-X_{\rm hyb}(t)\|
\le
\int_0^t K(t,s)\,\|q_{\rm red}(s)\|\,ds
\]

where `q_red` is the reduced-block source residual.

Status: future theorem or validated empirical bound.

---

## 7. PO-E: observable and spectrum adequacy

Need to map state errors to observable errors:

\[
\Delta C_\ell^{XY}
\le
\mathcal K_{XY}[\Delta X]
\]

or equivalent numerical calibration.

Channel-specific obligations:

- TT: trace reconstruction and propagation.
- TE: trace source plus E propagation.
- EE: source adequacy and spin-2 propagation.
- BB: full spin-2 necessity; trace Teff is insufficient.

Status: mostly validation/programmatic.

---

## 8. PO-R: realizability and switching

Teff chart has an admissibility domain, e.g.

\[
\Theta(\hat e)>0.
\]

For polarisation-like extensions one also needs constraints such as degree-of-polarisation bounds.

Obligations:

1. detect approach to boundary,
2. switch to resolved representation before breakdown,
3. avoid chattering by dwell-time/hysteresis rules,
4. prove or validate that switching preserves conservation and consistency.

Status: future theorem + runbook validation.

---

## 9. Claim-to-obligation table

| Desired claim | Required obligations | Current status |
|---|---|---|
| Teff diagnostic identifies spectral-shape forcing | Paper I tangency theorem | established under assumptions |
| eta dipole is non-redundant | Paper II non-redundancy + rank evidence | established/partly numerical |
| two-field entropy geometry is coherent | Paper III Gram-Hessian | established |
| observable reconstruction is locally controlled | state residual + Jacobian + local calibration | conditional |
| Thomson source bridge is exact | trace block on Teff manifold | established |
| hybrid solver is accurate | transport convergence + residual propagation + observable map | open validation |
| full Boltzmann solver | full phase-space/tensor/species/collision implementation + convergence | not yet established |
| characteristics is closure | impossible terminology | forbidden |

---

## 10. Kill-switches

The program must weaken its claims if any of these occur.

### K1. Diagnostic-state mismatch

If collision diagnostics fail to predict state residual growth, then Paper I diagnostics remain local collision monitors only.

### K2. Poor Jacobian conditioning

If `sigma_min(J)` becomes small in relevant regimes, Paper IV local reconstruction claim must be restricted to well-conditioned domains.

### K3. Spin-2 contamination

If trace-source adequacy does not predict EE/TE errors because spin-2 propagation dominates, then Teff should be advertised only as source semantics, not observable adequacy.

### K4. Characteristic convergence failure

If full characteristic reference does not converge, Teff validation against it is meaningless.

---

## 11. Recommended proof-obligation summary paragraph

> The current theorem chain establishes reduced-manifold geometry, local diagnostics, observable semantics, and an exact trace-sector source bridge. It does not by itself establish a full transport solver. Solver-level claims require a separate characteristic convergence theory, residual propagation estimates, channelwise observable-error control, and switching/realizability validation.
