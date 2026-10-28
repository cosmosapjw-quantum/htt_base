from pathlib import Path
A=Path(__file__).resolve().parents[1];p=A/'assemble.py';s=p.read_text()
# One builder, separate explicit fixture representation, preserving existing payloads.
s=s.replace("dump(out/'NUMERICAL_SUPPLEMENT.json',{'fixture_only':True,'complete_cached_result':extracted,'complete_response':response,'figure_data':figdata})", "dump(out/'NUMERICAL_SUPPLEMENT.json',numerical_supplement({'payload':extracted,'response':response},fixture_only=True))")
pos=s.index('\ndef render_final_products(')
builder='''\ndef numerical_supplement(context,fixture_only=False):
 payload=context['payload'];response=context['response']
 if fixture_only:
  return {'fixture_only':True,'complete_cached_result':payload,'complete_response':response,'figure_data':{'survival':survival_data([r['T_abs_J234'] for r in payload['source_result']['mc_rows']]),'response':response_data(response)}}
 roles=context['index']['roles']
 return {'complete_cached_result':payload,'complete_mask_response':response,'raw_input_inventory':strict_json(context['paths'][roles['raw_input_inventory']]),'source_scope':strict_json(context['paths'][roles['source_scope_note']]),'source_candidate_identity':context['binding']['source_candidate_identity'],'source_export_index':context['index'],'all_original_source_receipts':{k:strict_json(context['paths'][k]) for k in roles['source_receipts'] if context['paths'][k].suffix=='.json'}}
'''
s=s[:pos]+builder+s[pos:]
old="roles=context['index']['roles'];dump(out/'NUMERICAL_SUPPLEMENT.json',{'complete_cached_result':context['payload'],'complete_mask_response':response,'raw_input_inventory':strict_json(context['paths'][roles['raw_input_inventory']]),'source_scope':strict_json(context['paths'][roles['source_scope_note']]),'source_candidate_identity':context['binding']['source_candidate_identity'],'source_export_index':context['index'],'all_original_source_receipts':{k:strict_json(context['paths'][k]) for k in roles['source_receipts'] if context['paths'][k].suffix=='.json'}})"
assert old in s;s=s.replace(old,"dump(out/'NUMERICAL_SUPPLEMENT.json',numerical_supplement(context))")
s=s.replace('def check_rendered_products(context,out,fixture_only=False):','def check_rendered_products(context,out,fixture_only=False,built=None):')
s=s.replace("result=context['payload']['source_result'];response=context['response'];rank=context['payload']['derived_rank']\n require((out/'generated/numbers.tex')", "result=context['payload']['source_result'];response=context['response'];rank=context['payload']['derived_rank']\n supplement=out/'NUMERICAL_SUPPLEMENT.json';require(supplement.is_file(),'missing complete numerical supplement')\n require(strict_json(supplement)==numerical_supplement(context,fixture_only),'complete lossless numerical supplement parity')\n require((out/'generated/numbers.tex')")
start=s.index(" if (out/'main.pdf').exists():",s.index('def check_rendered_products'));end=s.index('\ndef main():',start)
s=s[:start]+''' verify=(out/'main.pdf').exists() if built is None else built
 if verify:verify_current_pdf(context,out)
 return {'assembled_ready':True,'pdf_verification':'VERIFIED_CURRENT_BUILD' if verify else 'UNVERIFIED_PREBUILD'}
'''+s[end:]
pos=s.index('\ndef check_rendered_products')
verify=r'''
def verify_current_pdf(context,out):
 """Reuse latexmk's native consumed-input hashes; PDF metadata is not science."""
 pdf=out/'main.pdf';require(pdf.is_file(),'PDF_BUILD_UNVERIFIED: missing PDF')
 logpath=out/'main.log';dbpath=out/'main.fdb_latexmk';flspath=out/'main.fls'
 require(logpath.is_file() and dbpath.is_file() and flspath.is_file(),'PDF_BUILD_UNVERIFIED: missing native build/dependency evidence')
 log=logpath.read_text();require(not re.search(r'undefined references|Citation .* undefined|Reference .* undefined|LaTeX Error|Overfull \\hbox|Float too large',log),'PDF_BUILD_UNVERIFIED: current build diagnostics')
 require('Output written on main.pdf' in log,'PDF_BUILD_UNVERIFIED: no successful PDF output')
 db=dbpath.read_text();require(db.startswith('# Fdb version 4\n'),'PDF_BUILD_UNVERIFIED: unsupported latexmk dependency format')
 header=re.search(r'^\["pdflatex"\].*$',db,re.M);require(header is not None and header[0].split()[-1]=='0','PDF_BUILD_UNVERIFIED: no successful pdflatex rule')
 records={}
 for rel,size,digest in re.findall(r'^\s+"([^"\n]+)"\s+\S+\s+(\d+)\s+([a-f0-9]{32})\s+',db,re.M):records[(out/rel).resolve()]=(int(size),digest)
 inputs=['main.tex','generated/numbers.tex','generated/methods_table.tex','generated/results_table.tex','figures/morphology_survival.pdf','figures/mask_response_columns.pdf','references.bib']
 fls=flspath.read_text()
 for rel in inputs:
  p=out/rel;require(p.is_file(),'PDF_BUILD_UNVERIFIED: missing current input '+rel)
  record=records.get(p.resolve());require(record==(p.stat().st_size,hashlib.md5(p.read_bytes()).hexdigest()),'PDF_BUILD_UNVERIFIED: current input not consumed '+rel)
  # Bibliography is consumed by BibTeX, with its hash recorded in the same DB.
  if rel!='references.bib':require(any((out/line[6:]).resolve()==p.resolve() for line in fls.splitlines() if line.startswith('INPUT ')),'PDF_BUILD_UNVERIFIED: missing TeX input dependency '+rel)
 text=subprocess.run(['pdftotext','-layout',str(pdf),'-'],check=True,capture_output=True,text=True).stdout
 require('??' not in text,'PDF_BUILD_UNVERIFIED: unresolved PDF text');text=' '.join(text.split())
 number=r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
 patterns=[(r'observed value is\s+('+number+r'), with\s+(\d+)\s+inclusive exceedances', ['Tobs','K']), (r'empirical tail fraction is\s+('+number+r'), and the plus-one rank is\s+('+number+r')\.', ['Empirical','Rank']), (r'binomial interval is\s*\[\s*('+number+r'),\s*('+number+r')\s*\], with half-width\s+('+number+r')\.', ['CPlow','CPhigh','CPhalf'])]
 rank=context['payload']['derived_rank'];expected={'Tobs':context['payload']['source_result']['observed']['T_abs_J234'],'K':rank['inclusive_tail_count_k'],'Empirical':rank['empirical_tail_k_over_B'],'Rank':rank['p_rank'],'CPlow':rank['clopper_pearson_95'][0],'CPhigh':rank['clopper_pearson_95'][1],'CPhalf':rank['interval_half_width']}
 for pattern,keys in patterns:
  matches=list(re.finditer(pattern,text));require(len(matches)==1,'PDF_BUILD_UNVERIFIED: unique current numerical paragraph '+','.join(keys))
  for key,value in zip(keys,matches[0].groups()):require(float(value)==float(f'{expected[key]:.12g}'),'PDF_BUILD_UNVERIFIED: current numerical text '+key)
 return True
'''
s=s[:pos]+verify+s[pos:]
s=s.replace("p.add_argument('--check',action='store_true');a=p.parse_args()", "p.add_argument('--check',action='store_true');p.add_argument('--built-pdf',action='store_true',help='require a successful current PDF build');a=p.parse_args()")
s=s.replace('  check_rendered_products(context,HERE)','  result=check_rendered_products(context,HERE,built=True if a.built_pdf else None if a.check else False)\n  print(json.dumps(result))')
p.write_text(s)
