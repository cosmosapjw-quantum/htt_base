from fractions import Fraction as F
import json
from pathlib import Path
out={}
# Frozen max-tail score, same three simulations, plus-one ranks.
obs=[F(99,100),F(1,10)]
sims=[[F(1,2),F(1,2)],[F(3,5),F(3,5)],[F(7,10),F(7,10)]]
plocal=[F(1+sum(row[j]>=obs[j] for row in sims),len(sims)+1) for j in range(2)]
pglobal=F(1+sum(max(row)>=max(obs) for row in sims),len(sims)+1)
assert pglobal<max(plocal)
out['NT2_A3']={'local_p':list(map(str,plocal)),'global_p':str(pglobal),'claimed_global_ge_max_local':False,'iid_uniform_analytic_global_p':str(1-obs[0]**2)}
# Signed common-state ratio. N=-2+s, D=2-s on [0,1], N/D=-1.
values=[(F(-2)+s)/(F(2)-s) for s in [F(0),F(1,4),F(1,2),F(3,4),F(1)]]
naive=[n/d for n in [F(-2),F(-1)] for d in [F(1),F(2)]]
assert all(v==-1 for v in values)
assert max(naive)==F(-1,2) and max(values)==F(-1)
out['T2_prime']={'joint_ratio_identity':'(-2+s)/(2-s)=-1 for every s in [0,1]','joint_upper':'-1','naive_upper':str(max(naive)),'cN_times_cD':'-1','claimed_upper_equality_iff_nonpositive_product':False}
# Counterexample to convergence for any decreasing r_l: r_l=1/l.
# (2l+1)/2 r_l^2 = 1/l + 1/(2l^2) >= 1/l.
for ell in range(4,100):
 assert F(2*ell+1,2*ell*ell)>=F(1,ell)
out['NT2_A2']={'response':'r_l=1/l -> 0','term':'1/l + 1/(2*l*l)','divergence_proof':'harmonic comparison','finite_identity_checks':96,'convergence_from_decay_alone':False}
Path('research_review/EXACT_COUNTEREXAMPLES.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
