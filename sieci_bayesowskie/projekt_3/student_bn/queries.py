from __future__ import annotations

import ast
import re
import numpy as np

from dataclasses import dataclass
from itertools import product
from pathlib import Path
from pgmpy.inference import VariableElimination

from .data import Description
from .joint import StateSpace


_QUERY = re.compile(r"\s*(P|MAP)\s*\((.*)\)\s*\Z", re.DOTALL)


@dataclass(frozen=True)
class Query:
    kind: str
    targets: tuple[str, ...]
    condition: ast.expr | None
    evidence: dict[str, str] | None
    text: str
    line: int


@dataclass(frozen=True)
class QueryResult:
    query: Query
    values: tuple[tuple[tuple[str, ...], float], ...]
    event_probability: float
    maximum: tuple[str, ...] | None = None


def _check_comparison(
    name: str,
    operation: ast.cmpop,
    right: ast.expr,
    states: dict[str, tuple[str, ...]],
    location: str,
) -> set[str]:
    if name not in states:
        raise ValueError(f"{location}: unknown variable {name!r}")
    if isinstance(operation, (ast.Eq, ast.NotEq)) and isinstance(right, ast.Name):
        labels = [right.id]
    elif (
        isinstance(operation, ast.In)
        and isinstance(right, ast.Set)
        and right.elts
        and all(isinstance(item, ast.Name) for item in right.elts)
    ):
        labels = [item.id for item in right.elts]
    else:
        raise ValueError(f"{location}: allowed: X==s, X!=s, X in {{a, b}}")
    for state in labels:
        if state not in states[name]:
            raise ValueError(f"{location}: {name}: unknown state {state!r}")
    return {name}


def _check_condition(node: ast.expr, states: dict[str, tuple[str, ...]], location: str) -> set[str]:
    if isinstance(node, ast.Tuple):
        return set().union(*(_check_condition(item, states, location) for item in node.elts))
    if isinstance(node, ast.BoolOp):
        if not isinstance(node.op, (ast.And, ast.Or)):
            raise ValueError(f"{location}: only 'and' and 'or' are supported")
        return set().union(*(_check_condition(item, states, location) for item in node.values))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return _check_condition(node.operand, states, location)
    if (
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Name)
        and len(node.ops) == len(node.comparators) == 1
    ):
        return _check_comparison(node.left.id, node.ops[0], node.comparators[0], states, location)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"atleast", "atmost"}:
        if node.keywords or len(node.args) < 2 or not isinstance(node.args[0], ast.Constant):
            raise ValueError(f"{location}: {node.func.id} requires an integer and at least one condition")
        number = node.args[0].value
        if type(number) is not int or number < 0:
            raise ValueError(f"{location}: count must be a nonnegative integer")
        return set().union(*(_check_condition(x, states, location) for x in node.args[1:]))
    raise ValueError(f"{location}: unsupported condition syntax: {ast.dump(node, include_attributes=False)}")


def _simple_evidence(node: ast.expr | None) -> dict[str, str] | None:
    if node is None:
        return {}
    if isinstance(node, ast.Compare):
        if isinstance(node.ops[0], ast.Eq):
            return {node.left.id: node.comparators[0].id}
        return None
    if isinstance(node, ast.Tuple):
        parts = node.elts
    elif isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
        parts = node.values
    else:
        return None
    combined = {}
    for part in parts:
        evidence = _simple_evidence(part)
        if evidence is None or any(k in combined and combined[k] != v for k, v in evidence.items()):
            return None
        combined.update(evidence)
    return combined


def parse_query(text: str, line: int, description: Description, *, advanced: bool = False) -> Query:
    location = f"line {line}"
    match = _QUERY.fullmatch(text)
    if not match:
        raise ValueError(f"{location}: expected P(...) or MAP(...): {text!r}")
    kind, body = match.groups()
    raw_targets, separator, raw_condition = body.partition("|")
    targets = tuple(item.strip() for item in raw_targets.split(","))
    if not targets or any(not item for item in targets) or len(set(targets)) != len(targets):
        raise ValueError(f"{location}: duplicate or missing query target")
    for target in targets:
        if target not in description.variables:
            raise ValueError(f"{location}: unknown query variable {target!r}")
    condition = None
    if separator:
        if not raw_condition.strip():
            raise ValueError(f"{location}: empty evidence after '|'")
        try:
            condition = ast.parse(raw_condition.strip(), mode="eval").body
        except SyntaxError as exc:
            raise ValueError(f"{location}: invalid condition at column {exc.offset}: {exc.msg}") from exc
        used = _check_condition(condition, description.states, location)
        overlap = used & set(targets)
        if overlap:
            raise ValueError(f"{location}: query variable also occurs in evidence: {sorted(overlap)}")
        evidence = _simple_evidence(condition)
        if not advanced and evidence is None:
            raise ValueError(f"{location}: only comma-separated equalities are allowed in zapytania.txt")
    else:
        evidence = {}
    return Query(kind, targets, condition, evidence, text, line)


def load_queries(path: Path, description: Description, *, advanced: bool = False) -> list[Query]:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise ValueError(f"{path}: {exc}") from exc
    results = []
    for number, raw in enumerate(lines, 1):
        text = raw.split("#", 1)[0].strip()
        if text:
            try:
                results.append(parse_query(text, number, description, advanced=advanced))
            except ValueError as exc:
                raise ValueError(f"{path}:{exc}") from exc
    return results


def condition_mask(node: ast.expr | None, space: StateSpace, assignments: np.ndarray) -> np.ndarray:
    if node is None:
        return np.ones(len(assignments), dtype=bool)
    if isinstance(node, ast.Tuple):
        return np.logical_and.reduce([condition_mask(x, space, assignments) for x in node.elts])
    if isinstance(node, ast.BoolOp):
        masks = [condition_mask(x, space, assignments) for x in node.values]
        reduction = np.logical_and if isinstance(node.op, ast.And) else np.logical_or
        return reduction.reduce(masks)
    if isinstance(node, ast.UnaryOp):
        return ~condition_mask(node.operand, space, assignments)
    if isinstance(node, ast.Compare):
        variable = node.left.id
        values = assignments[:, space.positions[variable]]
        operation = node.ops[0]
        if isinstance(operation, ast.In):
            states = [state.id for state in node.comparators[0].elts]
            return np.isin(values, [space.states[variable].index(s) for s in states])
        state = space.states[variable].index(node.comparators[0].id)
        return values == state if isinstance(operation, ast.Eq) else values != state
    if isinstance(node, ast.Call):
        count = node.args[0].value
        matched = np.sum([condition_mask(arg, space, assignments) for arg in node.args[1:]], axis=0)
        return matched >= count if node.func.id == "atleast" else matched <= count
    raise AssertionError("AST must be validated before execution")


def solve_query(query: Query, model, space: StateSpace, joint: np.ndarray, inference=None) -> QueryResult:
    mask = condition_mask(query.condition, space, space.assignments)
    event_probability = float(joint[mask].sum())
    if event_probability <= 0:
        raise ValueError(f"{query.text}: evidence has P=0")
    states = [space.states[v] for v in query.targets]
    configurations = tuple(product(*states))

    if query.evidence is not None:
        # Standard point evidence uses pgmpy's VariableElimination, as requested.
        if inference is None:
            inference = VariableElimination(model)
        distribution = inference.query(list(query.targets), evidence=query.evidence, show_progress=False)
        probabilities = np.array([distribution.get_value(**dict(zip(query.targets, cfg))) for cfg in configurations])
        if query.kind == "MAP":
            maximum_map = inference.map_query(list(query.targets), evidence=query.evidence, show_progress=False)
            maximum = tuple(maximum_map[v] for v in query.targets)
        else:
            maximum = None
    else:
        # General logical events are not representable as plain VE evidence.
        probabilities = space.marginal(joint * mask, query.targets).ravel() / event_probability
        maximum = configurations[int(np.argmax(probabilities))] if query.kind == "MAP" else None

    values = tuple((config, float(prob)) for config, prob in zip(configurations, probabilities))
    return QueryResult(query, values, event_probability, maximum)
