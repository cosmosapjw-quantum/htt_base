# Independent review of the moving-lens supplement

Decision: **SCOPED PASS** for the exact five-page external-reader supplement and source package identified below. There are no blocking findings. This decision approves publication of this package within the owner's existing authority; it does not submit, publish, admit a physical likelihood, or change any campaign acceptance.

Date: 2026-10-25. Requested reviewer identity: `gpt-6-astra/xhigh`; observed model: `UNKNOWN`; observed effort: `NOT_INDEPENDENTLY_OBSERVED`. The reviewer did not author the candidate, modify the source or repository, read previous review verdict files, or spawn another agent. The source document and primary evidence were assessed independently. The old-review identities quoted inside the candidate README and frozen source were treated as historical metadata, not approval evidence. Writes are confined to this review directory.

## Exact candidate and source identities

| Artifact | SHA256 |
|---|---|
| `r30_moving_lens_revtex_supplement/main.tex` | `6d9f3af8eb468d9c76e2e6b13fb79b002b49f9f2d8e1c48f56237b090b3af7f4` |
| `r30_moving_lens_revtex_supplement/main.pdf` | `8e50c04ca93e9f635006a4d3cd79b9a12c1e5f09ff9412a47a3bc79e65fa6376` |
| `r30_moving_lens_revtex_supplement/source_bundle.zip` | `1d48f56bfd64d5fa62e4034741739e9551d2add9401bafdb797e24abd1b4381f` |
| `r30_moving_lens_revtex_supplement/README_BUILD.md` | `c357a0b9f8ebbebad73e7b1732830437e42a70a8a38b8b52ea4b1485bc609971` |
| `r29_nonradial_moving_lens_intake/REPORT_REVISED.md` | `0f66033f7f4adc86c214c45ca479e557de1ede447c1b48afedae2752d505ce2d` |

Paths in this table are relative to `/mnt/extdrive/workdir/htt_open_data/`. All identities were checked against actual bytes. Initial repository context was the existing primary checkout, branch `research/htt-adaptive-methods-20261023`, HEAD `d93605e66adfececa89b90681124b232a5f90220`, origin `https://github.com/cosmosapjw-quantum/htt_base.git`, with existing tracked and untracked work preserved.

## Findings and limitations

No blocking scientific, source-fidelity, bibliography, or rendering finding.

Two nonblocking clarity observations do not require another review cycle:

- `main.tex:159`: the reciprocal scaling is an invariance of predicted bandpowers when the two multiplicative factors are allowed to vary jointly. The phrase “if either is unconstrained” should not be read as a symmetry of a joint likelihood containing an exact external calibration of the other factor. Fixing one nonzero factor would prevent the reciprocal transformation within that restricted parameter class. The conclusion at lines 169 and 173 is expressly restricted to unspecified calibration/nuisance classes and requires calibration uncertainty, so this does not invalidate the scoped conclusion. A future editorial revision could say “when both factors may vary without a constraint fixing their relative normalization.”
- `main.tex:177`: the tuple `(x,F,Pi,Q,G_F)` is not defined in this standalone supplement. It is used solely to decline evaluation, not to report a number, probability, bound, or significance. An external reader would benefit from descriptive names or a definition reference in a future editorial revision. No values or semantics may be inferred from this notation alone.

The retained `nameref` warning is a package interaction, not an undefined reference or duplicate equation label. No mandatory repair is requested.

## Independent mathematical and physical checks

| Candidate location | Check and conclusion |
|---|---|
| `main.tex:18-40` | Comoving length coordinates and time-valued conformal time imply `dX/deta = v_pec`; `beta=v/c`, `phi=Phi_W/c^2`, and `dchi partial_perp phi` are dimensionally consistent. Chain-rule translation gives the stated negative sign. The declared unreduced-deflection convention fixes the sign of `Theta=-alpha dot beta`. Reversal and zero-field limits are correct. Intrinsic evolution is separated. |
| `main.tex:44-77` | Poisson and continuity give `laplacian(phi'_v)=-kappa div[(1+delta)v]` under the stated fixed snapshot/background split. For the two-mode example, `div(v)=0`, `curl(v)=-Vq cos(qy)e_z`, and `v dot grad(delta)=epsilon V k^3 sin(kx)sin(qy)/kappa`. Inverting the Laplacian multiplies by `-1/(k^2+q^2)`, giving the positive displayed potential derivative. The coefficient ratio is exactly `k^2/(k^2+q^2)` and equals one half at `q=k`. Both derivatives have units `1/time`. Density positivity, weak field, slow motion, zero mode and periodic inverse are stated. This is an instantaneous scalar counterexample, not an Euler/Einstein solution or global cosmological no-go. |
| `main.tex:81-103` | Both real E/B tangent families are retained; the mode count follows `sum_(ell=1)^L(2ell+1)=L(L+2)`. Radial multiplicity and both tangent families give `2 N_r L(L+2)`. The advection Jacobian is correctly labelled formal outside a qualified bulk subspace. The extra potential variation has the correct factor and sign. Missing dynamics, light-cone mapping, boundaries, vector/tensor terms and acceleration/history closure are explicit. |
| `main.tex:107-120` | Product-rule curl, weighted-projection distinction, fixed-template temperature linearity and the `(delta L)T` term are correct. A derivative kernel is restricted to a local statement; no actual-survey response rank or solenoidal null is claimed. |
| `main.tex:124-149` | On symmetric positive-definite `C` and nonzero `t`, `h>0`. Independently differentiating `n=t^T A d`, `h=t^T A t`, and `b=n/h` gives `db=(dn-b dh)/h`. With `dA=-A(dC)A`, this reproduces every data, template and covariance term in Eq. (17), including the factor `2b` in the template term. Inverse covariance `A` is explicitly distinguished from four-acceleration. Source Eq. (23) has precisely the product differentiated in Eq. (18); variable weights/support require extra terms. Covariance and fitted weights are not treated as independent evidence. |
| `main.tex:151-169` | Conditional cross-mean cancellation follows only for the declared fixed response and independent mean-zero perturbation. It is not promoted to map or likelihood blindness. The lensing-gradient ambiguity preserves the specified patch signal under simultaneous shifts. The spherical internal-rotation snapshot has zero scalar density/potential time derivative and curl `2 Omega`; no full dynamical solution or rigid-halo no-go is asserted. |
| `main.tex:173-177` | Physical bands, calibrated response, joint covariance, selection/null laws and signed modes remain missing. Full tensor diagnostics are expressly not evaluated. The text supplies no finite physical vorticity/tilt/acceleration bound, calibration, posterior, native family identification, new measurement, or original K03 acceptance. |

These checks are analytic/manual. No numerical science, CAS certificate, solver, or new data experiment was performed or claimed. The minimal publishable result is a conditional operator-domain analysis, a local Poisson--continuity counterexample, and an estimator differential.

## Primary-source and bibliography check

The cached ACT--DESI paper `moving_lens_20261018/2605.18938v1.html` was inspected directly, including title/authors and Eqs. (4), (13), (17), (21)--(25), (38), and (42). It supports the potential-only reconstruction, squeezed hierarchy, empirical covariance formula, template amplitude, surrogate normalization, and deferred galaxy--potential calibration descriptions. Its metadata agree with Ref. [1]. The frozen revised intake was compared with every substantive section of the supplement; scope restrictions and the revised response and estimator formulas are preserved.

The author names and the stated domains were checked against [Hotinli, Johnson and Meyers, arXiv:2006.03060v3](https://arxiv.org/html/2006.03060v3), especially Sec. II and the discussion of lensing contamination, and [Wayland, Alonso and Coulton, arXiv:2609.04133v1](https://arxiv.org/html/2609.04133v1), especially Sec. 2.1. Both primary pages resolve. Their cited restrictions support the supplement's coherent-translation domain. The [DESI LRG source paper](https://arxiv.org/html/2309.06443v2#S7) resolves and its Sec. 7 is the data-products section.

Cached author, ACT and DESI release pages were inspected. Only the three `git_trees` objects in `r29_moving_lens_source_independent_review/SOURCE_AUDIT.json` were used for frozen repository metadata: exact revisions, complete trees, and relevant entries. No review verdict text was read. These records support the dated, bounded endpoint observation, not a new exhaustive absence finding. The three exact GitHub revision URLs are preserved in the PDF. No unverified journal metadata were added. Nine bibliography keys cover all citations, and ten external PDF hyperlink annotations contain the intended primary URLs, including the correct `#S7` fragment.

## Source package, build and rendering

The ZIP contains exactly `main.tex` and `README_BUILD.md`; its CRC check passes and both members equal the external candidate bytes. It has no missing TeX includes, image files, or external bibliography dependency. The inline bibliography is complete. REVTeX generates its own auxiliary notes files during a clean build.

The source ZIP was extracted only under this review directory and independently built with `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`: exit 0, five pages. The original PDF and rebuilt PDF were separately extracted with `pdftotext -layout`; their text is identical, and the original extraction also matches the author's retained extraction. All five original-PDF pages were freshly rendered with `pdftoppm` and visually inspected. Title/abstract, equations, paragraph flow, page breaks, and bibliography are legible, with no visible clipping, overlap, missing symbols or incomplete content. The dedicated bibliography page is sparse but valid.

No undefined citations/references, missing files, multiply defined labels, overfull or underfull boxes were found in the independent build log. The one warning is `Package nameref Warning: The definition of \\label has changed!`. There are no manuscript figures requiring separate source provenance. A prose scan and reading found no task IDs, agent roles, hash accounting or development workflow terms in the paper. Provenance details remain in the README. See `PACKAGE_CHECKS.json`, build/extraction logs, rendered pages, and the independent build directory for evidence.

## Publication scope and mechanically inherited provenance

This exact five-page package is approved for publication within the existing owner-authorized workflow. The approval is scoped to this reviewed conditional methods supplement. It is not permission for journal submission and makes no broader scientific admission. Physical-response and original K03 acceptance remain HOLD; tensor evaluation remains NOT_EVALUABLE.

The controller may copy the exact candidate and frozen revised source as provenance without a new scientific review. Preserve their byte identities, relative association, original dates and claim ceilings; include this review and the build evidence or resolvable links. A provenance-only wrapper may record the new publication path and this decision while preserving the historical README's pending-review statement as historical metadata. Do not silently alter the frozen ZIP to replace that history. If a wrapper or ZIP is repackaged, record its new packaging identity and verify the unchanged scientific member bytes; a packaging hash change alone is not a scientific failure. Publishing other historical source/review files mechanically does not grant their unrelated contents fresh scientific approval.

For routine trusted-remote publication, record provider success and the exact remote ref/commit identity under the project's R1 policy. No push, merge, source mutation or submission occurred in this review. No further review ladder is needed unless scientific content changes or a concrete defect is found.

Repository physics, claim, tensor-formalism, manuscript and build skills were audit guidance only, not scientific or approval oracles. No permanent claim registry, acceptance counter, controller state, frozen assignment, or historical cost was changed.
