import warnings
from dataclasses import dataclass, field

import z3

from .models import Dependency, Repository, Requirement
from .requirements_parser import normalize_name


@dataclass(frozen=True)
class Axiom:
    name: str
    label: str
    formula: z3.BoolRef


@dataclass
class KnowledgeBase:
    variables: dict[tuple[str, str], z3.BoolRef] = field(default_factory=dict)
    axioms: list[Axiom] = field(default_factory=list)

    def add_axiom(self, label: str, formula: z3.BoolRef) -> None:
        self.axioms.append(Axiom(f"axiom_{len(self.axioms)}", label, formula))

    def add_to_solver(self, solver: z3.Solver, *, tracked: bool = False) -> None:
        for axiom in self.axioms:
            if tracked:
                solver.assert_and_track(axiom.formula, z3.Bool(axiom.name))
            else:
                solver.add(axiom.formula)


def build_knowledge_base(repository: Repository) -> KnowledgeBase:
    builder = _KnowledgeBaseBuilder(repository)
    builder.create_variables()
    builder.add_axioms()
    return builder.kb


class _KnowledgeBaseBuilder:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository
        self.kb = KnowledgeBase()

    def create_variables(self) -> None:
        for package, versions in self.repository.packages.items():
            for version in versions:
                self.kb.variables[package, version] = z3.Bool(f"{package}=={version}")

    def matching_versions(self, requirement: Requirement) -> list[z3.BoolRef]:
        package = normalize_name(requirement.package)
        versions = self.repository.packages.get(package, {})
        matches = [
            self.kb.variables[package, version]
            for version in versions
            if requirement.matches(version)
        ]
        if not matches:
            warnings.warn(f"Brak wersji pasującej do wymagania {str(requirement)!r}.", stacklevel=2)
        return matches

    def add_axioms(self) -> None:
        for package, versions in self.repository.packages.items():
            self.add_single_version_axiom(package)
            for version, details in versions.items():
                self.add_dependencies(package, version, details.requires)
                self.add_conflicts(package, version, details.conflicts)

    def add_single_version_axiom(self, package: str) -> None:
        variables = [
            self.kb.variables[package, version] for version in self.repository.packages[package]
        ]
        if len(variables) > 1:
            self.kb.add_axiom(f"{package}: co najwyżej jedna wersja", z3.AtMost(*variables, 1))

    def add_dependencies(
        self, package: str, version: str, dependencies: tuple[Dependency, ...]
    ) -> None:
        selected = self.kb.variables[package, version]
        for dependency in dependencies:
            options: list[z3.BoolRef] = []
            for alternative in dependency.alternatives:
                options.extend(self.matching_versions(alternative))
            # Or([]) jest fałszem: brak pasującej wersji wyklucza instalację.
            self.kb.add_axiom(
                f"{package}=={version} wymaga {dependency}",
                z3.Implies(selected, z3.Or(options)),
            )

    def add_conflicts(self, package: str, version: str, conflicts: tuple[Requirement, ...]) -> None:
        selected = self.kb.variables[package, version]
        for conflict in conflicts:
            for other in self.matching_versions(conflict):
                self.kb.add_axiom(
                    f"{package}=={version} konfliktuje z {other}",
                    z3.Implies(selected, z3.Not(other)),
                )
