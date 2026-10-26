[SpinTune v5 design](README.md) › 1. Design decisions and evidence

# 1. Design decisions and evidence

## 1.1 Decisions this document makes [design calls; confirm or override]

1. **Target:** the (1,1) charge state, established by the [§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) evidence and the count. A "double-dot regime" window label is not the target: 73–91% of random 32×32 windows already qualify [measured].
2. **Research question:** *when* does information from previously tuned cells reduce acquisition cost without increasing wrong declarations ([§2](02-goals-non-goals-anti-goals.md))? A no-gain result is a valid outcome.
3. **Search policy:** one policy shared by every search tuner: a diagonal descent, then one ray per axis through the candidate empty point ([§6.1](06-tuners-and-baselines.md#61-the-shared-policy-diagonal-descent-then-axis-rays-design-call)). Not a lattice tracker (it can't resolve whole-electron offsets before anchoring), and not BoTorch.
4. **An evidence rule, not a proof:** the [§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) certificate implies the count only under its stated assumptions. Under noise and stress its error rate is measured and reported in three categories: wrong anchor, wrong count, inadequate margin.
5. **Headline branches are pre-registered** on headroom measured from sensor-only query traces (G0), with practical targets set relative to that headroom.
6. **Device template:** the paper's SEB + double-dot configuration, tuning plane (QT1, QA1).
7. **Queries:** rays of 8–64 samples and windows of 16, 32 or 64 px square ([§4.1](04-measurement-interface.md#41-queries-design-call)). The shared policy rounds each ray up to 16, 32 or 64 samples, because that makes the cold baseline fastest [measured].
   - **Shared-policy settings** (query sizing, ordering, retries) are tuned on validation to minimise T3's all-cell RF time, and every tuner then uses the same values. That keeps the cold baseline as strong as possible.
8. **Reader:** a signal-processing reader first. A CNN replaces it only if it beats it on validation ([§5.3](05-reading-the-device.md#53-reader-contract-design-call)).
9. **Budget B = 40,000 px** per cell, about one full-domain coarse mosaic plus a confirmation: the manual fallback a failed autotune triggers.
10. **Cost metrics:**
    - **Acquisition:** the paired pixel ratio over cells where both tuners succeed. It is conditional on joint success, so it is always shown with the four joint success/failure counts.
    - **Operational:** the all-cell elapsed cost, including tuner compute and a frozen fallback charge for every failure ([§11.3](11-success-measurement.md#113-scorecard)).
    - **Speed claims use RF time, never pixels.** Pixels are ~1% of RF time [measured].
11. **Trust claims:** "≤ 1% wrong declarations" is stated only if the one-sided 95% upper bound is ≤ 1%. Otherwise the wording is "observed X%, upper bound Y%".
12. **Success is judged on the nominal device** at V\*, with a margin. Success over a post-declaration hold in the noisy, latched device is reported beside it ([§11.2](11-success-measurement.md#112-success-for-one-cell)).
13. **Latching is a relaxation rate in instrument time**, not a per-pixel probability ([§4.3](04-measurement-interface.md#43-simulation-behind-the-interface-design-call)).
14. **Charge period in the in-distribution fleets:** P ≈ 15 mV ± 17% per cell. The design tolerance of 7.5–30 mV sets **P_max = 30 mV**. The 5–40 mV range is a separate "wide-period" scenario.
15. **C2 runs two labelled scenarios** (Equal1's measured Si/SiGe device; a 22FDX projection) and composes noise channels instead of adding infidelities ([§8.3](08-physics-layer-cz-error-budget.md#83-noise-and-error-budget-components)).
16. **RF is simulated; DC is only a re-costing** of the same query log.
17. **Scope:** planning caps per track adding up to 180 h, including 20 h of contingency ([§15.2](15-plan.md#152-tracks-and-hour-caps-design-call)). If a track doesn't fit, its promise shrinks before the contingency is spent.
18. **6-dot run:** a stretch goal, conditional on Equal1 confirming such a layout.

## 1.2 Evidence status (25 Oct 2026)

| Item | Status | Result |
|---|---|---|
| Main environment: QArray 1.6.0, Qiskit 2.6.1, Aer 0.18.0, qiskit-experiments 0.14.2, Samplomatic 0.21.0, Python 3.12 | **[measured]** installs | `StandardRB`, `InterleavedRB`, `LayerFidelity`, `PauliEvolutionGate`, `InjectNoise`, `Twirl`, `optimal_Vg` present |
| QDarts 1.0.5, own environment (numpy 1.26) | **[measured]** runs | 2 dots + sensor: 0.2 s at 32×32, 0.3 s at 64×64. t_c of 5 vs 80 µeV changes the scan by ~15% of the signal range |
| QArray timing (one thread, noise and latching, T = 300 mK) | **[measured]** | 2 dots: 97 ms per 100×100, 9.9 ms per 32×32. 4 dots: 116 / 12.4 ms |
| Charge cells are congruent in constant capacitance | **[measured]** | (1,1), (2,2), (3,3): 3,011–3,023 px each, so a window alone can't give the count |
| Zero-measurement success | **[measured]** | Narrow spreads (lever arms ±15%, offsets within one charge period): 82–100%. Sourced spreads (σ_cell 22 mV, die 74 mV): fleet mean **1–6%**, earlier-cells mean **6–12%**, for P = 15–25 mV |
| **Stopping rules on noiseless cells** | **[measured]** `anchor_check.py`: 300 QArray devices, P ~ U[5, 40] mV, each started at two spreads (22 and 77 mV); perfect occupancy readout; a descent along one axis at a time, stopping rule only | A fixed 22.5 mV rule (1.5 × the typical 15 mV period) declared an occupied point empty on **24/300** and **45/300** devices, all with P ≥ 25 mV. The period-bounded rule (L = 65 mV): **0/300 at each spread** (one-sided 95% bound ≈ 1% each, assuming independence). Not covered: visibility, signs, the 2D window, noise, latching, sensor transitions |
| **Policy cost, idealized** | **[measured]** `headroom_v4.py`: noiseless QArray, perfect reader, the [§6.1](06-tuners-and-baselines.md#61-the-shared-policy-diagonal-descent-then-axis-rays-design-call) policy with every ray and window metered (rays rounded up to 16/32/64 samples and shrunk to fit the ±300 mV domain; integer pixels; confirmation per [§5.2](05-reading-the-device.md#52-confirmation-and-declaration); billed retries), RF time per [§4.2](04-measurement-interface.md#42-cost-model-pixels-are-not-time). History beliefs are drawn around the truth with the [§7.2](07-fleet.md#72-parameters-defaults-and-sweep-ranges) spreads (start sd 22·√(1+1/k) mV, period 13%·√(1+1/k) after k earlier cells), not fitted from logs | **In-distribution:** T★ 357 px / 5.0 queries / 0.33 s; T3 cold 527 / 8.3 / 0.50 s; T3-M 528 px / 0.50 s; chip history (10-cell chips, cell 1 included) 451 / 5.8 / 0.36 s. History/cold **0.86 in pixels, 0.73 in time**; oracle-start headroom **32% in pixels, 33% in time**. Start knowledge alone 0.86 / 0.80; period knowledge alone 0.87 / 0.81. **Wide-period:** T★ 555, T3 757, history 652 px; history/cold 0.86 / 0.69; headroom 27% / 40%. 0 wrong anchors in 3,600 runs (300 cells × 6 tuner configurations × 2 fleets); ≤ 5/300 abstentions per tuner, from the domain limit |
| Pixels vs time | **[measured]** same script | Pixel integration is **about 1% of RF time** (1.1% and 1.3% for T3; up to 1.6% across tuners and fleets). Setup, settling and DC slew are the rest |
| Descent direction | **[measured]** `headroom_v4.py --axis-descent` | Descending one axis at a time stalls while the other dot is still occupied: its lines cross the axis every P/x (42 mV in a traced cell, below L = 49 mV). T3 then abstained on **19%** (in-distribution) and **22%** (wide) of cells, and cost 1.1–1.2× the pixels and 1.9× the time of the diagonal descent, which abstained on 0–1% |
| Ray sizes | **[measured]** `headroom_v4.py --need-sized` | Rays sized exactly to the missing evidence (8–64 samples) instead of rounded to 16/32/64: −4% pixels, but T3 is 6% (in-distribution) and 12% (wide) slower, with 3–5 more queries per cell. T★ is 11% faster, so the time headroom rises to 44% / 47%. History/cold ratios: 0.86 px, 0.72 / 0.67 time |
| Shortcut under the shared policy | **[measured]** `headroom_v4.py --stop-length 22.5` | With the 1.5-period length (22.5 mV) everywhere: 0/300 wrong anchors in-distribution, **4/300 for T3 and 1/300 for T3-M** in the wide fleet, for 8–10% lower cost. The descent's extra P_lo and the measured period partly protect it. A first point on the cost–risk curve ([§6.3](06-tuners-and-baselines.md#63-comparisons-each-one-answers-a-different-question) f) |
| "Double-dot regime" as a target | **[measured]** `regime_check.py` | 73–91% of random 32×32 windows already qualify |
| BoTorch overhead (3D, GP refit + qLogEI) | **[measured]** `bo_overhead.py` | 0.05–0.17 s per step at 50–300 observations |
| **Hann CZ pulse, standard convention** | **[measured]** `cz_v3_check.py`, `cz_v3_scan.py` | The nominal error oscillates with J_max/ΔE_z (e.g. 4×10⁻⁵ at 0.32, 2×10⁻⁶ at 0.33). Worst case up to a given ratio: ≤ 1×10⁻⁶ up to 0.15; ≤ 3.4×10⁻⁶ up to 0.21; ≤ 1×10⁻⁴ up to 0.35. **Design limit: J_max ≤ ΔE_z/5** |
| **Pure-ZZ formula vs full Hamiltonian** (local corrections fixed at nominal) | **[measured]** | Excess infidelity over 0.8 sin²(πδJ/4J) ≈ **1.15·(J_max/ΔE_z)²**: 0.03% at 0.017, 0.5–0.7% at 0.07–0.08, 2.9% at 0.16, 12–19% at 0.32. Agreement within 1% needs J_max/ΔE_z ≤ 0.09 |
| C2 propagation cost | **[measured]** | The exact 2×2 odd-block propagator matches 4×4 `expm` to 7×10⁻¹⁵. 1,000 draws × 2,000 slices take 0.12 s per map point, so **10⁴ points ≈ 0.3 core-hours**, vs ≈ 27 with a 4×4 `expm` per draw |
| CZ quasi-static error is pure ZZ; a `CPhase(π + δφ)` error model is 3× too pessimistic | **[measured]** | Holds within the validity range above |
| Equal1 22FDX cell configurations | **[sourced]**, verified against [2412.08422v2](https://arxiv.org/html/2412.08422v2) | Transport: dots QT0/QT1 and QT1/QT2, QT1 the barrier. **SEB + double dot (Fig. 4c,f): SEB between QT0 and QT1, double dot between QT1, QT2 and QA1**; barriers under QT2 and QA1; data at 700 mK; rf reflectometry at 75.5 MHz. In Fig. 4(c) the double-dot response is "overlaid with another set of transitions due to the SEB", and "further analysis is needed to understand each transition in detail" |
| External datasets | **[sourced]** Zenodo records and READMEs | **QDSD:** only single-dot diagrams are labelled; values are measured current; the interpolated CSV set (127 MB) loses information, the raw files are 186 MB. **D-CSD:** 9,850 diagrams selected with a clean/noisy classifier; raw HDF5 holds voltages and values; the default loader resizes to 128×128; no charge-count labels; 1.8 GB |
| RF/FPGA timing in practice | **[sourced]** [Roux et al., IEEE TQE (2026)](https://doi.org/10.1109/TQE.2026.3670353) | A 9.8× faster measurement gave a 2.2× faster total initialization, limited by Python execution. ~27 ms latency per command; stepped DC slews of 0.04–0.39 V/s; 0.5–16.6 ms integration per point |
| IBM Quantum Open Plan | **[sourced]** 25 Oct ([plans](https://quantum.cloud.ibm.com/docs/en/guides/plans-overview)) | Up to **10 min per rolling 28-day window**, us-east only. A promotion offers +180 min over 12 months (as of 16 Mar 2026) |
| Tuners, reader, benchmark | Not started | — |

All scripts are in `checks/` (see `checks/README.md`). They still need to be committed ([§15.1](15-plan.md#151-before-the-pitch-tue-27-oct-idea-only)).

---

← [0. Pitch](00-pitch.md) · [Index](README.md) · [2. Goals, non-goals, anti-goals](02-goals-non-goals-anti-goals.md) →
