import csv
import random
from dataclasses import dataclass
from pathlib import Path

from .dfs import solve_dfs
from .state import BlockWorldState
from .verifier import verify_plan

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


def save_results(
    output="results/results.csv",
    seed=DEFAULT_SEED,
    node_limit=200_000,
    time_limit=2.0,
) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "ziarno",
                "N",
                "nr",
                "start",
                "cel",
                "status",
                "długość",
                "rozwinięte_węzły",
                "czas_s",
                "weryfikacja",
                "sekwencja_dla_N_do_8",
            ]
        )

        for case in generate_cases(seed):
            result = solve_dfs(case.start, case.goal, node_limit, time_limit)
            if result.solved:
                verified, verification_message = verify_plan(
                    case.start, case.goal, result.moves
                )
            else:
                verified = False
                verification_message = "Nie zweryfikowano - przekroczono limit."

            moves = " -> ".join(map(str, result.moves)) if case.size <= 8 else ""
            writer.writerow(
                [
                    seed,
                    case.size,
                    case.number,
                    case.start.to_line(),
                    case.goal.to_line(),
                    result.status,
                    len(result.moves) if result.solved else "",
                    result.expanded_nodes,
                    f"{result.elapsed_seconds:.6f}",
                    "OK" if verified else verification_message,
                    moves,
                ]
            )

    return output_path


if __name__ == "__main__":
    result_file = save_results()
    print(f"Ziarno generatora: {DEFAULT_SEED}")
    print(f"Wyniki zapisano w: {result_file}")
