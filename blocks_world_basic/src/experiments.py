"""Losowe problemy, pomiary i raport dla punktu 4."""

import csv
import random
from dataclasses import dataclass
from pathlib import Path

from .blocks_world import BlockWorldState, verify_plan
from .dfs import SearchResult, solve_dfs

DEFAULT_SEED = 20261017


@dataclass(frozen=True)
class RandomCase:
    size: int
    number: int
    start: BlockWorldState
    goal: BlockWorldState


def random_state(size: int, generator: random.Random) -> BlockWorldState:
    blocks = list(range(1, size + 1))
    generator.shuffle(blocks)
    supports = [0] * size
    for previous, block in zip(blocks, blocks[1:]):
        supports[block - 1] = 0 if generator.random() < 0.5 else previous
    return BlockWorldState(tuple(supports))


def generate_cases(
    seed=DEFAULT_SEED, min_size=3, max_size=15, cases_per_size=5
) -> tuple[RandomCase, ...]:
    generator = random.Random(seed)
    cases = []
    for size in range(min_size, max_size + 1):
        for number in range(1, cases_per_size + 1):
            start = random_state(size, generator)
            goal = random_state(size, generator)
            while goal == start:
                goal = random_state(size, generator)
            cases.append(RandomCase(size, number, start, goal))
    return tuple(cases)


def generate_report(
    output="reports",
    seed=DEFAULT_SEED,
    node_limit=200_000,
    time_limit=2.0,
) -> tuple[Path, Path]:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    results = []

    for case in generate_cases(seed):
        result = solve_dfs(case.start, case.goal, node_limit, time_limit)
        verified = result.solved and verify_plan(case.start, case.goal, result.moves).valid
        results.append((case, result, verified))

    csv_path = output / "results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["N", "nr", "start", "cel", "status", "długość", "węzły", "czas_s", "weryfikacja"]
        )
        for case, result, verified in results:
            writer.writerow(
                [
                    case.size,
                    case.number,
                    case.start.to_line(),
                    case.goal.to_line(),
                    result.status,
                    len(result.moves) if result.solved else "",
                    result.expanded_nodes,
                    f"{result.elapsed_seconds:.6f}",
                    "OK" if verified else "NIE DOTYCZY/BŁĄD",
                ]
            )

    report_path = output / "report.md"
    report_path.write_text(
        _markdown(results, seed, node_limit, time_limit), encoding="utf-8"
    )
    return report_path, csv_path


def _markdown(results, seed, node_limit, time_limit) -> str:
    lines = [
        "# Raport — Blocks World, wariant podstawowy",
        "",
        "## Metoda",
        "",
        "Zastosowano DFS z backtrackingiem, zbiorem odwiedzonych stanów oraz "
        "limitami czasu i liczby rozwiniętych węzłów. Ruchy są porządkowane "
        "tak, aby najpierw budować od dołu poprawne fragmenty wież docelowych, "
        "a następnie wykonywać ruchy pomocnicze na stół.",
        "",
        f"Ziarno: `{seed}`, limit węzłów: `{node_limit}`, limit czasu: `{time_limit} s`.",
        "",
        "| N | Nr | Start | Cel | Status | Długość | Węzły | Czas [s] | Weryfikacja |",
        "|---:|---:|---|---|---|---:|---:|---:|---|",
    ]
    for case, result, verified in results:
        length = len(result.moves) if result.solved else "—"
        check = "OK" if verified else "NIE DOTYCZY/BŁĄD"
        lines.append(
            f"| {case.size} | {case.number} | `{case.start.to_line()}` | "
            f"`{case.goal.to_line()}` | {result.status} | {length} | "
            f"{result.expanded_nodes} | {result.elapsed_seconds:.6f} | {check} |"
        )

    lines += ["", "## Pełne sekwencje dla N ≤ 8", ""]
    for case, result, _ in results:
        if case.size <= 8:
            lines += [f"### N={case.size}, przypadek {case.number}", ""]
            if result.solved:
                lines += ["```text", *(str(move) for move in result.moves), "```", ""]
            else:
                lines += [f"Przekroczono limit: `{result.status}`.", ""]

    lines += [
        "## Wnioski",
        "",
        "DFS znajduje poprawny plan, ale nie gwarantuje planu najkrótszego. "
        "Dla większych N przestrzeń stanów rośnie bardzo szybko.",
        "",
    ]
    return "\n".join(lines)
