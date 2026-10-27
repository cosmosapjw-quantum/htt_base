"""Independent exact-rational finite-frame check; standard library only."""
from fractions import Fraction as F


def levi(i, j, k):
    if len({i, j, k}) != 3:
        return 0
    return 1 if ((j-i) % 3 == 1) else -1


def ricci(ns, av):
    ix = range(3)
    c = lambda i, j, k: levi(i, j, k)*ns[k] + av[i]*(j == k) - av[j]*(i == k)
    gam = lambda i, j, k: F(c(i,j,k)-c(j,k,i)+c(k,i,j), 2)
    curv = lambda l,m,i,j: sum(gam(j,m,k)*gam(i,k,l)-gam(i,m,k)*gam(j,k,l)-c(i,j,k)*gam(k,m,l) for k in ix)
    return tuple(tuple(sum(curv(i,j,i,k) for i in ix) for k in ix) for j in ix)


u = F(2, 7)
v = F(3, 11)
for name, ns, av, diag in [
    ('I', (0,0,0), (0,0,0), (0,0,0)),
    ('II', (u,0,0), (0,0,0), (u*u/2,-u*u/2,-u*u/2)),
    ('IX', (u,u,u), (0,0,0), (u*u/2,)*3),
    ('V', (0,0,0), (v,0,0), (-2*v*v,)*3),
    ('VII0-flat', (0,u,u), (0,0,0), (0,0,0)),
    ('VII0-matched', (0,2*u,u), (0,0,0), (-u*u/2,3*u*u/2,-3*u*u/2))]:
    rr = ricci(ns,av)
    assert rr == tuple(tuple(diag[i] if i == j else 0 for j in range(3)) for i in range(3)), (name,rr)
    print(name, [str(rr[i][i]) for i in range(3)], 'scalar', sum(rr[i][i] for i in range(3)))
print('PASS: six exact-rational Ricci matrices')
