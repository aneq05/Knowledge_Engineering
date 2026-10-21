from dataclasses import dataclass


Move = tuple[int, int]


@dataclass(frozen=True)
class BlockWorldState:
    supports: tuple[int, ...]      # podłoża poszczególnych klocków

    def __post_init__(self):    # automatycznie po inicjalizacji obiektu
        self._validate()

    @property
    def size(self) -> int:
        return len(self.supports)   # liczba klocków

    def support_of(self, block: int) -> int:    # podłoże danego klocka
        if not 1 <= block <= self.size:
            raise ValueError(f"Klocek {block} nie istnieje.")
        return self.supports[block - 1]

    def clear_blocks(self) -> set[int]: # bloczki które mają wolny wierzch
        occupied = {support for support in self.supports if support != 0}
        return set(range(1, self.size + 1)) - occupied

    def legal_moves(self) -> list[Move]:
        clear = sorted(self.clear_blocks())
        moves = []
        for block in clear:
            # jeśli wolny klocek stoi na innym klocku, to można go zdjąć na stół
            if self.support_of(block) != 0:
                moves.append((block, 0))
            else:
                # jeśli wolny klocek stoi na stole, to można go położyć na innym wolnym klocku
                moves.extend((block, target) for target in clear if target != block)
        return moves

# utworzenie aktualnego stanu po ruchu
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

# czy całe ustawienie jest możliwe?
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
