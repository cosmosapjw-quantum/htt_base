# Cosmicflows-4 CDS 404 recovery (2026-10-17 KST)

## Confirmed defect and source scope

The *already downloaded* Planck PR3 six masks (all 201,335,040 bytes) and the CDS
`ReadMe` (19,918 bytes) passed the user's transport-hash check; do **not** re-download them.
The original downloader incorrectly treats an HTTP 404 of a *fixed URL* as a transient,
and retries that same URL five times. The observed 404s apply only to CF4
`table2.dat`, `table3.dat`, `table4.dat` at the originally constructed HTTPS directory.

According to the official [CDS ReadMe](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/ApJ/944/94?format=html&tex=true),
the raw fixed-width file layout is:

| Original file | Record length (bytes) | Released rows |
|---|---:|---:|
| table2.dat | 190 | 55877 |
| table3.dat | 190 | 38053 |
| table4.dat | 157 | 38053 |

Their source server may expose compressed `.dat.gz` files rather than literal `.dat`.
The candidate `.gz` URLs used by this rescue code have **NOT been verified as HTTP 200
from this sandbox**. The script first tests candidate HTTPS endpoints on the *user's
machine*, rejects 404 without retry, checks gzip magic and decompresses to exact
expected fixed-width row counts; it then creates authenticated original-file receipts.
It does not overwrite existing raw files or Planck products.

If no such original can be verified, the downloader switches to **official VizieR**
ASU TSV exports:
- `J/ApJ/944/94/table2` (55877 galaxies), stored under `vizier/table2.tsv`
- `J/ApJ/944/94/groups` (38053 groups, combines Table 3/4), stored under `vizier/groups.tsv`

These are a *different dataset representation* than original fixed-width Table 3/4,
not their byte-identical source. The original `table[234].dat` remain absent when
this fallback is used. No downstream program requiring original byte layouts should
silently consume the TSV files; adapt the consumer with a declared provenance bridge.

VizieR ASU output is documented at:
https://vizier.cds.unistra.fr/doc/asu-summary.htx
Official target:
https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=J/ApJ/944/94

Additional public data: Extragalactic Distance Database at
https://edd.ifa.hawaii.edu/dfirst.php supplies updated table representations
and method-specific parent samples. Its CF4 group counts **may differ** from the
CDS release and therefore cannot be swapped without source-version reconciliation.

## Ubuntu terminal commands

Save/download this archive (e.g. `~/Downloads/HTT_CF4_CDS_404_RECOVERY_20261017.zip`).
The user-local original package is already at `/mnt/extdrive/workdir/htt_open_physics_20261016`.

```bash
ROOT=/mnt/extdrive/workdir/htt_open_data
mkdir -p /mnt/extdrive/workdir/htt_cf4_repair_20261017
unzip -oq ~/Downloads/HTT_CF4_CDS_404_RECOVERY_20261017.zip -d /mnt/extdrive/workdir/htt_cf4_repair_20261017
cd /mnt/extdrive/workdir/htt_cf4_repair_20261017

# Offline tests, no remote downloads needed; install pytest only if unavailable.
python3 -m pytest -q test_recover_cf4.py

# Review all candidate URLs and output paths without network calls:
python3 recover_cf4.py --root "$ROOT" --dry-run

# Attempt original compressed CDS fixed-width files; if none available,
# download official VizieR table2/groups under *different* filenames:
python3 recover_cf4.py --root "$ROOT" --mode auto

# Inspect per-file result, source URL, SHA and explicit representation class:
python3 -m json.tool "$ROOT/provenance/CF4_RECOVERY_AUDIT.json" | less

# Only when original raw triplet is verified, previous fixed-width checks pass:
python3 /mnt/extdrive/workdir/htt_open_physics_20261016/scripts/htt_data_fetch.py \
  --root "$ROOT" --group cf4 --verify
python3 /mnt/extdrive/workdir/htt_open_physics_20261016/scripts/htt_input_validate.py \
  --root "$ROOT"
```

If `.dat.gz` remains inaccessible, use the two TSV files through a **distinct adapter**.
To skip the unsuccessful attempts to raw endpoints:

```bash
python3 recover_cf4.py --root /mnt/extdrive/workdir/htt_open_data --mode vizier-only
```

### Important status distinction

- `RAW_RECOVERED_AND_VERIFIED`: complete original fixed-width catalogue, row counts,
  compression payload and receipt checked locally. Still no selection law.
- `VIZIER_REPRESENTATION_VERIFIED`: correct *alternative table* and rows; original
  `table3.dat` and `table4.dat` unfulfilled, no spurious `DOWNLOAD_RECEIPTS` entries.
- `VIZIER_UNAVAILABLE`: neither path passed local source-content checks. Do not use.

The script has no dependency other than Python 3.10+ standard library. Network transfer
was **NOT_RUN** here because the sandbox cannot access the relevant sites, but all
local transformation/path/receipt/failure tests were executed.

## Downstream physical-gate scope

Even valid CF4 source files only resolve the transport/input layer. H02 still needs
empirical selection/completeness, calibration, correlated peculiar velocities and a
normalized selected likelihood; K04 still needs a source-matched finite-redshift
optical transfer. The six-paper publication DAG must not be promoted on file
availability alone.
