import json
from dataclasses import dataclass
from pathlib import Path

from .models import JsonValue


@dataclass
class _ObjectPairs:
    pairs: list[tuple[str, object]]


@dataclass
class _InvalidConstant:
    value: str


def _key_path(location: str, key: str) -> str:
    if location == "$":
        return key if key.isidentifier() else f"[{key!r}]"
    if location == "packages" or location.endswith(".versions"):
        return f"{location}[{key!r}]"
    return f"{location}.{key}" if key.isidentifier() else f"{location}[{key!r}]"


def _convert_object(value: _ObjectPairs, location: str) -> dict[str, JsonValue]:
    result: dict[str, JsonValue] = {}
    for key, item in value.pairs:
        child_path = _key_path(location, key)
        if key in result:
            raise ValueError(f"{child_path}: powtórzony klucz {key!r}.")
        result[key] = _convert_value(item, child_path)
    return result


def _convert_value(value: object, location: str) -> JsonValue:
    if isinstance(value, _ObjectPairs):
        return _convert_object(value, location)
    if isinstance(value, list):
        return [_convert_value(item, f"{location}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, _InvalidConstant):
        raise ValueError(f"{location}: niedozwolona stała JSON {value.value}.")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ValueError(f"{location}: nieobsługiwana wartość JSON.")


def read_json(path: str | Path) -> JsonValue:
    try:
        text = Path(path).read_text(encoding="utf-8")
        raw: object = json.loads(
            text, object_pairs_hook=_ObjectPairs, parse_constant=_InvalidConstant
        )
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}:{exc.lineno}:{exc.colno}: {exc.msg}") from exc
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"Nie można odczytać {path}: {exc}") from exc
    try:
        return _convert_value(raw, "$")
    except ValueError as exc:
        raise ValueError(f"{path}: {exc}") from exc
