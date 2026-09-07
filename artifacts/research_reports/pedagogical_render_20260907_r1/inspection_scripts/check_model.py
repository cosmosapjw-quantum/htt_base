from runner import *
from fractions import Fraction as Q
from itertools import product,combinations_with_replacement,permutations
from math import prod
# Normalised angular mean of a monomial on S^2 (Lemma 3.2).
def df(n):return prod(range(n,0,-2))
def avg(indices):
 powers=[indices.count(i) for i in range(3)]
 return Q(0) if any(p%2 for p in powers) else Q(prod(df(p-1) for p in powers),df(sum(powers)+1))
def delta(a,b):return int(a==b)
checks=[]
# A spanning set of symmetric inputs is projected to STF, so checking each checks all STF inputs by linearity.
for order in [1,2,3]:
 for independent in combinations_with_replacement(range(3),order):
  sym={p:Q(1) for p in set(permutations(independent))}
  tensor={ind:sym.get(ind,Q(0)) for ind in product(range(3),repeat=order)}
  if order==2:
   tr=sum(tensor[i,i] for i in range(3));tensor={ind:x-Q(delta(*ind),3)*tr for ind,x in tensor.items()}
  if order==3:
   tr=[sum(tensor[i,j,j] for j in range(3)) for i in range(3)]
   tensor={ind:x-Q(1,5)*(delta(ind[0],ind[1])*tr[ind[2]]+delta(ind[0],ind[2])*tr[ind[1]]+delta(ind[1],ind[2])*tr[ind[0]]) for ind,x in tensor.items()}
  for target in product(range(3),repeat=order):
   value=4*sum((a*avg(list(source)+list(target)) for source,a in tensor.items()),Q(0))
   # traces of the target moment vanish against the STF source; source/target ranks agree.
   factor={1:Q(4,3),2:Q(8,15),3:Q(8,35)}[order]
   assert value==factor*tensor[target]
  checks.append({'order':order,'symmetric_seed':independent,'coefficient':str(factor),'all_target_components_equal':True})
# Third angular moment in a pure dipole brightness 3 q.e, normalised to flux q.
for a,b,c,k in product(range(3),repeat=4):
 actual=3*avg([a,b,c,k]);expected=Q(1,5)*(delta(a,b)*delta(c,k)+delta(a,c)*delta(b,k)+delta(b,c)*delta(a,k));assert actual==expected
# Streaming STF subtraction gives 1/5 (D_a q_b + D_b q_a) - 2/15 h_ab div q = 2/5 D_<a q_b>.
assert Q(2,5)*Q(4,3)/Q(8,15)==1
assert Q(9,4)*Q(4,3)*(Q(4,3)+Q(5,3))==9
assert Q(9,4)*Q(4,3)==3
assert Q(9,4)*Q(8,15)==Q(6,5)
assert Q(8,3)+Q(1,3)==3 and Q(9,3)+Q(3,9)==Q(10,3)
assert Q(6,5)*Q(1,9)==Q(2,15)
write('radiation-model-check.json',{'overall':'PASS_STATED_FIRST_ORDER_MODEL_CORRESPONDENCE','method':'Exact Fraction angular-moment contractions on a spanning symmetric basis followed by coefficient arithmetic; source derivation and commutators read separately','spanning_seed_checks':checks,'third_moment_component_checks':81,'streaming_coefficient':'2/5','direct_shear_dipole_envelope_coefficient':'1','conventional_shear_dipole_coefficient':'5 (conservative weakening)','octupole_divergence_factor':'sqrt(3); resulting 3 sqrt(3)/7 <= 9/7','vorticity_coefficients':['9','3','6/5'],'second_derivative_operator':r'D_[a D^c vartheta_b]c','uncontracted_hessian_factor_one_claimed':False,'physical_assumptions':'geodesic collisionless Planck brightness; first-order nearly isotropic system; positive density and expansion; all-domain stated derivative controls; background commutator used to retained order','strictness':'Weak bounds produce <=; strict displayed main-text bounds require explicit slack as stated by assembled Model M and Appendix E.7','finite_amplitude_nonlinear_error_bound':False,'general_nonlinear_cosmology_theorem':False,'old_cas_or_r2_replayed':False})
print('PASS exact angular contractions and rational coefficients; no nonlinear or observational claim')
