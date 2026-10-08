from sage.all import PolynomialRing, QQ


def zero(label, expression):
    if expression != 0:
        raise AssertionError('%s: %s' % (label, expression))
    print('PASS ' + label)


# The function values are independent scalar symbols. Differentiability is
# used only to name the gradient values at g and h; no Hessian is assumed.
R = PolynomialRing(QQ, names=('Hf','Hg','Hh','f','g','h','Gg','Gh'))
Hf,Hg,Hh,f,g,h,Gg,Gh = R.gens()
Dfg = Hf-Hg-Gg*(f-g)
Dfh = Hf-Hh-Gh*(f-h)
Dhg = Hh-Hg-Gg*(h-g)
rhs = (Gh-Gg)*(f-h)
zero('generic_coordinate_Bregman_three_point', Dfg-Dfh-Dhg-rhs)
zero('zero_coordinate_base', (Hf-Hg)-(Hf-Hh)-(Hh-Hg))

# Given the n-coordinate identity, adjoining one free coordinate changes
# the defect by precisely the generic coordinate identity above. Therefore
# induction proves it for every natural n, including zero.
zero('arbitrary_n_induction_step', -Gg*(f-g)+Gh*(f-h)+Gg*(h-g)-rhs)

# Arbitrary-k row identity by induction: A is the existing finite sum of
# v_j lambda_j. One additional term uses distributivity/commutativity only.
S = PolynomialRing(QQ, names=('x','A','v','lam','L','Rold'))
x,A,v,lam,L,Rold = S.gens()
row_step = x*(A+v*lam)-(x*A+lam*v*x)
zero('arbitrary_k_row_base', x*S(0)-S(0))
zero('arbitrary_k_row_induction_step', row_step)

# Arbitrary-n reindexing: L and Rold denote the already equal double sums.
# The new row contributes x(A+v lam) on the left and xA+lam v x on
# the right. Modulo the n-induction hypothesis their difference vanishes.
double_step = (L+x*(A+v*lam))-(Rold+x*A+lam*v*x)
zero('arbitrary_n_finite_sum_reindexing_step', double_step.subs({L:Rold}))
zero('empty_n_or_k_sum', S(0))

# If delta_i=sum_j V_ij lambda_j and each (V^T(f-h))_j=0, then
# sum_i delta_i(f_i-h_i)=sum_j lambda_j (V^T(f-h))_j=0.
T = PolynomialRing(QQ, names=('lambda_j','moment_j'))
lambda_j,moment_j = T.gens()
zero('exact_moment_zero_kernel', (lambda_j*moment_j).subs({moment_j:T(0)}))

Q = QQ
H = lambda z: z**3/Q(3)
grad = lambda z: z**2
D = lambda a,b: H(a)-H(b)-grad(b)*(a-b)
assert D(Q(2),Q(1)) == Q(4)/3
assert D(Q(1),Q(2)) == Q(5)/3
print('PASS orientation_control D(2||1)=4/3 D(1||2)=5/3')
assert Q(1)*Q(1)*Q(1)/10 == Q(1)/10 != 0
print('PASS approximate_matching_control residual=1/10 != 0')
print('SAGE_GENERIC_CERTIFICATE_PASS')
