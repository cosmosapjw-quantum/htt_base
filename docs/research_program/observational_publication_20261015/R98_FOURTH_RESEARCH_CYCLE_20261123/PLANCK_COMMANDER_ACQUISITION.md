# Commander PR3 acquisition and input verification

## Two resolved archive entries

The ESA PR3 CMB-map supplement identifies 999 usable component-separated signal realizations and 300 noise realizations per split. ID 00000 has distinct full-mission signal and noise products. In the bounded R98 archive preflight, both returned HTTP 200 with the requested filename, image/fits content type and 5,760-byte readable FITS primary/BINTABLE headers. Each has NSIDE 2048, RING ordering, I/Q/U in K_CMB and 1,024 float32 values per cell per channel. ESA ignored the Range request. The clients closed both streams immediately after reading the headers. Their generic header SHA-256 is identical, 49ac7aea70f04d5eee42ca1754566099027d88f40d9722eb84338761406fb46e. No complete remote Commander object was transferred.

- [Official PR3 CMB map and simulation conventions](https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/CMB_maps)
- [Commander ID 00000 full-mission signal](https://pla.esac.esa.int/pla/aio/product-action?SIMULATED_MAP.FILE_ID=dx12_v3_commander_cmb_mc_00000_raw.fits)
- [Commander ID 00000 full-mission noise](https://pla.esac.esa.int/pla/aio/product-action?SIMULATED_MAP.FILE_ID=dx12_v3_commander_noise_mc_00000_raw.fits)

The cached local signal ID 00000 was fully scanned and has 603,987,840 bytes and SHA-256 c84d83bf33d6c64287ebc37d1e07c649546fa1f29febf5c4fa7d295243f17a27. All three fields contain 50,331,648 finite values. The remote prefix matches the local prefix. Matching an independent publisher digest for the full local signal file is still open. No canonical Commander noise file for ID 00000 was found. A five-second HEAD request for HM1 noise timed out, so this check assigns no release status to that product.

## Executable intake

From the repository root, refresh the six release indexes, verify the auto-selected LoTSS source-table header, and read only the two bounded Commander headers:

```bash
.venv/bin/python -m scripts.r98.acquisition_preflight
```

The future acquisition command below requests **one** exact full-mission noise product and permits up to 603,987,840 science bytes for that object. It has not been run for the absent noise file. New payloads are written under the owner's Downloads directory; existing canonical files are read in place.

```bash
.venv/bin/python -m scripts.r98.acquisition_preflight --fetch dx12_v3_commander_noise_mc_00000_raw.fits --budget-bytes 603987840
```

Only two exact ESA IDs and three pre-existing R90 Quaia template IDs are supported. One ID is accepted per command. A streamed download is capped by the registered object size, must return the matching ESA filename, and is hashed in bounded chunks. The completion path verifies FITS geometry, column types, units, logical byte length and finite-pixel counts before publishing the file and receipt. The receipt records the local SHA-256. An independently obtained full-object digest can be supplied with `--expected-sha256`; its provenance must be recorded by the caller. Fresh downloads without such a digest are transport-verified local artifacts. Sources with identical generic headers still require payload- and release-level qualification.

A partial Quaia file uses the published Zenodo MD5. A complete valid partial is finalized locally before issuing any network request. A corrupt complete partial is kept for examination. For Commander, an existing partial also needs a known full-object SHA-256 (or a receipt from the previously completed transfer for a complete partial). For a genuinely partial body the server must return 206 with exactly the expected offset, final byte and total size. A 200 reply to a resume request preserves the partial untouched. Restarting from zero requires a clean partial path after preserving any earlier bytes. Concurrent requests for the same file are serialized.

The source IDs, component pipeline, realization correspondence, observing period, beam, masks, residual foreground model and selection law must be matched before applying the P2 estimator and re-evaluating SQ-CMB-NULL. New physical parameters, Commander ranks and an independent-sky interpretation do not follow from a successful network transfer.

## Other repaired source indexes

The former Gaia URL returned 404. The ESA EDR3 archive's agn_cross_id data-model page returned the Gaia-CRF3 documentation. The Strasbourg FTP path and an alternate HTML ReadMe timed out from the owner host; the CDS VizieR Harvard mirror returned the Cosmicflows-4 catalogue. This is the released post-intercalibration survey. The joint upstream zero-point law remains an outstanding input. The status and exact URLs are in ACQUISITION_PREFLIGHT.json.

- [ESA Gaia-CRF3 source table](https://gea.esac.esa.int/archive/documentation/GEDR3/Gaia_archive/chap_datamodel/sec_dm_auxiliary_tables/ssec_dm_agn_cross_id.html)
- [CDS VizieR Cosmicflows-4 mirror](https://vizier.cfa.harvard.edu/viz-bin/VizieR?-source=J%2FApJ%2F944%2F94)
- [LoTSS DR3 release](https://lofar-surveys.org/dr3.html)

The LoTSS release-page prose reports 13,664,379 sources; the published source catalogue's own FITS extension LoTSS_DR3_srl reports 13,667,877 rows. The server honored the requested bytes 11520–20159 with HTTP 206. These 8,640 extension-header bytes are byte-identical to the owner's local header (SHA-256 a3d6789ef08ba5e84a3edb7ada897b2db28dc201922bc59cd18901e261868056). The local and public table row counts agree, both exceeding the webpage number by 3,498. The cause of the prose discrepancy remains unresolved. The comparison transferred zero catalogue rows and does not establish identity of the full 3 GB payload. [Official v1.0 source catalogue](https://lofar-surveys.org/public/DR3/catalogues/LoTSS_DR3_v1.0.srl.fits).

The targeted command `.venv/bin/python -m pytest -q tests/obsstat/test_r98_acquisition_preflight.py` passed 11 cases, covering complete and corrupt partials, exact and rejected range responses, maximum file size, full SHA/MD5 replay, unbound Commander partials, correct product headers, and a header-limited LoTSS row-count comparison.
