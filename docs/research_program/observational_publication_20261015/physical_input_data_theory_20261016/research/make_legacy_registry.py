"""Generate evidence inventory from attached original archives, no extraction or mutation."""
from pathlib import Path
import zipfile,hashlib,json,datetime,os
ROOT=Path(os.environ.get('HTT_LEGACY_ARCHIVE_DIR','/mnt/data'))
ARCHIVES=[
 ('legacy_code_data','code_data_package(20261016-135512).zip',['README.md','ssot.py','bounds.py','teff_extended.py','analysis_extended.py','tilted_flrw.py']),
 ('legacy_manuscript','manuscript_source.zip',['abstract.tex','ch02_framework.tex','ch03_bianchi_bounds.tex','ch04_dipole.tex','ch05_teff.tex','ch07_results.tex']),
 ('legacy_htt_module','HTT(20261016-135543).zip',['HTT/README.md','HTT/htt/catalog_likelihood.py','HTT/docs/IS22_hostile_review.md']),
 ('legacy_overleaf','bianchi_defect_overleaf(20261016-135541).zip',['overleaf/chapters/ch02_sec7_tilted_kinematics.tex','overleaf/chapters/ch05_teff.tex','overleaf/abstract.tex']),
 ('legacy_bass_repair','BASS_HOSTILE_REPAIR_DAG_FINAL_20260820(1).zip',['BASS_HOSTILE_REPAIR_DAG_FINAL_20260820/audits/reports/PHYSICAL_KINETIC_HOSTILE_REVIEW.md','BASS_HOSTILE_REPAIR_DAG_FINAL_20260820/audits/reports/TASK2_MATH_COUNTEREXAMPLES_01954131.md'])
]
def digest_bytes(b):return hashlib.sha256(b).hexdigest()
def main():
    o={'schema':'htt.legacy_archival_source_identity/1','date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'scope':'legacy sources are scientific materials; neither execution nor physical truth follows from hashes','archives':[]}
    for key,name,targets in ARCHIVES:
        p=ROOT/name;entry={'id':key,'name':name,'bytes':p.stat().st_size,'sha256':digest_bytes(p.read_bytes()),'selected':[]}
        with zipfile.ZipFile(p) as z:
            entry['zip_member_count']=len(z.infolist())
            entry['total_uncompressed_bytes']=sum(i.file_size for i in z.infolist())
            for path in targets:
                if path in z.namelist():
                    b=z.read(path)
                    entry['selected'].append({'path':path,'bytes':len(b),'sha256':digest_bytes(b)})
                else:entry['selected'].append({'path':path,'status':'NOT_FOUND_NO_IMPUTATION'})
        o['archives'].append(entry)
    dest=Path(__file__).parent/'LEGACY_SOURCE_IDENTITIES.json'
    dest.write_text(json.dumps(o,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
    print('Inventory:',len(o['archives']),'archives,',sum(len(a['selected']) for a in o['archives']),'selected members',dest)
if __name__=='__main__':main()
