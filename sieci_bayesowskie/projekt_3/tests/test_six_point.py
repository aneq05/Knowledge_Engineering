import numpy as np
import pandas as pd
import pytest

from pathlib import Path

from student_bn.data import Description, Variable, load_csv, load_description
from student_bn.evaluation import observed_train_log_likelihood, marginal_comparison
from student_bn.joint import StateSpace
from student_bn.learning import _em_parameters, fit_em_multistart
from student_bn.structure import edge_changes, markov_equivalent, parameter_count, posterior_imputation

DATA = Path(__file__).resolve().parents[1] / "data/k26"


class CPD:
    def __init__(self, variable, columns, values, labels):
        self.variable = variable
        self.variables = columns
        self.values = np.asarray(values)
        self.state_names = {name: list(labels) for name in columns}


class Network:
    def __init__(self, cpds):
        self.cpds = {cpd.variable: cpd for cpd in cpds}

    def get_cpds(self, variable=None):
        if variable is None:
            return list(self.cpds.values())
        return self.cpds[variable]


def simple_case():
    states = ("No", "Yes")
    description = Description(
        variables={name: Variable(name, states) for name in ("X", "Y")},
        expert_edges=(("X", "Y"),), required_edges=(), forbidden_edges=(), tiers=(("X",), ("Y",)),
    )
    model = Network([
        CPD("X", ["X"], [0.75, 0.25], states),
        CPD("Y", ["Y", "X"], [[0.9, 0.2], [0.1, 0.8]], states),
    ])
    return description, model


def test_posterior_imputation_preserves_observed_cells_and_row_count():
    desc, model = simple_case()
    train = pd.DataFrame([
        ("No", None), (None, "Yes"), (None, None), ("Yes", "No")
    ], columns=["X", "Y"])
    imputed = posterior_imputation(model, train, StateSpace.from_description(desc), seed=99)
    assert imputed.shape == train.shape
    assert not imputed.isna().any().any()
    for col in train:
        observed = train[col].notna()
        assert (imputed.loc[observed, col] == train.loc[observed, col]).all()
    pd.testing.assert_frame_equal(imputed, posterior_imputation(model, train, StateSpace.from_description(desc), seed=99))


def test_posterior_sampling_respects_joint_conditional_distribution():
    desc, model = simple_case()
    train = pd.DataFrame([(None, "Yes")] * 4000, columns=["X", "Y"])
    sampled = posterior_imputation(model, train, StateSpace.from_description(desc), seed=2026)
    # P(X=Yes|Y=Yes) = 0.25*0.8 / (0.75*0.1 + 0.25*0.8)
    assert abs((sampled["X"] == "Yes").mean() - (0.2 / 0.275)) < 0.03


def test_random_start_em_observed_loglik_is_monotone_and_normalized():
    desc, model = simple_case()
    train = pd.DataFrame([
        ("No", "No"), ("No", "Yes"), ("Yes", "Yes"),
        (None, "Yes"), ("No", None), (None, None),
    ], columns=["X", "Y"])
    ends = []
    for seed in (7, 8, 9, 10, 11):
        tables, history = _em_parameters(desc, train, model, max_iter=50,
                                         tolerance=1e-6, seed=seed, initialization="random")
        assert len(history) >= 2
        assert all(b >= a - 1e-7 for a, b in zip(history, history[1:]))
        for table in tables.values():
            np.testing.assert_allclose(table.reshape(table.shape[0], -1).sum(axis=0), 1)
        ends.append(history[-1])
    assert max(ends) - min(ends) < 0.05  # toy example yields same observed optimum
    with pytest.raises(ValueError, match="at least five"):
        fit_em_multistart(desc, train, model, starts=4)


def test_graph_parameter_count_and_markov_equivalence():
    desc, _ = simple_case()
    assert parameter_count(desc, (("X", "Y"),)) == 3
    assert parameter_count(desc, ()) == 2
    nodes = ("A", "B", "C")
    assert markov_equivalent(nodes, (("A", "B"), ("B", "C")), (("B", "A"), ("B", "C")))
    assert not markov_equivalent(nodes, (("A", "B"), ("C", "B")), (("A", "B"), ("B", "C")))
    assert edge_changes((("A", "B"), ("B", "C")), (("B", "A"), ("B", "D"))) == {
        "added": (("B", "D"),), "removed": (("B", "C"),), "reversed": (("A", "B"),),
    }


def test_training_likelihood_marginalizes_unknown_entries():
    desc, model = simple_case()
    space = StateSpace.from_description(desc)
    train = pd.DataFrame([(None, "Yes"), ("No", None), ("Yes", "Yes")], columns=["X", "Y"])
    # P(Y=Yes)=0.75*0.1+0.25*0.8; P(X=No)=0.75; P(X=Yes,Y=Yes)=0.2
    expected = np.log(0.275) + np.log(0.75) + np.log(0.2)
    np.testing.assert_allclose(observed_train_log_likelihood(model, train, space), expected)
    frequencies = pd.DataFrame([("No", "Yes"), ("Yes", "No")], columns=["X", "Y"])
    rows = marginal_comparison({"toy": model}, frequencies, space)
    assert len(rows) == 4 and rows[0]["models"]["toy"] == pytest.approx(0.75)


def test_k26_random_multistart_numeric_is_finite():
    """Run the exact E/M kernel on the real incomplete dataset, no pgmpy needed."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from test_learning_numeric import reference_mle

    desc = load_description(DATA / "opis.json")
    train = load_csv(DATA / "dane.csv", desc)
    space = StateSpace.from_description(desc)
    init = reference_mle(desc, train, space)
    finals = []
    for seed in range(5):
        _, history = _em_parameters(desc, train, init, max_iter=80, tolerance=1e-6,
                                    seed=seed, initialization="random")
        assert history[-1] >= history[0]
        assert np.all(np.diff(history) >= -1e-7)
        finals.append(history[-1])
    assert len(finals) == 5 and all(np.isfinite(finals))
