from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd

from dataclasses import dataclass
from itertools import product
from math import prod

from .data import Description


@dataclass(frozen=True)
class StateSpace:
    variables: tuple[str, ...]
    states: dict[str, tuple[str, ...]]
    assignments: np.ndarray

    @classmethod
    def from_description(cls, description: Description) -> StateSpace:
        variables = tuple(description.variables)
        states = description.states
        assignments = np.asarray(list(product(*(range(len(states[v])) for v in variables))), dtype=int)
        return cls(variables, states, assignments)

    @property
    def cardinalities(self) -> tuple[int, ...]:
        return tuple(len(self.states[v]) for v in self.variables)

    @property
    def positions(self) -> dict[str, int]:
        return {name: i for i, name in enumerate(self.variables)}

    def encode(self, frame: pd.DataFrame, *, missing: int = -1) -> np.ndarray:
        columns = []
        for variable in self.variables:
            labels = {state: i for i, state in enumerate(self.states[variable])}
            column = frame[variable].map(labels).fillna(missing).to_numpy(dtype=int)
            columns.append(column)
        return np.column_stack(columns)

    def cpd_values(self, cpd) -> np.ndarray:
        values = np.asarray(cpd.values, dtype=float)
        names = getattr(cpd, "state_names", self.states)
        for axis, variable in enumerate(cpd.variables):
            indices = [names[variable].index(state) for state in self.states[variable]]
            values = np.take(values, indices, axis=axis)
        return values

    def probability_table(self, model) -> np.ndarray:
        probability = np.ones(len(self.assignments), dtype=float)
        positions = self.positions
        for cpd in model.get_cpds():
            indices = tuple(self.assignments[:, positions[v]] for v in cpd.variables)
            probability *= self.cpd_values(cpd)[indices]
        return probability

    def marginal(self, weights: np.ndarray, variables: tuple[str, ...]) -> np.ndarray:
        axes = [self.positions[v] for v in variables]
        shape = tuple(len(self.states[v]) for v in variables)
        flat = np.ravel_multi_index(self.assignments[:, axes].T, shape)
        return np.bincount(flat, weights=weights, minlength=prod(shape)).reshape(shape)

    def probability_of_rows(self, joint: np.ndarray, frame: pd.DataFrame) -> np.ndarray:
        indices = np.ravel_multi_index(self.encode(frame).T, self.cardinalities)
        return joint[indices]

    def samples(self, model, size: int, seed: int) -> pd.DataFrame:
        if size <= 0:
            raise ValueError("sample size must be positive")
        generator = np.random.default_rng(seed)
        codes = np.empty((size, len(self.variables)), dtype=int)
        positions = self.positions
        # Tie-break topological order with dataset variable order, not hash order.
        for variable in nx.lexicographical_topological_sort(model, key=positions.__getitem__):
            cpd = model.get_cpds(variable)
            parents = tuple(cpd.variables[1:])
            table = self.cpd_values(cpd).reshape(len(self.states[variable]), -1)
            if parents:
                parent_values = codes[:, [positions[p] for p in parents]]
                cards = [len(self.states[p]) for p in parents]
                parent_index = np.ravel_multi_index(parent_values.T, cards)
            else:
                parent_index = np.zeros(size, dtype=int)
            cdf = np.cumsum(table[:, parent_index], axis=0)
            codes[:, positions[variable]] = (generator.random(size)[None, :] >= cdf).sum(axis=0)
        return pd.DataFrame({name: np.asarray(self.states[name])[codes[:, positions[name]]]
                             for name in self.variables})
