# P6 optical appendix: frozen author text and consumption instructions

This is the author package for one addition to the existing qualified optical paper. The qualified baseline is `R32-05-P6-OPTICAL/repair_01/report`, candidate `7e35f553fb41c9cba9e90272e9731ad5cf3235314a2fc723c1aee59b0c62bfcc`; the legacy root `report/` is not that baseline. The source result is repaired optical candidate `d796c9df0a8e86e4834d6affb8ac0e4731e65d11cd4f865723b45dab3caafcbc`. Its actual independent return now qualifies `optical_joint_response`; this does not qualify this unimplemented manuscript revision. The complete identities and field locators are in `EDITOR_CONTRACT.json`.

Add one appendix immediately before the existing `\input{references.tex}`. Preserve every original paragraph, all 35 tagged equations, both figures, both generated tables, references, old result, and old qualification receipts. The only changes to an existing scientific document are the two-line appendix invocation in repaired `main.tex` and its rebuilt PDF. The appendix uses the existing RevTeX packages and bibliography. Add a short `README_CURRENT_OPTICAL.md` at the P6 root pointing readers to the repaired current report and its new consumer. Do not edit the three previously revised papers or P4.

The marked block is the public English manuscript source. Convert its Markdown headings and mathematical environments literally to RevTeX; expand the three table/figure directives from the exact source locators. Labels may be added for cross-references. No scientific rewrites or substituted numerical results are delegated.

**Manuscript text**

## Joint optical residuals with a separate direct-dipole constraint

### The seven-component response and its physical domain

The finite inverse can retain the complete signed octupole when testing a common local optical response. We use the same outward direction, signature \((-+++)\), and orthonormal observer rest frame as in the main text. With \(H>0\), \(d=-A/(cH)\), \(S=\sigma/H\), and \(\kappa=5/\ln 10\), the local field is \(-\kappa\ln[1+d\cdot n+S:nn]\). The quantities \(H\) and \(\sigma\) have inverse-time units; \(d,S\) are dimensionless. A physical application assumes one smooth emitter congruence and a regular local distance expansion. Let \(\sup_n|d\cdot n+S:nn|\leq\epsilon<1\) throughout the proposed parameter region. This is a condition on the region, not merely on its central estimate.

In Frobenius-orthonormal rank-three symmetric trace-free coordinates, the magnitude octupole has seven signed components. The retained local expansion gives [QOMethods]

\[
 O=\kappa L_Sd+R_3,\qquad
 L_Sd=\operatorname{STF}(d\otimes S),\qquad
 \|R_3\|_F\leq E_3(\epsilon)
 =\sqrt{\frac{35}{2}}\frac{|\kappa|\epsilon^3}{3(1-\epsilon)}.
\]

The response has the Gram matrix

\[
 M_S=L_S^TL_S=\frac{S:S}{3}I+\frac25 S^2.
\]

For nonzero \(S\), this three-dimensional matrix is positive definite, while the seven-dimensional octupole still has four directions perpendicular to the response image. The measured apparent CF4 tensor retained in the main text has Frobenius norm \(0.03265680189321492\). Inserting that same dimensionless tensor gives minimum and maximum singular values of \(L_S\) equal to \(0.018873110043440326\) and \(0.024097307981999622\). These quantify the conditional linear inverse. The tensor is already dimensionless and is not divided by \(\kappa\) again; its physical interpretation as \(\sigma/H\) still requires the stated response qualification.

Suppose \(\|S-\widehat S\|_F\leq e_S\) and \(\|d\|\leq D_{\max}\) hold on the same deterministic region or joint event. The STF identity implies \(\|L_{S-\widehat S}\|_{\rm op}\leq\sqrt{3/5}\,e_S\). A single outer radius for the seven-component optical residual is therefore

\[
 B=E_3(\epsilon)+e_O+B_z+B_{\rm sel}
       +|\kappa|\sqrt{3/5}\,e_SD_{\max}.
\]

Here \(e_O\) bounds the remaining observational octupole error, \(B_z\) the finite-distance contribution, and \(B_{\rm sel}\) the effect of selection, calibration and the specified fitting operator. Each contribution is included once according to its definition. The angular logarithmic remainder does not supply the finite-distance or selection bounds. A sufficient uniform domain condition is \(D_{\max}+\|\widehat S\|_{\rm op}+e_S\leq\epsilon<1\). More restrictive joint regions can also establish the required bound. A nonzero uncertain-shear term requires a finite bound on \(\|d\|\); omitting that bound cannot silently set the term to zero.

A separately supplied direct-dipole region constrains the argument of the optical map. For a spherical direct region and an optional physical amplitude bound, write

\[
 \mathcal D=\{d:\|d-d_{\rm obs}\|\leq r_d\}
             \cap\{d:\|d\|\leq D_{\max}\},\qquad
 r_*=\min_{d\in\mathcal D}\|\widehat O-\kappa L_{\widehat S}d\|_F.
\]

The second ball may be omitted in the purely mathematical fixed-response problem. Physical use still requires the uniform angular domain and any amplitude bound used to construct \(B\). Compatibility with the outer residual model means \(\mathcal D\ne\varnothing\) and \(r_*\leq B\). The direct-dipole radius \(r_d\) is profiled through \(\mathcal D\); it is not an additional octupole-error term in \(B\). A supplied correlated error body may be more restrictive than these separate outer bounds.

For \(\widehat S\ne0\), set \(\widehat d=\kappa^{-1}M_{\widehat S}^{-1}L_{\widehat S}^T\widehat O\) and \(\widehat O_\perp=\widehat O-\kappa L_{\widehat S}\widehat d\). At every admissible \(d\),

\[
 \|\widehat O-\kappa L_{\widehat S}d\|_F^2
 =\|\widehat O_\perp\|_F^2
 +\kappa^2(\widehat d-d)^TM_{\widehat S}(\widehat d-d).
\]

Both terms spend the same squared residual budget. Two orthogonal contributions of \(0.8B\) each give \(\sqrt{1.28}B>B\), although each passes its separate threshold. The saved unit-budget example has certified residual endpoints \(1.1313708498984756\) and \(1.1313708498984758\) and is incompatible. At \(S=0\), the response is zero and the appropriate test is directly \(\|\widehat O\|_F\leq B\), together with nonemptiness of \(\mathcal D\). No inverse is used. At \(B=0\), retain exact membership instead of a normalized score. Arbitrarily small nonzero \(S\) remains a distinct inverse problem; an absolute numerical threshold cannot replace it by \(S=0\).

[Include sealed JOINT_RESPONSE.pdf. Caption: A shared optical residual budget and a finite selected-source response. Left: the two orthogonal residual components each have size 0.8 of one declared unit budget; their combined norm exceeds that budget. Right: the saved 10-by-8 local Jacobian maps three dimensionless dipole and five dimensionless shear coordinates to three fitted direct-dipole coordinates and seven magnitude-octupole coordinates. Both panels are deterministic mathematical controls. The sampled response is not identified with a physical catalogue dipole.]

### Sampling, covariance and finite distance

Before assigning a physical meaning to fitted harmonics, retain the map from source magnitudes. Let \(T_a^{(2)}\) and \(T_b^{(3)}\) be Frobenius-orthonormal STF bases. For directions \(n_i\) and positive weights \(w_i\), use the full-rank 16-column design

\[
 X_i=(1,n_i^T,T_a^{(2)}:n_in_i,T_b^{(3)}:n_in_in_i),\qquad
 K=J(X^TWX)^{-1}X^TW,\quad W=\operatorname{diag}(w_i).
\]

The selector \(J\) multiplies the three fitted magnitude-dipole coordinates by \(-1/\kappa\) and retains all seven fitted octupole coordinates. Thus \(Ky\) is a ten-coordinate fitted summary; its first three entries need not equal the physical \(d\). For the local source model \(y_i=-\kappa\ln(1+q_i)\), \(q_i=d\cdot n_i+S:n_in_i\), its derivative is

\[
 \frac{\partial(Ky)}{\partial(d,S)}
 =K\operatorname{diag}\!\left(\frac{-\kappa}{1+q_i}\right)
       [\,n_i^T,\ T_a^{(2)}:n_in_i\,].
\]

The fixed illustration uses 96 deterministic directions, weights \(1+0.4n_z\), and an input vector \((0.012,-0.009,0.006)\), with the retained apparent tensor inserted as a mathematical coefficient. The rank of its sampled design is 16. The direction index is \(i=0,\ldots,95\), with \(z_i=1-2(i+1/2)/96\), \(\phi_i=i\pi(3-\sqrt5)\), and \(n_i=(\sqrt{1-z_i^2}\cos\phi_i,\sqrt{1-z_i^2}\sin\phi_i,z_i)\). These directions and coefficients are an illustration, not a CF4 data selection or a measured acceleration.

The signed coordinate convention in this illustration is fixed by lexicographic Cartesian unit monomials, STF projection, and successive Frobenius orthogonalization with positive normalization. The full rank-two and rank-three basis arrays accompany the numerical supplement. This rank-two coordinate ordering differs from the five-coordinate display in the main text; the common object is the Cartesian tensor \(S\), not an untransformed coordinate list.

[Generate OPTICAL-SIGNED table: all ten entries of synthetic_source_design/full_signed_summary, first three labelled fitted d_x,d_y,d_z in dimensionless units and remaining seven labelled O_1 through O_7 in mag. Retain signs and display at least 12 significant digits; full precision remains in the numerical supplement. Caption: Complete signed response of the declared 96-direction mathematical illustration. The seven octupole entries use the explicit STF basis in the numerical supplement; neither the fitted direct vector nor this octupole is a measured CF4 physical quantity.]

For a supplied full source covariance \(C_y\), the fitted covariance is \(C_{10}=KC_yK^T\). At fixed \(\widehat S\), its contribution to the residual covariance is

\[
 C_r=A C_{10} A^T,\qquad
 A=[-\kappa L_{\widehat S}\quad I_7].
\]

The off-diagonal direct-dipole--octupole blocks contribute to this expression. The illustration stipulates \(C_y=10^{-8}(I+0.2uu^T)\,{\rm mag}^2\), where the 96 components of \(u\) are equally spaced from \(-1\) to \(1\). Its direct-dipole--octupole cross-block Frobenius norm is \(1.7820478375045505\times10^{-12}\) in dimensionless-dipole times magnitude units, and \(\operatorname{tr}C_r=1.317508814238013\times10^{-8}\,{\rm mag}^2\). The complete 10-by-10 covariance, 7-by-7 residual covariance and 10-by-8 response derivative are retained, with their coordinate order and units. This is a source-covariance illustration at fixed \(S\), not a supplied empirical CF4 covariance, not an uncertain-\(S\) covariance calculation, and not a confidence region. A confidence threshold would additionally require a sampling law and its calibration. No unknown empirical cross-block is filled with zero.

Finite distance requires a separate contribution even when the angular expansion is controlled. If

\[
 d_L=\frac{cz}{H(1+q)}[1+z a_1(n)+O(z^2)],
\]

then the magnitude correction is \(\kappa z a_1(n)+O(z^2)\), generally first order in redshift. The saved source-level control uses \(a_1(n)=T_1^{(3)}:nnn\) and passes \(\kappa\ln[1+za_1(n)]\) through the same fitted octupole operator. At \(z=(0.02,0.01,0.005)\), its octupole norms are \((0.04342971604250298,0.021714693414132947,0.010857342173346137)\) mag. The successive ratios \(2.0000151608973153\) and \(2.0000008351436778\) illustrate the leading linear order. These values do not determine a physical \(B_z\) for a survey; that bound needs a controlled finite-distance coefficient and the actual estimator and depth weights.

[Include sealed SOURCE_AND_FINITE_Z.pdf. Caption: Declared source covariance and a finite-redshift response control. Left: all entries of the synthetic ten-coordinate covariance, ordered as three fitted dimensionless direct-dipole coordinates followed by seven magnitude-octupole coordinates. Entry units follow the corresponding pair of coordinates; the white lines mark the shared-source cross-blocks. The full numerical matrix accompanies the text. Right: the same selected octupole operator applied to a declared relative-distance perturbation, compared with a linear-redshift reference. Neither panel supplies an empirical CF4 joint law or a physical finite-distance error radius.]

Observer motion also changes the target. The same-congruence coefficient \(d=-A/(cH)\) is not interchangeable with a peculiar-velocity dipole. For the dust moving-observer construction, the first-order relation is \(d_{\rm boost}=-2(I+S)\beta+O(\|\beta\|^2)\), with \(\beta=v/c\); its inverse requires invertibility of \(I+S\) and control of the omitted order. At a fixed ray, the Doppler factor \(\Gamma>0\) gives \(1+\widetilde z=(1+z)/\Gamma\), \(\widetilde d_L=d_L/\Gamma\), and a shifted vertex \(\widetilde z_o=\Gamma^{-1}-1\). The corrected distance \(d_L^*=d_L/(1+z)^2\) obeys \(\widetilde d_L^*=\Gamma d_L^*\), so the vertex derivative transforms as \(d\widetilde z/d\widetilde d_L^*=\Gamma^{-2}dz/dd_L^*\) [Maartens2024]. The uncorrected-distance artefact \(2\operatorname{STF}(\beta\otimes S)\) is distinct from the nonlinear magnitude octupole \(\kappa L_Sd\). Neither relation turns a raw catalogue harmonic into a measured acceleration or observer velocity.

### Closed sets and numerical certificates

The numerical compatibility calculation keeps the two original dipole balls closed. Finite binary64 coordinates and radii are treated as exact rational inputs for squared-ball membership and emptiness. Zero-radius balls and external tangency are handled before optimization. A rounded tangent point is accepted only if it satisfies both original predicates. Failure to represent or verify a feasible witness returns numerical uncertainty, not physical exclusion or an enlarged radius.

An optimizer supplies a candidate, not a compatibility certificate. A verified feasible candidate supplies a primal residual bound. A lower bound follows from the seven-component support inequality: for \(\|u\|\leq1\),

\[
 r_*\geq u^T\widehat O-h_{\mathcal D}(K_S^Tu),\qquad K_S=\kappa L_{\widehat S},
\]

where the support function obeys

\[
 h_{\mathcal D}(v)\leq
 \min\{v^Td_{\rm obs}+r_d\|v\|,D_{\max}\|v\|\}.
\]

If the amplitude ball is omitted, only the first expression is used. This support bound need not be sharp. The implementation uses candidate residual and observation directions and incorporates its declared response-roundoff envelopes. It exports a lower endpoint rounded downward and an upper endpoint rounded upward. The positive-budget score is the upward-rounded quotient of the exported upper endpoint and \(B\); it is an upper bound, not a claim to have computed the exact minimizing score.

For a general nondegenerate case, the implemented decisions compare the upper endpoint before display rounding with \(B+\delta_{\rm loc}\), or the lower endpoint with \(B+\delta_{\rm glob}\). With binary64 machine epsilon \(\varepsilon_{\rm mach}\), the cancellation allowance is \(\delta_{\rm loc}=64\varepsilon_{\rm mach}\max(\|\widehat O\|,\|K_Sd_w\|)\) only when both terms are nonzero and the witness residual is at most half the larger norm; otherwise it is zero. The conservative rejection allowance is \(\delta_{\rm glob}=64\varepsilon_{\rm mach}\max(\|\widehat O\|,\|K_S\|_F D_{\rm cap})\), where \(D_{\rm cap}\) is the upward-enclosed triangle cap \(\|d_{\rm obs}\|+r_d\), restricted by \(D_{\max}\) when supplied. These are numerical response allowances, separate from the physical radii. A positive cancellation allowance is explicitly recorded, and an accepted case must not be advertised as a strict zero-allowance residual certificate unless its exported upper bound also lies below \(B\). A straddling interval remains numerical uncertainty.

For a singleton set or zero response, the finite-response residual square is compared with \(B^2\) using exact rational arithmetic, including equality. A nonzero-response exclusion too close to the declared global response allowance is still returned as numerical uncertainty. Underflow of a displayed square does not set a nonzero residual to zero. The complete certificates retain the witness, endpoint bounds, response envelope, cancellation allowance and display status.

[Generate OPTICAL-CERTIFICATES table from the contracted case locators. Use descriptive mathematical case names, not internal finding codes. Columns: case, lower endpoint, upper endpoint, B, result. Include the shared-unit-budget example, zero-response zero-budget case, narrow feasible ball, excluded physical boundary, exactly tangent singleton, one-spacing interior overlap with nonzero response, zero-response norm sqrt(3), exact empty direct singleton, and adjacent exterior empty set. Empty cases have no residual endpoints; display a dash, not zero. Caption: Saved finite-response controls. Endpoints bound the profiled residual or the exact fixed objective under the stated numerical response conventions; they are not uncertainty intervals for physical cosmological parameters. Empty-set decisions precede residual comparison. All radii are stipulated. Full witnesses and all diagnostic fields accompany the numerical supplement.]

The near-tangent examples make the closed-set convention concrete. Set both radii to \(1/8\). A center \((1/4,0,0)\) has the representable unique intersection \((1/8,0,0)\). For the adjacent binary64 center below \(1/4\), a feasible saved witness is \((0.12499999999999999,0,0)\); with \(S=\operatorname{diag}(0.001,-0.001,0)\), zero observed octupole and \(B=0.001\), its exported upper residual bound is \(0.00028033588262685186<B\). The adjacent center above \(1/4\) gives an exactly empty intersection. A direct singleton at \((1/8,10^{-60},0)\) lies outside the physical ball of radius \(1/8\): the second component gives a strictly positive exact squared excess, even when a rounded norm hides it. The decimal \(10^{-60}\) here denotes its supplied binary64 value, whose square is near \(10^{-120}\), not exactly that decimal rational. Zero and nonzero shear controls also preserve a residual of \(10^{-200}\) against a zero budget. These examples test witness availability and range handling; they do not prove that every feasible real intersection has a representable witness or that every numerical optimization is decisive.

The physical output remains a conditional response-compatible set. The apparent tensor, source-covariance illustration and numerical controls do not supply an empirical joint direct-dipole--octupole law, the missing finite-distance and selection bounds, or a common physical source/observer transfer. Vorticity, curvature, energy, absolute expansion and history remain unresolved as described in the main text. Full signed coordinates and shared dependence must be retained before any later scalar summary or physical attribution.

**End manuscript text**

## Exact source table and limited implementation

| Item | Source and locator | Use |
|---|---|---|
| Current optical qualification | `04_formal_return`: exact candidate, input identity, packet, acceptance and named product | Necessary source eligibility, not manuscript approval |
| Existing paper qualification | `p6_publication` and `p6_formal_return`; repaired result canonical manifest identity | Select repaired P6 baseline, preserve failed predecessor |
| Physics and domains | `hubble_protocol`, H1–H11; `04_interpretation`; reviewed `04_module` functions | Equations above and their conditional scope |
| Signed pattern and all matrices | `04_result:/synthetic_source_design` | Full 10-vector, 10-by-8 Jacobian, 10-by-10 joint covariance, 7-by-7 residual covariance; copy full precision |
| Fixed STF bases | `04_module:B2,B3`, functions `stf_basis`, `stf2`, `stf3` | Read-only import may export these deterministic basis arrays; do not rerun fits or profiles |
| Finite-redshift values | `04_result:/finite_z_example` | Three cached norms and both ratios, mathematical control only |
| Numerical certificates | Individual case pointers in `number_table` and `certificate_cases` | Copy complete objects, including nonfinite-range display statuses, empty-set branches and allowances |
| Two figures | `04_joint_figure`, `04_source_figure` | Copy sealed PDFs byte-for-byte; no plot regeneration |
| Old results | Repaired P6 `generated/`, `figures/`, `RESULT.json`, sources and old scripts | Immutable; copy only bounded TeX support into candidate |
| Existing implementation pattern | `overlay_reference` | Reuse the baseline/postimage resolver, bounded apply preflight and current consumer mechanics; do not import its CLI or modify its three-paper contract |

The worker implements one small `publication_overlay.py` under the new repaired P6 `report/r36_optical/` directory. It consumes the JSON and this text, emits the appendix, two generated tables, full numerical supplement, and one number/figure map, copies the two figures, and assembles the repaired report from preserved baseline bytes. One overlay manifest lists changed files and pre/postimages. This is document assembly; original scientific producers, the 19 optical tests, old 61 P6 checks, raw downloads, numerical fitting, optimization, Monte Carlo and physical evolution are not rerun. Minimal falsifiers concern dropped signed components/cross-blocks, false qualification and stale pre/postimage resolution, using small in-memory or external disposable copies.

Source resolution after application must accept either the exact old live file or a verified old baseline copy while also verifying that the corresponding live file is the reviewed new postimage. PDFs may use both initial byte identity and separately retained extracted-text identity for a legitimate rebuild. A baseline copy alone must not excuse unexpected live edits. Old manifests and validators keep their original meanings; run the new current consumer on the revised paper. Preserve the old scripts, and state clearly that the old `build_source.py` recreates the historical paper, not this addition.

The old repaired manifest also seals its build auxiliaries and raw logs. Build into the new `r36_optical/build` directory and copy only the resulting PDF to `report/main.pdf`; do not refresh the historical report-level `.aux`, `.log`, `.bbl`, `.blg`, `.fls`, `.fdb_latexmk`, `.out` or `mainNotes.bib`. The new consumer reads diagnostics from the new build directory. Those temporary build outputs are not installed as a new scientific result pack.

Only the author package exists now. The following is the required interface for the lower-tier implementation, not a claim that these commands have run. `assemble`, `check`, and `seal` take `--contract`, `--repo`, and `--output-root`; `check` additionally takes `--built-pdfs` and `--falsifiers`; `apply` takes `--manifest`, `--repo`, `--reviewed-manifest-sha256`, and `--review-return`. The last argument must be an actual independent manuscript-review return bound to the sealed overlay; the optical scientific qualification alone cannot authorize application.

```bash
repo=/home/cosmosapjw/Dropbox/bianchi/htt_base
framing=/mnt/extdrive/workdir/htt_open_data/r36_optical_manuscript_framing
author=/mnt/extdrive/workdir/htt_open_data/r36_optical_manuscript_author
candidate="$author/candidate"
relative=docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-05-P6-OPTICAL
helper="$author/publication_overlay.py"
python3 "$helper" assemble --contract "$framing/EDITOR_CONTRACT.json" --repo "$repo" --output-root "$candidate"
python3 "$helper" check --contract "$framing/EDITOR_CONTRACT.json" --repo "$repo" --output-root "$candidate" --falsifiers
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd -outdir=r36_optical/build "$candidate/$relative/repair_01/report/main.tex"
cp "$candidate/$relative/repair_01/report/r36_optical/build/main.pdf" "$candidate/$relative/repair_01/report/main.pdf"
python3 "$helper" check --contract "$framing/EDITOR_CONTRACT.json" --repo "$repo" --output-root "$candidate" --built-pdfs
python3 "$helper" seal --contract "$framing/EDITOR_CONTRACT.json" --repo "$repo" --output-root "$candidate"
```

After an actual fresh independent Astra manuscript decision, the controller supplies the actual return path and exact reviewed overlay SHA. No placeholder value may be accepted as evidence. The existing campaign and task accounting continue.

```bash
python3 "$helper" apply --manifest "$candidate/OVERLAY_MANIFEST.json" --repo "$repo" --reviewed-manifest-sha256 "$reviewed_overlay_sha256" --review-return "$actual_manuscript_review_return"
current="$repo/$relative/repair_01/report/r36_optical"
python3 "$current/publication_overlay.py" assemble --contract "$current/EDITOR_CONTRACT.json" --repo "$repo" --output-root "$repo"
python3 "$current/publication_overlay.py" check --contract "$current/EDITOR_CONTRACT.json" --repo "$repo" --output-root "$repo" --falsifiers
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd -outdir=r36_optical/build "$repo/$relative/repair_01/report/main.tex"
cp "$repo/$relative/repair_01/report/r36_optical/build/main.pdf" "$repo/$relative/repair_01/report/main.pdf"
python3 "$current/publication_overlay.py" check --contract "$current/EDITOR_CONTRACT.json" --repo "$repo" --output-root "$repo" --built-pdfs
python3 "$helper" apply --manifest "$candidate/OVERLAY_MANIFEST.json" --repo "$repo" --reviewed-manifest-sha256 "$reviewed_overlay_sha256" --review-return "$actual_manuscript_review_return"
```

The final apply must report zero changed targets. Compare all retained scientific bytes and the untouched P4/H03/P5/bandpass/supplement outputs against the contract, and inspect the new appendix pages for clipping and complete signs/indices. Record build diagnostics and actual outcomes; retain first failures. Source qualification, this manuscript's independent review, application, Git publication and original scientific acceptance remain separate facts. No original acceptance changes follow from this addition.
