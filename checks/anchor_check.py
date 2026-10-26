# R1 check: does the empty-anchor rule miscount? Noiseless QArray double dots, perfect transition
# detection along rays (an oracle reader), charge period P drawn over the full fleet range 5-40 mV.
#   v2 rule: descend along -e1 then -e2 until a ray segment is transition-free for 1.5 x P_prior
#            (P_prior = 15 mV); call that point empty.
#   v3 rule: same descent, but transition-free length L = 1.25 x (1 + r_m,max) x P_max = 65 mV
#            (P_max = 40 mV, interdot ratio r_m <= 0.3), alternating axes until both rays pass.
# Start points: true (1,1) centre + N(0, 77 mV) per axis (the cold prior spread) or + N(0, 22 mV).
# Also: fraction of fleet cells whose v3 certificate fits inside a +-300 mV domain.
import numpy as np
from qarray import DotArray
rng = np.random.default_rng(7)
def device(rng):
    a = 1 + 0.10*rng.uniform(-1, 1, 2); x = rng.uniform(0.1, 0.4, 2) * a[::-1]
    Cgd = np.array([[a[0], x[0]], [x[1], a[1]]]); c = 0.1*(1 + 0.3*rng.uniform(-1, 1))
    return DotArray(Cdd=np.array([[0, c], [c, 0]]), Cgd=Cgd, charge_carrier='e', T=0)
def occ(m, V): return np.asarray(m.ground_state_open(np.atleast_2d(V))).astype(int)
def period_and_cell(m):
    v = np.linspace(-1.5, 4.0, 2201); n = occ(m, np.c_[v, np.full_like(v, -1.5)])[:, 0]
    jumps = v[1:][np.diff(n) != 0]; P = jumps[1] - jumps[0]          # dot-1 spacing along e1, dot 2 empty
    g = np.linspace(-1.5, 4.0, 220); G = np.array(np.meshgrid(g, g, indexing='ij')).reshape(2, -1).T
    N = occ(m, G); c11 = G[(N[:, 0] == 1) & (N[:, 1] == 1)].mean(0)
    return P, c11
def descend(m, v, L, step, maxlen=2000.0):
    """Alternate rays along -e1/-e2 (model units). A ray passes when it runs L with no occupancy change.
    Returns final point and total ray length scanned."""
    scanned = 0.0; ok = [False, False]; ax = 0
    while not all(ok) and scanned < maxlen:
        e = np.zeros(2); e[ax] = -1
        n0 = occ(m, v)[0]; free = 0.0; changed = False
        while free < L and scanned < maxlen:
            v2 = v + e*step; n1 = occ(m, v2)[0]; scanned += step
            if (n1 != n0).any(): free = 0.0; n0 = n1; changed = True
            else: free += step
            v = v2
        ok[ax] = True
        if changed: ok[1-ax] = False        # moving along one axis can expose occupancy on the other
        ax = 1 - ax
    return v, scanned
res = {('v2', s): [] for s in (22, 77)} | {('v3', s): [] for s in (22, 77)}
cost = {s: [] for s in (22, 77)}
for i in range(300):
    m = device(rng); Pm, c11 = period_and_cell(m)
    P_mV = rng.uniform(5, 40); mv = P_mV / Pm               # mV per model unit (T=0 ground state is scale-free)
    for sig in (22, 77):
        v0 = c11 + rng.normal(0, sig, 2)/mv
        for rule, L_mV in (('v2', 1.5*15), ('v3', 1.25*1.3*40)):
            v, scanned = descend(m, v0.copy(), L_mV/mv, step=1.0/mv)
            res[(rule, sig)].append((tuple(occ(m, v)[0]), P_mV))
            if rule == 'v3': cost[sig].append(scanned*mv)
for (rule, sig), r in res.items():
    wrong = [p for (n, p) in r if n != (0, 0)]
    print(f"{rule} rule, start spread {sig:2d} mV: declared-empty point not empty in {len(wrong)}/{len(r)} cells"
          + (f" (P of failures: {min(wrong):.0f}-{max(wrong):.0f} mV)" if wrong else ""))
for sig in (22, 77):
    c = np.array(cost[sig]); print(f"v3 descent ray length, start spread {sig} mV: median {np.median(c):.0f} mV, p90 {np.percentile(c, 90):.0f} mV "
                                    f"(= {np.median(c)/2:.0f} / {np.percentile(c, 90)/2:.0f} px at 2 mV pitch)")
# Domain feasibility under the v2 hierarchy (offsets of the (1,1) target from fleet nominal, mV)
M = 200000; r2 = rng.uniform(0, 1, M)
off = rng.normal(0, 30, (M, 1)) + rng.normal(0, 60, (M, 1)) + rng.uniform(0, 60, (M, 1))*r2[:, None] + rng.normal(0, 22, (M, 2))
off -= off.mean(0)
P = rng.uniform(5, 40, (M, 1)); corner = off - P                  # corner sits about one period below the target
for lo in (-300, -350, -400):
    inside = np.all(corner - 65 > lo, axis=1) & np.all(off + 2*P < 300, axis=1)
    print(f"domain [{lo}, +300] mV: certificate fits for {inside.mean():.2%} of cells")
