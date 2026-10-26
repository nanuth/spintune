# Two checks with qarray ground truth (noiseless, T=0):
# (A) Are charge cells (1,1), (2,2), (3,3) the same shape? If yes, a small local
#     window cannot tell (1,1) from (2,2) -> absolute charge state is not
#     identifiable without seeing the empty (0,0) corner.
# (B) How far does the (1,1) centre move across a fleet drawn with the Design
#     Proposition's spreads, measured in units of the (1,1) cell size?
import numpy as np
from qarray import DotArray
rng = np.random.default_rng(1)

def device(rng, offsets=True):
    a = 1 + 0.15*rng.uniform(-1, 1, 2)                 # lever arms +-15%
    x = rng.uniform(0.1, 0.4, 2) * a[::-1]             # cross-cap 0.1-0.4 of diagonal
    Cgd = np.array([[a[0], x[0]], [x[1], a[1]]])
    c = 0.1*(1 + 0.2*rng.uniform(-1, 1))               # dot-dot +-20%
    Cdd = np.array([[0, c], [c, 0]])
    m = DotArray(Cdd=Cdd, Cgd=Cgd, charge_carrier='e', T=0)
    q0 = rng.uniform(-0.5, 0.5, 2) if offsets else np.zeros(2)   # offset charge, one period
    shift = -np.linalg.solve(Cgd, q0)                 # offset charge == gate-voltage shift
    return m, shift

def cell_stats(m, shift, lo=-1.5, hi=5.5, N=400):
    vg = m.gate_voltage_composer.do2d('P1', lo, hi, N, 'P2', lo, hi, N)
    n = np.asarray(m.ground_state_open(vg))
    px = ((hi-lo)/N)**2
    out = {}
    for s in [(1,1),(2,2),(3,3),(1,2),(2,1)]:
        mask = (n[...,0]==s[0]) & (n[...,1]==s[1])
        vs = vg[mask]
        out[s] = (mask.sum()*px, vs.mean(0)+shift if len(vs) else None, mask.sum())
    return out

# (A)
m, sh = device(rng, offsets=False)
st = cell_stats(m, sh)
print("(A) cell areas (V^2) for one device:")
for s,(area,c,cnt) in st.items(): print(f"    {s}: area={area:.4f}  pixels={cnt}")

# (B)
for offsets in (False, True):
    centres, widths = [], []
    for _ in range(300):
        m, sh = device(rng, offsets)
        st = cell_stats(m, sh, N=200)
        area, c, _ = st[(1,1)]
        centres.append(c); widths.append(np.sqrt(area))
    centres = np.array(centres); w = np.median(widths)
    sd = centres.std(0); span = np.percentile(centres,97.5,0)-np.percentile(centres,2.5,0)
    print(f"(B) offsets={'uniform 1 period' if offsets else 'none'}: (1,1) cell width ~{w:.2f} V; "
          f"centre SD = {sd[0]/w:.2f} / {sd[1]/w:.2f} cell widths; 95% span = {span[0]/w:.2f} x {span[1]/w:.2f} cell widths")

# (C) Zero-measurement baseline: set every device to the fleet-mean (1,1) centre.
print("(C) zero-measurement 'fleet mean' tuner, success = lands in true (1,1):")
for offsets in (False, True):
    devs = [device(rng, offsets) for _ in range(400)]
    cs = np.array([cell_stats(m, sh, N=200)[(1,1)][1] for m, sh in devs])
    v_mean = cs.mean(0)
    hit = 0
    for (m, sh) in devs:
        n = np.asarray(m.ground_state_open((v_mean - sh)[None, :]))[0]
        hit += int(n[0]==1 and n[1]==1)
    print(f"    offsets={'uniform 1 period' if offsets else 'none'}: {hit/len(devs):.0%} of devices")
