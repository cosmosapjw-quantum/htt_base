#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np

# These scripts are run as files and are also loaded by path from repo-root
# tests, so the sibling import needs this directory on sys.path either way.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from external_store import ensure_data_dir
try:
    import camb
except Exception as e:
    raise SystemExit("CAMB is not installed in the current Python. Activate the venv from bootstrap_env.sh or run: python -m pip install camb==1.6.6") from e

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--params-json', required=True)
    ap.add_argument('--outdir', default='./workdir/compact_products')
    args = ap.parse_args()
    outdir = Path(args.outdir).expanduser().resolve()
    ensure_data_dir(outdir)
    pars = json.loads(Path(args.params_json).read_text())
    cp = camb.CAMBparams()
    cp.set_cosmology(H0=pars['H0'], ombh2=pars['ombh2'], omch2=pars['omch2'], tau=pars['tau'], mnu=pars.get('mnu',0.06), omk=pars.get('omk',0.0), TCMB=pars.get('T_CMB',2.7255))
    cp.InitPower.set_params(As=pars['As'], ns=pars['ns'])
    cp.set_for_lmax(pars.get('lmax',4096), lens_potential_accuracy=pars.get('lens_potential_accuracy',4))
    cp.Want_CMB = True; cp.Want_CMB_lensing = True; cp.DoLensing = True; cp.WantTensors = False
    results = camb.get_results(cp)
    lensed = results.get_lensed_scalar_cls(CMB_unit='muK', raw_cl=False)
    lens_potential = results.get_lens_potential_cls(lmax=pars.get('lmax',4096), CMB_unit='muK', raw_cl=False)
    np.savez(outdir/'camb_planck2018_lensing_refs.npz', ell_cmb=np.arange(lensed.shape[0]), Dl_TT=lensed[:,0], Dl_EE=lensed[:,1], Dl_BB=lensed[:,2], Dl_TE=lensed[:,3], ell_pp=np.arange(lens_potential.shape[0]), lens_potential_cls=lens_potential, input_params=json.dumps(pars, sort_keys=True))
    print(f"[ok] wrote {outdir/'camb_planck2018_lensing_refs.npz'}")

if __name__ == '__main__':
    main()
