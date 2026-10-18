from dataclasses import dataclass
from time import perf_counter

from .blocks_world import BlockWorldState, Move


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
    if start.size != goal.size:
        raise ValueError("Stany muszą mieć ten sam rozmiar.")
    if node_limit < 1 or time_limit_seconds <= 0:
        raise ValueError("Limity muszą być dodatnie.")

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
