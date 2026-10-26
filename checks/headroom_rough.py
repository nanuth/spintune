# Rough pre-pilot headroom estimate (oracle reader, noiseless): ray-descent + two-axis certificate cost
# (v3 rule, L = 65 mV, 2 mV pitch) from start spreads 0 (oracle start = true (1,1) centre), 22, 31, 77 mV.
# Fixed extras added analytically: diagonal redundancy ray 46 px, 16x16 confirmation 256 px,
# and for starts without a usable P prior, one +axis ray pair to measure P (2 x 20 px).
import numpy as np
exec(open(__import__('sys').argv[1]).read().split('res = {')[0])   # reuse device/occ/period/descend
rng = np.random.default_rng(21); out = {s: [] for s in (0, 22, 31, 77)}
for i in range(300):
    m = device(rng); Pm, c11 = period_and_cell(m); P_mV = rng.uniform(5, 40); mv = P_mV/Pm
    for sig in out:
        v0 = c11 + (rng.normal(0, sig, 2)/mv if sig else 0)
        v, scanned = descend(m, v0.copy(), 65/mv, 1.0/mv); out[sig].append(scanned*mv/2)   # px at 2 mV pitch
fixed = 46 + 256
tot = {s: np.array(out[s]) + fixed + (40 if s == 77 else 0) for s in out}
for s in out:
    d = np.array(out[s]); t = tot[s]
    print(f"start spread {s:2d} mV: descent+certificate px mean {d.mean():5.0f} median {np.median(d):5.0f} p90 {np.percentile(d,90):5.0f} | total mean {t.mean():5.0f}")
for s in (22, 31, 77):
    print(f"headroom of spread-{s} start over oracle start (means): {(tot[s].mean()-tot[0].mean())/tot[s].mean():.0%}")
