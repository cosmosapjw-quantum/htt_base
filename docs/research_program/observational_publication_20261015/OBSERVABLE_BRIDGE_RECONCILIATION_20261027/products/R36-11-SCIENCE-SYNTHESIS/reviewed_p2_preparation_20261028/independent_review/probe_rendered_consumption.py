"""SYNTHETIC_UNIT_FIXTURE: generated artifact consumption checks only."""
import hashlib,json,pathlib,shutil,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'code'))
import assemble as a
import test_assemble as f
out=ROOT/'rendered_probe';out.mkdir(exist_ok=True)
(out/'.SYNTHETIC_UNIT_FIXTURE').write_text('Synthetic cached build exercise; no actual PR4 source result.\n')
result=f.synthetic_result();response=f.synthetic_response();prose=(ROOT/'code/MANUSCRIPT_ADDITIONS.md').read_text()
a.render_unit_fixture(result,response,prose,out)
shutil.copyfile(ROOT/'code/references.bib',out/'references.bib')
context={'payload':a.extract_cached_result(result,result['observed']),'response':response,'binding':{'source_candidate_identity':'SYNTHETIC_UNIT_FIXTURE_NOT_A_CANDIDATE','publication_export_sha256':'SYNTHETIC_UNIT_FIXTURE_NOT_AN_EXPORT','qualified_observed_replay_row_sha256':'SYNTHETIC_UNIT_FIXTURE_NOT_AN_OBSERVED_ROW'}}
a.dump(out/'NUMBER_FIGURE_MAP.json',a.map_for_products(context,out))
assert a.check_rendered_products(context,out)
summary={'fixture_only':'SYNTHETIC_UNIT_FIXTURE','actual_scientific_qualification':False,'initial_check':True}
supplement=out/'NUMERICAL_SUPPLEMENT.json';backup=supplement.read_bytes();supplement.unlink()
summary['missing_numerical_supplement_accepted']=a.check_rendered_products(context,out)
supplement.write_bytes(backup)
wrong=a.strict_json(supplement);wrong['complete_cached_result']['source_result']['observed'][a.FIELDS[1]]={};a.dump(supplement,wrong)
summary['lost_observed_B_coefficients_accepted']=a.check_rendered_products(context,out)
supplement.write_bytes(backup)
# Build the labelled synthetic fixture using real cached TeX tools.
p=subprocess.run(['latexmk','-g','-pdf','-interaction=nonstopmode','-halt-on-error','main.tex'],cwd=out,capture_output=True,text=True)
(ROOT/'synthetic_build_first.log').write_text(p.stdout+p.stderr)
summary['build_exit']=p.returncode
if p.returncode==0:
    assert a.check_rendered_products(context,out)
    prior_pdf_sha=a.sha(out/'main.pdf')
    oldtext=subprocess.run(['pdftotext','-layout',str(out/'main.pdf'),'-'],check=True,capture_output=True,text=True).stdout
    (ROOT/'synthetic_pdf_before.layout.txt').write_text(oldtext)
    # Change only observed threshold in a new synthetic source context, then reassemble
    # without rebuilding. Old PDF must not be treated as the new source's rendered PDF.
    result['observed']['features']['J234']=.6;result['observed']['T_abs_J234']=.6
    result['rank']=a.rank_summary(.6,[r['T_abs_J234'] for r in result['mc_rows']])
    a.render_unit_fixture(result,response,prose,out)
    context['payload']=a.extract_cached_result(result,result['observed'])
    a.dump(out/'NUMBER_FIGURE_MAP.json',a.map_for_products(context,out))
    summary['stale_pdf_after_source_update_accepted']=a.check_rendered_products(context,out)
    summary['pdf_unchanged_after_update']=a.sha(out/'main.pdf')==prior_pdf_sha
    summary['pdf_has_old_observed_threshold']=('0.2' in oldtext)
    summary['current_numbers_tex']=(out/'generated/numbers.tex').read_text()
    summary['old_Tobs']=.2;summary['new_Tobs']=.6
(ROOT/'RENDERED_CONSUMPTION_PROBE.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
