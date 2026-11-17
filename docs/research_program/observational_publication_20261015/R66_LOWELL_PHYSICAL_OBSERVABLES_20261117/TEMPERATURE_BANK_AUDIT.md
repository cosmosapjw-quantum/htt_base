# R66 targeted Commander temperature-bank repair

Read-only bounded source search after parent R8 reported that the extracted T coefficients from all100 cached `npipe6v20_commander_cmb_2048_mc_0300..0399_005a.fits` were zero and the covariance was rejected as singular. This report does not independently execute that numerical check. No FITS payload, scientific producer, download or native write was used here.

**A separate actual public Commander simulation product family is present in the previously cached complete PLA catalog:**

```
npipe6v20_commander_cmb_mc_0200.fits
...
npipe6v20_commander_cmb_mc_0299.fits
```

There is **no `2048` or `_005a` in these filenames**, and also no literal `4096`. Searching for `commander_cmb_4096` would miss them. The cached catalog contains exactly100distinct IDs200..299 with these names, each1610622720bytes. The catalog is `/mnt/extdrive/workdir/htt_open_data/r36_pr4_contract_preparation/PLA_PR4_ALL_SIMULATED_MAPS.json`, SHA256 `05ae88c82a63887829a4f691b8dbfccfdbba7268c5a230ecc5546c5e7b0224f0` (directly recomputed from these JSON bytes). It has6700total rows and1300Commander rows:400A2048,400B2048,400full2048 and this separate100product family. The first three families have603990720bytes per file.

| Exact file | PLA OID | MC number | Bytes | Catalog role |
|---|---:|---:|---:|---|
| npipe6v20_commander_cmb_mc_0200.fits |93361|200|1610622720|PR4,COMP_SEPARATION,full,cmb,commander,npipe6v20|
| npipe6v20_commander_cmb_mc_0299.fits |93448|299|1610622720|same|

Catalog distribution path is `simulated_maps/PR4/comp_separation`, server file root `/pla/plaps/simulated_maps/PR4/comp_separation`; dataAccessReference for0200 is `data-action?SIMULATED_MAP.SIMULATED_MAP_OID=93361`.

The exact public product URL formed with the documented official PLA endpoint is:

<https://pla.esac.esa.int/pla/aio/product-action?SIMULATED_MAP.FILE_ID=npipe6v20_commander_cmb_mc_0200.fits>

A second exact identifier endpoint is:

<https://pla.esac.esa.int/pla/aio/data-action?SIMULATED_MAP.SIMULATED_MAP_OID=93361>

These endpoints were **not requested** in this task; public release identity is supported by the saved actual PLA catalog and the saved official wiki, not new HTTP payload verification. The paper reported by the parent (`2506.22795`,100native4096Tsimulations) suggests this separate family is the relevant temperature candidate. This task has not inspected its FITS headers, so native4096/HDU/units/nonzeroT are **unresolved pending one product header and payload qualification**; file size and absence of2048 in name are not used as conclusive physics evidence.

The preserved official wiki `/mnt/extdrive/workdir/htt_open_data/r36_commander_response_source_research/esa_simulation_data_current.html`, lines605–614, gives the Commander product endpoint and lists realization0200..0299. Its illustrated URL is the2048/0300/005a polarization example, so the illustration must not replace the actual catalog's separate0200..0299family. The current exact catalog provides the constructive filename/OID resolution missing in that prose.

Bounded local inventory checked the exact-name pattern `npipe6v20_commander_cmb_mc_*` in:

- `/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/cache`
- `/mnt/extdrive/workdir/raw/planck_npipe_pr4/commander`
- `/mnt/extdrive/workdir/htt_open_data/research20261022/pr4`

No matching file was found in those three source/cache directories. Earlier compact caches in `r36_pr4_actual/analysis` are100E/Barrays only and carry noT. Targeted repository/source searches found no existing Commander temperatureMCcompactbank under this exact family. This is a bounded negative inventory, not a whole-drive proof of absence.

The existing source acquisition implementation `/mnt/extdrive/workdir/htt_open_data/r36_pr4_transfer_repair_preparation/fetch_commander_mc.py` is **not configured for this temperature candidate**: its name/selection code is fixed to2048/005aIDs300+ and uses the same cached catalog. Its source shows official-resolver-http10 handling but must not be executed unchanged for the newly identified family. No new acquisition DAG or permanent blocker is proposed.

Minimal next concrete source-repair action, if the parent elects acquisition, is one official product0200/OID93361: inspect metadata/HDU/unit/resolution and a small actual temperature payload, then pass it through the declared temperature estimator. If it is the correct nonzero released temperature realization, use this exact family and preserve its200..299realization identities. Do not reinterpret cached2048/005a polarization products as temperature null skies or regularize their zero-T covariance. No SMICA substitution or restricted SEVEM route is needed to pursue this public Commander candidate.

This amends the earlier history report's suggestion that one could simply extract usefulTfrom the cached0300..0399bank: that suggestion was conditional and did not inspect itsTpayload; parent R8's concrete zero-T result invalidates it. The actual observedCommanderTand deterministicstress quotient remain usable independently of whether this separateMCfamily can be qualified.
