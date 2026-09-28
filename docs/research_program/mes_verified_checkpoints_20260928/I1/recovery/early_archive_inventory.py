from pathlib import Path
import zipfile,io,json,hashlib,gzip,collections
ROOT=Path(__file__).resolve().parent; P=ROOT/'early_selected';P.mkdir(exist_ok=True)
outer=ROOT.parent/'upload/HTT_MES_THREAD_BACKUP_20260928_02_EARLY_ARCHIVE.zip'
inventory=[];archives=[];extracted=[]; seen={}; errors=[]
want=('MES_78_THEOREM_PROOFS_20260830_1be8c03c0c/','MES_ALL_THEOREMS_ADJUDICATION_20260830/','MES_TENSOR_TILT_RESEARCH_20260830/','MES_TENSOR_TILT_CODING_20260830/')
readnames=('audit_v3/report-source.md','audit_v3/CLAIM_SOURCE_LEDGER.md','audit_v3/coverage.json','audit_v3/read_ledger_cumulative.json','recovered_audit_v2/HTT_INDEPENDENT_AUDIT_VOL2_KO_20260908.md')
def recurse(blob,locator,depth):
 h=hashlib.sha256(blob).hexdigest()
 if h in seen:
  archives.append({'locator':locator,'sha256':h,'duplicate_of':seen[h],'read_depth':'duplicate_archive_identity'});return
 seen[h]=locator
 with zipfile.ZipFile(io.BytesIO(blob)) as z:
  infos=z.infolist();archives.append({'locator':locator,'sha256':h,'bytes':len(blob),'members':len(infos),'expanded_bytes':sum(i.file_size for i in infos),'depth':depth})
  for i in infos:
   if i.is_dir():continue
   loc=locator+'!/'+i.filename
   row={'locator':loc,'path':i.filename,'bytes':i.file_size,'compressed_bytes':i.compress_size,'crc32':f'{i.CRC:08x}','archive_sha256':h,'read_depth':'zip_member_metadata'}
   inventory.append(row)
   # Only original already-expanded research docs; duplicated 03 expansions are pointers.
   select=(i.filename in readnames or ('/02_original_files/' in i.filename and any(w in i.filename for w in want))) and i.filename.endswith(('.md','.json','.py','.wl','.csv'))
   if select:
    b=z.read(i); dest=P/i.filename
    assert dest.resolve().is_relative_to(P.resolve());dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
    extracted.append({'locator':loc,'local_path':str(dest.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'read_depth':'materialized_not_yet_read','archive_sha256':h})
   if i.filename.lower().endswith('.zip'):
    if depth>=5 or i.file_size>600_000_000:
     errors.append({'locator':loc,'status':'recursion_size_or_depth_boundary'});continue
    try:recurse(z.read(i),loc,depth+1)
    except Exception as e:errors.append({'locator':loc,'status':'zip_read_error','error':str(e)})
recurse(outer.read_bytes(),outer.name,0)
with gzip.open(ROOT/'EARLY_ARCHIVE_MEMBER_INVENTORY.jsonl.gz','wt') as f:
 for d in inventory:f.write(json.dumps(d,ensure_ascii=False)+'\n')
(ROOT/'EARLY_ARCHIVE_COVERAGE.json').write_text(json.dumps({'archives':archives,'member_records':len(inventory),'selected_sources':extracted,'unread_archive_boundaries':errors,'science_revalidated':False,'full_transcript_recovered':False},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'archives':len(archives),'members':len(inventory),'selected':len(extracted),'unread_boundaries':len(errors)},ensure_ascii=False))
