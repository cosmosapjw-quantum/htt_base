# RB22 CCHP-JAGB and KiDS-1000 source controls

## Scope

Descriptive source-bound summaries only. No uncertainty propagation, significance testing, cosmological likelihood, distance estimate, or physical-law claim is made.
CCHP RGC is preserved as the released coordinate; its unit is unresolved here and no conversion is applied.
KiDS values are the supplied five tomographic SOM n(z) tables. The source table labels columns `binstart, density`; this run treats each equally spaced row as nonnegative bin weight, normalizes those weights, and assumes uniform density within each bin only for quantile interpolation. The equal spacing means normalizing density×binwidth and normalizing row weights give the same bin probabilities.

## Sources

- CCHP ZIP SHA-256: `509fa70bff28337de5edb099b75b17266eed1537698c475e361f20bafeb7fdcd`. Zenodo DOI 10.5281/zenodo.14502265; README identifies JWST NIRCam photometry for Lee et al. (2024).
- KiDS tarball SHA-256: `1962a9117413f7fbb8adb863e4a85e250998257572cfffcbe2834e61c7d1704a`. Official KiDS DR4 page calls this a SOM-calibrated n(z) tarball for the five tomographic bins; see https://kids.strw.leidenuniv.nl/DR4/KiDS-1000_shearcatalogue.php and Hildebrandt et al. 2021 https://arxiv.org/abs/2007.15635.
- CCHP release source URL: https://zenodo.org/api/records/14502265/files/abiglee7/CCHP-JAGB-v1.zip/content

## CCHP-JAGB

Rows: 183543 across 11 host tables.
Each filter group is summarized separately. Within-host radial quartiles use empirical 25/50/75 percentiles of released RGC; color statistics are median and IQR. Spearman rho is descriptive only and has no p-value.

| Host | Color | Rows | Finite color pairs | Missing color pairs | Missing RGC | Finite color and RGC | Spearman rho |
|---|---|---:|---:|---:|---:|---:|---:|
| m101 | F115W-F444W | 9019 | 9019 | 0 | 0 | 9019 | -0.0198032231126782 |
| n1365 | F115W-F356W | 7298 | 7298 | 0 | 0 | 7298 | -0.01986252857751572 |
| n2442 | F115W-F356W | 8209 | 8209 | 0 | 0 | 8209 | -0.03645286880058771 |
| n3972 | F115W-F356W | 2044 | 2044 | 0 | 0 | 2044 | -0.05269292365759235 |
| n4038 | F115W-F356W | 4521 | 4521 | 0 | 0 | 4521 | -0.025087101958771403 |
| n4258 | F115W-F356W | 131005 | 70021 | 60984 | 0 | 70021 | -0.4012494387534523 |
| n4258 | F115W-F444W | 131005 | 60984 | 70021 | 0 | 60984 | -0.6449772785095087 |
| n4424 | F115W-F356W | 1750 | 1750 | 0 | 0 | 1750 | -0.04807152266310029 |
| n4536 | F115W-F444W | 4693 | 4693 | 0 | 0 | 4693 | -0.05022246506960355 |
| n4639 | F115W-F356W | 3153 | 3153 | 0 | 0 | 3153 | -0.0521421942198965 |
| n5643 | F115W-F356W | 8340 | 8340 | 0 | 0 | 8340 | 0.030257138755666803 |
| n7250 | F115W-F444W | 3511 | 3511 | 0 | 0 | 3511 | -0.1233903397982102 |

## KiDS SOM n(z)

| Tomographic bin | Mean z | q16 | q50 | q84 |
|---|---:|---:|---:|---:|
| TOMO1 | 0.257126 | 0.139229 | 0.232274 | 0.339787 |
| TOMO2 | 0.402716 | 0.303899 | 0.383953 | 0.504385 |
| TOMO3 | 0.563598 | 0.396400 | 0.567110 | 0.685778 |
| TOMO4 | 0.791830 | 0.671836 | 0.771000 | 0.905535 |
| TOMO5 | 0.983770 | 0.779232 | 0.958577 | 1.190379 |

Pairwise overlap is the descriptive discrete coefficient `sum_i min(p_i, q_i)` on the shared redshift grid. It is not an independence or covariance statement.
