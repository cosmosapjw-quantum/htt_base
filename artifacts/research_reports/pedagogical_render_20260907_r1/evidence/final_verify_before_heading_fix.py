from runner import *
import re, collections, importlib.util

def nodes(x, typ):
    if isinstance(x, dict):
        if x.get('t') == typ:
            yield x['c']
        for v in x.values():
            yield from nodes(v, typ)
    elif isinstance(x, list):
        for v in x:
            yield from nodes(v, typ)

md = (RUN/'assembled-final/FROM_A_CMB_SKY_MAP_TO_PHYSICAL_CONSTRAINTS.md').read_text()
tex = (OUT/'FROM_A_CMB_SKY_MAP_TO_PHYSICAL_CONSTRAINTS.tex').read_text()
pdf = OUT/'FROM_A_CMB_SKY_MAP_TO_PHYSICAL_CONSTRAINTS.pdf'
toc = pdf.with_suffix('.toc').read_text()
log = pdf.with_suffix('.log').read_text()
text = (E/'pdf-stf.txt').read_text()
pages = text.split('\f')
assert not pages[-1].strip()
pages.pop()
assert len(pages) == 55
clean_pages = []
for i, page in enumerate(pages, 1):
    lines = page.rstrip().splitlines()
    assert lines[-1].strip() == str(i), (i, lines[-1])
    clean_pages.append('\n'.join(lines[:-1]))
clean = '\n'.join(clean_pages)
src_ast = json.loads((E/'source-ast.json').read_text())
tex_ast = json.loads((E/'tex-ast-stf.json').read_text())
normal = lambda s: re.sub(r'\s+', '', s)
src_math = [normal(x[1]) for x in nodes(src_ast, 'Math')]
out_math = [normal(x[1]) for x in nodes(tex_ast, 'Math')]
assert out_math[:len(src_math)] == src_math
assert len(src_math) == 931 and len(out_math) == 933
assert out_math[-2:] == ['O(3)', r'\sin\Theta']
tags = re.findall(r'\\tag\{([^}]+)\}', md)
assert tags == re.findall(r'\\tag\{([^}]+)\}', tex)
assert len(tags) == len(set(tags)) == 147
assert all('('+t+')' in clean for t in tags)
refs = []
for x in re.finditer(r'\b(?:Eqs?\.|Equations?)\s+((?:\([A-E0-9]+\.\d+\)(?:[–—-]|,\s*|\s+and\s+|\s*))*\([A-E0-9]+\.\d+\))', md):
    refs.extend(re.findall(r'\(([A-E0-9]+\.\d+)\)', x.group(1)))
assert set(refs) <= set(tags)
raw_html = [x[1] for x in nodes(src_ast, 'RawInline') if x[0] == 'html']
assert raw_html == ['<a e_b>', '<a q_b>']
assert all(s in clean_pages[49] for s in raw_html)
assert all(s.replace('_', r'\_').replace('<', r'\textless ').replace('>', r'\textgreater{}') in tex for s in raw_html)
keys = set(re.findall(r'(?<!\w)@([A-Za-z0-9_]+)', md))
targets = re.findall(r'\\hypertarget\{ref-([^}]+)\}', tex)
assert len(targets) == len(set(targets)) == 20 and keys == set(targets)

# Reconstruct the twelve printed rational numbers from the actual PDF, removing
# only identified page footers, whitespace and the explicit continuation note.
spec=importlib.util.spec_from_file_location('axial', SRC/'check_axial_certificate.py')
axial=importlib.util.module_from_spec(spec);spec.loader.exec_module(axial)
block='\n'.join(clean_pages[41:43])
normal_block=block.split('m=0:',1)[1].split('B.3',1)[0]
minor_block=re.split(r'm=0[^\n]*:\s*',block.split('B.3',1)[1],maxsplit=1)[1]
def ratios(s):
    values=[]
    for body in re.split(r'm=\d[^\n]*:\s*',s):
        match=re.match(r'\s*([0-9\s]+)\s*/\s*([0-9\s]+)', body)
        assert match, body[:100]
        values.append(normal(match[1])+'/'+normal(match[2]))
    return values
normal_values=ratios(normal_block)
minor_values=ratios(minor_block)
assert tuple(normal_values)==axial.NORMAL
assert tuple(minor_values)==axial.MINOR_SQUARED

part_entries=re.findall(r'\\contentsline \{part\}.*?\}\{(\d+)\}\{part\.(\d+)\}',toc)
assert part_entries==[(str(p),str(i)) for i,p in enumerate([6,13,17,23,28,31,37],1)]
for numeral,p in zip(['I','II','III','IV','V','VI','VII'],[6,13,17,23,28,31,37]):
    assert 'Part '+numeral in clean_pages[p-1]
assert r'\contentsline {section}{Abstract}{4}{section*.1}' in toc
assert r'\contentsline {section}{How to read this report}{5}{section*.2}' in toc
assert r'\contentsline {section}{References}{54}{section*.150}' in toc
assert all('{appendix.'+a+'}' in toc for a in 'ABCDE')
bad=[s for s in log.splitlines() if re.search(r'Overfull|Underfull|Missing character|undefined|multiply defined',s)]
assert not bad, bad
warnings=[s for s in log.splitlines() if 'Warning:' in s]
assert len(warnings)==2 and all('unicode-math' in s for s in warnings)
assert not re.search(r'\\(?:overbracket|underbracket|coloneqq|eqqcolon|coloneq)\b',tex.split(r'\begin{document}',1)[1])
write('final-render-check.json',{
    'overall':'PASS_DOCUMENT_CORRESPONDENCE_AND_RENDER_CHECK',
    'source_commit':git('rev-parse','HEAD').decode().strip(),
    'pdf':ident(pdf.read_bytes()),'tex':ident(tex.encode()),
    'markdown':ident(md.encode()),'pages':55,
    'source_math_nodes_preserved_in_order':931,'render_math_nodes':933,
    'two_extra_math_nodes':'fixed bibliography O(3) and sin Theta only',
    'display_math_blocks':154,'equation_tags_unchanged':147,
    'all_equation_tags_present_in_pdf_text':True,
    'equation_reference_endpoints_including_long_spelling':len(refs),
    'unresolved_equation_references':[],
    'fixed_bibliography_entries_rendered_once':20,
    'restored_literal_STF_prose':raw_html,
    'pdf_reconstructed_normal_determinants':normal_values,
    'pdf_reconstructed_squared_minors':minor_values,
    'all_twelve_exact_pdf_fractions_match_fixed_source':True,
    'part_toc_pages':[6,13,17,23,28,31,37],
    'unnumbered_toc_anchors':'dedicated section anchors; References page 54',
    'overfull_underfull_missing_glyph_undefined_reference_count':0,
    'retained_nonblocking_warnings':warnings,
    'warning_scope':'mathtools/unicode-math ownership of unused bracket and colon macros',
    'visual_inspection':'separate PAGE_REVIEW; text extraction is not visual review'})
print('PASS: 55 pages; 931 math nodes; 147 tags; 20 bibliography targets; 12 exact PDF fractions')
