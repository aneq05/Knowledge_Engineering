"""Plan zmian między dwoma stanami oraz zapis stanu do pliku (potrzebne od progu 6)."""

from dataclasses import dataclass
from pathlib import Path

from .models import EnvironmentState
from .versions import version_key


@dataclass(frozen=True)
class Change:
    kind: str  # "install", "remove", "upgrade" albo "downgrade"
    package: str
    old: str | None = None
    new: str | None = None

    def __str__(self) -> str:
        if self.kind == "install":
            return f"instalacja {self.package} {self.new}"
        if self.kind == "remove":
            return f"usunięcie {self.package} {self.old}"
        word = "podniesienie" if self.kind == "upgrade" else "obniżenie"
        return f"{word} {self.package} {self.old} -> {self.new}"


# na 6
def diff_states(old: EnvironmentState, new: EnvironmentState) -> list[Change]:
    changes: list[Change] = []
    for name in sorted(old.installed.keys() | new.installed.keys()):
        before = old.installed.get(name)
        after = new.installed.get(name)
        # nowy stan
        if before is None and after is not None:
            changes.append(Change("install", name, None, after.version))
        # stary stan
        elif before is not None and after is None:
            changes.append(Change("remove", name, before.version, None))
        elif before is not None and after is not None:
            # Wersje 1.0 i 1.0.0 to ta sama wersja, więc porównujemy klucze, a nie napisy.
            old_key, new_key = version_key(before.version), version_key(after.version)
            if old_key != new_key:
                kind = "upgrade" if new_key > old_key else "downgrade"
                changes.append(Change(kind, name, before.version, after.version))
    return changes


def save_state(state: EnvironmentState, path: str | Path) -> None:
    lines = [
        f"{item.package} {item.version}{' manual' if item.manual else ''}"
        for item in sorted(state.installed.values(), key=lambda item: item.package)
    ]
    output_path = Path(path)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Nie można zapisać stanu do pliku {output_path}: {exc}") from exc