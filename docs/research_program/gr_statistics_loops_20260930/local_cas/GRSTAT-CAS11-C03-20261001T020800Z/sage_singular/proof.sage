from sage.all import *

# Exact polynomial/rational-function certificates. The general-dimensional
# argument, including positivity, is in PROOF.md.
P = PolynomialRing(QQ, names=('w1','w2','w3','b11','b21','b31','b12','b22','b32',
                              'x1','x2','x3','y1','y2','y3',
                              'r11','r21','r31','r12','r22','r32','a1','a2'))
z = P.gens_dict()
F = P.fraction_field()
w1,w2,w3 = (F(z[k]) for k in ('w1','w2','w3'))
B = matrix(F, 3, 2, [z['b11'],z['b12'],z['b21'],z['b22'],z['b31'],z['b32']])
W = diagonal_matrix(F, [w1,w2,w3])
G = B.transpose()*W*B
assert G.det() != 0
Q = B*G.inverse()*B.transpose()*W
assert Q*Q == Q, 'rank-two weighted projection idempotence'
assert B.transpose()*W*(identity_matrix(F,3)-Q) == 0, 'rank-two weighted orthogonality'
print('SAGE_PROJECTION_RANK2_SYMBOLIC_OK')

x = vector(F, [z['x1'],z['x2'],z['x3']])
y = vector(F, [z['y1'],z['y2'],z['y3']])
ip = lambda u,v: u*W*v
lhs = ip(x,x)*ip(y,y)-ip(x,y)**2
rhs = sum(W[i,i]*W[j,j]*(x[i]*y[j]-x[j]*y[i])**2
          for i in range(3) for j in range(i+1,3))
assert lhs == rhs, 'weighted Cauchy-Binet/SOS kernel'
print('SAGE_WEIGHTED_CS_SOS_SYMBOLIC_OK')

Rvec = [vector(F,[z['r11'],z['r21'],z['r31']]),
        vector(F,[z['r12'],z['r22'],z['r32']])]
a = vector(F,[z['a1'],z['a2']])
R = matrix(F,2,2,lambda i,j: ip(Rvec[i],Rvec[j]))
s = a[0]*Rvec[0] + a[1]*Rvec[1]
assert a*R*a == ip(s,s), 'weighted Gram quadratic identity'
assert R.det() == sum(W[i,i]*W[j,j]*(Rvec[0][i]*Rvec[1][j]-Rvec[0][j]*Rvec[1][i])**2
                      for i in range(3) for j in range(i+1,3)), 'Gram determinant SOS'
print('SAGE_GRAM_SYMBOLIC_OK')

# Degenerate controls, exact arithmetic.
I = identity_matrix(QQ,3)
Z = zero_matrix(QQ,3)
assert Z*Z == Z and I*I == I
assert not [] and sum([],0) == 0
assert matrix(QQ,2,2,[1,1,1,1]).det() == 0
print('SAGE_DEGENERATE_CONTROLS_OK')
print('SAGE_ALL_OK')
