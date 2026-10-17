"""Stan, ruchy, wejście i weryfikacja podstawowego Blocks World."""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

Move = tuple[int, int]


class InvalidStateError(ValueError):
    pass


class IllegalMoveError(ValueError):
    pass


class InputFormatError(ValueError):
    pass


@dataclass(frozen=True)
class BlockWorldState:
    """support[i-1] mówi, na czym leży klocek i; 0 oznacza stół."""

    supports: tuple[int, ...]

    def __post_init__(self):
        object.__setattr__(self, "supports", tuple(self.supports))
        self._validate()

    @property
    def size(self) -> int:
        return len(self.supports)

    def support_of(self, block: int) -> int:
        if not 1 <= block <= self.size:
            raise IllegalMoveError(f"Klocek {block} nie istnieje.")
        return self.supports[block - 1]

    def clear_blocks(self) -> set[int]:
        occupied = {x for x in self.supports if x != 0}
        return set(range(1, self.size + 1)) - occupied

    def legal_moves(self) -> list[Move]:
        """Ruchy 1-2 z wariantu podstawowego."""

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
        current = self.support_of(block)

        if not 0 <= target <= self.size:
            raise IllegalMoveError(f"Podłoże {target} nie istnieje.")
        if target == block:
            raise IllegalMoveError("Nie można położyć klocka na nim samym.")
        if block not in self.clear_blocks():
            raise IllegalMoveError(f"Klocek {block} nie jest wolny.")

        if target == 0:
            if current == 0:
                raise IllegalMoveError(f"Klocek {block} już leży na stole.")
        else:
            if current != 0:
                raise IllegalMoveError(
                    "W wariancie podstawowym na inny klocek przenosimy tylko ze stołu."
                )
            if target not in self.clear_blocks():
                raise IllegalMoveError(f"Klocek docelowy {target} nie jest wolny.")

        supports = list(self.supports)
        supports[block - 1] = target
        return BlockWorldState(tuple(supports))

    def to_line(self) -> str:
        return " ".join(map(str, self.supports))

    def _validate(self):
        if not self.supports:
            raise InvalidStateError("Układ jest pusty.")

        for block, support in enumerate(self.supports, 1):
            if not isinstance(support, int) or isinstance(support, bool):
                raise InvalidStateError(f"Podłoże klocka {block} nie jest liczbą.")
            if not 0 <= support <= self.size:
                raise InvalidStateError(f"Klocek {block} leży na nieistniejącym podłożu.")
            if block == support:
                raise InvalidStateError(f"Klocek {block} leży na samym sobie.")

        nonzero = [x for x in self.supports if x != 0]
        if len(nonzero) != len(set(nonzero)):
            raise InvalidStateError("Dwa klocki leżą bezpośrednio na tym samym klocku.")

        for start in range(1, self.size + 1):
            seen = set()
            block = start
            while block != 0:
                if block in seen:
                    raise InvalidStateError("Układ zawiera cykl.")
                seen.add(block)
                block = self.supports[block - 1]


def read_problem(path: str | Path) -> tuple[BlockWorldState, BlockWorldState]:
    lines = [
        line.strip()
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(lines) != 2:
        raise InputFormatError("Plik musi zawierać dwie linie danych: start i cel.")

    try:
        start = BlockWorldState(tuple(map(int, lines[0].split())))
        goal = BlockWorldState(tuple(map(int, lines[1].split())))
    except (ValueError, InvalidStateError) as error:
        raise InputFormatError(f"Niepoprawny układ: {error}") from error

    if start.size != goal.size:
        raise InputFormatError("Stan początkowy i docelowy muszą mieć tyle samo klocków.")
    return start, goal


@dataclass(frozen=True)
class VerificationResult:
    valid: bool
    message: str
    failed_move_index: int | None = None


def verify_plan(
    start: BlockWorldState,
    goal: BlockWorldState,
    moves: Iterable[Move],
) -> VerificationResult:
    state = start
    for number, move in enumerate(moves, 1):
        try:
            state = state.apply(move)
        except (IllegalMoveError, TypeError, ValueError) as error:
            return VerificationResult(False, f"Ruch {number} {move}: {error}", number)

    if state != goal:
        return VerificationResult(False, "Stan końcowy nie jest stanem docelowym.")
    return VerificationResult(True, "Plan jest poprawny.")
