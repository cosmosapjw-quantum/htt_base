"""Proof inventory tests use inert fixture text, never a proof engine."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import tarfile

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from catalog_lib.db import connect, get_meta
from catalog_lib.scan import Scanner
from catalog_lib.proofs import (build_lists, export_proof_lists, record_digest,
    CONFIRMED, UNCONFIRMED, EXCLUDED)
from catalog_lib.proof_sources import SourceReader
from catalog_lib.proof_discovery import uncovered_hits, prepare
from test_catalog import cmd, commit


@pytest.fixture
def proof_catalog(tmp_path):
    repo=tmp_path/'source';repo.mkdir();cmd(repo,'init','-q','-b','main')
    (repo/'proof.md').write_text('Theorem T: for every real x, x = x.\nProof: reflexivity.\n')
    (repo/'Proof.lean').write_text('theorem T (x : Real) : x = x := by rfl\n')
    (repo/'THEOREM_REGISTRY.json').write_text(json.dumps({'theorems':[
        {'id':'T','statement':'For every real x, x = x','assumptions':['x is real'],'status':'DERIVED','sources':['proof.md']},
        {'id':'C','statement':'Conjecture C','status':'PLANNED','proof_obligations':['Prove C']},
        {'id':'V','statement':'Validation record V','status':'PASS','sources':['proof.md']},
        {'id':'A','statement':'Active record A','status':'ACTIVE'},
        {'id':'R','statement':'Withdrawn claim','status':'RETRACTED'},
        {'id':'S','statement':'Replaced claim','status':'SUPERSEDED'},
    ]}))
    (repo/'ideas.md').write_text('# Planned proof\nTODO: prove a new conjecture for bounded x.\n')
    first=commit(repo,'proof fixture')
    with zipfile.ZipFile(repo/'copy.zip','w') as z:
        z.writestr('THEOREM_REGISTRY.json',(repo/'THEOREM_REGISTRY.json').read_bytes())
    with tarfile.open(repo/'copy.tar.gz','w:gz') as t:
        t.add(repo/'THEOREM_REGISTRY.json',arcname='THEOREM_REGISTRY.json')
    data=json.loads((repo/'THEOREM_REGISTRY.json').read_text());data['theorems'][0]['assumptions']=['x is complex'];data['theorems'][0]['status']='CONDITIONAL'
    (repo/'THEOREM_REGISTRY.json').write_text(json.dumps(data));last=commit(repo,'new premise and archive')
    db=tmp_path/'catalog.sqlite';scope={'baseline_source':'fixture','baseline_commit':last,'git_sources':[{'id':'fixture','path':str(repo),'history':'all'}],'filesystem_sources':[]}
    with connect(db) as c:Scanner(c,scope).run()
    return db,repo,first,last


def review_input(c, tmp_path):
    row=dict(c.execute("SELECT * FROM catalog WHERE kind='proposition' AND recorded_status='DERIVED' AND path='THEOREM_REGISTRY.json'").fetchone())
    proof=dict(c.execute("SELECT * FROM files WHERE path='proof.md'").fetchone())
    text='Proof: reflexivity.'
    review={'review_id':'fixture-reflexivity','classification':CONFIRMED,'reason':'reviewed_existing_proof',
        'statement':'For every real x, x = x','assumptions':['x is real'],'domain':'real numbers',
        'conventions':'ordinary equality','scope':'identity only','alignment':'Exact original T under real-domain premise',
        'limitations':['Fixture review only; no engine executed'],
        'evidence':[{'file_id':proof['id'],'content_sha256':proof['content_id'].split(':')[0],
            'kind':'proof_text','locator':'lines 1-2','text':text,'excerpt_sha256':hashlib.sha256(text.encode()).hexdigest()}],
        'bindings':[{'record_id':row['id'],'record_sha256':record_digest(row)}]}
    payload={'schema_version':1,'baseline':get_meta(c,'baseline'),'reviews':[review]}
    path=tmp_path/'reviews.json';path.write_text(json.dumps(payload));return path,payload,row


def test_no_status_declaration_or_reference_promotes(proof_catalog):
    db,*_=proof_catalog
    with connect(db,readonly=True) as c:
        items,occurrences,s=build_lists(c)
        assert not any(x['classification']==CONFIRMED for x in items)
        assert s['checks']['all_proposition_records_accounted']
        assert s['counts']['additional_discovery_records']>0
        assert {'validation_is_not_proof','declaration_without_bound_proof_record','retracted_record','superseded_record'} <= {x['reason'] for x in items}
        assert all(x['proof_reexecution']=='NOT_EXECUTED' for x in items)


def test_exact_review_and_premise_version_separation(proof_catalog,tmp_path):
    db,*_=proof_catalog
    before=db.read_bytes()
    with connect(db,readonly=True) as c:
        path,_,row=review_input(c,tmp_path)
        items,occ,s=build_lists(c,path)
        yes=[x for x in items if x['classification']==CONFIRMED]
        assert len(yes)==1 and yes[0]['occurrence_ids']==[row['id']]
        assert not yes[0]['r8_source_present']
        assert any(x['catalog_status']=='recorded_conditional' and x['classification']==UNCONFIRMED for x in items)
        assert any('copy.zip!' in o['path'] and o['classification']==UNCONFIRMED for o in occ)
        assert s['checks']['unique_occurrence_partition']
    assert db.read_bytes()==before


@pytest.mark.parametrize('change',['statement_binding','evidence_hash','excerpt','missing_assumptions','receipt_only','conflict'])
def test_reject_stale_or_insufficient_review(proof_catalog,tmp_path,change):
    db,*_=proof_catalog
    with connect(db,readonly=True) as c:
        path,payload,row=review_input(c,tmp_path);r=payload['reviews'][0]
        if change=='statement_binding':r['bindings'][0]['record_sha256']='0'*64
        elif change=='evidence_hash':r['evidence'][0]['content_sha256']='0'*64
        elif change=='excerpt':r['evidence'][0]['text']='changed'
        elif change=='missing_assumptions':r['assumptions']=[]
        elif change=='receipt_only':r['evidence'][0]['kind']='historical_build_record'
        elif change=='conflict':payload['reviews'].append(dict(r,review_id='conflicting'))
        path.write_text(json.dumps(payload))
        with pytest.raises(ValueError):build_lists(c,path)


def test_deterministic_export_and_no_source_access(proof_catalog,tmp_path):
    db,repo,*_=proof_catalog
    with connect(db,readonly=True) as c:
        path,_,_=review_input(c,tmp_path)
        a=tmp_path/'a';b=tmp_path/'b';export_proof_lists(c,a,path)
        repo.rename(tmp_path/'source-unavailable')
        export_proof_lists(c,b,path)
    assert {str(p.relative_to(a)):p.read_bytes() for p in a.rglob('*') if p.is_file()}=={str(p.relative_to(b)):p.read_bytes() for p in b.rglob('*') if p.is_file()}
    assert json.loads((a/'confirmed.json').read_text())[0]['reviewed_support']['assumptions']==['x is real']
    assert all((a/(stem+ext)).exists() for stem in ['confirmed','unconfirmed'] for ext in ['.md','.json','.csv'])
    assert (a/'excluded.csv.gz').exists() and (a/'occurrences/index.json').exists()


def test_raw_reader_git_archive_and_source_drift(proof_catalog):
    db,repo,*_=proof_catalog
    with connect(db,readonly=True) as c:
        reader=SourceReader(c)
        f=c.execute("SELECT id FROM files WHERE path='copy.zip!/THEOREM_REGISTRY.json'").fetchone()
        assert json.loads(reader.read(f[0]))['theorems'][0]['assumptions']==['x is real']
        tar=c.execute("SELECT id FROM files WHERE path='copy.tar.gz!/THEOREM_REGISTRY.json'").fetchone()
        assert json.loads(reader.read(tar[0]))['theorems'][0]['assumptions']==['x is real']
        assert not (repo/'NEVER_EXECUTE').exists()


def test_reader_single_file_annotation_locator(proof_catalog):
    db,repo,*_=proof_catalog
    with connect(db) as c:
        f=dict(c.execute("SELECT * FROM files WHERE path='proof.md'").fetchone())
        c.execute("INSERT INTO sources VALUES(?,?,?,?,?,?,?)",('annotation','curated_navigation',str(repo/'proof.md'),'','','catalog_annotation','{}'))
        f.update(id='single-file-fixture',source_id='annotation',git_blob=None)
        c.execute('INSERT INTO files ('+','.join(f)+') VALUES ('+','.join('?' for _ in f)+')',tuple(f.values()))
        assert SourceReader(c).read(f['id'])==(repo/'proof.md').read_bytes()


def test_occurrence_parts_preserve_every_row(tmp_path):
    import gzip
    from catalog_lib.proofs import write_occurrence_parts
    rows=[{'record_id':str(i),'data':'x'*30} for i in range(30)]
    write_occurrence_parts(tmp_path,rows,limit=300)
    index=json.loads((tmp_path/'index.json').read_text());actual=[]
    assert len(index['parts'])>1
    for p in index['parts']:
        raw=(tmp_path/p['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==p['sha256']
        assert p['uncompressed_bytes']<=300
        actual.extend(map(json.loads,gzip.decompress(raw).decode().splitlines()))
    assert actual==rows and index['rows']==len(rows)


def test_missing_review_is_not_silent(proof_catalog,tmp_path):
    db,*_=proof_catalog
    with connect(db,readonly=True) as c:
        with pytest.raises(FileNotFoundError):build_lists(c,tmp_path/'missing-review.json')


def test_full_source_supplement_finds_clipped_proposal_and_preserves_general_hits():
    text='already exported theorem T\n'+'x'*9000+' TODO: prove hidden result for bounded real x\nproof tooling version\n'
    hits=list(uncovered_hits(text,'content',{'records':[{'summary':'already exported theorem T'}]}))
    assert len(hits)==2
    assert hits[0]['is_proposal'] and hits[0]['line']==2 and hits[0]['excerpt_truncated']
    assert not hits[1]['is_proposal'] and hits[1]['line']==3


def test_source_scan_and_supplement_are_read_only_offline(proof_catalog,tmp_path):
    db,repo,*_=proof_catalog;before=db.read_bytes()
    with connect(db,readonly=True) as c:
        output=tmp_path/'discovery';summary=prepare(c,output)
        assert summary['content_versions']==c.execute('SELECT count(*) FROM contents').fetchone()[0]
        path,payload,_=review_input(c,tmp_path)
        raw=(output/'source_discovery.json').read_bytes()
        (tmp_path/'source_discovery.json').write_bytes(raw)
        payload['supplemental_discovery']={'file':'source_discovery.json','sha256':hashlib.sha256(raw).hexdigest()}
        path.write_text(json.dumps(payload));repo.rename(tmp_path/'gone')
        _,occ,s=build_lists(c,path)
        assert s['checks']['unique_occurrence_partition']
        assert s['raw_source_discovery']['content_versions']==summary['content_versions']
        (tmp_path/'source_discovery.json').write_bytes(raw+b' ')
        with pytest.raises(ValueError,match='discovery has changed'):build_lists(c,path)
    assert before==db.read_bytes()


def test_cli_rejects_filters_for_complete_proof_partition(proof_catalog,tmp_path):
    from project_catalog import main
    db,*_=proof_catalog
    with pytest.raises(ValueError,match='all versions'):
        main(['--db',str(db),'export','--proof-lists',str(tmp_path/'out'),'--kind','proposition'])
