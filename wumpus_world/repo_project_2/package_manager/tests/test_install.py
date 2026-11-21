"""Testy instalacji. Wymagają z3 (pip install z3-solver); bez niego są pomijane."""

import itertools
from pathlib import Path

import pytest

pytest.importorskip("z3")

from package_manager.installer import install  # noqa: E402
from package_manager.loaders import load_repository  # noqa: E402
from package_manager.models import EnvironmentState, InstalledPackage  # noqa: E402
from package_manager.requirements_parser import normalize_name, parse_requirement  # noqa: E402
from package_manager.verification import verify_state  # noqa: E402
from package_manager.versions import version_key  # noqa: E402

EXAMPLE = Path(__file__).parent.parent / "examples" / "repo_example.json"

# Tabela z treści zadania (instalacja do pustego środowiska).
EXPECTED = [
    (["app"], {"app": "2.0", "lib": "2.0", "util": "2.0"}),
    (["tool"], {"tool": "1.1", "lib": "1.0", "json-slow": "1.0"}),
    (["app", "tool"], {"app": "1.0", "tool": "1.1", "lib": "1.0", "json-slow": "1.0"}),
    (["app", "legacy"], {"app": "1.0", "legacy": "1.0", "lib": "1.0"}),
    (["app==2.0", "tool"], None),
]


@pytest.fixture(scope="module")
def repository():
    return load_repository(EXAMPLE)


@pytest.mark.parametrize(("texts", "expected"), EXPECTED)
def test_table_from_assignment(repository, texts, expected):
    requests = [parse_requirement(text) for text in texts]
    result = install(repository, requests)
    if expected is None:
        assert result is None
        return
    assert {p: i.version for p, i in result.state.installed.items()} == expected
    assert verify_state(repository, result.state, requests) == []


def _cost(repository, state, requested):
    """Trzy kryteria z 4.3 liczone niezależnie od solvera."""
    requested_cost = other_cost = 0
    for package, item in state.installed.items():
        order = sorted(repository.packages[package], key=version_key, reverse=True)
        rank = [version_key(v) for v in order].index(version_key(item.version))
        if package in requested:
            requested_cost += rank
        else:
            other_cost += rank
    return requested_cost, len(state.installed), other_cost


def _brute_force(repository, requests):
    """Przegląda wszystkie stany (repozytorium przykładowe ma ok. 46 tys. stanów)."""
    names = list(repository.packages)
    requested = {normalize_name(r.package) for r in requests}
    options = [[None, *repository.packages[name]] for name in names]
    best = None
    for combo in itertools.product(*options):
        installed = {n: InstalledPackage(n, v) for n, v in zip(names, combo) if v is not None}
        state = EnvironmentState(installed)
        if verify_state(repository, state, requests):
            continue
        cost = _cost(repository, state, requested)
        if best is None or cost < best:
            best = cost
    return best


@pytest.mark.parametrize("texts", [["app"], ["tool"], ["app", "tool"], ["lib<2.0", "web"], ["a", "b"], ["json-fast", "legacy"]])
def test_solver_matches_brute_force(repository, texts):
    requests = [parse_requirement(text) for text in texts]
    result = install(repository, requests)
    expected = _brute_force(repository, requests)
    assert expected is not None and result is not None
    got = (result.requested_staleness, result.package_count, result.dependency_staleness)
    assert got == expected
