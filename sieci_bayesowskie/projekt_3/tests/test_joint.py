import numpy as np
import pandas as pd

from pathlib import Path

from student_bn.data import Description, Variable
from student_bn.joint import StateSpace


class FakeCPD:
    def __init__(self, variable, variables, values):
        self.variable = variable
        self.variables = variables
        self.values = np.asarray(values)


class FakeModel:
    def __init__(self, cpds):
        self.cpds = cpds

    def get_cpds(self):
        return self.cpds


def test_joint_and_marginal_for_three_binary_variables():
    description = Description(
        variables={name: Variable(name, ("No", "Yes")) for name in ("X", "Y", "Z")},
        expert_edges=(("X", "Y"),), required_edges=(), forbidden_edges=(), tiers=(("X", "Z"), ("Y",)),
    )
    space = StateSpace.from_description(description)
    network = FakeModel([
        FakeCPD("X", ["X"], [0.6, 0.4]),
        FakeCPD("Z", ["Z"], [0.2, 0.8]),
        FakeCPD("Y", ["Y", "X"], [[0.9, 0.1], [0.1, 0.9]]),
    ])
    joint = space.probability_table(network)
    assert np.isclose(joint.sum(), 1)
    np.testing.assert_allclose(space.marginal(joint, ("Y",)), [0.58, 0.42])
    frame = pd.DataFrame([{"X": "No", "Y": "Yes", "Z": "Yes"}])
    np.testing.assert_allclose(space.probability_of_rows(joint, frame), [0.6 * 0.1 * 0.8])
