import re

from .models import ComparisonOperator, Dependency, Requirement, VersionConstraint
from .versions import version_key

_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
_CONSTRAINT = re.compile(r"(==|!=|<=|>=|<|>)\s*([0-9]+(?:\.[0-9]+)*)")


def normalize_name(name: str) -> str:
    if not _NAME.fullmatch(name):
        raise ValueError(f"Niepoprawna nazwa pakietu: {name!r}")
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_requirement(text: str) -> Requirement:
    text = text.strip()
    match = _NAME.match(text)
    if match is None:
        raise ValueError(f"Niepoprawne wymaganie: {text!r}")
    name = normalize_name(match.group())
    constraints = _parse_constraints(text[match.end() :], text)
    return Requirement(name, constraints)


def parse_dependency(text: str) -> Dependency:
    return Dependency(tuple(parse_requirement(part) for part in text.split("|")))


def _parse_constraints(rest: str, requirement: str) -> tuple[VersionConstraint, ...]:
    constraints: list[VersionConstraint] = []
    while rest.strip(): # odczytuje kolejne operatory i wersje w pętli bo może ich być kilka
        rest = rest.lstrip()
        match = _CONSTRAINT.match(rest)
        if match is None:
            raise ValueError(f"Niepoprawne ograniczenie wersji w wymaganiu {requirement!r}")
        operator, version = match.groups()
        version_key(version)
        constraints.append(VersionConstraint(ComparisonOperator(operator), version))
        rest = _after_constraint(rest[match.end() :], requirement)
    return tuple(constraints)

# sprawdzenie poprawności separatorów między warunkami
def _after_constraint(rest: str, requirement: str) -> str:
    if not rest:
        return ""
    if not rest[0].isspace() and not rest.startswith(","):
        raise ValueError(f"Niepoprawne ograniczenie wersji w wymaganiu {requirement!r}")
    rest = rest.lstrip()
    if rest.startswith(","):
        rest = rest[1:]
        if not rest.strip():
            raise ValueError(f"Niepoprawne ograniczenie wersji w wymaganiu {requirement!r}")
    return rest
