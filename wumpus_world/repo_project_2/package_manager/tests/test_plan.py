from package_manager.loaders import load_state
from package_manager.models import EnvironmentState, InstalledPackage
from package_manager.plan import diff_states, save_state


def _state(*items):
    return EnvironmentState({n: InstalledPackage(n, v, m) for n, v, m in items})


def test_diff_has_all_four_kinds():
    old = _state(("app", "1.0", True), ("lib", "1.0", False), ("tool", "1.1", True), ("x", "2.0", False))
    new = _state(("app", "2.0", True), ("lib", "1.0.0", False), ("x", "1.0", False), ("util", "2.0", False))
    text = [str(change) for change in diff_states(old, new)]
    assert text == [
        "podniesienie app 1.0 -> 2.0",
        "usunięcie tool 1.1",
        "instalacja util 2.0",
        "obniżenie x 2.0 -> 1.0",
    ]  # lib 1.0 -> 1.0.0 to ta sama wersja, więc bez zmiany


def test_save_and_load_roundtrip(tmp_path):
    state = _state(("tool", "1.1", True), ("lib", "1.0", False))
    save_state(state, tmp_path / "state.txt")
    assert load_state(tmp_path / "state.txt").installed == state.installed
