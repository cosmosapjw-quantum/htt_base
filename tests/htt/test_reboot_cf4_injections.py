import importlib.util,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
import run_reboot_cf4_injections as m

def test_missing_hessian_interval_cannot_pass_numerical_gate():
 rows=[{'status':'RESOLVED','fit':{'best':{'success':True}},'interval_status':'GAUSSIAN_WALD_PROXY'}for _ in range(32)]
 assert m.numerical_status(1e-10,rows)=='PASS_SCOPED'
 rows[3]['interval_status']='UNAVAILABLE'
 assert m.numerical_status(1e-10,rows)=='HOLD_NUMERICAL_CHECKS'
 rows[3]['interval_status']='GAUSSIAN_WALD_PROXY'
 rows[7]['status']='QUADRATURE_UNRESOLVED'
 assert m.numerical_status(1e-10,rows)=='HOLD_NUMERICAL_CHECKS'
 assert m.numerical_status(1e-3,rows)=='HOLD_NUMERICAL_CHECKS'
