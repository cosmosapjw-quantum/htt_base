import inspect
import numpy as np
import scipy, sys
from scripts.r97 import bianchi_coupled_m_transport as c
print('python numpy scipy',sys.version.split()[0],np.__version__,scipy.__version__)
print('canonical_oracle',c.verify_angular_quadrature_oracle())
s=c._build_default_admissible_state_for_family('VII_h')
print('state_H, tuple(n.a)',s.H,s.algebra.n@s.algebra.a)
print('constraints',s.constraints)
src=inspect.getsource(c.verify_angular_quadrature_oracle)
lines=src.splitlines()
i=next(i for i,l in enumerate(lines) if l.startswith('    alg_a ='))
j=next(i for i,l in enumerate(lines) if l.startswith('    sig_gen ='))
lines[i:j+1]=['    alg_a = st.algebra.a / st.H','    alg_n = st.algebra.n / st.H','    sig_gen = st.sigma_ab / st.H']
ns=dict(vars(c),st=s)
exec('\n'.join(lines),ns)
print('admissible_vii_h_oracle',ns['verify_angular_quadrature_oracle']())
