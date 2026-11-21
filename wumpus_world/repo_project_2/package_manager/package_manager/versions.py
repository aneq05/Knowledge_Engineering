import re
from functools import lru_cache
from typing import TypeAlias


VersionKey: TypeAlias = tuple[int, ...]
_VERSION = re.compile(r"[0-9]+(?:\.[0-9]+)*")

@lru_cache(maxsize=None)  # version_key jest wołany tysiące razy, więc wynik pamiętamy
def version_key(version: str) -> VersionKey:
    if not _VERSION.fullmatch(version):
        raise ValueError(f"Niepoprawna wersja: {version!r}")
    parts = [int(part) for part in version.split(".")]
    # Końcowe zera nie mają znaczenia: 1.0 i 1.0.0 to ta sama wersja.
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)