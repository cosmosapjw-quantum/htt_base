"""Acquire only official public data into the D03-owned external directory.

No downloaded Python is executed. Failed transports are retained in receipts.
"""
from pathlib import Path
import hashlib
import json
import urllib.request
import datetime
import argparse
import ssl
import urllib.parse

ROOT = Path('/mnt/extdrive/workdir/htt_open_data/pantheonplus/d03_crosswalk_20261018')
COMMIT = 'c447f0fea703fcd0fff57de5000947b5ca81286b'
BASE = f'https://raw.githubusercontent.com/PantheonPlusSH0ES/DataRelease/{COMMIT}/'
FILES = {
    'distance_README': BASE+'Pantheon%2B_Data/4_DISTANCES_AND_COVAR/README',
    'SH0ES_README.md': BASE+'SH0ES_Data/README.md',
    'SH0ES_table2.README': BASE+'SH0ES_Data/table2.README',
    'SH0ES_table2.tex': BASE+'SH0ES_Data/table2.tex',
    'all_redshifts_PVs.csv': BASE+'Pantheon%2B_Data/1_DATA/all_redshifts_PVs.csv',
}
for prefix in ('allc', 'alll', 'ally'):
    name = prefix+'_shoes_ceph_topantheonwt6.0_112221.fits'
    FILES[name+'.lfs_pointer'] = BASE+'SH0ES_Data/'+name
    FILES[name] = f'https://media.githubusercontent.com/media/PantheonPlusSH0ES/DataRelease/{COMMIT}/SH0ES_Data/{name}'


def run():
    ROOT.mkdir(parents=True, exist_ok=True)
    receipt_path = ROOT/'ACQUISITION.json'
    records = json.loads(receipt_path.read_text()) if receipt_path.exists() else []
    for name, url in FILES.items():
        path = ROOT/name
        raw_source=ROOT/(name+'.lfs_pointer')
        if name.endswith('.fits') and raw_source.exists() and raw_source.read_bytes().startswith(b'SIMPLE  ='):
            print('RAW_GITHUB_IS_ACTUAL_FITS',raw_source.name)
            continue
        if path.exists():
            print('REUSE', name, path.stat().st_size)
            continue
        item = {'name':name, 'url':url, 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                data = response.read(110_000_001)
                if len(data)>110_000_000:
                    raise ValueError('110 MB per-source ceiling exceeded')
                item.update(status=response.status, final_url=response.url,
                            headers=dict(response.headers), bytes=len(data),
                            sha256=hashlib.sha256(data).hexdigest())
            if not data or data.lstrip().lower().startswith(b'<!doctype html'):
                raise ValueError('empty or HTML source')
            path.write_bytes(data)
            item['result']='FETCHED_DATA_NOT_SCIENTIFIC_ADMISSION'
        except Exception as exc:
            item.update(result='FAILED', error=repr(exc))
        records.append(item)
        receipt_path.write_text(json.dumps(records,indent=2)+'\n')
        print(name, item['result'], item.get('bytes'), item.get('error',''))
    for pointer in ROOT.glob('*.lfs_pointer'):
        data_path=pointer.with_name(pointer.name.removesuffix('.lfs_pointer'))
        raw=pointer.read_bytes()
        if not raw.startswith(b'version https://git-lfs.github.com/spec/v1'):
            continue
        text=raw.decode('ascii')
        if text.startswith('version https://git-lfs.github.com/spec/v1') and data_path.exists():
            fields=dict(line.split(' ',1) for line in text.splitlines()[1:])
            assert data_path.stat().st_size==int(fields['size'])
            assert hashlib.sha256(data_path.read_bytes()).hexdigest()==fields['oid'].split(':')[1]
            print('LFS_SHA_SIZE_MATCH',data_path.name)
    # The public EDD endpoint currently has an expired server certificate.
    # Save only the schema, source form and the ordinary query response.
    # A human-verification response is a barrier, never bypassed.
    exploratory=ssl._create_unverified_context()
    query=urllib.parse.urlencode({'tblbool[]':'kcf4snia','kcf4snia_cols[]':'All',
          'submit1':'All','rowStart':'1','rowEnd':'2000','num_catalogs':'1',
          'catalogs_imploded':'kcf4snia','pgcnum':''}).encode('ascii')
    for name,url,body in [('EDD_schema.html','https://edd.ifa.hawaii.edu/describe_columns.php?table=kcf4snia',None),
                          ('EDD_form.html','https://edd.ifa.hawaii.edu/dfirst.php',None),
                          ('EDD_query_response.html','https://edd.ifa.hawaii.edu/dsecond.php',query)]:
        path=ROOT/name
        if path.exists(): continue
        item={'name':name,'url':url,'tls':'UNVERIFIED_EXPIRED_CERT_EXPLORATORY',
              'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        try:
            with urllib.request.urlopen(urllib.request.Request(url,data=body),context=exploratory,timeout=30) as response:
                blob=response.read(2_000_000)
                path.write_bytes(blob)
                item.update(status=response.status,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),
                            result='HUMAN_VERIFICATION_BARRIER' if b'Please verify that you are not a robot' in blob else 'EXPLORATORY_SCHEMA_ONLY')
        except Exception as exc: item.update(result='FAILED',error=repr(exc))
        records.append(item);receipt_path.write_text(json.dumps(records,indent=2)+'\n')
        print(name,item['result'])


if __name__=='__main__':
    run()
