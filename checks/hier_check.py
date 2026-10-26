# Zero-measurement success under SOURCED hierarchical spreads (22FDX):
#   within-die first-electron spread sigma_cell ~ 0.9 charge periods (arXiv 2310.20434)
#   die-to-die spread sigma_die ~ 3 periods (wafer IQR ~100 mV / ~25 mV period; 2501.10146, low-med confidence)
# Offsets are applied as gate-voltage shifts in units of charge periods (e).
import numpy as np
from qarray import DotArray
rng = np.random.default_rng(7)
def device(rng, q0):
    a = 1 + 0.15*rng.uniform(-1, 1, 2); x = rng.uniform(0.1, 0.4, 2) * a[::-1]
    Cgd = np.array([[a[0], x[0]], [x[1], a[1]]]); c = 0.1*(1 + 0.2*rng.uniform(-1, 1))
    m = DotArray(Cdd=np.array([[0, c], [c, 0]]), Cgd=Cgd, charge_carrier='e', T=0)
    return m, -np.linalg.solve(Cgd, q0)
def centre11(m, lo=-1.5, hi=5.5, N=160):
    vg = m.gate_voltage_composer.do2d('P1', lo, hi, N, 'P2', lo, hi, N)
    n = np.asarray(m.ground_state_open(vg)); mask = (n[...,0]==1)&(n[...,1]==1)
    return vg[mask].mean(0)
def hit(m, sh, v):
    n = np.asarray(m.ground_state_open((v - sh)[None, :]))[0]; return n[0]==1 and n[1]==1
N_DIE, CELLS = 40, 10
s_die, s_cell = 3.0, 0.9
devs = []
for d in range(N_DIE):
    die = rng.normal(0, s_die)                       # common to every dot on the die
    for c in range(CELLS):
        q0 = die + rng.normal(0, s_cell, 2)
        m, sh = device(rng, q0); devs.append((d, m, sh, centre11(m) + sh))
cent = np.array([x[3] for x in devs]); fleet_mean = cent.mean(0)
r_fleet = np.mean([hit(m, sh, fleet_mean) for _, m, sh, _ in devs])
# Die-informed start: mean (1,1) centre of the OTHER cells on the same die (an
# upper bound on what tuning earlier cells on that die could tell you).
r_die = []
for i, (d, m, sh, _) in enumerate(devs):
    others = [x[3] for j, x in enumerate(devs) if x[0]==d and j!=i]
    r_die.append(hit(m, sh, np.mean(others, 0)))
print(f"{len(devs)} devices ({N_DIE} dies x {CELLS} cells), sigma_die={s_die}, sigma_cell={s_cell} periods")
print(f"  zero-measurement, fleet-mean start      : {r_fleet:.0%}")
print(f"  zero-measurement, same-die mean start   : {np.mean(r_die):.0%}")
