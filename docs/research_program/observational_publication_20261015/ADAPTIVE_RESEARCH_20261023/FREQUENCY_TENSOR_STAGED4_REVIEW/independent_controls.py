"""Small independent read-only controls; never runs native production transforms."""
import time
START = time.monotonic()
import hashlib, itertools, json, math, os, pathlib, resource, sys
import numpy as np
import scipy
from scipy.special import sph_harm_y
import healpy as hp
import astropy
from astropy.io import fits
from threadpoolctl import threadpool_info

P=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r25_frequency_tensor_staged4')
R=pathlib.Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
CFG=R/'docs/research_program/observational_publication_20261015/ADAPTIVE_RESEARCH_20261023/R25-PR3-STAGED4-TENSOR-CONTRAST_INPUT.json'
sys.path.insert(0,str(P))
import compute

def digest(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
cfg=json.loads(CFG.read_text()); manifest=json.loads((P/'MANIFEST.json').read_text())
assert digest(CFG)=='ff5db155e8266b4a913ceb48e69b60d6a6356928940305cd2d28d82fc3f690e5'
assert digest(P/'MANIFEST.json')=='e05e9aefcbee3382778bc2a74e4a4617fed311fd5a1ac7dc78ef4abe45a8e175'
for name,seal in manifest['files_sha256'].items(): assert digest(P/name)==seal,name
assert digest(R/cfg['carrier']['tensor_decoder']['path'])==cfg['carrier']['tensor_decoder']['sha256']
pool=threadpool_info()
assert all(x['num_threads']==1 for x in pool),pool

z=np.load(P/'FULL_CARRIER_AND_CONTRASTS.npz',allow_pickle=False)
c=z['carrier_canonical_96']; contrasts=z['pair_contrasts_canonical_6x24']; bands=[30,44,70,100]
assert c.shape==(4,24) and np.isfinite(c).all()
assert z['bands_GHz'].tolist()==bands
pairs=list(itertools.combinations(bands,2))
assert z['pair_bands_GHz'].tolist()==[list(x) for x in pairs]
for i,(a,b) in enumerate(pairs): assert np.array_equal(contrasts[i],c[bands.index(a)]-c[bands.index(b)])
assert np.allclose(z['Q_computational'],np.linalg.norm(c/1e-5,axis=1),rtol=2e-15,atol=0)

support=np.load(P/'COMMON_SUPPORT_S4.npz',allow_pickle=False)
base=np.load(R/cfg['support']['base']['path'],allow_pickle=False)
assert np.array_equal(support['selected_mask_ring64'],base['selected_mask_ring64'])
n2r=hp.nest2ring(64,np.arange(49152)); sn=support['selected_mask_ring64'][n2r]
intersection=sn.copy()
for b in bands: intersection &= support[f'valid_{b}_nest64']
assert np.array_equal(intersection,support['s4_mask_ring64'][n2r])
assert np.array_equal(support['retained_ring64'],np.flatnonzero(support['s4_mask_ring64']))
assert np.array_equal(support['removed_ring64'],np.flatnonzero(support['selected_mask_ring64']&~support['s4_mask_ring64']))
assert intersection.sum()==30021

# Independent Cartesian polynomial vs scipy spherical harmonics checks, all blocks.
rng=np.random.default_rng(20261023)
vec=rng.normal(size=(83,3));vec/=np.linalg.norm(vec,axis=1)[:,None]
th=np.arccos(vec[:,2]);ph=np.mod(np.arctan2(vec[:,1],vec[:,0]),2*np.pi)
stfmax=0.; symmax=0.; tracemax=0.
for values,prefix in [(c,''),(contrasts,'pair_')]:
 for row,x in enumerate(values):
  for start,ell,name in [(0,2,'E2'),(5,3,'E3'),(12,2,'B2'),(17,3,'B3')]:
   block=x[start:start+2*ell+1];target=block[0]*sph_harm_y(ell,0,th,ph).real
   for m in range(1,ell+1):
    a=(block[2*m-1]-1j*block[2*m])/np.sqrt(2)
    target+=2*np.real(a*sph_harm_y(ell,m,th,ph))
   tensor=z[prefix+name+'_stf'][row]
   actual=np.einsum('ij,ni,nj->n',tensor,vec,vec) if ell==2 else np.einsum('ijk,ni,nj,nk->n',tensor,vec,vec,vec)
   stfmax=max(stfmax,float(np.max(np.abs(actual-target))))
   for perm in itertools.permutations(range(ell)): symmax=max(symmax,float(np.max(np.abs(tensor-tensor.transpose(perm)))))
   tracemax=max(tracemax,float(np.max(np.abs(np.trace(tensor,axis1=0,axis2=1)))))
assert stfmax<1e-18 and symmax<1e-18 and tracemax<1e-18

# Independent spin harmonics via twice applying eth/bar-eth to scalar Y.
# No Wigner-d recurrence or production spin_y is used to construct the oracle.
nside=16;n=hp.nside2npix(nside);pixels=np.arange(n)
theta,phi=hp.pix2ang(nside,pixels)
cs=1/np.sin(theta);cot=np.cos(theta)*cs
yp={};ym={}
for ell in (2,3):
 for m in range(-ell,ell+1):
  y,d,h=sph_harm_y(ell,m,theta,phi,diff_n=2)
  scale=math.sqrt((ell-1)*ell*(ell+1)*(ell+2))
  yp[ell,m]=(h[:,0,0]-(2*m*cs+cot)*d[:,0]+(m*m*cs*cs+2*m*cs*cot)*y)/scale
  ym[ell,m]=(h[:,0,0]+(2*m*cs-cot)*d[:,0]+(m*m*cs*cs-2*m*cs*cot)*y)/scale
analytic20=math.sqrt(15/(32*math.pi))*np.sin(theta)**2
assert np.max(np.abs(yp[2,0]-analytic20))<2e-15
mask=((pixels*37)%113)>24
antip=hp.ang2pix(nside,np.pi-theta,np.mod(phi+np.pi,2*np.pi))
assert np.array_equal(antip[antip],pixels)

def build_alms(x):
 e=np.zeros(10,complex);b=np.zeros(10,complex)
 for off,ell,arr in [(0,2,e),(5,3,e),(12,2,b),(17,3,b)]:
  arr[hp.Alm.getidx(3,ell,0)]=x[off]
  for m in range(1,ell+1): arr[hp.Alm.getidx(3,ell,m)]=(x[off+2*m-1]-1j*x[off+2*m])/np.sqrt(2)
 return e,b

def pack(e,b):
 return np.array([v for arr in (e,b) for ell in (2,3) for m in range(ell+1)
                  for v in ([arr[hp.Alm.getidx(3,ell,m)].real] if m==0 else [np.sqrt(2)*arr[hp.Alm.getidx(3,ell,m)].real,-np.sqrt(2)*arr[hp.Alm.getidx(3,ell,m)].imag])])

def field(x):
 e,b=build_alms(x);zp=np.zeros(n,complex);zm=np.zeros(n,complex)
 for ell in (2,3):
  for m in range(-ell,ell+1):
   am=abs(m);ee=e[hp.Alm.getidx(3,ell,am)];bb=b[hp.Alm.getidx(3,ell,am)]
   if m<0:ee=(-1)**m*ee.conjugate();bb=(-1)**m*bb.conjugate()
   zp-= (ee+1j*bb)*yp[ell,m];zm-=(ee-1j*bb)*ym[ell,m]
 q=(zp+zm)/2;u=(zp-zm)/(2j)
 assert max(np.max(np.abs(q.imag)),np.max(np.abs(u.imag)))<1e-18
 return q.real,u.real

def quadrature(q,u):
 e=np.zeros(10,complex);b=np.zeros(10,complex)
 for ell in (2,3):
  for m in range(ell+1):
   aplus=4*np.pi/n*np.vdot(yp[ell,m],q+1j*u)
   aminus=4*np.pi/n*np.vdot(ym[ell,m],q-1j*u)
   k=hp.Alm.getidx(3,ell,m);e[k]=-(aplus+aminus)/2;b[k]=.5j*(aplus-aminus)
 return pack(e,b)

max_synthesis=0.;max_projection=0.;max_parity=0.;max_chunk=0.
fixture=np.vstack([np.eye(24),np.sin(np.arange(24)+.3),np.cos(np.arange(24)*1.7)])*1e-5
for j,x in enumerate(fixture):
 q,u=field(x);hq,hu=hp.alm2map_spin(build_alms(x),nside,spin=2,lmax=3,mmax=3)
 max_synthesis=max(max_synthesis,float(np.max(np.abs(q-hq))),float(np.max(np.abs(u-hu))))
 q=np.where(mask,q,0);u=np.where(mask,u,0)
 measured=pack(*hp.map2alm_spin([q,u],spin=2,lmax=3,mmax=3));expected=quadrature(q,u)
 max_projection=max(max_projection,float(np.max(np.abs(measured-expected))))
 p=pack(*hp.map2alm_spin([q[antip],-u[antip]],spin=2,lmax=3,mmax=3))
 parity=np.r_[np.ones(5),-np.ones(7),-np.ones(5),np.ones(7)]
 max_parity=max(max_parity,float(np.max(np.abs(p-parity*measured))))
 if j>=24:
  a=compute.low_sum(q,u,nside,chunk=97);b=compute.low_sum(q,u,nside,chunk=509)
  max_chunk=max(max_chunk,float(np.max(np.abs(compute.canonical_grid(*a[:2])-compute.canonical_grid(*b[:2])))))
 assert np.allclose(measured,expected,rtol=1e-9,atol=1e-12)
assert max_synthesis<1e-17 and max_parity<1e-17 and max_chunk<1e-17
v=np.zeros(24);v[2]=-np.sqrt(2)
assert abs(compute.decode(v)[0][1,2]-math.sqrt(15/(8*math.pi)))<1e-15

# Both Stokes fields: exact native sentinel, neighbours, NaN and infinities.
sent=np.float32(-1.6375e30);near=np.nextafter(sent,np.float32(0))
q=np.array([1,sent,np.nan,np.inf,-np.inf,near,1,1,1],dtype=np.float32)
u=np.array([2,2,2,2,2,2,sent,np.nan,np.inf],dtype=np.float32)
ok=np.isfinite(q)&np.isfinite(u)&(q!=sent)&(u!=sent)
assert ok.tolist()==[True,False,False,False,False,True,False,False,False]
assert np.isfinite(np.where(ok,q,0)).all() and np.isfinite(np.where(ok,u,0)).all()

products=[]
for product in cfg['input_products']:
 path=pathlib.Path(product['path']);band=product['band_GHz'];ns=product['native_nside']
 assert path.stat().st_size==product['size_bytes']
 for key in ('receipt','header_metadata'):assert digest(product[key]['path'])==product[key]['sha256']
 rec=json.loads(pathlib.Path(product['receipt']['path']).read_text())
 assert rec['local_sha256']==product['sha256'] and rec['local_byte_count']==product['size_bytes']
 assert rec['filename']==path.name and rec['final_url']==product['source_url']
 with fits.open(path,memmap=True,lazy_load_hdus=True) as hdus:
  h=hdus[1].header
  assert h['ORDERING']=='NESTED' and h['NSIDE']==ns and h['COORDSYS']=='GALACTIC'
  pol='POLCCONV' if band==100 else 'POLCONV';assert h[pol]=='COSMO'
  assert h['TTYPE2']=='Q_STOKES' and h['TTYPE3']=='U_STOKES'
  assert h['TFORM2']=='E' and h['TFORM3']=='E' and h['NAXIS1']==40
  assert h['TUNIT2'] in ('K_CMB','Kcmb') and h['TUNIT3']==h['TUNIT2']
  assert float(np.float32(h['BAD_DATA']))==float(sent)
  headers={key:h.get(key) for key in ['NSIDE','ORDERING','COORDSYS',pol,'TUNIT2','BAD_DATA','FILENAME','FREQ','PROCVER']}
  invalid=np.flatnonzero(~support[f'valid_{band}_nest64'])
  invalid_check=[]
  for parent in invalid:
   child=(ns//64)**2;start=int(parent)*child;stop=start+child
   qq=hdus[1].data['Q_STOKES'][start:stop];uu=hdus[1].data['U_STOKES'][start:stop]
   bad=~(np.isfinite(qq)&np.isfinite(uu)&(qq!=sent)&(uu!=sent))
   assert bad.sum()==1 and not sn[parent]
   invalid_check.append({'nested64_parent':int(parent),'ring64_parent':int(n2r[parent]),'bad_native_pixels':(start+np.flatnonzero(bad)).tolist(),'selected':False})
  products.append({'band_GHz':band,'headers':headers,'invalid_parent_spot_check':invalid_check,'whole_raw_rehash':'NOT_REPEATED; exact candidate execution hash and bound acquisition receipts inspected'})
 # Native parent mapping checked by independent angular lookup on 1001 centres.
 sample=np.unique(np.linspace(0,hp.nside2npix(ns)-1,1001,dtype=np.int64));tt,pp=hp.pix2ang(ns,sample,nest=True)
 assert np.array_equal(hp.ang2pix(64,tt,pp,nest=True),sample//((ns//64)**2))
 assert np.array_equal(hp.ring2nest(ns,hp.nest2ring(ns,sample)),sample)

out={'status':'PASS','checks':{'manifest_members':len(manifest['files_sha256']),'carrier_coordinates':int(c.size),'contrasts_shape':list(contrasts.shape),'support_cells':int(intersection.sum()),'independent_eth_basis_cases':24,'independent_fixed_mixtures':2,'independent_STF_scalar_evaluation_max_abs_K_CMB':stfmax,'STF_symmetry_max_abs':symmax,'STF_trace_max_abs':tracemax,'eth_vs_healpy_synthesis_max_abs_K_CMB':max_synthesis,'eth_quadrature_vs_healpy_projection_max_abs_K_CMB':max_projection,'joint_parity_max_abs_K_CMB':max_parity,'small_fixture_chunk_97_vs_509_max_abs_K_CMB':max_chunk,'sentinel_nonfinite_both_fields':'PASS','native_parent_and_permutation_samples_per_band':1001},'actual_product_spot_checks':products,'review_environment_only':{'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'healpy':hp.__version__,'astropy':astropy.__version__,'threadpools':pool},'resource':{'wall_seconds':time.monotonic()-START,'process_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'thread_environment':{k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']}}}
print(json.dumps(out,indent=2,allow_nan=False))
