import networkx as nx
import numpy as np
import pandas as pd

from student_bn.data import Description, Variable
from student_bn.joint import StateSpace
from student_bn.learning import _em_parameters


class CPD:
    def __init__(self, variable, variables, values, state_names):
        self.variable = variable
        self.variables = variables
        self.values = np.asarray(values)
        self.state_names = state_names


class Network(nx.DiGraph):
    def __init__(self, cpds):
        super().__init__()
        self.cpds = {cpd.variable: cpd for cpd in cpds}
        self.add_nodes_from(self.cpds)
        self.add_edges_from((parent, cpd.variable) for cpd in cpds for parent in cpd.variables[1:])

    def get_cpds(self, variable=None):
        return self.cpds[variable] if variable is not None else list(self.cpds.values())


def student_pair():
    description = Description(
        variables={name: Variable(name, ("No", "Yes")) for name in ("X", "Y")},
        expert_edges=(("X", "Y"),), required_edges=(), forbidden_edges=(), tiers=(("X",), ("Y",)),
    )
    canonical = Network([
        CPD("X", ["X"], [0.6, 0.4], {"X": ["No", "Yes"]}),
        CPD("Y", ["Y", "X"], [[0.8, 0.3], [0.2, 0.7]],
            {"Y": ["No", "Yes"], "X": ["No", "Yes"]}),
    ])
    reversed_states = Network([
        CPD("X", ["X"], [0.4, 0.6], {"X": ["Yes", "No"]}),
        CPD("Y", ["Y", "X"], [[0.7, 0.2], [0.3, 0.8]],
            {"Y": ["Yes", "No"], "X": ["Yes", "No"]}),
    ])
    return description, canonical, reversed_states


def test_joint_and_sampling_align_nonstandard_state_order():
    description, canonical, reversed_states = student_pair()
    space = StateSpace.from_description(description)
    expected = np.array([0.48, 0.12, 0.12, 0.28])
    for model in (canonical, reversed_states):
        np.testing.assert_allclose(space.probability_table(model), expected)
        samples = space.samples(model, size=25000, seed=2026)
        pd.testing.assert_frame_equal(space.samples(model, size=5, seed=11),
                                      space.samples(model, size=5, seed=11))
        observed = space.encode(samples)
        sample_index = np.ravel_multi_index(observed.T, space.cardinalities)
        estimated = np.bincount(sample_index, minlength=4) / len(samples)
        assert 0.5 * np.abs(estimated - expected).sum() < 0.02


def test_em_is_invariant_to_cpd_state_order():
    description, canonical, reversed_states = student_pair()
    observations = pd.DataFrame([
        ("No", "No"), ("No", "Yes"), ("Yes", "Yes"),
        ("No", None), (None, "No"), (None, "Yes"),
    ], columns=["X", "Y"])
    first, first_history = _em_parameters(description, observations, canonical, max_iter=15, tolerance=1e-9)
    second, second_history = _em_parameters(description, observations, reversed_states, max_iter=15, tolerance=1e-9)
    for name in first:
        np.testing.assert_allclose(first[name], second[name], atol=1e-12)
    np.testing.assert_allclose(first_history, second_history, atol=1e-12)


def test_joint_is_invariant_to_parent_axis_order():
    description = Description(
        variables={name: Variable(name, ("No", "Yes")) for name in ("X", "Z", "Y")},
        expert_edges=(("X", "Y"), ("Z", "Y")), required_edges=(), forbidden_edges=(),
        tiers=(("X", "Z"), ("Y",)),
    )
    space = StateSpace.from_description(description)
    values = np.array([
        [[0.9, 0.7], [0.4, 0.2]],
        [[0.1, 0.3], [0.6, 0.8]],
    ])
    canonical = Network([
        CPD("X", ["X"], [0.6, 0.4], {"X": ["No", "Yes"]}),
        CPD("Z", ["Z"], [0.8, 0.2], {"Z": ["No", "Yes"]}),
        CPD("Y", ["Y", "X", "Z"], values,
            {v: ["No", "Yes"] for v in ("Y", "X", "Z")}),
    ])
    swapped = Network([
        canonical.get_cpds("X"),
        canonical.get_cpds("Z"),
        CPD("Y", ["Y", "Z", "X"], values.transpose(0, 2, 1),
            {v: ["No", "Yes"] for v in ("Y", "X", "Z")}),
    ])
    np.testing.assert_allclose(space.probability_table(canonical),
                               space.probability_table(swapped))
