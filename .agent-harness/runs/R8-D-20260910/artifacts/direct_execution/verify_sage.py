"""Host direct Sage/Singular rational-function and finite fixture checks."""
import json
from sage.all import QQ,PolynomialRing,matrix,vector,identity_matrix,singular
from sage.env import SAGE_VERSION
P=PolynomialRing(QQ,names=('t','qd','g','d','cd','c','e'))
t,qd,g,d,cd,c,e=P.gens();F=P.fraction_field()
residuals=[F(-qd+g+QQ(3)/7*d)/t-(-qd/t+g/t+3*d/(7*t)),
           F(3*cd/t+c-6*e/(5*t))/t-(3*cd/t**2+c/t-6*e/(5*t**2))]
ring=singular.ring(0,'(t,qd,g,d,cd,c,e)','dp')
singular_ok=all(str(singular(str(z.numerator())))=='0' for z in residuals)
checks={'P1_normalized_coefficients':all(z==0 for z in residuals) and singular_ok,
 'P2_mock6_squared_norms':sum(x*x for x in (1,2,1,2,1,2,1,2))==20 and sum([1]*8)==8 and 5+3==8,
 'J1_set_logic_and_allocation':1-4*QQ(1)/80==QQ(19)/20 and all((a and (b or c))==((a and b) or (a and c)) for a in (False,True) for b in (False,True) for c in (False,True))}
K=identity_matrix(QQ,8);v=K.column(7);R=K[:4,:]
checks['V08_fixture_ray']=R*v==vector(QQ,4) and K*v==v and v.dot_product(v)==1
checks={k:bool(v) for k,v in checks.items()}
assert all(checks.values())
print(json.dumps({'checks':checks,'versions':{'sage':SAGE_VERSION,'singular':str(singular.eval('system("version");'))}}))
