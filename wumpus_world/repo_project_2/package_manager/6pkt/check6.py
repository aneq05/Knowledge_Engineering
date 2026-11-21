"""Sprawdzenie progu 6: uruchamia wszystkie przykłady z treści zadania i zapisuje wyniki
do plików w katalogu 6pkt/results (materiał do raportu).

Plik leży w katalogu 6pkt/ wewnątrz projektu. Otwórz go w VS Code i kliknij ▶ (Run Python File)."""

import contextlib
import io
import sys
import time
import traceback
import warnings
from pathlib import Path

# Katalog główny projektu (o jeden wyżej niż 6pkt/), żeby działał import package_manager.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import z3  # noqa: E402

from package_manager.explanations import explain_requests  # noqa: E402
from package_manager.installer import _request_formula, install  # noqa: E402
from package_manager.knowledge_base import build_knowledge_base  # noqa: E402
from package_manager.loaders import load_repository, load_state  # noqa: E402
from package_manager.models import EnvironmentState  # noqa: E402
from package_manager.operations import install_with_state, remove_packages  # noqa: E402
from package_manager.requirements_parser import parse_requirement  # noqa: E402

RESULTS = Path(__file__).resolve().parent / "results"
RESULTS.mkdir(exist_ok=True)
EXAMPLES = ROOT / "examples"

repository = load_repository(EXAMPLES / "repo_example.json")
initial_state = load_state(EXAMPLES / "state_example.txt")
summary: list[tuple[str, bool]] = []


def show_state(state) -> list[str]:
    return [
        f"  {item.package} {item.version}{' manual' if item.manual else ''}"
        for item in sorted(state.installed.values(), key=lambda item: item.package)
    ]


def plan_of(result) -> list[str]:
    return sorted(str(change) for change in result.changes)


def expect(actual: list[str], expected: list[str], lines: list[str]) -> None:
    lines.append("Plan zmian:")
    lines.extend(f"  {line}" for line in actual)
    if actual != sorted(expected):
        lines.append("NIEZGODNE z treścią zadania. Oczekiwano:")
        lines.extend(f"  {line}" for line in sorted(expected))
        raise AssertionError("plan inny niż w treści zadania")
    lines.append("Zgodne z treścią zadania.")


def run(name: str, filename: str, function) -> None:
    """Uruchamia jedno sprawdzenie, zapisuje jego wynik do pliku i dopisuje je do podsumowania."""
    lines: list[str] = [f"# {name}", ""]
    started = time.perf_counter()
    try:
        function(lines)
        ok = True
    except Exception:  # błąd zapisujemy w pliku i kontynuujemy kolejne sprawdzenia
        ok = False
        lines += ["", "BŁĄD:", traceback.format_exc()]
    lines += ["", f"Czas: {time.perf_counter() - started:.2f} s", f"Wynik: {'PASS' if ok else 'FAIL'}"]
    (RESULTS / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary.append((name, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}  ->  results/{filename}")


# ---------------------------------------------------------------- 6.1
def check_empty_state(lines):
    lines.append("Pusty stan: nowe kryteria muszą odpowiadać kryteriom z 4.3 (dwa pierwsze są zerami).")
    lines.append("")
    lines.append("żądania | stary install (przest. żądanych, liczba pakietów, przest. pozostałych) | nowe kryteria [1..5]")
    for texts in [["app"], ["tool"], ["app", "tool"], ["app", "legacy"], ["app==2.0", "tool"]]:
        requests = [parse_requirement(t) for t in texts]
        old = install(repository, requests)
        new = install_with_state(repository, requests, EnvironmentState())
        if old is None or new is None:
            assert old is None and new is None, f"{texts}: tylko jeden wynik jest pusty"
            lines.append(f"{texts} | brak rozwiązania | brak rozwiązania")
            continue
        expected = [0, 0, old.requested_staleness, old.package_count, old.dependency_staleness]
        lines.append(
            f"{texts} | ({old.requested_staleness}, {old.package_count}, {old.dependency_staleness})"
            f" | {new.costs}"
        )
        assert new.costs == expected, f"{texts}: {new.costs} != {expected}"
    lines += ["", "Wszystkie zgodne."]


def check_install_into_state(lines):
    lines += ["Stan początkowy (state_example.txt):", *show_state(initial_state), "", "Żądanie: app==2.0", ""]
    result = install_with_state(repository, [parse_requirement("app==2.0")], initial_state)
    assert result is not None, "brak rozwiązania"
    expect(
        plan_of(result),
        ["podniesienie app 1.0 -> 2.0", "podniesienie lib 1.0 -> 2.0", "usunięcie tool 1.1", "instalacja util 2.0"],
        lines,
    )
    lines += ["", "Stan końcowy:", *show_state(result.state), "", f"Kryteria [1..5]: {result.costs}"]
    assert result.state.installed["app"].manual, "app powinien być oznaczony jako manual"


# ---------------------------------------------------------------- 6.2
def check_remove(lines):
    cases = [
        ("remove lib", ["lib"], False, ["usunięcie app 1.0", "usunięcie lib 1.0", "usunięcie tool 1.1"]),
        ("remove tool z autoremove", ["tool"], True, ["usunięcie tool 1.1", "usunięcie json-slow 1.0"]),
        ("remove tool bez autoremove", ["tool"], False, ["usunięcie tool 1.1"]),
    ]
    for title, names, autoremove, expected in cases:
        lines += [f"## {title}", ""]
        result = remove_packages(repository, names, initial_state, autoremove)
        assert result is not None, f"{title}: brak rozwiązania"
        expect(plan_of(result), expected, lines)
        lines += ["Stan końcowy:", *show_state(result.state), f"Kryteria [1..4]: {result.costs}", ""]


# ---------------------------------------------------------------- 6.3
def verify_core(requests, core) -> list[str]:
    """Niezależnie od funkcji explain: rdzeń musi być sprzeczny, a bez dowolnego elementu spełnialny."""
    kb = build_knowledge_base(repository)
    formulas = {axiom.label: axiom.formula for axiom in kb.axioms}
    for request in requests:
        formulas[f"żądanie użytkownika: {request}"] = _request_formula(request, kb)
    solver = z3.Solver()
    for label in core:
        solver.add(formulas[label])
    report = [f"  sprzeczność całego rdzenia: {'tak' if solver.check() == z3.unsat else 'NIE (błąd!)'}"]
    assert solver.check() == z3.unsat, "rdzeń nie jest sprzeczny"
    for skipped in core:
        solver = z3.Solver()
        for label in core:
            if label != skipped:
                solver.add(formulas[label])
        status = solver.check()
        report.append(f"  bez „{skipped}” -> {'spełnialny (OK)' if status == z3.sat else 'NADAL SPRZECZNY (błąd!)'}")
        assert status == z3.sat, f"rdzeń nie jest minimalny: zbędne „{skipped}”"
    return report


def check_explanations(lines):
    cases = [
        ("app==2.0 + tool (przykład z treści zadania)", ["app==2.0", "tool"]),
        ("legacy + web==2.0 (legacy blokuje util >=2.0, a web==2.0 go wymaga)", ["legacy", "web==2.0"]),
        ("json-fast + json-slow (json-fast konfliktuje z json-slow)", ["json-fast", "json-slow"]),
        ("a==2.0 + b==2.0 (a 2.0 wymaga b <2.0)", ["a==2.0", "b==2.0"]),
    ]
    lines.append(
        "W danych grupy 26 (N = 10..1000) wszystkie żądania miały rozwiązanie, więc wyjaśnienia pokazano "
        "na przykładzie z treści zadania i trzech skonstruowanych przypadkach."
    )
    lines.append("")
    for title, texts in cases:
        requests = [parse_requirement(t) for t in texts]
        core = explain_requests(repository, requests)
        lines += [f"## {title}", "Minimalny sprzeczny podzbiór:"]
        assert core, f"{texts}: brak wyjaśnienia, a rozwiązania nie ma"
        lines.extend(f"  - {label}" for label in core)
        lines.append("Sprawdzenie minimalności (niezależnym solverem):")
        lines.extend(verify_core(requests, core))
        lines.append("")
    assert explain_requests(repository, [parse_requirement("app")]) is None
    lines.append("Dla spełnialnego żądania `app` wyjaśnienie nie jest tworzone (None).")


# ---------------------------------------------------------------- 6.4
def check_scenario(lines):
    from package_manager import scenario

    path = ROOT / "data" / "repo_200.json"
    if not path.exists():
        raise FileNotFoundError(f"brak {path} (katalog z danymi grupy musi nazywać się data)")
    lines += [f"Repozytorium: {path.name}", f"Ziarno generatora: {scenario.SEED}", ""]
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        scenario.main(str(path))
    lines.append(buffer.getvalue().rstrip())
    lines += ["", "Każdy stan pośredni przeszedł verify_state (scenariusz przerwałby się wyjątkiem)."]


if __name__ == "__main__":
    started = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")  # ostrzeżenia z danych nie zasłaniają wyników; liczymy je
        print("=== Sprawdzenie progu 6 ===")
        run("6.1 pusty stan = stary install", "6_1_pusty_stan.txt", check_empty_state)
        run("6.1 install app==2.0 do state_example.txt", "6_1_install_ze_stanem.txt", check_install_into_state)
        run("6.2 usuwanie (remove, autoremove)", "6_2_usuwanie.txt", check_remove)
        run("6.3 wyjaśnianie braku rozwiązania", "6_3_wyjasnienia.txt", check_explanations)
        run("6.4 scenariusz losowy na repo_200.json", "6_4_scenariusz.txt", check_scenario)

    passed = sum(ok for _, ok in summary)
    report = [
        "Podsumowanie sprawdzenia progu 6",
        f"Wersja Z3: {z3.get_version_string()}",
        f"Ostrzeżenia z danych (wymagania bez pasującej wersji): {len(caught)}",
        f"Łączny czas: {time.perf_counter() - started:.1f} s",
        "",
        *[f"[{'PASS' if ok else 'FAIL'}] {name}" for name, ok in summary],
        "",
        f"Wynik: {passed} z {len(summary)} sprawdzeń przeszło.",
    ]
    (RESULTS / "00_podsumowanie.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\nWynik: {passed} z {len(summary)} sprawdzeń przeszło.")
    print(f"Wyniki zapisano w: {RESULTS}")
