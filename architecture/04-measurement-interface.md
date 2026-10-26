[SpinTune v5 design](README.md) › 4. The measurement interface

# 4. The measurement interface (the only view of a device)

**Rule:**
- Tuners never see device parameters, noiseless maps or labels. They act only through a **session**, which bills every query.
- Only the evaluator sees ground truth, and it judges *after* the run.
- **The only exception is public metadata:** chip ID, wafer ID, cell index and die position (x, y), which a fab always knows.

## 4.1 Queries [design call]

| Query | Shape | Pixels | Use |
|---|---|---:|---|
| `window(center, pitch, size)` | 2D, size ∈ {16, 32, 64} | 256 / 1,024 / 4,096 | Confirmation, mosaic tiles, drift reference (32×32) |
| `ray(start, direction, pitch, n)` | 1D, 8 ≤ n ≤ 64 | n | Descent, certificate, measuring the period |

- **Pitch:** one of {0.5, 1, 2, 4} mV per query. The largest window, and the longest ray at 4 mV, span 256 mV.
- **Ray length:** chosen by the tuner for each query, 8–64 samples. The shared policy sizes each ray for the transition-free length still missing plus one period, rounds it up to 16, 32 or 64 samples, and shrinks it to the largest of those that fits above the domain floor ([§6.1](06-tuners-and-baselines.md#61-the-shared-policy-diagonal-descent-then-axis-rays-design-call)). Samples acquired after the evidence is complete are billed and unused.
  - Rays sized exactly to the evidence save ~4% of pixels but cost the cold baseline 6–12% more RF time, through 3–5 extra queries per cell [measured]. Under the rule in [§1.1](01-design-decisions-and-evidence.md#11-decisions-this-document-makes-design-calls-confirm-or-override) (make T3 fastest), the rounded sizes win.
- **Domain:** [−300, +300] mV per axis around the design-nominal target.
  - Queries that would leave it are refused (logged, not billed).
  - A descent never goes below the point where the certificate would no longer fit; if it would have to, the tuner abstains.
  - In the idealized estimate, 0–1.7% of cells abstain for this reason, depending on the tuner [measured].
- **Mosaic:** larger regions are covered by tiling 64×64 windows, each billed.
  - The full domain at 4 mV is a 3×3 mosaic: **36,864 px**.
- **Budget:** **B = 40,000 px** per cell.
  - That's a full-domain coarse mosaic plus a certificate and a confirmation: the manual fallback a failed autotune triggers [design call].
  - At a much larger budget, such as 300 32×32 windows (307,200 px), nothing fails, so reliability would tell us nothing.
  - A run that exceeds B is a failure.
  - B is also the fallback charge in the all-cell cost ([§11.3](11-success-measurement.md#113-scorecard)).
  - The success-versus-budget curve is reported from 300 px up to B.
- **Compute cap:** 120 s of tuner computation per cell [assumed].

## 4.2 Cost model (pixels are not time)

```text
t_query = n_px · t_int + t_setup + n_lines · t_settle + |ΔV_jump| / slew
```

- **Within a query**, the sweep runs at the pixel rate (fast gate lines).
- **ΔV_jump** is the DC move from where the previous query ended to where this one starts, at the DC slew rate.
- **Instrument time** is cumulative per cell, and the persistent noise processes evolve in it ([§4.3](#43-simulation-behind-the-interface-design-call)).

| Term | RF scenario (Equal1-relevant) | DC scenario | Status |
|---|---|---|---|
| t_int per pixel | 10 µs | 1 ms | [assumed], swept |
| t_setup per query | 20 ms | 20 ms | [assumed], swept 5 / 20 / 50 ms |
| t_settle per line | 1 ms | 5 ms | [assumed] |
| DC slew | 1 V/s | 1 V/s | [assumed], swept 0.4 / 1 / 10 V/s |

**What dominates** [measured, idealized]: pixel integration is about 1% of a ray-policy run's RF time (up to 1.6%). Query setup and DC slew are most of the rest; one extra query costs as much time as ~2,000 pixels. So:
- the pixel count measures acquisition, and it is reproducible;
- time savings come from fewer queries and shorter moves;
- every "faster" claim uses RF time, shows its sensitivity to t_setup and slew, and is checked against Equal1's own time breakdown when available ([§14](14-questions-for-equal1.md) Q5).

Published practice brackets these defaults. An RF/FPGA autotuning study measured ~27 ms latency per command, stepped DC slews of 0.04–0.39 V/s and 0.5–16.6 ms integration per point ([Roux et al., IEEE TQE (2026)](https://doi.org/10.1109/TQE.2026.3670353)) [sourced]. Our 20 ms setup is consistent with that; our 1 V/s slew and 10 µs pixels are optimistic.

- **One simulation, two costings:**
  - Every run is simulated once, in the RF scenario. Per-pixel SNR, telegraph switching and latching are all defined at the RF pixel rate and in RF instrument time.
  - DC time is a re-costing of the same query log, not a separate run. It is not a prediction of DC tuning reliability.
- **Elapsed time** = RF instrument time + measured tuner compute (single thread, reference laptop). The operational metric uses it ([§11.3](11-success-measurement.md#113-scorecard)).
- **Time budget B_t (RF):** 1.25 × the RF time of a full-domain mosaic plus a certificate and a confirmation, i.e. T2's whole protocol.
  - The harness computes it once from the frozen constants and freezes it. That's ≈ 5 s with the defaults.
  - A run that exceeds B_t is a failure.
  - The DC equivalent (≈ 54 s) is used only for the DC re-costing.
- **Frozen fallback:** a run that fails or abstains is charged T2's protocol on top of what it spent: B px and B_t/1.25 of RF time.
- **Reported:** pixels, RF time, elapsed time, DC re-costing, query count, total slew distance, tuner compute.

## 4.3 Simulation behind the interface [design call]

- **Deterministic part:** a lazy tile cache. Noiseless occupancy and sensor maps are computed on demand per pitch and stored per cell.
- **Persistent stochastic state:** for each cell session, telegraph fluctuators, 1/f drift and latched occupancy carry over between queries. They are drawn along the actual acquisition path (raster or ray order) in simulated instrument time. Queries are simulated in the order they are issued.
- **Evolution between samples:** noise processes and latched states evolve during every interval of instrument time: pixel integration, query setup, line settling, slews and tuner compute (charged at its measured duration).
- **Noise parameters (defaults [assumed], swept):**
  - **White noise:** SNR = (dot-A step height) / (per-pixel noise σ) = 10 at the RF pixel time. Dot-B steps are smaller by the SEB sensitivity ratio ([§7.2](07-fleet.md#72-parameters-defaults-and-sweep-ranges)).
  - **Telegraph noise:** 2 fluctuators per dot. Each shifts that dot's lines by 0.05–0.2·P, with switching rates log-uniform over 1–100 Hz in instrument time. A shift can exceed the 0.15·P declaration margin, so hold success ([§11.2](11-success-measurement.md#112-success-for-one-cell)) can fall below nominal success; the gap is measured, not hidden.
  - **Latching as relaxation:** a charge transition that has become energetically allowed happens within an interval Δt with probability 1 − exp(−Γ·Δt). Γ is set per transition type (lead A, lead B, inter-dot; [§7.2](07-fleet.md#72-parameters-defaults-and-sweep-ranges)) and may depend on detuning. At the RF pixel time, the defaults equal per-pixel probabilities of 0.95 / 0.85 / 0.99.
    - At the default rates a latched state relaxes within microseconds, so latching shows up only within a sweep, as lines displaced along the scan direction. Every gap between queries clears it, because each query starts with ≥ 5 ms of setup ([§4.2](#42-cost-model-pixels-are-not-time)).
    - The model is phenomenological. A **partition test** runs one 64-sample path as 1, 2, 4 and 8 queries, with setup, settling and slew set to zero, and checks that the latched-state statistics agree within sampling error.
    - **Slow-lead stress values** ([§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) b): Γ_B = 10³, 10² and 10 s⁻¹, and Γ_B = 0 ("dot B unloads only via dot A"). Γ_B = 10³ s⁻¹ outlasts a 64-sample ray (0.64 ms) but not a query setup (survival e^−20 at 20 ms, 0.7% at 5 ms), so it stresses latching *within* a query. Only Γ_B ≤ 10² s⁻¹ and Γ_B = 0 carry a latched state *across* a query boundary (14% and 100% at 20 ms setup) [computed]. Persistent latched state is therefore exercised only by those B4 stress scenarios.
  - **SEB background transitions (stress scenario):** the sensor's own charge transitions appear as extra steps of either sign along each axis, with residual compensation error of 0–20%. Equal1's Fig. 4(c) shows the double-dot response overlaid with such transitions ([§1.2](01-design-decisions-and-evidence.md#12-evidence-status-25-oct-2026)).
- **Common random numbers:** only exogenous randomness is shared between tuners. That means white-noise samples, telegraph switching times and 1/f trajectories indexed by instrument time, plus the uniform draws used for latching decisions on a fixed time grid. Latched occupancy itself is not shared, because different tuners drive the device through different states.
- **Ablation:** "per-query reset", labelled as a simplified scenario. The persistent run is the reference.
- **QDarts** runs as a worker that returns noiseless tiles; the wrapper adds the stochastic parts. QDarts is an equilibrium simulator (it has white and slow sensor noise but no dynamics), so the OOD-simulator fleet tests the physics, not our noise and latching wrapper.

Code-level interfaces: [Appendix A](appendix-a-interfaces-and-code-layout.md).

---

← [3. Scope and device template](03-scope-and-device-template.md) · [Index](README.md) · [5. Reading the device](05-reading-the-device.md) →
