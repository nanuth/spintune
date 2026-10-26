[SpinTune v5 design](README.md) › 12. Compute plan

# 12. Compute plan

- **Measured:**
  - QArray: ~10 ms per 32×32 window; rays are cheaper.
  - QDarts: ~0.2 s per window.
  - The tile cache makes repeated queries < 1 ms.
- **Ray-policy runs** take ~4–9 queries in the idealized estimate ([§1.2](01-design-decisions-and-evidence.md#12-evidence-status-25-oct-2026)), so ≲ 0.2 s per run with reader inference [estimate]. T2's mosaic adds ~0.5 s.
- **BoTorch** is needed only for the optional T-BO.
- **HPC is optional.** The full spread map is the HPC showcase if cluster hours appear.

| Job | Count | Core-hours | Laptop, 14 cores |
|---|---|---:|---:|
| Frozen evaluation: ~18 tuner configs (including T3-L and the ablations) × 3 seeds × 3,500 QArray cells (ID + OOD + OOD-spec) | ~189,000 runs | ~10–20 | ~1–1.5 h |
| Certificate stress set ([§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) b): ≥ 3,000 cells × ~6 scenarios, shared policy | ~18,000 runs | ~1–2 | minutes |
| Same stress set, cost–risk baselines: T3-L(ℓ) at its 4 lengths and T2-N | ~90,000 runs | ~8–10 | < 1 h |
| OOD-simulator (QDarts) | ~6,000 runs × ~10 queries | ~1.5–5 | < 1 h |
| Training-fleet tuning logs (T3 over 10,000 cells) | 10,000 runs | ~1 | minutes |
| Coarse spread map (the break-even map): 3 σ_die × 2 hierarchy strengths × 2 period-predictability levels (cell-level P spread 5% and 13%) × 2 noise levels × 1,000 cells × 4 tuners (T2, T3, T3-H, T6) × 3 seeds | ~288,000 runs | ~20–30 | ~2 h |
| Full spread map (optional HPC): 5 σ_die × 3 σ_cell × 3 hierarchy × 3 period predictability × 3 noise × 2 temperatures × 1,000 × 4 × 3 | ~9.7 M runs | ~600–900 | ~3 days (or ~6 h on a 128-core node) |
| C2 map: 10⁴ points × 10³ draws, exact 2×2 block | — | **0.3 [measured basis]** | minutes |
| CNN reader training (optional, CPU) | — | ~10–30 | overnight |
| Optional T-BO: 0.05–0.17 s per step × ~50 steps × 3,000 cells × 2 variants × 3 seeds | — | ~13–43 | ~1–3 h |

**Parallelism:** pin backend threads to 1 per worker. Parallelise across independent sessions (wafer × tuner × seed). Within a wafer, chips and cells run in order, because each tuner's history is sequential.

---

← [11. How success is measured](11-success-measurement.md) · [Index](README.md) · [13. Prerequisites](13-prerequisites.md) →
