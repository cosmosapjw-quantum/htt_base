#!/usr/bin/env python3
"""Gaia DR3 AGN-frame pilot. A *frame-calibration* source, not material vorticity."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ADQL="""SELECT TOP 10000
  g.source_id, g.ra, g.dec, g.pmra, g.pmdec, g.pmra_error,
  g.pmdec_error, g.pmra_pmdec_corr, g.astrometric_params_solved
FROM gaiadr3.gaia_source AS g
JOIN gaiadr3.agn_cross_id AS a ON g.source_id = a.source_id
WHERE g.pmra IS NOT NULL AND g.pmdec IS NOT NULL
  AND g.pmra_error > 0 AND g.pmdec_error > 0
ORDER BY g.source_id"""
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path('/mnt/extdrive/workdir/htt_open_data'))
    ap.add_argument('--print-query',action='store_true')
    ap.add_argument('--execute',action='store_true',help='run TAP query online; default only writes ADQL')
    args=ap.parse_args(); dest=args.root/'gaia'/'DR3';dest.mkdir(parents=True,exist_ok=True)
    (dest/'agn_pilot.adql').write_text(ADQL+'\n')
    print('ADQL saved',dest/'agn_pilot.adql')
    if args.print_query:print(ADQL)
    if not args.execute:return
    try:from astroquery.gaia import Gaia
    except ImportError as e:raise SystemExit('pip install astroquery astropy') from e
    Gaia.ROW_LIMIT=-1
    job=Gaia.launch_job_async(ADQL,dump_to_file=False)
    t=job.get_results();tmp=dest/'agn_pilot.ecsv.part'; out=dest/'agn_pilot.ecsv'
    t.write(tmp,format='ascii.ecsv',overwrite=True);tmp.replace(out)
    h=hashlib.sha256(out.read_bytes()).hexdigest()
    (dest/'agn_pilot_receipt.json').write_text(json.dumps({
        'source':'ESA Gaia TAP gaiadr3.gaia_source + agn_cross_id',
        'query_sha256':hashlib.sha256(ADQL.encode()).hexdigest(),
        'timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'rows':len(t),'sha256':h,'physical_interpretation':'quasar/reference-frame calibration only; no direct matter vorticity'
    },indent=2)+'\n')
    print('wrote',len(t),'rows',h)
if __name__=='__main__':main()
