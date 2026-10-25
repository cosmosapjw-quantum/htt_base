# Frozen scientific build contract: R32-05-P6-OPTICAL

## Assignment and ownership

The scientific source is the complete `MANUSCRIPT.md` in this directory. It contains 35 tagged equations and proofs of the full-field error bound, finite inverse/support result, and physical-radius bounds. Implement it literally in a readable English RevTeX note. The scientific author has completed writing and will release the sole production writer to the lower-tier builder through the host. The builder owns only this product's `report/` directory. Do not edit `science/`, other products, controller state, historical evidence, Git, runtime settings or budgets. You are not alone in the checkout; preserve all unrelated work.

Task ID: `R32-05-P6-OPTICAL`; execute packet: `4061878216a65321d922f6c919d44fd3406ce3e8bfefe7d7e02a1329d703ceec`; input identity: `sha256:f900ec93d972751795cdd825ee0f362eabed3a2aae60b59e4c24d265ee6ec132`. Retain the existing campaign and attempt. This build produces a candidate, not independent scientific acceptance or an original42 promotion. Root records the completed execute candidate before requesting its independent review.

## Sources and conventions

Let `P=docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025`. Consume only small retained files:

1. `P/EVIDENCE_MANIFEST.json`, expected SHA-256 `10703b1d37198379ee8ec4565dbef737e7ee35e6143de404c4d94ed48658f2d3`.
2. `P/evidence/research/latest_results.json`, specifically `units_correction` and `cf4_calibration_quotient`. Validate its existing manifest entry. It supplies the full five-vector, full precision 3x3 tensor, spectrum, norm, working 5x5 shape matrix, target singular values, rank and selected-row counts.
3. `P/evidence/RESULT_OBSERVABLE_MAP.json` for the independent declared dimensional convention and scalar cross-reference. Validate its manifest entry when present; record its actual SHA regardless.
4. `P/evidence/research/physical_derivations.md`, specifically P3 and P7–P8, and `P/evidence/research/latest_physical_results.md`, the source-bound unit correction, for claim-to-source bindings. Validate the existing manifest entries.
5. `P/products/R32-01-QO-METHODS/science/MANUSCRIPT.md` equations (20)–(24), (36), (38)–(39), and its existing report RESULT/independent assessment if needed for reused theory provenance. Record actual hashes, without replaying the companion's geometry, quadrature, CAS or review.
6. The three `science/` author files for manuscript/contract/provenance inputs; record their exact hashes.

Use no raw catalogue, sky map, ODE, native solver, network acquisition or historical full-check replay. The narrow arXiv bibliographic checks have already been performed by the author; complete reference entries are in the manuscript. No new source audit is needed to implement the literal formulas.

The CF4 tensor is already dimensionless. Its STF basis is exactly `diag(1,-1,0)/sqrt(2)`, `diag(1,1,-2)/sqrt(6)`, symmetric xy/xz/yz pairs divided by sqrt(2). Preserve the T1 sign. Norms are full ordered-index Frobenius norms. Do not divide these coefficients, norm or errors by kappa or H. `Q_mu` is the separate magnitude tensor, and `Q_phi` is the scalar policy score. The saved matrix is only an adopted working error-shape matrix for the deterministic illustration; it carries no empirical covariance or confidence claim.

## Required numerical tables

Generate CSV and TeX tables directly from retained full precision inputs and the manuscript formulas:

**Table 1: apparent retained tensor.** Rows for its five coefficient values, three ordered eigenvalues, Frobenius norm, directional RMS `sqrt(2/15)*norm`, numerical rank, and minimum/maximum singular values. A two-part table is acceptable. State J2000 basis, dimensionless coefficient convention and working-metric singular values. Optional source row counts can appear in the table caption or prose. Show about 9–12 significant digits for central values without using rounded manuscript matrix (25) as a computation input.

**Table 2: conditional error frontier.** Radius rows `r_Q = 0, 0.005, 0.01, 0.02, t, 0.04`, using `t` from the actual saved norm. Columns `r_Q`, `(t-r_Q)_+/sqrt(6)`, `(t+r_Q)/sqrt(6)`, and, for the chosen illustrative `r_H/H_*=0.1`, the dimensional-rate endpoints normalized by `H_*`: `0.9*(t-r_Q)_+/sqrt(6)` and `1.1*(t+r_Q)/sqrt(6)`. Explicitly name all radii assumed. The zero-radius row is an exact-response limiting scenario, not a calibrated physical estimate. No physical H value is inserted.

## Figure 1: error-radius frontier

Create a two-panel vector PDF from analytic formulas, with at least 301 grid values `0 <= r_Q/t <= 1.5`, and include the exact crossing `r_Q/t=1` in the grid.

- Left: lower/upper dimensionless `Sigma` from (29), horizontal x coordinate `r_Q/t`. Mark the crossing at one; annotate `t=0.0326568018932` and `r_Q assumed`.
- Right: `||sigma||_F/(sqrt(6)*H_*)` endpoints from (30), for assumed `delta_H=r_H/H_*` equal to 0, 0.1, 0.25. Use one color per delta_H, solid upper and dashed lower, or equivalently clearly shaded bounded bands. Equations are `(1-delta_H)*max(0,t-r_Q)/sqrt(6)` and `(1+delta_H)*(t+r_Q)/sqrt(6)`. The dimensionless Sigma left panel does not vary with H uncertainty.

Caption: “Conditional shear bounds from the retained apparent CF4 tensor. The horizontal coordinate is an assumed qualified dimensionless response-error radius divided by the apparent norm. The left panel gives the dimensionless shear-amplitude interval. The right panel converts it to a dimensional shear rate, divided by a symbolic reference Hubble rate, for three assumed relative Hubble intervals. A positive lower bound requires r_Q below the apparent norm. The figure assumes the same-event, same-congruence response in equation (28); neither error radius nor a physical shear detection is estimated here.”

## Figure 2: the retained tensor error image

Use the full retained five-vector and the `working_covariance` matrix only as the shape C in (20)–(21). Set `rho=1`, `G=I_5`, and assumed `eta=0, 0.005, 0.01`. The full set is `bhat+C^(1/2)B_1+B_eta`; plot its projection onto the first two source-basis coordinates b0,b1, not its section at b2=b3=b4=0. Let C2 be the leading 2x2 principal submatrix, c=bhat[:2], and a(phi)=(cos(phi),sin(phi)). The exposed boundary is

`p(phi)=c+C2@a/sqrt(a@C2@a)+eta*a`, for `0 <= phi <= 2*pi`.

The source C2 is positive definite; verify before using this formula. If not, stop with the actual failing eigenvalue rather than selecting another matrix. With at least 721 angles and equal axis aspect, plot these three projected boundaries, the actual apparent center and the origin if readable. A second panel shows the directional centered support `sqrt(a@C2@a)+eta` versus phi. Both are dimensionless. Retain the full five-dimensional shape and tensor in generated JSON; do not replace the scientific carrier with this drawing.

Caption: “A deterministic projection of the tensor error region. The retained working matrix supplies an illustrative ellipsoidal shape, with unit assumed ellipsoid radius and three assumed isotropic response radii. Curves show the projection onto the first two Frobenius-orthonormal source coordinates, and the corresponding centered directional support. The product error-set assumption gives the support exactly. The unit radius has no assigned confidence level, and the additional response radii are sensitivity choices.”

## Required focused implementation checks

Use NumPy and deterministic small matrices; no new scientific solver. Preserve the first actual command failure and its output. General theorems are supported by the manuscript proofs; these checks verify faithful implementation and source conventions.

1. Check source file identities against the manifest entries actually consumed. Do not regenerate retained files. Record requested/observed executor identities separately, unknown observation as UNKNOWN.
2. Decode the five-vector with the exact basis and compare with the saved 3x3 matrix; verify symmetry, trace freedom, basis Gram matrix I5, norm equality, ordered eigenvalues, directional RMS and corrected dimensionless unit metadata. Absolute tolerance `1e-12` for these dimensionless equalities. Check the saved norm matches `0.03265680189321492`, not that number divided by kappa.
3. Validate C is finite, symmetric within `1e-12`, and has strictly positive eigenvalues; use the actual raw eigenvalues in the record. Its positive definiteness is a property of this input, not permission to label it an empirical law.
4. Verify figure/table endpoint formulas, nonnegative lower endpoints, upper >= lower, strict positive lower endpoint for each grid point with r_Q<t, and zero lower endpoint for r_Q>=t. Absolute tolerance `1e-12`; use the mathematical inequality for the positivity test, with the exact crossing stored rather than a rounded reconstructed t. For H uncertainty confirm left endpoints unchanged and right endpoints multiplied by 1±delta_H. Check delta_H<1.
5. Verify the support parametrization of Figure 2: `a@(p-c)=sqrt(a@C2@a)+eta` for all displayed directions to `1e-12`. At each eta, compare an independent projected ellipsoid expression `sqrt((embed(a))@C@embed(a))+eta` to the plotted support, to `1e-12`. This tests projection and preserves off-projection coordinates in the retained full set.
6. Test the finite inverse formula with the **synthetic algebraic fixture** `A=diag(2,1,0)`, `z=(2,-1,0.2)`, error ball radius `0.3`. The residual-compatible error slice has `e3=0.2` and tangential radius `sqrt(0.3^2-0.2^2)`. For J selecting the first two coordinates, its support in direction a is `a dot (1,-1)+sqrt(0.3^2-0.2^2)*sqrt((a1/2)^2+a2^2)`. Generate its extremizing error with `e12=-r*(a1/2,a2)/norm((a1/2,a2))`, e3=0.2, and theta=Aplus@(z-e). Verify residual equation and support at axes plus `(1,1)/sqrt(2)`, absolute tolerance `1e-12`. Verify `A@(theta+(0,0,7))=A@theta` and J kills that kernel. For the second fixture z3=0.4, the radius 0.3 error ball is infeasible by `abs(z3)>0.3`; never report a pseudoinverse point as a feasible solution. This is a meaningful range-compatibility regression check, not an observation.
7. Check equations (7)–(8) analytically in prose as delivered; implementation need only evaluate the finite bound B at illustrative `epsilon=.2`, `delta=0,.001,.01` and verify zero at delta=0, positivity otherwise and monotonicity. Do not run another full-sphere integration to repeat established inverse proofs.

Do not add acceptance thresholds, alter a physical convention, regularize a source eigenvalue or select a new error law to pass. Return any substantive problem to the scientific author/root with its exact first failure.

## Publication layout and outputs

Translate the manuscript faithfully: equations, proofs, conventions, number labels, citations and all set/domain qualifications are scientific content. Use readable RevTeX, title and abstract together, meaningful figure placements and generated table inputs. The manuscript's novelty assessment belongs only in RESEARCH_NOTE.md. Use the relevant repository manuscript/build/claim skills for layout and checking; no style pilot or new repository-wide validation is required.

Deliver under `report/`: `reproduce.py` (or equivalently named runnable retained-input consumer), `main.tex`, `main.pdf`, references, generated CSV/TeX/JSON, two vector figures, raw command/build logs, a concise README and `RESULT.json` with a manifest of source and output hashes. Include a claim-to-source JSON from the table in RESEARCH_NOTE.md. Include the full five-vector, tensor, C, basis definition and finite set parameters in generated output, as well as explicit statuses for all of x/F/Pi/Q/G_F. A manifest is appropriate here because root and the independent reviewer consume its exact candidate identity.

`RESULT.json` records `candidate_only=true`, `acceptance_passed=false`, `original_acceptance_passed=false`, `qualified_products=[]`; use `proposed_qualified_products=["optical_inverse_note"]`. These fields remain false/empty pending the host's fresh independent review. Include source/error-law limitations as specific conditions; no original42 counter change. The scientific author will read the actual result and candidate before writing the bound execute return. The host then records it to obtain the independent review packet. There is no wait for review before the execute result.

Run the narrow consumer once and complete the TeX build/layout checks. Return the literal commands and actual exits, complete candidate path, RESULT SHA-256, relevant generated checks, page/equation counts and any material limitations. Do not claim an execution, review, publication or physical calibration absent its actual receipt.
