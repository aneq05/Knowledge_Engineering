// Kod wyświetlany w panelu. Numery linii w trace.js odnoszą się do tych kopii.
// String.raw zachowuje sekwencje takie jak \n w kodzie Pythona.
window.BlocksWorldDFS = {
  sources: {
    "dfs.py": String.raw`from dataclasses import dataclass
from time import perf_counter

from .state import BlockWorldState, Move


@dataclass(frozen=True)
class SearchResult:
    status: str
    moves: tuple[Move, ...]
    expanded_nodes: int
    elapsed_seconds: float

    @property
    def solved(self) -> bool:
        return self.status == "solved"


def solve_dfs(
    start: BlockWorldState,
    goal: BlockWorldState,
    node_limit: int = 200_000,
    time_limit_seconds: float = 10.0,
) -> SearchResult:
    started = perf_counter()
    stack = [start]
    visited = {start}
    parent: dict[BlockWorldState, tuple[BlockWorldState, Move]] = {}
    expanded = 0

    while stack:
        elapsed = perf_counter() - started
        if elapsed >= time_limit_seconds:
            return SearchResult("time_limit", (), expanded, elapsed)
        if expanded >= node_limit:
            return SearchResult("node_limit", (), expanded, elapsed)

        state = stack.pop()
        if state == goal:
            return SearchResult(
                "solved", _build_plan(start, goal, parent), expanded, elapsed
            )
        expanded += 1

        moves = _ordered_moves(state, goal)
        for move in reversed(moves):
            next_state = state.apply(move)
            if next_state not in visited:
                visited.add(next_state)
                parent[next_state] = (state, move)
                stack.append(next_state)

    return SearchResult("no_solution", (), expanded, perf_counter() - started)


def _build_plan(start, goal, parent) -> tuple[Move, ...]:
    moves = []
    state = goal
    while state != start:
        state, move = parent[state]
        moves.append(move)
    return tuple(reversed(moves))


def _ordered_moves(state: BlockWorldState, goal: BlockWorldState) -> list[Move]:

    settled = set()
    changed = True
    while changed:
        changed = False
        for block in range(1, state.size + 1):
            support = state.support_of(block)
            if (
                block not in settled
                and support == goal.support_of(block)
                and (support == 0 or support in settled)
            ):
                settled.add(block)
                changed = True

    def priority(move: Move):
        block, target = move
        reaches_goal = target == goal.support_of(block)
        target_ready = target == 0 or target in settled
        if reaches_goal and target_ready and block not in settled:
            return 0, block, target
        if target == 0 and block not in settled:
            return 1, block, target
        if block not in settled:
            return 2, block, target
        return 3, block, target

    return sorted(state.legal_moves(), key=priority)
`,

    "state.py": String.raw`from dataclasses import dataclass


Move = tuple[int, int]


@dataclass(frozen=True)
class BlockWorldState:
    supports: tuple[int, ...]

    def __post_init__(self):
        self._validate()

    @property
    def size(self) -> int:
        return len(self.supports)

    def support_of(self, block: int) -> int:
        if not 1 <= block <= self.size:
            raise ValueError(f"Klocek {block} nie istnieje.")
        return self.supports[block - 1]

    def clear_blocks(self) -> set[int]:
        occupied = {support for support in self.supports if support != 0}
        return set(range(1, self.size + 1)) - occupied

    def legal_moves(self) -> list[Move]:
        clear = sorted(self.clear_blocks())
        moves = []
        for block in clear:
            if self.support_of(block) != 0:
                moves.append((block, 0))
            else:
                moves.extend((block, target) for target in clear if target != block)
        return moves

    def apply(self, move: Move) -> "BlockWorldState":
        block, target = move
        current_support = self.support_of(block)

        if not 0 <= target <= self.size:
            raise ValueError(f"Podłoże {target} nie istnieje.")
        if target == block:
            raise ValueError("Nie można położyć klocka na nim samym.")
        if block not in self.clear_blocks():
            raise ValueError(f"Klocek {block} nie jest wolny.")

        if target == 0:
            if current_support == 0:
                raise ValueError(f"Klocek {block} już leży na stole.")
        else:
            if current_support != 0:
                raise ValueError(
                    "W wariancie podstawowym na inny klocek przenosimy tylko ze stołu."
                )
            if target not in self.clear_blocks():
                raise ValueError(f"Klocek docelowy {target} nie jest wolny.")

        supports = list(self.supports)
        supports[block - 1] = target
        return BlockWorldState(tuple(supports))

    def to_line(self) -> str:
        return " ".join(map(str, self.supports))

    def _validate(self):
        for block, support in enumerate(self.supports, 1):
            if not 0 <= support <= self.size:
                raise ValueError(f"Klocek {block} leży na nieistniejącym podłożu.")
            if block == support:
                raise ValueError(f"Klocek {block} leży na samym sobie.")

        supports = [support for support in self.supports if support != 0]
        if len(supports) != len(set(supports)):
            raise ValueError("Dwa klocki leżą bezpośrednio na tym samym klocku.")

        for start in range(1, self.size + 1):
            visited = set()
            block = start
            while block != 0:
                if block in visited:
                    raise ValueError("Układ zawiera cykl.")
                visited.add(block)
                block = self.supports[block - 1]
`,

    "main.py": String.raw`import sys

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
`
  }
};
