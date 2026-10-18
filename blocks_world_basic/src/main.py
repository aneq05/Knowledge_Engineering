import sys

from .dfs import solve_dfs
from .input_reader import read_problem
from .verifier import verify_plan


INPUT_FILE = "examples/example.txt"


def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE

    try:
        start_state, goal_state = read_problem(input_file)
    except (OSError, ValueError) as error:
        print("Błąd danych wejściowych:", error)
        return

    print("Stan początkowy:", start_state.supports)
    print("Stan docelowy:  ", goal_state.supports)

    result = solve_dfs(start_state, goal_state)

    if result.solved:
        print("\nZnalezione ruchy:")
        for number, move in enumerate(result.moves, start=1):
            print(f"{number}. {move}")

        valid, message = verify_plan(start_state, goal_state, result.moves)
        print("\nWeryfikacja:", message)
    else:
        print("Nie znaleziono rozwiązania:", result.status)


if __name__ == "__main__":
    main()
