# Fine scan of nominal Hann-pulse error vs Jmax/dEz (standard convention), using the exact
# 2x2 odd-block propagator; best local-Z corrections fitted per point.
import numpy as np, sys
sys.path.insert(0, sys.argv[1]); 
from scipy.optimize import minimize
exec(open(sys.argv[1]+'/cz_v3_check.py').read().split('print("1)')[0])   # reuse defs (U4, fit helpers)
src = open(sys.argv[1]+'/cz_v3_check.py').read()
exec(src[src.index('def odd_block_prop'):src.index('Jmax, dEz = 20e6')])
def best_err(U):
    d = np.diag(U); ph = np.angle(d)
    # analytic local-Z: choose a,b to null single-qubit phases; residual = conditional phase + off-diagonal leakage
    f = lambda p: 1-favg(k(rz(p[0]),rz(p[1]))@U, CZ)
    a0 = -(ph[2]-ph[0]); b0 = -(ph[1]-ph[0])
    r = min((minimize(f, x0, method='Nelder-Mead', options={'xatol':1e-12,'fatol':1e-16}) for x0 in ([a0,b0],[0,0],[1,1],[-1,2],[2,-1])), key=lambda r: r.fun)
    return r.fun
dEz = 63e6
rat = np.round(np.arange(0.02, 0.501, 0.01), 3); errs = []
for q in rat:
    U = odd_block_prop(q*dEz, dEz, np.array([0.0]))[0]; errs.append(best_err(U))
errs = np.array(errs)
for q, e in zip(rat, errs): print(f"{q:5.2f} {e:.2e}")
for thr in (1e-6, 1e-5, 1e-4):
    ok = rat[np.maximum.accumulate(errs) <= thr]
    print(f"envelope <= {thr:.0e} for Jmax/dEz <= {ok.max() if len(ok) else 'none'}")
