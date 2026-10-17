# HTT P2/L01 source identity와 cut-sky spin-2 response, R5 (2026-10-17 KST)

**Authority:** stacked from HTT PR #553 HEAD `ad5dcaffd47192c70575d50795cc518052f87154`; canonical six-paper publication DAG blob `ac4a94c3da13f142eaab3b06b5275b58096c95e1`. This is an enabling result within still-`pending` L01, **not** a physical Planck leakage detection.

## 1. Observed bug, source locks, different identity relations

The originally published `native_planck_pol_response.py` hardcodes SHA-256 for `common` (64 hex), `HM` (64), `OE` (**45**). SHA-256 hex must contain 64 digits. Thus `ValueError: FITS original SHA drift OE` is **not evidence that the local OE FITS data changed**. The immediate proven cause is `EXPECTED_DIGEST_MALFORMED`. Neither a corrupted FITS payload nor any science-level E/B difference has been established. Do not rewrite the original 45-char source provenance as a fabricated 64-char digest; preserve it in the historic code and annotate the new report. Independently restore/re-download and qualify the OE SHA before physical admission.

For any candidate file f, retain independent dimensions:

- `BYTE_IDENTITY`: valid locked 64-character expected SHA vs actual SHA, and exact size; malformed baseline, mismatch and absent file are **different statuses**.
- `STRUCTURAL_IDENTITY`: an actual two-HDU FITS, exactly one `PMASK` float32 column, Nside2048, 50,331,648 pixels, Galactic NESTED, FITS 2880-byte block consistency and the expected original 201,335,040 byte size.
- `SEMANTIC_IDENTITY`: against an independent, qualified reference, decoded Galactic NESTED PMASK values agree for every pixel and the bad-data/unit conventions agree. Metadata DATE/COMMENT/padding differences can change the file SHA without changing PMASK values. Reordering, changed frame, loss of masks or unsupported schema **cannot** be auto-declared equivalent.
- `NUMERICAL_IDENTITY`: separate declared threshold/downgrade, effective pixel support, OLS K and computed observable agree at justified tolerance; not implied by global FITS equality alone when processing differs.
- `SCIENTIFIC_EQUIVALENCE`: source-conditioned physical maps, beam/foreground/noise, end-to-end matched null, prior trial selection and transfer checks; still `NOT_RUN`.

`CHECKSUM` and `DATASUM`, when present, test FITS HDU integrity and do not substitute for SHA-256 provenance or physical equality. Scope of the included bytewise PMASK semantic checker is strict 1E single-column Galactic NESTED, not compressed FITS, Q/U frames or an arbitrary FITS equality algorithm. `--compare-root` does not promote an unverified reference to an original source.

The official IRSA PDR3 OE POL product lists a **single `PMASK` field**; the published header shows `NAXIS1=4`, `NAXIS2=50331648`, `COORDSYS=GALACTIC`, `ORDERING=NESTED`, `NSIDE=2048`, `TTYPE1=PMASK`, `TFORM1=1E`. Thus the narrow format contract is sourced, not guessed. Source: https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/previews/COM_Mask_CMB-OE-Misspix-Mask-Pol_2048_R3.00/ ; header `.../header.txt`. FITS standard: https://fits.gsfc.nasa.gov/fits_standard.html . HEALPix `read_map` ordering convention: https://healpy.readthedocs.io/en/1.17.3/generated/healpy.fitsfunc.read_map.html . Planck 2018 IV: https://doi.org/10.1051/0004-6361/201833881 .

## 2. Exact mask-response sensitivity theorem

Fix a finite real Q/U pixel-coordinate convention. Let `L ∈ R^{2N×p}`, `H ∈ R^{2N×q}` be low/high spin2 designs and `W,W'` diagonal nonnegative masks/weights, with Gram matrices `G=L^TWL` and `G'=L^TW'L` SPD. Define `C=L^TWH` and `K(W)=G^{-1}C`. Write `ΔW=W'-W`.

Then `G'(K(W')-K(W)) = L^T ΔW(H-LK(W))`, hence **exactly**:

`K(W')-K(W)=(L^TW'L)^(-1) L^T ΔW (H-LK(W)).`

This is a finite-dimensional algebraic identity, independent of the probability law of the sky. It implies, using the spectral norm,

`||K(W')-K(W)||_2 <= ||L^TΔW(H-LK(W))||_2 / λ_min(L^TW'L)`.

If `G'` is singular there is no such inverse-form result; an ill-conditioned `G'` may amplify a geometrically small mask mismatch. The changed-pixel **residual**, not merely changed sky fraction, controls the leakage difference. `W` must weight both Q and U consistently, otherwise the stated spin-frame/covariance contract is not the same calculation. The original finite operator is for l=2..5 E/B against l=6..8, **not the full high-l tail**, and the PR #553 derived reference geometry comes from a temperature mask, not the Planck POL PMASK.

**Verification:** Wolfram exact 3×2/1 example returned `ExactIdentity=True`, `K=(1,-1)^T`, `K'=(5/3,-1/3)^T`. Python manufactured 80×7/12 example gave `||ΔK||₂=0.19309864992493064`, certified bound `0.27857612705817725`; exact resolvent difference < `4e-14`. No numerical real-sky claim follows.

A separate processing sensitivity: degrading a binary NSIDE2048 mask to NSIDE64 averages 1024 subpixels per coarse pixel. Threshold `>0.5` admits a pixel with at least **513/1024** valid children; it is not the conservative all-children-valid support (1024/1024). This is a declared choice to explore, not an error in the source FITS. No physical beam/noise leakage correction is implied.

## 3. Scope and DAG status

- R5 constructive identity: `derived`; Wolfram exact finite check and Python numerical manufactured check: `numerically_checked`.
- C5/C6 audit implementation: see test receipt; actual 2048 source files are absent in sandbox, and connected local desktop commands are limited by the remote plugin's monthly usage cap. `native_healpy_run=NOT_RUN`.
- Immutable OE expected SHA repair requires independently verified original source; `P2/L01=pending`, `P2/L03=unresolved`; historical T-mask control is still geometry-only.
- Six-paper submission gates: 0/6 ready; nodes scoped complete remain **14/42** with 28 pending. This run adds a theorem, a typed diagnostic and executable tests, **not** a falsely completed DAG node.