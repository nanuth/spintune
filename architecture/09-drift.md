[SpinTune v5 design](README.md) › 9. Drift

# 9. Drift (stretch, C3, first to cut)

- **Injection:** physical, through the persistent telegraph and 1/f processes of [§4.3](04-measurement-interface.md#43-simulation-behind-the-interface-design-call).
- **Monitoring:** every k simulated jobs, a 32×32 reference window. It must **contain at least two transition lines** near V\*; a featureless patch can't be cross-correlated.
- **Detection:** 2D cross-correlation shift against the reference, with no ML. The reader checks the charge state.
- **Ground truth for "needs re-tune":** V\* no longer meets the [§11.2](11-success-measurement.md#112-success-for-one-cell) success definition.
- **Recovery:** a local re-tune seeded at V\*, compared with a restart at equal success definition and total cost.
- **Reuse:** the same check is the convergence test for a multi-dot run, if that stretch goal happens ([§3.4](03-scope-and-device-template.md#34-deferred-and-stretch)).

---

← [8. Physics layer: CZ error budget](08-physics-layer-cz-error-budget.md) · [Index](README.md) · [10. Quantum layer (Qiskit)](10-quantum-layer-qiskit.md) →
