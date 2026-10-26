# Same as headroom_rough.py, but with a period-aware pitch rule: rays use the largest allowed pitch
# in {0.5, 1, 2, 4} mV that is <= P/3 (>= 3 px per charge period). Tuners that do not know P first
# spend one 64-px ray at 1 mV to measure it. Confirmation: 16x16 window (256 px). Diagonal ray: sqrt(2)*65 mV.
#   oracle start: true (1,1) centre and true P
#   chip-history start: spread 22-31 mV, P known to +-10% (uses pitch for 0.9 P)
#   cold / fleet-mean start: spread 77 mV, P unknown (5-40 mV)
import numpy as np
exec(open(__import__('sys').argv[1]).read().split('res = {')[0])
def pitch(P): return max([p for p in (0.5, 1, 2, 4) if p <= P/3] or [0.5])
rng = np.random.default_rng(33); rows = []
for i in range(300):
    m = device(rng); Pm, c11 = period_and_cell(m); P = rng.uniform(5, 40); mv = P/Pm
    r = {}
    for name, sig, knowsP in (('oracle', 0, True), ('hist22', 22, True), ('hist31', 31, True), ('cold77', 77, False)):
        v0 = c11 + (rng.normal(0, sig, 2)/mv if sig else 0)
        _, L = descend(m, v0.copy(), 65/mv, 1.0/mv); L *= mv
        p = pitch(P if name == 'oracle' else 0.9*P) if knowsP else pitch(P)
        r[name] = L/p + np.sqrt(2)*65/p + 256 + (0 if knowsP else 64)
    rows.append(r)
tot = {k: np.array([r[k] for r in rows]) for k in rows[0]}
for k, v in tot.items(): print(f"{k:7s}: mean {v.mean():5.0f} px, median {np.median(v):5.0f}, p90 {np.percentile(v,90):5.0f}")
c = tot['cold77'].mean()
for k in ('oracle', 'hist22', 'hist31'): print(f"cost ratio {k}/cold = {tot[k].mean()/c:.2f}")
