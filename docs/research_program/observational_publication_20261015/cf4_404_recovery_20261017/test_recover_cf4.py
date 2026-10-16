"""Offline focused tests, never contact external CDS or change user's Planck masks."""
import gzip
import io
import json
from pathlib import Path
from unittest.mock import patch
import pytest
import recover_cf4 as t


def row(i,width):
    return (f'{i:7d}'+'x'*(width-7)+'\n').encode()


def tsv(rows):
    return b'#CDS VizieR export\n1PGC\tRA\tDE\tDM\tVh\tMethod\n---\t---\t---\t---\t---\t---\n' + b''.join(f'{i}\t1\t2\t31.2\t2000\tTF\n'.encode() for i in range(1,rows+1))


def test_urls_and_checks():
    assert t.vizier_url(t.VIZIER_BASES[0],'groups').endswith('J/ApJ/944/94/groups&-out.max=unlimited&-out.all')
    assert t.RECS['table2']==(55877,190)
    assert t.RECS['table3']==(38053,190)


def test_check_target_escape(tmp_path):
    with pytest.raises(ValueError):t.check_target(tmp_path,'../../secrets')
    with pytest.raises(ValueError):t.check_target(tmp_path,'/absolute')
    s=tmp_path/'sym';s.symlink_to(tmp_path.parent, target_is_directory=True)
    with pytest.raises(ValueError):t.check_target(tmp_path,'sym/bad')


def test_tls_and_redirect_restriction():
    for u in ['http://vizier.cds.unistra.fr/x','https://evil.org/evil', 'https://u@vizier.cds.unistra.fr/x']:
        with pytest.raises(ValueError):t.check_url(u)


def test_fixed_width_valid(tmp_path,monkeypatch):
    monkeypatch.setitem(t.RECS,'table3',(3,190))
    p=tmp_path/'table3.dat';p.write_bytes(b''.join(row(i,190) for i in (1,2,3)))
    result=t.fixed_width_rows(p,'table3')
    assert result['rows']==3 and result['lrecl_max']==190


def test_fixed_width_rejects_bad_rows(tmp_path,monkeypatch):
    monkeypatch.setitem(t.RECS,'table4',(2,157))
    p=tmp_path/'table4.dat'
    p.write_bytes(row(1,157))
    with pytest.raises(ValueError):t.fixed_width_rows(p,'table4')
    p.write_bytes(row(1,157)+b'ABCD'+b'x'*149+b'\n')
    with pytest.raises(ValueError):t.fixed_width_rows(p,'table4')


def test_gzip_extract_only_after_validation(tmp_path,monkeypatch):
    monkeypatch.setitem(t.RECS,'table2',(2,190))
    gz=tmp_path/'table2.dat.gz';gz.write_bytes(gzip.compress(row(1,190)+row(2,190)))
    dat=tmp_path/'table2.dat'
    assert t.decode_gzip_into(gz,dat,'table2')['rows']==2
    assert dat.read_bytes().startswith(b'      1')
    with pytest.raises(FileExistsError):t.decode_gzip_into(gz,dat,'table2')


def test_gzip_refuses_html(tmp_path,monkeypatch):
    monkeypatch.setitem(t.RECS,'table2',(2,190))
    gz=tmp_path/'table2.dat.gz';gz.write_bytes(b'<!doctype html><title>404</title>')
    with pytest.raises(OSError):t.decode_gzip_into(gz,tmp_path/'table2.dat','table2')
    assert not (tmp_path/'table2.dat').exists()


def test_receipt_preserves_planck_data(tmp_path,monkeypatch):
    monkeypatch.setitem(t.RECS,'table3',(1,190))
    m=tmp_path/'planck/PR3/masks/x.fits';m.parent.mkdir(parents=True);m.write_bytes(b'SIMPLE  = ORIGINAL')
    gz=tmp_path/t.ROOT/'table3.dat.gz';gz.parent.mkdir(parents=True);gz.write_bytes(gzip.compress(row(5,190)))
    status=t.recover_raw(tmp_path,'table3')
    assert status['status']=='RAW_RECOVERED_FROM_EXISTING_GZIP'
    rec=json.loads((tmp_path/'provenance/DOWNLOAD_RECEIPTS.json').read_text())
    assert rec['cf4_table3_dat']['status']=='downloaded'
    assert m.read_bytes()==b'SIMPLE  = ORIGINAL'
    status=t.recover_raw(tmp_path,'table3')
    assert status['status']=='RAW_ALREADY_VERIFIED'


def test_vizier_row_and_metadata(tmp_path):
    p=tmp_path/'groups.tsv';p.write_bytes(tsv(38053))
    d=t.vizier_rows(p,'groups')
    assert d['rows']==38053 and d['format']=='VIZIER_TSV_NOT_FIXED_WIDTH_ORIGINAL'
    p.write_bytes(tsv(38052))
    with pytest.raises(ValueError):t.vizier_rows(p,'groups')


def test_vizier_table2_expected_count(tmp_path):
    p=tmp_path/'table2.tsv';p.write_bytes(tsv(55877))
    assert t.vizier_rows(p,'table2')['rows']==55877


def test_fetch_does_not_retry_404(tmp_path,monkeypatch):
    from urllib.error import HTTPError
    n=[]
    def bad(*a,**k):
        n.append(1)
        raise HTTPError('https://vizier.cds.unistra.fr/x',404,'missing',{},None)
    monkeypatch.setattr(t.request,'urlopen',bad)
    with pytest.raises(HTTPError):t.fetch('https://vizier.cds.unistra.fr/x',tmp_path/'src',retries=4)
    assert len(n)==1


def test_offline_dry_run_doesnt_create_root(tmp_path):
    root=tmp_path/'absent'
    assert t.main(['--root',str(root),'--dry-run'])==0
    assert not root.exists()


def test_source_mismatch_preserves_existing(tmp_path):
    p=tmp_path/t.ROOT/'vizier/table2.tsv';p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(tsv(55877))
    with pytest.raises(ValueError):t.recover_vizier(tmp_path,'table2')
    assert p.is_file()


def test_only_vizier_marks_no_raw(tmp_path,monkeypatch):
    monkeypatch.setattr(t, 'recover_vizier',lambda root,table,timeout:{'status':'VIZIER_REPRESENTATION_VERIFIED','rows':55877 if table=='table2' else 38053})
    assert t.main(['--root',str(tmp_path),'--mode','vizier-only'])==0
    audit=json.loads((tmp_path/'provenance/CF4_RECOVERY_AUDIT.json').read_text())
    assert not audit['fixed_width_complete'] and audit['vizier_alternative_complete']
    assert not (tmp_path/t.ROOT/'table2.dat').exists()
