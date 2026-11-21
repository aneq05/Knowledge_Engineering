from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd

from dataclasses import dataclass
from itertools import combinations
from math import prod
from pgmpy.causal_discovery import ExpertKnowledge, HillClimbSearch
from pgmpy.base import DAG
from pgmpy.structure_score import BIC

from .data import Description
from .joint import StateSpace
from .learning import EMResult, fit_em, fit_mle


@dataclass(frozen=True)
class ImputationStep:
    round: int
    edges: tuple[tuple[str, str], ...]
    em: EMResult


@dataclass(frozen=True)
class StructureResult:
    model: object
    edges: tuple[tuple[str, str], ...]
    bic: float
    expert_bic: float
    complete_rows: int


def learn_dag(description: Description, complete: pd.DataFrame, *, constrained: bool):
    if complete.empty or complete.isna().any().any():
        raise ValueError("HillClimbSearch requires nonempty, fully observed training rows")
    if set(complete.columns) != set(description.variables):
        raise ValueError("HillClimbSearch requires exactly the described variables")

    knowledge = (
        ExpertKnowledge(
            required_edges=list(description.required_edges),
            forbidden_edges=list(description.forbidden_edges),
            temporal_order=[list(tier) for tier in description.tiers],
        )
        if constrained else None
    )
    hc = HillClimbSearch(
        scoring_method="bic-d",
        expert_knowledge=knowledge,
        return_type="dag",     # do not use the default PDAG for parameter fitting
        show_progress=False,
    )
    hc.fit(complete.loc[:, list(description.variables)])
    dag = hc.causal_graph_
    if set(dag.nodes()) != set(description.variables) or not nx.is_directed_acyclic_graph(dag):
        raise ValueError("Hill climbing returned an invalid graph")
    if constrained:
        edges = set(dag.edges())
        tier = {name: rank for rank, layer in enumerate(description.tiers) for name in layer}
        if not set(description.required_edges).issubset(edges):
            raise ValueError("Learned graph is missing required edges")
        if edges & set(description.forbidden_edges):
            raise ValueError("Learned graph contains forbidden edges")
        if any(tier[left] > tier[right] for left, right in edges):
            raise ValueError("Learned graph contradicts the temporal order")
    return dag


def learn_bic_structure(description: Description, data: pd.DataFrame) -> StructureResult:
    complete = data.dropna()
    dag = learn_dag(description, complete, constrained=True)
    expert = DAG(description.expert_edges)
    expert.add_nodes_from(description.variables)
    bic = BIC(complete, state_names={k: list(v) for k, v in description.states.items()})
    model = fit_mle(description, data, dag.edges())
    return StructureResult(
        model, tuple(sorted(dag.edges())), float(bic.score(dag)),
        float(bic.score(expert)), len(complete),
    )


def posterior_imputation(
    model, incomplete: pd.DataFrame, space: StateSpace, *, seed: int
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    encoded = space.encode(incomplete)
    patterns, inverse = np.unique(encoded, axis=0, return_inverse=True)
    joint = space.probability_table(model)
    completed = np.empty_like(encoded)

    for pattern_index, pattern in enumerate(patterns):
        rows = np.flatnonzero(inverse == pattern_index)
        compatible = np.all(
            (pattern == -1) | (space.assignments == pattern), axis=1
        )
        choices = np.flatnonzero(compatible)
        probabilities = joint[choices]
        total = probabilities.sum()
        if total <= 0:
            raise ValueError("Cannot impute an observation with P(evidence)=0")
        completed[rows] = space.assignments[
            rng.choice(choices, size=len(rows), p=probabilities / total)
        ]

    return pd.DataFrame(
        {variable: np.asarray(space.states[variable])[completed[:, i]]
         for i, variable in enumerate(space.variables)},
        columns=list(space.variables),
    )


def iterative_structure_learning(
    description: Description,
    train: pd.DataFrame,
    start_model,
    *,
    rounds: int = 2,
    max_iter: int = 100,
    tolerance: float = 1e-6,
    seed: int = 42,
) -> tuple[ImputationStep, ...]:
    if rounds < 1:
        raise ValueError("At least one structure-imputation round is needed")
    space = StateSpace.from_description(description)
    model = start_model
    steps = []
    for index in range(rounds):
        filled = posterior_imputation(model, train, space, seed=seed + index)
        assert len(filled) == len(train) and not filled.isna().any().any()
        dag = learn_dag(description, filled, constrained=True)
        mle = fit_mle(description, train, edges=list(dag.edges()))
        em = fit_em(description, train, mle, max_iter=max_iter, tolerance=tolerance)
        steps.append(ImputationStep(index + 1, tuple(sorted(dag.edges())), em))
        model = em.model
    return tuple(steps)


def parameter_count(description: Description, edges) -> int:
    parents = {name: [] for name in description.variables}
    for left, right in edges:
        parents[right].append(left)
    return sum((len(description.states[name]) - 1) *
               prod(len(description.states[parent]) for parent in inputs)
               for name, inputs in parents.items())


def markov_equivalent(nodes, first_edges, second_edges) -> bool:
    first = nx.DiGraph()
    second = nx.DiGraph()
    for graph, edges in ((first, first_edges), (second, second_edges)):
        graph.add_nodes_from(nodes)
        graph.add_edges_from(edges)

    def skeleton(graph):
        return {frozenset(edge) for edge in graph.edges()}

    def colliders(graph):
        undirected = graph.to_undirected()
        return {
            (frozenset({left, right}), middle)
            for middle in graph.nodes()
            for left, right in combinations(graph.predecessors(middle), 2)
            if not undirected.has_edge(left, right)
        }

    return skeleton(first) == skeleton(second) and colliders(first) == colliders(second)


def edge_changes(reference, candidate) -> dict[str, tuple[tuple[str, str], ...]]:
    old, new = set(reference), set(candidate)
    reversed_edges = {edge for edge in old if edge[::-1] in new}
    removed = old - new - reversed_edges
    added = new - old - {edge[::-1] for edge in reversed_edges}
    return {
        "added": tuple(sorted(added)),
        "removed": tuple(sorted(removed)),
        "reversed": tuple(sorted(reversed_edges)),
    }
