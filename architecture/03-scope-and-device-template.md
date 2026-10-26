[SpinTune v5 design](README.md) › 3. Scope and device template

# 3. Scope and device template

## 3.1 Primary device: a 22FDX SEB-sensed double dot, modelled on Equal1's cells

```text
 source ── QA0 ── QT0 ── QT1 ── QT2 ── QA1 ── drain        (+ global back gate BG under the buried oxide)
 (QR0)   spacer   └─ SEB ─┘└ dot A ┘└ dot B ┘    spacer (QR1)
          rf reflectometry on the source, 75.5 MHz
```

| | Value | Status |
|---|---|---|
| Gates | QA0, QT0, QT1, QT2, QA1 in series between doped source and drain. QA0 and QA1 are spacers. A back gate reaches the substrate through a via. There are no plunger gates; barrier gates and back gate act as plungers | [sourced] 2412.08422v2, Fig. 1, Table 1 |
| Configuration | SEB + double dot: "a SEB forming between QT0 and QT1, with a double quantum dot forming between QT1, QT2, and QA1". Barriers are formed under QT2 and QA1 | [sourced] Fig. 4c,f |
| Inter-dot barrier | QT2 (the gate shared by the two sensed dots). Held fixed during charge tuning | [inferred] |
| Charge-tuning plane | (QT1, QA1) at fixed QT2 and BG. Each swept gate is next to one dot; the other dot sees it through next-nearest coupling | [design call]. The paper does not name the swept axes; question 1 for Equal1 ([§14](14-questions-for-equal1.md)) |
| Sensor | The SEB, next to QT1. Sweeping QT1 detunes the sensor strongly, so the interface models a **compensated** sensor by default (virtual compensation on QT0). An uncompensated sensor is a stress scenario. Equal1's Fig. 4(c) shows the double-dot response overlaid with SEB transitions, so residual SEB transitions are a second stress scenario ([§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) b) | Compensation [assumed] |
| Sensor sensitivity | Dot A, adjacent to the SEB, gives larger steps than dot B. Ratio 2–4 [assumed], swept. This matters for the certificate's visibility test | [assumed] |
| Reservoirs | The SEB is tunnel-coupled to the source; dot A loads through the QT1 barrier [inferred]. How dot B loads (from the drain through QA1, or only via dot A) isn't stated. Its lead transitions are modelled as prone to latching | [assumed]; question 2 ([§14](14-questions-for-equal1.md)) |
| Carrier | Electrons | [sourced] 2412.08422v2, [2412.08302v1](https://arxiv.org/html/2412.08302v1), [equal1.com/technology](https://www.equal1.com/technology) |
| Published operating data | V_QT1 = 350 / 390 / 420 mV for decoupled / separating / merged dots (transport configuration, where QT1 is the barrier). Data at 700 mK (Figs. 2, 4) and 70 mK (Fig. 3). Lever arm 0.27 eV/V | [sourced]; which gate the lever arm refers to in this configuration is [assumed] |

**Why not the transport configuration?**
- In transport, the dots sit between QT0/QT1 and QT1/QT2 with QT1 as the barrier.
- A series double dot in transport conducts only near triple points, so a charge-sensing reader doesn't apply.

**Status of this template:** our reading of the published papers, not a confirmed Bell-1 specification. The generator is described as *modelled on* the published devices.

**Hidden coupling structure in the generator:**
- Each dot couples to its swept gate with lever arm α. Next-nearest couplings are x_A·α (QA1 → dot A) and x_B·α (QT1 → dot B), with x ~ 0.1–0.4 [assumed].
- QT2 and BG couple to both dots. Their fixed voltages enter as offsets.
- Inter-dot capacitance is ±20%.
- The SEB couples to QT1 and to both dots, with dot A coupled more strongly.

**Secondary template:** a generic double dot with plungers P1 and P2, an inter-dot barrier, and a sensor dot. It's for comparison with the autotuning literature and public datasets.

## 3.2 What "a chip" means here

- Equal1 reports 29 NMOS + PMOS cells per chip (its technology page says 35), each a linear array of at most 3 dots [sourced].
- **The unit of tuning is one cell.**
- A fleet "chip" is 10 cells sharing die-level parameters. A "wafer" groups chips sharing wafer-level parameters ([§7.1](07-fleet.md#71-structure-design-call)).

## 3.3 Simulators

- **QArray 1.6.0** (constant capacitance, Rust backend) [measured].
  - **Use:** all in-distribution and most OOD fleets.
  - **Strengths:** fast, with analytic ground truth (`optimal_Vg`).
  - **Limits:** identical charge cells, no tunnel coupling, no dot formation.
- **QDarts 1.0.5** ([repo](https://github.com/qplai/QDarts), [arXiv 2404.02064](https://arxiv.org/abs/2404.02064), MIT licence) [measured].
  - **Physics:** finite tunnel coupling, an exact thermal state, voltage-dependent tunnel couplings, and non-constant charging energy (which breaks the identical-cell symmetry). It is an equilibrium simulator: white and slow sensor noise, but no dynamics.
  - **Use:** the OOD-simulator fleet.
  - **How it runs:** in its own environment, as a worker process behind the same interface. Latching and 1/f noise are added in our wrapper ([§4.3](04-measurement-interface.md#43-simulation-behind-the-interface-design-call)).
- **Fallback if QDarts misbehaves:** QArray plus our own rounded inter-dot lineshape layer.
- **Not adopted:**
  - SimCATS: no t_c parameter, and a non-commercial licence.
  - QDFlow: no tunnel coupling, and much slower.

## 3.4 Deferred and stretch

Listed so nobody builds them early:
- **6-dot / multi-cell run.** Equal1's published cells are linear arrays of at most 3 dots ([§3.2](#32-what-a-chip-means-here)). Build it only if Equal1 confirms a linear multi-dot layout to tune pair by pair. If so, use iterative sweeps, a 5-pass cap, convergence by cross-correlation ([§9](09-drift.md)), and cold vs per-position prior on ~20 chips. `LayerFidelity`/EPLG would then be the natural chain metric.
- **Stages where per-device search may cost more than charge-state tuning:** sensor operating-point search; barrier and tunnel-coupling setting with QDarts' voltage-dependent couplings; virtual-gate calibration. These are candidates for a follow-up C1 if G0 shows little headroom. They are not designed here.
- t_c and lever-arm estimation in the charge-qubit regime; noise learning; valley physics; real-Equal1 replay.

What scales and what doesn't, for more cells and for more dots per cell: [§18](18-scaling.md).

---

← [2. Goals, non-goals, anti-goals](02-goals-non-goals-anti-goals.md) · [Index](README.md) · [4. The measurement interface](04-measurement-interface.md) →
