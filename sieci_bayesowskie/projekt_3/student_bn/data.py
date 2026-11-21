from __future__ import annotations

import csv
import json
import keyword
import re
import networkx as nx
import numpy as np
import pandas as pd

from dataclasses import dataclass
from pathlib import Path


_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]*\Z")
_RESERVED = {"P", "MAP", "atleast", "atmost"}
_FIELDS = {"meta", "variables", "expert_edges", "required_edges", "forbidden_edges", "tiers"}


@dataclass(frozen=True)
class Variable:
    description: str
    states: tuple[str, ...]


@dataclass(frozen=True)
class Description:
    variables: dict[str, Variable]
    expert_edges: tuple[tuple[str, str], ...]
    required_edges: tuple[tuple[str, str], ...]
    forbidden_edges: tuple[tuple[str, str], ...]
    tiers: tuple[tuple[str, ...], ...]
    name: str = "dataset"

    @property
    def states(self) -> dict[str, tuple[str, ...]]:
        return {name: variable.states for name, variable in self.variables.items()}


def _check_name(name: object, where: str) -> str:
    if not isinstance(name, str) or not _NAME.fullmatch(name) or keyword.iskeyword(name) or name in _RESERVED:
        raise ValueError(f"{where}: invalid or reserved identifier {name!r}")
    return name


def _edges(value: object, where: str, nodes: set[str]) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, list):
        raise ValueError(f"{where}: expected a list")
    result = []
    for i, edge in enumerate(value):
        location = f"{where}[{i}]"
        if not isinstance(edge, list) or len(edge) != 2:
            raise ValueError(f"{location}: expected [source, target]")
        a, b = edge
        if not isinstance(a, str) or not isinstance(b, str) or a not in nodes or b not in nodes:
            raise ValueError(f"{location}: unknown variable in {edge!r}")
        if a == b or (a, b) in result:
            raise ValueError(f"{location}: self-loop or duplicate edge {edge!r}")
        result.append((a, b))
    return tuple(result)


def _read_description_document(path: Path) -> dict[str, object]:
    try:
        document = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}:{exc.lineno}:{exc.colno}: invalid JSON: {exc.msg}") from exc
    except OSError as exc:
        raise ValueError(f"{path}: {exc}") from exc

    if not isinstance(document, dict):
        raise ValueError(f"{path}: root must be a JSON object")
    for field in document:
        if field not in _FIELDS:
            raise ValueError(f"{path}: $.{field}: unknown field")
    for field in _FIELDS - {"meta"}:
        if field not in document:
            raise ValueError(f"{path}: $.{field}: missing field")
    return document


def _parse_variables(raw: object, path: Path) -> dict[str, Variable]:
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"{path}: $.variables: expected nonempty object")
    variables = {}
    for name, definition in raw.items():
        loc = f"$.variables.{name}"
        _check_name(name, loc)
        if not isinstance(definition, dict) or set(definition) != {"description", "states"}:
            raise ValueError(f"{path}: {loc}: expected exactly 'description' and 'states'")
        if not isinstance(definition["description"], str):
            raise ValueError(f"{path}: {loc}.description: expected a string")
        states = definition["states"]
        if not isinstance(states, list) or len(states) < 2:
            raise ValueError(f"{path}: {loc}.states: at least two states required")
        for i, state in enumerate(states):
            _check_name(state, f"{path}: {loc}.states[{i}]")
            if state in states[:i]:
                raise ValueError(f"{path}: {loc}.states[{i}]: duplicate state {state!r}")
        variables[name] = Variable(definition["description"], tuple(states))
    return variables


def _parse_tiers(
    tiers: object,
    path: Path,
    nodes: set[str],
    directed_edges: dict[str, tuple[tuple[str, str], ...]],
) -> tuple[tuple[str, ...], ...]:
    if not isinstance(tiers, list) or not tiers or any(not isinstance(t, list) or not t for t in tiers):
        raise ValueError(f"{path}: $.tiers: expected a nonempty list of nonempty lists")
    seen = set()
    level = {}
    for i, tier in enumerate(tiers):
        for j, name in enumerate(tier):
            if not isinstance(name, str) or name not in nodes or name in seen:
                raise ValueError(f"{path}: $.tiers[{i}][{j}]: unknown or duplicate variable {name!r}")
            seen.add(name)
            level[name] = i
    if seen != nodes:
        raise ValueError(f"{path}: $.tiers: missing variables {sorted(nodes - seen)}")
    for field, edges in directed_edges.items():
        for a, b in edges:
            if level[a] > level[b]:
                raise ValueError(f"{path}: $.{field}: edge {a}->{b} contradicts tiers")
    return tuple(map(tuple, tiers))


def load_description(path: Path) -> Description:
    document = _read_description_document(path)
    variables = _parse_variables(document["variables"], path)
    nodes = set(variables)

    expert = _edges(document["expert_edges"], f"{path}: $.expert_edges", nodes)
    required = _edges(document["required_edges"], f"{path}: $.required_edges", nodes)
    forbidden = _edges(document["forbidden_edges"], f"{path}: $.forbidden_edges", nodes)
    if set(required) & set(forbidden):
        raise ValueError(f"{path}: $.required_edges conflicts with $.forbidden_edges")
    directed_edges = {"expert_edges": expert, "required_edges": required}
    for field, edges in directed_edges.items():
        graph = nx.DiGraph()
        graph.add_nodes_from(nodes)
        graph.add_edges_from(edges)
        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError(f"{path}: $.{field}: directed cycle detected")

    tiers = _parse_tiers(document["tiers"], path, nodes, directed_edges)
    name = document.get("meta", {})
    title = name.get("description", "dataset") if isinstance(name, dict) else "dataset"
    return Description(variables, expert, required, forbidden, tiers, str(title))


def load_csv(path: Path, description: Description, *, complete: bool = False) -> pd.DataFrame:
    try:
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file, strict=True)
            header = next(reader, None)
            if header is None:
                raise ValueError(f"{path}:1: missing header")
            expected = set(description.variables)
            if len(header) != len(set(header)):
                raise ValueError(f"{path}:1: duplicate CSV column")
            if set(header) != expected:
                raise ValueError(
                    f"{path}:1: unknown columns {sorted(set(header)-expected)}, "
                    f"missing columns {sorted(expected-set(header))}"
                )
            rows = []
            for record in reader:
                line = reader.line_num
                if len(record) != len(header):
                    raise ValueError(f"{path}:{line}: expected {len(header)} fields, got {len(record)}")
                for column, value in zip(header, record):
                    if not value and complete:
                        raise ValueError(f"{path}:{line}: missing value in {column} (test must be complete)")
                    if value and value not in description.variables[column].states:
                        raise ValueError(f"{path}:{line}: {column}: unknown state {value!r}")
                rows.append([value if value else np.nan for value in record])
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ValueError(f"{path}: invalid CSV: {exc}") from exc
    if not rows:
        raise ValueError(f"{path}:2: dataset has no rows")
    return pd.DataFrame(rows, columns=header).reindex(columns=description.variables).astype(object)


def data_statistics(frame: pd.DataFrame) -> dict:
    return {
        "rows": len(frame),
        "complete_rows": int(frame.notna().all(axis=1).sum()),
        "missing_rate": {key: float(value) for key, value in frame.isna().mean().items()},
    }
