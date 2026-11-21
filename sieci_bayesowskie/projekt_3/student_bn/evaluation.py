from __future__ import annotations

import numpy as np
import pandas as pd

from dataclasses import dataclass
from math import prod

from .joint import StateSpace
from .queries import Query, QueryResult, condition_mask


@dataclass(frozen=True)
class Metrics:
    mean_log_probability: float
    zero_probability_rows: int
    grade_accuracy: float
    impossible_grade_contexts: int


def majority_grade(train: pd.DataFrame, states: tuple[str, ...]) -> str:
    counts = train["G"].value_counts()
    return max(states, key=lambda name: counts.get(name, 0))


def evaluate_model(model, test: pd.DataFrame, space: StateSpace, *, fallback_grade: str) -> Metrics:
    joint = space.probability_table(model)
    probabilities = space.probability_of_rows(joint, test)
    mean_log_p = float(np.mean(np.log(np.maximum(probabilities, 1e-10))))
    zeros = int(np.count_nonzero(probabilities == 0))

    grade_axis = space.positions["G"]
    others = [i for i in range(len(space.variables)) if i != grade_axis]
    contexts = np.moveaxis(joint.reshape(space.cardinalities), grade_axis, -1)
    context_card = [space.cardinalities[i] for i in others]
    test_codes = space.encode(test)
    keys = np.ravel_multi_index(test_codes[:, others].T, context_card)
    scores = contexts.reshape(-1, len(space.states["G"]))[keys]
    predictions = np.argmax(scores, axis=1)
    impossible = scores.sum(axis=1) == 0
    predictions[impossible] = space.states["G"].index(fallback_grade)
    accuracy = float(np.mean(predictions == test_codes[:, grade_axis]))
    return Metrics(mean_log_p, zeros, accuracy, int(impossible.sum()))


def majority_accuracy(test: pd.DataFrame, most_common: str) -> float:
    return float((test["G"] == most_common).mean())


def conditional_probability(
    space: StateSpace,
    joint: np.ndarray,
    variable: str,
    state: str,
    evidence: dict[str, str] | None = None,
) -> float:
    evidence = evidence or {}
    mask = np.ones(len(joint), dtype=bool)
    for name, label in evidence.items():
        mask &= space.assignments[:, space.positions[name]] == space.states[name].index(label)
    mass = float(joint[mask].sum())
    if mass <= 0:
        raise ValueError(f"P({evidence})=0")
    target = space.assignments[:, space.positions[variable]] == space.states[variable].index(state)
    return float(joint[mask & target].sum() / mass)


def independence_checks(model, space: StateSpace, joint: np.ndarray) -> list[dict]:
    triples = [
        ("D", "I", None),
        ("D", "I", "G"),
        ("D", "B", "G"),
        ("D", "B", None),
        ("G", "S", "I"),
        ("Q", "M", None),
    ]
    results = []
    for x, y, z in triples:
        if not {x, y, z}.difference({None}).issubset(space.variables):
            continue
        dependent = bool(model.is_dconnected(x, y, observed=[z] if z else []))
        weighted_tv = 0.0
        states = space.states[z] if z else (None,)
        for state in states:
            mask = np.ones(len(joint), dtype=bool)
            if z:
                mask = space.assignments[:, space.positions[z]] == space.states[z].index(state)
            p_z = float(joint[mask].sum())
            if p_z == 0:
                continue
            distribution = space.marginal(joint * mask, (x, y)) / p_z
            independent = distribution.sum(axis=1, keepdims=True) * distribution.sum(axis=0, keepdims=True)
            weighted_tv += p_z * 0.5 * float(np.abs(distribution - independent).sum())
        results.append({"X": x, "Y": y, "given": z, "d_connected": dependent, "conditional_tv": weighted_tv})
    return results


def sampling_comparison(
    model, space: StateSpace, joint: np.ndarray, queries: list[Query], *, size: int = 20000, seed: int = 42
) -> list[dict]:
    if size < 1:
        return []
    codes = space.encode(space.samples(model, size, seed))
    results = []
    for query in queries:
        exact_mask = condition_mask(query.condition, space, space.assignments)
        sample_mask = condition_mask(query.condition, space, codes)
        accepted = int(sample_mask.sum())
        p_condition = float(joint[exact_mask].sum())
        if accepted == 0 or p_condition == 0:
            results.append({"query": query.text, "accepted": accepted, "tv": None})
            continue
        target_axes = [space.positions[name] for name in query.targets]
        target_shape = [len(space.states[name]) for name in query.targets]
        sample_indices = np.ravel_multi_index(codes[sample_mask][:, target_axes].T, target_shape)
        frequencies = np.bincount(sample_indices, minlength=prod(target_shape)) / accepted
        exact = space.marginal(joint * exact_mask, query.targets).ravel() / p_condition
        results.append({"query": query.text, "accepted": accepted, "tv": 0.5 * float(np.abs(exact - frequencies).sum())})
    return results


def observed_train_log_likelihood(model, train: pd.DataFrame, space: StateSpace) -> float:
    patterns, counts = np.unique(space.encode(train), axis=0, return_counts=True)
    joint = space.probability_table(model)
    matches = np.ones((len(patterns), len(space.assignments)), dtype=bool)
    for axis, _ in enumerate(space.variables):
        matches &= (patterns[:, axis, None] == -1) | (
            patterns[:, axis, None] == space.assignments[None, :, axis]
        )
    masses = matches @ joint
    if (masses <= 0).any():
        return float("-inf")
    return float(np.dot(counts, np.log(masses)))


def marginal_comparison(
    models: dict[str, object], test: pd.DataFrame, space: StateSpace
) -> list[dict[str, object]]:
    joints = {name: space.probability_table(model) for name, model in models.items()}
    marginals = {
        name: {variable: space.marginal(joint, (variable,)) for variable in space.variables}
        for name, joint in joints.items()
    }
    return [
        {"variable": variable, "state": state, "test": float((test[variable] == state).mean()),
         "models": {name: float(values[variable][state_index])
                    for name, values in marginals.items()}}
        for variable in space.variables
        for state_index, state in enumerate(space.states[variable])
    ]


def query_changes(
    reference: list[QueryResult], candidates: dict[str, list[QueryResult]],
    *, limit: int = 10,
) -> list[dict]:
    items = []
    for name, answers in candidates.items():
        if len(answers) != len(reference):
            raise ValueError("Compared query files have different numbers of queries")
        for base, other in zip(reference, answers):
            if base.query.text != other.query.text:
                raise ValueError("Compared query order differs")
            first = np.array([probability for _, probability in base.values])
            second = np.array([probability for _, probability in other.values])
            items.append({
                "model": name,
                "query": base.query.text,
                "tv": 0.5 * float(np.abs(first - second).sum()),
                "evidence_delta": other.event_probability - base.event_probability,
                "base_map": base.maximum,
                "other_map": other.maximum,
            })
    return sorted(items, key=lambda item: item["tv"], reverse=True)[:limit]
