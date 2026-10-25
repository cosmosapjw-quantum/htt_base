#!/usr/bin/env python3
"""Frozen exact-ID, outcome-blind Gaia source-property intake. No PM access."""
import collections
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import signal
import sys
import time
import traceback
import xml.etree.ElementTree as ET
import zipfile

import astropy
from astropy.io.votable import parse
import numpy as np
import requests

ROOT = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
BASE = Path(__file__).resolve().parent
CONTRACT = ROOT / 'docs/research_program/observational_publication_20261015/ADAPTIVE_RESEARCH_20261023/R25-GAIA-SOURCE-PROPERTY-INTAKE_INPUT.json'
PACKET = Path('/mnt/extdrive/workdir/htt_open_data/r25_root_space_recovery/receipts/POST_GAIA_EXECUTION_NEXT_PACKET.json')
ACK = Path('/mnt/extdrive/workdir/htt_open_data/r25_root_space_recovery/receipts/GAIA_PROPERTIES_ACTUAL_ACK.json')
TASK = 'R25-GAIA-SOURCE-PROPERTY-INTAKE'
PID = 'e381b2c8bc7aa239b8df9e66c69e652c01e3f5a7cd821437b005623512581976'
CID = '00508df7ec44ab6680ab8291868acaa203247aba18aaabfe2eaf029fc6ddad60'
AGENT = '/root/rc_e381b2c8bc7aa239'
START = time.monotonic()
WIRE_EMPTY = {}
WIRE_CHAR = {}
OFFLINE = '--offline-validate' in sys.argv
RECEIPT = {'task_id': TASK, 'packet_id': PID, 'input_identity': 'sha256:'+CID,
           'agent_id': AGENT, 'observed_runtime': 'UNKNOWN', 'requests': [],
           'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
           'command': 'PYTHONDONTWRITEBYTECODE=1 python -B acquire.py', 'cwd': str(BASE),
           'versions': {'python':platform.python_version(),'numpy':np.__version__,
                        'astropy':astropy.__version__,'requests':requests.__version__},
           'outcome_arrays_accessed': [], 'cache_first': {'exact_owned_caches_absent':True,
           'external_open_data_filename_search':'No qso_candidates/source_propert/gaia_properties cache candidates'},
           'preservation': {'original_acceptance':'17/42','alternate_acceptance':'18/42',
                            'historical48':'unchanged','one_use':'unchanged','ultra':'unchanged','R9':'UNKNOWN'}}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def save(name, obj):
    (BASE/name).write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')

def reserve():
    st=os.statvfs(BASE)
    assert st.f_bavail*st.f_frsize >= 2147483648, 'External reserve below 2GiB'

def request_query(name, sql, upload):
    if OFFLINE:
        previous=json.loads((BASE/f'raw/{name}_request.json').read_text())
        assert previous['params']['QUERY']==sql and previous['upload_sha256']==digest(upload)
        rec=[r for r in RECEIPT['requests'] if r['name']==name and r.get('http_status')==200]
        assert len(rec)==1 and rec[0]['complete_http_body']
        data=Path(rec[0]['raw_path']).read_bytes()
        assert digest(data)==rec[0]['sha256']
        return data
    params={'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable_plain','MAXREC':'5000',
            'UPLOAD':'ids4756,param:idsfile','QUERY':sql}
    save('raw/'+name+'_request.json', {'endpoint':contract['request']['endpoint'],
         'method':'POST','params':params,'upload_sha256':digest(upload),
         'upload_file':'inputs/ids4756.xml','connect_timeout':10,'read_timeout':45})
    for attempt in (1,2):
        reserve()
        t=time.monotonic()
        rec={'name':name,'attempt':attempt,'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
             'request_spec':'raw/'+name+'_request.json','upload_sha256':digest(upload)}
        RECEIPT['requests'].append(rec)
        save('RAW_RECEIPT.json',RECEIPT)
        try:
            with requests.post(contract['request']['endpoint'],data=params,
                 files={'idsfile':('ids4756.xml',upload,'application/x-votable+xml')},
                 timeout=(10,45),stream=True) as r:
                rec.update({'http_status':r.status_code,'response_headers':dict(r.headers),
                            'final_url':r.url,'redirects':[{'status':x.status_code,'url':x.url} for x in r.history]})
                path=BASE/f'raw/{name}_attempt{attempt}.vot'
                with path.open('wb') as f:
                    for chunk in r.iter_content(65536):
                        reserve()
                        f.write(chunk)
                data=path.read_bytes()
                rec.update({'raw_path':str(path),'bytes':len(data),'sha256':digest(data),
                            'elapsed_seconds':time.monotonic()-t,'complete_http_body':True})
                save('RAW_RECEIPT.json',RECEIPT)
                if r.status_code==200:
                    return data
                if attempt==1 and (r.status_code in (408,429) or 500<=r.status_code<600):
                    rec['retry_reason']='Transient HTTP status'
                    continue
                raise RuntimeError(f'{name}: HTTP {r.status_code}, no permitted retry remains')
        except (requests.exceptions.Timeout,requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError) as e:
            rec.update({'error_type':type(e).__name__,'error':str(e),'elapsed_seconds':time.monotonic()-t})
            save('RAW_RECEIPT.json',RECEIPT)
            if attempt==1:
                rec['retry_reason']='Transient transport failure'
                continue
            raise

def read_votable(data,name):
    tree=ET.fromstring(data)
    assert tree.attrib.get('version') in ['1.3','1.4','1.5'], 'Unexpected VOTable version for empty-cell null semantics'
    statuses=[x.attrib.get('value') for x in tree.iter() if x.tag.split('}')[-1]=='INFO' and x.attrib.get('name')=='QUERY_STATUS']
    assert statuses and all(s=='OK' for s in statuses), (name,'QUERY_STATUS',statuses)
    document=parse(io.BytesIO(data),verify='exception')
    tables=list(document.iter_tables())
    assert len(tables)==1,(name,'table count',len(tables))
    table=tables[0]
    xml_tables=[x for x in tree.iter() if x.tag.split('}')[-1]=='TABLE']
    assert len(xml_tables)==1
    xml_fields=[x for x in xml_tables[0] if x.tag.split('}')[-1]=='FIELD']
    xml_rows=[x for x in xml_tables[0].iter() if x.tag.split('}')[-1]=='TR']
    assert len(xml_rows)==len(table.array)
    wire={}
    for j,f in enumerate(xml_fields):
        key=f.attrib.get('ID',f.attrib['name'])
        wire[key]=[i for i,tr in enumerate(xml_rows) if tr[j].text is None or tr[j].text=='']
    WIRE_EMPTY[id(table.array)]=wire
    WIRE_CHAR[id(table.array)]={f.attrib.get('ID',f.attrib['name']):[tr[j].text for tr in xml_rows]
        for j,f in enumerate(xml_fields) if f.attrib['datatype'] in ['char','unicodeChar']}
    save(f'products/{name}_wire_masks.json',{'votable_version':tree.attrib.get('version'),
         'wire_empty_TD_indices':wire,
         'astropy_original_mask_indices':{f:np.flatnonzero(np.ma.getmaskarray(table.array[f])).tolist() for f in table.array.dtype.names},
         'astropy_original_values':{f:[None if np.ma.is_masked(v) else (v.item() if isinstance(v,np.generic) else v) for v in table.array[f]] for f in table.array.dtype.names},
         'normalization_source':'https://www.ivoa.net/documents/VOTable/20191021/REC-VOTable-1.4-20191021.html',
         'rule':'VOTable 1.3+ empty TD means null, including char; retain original parser masks and values separately. Whitespace char values stay unchanged.',
         'ambiguity':'Database SQL null versus hypothetical literal empty string is not recoverable from this wire representation; no database-null assertion.'})
    info={'query_statuses':statuses,'complete_xml':True,'rows':len(table.array),
          'fields':{f.ID or f.name:{'name':f.name,'datatype':f.datatype,'arraysize':f.arraysize,'unit':str(f.unit) if f.unit else None} for f in table.fields}}
    return table,info

def scalar(array,field,i):
    if i in WIRE_EMPTY.get(id(array),{}).get(field,[]):return None
    if field in WIRE_CHAR.get(id(array),{}):return WIRE_CHAR[id(array)][field][i]
    value=array[field][i]
    if np.ma.is_masked(value):return None
    if isinstance(value,np.generic): value=value.item()
    if isinstance(value,bytes): value=value.decode('utf-8')
    if isinstance(value,float):assert np.isfinite(value), (field,i,'nonfinite unmasked value')
    return value

def category(value):
    if value is None:return 'ROW_NULL'
    if value is True:return 'True'
    if value is False:return 'False'
    return str(value)

def run():
    global contract
    assert digest(CONTRACT.read_bytes())==CID
    contract=json.loads(CONTRACT.read_text())
    packet=json.loads(PACKET.read_text());ack=json.loads(ACK.read_text())
    assert packet['packet_id']==PID and packet['input_identity']=='sha256:'+CID
    assert ack['packet_id']==PID and ack['agent_id']==AGENT and ack['status']=='ACTUAL_NATIVE_LAUNCH_ACKNOWLEDGED'
    for p,n in [(CONTRACT,'contract.json'),(PACKET,'packet.json'),(ACK,'actual_ack.json')]:
        (BASE/'inputs'/n).write_bytes(p.read_bytes())
    source=ROOT/contract['source_id_input']['path']
    assert digest(source.read_bytes())==contract['source_id_input']['sha256']
    with zipfile.ZipFile(source) as z:
        ids_array=np.load(io.BytesIO(z.read('source_id.npy')),allow_pickle=False)
    assert ids_array.dtype==np.dtype('int64')
    ids=sorted(map(int,ids_array));assert len(ids)==len(set(ids))==4756
    canonical=''.join(str(i)+'\n' for i in ids).encode('ascii')
    assert len(canonical)==94469 and digest(canonical)==contract['source_id_input']['canonical_ID_sha256']
    (BASE/'inputs/source_ids.txt').write_bytes(canonical)
    upload=('<?xml version="1.0" encoding="UTF-8"?>\n<VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3"><RESOURCE><TABLE><FIELD name="source_id" datatype="long"/><DATA><TABLEDATA>'+''.join(f'<TR><TD>{i}</TD></TR>' for i in ids)+'</TABLEDATA></DATA></TABLE></RESOURCE></VOTABLE>\n').encode('ascii')
    (BASE/'inputs/ids4756.xml').write_bytes(upload)
    ut,ui=read_votable_upload(upload)
    assert [int(x) for x in ut.array['source_id']]==ids
    RECEIPT['input_identity_evidence']={'npz_sha256':contract['source_id_input']['sha256'],
         'opened_array_only':'source_id.npy','canonical_id_sha256':digest(canonical),
         'count':len(ids),'upload_sha256':digest(upload),'upload_bytes':len(upload)}
    save('RAW_RECEIPT.json',RECEIPT)
    main=request_query('property',contract['request']['main_SQL'],upload)
    mt,mi=read_votable(main,'property')
    # Never replay a successful main request, including after validation failure.
    counts=request_query('independent_count',contract['request']['independent_count_SQL'],upload)
    ct,ci=read_votable(counts,'independent_count')
    a=mt.array; names=set(a.dtype.names)
    assert len(a)==4756 and {'retained_source_id','qso_source_id'}<=names
    for field in ['retained_source_id','qso_source_id']:
        assert mi['fields'][field]['datatype']=='long',(field,mi['fields'][field])
    got=[scalar(a,'retained_source_id',i) for i in range(len(a))]
    assert got==ids and len(set(got))==4756
    assert len(ct.array)==1
    nleft=scalar(ct.array,'n_left',0);nmatched=scalar(ct.array,'n_matched',0)
    assert type(nleft) is int and type(nmatched) is int and nleft==4756
    fields=list(contract['advisor_live_discovery']['columns']); fields.remove('source_id')
    for f in fields:
        if f in names: assert mi['fields'][f]['datatype']==contract['advisor_live_discovery']['columns'][f],(f,mi['fields'][f])
    rows=[]; availability={f:collections.Counter() for f in fields}
    strata={k:collections.Counter() for k in ['host_flag','DSC','variability','selection_bit1']}
    cross={k:collections.Counter() for k in ['host_detected','transit_availability','module_selection_bits']}
    matched=0
    for i,sid in enumerate(ids):
        qid=scalar(a,'qso_source_id',i)
        if qid is not None: assert type(qid) is int and qid==sid;matched+=1
        row={'retained_source_id':sid,'qso_source_id':qid,'field_states':{}}
        for f in fields:
            val=scalar(a,f,i) if f in names else None
            row[f]=val
            state='FIELD_UNAVAILABLE' if f not in names else ('NO_QSO_ROW' if qid is None else ('ROW_NULL' if val is None else 'PRESENT'))
            if qid is None and f in names:assert val is None,(sid,f,'no-row non-null payload')
            row['field_states'][f]=state;availability[f][state]+=1
        flag=row['host_galaxy_flag']
        host='NO_QSO_ROW' if qid is None else ('FIELD_UNAVAILABLE' if 'host_galaxy_flag' not in names else ('ROW_NULL' if flag is None else (str(flag) if flag in range(1,7) else 'UNEXPECTED_CODE')))
        dsc='NO_QSO_ROW' if qid is None else ('FIELD_UNAVAILABLE' if 'classlabel_dsc_joint' not in names else category(row['classlabel_dsc_joint']))
        var='NO_QSO_ROW' if qid is None else ('FIELD_UNAVAILABLE' if 'vari_best_class_name' not in names else category(row['vari_best_class_name']))
        bits=row['source_selection_flags']
        bit1='NO_QSO_ROW' if qid is None else ('FIELD_UNAVAILABLE' if 'source_selection_flags' not in names else ('ROW_NULL' if bits is None else str(bool(bits&1))))
        row['strata']={'host_flag':host,'DSC':dsc,'variability':var,'selection_bit1':bit1,
                       'future_host_comparison':'Host1-2' if host in ['1','2'] else ('Host3' if host=='3' else 'EXCLUDED_FROM_PRIMARY_ONLY')}
        for k in strata:strata[k][row['strata'][k]]+=1
        for k,v in [('host_detected',category(row['host_galaxy_detected'])),('transit_availability',row['field_states']['n_transits']),('module_selection_bits',category(bits))]:cross[k][(host,v)]+=1
        rows.append(row)
    assert matched==nmatched
    avail={}
    for f,c in availability.items():
        avail[f]={s:c[s] for s in ['FIELD_UNAVAILABLE','NO_QSO_ROW','ROW_NULL','PRESENT']}
        assert sum(c.values())==4756
        if f in names:assert c['NO_QSO_ROW']+c['ROW_NULL']+c['PRESENT']==4756
    # Explicit zero-count strata retain the frozen host categories.
    for host in contract['outcome_blind_strata']['host_flags']:strata['host_flag'][host]+=0
    save('products/property_table.json',{'schema':'htt.gaia_source_properties/1','source_release':'Gaia DR3',
         'rows':rows,'fields':mi['fields'],'null_representation':'JSON null plus field_states; no zero filling'})
    summary={'rows':4756,'matched_qso_rows':matched,'no_qso_row':4756-matched,
         'independent_count':{'n_left':nleft,'n_matched':nmatched},'availability':avail,
         'strata':{k:dict(v) for k,v in strata.items()},
         'raw_crosstabs':{k:[{'host_flag':h,'value':v,'count':n} for (h,v),n in sorted(c.items())] for k,c in cross.items()},
         'semantics':contract['outcome_blind_strata'],
         'caveats':['Source-property association only; no causal centroid or independent physical validation.',
                    'DSC uses astrometry; scores are not newly calibrated probabilities.',
                    'No nonvariability inferred from missing metadata; flag5/False preserved without inconsistency rule.',
                    'No PM/covariance/outcome arrays accessed; original acceptance unchanged.']}
    save('products/AVAILABILITY.json',summary)
    validation={'status':'EXECUTION_VALIDATED_PENDING_INDEPENDENT_REVIEW','main':mi,'count':ci,
         'exact_4756_left_join':True,'exact_integer_ids':True,'count_agreement':True,
         'per_field_4756_identities':True,'preserved_masks_types_and_raw_values':True,
         'source_id_only_input_access':True,'no_successful_query_replay':True,
         'outcome_blind_strata_frozen':True,'qualified_product_admission':False}
    save('VALIDATION.json',validation)
    RECEIPT.update({'status':'EXECUTION_VALIDATED_PENDING_INDEPENDENT_REVIEW','elapsed_seconds':time.monotonic()-START,
                    'ended_utc':dt.datetime.now(dt.timezone.utc).isoformat()})
    save('RAW_RECEIPT.json',RECEIPT)
    print(json.dumps({'status':RECEIPT['status'],'matched':matched,'no_row':4756-matched,'strata':summary['strata']}))

def read_votable_upload(data):
    doc=parse(io.BytesIO(data),verify='exception'); table=list(doc.iter_tables())[0]
    return table,{}

if __name__=='__main__':
    def timeout(signum, frame):raise TimeoutError('Frozen 600 second wall limit')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(600)
    if OFFLINE:
        RECEIPT=json.loads((BASE/'RAW_RECEIPT.json').read_text())
        RECEIPT['offline_validation']={'command':'python -B acquire.py --offline-validate',
            'network_requests':0,'preserved_acquisition_elapsed_seconds':RECEIPT.get('elapsed_seconds'),
            'reason':'VOTable 1.3+ empty char TD null normalization; original mask evidence retained'}
    try:run()
    except BaseException as exc:
        RECEIPT.update({'status':'HOLD_EXECUTION_FAILURE','error_type':type(exc).__name__,'error':str(exc),
                        'traceback':traceback.format_exc(),'elapsed_seconds':time.monotonic()-START})
        save('RAW_RECEIPT.json',RECEIPT)
        print(RECEIPT['traceback'],file=sys.stderr)
        sys.exit(1)
