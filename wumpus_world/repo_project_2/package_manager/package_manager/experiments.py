"""Eksperyment 4.5: instalacja do pustego środowiska dla N = 10, 30, 100, 300, 1000.

Uruchomienie (z katalogu głównego projektu):
    python -m package_manager.experiments repos/k26 --group 26
"""

import argparse
import csv
import time
import warnings

from pathlib import Path

from .installer import solve
from .knowledge_base import build_knowledge_base
from .loaders import load_repository, load_requests
from .verification import verify_state

SIZES = (10, 30, 100, 300, 1000)


def run_case(folder: Path, size: int, timeout_ms: int | None = None) -> dict[str, object]:
    # Czas budowy bazy obejmuje wczytanie plików (tak wymaga polecenie).
    start = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        repository = load_repository(folder / f"repo_{size}.json")
        requests = load_requests(folder / f"requests_{size}.txt")
        kb = build_knowledge_base(repository)
    build_seconds = time.perf_counter() - start

    row: dict[str, object] = {
        "N": size,
        "versions": len(kb.variables),
        "axioms": len(kb.axioms),
        "requests": "; ".join(str(request) for request in requests),
        "warnings": len(caught),
        "build_s": round(build_seconds, 3),
    }

    start = time.perf_counter()
    try:
        result = solve(repository, kb, requests, timeout_ms)
    except RuntimeError as exc:  # np. timeout solvera (status unknown)
        row.update(solve_s=round(time.perf_counter() - start, 3), result=f"błąd: {exc}")
        row.update(packages="", requested_staleness="", other_staleness="", verification="n/d")
        return row
    row["solve_s"] = round(time.perf_counter() - start, 3)

    if result is None:
        row.update(result="brak rozwiązania", packages="", requested_staleness="")
        row.update(other_staleness="", verification="n/d (brak stanu do sprawdzenia)")
        return row

    # Niezależna weryfikacja bez solvera.
    errors = verify_state(repository, result.state, requests)
    row.update(
        result="rozwiązanie",
        packages=result.package_count,
        requested_staleness=result.requested_staleness,
        other_staleness=result.dependency_staleness,
        verification="OK" if not errors else "; ".join(errors),
    )
    return row


def write_outputs(rows: list[dict[str, object]], group: str, csv_path: Path, md_path: Path) -> None:
    columns = [
        "N", "versions", "axioms", "requests", "result", "packages",
        "requested_staleness", "other_staleness", "build_s", "solve_s", "verification", "warnings",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    lines = [f"Grupa k = {group}", "", "| " + " | ".join(columns) + " |"]
    lines.append("|" + "---|" * len(columns))
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Eksperyment 4.5")
    parser.add_argument("folder", type=Path, help="katalog z repo_N.json i requests_N.txt")
    parser.add_argument("--group", default="?", help="numer grupy do raportu")
    parser.add_argument("--out", type=Path, default=Path("4pkt/results"), help="katalog na wyniki")
    parser.add_argument("--timeout", type=int, default=None, help="limit czasu solvera w sekundach")
    args = parser.parse_args()
    timeout_ms = args.timeout * 1000 if args.timeout else None

    rows = []
    for size in SIZES:
        print(f"N = {size} ...", flush=True)
        rows.append(run_case(args.folder, size, timeout_ms))
        print(f"  {rows[-1]['result']}, build {rows[-1]['build_s']} s, solve {rows[-1]['solve_s']} s")
    args.out.mkdir(parents=True, exist_ok=True)
    write_outputs(rows, args.group, args.out / "results_4_5.csv", args.out / "results_4_5.md")
    print(f"Zapisano results_4_5.csv oraz results_4_5.md w katalogu {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
