# Headroom with spreads specified in mV (sourced) and P derived from E_c/alpha.
#   sigma_cell = 22 mV (2310.20434), sigma_die = 74 mV (wafer IQR ~100 mV, 2501.10146)
#   P = E_c/alpha: 15 mV (E_c 4 meV, alpha 0.27) and 25 mV for comparison.
# "Earlier cells" = mean target of cells 1..k-1 on the same chip (k = 2..10), the
# information a sequential tuner really has; "all others" = upper bound (as in hier_check.py).
import numpy as np
from qarray import DotArray
def device(rng, q0):
    a = 1 + 0.15*rng.uniform(-1, 1, 2); x = rng.uniform(0.1, 0.4, 2) * a[::-1]
    Cgd = np.array([[a[0], x[0]], [x[1], a[1]]]); c = 0.1*(1 + 0.2*rng.uniform(-1, 1))
    return DotArray(Cdd=np.array([[0, c], [c, 0]]), Cgd=Cgd, charge_carrier='e', T=0), -np.linalg.solve(Cgd, q0)
def centre11(m, N=160, lo=-1.5, hi=5.5):
    vg = m.gate_voltage_composer.do2d('P1', lo, hi, N, 'P2', lo, hi, N)
    n = np.asarray(m.ground_state_open(vg)); return vg[(n[...,0]==1)&(n[...,1]==1)].mean(0)
def hit(m, sh, v):
    n = np.asarray(m.ground_state_open((v - sh)[None, :]))[0]; return n[0]==1 and n[1]==1
for P_mV in (15, 25):
    rng = np.random.default_rng(11)
    s_cell, s_die = 22/P_mV, 74/P_mV
    chips = []
    for d in range(40):
        die = rng.normal(0, s_die); cells = []
        for c in range(10):
            m, sh = device(rng, die + rng.normal(0, s_cell, 2)); cells.append((m, sh, centre11(m)+sh))
        chips.append(cells)
    allc = np.array([c[2] for ch in chips for c in ch]); fm = allc.mean(0)
    r_fleet = np.mean([hit(m, sh, fm) for ch in chips for (m, sh, _) in ch])
    r_up, r_seq = [], []
    for ch in chips:
        for k, (m, sh, _) in enumerate(ch):
            r_up.append(hit(m, sh, np.mean([x[2] for j, x in enumerate(ch) if j != k], 0)))
            if k >= 1: r_seq.append(hit(m, sh, np.mean([x[2] for x in ch[:k]], 0)))
    print(f"P = {P_mV} mV (sigma_cell = {s_cell:.2f} P, sigma_die = {s_die:.2f} P), 400 cells:")
    print(f"   fleet-mean start {np.mean(r_fleet):.0%} | earlier-cells mean (k>=2) {np.mean(r_seq):.0%} | all-other-cells upper bound {np.mean(r_up):.0%}")
