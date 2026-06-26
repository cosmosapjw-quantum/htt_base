# Web CRAG Ledger

access_date: 2026-06-26
owner: COMMON
claim_tier: diagnostic_only
transfer_source: none
caveats:
- Web checks support planning only. They do not replace local input manifests.
- Availability, URLs, and product layouts can drift.

## Sources

| Topic | Source | Use | Caveat |
| --- | --- | --- | --- |
| Planck official data portal | https://pla.esac.esa.int/ | Confirms the Planck Legacy Archive is the official source for Planck data products. | Web UI/product paths must be verified during actual download. |
| Planck PR4/NPIPE overview | https://data.cmb-s4.org/planck_pr4.html | Confirms PR4/NPIPE is a common-pipeline reprocessing with lower noise/systematics and NERSC-hosted products. | Mirror/portal, not a substitute for data manifest. |
| Planck PR4 simulations context | https://www.aanda.org/articles/aa/full_html/2024/02/aa48015-23/aa48015-23.html | Notes PR4 provides end-to-end Monte Carlo simulations processed with NPIPE for bias characterization. | Exact simulation set must be manifest-bound. |
| CF4 WF/CR paper | https://arxiv.org/abs/2311.01340 | Describes CF4 velocity-field reconstruction using Bias Gaussianization, Wiener filtering, and constrained realizations. | Realization products still need access and hashes. |
| CF4 MNRAS version | https://academic.oup.com/mnras/article/527/2/3788/7419869 | Supports method context for WF/CR and CF4 velocity-field interpretation. | Paper does not provide repo-local data files. |
| Hoffman-Ribak constrained realizations | https://ui.adsabs.harvard.edu/abs/1991ApJ...380L...5H/abstract | Algorithmic basis for constrained Gaussian-field realizations. | Implementation details must be matched to supplied CF4 field products. |

## CRAG Takeaways

- K1 is the most direct blocker to discharge because the needed simulation class is public, but exact products and masks must be bound before any result row changes.
- CF4 WF/CR is methodologically aligned with K5/K6, but access to field realizations and release-matched mocks is the controlling blocker.
- PR10 remains separate; web evidence does not supply a native low-ell solver.

