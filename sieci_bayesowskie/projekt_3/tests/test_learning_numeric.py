import numpy as np

from pathlib import Path

from student_bn.data import load_csv, load_description
from student_bn.evaluation import evaluate_model, majority_grade
from student_bn.joint import StateSpace
from student_bn.learning import _em_parameters, largest_cpd_info
from student_bn.queries import condition_mask, load_queries

DATA = Path(__file__).resolve().parents[1] / "data/k26"


class CPD:
    def __init__(self, variable, columns, values, space):
        self.variable = variable
        self.variables = columns
        self.values = values
        self.space = space

    def get_value(self, **kwargs):
        return float(self.values[tuple(self.space.states[v].index(kwargs[v]) for v in self.variables)])


class Model:
    def __init__(self, cpds, edges):
        self.cpds = cpds
        self._edges = edges

    def get_cpds(self, variable=None):
        if variable is None:
            return list(self.cpds.values())
        return self.cpds[variable]

    def edges(self):
        return self._edges


def reference_mle(description, training, space):
    codes = space.encode(training)
    cpds = {}
    for name in space.variables:
        columns = [name] + sorted(a for a, b in description.expert_edges if b == name)
        axes = [space.positions[v] for v in columns]
        dims = tuple(len(space.states[v]) for v in columns)
        observed = codes[:, axes]
        valid = (observed >= 0).all(axis=1)
        flat = np.ravel_multi_index(observed[valid].T, dims)
        counts = np.bincount(flat, minlength=int(np.prod(dims))).reshape(dims[0], -1)
        col_sums = counts.sum(axis=0)
        values = np.divide(counts, col_sums, out=np.full_like(counts, 1 / dims[0], dtype=float), where=col_sums > 0)
        cpds[name] = CPD(name, columns, values.reshape(dims), space)
    return Model(cpds, description.expert_edges)


def test_numeric_mle_and_em_with_real_k26_data():
    description = load_description(DATA / "opis.json")
    training = load_csv(DATA / "dane.csv", description)
    test = load_csv(DATA / "test.csv", description, complete=True)
    space = StateSpace.from_description(description)
    mle = reference_mle(description, training, space)
    joint = space.probability_table(mle)
    assert np.isclose(joint.sum(), 1)

    info = largest_cpd_info(description, mle, training)
    assert info["variable"] == "G"
    assert info["entries"] == 24
    assert info["unseen_parent_configurations"] == 0

    for query in load_queries(DATA / "ograniczenia.txt", description, advanced=True):
        mask = condition_mask(query.condition, space, space.assignments)
        assert joint[mask].sum() > 0

    most_common = majority_grade(training, space.states["G"])
    metrics = evaluate_model(mle, test, space, fallback_grade=most_common)
    assert np.isfinite(metrics.mean_log_probability)
    assert metrics.zero_probability_rows >= 0
    assert 0 <= metrics.grade_accuracy <= 1

    parameters, history = _em_parameters(description, training, mle, max_iter=12, tolerance=1e-10)
    assert len(history) == 13
    assert all(after >= before - 1e-7 for before, after in zip(history, history[1:]))
    assert history[-1] > history[0]
    for name, values in parameters.items():
        np.testing.assert_allclose(values.reshape(values.shape[0], -1).sum(axis=0), 1, atol=1e-10)
