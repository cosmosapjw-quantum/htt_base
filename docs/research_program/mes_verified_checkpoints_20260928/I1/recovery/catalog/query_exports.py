"""Search preserved catalog excerpts or paths without the 10 GiB source DB."""
import argparse,gzip,json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('query')
p.add_argument('--topic',choices=['CF4','CMB_product_law','full_QO_morphology','MES_departure','local_global','JWST_calibration','DESI_Union3','Teff_error'])
p.add_argument('--limit',type=int,default=20)
p.add_argument('--exports',type=Path,default=Path(__file__).resolve().parent/'exports')
a=p.parse_args()
name='topic_'+a.topic if a.topic else 'files'
terms=a.query.casefold().split();shown=0
with gzip.open(a.exports/(name+'.jsonl.gz'),'rt',encoding='utf-8') as f:
    for line in f:
        d=json.loads(line)
        hay=' '.join(str(d.get(k,'')) for k in ('path','name','summary','recorded_status','source_id')).casefold()
        if not all(t in hay for t in terms):continue
        keys=('id','file_id','source_id','path','observed_commit','git_blob','bytes','kind','name','status','recorded_status','baseline_membership','line','end_line')
        print(json.dumps({k:d[k] for k in keys if k in d},ensure_ascii=False))
        shown+=1
        if shown>=a.limit:break
