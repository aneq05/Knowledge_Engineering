from __future__ import annotations

import numpy as np
import pandas as pd

from dataclasses import dataclass
from itertools import product
from math import prod
from pgmpy.factors.discrete import TabularCPD
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.parameter_estimator import DiscreteMLE

from .data import Description
from .joint import StateSpace


@dataclass(frozen=True)
class EMResult:
    model: object
    observed_log_likelihood: tuple[float, ...]
    converged: bool = False
    seed: int | None = None
    initialization: str = "mle"


@dataclass(frozen=True)
class MultiStartEM:
    runs: tuple[EMResult, ...]
    best_index: int

    @property
    def best(self) -> EMResult:
        return self.runs[self.best_index]


def empty_network(description: Description, edges) -> object:
    model = DiscreteBayesianNetwork(list(edges))
    model.add_nodes_from(description.variables)  # independent nodes, too
    return model


def fit_mle(description: Description, data: pd.DataFrame, edges=None) -> object:
    model = empty_network(description, description.expert_edges if edges is None else edges)
    estimator = DiscreteMLE(state_names={name: list(labels) for name, labels in description.states.items()})
    estimator.fit(model, data)
    model.add_cpds(*estimator.parameters_)
    model.check_model()
    return model


def _em_parameters(
    description: Description,
    data: pd.DataFrame,
    initial_model,
    *,
    max_iter: int,
    tolerance: float,
    seed: int | None = None,
    initialization: str = "mle",
) -> tuple[dict[str, np.ndarray], tuple[float, ...]]:
    if max_iter < 1 or tolerance <= 0:
        raise ValueError("max_iter must be >= 1 and tolerance must be > 0")
    if initialization not in {"mle", "random"}:
        raise ValueError("initialization must be 'mle' or 'random'")

    space = StateSpace.from_description(description)
    patterns, frequencies = np.unique(space.encode(data), axis=0, return_counts=True)
    matches = np.ones((len(patterns), len(space.assignments)), dtype=bool)
    for axis in range(len(space.variables)):
        observed = patterns[:, axis, None]
        matches &= (observed == -1) | (observed == space.assignments[None, :, axis])

    family = {}
    parameters = {}
    rng = np.random.default_rng(seed)
    for name in space.variables:
        cpd = initial_model.get_cpds(name)
        variables = tuple(cpd.variables)
        shape = tuple(len(space.states[v]) for v in variables)
        indices = tuple(space.assignments[:, space.positions[v]] for v in variables)
        flat = np.ravel_multi_index(indices, shape)
        family[name] = (shape, indices, flat)

        if initialization == "random":
            # One independent, strictly positive Dirichlet draw per parent config.
            parameters[name] = rng.dirichlet(np.ones(shape[0]), size=prod(shape[1:])).T.reshape(shape)
        else:
            # Mild smoothing keeps every partially observed record possible at initialization.
            parameters[name] = space.cpd_values(cpd) * 0.98 + 0.02 / shape[0]

    def joint_table() -> np.ndarray:
        joint = np.ones(len(space.assignments), dtype=float)
        for name in space.variables:
            joint *= parameters[name][family[name][1]]
        return joint

    def observed_mass(joint: np.ndarray) -> np.ndarray:
        return (matches * joint[None, :]).sum(axis=1)

    def log_likelihood(mass: np.ndarray) -> float:
        if np.any(mass <= 0):
            raise ValueError("EM found a record with zero probability; check initial CPDs")
        return float(np.dot(frequencies, np.log(mass)))

    history = [log_likelihood(observed_mass(joint_table()))]
    for _ in range(max_iter):
        # E-step: p[h] / p_r for each possible completion h of each observed row.
        weighted = matches * joint_table()[None, :]
        mass = weighted.sum(axis=1)
        if np.any(mass <= 0):
            raise ValueError("EM encountered impossible observed evidence")
        expected = ((weighted / mass[:, None]) * frequencies[:, None]).sum(axis=0)

        # M-step: weighted CPD family counts, normalized over each variable X.
        for name in space.variables:
            shape, _, flat = family[name]
            counts = np.bincount(flat, weights=expected, minlength=prod(shape)).reshape(shape[0], -1)
            totals = counts.sum(axis=0)
            updated = np.divide(
                counts,
                totals,
                out=np.full_like(counts, 1.0 / shape[0]),
                where=totals > 0,
            )
            parameters[name] = updated.reshape(shape)

        updated_l = log_likelihood(observed_mass(joint_table()))
        if updated_l < history[-1] - 1e-7:
            raise ArithmeticError(f"EM likelihood decreased: {history[-1]} -> {updated_l}")
        history.append(updated_l)
        if abs(history[-1] - history[-2]) < tolerance * len(data):
            break

    return parameters, tuple(history)


def fit_em(
    description: Description,
    data: pd.DataFrame,
    initial_model,
    *,
    max_iter: int = 100,
    tolerance: float = 1e-6,
    seed: int | None = None,
    initialization: str = "mle",
) -> EMResult:

    parameters, history = _em_parameters(
        description,
        data,
        initial_model,
        max_iter=max_iter,
        tolerance=tolerance,
        seed=seed,
        initialization=initialization,
    )
    model = empty_network(description, initial_model.edges())
    cpds = []
    for name, table in parameters.items():
        variables = tuple(initial_model.get_cpds(name).variables)
        parents = list(variables[1:])
        cpds.append(
            TabularCPD(
                variable=name,
                variable_card=table.shape[0],
                values=table.reshape(table.shape[0], -1),
                evidence=parents or None,
                evidence_card=[len(description.states[p]) for p in parents] or None,
                state_names={variable: list(description.states[variable]) for variable in variables},
            )
        )
    model.add_cpds(*cpds)
    model.check_model()
    return EMResult(
        model,
        history,
        converged=abs(history[-1] - history[-2]) < tolerance * len(data),
        seed=seed,
        initialization=initialization,
    )


def fit_em_multistart(
    description: Description,
    data: pd.DataFrame,
    initial_model,
    *,
    starts: int = 5,
    seed: int = 42,
    max_iter: int = 100,
    tolerance: float = 1e-6,
) -> MultiStartEM:
    if starts < 5:
        raise ValueError("The 6-point task requires at least five EM random starts")
    rng = np.random.default_rng(seed)
    seeds = rng.choice(np.iinfo(np.int32).max, size=starts, replace=False)
    runs = tuple(
        fit_em(
            description, data, initial_model,
            max_iter=max_iter,
            tolerance=tolerance,
            initialization="random",
            seed=int(run_seed),
        )
        for run_seed in seeds
    )
    best_index = max(range(len(runs)), key=lambda index: runs[index].observed_log_likelihood[-1])
    return MultiStartEM(runs, best_index)


def largest_cpd_info(description: Description, model, data: pd.DataFrame) -> dict:
    cpd = max(model.get_cpds(), key=lambda item: np.asarray(item.values).size)
    variable = cpd.variable
    parents = tuple(cpd.variables[1:])
    configurations = list(product(*(description.states[p] for p in parents)))
    seen = set(tuple(row) for row in data[[variable, *parents]].dropna()[list(parents)].itertuples(index=False, name=None))
    missing = [parent_states for parent_states in configurations if parent_states not in seen]
    probabilities = None
    if missing:
        evidence = dict(zip(parents, missing[0]))
        probabilities = [float(cpd.get_value(**{variable: state, **evidence})) for state in description.states[variable]]
    return {
        "variable": variable,
        "parents": parents,
        "shape": tuple(np.asarray(cpd.values).shape),
        "entries": int(np.asarray(cpd.values).size),
        "unseen_parent_configurations": len(missing),
        "unseen_example": dict(zip(parents, missing[0])) if missing else None,
        "unseen_cpd": probabilities,
        "states": description.states[variable],
    }
