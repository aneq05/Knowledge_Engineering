import re
from typing import TypeAlias

VersionKey: TypeAlias = tuple[int, ...]
_VERSION = re.compile(r"[0-9]+(?:\.[0-9]+)*")


def version_key(version: str) -> VersionKey:
    if not _VERSION.fullmatch(version):
        raise ValueError(f"Niepoprawna wersja: {version!r}")
    parts = [int(part) for part in version.split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)
