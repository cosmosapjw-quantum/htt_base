#!/usr/bin/env python3
"""Check report/index/rendered-text integrity only; never import research code."""
from pathlib import Path
import argparse,collections,csv,hashlib,json,re,subprocess
BASE=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-git',action='store_true');args=parser.parse_args()
    md=(BASE/'REPORT.md').read_text();sources=list(csv.DictReader((BASE/'sources.csv').open()));coverage=json.loads((BASE/'COVERAGE_INDEX.json').read_text());proposals=json.loads((BASE/'PROPOSAL_INDEX.json').read_text());summary=json.loads((BASE/'inventory_summary.json').read_text())
    headings=[int(x) for x in re.findall(r'(?m)^## (\d+)\.',md)];assert headings==list(range(1,29)),headings
    anchors=re.findall(r'<a id="(s\d+)">',md);assert len(set(anchors))==len(anchors)==28
    ids={r['source_id'] for r in sources};assert set(re.findall(r'\bS\d{2}\b',md))<=ids
    assert len(sources)==summary['sources']==55
    assert len(coverage)==summary['coverage_rows']==466
    assert dict(collections.Counter(r['group'] for r in coverage))==summary['counts']
    assert len({(r['group'],r['record_id']) for r in coverage})==len(coverage)
    assert proposals==[r for r in coverage if r['group']=='historical_proposal'] and len(proposals)==172
    assert all(r['original_record'] and r['path'] and r['disposition'] for r in coverage)
    for name,records in [('COVERAGE_INDEX.csv',coverage),('PROPOSAL_INDEX.csv',proposals)]:
        csvrows=list(csv.DictReader((BASE/name).open()));assert len(csvrows)==len(records)
        for a,b in zip(csvrows,records):assert a['record_id']==b['record_id'] and json.loads(a['original_record'])==b['original_record']
    for name in ['SOURCES.md','COVERAGE_INDEX.md','PROPOSAL_INDEX.md','README.md']:
        for url in re.findall(r'\]\(([^)]+)\)',(BASE/name).read_text()):
            if '://' in url:continue
            path,_,frag=url.partition('#');target=(BASE/path).resolve() if path else BASE/name
            assert target.exists(),(name,url)
            if frag.startswith('s') and frag[1:].isdigit():assert f'id="{frag}"' in target.read_text(),url
    if args.verify_git:
        repo=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=BASE,text=True).strip())
        for r in sources:
            b=subprocess.check_output(['git','show',r['commit']+':'+r['path']],cwd=repo)
            assert hashlib.sha256(b).hexdigest()==r['sha256'],r['source_id']
    tex0=(BASE/'report.tex').read_bytes();subprocess.run(['python3','-B',str(BASE/'build_report.py'),'--tex-only'],check=True);assert (BASE/'report.tex').read_bytes()==tex0
    pdftext=subprocess.check_output(['pdftotext','-layout',str(BASE/'report.pdf'),'-'],text=True)
    info=subprocess.check_output(['pdfinfo',str(BASE/'report.pdf')],text=True);pages=int(re.search(r'Pages:\s+(\d+)',info).group(1))
    assert pages>=28 and len(pdftext.split('\f'))-1==pages
    normalized=re.sub(r'\s+','',pdftext)
    for term in ['tensorized','local','global','공동','운동학','수축','교차','source-normalization']:
        assert term in normalized,term
    assert not '\ufffd' in pdftext
    log=BASE/'.build/report.log';warnings=[]
    if log.exists():
        txt=log.read_text();bad=re.findall(r'.*(?:Overfull|Missing character|undefined|LaTeX Error|Duplicate|already defined).*',txt);assert not bad,bad
        warnings=re.findall(r'.*(?:Warning|Underfull).*',txt)
    result={'status':'PASS','scope':'report packaging, index and static source identities only','pages':pages,'sources':len(sources),'coverage_rows':len(coverage),'proposals':len(proposals),'git_source_check':args.verify_git,'deterministic_tex':True,'warnings':warnings,'research_execution':False,'files':{n:hashlib.sha256((BASE/n).read_bytes()).hexdigest() for n in ['REPORT.md','report.tex','report.pdf','sources.csv','COVERAGE_INDEX.json','PROPOSAL_INDEX.json']}}
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
