#!/usr/bin/env python3
"""Check known input structure after HTTPS transport hashes have been recorded."""
import argparse,json,hashlib
from pathlib import Path

def ascii_count(path):
    if not path.exists():return {'status':'MISSING'}
    with path.open('rb') as f:lines=[line for line in f if line.strip() and not line.startswith((b'#',b'!'))]
    return {'status':'CHECKED_ROWS','row_count':len(lines),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def fits_header(path):
    if not path.exists():return {'status':'MISSING'}
    try:from astropy.io import fits
    except ImportError:return {'status':'BLOCKED_ASTROPY_NOT_INSTALLED'}
    with fits.open(path,memmap=True,mode='readonly',lazy_load_hdus=True) as f:
        return {'status':'HEADER_READ', 'HDU_count':len(f),'hdus':[
            {'index':i,'extname':h.header.get('EXTNAME'),'nside':h.header.get('NSIDE'),
            'ordering':h.header.get('ORDERING'),'coordsys':h.header.get('COORDSYS'),
            'columns':[c.name for c in h.columns] if hasattr(h,'columns') and h.columns else []}
            for i,h in enumerate(f)]}

def main():
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=Path('/mnt/extdrive/workdir/htt_open_data'));args=a.parse_args()
    root=args.root; rows={name:ascii_count(root/'cf4'/'J_ApJ_944_94'/name) for name in ['table2.dat','table3.dat','table4.dat']}
    fitsresults={}
    planck=root/'planck'/'PR3'
    for p in sorted(planck.rglob('*.fits')):
        fitsresults[str(p.relative_to(root))]=fits_header(p)
    issues=[]
    for name,expected in [('table2.dat',55877),('table3.dat',38053),('table4.dat',38053)]:
        val=rows[name]
        if val.get('row_count')!=expected:
            issues.append(f'{name}: row count {val.get("row_count")} != {expected}; CDS 38053 released rows vs 38065 original paper are distinct')
    for name,data in fitsresults.items():
        cols=set(c for d in data.get('hdus',[]) for c in d.get('columns',[]))
        if name.endswith('smica-nosz_2048_R3.00_full.fits') and cols.intersection({'Q_STOKES','U_STOKES'}):
            issues.append('unexpected Q/U in declared noSZ temperature-only: inspect release identity')
    result={'schema':'htt.input_structural_audit/1','cf4':rows,'planck_fits':fitsresults,'issues':issues,
     'scientific_claim':'FILE_STRUCTURE_ONLY_NO_SOURCE_SELECTION_OR_TRANSFER_VALIDATED'}
    dest=root/'provenance'/'INPUT_STRUCTURE_AUDIT.json';dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('Saved',dest);print('Issues',issues)
    return 1 if issues else 0
if __name__=='__main__':raise SystemExit(main())
