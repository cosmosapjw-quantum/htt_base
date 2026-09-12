"""Catalog-only tests. Fixture code is never imported or executed."""
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import zipfile

import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from catalog_lib.db import connect, counts, get_meta
from catalog_lib.extract import extract, state
from catalog_lib.scan import Scanner, version_members
from catalog_lib.query import query, show, history, check
from catalog_lib.package import pack, restore


def cmd(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()


def commit(root,message):
    cmd(root,'add','.')
    cmd(root,'-c','user.name=Catalog Fixture','-c','user.email=catalog@example.invalid','commit','-qm',message)
    return cmd(root,'rev-parse','HEAD')


@pytest.fixture
def project(tmp_path):
    repo=tmp_path/'repo';repo.mkdir();cmd(repo,'init','-q','-b','main')
    (repo/'model.py').write_text('"""CF4 source feature."""\nimport forbidden_research_runtime\ndef fit(x: int=2) -> int:\n    """Return a synthetic fixture value."""\n    return x+1\n\ndef planned(x):\n    raise NotImplementedError\n\nif __name__ == "__main__":\n    raise RuntimeError("NEVER EXECUTE")\n')
    (repo/'proof.py').write_text('raise RuntimeError("NEVER IMPORT PROOF")\n')
    (repo/'THEOREM_REGISTRY.yaml').write_text('entries:\n- id: P1\n  title: Fixture statement under A\n  status: ACTIVE\n  assumptions: [A]\n  sources: [proof.py]\n- id: P2\n  title: Candidate\n  status: PLANNED\n  sources: [missing.py]\n')
    first=commit(repo,'first')
    cmd(repo,'mv','model.py','renamed.py')
    (repo/'proof.py').unlink()
    (repo/'THEOREM_REGISTRY.yaml').write_text('entries:\n- id: P1\n  title: Fixture statement under B\n  status: RETRACTED\n  assumptions: [B]\n  superseded_by: P2\n  sources: [proof.py]\n- id: P2\n  title: Candidate\n  status: PLANNED\n')
    with zipfile.ZipFile(repo/'legacy.zip','w') as z:
        z.writestr('old.py','def legacy(x):\n    return x\n')
        z.writestr('THEOREM_REGISTRY.yaml','entries:\n- id: P1\n  statement: Archived different premise\n  status: PROVEN\n  assumptions: [C]\n')
    second=commit(repo,'rename and correction')
    scope={'baseline_source':'fixture','baseline_commit':second,'git_sources':[{'id':'fixture','path':str(repo),'history':'all'}], 'filesystem_sources':[], 'text_limit_bytes':1000000}
    db=tmp_path/'catalog.sqlite'
    with connect(db) as c:Scanner(c,scope).run()
    return repo,first,second,scope,db


def test_full_history_rename_and_archive(project):
    repo,first,second,scope,db=project
    with connect(db,readonly=True) as c:
        assert len(version_members(c,'fixture',first))==3
        assert len(version_members(c,'fixture',second))==3
        assert {r['path'] for r in query(c,kind='code',ref=first)}=={'model.py'}
        now=query(c,kind='code',ref=second)
        assert {r['path'] for r in now}=={'renamed.py','legacy.zip!/old.py'}
        renamed=next(r for r in now if r['name']=='fit')
        original=next(r for r in query(c,kind='code',ref=first) if r['name']=='fit')
        assert original['content_id']==renamed['content_id']
        assert original['file_id']!=renamed['file_id']
        assert check(c)['status']=='PASS'


def test_claim_states_no_promotion_and_version_bound_references(project):
    _,first,second,scope,db=project
    with connect(db,readonly=True) as c:
        old=next(r for r in query(c,kind='proposition',ref=first) if r['recorded_status']=='ACTIVE')
        new=next(r for r in query(c,kind='proposition',ref=second) if r['recorded_status']=='RETRACTED')
        assert old['status']=='recorded_active' and new['status']=='recorded_retracted'
        assert json.loads(old['details'])['proof_status']=='NOT_RECHECKED'
        assert any(e['resolution']=='same_version_file_present' for e in show(c,old['id'])['relationships'] if e['target']=='proof.py')
        assert all(e['resolution']=='unresolved_at_source_version' for e in show(c,new['id'])['relationships'] if e['target']=='proof.py')
        assert show(c,old['id'])['proof_evidence']['support_status']=='REFERENCED_FILES_ONLY'
        assert show(c,new['id'])['proof_evidence']['support_status']=='NO_BOUND_REFERENCE'
        assert len(history(c,old['id']))==2
        assert any(r['status']=='recorded_proven_or_derived' for r in query(c,kind='proposition',ref=second))


def test_static_inputs_stubs_and_imports(project):
    _,_,_,_,db=project
    with connect(db,readonly=True) as c:
        code=query(c,kind='code')
        fit=next(r for r in code if r['name']=='fit')
        assert 'x: int=2' in json.loads(fit['details'])['signature']
        assert next(r for r in code if r['name']=='planned')['status']=='stub'
        assert query(c,kind='analysis',text='CF4')
        assert query(c,needs_update=True)
        assert c.execute("SELECT count(*) FROM edges WHERE relation='imports' AND target='forbidden_research_runtime'").fetchone()[0]>0


def test_incremental_logical_stability_and_new_commit(project):
    repo,first,second,scope,db=project
    with connect(db) as c:
        before=counts(c)
        report=Scanner(c,scope).run()
        assert report['parsed_new']==0
        assert counts(c)==before
        (repo/'new.py').write_text('def later():\n    return 3\n')
        third=commit(repo,'third')
        Scanner(c,scope).run()
        assert len(query(c,kind='code',ref=third))==4
        assert counts(c)['commits']==before['commits']+1


def test_independent_full_rebuild_preserves_all_logical_rows(project,tmp_path):
    _,_,_,scope,db=project
    rebuilt=tmp_path/'rebuilt.sqlite'
    with connect(rebuilt) as fresh:Scanner(fresh,scope).run()
    with connect(db,readonly=True) as a,connect(rebuilt,readonly=True) as b:
        for table in ['sources','commits','refs','trees','contents','files','records','edges','filesystem','gaps','commit_aliases','snapshots','members']:
            left=sorted(tuple(r) for r in a.execute('SELECT * FROM '+table))
            right=sorted(tuple(r) for r in b.execute('SELECT * FROM '+table))
            assert left==right,table


def test_pack_restore_and_query_without_sources(project,tmp_path):
    repo,first,second,scope,db=project
    dest=tmp_path/'package'
    manifest=pack(db,dest,chunk_bytes=5000)
    assert len(manifest['parts'])>1
    repo.rename(tmp_path/'source-hidden')
    restored=tmp_path/'restored.sqlite'
    restore(dest,restored)
    with connect(restored,readonly=True) as c:
        assert query(c,kind='analysis') and check(c)['status']=='PASS'
    part=dest/manifest['parts'][0]['name'];part.write_bytes(b'bad')
    with pytest.raises(ValueError):restore(dest,tmp_path/'bad.sqlite')


def test_filesystem_overlay_incremental_and_missing(tmp_path):
    root=tmp_path/'files';root.mkdir();(root/'local.py').write_text('def original():\n    pass\n')
    (root/'raw.bin').write_bytes(b'12345')
    (root/'broken').symlink_to('absent')
    scope={'filesystem_sources':[{'id':'local','path':str(root)}]}
    with connect(tmp_path/'fs.sqlite') as c:
        Scanner(c,scope).run()
        assert query(c,kind='code',ref='working')
        assert query(c,kind='gap',text='broken')
        before=counts(c);Scanner(c,scope).run();assert counts(c)==before
        (root/'local.py').unlink();Scanner(c,scope).run()
        assert not query(c,kind='code',ref='working')
        assert query(c,kind='code',ref='all')


@pytest.mark.parametrize('lang,body,expected',[
 ('a.rs','pub struct Foo {}\npub fn bar() {}','bar'),
 ('a.lean','namespace X\ntheorem claim : True := by trivial\nend X','X.claim'),
 ('a.wls','f[x_] := x + 1','f'),
 ('a.sage','def fit(x):\n    return x','fit'),
 ('a.sh','run_this() { echo hello; }','run_this'),
])
def test_lexical_languages_are_explicitly_partial(lang,body,expected):
    result=extract(body.encode(),lang)
    assert result['status']=='lexical_partial'
    assert any(r['name']==expected for r in result['records'])


def test_notebook_and_bad_python_are_accounted():
    notebook={'cells':[{'cell_type':'code','source':['def n():\n','    return 1\n']}]}
    result=extract(json.dumps(notebook).encode(),'a.ipynb')
    assert any(r['name']=='n' and r['details']['cell_index']==0 for r in result['records'])
    assert extract(b'def old(:\n','legacy.py')['status']=='parse_error'
    assert state('CAS_4AXIS_PASS')=='recorded_validation_claim'
    assert state('ACTIVE_CONDITIONAL')=='recorded_conditional'


def test_scan_never_runs_git_clean_filters_or_fsmonitor(project,tmp_path):
    repo,_,_,scope,db=project
    clean=tmp_path/'clean-filter-ran';monitor=tmp_path/'fsmonitor-ran'
    (repo/'.gitattributes').write_text('renamed.py filter=catalog_fixture\n')
    cmd(repo,'config','filter.catalog_fixture.clean',f'touch {clean}; cat')
    cmd(repo,'config','core.fsmonitor',f'touch {monitor}')
    (repo/'renamed.py').write_text('def modified():\n    return 999\n')
    scope['filesystem_sources']=[{'id':'overlay','path':str(repo)}]
    with connect(db) as c:
        Scanner(c,scope).run()
        assert any(r['name']=='modified' for r in query(c,kind='code',ref='working'))
        assert not clean.exists() and not monitor.exists()


def test_same_content_different_classifier_context_is_order_independent(tmp_path):
    content=b'entries:\n- id: P1\n  title: Example\n  status: ACTIVE\n'
    with connect(tmp_path/'contexts.sqlite') as c:
        scanner=Scanner(c,{});scanner.source('x','filesystem','fixture')
        for name in ['a.yaml','conjectures.yaml','experiments.yaml']:
            scanner.material('x',name,content)
        found={r['path']:r['kind'] for r in c.execute('SELECT path,kind FROM catalog')}
        assert found=={'a.yaml':'evidence','conjectures.yaml':'proposition','experiments.yaml':'analysis'}


def test_changed_extraction_limits_refuse_stale_incremental(project):
    _,_,_,scope,db=project
    scope=dict(scope,text_limit_bytes=1001)
    with connect(db) as c:
        with pytest.raises(ValueError,match='extraction limits changed'):Scanner(c,scope)


def test_source_filter_and_invalid_exclusion(project):
    _,_,_,scope,db=project
    with connect(db) as c:
        Scanner(c,scope).source('other','filesystem','missing')
        assert [r['id'] for r in query(c,kind='source',source='fixture')]==['fixture']
        for ref in ['all','working']:
            with pytest.raises(ValueError,match='concrete'):query(c,not_in_ref=ref)


def test_abstract_interfaces_and_empty_exception_are_not_update_defects():
    body=b'from abc import abstractmethod\nclass Error(Exception):\n    pass\nclass P(Protocol):\n    def interface(self): ...\n@abstractmethod\ndef abstract():\n    pass\n'
    result=extract(body,'interfaces.py')
    assert not any(r['kind']=='update' for r in result['records'])
    assert any(r['name']=='P.interface' and r['status']=='abstract_interface' for r in result['records'])


def test_overloads_and_conditional_definitions_do_not_disappear(tmp_path):
    code=b'def f(x: int): ...\ndef f(x: str): ...\ndef f(x):\n    return x\n'
    with connect(tmp_path/'duplicates.sqlite') as c:
        scanner=Scanner(c,{});scanner.source('x','filesystem','fixture')
        scanner.material('x','overloaded.py',code)
        rows=c.execute("SELECT local_id FROM records WHERE kind='code'").fetchall()
        assert len(rows)==3
        assert len({r[0] for r in rows})==3
        scanner.refresh_record_views()
        assert c.execute("SELECT count(*) FROM records WHERE kind='code'").fetchone()[0]==3


def test_document_generation_and_read_only_query_without_yaml(project,tmp_path):
    _,_,_,_,db=project
    from catalog_lib.reports import write_reports
    with connect(db) as c:
        result=write_reports(c,tmp_path/'docs')
        assert result['baseline_file_count']==3
        assert (tmp_path/'docs'/'COVERAGE.md').is_file()
    script="import sys;sys.modules['yaml']=None;sys.path.insert(0,sys.argv[1]);import project_catalog;project_catalog.main(['--db',sys.argv[2],'query','--kind','code','--limit','1'])"
    proc=subprocess.run([sys.executable,'-B','-c',script,str(ROOT/'scripts'),str(db)],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr


def test_port_mentions_preserve_negation_and_never_assert_completion(tmp_path):
    with connect(tmp_path/'port.sqlite') as c:
        scanner=Scanner(c,{});scanner.source('x','filesystem','fixture')
        scanner.material('x','migration.md',b'# Migration\nPorted from old.py to new.py.\nRejected migration of the inference owner.\n')
        scanner.refresh_record_views()
        row=c.execute("SELECT * FROM records WHERE kind='port'").fetchone()
        assert row['status']=='recorded_port_mention'
        assert 'Rejected migration' in row['summary']
        assert json.loads(row['details'])['port_completion']=='NOT_VERIFIED'


def test_streaming_exports_preserve_rows_and_quoting(project,tmp_path):
    import csv
    from catalog_lib.query import write_rows
    _,_,_,_,db=project
    with connect(db,readonly=True) as c:
        expected=query(c,kind='code',ref='all',limit=-1)
        for form in ['json','csv','table']:
            rows=query(c,kind='code',ref='all',limit=-1,stream=True)
            assert not isinstance(rows,list)
            target=tmp_path/('export.'+form);write_rows(rows,target,form)
            if form=='json':assert json.loads(target.read_text())==expected
            if form=='csv':
                with target.open() as f:assert [r['id'] for r in csv.DictReader(f)]==[r['id'] for r in expected]


def test_curated_version_bindings_survive_incremental_scan(project,tmp_path):
    from catalog_lib.reports import add_curation
    _,_,_,scope,db=project
    card=tmp_path/'curation.json'
    card.write_text(json.dumps({'cards':[{'id':'C1','title':'Fixture guide','owner':'common',
        'evidence_level':'static_curated_source_summary','question':'Where is the fixture?',
        'source_refs':['renamed.py']}]}))
    with connect(db) as c:
        add_curation(c,card)
        before=counts(c)
        Scanner(c,scope).run()
        assert counts(c)==before


def test_dependency_history_is_labeled_and_has_no_project_symbols(project,tmp_path):
    repo,_,_,_,_=project
    scope={'git_sources':[{'id':'dependency','path':str(repo),'history':'all','dependency_only':True}]}
    with connect(tmp_path/'dependency.sqlite') as c:
        Scanner(c,scope).run()
        source=query(c,kind='source',source='dependency')[0]
        assert source['kind']=='git_dependency_metadata'
        assert source['history_scope']=='commit_and_ref_metadata'
        assert c.execute('SELECT count(*) FROM commits').fetchone()[0]==2
        assert c.execute('SELECT count(*) FROM records').fetchone()[0]==0


def test_agent_cache_is_metadata_only_and_never_recursive(tmp_path):
    root=tmp_path/'root';root.mkdir();cache=root/'.remember';cache.mkdir()
    (root/'source.py').write_text('def useful(): return 1\n')
    (cache/'notes.md').write_text('# Theorem must not enter project catalog\n')
    scope={'filesystem_sources':[{'id':'local','path':str(root)}]}
    with connect(tmp_path/'cache.sqlite') as c:
        scanner=Scanner(c,scope);scanner.run()
        before=counts(c)
        (cache/'new.md').write_text('# Another cached conversation\n')
        Scanner(c,scope).run();assert counts(c)==before
        # Simulate an earlier collector that included context text.
        fid=scanner.material('local','old.md',b'# Cached proposition\ncontext text\n')
        c.execute("UPDATE files SET path='.remember/old.md' WHERE id=?",(fid,))
        assert scanner.omit_context_caches()==1
        assert not c.execute('SELECT 1 FROM records WHERE file_id=?',(fid,)).fetchone()
        assert tuple(c.execute('SELECT content_id,processing_status FROM files WHERE id=?',(fid,)).fetchone())==(None,'agent_context_cache_metadata_only')


def test_status_tokens_never_turn_provenance_into_proven(tmp_path):
    assert state('NOT_EVALUATED_PROVENANCE_REPLAY_ONLY')=='recorded_unresolved'
    assert state('PROVENANCE_BOUND')=='source_present'
    assert state('UNPROVEN')=='recorded_unresolved'
    assert state('BYPASS')=='source_present'
    assert state('INACTIVE')=='source_present'
    assert state('CANDIDATE')=='candidate'
    with connect(tmp_path/'states.sqlite') as c:
        scanner=Scanner(c,{});scanner.source('x','filesystem','fixture')
        scanner.material('x','claims.yaml',b'entries:\n- id: P1\n  status: NOT_EVALUATED_PROVENANCE_REPLAY_ONLY\n')
        c.execute("UPDATE records SET status='recorded_proven_or_derived'")
        assert scanner.refresh_record_states()==1
        assert c.execute('SELECT status FROM records').fetchone()[0]=='recorded_unresolved'


def test_catalog_outputs_in_future_git_history_and_archives_are_not_recursive(project):
    repo,_,_,scope,db=project
    generated=repo/'docs/project_catalog/lists/proposition-001.md'
    generated.parent.mkdir(parents=True);body='# Theorem catalog output is not a new source\n'
    generated.write_text(body)
    with zipfile.ZipFile(repo/'catalog-copy.zip','w') as z:
        z.writestr('docs/project_catalog/README.md',body)
    commit(repo,'generated catalog fixture')
    with connect(db) as c:
        Scanner(c,scope).run()
        rows=c.execute("SELECT id,processing_status,bytes FROM files WHERE path LIKE '%docs/project_catalog/%'").fetchall()
        assert len(rows)==2
        assert all(r['processing_status']=='catalog_generated_metadata_only' and r['bytes']==len(body) for r in rows)
        assert not c.execute("SELECT 1 FROM catalog WHERE path LIKE '%docs/project_catalog/%'").fetchone()
