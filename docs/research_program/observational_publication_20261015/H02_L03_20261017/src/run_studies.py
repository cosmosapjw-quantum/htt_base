"""CLI to recompute two independently source-locked, prephysical HTT results."""
import sys,json,argparse,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from h02_calibration_fisher import diagnostics as h02
from l03_paired_scan import diagnostics as l03

def write_json(path,obj):
    text=json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding='utf-8')
    return hashlib.sha256(text.encode()).hexdigest()

def main():
    r=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser()
    p.add_argument('--cf4-npz',type=Path,default=r/'inputs/selected_source_observables.npz')
    p.add_argument('--planck-bank',type=Path,default=r/'inputs/processing_coefficients.npz')
    p.add_argument('--output-dir',type=Path,default=r/'results')
    a=p.parse_args()
    out={}
    for k,result in [('H02',h02(a.cf4_npz)),('L03',l03(a.planck_bank))]:
        path=a.output_dir/('H02_ACTUAL_SELECTED_SOURCE_FISHER.json' if k=='H02' else 'L03_ACTUAL_SOURCE_PAIRED_SCAN.json')
        out[k]={'file':str(path),'sha256':write_json(path,result)}
    print(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2))
if __name__=='__main__':main()
