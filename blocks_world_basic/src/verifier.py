from collections.abc import Iterable

from .state import BlockWorldState, Move


def verify_plan(
    start: BlockWorldState,
    goal: BlockWorldState,
    moves: Iterable[Move],
) -> tuple[bool, str]:
    state = start

    for number, move in enumerate(moves, 1):
        try:
            state = state.apply(move)
        except ValueError as error:
            return False, f"Ruch {number} {move}: {error}"

    if state != goal:
        return False, "Stan końcowy nie jest stanem docelowym."

    return True, "Plan jest poprawny."
