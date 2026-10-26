[SpinTune v5 design](README.md) › 8. Physics layer: CZ error budget

# 8. Physics layer: the Qiskit CZ error-budget study (C2)

## 8.1 Conventions [design call]

- Energies are in µeV; frequencies (J/h, ΔE_z/h) in MHz.
- **Exchange:** J = 4·U·t_c² / (U² − ε²) ([QTCAD](https://docs.nanoacademic.com/qtcad/theory_spin_fem/exchange/)). ε is measured from the (1,1) centre along the detuning axis.
- **Validity:**
  - t_c ≤ 0.1·(U − |ε|) [assumed];
  - gate voltages inside the domain;
  - **J_max ≤ ΔE_z/5**, the pulse limit ([§8.2](#82-cz-gate-model-measured-checks)).
- **Barrier control:** t_c = t₀·10^((V_QT2 − V₀)/V_dec), with V_dec swept over 33–110 mV per decade ([2410.15590v2](https://arxiv.org/html/2410.15590v2), [2411.13882](https://arxiv.org/abs/2411.13882)) [sourced].
  - In this configuration the inter-dot barrier is QT2 ([§3.1](03-scope-and-device-template.md#31-primary-device-a-22fdx-seb-sensed-double-dot-modelled-on-equal1s-cells)). The paper's 350–420 mV values refer to QT1 in the transport configuration.

## 8.2 CZ gate model [measured checks]

```text
H(t) = (J(t)/4)(XX + YY + ZZ) + (ΔE_z/4)(ZI − IZ)     ΔE_z = difference of the two qubit frequencies
       odd-subspace splitting = √(J² + ΔE_z²)
Hann pulse: J(t) = J_max · sin²(π t / T),  T = 1/J_max  (∫J dt = 1/2)
local Z corrections calibrated once at nominal, in the ΔE_z rotating frame
```

**Propagation:**
- |00⟩ and |11⟩ only pick up a phase, so the exact propagator reduces to a 2×2 problem in the odd subspace.
- It is computed in closed form per time slice and vectorised over noise draws.
- It matches the 4×4 matrix exponential to 7×10⁻¹⁵ [measured].

**Checks** (`cz_v3_check.py`, `cz_v3_scan.py`):
- **Nominal Hann error** oscillates with J_max/ΔE_z. The worst case up to a given ratio is:
  - ≤ 1×10⁻⁶ up to 0.15;
  - ≤ 3.4×10⁻⁶ up to 0.21;
  - ≤ 1×10⁻⁴ up to 0.35.

  **The design limit is J_max ≤ ΔE_z/5.**
- **Quasi-static δJ with fixed corrections:**
  - The error is close to the pure-ZZ form 1 − F = 0.8·sin²(δφ/4), with δφ = π·δJ/J.
  - The full Hamiltonian adds ≈ 1.15·(J_max/ΔE_z)² relative excess.
  - So the formula is a **large-gradient approximation**, valid to 1% for J_max/ΔE_z ≤ 0.09. At J_max = ΔE_z/5, the full result is ≈ 5% higher.
- **Square pulses** need synchronisation with the Zeeman splitting. They are not used.
- **Equal1's CZ** is 200 ns, with F_CZ = 99.30% at 350 mK and 98.41% at 750 mK (Si/SiGe, [2412.01920 v3](https://arxiv.org/html/2412.01920v3)) [sourced].
  - A 200 ns Hann pulse means J_max = 5 MHz.
  - That's within J_max ≤ ΔE_z/5 for ΔE_z ≥ 25 MHz.

## 8.3 Noise and error-budget components

The components are **composed as channels**, not added as infidelities.

| Component | Model | Inputs |
|---|---|---|
| Charge noise through J | Per shot or RB sequence, draw one quasi-static (δε_A, δε_B, δV_QT2) from [§7.3](07-fleet.md#73-charge-noise-as-seen-by-the-gates) and hold it for the whole circuit. Evaluate J exactly, so second order at ε = 0 is kept | [§7.3](07-fleet.md#73-charge-noise-as-seen-by-the-gates); ε, U, V_dec |
| Single-qubit dephasing during the gate | Quasi-static frequency noise with total σ_f set by T2* = 5.9–11.1 µs [sourced, 2412.01920 v3]. The charge-noise part is (∂f/∂ε)·σ_ε. It must not exceed σ_f; the remainder is attributed to other quasi-static sources | ∂f/∂ε [assumed, micromagnet scenario] |
| Residual coherent pulse error | From the Hann-pulse Hamiltonian | J_max, ΔE_z (20–300 MHz) [assumed] |
| Residual floor | Depolarising, applied last | Derived below |

**Composition:**
- Per noise draw, the charge-noise, dephasing and pulse terms enter one Hamiltonian and are propagated together. Averaging over draws gives the model's channel and its average gate fidelity F_model.
- **Residual floor:** a depolarising channel of strength λ applied after the model channel gives F_total = (1 − λ)·F_model + λ/d, with d = 4. So λ = (F_model − F_CZ)/(F_model − 1/d) reaches Equal1's reported F_CZ at the nominal point. For a perfect model channel this reduces to Aer's λ = (1 − F_CZ)·d/(d − 1) ([Aer docs](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.depolarizing_error.html)).
- **Rejection rule:** if F_model is already below the reported fidelity, the residual would need negative noise. Such parameter sets are rejected and counted, not clipped.
- **No double counting:** charge noise enters once, through J and through (∂f/∂ε). T2* is the total quasi-static dephasing, not an extra term. Parameter sets with (∂f/∂ε)·σ_ε > σ_f are rejected.
- Matching the floor to one reported fidelity does not identify its physical cause. The floor is labelled as unexplained.

## 8.4 Why the tuner doesn't estimate these parameters

- **t_c:** at Equal1's exchange (J ≈ 2.5–5 MHz, U ≈ 2 meV), t_c ≈ 2–3 µeV. A polarisation-line fit ([DiCarlo et al., PRL 92, 226801](https://arxiv.org/abs/cond-mat/0311308)) constrains t_c only for t_c ≳ 0.5·k_BT_e ≈ 13 µeV at 0.3 K.
- **α:** the thermal linewidth (≈ 3.5·k_BT/α ≈ 0.34 mV) is below the 0.5 mV minimum pitch.
- **∂f/∂ε and ΔE_z:** charge measurements can't see them.

So C2 is a **model-based map over sourced and assumed ranges**, not a tuner capability.

## 8.5 The study and its expected outcome

**Two labelled platform scenarios [design call]** (Equal1 question 7, on the platform, is still open):

| Scenario | Charge noise | T2*, CZ duration and floor | Status |
|---|---|---|---|
| **S1: Equal1's measured device (Si/SiGe)** | √S_E 0.3–1 µeV/√Hz ([2209.07242](https://arxiv.org/abs/2209.07242)) | T2* 5.9–11.1 µs; 200 ns CZ; floor set to F_CZ = 99.30% (350 mK) ([2412.01920 v3](https://arxiv.org/html/2412.01920v3)) | Calibrated to a published device |
| **S2: 22FDX projection** | √S_E 1.7–6.5 µeV/√Hz ([§7.2](07-fleet.md#72-parameters-defaults-and-sweep-ranges)) | S1's T2*, pulse and floor reused as placeholders | **Projection**, labelled so on every figure |

The O1 statement is made separately for each scenario.

**Map** the CZ error budget (each [§8.3](#83-noise-and-error-budget-components) component, and the total) over:
- ε ∈ [−U/2, U/2];
- J_max ∈ [1 MHz, ΔE_z/5];
- ΔE_z ∈ [20, 300] MHz;
- √S_E over its sourced range, with dot-to-dot correlation 0 and 0.5;
- ∂f/∂ε over its assumed range.

Full propagation is used everywhere (0.3 core-hours, [measured basis]). The ZZ formula serves only as a cross-check inside its validity range.

**Two rules are marked on the map:**
- **O0:** cell centre, default barrier;
- **O1:** ε = 0 with J_max = ΔE_z/5.

**Back-of-envelope with the defaults** (pure-ZZ, so valid at small J_max/ΔE_z):
- **Barrier channel:** δJ/J ≈ 0.3%, so infidelity ≈ 4×10⁻⁶, independent of the barrier setting.
- **Detuning channel** at ε = U/2: infidelity ≈ 0.7–1.5×10⁻⁴; negligible at ε = 0.
- **Dephasing** during a 200 ns gate: of order 10⁻³.
- **Pulse error:** ≤ 3.4×10⁻⁶ at J_max ≤ ΔE_z/5.
- **For comparison:** Equal1's measured CZ error is ≈ 7×10⁻³.

**Expected result (a sensitivity study, conditional on the model):**
- Charge noise through J is at most a few percent of the budget.
- The best point is ε = 0 with J at the pulse limit, i.e. rule O1. That optimum may mostly reflect the model's assumptions (first-order insensitivity at ε = 0, the imposed pulse limit), so it is stated as conditional on them.
- If the map confirms this, the result is the budget figure plus, per scenario: *"Under these assumptions, O1 is sufficient; the remaining two-qubit error is dephasing and the unexplained floor"*. In S2 that claim covers only the FD-SOI charge-noise channel.
- If some regions lose ≥ 0.1 percentage points under O1, those regions are the result.
- **What C2 does not show:** that the tuner's electron count is right, or that physical gate fidelity improves.

---

← [7. The fleet](07-fleet.md) · [Index](README.md) · [9. Drift](09-drift.md) →
