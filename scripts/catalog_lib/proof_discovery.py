"""Static full-source supplement to the catalog's sometimes clipped excerpts.

Run with ``PYTHONPATH=scripts python -m catalog_lib.proof_discovery --db ...
--output ...``. This preparation step reads existing bytes; export only reads
its saved result. It does not import, compile or execute research/proof code.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

from .db import connect, identity, js
from .proofs import PROOF_WORDS, PROPOSAL_WORDS, write_json
from .proof_sources import SourceReader


def uncovered_hits(text, content_id, parsed):
    """Retain uncovered keyword windows, including long/minified source lines.

    Only suppress a hit when its exact surrounding line/window already occurs
    in an extracted record, never merely because its enclosing section exists.
    The proposed flag only routes to *unconfirmed*; it cannot confirm a proof.
    """
    existing = [js(r) for r in parsed.get('records',[])]
    for lineno, line in enumerate(text.splitlines(),1):
        matches = list(PROOF_WORDS.finditer(line))
        windows=[]
        for match in matches:
            lo=max(0,match.start()-300); hi=min(len(line),match.end()+1300)
            if windows and lo<=windows[-1][1]: windows[-1][1]=max(windows[-1][1],hi)
            else: windows.append([lo,hi])
        for lo,hi in windows:
            excerpt=line[lo:hi].strip()
            if not excerpt or any(excerpt in r or json.dumps(excerpt,ensure_ascii=False)[1:-1] in r for r in existing):
                continue
            is_proposal=bool(PROPOSAL_WORDS.search(excerpt) or re.search(r'\b(theorem|lemma|proposition|corollary)\b|정리|명제',excerpt,re.I))
            yield {'candidate_id':identity('raw-proof-v1',content_id,lineno,lo,hi),
                'content_id':content_id,'line':lineno,'locator':f'line {lineno}, characters {lo+1}-{hi}',
                'text':excerpt,'title':excerpt[:180], 'is_proposal':is_proposal,
                'excerpt_truncated':lo!=0 or hi!=len(line)}


def prepare(c, directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    reader=SourceReader(c)
    counts=Counter();candidates=[]
    columns=['content_id','language','bytes','file_occurrences','selected_file_id','processing_status','candidate_windows','errors']
    with (directory/'source_scan.csv').open('w',newline='') as output:
        writer=csv.DictWriter(output,fieldnames=columns,lineterminator='\n');writer.writeheader()
        for n, raw in enumerate(c.execute('SELECT id,language,bytes,parsed FROM contents ORDER BY id'),1):
            content=dict(raw);cid=content['id']
            files=list(c.execute('SELECT id,git_blob,container_id FROM files WHERE content_id=? ORDER BY git_blob IS NULL, container_id IS NOT NULL,id',(cid,)))
            row=dict(content_id=cid,language=content['language'],bytes=content['bytes'],file_occurrences=len(files),selected_file_id='',processing_status='',candidate_windows=0,errors=[])
            data=None
            if content['language']=='binary_or_unclassified':
                row['processing_status']='unsupported_binary'
            else:
                for f in files:
                    try:
                        data=reader.read(f['id']);row['selected_file_id']=f['id'];break
                    except (OSError,ValueError,KeyError,subprocess.SubprocessError,EOFError) as exc:
                        row['errors'].append({'file_id':f['id'],'error':str(exc)[:500]})
                if data is None:row['processing_status']='source_unavailable_or_changed'
            if data is not None:
                if content['language']=='pdf':
                    if not shutil.which('pdftotext'):
                        row['processing_status']='pdf_extractor_unavailable';text=None
                    else:
                        try:
                            p=subprocess.run(['pdftotext','-layout','-','-'],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
                            text=p.stdout.decode('utf-8') if p.returncode==0 else None
                            row['processing_status']='pdf_text_only' if text is not None else 'pdf_text_error'
                        except (subprocess.TimeoutExpired,UnicodeError):
                            text=None;row['processing_status']='pdf_text_error'
                else:
                    try:text=data.decode('utf-8-sig');row['processing_status']='read_exact_utf8'
                    except UnicodeError:text=data.decode('latin1');row['processing_status']='read_exact_latin1_fallback'
                if text is not None:
                    found=list(uncovered_hits(text,cid,json.loads(content['parsed'])))
                    candidates.extend(found);row['candidate_windows']=len(found)
            counts[row['processing_status']]+=1;counts['content_versions']+=1
            counts['file_occurrences']+=len(files);counts['candidate_windows']+=row['candidate_windows']
            row['errors']=js(row['errors']);writer.writerow(row)
            reader.cache.clear()
            if n%1000==0:print(js({'contents_processed':n,'candidate_windows':len(candidates)}),flush=True)
    result={'schema_version':1,'summary':dict(sorted(counts.items())),
        'method':'Exact existing source bytes; line keyword windows beyond catalog excerpts; PDF extracted text only, no equation/visual audit; unavailable bytes retained in source_scan.csv',
        'candidates':candidates}
    write_json(directory/'source_discovery.json',result)
    return result['summary']


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    with connect(args.db,readonly=True) as c:print(js(prepare(c,args.output)))
