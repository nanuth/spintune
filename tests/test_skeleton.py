"""The package layout in architecture/appendix-a-interfaces-and-code-layout.md exists."""

import importlib

import pytest

MODULES = [
    "spintune.fleet",
    "spintune.device",
    "spintune.interface",
    "spintune.evaluator",
    "spintune.anchor",
    "spintune.reader",
    "spintune.prior",
    "spintune.harness",
    "spintune.tuners",
    "spintune.qiskit_cz",
]


@pytest.mark.parametrize("name", MODULES)
def test_appendix_a_module_imports(name):
    importlib.import_module(name)
