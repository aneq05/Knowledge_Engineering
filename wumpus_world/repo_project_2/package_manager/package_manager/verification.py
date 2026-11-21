from collections import defaultdict
from collections.abc import Sequence

from .models import EnvironmentState, InstalledPackage, PackageVersion, Repository, Requirement
from .requirements_parser import normalize_name
from .versions import version_key


def _satisfies(requirement: Requirement, installed: dict[str, list[InstalledPackage]]) -> bool:
    for package in installed.get(normalize_name(requirement.package), []):
        try:
            if requirement.matches(package.version):
                return True
        except ValueError:
            # Niepoprawną wersję zgłaszamy osobno przy sprawdzaniu stanu.
            continue
    return False


def _index_installed(
    state: EnvironmentState, errors: list[str]
) -> dict[str, list[InstalledPackage]]:
    installed: dict[str, list[InstalledPackage]] = defaultdict(list)
    for item in state.installed.values():
        try:
            name = normalize_name(item.package)
        except ValueError:
            errors.append(f"Niepoprawna nazwa zainstalowanego pakietu: {item.package!r}.")
            continue
        installed[name].append(item)
    for name, versions in installed.items():
        if len(versions) > 1:
            errors.append(f"Pakiet {name} jest zainstalowany więcej niż raz.")
    return dict(installed)


def _find_version(repository: Repository, item: InstalledPackage) -> PackageVersion | None:
    name = normalize_name(item.package)
    wanted_version = version_key(item.version)
    versions = repository.packages.get(name, {})
    for version, details in versions.items():
        if version_key(version) == wanted_version:
            return details
    return None


def _check_dependencies(
    details: PackageVersion, installed: dict[str, list[InstalledPackage]], errors: list[str]
) -> None:
    for dependency in details.requires:
        if not any(_satisfies(item, installed) for item in dependency.alternatives):
            errors.append(f"{details.package}=={details.version} wymaga {dependency}.")


def _check_conflicts(
    details: PackageVersion, installed: dict[str, list[InstalledPackage]], errors: list[str]
) -> None:
    for requirement in details.conflicts:
        for item in installed.get(normalize_name(requirement.package), []):
            try:
                matches = requirement.matches(item.version)
            except ValueError:
                continue
            if matches:
                errors.append(
                    f"{details.package}=={details.version} konfliktuje z "
                    f"{item.package}=={item.version} ({requirement})."
                )


def verify_state(
    repository: Repository, state: EnvironmentState, requests: Sequence[Requirement] = ()
) -> list[str]:
    errors: list[str] = []
    installed = _index_installed(state, errors)
    for items in installed.values():
        for item in items:
            try:
                details = _find_version(repository, item)
            except ValueError:
                details = None
            if details is None:
                errors.append(f"Brak {item.package}=={item.version} w repozytorium.")
                continue
            _check_dependencies(details, installed, errors)
            _check_conflicts(details, installed, errors)

    for request in requests:
        if not _satisfies(request, installed):
            errors.append(f"Niespełnione żądanie: {request}.")
    return errors
