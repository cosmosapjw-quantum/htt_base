# Independent review: R32-05-P6-OPTICAL

**Verdict: HOLD for the exact candidate `optical_inverse_note`.** One bounded mathematical correction is required in Theorem 2. The remaining reviewed mathematical, numerical, unit, provenance, claim and presentation requirements are satisfied within their explicitly conditional scope. This is not a controller qualification, original42 acceptance, physical detection or publication decision.

Formal review packet: **PENDING_SCHEDULER_FAIRNESS**. No formal review packet ID, acknowledgment or qualified controller state is asserted. This assessment can be bound to the later actual packet for the same candidate without repeating the completed full review.

Requested reviewer: `gpt-6-astra/xhigh`; observed runtime identity: **UNKNOWN**. This reviewer did not author or build the candidate. Excluded authors are `/root/rc_4061878216a65321` and `/root/r35_p6_prescribed_build`. All repository and controller files were read-only. Review output is restricted to this directory; no children, Git mutation, publication or scientific solver replay occurred.

## Exact candidate

- Root: `/home/cosmosapjw/Dropbox/bianchi/htt_base`.
- Product: `docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-05-P6-OPTICAL`.
- `report/RESULT.json` SHA-256: `343622f6bed1197dd0e08b7c64fbfabefba74f5ec02baf9a51b839dda97ae9b3` at intake and closeout.
- Canonical embedded manifest SHA-256: `341346452c546de7877bf839bde8e583e37c8c461703469644ab7675edba1bfd`.
- All 80 sealed source/output entries match their hashes and sizes. Scientific source, report, figure, table, raw failure and build files are bound by that manifest.
- Branch/HEAD at intake: `research/htt-adaptive-methods-20261023`, `dff1f6a330bffec122225c3b0e8edb19e8b7d122`. Existing dirty state was recorded and left intact.

## Blocking finding P6-IR-01 — add feasibility to the infinite-support branch

**Severity: P2; mathematical domain error, bounded repair.**

Locations: `science/MANUSCRIPT.md:172` (proof at line 178), `report/main.tex:183` (proof at line 189), rendered PDF page 5.

The theorem says that if `J^T a` has a nonzero component in `ker A`, the support is `+infinity`. This requires a feasible base point, equivalently `E_z != empty`. The theorem itself admits arbitrary observations and tests feasibility, so this hypothesis cannot be assumed globally.

Take

```
A = diag(1, 0), z = (0, 2), E = {e : ||e||_2 <= 1},
J = (0, 1), a = 1.
```

Range compatibility forces `e_2 = 2`, which is impossible in the unit ball. Hence `E_z` and `Theta_lin(z)` are empty. Nevertheless `J^T a = (0,1)` is a nonzero kernel vector. The literal statement predicts `+infinity`; the support of the empty image is `-infinity` under the extended-real convention, or undefined if that convention is not adopted. It is never `+infinity`. The proof's scaling argument cannot begin without a feasible parameter.

Independent optimization also reproduced the distinction in a nondiagonal rank-two 4-by-3 model: the kernel-visible objective is unbounded for feasible residual data, while changing the fourth observation beyond the allowed error box makes it infeasible. The saved candidate checks test infeasibility for an identified carrier but do not cover this kernel-visible empty branch.

**Minimal bounded repair definition:**

1. Scientific author adds `E_z != empty` to the infinite-support statement and its proof. State the empty-set case explicitly: `E_z = empty` gives an empty parameter/image set; choose either `h_empty = -infinity` or leave support undefined there. Do not change the finite inverse, range test, tensor result or physical assumptions.
2. Lower-tier builder incorporates the correction in TeX/PDF and refreshes only affected candidate bindings and build records. Preserve the original candidate and first failures as historical evidence. The 61-check consumer need not be replayed, and unchanged numerical tables/figures remain reusable.
3. Add or retain the above tiny feasible/infeasible kernel-visible case as a focused boundary check. Closeout checks the final statement/proof, rendered page and new identity against this finding. A full repeated review, catalogue run, spherical quadrature or CAS campaign is unnecessary.

This is a correction to the exact methods statement, not a failure of the measured CF4 tensor or of the residual-compatible formula (17).

## Physics and mathematics audit

Assumptions inspected: signature `(-+++)`, proper length `c tau`, observer-to-source `n`, past null vector `-u+n`; same-event/congruence optical law; positive angular rate; normalized full-sphere measure; `||q||_infinity <= epsilon < 1`; bounded sampling rows; invertible working W; linear nuisance family; finite error sets; unrestricted linear parameter domain unless intersected with an explicitly supplied physical domain.

| Item | Assessment | Evidence and scope |
|---|---|---|
| Local optical sign/units | Satisfied | Direct rest-frame contraction returns `H - A.n/c + sigma:nn`; antisymmetric vorticity cancels. Source law is conditional on its stated congruence and local expansion. |
| Complete-field inverse, equations (5)–(8) | Satisfied | Reviewed normalized exponentiation, intercept cancellation, exact spherical moments, positive-weight ratio bound, orthogonal harmonic projection and both norm constants. Finite positive-weight error probe passed; no spherical integration was repeated. |
| Composed map and finite remainder, (9)–(15) | Satisfied | Nuisance projection, whitening transpose, signed-window total variation, logarithmic tail and Minkowski support are consistent. Enumerated finite box corners with nonsymmetric W independently attain the claimed outer support. Nonlinear tail dependence remains explicitly enlarged. |
| Exact linear inverse, (16)–(19) | HOLD at the infinite-support domain only | Kernel/range proof and nondiagonal LP support checks agree. Rank-zero, physical-domain intersection and tangent-versus-global distinctions are retained. Empty feasible sets require the finding above. |
| Tensor product-error image, (20)–(22) | Satisfied | Full five-dimensional C and basis retained; product-set assumption explicit. Independent singular-PSD/nonidentity-G support witness passed. The scalar ball is an outer summary only. |
| CF4 units and basis, (23)–(27) | Satisfied | Exact current producer SHA matches the cited model. Source `register('shear', -KAPPA*response)` and basis sign confirm the coefficient is already dimensionless. Norm `0.03265680189321492` and ordered spectrum agree. No second kappa/H division. |
| Physical-radius bounds, (28)–(32) | Satisfied conditionally | Independent attaining tensors reproduce all six table rows. Lower endpoint is positive iff `r_Q < t`; H multiplies conversion to dimensional rate. All physical response/error/H inputs remain assumed rather than calibrated. |
| Tensor carrier and x/Q/F/Pi/G_F, (33)–(35) | Satisfied | Full carrier retained, absent physical sectors unresolved, positive policy denominator required, no invented measure or joint law. MIO deterministic image and HTT probability ownership remain distinct. |

For the actual C, full five-dimensional support witnesses reproduce the displayed projection exactly at tested directions. A centered section would have a different x support (`0.00372521879618` versus projection `0.00374934050118`); the zero-hidden-coordinate section of the eta=0 ellipsoid is empty (minimum ellipsoid cost `26.56949 > 1`). This directly checks that the figure represents a projection.

## Evidence and validation

Read the full `MANUSCRIPT.md`, `BUILD_CONTRACT.md`, `RESEARCH_NOTE.md`, generated claim map, all 61 saved checks and their producing code, full retained tensor/C, figure data, table data, candidate source/build code, source identities, raw build/recovery receipts and actual PDF. Repository guidance used: AGENTS, CURRENT_CODEX_RUNTIME, physics/math audit, manuscript/figure audit, claim firewall/provenance, xqpi formalism and LaTeX build skills. No repository harness verdict was used as an oracle.

`independent_probes.py` imports only NumPy/SciPy and standard libraries, not candidate or project modules. Nineteen probe groups produced eighteen successful groups and the one explicit theorem counterexample. These groups include identity and receipt checks as well as mathematical tests; their count is not a claim of eighteen independent proofs. The exact commands, timestamps and exit codes are in `raw/commands.json`; numerical evidence is in `raw/probe_results.json`.

The first reviewer probe command failed while serializing a NumPy boolean to JSON after the calculations. Its original source and stderr are retained (`raw/independent_probes_first.py`, `raw/independent_probes.stderr`). The only reviewer-script repair converts NumPy scalars during serialization; numerical logic and tolerances are unchanged. The subsequent command exited 0 and recorded the theorem counterexample explicitly rather than asserting universal success.

The 61 candidate checks were read with their implementation and retained output; the candidate consumer was not rerun. A separate disposable LaTeX fixture contained only the six required source/table/figure files. `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` exited 0 and produced twelve pages. All 35 tagged equations agree between source and TeX after layout normalization. Build logs have no overfull boxes or undefined citations/references; the documented nameref/RevTeX warning remains.

The actual candidate PDF was independently rendered and all twelve pages were inspected at readable size. Both tables, both figures, proofs, captions and references are readable, without clipping or blank pages. `pdfimages -list` finds no raster objects in either figure. Table I spells `lambda` as Latin math text rather than a Greek glyph; this cosmetic point does not block the scientific product.

The narrow bibliographic identity check confirmed author/title/version/journal/DOI at the primary [Heinesen v2](https://arxiv.org/abs/2010.06534v2) and [Maartens et al. v3](https://arxiv.org/abs/2312.09875v3) pages. Their context supports general local cosmography and the need to treat observer transformations explicitly. This was not a new prior-art priority determination or a full historical theorem replay; the candidate's displayed derivations were assessed directly.

## Packaging incident and remaining claim boundaries

The earlier packaging cwd failure and restoration evidence remain sealed. Current root README bytes equal HEAD and the recorded original hash, the restoration diff is empty, and root BUILD_REPORT.md/finalize.py are absent. All candidate scientific files match the exact manifest. No material effect of that incident on this candidate was found. This review does not claim independent observation of the historical pre-mutation state; current restoration and retained evidence are sufficient for this scoped finding assessment.

No physical radius, Hubble value, calibrated covariance, confidence coverage, null law, native transfer, Bianchi family or original42 completion is supplied by this product. Those stronger inputs are not added as prerequisites for the conditional methods note. The only acceptance blocker found here is P6-IR-01. After the bounded repair, the next scientific action is a targeted independent closeout bound to the changed candidate. The next controller action remains receiving the actual formal packet and recording/acknowledging it through the existing controller; this review invents none of those states.
