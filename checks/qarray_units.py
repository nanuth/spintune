# Single dot: guess E_c[meV]=2/C_sigma, P[mV]=1/Cg, T in mK. Check period and thermal width.
import numpy as np
from qarray import DotArray
Ec, P, T_mK = 4.0, 15.0, 300.0
Cg = 1/P; Csig = 2/Ec; Clead = Csig - Cg
for impl in ['rust', 'jax']:
    try:
        m = DotArray(Cdd=[[Clead]], Cgd=[[Cg]], charge_carrier='e', T=T_mK, implementation=impl)
    except Exception as e:
        print(impl, 'fail', e); continue
    V = np.linspace(0, 40, 4001)[:, None]
    n = np.asarray(m.ground_state_open(V))[:, 0]
    # first transition centre and width
    i = np.argmin(abs(n - 0.5)); V0 = V[i, 0]
    lo, hi = V[np.argmin(abs(n-0.1)),0], V[np.argmin(abs(n-0.9)),0]
    alpha = Ec / P                               # eV/V == meV/mV
    kT = 8.617e-5 * T_mK                         # meV if T in mK
    pred = 2 * np.log(9) * kT / alpha            # 10-90% width of Fermi step in mV
    i2 = np.argmin(abs(n - 1.5))
    print(impl, 'V0', V0, 'period', V[i2,0]-V0, '10-90 width', hi-lo, 'pred', pred)
