"""Static extraction only: ast.parse/safe_load/text parsing, never module import.

Non-Python declarations are lexical, not a compiler or proof checker. Their
limitations are stored alongside every affected file and symbol.
"""
from __future__ import annotations

import ast
import io
import json
import re
import tokenize
import shutil
import subprocess
from pathlib import PurePosixPath

import yaml

LANGUAGES = {'.py': 'python', '.pyi': 'python', '.rs': 'rust', '.lean': 'lean',
 '.wl': 'wolfram', '.wls': 'wolfram', '.m': 'wolfram', '.nb': 'wolfram_notebook',
 '.sage': 'sage', '.sh': 'shell', '.bash': 'shell', '.ipynb': 'notebook',
 '.json': 'json', '.jsonl': 'jsonl', '.yaml': 'yaml', '.yml': 'yaml', '.toml': 'toml',
 '.ini': 'config', '.cfg': 'config', '.md': 'markdown', '.rst': 'markdown',
 '.tex': 'latex', '.txt': 'text', '.stdout': 'text', '.stderr': 'text', '.log': 'text',
 '.c': 'c', '.h': 'c', '.cpp': 'cpp', '.hpp': 'cpp', '.f90': 'fortran', '.f': 'fortran',
 '.jl': 'julia', '.R': 'r', '.r': 'r', '.sql': 'sql', '.csv': 'csv', '.tsv': 'csv', '.pdf': 'pdf'}
CODE = {'python', 'rust', 'lean', 'wolfram', 'wolfram_notebook', 'sage', 'shell',
        'notebook', 'c', 'cpp', 'fortran', 'julia', 'r', 'sql'}
ARCHIVES = ('.zip', '.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tar.xz')
CONTEXT_WORDS = ('theorem','claim','proposition','lemma','conjecture','candidate','cas_contract',
                 'experiment_registry','experiments','analysis_registry')
PATH_RE = re.compile(r"(?<![\w])((?:[\w.@+()\-]+/)*[\w.@+()\-]+\.(?:py|rs|lean|wl|wls|sage|json|yaml|yml|md|tex|csv|npz|npy|fits|fit|h5|txt|pdf|zip|toml))(?:\b|$)")


def language(path):
    suffix = PurePosixPath(path).suffix
    if path.lower().endswith(ARCHIVES):
        return 'archive'
    return LANGUAGES.get(suffix, 'binary_or_unclassified')


def extraction_context(path):
    return tuple(x for x in CONTEXT_WORDS if x in path.lower())


def catalog_generated(path):
    p='/'+path.replace('!/','/').strip('/')+'/'
    return '/docs/project_catalog/' in p or '/.cache/project_catalog/' in p


def owner(path):
    p = '/' + path.lower()
    for token, value in [('/tsc', 'tsc_legacy'), ('/teff', 'tsc_legacy'), ('/mio/', 'mio'),
                         ('/obsstat/', 'obsstat'), ('/bass/', 'bass'), ('/src/common/', 'common'),
                         ('/htt/htt/', 'htt'), ('/src/', 'bass_rs')]:
        if token in p:
            return value
    return 'common' if p.startswith(('/scripts/', '/tests/', '/.agent', '/harness')) else 'docs'


def role(path, lang):
    p = path.lower()
    if any(x in p.split('/') for x in ['old_version', 'legacy', 'legacy_sources', 'tsc_legacy']):
        return 'legacy_source' if lang in CODE else 'legacy_material'
    if '/test' in '/' + p or PurePosixPath(p).name.startswith('test_'):
        return 'test' if lang in CODE else 'test_fixture'
    if lang == 'archive':
        return 'archive'
    if lang in CODE:
        return 'tooling' if p.startswith(('.agent', '.codex', 'scripts/codex_harness', 'scripts/catalog_lib', 'scripts/project_catalog.py', 'harness')) else 'code'
    if any(x in p for x in ['generated/', 'receipt', 'validation', 'adjudication', 'cas/axes', 'evidence']):
        return 'saved_evidence'
    if lang in {'markdown', 'latex', 'text'}:
        return 'documentation'
    if lang in {'json', 'yaml', 'jsonl', 'toml', 'config'}:
        return 'configuration_or_registry'
    return 'data_or_binary'


def state(raw):
    """Describe an assertion as recorded. Never infer proof from ACTIVE or PASS."""
    s = str(raw or '').upper()
    tokens=re.sub(r'[^A-Z0-9]+','_',s).strip('_')
    def token(pattern):return bool(re.search(r'(?:^|_)(?:'+pattern+r')(?:_|$)',tokens))
    if any(x in s for x in ['RETRACT', 'REFUTED']): return 'recorded_retracted'
    if any(x in s for x in ['SUPERSEDED', 'DEPRECATED', 'RETIRED']): return 'recorded_superseded'
    if any(x in s for x in ['BLOCK', 'WITHHELD', 'UNRESOLVED', 'STOP_', 'FAIL', 'UNVERIFIED']) or token('NOT_EVALUATED|NOT_PROVEN|UNPROVEN|NOT_VALIDATED|UNVALIDATED'): return 'recorded_unresolved'
    if any(x in s for x in ['PROPOSE', 'PLANNED', 'SPECIFIED', 'HYPOTHESIS', 'PENDING', 'SPECULATIVE']) or token('CANDIDATE|CONJECTURE'): return 'candidate'
    if 'CONDITIONAL' in s: return 'recorded_conditional'
    if token('PROVEN|DERIVED|PROOF_COMPLETE'): return 'recorded_proven_or_derived'
    if token('PASS|PASSED|VALIDATED'): return 'recorded_validation_claim'
    if token('ACTIVE'): return 'recorded_active'
    return 'source_present'


def record(kind, local_id, name, *, line=1, end_line=None, summary='', raw='', status=None, **details):
    return dict(kind=kind, local_id=str(local_id), name=str(name), line=line, end_line=end_line,
                summary=str(summary), recorded_status=str(raw or ''), status=status or state(raw),
                evidence_level='static_source_only', details=details)


def reference_edges(text):
    return sorted(set(PATH_RE.findall(text)))


def _brief(value, limit=12000):
    s = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    return s if len(s) <= limit else s[:limit] + '\n[CATALOG_EXCERPT_TRUNCATED; consult source]'


def _stub(node):
    body = list(getattr(node, 'body', []))
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    return not body or all(isinstance(x, ast.Pass) or
        (isinstance(x, ast.Expr) and isinstance(x.value, ast.Constant) and x.value.value is Ellipsis) or
        (isinstance(x, ast.Raise) and isinstance(x.exc, (ast.Name, ast.Call)) and
         (getattr(x.exc, 'id', None) == 'NotImplementedError' or getattr(getattr(x.exc, 'func', None), 'id', None) == 'NotImplementedError'))
        for x in body)


def python_records(text):
    tree = ast.parse(text)
    out = []
    doc = ast.get_docstring(tree, clean=False) or ''
    imports, calls, io_calls, arguments = [], set(), [], []
    entry = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append('.' * node.level + (node.module or ''))
        elif isinstance(node, ast.Call):
            name = ast.unparse(node.func)
            calls.add(name)
            if any(name.endswith(x) for x in ['.load', '.save', '.loadtxt', '.savetxt', '.read_text', '.write_text', '.read_csv', '.to_csv', '.open', 'open', '.savez', '.savez_compressed']):
                io_calls.append({'line': node.lineno, 'expression': ast.get_source_segment(text, node)})
            if name.endswith('.add_argument'):
                arguments.append(ast.get_source_segment(text, node))
        elif isinstance(node, ast.If) and '__name__' in ast.unparse(node.test) and '__main__' in ast.unparse(node.test):
            entry = True
    out.append(record('feature', 'module', 'module', summary=doc[:6000],
               imports=sorted(set(imports)), calls=sorted(calls), io=io_calls,
               arguments=arguments, entrypoint=entry, extraction='python_ast',
               runtime_status='NOT_EXECUTED', dynamic_resolution='not_attempted'))

    def visit(body, prefix='', interface=False):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                q = prefix + node.name
                sig = ('class ' + node.name + '(' + ', '.join(ast.unparse(x) for x in node.bases) + ')') if isinstance(node, ast.ClassDef) else (
                    ('async ' if isinstance(node, ast.AsyncFunctionDef) else '') + 'def ' + node.name + '(' + ast.unparse(node.args) + ')' +
                    (' -> ' + ast.unparse(node.returns) if node.returns else ''))
                abstract = interface or any(ast.unparse(x).endswith('abstractmethod') for x in node.decorator_list)
                is_stub = not isinstance(node,ast.ClassDef) and _stub(node)
                d = ast.get_docstring(node, clean=False) or ''
                inner_calls = sorted({ast.unparse(x.func) for x in ast.walk(node) if isinstance(x, ast.Call)})
                out.append(record('code', q, q, line=node.lineno, end_line=node.end_lineno,
                    summary=d[:6000], status='abstract_interface' if abstract else 'stub' if is_stub else 'definition_present', signature=sig,
                    declaration='class' if isinstance(node, ast.ClassDef) else 'function',
                    decorators=[ast.unparse(x) for x in node.decorator_list], calls=inner_calls,
                    runtime_status='NOT_EXECUTED', input_output_basis='signature_and_docstring'))
                if is_stub and not abstract:
                    out.append(record('update', 'stub:' + q, q + ' implementation body', line=node.lineno,
                        summary='스텁 본문이 존재한다. 사용하려면 구현 또는 명시적 추상 인터페이스 여부 확인이 필요하다.',
                        status='needs_implementation_review', reason='body_only_pass_ellipsis_or_NotImplementedError',
                        required_action='Check intended abstract/interface role; implement only if a consumer requires concrete behavior.',
                        priority='consumer_dependent', verification='future consumer-specific tests; not executed in catalog scan'))
                protocol = isinstance(node,ast.ClassDef) and any(ast.unparse(x).endswith('Protocol') for x in node.bases)
                visit(node.body, q + '.', protocol)
            else:
                for name in ['body', 'orelse', 'finalbody']:
                    nested = getattr(node, name, None)
                    if isinstance(nested, list): visit(nested, prefix)
                for handler in getattr(node, 'handlers', []): visit(handler.body, prefix)
    visit(tree.body)
    return out


DECLARATIONS = {
 'rust': r'^\s*(?:pub(?:\([^)]*\))?\s+)?(?:(?:async|unsafe|const|extern\s+"[^"]+")\s+)*(fn|struct|enum|trait|type|mod|impl|macro_rules!)\s*([\w:<>]+)',
 'lean': r'^\s*(?:(?:private|protected|noncomputable|unsafe|partial)\s+)*(theorem|lemma|def|abbrev|axiom|constant|structure|class|inductive|instance)\s+([^\s(:{]+)',
 'wolfram': r'^\s*([A-Za-z$][\w$`]*)\s*(\[[^\n]*?\])?\s*(?::=|=)',
 'sage': r'^\s*(def|class)\s+(\w+)',
 'shell': r'^\s*(?:function\s+([\w-]+)|([\w-]+)\s*\(\))',
 'fortran': r'^\s*(?:(?:recursive|pure|elemental)\s+)*(module|subroutine|function|program)\s+(\w+)',
 'julia': r'^\s*(function|struct|module|macro)\s+([\w.!]+)',
 'r': r'^\s*([\w.]+)\s*<-\s*function\s*\(',
 'c': r'^\s*(?:static\s+|inline\s+|extern\s+)?[\w*\s]+?\s+(\w+)\s*\([^;]*\)\s*\{',
 'cpp': r'^\s*(?:(?:class|struct|namespace)\s+(\w+)|[\w:*\s]+?\s+([\w:]+)\s*\([^;]*\)\s*\{)',
 'sql': r'^\s*CREATE\s+(?:VIRTUAL\s+)?(TABLE|VIEW|INDEX|TRIGGER)\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w]+)',
}


def lexical_records(text, lang):
    lines = text.splitlines()
    out = [record('feature', 'module', 'module', summary='\n'.join(lines[:30])[:4000],
        extraction='lexical_declarations', limitations=['not compiler-validated', 'macros/dynamic declarations and nested scopes may be unresolved'], runtime_status='NOT_EXECUTED')]
    expression = DECLARATIONS.get(lang)
    if not expression:
        return out
    namespace = []
    for i, line in enumerate(lines, 1):
        if lang == 'lean':
            n = re.match(r'^\s*namespace\s+(\S+)', line)
            if n: namespace.append(n.group(1))
            if re.match(r'^\s*end(?:\s|$)', line) and namespace: namespace.pop()
        m = re.match(expression, line, re.I if lang in {'fortran', 'sql'} else 0)
        if not m: continue
        groups = [x for x in m.groups() if x]
        name = groups[-1] if lang not in {'wolfram', 'r'} else groups[0]
        if lang == 'wolfram' and name.startswith('['): name = groups[0]
        q = '.'.join(namespace + [name])
        decl = groups[0] if len(groups) > 1 and lang not in {'wolfram', 'cpp'} else 'declaration'
        kind = 'proposition' if lang == 'lean' and decl in {'theorem', 'lemma', 'axiom', 'constant'} else 'code'
        following = '\n'.join(lines[i-1:i+15])
        out.append(record(kind, f'{q}@{i}', q, line=i, summary=following[:2400],
            status='declaration_present', signature=line.strip(), declaration=decl,
            extraction='lexical', proof_status='NOT_RECHECKED' if kind == 'proposition' else None,
            sorry_or_admit_nearby=bool(re.search(r'\b(sorry|admit)\b', following)) if lang == 'lean' else None))
    return out


def structured_records(data, path):
    out = []
    context = ' '.join(extraction_context(path))
    seen = set()
    def walk(value, loc='$', parent=''):
        if isinstance(value, dict):
            if id(value) in seen: return
            seen.add(id(value))
            local_id = next((value[k] for k in ['claim_id', 'theorem_id', 'lemma_id', 'candidate_id', 'id'] if k in value and isinstance(value[k], (str, int))), None)
            raw = next((value[k] for k in ['status', 'state', 'verdict', 'scientific_status', 'result', 'decision'] if k in value and isinstance(value[k], (str, bool))), '')
            title = next((value[k] for k in ['statement', 'claim', 'title', 'name', 'text', 'description', 'objective'] if isinstance(value.get(k), str)), '')
            kind = None
            if local_id is not None:
                if any(x in context + ' ' + parent.lower() for x in ['theorem', 'claim', 'proposition', 'lemma', 'conjecture', 'candidate', 'cas_contract']):
                    kind = 'proposition'
                elif any(x in context + ' ' + parent.lower() for x in ['experiment_registry', 'experiments', 'analysis_registry']): kind = 'analysis'
                elif str(local_id).startswith(('PR-', 'REV-', 'WU-')) or parent == 'prs': kind = 'plan'
                elif title and raw: kind = 'evidence'
            elif loc == '$' and raw:
                kind = 'evidence'; local_id = '$'
            if kind:
                details = {k: value[k] for k in ['owner','scope','claim_tier','transfer_source','assumptions','conditions','domain','conventions','units','sources','source_refs','evidence_refs','proof','proof_obligations','required_inputs','required_outputs','inputs','outputs','files','tests','depends','supersedes','superseded_by','landing','note','caveats','command','generating_command','kill','dod','allowed_claim_tier','blocked_claims','status_surface','scientific_status','independence_mode'] if k in value}
                details['source_pointer'] = loc
                details['source_record_excerpt'] = _brief(value)
                details['runtime_status'] = 'NOT_EXECUTED'
                if kind == 'proposition': details['proof_status'] = 'NOT_RECHECKED'
                out.append(record(kind, f'{local_id}:{loc}', title or str(local_id), summary=title,
                    raw=raw, registered_id=str(local_id), **details))
                if state(raw) in {'recorded_retracted','recorded_superseded'} and value.get('superseded_by'):
                    out.append(record('update', f'successor:{local_id}:{loc}', str(local_id) + ' successor',
                        raw=raw, summary=f"원문이 후속 항목 {value['superseded_by']}를 지정한다. 소비자의 참조·가정 차이를 확인한다.",
                        required_action='Inspect the named successor and compare assumptions before updating consumers.',
                        superseded_by=value['superseded_by'], source_pointer=loc, priority='consumer_dependent'))
            for k, v in value.items():
                if isinstance(v, (dict, list)):
                    walk(v, loc + '/' + str(k).replace('~','~0').replace('/','~1'), str(k))
        elif isinstance(value, list):
            for i, v in enumerate(value):
                if isinstance(v, (dict, list)): walk(v, loc + '/' + str(i), parent)
    walk(data)
    return out


def prose_records(text, lang):
    lines = text.splitlines()
    marks = []
    for i, line in enumerate(lines):
        if re.match(r'^#{1,6}\s+\S', line) or re.match(r'^\s*(?:Theorem|Lemma|Proposition|Corollary|Conjecture|정리|명제)\s+[\w.:-]+',line) or (lang == 'latex' and re.search(r'\\(?:begin\{(?:theorem|lemma|proposition|corollary|conjecture)\}|(?:sub)*section\{)', line)):
            marks.append((i, line.strip()))
    out = []
    for n, (i, title) in enumerate(marks):
        stop = marks[n+1][0] if n+1 < len(marks) else len(lines)
        body = '\n'.join(lines[i:stop])
        title = title.lstrip('# ').strip()
        claim = bool(re.search(r'\b(theorem|lemma|proposition|corollary|conjecture)\b|정리|명제|증명|추측', title, re.I))
        planned = bool(re.search(r'candidate|propos|planned|후보|예정|계획', title, re.I))
        out.append(record('proposition' if claim else 'document', f'section:{i+1}', title,
            line=i+1, end_line=stop, summary=body[:8000], status='candidate' if claim and planned else 'textual_statement' if claim else 'documented',
            extraction='section_text', proof_status='NOT_RECHECKED' if claim else None,
            excerpt_truncated=len(body)>8000))
    return out


def extract(data, path):
    lang = language(path)
    result = {'status': 'parsed', 'language': lang, 'summary': '', 'records': [], 'references': [], 'limitations': []}
    if lang not in CODE | {'json','jsonl','yaml','toml','config','markdown','latex','text','csv','pdf'}:
        result['status'] = 'metadata_only'; return result
    if lang=='pdf':
        converter=shutil.which('pdftotext')
        if not converter:
            result['status']='pdf_extractor_unavailable';result['limitations']=['pdftotext not installed'];return result
        try:
            conversion=subprocess.run([converter,'-layout','-','-'],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
            if conversion.returncode:
                result['status']='pdf_text_error';result['limitations']=[conversion.stderr.decode('utf8','replace')[:1000]];return result
            text=conversion.stdout.decode('utf8','replace')
            result['summary']=text[:4000];result['records']=prose_records(text,'text');result['references']=reference_edges(text)
            result['status']='pdf_text_partial';result['limitations']=['text extraction only; equations, images and reading order not visually audited']
            return result
        except subprocess.TimeoutExpired:
            result['status']='pdf_text_timeout';result['limitations']=['pdftotext exceeded 60 seconds'];return result
    try:
        encoding = tokenize.detect_encoding(io.BytesIO(data).readline)[0] if lang == 'python' else 'utf-8-sig'
        text = data.decode(encoding)
    except (UnicodeError, SyntaxError):
        try: text = data.decode('latin-1'); result['limitations'].append('latin1_fallback')
        except UnicodeError:
            result['status'] = 'decode_error'; return result
    result['summary'] = text[:4000]
    result['references'] = reference_edges(text)
    try:
        if lang == 'python':
            result['records'] = python_records(text)
        elif lang == 'notebook':
            notebook = json.loads(text)
            for i, cell in enumerate(notebook.get('cells', [])):
                source = cell.get('source', '')
                source = ''.join(source) if isinstance(source, list) else source
                records = prose_records(source, 'markdown') if cell.get('cell_type') == 'markdown' else python_records(source)
                for r in records:
                    r['local_id'] = f'cell:{i}/' + r['local_id']; r['details']['cell_index'] = i
                    result['records'].append(r)
        elif lang in CODE:
            result['records'] = lexical_records(text, lang)
            result['status'] = 'lexical_partial'
            result['limitations'].append('lexical_only_not_compiler_or_proof_validation')
        elif lang in {'json','yaml','jsonl','toml'}:
            if lang == 'json': values = [json.loads(text)]
            elif lang == 'yaml': values = list(yaml.safe_load_all(text))
            elif lang == 'toml':
                import tomllib
                values = [tomllib.loads(text)]
            else: values = [json.loads(line) for line in text.splitlines() if line.strip()]
            for i, value in enumerate(values):
                recs = structured_records(value, path)
                for r in recs:
                    r['local_id'] = f'doc:{i}/' + r['local_id']
                result['records'].extend(recs)
        elif lang in {'markdown','latex','text'}:
            result['records'] = prose_records(text, lang)
    except (SyntaxError, ValueError, TypeError, RecursionError, yaml.YAMLError) as exc:
        result['status'] = 'parse_error'
        result['limitations'].append(f'{type(exc).__name__}: {str(exc)[:500]}')
        if lang == 'python':
            result['records'] = lexical_records(text, 'sage')
            result['limitations'].append('Python AST failed; lexical declarations retained')
    # TODO is an annotation, not automatically an implementation defect.
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(r'\b(TODO|FIXME|NotImplementedError|unimplemented!|todo!)\b', line) and lang in CODE:
            result['records'].append(record('annotation', f'note:{i}', line.strip()[:180], line=i,
                summary=line.strip(), status='recorded_followup_marker', basis='lexical_marker_not_adjudicated'))
    return result
