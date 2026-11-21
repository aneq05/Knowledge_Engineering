import z3

from collections.abc import Sequence
from dataclasses import dataclass

from .knowledge_base import KnowledgeBase, build_knowledge_base
from .models import EnvironmentState, InstalledPackage, Repository, Requirement
from .requirements_parser import normalize_name
from .verification import verify_state
from .versions import version_key


@dataclass(frozen=True)
class InstallationResult:
    state: EnvironmentState
    requested_staleness: int
    package_count: int
    dependency_staleness: int


def _sum_costs(terms: list[z3.ArithRef]) -> z3.ArithRef:
    return z3.Sum(terms) if terms else z3.IntVal(0)


def _request_formula(requirement: Requirement, kb: KnowledgeBase) -> z3.BoolRef:
    name = normalize_name(requirement.package)
    matches = [
        variable
        for (package, version), variable in kb.variables.items()
        if normalize_name(package) == name and requirement.matches(version)
    ]
    return z3.Or(matches)


def _costs(
    repository: Repository, kb: KnowledgeBase, requested_names: set[str]
) -> tuple[z3.ArithRef, z3.ArithRef, z3.ArithRef]:
    requested_costs: list[z3.ArithRef] = []
    other_costs: list[z3.ArithRef] = []
    package_costs: list[z3.ArithRef] = []

    for package, versions in repository.packages.items():
        ordered_versions = sorted(versions, key=version_key, reverse=True)
        costs = requested_costs if normalize_name(package) in requested_names else other_costs

        for rank, version in enumerate(ordered_versions):
            selected = kb.variables[package, version]
            costs.append(z3.If(selected, rank, 0))
            package_costs.append(z3.If(selected, 1, 0))

    return _sum_costs(requested_costs), _sum_costs(package_costs), _sum_costs(other_costs)


def _read_state(
    model: z3.ModelRef, kb: KnowledgeBase, requested_names: set[str]
) -> EnvironmentState:
    installed: dict[str, InstalledPackage] = {}

    for (package, version), variable in kb.variables.items():
        if z3.is_true(model.eval(variable, model_completion=True)):
            installed[package] = InstalledPackage(
                package, version, manual=normalize_name(package) in requested_names
            )

    return EnvironmentState(installed)


def install(repository: Repository, requests: Sequence[Requirement]) -> InstallationResult | None:
    return solve(repository, build_knowledge_base(repository), requests)


def solve(
    repository: Repository,
    kb: KnowledgeBase,
    requests: Sequence[Requirement],
    timeout_ms: int | None = None,
) -> InstallationResult | None:
    requested_names = {normalize_name(request.package) for request in requests}
    optimizer = z3.Optimize()
    optimizer.set(priority="lex")

    if timeout_ms is not None:
        optimizer.set("timeout", timeout_ms)
    for axiom in kb.axioms:
        optimizer.add(axiom.formula)
    for request in requests:
        optimizer.add(_request_formula(request, kb))

    costs = _costs(repository, kb, requested_names)
    for cost in costs:
        optimizer.minimize(cost)

    status = optimizer.check()
    if status == z3.unsat:
        return None
    if status != z3.sat:
        raise RuntimeError(f"Solver nie rozstrzygnął problemu: {optimizer.reason_unknown()}")

    model = optimizer.model()
    state = _read_state(model, kb, requested_names)
    errors = verify_state(repository, state, requests)
    if errors:
        raise RuntimeError("Solver zwrócił niepoprawny stan:\n" + "\n".join(errors))
    values = [model.eval(cost, model_completion=True).as_long() for cost in costs]

    return InstallationResult(state, values[0], values[1], values[2])
