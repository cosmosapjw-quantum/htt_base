"""Read-only independent P5 checks; no producer compute/metrics reuse."""
import os
os.environ['MPLCONFIGDIR']='/mnt/extdrive/workdir/htt_open_data/r35_p5_fresh_independent_review/mplconfig'
import csv, json, math, hashlib, importlib.util
from decimal import Decimal, localcontext
from fractions import Fraction as F
from pathlib import Path
import numpy as np
P=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-07-P5-ALGEBRA/report')
OUT=Path('/mnt/extdrive/workdir/htt_open_data/r35_p5_fresh_independent_review')
data=np.load(P/'arrays.npz',allow_pickle=False)
results={'array_sha256':hashlib.sha256((P/'arrays.npz').read_bytes()).hexdigest(),'checks':{}}
def check(name,condition,detail=None):
    results['checks'][name]={'pass':bool(condition),'detail':detail}
    assert condition,(name,detail)
def close(name,a,b,tol=2e-12):
    err=float(np.max(np.abs(np.asarray(a)-np.asarray(b))))
    check(name,np.isfinite(err) and err<=tol,{'max_abs_error':err,'tolerance':tol})

# Solve at fixed curvature through flux/normal-energy ratio, independently of
# the producer's rest-density quadratic.  Scale that boundary by u afterwards.
def image(K,beta,w,u):
    B=(1+w*beta**2)/(1-beta**2)
    r=(1+w)*np.abs(beta)/(1+w*beta**2)
    za=r*(1-K)/(np.sqrt(K+r*r*(1-K))+np.sqrt(K))
    Ommax=(1-K-za*za)/B
    Om=u*Ommax; z=u*np.sign(beta)*za
    En=u*(1-K-za*za); El=En-Om
    return dict(Omega_max=Ommax,Omega=Om,z_s=z,Sigma2=z*z,Omega_n=En,
                Omega_Lambda=1-K-z*z-En,E_tilt=El,pressure=w*Om+El/3)
diag=np.diag([-1.,-1.,2.])
for prefix,K,b,w,u in [
    ('joint',data['joint_K'],data['joint_beta'],data['joint_w'],data['joint_u']),
    ('domain',data['domain_K'][None,None,:],data['domain_beta'][None,:,None],data['domain_w'][:,None,None],1.)]:
    expected=image(K,b,w,u)
    for key,value in expected.items():
        if prefix+'_'+key in data: close(prefix+'_'+key,data[prefix+'_'+key],value)
    close(prefix+'_shear',data[prefix+'_shear'],expected['z_s'][...,None,None]*diag)
    close(prefix+'_pi',data[prefix+'_pi'],expected['E_tilt'][...,None,None]*diag/3)
    f=np.zeros(expected['z_s'].shape+(3,));f[...,2]=2*np.sqrt(K)*expected['z_s']
    close(prefix+'_flux',data[prefix+'_flux'],f)
    close(prefix+'_stf_shear',np.trace(data[prefix+'_shear'],axis1=-2,axis2=-1),0)
    close(prefix+'_stf_stress',np.trace(data[prefix+'_pi'],axis1=-2,axis2=-1),0)
    close(prefix+'_hamiltonian',K+data[prefix+'_Sigma2']+data[prefix+'_Omega_n']+data[prefix+'_Omega_Lambda'],1)
check('joint_count',data['joint_K'].size==280,int(data['joint_K'].size))
check('heatmap_count',data['domain_Sigma2'].size==58282,int(data['domain_Sigma2'].size))
check('joint_parameter_grid',set(zip(data['joint_K'],data['joint_w'],data['joint_beta'],data['joint_u']))==
      {(k,w,b,u) for k in (.05,.2,.5,.8) for w in (0.,1/3) for b in (0.,-.2,.2,-.5,.5,-.8,.8) for u in (0.,.25,.5,.75,1.)})
close('K_grid',data['domain_K'],.02+.96*np.arange(161)/160)
close('beta_grid',data['domain_beta'],-.9+1.8*np.arange(181)/180)
vac=data['joint_Omega']==0
check('vacuum_physical_velocity_undefined',np.all(np.isnan(data['joint_beta_physical'][vac])) and np.all(data['joint_matter_velocity_status'][vac]=='UNDEFINED_ABSENT_MATTER'))
check('vacuum_exact_zero_tensors',np.all(data['joint_shear'][vac]==0) and np.all(data['joint_pi'][vac]==0) and np.all(data['joint_flux'][vac]==0))
check('matter_vorticity_undefined',np.all(np.isnan(data['joint_matter_vorticity'])) and np.all(data['joint_matter_vorticity_status']=='NOT_DETERMINED'))
check('normal_vorticity_zero',np.all(data['joint_normal_vorticity']==0))

# Fixed-density bound found by monotone bisection of the original Hamiltonian,
# using a different independent variable from the closed-form t root.
K=data['fixed_K'][None,None,:];w=data['fixed_w'][:,None,None];Om=data['fixed_Omega'][None,:,None]
valid=np.broadcast_to(K+Om<=1,data['fixed_beta_bound'].shape)
lo=np.zeros(valid.shape);hi=np.full(valid.shape,np.nextafter(1.,0.))
for _ in range(80):
    mid=(lo+hi)/2;g2=1/(1-mid*mid)
    z=(1+w)*Om*g2*mid/(2*np.sqrt(K))
    energy=K+z*z+Om*((1+w)*g2-w)
    lo=np.where(energy<=1,mid,lo);hi=np.where(energy>1,mid,hi)
close('fixed_bound_bisection',data['fixed_beta_bound'][valid],((lo+hi)/2)[valid],5e-12)
check('fixed_empty_mask',np.all(np.isnan(data['fixed_beta_bound'][~valid])) and np.all(data['fixed_status'][~valid]=='EMPTY_DOMAIN'),int(np.count_nonzero(~valid)))
check('fixed_tuple_count',len(data['fixed_boundary_K'])==1300,len(data['fixed_boundary_K']))
K=data['fixed_boundary_K'];b=data['fixed_boundary_beta'];w=data['fixed_boundary_w'];Om=data['fixed_boundary_Omega'];g2=1/(1-b*b)
z=(1+w)*Om*g2*b/(2*np.sqrt(K));E=(1+w)*Om*(g2-1)
close('fixed_z',data['fixed_boundary_z_s'],z)
close('fixed_shear',data['fixed_boundary_shear'],z[:,None,None]*diag)
close('fixed_pi',data['fixed_boundary_pi'],E[:,None,None]*diag/3)
close('fixed_boundary_hamiltonian',K+z*z+Om*((1+w)*g2-w),1,5e-12)

# All scalar/vector/tensor CSV values must agree with saved numerical carriers.
rows=list(csv.DictReader((P/'joint_image.csv').open()))
check('joint_csv_count',len(rows)==280)
for key in ('K','w','beta','u','Omega','Omega_max','z_s','Sigma2','Omega_n','Omega_Lambda','E_tilt','pressure'):
    close('csv_'+key,np.array([float(x[key]) for x in rows]),data['joint_'+key],0)
for key in ('shear','pi'):
    got=np.array([[[float(row[key+'_'+i+j]) for j in 'xyz'] for i in 'xyz'] for row in rows])
    close('csv_'+key,got,data['joint_'+key],0)
for key in ('flux','beta_chart'):
    got=np.array([[float(row[key+'_'+i]) for i in 'xyz'] for row in rows]);close('csv_'+key,got,data['joint_'+key],0)
selected=list(csv.DictReader((P/'generated_table.csv').open()))
ix=np.where((data['joint_u']==1)&(data['joint_beta']==.5))[0]
check('table_rows',len(selected)==len(ix)==8)
for key in selected[0]:
    expected=np.array([float(format(x,'.10g')) for x in data['joint_'+key][ix]])
    close('table_'+key,[float(row[key]) for row in selected],expected,0)

# Decimal probes of the actual closed form cover branches outside the plot
# grids without approaching binary64 overflow/underflow.
spec=importlib.util.spec_from_file_location('p5_consumer_readonly',P/'build_product.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
max_dec=0.;cases=[]
with localcontext() as ctx:
    ctx.prec=80
    one=Decimal(1)
    for k in ('0.000001','0.02','0.2','0.999999','1'):
      for b in ('0','-.5','.5','-.999999','.999999'):
       for w in ('0',str(1/3),'1'):
        for u in ('0','.5','1'):
            K,beta,W,U=map(Decimal,(k,b,w,u));A=(1+W)**2*beta**2/(4*K*(1-beta**2)**2);B=(1+W*beta**2)/(1-beta**2);D=1-K
            Om=U*2*D/(B+(B*B+4*A*D).sqrt());zs=(1+W)*Om*beta/(2*K.sqrt()*(1-beta**2));En=B*Om;La=D-En-zs*zs
            got=mod.tuple_at(float(K),float(beta),float(W),float(U))
            vals={'Omega':Om,'z_s':zs,'Sigma2':zs*zs,'Omega_n':En,'Omega_Lambda':La}
            err=max(abs(got[key]-float(val)) for key,val in vals.items());max_dec=max(max_dec,err)
            assert err<2e-12,(k,b,w,u,err)
            if K==1: assert got['Omega']==got['z_s']==0 and got['beta_physical'] is None
            cases.append([k,b,w,u,err])
    lim=[];K=Decimal('.2');W=Decimal(1)/3
    for n in (2,4,6,8,12):
        v=1-Decimal(10)**(-n);r=(1+W)*v/(1+W*v*v)
        z=r*(1-K)/((K+r*r*(1-K)).sqrt()+K.sqrt());En=2*K.sqrt()*z/r
        B=(1+W*v*v)/(1-v*v);Om=En/B
        lim.append({'n':n,'rest_density':float(Om),'normal_energy':float(En),'shear_gap':float(1-K.sqrt()-z)})
    check('ultrarelativistic_sequence',all(x['shear_gap']>0 for x in lim) and all(lim[i+1]['shear_gap']<lim[i]['shear_gap'] and lim[i+1]['rest_density']<lim[i]['rest_density'] for i in range(4)),lim)
check('decimal_closed_form_cases',len(cases)==225,{'count':len(cases),'max_abs_error':max_dec})
invalid=[]
for idx in range(4):
  for x in (math.nan,math.inf,-math.inf):
    args=[.2,.5,1/3,.5];args[idx]=x;invalid.append((args,'OUTSIDE_DOMAIN'))
for args,status in [([0,.5,0,.5],'OUTSIDE_DOMAIN'),([-1,.5,0,.5],'OUTSIDE_DOMAIN'),([1.1,.5,0,.5],'EMPTY_DOMAIN'),([.2,1,0,.5],'OUTSIDE_DOMAIN'),([.2,-1,0,.5],'OUTSIDE_DOMAIN'),([.2,.5,-.1,.5],'OUTSIDE_DOMAIN'),([.2,.5,1.1,.5],'OUTSIDE_DOMAIN'),([.2,.5,0,-.1],'OUTSIDE_DOMAIN'),([.2,.5,0,1.1],'OUTSIDE_DOMAIN')]:invalid.append((args,status))
check('invalid_domains',all(mod.tuple_at(*args)['status']==status and bool(mod.tuple_at(*args)['reason']) for args,status in invalid),len(invalid))
check('negative_directional_expansion',mod.tuple_at(.05,-.5,0,1)['z_s']<-.5)
check('no_tilt_nonvacuum',mod.tuple_at(.2,0,1/3,.5)['Omega']==.4 and mod.tuple_at(.2,0,1/3,.5)['z_s']==0)

# Independent polynomial coefficients/rates, endpoints and full-sphere map.
alpha=F(4,5);eps=F(1,50)
check('exact_history_endpoints',(1-alpha)+alpha==1 and 1-alpha+2*alpha==F(9,5) and ((1-alpha)/2+alpha/4)==F(3,10))
t=np.arange(201)/200;L=float(eps)*diag
close('history_BA',data['B_A'],t[:,None,None]*L,2e-14)
close('history_BB',data['B_B'],((t+4*t*t)/5)[:,None,None]*L,2e-14)
close('history_rateA',data['shear_A_over_H'],np.broadcast_to(L,(201,3,3)),2e-14)
close('history_rateB',data['shear_B_over_H'],((1+8*t)/5)[:,None,None]*L,2e-14)
mu=np.arange(401)/200-1
expected=1/np.sqrt(math.exp(-.04)*(1-mu*mu)+math.exp(.08)*mu*mu)
for name in ('temperature_A','temperature_B','temperature_explicit'):close(name,data[name],expected,2e-14)
directions=np.array([[1,0,0],[0,0,1],[1,2,3],[-4,3,2],[2,-5,7]],float);directions/=np.linalg.norm(directions,axis=1)[:,None]
temps=[]
for key in ('B_A','B_B'):
    final=data[key][-1];temps.append(1/np.sqrt(np.sum(np.exp(2*np.diag(final))*directions**2,axis=1)))
close('off_axis_temperature_pair',temps[0],temps[1],2e-14)
midA=1/np.sqrt(np.sum(np.exp(2*np.diag(data['B_A'][100]))*directions**2,axis=1))
midB=1/np.sqrt(np.sum(np.exp(2*np.diag(data['B_B'][100]))*directions**2,axis=1))
check('intermediate_temperature_difference',np.max(abs(midA-midB))>0.001,float(np.max(abs(midA-midB))))
close('endpoint_sigma2',[np.sum(data['shear_A_over_H'][-1]**2)/6,np.sum(data['shear_B_over_H'][-1]**2)/6],[1/2500,81/62500],2e-14)
separation=np.linalg.norm(data['shear_B_over_H'][-1]-data['shear_A_over_H'][-1]);radius=np.arange(101)*.02/100
close('error_separation',data['error_separation'],separation,2e-14)
close('error_margin',data['error_margin'],separation-2*radius,2e-14)
check('error_statuses',np.array_equal(data['error_status'],np.where(2*radius<separation,'DISJOINT',np.where(2*radius>separation,'INTERSECT','TOUCHING'))))
check('exact_touch_expression',str(data['error_touch_expression'])=='alpha*sqrt(6)*epsilon/2' and str(data['error_touch_status'])=='TOUCHING' and data['error_touch_margin_exact']==0)
mid=(data['shear_A_over_H'][-1]+data['shear_B_over_H'][-1])/2
close('touching_midpoint_distances',[np.linalg.norm(mid-data['shear_A_over_H'][-1]),np.linalg.norm(mid-data['shear_B_over_H'][-1])],separation/2,2e-14)
results['status']='PASS';results['check_count']=len(results['checks'])
(OUT/'raw/independent_probes.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
print(json.dumps({'status':'PASS','check_count':len(results['checks']),'decimal_cases':len(cases),'decimal_max_abs_error':max_dec,'array_sha256':results['array_sha256']}))
