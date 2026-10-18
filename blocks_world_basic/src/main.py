import sys

from .blocks_world import InputFormatError, read_problem, verify_plan
from .dfs import solve_dfs


INPUT_FILE = "examples/example.txt"


def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE

    try:
        start_state, goal_state = read_problem(input_file)
        # for testing purpose
        # print(type(start_state))
        # print(type(goal_state))
        # print(start_state.supports)
        # print(goal_state.supports)
    except (OSError, InputFormatError) as error:
        print("Błąd danych wejściowych:", error)
        return

    print("Stan początkowy:", start_state.supports)
    print("Stan docelowy:  ", goal_state.supports)

    result = solve_dfs(start_state, goal_state)

    if result.solved:
        print("\nZnalezione ruchy:")
        for number, move in enumerate(result.moves, start=1):
            print(f"{number}. {move}")

        verification = verify_plan(start_state, goal_state, result.moves)
        print("\nWeryfikacja:", verification.message)
    else:
        print("Nie znaleziono rozwiązania:", result.status)


if __name__ == "__main__":
    main()
