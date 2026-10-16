import subprocess,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_reproduce_bundled_selected_npz(tmp_path):
    import hashlib
    p=ROOT/'data/selected_source_observables.npz'
    assert hashlib.sha256(p.read_bytes()).hexdigest()=='86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c'
    cmd=[sys.executable,str(ROOT/'src/prior_selected_source_sky.py'),'--npz',str(p),'--output',str(tmp_path/'out.json')]
    q=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    out=json.loads((tmp_path/'out.json').read_text())
    assert out['selected_source_count']==35970
    assert out['rank_angular_after_calibration']==8
