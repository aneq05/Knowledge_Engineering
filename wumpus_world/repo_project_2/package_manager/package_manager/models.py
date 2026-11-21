import operator

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

from .versions import version_key

class ComparisonOperator(StrEnum):
    EQ = "=="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="


_COMPARISONS: dict[
    ComparisonOperator, Callable[[tuple[int, ...], tuple[int, ...]], bool]
] = {
    ComparisonOperator.EQ: operator.eq,
    ComparisonOperator.NE: operator.ne,
    ComparisonOperator.LT: operator.lt,
    ComparisonOperator.LE: operator.le,
    ComparisonOperator.GT: operator.gt,
    ComparisonOperator.GE: operator.ge,
}


@dataclass(frozen=True)
class VersionConstraint:
    operator: ComparisonOperator
    version: str

    def matches(self, version: str) -> bool:
        compare = _COMPARISONS[self.operator]
        return compare(version_key(version), version_key(self.version))

    def __str__(self) -> str:
        return f"{self.operator.value}{self.version}"


@dataclass(frozen=True)
class Requirement:
    package: str
    constraints: tuple[VersionConstraint, ...] = ()

    def matches(self, version: str) -> bool:
        version_key(version)  # Także wymaganie bez ograniczeń odrzuca złą wersję.
        return all(constraint.matches(version) for constraint in self.constraints)

    def __str__(self) -> str:
        return " ".join([self.package, *(str(item) for item in self.constraints)])


@dataclass(frozen=True)
class Dependency:
    alternatives: tuple[Requirement, ...]

    def __str__(self) -> str:
        return " | ".join(str(item) for item in self.alternatives)


@dataclass(frozen=True)
class PackageVersion:
    package: str
    version: str
    requires: tuple[Dependency, ...] = ()
    conflicts: tuple[Requirement, ...] = ()


@dataclass
class Repository:
    packages: dict[str, dict[str, PackageVersion]] = field(default_factory=dict)
    meta: object = field(default_factory=dict)


@dataclass(frozen=True)
class InstalledPackage:
    package: str
    version: str
    manual: bool = False


@dataclass
class EnvironmentState:
    installed: dict[str, InstalledPackage] = field(default_factory=dict)
