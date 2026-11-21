"""Sprawdzenie progu 4: uruchamia przykłady dla zadań 4.1-4.5 i zapisuje wyniki
do plików w katalogu 4pkt/results (materiał do raportu).

Plik leży w katalogu 4pkt/ wewnątrz projektu. Otwórz go w VS Code i kliknij ▶ (Run Python File)."""

import subprocess
import sys
import tempfile
import time
import traceback
import warnings
from pathlib import Path

# Katalog główny projektu (o jeden wyżej niż 4pkt/), żeby działał import package_manager.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import z3  # noqa: E402

from package_manager.experiments import SIZES, run_case  # noqa: E402
from package_manager.installer import install  # noqa: E402
from package_manager.knowledge_base import build_knowledge_base  # noqa: E402
from package_manager.loaders import load_repository, load_requests  # noqa: E402
from package_manager.models import EnvironmentState, InstalledPackage  # noqa: E402
from package_manager.requirements_parser import parse_requirement  # noqa: E402
from package_manager.verification import verify_state  # noqa: E402

RESULTS = Path(__file__).resolve().parent / "results"
RESULTS.mkdir(exist_ok=True)
EXAMPLES = ROOT / "examples"
repository = load_repository(EXAMPLES / "repo_example.json")
summary: list[tuple[str, bool]] = []


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


# ---------------------------------------------------------------- 4.1
BAD_FILES = [
    ("niepoprawny JSON", '{"packages": '),
    ("brak pola packages", "{}"),
    ("nieznane pole", '{"packages": {}, "foo": 1}'),
    ("requires nie jest listą", '{"packages": {"a": {"versions": {"1.0": {"requires": "b"}}}}}'),
    ("niepoprawna nazwa", '{"packages": {"bad name!": {"versions": {"1.0": {}}}}}'),
    ("niepoprawna wersja", '{"packages": {"a": {"versions": {"1.x": {}}}}}'),
    ("niepoprawny operator", '{"packages": {"a": {"versions": {"1.0": {"requires": ["b =>1"]}}}}}'),
    ("wersje 1.0 i 1.0.0", '{"packages": {"a": {"versions": {"1.0": {}, "1.0.0": {}}}}}'),
    (
        "pakiety Foo_Bar i foo-bar",
        '{"packages": {"Foo_Bar": {"versions": {"1.0": {}}}, "foo-bar": {"versions": {"1.0": {}}}}}',
    ),
    ("pakiet wymaga samego siebie", '{"packages": {"a": {"versions": {"1.0": {"requires": ["a"]}}}}}'),
    ("pakiet konfliktuje z sobą", '{"packages": {"a": {"versions": {"1.0": {"conflicts": ["a"]}}}}}'),
    ("powtórzony klucz obiektu", '{"packages": {"a": {"versions": {"1.0": {}, "1.0": {}}}}}'),
    ("pusty obiekt versions", '{"packages": {"a": {"versions": {}}}}'),
    ("błąd w drugim wymaganiu", '{"packages": {"app": {"versions": {"2.0": {"requires": ["ok", "x =>1"]}}}}}'),
]


def check_validation(lines):
    lines.append("Każdy niepoprawny plik musi zostać odrzucony z komunikatem wskazującym miejsce błędu.")
    lines.append("")
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "repo.json"
        for title, text in BAD_FILES:
            path.write_text(text, encoding="utf-8")
            try:
                load_repository(path)
            except ValueError as exc:
                message = str(exc).replace(str(path), "repo.json")
                lines += [f"## {title}", f"  komunikat: {message}"]
            else:
                raise AssertionError(f"plik „{title}” został przyjęty, a powinien być odrzucony")
        # Plik z BOM (Notatnik w Windows) musi być poprawnie odczytany.
        path.write_bytes(b"\xef\xbb\xbf" + b'{"packages": {"app": {"versions": {"1.0": {}}}}}')
        assert "app" in load_repository(path).packages
        lines += ["", "Plik z BOM został poprawnie wczytany."]
        # Błąd w pliku żądań ma numer linii.
        requests = Path(folder) / "requests.txt"
        requests.write_text("# komentarz\napp\n\nlib =>1\n", encoding="utf-8")
        try:
            load_requests(requests)
        except ValueError as exc:
            lines.append(f"Plik żądań, błędna linia 4: {str(exc).replace(str(requests), 'requests.txt')}")
        else:
            raise AssertionError("błędne żądanie zostało przyjęte")


# ---------------------------------------------------------------- 4.2
def check_knowledge_base(lines):
    kb = build_knowledge_base(repository)
    versions = len(kb.variables)
    a1 = sum(axiom.label.endswith("co najwyżej jedna wersja") for axiom in kb.axioms)
    a3 = sum("konfliktuje" in axiom.label for axiom in kb.axioms)
    lines += [
        f"repo_example.json: {versions} wersji (zmiennych), {len(kb.axioms)} aksjomatów",
        f"  A1 (co najwyżej jedna wersja): {a1}",
        f"  A2 (zależności): {len(kb.axioms) - a1 - a3}",
        f"  A3 (konflikty): {a3}",
        "",
        "Wszystkie aksjomaty (etykieta -> formuła):",
    ]
    for axiom in kb.axioms:
        lines.append(f"  {axiom.label}\n      {axiom.formula}")


# ---------------------------------------------------------------- 4.3
EXPECTED = [
    (["app"], {"app": "2.0", "lib": "2.0", "util": "2.0"}),
    (["tool"], {"tool": "1.1", "lib": "1.0", "json-slow": "1.0"}),
    (["app", "tool"], {"app": "1.0", "tool": "1.1", "lib": "1.0", "json-slow": "1.0"}),
    (["app", "legacy"], {"app": "1.0", "legacy": "1.0", "lib": "1.0"}),
    (["app==2.0", "tool"], None),
]


def check_install(lines):
    lines.append("żądania | wynik | kryteria (przest. żądanych, liczba pakietów, przest. pozostałych) | weryfikacja")
    for texts, expected in EXPECTED:
        requests = [parse_requirement(t) for t in texts]
        result = install(repository, requests)
        if expected is None:
            assert result is None, f"{texts}: powinno nie być rozwiązania"
            lines.append(f"{texts} | brak rozwiązania | - | brak stanu do sprawdzenia")
            continue
        assert result is not None, f"{texts}: brak rozwiązania"
        got = {p: i.version for p, i in result.state.installed.items()}
        errors = verify_state(repository, result.state, requests)
        lines.append(
            f"{texts} | {dict(sorted(got.items()))} | "
            f"({result.requested_staleness}, {result.package_count}, {result.dependency_staleness}) | "
            f"{'OK' if not errors else errors}"
        )
        assert got == expected, f"{texts}: {got} != {expected}"
        assert not errors, errors
    lines += ["", "Wszystkie wyniki zgodne z tabelą z treści zadania."]


# ---------------------------------------------------------------- 4.4
def check_verifier(lines):
    def state(*items):
        return EnvironmentState({n: InstalledPackage(n, v) for n, v in items})

    good = state(("app", "2.0"), ("lib", "2.0"), ("util", "2.0"))
    cases = [
        ("poprawny stan", good, [parse_requirement("app")], False),
        ("brakujące zależności (app 2.0 samo)", state(("app", "2.0")), [], True),
        ("konflikt (legacy 1.0 z util 2.0)", state(("legacy", "1.0"), ("util", "2.0")), [], True),
        ("pakiet spoza repozytorium", state(("ghost", "1.0")), [], True),
        ("nieistniejąca wersja", state(("util", "9.9")), [], True),
        ("niespełnione żądanie", state(("util", "1.0")), [parse_requirement("app")], True),
        (
            "ten sam pakiet dwa razy",
            EnvironmentState(
                {"util": InstalledPackage("util", "1.0"), "Util": InstalledPackage("Util", "2.0")}
            ),
            [],
            True,
        ),
    ]
    lines.append("Weryfikator (bez solvera) musi znaleźć wszystkie naruszenia w niepoprawnych stanach.")
    lines.append("")
    for title, current, requests, should_fail in cases:
        errors = verify_state(repository, current, requests)
        lines.append(f"## {title}")
        lines.extend(f"  naruszenie: {error}" for error in errors) if errors else lines.append("  brak naruszeń")
        assert bool(errors) == should_fail, f"{title}: nieoczekiwany wynik weryfikatora"
        lines.append("")


# ---------------------------------------------------------------- 4.5
def check_experiment(lines):
    folder = ROOT / "data"
    if not folder.exists():
        raise FileNotFoundError(f"brak {folder} (katalog z danymi grupy musi nazywać się data)")
    lines.append("Grupa k = 26. Czasy: budowa bazy (z wczytaniem plików) i rozwiązanie.")
    lines.append("")
    columns = ["N", "versions", "axioms", "result", "packages", "requested_staleness", "other_staleness"]
    columns += ["build_s", "solve_s", "verification", "warnings"]
    lines.append(" | ".join(columns))
    for size in SIZES:
        row = run_case(folder, size)
        lines.append(" | ".join(str(row.get(column, "")) for column in columns))
        lines.append(f"    żądania: {row['requests']}")
        assert row["verification"] in ("OK", "n/d (brak stanu do sprawdzenia)"), row["verification"]


# ---------------------------------------------------------------- testy
def check_pytest(lines):
    done = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header"],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    lines += done.stdout.strip().splitlines()
    lines += done.stderr.strip().splitlines()
    assert done.returncode == 0, f"pytest zakończył się kodem {done.returncode}"


if __name__ == "__main__":
    started = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")  # ostrzeżenia z danych nie zasłaniają wyników; liczymy je
        print("=== Sprawdzenie progu 4 ===")
        run("4.1 wczytywanie i walidacja", "4_1_walidacja.txt", check_validation)
        run("4.2 baza wiedzy A1-A3", "4_2_baza_wiedzy.txt", check_knowledge_base)
        run("4.3 instalacja do pustego środowiska", "4_3_instalacja.txt", check_install)
        run("4.4 weryfikacja bez solvera", "4_4_weryfikacja.txt", check_verifier)
        run("4.5 eksperyment na danych grupy 26", "4_5_eksperyment.txt", check_experiment)
        run("testy automatyczne (pytest)", "4_6_testy.txt", check_pytest)

    passed = sum(ok for _, ok in summary)
    report = [
        "Podsumowanie sprawdzenia progu 4",
        f"Wersja Z3: {z3.get_version_string()}",
        f"Łączny czas: {time.perf_counter() - started:.1f} s",
        "",
        *[f"[{'PASS' if ok else 'FAIL'}] {name}" for name, ok in summary],
        "",
        f"Wynik: {passed} z {len(summary)} sprawdzeń przeszło.",
    ]
    (RESULTS / "00_podsumowanie.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\nWynik: {passed} z {len(summary)} sprawdzeń przeszło.")
    print(f"Wyniki zapisano w: {RESULTS}")
