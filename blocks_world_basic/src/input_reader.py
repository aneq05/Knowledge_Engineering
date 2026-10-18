from pathlib import Path

from .state import BlockWorldState


def read_problem(path: str) -> tuple[BlockWorldState, BlockWorldState]:
    lines = [
        line.strip()
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]

    if len(lines) != 2:
        raise ValueError("Plik musi zawierać dwie linie danych: start i cel.")

    try:
        start_values = tuple(map(int, lines[0].split()))
        goal_values = tuple(map(int, lines[1].split()))
    except ValueError:
        raise ValueError("Układy muszą zawierać liczby całkowite.")

    start = BlockWorldState(start_values)
    goal = BlockWorldState(goal_values)

    if start.size != goal.size:
        raise ValueError("Stan początkowy i docelowy muszą mieć tyle samo klocków.")

    return start, goal
