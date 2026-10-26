import time, numpy as np, os
from qarray import ChargeSensedDotArray, WhiteNoise, TelegraphNoise, LatchingModel
def make(n_dots, T, noise=True, latch=True, seed=0):
    rng = np.random.default_rng(seed)
    Cdd = np.zeros((n_dots, n_dots))
    for i in range(n_dots-1): Cdd[i,i+1]=Cdd[i+1,i]=0.1*(1+0.2*rng.uniform(-1,1))
    Cgd = np.eye(n_dots)*(1+0.15*rng.uniform(-1,1,n_dots))
    for i in range(n_dots-1): Cgd[i,i+1]=Cgd[i+1,i]=0.2
    Cgd = np.hstack([Cgd, 0.01*np.ones((n_dots,1))])          # + sensor gate column
    Cds = np.array([[0.02*(1+0.2*rng.uniform(-1,1)) for _ in range(n_dots)]])
    Cgs = np.array([[0.06]*n_dots + [1.0]])
    nm = (WhiteNoise(amplitude=1e-2) + TelegraphNoise(amplitude=5e-4, p01=1e-3, p10=1e-2)) if noise else None
    lm = LatchingModel(n_dots=n_dots, p_leads=0.95*np.ones(n_dots), p_inter=0.99*np.ones((n_dots,n_dots))) if latch else None
    return ChargeSensedDotArray(Cdd=Cdd, Cgd=Cgd, Cds=Cds, Cgs=Cgs, coulomb_peak_width=0.05, T=T,
                                noise_model=nm, latching_model=lm, charge_carrier='e')
for n_dots in (2,4):
    for npx in (100, 32):
        m = make(n_dots, T=300)
        vg = m.gate_voltage_composer.do2d('P1', -2, 8, npx, 'P2', -2, 8, npx)
        m.charge_sensor_open(vg)  # warm-up
        t=time.perf_counter(); R=10
        for _ in range(R): z, n = m.charge_sensor_open(vg)
        dt=(time.perf_counter()-t)/R
        print(f"{n_dots} dots, {npx}x{npx}, T=300 mK, noise+latching: {dt*1e3:7.1f} ms/CSD  (z {z.shape}, n {n.shape})")
