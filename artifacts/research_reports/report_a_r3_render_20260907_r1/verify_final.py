from runner import *
import re

def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def math(ast): return [(n['c'][0]['t'],n['c'][1]) for n in walk(ast) if n.get('t')=='Math']
def tokens(s):return re.findall(r'\\[A-Za-z]+|\\[^\r\n]|[^ \t\r\n]',s)
source=json.loads((E/'source-comparison-initial.json').read_text())
assert source['main_sections']==list(range(1,13))
assert source['appendices']==list('ABCD')
assert all(c['token_equal'] for c in source['display_math_comparison'])
assert sum(c['new_display_count'] for c in source['display_math_comparison'])==85
assert source['continuum_tables_equal'] and source['continuum_table_count']==1
assert all(c['exact_text_equal'] for c in source['k4_explicit_comparison'].values())
assert source['claim_count']==source['unique_claim_count']==40 and source['claim_ids_match']
assert source['bibliography_count']==source['unique_bibliography_count']==20
assert source['unresolved_citations']==source['unused_bibliography_keys']==source['unexpected_control_characters']==[]
for path,ident0 in source['input_identities'].items():assert ident((REPO/path).read_bytes())==ident0
raw=MAN.read_text(); appendix=raw[raw.index('# Appendix A'):raw.index('# Appendix B')]
relations=re.findall(r'\|[^|]+; (retained|revised|new) \|',appendix)
assert {x:relations.count(x) for x in set(relations)}=={'retained':26,'revised':4,'new':10}
a=math(json.loads((E/'r3.ast.json').read_text())); b=math(json.loads((E/'tex-final.ast.json').read_text()))
assert len(a)==244 and len(b)==246
assert all(x[0]==y[0] and tokens(x[1])==tokens(y[1]) for x,y in zip(a,b))
assert [x[1] for x in b[244:]]==['O(3)',r'\sin\Theta']
tex=(OUT/'HTT_REPORT_A_R3.tex').read_text(); body=tex.split(r'\begin{document}',1)[1]
sections_before,sections_after=body.split(r'\appendix')
assert len(re.findall(r'\\section\{',sections_before))==12
assert len(re.findall(r'\\section\{',sections_after))==4
assert len(re.findall(r'\\subsection\{',sections_after))==6
assert tex.count(r'\section*{References}')==1
assert not re.search(r'\\(?:sub)?section\{[A-D]\.\d',tex)
keys=re.findall(r'\\hypertarget\{ref-([^}]+)\}',tex)
assert len(keys)==len(set(keys))==20 and set(keys)==set(source['bibliography_keys'])
initial_math=math(json.loads((E/'tex.ast.json').read_text()))
assert initial_math==b
assert re.findall(r'RA-[A-Z]+-\d{3}',tex[tex.index(r'\section{Forty-claim'):tex.index(r'\section{Source and execution')])==source['appendix_a_claim_ids']
assert sum(n.get('t')=='Image' for n in walk(json.loads((E/'r3.ast.json').read_text())))==0
pandoc=json.loads((E/'pandoc-final.json').read_text()); assert all(x['verbosity']=='INFO' for x in pandoc)
log=(OUT/'HTT_REPORT_A_R3.log').read_text(); forbidden=[r'Overfull',r'Underfull',r'Missing character',r'undefined',r'^! ',r' multiply defined']
assert not any(re.search(p,log,re.M) for p in forbidden)
assert not any(re.search(r'\\'+name+r'\b',body) for name in ['overbracket','underbracket','dblcolon','coloneqq','Coloneqq','eqqcolon'])
pages=json.loads((E/'final-page-comparison.json').read_text())
assert len(pages['pages'])==29 and pages['changed_pages']==[10]
text=(E/'pdf-final-text.txt').read_text(); assert text.count('\f')==29
assert 'RATIO_UNIDENTIFIED' in text and 'RA-\nTIO_UNIDENTIFIED' not in text
assert 'revision 3' in text and 'canonical release' in text
assert all(c in text for c in ['B.1','B.2','B.3','D.1','D.2','D.3'])
assert len(re.findall(r'^References\s*$',text,re.M))==1
assert git('diff','--exit-code')==b''
result={'overall':'PASS_SOURCE_AND_RENDER_CORRESPONDENCE','source_unchanged':True,'bibliography_unchanged':True,'display_math_tokens_equal':85,'all_source_math_nodes_preserved_in_order':244,'generated_math_nodes':246,'extra_math_nodes_from_bibliography':['O(3)',r'\sin\Theta'],'math_unchanged_by_layout_repair':True,'main_sections':12,'appendices':['A','B','C','D'],'appendix_subsections':['B.1','B.2','B.3','D.1','D.2','D.3'],'unique_unnumbered_references_heading':1,'core_claim_ids':40,'relations_to_canonical':{'retained':26,'revised':4,'new':10},'canonical_identity_total_including_revised':30,'bib_keys_and_cited_keys':20,'rendered_bibliography_keys':keys,'unresolved_citations':0,'figures_in_source':0,'missing_figure_assets':0,'continuum_table_exact':True,'k4_sections_exact':['5.1','8.2','11.2'],'source_controls':0,'pdf_pages':29,'final_changed_page':10,'unchanged_final_pages_pixel_identical_to_visually_reviewed_images':28,'pandoc_warnings':0,'tex_overfull_underfull_missing_glyph_undefined_or_duplicate_errors':0,'warnings':[{'kind':'unicode-math/mathtools definitions','count':2,'judgement':'Harmless for this body: affected bracket/colon macros absent.'},{'kind':'rsfs font-size substitution','count':1,'summary_warning':True,'judgement':'5.475pt requests use 5pt; script symbols legible on reviewed pages, no missing glyphs.'}],'rendered_source':ident(MAN.read_bytes()),'bibliography':ident(BIB.read_bytes()),'pdf':ident((OUT/'HTT_REPORT_A_R3.pdf').read_bytes()),'tex':ident((OUT/'HTT_REPORT_A_R3.tex').read_bytes())}
write('final-verification.json',result)
print(json.dumps(result,indent=2))
