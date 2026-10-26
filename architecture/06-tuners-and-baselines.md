[SpinTune v5 design](README.md) › 6. Tuners and baselines

# 6. Tuners and baselines

## 6.1 The shared policy: diagonal descent, then axis rays [design call]

Every search tuner except T2 runs this policy. They differ only in what they know before the first query:
- a start point s;
- a belief about the charge period, summarised by a point estimate P̂ and its 5th percentile P_lo.

Every tuner also knows the scenario's design spec, including P_max, because the evidence rule needs it.

1. **Measure the period first, but only if it pays.**
   - The test: would a known period allow a coarser pitch than P_lo does, i.e. is pitch(P_lo) < pitch(0.9·P̂)?
   - If so, first cast one 64-sample ray centred on s along +QT1, at the finest pitch spanning ≥ 2·P_max: 1 mV when P_max ≤ 32 mV, otherwise 2 mV.
   - If that ray shows ≥ 2 same-dot crossings, P is measured, and P_lo becomes 0.9 × the measured value.
2. **Pitch.** Use the largest allowed pitch ≤ P_lo/3, which gives ≥ 3 samples per period.
3. **Descend** along −(1, 1)/√2 from s until the stretch since the last transition is ≥ √2·L + P_lo.
   - Each query is sized for the free length still missing plus one period, rounded up to 16, 32 or 64 samples, and shrunk to the largest of those that fits above the domain floor.
   - The descent never goes below the point where the certificate would leave the domain. If it would have to, the tuner abstains.
   - **Why diagonal:** descending one axis at a time stalls while the other dot is still occupied, because that dot's lines cross the axis every P/x, which can be shorter than L. In the idealized estimate that made T3 abstain on 19–22% of cells, against 0–1% for the diagonal descent [measured].
4. **Certify** ([§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call)) at v0 = the descent's stopping point + √2·L along (1, 1)/√2. v0 sits inside the free stretch, so the descent itself is the diagonal ray through v0.
   - Cast one ray per axis from v0 − L·e upward to the first crossing, plus 2 samples.
   - If either ray shows a transition below v0, restart the descent from v0 − L·e.
   - If P is still unknown, cast one 64-sample ray above the first dot-A line to measure it.
5. **Confirm** with the [§5.2](05-reading-the-device.md#52-confirmation-and-declaration) window at the corner plus the estimated half-periods. Retry (billed) if the fitted period differs from the estimate by more than 20%.
6. **Declare V\* or abstain.**

This is the policy simulated in `checks/headroom_v4.py` with a perfect reader ([§1.2](01-design-decisions-and-evidence.md#12-evidence-status-25-oct-2026)). It is one reasonable way to collect the [§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) evidence, not the cheapest possible. T★'s cost is a reference for this policy, not a floor.

The prior **never** sets absolute charge numbers. It only chooses s, the query sizes and the pitch.

**Tuning:** query sizing beyond the rules above, ordering and retry logic are tuned on validation to minimise T3's all-cell RF time ([§1.1](01-design-decisions-and-evidence.md#11-decisions-this-document-makes-design-calls-confirm-or-override)), and every tuner uses the same values. Pixels are reported for that same policy.

## 6.2 Tuners

| ID | Tuner | Starting knowledge | What it isolates |
|---|---|---|---|
| T★ | **Oracle start:** the shared policy from the true (1,1) centre, with the true P | Truth (evaluator) | **Oracle-start reference:** what this policy's evidence costs when the start is perfect. It is not a lower bound for other policies |
| T0 | **Random start:** the shared policy from a uniformly random point in the domain, with the design-spec period belief (as T3) | No start knowledge; the design spec only for P and P_max | What a search costs without a start point |
| T2 | **Scan-and-fit:** 3×3 mosaic at 4 mV (36,864 px); fit lines with reader v1's Hough + least squares; compute the target from the fitted lines; then the [§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) evidence and confirmation. A simple fitter, not a research project | Design spec only | The physics baseline an Equal1 engineer would propose, and a validation comparator. Expensive in pixels, strong on reliability |
| T2-N | **T2 with its native count:** counts lines from the mosaic's empty corner and declares, without the [§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) rays | Design spec only | A credible heuristic without the extra verification ([§6.3](#63-comparisons-each-one-answers-a-different-question) f) |
| T3 | **Ray navigation, cold:** the shared policy with only the **design spec**: s = design-nominal target (the domain centre), P̂ = 15 mV, P_lo = 7.5 mV (the tolerance's lower end). Its period belief allows only a 2 mV pitch, so it measures P first | Design spec | Competitive classical method, in the spirit of ray-based state identification ([Zwolak et al., PRX Quantum 2, 020335 (2021)](https://arxiv.org/abs/2102.11784)) |
| T3-M | **Fleet-mean start:** T3 with s = the fleet-mean target and P̂, P_lo from the fleet's period distribution (all from training logs) | Fleet mean and spread | "What do fleet statistics alone give?" With the default Δ_nom = 0 it differs from T3 only through the P belief, so it is expected to be about equal [measured, idealized: 1.00× in pixels in-distribution, 0.94× in the wide fleet]. It differs more in the Δ_nom sweep |
| T3-H | **Conventional history:** T3 with s = the running mean of its *own earlier declared* V\* on this chip. For a chip's first cell, s = the running mean over this wafer's earlier chips; with no history at all, the design spec. P̂ = the median of its own earlier measured periods and P_lo their 5th percentile, or the T3-M belief while fewer than 3 exist | Own chip and wafer history | The strongest classical use of the same information as T6 |
| T3-L(ℓ) | **Stopping-length sweep:** T3 with the transition-free length L replaced by ℓ ∈ {1.5·P_nom, 0.5·L, 0.75·L, L} everywhere: the descent stretch (√2·ℓ + P_lo), the axis rays and the diagonal | Design spec | The cost–risk curve: what a shorter stopping rule saves, and what it costs in wrong declarations ([§6.3](#63-comparisons-each-one-answers-a-different-question) f) |
| T5 | **SpinTune-F:** the shared policy with s and the period belief from the fleet prior (hierarchical empirical Bayes, fitted from training logs, with a radial term from die position) | Fleet | Value of a learned fleet prior |
| T6 | **SpinTune-H:** T5 plus this chip's and this wafer's own earlier traces, combined by hierarchical shrinkage into a posterior over the chip's offset, scales and P | Fleet + own history | **Headline candidate** |

**Optional, first to cut:**
- **T6-NN:** a learned set encoder or probe CNN in place of shrinkage. Kept only if it beats T6 on validation by ≥ 10% cost.
- **T-BO:** BoTorch with a prior from tuning logs, as a literature-style comparator. It is not the search policy: a scalar window score can't count electrons, and its per-step overhead (0.05–0.17 s [measured]) exceeds the simulation itself.

**Ablations:**
- T6 with start knowledge only, and with period knowledge only ([§6.3](#63-comparisons-each-one-answers-a-different-question) g).
- T6 with the prior fitted on unfiltered logs ([§6.4](#64-histories-and-tuning-logs)).
- T5 without the radial term.
- Per-query-reset noise ([§4.3](04-measurement-interface.md#43-simulation-behind-the-interface-design-call)).

## 6.3 Comparisons (each one answers a different question)

| | Comparison | Question |
|---|---|---|
| (a) | T6 vs T5, and T3-H vs T3 | Does history help, within the same policy? |
| (b) | **T6 vs T3-H** | With equal information, does learned inference beat a conventional running mean? |
| (c) | T5 vs T3, and T3-M vs T3 | What does the fleet prior give, and what does the fleet mean alone give? |
| (d) | T6 vs the **primary classical comparator** | Is it better than the best classical option? The comparator is chosen on validation among {T2, T3, T3-M, T3-H}, as the one with the lowest paired cost among those meeting T6's reliability minus 2 points. It is frozen at the tag. It is never chosen as the minimum on test |
| (e) | Everything vs T★ | How much avoidable cost is left within this policy? |
| (f) | T2 vs T2-N, and the T3-L(ℓ) curve | What does the extra verification cost, at a matched wrong-declaration rate? |
| (g) | T6 with start knowledge only vs period knowledge only | Which part of the history does the work? |

## 6.4 Histories and tuning logs

- **Test-time history:** only *that tuner's own* earlier traces on this chip and wafer. That includes its declarations (right or wrong), the lines and periods it measured, and its abstentions. Never evaluator truth.
- **Tuning order:** fixed and random, set by seed.
  - Chips are tuned in order on their wafer; chip j sees chips 1…j−1.
  - Cells are tuned in order on their chip; cell k sees cells 1…k−1.
  - Every tuner uses the same order.
- **Reported:**
  - totals over all 10 cells per chip, including the cold first cell and any failures;
  - the gain as a function of k.
- **Training logs:** T3 runs with the frozen reader ([§5.3](05-reading-the-device.md#53-reader-contract-design-call)) over the training fleet.
  - Each log entry has a downstream-verification flag. In simulation it is the evaluator's judgement; on hardware it has to come from an independent downstream measurement ([§14](14-questions-for-equal1.md) Q4). This mirrors how a fab learns which bring-ups worked.
  - The prior is fitted on **verified** logs [design call]. An ablation fits it on unfiltered logs.
- **Prior file:**
  - the fleet mean of the target;
  - covariances at wafer, chip and cell level;
  - the radial coefficient;
  - the P model.

---

← [5. Reading the device](05-reading-the-device.md) · [Index](README.md) · [7. The fleet](07-fleet.md) →
