# HFI RIMO R3.01 source intake

Determination: `INTAKE_INCOMPLETE`.

Owner: obsstat. Scope: source qualification only, C0, non-claim-bearing;
transfer_source: none. This candidate does not complete D04/L03 or change any
scientific admission. Independent Astra source assessment is pending.

The official IRSA URL and final URL are
https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/HFI_RIMO_BEAMS_R3.01.tar.gz.
The parent-owned create-only fetch completed with status DOWNLOADED, 86,556,876
bytes and local SHA-256
`187755434816addc045f13a4efd8515bb86b83531adc0eb7586412d9cfca4994`.
The verified object is outside Git at
`/mnt/extdrive/workdir/htt_open_data/planck/PR3/beams/HFI_RIMO_BEAMS_R3.01.tar.gz`;
its adjacent `.receipt.json` records time 2026-10-18T13:17:19.438971+00:00,
Last-Modified `Mon, 19 Aug 2019 22:12:13 GMT`, content type application/x-gzip,
ETag unavailable. Upstream checksum is unavailable. The fetch implementation
requires HTTP 200 and validates gzip CRC/format; the receipt does not separately
persist the numeric HTTP status. Acquisition wall time was not instrumented
exactly; the parent observed approximately six minutes, below its 600-second cap.

The first official metadata command matched archive bytes/SHA/path to that
receipt and stopped at the first decompressed 512-byte block with
`tarfile.InvalidHeaderError: bad checksum`. It indexed zero members. This is a
format/parser obstruction, not evidence that split response information is
absent and not a scientific-integrity finding. The actual first block was not
retained by the first-run parser; a diagnostic requires separate approval.

All archive contents remain uninspected. In particular, no frequency/detector or
full/hm1/hm2/oe1/oe2 association, HDU/column/unit/matrix axis, multipole range,
amplitude/spectrum/covariance semantics, T/E/B/cross-field definition,
lm-to-l'm'/spatial/scan dependence, normalization/pixel-window/calibration/
LFI-renormalization/SMICA connection, or uncertainty/eigenvalue/correlation/
confidence convention has been qualified. Internal release declarations have
not been reached and cannot yet be compared with the R3.01 source label.

`SOURCE_INDEX.json` preserves the exact first outcome, fetched-source receipt,
command, interpreter and resource accounting. Decompressed bytes including skip:
512; retained decoded metadata: 0; physical tar headers indexed: 0;
inspection elapsed: 0.0003563729114830494 s; complete command internal elapsed:
0.41343866602983326 s; max RSS: 419,600 KiB; observed process threads: 2;
address-space limit: 536,870,912 bytes. The command used the existing canonical
`.venv/bin/python`, Astropy 8.0.2, requested executor gpt-6.1-sol/high and
observed runtime UNKNOWN. No extraction, link following, upstream execution,
numeric FITS columns, beam/noise/map computation, or network fetch occurred.

## Commands and raw outcomes

Parser/control fixture command:

```text
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python -m pytest -q -o addopts= docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D04_HFI_BEAM_SOURCE/test_inspect_source.py
```

First outcome:

```text
......                                                                   [100%]
6 passed in 0.51s
```

After exact-cap EOF and observed-thread hardening, the same fixture command:

```text
......                                                                   [100%]
6 passed in 4.06s
```

Fixtures cover BINTABLE PCOUNT heap sizing, later HDU header reachability,
duplicate literal names, PAX long names, links, malformed/nested content, and
byte/member/metadata/item/wall bounds. They are parser/control fixtures and do
not charge or replace any SDSS/science execution.

Official first command (exit 2):

```text
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D04_HFI_BEAM_SOURCE/inspect_source.py /mnt/extdrive/workdir/htt_open_data/planck/PR3/beams/HFI_RIMO_BEAMS_R3.01.tar.gz docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D04_HFI_BEAM_SOURCE/SOURCE_INDEX.json --fetch-receipt /mnt/extdrive/workdir/htt_open_data/planck/PR3/beams/HFI_RIMO_BEAMS_R3.01.tar.gz.receipt.json
```

```json
{
  "coverage": "INTAKE_INCOMPLETE",
  "obstruction": {
    "type": "InvalidHeaderError",
    "message": "bad checksum",
    "active_member_ordinal": null,
    "uninspected": "active member remainder and all later archive contents"
  },
  "resources": {
    "decompressed_bytes_including_skip": 512,
    "retained_decoded_metadata_bytes": 0,
    "physical_tar_headers_indexed": 0,
    "inspection_elapsed_seconds": 0.0003563729114830494,
    "max_rss_kib": 419600
  }
}
```

A preparatory local Astropy API lookup tried nonexistent
`_BaseHDU._data_size.fget` and returned AttributeError. It performed no source
inspection. The implementation instead uses the installed public
`Header.data_size` property, confirmed from local Astropy HDU source and the
synthetic multi-HDU/heap fixture; no API behavior was inferred from that failed
lookup. This is preserved as the first preparatory failure.

## Claim audit

The bounded source intake and its tested parser are IMPLEMENTED. The official
source qualification is INCOMPLETE; numeric validity and response-law support
remain UNKNOWN. No upgraded scientific claims, native-transfer claims, family
claims, manuscript changes, or permanent claim-ledger updates follow. The
required next decision is a bounded format diagnosis, followed by separate
independent Astra review; no original-node admission is authorized.
