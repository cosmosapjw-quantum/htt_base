from runner import *
import csv, io, re, difflib
pins={str(MAN.relative_to(REPO)):'e8566be7c8095c38befdbbdbe7851f9502510753',str(BIB.relative_to(REPO)):'331c557c0f6a7de84fdd97123d8bdb8fae0e0a53',str(OLD.relative_to(REPO)):'99a3f75c67ece3cfb00179bfd61787f47cb7e7ac','docs/research_reports/report_a/structure.lua':'afaf143126319a864b7f08790348db20963d55d2','docs/research_reports/report_a/header.tex':'21102ea9ae0a117fc921189884916226c13d5aae'}
for path,blob in pins.items(): assert ident(git('show',BASE+':'+path))['git_blob']==blob
sectionraw=git('show','581d50cb8b8be61ca8ead538d0bf7d75420f9037:artifacts/research_reports/k2fr_20260905/authority-bundle/REPORT_SECTION_CLAIM_MAP_V3.csv')
assert ident(sectionraw)['git_blob']=='1478f55c074ec0aeb62a8680a5e7fc76849b89c4'
(E/'fixed-section-map.csv').write_bytes(sectionraw)
fixedbib=git('show','581d50cb8b8be61ca8ead538d0bf7d75420f9037:artifacts/research_reports/k2fr_20260905/authority-bundle/HTT_REPORT_A_REFERENCES_V2.bib')
assert BIB.read_bytes()==fixedbib
for label,p in [('r3',MAN),('r2',OLD)]:run('parse-'+label,[PANDOC,p,'--from='+FMT,'--to=json','--output='+str(E/(label+'.ast.json'))])
run('parse-bibliography',[PANDOC,BIB,'--from=biblatex','--to=csljson','--output='+str(E/'bibliography.json')])
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values(): yield from walk(v)
 elif isinstance(x,list):
  for v in x: yield from walk(v)
def text(x):
 return ''.join(n['c'] if n['t'] in ('Str','Code') and isinstance(n.get('c'),str) else ' ' if n['t']=='Space' else '' for n in walk(x) if 't' in n)
def sections(ast):
 output={}; current=None
 for b in ast['blocks']:
  if b['t']=='Header':
   label=text(b['c'][2])
   match=re.match(r'^(\d+)\. ',label)
   if b['c'][0]==2 and match: current=int(match[1]); output[current]=[]
   elif label.startswith('Appendix '): current=None
  if current is not None:output[current].append(b)
 return output
def math(blocks,display=True):return [n['c'][1] for n in walk(blocks) if n.get('t')=='Math' and (not display or n['c'][0]['t']=='DisplayMath')]
def tokens(s): return re.findall(r'\\[A-Za-z]+|\\[^\r\n]|[^ \t\r\n]',s)
a=json.loads((E/'r2.ast.json').read_text()); b=json.loads((E/'r3.ast.json').read_text()); sa,sb=sections(a),sections(b)
comparison=[]
for key in sorted(sa):
 old,new=math(sa[key]),math(sb[key]); diffs=[]
 for i in range(max(len(old),len(new))):
  if i>=len(old) or i>=len(new) or tokens(old[i])!=tokens(new[i]):diffs.append({'index':i,'before':old[i] if i<len(old) else None,'after':new[i] if i<len(new) else None})
 comparison.append({'section':key,'old_display_count':len(old),'new_display_count':len(new),'token_equal':not diffs,'differences':diffs})
raw=MAN.read_text(); previous=OLD.read_text()
controls=[{'offset':i,'codepoint':ord(c)} for i,c in enumerate(raw) if ord(c)<32 and c not in '\t\r\n']
appendix=raw[raw.index('# Appendix A'):raw.index('# Appendix B')]
ids=re.findall(r'`(RA-[A-Z]+-\d{3})`',appendix)
rows=list(csv.DictReader(io.StringIO(sectionraw.decode()))); key=next(k for k in rows[0] if k.lower()=='claim_id'); fixedids=[r[key] for r in rows]
bib=json.loads((E/'bibliography.json').read_text()); bibkeys=[r['id'] for r in bib]
citations=sorted({c['citationId'] for n in walk(b) if n.get('t')=='Cite' for c in n['c'][0]})
def chunk(s,h):
 start=s.index('### '+h+' '); match=re.search(r'^#{1,3} ',s[start+4:],re.M); end=start+4+match.start() if match else len(s); return s[start:end]
k4={h:{'exact_text_equal':chunk(raw,h)==chunk(previous,h),'ascii_whitespace_only_equal':re.sub('[ \t\r\n]','',chunk(raw,h))==re.sub('[ \t\r\n]','',chunk(previous,h))} for h in ['5.1','8.2','11.2']}
tablesa=[n for n in walk(sa[10]) if n.get('t')=='Table']; tablesb=[n for n in walk(sb[10]) if n.get('t')=='Table']
result={'source_snapshot':BASE,'source_snapshot_tree':git('rev-parse',BASE+'^{tree}').decode().strip(),'input_identities':{p:ident((REPO/p).read_bytes()) for p in pins},'section_map':ident(sectionraw),'bibliography_matches_fixed_copy':True,'main_sections':sorted(sb),'appendices':re.findall(r'^# Appendix ([A-D])\.',raw,re.M),'display_math_comparison':comparison,'unexpected_control_characters':controls,'appendix_a_claim_ids':ids,'claim_count':len(ids),'unique_claim_count':len(set(ids)),'fixed_claim_count':len(fixedids),'claim_ids_match':set(ids)==set(fixedids),'bibliography_keys':bibkeys,'bibliography_count':len(bibkeys),'unique_bibliography_count':len(set(bibkeys)),'citation_keys':citations,'unresolved_citations':sorted(set(citations)-set(bibkeys)),'unused_bibliography_keys':sorted(set(bibkeys)-set(citations)),'continuum_tables_equal':tablesa==tablesb,'continuum_table_count':len(tablesb),'k4_explicit_comparison':k4}
write('source-comparison-initial.json',result)
(E/'r2-to-r3.patch').write_text(''.join(difflib.unified_diff(previous.splitlines(True),raw.splitlines(True),fromfile=str(OLD.relative_to(REPO)),tofile=str(MAN.relative_to(REPO)))))
print(json.dumps({k:v for k,v in result.items() if k not in ('input_identities','appendix_a_claim_ids','bibliography_keys','citation_keys')},indent=2))
