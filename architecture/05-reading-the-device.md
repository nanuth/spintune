[SpinTune v5 design](README.md) › 5. Reading the device

# 5. Reading the device: certificate, count, confirm

## 5.1 The anchor certificate [design call]

A window alone can't tell (1,1) from (2,2) [measured]. Every tuner must therefore show evidence of an **empty (0,0) region** before it may declare a charge state.

**What "certificate" means here.** It is an evidence rule: a fixed list of measurements that must all pass. Under assumptions A1–A4 below, passing it implies that the anchor is empty. Real devices can break those assumptions, so outside the noiseless model its error rate is measured, not guaranteed. An SNR threshold does not by itself bound that error rate.

**Constants (frozen with the fleet spec):**
- **P_max:** the upper end of the design tolerance for the addition voltage along a swept-gate axis. It is part of each scenario's spec.
  - **30 mV** for the in-distribution and OOD QArray fleets (design nominal 15 mV, tolerance ×/÷ 2).
  - **40 mV** for the wide-period scenario.
  - For QDarts, computed from its generator, including the larger first addition energy.
  - The OOD-spec fleet ([§7.4](07-fleet.md#74-fleets)) tests what happens when real devices exceed P_max.
- **r_m,max = 0.3:** the largest shift of one dot's lines when the other dot gains an electron, as a fraction of P.
- **L = 1.25 · (1 + r_m,max) · P_max:** the required transition-free length. That's **49 mV** at P_max = 30 mV and 65 mV at 40 mV.

**The evidence for a candidate empty point v0 (every ray billed; all must hold):**
1. **Axis rays.** For each axis (−QT1 and −QA1), a ray through v0 whose samples show a transition-free stretch of length ≥ L that contains v0, ending in a visible crossing above v0.
   - A ray cast upward from v0 − L·e to the first crossing satisfies this. So does a descent along that axis, if v0 lies in its final free stretch.
   - The crossing is the visibility check: it shows that the sensor responds on this ray.
2. **Diagonal ray.** The stretch from v0 down to v0 − √2·L along (1, 1)/√2 is transition-free. The [§6.1](06-tuners-and-baselines.md#61-the-shared-policy-diagonal-descent-then-axis-rays-design-call) diagonal descent provides it, because v0 is placed √2·L above the point where the descent stopped, inside its free stretch. This is redundancy against one missed line.
3. **Sign and noise floor on rays.**
   - Each crossing's step sign must match electron addition, with the polarity calibrated from the session's first crossings.
   - The noise floor is measured on the transition-free stretch.
   - Rays do **not** decide which dot a line belongs to.
4. **Visibility per dot, in 2D.**
   - The confirmation window ([§5.2](#52-confirmation-and-declaration)) must show the two first lines that bound the certified empty region, with the two distinct orientations: dot-A lines steep in the (QT1, QA1) plane, dot-B lines shallow.
   - Each must reach step SNR ≥ s_min (tuned on validation).
   - **Step SNR** = (step height / per-pixel σ) × √(n/2), for a matched filter averaging n pixels on each side.
   - A tuner may repeat a ray or window to average; repeats are billed.
   - If either dot's first line isn't visible, the tuner abstains; it does not conclude "empty".
5. **Domain.** If any required ray would leave the domain, the tuner abstains.
6. **Validity at v0.** Every ray in the evidence must pass through v0. A ray cast before a later move no longer counts.

**Count:**
- The target (1,1) cell is the region reached from v0 by crossing dot A's first line once and dot B's once, in the addition direction, and no other line.
- Dot identity comes from orientation in the 2D confirmation window.
- Inter-dot lines on a ray count as transitions: they reset the transition-free stretch.
- No hypothesis tracking is needed, because nothing about absolute charge numbers is inferred before the certificate.

**Noiseless argument** (a written statement, separate from any Monte Carlo):
- **Assumptions:**
  - **A1. Electrostatics:** constant capacitance. At fixed occupancy each dot's electrochemical potential is linear in the gate voltages, and lowering a swept gate raises every dot's potential.
  - **A2. Period bound:** along each swept axis, at fixed occupancy of the other dot, every addition voltage of the dot next to that gate, including the first, is ≤ P_max.
  - **A3. Equilibrium:** along each ray, the occupancy is the ground state. There is no latching, and thermal broadening is below one pitch.
  - **A4. Detection:** the reader reports every occupancy change along a ray and nothing else. The sensor response is visible and correctly signed, and the sensor has no transitions of its own.
- **Claim:** if v0 lies in a transition-free stretch of length ≥ P_max along −QT1, dot A is empty at v0. If it lies in one along −QA1, dot B is empty. Together, v0 is (0,0).
- **Argument (dot A; dot B is the same):**
  - On a transition-free stretch the occupancy (n_A, n_B) is constant (A3, A4). Suppose n_A ≥ 1 on it.
  - At the stretch's upper end c, the n_A-th electron is bound, μ_A(n_A) ≤ 0, and the next one is not, μ_A(n_A + 1) > 0.
  - Moving down the −QT1 axis raises μ_A at the rate set by that gate's lever arm (A1). So the n_A-th electron leaves within one addition voltage, (μ_A(n_A+1) − μ_A(n_A))/α ≤ P_max (A2), below c.
  - That transition lies inside the stretch, a contradiction.
  - Any other transition that happens first (dot B unloading through cross-coupling, or an inter-dot transfer) also lies inside the stretch, so it is also a contradiction.
  - So n_A = 0 everywhere on the stretch, including at v0.
- **Margins:** the argument needs only P_max, because the other dot's occupancy is constant on a transition-free stretch. The rule uses L = 1.25·(1 + r_m,max)·P_max anyway: the 1.25 covers pitch quantisation and uncertainty in P_max, and (1 + r_m,max) covers devices outside constant capacitance (QDarts, real cells), where the spacing can shift with the other dot's occupancy. Whether a shorter L is safe under noise is measured by the T3-L sweep ([§6.3](06-tuners-and-baselines.md#63-comparisons-each-one-answers-a-different-question) f), not assumed.
- **What breaks it:**
  - a period above P_max (A2; the OOD-spec fleet);
  - a dot that can't unload within the ray, for example dot B if it loads only through dot A (A3);
  - a missed or invented line from weak dot-B response, sensor detuning, compensation error or SEB background transitions (A4).

  Two rays can miss the same line for the same reason. The diagonal adds redundancy, not independence.

**Evidence so far:**
- On noiseless QArray devices with perfect occupancy readout, a descent along one axis at a time with the period-bounded length made 0 errors on 300 devices at each of two start spreads (P = 5–40 mV, L = 65 mV). With a fixed 22.5 mV length it failed on 8–15% [measured].
- In the metered estimate of the adopted policy, there were 0 wrong anchors in 3,600 runs (300 cells × 6 tuner configurations × 2 fleets). With the 22.5 mV length, T3 made 4/300 wrong anchors in the wide fleet [measured].
- Neither test covers the full evidence rule under noise. Claims about its error rate wait for B1 ([§15.3](15-plan.md#153-tasks-needs--hard-dependencies-done--the-check-that-must-pass)).

**Pre-registered contingency:** if the ray-only certificate's wrong-anchor rate on the nominal-noise set exceeds 0.5%, a depletion window below v0 is added: 16×16 at 4 mV (256 px, spanning 64 mV ≥ L at P_max = 30 mV), or 32×32 at 4 mV in the wide-period scenario. This is decided before the freeze.

**Required tests (part of G1 and G2):**
- **(a) Noiseless, through the metered session:** the whole evidence rule (descent, axis rays, signs, 2D visibility, domain refusal, declaration), across the scenario's full P range up to P_max and the full cross-coupling range. Every cell is either counted correctly or abstains.
- **(b) Noisy and stress.** These run on ≥ 3,000 noisy cells from validation-type wafers, never test wafers, so that zero errors gives a one-sided 95% bound of 0.1%.
  - **Nominal noise:** sensor SNR 5–30, telegraph noise, latching at the [§7.2](07-fleet.md#72-parameters-defaults-and-sweep-ranges) rates. Bar: observed wrong-anchor rate ≤ 0.5%, with its upper bound reported.
  - **Stress scenarios, reported without a bar:**
    - **low SNR:** SNR 3, where dot-B steps are about 1σ per pixel;
    - **correlated missed transitions:** a dot-B step suppressed on both its axis ray and the diagonal (sensor on a flat part of the SEB peak);
    - **persistent latching:** the dot-B lead rate lowered until unloading takes longer than a ray (Γ_B = 10³, 10², 10 s⁻¹), plus Γ_B = 0, "dot B unloads only via dot A" ([§4.3](04-measurement-interface.md#43-simulation-behind-the-interface-design-call));
    - **SEB background transitions** overlaid on the dot response, with 0–20% compensation error;
    - **sensor detuning** that changes the step size along a ray, including a sign flip past the Coulomb peak;
    - **out-of-spec periods** (OOD-spec).
  - **Reported separately for every scenario:** wrong anchors (v0 not (0,0)); wrong final counts (V\* not in (1,1)); correct counts with inadequate margin. The last two are wrong declarations ([§11.2](11-success-measurement.md#112-success-for-one-cell)).
- **(c) Ambiguity test:**
  - Take two cells whose local scans around the start point are identical, but whose targets lie several periods apart.
  - The policy must not declare before certification, and must declare correctly after it.

## 5.2 Confirmation and declaration

- **Window:** one 16×16 window at the predicted (1,1) centre.
  - **Pitch:** the largest allowed value ≤ P_est/4 (≥ 4 px per period).
  - Allowed pitches are a factor 2 apart, so the span is always 2–4·P_est for P_est from 2 to 32 mV.
  - Above 32 mV (wide-period scenario only), a 32×32 window at 4 mV is used instead.
- **What it must show:** the (0,0) corner, both certified first lines, and the (1,1) cell. The count is then visible in 2D within one billed query.
- **Period check:** if the period fitted in the window differs from P_est by more than 20%, the tuner retries with the corrected value (billed).
- **Declared point V\*:** the point inside (1,1) with the largest margin from the fitted bounding lines.
- **Margin:** **≥ 0.15·P_est** along each bounding line's normal, **and** ≥ 3σ of quasi-static gate noise projected onto that normal ([§7.3](07-fleet.md#73-charge-noise-as-seen-by-the-gates)). The margin is geometric, on the nominal device; telegraph shifts can exceed it, which hold success measures ([§11.2](11-success-measurement.md#112-success-for-one-cell)).
- **Retries** are allowed and billed.
- **Outcome:** the tuner either declares V\* or abstains with a reason.

## 5.3 Reader contract [design call]

**Reader v1 is signal processing**, shared by all tuners. A small CNN (U-Net-lite with a 1D ray head) replaces it only if, on validation, the CNN lowers the wrong-anchor rate, or the abstention rate at an equal wrong-anchor rate, by a margin fixed before training (default 25% relative). The choice is frozen at the end of week 2, before the training-fleet logs are generated (D1), and recorded in the tag.

- **Rays (v1):** a matched-filter step detector. It takes the difference of means over n samples on each side and thresholds it against the noise floor measured on the ray's own flat stretches.
- **Windows (v1):** gradient and structure-tensor orientation separate steep (dot A) from shallow (dot B) lines. Hough plus least squares fits the bounding lines. Inter-dot lines are the short segments joining the two families.
- **Output contract** (the same for v1 and the CNN):
  - **Input:** a normalised window or ray, plus its pitch.
  - **Per pixel, windows (multi-label):** dot-A line, dot-B line, inter-dot line. Pixels where two families meet, such as triple points, carry both labels.
  - **Per sample, rays:** transition or none, plus step amplitude and sign.
    - Ray transitions are given a dot only provisionally, by step height and spacing, and only to estimate P ([§6.1](06-tuners-and-baselines.md#61-the-shared-policy-diagonal-descent-then-axis-rays-design-call)).
    - The 2D window is the authority on which dot a line belongs to.
  - **Window-level head:** {no transitions, lines present, bad}. The "bad" class (low SNR, latching artefact) feeds abstention.
  - **Abstention:** a confidence map, plus an abstain flag when confidence along the detected lines falls below a threshold tuned on validation.
- **Labels from the evaluator** (to score both readers and to train the CNN):
  - **QArray:** a pixel is a dot-A line if dot A's occupancy changes between it and a neighbour, and so on.
  - **QDarts:** a pixel is labelled where the *dominant* charge configuration changes. Pixels where no configuration reaches probability 0.9 are marked as a transition zone. Line positions are the 0.5-probability contours.
- **Not the reader's job:** the charge count. That comes from the certificate and count, which are algorithmic and tested separately.
- **CNN training data:** windows and rays from the training fleet only, mixed across pitches and noise levels.

## 5.4 Oracle-assisted development mode

- During development, each tuner also runs with a perfect reader (masks supplied by the evaluator). This tests the search geometry and the budget before reader errors are added.
- These results are labelled "oracle-assisted" and are never mixed with sensor-only results.

---

← [4. The measurement interface](04-measurement-interface.md) · [Index](README.md) · [6. Tuners and baselines](06-tuners-and-baselines.md) →
