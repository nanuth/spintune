[SpinTune v5 design](README.md) › 7. The fleet

# 7. The fleet

## 7.1 Structure [design call]

The fleet is hierarchical: **wafer → chip (die) → cell**.

| Level | Shared by | Varies |
|---|---|---|
| Wafer | All cells on the wafer | Common voltage offset (σ_wafer); radial edge-shift amplitude Δ_edge |
| Chip (die) | All cells on the chip | Common-mode offset σ_die; lever-arm scale (±5%); cross-coupling scale (±10%); radial term Δ_edge·(r/R)² from die position |
| Cell | — | Per-dot first-electron offset σ_cell; per-dot lever arms (±10% about the chip scale); cross-coupling; inter-dot capacitance; E_c |

- **Splits are by whole wafer.** Train, validation and test never share a wafer.
- **Hierarchy strength**, the fraction of variance at chip level, is swept ([§12](12-compute-plan.md)).

## 7.2 Parameters (defaults and sweep ranges)

| Parameter | Default | Sweep | Source / status |
|---|---|---|---|
| Lever arm α | 0.27 eV/V × chip scale (lognormal 5%) × cell factor (lognormal 10%) | Centre 0.2–0.4 | [sourced] centre: Equal1 22FDX ([2412.08302v1](https://arxiv.org/html/2412.08302v1)); Quobly/CEA 22FDX 0.2–0.4 ([2501.10146](https://arxiv.org/abs/2501.10146)). Spreads and the gate it refers to in our plane are [assumed] |
| Charging energy E_c | 4 meV × chip scale (lognormal 10%) × cell factor (lognormal 8%) | Centre 2–8 meV | [sourced] centre: 2.0–4.5 meV in multi-gate 22FDX dots (2501.10146). Spreads [assumed] |
| Charge period P = E_c/α, per cell | ≈ 15 mV × lognormal(≈ 17%); chip-level part ≈ 11%, cell-level ≈ 13% | **Wide-period scenario:** P ~ U[5, 40] mV, P_max 40 mV | Derived. The **design spec** gives T3 a nominal 15 mV with a tolerance of 7.5–30 mV; **P_max = 30 mV** sets the certificate length ([§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call)) |
| σ_cell, per-dot first-electron spread within a chip | 22 mV | 10–40 mV | [sourced] σ = 22 mV for the 28 nm devices of a **different group's 1,024-dot 22FDX transistor-dot array**, of which 16 mV is intrinsic ([Thomas et al. 2025](https://doi.org/10.1038/s41928-024-01304-y)); not an Equal1 multi-gate cell. Intel Si/SiGe: 61–63 mV ([2307.04812v2](https://arxiv.org/html/2307.04812v2)) |
| σ_die, chip-to-chip offset (residual after the radial term) | 60 mV | 0–150 mV | [sourced, low–medium confidence] room-temperature threshold-voltage IQR ≈ 100 mV over ~40 dies, pooled over gates and including systematic access-gate shifts (2501.10146) |
| Δ_edge, radial edge shift | 0–60 mV (uniform per wafer) | 0–120 mV | [assumed] |
| σ_wafer | 30 mV | 0–80 mV | [assumed] |
| **Δ_nom**, gap between the design-nominal prediction and the true fleet mean | 0 mV | 0–100 mV | [assumed]. Default 0 is conservative (cold = fleet-mean start) |
| Cross-coupling x (next-nearest gate) | 0.25 (cell 0.1–0.4) | 0.1–0.6 | [assumed] |
| Inter-dot capacitance | ±20% around nominal (r_m ≤ 0.3) | ±10–30% | [assumed] |
| SEB sensitivity, dot A : dot B | 3 | 2–4 | [assumed] |
| Temperature | 0.3 K (QArray `T=300`) | 0.35 / 0.5 / 0.75 K | Bell-1 runs at 0.3 K; Equal1 measured at 350/500/750 mK ([2412.01920 v3](https://arxiv.org/html/2412.01920v3)) |
| Sensor white noise | SNR 10 per pixel at the RF t_int, defined on **dot-A** steps (dot B: 10/3) | SNR 5–30 | [assumed]. Definition in [§4.3](04-measurement-interface.md#43-simulation-behind-the-interface-design-call) |
| Telegraph noise | 2 fluctuators per dot, line shift 0.05–0.2·P, rates 1–100 Hz | Amplitude ×0.5–2 | [assumed]. Can exceed the 0.15·P margin ([§11.2](11-success-measurement.md#112-success-for-one-cell)) |
| Charge noise √S_E at 1 Hz | 4 µeV/√Hz | 1.7–6.5 µeV/√Hz | [sourced] SOI 1.7–6.3 ([2209.01853](https://arxiv.org/abs/2209.01853)); 22FDX p-type median 6.5 ([2507.21306v1](https://arxiv.org/html/2507.21306v1)) |
| Latching (relaxation rate Γ, [§4.3](04-measurement-interface.md#43-simulation-behind-the-interface-design-call)) | Lead A 3.0×10⁵ s⁻¹, lead B 1.9×10⁵ s⁻¹, inter-dot 4.6×10⁵ s⁻¹ (per-pixel 0.95 / 0.85 / 0.99 at 10 µs) | Per-pixel equivalent 0.8–1.0; stress: lead B down to 0.5, and "dot B unloads only via dot A" | [assumed] |

**Joint distributions are the main unknown.** The sources above give plausible ranges for single parameters, measured on other groups' devices: a single-gate transistor-dot array, and room-temperature thresholds pooled over gates. They do not identify Equal1's cryogenic covariance between cells, chips, wafers, periods and target locations. That covariance is what creates the history advantage, so it is swept ([§12](12-compute-plan.md)) and treated as an assumption until Equal1 data exist ([§14](14-questions-for-equal1.md) Q3).

## 7.3 Charge noise as seen by the gates

- Energy noise converts to gate-voltage noise as √S_V = √S_E/α.
- For 1/f noise, the quasi-static variance is S(1 Hz)·ln(f_high/f_low).
- **Defaults:**
  - f_low = 1/(1000 s) and f_high = 1/t_gate, so the log factor ≈ 22.3 at t_gate = 200 ns;
  - σ_E ≈ 19 µeV and σ_V ≈ 70 µV;
  - dot-to-dot correlation of 0 and 0.5 are both run [assumed].

## 7.4 Fleets

| Fleet | Size | Purpose |
|---|---|---|
| Pilot | 5 wafers × 4 chips × 10 cells (200) | Building, debugging, G0, and sizing the test fleet |
| Train | 50 wafers × 20 chips × 10 cells (10,000) | Reader, tuning logs, priors |
| Validation | 10 wafers × 5 chips × 10 cells (500) | Thresholds, hyperparameters and comparator selection for **all** tuners |
| **Test (in-distribution)** | **20 wafers × 5 chips × 10 cells (1,000)**. The pilot may raise this to at most 40 wafers (sizing rule in [§11.5](11-success-measurement.md#115-statistics)) | **Headline**, run once after the freeze |
| OOD-hot / OOD-noisy / OOD-crosstalk | The **same underlying cells** as test wafers 1–10 (500 cells), changing only: 0.75 K / √S_E = 6.5 with SNR 5 / cross-coupling 0.4–0.6. SNR 5 rather than 3: with the 3:1 sensitivity ratio, SNR 3 would put dot B near 1 per pixel | Paired robustness tests |
| Certificate stress set | 60 wafers × 5 chips × 10 cells (3,000), generated like validation; never test | The [§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) b nominal-noise bar and the stress scenarios |
| OOD-spec (in the trust report; no cost gate) | The same 500 cells, with E_c scaled so that ~10% of cells exceed P_max | What the certificate does when devices fall outside the design tolerance it relies on |
| OOD-wafer | 10 new wafers × 5 × 10, with σ_wafer and Δ_edge ×2 | Fab-level shift |
| OOD-simulator | QDarts, 10 wafers × 2 chips × 10 cells (200); underlying parameters mapped where defined | Finite t_c, non-constant charging energy |

## 7.5 Tuning logs

- Training-fleet logs come from T3 with the frozen reader ([§6.4](06-tuners-and-baselines.md#64-histories-and-tuning-logs)).
- The prior and hierarchy (T5, T6) are fitted only from these logs.
- The generator's parameters are never used for fitting.

## 7.6 External real-device data [sourced; none is 22FDX]

| Dataset | What it is | Labels | What it can test | What it can't |
|---|---|---|---|---|
| **QDSD** ([Zenodo 11402792](https://doi.org/10.5281/zenodo.11402792)), CC-BY-4.0 | Si-MOS and GaAs stability diagrams. The values are measured current. Raw x/y/z files (186 MB) and an interpolated CSV set (127 MB) that loses information | Only single-dot diagrams are labelled (transition lines and charge areas) | A separate single-dot counting experiment: line detection and counting from the empty region, with an observation model adapted to current peaks. Uses the raw files | The two-dot SEB certificate: a current peak is not a sensor step |
| **Delft D-CSD** ([Zenodo 16363472](https://doi.org/10.5281/zenodo.16363472)), CC-BY-4.0 | 9,850 Si/SiGe and Ge/SiGe stability diagrams, selected with a clean/noisy classifier. Raw HDF5 holds voltages and measured values; the default loader resizes to 128×128 (CSD archive 1.8 GB) | Clean/noisy only; no charge counts | Line-detection transfer of the reader on real scans, against our own hand labels; ambiguity analysis | Absolute (1,1) truth, sequential interventions, a fab-level hierarchy |
| **QFlow 2.0 `exp_small`** ([NIST](https://data.nist.gov/od/id/66492819760D3FF6E05324570681BA721894)), registration required | 756 measured scans | No dot / single / double | Optional; first to cut. Test only | — |

**How we use them:**
- Use the raw data, record how each set was selected, and never resize.
- **Labelling is timed before it is promised.** Label 5–10 D-CSD scans first, including ambiguous ones, with the other team member reviewing a subset. Commit to 50 only if that rate fits the external-data cap ([§15.2](15-plan.md#152-tracks-and-hour-caps-design-call)).
- **Static replay is observation evidence only.** A stored scan can't show what the device would have done under a different scan order, dwell time, averaging request or latch state.
- If public data are used to tune preprocessing or thresholds, the test scans are frozen first and never touched.
- QDarts widens the physics tested (tunnel coupling, non-constant charging energy). It is an equilibrium simulator, so it doesn't validate our noise and latching wrapper.

---

← [6. Tuners and baselines](06-tuners-and-baselines.md) · [Index](README.md) · [8. Physics layer: CZ error budget](08-physics-layer-cz-error-budget.md) →
