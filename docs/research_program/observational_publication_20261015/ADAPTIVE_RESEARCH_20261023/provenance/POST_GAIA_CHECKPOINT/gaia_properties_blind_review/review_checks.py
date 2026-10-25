"""Independent, offline review of frozen Gaia intake; never writes candidate."""
from pathlib import Path
import collections, datetime, hashlib, importlib.util, io, json, platform, resource, socket, struct, sys, time, traceback, xml.etree.ElementTree as ET, zipfile
import numpy as np
from astropy.io.votable import parse
import astropy
ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
B=Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_source_properties_20261023')
OUT=Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_properties_blind_review')
EXPECTED='005aa5cf96fe1350ef7690a275edd4ae61e9b30092266e8900c8b3d86b482568'
start=time.monotonic()
receipt={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':'PYTHONDONTWRITEBYTECODE=1 python -B review_checks.py','cwd':str(ROOT),'versions':{'python':platform.python_version(),'numpy':np.__version__,'astropy':astropy.__version__},'checks':{},'network_requests':0,'candidate_writes':0,'source_arrays_opened':[]}
def load(path):return json.loads(path.read_text())
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def write(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def local(x):return x.tag.rsplit('}',1)[-1]
def full_xml(data):
 t=ET.fromstring(data)
 assert local(t)=='VOTABLE' and t.attrib['version']=='1.4'
 status=[x.attrib['value'] for x in t.iter() if local(x)=='INFO' and x.attrib.get('name')=='QUERY_STATUS']
 assert status and all(s=='OK' for s in status),status
 tables=[x for x in t.iter() if local(x)=='TABLE'];assert len(tables)==1
 table=tables[0];fields=[x.attrib for x in table if local(x)=='FIELD']
 td=[x for x in table.iter() if local(x)=='TABLEDATA'];assert len(td)==1
 rows=list(td[0]);assert all(local(tr)=='TR' and len(tr)==len(fields) and all(local(c)=='TD' and len(c)==0 for c in tr) for tr in rows)
 return t,fields,rows,status
def scalar(kind,text):
 if text is None or text=='':return None
 if kind in ('long','int','short'):
  v=int(text);bits={'long':64,'int':32,'short':16}[kind];assert -(2**(bits-1))<=v<2**(bits-1);return v
 if kind=='boolean':
  assert text.lower() in ('t','f','true','false','1','0');return text.lower() in ('t','true','1')
 if kind=='float':return struct.unpack('>f',struct.pack('>f',float(text)))[0]
 if kind=='double':return float(text)
 if kind=='char':return text
 raise AssertionError(kind)
def cat(v):return 'ROW_NULL' if v is None else str(v)
def run():
 # Block every socket operation during validation, including imported candidate code.
 def forbidden(*a,**k):raise AssertionError('Network forbidden in review validation')
 socket.socket=forbidden;socket.create_connection=forbidden
 manifest=load(B/'MANIFEST.json');assert sha(B/'MANIFEST.json')==EXPECTED
 initial={n:sha(B/n) for n in manifest['files']}
 assert set(initial)=={str(p.relative_to(B)) for p in B.rglob('*') if p.is_file() and p.name not in manifest['inventory_excludes']}
 for n,meta in manifest['files'].items():assert initial[n]==meta['sha256'] and (B/n).stat().st_size==meta['bytes'],n
 receipt['checks']['candidate_inventory']={'sha256':EXPECTED,'sealed_files':len(initial),'all_match':True}
 contractpath=ROOT/'docs/research_program/observational_publication_20261015/ADAPTIVE_RESEARCH_20261023/R25-GAIA-SOURCE-PROPERTY-INTAKE_INPUT.json'
 contract=load(contractpath);cid='00508df7ec44ab6680ab8291868acaa203247aba18aaabfe2eaf029fc6ddad60'
 assert sha(contractpath)==sha(B/'inputs/contract.json')==cid
 npz=ROOT/contract['source_id_input']['path'];assert sha(npz)==contract['source_id_input']['sha256']
 with zipfile.ZipFile(npz) as z:
  array=np.load(io.BytesIO(z.read('source_id.npy')),allow_pickle=False)
 receipt['source_arrays_opened']=['source_id.npy']
 assert array.dtype==np.dtype('int64') and array.ndim==1
 ids=sorted(map(int,array));assert len(ids)==len(set(ids))==4756
 canonical=''.join(str(i)+'\n' for i in ids).encode('ascii')
 assert len(canonical)==94469 and hashlib.sha256(canonical).hexdigest()==contract['source_id_input']['canonical_ID_sha256']
 assert canonical==(B/'inputs/source_ids.txt').read_bytes()
 upload=ET.parse(B/'inputs/ids4756.xml').getroot();uf=[x for x in upload.iter() if local(x)=='FIELD'];assert len(uf)==1 and uf[0].attrib=={'name':'source_id','datatype':'long'}
 assert [int(x.text) for x in upload.iter() if local(x)=='TD']==ids
 receipt['checks']['source_identity']={'npz_sha256':sha(npz),'canonical_sha256':hashlib.sha256(canonical).hexdigest(),'count':4756,'upload_long_exact':True,'over_2pow53':sum(i>2**53 for i in ids)}
 trees={};raw=load(B/'RAW_RECEIPT.json');assert len(raw['requests'])==2
 for name,sqlkey in [('property','main_SQL'),('independent_count','independent_count_SQL')]:
  request=load(B/f'raw/{name}_request.json');params=request['params']
  assert request['endpoint']==contract['request']['endpoint'] and request['method']=='POST'
  assert params=={'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable_plain','MAXREC':'5000','UPLOAD':'ids4756,param:idsfile','QUERY':contract['request'][sqlkey]}
  assert request['upload_sha256']==sha(B/'inputs/ids4756.xml')
  assert request['connect_timeout']==10 and request['read_timeout']==45
  rec=[r for r in raw['requests'] if r['name']==name];assert len(rec)==1;rec=rec[0]
  assert rec['attempt']==1 and rec['http_status']==200 and rec['complete_http_body'] and not rec['redirects']
  p=B/f'raw/{name}_attempt1.vot';assert str(p)==rec['raw_path'] and sha(p)==rec['sha256'] and p.stat().st_size==rec['bytes']
  tree,fs,rows,status=full_xml(p.read_bytes());trees[name]=(tree,fs,rows,status)
  assert [x.attrib['value'] for x in tree.iter() if local(x)=='INFO' and x.attrib.get('name')=='QUERY']==[params['QUERY']]
  assert [x.attrib['value'] for x in tree.iter() if local(x)=='PARAM' and x.attrib.get('name')=='RELEASE']==['Gaia DR3']
 first=load(B/'raw/FIRST_PASS_RAW_RECEIPT.json')
 assert first['requests']==raw['requests']
 assert 0<raw['acquisition_elapsed_seconds']==first['elapsed_seconds']<600
 assert 0<raw['offline_validation']['preserved_acquisition_elapsed_seconds']==first['elapsed_seconds']
 request_elapsed=sum(r['elapsed_seconds'] for r in raw['requests']);assert request_elapsed<first['elapsed_seconds']
 wall=(datetime.datetime.fromisoformat(raw['ended_utc'])-datetime.datetime.fromisoformat(raw['started_utc'])).total_seconds();assert wall<600
 receipt['checks']['requests_accounting']={'successful_queries':2,'retries':0,'http_failures':0,'query_upload_and_returned_SQL_exact':True,'acquisition_seconds':first['elapsed_seconds'],'HTTP_elapsed_sum_seconds':request_elapsed,'original_start_to_offline_end_seconds':wall,'original_first_pass_preserved':True}
 tree,fields,wrows,status=trees['property'];assert len(wrows)==4756 and len(fields)==10
 expected={'retained_source_id':'long','qso_source_id':'long',**{k:v for k,v in contract['advisor_live_discovery']['columns'].items() if k!='source_id'}}
 assert {f['name']:f['datatype'] for f in fields}==expected
 assert all(f.get('unit') is None for f in fields)
 data=load(B/'products/property_table.json');rows=data['rows'];assert len(rows)==4756
 summary=load(B/'products/AVAILABILITY.json');masks=load(B/'products/property_wire_masks.json')
 astable=list(parse(io.BytesIO((B/'raw/property_attempt1.vot').read_bytes()),verify='exception').iter_tables())[0]
 for f in fields:
  name=f['name'];empties=[i for i,tr in enumerate(wrows) if tr[list(expected).index(name)].text in (None,'')]
  assert masks['wire_empty_TD_indices'][name]==empties
  assert masks['astropy_original_mask_indices'][name]==np.flatnonzero(np.ma.getmaskarray(astable.array[name])).tolist()
  vals=[None if np.ma.is_masked(v) else v.item() if isinstance(v,np.generic) else v for v in astable.array[name]]
  assert masks['astropy_original_values'][name]==vals
  assert data['fields'][name]=={'name':name,'datatype':f['datatype'],'arraysize':f.get('arraysize'),'unit':None}
 availability={f:collections.Counter() for f in expected if f not in ('retained_source_id','qso_source_id')}
 strata={f:collections.Counter() for f in ('host_flag','DSC','variability','selection_bit1')};cross={f:collections.Counter() for f in ('host_detected','transit_availability','module_selection_bits')};checked=0
 for sid,tr,row in zip(ids,wrows,rows):
  assert row['retained_source_id']==sid==row['qso_source_id']
  assert set(row)==set(expected)|{'field_states','strata'}
  for f,td in zip(fields,tr):
   name=f['name'];value=scalar(f['datatype'],td.text)
   assert value==row[name] and type(value)==type(row[name]),(sid,name,value,row[name]);checked+=1
   if name in availability:
    state='ROW_NULL' if value is None else 'PRESENT';assert row['field_states'][name]==state;availability[name][state]+=1
  flag=row['host_galaxy_flag'];host='ROW_NULL' if flag is None else str(flag) if flag in range(1,7) else 'UNEXPECTED_CODE'
  expectedstr={'host_flag':host,'DSC':cat(row['classlabel_dsc_joint']),'variability':cat(row['vari_best_class_name']),'selection_bit1':cat(None if row['source_selection_flags'] is None else bool(row['source_selection_flags']&1)),'future_host_comparison':'Host1-2' if host in ('1','2') else 'Host3' if host=='3' else 'EXCLUDED_FROM_PRIMARY_ONLY'}
  assert row['strata']==expectedstr
  for k in strata:strata[k][expectedstr[k]]+=1
  cross['host_detected'][(host,cat(row['host_galaxy_detected']))]+=1
  cross['transit_availability'][(host,row['field_states']['n_transits'])]+=1
  cross['module_selection_bits'][(host,cat(row['source_selection_flags']))]+=1
 for f,c in availability.items():
  assert summary['availability'][f]=={s:c[s] for s in ('FIELD_UNAVAILABLE','NO_QSO_ROW','ROW_NULL','PRESENT')}
  assert sum(c.values())==4756
 for h in contract['outcome_blind_strata']['host_flags']:strata['host_flag'][h]+=0
 assert summary['strata']=={k:dict(v) for k,v in strata.items()}
 assert summary['raw_crosstabs']=={k:[{'host_flag':h,'value':v,'count':n} for (h,v),n in sorted(c.items())] for k,c in cross.items()}
 assert summary['semantics']==contract['outcome_blind_strata']
 _,cfields,crows,_=trees['independent_count'];assert [(f['name'],f['datatype']) for f in cfields]==[('n_left','long'),('n_matched','long')]
 assert len(crows)==1 and [int(x.text) for x in crows[0]]==[4756,4756]
 assert summary['rows']==summary['matched_qso_rows']==4756 and summary['no_qso_row']==0
 assert summary['independent_count']=={'n_left':4756,'n_matched':4756}
 assert summary['future_primary_design']['host1_2']==0 and summary['future_primary_design']['host3']==3149 and summary['future_primary_design']['status']=='ZERO_EXPOSURE_SUPPORT'
 receipt['checks']['actual_consumer']={'cells':checked,'rows':len(rows),'all_values_types_states_masks_strata_and_crosstabs_equal_wire':True,'host_counts':dict(strata['host_flag']),'variability_counts':dict(strata['variability']),'field_null_counts':{k:v['ROW_NULL'] for k,v in availability.items()},'host1_2':0,'downstream_primary':'ZERO_EXPOSURE_SUPPORT'}
 # Import inspected code; replace its only write helper with an in-memory collector.
 spec=importlib.util.spec_from_file_location('candidate_acquire',B/'acquire.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 saved={};m.save=lambda name,obj:saved.__setitem__(name,obj)
 bad={k:(B/'raw/property_attempt1.vot').read_bytes().replace(b'</RESOURCE>',f'<INFO name="QUERY_STATUS" value="{k}"/></RESOURCE>'.encode()) for k in ('OVERFLOW','ERROR')}
 bad['TRUNCATED_XML']=(B/'raw/property_attempt1.vot').read_bytes()[:-20]
 falsifiers=[]
 for key,blob in bad.items():
  try:m.read_votable(blob,key)
  except Exception as e:falsifiers.append({'case':key,'rejected':True,'exception':type(e).__name__})
  else:raise AssertionError('Accepted '+key)
 fixture=(B/'raw/null_parser_fixture.vot').read_bytes();tab,_=m.read_votable(fixture,'review_fixture')
 assert m.scalar(tab.array,'sid',0)==9007199254740993
 assert m.scalar(tab.array,'label',0) is None and m.scalar(tab.array,'label',1)==' '
 assert m.scalar(tab.array,'flag',0) is False and m.scalar(tab.array,'score',0)==0.0 and m.scalar(tab.array,'score',1)==1.0
 assert str(tab.array['label'][1])=='' # reproduce original parser whitespace failure
 firstfailure=load(B/'raw/PARSER_FIRST_FAILURE.json');assert firstfailure['status']=='FAIL'
 receipt['checks']['parser_falsifiers']={'rejections':falsifiers,'exact_int64_whitespace_false_zero_endpoints':True,'original_astropy_whitespace_loss_reproduced':True,'author_first_failure_preserved':True,'astropy_empty_char_masked':bool(np.ma.is_masked(tab.array['label'][0])),'normalization_scope':'Wire null only; database NULL versus empty string not inferable'}
 # Execute existing real consumer without its __main__ writer.
 sp=importlib.util.spec_from_file_location('candidate_consumer',B/'validate_consumer.py');consumer=importlib.util.module_from_spec(sp);sp.loader.exec_module(consumer)
 actual=consumer.run();assert actual==load(B/'CONSUMER_VALIDATION.json')
 receipt['checks']['candidate_consumer_rerun']=actual
 assert sha(B/'MANIFEST.json')==EXPECTED
 assert all(sha(B/n)==v for n,v in initial.items())
 receipt['checks']['candidate_unchanged']=True
 receipt['status']='PASS'
try:run()
except BaseException as exc:
 receipt.update(status='FAIL',error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc());traceback.print_exc()
finally:
 receipt['elapsed_seconds']=time.monotonic()-start;receipt['resource_usage']={'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'user_seconds':resource.getrusage(resource.RUSAGE_SELF).ru_utime,'system_seconds':resource.getrusage(resource.RUSAGE_SELF).ru_stime}
 receipt['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();write('INDEPENDENT_CHECKS.json',receipt);print(json.dumps(receipt,indent=2))
if receipt['status']!='PASS':sys.exit(1)
