# How easy is Bobi's "double" target? Label random 32x32 windows with PLAN.md decision 2:
#   no-dot : zero electrons everywhere
#   single : only one dot's occupation changes in the window
#   double : both dots' occupations change AND an interdot transition is present
# Fleet per PLAN.md decision 4: each capacitance entry x lognormal(10%), common back-gate
# offset N(0, sigma_bg). Domain = plungers in [-2, 8] (the 100x100 map range used for timing).
import numpy as np
from qarray import DotArray
rng = np.random.default_rng(3)
def device(rng, sigma_bg):
    ln = lambda x: x*np.exp(rng.normal(0, 0.10, np.shape(x)))
    Cgd = ln(np.array([[1.0, 0.2], [0.2, 1.0]])); c = ln(0.1)
    m = DotArray(Cdd=np.array([[0, c], [c, 0]]), Cgd=Cgd, charge_carrier='e', T=0)
    return m, rng.normal(0, sigma_bg)            # back gate = common shift on both plungers
def label(m, bg, cx, cy, span, res=32):
    vg = m.gate_voltage_composer.do2d('P1', cx-span/2, cx+span/2, res, 'P2', cy-span/2, cy+span/2, res) + bg
    n = np.asarray(m.ground_state_open(vg)).astype(int)
    if n.sum() == 0: return "no-dot"
    ch1 = (np.ptp(n[...,0]) > 0); ch2 = (np.ptp(n[...,1]) > 0)
    if ch1 != ch2: return "single"
    if not (ch1 and ch2): return "flat"           # one constant charge state: not covered by PLAN labels
    inter = False
    for ax in (0, 1):
        d = np.diff(n, axis=ax)                    # neighbour differences
        if np.any((d[...,0] == 1) & (d[...,1] == -1)) or np.any((d[...,0] == -1) & (d[...,1] == 1)): inter = True
    return "double" if inter else "both-no-interdot"
for sigma_bg in (0.5,):
    for span in (1.0, 2.0, 3.3):
        counts = {}
        for _ in range(60):
            m, bg = device(rng, sigma_bg)
            for _ in range(25):
                cx, cy = rng.uniform(-2, 8, 2)
                l = label(m, bg, cx, cy, span); counts[l] = counts.get(l, 0) + 1
        tot = sum(counts.values())
        print(f"window span {span:.1f} V (~{span/1.03:.1f} charge periods), {tot} random windows: " +
              ", ".join(f"{k} {v/tot:.0%}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1])))
