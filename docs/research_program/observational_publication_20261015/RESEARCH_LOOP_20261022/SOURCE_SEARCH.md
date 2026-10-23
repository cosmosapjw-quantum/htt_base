# External source search — scope and useful changes

2026-10-22. Owner: research intake; C0 source research, no physical admission.
Primary publications, author releases and official archives determine the claims.
SciSpace and Exa are discovery tools; their ranking/abstracts do not certify a
payload. The data worker's author-source acquisition is in [data/REPORT.md](data/REPORT.md).

## What changed

- The [Pantheon+ author release](https://github.com/PantheonPlusSH0ES/DataRelease/tree/c447f0fea703fcd0fff57de5000947b5ca81286b)
  supplies the explicit two-redshift likelihood convention. Its distinction from
  the retained zCMB template is now measured on the same row IDs.
- The [IRSA LFI product page](https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/LFI_Products.html)
  lists **R4.00** year-1-3 and year-2-4 30GHz maps under a `release_3` URL path.
  The product release is R4.00; URL-directory naming alone is not its release.
  These are the observed A/B availability path missing in the prior checkpoint.
- [NPIPE paper Table 5](https://www.aanda.org/articles/aa/full_html/2020/11/aa38073-20/T5.html)
  assigns 30GHz A to years1,3 and B to years2,4 **and start of5**. The
  [ESA frequency-map supplement](https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/Frequency_maps)
  uses the delivered year-1-3/year-2-4 names. Keep the paper's start-of5 detail;
  filenames alone do not establish exact sample timestamps. These are alternating-
  year splits, not horns27/28 or ringhalf1/2.
- [NERSC misc](https://portal.nersc.gov/cfs/cmb/planck2020/misc/)
  exposes the PR4 LoLLiPoP masks and RIMO/transfer archive. A mask intended for
  low-ell component-separated analysis does not validate a raw30GHz null.
- [CMB-S4 Quickpol listing](https://data.cmb-s4.org/planck_pr4-quickpol.html)
  advertises exact 030Ax030B beam/window products. Its linked Globus manifest and
  files returned HTTP404 on unauthenticated probes. Listing existence is not
  acquisition. The data report preserves those failed endpoints. A subsequent
  [official NERSC RIMO archive](https://portal.nersc.gov/cfs/cmb/planck2020/misc/PLANCK_RIMO_TF_R4.00.tar.gz)
  supplied the exact named `030Ax030B` Bl_TEB and Wl members. Their byte identity,
  FITS schema and finite values were checked. This resolves product availability;
  foreground/map-processing and statistic-specific null obligations remain.

## Search coverage and limitations

Parent ran two SciSpace questions (10 results each): matched NPIPE polarization
products, and existing computed Bianchi polarized templates. Duplicate paper
records, unrelated speculative templates, general isotropic codes and spectral-only
products were excluded. This is 20 search hits, not 20 validated sources.
Three Exa search workstreams covered PR4 product chains, exact30GHz A/B identity,
and precomputed physical polarized Bianchi output; follow-up fetching used official
NPIPE, LAMBDA, IRSA, CMB-S4 and the NPIPE paper/supplement. The data worker separately
used pinned author trees and primary papers. Counts are tool activity, not evidence
of completeness of the world's archives.

The atlas search returned known [Pontzen–Challinor](https://arxiv.org/abs/0706.2075),
[Saadeh et al.](https://arxiv.org/abs/1604.01024), and
[Sung–Coles](https://arxiv.org/abs/0905.2307) paths. The existing source inventory
already distinguishes numeric temperature-only fixtures, animations, figures and
code from a physical polarized all-m/history payload. No new qualified numeric
payload appeared in these results; the old source downloads were reused and no
solver was executed. This bounded search establishes no universal absence claim.

An attempted guessed IRSA `release_4/` URL and a guessed CMB-S4 `detset` page were
404/CRAWL_NOT_FOUND. Following the official LAMBDA→IRSA links resolved the actual
R4 product path. This was a changed source route, not repeated blind retry.
The CMB-S4 direct-download paths were tested without authentication; no login or
access-wall bypass was attempted.

Wolfram context search returned irrelevant/general computational documentation;
none was used as cosmological evidence. A stateless evaluator call then checked
the explicit finite rational and derivative expressions in
[WOLFRAM_CHECK.json](WOLFRAM_CHECK.json). No persistent kernel was started.
