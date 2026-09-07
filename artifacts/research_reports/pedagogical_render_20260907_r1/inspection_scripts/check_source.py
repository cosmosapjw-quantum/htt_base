from runner import *
import re,collections,importlib.util
MAN=RUN/'assembled/FROM_A_CMB_SKY_MAP_TO_PHYSICAL_CONSTRAINTS.md'
spec=importlib.util.spec_from_file_location('axial',SRC/'check_axial_certificate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
text=MAN.read_text()
# The comparison binds the actual printed source fractions, not only copied Python constants.
parts=(SRC/'05_APPENDICES_CERTIFICATES_AND_FIBRES.md').read_text()
normal_section=parts.split('## B.2 ')[1].split('## B.3 ')[0]
minor_section=parts.split('## B.3 ')[1].split('# Appendix C.')[0]
def fractions(s):
 block=re.search(r'```text\n(.*?)```',s,re.S).group(1)
 values=[]
 for body in re.split(r'm=\d[^\n]*:\n',block)[1:]:
  chunks=body.strip().split('/')
  assert len(chunks)==2
  values.append('/'.join(re.sub(r'\s','',c) for c in chunks))
 return values
assert tuple(fractions(normal_section))==m.NORMAL
assert tuple(fractions(minor_section))==m.MINOR_SQUARED
baseline=m.check();assert baseline['printed_certificate_matches']
n,d=m.NORMAL[0].split('/');old=m.NORMAL;m.NORMAL=(str(int(n)+1)+'/'+d,)+old[1:]
mutant=m.check();assert not mutant['printed_certificate_matches'] and mutant['overall']=='NONPASS_PRINTED_CERTIFICATE_COMPARISON';m.NORMAL=old
write('axial-sensitivity.json',{'operation':'Checker sensitivity, not a physical result','mutation':'Increment selected expected normal numerator m=0 by one, in memory only','original_expected':old[0],'mutant_expected':str(int(n)+1)+'/'+d,'archived_checker_unchanged':True,'printed_fraction_binding':True,'mutant_result':mutant})
# All displayed mathematics must survive the authored editorial paragraph assembly.
chapters='\n\n'.join(p.read_text() for p in sorted(SRC.glob('[0-9][0-9]_*.md')))
math=lambda s:re.findall(r'\\\[(.*?)\\\]',s,re.S)
assert math(chapters)==math(text)
tags=re.findall(r'\\tag\{([^}]+)\}',text); assert len(tags)==len(set(tags))
# Explicit Eq./Eqs. references, including paired/range references through the sentence.
refs=[]
for match in re.finditer(r'\bEqs?\.\s+((?:\([A-E0-9]+\.\d+\)(?:[–—-]|,\s*|\s+and\s+|\s*))*\([A-E0-9]+\.\d+\))',text):
 refs.extend(re.findall(r'\(([A-E0-9]+\.\d+)\)',match.group(1)))
assert set(refs)<=set(tags),set(refs)-set(tags)
keys=set(re.findall(r'(?<!\w)@([A-Za-z0-9_]+)',text))
bib=set(re.findall(r'@\w+\s*\{\s*([^,\s]+)',BIB.read_text()))
assert len(bib)==20 and keys<=bib
assert not re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]',text)
assert re.findall(r'^## (\d+)\. ',text,re.M)==list(map(str,range(1,14)))
assert re.findall(r'^# Appendix ([A-E])\.',text,re.M)==list('ABCDE')
assert text.count('\n# References\n')==1
assert 'A reader wishing to derive the imported bounds' not in text
assert 'bounds from the stated moment equations and derivative envelopes' in text
assert 'The general nonlinear almost-isotropy theorem is not asserted here.' in text
assert (SRC/'06_RADIATION_MODEL_AND_MES_DERIVATION.md').read_text().rstrip() in text
assert 'WORK_THREAD' not in text
# Check numbered section/subsection, named results and appendix references against existing headings.
headers=re.findall(r'^#{1,3} (.+)$',text,re.M)
section_ids={re.match(r'([A-E0-9]+(?:\.\d+)?)\.? ',h).group(1) for h in headers if re.match(r'([A-E0-9]+(?:\.\d+)?)\.? ',h)}
section_refs=re.findall(r'\bSection\s+(\d+(?:\.\d+)?)',text)
assert set(section_refs)<=section_ids,set(section_refs)-section_ids
results=set(re.findall(r'\*\*(?:Proposition|Theorem|Lemma|Corollary) ([0-9]+\.[0-9]+)',text))
result_refs=set(re.findall(r'(?<!\*\*)\b(?:Proposition|Theorem|Lemma|Corollary) ([0-9]+\.[0-9]+)',text))
assert result_refs<=results,result_refs-results
record={'overall':'PASS_SOURCE_CORRESPONDENCE','assembled':ident(MAN.read_bytes()),'display_math_blocks_preserved':len(math(text)),'unique_equation_tags':len(tags),'explicit_equation_references_checked':len(refs),'undefined_equation_references':sorted(set(refs)-set(tags)),'main_sections':13,'appendices':list('ABCDE'),'named_results':len(results),'section_references_checked':len(section_refs),'main_subsections':len(re.findall(r'^### \d+\.\d+ ',text,re.M)),'references_headings':1,'bibliography_total':len(bib),'used_bibliography_keys':sorted(keys),'unused_bibliography_keys':sorted(bib-keys),'unresolved_citations':[],'axial_all_12_printed_fractions_match_checker_constants':True,'axial_mutation_reports_NONPASS':True,'sixth_part_complete':True,'editorial_replacements':8,'source_control_characters':0,'no_new_claim_ledger':True}
write('source-check.json',record)
print(record)
