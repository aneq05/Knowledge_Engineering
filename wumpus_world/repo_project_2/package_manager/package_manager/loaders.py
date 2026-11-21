from pathlib import Path

from .json_reader import read_json
from .models import (
    Dependency,
    EnvironmentState,
    InstalledPackage,
    PackageVersion,
    Repository,
    Requirement,
)
from .requirements_parser import normalize_name, parse_dependency, parse_requirement
from .versions import version_key


def _require_object(value: object, location: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{location}: oczekiwano obiektu JSON.")
    return value


def _check_fields(
    data: dict[str, object], location: str, allowed: set[str], required: set[str]
) -> None:
    for name in sorted(data.keys() - allowed):
        raise ValueError(f"{location}.{name}: nieznane pole.")
    for name in sorted(required - data.keys()):
        raise ValueError(f"{location}.{name}: brak wymaganego pola.")


def _string_list(value: object, location: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{location}: oczekiwano listy napisów.")
    result: list[str] = []
    for index, text in enumerate(value):
        if not isinstance(text, str):
            raise ValueError(f"{location}[{index}]: oczekiwano napisu.")
        result.append(text)
    return result


def _load_dependencies(value: object, package: str, location: str) -> tuple[Dependency, ...]:
    dependencies: list[Dependency] = []
    for index, text in enumerate(_string_list(value, location)):
        try:
            dependency = parse_dependency(text)
        except ValueError as exc:
            raise ValueError(f"{location}[{index}]: {exc}") from exc
        if any(item.package == package for item in dependency.alternatives):
            raise ValueError(f"{location}[{index}]: pakiet nie może wymagać samego siebie.")
        dependencies.append(dependency)
    return tuple(dependencies)


def _load_conflicts(value: object, package: str, location: str) -> tuple[Requirement, ...]:
    conflicts: list[Requirement] = []
    for index, text in enumerate(_string_list(value, location)):
        try:
            conflict = parse_requirement(text)
        except ValueError as exc:
            raise ValueError(f"{location}[{index}]: {exc}") from exc
        if conflict.package == package:
            raise ValueError(f"{location}[{index}]: pakiet nie może konfliktować z samym sobą.")
        conflicts.append(conflict)
    return tuple(conflicts)


def _load_version(package: str, version: str, value: object, location: str) -> PackageVersion:
    data = _require_object(value, location)
    _check_fields(data, location, allowed={"requires", "conflicts"}, required=set())
    requires = _load_dependencies(data.get("requires", []), package, f"{location}.requires")
    conflicts = _load_conflicts(data.get("conflicts", []), package, f"{location}.conflicts")
    return PackageVersion(package, version, requires, conflicts)


def _load_versions(package: str, value: object, location: str) -> dict[str, PackageVersion]:
    data = _require_object(value, location)
    if not data:
        raise ValueError(f"{location}: pakiet musi mieć co najmniej jedną wersję.")
    versions: dict[str, PackageVersion] = {}
    seen: dict[tuple[int, ...], str] = {}
    for version, details in data.items():
        item_location = f"{location}[{version!r}]"
        try:
            key = version_key(version)
        except ValueError as exc:
            raise ValueError(f"{item_location}: {exc}") from exc
        if key in seen:
            raise ValueError(f"{item_location}: wersja powtarza {seen[key]!r}.")
        seen[key] = version
        versions[version] = _load_version(package, version, details, item_location)
    return versions


def _load_packages(value: object) -> dict[str, dict[str, PackageVersion]]:
    data = _require_object(value, "packages")
    packages: dict[str, dict[str, PackageVersion]] = {}
    for original_name, details in data.items():
        location = f"packages[{original_name!r}]"
        try:
            name = normalize_name(original_name)
        except ValueError as exc:
            raise ValueError(f"{location}: {exc}") from exc
        if name in packages:
            raise ValueError(f"{location}: powtórzony pakiet po normalizacji nazwy: {name!r}.")
        package_data = _require_object(details, location)
        _check_fields(package_data, location, allowed={"versions"}, required={"versions"})
        packages[name] = _load_versions(name, package_data["versions"], f"{location}.versions")
    return packages


def load_repository(path: str | Path) -> Repository:
    raw = read_json(path)
    try:
        data = _require_object(raw, "$")
        _check_fields(data, "$", allowed={"packages", "meta"}, required={"packages"})
        return Repository(packages=_load_packages(data["packages"]), meta=data.get("meta", {}))
    except ValueError as exc:
        raise ValueError(f"{path}: {exc}") from exc


def _read_lines(path: str | Path) -> list[tuple[int, str]]:
    try:
        lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"Nie można odczytać {path}: {exc}") from exc
    result: list[tuple[int, str]] = []
    for number, original in enumerate(lines, start=1):
        content = original.split("#", 1)[0].strip()
        if content:
            result.append((number, content))
    return result


def load_requests(path: str | Path) -> list[Requirement]:
    requests: list[Requirement] = []
    for line_number, line in _read_lines(path):
        try:
            requests.append(parse_requirement(line))
        except ValueError as exc:
            raise ValueError(f"{path}:{line_number}: {exc}") from exc
    return requests

# na 6
def _parse_installed(line: str) -> InstalledPackage:
    parts = line.split()
    if len(parts) not in (2, 3) or (len(parts) == 3 and parts[2] != "manual"):
        raise ValueError("Oczekiwano 'NAZWA WERSJA [manual]'.")
    name, version = parts[:2]
    name = normalize_name(name)
    version_key(version)
    return InstalledPackage(name, version, manual=len(parts) == 3)

# na 6
def load_state(path: str | Path) -> EnvironmentState:
    installed: dict[str, InstalledPackage] = {}
    for line_number, line in _read_lines(path):
        try:
            item = _parse_installed(line)
            if item.package in installed:
                raise ValueError(f"Powtórzony pakiet {item.package!r}.")
        except ValueError as exc:
            raise ValueError(f"{path}:{line_number}: {exc}") from exc
        installed[item.package] = item
    return EnvironmentState(installed)

def load_names(path: str | Path) -> list[str]:
    names = []
    for line_number, line in _read_lines(path):
        try:
            names.append(normalize_name(line))
        except ValueError as exc:
            raise ValueError(f"{path}:{line_number}: {exc}") from exc
    return names