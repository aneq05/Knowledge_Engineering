"""Interfejs wiersza poleceń projektu Blocks World."""

from __future__ import annotations

import argparse

from .blocks_world import InputFormatError, read_problem, verify_plan
from .dfs import solve_dfs
from .experiments import DEFAULT_SEED, generate_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Blocks World — wariant podstawowy")
    subparsers = parser.add_subparsers(dest="command", required=True)

    solve = subparsers.add_parser("solve", help="Rozwiąż problem z pliku")
    solve.add_argument("input", help="Plik zawierający stan początkowy i docelowy")
    solve.add_argument("--node-limit", type=int, default=200_000)
    solve.add_argument("--time-limit", type=float, default=10.0)

    report = subparsers.add_parser("report", help="Wygeneruj eksperymenty i raport")
    report.add_argument("--output", default="reports")
    report.add_argument("--seed", type=int, default=DEFAULT_SEED)
    report.add_argument("--node-limit", type=int, default=200_000)
    report.add_argument("--time-limit", type=float, default=2.0)
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "report":
        markdown, csv_file = generate_report(
            args.output,
            args.seed,
            args.node_limit,
            args.time_limit,
        )
        print(f"Zapisano raport: {markdown}")
        print(f"Zapisano dane: {csv_file}")
        return 0

    try:
        start, goal = read_problem(args.input)
    except (OSError, InputFormatError) as exc:
        print(f"Błąd danych wejściowych: {exc}")
        return 2

    result = solve_dfs(
        start,
        goal,
        node_limit=args.node_limit,
        time_limit_seconds=args.time_limit,
    )
    print(f"Status: {result.status}")
    print(f"Rozwinięte węzły: {result.expanded_nodes}")
    print(f"Czas: {result.elapsed_seconds:.6f} s")

    if not result.solved:
        return 1

    print(f"Liczba ruchów: {len(result.moves)}")
    for number, move in enumerate(result.moves, start=1):
        print(f"{number}. {move}")

    verification = verify_plan(start, goal, result.moves)
    print(f"Weryfikacja: {verification.message}")
    return 0 if verification.valid else 3


if __name__ == "__main__":
    raise SystemExit(main())
